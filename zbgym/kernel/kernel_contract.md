# ZBGym Kernel Contract

## Overview

This document defines the **contract** between the Kernel and all other components. The Kernel guarantees certain behaviors. In return, modules must follow certain rules.

---

## Kernel Guarantees

### 1. Deterministic Execution

**Guarantee:** Given the same initial state and inputs, the Kernel will produce the same sequence of states and outputs.

**Conditions:**
- Same configuration
- Same seed (if applicable)
- Same input sequence
- No non-deterministic external factors

**Verification:**
```python
# Run 1
kernel1 = Kernel(config, seed=42)
result1 = kernel1.run(episodes=10)

# Run 2
kernel2 = Kernel(config, seed=42)
result2 = kernel2.run(episodes=10)

# Guarantees
assert result1.states == result2.states  # Identical states
assert result1.actions == result2.actions  # Identical actions
assert result1.rewards == result2.rewards  # Identical rewards
```

---

### 2. Lifecycle Ordering

**Guarantee:** Modules are initialized, started, stopped, and shutdown in a deterministic order based on their dependencies.

**Conditions:**
- Valid dependency graph
- No circular dependencies
- All required dependencies available

**Guaranteed Order:**
```
Initialize:  Dependency → Dependent
Stop:        Dependent → Dependency
Shutdown:    Dependency → Dependent
```

**Example:**
```
Dependencies: A → B → C (C depends on B, B depends on A)

Initialization Order:  A, B, C
Shutdown Order:        C, B, A
```

---

### 3. Dependency Resolution

**Guarantee:** The Kernel will resolve all dependencies and report any resolution failures before modules are initialized.

**Conditions:**
- All dependencies declared correctly
- Version requirements met
- Required modules available

**Guaranteed Behavior:**
```python
# Resolution happens during bootstrap
# Before any initialization occurs
kernel.bootstrap()

# If resolution fails, exception is raised
# No modules are initialized
```

---

### 4. Service Availability

**Guarantee:** When a module receives its initialization callback, all declared dependencies are available through RuntimeContext.

**Conditions:**
- Module declares dependencies correctly
- Dependencies are required (not optional)

**Guaranteed Behavior:**
```python
class MyModule:
    def initialize(self, context: RuntimeContext):
        # GUARANTEED: context.engine exists
        # GUARANTEED: context.event_bus exists
        # GUARANTEED: context.physics exists
        
        engine = context.engine  # Always available
```

---

### 5. Event Ordering

**Guarantee:** Events are delivered to subscribers in deterministic order based on priority.

**Conditions:**
- Subscribers registered with priority
- Events emitted with timestamp
- No concurrent event emission

**Guaranteed Order:**
```python
# Priority order (higher = first)
Priority 100 → Priority 50 → Priority 0

# Same priority: FIFO
Event1 → Event2 → Event3 (if same priority)
```

---

### 6. Runtime Synchronization

**Guarantee:** The Kernel ensures proper synchronization between modules accessing shared resources.

**Conditions:**
- Proper use of RuntimeContext
- No direct module-to-module communication
- Thread-safe module implementations

**Guaranteed Behavior:**
```python
# Kernel synchronizes access to:
# - EventBus
# - StateStore
# - Module registry
# - Service registry
```

---

### 7. Tick Ordering

**Guarantee:** Tick pipeline stages execute in the exact order defined, with proper hook integration.

**Conditions:**
- Standard tick pipeline
- No stage skipping (unless configured)

**Guaranteed Order:**
```
1. PREPARE → 2. SCHEDULER → 3. AI → 4. ACTIONS → ...
```

---

### 8. Graceful Degradation

**Guarantee:** The Kernel will continue operating (in degraded mode) if non-critical modules fail.

**Conditions:**
- Failed module is non-critical
- Recovery is possible

**Guaranteed Behavior:**
```python
# If dashboard fails:
# - Simulation continues
# - Replay continues
# - AI continues
# - Only dashboard features unavailable
```

---

### 9. Health Monitoring

**Guarantee:** The Kernel provides accurate health status for all modules.

