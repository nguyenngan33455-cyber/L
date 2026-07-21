"""Tests for ZBGym engine modules."""

import pytest

from zbgym.engine.event_bus import Event, EventBus
from zbgym.engine.map import MapData, MapManager
from zbgym.engine.spawn import SpawnConfig, SpawnSystem
from zbgym.engine.tick_system import TickSystem
from zbgym.physics.vector import Vector2D


class TestEventBus:
    """Tests for EventBus."""

    def test_subscribe_and_emit(self):
        """Test basic subscribe and emit."""
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("test_event", handler)
        bus.emit(Event(type="test_event", data={"value": 42}))

        assert len(received) == 1
        assert received[0].data["value"] == 42

    def test_unsubscribe(self):
        """Test unsubscribe."""
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        sub_id = bus.subscribe("test_event", handler)
        bus.unsubscribe(sub_id)
        bus.emit(Event(type="test_event"))

        assert len(received) == 0

    def test_once_subscription(self):
        """Test one-time subscription."""
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("test_event", handler, once=True)
        bus.emit(Event(type="test_event"))
        bus.emit(Event(type="test_event"))

        assert len(received) == 1

    def test_event_history(self):
        """Test event history."""
        bus = EventBus()
        bus.emit(Event(type="test_event"))
        bus.emit(Event(type="test_event"))

        history = bus.get_history(limit=10)
        assert len(history) == 2


class TestTickSystem:
    """Tests for TickSystem."""

    def test_tick(self):
        """Test basic tick."""
        system = TickSystem(tick_rate=60)
        assert system.tick_rate == 60
        assert system.current_tick == 0

    def test_register_callback(self):
        """Test callback registration."""
        system = TickSystem()
        called = []

        def callback(dt):
            called.append(dt)

        cb_id = system.register_callback(callback)
        system.start()
        system.tick()

        assert len(called) == 1
        assert cb_id is not None

    def test_unregister_callback(self):
        """Test callback unregistration."""
        system = TickSystem()
        called = []

        def callback(dt):
            called.append(dt)

        cb_id = system.register_callback(callback)
        system.unregister_callback(cb_id)
        system.tick()

        assert len(called) == 0


class TestMapManager:
    """Tests for MapManager."""

    def test_register_and_load_map(self):
        """Test map registration and loading."""
        manager = MapManager()
        map_data = MapData(
            id="test_map",
            name="Test Map",
            width=1000,
            height=1000,
        )
        manager.register_map(map_data)

        loaded = manager.load_map("test_map")
        assert loaded.id == "test_map"
        assert loaded.width == 1000

    def test_default_map(self):
        """Test default map."""
        manager = MapManager()
        loaded = manager.load_map("default")

        assert loaded is not None
        assert len(loaded.spawn_points) == 4
        assert len(loaded.obstacles) == 4


class TestSpawnSystem:
    """Tests for SpawnSystem."""

    def test_spawn_request(self):
        """Test spawn request."""
        manager = MapManager()
        manager.load_map("default")

        system = SpawnSystem(map_manager=manager)
        success = system.request_spawn("player_1", "red")

        assert success is True

    def test_spawn_protection(self):
        """Test spawn protection."""
        system = SpawnSystem(config=SpawnConfig(spawn_protection_time=2.0))
        system._spawn_protections["player_1"] = 2.0

        assert system.is_spawn_protected("player_1") is True


class TestPhysicsVector:
    """Tests for Vector2D."""

    def test_vector_creation(self):
        """Test vector creation."""
        v = Vector2D(3.0, 4.0)
        assert v.x == 3.0
        assert v.y == 4.0

    def test_vector_operations(self):
        """Test vector operations."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, 4.0)

        # Addition
        v3 = v1 + v2
        assert v3.x == 4.0
        assert v3.y == 6.0

        # Subtraction
        v4 = v2 - v1
        assert v4.x == 2.0
        assert v4.y == 2.0

        # Multiplication
        v5 = v1 * 2.0
        assert v5.x == 2.0
        assert v5.y == 4.0

    def test_vector_length(self):
        """Test vector length."""
        v = Vector2D(3.0, 4.0)
        assert v.length == 5.0

    def test_vector_normalized(self):
        """Test vector normalization."""
        v = Vector2D(3.0, 4.0)
        n = v.normalized
        assert abs(n.length - 1.0) < 0.001

    def test_vector_distance(self):
        """Test distance calculation."""
        v1 = Vector2D(0.0, 0.0)
        v2 = Vector2D(3.0, 4.0)
        assert v1.distance_to(v2) == 5.0

    def test_vector_dot(self):
        """Test dot product."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, 4.0)
        assert v1.dot(v2) == 11.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
