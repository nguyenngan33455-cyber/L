# ZBGym Kernel Lifecycle

## Overview

The lifecycle defines how the framework and modules transition between states. The Kernel manages all lifecycle transitions to ensure deterministic, reproducible behavior.

---

## Module Lifecycle States

```
┌─────────────┐
│  DISCOVERED │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ REGISTERED  │◄──────────────────┐
└──────┬──────┘                   │
       │                           │
       ▼                           │
┌─────────────┐                    │
│INITIALIZED  │◄──────────────────┤
└──────┬──────┘                   │
       │                           │
       ▼                           │
┌─────────────┐                    │
│   STARTED   │◄──────────────────┤
└──────┬──────┘                   │
       │                           │
       ▼                           │
┌─────────────┐                    │
│  RUNNING    │◄──────────────────┤
└──────┬──────┘                   │
       │                           │
       ▼                           │
┌─────────────┐                    │
│   PAUSED    │────────────────────┤
└──────┬──────┘                   │
       │                           │
       ▼                           │
┌─────────────┐                    │
│  STOPPED    │◄──────────────────┤
└──────┬──────┘                   │
       │                           │
       ▼                           │
┌─────────────┐                    │
│  SHUTDOWN   │◄──────────────────┤
└──────┬──────┘                   │
       │                           │
       ▼                           │
┌─────────────┐
│  UNLOADED  │
└─────────────┘
```

---

## State Definitions

### DISCOVERED

Module is found but not registered.

**Allowed Operations:**
- Validate metadata
- Check dependencies

**Forbidden Operations:**
- Access other modules
- Subscribe to events
- Register services

### REGISTERED

Module is registered with Kernel.

**Allowed Operations:**
- Access RuntimeContext
- Read configuration
- Validate capabilities

**Forbidden Operations:**
- Initialize resources
- Subscribe to events
- Execute logic

### INITIALIZED

Module has allocated resources.

**Allowed Operations:**
- Subscribe to events
- Register services
- Prepare for execution

**Forbidden Operations:**
- Execute simulation logic
- Access simulation state
- Modify replay data

### STARTED

Module is ready to run.

**Allowed Operations:**
- Execute initialization callbacks
- Setup tick handlers
- Prepare first tick

**Forbidden Operations:**
- Process simulation ticks
- Generate output

### RUNNING

Module is actively processing.

**Allowed Operations:**
- Process ticks
- Generate events
- Modify state
- Record metrics

**Forbidden Operations:**
- Re-initialize
- Change capabilities

### PAUSED

Module is paused but not stopped.

**Allowed Operations:**
- Read state
- Handle pause callbacks
- Resume

**Forbidden Operations:**
- Process new ticks
- Modify state

### STOPPED

Module is stopped but not shutdown.

**Allowed Operations:**
- Read state
- Prepare shutdown
- Cleanup partial state

**Forbidden Operations:**
- Process ticks
- Generate events

### SHUTDOWN

Module is shutting down.

**Allowed Operations:**
- Cleanup resources
- Finalize state
- Persist data

**Forbidden Operations:**
- Access other modules
- Generate events
- Modify state

### UNLOADED

Module is fully unloaded.

**Allowed Operations:**
- None

---

## State Transitions

### Valid Transitions

| From | To | Condition |
|------|-----|-----------|
| DISCOVERED | REGISTERED | Metadata valid, deps satisfied |
| REGISTERED | INITIALIZED | Resources allocated |
| INITIALIZED | STARTED | Ready for execution |
| STARTED | RUNNING | First tick received |
| RUNNING | PAUSED | Pause requested |
| PAUSED | RUNNING | Resume requested |
| RUNNING | STOPPED | Stop requested |
| STOPPED | RUNNING | Restart requested |
| STOPPED | SHUTDOWN | Shutdown requested |
| SHUTDOWN | UNLOADED | Cleanup complete |
| RUNNING | SHUTDOWN | Emergency shutdown |
| PAUSED | SHUTDOWN | Emergency shutdown |

### Invalid Transitions

These transitions MUST be rejected:

| From | To | Reason |
|------|-----|--------|
| DISCOVERED | RUNNING | Must register and initialize |
| REGISTERED | RUNNING | Must initialize and start |
| SHUTDOWN | RUNNING | Cannot restart from shutdown |
| UNLOADED | * | Cannot transition from unloaded |

---

## Framework Lifecycle

### Boot Sequence

```
1. Create Kernel instance
2. Load configuration
3. Create RuntimeContext
4. Discover modules
5. Register modules
6. Validate dependencies
7. Resolve load order
8. Initialize modules (in order)
9. Start modules (in order)
10. Enter main loop (RUNNING)
```

### Shutdown Sequence

```
1. Request shutdown
2. Transition all modules to STOPPED
3. Transition all modules to SHUTDOWN
4. Cleanup resources
5. Persist state (if configured)
6. Transition all modules to UNLOADED
7. Release RuntimeContext
8. Exit
```

