"""Configuration management for ZBGym."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ZBGymConfig(BaseModel):
    """Main configuration for ZBGym."""

    # Physics settings
    gravity: float = 980.0
    friction: float = 0.98
    air_resistance: float = 0.99
    max_speed: float = 500.0
    tick_rate: int = 60

    # Arena settings
    arena_width: int = 2000
    arena_height: int = 1500
    safe_zone_shrink_rate: float = 0.5

    # Game settings
    game_mode: str = "deathmatch"
    max_players: int = 4
    respawn_time: float = 5.0
    match_duration: float = 600.0  # 10 minutes
    score_limit: int = 30

    # Training settings
    frame_skip: int = 4
    reward_scale: float = 1.0
    discount_factor: float = 0.99

    # Observation settings
    obs_include_items: bool = True
    obs_include_vision: bool = True
    obs_include_projectiles: bool = True
    obs_vision_range: float = 500.0

    # Replay settings
    save_replays: bool = True
    replay_dir: Path = Path("./replays")
    max_replays: int = 100

    # Dashboard settings
    dashboard_port: int = 8000
    dashboard_host: str = "0.0.0.0"

    # Logging
    log_level: str = "INFO"
    log_dir: Path = Path("./logs")

    class Config:
        """Pydantic config."""

        extra = "ignore"


@dataclass
class EnvironmentConfig:
    """Configuration for a ZBGym environment."""

    name: str = "BattleArena-v1"
    config: ZBGymConfig = field(default_factory=ZBGymConfig)

    # Map settings
    map_name: str = "default"
    map_data: dict[str, Any] = field(default_factory=dict)

    # Character settings
    characters: list[str] = field(default_factory=lambda: ["soldier"])
    num_agents: int = 2

    # Weapon pool
    weapon_pool: list[str] = field(default_factory=lambda: ["rifle", "pistol"])

    # Rendering
    render_mode: str | None = None
    render_fps: int = 30

    # Seed for reproducibility
    seed: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvironmentConfig:
        """Create config from dictionary."""
        config = ZBGymConfig(**data.get("config", {}))
        return cls(
            name=data.get("name", "BattleArena-v1"),
            config=config,
            map_name=data.get("map_name", "default"),
            characters=data.get("characters", ["soldier"]),
            num_agents=data.get("num_agents", 2),
            weapon_pool=data.get("weapon_pool", ["rifle", "pistol"]),
            render_mode=data.get("render_mode"),
            render_fps=data.get("render_fps", 30),
            seed=data.get("seed"),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> EnvironmentConfig:
        """Load config from YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "name": self.name,
            "config": self.config.model_dump(),
            "map_name": self.map_name,
            "characters": self.characters,
            "num_agents": self.num_agents,
            "weapon_pool": self.weapon_pool,
            "render_mode": self.render_mode,
            "render_fps": self.render_fps,
            "seed": self.seed,
        }

    def save_yaml(self, path: str | Path) -> None:
        """Save config to YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)


def get_default_config() -> ZBGymConfig:
    """Get the default ZBGym configuration."""
    return ZBGymConfig()


def load_config_from_env() -> ZBGymConfig:
    """Load configuration from environment variables."""
    config = ZBGymConfig()

    # Override with environment variables if set
    if tick_rate := os.getenv("ZBGYM_TICK_RATE"):
        config.tick_rate = int(tick_rate)
    if max_players := os.getenv("ZBGYM_MAX_PLAYERS"):
        config.max_players = int(max_players)
    if log_level := os.getenv("ZBGYM_LOG_LEVEL"):
        config.log_level = log_level
    if save_replays := os.getenv("ZBGYM_SAVE_REPLAYS"):
        config.save_replays = save_replays.lower() == "true"

    return config
