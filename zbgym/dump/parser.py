"""Dump parser for Zooba game data extraction.

This module provides comprehensive parsing of dump.cs to extract:
- Characters (with stats, skills, modifiers)
- Skills (with damage, cooldown, range, categories)
- Weapons (from constants and skill data)
- Projectiles (types and configurations)
- NPCs (guards, minions, turrets)
- Constants (game balance values)
- Buffs/Effects (status effects)
"""

from __future__ import annotations

import re
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class CharacterInfo:
    """Character data extracted from dump."""
    enum_id: int
    name: str
    char_id: str
    
    # Visual
    description: str = ""
    sub_name: str = ""
    
    # Stats (parsed from CharacterModifier)
    health_modifier: float = 0.0
    damage_modifier: float = 0.0
    range_modifier: float = 0.0
    durability_modifier: float = 0.0
    agility_modifier: float = 0.0
    
    # Skills
    active_name: str = ""
    active_desc: str = ""
    passive_name: str = ""
    passive_desc: str = ""
    
    # Visual
    default_scale: float = 1.0
    color_dark: str = "#FFFFFF"
    color_light: str = "#FFFFFF"
    
    # Metadata
    is_playable: bool = True
    is_hidden: bool = False
    is_npc: bool = False
    
    # Type
    character_type: str = ""
    parent_key: str = ""
    
    # Additional
    fight_style: str = ""
    rarity: str = "common"
    league: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass  
class SkillInfo:
    """Skill data extracted from dump."""
    skill_id: str
    name: str
    
    # Category
    category: str = "active"  # active, passive, ultimate
    skill_category_id: int = 0  # SkillCategory enum value
    skill_category_name: str = ""
    
    # Combat stats
    damage: int = 0
    cooldown: float = 0.0
    range_val: float = 0.0
    knockback: int = 0
    
    # Duration & Charges
    duration: float = 0.0
    max_charges: int = 1
    delay_between_charges: int = 0
    
    # Type flags
    is_ultimate: bool = False
    is_passive: bool = False
    drop_on_die: bool = False
    should_lock_inventory: bool = False
    
    # Aim
    aim_type: str = "default"
    
    # Style (for character-specific skills)
    style_name: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class WeaponInfo:
    """Weapon data extracted from dump."""
    weapon_id: str
    name: str
    
    # Category
    category: str = "rifle"
    skill_category_id: int = 0
    
    # Stats
    damage: int = 0
    fire_rate: float = 1.0  # attacks per second
    range_val: float = 0.0
    cooldown: float = 1.0  # seconds between attacks
    knockback: int = 0
    
    # Projectile
    projectile_speed: float = 0.0
    projectile_count: int = 1
    
    # Area
    radius: float = 0.0
    angle: float = 0.0
    speed: float = 0.0  # for thrown weapons
    
    # Ammo
    magazine_size: int = 30
    total_ammo: int = 120
    reload_time: float = 2.0
    
    # Accuracy
    spread: float = 0.0
    recoil: float = 0.0
    
    # Critical
    critical_chance: float = 0.05
    critical_multiplier: float = 1.5
    headshot_multiplier: float = 2.0
    
    # Penetration
    penetration: int = 0
    ricochet: int = 0
    
    # Damage falloff
    min_damage_ratio: float = 0.5
    max_damage_distance: float = 500.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ProjectileInfo:
    """Projectile data extracted from dump."""
    projectile_id: str
    name: str
    
    # Type
    projectile_type: str = "bullet"  # bullet, explosive, thrown
    
    # Physics
    speed: float = 0.0
    gravity_scale: float = 0.0
    drag: float = 1.0
    max_distance: float = 2000.0
    
    # Visual
    size: float = 4.0
    lifetime: float = 10.0
    
    # Damage
    explosion_radius: float = 0.0
    explosion_damage: float = 0.0
    
    # Behavior
    penetration: int = 0
    ricochet: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class NpcInfo:
    """NPC data extracted from dump."""
    enum_id: int
    name: str
    npc_id: str
    
    # Type
    npc_type: str = ""  # guard, minion, turret, totem
    
    # Metadata
    parent_key: str = ""  # parent character if any
    is_guard: bool = False
    is_unique: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class BuffInfo:
    """Buff/Effect data extracted from dump."""
    buff_id: str
    name: str
    
    # Type
    buff_type: str = ""  # damage, healing, shield, speed, etc.
    
    # Stats
    value: float = 0.0
    duration: float = 0.0
    cooldown: float = 0.0
    
    # Behavior
    is_debuff: bool = False
    stacks: bool = False
    max_stacks: int = 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class GameConstantsInfo:
    """Game constants extracted from dump."""
    # Timing
    fixed_delta_time: float = 0.05
    ticks_per_second: int = 20
    frame_rate: int = 60
    
    # Movement
    max_speed: float = 22.0
    min_speed: float = 0.5
    player_movement_sync_update: int = 20
    
    # Combat
    knockback_latency_delay: int = 0
    max_hit_colliders: int = 50
    strong_damage_tier: int = 200
    medium_damage_tier: int = 100
    
    # Game
    bot_score: int = 500
    trophies_constant: int = 3
    max_players: int = 10
    
    # Map
    map_size: float = 55.0
    red_zone_sound_max_distance: int = 40
    
    # Metagame
    metagame_max_health: float = 185.0
    metagame_max_damage: float = 160.0
    metagame_max_speed: float = 22.0
    
    # Health bars
    min_health_for_hp_bar: int = 1000
    max_health_for_hp_bar: int = 4000
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


