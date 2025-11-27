# Covenant Systems - Usage Guide

**Version:** 0.2.0 (Bronze → Silver → Gold → Search)
**Last Updated:** 2025-11-21

---

## 📖 Table of Contents

1. [Quick Start (Existing Data)](#-quick-start-existing-data)
2. [Complete Workflow (From Scratch)](#-complete-workflow-from-scratch)
3. [System Architecture](#-system-architecture)
4. [Phase 1: Data Gathering](#phase-1-data-gathering)
5. [Phase 2: Manifest Management](#phase-2-manifest-management)
6. [Phase 3: Ingestion Pipeline](#phase-3-ingestion-pipeline)
7. [Phase 4: Embeddings & Search](#phase-4-embeddings--search)
8. [Common Workflows](#-common-workflows)
9. [Troubleshooting](#-troubleshooting)
10. [Command Reference](#-quick-command-reference)

---

## 🚀 Quick Start (Existing Data)

**If you already have PDFs and manifests**, use this shortcut:

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Process documents (Bronze → Silver)
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error
python3 batch_ingest.py data/raw/fintrac_guidance_manifest.yaml --continue-on-error

# 3. Generate embeddings (Silver → Gold)
python3 generate_embeddings.py

# 4. Launch dashboard
./run_dashboard.sh
```

**Result:** Browse at http://localhost:8501
- 📤 Upload: Process new PDFs
- 🔷 Silver Layer: Browse structured sections
- 🔍 Search: Semantic search across all documents

---

## 🔄 Complete Workflow (From Scratch)

**Starting with no data?** Follow this complete sequence:

```
1. Data Gathering
   └─> Configure mapper (mapper_config.yaml)
   └─> Download acts/regulations (run_mapper_from_config.py)
   └─> Scrape FINTRAC guidance (scrape_fintrac.py)
   └─> Convert HTML to PDF (convert_html_to_pdf.py)

2. Manifest Management
   └─> Auto-generated manifest (manifest.yaml)
   └─> Validate manifest (validate_manifest.py)

3. Ingestion Pipeline
   └─> PDF → Bronze → Silver (batch_ingest.py)

4. Embeddings & Search
   └─> Silver → Gold (generate_embeddings.py)
   └─> Search (dashboard or CLI)
```

---

## 📊 System Architecture

```
Data Sources (Laws.justice.gc.ca, FINTRAC)
    ↓
┌─────────────────────────────────────────────┐
│ DATA GATHERING                              │
│ • Mapper downloads acts/regulations         │
│ • Scraper fetches FINTRAC HTML guidance    │
│ • HTML → PDF conversion                     │
│ Output: data/raw/{acts,regulations,guidance}│
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ MANIFEST (Metadata Registry)                │
│ • Auto-generated from downloads             │
│ • YAML format (document metadata)           │
│ Output: data/raw/manifest.yaml              │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ BRONZE LAYER (Raw Text)                     │
│ • Adobe PDF Services (95%+ accuracy)        │
│ • Language filtering (English only)         │
│ • OCR fallback for scanned docs             │
│ Output: storage/bronze/{category}/{doc_id}/ │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ SILVER LAYER (Structured Sections)          │
│ • Hybrid segmentation (bookmarks + regex)   │
│ • Hierarchical numbering (1, 1.1, 1.2.3)   │
│ • Metadata inference (jurisdiction, type)   │
│ Output: storage/silver/{category}/{doc_id}/ │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ GOLD LAYER (Embeddings)                     │
│ • sentence-transformers (384 dimensions)    │
│ • FAISS vector index (cosine similarity)    │
│ Output: storage/gold/{doc_id}/              │
│         storage/vector_db/covenant.index    │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ SEARCH (Semantic Similarity)                │
│ • Natural language queries                  │
│ • Top-K retrieval with scores               │
│ • Category filtering (act, reg, guidance)   │
│ • Export (JSON, CSV)                        │
└─────────────────────────────────────────────┘
```

---

## Phase 1: Data Gathering

### Step 1.1: Configure Mapper

The mapper configuration defines which acts and regulations to download from laws-justice.gc.ca.

**Edit Configuration:**
```bash
vim mapper_config.yaml
```

**Example Configuration:**
```yaml
# Acts to download (auto-discovers related regulations)
acts:
  - "Bank Act"
  - "Proceeds of Crime (Money Laundering) and Terrorist Financing Act"
  - "Personal Information Protection and Electronic Documents Act"

# Act slugs (alternative identifiers)
act_slugs:
  - "P-24.501"  # PCMLTFA
  - "P-8.6"     # PIPEDA

# Specific regulations (if not auto-discovered)
regulation_slugs:
  - "SOR-2002-184"  # PCMLTFA Regulations
  - "SOR-2001-317"  # PCMLTFA STR Regulations
  - "SOR-2002-412"  # Cross-border Currency Reporting
```

**What This Does:**
- Acts: Downloads full legislation text
- Regulations: Downloads implementing regulations
- Auto-discovery: Finds related regulations for each act
- Output: Organizes files into `data/raw/acts/` and `data/raw/regulations/`

---

### Step 1.2: Download Acts & Regulations

**Command:**
```bash
python3 run_mapper_from_config.py
```

**What Happens:**
1. Reads `mapper_config.yaml`
2. Queries laws-justice.gc.ca API
3. Downloads acts as PDFs → `data/raw/acts/`
4. Downloads regulations as PDFs → `data/raw/regulations/`
5. Generates/updates `manifest.yaml` with metadata
6. Creates backup: `manifest.backup.TIMESTAMP.yaml`

**Output:**
```
✓ Downloaded: Bank Act → data/raw/acts/S.C.1991, c. 46 - Bank Act.pdf
✓ Downloaded: PCMLTFA → data/raw/acts/S.C.2000, c. 17 - Proceeds of Crime....pdf
✓ Downloaded: SOR-2002-184 → data/raw/regulations/SOR-2002-184 - PCMLTFA Regulations.pdf
...
✓ Manifest updated: data/raw/manifest.yaml
```

**Performance:**
- ~30 seconds per document
- Includes checksums for integrity verification
- Idempotent: Skips existing files (checks checksum)

---

### Step 1.3: Scrape FINTRAC Guidance

FINTRAC guidance documents are HTML pages that need to be scraped and converted to PDF.

**Command:**
```bash
python3 scrape_fintrac.py data/raw/fintrac_guidance_manifest.yaml --format html
```

**What Happens:**
1. Reads guidance documents from FINTRAC-specific manifest
2. Fetches HTML from FINTRAC website
3. Extracts main content (removes navigation, footers)
4. Saves clean HTML → `data/raw/guidance/fintrac/html/`

**Output:**
```
============================================================
FINTRAC GUIDANCE SCRAPER
============================================================
Manifest: data/raw/fintrac_guidance_manifest.yaml
Output: data/raw/guidance/fintrac/html
Format: html
============================================================

Found 8 FINTRAC guidance documents

[1/8] Guidance on the Risk-Based Approach
  URL: https://fintrac-canafe.canada.ca/guidance-directives/compliance-conformite/rba/rba-eng
  ✅ Saved: FINTRAC - Risk-Based Approach Guidance.html

[2/8] Methods to verify the identity of persons and entities
  URL: https://fintrac-canafe.canada.ca/guidance-directives/client-clientele/Guide11/11-eng
  ✅ Saved: FINTRAC - Methods to Verify Identity.html
...
✓ 8 documents fetched
```

**Options:**
- `--format html` - Clean HTML (recommended)
- `--format text` - Plain text (loses formatting)

**Note:** The FINTRAC guidance manifest (`fintrac_guidance_manifest.yaml`) is separate from the main manifest and contains only the guidance documents listed in `mapper_config.yaml`.

---

### Step 1.4: Convert HTML to PDF

**Option A: Automated Conversion (Recommended)**
```bash
python3 convert_html_to_pdf.py
```

Converts all HTML files in `data/raw/guidance/fintrac/html/` to PDF using weasyprint or pdfkit.

**What Happens:**
1. Scans `data/raw/guidance/fintrac/html/` for HTML files
2. Converts each to PDF using weasyprint (or pdfkit fallback)
3. Saves PDFs to `data/raw/guidance/fintrac/`
4. Skips existing PDFs (idempotent)

**Output:**
```
============================================================
HTML TO PDF CONVERTER
============================================================
Source: data/raw/guidance/fintrac/html
Target: data/raw/guidance/fintrac
Found 8 HTML files
============================================================

[1/8] FINTRAC - Risk-Based Approach Guidance.html
  → Converting to PDF...
  ✓ Saved: FINTRAC - Risk-Based Approach Guidance.pdf (245.3 KB)

[2/8] FINTRAC - Methods to Verify Identity.html
  → Converting to PDF...
  ✓ Saved: FINTRAC - Methods to Verify Identity.pdf (312.7 KB)
...

============================================================
CONVERSION SUMMARY
============================================================
Converted: 8
Skipped:   0
Failed:    0
Total:     8
============================================================
```

**Options:**
- `--check-only` - Preview what would be converted without converting
- `--force` - Overwrite existing PDFs

**Option B: Manual Conversion (Higher Quality)**
```bash
# 1. Open HTML in browser
open data/raw/guidance/fintrac/html/FINTRAC\ -\ Risk-Based\ Approach\ Guidance.html

# 2. Print → Save as PDF
# 3. Save to data/raw/guidance/fintrac/

# Repeat for each HTML file
```

**Prerequisites for Automated Conversion:**
```bash
# Install weasyprint (recommended)
pip install weasyprint

# macOS: Install pango dependency
brew install pango

# Alternative: pdfkit
pip install pdfkit
```

---

### Step 1.5: Verify Data Gathering

**Check Downloaded Files:**
```bash
# Count downloaded documents
ls data/raw/acts/*.pdf | wc -l
ls data/raw/regulations/*.pdf | wc -l
ls data/raw/guidance/*.pdf | wc -l

# Total documents
find data/raw -name "*.pdf" | wc -l
```

**Expected Output:**
```
Acts: 4
Regulations: 9
Guidance: 33
Total: 46 documents
```

---

## Phase 2: Manifest Management

### Step 2.1: Understanding Manifests

Manifests are YAML files that define document metadata for ingestion.

**Available Manifests:**

| Manifest | Size | Docs | Purpose |
|----------|------|------|---------|
| `manifest.yaml` | 20KB | 46 | Master registry (all documents) |
| `milestone_1_fintrac_pcmltfa.yaml` | 16KB | 36 | Complete PCMLTFA framework |
| `milestone_1_fintrac_guidance_only.yaml` | 15KB | 33 | Guidance only (incremental) |
| `test_minimal.yaml` | 1.8KB | 3 | Development/testing |

**See:** [docs/MANIFEST_GUIDE.md](docs/MANIFEST_GUIDE.md) for detailed comparison.

---

### Step 2.2: Manifest Structure

**Example Entry:**
```yaml
documents:
- filename: SOR-2002-184 - PCMLTFA Regulations.pdf
  category: regulation
  title: Proceeds of Crime (Money Laundering) and Terrorist Financing Regulations
  citation: SOR/2002-184
  jurisdiction: federal
  parent_act: Proceeds of Crime (Money Laundering) and Terrorist Financing Act
  checksum: 0cb297c61064f58b8f4bc3504a85ad1540e553906d24b441f706b288aa006029
```

**Fields:**
- `filename`: PDF filename in `data/raw/{category}/`
- `category`: act | regulation | guidance | policy
- `title`: Full legal title
- `citation`: Official citation
- `jurisdiction`: federal | provincial | municipal
- `parent_act`: Parent legislation (for regs/guidance)
- `checksum`: SHA256 hash (integrity verification)

---

### Step 2.3: Validate Manifest

**Command:**
```bash
python3 validate_manifest.py data/raw/manifest.yaml
```

**Checks:**
- ✓ All PDF files exist in correct directories
- ✓ Parent act references are valid
- ✓ Required fields present (filename, category, title)
- ✓ No duplicate filenames
- ✓ Valid category values
- ✓ Checksums match (if provided)

**Output (Success):**
```
✓ Manifest valid: 46 documents
✓ Files exist: 46/46
✓ Parent references valid: 42/42
✓ No duplicates found
```

**Output (Errors):**
```
❌ Validation failed:
  - File not found: data/raw/acts/Missing Act.pdf
  - Parent act not found: "Non-existent Act" (referenced by 3 regulations)
  - Duplicate filename: SOR-2002-184.pdf (appears 2 times)
```

---

### Step 2.4: Manifest Backups

Manifests are automatically backed up before modification:

```bash
# List backups
ls data/raw/manifest.backup.*.yaml

# Example backups
data/raw/manifest.backup.20251120_211551.yaml
data/raw/manifest.backup.20251120_212153.yaml
```

**Restore from Backup:**
```bash
# List available backups with index
python3 restore_manifest.py list

# Restore specific backup
python3 restore_manifest.py restore 1
```

---

## Phase 3: Ingestion Pipeline

### Step 3.1: Batch Ingestion (PDF → Bronze → Silver)

**Commands:**
```bash
# 1. Ingest acts & regulations
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error

# 2. Ingest FINTRAC guidance
python3 batch_ingest.py data/raw/fintrac_guidance_manifest.yaml --continue-on-error
```

**Note:** Since manifests are separate, run batch_ingest twice to process all documents.

**If Re-running After Errors:**
If you encountered issues during ingestion (corrupted data, wrong Bronze files used), clear Silver and re-run:
```bash
# Clear corrupted Silver data (Bronze is preserved)
rm -rf storage/silver/*

# Re-run ingestion (uses cached Bronze, fast)
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error
python3 batch_ingest.py data/raw/fintrac_guidance_manifest.yaml --continue-on-error
```

**What Happens:**

**Bronze Layer (PDF → Raw Text):**
1. Checks if Bronze already exists (idempotent)
2. If not: Extracts text via Adobe PDF Services API
3. Falls back to PyPDF2 if Adobe fails
4. Applies OCR for scanned documents
5. Saves raw text: `storage/bronze/{category}/{doc_id}/raw_text.txt`

**Silver Layer (Raw Text → Structured Sections):**
1. Loads Bronze text (or extracts PDF if Bronze missing)
2. Applies hybrid segmentation:
   - PDF bookmarks (table of contents)
   - Regex patterns (section numbers: 1, 1.1, 1.2.3)
   - Fallback: Fixed-size chunks
3. **Detects and tags Table of Contents sections** (`is_toc: true`)
4. Infers metadata (jurisdiction, regulator, topics)
5. Saves sections: `storage/silver/{category}/{doc_id}/sections.json`

**TOC Detection:**
- Identifies sections like "TABLE OF PROVISIONS", "TABLE ANALYTIQUE", "TABLE OF CONTENTS"
- Tags them with `is_toc: true` in metadata
- These sections are filtered out during embedding generation (Gold layer)
- Prevents TOC sections from polluting search results

**Flags:**
- `--continue-on-error`: Skip failures, process remaining docs
- `--skip-validation`: Skip manifest validation

**Performance:**
- **First run (PDF → Bronze → Silver):** ~3 min/doc
- **Subsequent runs (Bronze → Silver):** ~15 sec/doc
- **Idempotent:** Safe to re-run (uses Bronze cache)

**Output:**
```
Processing 46 documents from manifest.yaml...

[1/46] Bank Act
  ✓ Bronze exists (using cache)
  → Segmenting sections...
  ✓ 501 sections extracted → storage/silver/act/bank_act_1991/

[2/46] PCMLTFA
  → Extracting PDF via Adobe API...
  ✓ Bronze created → storage/bronze/act/pcmltfa_2000/
  → Segmenting sections...
  ✓ 425 sections extracted → storage/silver/act/pcmltfa_2000/

...

✓ 46/46 documents processed
✓ 42 Bronze cached (instant)
✓ 4 new extractions (12 min)
✓ 10,432 total sections
```

---

### Step 3.2: Bronze → Silver Re-processing (Optional)

**Use Case:** You updated the segmentation algorithm and want to re-parse without re-extracting PDFs.

**Command:**
```bash
python3 bronze_to_silver.py
```

**What Happens:**
1. Scans `storage/bronze/` for all raw text files
2. Re-applies segmentation algorithm
3. Regenerates `storage/silver/` sections

**Benefits:**
- **10x faster** than full PDF extraction
- **No Adobe API credits** consumed
- **All Bronze files** processed in ~5 minutes

**When to Use:**
- Updated section parsing logic
- Changed metadata inference rules
- Testing new segmentation patterns
- Bronze exists but Silver is corrupted

---

### Step 3.3: Verify Ingestion

**Check Storage:**
```bash
# Count Bronze documents
ls storage/bronze/*/* -d | wc -l

# Count Silver documents
ls storage/silver/*/* -d | wc -l

# Check specific document
cat storage/silver/act/pcmltfa_2000/sections.json | jq '.sections | length'
```

**Expected Output:**
```
Bronze: 46 documents
Silver: 46 documents
PCMLTFA sections: 425
```

**Browse Silver via Dashboard:**
```bash
./run_dashboard.sh
# Navigate to 🔷 Silver Layer page
```

---

## Phase 4: Embeddings & Search

### Step 4.1: Generate Embeddings (Silver → Gold)

**Command:**
```bash
python3 generate_embeddings.py
```

**What Happens:**
1. Loads all sections from `storage/silver/`
2. Generates 384-dim vectors using `sentence-transformers/all-MiniLM-L6-v2`
3. Builds FAISS index (cosine similarity)
4. Saves Gold layer:
   - `storage/gold/{doc_id}/embeddings.npy`
   - `storage/gold/{doc_id}/sections.json`
   - `storage/gold/{doc_id}/metadata.json`
5. Creates vector index:
   - `storage/vector_db/covenant.index` (FAISS index)
   - `storage/vector_db/id_to_section.json` (lookup table)
   - `storage/vector_db/index_metadata.json` (config)

**Performance:**
- ~500 sections/minute on CPU
- 10,432 sections = ~20 minutes
- GPU: 5x faster

**Output:**
```
Loading sections from Silver layer...
✓ 10,432 sections loaded from 46 documents

Generating embeddings (batch_size=32)...
████████████████████████████████ 10,432/10,432 (100%)

Building FAISS index...
✓ Index created: 10,432 vectors (384 dimensions)
✓ Metric: Cosine similarity
✓ Index type: Flat (exact search)

Saving outputs...
✓ Gold layer: storage/gold/
✓ Vector index: storage/vector_db/covenant.index

✓ Embeddings generation complete!
```

---

### Step 4.2: Search (CLI)

**Command:**
```bash
python3 search/semantic_search.py "customer due diligence requirements"
```

**Output:**
```
Top 10 results for: "customer due diligence requirements"

1. [Score: 0.8247] FINTRAC - Methods to Verify Identity
   Section 3.2: Customer Due Diligence Procedures
   Category: guidance | Jurisdiction: federal

   "Customer due diligence (CDD) is the process of identifying your
   client and verifying their identity. You must conduct CDD when you
   enter into a business relationship, conduct certain transactions..."

2. [Score: 0.7983] PCMLTFA Regulations (SOR/2002-184)
   Section 54(1): Identification Requirements
   Category: regulation | Jurisdiction: federal

   "Every person or entity that is subject to the Act shall, in
   accordance with subsection 64(1), ascertain the identity of every
   person who conducts a transaction..."

...
```

**Options:**
- `--top-k 20` - Return top 20 results (default: 10)
- `--threshold 0.7` - Minimum similarity score (default: 0.0)
- `--category guidance` - Filter by category
- `--export results.json` - Export results

---

### Step 4.3: Search (Dashboard)

**Launch Dashboard:**
```bash
./run_dashboard.sh
```

**Navigate to 🔍 Search Page:**

**Features:**
- **Natural Language Queries:** "What are the PEP requirements for financial institutions?"
- **Relevance Scoring:** 0-1 similarity score
- **Advanced Filtering:**
  - Top-K results (1-50)
  - Minimum score threshold
  - Category filter (act, regulation, guidance)
- **Export:** Download results as JSON or CSV
- **Context View:** Expand results to see full section content + metadata

**Example Queries:**
```
"Money laundering reporting obligations for MSBs"
"Record keeping requirements for financial entities"
"Suspicious transaction reporting thresholds"
"Beneficial ownership identification methods"
"Travel rule for electronic funds transfers"
```

---

## 🔄 Common Workflows

### Workflow 1: Fresh Start (No Data)

**Scenario:** Starting from scratch, need complete FINTRAC PCMLTFA knowledge base.

```bash
# 1. Configure what to download
vim mapper_config.yaml

# 2. Download acts & regulations
python3 run_mapper_from_config.py

# 3. Scrape FINTRAC guidance
python3 scrape_fintrac.py data/raw/manifest.yaml --format html

# 4. Convert HTML to PDF (manual or automated)
# Manual: Open each HTML in browser → Print → Save as PDF
# Automated: python3 convert_html_to_pdf.py data/raw/guidance/fintrac/html/

# 5. Validate manifests
python3 validate_manifest.py data/raw/manifest.yaml
python3 validate_manifest.py data/raw/fintrac_guidance_manifest.yaml

# 6. Ingest documents (Bronze → Silver)
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error
python3 batch_ingest.py data/raw/fintrac_guidance_manifest.yaml --continue-on-error

# 7. Generate embeddings (Silver → Gold)
python3 generate_embeddings.py

# 8. Launch dashboard
./run_dashboard.sh
```

**Time:** 2-3 hours (first run)
**Result:** Full FINTRAC PCMLTFA knowledge base with semantic search

---

### Workflow 2: Add New Documents

**Scenario:** Already have system running, want to add new regulations.

```bash
# 1. Add new entries to mapper config
vim mapper_config.yaml
# Add: "SOR-2024-123" to regulation_slugs

# 2. Download new documents
python3 run_mapper_from_config.py
# Skips existing, downloads new

# 3. Validate updated manifest
python3 validate_manifest.py data/raw/manifest.yaml

# 4. Ingest new documents only
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error
# Idempotent: Skips existing Bronze files

# 5. Regenerate embeddings (includes new + existing)
python3 generate_embeddings.py

# 6. Search now includes new documents!
```

**Time:** 5-10 minutes per new document
**Result:** Incremental update without reprocessing existing docs

---

### Workflow 3: Update Segmentation Algorithm

**Scenario:** Improved section parsing logic, want to re-segment all documents.

```bash
# Option A: Fast re-processing (Bronze → Silver)
python3 bronze_to_silver.py
# Uses existing Bronze, regenerates Silver

# Option B: Full re-processing (PDF → Bronze → Silver)
python3 clear_storage.py  # Deletes Bronze + Silver
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error

# Regenerate embeddings
python3 generate_embeddings.py
```

**Time:**
- Option A: ~5 minutes (Bronze → Silver)
- Option B: ~2 hours (PDF → Bronze → Silver)

**Recommendation:** Use Option A unless Bronze is corrupted

---

### Workflow 4: Regenerate Silver with TOC Filtering

**Scenario:** Updated segmentation to filter Table of Contents sections, need to regenerate Silver layer.

```bash
# 1. Clear Acts/Regulations Silver layer (preserve FINTRAC guidance)
rm -rf storage/silver/acts/* storage/silver/regulations/*

# 2. Re-ingest with updated TOC detection
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error
# Uses Bronze cache (fast: ~25 min for 15 docs)

# 3. Clear Gold layer and vector DB (preserve faiss_manager.py code)
rm -rf storage/gold/*
rm -rf storage/vector_db/*.index storage/vector_db/*.json

# 4. Regenerate embeddings with TOC filtering
python3 generate_embeddings.py
# Expected: "⚠️  Filtered X TOC sections" messages

# 5. Test TOC filtering
python3 search/semantic_search.py "table of provisions"
# Expected: No results (TOC sections excluded)

python3 search/semantic_search.py "customer due diligence"
# Expected: Relevant sections, no TOC noise
```

**Time:** ~50 minutes total
- Clear Silver: 1 sec
- Re-ingest: ~25 min (Bronze cache)
- Clear Gold: 1 sec
- Regenerate embeddings: ~20 min

**Result:** TOC sections tagged and excluded from search results

**What Changed:**
- Silver sections now have `is_toc: true` metadata for TOC sections
- Gold layer filters out TOC during embedding generation
- Search results no longer polluted with "TABLE OF PROVISIONS" entries

---

### Workflow 5: Development/Testing

**Scenario:** Testing changes, don't want to process 46 documents.

```bash
# Use minimal test manifest (3 documents)
python3 batch_ingest.py data/raw/test_minimal.yaml --continue-on-error

# Generate embeddings
python3 generate_embeddings.py

# Test search
python3 search/semantic_search.py "customer identification"

# Launch dashboard
./run_dashboard.sh
```

**Time:** 10-15 minutes
**Documents:** 3 (PCMLTFA Act, PCMLTFA Regulations, FINTRAC Identity Guidance)
**Sections:** 1,019

**Use For:**
- Testing pipeline changes
- Debugging segmentation
- Demos and presentations
- CI/CD validation

---

## 🐛 Troubleshooting

### Issue: Mapper Download Fails

**Error:**
```
❌ Failed to download: Bank Act
ConnectionError: Unable to reach laws-justice.gc.ca
```

**Solutions:**
1. Check internet connection
2. Verify laws-justice.gc.ca is accessible
3. Wait 30 seconds and retry (rate limiting)
4. Check act name spelling in `mapper_config.yaml`

---

### Issue: Adobe API Quota Exceeded

**Error:**
```
❌ Adobe PDF extraction failed: Quota exceeded
Falling back to PyPDF2...
```

**Solution:**
```bash
# Continue processing (uses PyPDF2 fallback)
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error

# Check which docs used fallback
grep "PyPDF2" logs/ingestion.log

# Failed extractions will be in Bronze but may have lower quality
```

**Recommendation:** Upgrade Adobe API plan or process in batches

---

### Issue: Manifest Validation Fails

**Error:**
```
❌ Validation failed:
  - File not found: data/raw/guidance/FINTRAC - Accountants Guidance.pdf
```

**Solution:**
```bash
# Check if HTML needs to be converted to PDF
ls data/raw/guidance/fintrac/html/*.html

# Convert missing HTML to PDF
python3 convert_html_to_pdf.py data/raw/guidance/fintrac/html/

# Or convert manually (higher quality)
open data/raw/guidance/fintrac/html/FINTRAC\ -\ Accountants\ Guidance.html
# Print → Save as PDF → data/raw/guidance/

# Re-validate
python3 validate_manifest.py data/raw/manifest.yaml
```

---

### Issue: FAISS Segmentation Fault (macOS)

**Error:**
```
zsh: segmentation fault  python3 search/semantic_search.py "query"
```

**Solution:** Already fixed! Environment variables are set in:
- `storage/vector_db/faiss_manager.py`
- `ingestion/embed/embedder.py`
- `run_dashboard.sh`

If you still encounter issues:
```bash
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
python3 search/semantic_search.py "query"
```

---

### Issue: Search Index Not Found

**Error:**
```
❌ FAISS index not found: storage/vector_db/covenant.index
```

**Solution:**
```bash
# Generate embeddings
python3 generate_embeddings.py

# Verify index created
ls -lh storage/vector_db/covenant.index
```

---

### Issue: Slow First Ingestion

**Expected:** PDF extraction is slow (~3 min/doc for 46 docs = ~2 hours)

**Solutions:**
1. Use `--continue-on-error` to process in batches
2. Start with `test_minimal.yaml` (3 docs, 10 min)
3. Subsequent runs are 10x faster (uses Bronze cache)
4. Use `bronze_to_silver.py` for re-processing

---

### Issue: Streamlit Can't Find Index

**Error in Dashboard:**
```
❌ FAISS index not found: storage/vector_db/covenant.index
Run: python3 generate_embeddings.py
```

**Solution:** Use the launcher script (sets correct paths):
```bash
./run_dashboard.sh
```

**Don't run:** `streamlit run dashboard/app.py` (wrong working directory)

---

## 📊 Current System Stats

**As of 2025-11-21:**

| Layer | Documents | Sections | Size |
|-------|-----------|----------|------|
| Source PDFs | 46 | N/A | ~150 MB |
| Bronze | 46 | N/A | ~25 MB |
| Silver | 46 | 10,432 | ~45 MB |
| Gold | 46 | 10,432 | ~16 MB |
| Vector Index | 1 | 10,432 | 16 MB |

**Documents in manifest.yaml:**
- Acts: 4 (Bank Act, PCMLTFA, PIPEDA, CDIC Act)
- Regulations: 9 (PCMLTFA regs, Bank regs, PIPEDA reg)
- Guidance: 33 (All FINTRAC sector + topic guidance)
- **Total: 46 documents**

**Documents in test_minimal.yaml:**
- Acts: 1 (PCMLTFA)
- Regulations: 1 (PCMLTFA Regulations)
- Guidance: 1 (FINTRAC Identity Methods)
- **Total: 3 documents, 1,019 sections**

---

## 📂 Directory Structure

```
covenant_systems/
├── data/raw/                      # Source documents + manifests
│   ├── acts/                      # Downloaded acts (PDFs)
│   ├── regulations/               # Downloaded regulations (PDFs)
│   ├── guidance/                  # Guidance documents (PDFs)
│   │   └── fintrac/
│   │       └── html/              # Scraped HTML (before conversion)
│   ├── manifest.yaml              # Master manifest (46 docs)
│   ├── milestone_1_fintrac_pcmltfa.yaml  # PCMLTFA manifest (36 docs)
│   ├── milestone_1_fintrac_guidance_only.yaml  # Guidance only (33 docs)
│   └── test_minimal.yaml          # Test manifest (3 docs)
│
├── storage/
│   ├── bronze/                    # Raw extracted text
│   │   └── {category}/{doc_id}/raw_text.txt
│   ├── silver/                    # Structured sections
│   │   └── {category}/{doc_id}/sections.json
│   ├── gold/                      # Embeddings per document
│   │   └── {doc_id}/
│   │       ├── embeddings.npy
│   │       ├── sections.json
│   │       └── metadata.json
│   └── vector_db/                 # FAISS index (global)
│       ├── covenant.index
│       ├── id_to_section.json
│       └── index_metadata.json
│
├── ingestion/                     # ETL pipeline
│   ├── extract/                   # PDF extraction
│   ├── segment/                   # Section parsing
│   └── embed/                     # Embedding generation
│
├── search/                        # Search engine
│   └── semantic_search.py
│
├── dashboard/                     # Streamlit UI
│   ├── app.py
│   └── pages/
│       ├── 1_📤_Upload.py
│       ├── 2_🔷_Silver_Layer.py
│       └── 3_🔍_Search.py
│
├── mapper_config.yaml             # Download configuration
├── run_mapper_from_config.py      # Act/regulation downloader
├── scrape_fintrac.py              # FINTRAC guidance scraper
├── convert_html_to_pdf.py         # HTML → PDF converter
├── batch_ingest.py                # Main ingestion script
├── bronze_to_silver.py            # Re-processing script
├── generate_embeddings.py         # Embeddings generator
├── validate_manifest.py           # Manifest validator
├── clear_storage.py               # Storage cleanup utility
└── run_dashboard.sh               # Dashboard launcher
```

---

## ✅ Quick Command Reference

| Task | Command |
|------|---------|
| **Data Gathering** | |
| Configure downloads | `vim mapper_config.yaml` |
| Download acts/regs | `python3 run_mapper_from_config.py` |
| Scrape FINTRAC guidance | `python3 scrape_fintrac.py data/raw/fintrac_guidance_manifest.yaml --format html` |
| Convert HTML to PDF | `python3 convert_html_to_pdf.py` |
| **Manifests** | |
| Validate main manifest | `python3 validate_manifest.py data/raw/manifest.yaml` |
| Validate guidance manifest | `python3 validate_manifest.py data/raw/fintrac_guidance_manifest.yaml` |
| List backups | `python3 restore_manifest.py list` |
| Restore backup | `python3 restore_manifest.py restore 1` |
| **Ingestion** | |
| Process acts/regs | `python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error` |
| Process guidance | `python3 batch_ingest.py data/raw/fintrac_guidance_manifest.yaml --continue-on-error` |
| Re-process Silver | `python3 bronze_to_silver.py` |
| Clear storage | `python3 clear_storage.py` |
| **Embeddings & Search** | |
| Generate embeddings | `python3 generate_embeddings.py` |
| Search (CLI) | `python3 search/semantic_search.py "query"` |
| Launch dashboard | `./run_dashboard.sh` |

---

## 🎯 Next Steps

**Completed Milestones:**
- ✅ Data gathering pipeline (mapper + scraper)
- ✅ Manifest management (validation + backups)
- ✅ Bronze → Silver → Gold pipeline
- ✅ Semantic search (FAISS + sentence-transformers)
- ✅ Streamlit dashboard
- ✅ Idempotent ingestion

**Upcoming Features:**
- 🔄 RAG Q&A Assistant (LLM-powered answers with citations)
- 🔄 Obligations Extraction (identify requirements, prohibitions, permissions)
- 🔄 Knowledge Graph (relationship mapping between regulations)
- 🔄 Gap Analysis (policy vs regulation comparison)
- 🔄 Controls Library (regulatory controls mapping)

---

## 📚 Additional Documentation

- **Project Specification:** [CLAUDE.md](CLAUDE.md) - Full system architecture
- **Manifest Guide:** [docs/MANIFEST_GUIDE.md](docs/MANIFEST_GUIDE.md) - Detailed manifest comparison
- **Manifest Recovery:** [docs/MANIFEST_RECOVERY.md](docs/MANIFEST_RECOVERY.md) - Backup/restore procedures
- **Dashboard Architecture:** [docs/CUSTOMER_DASHBOARD_ARCHITECTURE.md](docs/CUSTOMER_DASHBOARD_ARCHITECTURE.md) - UI design

---

**Questions?** Check the detailed architecture in [CLAUDE.md](CLAUDE.md) or review specific module documentation in the codebase.
