"""Tests for physics body module."""

import pytest
from zbgym.physics.body import DynamicBody, BodyType, PhysicsBody, BoundingBox
from zbgym.physics.vector import Vector2D


class TestDynamicBody:
    """Test DynamicBody class."""

    def test_create(self):
        """Test creating a dynamic body."""
        body = DynamicBody(id="test_body")
        
        assert body.id == "test_body"
        assert body.position == Vector2D.zero()
        assert body.velocity == Vector2D.zero()
        assert body.body_type == BodyType.DYNAMIC

    def test_create_with_position(self):
        """Test creating body with initial position."""
        body = DynamicBody(
            id="test",
            position=Vector2D(100.0, 200.0)
        )
        
        assert body.position.x == 100.0
        assert body.position.y == 200.0

    def test_create_with_velocity(self):
        """Test creating body with initial velocity."""
        body = DynamicBody(
            id="test",
            velocity=Vector2D(10.0, 5.0)
        )
        
        assert body.velocity.x == 10.0
        assert body.velocity.y == 5.0

    def test_update_changes_position(self):
        """Test that update changes position."""
        body = DynamicBody(id="test", velocity=Vector2D(10.0, 0.0))
        
        body.update(1.0)
        
        # Position should have changed
        assert body.position.x != 0.0 or body.position.y != 0.0


class TestBodyType:
    """Test BodyType enum."""

    def test_body_types_exist(self):
        """Test all body types exist."""
        assert BodyType.STATIC is not None
        assert BodyType.DYNAMIC is not None
        assert BodyType.KINEMATIC is not None

    def test_body_type_values(self):
        """Test body type values."""
        assert BodyType.STATIC.value == "static"
        assert BodyType.DYNAMIC.value == "dynamic"
        assert BodyType.KINEMATIC.value == "kinematic"


class TestBoundingBox:
    """Test BoundingBox class."""

    def test_create(self):
        """Test creating bounding box."""
        bb = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=100)
        
        assert bb.min_x == 0
        assert bb.min_y == 0
        assert bb.max_x == 100
        assert bb.max_y == 100
        assert bb.width == 100
        assert bb.height == 100


class TestBodyDeterminism:
    """Test body physics determinism."""

    def test_same_update_same_result(self):
        """Test same updates produce same results."""
        results = []
        for _ in range(5):
            body = DynamicBody(
                id="test",
                velocity=Vector2D(10.0, 0.0)
            )
            body.update(0.1)
            results.append((body.position.x, body.position.y))
        
        # All results should be identical
        assert len(set(results)) == 1
