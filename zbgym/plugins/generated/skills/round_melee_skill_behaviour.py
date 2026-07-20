"""Auto-generated skill plugin: RoundMeleeSkillBehaviour."""

from zbgym.plugins.skill import Skill, SkillConfig, SkillType, register_skill
from zbgym.physics.vector import Vector2D


@register_skill(
    "round_melee_skill_behaviour",
    "RoundMeleeSkillBehaviour",
    SkillType.ACTIVE,
    SkillConfig(
        cooldown=5.0,
        energy_cost=0.0,
        cast_time=0.0,
        channel_duration=0.0,
        damage=0.0,
        healing=0.0,
        shield_amount=0.0,
        speed_modifier=1.0,
        duration=0.0,
        range=0.0,
        area_radius=0.0,
    ),
    description="Auto-generated from dump.cs",
)
class RoundMeleeSkillBehaviourSkill(Skill):
    """Skill plugin for RoundMeleeSkillBehaviour."""

    def _apply_effects(self, target: Vector2D | None) -> None:
        # TODO: Implement skill effects based on dump.cs data
        pass
