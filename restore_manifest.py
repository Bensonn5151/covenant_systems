"""
Manifest Recovery Tool

Restores manifest.yaml from backup or merges multiple manifests.
Use this if manifest was accidentally overwritten.
"""

import argparse
import yaml
from pathlib import Path
from datetime import datetime


def list_backups(data_dir: str = "data/raw"):
    """List all available manifest backups."""
    data_path = Path(data_dir)
    backups = sorted(data_path.glob("manifest.backup.*.yaml"), reverse=True)

    if not backups:
        print("❌ No backups found")
        return []

    print(f"\n{'='*60}")
    print("AVAILABLE BACKUPS")
    print(f"{'='*60}\n")

    for i, backup in enumerate(backups, 1):
        # Extract timestamp from filename
        timestamp_str = backup.stem.replace("manifest.backup.", "")
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp_str

        # Get file size and document count
        with open(backup, 'r') as f:
            data = yaml.safe_load(f)
            doc_count = len(data.get('documents', [])) if data else 0

        file_size = backup.stat().st_size

        print(f"[{i}] {backup.name}")
        print(f"    Created: {formatted_time}")
        print(f"    Documents: {doc_count}")
        print(f"    Size: {file_size:,} bytes")
        print()

    return backups


def restore_from_backup(backup_path: str, output_path: str = "data/raw/manifest.yaml"):
    """Restore manifest from backup."""
    backup = Path(backup_path)
    output = Path(output_path)

    if not backup.exists():
        print(f"❌ Backup not found: {backup_path}")
        return False

    # Create backup of current manifest before restoring
    if output.exists():
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        current_backup = output.parent / f"manifest.before_restore.{timestamp}.yaml"

        import shutil
        shutil.copy2(output, current_backup)
        print(f"💾 Backed up current manifest to: {current_backup.name}")

    # Restore from backup
    import shutil
    shutil.copy2(backup, output)

    # Verify restoration
    with open(output, 'r') as f:
        data = yaml.safe_load(f)
        doc_count = len(data.get('documents', [])) if data else 0

    print(f"\n✅ Restored from backup: {backup.name}")
    print(f"   Documents: {doc_count}")
    print(f"   Location: {output}")

    return True


def merge_manifests(manifest_paths: list, output_path: str = "data/raw/manifest.yaml"):
    """Merge multiple manifests, removing duplicates."""

    all_documents = []
    seen_filenames = set()

    print(f"\n{'='*60}")
    print("MERGING MANIFESTS")
    print(f"{'='*60}\n")

    for manifest_path in manifest_paths:
        path = Path(manifest_path)

        if not path.exists():
            print(f"⚠️  Skipping (not found): {manifest_path}")
            continue

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        if not data or 'documents' not in data:
            print(f"⚠️  Skipping (no documents): {manifest_path}")
            continue

        count_before = len(all_documents)

        for doc in data['documents']:
            filename = doc.get('filename')

            if filename and filename not in seen_filenames:
                all_documents.append(doc)
                seen_filenames.add(filename)

        count_added = len(all_documents) - count_before
        print(f"✅ {path.name}: Added {count_added} documents (total: {len(all_documents)})")

    if not all_documents:
        print("\n❌ No documents to merge")
        return False

    # Write merged manifest
    output = Path(output_path)

    # Backup current manifest
    if output.exists():
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup = output.parent / f"manifest.before_merge.{timestamp}.yaml"

        import shutil
        shutil.copy2(output, backup)
        print(f"\n💾 Backed up current manifest to: {backup.name}")

    # Write merged result
    with open(output, 'w', encoding='utf-8') as f:
        f.write("# Merged manifest\n")
        f.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n")
        f.write(f"# Merged from {len(manifest_paths)} sources\n\n")

        yaml.dump(
            {"documents": all_documents},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    print(f"\n✅ Merged manifest saved: {output}")
    print(f"   Total documents: {len(all_documents)}")

    # Summary by category
    categories = {}
    for doc in all_documents:
        cat = doc.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    for cat in sorted(categories.keys()):
        print(f"   • {cat}: {categories[cat]}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Restore or merge manifest files"
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # List backups command
    list_parser = subparsers.add_parser('list', help='List available backups')
    list_parser.add_argument('--dir', default='data/raw', help='Directory to search for backups')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup', help='Path to backup file or backup number from list')
    restore_parser.add_argument('--output', default='data/raw/manifest.yaml', help='Output path')

    # Merge command
    merge_parser = subparsers.add_parser('merge', help='Merge multiple manifests')
    merge_parser.add_argument('manifests', nargs='+', help='Manifest files to merge')
    merge_parser.add_argument('--output', default='data/raw/manifest.yaml', help='Output path')

    args = parser.parse_args()

    if args.command == 'list':
        list_backups(args.dir)

    elif args.command == 'restore':
        # Check if backup is a number (index from list)
        if args.backup.isdigit():
            backups = sorted(Path(args.dir if hasattr(args, 'dir') else 'data/raw').glob("manifest.backup.*.yaml"), reverse=True)
            index = int(args.backup) - 1

            if 0 <= index < len(backups):
                restore_from_backup(str(backups[index]), args.output)
            else:
                print(f"❌ Invalid backup number. Use 'list' command to see available backups.")
        else:
            restore_from_backup(args.backup, args.output)

    elif args.command == 'merge':
        merge_manifests(args.manifests, args.output)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()