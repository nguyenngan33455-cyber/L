#!/usr/bin/env python3
"""
Validate dump.cs for parsing.

Usage:
    python -m tools.validate_dump [dump_path]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from collections import Counter


def main():
    parser = argparse.ArgumentParser(
        description="Validate dump.cs for parsing"
    )
    parser.add_argument(
        "dump_path",
        nargs="?",
        default="dump/dump.cs",
        help="Path to dump.cs file (default: dump/dump.cs)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    dump_path = Path(args.dump_path)
    if not dump_path.exists():
        print(f"Error: dump.cs not found at {dump_path}")
        sys.exit(1)

    print(f"Validating {dump_path}...")

    with open(dump_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Statistics
    stats = {
        "total_size": len(content),
        "lines": content.count("\n"),
        "classes": len(re.findall(r"public (?:sealed |abstract |static )?class ", content)),
        "enums": len(re.findall(r"public enum ", content)),
        "structs": len(re.findall(r"public struct ", content)),
        "interfaces": len(re.findall(r"public interface ", content)),
        "namespaces": len(re.findall(r"namespace ", content)),
        "methods": len(re.findall(r"public .*?\([^)]*\)", content)),
        "fields": len(re.findall(r"public .+? .+?;", content)),
        "properties": len(re.findall(r"public .+? { (?:get|set)", content)),
    }

    # Find key enums
    key_enums = []
    for match in re.finditer(r"public enum (\w+)", content):
        enum_name = match.group(1)
        if any(keyword in enum_name.lower() for keyword in ["character", "weapon", "skill", "projectile", "item", "effect"]):
            key_enums.append(enum_name)

    # Find key classes
    key_classes = []
    for match in re.finditer(r"public (?:sealed |abstract |static )?class (\w+)", content):
        class_name = match.group(1)
        if any(keyword in class_name.lower() for keyword in ["config", "data", "stats", "character", "weapon", "skill", "projectile"]):
            key_classes.append(class_name)

    # Print report
    print("\n" + "=" * 60)
    print("DUMP.CS VALIDATION REPORT")
    print("=" * 60)

    print("\n=== Statistics ===")
    for key, value in stats.items():
        print(f"  {key}: {value:,}")

    print(f"\n=== Key Enums ({len(key_enums)}) ===")
    for enum_name in sorted(key_enums)[:20]:
        print(f"  - {enum_name}")
    if len(key_enums) > 20:
        print(f"  ... and {len(key_enums) - 20} more")

    print(f"\n=== Key Classes ({len(key_classes)}) ===")
    for class_name in sorted(key_classes)[:20]:
        print(f"  - {class_name}")
    if len(key_classes) > 20:
        print(f"  ... and {len(key_classes) - 20} more")

    # Check for CharacterEnum specifically
    char_enum_match = re.search(r"public enum CharacterEnum\s*\{([^}]+)\}", content, re.DOTALL)
    if char_enum_match:
        enum_block = char_enum_match.group(1)
        char_names = re.findall(r"public const CharacterEnum\s+(\w+)\s*=\s*(\d+);", enum_block)
        print(f"\n=== CharacterEnum ({len(char_names)} characters) ===")
        for name, value in sorted(char_names, key=lambda x: int(x[1]))[:15]:
            print(f"  {name} = {value}")
        if len(char_names) > 15:
            print(f"  ... and {len(char_names) - 15} more")
    else:
        print("\n!!! CharacterEnum not found !!!")

    # Validation checks
    print("\n=== Validation Checks ===")

    checks = [
        ("Has CharacterEnum", char_enum_match is not None),
        ("Has namespaces", stats["namespaces"] > 0),
        ("Has classes", stats["classes"] > 100),
        ("Has enums", stats["enums"] > 10),
        ("Reasonable size (>1MB)", stats["total_size"] > 1_000_000),
    ]

    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("Validation PASSED")
    else:
        print("Validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
