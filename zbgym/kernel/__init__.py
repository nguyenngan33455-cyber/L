"""
ZBGym Kernel Module.

This module provides the Kernel architecture and implementation for ZBGym.
The kernel is the central coordinator responsible for:
- Framework lifecycle management
- Module communication
- Scheduling and tick coordination
- Dependency management
- Runtime orchestration
"""

from zbgym.kernel.core import (
    Kernel,
    KernelState,
    KernelConfig,
    RuntimeContext,
    Clock,
    ModuleManager,
    ModuleState,
    LifecycleManager,
    LifecycleCallbacks,
    DependencyResolver,
    Dependency,
    DependencyType,
    ModuleSpec,
    TickCoordinator,
    TickStage,
    TickResult,
    StageResult,
    EventDispatcher,
    Event,
    Subscription,
    PanicManager,
    PanicLevel,
    PanicEvent,
    StateStore,
    StateSnapshot,
    HealthMonitor,
    HealthStatus,
    HealthReport,
    ModuleHealth,
    MetricsCollector,
    Metric,
    # Exceptions
    ModuleNotFoundError,
    LifecycleTransitionError,
    DependencyError,
    CyclicDependencyError,
    MissingDependencyError,
)

# Import integration layer
from zbgym.kernel.integration import (
    KernelIntegration,
    ModuleRegistry,
    get_registry,
    register_module,
    get_module,
    has_module,
    list_modules,
)

# Import factory
from zbgym.kernel.factory import (
    create_kernel,
    create_integrated_environment,
    KernelContext,
    run_kernel_env,
)

__all__ = [
    # Core
    "Kernel",
    "KernelState",
    "KernelConfig",
    "RuntimeContext",
    "Clock",
    # Module
    "ModuleManager",
    "ModuleState",
    "ModuleNotFoundError",
    # Lifecycle
    "LifecycleManager",
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
    # Integration
    "KernelIntegration",
    "ModuleRegistry",
    "get_registry",
    "register_module",
    "get_module",
    "has_module",
    "list_modules",
    # Factory
    "create_kernel",
    "create_integrated_environment",
    "KernelContext",
    "run_kernel_env",
]

__version__ = "1.0.0"
__status__ = "implementation"
