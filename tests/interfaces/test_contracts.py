"""
Tests for ZBGym Interface Contracts.

This module provides comprehensive tests for all interface contracts
to ensure they work correctly and maintain expected behavior.
"""

import pytest
import numpy as np
from zbgym.interfaces.contracts import (
    Vector2D,
    Position,
    Velocity,
    Rotation,
    Health,
    Mana,
    Score,
    Experience,
    GameTime,
    TeamID,
    EntityID,
    Inventory,
    GameConfig,
)


class TestVector2D:
    """Tests for Vector2D contract."""
    
    def test_creation(self):
        """Test Vector2D creation."""
        vec = Vector2D(x=10.0, y=20.0)
        assert vec.x == 10.0
        assert vec.y == 20.0
    
    def test_zero(self):
        """Test zero vector creation."""
        vec = Vector2D.zero()
        assert vec.x == 0.0
        assert vec.y == 0.0
    
    def test_immutable(self):
        """Test that Vector2D is immutable."""
        vec = Vector2D(x=1.0, y=2.0)
        with pytest.raises(Exception):  # frozen dataclass
            vec.x = 3.0
    
    def test_distance_to(self):
        """Test distance calculation."""
        vec1 = Vector2D(x=0.0, y=0.0)
        vec2 = Vector2D(x=3.0, y=4.0)
        assert vec1.distance_to(vec2) == 5.0
    
    def test_magnitude(self):
        """Test magnitude calculation."""
        vec = Vector2D(x=3.0, y=4.0)
        assert vec.magnitude() == 5.0
    
    def test_normalized(self):
        """Test normalization."""
        vec = Vector2D(x=3.0, y=4.0)
        norm = vec.normalized()
        assert norm.x == pytest.approx(0.6)
        assert norm.y == pytest.approx(0.8)
    
    def test_normalized_zero(self):
        """Test normalization of zero vector."""
        vec = Vector2D.zero()
        norm = vec.normalized()
        assert norm.x == 0.0
        assert norm.y == 0.0
    
    def test_dot(self):
        """Test dot product."""
        vec1 = Vector2D(x=1.0, y=2.0)
        vec2 = Vector2D(x=3.0, y=4.0)
        assert vec1.dot(vec2) == 11.0
    
    def test_angle_to(self):
        """Test angle calculation."""
        vec1 = Vector2D(x=0.0, y=0.0)
        vec2 = Vector2D(x=1.0, y=0.0)
        angle = vec1.angle_to(vec2)
        assert angle == pytest.approx(0.0)
    
    def test_to_array(self):
        """Test conversion to numpy array."""
        vec = Vector2D(x=1.0, y=2.0)
        arr = vec.to_array()
        assert isinstance(arr, np.ndarray)
        assert arr[0] == 1.0
        assert arr[1] == 2.0
    
    def test_from_array(self):
        """Test creation from numpy array."""
        arr = np.array([3.0, 4.0])
        vec = Vector2D.from_array(arr)
        assert vec.x == 3.0
        assert vec.y == 4.0
    
    def test_from_angle(self):
        """Test creation from angle."""
        vec = Vector2D.from_angle(0.0, 1.0)
        assert vec.x == pytest.approx(1.0)
        assert vec.y == pytest.approx(0.0)


class TestPosition:
    """Tests for Position contract."""
    
    def test_creation(self):
        """Test Position creation."""
        pos = Position(x=10.0, y=20.0, z=30.0)
        assert pos.x == 10.0
        assert pos.y == 20.0
        assert pos.z == 30.0
    
    def test_default_z(self):
        """Test default Z value."""
        pos = Position(x=10.0, y=20.0)
        assert pos.z == 0.0
    
    def test_to_vector2d(self):
        """Test conversion to Vector2D."""
        pos = Position(x=10.0, y=20.0, z=30.0)
        vec = pos.to_vector2d()
        assert vec.x == 10.0
        assert vec.y == 20.0
    
    def test_distance_to(self):
        """Test 3D distance calculation."""
        pos1 = Position(x=0.0, y=0.0, z=0.0)
        pos2 = Position(x=1.0, y=1.0, z=1.0)
        dist = pos1.distance_to(pos2)
        assert dist == pytest.approx(np.sqrt(3.0))
    
    def test_to_array(self):
        """Test conversion to numpy array."""
        pos = Position(x=1.0, y=2.0, z=3.0)
        arr = pos.to_array()
        assert np.array_equal(arr, [1.0, 2.0, 3.0])


