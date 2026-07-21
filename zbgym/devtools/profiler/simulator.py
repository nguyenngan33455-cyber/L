"""Profiling tools for ZBGym."""

from __future__ import annotations

import cProfile
import pstats
import time
from dataclasses import dataclass, field
from io import StringIO
from typing import Any, Callable

from zbgym.engine.tick_system import TickSystem
from zbgym.engine.event_bus import EventBus
from zbgym.constants import EventType


@dataclass
class ProfileResult:
    """Result of a profiling session."""

    name: str
    total_calls: int
    total_time: float
    function_times: list[dict[str, Any]] = field(default_factory=list)
    duration: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "total_calls": self.total_calls,
            "total_time": self.total_time,
            "duration": self.duration,
            "functions": self.function_times[:20],  # Top 20
        }


class Profiler:
    """
    Simulation profiler.

    Profiles various subsystems.
    """

    def __init__(self) -> None:
        """Initialize the profiler."""
        self._results: dict[str, ProfileResult] = {}

    def profile_tick_system(
        self,
        ticks: int = 100,
        tick_rate: int = 60,
    ) -> ProfileResult:
        """
        Profile the tick system.

        Args:
            ticks: Number of ticks to profile
            tick_rate: Tick rate

        Returns:
            ProfileResult
        """
        ts = TickSystem(tick_rate=tick_rate)
        ts.start()

        profiler = cProfile.Profile()
        profiler.enable()

        start = time.perf_counter()
        for _ in range(ticks):
            ts.tick()
        duration = time.perf_counter() - start

        profiler.disable()

        # Parse stats
        stats = pstats.Stats(profiler)
        s = StringIO()
        stats.stream = s
        stats.sort_stats("cumulative")
        stats.print_stats(20)

        function_times = []
        for stat in stats.stats:
            filename, lineno, func_name = stat[:3]
            cc, nc, tt, ct, callers = stats.stats[stat]
            function_times.append(
                {
                    "function": func_name,
                    "file": filename,
                    "line": lineno,
                    "calls": nc,
                    "total_time": tt,
                    "cumulative_time": ct,
                }
            )

        result = ProfileResult(
            name="tick_system",
            total_calls=stats.total_calls,
            total_time=duration,
            function_times=function_times,
            duration=duration,
        )

        ts.stop()
        self._results["tick_system"] = result
        return result

    def profile_event_bus(
        self,
        events: int = 1000,
    ) -> ProfileResult:
        """
        Profile the event bus.

        Args:
            events: Number of events to emit

        Returns:
            ProfileResult
        """
        bus = EventBus()

        # Subscribe handlers
        def handler(event):
            pass

        for _ in range(10):
            bus.subscribe(EventType.MATCH_START, handler)

        start = time.perf_counter()
        for i in range(events):
            bus.emit(EventType.MATCH_START, data={"tick": i})
        duration = time.perf_counter() - start

        result = ProfileResult(
            name="event_bus",
            total_calls=events * 10,  # 10 handlers
            total_time=duration,
            duration=duration,
        )

        self._results["event_bus"] = result
        return result

    def profile_function(
        self,
        func: Callable[[], Any],
        name: str = "custom",
    ) -> ProfileResult:
        """
        Profile a custom function.

        Args:
            func: Function to profile
            name: Profile name

        Returns:
            ProfileResult
        """
        profiler = cProfile.Profile()
        profiler.enable()

        start = time.perf_counter()
        func()
        duration = time.perf_counter() - start

        profiler.disable()

        stats = pstats.Stats(profiler)
        function_times = []
        for stat in stats.stats:
            filename, lineno, func_name = stat[:3]
            cc, nc, tt, ct, callers = stats.stats[stat]
            function_times.append(
                {
                    "function": func_name,
                    "file": filename,
                    "line": lineno,
                    "calls": nc,
                    "total_time": tt,
                    "cumulative_time": ct,
                }
            )

        result = ProfileResult(
            name=name,
            total_calls=stats.total_calls,
            total_time=duration,
            function_times=function_times,
            duration=duration,
        )

        self._results[name] = result
        return result

    def print_result(self, result: ProfileResult) -> None:
        """Print a profile result."""
        print(f"\n{'=' * 60}")
        print(f"Profile: {result.name}")
        print(f"{'=' * 60}")
        print(f"Duration: {result.duration:.4f}s")
        print(f"Total Calls: {result.total_calls}")
        print(f"Time per Call: {result.total_time / max(result.total_calls, 1) * 1000:.4f}ms")
        print()

        if result.function_times:
            print(f"{'Function':<40} {'Calls':>10} {'Time (ms)':>12}")
            print("-" * 60)
            for func in result.function_times[:10]:
                print(
                    f"{func['function']:<40} "
                    f"{func['calls']:>10} "
                    f"{func['total_time'] * 1000:>12.4f}"
                )

    def get_results(self) -> dict[str, ProfileResult]:
        """Get all profile results."""
        return self._results.copy()


