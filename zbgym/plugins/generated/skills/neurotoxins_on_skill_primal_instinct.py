"""Auto-generated skill plugin: NeurotoxinsOnSkillPrimalInstinct."""

from zbgym.physics.vector import Vector2D
from zbgym.plugins.skill import Skill, SkillConfig, SkillType, register_skill


@register_skill(
    "neurotoxins_on_skill_primal_instinct",
    "NeurotoxinsOnSkillPrimalInstinct",
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
class NeurotoxinsOnSkillPrimalInstinctSkill(Skill):
    """Skill plugin for NeurotoxinsOnSkillPrimalInstinct."""

    def _apply_effects(self, target: Vector2D | None) -> None:
        # TODO: Implement skill effects based on dump.cs data
        pass
