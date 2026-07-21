"""Auto-generated character plugin: Bat."""

from zbgym.plugins.character import Character, CharacterStats, register_character


@register_character(
    "bat",
    "Bat",
    CharacterStats(
        max_health=100.0,
        max_shield=50.0,
        max_energy=100.0,
        move_speed=300.0,
        sprint_speed=450.0,
        jump_force=400.0,
        armor=0.0,
        vision_range=500.0,
        base_damage=10.0,
        critical_chance=0.05,
        critical_multiplier=1.5,
        headshot_multiplier=2.0,
    ),
    description="Auto-generated from dump.cs",
)
class BatCharacter(Character):
    """Character plugin for Bat."""
