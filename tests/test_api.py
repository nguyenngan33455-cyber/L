"""Tests for ZBGym API."""

import pytest
from zbgym.api import DashboardAPI, TrainingSession, ModelInfo


class TestDashboardAPI:
    """Tests for DashboardAPI."""

    def test_api_creation(self):
        """Test creating API."""
        api = DashboardAPI()
        assert api is not None
        app = api.get_app()
        assert app is not None
        assert app.title == "ZBGym Dashboard API"

    def test_add_session(self):
        """Test adding session."""
        api = DashboardAPI()
        session = TrainingSession(id="test123")
        api.add_session(session)
        assert "test123" in api._sessions

    def test_add_model(self):
        """Test adding model."""
        api = DashboardAPI()
        model = ModelInfo(
            id="model1",
            name="Test Model",
            path="./test.zip",
            algorithm="PPO",
            env_id="Test-v1",
            created_at=0.0,
        )
        api.add_model(model)
        assert "model1" in api._models

    def test_broadcast(self):
        """Test broadcast."""
        api = DashboardAPI()
        # Should not raise
        api.broadcast({"type": "test"})


class TestTrainingSession:
    """Tests for TrainingSession."""

    def test_session_creation(self):
        """Test creating session."""
        session = TrainingSession(id="test")
        assert session.id == "test"
        assert session.status == "idle"

    def test_session_with_params(self):
        """Test creating session with parameters."""
        session = TrainingSession(
            id="test",
            env_id="BattleArena-v1",
            algorithm="PPO",
            total_timesteps=1000000,
        )
        assert session.env_id == "BattleArena-v1"
        assert session.algorithm == "PPO"
        assert session.total_timesteps == 1000000


class TestModelInfo:
    """Tests for ModelInfo."""

    def test_model_creation(self):
        """Test creating model info."""
        model = ModelInfo(
            id="model1",
            name="Test",
            path="./test.zip",
            algorithm="PPO",
            env_id="Test-v1",
            created_at=0.0,
        )
        assert model.id == "model1"
        assert model.name == "Test"
