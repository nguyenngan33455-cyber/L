"""
ZBGym Plugin SDK

Provides a production-grade plugin system for extending ZBGym.

Example:
    >>> from zbgym.plugin_sdk import PluginRegistry, PluginLoader
    >>>
    >>> # Load plugins
    >>> loader = PluginLoader()
    >>> registry = PluginRegistry()
    >>>
    >>> # Discover and load plugins
    >>> plugins = loader.discover_plugins("./plugins")
    >>> for plugin in plugins:
    ...     registry.register(plugin)
    >>>
    >>> # Enable all
    >>> registry.enable_all()
"""

from zbgym.plugin_sdk.base import (
    PluginBase,
    PluginMetadata,
    PluginState,
    PluginError,
    PluginLoadError,
    PluginDependencyError,
    PluginVersionError,
    PluginSandboxError,
)
from zbgym.plugin_sdk.registry import PluginRegistry
from zbgym.plugin_sdk.loader import PluginLoader
from zbgym.plugin_sdk.hooks import HookSystem, Hook

__version__ = "1.0.0"
__all__ = [
    "PluginBase",
    "PluginMetadata",
    "PluginState",
    "PluginError",
    "PluginLoadError",
    "PluginDependencyError",
    "PluginVersionError",
    "PluginSandboxError",
    "PluginRegistry",
    "PluginLoader",
    "HookSystem",
    "Hook",
]
