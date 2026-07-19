"""Plugin system for ZBGym."""

from zbgym.plugins.base import Plugin, PluginMetadata, PluginRegistry
from zbgym.plugins.character import (
    Character,
    CharacterStats,
    CharacterConfig,
    Ability,
    character_registry,
    register_character,
    create_character,
)
from zbgym.plugins.weapon import (
    Weapon,
    WeaponStats,
    WeaponConfig,
    weapon_registry,
    register_weapon,
    create_weapon,
)
from zbgym.plugins.skill import (
    Skill,
    SkillConfig,
    skill_registry,
    register_skill,
    create_skill,
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