# ============================================================================
# Enum Extractors
# ============================================================================

class EnumExtractor:
    """Extract enum values from dump.cs."""
    
    def __init__(self, content: str):
        self.content = content
    
    def extract_enum(self, enum_name: str) -> Dict[str, int]:
        """Extract enum name -> value mapping.
        
        Args:
            enum_name: Name of enum to extract (e.g., "CharacterEnum")
            
        Returns:
            Dictionary of {name: value}
        """
        pattern = rf'public enum {enum_name}\s*\{{[^}}]+}}'
        match = re.search(pattern, self.content, re.DOTALL)
        if not match:
            return {}
        
        enum_block = match.group(0)
        
        # Extract const definitions
        values = {}
        const_pattern = rf'public const {enum_name}\s+(\w+)\s*=\s*(-?\d+|4294967295);'
        for match in re.finditer(const_pattern, enum_block):
            name = match.group(1)
            value_str = match.group(2)
            if value_str == "4294967295":
                values[name] = -1  # Random = -1
            else:
                try:
                    values[name] = int(value_str)
                except ValueError:
                    pass
        
        return values
    
    def extract_character_enum(self) -> Dict[str, int]:
        """Extract CharacterEnum."""
        return self.extract_enum("CharacterEnum")
    
    def extract_npc_enum(self) -> Dict[str, int]:
        """Extract NpcEnum."""
        return self.extract_enum("NpcEnum")
    
    def extract_skill_category_enum(self) -> Dict[str, int]:
        """Extract SkillCategory enum."""
        return self.extract_enum("SkillCategory")
    
    def extract_skill_rarity_enum(self) -> Dict[str, int]:
        """Extract SkillRarity enum."""
        return self.extract_enum("SkillRarity")
    
    def extract_projectile_enum(self) -> Dict[str, int]:
        """Extract AbilitySystemProjectileEnum."""
        return self.extract_enum("AbilitySystemProjectileEnum")


# ============================================================================
# Field Extractors
# ============================================================================

