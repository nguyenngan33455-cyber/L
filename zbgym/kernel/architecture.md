# ZBGym Kernel Architecture

## Overview

The Kernel is the **central coordinator** of ZBGym. It is responsible for:

- Framework lifecycle management
- Module communication
- Scheduling and tick coordination
- Dependency management
- Runtime orchestration

The Kernel **ONLY coordinates**. It does not execute gameplay, AI logic, physics, or rewards.

---

## Kernel Responsibilities

### The Kernel SHALL:

1. **Bootstrap Framework**
   - Initialize runtime context
   - Load configuration
   - Register modules

2. **Shutdown Framework**
   - Graceful shutdown
   - Resource cleanup
   - State persistence

3. **Coordinate Module Lifecycle**
   - Manage module states
   - Validate transitions
   - Handle errors

4. **Route Events**
   - Central event dispatcher
   - Deterministic ordering
   - No direct forwarding

5. **Dispatch Commands**
   - Command routing
   - Permission checking
   - Response handling

6. **Synchronize Tick Order**
   - Execute tick pipeline
   - Phase ordering
   - Timing control

7. **Maintain RuntimeContext**
   - Module references
   - Service registry
   - State management

8. **Register Modules**
   - Module discovery
   - Capability registration
   - Dependency tracking

9. **Resolve Dependencies**
   - Build dependency graph
   - Validate cycles
   - Load ordering

10. **Perform Health Monitoring**
    - Module health checks
    - Performance metrics
    - Error reporting

### The Kernel SHALL NOT:

- Execute gameplay logic
- Execute AI decisions
- Calculate physics
- Calculate rewards
- Modify replay data
- Access module internals

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           ZBGym Kernel                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │  Lifecycle  │  │   Module   │  │ Dependency │  │  Event   │ │
│  │  Manager    │  │   Manager  │  │  Resolver  │  │ Dispatch │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘ │
│         │                │                │                │        │
│         └────────────────┴────────────────┴────────────────┘        │
│                               │                                     │
│                    ┌──────────▼──────────┐                        │
│                    │   RuntimeContext    │                        │
│                    └──────────┬──────────┘                        │
│                               │                                     │
│  ┌─────────────┐  ┌──────────▼──────────┐  ┌─────────────┐       │
│  │   Health    │  │     Service         │  │  Metrics    │       │
│  │   Monitor   │  │     Registry       │  │  Collector  │       │
│  └─────────────┘  └────────────────────┘  └─────────────┘       │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                           Modules                                    │
│                                                                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ Engine  │  │Physics  │  │   AI    │  │ Replay  │  │Dashboard│  │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  │
│       │            │            │            │            │        │
│       └────────────┴─────┬──────┴────────────┴────────────┘        │
│                          │                                          │
│                 ┌─────────▼─────────┐                               │
│                 │  TickCoordinator │                                │
│                 └──────────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Kernel Components

### 1. LifecycleManager

Manages framework and module lifecycles.

**Responsibilities:**
- Boot sequence orchestration
- Shutdown handling
- State machine validation
- Error recovery

### 2. ModuleManager

Manages module registration and lifecycle.

**Responsibilities:**
- Module discovery
- Capability tracking
- Lifecycle state management
- Module isolation

### 3. DependencyResolver

Resolves module dependencies.

**Responsibilities:**
- Build dependency graph
- Detect cycles
- Compute load order
- Validate compatibility

### 4. EventDispatcher

Central event routing.

**Responsibilities:**
- Event queuing
- Subscriber management
- Deterministic ordering
- Event filtering

### 5. TickCoordinator

Coordinates simulation tick execution.

**Responsibilities:**
- Phase ordering
- Timing control
- Synchronization
- Progress tracking

### 6. HealthMonitor

Monitors system health.

**Responsibilities:**
- Module health checks
- Performance monitoring
- Error detection
- Alert generation

### 7. ServiceRegistry

Manages module services.

**Responsibilities:**
- Service registration
- Service discovery
- Dependency injection
- Lifecycle binding

### 8. MetricsCollector

Collects runtime metrics.

**Responsibilities:**
- Performance counters
- Resource usage
- Tick statistics
- Event metrics

---

## Communication Rules

### Module Communication

Modules **CANNOT** communicate directly. All communication must go through the Kernel.

```
✓ Valid:
Dashboard → Kernel → AI
Engine → Kernel → Physics
Replay → Kernel → Dashboard

✗ Invalid:
Dashboard → AI (direct)
Physics → Replay (direct)
Engine → Dashboard (direct)
```

### Service Access

Modules access services through RuntimeContext.

```python
# Module receives RuntimeContext
class MyModule:
    def __init__(self, context: RuntimeContext):
        self._context = context
    
    def do_something(self):
        # Access services through context
        event_bus = self._context.event_bus
        scheduler = self._context.scheduler
```

### Event Flow

All events flow through EventDispatcher.

```
Producer → Kernel Dispatcher → Subscribers
```

No direct event forwarding between modules.

---

## Error Policy

### Module Failure Handling

```
Module Failure
      ↓
Kernel catches exception
      ↓
Log error with context
      ↓
Mark module as unhealthy
      ↓
Isolate module (stop dispatching)
      ↓
Continue simulation if possible
      ↓
Report to HealthMonitor
```

### Recovery Strategies

1. **Retry**: Re-initialize module
2. **Fallback**: Use default implementation
3. **Isolate**: Continue without module
4. **Shutdown**: Stop simulation gracefully

### Kernel Failure

Kernel failure is **unrecoverable**. The framework must shutdown.

---

## Performance Considerations

### Kernel Overhead

Kernel operations must be:
- O(1) or O(log n) for common operations
- Deterministic execution time
- Minimal memory allocation

### Bottlenecks

Avoid:
- Lock contention
- Excessive copying
- Blocking operations
- Memory fragmentation

---

## Security Considerations

### Module Isolation

Modules are isolated through:
- Sandboxed execution
- Restricted imports
- Resource limits
- Permission system

### Access Control

Kernel validates:
- Service access permissions
- Event subscription rights
- Configuration modifications
- Lifecycle operations

---

## Extension Points

### Plugin Integration

Plugins integrate through:
- Hook system
- Service registration
- Capability declaration
- Lifecycle callbacks

### Custom Modules

Custom modules must:
- Implement ModuleInterface
- Declare capabilities
- Follow lifecycle protocol
- Register with Kernel

---

## Implementation Guidelines

### Thread Safety

Kernel must be thread-safe:
- Use locks for shared state
- Avoid deadlocks
- Minimize critical sections
- Document lock ordering

### Memory Management

- No memory leaks
- Resource cleanup on shutdown
- Bounded queues
- Pooled allocations

### Logging

- Structured logging
- Context preservation
- Performance impact minimized
- Configurable verbosity

---

## Future Extensions

### Planned Features

1. **Distributed Kernel**: Multi-process coordination
2. **Hot Reload**: Module reloading without restart
3. **Remote Modules**: Network-based module execution
4. **Transaction Support**: Atomic multi-module operations

---

## Summary

The Kernel is the **single source of truth** for ZBGym coordination.

Key principles:
1. Kernel coordinates, modules execute
2. All communication through Kernel
3. Deterministic, reproducible behavior
4. Graceful degradation on errors
5. No direct module-to-module communication

This architecture enables:
- Modular design
- Testability
- Extensibility
- Determinism
- Reliability
