"""Plugin system for ZBGym."""

from zbgym.plugins.base import Plugin, PluginMetadata, PluginRegistry
from zbgym.plugins.character import (
    Ability,
    Character,
    CharacterConfig,
    CharacterStats,
    character_registry,
    create_character,
    load_default_characters,
    register_character,
)
from zbgym.plugins.skill import (
    Skill,
    SkillConfig,
    create_skill,
    register_skill,
    skill_registry,
)
from zbgym.plugins.weapon import (
    Weapon,
    WeaponConfig,
    WeaponStats,
    create_weapon,
    register_weapon,
    weapon_registry,
)

__all__ = [
    # Base
    "Plugin",
    "PluginMetadata",
    "PluginRegistry",
    # Character
    "Character",
    "CharacterStats",
    "CharacterConfig",
    "Ability",
    "character_registry",
    "register_character",
    "create_character",
    "load_default_characters",
    # Weapon
    "Weapon",
    "WeaponStats",
    "WeaponConfig",
    "weapon_registry",
    "register_weapon",
    "create_weapon",
    # Skill
    "Skill",
    "SkillConfig",
    "skill_registry",
    "register_skill",
    "create_skill",
]
