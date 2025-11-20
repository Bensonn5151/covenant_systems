# Covenant Systems - Complete Usage Guide

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA ACQUISITION LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│  1. run_mapper_from_config.py  →  Downloads Acts & Regulations  │
│  2. scrape_fintrac.py           →  Downloads FINTRAC Guidance   │
│                                                                  │
│                           ↓                                      │
│                    manifest.yaml                                 │
│              (Master Document Registry)                          │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                      VALIDATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  validate_manifest.py  →  Checks files exist, validates refs    │
│  fix_manifest_parent_acts.py  →  Fixes missing parent_act       │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  batch_ingest.py  →  Bronze (raw text) + Silver (sections)      │
│                                                                  │
│  Input:  data/raw/{acts,regulations,guidance}/*.pdf             │
│  Output: storage/bronze/text/*.txt                              │
│          storage/silver/sections/*.json                         │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                   KNOWLEDGE GRAPH LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  build_kg_from_manifest.py  →  Creates relationship graph       │
│                                                                  │
│  Output: storage/knowledge_graph/nodes.yaml                     │
│          storage/knowledge_graph/edges.yaml                     │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                      RECOVERY TOOLS                              │
├─────────────────────────────────────────────────────────────────┤
│  restore_manifest.py  →  Backup/restore/merge manifests         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📚 Complete Workflow - Start to Finish

### Step 1: Configure What to Download

**Edit `mapper_config.yaml`:**

```yaml
act_slugs:
  - "B-1.01"          # Bank Act
  - "P-24.501"        # PCMLTFA
  - "C-3"             # Canada Deposit Insurance Corporation Act

regulation_slugs:
  - "SOR-2021-181"
  - "SOR-2018-57"
```

**Purpose:** Centralized list of all legislation to download

---

### Step 2: Download Acts & Regulations

**Run:**
```bash
python3 run_mapper_from_config.py
```

**What it does:**
1. Reads `mapper_config.yaml`
2. Fetches each act/regulation from laws-lois.justice.gc.ca
3. Downloads PDFs to:
   - `data/raw/acts/`
   - `data/raw/regulations/`
4. **Merges** with existing `data/raw/manifest.yaml` (no data loss!)
5. Creates automatic backup: `manifest.backup.YYYYMMDD_HHMMSS.yaml`

**Output:**
```
data/raw/
├── acts/
│   ├── S.C.1991, c. 46 - Bank Act.pdf
│   └── ...
├── regulations/
│   ├── SOR-2021-181 - Financial Consumer Protection.pdf
│   └── ...
└── manifest.yaml  ← Updated with new entries
```

**Alternative (one-off downloads):**
```bash
# Download specific act
python3 run_mapper.py --act-slugs "B-1.01"

# Download specific regulations
python3 run_mapper.py --regulation-slugs "SOR-2021-181"
```

---

### Step 3: Download FINTRAC Guidance (HTML-based)

**Run:**
```bash
python3 scrape_fintrac.py data/raw/fintrac_guidance_manifest.yaml --format html
```

**What it does:**
1. Reads `data/raw/fintrac_guidance_manifest.yaml` (30+ guidance documents)
2. Fetches HTML pages from fintrac-canafe.canada.ca
3. Extracts main content (removes navigation/footers)
4. Saves to:
   - `data/raw/guidance/fintrac/html/` (for --format html)
   - `data/raw/guidance/fintrac/txt/` (for --format text)

**Manual step required (if using HTML format):**
```
1. Open each HTML file in browser
2. Print → Save as PDF
3. Save to data/raw/guidance/fintrac/
```

**Then merge manifests:**
```bash
python3 restore_manifest.py merge \
    data/raw/manifest.yaml \
    data/raw/fintrac_guidance_manifest.yaml
```

---

### Step 4: Validate Manifest

**Run:**
```bash
python3 validate_manifest.py data/raw/manifest.yaml
```

**What it checks:**
- ✅ All PDF files exist in correct subdirectories
- ✅ All `parent_act` references match existing acts (case-insensitive)
- ✅ Required fields present
- ✅ No duplicate filenames

**If errors appear:**

**Error:** "Regulations must have 'parent_act' field"
```bash
# Fix missing parent_act
python3 fix_manifest_parent_acts.py
```

**Error:** "parent_act 'XYZ ACT' not found in manifest acts"
```bash
# Add the missing act to mapper_config.yaml
# Then re-run: python3 run_mapper_from_config.py
```

---

### Step 5: Batch Ingest (Bronze + Silver)

**Run:**
```bash
python3 batch_ingest.py data/raw/manifest.yaml

# Or continue on errors (large files may fail)
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error
```

**What it does:**
1. Processes in dependency order:
   - Acts first
   - Regulations (depend on acts)
   - Guidance
   - Policies
2. For each PDF:
   - **Bronze layer:** Extract raw text
     - Tries Adobe PDF Services (best quality)
     - Falls back to PyMuPDF/pdfplumber if Adobe fails
   - **Silver layer:** Parse into sections
     - Detects section numbers (1, 1.1, 1.2.3)
     - Creates JSON for each section
3. Skips already-processed documents

**Output:**
```
storage/
├── bronze/
│   ├── text/
│   │   ├── bank_act_s_c_1991_c_46.txt
│   │   └── ...
│   └── metadata/
│       └── bank_act_s_c_1991_c_46_metadata.json
└── silver/
    └── sections/
        ├── bank_act_s_c_1991_c_46_sections.json
        └── ...
```

**If errors occur:**
```
❌ Adobe PDF extraction failed: File exceeds page limit
```
→ Use `--continue-on-error` to skip and continue
→ Large files will fall back to PyMuPDF

---

### Step 6: Build Knowledge Graph

**Run:**
```bash
python3 build_kg_from_manifest.py data/raw/manifest.yaml
```

**What it does:**
1. Reads manifest relationships:
   - `parent_act` → Creates `derives_from` edges
   - `implements` → Creates `implements` edges
2. Generates:
   - **Nodes:** Each document/section
   - **Edges:** Relationships between documents

**Output:**
```
storage/knowledge_graph/
├── nodes.yaml     # All documents as graph nodes
└── edges.yaml     # Relationships (derives_from, implements, relates_to)
```

**Example edge:**
```yaml
- from: "SOR-2021-181 - Financial Consumer Protection.pdf"
  to: "Bank Act (S.C.1991, c. 46)"
  type: "derives_from"
  confidence: 1.0
```

---

## 🔧 Tool Reference

### 1. `mapper_config.yaml`
**Purpose:** Central configuration for legislative mapper

**Usage:**
```yaml
act_slugs:
  - "B-1.01"    # Just add new slugs here

regulation_slugs:
  - "SOR-2025-XXX"  # Add as you discover them
```

---

### 2. `run_mapper_from_config.py`
**Purpose:** Download all acts/regulations from config

**Usage:**
```bash
python3 run_mapper_from_config.py              # Normal mode
python3 run_mapper_from_config.py --force      # Re-download existing
```

**What it does:**
- Reads `mapper_config.yaml`
- Downloads all listed acts/regulations
- Merges with existing manifest (safe!)
- Creates backups automatically

---

### 3. `run_mapper.py` (One-off downloads)
**Purpose:** Download specific acts/regulations without config

**Usage:**
```bash
# By name
python3 run_mapper.py --acts "Bank Act"

# By slug
python3 run_mapper.py --act-slugs "B-1.01"

# Specific regulations
python3 run_mapper.py --regulation-slugs "SOR-2021-181"
```

---

### 4. `scrape_fintrac.py`
**Purpose:** Download FINTRAC HTML guidance

**Usage:**
```bash
python3 scrape_fintrac.py data/raw/fintrac_guidance_manifest.yaml --format html
```

**Note:** Requires manual HTML → PDF conversion

---

### 5. `validate_manifest.py`
**Purpose:** Pre-flight checks before ingestion

**Usage:**
```bash
python3 validate_manifest.py data/raw/manifest.yaml
```

**Checks:**
- Files exist in correct directories
- Parent act references are valid
- Required fields present
- No duplicates

---

### 6. `fix_manifest_parent_acts.py`
**Purpose:** Fix missing `parent_act` fields

**Usage:**
```bash
python3 fix_manifest_parent_acts.py
```

**Edit the script to add known mappings:**
```python
KNOWN_PARENT_ACTS = {
    "SOR-2021-181": "Bank Act (S.C.1991, c. 46)",
    # Add more here
}
```

---

### 7. `batch_ingest.py`
**Purpose:** Process PDFs → Bronze + Silver layers

**Usage:**
```bash
python3 batch_ingest.py data/raw/manifest.yaml
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error
python3 batch_ingest.py data/raw/manifest.yaml --skip-validation
```

**Options:**
- `--continue-on-error` - Don't stop on failures (recommended for large batches)
- `--skip-validation` - Skip pre-flight validation
- `--dry-run` - Validate only, don't process

---

### 8. `build_kg_from_manifest.py`
**Purpose:** Generate knowledge graph from relationships

**Usage:**
```bash
python3 build_kg_from_manifest.py data/raw/manifest.yaml
```

**Output:**
- `storage/knowledge_graph/nodes.yaml`
- `storage/knowledge_graph/edges.yaml`

---

### 9. `restore_manifest.py`
**Purpose:** Backup, restore, merge manifests

**Usage:**
```bash
# List backups
python3 restore_manifest.py list

# Restore from backup
python3 restore_manifest.py restore 1

# Merge multiple manifests
python3 restore_manifest.py merge \
    data/raw/manifest.yaml \
    data/raw/fintrac_guidance_manifest.yaml
```

---

## 🎯 Common Scenarios

### Scenario 1: Add New Acts/Regulations

```bash
# 1. Add to config
echo "  - \"P-21\"  # Privacy Act" >> mapper_config.yaml

# 2. Download
python3 run_mapper_from_config.py

# 3. Validate
python3 validate_manifest.py data/raw/manifest.yaml

# 4. Ingest
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error
```

---

### Scenario 2: Validation Errors

**Error:** "parent_act 'XYZ' not found"
```bash
# Solution 1: Add the act to mapper_config.yaml
vim mapper_config.yaml  # Add "XYZ" act slug
python3 run_mapper_from_config.py

# Solution 2: Fix parent_act reference manually
vim fix_manifest_parent_acts.py  # Add mapping
python3 fix_manifest_parent_acts.py
```

---

### Scenario 3: Ingestion Failures

**Error:** "Adobe PDF extraction failed: Page limit exceeded"
```bash
# Use continue-on-error to skip large files
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error

# Check which files failed
# (They'll be listed in the summary at the end)
```

**At end of run, you'll see:**
```
❌ Failed documents (needs review):
  • Bank Act - File too large for Adobe API
  • PCMLTFA - Scanned PDF, OCR needed
```

---

### Scenario 4: Manifest Data Loss

**Accidentally overwrote manifest:**
```bash
# List backups
python3 restore_manifest.py list

# Restore most recent
python3 restore_manifest.py restore 1

# Verify
python3 validate_manifest.py data/raw/manifest.yaml
```

---

### Scenario 5: Building Complete AML/CFT Knowledge Base

```bash
# 1. Configure all acts
cat > mapper_config.yaml <<EOF
act_slugs:
  - "B-1.01"          # Bank Act
  - "P-24.501"        # PCMLTFA
  - "P-8.6"           # PIPEDA
  - "C-3"             # CDIC Act
EOF

# 2. Download acts & regulations
python3 run_mapper_from_config.py

# 3. Download FINTRAC guidance
python3 scrape_fintrac.py data/raw/fintrac_guidance_manifest.yaml --format html
# (Manually convert HTML → PDF)

# 4. Merge manifests
python3 restore_manifest.py merge \
    data/raw/manifest.yaml \
    data/raw/fintrac_guidance_manifest.yaml

# 5. Validate
python3 validate_manifest.py data/raw/manifest.yaml

# 6. Fix any errors
python3 fix_manifest_parent_acts.py

# 7. Batch ingest
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error

# 8. Build knowledge graph
python3 build_kg_from_manifest.py data/raw/manifest.yaml
```

**Result:**
```
data/raw/
├── acts/ (5 PDFs)
├── regulations/ (50+ PDFs)
├── guidance/fintrac/ (30+ PDFs)
└── manifest.yaml (85+ documents)

storage/
├── bronze/text/ (85+ text files)
├── silver/sections/ (85+ JSON files)
└── knowledge_graph/
    ├── nodes.yaml
    └── edges.yaml
```

---

## 📊 File Organization

```
covenant_systems/
├── mapper_config.yaml                 # ← Configuration
├── run_mapper_from_config.py         # ← Main download script
├── validate_manifest.py               # ← Pre-flight validation
├── batch_ingest.py                    # ← Main processing script
├── build_kg_from_manifest.py          # ← Knowledge graph builder
├── restore_manifest.py                # ← Recovery tool
│
├── data/raw/
│   ├── acts/                          # ← PDFs from run_mapper
│   ├── regulations/                   # ← PDFs from run_mapper
│   ├── guidance/
│   │   └── fintrac/
│   │       ├── html/                  # ← HTML files from scrape_fintrac
│   │       ├── txt/                   # ← Text files from scrape_fintrac
│   │       └── *.pdf                  # ← Converted PDFs (for ingestion)
│   ├── manifest.yaml                  # ← Master registry
│   ├── manifest.backup.*.yaml         # ← Auto-backups
│   └── fintrac_guidance_manifest.yaml # ← FINTRAC config
│
└── storage/
    ├── bronze/
    │   ├── text/                      # ← Raw text (from batch_ingest)
    │   └── metadata/                  # ← Metadata JSON
    ├── silver/
    │   └── sections/                  # ← Section JSON (from batch_ingest)
    └── knowledge_graph/
        ├── nodes.yaml                 # ← From build_kg_from_manifest
        └── edges.yaml                 # ← From build_kg_from_manifest
```

---

## 🔍 Troubleshooting

### Issue: "File not found" errors

**Cause:** Files in wrong directory

**Solution:**
```bash
# Check where files actually are
ls data/raw/
ls data/raw/acts/
ls data/raw/regulations/

# Validation now checks subdirectories automatically
python3 validate_manifest.py data/raw/manifest.yaml
```

---

### Issue: "parent_act not found" errors

**Cause:** Act name mismatch (case, citation)

**Solution:** Validation now does smart matching (case-insensitive, ignores citations)

If still failing:
```bash
# Add the missing act
vim mapper_config.yaml
python3 run_mapper_from_config.py
```

---

### Issue: Adobe PDF extraction fails

**Cause:** File too large or scanned

**Solutions:**
1. Use `--continue-on-error` to skip and continue
2. Falls back to PyMuPDF automatically (if implemented)
3. For scanned PDFs: Use Adobe OCR separately

```bash
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error
```

---

### Issue: Manifest overwritten

**Solution:**
```bash
# Automatic backups created before every write
python3 restore_manifest.py list
python3 restore_manifest.py restore 1
```

---

## 🎓 Quick Reference

| Task | Command |
|------|---------|
| Add new legislation | Edit `mapper_config.yaml` → `run_mapper_from_config.py` |
| Validate before ingesting | `validate_manifest.py data/raw/manifest.yaml` |
| Process all documents | `batch_ingest.py data/raw/manifest.yaml --continue-on-error` |
| Build knowledge graph | `build_kg_from_manifest.py data/raw/manifest.yaml` |
| Restore from backup | `restore_manifest.py list` → `restore_manifest.py restore 1` |
| Fix missing parent_act | Edit `fix_manifest_parent_acts.py` → Run it |
| Merge manifests | `restore_manifest.py merge manifest1.yaml manifest2.yaml` |

---

## 📖 Additional Documentation

- **Manifest recovery:** [docs/MANIFEST_RECOVERY.md](docs/MANIFEST_RECOVERY.md)
- **Dashboard architecture:** [docs/CUSTOMER_DASHBOARD_ARCHITECTURE.md](docs/CUSTOMER_DASHBOARD_ARCHITECTURE.md)
- **Project specification:** [CLAUDE.md](CLAUDE.md)
- **Legislative mapper design:** [PLAN.md](PLAN.md)

---

## ✅ Complete Checklist

**Initial Setup:**
- [ ] Configure `mapper_config.yaml` with acts/regulations
- [ ] Run `python3 run_mapper_from_config.py`
- [ ] Scrape FINTRAC guidance (if needed)
- [ ] Merge manifests (if needed)

**Pre-Ingestion:**
- [ ] Run `python3 validate_manifest.py data/raw/manifest.yaml`
- [ ] Fix any validation errors
- [ ] Re-validate until clean

**Ingestion:**
- [ ] Run `python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error`
- [ ] Review any failed documents
- [ ] Check Bronze/Silver outputs

**Knowledge Graph:**
- [ ] Run `python3 build_kg_from_manifest.py data/raw/manifest.yaml`
- [ ] Verify nodes.yaml and edges.yaml created

**Maintenance:**
- [ ] Add new acts/regulations to `mapper_config.yaml` as discovered
- [ ] Re-run mapper periodically for updates
- [ ] Keep backups of manifest

---

## 🚀 You're Ready!

The system is now fully operational. Start by adding legislation to `mapper_config.yaml` and running through the workflow!
