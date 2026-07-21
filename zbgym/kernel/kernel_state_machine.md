# ZBGym Kernel State Machine

## Overview

This document defines the complete state machine for the ZBGym Kernel. The Kernel transitions between states based on lifecycle events and errors.

---

## Kernel States

```
┌─────────────┐
│   CREATED   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   BOOTING   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│INITIALIZING │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    READY    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  RUNNING    │
└──────┬──────┘
       │
       ├───┬───────────┬──────────┐
       │   │           │          │
       ▼   ▼           ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
│ PAUSED │ │RECOVERING│ │STOPPING │ │ ERROR    │
└────┬───┘ └────┬────┘ └────┬─────┘ └────┬─────┘
     │          │           │            │
     │          │           │            │
     ▼          │           ▼            ▼
┌─────────┐     │     ┌─────────┐ ┌─────────┐
│ RUNNING │     │     │STOPPED  │ │ FAILED  │
└────┬───┘     │     └────┬─────┘ └────┬─────┘
     │          │          │            │
     └──────────┴──────────┴────────────┘
                    │
                    ▼
            ┌─────────────┐
            │  SHUTDOWN   │
            └──────┬──────┘
                   │
                   ▼
            ┌─────────────┐
            │ TERMINATED  │
            └─────────────┘
```

---

## State Definitions

### CREATED

**Description:** Kernel instance created but not initialized.

**Entry Condition:** `Kernel()` constructor called.

**Exit Condition:** Bootstrap initiated.

**Allowed Operations:**
- Set configuration
- Register lifecycle callbacks
- Validate environment

**Forbidden Operations:**
- Access modules
- Start simulation
- Emit events

**Resources:** None allocated.

---

### BOOTING

**Description:** Kernel is bootstrapping.

**Entry Condition:** `kernel.bootstrap()` called.

**Exit Condition:** All modules discovered and registered.

**Allowed Operations:**
- Load configuration
- Discover modules
- Register modules
- Resolve dependencies

**Forbidden Operations:**
- Start simulation
- Process ticks
- Handle external requests

**Resources Allocated:**
- Configuration
- Module registry
- Dependency graph

---

### INITIALIZING

**Description:** Modules are being initialized.

**Entry Condition:** All modules registered, bootstrap complete.

**Exit Condition:** All modules initialized successfully.

**Allowed Operations:**
- Initialize modules in dependency order
- Allocate module resources
- Register services
- Setup event subscriptions

**Forbidden Operations:**
- Start simulation
- Process ticks

**Resources Allocated:**
- Module resources
- Service instances
- Event subscriptions

---

### READY

**Description:** Kernel and all modules are ready to run.

**Entry Condition:** All modules initialized.

**Exit Condition:** `kernel.start()` called or shutdown initiated.

**Allowed Operations:**
- Configure simulation
- Start simulation
- Query module status
- Register pre-simulation hooks

**Forbidden Operations:**
- Process simulation ticks
- Modify module initialization state

**Resources:** All allocated.

---

### RUNNING

**Description:** Simulation is actively running.

**Entry Condition:** `kernel.start()` called, first tick initiated.

**Exit Condition:** Pause, stop, error, or shutdown.

**Allowed Operations:**
- Process simulation ticks
- Handle module communication
- Record metrics
- Process events

**Forbidden Operations:**
- Initialize new modules
- Modify module registry

**Resources:** All in use.

---

### PAUSED

**Description:** Simulation is paused.

**Entry Condition:** `kernel.pause()` called during RUNNING.

**Exit Condition:** `kernel.resume()` or `kernel.stop()`.

**Allowed Operations:**
- Read simulation state
- Query modules
- Resume simulation
- Stop simulation

**Forbidden Operations:**
- Process new ticks
- Modify simulation state

**Resources:** All retained.

---

### RECOVERING

**Description:** Recovering from a module failure.

**Entry Condition:** Module error detected during RUNNING.

**Exit Condition:** Recovery complete or shutdown initiated.

**Allowed Operations:**
- Isolate failed module
- Attempt recovery
- Continue with degraded functionality
- Log recovery progress

**Forbidden Operations:**
- Process new ticks until stable
- Access failed module

**Resources:** Partial (healthy modules only).

---

### STOPPING

**Description:** Graceful shutdown in progress.

**Entry Condition:** `kernel.stop()` called.

**Exit Condition:** All modules stopped.

**Allowed Operations:**
- Stop modules in reverse dependency order
- Persist state
- Release resources
- Finalize shutdown

