"""Tests for ZBGym CLI."""

from zbgym.cli import commands
from zbgym.cli.main import CLI


class TestCLI:
    """Tests for CLI."""

    def test_cli_creation(self):
        """Test creating CLI."""
        cli = CLI()
        assert cli is not None

    def test_show_help(self):
        """Test showing help."""
        cli = CLI()
        result = cli.show_help()
        assert result == 0

    def test_show_version(self):
        """Test showing version."""
        cli = CLI()
        result = cli.show_version()
        assert result == 0

    def test_unknown_command(self, capsys):
        """Test unknown command."""
        cli = CLI()
        cli.argv = ["unknown_command"]
        result = cli.run()
        assert result == 1


class TestCommands:
    """Tests for CLI commands."""

    def test_init(self, tmp_path):
        """Test init command."""
        result = commands.init([str(tmp_path)])
        assert result == 0
        assert (tmp_path / "config").exists()
        assert (tmp_path / "models").exists()
        assert (tmp_path / "logs").exists()
        assert (tmp_path / "replays").exists()

    def test_doctor(self):
        """Test doctor command."""
        result = commands.doctor([])
        assert result == 0

    def test_plugins(self):
        """Test plugins command."""
        result = commands.plugins([])
        assert result == 0

    def test_plugins_characters(self):
        """Test plugins command for characters."""
        result = commands.plugins(["--type", "character"])
        assert result == 0

    def test_plugins_weapons(self):
        """Test plugins command for weapons."""
        result = commands.plugins(["--type", "weapon"])
        assert result == 0

    def test_plugins_skills(self):
        """Test plugins command for skills."""
        result = commands.plugins(["--type", "skill"])
        assert result == 0

    def test_export(self, tmp_path):
        """Test export command."""
        # Create a dummy model file
        model_file = tmp_path / "model.zip"
        model_file.write_text("dummy")
        result = commands.export([str(model_file), "--format", "onnx"])
        # Should handle gracefully even if not fully implemented
        assert result == 0
