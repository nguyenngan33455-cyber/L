"""
Kernel Dependency Resolution Tests for Phase 26.5 Validation.

Tests dependency resolution and cycle detection.
"""

import pytest
from zbgym.kernel import (
    DependencyResolver, ModuleSpec, Dependency, DependencyType,
    CyclicDependencyError, MissingDependencyError
)


class TestDependencyResolver:
    """Test dependency resolver."""

    def test_simple_resolution(self):
        """Test simple dependency resolution."""
        resolver = DependencyResolver()
        
        resolver.register_module(ModuleSpec(name="module_a"))
        resolver.register_module(ModuleSpec(name="module_b", dependencies=[Dependency("module_a")]))
        
        order = resolver.resolve()
        
        assert order.index("module_a") < order.index("module_b")
        
    def test_chain_resolution(self):
        """Test chain dependency resolution."""
        resolver = DependencyResolver()
        
        resolver.register_module(ModuleSpec(name="a"))
        resolver.register_module(ModuleSpec(name="b", dependencies=[Dependency("a")]))
        resolver.register_module(ModuleSpec(name="c", dependencies=[Dependency("b")]))
        
        order = resolver.resolve()
        
        assert order == ["a", "b", "c"]

    def test_diamond_resolution(self):
        """Test diamond dependency resolution."""
        resolver = DependencyResolver()
        
        resolver.register_module(ModuleSpec(name="a"))
        resolver.register_module(ModuleSpec(name="b", dependencies=[Dependency("a")]))
        resolver.register_module(ModuleSpec(name="c", dependencies=[Dependency("a")]))
        resolver.register_module(ModuleSpec(name="d", dependencies=[Dependency("b"), Dependency("c")]))
        
        order = resolver.resolve()
        
        # a must come first
        assert order[0] == "a"
        # d must come last
        assert order[-1] == "d"
        # b and c must come before d
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_no_dependencies(self):
        """Test module with no dependencies."""
        resolver = DependencyResolver()
        
        resolver.register_module(ModuleSpec(name="a"))
        resolver.register_module(ModuleSpec(name="b"))
        resolver.register_module(ModuleSpec(name="c"))
        
        order = resolver.resolve()
        
        assert len(order) == 3
        assert set(order) == {"a", "b", "c"}


class TestCycleDetection:
    """Test cycle detection."""

    def test_self_cycle(self):
        """Test self-referential cycle detection."""
        resolver = DependencyResolver()
        
        resolver.register_module(ModuleSpec(name="a", dependencies=[Dependency("a")]))
        
        with pytest.raises(CyclicDependencyError):
            resolver.resolve()

    def test_two_node_cycle(self):
        """Test two-node cycle detection."""
        resolver = DependencyResolver()
        
        resolver.register_module(ModuleSpec(name="a", dependencies=[Dependency("b")]))
        resolver.register_module(ModuleSpec(name="b", dependencies=[Dependency("a")]))
        
        with pytest.raises(CyclicDependencyError):
            resolver.resolve()

    def test_three_node_cycle(self):
        """Test three-node cycle detection."""
        resolver = DependencyResolver()
        
        resolver.register_module(ModuleSpec(name="a", dependencies=[Dependency("b")]))
        resolver.register_module(ModuleSpec(name="b", dependencies=[Dependency("c")]))
        resolver.register_module(ModuleSpec(name="c", dependencies=[Dependency("a")]))
        
        with pytest.raises(CyclicDependencyError):
            resolver.resolve()


class TestMissingDependency:
    """Test missing dependency detection."""

    def test_missing_required(self):
        """Test missing required dependency."""
        resolver = DependencyResolver()
        
        resolver.register_module(ModuleSpec(name="a", dependencies=[Dependency("nonexistent")]))
        
        with pytest.raises(MissingDependencyError):
            resolver.resolve()

    def test_optional_missing(self):
        """Test missing optional dependency is allowed."""
        resolver = DependencyResolver()
        
        resolver.register_module(ModuleSpec(name="a", dependencies=[
            Dependency("nonexistent", type=DependencyType.OPTIONAL)
        ]))
        
        # Should not raise
        order = resolver.resolve()
        assert "a" in order


class TestDependencyAPI:
    """Test dependency resolver API."""

    def test_get_dependencies(self):
        """Test getting dependencies."""
        resolver = DependencyResolver()
        
        resolver.register_module(ModuleSpec(
            name="a",
            dependencies=[Dependency("b"), Dependency("c")]
        ))
        
        deps = resolver.get_dependencies("a")
        
        assert len(deps) == 2
        assert {d.name for d in deps} == {"b", "c"}

    def test_get_dependents(self):
        """Test getting dependents."""
        resolver = DependencyResolver()
        
        resolver.register_module(ModuleSpec(name="a"))
        resolver.register_module(ModuleSpec(name="b", dependencies=[Dependency("a")]))
        resolver.register_module(ModuleSpec(name="c", dependencies=[Dependency("a")]))
        
        dependents = resolver.get_dependents("a")
        
        assert set(dependents) == {"b", "c"}

    def test_unregister_module(self):
        """Test unregistering module."""
        resolver = DependencyResolver()
        
        resolver.register_module(ModuleSpec(name="a"))
        resolver.unregister_module("a")
        
        order = resolver.resolve()
        assert "a" not in order

    def test_validate_graph(self):
        """Test graph validation."""
        resolver = DependencyResolver()
        
        # Valid graph
        resolver.register_module(ModuleSpec(name="a"))
        resolver.register_module(ModuleSpec(name="b", dependencies=[Dependency("a")]))
        
        valid, errors = resolver.validate_graph()
        
        assert valid is True
        assert len(errors) == 0

    def test_validate_graph_invalid(self):
        """Test invalid graph validation."""
        resolver = DependencyResolver()
        
        # Invalid: cyclic
        resolver.register_module(ModuleSpec(name="a", dependencies=[Dependency("b")]))
        resolver.register_module(ModuleSpec(name="b", dependencies=[Dependency("a")]))
        
        valid, errors = resolver.validate_graph()
        
        assert valid is False
        assert len(errors) > 0


class TestDeterminism:
    """Test resolution determinism."""

    def test_same_result(self):
        """Test same resolution result."""
        def resolve_modules(modules):
            resolver = DependencyResolver()
            for m in modules:
                resolver.register_module(m)
            return resolver.resolve()
        
        modules = [
            ModuleSpec(name="a"),
            ModuleSpec(name="b", dependencies=[Dependency("a")]),
            ModuleSpec(name="c", dependencies=[Dependency("a")]),
        ]
        
        result1 = resolve_modules(modules)
        result2 = resolve_modules(modules)
        
        assert result1 == result2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
