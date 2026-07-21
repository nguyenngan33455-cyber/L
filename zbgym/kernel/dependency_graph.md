# ZBGym Dependency Graph

## Overview

The DependencyResolver builds and manages the module dependency graph. All dependencies must be resolved before modules can be initialized.

---

## Dependency Types

### 1. Required Dependencies

Module **must** have dependency to function.

```toml
[plugin]
dependencies = ["engine", "event-bus"]
```

```python
# If dependency unavailable, module cannot initialize
```

### 2. Optional Dependencies

Module **can** function without dependency.

```toml
[plugin]
optional-dependencies = ["dashboard", "metrics"]
```

```python
# Module initializes even if dependency unavailable
# Must check availability at runtime
```

### 3. Soft Dependencies

Module **prefers** dependency but works without.

```toml
[plugin]
soft-dependencies = ["replay"]
```

```python
# Full functionality with dependency
# Reduced functionality without
```

---

## Dependency Declaration

### Plugin Manifest

```toml
[plugin]
name = "my-plugin"
version = "1.0.0"

# Required modules
dependencies = [
    "engine",
    "physics",
    "ai-scheduler"
]

# Optional modules
optional-dependencies = [
    "dashboard",
    "replay"
]

# Framework version requirement
minimum-zbgym-version = "1.0.0"
```

### Module Registration

```python
class MyModule(ModuleInterface):
    @staticmethod
    def get_dependencies() -> list[str]:
        return ["engine", "physics", "ai-scheduler"]
    
    @staticmethod
    def get_optional_dependencies() -> list[str]:
        return ["dashboard", "replay"]
```

---

## Dependency Graph Structure

```python
@dataclass
class DependencyNode:
    """Node in dependency graph."""
    
    module_name: str
    module: ModuleInterface
    dependencies: list[str]      # Required
    optional_dependencies: list[str]  # Optional
    dependents: list[str]         # Modules depending on this
    state: ModuleState
    version: str
    
@dataclass
class DependencyGraph:
    """Complete dependency graph."""
    
    nodes: dict[str, DependencyNode]
    edges: list[tuple[str, str]]  # (dependent, dependency)
    cycles: list[list[str]]        # Detected cycles
    
    def add_module(self, module: ModuleInterface) -> None:
        """Add module to graph."""
        pass
    
    def remove_module(self, module_name: str) -> None:
        """Remove module from graph."""
        pass
    
    def get_load_order(self) -> list[str]:
        """Compute topological sort order."""
        pass
```

---

## Graph Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    Dependency Graph                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│    Dashboard ───────────────────────┐                      │
│         │                           │                      │
│         │                           ▼                      │
│         │                    ┌────────────┐                │
│         │                    │    AI      │                │
│         │                    └─────┬──────┘                │
│         │                          │                        │
│         ▼                          │                        │
│  ┌────────────┐                   │                        │
│  │  Replay    │                   │                        │
│  └─────┬──────┘                   │                        │
│        │                          │                        │
│        │         ┌────────────────┴────────────────┐       │
│        │         │                                 │       │
│        ▼         ▼                                 ▼       │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────────┐  │
│  │  Physics   │──│  Engine    │──│  ActionQueue        │  │
│  └────────────┘  └────────────┘  └─────────────────────┘  │
│        │                                                        │
│        │                                                        │
│        ▼                                                        │
│  ┌────────────┐                                                │
│  │ Collision  │                                                │
│  └────────────┘                                                │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Load Order:** Collision → Physics → Engine → ActionQueue → AI → Replay → Dashboard

---

## Resolution Algorithm

### Step 1: Build Graph

```
1. For each module:
   a. Parse dependencies from manifest
   b. Create DependencyNode
   c. Add to graph
```

### Step 2: Validate Nodes

```
1. Check all required dependencies exist
2. Check version compatibility
3. Check capability availability
```

### Step 3: Detect Cycles

```
1. Run DFS from each unvisited node
2. Track recursion stack
3. If node in stack found, cycle detected
4. Return cycle path
```

### Step 4: Topological Sort

```
1. Kahn's algorithm:
   a. Calculate in-degree for each node
   b. Add all zero in-degree nodes to queue
   c. For each node in queue:
      - Add to result
      - Decrease in-degree of dependents
      - Add newly zero nodes to queue
   d. If result size < node count, cycle exists
```

---

## Resolution Rules

### Rule 1: Dependencies First

```
Module can only load after all dependencies load
```

### Rule 2: Version Compatibility

```
Module version must be compatible with declared minimum
```

### Rule 3: No Cycles

```
Circular dependencies are not allowed
```

### Rule 4: Optional First

```
Optional dependencies resolved before required
```

### Rule 5: Capability Check

```
Module must have required capabilities
```

---

## Version Compatibility

### Semantic Versioning

```
major.minor.patch
```

| Change Type | Compatibility |
|-------------|---------------|
| Patch | Fully compatible |
| Minor | Backward compatible |
| Major | Incompatible |

