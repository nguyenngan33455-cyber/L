"""Collision detection modules for ZBGym."""

from zbgym.collision.detector import Collision, CollisionDetector
from zbgym.collision.shapes import Circle, Rectangle, Shape

# Alias for backwards compatibility
CollisionSystem = CollisionDetector

__all__ = [
    "Circle",
    "Collision",
    "CollisionDetector",
    "CollisionSystem",  # Alias for CollisionDetector
    "Rectangle",
    "Shape",
]
