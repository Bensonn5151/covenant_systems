# Manifest Recovery & Data Loss Prevention

## Problem

The Legislative Mapper (`run_mapper.py`) was overwriting `data/raw/manifest.yaml` instead of merging with existing entries, causing loss of previously discovered regulations.

### What Happened

1. User had a manifest with 13 regulations
2. Ran `python3 run_mapper.py --acts "Bank Act"`
3. Manifest was overwritten with only the Bank Act
4. All 13 regulations were lost

## Solution Implemented

### 1. Automatic Merging (Default Behavior)

`ManifestGenerator` now defaults to **merge mode**:

```python
# This is now the default behavior
generator = ManifestGenerator(output_path="manifest.yaml", merge=True)
```

**What it does:**
- Loads existing manifest on initialization
- Preserves all existing documents
- Only adds new discoveries
- Skips duplicates (based on filename)

**Verification:**
```bash
python3 test_manifest_merge.py
```

### 2. Automatic Backups

Every time `generate()` is called, a timestamped backup is created:

```
data/raw/
├── manifest.yaml
├── manifest.backup.20251120_120000.yaml
├── manifest.backup.20251120_130000.yaml
└── ...
```

**Retention policy:**
- Keeps last 10 backups automatically
- Older backups are deleted automatically

### 3. Recovery Tools

#### List Available Backups

```bash
python3 restore_manifest.py list
```

Output:
```
============================================================
AVAILABLE BACKUPS
============================================================

[1] manifest.backup.20251120_130000.yaml
    Created: 2025-11-20 13:00:00
    Documents: 14
    Size: 2,456 bytes

[2] manifest.backup.20251120_120000.yaml
    Created: 2025-11-20 12:00:00
    Documents: 13
    Size: 2,234 bytes
```

#### Restore from Backup

By number:
```bash
python3 restore_manifest.py restore 1
```

By path:
```bash
python3 restore_manifest.py restore data/raw/manifest.backup.20251120_130000.yaml
```

#### Merge Multiple Manifests

If you have separate manifests that need to be combined:

```bash
python3 restore_manifest.py merge \
    data/raw/manifest.yaml \
    data/raw/fintrac_guidance_manifest.yaml \
    data/raw/old_manifest.yaml
```

**Features:**
- Removes duplicates (based on filename)
- Preserves all unique documents
- Creates backup before merging

## Usage Guidelines

### Safe Usage

✅ **DO:**
```bash
# This is safe - will merge with existing manifest
python3 run_mapper.py --acts "Bank Act"

# This is safe - will add new regulations without removing old ones
python3 run_mapper.py --regulation-slugs "SOR-2025-001"

# Multiple runs are safe
python3 run_mapper.py --acts "PCMLTFA"
python3 run_mapper.py --acts "PIPEDA"
```

❌ **DON'T:**
```bash
# Don't manually delete manifest unless intentional
rm data/raw/manifest.yaml

# Don't use overwrite mode unless you want to start fresh
# (This would require code modification - merge is default)
```

### Recovering from Data Loss

If you accidentally lose data:

1. **List backups:**
   ```bash
   python3 restore_manifest.py list
   ```

2. **Restore the most recent backup:**
   ```bash
   python3 restore_manifest.py restore 1
   ```

3. **Verify restoration:**
   ```bash
   python3 validate_manifest.py data/raw/manifest.yaml
   ```

### Rebuilding from Scratch

If you need to rebuild the entire manifest:

1. **Archive current manifest:**
   ```bash
   mv data/raw/manifest.yaml data/raw/manifest.archive.yaml
   ```

2. **Run mapper for all acts:**
   ```bash
   python3 run_mapper.py --acts "Bank Act" "PCMLTFA" "PIPEDA"
   ```

3. **Merge with specialized manifests:**
   ```bash
   python3 restore_manifest.py merge \
       data/raw/manifest.yaml \
       data/raw/fintrac_guidance_manifest.yaml
   ```

## Technical Details

### Merge Algorithm

1. **Load existing manifest**
   - Read all existing documents into memory
   - Create index of filenames for duplicate detection

2. **Add new documents**
   - Check if filename already exists
   - Skip if duplicate
   - Add if new

3. **Write with backup**
   - Create timestamped backup of current manifest
   - Write merged result
   - Clean up old backups (keep last 10)

### Duplicate Detection

Documents are considered duplicates if they have the same `filename`:

```yaml
# These are duplicates (same filename)
- filename: "Bank Act.pdf"
  citation: "S.C.1991, c. 46"

- filename: "Bank Act.pdf"
  citation: "S.C.1991, c. 46"
```

### Backup Naming Convention

```
manifest.backup.{timestamp}.yaml
manifest.backup.20251120_130000.yaml
                ^^^^^^^^ ^^^^^^
                YYYYMMDD HHMMSS (UTC)
```

## Preventing Future Issues

### Best Practices

1. **Always validate before processing:**
   ```bash
   python3 validate_manifest.py data/raw/manifest.yaml
   ```

2. **Use version control:**
   ```bash
   git add data/raw/manifest.yaml
   git commit -m "Updated manifest with new regulations"
   ```

3. **Periodic backups:**
   ```bash
   # Manual backup before major changes
   cp data/raw/manifest.yaml data/raw/manifest.$(date +%Y%m%d).yaml
   ```

4. **Review changes:**
   ```bash
   # See what was added
   git diff data/raw/manifest.yaml
   ```

### Monitoring

Check manifest health regularly:

```bash
# Count documents by category
python3 -c "
import yaml
with open('data/raw/manifest.yaml') as f:
    docs = yaml.safe_load(f)['documents']

from collections import Counter
counts = Counter(d['category'] for d in docs)

for cat, count in sorted(counts.items()):
    print(f'{cat}: {count}')
"
```

Expected output:
```
act: 5
guidance: 30
regulation: 50
```

## Troubleshooting

### Issue: Manifest still being overwritten

**Diagnosis:**
```python
# Check if merge mode is enabled
from ingestion.mapper import ManifestGenerator
gen = ManifestGenerator()
print(gen.merge)  # Should be True
```

**Solution:**
- Verify `manifest_generator.py` has `merge: bool = True` default parameter
- Update code if necessary

### Issue: Backups not being created

**Diagnosis:**
```bash
ls -la data/raw/manifest.backup.*.yaml
```

**Solution:**
- Ensure `_create_backup()` is being called in `generate()`
- Check file permissions on `data/raw/` directory

### Issue: Duplicates appearing in manifest

**Diagnosis:**
```bash
python3 -c "
import yaml
with open('data/raw/manifest.yaml') as f:
    docs = yaml.safe_load(f)['documents']

filenames = [d['filename'] for d in docs]
duplicates = [f for f in filenames if filenames.count(f) > 1]

if duplicates:
    print('Duplicates found:', set(duplicates))
else:
    print('No duplicates')
"
```

**Solution:**
```bash
# Deduplicate using merge tool
python3 restore_manifest.py merge data/raw/manifest.yaml
```

## Summary

✅ **Manifest merging is now automatic** - no more data loss
✅ **Automatic backups** - can always recover
✅ **Recovery tools** - easy restoration
✅ **Validation** - catch issues early

**The system is now safe to use repeatedly without data loss.**