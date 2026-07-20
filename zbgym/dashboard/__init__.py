"""Dashboard Connector for ZBGym.

This module provides a client for connecting to the ZBGym Dashboard
server to track and monitor RL training sessions.

Example:
    from zbgym.dashboard import DashboardClient

    # Create and connect
    dashboard = DashboardClient()
    dashboard.connect(
        url="https://dashboard.zbgym.dev",
        api_key="zb_xxx"
    )

    # Start session
    with dashboard.session("Zooba", "PPO", "BattleArena-v2"):
        for step in range(1000000):
            # Training
            dashboard.publish_metrics(reward=reward, loss=loss)

    dashboard.disconnect()
"""

from zbgym.dashboard.client import (
    DashboardClient,
    connect,
    disconnect,
    get_dashboard,
)
from zbgym.dashboard.config import (
    DashboardConfig,
    configure,
    get_config,
)
from zbgym.dashboard.events import Event
from zbgym.dashboard.exceptions import (
    DashboardAuthError,
    DashboardConnectionError,
    DashboardError,
    DashboardProtocolError,
    DashboardQueueFullError,
    DashboardReconnectError,
    DashboardSessionError,
    DashboardTimeoutError,
    DashboardUploadError,
)
from zbgym.dashboard.metrics import Metrics, MetricsAggregator
from zbgym.dashboard.models import (
    CheckpointData,
    EventData,
    EventType,
    LogData,
    LogLevel,
    MetricType,
    MetricsData,
    PacketType,
    ReplayData,
    TrainingSession,
    ZBGYM_VERSION,
)

__all__ = [
    # Client
    "DashboardClient",
    "connect",
    "disconnect",
    "get_dashboard",
    # Config
    "DashboardConfig",
    "configure",
    "get_config",
    # Events
    "Event",
    # Exceptions
    "DashboardError",
    "DashboardAuthError",
    "DashboardConnectionError",
    "DashboardProtocolError",
    "DashboardQueueFullError",
    "DashboardReconnectError",
    "DashboardSessionError",
    "DashboardTimeoutError",
    "DashboardUploadError",
    # Metrics
    "Metrics",
    "MetricsAggregator",
    # Models
    "CheckpointData",
    "EventData",
    "EventType",
    "LogData",
    "LogLevel",
    "MetricType",
    "MetricsData",
    "PacketType",
    "ReplayData",
    "TrainingSession",
    "ZBGYM_VERSION",
]

__version__ = ZBGYM_VERSION


# Dashboard Manager
from zbgym.dashboard.manager import (
    DashboardManager,
    DashboardManagerConfig,
    get_dashboard_manager,
    configure_dashboard,
)
from zbgym.dashboard.callback import (
    DashboardCallback,
    DashboardMetricsCallback,
    DashboardCheckpointCallback,
)

__all__ += [
    # Manager
    "DashboardManager",
    "DashboardManagerConfig",
    "get_dashboard_manager",
    "configure_dashboard",
    # Callback
    "DashboardCallback",
    "DashboardMetricsCallback",
    "DashboardCheckpointCallback",
]
