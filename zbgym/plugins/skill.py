"""Skill plugin system for ZBGym."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from zbgym.constants import SkillType
from zbgym.physics.vector import Vector2D
from zbgym.plugins.base import Plugin, PluginMetadata, PluginRegistry

if TYPE_CHECKING:
    from zbgym.engine.event_bus import EventBus
    from zbgym.plugins.character import Character


@dataclass
class SkillConfig:
    """Configuration for a skill."""

    skill_type: SkillType = SkillType.PROJECTILE
    cooldown: float = 5.0
    energy_cost: float = 20.0
    cast_time: float = 0.0  # time to channel before activating
    channel_duration: float = 0.0  # time to hold

    # Range and area
    range: float = 500.0
    area_radius: float = 0.0

    # Effects
    damage: float = 0.0
    healing: float = 0.0
    shield_amount: float = 0.0
    speed_modifier: float = 1.0
    duration: float = 0.0


class Skill(Plugin):
    """
    Skill plugin base class.

    Skills are abilities that characters can use.
    Each skill type is a plugin that defines behavior and effects.
    """

    metadata: PluginMetadata
    config: SkillConfig

    def __init__(
        self,
        owner: Character | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """
        Initialize skill.

        Args:
            owner: Character using this skill
            event_bus: Event bus for skill events
        """
        self.owner = owner
        self.event_bus = event_bus

        # State
        self.cooldown_remaining = 0.0
        self.is_active = False
        self.active_time = 0.0
        self.is_channeling = False
        self.channel_time = 0.0

    def initialize(self) -> None:
        """Initialize skill."""
        self._reset_state()

    def shutdown(self) -> None:
        """Cleanup skill."""

    def _reset_state(self) -> None:
        """Reset skill state."""
        self.cooldown_remaining = 0.0
        self.is_active = False
        self.active_time = 0.0
        self.is_channeling = False
        self.channel_time = 0.0

    def can_use(self, target: Vector2D | None = None) -> bool:
        """
        Check if skill can be used.

        Args:
            target: Optional target position

        Returns:
            True if skill can be used
        """
        if self.owner is None:
            return False

        if not self.owner.is_alive or self.owner.is_stunned:
            return False

        if self.cooldown_remaining > 0:
            return False

        if self.owner.energy < self.config.energy_cost:
            return False

        # Check range
        if target is not None and self.config.range > 0:
            distance = self.owner.position.distance_to(target)
            if distance > self.config.range:
                return False

        return True

    def use(self, target: Vector2D | None = None) -> bool:
        """
        Use the skill.

        Args:
            target: Optional target position

        Returns:
            True if skill was used successfully
        """
        if not self.can_use(target):
            return False

        # Consume energy
        if self.config.energy_cost > 0:
            self.owner.use_energy(self.config.energy_cost)

        # Handle cast time
        if self.config.cast_time > 0:
            self.is_channeling = True
            self.channel_time = self.config.cast_time
            return True

        # Execute skill
        return self._execute(target)

    def _execute(self, target: Vector2D | None) -> bool:
        """Execute the skill effect."""
        # Set cooldown
        self.cooldown_remaining = self.config.cooldown

        # Activate skill
        self.is_active = True
        self.active_time = 0.0

        # Apply effects
        self._apply_effects(target)

        # Emit skill event
        if self.event_bus:
            self.event_bus.emit(
                "skill_use",
                skill_id=self.metadata.id,
                owner_id=self.owner.character_id if self.owner else None,
                target=target.to_dict() if target else None,
            )

        return True

    @abstractmethod
    def _apply_effects(self, target: Vector2D | None) -> None:
        """Apply the skill effects."""

    def update(self, dt: float) -> None:
        """Update skill state."""
        # Update cooldown
        if self.cooldown_remaining > 0:
            self.cooldown_remaining = max(0, self.cooldown_remaining - dt)

        # Update channeling
        if self.is_channeling:
            self.channel_time -= dt
            if self.channel_time <= 0:
                self.is_channeling = False
                self._execute(None)

        # Update active duration
        if self.is_active:
            self.active_time += dt
            if self.config.duration > 0 and self.active_time >= self.config.duration:
                self._on_end()

    def _on_end(self) -> None:
        """Called when skill effect ends."""
        self.is_active = False
        self.active_time = 0.0

    def cancel(self) -> None:
        """Cancel the skill."""
        self.is_channeling = False
        self.is_active = False
        self.active_time = 0.0


# Skill registry
skill_registry = PluginRegistry[Skill]()


def register_skill(
    skill_id: str,
    name: str,
    skill_type: SkillType,
    config: SkillConfig,
    **kwargs,
) -> type[Skill]:
    """
    Decorator to register a skill type.

    Usage:
        @register_skill("heal", "Heal", SkillType.HEAL, SkillConfig(...))
        class HealSkill(Skill):
            pass
    """
    _config = config
    _metadata = PluginMetadata(
        id=skill_id,
        name=name,
        description=kwargs.get("description", ""),
    )

    def decorator(cls: type[Skill]) -> type[Skill]:
        # Use type() to create class with proper scope
        RegisteredSkill = type(
            f"Registered{cls.__name__}",
            (cls,),
            {
                "metadata": _metadata,
                "config": _config,
            },
        )

        skill_registry.register(RegisteredSkill, skill_id)
        return cls

    return decorator


def create_skill(
    skill_id: str,
    owner: Character | None = None,
    **kwargs,
) -> Skill | None:
    """
    Create a skill instance.

    Args:
        skill_id: Type of skill to create
        owner: Character using this skill
        **kwargs: Additional arguments

    Returns:
        Skill instance or None if not found
    """
    skill_type = skill_registry.get(skill_id)
    if skill_type is None:
        return None

    return skill_type(owner=owner, **kwargs)


# Pre-register default skills


@register_skill(
    "heal",
    "Healing Surge",
    SkillType.HEAL,
    SkillConfig(
        cooldown=15.0,
        energy_cost=30.0,
        healing=50.0,
        cast_time=0.5,
    ),
)
class HealSkill(Skill):
    """Heal the owner."""

    def _apply_effects(self, target: Vector2D | None) -> None:
        if self.owner:
            self.owner.heal(self.config.healing)


@register_skill(
    "shield",
    "Energy Shield",
    SkillType.SHIELD,
    SkillConfig(
        cooldown=20.0,
        energy_cost=40.0,
        shield_amount=50.0,
        duration=5.0,
    ),
)
class ShieldSkill(Skill):
    """Grant temporary shield."""

    def _apply_effects(self, target: Vector2D | None) -> None:
        if self.owner:
            self.owner.shield += self.config.shield_amount


@register_skill(
    "speed_boost",
    "Speed Boost",
    SkillType.BUFF,
    SkillConfig(
        cooldown=30.0,
        energy_cost=20.0,
        speed_modifier=1.5,
        duration=5.0,
    ),
)
class SpeedBoostSkill(Skill):
    """Increase movement speed."""

    def _apply_effects(self, target: Vector2D | None) -> None:
        # Speed boost would modify character stats
        pass


@register_skill(
    "dash",
    "Combat Dash",
    SkillType.DASH,
    SkillConfig(
        cooldown=3.0,
        energy_cost=10.0,
        range=300.0,
    ),
)
class DashSkill(Skill):
    """Dash in target direction."""

    def _apply_effects(self, target: Vector2D | None) -> None:
        if self.owner and target is not None:
            direction = (target - self.owner.position).normalized
            distance = min(self.config.range, target.distance_to(self.owner.position))
            self.owner.position = self.owner.position + direction * distance


@register_skill(
    "grenade",
    "Frag Grenade",
    SkillType.AOE,
    SkillConfig(
        cooldown=10.0,
        energy_cost=25.0,
        range=500.0,
        area_radius=200.0,
        damage=40.0,
    ),
)
class GrenadeSkill(Skill):
    """Area damage projectile."""

    def _apply_effects(self, target: Vector2D | None) -> None:
        # Would spawn an explosive projectile
        pass


@register_skill(
    "ultimate",
    "Ultimate Ability",
    SkillType.ULTIMATE,
    SkillConfig(
        cooldown=120.0,
        energy_cost=100.0,
        duration=10.0,
        damage=100.0,
    ),
)
class UltimateSkill(Skill):
    """Powerful ultimate ability."""

    def _apply_effects(self, target: Vector2D | None) -> None:
        pass
