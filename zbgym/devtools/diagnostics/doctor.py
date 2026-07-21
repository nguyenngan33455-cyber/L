"""Framework diagnostics for ZBGym."""

from __future__ import annotations

import logging
import os
import platform
import sys
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from zbgym import __version__

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""

    name: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class DiagnosticReport:
    """Complete diagnostic report."""

    results: list[DiagnosticResult] = field(default_factory=list)
    timestamp: str = ""
    platform: str = ""
    python_version: str = ""
    zbgym_version: str = ""
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warnings_count: int = 0
    errors_count: int = 0

    @property
    def is_healthy(self) -> bool:
        """Check if all checks passed."""
        return self.failed_checks == 0

    def add_result(self, result: DiagnosticResult) -> None:
        """Add a diagnostic result."""
        self.results.append(result)
        self.total_checks += 1
        if result.passed:
            self.passed_checks += 1
        else:
            self.failed_checks += 1
        self.warnings_count += len(result.warnings)
        self.errors_count += len(result.errors)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_healthy": self.is_healthy,
            "timestamp": self.timestamp,
            "platform": self.platform,
            "python_version": self.python_version,
            "zbgym_version": self.zbgym_version,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "warnings_count": self.warnings_count,
            "errors_count": self.errors_count,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                    "warnings": r.warnings,
                    "errors": r.errors,
                }
                for r in self.results
            ],
        }