**Conditions:**
- Modules implement health checks
- Health checks are responsive

**Guaranteed Behavior:**
```python
report = kernel.health_monitor.check_health()

# Report contains:
# - Module health status
# - Error information
# - Recovery recommendations
```

---

### 10. Configuration Validation

**Guarantee:** Invalid configuration is detected and reported before any initialization.

**Conditions:**
- Configuration schema is correct
- Required fields present

**Guaranteed Behavior:**
```python
kernel = Kernel(config)

# If config invalid:
kernel.bootstrap()  # Raises ConfigurationError
# No initialization occurs
```

---

## Kernel Does NOT Guarantee

### 1. Gameplay Correctness

```
Kernel does NOT guarantee:
- Game rules are correctly implemented
- Win/lose conditions are accurate
- Character behavior is correct
```

**Module Responsibility:** Engine, Game Logic

---

### 2. AI Intelligence

```
Kernel does NOT guarantee:
- AI produces optimal decisions
- AI learns correctly
- AI behavior is sensible
```

**Module Responsibility:** AI System

---

### 3. Reward Quality

```
Kernel does NOT guarantee:
- Rewards are meaningful
- Rewards drive correct behavior
- Reward shaping is appropriate
```

**Module Responsibility:** Reward System

---

### 4. Rendering Quality

```
Kernel does NOT guarantee:
- Visuals are correct
- Performance is adequate
- User experience is good
```

**Module Responsibility:** Dashboard, Renderer

---

### 5. Physics Accuracy

```
Kernel does NOT guarantee:
- Physics simulations are accurate
- Collisions are correct
- Bodies behave realistically
```

**Module Responsibility:** Physics Engine

---

### 6. Module Internal Behavior

```
Kernel does NOT guarantee:
- Module implementation is correct
- Module is bug-free
- Module follows its contract
```

**Module Responsibility:** Each module developer

---

### 7. External Dependencies

```
Kernel does NOT guarantee:
- Network connectivity
- File system availability
- System resources
```

**Module Responsibility:** Handle external failures

---

### 8. Data Persistence

```
Kernel does NOT guarantee:
- Data is correctly saved
- Saves are not corrupted
- Recovery from saves works
```

**Module Responsibility:** Replay, State Management

---

## Module Contract

### Requirements

Modules MUST:

1. **Declare Dependencies**
   ```python
   @staticmethod
   def get_dependencies() -> list[str]:
       return ["engine", "physics"]
   ```

2. **Implement Lifecycle Callbacks**
   ```python
   def initialize(self, context: RuntimeContext) -> None: ...
   def start(self) -> None: ...
   def stop(self) -> None: ...
   def shutdown(self) -> None: ...
   ```

3. **Report Health**
   ```python
   def health_check(self) -> bool:
       return self.is_healthy
   ```

4. **Use RuntimeContext**
   ```python
   # ✓ Correct
   context.event_bus.emit(...)
   
   # ✗ Incorrect
   global_event_bus.emit(...)
   ```

5. **Handle Errors**
   ```python
   def on_error(self, error: Exception) -> None:
       self._logger.error(f"Error: {error}")
       self._healthy = False
   ```

6. **Release Resources**
   ```python
   def shutdown(self) -> None:
       self._cleanup()
       self._socket.close()
   ```

---

### Forbidden Actions

Modules MUST NOT:

1. **Direct Module-to-Module Communication**
   ```python
   # ✗ Forbidden
   other_module.do_something()
   
   # ✓ Correct
   context.event_bus.emit("module_action", target="other")
   ```

2. **Access Undeclared Dependencies**
   ```python
   # ✗ Forbidden
   engine = context.engine  # If not declared
   
   # ✓ Correct
   # Declare in get_dependencies() first
   ```

3. **Access Module Internals**
   ```python
   # ✗ Forbidden
   engine._internal_state
   
   # ✓ Correct
   # Use public API only
   ```

4. **Create Threads**
   ```python
   # ✗ Forbidden
   threading.Thread(...)
   
   # ✓ Correct
   # Use Kernel's async mechanisms
   ```

