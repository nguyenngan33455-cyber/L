"""
ZBGym Kernel Core Implementation.

This module provides the production-grade Kernel implementation.
"""

from zbgym.kernel.core.kernel import Kernel, KernelState, KernelConfig
from zbgym.kernel.core.runtime_context import RuntimeContext, Clock
from zbgym.kernel.core.module_manager import ModuleManager, ModuleNotFoundError
from zbgym.kernel.core.lifecycle_manager import (
    LifecycleManager,
    ModuleState,
    LifecycleCallbacks,
    LifecycleTransitionError
)
from zbgym.kernel.core.dependency_resolver import (
    DependencyResolver,
    Dependency,
    DependencyType,
    ModuleSpec,
    DependencyError,
    CyclicDependencyError,
    MissingDependencyError
)
from zbgym.kernel.core.tick_coordinator import (
    TickCoordinator,
    TickStage,
    TickResult,
    StageResult
)
from zbgym.kernel.core.event_dispatcher import (
    EventDispatcher,
    Event,
    Subscription
)
from zbgym.kernel.core.panic_manager import (
    PanicManager,
    PanicLevel,
    PanicEvent
)
from zbgym.kernel.core.state_store import StateStore, StateSnapshot
from zbgym.kernel.core.health_monitor import (
    HealthMonitor,
    HealthStatus,
    HealthReport,
    ModuleHealth
)
from zbgym.kernel.core.metrics_collector import MetricsCollector, Metric

__all__ = [
    # Kernel
    "Kernel",
    "KernelState",
    "KernelConfig",
    # Runtime
    "RuntimeContext",
    "Clock",
    # Module
    "ModuleManager",
    "ModuleNotFoundError",
    # Lifecycle
    "LifecycleManager",
    "ModuleState",
    "LifecycleCallbacks",
    "LifecycleTransitionError",
    # Dependency
    "DependencyResolver",
    "Dependency",
    "DependencyType",
    "ModuleSpec",
    "DependencyError",
    "CyclicDependencyError",
    "MissingDependencyError",
    # Tick
    "TickCoordinator",
    "TickStage",
    "TickResult",
    "StageResult",
    # Event
    "EventDispatcher",
    "Event",
    "Subscription",
    # Panic
    "PanicManager",
    "PanicLevel",
    "PanicEvent",
    # State
    "StateStore",
    "StateSnapshot",
    # Health
    "HealthMonitor",
    "HealthStatus",
    "HealthReport",
    "ModuleHealth",
    # Metrics
    "MetricsCollector",
    "Metric",
]