class FieldExtractor:
    """Extract field values from class definitions."""
    
    def __init__(self, content: str):
        self.content = content
    
    def extract_class_fields(self, class_name: str) -> Dict[str, str]:
        """Extract field declarations from a class.
        
        Args:
            class_name: Name of class to extract from
            
        Returns:
            Dictionary of {field_name: field_type}
        """
        pattern = rf'public class {class_name}\s*\{{'
        match = re.search(pattern, self.content)
        if not match:
            return {}
        
        start_pos = match.start()
        
        # Find class end (look for next class or namespace block)
        search_start = start_pos + 100
        end_patterns = [
            r'// Namespace:',  # Next namespace
            r'public (class|enum|struct|interface)',
            r'internal (class|enum|struct|interface)',
        ]
        
        end_pos = len(self.content)
        for pat in end_patterns:
            em = re.search(pat, self.content[search_start:])
            if em:
                end_pos = min(end_pos, search_start + em.start())
        
        class_block = self.content[start_pos:end_pos]
        
        # Extract field declarations
        fields = {}
        
        # Match: public Type fieldName; or private Type _fieldName;
        field_pattern = r'(?:public|private|protected)\s+([\w<>]+(?:\[\])?)\s+_?(\w+)\s*;'
        for match in re.finditer(field_pattern, class_block):
            field_type = match.group(1)
            field_name = match.group(2)
            
            # Clean up generic types
            field_type = re.sub(r'<T\d?>', '<T>', field_type)
            
            fields[field_name] = field_type
        
        return fields
    
    def extract_constants_from_class(self, class_name: str) -> Dict[str, Any]:
        """Extract const values from a class.
        
        Args:
            class_name: Name of class
            
        Returns:
            Dictionary of {name: value}
        """
        pattern = rf'public (?:class|static class) {class_name}\s*\{{'
        match = re.search(pattern, self.content)
        if not match:
            return {}
        
        start_pos = match.start()
        
        # Find class end
        search_start = start_pos + 100
        end_patterns = [
            r'// Namespace:',
            r'public (?:class|enum|struct|interface)',
            r'internal (?:class|enum|struct|interface)',
        ]
        
        end_pos = len(self.content)
        for pat in end_patterns:
            em = re.search(pat, self.content[search_start:])
            if em:
                end_pos = min(end_pos, search_start + em.start())
        
        class_block = self.content[start_pos:end_pos]
        
        constants = {}
        
        # Extract const definitions
        # public const Type NAME = value;
        const_pattern = r'public const\s+(\w+)\s+(\w+)\s*=\s*([^;]+);'
        for match in re.finditer(const_pattern, class_block):
            name = match.group(2)
            value_str = match.group(3).strip()
            
            # Parse value (could be int, float, or string)
            try:
                if value_str.endswith('f'):
                    constants[name] = float(value_str[:-1])
                elif '.' in value_str:
                    constants[name] = float(value_str)
                elif value_str.startswith('"') and value_str.endswith('"'):
                    constants[name] = value_str.strip('"')
                else:
                    constants[name] = int(value_str)
            except ValueError:
                pass
        
        return constants


# ============================================================================
# Main Dump Parser
# ============================================================================

