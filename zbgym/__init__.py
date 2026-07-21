"""
ZBGym: A professional Reinforcement Learning battle arena simulator.

ZBGym provides a modular, extensible environment for training RL agents
in battle arena combat scenarios.
"""

from zbgym.config import EnvironmentConfig, ZBGymConfig, get_default_config
from zbgym.make import make, register
from zbgym.version import (
    __author__,
    __description__,
    __email__,
    __license__,
    __title__,
    __url__,
    __version__,
    __version_info__,
)

__all__ = [
    # Version
    "__version__",
    "__version_info__",
    "__title__",
    "__description__",
    "__author__",
    "__email__",
    "__license__",
    "__url__",
    # Main API
    "make",
    "register",
    # Config
    "ZBGymConfig",
    "EnvironmentConfig",
    "get_default_config",
    # Environment
    "ZBGym",
]


def ZBGym(env_id: str = "BattleArena-v1", **kwargs) -> "BattleArena":
    """
    Convenience function to create a ZBGym environment.

    Args:
        env_id: Environment ID to create
        **kwargs: Additional arguments passed to make()

    Returns:
        ZBGym environment instance
    """
    return make(env_id, **kwargs)
