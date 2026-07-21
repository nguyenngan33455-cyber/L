# ZBGym Multi-Game Architecture Diagrams

## Diagram 1: Current Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CURRENT ARCHITECTURE                            │
│                     (BattleArena-Coupled)                               │
└─────────────────────────────────────────────────────────────────────────┘

                         ┌─────────────────┐
                         │     make()      │
                         │   (Entry API)   │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
         ┌─────────────────┐        ┌─────────────────┐
         │  BattleArena-v1 │        │    Zooba-v1     │
         │    (Direct)     │        │   (Adapter)     │
         └────────┬────────┘        └────────┬────────┘
                  │                          │
                  │         ┌─────────────────┘
                  │         │
                  ▼         ▼
         ┌─────────────────────────────────────────┐
         │            BattleArena                  │
         │  ┌─────────────────────────────────┐   │
         │  │       BattleArenaState          │   │
         │  │  - characters: Dict             │   │
         │  │  - zone: ZoneState             │   │
         │  │  - scores: Dict                │   │
         │  └─────────────────────────────────┘   │
         └─────────────────┬───────────────────────┘
                           │
     ┌─────────────────────┼─────────────────────┐
     │                     │                     │
     ▼                     ▼                     ▼
┌─────────────┐    ┌─────────────┐      ┌─────────────┐
│ Observation │    │    Reward   │      │   Plugins   │
│             │    │             │      │             │
│ • enemy.py  │    │ • combat.py │      │ • character │
│ • health.py│    │ • survival  │      │ • weapon.py │
│ • position │    │ • utility   │      │ • skill.py  │
└──────┬──────┘    └──────┬──────┘      └──────┬──────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │     Replay      │
                  │    Recorder     │
                  └─────────────────┘


TIGHT COUPLING:
  • All modules import BattleArenaState directly
  • Cannot support other game types without duplication
  • Hard to test modules in isolation
```

---

## Diagram 2: Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       TARGET ARCHITECTURE                                │
│                      (Multi-Game Capable)                               │
└─────────────────────────────────────────────────────────────────────────┘

                         ┌─────────────────┐
                         │     make()      │
                         │   (Entry API)   │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
         ┌─────────────────┐        ┌─────────────────┐
         │   GameAdapter   │        │   GameAdapter   │
         │  (Interface)   │        │  (Interface)    │
         └────────┬────────┘        └────────┬────────┘
                  │                          │
       ┌──────────┴──────────┐       ┌────────┴────────┐
       │                     │       │                 │
       ▼                     │       ▼                 │
┌─────────────────┐         │  ┌─────────────────┐   │
│ BattleArena     │         │  │   MOBAAttacker  │   │
│ Adapter         │         │  │   (Future)      │   │
└────────┬────────┘         │  └─────────────────┘   │
         │                 │                        │
         │    ┌────────────┴────────────┐            │
         │    │                         │            │
         ▼    ▼                         │            ▼
┌─────────────────────────────────┐    │   ┌─────────────────┐
│         GameState               │◄───┘   │  ShooterAdapter │
│  (Generic Interface)           │        │  (Future)      │
│                                │        └─────────────────┘
│  • entities: List[Entity]      │
│  • teams: List[Team]           │
│  • tick: int                   │
│  • elapsed_time: float         │
└─────────────────┬──────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐ ┌─────────┐ ┌─────────────┐
│Observa- │ │ Rewards │ │   Plugins   │
│tion     │ │         │ │             │
│         │ │         │ │             │
│Provider │ │Provider │ │  Provider   │
└────┬────┘ └────┬────┘ └──────┬──────┘
     │           │             │
     └───────────┴─────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │     Replay      │
        │   Provider      │
        └─────────────────┘


DECOUPLED:
  • GameState is generic interface
  • Adapters convert game-specific to generic
  • Observation/Reward work with any GameState
  • Easy to add new game types
```

---

