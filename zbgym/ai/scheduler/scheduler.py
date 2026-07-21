"""
AI Scheduler

Manages AI agent execution within the game loop.
Provides deterministic scheduling, priority execution, and tick synchronization.

Example:
    >>> scheduler = AIScheduler(tick_rate=60)
    >>> scheduler.attach_agent("player_1", agent)
    >>> scheduler.attach_agent("player_2", agent2)
    >>> 
    >>> # In game loop
    >>> scheduler.tick(game_state, elapsed_time)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import TYPE_CHECKING

from zbgym.ai.core.agent import AIAgent
from zbgym.ai.core.types import ActionRequest, ActionResult, DecisionContext, PerceptionResult
from zbgym.ai.blackboard.blackboard import Blackboard
from zbgym.ai.memory.memory import Memory

if TYPE_CHECKING:
    from zbgym.interfaces import GameState


@dataclass
class AgentUpdateContext:
    """
    Context passed to agent during update.
    
    Attributes:
        agent_id: Agent identifier
        decision_frequency: How often agent should decide
        reaction_time: Minimum reaction delay
    """
    
    agent_id: str
    tick: int
    elapsed_time: float
    decision_frequency: int = 1
    reaction_time: float = 0.0


@dataclass
class ScheduledAgent:
    """
    Represents an agent scheduled for execution.
    
    Attributes:
        agent: The AI agent
        agent_id: Agent identifier
        priority: Execution priority (higher first)
        decision_frequency: Ticks between decisions
        reaction_time: Minimum reaction delay
        last_decision_tick: Last tick when decision was made
        is_paused: Whether agent is paused
        is_human: Whether controlled by human
    """
    
    agent: AIAgent
    agent_id: str
    priority: int = 0
    decision_frequency: int = 1
    reaction_time: float = 0.0
    last_decision_tick: int = -1
    is_paused: bool = False
    is_human: bool = False


class AIScheduler:
    """
    Schedules and executes AI agents within the game loop.
    
    Features:
    - Deterministic agent ordering
    - Configurable decision frequency per agent
    - Reaction delay simulation
    - Priority-based execution
    - Human/AI mixed control
    - Pause/resume support
    
    Thread Safety:
        Uses RLock for thread-safe operations.
    """
    
    def __init__(
        self,
        tick_rate: int = 60,
        seed: int | None = None,
        shared_blackboard: bool = True,
    ) -> None:
        """
        Initialize AI scheduler.
        
        Args:
            tick_rate: Target ticks per second
            seed: Random seed for determinism
            shared_blackboard: Use shared blackboard for all agents
        """
        self._tick_rate = tick_rate
        self._seed = seed
        self._lock = RLock()
        
        # Agent management
        self._agents: dict[str, ScheduledAgent] = {}
        self._agent_order: list[str] = []  # Deterministic order
        
        # Blackboard
        self._shared_blackboard = shared_blackboard
        self._blackboard = Blackboard(seed=seed) if shared_blackboard else None
        
        # State
        self._current_tick: int = 0
        self._elapsed_time: float = 0.0
        self._running: bool = False
        self._paused: bool = False
        
        # Stats
        self._decisions_made: int = 0
        self._decisions_by_agent: dict[str, int] = {}
        self._total_decision_time: float = 0.0
    
    @property
    def tick_rate(self) -> int:
        """Target tick rate."""
        return self._tick_rate
    
    @property
    def current_tick(self) -> int:
        """Current tick number."""
        return self._current_tick
    
    @property
    def num_agents(self) -> int:
        """Number of attached agents."""
        with self._lock:
            return len(self._agents)
    
    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running
    
    @property
    def is_paused(self) -> bool:
        """Check if scheduler is paused."""
        return self._paused
    
    @property
    def blackboard(self) -> Blackboard | None:
        """Get shared blackboard."""
        return self._blackboard
    
    def attach_agent(
        self,
        agent_id: str,
        agent: AIAgent,
        priority: int = 0,
        decision_frequency: int = 1,
        reaction_time: float = 0.0,
        is_human: bool = False,
    ) -> None:
        """
        Attach an AI agent to the scheduler.
        
        Args:
            agent_id: Unique agent identifier
            agent: AIAgent implementation
            priority: Execution priority (higher first)
            decision_frequency: Ticks between decisions
            reaction_time: Minimum reaction delay in seconds
            is_human: Whether controlled by human
        """
        with self._lock:
            if agent_id in self._agents:
                raise ValueError(f"Agent '{agent_id}' already attached")
            
            # Initialize agent
            if not agent.is_initialized:
                agent.initialize()
            
            # Set blackboard if shared
            if self._shared_blackboard and self._blackboard:
                agent.blackboard = self._blackboard
            
            # Create scheduled agent
            scheduled = ScheduledAgent(
                agent=agent,
                agent_id=agent_id,
                priority=priority,
                decision_frequency=decision_frequency,
                reaction_time=reaction_time,
                is_human=is_human,
            )
            
            self._agents[agent_id] = scheduled
            self._update_agent_order()
            self._decisions_by_agent[agent_id] = 0
    
    def detach_agent(self, agent_id: str) -> bool:
        """
        Detach an agent from the scheduler.
        
        Args:
            agent_id: Agent to detach
            
        Returns:
            True if detached
        """
        with self._lock:
            if agent_id not in self._agents:
                return False
            
            agent = self._agents[agent_id].agent
            agent.shutdown()
            
            del self._agents[agent_id]
            self._update_agent_order()
            
            if agent_id in self._decisions_by_agent:
                del self._decisions_by_agent[agent_id]
            
            return True
    
    def replace_agent(self, agent_id: str, agent: AIAgent) -> bool:
        """
        Replace an attached agent.
        
        Args:
            agent_id: Agent to replace
            agent: New AIAgent
            
        Returns:
            True if replaced
        """
        with self._lock:
            if agent_id not in self._agents:
                return False
            
            old_scheduled = self._agents[agent_id]
            
            # Initialize new agent
            if not agent.is_initialized:
                agent.initialize()
            
            # Set blackboard if shared
            if self._shared_blackboard and self._blackboard:
                agent.blackboard = self._blackboard
            
            # Create new scheduled agent with same settings
            new_scheduled = ScheduledAgent(
                agent=agent,
                agent_id=agent_id,
                priority=old_scheduled.priority,
                decision_frequency=old_scheduled.decision_frequency,
                reaction_time=old_scheduled.reaction_time,
                last_decision_tick=old_scheduled.last_decision_tick,
                is_paused=old_scheduled.is_paused,
                is_human=old_scheduled.is_human,
            )
            
            # Shutdown old agent
            old_scheduled.agent.shutdown()
            
            self._agents[agent_id] = new_scheduled
            return True
    
    def pause_agent(self, agent_id: str) -> bool:
        """Pause an agent."""
        with self._lock:
            if agent_id not in self._agents:
                return False
            self._agents[agent_id].is_paused = True
            return True
    
    def resume_agent(self, agent_id: str) -> bool:
        """Resume an agent."""
        with self._lock:
            if agent_id not in self._agents:
                return False
            self._agents[agent_id].is_paused = False
            return True
    
    def get_agent(self, agent_id: str) -> AIAgent | None:
        """Get an attached agent."""
        with self._lock:
            if agent_id not in self._agents:
                return None
            return self._agents[agent_id].agent
    
    def list_agents(self) -> list[str]:
        """List all attached agent IDs."""
        with self._lock:
            return list(self._agent_order)
    
    def get_agent_info(self, agent_id: str) -> dict | None:
        """Get information about an agent."""
        with self._lock:
            if agent_id not in self._agents:
                return None
            
            scheduled = self._agents[agent_id]
            return {
                "agent_id": scheduled.agent_id,
                "priority": scheduled.priority,
                "decision_frequency": scheduled.decision_frequency,
                "reaction_time": scheduled.reaction_time,
                "is_paused": scheduled.is_paused,
                "is_human": scheduled.is_human,
                "decisions_made": self._decisions_by_agent.get(agent_id, 0),
            }
    
    def _update_agent_order(self) -> None:
        """Update deterministic agent execution order."""
        # Sort by priority (descending), then by agent_id (ascending) for determinism
        self._agent_order = sorted(
            self._agents.keys(),
            key=lambda aid: (-self._agents[aid].priority, aid)
        )
    
    def should_decide(self, scheduled: ScheduledAgent, tick: int) -> bool:
        """
        Check if agent should make a decision this tick.
        
        Args:
            scheduled: Scheduled agent
            tick: Current tick
            
        Returns:
            True if should decide
        """
        # Skip paused agents
        if scheduled.is_paused:
            return False
        
        # Skip human-controlled agents
        if scheduled.is_human:
            return False
        
        # Check decision frequency
        if tick - scheduled.last_decision_tick < scheduled.decision_frequency:
            return False
        
        # Check reaction time
        if scheduled.reaction_time > 0:
            ticks_since_last = tick - scheduled.last_decision_tick
            min_ticks = int(scheduled.reaction_time * self._tick_rate)
            if ticks_since_last < min_ticks:
                return False
        
        return True
    
    def tick(
        self,
        game_state: GameState,
        elapsed_time: float | None = None,
    ) -> dict[str, ActionRequest]:
        """
        Execute one scheduler tick.
        
        This is the main entry point called from the game loop.
        
        Args:
            game_state: Current game state
            elapsed_time: Elapsed time in seconds
            
        Returns:
            Dict of agent_id -> ActionRequest for agents that decided
        """
        with self._lock:
            self._current_tick += 1
            if elapsed_time is not None:
                self._elapsed_time = elapsed_time
            else:
                self._elapsed_time += 1.0 / self._tick_rate
            
            decisions: dict[str, ActionRequest] = {}
            
            # Execute in deterministic order
            for agent_id in self._agent_order:
                scheduled = self._agents[agent_id]
                
                # Check if should decide
                if not self.should_decide(scheduled, self._current_tick):
                    continue
                
                # Create context
                context = AgentUpdateContext(
                    agent_id=agent_id,
                    tick=self._current_tick,
                    elapsed_time=self._elapsed_time,
                    decision_frequency=scheduled.decision_frequency,
                    reaction_time=scheduled.reaction_time,
                )
                
                # Execute agent decision
                try:
                    action = self._execute_agent(scheduled, game_state, context)
                    if action is not None:
                        decisions[agent_id] = action
                        scheduled.last_decision_tick = self._current_tick
                        self._decisions_made += 1
                        self._decisions_by_agent[agent_id] = (
                            self._decisions_by_agent.get(agent_id, 0) + 1
                        )
                except Exception:
                    # Log error but continue with other agents
                    pass
            
            return decisions
    
    def _execute_agent(
        self,
        scheduled: ScheduledAgent,
        game_state: GameState,
        context: AgentUpdateContext,
    ) -> ActionRequest | None:
        """
        Execute a single agent's decision cycle.
        
        Args:
            scheduled: Scheduled agent
            game_state: Current game state
            context: Update context
            
        Returns:
            ActionRequest or None
        """
        agent = scheduled.agent
        
        # Observe
        perception = agent.observe(game_state)
        
        # Create decision context
        agent_player = game_state.get_player(scheduled.agent_id)
        position = agent_player.position if agent_player else None
        
        decision_context = DecisionContext(
            game_state=game_state,
            perception=perception,
            agent_id=scheduled.agent_id,
            agent_position=position,
            tick=context.tick,
            elapsed_time=context.elapsed_time,
            memory=agent.memory,
            blackboard=agent.blackboard,
        )
        
        # Think
        action = agent.think(decision_context)
        
        # Update stats
        agent.update(ActionResult.success_result(action))
        
        return action
    
    def start(self) -> None:
        """Start the scheduler."""
        with self._lock:
            self._running = True
            self._paused = False
    
    def stop(self) -> None:
        """Stop the scheduler."""
        with self._lock:
            self._running = False
    
    def pause(self) -> None:
        """Pause all agents."""
        with self._lock:
            self._paused = True
            for scheduled in self._agents.values():
                scheduled.is_paused = True
    
    def resume(self) -> None:
        """Resume all agents."""
        with self._lock:
            self._paused = False
            for scheduled in self._agents.values():
                scheduled.is_paused = False
    
    def reset(self, seed: int | None = None) -> None:
        """
        Reset the scheduler.
        
        Args:
            seed: New random seed
        """
        with self._lock:
            self._current_tick = 0
            self._elapsed_time = 0.0
            self._decisions_made = 0
            self._decisions_by_agent.clear()
            
            if seed is not None:
                self._seed = seed
            
            # Reset all agents
            for scheduled in self._agents.values():
                scheduled.agent.reset(seed=self._seed)
                scheduled.last_decision_tick = -1
    
    def shutdown(self) -> None:
        """Shutdown all agents and scheduler."""
        with self._lock:
            for scheduled in self._agents.values():
                scheduled.agent.shutdown()
            self._agents.clear()
            self._agent_order.clear()
            self._running = False
    
    def get_stats(self) -> dict:
        """Get scheduler statistics."""
        with self._lock:
            return {
                "tick_rate": self._tick_rate,
                "current_tick": self._current_tick,
                "elapsed_time": self._elapsed_time,
                "num_agents": len(self._agents),
                "decisions_made": self._decisions_made,
                "decisions_by_agent": dict(self._decisions_by_agent),
                "avg_decision_time": (
                    self._total_decision_time / max(1, self._decisions_made)
                ),
                "running": self._running,
                "paused": self._paused,
                "shared_blackboard": self._shared_blackboard,
            }
