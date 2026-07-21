# ZBGym Runtime Flow

## Overview

This document traces the complete runtime execution flow through the ZBGym framework. Every step is documented with inputs, outputs, and ownership.

---

## Application Startup Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     APPLICATION STARTUP                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. User launches application                                        │
│     │                                                               │
│     ▼                                                               │
│  2. Python interpreter starts                                        │
│     │                                                               │
│     ▼                                                               │
│  3. Application main() called                                       │
│     │                                                               │
│     ▼                                                               │
│  4. Configuration loaded                                             │
│     │   - config.yaml                                               │
│     │   - environment variables                                     │
│     │   - defaults                                                  │
│     ▼                                                               │
│  5. Kernel created (CREATED state)                                  │
│     │                                                               │
│     ▼                                                               │
│  6. Kernel.bootstrap() called (BOOTING state)                        │
│     │                                                               │
│     ├─→ Load configuration                                          │
│     │                                                               │
│     ├─→ Create RuntimeContext                                       │
│     │                                                               │
│     ├─→ Discover modules                                             │
│     │                                                               │
│     ├─→ Register modules                                            │
│     │                                                               │
│     ├─→ Resolve dependencies                                        │
│     │                                                               │
│     └─→ Transition to INITIALIZING                                  │
│                                                                      │
│  7. Kernel initializes modules (INITIALIZING state)                   │
│     │                                                               │
│     ├─→ Initialize in dependency order                              │
│     │                                                               │
│     ├─→ Allocate resources                                           │
│     │                                                               │
│     ├─→ Register services                                            │
│     │                                                               │
│     └─→ Transition to READY                                         │
│                                                                      │
│  8. Kernel ready (READY state)                                       │
│     │                                                               │
│     ▼                                                               │
│  9. Kernel.start() called (RUNNING state)                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Simulation Tick Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SIMULATION TICK                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────┐                                                        │
│  │ KERNEL  │                                                        │
│  └────┬────┘                                                        │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    TICK PIPELINE                             │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                               │   │
│  │  STAGE 1: PREPARE                                           │   │
│  │  Owner: Engine                                              │   │
│  │  Input:  ()                                                  │   │
│  │  Output: TickContext                                        │   │
│  │  │                                                          │   │
│  │  │  - Increment tick counter                                │   │
│  │  │  - Calculate delta time                                  │   │
│  │  │  - Update elapsed time                                  │   │
│  │  │  - Validate state consistency                           │   │
│  │  │  - Clear transient buffers                              │   │
│  │  ▼                                                          │   │
│  │                                                               │   │
│  │  STAGE 2: SCHEDULER                                         │   │
│  │  Owner: AIScheduler                                          │   │
│  │  Input:  TickContext                                         │   │
│  │  Output: ScheduledCallbacks                                 │   │
│  │  │                                                          │   │
│  │  │  - Update scheduler tick                                │   │
│  │  │  - Process scheduled callbacks                          │   │
│  │  │  - Update agent priorities                              │   │
│  │  │  - Check agent health                                   │   │
│  │  ▼                                                          │   │
│  │                                                               │   │
│  │  STAGE 3: AI DECISIONS                                      │   │
│  │  Owner: AI System                                            │   │
│  │  Input:  Observation                                         │   │
│  │  Output: Actions                                             │   │
│  │  │                                                          │   │
│  │  │  - For each agent:                                      │   │
│  │  │    - Get observation                                    │   │
│  │  │    - Process with AI model                              │   │
│  │  │    - Generate action                                    │   │
│  │  │  - Cache actions for later                              │   │
│  │  ▼                                                          │   │
│  │                                                               │   │
│  │  STAGE 4: ACTION QUEUE                                      │   │
│  │  Owner: ActionQueue                                          │   │
│  │  Input:  Actions                                             │   │
│  │  Output: ValidatedActions                                    │   │
│  │  │                                                          │   │
│  │  │  - Validate all actions                                 │   │
│  │  │  - Resolve conflicts                                     │   │
│  │  │  - Prioritize actions                                   │   │
│  │  │  - Queue for execution                                   │   │
│  │  ▼                                                          │   │
│  │                                                               │   │
│  │  STAGE 5: PHYSICS                                           │   │
│  │  Owner: Physics Engine                                      │   │
│  │  Input:  ValidatedActions                                    │   │
│  │  Output: PhysicsState                                        │   │
│  │  │                                                          │   │
│  │  │  - For each physics body:                               │   │
│  │  │    - Apply forces                                        │   │
│  │  │    - Integrate velocity                                  │   │
│  │  │    - Integrate position                                  │   │
│  │  │  - Update transforms                                     │   │
│  │  ▼                                                          │   │
│  │                                                               │   │
│  │  STAGE 6: COLLISION                                         │   │
│  │  Owner: Collision System                                    │   │
│  │  Input:  PhysicsState                                        │   │
│  │  Output: CollisionEvents                                     │   │
│  │  │                                                          │   │
│  │  │  - Broad phase collision detection                      │   │
│  │  │  - Narrow phase collision detection                     │   │
│  │  │  - Generate collision events                            │   │
│  │  │  - Apply collision response                            │   │
│  │  │  - Update collision state                              │   │
│  │  ▼                                                          │   │
│  │                                                               │   │
│  │  STAGE 7: GAME LOGIC                                        │   │
│  │  Owner: Engine                                              │   │
│  │  Input:  PhysicsState, CollisionEvents                      │   │
│  │  Output: GameState                                           │   │
│  │  │                                                          │   │
│  │  │  - Process damage                                        │   │
│  │  │  - Apply buffs/debuffs                                  │   │
│  │  │  - Check win/lose conditions                            │   │
│  │  │  - Update character state                               │   │
│  │  │  - Process abilities                                    │   │
│  │  ▼                                                          │   │
│  │                                                               │   │
│  │  STAGE 8: REWARD                                             │   │
│  │  Owner: Reward System                                        │   │
│  │  Input:  GameState                                           │   │
│  │  Output: Rewards                                             │   │
│  │  │                                                          │   │
│  │  │  - For each agent:                                      │   │
│  │  │    - Calculate individual reward                        │   │
│  │  │    - Add reward to buffer                               │   │
│  │  │  - Normalize rewards (if configured)                    │   │
│  │  ▼                                                          │   │
│  │                                                               │   │
│  │  STAGE 9: OBSERVATION                                       │   │
│  │  Owner: Observation System                                  │   │
│  │  Input:  GameState                                           │   │
│  │  Output: Observations                                        │   │
│  │  │                                                          │   │
│  │  │  - For each agent:                                      │   │
│  │  │    - Gather visible entities                            │   │
│  │  │    - Generate observation vector                        │   │
│  │  │    - Encode spatial data                                │   │
│  │  │  - Return observation dict                              │   │
│  │  ▼                                                          │   │
│  │                                                               │   │
│  │  STAGE 10: REPLAY                                           │   │
│  │  Owner: Replay System                                       │   │
│  │  Input:  GameState, Actions, Rewards, Observations          │   │
│  │  Output: ReplayData                                          │   │
│  │  │                                                          │   │
│  │  │  - Serialize game state                                │   │
│  │  │  - Record actions                                       │   │
│  │  │  - Record rewards                                       │   │
│  │  │  - Record observations                                  │   │
│  │  │  - Compress (if enabled)                                │   │
│  │  ▼                                                          │   │
│  │                                                               │   │
│  │  STAGE 11: DASHBOARD                                         │   │
│  │  Owner: Dashboard                                           │   │
│  │  Input:  GameState                                           │   │
│  │  Output: RenderState                                         │   │
│  │  │                                                          │   │
│  │  │  - Update render state                                  │   │
│  │  │  - Send to dashboard clients                            │   │
│  │  │  - Process dashboard commands                            │   │
│  │  ▼                                                          │   │
│  │                                                               │   │
│  │  STAGE 12: METRICS                                          │   │
│  │  Owner: MetricsCollector                                     │   │
│  │  Input:  All stage data                                      │   │
│  │  Output: Metrics                                             │   │
│  │  │                                                          │   │
│  │  │  - Record tick duration                                 │   │
│  │  │  - Record stage durations                               │   │
│  │  │  - Record memory usage                                  │   │
│  │  │  - Update counters                                      │   │
│  │  ▼                                                          │   │
│  │                                                               │   │
│  │  STAGE 13: EVENTS                                           │   │
│  │  Owner: EventBus                                             │   │
│  │  Input:  PendingEvents                                       │   │
│  │  Output: DispatchedEvents                                     │   │
│  │  │                                                          │   │
│  │  │  - Process event queue                                  │   │
│  │  │  - Notify subscribers                                    │   │
│  │  │  - Clear processed events                               │   │
│  │  ▼                                                          │   │
│  │                                                               │   │
│  │  STAGE 14: FINISH                                            │   │
│  │  Owner: Engine                                               │   │
│  │  Input:  ()                                                  │   │
│  │  Output: TickResult                                          │   │
│  │  │                                                          │   │
│  │  │  - Validate state                                        │   │
│  │  │  - Update metrics                                       │   │
│  │  │  - Prepare for next tick                                │   │
│  │  │  - Return tick results                                  │   │
│  │  │                                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────┐                                                        │
│  │ KERNEL  │                                                        │
│  └────┬────┘                                                        │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    EVENT DISPATCH                            │   │
│  │                                                               │   │
│  │  TickComplete → EventBus → Subscribers                       │   │
│  │                                                               │   │
│  │  1. Event created with tick data                            │   │
│  │  2. Event dispatched to EventBus                            │   │
│  │  3. EventBus notifies all subscribers                       │   │
│  │  4. Subscribers process event (may emit new events)         │   │
│  │  5. All events processed                                    │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  Return TickResult to caller                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Event Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EVENT FLOW                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Producer                                                           │
│     │                                                               │
│     ▼                                                               │
│  ┌─────────┐                                                        │
│  │ EventBus │  ← All events go through EventBus                     │
│  └────┬────┘                                                        │
│       │                                                             │
│       ├─→ Filter (optional)                                        │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              SUBSCRIBER MATCHING                             │   │
│  │                                                               │   │
│  │  Event: TICK_COMPLETE                                       │   │
│  │  Subscribers:                                                │   │
│  │    - Replay (records tick)                                   │   │
│  │    - Dashboard (updates display)                            │   │
│  │    - Metrics (records stats)                                │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              NOTIFICATION (in priority order)                │   │
│  │                                                               │   │
│  │  1. Priority 100: Metrics                                    │   │
│  │  2. Priority 50: Replay                                      │   │
│  │  3. Priority 0: Dashboard                                    │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  Subscribers process events (may emit new events)                   │
│       │                                                             │
│       ▼                                                             │
│  All events processed                                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Module Communication Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                   MODULE COMMUNICATION                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ✗ INVALID: Direct module-to-module                                 │
│                                                                      │
│    ModuleA ────X───→ ModuleB                                        │
│                                                                      │
│  ✓ VALID: Through Kernel/EventBus                                   │
│                                                                      │
│    ModuleA → Kernel → EventBus → ModuleB                            │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Example: Dashboard requests AI decision                             │
│                                                                      │
│    Dashboard                                                        │
│       │                                                             │
│       │  emit(Command(REQUEST_AI_DECISION))                         │
│       ▼                                                             │
│    EventBus                                                         │
│       │                                                             │
│       │  dispatch to AI subscriber                                  │
│       ▼                                                             │
│    AI System                                                        │
│       │                                                             │
│       │  process command                                            │
│       │  emit(Response(DECISION, data))                             │
│       ▼                                                             │
│    EventBus                                                         │
│       │                                                             │
│       │  dispatch to Dashboard subscriber                           │
│       ▼                                                             │
│    Dashboard                                                        │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Example: Physics collision triggers game logic                      │
│                                                                      │
│    Physics                                                          │
│       │                                                             │
│       │  detect collision                                           │
│       │  emit(Event(COLLISION, bodies=b1+b2))                       │
│       ▼                                                             │
│    EventBus                                                         │
│       │                                                             │
│       │  dispatch to Engine subscriber                              │
│       ▼                                                             │
│    Engine                                                           │
│       │                                                             │
│       │  process collision                                          │
│       │  update game state                                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Command Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       COMMAND FLOW                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  External Client                                                    │
│       │                                                             │
│       │  POST /api/command                                          │
│       ▼                                                             │
│  Dashboard                                                          │
│       │                                                             │
│       │  validate command                                           │
│       │  emit CommandEvent                                          │
│       ▼                                                             │
│  EventBus                                                           │
│       │                                                             │
│       │  route to CommandHandler                                    │
│       ▼                                                             │
│  CommandHandler                                                     │
│       │                                                             │
│       │  parse command                                             │
│       │  check permissions                                         │
│       │  route to target module                                     │
│       ▼                                                             │
│  Target Module                                                      │
│       │                                                             │
│       │  execute command                                            │
│       │  return Result                                              │
│       ▼                                                             │
│  CommandHandler                                                     │
│       │                                                             │
│       │  format response                                            │
│       ▼                                                             │
│  Dashboard                                                          │
│       │                                                             │
│       │  emit ResultEvent                                           │
│       ▼                                                             │
│  External Client (response)                                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Shutdown Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       SHUTDOWN FLOW                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Shutdown requested (kernel.shutdown())                          │
│     │                                                               │
│     ▼                                                               │
│  2. Transition to STOPPING                                           │
│     │                                                               │
│     ▼                                                               │
│  3. Stop tick processing                                            │
│     │                                                               │
│     ▼                                                               │
│  4. Stop modules in reverse dependency order                         │
│     │                                                               │
│     ├─→ Stop Dashboard                                              │
│     ├─→ Stop Replay                                                 │
│     ├─→ Stop AI System                                              │
│     ├─→ Stop Physics                                                │
│     └─→ Stop Engine                                                 │
│     │                                                               │
│     ▼                                                               │
│  5. Transition to STOPPED                                           │
│     │                                                               │
│     ▼                                                               │
│  6. Persist state (if configured)                                   │
│     │                                                               │
│     ├─→ Save replay                                                 │
│     ├─→ Save metrics                                               │
│     └─→ Save checkpoints                                           │
│     │                                                               │
│     ▼                                                               │
│  7. Transition to SHUTDOWN                                          │
│     │                                                               │
│     ▼                                                               │
│  8. Release resources                                               │
│     │                                                               │
│     ├─→ Close file handles                                          │
│     ├─→ Release network connections                                 │
│     ├─→ Free memory                                                │
│     └─→ Clear caches                                                │
│     │                                                               │
│     ▼                                                               │
│  9. Transition to TERMINATED                                        │
│     │                                                               │
│     ▼                                                               │
│  10. Exit process                                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Error Recovery Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ERROR RECOVERY FLOW                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Error detected in module                                            │
│     │                                                               │
│     ▼                                                               │
│  Kernel catches exception                                            │
│     │                                                               │
│     ▼                                                               │
│  Mark module as unhealthy                                           │
│     │                                                               │
│     ▼                                                               │
│  Isolate module (stop dispatching)                                   │
│     │                                                               │
│     ▼                                                               │
│  Log error with full context                                        │
│     │                                                               │
│     ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    RECOVERY DECISION                          │   │
│  │                                                               │   │
│  │  Is error recoverable?                                       │   │
│  │      │                                                        │   │
│  │  Yes │ No                                                     │   │
│  │      │                                                        │   │
│  │      ▼                                                        │   │
│  │  ┌─────────────┐                                              │   │
│  │  │ Attempt     │                                              │   │
│  │  │ Recovery    │                                              │   │
│  │  └──────┬──────┘                                              │   │
│  │         │                                                      │   │
│  │         ├─→ Retry initialization                              │   │
│  │         ├─→ Use fallback implementation                        │   │
│  │         └─→ Skip failed functionality                         │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│     │                                                               │
│     ├─→ Recovery successful?                                        │
│     │      │                                                        │   │
│     │  Yes │ No                                                     │   │
│     │      │                                                        │   │
│     │      ▼                                                        │   │
│     │  ┌─────────────────┐                                         │   │
│     │  │ Module critical? │                                        │   │
│     │  └────────┬────────┘                                         │   │
│     │           │                                                   │   │
│     │       Yes │ No                                                │   │
│     │           │                                                    │   │
│     │           ▼                                                    │   │
│     │      ┌─────────────┐                                          │   │
│     │      │ Continue    │                                          │   │
│     │      │ (degraded)  │                                          │   │
│     │      └─────────────┘                                          │   │
│     │                                                               │   │
│     ▼                                                               │   │
│  Report to HealthMonitor                                            │
│     │                                                               │
│     ▼                                                               │
│  Continue simulation                                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW SUMMARY                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Input Sources:                                                     │
│  ┌─────────┐                                                        │
│  │ Config  │ → Configuration                                        │
│  └─────────┘                                                        │
│  ┌─────────┐                                                        │
│  │ User    │ → Commands                                             │
│  └─────────┘                                                        │
│  ┌─────────┐                                                        │
│  │ AI      │ → Actions                                              │
│  └─────────┘                                                        │
│                                                                      │
│  Processing:                                                        │
│  ┌─────────┐                                                        │
│  │ Physics │ → Transform actions to physics                        │
│  └─────────┘                                                        │
│  ┌─────────┐                                                        │
│  │ Engine  │ → Apply game rules                                    │
│  └─────────┘                                                        │
│                                                                      │
│  Output Sinks:                                                      │
│  ┌─────────┐                                                        │
│  │ Reward  │ ← Agent feedback                                       │
│  └─────────┘                                                        │
│  ┌─────────┐                                                        │
│  │ Observe │ ← Agent state                                          │
│  └─────────┘                                                        │
│  ┌─────────┐                                                        │
│  │ Replay  │ ← State recording                                      │
│  └─────────┘                                                        │
│  ┌─────────┐                                                        │
│  │Dashboard│ ← Visualization                                        │
│  └─────────┘                                                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Summary

| Flow | Direction | Owner |
|------|-----------|-------|
| Startup | Linear | Kernel |
| Tick | Pipeline | Kernel → Modules |
| Event | Broadcast | EventBus |
| Command | Request/Response | Dashboard → Kernel |
| Communication | Indirect | EventBus (hub) |
| Shutdown | Reverse | Kernel |
| Recovery | Conditional | Kernel |
