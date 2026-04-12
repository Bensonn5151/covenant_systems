# Covenant Systems — Regulatory Intelligence Platform

**Version:** 0.3.0 (Bronze → Silver → Gold → Knowledge Graph)  
**Last Updated:** 2026-04-02

---

## Overview

Covenant Systems is a **GraphRAG-powered regulatory intelligence engine** that automates compliance workflows for financial institutions. The platform ingests regulatory documents (Acts, Regulations, Guidance) and transforms them into a searchable knowledge base with semantic understanding and relationship mapping.

**Current Status**: Operational Bronze → Silver → Gold pipeline with semantic search capabilities.

---

## Quick Start

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

**Result**: Browse at http://localhost:8501
- 📤 Upload: Process new PDFs
- 🔷 Silver Layer: Browse structured sections
- 🔍 Search: Semantic search across all documents

---

## System Architecture

```
Data Sources (laws.justice.gc.ca, FINTRAC)
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
│ • TOC filtering (is_toc metadata)           │
│ • Metadata inference (jurisdiction, type)   │
│ Output: storage/silver/{category}/{doc_id}/ │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ GOLD LAYER (Embeddings)                     │
│ • sentence-transformers (384 dimensions)    │
│ • FAISS vector index (cosine similarity)    │
│ • TOC sections excluded from embeddings     │
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

## Current Capabilities

### ✅ Operational Features

1. **Automated Data Acquisition**
   - Legislative Mapper: Downloads Acts/Regulations from laws.justice.gc.ca
   - FINTRAC Scraper: Fetches guidance documents as HTML
   - HTML-to-PDF conversion for guidance documents

2. **Multi-Layer Data Pipeline**
   - **Bronze**: Raw text extraction (Adobe PDF Services + PyPDF2 fallback)
   - **Silver**: Structured sections with hierarchical numbering
   - **Gold**: 384-dimensional embeddings with FAISS indexing

3. **Semantic Search**
   - CLI: `python3 search/semantic_search.py "query"`
   - Dashboard: Interactive search UI with filtering
   - 22,402 sections indexed across 23 documents

4. **Document Coverage** (PCMLTFA-Focused)
   - 6 Acts (PCMLTFA, PIPEDA, Bank Act, CDIC Act, SEMA, Magnitsky Law)
   - 9 Regulations (PCMLTFA regs, sanctions, privacy)
   - 8 FINTRAC Guidance documents

5. **Knowledge Graph (Operational)**
   - 509 nodes and 121 edges across regulatory corpus
   - Cross-document relationship mapping (cites, requires, implements)
   - Domain taxonomy covering AML, KYC, PIPEDA, and more

6. **Bilingual Extraction Pipeline**
   - Spatial column clipping for side-by-side EN/FR Canadian PDFs
   - BilingualExtractor using pdfplumber + PyMuPDF (no API dependency)
   - Language-filtered output (English-only sections)

7. **Gold Layer Enrichment**
   - Classification labels (obligation, permission, prohibition)
   - Risk-level tagging per section
   - RAG-ready vectors with semantic labels

### 🚧 In Development

- Graph-augmented retrieval (semantic + graph traversal)
- Impact analysis engine (regulatory change detection)
- Explainable reasoning interface

---

## Data Architecture

### Bronze Layer (Raw Text)
- **Purpose**: Ground truth archive for audits
- **Content**: Raw text extracted from PDFs, no transformations
- **Storage**: `storage/bronze/{category}/{doc_id}/raw_text.txt`
- **Features**: OCR support, language filtering (English only)

### Silver Layer (Structured Sections)
- **Purpose**: Parsed, hierarchical regulatory content
- **Content**: Sections with metadata (title, number, hierarchy)
- **Storage**: `storage/silver/{category}/{doc_id}/sections.json`
- **Features**:
  - Hybrid segmentation (PDF bookmarks + regex patterns)
  - TOC detection and tagging (`is_toc: true`)
  - Metadata inference (jurisdiction, regulator, topics)

### Gold Layer (Embeddings)
- **Purpose**: Semantic search-ready vectors
- **Content**: 384-dim embeddings (sentence-transformers/all-MiniLM-L6-v2)
- **Storage**: 
  - `storage/gold/{doc_id}/embeddings.npy`
  - `storage/vector_db/covenant.index` (FAISS)
- **Features**:
  - TOC sections excluded from embeddings
  - Cosine similarity search
  - Batch processing (500 sections/min on CPU)

---

## Folder Structure

```
/
├── README.md
├── usage.md                    # Detailed operational guide
├── EXECUTIVE_SUMMARY.md        # Business/funding overview
├── mapper_config.yaml          # Acts/regulations to download

