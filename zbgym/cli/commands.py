"""CLI commands for ZBGym."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def init(args: list[str]) -> int:
    """Initialize a new ZBGym project."""
    parser = argparse.ArgumentParser(description="Initialize a new ZBGym project")
    parser.add_argument("path", nargs="?", default=".", help="Project directory")
    parser.add_argument("--template", default="basic", help="Project template")
    parsed = parser.parse_args(args)

    path = Path(parsed.path)
    path.mkdir(parents=True, exist_ok=True)

    # Create basic structure
    (path / "config").mkdir(exist_ok=True)
    (path / "models").mkdir(exist_ok=True)
    (path / "logs").mkdir(exist_ok=True)
    (path / "replays").mkdir(exist_ok=True)

    # Create config file
    config = {
        "env_id": "BattleArena-v1",
        "algorithm": "PPO",
        "total_timesteps": 1000000,
        "learning_rate": 3e-4,
        "num_envs": 4,
    }
    with open(path / "config" / "train.yaml", "w") as f:
        json.dump(config, f, indent=2)

    print(f"Initialized ZBGym project at {path}")
    return 0


def train(args: list[str]) -> int:
    """Train an RL agent."""
    parser = argparse.ArgumentParser(description="Train an RL agent")
    parser.add_argument("--env", default="BattleArena-v1", help="Environment ID")
    parser.add_argument("--algorithm", default="PPO", help="RL algorithm")
    parser.add_argument("--timesteps", type=int, default=100000, help="Total timesteps")
    parser.add_argument("--save-dir", default="./models", help="Save directory")
    parser.add_argument("--log-dir", default="./logs", help="Log directory")
    parser.add_argument("--seed", type=int, help="Random seed")
    parsed = parser.parse_args(args)

    print(f"Training {parsed.algorithm} on {parsed.env}")
    print(f"Total timesteps: {parsed.timesteps}")
    print(f"Save directory: {parsed.save_dir}")

    # Check if stable-baselines3 is available
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.env_util import make_vec_env
    except ImportError:
        print("Error: stable-baselines3 not installed. Run: pip install stable-baselines3")
        return 1

    # Create environment
    env = make_vec_env(parsed.env, n_envs=4, seed=parsed.seed)

    # Create model
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
    )

    # Train
    try:
        model.learn(total_timesteps=parsed.timesteps, progress_bar=True)
    except KeyboardInterrupt:
        print("\nTraining interrupted by user")

    # Save model
    import time

    save_path = Path(parsed.save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    model.save(save_path / f"model_{int(time.time())}")
    print(f"Model saved to {save_path}")

    return 0


def evaluate(args: list[str]) -> int:
    """Evaluate a trained model."""
    parser = argparse.ArgumentParser(description="Evaluate a trained model")
    parser.add_argument("model", help="Path to model file")
    parser.add_argument("--env", default="BattleArena-v1", help="Environment ID")
    parser.add_argument("--episodes", type=int, default=10, help="Number of episodes")
    parser.add_argument("--deterministic", action="store_true", help="Use deterministic policy")
    parsed = parser.parse_args(args)

    if not Path(parsed.model).exists():
        print(f"Error: Model file not found: {parsed.model}")
        return 1

    print(f"Evaluating model: {parsed.model}")
    print(f"Episodes: {parsed.episodes}")

    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.evaluation import evaluate_policy
    except ImportError:
        print("Error: stable-baselines3 not installed.")
        return 1

    # Load model
    model = PPO.load(parsed.model)

    # Create environment
    import gymnasium as gym

    env = gym.make(parsed.env)

    # Evaluate
    rewards, lengths = evaluate_policy(
        model,
        env,
        n_eval_episodes=parsed.episodes,
        deterministic=parsed.deterministic,
        return_episode_rewards=True,
    )

    import numpy as np

    print("\nResults:")
    print(f"  Mean reward: {np.mean(rewards):.2f} ± {np.std(rewards):.2f}")
    print(f"  Mean length: {np.mean(lengths):.2f} ± {np.std(lengths):.2f}")

    return 0


def replay(args: list[str]) -> int:
    """Play back a recorded episode."""
    parser = argparse.ArgumentParser(description="Play back a recorded episode")
    parser.add_argument("replay", help="Path to replay file")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed")
    parsed = parser.parse_args(args)

    if not Path(parsed.replay).exists():
        print(f"Error: Replay file not found: {parsed.replay}")
        return 1

    print(f"Playing replay: {parsed.replay}")
    print(f"Speed: {parsed.speed}x")

    try:
        from zbgym.replay import ReplayRecorder

        recorder = ReplayRecorder()
        replay = recorder.load(parsed.replay)

        print(f"Replay length: {len(replay)} steps")
        print(f"Total reward: {replay.total_reward:.2f}")

        # Note: Full playback requires a renderer
        print("(Playback visualization not yet implemented)")

    except Exception as e:
        print(f"Error loading replay: {e}")
        return 1

    return 0


def dashboard(args: list[str]) -> int:
    """Start the web dashboard."""
    parser = argparse.ArgumentParser(description="Start the web dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parsed = parser.parse_args(args)

    print(f"Starting ZBGym Dashboard on {parsed.host}:{parsed.port}")
    print("Press Ctrl+C to stop")

    try:
        import uvicorn

        from zbgym.api import api

        uvicorn.run(
            api.get_app(),
            host=parsed.host,
            port=parsed.port,
            reload=parsed.reload,
        )
    except ImportError:
        print("Error: uvicorn not installed. Run: pip install uvicorn")
        return 1
    except KeyboardInterrupt:
        print("\nDashboard stopped")
        return 0

    return 0


def plugins(args: list[str]) -> int:
    """List available plugins."""
    parser = argparse.ArgumentParser(description="List available plugins")
    parser.add_argument("--type", choices=["character", "weapon", "skill", "all"], default="all")
    parsed = parser.parse_args(args)

    print("Available Plugins")
    print("=" * 50)

    if parsed.type in ("character", "all"):
        print("\nCharacters:")
        try:
            from zbgym.plugins.character import character_registry

            for pid in character_registry.list_plugins():
                print(f"  - {pid}")
        except Exception:
            print("  (Could not load character plugins)")

    if parsed.type in ("weapon", "all"):
        print("\nWeapons:")
        try:
            from zbgym.plugins.weapon import weapon_registry

            for pid in weapon_registry.list_plugins():
                print(f"  - {pid}")
        except Exception:
            print("  (Could not load weapon plugins)")

    if parsed.type in ("skill", "all"):
        print("\nSkills:")
        try:
            from zbgym.plugins.skill import skill_registry

            for pid in skill_registry.list_plugins():
                print(f"  - {pid}")
        except Exception:
            print("  (Could not load skill plugins)")

    return 0


def export(args: list[str]) -> int:
    """Export a model."""
    parser = argparse.ArgumentParser(description="Export a model")
    parser.add_argument("model", help="Path to model file")
    parser.add_argument("--format", default="onnx", choices=["onnx", "torchscript"])
    parser.add_argument("--output", help="Output path")
    parsed = parser.parse_args(args)

    if not Path(parsed.model).exists():
        print(f"Error: Model file not found: {parsed.model}")
        return 1

    print(f"Exporting model: {parsed.model}")
    print(f"Format: {parsed.format}")

    # Placeholder for export functionality
    print("(Model export not yet fully implemented)")
    return 0


def doctor(args: list[str]) -> int:
    """Check system requirements."""
    import importlib

    print("ZBGym System Check")
    print("=" * 50)

    # Check Python version
    print(f"\nPython: {sys.version}")
    if sys.version_info < (3, 8):
        print("  ⚠️  Python 3.8+ recommended")
    else:
        print("  ✓ Python version OK")

    # Check dependencies
    deps = [
        "numpy",
        "gymnasium",
        "stable_baselines3",
        "torch",
    ]

    print("\nDependencies:")
    for dep in deps:
        try:
            mod = importlib.import_module(dep.replace("-", "_"))
            version = getattr(mod, "__version__", "unknown")
            print(f"  ✓ {dep}: {version}")
        except ImportError:
            print(f"  ✗ {dep}: NOT INSTALLED")

    # Check optional dependencies
    print("\nOptional Dependencies:")
    optional = ["fastapi", "uvicorn", "tensorboard"]
    for dep in optional:
        try:
            importlib.import_module(dep.replace("-", "_"))
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ○ {dep}: NOT INSTALLED (optional)")

    return 0
