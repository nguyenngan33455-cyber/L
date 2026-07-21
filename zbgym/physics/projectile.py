"""Projectile physics for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from zbgym.constants import DEFAULT_GRAVITY
from zbgym.physics.body import DynamicBody
from zbgym.physics.vector import Vector2D


class ProjectileType(Enum):
    """Types of projectiles."""

    BULLET = "bullet"
    ROCKET = "rocket"
    GRENADE = "grenade"
    ARROW = "arrow"
    ENERGY = "energy"
    MELEE = "melee"


@dataclass
class ProjectileConfig:
    """Configuration for a projectile type."""

    speed: float = 1000.0
    gravity_scale: float = 0.0
    drag: float = 1.0
    max_distance: float = 2000.0
    explosion_radius: float = 0.0
    explosion_damage: float = 0.0
    penetration: int = 0
    ricochet: int = 0
    size: float = 4.0
    lifetime: float = 10.0


@dataclass
class Projectile(DynamicBody):
    """
    Projectile physics body.

    Extended from DynamicBody with projectile-specific properties.
    """

    projectile_type: ProjectileType = ProjectileType.BULLET
    config: ProjectileConfig = field(default_factory=ProjectileConfig)

    # Damage properties
    damage: float = 10.0
    headshot_multiplier: float = 1.5
    critical_multiplier: float = 1.25

    # Owner tracking
    owner_id: str | None = None

    # State
    distance_traveled: float = 0.0
    lifetime_remaining: float = 10.0
    bounces_remaining: int = 0
    penetration_count: int = 0

    # Visual
    trail_color: tuple[int, int, int] = (255, 200, 100)
    trail_length: int = 5

    def __post_init__(self) -> None:
        super().__post_init__()
        # Apply config
        self.speed = self.config.speed
        self.gravity_scale = self.config.gravity_scale
        self.use_gravity = self.config.gravity_scale > 0
        self.bounces_remaining = self.config.ricochet
        self.lifetime_remaining = self.config.lifetime

    def update(self, dt: float) -> None:
        """Update projectile physics."""
        if not self.enabled:
            return

        # Apply gravity
        if self.use_gravity:
            gravity = Vector2D(0, DEFAULT_GRAVITY * self.gravity_scale)
            self.velocity += gravity * dt

        # Apply drag
        if self.config.drag < 1.0:
            self.velocity *= self.config.drag

        # Update position
        old_position = (
            self.position.copy()
            if hasattr(self.position, "copy")
            else Vector2D(self.position.x, self.position.y)
        )
        self.position += self.velocity * dt

        # Track distance
        delta = self.position - old_position
        self.distance_traveled += delta.length

        # Update lifetime
        self.lifetime_remaining -= dt

        # Update rotation to face velocity direction
        if self.velocity.length_squared > 0:
            self.rotation = self.velocity.angle

    def is_expired(self) -> bool:
        """Check if projectile should be destroyed."""
        return (
            self.lifetime_remaining <= 0
            or self.distance_traveled >= self.config.max_distance
            or not self.enabled
        )

    def on_hit(self, target_id: str) -> dict:
        """
        Called when projectile hits something.

        Args:
            target_id: ID of the hit entity

        Returns:
            Impact data for damage calculation
        """
        return {
            "damage": self.damage,
            "headshot_multiplier": self.headshot_multiplier,
            "critical_multiplier": self.critical_multiplier,
            "owner_id": self.owner_id,
            "projectile_id": self.id,
            "position": self.position.to_dict(),
            "velocity": self.velocity.to_dict(),
        }

    def on_bounce(self, normal: Vector2D) -> None:
        """Handle bounce off surface."""
        if self.bounces_remaining > 0:
            # Reflect velocity
            dot = self.velocity.dot(normal)
            self.velocity = self.velocity - normal * (2 * dot)
            self.bounces_remaining -= 1
        else:
            self.enabled = False

    def on_penetrate(self) -> bool:
        """
        Attempt to penetrate through target.

        Returns:
            True if can continue, False if should stop
        """
        if self.config.penetration > 0:
            self.penetration_count += 1
            if self.penetration_count <= self.config.penetration:
                # Reduce damage on penetration
                self.damage *= 0.7
                return True
        return False


def create_projectile(
    projectile_type: ProjectileType,
    position: Vector2D,
    direction: Vector2D,
    config: ProjectileConfig | None = None,
    owner_id: str | None = None,
    damage: float = 10.0,
) -> Projectile:
    """
    Factory function to create a projectile.

    Args:
        projectile_type: Type of projectile
        position: Starting position
        direction: Direction to fire (will be normalized)
        config: Projectile configuration
        owner_id: ID of entity that fired the projectile
        damage: Base damage

    Returns:
        New Projectile instance
    """
    config = config or ProjectileConfig()
    direction = direction.normalized

    return Projectile(
        id=f"proj_{id(object())}",
        position=position,
        velocity=direction * config.speed,
        projectile_type=projectile_type,
        config=config,
        damage=damage,
        owner_id=owner_id,
    )
