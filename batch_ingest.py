"""
Batch Ingestion Script

Processes all documents from a manifest file through the ingestion pipeline.
Handles dependency ordering (parent acts before regulations).

Usage:
    python3 batch_ingest.py data/raw/manifest.yaml [--skip-validation] [--continue-on-error]

Examples:
    python3 batch_ingest.py data/raw/manifest.yaml
    python3 batch_ingest.py data/raw/manifest.yaml --skip-validation
    python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error
"""

import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from ingestion.pipeline import IngestionPipeline
from validate_manifest import ManifestValidator


class BatchIngester:
    """Batch processes documents from a manifest."""

    # Category processing order (parent acts first, then regulations, etc.)
    CATEGORY_ORDER = {
        "act": 1,
        "regulation": 2,
        "guidance": 3,
        "policy": 4,
    }

    def __init__(self, manifest_path: str, continue_on_error: bool = False):
        """
        Initialize batch ingester.

        Args:
            manifest_path: Path to manifest.yaml file
            continue_on_error: If True, continue processing even if a document fails
        """
        self.manifest_path = Path(manifest_path)
        self.manifest_dir = self.manifest_path.parent
        self.continue_on_error = continue_on_error
        self.manifest_data = None
        self.results: List[Dict] = []
        self.errors: List[Dict] = []

        # Initialize pipeline
        self.pipeline = IngestionPipeline(
            bronze_path="storage/bronze",
            silver_path="storage/silver",
        )

    def load_manifest(self) -> bool:
        """Load manifest file."""
        if not self.manifest_path.exists():
            print(f"❌ Manifest file not found: {self.manifest_path}")
            return False

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self.manifest_data = yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            print(f"❌ YAML parsing error: {e}")
            return False

    def sort_documents(self) -> List[Dict]:
        """
        Sort documents by dependency order.

        Acts first, then regulations, then guidance, then policies.
        This ensures parent documents are processed before their children.
        """
        documents = self.manifest_data.get("documents", [])

        def sort_key(doc):
            category = doc.get("category", "unknown")
            return self.CATEGORY_ORDER.get(category, 999)

        return sorted(documents, key=sort_key)

    def process_document(self, doc: Dict, doc_num: int, total: int) -> bool:
        """
        Process a single document from the manifest.

        Args:
            doc: Document metadata from manifest
            doc_num: Document number (for display)
            total: Total number of documents

        Returns:
            True if successful, False otherwise
        """
        filename = doc.get("filename", "unknown")
        category = doc.get("category")
        title = doc.get("title", filename)

        print("\n" + "=" * 60)
        print(f"PROCESSING DOCUMENT {doc_num}/{total}")
        print("=" * 60)
        print(f"File: {filename}")
        print(f"Category: {category}")
        print(f"Title: {title}")

        # Check if file exists (look in category subdirectory)
        file_found = False

        # Try category directory first
        if category:
            file_path = self.manifest_dir / category / filename
            if file_path.exists():
                file_found = True
            else:
                # Try plural form (acts, regulations, guidance -> remains guidance, policies)
                plural = f"{category}s" if category != "guidance" else category
                file_path_plural = self.manifest_dir / plural / filename
                if file_path_plural.exists():
                    file_found = True
                    file_path = file_path_plural

                # For guidance documents, check regulator subdirectory
                if not file_found and category == "guidance" and "regulator" in doc:
                    regulator = doc["regulator"].lower()
                    file_path_regulator = self.manifest_dir / category / regulator / filename
                    if file_path_regulator.exists():
                        file_found = True
                        file_path = file_path_regulator

        # Fallback to manifest directory root
        if not file_found:
            file_path_root = self.manifest_dir / filename
            if file_path_root.exists():
                file_found = True
                file_path = file_path_root

        if not file_found:
            expected_path = f"{category}/ or {category}s/" if category else ""
            error_msg = f"File not found: {filename} (expected in {expected_path})"
            print(f"❌ {error_msg}")
            self.errors.append({
                "filename": filename,
                "error": error_msg,
                "doc_num": doc_num,
            })
            return False

        # Extract metadata
        document_type = doc.get("document_type", self._infer_document_type(category, title))
        jurisdiction = doc.get("jurisdiction", "unknown")
        is_bilingual = doc.get("bilingual", False)

        # Category-specific parameters
        regulator = doc.get("regulator")
        parent_act = doc.get("parent_act")
        company_id = doc.get("company_id")

        # Generate document_id from filename (consistent with how Bronze folders are created)
        document_id = Path(filename).stem.lower().replace(" ", "_").replace(",_", "_").replace("_-_", "_")

        # Check if Bronze already exists
        bronze_file = self._find_bronze_file(filename, category, regulator, company_id)

        if bronze_file:
            print(f"📦 Found existing Bronze: {bronze_file}")
            print("   → Using Bronze→Silver flow (skipping PDF extraction)")
            input_path = bronze_file
        else:
            print(f"📄 No Bronze found, processing PDF: {file_path}")
            print("   → Using PDF→Bronze→Silver flow")
            input_path = str(file_path)

        try:
            # Process through pipeline (handles both PDF and Bronze .txt)
            result = self.pipeline.process_document(
                pdf_path=input_path,  # Can be PDF or Bronze .txt
                document_id=document_id,  # CRITICAL: Pass document_id explicitly
                document_type=document_type,
                jurisdiction=jurisdiction,
                is_bilingual=is_bilingual if not bronze_file else False,  # Bronze already filtered
                manual_category=category,
                regulator=regulator,
                parent_act=parent_act,
                company_id=company_id,
            )

            # Store result
            self.results.append({
                "filename": filename,
                "title": title,
                "category": category,
                "document_id": result["document_id"],
                "sections_count": result["sections_count"],
                "needs_ocr": result["needs_ocr"],
                "success": True,
            })

            print(f"\n✅ Successfully processed: {filename}")
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Failed to process {filename}: {error_msg}")

            self.errors.append({
                "filename": filename,
                "error": error_msg,
                "doc_num": doc_num,
            })

            return False

    def _find_bronze_file(self, filename: str, category: str, regulator: str = None, company_id: str = None) -> str:
        """
        Check if Bronze file already exists for this document.

        Args:
            filename: Original PDF filename
            category: Document category (act, regulation, guidance, policy)
            regulator: Regulator code (for guidance)
            company_id: Company ID (for policies)

        Returns:
            Path to Bronze raw_text.txt if found, None otherwise
        """
        bronze_base = Path("storage/bronze")

        # Construct expected document ID from filename
        # Remove extension, lowercase, replace spaces with underscores
        doc_id = Path(filename).stem.lower().replace(" ", "_")

        # Also try with commas normalized
        doc_id_normalized = doc_id.replace(",_", "_").replace("_-_", "_")

        # Map category to plural form for storage
        category_plural = {
            "act": "acts",
            "regulation": "regulations",
            "guidance": "guidance",
            "policy": "company_policies"
        }.get(category, category)

        # Build multiple possible paths to check
        possible_paths = []

        if category == "guidance" and regulator:
            # guidance/{regulator}/{doc_id}/raw_text.txt
            possible_paths.append(bronze_base / category_plural / regulator.lower() / doc_id / "raw_text.txt")
            possible_paths.append(bronze_base / category_plural / regulator.lower() / doc_id_normalized / "raw_text.txt")
        elif category == "policy" and company_id:
            # company_policies/{company_id}/{doc_id}/raw_text.txt
            possible_paths.append(bronze_base / category_plural / company_id.lower() / doc_id / "raw_text.txt")
            possible_paths.append(bronze_base / category_plural / company_id.lower() / doc_id_normalized / "raw_text.txt")
        else:
            # acts/{doc_id}/raw_text.txt or regulations/{doc_id}/raw_text.txt
            possible_paths.append(bronze_base / category_plural / doc_id / "raw_text.txt")
            possible_paths.append(bronze_base / category_plural / doc_id_normalized / "raw_text.txt")

        # Check all possible paths
        for bronze_path in possible_paths:
            if bronze_path.exists():
                return str(bronze_path)

        # No Bronze file found - will trigger PDF extraction
        # (Fuzzy matching disabled to prevent incorrect matches)
        return None


    def _infer_document_type(self, category: str, title: str) -> str:
        """Infer document type from category and title."""
        if category == "act":
            return "Act"
        elif category == "regulation":
            return "Regulation"
        elif category == "guidance":
            return "Guideline"
        elif category == "policy":
            return "Policy"
        else:
            return "Unknown"

    def process_all(self) -> bool:
        """Process all documents from manifest."""
        if not self.load_manifest():
            return False

        documents = self.sort_documents()
        total = len(documents)

        print("\n" + "=" * 60)
        print("BATCH INGESTION STARTING")
        print("=" * 60)
        print(f"Manifest: {self.manifest_path}")
        print(f"Total documents: {total}")
        print(f"Continue on error: {self.continue_on_error}")

        # Summary by category
        categories = {}
        for doc in documents:
            cat = doc.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        print("\nProcessing order:")
        for cat in ["act", "regulation", "guidance", "policy"]:
            if cat in categories:
                print(f"  {categories[cat]:2d} {cat}(s)")

        print("=" * 60)

        # Process each document
        start_time = datetime.now()

        for i, doc in enumerate(documents, 1):
            success = self.process_document(doc, i, total)

            if not success and not self.continue_on_error:
                print("\n❌ Stopping due to error (use --continue-on-error to skip failures)")
                break

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Print summary
        self._print_summary(duration)

        return len(self.errors) == 0

    def _print_summary(self, duration: float):
        """Print processing summary."""
        print("\n" + "=" * 60)
        print("BATCH INGESTION SUMMARY")
        print("=" * 60)

        successful = len(self.results)
        failed = len(self.errors)
        total = successful + failed

        print(f"\nTotal documents: {total}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Duration: {duration:.2f}s")

        if successful > 0:
            print(f"   Average: {duration/successful:.2f}s per document")

        # Breakdown by category
        if self.results:
            print("\nSuccessful by category:")
            categories = {}
            for result in self.results:
                cat = result["category"]
                categories[cat] = categories.get(cat, 0) + 1

            for cat in sorted(categories.keys()):
                print(f"  • {cat}: {categories[cat]}")

        # List errors
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  • {error['filename']}: {error['error']}")

        # Total sections extracted
        if self.results:
            total_sections = sum(r["sections_count"] for r in self.results)
            print(f"\nTotal sections extracted: {total_sections:,}")

            # OCR stats
            ocr_count = sum(1 for r in self.results if r["needs_ocr"])
            if ocr_count > 0:
                print(f"Documents requiring OCR: {ocr_count}")

        print("=" * 60)


def main():
    """Main batch ingestion function."""
    parser = argparse.ArgumentParser(
        description="Batch process documents from manifest file"
    )
    parser.add_argument("manifest", help="Path to manifest.yaml file")
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip manifest validation step"
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing even if a document fails"
    )

    args = parser.parse_args()

    # Validate manifest first (unless skipped)
    if not args.skip_validation:
        print("🔍 Validating manifest...\n")
        validator = ManifestValidator(args.manifest)
        if not validator.validate():
            print("\n❌ Manifest validation failed. Fix errors before ingestion.")
            print("   (Use --skip-validation to bypass this check)")
            sys.exit(1)
        print("\n✅ Manifest validation passed!\n")

    # Process documents
    ingester = BatchIngester(args.manifest, continue_on_error=args.continue_on_error)
    success = ingester.process_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()