### Version Ranges

```toml
[plugin]
# Exact version
dependencies = ["engine@1.0.0"]

# Minimum version
dependencies = ["engine@>=1.0.0"]

# Range
dependencies = ["engine@>=1.0.0,<2.0.0"]

# Any compatible
dependencies = ["engine@~1.0"]
```

---

## Error Cases

### 1. Missing Dependency

```
Module "my-plugin" requires "engine" which is not available
```

**Action:** Fail resolution, list missing dependencies

### 2. Version Mismatch

```
Module "my-plugin" requires "engine>=2.0.0" but "engine@1.0.0" is available
```

**Action:** Fail resolution, suggest upgrade

### 3. Circular Dependency

```
A → B → C → A (cycle detected)
```

**Action:** Fail resolution, show cycle path

### 4. Conflicting Versions

```
Plugin A requires "engine@1.0.0"
Plugin B requires "engine@2.0.0"
```

**Action:** Fail resolution, no compatible version

### 5. Missing Capability

```
Module "my-plugin" requires "physics" capability not provided
```

**Action:** Fail resolution, list required capabilities

---

## Load Order Computation

### Example

```
Modules:
- A (depends on B, C)
- B (depends on C)
- C (no deps)
- D (no deps)

Graph:
A → B → C
A → C
B → C
C
D

Topological Sort:
1. C (no deps)
2. B (only depends on C, which is done)
3. A (depends on B, C, both done)
4. D (no deps)

Load Order: C, B, A, D
```

### Implementation

```python
def get_load_order(self) -> list[str]:
    """
    Compute topological sort using Kahn's algorithm.
    
    Returns:
        List of module names in load order
    """
    # Calculate in-degrees
    in_degree = {name: 0 for name in self.nodes}
    for node in self.nodes.values():
        in_degree[node.module_name] = len(node.dependencies)
    
    # Start with zero in-degree nodes
    queue = deque([
        name for name, degree in in_degree.items() 
        if degree == 0
    ])
    
    result = []
    
    while queue:
        # Process node
        current = queue.popleft()
        result.append(current)
        
        # Update dependents
        node = self.nodes[current]
        for dependent_name in node.dependents:
            in_degree[dependent_name] -= 1
            if in_degree[dependent_name] == 0:
                queue.append(dependent_name)
    
    # Check for cycles
    if len(result) != len(self.nodes):
        raise CyclicDependencyError(self._detect_cycle())
    
    return result
```

---

## Dynamic Dependencies

### Runtime Dependency Addition

```python
class ModuleManager:
    def add_dependency(
        self,
        module_name: str,
        dependency: str
    ) -> None:
        """Add dependency at runtime."""
        if module_name not in self._graph.nodes:
            raise ModuleNotFoundError(module_name)
        
        if dependency not in self._graph.nodes:
            raise DependencyNotFoundError(dependency)
        
        # Update graph
        self._graph.nodes[module_name].dependencies.append(dependency)
        self._graph.nodes[dependency].dependents.append(module_name)
        
        # Validate no cycles
        if self._graph.has_cycle():
            raise CyclicDependencyError()
```

### Runtime Dependency Removal

```python
def remove_dependency(
    self,
    module_name: str,
    dependency: str
) -> None:
    """Remove dependency at runtime."""
    # Check if module depends on it
    if dependency in self._graph.nodes[module_name].dependencies:
        # Check if other modules depend on it
        if len(self._graph.nodes[dependency].dependents) > 1:
            self._graph.nodes[module_name].dependencies.remove(dependency)
            self._graph.nodes[dependency].dependents.remove(module_name)
        else:
            raise DependencyInUseError(dependency)
```

---

## Dependency Injection

### Constructor Injection

```python
class Module:
    def __init__(self, deps: Dependencies) -> None:
        self._engine = deps.get(Engine)
        self._physics = deps.get(Physics)
```

### Property Injection

```python
class Module:
    def set_dependencies(self, deps: Dependencies) -> None:
        self._engine = deps.get(Engine)
```

### Interface Injection

```python
class Module(ModuleInterface):
    def inject_dependencies(
        self,
        engine: Engine,
        physics: Physics
    ) -> None:
        self._engine = engine
        self._physics = physics
```

---

## Conflict Resolution

### Version Conflicts

```
When two plugins require incompatible versions:
1. Check for compatible overlap
2. If overlap exists, use overlap
3. If no overlap, fail resolution
```

### Capability Conflicts

```
When two modules provide same capability:
1. First registered wins
2. Or explicit override in config
```

---

## Summary

Key dependency management principles:

1. **Explicit Declaration**: All dependencies declared
2. **Validation**: All dependencies validated before use
3. **Topological Sort**: Load order computed from graph
4. **No Cycles**: Circular dependencies rejected
5. **Versioning**: Semantic versioning with compatibility
6. **Optional Support**: Graceful handling of optional deps
7. **Dynamic Updates**: Runtime dependency changes supported
