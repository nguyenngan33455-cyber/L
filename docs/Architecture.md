# ZBGym Architecture

> **Alpha Version Documentation** - Last updated for v0.1.0-alpha

## Overview

ZBGym is a professional Reinforcement Learning framework designed for battle arena simulations. It provides a Gymnasium-compatible environment with advanced physics, combat systems, and training capabilities.

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                           ZBGym System                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐   │
│   │     CLI     │    │  Dashboard  │    │      Trainer        │   │
│   │  (Commands) │    │   (API)     │    │  (Stable-Baselines3)│   │
│   └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘   │
│          │                   │                        │              │
│          └───────────────────┴────────────────────────┘              │
│                                 │                                     │
│                          ┌──────▼──────┐                             │
│                          │ BattleArena │                             │
│                          │   (Env)     │                             │
│                          └──────┬──────┘                             │
│                                 │                                     │
│   ┌─────────────────────────────┼─────────────────────────────┐     │
│   │                             │                             │     │
│   │  ┌───────────┐  ┌──────────┴───┐  ┌────────────────┐   │     │
│   │  │  Engine   │  │   Physics    │  │    Plugins     │   │     │
│   │  │-EventBus  │  │ -Vector2D    │  │ -Characters(17)│   │     │
│   │  │-TickSystem│  │ -Bodies      │  │ -Weapons(17)   │   │     │
│   │  │-Spawn     │  │ -Movement     │  │ -Skills(37)    │   │     │
│   │  │-Map       │  │ -Collision    │  │                │   │     │
│   │  └───────────┘  └──────────────┘  └────────────────┘   │     │
│   │                             │                             │     │
│   │              ┌──────────────┴──────────────┐              │     │
│   │              │        Reward System        │              │     │
│   │              │  -Survival  -Combat         │              │     │
│   │              │  -Movement  -Zone           │              │     │
│   │              └─────────────────────────────┘              │     │
│   └───────────────────────────────────────────────────────────┘     │
│                                                                       │
└────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Environment (`zbgym.env`)

The main RL environment following the Gymnasium API.

| Class | Description |
|-------|-------------|
| `BattleArena` | Primary battle arena environment |
| `VectorizedBattleArena` | Parallel environment for vectorized training |
| `SyncVectorizedEnv` | Synchronous vectorized wrapper |

**Key Features:**
- Fixed timestep (1/60s) for deterministic simulation
- Combat system with auto-attack when in range
- Zone damage for outside-safe-zone penalties
- Episode termination on combat/winner/timeout

### 2. Engine (`zbgym.engine`)

Core game engine components.

| Component | File | Description |
|-----------|------|-------------|
| EventBus | `event_bus.py` | Pub/sub event system |
| TickSystem | `tick_system.py` | Game loop with dt tracking |
| MapManager | `map.py` | Map loading/management |
| SpawnSystem | `spawn.py` | Character spawn/respawn |

### 3. Physics (`zbgym.physics`)

Physics simulation components.

| Component | Description |
|-----------|-------------|
| `Vector2D` | 2D vector math (add, subtract, normalize, distance) |
| `PhysicsBody` | Base physics object with position/radius |
| `DynamicBody` | Moving physics body with velocity |
| `MovementSystem` | Character movement calculations |
| `CollisionSystem` | Circle-circle collision detection |

### 4. Plugins (`zbgym.plugins`)

Extensible entity system using registry pattern.

```
character_registry ─┬─ 55 characters from game dump
                    │
weapon_registry ────┼─ 17 weapons (rifle, pistol, shotgun, etc.)
                    │
skill_registry ─────┘─ 37 skills parsed from dump
```

**Plugin Registration:**
```python
@register_character("hero_id", "Hero Name", CharacterStats(...))
class HeroCharacter(Character):
    pass
```

### 5. Training (`zbgym.trainer`)

RL training infrastructure.

