"""
Test Manifest Merging Functionality

Verifies that ManifestGenerator correctly merges with existing manifest
instead of overwriting it.
"""

import yaml
import tempfile
from pathlib import Path
from ingestion.mapper import ManifestGenerator


def test_merge_preserves_existing_entries():
    """Test that merge mode preserves existing entries."""

    # Create temporary manifest with existing entries
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        existing_manifest = {
            "documents": [
                {
                    "filename": "existing_regulation.pdf",
                    "category": "regulation",
                    "title": "Existing Regulation",
                    "citation": "SOR-2021-001",
                    "jurisdiction": "federal",
                },
                {
                    "filename": "existing_act.pdf",
                    "category": "act",
                    "title": "Existing Act",
                    "citation": "S.C. 2020, c. 1",
                    "jurisdiction": "federal",
                }
            ]
        }
        yaml.dump(existing_manifest, f)
        temp_path = f.name

    try:
        # Initialize generator with merge=True
        generator = ManifestGenerator(output_path=temp_path, merge=True)

        # Should have loaded 2 existing documents
        assert len(generator.documents) == 2, f"Expected 2 documents, got {len(generator.documents)}"
        print("✅ Loaded existing manifest: 2 documents")

        # Add a new act
        new_metadata = {
            "title": "New Act",
            "citation": "S.C. 2025, c. 1",
            "current_to": "2025-11-20",
        }
        new_download = {
            "filename": "new_act.pdf",
            "checksum": "abc123",
            "downloaded_at": "2025-11-20T00:00:00Z",
        }
        generator.add_act(new_metadata, new_download)

        # Should now have 3 documents
        assert len(generator.documents) == 3, f"Expected 3 documents, got {len(generator.documents)}"
        print("✅ Added new act: 3 documents total")

        # Try to add duplicate - should skip
        generator.add_act(new_metadata, new_download)
        assert len(generator.documents) == 3, f"Expected 3 documents (no duplicate), got {len(generator.documents)}"
        print("✅ Skipped duplicate: still 3 documents")

        # Generate manifest
        generator.generate()

        # Read back and verify
        with open(temp_path, 'r') as f:
            result = yaml.safe_load(f)

        assert len(result['documents']) == 3, f"Expected 3 documents in file, got {len(result['documents'])}"

        # Verify original entries still exist
        filenames = [doc['filename'] for doc in result['documents']]
        assert "existing_regulation.pdf" in filenames, "Missing original regulation"
        assert "existing_act.pdf" in filenames, "Missing original act"
        assert "new_act.pdf" in filenames, "Missing new act"

        print("✅ All entries preserved in final manifest")
        print("\n✅ MERGE TEST PASSED - Manifest merging works correctly!")

    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)


def test_overwrite_mode():
    """Test that merge=False overwrites existing manifest."""

    # Create temporary manifest
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({"documents": [{"filename": "old.pdf"}]}, f)
        temp_path = f.name

    try:
        # Initialize with merge=False
        generator = ManifestGenerator(output_path=temp_path, merge=False)

        # Should NOT have loaded existing documents
        assert len(generator.documents) == 0, f"Expected 0 documents (overwrite mode), got {len(generator.documents)}"
        print("✅ Overwrite mode correctly ignores existing manifest")

    finally:
        Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING MANIFEST MERGE FUNCTIONALITY")
    print("=" * 60)
    print()

    test_merge_preserves_existing_entries()
    print()
    test_overwrite_mode()
    print()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)