**Forbidden Operations:**
- Start new ticks
- Create new entities

**Resources:** Releasing.

---

### STOPPED

**Description:** All modules stopped, ready for shutdown or restart.

**Entry Condition:** Stopping complete.

**Exit Condition:** `kernel.shutdown()` or `kernel.start()`.

**Allowed Operations:**
- Query stopped state
- Restart (return to READY)
- Shutdown (proceed to SHUTDOWN)

**Forbidden Operations:**
- Process ticks
- Modify stopped modules

**Resources:** All retained.

---

### ERROR

**Description:** Non-fatal error detected.

**Entry Condition:** Recoverable error during RUNNING.

**Exit Condition:** Recovery attempted.

**Allowed Operations:**
- Log error details
- Attempt automatic recovery
- Notify health monitor
- Continue with degraded state

**Forbidden Operations:**
- Process new ticks until resolved
- Access erroring module

**Resources:** Partial.

---

### FAILED

**Description:** Unrecoverable error, shutdown required.

**Entry Condition:** Unrecoverable error detected.

**Exit Condition:** `kernel.shutdown()` initiated.

**Allowed Operations:**
- Log fatal error
- Preserve state for diagnostics
- Initiate forced shutdown

**Forbidden Operations:**
- Any simulation operations
- Module access

**Resources:** Frozen for diagnostics.

---

### SHUTDOWN

**Description:** Kernel is shutting down.

**Entry Condition:** `kernel.shutdown()` called from any state.

**Exit Condition:** All resources released.

**Allowed Operations:**
- Release all resources
- Finalize log entries
- Close file handles
- Exit process

**Forbidden Operations:**
- Create new objects
- Access modules

**Resources:** Releasing all.

---

### TERMINATED

**Description:** Kernel has fully terminated.

**Entry Condition:** Shutdown complete.

**Exit Condition:** Process exit.

**Allowed Operations:** None.

**Resources:** All released.

---

## State Transitions

### Valid Transitions

| From | To | Trigger | Condition |
|------|-----|---------|-----------|
| CREATED | BOOTING | bootstrap() | Config valid |
| BOOTING | INITIALIZING | bootstrap_complete | All deps resolved |
| INITIALIZING | READY | init_complete | All modules ok |
| READY | RUNNING | start() | At least one module |
| RUNNING | PAUSED | pause() | Simulation running |
| PAUSED | RUNNING | resume() | Pause successful |
| RUNNING | STOPPING | stop() | Normal stop |
| RUNNING | RECOVERING | module_error | Recoverable |
| RUNNING | ERROR | non_fatal_error | Error detected |
| RECOVERING | RUNNING | recovery_success | Module restored |
| RECOVERING | ERROR | recovery_failed | Cannot recover |
| RECOVERING | SHUTDOWN | recovery_impossible | Fatal |
| ERROR | RUNNING | error_resolved | Auto-recovery |
| ERROR | FAILED | error_fatal | Cannot recover |
| STOPPING | STOPPED | stop_complete | All stopped |
| STOPPED | READY | restart() | Clean restart |
| STOPPED | SHUTDOWN | shutdown() | Final shutdown |
| FAILED | SHUTDOWN | shutdown() | Must cleanup |
| SHUTDOWN | TERMINATED | shutdown_complete | All released |

### Forbidden Transitions

| From | To | Reason |
|------|-----|--------|
| CREATED | RUNNING | Must bootstrap first |
| TERMINATED | * | Cannot transition |
| FAILED | RUNNING | Must shutdown |
| SHUTDOWN | RUNNING | Cannot restart from shutdown |
| STOPPING | RUNNING | Must complete stop |

---

## Transition Callbacks

```python
class KernelCallbacks:
    """Callbacks for kernel state transitions."""
    
    def on_booting(self) -> None:
        """Called when entering BOOTING."""
        pass
    
    def on_booted(self) -> None:
        """Called when exiting BOOTING."""
        pass
    
    def on_initializing(self) -> None:
        """Called when entering INITIALIZING."""
        pass
    
    def on_initialized(self) -> None:
        """Called when exiting INITIALIZING."""
        pass
    
    def on_ready(self) -> None:
        """Called when entering READY."""
        pass
    
    def on_running(self) -> None:
        """Called when entering RUNNING."""
        pass
    
    def on_pausing(self) -> None:
        """Called when entering PAUSED."""
        pass
    
    def on_resuming(self) -> None:
        """Called when exiting PAUSED."""
        pass
    
    def on_stopping(self) -> None:
        """Called when entering STOPPING."""
        pass
    
    def on_stopped(self) -> None:
        """Called when entering STOPPED."""
        pass
    
    def on_recovering(self) -> None:
        """Called when entering RECOVERING."""
        pass
    
    def on_error(self, error: Exception) -> None:
        """Called when entering ERROR."""
        pass
    
    def on_failed(self, error: Exception) -> None:
        """Called when entering FAILED."""
        pass
    
    def on_shutting_down(self) -> None:
        """Called when entering SHUTDOWN."""
        pass
    
    def on_terminated(self) -> None:
        """Called when entering TERMINATED."""
        pass
```

