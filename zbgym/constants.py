"""Constants used throughout ZBGym."""

from enum import Enum
from typing import Final


# Physics constants
DEFAULT_GRAVITY: Final[float] = 980.0  # pixels/s^2
DEFAULT_FRICTION: Final[float] = 0.98
DEFAULT_AIR_RESISTANCE: Final[float] = 0.99
DEFAULT_MAX_SPEED: Final[float] = 500.0  # pixels/s
DEFAULT_DASH_SPEED: Final[float] = 1000.0
DEFAULT_JUMP_FORCE: Final[float] = 400.0

# Game constants
DEFAULT_TICK_RATE: Final[int] = 60  # Hz
DEFAULT_FRAME_RATE: Final[int] = 30  # FPS for rendering
MAX_ENTITIES: Final[int] = 100
MAX_PROJECTILES: Final[int] = 500
MAX_ITEMS: Final[int] = 200

# Arena constants
DEFAULT_ARENA_WIDTH: Final[int] = 2000
DEFAULT_ARENA_HEIGHT: Final[int] = 1500
SAFE_ZONE_SHRINK_RATE: Final[float] = 0.5  # units per second

# Character constants
MAX_HEALTH: Final[int] = 100
MAX_SHIELD: Final[int] = 50
MAX_ENERGY: Final[int] = 100
START_AMMO: Final[int] = 30
MAX_AMMO: Final[int] = 120
RESPAWN_TIME: Final[float] = 5.0  # seconds

# Combat constants
HEADSHOT_MULTIPLIER: Final[float] = 1.5
CRITICAL_MULTIPLIER: Final[float] = 1.25
MAX_DAMAGE_DISTANCE: Final[float] = 1000.0
MIN_DAMAGE_RATIO: Final[float] = 0.5

# Reward constants
KILL_REWARD: Final[float] = 10.0
ASSIST_REWARD: Final[float] = 3.0
DEATH_PENALTY: Final[float] = -5.0
DAMAGE_REWARD_RATIO: Final[float] = 0.1
SURVIVAL_TIME_REWARD: Final[float] = 0.1
IDLE_PENALTY: Final[float] = -0.01


class GameMode(str, Enum):
    """Game modes available in ZBGym."""

    DEATHMATCH = "deathmatch"
    TEAM_DEATHMATCH = "team_deathmatch"
    FREE_FOR_ALL = "free_for_all"
    CAPTURE_THE_FLAG = "ctf"
    SURVIVAL = "survival"


class Team(str, Enum):
    """Team identifiers."""

    NONE = "none"
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"


class DamageType(str, Enum):
    """Types of damage in the game."""

    BULLET = "bullet"
    MELEE = "melee"
    EXPLOSION = "explosion"
    BURN = "burn"
    POISON = "poison"
    TRUE = "true"
    FALL = "fall"


class WeaponType(str, Enum):
    """Categories of weapons."""

    RIFLE = "rifle"
    SHOTGUN = "shotgun"
    SNIPER = "sniper"
    SMG = "smg"
    PISTOL = "pistol"
    MELEE = "melee"
    EXPLOSIVE = "explosive"


class SkillType(str, Enum):
    """Categories of skills."""

    PROJECTILE = "projectile"
    DASH = "dash"
    AOE = "aoe"
    HEAL = "heal"
    SHIELD = "shield"
    TRAP = "trap"
    BUFF = "buff"
    DEBUFF = "debuff"
    ULTIMATE = "ultimate"


class StatusEffectType(str, Enum):
    """Types of status effects."""

    STUN = "stun"
    SLOW = "slow"
    SPEED_BOOST = "speed_boost"
    DAMAGE_BOOST = "damage_boost"
    INVULNERABLE = "invulnerable"
    INVISIBLE = "invisible"
    BURNING = "burning"
    POISONED = "poisoned"
    FROZEN = "frozen"
    BLIND = "blind"


class EntityType(str, Enum):
    """Types of entities in the game."""

    CHARACTER = "character"
    PROJECTILE = "projectile"
    ITEM = "item"
    TRAP = "trap"
    OBSTACLE = "obstacle"
    EFFECT = "effect"


class EventType(str, Enum):
    """Event types for the event bus."""

    CHARACTER_SPAWN = "character_spawn"
    CHARACTER_DEATH = "character_death"
    CHARACTER_DAMAGE = "character_damage"
    CHARACTER_HEAL = "character_heal"
    PROJECTILE_FIRE = "projectile_fire"
    PROJECTILE_HIT = "projectile_hit"
    PROJECTILE_DESTROY = "projectile_destroy"
    SKILL_USE = "skill_use"
    SKILL_ACTIVATE = "skill_activate"
    ITEM_PICKUP = "item_pickup"
    ITEM_DROP = "item_drop"
    ZONE_SHRINK = "zone_shrink"
    MATCH_START = "match_start"
    MATCH_END = "match_end"
    ROUND_START = "round_start"
    ROUND_END = "round_end"
