"""
Tests for AI Scheduler

Verifies:
- Agent attachment/detachment
- Decision frequency
- Priority ordering
- Deterministic execution
- Pause/resume
"""

import pytest
from unittest.mock import MagicMock

from zbgym.ai.scheduler import AIScheduler, AgentUpdateContext
from zbgym.ai.agents import IdleAgent, RandomAgent
from zbgym.ai.core.types import ActionRequest, ActionType
from zbgym.interfaces import GameState, Player, Vector2D


def create_mock_game_state(agents: list[str] = None):
    """Create a mock game state."""
    mock_state = MagicMock(spec=GameState)
    mock_state.tick = 0
    mock_state.elapsed_time = 0.0
    
    # Create mock players
    players = {}
    for agent_id in (agents or []):
        mock_player = MagicMock(spec=Player)
        mock_player.id = agent_id
        mock_player.is_alive = True
        mock_player.position = MagicMock(spec=Vector2D)
        mock_player.position.x = 100.0
        mock_player.position.y = 100.0
        players[agent_id] = mock_player
    
    mock_state.get_player = lambda aid: players.get(aid)
    mock_state.players = list(players.values())
    
    return mock_state


class TestAIScheduler:
    """Test AIScheduler."""

    def test_scheduler_creation(self):
        """Test scheduler creation."""
        scheduler = AIScheduler(tick_rate=60, seed=42)
        
        assert scheduler.tick_rate == 60
        assert scheduler.num_agents == 0
        assert not scheduler.is_running

    def test_attach_agent(self):
        """Test attaching an agent."""
        scheduler = AIScheduler()
        agent = IdleAgent(agent_id="test_1")
        
        scheduler.attach_agent("test_1", agent)
        
        assert scheduler.num_agents == 1
        assert scheduler.get_agent("test_1") is agent

    def test_detach_agent(self):
        """Test detaching an agent."""
        scheduler = AIScheduler()
        agent = IdleAgent(agent_id="test_1")
        
        scheduler.attach_agent("test_1", agent)
        assert scheduler.num_agents == 1
        
        result = scheduler.detach_agent("test_1")
        assert result is True
        assert scheduler.num_agents == 0

    def test_detach_nonexistent(self):
        """Test detaching non-existent agent."""
        scheduler = AIScheduler()
        result = scheduler.detach_agent("nonexistent")
        assert result is False

    def test_replace_agent(self):
        """Test replacing an agent."""
        scheduler = AIScheduler()
        agent1 = IdleAgent(agent_id="test_1")
        agent2 = IdleAgent(agent_id="test_1")
        
        scheduler.attach_agent("test_1", agent1)
        result = scheduler.replace_agent("test_1", agent2)
        
        assert result is True
        assert scheduler.get_agent("test_1") is agent2

    def test_pause_resume_agent(self):
        """Test pausing and resuming an agent."""
        scheduler = AIScheduler()
        agent = IdleAgent(agent_id="test_1")
        
        scheduler.attach_agent("test_1", agent)
        
        scheduler.pause_agent("test_1")
        info = scheduler.get_agent_info("test_1")
        assert info["is_paused"] is True
        
        scheduler.resume_agent("test_1")
        info = scheduler.get_agent_info("test_1")
        assert info["is_paused"] is False

    def test_priority_ordering(self):
        """Test agents are ordered by priority."""
        scheduler = AIScheduler()
        
        agent1 = IdleAgent(agent_id="low")
        agent2 = IdleAgent(agent_id="high")
        agent3 = IdleAgent(agent_id="medium")
        
        scheduler.attach_agent("low", agent1, priority=1)
        scheduler.attach_agent("high", agent2, priority=10)
        scheduler.attach_agent("medium", agent3, priority=5)
        
        agents = scheduler.list_agents()
        # Should be: high, medium, low (sorted by priority descending)
        assert agents == ["high", "medium", "low"]

    def test_decision_frequency(self):
        """Test decision frequency control."""
        scheduler = AIScheduler(tick_rate=60)
        agent = IdleAgent(agent_id="freq_test")
        
        # Attach with decision frequency of 5
        scheduler.attach_agent("freq_test", agent, decision_frequency=5)
        
        game_state = create_mock_game_state(["freq_test"])
        
        # All ticks should produce decision since agent always decides
        # The decision_frequency just controls timing
        for i in range(5):
            scheduler.tick(game_state)
        
        info = scheduler.get_agent_info("freq_test")
        # With freq=5, should have 1 decision in 5 ticks
        assert info["decisions_made"] == 1

    def test_human_agent_skipped(self):
        """Test human-controlled agents are skipped."""
        scheduler = AIScheduler()
        agent = IdleAgent(agent_id="human_test")
        
        scheduler.attach_agent("human_test", agent, is_human=True)
        
        game_state = create_mock_game_state(["human_test"])
        decisions = scheduler.tick(game_state)
        
        # Human should not produce decisions
        assert "human_test" not in decisions

    def test_tick_increment(self):
        """Test tick is incremented correctly."""
        scheduler = AIScheduler()
        
        assert scheduler.current_tick == 0
        
        game_state = create_mock_game_state()
        for _ in range(10):
            scheduler.tick(game_state)
        
        assert scheduler.current_tick == 10

    def test_start_stop(self):
        """Test start/stop."""
        scheduler = AIScheduler()
        
        scheduler.start()
        assert scheduler.is_running
        assert not scheduler.is_paused
        
        scheduler.stop()
        assert not scheduler.is_running

    def test_pause_resume_all(self):
        """Test pausing/resuming all agents."""
        scheduler = AIScheduler()
        scheduler.attach_agent("a1", IdleAgent(agent_id="a1"))
        scheduler.attach_agent("a2", IdleAgent(agent_id="a2"))
        
        scheduler.pause()
        assert scheduler.is_paused
        
        scheduler.resume()
        assert not scheduler.is_paused

    def test_reset(self):
        """Test reset."""
        scheduler = AIScheduler(seed=42)
        scheduler.attach_agent("test", IdleAgent(agent_id="test"))
        
        # Run some ticks
        game_state = create_mock_game_state(["test"])
        for _ in range(10):
            scheduler.tick(game_state)
        
        # Reset
        scheduler.reset()
        
        assert scheduler.current_tick == 0
        assert scheduler.get_agent_info("test")["decisions_made"] == 0

    def test_shutdown(self):
        """Test shutdown."""
        scheduler = AIScheduler()
        scheduler.attach_agent("test", IdleAgent(agent_id="test"))
        
        scheduler.shutdown()
        
        assert scheduler.num_agents == 0

    def test_get_stats(self):
        """Test statistics."""
        scheduler = AIScheduler(tick_rate=60)
        scheduler.attach_agent("test", IdleAgent(agent_id="test"))
        
        stats = scheduler.get_stats()
        
        assert "tick_rate" in stats
        assert "current_tick" in stats
        assert "num_agents" in stats
        assert stats["num_agents"] == 1


class TestSchedulerDeterminism:
    """Test scheduler determinism."""

    def test_same_seed_same_order(self):
        """Test same seed produces same agent order."""
        scheduler1 = AIScheduler(seed=123)
        scheduler2 = AIScheduler(seed=123)
        
        for i in range(5):
            agent = IdleAgent(agent_id=f"agent_{i}")
            scheduler1.attach_agent(f"agent_{i}", agent)
        
        for i in range(5):
            agent = IdleAgent(agent_id=f"agent_{i}")
            scheduler2.attach_agent(f"agent_{i}", agent)
        
        # Same order despite different object instances
        assert scheduler1.list_agents() == scheduler2.list_agents()
