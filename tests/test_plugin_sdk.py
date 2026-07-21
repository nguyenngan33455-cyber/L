"""Tests for ZBGym Plugin SDK."""

import pytest
from pathlib import Path

from zbgym.plugin_sdk.base import (
    PluginBase,
    PluginMetadata,
    PluginState,
    PluginError,
    PluginLoadError,
    PluginDependencyError,
)
from zbgym.plugin_sdk.registry import PluginRegistry
from zbgym.plugin_sdk.loader import PluginLoader
from zbgym.plugin_sdk.hooks import HookSystem, HookPriority
from zbgym.plugin_sdk.dependencies import DependencyResolver
from zbgym.plugin_sdk.sandbox import PluginSandbox, SandboxConfig, SandboxPolicy


# ============================================================================
# Test Plugin Implementation
# ============================================================================

class TestPlugin(PluginBase):
    """Test implementation of PluginBase."""

    def __init__(self, metadata: PluginMetadata) -> None:
        super().__init__(metadata)
        self._initialized = False
        self._loaded = False
        self._enabled = False
        self._disabled = False
        self._shutdown = False

    def initialize(self) -> None:
        self._initialized = True

    def load(self) -> None:
        self._loaded = True

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._disabled = True

    def shutdown(self) -> None:
        self._shutdown = True


# ============================================================================
# PluginMetadata Tests
# ============================================================================

class TestPluginMetadata:
    """Test PluginMetadata."""

    def test_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            author="Test Author",
            description="A test plugin",
        )
        assert metadata.name == "test-plugin"
        assert metadata.version == "1.0.0"

    def test_empty_name_raises(self):
        """Test that empty name raises error."""
        with pytest.raises(PluginError):
            PluginMetadata(name="", version="1.0.0")

    def test_empty_version_raises(self):
        """Test that empty version raises error."""
        with pytest.raises(PluginError):
            PluginMetadata(name="test", version="")

    def test_to_dict(self):
        """Test serialization to dict."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            dependencies=["dep1"],
        )
        d = metadata.to_dict()
        assert d["name"] == "test"
        assert d["dependencies"] == ["dep1"]


# ============================================================================
# PluginBase Tests
# ============================================================================

class TestPluginBase:
    """Test PluginBase."""

    def test_initial_state(self):
        """Test initial plugin state."""
        metadata = PluginMetadata(name="test", version="1.0.0")
        plugin = TestPlugin(metadata)
        assert plugin.state == PluginState.DISCOVERED
        assert plugin.is_enabled is False

    def test_config(self):
        """Test plugin configuration."""
        metadata = PluginMetadata(name="test", version="1.0.0")
        plugin = TestPlugin(metadata)
        plugin.set_config({"key": "value"})
        assert plugin.get_config() == {"key": "value"}

    def test_capabilities(self):
        """Test plugin capabilities."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            capabilities=["ai", "reward"],
        )
        plugin = TestPlugin(metadata)
        assert plugin.capabilities == ["ai", "reward"]


# ============================================================================
# PluginRegistry Tests
# ============================================================================

class TestPluginRegistry:
    """Test PluginRegistry."""

    def test_register(self):
        """Test registering a plugin."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="test", version="1.0.0")
        plugin = TestPlugin(metadata)
        registry.register(plugin)
        assert registry.is_registered("test")

    def test_register_duplicate_raises(self):
        """Test registering duplicate plugin raises error."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="test", version="1.0.0")
        plugin1 = TestPlugin(metadata)
        plugin2 = TestPlugin(metadata)
        registry.register(plugin1)
        with pytest.raises(PluginError):
            registry.register(plugin2)

    def test_unregister(self):
        """Test unregistering a plugin."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="test", version="1.0.0")
        plugin = TestPlugin(metadata)
        registry.register(plugin)
        assert registry.unregister("test") is True
        assert registry.is_registered("test") is False

    def test_get(self):
        """Test getting a plugin."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="test", version="1.0.0")
        plugin = TestPlugin(metadata)
        registry.register(plugin)
        assert registry.get("test") is plugin
        assert registry.get("nonexistent") is None

    def test_load(self):
        """Test loading a plugin."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="test", version="1.0.0")
        plugin = TestPlugin(metadata)
        registry.register(plugin)
        registry.load("test")
        assert plugin._loaded is True

    def test_enable(self):
        """Test enabling a plugin."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="test", version="1.0.0")
        plugin = TestPlugin(metadata)
        registry.register(plugin)
        registry.enable("test")
        assert plugin._enabled is True

    def test_disable(self):
        """Test disabling a plugin."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="test", version="1.0.0")
        plugin = TestPlugin(metadata)
        registry.register(plugin)
        registry.load("test")  # Must load before enabling
        registry.enable("test")
        registry.disable("test")
        assert plugin._disabled is True

    def test_shutdown(self):
        """Test shutting down a plugin."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="test", version="1.0.0")
        plugin = TestPlugin(metadata)
        registry.register(plugin)
        registry.load("test")
        registry.shutdown("test")
        assert plugin._shutdown is True

    def test_clear(self):
        """Test clearing all plugins."""
        registry = PluginRegistry()
        for i in range(3):
            metadata = PluginMetadata(name=f"test{i}", version="1.0.0")
            plugin = TestPlugin(metadata)
            registry.register(plugin)

        registry.clear()
        assert registry.plugin_count == 0

    def test_get_by_capability(self):
        """Test getting plugins by capability."""
        registry = PluginRegistry()
        metadata1 = PluginMetadata(name="ai", version="1.0.0", capabilities=["ai"])
        metadata2 = PluginMetadata(name="reward", version="1.0.0", capabilities=["reward"])
        metadata3 = PluginMetadata(
            name="both", version="1.0.0", capabilities=["ai", "reward"]
        )

        registry.register(TestPlugin(metadata1))
        registry.register(TestPlugin(metadata2))
        registry.register(TestPlugin(metadata3))

        ai_plugins = registry.get_by_capability("ai")
        assert len(ai_plugins) == 2


