"""Tests for ZBGym replay system."""

import numpy as np

from zbgym.replay import (
    Replay,
    ReplayBuffer,
    ReplayMetadata,
    ReplayRecorder,
    Step,
)


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


# ============================================================
# Tests for replay/deterministic.py
# ============================================================

from zbgym.replay.deterministic import (
    Action,
    DeterministicPlayer,
    DeterministicRecorder,
    DeterministicReplay,
    Event,
    ReplayStep,
    StateSnapshot,
)


class TestAction:
    """Tests for Action dataclass."""

    def test_action_creation(self):
        """Test creating an action."""
        action = Action(
            agent_id="agent_0",
            action_type="move",
            action_data={"x": 1.0, "y": 0.0},
            tick=0,
            seed=42,
        )
        assert action.agent_id == "agent_0"
        assert action.action_type == "move"
        assert action.tick == 0
        assert action.seed == 42

    def test_action_to_dict(self):
        """Test converting action to dict."""
        action = Action(
            agent_id="agent_0",
            action_type="attack",
            action_data={},
            tick=1,
        )
        d = action.to_dict()
        assert d["agent_id"] == "agent_0"
        assert d["action_type"] == "attack"
        assert d["tick"] == 1
        assert d["seed"] is None

    def test_action_from_dict(self):
        """Test creating action from dict."""
        data = {
            "agent_id": "agent_1",
            "action_type": "jump",
            "action_data": {"height": 5},
            "tick": 2,
            "seed": 100,
        }
        action = Action.from_dict(data)
        assert action.agent_id == "agent_1"
        assert action.tick == 2


class TestStateSnapshot:
    """Tests for StateSnapshot dataclass."""

    def test_snapshot_creation(self):
        """Test creating a state snapshot."""
        snapshot = StateSnapshot(
            tick=0,
            state_hash="abc123",
            positions={"agent_0": (100.0, 200.0)},
            velocities={"agent_0": (10.0, 0.0)},
            healths={"agent_0": 100.0},
            shields={"agent_0": 50.0},
            energies={"agent_0": 80.0},
            is_alive={"agent_0": True},
        )
        assert snapshot.tick == 0
        assert snapshot.state_hash == "abc123"
        assert snapshot.positions["agent_0"] == (100.0, 200.0)

    def test_snapshot_to_dict(self):
        """Test converting snapshot to dict."""
        snapshot = StateSnapshot(
            tick=0,
            state_hash="hash123",
            positions={},
            velocities={},
            healths={},
            shields={},
            energies={},
            is_alive={},
        )
        d = snapshot.to_dict()
        assert d["tick"] == 0
        assert d["state_hash"] == "hash123"

    def test_snapshot_from_dict(self):
        """Test creating snapshot from dict."""
        data = {
            "tick": 5,
            "state_hash": "xyz789",
            "positions": {"a": (1, 2)},
            "velocities": {},
            "healths": {},
            "shields": {},
            "energies": {},
            "is_alive": {},
        }
        snapshot = StateSnapshot.from_dict(data)
        assert snapshot.tick == 5
        assert snapshot.state_hash == "xyz789"


class TestEvent:
    """Tests for Event dataclass."""

    def test_event_creation(self):
        """Test creating an event."""
        event = Event(
            tick=10,
            event_type="damage",
            data={"target": "agent_0", "amount": 25.0},
        )
        assert event.tick == 10
        assert event.event_type == "damage"

    def test_event_to_dict(self):
        """Test converting event to dict."""
        event = Event(tick=1, event_type="kill", data={})
        d = event.to_dict()
        assert d["tick"] == 1
        assert d["event_type"] == "kill"

    def test_event_from_dict(self):
        """Test creating event from dict."""
        data = {"tick": 3, "event_type": "spawn", "data": {"id": "x"}}
        event = Event.from_dict(data)
        assert event.tick == 3
        assert event.event_type == "spawn"


class TestReplayStep:
    """Tests for ReplayStep dataclass."""

    def test_replay_step_creation(self):
        """Test creating a replay step."""
        step = ReplayStep(
            tick=0,
            observation=[1.0, 2.0, 3.0],
            actions=[],
            rewards={"agent_0": 1.5},
            events=[],
        )
        assert step.tick == 0
        assert len(step.observation) == 3
        assert step.rewards["agent_0"] == 1.5

    def test_replay_step_with_projectiles(self):
        """Test replay step with projectiles."""
        step = ReplayStep(
            tick=1,
            observation=[0.0],
            actions=[],
            rewards={},
            events=[],
            projectiles=[{"id": "bullet_1", "pos": (100, 200)}],
        )
        assert len(step.projectiles) == 1
        assert step.projectiles[0]["id"] == "bullet_1"

    def test_replay_step_with_damages(self):
        """Test replay step with damage events."""
        step = ReplayStep(
            tick=2,
            observation=[],
            actions=[],
            rewards={},
            events=[],
            damages=[{"attacker": "a", "target": "b", "damage": 50}],
        )
        assert len(step.damages) == 1
        assert step.damages[0]["damage"] == 50

    def test_replay_step_to_dict(self):
        """Test converting replay step to dict."""
        step = ReplayStep(
            tick=0,
            observation=[1.0],
            actions=[],
            rewards={},
            events=[],
        )
        d = step.to_dict()
        assert d["tick"] == 0
        assert d["observation"] == [1.0]

    def test_replay_step_from_dict(self):
        """Test creating replay step from dict."""
        data = {
            "tick": 5,
            "observation": [1, 2, 3],
            "actions": [],
            "rewards": {"a": 1.0},
            "events": [],
            "projectiles": [],
            "damages": [],
            "cooldowns": {},
        }
        step = ReplayStep.from_dict(data)
        assert step.tick == 5
        assert step.rewards["a"] == 1.0