---

## Recovery Paths

### Path 1: Module Recovery

```
RUNNING
    │
    ▼
RECOVERING (module X failed)
    │
    ├─→ Can recover X?
    │       │
    │   Yes ├─→ Retry initialization
    │       │       │
    │       │   Success → RUNNING
    │       │   Fail → ERROR
    │       │
    │   No ├─→ Isolate X
    │           │
    │       Continue without X → RUNNING (degraded)
    │
    └─→ Fatal error?
            │
        Yes → FAILED → SHUTDOWN
```

### Path 2: Error Recovery

```
RUNNING
    │
    ▼
ERROR (non-fatal error)
    │
    ├─→ Auto-fixable?
    │       │
    │   Yes ├─→ Apply fix → RUNNING
    │       │
    │   No ├─→ Notify
    │           │
    │       User action → RUNNING or SHUTDOWN
    │
    └─→ Fatal?
            │
        Yes → FAILED → SHUTDOWN
```

### Path 3: Panic Recovery

```
RUNNING
    │
    ▼
KERNEL_PANIC (critical error)
    │
    ├─→ Log critical state
    │
    ├─→ Preserve state for diagnostics
    │
    └─→ Force shutdown → TERMINATED
```

---

## Failure Modes

### Mode 1: Module Crash

**Detection:** Exception in module callback.

**Response:** Enter RECOVERING, attempt module restart.

**Resolution:**
- Success: Return to RUNNING
- Fail: Isolate module, return to RUNNING (degraded)
- Fatal: Enter SHUTDOWN

### Mode 2: Resource Exhaustion

**Detection:** Memory/error limits exceeded.

**Response:** Enter RECOVERING, attempt cleanup.

**Resolution:**
- Success: Return to RUNNING
- Fail: Enter SHUTDOWN

### Mode 3: Dependency Failure

**Detection:** Required dependency unavailable.

**Response:** Enter ERROR, attempt resolution.

**Resolution:**
- Success: Return to RUNNING
- Fail: Enter SHUTDOWN

### Mode 4: Kernel Panic

**Detection:** Critical internal error.

**Response:** Enter FAILED, force shutdown.

**Resolution:** Process termination.

---

## State Validation

### Pre-Transition Validation

Before any transition:
1. Verify current state allows transition
2. Validate transition preconditions
3. Check required resources
4. Verify permissions

### Post-Transition Validation

After any transition:
1. Verify new state reached
2. Validate state invariants
3. Check resource allocation
4. Verify consistency

### Invariants

| State | Invariant |
|-------|-----------|
| CREATED | No resources allocated |
| BOOTING | Configuration valid |
| INITIALIZING | Modules being initialized |
| READY | All modules initialized |
| RUNNING | Tick processing active |
| PAUSED | Tick processing paused |
| RECOVERING | Some modules unhealthy |
| STOPPING | Modules shutting down |
| STOPPED | All modules stopped |
| SHUTDOWN | Resources releasing |
| TERMINATED | All resources released |

---

## Summary

| State | Purpose | Recovery | Resources |
|-------|---------|----------|-----------|
| CREATED | Initial | N/A | None |
| BOOTING | Bootstrap | Retry | Config |
| INITIALIZING | Module setup | Retry | Partial |
| READY | Prepared | Restart | All |
| RUNNING | Active | Depends | All |
| PAUSED | Suspended | Resume | All |
| RECOVERING | Error handling | Recovery | Partial |
| STOPPING | Cleanup | N/A | Releasing |
| STOPPED | Halted | Restart | All |
| ERROR | Non-fatal error | Fix | Partial |
| FAILED | Fatal error | Shutdown | Frozen |
| SHUTDOWN | Teardown | N/A | Releasing |
| TERMINATED | Done | N/A | None |
