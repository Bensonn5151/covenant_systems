"""
Manifest Validation Script

Validates the data/raw/manifest.yaml file before ingestion:
- Checks if all referenced PDF files exist
- Validates parent_act references
- Ensures required fields are present
- Checks for duplicate filenames
- Validates relationship integrity

Usage:
    python3 validate_manifest.py data/raw/manifest.yaml
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Set


class ManifestValidator:
    """Validates manifest structure and references."""

    def __init__(self, manifest_path: str):
        """
        Initialize validator.

        Args:
            manifest_path: Path to manifest.yaml file
        """
        self.manifest_path = Path(manifest_path)
        self.manifest_dir = self.manifest_path.parent
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.manifest_data = None

    def load_manifest(self) -> bool:
        """Load and parse manifest file."""
        if not self.manifest_path.exists():
            self.errors.append(f"Manifest file not found: {self.manifest_path}")
            return False

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self.manifest_data = yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"YAML parsing error: {e}")
            return False

    def validate_structure(self) -> bool:
        """Validate top-level manifest structure."""
        if not self.manifest_data:
            self.errors.append("Manifest is empty")
            return False

        if "documents" not in self.manifest_data:
            self.errors.append("Missing 'documents' key in manifest")
            return False

        if not isinstance(self.manifest_data["documents"], list):
            self.errors.append("'documents' must be a list")
            return False

        if len(self.manifest_data["documents"]) == 0:
            self.warnings.append("No documents defined in manifest")

        return True

    def validate_documents(self) -> bool:
        """Validate each document entry."""
        documents = self.manifest_data.get("documents", [])
        seen_filenames: Set[str] = set()
        valid_categories = {"act", "regulation", "guidance", "policy"}
        all_titles: Set[str] = set()

        for i, doc in enumerate(documents):
            doc_num = i + 1

            # Check required fields
            if "filename" not in doc:
                self.errors.append(f"Document {doc_num}: Missing 'filename' field")
                continue

            filename = doc["filename"]

            # Check for duplicate filenames
            if filename in seen_filenames:
                self.errors.append(f"Document {doc_num}: Duplicate filename '{filename}'")
            seen_filenames.add(filename)

            # Check if file exists (look in category subdirectory)
            category = doc.get("category", "")
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
                self.errors.append(f"Document {doc_num}: File not found: {filename} (expected in {expected_path})")

            # Check category
            if "category" not in doc:
                self.errors.append(f"Document {doc_num} ({filename}): Missing 'category' field")
            elif doc["category"] not in valid_categories:
                self.errors.append(
                    f"Document {doc_num} ({filename}): Invalid category '{doc['category']}'. "
                    f"Must be one of: {valid_categories}"
                )

            # Check title
            if "title" not in doc:
                self.warnings.append(f"Document {doc_num} ({filename}): Missing 'title' field")
            else:
                all_titles.add(doc["title"])

            # Category-specific validation
            category = doc.get("category")

            if category == "regulation":
                if "parent_act" not in doc:
                    self.errors.append(
                        f"Document {doc_num} ({filename}): Regulations must have 'parent_act' field"
                    )

            if category == "guidance":
                if "regulator" not in doc:
                    self.errors.append(
                        f"Document {doc_num} ({filename}): Guidance documents must have 'regulator' field"
                    )

            if category == "policy":
                if "company_id" not in doc:
                    self.errors.append(
                        f"Document {doc_num} ({filename}): Policies must have 'company_id' field"
                    )

        return len(self.errors) == 0

    def _normalize_act_name(self, name: str) -> str:
        """Normalize act name for matching (case-insensitive, remove citation)."""
        # Remove citation in parentheses: "(S.C.1991, c. 46)"
        import re
        name = re.sub(r'\s*\([^)]+\)\s*$', '', name)
        # Convert to lowercase for comparison
        return name.strip().lower()

    def _find_matching_act(self, parent_act_name: str, acts: set) -> bool:
        """Find if parent_act matches any act (case-insensitive, ignoring citations)."""
        normalized_parent = self._normalize_act_name(parent_act_name)

        for act_title in acts:
            normalized_act = self._normalize_act_name(act_title)
            if normalized_parent == normalized_act:
                return True

        return False

    def validate_relationships(self) -> bool:
        """Validate parent_act, implements, and related_acts references."""
        documents = self.manifest_data.get("documents", [])

        # Build index of all titles by category
        acts = {doc.get("title") for doc in documents if doc.get("category") == "act"}
        all_titles = {doc.get("title") for doc in documents if "title" in doc}

        # Check if this is a guidance-only manifest
        has_acts = len(acts) > 0
        is_guidance_only = all(doc.get("category") == "guidance" for doc in documents)

        for i, doc in enumerate(documents):
            doc_num = i + 1
            filename = doc.get("filename", f"doc_{doc_num}")

            # Validate parent_act references
            if "parent_act" in doc:
                parent = doc["parent_act"]

                # Skip parent_act validation for guidance-only manifests
                if is_guidance_only:
                    # Just validate that parent_act is a string
                    if not isinstance(parent, str):
                        self.errors.append(
                            f"Document {doc_num} ({filename}): "
                            f"parent_act must be a string"
                        )
                    continue

                # For mixed manifests, validate that parent_act exists
                # Try exact match first
                if parent not in acts:
                    # Try normalized match (case-insensitive, ignore citations)
                    if not self._find_matching_act(parent, acts):
                        self.errors.append(
                            f"Document {doc_num} ({filename}): "
                            f"parent_act '{parent}' not found in manifest acts"
                        )

            # Validate implements references
            if "implements" in doc:
                implements = doc["implements"]
                if not isinstance(implements, list):
                    self.errors.append(
                        f"Document {doc_num} ({filename}): 'implements' must be a list"
                    )
                else:
                    for impl in implements:
                        if impl not in all_titles:
                            self.warnings.append(
                                f"Document {doc_num} ({filename}): "
                                f"implements reference '{impl}' not found in manifest"
                            )

            # Validate related_acts references
            if "related_acts" in doc:
                related = doc["related_acts"]
                if not isinstance(related, list):
                    self.errors.append(
                        f"Document {doc_num} ({filename}): 'related_acts' must be a list"
                    )
                else:
                    for rel in related:
                        if rel not in acts:
                            self.warnings.append(
                                f"Document {doc_num} ({filename}): "
                                f"related_acts reference '{rel}' not found in manifest acts"
                            )

        return len(self.errors) == 0

    def validate(self) -> bool:
        """Run all validations."""
        print("=" * 60)
        print("VALIDATING MANIFEST")
        print("=" * 60)
        print(f"Manifest: {self.manifest_path}\n")

        # Load manifest
        if not self.load_manifest():
            return False

        # Validate structure
        if not self.validate_structure():
            return False

        # Validate documents
        self.validate_documents()

        # Validate relationships
        self.validate_relationships()

        # Display results
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All validations passed!")
            print(f"   Documents: {len(self.manifest_data['documents'])}")

            # Summary by category
            categories = {}
            for doc in self.manifest_data["documents"]:
                cat = doc.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1

            print("\n   Breakdown:")
            for cat, count in sorted(categories.items()):
                print(f"   • {cat}: {count}")

        print("=" * 60)

        return len(self.errors) == 0


def main():
    """Main validation function."""
    if len(sys.argv) != 2:
        print("Usage: python3 validate_manifest.py <manifest.yaml>")
        print("\nExample:")
        print("  python3 validate_manifest.py data/raw/manifest.yaml")
        sys.exit(1)

    manifest_path = sys.argv[1]

    validator = ManifestValidator(manifest_path)
    success = validator.validate()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()