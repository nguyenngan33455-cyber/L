"""Tests for ZBGym observation system."""

import numpy as np
import pytest

from zbgym.env.battle_arena import BattleArenaState, CharacterState
from zbgym.observation import (
    EnemyObservation,
    HealthObservation,
    ObservationBuilder,
    ObservationBuilderConfig,
    PositionObservation,
    ZoneObservation,
)
from zbgym.physics.vector import Vector2D


@pytest.fixture
def mock_state():
    """Create a mock game state."""
    state = BattleArenaState(
        tick=100,
        match_active=True,
        safe_zone_center=Vector2D(1000, 750),
        safe_zone_radius=800.0,
        danger_zone_radius=1000.0,
    )

    state.characters["player_1"] = CharacterState(
        id="player_1",
        position=Vector2D(900, 700),
        velocity=Vector2D(100, 50),
        health=80.0,
        shield=30.0,
        energy=60.0,
        is_alive=True,
    )
    state.characters["enemy_1"] = CharacterState(
        id="enemy_1",
        position=Vector2D(1200, 800),
        health=100.0,
        is_alive=True,
    )

    return state


class TestHealthObservation:
    """Tests for HealthObservation."""

    def test_observation_creation(self):
        """Test creating a health observation."""
        obs = HealthObservation()
        assert obs is not None
        assert obs.get_dimension() == 4

    def test_compute_health(self, mock_state):
        """Test computing health observation."""
        obs = HealthObservation()
        data = obs.compute(mock_state)

        assert data.shape == (4,)
        # health = 80/100 = 0.8, shield = 30/50 = 0.6, energy = 60/100 = 0.6
        assert np.isclose(data[0], 0.8)
        assert np.isclose(data[1], 0.6)
        assert np.isclose(data[2], 0.6)

    def test_no_alive_character(self):
        """Test with no alive characters."""
        state = BattleArenaState(
            tick=0,
            match_active=True,
            safe_zone_center=Vector2D(0, 0),
            safe_zone_radius=1000.0,
            danger_zone_radius=2000.0,
        )
        state.characters["dead"] = CharacterState(
            id="dead",
            position=Vector2D(0, 0),
            health=0.0,
            is_alive=False,
        )

        obs = HealthObservation()
        data = obs.compute(state)

        assert data.shape == (4,)
        assert np.allclose(data, 0.0)


class TestPositionObservation:
    """Tests for PositionObservation."""

    def test_observation_creation(self):
        """Test creating a position observation."""
        obs = PositionObservation()
        assert obs is not None
        assert obs.get_dimension() == 5

    def test_compute_position(self, mock_state):
        """Test computing position observation."""
        obs = PositionObservation()
        data = obs.compute(mock_state)

        assert data.shape == (5,)
        # pos_x = 900/2000 = 0.45, pos_y = 700/1500 = 0.467
        assert np.isclose(data[0], 0.45, atol=0.01)
        assert np.isclose(data[1], 0.467, atol=0.01)


class TestEnemyObservation:
    """Tests for EnemyObservation."""

    def test_observation_creation(self):
        """Test creating an enemy observation."""
        obs = EnemyObservation()
        assert obs is not None
        assert obs.get_dimension() > 0

    def test_compute_enemies(self, mock_state):
        """Test computing enemy observation."""
        obs = EnemyObservation()
        data = obs.compute(mock_state)

        assert data.shape[0] > 0
        # Should detect 1 visible enemy
        assert data[0] == 1.0


class TestZoneObservation:
    """Tests for ZoneObservation."""

    def test_observation_creation(self):
        """Test creating a zone observation."""
        obs = ZoneObservation()
        assert obs is not None
        assert obs.get_dimension() > 0

    def test_compute_zone(self, mock_state):
        """Test computing zone observation."""
        obs = ZoneObservation()
        data = obs.compute(mock_state)

        assert data.shape[0] > 0
        # Zone radius is in the observation
        assert data[-1] > 0  # Zone radius should be positive


class TestObservationBuilder:
    """Tests for ObservationBuilder."""

    def test_builder_creation(self):
        """Test creating an observation builder."""
        config = ObservationBuilderConfig(observation_types=["health", "position"])
        builder = ObservationBuilder(config=config)

        assert builder is not None
        assert builder.dimension > 0

    def test_build_observation(self, mock_state):
        """Test building complete observation."""
        config = ObservationBuilderConfig(
            observation_types=["health", "position", "enemies", "zone"]
        )
        builder = ObservationBuilder(config=config)

        result = builder.build(mock_state)

        assert result.data.shape == (builder.dimension,)
        assert result.names is not None
        assert len(result.names) == builder.dimension

    def test_add_observation(self):
        """Test adding observation to builder."""
        config = ObservationBuilderConfig(observation_types=[])
        builder = ObservationBuilder(config=config)

        initial_dim = builder.dimension
        builder.add_observation("health")
        assert builder.dimension > initial_dim

    def test_remove_observation(self):
        """Test removing observation from builder."""
        config = ObservationBuilderConfig(observation_types=["health"])
        builder = ObservationBuilder(config=config)

        initial_dim = builder.dimension
        builder.remove_observation("health")
        assert builder.dimension < initial_dim

    def test_build_dict(self, mock_state):
        """Test building observation as dictionary."""
        config = ObservationBuilderConfig(observation_types=["health"])
        builder = ObservationBuilder(config=config)

        obs_dict = builder.build_dict(mock_state)

        assert isinstance(obs_dict, dict)
        assert "health" in obs_dict
        assert "shield" in obs_dict

    def test_get_space(self):
        """Test getting observation space info."""
        config = ObservationBuilderConfig(observation_types=["health"])
        builder = ObservationBuilder(config=config)

        space = builder.get_space()

        assert space["shape"] == (builder.dimension,)
        assert space["dtype"] == np.float32