├── data/
│   └── raw/
│       ├── acts/               # Downloaded acts (PDFs)
│       ├── regulations/        # Downloaded regulations (PDFs)
│       ├── guidance/           # FINTRAC guidance (PDFs)
│       ├── manifest.yaml       # Master document registry
│       └── fintrac_guidance_manifest.yaml

├── ingestion/
│   ├── extract/                # PDF extraction (Adobe, PyPDF2)
│   ├── segment/                # Section segmentation
│   │   ├── advanced_segmenter.py
│   │   └── bookmark_segmenter.py
│   └── utils/

├── storage/
│   ├── bronze/                 # Raw text layer
│   ├── silver/                 # Structured sections layer
│   ├── gold/                   # Embeddings layer
│   └── vector_db/              # FAISS index
│       ├── covenant.index
│       ├── id_to_section.json
│       └── faiss_manager.py

├── search/
│   └── semantic_search.py      # CLI search tool

├── dashboard/                  # Streamlit UI
│   ├── app.py
│   └── pages/

└── web/                        # Next.js frontend (future)
```

---

## Knowledge Graph (Planned - Milestone 1)

### Purpose
The Knowledge Graph will enable:
- **Cross-document navigation**: Bank Act → OSFI Guidelines → Internal Policies
- **Relationship detection**: `cites`, `requires`, `implements`, `conflicts_with`
- **Context expansion**: Follow edges to find related sections during retrieval
- **Impact analysis**: Trace how regulatory changes cascade through compliance frameworks

### Node Types
- **regulation**: Sections from acts/regulations
- **clause**: Specific clauses/subsections
- **obligation**: Extracted requirements
- **prohibition**: Extracted restrictions
- **definition**: Legal term definitions

### Relationship Types
- `cites`: Section A references Section B
- `requires`: Section A mandates compliance with Section B
- `implements`: Policy implements regulation
- `conflicts_with`: Potential conflict detected
- `amends`: Regulation modifies another

### Storage Format
- `nodes.yaml`: Regulatory sections as graph nodes
- `edges.yaml`: Relationships between sections
- `domains.yaml`: Compliance domain taxonomy

---

## Search Capabilities

### Semantic Search (Operational)

**CLI Usage**:
```bash
python3 search/semantic_search.py "customer due diligence requirements"
```

**Dashboard Usage**:
```bash
./run_dashboard.sh
# Navigate to 🔍 Search page
```

**Features**:
- Natural language queries
- Relevance scoring (0-1 similarity)
- Category filtering (act, regulation, guidance)
- Top-K results (configurable)
- Export to JSON/CSV

**Example Queries**:
- "beneficial ownership identification requirements"
- "suspicious transaction reporting thresholds"
- "PEP screening obligations for banks"
- "record keeping requirements for MSBs"

### Hybrid Retrieval (Planned - Milestone 1)

Future enhancement combining:
1. Semantic search (current FAISS)
2. Graph traversal (follow KG edges)
3. Rank aggregation (merge results)
4. Reranking (cross-encoder precision boost)

---

## Configuration

### Mapper Configuration (`mapper_config.yaml`)

Defines which Acts and Regulations to download:

```yaml
# Acts to download (auto-discovers related regulations)
act_slugs:
  - "P-24.501"  # PCMLTFA
  - "P-8.6"     # PIPEDA
  - "B-1.01"    # Bank Act

