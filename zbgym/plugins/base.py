"""Base classes for ZBGym plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""

    id: str
    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)


class Plugin(ABC):
    """Base class for all ZBGym plugins."""

    metadata: PluginMetadata

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin."""

    @abstractmethod
    def shutdown(self) -> None:
        """Cleanup when plugin is unloaded."""


class PluginRegistry(Generic[T]):
    """Registry for plugins of a specific type."""

    def __init__(self) -> None:
        self._plugins: dict[str, type[T]] = {}
        self._instances: dict[str, T] = {}

    def register(self, plugin_class: type[T], plugin_id: str | None = None) -> type[T]:
        """
        Register a plugin class.

        Args:
            plugin_class: Plugin class to register
            plugin_id: Optional plugin ID (uses class name if not provided)

        Returns:
            The plugin class
        """
        plugin_id = plugin_id or plugin_class.__name__.lower()
        self._plugins[plugin_id] = plugin_class
        return plugin_class

    def get(self, plugin_id: str) -> type[T] | None:
        """Get a plugin class by ID."""
        return self._plugins.get(plugin_id)

    def create(self, plugin_id: str, **kwargs) -> T | None:
        """Create an instance of a plugin."""
        plugin_class = self.get(plugin_id)
        if plugin_class is None:
            return None

        instance = plugin_class(**kwargs)
        instance.plugin_id = plugin_id
        self._instances[plugin_id] = instance
        return instance

    def get_instance(self, plugin_id: str) -> T | None:
        """Get an existing plugin instance."""
        return self._instances.get(plugin_id)

    def list_plugins(self) -> list[str]:
        """List all registered plugin IDs."""
        return list(self._plugins.keys())

    def unregister(self, plugin_id: str) -> bool:
        """Unregister a plugin."""
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            return True
        return False
