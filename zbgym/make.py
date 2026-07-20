"""Environment factory and registry for ZBGym."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArena

# Environment registry
_REGISTRY: dict[str, Callable[..., "BattleArena"]] = {}


class EnvironmentSpec:
    """Specification for a registered environment."""

    def __init__(
        self,
        id: str,
        entry_point: Callable[..., "BattleArena"],
        kwargs: dict[str, Any] | None = None,
        description: str = "",
    ) -> None:
        self.id = id
        self.entry_point = entry_point
        self.kwargs = kwargs or {}
        self.description = description

    def make(self, **kwargs: Any) -> "BattleArena":
        """Create an instance of this environment."""
        merged_kwargs = {**self.kwargs, **kwargs}
        return self.entry_point(**merged_kwargs)


def register(
    id: str,
    entry_point: Callable[..., "BattleArena"],
    kwargs: dict[str, Any] | None = None,
    description: str = "",
) -> None:
    """
    Register a new environment in the ZBGym registry.

    Args:
        id: Unique identifier for the environment (e.g., "BattleArena-v1")
        entry_point: Callable that returns an environment instance
        kwargs: Default keyword arguments for the environment
        description: Human-readable description of the environment
    """
    if id in _REGISTRY:
        raise ValueError(f"Environment '{id}' already registered")

    _REGISTRY[id] = entry_point
    # Also register in gymnasium for compatibility
    try:
        import gymnasium as gym

        gym.register(id, entry_point=entry_point, kwargs=kwargs)
    except ImportError:
        pass


def make(env_id: str, **kwargs: Any) -> "BattleArena":
    """
    Create a ZBGym environment by ID.

    Args:
        env_id: Environment identifier (e.g., "BattleArena-v1")
        **kwargs: Additional arguments passed to the environment

    Returns:
        ZBGym environment instance

    Raises:
        Error: If the environment ID is not found
    """
    # Import here to avoid circular imports
    from zbgym.env.battle_arena import BattleArena

    if env_id in _REGISTRY:
        return _REGISTRY[env_id](**kwargs)

    # Try gymnasium registry
    try:
        import gymnasium as gym

        return gym.make(env_id, **kwargs)
    except Exception:
        pass

    raise ValueError(f"Environment '{env_id}' not found. Did you register it?")


def list_envs() -> list[str]:
    """List all registered environment IDs."""
    return list(_REGISTRY.keys())


# Auto-register default environments
def _register_defaults() -> None:
    """Register default ZBGym environments."""
    from zbgym.env.battle_arena import BattleArena

    # Register default battle arena
    register(
        id="BattleArena-v1",
        entry_point=lambda **kw: BattleArena(**kw),
        description="Standard battle arena with 2 players",
    )
    register(
        id="BattleArena-v0",
        entry_point=lambda **kw: BattleArena(**kw),
        description="Legacy battle arena environment",
    )
    register(
        id="BattleArenaTeam-v1",
        entry_point=lambda **kw: BattleArena(mode="team_deathmatch", **kw),
        description="Team-based battle arena",
    )
    register(
        id="BattleArenaSurvival-v1",
        entry_point=lambda **kw: BattleArena(mode="survival", **kw),
        description="Survival mode with shrinking safe zone",
    )


# Initialize on import
_register_defaults()
