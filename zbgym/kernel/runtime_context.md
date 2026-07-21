# ZBGym RuntimeContext

## Overview

RuntimeContext is the **single source of truth** for framework state and services. Every module receives RuntimeContext - no module stores global references.

---

## Design Principles

1. **Dependency Injection**: Modules receive dependencies, don't fetch them
2. **Immutable After Creation**: RuntimeContext is created once at boot
3. **Service Access**: All services accessible through context
4. **No Global State**: No module globals, singletons, or registries
5. **Type Safety**: Strong typing for all context properties

---

## RuntimeContext Structure

```python
@dataclass
class RuntimeContext:
    """
    Central context for framework runtime.
    
    Provides access to all framework services and state.
    """
    
    # Configuration
    config: Configuration
    
    # Core Services
    event_bus: EventBus
    scheduler: TickScheduler
    clock: Clock
    logger: Logger
    
    # Module References
    engine: Engine
    physics: PhysicsEngine
    ai: AISystem
    replay: ReplaySystem
    dashboard: Dashboard
    
    # Plugin System
    plugin_registry: PluginRegistry
    hook_system: HookSystem
    
    # State Management
    state_store: StateStore
    metrics: MetricsCollector
    health_monitor: HealthMonitor
    
    # Lifecycle
    lifecycle_manager: LifecycleManager
    module_manager: ModuleManager
```

---

## Service Access

### Pattern: Constructor Injection

```python
class MyModule:
    """Example module using RuntimeContext."""
    
    def __init__(self, context: RuntimeContext) -> None:
        self._context = context
        self._event_bus = context.event_bus
        self._scheduler = context.scheduler
        self._config = context.config
    
    def initialize(self) -> None:
        """Initialize module."""
        # Subscribe to events
        self._event_bus.subscribe(
            EventType.TICK_END,
            self.on_tick_end
        )
    
    def on_tick_end(self, event: Event) -> None:
        """Handle tick end event."""
        # Access services through context
        tick = self._context.scheduler.current_tick
```

### Pattern: Property Access

```python
class MyModule:
    def __init__(self, context: RuntimeContext) -> None:
        self._context = context
    
    @property
    def event_bus(self) -> EventBus:
        return self._context.event_bus
    
    @property
    def config(self) -> Configuration:
        return self._context.config
```

---

## Module References

### Accessing Modules

```python
class MyModule:
    def __init__(self, context: RuntimeContext) -> None:
        self._context = context
    
    def access_other_module(self) -> None:
        # Access engine
        engine = self._context.engine
        
        # Access physics
        physics = self._context.physics
        
        # Access AI
        ai = self._context.ai
        
        # Access replay
        replay = self._context.replay
        
        # Access dashboard
        dashboard = self._context.dashboard
```

### Module Communication

**ALL communication goes through Kernel/event_bus:**

```python
class ModuleA:
    def __init__(self, context: RuntimeContext) -> None:
        self._context = context
    
    def request_from_b(self) -> None:
        # Send event - do NOT call ModuleB directly
        self._context.event_bus.emit(
            Event(type="module_a_request"),
            target="module_b"
        )

class ModuleB:
    def __init__(self, context: RuntimeContext) -> None:
        self._context = context
        self._context.event_bus.subscribe(
            "module_a_request",
            self.handle_request
        )
    
    def handle_request(self, event: Event) -> None:
        # Handle request through event
        pass
```

---

## Configuration Access

```python
@dataclass
class Configuration:
    """Framework configuration."""
    
    # Environment
    tick_rate: int = 60
    map_width: int = 1000
    map_height: int = 1000
    
    # Physics
    gravity: float = 9.81
    friction: float = 0.98
    
    # AI
    ai_tick_rate: int = 10
    max_actions: int = 100
    
    # Replay
    replay_enabled: bool = True
    replay_compression: str = "gzip"
    
    # Plugins
    plugin_dirs: list[str] = field(default_factory=list)
    plugin_safe_mode: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_file: str | None = None
    
    # Metrics
    metrics_enabled: bool = True
    metrics_interval: float = 1.0
```

---

## State Store

```python
class StateStore:
    """
    Thread-safe state storage.
    
    Modules store and retrieve state through this interface.
    """
    
    def get(self, key: str) -> Any:
        """Get state value."""
        pass
    
    def set(self, key: str, value: Any) -> None:
        """Set state value."""
        pass
    
    def delete(self, key: str) -> None:
        """Delete state value."""
        pass
    
    def snapshot(self) -> dict[str, Any]:
        """Create state snapshot."""
        pass
    
    def restore(self, snapshot: dict[str, Any]) -> None:
        """Restore from snapshot."""
        pass
    
    def clear(self) -> None:
        """Clear all state."""
        pass
```