class TestVelocity:
    """Tests for Velocity contract."""
    
    def test_creation(self):
        """Test Velocity creation."""
        vel = Velocity(dx=10.0, dy=20.0, dz=30.0)
        assert vel.dx == 10.0
        assert vel.dy == 20.0
        assert vel.dz == 30.0
    
    def test_speed(self):
        """Test speed calculation."""
        vel = Velocity(dx=3.0, dy=4.0, dz=0.0)
        assert vel.speed() == 5.0
    
    def test_to_vector2d(self):
        """Test conversion to Vector2D."""
        vel = Velocity(dx=10.0, dy=20.0, dz=30.0)
        vec = vel.to_vector2d()
        assert vec.x == 10.0
        assert vec.y == 20.0
    
    def test_to_array(self):
        """Test conversion to numpy array."""
        vel = Velocity(dx=1.0, dy=2.0, dz=3.0)
        arr = vel.to_array()
        assert np.array_equal(arr, [1.0, 2.0, 3.0])


class TestRotation:
    """Tests for Rotation contract."""
    
    def test_creation(self):
        """Test Rotation creation."""
        rot = Rotation(yaw=1.0, pitch=0.5, roll=0.1)
        assert rot.yaw == 1.0
        assert rot.pitch == 0.5
        assert rot.roll == 0.1
    
    def test_default_pitch_roll(self):
        """Test default pitch and roll."""
        rot = Rotation(yaw=1.0)
        assert rot.pitch == 0.0
        assert rot.roll == 0.0
    
    def test_from_degrees(self):
        """Test creation from degrees."""
        rot = Rotation.from_degrees(yaw=90, pitch=45, roll=0)
        assert rot.yaw == pytest.approx(np.pi / 2)
        assert rot.pitch == pytest.approx(np.pi / 4)
    
    def test_to_degrees(self):
        """Test conversion to degrees."""
        rot = Rotation(yaw=np.pi / 2, pitch=np.pi / 4, roll=0.0)
        yaw_deg, pitch_deg, roll_deg = rot.to_degrees()
        assert yaw_deg == pytest.approx(90.0)
        assert pitch_deg == pytest.approx(45.0)
    
    def test_forward_vector(self):
        """Test forward vector calculation."""
        rot = Rotation(yaw=0.0)
        forward = rot.forward_vector()
        assert forward.x == pytest.approx(1.0)
        assert forward.y == pytest.approx(0.0)


class TestHealth:
    """Tests for Health contract."""
    
    def test_creation(self):
        """Test Health creation."""
        health = Health(current=80.0, max=100.0, regen=1.0)
        assert health.current == 80.0
        assert health.max == 100.0
        assert health.regen == 1.0
    
    def test_default_values(self):
        """Test default values."""
        health = Health()
        assert health.current == 100.0
        assert health.max == 100.0
        assert health.regen == 0.0
    
    def test_ratio(self):
        """Test health ratio calculation."""
        health = Health(current=50.0, max=100.0)
        assert health.ratio == 0.5
    
    def test_ratio_clamped(self):
        """Test ratio clamping."""
        health = Health(current=150.0, max=100.0)
        assert health.ratio == 1.0
    
    def test_ratio_zero_max(self):
        """Test ratio with zero max."""
        health = Health(current=50.0, max=0.0)
        assert health.ratio == 0.0
    
    def test_is_dead(self):
        """Test dead check."""
        health_alive = Health(current=50.0)
        health_dead = Health(current=0.0)
        assert not health_alive.is_dead
        assert health_dead.is_dead
    
    def test_is_full(self):
        """Test full check."""
        health_full = Health(current=100.0)
        health_not_full = Health(current=50.0)
        assert health_full.is_full
        assert not health_not_full.is_full


