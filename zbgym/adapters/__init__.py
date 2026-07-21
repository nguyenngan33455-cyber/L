"""
ZBGym Adapters Package

This package provides adapters that bridge game-specific implementations
to the generic ZBGym interface layer.

Example:
    >>> from zbgym.adapters import AdapterFactory
    >>> 
    >>> adapter = AdapterFactory.create('BattleArena-v1')
    >>> state = adapter.get_game_state()
"""

from zbgym.adapters.factory import AdapterFactory
from zbgym.adapters.battle_arena import (
    BattleArenaAdapter,
    BattleArenaGameState,
    BattleArenaPlayer,
    BattleArenaTeam,
    BattleArenaZone,
    BattleArenaMap,
)

__all__ = [
    "AdapterFactory",
    "BattleArenaAdapter",
    "BattleArenaGameState",
    "BattleArenaPlayer",
    "BattleArenaTeam",
    "BattleArenaZone",
    "BattleArenaMap",
]

__version__ = "0.1.0"
