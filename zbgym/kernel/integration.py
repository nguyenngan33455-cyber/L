"""
Kernel Integration Layer for ZBGym.

This module provides integration between the Kernel and existing framework modules.
All modules should be initialized through this layer.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from zbgym.kernel.core import (
    Kernel,
    KernelConfig,
    RuntimeContext,
    EventDispatcher,
    Event,
    StateStore,
    HealthMonitor,
    HealthStatus,
    MetricsCollector,
    TickStage,
)

if TYPE_CHECKING:
    pass


class KernelIntegration:
    """
    Integration layer for Kernel and framework modules.
    
    This class provides a unified way to:
    - Bootstrap the Kernel
    - Register framework modules
    - Coordinate execution
    - Monitor health
    - Collect metrics
    """

    def __init__(self, config: KernelConfig | None = None) -> None:
        """
        Initialize Kernel integration.
        
        Args:
            config: Optional Kernel configuration
        """
        self._kernel = Kernel(config)
        self._initialized = False
        self._modules: dict[str, Any] = {}

    @property
    def kernel(self) -> Kernel:
        """Get the Kernel instance."""
        return self._kernel

    @property
    def context(self) -> RuntimeContext:
        """Get RuntimeContext."""
        return self._kernel.context

    def bootstrap(self) -> "KernelIntegration":
        """
        Bootstrap the Kernel.
        
        Returns:
            Self for chaining
        """
        self._kernel.bootstrap()
        self._initialized = True
        return self

    def register_module(
        self,
        name: str,
        instance: Any,
        dependencies: list[str] | None = None,
        metadata: dict | None = None
    ) -> "KernelIntegration":
        """
        Register a module with the Kernel.
        
        Args:
            name: Module name
            instance: Module instance
            dependencies: Optional dependencies
            metadata: Optional metadata
            
        Returns:
            Self for chaining
        """
        self._kernel.register_module(name, instance, dependencies, metadata)
        self._modules[name] = instance
        return self

    def register_core_services(self) -> "KernelIntegration":
        """
        Register core framework services with Kernel.
        
        Returns:
            Self for chaining
        """
        # These are already registered in Kernel.bootstrap()
        # This method is for explicit documentation
        return self

    def initialize(self) -> "KernelIntegration":
        """
        Initialize all registered modules.
        
        Returns:
            Self for chaining
        """
        self._kernel.initialize_modules()
        return self

    def start(self) -> "KernelIntegration":
        """
        Start the Kernel.
        
        Returns:
            Self for chaining
        """
        self._kernel.start()
        return self

    def tick(self) -> bool:
        """
        Execute one tick.
        
        Returns:
            True if tick succeeded
        """
        return self._kernel.tick()

    def pause(self) -> "KernelIntegration":
        """
        Pause the Kernel.
        
        Returns:
            Self for chaining
        """
        self._kernel.pause()
        return self

    def resume(self) -> "KernelIntegration":
        """
        Resume the Kernel.
        
        Returns:
            Self for chaining
        """
        self._kernel.resume()
        return self

    def stop(self) -> "KernelIntegration":
        """
        Stop the Kernel.
        
        Returns:
            Self for chaining
        """
        self._kernel.stop()
        return self

    def shutdown(self) -> None:
        """Shutdown the Kernel and all modules."""
        try:
            self._kernel.shutdown()
        except Exception:
            pass  # Ignore shutdown errors
        self._initialized = False

    def get_module(self, name: str) -> Any:
        """
        Get a registered module.
        
        Args:
            name: Module name
            
        Returns:
            Module instance
        """
        return self._kernel.get_module(name)

    def has_module(self, name: str) -> bool:
        """Check if module is registered."""
        return self._kernel.has_module(name)

    def emit_event(
        self,
        event_type: str,
        data: dict | None = None,
        source: str | None = None
    ) -> Event:
        """
        Emit an event through the Kernel.
        
        Args:
            event_type: Event type
            data: Optional event data
            source: Optional event source
            
        Returns:
            The emitted event
        """
        event = Event(type=event_type, data=data or {}, source=source)
        self.context.event_bus.emit(event)
        return event

    def subscribe(
        self,
        event_type: str,
        callback: Any,
        priority: int = 0
    ) -> str:
        """
        Subscribe to events.
        
        Args:
            event_type: Event type to subscribe to
            callback: Callback function
            priority: Subscription priority
            
        Returns:
            Subscription ID
        """
        return self.context.event_bus.subscribe(event_type, callback, priority=priority)

    def record_metric(
        self,
        name: str,
        value: float,
        labels: dict | None = None
    ) -> None:
        """
        Record a metric.
        
        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels
        """
        self.context.metrics.histogram(f"kernel.{name}", value, labels)

    def get_status(self) -> dict:
        """
        Get integration status.
        
        Returns:
            Status dictionary
        """
        return {
            "initialized": self._initialized,
            "kernel_state": self._kernel.state.value,
            "modules": list(self._modules.keys()),
            "tick": self.context.clock.current_tick,
        }

    def __enter__(self) -> "KernelIntegration":
        """Context manager entry."""
        return self.bootstrap()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.shutdown()


# Module registry for framework integration
class ModuleRegistry:
    """
    Registry for framework modules.
    
    Provides a centralized way to register and access modules.
    """

    def __init__(self) -> None:
        """Initialize the module registry."""
        self._modules: dict[str, Any] = {}
        self._singletons: dict[str, type] = {}

    def register(self, name: str, instance: Any) -> None:
        """
        Register a module instance.
        
        Args:
            name: Module name
            instance: Module instance
        """
        self._modules[name] = instance

    def get(self, name: str) -> Any | None:
        """
        Get a module.
        
        Args:
            name: Module name
            
        Returns:
            Module instance or None
        """
        return self._modules.get(name)

    def has(self, name: str) -> bool:
        """Check if module exists."""
        return name in self._modules

    def list_modules(self) -> list[str]:
        """List all registered modules."""
        return list(self._modules.keys())

    def clear(self) -> None:
        """Clear all registered modules."""
        self._modules.clear()


# Global registry instance
_global_registry = ModuleRegistry()


def get_registry() -> ModuleRegistry:
    """Get the global module registry."""
    return _global_registry


def register_module(name: str, instance: Any) -> None:
    """
    Register a module globally.
    
    Args:
        name: Module name
        instance: Module instance
    """
    _global_registry.register(name, instance)


def get_module(name: str) -> Any | None:
    """
    Get a global module.
    
    Args:
        name: Module name
        
    Returns:
        Module instance or None
    """
    return _global_registry.get(name)


def has_module(name: str) -> bool:
    """Check if global module exists."""
    return _global_registry.has(name)


def list_modules() -> list[str]:
    """List all global modules."""
    return _global_registry.list_modules()
