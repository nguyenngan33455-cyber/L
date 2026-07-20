"""Character plugin system for ZBGym."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from zbgym.plugins.base import Plugin, PluginMetadata, PluginRegistry
from zbgym.physics.vector import Vector2D
from zbgym.physics.body import DynamicBody
from zbgym.constants import MAX_HEALTH, MAX_SHIELD, MAX_ENERGY

if TYPE_CHECKING:
    from zbgym.engine.event_bus import EventBus


@dataclass
class CharacterStats:
    """Base stats for a character."""

    max_health: float = MAX_HEALTH
    max_shield: float = MAX_SHIELD
    max_energy: float = MAX_ENERGY
    move_speed: float = 300.0
    sprint_speed: float = 450.0
    jump_force: float = 400.0
    armor: float = 0.0  # damage reduction
    vision_range: float = 500.0

    # Combat stats
    base_damage: float = 10.0
    critical_chance: float = 0.05
    critical_multiplier: float = 1.5
    headshot_multiplier: float = 2.0


@dataclass
class Ability:
    """A character ability."""

    id: str
    name: str
    description: str
    cooldown: float = 5.0
    energy_cost: float = 0.0
    is_ultimate: bool = False

    # Behavior
    can_interrupt: bool = True
    channel_time: float = 0.0  # time to hold before activating


@dataclass
class CharacterConfig:
    """Configuration for a character type."""

    stats: CharacterStats = field(default_factory=CharacterStats)
    abilities: list[Ability] = field(default_factory=list)
    hitbox_radius: float = 16.0
    model_id: str = "default"
    animation_set: str = "default"


class Character(Plugin):
    """
    Character plugin base class.

    Characters are the playable entities in the arena.
    Each character type is a plugin that defines stats, abilities, and behaviors.
    """

    metadata: PluginMetadata
    config: CharacterConfig

    def __init__(
        self,
        character_id: str,
        team: str = "none",
        event_bus: EventBus | None = None,
        seed: int | None = None,
    ) -> None:
        """
        Initialize character.

        Args:
            character_id: Unique ID for this character instance
            team: Team identifier
            event_bus: Event bus for character events
            seed: Random seed for deterministic behavior
        """
        self.character_id = character_id
        self.team = team
        self.event_bus = event_bus

        # Deterministic RNG
        self._rng = random.Random(seed)

        # State
        self.health = self.config.stats.max_health
        self.shield = self.config.stats.max_shield
        self.energy = self.config.stats.max_energy

        self.is_alive = True
        self.is_stunned = False
        self.is_invisible = False

        # Position and movement
        self.position = Vector2D.zero()
        self.velocity = Vector2D.zero()
        self.facing_direction = Vector2D.right()

        # Combat state
        self.current_weapon: str | None = None
        self.ability_cooldowns: dict[str, float] = {}
        self.active_effects: list[str] = []

        # Physics body
        self.body = DynamicBody(
            id=character_id,
            position=self.position,
            radius=self.config.hitbox_radius,
            mass=1.0,
        )

        # Callbacks
        self._on_damage_taken: list[Callable[[float, str], None]] = []
        self._on_heal: list[Callable[[float], None]] = []
        self._on_death: list[Callable[[], None]] = []

    def initialize(self) -> None:
        """Initialize character."""
        self._reset_state()

    def shutdown(self) -> None:
        """Cleanup character."""
        pass

    def _reset_state(self) -> None:
        """Reset character to initial state."""
        self.health = self.config.stats.max_health
        self.shield = self.config.stats.max_shield
        self.energy = self.config.stats.max_energy
        self.is_alive = True
        self.is_stunned = False
        self.is_invisible = False
        self.ability_cooldowns.clear()
        self.active_effects.clear()

    def take_damage(
        self,
        damage: float,
        source_id: str,
        damage_type: str = "bullet",
        is_headshot: bool = False,
    ) -> float:
        """
        Apply damage to character.

        Args:
            damage: Base damage amount
            source_id: ID of damage source
            damage_type: Type of damage
            is_headshot: Whether damage was a headshot

        Returns:
            Actual damage dealt after shields/armor
        """
        if not self.is_alive:
            return 0.0

        # Apply armor reduction
        armor_reduction = self.config.stats.armor
        damage = damage * (1.0 - armor_reduction)

        # Apply headshot multiplier
        if is_headshot:
            damage *= self.config.stats.headshot_multiplier

        # Apply critical using seeded RNG
        if not is_headshot and self.config.stats.critical_chance > 0:
            if self._rng.random() < self.config.stats.critical_chance:
                damage *= self.config.stats.critical_multiplier

        # Damage shield first
        actual_damage = damage
        if self.shield > 0:
            shield_damage = min(self.shield, damage)
            self.shield -= shield_damage
            actual_damage -= shield_damage

        # Apply remaining to health
        if actual_damage > 0:
            self.health -= actual_damage

        # Check death
        if self.health <= 0:
            self.health = 0
            self.die(source_id)

        # Emit damage event
        if self.event_bus:
            self.event_bus.emit(
                "character_damage",
                character_id=self.character_id,
                damage=actual_damage,
                source_id=source_id,
                health_remaining=self.health,
            )

        # Call damage callbacks
        for callback in self._on_damage_taken:
            callback(actual_damage, source_id)

        return actual_damage

    def heal(self, amount: float) -> float:
        """
        Heal the character.

        Args:
            amount: Amount to heal

        Returns:
            Actual healing applied
        """
        if not self.is_alive:
            return 0.0

        old_health = self.health
        max_heal = self.config.stats.max_health - self.health
        actual_heal = min(amount, max_heal)

        self.health += actual_heal

        if actual_heal > 0:
            if self.event_bus:
                self.event_bus.emit(
                    "character_heal",
                    character_id=self.character_id,
                    amount=actual_heal,
                )

            for callback in self._on_heal:
                callback(actual_heal)

        return actual_heal

    def use_energy(self, amount: float) -> bool:
        """
        Use energy for abilities.

        Args:
            amount: Energy cost

        Returns:
            True if enough energy was available
        """
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False

    def can_use_ability(self, ability_id: str) -> bool:
        """Check if an ability can be used."""
        if not self.is_alive or self.is_stunned:
            return False

        # Check cooldown
        cooldown_remaining = self.ability_cooldowns.get(ability_id, 0.0)
        if cooldown_remaining > 0:
            return False

        # Find ability
        ability = self.get_ability(ability_id)
        if ability is None:
            return False

        # Check energy
        if self.energy < ability.energy_cost:
            return False

        return True

    def use_ability(self, ability_id: str) -> bool:
        """
        Attempt to use an ability.

        Args:
            ability_id: ID of ability to use

        Returns:
            True if ability was used successfully
        """
        if not self.can_use_ability(ability_id):
            return False

        ability = self.get_ability(ability_id)
        if ability is None:
            return False

        # Consume energy
        if ability.energy_cost > 0:
            self.use_energy(ability.energy_cost)

        # Set cooldown
        self.ability_cooldowns[ability_id] = ability.cooldown

        # Emit ability event
        if self.event_bus:
            self.event_bus.emit(
                "ability_use",
                character_id=self.character_id,
                ability_id=ability_id,
            )

        return True

    def update_abilities(self, dt: float) -> None:
        """Update ability cooldowns."""
        for ability_id in list(self.ability_cooldowns.keys()):
            self.ability_cooldowns[ability_id] = max(
                0.0, self.ability_cooldowns[ability_id] - dt
            )

    def die(self, killer_id: str) -> None:
        """Handle character death."""
        self.is_alive = False
        self.health = 0

        if self.event_bus:
            self.event_bus.emit(
                "character_death",
                character_id=self.character_id,
                killer_id=killer_id,
                position=self.position.to_dict(),
            )

        for callback in self._on_death:
            callback()

    def respawn(self, position: Vector2D) -> None:
        """Respawn character at position."""
        self.position = position
        self._reset_state()

    def get_ability(self, ability_id: str) -> Ability | None:
        """Get an ability by ID."""
        for ability in self.config.abilities:
            if ability.id == ability_id:
                return ability
        return None

    def get_stats(self) -> dict[str, Any]:
        """Get current character stats."""
        return {
            "health": self.health,
            "max_health": self.config.stats.max_health,
            "health_percent": self.health / self.config.stats.max_health,
            "shield": self.shield,
            "max_shield": self.config.stats.max_shield,
            "energy": self.energy,
            "max_energy": self.config.stats.max_energy,
            "is_alive": self.is_alive,
            "is_stunned": self.is_stunned,
            "position": self.position.to_dict(),
        }

    def on_damage_taken(self, callback: Callable[[float, str], None]) -> None:
        """Register damage taken callback."""
        self._on_damage_taken.append(callback)

    def on_heal(self, callback: Callable[[float], None]) -> None:
        """Register heal callback."""
        self._on_heal.append(callback)

    def on_death(self, callback: Callable[[], None]) -> None:
        """Register death callback."""
        self._on_death.append(callback)


# Character registry
character_registry = PluginRegistry[Character]()


def register_character(
    character_id: str,
    name: str,
    stats: CharacterStats,
    abilities: list[Ability] | None = None,
    **kwargs,
) -> type[Character]:
    """
    Decorator to register a character type.

    Usage:
        @register_character("soldier", "Soldier", CharacterStats(...))
        class SoldierCharacter(Character):
            pass
    """
    _config = CharacterConfig(
        stats=stats,
        abilities=abilities or [],
        **kwargs,
    )
    _metadata = PluginMetadata(
        id=character_id,
        name=name,
        description=kwargs.get("description", ""),
    )

    def decorator(cls: type[Character]) -> type[Character]:
        # Use type() to create class with proper scope
        RegisteredCharacter = type(
            f"Registered{cls.__name__}",
            (cls,),
            {
                "metadata": _metadata,
                "config": _config,
            },
        )

        character_registry.register(RegisteredCharacter, character_id)
        return cls

    return decorator


def create_character(
    character_id: str,
    instance_id: str,
    team: str = "none",
    **kwargs,
) -> Character | None:
    """
    Create a character instance.

    Args:
        character_id: Type of character to create
        instance_id: Unique ID for this instance
        team: Team identifier
        **kwargs: Additional arguments

    Returns:
        Character instance or None if not found
    """
    character_type = character_registry.get(character_id)
    if character_type is None:
        return None

    return character_type(character_id=instance_id, team=team, **kwargs)
