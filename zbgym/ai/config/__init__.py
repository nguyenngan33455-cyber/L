"""
AI Configuration Package

Provides configuration classes for AI agents and systems.
"""

from dataclasses import dataclass, field
from typing import Any

from zbgym.ai.config.base_config import AIConfig
from zbgym.ai.config.agent_config import AgentConfig

__all__ = ["AIConfig", "AgentConfig"]
