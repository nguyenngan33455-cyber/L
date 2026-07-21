"""
Minimal Plugin Example

This is a minimal example of a ZBGym plugin.
"""

from zbgym.plugin_sdk.base import PluginBase, PluginMetadata
from zbgym.plugin_sdk.hooks import get_hook_system


class MinimalPlugin(PluginBase):
    """A minimal plugin that logs tick events."""

    def __init__(self, metadata: PluginMetadata) -> None:
        """Initialize the plugin."""
        super().__init__(metadata)
        self._hook = None

    def initialize(self) -> None:
        """Initialize the plugin."""
        self._logger.info(f"MinimalPlugin initializing...")

    def load(self) -> None:
        """Load the plugin."""
        self._logger.info(f"MinimalPlugin loaded")

    def enable(self) -> None:
        """Enable the plugin."""
        self._logger.info(f"MinimalPlugin enabled")

        # Register a hook
        hooks = get_hook_system()
        self._hook = hooks.register_hook(
            "after_tick",
            self.on_tick,
            priority=0,
            plugin_name=self.name,
        )

    def disable(self) -> None:
        """Disable the plugin."""
        self._logger.info(f"MinimalPlugin disabled")

        if self._hook:
            self._hook.enabled = False
            self._hook = None

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        self._logger.info(f"MinimalPlugin shutdown")

    def on_tick(self, tick: int, dt: float) -> None:
        """Handle tick event."""
        self._logger.debug(f"Tick {tick}: dt={dt:.4f}")


def create_plugin(metadata: PluginMetadata) -> MinimalPlugin:
    """Create the plugin instance."""
    return MinimalPlugin(metadata)
