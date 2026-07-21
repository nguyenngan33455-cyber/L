"""
DependencyResolver implementation for ZBGym Kernel.

Resolves module dependencies using topological sort.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class DependencyType(Enum):
    """Dependency type enumeration."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    SOFT = "soft"


@dataclass
class Dependency:
    """Represents a module dependency."""
    name: str
    type: DependencyType = DependencyType.REQUIRED
    version: str | None = None


@dataclass
class ModuleSpec:
    """Module specification for dependency resolution."""
    name: str
    dependencies: list[Dependency] = field(default_factory=list)
    version: str = "1.0.0"
    metadata: dict = field(default_factory=dict)


class DependencyError(Exception):
    """Exception raised for dependency errors."""
    pass


class CyclicDependencyError(DependencyError):
    """Exception raised for cyclic dependencies."""
    pass


class MissingDependencyError(DependencyError):
    """Exception raised for missing dependencies."""
    pass


class DependencyResolver:
    """
    Resolves module dependencies using topological sort.
    
    Supports required, optional, and soft dependencies.
    Validates dependency graph for cycles.
    """

    def __init__(self) -> None:
        """Initialize the dependency resolver."""
        self._modules: dict[str, ModuleSpec] = {}
        self._graph: dict[str, set[str]] = {}

    def register_module(self, spec: ModuleSpec) -> None:
        """
        Register a module specification.
        
        Args:
            spec: Module specification
        """
        self._modules[spec.name] = spec
        self._graph[spec.name] = {dep.name for dep in spec.dependencies}

    def unregister_module(self, name: str) -> bool:
        """
        Unregister a module.
        
        Args:
            name: Module name
            
        Returns:
            True if unregistered
        """
        if name not in self._modules:
            return False

        del self._modules[name]
        del self._graph[name]

        # Remove from other graphs
        for deps in self._graph.values():
            deps.discard(name)

        return True

    def resolve(self) -> list[str]:
        """
        Resolve dependencies and return load order.
        
        Returns:
            List of module names in dependency order
            
        Raises:
            CyclicDependencyError: If cycle detected
            MissingDependencyError: If required dependency missing
        """
        # Validate required dependencies exist
        self._validate_dependencies()

        # Detect cycles
        self._detect_cycles()

        # Topological sort (Kahn's algorithm)
        return self._topological_sort()

    def _validate_dependencies(self) -> None:
        """Validate all required dependencies exist."""
        available = set(self._modules.keys())

        for name, spec in self._modules.items():
            for dep in spec.dependencies:
                if dep.type == DependencyType.REQUIRED and dep.name not in available:
                    raise MissingDependencyError(
                        f"Module '{name}' requires '{dep.name}' but it is not registered"
                    )

    def _detect_cycles(self) -> None:
        """Detect cycles in dependency graph."""
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    raise CyclicDependencyError(
                        f"Cyclic dependency detected: {' -> '.join(cycle)}"
                    )

            path.pop()
            rec_stack.remove(node)

        for module in self._modules:
            if module not in visited:
                dfs(module)

    def _topological_sort(self) -> list[str]:
        """
        Perform topological sort using Kahn's algorithm.
        
        Returns:
            List of modules in dependency order
        """
        # Calculate in-degree for each node
        in_degree: dict[str, int] = {name: 0 for name in self._modules}

        for name, deps in self._graph.items():
            for dep in deps:
                in_degree[name] += 1

        # Start with nodes that have no dependencies
        queue: list[str] = [name for name, degree in in_degree.items() if degree == 0]
        result: list[str] = []

        while queue:
            # Sort for determinism
            queue.sort()
            node = queue.pop(0)
            result.append(node)

            # Reduce in-degree for dependent nodes
            for name, deps in self._graph.items():
                if node in deps:
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)

        return result

    def get_dependencies(self, name: str) -> list[Dependency]:
        """
        Get dependencies for a module.
        
        Args:
            name: Module name
            
        Returns:
            List of dependencies
        """
        spec = self._modules.get(name)
        if spec is None:
            return []
        return spec.dependencies

    def get_dependents(self, name: str) -> list[str]:
        """
        Get modules that depend on this module.
        
        Args:
            name: Module name
            
        Returns:
            List of dependent module names
        """
        dependents = []
        for module_name, deps in self._graph.items():
            if name in deps:
                dependents.append(module_name)
        return dependents

    def get_resolution_order(self, name: str) -> list[str]:
        """
        Get resolution order for a specific module.
        
        Args:
            name: Module name
            
        Returns:
            List of modules needed before this one
        """
        order = self.resolve()
        if name not in order:
            return []
        idx = order.index(name)
        return order[:idx]

    def validate_graph(self) -> tuple[bool, list[str]]:
        """
        Validate the dependency graph.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors: list[str] = []

        # Check for missing required dependencies
        for name, spec in self._modules.items():
            for dep in spec.dependencies:
                if dep.type == DependencyType.REQUIRED and dep.name not in self._modules:
                    errors.append(
                        f"Module '{name}' requires missing dependency '{dep.name}'"
                    )

        # Check for cycles
        try:
            self._detect_cycles()
        except CyclicDependencyError as e:
            errors.append(str(e))

        return (len(errors) == 0, errors)
