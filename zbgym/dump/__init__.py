"""Dump module - Dynamic data extraction from Zooba dump.cs.

Usage:
    from zbgym.dump import load_from_dump
    
    # Load all game data from dump.cs
    gen = load_from_dump('path/to/dump.cs')
    
    # Access generated plugins
    from zbgym.plugins.character import character_registry
    
    for char_id in character_registry.list_plugins():
        print(f"Character: {char_id}")
"""

from zbgym.dump.parser import DumpParser, CharacterInfo, WeaponInfo, SkillInfo
from zbgym.dump.generator import (
    DynamicPluginGenerator,
    get_generator,
    load_from_dump,
)

# Import registries for easy access
from zbgym.plugins.character import character_registry
from zbgym.plugins.weapon import weapon_registry
from zbgym.plugins.skill import skill_registry

__all__ = [
    'DumpParser',
    'CharacterInfo',
    'WeaponInfo',
    'SkillInfo',
    'DynamicPluginGenerator',
    'get_generator',
    'load_from_dump',
    'character_registry',
    'weapon_registry',
    'skill_registry',
]
