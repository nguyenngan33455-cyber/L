# ZBGym

A professional, production-quality Reinforcement Learning framework for battle arena simulation.

## Overview

ZBGym is an independent battle arena simulator designed for RL research. It provides a modular, extensible environment where agents can learn combat skills through interaction.

## Features

- **Modular Architecture**: Engine, physics, characters, weapons, and skills are all plugins
- **Gymnasium Compatible**: Drop-in replacement for your existing RL workflows
- **Deterministic**: Fully deterministic simulation for reproducible results
- **Scalable**: Support for vectorized environments and distributed training
- **Extensible**: Easy to add custom characters, weapons, maps, and reward functions
- **Production Ready**: Built-in replay system, dashboard, and model management

## Installation

```bash
pip install zbgym
```

For development:

```bash
git clone https://github.com/zbgym/zbgym.git
cd zbgym
pip install -e ".[all]"
```

## Docker

```bash
# Build image
docker build -t zbgym .

# Run with docker-compose
docker-compose up -d

# Run training
docker-compose run zbgym python -m zbgym.cli.main train --timesteps 100000

# Run dashboard
docker-compose up dashboard
```

## CLI Usage

```bash
# Initialize a project
zbgym init my_project

# Train an agent
zbgym train --timesteps 100000 --algorithm PPO

# Evaluate a model
zbgym evaluate models/model_100k.zip --episodes 10

# Start dashboard
zbgym dashboard

# List plugins
zbgym plugins

# Check system
zbgym doctor
```

## Quick Start

```python
import zbgym

# Create environment
env = zbgym.make("BattleArena-v1")

# Reset and interact
obs, info = env.reset()
done = False

while not done:
    action = env.action_space.sample()  # Replace with your policy
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated

env.close()
```

## Documentation

Full documentation is available at [https://zbgym.readthedocs.io](https://zbgym.readthedocs.io)

## License

MIT License - see [LICENSE](LICENSE) for details.
