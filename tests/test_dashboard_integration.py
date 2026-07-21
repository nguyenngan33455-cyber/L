"""Integration tests for Dashboard module."""

from unittest.mock import MagicMock, patch

from zbgym.dashboard.callback import (
    DashboardCallback,
)
from zbgym.dashboard.client import DashboardClient
from zbgym.dashboard.manager import (
    DashboardManager,
    DashboardManagerConfig,
    configure_dashboard,
    get_dashboard_manager,
)
from zbgym.dashboard.models import LogLevel


class TestDashboardManager:
    """Test DashboardManager."""

    def test_manager_disabled_by_default(self):
        """Test manager is disabled by default."""
        manager = DashboardManager()
        assert manager.is_enabled is False
        assert manager.session_id is None

    def test_manager_configure(self):
        """Test manager configuration."""
        config = DashboardManagerConfig(
            enabled=True,
            url="https://test.example.com",
            api_key="test_key",
            publish_interval=50,
        )
        manager = DashboardManager(config)

        assert manager.is_enabled is True
        assert manager._config.url == "https://test.example.com"
        assert manager._config.api_key == "test_key"
        assert manager._config.publish_interval == 50

    def test_manager_enable_disable(self):
        """Test enabling and disabling dashboard."""
        manager = DashboardManager()
        assert manager.is_enabled is False

        manager.configure(enabled=True)
        assert manager.is_enabled is True

        manager.configure(enabled=False)
        assert manager.is_enabled is False

    def test_start_session_disabled(self):
        """Test starting session when disabled."""
        manager = DashboardManager()
        result = manager.start_session(project="Test", trainer="PPO", env="Test-v1")
        assert result is None

    @patch("zbgym.dashboard.manager.DashboardClient")
    def test_start_session_enabled(self, MockDashboardClient):
        """Test starting session when enabled."""
        from zbgym.dashboard.models import TrainingSession

        # Create mock client
        mock_client = MagicMock()
        mock_session = TrainingSession.create(project_name="Test", trainer="PPO", env_id="Test-v1")
        mock_client.connect.return_value = None
        mock_client.is_connected = True
        mock_client.start_session.return_value = mock_session

        MockDashboardClient.return_value = mock_client

        manager = DashboardManager(DashboardManagerConfig(enabled=True))
        result = manager.start_session(project="Test", trainer="PPO", env="Test-v1")

        assert result == mock_session.session_id
        assert manager.session_id == mock_session.session_id

    @patch.object(DashboardClient, "connect")
    @patch.object(DashboardClient, "start_session")
    def test_finish_session(self, mock_start, mock_connect):
        """Test finishing session."""
        mock_session = MagicMock()
        mock_session.session_id = "test123"
        mock_start.return_value = mock_session

        manager = DashboardManager(DashboardManagerConfig(enabled=True))
        manager.start_session(project="Test", trainer="PPO", env="Test-v1")
        manager.finish_session(status="finished")

        assert manager.session_id is None

    def test_publish_metrics_disabled(self):
        """Test publishing metrics when disabled doesn't error."""
        manager = DashboardManager()
        manager.publish_metrics(reward=10.0, loss=0.5)  # Should not error

    def test_publish_event_disabled(self):
        """Test publishing event when disabled doesn't error."""
        manager = DashboardManager()
        manager.publish_event("test_event", {"key": "value"})  # Should not error

    def test_publish_log_disabled(self):
        """Test publishing log when disabled doesn't error."""
        manager = DashboardManager()
        manager.publish_log(LogLevel.INFO, "Test message")  # Should not error

    def test_publish_checkpoint_disabled(self):
        """Test publishing checkpoint when disabled doesn't error."""
        manager = DashboardManager()
        manager.publish_checkpoint("/path/to/model.pt", timestep=1000)  # Should not error

    def test_publish_replay_disabled(self):
        """Test publishing replay when disabled doesn't error."""
        manager = DashboardManager()
        manager.publish_replay("/path/to/replay.json", episode=100)  # Should not error

    def test_should_publish_by_timestep(self):
        """Test publish interval by timestep."""
        config = DashboardManagerConfig(
            enabled=True,
            publish_interval=100,
        )
        manager = DashboardManager(config)

        # Should not publish initially
        assert manager.should_publish(0) is False

        # Should publish at interval
        assert manager.should_publish(100) is True

        # Should not publish again until next interval
        assert manager.should_publish(150) is False
        assert manager.should_publish(200) is True

    def test_event_shortcuts(self):
        """Test event shortcut methods."""
        manager = DashboardManager()
        manager.log_info("Info message")
        manager.log_warning("Warning message")
        manager.log_error("Error message")
        manager.log_debug("Debug message")

    def test_on_episode_events(self):
        """Test episode event methods."""
        manager = DashboardManager()
        manager.on_episode_start(episode=1)
        manager.on_episode_end(episode=1, reward=10.0, length=100)

    def test_context_manager(self):
        """Test context manager usage."""
        with DashboardManager() as manager:
            manager.configure(enabled=True)
            assert manager.is_enabled is True