## Diagram 3: Interface Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INTERFACE HIERARCHY                            │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────┐
                    │    <<ABC>>        │
                    │   GameState      │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │ BattleArena │  │   MOBAAttack│  │  Shooter    │
     │ GameState   │  │  GameState  │  │ GameState   │
     └─────────────┘  │  (Future)   │  │  (Future)   │
                      └─────────────┘  └─────────────┘


                    ┌───────────────────┐
                    │   <<Protocol>>    │
                    │     Entity       │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │   Player    │  │  Projectile │  │   Item      │
     │             │  │             │  │             │
     │ + health    │  │ + position  │  │ + position  │
     │ + team_id   │  │ + velocity  │  │ + type      │
     └──────┬──────┘  └─────────────┘  └─────────────┘
            │
            │ extends
            ▼
     ┌─────────────┐
     │   Team      │
     │             │
     │ + score     │
     │ + players   │
     └─────────────┘


                    ┌───────────────────┐
                    │   <<Protocol>>    │
                    │    Action        │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │  Movement   │  │   Ability   │  │   Target    │
     │   Action    │  │   Action    │  │   Action    │
     │             │  │             │  │             │
     │ + dx, dy    │  │ + ability_id│  │ + target_id │
     │             │  │ + target    │  │ + type      │
     └─────────────┘  └─────────────┘  └─────────────┘
```

---

## Diagram 4: Adapter Pattern

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ADAPTER PATTERN                                 │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         <<ABC>>                                         │
│                       GameAdapter                                       │
├─────────────────────────────────────────────────────────────────────────┤
│ + engine: GameEngine                                                    │
│ + observation_provider: ObservationProvider                             │
│ + reward_provider: RewardProvider                                       │
│ + replay_provider: ReplayProvider                                       │
├─────────────────────────────────────────────────────────────────────────┤
│ + get_game_state(): GameState                                          │
│ + set_game_state(state: GameState): None                               │
│ + get_observation(agent_id: str): np.ndarray                           │
│ + compute_reward(prev, current, agent_id): float                        │
└─────────────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ BattleArena     │ │    MOBA         │ │   Shooter       │
│ Adapter         │ │   Adapter       │ │   Adapter       │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ - _engine:      │ │ (Future)        │ │ (Future)        │
│   BattleArena   │ │                 │ │                 │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ + get_game_     │ │ + get_game_     │ │ + get_game_     │
│   state():      │ │   state():     │ │   state():     │
│   BattleArena   │ │   MOBAAttack    │ │   Shooter       │
│   GameState     │ │   GameState     │ │   GameState     │
└─────────────────┘ └─────────────────┘ └─────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                      AdapterFactory                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ _adapters: Dict[str, Type[GameAdapter]]                                │
├─────────────────────────────────────────────────────────────────────────┤
│ + register(env_id: str, adapter: Type[GameAdapter]): None              │
│ + create(env_id: str, **kwargs): GameAdapter                           │
│ + list_adapters(): List[str]                                          │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  Registered Adapters         │
              ├───────────────────────────────┤
              │  • BattleArena-v1 → BattleArenaAdapter  │
              │  • Zooba-v1 → ZoobaAdapter              │
              │  • (Future) Moba-v1 → MOBAAttackAdapter │
              │  • (Future) Shooter-v1 → ShooterAdapter  │
              └───────────────────────────────┘
```

---