class TestMana:
    """Tests for Mana contract."""
    
    def test_creation(self):
        """Test Mana creation."""
        mana = Mana(current=80.0, max=100.0, regen=2.0)
        assert mana.current == 80.0
        assert mana.max == 100.0
    
    def test_ratio(self):
        """Test mana ratio."""
        mana = Mana(current=25.0, max=100.0)
        assert mana.ratio == 0.25
    
    def test_is_empty(self):
        """Test empty check."""
        mana_empty = Mana(current=0.0)
        mana_not_empty = Mana(current=50.0)
        assert mana_empty.is_empty
        assert not mana_not_empty.is_empty
    
    def test_can_cast(self):
        """Test can_cast check."""
        mana = Mana(current=10.0)
        assert mana.can_cast


class TestScore:
    """Tests for Score contract."""
    
    def test_creation(self):
        """Test Score creation."""
        score = Score(value=100, kills=5, deaths=2, assists=10)
        assert score.value == 100
        assert score.kills == 5
        assert score.deaths == 2
        assert score.assists == 10
    
    def test_kda(self):
        """Test KDA calculation."""
        score = Score(kills=5, deaths=2, assists=10)
        assert score.kda == 7.5
    
    def test_kda_no_deaths(self):
        """Test KDA with no deaths."""
        score = Score(kills=5, deaths=0, assists=10)
        assert score.kda == 15.0
    
    def test_other(self):
        """Test other score components."""
        score = Score(other={"captures": 3, "blocks": 5})
        assert score.other["captures"] == 3


class TestExperience:
    """Tests for Experience contract."""
    
    def test_creation(self):
        """Test Experience creation."""
        xp = Experience(level=5, current=50.0, required=100.0, total=500.0)
        assert xp.level == 5
        assert xp.current == 50.0
    
    def test_ratio(self):
        """Test level progress ratio."""
        xp = Experience(current=50.0, required=100.0)
        assert xp.ratio == 0.5
    
    def test_ratio_zero_required(self):
        """Test ratio with zero required."""
        xp = Experience(current=50.0, required=0.0)
        assert xp.ratio == 0.0


class TestGameTime:
    """Tests for GameTime contract."""
    
    def test_creation(self):
        """Test GameTime creation."""
        time = GameTime(tick=100, elapsed=10.0, duration=60.0)
        assert time.tick == 100
        assert time.elapsed == 10.0
        assert time.duration == 60.0
    
    def test_is_match_active(self):
        """Test match active check."""
        time_active = GameTime(elapsed=10.0, duration=60.0)
        time_ended = GameTime(elapsed=70.0, duration=60.0)
        time_unlimited = GameTime(elapsed=100.0, duration=0.0)
        assert time_active.is_match_active
        assert not time_ended.is_match_active
        assert time_unlimited.is_match_active
    
    def test_remaining(self):
        """Test remaining time calculation."""
        time = GameTime(elapsed=10.0, duration=60.0)
        assert time.remaining == 50.0
    
    def test_remaining_unlimited(self):
        """Test remaining with unlimited duration."""
        time = GameTime(elapsed=10.0, duration=0.0)
        assert time.remaining == float('inf')
    
    def test_progress(self):
        """Test progress calculation."""
        time = GameTime(elapsed=30.0, duration=60.0)
        assert time.progress == 0.5
    
    def test_progress_unlimited(self):
        """Test progress with unlimited duration."""
        time = GameTime(elapsed=100.0, duration=0.0)
        assert time.progress == 0.0


