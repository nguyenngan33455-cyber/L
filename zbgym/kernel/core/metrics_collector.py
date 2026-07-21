"""
MetricsCollector implementation for ZBGym Kernel.

Collects and aggregates performance metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any
import time


@dataclass
class Metric:
    """Represents a single metric."""
    name: str
    value: float
    timestamp: float
    unit: str = ""
    tags: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Metrics collection system.
    
    Collects counters, gauges, histograms, and timers.
    Thread-safe.
    """

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._timers: dict[str, list[float]] = {}
        self._lock = Lock()
        self._start_time: float = time.time()

    def counter(self, name: str, value: float = 1.0) -> None:
        """
        Increment a counter.
        
        Args:
            name: Counter name
            value: Value to add
        """
        with self._lock:
            self._counters[name] = self._counters.get(name, 0.0) + value

    def gauge(self, name: str, value: float) -> None:
        """
        Set a gauge value.
        
        Args:
            name: Gauge name
            value: Gauge value
        """
        with self._lock:
            self._gauges[name] = value

    def histogram(self, name: str, value: float) -> None:
        """
        Record a histogram value.
        
        Args:
            name: Histogram name
            value: Value to record
        """
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = []
            self._histograms[name].append(value)

    def timer(self, name: str, duration_ms: float) -> None:
        """
        Record a timer value.
        
        Args:
            name: Timer name
            duration_ms: Duration in milliseconds
        """
        with self._lock:
            if name not in self._timers:
                self._timers[name] = []
            self._timers[name].append(duration_ms)

    def get_counter(self, name: str) -> float:
        """Get counter value."""
        with self._lock:
            return self._counters.get(name, 0.0)

    def get_gauge(self, name: str) -> float | None:
        """Get gauge value."""
        with self._lock:
            return self._gauges.get(name)

    def get_histogram_stats(self, name: str) -> dict[str, float] | None:
        """
        Get histogram statistics.
        
        Args:
            name: Histogram name
            
        Returns:
            Statistics dict or None
        """
        with self._lock:
            values = self._histograms.get(name)
            if not values:
                return None

            sorted_values = sorted(values)
            count = len(sorted_values)

            return {
                "count": count,
                "min": sorted_values[0],
                "max": sorted_values[-1],
                "mean": sum(sorted_values) / count,
                "p50": sorted_values[count // 2],
                "p95": sorted_values[int(count * 0.95)] if count > 1 else sorted_values[0],
                "p99": sorted_values[int(count * 0.99)] if count > 1 else sorted_values[0],
            }

    def get_timer_stats(self, name: str) -> dict[str, float] | None:
        """
        Get timer statistics.
        
        Args:
            name: Timer name
            
        Returns:
            Statistics dict or None
        """
        return self.get_histogram_stats(name)

    def record_tick_duration(self, duration_ms: float) -> None:
        """Record tick duration."""
        self.histogram("kernel.tick.duration_ms", duration_ms)

    def record_stage_duration(self, stage: str, duration_ms: float) -> None:
        """Record stage duration."""
        self.histogram(f"kernel.stage.{stage}.duration_ms", duration_ms)

    def record_boot_duration(self, duration_ms: float) -> None:
        """Record boot duration."""
        self.histogram("kernel.boot.duration_ms", duration_ms)

    def record_shutdown_duration(self, duration_ms: float) -> None:
        """Record shutdown duration."""
        self.histogram("kernel.shutdown.duration_ms", duration_ms)

    def get_summary(self) -> dict[str, Any]:
        """Get metrics summary."""
        with self._lock:
            elapsed = time.time() - self._start_time

            summary = {
                "uptime_seconds": elapsed,
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {},
                "timers": {}
            }

            for name, values in self._histograms.items():
                stats = self.get_histogram_stats(name)
                if stats:
                    summary["histograms"][name] = stats

            for name, values in self._timers.items():
                stats = self.get_timer_stats(name)
                if stats:
                    summary["timers"][name] = stats

            return summary

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
            self._start_time = time.time()

    def shutdown(self) -> None:
        """Shutdown the metrics collector."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
