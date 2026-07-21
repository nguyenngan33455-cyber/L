# ZBGym Tick Pipeline

## Overview

The TickPipeline defines the **exact order** of operations during each simulation tick. The Kernel TickCoordinator ensures this order is followed deterministically.

---

## Tick Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────────┐
│                           TICK PIPELINE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────┐                                                       │
│  │   1     │  PREPARE                                               │
│  │INPUT     │                                                       │
│  └────┬────┘                                                       │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────┐                                                       │
│  │   2     │  SCHEDULER                                             │
│  │         │                                                       │
│  └────┬────┘                                                       │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────┐                                                       │
│  │   3     │  AI DECISIONS                                          │
│  │         │                                                       │
│  └────┬────┘                                                       │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────┐                                                       │
│  │   4     │  ACTION QUEUE                                          │
│  │         │                                                       │
│  └────┬────┘                                                       │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────┐                                                       │
│  │   5     │  PHYSICS                                               │
│  │         │                                                       │
│  └────┬────┘                                                       │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────┐                                                       │
│  │   6     │  COLLISION                                             │
│  │         │                                                       │
│       ▼                                                             │
│  ┌─────────┐                                                       │
│  │   7     │  GAME LOGIC                                            │
│  │         │                                                       │
│  └────┬────┘                                                       │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────┐                                                       │
│  │   8     │  REWARD                                                │
│  │         │                                                       │
│  └────┬────┘                                                       │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────┐                                                       │
│  │   9     │  OBSERVATION                                          │
│  │         │                                                       │
│       ▼                                                             │
│  ┌─────────┐                                                       │
│  │  10     │  REPLAY                                                │
│  │         │                                                       │
│       ▼                                                             │
│  ┌─────────┐                                                       │
│  │  11     │  DASHBOARD                                             │
│  │         │                                                       │
│       ▼                                                             │
│  ┌─────────┐                                                       │
│  │  12     │  METRICS                                              │
│  │         │                                                       │
│       ▼                                                             │
│  ┌─────────┐                                                       │
│  │  13     │  EVENTS                                               │
│  │         │                                                       │
│       ▼                                                             │
│  ┌─────────┐                                                       │
│  │  14     │  FINISH                                               │
│  │         │                                                       │
│  └─────────┘                                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Stage Details

### Stage 1: PREPARE (Input)

**Purpose:** Prepare tick environment

**Operations:**
1. Increment tick counter
2. Calculate delta time
3. Update elapsed time
4. Validate state consistency
5. Clear transient buffers

**Module:** Engine (prepare phase)

**Deterministic:** Yes

---

### Stage 2: SCHEDULER

**Purpose:** Schedule AI decisions

**Operations:**
1. Update scheduler tick
2. Process scheduled callbacks
3. Update agent priorities
4. Check agent health

**Module:** AIScheduler

**Deterministic:** Yes (seed-controlled randomness)

---

### Stage 3: AI DECISIONS

**Purpose:** Generate AI actions

**Operations:**
1. For each agent:
   - Get observation
   - Process with AI model
   - Generate action
2. Cache actions for later

**Module:** AI System

**Deterministic:** Yes (seed-controlled)

---

### Stage 4: ACTION QUEUE

**Purpose:** Queue and validate actions

**Operations:**
1. Validate all actions
2. Resolve conflicts
3. Prioritize actions
4. Queue for execution

**Module:** ActionQueue

**Deterministic:** Yes (deterministic conflict resolution)

---

### Stage 5: PHYSICS

**Purpose:** Apply physics simulation

**Operations:**
1. For each physics body:
   - Apply forces
   - Integrate velocity
   - Integrate position
2. Update transforms

**Module:** Physics Engine

**Deterministic:** Yes (deterministic integration)

---

### Stage 6: COLLISION

**Purpose:** Detect and resolve collisions

**Operations:**
1. Broad phase collision detection
2. Narrow phase collision detection
3. Generate collision events
4. Apply collision response
5. Update collision state

**Module:** Collision System

**Deterministic:** Yes (deterministic detection)

---

### Stage 7: GAME LOGIC

**Purpose:** Execute game rules

**Operations:**
1. Process damage
2. Apply buffs/debuffs
3. Check win/lose conditions
4. Update character state
5. Process abilities

**Module:** Engine (game logic phase)

**Deterministic:** Yes (deterministic rules)

---

### Stage 8: REWARD

**Purpose:** Calculate rewards

**Operations:**
1. For each agent:
   - Calculate individual reward
   - Add reward to buffer
2. Normalize rewards (if configured)

**Module:** Reward System

**Deterministic:** Yes (deterministic calculation)

---

### Stage 9: OBSERVATION

**Purpose:** Generate observations

**Operations:**
1. For each agent:
   - Gather visible entities
   - Generate observation vector
   - Encode spatial data