5. **Access Global State**
   ```python
   # ✗ Forbidden
   global_config.set(...)
   
   # ✓ Correct
   context.config.get(...)
   ```

6. **Modify Kernel State**
   ```python
   # ✗ Forbidden
   kernel._internal_state = ...
   
   # ✓ Correct
   # Use documented APIs only
   ```

7. **Block Tick Processing**
   ```python
   # ✗ Forbidden
   time.sleep(1)  # In tick callback
   
   # ✓ Correct
   # Operations must complete in < 1ms
   ```

---

## API Stability Contract

### Stable APIs

The following APIs are stable and will not change without major version bump:

```python
RuntimeContext.config          # Configuration
RuntimeContext.event_bus      # EventBus
RuntimeContext.scheduler       # TickScheduler
RuntimeContext.health_monitor  # HealthMonitor
RuntimeContext.state_store     # StateStore
RuntimeContext.metrics         # MetricsCollector

Kernel.bootstrap()              # Bootstrap
Kernel.start()                  # Start
Kernel.pause()                  # Pause
Kernel.resume()                 # Resume
Kernel.stop()                   # Stop
Kernel.shutdown()               # Shutdown
```

### Experimental APIs

The following APIs are experimental and may change:

```python
RuntimeContext.plugin_registry  # Plugin system
RuntimeContext.hook_system      # Hook system
Kernel.reload_module()           # Hot reload
```

### Internal APIs

The following are internal and MUST NOT be used by modules:

```python
Kernel._internal_state
Kernel._module_manager
Module._kernel_reference
EventBus._dispatcher
```

---

## Version Contract

### Semantic Versioning

```
Kernel Version: major.minor.patch

major: Breaking changes (requires migration)
minor: New features (backward compatible)
patch: Bug fixes (backward compatible)
```

### Compatibility Matrix

| Module Version | Kernel 1.0 | Kernel 1.1 | Kernel 2.0 |
|----------------|-------------|------------|------------|
| Module 1.0    | ✓           | ✓          | ✗          |
| Module 1.1    | ✗           | ✓          | ✗          |
| Module 2.0    | ✗           | ✗          | ✓          |

---

## Error Handling Contract

### Kernel Errors

| Error | Behavior | Module Notified |
|-------|----------|-----------------|
| ConfigurationError | Bootstrap fails | N/A |
| DependencyError | Bootstrap fails | N/A |
| ModuleInitError | Kernel tries recovery | Yes |
| ModuleRuntimeError | Kernel isolates | Yes |
| FatalError | Kernel shuts down | Yes |

### Module Errors

| Error | Kernel Behavior | Guaranteed |
|-------|-----------------|------------|
| Non-fatal | Continue (degraded) | Yes |
| Fatal | Shutdown | Yes |
| Timeout | Isolate | Yes |
| Resource exhaust | Recover or shutdown | Yes |

---

## Summary

### Kernel Guarantees (Immutable)

| Guarantee | Description |
|-----------|-------------|
| Determinism | Same input = same output |
| Lifecycle ordering | Dependency-based order |
| Dependency resolution | Pre-initialization |
| Service availability | Declared deps available |
| Event ordering | Priority-based |
| Synchronization | Thread-safe access |
| Tick ordering | Pipeline order |
| Graceful degradation | Non-critical failures isolated |
| Health monitoring | Accurate status |
| Config validation | Pre-initialization |

### Module Responsibilities (Immutable)

| Responsibility | Description |
|----------------|-------------|
| Declare deps | List all dependencies |
| Implement lifecycle | All callbacks required |
| Report health | Accurate health status |
| Use context | Access via RuntimeContext |
| Handle errors | Internal error handling |
| Release resources | Proper cleanup |

### What Kernel Does NOT Guarantee

| Item | Owner |
|------|-------|
| Gameplay correctness | Engine |
| AI intelligence | AI System |
| Reward quality | Reward System |
| Rendering | Dashboard |
| Physics accuracy | Physics |
| Module correctness | Module |
| External dependencies | Module |
| Data persistence | Replay |
