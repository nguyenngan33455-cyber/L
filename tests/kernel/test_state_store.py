"""
Kernel State Store Tests for Phase 26.5 Validation.

Tests state storage and snapshot functionality.
"""

import pytest
from zbgym.kernel import (
    StateStore, StateSnapshot
)
import time


class TestStateStore:
    """Test state store operations."""

    def test_set_get(self):
        """Test basic set/get."""
        store = StateStore()
        
        store.set("key1", "value1")
        assert store.get("key1") == "value1"
        
        store.shutdown()

    def test_get_default(self):
        """Test get with default."""
        store = StateStore()
        
        assert store.get("nonexistent", "default") == "default"
        
        store.shutdown()

    def test_delete(self):
        """Test delete."""
        store = StateStore()
        
        store.set("key1", "value1")
        assert store.delete("key1") is True
        assert store.get("key1") is None
        assert store.delete("nonexistent") is False
        
        store.shutdown()

    def test_has(self):
        """Test has check."""
        store = StateStore()
        
        store.set("key1", "value1")
        assert store.has("key1") is True
        assert store.has("nonexistent") is False
        
        store.shutdown()

    def test_clear(self):
        """Test clear."""
        store = StateStore()
        
        store.set("key1", "value1")
        store.set("key2", "value2")
        store.clear()
        
        assert store.get("key1") is None
        assert store.get("key2") is None
        
        store.shutdown()

    def test_keys_values_items(self):
        """Test keys/values/items."""
        store = StateStore()
        
        store.set("key1", "value1")
        store.set("key2", "value2")
        
        assert set(store.keys()) == {"key1", "key2"}
        assert set(store.values()) == {"value1", "value2"}
        assert set(store.items()) == {("key1", "value1"), ("key2", "value2")}
        
        store.shutdown()


class TestStateSnapshot:
    """Test state snapshot functionality."""

    def test_snapshot(self):
        """Test basic snapshot."""
        store = StateStore()
        
        store.set("key1", "value1")
        store.set("key2", "value2")
        
        snapshot = store.snapshot()
        
        assert snapshot == {"key1": "value1", "key2": "value2"}
        
        store.shutdown()

    def test_restore(self):
        """Test restore from snapshot."""
        store = StateStore()
        
        store.set("key1", "value1")
        store.set("key2", "value2")
        
        snapshot = store.snapshot()
        
        # Modify state
        store.set("key1", "modified")
        assert store.get("key1") == "modified"
        
        # Restore
        store.restore(snapshot)
        assert store.get("key1") == "value1"
        assert store.get("key2") == "value2"
        
        store.shutdown()

    def test_snapshot_count(self):
        """Test snapshot count."""
        store = StateStore()
        
        store.set("key", "value")
        
        assert store.get_snapshot_count() == 0
        
        store.snapshot()
        assert store.get_snapshot_count() == 1
        
        store.snapshot()
        assert store.get_snapshot_count() == 2
        
        store.shutdown()

    def test_get_snapshots(self):
        """Test get all snapshots."""
        store = StateStore()
        
        store.set("key", "value1")
        store.snapshot()
        
        store.set("key", "value2")
        store.snapshot()
        
        snapshots = store.get_snapshots()
        assert len(snapshots) == 2
        assert snapshots[0] == {"key": "value1"}
        assert snapshots[1] == {"key": "value2"}
        
        store.shutdown()


class TestConcurrentAccess:
    """Test concurrent state access."""
    
    def test_concurrent_set_get(self):
        """Test concurrent set/get operations."""
        import threading
        
        store = StateStore()
        
        results = []
        
        def writer(thread_id):
            for i in range(100):
                store.set(f"key_{thread_id}_{i}", f"value_{thread_id}_{i}")
        
        def reader(thread_id):
            for i in range(100):
                value = store.get(f"key_{thread_id}_{i}")
                results.append(value)
        
        threads = []
        for i in range(5):
            threads.append(threading.Thread(target=writer, args=(i,)))
            threads.append(threading.Thread(target=reader, args=(i,)))
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have no errors
        assert len(results) > 0
        
        store.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
