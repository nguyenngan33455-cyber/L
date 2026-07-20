# Developer Guide

> **Alpha Version** - For ZBGym v0.1.0-alpha

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Running Tests](#running-tests)
4. [Code Quality](#code-quality)
5. [Project Structure](#project-structure)
6. [Creating Custom Plugins](#creating-custom-plugins)
7. [Environment Configuration](#environment-configuration)
8. [Training Agents](#training-agents)
9. [API Reference](#api-reference)
10. [Debugging](#debugging)

---

## Getting Started

### Prerequisites

| Requirement | Version | Notes |
|------------|---------|-------|
| Python | 3.8+ | Tested on 3.13 |
| Git | Any | For cloning |
| pip/uv | Latest | Package management |

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/nguyenngan33455-cyber/L.git
cd L

# Install in development mode
pip install -e ".[dev]"

# Or with uv
uv pip install -e ".[dev]"
```

### Verify Installation

```bash
# Check installation
python -c "import zbgym; print(zbgym.__version__)"

# Run quick test
python -c "
import zbgym
env = zbgym.make('BattleArena-v1')
obs, info = env.reset()
print(f'Observation shape: {obs.shape}')
print(f'Action space: {env.action_space}')
env.close()
"
```

---

## Development Setup

### Dependencies

```toml
# pyproject.toml
[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "ruff", "mypy"]
all = ["torch", "stable-baselines3", "fastapi", "uvicorn"]
```

### Virtual Environment (Recommended)

```bash
# Create venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# Install
pip install -e ".[dev,all]"
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=zbgym --cov-report=html --cov-report=term

# Specific test files
pytest tests/test_engine.py -v
pytest tests/test_renderer.py -v
pytest tests/test_vectorized.py -v
```

### Test Results (v0.1.0-alpha)

```
249 tests passed ✅
- test_engine.py: 17 tests
- test_vectorized.py: 10 tests  
- test_renderer.py: 12 tests
- test_replay.py: 8 tests
- test_trainer.py: 6 tests
```

---

## Code Quality

```bash
# Format all Python files
ruff format .

# Lint all files
ruff check .

# Auto-fix issues
ruff check --fix .
```

---

## Project Structure

```
zbgym/
├── __init__.py              # Package init, make(), version
├── version.py               # Version info
├── config.py                # Configuration dataclasses
├── constants.py             # Game constants
│
├── env/                     # RL Environments
│   ├── battle_arena.py     # Main BattleArena env
│   └── vectorized.py       # Vectorized wrapper
│
├── engine/                  # Game Engine
│   ├── event_bus.py        # Pub/sub event system
│   ├── tick_system.py      # Game loop (dt tracking)
│   ├── map.py              # Map management
│   └── spawn.py            # Spawn system
│
├── physics/                 # Physics Engine
│   ├── vector.py          # Vector2D class
│   ├── body.py             # PhysicsBody, DynamicBody
│   └── movement.py         # MovementSystem
│
├── plugins/                 # Entity Plugins
│   ├── character.py        # 55 characters
│   ├── weapon.py          # 17 weapons
│   └── skill.py           # 37 skills
│
├── trainer/                 # Training
│   ├── ppo.py             # PPOTrainer
│   └── callbacks.py       # CheckpointCallback
│
├── replay/                 # Replay System
│   └── deterministic.py   # ReplayRecorder, ReplayPlayer
│
├── data/                   # Game Data
│   ├── characters.json     # 55 characters
│   ├── weapons.json       # 17 weapons
│   └── skills.json        # 37 skills
│
├── rendering/              # Debug Rendering
│   └── debug_renderer.py   # DebugRenderer
│
├── cli/                    # CLI Tools
│   └── main.py            # Main CLI
│
├── examples/              # Examples
│   └── quickstart.py      # Quick start
│
└── tests/                 # Test Suite (249 tests)
```

---

## Creating Custom Plugins

### Custom Character

```python
from zbgym.plugins.character import (
    Character,
    CharacterStats,
    Ability,
    register_character,
)

@register_character(
    character_id="my_hero",
    name="My Hero",
    stats=CharacterStats(
        max_health=200,
        max_shield=50,
        max_energy=100,
        move_speed=350,
        base_damage=15.0,
    ),
    abilities=[
        Ability(id="Q", name="Skill Shot", ...),
        Ability(id="E", name="Dash", ...),
    ],
    description="A balanced hero with good damage"
)
class MyHeroCharacter(Character):
    """Custom hero character."""
    pass
```

### Custom Weapon

```python
from zbgym.plugins.weapon import (
    Weapon,
    WeaponStats,
    WeaponType,
    register_weapon,
)

@register_weapon(
    weapon_id="plasma_rifle",
    name="Plasma Rifle",
    weapon_type=WeaponType.ENERGY,
    stats=WeaponStats(
        damage=35.0,
        fire_rate=5.0,
        magazine_size=25,
        reload_time=2.5,
        projectile_speed=1200.0,
        range_val=500.0,
    )
)
class PlasmaRifle(Weapon):
    """Custom energy weapon."""
    pass
```

---

## Environment Configuration

### Basic Usage

```python
import zbgym

# Create with defaults
env = zbgym.make("BattleArena-v1")
obs, info = env.reset(seed=42)

# Step through episode
for step in range(1000):
    action = env.action_space.sample()  # Replace with your policy
    obs, reward, terminated, truncated, info = env.step(action)
    
    if terminated or truncated:
        obs, info = env.reset()

env.close()
```

### Custom Configuration

```python
from zbgym.config import EnvironmentConfig
from zbgym.env.battle_arena import BattleArena

config = EnvironmentConfig(
    arena_width=2000,
    arena_height=1500,
    num_agents=4,
    match_duration=600.0,
    tick_rate=60,
)

env = BattleArena(
    config=config,
    render_mode="human",
    obs_config={
        "include_health": True,
        "include_position": True,
        "include_enemies": True,
        "max_enemies": 8,
    },
    reward_config={
        "kill_reward": 10.0,
        "death_penalty": -5.0,
        "survival_reward": 0.01,
    },
)
```

---

## Training Agents

### Basic PPO Training

```python
from zbgym.trainer import PPOTrainer, TrainerConfig

config = TrainerConfig(
    env_id="BattleArena-v1",
    total_timesteps=100_000,
    num_envs=4,
    learning_rate=3e-4,
)

trainer = PPOTrainer(
    config=config,
    model_save_dir="./models",
    log_dir="./logs",
)

trainer.setup()
model = trainer.train()
model.save("./models/ppo_final")
```

---

## API Reference

### Environment Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `make` | `(env_id, **kwargs)` | Create environment |
| `reset` | `(seed=None)` | Reset environment |
| `step` | `(action)` | Execute action |
| `render` | `(mode=None)` | Render frame |
| `close` | `()` | Clean up |

### Spaces

```python
# Action Space
env.action_space  # Box(-1, 1, shape=(4,))
# [move_x, move_y, aim_x, aim_y]

# Observation Space  
env.observation_space  # Box(-inf, inf, shape=(50,))
```

---

## Debugging

### Debug Rendering

```python
from zbgym.rendering import DebugRenderer

env = zbgym.make("BattleArena-v1")
renderer = DebugRenderer.from_env(env)

for step in range(1000):
    action = policy(obs)
    obs, reward, terminated, truncated, info = env.step(action)
    
    # Render debug view
    renderer.clear()
    renderer.render_from_env(env)
    img = renderer.to_image()
    
    if terminated or truncated:
        break
```

### Check Determinism

```python
env1 = zbgym.make("BattleArena-v1")
env2 = zbgym.make("BattleArena-v1")

obs1, _ = env1.reset(seed=42)
obs2, _ = env2.reset(seed=42)

assert (obs1 == obs2).all(), "Not deterministic!"
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Pull Request Checklist

- [ ] Tests pass (`pytest`)
- [ ] Code formatted (`ruff format`)
- [ ] No linting errors (`ruff check`)
- [ ] Type hints added
- [ ] Docstrings added
