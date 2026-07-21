"""Universal Environment Framework for ZBGym.

This module provides a framework for supporting multiple game types
with a unified RL interface.
"""

from zbgym.envs.adapters.zooba import ZoobaAdapter
from zbgym.envs.base.environment import BaseEnvironment, EnvironmentConfig

__all__ = [
    "BaseEnvironment",
    "EnvironmentConfig",
    "ZoobaAdapter",
]


def make_env(env_id: str, **kwargs) -> BaseEnvironment:
    """
    Create an environment by ID.

    Args:
        env_id: Environment ID (e.g., "Zooba-v1")
        **kwargs: Additional arguments

    Returns:
        BaseEnvironment instance
    """
    adapters = {
        "Zooba-v1": ZoobaAdapter,
    }

    if env_id not in adapters:
        raise ValueError(f"Unknown environment: {env_id}. Available: {list(adapters.keys())}")

    return adapters[env_id](**kwargs)
