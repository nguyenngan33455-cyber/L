"""Dump parser for Zooba game data extraction."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class CharacterInfo:
    """Character data extracted from dump."""
    enum_id: int
    name: str
    char_id: str
    stats: Dict[str, Any] = field(default_factory=dict)
    abilities: List[str] = field(default_factory=list)
    default_weapon: Optional[str] = None
    default_skill: Optional[str] = None


@dataclass
class WeaponInfo:
    """Weapon data extracted from dump."""
    weapon_id: str
    name: str
    damage: float = 0.0
    fire_rate: float = 1.0
    range_val: float = 0.0
    projectile_speed: float = 0.0
    stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillInfo:
    """Skill data extracted from dump."""
    skill_id: str
    name: str
    category: str = "active"
    cooldown: float = 0.0
    duration: float = 0.0
    effects: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


class DumpParser:
    """Parser for Zooba dump.cs file."""
    
    def __init__(self, dump_path: str):
        self.dump_path = dump_path
        self._content: Optional[str] = None
        self._characters: Dict[int, CharacterInfo] = {}
        self._weapons: Dict[str, WeaponInfo] = {}
        self._skills: Dict[str, SkillInfo] = {}
        
    def load(self) -> None:
        """Load dump file into memory."""
        with open(self.dump_path, 'r', encoding='utf-8', errors='ignore') as f:
            self._content = f.read()
        print(f"[DumpParser] Loaded {len(self._content):,} characters")
        
    def parse_characters(self) -> Dict[int, CharacterInfo]:
        """Extract all characters from dump."""
        if not self._content:
            self.load()
            
        # Find CharacterEnum definition
        pattern = r'public enum CharacterEnum\s*\{[^}]+\}'
        match = re.search(pattern, self._content, re.DOTALL)
        if not match:
            print("[DumpParser] CharacterEnum not found")
            return {}
            
        enum_block = match.group(0)
        
        # Extract character definitions
        char_pattern = r'public const CharacterEnum\s+(\w+)\s*=\s*(\d+);'
        for match in re.finditer(char_pattern, enum_block):
            name = match.group(1)
            enum_id = int(match.group(2))
            
            if name in ('Random', 'None'):
                continue
                
            char_id = self._name_to_char_id(name)
            self._characters[enum_id] = CharacterInfo(
                enum_id=enum_id,
                name=name,
                char_id=char_id
            )
            
        print(f"[DumpParser] Found {len(self._characters)} characters")
        return self._characters
    
    def parse_weapons(self) -> Dict[str, WeaponInfo]:
        """Extract weapon data from dump."""
        if not self._content:
            self.load()
            
        weapon_names = set()
        for pattern in [r'class\s+(\w*[Ww]eapon\w+)', r'(\w*[Ww]eapon\w+)Enum']:
            for match in re.finditer(pattern, self._content):
                name = match.group(1)
                if not name.endswith('d__'):  # Skip compiler generated
                    weapon_names.add(name)
        
        # Create weapon info for found weapons
        for name in sorted(weapon_names):
            weapon_id = self._name_to_id(name)
            self._weapons[weapon_id] = WeaponInfo(
                weapon_id=weapon_id,
                name=name
            )
            
        print(f"[DumpParser] Found {len(self._weapons)} weapon types")
        return self._weapons
    
    def parse_skills(self) -> Dict[str, SkillInfo]:
        """Extract skill data from dump."""
        if not self._content:
            self.load()
            
        skill_names = set()
        
        # Find skill classes
        skill_patterns = [
            r'class\s+(\w*[Ss]kill\w+)',
            r'(\w*[Ss]kill\w+)Enum',
        ]
        
        for pattern in skill_patterns:
            for match in re.finditer(pattern, self._content):
                name = match.group(1)
                if not name.endswith('d__'):  # Skip compiler generated
                    skill_names.add(name)
        
        # Categorize skills
        for name in sorted(skill_names):
            skill_id = self._name_to_id(name)
            
            # Determine category
            category = "active"
            if 'Passive' in name or 'passive' in name:
                category = "passive"
            elif 'Ultimate' in name or 'ultimate' in name:
                category = "ultimate"
            elif 'Support' in name or 'support' in name:
                category = "support"
                
            self._skills[skill_id] = SkillInfo(
                skill_id=skill_id,
                name=name,
                category=category
            )
            
        print(f"[DumpParser] Found {len(self._skills)} skill types")
        return self._skills
    
    def parse_all(self) -> None:
        """Parse all game data from dump."""
        self.parse_characters()
        self.parse_weapons()
        self.parse_skills()
        print(f"[DumpParser] Parsing complete!")
        
    def get_character_by_name(self, name: str) -> Optional[CharacterInfo]:
        """Get character by name."""
        for char in self._characters.values():
            if char.name.lower() == name.lower():
                return char
        return None
    
    def get_all_characters(self) -> List[CharacterInfo]:
        """Get all parsed characters."""
        return list(self._characters.values())
    
    def get_all_weapons(self) -> List[WeaponInfo]:
        """Get all parsed weapons."""
        return list(self._weapons.values())
    
    def get_all_skills(self) -> List[SkillInfo]:
        """Get all parsed skills."""
        return list(self._skills.values())
    
    @staticmethod
    def _name_to_id(name: str) -> str:
        """Convert class name to snake_case ID."""
        result = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        return re.sub(r'_+', '_', result).strip('_')
    
    @staticmethod
    def _name_to_char_id(name: str) -> str:
        """Convert character name to char_id format."""
        return DumpParser._name_to_id(name)
