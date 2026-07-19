"""Tests for ZBGym replay system."""

import pytest
from zbgym.replay import (
    Step,
    ReplayMetadata,
    Replay,
    ReplayBuffer,
    ReplayRecorder,
)
import numpy as np


class TestReplayMetadata:
    """Tests for ReplayMetadata."""

    def test_metadata_creation(self):
        """Test creating metadata."""
        meta = ReplayMetadata(env_id="TestEnv-v1")
        assert meta.env_id == "TestEnv-v1"
        assert meta.total_ticks == 0

    def test_metadata_to_dict(self):
        """Test converting metadata to dict."""
        meta = ReplayMetadata(env_id="TestEnv-v1")
        d = meta.to_dict()
        assert d["env_id"] == "TestEnv-v1"


class TestStep:
    """Tests for Step."""

    def test_step_creation(self):
        """Test creating a step."""
        step = Step(
            tick=0,
            state={"active": True},
            observations={"agent_0": np.array([1.0])},
            actions={"agent_0": 0},
            rewards={"agent_0": 1.0},
            dones={"agent_0": False},
            infos={},
        )
        assert step.tick == 0

    def test_step_to_dict(self):
        """Test converting step to dict."""
        step = Step(
            tick=0,
            state={"active": True},
            observations={"agent_0": np.array([1.0])},
            actions={"agent_0": 0},
            rewards={"agent_0": 1.0},
            dones={"agent_0": False},
            infos={},
        )
        d = step.to_dict()
        assert d["tick"] == 0


class TestReplay:
    """Tests for Replay."""

    def test_replay_creation(self):
        """Test creating a replay."""
        meta = ReplayMetadata(env_id="TestEnv-v1")
        replay = Replay(metadata=meta)
        assert replay.metadata.env_id == "TestEnv-v1"
        assert len(replay) == 0

    def test_add_step(self):
        """Test adding steps."""
        meta = ReplayMetadata(env_id="TestEnv-v1")
        replay = Replay(metadata=meta)

        step = Step(
            tick=0,
            state={},
            observations={},
            actions={},
            rewards={},
            dones={},
            infos={},
        )
        replay.add_step(step)
        assert len(replay) == 1

    def test_total_reward(self):
        """Test total reward calculation."""
        meta = ReplayMetadata(env_id="TestEnv-v1")
        replay = Replay(metadata=meta)

        for i in range(3):
            step = Step(
                tick=i,
                state={},
                observations={},
                actions={},
                rewards={"agent_0": 1.0},
                dones={},
                infos={},
            )
            replay.add_step(step)

        assert replay.total_reward == 3.0

    def test_compress_decompress(self):
        """Test compression."""
        meta = ReplayMetadata(env_id="TestEnv-v1")
        replay = Replay(metadata=meta)

        step = Step(
            tick=0,
            state={"data": "x" * 100},
            observations={},
            actions={},
            rewards={},
            dones={},
            infos={},
        )
        replay.add_step(step)

        compressed = replay.compress()
        assert isinstance(compressed, bytes)

        decompressed = Replay.decompress(compressed)
        assert len(decompressed) == 1


class TestReplayBuffer:
    """Tests for ReplayBuffer."""

    def test_buffer_creation(self):
        """Test creating a buffer."""
        buffer = ReplayBuffer(max_size=10)
        assert len(buffer) == 0

    def test_add_replay(self):
        """Test adding replays."""
        buffer = ReplayBuffer(max_size=10)
        meta = ReplayMetadata(env_id="TestEnv-v1")
        replay = Replay(metadata=meta)

        buffer.add(replay)
        assert len(buffer) == 1

    def test_max_size(self):
        """Test max size enforcement."""
        buffer = ReplayBuffer(max_size=2)
        for i in range(5):
            meta = ReplayMetadata(env_id="TestEnv-v1")
            buffer.add(Replay(metadata=meta))

        assert len(buffer) == 2


class TestReplayRecorder:
    """Tests for ReplayRecorder."""

    def test_recorder_creation(self):
        """Test creating a recorder."""
        recorder = ReplayRecorder("TestEnv-v1")
        assert recorder.env_id == "TestEnv-v1"

    def test_start_stop(self):
        """Test starting and stopping recording."""
        recorder = ReplayRecorder("TestEnv-v1")
        assert not recorder.is_recording()

        recorder.start()
        assert recorder.is_recording()

        replay = recorder.stop()
        assert replay is not None
        assert not recorder.is_recording()

    def test_record_step(self):
        """Test recording steps."""
        recorder = ReplayRecorder("TestEnv-v1")
        recorder.start()

        recorder.record_step(
            state={"tick": 0},
            observations={"a": np.array([1.0])},
            actions={"a": 0},
            rewards={"a": 1.0},
            dones={"a": False},
            infos={},
        )

        replay = recorder.stop()
        assert len(replay) == 1

    def test_save_load(self, tmp_path):
        """Test saving and loading."""
        recorder = ReplayRecorder("TestEnv-v1")
        recorder.start()

        recorder.record_step(
            state={"tick": 0},
            observations={},
            actions={},
            rewards={},
            dones={},
            infos={},
        )

        replay = recorder.stop()
        path = recorder.save(replay, str(tmp_path / "test.replay"))

        loaded = recorder.load(path)
        assert len(loaded) == 1
