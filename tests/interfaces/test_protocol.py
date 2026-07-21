"""
Tests for ZBGym Protocol Interfaces.

This module provides comprehensive tests for all protocol interfaces
to ensure they work correctly with runtime type checking.
"""

import pytest
import numpy as np
from typing import Any

from zbgym.interfaces.protocol import (
    GameState,
    GameEngine,
    GameAdapter,
    Entity,
    Player,
    Team,
    GameMap,
    Zone,
    Action,
    ObservationProvider,
    RewardProvider,
    ReplayProvider,
    DashboardProvider,
    CheckpointProvider,
)
from zbgym.interfaces.contracts import (
    Vector2D,
    Health,
    GameTime,
)
from zbgym.interfaces.exceptions import (
    InterfaceError,
    StateError,
    EntityError,
    ActionError,
    ProviderError,
)


class TestEntityProtocol:
    """Tests for Entity protocol."""
    
    def test_entity_protocol(self):
        """Test Entity protocol implementation."""
        class MyEntity:
            def __init__(self):
                self.id = "test_entity"
                self.position = Vector2D(x=10, y=20)
                self.is_active = True
        
        entity = MyEntity()
        assert isinstance(entity, Entity)
        assert entity.id == "test_entity"
        assert entity.position.x == 10


class TestPlayerProtocol:
    """Tests for Player protocol."""
    
    def test_player_protocol(self):
        """Test Player protocol implementation."""
        class MyPlayer:
            def __init__(self):
                self.id = "player_1"
                self.position = Vector2D(x=10, y=20)
                self.is_active = True
                self.team_id = "team_red"
                self.health = Health(current=100, max=100)
                self.is_alive = True
                self.velocity = Vector2D(x=5, y=-3)
        
        player = MyPlayer()
        assert isinstance(player, Player)
        assert player.team_id == "team_red"
        assert player.health.current == 100


class TestTeamProtocol:
    """Tests for Team protocol."""
    
    def test_team_protocol(self):
        """Test Team protocol implementation."""
        class MyTeam:
            def __init__(self):
                self.id = "team_blue"
                self.name = "Blue Team"
                self.score = 50
                self.player_ids = ["p1", "p2", "p3"]
        
        team = MyTeam()
        assert isinstance(team, Team)
        assert team.name == "Blue Team"
        assert len(team.player_ids) == 3


class TestGameMapProtocol:
    """Tests for GameMap protocol."""
    
    def test_map_protocol(self):
        """Test GameMap protocol implementation."""
        class MyMap:
            def __init__(self):
                self.width = 1000.0
                self.height = 800.0
            
            def is_valid_position(self, x: float, y: float) -> bool:
                return 0 <= x <= self.width and 0 <= y <= self.height
            
            def get_zone_at(self, x: float, y: float) -> Zone | None:
                return None
        
        map_obj = MyMap()
        assert isinstance(map_obj, GameMap)
        assert map_obj.width == 1000.0
        assert map_obj.is_valid_position(500, 400)
        assert not map_obj.is_valid_position(1500, 400)


class TestZoneProtocol:
    """Tests for Zone protocol."""
    
    def test_zone_protocol(self):
        """Test Zone protocol implementation."""
        class MyZone:
            def __init__(self):
                self.id = "safe_zone"
                self.center = Vector2D(x=500, y=400)
                self.radius = 100.0
                self.danger_level = 0.0
            
            def contains_point(self, x: float, y: float) -> bool:
                return self.center.distance_to(Vector2D(x, y)) <= self.radius
        
        zone = MyZone()
        assert isinstance(zone, Zone)
        assert zone.danger_level == 0.0
        assert zone.contains_point(500, 400)
        assert not zone.contains_point(700, 400)


class TestActionProtocol:
    """Tests for Action protocol."""
    
    def test_action_protocol(self):
        """Test Action protocol implementation."""
        class MyAction:
            def __init__(self):
                self.action_type = "movement"
            
            def to_array(self) -> np.ndarray:
                return np.array([1.0, 0.0, 0.0, 0.0])
        
        action = MyAction()
        assert isinstance(action, Action)
        assert action.action_type == "movement"
        arr = action.to_array()
        assert arr.shape == (4,)