## Diagram 5: Provider Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       PROVIDER ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     <<ABC>>                                             │
│                 ObservationProvider                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ + compute(state: GameState, agent_id: str) -> np.ndarray              │
│ + get_space() -> Space                                                 │
└─────────────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐     ┌───────────────┐
│   Enemy       │   │   Health     │     │   Position    │
│  Provider     │   │  Provider    │     │  Provider     │
├───────────────┤   ├───────────────┤     ├───────────────┤
│ Uses:         │   │ Uses:         │     │ Uses:         │
│ GameState     │   │ GameState     │     │ GameState     │
│ .entities     │   │ .entities     │     │ .entities     │
│ Player.health │   │ Player.team   │     │ Player.pos    │
└───────────────┘   └───────────────┘     └───────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                     <<ABC>>                                             │
│                   RewardProvider                                        │
├─────────────────────────────────────────────────────────────────────────┤
│ + compute(prev: GameState, curr: GameState, agent_id: str) -> float   │
│ + reset(): None                                                        │
└─────────────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐     ┌───────────────┐
│   Combat      │   │  Survival     │     │   Utility     │
│    Reward     │   │   Reward      │     │    Reward     │
├───────────────┤   ├───────────────┤     ├───────────────┤
│ • kill_reward │   │ • alive_reward│     │ • action_reg  │
│ • damage_mult │   │ • zone_damage │     │ • exploration │
└───────────────┘   └───────────────┘     └───────────────┘
```

---

## Diagram 6: Migration Stages

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MIGRATION STAGES                                │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: Interface Foundation (Week 1-2)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  zbgym/interfaces/                                          │        │
│  │  ├── __init__.py                                           │        │
│  │  ├── state.py      ←─── GameState, Entity, Player, Team    │        │
│  │  ├── action.py     ←─── Action protocols                   │        │
│  │  ├── vector.py     ←─── Vector interface                   │        │
│  │  ├── providers.py  ←─── Provider interfaces                 │        │
│  │  └── engine.py     ←─── GameEngine interface               │        │
│  └─────────────────────────────────────────────────────────────┘        │
│                                                                         │
│  EXISTING CODE: UNCHANGED                                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: BattleArena Adapter (Week 3-4)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  zbgym/adapters/                                           │        │
│  │  ├── __init__.py                                           │        │
│  │  ├── base.py          ←─── GameAdapter (ABC)               │        │
│  │  ├── factory.py       ←─── AdapterFactory                  │        │
│  │  └── battle_arena/                                          │        │
│  │      ├── __init__.py                                       │        │
│  │      ├── adapter.py     ←─── BattleArenaAdapter            │        │
│  │      └── state.py      ←─── BattleArenaGameState           │        │
│  └─────────────────────────────────────────────────────────────┘        │
│                                                                         │
│  EXISTING BattleArena: UNCHANGED                                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 3-4: Observation & Reward Decoupling (Week 5-8)                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  zbgym/observation/base.py                                  │        │
│  │  - compute(state: GameState, agent_id) → np.ndarray        │        │
│  └─────────────────────────────────────────────────────────────┘        │
│                              │                                         │
│                              ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  zbgym/reward/base.py                                      │        │
│  │  - compute(prev: GameState, curr: GameState, agent_id)      │        │
│  └─────────────────────────────────────────────────────────────┘        │
│                                                                         │
│  ALL MODULES: Use GameState instead of BattleArenaState                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 5-6: Plugins & Multi-Game Ready (Week 9-12)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  zbgym/plugins/                                            │        │
│  │  - Use Entity protocol instead of CharacterState            │        │
│  │  - Provide adapters for game-specific implementations       │        │
│  └─────────────────────────────────────────────────────────────┘        │
│                              │                                         │
│                              ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  NEW GAME ADAPTERS (Future)                                 │        │
│  │  - MOBAAttackAdapter                                        │        │
│  │  - ShooterAdapter                                          │        │
│  │  - All share same observation/reward providers!              │        │
│  └─────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Diagram 7: Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW                                     │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        Training Pipeline                                │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐
    │   Agent  │
    │  (Policy)│
    └────┬─────┘
         │ action
         ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  GameAdapter    │────▶│    GameEngine   │────▶│   GameState     │
│                 │      │  (BattleArena) │      │  (Generic)      │
└─────────────────┘      └─────────────────┘      └────────┬────────┘
         │                                                │
         │                                                │
         ▼                                                ▼
┌─────────────────┐                              ┌─────────────────┐
│ Observation     │◄─────────────────────────────│  GameState      │
│ Provider        │                              │  Interface      │
│                 │                              │                 │
│ - enemy.py      │                              │ .entities       │
│ - health.py     │                              │ .teams          │
│ - position.py   │                              │ .tick           │
└────────┬────────┘                              └─────────────────┘
         │                                                ▲
         │ observation                                     │
         ▼                                                │
┌─────────────────┐                              ┌─────────────────┐
│    Agent        │                              │   Reward        │
│  (Observation)  │                              │   Provider      │
└─────────────────┘                              │                 │
                                                   │ - combat.py    │
         ┌───────────────────────────────────────┤ - survival.py   │
         │                                       │ - utility.py    │
         │ reward                                └─────────────────┘
         ▼                                                ▲
┌─────────────────┐                                       │
│    Agent        │                                       │
│   (Reward)      │───────────────────────────────────────┘
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Policy        │
│   (Update)      │
└─────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                     State Conversion Flow                               │
└─────────────────────────────────────────────────────────────────────────┘

   BattleArenaState                BattleArenaGameState              GameState
┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
│ characters: Dict │  ───────▶  │ players: List   │  ───────▶  │ entities: List  │
│ safe_zone: ...   │            │ zone: Zone      │            │ teams: List     │
│ scores: Dict     │            │ scores: Dict    │            │ tick, time      │
└─────────────────┘            └─────────────────┘            └─────────────────┘
         │                              │                              │
         │ to_battle_arena()           │ to_generic()                │
         │                              │                             │
         ▼                              ▼                              ▼
┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
│ BattleArena     │  ◀──────── │ Adapter         │  ◀──────── │ Any Game Type  │
│ (Internal)      │            │ (Converter)     │            │                │
└─────────────────┘            └─────────────────┘            └─────────────────┘
```

