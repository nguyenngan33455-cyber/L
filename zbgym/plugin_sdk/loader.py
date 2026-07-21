"""Plugin loader for discovering and loading plugins."""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import toml

if TYPE_CHECKING:
    from zbgym.plugin_sdk.base import PluginBase, PluginMetadata

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Discovers and loads plugins from various sources.

    Supports:
    - Local plugin directories
    - Editable plugins
    - Future: pip packages
    - Future: Git repositories
    """

    def __init__(
        self,
        plugin_dirs: list[Path] | None = None,
        safe_mode: bool = True,
    ) -> None:
        """
        Initialize plugin loader.

        Args:
            plugin_dirs: Directories to search for plugins
            safe_mode: If True, isolate plugin execution
        """
        self._plugin_dirs = plugin_dirs or [Path("./plugins"), Path("~/.zbgym/plugins")]
        self._safe_mode = safe_mode
        self._loaded_modules: dict[str, object] = {}

    def discover_plugins(
        self,
        plugin_dir: Path | str | None = None,
    ) -> list[PluginBase]:
        """
        Discover plugins in a directory.

        Args:
            plugin_dir: Directory to search (uses default if None)

        Returns:
            List of discovered plugins
        """
        if plugin_dir is None:
            plugins = []
            for directory in self._plugin_dirs:
                plugins.extend(self._discover_in_dir(Path(directory)))
            return plugins

        return self._discover_in_dir(Path(plugin_dir))

    def _discover_in_dir(self, plugin_dir: Path) -> list[PluginBase]:
        """Discover plugins in a single directory."""
        plugins: list[PluginBase] = []

        if not plugin_dir.exists():
            logger.debug(f"Plugin directory does not exist: {plugin_dir}")
            return plugins

        # Expand user path
        plugin_dir = plugin_dir.expanduser()

        for item in plugin_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                manifest_path = item / "plugin.toml"
                if manifest_path.exists():
                    try:
                        plugin = self._load_from_directory(item)
                        if plugin:
                            plugins.append(plugin)
                    except Exception as e:
                        logger.error(f"Failed to load plugin from {item}: {e}")

        logger.info(f"Discovered {len(plugins)} plugins in {plugin_dir}")
        return plugins

    def _load_from_directory(self, plugin_path: Path) -> PluginBase | None:
        """Load a plugin from a directory."""
        manifest_path = plugin_path / "plugin.toml"

        if not manifest_path.exists():
            return None

        # Load manifest
        with open(manifest_path) as f:
            manifest_data = toml.load(f)

        metadata = self._parse_manifest(manifest_data, plugin_path)

        # Find and load entry point
        entry_point = metadata.entry_point
        if not entry_point:
            # Try default: plugin.py
            entry_point = "plugin.py"

        entry_path = plugin_path / entry_point
        if not entry_path.exists():
            raise FileNotFoundError(f"Plugin entry point not found: {entry_path}")

        # Load the module
        module_name = f"zbgym_plugins.{metadata.name.replace('-', '_')}"

        try:
            spec = importlib.util.spec_from_file_location(module_name, entry_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                self._loaded_modules[metadata.name] = module
                spec.loader.exec_module(module)

                # Get plugin class
                if hasattr(module, "create_plugin"):
                    plugin = module.create_plugin(metadata)
                elif hasattr(module, "Plugin"):
                    plugin = module.Plugin(metadata)
                else:
                    raise PluginLoadError(
                        f"Plugin module must define 'Plugin' class or 'create_plugin' function"
                    )

                return plugin

        except Exception as e:
            logger.error(f"Failed to load plugin module: {e}")
            raise PluginLoadError(f"Failed to load plugin: {e}") from e

        return None

    def _parse_manifest(
        self,
        manifest_data: dict,
        plugin_path: Path,
    ) -> PluginMetadata:
        """Parse plugin manifest."""
        from zbgym.plugin_sdk.base import PluginMetadata

        plugin_info = manifest_data.get("plugin", {})

        return PluginMetadata(
            name=plugin_info.get("name", plugin_path.name),
            version=plugin_info.get("version", "1.0.0"),
            author=plugin_info.get("author", ""),
            description=plugin_info.get("description", ""),
            minimum_zbgym_version=plugin_info.get("minimum-zbgym-version", "1.0.0"),
            api_version=plugin_info.get("api-version", "1.0"),
            dependencies=plugin_info.get("dependencies", []),
            optional_dependencies=plugin_info.get("optional-dependencies", []),
            supported_games=plugin_info.get("supported-games", []),
            capabilities=plugin_info.get("capabilities", []),
            entry_point=plugin_info.get("entry-point", "plugin.py"),
            path=plugin_path,
        )

    def load_plugin_class(
        self,
        plugin_path: Path,
        class_name: str = "Plugin",
    ) -> type[PluginBase]:
        """
        Load a specific plugin class from a file.

        Args:
            plugin_path: Path to plugin file
            class_name: Name of plugin class

        Returns:
            Plugin class
        """
        module_name = f"zbgym_plugin_{plugin_path.stem}"

        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            self._loaded_modules[module_name] = module
            spec.loader.exec_module(module)

            if not hasattr(module, class_name):
                raise PluginLoadError(
                    f"Plugin module does not define '{class_name}' class"
                )

            return getattr(module, class_name)

        raise PluginLoadError(f"Failed to load plugin class from {plugin_path}")

    def validate_plugin(self, plugin_path: Path) -> tuple[bool, str | None]:
        """
        Validate a plugin directory.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not plugin_path.exists():
            return False, f"Plugin path does not exist: {plugin_path}"

        if not plugin_path.is_dir():
            return False, f"Plugin path is not a directory: {plugin_path}"

        manifest_path = plugin_path / "plugin.toml"
        if not manifest_path.exists():
            return False, "Missing plugin.toml"

        try:
            with open(manifest_path) as f:
                manifest_data = toml.load(f)

            plugin_info = manifest_data.get("plugin", {})

            # Validate required fields
            if not plugin_info.get("name"):
                return False, "Missing plugin name"

            if not plugin_info.get("version"):
                return False, "Missing plugin version"

            # Validate entry point exists
            entry_point = plugin_info.get("entry-point", "plugin.py")
            entry_path = plugin_path / entry_point
            if not entry_path.exists():
                return False, f"Entry point not found: {entry_point}"

        except Exception as e:
            return False, f"Failed to parse manifest: {e}"

        return True, None

    def get_unloaded_module(self, name: str) -> object | None:
        """Get a loaded module by name."""
        return self._loaded_modules.get(name)

    def unload_module(self, name: str) -> None:
        """Unload a plugin module."""
        if name in self._loaded_modules:
            del self._loaded_modules[name]
        if name in sys.modules and name.startswith("zbgym_plugins."):
            del sys.modules[name]


from zbgym.plugin_sdk.base import PluginBase, PluginLoadError
