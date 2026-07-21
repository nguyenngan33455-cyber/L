"""Tests for ZBGym Developer Tools."""

import pytest
from pathlib import Path

from zbgym.devtools.diagnostics.doctor import Doctor, DiagnosticReport
from zbgym.devtools.benchmark.runner import Benchmark, BenchmarkReport
from zbgym.devtools.packaging.builder import PluginBuilder, PackageVerifier
from zbgym.devtools.profiler.simulator import Profiler, TickProfiler
from zbgym.devtools.diagnostics.plugin_validator import PluginValidator
from zbgym.devtools.diagnostics.replay_inspector import ReplayInspector


# ============================================================================
# Doctor Tests
# ============================================================================

class TestDoctor:
    """Test Doctor diagnostics."""

    def test_run_all_checks(self):
        """Test running all checks."""
        doctor = Doctor()
        report = doctor.run_all_checks()

        assert report.total_checks > 0
        assert report.python_version != ""
        assert report.zbgym_version != ""

    def test_report_is_healthy(self):
        """Test report health status."""
        doctor = Doctor()
        report = doctor.run_all_checks()

        # Report should have health status
        assert hasattr(report, "is_healthy")
        assert isinstance(report.is_healthy, bool)

    def test_report_to_dict(self):
        """Test report serialization."""
        doctor = Doctor()
        report = doctor.run_all_checks()
        d = report.to_dict()

        assert "total_checks" in d
        assert "passed_checks" in d
        assert "failed_checks" in d
        assert "results" in d


# ============================================================================
# Benchmark Tests
# ============================================================================

class TestBenchmark:
    """Test Benchmark."""

    def test_run_vector_benchmark(self):
        """Test vector operations benchmark."""
        benchmark = Benchmark(warmup=2, iterations=10)
        report = benchmark.run_all()

        assert report.total_time > 0
        assert len(report.results) > 0

    def test_benchmark_result(self):
        """Test benchmark result."""
        from zbgym.devtools.benchmark.runner import BenchmarkResult

        result = BenchmarkResult(
            name="test",
            iterations=100,
            total_time=1.0,
            avg_time=0.01,
            min_time=0.005,
            max_time=0.02,
            std_time=0.003,
            ops_per_second=100.0,
        )

        assert result.passes is True

    def test_report_to_dict(self):
        """Test benchmark report serialization."""
        benchmark = Benchmark(warmup=1, iterations=5)
        report = benchmark.run_all()
        d = report.to_dict()

        assert "total_time" in d
        assert "results" in d


# ============================================================================
# Profiler Tests
# ============================================================================

class TestProfiler:
    """Test Profiler."""

    def test_profile_function(self):
        """Test profiling a function."""
        profiler = Profiler()

        def slow_func():
            total = 0
            for i in range(100):
                total += i
            return total

        result = profiler.profile_function(slow_func, "slow_test")

        assert result.name == "slow_test"
        assert result.total_time > 0

    def test_tick_profiler(self):
        """Test tick profiler."""
        profiler = TickProfiler()

        profiler.start_tick()
        profiler.start_phase("test_phase")
        # Do some work
        _ = sum(range(100))
        profiler.end_phase()
        profiler.end_tick()

        stats = profiler.get_statistics()
        assert "tick_count" in stats
        assert stats["tick_count"] == 1


# ============================================================================
# Plugin Builder Tests
# ============================================================================

