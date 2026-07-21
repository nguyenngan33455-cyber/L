"""CLI tools for ZBGym."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from zbgym import __version__
from zbgym.devtools.diagnostics.doctor import Doctor
from zbgym.devtools.diagnostics.replay_inspector import ReplayInspector
from zbgym.devtools.diagnostics.plugin_validator import PluginValidator
from zbgym.devtools.benchmark.runner import Benchmark
from zbgym.devtools.packaging.builder import PluginBuilder


class CLI:
    """
    ZBGym CLI interface.

    Provides commands for development, validation, and diagnostics.
    """

    def __init__(self) -> None:
        """Initialize CLI."""
        self._parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            prog="zbgym",
            description="ZBGym Developer Tools",
        )

        parser.add_argument(
            "--version",
            action="version",
            version=f"ZBGym {__version__}",
        )

        subparsers = parser.add_subparsers(dest="command", help="Commands")

        # Info command
        self._add_info_command(subparsers)

        # Doctor command
        self._add_doctor_command(subparsers)

        # Plugin commands
        self._add_plugin_commands(subparsers)

        # Replay commands
        self._add_replay_commands(subparsers)

        # Benchmark command
        self._add_benchmark_command(subparsers)

        return parser

    def _add_info_command(self, subparsers) -> None:
        """Add info subcommand."""
        parser = subparsers.add_parser("info", help="Show framework info")
        parser.add_argument("--verbose", "-v", action="store_true")

    def _add_doctor_command(self, subparsers) -> None:
        """Add doctor subcommand."""
        subparsers.add_parser("doctor", help="Run framework diagnostics")

    def _add_plugin_commands(self, subparsers) -> None:
        """Add plugin subcommands."""
        plugin_parser = subparsers.add_parser("plugin", help="Plugin commands")
        plugin_subparsers = plugin_parser.add_subparsers(
            dest="plugin_command", help="Plugin subcommands"
        )

        # Plugin list
        list_parser = plugin_subparsers.add_parser("list", help="List plugins")
        list_parser.add_argument(
            "--path", "-p", default="./plugins", help="Plugin directory"
        )

        # Plugin validate
        validate_parser = plugin_subparsers.add_parser(
            "validate", help="Validate plugin"
        )
        validate_parser.add_argument("path", help="Plugin path")

        # Plugin create
        create_parser = plugin_subparsers.add_parser("create", help="Create plugin")
        create_parser.add_argument("name", help="Plugin name")
        create_parser.add_argument(
            "--path", "-p", default="./plugins", help="Output directory"
        )

        # Plugin package
        package_parser = plugin_subparsers.add_parser("package", help="Package plugin")
        package_parser.add_argument(
            "path", help="Plugin directory"
        )
        package_parser.add_argument(
            "--output", "-o", help="Output name"
        )

    def _add_replay_commands(self, subparsers) -> None:
        """Add replay subcommands."""
        replay_parser = subparsers.add_parser("replay", help="Replay commands")
        replay_subparsers = replay_parser.add_subparsers(
            dest="replay_command", help="Replay subcommands"
        )

        # Replay inspect
        inspect_parser = replay_subparsers.add_parser(
            "inspect", help="Inspect replay file"
        )
        inspect_parser.add_argument("path", help="Replay file path")

        # Replay verify
        verify_parser = replay_subparsers.add_parser(
            "verify", help="Verify replay file"
        )
        verify_parser.add_argument("path", help="Replay file path")

        # Replay hash
        hash_parser = replay_subparsers.add_parser("hash", help="Get replay hash")
        hash_parser.add_argument("path", help="Replay file path")

    def _add_benchmark_command(self, subparsers) -> None:
        """Add benchmark subcommand."""
        parser = subparsers.add_parser("benchmark", help="Run benchmarks")
        parser.add_argument(
            "--quick", "-q", action="store_true", help="Quick benchmark"
        )
        parser.add_argument(
            "--iterations", "-i", type=int, default=100, help="Iterations"
        )

    def run(self, args: list[str] | None = None) -> int:
        """
        Run CLI.

        Args:
            args: Command line arguments (uses sys.argv if None)

        Returns:
            Exit code
        """
        parsed = self._parser.parse_args(args)

        if not parsed.command:
            self._parser.print_help()
            return 0

        return self._dispatch(parsed)

    def _dispatch(self, parsed: argparse.Namespace) -> int:
        """Dispatch to command handler."""
        command = parsed.command

        if command == "info":
            return self._cmd_info(parsed)
        elif command == "doctor":
            return self._cmd_doctor(parsed)
        elif command == "plugin":
            return self._cmd_plugin(parsed)
        elif command == "replay":
            return self._cmd_replay(parsed)
        elif command == "benchmark":
            return self._cmd_benchmark(parsed)

        return 0

    def _cmd_info(self, args: Any) -> int:
        """Handle info command."""
        print(f"ZBGym v{__version__}")
        print(f"Python: {sys.version}")
        print(f"Platform: {sys.platform}")
        return 0

    def _cmd_doctor(self, args: Any) -> int:
        """Handle doctor command."""
        doctor = Doctor()
        report = doctor.run_all_checks()
        doctor.print_report(report)
        return 0 if report.is_healthy else 1

    def _cmd_plugin(self, args: Any) -> int:
        """Handle plugin commands."""
        plugin_command = args.plugin_command

        if plugin_command == "list":
            return self._cmd_plugin_list(args)
        elif plugin_command == "validate":
            return self._cmd_plugin_validate(args)
        elif plugin_command == "create":
            return self._cmd_plugin_create(args)
        elif plugin_command == "package":
            return self._cmd_plugin_package(args)

        return 0

    def _cmd_plugin_list(self, args: Any) -> int:
        """List plugins."""
        from zbgym.plugin_sdk.loader import PluginLoader

        plugin_path = Path(args.path)
        if not plugin_path.exists():
            print(f"Plugin directory not found: {plugin_path}")
            return 1

        loader = PluginLoader()
        plugins = loader.discover_plugins(plugin_path)

        if not plugins:
            print("No plugins found.")
            return 0

        print(f"\nPlugins in {plugin_path}:")
        print("-" * 60)
        for plugin in plugins:
            print(f"  {plugin.name} v{plugin.version}")
            print(f"    Author: {plugin.metadata.author}")
            print(f"    Capabilities: {', '.join(plugin.capabilities)}")
            print()

        return 0

    def _cmd_plugin_validate(self, args: Any) -> int:
        """Validate plugin."""
        validator = PluginValidator()
        result = validator.validate(args.path)
        validator.print_result(result)
        return 0 if result.is_valid else 1

    def _cmd_plugin_create(self, args: Any) -> int:
        """Create plugin."""
        builder = PluginBuilder("./")
        try:
            path = builder.create_template(args.name, args.path)
            print(f"Created plugin: {path}")
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _cmd_plugin_package(self, args: Any) -> int:
        """Package plugin."""
        builder = PluginBuilder(args.path)
        info = builder.build(args.output)
        return 0 if info else 1

    def _cmd_replay(self, args: Any) -> int:
        """Handle replay commands."""
        replay_command = args.replay_command

        if replay_command == "inspect":
            return self._cmd_replay_inspect(args)
        elif replay_command == "verify":
            return self._cmd_replay_verify(args)
        elif replay_command == "hash":
            return self._cmd_replay_hash(args)

        return 0

    def _cmd_replay_inspect(self, args: Any) -> int:
        """Inspect replay."""
        inspector = ReplayInspector()
        info = inspector.inspect(args.path)
        if info:
            inspector.print_info(info)
            return 0
        return 1

    def _cmd_replay_verify(self, args: Any) -> int:
        """Verify replay."""
        inspector = ReplayInspector()
        valid, errors = inspector.verify(args.path)

        if valid:
            print(f"✅ Replay is valid: {args.path}")
            return 0
        else:
            print(f"❌ Replay has issues: {args.path}")
            for error in errors:
                print(f"  - {error}")
            return 1

    def _cmd_replay_hash(self, args: Any) -> int:
        """Get replay hash."""
        inspector = ReplayInspector()
        hash_value = inspector.get_hash(args.path)

        if hash_value:
            print(hash_value)
            return 0
        return 1

    def _cmd_benchmark(self, args: Any) -> int:
        """Run benchmark."""
        iterations = 100 if args.quick else args.iterations

        print(f"Running benchmark ({iterations} iterations)...")
        benchmark = Benchmark(iterations=iterations)
        report = benchmark.run_all()
        benchmark.print_report(report)

        return 0


def main() -> int:
    """Main entry point."""
    cli = CLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
