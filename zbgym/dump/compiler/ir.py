"""Intermediate Representation (IR) for dump.cs data extraction."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class CharacterIR:
    """Intermediate representation of a character."""

    id: str
    name: str
    enum_id: int = 0

    # Stats
    max_health: float = 100.0
    max_shield: float = 50.0
    max_energy: float = 100.0
    move_speed: float = 300.0
    sprint_speed: float = 450.0
    jump_force: float = 400.0
    armor: float = 0.0
    vision_range: float = 500.0
    base_damage: float = 10.0
    critical_chance: float = 0.05
    critical_multiplier: float = 1.5
    headshot_multiplier: float = 2.0

    # Game data
    rarity: str = "common"
    league: int = 0
    default_weapon: str = ""
    default_skill: str = ""
    abilities: list[str] = field(default_factory=list)

    # Metadata
    is_playable: bool = True
    is_hidden: bool = False
    is_disabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_plugin_dict(self) -> dict[str, Any]:
        """Convert to plugin-compatible dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "stats": {
                "max_health": self.max_health,
                "max_shield": self.max_shield,
                "max_energy": self.max_energy,
                "move_speed": self.move_speed,
                "sprint_speed": self.sprint_speed,
                "jump_force": self.jump_force,
                "armor": self.armor,
                "vision_range": self.vision_range,
                "base_damage": self.base_damage,
                "critical_chance": self.critical_chance,
                "critical_multiplier": self.critical_multiplier,
                "headshot_multiplier": self.headshot_multiplier,
            },
            "abilities": self.abilities,
            "default_weapon": self.default_weapon,
            "rarity": self.rarity,
        }


