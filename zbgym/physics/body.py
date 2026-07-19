"""Physics body classes for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from zbgym.physics.vector import Vector2D
from zbgym.constants import DEFAULT_GRAVITY, DEFAULT_FRICTION, DEFAULT_MAX_SPEED

if TYPE_CHECKING:
    from zbgym.physics.movement import MovementSystem


class BodyType(Enum):
    """Types of physics bodies."""

    DYNAMIC = "dynamic"
    STATIC = "static"
    KINEMATIC = "kinematic"


class ShapeType(Enum):
    """Shapes for collision detection."""

    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    LINE = "line"


@dataclass
class BoundingBox:
    """Axis-aligned bounding box."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def center(self) -> Vector2D:
        return Vector2D(
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
        )

    @property
    def area(self) -> float:
        return self.width * self.height

    def intersects(self, other: BoundingBox) -> bool:
        """Check if this box intersects another."""
        return (
            self.min_x < other.max_x
            and self.max_x > other.min_x
            and self.min_y < other.max_y
            and self.max_y > other.min_y
        )

    def contains_point(self, point: Vector2D) -> bool:
        """Check if box contains a point."""
        return (
            self.min_x <= point.x <= self.max_x
            and self.min_y <= point.y <= self.max_y
        )

    @classmethod
    def from_center_size(
        cls, center: Vector2D, width: float, height: float
    ) -> BoundingBox:
        """Create box from center and dimensions."""
        half_w = width / 2
        half_h = height / 2
        return cls(
            min_x=center.x - half_w,
            min_y=center.y - half_h,
            max_x=center.x + half_w,
            max_y=center.y + half_h,
        )

    def expand(self, margin: float) -> BoundingBox:
        """Expand box by margin on all sides."""
        return BoundingBox(
            min_x=self.min_x - margin,
            min_y=self.min_y - margin,
            max_x=self.max_x + margin,
            max_y=self.max_y + margin,
        )


@dataclass
class PhysicsBody:
    """
    Base physics body.

    Represents an object's physical properties for collision and movement.
    """

    id: str
    position: Vector2D = field(default_factory=Vector2D.zero)
    velocity: Vector2D = field(default_factory=Vector2D.zero)
    acceleration: Vector2D = field(default_factory=Vector2D.zero)
    rotation: float = 0.0  # radians
    angular_velocity: float = 0.0

    # Shape properties
    shape_type: ShapeType = ShapeType.CIRCLE
    radius: float = 16.0  # for circle
    width: float = 32.0  # for rectangle
    height: float = 32.0  # for rectangle

    # Physical properties
    mass: float = 1.0
    restitution: float = 0.5  # bounciness
    friction: float = DEFAULT_FRICTION
    is_sensor: bool = False  # detects collision but doesn't respond

    # State
    body_type: BodyType = BodyType.DYNAMIC
    enabled: bool = True
    layer: int = 0  # collision layer
    mask: int = 0xFFFFFFFF  # collision mask

    def __post_init__(self) -> None:
        """Post-initialization."""
        pass

    @property
    def bounding_box(self) -> BoundingBox:
        """Get axis-aligned bounding box."""
        if self.shape_type == ShapeType.CIRCLE:
            return BoundingBox(
                min_x=self.position.x - self.radius,
                min_y=self.position.y - self.radius,
                max_x=self.position.x + self.radius,
                max_y=self.position.y + self.radius,
            )
        return BoundingBox.from_center_size(self.position, self.width, self.height)

    def apply_force(self, force: Vector2D) -> None:
        """Apply a force to the body."""
        if self.body_type == BodyType.DYNAMIC:
            self.acceleration += force / self.mass

    def apply_impulse(self, impulse: Vector2D) -> None:
        """Apply an instant impulse to the body."""
        if self.body_type == BodyType.DYNAMIC:
            self.velocity += impulse / self.mass

    def get_speed(self) -> float:
        """Get current speed."""
        return self.velocity.length

    def get_speed_squared(self) -> float:
        """Get squared speed (faster)."""
        return self.velocity.length_squared

    def set_position(self, x: float, y: float) -> None:
        """Set position directly."""
        self.position = Vector2D(x, y)

    def set_velocity(self, x: float, y: float) -> None:
        """Set velocity directly."""
        self.velocity = Vector2D(x, y)

    def can_collide_with(self, other: PhysicsBody) -> bool:
        """Check if collision is allowed with another body."""
        if not self.enabled or not other.enabled:
            return False
        return bool((self.layer & other.mask) and (other.layer & self.mask))

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "position": self.position.to_dict(),
            "velocity": self.velocity.to_dict(),
            "rotation": self.rotation,
            "shape_type": self.shape_type.value,
            "radius": self.radius,
            "width": self.width,
            "height": self.height,
            "mass": self.mass,
            "body_type": self.body_type.value,
            "layer": self.layer,
        }


@dataclass
class DynamicBody(PhysicsBody):
    """Dynamic physics body affected by forces."""

    body_type: BodyType = field(default=BodyType.DYNAMIC, init=False)

    # Movement properties
    max_speed: float = DEFAULT_MAX_SPEED
    acceleration_limit: float = 2000.0
    air_resistance: float = 0.99
    gravity_scale: float = 1.0
    use_gravity: bool = True

    def __post_init__(self) -> None:
        """Post-initialization."""
        pass

    def update(self, dt: float, gravity: float = DEFAULT_GRAVITY) -> None:
        """
        Update body physics.

        Args:
            dt: Delta time in seconds
            gravity: Gravity acceleration
        """
        if not self.enabled or self.body_type != BodyType.DYNAMIC:
            return

        # Apply gravity
        if self.use_gravity:
            self.acceleration += Vector2D(0, gravity * self.gravity_scale)

        # Update velocity
        self.velocity += self.acceleration * dt

        # Clamp speed
        if self.velocity.length > self.max_speed:
            self.velocity = self.velocity.normalized * self.max_speed

        # Apply air resistance
        self.velocity *= self.air_resistance

        # Update position
        self.position += self.velocity * dt

        # Reset acceleration
        self.acceleration = Vector2D.zero()

        # Update rotation
        self.rotation += self.angular_velocity * dt


@dataclass
class StaticBody(PhysicsBody):
    """Static physics body that doesn't move."""

    body_type: BodyType = field(default=BodyType.STATIC, init=False)


@dataclass
class KinematicBody(PhysicsBody):
    """Kinematic body controlled by code."""

    body_type: BodyType = field(default=BodyType.KINEMATIC, init=False)
