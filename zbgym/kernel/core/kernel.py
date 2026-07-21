"""
Kernel implementation for ZBGym.

Main entry point for framework coordination.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
import time
import logging

from zbgym.kernel.core.runtime_context import RuntimeContext, Clock
from zbgym.kernel.core.module_manager import ModuleManager, ModuleNotFoundError
from zbgym.kernel.core.tick_coordinator import TickCoordinator, TickStage
from zbgym.kernel.core.event_dispatcher import EventDispatcher, Event
from zbgym.kernel.core.panic_manager import PanicManager, PanicLevel, PanicEvent
from zbgym.kernel.core.state_store import StateStore
from zbgym.kernel.core.health_monitor import HealthMonitor, HealthStatus


class KernelState(Enum):
    """Kernel states."""
    CREATED = "created"
    BOOTING = "booting"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    SHUTTING_DOWN = "shutting_down"
    TERMINATED = "terminated"
    FAILED = "failed"


@dataclass
class KernelConfig:
    """Kernel configuration."""
    name: str = "ZBGym"
    version: str = "1.0.0"
    tick_rate: int = 60
    max_tick_duration_ms: float = 100.0
    enable_health_monitoring: bool = True
    enable_metrics: bool = True
    enable_panic_recovery: bool = True
    shutdown_timeout_seconds: float = 10.0


class Kernel:
    """
    ZBGym Kernel.
    
    Central coordinator for the framework.
    Owns RuntimeContext, ModuleManager, TickCoordinator, and more.
    """

    # Valid state transitions
    VALID_TRANSITIONS: dict[KernelState, set[KernelState]] = {
        KernelState.CREATED: {KernelState.BOOTING},
        KernelState.BOOTING: {KernelState.INITIALIZING, KernelState.FAILED},
        KernelState.INITIALIZING: {KernelState.READY, KernelState.FAILED},
        KernelState.READY: {KernelState.RUNNING, KernelState.SHUTTING_DOWN},
        KernelState.RUNNING: {KernelState.PAUSED, KernelState.STOPPING, KernelState.FAILED},
        KernelState.PAUSED: {KernelState.RUNNING, KernelState.STOPPING},
        KernelState.STOPPING: {KernelState.STOPPED},
        KernelState.STOPPED: {KernelState.READY, KernelState.SHUTTING_DOWN},
        KernelState.SHUTTING_DOWN: {KernelState.TERMINATED},
        KernelState.FAILED: {KernelState.SHUTTING_DOWN},
        KernelState.TERMINATED: set(),
    }

    def __init__(self, config: KernelConfig | None = None) -> None:
        """
        Initialize Kernel.
        
        Args:
            config: Optional kernel configuration
        """
        self.config = config or KernelConfig()
        self.logger = logging.getLogger(f"zbgym.kernel.{self.config.name}")

        # Core components
        self._context: RuntimeContext = RuntimeContext()
        self._module_manager: ModuleManager = ModuleManager()
        self._tick_coordinator: TickCoordinator = TickCoordinator()
        self._event_dispatcher: EventDispatcher = EventDispatcher()
        self._panic_manager: PanicManager = PanicManager()
        self._state: KernelState = KernelState.CREATED
        self._lock: Lock = Lock()

        # Setup panic handler
        self._panic_manager.set_shutdown_handler(self._on_panic_shutdown)

        # Metrics
        self._boot_start_time: float = 0.0
        self._shutdown_start_time: float = 0.0

    def bootstrap(self) -> None:
        """
        Bootstrap the Kernel.
        
        Initializes RuntimeContext and prepares for module loading.
        
        Raises:
            RuntimeError: If already bootstrapped or in wrong state
        """
        with self._lock:
            self._validate_transition(KernelState.BOOTING)
            self._boot_start_time = time.perf_counter()

            self.logger.info(f"Bootstrapping {self.config.name} v{self.config.version}")

            # Initialize RuntimeContext
            self._context.initialize()

            # Register core services
            self._context.register_module("kernel", self)
            self._context.register_module("event_dispatcher", self._event_dispatcher)
            self._context.register_module("tick_coordinator", self._tick_coordinator)
            self._context.register_module("panic_manager", self._panic_manager)
            self._context.register_module("state_store", self._context.state_store)
            self._context.register_module("health_monitor", self._context.health_monitor)
            self._context.register_module("metrics", self._context.metrics)

            # Setup clock
            if self._context.clock:
                self._context.clock._tick_rate = self.config.tick_rate

            boot_duration = (time.perf_counter() - self._boot_start_time) * 1000
            self.logger.info(f"Bootstrap complete in {boot_duration:.2f}ms")

            self._context.metrics.histogram("kernel.boot.duration_ms", boot_duration)

            self._transition(KernelState.INITIALIZING)

    def initialize_modules(self) -> None:
        """
        Initialize all registered modules.
        """
        with self._lock:
            self._validate_state({KernelState.INITIALIZING})
            self.logger.info("Initializing modules")

            # Initialize all modules in dependency order
            self._module_manager.initialize_all()

            # Mark as ready
            self._transition(KernelState.READY)
            self.logger.info("All modules initialized")

    def start(self) -> None:
        """
        Start the Kernel and begin tick loop.
        """
        with self._lock:
            self._validate_state({KernelState.READY, KernelState.STOPPED})

            if self._state == KernelState.STOPPED:
                # Restart after stop
                self._module_manager.start_all()
            else:
                # First start
                self._module_manager.start_all()

            self._tick_coordinator.start()
            if self._context.clock:
                self._context.clock.start()

            self._transition(KernelState.RUNNING)
            self.logger.info("Kernel started")

    def pause(self) -> None:
        """
        Pause the Kernel.
        """
        with self._lock:
            self._validate_state({KernelState.RUNNING})

            self._tick_coordinator.stop()
            if self._context.clock:
                self._context.clock.pause()

            self._transition(KernelState.PAUSED)
            self.logger.info("Kernel paused")

    def resume(self) -> None:
        """
        Resume the Kernel.
        """
        with self._lock:
            self._validate_state({KernelState.PAUSED})

            if self._context.clock:
                self._context.clock.resume()
            self._tick_coordinator.start()

            self._transition(KernelState.RUNNING)
            self.logger.info("Kernel resumed")

    def stop(self) -> None:
        """
        Stop the Kernel.
        """
        with self._lock:
            self._validate_state({KernelState.RUNNING, KernelState.PAUSED})

            self._transition(KernelState.STOPPING)
            self._tick_coordinator.stop()

            # Stop all modules
            self._module_manager.stop_all()

            self._transition(KernelState.STOPPED)
            self.logger.info("Kernel stopped")

    def shutdown(self) -> None:
        """
        Shutdown the Kernel gracefully.
        """
        # Can shutdown from any state except TERMINATED
        if self._state == KernelState.TERMINATED:
            return

        # Stop tick coordinator
        self._tick_coordinator.stop()

        # Shutdown modules (release lock before calling)
        try:
            self._module_manager.shutdown_all()
        except Exception:
            pass

        # Shutdown RuntimeContext
        try:
            self._context.shutdown()
        except Exception:
            pass

        # Direct state transition
        self._state = KernelState.TERMINATED

    def tick(self) -> bool:
        """
        Execute one tick.
        
        Returns:
            True if tick succeeded
        """
        with self._lock:
            if self._state != KernelState.RUNNING:
                return False

        start_time = time.perf_counter()
        result = self._tick_coordinator.tick()
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Record metrics
        self._context.metrics.record_tick_duration(duration_ms)

        # Check tick duration
        if duration_ms > self.config.max_tick_duration_ms:
            self._panic_manager.warning(
                f"Tick {self._tick_coordinator.current_tick} exceeded "
                f"max duration: {duration_ms:.2f}ms > {self.config.max_tick_duration_ms}ms"
            )

        # Update clock
        if self._context.clock:
            self._context.clock.tick()

        # Emit tick event
        self._event_dispatcher.emit(Event(
            type="kernel.tick.complete",
            data={
                "tick": self._tick_coordinator.current_tick,
                "duration_ms": duration_ms,
                "success": result.success
            }
        ))

        return result.success

    def register_module(
        self,
        name: str,
        instance: Any,
        dependencies: list[str] | None = None,
        metadata: dict | None = None
    ) -> None:
        """
        Register a module with the Kernel.
        
        Args:
            name: Module name
            instance: Module instance
            dependencies: Optional dependencies
            metadata: Optional metadata
        """
        with self._lock:
            self._module_manager.register(name, instance, dependencies, metadata)
            self._context.register_module(name, instance)

            if self.config.enable_health_monitoring:
                self._context.health_monitor.register_module(name)

    def get_module(self, name: str) -> Any:
        """
        Get a module by name.
        
        Args:
            name: Module name
            
        Returns:
            Module instance
            
        Raises:
            ModuleNotFoundError: If module not found
        """
        return self._module_manager.get(name)

    def has_module(self, name: str) -> bool:
        """Check if module exists."""
        return self._module_manager.has(name)

    @property
    def context(self) -> RuntimeContext:
        """Get RuntimeContext."""
        return self._context

    @property
    def state(self) -> KernelState:
        """Get current kernel state."""
        with self._lock:
            return self._state

    @property
    def is_running(self) -> bool:
        """Check if kernel is running."""
        with self._lock:
            return self._state == KernelState.RUNNING

    def get_status(self) -> dict:
        """
        Get kernel status.
        
        Returns:
            Status dictionary
        """
        with self._lock:
            return {
                "name": self.config.name,
                "version": self.config.version,
                "state": self._state.value,
                "tick": self._tick_coordinator.current_tick,
                "modules": self._module_manager.get_all(),
                "running": self._state == KernelState.RUNNING,
            }

    def _validate_transition(self, target: KernelState) -> None:
        """Validate state transition."""
        if target not in self.VALID_TRANSITIONS.get(self._state, set()):
            raise RuntimeError(
                f"Invalid state transition: {self._state.value} -> {target.value}"
            )

    def _validate_state(self, states: set[KernelState]) -> None:
        """Validate current state."""
        if self._state not in states:
            raise RuntimeError(
                f"Invalid state: {self._state.value}, expected one of "
                f"{[s.value for s in states]}"
            )

    def _transition(self, new_state: KernelState) -> None:
        """Transition to new state."""
        old_state = self._state
        self._state = new_state
        self.logger.debug(f"State transition: {old_state.value} -> {new_state.value}")

        # Emit state change event
        self._event_dispatcher.emit(Event(
            type="kernel.state.changed",
            data={"from": old_state.value, "to": new_state.value}
        ))

    def _on_panic_shutdown(self) -> None:
        """Handle panic shutdown."""
        self.logger.critical("PANIC: Initiating emergency shutdown")

        try:
            # Stop tick coordinator
            self._tick_coordinator.stop()

            # Stop modules
            self._module_manager.stop_all()

            # Save panic snapshot
            snapshot = self._create_snapshot()
            self._panic_manager.save_snapshot(snapshot)

            # Transition to failed
            with self._lock:
                self._transition(KernelState.FAILED)

        except Exception as e:
            self.logger.critical(f"Error during panic shutdown: {e}")

    def _create_snapshot(self) -> dict:
        """Create state snapshot."""
        return {
            "timestamp": time.time(),
            "tick": self._tick_coordinator.current_tick,
            "state": self._state.value,
            "modules": {
                name: self._module_manager.get_state(name).value
                for name in self._module_manager.get_all()
            }
        }

    def panic(self, message: str, exception: Exception | None = None) -> None:
        """
        Trigger kernel panic.
        
        Args:
            message: Panic message
            exception: Optional exception
        """
        self._panic_manager.panic(message, exception=exception)

    def __enter__(self) -> "Kernel":
        """Context manager entry."""
        self.bootstrap()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.shutdown()