2. Return observation dict

**Module:** Observation System

**Deterministic:** Yes (deterministic encoding)

---

### Stage 10: REPLAY

**Purpose:** Record tick data

**Operations:**
1. Serialize game state
2. Record actions
3. Record rewards
4. Record observations
5. Compress (if enabled)

**Module:** Replay System

**Deterministic:** Yes (full state capture)

---

### Stage 11: DASHBOARD

**Purpose:** Update visualization

**Operations:**
1. Update render state
2. Send to dashboard clients
3. Process dashboard commands

**Module:** Dashboard

**Deterministic:** Output-only (no effect on simulation)

---

### Stage 12: METRICS

**Purpose:** Collect tick metrics

**Operations:**
1. Record tick duration
2. Record stage durations
3. Record memory usage
4. Update counters

**Module:** MetricsCollector

**Deterministic:** Recording-only (no effect on simulation)

---

### Stage 13: EVENTS

**Purpose:** Dispatch pending events

**Operations:**
1. Process event queue
2. Notify subscribers
3. Clear processed events

**Module:** EventBus

**Deterministic:** Yes (deterministic ordering)

---

### Stage 14: FINISH

**Purpose:** Complete tick

**Operations:**
1. Validate state
2. Update metrics
3. Prepare for next tick
4. Return tick results

**Module:** Engine (finish phase)

**Deterministic:** Yes

---

## Hook Integration

Each stage has associated hooks:

```
┌────────────────────────────────────────────────────┐
│ Stage Hooks                                        │
├────────────────────────────────────────────────────┤
│                                                    │
│  before_prepare    →  before_prepare()           │
│  after_prepare     →  after_prepare()             │
│                                                    │
│  before_scheduler  →  before_scheduler()           │
│  after_scheduler   →  after_scheduler()            │
│                                                    │
│  before_ai         →  before_ai()                │
│  after_ai          →  after_ai()                  │
│                                                    │
│  before_physics     →  before_physics()           │
│  after_physics      →  after_physics()            │
│                                                    │
│  before_collision   →  before_collision()          │
│  after_collision   →  after_collision()          │
│                                                    │
│  before_game_logic  →  before_game_logic()        │
│  after_game_logic   →  after_game_logic()          │
│                                                    │
│  before_reward      →  before_reward()            │
│  after_reward       →  after_reward()             │
│                                                    │
│  before_observation →  before_observation()       │
│  after_observation  →  after_observation()         │
│                                                    │
│  before_replay      →  before_replay()            │
│  after_replay       →  after_replay()             │
│                                                    │
│  before_finish      →  before_finish()            │
│  after_finish       →  after_finish()             │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## Hook Execution Order

```
Kernel.start_tick()
      │
      ▼
before_prepare()
      │
      ▼
[PREPARE Stage]
      │
      ▼
after_prepare()
      │
      ▼
before_scheduler()
      │
      ▼
[SCHEDULER Stage]
      │
      ▼
after_scheduler()
      │
      ▼
... (repeat for all stages)
      │
      ▼
before_finish()
      │
      ▼
[FINISH Stage]
      │
      ▼
after_finish()
      │
      ▼
Kernel.end_tick()
```

---

## Timing Requirements

### Target Timing

| Stage | Target Time | Max Time |
|-------|-------------|----------|
| PREPARE | 0.1ms | 0.5ms |
| SCHEDULER | 0.5ms | 1ms |
| AI | 5ms | 10ms |
| ACTION_QUEUE | 0.1ms | 0.5ms |
| PHYSICS | 1ms | 2ms |
| COLLISION | 1ms | 3ms |
| GAME_LOGIC | 1ms | 2ms |
| REWARD | 0.1ms | 0.5ms |
| OBSERVATION | 0.5ms | 1ms |
| REPLAY | 1ms | 5ms |
| DASHBOARD | 0.5ms | 10ms |
| METRICS | 0.1ms | 0.5ms |
| EVENTS | 0.2ms | 1ms |
| **TOTAL** | **~12ms** | **~35ms** |

### Target: 60 ticks/second (16.67ms budget)

---

## Stage Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA FLOW                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PREPARE:        ()  →  TickContext                        │
│                                                              │
│  SCHEDULER:      TickContext  →  ScheduledCallbacks        │
│                                                              │
│  AI:             Observation  →  Actions                    │
│                                                              │
│  ACTION_QUEUE:   Actions  →  ValidatedActions             │
│                                                              │
│  PHYSICS:        ValidatedActions  →  PhysicsState         │
│                                                              │
│  COLLISION:      PhysicsState  →  CollisionEvents          │
│                                                              │
│  GAME_LOGIC:     (PhysicsState, CollisionEvents)  →  GameState │
│                                                              │
│  REWARD:         GameState  →  Rewards                     │
│                                                              │
│  OBSERVATION:    GameState  →  Observations                 │
│                                                              │
│  REPLAY:         (GameState, Actions, Rewards, Obs)  →  Replay │
│                                                              │
│  DASHBOARD:      GameState  →  RenderState                 │
│                                                              │
│  METRICS:        (all above)  →  Metrics                   │
│                                                              │
│  EVENTS:         PendingEvents  →  DispatchedEvents          │
│                                                              │
│  FINISH:         ()  →  TickResult                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## TickContext

```python
@dataclass
class TickContext:
    """Context passed through tick pipeline."""
    
    # Tick info
    tick_number: int
    delta_time: float
    elapsed_time: float
    
    # Stage data
    scheduled_callbacks: list[Callback]
    actions: dict[str, Action]
    physics_state: PhysicsState
    collision_events: list[CollisionEvent]
    game_state: GameState
    rewards: dict[str, float]
    observations: dict[str, np.ndarray]
    events: list[Event]
    
    # Metadata
    stage: TickStage
    errors: list[Exception]
    
    # Access
    config: Configuration
