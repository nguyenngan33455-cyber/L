# ZBGym Kernel Ownership Model

## Overview

This document defines the **ownership hierarchy** for all objects in the ZBGym framework. Every object has exactly one owner. No shared ownership. No undefined lifetime.

---

## Ownership Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                         OWNERSHIP HIERARCHY                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                           KERNEL (Root Owner)                        │
│                                  │                                   │
│         ┌───────────────────────┼───────────────────────┐           │
│         │                       │                       │           │
│         ▼                       ▼                       ▼           │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────────┐  │
│  │RuntimeContext│       │LifecycleMgr│       │ModuleManager    │  │
│  └──────┬──────┘       └──────┬──────┘       └────────┬────────┘  │
│         │                      │                      │             │
│         │          ┌───────────┴───────────┐          │             │
│         │          │                       │          │             │
│         ▼          ▼                       ▼          ▼             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │EventBus     │ │ServiceRegistry│ │TickScheduler│ │HealthMonitor││
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘│
│         │               │               │               │           │
│         └───────────────┴───────────────┴───────────────┘           │
│                               │                                     │
│                               ▼                                     │
│                   ┌─────────────────────┐                           │
│                   │    Configuration   │                           │
│                   └─────────────────────┘                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Kernel (Root Owner)

**Owner:** System (Application Main)

**Owns:**
- RuntimeContext
- LifecycleManager
- ModuleManager
- DependencyResolver
- EventDispatcher
- TickCoordinator
- HealthMonitor
- ServiceRegistry
- MetricsCollector

**Lifetime:**
- Created at application start
- Destroyed at application exit

**Responsibilities:**
- Coordinate all sub-systems
- Manage lifecycle transitions
- Ensure deterministic behavior

---

## RuntimeContext

**Owner:** Kernel

**Owns:**
- Configuration
- EventBus
- TickScheduler
- Clock
- Logger
- Engine
- Physics
- AI System
- Replay System
- Dashboard
- PluginRegistry
- HookSystem
- StateStore
- MetricsCollector
- HealthMonitor

**Lifetime:**
- Created during Kernel bootstrap
- Destroyed during Kernel shutdown

**Creation:**
```python
# Kernel creates RuntimeContext
runtime_context = RuntimeContext(
    config=Configuration(),
    event_bus=EventBus(),
    scheduler=TickScheduler(),
    ...
)
```

**Destruction:**
```python
# Kernel destroys RuntimeContext on shutdown
runtime_context.shutdown()
del runtime_context
```

---

## Configuration

**Owner:** RuntimeContext

**Owns:** Configuration data only (immutable after creation)

**Created by:** Kernel during bootstrap

**Destroyed by:** RuntimeContext during shutdown

**Access:**
- Read-only after creation
- Passed to all modules via RuntimeContext

---

## EventBus

**Owner:** RuntimeContext

**Owns:**
- Event subscriptions
- Event queue
- Subscriber callbacks

**Created by:** RuntimeContext during initialization

**Destroyed by:** RuntimeContext during shutdown

**Access:**
- All modules may subscribe/unsubscribe
- All modules may emit events
- No module owns EventBus references after shutdown

---

## TickScheduler

**Owner:** RuntimeContext

**Owns:**
- Scheduled callbacks
- Timing state
- Tick counter

**Created by:** RuntimeContext during initialization

**Destroyed by:** RuntimeContext during shutdown

**Access:**
- Modules register callbacks
- Kernel coordinates execution order

---

## HealthMonitor

**Owner:** RuntimeContext

**Owns:**
- Health check registrations
- Health status
- Alert callbacks

**Created by:** RuntimeContext during initialization

**Destroyed by:** RuntimeContext during shutdown

**Access:**
- Modules register health checks
- HealthReport generated on demand

---

## ServiceRegistry

**Owner:** RuntimeContext

**Owns:**
- Service registrations
- Service implementations

**Created by:** RuntimeContext during initialization

**Destroyed by:** RuntimeContext during shutdown

**Access:**
- Modules register services
- Modules query services
- No singleton access

---

## MetricsCollector

**Owner:** RuntimeContext

**Owns:**
- Metric counters
- Metric history
- Aggregation state

**Created by:** RuntimeContext during initialization

**Destroyed by:** RuntimeContext during shutdown

**Access:**
- All modules may record metrics
- Metrics are read-only externally

---

## StateStore

**Owner:** RuntimeContext

**Owns:**
- Key-value state
- State snapshots

**Created by:** RuntimeContext during initialization

**Destroyed by:** RuntimeContext during shutdown

**Access:**
- Modules may store/retrieve state
- Kernel may create snapshots

---

## Module Ownership

### Engine

**Owner:** RuntimeContext

**Owns:**
- World
- Entity registry
- Simulation state
- Game logic

**Created by:** RuntimeContext during initialization

**Destroyed by:** RuntimeContext during shutdown

**Dependencies:**
- Physics (for world updates)
- EventBus (for communication)

---

### Physics

**Owner:** RuntimeContext

**Owns:**
- Physics bodies
- Collision world
- Physics state