class TestDeterministicReplay:
    """Tests for DeterministicReplay class."""

    def test_replay_creation(self):
        """Test creating a deterministic replay."""
        replay = DeterministicReplay(
            metadata={"env_id": "Test-v1"},
            initial_seed=42,
        )
        assert replay.initial_seed == 42
        assert len(replay.steps) == 0

    def test_add_step(self):
        """Test adding steps to replay."""
        replay = DeterministicReplay(
            metadata={},
            initial_seed=0,
        )
        step = ReplayStep(
            tick=0,
            observation=[],
            actions=[],
            rewards={},
            events=[],
        )
        replay.add_step(step)
        assert len(replay.steps) == 1

    def test_add_snapshot(self):
        """Test adding state snapshots."""
        replay = DeterministicReplay(
            metadata={},
            initial_seed=0,
        )
        snapshot = StateSnapshot(
            tick=0,
            state_hash="h",
            positions={},
            velocities={},
            healths={},
            shields={},
            energies={},
            is_alive={},
        )
        replay.add_snapshot(snapshot)
        assert len(replay.state_snapshots) == 1

    def test_verify_determinism_empty(self):
        """Test determinism verification with empty replay."""
        replay = DeterministicReplay(metadata={}, initial_seed=0)
        assert replay.verify_determinism() is True

    def test_verify_determinism_with_snapshots(self):
        """Test determinism verification with snapshots."""
        replay = DeterministicReplay(metadata={}, initial_seed=0)
        # Add valid snapshots
        for i in range(3):
            snapshot = StateSnapshot(
                tick=i,
                state_hash=replay._compute_state_hash(
                    StateSnapshot(
                        tick=i,
                        state_hash="",
                        positions={},
                        velocities={},
                        healths={},
                        shields={},
                        energies={},
                        is_alive={},
                    )
                ),
                positions={},
                velocities={},
                healths={},
                shields={},
                energies={},
                is_alive={},
            )
            replay.add_snapshot(snapshot)
        assert replay.verify_determinism() is True

    def test_compute_state_hash(self):
        """Test state hash computation."""
        replay = DeterministicReplay(metadata={}, initial_seed=0)
        snapshot = StateSnapshot(
            tick=0,
            state_hash="",
            positions={"a": (1, 2)},
            velocities={"a": (0, 0)},
            healths={"a": 100},
            shields={"a": 50},
            energies={"a": 100},
            is_alive={"a": True},
        )
        hash1 = replay._compute_state_hash(snapshot)
        assert isinstance(hash1, str)
        assert len(hash1) == 16

        # Same data should produce same hash
        hash2 = replay._compute_state_hash(snapshot)
        assert hash1 == hash2

    def test_save_and_load(self, tmp_path):
        """Test saving and loading replay."""
        replay = DeterministicReplay(
            metadata={"env_id": "Test-v1", "version": "1.0"},
            initial_seed=42,
        )
        # Add a step
        step = ReplayStep(
            tick=0,
            observation=[1.0, 2.0],
            actions=[Action(agent_id="a", action_type="x", action_data={})],
            rewards={"a": 1.0},
            events=[Event(tick=0, event_type="spawn", data={})],
        )
        replay.add_step(step)

        # Save
        path = tmp_path / "test.zbgr"
        replay.save(path)
        assert path.exists()

        # Load
        loaded = DeterministicReplay.load(path)
        assert loaded.initial_seed == 42
        assert len(loaded.steps) == 1
        assert loaded.metadata["env_id"] == "Test-v1"

    def test_to_dict(self):
        """Test converting to dict."""
        replay = DeterministicReplay(
            metadata={"id": "test"},
            initial_seed=123,
        )
        d = replay.to_dict()
        assert d["initial_seed"] == 123
        assert d["metadata"]["id"] == "test"


