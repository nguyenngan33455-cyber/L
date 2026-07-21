# ZBGym Failure Recovery

## Overview

This document defines the failure handling and recovery strategies for the ZBGym Kernel and all framework components.

---

## Failure Categories

### Category 1: Kernel Failures

These are critical failures that affect the entire framework.

| Failure | Severity | Recovery |
|---------|----------|----------|
| Bootstrap failure | CRITICAL | Cannot start |
| Initialization failure | CRITICAL | Cannot start |
| Internal error | CRITICAL | Shutdown |
| Resource exhaustion | CRITICAL | Shutdown |

### Category 2: Module Failures

These affect individual modules but may allow continued operation.

| Failure | Severity | Recovery |
|---------|----------|----------|
| Init failure | HIGH | Retry or isolate |
| Runtime error | MEDIUM | Isolate or recover |
| Timeout | MEDIUM | Retry or isolate |
| Health check fail | LOW | Monitor |

### Category 3: External Failures

These are external system failures that modules must handle.

| Failure | Severity | Recovery |
|---------|----------|----------|
| Network disconnect | MEDIUM | Reconnect |
| File system error | HIGH | Depends |
| Memory exhaustion | CRITICAL | Shutdown |

---

## Module Crash Recovery

### Detection

```python
# Kernel catches exceptions from module callbacks
try:
    module.tick(tick)
except Exception as e:
    kernel._handle_module_error(module, e)
```

### Recovery Flow

```
Module Error Detected
        │
        ▼
┌─────────────────┐
│ Classify Error  │
└────────┬────────┘
         │
         ├─→ CRITICAL?
         │       │
         │   Yes ├─→ Enter SHUTDOWN
         │       │
         │   No  ├─→ Continue
         │       │
         ▼       │
┌─────────────────┐
│ Is Recoverable?│
└────────┬────────┘
         │
         ├─→ Yes ├─→ Attempt Recovery
         │       │
         │       └─→ Success? ─┐
         │                       │
         │                   Yes ├─→ Return to RUNNING
         │                       │
         │                   No  ├─→ Isolate Module
         │                               │
         │                               └─→ Return to RUNNING (degraded)
         │
         └─→ No ├─→ Isolate Module
                     │
                     └─→ Can continue without?
                             │
                         Yes ├─→ Return to RUNNING (degraded)
                         │
                         No ├─→ Enter SHUTDOWN
```

### Recovery Strategies

#### Strategy 1: Retry Initialization

```python
def recover_module_retry(module: Module) -> bool:
    """Attempt to reinitialize the module."""
    for attempt in range(MAX_RETRIES):
        try:
            module.shutdown()
            module.initialize(context)
            module.start()
            return True
        except Exception as e:
            logger.warning(f"Retry {attempt} failed: {e}")
            time.sleep(RETRY_DELAY)
    return False
```

#### Strategy 2: Fallback Implementation

```python
def recover_with_fallback(module: Module) -> bool:
    """Use fallback implementation."""
    if hasattr(module, "fallback"):
        module.fallback()
        return True
    return False
```

#### Strategy 3: Module Isolation

```python
def isolate_module(module: Module) -> None:
    """Isolate failed module."""
    # Remove from event dispatch
    event_bus.unsubscribe_all(module)
    
    # Remove from tick pipeline
    tick_coordinator.remove_module(module)
    
    # Mark as unhealthy
    module.health_status = HealthStatus.ISOLATED
    
    # Log for diagnostics
    logger.error(f"Module {module.name} isolated")
```

#### Strategy 4: Graceful Degradation

```python
def continue_degraded(missing_modules: list[str]) -> None:
    """Continue with missing functionality."""
    if "dashboard" in missing_modules:
        logger.warning("Running without dashboard")
        # Simulation continues without visualization
    
    if "replay" in missing_modules:
        logger.warning("Running without replay")
        # Simulation continues without recording
```

---

## Plugin Crash Recovery

### Detection

```python
try:
    sandbox.execute(plugin, "on_tick", tick)
except SandboxViolation as e:
    kernel.handle_plugin_error(plugin, e)
except TimeoutError:
    kernel.handle_plugin_timeout(plugin)
except Exception as e:
    kernel.handle_plugin_crash(plugin, e)
```

### Recovery Flow