| Component | Description |
|-----------|-------------|
| `PPOTrainer` | PPO training via Stable-Baselines3 |
| `TrainerConfig` | Training hyperparameters |
| `CheckpointCallback` | Model checkpointing |
| `ProgressCallback` | Training progress logging |

### 6. Replay (`zbgym.replay`)

Episode recording and playback.

| Class | Description |
|-------|-------------|
| `ReplayRecorder` | Records episodes to file |
| `ReplayPlayer` | Playback recorded episodes |
| `DeterministicReplay` | Replay with determinism verification |
| `DeterministicRecorder` | Alias for ReplayRecorder |

**File Format:** Custom binary format (.zbr) with zlib compression

### 7. Data System (`zbgym.data`)

Game data loaded from dump parsing.

| File | Content |
|------|---------|
| `characters.json` | 55 character configs |
| `weapons.json` | 17 weapon configs |
| `skills.json` | 37 skill configs |

### 8. Rendering (`zbgym.rendering`)

Debug visualization system.

| Class | Description |
|-------|-------------|
| `DebugRenderer` | Main debug renderer |
| `DebugColor` | RGBA color definitions |
| `DebugShape` | Shape primitives |
| `DebugLayer` | Layer visibility control |

## Environment API

### Standard Gymnasium Interface

```python
import zbgym

# Create
env = zbgym.make("BattleArena-v1")

# Reset
obs, info = env.reset(seed=42)

# Step
for step in range(1000):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()

# Close
env.close()
```

### Action Space

`Box(-1, 1, shape=(4,))` - Continuous actions
- `[move_x, move_y, aim_x, aim_y]`
- Values normalized to [-1, 1]

### Observation Space

`Box(-inf, inf, shape=(50,))` - 50-dimensional vector
- Self: health, position (2), velocity (2), energy, shield
- Zone: distance to safe zone center
- Enemies: position (2), health per enemy (up to 8 enemies)

### Reward Signals

| Signal | Value | Trigger |
|--------|-------|---------|
| `survival_reward` | +0.01 | Per step alive |
| `movement_reward` | +0.02×mag | Moving |
| `damage_reward` | +0.1×damage | Combat |
| `kill_reward` | +10.0 | Enemy killed |
| `death_penalty` | -5.0 | Agent died |
| `idle_penalty` | -0.01 | No movement |
| `zone_danger` | -0.02 | Outside safe zone |

## Data Flow

```
Agent Policy
     │
     ▼ action
┌────────────┐
│  Env.step  │
└─────┬──────┘
      │
      ▼
┌────────────────────────────────────────┐
│         Engine Update (dt=1/60)          │
│  ┌──────────────────────────────────┐  │
│  │ 1. Process action                 │  │
│  │ 2. Update positions              │  │
│  │ 3. Combat (auto-attack)          │  │
│  │ 4. Zone damage                   │  │
│  │ 5. Check termination            │  │
│  └──────────────────────────────────┘  │
└─────────────┬──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│           Compute Reward               │
│  - Damage delta detection              │
│  - Kill/death tracking                │
│  - Health-based signals               │
└─────────────┬──────────────────────────┘
              │
              ▼
       obs, reward, terminated, truncated, info
```

## Configuration

### Environment Config

```python
from zbgym.config import EnvironmentConfig

config = EnvironmentConfig(
    arena_width=2000,
    arena_height=1500,
    num_agents=2,
    match_duration=600.0,  # seconds
    tick_rate=60,
)
```

### Trainer Config

```python
from zbgym.trainer import TrainerConfig

config = TrainerConfig(
    env_id="BattleArena-v1",
    total_timesteps=1_000_000,
    num_envs=4,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
)
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | ≥1.20 | Numerical computing |
| gymnasium | ≥0.28 | RL environment interface |
| stable-baselines3 | ≥2.0 | RL algorithms |
| torch | ≥2.0 | Neural networks |
| fastapi | ≥0.100 | Dashboard API (optional) |
| pytest | ≥7.0 | Testing |
| ruff | ≥0.1 | Linting/formatting |
