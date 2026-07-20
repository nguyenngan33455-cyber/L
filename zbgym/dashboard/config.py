"""Dashboard configuration for ZBGym.

This module manages Dashboard client configuration including
connection settings, authentication, and behavior options.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import ClassVar


# Default configuration values
DEFAULT_URL = "http://localhost:8080"
DEFAULT_WS_URL = "ws://localhost:8080/ws"
DEFAULT_HEARTBEAT_INTERVAL = 30.0
DEFAULT_TIMEOUT = 10.0
DEFAULT_MAX_QUEUE_SIZE = 10000
DEFAULT_RECONNECT_DELAY = 1.0
DEFAULT_MAX_RECONNECT_DELAY = 60.0
DEFAULT_RECONNECT_MULTIPLIER = 2.0
DEFAULT_MAX_RECONNECT_ATTEMPTS = 10
DEFAULT_BATCH_SIZE = 100
DEFAULT_BATCH_INTERVAL = 5.0


@dataclass
class DashboardConfig:
    """Configuration for Dashboard client.

    This class holds all configuration options for the Dashboard client.
    It can be created directly or loaded from environment variables.

    Example:
        # Direct configuration
        config = DashboardConfig(
            url="https://dashboard.zbgym.dev",
            api_key="zb_xxx",
            reconnect=True
        )

        # Or load from environment
        config = DashboardConfig.from_env()

    Attributes:
        url: Dashboard server URL (HTTP).
        ws_url: Dashboard WebSocket URL (WSS).
        api_key: API key for authentication.
        reconnect: Whether to automatically reconnect on disconnect.
        heartbeat_interval: Heartbeat interval in seconds.
        timeout: Request timeout in seconds.
        max_queue_size: Maximum number of items in publish queue.
        reconnect_delay: Initial delay between reconnection attempts.
        max_reconnect_delay: Maximum delay between reconnection attempts.
        reconnect_multiplier: Multiplier for exponential backoff.
        max_reconnect_attempts: Maximum number of reconnection attempts.
        batch_size: Number of items to batch before sending.
        batch_interval: Maximum interval between batch sends.
        enabled: Whether dashboard is enabled.
        log_level: Logging level for dashboard operations.
    """

    # Default URLs
    DEFAULT_URL: ClassVar[str] = DEFAULT_URL
    DEFAULT_WS_URL: ClassVar[str] = DEFAULT_WS_URL

    # Connection settings
    url: str = DEFAULT_URL
    ws_url: str | None = None
    api_key: str | None = None

    # Behavior settings
    reconnect: bool = True
    heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL
    timeout: float = DEFAULT_TIMEOUT

    # Queue settings
    max_queue_size: int = DEFAULT_MAX_QUEUE_SIZE
    batch_size: int = DEFAULT_BATCH_SIZE
    batch_interval: float = DEFAULT_BATCH_INTERVAL

    # Reconnection settings
    reconnect_delay: float = DEFAULT_RECONNECT_DELAY
    max_reconnect_delay: float = DEFAULT_MAX_RECONNECT_DELAY
    reconnect_multiplier: float = DEFAULT_RECONNECT_MULTIPLIER
    max_reconnect_attempts: int = DEFAULT_MAX_RECONNECT_ATTEMPTS

    # Feature flags
    enabled: bool = True

    # Logging
    log_level: str = "INFO"

    # Internal state
    _validated: bool = field(default=False, repr=False)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If any configuration value is invalid.
        """
        if self.timeout <= 0:
            raise ValueError(f"timeout must be positive, got {self.timeout}")

        if self.heartbeat_interval <= 0:
            raise ValueError(
                f"heartbeat_interval must be positive, got {self.heartbeat_interval}"
            )

        if self.max_queue_size <= 0:
            raise ValueError(
                f"max_queue_size must be positive, got {self.max_queue_size}"
            )

        if self.batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {self.batch_size}")

        if self.batch_interval <= 0:
            raise ValueError(
                f"batch_interval must be positive, got {self.batch_interval}"
            )

        if self.reconnect_delay <= 0:
            raise ValueError(
                f"reconnect_delay must be positive, got {self.reconnect_delay}"
            )

        if self.max_reconnect_delay < self.reconnect_delay:
            raise ValueError(
                f"max_reconnect_delay ({self.max_reconnect_delay}) must be >= "
                f"reconnect_delay ({self.reconnect_delay})"
            )

        if self.max_reconnect_attempts < 0:
            raise ValueError(
                f"max_reconnect_attempts must be non-negative, "
                f"got {self.max_reconnect_attempts}"
            )

        if self.url and not self.url.startswith(("http://", "https://")):
            raise ValueError(f"url must start with http:// or https://, got {self.url}")

        self._validated = True

    @property
    def ws_url_computed(self) -> str:
        """Compute WebSocket URL from HTTP URL.

        Returns:
            WebSocket URL derived from the HTTP URL.
        """
        if self.ws_url:
            return self.ws_url

        # Derive WS URL from HTTP URL
        if self.url.startswith("https://"):
            return self.url.replace("https://", "wss://") + "/ws"
        elif self.url.startswith("http://"):
            return self.url.replace("http://", "ws://") + "/ws"

        return self.ws_url or DEFAULT_WS_URL

    @classmethod
    def from_env(cls) -> DashboardConfig:
        """Create configuration from environment variables.

        Environment variables:
            ZBGYM_DASHBOARD_URL: Dashboard server URL.
            ZBGYM_DASHBOARD_API_KEY: API key for authentication.
            ZBGYM_DASHBOARD_ENABLED: Whether dashboard is enabled.
            ZBGYM_DASHBOARD_LOG_LEVEL: Logging level.

        Returns:
            DashboardConfig instance with values from environment.

        Example:
            # Set environment variables
            export ZBGYM_DASHBOARD_URL="https://dashboard.zbgym.dev"
            export ZBGYM_DASHBOARD_API_KEY="zb_xxx"
            export ZBGYM_DASHBOARD_ENABLED="true"

            # Load config
            config = DashboardConfig.from_env()
        """
        return cls(
            url=os.environ.get("ZBGYM_DASHBOARD_URL", DEFAULT_URL),
            api_key=os.environ.get("ZBGYM_DASHBOARD_API_KEY"),
            ws_url=os.environ.get("ZBGYM_DASHBOARD_WS_URL"),
            enabled=os.environ.get("ZBGYM_DASHBOARD_ENABLED", "true").lower()
            == "true",
            log_level=os.environ.get("ZBGYM_DASHBOARD_LOG_LEVEL", "INFO"),
        )

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration.
            Note: api_key is excluded for security.
        """
        return {
            "url": self.url,
            "ws_url": self.ws_url,
            "reconnect": self.reconnect,
            "heartbeat_interval": self.heartbeat_interval,
            "timeout": self.timeout,
            "max_queue_size": self.max_queue_size,
            "batch_size": self.batch_size,
            "batch_interval": self.batch_interval,
            "reconnect_delay": self.reconnect_delay,
            "max_reconnect_delay": self.max_reconnect_delay,
            "reconnect_multiplier": self.reconnect_multiplier,
            "max_reconnect_attempts": self.max_reconnect_attempts,
            "enabled": self.enabled,
            "log_level": self.log_level,
        }

    def masked_api_key(self) -> str:
        """Get masked API key for logging.

        Returns:
            Masked API key showing only first and last 4 characters.
        """
        if not self.api_key:
            return "None"
        if len(self.api_key) <= 8:
            return "*" * len(self.api_key)
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"

    def copy(self) -> DashboardConfig:
        """Create a copy of this configuration.

        Returns:
            New DashboardConfig instance with same values.
        """
        return DashboardConfig(
            url=self.url,
            ws_url=self.ws_url,
            api_key=self.api_key,
            reconnect=self.reconnect,
            heartbeat_interval=self.heartbeat_interval,
            timeout=self.timeout,
            max_queue_size=self.max_queue_size,
            batch_size=self.batch_size,
            batch_interval=self.batch_interval,
            reconnect_delay=self.reconnect_delay,
            max_reconnect_delay=self.max_reconnect_delay,
            reconnect_multiplier=self.reconnect_multiplier,
            max_reconnect_attempts=self.max_reconnect_attempts,
            enabled=self.enabled,
            log_level=self.log_level,
        )


# Global configuration instance
_global_config: DashboardConfig | None = None


def get_config() -> DashboardConfig:
    """Get global dashboard configuration.

    Returns:
        Global DashboardConfig instance.
    """
    global _global_config
    if _global_config is None:
        _global_config = DashboardConfig()
    return _global_config


def configure(
    url: str | None = None,
    api_key: str | None = None,
    **kwargs,
) -> DashboardConfig:
    """Configure global dashboard settings.

    This is a convenience function to configure the global
    Dashboard configuration instance.

    Args:
        url: Dashboard server URL.
        api_key: API key for authentication.
        **kwargs: Additional configuration options.

    Returns:
        The configured DashboardConfig instance.

    Example:
        dashboard.configure(
            url="https://dashboard.zbgym.dev",
            api_key="zb_xxx",
            reconnect=True,
            heartbeat=30
        )
    """
    global _global_config

    if _global_config is None:
        _global_config = DashboardConfig(
            url=url or DEFAULT_URL,
            api_key=api_key,
            **kwargs
        )
    else:
        # Update existing config
        if url is not None:
            _global_config.url = url
        if api_key is not None:
            _global_config.api_key = api_key

    # Update other kwargs
    for key, value in kwargs.items():
        if hasattr(_global_config, key):
            setattr(_global_config, key, value)
        else:
            raise ValueError(f"Unknown configuration option: {key}")

    _global_config._validate()
    return _global_config
