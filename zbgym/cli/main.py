"""CLI main module for ZBGym."""

from __future__ import annotations

import sys
from typing import Any


class CLI:
    """Main CLI class for ZBGym."""

    COMMANDS = {
        "init": "Initialize a new ZBGym project",
        "train": "Train an RL agent",
        "evaluate": "Evaluate a trained model",
        "replay": "Play back a recorded episode",
        "dashboard": "Start the web dashboard",
        "plugins": "List available plugins",
        "export": "Export a model",
        "doctor": "Check system requirements",
        "version": "Show version information",
        "help": "Show this help message",
    }

    def __init__(self) -> None:
        self.argv = sys.argv[1:]

    def run(self) -> int:
        """Run the CLI."""
        if not self.argv:
            return self.show_help()

        command = self.argv[0]

        if command == "help" or command == "--help" or command == "-h":
            return self.show_help()

        if command == "version":
            return self.show_version()

        if command not in self.COMMANDS:
            print(f"Error: Unknown command '{command}'")
            print("Run 'zbgym help' for usage information.")
            return 1

        # Import and run the command
        try:
            from zbgym.cli import commands
            cmd_func = getattr(commands, command, None)
            if cmd_func is None:
                print(f"Error: Command '{command}' not implemented")
                return 1
            return cmd_func(self.argv[1:])
        except ImportError as e:
            print(f"Error: Could not load command '{command}': {e}")
            return 1

    def show_help(self) -> int:
        """Show help message."""
        print("ZBGym - Professional RL Framework for Battle Arena")
        print()
        print("Usage: zbgym <command> [options]")
        print()
        print("Commands:")
        for cmd, desc in self.COMMANDS.items():
            print(f"  {cmd:12} {desc}")
        print()
        print("Run 'zbgym <command> --help' for more information on a command.")
        return 0

    def show_version(self) -> int:
        """Show version information."""
        from zbgym import __version__
        print(f"ZBGym version {__version__}")
        return 0


def main() -> int:
    """Main entry point."""
    cli = CLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
