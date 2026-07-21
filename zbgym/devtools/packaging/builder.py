"""Plugin packaging tools for ZBGym."""

from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import toml

from zbgym.plugin_sdk.base import PluginMetadata


@dataclass
class PackageInfo:
    """Information about a plugin package."""

    name: str
    version: str
    author: str
    description: str
    files: list[str]
    size_bytes: int
    checksum: str
    created_at: str = ""


class PluginBuilder:
    """
    Build and package ZBGym plugins.

    Creates distributable plugin archives.
    """

    def __init__(self, plugin_dir: Path | str) -> None:
        """
        Initialize the builder.

        Args:
            plugin_dir: Path to plugin directory
        """
        self._plugin_dir = Path(plugin_dir)
        self._manifest_path = self._plugin_dir / "plugin.toml"
        self._output_dir = Path("./dist")

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the plugin structure.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check plugin directory exists
        if not self._plugin_dir.exists():
            errors.append(f"Plugin directory does not exist: {self._plugin_dir}")
            return False, errors

        # Check manifest exists
        if not self._manifest_path.exists():
            errors.append("Missing plugin.toml")
            return False, errors

        # Parse manifest
        try:
            with open(self._manifest_path) as f:
                manifest = toml.load(f)
        except Exception as e:
            errors.append(f"Failed to parse plugin.toml: {e}")
            return False, errors

        plugin_info = manifest.get("plugin", {})

        # Check required fields
        required_fields = ["name", "version"]
        for field in required_fields:
            if not plugin_info.get(field):
                errors.append(f"Missing required field: {field}")

        # Check entry point exists
        entry_point = plugin_info.get("entry-point", "plugin.py")
        entry_path = self._plugin_dir / entry_point
        if not entry_path.exists():
            errors.append(f"Entry point not found: {entry_point}")

        # Check for documentation
        readme = self._plugin_dir / "README.md"
        if not readme.exists():
            errors.append("Missing README.md (recommended)")

        return len(errors) == 0, errors

    def build(
        self,
        output_name: str | None = None,
        compression: str = "gz",
    ) -> PackageInfo | None:
        """
        Build the plugin package.

        Args:
            output_name: Output filename (without extension)
            compression: Compression type ('gz', 'xz', 'bz2')

        Returns:
            PackageInfo if successful, None otherwise
        """
        valid, errors = self.validate()
        if not valid:
            print("Validation failed:")
            for error in errors:
                print(f"  - {error}")
            return None

        # Parse manifest
        with open(self._manifest_path) as f:
            manifest = toml.load(f)

        plugin_info = manifest.get("plugin", {})
        name = plugin_info.get("name", self._plugin_dir.name)
        version = plugin_info.get("version", "1.0.0")

        if output_name is None:
            output_name = f"{name}-{version}"

        # Create output directory
        self._output_dir.mkdir(parents=True, exist_ok=True)

        # Create tarball
        archive_path = self._output_dir / f"{output_name}.tar.gz"

        files = []
        size_total = 0

        with tarfile.open(archive_path, f"w:{compression}") as tar:
            for file_path in self._plugin_dir.rglob("*"):
                if file_path.is_file() and not self._should_exclude(file_path):
                    # Calculate size
                    size = file_path.stat().st_size
                    size_total += size
                    files.append(str(file_path.relative_to(self._plugin_dir)))

                    # Add to archive
                    tar.add(file_path, arcname=file_path.relative_to(self._plugin_dir.parent))

        # Calculate checksum
        checksum = self._calculate_checksum(archive_path)

        # Create package info
        info = PackageInfo(
            name=name,
            version=version,
            author=plugin_info.get("author", ""),
            description=plugin_info.get("description", ""),
            files=files,
            size_bytes=size_total,
            checksum=checksum,
        )

        # Save package info
        info_path = self._output_dir / f"{output_name}.info.json"
        with open(info_path, "w") as f:
            json.dump(
                {
                    "name": info.name,
                    "version": info.version,
                    "author": info.author,
                    "description": info.description,
                    "files": info.files,
                    "size_bytes": info.size_bytes,
                    "checksum": info.checksum,
                },
                f,
                indent=2,
            )

        print(f"Built: {archive_path}")
        print(f"Size: {size_total / 1024:.1f} KB")
        print(f"Files: {len(files)}")
        print(f"Checksum: {checksum[:16]}...")

        return info

    def _should_exclude(self, path: Path) -> bool:
        """Check if a file should be excluded from the package."""
        exclude_patterns = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".git",
            ".pytest_cache",
            "*.log",
            ".DS_Store",
            "node_modules",
        ]

        path_str = str(path)
        for pattern in exclude_patterns:
            if pattern in path_str:
                return True
            if path.suffix in (".pyc", ".pyo"):
                return True

        return False

    def _calculate_checksum(self, path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def create_template(
        self,
        name: str,
        output_dir: Path | str | None = None,
    ) -> Path:
        """
        Create a plugin template.

        Args:
            name: Plugin name
            output_dir: Output directory

        Returns:
            Path to created template
        """
        if output_dir is None:
            output_dir = Path("./plugins")

        output_dir = Path(output_dir)
        plugin_dir = output_dir / name

        if plugin_dir.exists():
            raise FileExistsError(f"Plugin directory already exists: {plugin_dir}")

        plugin_dir.mkdir(parents=True)

        # Create plugin.toml
        manifest = f"""[plugin]
name = "{name}"
version = "1.0.0"
author = "Your Name <your@email.com>"
description = "A brief description of {name}"

minimum-zbgym-version = "1.0.0"
api-version = "1.0"

dependencies = []
optional-dependencies = []
supported-games = []
capabilities = []

entry-point = "plugin.py"
"""
        (plugin_dir / "plugin.toml").write_text(manifest)

        # Create plugin.py
        plugin_code = f'''"""Plugin: {name}"""

from zbgym.plugin_sdk.base import PluginBase, PluginMetadata


class Plugin(PluginBase):
    """Plugin {name}."""

    def __init__(self, metadata: PluginMetadata) -> None:
        """Initialize the plugin."""
        super().__init__(metadata)

    def initialize(self) -> None:
        """Initialize the plugin."""
        self._logger.info(f"Initializing {{self.name}} v{{self.version}}")

    def load(self) -> None:
        """Load the plugin."""
        self._logger.info(f"Loading {{self.name}}")

    def enable(self) -> None:
        """Enable the plugin."""
        self._logger.info(f"Enabling {{self.name}}")

    def disable(self) -> None:
        """Disable the plugin."""
        self._logger.info(f"Disabling {{self.name}}")

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        self._logger.info(f"Shutting down {{self.name}}")

    def health_check(self) -> bool:
        """Check plugin health."""
        return True


def create_plugin(metadata: PluginMetadata) -> Plugin:
    """Create the plugin instance."""
    return Plugin(metadata)
'''
        (plugin_dir / "plugin.py").write_text(plugin_code)

        # Create README.md
        readme = f"""# {name}

A ZBGym plugin.

## Installation

1. Copy this directory to your `plugins/` folder
2. Restart ZBGym

## Configuration

Edit `plugin.toml` to configure the plugin.

## Usage

Describe how to use this plugin.

## License

MIT
"""
        (plugin_dir / "README.md").write_text(readme)

        # Create tests directory
        tests_dir = plugin_dir / "tests"
        tests_dir.mkdir()

        (tests_dir / "__init__.py").write_text('"""Tests for the plugin."""\n')

        print(f"Created plugin template: {plugin_dir}")
        return plugin_dir


class PackageVerifier:
    """Verify plugin packages."""

    @staticmethod
    def verify(path: Path | str) -> tuple[bool, str | None]:
        """
        Verify a plugin package.

        Args:
            path: Path to package

        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(path)

        if not path.exists():
            return False, f"Package not found: {path}"

        try:
            with tarfile.open(path, "r:*") as tar:
                # Check for manifest
                members = tar.getnames()
                if "plugin.toml" not in members:
                    return False, "Missing plugin.toml in package"

                # Check for entry point
                manifest_data = tar.extractfile("plugin.toml")
                if manifest_data:
                    manifest = toml.loads(manifest_data.read().decode())
                    plugin_info = manifest.get("plugin", {})
                    entry_point = plugin_info.get("entry-point", "plugin.py")

                    if entry_point not in members:
                        return False, f"Entry point not found: {entry_point}"

            return True, None

        except Exception as e:
            return False, f"Failed to verify package: {e}"
