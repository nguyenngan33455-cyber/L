"""
AI Targeting Package

Provides target selection systems.
Used by agents to select targets based on various criteria.

Components:
- TargetSelector: Base target selection
- PriorityTargeting: Priority-based targeting
- NearestTargeting: Target nearest enemy
- HealthTargeting: Target lowest/highest health
- ThreatTargeting: Target most dangerous threat
"""

from zbgym.ai.targeting.selector import TargetSelector

__all__ = ["TargetSelector"]