class TestTeamID:
    """Tests for TeamID contract."""
    
    def test_creation(self):
        """Test TeamID creation."""
        team_id = TeamID(value="team_red")
        assert team_id.value == "team_red"
    
    def test_str(self):
        """Test string conversion."""
        team_id = TeamID(value="team_blue")
        assert str(team_id) == "team_blue"
    
    def test_hash(self):
        """Test hashing."""
        team_id1 = TeamID(value="team_red")
        team_id2 = TeamID(value="team_red")
        assert hash(team_id1) == hash(team_id2)


class TestEntityID:
    """Tests for EntityID contract."""
    
    def test_creation(self):
        """Test EntityID creation."""
        entity_id = EntityID(value="player_1")
        assert entity_id.value == "player_1"
    
    def test_str(self):
        """Test string conversion."""
        entity_id = EntityID(value="enemy_1")
        assert str(entity_id) == "enemy_1"
    
    def test_hash(self):
        """Test hashing."""
        entity_id1 = EntityID(value="player_1")
        entity_id2 = EntityID(value="player_1")
        assert hash(entity_id1) == hash(entity_id2)


class TestInventory:
    """Tests for Inventory contract."""
    
    def test_creation(self):
        """Test Inventory creation."""
        inv = Inventory(capacity=10)
        assert inv.capacity == 10
        assert len(inv.items) == 0
    
    def test_add(self):
        """Test adding items."""
        inv = Inventory()
        result = inv.add("sword", 1)
        assert result
        assert inv.count("sword") == 1
    
    def test_add_full(self):
        """Test adding to full inventory."""
        inv = Inventory(capacity=1)
        inv.add("sword")
        result = inv.add("shield")  # Different item, inventory full
        assert not result
    
    def test_add_existing(self):
        """Test adding existing item to full inventory."""
        inv = Inventory(capacity=1)
        inv.add("sword")
        result = inv.add("sword")  # Same item, should work
        assert result
    
    def test_remove(self):
        """Test removing items."""
        inv = Inventory()
        inv.add("sword", 2)
        result = inv.remove("sword", 1)
        assert result
        assert inv.count("sword") == 1
    
    def test_remove_not_enough(self):
        """Test removing more than available."""
        inv = Inventory()
        inv.add("sword", 1)
        result = inv.remove("sword", 2)
        assert not result
    
    def test_remove_last(self):
        """Test removing last of item."""
        inv = Inventory()
        inv.add("sword")
        inv.remove("sword")
        assert inv.count("sword") == 0
        assert "sword" not in inv.items
    
    def test_has(self):
        """Test has check."""
        inv = Inventory()
        inv.add("sword", 2)
        assert inv.has("sword", 1)
        assert inv.has("sword", 2)
        assert not inv.has("sword", 3)
    
    def test_count(self):
        """Test count."""
        inv = Inventory()
        assert inv.count("sword") == 0
        inv.add("sword", 3)
        assert inv.count("sword") == 3


class TestGameConfig:
    """Tests for GameConfig contract."""
    
    def test_creation(self):
        """Test GameConfig creation."""
        config = GameConfig(
            name="TestGame-v1",
            max_players=8,
            max_teams=4,
            match_duration=300.0,
        )
        assert config.name == "TestGame-v1"
        assert config.max_players == 8
        assert config.max_teams == 4
    
    def test_defaults(self):
        """Test default values."""
        config = GameConfig()
        assert config.name == "Game-v0"
        assert config.max_players == 10
        assert config.max_teams == 2
        assert config.match_duration == 600.0
        assert not config.allow_respawn
        assert config.respawn_time == 5.0
    
    def test_to_dict(self):
        """Test serialization."""
        config = GameConfig(name="Test")
        data = config.to_dict()
        assert data["name"] == "Test"
        assert "max_players" in data
    
    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "name": "LoadedGame",
            "max_players": 4,
        }
        config = GameConfig.from_dict(data)
        assert config.name == "LoadedGame"
        assert config.max_players == 4
