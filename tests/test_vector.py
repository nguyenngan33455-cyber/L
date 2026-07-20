"""Tests for vector physics module."""

import math
import pytest
from zbgym.physics.vector import Vector2D


class TestVector2D:
    """Test Vector2D class."""

    def test_create(self):
        """Test creating a vector."""
        v = Vector2D(3.0, 4.0)
        assert v.x == 3.0
        assert v.y == 4.0

    def test_zero(self):
        """Test zero vector."""
        v = Vector2D.zero()
        assert v.x == 0.0
        assert v.y == 0.0

    def test_right(self):
        """Test right unit vector."""
        v = Vector2D.right()
        assert v.x == 1.0
        assert v.y == 0.0

    def test_up(self):
        """Test up unit vector (negative y in screen coords)."""
        v = Vector2D.up()
        assert v.x == 0.0
        assert v.y == -1.0

    def test_down(self):
        """Test down unit vector."""
        v = Vector2D.down()
        assert v.x == 0.0
        assert v.y == 1.0

    def test_left(self):
        """Test left unit vector."""
        v = Vector2D.left()
        assert v.x == -1.0
        assert v.y == 0.0

    def test_addition(self):
        """Test vector addition."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, 4.0)
        result = v1 + v2
        assert result.x == 4.0
        assert result.y == 6.0

    def test_subtraction(self):
        """Test vector subtraction."""
        v1 = Vector2D(5.0, 7.0)
        v2 = Vector2D(2.0, 3.0)
        result = v1 - v2
        assert result.x == 3.0
        assert result.y == 4.0

    def test_multiplication_scalar(self):
        """Test scalar multiplication."""
        v = Vector2D(2.0, 3.0)
        result = v * 2.0
        assert result.x == 4.0
        assert result.y == 6.0

    def test_multiplication_reverse(self):
        """Test reverse scalar multiplication."""
        v = Vector2D(2.0, 3.0)
        result = 2.0 * v
        assert result.x == 4.0
        assert result.y == 6.0

    def test_division(self):
        """Test vector division."""
        v = Vector2D(4.0, 6.0)
        result = v / 2.0
        assert result.x == 2.0
        assert result.y == 3.0

    def test_length_property(self):
        """Test length property (magnitude)."""
        v = Vector2D(3.0, 4.0)
        assert v.length == 5.0

    def test_length_squared(self):
        """Test squared length."""
        v = Vector2D(3.0, 4.0)
        assert v.length_squared == 25.0

    def test_normalized(self):
        """Test vector normalization (property)."""
        v = Vector2D(3.0, 4.0)
        normalized = v.normalized
        assert abs(normalized.length - 1.0) < 0.0001

    def test_dot_product(self):
        """Test dot product."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, 4.0)
        assert v1.dot(v2) == 11.0

    def test_cross_product(self):
        """Test cross product."""
        v1 = Vector2D(1.0, 0.0)
        v2 = Vector2D(0.0, 1.0)
        assert v1.cross(v2) == 1.0

    def test_distance_to(self):
        """Test distance calculation."""
        v1 = Vector2D(0.0, 0.0)
        v2 = Vector2D(3.0, 4.0)
        assert v1.distance_to(v2) == 5.0

    def test_distance_squared_to(self):
        """Test squared distance."""
        v1 = Vector2D(0.0, 0.0)
        v2 = Vector2D(3.0, 4.0)
        assert v1.distance_squared_to(v2) == 25.0

    def test_rotate(self):
        """Test vector rotation."""
        v = Vector2D(1.0, 0.0)
        rotated = v.rotate(math.pi / 2)  # 90 degrees CCW
        assert abs(rotated.x) < 0.0001
        assert abs(rotated.y - 1.0) < 0.0001

    def test_angle_property(self):
        """Test angle property."""
        v = Vector2D(1.0, 0.0)
        assert abs(v.angle) < 0.0001

    def test_lerp(self):
        """Test linear interpolation."""
        v1 = Vector2D(0.0, 0.0)
        v2 = Vector2D(10.0, 10.0)
        result = v1.lerp(v2, 0.5)
        assert result.x == 5.0
        assert result.y == 5.0

    def test_lerp_at_start(self):
        """Test lerp at t=0."""
        v1 = Vector2D(0.0, 0.0)
        v2 = Vector2D(10.0, 10.0)
        result = v1.lerp(v2, 0.0)
        assert result.x == 0.0
        assert result.y == 0.0

    def test_lerp_at_end(self):
        """Test lerp at t=1."""
        v1 = Vector2D(0.0, 0.0)
        v2 = Vector2D(10.0, 10.0)
        result = v1.lerp(v2, 1.0)
        assert result.x == 10.0
        assert result.y == 10.0

    def test_perpendicular(self):
        """Test perpendicular vector."""
        v = Vector2D(1.0, 0.0)
        perp = v.perpendicular
        assert perp.x == 0.0
        # y is 1.0 (90 degrees clockwise)
        assert perp.y == 1.0

    def test_from_angle(self):
        """Test creating from angle."""
        v = Vector2D.from_angle(0)
        assert abs(v.x - 1.0) < 0.0001
        assert abs(v.y) < 0.0001


class TestVectorDeterminism:
    """Test vector determinism for RL reproducibility."""

    def test_same_operations_same_result(self):
        """Test that same operations produce same results."""
        v1 = Vector2D(3.0, 4.0)
        v2 = Vector2D(1.0, 2.0)
        
        # Multiple times to ensure determinism
        for _ in range(10):
            result = (v1 + v2).length
            assert abs(result - 7.211) < 0.001

    def test_rotation_deterministic(self):
        """Test rotation is deterministic."""
        v = Vector2D(1.0, 0.0)
        
        results = []
        for _ in range(10):
            rotated = v.rotate(math.pi / 4)
            results.append((rotated.x, rotated.y))
        
        # All results should be identical
        assert all(abs(r[0] - results[0][0]) < 0.0001 for r in results)
        assert all(abs(r[1] - results[0][1]) < 0.0001 for r in results)

    def test_normalize_deterministic(self):
        """Test normalization is deterministic."""
        v = Vector2D(10.0, 20.0)
        
        results = []
        for _ in range(10):
            normalized = v.normalized
            results.append((normalized.x, normalized.y))
        
        # All results should be identical
        assert len(set(results)) == 1
