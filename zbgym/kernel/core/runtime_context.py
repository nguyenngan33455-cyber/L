"""
RuntimeContext implementation for ZBGym Kernel.

RuntimeContext is the single source of truth for framework state and services.
Every module receives RuntimeContext - no module stores global references.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from zbgym.config import ZBGymConfig
    from zbgym.engine.event_bus import EventBus
    from zbgym.engine.tick_system import TickSystem
    from zbgym.physics.vector import Vector2D
    from zbgym.physics.body import PhysicsBody
    from zbgym.ai.scheduler.scheduler import AIScheduler
    from zbgym.replay.recorder import ReplayRecorder
    from zbgym.dashboard.dashboard import Dashboard
    from zbgym.plugin_sdk.registry import PluginRegistry
    from zbgym.plugin_sdk.hooks import HookSystem
    from zbgym.kernel.core.state_store import StateStore
    from zbgym.kernel.core.health_monitor import HealthMonitor
    from zbgym.kernel.core.metrics_collector import MetricsCollector
    import logging


@dataclass
class RuntimeContext:
    """
    Central context for framework runtime.
    
    Provides access to all framework services and state.
    All modules receive RuntimeContext through dependency injection.
    No global state. No singletons.
    
    Attributes:
        config: Framework configuration
        clock: Framework clock
        event_bus: Central event dispatcher
        scheduler: Tick scheduler
        engine: Game engine
        physics: Physics engine
        ai: AI system
        replay: Replay system
        dashboard: Dashboard
        plugin_registry: Plugin registry
        hook_system: Hook system
        state_store: State store
        metrics: Metrics collector
        health_monitor: Health monitor
        logger: Logger
    """

    config: ZBGymConfig | None = None
    clock: Clock | None = None
    event_bus: EventBus | None = None
    scheduler: TickSystem | None = None
    engine: Any = None
    physics: Any = None
    ai: AIScheduler | None = None
    replay: ReplayRecorder | None = None
    dashboard: Dashboard | None = None
    plugin_registry: PluginRegistry | None = None
    hook_system: HookSystem | None = None
    state_store: StateStore | None = None
    metrics: MetricsCollector | None = None
    health_monitor: HealthMonitor | None = None
    logger: logging.Logger | None = None

    _initialized: bool = field(default=False, repr=False)
    _modules: dict[str, Any] = field(default_factory=dict, repr=False)

    def initialize(self) -> None:
        """Initialize RuntimeContext and all services."""
        if self._initialized:
            raise RuntimeError("RuntimeContext already initialized")

        # Create default clock if not provided
        if self.clock is None:
            self.clock = Clock()

        # Create default event bus if not provided
        if self.event_bus is None:
            from zbgym.engine.event_bus import EventBus
            self.event_bus = EventBus()

        # Create default state store if not provided
        if self.state_store is None:
            from zbgym.kernel.core.state_store import StateStore
            self.state_store = StateStore()

        # Create default health monitor if not provided
        if self.health_monitor is None:
            from zbgym.kernel.core.health_monitor import HealthMonitor
            self.health_monitor = HealthMonitor(self.event_bus)

        # Create default metrics collector if not provided
        if self.metrics is None:
            from zbgym.kernel.core.metrics_collector import MetricsCollector
            self.metrics = MetricsCollector()

        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown RuntimeContext and all services."""
        if not self._initialized:
            return

        # Shutdown services in reverse order
        if self.health_monitor:
            try:
                self.health_monitor.shutdown()
            except Exception:
                pass

        if self.metrics:
            try:
                self.metrics.shutdown()
            except Exception:
                pass

        if self.state_store:
            try:
                self.state_store.shutdown()
            except Exception:
                pass

        self._modules.clear()
        self._initialized = False

    def register_module(self, name: str, module: Any) -> None:
        """Register a module with RuntimeContext."""
        self._modules[name] = module

    def get_module(self, name: str) -> Any | None:
        """Get a registered module by name."""
        return self._modules.get(name)

    @property
    def is_initialized(self) -> bool:
        """Check if RuntimeContext is initialized."""
        return self._initialized

    def snapshot(self) -> dict[str, Any]:
        """Create a snapshot of RuntimeContext state."""
        return {
            "initialized": self._initialized,
            "modules": list(self._modules.keys()),
            "config": self.config.__dict__ if self.config else None,
        }


class Clock:
    """
    Framework clock for time tracking.
    
    Tracks simulation tick, elapsed time, and provides timing utilities.
    """

    def __init__(self) -> None:
        """Initialize the clock."""
        self._tick: int = 0
        self._start_time: float = 0.0
        self._pause_time: float = 0.0
        self._paused: bool = False
        self._tick_rate: float = 60.0

    @property
    def current_tick(self) -> int:
        """Current simulation tick."""
        return self._tick

    @property
    def elapsed_time(self) -> float:
        """Elapsed real time in seconds."""
        import time
        if self._paused:
            return self._pause_time - self._start_time
        return time.perf_counter() - self._start_time

    @property
    def simulation_time(self) -> float:
        """Elapsed simulation time (tick / tick_rate)."""
        return self._tick / self._tick_rate

    @property
    def tick_rate(self) -> float:
        """Target tick rate."""
        return self._tick_rate

    @property
    def delta_time(self) -> float:
        """Time since last tick (1/tick_rate)."""
        return 1.0 / self._tick_rate

    @property
    def is_paused(self) -> bool:
        """Check if clock is paused."""
        return self._paused

    def start(self) -> None:
        """Start the clock."""
        import time
        if self._start_time == 0.0:
            self._start_time = time.perf_counter()

    def pause(self) -> None:
        """Pause the clock."""
        import time
        if not self._paused:
            self._pause_time = time.perf_counter()
            self._paused = True

    def resume(self) -> None:
        """Resume the clock."""
        import time
        if self._paused:
            pause_duration = time.perf_counter() - self._pause_time
            self._start_time += pause_duration
            self._paused = False

    def tick(self) -> int:
        """Increment tick and return new tick number."""
        if not self._paused:
            self._tick += 1
        return self._tick

    def reset(self) -> None:
        """Reset the clock."""
        self._tick = 0
        self._start_time = 0.0
        self._pause_time = 0.0
        self._paused = False

    def set_tick_rate(self, rate: float) -> None:
        """Set the tick rate."""
        if rate <= 0:
            raise ValueError("Tick rate must be positive")
        self._tick_rate = rate