class TestPluginBuilder:
    """Test PluginBuilder."""

    def test_validate_missing_directory(self, tmp_path):
        """Test validation of missing directory."""
        builder = PluginBuilder(tmp_path / "missing")
        valid, errors = builder.validate()

        assert valid is False
        assert len(errors) > 0

    def test_validate_missing_manifest(self, tmp_path):
        """Test validation of missing manifest."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        builder = PluginBuilder(plugin_dir)
        valid, errors = builder.validate()

        assert valid is False
        assert any("plugin.toml" in e for e in errors)

    def test_validate_valid_plugin(self, tmp_path):
        """Test validation of valid plugin."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        # Create manifest
        manifest = """[plugin]
name = "test"
version = "1.0.0"
"""
        (plugin_dir / "plugin.toml").write_text(manifest)

        # Create entry point
        (plugin_dir / "plugin.py").write_text('class Plugin: pass\n')

        # Create README (recommended)
        (plugin_dir / "README.md").write_text("# Test Plugin\n")

        builder = PluginBuilder(plugin_dir)
        valid, errors = builder.validate()

        # Should pass - warnings are okay
        assert valid is True
        assert len([e for e in errors if "error" not in e.lower()]) == 0

    def test_create_template(self, tmp_path):
        """Test plugin template creation."""
        # Use unique name to avoid collision
        import uuid
        plugin_name = f"test_plugin_{uuid.uuid4().hex[:8]}"
        
        builder = PluginBuilder(tmp_path)
        path = builder.create_template(plugin_name)

        assert path.exists()
        assert (path / "plugin.toml").exists()
        assert (path / "plugin.py").exists()
        assert (path / "README.md").exists()


# ============================================================================
# Package Verifier Tests
# ============================================================================

class TestPackageVerifier:
    """Test PackageVerifier."""

    def test_verify_missing_file(self):
        """Test verification of missing file."""
        valid, error = PackageVerifier.verify(Path("/missing"))
        assert valid is False
        assert error is not None


# ============================================================================
# Plugin Validator Tests
# ============================================================================

class TestPluginValidator:
    """Test PluginValidator."""

    def test_validate_missing_directory(self):
        """Test validation of missing directory."""
        validator = PluginValidator()
        result = validator.validate("/missing")

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_valid_plugin(self, tmp_path):
        """Test validation of valid plugin."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        # Create manifest
        manifest = """[plugin]
name = "test"
version = "1.0.0"
api-version = "1.0"
"""
        (plugin_dir / "plugin.toml").write_text(manifest)

        # Create entry point
        (plugin_dir / "plugin.py").write_text('class Plugin: pass\n')

        validator = PluginValidator()
        result = validator.validate(plugin_dir)

        assert result.is_valid is True

    def test_validate_invalid_version(self, tmp_path):
        """Test validation of invalid version."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        manifest = """[plugin]
name = "test"
version = "invalid"
"""
        (plugin_dir / "plugin.toml").write_text(manifest)
        (plugin_dir / "plugin.py").write_text('class Plugin: pass\n')

        validator = PluginValidator()
        result = validator.validate(plugin_dir)

        assert result.is_valid is False


# ============================================================================
# Replay Inspector Tests
# ============================================================================

class TestReplayInspector:
    """Test ReplayInspector."""

    def test_inspect_missing_file(self):
        """Test inspection of missing file."""
        inspector = ReplayInspector()
        info = inspector.inspect(Path("/missing.replay"))

        assert info is None

    def test_verify_missing_file(self):
        """Test verification of missing file."""
        inspector = ReplayInspector()
        valid, errors = inspector.verify(Path("/missing.replay"))

        assert valid is False
        assert len(errors) > 0

    def test_get_hash_missing_file(self):
        """Test hash of missing file."""
        inspector = ReplayInspector()
        hash_value = inspector.get_hash(Path("/missing"))

        assert hash_value is None


# ============================================================================
# CLI Tests
# ============================================================================

class TestCLI:
    """Test CLI."""

    def test_info_command(self):
        """Test info command."""
        from zbgym.devtools.cli.parser import CLI

        cli = CLI()
        exit_code = cli.run(["info"])

        assert exit_code == 0

    def test_doctor_command(self):
        """Test doctor command."""
        from zbgym.devtools.cli.parser import CLI

        cli = CLI()
        exit_code = cli.run(["doctor"])

        # Should complete without error
        assert exit_code in (0, 1)

    def test_help_command(self):
        """Test help output."""
        from zbgym.devtools.cli.parser import CLI

        cli = CLI()
        exit_code = cli.run([])

        assert exit_code == 0

    def test_benchmark_command(self):
        """Test benchmark command."""
        from zbgym.devtools.cli.parser import CLI

        cli = CLI()
        exit_code = cli.run(["benchmark", "--quick"])

        assert exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