```

---

## Error Handling

### Per-Stage Error Handling

```
Stage execution
      │
      ▼
┌─────────────┐
│ Error?      │
└──────┬──────┘
       │
   Yes │ No
       │ │
       ▼ │
┌─────────────────┐
│ Catch exception │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Log error       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Mark in context │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Continue stage? │
└──────┬──────────┘
       │
   Yes │ No
       │ │
       ▼ │
┌─────────────┐
│ Continue    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Continue tick?  │
└──────┬──────────┘
       │
   Yes │ No
       │ │
       ▼ │
┌─────────────┐
│ Stop tick   │
└─────────────┘
```

### Stage Continuation Rules

| Error Type | Continue? | Reason |
|-----------|-----------|--------|
| Non-critical | Yes | Game can continue |
| Critical | No | State integrity at risk |
| AI failure | Maybe | Use default action |
| Physics error | Maybe | Skip physics for entity |
| Game logic | Maybe | Skip entity logic |

---

## Skippable Stages

Some stages can be skipped:

| Stage | Skippable | Condition |
|-------|-----------|-----------|
| DASHBOARD | Yes | No connected clients |
| REPLAY | Yes | Recording disabled |
| METRICS | Yes | Metrics disabled |
| AI | Yes | Using scripted agents |
| COLLISION | Yes | Using simplified physics |

---

## Parallelization

### Potential Parallel Stages

```
Note: Tick order must be preserved

Stage 1: PREPARE      [Sequential]
Stage 2: SCHEDULER    [Sequential]
Stage 3: AI           [Parallel per agent]
Stage 4: ACTION_QUEUE [Sequential]
Stage 5: PHYSICS      [Parallel per body]
Stage 6: COLLISION    [Parallel per pair]
Stage 7: GAME_LOGIC   [Parallel per entity]
Stage 8: REWARD       [Parallel per agent]
Stage 9: OBSERVATION  [Parallel per agent]
Stage 10: REPLAY      [Sequential]
Stage 11: DASHBOARD   [Sequential]
Stage 12: METRICS     [Sequential]
Stage 13: EVENTS      [Sequential]
Stage 14: FINISH      [Sequential]
```

### Synchronization Points

```
Parallel stages must synchronize before next sequential stage

[AI agents] ──────┐
[AI agents] ──────┼──→ SCHEDULER sync ──→ ACTION_QUEUE
[AI agents] ──────┘
```

---

## Performance Optimization

### Stage Budget Tracking

```python
class TickCoordinator:
    def execute_tick(self, tick: int) -> TickResult:
        budgets = {
            "prepare": 0.5,    # ms
            "scheduler": 1.0,
            "ai": 10.0,
            "physics": 2.0,
            "collision": 3.0,
            "game_logic": 2.0,
            "reward": 0.5,
            "observation": 1.0,
            "replay": 5.0,
            "dashboard": 10.0,
            "metrics": 0.5,
            "events": 1.0,
        }
        
        for stage, budget in budgets.items():
            start = time.perf_counter()
            self._execute_stage(stage)
            duration = (time.perf_counter() - start) * 1000
            
            if duration > budget:
                self._log_warning(f"{stage} exceeded budget: {duration:.2f}ms > {budget}ms")
```

---

## Summary

Key tick pipeline principles:

1. **Fixed Order**: Every stage executes in defined order
2. **Deterministic**: Same input = same output
3. **Hook Integration**: Plugins can hook into any stage
4. **Error Isolation**: Errors contained per stage
5. **Performance Tracking**: Budget monitoring per stage
6. **Skippable Stages**: Optional stages can be disabled
7. **Data Flow**: Each stage passes data to next
8. **No Shortcuts**: All stages execute unless skipped