class TestDashboardCallback:
    """Test DashboardCallback."""

    def test_callback_init(self):
        """Test callback initialization."""
        manager = DashboardManager(DashboardManagerConfig(enabled=True))
        callback = DashboardCallback(manager)

        assert callback._dashboard is manager
        assert callback._episode_count == 0

    def test_callback_disabled_manager(self):
        """Test callback with disabled manager."""
        manager = DashboardManager()  # Disabled by default
        callback = DashboardCallback(manager)

        callback.on_training_start({}, {})
        callback._on_step()
        callback.on_training_end({}, {})

        # Should not error even though manager is disabled


class TestTrainerDashboardIntegration:
    """Test trainer integration with dashboard."""

    def test_ppo_trainer_no_dashboard(self):
        """Test PPO trainer without dashboard."""
        from zbgym.trainer.base import TrainerConfig
        from zbgym.trainer.ppo import PPOTrainer

        config = TrainerConfig(total_timesteps=100)
        trainer = PPOTrainer(config=config)

        assert trainer.dashboard is None

    def test_ppo_trainer_with_dashboard_enabled(self):
        """Test PPO trainer with dashboard enabled."""
        from zbgym.trainer.base import TrainerConfig
        from zbgym.trainer.ppo import PPOTrainer

        config = TrainerConfig(total_timesteps=100)
        trainer = PPOTrainer(
            config=config,
            dashboard=True,
            dashboard_url="http://localhost:8080",
            dashboard_api_key="test_key",
        )

        assert trainer.dashboard is not None
        assert trainer.dashboard.is_enabled is True

    def test_ppo_trainer_with_dashboard_disabled(self):
        """Test PPO trainer with dashboard explicitly disabled."""
        from zbgym.trainer.base import TrainerConfig
        from zbgym.trainer.ppo import PPOTrainer

        config = TrainerConfig(total_timesteps=100)
        trainer = PPOTrainer(config=config, dashboard=False)

        assert trainer.dashboard is None

    def test_ppo_trainer_with_manager_instance(self):
        """Test PPO trainer with DashboardManager instance."""
        from zbgym.trainer.base import TrainerConfig
        from zbgym.trainer.ppo import PPOTrainer

        manager = DashboardManager(DashboardManagerConfig(enabled=True))
        config = TrainerConfig(total_timesteps=100)

        trainer = PPOTrainer(config=config, dashboard=manager)

        assert trainer.dashboard is manager

    def test_ppo_trainer_with_manager_config(self):
        """Test PPO trainer with DashboardManagerConfig."""
        from zbgym.trainer.base import TrainerConfig
        from zbgym.trainer.ppo import PPOTrainer

        config = TrainerConfig(total_timesteps=100)
        dash_config = DashboardManagerConfig(enabled=True, url="https://test.com")

        trainer = PPOTrainer(config=config, dashboard=dash_config)

        assert trainer.dashboard is not None
        assert trainer.dashboard.is_enabled is True
        assert trainer.dashboard._config.url == "https://test.com"


