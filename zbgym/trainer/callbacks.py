"""Training callbacks for ZBGym."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

import numpy as np


class BaseCallback:
    """Base callback class for training."""

    def __init__(self) -> None:
        self.model = None
        self.num_timesteps = 0
        self.locals: dict = {}
        self.globals: dict = {}

    def __call__(
        self,
        locals: dict,
        globals: dict,
    ) -> bool:
        """Call the callback."""
        self.locals = locals
        self.globals = globals
        self.num_timesteps = globals.get("n_callbacks", 0)
        return self._on_step()

    def _on_step(self) -> bool:
        """Called at each step. Return False to stop training."""
        return True

    def on_training_start(self, locals: dict, globals: dict) -> None:
        """Called at the start of training."""
        pass

    def on_training_end(self, locals: dict, globals: dict) -> None:
        """Called at the end of training."""
        pass


class CallbackList:
    """Container for multiple callbacks."""

    def __init__(self, callbacks: list[BaseCallback] | None = None) -> None:
        self.callbacks = callbacks or []

    def append(self, callback: BaseCallback) -> None:
        """Add a callback."""
        self.callbacks.append(callback)

    def __call__(
        self,
        locals: dict,
        globals: dict,
    ) -> bool:
        """Call all callbacks."""
        for callback in self.callbacks:
            if not callback(locals, globals):
                return False
        return True


class CheckpointCallback(BaseCallback):
    """Callback to save model checkpoints."""

    def __init__(
        self,
        save_freq: int = 10000,
        save_path: str | Path = "./models",
        name_prefix: str = "model",
        save_replay: bool = False,
    ) -> None:
        super().__init__()
        self.save_freq = save_freq
        self.save_path = Path(save_path)
        self.name_prefix = name_prefix
        self.save_replay = save_replay

    def _on_step(self) -> bool:
        """Save checkpoint if needed."""
        if self.num_timesteps % self.save_freq == 0:
            self.save_path.mkdir(parents=True, exist_ok=True)

            path = self.save_path / f"{self.name_prefix}_{self.num_timesteps}"
            if self.model is not None:
                self.model.save(str(path))
                print(f"Saved model to {path}")

        return True


class EvaluationCallback(BaseCallback):
    """Callback to evaluate the model periodically."""

    def __init__(
        self,
        eval_env: Any,
        n_eval_episodes: int = 5,
        eval_freq: int = 1000,
        deterministic: bool = True,
        log_path: str | Path | None = None,
    ) -> None:
        super().__init__()
        self.eval_env = eval_env
        self.n_eval_episodes = n_eval_episodes
        self.eval_freq = eval_freq
        self.deterministic = deterministic
        self.log_path = Path(log_path) if log_path else None
        self.best_mean_reward = -float("inf")

    def _on_step(self) -> bool:
        """Evaluate if needed."""
        if self.num_timesteps % self.eval_freq == 0:
            rewards, lengths = self._evaluate()

            mean_reward = np.mean(rewards)
            mean_length = np.mean(lengths)

            if mean_reward > self.best_mean_reward:
                self.best_mean_reward = mean_reward
                if self.model is not None:
                    best_path = self.save_path / "best_model"
                    self.save_path.mkdir(parents=True, exist_ok=True)
                    self.model.save(str(best_path))
                    print(f"New best mean reward: {mean_reward:.2f}")

            if self.log_path:
                self._log_results(rewards, lengths)

        return True

    def _evaluate(self) -> tuple[list[float], list[int]]:
        """Run evaluation."""
        from stable_baselines3.common.evaluation import evaluate_policy

        rewards, lengths = evaluate_policy(
            self.model,
            self.eval_env,
            n_eval_episodes=self.n_eval_episodes,
            deterministic=self.deterministic,
            return_episode_rewards=True,
        )
        return rewards, lengths

    def _log_results(self, rewards: list[float], lengths: list[int]) -> None:
        """Log evaluation results."""
        results = {
            "timestep": self.num_timesteps,
            "mean_reward": float(np.mean(rewards)),
            "std_reward": float(np.std(rewards)),
            "mean_length": float(np.mean(lengths)),
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(results) + "\n")

    @property
    def save_path(self) -> Path:
        """Get save path for best model."""
        if self.log_path:
            return self.log_path.parent / "best_model"
        return Path("./models/best_model")


class TensorboardCallback(BaseCallback):
    """Callback to log metrics to TensorBoard."""

    def __init__(self, log_dir: str | Path = "./logs/tensorboard") -> None:
        super().__init__()
        self.log_dir = Path(log_dir)

    def _on_step(self) -> bool:
        """Log metrics."""
        try:
            from torch.utils.tensorboard import SummaryWriter
        except ImportError:
            return True

        if not hasattr(self, "_writer"):
            self._writer = SummaryWriter(str(self.log_dir))

        # Log episode reward if available
        if "infos" in self.locals:
            for info in self.locals.get("infos", []):
                if "episode" in info:
                    self._writer.add_scalar(
                        "rollout/ep_rew_mean",
                        info["episode"]["r"],
                        self.num_timesteps,
                    )
                    self._writer.add_scalar(
                        "rollout/ep_len_mean",
                        info["episode"]["l"],
                        self.num_timesteps,
                    )

        return True


class ProgressCallback(BaseCallback):
    """Callback to display training progress."""

    def __init__(self, total_timesteps: int, print_freq: int = 1000) -> None:
        super().__init__()
        self.total_timesteps = total_timesteps
        self.print_freq = print_freq
        self.last_print = 0

    def _on_step(self) -> bool:
        """Print progress."""
        if self.num_timesteps - self.last_print >= self.print_freq:
            progress = self.num_timesteps / self.total_timesteps * 100
            print(f"Progress: {progress:.1f}% ({self.num_timesteps}/{self.total_timesteps})")
            self.last_print = self.num_timesteps
        return True


class EarlyStoppingCallback(BaseCallback):
    """Callback to stop training if reward doesn't improve."""

    def __init__(
        self,
        patience: int = 10,
        min_delta: float = 0.1,
        target_reward: float | None = None,
    ) -> None:
        super().__init__()
        self.patience = patience
        self.min_delta = min_delta
        self.target_reward = target_reward
        self.best_reward = -float("inf")
        self.wait = 0

    def _on_step(self) -> bool:
        """Check for early stopping."""
        if "infos" in self.locals:
            for info in self.locals.get("infos", []):
                if "episode" in info:
                    reward = info["episode"]["r"]

                    if self.target_reward is not None:
                        if reward >= self.target_reward:
                            print(f"Target reward {self.target_reward} reached!")
                            return False

                    if reward > self.best_reward + self.min_delta:
                        self.best_reward = reward
                        self.wait = 0
                    else:
                        self.wait += 1
                        if self.wait >= self.patience:
                            print(f"No improvement for {self.patience} episodes. Stopping.")
                            return False

        return True