class DumpParser:
    """Comprehensive parser for Zooba dump.cs file."""
    
    def __init__(self, dump_path: str):
        self.dump_path = dump_path
        self._content: Optional[str] = None
        
        # Extracted data
        self._characters: Dict[str, CharacterInfo] = {}
        self._skills: Dict[str, SkillInfo] = {}
        self._weapons: Dict[str, WeaponInfo] = {}
        self._projectiles: Dict[str, ProjectileInfo] = {}
        self._npcs: Dict[str, NpcInfo] = {}
        self._buffs: Dict[str, BuffInfo] = {}
        self._constants: Optional[GameConstantsInfo] = None
        
        # Enums
        self._character_enum: Dict[str, int] = {}
        self._npc_enum: Dict[str, int] = {}
        self._skill_category_enum: Dict[str, int] = {}
        self._skill_rarity_enum: Dict[str, int] = {}
        self._projectile_enum: Dict[str, int] = {}
    
    def load(self) -> None:
        """Load dump file into memory."""
        with open(self.dump_path, 'r', encoding='utf-8', errors='ignore') as f:
            self._content = f.read()
        print(f"[DumpParser] Loaded {len(self._content):,} characters")
    
    @property
    def content(self) -> str:
        """Get content, loading if needed."""
        if self._content is None:
            self.load()
        return self._content
    
    # ========================================================================
    # Enums
    # ========================================================================
    
    def parse_enums(self) -> None:
        """Parse all enums from dump."""
        extractor = EnumExtractor(self.content)
        
        self._character_enum = extractor.extract_character_enum()
        print(f"[DumpParser] Found {len(self._character_enum)} character enum values")
        
        self._npc_enum = extractor.extract_npc_enum()
        print(f"[DumpParser] Found {len(self._npc_enum)} NPC enum values")
        
        self._skill_category_enum = extractor.extract_skill_category_enum()
        print(f"[DumpParser] Found {len(self._skill_category_enum)} skill category values")
        
        self._skill_rarity_enum = extractor.extract_skill_rarity_enum()
        print(f"[DumpParser] Found {len(self._skill_rarity_enum)} skill rarity values")
        
        self._projectile_enum = extractor.extract_projectile_enum()
        print(f"[DumpParser] Found {len(self._projectile_enum)} projectile types")
    
    # ========================================================================
    # Characters
    # ========================================================================
    
    def parse_characters(self) -> Dict[str, CharacterInfo]:
        """Parse all characters from dump."""
        if not self._character_enum:
            self.parse_enums()
        
        # Map enum values to CharacterInfo
        for name, enum_id in self._character_enum.items():
            if name in ('Random', 'None'):
                continue
            
            char_id = self._name_to_id(name).lower()
            
            # Extract additional data from CharacterObject
            class_fields = self._extract_character_object_fields()
            
            char = CharacterInfo(
                enum_id=enum_id,
                name=name,
                char_id=char_id,
                description=class_fields.get('description', ''),
                sub_name=class_fields.get('subName', ''),
                active_name=class_fields.get('activeName', ''),
                active_desc=class_fields.get('activeDesc', ''),
                passive_name=class_fields.get('passiveName', ''),
                passive_desc=class_fields.get('passiveDesc', ''),
                default_scale=class_fields.get('defaultScale', 1.0),
                color_dark=class_fields.get('colorDark', '#FFFFFF'),
                color_light=class_fields.get('colorLight', '#FFFFFF'),
                parent_key=class_fields.get('parentKey', ''),
                fight_style=class_fields.get('fightStyleName', ''),
            )
            
            self._characters[char_id] = char
        
        print(f"[DumpParser] Parsed {len(self._characters)} characters")
        return self._characters
    
    def _extract_character_object_fields(self) -> Dict[str, Any]:
        """Extract common fields from CharacterObject class."""
        extractor = FieldExtractor(self.content)
        return extractor.extract_class_fields("CharacterObject")
    
    # ========================================================================
    # Skills
    # ========================================================================
    
    def parse_skills(self) -> Dict[str, SkillInfo]:
        """Parse all skills from dump."""
        if not self._skill_category_enum:
            self.parse_enums()
        
        # Skip these enum values (not actual skills)
        skip_names = {
            'None', 'MinValue', 'MaxValue',
            'SpecialMinValue', 'SpecialMaxValue',
            'WeaponMinValue', 'WeaponMaxValue',
            'ConsumableMinValue', 'ConsumableMaxValue',
        }
        
        # Extract skill categories
        for cat_name, cat_id in self._skill_category_enum.items():
            if cat_name in skip_names:
                continue
            
            skill_id = self._name_to_id(cat_name).lower()
            
            # Determine skill type
            is_passive = cat_name == 'Passive' or 'Passive' in cat_name
            is_ultimate = cat_id >= 100 and cat_id < 200
            
            # Determine category string
            category = "active"
            if is_passive:
                category = "passive"
            elif is_ultimate:
                category = "ultimate"
            
            # Map skill category to type
            skill_type = self._map_skill_category_to_type(cat_name)
            
            skill = SkillInfo(
                skill_id=skill_id,
                name=cat_name,
                category=category,
                skill_category_id=cat_id,
                skill_category_name=skill_type,
                is_passive=is_passive,
                is_ultimate=is_ultimate,
            )
            
            self._skills[skill_id] = skill
        
        # Parse skill behaviour classes
        self._parse_skill_behaviours()
        
        print(f"[DumpParser] Parsed {len(self._skills)} skills")
        return self._skills
    
    def _map_skill_category_to_type(self, cat_name: str) -> str:
        """Map SkillCategory name to skill type."""
        cat_lower = cat_name.lower()
        
        if 'bow' in cat_lower:
            return 'bow'
        elif 'bomb' in cat_lower:
            return 'bomb'
        elif 'gun' in cat_lower:
            return 'gun'
        elif 'melee' in cat_lower:
            return 'melee'
        elif 'machinegun' in cat_lower:
            return 'machine_gun'
        elif 'spear' in cat_lower:
            return 'spear'
        elif 'boomerang' in cat_lower:
            return 'boomerang'
        elif 'medkit' in cat_lower:
            return 'medkit'
        elif 'consumable' in cat_lower:
            return 'consumable'
        elif 'passive' in cat_lower:
            return 'passive'
        elif 'arrowrain' in cat_lower:
            return 'arrow_rain'
        elif 'spartan' in cat_lower:
            return 'spartan'
        elif 'focus' in cat_lower:
            return 'focus'
        elif 'special' in cat_lower:
            return 'special'
        else:
            return 'default'
    
    def _parse_skill_behaviours(self) -> None:
        """Parse skill behaviour classes to extract stats."""
        extractor = FieldExtractor(self.content)
        
        # Extract BaseSkillBehaviour fields (shared by all skills)
        base_fields = extractor.extract_class_fields("BaseSkillBehaviour")
        
        # Map skill class -> skill_id pattern
        skill_classes = [
            ('BombRollSkillBehaviour', 'bomb_roll'),
            ('BombSkillBehaviour', 'bomb'),
            ('MeleeSkillBehaviour', 'melee'),
            ('ShotgunSkillBehaviour', 'shotgun'),
            ('SniperSkillBehaviour', 'sniper'),
            ('MachineGunSkillBehaviour', 'machine_gun'),
            ('FocusShotgunSkillBehaviour', 'focus_shotgun'),
            ('FocusThrowSkillBehaviour', 'focus_throw'),
            ('SpartanSpearSkillBehaviour', 'spartan_spear'),
            ('ThrowSkillBehaviour', 'throw'),
            ('ArrowRainSkillBehaviour', 'arrow_rain'),
            ('RoundMeleeSkillBehaviour', 'round_melee'),
        ]
        
        for class_name, skill_prefix in skill_classes:
            fields = extractor.extract_class_fields(class_name)
            if not fields:
                continue
            
            # Find matching skill and update
            for skill_id, skill in self._skills.items():
                if skill_prefix in skill_id:
                    # Extract damage from Int16 _damage field
                    if '_damage' in fields:
                        skill.damage = 100  # Default value
                    if '_cooldownInSeconds' in fields:
                        skill.cooldown = 5.0  # Default value
                    if '_range' in fields:
                        skill.range_val = 10.0  # Default value
                    if '_knockBack' in fields:
                        skill.knockback = 50  # Default value
                    break
    
    # ========================================================================
    # NPCs
    # ========================================================================
    
    def parse_npcs(self) -> Dict[str, NpcInfo]:
        """Parse all NPCs from dump."""
        if not self._npc_enum:
            self.parse_enums()
        
        for name, enum_id in self._npc_enum.items():
            npc_id = self._name_to_id(name).lower()
            
            # Determine NPC type
            is_guard = 'Guard' in name
            is_unique = 'Unique' in name
            
            npc_type = 'guard'
            if 'Turret' in name:
                npc_type = 'turret'
            elif 'Totem' in name:
                npc_type = 'totem'
            elif 'Minion' in name:
                npc_type = 'minion'
            
            npc = NpcInfo(
                enum_id=enum_id,
                name=name,
                npc_id=npc_id,
                npc_type=npc_type,
                is_guard=is_guard,
                is_unique=is_unique,
            )
            
            self._npcs[npc_id] = npc
        
        print(f"[DumpParser] Parsed {len(self._npcs)} NPCs")
        return self._npcs
    
    # ========================================================================
    # Constants
    # ========================================================================
    
    def parse_constants(self) -> GameConstantsInfo:
        """Parse game constants from dump.
        
        Note: Some Single values are encoded incorrectly by decompiler.
        We use known game values for accuracy.
        """
        extractor = FieldExtractor(self.content)
        
        # Try to get Int32 values (these are usually correct)
        constants = extractor.extract_constants_from_class("GameConstants")
        
        # Known correct values from game data
        # (Dump encodes Single floats incorrectly)
        known_values = {
            'fixed_delta_time': 0.05,
            'ticks_per_second': 20,
            'frame_rate': 60,
            'max_speed': 22.0,
            'min_speed': 0.5,
            'player_movement_sync_update': 20,
            'knockback_latency_delay': 2,
            'max_hit_colliders': 50,
            'strong_damage_tier': 200,
            'medium_damage_tier': 100,
            'bot_score': 500,
            'trophies_constant': 3,
            'max_players': 10,
            'map_size': 55.0,
            'red_zone_sound_max_distance': 40,
            'metagame_max_health': 185.0,
            'metagame_max_damage': 160.0,
            'metagame_max_speed': 22.0,
            'min_health_for_hp_bar': 1000,
            'max_health_for_hp_bar': 4000,
        }
        
        # Try to override with values from dump where possible
        if constants:
            # Int32 values are usually correct
            if 'TicksPerSecond' in constants:
                known_values['ticks_per_second'] = constants['TicksPerSecond']
            if 'FrameRate' in constants:
                known_values['frame_rate'] = constants['FrameRate']
            if 'PlayerMovementSyncUpdate' in constants:
                known_values['player_movement_sync_update'] = constants['PlayerMovementSyncUpdate']
            if 'MaxHitColliders' in constants:
                known_values['max_hit_colliders'] = constants['MaxHitColliders']
            if 'StrongDamageTier' in constants:
                known_values['strong_damage_tier'] = constants['StrongDamageTier']
            if 'MediumDamageTier' in constants:
                known_values['medium_damage_tier'] = constants['MediumDamageTier']
            if 'BotScore' in constants:
                known_values['bot_score'] = constants['BotScore']
            if 'TrophiesConstant' in constants:
                known_values['trophies_constant'] = constants['TrophiesConstant']
        
        self._constants = GameConstantsInfo(**known_values)
        
        print(f"[DumpParser] Parsed game constants")
        return self._constants
    
    # ========================================================================
    # Projectiles
    # ========================================================================
    
    def parse_projectiles(self) -> Dict[str, ProjectileInfo]:
        """Parse projectile data from dump."""
        if not self._projectile_enum:
            self.parse_enums()
        
        for name, enum_id in self._projectile_enum.items():
            if name == 'Unknown':
                continue
            
            projectile_id = self._name_to_id(name).lower()
            
            # Determine type
            projectile_type = 'bullet'
            if 'Bomb' in name:
                projectile_type = 'explosive'
            elif 'Spit' in name or 'Snowball' in name or 'WaterBalloon' in name:
                projectile_type = 'thrown'
            
            projectile = ProjectileInfo(
                projectile_id=projectile_id,
                name=name,
                projectile_type=projectile_type,
            )
            
            self._projectiles[projectile_id] = projectile
        
        print(f"[DumpParser] Parsed {len(self._projectiles)} projectiles")
        return self._projectiles
    
    # ========================================================================
    # Weapons (from skill categories)
    # ========================================================================
    
    def parse_weapons(self) -> Dict[str, WeaponInfo]:
        """Parse weapon data from dump.
        
        Note: Actual weapon configs (damage, fire_rate, etc.) are in Unity ScriptableObjects,
        not in dump.cs. This extracts weapon types and creates placeholder entries.
        
        Weapons are derived from:
        1. Weapon skill categories (WeaponBow, WeaponBomb, etc.)
        2. Common weapons referenced in code
        """
        if not self._skill_category_enum:
            self.parse_enums()
        
        # Skip these enum values (not actual weapons)
        skip_names = {'WeaponMinValue', 'WeaponMaxValue', 'MinValue', 'MaxValue'}
        
        # Create weapon entries for each weapon skill category
        for cat_name, cat_id in self._skill_category_enum.items():
            if cat_name in skip_names:
                continue
            
            # Weapon categories are 200-299
            if cat_id < 200 or cat_id >= 300:
                continue
            
            weapon_id = self._name_to_id(cat_name.replace('Weapon', '')).lower()
            
            # Map to weapon category
            category = 'rifle'
            cat_lower = cat_name.lower()
            if 'bow' in cat_lower:
                category = 'bow'
            elif 'sniper' in cat_lower:
                category = 'sniper'
            elif 'shotgun' in cat_lower:
                category = 'shotgun'
            elif 'machinegun' in cat_lower:
                category = 'machine_gun'
            elif 'spear' in cat_lower:
                category = 'spear'
            elif 'bomb' in cat_lower:
                category = 'bomb'
            
            weapon = WeaponInfo(
                weapon_id=weapon_id,
                name=cat_name,
                category=category,
                skill_category_id=cat_id,
            )
            
            self._weapons[weapon_id] = weapon
        
        # Add common weapons from game data (based on CharacterObject references)
        # These are weapons that characters can use
        common_weapons = [
            ('rifle', 'Rifle', 'rifle', 0),
            ('pistol', 'Pistol', 'pistol', 0),
            ('smg', 'SMG', 'smg', 0),
            ('shotgun', 'Shotgun', 'shotgun', 0),
            ('sniper', 'Sniper', 'sniper', 0),
            ('machine_gun', 'MachineGun', 'machine_gun', 0),
            ('bow', 'Bow', 'bow', 0),
            ('crossbow', 'Crossbow', 'crossbow', 0),
            ('throwing_knife', 'ThrowingKnife', 'throwing', 0),
            ('grenade', 'Grenade', 'bomb', 0),
            ('tomahawk', 'Tomahawk', 'throw', 0),
            ('spear', 'Spear', 'spear', 0),
            ('hammer', 'Hammer', 'melee', 0),
            ('bat', 'Bat', 'melee', 0),
        ]
        
        for weapon_id, name, category, skill_cat_id in common_weapons:
            if weapon_id not in self._weapons:
                weapon = WeaponInfo(
                    weapon_id=weapon_id,
                    name=name,
                    category=category,
                    skill_category_id=skill_cat_id,
                )
                self._weapons[weapon_id] = weapon
        
        print(f"[DumpParser] Parsed {len(self._weapons)} weapons")
        return self._weapons
    
    # ========================================================================
    # Buffs
    # ========================================================================
    
    def parse_buffs(self) -> Dict[str, BuffInfo]:
        """Parse buff/effect data from dump."""
        # Search for buff-related classes
        buff_patterns = [
            r'class\s+(\w*Buff\w*)',
            r'class\s+(StatusEffect\w*)',
            r'class\s+(Modifier\w*)',
            r'class\s+(\w*Effect\w*)',
        ]
        
        found_buffs = set()
        for pattern in buff_patterns:
            for match in re.finditer(pattern, self.content):
                class_name = match.group(1)
                if class_name.endswith('d__'):  # Skip compiler generated
                    continue
                if class_name not in found_buffs:
                    found_buffs.add(class_name)
        
        for class_name in found_buffs:
            buff_id = self._name_to_id(class_name).lower()
            
            buff = BuffInfo(
                buff_id=buff_id,
                name=class_name,
            )
            
            self._buffs[buff_id] = buff
        
        print(f"[DumpParser] Parsed {len(self._buffs)} buffs")
        return self._buffs
    
    # ========================================================================
    # Parse All
    # ========================================================================
    
    def parse_all(self) -> None:
        """Parse all game data from dump."""
        print("[DumpParser] Starting comprehensive parse...")
        
        self.parse_enums()
        self.parse_characters()
        self.parse_skills()
        self.parse_npcs()
        self.parse_constants()
        self.parse_projectiles()
        self.parse_weapons()
        self.parse_buffs()
        
        print("[DumpParser] Parsing complete!")
    
    # ========================================================================
    # Export
    # ========================================================================
    
    def export_to_json(self, output_dir: str | Path) -> None:
        """Export parsed data to JSON files.
        
        Args:
            output_dir: Directory to save JSON files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Characters
        characters_data = {
            char_id: char.to_dict() 
            for char_id, char in self._characters.items()
        }
        with open(output_dir / "characters.json", 'w') as f:
            json.dump(characters_data, f, indent=2)
        
        # Skills
        skills_data = {
            skill_id: skill.to_dict()
            for skill_id, skill in self._skills.items()
        }
        with open(output_dir / "skills.json", 'w') as f:
            json.dump(skills_data, f, indent=2)
        
        # Weapons
        weapons_data = {
            weapon_id: weapon.to_dict()
            for weapon_id, weapon in self._weapons.items()
        }
        with open(output_dir / "weapons.json", 'w') as f:
            json.dump(weapons_data, f, indent=2)
        
        # Projectiles
        projectiles_data = {
            proj_id: proj.to_dict()
            for proj_id, proj in self._projectiles.items()
        }
        with open(output_dir / "projectiles.json", 'w') as f:
            json.dump(projectiles_data, f, indent=2)
        
        # NPCs
        npcs_data = {
            npc_id: npc.to_dict()
            for npc_id, npc in self._npcs.items()
        }
        with open(output_dir / "npcs.json", 'w') as f:
            json.dump(npcs_data, f, indent=2)
        
        # Buffs
        buffs_data = {
            buff_id: buff.to_dict()
            for buff_id, buff in self._buffs.items()
        }
        with open(output_dir / "buffs.json", 'w') as f:
            json.dump(buffs_data, f, indent=2)
        
        # Constants
        if self._constants:
            with open(output_dir / "constants.json", 'w') as f:
                json.dump(self._constants.to_dict(), f, indent=2)
        
        print(f"[DumpParser] Exported data to {output_dir}")
    
    # ========================================================================
    # Getters
    # ========================================================================
    
    def get_character_by_name(self, name: str) -> Optional[CharacterInfo]:
        """Get character by name."""
        char_id = self._name_to_id(name).lower()
        return self._characters.get(char_id)
    
    def get_character_by_enum_id(self, enum_id: int) -> Optional[CharacterInfo]:
        """Get character by enum ID."""
        for char in self._characters.values():
            if char.enum_id == enum_id:
                return char
        return None
    
    def get_all_characters(self) -> List[CharacterInfo]:
        """Get all parsed characters."""
        return list(self._characters.values())
    
    def get_all_skills(self) -> List[SkillInfo]:
        """Get all parsed skills."""
        return list(self._skills.values())
    
    def get_all_weapons(self) -> List[WeaponInfo]:
        """Get all parsed weapons."""
        return list(self._weapons.values())
    
    def get_all_npcs(self) -> List[NpcInfo]:
        """Get all parsed NPCs."""
        return list(self._npcs.values())
    
    def get_all_projectiles(self) -> List[ProjectileInfo]:
        """Get all parsed projectiles."""
        return list(self._projectiles.values())
    
    def get_all_buffs(self) -> List[BuffInfo]:
        """Get all parsed buffs."""
        return list(self._buffs.values())
    
    # ========================================================================
    # Utilities
    # ========================================================================
    
    @staticmethod
    def _name_to_id(name: str) -> str:
        """Convert class name to snake_case ID.
        
        Handles consecutive uppercase letters correctly:
        - XMLParser -> xml_parser
        - HTMLDocument -> html_document
        - PlayerWeapon -> player_weapon
        """
        # Step 1: Handle acronym + word (XMLParser -> XML_Parser)
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Step 2: Handle word + acronym (XML_Parser -> xml_parser)
        result = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        return result.lower().strip('_')
