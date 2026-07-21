"""
Kernel Health Monitor Tests for Phase 26.5 Validation.

Tests health monitoring and heartbeat functionality.
"""

import pytest
import time
from zbgym.kernel import (
    HealthMonitor, HealthStatus, HealthReport,
    EventDispatcher
)


class TestHealthMonitor:
    """Test health monitor."""

    def test_register_module(self):
        """Test module registration."""
        monitor = HealthMonitor()
        
        monitor.register_module("test_module")
        
        report = monitor.get_module_health("test_module")
        assert report is not None
        assert report.module == "test_module"
        assert report.status == HealthStatus.HEALTHY
        
        monitor.shutdown()

    def test_unregister_module(self):
        """Test module unregistration."""
        monitor = HealthMonitor()
        
        monitor.register_module("test_module")
        assert monitor.unregister_module("test_module") is True
        assert monitor.get_module_health("test_module") is None
        
        monitor.shutdown()

    def test_heartbeat(self):
        """Test heartbeat."""
        monitor = HealthMonitor()
        
        monitor.register_module("test_module")
        monitor.heartbeat("test_module")
        
        report = monitor.get_module_health("test_module")
        assert report.status == HealthStatus.HEALTHY
        
        monitor.shutdown()

    def test_record_failure(self):
        """Test failure recording."""
        monitor = HealthMonitor()
        
        monitor.register_module("test_module")
        monitor.record_failure("test_module", "Test error")
        
        report = monitor.get_module_health("test_module")
        assert report.status == HealthStatus.UNHEALTHY
        assert report.failures == 1
        
        monitor.shutdown()

    def test_record_recovery(self):
        """Test recovery recording."""
        monitor = HealthMonitor()
        
        monitor.register_module("test_module")
        monitor.record_failure("test_module")
        monitor.record_recovery("test_module")
        
        report = monitor.get_module_health("test_module")
        assert report.status == HealthStatus.HEALTHY
        assert report.recovery_count == 1
        
        monitor.shutdown()

    def test_health_check_function(self):
        """Test health check function."""
        monitor = HealthMonitor()
        
        def failing_check():
            return False
        
        def passing_check():
            return True
        
        monitor.register_module("failing", failing_check)
        monitor.register_module("passing", passing_check)
        
        reports = monitor.check_health()
        
        # Find reports
        failing_report = next(r for r in reports if r.module == "failing")
        passing_report = next(r for r in reports if r.module == "passing")
        
        assert failing_report.status == HealthStatus.UNHEALTHY
        assert passing_report.status == HealthStatus.HEALTHY
        
        monitor.shutdown()

    def test_overall_health(self):
        """Test overall health calculation."""
        monitor = HealthMonitor()
        
        monitor.register_module("module1")
        monitor.register_module("module2")
        monitor.register_module("module3")
        
        # All healthy
        assert monitor.get_overall_health() == HealthStatus.HEALTHY
        
        # One unhealthy
        monitor.record_failure("module1")
        assert monitor.get_overall_health() == HealthStatus.UNHEALTHY
        
        monitor.shutdown()

    def test_subscription(self):
        """Test health report subscription."""
        monitor = HealthMonitor()
        
        received = []
        
        def callback(report):
            received.append(report)
        
        monitor.subscribe(callback)
        
        monitor.register_module("test_module")
        monitor.check_health()
        
        assert len(received) > 0
        
        monitor.unsubscribe(callback)
        monitor.shutdown()


class TestHealthReport:
    """Test health report."""

    def test_report_creation(self):
        """Test health report creation."""
        report = HealthReport(
            timestamp=time.time(),
            status=HealthStatus.HEALTHY,
            module="test_module",
            message="All good",
            latency_ms=0.5,
            failures=0,
            recovery_count=0
        )
        
        assert report.module == "test_module"
        assert report.status == HealthStatus.HEALTHY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
