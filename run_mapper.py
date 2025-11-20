"""
Legislative Mapper - Main CLI Tool

Automatically discovers and downloads Canadian federal legislation from laws-lois.justice.gc.ca.
Generates manifest.yaml for use with batch_ingest.py.

Usage:
    python3 run_mapper.py --acts "Bank Act" "PCMLTFA" "PIPEDA"
    python3 run_mapper.py --act-slugs "B-1.01" "P-24.501"
    python3 run_mapper.py --regulation-slugs "SOR-86-304" "SOR-2021-181"

Examples:
    # Map Bank Act and all its regulations
    python3 run_mapper.py --acts "Bank Act"

    # Map specific act by slug
    python3 run_mapper.py --act-slugs "B-1.01"

    # Map specific regulations
    python3 run_mapper.py --regulation-slugs "SOR-86-304"

    # Map multiple acts (will discover all related regulations)
    python3 run_mapper.py --acts "Bank Act" "PCMLTFA" "PIPEDA"
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

from ingestion.mapper import JusticeClient, MetadataParser, Downloader, ManifestGenerator


# Mapping of common act names to their slugs
ACT_SLUG_MAP = {
    "Bank Act": "B-1.01",
    "PCMLTFA": "P-24.501",
    "Proceeds of Crime (Money Laundering) and Terrorist Financing Act": "P-24.501",
    "PIPEDA": "P-8.6",
    "Personal Information Protection and Electronic Documents Act": "P-8.6",
    "Canada Labour Code": "L-2",
    "Access to Information Act": "A-1",
    "Privacy Act": "P-21",
}


class LegislativeMapper:
    """Main mapper orchestrator."""

    def __init__(self, output_dir: str = "data/raw", force: bool = False):
        """
        Initialize mapper.

        Args:
            output_dir: Output directory for PDFs and manifest
            force: If True, re-download existing files
        """
        self.output_dir = Path(output_dir)
        self.force = force

        # Initialize components
        self.client = JusticeClient()
        self.parser = MetadataParser()
        self.downloader = Downloader(output_dir=str(self.output_dir))
        self.manifest = ManifestGenerator(output_path=str(self.output_dir / "manifest.yaml"))

        self.stats = {
            "acts_processed": 0,
            "regulations_processed": 0,
            "downloads": 0,
            "skipped": 0,
            "errors": 0,
        }

    def map_act(self, act_slug: str) -> bool:
        """
        Map an Act and all its related regulations.

        Args:
            act_slug: Act identifier (e.g., "B-1.01")

        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'=' * 60}")
        print(f"MAPPING ACT: {act_slug}")
        print(f"{'=' * 60}")

        # Fetch Act page
        print(f"\n📄 Fetching Act page...")
        response = self.client.get_act_page(act_slug)

        if not response:
            print(f"  ❌ Failed to fetch Act page")
            self.stats["errors"] += 1
            return False

        # Parse metadata
        print(f"  🔍 Parsing metadata...")
        metadata = self.parser.parse_act_page(response.text)

        if not metadata.get("title"):
            print(f"  ❌ Failed to parse Act metadata")
            self.stats["errors"] += 1
            return False

        print(f"  ✅ Title: {metadata['title']}")
        print(f"  ✅ Citation: {metadata['citation']}")
        print(f"  ✅ Last Amended: {metadata.get('last_amended', 'N/A')}")

        # Download PDF if available
        if metadata.get("pdf_url"):
            filename = self.parser.sanitize_filename(metadata["title"], metadata["citation"])
            download_info = self.downloader.download(
                self.client,
                metadata["pdf_url"],
                filename,
                category="acts",
                force=self.force
            )

            if download_info:
                if download_info["status"] == "downloaded":
                    self.stats["downloads"] += 1
                elif download_info["status"] == "skipped":
                    self.stats["skipped"] += 1

                # Add to manifest
                self.manifest.add_act(metadata, download_info)
                self.stats["acts_processed"] += 1
            else:
                print(f"  ⚠️  Failed to download Act PDF")
                self.stats["errors"] += 1
        else:
            print(f"  ⚠️  No PDF URL found for Act")

        # Map related regulations
        if metadata.get("related_regulations"):
            print(f"\n📋 Found {len(metadata['related_regulations'])} related regulations")

            for i, reg_slug in enumerate(metadata["related_regulations"], 1):
                print(f"\n  [{i}/{len(metadata['related_regulations'])}] Mapping regulation: {reg_slug}")
                self.map_regulation(reg_slug, indent=True)

        return True

    def map_regulation(self, regulation_slug: str, indent: bool = False) -> bool:
        """
        Map a Regulation.

        Args:
            regulation_slug: Regulation identifier (e.g., "SOR-2021-181")
            indent: If True, indent output for nested display

        Returns:
            True if successful, False otherwise
        """
        prefix = "    " if indent else ""

        if not indent:
            print(f"\n{'=' * 60}")
            print(f"MAPPING REGULATION: {regulation_slug}")
            print(f"{'=' * 60}")

        # Fetch Regulation page
        print(f"{prefix}📄 Fetching Regulation page...")
        response = self.client.get_regulation_page(regulation_slug)

        if not response:
            print(f"{prefix}  ❌ Failed to fetch Regulation page (possibly repealed)")
            self.stats["errors"] += 1
            return False

        # Parse metadata
        print(f"{prefix}  🔍 Parsing metadata...")
        metadata = self.parser.parse_regulation_page(response.text)

        if not metadata.get("title"):
            print(f"{prefix}  ❌ Failed to parse Regulation metadata")
            self.stats["errors"] += 1
            return False

        print(f"{prefix}  ✅ Title: {metadata['title']}")
        print(f"{prefix}  ✅ Citation: {metadata['citation']}")
        if metadata.get("enabling_acts"):
            print(f"{prefix}  ✅ Enabling Act: {metadata['enabling_acts'][0]}")

        # Download PDF if available
        if metadata.get("pdf_url"):
            filename = self.parser.sanitize_filename(metadata["title"], metadata["citation"])
            download_info = self.downloader.download(
                self.client,
                metadata["pdf_url"],
                filename,
                category="regulations",
                force=self.force
            )

            if download_info:
                if download_info["status"] == "downloaded":
                    self.stats["downloads"] += 1
                elif download_info["status"] == "skipped":
                    self.stats["skipped"] += 1

                # Add to manifest
                self.manifest.add_regulation(metadata, download_info)
                self.stats["regulations_processed"] += 1
            else:
                print(f"{prefix}  ⚠️  Failed to download Regulation PDF")
                self.stats["errors"] += 1
        else:
            print(f"{prefix}  ⚠️  No PDF URL found for Regulation")

        return True

    def finalize(self):
        """Generate manifest and print summary."""
        print(f"\n{'=' * 60}")
        print("FINALIZING")
        print(f"{'=' * 60}")

        # Generate manifest
        self.manifest.generate()

        # Print statistics
        print(f"\n{'=' * 60}")
        print("MAPPING SUMMARY")
        print(f"{'=' * 60}")
        print(f"Acts processed: {self.stats['acts_processed']}")
        print(f"Regulations processed: {self.stats['regulations_processed']}")
        print(f"Total documents: {self.stats['acts_processed'] + self.stats['regulations_processed']}")
        print(f"New downloads: {self.stats['downloads']}")
        print(f"Skipped (existing): {self.stats['skipped']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"{'=' * 60}\n")

        # Close client
        self.client.close()


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Legislative Mapper - Automated legislation discovery and download"
    )

    # Input options
    parser.add_argument(
        "--acts",
        nargs="+",
        help='Act names (e.g., "Bank Act" "PCMLTFA")'
    )
    parser.add_argument(
        "--act-slugs",
        nargs="+",
        help='Act slugs (e.g., "B-1.01" "P-24.501")'
    )
    parser.add_argument(
        "--regulation-slugs",
        nargs="+",
        help='Regulation slugs (e.g., "SOR-86-304")'
    )

    # Options
    parser.add_argument(
        "--output",
        default="data/raw",
        help="Output directory (default: data/raw)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download existing files"
    )

    args = parser.parse_args()

    # Validate input
    if not (args.acts or args.act_slugs or args.regulation_slugs):
        parser.error("Must specify --acts, --act-slugs, or --regulation-slugs")

    # Initialize mapper
    mapper = LegislativeMapper(output_dir=args.output, force=args.force)

    start_time = datetime.now()

    # Map acts by name
    if args.acts:
        for act_name in args.acts:
            if act_name in ACT_SLUG_MAP:
                slug = ACT_SLUG_MAP[act_name]
                mapper.map_act(slug)
            else:
                print(f"\n⚠️  Unknown act name: {act_name}")
                print(f"   Known acts: {', '.join(ACT_SLUG_MAP.keys())}")

    # Map acts by slug
    if args.act_slugs:
        for slug in args.act_slugs:
            mapper.map_act(slug)

    # Map regulations by slug
    if args.regulation_slugs:
        for slug in args.regulation_slugs:
            mapper.map_regulation(slug)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Finalize
    mapper.finalize()

    print(f"⏱️  Total time: {duration:.2f}s\n")

    sys.exit(0)


if __name__ == "__main__":
    main()