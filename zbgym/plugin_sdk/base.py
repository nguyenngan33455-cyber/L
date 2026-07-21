"""Plugin SDK base classes and exceptions."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class PluginState(Enum):
    """States a plugin can be in."""

    DISCOVERED = "discovered"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UNLOADED = "unloaded"


class PluginError(Exception):
    """Base exception for plugin errors."""
    pass


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""
    pass


class PluginDependencyError(PluginError):
    """Raised when plugin dependencies cannot be satisfied."""
    pass


class PluginVersionError(PluginError):
    """Raised when plugin version is incompatible."""
    pass


class PluginSandboxError(PluginError):
    """Raised when plugin violates sandbox rules."""
    pass


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""

    name: str
    version: str
    author: str = ""
    description: str = ""
    minimum_zbgym_version: str = "1.0.0"
    api_version: str = "1.0"
    dependencies: list[str] = field(default_factory=list)
    optional_dependencies: list[str] = field(default_factory=list)
    supported_games: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    entry_point: str = ""
    path: Path | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise PluginError("Plugin name cannot be empty")
        if not self.version:
            raise PluginError("Plugin version cannot be empty")

    def is_compatible_with(self, framework_version: str) -> bool:
        """Check if plugin is compatible with framework version."""
        from packaging.version import Version

        try:
            plugin_min = Version(self.minimum_zbgym_version)
            framework = Version(framework_version)
            return framework >= plugin_min
        except Exception:
            return True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "minimum_zbgym_version": self.minimum_zbgym_version,
            "api_version": self.api_version,
            "dependencies": self.dependencies,
            "optional_dependencies": self.optional_dependencies,
            "supported_games": self.supported_games,
            "capabilities": self.capabilities,
            "entry_point": self.entry_point,
        }


class PluginBase(ABC):
    """
    Abstract base class for all plugins.

    Plugins must implement all lifecycle methods.
    """

    def __init__(self, metadata: PluginMetadata) -> None:
        """
        Initialize plugin with metadata.

        Args:
            metadata: Plugin metadata
        """
        self._metadata = metadata
        self._state = PluginState.DISCOVERED
        self._logger = logging.getLogger(f"plugin.{metadata.name}")
        self._config: dict[str, Any] = {}

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return self._metadata

    @property
    def name(self) -> str:
        """Get plugin name."""
        return self._metadata.name

    @property
    def version(self) -> str:
        """Get plugin version."""
        return self._metadata.version

    @property
    def state(self) -> PluginState:
        """Get plugin state."""
        return self._state

    @property
    def capabilities(self) -> list[str]:
        """Get plugin capabilities."""
        return self._metadata.capabilities

    @property
    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._state == PluginState.ENABLED

    def set_config(self, config: dict[str, Any]) -> None:
        """Set plugin configuration."""
        self._config = config

    def get_config(self) -> dict[str, Any]:
        """Get plugin configuration."""
        return self._config.copy()

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the plugin.

        Called once during discovery. Use for registration only.
        Do not start long-running tasks here.
        """
        pass

    @abstractmethod
    def load(self) -> None:
        """
        Load the plugin.

        Called when plugin is being loaded.
        Allocate resources, register handlers.
        """
        pass

    @abstractmethod
    def enable(self) -> None:
        """
        Enable the plugin.

        Called when plugin is enabled.
        Start services, subscribe to hooks.
        """
        pass

    @abstractmethod
    def disable(self) -> None:
        """
        Disable the plugin.

        Called when plugin is disabled.
        Stop services, unsubscribe from hooks.
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """
        Shutdown the plugin.

        Called when plugin is being unloaded.
        Clean up all resources.
        """
        pass

    def reload(self) -> None:
        """
        Reload the plugin.

        Default implementation: disable, shutdown, load, enable.
        Override for custom reload behavior.
        """
        self.disable()
        self.shutdown()
        self.load()
        self.enable()

    def health_check(self) -> bool:
        """
        Check if plugin is healthy.

        Returns:
            True if plugin is functioning correctly
        """
        return self._state in (PluginState.ENABLED, PluginState.LOADED)

    def on_error(self, error: Exception) -> None:
        """
        Handle plugin error.

        Args:
            error: The exception that occurred
        """
        self._logger.error(f"Plugin error: {error}")
        self._state = PluginState.ERROR

    def __repr__(self) -> str:
        return f"Plugin({self.name} v{self.version}, state={self._state.value})"
