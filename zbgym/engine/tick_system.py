"""Tick system for ZBGym engine."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from zbgym.engine.event_bus import EventBus, Event
from zbgym.constants import EventType


@dataclass
class TickCallback:
    """Represents a callback registered for tick events."""

    id: str = field(default_factory=lambda: str(id(object())))
    callback: Callable[[float], None] = field(default_factory=lambda: lambda dt: None)
    priority: int = 0
    enabled: bool = True


class TickSystem:
    """
    Manages the game loop tick rate and calls registered callbacks.

    Provides deterministic timing for physics and game logic updates.
    """

    def __init__(
        self,
        tick_rate: int = 60,
        event_bus: EventBus | None = None,
        max_frame_time: float = 0.1,
    ) -> None:
        """
        Initialize tick system.

        Args:
            tick_rate: Target ticks per second
            event_bus: Event bus for emitting tick events
            max_frame_time: Maximum delta time to prevent spiral of death
        """
        self._tick_rate = tick_rate
        self._tick_interval = 1.0 / tick_rate
        self._event_bus = event_bus or EventBus()
        self._max_frame_time = max_frame_time

        self._callbacks: list[TickCallback] = []
        self._running = False
        self._paused = False

        # Timing stats
        self._current_tick = 0
        self._last_tick_time = 0.0
        self._delta_time = 0.0
        self._elapsed_time = 0.0
        self._fps = 0.0
        self._actual_fps = 0.0

    @property
    def tick_rate(self) -> int:
        """Target tick rate."""
        return self._tick_rate

    @property
    def tick_interval(self) -> float:
        """Time between ticks in seconds."""
        return self._tick_interval

    @property
    def current_tick(self) -> int:
        """Current tick number."""
        return self._current_tick

    @property
    def delta_time(self) -> float:
        """Delta time since last tick."""
        return self._delta_time

    @property
    def elapsed_time(self) -> float:
        """Total elapsed time in seconds."""
        return self._elapsed_time

    @property
    def fps(self) -> float:
        """Current frames per second."""
        return self._fps

    @property
    def actual_fps(self) -> float:
        """Actual frames per second achieved."""
        return self._actual_fps

    @property
    def is_running(self) -> bool:
        """Check if tick system is running."""
        return self._running

    @property
    def is_paused(self) -> bool:
        """Check if tick system is paused."""
        return self._paused

    def register_callback(
        self,
        callback: Callable[[float], None],
        priority: int = 0,
    ) -> str:
        """
        Register a callback to be called on each tick.

        Args:
            callback: Function accepting delta time in seconds
            priority: Higher priority callbacks are called first

        Returns:
            Callback ID for later removal
        """
        tick_callback = TickCallback(callback=callback, priority=priority)
        self._callbacks.append(tick_callback)
        self._callbacks.sort(key=lambda c: -c.priority)
        return tick_callback.id

    def unregister_callback(self, callback_id: str) -> bool:
        """
        Unregister a callback.

        Args:
            callback_id: ID returned from register_callback

        Returns:
            True if callback was found and removed
        """
        for i, cb in enumerate(self._callbacks):
            if cb.id == callback_id:
                self._callbacks.pop(i)
                return True
        return False

    def enable_callback(self, callback_id: str) -> bool:
        """Enable a callback."""
        for cb in self._callbacks:
            if cb.id == callback_id:
                cb.enabled = True
                return True
        return False

    def disable_callback(self, callback_id: str) -> bool:
        """Disable a callback."""
        for cb in self._callbacks:
            if cb.id == callback_id:
                cb.enabled = False
                return True
        return False

    def start(self) -> None:
        """Start the tick system."""
        if self._running:
            return

        self._running = True
        self._paused = False
        self._last_tick_time = time.perf_counter()

        self._event_bus.emit(EventType.MATCH_START, tick=0)

    def stop(self) -> None:
        """Stop the tick system."""
        if not self._running:
            return

        self._running = False
        self._event_bus.emit(EventType.MATCH_END, tick=self._current_tick)

    def pause(self) -> None:
        """Pause the tick system."""
        self._paused = True

    def resume(self) -> None:
        """Resume the tick system."""
        self._paused = False
        self._last_tick_time = time.perf_counter()

    def tick(self) -> float:
        """
        Advance the tick system by one tick.

        Returns:
            Delta time in seconds
        """
        if not self._running or self._paused:
            return 0.0

        current_time = time.perf_counter()
        self._delta_time = current_time - self._last_tick_time

        # Clamp delta time to prevent spiral of death
        if self._delta_time > self._max_frame_time:
            self._delta_time = self._max_frame_time

        self._last_tick_time = current_time
        self._elapsed_time += self._delta_time
        self._current_tick += 1

        # Calculate FPS
        if self._delta_time > 0:
            self._actual_fps = 1.0 / self._delta_time

        # Run callbacks
        for callback in self._callbacks:
            if callback.enabled:
                callback.callback(self._delta_time)

        # Emit tick event
        self._event_bus.emit(
            Event(
                type="tick",
                data={
                    "tick": self._current_tick,
                    "delta_time": self._delta_time,
                    "elapsed_time": self._elapsed_time,
                },
            )
        )

        return self._delta_time

    def run(self, duration: float | None = None) -> None:
        """
        Run the tick loop for a specified duration.

        Args:
            duration: Duration in seconds, None for infinite
        """
        self.start()
        start_time = time.perf_counter()

        while self._running:
            self.tick()

            if duration is not None:
                elapsed = time.perf_counter() - start_time
                if elapsed >= duration:
                    break

            # Sleep to maintain tick rate
            sleep_time = self._tick_interval - (time.perf_counter() - self._last_tick_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.stop()

    def get_stats(self) -> dict:
        """Get tick system statistics."""
        return {
            "tick_rate": self._tick_rate,
            "current_tick": self._current_tick,
            "elapsed_time": self._elapsed_time,
            "delta_time": self._delta_time,
            "fps": self._fps,
            "actual_fps": self._actual_fps,
            "num_callbacks": len(self._callbacks),
            "running": self._running,
            "paused": self._paused,
        }

    def reset(self) -> None:
        """Reset tick system state."""
        self._current_tick = 0
        self._elapsed_time = 0.0
        self._delta_time = 0.0
        self._last_tick_time = time.perf_counter()