```
Plugin Error
     │
     ▼
┌─────────────────┐
│ Sandbox Caught  │ → Violation → Unload Plugin
└────────┬────────┘
         │
         └─→ Exception
                │
                ▼
         ┌─────────────────┐
         │ Classify Error  │
         └────────┬────────┘
                  │
                  ├─→ Runtime Error
                  │       │
                  │       ▼
                  │  ┌─────────────────┐
                  │  │ Retry? (< 3)   │
                  │  └────────┬────────┘
                  │           │
                  │       Yes ├─→ Retry sandbox
                  │           │
                  │       No  ├─→ Isolate Plugin
                  │                   │
                  │                   └─→ Continue Simulation
                  │
                  ├─→ Timeout
                  │       │
                  │       ▼
                  │  Terminate Sandbox
                  │       │
                  │       └─→ Isolate Plugin
                  │               │
                  │               └─→ Continue Simulation
                  │
                  └─→ Fatal Error
                          │
                          └─→ Unload Plugin
                                  │
                                  └─→ Continue Simulation
```

### Sandbox Recovery

```python
class SandboxRecovery:
    """Handles plugin sandbox recovery."""
    
    def __init__(self, max_retries: int = 3):
        self._retries = {}
        self._max_retries = max_retries
    
    def should_retry(self, plugin: str) -> bool:
        """Check if plugin should retry."""
        return self._retries.get(plugin, 0) < self._max_retries
    
    def record_retry(self, plugin: str) -> None:
        """Record retry attempt."""
        self._retries[plugin] = self._retries.get(plugin, 0) + 1
    
    def reset(self, plugin: str) -> None:
        """Reset retry count."""
        self._retries[plugin] = 0
```

---

## Dashboard Disconnect Recovery

### Detection

```python
# WebSocket connection lost
async def on_disconnect(websocket):
    kernel.handle_dashboard_disconnect()
```

### Recovery Flow

```
Dashboard Disconnect
        │
        ▼
┌─────────────────┐
│ Log Disconnect  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Simulation      │
│ Continues       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Reconnect       │
│ Attempts        │
└────────┬────────┘
         │
         ├─→ Connected
         │       │
         │       ▼
         │  Sync State ─→ Resume Normal Operation
         │
         └─→ Failed
                 │
                 └─→ Log Warning ─→ Continue Without Dashboard
```

### Reconnection Strategy

```python
class DashboardReconnection:
    """Handles dashboard reconnection."""
    
    def __init__(self, max_attempts: int = 5, backoff: float = 1.0):
        self._max_attempts = max_attempts
        self._backoff = backoff
    
    async def reconnect(self) -> bool:
        """Attempt to reconnect with exponential backoff."""
        for attempt in range(self._max_attempts):
            try:
                await websocket.connect(url)
                await self._sync_state()
                return True
            except Exception as e:
                delay = self._backoff * (2 ** attempt)
                await asyncio.sleep(delay)
        return False
```

---

## Replay Failure Recovery

### Detection

```python
try:
    recorder.record_step(state)
except IOError as e:
    kernel.handle_replay_error("write", e)
except MemoryError:
    kernel.handle_replay_error("memory", None)
```

### Recovery Flow

```
Replay Error
     │
     ▼
┌─────────────────┐
│ Classify Error  │
└────────┬────────┘
         │
         ├─→ Write Error
         │       │
         │       ▼
         │  ┌─────────────────┐
         │  │ Retry? (< 3)   │
         │  └────────┬────────┘
         │           │
         │       Yes ├─→ Retry Write
         │           │
         │       No  ├─→ Stop Recording
         │               │
         │               └─→ Continue Simulation (no replay)
         │
         ├─→ Memory Error
         │       │
         │       ▼
         │  Flush Buffer
         │       │
         │       └─→ Continue with smaller buffer
         │
         └─→ Corrupt Data
                 │
                 └─→ Mark Replay Corrupt
                         │
                         └─→ Attempt Recovery ─→ Continue
```

---

## Scheduler Failure Recovery

### Detection

```python
# Scheduler timeout
if not scheduler.tick_completed_within(timeout):
    kernel.handle_scheduler_timeout()

# Scheduler exception
try:
    scheduler.tick()
except Exception as e:
    kernel.handle_scheduler_error(e)
```

### Recovery Flow

```
Scheduler Error
     │
     ▼
┌─────────────────┐
│ Log Error       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Is AI Affected? │
└────────┬────────┘
         │
         ├─→ Yes
         │       │
         │       ▼
         │  ┌─────────────────┐
         │  │ Use Fallback AI │
         │  │ (scripted)      │
         │  └────────┬────────┘
         │           │
         │       Success ├─→ Continue (degraded AI)
         │           │
         │       Fail  └─→ Pause Simulation
         │
         └─→ No
                 │
                 └─→ Continue Simulation
```

---

## Memory Exhaustion Recovery

### Detection

```python
# Memory threshold exceeded
if memory_usage > MEMORY_THRESHOLD:
    kernel.trigger_gc()
    
    if memory_usage > CRITICAL_THRESHOLD:
        kernel.handle_memory_critical()
```

