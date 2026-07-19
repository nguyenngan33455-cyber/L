"""Dynamic plugin generator from Zooba dump."""

from typing import Dict, Type, Optional
from zbgym.plugins.character import Character, character_registry
from zbgym.plugins.weapon import Weapon, weapon_registry
from zbgym.plugins.skill import Skill, skill_registry
from zbgym.dump.parser import DumpParser, CharacterInfo, WeaponInfo, SkillInfo


class DynamicPluginGenerator:
    """Generates plugins dynamically from dump data."""
    
    def __init__(self, dump_path: str):
        self.parser = DumpParser(dump_path)
        self._character_classes: Dict[str, Type[Character]] = {}
        self._weapon_classes: Dict[str, Type[Weapon]] = {}
        self._skill_classes: Dict[str, Type[Skill]] = {}
        
    def load(self) -> None:
        """Load and parse dump file."""
        print("[Generator] Loading dump...")
        self.parser.load()
        self.parser.parse_all()
        
    def generate_character(self, info: CharacterInfo) -> Type[Character]:
        """Generate a Character class from CharacterInfo."""
        
        def create_character_class():
            attrs = {
                'plugin_id': info.char_id,
                'name': info.name,
                'health': 1000,
                'speed': 5.0,
                'damage': 100,
                'attack_range': 3.0,
                'attack_speed': 1.0,
                '_char_enum_id': info.enum_id,
            }
            
            # Add custom stats from dump
            for key, value in info.stats.items():
                attrs[key] = value
                
            return type(info.name, (Character,), attrs)
            
        cls = create_character_class()
        self._character_classes[info.char_id] = cls
        return cls
    
    def generate_weapon(self, info: WeaponInfo) -> Type[Weapon]:
        """Generate a Weapon class from WeaponInfo."""
        
        def create_weapon_class():
            attrs = {
                'plugin_id': info.weapon_id,
                'name': info.name,
                'damage': info.damage,
                'fire_rate': info.fire_rate,
                'range_val': info.range_val,
                'projectile_speed': info.projectile_speed,
            }
            
            for key, value in info.stats.items():
                attrs[key] = value
                
            return type(info.name, (Weapon,), attrs)
            
        cls = create_weapon_class()
        self._weapon_classes[info.weapon_id] = cls
        return cls
    
    def generate_skill(self, info: SkillInfo) -> Type[Skill]:
        """Generate a Skill class from SkillInfo."""
        
        def create_skill_class():
            attrs = {
                'plugin_id': info.skill_id,
                'name': info.name,
                'category': info.category,
                'cooldown': info.cooldown,
                'duration': info.duration,
                'effects': info.effects,
            }
            
            for key, value in info.stats.items():
                attrs[key] = value
                
            return type(info.name, (Skill,), attrs)
            
        cls = create_skill_class()
        self._skill_classes[info.skill_id] = cls
        return cls
    
    def generate_all(self) -> None:
        """Generate all plugins from parsed data."""
        print("[Generator] Generating characters...")
        for info in self.parser.get_all_characters():
            self.generate_character(info)
            
        print("[Generator] Generating weapons...")
        for info in self.parser.get_all_weapons():
            self.generate_weapon(info)
            
        print("[Generator] Generating skills...")
        for info in self.parser.get_all_skills():
            self.generate_skill(info)
            
        print(f"[Generator] Generated {len(self._character_classes)} characters, "
              f"{len(self._weapon_classes)} weapons, {len(self._skill_classes)} skills")
    
    def register_all(self) -> None:
        """Register all generated plugins to their registries."""
        print("[Generator] Registering plugins...")
        
        # Register characters
        for char_id, cls in self._character_classes.items():
            character_registry.register(cls, char_id)
            
        # Register weapons
        for weapon_id, cls in self._weapon_classes.items():
            weapon_registry.register(cls, weapon_id)
            
        # Register skills
        for skill_id, cls in self._skill_classes.items():
            skill_registry.register(cls, skill_id)
            
        print(f"[Generator] Registered {len(character_registry.list_plugins())} characters, "
              f"{len(weapon_registry.list_plugins())} weapons, {len(skill_registry.list_plugins())} skills")
    
    def load_and_register(self) -> None:
        """Full pipeline: load dump, generate plugins, register them."""
        self.load()
        self.generate_all()
        self.register_all()
    
    def get_character_class(self, char_id: str) -> Optional[Type[Character]]:
        """Get generated character class by ID."""
        return self._character_classes.get(char_id)
    
    def get_weapon_class(self, weapon_id: str) -> Optional[Type[Weapon]]:
        """Get generated weapon class by ID."""
        return self._weapon_classes.get(weapon_id)
    
    def get_skill_class(self, skill_id: str) -> Optional[Type[Skill]]:
        """Get generated skill class by ID."""
        return self._skill_classes.get(skill_id)


# Global generator instance
_generator: Optional[DynamicPluginGenerator] = None


def get_generator(dump_path: Optional[str] = None) -> DynamicPluginGenerator:
    """Get or create the global generator instance."""
    global _generator
    if _generator is None and dump_path:
        _generator = DynamicPluginGenerator(dump_path)
    return _generator


def load_from_dump(dump_path: str) -> DynamicPluginGenerator:
    """Load and register all plugins from dump file."""
    gen = get_generator(dump_path)
    gen.load_and_register()
    return gen