class TestDashboardFaultTolerance:
    """Test fault tolerance of dashboard integration."""

    def test_manager_handles_connection_error(self):
        """Test manager handles connection errors gracefully."""
        manager = DashboardManager(DashboardManagerConfig(enabled=True))

        # Should not raise even if connect fails
        # (start_session catches exceptions)
        result = manager.start_session(project="Test", trainer="PPO", env="Test-v1")
        # Result is None because connection failed

    def test_manager_handles_publish_error(self):
        """Test manager handles publish errors gracefully."""
        manager = DashboardManager(DashboardManagerConfig(enabled=True))

        # Should not raise even if publish fails
        manager.publish_metrics(reward=10.0)
        manager.publish_event("test", {})
        manager.publish_log(LogLevel.INFO, "test")


class TestDashboardGlobalConfig:
    """Test global dashboard configuration."""

    def test_configure_dashboard(self):
        """Test configure_dashboard function."""
        manager = configure_dashboard(
            enabled=True,
            url="https://test.com",
            api_key="test_key",
        )

        assert manager.is_enabled is True
        assert manager._config.url == "https://test.com"
        assert manager._config.api_key == "test_key"

    def test_get_dashboard_manager(self):
        """Test get_dashboard_manager function."""
        manager1 = get_dashboard_manager()
        manager2 = get_dashboard_manager()

        assert manager1 is manager2  # Singleton


class TestDashboardEvents:
    """Test dashboard event publishing."""

    def test_training_lifecycle_events(self):
        """Test training lifecycle events."""
        manager = DashboardManager(DashboardManagerConfig(enabled=True))

        manager.on_training_start()
        manager.on_episode_start(episode=1)
        manager.on_episode_end(episode=1, reward=10.0, length=100)
        manager.on_training_end(status="finished", duration=60.0)

    def test_evaluation_events(self):
        """Test evaluation events."""
        manager = DashboardManager(DashboardManagerConfig(enabled=True))

        manager.on_evaluation_start()
        manager.on_evaluation_end(
            mean_reward=10.0,
            std_reward=1.0,
            n_episodes=10,
        )

    def test_checkpoint_events(self):
        """Test checkpoint events."""
        manager = DashboardManager(DashboardManagerConfig(enabled=True))

        manager.on_checkpoint_save("/path/to/model.pt", timestep=1000, is_best=False)
        manager.on_checkpoint_save("/path/to/best.pt", timestep=2000, is_best=True)

    def test_replay_events(self):
        """Test replay events."""
        manager = DashboardManager(DashboardManagerConfig(enabled=True))

        manager.on_replay_save("/path/to/replay.json", episode=100, duration=60.5)


class TestDashboardPublishInterval:
    """Test dashboard publish interval configuration."""

    def test_publish_by_timesteps(self):
        """Test publishing by timesteps."""
        config = DashboardManagerConfig(
            enabled=True,
            publish_interval=100,
        )
        manager = DashboardManager(config)

        assert manager.should_publish(0) is False
        assert manager.should_publish(50) is False
        assert manager.should_publish(100) is True
        assert manager.should_publish(101) is False
        assert manager.should_publish(200) is True

    def test_publish_by_time(self):
        """Test publishing by time interval."""
        config = DashboardManagerConfig(
            enabled=True,
            publish_interval_seconds=1.0,  # 1 second
        )
        manager = DashboardManager(config)

        # First call should return True
        assert manager.should_publish(0) is True

        # Immediate second call should return False
        assert manager.should_publish(0) is False

    def test_publish_disabled(self):
        """Test publishing when dashboard is disabled."""
        config = DashboardManagerConfig(enabled=False)
        manager = DashboardManager(config)

        assert manager.should_publish(100) is False


class TestDashboardRepr:
    """Test string representations."""

    def test_manager_repr_disabled(self):
        """Test manager repr when disabled."""
        manager = DashboardManager()
        assert "disabled" in repr(manager)

    def test_manager_repr_enabled(self):
        """Test manager repr when enabled."""
        config = DashboardManagerConfig(enabled=True)
        manager = DashboardManager(config)
        assert "enabled" in repr(manager)
