"""
LifecycleManager implementation for ZBGym Kernel.

Manages module lifecycle states and transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Callable


class ModuleState(Enum):
    """Module lifecycle states."""
    DISCOVERED = "discovered"
    REGISTERED = "registered"
    INITIALIZED = "initialized"
    STARTED = "started"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    SHUTDOWN = "shutdown"
    UNLOADED = "unloaded"


class LifecycleTransitionError(Exception):
    """Exception raised for invalid lifecycle transitions."""
    pass


@dataclass
class ModuleLifecycle:
    """Lifecycle state for a module."""
    name: str
    state: ModuleState = ModuleState.DISCOVERED
    metadata: dict = field(default_factory=dict)


class LifecycleCallbacks:
    """Lifecycle callbacks for a module."""

    def on_initializing(self) -> None:
        """Called when entering INITIALIZING state."""
        pass

    def on_initialized(self) -> None:
        """Called when exiting INITIALIZING state."""
        pass

    def on_starting(self) -> None:
        """Called when entering STARTED state."""
        pass

    def on_started(self) -> None:
        """Called when exiting STARTED state."""
        pass

    def on_running(self) -> None:
        """Called when entering RUNNING state."""
        pass

    def on_pausing(self) -> None:
        """Called when entering PAUSED state."""
        pass

    def on_resuming(self) -> None:
        """Called when exiting PAUSED state."""
        pass

    def on_stopping(self) -> None:
        """Called when entering STOPPED state."""
        pass

    def on_shutting_down(self) -> None:
        """Called when entering SHUTDOWN state."""
        pass

    def on_unloaded(self) -> None:
        """Called when entering UNLOADED state."""
        pass


# Valid transitions: current_state -> [allowed_next_states]
VALID_TRANSITIONS: dict[ModuleState, set[ModuleState]] = {
    ModuleState.DISCOVERED: {ModuleState.REGISTERED},
    ModuleState.REGISTERED: {ModuleState.INITIALIZED, ModuleState.DISCOVERED},
    ModuleState.INITIALIZED: {ModuleState.STARTED, ModuleState.REGISTERED},
    ModuleState.STARTED: {ModuleState.RUNNING, ModuleState.INITIALIZED},
    ModuleState.RUNNING: {ModuleState.PAUSED, ModuleState.STOPPED, ModuleState.RUNNING},
    ModuleState.PAUSED: {ModuleState.RUNNING, ModuleState.STOPPED, ModuleState.PAUSED},
    ModuleState.STOPPED: {ModuleState.SHUTDOWN, ModuleState.STARTED},
    ModuleState.SHUTDOWN: {ModuleState.UNLOADED, ModuleState.STOPPED},
    ModuleState.UNLOADED: set(),
}


class LifecycleManager:
    """
    Manages module lifecycle states and transitions.
    
    Ensures valid state transitions only.
    Calls lifecycle callbacks on transitions.
    """

    def __init__(self) -> None:
        """Initialize the lifecycle manager."""
        self._modules: dict[str, ModuleLifecycle] = {}
        self._instances: dict[str, Any] = {}
        self._callbacks: dict[str, LifecycleCallbacks] = {}
        self._lock = Lock()

    def discover(
        self,
        name: str,
        instance: Any,
        callbacks: LifecycleCallbacks | None = None
    ) -> None:
        """
        Discover a module.
        
        Args:
            name: Module name
            instance: Module instance
            callbacks: Optional lifecycle callbacks
        """
        with self._lock:
            if name in self._modules:
                raise LifecycleTransitionError(f"Module '{name}' already discovered")

            self._modules[name] = ModuleLifecycle(name=name)
            self._instances[name] = instance
            if callbacks:
                self._callbacks[name] = callbacks

    def register(self, name: str) -> None:
        """
        Register a module.
        
        Args:
            name: Module name
            
        Raises:
            LifecycleTransitionError: If transition is invalid
        """
        self._transition(name, ModuleState.REGISTERED)

    def initialize(self, name: str) -> None:
        """
        Initialize a module.
        
        Args:
            name: Module name
            
        Raises:
            LifecycleTransitionError: If transition is invalid
        """
        self._call_callback(name, "on_initializing")
        self._transition(name, ModuleState.INITIALIZED)
        self._call_callback(name, "on_initialized")

    def start(self, name: str) -> None:
        """
        Start a module.
        
        Args:
            name: Module name
            
        Raises:
            LifecycleTransitionError: If transition is invalid
        """
        self._call_callback(name, "on_starting")
        self._transition(name, ModuleState.STARTED)
        self._call_callback(name, "on_started")

    def set_running(self, name: str) -> None:
        """
        Set module to running state.
        
        Args:
            name: Module name
            
        Raises:
            LifecycleTransitionError: If transition is invalid
        """
        self._call_callback(name, "on_running")
        self._transition(name, ModuleState.RUNNING)

    def pause(self, name: str) -> None:
        """
        Pause a module.
        
        Args:
            name: Module name
            
        Raises:
            LifecycleTransitionError: If transition is invalid
        """
        self._call_callback(name, "on_pausing")
        self._transition(name, ModuleState.PAUSED)

    def resume(self, name: str) -> None:
        """
        Resume a module.
        
        Args:
            name: Module name
            
        Raises:
            LifecycleTransitionError: If transition is invalid
        """
        self._call_callback(name, "on_resuming")
        self._transition(name, ModuleState.RUNNING)

    def stop(self, name: str) -> None:
        """
        Stop a module.
        
        Args:
            name: Module name
            
        Raises:
            LifecycleTransitionError: If transition is invalid
        """
        self._call_callback(name, "on_stopping")
        self._transition(name, ModuleState.STOPPED)

    def shutdown(self, name: str) -> None:
        """
        Shutdown a module.
        
        Args:
            name: Module name
            
        Raises:
            LifecycleTransitionError: If transition is invalid
        """
        self._call_callback(name, "on_shutting_down")
        self._transition(name, ModuleState.SHUTDOWN)

    def unload(self, name: str) -> None:
        """
        Unload a module.
        
        Args:
            name: Module name
            
        Raises:
            LifecycleTransitionError: If transition is invalid
        """
        self._call_callback(name, "on_unloaded")
        self._transition(name, ModuleState.UNLOADED)

    def _transition(self, name: str, new_state: ModuleState) -> None:
        """
        Transition module to new state.
        
        Args:
            name: Module name
            new_state: Target state
            
        Raises:
            LifecycleTransitionError: If transition is invalid
        """
        with self._lock:
            if name not in self._modules:
                raise LifecycleTransitionError(f"Module '{name}' not found")

            lifecycle = self._modules[name]
            current_state = lifecycle.state

            if new_state not in VALID_TRANSITIONS.get(current_state, set()):
                raise LifecycleTransitionError(
                    f"Invalid transition: {current_state.value} -> {new_state.value} "
                    f"for module '{name}'"
                )

            lifecycle.state = new_state

    def _call_callback(self, name: str, callback_name: str) -> None:
        """
        Call a lifecycle callback.
        
        Args:
            name: Module name
            callback_name: Callback method name
        """
        callbacks = self._callbacks.get(name)
        if callbacks:
            method = getattr(callbacks, callback_name, None)
            if method:
                method()

    def get_state(self, name: str) -> ModuleState | None:
        """
        Get module state.
        
        Args:
            name: Module name
            
        Returns:
            Module state or None
        """
        with self._lock:
            lifecycle = self._modules.get(name)
            return lifecycle.state if lifecycle else None

    def get_instance(self, name: str) -> Any | None:
        """
        Get module instance.
        
        Args:
            name: Module name
            
        Returns:
            Module instance or None
        """
        with self._lock:
            return self._instances.get(name)

    def get_all_states(self) -> dict[str, ModuleState]:
        """
        Get all module states.
        
        Returns:
            Dict of module name to state
        """
        with self._lock:
            return {name: lc.state for name, lc in self._modules.items()}

    def get_modules_in_state(self, state: ModuleState) -> list[str]:
        """
        Get modules in specific state.
        
        Args:
            state: Target state
            
        Returns:
            List of module names
        """
        with self._lock:
            return [
                name for name, lc in self._modules.items()
                if lc.state == state
            ]