### Emergency Shutdown

```
1. Log critical error
2. Transition all modules to SHUTDOWN
3. Force cleanup
4. Exit immediately
```

---

## Lifecycle Callbacks

Modules MUST implement lifecycle callbacks:

```python
class ModuleInterface:
    def on_discovered(self, context: RuntimeContext) -> None:
        """Called when module is discovered."""
        pass
    
    def on_registered(self) -> None:
        """Called when module is registered."""
        pass
    
    def on_initializing(self) -> None:
        """Called before initialization."""
        pass
    
    def on_initialized(self) -> None:
        """Called after initialization."""
        pass
    
    def on_starting(self) -> None:
        """Called before starting."""
        pass
    
    def on_started(self) -> None:
        """Called after starting."""
        pass
    
    def on_tick(self, tick: int) -> None:
        """Called on each tick."""
        pass
    
    def on_pausing(self) -> None:
        """Called before pause."""
        pass
    
    def on_paused(self) -> None:
        """Called after pause."""
        pass
    
    def on_resuming(self) -> None:
        """Called before resume."""
        pass
    
    def on_resumed(self) -> None:
        """Called after resume."""
        pass
    
    def on_stopping(self) -> None:
        """Called before stop."""
        pass
    
    def on_stopped(self) -> None:
        """Called after stop."""
        pass
    
    def on_shutting_down(self) -> None:
        """Called before shutdown."""
        pass
    
    def on_shutdown(self) -> None:
        """Called after shutdown."""
        pass
    
    def on_unload(self) -> None:
        """Called before unload."""
        pass
    
    def on_error(self, error: Exception) -> None:
        """Called on error."""
        pass
```

---

## Lifecycle Validation

### Pre-Transition Validation

Before any transition, Kernel validates:

1. **State Validity**: Target state is valid for current state
2. **Dependencies**: All dependencies are in valid states
3. **Resources**: Required resources are available
4. **Permissions**: Caller has permission to trigger transition
5. **Idempotency**: Repeated transitions are handled gracefully

### Post-Transition Validation

After transition, Kernel validates:

1. **State Consistency**: Module state matches target
2. **Resource Integrity**: Resources are properly allocated/released
3. **Capability Integrity**: Capabilities match module state
4. **Event Consistency**: No orphaned events or handlers

---

## Error Handling

### Lifecycle Errors

| Error | Action |
|-------|--------|
| Invalid transition | Reject transition, log warning |
| Dependency not ready | Block transition, retry later |
| Resource unavailable | Mark module unhealthy |
| Exception in callback | Log error, continue or abort |

### Recovery Strategies

1. **Retry**: Re-attempt failed transition
2. **Fallback**: Use default module implementation
3. **Skip**: Continue without this module
4. **Abort**: Stop entire framework

---

## Tick Lifecycle

### Tick States

```
┌─────────┐
│  IDLE   │
└────┬────┘
     │
     ▼
┌─────────┐
│ RUNNING │
└────┬────┘
     │
     ▼
┌─────────┐
│ PAUSED │
└────┬────┘
     │
     ▼
┌─────────┐
│ STOPPED │
└─────────┘
```

### Tick Transitions

```
IDLE → RUNNING: First tick() call
RUNNING → PAUSED: Pause requested
PAUSED → RUNNING: Resume requested
RUNNING → STOPPED: Stop requested
STOPPED → IDLE: Reset requested
```

---

## Health States

Modules report health status:

| State | Meaning |
|-------|---------|
| HEALTHY | Module functioning normally |
| DEGRADED | Module operating with limitations |
| UNHEALTHY | Module needs attention |
| FAILED | Module has failed |

### Health Transitions

```
HEALTHY → DEGRADED: Non-critical issue detected
DEGRADED → HEALTHY: Issue resolved
HEALTHY → UNHEALTHY: Critical issue detected
UNHEALTHY → HEALTHY: Issue resolved
* → FAILED: Unrecoverable error
```

---

## Concurrency

### Thread Safety

Lifecycle operations must be thread-safe:

1. **State Access**: Protected by locks
2. **Transitions**: Serialized per module
3. **Callbacks**: May be called from different threads
4. **Validation**: Atomic checks

### Lock Ordering

To prevent deadlocks:

```
1. RuntimeContext lock (outermost)
2. ModuleManager lock
3. Individual module locks (innermost)
```

---

## Summary

Key lifecycle principles:

1. **State Machine**: All transitions are explicit and validated
2. **Callbacks**: Modules notified of all lifecycle events
3. **Validation**: Pre and post-transition validation
4. **Error Handling**: Graceful degradation on errors
5. **Thread Safety**: All operations are thread-safe
6. **Determinism**: Same sequence of states produces same result
