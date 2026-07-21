"""Movement system for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from zbgym.constants import (
    DEFAULT_DASH_SPEED,
    DEFAULT_FRICTION,
    DEFAULT_GRAVITY,
    DEFAULT_JUMP_FORCE,
    DEFAULT_MAX_SPEED,
)
from zbgym.physics.body import DynamicBody
from zbgym.physics.vector import Vector2D

if TYPE_CHECKING:
    from zbgym.engine.event_bus import EventBus


@dataclass
class MovementState:
    """Current movement state of a character."""

    is_grounded: bool = False
    is_jumping: bool = False
    is_dashing: bool = False
    is_flying: bool = False
    dash_direction: Vector2D | None = None
    dash_time_remaining: float = 0.0
    jump_time_remaining: float = 0.0
    coyote_time: float = 0.0
    jump_buffer_time: float = 0.0


@dataclass
class MovementConfig:
    """Configuration for movement system."""

    gravity: float = DEFAULT_GRAVITY
    max_speed: float = DEFAULT_MAX_SPEED
    acceleration: float = 2000.0
    deceleration: float = 1500.0
    friction: float = DEFAULT_FRICTION
    air_friction: float = 0.95
    air_control: float = 0.3

    # Jump
    jump_force: float = DEFAULT_JUMP_FORCE
    jump_duration: float = 0.3
    jump_cut_multiplier: float = 0.5
    coyote_time: float = 0.1
    jump_buffer_time: float = 0.1

    # Dash
    dash_speed: float = DEFAULT_DASH_SPEED
    dash_duration: float = 0.2
    dash_cooldown: float = 1.0
    dash_gravity_scale: float = 0.0

    # Wall
    wall_slide_speed: float = 100.0
    wall_jump_force: Vector2D = field(default_factory=lambda: Vector2D(300, -400))
    wall_stick_time: float = 0.1


class MovementSystem:
    """
    Handles character movement including walking, jumping, dashing.

    Provides:
    - Acceleration-based movement
    - Jump with coyote time and jump buffering
    - Dash with cooldown
    - Wall interactions
    """

    def __init__(
        self,
        config: MovementConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """
        Initialize movement system.

        Args:
            config: Movement configuration
            event_bus: Event bus for movement events
        """
        self.config = config or MovementConfig()
        self.event_bus = event_bus
        self._states: dict[str, MovementState] = {}
        self._cooldowns: dict[str, dict[str, float]] = {}

    def get_state(self, entity_id: str) -> MovementState:
        """Get or create movement state for an entity."""
        if entity_id not in self._states:
            self._states[entity_id] = MovementState()
        return self._states[entity_id]

    def get_cooldowns(self, entity_id: str) -> dict[str, float]:
        """Get or create cooldowns for an entity."""
        if entity_id not in self._cooldowns:
            self._cooldowns[entity_id] = {}
        return self._cooldowns[entity_id]

    def move(
        self,
        body: DynamicBody,
        direction: Vector2D,
        dt: float,
    ) -> None:
        """
        Apply movement input to a body.

        Args:
            body: Physics body to move
            direction: Movement direction (normalized)
            dt: Delta time
        """
        state = self.get_state(body.id)

        # Calculate acceleration
        if state.is_grounded:
            accel = self.config.acceleration
            friction = self.config.friction
        else:
            accel = self.config.acceleration * self.config.air_control
            friction = self.config.air_friction

        # Apply acceleration
        target_velocity = direction * self.config.max_speed
        current_speed = body.velocity.dot(direction)

        if direction.length_squared > 0:
            # Accelerate in direction
            if current_speed < self.config.max_speed:
                acceleration = accel * dt
                new_speed = min(current_speed + acceleration, self.config.max_speed)
                body.velocity += direction * (new_speed - current_speed)

        # Apply friction perpendicular to movement
        if direction.length_squared > 0:
            perpendicular = body.velocity - direction * body.velocity.dot(direction)
            body.velocity -= perpendicular * friction * dt

    def jump(
        self,
        body: DynamicBody,
        early_cut: bool = False,
    ) -> bool:
        """
        Attempt to make entity jump.

        Args:
            body: Physics body
            early_cut: If True, cut jump short (for variable jump height)

        Returns:
            True if jump was executed
        """
        state = self.get_state(body.id)
        cooldowns = self.get_cooldowns(body.id)

        # Check if can jump
        if state.is_jumping and not early_cut:
            return False

        can_jump = state.is_grounded or state.coyote_time > 0

        if early_cut and state.is_jumping:
            # Cut jump short
            state.is_jumping = False
            if body.velocity.y < 0:
                body.velocity.y *= self.config.jump_cut_multiplier
            return True

        if not can_jump:
            # Buffer jump for later
            state.jump_buffer_time = self.config.jump_buffer_time
            return False

        # Execute jump
        state.is_jumping = True
        state.jump_time_remaining = self.config.jump_duration
        state.coyote_time = 0
        body.velocity.y = -self.config.jump_force
        state.is_grounded = False

        return True

    def dash(
        self,
        body: DynamicBody,
        direction: Vector2D,
    ) -> bool:
        """
        Attempt to dash.

        Args:
            body: Physics body
            direction: Dash direction

        Returns:
            True if dash was executed
        """
        state = self.get_state(body.id)
        cooldowns = self.get_cooldowns(body.id)

        # Check cooldown
        dash_cooldown = cooldowns.get("dash", 0.0)
        if dash_cooldown > 0 or state.is_dashing:
            return False

        # Normalize direction
        if direction.length_squared > 0:
            direction = direction.normalized
        else:
            direction = Vector2D.right()

        # Start dash
        state.is_dashing = True
        state.dash_direction = direction
        state.dash_time_remaining = self.config.dash_duration

        # Set dash velocity
        body.velocity = direction * self.config.dash_speed

        # Disable gravity during dash
        body.gravity_scale = self.config.dash_gravity_scale

        # Set cooldown
        cooldowns["dash"] = self.config.dash_cooldown

        return True

    def update(self, body: DynamicBody, dt: float) -> None:
        """
        Update movement state for an entity.

        Args:
            body: Physics body to update
            dt: Delta time
        """
        state = self.get_state(body.id)
        cooldowns = self.get_cooldowns(body.id)

        # Update cooldowns
        for cooldown_name in list(cooldowns.keys()):
            cooldowns[cooldown_name] = max(0, cooldowns[cooldown_name] - dt)

        # Update dash
        if state.is_dashing:
            state.dash_time_remaining -= dt
            if state.dash_time_remaining <= 0:
                state.is_dashing = False
                state.dash_direction = None
                body.gravity_scale = 1.0
                # Dampen velocity after dash
                body.velocity *= 0.5

        # Update jump
        if state.is_jumping:
            state.jump_time_remaining -= dt
            if state.jump_time_remaining <= 0:
                state.is_jumping = False

        # Update coyote time
        if state.is_grounded:
            state.coyote_time = self.config.coyote_time
        else:
            state.coyote_time = max(0, state.coyote_time - dt)

        # Check jump buffer
        if state.jump_buffer_time > 0:
            state.jump_buffer_time -= dt
            if state.is_grounded or state.coyote_time > 0:
                self.jump(body)
                state.jump_buffer_time = 0

        # Apply gravity when not dashing
        if not state.is_dashing and body.use_gravity:
            gravity = Vector2D(0, self.config.gravity * body.gravity_scale)
            body.velocity += gravity * dt

        # Apply friction
        if state.is_grounded and not state.is_dashing:
            body.velocity.x *= self.config.friction

        # Clamp velocity
        if body.velocity.length > self.config.max_speed and not state.is_dashing:
            body.velocity = body.velocity.normalized * self.config.max_speed

    def set_grounded(self, entity_id: str, grounded: bool) -> None:
        """Set grounded state for an entity."""
        state = self.get_state(entity_id)
        was_grounded = state.is_grounded
        state.is_grounded = grounded

        if grounded and not was_grounded:
            # Just landed
            state.is_jumping = False

    def reset(self, entity_id: str) -> None:
        """Reset movement state for an entity."""
        if entity_id in self._states:
            self._states[entity_id] = MovementState()
        if entity_id in self._cooldowns:
            self._cooldowns[entity_id] = {}

    def reset_all(self) -> None:
        """Reset all movement states."""
        self._states.clear()
        self._cooldowns.clear()

    def get_horizontal_speed(self, entity_id: str) -> float:
        """Get horizontal speed for an entity."""
        state = self.get_state(entity_id)
        return abs(state.dash_direction.x * self.config.dash_speed) if state.is_dashing else 0.0

    def is_moving(self, entity_id: str) -> bool:
        """Check if entity is actively moving."""
        state = self.get_state(entity_id)
        return state.is_dashing or state.is_jumping