class TestGameState:
    """Tests for GameState abstract class."""
    
    def test_game_state_abstract(self):
        """Test that GameState cannot be instantiated directly."""
        with pytest.raises(TypeError):
            GameState()
    
    def test_game_state_implementation(self):
        """Test implementing GameState."""
        class MyGameState(GameState):
            def __init__(self):
                self._tick = 100
                self._elapsed = 10.0
                self._active = True
                self._duration = 60.0
            
            @property
            def tick(self) -> int:
                return self._tick
            
            @property
            def elapsed_time(self) -> float:
                return self._elapsed
            
            @property
            def is_match_active(self) -> bool:
                return self._active
            
            @property
            def match_duration(self) -> float:
                return self._duration
            
            def get_players(self) -> list[Player]:
                return []
            
            def get_player(self, player_id: str) -> Player | None:
                return None
            
            def get_teams(self) -> list[Team]:
                return []
            
            def get_team(self, team_id: str) -> Team | None:
                return None
            
            def get_map(self) -> GameMap:
                class MyMap:
                    width = 1000.0
                    height = 800.0
                    def is_valid_position(self, x, y): return True
                    def get_zone_at(self, x, y): return None
                return MyMap()
            
            def get_zones(self) -> list[Zone]:
                return []
            
            def to_dict(self) -> dict[str, Any]:
                return {}
            
            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> GameState:
                return cls()
        
        state = MyGameState()
        assert state.tick == 100
        assert state.is_match_active
        assert len(state.get_players()) == 0


class TestGameEngine:
    """Tests for GameEngine abstract class."""
    
    def test_game_engine_abstract(self):
        """Test that GameEngine cannot be instantiated directly."""
        with pytest.raises(TypeError):
            GameEngine()
    
    def test_game_engine_implementation(self):
        """Test implementing GameEngine."""
        class MyEngine(GameEngine):
            def __init__(self):
                self._obs_space = None
                self._action_space = None
            
            @property
            def observation_space(self) -> Any:
                return self._obs_space
            
            @property
            def action_space(self) -> Any:
                return self._action_space
            
            @property
            def spec(self) -> Any | None:
                return None
            
            def reset(self, seed=None, options=None):
                return np.zeros(10), {}
            
            def step(self, action):
                return np.zeros(10), 0.0, False, False, {}
            
            def close(self):
                pass
        
        engine = MyEngine()
        obs, info = engine.reset()
        assert obs.shape == (10,)


class TestObservationProvider:
    """Tests for ObservationProvider abstract class."""
    
    def test_observation_provider_abstract(self):
        """Test that ObservationProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ObservationProvider()
    
    def test_observation_provider_implementation(self):
        """Test implementing ObservationProvider."""
        class MyObsProvider(ObservationProvider):
            def __init__(self):
                self._space = None
            
            def compute(self, state: GameState, agent_id: str) -> np.ndarray:
                return np.zeros(50)
            
            def get_space(self) -> Any:
                return self._space
        
        provider = MyObsProvider()
        obs = provider.compute(None, "agent_1")
        assert obs.shape == (50,)


class TestRewardProvider:
    """Tests for RewardProvider abstract class."""
    
    def test_reward_provider_abstract(self):
        """Test that RewardProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            RewardProvider()
    
    def test_reward_provider_implementation(self):
        """Test implementing RewardProvider."""
        class MyRewardProvider(RewardProvider):
            def compute(self, prev_state: GameState, current_state: GameState, agent_id: str) -> float:
                return 1.0
            
            def reset(self) -> None:
                pass
        
        provider = MyRewardProvider()
        reward = provider.compute(None, None, "agent_1")
        assert reward == 1.0


