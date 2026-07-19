"""Collision shapes for ZBGym."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from zbgym.physics.vector import Vector2D

if TYPE_CHECKING:
    from zbgym.physics.body import PhysicsBody


class Shape(ABC):
    """Abstract base class for collision shapes."""

    @abstractmethod
    def contains_point(self, point: Vector2D) -> bool:
        """Check if shape contains a point."""
        pass

    @abstractmethod
    def intersects(self, other: Shape) -> bool:
        """Check if shape intersects another."""
        pass

    @abstractmethod
    def get_center(self) -> Vector2D:
        """Get center point of shape."""
        pass

    @abstractmethod
    def get_bounding_radius(self) -> float:
        """Get bounding radius for broad phase."""
        pass


@dataclass
class Circle(Shape):
    """Circle collision shape."""

    center: Vector2D
    radius: float

    def contains_point(self, point: Vector2D) -> bool:
        return self.center.distance_to(point) <= self.radius

    def intersects(self, other: Shape) -> bool:
        if isinstance(other, Circle):
            return self.intersects_circle(other)
        elif isinstance(other, Rectangle):
            return self.intersects_rectangle(other)
        return False

    def intersects_circle(self, other: Circle) -> bool:
        distance = self.center.distance_to(other.center)
        return distance < self.radius + other.radius

    def intersects_rectangle(self, rect: Rectangle) -> bool:
        # Find closest point on rectangle to circle center
        closest_x = max(rect.min_x, min(self.center.x, rect.max_x))
        closest_y = max(rect.min_y, min(self.center.y, rect.max_y))

        distance = math.sqrt(
            (self.center.x - closest_x) ** 2 + (self.center.y - closest_y) ** 2
        )
        return distance < self.radius

    def get_center(self) -> Vector2D:
        return self.center

    def get_bounding_radius(self) -> float:
        return self.radius

    @classmethod
    def from_body(cls, body: PhysicsBody) -> Circle:
        """Create circle from physics body."""
        return cls(center=body.position, radius=body.radius)


@dataclass
class Rectangle(Shape):
    """Rectangle collision shape (axis-aligned)."""

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

    def contains_point(self, point: Vector2D) -> bool:
        return (
            self.min_x <= point.x <= self.max_x
            and self.min_y <= point.y <= self.max_y
        )

    def intersects(self, other: Shape) -> bool:
        if isinstance(other, Circle):
            return other.intersects_rectangle(self)
        elif isinstance(other, Rectangle):
            return self.intersects_rectangle(other)
        return False

    def intersects_rectangle(self, other: Rectangle) -> bool:
        return (
            self.min_x < other.max_x
            and self.max_x > other.min_x
            and self.min_y < other.max_y
            and self.max_y > other.min_y
        )

    def get_center(self) -> Vector2D:
        return Vector2D(
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
        )

    def get_bounding_radius(self) -> float:
        return math.sqrt(self.width**2 + self.height**2) / 2

    def get_closest_point(self, point: Vector2D) -> Vector2D:
        """Get closest point on rectangle to a point."""
        return Vector2D(
            max(self.min_x, min(point.x, self.max_x)),
            max(self.min_y, min(point.y, self.max_y)),
        )

    @classmethod
    def from_center_size(
        cls, center: Vector2D, width: float, height: float
    ) -> Rectangle:
        """Create rectangle from center and dimensions."""
        half_w = width / 2
        half_h = height / 2
        return cls(
            min_x=center.x - half_w,
            min_y=center.y - half_h,
            max_x=center.x + half_w,
            max_y=center.y + half_h,
        )

    @classmethod
    def from_body(cls, body: PhysicsBody) -> Rectangle:
        """Create rectangle from physics body."""
        return cls.from_center_size(
            body.position, body.width, body.height
        )


def create_shape_from_body(body: PhysicsBody) -> Shape:
    """Create appropriate shape from physics body."""
    if body.shape_type.value == "circle":
        return Circle.from_body(body)
    return Rectangle.from_body(body)
