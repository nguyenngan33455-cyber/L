"""
ZBGym Quickstart Example

This example demonstrates how to use ZBGym for Reinforcement Learning training.
"""

import numpy as np
import zbgym
from zbgym.plugins.character import CharacterStats, register_character, create_character
from zbgym.plugins.weapon import create_weapon
from zbgym.physics.vector import Vector2D


def main():
    print("=" * 60)
    print("ZBGym Quickstart Example")
    print("=" * 60)

    # Register a custom character
    @register_character("warrior", "Warrior", CharacterStats(
        max_health=150,
        max_shield=30,
        move_speed=350,
    ))
    class WarriorCharacter(zbgym.plugins.Character):
        pass

    print("\n1. Creating ZBGym Environment")
    print("-" * 40)
    env = zbgym.make("BattleArena-v1")
    print(f"   Environment: {type(env).__name__}")
    print(f"   Observation space: {env.observation_space}")
    print(f"   Action space: {env.action_space}")

    print("\n2. Resetting Environment")
    print("-" * 40)
    obs, info = env.reset(seed=42)
    print(f"   Observation shape: {obs.shape}")
    print(f"   Info keys: {list(info.keys())}")
    print(f"   Alive agents: {info.get('alive_agents', 0)}")

    print("\n3. Running Random Agent")
    print("-" * 40)
    total_reward = 0
    for step in range(10):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        print(f"   Step {step + 1}: reward={reward:.4f}, alive={info.get('alive_agents', 0)}")
        if terminated or truncated:
            break

    print(f"\n   Total reward: {total_reward:.4f}")

    print("\n4. Creating Characters and Weapons")
    print("-" * 40)
    char = create_character("warrior", "player_1", team="red")
    print(f"   Character: {char.__class__.__name__}")
    print(f"   Health: {char.health}/{char.config.stats.max_health}")
    print(f"   Shield: {char.shield}/{char.config.stats.max_shield}")

    weapon = create_weapon("rifle", owner_id="player_1")
    print(f"\n   Weapon: {weapon.metadata.name}")
    print(f"   Ammo: {weapon.current_ammo}/{weapon.config.stats.magazine_size}")

    # Fire weapon
    projectiles = weapon.fire(Vector2D(0, 0), Vector2D(1, 0))
    print(f"   Projectiles fired: {len(projectiles)}")
    print(f"   Ammo remaining: {weapon.current_ammo}")

    print("\n5. Testing Combat")
    print("-" * 40)
    # Deal damage
    result = char.take_damage(100, "enemy_1")
    print(f"   Took 100 damage: {result:.1f} to health")
    print(f"   Health: {char.health:.1f}/{char.config.stats.max_health}")
    print(f"   Shield: {char.shield:.1f}/{char.config.stats.max_shield}")

    # Heal
    heal_amount = char.heal(50)
    print(f"\n   Healed for: {heal_amount:.1f}")
    print(f"   Health: {char.health:.1f}/{char.config.stats.max_health}")

    print("\n6. Running Full Episode")
    print("-" * 40)
    obs, _ = env.reset()
    episode_reward = 0
    steps = 0

    while True:
        # Simple policy: random actions
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        episode_reward += reward
        steps += 1

        if terminated or truncated:
            break

    print(f"   Episode completed in {steps} steps")
    print(f"   Total reward: {episode_reward:.4f}")
    print(f"   Final info: alive={info.get('alive_agents', 0)}, tick={info.get('tick', 0)}")

    env.close()

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
