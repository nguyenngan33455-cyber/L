"""
TickCoordinator implementation for ZBGym Kernel.

Orchestrates deterministic tick pipeline execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
import time


class TickStage(Enum):
    """Tick pipeline stages."""
    PREPARE = "prepare"
    SCHEDULER = "scheduler"
    AI = "ai"
    ACTION_QUEUE = "action_queue"
    PHYSICS = "physics"
    COLLISION = "collision"
    GAME_LOGIC = "game_logic"
    REWARD = "reward"
    OBSERVATION = "observation"
    REPLAY = "replay"
    DASHBOARD = "dashboard"
    METRICS = "metrics"
    EVENTS = "events"
    FINISH = "finish"


@dataclass
class StageResult:
    """Result of a stage execution."""
    stage: TickStage
    duration_ms: float
    success: bool
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class TickResult:
    """Result of a tick execution."""
    tick: int
    duration_ms: float
    stage_results: list[StageResult]
    success: bool
    error: str | None = None


class TickCoordinator:
    """
    Coordinates tick pipeline execution.
    
    Executes stages in deterministic order.
    Records stage timing and results.
    """

    # Fixed stage order - NEVER CHANGE
    STAGE_ORDER: list[TickStage] = [
        TickStage.PREPARE,
        TickStage.SCHEDULER,
        TickStage.AI,
        TickStage.ACTION_QUEUE,
        TickStage.PHYSICS,
        TickStage.COLLISION,
        TickStage.GAME_LOGIC,
        TickStage.REWARD,
        TickStage.OBSERVATION,
        TickStage.REPLAY,
        TickStage.DASHBOARD,
        TickStage.METRICS,
        TickStage.EVENTS,
        TickStage.FINISH,
    ]

    def __init__(self) -> None:
        """Initialize the tick coordinator."""
        self._handlers: dict[TickStage, Callable[[], Any]] = {}
        self._before_handlers: dict[TickStage, Callable[[], None]] = {}
        self._after_handlers: dict[TickStage, Callable[[], None]] = {}
        self._current_tick: int = 0
        self._running: bool = False
        self._tick_results: list[TickResult] = []

    def register_stage(
        self,
        stage: TickStage,
        handler: Callable[[], Any],
        before_hook: Callable[[], None] | None = None,
        after_hook: Callable[[], None] | None = None
    ) -> None:
        """
        Register a stage handler.
        
        Args:
            stage: Stage to register
            handler: Stage execution function
            before_hook: Optional before-hook
            after_hook: Optional after-hook
        """
        self._handlers[stage] = handler
        if before_hook:
            self._before_handlers[stage] = before_hook
        if after_hook:
            self._after_handlers[stage] = after_hook

    def unregister_stage(self, stage: TickStage) -> bool:
        """
        Unregister a stage.
        
        Args:
            stage: Stage to unregister
            
        Returns:
            True if unregistered
        """
        if stage in self._handlers:
            del self._handlers[stage]
            self._before_handlers.pop(stage, None)
            self._after_handlers.pop(stage, None)
            return True
        return False

    def tick(self) -> TickResult:
        """
        Execute one tick.
        
        Returns:
            Tick result with stage results
        """
        if not self._running:
            raise RuntimeError("TickCoordinator not running")

        self._current_tick += 1
        start_time = time.perf_counter()
        stage_results: list[StageResult] = []
        overall_success = True
        error_msg: str | None = None

        # Execute stages in order
        for stage in self.STAGE_ORDER:
            stage_result = self._execute_stage(stage)
            stage_results.append(stage_result)

            if not stage_result.success:
                overall_success = False
                if error_msg is None:
                    error_msg = stage_result.error

        duration_ms = (time.perf_counter() - start_time) * 1000

        result = TickResult(
            tick=self._current_tick,
            duration_ms=duration_ms,
            stage_results=stage_results,
            success=overall_success,
            error=error_msg
        )

        self._tick_results.append(result)
        return result

    def _execute_stage(self, stage: TickStage) -> StageResult:
        """
        Execute a single stage.
        
        Args:
            stage: Stage to execute
            
        Returns:
            Stage result
        """
        start_time = time.perf_counter()

        try:
            # Before hook
            if stage in self._before_handlers:
                self._before_handlers[stage]()

            # Main handler
            if stage in self._handlers:
                self._handlers[stage]()

            # After hook
            if stage in self._after_handlers:
                self._after_handlers[stage]()

            duration_ms = (time.perf_counter() - start_time) * 1000

            return StageResult(
                stage=stage,
                duration_ms=duration_ms,
                success=True
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            return StageResult(
                stage=stage,
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )

    def start(self) -> None:
        """Start the tick coordinator."""
        self._running = True

    def stop(self) -> None:
        """Stop the tick coordinator."""
        self._running = False

    @property
    def current_tick(self) -> int:
        """Current tick number."""
        return self._current_tick

    @property
    def is_running(self) -> bool:
        """Check if running."""
        return self._running

    def reset(self) -> None:
        """Reset the tick coordinator."""
        self._current_tick = 0
        self._tick_results.clear()
        self._running = False

    def get_stage_duration(self, stage: TickStage) -> float:
        """
        Get average stage duration.
        
        Args:
            stage: Stage to measure
            
        Returns:
            Average duration in ms
        """
        durations = [
            sr.duration_ms
            for tr in self._tick_results
            for sr in tr.stage_results
            if sr.stage == stage
        ]

        if not durations:
            return 0.0

        return sum(durations) / len(durations)

    def get_last_result(self) -> TickResult | None:
        """Get last tick result."""
        if self._tick_results:
            return self._tick_results[-1]
        return None

    def get_results(self, count: int = 100) -> list[TickResult]:
        """
        Get recent tick results.
        
        Args:
            count: Number of results to return
            
        Returns:
            List of tick results
        """
        return self._tick_results[-count:]

    def get_stage_handlers(self) -> list[TickStage]:
        """Get list of registered stages."""
        return list(self._handlers.keys())