class Doctor:
    """
    Framework diagnostics.

    Runs comprehensive health checks on the ZBGym framework.
    """

    def __init__(self) -> None:
        """Initialize the doctor."""
        self._checks: list[callable] = []

    def run_all_checks(self) -> DiagnosticReport:
        """Run all diagnostic checks."""
        from datetime import datetime

        report = DiagnosticReport(
            timestamp=datetime.now().isoformat(),
            platform=platform.platform(),
            python_version=sys.version,
            zbgym_version=__version__,
        )

        # Core checks
        self._check_python_version(report)
        self._check_numpy_version(report)
        self._check_zbgym_version(report)
        self._check_imports(report)
        self._check_core_modules(report)
        self._check_configuration(report)
        self._check_memory(report)
        self._check_threading(report)

        return report

    def _check_python_version(self, report: DiagnosticReport) -> None:
        """Check Python version."""
        result = DiagnosticResult(
            name="python_version",
            passed=True,
            message="Python version OK",
            details={"version": sys.version, "executable": sys.executable},
        )

        if sys.version_info < (3, 10):
            result.passed = False
            result.message = "Python 3.10+ required"
            result.errors.append("Python 3.10 or higher is required")

        report.add_result(result)

    def _check_numpy_version(self, report: DiagnosticReport) -> None:
        """Check NumPy version."""
        result = DiagnosticResult(
            name="numpy_version",
            passed=True,
            message="NumPy version OK",
            details={"version": np.__version__},
        )

        if np.__version__.startswith("1."):
            result.warnings.append("NumPy 1.x detected. Consider upgrading to 2.x")

        report.add_result(result)

    def _check_zbgym_version(self, report: DiagnosticReport) -> None:
        """Check ZBGym version."""
        result = DiagnosticResult(
            name="zbgym_version",
            passed=True,
            message=f"ZBGym v{__version__} installed",
            details={"version": __version__},
        )

        report.add_result(result)

    def _check_imports(self, report: DiagnosticReport) -> None:
        """Check all critical imports."""
        result = DiagnosticResult(
            name="imports",
            passed=True,
            message="All imports successful",
        )

        critical_imports = [
            "zbgym",
            "zbgym.engine",
            "zbgym.physics",
            "zbgym.ai",
            "zbgym.replay",
            "zbgym.env",
        ]

        failed_imports = []
        for module in critical_imports:
            try:
                __import__(module)
            except ImportError as e:
                failed_imports.append(f"{module}: {e}")

        if failed_imports:
            result.passed = False
            result.message = "Some imports failed"
            result.errors.extend(failed_imports)

        result.details["checked"] = len(critical_imports)
        result.details["failed"] = len(failed_imports)

        report.add_result(result)

    def _check_core_modules(self, report: DiagnosticReport) -> None:
        """Check core modules exist."""
        result = DiagnosticResult(
            name="core_modules",
            passed=True,
            message="All core modules present",
        )

        required_modules = [
            "zbgym.engine.tick_system",
            "zbgym.engine.event_bus",
            "zbgym.physics.vector",
            "zbgym.physics.body",
            "zbgym.ai.scheduler",
            "zbgym.replay.recorder",
            "zbgym.env.battle_arena",
        ]

        missing = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing.append(module)

        if missing:
            result.passed = False
            result.message = "Some core modules missing"
            result.errors.extend(missing)

        result.details["checked"] = len(required_modules)
        result.details["missing"] = len(missing)

        report.add_result(result)

    def _check_configuration(self, report: DiagnosticReport) -> None:
        """Check framework configuration."""
        result = DiagnosticResult(
            name="configuration",
            passed=True,
            message="Configuration OK",
        )

        try:
            from zbgym.config import EnvironmentConfig

            config = EnvironmentConfig()
            result.details = {
                "tick_rate": config.tick_rate,
                "map_width": config.map_width,
                "map_height": config.map_height,
            }
        except Exception as e:
            result.passed = False
            result.message = "Configuration error"
            result.errors.append(str(e))

        report.add_result(result)

    def _check_memory(self, report: DiagnosticReport) -> None:
        """Check memory availability."""
        result = DiagnosticResult(
            name="memory",
            passed=True,
            message="Memory check OK",
        )

        try:
            import psutil

            mem = psutil.virtual_memory()
            result.details = {
                "total_gb": mem.total / (1024**3),
                "available_gb": mem.available / (1024**3),
                "percent_used": mem.percent,
            }

            if mem.percent > 90:
                result.warnings.append("Memory usage above 90%")
        except ImportError:
            result.warnings.append("psutil not installed - memory check skipped")

        report.add_result(result)

    def _check_threading(self, report: DiagnosticReport) -> None:
        """Check threading capabilities."""
        result = DiagnosticResult(
            name="threading",
            passed=True,
            message="Threading OK",
            details={"max_workers": os.cpu_count() or 1},
        )

        import threading

        try:
            thread = threading.Thread(target=lambda: None)
            thread.start()
            thread.join(timeout=1)
            if not thread.is_alive():
                result.details["test_passed"] = True
            else:
                result.warnings.append("Thread did not complete in time")
        except Exception as e:
            result.passed = False
            result.errors.append(f"Thread test failed: {e}")

        report.add_result(result)

    def print_report(self, report: DiagnosticReport) -> None:
        """Print a human-readable report."""
        print("\n" + "=" * 60)
        print("ZBGym Framework Doctor Report")
        print("=" * 60)
        print(f"Platform: {report.platform}")
        print(f"Python: {report.python_version}")
        print(f"ZBGym: v{report.zbgym_version}")
        print(f"Time: {report.timestamp}")
        print("-" * 60)

        for result in report.results:
            status = "✅" if result.passed else "❌"
            print(f"\n{status} {result.name}: {result.message}")

            if result.warnings:
                for warning in result.warnings:
                    print(f"   ⚠️  {warning}")

            if result.errors:
                for error in result.errors:
                    print(f"   ❌ {error}")

        print("\n" + "-" * 60)
        print(f"Total: {report.total_checks} checks")
        print(f"Passed: {report.passed_checks}")
        print(f"Failed: {report.failed_checks}")
        print(f"Warnings: {report.warnings_count}")
        print("=" * 60)

        if report.is_healthy:
            print("\n✅ Framework is healthy!")
        else:
            print("\n❌ Framework has issues. Please review above.")
