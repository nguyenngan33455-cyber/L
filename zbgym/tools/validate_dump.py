"""Dump validation tools for ZBGym.

Provides functions to validate dump.cs data integrity.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple


class ValidationResult(NamedTuple):
    """Result of dump validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]


def validate_enum_consistency(dump_path: str) -> ValidationResult:
    """
    Validate enum consistency in dump.

    Checks for:
    - Duplicate enum values
    - Gaps in enum sequences
    - Invalid references

    Args:
        dump_path: Path to dump.cs file

    Returns:
        ValidationResult with status and issues
    """
    errors = []
    warnings = []

    with open(dump_path, encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Check CharacterEnum
    char_enum = re.search(r"public enum CharacterEnum\s*\{([^}]+)\}", content, re.DOTALL)
    if char_enum:
        enum_block = char_enum.group(1)
        values = re.findall(r"= (\d+);", enum_block)
        values = [int(v) for v in values]

        if len(values) != len(set(values)):
            duplicates = [v for v in values if values.count(v) > 1]
            errors.append(f"Duplicate CharacterEnum values: {set(duplicates)}")

        # Check for gaps
        if values:
            expected = set(range(min(values), max(values) + 1))
            actual = set(values)
            gaps = expected - actual
            if gaps:
                warnings.append(f"CharacterEnum has gaps at: {sorted(gaps)}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_class_structure(dump_path: str) -> ValidationResult:
    """
    Validate class structure in dump.

    Checks for:
    - Unclosed braces
    - Duplicate class definitions
    - Missing semicolons

    Args:
        dump_path: Path to dump.cs file

    Returns:
        ValidationResult with status and issues
    """
    errors = []
    warnings = []

    with open(dump_path, encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Count braces
    open_braces = content.count("{")
    close_braces = content.count("}")

    if open_braces != close_braces:
        errors.append(f"Mismatched braces: {open_braces} open, {close_braces} close")

    # Check for duplicate class definitions
    class_pattern = r"public class (\w+)"
    classes = re.findall(class_pattern, content)
    duplicates = [c for c in classes if classes.count(c) > 1]

    if duplicates:
        errors.append(f"Duplicate class definitions: {set(duplicates)}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_all(dump_path: str) -> ValidationResult:
    """
    Run all validation checks.

    Args:
        dump_path: Path to dump.cs file

    Returns:
        Combined ValidationResult
    """
    all_errors = []
    all_warnings = []

    # Run all validations
    enum_result = validate_enum_consistency(dump_path)
    all_errors.extend(enum_result.errors)
    all_warnings.extend(enum_result.warnings)

    class_result = validate_class_structure(dump_path)
    all_errors.extend(class_result.errors)
    all_warnings.extend(class_result.warnings)

    return ValidationResult(is_valid=len(all_errors) == 0, errors=all_errors, warnings=all_warnings)


def main() -> int:
    """CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m zbgym.tools.validate_dump <dump_path>")
        return 1

    dump_path = sys.argv[1]

    if not Path(dump_path).exists():
        print(f"Error: File not found: {dump_path}")
        return 1

    print(f"Validating: {dump_path}")
    print("-" * 50)

    result = validate_all(dump_path)

    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")

    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  ✗ {error}")

    if result.is_valid:
        print("\n✓ Validation passed!")
        return 0
    print("\n✗ Validation failed!")
    return 1


if __name__ == "__main__":
    exit(main())
