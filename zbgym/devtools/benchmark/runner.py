"""Performance benchmarking for ZBGym."""

from __future__ import annotations

import gc
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np


@dataclass
class BenchmarkResult:
    """Result of a benchmark."""

    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_time: float
    ops_per_second: float
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def passes(self) -> bool:
        """Check if benchmark passes performance threshold."""
        return self.avg_time < 1.0  # 1 second per operation max


@dataclass
class BenchmarkReport:
    """Complete benchmark report."""

    results: list[BenchmarkResult] = field(default_factory=list)
    timestamp: str = ""
    total_time: float = 0.0
    benchmarks_passed: int = 0
    benchmarks_failed: int = 0

    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result."""
        self.results.append(result)
        self.total_time += result.total_time
        if result.passes:
            self.benchmarks_passed += 1
        else:
            self.benchmarks_failed += 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "total_time": self.total_time,
            "benchmarks_passed": self.benchmarks_passed,
            "benchmarks_failed": self.benchmarks_failed,
            "results": [
                {
                    "name": r.name,
                    "iterations": r.iterations,
                    "total_time": r.total_time,
                    "avg_time": r.avg_time,
                    "ops_per_second": r.ops_per_second,
                }
                for r in self.results
            ],
        }


class Benchmark:
    """
    Performance benchmarking suite.

    Benchmarks various ZBGym subsystems.
    """

    def __init__(self, warmup: int = 10, iterations: int = 1000) -> None:
        """
        Initialize benchmark.

        Args:
            warmup: Number of warmup iterations
            iterations: Number of benchmark iterations
        """
        self._warmup = warmup
        self._iterations = iterations

    def run_all(self) -> BenchmarkReport:
        """Run all benchmarks."""
        from datetime import datetime

        report = BenchmarkReport(timestamp=datetime.now().isoformat())

        # Vector operations
        self._benchmark_vector_add(report)
        self._benchmark_vector_mul(report)

        # Physics
        self._benchmark_body_creation(report)
        self._benchmark_collision(report)

        # Scheduler
        self._benchmark_scheduler(report)

        # Event bus
        self._benchmark_event_bus(report)

        # Replay
        self._benchmark_replay(report)

        # Memory
        self._benchmark_memory(report)

        return report

    def _benchmark_vector_add(self, report: BenchmarkReport) -> None:
        """Benchmark vector addition."""
        from zbgym.physics.vector import Vector2D

        def operation():
            v1 = Vector2D(1.0, 2.0)
            v2 = Vector2D(3.0, 4.0)
            return v1 + v2

        self._run_benchmark("vector_add", operation, report)

    def _benchmark_vector_mul(self, report: BenchmarkReport) -> None:
        """Benchmark vector multiplication."""
        from zbgym.physics.vector import Vector2D

        def operation():
            v = Vector2D(1.0, 2.0)
            return v * 2.0

        self._run_benchmark("vector_mul", operation, report)

    def _benchmark_body_creation(self, report: BenchmarkReport) -> None:
        """Benchmark physics body creation."""
        from zbgym.physics.vector import Vector2D
        from zbgym.physics.body import PhysicsBody

        def operation():
            body = PhysicsBody(
                id="test_body",
                position=Vector2D(0, 0),
                velocity=Vector2D(1, 1),
                mass=1.0,
            )
            return body

        self._run_benchmark("body_creation", operation, report)

    def _benchmark_collision(self, report: BenchmarkReport) -> None:
        """Benchmark collision detection."""
        from zbgym.physics.vector import Vector2D
        from zbgym.physics.body import PhysicsBody

        def operation():
            body1 = PhysicsBody(
                id="body1",
                position=Vector2D(0, 0),
                velocity=Vector2D(1, 1),
                mass=1.0,
            )
            body2 = PhysicsBody(
                id="body2",
                position=Vector2D(1, 1),
                velocity=Vector2D(-1, -1),
                mass=1.0,
            )
            diff = body1.position - body2.position
            dist = diff.length  # length is a property
            return dist < 2.0

        self._run_benchmark("collision_check", operation, report)

    def _benchmark_scheduler(self, report: BenchmarkReport) -> None:
        """Benchmark AI scheduler."""
        from unittest.mock import MagicMock
        from zbgym.ai.scheduler.scheduler import AIScheduler

        scheduler = AIScheduler(tick_rate=60, seed=42)

        def operation():
            mock_state = MagicMock()
            mock_state.tick = 0
            scheduler.tick(mock_state)

        self._run_benchmark("scheduler_tick", operation, report)
        scheduler.shutdown()

    def _benchmark_event_bus(self, report: BenchmarkReport) -> None:
        """Benchmark event bus."""
        from zbgym.engine.event_bus import EventBus
        from zbgym.constants import EventType

        bus = EventBus()

        def operation():
            bus.emit(EventType.MATCH_START, data={"tick": 0})

        self._run_benchmark("event_emit", operation, report)

    def _benchmark_replay(self, report: BenchmarkReport) -> None:
        """Benchmark replay recording."""
        from zbgym.replay.recorder import ReplayRecorder

        recorder = ReplayRecorder("test", compress=False)

        def operation():
            recorder.start()
            for _ in range(10):
                recorder.record_step(state={"tick": 0})
            recorder.stop()

        self._run_benchmark("replay_record", operation, report)

    def _benchmark_memory(self, report: BenchmarkReport) -> None:
        """Benchmark memory operations."""
        from zbgym.ai.memory import Memory

        memory = Memory(capacity=100)

        def operation():
            for i in range(10):
                memory.remember(f"key_{i}", f"value_{i}")

        self._run_benchmark("memory_operations", operation, report)

    def _run_benchmark(
        self,
        name: str,
        operation: Callable[[], Any],
        report: BenchmarkReport,
    ) -> None:
        """Run a single benchmark."""
        # Warmup
        for _ in range(self._warmup):
            operation()

        # GC before benchmark
        gc.collect()

        # Benchmark
        times = []
        start = time.perf_counter()

        for _ in range(self._iterations):
            iter_start = time.perf_counter()
            operation()
            iter_end = time.perf_counter()
            times.append(iter_end - iter_start)

        total_time = time.perf_counter() - start

        times_arr = np.array(times)

        result = BenchmarkResult(
            name=name,
            iterations=self._iterations,
            total_time=total_time,
            avg_time=np.mean(times_arr),
            min_time=np.min(times_arr),
            max_time=np.max(times_arr),
            std_time=np.std(times_arr),
            ops_per_second=self._iterations / total_time,
        )

        report.add_result(result)

    def print_report(self, report: BenchmarkReport) -> None:
        """Print a human-readable report."""
        print("\n" + "=" * 80)
        print("ZBGym Performance Benchmark Report")
        print("=" * 80)
        print(f"Timestamp: {report.timestamp}")
        print(f"Total Time: {report.total_time:.2f}s")
        print("-" * 80)

        print(f"\n{'Benchmark':<30} {'Ops/sec':>15} {'Avg (ms)':>12} {'Status':>10}")
        print("-" * 80)

        for result in report.results:
            status = "✅ PASS" if result.passes else "❌ FAIL"
            print(
                f"{result.name:<30} "
                f"{result.ops_per_second:>15.2f} "
                f"{result.avg_time * 1000:>12.4f} "
                f"{status:>10}"
            )

        print("-" * 80)
        print(f"Total: {report.benchmarks_passed} passed, {report.benchmarks_failed} failed")
        print("=" * 80)


def run_quick_benchmark() -> BenchmarkReport:
    """Run a quick benchmark with fewer iterations."""
    benchmark = Benchmark(warmup=5, iterations=100)
    return benchmark.run_all()


def run_full_benchmark() -> BenchmarkReport:
    """Run a full benchmark with more iterations."""
    benchmark = Benchmark(warmup=10, iterations=1000)
    return benchmark.run_all()
