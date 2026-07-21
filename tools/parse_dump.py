#!/usr/bin/env python3
"""
Parse dump.cs and generate Intermediate Representation.

Usage:
    python -m tools.parse_dump [dump_path] [--output OUTPUT_DIR]

Example:
    python -m tools.parse_dump dump/dump.cs --output zbgym/data
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zbgym.dump.compiler import Compiler


def main():
    parser = argparse.ArgumentParser(
        description="Parse dump.cs and generate Intermediate Representation"
    )
    parser.add_argument(
        "dump_path",
        nargs="?",
        default="dump/dump.cs",
        help="Path to dump.cs file (default: dump/dump.cs)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="zbgym/data",
        help="Output directory for JSON files (default: zbgym/data)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "ir"],
        default="json",
        help="Output format (default: json)",
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

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Parsing {dump_path}...")

    # Compile dump.cs to IR
    compiler = Compiler(str(dump_path))
    ir = compiler.compile()

    if args.format == "json":
        # Generate JSON databases
        compiler.generate_json_databases(output_dir)
        print(f"\nGenerated JSON databases in {output_dir}")

        # Also save raw IR
        ir_path = output_dir / "ir.json"
        with open(ir_path, "w") as f:
            json.dump(ir.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"Saved IR to {ir_path}")

    else:
        # Save raw IR
        ir_path = output_dir / "ir.json"
        with open(ir_path, "w") as f:
            json.dump(ir.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"Saved IR to {ir_path}")

    # Print summary
    print("\n=== Summary ===")
    print(f"Characters: {len(ir.characters)}")
    print(f"Weapons: {len(ir.weapons)}")
    print(f"Skills: {len(ir.skills)}")
    print(f"Projectiles: {len(ir.projectiles)}")
    print(f"Maps: {len(ir.maps)}")

    if args.verbose:
        print("\n=== Characters ===")
        for char_id, char in sorted(ir.characters.items()):
            print(f"  {char_id}: {char.name} (enum_id={char.enum_id})")


if __name__ == "__main__":
    main()
