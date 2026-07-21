"""Weapon plugin system for ZBGym."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import yaml

from zbgym.constants import WeaponType
from zbgym.physics.projectile import Projectile, ProjectileConfig
from zbgym.physics.vector import Vector2D
from zbgym.plugins.base import Plugin, PluginMetadata, PluginRegistry

if TYPE_CHECKING:
    from zbgym.engine.event_bus import EventBus


@dataclass
class WeaponStats:
    """Weapon statistics."""

    damage: float = 10.0
    fire_rate: float = 10.0  # rounds per second
    projectile_speed: float = 1000.0
    range: float = 1000.0
    magazine_size: int = 30
    total_ammo: int = 120
    reload_time: float = 2.0

    # Accuracy
    spread: float = 0.0  # radians
    recoil: float = 0.0

    # Special
    critical_chance: float = 0.05
    critical_multiplier: float = 1.5
    headshot_multiplier: float = 2.0
    penetration: int = 0
    ricochet: int = 0

    # Projectile
    projectile_count: int = 1
    explosion_radius: float = 0.0
    explosion_damage: float = 0.0

    # Range damage falloff
    min_damage_ratio: float = 0.5
    max_damage_distance: float = 500.0


@dataclass
class WeaponConfig:
    """Configuration for a weapon type."""

    weapon_type: WeaponType = WeaponType.RIFLE
    stats: WeaponStats = field(default_factory=WeaponStats)
    model_id: str = "default"
    fire_sound: str = "default_fire"
    reload_sound: str = "default_reload"


class Weapon(Plugin):
    """
    Weapon plugin base class.

    Weapons are items that characters can use to attack.
    Each weapon type is a plugin that defines stats and behaviors.
    """

    metadata: PluginMetadata
    config: WeaponConfig

    def __init__(
        self,
        owner_id: str | None = None,
        event_bus: EventBus | None = None,
        seed: int | None = None,
    ) -> None:
        """
        Initialize weapon.

        Args:
            owner_id: ID of the character owning this weapon
            event_bus: Event bus for weapon events
            seed: Random seed for deterministic behavior
        """
        self.owner_id = owner_id
        self.event_bus = event_bus

        # Deterministic RNG
        self._rng = random.Random(seed)

        # Ammo state
        self.current_ammo = self.config.stats.magazine_size
        self.reserve_ammo = self.config.stats.total_ammo

        # Firing state
        self.is_reloading = False
        self.reload_timer = 0.0
        self.fire_cooldown = 0.0

        # Burst
        self.burst_count = 0
        self.burst_cooldown = 0.0

    def initialize(self) -> None:
        """Initialize weapon."""
        self._reset_state()

    def shutdown(self) -> None:
        """Cleanup weapon."""

    def _reset_state(self) -> None:
        """Reset weapon to ready state."""
        self.current_ammo = self.config.stats.magazine_size
        self.is_reloading = False
        self.reload_timer = 0.0
        self.fire_cooldown = 0.0

    def can_fire(self) -> bool:
        """Check if weapon can fire."""
        if self.is_reloading:
            return False
        if self.current_ammo <= 0:
            return False
        if self.fire_cooldown > 0:
            return False
        return True

    def fire(self, position: Vector2D, direction: Vector2D) -> list[Projectile]:
        """
        Fire the weapon.

        Args:
            position: Firing position
            direction: Firing direction

        Returns:
            List of projectiles created
        """
        if not self.can_fire():
            return []

        projectiles = []

        # Consume ammo
        self.current_ammo -= 1

        # Set cooldown
        self.fire_cooldown = 1.0 / self.config.stats.fire_rate

        # Create projectiles
        for i in range(self.config.stats.projectile_count):
            # Apply spread using seeded RNG

            spread = self.config.stats.spread
            if spread > 0:
                angle_offset = self._rng.gauss(0, spread)
            else:
                angle_offset = 0.0

            projectile_dir = direction.rotate(angle_offset)

            # Create projectile config
            proj_config = ProjectileConfig(
                speed=self.config.stats.projectile_speed,
                max_distance=self.config.stats.range,
                explosion_radius=self.config.stats.explosion_radius,
                explosion_damage=self.config.stats.explosion_damage,
                penetration=self.config.stats.penetration,
                ricochet=self.config.stats.ricochet,
            )

            # Create projectile
            projectile = Projectile(
                id=f"proj_{id(object())}",
                position=position,
                velocity=projectile_dir * self.config.stats.projectile_speed,
                config=proj_config,
                damage=self.config.stats.damage,
                owner_id=self.owner_id,
            )

            projectiles.append(projectile)

        # Emit fire event
        if self.event_bus:
            self.event_bus.emit(
                "projectile_fire",
                weapon_id=self.metadata.id,
                owner_id=self.owner_id,
                position=position.to_dict(),
                direction=direction.to_dict(),
                projectile_count=len(projectiles),
            )

        return projectiles

    def reload(self) -> bool:
        """
        Start reloading.

        Returns:
            True if reload started
        """
        if self.is_reloading:
            return False
        if self.reserve_ammo <= 0:
            return False
        if self.current_ammo >= self.config.stats.magazine_size:
            return False

        self.is_reloading = True
        self.reload_timer = self.config.stats.reload_time

        # Emit reload event
        if self.event_bus:
            self.event_bus.emit(
                "weapon_reload",
                weapon_id=self.metadata.id,
                owner_id=self.owner_id,
            )

        return True

    def update(self, dt: float) -> None:
        """Update weapon state."""
        # Update fire cooldown
        if self.fire_cooldown > 0:
            self.fire_cooldown = max(0, self.fire_cooldown - dt)

        # Update reload
        if self.is_reloading:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self._complete_reload()

    def _complete_reload(self) -> None:
        """Complete the reload."""
        ammo_needed = self.config.stats.magazine_size - self.current_ammo
        ammo_available = min(ammo_needed, self.reserve_ammo)

        self.current_ammo += ammo_available
        self.reserve_ammo -= ammo_available
        self.is_reloading = False
        self.reload_timer = 0.0

    def add_ammo(self, amount: int) -> int:
        """
        Add ammo to reserve.

        Args:
            amount: Ammo to add

        Returns:
            Actual ammo added
        """
        max_ammo = self.config.stats.total_ammo
        can_add = max_ammo - self.reserve_ammo
        actual = min(amount, can_add)

        self.reserve_ammo += actual
        return actual

    def get_stats(self) -> dict[str, Any]:
        """Get current weapon stats."""
        return {
            "current_ammo": self.current_ammo,
            "magazine_size": self.config.stats.magazine_size,
            "reserve_ammo": self.reserve_ammo,
            "is_reloading": self.is_reloading,
            "reload_progress": (
                1.0 - self.reload_timer / self.config.stats.reload_time
                if self.is_reloading
                else 0.0
            ),
            "can_fire": self.can_fire(),
        }

    @classmethod
    def from_yaml(cls, yaml_path: str) -> WeaponConfig:
        """Load weapon config from YAML file."""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        weapon_type = WeaponType(data.get("type", "rifle"))
        stats = WeaponStats(**data.get("stats", {}))
        config = WeaponConfig(weapon_type=weapon_type, stats=stats)

        if "model" in data:
            config.model_id = data["model"]
        if "sounds" in data:
            config.fire_sound = data["sounds"].get("fire", "default_fire")
            config.reload_sound = data["sounds"].get("reload", "default_reload")

        return config


# Weapon registry
weapon_registry = PluginRegistry[Weapon]()


def register_weapon(
    weapon_id: str,
    name: str,
    weapon_type: WeaponType,
    stats: WeaponStats,
    **kwargs,
) -> type[Weapon]:
    """
    Decorator to register a weapon type.

    Usage:
        @register_weapon("rifle", "Assault Rifle", WeaponType.RIFLE, WeaponStats(...))
        class Rifle(Weapon):
            pass
    """
    _config = WeaponConfig(
        weapon_type=weapon_type,
        stats=stats,
        **kwargs,
    )
    _metadata = PluginMetadata(
        id=weapon_id,
        name=name,
        description=kwargs.get("description", ""),
    )

    def decorator(cls: type[Weapon]) -> type[Weapon]:
        # Use type() to create class with proper scope
        RegisteredWeapon = type(
            f"Registered{cls.__name__}",
            (cls,),
            {
                "metadata": _metadata,
                "config": _config,
            },
        )

        weapon_registry.register(RegisteredWeapon, weapon_id)
        return cls

    return decorator


def create_weapon(
    weapon_id: str,
    owner_id: str | None = None,
    **kwargs,
) -> Weapon | None:
    """
    Create a weapon instance.

    Args:
        weapon_id: Type of weapon to create
        owner_id: ID of character holding this weapon
        **kwargs: Additional arguments

    Returns:
        Weapon instance or None if not found
    """
    weapon_type = weapon_registry.get(weapon_id)
    if weapon_type is None:
        return None

    return weapon_type(owner_id=owner_id, **kwargs)


# Pre-register default weapons
@register_weapon(
    "rifle",
    "Assault Rifle",
    WeaponType.RIFLE,
    WeaponStats(
        damage=15.0,
        fire_rate=10.0,
        projectile_speed=1500.0,
        range=1000.0,
        magazine_size=30,
        total_ammo=120,
        reload_time=2.0,
        spread=0.02,
    ),
)
class Rifle(Weapon):
    pass


@register_weapon(
    "pistol",
    "Pistol",
    WeaponType.PISTOL,
    WeaponStats(
        damage=10.0,
        fire_rate=6.0,
        projectile_speed=1200.0,
        range=500.0,
        magazine_size=12,
        total_ammo=48,
        reload_time=1.5,
        spread=0.03,
    ),
)
class Pistol(Weapon):
    pass


@register_weapon(
    "shotgun",
    "Shotgun",
    WeaponType.SHOTGUN,
    WeaponStats(
        damage=8.0,
        fire_rate=1.5,
        projectile_speed=800.0,
        range=300.0,
        magazine_size=8,
        total_ammo=32,
        reload_time=2.5,
        spread=0.15,
        projectile_count=8,
    ),
)
class Shotgun(Weapon):
    pass


@register_weapon(
    "sniper",
    "Sniper Rifle",
    WeaponType.SNIPER,
    WeaponStats(
        damage=50.0,
        fire_rate=0.5,
        projectile_speed=2000.0,
        range=2000.0,
        magazine_size=5,
        total_ammo=20,
        reload_time=3.0,
        spread=0.005,
        critical_chance=0.3,
        headshot_multiplier=2.5,
    ),
)
class Sniper(Weapon):
    pass


@register_weapon(
    "smg",
    "SMG",
    WeaponType.SMG,
    WeaponStats(
        damage=8.0,
        fire_rate=20.0,
        projectile_speed=1000.0,
        range=400.0,
        magazine_size=25,
        total_ammo=100,
        reload_time=1.8,
        spread=0.06,
    ),
)
class SMG(Weapon):
    pass