### Recovery Flow

```
Memory Warning
     │
     ▼
┌─────────────────┐
│ Trigger GC      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Memory OK?      │
└────────┬────────┘
         │
     Yes ├─→ Continue
         │
     No  ├─→ Attempt Cleanup
         │       │
         │       ├─→ Clear caches
         │       ├─→ Flush buffers
         │       └─→ Run GC
         │       │
         │       └─→ Memory OK?
         │               │
         │           Yes ├─→ Continue
         │               │
         │           No  ├─→ Critical
         │                   │
         │                   └─→ ┌─────────────────┐
         │                       │ Enter Recovery  │
         │                       │ Mode            │
         │                       └────────┬────────┘
         │                                │
         │                                └─→ Still Critical?
         │                                        │
         │                                    Yes ├─→ SHUTDOWN
         │                                        │
         │                                    No  └─→ Continue (degraded)
```

### Memory Emergency Actions

```python
def handle_memory_critical():
    """Handle critical memory situation."""
    # 1. Stop new allocations in non-critical modules
    # 2. Flush all buffers
    # 3. Run full garbage collection
    # 4. Compact memory
    # 5. If still critical, begin graceful shutdown
```

---

## Dependency Failure Recovery

### Detection

```python
# Required dependency unavailable
if not context.has_service(required_dep):
    kernel.handle_dependency_missing(module, required_dep)
```

### Recovery Flow

```
Dependency Missing
        │
        ▼
┌─────────────────┐
│ Is Dependency   │
│ Required?       │
└────────┬────────┘
         │
     Yes ├─→ Is Module Critical?
         │       │
         │   Yes ├─→ SHUTDOWN
         │       │
         │   No  ├─→ Isolate Module
         │           │
         │           └─→ Continue Without Module
         │
     No  └─→ Module Continues Without Dependency
```

---

## Kernel Panic Recovery

### Definition

Kernel Panic is a critical failure from which recovery is impossible.

### Triggers

| Trigger | Action |
|---------|--------|
| Internal state corruption | PANIC |
| Unrecoverable deadlock | PANIC |
| Stack overflow | PANIC |
| Fatal signal | PANIC |

### Panic Flow

```
Kernel Panic
     │
     ▼
┌─────────────────┐
│ Log Critical    │
│ State           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Preserve State  │
│ for Debugging   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Signal Handlers │
│ Disabled        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Exit Process    │
│ (with code 1)   │
└─────────────────┘
```

### Panic State Preservation

```python
def handle_kernel_panic(error: Exception):
    """Handle unrecoverable kernel error."""
    # 1. Disable signal handlers
    # 2. Write panic dump
    with open("panic_dump.log", "w") as f:
        f.write(f"Kernel Panic: {error}\n")
        f.write(f"State: {kernel.state}\n")
        f.write(f"Modules: {list(kernel.modules.keys())}\n")
        f.write(f"Traceback:\n{traceback.format_exc()}\n")
    
    # 3. Exit with error code
    os._exit(1)
```

---

## Error Recovery Summary

| Error Type | Detection | Recovery | Continuation |
|------------|-----------|----------|--------------|
| Module crash | Exception | Retry/Fallback/Isolate | Depends |
| Plugin crash | Sandbox | Unload/Isolate | Always |
| Dashboard disconnect | WebSocket | Reconnect | Always |
| Replay failure | IOError | Retry/Stop | Always |
| Scheduler failure | Timeout | Fallback/Pause | Depends |
| Memory exhaustion | Threshold | GC/Cleanup | Depends |
| Dependency missing | Check | Isolate/Shutdown | Depends |
| Kernel panic | Critical | Exit | Never |

---

## Recovery Best Practices

### 1. Fail Fast

Detect errors early and fail with clear messages.

### 2. Fail Gracefully

Handle errors without crashing the entire system.

### 3. Log Everything

Record all errors for debugging.

### 4. Provide Context

Include relevant state in error messages.

### 5. Attempt Recovery

Always try to recover before giving up.

### 6. Isolate Failures

Prevent failures from propagating.

### 7. Maintain invariants

Ensure consistent state after recovery.

---

## Summary

| Scenario | Recovery | Guarantees |
|----------|----------|------------|
| Module crash | Retry/Isolate | Simulation continues |
| Plugin crash | Unload | Simulation continues |
| Dashboard disconnect | Reconnect | Simulation continues |
| Replay failure | Retry/Stop | Simulation continues |
| Scheduler failure | Fallback | Simulation continues (degraded) |
| Memory exhaustion | GC/Cleanup | May shutdown |
| Dependency missing | Isolate | Simulation continues (degraded) |
| Kernel panic | Exit | No continuation |
