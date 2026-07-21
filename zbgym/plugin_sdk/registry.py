"""Plugin registry for managing loaded plugins."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from zbgym.plugin_sdk.base import PluginError, PluginState

if TYPE_CHECKING:
    from zbgym.plugin_sdk.base import PluginBase, PluginMetadata

logger = logging.getLogger(__name__)


@dataclass
class RegistryEntry:
    """Entry in the plugin registry."""

    plugin: PluginBase
    load_order: int = 0
    enable_order: int = 0


class PluginRegistry:
    """
    Central registry for all plugins.

    Manages plugin registration, lookup, and lifecycle.
    """

    def __init__(self) -> None:
        """Initialize the plugin registry."""
        self._plugins: dict[str, RegistryEntry] = {}
        self._load_order: list[str] = []
        self._enable_order: list[str] = []
        self._load_counter = 0
        self._enable_counter = 0

    @property
    def plugins(self) -> dict[str, RegistryEntry]:
        """Get all registered plugins."""
        return self._plugins.copy()

    @property
    def plugin_count(self) -> int:
        """Get number of registered plugins."""
        return len(self._plugins)

    def register(self, plugin: PluginBase) -> None:
        """
        Register a plugin.

        Args:
            plugin: Plugin to register

        Raises:
            PluginError: If plugin is already registered
        """
        name = plugin.name

        if name in self._plugins:
            raise PluginError(f"Plugin '{name}' is already registered")

        self._plugins[name] = RegistryEntry(plugin=plugin)
        logger.info(f"Registered plugin: {name} v{plugin.version}")

    def unregister(self, name: str) -> bool:
        """
        Unregister a plugin.

        Args:
            name: Plugin name

        Returns:
            True if plugin was found and removed
        """
        if name in self._plugins:
            del self._plugins[name]
            if name in self._load_order:
                self._load_order.remove(name)
            if name in self._enable_order:
                self._enable_order.remove(name)
            logger.info(f"Unregistered plugin: {name}")
            return True
        return False

    def get(self, name: str) -> PluginBase | None:
        """
        Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin or None if not found
        """
        entry = self._plugins.get(name)
        return entry.plugin if entry else None

    def get_by_capability(self, capability: str) -> list[PluginBase]:
        """
        Get all plugins with a specific capability.

        Args:
            capability: Capability to search for

        Returns:
            List of plugins with the capability
        """
        result = []
        for entry in self._plugins.values():
            if capability in entry.plugin.capabilities:
                result.append(entry.plugin)
        return result

    def is_registered(self, name: str) -> bool:
        """Check if a plugin is registered."""
        return name in self._plugins

    def load(self, name: str) -> None:
        """
        Load a plugin.

        Args:
            name: Plugin name
        """
        entry = self._plugins.get(name)
        if not entry:
            raise PluginError(f"Plugin '{name}' is not registered")

        if entry.plugin.state.value in ("loaded", "enabled"):
            logger.warning(f"Plugin '{name}' is already loaded")
            return

        try:
            entry.plugin.load()
            entry.plugin._state = PluginState.LOADED  # Update state
            self._load_counter += 1
            entry.load_order = self._load_counter
            self._load_order.append(name)
            logger.info(f"Loaded plugin: {name}")
        except Exception as e:
            entry.plugin.on_error(e)
            raise

    def enable(self, name: str) -> None:
        """
        Enable a plugin.

        Args:
            name: Plugin name
        """
        entry = self._plugins.get(name)
        if not entry:
            raise PluginError(f"Plugin '{name}' is not registered")

        if entry.plugin.state.value == "enabled":
            logger.warning(f"Plugin '{name}' is already enabled")
            return

        # Load if not already loaded
        if entry.plugin.state.value == "discovered":
            self.load(name)

        try:
            entry.plugin.enable()
            entry.plugin._state = PluginState.ENABLED  # Update state
            self._enable_counter += 1
            entry.enable_order = self._enable_counter
            self._enable_order.append(name)
            logger.info(f"Enabled plugin: {name}")
        except Exception as e:
            entry.plugin.on_error(e)
            raise

    def disable(self, name: str) -> None:
        """
        Disable a plugin.

        Args:
            name: Plugin name
        """
        entry = self._plugins.get(name)
        if not entry:
            raise PluginError(f"Plugin '{name}' is not registered")

        if entry.plugin.state.value != "enabled":
            logger.warning(f"Plugin '{name}' is not enabled")
            return

        try:
            entry.plugin.disable()
            if name in self._enable_order:
                self._enable_order.remove(name)
            logger.info(f"Disabled plugin: {name}")
        except Exception as e:
            entry.plugin.on_error(e)
            raise

    def shutdown(self, name: str) -> None:
        """
        Shutdown a plugin.

        Args:
            name: Plugin name
        """
        entry = self._plugins.get(name)
        if not entry:
            return

        try:
            entry.plugin.shutdown()
            if name in self._load_order:
                self._load_order.remove(name)
            logger.info(f"Shutdown plugin: {name}")
        except Exception as e:
            entry.plugin.on_error(e)

    def reload(self, name: str) -> None:
        """
        Reload a plugin.

        Args:
            name: Plugin name
        """
        entry = self._plugins.get(name)
        if not entry:
            raise PluginError(f"Plugin '{name}' is not registered")

        try:
            entry.plugin.reload()
            logger.info(f"Reloaded plugin: {name}")
        except Exception as e:
            entry.plugin.on_error(e)
            raise

    def enable_all(self) -> None:
        """Enable all registered plugins in dependency order."""
        # First, load all plugins
        for name in self._load_order:
            entry = self._plugins.get(name)
            if entry and entry.plugin.state.value == "discovered":
                self.load(name)

        # Then enable all
        for name in self._enable_order:
            entry = self._plugins.get(name)
            if entry and entry.plugin.state.value == "loaded":
                self.enable(name)

    def disable_all(self) -> None:
        """Disable all enabled plugins in reverse order."""
        for name in reversed(self._enable_order):
            entry = self._plugins.get(name)
            if entry and entry.plugin.state.value == "enabled":
                self.disable(name)

    def shutdown_all(self) -> None:
        """Shutdown all plugins in reverse order."""
        for name in reversed(self._load_order):
            entry = self._plugins.get(name)
            if entry:
                self.shutdown(name)

    def clear(self) -> None:
        """Clear all plugins from the registry."""
        self.shutdown_all()
        self._plugins.clear()
        self._load_order.clear()
        self._enable_order.clear()

    def get_load_order(self) -> list[str]:
        """Get plugins in load order."""
        return self._load_order.copy()

    def get_enable_order(self) -> list[str]:
        """Get plugins in enable order."""
        return self._enable_order.copy()

    def get_health_report(self) -> dict[str, dict]:
        """Get health status of all plugins."""
        return {
            name: {
                "state": entry.plugin.state.value,
                "healthy": entry.plugin.health_check(),
                "capabilities": entry.plugin.capabilities,
            }
            for name, entry in self._plugins.items()
        }

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate plugin registry.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check for duplicate states
        enabled_count = sum(
            1 for e in self._plugins.values() if e.plugin.is_enabled
        )

        # Check load order integrity
        for name in self._load_order:
            if name not in self._plugins:
                errors.append(f"Load order references unknown plugin: {name}")

        return len(errors) == 0, errors
