"""Hook system for plugin extensions."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class HookPriority(Enum):
    """Priority levels for hooks."""

    LOWEST = -100
    LOW = -50
    NORMAL = 0
    HIGH = 50
    HIGHEST = 100


@dataclass
class Hook:
    """
    Represents a hook callback.

    Attributes:
        name: Hook name
        callback: Function to call
        priority: Execution priority
        plugin_name: Name of plugin that registered this hook
    """

    name: str
    callback: Callable[..., Any]
    priority: int = HookPriority.NORMAL.value
    plugin_name: str = ""
    enabled: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.priority, HookPriority):
            self.priority = self.priority.value

    def __lt__(self, other: Hook) -> bool:
        return self.priority < other.priority

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the hook callback."""
        if self.enabled:
            return self.callback(*args, **kwargs)
        return None


class HookSystem:
    """
    Central hook system for plugin extensions.

    Plugins subscribe to hooks to extend framework behavior.
    The core framework remains unchanged.
    """

    # Core hooks
    BEFORE_SIMULATION_START = "before_simulation_start"
    AFTER_SIMULATION_START = "after_simulation_start"
    BEFORE_TICK = "before_tick"
    AFTER_TICK = "after_tick"
    BEFORE_PHYSICS = "before_physics"
    AFTER_PHYSICS = "after_physics"
    BEFORE_COLLISION = "before_collision"
    AFTER_COLLISION = "after_collision"
    BEFORE_REWARD = "before_reward"
    AFTER_REWARD = "after_reward"
    BEFORE_OBSERVATION = "before_observation"
    AFTER_OBSERVATION = "after_observation"
    BEFORE_REPLAY_SAVE = "before_replay_save"
    AFTER_REPLAY_SAVE = "after_replay_save"
    BEFORE_AGENT_DECISION = "before_agent_decision"
    AFTER_AGENT_DECISION = "after_agent_decision"
    ON_CHARACTER_SPAWN = "on_character_spawn"
    ON_CHARACTER_DEATH = "on_character_death"
    ON_CHARACTER_DAMAGE = "on_character_damage"
    ON_MATCH_START = "on_match_start"
    ON_MATCH_END = "on_match_end"

    def __init__(self) -> None:
        """Initialize the hook system."""
        self._hooks: dict[str, list[Hook]] = {}
        self._global_hooks: list[Hook] = []

    def register_hook(
        self,
        name: str,
        callback: Callable[..., Any],
        priority: int = HookPriority.NORMAL.value,
        plugin_name: str = "",
    ) -> Hook:
        """
        Register a hook callback.

        Args:
            name: Hook name
            callback: Function to call
            priority: Execution priority (higher runs first)
            plugin_name: Plugin that owns this hook

        Returns:
            The registered hook
        """
        hook = Hook(
            name=name,
            callback=callback,
            priority=priority,
            plugin_name=plugin_name,
        )

        if name not in self._hooks:
            self._hooks[name] = []

        self._hooks[name].append(hook)
        self._hooks[name].sort(key=lambda h: -h.priority)

        logger.debug(f"Registered hook: {name} from {plugin_name}")
        return hook

    def unregister_hook(self, hook: Hook) -> bool:
        """
        Unregister a hook.

        Args:
            hook: Hook to unregister

        Returns:
            True if hook was found and removed
        """
        if hook.name in self._hooks:
            try:
                self._hooks[hook.name].remove(hook)
                logger.debug(f"Unregistered hook: {hook.name}")
                return True
            except ValueError:
                pass
        return False

    def unregister_plugin_hooks(self, plugin_name: str) -> int:
        """
        Unregister all hooks from a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            Number of hooks removed
        """
        count = 0
        for name in list(self._hooks.keys()):
            self._hooks[name] = [
                h for h in self._hooks[name] if h.plugin_name != plugin_name
            ]
            count += len(
                [h for h in self._hooks[name] if h.plugin_name == plugin_name]
            )

        self._hooks = {k: v for k, v in self._hooks.items() if v}

        logger.debug(f"Unregistered {count} hooks for plugin: {plugin_name}")
        return count

    def call(self, name: str, *args: Any, **kwargs: Any) -> list[Any]:
        """
        Call all hooks for a given name.

        Args:
            name: Hook name
            *args: Positional arguments to pass to hooks
            **kwargs: Keyword arguments to pass to hooks

        Returns:
            List of return values from hooks
        """
        if name not in self._hooks:
            return []

        results = []
        for hook in self._hooks[name]:
            if hook.enabled:
                try:
                    result = hook(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(
                        f"Hook '{name}' from {hook.plugin_name} raised error: {e}"
                    )

        return results

    def call_first(self, name: str, *args: Any, **kwargs: Any) -> Any | None:
        """
        Call the first (highest priority) hook for a name.

        Args:
            name: Hook name
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Return value from first hook, or None
        """
        if name not in self._hooks or not self._hooks[name]:
            return None

        hook = self._hooks[name][0]
        if hook.enabled:
            try:
                return hook(*args, **kwargs)
            except Exception as e:
                logger.error(f"Hook '{name}' raised error: {e}")

        return None

    def has_hooks(self, name: str) -> bool:
        """Check if any hooks are registered for a name."""
        return name in self._hooks and len(self._hooks[name]) > 0

    def get_hook_count(self, name: str) -> int:
        """Get number of hooks registered for a name."""
        return len(self._hooks.get(name, []))

    def get_all_hooks(self) -> dict[str, list[str]]:
        """Get all registered hooks by name."""
        return {
            name: [f"{h.plugin_name} (pri={h.priority})" for h in hooks]
            for name, hooks in self._hooks.items()
        }

    def clear(self) -> None:
        """Clear all hooks."""
        self._hooks.clear()
        self._global_hooks.clear()

    def disable_hook(self, name: str, plugin_name: str) -> bool:
        """Disable a specific plugin's hook."""
        if name not in self._hooks:
            return False

        for hook in self._hooks[name]:
            if hook.plugin_name == plugin_name:
                hook.enabled = False
                return True
        return False

    def enable_hook(self, name: str, plugin_name: str) -> bool:
        """Enable a specific plugin's hook."""
        if name not in self._hooks:
            return False

        for hook in self._hooks[name]:
            if hook.plugin_name == plugin_name:
                hook.enabled = True
                return True
        return False


# Global hook system instance
_global_hook_system: HookSystem | None = None


def get_hook_system() -> HookSystem:
    """Get the global hook system instance."""
    global _global_hook_system
    if _global_hook_system is None:
        _global_hook_system = HookSystem()
    return _global_hook_system
