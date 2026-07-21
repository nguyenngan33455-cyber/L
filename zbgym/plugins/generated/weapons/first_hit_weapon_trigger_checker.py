"""Auto-generated weapon plugin: FirstHitWeaponTriggerChecker."""

from zbgym.plugins.weapon import Weapon, WeaponStats, WeaponType, register_weapon


@register_weapon(
    "first_hit_weapon_trigger_checker",
    "FirstHitWeaponTriggerChecker",
    WeaponType.RIFLE,
    WeaponStats(
        damage=10.0,
        fire_rate=10.0,
        magazine_size=30,
        total_ammo=120,
        reload_time=2.0,
        spread=0.0,
        recoil=0.0,
        range=1000.0,
        projectile_speed=1000.0,
        projectile_count=1,
        explosion_radius=0.0,
        explosion_damage=0.0,
        critical_chance=0.05,
        critical_multiplier=1.5,
        headshot_multiplier=2.0,
        penetration=0,
        ricochet=0,
        min_damage_ratio=0.5,
        max_damage_distance=500.0,
    ),
    description="Auto-generated from dump.cs",
)
class FirstHitWeaponTriggerChecker(Weapon):
    """Weapon plugin for FirstHitWeaponTriggerChecker."""
