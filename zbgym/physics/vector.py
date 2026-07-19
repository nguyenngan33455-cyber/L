"""Vector mathematics for ZBGym physics."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterator


@dataclass
class Vector2D:
    """
    2D vector for positions, velocities, and forces.

    Provides common vector operations with immutable-style methods.
    """

    x: float = 0.0
    y: float = 0.0

    def __post_init__(self) -> None:
        self.x = float(self.x)
        self.y = float(self.y)

    @classmethod
    def zero(cls) -> Vector2D:
        """Create zero vector."""
        return cls(0.0, 0.0)

    @classmethod
    def up(cls) -> Vector2D:
        """Create unit vector pointing up."""
        return cls(0.0, -1.0)

    @classmethod
    def down(cls) -> Vector2D:
        """Create unit vector pointing down."""
        return cls(0.0, 1.0)

    @classmethod
    def left(cls) -> Vector2D:
        """Create unit vector pointing left."""
        return cls(-1.0, 0.0)

    @classmethod
    def right(cls) -> Vector2D:
        """Create unit vector pointing right."""
        return cls(1.0, 0.0)

    @classmethod
    def from_angle(cls, angle: float) -> Vector2D:
        """
        Create unit vector from angle in radians.

        Args:
            angle: Angle in radians, 0 = right, CCW positive
        """
        return cls(math.cos(angle), math.sin(angle))

    @property
    def length(self) -> float:
        """Magnitude of the vector."""
        return math.sqrt(self.x * self.x + self.y * self.y)

    @property
    def length_squared(self) -> float:
        """Squared magnitude (faster than length)."""
        return self.x * self.x + self.y * self.y

    @property
    def normalized(self) -> Vector2D:
        """Unit vector in the same direction."""
        length = self.length
        if length > 0:
            return Vector2D(self.x / length, self.y / length)
        return Vector2D.zero()

    @property
    def perpendicular(self) -> Vector2D:
        """Perpendicular vector (rotated 90 degrees CCW)."""
        return Vector2D(-self.y, self.x)

    @property
    def angle(self) -> float:
        """Angle in radians from the positive x-axis."""
        return math.atan2(self.y, self.x)

    def dot(self, other: Vector2D) -> float:
        """Dot product with another vector."""
        return self.x * other.x + self.y * other.y

    def cross(self, other: Vector2D) -> float:
        """2D cross product (returns scalar)."""
        return self.x * other.y - self.y * other.x

    def distance_to(self, other: Vector2D) -> float:
        """Distance to another point."""
        return (self - other).length

    def distance_squared_to(self, other: Vector2D) -> float:
        """Squared distance to another point."""
        return (self - other).length_squared

    def angle_to(self, other: Vector2D) -> float:
        """Angle to another point in radians."""
        return (other - self).angle

    def lerp(self, other: Vector2D, t: float) -> Vector2D:
        """Linear interpolation to another vector."""
        return self + (other - self) * t

    def rotate(self, angle: float) -> Vector2D:
        """Rotate by angle in radians."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Vector2D(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a,
        )

    def clamp_length(self, max_length: float) -> Vector2D:
        """Clamp magnitude to max_length."""
        if self.length_squared > max_length * max_length:
            return self.normalized * max_length
        return self

    def __add__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2D:
        return Vector2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vector2D:
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> Vector2D:
        return Vector2D(self.x / scalar, self.y / scalar)

    def __neg__(self) -> Vector2D:
        return Vector2D(-self.x, -self.y)

    def __abs__(self) -> Vector2D:
        return Vector2D(abs(self.x), abs(self.y))

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y

    def __repr__(self) -> str:
        return f"Vector2D({self.x:.2f}, {self.y:.2f})"

    def to_tuple(self) -> tuple[float, float]:
        """Convert to tuple."""
        return (self.x, self.y)

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {"x": self.x, "y": self.y}


@dataclass
class Vector3D:
    """3D vector for positions, velocities, and forces."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __post_init__(self) -> None:
        self.x = float(self.x)
        self.y = float(self.y)
        self.z = float(self.z)

    @classmethod
    def zero(cls) -> Vector3D:
        """Create zero vector."""
        return cls(0.0, 0.0, 0.0)

    @property
    def length(self) -> float:
        """Magnitude of the vector."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    @property
    def normalized(self) -> Vector3D:
        """Unit vector in the same direction."""
        length = self.length
        if length > 0:
            return Vector3D(self.x / length, self.y / length, self.z / length)
        return Vector3D.zero()

    def dot(self, other: Vector3D) -> float:
        """Dot product with another vector."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vector3D) -> Vector3D:
        """Cross product with another vector."""
        return Vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def distance_to(self, other: Vector3D) -> float:
        """Distance to another point."""
        return (self - other).length

    def __add__(self, other: Vector3D) -> Vector3D:
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vector3D) -> Vector3D:
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Vector3D:
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> Vector3D:
        return self.__mul__(scalar)

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y
        yield self.z

    def __repr__(self) -> str:
        return f"Vector3D({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"

    def to_tuple(self) -> tuple[float, float, float]:
        """Convert to tuple."""
        return (self.x, self.y, self.z)


# Utility functions
def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between two values."""
    return a + (b - a) * t


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def approach(current: float, target: float, delta: float) -> float:
    """Approach target by delta amount."""
    if current < target:
        return min(current + delta, target)
    return max(current - delta, target)


def angle_lerp(a: float, b: float, t: float) -> float:
    """Lerp between two angles, taking the shortest path."""
    delta = ((b - a + math.pi) % (2 * math.pi)) - math.pi
    return a + delta * t
