"""
Example Plugin Template for ZBGym

This is a template for creating ZBGym plugins.
Copy this file and modify it for your plugin.
"""

from zbgym.plugin_sdk.base import (
    PluginBase,
    PluginMetadata,
    PluginState,
)
from zbgym.plugin_sdk.hooks import get_hook_system


class Plugin(PluginBase):
    """Example plugin for ZBGym."""

    def __init__(self, metadata: PluginMetadata) -> None:
        """Initialize the plugin."""
        super().__init__(metadata)
        self._hooks = []

    def initialize(self) -> None:
        """Initialize the plugin."""
        self._logger.info(f"Initializing {self.name} v{self.version}")
        # Register capabilities
        self._logger.info("Plugin initialized")

    def load(self) -> None:
        """Load the plugin."""
        self._logger.info(f"Loading {self.name}")
        # Load resources, setup state
        self._logger.info(f"{self.name} loaded")

    def enable(self) -> None:
        """Enable the plugin."""
        self._logger.info(f"Enabling {self.name}")

        # Register hooks
        hooks = get_hook_system()
        self._hooks.append(
            hooks.register_hook(
                "after_tick",
                self.on_tick,
                priority=0,
                plugin_name=self.name,
            )
        )

        self._logger.info(f"{self.name} enabled")

    def disable(self) -> None:
        """Disable the plugin."""
        self._logger.info(f"Disabling {self.name}")

        # Unregister hooks
        for hook in self._hooks:
            hook.enabled = False
        self._hooks.clear()

        self._logger.info(f"{self.name} disabled")

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        self._logger.info(f"Shutting down {self.name}")
        # Cleanup resources
        self._logger.info(f"{self.name} shutdown")

    def health_check(self) -> bool:
        """Check plugin health."""
        return True

    def on_tick(self, tick: int, dt: float) -> None:
        """Handle tick event."""
        pass


def create_plugin(metadata: PluginMetadata) -> Plugin:
    """Factory function to create the plugin."""
    return Plugin(metadata)
