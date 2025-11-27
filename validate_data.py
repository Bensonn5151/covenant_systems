#!/usr/bin/env python3
"""
Data quality validation for Covenant Systems.
Run before GraphRAG work to ensure data integrity.

Usage:
    python3 validate_data.py              # Validate all layers
    python3 validate_data.py --bronze     # Bronze only
    python3 validate_data.py --silver     # Silver only
    python3 validate_data.py --gold       # Gold only
    python3 validate_data.py --verbose    # Show all errors
"""
import json
import argparse
import sys
from pathlib import Path
from typing import Tuple

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ingestion.schemas import BronzeMetadata, SilverSection, GoldSection, GoldMetadata

STORAGE = Path("storage")


def validate_bronze(verbose: bool = False) -> Tuple[int, int]:
    """Validate Bronze layer metadata against schema"""
    passed, failed = 0, 0
    errors = []

    for meta_file in STORAGE.glob("bronze/**/metadata.json"):
        try:
            data = json.loads(meta_file.read_text())
            BronzeMetadata(**data)
            passed += 1
        except Exception as e:
            failed += 1
            errors.append(f"  {meta_file.relative_to(STORAGE)}: {e}")

    if verbose and errors:
        print("\nBronze Errors:")
        for err in errors[:10]:  # Limit to first 10
            print(err)
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

    return passed, failed


def validate_silver(verbose: bool = False) -> Tuple[int, int]:
    """Validate Silver layer sections against schema"""
    passed, failed = 0, 0
    errors = []

    for sections_file in STORAGE.glob("silver/**/sections.json"):
        try:
            sections = json.loads(sections_file.read_text())
            for i, s in enumerate(sections):
                try:
                    SilverSection(**s)
                    passed += 1
                except Exception as e:
                    failed += 1
                    errors.append(f"  {sections_file.relative_to(STORAGE)}[{i}]: {e}")
        except json.JSONDecodeError as e:
            failed += 1
            errors.append(f"  {sections_file.relative_to(STORAGE)}: Invalid JSON - {e}")

    if verbose and errors:
        print("\nSilver Errors:")
        for err in errors[:10]:
            print(err)
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

    return passed, failed


def validate_gold(verbose: bool = False) -> Tuple[int, int]:
    """Validate Gold layer embeddings against schema"""
    passed, failed = 0, 0
    errors = []

    for gold_dir in STORAGE.glob("gold/*/"):
        if not gold_dir.is_dir():
            continue

        meta_file = gold_dir / "metadata.json"
        sections_file = gold_dir / "sections.json"

        # Validate metadata
        if meta_file.exists():
            try:
                GoldMetadata(**json.loads(meta_file.read_text()))
            except Exception as e:
                failed += 1
                errors.append(f"  {meta_file.relative_to(STORAGE)}: {e}")

        # Validate sections
        if sections_file.exists():
            try:
                sections = json.loads(sections_file.read_text())
                for i, s in enumerate(sections):
                    try:
                        GoldSection(**s)
                        passed += 1
                    except Exception as e:
                        failed += 1
                        errors.append(f"  {sections_file.relative_to(STORAGE)}[{i}]: {e}")
            except json.JSONDecodeError as e:
                failed += 1
                errors.append(f"  {sections_file.relative_to(STORAGE)}: Invalid JSON - {e}")

    if verbose and errors:
        print("\nGold Errors:")
        for err in errors[:10]:
            print(err)
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

    return passed, failed


def validate_silver_gold_mapping() -> bool:
    """
    Ensure 1:1 mapping between Silver and Gold sections (excluding TOC).
    As per CLAUDE.md Section 6.6: "Every Silver section must produce exactly one Gold vector."
    """
    silver_count = 0
    gold_count = 0

    # Count Silver sections (excluding TOC)
    for f in STORAGE.glob("silver/**/sections.json"):
        try:
            sections = json.loads(f.read_text())
            non_toc = [s for s in sections if not s.get('metadata', {}).get('is_toc', False)]
            silver_count += len(non_toc)
        except:
            pass

    # Count Gold sections
    for f in STORAGE.glob("gold/*/sections.json"):
        try:
            sections = json.loads(f.read_text())
            gold_count += len(sections)
        except:
            pass

    if silver_count != gold_count:
        print(f"FAIL: Silver-Gold mapping mismatch")
        print(f"      Silver (non-TOC): {silver_count}")
        print(f"      Gold:             {gold_count}")
        print(f"      Difference:       {abs(silver_count - gold_count)}")
        return False

    print(f"PASS: Silver-Gold 1:1 mapping ({silver_count} sections)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Validate Covenant Systems data layers")
    parser.add_argument('--bronze', action='store_true', help='Validate Bronze layer only')
    parser.add_argument('--silver', action='store_true', help='Validate Silver layer only')
    parser.add_argument('--gold', action='store_true', help='Validate Gold layer only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed errors')
    args = parser.parse_args()

    all_layers = not (args.bronze or args.silver or args.gold)
    total_passed, total_failed = 0, 0

    print("=" * 60)
    print("Covenant Systems Data Validation")
    print("=" * 60)

    if args.bronze or all_layers:
        p, f = validate_bronze(args.verbose)
        status = "PASS" if f == 0 else "FAIL"
        print(f"\nBronze: {p} passed, {f} failed [{status}]")
        total_passed += p
        total_failed += f

    if args.silver or all_layers:
        p, f = validate_silver(args.verbose)
        status = "PASS" if f == 0 else "FAIL"
        print(f"\nSilver: {p} passed, {f} failed [{status}]")
        total_passed += p
        total_failed += f

    if args.gold or all_layers:
        p, f = validate_gold(args.verbose)
        status = "PASS" if f == 0 else "FAIL"
        print(f"\nGold:   {p} passed, {f} failed [{status}]")
        total_passed += p
        total_failed += f

    if all_layers:
        print("\n" + "-" * 60)
        validate_silver_gold_mapping()

    print("\n" + "=" * 60)
    overall = "PASS" if total_failed == 0 else "FAIL"
    print(f"TOTAL: {total_passed} passed, {total_failed} failed [{overall}]")
    print("=" * 60)

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    exit(main())