@dataclass
class WeaponIR:
    """Intermediate representation of a weapon."""

    id: str
    name: str
    weapon_type: str = "rifle"

    # Combat stats
    damage: float = 10.0
    fire_rate: float = 10.0
    magazine_size: int = 30
    total_ammo: int = 120
    reload_time: float = 2.0

    # Accuracy
    spread: float = 0.0
    recoil: float = 0.0
    range: float = 1000.0

    # Projectile
    projectile_speed: float = 1000.0
    projectile_count: int = 1
    explosion_radius: float = 0.0
    explosion_damage: float = 0.0

    # Special
    critical_chance: float = 0.05
    critical_multiplier: float = 1.5
    headshot_multiplier: float = 2.0
    penetration: int = 0
    ricochet: int = 0

    # Damage falloff
    min_damage_ratio: float = 0.5
    max_damage_distance: float = 500.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_plugin_dict(self) -> dict[str, Any]:
        """Convert to plugin-compatible dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "weapon_type": self.weapon_type,
            "stats": {
                "damage": self.damage,
                "fire_rate": self.fire_rate,
                "magazine_size": self.magazine_size,
                "total_ammo": self.total_ammo,
                "reload_time": self.reload_time,
                "spread": self.spread,
                "recoil": self.recoil,
                "range": self.range,
                "projectile_speed": self.projectile_speed,
                "projectile_count": self.projectile_count,
                "explosion_radius": self.explosion_radius,
                "explosion_damage": self.explosion_damage,
                "critical_chance": self.critical_chance,
                "critical_multiplier": self.critical_multiplier,
                "headshot_multiplier": self.headshot_multiplier,
                "penetration": self.penetration,
                "ricochet": self.ricochet,
                "min_damage_ratio": self.min_damage_ratio,
                "max_damage_distance": self.max_damage_distance,
            },
        }


@dataclass
class SkillIR:
    """Intermediate representation of a skill."""

    id: str
    name: str
    skill_type: str = "active"
    category: str = "normal"

    # Costs
    cooldown: float = 5.0
    energy_cost: float = 0.0
    cast_time: float = 0.0
    channel_duration: float = 0.0

    # Effects
    damage: float = 0.0
    healing: float = 0.0
    shield_amount: float = 0.0
    speed_modifier: float = 1.0
    duration: float = 0.0

    # Range and area
    range: float = 0.0
    area_radius: float = 0.0

    # Metadata
    is_ultimate: bool = False
    is_passive: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ProjectileIR:
    """Intermediate representation of a projectile."""

    id: str
    name: str
    projectile_type: str = "bullet"

    speed: float = 1000.0
    gravity_scale: float = 0.0
    drag: float = 1.0
    max_distance: float = 2000.0
    size: float = 4.0
    lifetime: float = 10.0

    explosion_radius: float = 0.0
    explosion_damage: float = 0.0
    penetration: int = 0
    ricochet: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class MapIR:
    """Intermediate representation of a map."""

    id: str
    name: str
    width: int = 2000
    height: int = 1500

    # Zone settings
    safe_zone_radius: float = 1000.0
    danger_zone_radius: float = 1200.0
    zone_shrink_rate: float = 0.5

    # Spawn points
    spawn_points: list[dict[str, float]] = field(default_factory=list)

    # Map elements
    obstacles: list[dict[str, Any]] = field(default_factory=list)
    bushes: list[dict[str, Any]] = field(default_factory=list)
    loot_spawns: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class IntermediateRepresentation:
    """Container for all extracted IR data."""

    characters: dict[str, CharacterIR] = field(default_factory=dict)
    weapons: dict[str, WeaponIR] = field(default_factory=dict)
    skills: dict[str, SkillIR] = field(default_factory=dict)
    projectiles: dict[str, ProjectileIR] = field(default_factory=dict)
    maps: dict[str, MapIR] = field(default_factory=dict)

    # Additional data
    enums: dict[str, list[tuple[str, int]]] = field(default_factory=dict)
    classes: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "weapons": {k: v.to_dict() for k, v in self.weapons.items()},
            "skills": {k: v.to_dict() for k, v in self.skills.items()},
            "projectiles": {k: v.to_dict() for k, v in self.projectiles.items()},
            "maps": {k: v.to_dict() for k, v in self.maps.items()},
        }


class Compiler:
    """Compiler that transforms parsed AST into IR and generates output."""

    def __init__(self, dump_path: str) -> None:
        """
        Initialize the compiler.

        Args:
            dump_path: Path to dump.cs file
        """
        self.dump_path = Path(dump_path)
        self.content: str = ""
        self.ir = IntermediateRepresentation()

    def load(self) -> None:
        """Load dump.cs into memory."""
        print(f"[Compiler] Loading {self.dump_path}...")
        with open(self.dump_path, "r", encoding="utf-8", errors="ignore") as f:
            self.content = f.read()
        print(f"[Compiler] Loaded {len(self.content):,} characters")

    def compile(self) -> IntermediateRepresentation:
        """
        Compile dump.cs to IR.

        Returns:
            IntermediateRepresentation containing all extracted data
        """
        if not self.content:
            self.load()

        print("[Compiler] Extracting CharacterEnum...")
        self._extract_characters()

        print("[Compiler] Extracting weapon data...")
        self._extract_weapons()

        print("[Compiler] Extracting skill data...")
        self._extract_skills()

        print("[Compiler] Extracting projectile data...")
        self._extract_projectiles()

        print("[Compiler] Compiling complete!")
        return self.ir

    def _extract_characters(self) -> None:
        """Extract character data from dump.cs."""
        # Find CharacterEnum
        pattern = r"public enum CharacterEnum\s*\{[^}]+\}"
        match = re.search(pattern, self.content, re.DOTALL)

        if not match:
            print("[Compiler] CharacterEnum not found")
            return

        enum_block = match.group(0)

        # Extract character definitions
        char_pattern = r"public const CharacterEnum\s+(\w+)\s*=\s*(\d+);"
        for match in re.finditer(char_pattern, enum_block):
            name = match.group(1)
            enum_id = int(match.group(2))

            if name in ("Random", "None"):
                continue

            char_id = self._to_snake_case(name)

            # Create character IR with default values
            # These can be overridden with actual game data
            char = CharacterIR(
                id=char_id,
                name=name,
                enum_id=enum_id,
                is_playable=True,
            )

            self.ir.characters[char_id] = char

        print(f"[Compiler] Found {len(self.ir.characters)} characters")

    def _extract_weapons(self) -> None:
        """Extract weapon data from dump.cs."""
        # Find weapon-related classes
        weapon_patterns = [
            r"class\s+(\w*[Ww]eapon\w+)",
            r"(\w*[Ww]eapon\w+)Enum",
        ]

        weapon_names = set()
        for pattern in weapon_patterns:
            for match in re.finditer(pattern, self.content):
                name = match.group(1)
                if not name.endswith("d__"):  # Skip compiler generated
                    weapon_names.add(name)

        for name in sorted(weapon_names):
            weapon_id = self._to_snake_case(name)
            weapon = WeaponIR(
                id=weapon_id,
                name=name,
                weapon_type=self._infer_weapon_type(name),
            )
            self.ir.weapons[weapon_id] = weapon

        print(f"[Compiler] Found {len(self.ir.weapons)} weapon types")

    def _extract_skills(self) -> None:
        """Extract skill data from dump.cs."""
        skill_patterns = [
            r"class\s+(\w*[Ss]kill\w+)",
            r"(\w*[Ss]kill\w+)Enum",
        ]

        skill_names = set()
        for pattern in skill_patterns:
            for match in re.finditer(pattern, self.content):
                name = match.group(1)
                if not name.endswith("d__"):
                    skill_names.add(name)

        for name in sorted(skill_names):
            skill_id = self._to_snake_case(name)
            skill = SkillIR(
                id=skill_id,
                name=name,
                skill_type=self._infer_skill_type(name),
                category=self._infer_skill_category(name),
                is_passive="Passive" in name,
                is_ultimate="Ultimate" in name,
            )
            self.ir.skills[skill_id] = skill

        print(f"[Compiler] Found {len(self.ir.skills)} skill types")

    def _extract_projectiles(self) -> None:
        """Extract projectile data from dump.cs."""
        proj_patterns = [
            r"class\s+(\w*[Pp]rojectile\w+)",
            r"(\w*[Pp]rojectile\w+)Enum",
        ]

        proj_names = set()
        for pattern in proj_patterns:
            for match in re.finditer(pattern, self.content):
                name = match.group(1)
                if not name.endswith("d__"):
                    proj_names.add(name)

        for name in sorted(proj_names):
            proj_id = self._to_snake_case(name)
            proj = ProjectileIR(
                id=proj_id,
                name=name,
                projectile_type=self._infer_projectile_type(name),
            )
            self.ir.projectiles[proj_id] = proj

        print(f"[Compiler] Found {len(self.ir.projectiles)} projectile types")

    def generate_json_databases(self, output_dir: Path | None = None) -> None:
        """
        Generate JSON database files.

        Args:
            output_dir: Output directory for JSON files
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent / "data"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate characters.json
        characters_data = {k: v.to_dict() for k, v in self.ir.characters.items()}
        self._write_json(output_dir / "characters.json", characters_data)

        # Generate weapons.json
        weapons_data = {k: v.to_dict() for k, v in self.ir.weapons.items()}
        self._write_json(output_dir / "weapons.json", weapons_data)

        # Generate skills.json
        skills_data = {k: v.to_dict() for k, v in self.ir.skills.items()}
        self._write_json(output_dir / "skills.json", skills_data)

        # Generate projectiles.json
        projectiles_data = {k: v.to_dict() for k, v in self.ir.projectiles.items()}
        self._write_json(output_dir / "projectiles.json", projectiles_data)

        # Generate maps.json
        maps_data = {k: v.to_dict() for k, v in self.ir.maps.items()}
        self._write_json(output_dir / "maps.json", maps_data)

        # Generate constants.json
        self._generate_constants(output_dir)

        # Generate damage_types.json
        self._generate_damage_types(output_dir)

        # Generate effects.json
        self._generate_effects(output_dir)

        # Generate buffs.json
        self._generate_buffs(output_dir)

        # Generate loot.json
        self._generate_loot(output_dir)

        # Generate movement.json
        self._generate_movement(output_dir)

        # Generate animations.json
        self._generate_animations(output_dir)

        print(f"[Compiler] Generated JSON databases in {output_dir}")

    def _generate_constants(self, output_dir: Path) -> None:
        """Generate constants.json."""
        constants = {
            "physics": {
                "DEFAULT_GRAVITY": 980.0,
                "DEFAULT_FRICTION": 0.98,
                "DEFAULT_AIR_RESISTANCE": 0.99,
                "DEFAULT_MAX_SPEED": 500.0,
                "DEFAULT_DASH_SPEED": 1000.0,
                "DEFAULT_JUMP_FORCE": 400.0,
            },
            "game": {
                "DEFAULT_TICK_RATE": 60,
                "DEFAULT_FRAME_RATE": 30,
                "MAX_ENTITIES": 100,
                "MAX_PROJECTILES": 500,
                "MAX_ITEMS": 200,
            },
            "arena": {
                "DEFAULT_ARENA_WIDTH": 2000,
                "DEFAULT_ARENA_HEIGHT": 1500,
                "SAFE_ZONE_SHRINK_RATE": 0.5,
            },
            "character": {
                "MAX_HEALTH": 100,
                "MAX_SHIELD": 50,
                "MAX_ENERGY": 100,
                "START_AMMO": 30,
                "MAX_AMMO": 120,
                "RESPAWN_TIME": 5.0,
            },
            "combat": {
                "HEADSHOT_MULTIPLIER": 1.5,
                "CRITICAL_MULTIPLIER": 1.25,
                "MAX_DAMAGE_DISTANCE": 1000.0,
                "MIN_DAMAGE_RATIO": 0.5,
            },
            "reward": {
                "KILL_REWARD": 10.0,
                "ASSIST_REWARD": 3.0,
                "DEATH_PENALTY": -5.0,
                "DAMAGE_REWARD_RATIO": 0.1,
                "SURVIVAL_TIME_REWARD": 0.1,
                "IDLE_PENALTY": -0.01,
            },
        }
        self._write_json(output_dir / "constants.json", constants)

    def _generate_damage_types(self, output_dir: Path) -> None:
        """Generate damage_types.json."""
        damage_types = {
            "bullet": {"name": "Bullet", "description": "Standard bullet damage"},
            "melee": {"name": "Melee", "description": "Close range weapon damage"},
            "explosion": {"name": "Explosion", "description": "Area explosion damage"},
            "burn": {"name": "Burn", "description": "Fire damage over time"},
            "poison": {"name": "Poison", "description": "Damage over time"},
            "true": {"name": "True", "description": "Ignores armor and shields"},
            "fall": {"name": "Fall", "description": "Fall damage"},
        }
        self._write_json(output_dir / "damage_types.json", damage_types)

    def _generate_effects(self, output_dir: Path) -> None:
        """Generate effects.json."""
        effects = {
            "stun": {"name": "Stun", "duration": 1.0, "type": "control"},
            "slow": {"name": "Slow", "duration": 2.0, "speed_modifier": 0.5, "type": "debuff"},
            "speed_boost": {"name": "Speed Boost", "duration": 3.0, "speed_modifier": 1.5, "type": "buff"},
            "damage_boost": {"name": "Damage Boost", "duration": 5.0, "damage_modifier": 1.25, "type": "buff"},
            "invulnerable": {"name": "Invulnerable", "duration": 2.0, "type": "buff"},
            "invisible": {"name": "Invisible", "duration": 3.0, "type": "buff"},
            "burning": {"name": "Burning", "duration": 3.0, "damage_per_second": 10.0, "type": "dot"},
            "poisoned": {"name": "Poisoned", "duration": 5.0, "damage_per_second": 5.0, "type": "dot"},
            "frozen": {"name": "Frozen", "duration": 1.5, "type": "control"},
            "blind": {"name": "Blind", "duration": 2.0, "type": "debuff"},
        }
        self._write_json(output_dir / "effects.json", effects)

    def _generate_buffs(self, output_dir: Path) -> None:
        """Generate buffs.json."""
        buffs = {
            "health_regen": {
                "name": "Health Regeneration",
                "type": "regen",
                "healing_per_second": 5.0,
            },
            "shield_regen": {
                "name": "Shield Regeneration",
                "type": "regen",
                "shield_per_second": 2.0,
            },
            "energy_regen": {
                "name": "Energy Regeneration",
                "type": "regen",
                "energy_per_second": 3.0,
            },
            "damage_boost": {
                "name": "Damage Boost",
                "type": "buff",
                "damage_modifier": 1.25,
            },
            "speed_boost": {
                "name": "Speed Boost",
                "type": "buff",
                "speed_modifier": 1.5,
            },
            "armor_boost": {
                "name": "Armor Boost",
                "type": "buff",
                "armor_modifier": 1.5,
            },
        }
        self._write_json(output_dir / "buffs.json", buffs)

    def _generate_loot(self, output_dir: Path) -> None:
        """Generate loot.json."""
        loot = {
            "weapon_common": {
                "name": "Common Weapon",
                "type": "weapon",
                "rarity": "common",
                "stats_multiplier": 1.0,
            },
            "weapon_rare": {
                "name": "Rare Weapon",
                "type": "weapon",
                "rarity": "rare",
                "stats_multiplier": 1.25,
            },
            "weapon_epic": {
                "name": "Epic Weapon",
                "type": "weapon",
                "rarity": "epic",
                "stats_multiplier": 1.5,
            },
            "weapon_legendary": {
                "name": "Legendary Weapon",
                "type": "weapon",
                "rarity": "legendary",
                "stats_multiplier": 2.0,
            },
            "health_pack": {
                "name": "Health Pack",
                "type": "consumable",
                "healing": 50.0,
            },
            "shield_potion": {
                "name": "Shield Potion",
                "type": "consumable",
                "shield": 25.0,
            },
            "speed_boost": {
                "name": "Speed Boost",
                "type": "buff",
                "duration": 5.0,
            },
        }
        self._write_json(output_dir / "loot.json", loot)

    def _generate_movement(self, output_dir: Path) -> None:
        """Generate movement.json."""
        movement = {
            "walk": {"speed": 300.0, "acceleration": 1000.0, "deceleration": 2000.0},
            "sprint": {"speed": 450.0, "acceleration": 800.0, "deceleration": 1500.0},
            "dash": {"speed": 1000.0, "duration": 0.2, "cooldown": 3.0},
            "jump": {"force": 400.0, "gravity": 980.0, "air_control": 0.5},
            "crouch": {"speed_modifier": 0.5, "hitbox_shrink": 0.5},
        }
        self._write_json(output_dir / "movement.json", movement)

    def _generate_animations(self, output_dir: Path) -> None:
        """Generate animations.json."""
        animations = {
            "idle": {"duration": 1.0, "loop": True},
            "walk": {"duration": 0.5, "loop": True},
            "run": {"duration": 0.3, "loop": True},
            "jump": {"duration": 0.4, "loop": False},
            "fall": {"duration": 0.3, "loop": True},
            "attack": {"duration": 0.2, "loop": False},
            "skill": {"duration": 0.5, "loop": False},
            "death": {"duration": 1.0, "loop": False},
            "respawn": {"duration": 1.5, "loop": False},
        }
        self._write_json(output_dir / "animations.json", animations)

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        """Write data to JSON file."""
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert name to snake_case."""
        result = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        return re.sub(r"_+/", "_", result).strip("_")

    @staticmethod
    def _infer_weapon_type(name: str) -> str:
        """Infer weapon type from name."""
        name_lower = name.lower()
        if "pistol" in name_lower:
            return "pistol"
        elif "rifle" in name_lower:
            return "rifle"
        elif "shotgun" in name_lower:
            return "shotgun"
        elif "sniper" in name_lower:
            return "sniper"
        elif "smg" in name_lower:
            return "smg"
        elif "rocket" in name_lower or "launcher" in name_lower:
            return "explosive"
        elif "melee" in name_lower or "sword" in name_lower:
            return "melee"
        return "rifle"

    @staticmethod
    def _infer_skill_type(name: str) -> str:
        """Infer skill type from name."""
        name_lower = name.lower()
        if "heal" in name_lower or "health" in name_lower:
            return "heal"
        elif "shield" in name_lower or "protect" in name_lower:
            return "shield"
        elif "dash" in name_lower or "blink" in name_lower:
            return "dash"
        elif "ultimate" in name_lower or "super" in name_lower:
            return "ultimate"
        elif "aoe" in name_lower or "area" in name_lower:
            return "aoe"
        elif "passive" in name_lower:
            return "passive"
        return "active"

    @staticmethod
    def _infer_skill_category(name: str) -> str:
        """Infer skill category from name."""
        name_lower = name.lower()
        if "ultimate" in name_lower:
            return "ultimate"
        elif "passive" in name_lower:
            return "passive"
        elif "support" in name_lower:
            return "support"
        return "normal"

    @staticmethod
    def _infer_projectile_type(name: str) -> str:
        """Infer projectile type from name."""
        name_lower = name.lower()
        if "bullet" in name_lower:
            return "bullet"
        elif "rocket" in name_lower or "missile" in name_lower:
            return "rocket"
        elif "arrow" in name_lower:
            return "arrow"
        elif "energy" in name_lower:
            return "energy"
        elif "grenade" in name_lower or "bomb" in name_lower:
            return "grenade"
        return "bullet"
