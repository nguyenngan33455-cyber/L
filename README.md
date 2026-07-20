# 🎮 ZBGym - Battle Arena RL Framework

> **⚠️ ALPHA VERSION NOTICE**
> This is an **early alpha release** (v0.1.0-alpha). The codebase is actively being developed and may contain bugs, incomplete features, or breaking changes. We welcome feedback and contributions! Please report issues on GitHub.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-249%20passed-brightgreen.svg)]()

## Overview

**ZBGym** is a professional Reinforcement Learning framework designed for battle arena simulations. It provides a Gymnasium-compatible environment where AI agents learn combat skills through interaction in a physics-based arena.

### Key Features

| Feature | Description |
|---------|-------------|
| 🎯 **Gymnasium Compatible** | Drop-in replacement for standard RL workflows |
| 🔬 **Deterministic** | Fully reproducible results with seeded environments |
| ⚡ **Vectorized Training** | Parallel environment execution for faster training |
| 🎨 **Extensible Plugins** | Custom characters, weapons, skills, rewards |
| 📊 **Built-in Dashboard** | Real-time training visualization |
| 🎬 **Replay System** | Record and analyze episodes |
| 🧪 **249 Tests** | Comprehensive test coverage |

## Quick Start

### Installation

```bash
# From PyPI (when available)
pip install zbgym

# Development installation
git clone https://github.com/nguyenngan33455-cyber/L.git
cd L
pip install -e ".[all]"
```

### Your First Agent

```python
import numpy as np
import zbgym

# Create environment
env = zbgym.make("BattleArena-v1")

# Reset environment
obs, info = env.reset(seed=42)
print(f"Observation shape: {obs.shape}")
print(f"Action space: {env.action_space}")

# Run one episode
total_reward = 0
for step in range(1000):
    # Replace with your policy
    action = env.action_space.sample()
    
    obs, reward, terminated, truncated, info = env.step(action)
    total_reward += reward
    
    if terminated or truncated:
        print(f"Episode ended at step {step} with reward {total_reward:.2f}")
        obs, info = env.reset(seed=42)
        total_reward = 0

env.close()
```

### Training with PPO

```python
from zbgym.trainer import PPOTrainer, TrainerConfig

config = TrainerConfig(
    env_id="BattleArena-v1",
    total_timesteps=100_000,
    num_envs=4,
    learning_rate=3e-4,
)

trainer = PPOTrainer(config=config)
trainer.setup()
model = trainer.train()
model.save("./models/ppo_battle_arena")
```

## Environment Details

### BattleArena-v1

**Action Space:** `Box(-1, 1, shape=(4,))` - Continuous actions for movement and aiming
- `[move_x, move_y, aim_x, aim_y]`

**Observation Space:** `Box(-inf, inf, shape=(50,))` - 50-dimensional state vector including:
- Health, position, velocity, energy, shield
- Enemy positions and health
- Safe zone information

**Reward Shaping:**
| Event | Reward |
|-------|--------|
| Survival (per step) | +0.01 |
| Movement | +0.02 × magnitude |
| Damage dealt | +0.1 × damage |
| Kill | +10.0 |
| Death | -5.0 |
| Idle | -0.01 |
| Zone danger | -0.02 |

**Episode Termination:**
- ✅ All enemies eliminated (1 agent remains)
- ✅ Time limit reached (600 seconds)
- ✅ All agents eliminated
- ⏱️ Max steps reached (1000) → truncated

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ZBGym Architecture                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │   CLI   │    │   API   │    │ Trainer │    │  Env    │ │
│  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘ │
│       │              │              │              │       │
│       └──────────────┴──────────────┴──────────────┘       │
│                              │                              │
│  ┌───────────────────────────▼───────────────────────────┐ │
│  │                    BattleArena Env                      │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │ │
│  │  │ Engine   │  │ Physics  │  │ Plugins  │  │ Reward │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Available Plugins

### Characters (17 available)
- Pre-loaded from game dump data
- Custom characters via `@register_character` decorator

### Weapons (17 available)
| Weapon | Type | Damage | Fire Rate |
|--------|------|--------|-----------|
| pistol | Pistol | 18 | 5.0/s |
| rifle | Rifle | 30 | 8.0/s |
| shotgun | Shotgun | 15×8 | 1.0/s |
| sniper | Sniper | 120 | 0.5/s |
| smg | Rifle | 18 | 12.0/s |
| grenade | Bomb | 120 | 0.5/s |
| + 11 more... | | | |

## CLI Reference

```bash
# Initialize new project
zbgym init my_agent

# Train agent
zbgym train --env BattleArena-v1 --timesteps 100000 --algorithm PPO

# Evaluate trained model
zbgym evaluate --model models/ppo_battle_arena.zip --episodes 10

# Start dashboard
zbgym dashboard --port 8000

# List available plugins
zbgym plugins

# System check
zbgym doctor
```

## Docker Deployment

```bash
# Build image
docker build -t zbgym .

# Run with docker-compose
docker-compose up -d

# Train in container
docker-compose run zbgym python -m zbgym.cli.main train --timesteps 100000

# Access dashboard
open http://localhost:8000
```

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/Architecture.md) | System design and components |
| [Developer Guide](docs/DeveloperGuide.md) | Setup, testing, development |
| [Plugin Guide](docs/PluginGuide.md) | Creating custom plugins |

## Known Limitations (Alpha)

- ⚠️ Dashboard requires `fastapi` dependency (not bundled)
- ⚠️ Some weapon stats are estimated (from enum parsing)
- ⚠️ Training hyperparameters not yet optimized
- ⚠️ GPU acceleration not yet implemented
- ⚠️ Documentation in progress

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Format code
ruff format .

# Lint
ruff check .
```

## Changelog

### v0.1.0-alpha (Current)
- ✅ Gymnasium-compatible BattleArena environment
- ✅ Combat system with auto-attack
- ✅ Zone damage system
- ✅ Deterministic replay recording
- ✅ Vectorized environments (32-1024 parallel)
- ✅ 17 weapons, 55 characters from game dump
- ✅ CLI tools and dashboard
- ✅ 249 passing tests

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/nguyenngan33455-cyber/L/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/nguyenngan33455-cyber/L/discussions)
- 📧 **Email:** ngan.dev@example.com

---

*ZBGym - Train your agents. Dominate the arena. 🎮*