### Usage

```python
class MyModule:
    def __init__(self, context: RuntimeContext) -> None:
        self._context = context
        self._state = context.state_store
    
    def save_state(self) -> None:
        self._state.set("my_module.counter", 42)
    
    def load_state(self) -> int:
        return self._state.get("my_module.counter", default=0)
```

---

## Metrics Access

```python
class MetricsCollector:
    """Collects runtime metrics."""
    
    def increment(self, name: str, value: int = 1) -> None:
        """Increment counter."""
        pass
    
    def gauge(self, name: str, value: float) -> None:
        """Set gauge value."""
        pass
    
    def timing(self, name: str, duration_ms: float) -> None:
        """Record timing."""
        pass
    
    def histogram(self, name: str, value: float) -> None:
        """Record histogram value."""
        pass
    
    def get_metrics(self) -> dict[str, Any]:
        """Get all metrics."""
        pass
```

### Usage

```python
class MyModule:
    def __init__(self, context: RuntimeContext) -> None:
        self._context = context
        self._metrics = context.metrics
    
    def record_action(self) -> None:
        self._metrics.increment("my_module.actions")
        self._metrics.gauge("my_module.active", 1)
```

---

## Health Monitoring

```python
class HealthMonitor:
    """Monitors system health."""
    
    def register_check(
        self,
        name: str,
        check: Callable[[], bool]
    ) -> None:
        """Register health check."""
        pass
    
    def unregister_check(self, name: str) -> None:
        """Unregister health check."""
        pass
    
    def check_health(self) -> HealthReport:
        """Run all health checks."""
        pass
    
    def get_module_health(self, module: str) -> HealthStatus:
        """Get specific module health."""
        pass
    
    def subscribe(
        self,
        callback: Callable[[HealthReport], None]
    ) -> None:
        """Subscribe to health updates."""
        pass
```

---

## Clock

```python
class Clock:
    """Framework clock."""
    
    @property
    def current_tick(self) -> int:
        """Current simulation tick."""
        pass
    
    @property
    def elapsed_time(self) -> float:
        """Elapsed real time in seconds."""
        pass
    
    @property
    def simulation_time(self) -> float:
        """Elapsed simulation time."""
        pass
    
    @property
    def tick_rate(self) -> float:
        """Target tick rate."""
        pass
    
    @property
    def delta_time(self) -> float:
        """Time since last tick."""
        pass
    
    def sleep_until(self, target_tick: int) -> None:
        """Sleep until target tick."""
        pass
```

---

## Event Bus Access

```python
class EventBus:
    """Central event dispatcher."""
    
    def subscribe(
        self,
        event_type: EventType | str,
        callback: Callable[[Event], None],
        filter_fn: Callable[[Event], bool] | None = None,
        priority: int = 0,
    ) -> str:
        """Subscribe to event."""
        pass
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from event."""
        pass
    
    def emit(
        self,
        event: Event | EventType | str,
        **data: Any
    ) -> Event:
        """Emit event."""
        pass
    
    def get_history(
        self,
        event_type: EventType | str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """Get event history."""
        pass
```

---

## Service Registry

```python
class ServiceRegistry:
    """Registry for module services."""
    
    def register(
        self,
        service_type: type,
        implementation: Any,
        lifecycle: LifecycleBinding = LifecycleBinding.SINGLETON,
    ) -> None:
        """Register service."""
        pass
    
    def get(self, service_type: type) -> Any:
        """Get service instance."""
        pass
    
    def unregister(self, service_type: type) -> None:
        """Unregister service."""
        pass
    
    def has(self, service_type: type) -> bool:
        """Check if service registered."""
        pass
```

---

## Validation

RuntimeContext validates:

1. **Immutability**: Cannot modify after creation
2. **Completeness**: All required fields populated
3. **Type Safety**: Correct types for all fields
4. **Cycles**: No circular dependencies
5. **Null Checks**: No None values for required fields

---

## Thread Safety

RuntimeContext is **immutable after creation**, making it inherently thread-safe for reads. All writes happen during bootstrap.

Modules accessing RuntimeContext must:
1. Not cache mutable references
2. Not store context in globals
3. Pass context to worker threads explicitly

---

## Summary

RuntimeContext design principles:

1. **Single Source of Truth**: All services in one place
2. **Dependency Injection**: Modules receive, not fetch
3. **Immutability**: Context created once, never modified
4. **Type Safety**: Strong typing throughout
5. **No Globals**: No module globals or singletons
6. **Thread Safety**: Immutable after creation
7. **Complete Access**: All framework services available