class TickProfiler:
    """Profile individual ticks."""

    def __init__(self) -> None:
        """Initialize the profiler."""
        self._tick_times: list[float] = []
        self._phase_times: dict[str, list[float]] = {}

    def start_tick(self) -> None:
        """Start profiling a tick."""
        self._tick_start = time.perf_counter()

    def start_phase(self, name: str) -> None:
        """Start a profiling phase."""
        self._phase_start = time.perf_counter()
        self._current_phase = name

    def end_phase(self) -> float:
        """End the current phase."""
        if not hasattr(self, "_phase_start"):
            return 0.0

        duration = time.perf_counter() - self._phase_start

        if self._current_phase not in self._phase_times:
            self._phase_times[self._current_phase] = []

        self._phase_times[self._current_phase].append(duration)
        return duration

    def end_tick(self) -> float:
        """End profiling a tick."""
        duration = time.perf_counter() - self._tick_start
        self._tick_times.append(duration)
        return duration

    def get_statistics(self) -> dict[str, Any]:
        """Get profiling statistics."""
        import numpy as np

        if not self._tick_times:
            return {}

        tick_times = np.array(self._tick_times)

        stats = {
            "tick_count": len(self._tick_times),
            "avg_tick_time_ms": np.mean(tick_times) * 1000,
            "min_tick_time_ms": np.min(tick_times) * 1000,
            "max_tick_time_ms": np.max(tick_times) * 1000,
            "std_tick_time_ms": np.std(tick_times) * 1000,
        }

        # Phase statistics
        phase_stats = {}
        for phase, times in self._phase_times.items():
            times_arr = np.array(times)
            phase_stats[phase] = {
                "count": len(times),
                "avg_ms": np.mean(times_arr) * 1000,
                "total_ms": np.sum(times_arr) * 1000,
            }
        stats["phases"] = phase_stats

        return stats

    def print_statistics(self) -> None:
        """Print profiling statistics."""
        stats = self.get_statistics()

        print("\n" + "=" * 60)
        print("Tick Profiler Statistics")
        print("=" * 60)

        if not stats:
            print("No profiling data available.")
            return

        print(f"\nTick Count: {stats['tick_count']}")
        print(f"Average Tick Time: {stats['avg_tick_time_ms']:.4f}ms")
        print(f"Min Tick Time: {stats['min_tick_time_ms']:.4f}ms")
        print(f"Max Tick Time: {stats['max_tick_time_ms']:.4f}ms")
        print(f"Std Dev: {stats['std_tick_time_ms']:.4f}ms")

        if "phases" in stats:
            print("\nPhase Breakdown:")
            print("-" * 40)
            for phase, phase_stats in stats["phases"].items():
                print(
                    f"  {phase:<20} {phase_stats['avg_ms']:>8.4f}ms "
                    f"({phase_stats['count']} calls)"
                )

        print("=" * 60)

    def reset(self) -> None:
        """Reset profiling data."""
        self._tick_times.clear()
        self._phase_times.clear()