# Specific regulations
regulation_slugs:
  - "SOR-2002-184"  # PCMLTFA Regulations
  - "SOR-2001-317"  # Suspicious Transaction Reporting
  - "SOR-2019-240"  # Virtual Currency Regulations

# Guidance priorities (for scraping)
guidance:
  fintrac:
    - "Guidance on the Risk-Based Approach"
    - "Methods to verify the identity of persons and entities"
    - "Beneficial ownership requirements"
```

---

## Development Roadmap

### ✅ Phase 1: Data Pipeline (Complete)
- Automated data acquisition (Legislative Mapper + FINTRAC Scraper)
- Bronze → Silver → Gold ingestion pipeline
- Semantic search with FAISS
- Dashboard UI (Streamlit)

### 🚧 Phase 2: GraphRAG MVP (In Progress - Milestone 1)
- Knowledge Graph construction
- Graph-augmented retrieval
- Impact analysis engine
- Explainable reasoning interface

### 📋 Phase 3: Enterprise Features (Planned)
- Multi-jurisdiction support (UK, US, EU)
- Policy gap analysis
- Compliance scoring engine
- Audit report generation
- FastAPI backend
- SOC 2 Type II certification

---

## Performance Metrics

**Current System**:
- Documents: 23 (6 Acts + 9 Regulations + 8 Guidance)
- Sections: 22,402 (after TOC filtering)
- Embedding dimension: 384
- Search latency: <1 second for top-10 results
- Ingestion speed: ~3 min/doc (first run), ~15 sec/doc (Bronze cached)

---

## Documentation

- **[usage.md](usage.md)**: Complete operational guide (data gathering, ingestion, search)
- **[EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)**: Business overview and funding milestones
- **[docs/MANIFEST_GUIDE.md](docs/MANIFEST_GUIDE.md)**: Manifest structure and validation

---

## Technology Stack

**Data Processing**:
- Adobe PDF Services API (text extraction)
- PyPDF2 (fallback extraction)
- Python 3.11+

**Embeddings & Search**:
- sentence-transformers (all-MiniLM-L6-v2)
- FAISS (vector indexing)
- NumPy (embedding storage)

**UI**:
- Streamlit (dashboard)
- Next.js (future web frontend)

**Infrastructure**:
- YAML (manifests, configuration)
- JSON (structured data)
- Git (version control)

---

## Testing with TestSprite

This project uses [TestSprite MCP](https://testsprite.com) for automated AI-driven testing.

### Test Results Summary

| Round | Pass Rate | Tests Passed | Tests Failed | Key Fixes |
|-------|-----------|-------------|-------------|-----------|
| Round 1 | 25% | 2/8 | 6/8 | Baseline |
| Round 2 | 62.5% | 5/8 | 3/8 | +email endpoint, +error codes, +path fixes |

**Bugs Found & Fixed:**
- Missing email signup endpoint on backend API
- Incorrect HTTP status codes for scrape error handling
- Undocumented default manifest paths causing test mismatches
- Semantic search engine per-request initialization (architectural issue identified)

**Test Coverage:** 8 backend API test cases covering ingestion, batch processing, legislation discovery, semantic search, knowledge graph, data validation, email signup, and web scraping.

All test cases and reports are in [`testsprite_tests/`](./testsprite_tests/).

---

## Project Structure

```
covenant_systems/
├── ingestion/              # ETL pipeline (extract, segment, classify, embed)
├── api/fastapi/            # REST API backend (FastAPI)
├── search/                 # Semantic search engine (FAISS)
├── storage/                # Bronze/Silver/Gold data layers + vector DB
├── dashboard/              # Streamlit analytics UI
├── web/                    # Next.js frontend
├── configs/                # Taxonomy, ontology, settings
├── data/raw/               # Source documents + manifests
├── testsprite_tests/       # AI-generated test cases (TestSprite MCP)
└── README.md
```

---

## License

Proprietary - Covenant Systems

---

## Contact

For investor materials, technical documentation, or partnership inquiries, contact the Covenant Systems team.
