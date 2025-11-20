"""
Run Legislative Mapper from Configuration File

Reads mapper_config.yaml and maps all defined acts and regulations.
Automatically organizes files into:
  - Acts → data/raw/acts/
  - Regulations → data/raw/regulations/

Usage:
    python3 run_mapper_from_config.py
    python3 run_mapper_from_config.py --config custom_config.yaml
    python3 run_mapper_from_config.py --force  # Re-download existing files
"""

import sys
import yaml
import argparse
from pathlib import Path
from datetime import datetime
from run_mapper import LegislativeMapper, ACT_SLUG_MAP


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    path = Path(config_path)

    if not path.exists():
        print(f"❌ Config file not found: {config_path}")
        print("\nCreate mapper_config.yaml with this structure:")
        print("""
acts:
  - "Bank Act"

act_slugs:
  - "B-1.01"

regulation_slugs:
  - "SOR-2021-181"
""")
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config or {}


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Run Legislative Mapper from configuration file"
    )

    parser.add_argument(
        "--config",
        default="mapper_config.yaml",
        help="Path to config file (default: mapper_config.yaml)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download existing files"
    )

    args = parser.parse_args()

    # Load configuration
    print(f"📋 Loading configuration from: {args.config}")
    config = load_config(args.config)

    # Extract lists
    acts = config.get("acts", [])
    act_slugs = config.get("act_slugs", [])
    regulation_slugs = config.get("regulation_slugs", [])

    # Count total items
    total = len(acts) + len(act_slugs) + len(regulation_slugs)

    if total == 0:
        print("\n⚠️  No acts or regulations defined in config file")
        print(f"   Edit {args.config} to add slugs")
        sys.exit(0)

    print(f"\n{'='*60}")
    print("LEGISLATIVE MAPPER - CONFIG MODE")
    print(f"{'='*60}")
    print(f"Acts (by name): {len(acts)}")
    print(f"Acts (by slug): {len(act_slugs)}")
    print(f"Regulations: {len(regulation_slugs)}")
    print(f"Total items: {total}")
    print(f"Force re-download: {args.force}")
    print(f"{'='*60}\n")

    # Initialize mapper
    mapper = LegislativeMapper(output_dir="data/raw", force=args.force)

    start_time = datetime.now()

    # Map acts by name
    if acts:
        print(f"\n📚 Mapping {len(acts)} acts by name...\n")
        for act_name in acts:
            if act_name in ACT_SLUG_MAP:
                slug = ACT_SLUG_MAP[act_name]
                mapper.map_act(slug)
            else:
                print(f"\n⚠️  Unknown act name: {act_name}")
                print(f"   Known acts: {', '.join(ACT_SLUG_MAP.keys())}")
                print(f"   Tip: Use act_slugs instead")

    # Map acts by slug
    if act_slugs:
        print(f"\n📚 Mapping {len(act_slugs)} acts by slug...\n")
        for slug in act_slugs:
            mapper.map_act(slug)

    # Map regulations
    if regulation_slugs:
        print(f"\n📜 Mapping {len(regulation_slugs)} regulations...\n")
        for slug in regulation_slugs:
            mapper.map_regulation(slug)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Finalize
    mapper.finalize()

    print(f"⏱️  Total time: {duration:.2f}s\n")

    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Validate manifest:")
    print("   python3 validate_manifest.py data/raw/manifest.yaml")
    print()
    print("2. Batch ingest:")
    print("   python3 batch_ingest.py data/raw/manifest.yaml")
    print()
    print("3. Add more slugs:")
    print(f"   Edit {args.config} and run this script again")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
