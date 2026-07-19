# Developer Guide

## Getting Started

### Prerequisites

- Python 3.8+
- pip or uv package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/zbgym.git
cd zbgym

# Install in development mode
pip install -e ".[dev]"

# Or with uv
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=zbgym --cov-report=html

# Run specific test file
pytest tests/test_engine.py -v
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy zbgym/
```

## Project Structure

```
zbgym/
├── __init__.py           # Package init, version, make()
├── config.py             # Configuration classes
├── constants.py          # Game constants
├── env/                  # RL environments
│   ├── __init__.py
│   └── battle_arena.py   # Main environment
├── engine/               # Game engine
│   ├── event_bus.py      # Event system
│   ├── tick_system.py    # Game loop
│   ├── engine.py         # Core engine
│   ├── map.py            # Map management
│   └── spawn.py          # Spawn system
├── physics/              # Physics engine
│   ├── vector.py         # Vector math
│   ├── body.py           # Physics bodies
│   ├── movement.py       # Movement
│   └── projectile.py     # Projectiles
├── collision/            # Collision detection
├── plugins/              # Entity plugins
│   ├── character.py      # Characters
│   ├── weapon.py         # Weapons
│   └── skill.py          # Skills
├── observation/          # State observations
│   ├── base.py           # Base classes
│   ├── builder.py        # Observation builder
│   └── *.py              # Observation types
├── reward/              # Reward computation
│   ├── base.py           # Base classes
│   ├── builder.py        # Reward builder
│   └── *.py              # Reward types
├── trainer/              # Training
│   ├── base.py           # Base trainer
│   ├── ppo.py            # PPO implementation
│   └── callbacks.py       # Training callbacks
├── replay/               # Episode replay
│   ├── base.py           # Replay classes
│   └── recorder.py       # Recording
├── api/                  # Dashboard API
│   └── server.py         # FastAPI server
├── cli/                  # CLI tools
│   ├── main.py           # Main CLI
│   └── commands.py       # Commands
├── rendering/             # Rendering (future)
├── utils/                # Utilities
├── docs/                 # Documentation
├── examples/             # Example scripts
└── tests/                # Unit tests
```

## Creating Custom Plugins

### Custom Character

```python
from zbgym.plugins.character import (
    Character,
    CharacterStats,
    register_character,
)

@register_character(
    "my_character",
    "My Character",
    CharacterStats(
        max_health=200,
        max_shield=50,
        move_speed=350,
    )
)
class MyCharacter(Character):
    def special_ability(self):
        # Custom ability implementation
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
    "plasma_gun",
    "Plasma Gun",
    WeaponType.ENERGY,
    WeaponStats(
        damage=25.0,
        fire_rate=3.0,
        magazine_size=20,
        reload_time=2.5,
    )
)
class PlasmaGun(Weapon):
    pass
```

### Custom Skill

```python
from zbgym.plugins.skill import (
    Skill,
    SkillType,
    SkillConfig,
    register_skill,
)

@register_skill(
    "teleport",
    "Teleport",
    SkillType.MOVEMENT,
    SkillConfig(
        cooldown=15.0,
        energy_cost=30.0,
        range=100.0,
    )
)
class TeleportSkill(Skill):
    pass
```

### Custom Observation

```python
from zbgym.observation import (
    Observation,
    ObservationConfig,
    observation_registry,
)

class CustomObservation(Observation):
    def __init__(self, config=None):
        self.config = config or ObservationConfig()
    
    def get_dimension(self) -> int:
        return 5  # Your observation dimension
    
    def compute(self, state):
        # Compute observation from state
        return np.array([...])

observation_registry.register("custom", CustomObservation)
```

### Custom Reward

```python
from zbgym.reward import (
    Reward,
    RewardConfig,
    reward_registry,
)

class CustomReward(Reward):
    def __init__(self, config=None):
        self.config = config or RewardConfig()
    
    def compute(self, state, prev_state=None):
        # Compute reward
        return 1.0

reward_registry.register("custom", CustomReward)
```

## Environment Configuration

```python
import zbgym

# Create environment
env = zbgym.make(
    "BattleArena-v1",
    num_agents=4,
    map_size="large",
    config={
        "tick_rate": 60,
        "max_steps": 10000,
    }
)

# Run episode
obs, info = env.reset()
for step in range(1000):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        break
env.close()
```

## Training

```python
from zbgym.trainer import PPOTrainer, TrainerConfig, CheckpointCallback

config = TrainerConfig(
    env_id="BattleArena-v1",
    total_timesteps=1_000_000,
    num_envs=4,
)

trainer = PPOTrainer(
    config=config,
    model_save_dir="./models",
    log_dir="./logs",
)

trainer.setup()
model = trainer.train()
```

## API Reference

### Environment

- `zbgym.make(env_id, **kwargs)` - Create environment
- `BattleArena.reset(seed)` - Reset environment
- `BattleArena.step(action)` - Take action
- `BattleArena.render()` - Render frame
- `BattleArena.close()` - Close environment

### Engine

- `GameEngine` - Main game engine
- `EventBus` - Event system
- `TickSystem` - Game loop
- `MapManager` - Map loading

### Physics

- `Vector2D` / `Vector3D` - Vector operations
- `DynamicBody` - Moving physics body
- `Projectile` - Bullet physics

### Plugins

- `character_registry` - Character plugin registry
- `weapon_registry` - Weapon plugin registry
- `skill_registry` - Skill plugin registry
- `create_character()` - Create character instance
- `create_weapon()` - Create weapon instance
- `create_skill()` - Create skill instance