class TestReplayProvider:
    """Tests for ReplayProvider abstract class."""
    
    def test_replay_provider_abstract(self):
        """Test that ReplayProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ReplayProvider()
    
    def test_replay_provider_implementation(self):
        """Test implementing ReplayProvider."""
        class MyReplayProvider(ReplayProvider):
            def __init__(self):
                self.steps = []
            
            def record_step(self, state: GameState, action: Any, reward: float) -> None:
                self.steps.append((state, action, reward))
            
            def save(self, path: str) -> None:
                pass
            
            def load(self, path: str) -> None:
                pass
            
            def get_replay_data(self) -> dict[str, Any]:
                return {"steps": len(self.steps)}
        
        provider = MyReplayProvider()
        provider.record_step(None, {"move": 1}, 0.5)
        assert len(provider.steps) == 1
        assert provider.get_replay_data()["steps"] == 1


class TestDashboardProvider:
    """Tests for DashboardProvider abstract class."""
    
    def test_dashboard_provider_abstract(self):
        """Test that DashboardProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DashboardProvider()
    
    def test_dashboard_provider_implementation(self):
        """Test implementing DashboardProvider."""
        class MyDashboardProvider(DashboardProvider):
            def __init__(self):
                self.metrics = []
            
            def publish_metrics(self, metrics: dict[str, Any]) -> None:
                self.metrics.append(metrics)
            
            def publish_event(self, event_type: str, data: dict[str, Any]) -> None:
                pass
            
            def is_enabled(self) -> bool:
                return True
        
        provider = MyDashboardProvider()
        provider.publish_metrics({"loss": 0.5})
        assert len(provider.metrics) == 1
        assert provider.is_enabled()


class TestCheckpointProvider:
    """Tests for CheckpointProvider abstract class."""
    
    def test_checkpoint_provider_abstract(self):
        """Test that CheckpointProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CheckpointProvider()
    
    def test_checkpoint_provider_implementation(self):
        """Test implementing CheckpointProvider."""
        class MyCheckpointProvider(CheckpointProvider):
            def __init__(self):
                self.checkpoints = {}
            
            def save_checkpoint(self, path: str, data: dict[str, Any]) -> None:
                self.checkpoints[path] = data
            
            def load_checkpoint(self, path: str) -> dict[str, Any]:
                return self.checkpoints.get(path, {})
            
            def list_checkpoints(self, directory: str) -> list[str]:
                return list(self.checkpoints.keys())
        
        provider = MyCheckpointProvider()
        provider.save_checkpoint("ckpt_1", {"epoch": 1})
        assert "ckpt_1" in provider.list_checkpoints("")
        data = provider.load_checkpoint("ckpt_1")
        assert data["epoch"] == 1


class TestGameAdapter:
    """Tests for GameAdapter abstract class."""
    
    def test_game_adapter_abstract(self):
        """Test that GameAdapter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            GameAdapter()
    
    def test_game_adapter_implementation(self):
        """Test implementing GameAdapter."""
        class MockEngine(GameEngine):
            @property
            def observation_space(self): return None
            @property
            def action_space(self): return None
            @property
            def spec(self): return None
            def reset(self, seed=None, options=None): return np.zeros(10), {}
            def step(self, action): return np.zeros(10), 0.0, False, False, {}
            def close(self): pass
        
        class MockObsProvider(ObservationProvider):
            def compute(self, state, agent_id): return np.zeros(10)
            def get_space(self): return None
        
        class MockRewardProvider(RewardProvider):
            def compute(self, prev, curr, agent_id): return 0.0
            def reset(self): pass
        
        class MyAdapter(GameAdapter):
            def __init__(self):
                self._engine = MockEngine()
                self._obs = MockObsProvider()
                self._reward = MockRewardProvider()
            
            @property
            def engine(self) -> GameEngine:
                return self._engine
            
            def get_game_state(self) -> GameState:
                class SimpleState(GameState):
                    tick = 0
                    elapsed_time = 0.0
                    is_match_active = True
                    match_duration = 0.0
                    def get_players(self): return []
                    def get_player(self, pid): return None
                    def get_teams(self): return []
                    def get_team(self, tid): return None
                    def get_map(self):
                        class M:
                            width = 1000
                            height = 800
                            def is_valid_position(self, x, y): return True
                            def get_zone_at(self, x, y): return None
                        return M()
                    def get_zones(self): return []
                    def to_dict(self): return {}
                    @classmethod
                    def from_dict(cls, d): return cls()
                return SimpleState()
            
            def set_game_state(self, state: GameState) -> None:
                pass
            
            def get_observation_provider(self) -> ObservationProvider:
                return self._obs
            
            def get_reward_provider(self) -> RewardProvider:
                return self._reward
        
        adapter = MyAdapter()
        assert isinstance(adapter.engine, GameEngine)
        assert isinstance(adapter.get_observation_provider(), ObservationProvider)
        assert isinstance(adapter.get_reward_provider(), RewardProvider)