---

## Diagram 8: Module Dependency (Target)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TARGET DEPENDENCY GRAPH                              │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │     make.py     │
                    │   (Entry API)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              │              ▼
    ┌─────────────────┐     │     ┌─────────────────┐
    │ AdapterFactory  │     │     │  GameAdapter    │
    └────────┬────────┘     │     │   (Interface)   │
             │             │     └────────┬────────┘
             │             │              │
             │    ┌────────┴────────┐      │
             │    │                 │      │
             ▼    ▼                 │      ▼
┌─────────────────────────────────────────────┐
│              GameState                      │
│            (Interface)                      │
│                                             │
│  • entities: List[Entity]                   │
│  • teams: List[Team]                        │
│  • tick, elapsed_time                       │
└─────────────────────┬───────────────────────┘
                      │
     ┌────────────────┼────────────────┐
     │                │                │
     ▼                ▼                ▼
┌─────────┐    ┌─────────┐      ┌─────────┐
│Observa- │    │ Rewards │      │ Plugins │
│tion     │    │         │      │         │
│Provider │    │Provider │      │Provider │
└────┬────┘    └────┬────┘      └────┬────┘
     │               │               │
     │    ┌──────────┴──────────┐    │
     │    │                     │    │
     ▼    ▼                     ▼    ▼
┌─────────────────────────────────────────────┐
│            Game-Specific Adapters            │
│                                             │
│  ┌─────────────┐  ┌─────────────┐          │
│  │ BattleArena │  │   Future    │          │
│  │  Adapter    │  │   Games     │          │
│  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────┘
```

---

## Summary

These diagrams show the transformation from a tightly-coupled BattleArena-specific architecture to a flexible multi-game framework:

1. **Current State**: All modules depend directly on BattleArenaState
2. **Target State**: All modules depend on generic GameState interface
3. **Bridge**: Adapters convert game-specific to generic
4. **Benefits**: 
   - Observation/Reward providers reusable
   - Easy to add new game types
   - Better testability
   - Clear separation of concerns
