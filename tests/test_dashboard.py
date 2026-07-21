"""Tests for Dashboard module."""

import json
import time

import pytest

from zbgym.dashboard.client import DashboardClient
from zbgym.dashboard.config import DashboardConfig, configure
from zbgym.dashboard.events import Event
from zbgym.dashboard.exceptions import (
    DashboardAuthError,
    DashboardConnectionError,
    DashboardError,
    DashboardProtocolError,
    DashboardSessionError,
)
from zbgym.dashboard.metrics import Metrics, MetricsAggregator
from zbgym.dashboard.models import (
    EventType,
    LogLevel,
    MetricsData,
    MetricType,
    PacketType,
    TrainingSession,
)
from zbgym.dashboard.packet import (
    Packet,
    PacketBuilder,
)


class TestDashboardConfig:
    """Test DashboardConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = DashboardConfig()

        assert config.url == "http://localhost:8080"
        assert config.reconnect is True
        assert config.timeout == 10.0
        assert config.heartbeat_interval == 30.0
        assert config.enabled is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = DashboardConfig(
            url="https://dashboard.example.com",
            api_key="test_key",
            reconnect=False,
            timeout=5.0,
        )

        assert config.url == "https://dashboard.example.com"
        assert config.api_key == "test_key"
        assert config.reconnect is False
        assert config.timeout == 5.0

    def test_config_validation(self):
        """Test configuration validation."""
        with pytest.raises(ValueError):
            DashboardConfig(timeout=-1)

        with pytest.raises(ValueError):
            DashboardConfig(max_queue_size=0)

    def test_ws_url_computed(self):
        """Test WebSocket URL derivation."""
        config = DashboardConfig(url="https://dashboard.example.com")
        assert config.ws_url_computed == "wss://dashboard.example.com/ws"

        config = DashboardConfig(url="http://localhost:8080")
        assert config.ws_url_computed == "ws://localhost:8080/ws"

    def test_ws_url_override(self):
        """Test WebSocket URL override."""
        config = DashboardConfig(
            url="https://dashboard.example.com", ws_url="wss://custom.ws.com/socket"
        )
        assert config.ws_url_computed == "wss://custom.ws.com/socket"

    def test_masked_api_key(self):
        """Test API key masking."""
        config = DashboardConfig(api_key="zb_test_key_123")
        masked = config.masked_api_key()
        # Should mask middle portion
        assert "zb_" in masked
        assert "..." in masked
        assert masked != "zb_test_key_123"

        config = DashboardConfig(api_key=None)
        assert config.masked_api_key() == "None"

    def test_config_from_env(self):
        """Test loading config from environment."""
        import os

        os.environ["ZBGYM_DASHBOARD_URL"] = "https://env.example.com"
        os.environ["ZBGYM_DASHBOARD_API_KEY"] = "env_key"

        config = DashboardConfig.from_env()

        assert config.url == "https://env.example.com"
        assert config.api_key == "env_key"

        # Cleanup
        del os.environ["ZBGYM_DASHBOARD_URL"]
        del os.environ["ZBGYM_DASHBOARD_API_KEY"]

    def test_config_copy(self):
        """Test config copy."""
        config = DashboardConfig(url="https://example.com", api_key="key")
        copy = config.copy()

        assert copy.url == config.url
        assert copy.api_key == config.api_key
        assert copy is not config

    def test_configure_function(self):
        """Test configure function creates and stores config."""
        from zbgym.dashboard.config import _global_config

        # Store original
        original = _global_config

        config = configure(url="https://new.example.com", api_key="new_key")

        # configure should return a config with new values
        assert config.url == "https://new.example.com"
        assert config.api_key == "new_key"

        # get_config should return the same instance
        from zbgym.dashboard.config import get_config

        current_config = get_config()
        assert current_config is config

        # Restore original
        # Note: This test doesn't restore to avoid affecting other tests
        # In real scenario, use fixtures for isolation


class TestTrainingSession:
    """Test TrainingSession model."""

    def test_create_session(self):
        """Test creating a training session."""
        session = TrainingSession.create(
            project_name="TestProject",
            trainer="PPO",
            env_id="BattleArena-v2",
            total_timesteps=1000000,
        )

        assert session.project_name == "TestProject"
        assert session.trainer == "PPO"
        assert session.env_id == "BattleArena-v2"
        assert session.total_timesteps == 1000000
        assert session.status == "running"
        assert len(session.session_id) == 8

    def test_session_to_dict(self):
        """Test session serialization."""
        session = TrainingSession.create(project_name="Test", trainer="PPO", env_id="Env-v1")

        data = session.to_dict()

        assert data["project_name"] == "Test"
        assert data["trainer"] == "PPO"
        assert data["env_id"] == "Env-v1"
        assert "session_id" in data

    def test_session_from_dict(self):
        """Test session deserialization."""
        data = {
            "session_id": "abc12345",
            "project_name": "Test",
            "trainer": "PPO",
            "env_id": "Env-v1",
            "total_timesteps": 500000,
        }

        session = TrainingSession.from_dict(data)

        assert session.session_id == "abc12345"
        assert session.total_timesteps == 500000


class TestPacket:
    """Test Packet classes."""

    def test_packet_to_dict(self):
        """Test packet serialization."""
        packet = Packet(type=PacketType.METRICS, session="test123", payload={"reward": 10.5})

        data = packet.to_dict()

        assert data["type"] == "metrics"
        assert data["session"] == "test123"
        assert data["payload"]["reward"] == 10.5
        assert "timestamp" in data

    def test_packet_to_json(self):
        """Test packet JSON serialization."""
        packet = Packet(type=PacketType.HEARTBEAT, session="test123")

        json_str = packet.to_json()
        data = json.loads(json_str)

        assert data["type"] == "heartbeat"

    def test_packet_from_dict(self):
        """Test packet deserialization."""
        data = {
            "type": "metrics",
            "session": "abc123",
            "timestamp": time.time(),
            "payload": {"loss": 0.5},
        }

        packet = Packet.from_dict(data)

        assert packet.type == PacketType.METRICS
        assert packet.session == "abc123"
        assert packet.payload["loss"] == 0.5

    def test_packet_from_json(self):
        """Test packet JSON deserialization."""
        json_str = '{"type": "event", "session": "xyz", "payload": {}}'

        packet = Packet.from_json(json_str)

        assert packet.type == PacketType.EVENT
        assert packet.session == "xyz"

    def test_invalid_packet_type(self):
        """Test invalid packet type."""
        data = {"type": "invalid_type", "session": "test"}

        with pytest.raises(DashboardProtocolError):
            Packet.from_dict(data)

    def test_missing_required_field(self):
        """Test missing required field."""
        data = {"type": "metrics"}  # Missing "session"

        with pytest.raises(DashboardProtocolError):
            Packet.from_dict(data)


class TestPacketBuilder:
    """Test PacketBuilder."""

    def test_metrics_packet(self):
        """Test building metrics packet."""
        builder = PacketBuilder(session="test123")
        packet = builder.metrics({"reward": 10.0, "loss": 0.5})

        assert packet.type == PacketType.METRICS
        assert packet.session == "test123"
        assert packet.payload["metrics"]["reward"] == 10.0
        assert packet.seq == 1

    def test_sequence_numbers(self):
        """Test sequence number increment."""
        builder = PacketBuilder(session="test")

        p1 = builder.metrics({"a": 1})
        p2 = builder.metrics({"b": 2})
        p3 = builder.metrics({"c": 3})

        assert p1.seq == 1
        assert p2.seq == 2
        assert p3.seq == 3

    def test_heartbeat_packet(self):
        """Test building heartbeat packet."""
        builder = PacketBuilder(session="test")
        packet = builder.heartbeat()

        assert packet.type == PacketType.HEARTBEAT

    def test_log_packet(self):
        """Test building log packet."""
        builder = PacketBuilder(session="test")
        packet = builder.log("info", "Test message", source="test_module")

        assert packet.type == PacketType.LOG
        assert packet.payload["level"] == "info"
        assert packet.payload["message"] == "Test message"
        assert packet.payload["source"] == "test_module"

    def test_checkpoint_packet(self):
        """Test building checkpoint packet."""
        builder = PacketBuilder(session="test")
        packet = builder.checkpoint(
            file_path="/path/to/model.pt",
            file_size=1000000,
            file_type=".pt",
            timestep=50000,
            is_best=True,
        )

        assert packet.type == PacketType.CHECKPOINT
        assert packet.payload["file_path"] == "/path/to/model.pt"
        assert packet.payload["is_best"] is True


class TestMetrics:
    """Test Metrics class."""

    def test_training_metrics(self):
        """Test creating training metrics."""
        metrics = Metrics.training(
            session_id="test", episode=100, timestep=50000, reward=15.5, loss=0.3, entropy=0.01
        )

        assert metrics.session_id == "test"
        assert metrics.episode == 100
        assert "reward" in metrics.values or "episode_reward" in metrics.values
        assert "loss" in metrics.values

    def test_metrics_add(self):
        """Test adding metric values."""
        metrics = MetricsData(session_id="test")
        metrics.add(MetricType.EPISODE_REWARD, 10.0)
        metrics.add("custom_metric", 5.0)

        assert metrics.values["episode_reward"] == 10.0
        assert metrics.values["custom_metric"] == 5.0


class TestMetricsAggregator:
    """Test MetricsAggregator."""

    def test_aggregator_basic(self):
        """Test basic aggregation."""
        agg = MetricsAggregator(window_size=10)

        agg.add({"reward": 10.0, "loss": 0.5})
        agg.add({"reward": 20.0, "loss": 0.3})

        stats = agg.get()

        assert stats["reward"] == 15.0
        assert stats["loss"] == 0.4

    def test_aggregator_window(self):
        """Test rolling window."""
        agg = MetricsAggregator(window_size=2)

        agg.add({"value": 10.0})
        agg.add({"value": 20.0})
        agg.add({"value": 30.0})  # Should evict first value

        stats = agg.get()

        # Average of 20 and 30
        assert stats["value"] == 25.0

    def test_aggregator_reset(self):
        """Test reset."""
        agg = MetricsAggregator()
        agg.add({"value": 10.0})
        agg.reset()

        assert agg.count == 0
        assert agg.get() == {}


class TestEvent:
    """Test Event class."""

    def test_character_spawn(self):
        """Test character spawn event."""
        event = Event.character_spawn(
            session_id="test",
            character_id="player_1",
            character_type="Soldier",
            position={"x": 100, "y": 200},
        )

        assert event.session_id == "test"
        assert event.event_type == EventType.CHARACTER_SPAWN
        assert event.data["character_id"] == "player_1"
        assert event.data["position"]["x"] == 100

    def test_kill_event(self):
        """Test kill event."""
        event = Event.kill(
            session_id="test", killer_id="player_1", victim_id="player_2", weapon="Rifle"
        )

        assert event.event_type == EventType.KILL
        assert event.actor == "player_1"
        assert event.data["victim_id"] == "player_2"
        assert event.data["weapon"] == "Rifle"

    def test_custom_event(self):
        """Test custom event."""
        event = Event.custom(
            session_id="test",
            event_name="special_ability",
            event_data={"ability": "shield", "duration": 5.0},
        )

        assert event.event_type == EventType.CUSTOM
        assert event.data["event_name"] == "special_ability"
        assert event.data["ability"] == "shield"


class TestExceptions:
    """Test exceptions."""

    def test_dashboard_error(self):
        """Test base exception."""
        error = DashboardError("Test error", {"key": "value"})

        assert error.message == "Test error"
        assert error.details["key"] == "value"
        assert str(error) == "Test error (key=value)"

    def test_connection_error(self):
        """Test connection error."""
        error = DashboardConnectionError(url="https://example.com", reason="timeout")

        assert "example.com" in str(error)

    def test_auth_error(self):
        """Test auth error."""
        error = DashboardAuthError(reason="invalid_key")

        assert error.details["reason"] == "invalid_key"

    def test_session_error(self):
        """Test session error."""
        error = DashboardSessionError(session_id="abc123", operation="finish")

        assert error.details["session_id"] == "abc123"


class TestDashboardClient:
    """Test DashboardClient."""

    def test_client_init(self):
        """Test client initialization."""
        client = DashboardClient()

        assert client.is_connected is False

    def test_client_not_connected_error(self):
        """Test error when not connected."""
        client = DashboardClient()

        with pytest.raises(DashboardConnectionError):
            client.publish_metrics(reward=10.0)

    def test_client_disconnect_when_not_connected(self):
        """Test disconnect when not connected."""
        client = DashboardClient()
        client.disconnect()  # Should not raise

    def test_client_context_manager(self):
        """Test client as context manager."""
        client = DashboardClient()

        with pytest.raises(DashboardConnectionError), client:
            client.publish_metrics(reward=10.0)

    def test_client_singleton(self):
        """Test singleton pattern."""
        DashboardClient._instance = None

        client1 = DashboardClient()
        client2 = DashboardClient.get_instance()

        assert client1 is client2

        # Cleanup
        DashboardClient._instance = None


class TestEnums:
    """Test enum values."""

    def test_packet_types(self):
        """Test PacketType enum."""
        assert PacketType.HEARTBEAT.value == "heartbeat"
        assert PacketType.METRICS.value == "metrics"
        assert PacketType.EVENT.value == "event"

    def test_metric_types(self):
        """Test MetricType enum."""
        assert MetricType.EPISODE_REWARD.value == "episode_reward"
        assert MetricType.LOSS.value == "loss"
        assert MetricType.ENTROPY.value == "entropy"

    def test_event_types(self):
        """Test EventType enum."""
        assert EventType.CHARACTER_SPAWN.value == "character_spawn"
        assert EventType.KILL.value == "kill"

    def test_log_levels(self):
        """Test LogLevel enum."""
        assert LogLevel.INFO.value == "info"
        assert LogLevel.ERROR.value == "error"
