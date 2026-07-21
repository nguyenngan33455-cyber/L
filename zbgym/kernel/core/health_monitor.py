"""
HealthMonitor implementation for ZBGym Kernel.

Tracks module health, heartbeats, and recovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Callable
import time


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthReport:
    """Health report for a module or system."""
    
    timestamp: float
    status: HealthStatus
    module: str | None = None
    message: str | None = None
    latency_ms: float = 0.0
    failures: int = 0
    recovery_count: int = 0


@dataclass
class ModuleHealth:
    """Health tracking for a single module."""
    
    name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    last_heartbeat: float = 0.0
    last_check: float = 0.0
    failures: int = 0
    recovery_count: int = 0
    check_func: Callable[[], bool] | None = None
    metadata: dict = field(default_factory=dict)


class HealthMonitor:
    """
    Health monitoring system.
    
    Tracks health of all modules, performs heartbeats, and reports health status.
    """

    def __init__(self, event_bus: Any = None) -> None:
        """
        Initialize the health monitor.
        
        Args:
            event_bus: Optional event bus for health events
        """
        self._modules: dict[str, ModuleHealth] = {}
        self._lock = Lock()
        self._event_bus = event_bus
        self._healthy_threshold: float = 10.0  # seconds
        self._report_callbacks: list[Callable[[HealthReport], None]] = []

    def register_module(
        self,
        name: str,
        check_func: Callable[[], bool] | None = None,
        metadata: dict | None = None
    ) -> None:
        """
        Register a module for health monitoring.
        
        Args:
            name: Module name
            check_func: Optional health check function
            metadata: Optional metadata
        """
        with self._lock:
            self._modules[name] = ModuleHealth(
                name=name,
                check_func=check_func,
                metadata=metadata or {},
                last_heartbeat=time.time()
            )

    def unregister_module(self, name: str) -> bool:
        """
        Unregister a module.
        
        Args:
            name: Module name
            
        Returns:
            True if unregistered
        """
        with self._lock:
            if name in self._modules:
                del self._modules[name]
                return True
            return False

    def heartbeat(self, name: str) -> bool:
        """
        Record module heartbeat.
        
        Args:
            name: Module name
            
        Returns:
            True if heartbeat recorded
        """
        with self._lock:
            if name in self._modules:
                self._modules[name].last_heartbeat = time.time()
                self._modules[name].status = HealthStatus.HEALTHY
                return True
            return False

    def record_failure(self, name: str, error: str | None = None) -> None:
        """
        Record module failure.
        
        Args:
            name: Module name
            error: Optional error message
        """
        with self._lock:
            if name in self._modules:
                module = self._modules[name]
                module.failures += 1
                module.status = HealthStatus.UNHEALTHY
                if error:
                    module.metadata["last_error"] = error

    def record_recovery(self, name: str) -> None:
        """
        Record module recovery.
        
        Args:
            name: Module name
        """
        with self._lock:
            if name in self._modules:
                module = self._modules[name]
                module.recovery_count += 1
                module.status = HealthStatus.HEALTHY
                module.failures = 0

    def check_health(self) -> list[HealthReport]:
        """
        Check health of all modules.
        
        Returns:
            List of health reports
        """
        reports = []
        current_time = time.time()

        with self._lock:
            for name, module in self._modules.items():
                # Check heartbeat timeout
                if current_time - module.last_heartbeat > self._healthy_threshold:
                    module.status = HealthStatus.UNHEALTHY

                # Run check function if available
                if module.check_func:
                    try:
                        is_healthy = module.check_func()
                        if not is_healthy:
                            module.status = HealthStatus.UNHEALTHY
                    except Exception:
                        module.status = HealthStatus.UNHEALTHY

                module.last_check = current_time

                reports.append(HealthReport(
                    timestamp=current_time,
                    status=module.status,
                    module=name,
                    failures=module.failures,
                    recovery_count=module.recovery_count,
                    latency_ms=0.0
                ))

        # Notify callbacks
        for report in reports:
            for callback in self._report_callbacks:
                try:
                    callback(report)
                except Exception:
                    pass

        return reports

    def get_module_health(self, name: str) -> HealthReport | None:
        """
        Get health for specific module.
        
        Args:
            name: Module name
            
        Returns:
            Health report or None
        """
        with self._lock:
            if name not in self._modules:
                return None

            module = self._modules[name]
            return HealthReport(
                timestamp=module.last_check,
                status=module.status,
                module=name,
                failures=module.failures,
                recovery_count=module.recovery_count
            )

    def subscribe(self, callback: Callable[[HealthReport], None]) -> None:
        """
        Subscribe to health reports.
        
        Args:
            callback: Callback function
        """
        with self._lock:
            self._report_callbacks.append(callback)

    def unsubscribe(self, callback: Callable[[HealthReport], None]) -> None:
        """
        Unsubscribe from health reports.
        
        Args:
            callback: Callback function
        """
        with self._lock:
            if callback in self._report_callbacks:
                self._report_callbacks.remove(callback)

    def get_overall_health(self) -> HealthStatus:
        """
        Get overall system health.
        
        Returns:
            Overall health status
        """
        with self._lock:
            if not self._modules:
                return HealthStatus.UNKNOWN

            statuses = [m.status for m in self._modules.values()]

            if all(s == HealthStatus.HEALTHY for s in statuses):
                return HealthStatus.HEALTHY
            elif any(s == HealthStatus.UNHEALTHY for s in statuses):
                return HealthStatus.UNHEALTHY
            elif any(s == HealthStatus.DEGRADED for s in statuses):
                return HealthStatus.DEGRADED
            return HealthStatus.UNKNOWN

    def shutdown(self) -> None:
        """Shutdown the health monitor."""
        with self._lock:
            self._modules.clear()
            self._report_callbacks.clear()
