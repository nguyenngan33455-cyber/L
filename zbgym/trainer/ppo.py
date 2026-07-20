"""PPO trainer for ZBGym."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from zbgym.dashboard.callback import DashboardCallback
from zbgym.dashboard.manager import DashboardManager, DashboardManagerConfig
from zbgym.trainer.base import BaseTrainer, TrainerConfig, TrainingStats


class PPOTrainer(BaseTrainer):
    """
    PPO trainer using Stable-Baselines3.

    Proximal Policy Optimization (PPO) is an on-policy algorithm
    suitable for discrete and continuous action spaces.

    Supports optional Dashboard integration for tracking training metrics.
    """

    def __init__(
        self,
        config: TrainerConfig | None = None,
        model_save_dir: str | Path = "./models",
        log_dir: str | Path = "./logs",
        dashboard: DashboardManagerConfig | DashboardManager | bool | None = None,
        dashboard_url: str | None = None,
        dashboard_api_key: str | None = None,
        dashboard_publish_interval: int = 100,
    ) -> None:
        """
        Initialize PPO trainer.

        Args:
            config: Training configuration
            model_save_dir: Directory to save models
            log_dir: Directory for logs
            dashboard: Dashboard configuration (DashboardManagerConfig,
                     DashboardManager instance, bool, or None)
            dashboard_url: Dashboard server URL (if dashboard=True)
            dashboard_api_key: Dashboard API key (if dashboard=True)
            dashboard_publish_interval: Publish metrics every N timesteps
        """
        super().__init__(
            config=config,
            model_save_dir=model_save_dir,
            log_dir=log_dir,
            dashboard=dashboard,
            dashboard_url=dashboard_url,
            dashboard_api_key=dashboard_api_key,
            dashboard_publish_interval=dashboard_publish_interval,
        )
        self._env = None
        self._vec_env = None
        self._training_start_time: float = 0

    def setup(self) -> None:
        """Setup training environment and PPO model."""
        try:
            from stable_baselines3 import PPO
            from stable_baselines3.common.env_util import make_vec_env
        except ImportError:
            raise ImportError(
                "stable-baselines3 is required. Install with: pip install stable-baselines3"
            )

        # Create vectorized environment
        self._vec_env = make_vec_env(
            self.config.env_id,
            n_envs=self.config.num_envs,
            seed=self.config.seed,
        )

        # Create PPO model
        self.model = PPO(
            policy="MlpPolicy",
            env=self._vec_env,
            learning_rate=self.config.learning_rate,
            n_steps=self.config.n_steps,
            batch_size=self.config.batch_size,
            n_epochs=self.config.n_epochs,
            gamma=self.config.gamma,
            gae_lambda=self.config.gae_lambda,
            clip_range=self.config.clip_range,
            clip_range_vf=self.config.clip_range_vf,
            ent_coef=self.config.ent_coef,
            normalize_advantage=self.config.normalize_advantage,
            max_grad_norm=self.config.max_grad_norm,
            use_sde=self.config.use_sde,
            sde_sample_freq=self.config.sde_sample_freq,
            target_kl=self.config.target_kl,
            verbose=self.config.verbose,
            seed=self.config.seed,
            device=self.config.device,
        )

    def train(self, callback: Callable | None = None) -> Any:
        """
        Train the PPO model.

        Args:
            callback: Training callback

        Returns:
            Trained model
        """
        if self.model is None:
            self.setup()

        self.start_time = self._get_time()
        self._training_start_time = time.time()

        # Start dashboard session if enabled
        if self._dashboard and self._dashboard.is_enabled:
            try:
                self._dashboard.start_session(
                    project="ZBGym",
                    trainer="PPO",
                    env=self.config.env_id,
                    total_timesteps=self.config.total_timesteps,
                )
            except Exception as e:
                self._log(f"Dashboard start failed: {e}, continuing without dashboard")

        # Create dashboard callback if dashboard is enabled
        dashboard_callback = None
        if self._dashboard and self._dashboard.is_enabled:
            dashboard_callback = DashboardCallback(
                self._dashboard,
                publish_freq=self._dashboard._config.publish_interval,
            )

        # Combine callbacks
        if callback is not None and dashboard_callback is not None:
            from zbgym.trainer.callbacks import CallbackList
            if isinstance(callback, CallbackList):
                callback.callbacks.append(dashboard_callback)
            else:
                callback = CallbackList([callback, dashboard_callback])
        elif dashboard_callback is not None:
            callback = dashboard_callback

        try:
            self.model.learn(
                total_timesteps=self.config.total_timesteps,
                callback=callback,
                progress_bar=True,
                reset_num_timesteps=True,
            )

            self.stats.time_elapsed = self._get_time() - self.start_time

        finally:
            # Finish dashboard session
            if self._dashboard and self._dashboard.is_enabled:
                try:
                    self._dashboard.finish_session(
                        status="finished",
                        final_metrics={
                            "total_timesteps": self.config.total_timesteps,
                            "duration": time.time() - self._training_start_time,
                        },
                    )
                except Exception as e:
                    self._log(f"Dashboard finish failed: {e}")

        return self.model

    def _log(self, message: str) -> None:
        """Log message if verbose is enabled."""
        if self.config.verbose > 0:
            print(message)

    def predict(self, observation: np.ndarray, deterministic: bool = True) -> tuple:
        """
        Make a prediction.

        Args:
            observation: Environment observation
            deterministic: Use deterministic policy

        Returns:
            Action and state
        """
        if self.model is None:
            raise ValueError("Model not initialized. Call setup() or train() first.")

        action, state = self.model.predict(observation, deterministic=deterministic)
        return action, state

    def evaluate(
        self,
        env: Any,
        n_episodes: int = 10,
        deterministic: bool = True,
    ) -> dict[str, float]:
        """
        Evaluate the model.

        Args:
            env: Environment to evaluate in
            n_episodes: Number of episodes
            deterministic: Use deterministic policy

        Returns:
            Evaluation statistics
        """
        if self.model is None:
            raise ValueError("Model not initialized.")

        from stable_baselines3.common.evaluation import evaluate_policy

        rewards, lengths = evaluate_policy(
            self.model,
            env,
            n_eval_episodes=n_episodes,
            deterministic=deterministic,
            return_episode_rewards=True,
        )

        return {
            "mean_reward": float(np.mean(rewards)),
            "std_reward": float(np.std(rewards)),
            "mean_length": float(np.mean(lengths)),
            "std_length": float(np.std(lengths)),
        }

    def get_policy(self) -> Any:
        """Get the policy network."""
        if self.model is None:
            return None
        return self.model.policy

    def _get_time(self) -> float:
        """Get current time."""
        return __import__("time").time()
