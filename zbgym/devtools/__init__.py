"""
ZBGym Developer Tools

Professional development tools for ZBGym.

Modules:
- diagnostics: Framework and plugin diagnostics
- benchmark: Performance benchmarking
- profiler: Simulation profiling
- packaging: Plugin packaging tools
- cli: CLI extensions
- validator: Plugin validation
- replay_inspector: Replay file inspection

Example:
    >>> from zbgym.devtools import Doctor, Benchmark
    >>> doctor = Doctor()
    >>> report = doctor.run_all_checks()
    >>> print(report)
"""

from zbgym.devtools.diagnostics.doctor import Doctor
from zbgym.devtools.benchmark.runner import Benchmark
from zbgym.devtools.packaging.builder import PluginBuilder
from zbgym.devtools.cli.parser import CLI

__version__ = "1.0.0"
__all__ = [
    "Doctor",
    "Benchmark",
    "PluginBuilder",
    "CLI",
]
