# Plugin Guide

ZBGym uses a plugin-based architecture that allows you to extend the framework with custom characters, weapons, skills, observations, and rewards.

## Plugin Registry

All plugins are registered through registries that maintain a mapping from plugin IDs to plugin classes.

```python
from zbgym.plugins.character import character_registry
from zbgym.plugins.weapon import weapon_registry
from zbgym.plugins.skill import skill_registry
from zbgym.observation import observation_registry
from zbgym.reward import reward_registry
```

## Character Plugins

### Base Character

```python
from zbgym.plugins.character import Character, CharacterStats

class MyCharacter(Character):
    def __init__(self, character_id, team, **kwargs):
        super().__init__(character_id, team, **kwargs)
        # Custom initialization
```

### Character Stats

```python
@dataclass
class CharacterStats:
    max_health: float = 100.0
    max_shield: float = 50.0
    max_energy: float = 100.0
    move_speed: float = 300.0
    sprint_speed: float = 450.0
    jump_force: float = 400.0
    armor: float = 0.0
    vision_range: float = 500.0
    base_damage: float = 10.0
    critical_chance: float = 0.05
    critical_multiplier: float = 1.5
    headshot_multiplier: float = 2.0
```

### Registration

```python
from zbgym.plugins.character import register_character

@register_character(
    "hero",
    "Hero",
    CharacterStats(
        max_health=150,
        max_shield=30,
        move_speed=350,
        base_damage=12.0,
    ),
    abilities=[
        Ability(id="Q", name="Skill Shot", ...),
        Ability(id="E", name="Dash", ...),
    ],
    description="A balanced hero with high damage"
)
class HeroCharacter(Character):
    pass
```

## Weapon Plugins

### Base Weapon

```python
from zbgym.plugins.weapon import Weapon, WeaponStats, WeaponType

class MyWeapon(Weapon):
    def __init__(self, owner_id, **kwargs):
        super().__init__(owner_id, **kwargs)
        # Custom initialization
```

### Weapon Types

```python
class WeaponType(Enum):
    MELEE = "melee"
    PISTOL = "pistol"
    RIFLE = "rifle"
    SHOTGUN = "shotgun"
    SNIPER = "sniper"
    SMG = "smg"
    LAUNCHER = "launcher"
    ENERGY = "energy"
```

### Weapon Stats

```python
@dataclass
class WeaponStats:
    damage: float = 10.0
    fire_rate: float = 1.0  # shots per second
    magazine_size: int = 30
    reload_time: float = 2.0
    spread: float = 0.0
    projectile_speed: float = 1000.0
    range: float = 500.0
    armor_penetration: float = 0.0
    critical_chance: float = 0.0
```

### Registration

```python
from zbgym.plugins.weapon import register_weapon

@register_weapon(
    "laser_rifle",
    "Laser Rifle",
    WeaponType.ENERGY,
    WeaponStats(
        damage=30.0,
        fire_rate=5.0,
        magazine_size=40,
        reload_time=3.0,
        projectile_speed=2000.0,
        range=600.0,
    )
)
class LaserRifle(Weapon):
    pass
```

## Skill Plugins

### Base Skill

```python
from zbgym.plugins.skill import Skill, SkillType, SkillConfig

class MySkill(Skill):
    def __init__(self, owner_id, **kwargs):
        super().__init__(owner_id, **kwargs)
        # Custom initialization
    
    def execute(self, target_position=None):
        # Custom execution logic
        pass
```

### Skill Types

```python
class SkillType(Enum):
    DAMAGE = "damage"
    HEAL = "heal"
    SHIELD = "shield"
    MOVEMENT = "movement"
    BUFF = "buff"
    DEBUFF = "debuff"
    ULTIMATE = "ultimate"
```

### Skill Config

```python
@dataclass
class SkillConfig:
    cooldown: float = 10.0
    energy_cost: float = 0.0
    range: float = 100.0
    radius: float = 0.0
    duration: float = 0.0
    damage: float = 0.0
    healing: float = 0.0
```

### Registration

```python
from zbgym.plugins.skill import register_skill

@register_skill(
    "freeze",
    "Freeze",
    SkillType.DEBUFF,
    SkillConfig(
        cooldown=20.0,
        energy_cost=40.0,
        range=150.0,
        radius=50.0,
        duration=3.0,
        damage=50.0,
    ),
    description="Freeze enemies in an area"
)
class FreezeSkill(Skill):
    pass
```

## Observation Plugins

### Base Observation

```python
from zbgym.observation import Observation, ObservationConfig

class MyObservation(Observation):
    def __init__(self, config=None):
        self.config = config or ObservationConfig()
        self._names = ["custom_obs_1", "custom_obs_2"]
    
    @property
    def names(self) -> list[str]:
        return self._names
    
    def get_dimension(self) -> int:
        return len(self._names)
    
    def compute(self, state):
        # Compute observation values
        return np.array([...])
```

### Registration

```python
from zbgym.observation import observation_registry

observation_registry.register("my_observation", MyObservation)
```

## Reward Plugins

### Base Reward

```python
from zbgym.reward import Reward, RewardConfig

class MyReward(Reward):
    def __init__(self, config=None):
        self.config = config or RewardConfig()
    
    def compute(self, state, prev_state=None):
        # Compute reward
        return reward_value
```

### Registration

```python
from zbgym.reward import reward_registry

reward_registry.register("my_reward", MyReward)
```

## Using Custom Plugins

### In Code

```python
import zbgym

# Create character with custom plugin
char = create_character("hero", "player_1", team="red")

# Create weapon with custom plugin
weapon = create_weapon("laser_rifle", owner_id="player_1")

# Use in environment
env = zbgym.make("BattleArena-v1")
obs, info = env.reset()
```

### In Configuration

```yaml
# config/train.yaml
plugins:
  characters:
    - hero
  weapons:
    - laser_rifle
  skills:
    - freeze

observation:
  types:
    - health
    - position
    - enemies
    - my_observation

reward:
  types:
    - survival
    - kill
    - my_reward
  weights:
    survival: 1.0
    kill: 1.0
    my_reward: 0.5
```

## CLI Commands

```bash
# List all plugins
zbgym plugins

# List specific type
zbgym plugins --type character
zbgym plugins --type weapon
zbgym plugins --type skill
```

## Best Practices

1. **Unique IDs**: Use unique, descriptive IDs for your plugins
2. **Documentation**: Document your plugins with descriptions
3. **Testing**: Write tests for your custom plugins
4. **Configuration**: Make values configurable via SkillConfig, WeaponStats, etc.
5. **Events**: Use EventBus for communication between plugins
6. **Validation**: Validate inputs in your plugins