class TestDR:
    """Tests for DeterministicRecorder."""

    def test_recorder_is_separate_class(self):
        """Test that DeterministicRecorder is separate from ReplayRecorder."""
        assert DeterministicRecorder is not ReplayRecorder
        assert DeterministicRecorder.__name__ == "ReplayRecorder"

    def test_recorder_initialization(self):
        """Test recorder initialization."""
        recorder = DeterministicRecorder(initial_seed=42, metadata={"test": True})
        assert recorder.initial_seed == 42
        assert recorder.metadata["test"] is True

    def test_record_step_numpy(self):
        """Test recording with numpy observation."""
        import numpy as np

        recorder = DeterministicRecorder(initial_seed=0)
        recorder.record_step(
            observation=np.array([1.0, 2.0, 3.0]),
            actions=[],
            rewards={"a": 1.0},
            events=[],
        )
        assert len(recorder.steps) == 1
        assert recorder.steps[0].observation == [1.0, 2.0, 3.0]

    def test_finalize(self):
        """Test finalizing recording."""
        recorder = DeterministicRecorder(initial_seed=0, metadata={"env": "test"})
        recorder.record_step(
            observation=[1.0],
            actions=[],
            rewards={},
            events=[],
        )
        replay = recorder.finalize()
        assert isinstance(replay, DeterministicReplay)
        assert replay.initial_seed == 0

    def test_save(self, tmp_path):
        """Test saving replay."""
        recorder = DeterministicRecorder(initial_seed=0)
        recorder.record_step(
            observation=[],
            actions=[],
            rewards={},
            events=[],
        )
        recorder.save(tmp_path / "test.zbgr")


class TestDP:
    """Tests for DeterministicPlayer."""

    def test_player_is_deterministic_replay_player(self):
        """Test that DeterministicPlayer is a proper player class."""
        assert DeterministicPlayer.__name__ == "ReplayPlayer"

    def test_player_initialization(self):
        """Test player initialization."""
        replay = DeterministicReplay(metadata={}, initial_seed=0)
        player = DeterministicPlayer(replay)
        assert player.initial_seed == 0
        assert player.current_step == 0

    def test_iteration(self):
        """Test iterating through replay."""
        replay = DeterministicReplay(metadata={}, initial_seed=0)
        for i in range(3):
            replay.add_step(
                ReplayStep(
                    tick=i,
                    observation=[i],
                    actions=[],
                    rewards={},
                    events=[],
                )
            )

        player = DeterministicPlayer(replay)
        steps = list(player)
        assert len(steps) == 3
        assert steps[0].tick == 0
        assert steps[1].tick == 1
        assert steps[2].tick == 2

    def test_get_step(self):
        """Test getting specific step."""
        replay = DeterministicReplay(metadata={}, initial_seed=0)
        replay.add_step(ReplayStep(tick=0, observation=[], actions=[], rewards={}, events=[]))

        player = DeterministicPlayer(replay)
        step = player.get_step(0)
        assert step is not None
        assert step.tick == 0

        step = player.get_step(99)
        assert step is None

    def test_get_snapshot(self):
        """Test getting snapshot by tick."""
        replay = DeterministicReplay(metadata={}, initial_seed=0)
        snapshot = StateSnapshot(
            tick=5,
            state_hash="h",
            positions={},
            velocities={},
            healths={},
            shields={},
            energies={},
            is_alive={},
        )
        replay.add_snapshot(snapshot)

        player = DeterministicPlayer(replay)
        found = player.get_snapshot(5)
        assert found is not None
        assert found.tick == 5

        not_found = player.get_snapshot(99)
        assert not_found is None

    def test_get_events_of_type(self):
        """Test filtering events by type."""
        replay = DeterministicReplay(metadata={}, initial_seed=0)
        replay.add_step(
            ReplayStep(
                tick=0,
                observation=[],
                actions=[],
                rewards={},
                events=[
                    Event(tick=0, event_type="damage", data={}),
                    Event(tick=0, event_type="heal", data={}),
                ],
            )
        )
        replay.add_step(
            ReplayStep(
                tick=1,
                observation=[],
                actions=[],
                rewards={},
                events=[
                    Event(tick=1, event_type="damage", data={}),
                ],
            )
        )

        player = DeterministicPlayer(replay)
        damage_events = player.get_events_of_type("damage")
        assert len(damage_events) == 2

        heal_events = player.get_events_of_type("heal")
        assert len(heal_events) == 1

    def test_replay_info(self):
        """Test replay info summary."""
        replay = DeterministicReplay(metadata={}, initial_seed=0)
        replay.add_step(
            ReplayStep(
                tick=0,
                observation=[],
                actions=[Action(agent_id="a", action_type="x", action_data={})],
                rewards={},
                events=[
                    Event(tick=0, event_type="character_death", data={}),
                ],
                damages=[{"damage": 50}],
            )
        )

        player = DeterministicPlayer(replay)
        info = player.replay_info()
        assert info["duration_ticks"] == 1
        assert info["total_events"] == 1
        assert info["total_damage"] == 50
        assert info["total_kills"] == 1
        assert info["unique_agents"] == 1
