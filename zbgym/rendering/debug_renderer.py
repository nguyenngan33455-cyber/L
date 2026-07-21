"""Debug Visualization for ZBGym.

Renders hitboxes, collision, projectiles, vision, bushes, loot, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

import numpy as np

from zbgym.physics.body import PhysicsBody
from zbgym.physics.vector import Vector2D

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArena


class DebugLayer(Enum):
    """Debug visualization layers."""

    HITBOXES = auto()
    COLLISION = auto()
    PROJECTILES = auto()
    VISION = auto()
    BUSHES = auto()
    LOOT = auto()
    SAFE_ZONE = auto()
    REWARDS = auto()
    AGENT_DECISIONS = auto()
    POLICY_OUTPUTS = auto()
    NAVIGATION = auto()
    DAMAGE_NUMBERS = auto()
    COOLDOWNS = auto()


@dataclass
class DebugColor:
    """RGBA color for debugging."""

    r: float = 1.0
    g: float = 1.0
    b: float = 1.0
    a: float = 1.0

    def to_tuple(self) -> tuple[float, float, float, float]:
        return (self.r, self.g, self.b, self.a)


# Predefined colors (as class attributes)
DebugColor.RED = DebugColor(1.0, 0.0, 0.0)
DebugColor.GREEN = DebugColor(0.0, 1.0, 0.0)
DebugColor.BLUE = DebugColor(0.0, 0.0, 1.0)
DebugColor.YELLOW = DebugColor(1.0, 1.0, 0.0)
DebugColor.CYAN = DebugColor(0.0, 1.0, 1.0)
DebugColor.MAGENTA = DebugColor(1.0, 0.0, 1.0)
DebugColor.WHITE = DebugColor(1.0, 1.0, 1.0)
DebugColor.GRAY = DebugColor(0.5, 0.5, 0.5)
DebugColor.ORANGE = DebugColor(1.0, 0.5, 0.0)


@dataclass
class DebugShape:
    """A debug shape to render."""

    shape_type: str  # "circle", "rectangle", "line", "point", "arc", "text"
    position: Vector2D = field(default_factory=Vector2D.zero)
    size: float = 0.0
    size2: float = 0.0  # For rectangles: width, height
    color: DebugColor = field(default_factory=DebugColor)
    data: Any = None  # Additional data (text, direction, etc.)
    layer: DebugLayer = DebugLayer.HITBOXES

    # For lines
    end_position: Vector2D | None = None
    direction: Vector2D | None = None

    # For arcs
    start_angle: float = 0.0
    end_angle: float = 0.0


class DebugRenderer:
    """
    Debug renderer for ZBGym.

    Renders various debug information on top of the game state.
    """

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        scale: float = 1.0,
    ) -> None:
        """
        Initialize debug renderer.

        Args:
            width: Canvas width
            height: Canvas height
            scale: Scale factor for rendering
        """
        self.width = width
        self.height = height
        self.scale = scale

        # Debug shapes to render
        self.shapes: list[DebugShape] = []

        # Active layers
        self.active_layers: set[DebugLayer] = {
            DebugLayer.HITBOXES,
            DebugLayer.SAFE_ZONE,
        }

        # Agent color mapping
        self.agent_colors: dict[str, DebugColor] = {}

        # Render buffer
        self._render_buffer: np.ndarray | None = None

    @classmethod
    def from_env(cls, env: BattleArena, scale: float = 1.0) -> DebugRenderer:
        """
        Create a DebugRenderer from an environment.

        Args:
            env: BattleArena environment to render
            scale: Scale factor for rendering

        Returns:
            DebugRenderer configured for the environment
        """
        width = int(env.config.config.arena_width)
        height = int(env.config.config.arena_height)
        return cls(width=width, height=height, scale=scale)

    def add_shape(self, shape: DebugShape) -> None:
        """Add a shape to render."""
        self.shapes.append(shape)

    def clear(self) -> None:
        """Clear all shapes."""
        self.shapes.clear()

    def enable_layer(self, layer: DebugLayer) -> None:
        """Enable a debug layer."""
        self.active_layers.add(layer)

    def disable_layer(self, layer: DebugLayer) -> None:
        """Disable a debug layer."""
        self.active_layers.discard(layer)

    def toggle_layer(self, layer: DebugLayer) -> None:
        """Toggle a debug layer."""
        if layer in self.active_layers:
            self.active_layers.discard(layer)
        else:
            self.active_layers.add(layer)

    def get_agent_color(self, agent_id: str) -> DebugColor:
        """Get or create a color for an agent."""
        if agent_id not in self.agent_colors:
            # Generate deterministic color from agent_id
            hash_val = hash(agent_id)
            r = ((hash_val >> 16) & 0xFF) / 255.0
            g = ((hash_val >> 8) & 0xFF) / 255.0
            b = (hash_val & 0xFF) / 255.0
            self.agent_colors[agent_id] = DebugColor(r, g, b)
        return self.agent_colors[agent_id]

    def render_hitbox(self, body: PhysicsBody, color: DebugColor | None = None) -> None:
        """Render a physics body hitbox."""
        if DebugLayer.HITBOXES not in self.active_layers:
            return

        self.add_shape(
            DebugShape(
                shape_type="circle",
                position=body.position,
                size=body.radius,
                color=color or DebugColor.YELLOW,
                layer=DebugLayer.HITBOXES,
            )
        )

    def render_collision(
        self, point: Vector2D, normal: Vector2D, color: DebugColor = DebugColor.RED
    ) -> None:
        """Render collision point and normal."""
        if DebugLayer.COLLISION not in self.active_layers:
            return

        # Collision point
        self.add_shape(
            DebugShape(
                shape_type="point",
                position=point,
                color=color,
                layer=DebugLayer.COLLISION,
            )
        )

        # Normal line
        normal_end = point + normal * 30.0
        self.add_shape(
            DebugShape(
                shape_type="line",
                position=point,
                end_position=normal_end,
                color=color,
                layer=DebugLayer.COLLISION,
            )
        )

    def render_projectile(
        self,
        position: Vector2D,
        velocity: Vector2D,
        owner_id: str | None = None,
        color: DebugColor | None = None,
    ) -> None:
        """Render a projectile."""
        if DebugLayer.PROJECTILES not in self.active_layers:
            return

        proj_color = color or self.get_agent_color(owner_id or "unknown")

        # Projectile body
        self.add_shape(
            DebugShape(
                shape_type="circle",
                position=position,
                size=4.0,
                color=proj_color,
                layer=DebugLayer.PROJECTILES,
            )
        )

        # Velocity direction
        if velocity.length_squared > 0:
            vel_normalized = velocity.normalized
            trail_end = position - vel_normalized * 20.0
            self.add_shape(
                DebugShape(
                    shape_type="line",
                    position=position,
                    end_position=trail_end,
                    color=DebugColor(
                        *proj_color.rgb if hasattr(proj_color, "rgb") else (1.0, 1.0, 1.0), 0.5
                    ),
                    layer=DebugLayer.PROJECTILES,
                )
            )

    def render_vision(
        self,
        position: Vector2D,
        direction: Vector2D,
        range: float,
        fov: float = 60.0,
        color: DebugColor | None = None,
    ) -> None:
        """Render vision cone."""
        if DebugLayer.VISION not in self.active_layers:
            return

        # Convert FOV to radians
        fov_rad = np.radians(fov)

        # Calculate arc endpoints
        half_fov = fov_rad / 2
        angle = direction.angle

        start_angle = angle - half_fov
        end_angle = angle + half_fov

        self.add_shape(
            DebugShape(
                shape_type="arc",
                position=position,
                size=range,
                start_angle=start_angle,
                end_angle=end_angle,
                color=color or DebugColor.CYAN,
                layer=DebugLayer.VISION,
            )
        )

    def render_safe_zone(
        self,
        center: Vector2D,
        radius: float,
        danger_radius: float | None = None,
        safe_color: DebugColor = DebugColor.GREEN,
        danger_color: DebugColor = DebugColor.RED,
    ) -> None:
        """Render safe zone and danger zone."""
        if DebugLayer.SAFE_ZONE not in self.active_layers:
            return

        # Safe zone
        self.add_shape(
            DebugShape(
                shape_type="circle",
                position=center,
                size=radius,
                color=DebugColor(safe_color.r, safe_color.g, safe_color.b, 0.3),
                layer=DebugLayer.SAFE_ZONE,
            )
        )

        # Danger zone
        if danger_radius:
            self.add_shape(
                DebugShape(
                    shape_type="circle",
                    position=center,
                    size=danger_radius,
                    color=DebugColor(danger_color.r, danger_color.g, danger_color.b, 0.3),
                    layer=DebugLayer.SAFE_ZONE,
                )
            )

    def render_bush(self, position: Vector2D, size: float, is_occupied: bool = False) -> None:
        """Render a bush."""
        if DebugLayer.BUSHES not in self.active_layers:
            return

        color = DebugColor.GREEN if not is_occupied else DebugColor.ORANGE
        self.add_shape(
            DebugShape(
                shape_type="circle",
                position=position,
                size=size,
                color=DebugColor(color.r, color.g, color.b, 0.5),
                layer=DebugLayer.BUSHES,
            )
        )

    def render_loot(
        self,
        position: Vector2D,
        loot_type: str,
        rarity: str = "common",
    ) -> None:
        """Render loot item."""
        if DebugLayer.LOOT not in self.active_layers:
            return

        rarity_colors = {
            "common": DebugColor.GRAY,
            "rare": DebugColor.BLUE,
            "epic": DebugColor.MAGENTA,
            "legendary": DebugColor.ORANGE,
        }

        color = rarity_colors.get(rarity, DebugColor.WHITE)
        self.add_shape(
            DebugShape(
                shape_type="rectangle",
                position=position,
                size=12.0,
                size2=12.0,
                color=color,
                data=loot_type,
                layer=DebugLayer.LOOT,
            )
        )

    def render_reward(
        self,
        position: Vector2D,
        reward_value: float,
        reward_type: str,
    ) -> None:
        """Render reward indicator."""
        if DebugLayer.REWARDS not in self.active_layers:
            return

        color = DebugColor.GREEN if reward_value >= 0 else DebugColor.RED
        self.add_shape(
            DebugShape(
                shape_type="text",
                position=position,
                color=color,
                data=f"{reward_type}: {reward_value:.2f}",
                layer=DebugLayer.REWARDS,
            )
        )

    def render_agent_decision(
        self,
        agent_id: str,
        position: Vector2D,
        action_type: str,
        action_value: Any,
    ) -> None:
        """Render agent decision."""
        if DebugLayer.AGENT_DECISIONS not in self.active_layers:
            return

        color = self.get_agent_color(agent_id)
        self.add_shape(
            DebugShape(
                shape_type="text",
                position=position + Vector2D(0, 30),
                color=color,
                data=f"{agent_id}: {action_type}",
                layer=DebugLayer.AGENT_DECISIONS,
            )
        )

    def render_policy_output(
        self,
        position: Vector2D,
        q_values: dict[str, float],
        chosen_action: str,
    ) -> None:
        """Render policy output (Q-values, probabilities)."""
        if DebugLayer.POLICY_OUTPUTS not in self.active_layers:
            return

        text_lines = [f"Q-values: {', '.join(f'{k}: {v:.2f}' for k, v in q_values.items())}"]
        text_lines.append(f"Action: {chosen_action}")

        self.add_shape(
            DebugShape(
                shape_type="text",
                position=position + Vector2D(50, 0),
                color=DebugColor.WHITE,
                data="\n".join(text_lines),
                layer=DebugLayer.POLICY_OUTPUTS,
            )
        )

    def render_cooldown(
        self,
        position: Vector2D,
        ability_id: str,
        cooldown_remaining: float,
        cooldown_total: float,
    ) -> None:
        """Render cooldown indicator."""
        if DebugLayer.COOLDOWNS not in self.active_layers:
            return

        progress = 1.0 - (cooldown_remaining / cooldown_total) if cooldown_total > 0 else 1.0

        self.add_shape(
            DebugShape(
                shape_type="text",
                position=position + Vector2D(-20, -20),
                color=DebugColor.YELLOW if progress >= 1.0 else DebugColor.GRAY,
                data=f"{ability_id}: {cooldown_remaining:.1f}s",
                layer=DebugLayer.COOLDOWNS,
            )
        )

    def render_damage_number(
        self,
        position: Vector2D,
        damage: float,
        is_critical: bool = False,
        is_headshot: bool = False,
    ) -> None:
        """Render damage number."""
        if DebugLayer.DAMAGE_NUMBERS not in self.active_layers:
            return

        prefix = ""
        if is_headshot:
            prefix = "HS! "
        elif is_critical:
            prefix = "CRIT! "

        color = DebugColor.RED
        if is_critical:
            color = DebugColor.ORANGE
        if is_headshot:
            color = DebugColor.MAGENTA

        self.add_shape(
            DebugShape(
                shape_type="text",
                position=position,
                color=color,
                data=f"{prefix}{damage:.0f}",
                layer=DebugLayer.DAMAGE_NUMBERS,
            )
        )

    def render_from_env(self, env: BattleArena) -> None:
        """
        Render debug info from an environment.

        Args:
            env: BattleArena environment
        """
        state = env.get_state()

        # Render characters
        for char_id, char in state.characters.items():
            # Hitbox
            self.render_hitbox(char.body, self.get_agent_color(char_id))

            # Vision
            if hasattr(char, "facing_direction"):
                self.render_vision(
                    char.position,
                    char.facing_direction,
                    char.config.stats.vision_range,
                )

        # Render safe zone
        self.render_safe_zone(
            state.safe_zone_center,
            state.safe_zone_radius,
            state.danger_zone_radius,
        )

    def get_render_buffer(self) -> np.ndarray:
        """
        Get the render buffer as numpy array.

        Returns:
            RGBA image as numpy array
        """
        if self._render_buffer is None:
            self._render_buffer = np.zeros(
                (self.height, self.width, 4),
                dtype=np.float32,
            )

        # Clear buffer
        self._render_buffer.fill(0)

        # Render shapes
        for shape in self.shapes:
            if shape.layer not in self.active_layers:
                continue

            self._render_shape(shape)

        return self._render_buffer

    def _render_shape(self, shape: DebugShape) -> None:
        """Render a single shape to the buffer."""
        # Scale position to pixel coordinates
        px = int(shape.position.x * self.scale)
        py = int(shape.position.y * self.scale)

        if shape.shape_type == "circle":
            self._render_circle(px, py, int(shape.size * self.scale), shape.color)
        elif shape.shape_type == "line":
            if shape.end_position:
                ex = int(shape.end_position.x * self.scale)
                ey = int(shape.end_position.y * self.scale)
                self._render_line(px, py, ex, ey, shape.color)
        elif shape.shape_type == "rectangle":
            self._render_rectangle(
                px,
                py,
                int(shape.size * self.scale),
                int(shape.size2 * self.scale),
                shape.color,
            )
        elif shape.shape_type == "point":
            self._render_point(px, py, shape.color)

    def _render_circle(self, cx: int, cy: int, radius: int, color: DebugColor) -> None:
        """Render a circle."""
        if radius <= 0:
            return

        for y in range(max(0, cy - radius), min(self.height, cy + radius + 1)):
            for x in range(max(0, cx - radius), min(self.width, cx + radius + 1)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= radius**2:
                    self._render_buffer[y, x] = color.to_tuple()

    def _render_line(self, x1: int, y1: int, x2: int, y2: int, color: DebugColor) -> None:
        """Render a line using Bresenham's algorithm."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            if 0 <= x1 < self.width and 0 <= y1 < self.height:
                self._render_buffer[y1, x1] = color.to_tuple()

            if x1 == x2 and y1 == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def _render_rectangle(self, x: int, y: int, w: int, h: int, color: DebugColor) -> None:
        """Render a rectangle."""
        for dy in range(h):
            for dx in range(w):
                px, py = x + dx, y + dy
                if 0 <= px < self.width and 0 <= py < self.height:
                    self._render_buffer[py, px] = color.to_tuple()

    def _render_point(self, x: int, y: int, color: DebugColor) -> None:
        """Render a point."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self._render_buffer[y, x] = color.to_tuple()

    def to_image(self) -> np.ndarray:
        """
        Convert render buffer to RGB image.

        Returns:
            RGB image as numpy array (uint8)
        """
        buffer = self.get_render_buffer()
        # Convert RGBA to RGB
        rgb = buffer[:, :, :3] * 255
        return rgb.astype(np.uint8)

    def render(self, mode: str = "human") -> np.ndarray | None:
        """
        Render the current frame.

        Args:
            mode: Rendering mode ("human" or "rgb_array")

        Returns:
            RGB array if mode="rgb_array", None otherwise
        """
        image = self.to_image()

        if mode == "human":
            # For human mode, caller should handle display
            # Just return None as per gym convention
            return None

        return image

    def close(self) -> None:
        """Close the renderer and cleanup resources."""
        self.clear()
