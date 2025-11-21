"""
Manifest Generator

Generates manifest.yaml from discovered documents.
Compatible with existing batch_ingest.py and build_kg_from_manifest.py.
"""

import yaml
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class ManifestGenerator:
    """Generates manifest.yaml from discovered legislation."""

    def __init__(self, output_path: str = "data/raw/manifest.yaml", merge: bool = True):
        """
        Initialize manifest generator.

        Args:
            output_path: Path to save manifest.yaml
            merge: If True, merge with existing manifest instead of overwriting
        """
        self.output_path = Path(output_path)
        self.merge = merge
        self.documents: List[Dict] = []

        # Load existing manifest if merge=True
        if self.merge and self.output_path.exists():
            self._load_existing_manifest()

    def _load_existing_manifest(self):
        """Load existing manifest and preserve entries."""
        try:
            with open(self.output_path, "r", encoding="utf-8") as f:
                existing = yaml.safe_load(f)

            if existing and "documents" in existing:
                self.documents = existing["documents"]
                print(f"  📋 Loaded existing manifest: {len(self.documents)} documents")

        except Exception as e:
            print(f"  ⚠️  Could not load existing manifest: {e}")

    def _document_exists(self, filename: str) -> bool:
        """Check if document already exists in manifest."""
        return any(doc.get("filename") == filename for doc in self.documents)

    def add_act(self, metadata: Dict, download_info: Dict):
        """
        Add Act to manifest (skip if already exists).

        Args:
            metadata: Metadata from MetadataParser.parse_act_page()
            download_info: Download info from Downloader.download()
        """
        # Check if already exists
        if self._document_exists(download_info["filename"]):
            print(f"  ⏩ Already in manifest: {download_info['filename']}")
            return

        doc = {
            "filename": download_info["filename"],
            "category": "act",
            "title": metadata["title"],
            "citation": metadata["citation"],
            "jurisdiction": "federal",  # All from laws-lois.justice.gc.ca are federal
        }

        # Add optional fields
        if metadata.get("current_to"):
            doc["current_to"] = metadata["current_to"]

        if metadata.get("last_amended"):
            doc["last_amended"] = metadata["last_amended"]

        if download_info.get("checksum"):
            doc["checksum"] = download_info["checksum"]

        if download_info.get("downloaded_at"):
            doc["downloaded_at"] = download_info["downloaded_at"]

        # Store related regulations for KG building
        if metadata.get("related_regulations"):
            doc["related_regulations"] = metadata["related_regulations"]

        self.documents.append(doc)

    def add_regulation(self, metadata: Dict, download_info: Dict):
        """
        Add Regulation to manifest (skip if already exists).

        Args:
            metadata: Metadata from MetadataParser.parse_regulation_page()
            download_info: Download info from Downloader.download()
        """
        # Check if already exists
        if self._document_exists(download_info["filename"]):
            print(f"  ⏩ Already in manifest: {download_info['filename']}")
            return

        doc = {
            "filename": download_info["filename"],
            "category": "regulation",
            "title": metadata["title"],
            "citation": metadata["citation"],
            "jurisdiction": "federal",
        }

        # Add parent act (enabling act)
        if metadata.get("enabling_acts") and len(metadata["enabling_acts"]) > 0:
            doc["parent_act"] = metadata["enabling_acts"][0]

        # Add optional fields
        if metadata.get("current_to"):
            doc["current_to"] = metadata["current_to"]

        if metadata.get("last_amended"):
            doc["last_amended"] = metadata["last_amended"]

        if download_info.get("checksum"):
            doc["checksum"] = download_info["checksum"]

        if download_info.get("downloaded_at"):
            doc["downloaded_at"] = download_info["downloaded_at"]

        self.documents.append(doc)

    def _create_backup(self):
        """Create timestamped backup of existing manifest."""
        if self.output_path.exists():
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = self.output_path.parent / f"manifest.backup.{timestamp}.yaml"

            import shutil
            shutil.copy2(self.output_path, backup_path)
            print(f"  💾 Backup created: {backup_path.name}")

            # Keep only last 10 backups
            backups = sorted(self.output_path.parent.glob("manifest.backup.*.yaml"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
                    print(f"  🗑️  Removed old backup: {old_backup.name}")

    def generate(self) -> bool:
        """
        Generate manifest.yaml file.

        Returns:
            True if successful, False otherwise
        """
        if not self.documents:
            print("  ⚠️  No documents to write to manifest")
            return False

        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create backup before writing
        self._create_backup()

        # Build manifest structure
        manifest = {
            "# Auto-generated by Legislative Mapper": None,
            "# Generated": datetime.utcnow().isoformat() + "Z",
            "# Source": "laws-lois.justice.gc.ca",
            "documents": self.documents,
        }

        # Write to YAML
        try:
            with open(self.output_path, "w", encoding="utf-8") as f:
                # Write header comments
                f.write("# Auto-generated by Legislative Mapper\n")
                f.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n")
                f.write("# Source: laws-lois.justice.gc.ca\n\n")

                # Write documents
                yaml.dump(
                    {"documents": self.documents},
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            print(f"\n✅ Manifest generated: {self.output_path}")
            print(f"   Documents: {len(self.documents)}")

            # Summary by category
            categories = {}
            for doc in self.documents:
                cat = doc.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1

            for cat in sorted(categories.keys()):
                print(f"   • {cat}: {categories[cat]}")

            return True

        except Exception as e:
            print(f"  ❌ Failed to write manifest: {e}")
            return False