**Created by:** RuntimeContext during initialization

**Destroyed by:** RuntimeContext during shutdown

**Dependencies:**
- EventBus (for collision events)

---

### AI System

**Owner:** RuntimeContext

**Owns:**
- AI models
- Decision state
- Agent registry

**Created by:** RuntimeContext during initialization

**Destroyed by:** RuntimeContext during shutdown

**Dependencies:**
- Scheduler (for decision timing)
- EventBus (for communication)

---

### Replay System

**Owner:** RuntimeContext

**Owns:**
- Replay buffer
- Recorded state
- Compression state

**Created by:** RuntimeContext during initialization

**Destroyed by:** RuntimeContext during shutdown

**Access:**
- Engine (records state)
- Dashboard (reads replay)

---

### Dashboard

**Owner:** RuntimeContext

**Owns:**
- WebSocket connections
- Render state
- Client registry

**Created by:** RuntimeContext during initialization

**Destroyed by:** RuntimeContext during shutdown

**Access:**
- Reads simulation state
- Sends commands to Kernel

---

## Plugin Ownership

### PluginRegistry

**Owner:** RuntimeContext

**Owns:**
- Plugin registrations
- Plugin instances
- Plugin metadata

**Created by:** RuntimeContext during initialization

**Destroyed by:** RuntimeContext during shutdown

---

### HookSystem

**Owner:** RuntimeContext

**Owns:**
- Hook registrations
- Hook callbacks
- Execution order

**Created by:** RuntimeContext during initialization

**Destroyed by:** RuntimeContext during shutdown

---

### Plugin (External)

**Owner:** Plugin developer

**Owns:**
- Plugin logic
- Plugin state
- Plugin resources

**Lifetime:**
- Loaded by PluginRegistry
- Unloaded by PluginRegistry
- Plugin developer manages internal state

**Kernel owns:** Plugin lifecycle (load/unload)

---

## Entity Ownership

### World

**Owner:** Engine

**Owns:**
- Entity registry
- Spatial partitioning
- World state

**Created by:** Engine during initialization

**Destroyed by:** Engine during shutdown

---

### Entity

**Owner:** World

**Owns:**
- Entity components
- Entity state
- Entity ID

**Created by:** World during spawn

**Destroyed by:** World during despawn

---

### PhysicsBody

**Owner:** Physics

**Owns:**
- Body properties
- Transform state
- Collision shape

**Created by:** Physics during body creation

**Destroyed by:** Physics during body destruction

---

## Ownership Rules

### Rule 1: Single Owner

Every object has exactly one owner.

```
✓ Valid: Kernel owns RuntimeContext owns EventBus
✗ Invalid: Both Kernel and Module own EventBus
```

### Rule 2: No Circular Ownership

```
✓ Valid: Kernel owns A owns B owns C
✗ Invalid: Kernel owns A owns B owns A (cycle)
```

### Rule 3: Transitive Destruction

When owner is destroyed, all owned objects are destroyed.

```
RuntimeContext destroyed
    → EventBus destroyed
    → TickScheduler destroyed
    → HealthMonitor destroyed
    → ...
```

### Rule 4: No Access After Destruction

Objects cannot access destroyed owners.

```
✓ Valid: Use object while owner is alive
✗ Invalid: Store reference, use after owner destroyed
```

### Rule 5: No Shared Ownership

```
✓ Valid: Kernel owns Object A, Module owns Object B
✗ Invalid: Both Kernel and Module own Object C
```

---

## Ownership Transfer

Ownership may transfer in limited cases:

### Initialization Transfer

```python
# Kernel creates RuntimeContext
# Ownership transfers from Kernel to "system"
runtime_context = RuntimeContext(...)
```

### Module Registration Transfer

```python
# Plugin registers service
# Ownership transfers from Plugin to RuntimeContext
runtime_context.service_registry.register(MyService)
```

### Lifecycle Transfer

```python
# Module shutdown
# Ownership of module resources returns to Kernel
module.shutdown()
```

---

## Lifetime Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    LIFETIME HIERARCHY                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Kernel:          |───────── Application Lifetime ─────────|│
│                    │                                         │
│  RuntimeContext:  │ |--- Bootstrap ---||--- Runtime ---||---|│
│                    │                                         │
│  Modules:         │   |--- Init ---||--- Running ---||---||│
│                    │                                         │
│  Entities:        │       |--- Spawn ---||--- Update ---||---|│
│                    │                                         │
│  Events:          │           |--- Emit ---||--- Process ---|│
│                    │                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

| Owner | Owns |
|-------|------|
| Kernel | RuntimeContext, Managers |
| RuntimeContext | All services, All modules |
| EventBus | Subscriptions, Events |
| TickScheduler | Callbacks, Timing |
| Engine | World, Entities |
| Physics | Bodies, Collisions |
| AI System | Models, Decisions |
| Replay | Buffer, Recordings |
| Dashboard | Connections, Clients |
| World | Entities |
| PluginRegistry | Plugins |

Every object has a clear owner. Every owner has a clear lifetime.
