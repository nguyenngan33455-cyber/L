"""
ModuleManager implementation for ZBGym Kernel.

Manages module registration, lookup, and lifecycle coordination.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable

from zbgym.kernel.core.lifecycle_manager import (
    LifecycleManager,
    ModuleState,
    LifecycleCallbacks
)
from zbgym.kernel.core.dependency_resolver import (
    DependencyResolver,
    ModuleSpec,
    Dependency
)


@dataclass
class Module:
    """Represents a registered module."""
    name: str
    instance: Any
    spec: ModuleSpec | None = None
    metadata: dict = field(default_factory=dict)


class ModuleNotFoundError(Exception):
    """Exception raised when module not found."""
    pass


class ModuleManager:
    """
    Manages framework modules.
    
    Handles registration, lookup, and coordinates with LifecycleManager
    and DependencyResolver.
    """

    def __init__(self) -> None:
        """Initialize the module manager."""
        self._modules: dict[str, Module] = {}
        self._lifecycle: LifecycleManager = LifecycleManager()
        self._dependency_resolver: DependencyResolver = DependencyResolver()
        self._lock = Lock()

    def register(
        self,
        name: str,
        instance: Any,
        dependencies: list[str] | None = None,
        metadata: dict | None = None
    ) -> None:
        """
        Register a module.
        
        Args:
            name: Module name
            instance: Module instance
            dependencies: Optional list of dependency names
            metadata: Optional metadata
        """
        with self._lock:
            if name in self._modules:
                raise ValueError(f"Module '{name}' already registered")

            # Create spec for dependency resolver
            spec = ModuleSpec(
                name=name,
                dependencies=[Dependency(d) for d in (dependencies or [])],
                metadata=metadata or {}
            )

            self._dependency_resolver.register_module(spec)
            self._modules[name] = Module(
                name=name,
                instance=instance,
                spec=spec,
                metadata=metadata or {}
            )

            # Discover module
            self._lifecycle.discover(name, instance)

    def unregister(self, name: str) -> bool:
        """
        Unregister a module.
        
        Args:
            name: Module name
            
        Returns:
            True if unregistered
        """
        with self._lock:
            if name not in self._modules:
                return False

            del self._modules[name]
            self._dependency_resolver.unregister_module(name)

            return True

    def get(self, name: str) -> Any:
        """
        Get module instance.
        
        Args:
            name: Module name
            
        Returns:
            Module instance
            
        Raises:
            ModuleNotFoundError: If module not found
        """
        with self._lock:
            module = self._modules.get(name)
            if module is None:
                raise ModuleNotFoundError(f"Module '{name}' not found")
            return module.instance

    def get_module_info(self, name: str) -> Module | None:
        """
        Get module info.
        
        Args:
            name: Module name
            
        Returns:
            Module info or None
        """
        with self._lock:
            return self._modules.get(name)

    def has(self, name: str) -> bool:
        """
        Check if module exists.
        
        Args:
            name: Module name
            
        Returns:
            True if module exists
        """
        with self._lock:
            return name in self._modules

    def get_all(self) -> list[str]:
        """
        Get all module names.
        
        Returns:
            List of module names
        """
        with self._lock:
            return list(self._modules.keys())

    def resolve_dependencies(self) -> list[str]:
        """
        Resolve dependencies and return load order.
        
        Returns:
            List of module names in dependency order
            
        Raises:
            Exception: If resolution fails
        """
        with self._lock:
            return self._dependency_resolver.resolve()

    def initialize_all(self) -> None:
        """Initialize all modules in dependency order."""
        order = self.resolve_dependencies()

        for name in order:
            self._lifecycle.register(name)
            self._lifecycle.initialize(name)

    def start_all(self) -> None:
        """Start all initialized modules."""
        with self._lock:
            order = self.resolve_dependencies()

        for name in order:
            state = self._lifecycle.get_state(name)
            if state == ModuleState.INITIALIZED:
                self._lifecycle.start(name)
                self._lifecycle.set_running(name)

    def stop_all(self) -> None:
        """Stop all modules in reverse dependency order."""
        with self._lock:
            order = self.resolve_dependencies()
            order.reverse()

        for name in order:
            state = self._lifecycle.get_state(name)
            if state in {ModuleState.RUNNING, ModuleState.PAUSED}:
                self._lifecycle.stop(name)

    def shutdown_all(self) -> None:
        """Shutdown all modules in reverse dependency order."""
        with self._lock:
            if not self._modules:
                return  # No modules registered
            order = self.resolve_dependencies()
            order.reverse()

        for name in order:
            state = self._lifecycle.get_state(name)
            if state == ModuleState.STOPPED:
                self._lifecycle.shutdown(name)

    def get_state(self, name: str) -> ModuleState | None:
        """
        Get module state.
        
        Args:
            name: Module name
            
        Returns:
            Module state or None
        """
        return self._lifecycle.get_state(name)

    def get_lifecycle(self) -> LifecycleManager:
        """
        Get lifecycle manager.
        
        Returns:
            LifecycleManager instance
        """
        return self._lifecycle

    def get_dependency_resolver(self) -> DependencyResolver:
        """
        Get dependency resolver.
        
        Returns:
            DependencyResolver instance
        """
        return self._dependency_resolver
