"""
AI Registry Package

Provides agent registry for managing and instantiating AI agents.
"""

from zbgym.ai.registry.registry import (
    AIRegistry,
    get_global_registry,
    register_agent,
    create_agent,
)

__all__ = ["AIRegistry", "get_global_registry", "register_agent", "create_agent"]
