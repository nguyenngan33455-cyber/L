# ZBGym Multi-Game Architecture Plan

## Executive Summary

This document defines the architecture for transforming ZBGym from a BattleArena-focused framework into a generic multi-game reinforcement learning platform.

---

## Part 1: Current Architecture Analysis

### 1.1 Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CURRENT ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │   make.py        │
                    │   (Entry Point)  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  BattleArena     │
                    │  (Core Engine)   │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌────────────────┐  ┌────────────────┐
│ Observation   │  │     Reward      │  │    Plugin      │
│               │  │                │  │                │
│ - base.py     │  │ - base.py      │  │ - character.py │
│ - enemy.py    │  │ - combat.py    │  │ - weapon.py    │
│ - health.py   │  │ - survival.py  │  │ - skill.py     │
│ - position.py │  │ - utility.py   │  │                │
│ - zone.py     │  │                │  │                │
└───────┬───────┘  └───────┬────────┘  └───────┬────────┘
        │                  │                    │
        └──────────────────┴────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Replay         │
                    │   Recorder       │
                    └──────────────────┘
```

### 1.2 Coupling Points

| Module | Depends On | Coupling Type |
|--------|-----------|---------------|
| `observation/*` | `BattleArenaState` | Direct import |
| `reward/*` | `BattleArenaState` | Direct import |
| `plugins/*` | `CharacterState` | Direct import |
| `rendering/*` | `BattleArena` | Direct import |
| `ZoobaAdapter` | `BattleArena` | Composition |

### 1.3 BattleArenaState Fields

```python
@dataclass
class BattleArenaState:
    # Timing
    tick: int
    elapsed_time: float
    match_active: bool
    match_duration: float
    
    # Entities
    characters: dict[str, CharacterState]
    
    # Zone
    safe_zone_center: Vector2D
    safe_zone_radius: float
    danger_zone_radius: float
    
    # Scores
    scores: dict[str, int]
```

### 1.4 CharacterState Fields

```python
@dataclass
class CharacterState:
    id: str
    position: Vector2D
    velocity: Vector2D
    health: float
    shield: float
    energy: float
    is_alive: bool
    team: str
    
    # Stats
    kills: int
    deaths: int
    assists: int
    damage_dealt: float
    damage_taken: float
    healing: float
    
    # Cooldowns
    ability_cooldowns: dict[str, float]
```

---

## Part 2: Generic Interface Design

### 2.1 Core Interface Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GENERIC INTERFACE HIERARCHY                     │
└─────────────────────────────────────────────────────────────────────┘

                          ┌─────────────┐
                          │ GameState   │  (Abstract)
                          └──────┬──────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌────────────────┐      ┌────────────────┐
│ BattleState   │      │  MobaState     │      │  ShooterState   │
│ (BattleArena) │      │  (Future)      │      │  (Future)      │
└───────────────┘      └────────────────┘      └────────────────┘


                          ┌─────────────┐
                          │ GameEntity  │  (Protocol)
                          └──────┬──────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌────────────────┐      ┌────────────────┐
│ Character     │      │  Unit          │      │  Agent         │
│ (Player)      │      │  (MOBA)        │      │  (FPS)         │
└───────────────┘      └────────────────┘      └────────────────┘


                          ┌─────────────┐
                          │ Action      │  (Protocol)
                          └──────┬──────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌────────────────┐      ┌────────────────┐
│ MovementAction│      │  AbilityAction │      │  TargetAction  │
│ + move_x     │      │  + ability_id  │      │  + target_id   │
│ + move_y     │      │  + target_pos  │      │  + action_type │
└───────────────┘      └────────────────┘      └────────────────┘
```

### 2.2 Interface Definitions

#### Core Interfaces

```python
# ===== CORE INTERFACES =====

from abc import ABC, abstractmethod
from typing import Protocol, Any, Generic, TypeVar
import numpy as np

# --- Game State ---
class GameState(ABC):
    """Abstract base for all game states."""
    
    @property
    @abstractmethod
    def tick(self) -> int: ...
    
    @property
    @abstractmethod
    def elapsed_time(self) -> float: ...
    
    @property
    @abstractmethod
    def is_match_active(self) -> bool: ...
    
    @abstractmethod
    def get_entities(self) -> list['Entity']: ...
    
    @abstractmethod
    def get_teams(self) -> list['Team']: ...
    
    @abstractmethod
    def to_dict(self) -> dict[str, Any]: ...
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> 'GameState': ...


# --- Entity ---
class Entity(ABC):
    """Abstract base for all game entities."""
    
    @property
    @abstractmethod
    def id(self) -> str: ...
    
    @property
    @abstractmethod
    def position(self) -> 'Vector': ...
    
    @property
    @abstractmethod
    def is_active(self) -> bool: ...


# --- Player/Agent ---
class Player(Entity, ABC):
    """Abstract base for players/agents."""
    
    @property
    @abstractmethod
    def team_id(self) -> str | None: ...
    
    @property
    @abstractmethod
    def health(self) -> float: ...
    
    @property
    @abstractmethod
    def energy(self) -> float: ...
    
    @property
    @abstractmethod
    def is_alive(self) -> bool: ...


# --- Team ---
class Team(ABC):
    """Abstract base for teams/factions."""
    
    @property
    @abstractmethod
    def id(self) -> str: ...
    
    @property
    @abstractmethod
    def score(self) -> int: ...
    
    @abstractmethod
    def get_players(self) -> list[Player]: ...


# --- Map ---
class GameMap(ABC):
    """Abstract base for game maps."""
    
    @property
    @abstractmethod
    def width(self) -> float: ...
    
    @property
    @abstractmethod
    def height(self) -> float: ...
    
    @abstractmethod
    def is_valid_position(self, x: float, y: float) -> bool: ...
    
    @abstractmethod
    def get_zone(self, x: float, y: float) -> 'Zone': ...


# --- Zone ---
class Zone(ABC):
    """Abstract base for map zones."""
    
    @property
    @abstractmethod
    def center(self) -> 'Vector': ...
    
    @property
    @abstractmethod
    def radius(self) -> float: ...
    
    @property
    @abstractmethod
    def danger_level(self) -> float: ...  # 0.0 to 1.0


# --- Action ---
class Action(Protocol):
    """Protocol for all actions."""
    
    def to_array(self) -> np.ndarray: ...


class MovementAction:
    """Movement action with direction."""
    
    def __init__(self, dx: float, dy: float):
        self.dx = dx
        self.dy = dy


class AbilityAction:
    """Ability/skill activation."""
    
    def __init__(self, ability_id: str, target_x: float | None = None, 
                 target_y: float | None = None, target_entity: str | None = None):
        self.ability_id = ability_id
        self.target_x = target_x
        self.target_y = target_y
        self.target_entity = target_entity


# --- Vector (Generic) ---
class Vector(ABC):
    """Abstract base for vectors."""
    
    @property
    @abstractmethod
    def x(self) -> float: ...
    
    @property
    @abstractmethod
    def y(self) -> float: ...
    
    @abstractmethod
    def distance_to(self, other: 'Vector') -> float: ...
    
    @abstractmethod
    def __add__(self, other: 'Vector') -> 'Vector': ...
    
    @abstractmethod
    def __sub__(self, other: 'Vector') -> 'Vector': ...
```

#### Game Engine Interface

```python
# ===== GAME ENGINE INTERFACES =====

class GameEngine(ABC):
    """Abstract base for game engines."""
    
    @abstractmethod
    def reset(self, seed: int | None = None) -> tuple[np.ndarray, dict]: ...
    
    @abstractmethod
    def step(self, action: Any) -> tuple[np.ndarray, float, bool, bool, dict]: ...
    
    @abstractmethod
    def get_state(self) -> GameState: ...
    
    @abstractmethod
    def set_state(self, state: GameState) -> None: ...
    
    @abstractmethod
    def close(self) -> None: ...
    
    @property
    @abstractmethod
    def observation_space(self) -> Any: ...
    
    @property
    @abstractmethod
    def action_space(self) -> Any: ...


class GameAdapter(ABC):
    """
    Adapter pattern for wrapping game-specific engines.
    
    Translates game-specific logic into generic interfaces.
    """
    
    @property
    @abstractmethod
    def engine(self) -> GameEngine: ...
    
    @abstractmethod
    def get_game_state(self) -> GameState: ...
    
    @abstractmethod
    def set_game_state(self, state: GameState) -> None: ...
    
    @abstractmethod
    def get_observation_provider(self) -> 'ObservationProvider': ...
    
    @abstractmethod
    def get_reward_provider(self) -> 'RewardProvider': ...
```

#### Provider Interfaces

```python
# ===== PROVIDER INTERFACES =====

class ObservationProvider(ABC):
    """Provider for computing observations."""
    
    @abstractmethod
    def compute(self, state: GameState, agent_id: str) -> np.ndarray: ...
    
    @abstractmethod
    def get_space(self) -> Any: ...


class RewardProvider(ABC):
    """Provider for computing rewards."""
    
    @abstractmethod
    def compute(self, prev_state: GameState, current_state: GameState, 
                agent_id: str) -> float: ...
    
    @abstractmethod
    def reset(self) -> None: ...


class ReplayProvider(ABC):
    """Provider for recording replays."""
    
    @abstractmethod
    def record_step(self, state: GameState, action: Any, reward: float) -> None: ...
    
    @abstractmethod
    def save(self, path: str) -> None: ...
    
    @abstractmethod
    def load(self, path: str) -> None: ...


class DashboardProvider(ABC):
    """Provider for dashboard integration."""
    
    @abstractmethod
    def publish_metrics(self, metrics: dict) -> None: ...
    
    @abstractmethod
    def publish_event(self, event_type: str, data: dict) -> None: ...
```

#### Game-Specific Entity Interfaces

```python
# ===== GAME-SPECIFIC ENTITY INTERFACES =====

class Weapon(ABC):
    """Interface for weapons."""
    
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def damage(self) -> float: ...
    
    @property
    @abstractmethod
    def fire_rate(self) -> float: ...
    
    @property
    @abstractmethod
    def range(self) -> float: ...


class Skill(ABC):
    """Interface for abilities/skills."""
    
    @property
    @abstractmethod
    def id(self) -> str: ...
    
    @property
    @abstractmethod
    def cooldown(self) -> float: ...
    
    @property
    @abstractmethod
    def energy_cost(self) -> float: ...
    
    @abstractmethod
    def is_ready(self, state: GameState, player_id: str) -> bool: ...


class Projectile(ABC):
    """Interface for projectiles."""
    
    @property
    @abstractmethod
    def position(self) -> Vector: ...
    
    @property
    @abstractmethod
    def velocity(self) -> Vector: ...
    
    @property
    @abstractmethod
    def owner_id(self) -> str: ...
    
    @abstractmethod
    def update(self, dt: float) -> None: ...
```

---

## Part 3: Adapter Architecture

### 3.1 Adapter Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ADAPTER ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────┘

                          ┌─────────────────┐
                          │   GameAdapter   │  (Abstract)
                          │   (Base Class)  │
                          └────────┬────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ BattleArena     │      │   MOBA          │      │   Shooter       │
│ Adapter        │      │   Adapter       │      │   Adapter       │
│                 │      │   (Future)      │      │   (Future)      │
└─────────────────┘      └─────────────────┘      └─────────────────┘
          │
          ▼
┌─────────────────┐
│ Zooba           │
│ Adapter         │  (Extends BattleArena Adapter)
└─────────────────┘


Adapter Responsibilities:

┌─────────────────────────────────────────────────────────────────────┐
│                         GameAdapter                                 │
├─────────────────────────────────────────────────────────────────────┤
│  + engine: GameEngine                                               │
│  + observation_provider: ObservationProvider                        │
│  + reward_provider: RewardProvider                                  │
│  + replay_provider: ReplayProvider                                 │
│  + dashboard_provider: DashboardProvider                            │
├─────────────────────────────────────────────────────────────────────┤
│  + get_game_state() -> GameState                                   │
│  + set_game_state(state: GameState) -> None                        │
│  + get_observation(agent_id: str) -> np.ndarray                    │
│  + compute_reward(prev_state, current_state, agent_id) -> float    │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Example Adapter Implementation

```python
# ===== BATTLE ARENA ADAPTER =====

class BattleArenaAdapter(GameAdapter):
    """
    Adapter for BattleArena environment.
    
    Wraps BattleArena with generic GameAdapter interface.
    """
    
    def __init__(
        self,
        config: EnvironmentConfig | None = None,
        render_mode: str | None = None,
        obs_config: dict | None = None,
        reward_config: dict | None = None,
    ):
        # Create the internal engine
        self._engine = BattleArena(
            config=config,
            render_mode=render_mode,
            obs_config=obs_config,
            reward_config=reward_config,
        )
        
        # Create providers (these will be refactored to use GameState)
        self._obs_provider = BattleArenaObservationProvider(self._engine)
        self._reward_provider = BattleArenaRewardProvider(self._engine)
        self._replay_provider = BattleArenaReplayProvider()
        self._dashboard_provider = BattleArenaDashboardProvider()
    
    @property
    def engine(self) -> BattleArena:
        return self._engine
    
    def get_game_state(self) -> BattleArenaGameState:
        """Convert BattleArenaState to generic GameState."""
        arena_state = self._engine.get_state()
        return BattleArenaGameState.from_battle_arena_state(arena_state)
    
    def set_game_state(self, state: GameState) -> None:
        """Convert generic GameState back to BattleArenaState."""
        if isinstance(state, BattleArenaGameState):
            arena_state = state.to_battle_arena_state()
            self._engine.set_state(arena_state)
        else:
            raise TypeError(f"Cannot convert {type(state)} to BattleArenaState")
    
    def get_observation_provider(self) -> ObservationProvider:
        return self._obs_provider
    
    def get_reward_provider(self) -> RewardProvider:
        return self._reward_provider
    
    # ... etc
```

### 3.3 Adapter Factory

```python
# ===== ADAPTER FACTORY =====

class AdapterFactory:
    """Factory for creating game adapters."""
    
    _adapters: dict[str, type[GameAdapter]] = {
        'BattleArena-v0': BattleArenaAdapter,
        'BattleArena-v1': BattleArenaAdapter,
        'BattleArenaTeam-v1': BattleArenaTeamAdapter,
        'BattleArenaSurvival-v1': BattleArenaSurvivalAdapter,
        'Zooba-v1': ZoobaAdapter,
        # Future games can be registered here
        # 'Moba-v1': MobaAdapter,
        # 'Shooter-v1': ShooterAdapter,
    }
    
    @classmethod
    def register(cls, env_id: str, adapter_class: type[GameAdapter]) -> None:
        """Register a new adapter."""
        cls._adapters[env_id] = adapter_class
    
    @classmethod
    def create(cls, env_id: str, **kwargs) -> GameAdapter:
        """Create an adapter for the given environment."""
        if env_id not in cls._adapters:
            raise KeyError(f"No adapter registered for {env_id}")
        
        return cls._adapters[env_id](**kwargs)
```

---

## Part 4: Observation Refactoring Plan

### 4.1 Current Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CURRENT OBSERVATION FLOW                        │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │ Observation  │
  │  Builder     │
  └──────┬───────┘
         │
         │ Uses BattleArenaState directly
         ▼
  ┌──────────────┐      ┌──────────────────┐
  │   Enemy      │ ───► │  BattleArena     │
  │ Observation  │      │    State         │
  └──────────────┘      └──────────────────┘
         │
         │ Uses CharacterState directly
         ▼
  ┌──────────────┐
  │  Position    │
  │ Observation  │
  └──────────────┘
```

### 4.2 Target Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TARGET OBSERVATION FLOW                          │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │ Observation  │         ┌─────────────────┐
  │  Provider    │ ◄────── │   GameState     │  (Generic Interface)
  └──────┬───────┘         │   (Abstract)    │
         │                 └─────────────────┘
         │
         │ Adapters convert game-specific to generic
         ▼
  ┌──────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │   Enemy      │ ◄─── │  BattleArena     │ ◄─── │   BattleArena    │
  │ Provider     │      │  Adapter         │      │     State        │
  └──────────────┘      └──────────────────┘      └──────────────────┘
         │
         ▼
  ┌──────────────┐
  │  Position    │
  │ Provider     │
  └──────────────┘
```

### 4.3 Refactoring Steps

```
┌─────────────────────────────────────────────────────────────────────┐
│                     OBSERVATION REFACTORING                         │
└─────────────────────────────────────────────────────────────────────┘

STAGE 1: Create generic GameState interface
  - Create zbgym/interfaces/state.py
  - Define GameState abstract class
  - Define Entity, Player, Team protocols
  - Define Vector interface

STAGE 2: Create BattleArenaGameState
  - Create zbgym/env/adapters/battle_arena_state.py
  - Implement GameState interface
  - Add conversion methods (to/from BattleArenaState)

STAGE 3: Update ObservationProvider interface
  - Modify observation/base.py
  - Change from BattleArenaState to GameState
  - Update method signatures

STAGE 4: Update concrete providers
  - observation/enemy.py
  - observation/health.py
  - observation/position.py
  - observation/zone.py
  - All now use GameState

STAGE 5: Update Adapter
  - Modify BattleArenaAdapter
  - Implement get_game_state() conversion
  - Update observation_provider to use GameState
```

### 4.4 Code Changes

```python
# ===== BEFORE (tight coupling) =====

class EnemyObservation(BaseObservation):
    def compute(self, state: BattleArenaState, agent_id: str) -> np.ndarray:
        enemies = []
        for char_id, char in state.characters.items():
            if char_id != agent_id and char.is_alive:
                enemies.append(char)
        # ... compute observation
        return observation


# ===== AFTER (decoupled) =====

class EnemyObservation(BaseObservation):
    def compute(self, state: GameState, agent_id: str) -> np.ndarray:
        # Use generic interface
        entities = state.get_entities()
        enemies = [e for e in entities if e.id != agent_id and e.is_active]
        # ... compute observation
        return observation
```

---

## Part 5: Reward Refactoring Plan

### 5.1 Current Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       CURRENT REWARD FLOW                           │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │   Reward     │
  │   Builder    │
  └──────┬───────┘
         │
         │ Uses BattleArenaState directly
         ▼
  ┌──────────────┐      ┌──────────────────┐
  │   Combat     │ ───► │  BattleArena     │
  │   Reward     │      │    State         │
  └──────────────┘      └──────────────────┘
```

### 5.2 Target Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      TARGET REWARD FLOW                             │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐         ┌─────────────────┐
  │    Reward    │ ◄────── │   GameState     │  (Generic Interface)
  │   Provider   │         │   (Abstract)    │
  └──────┬───────┘         └─────────────────┘
         │
         │ Adapters convert game-specific to generic
         ▼
  ┌──────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │   Combat     │ ◄─── │  BattleArena     │ ◄─── │   BattleArena    │
  │   Provider   │      │  Adapter         │      │     State        │
  └──────────────┘      └──────────────────┘      └──────────────────┘
```

### 5.3 Refactoring Steps

```
┌─────────────────────────────────────────────────────────────────────┐
│                       REWARD REFACTORING                            │
└─────────────────────────────────────────────────────────────────────┘

STAGE 1: Update RewardProvider interface
  - Modify reward/base.py
  - Change signature from BattleArenaState to GameState
  - Add GameState type hints

STAGE 2: Update concrete reward providers
  - reward/combat.py
  - reward/survival.py
  - reward/utility.py
  - All now use GameState

STAGE 3: Update RewardBuilder
  - reward/builder.py
  - Build rewards using GameState interface
```

### 5.4 Code Changes

```python
# ===== BEFORE (tight coupling) =====

class CombatReward(BaseReward):
    def compute(
        self, 
        prev_state: BattleArenaState, 
        current_state: BattleArenaState,
        agent_id: str
    ) -> float:
        prev_char = prev_state.characters[agent_id]
        curr_char = current_state.characters[agent_id]
        reward = curr_char.kills - prev_char.kills
        return reward * self.kill_reward


# ===== AFTER (decoupled) =====

class CombatReward(BaseReward):
    def compute(
        self, 
        prev_state: GameState, 
        current_state: GameState,
        agent_id: str
    ) -> float:
        # Use generic interface
        prev_entities = {e.id: e for e in prev_state.get_entities()}
        curr_entities = {e.id: e for e in current_state.get_entities()}
        
        if agent_id in prev_entities and agent_id in curr_entities:
            prev_player = prev_entities[agent_id]
            curr_player = curr_entities[agent_id]
            reward = curr_player.stats.kills - prev_player.stats.kills
            return reward * self.kill_reward
        return 0.0
```

---

## Part 6: Migration Roadmap

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MIGRATION ROADMAP                           │
└─────────────────────────────────────────────────────────────────────┘

╔═════════════════════════════════════════════════════════════════════╗
║  STAGE 1: Interface Foundation (Week 1-2)                          ║
╠═════════════════════════════════════════════════════════════════════╣
║  • Create zbgym/interfaces/ directory                              ║
║  • Define GameState, Entity, Player, Team interfaces               ║
║  • Define Action, Vector interfaces                                ║
║  • Define Provider interfaces (Observation, Reward, etc.)          ║
║  • NO changes to existing code                                     ║
║  • Add tests for new interfaces                                    ║
║                                                                     ║
║  EXIT CRITERIA: All interfaces compile, tests pass                 ║
╚═════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
╔═════════════════════════════════════════════════════════════════════╗
║  STAGE 2: BattleArena Adapter (Week 3-4)                           ║
╠═════════════════════════════════════════════════════════════════════╣
║  • Create BattleArenaGameState implementing GameState               ║
║  • Create BattleArenaAdapter implementing GameAdapter               ║
║  • Keep existing BattleArena class 100% compatible                 ║
║  • Add factory for creating adapters                               ║
║                                                                     ║
║  EXIT CRITERIA: BattleArenaAdapter works, BattleArena unchanged    ║
╚═════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
╔═════════════════════════════════════════════════════════════════════╗
║  STAGE 3: Observation Decoupling (Week 5-6)                         ║
╠═════════════════════════════════════════════════════════════════════╣
║  • Update ObservationProvider to use GameState                     ║
║  • Update all observation modules                                  ║
║  • Create BattleArenaObservationProvider                           ║
║  • Update observation builder                                      ║
║                                                                     ║
║  EXIT CRITERIA: Observations work with GameState, tests pass      ║
╚═════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
╔═════════════════════════════════════════════════════════════════════╗
║  STAGE 4: Reward Decoupling (Week 7-8)                            ║
╠═════════════════════════════════════════════════════════════════════╣
║  • Update RewardProvider to use GameState                          ║
║  • Update all reward modules                                       ║
║  • Create BattleArenaRewardProvider                               ║
║  • Update reward builder                                           ║
║                                                                     ║
║  EXIT CRITERIA: Rewards work with GameState, tests pass          ║
╚═════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
╔═════════════════════════════════════════════════════════════════════╗
║  STAGE 5: Plugin Interface (Week 9-10)                            ║
╠═════════════════════════════════════════════════════════════════════╣
║  • Update plugin interfaces to use Entity protocol                ║
║  • Create CharacterAdapter for plugins                             ║
║  • Maintain full backward compatibility                            ║
║                                                                     ║
║  EXIT CRITERIA: Plugins work with new entity interface            ║
╚═════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
╔═════════════════════════════════════════════════════════════════════╗
║  STAGE 6: Multi-Game Ready (Week 11-12)                           ║
╠═════════════════════════════════════════════════════════════════════╣
║  • Document new game adapter interface                            ║
║  • Create example adapter skeleton                                ║
║  • Update examples and tutorials                                  ║
║  • Performance testing                                            ║
║                                                                     ║
║  EXIT CRITERIA: Framework supports new games via adapters         ║
╚═════════════════════════════════════════════════════════════════════╝

TOTAL ESTIMATED EFFORT: 12 weeks
```

---

## Part 7: Risk Analysis

### 7.1 Breaking API Risk

| Change | Risk Level | Mitigation |
|--------|------------|------------|
| Adding interfaces | LOW | Pure addition, no changes |
| GameState abstraction | MEDIUM | Keep BattleArenaState, add adapter |
| Observation signature change | MEDIUM | Provide backward-compatible wrapper |
| Reward signature change | MEDIUM | Provide backward-compatible wrapper |

### 7.2 Performance Impact

| Component | Impact | Mitigation |
|-----------|--------|------------|
| Interface calls | ~1-2% | Acceptable |
| State conversion | ~2-3% | Cache conversions |
| Memory for adapters | +5-10% | Acceptable for flexibility |

### 7.3 Migration Complexity

| Task | Complexity | Notes |
|------|------------|-------|
| Interface design | LOW | Well-understood patterns |
| BattleArenaGameState | MEDIUM | Need to map all fields |
| Provider updates | HIGH | Many modules affected |
| Plugin updates | MEDIUM | 3 plugin types |

### 7.4 Testing Requirements

| Test Type | Count | Priority |
|-----------|-------|----------|
| Interface tests | 50 | HIGH |
| Adapter tests | 30 | HIGH |
| Provider tests | 100 | HIGH |
| Integration tests | 20 | MEDIUM |
| Performance tests | 10 | LOW |

---

## Part 8: Deliverables

### 8.1 Directory Structure

```
zbgym/
├── interfaces/                    # NEW: Generic interfaces
│   ├── __init__.py
│   ├── state.py                  # GameState, Entity, Player, Team
│   ├── action.py                # Action protocols
│   ├── vector.py                # Vector interface
│   ├── providers.py             # Provider interfaces
│   └── engine.py                # GameEngine interface
│
├── adapters/                      # NEW: Game adapters
│   ├── __init__.py
│   ├── base.py                  # GameAdapter base class
│   ├── factory.py               # AdapterFactory
│   └── battle_arena/
│       ├── __init__.py
│       ├── adapter.py           # BattleArenaAdapter
│       ├── state.py             # BattleArenaGameState
│       └── providers/
│           ├── __init__.py
│           ├── observation.py   # BattleArenaObservationProvider
│           └── reward.py        # BattleArenaRewardProvider
│
├── env/
│   └── battle_arena.py          # UNCHANGED - kept for compatibility
│
├── observation/                  # REFACTORED - use GameState
│   ├── base.py
│   ├── enemy.py
│   ├── health.py
│   ├── position.py
│   └── zone.py
│
├── reward/                       # REFACTORED - use GameState
│   ├── base.py
│   ├── combat.py
│   ├── survival.py
│   └── utility.py
│
├── plugins/                      # REFACTORED - use Entity
│   ├── character.py
│   ├── weapon.py
│   └── skill.py
│
└── ... (rest unchanged)
```

### 8.2 Key Files to Create

| File | Purpose |
|------|---------|
| `interfaces/state.py` | GameState, Entity, Player, Team interfaces |
| `interfaces/action.py` | Action protocol |
| `interfaces/vector.py` | Vector interface |
| `interfaces/providers.py` | ObservationProvider, RewardProvider |
| `interfaces/engine.py` | GameEngine interface |
| `adapters/base.py` | GameAdapter abstract class |
| `adapters/factory.py` | AdapterFactory |
| `adapters/battle_arena/state.py` | BattleArenaGameState |
| `adapters/battle_arena/adapter.py` | BattleArenaAdapter |

### 8.3 Estimated Implementation Effort

| Component | Lines of Code | Effort (days) |
|-----------|---------------|---------------|
| Interfaces | ~500 | 5 |
| Adapters | ~800 | 8 |
| State converters | ~400 | 4 |
| Provider updates | ~600 | 6 |
| Plugin updates | ~300 | 3 |
| Tests | ~1000 | 10 |
| Documentation | ~300 | 3 |
| **TOTAL** | ~3900 | 39 days |

---

## Part 9: Backward Compatibility Matrix

| Old API | New API | Compatible | Migration Path |
|---------|---------|------------|----------------|
| `BattleArena` | `BattleArenaAdapter` | YES | Keep both |
| `BattleArenaState` | `BattleArenaGameState` | YES | Add conversion |
| `Observation.compute(state, agent)` | `ObservationProvider.compute(state, agent)` | YES | Wrapper class |
| `Reward.compute(prev, curr, agent)` | `RewardProvider.compute(prev, curr, agent)` | YES | Wrapper class |
| `CharacterState` | `Player` | PARTIAL | Plugin adapter |
| `make('BattleArena-v1')` | `make('BattleArena-v1')` | YES | No change |

---

## Conclusion

This architecture plan provides a clear path from the current BattleArena-coupled design to a flexible multi-game framework. The key principles are:

1. **Add, don't replace** - Keep existing classes while adding new interfaces
2. **Adapters as bridges** - Use adapters to translate between generic and specific
3. **Gradual migration** - Each stage preserves backward compatibility
4. **Interfaces first** - Define interfaces before implementing adapters

The migration can be completed in 12 weeks with minimal risk to existing functionality.
