"""Dynamic plugin generator from Zooba dump."""

from zbgym.dump.parser import (
    CharacterInfo,
    DumpParser,
    SkillInfo,
    WeaponInfo,
)
from zbgym.plugins.base import PluginMetadata
from zbgym.plugins.character import (
    Ability,
    Character,
    CharacterConfig,
    CharacterStats,
    character_registry,
)
from zbgym.plugins.skill import Skill, SkillConfig, SkillType, skill_registry
from zbgym.plugins.weapon import Weapon, WeaponConfig, WeaponStats, weapon_registry


class DynamicPluginGenerator:
    """Generates plugins dynamically from dump data."""

    def __init__(self, dump_path: str):
        self.parser = DumpParser(dump_path)
        self._character_classes: dict[str, type[Character]] = {}
        self._weapon_classes: dict[str, type[Weapon]] = {}
        self._skill_classes: dict[str, type[Skill]] = {}

    def load(self) -> None:
        """Load and parse dump file."""
        print("[Generator] Loading dump...")
        self.parser.load()
        self.parser.parse_all()

    def generate_character(self, info: CharacterInfo) -> type[Character]:
        """Generate a Character class from CharacterInfo."""

        # Create metadata
        metadata = PluginMetadata(
            id=info.char_id,
            name=info.name,
            description=info.description,
        )

        # Create stats (use defaults if not available)
        stats = CharacterStats(
            max_health=1000,  # Default
            max_shield=500,  # Default
            max_energy=100,  # Default
            move_speed=300,  # Default
            base_damage=10,  # Default
        )

        # Map modifier fields if available
        if info.health_modifier != 0:
            stats.max_health = 1000 * (1 + info.health_modifier)
        if info.damage_modifier != 0:
            stats.base_damage = 10 * (1 + info.damage_modifier)
        if info.agility_modifier != 0:
            stats.move_speed = 300 * (1 + info.agility_modifier)

        # Create abilities
        abilities = []
        if info.active_name:
            abilities.append(
                Ability(
                    id=f"{info.char_id}_active",
                    name=info.active_name,
                    description=info.active_desc,
                    cooldown=5.0,
                    is_ultimate=False,  # Character doesn't have category
                )
            )
        if info.passive_name:
            abilities.append(
                Ability(
                    id=f"{info.char_id}_passive",
                    name=info.passive_name,
                    description=info.passive_desc,
                    cooldown=0,
                )
            )

        # Create config
        config = CharacterConfig(
            stats=stats,
            abilities=abilities,
            model_id=info.char_id,
        )

        # Create class dynamically
        attrs = {
            "__module__": "zbgym.plugins.generated",
            "metadata": metadata,
            "config": config,
            "_char_enum_id": info.enum_id,
        }

        cls = type(info.name, (Character,), attrs)
        self._character_classes[info.char_id] = cls
        return cls

    def generate_weapon(self, info: WeaponInfo) -> type[Weapon]:
        """Generate a Weapon class from WeaponInfo."""

        # Create metadata
        metadata = PluginMetadata(
            id=info.weapon_id,
            name=info.name,
        )

        # Create stats
        stats = WeaponStats(
            damage=info.damage if info.damage > 0 else 10,
            fire_rate=info.fire_rate if info.fire_rate > 0 else 10,
            projectile_speed=info.projectile_speed if info.projectile_speed > 0 else 1000,
            range=info.range_val if info.range_val > 0 else 1000,
            magazine_size=info.magazine_size if info.magazine_size > 0 else 30,
            total_ammo=info.total_ammo if info.total_ammo > 0 else 120,
            reload_time=info.reload_time if info.reload_time > 0 else 2.0,
            spread=info.spread,
            recoil=info.recoil,
            critical_chance=info.critical_chance,
            critical_multiplier=info.critical_multiplier,
            headshot_multiplier=info.headshot_multiplier,
            penetration=info.penetration,
            ricochet=info.ricochet,
            projectile_count=info.projectile_count,
            # explosion_radius and explosion_damage not in WeaponInfo
            min_damage_ratio=info.min_damage_ratio,
            max_damage_distance=info.max_damage_distance,
        )

        # Create config
        config = WeaponConfig(
            stats=stats,
            model_id=info.weapon_id,
        )

        # Create class dynamically
        attrs = {
            "__module__": "zbgym.plugins.generated",
            "metadata": metadata,
            "config": config,
            "_skill_category_id": info.skill_category_id,
        }

        cls = type(info.name, (Weapon,), attrs)
        self._weapon_classes[info.weapon_id] = cls
        return cls

    def generate_skill(self, info: SkillInfo) -> type[Skill]:
        """Generate a Skill class from SkillInfo."""

        # Create metadata
        metadata = PluginMetadata(
            id=info.skill_id,
            name=info.name,
        )

        # Map skill category to SkillType
        skill_type = self._map_skill_type(info.skill_category_name)

        # Create config
        config = SkillConfig(
            skill_type=skill_type,
            cooldown=info.cooldown if info.cooldown > 0 else 5.0,
            range=info.range_val if info.range_val > 0 else 500,
            duration=info.duration,
            damage=info.damage,
        )

        # Create class dynamically with abstract method implemented
        class_name = info.name

        # Create a concrete skill class
        class GeneratedSkill(Skill):
            def _apply_effects(self, target) -> None:
                """Generated skill effect."""

        # Set metadata and config
        GeneratedSkill.metadata = metadata
        GeneratedSkill.config = config
        GeneratedSkill.__name__ = class_name
        GeneratedSkill.__module__ = "zbgym.plugins.generated"

        cls = GeneratedSkill
        self._skill_classes[info.skill_id] = cls
        return cls

    def _map_skill_type(self, skill_category: str) -> SkillType:
        """Map skill category string to SkillType enum."""
        mapping = {
            "bow": SkillType.PROJECTILE,
            "bomb": SkillType.AOE,
            "gun": SkillType.PROJECTILE,
            "melee": SkillType.AOE,  # Closest match
            "machine_gun": SkillType.PROJECTILE,
            "spear": SkillType.PROJECTILE,
            "boomerang": SkillType.PROJECTILE,
            "medkit": SkillType.HEAL,
            "consumable": SkillType.BUFF,
            "passive": SkillType.BUFF,
            "arrow_rain": SkillType.AOE,
            "spartan": SkillType.PROJECTILE,
            "focus": SkillType.PROJECTILE,
            "special": SkillType.ULTIMATE,
            "default": SkillType.PROJECTILE,
        }
        return mapping.get(skill_category, SkillType.PROJECTILE)

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

        print(
            f"[Generator] Generated {len(self._character_classes)} characters, "
            f"{len(self._weapon_classes)} weapons, {len(self._skill_classes)} skills"
        )

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

        print(
            f"[Generator] Registered {len(character_registry.list_plugins())} characters, "
            f"{len(weapon_registry.list_plugins())} weapons, {len(skill_registry.list_plugins())} skills"
        )

    def load_and_register(self) -> None:
        """Full pipeline: load dump, generate plugins, register them."""
        self.load()
        self.generate_all()
        self.register_all()

    def get_character_class(self, char_id: str) -> type[Character] | None:
        """Get generated character class by ID."""
        return self._character_classes.get(char_id)

    def get_weapon_class(self, weapon_id: str) -> type[Weapon] | None:
        """Get generated weapon class by ID."""
        return self._weapon_classes.get(weapon_id)

    def get_skill_class(self, skill_id: str) -> type[Skill] | None:
        """Get generated skill class by ID."""
        return self._skill_classes.get(skill_id)


# Global generator instance
_generator: DynamicPluginGenerator | None = None


def get_generator(dump_path: str | None = None) -> DynamicPluginGenerator:
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
