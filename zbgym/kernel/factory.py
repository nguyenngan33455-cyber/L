"""
Kernel Factory for ZBGym.

Provides factory methods for creating fully integrated Kernel environments.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from zbgym.kernel.core import (
    Kernel,
    KernelConfig,
    RuntimeContext,
)

if TYPE_CHECKING:
    pass


def create_kernel(
    name: str = "ZBGym",
    tick_rate: int = 60,
    enable_health: bool = True,
    enable_metrics: bool = True,
) -> Kernel:
    """
    Create a configured Kernel.
    
    Args:
        name: Kernel name
        tick_rate: Target tick rate
        enable_health: Enable health monitoring
        enable_metrics: Enable metrics collection
        
    Returns:
        Configured Kernel instance
    """
    config = KernelConfig(
        name=name,
        tick_rate=tick_rate,
        enable_health_monitoring=enable_health,
        enable_metrics=enable_metrics,
    )
    
    kernel = Kernel(config)
    kernel.bootstrap()
    
    return kernel


def create_integrated_environment(
    env_class: type,
    config: dict | None = None,
    kernel_config: KernelConfig | None = None,
    **kwargs: Any
) -> tuple[env_class, Kernel]:
    """
    Create an environment with Kernel integration.
    
    Args:
        env_class: Environment class to instantiate
        config: Environment configuration
        kernel_config: Kernel configuration
        **kwargs: Additional arguments for environment
        
    Returns:
        Tuple of (environment, kernel)
    """
    # Create kernel
    kernel = Kernel(kernel_config or KernelConfig())
    kernel.bootstrap()
    
    # Create environment
    env = env_class(**kwargs) if kwargs else env_class()
    
    # Register environment with kernel
    kernel.register_module(
        "environment",
        env,
        dependencies=["event_bus", "tick_system"],
        metadata={"type": "environment"}
    )
    
    return env, kernel


class KernelContext:
    """
    Context manager for Kernel-based environments.
    
    Usage:
        with KernelContext() as ctx:
            env = ctx.create_environment("BattleArena-v1")
            for _ in range(100):
                ctx.tick()
    """

    def __init__(self, config: KernelConfig | None = None) -> None:
        """
        Initialize Kernel context.
        
        Args:
            config: Optional Kernel configuration
        """
        self._config = config or KernelConfig()
        self._kernel: Kernel | None = None
        self._env: Any | None = None

    def __enter__(self) -> "KernelContext":
        """Enter context."""
        self._kernel = Kernel(self._config)
        self._kernel.bootstrap()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context."""
        if self._kernel:
            self._kernel.shutdown()

    @property
    def kernel(self) -> Kernel:
        """Get Kernel."""
        if self._kernel is None:
            raise RuntimeError("KernelContext not entered")
        return self._kernel

    @property
    def context(self) -> RuntimeContext:
        """Get RuntimeContext."""
        return self.kernel.context

    def create_environment(
        self,
        env_id: str | type,
        **kwargs: Any
    ) -> Any:
        """
        Create an environment.
        
        Args:
            env_id: Environment ID or class
            **kwargs: Environment arguments
            
        Returns:
            Environment instance
        """
        from zbgym.make import make
        
        if isinstance(env_id, str):
            self._env = make(env_id, **kwargs)
        else:
            self._env = env_id(**kwargs) if kwargs else env_id()
        
        # Register with kernel
        self.kernel.register_module(
            "environment",
            self._env,
            metadata={"type": "environment"}
        )
        
        return self._env

    def tick(self) -> bool:
        """Execute one tick."""
        return self.kernel.tick()

    def run(self, steps: int) -> None:
        """Run for specified steps."""
        for _ in range(steps):
            self.tick()


# Convenience functions
def run_kernel_env(
    env_id: str,
    steps: int = 1000,
    config: KernelConfig | None = None
) -> tuple[Any, dict]:
    """
    Run an environment with Kernel integration.
    
    Args:
        env_id: Environment ID
        steps: Number of steps to run
        config: Optional Kernel configuration
        
    Returns:
        Tuple of (environment, status)
    """
    status = {"steps": 0, "errors": 0}
    
    with KernelContext(config) as ctx:
        env = ctx.create_environment(env_id)
        
        for i in range(steps):
            try:
                ctx.tick()
                status["steps"] = i + 1
            except Exception:
                status["errors"] += 1
                break
    
    return env, status
