"""Collision detection system for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from zbgym.physics.vector import Vector2D
from zbgym.physics.body import PhysicsBody
from zbgym.collision.shapes import Circle, Rectangle, create_shape_from_body

if TYPE_CHECKING:
    from zbgym.engine.event_bus import EventBus


@dataclass
class Collision:
    """Represents a collision between two bodies."""

    body_a: PhysicsBody
    body_b: PhysicsBody
    point: Vector2D
    normal: Vector2D
    penetration: float
    timestamp: float = 0.0

    @property
    def entity_a(self) -> str:
        return self.body_a.id

    @property
    def entity_b(self) -> str:
        return self.body_b.id


class CollisionDetector:
    """
    Collision detection system with broad and narrow phase.

    Supports:
    - Spatial hashing for efficient broad phase
    - Multiple collision shapes (circle, rectangle)
    - Collision callbacks
    - Collision layers and masks
    """

    def __init__(self, cell_size: float = 100.0) -> None:
        """
        Initialize collision detector.

        Args:
            cell_size: Size of spatial hash cells
        """
        self._cell_size = cell_size
        self._bodies: dict[str, PhysicsBody] = {}
        self._spatial_hash: dict[int, set[str]] = {}
        self._collision_callbacks: list[Callable[[Collision], None]] = []

    def register_body(self, body: PhysicsBody) -> None:
        """Register a body for collision detection."""
        self._bodies[body.id] = body

    def unregister_body(self, body_id: str) -> bool:
        """Unregister a body."""
        if body_id in self._bodies:
            del self._bodies[body_id]
            return True
        return False

    def register_callback(self, callback: Callable[[Collision], None]) -> None:
        """Register a collision callback."""
        self._collision_callbacks.append(callback)

    def detect(self) -> list[Collision]:
        """
        Detect all collisions.

        Returns:
            List of detected collisions
        """
        # Clear spatial hash
        self._spatial_hash.clear()

        # Populate spatial hash
        for body in self._bodies.values():
            if not body.enabled:
                continue

            shape = create_shape_from_body(body)
            radius = shape.get_bounding_radius()

            # Get cells this body could be in
            min_cell_x = int((body.position.x - radius) / self._cell_size)
            max_cell_x = int((body.position.x + radius) / self._cell_size)
            min_cell_y = int((body.position.y - radius) / self._cell_size)
            max_cell_y = int((body.position.y + radius) / self._cell_size)

            for cx in range(min_cell_x, max_cell_x + 1):
                for cy in range(min_cell_y, max_cell_y + 1):
                    cell_hash = self._hash_cell(cx, cy)
                    if cell_hash not in self._spatial_hash:
                        self._spatial_hash[cell_hash] = set()
                    self._spatial_hash[cell_hash].add(body.id)

        # Detect collisions
        collisions: list[Collision] = []
        checked_pairs: set[tuple[str, str]] = set()

        for body_id, body in self._bodies.items():
            if not body.enabled:
                continue

            # Get nearby bodies from spatial hash
            shape = create_shape_from_body(body)
            radius = shape.get_bounding_radius()

            min_cell_x = int((body.position.x - radius) / self._cell_size)
            max_cell_x = int((body.position.x + radius) / self._cell_size)
            min_cell_y = int((body.position.y - radius) / self._cell_size)
            max_cell_y = int((body.position.y + radius) / self._cell_size)

            for cx in range(min_cell_x, max_cell_x + 1):
                for cy in range(min_cell_y, max_cell_y + 1):
                    cell_hash = self._hash_cell(cx, cy)
                    if cell_hash not in self._spatial_hash:
                        continue

                    for other_id in self._spatial_hash[cell_hash]:
                        if other_id == body_id:
                            continue

                        # Check if pair already processed
                        pair = tuple(sorted([body_id, other_id]))
                        if pair in checked_pairs:
                            continue
                        checked_pairs.add(pair)

                        other = self._bodies.get(other_id)
                        if other is None or not other.enabled:
                            continue

                        # Check collision layers
                        if not body.can_collide_with(other):
                            continue

                        # Narrow phase collision detection
                        collision = self._check_collision(body, other)
                        if collision is not None:
                            collisions.append(collision)
                            for callback in self._collision_callbacks:
                                callback(collision)

        return collisions

    def _check_collision(
        self, body_a: PhysicsBody, body_b: PhysicsBody
    ) -> Collision | None:
        """Perform narrow phase collision detection."""
        shape_a = create_shape_from_body(body_a)
        shape_b = create_shape_from_body(body_b)

        if isinstance(shape_a, Circle) and isinstance(shape_b, Circle):
            return self._circle_vs_circle(shape_a, shape_b, body_a, body_b)
        elif isinstance(shape_a, Circle) and isinstance(shape_b, Rectangle):
            return self._circle_vs_rectangle(shape_a, shape_b, body_a, body_b)
        elif isinstance(shape_a, Rectangle) and isinstance(shape_b, Circle):
            result = self._circle_vs_rectangle(shape_b, shape_a, body_b, body_a)
            if result:
                # Swap bodies back
                return Collision(
                    body_a=body_a,
                    body_b=body_b,
                    point=result.point,
                    normal=-result.normal,
                    penetration=result.penetration,
                )
            return None
        elif isinstance(shape_a, Rectangle) and isinstance(shape_b, Rectangle):
            return self._rect_vs_rect(shape_a, shape_b, body_a, body_b)

        return None

    def _circle_vs_circle(
        self,
        circle_a: Circle,
        circle_b: Circle,
        body_a: PhysicsBody,
        body_b: PhysicsBody,
    ) -> Collision | None:
        """Circle vs Circle collision."""
        delta = circle_b.center - circle_a.center
        distance = delta.length
        radii_sum = circle_a.radius + circle_b.radius

        if distance >= radii_sum:
            return None

        # Calculate collision data
        if distance > 0:
            normal = delta / distance
        else:
            normal = Vector2D.right()

        point = circle_a.center + normal * circle_a.radius
        penetration = radii_sum - distance

        return Collision(
            body_a=body_a,
            body_b=body_b,
            point=point,
            normal=normal,
            penetration=penetration,
        )

    def _circle_vs_rectangle(
        self,
        circle: Circle,
        rect: Rectangle,
        body_a: PhysicsBody,
        body_b: PhysicsBody,
    ) -> Collision | None:
        """Circle vs Rectangle collision."""
        closest = rect.get_closest_point(circle.center)
        delta = circle.center - closest
        distance = delta.length

        if distance >= circle.radius:
            return None

        # Calculate collision data
        if distance > 0:
            normal = delta / distance
        else:
            normal = Vector2D.up()

        point = closest
        penetration = circle.radius - distance

        return Collision(
            body_a=body_a,
            body_b=body_b,
            point=point,
            normal=normal,
            penetration=penetration,
        )

    def _rect_vs_rect(
        self,
        rect_a: Rectangle,
        rect_b: Rectangle,
        body_a: PhysicsBody,
        body_b: PhysicsBody,
    ) -> Collision | None:
        """Rectangle vs Rectangle collision."""
        # Check for overlap
        if (
            rect_a.max_x <= rect_b.min_x
            or rect_a.min_x >= rect_b.max_x
            or rect_a.max_y <= rect_b.min_y
            or rect_a.min_y >= rect_b.max_y
        ):
            return None

        # Calculate overlap on each axis
        overlap_x = min(rect_a.max_x, rect_b.max_x) - max(rect_a.min_x, rect_b.min_x)
        overlap_y = min(rect_a.max_y, rect_b.max_y) - max(rect_a.min_y, rect_b.min_y)

        # Choose smaller overlap as penetration axis
        if overlap_x < overlap_y:
            penetration = overlap_x
            if rect_a.get_center().x < rect_b.get_center().x:
                normal = Vector2D.left()
                point = Vector2D(rect_a.max_x, rect_a.get_center().y)
            else:
                normal = Vector2D.right()
                point = Vector2D(rect_a.min_x, rect_a.get_center().y)
        else:
            penetration = overlap_y
            if rect_a.get_center().y < rect_b.get_center().y:
                normal = Vector2D.up()
                point = Vector2D(rect_a.get_center().x, rect_a.max_y)
            else:
                normal = Vector2D.down()
                point = Vector2D(rect_a.get_center().x, rect_a.min_y)

        return Collision(
            body_a=body_a,
            body_b=body_b,
            point=point,
            normal=normal,
            penetration=penetration,
        )

    def _hash_cell(self, x: int, y: int) -> int:
        """Hash cell coordinates to integer."""
        # Simple but effective hashing
        return (x * 73856093) ^ (y * 19349663)

    def raycast(
        self,
        origin: Vector2D,
        direction: Vector2D,
        max_distance: float = 1000.0,
        layer_mask: int = 0xFFFFFFFF,
    ) -> Collision | None:
        """
        Raycast against registered bodies.

        Args:
            origin: Ray origin
            direction: Ray direction (will be normalized)
            max_distance: Maximum ray distance
            layer_mask: Layer mask to filter bodies

        Returns:
            First collision or None
        """
        direction = direction.normalized
        closest_collision: Collision | None = None
        closest_distance = max_distance

        for body in self._bodies.values():
            if not body.enabled:
                continue
            if not (body.layer & layer_mask):
                continue

            shape = create_shape_from_body(body)

            if isinstance(shape, Circle):
                collision = self._raycast_circle(origin, direction, shape, body, max_distance)
                if collision:
                    dist = (collision.point - origin).length
                    if dist < closest_distance:
                        closest_distance = dist
                        closest_collision = collision

        return closest_collision

    def _raycast_circle(
        self,
        origin: Vector2D,
        direction: Vector2D,
        circle: Circle,
        body: PhysicsBody,
        max_distance: float,
    ) -> Collision | None:
        """Ray vs Circle intersection."""
        to_circle = circle.center - origin
        projection = to_circle.dot(direction)

        if projection < 0 or projection > max_distance:
            return None

        closest_point = origin + direction * projection
        distance = closest_point.distance_to(circle.center)

        if distance <= circle.radius:
            penetration = circle.radius - distance
            normal = (closest_point - circle.center).normalized if distance > 0 else direction

            return Collision(
                body_a=body,
                body_b=body,  # Ray has no body
                point=closest_point,
                normal=normal,
                penetration=penetration,
            )

        return None

    def clear(self) -> None:
        """Clear all registered bodies."""
        self._bodies.clear()
        self._spatial_hash.clear()

    def get_body(self, body_id: str) -> PhysicsBody | None:
        """Get a registered body by ID."""
        return self._bodies.get(body_id)
