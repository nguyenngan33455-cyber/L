#!/usr/bin/env python3
"""
Update the entire simulator from dump.cs.

This is the main workflow script that:
1. Parses dump.cs
2. Generates JSON databases
3. Generates plugin code
4. Validates the output

Usage:
    python -m tools.update_game [--dump DUMP_PATH] [--output OUTPUT_DIR]

Workflow:
    Replace dump.cs
         ↓
    Run update_game.py
         ↓
    Everything regenerates automatically.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser(
        description="Update ZBGym from dump.cs - regenerates all data and plugins"
    )
    parser.add_argument(
        "--dump",
        "-d",
        default="dump/dump.cs",
        help="Path to dump.cs file (default: dump/dump.cs)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="zbgym/data",
        help="Output directory for generated files (default: zbgym/data)",
    )
    parser.add_argument(
        "--plugins",
        "-p",
        default="zbgym/plugins/generated",
        help="Output directory for generated plugins (default: zbgym/plugins/generated)",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validation step",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    dump_path = Path(args.dump)
    if not dump_path.exists():
        print(f"Error: dump.cs not found at {dump_path}")
        print("Please place your updated dump.cs file in the dump/ directory")
        sys.exit(1)

    output_dir = Path(args.output)
    plugins_dir = Path(args.plugins)

    print("=" * 60)
    print("ZBGym Update Game Script")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Dump path: {dump_path}")
    print(f"Output dir: {output_dir}")
    print(f"Plugins dir: {plugins_dir}")
    print("=" * 60)

    # Step 1: Parse dump.cs
    print("\n[1/4] Parsing dump.cs...")
    from zbgym.dump.compiler import Compiler

    compiler = Compiler(str(dump_path))
    ir = compiler.compile()

    # Step 2: Generate JSON databases
    print("\n[2/4] Generating JSON databases...")
    output_dir.mkdir(parents=True, exist_ok=True)
    compiler.generate_json_databases(output_dir)
    print(f"  Generated in {output_dir}")

    # Step 3: Generate plugins
    print("\n[3/4] Generating plugin code...")
    plugins_dir.mkdir(parents=True, exist_ok=True)
    _generate_plugins(ir, plugins_dir, args.verbose)
    print(f"  Generated in {plugins_dir}")

    # Step 4: Validation
    if not args.skip_validation:
        print("\n[4/4] Validating generated files...")
        _validate_output(output_dir, plugins_dir)
    else:
        print("\n[4/4] Validation skipped")

    # Summary
    print("\n" + "=" * 60)
    print("Update Complete!")
    print("=" * 60)
    print("\nGenerated files:")
    print(f"  - JSON databases: {output_dir}")
    print(f"  - Plugin code: {plugins_dir}")
    print("\nNext steps:")
    print("  1. Review generated JSON files")
    print("  2. Update any hardcoded values if needed")
    print("  3. Run tests: pytest tests/")
    print("  4. Run the simulator: zbgym train")


def _generate_plugins(ir, plugins_dir: Path, verbose: bool = False) -> None:
    """Generate plugin code from IR."""
    # Generate character plugins
    char_dir = plugins_dir / "characters"
    char_dir.mkdir(parents=True, exist_ok=True)

    for char_id, char in ir.characters.items():
        _generate_character_plugin(char, char_dir, verbose)

    # Generate weapon plugins
    weapon_dir = plugins_dir / "weapons"
    weapon_dir.mkdir(parents=True, exist_ok=True)

    for weapon_id, weapon in ir.weapons.items():
        _generate_weapon_plugin(weapon, weapon_dir, verbose)

    # Generate skill plugins
    skill_dir = plugins_dir / "skills"
    skill_dir.mkdir(parents=True, exist_ok=True)

    for skill_id, skill in ir.skills.items():
        _generate_skill_plugin(skill, skill_dir, verbose)

    # Generate __init__.py files
    _generate_init_file(char_dir)
    _generate_init_file(weapon_dir)
    _generate_init_file(skill_dir)

    # Generate registry
    _generate_registry(ir, plugins_dir)


def _generate_character_plugin(char, output_dir: Path, verbose: bool = False) -> None:
    """Generate a character plugin file."""
    class_name = "".join(word.capitalize() for word in char.id.split("_"))

    content = f'''"""Auto-generated character plugin: {char.name}."""

from zbgym.plugins.character import Character, CharacterStats, register_character


@register_character(
    "{char.id}",
    "{char.name}",
    CharacterStats(
        max_health={char.max_health},
        max_shield={char.max_shield},
        max_energy={char.max_energy},
        move_speed={char.move_speed},
        sprint_speed={char.sprint_speed},
        jump_force={char.jump_force},
        armor={char.armor},
        vision_range={char.vision_range},
        base_damage={char.base_damage},
        critical_chance={char.critical_chance},
        critical_multiplier={char.critical_multiplier},
        headshot_multiplier={char.headshot_multiplier},
    ),
    description="Auto-generated from dump.cs",
)
class {class_name}Character(Character):
    """Character plugin for {char.name}."""

    pass
'''

    output_path = output_dir / f"{char.id}.py"
    with open(output_path, "w") as f:
        f.write(content)

    if verbose:
        print(f"  Generated character: {char.id}")


def _generate_weapon_plugin(weapon, output_dir: Path, verbose: bool = False) -> None:
    """Generate a weapon plugin file."""
    class_name = "".join(word.capitalize() for word in weapon.id.split("_"))

    content = f'''"""Auto-generated weapon plugin: {weapon.name}."""

from zbgym.plugins.weapon import Weapon, WeaponStats, WeaponType, register_weapon


@register_weapon(
    "{weapon.id}",
    "{weapon.name}",
    WeaponType.{weapon.weapon_type.upper()},
    WeaponStats(
        damage={weapon.damage},
        fire_rate={weapon.fire_rate},
        magazine_size={weapon.magazine_size},
        total_ammo={weapon.total_ammo},
        reload_time={weapon.reload_time},
        spread={weapon.spread},
        recoil={weapon.recoil},
        range={weapon.range},
        projectile_speed={weapon.projectile_speed},
        projectile_count={weapon.projectile_count},
        explosion_radius={weapon.explosion_radius},
        explosion_damage={weapon.explosion_damage},
        critical_chance={weapon.critical_chance},
        critical_multiplier={weapon.critical_multiplier},
        headshot_multiplier={weapon.headshot_multiplier},
        penetration={weapon.penetration},
        ricochet={weapon.ricochet},
        min_damage_ratio={weapon.min_damage_ratio},
        max_damage_distance={weapon.max_damage_distance},
    ),
    description="Auto-generated from dump.cs",
)
class {class_name}(Weapon):
    """Weapon plugin for {weapon.name}."""

    pass
'''

    output_path = output_dir / f"{weapon.id}.py"
    with open(output_path, "w") as f:
        f.write(content)

    if verbose:
        print(f"  Generated weapon: {weapon.id}")


def _generate_skill_plugin(skill, output_dir: Path, verbose: bool = False) -> None:
    """Generate a skill plugin file."""
    class_name = "".join(word.capitalize() for word in skill.id.split("_"))

    skill_type = skill.skill_type.upper() if hasattr(skill, "skill_type") else "ACTIVE"

    content = f'''"""Auto-generated skill plugin: {skill.name}."""

from zbgym.plugins.skill import Skill, SkillConfig, SkillType, register_skill
from zbgym.physics.vector import Vector2D


@register_skill(
    "{skill.id}",
    "{skill.name}",
    SkillType.{skill_type},
    SkillConfig(
        cooldown={skill.cooldown},
        energy_cost={skill.energy_cost},
        cast_time={skill.cast_time},
        channel_duration={skill.channel_duration},
        damage={skill.damage},
        healing={skill.healing},
        shield_amount={skill.shield_amount},
        speed_modifier={skill.speed_modifier},
        duration={skill.duration},
        range={skill.range},
        area_radius={skill.area_radius},
    ),
    description="Auto-generated from dump.cs",
)
class {class_name}Skill(Skill):
    """Skill plugin for {skill.name}."""

    def _apply_effects(self, target: Vector2D | None) -> None:
        # TODO: Implement skill effects based on dump.cs data
        pass
'''

    output_path = output_dir / f"{skill.id}.py"
    with open(output_path, "w") as f:
        f.write(content)

    if verbose:
        print(f"  Generated skill: {skill.id}")


def _generate_init_file(output_dir: Path) -> None:
    """Generate __init__.py for a plugin directory."""
    init_path = output_dir / "__init__.py"

    # Find all .py files except __init__.py
    py_files = [f.stem for f in output_dir.glob("*.py") if f.stem != "__init__"]

    content = '''"""Auto-generated plugins."""

# Auto-generated plugins from dump.cs
'''

    with open(init_path, "w") as f:
        f.write(content)


def _generate_registry(ir, output_dir: Path) -> None:
    """Generate a registry summary file."""
    registry = {
        "generated_at": datetime.now().isoformat(),
        "characters": list(ir.characters.keys()),
        "weapons": list(ir.weapons.keys()),
        "skills": list(ir.skills.keys()),
        "projectiles": list(ir.projectiles.keys()),
        "maps": list(ir.maps.keys()),
    }

    registry_path = output_dir / "registry.json"
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def _validate_output(data_dir: Path, plugins_dir: Path) -> None:
    """Validate generated output."""
    errors = []
    warnings = []

    # Check required JSON files
    required_files = [
        "characters.json",
        "weapons.json",
        "skills.json",
        "projectiles.json",
        "maps.json",
        "constants.json",
        "damage_types.json",
        "effects.json",
        "buffs.json",
        "loot.json",
        "movement.json",
        "animations.json",
    ]

    for filename in required_files:
        filepath = data_dir / filename
        if not filepath.exists():
            errors.append(f"Missing required file: {filename}")
        else:
            # Try to load JSON
            try:
                with open(filepath) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON in {filename}: {e}")

    # Check plugin directories
    for subdir in ["characters", "weapons", "skills"]:
        dir_path = plugins_dir / subdir
        if not dir_path.exists():
            warnings.append(f"Plugin directory not found: {subdir}")
        elif not list(dir_path.glob("*.py")):
            warnings.append(f"No plugins generated in: {subdir}")

    # Report
    if errors:
        print("\n  ERRORS:")
        for error in errors:
            print(f"    - {error}")
        sys.exit(1)

    if warnings:
        print("\n  WARNINGS:")
        for warning in warnings:
            print(f"    - {warning}")

    if not errors:
        print("  ✓ All validations passed")


if __name__ == "__main__":
    main()