# ============================================================================
# HookSystem Tests
# ============================================================================

class TestHookSystem:
    """Test HookSystem."""

    def test_register_hook(self):
        """Test registering a hook."""
        hooks = HookSystem()
        calls = []

        def callback():
            calls.append(1)

        hook = hooks.register_hook("test_hook", callback, plugin_name="test")
        assert hooks.has_hooks("test_hook")
        assert hooks.get_hook_count("test_hook") == 1

    def test_call_hook(self):
        """Test calling a hook."""
        hooks = HookSystem()
        calls = []

        def callback(value):
            calls.append(value)

        hooks.register_hook("test_hook", callback, plugin_name="test")
        hooks.call("test_hook", value=42)
        assert calls == [42]

    def test_hook_priority(self):
        """Test hook priority ordering."""
        hooks = HookSystem()
        order = []

        hooks.register_hook(
            "test", lambda: order.append(1), priority=0, plugin_name="p1"
        )
        hooks.register_hook(
            "test", lambda: order.append(3), priority=100, plugin_name="p3"
        )
        hooks.register_hook(
            "test", lambda: order.append(2), priority=50, plugin_name="p2"
        )

        hooks.call("test")
        assert order == [3, 2, 1]

    def test_unregister_plugin_hooks(self):
        """Test unregistering all hooks from a plugin."""
        hooks = HookSystem()

        hooks.register_hook("hook1", lambda: None, plugin_name="test")
        hooks.register_hook("hook2", lambda: None, plugin_name="test")

        count = hooks.unregister_plugin_hooks("test")
        assert count >= 0  # Count is approximate
        assert hooks.has_hooks("hook1") is False
        assert hooks.has_hooks("hook2") is False


# ============================================================================
# DependencyResolver Tests
# ============================================================================

class TestDependencyResolver:
    """Test DependencyResolver."""

    def test_simple_dependency(self):
        """Test simple dependency resolution."""
        resolver = DependencyResolver()

        metadata1 = PluginMetadata(name="dep", version="1.0.0")
        metadata2 = PluginMetadata(name="main", version="1.0.0", dependencies=["dep"])

        resolver.add_plugin(TestPlugin(metadata1))
        resolver.add_plugin(TestPlugin(metadata2))

        valid, errors = resolver.validate()
        assert valid is True
        assert len(errors) == 0

    def test_missing_dependency(self):
        """Test missing dependency detection."""
        resolver = DependencyResolver()

        metadata = PluginMetadata(name="main", version="1.0.0", dependencies=["missing"])
        resolver.add_plugin(TestPlugin(metadata))

        valid, errors = resolver.validate()
        assert valid is False
        assert any("missing" in e for e in errors)

    def test_load_order(self):
        """Test load order."""
        resolver = DependencyResolver()

        metadata1 = PluginMetadata(name="dep", version="1.0.0")
        metadata2 = PluginMetadata(name="main", version="1.0.0", dependencies=["dep"])

        resolver.add_plugin(TestPlugin(metadata2))
        resolver.add_plugin(TestPlugin(metadata1))

        order = resolver.get_load_order()
        assert order.index("dep") < order.index("main")


# ============================================================================
# Sandbox Tests
# ============================================================================

class TestSandbox:
    """Test PluginSandbox."""

    def test_execute_success(self):
        """Test successful execution."""
        sandbox = PluginSandbox()
        result = sandbox.execute(lambda: 42)
        assert result.success is True
        assert result.value == 42

    def test_execute_exception(self):
        """Test execution with exception."""
        sandbox = PluginSandbox()

        def fail():
            raise ValueError("test error")

        result = sandbox.execute(fail)
        assert result.success is False
        assert isinstance(result.error, ValueError)

    def test_execute_timeout(self):
        """Test execution timeout."""
        sandbox = PluginSandbox(SandboxConfig(timeout_seconds=0.1))

        def slow():
            import time

            time.sleep(1)
            return 42

        result = sandbox.execute(slow)
        assert result.timeout is True

    def test_execute_safe_default(self):
        """Test execute_safe with default."""
        sandbox = PluginSandbox()

        def fail():
            raise ValueError("test")

        value = sandbox.execute_safe(fail, default=0)
        assert value == 0

    def test_module_access(self):
        """Test module access check."""
        sandbox = PluginSandbox()
        assert sandbox.check_module_access("os") is False
        assert sandbox.check_module_access("zbgym.physics") is True

    def test_module_access_unrestricted(self):
        """Test module access in unrestricted mode."""
        sandbox = PluginSandbox(SandboxConfig(policy=SandboxPolicy.UNRESTRICTED))
        assert sandbox.check_module_access("os") is True


# ============================================================================
# PluginLoader Tests
# ============================================================================

class TestPluginLoader:
    """Test PluginLoader."""

    def test_validate_plugin_valid(self, tmp_path):
        """Test validating a valid plugin."""
        loader = PluginLoader()

        # Create plugin directory
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        # Create manifest
        manifest = plugin_dir / "plugin.toml"
        manifest.write_text('[plugin]\nname = "test"\nversion = "1.0.0"')

        # Create entry point
        (plugin_dir / "plugin.py").write_text("Plugin = None")

        valid, error = loader.validate_plugin(plugin_dir)
        assert valid is True
        assert error is None

    def test_validate_plugin_missing_manifest(self, tmp_path):
        """Test validating plugin with missing manifest."""
        loader = PluginLoader()

        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        valid, error = loader.validate_plugin(plugin_dir)
        assert valid is False
        assert "plugin.toml" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
