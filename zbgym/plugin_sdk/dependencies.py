"""Plugin dependency resolver."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zbgym.plugin_sdk.base import PluginBase, PluginMetadata

logger = logging.getLogger(__name__)


@dataclass
class DependencyNode:
    """Node in the dependency graph."""

    plugin: PluginBase
    required_by: list[str] = None

    def __post_init__(self) -> None:
        if self.required_by is None:
            self.required_by = []


class DependencyResolver:
    """
    Resolves plugin dependencies.

    Validates:
    - Required dependencies exist
    - Version compatibility
    - No circular dependencies
    """

    def __init__(self) -> None:
        """Initialize the dependency resolver."""
        self._graph: dict[str, DependencyNode] = {}

    def add_plugin(self, plugin: PluginBase) -> None:
        """
        Add a plugin to the dependency graph.

        Args:
            plugin: Plugin to add
        """
        self._graph[plugin.name] = DependencyNode(plugin=plugin)

    def resolve(self) -> tuple[bool, list[str]]:
        """
        Resolve dependencies.

        Returns:
            Tuple of (success, error_messages)
        """
        errors = []

        # Build required_by relationships
        for name, node in self._graph.items():
            for dep in node.plugin.metadata.dependencies:
                if dep in self._graph:
                    self._graph[dep].required_by.append(name)

        # Check for circular dependencies
        circular = self._detect_cycles()
        if circular:
            errors.append(f"Circular dependency detected: {' -> '.join(circular)}")

        # Check for missing dependencies
        for name, node in self._graph.items():
            for dep in node.plugin.metadata.dependencies:
                if dep not in self._graph:
                    errors.append(f"Plugin '{name}' requires missing dependency: '{dep}'")

        # Check for missing optional dependencies (warning only)
        for name, node in self._graph.items():
            for dep in node.plugin.metadata.optional_dependencies:
                if dep not in self._graph:
                    logger.warning(
                        f"Plugin '{name}' has optional dependency '{dep}' "
                        "that is not installed"
                    )

        # Check version compatibility
        for name, node in self._graph.items():
            for dep_name in node.plugin.metadata.dependencies:
                if dep_name in self._graph:
                    dep_node = self._graph[dep_name]
                    if not dep_node.plugin.metadata.is_compatible_with(
                        node.plugin.metadata.minimum_zbgym_version
                    ):
                        errors.append(
                            f"Plugin '{name}' requires {node.plugin.metadata.minimum_zbgym_version}+ "
                            f"but '{dep_name}' is version {dep_node.plugin.version}"
                        )

        return len(errors) == 0, errors

    def _detect_cycles(self) -> list[str] | None:
        """Detect circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> list[str] | None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            if node in self._graph:
                for dep in self._graph[node].plugin.metadata.dependencies:
                    if dep in self._graph:
                        if dep not in visited:
                            result = dfs(dep)
                            if result:
                                return result
                        elif dep in rec_stack:
                            cycle_start = path.index(dep)
                            return path[cycle_start:] + [dep]

            path.pop()
            rec_stack.remove(node)
            return None

        for node in self._graph:
            if node not in visited:
                cycle = dfs(node)
                if cycle:
                    return cycle

        return None

    def get_load_order(self) -> list[str]:
        """
        Get plugins in dependency order (dependencies first).

        Returns:
            List of plugin names in load order
        """
        # Simple topological sort
        visited = set()
        order = []

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)

            if name in self._graph:
                for dep in self._graph[name].plugin.metadata.dependencies:
                    if dep in self._graph:
                        visit(dep)

            order.append(name)

        for name in self._graph:
            visit(name)

        return order

    def get_reverse_load_order(self) -> list[str]:
        """Get plugins in reverse dependency order."""
        return list(reversed(self.get_load_order()))

    def get_dependency_tree(self, plugin_name: str) -> dict[str, list[str]]:
        """
        Get dependency tree for a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            Dictionary mapping plugin names to their dependencies
        """
        if plugin_name not in self._graph:
            return {}

        tree = {}

        def collect(name: str, seen: set[str] | None = None) -> None:
            if seen is None:
                seen = set()

            if name in seen:
                return

            seen.add(name)

            if name in self._graph:
                deps = self._graph[name].plugin.metadata.dependencies
                tree[name] = deps

                for dep in deps:
                    collect(dep, seen)

        collect(plugin_name)
        return tree

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the dependency graph.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        return self.resolve()

    def clear(self) -> None:
        """Clear the dependency graph."""
        self._graph.clear()
