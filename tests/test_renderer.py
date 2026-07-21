"""Tests for rendering system."""

import numpy as np

from zbgym.rendering.debug_renderer import (
    DebugColor,
    DebugRenderer,
    DebugShape,
)


class TestDebugRenderer:
    """Tests for DebugRenderer."""

    def test_init(self):
        """Test renderer initialization."""
        renderer = DebugRenderer(width=640, height=480)
        assert renderer.width == 640
        assert renderer.height == 480

    def test_render_method_exists(self):
        """Test that render() method exists."""
        renderer = DebugRenderer()
        assert hasattr(renderer, "render")
        assert callable(renderer.render)

    def test_render_rgb_array(self):
        """Test render returns RGB array in rgb_array mode."""
        renderer = DebugRenderer(width=100, height=100)

        # Add a shape using add_shape
        shape = DebugShape(
            shape_type="circle",
            position=(50, 50),
            size=10,
            color=DebugColor.RED,
            layer=0,
        )
        renderer.add_shape(shape)

        # Render
        result = renderer.render(mode="rgb_array")

        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_render_human_mode(self):
        """Test render in human mode returns None."""
        renderer = DebugRenderer(width=100, height=100)
        shape = DebugShape(
            shape_type="circle",
            position=(50, 50),
            size=10,
            color=DebugColor.RED,
            layer=0,
        )
        renderer.add_shape(shape)

        result = renderer.render(mode="human")

        assert result is None

    def test_to_image(self):
        """Test to_image returns RGB array."""
        renderer = DebugRenderer(width=100, height=100)
        shape = DebugShape(
            shape_type="circle",
            position=(50, 50),
            size=10,
            color=DebugColor.RED,
            layer=0,
        )
        renderer.add_shape(shape)

        image = renderer.to_image()

        assert image.shape == (100, 100, 3)
        assert image.dtype == np.uint8

    def test_close(self):
        """Test close method."""
        renderer = DebugRenderer()
        renderer.close()

        # After close, buffer should be cleared
        assert len(renderer.shapes) == 0


class TestDebugShape:
    """Tests for DebugShape."""

    def test_create_circle(self):
        """Test circle shape creation."""
        shape = DebugShape(
            shape_type="circle",
            position=(100, 100),
            size=10,
            color=DebugColor.RED,
            layer=0,
        )

        assert shape.shape_type == "circle"
        assert shape.size == 10

    def test_create_line(self):
        """Test line shape creation."""
        shape = DebugShape(
            shape_type="line",
            position=(0, 0),
            end_position=(100, 100),
            size=2,
            color=DebugColor.GREEN,
            layer=0,
        )

        assert shape.shape_type == "line"
        assert shape.end_position is not None


class TestDebugColor:
    """Tests for DebugColor."""

    def test_red_color(self):
        """Test RED color."""
        color = DebugColor.RED
        assert color.r == 1.0
        assert color.g == 0.0
        assert color.b == 0.0

    def test_green_color(self):
        """Test GREEN color."""
        color = DebugColor.GREEN
        assert color.r == 0.0
        assert color.g == 1.0
        assert color.b == 0.0

    def test_blue_color(self):
        """Test BLUE color."""
        color = DebugColor.BLUE
        assert color.r == 0.0
        assert color.g == 0.0
        assert color.b == 1.0

    def test_to_tuple(self):
        """Test to_tuple conversion."""
        color = DebugColor.RED
        result = color.to_tuple()
        assert len(result) == 4  # RGBA
        assert all(0 <= v <= 1 for v in result)
