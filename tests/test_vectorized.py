"""Tests for vectorized environments."""

import pytest

from zbgym.env.vectorized import (
    SyncVectorizedEnv,
    VectorizedBattleArena,
    VectorizedState,
    make_vectorized,
)


class TestVectorizedState:
    """Tests for VectorizedState dataclass."""

    def test_default_state(self):
        """Test default state initialization."""
        state = VectorizedState()
        assert state.num_envs == 1
        assert state.positions.shape == (1, 10, 2)
        assert state.healths.shape == (1, 10)

    def test_custom_num_envs(self):
        """Test state with custom num_envs."""
        state = VectorizedState(num_envs=8)
        assert state.num_envs == 8
        # Note: positions shape depends on default, num_envs is just metadata


class TestVectorizedBattleArena:
    """Tests for VectorizedBattleArena."""

    def test_init_small_num_envs(self):
        """Test that small num_envs (e.g., 8) works."""
        # Previously this would raise ValueError
        env = VectorizedBattleArena(num_envs=8)
        assert env.num_envs == 8
        env.close()

    def test_init_standard_num_envs(self):
        """Test standard num_envs values."""
        for num in [32, 64, 128]:
            env = VectorizedBattleArena(num_envs=num)
            assert env.num_envs == num
            env.close()

    def test_init_invalid_num_envs(self):
        """Test that invalid num_envs raises error."""
        with pytest.raises(ValueError):
            VectorizedBattleArena(num_envs=0)

        with pytest.raises(ValueError):
            VectorizedBattleArena(num_envs=-1)

    def test_reset(self):
        """Test reset returns observations."""
        env = VectorizedBattleArena(num_envs=4)
        obs, infos = env.reset()

        assert obs.shape[0] == 4  # num_envs
        assert len(infos) == 4
        env.close()

    def test_reset_with_seeds(self):
        """Test reset with seeds."""
        env = VectorizedBattleArena(num_envs=4)
        seeds = [1, 2, 3, 4]
        obs, infos = env.reset(seeds=seeds)

        assert obs.shape[0] == 4
        assert len(infos) == 4
        env.close()

    def test_get_state(self):
        """Test get_state returns VectorizedState."""
        env = VectorizedBattleArena(num_envs=2)
        env.reset()

        state = env.get_state()
        assert isinstance(state, VectorizedState)
        assert state.num_envs == 2
        env.close()


class TestSyncVectorizedEnv:
    """Tests for SyncVectorizedEnv."""

    def test_init(self):
        """Test sync vectorized env initialization."""
        env = SyncVectorizedEnv(num_envs=256)
        assert env.num_envs == 256
        env.close()


class TestMakeVectorized:
    """Tests for make_vectorized factory function."""

    def test_make_vectorized(self):
        """Test factory function."""
        env = make_vectorized(num_envs=8)
        assert isinstance(env, VectorizedBattleArena)
        assert env.num_envs == 8
        env.close()
