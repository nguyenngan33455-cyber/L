"""Plugin validator for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import toml

from zbgym.plugin_sdk.base import PluginMetadata


@dataclass
class ValidationResult:
    """Result of plugin validation."""

    name: str
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str) -> None:
        """Add an error."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning."""
        self.warnings.append(message)

    def add_info(self, key: str, value: Any) -> None:
        """Add info."""
        self.info[key] = value


class PluginValidator:
    """
    Validate ZBGym plugins.

    Checks manifest, dependencies, API version, hooks, and structure.
    """

    def __init__(self) -> None:
        """Initialize the validator."""
        self._required_hooks = {
            "initialize",
            "load",
            "enable",
            "disable",
            "shutdown",
        }

    def validate(self, plugin_dir: Path | str) -> ValidationResult:
        """
        Validate a plugin directory.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            ValidationResult
        """
        plugin_dir = Path(plugin_dir)
        result = ValidationResult(name=plugin_dir.name, is_valid=True)

        # Check directory exists
        if not plugin_dir.exists():
            result.add_error(f"Plugin directory does not exist: {plugin_dir}")
            return result

        # Check manifest
        manifest_result = self._validate_manifest(plugin_dir)
        if not manifest_result.is_valid:
            result.is_valid = False
            result.errors.extend(manifest_result.errors)

        result.warnings.extend(manifest_result.warnings)
        result.info.update(manifest_result.info)

        # Check entry point
        entry_result = self._validate_entry_point(plugin_dir)
        if not entry_result.is_valid:
            result.is_valid = False
            result.errors.extend(entry_result.errors)

        result.warnings.extend(entry_result.warnings)

        # Check documentation
        doc_result = self._validate_documentation(plugin_dir)
        result.warnings.extend(doc_result.warnings)

        # Check structure
        structure_result = self._validate_structure(plugin_dir)
        if not structure_result.is_valid:
            result.is_valid = False
            result.errors.extend(structure_result.errors)

        return result

    def _validate_manifest(self, plugin_dir: Path) -> ValidationResult:
        """Validate plugin.toml."""
        result = ValidationResult(name="manifest", is_valid=True)

        manifest_path = plugin_dir / "plugin.toml"
        if not manifest_path.exists():
            result.add_error("Missing plugin.toml")
            return result

        try:
            with open(manifest_path) as f:
                manifest = toml.load(f)
        except Exception as e:
            result.add_error(f"Failed to parse plugin.toml: {e}")
            return result

        plugin_info = manifest.get("plugin", {})

        # Required fields
        required_fields = {
            "name": "Plugin name",
            "version": "Version",
        }

        for field, description in required_fields.items():
            if not plugin_info.get(field):
                result.add_error(f"Missing required field: {field}")

        # Validate version format
        version = plugin_info.get("version", "")
        if version and not self._is_valid_version(version):
            result.add_error(f"Invalid version format: {version}")

        # Validate API version
        api_version = plugin_info.get("api-version", "1.0")
        if api_version not in ("1.0", "1.1", "2.0"):
            result.add_warning(f"Untested API version: {api_version}")

        # Validate minimum ZBGym version
        min_version = plugin_info.get("minimum-zbgym-version", "1.0.0")
        if min_version and not self._is_valid_version(min_version):
            result.add_warning(f"Unusual minimum version format: {min_version}")

        result.add_info("api_version", api_version)
        result.add_info("min_zbgym_version", min_version)

        return result

    def _validate_entry_point(self, plugin_dir: Path) -> ValidationResult:
        """Validate plugin entry point."""
        result = ValidationResult(name="entry_point", is_valid=True)

        manifest_path = plugin_dir / "plugin.toml"
        if not manifest_path.exists():
            result.add_error("Missing plugin.toml")
            return result

        try:
            with open(manifest_path) as f:
                manifest = toml.load(f)
        except Exception:
            result.add_error("Failed to parse plugin.toml")
            return result

        plugin_info = manifest.get("plugin", {})
        entry_point = plugin_info.get("entry-point", "plugin.py")

        entry_path = plugin_dir / entry_point
        if not entry_path.exists():
            result.add_error(f"Entry point not found: {entry_point}")
            return result

        # Check for required class or function
        try:
            import ast

            code = entry_path.read_text()
            tree = ast.parse(code)

            has_plugin_class = False
            has_create_function = False

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "Plugin":
                    has_plugin_class = True
                elif isinstance(node, ast.FunctionDef) and node.name == "create_plugin":
                    has_create_function = True

            if not has_plugin_class and not has_create_function:
                result.add_error(
                    "Plugin must define 'Plugin' class or 'create_plugin' function"
                )

        except SyntaxError as e:
            result.add_error(f"Entry point has syntax error: {e}")

        result.add_info("entry_point", entry_point)
        result.add_info("has_plugin_class", has_plugin_class)
        result.add_info("has_create_function", has_create_function)

        return result

    def _validate_documentation(self, plugin_dir: Path) -> ValidationResult:
        """Validate documentation."""
        result = ValidationResult(name="documentation", is_valid=True)

        # Check README
        readme = plugin_dir / "README.md"
        if not readme.exists():
            result.add_warning("Missing README.md")

        # Check for tests
        tests_dir = plugin_dir / "tests"
        if not tests_dir.exists():
            result.add_warning("No tests directory found")

        return result

    def _validate_structure(self, plugin_dir: Path) -> ValidationResult:
        """Validate directory structure."""
        result = ValidationResult(name="structure", is_valid=True)

        # Check for common patterns that might indicate issues
        src_dir = plugin_dir / "src"
        if src_dir.exists():
            result.add_info("has_src_directory", True)

        # Check for __init__.py in expected locations
        init_files = list(plugin_dir.rglob("__init__.py"))
        result.add_info("init_files", len(init_files))

        return result

    def _is_valid_version(self, version: str) -> bool:
        """Check if version string is valid."""
        parts = version.split(".")
        if len(parts) < 2 or len(parts) > 3:
            return False

        try:
            for part in parts:
                # Remove any suffix like "alpha", "beta", etc.
                clean = "".join(c for c in part if c.isdigit())
                if clean:
                    int(clean)
            return True
        except ValueError:
            return False

    def print_result(self, result: ValidationResult) -> None:
        """Print validation result."""
        print("\n" + "=" * 60)
        print(f"Plugin Validation: {result.name}")
        print("=" * 60)

        if result.is_valid:
            print("✅ Validation PASSED")
        else:
            print("❌ Validation FAILED")

        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  ❌ {error}")

        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  ⚠️  {warning}")

        if result.info:
            print("\nInfo:")
            for key, value in result.info.items():
                print(f"  {key}: {value}")

        print("=" * 60)


def validate_plugin(plugin_dir: Path | str) -> ValidationResult:
    """Quick plugin validation."""
    validator = PluginValidator()
    result = validator.validate(plugin_dir)
    validator.print_result(result)
    return result
