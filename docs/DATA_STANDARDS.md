# Data Standards & Schema Documentation

This document defines the data formats, schemas, and standards used at each layer of the Covenant Systems pipeline.

---

## Overview: Bronze → Silver → Gold Architecture

```
Bronze (Raw)  →  Silver (Structured)  →  Gold (Semantic)
   ↓                    ↓                      ↓
Plain text         JSON sections          Embeddings + Labels
```

---

## 1. BRONZE LAYER - Raw Storage

### Purpose
Store documents **exactly as ingested** with zero transformation.

### Format
- **Text Files**: UTF-8 encoded `.txt`
- **Metadata**: JSON (ISO 8601 dates, SHA-256 hashes)

### Directory Structure
```
storage/bronze/
└── <document_id>/
    ├── raw_text.txt          # Extracted text (verbatim)
    ├── metadata.json         # File-level metadata only
    └── source.pdf            # Original PDF (optional)
```

### Metadata Schema (Bronze)

```json
{
  "document_id": "string (required)",
  "source_file": "string (path to original)",
  "file_size_bytes": "integer",
  "file_hash": "string (SHA-256 hex)",
  "page_count": "integer",
  "char_count": "integer",
  "extraction_date": "string (ISO 8601 UTC)",
  "extraction_method": "string (pdfplumber | pypdf2 | ocr | bilingual_column)",
  "column_boundary": "float (optional, for bilingual PDFs)"
}
```

### Standards Reference
- **Character Encoding**: UTF-8 (RFC 3629)
- **Hashing**: SHA-256 (FIPS 180-4)
- **Timestamps**: ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)

### Bronze Rules
❌ **No interpretation**
❌ **No summarization**
❌ **No structural inference**
✅ **Preserve verbatim**
✅ **Log extraction metadata only**

---

## 2. SILVER LAYER - Structured Sections

### Purpose
Transform raw text into **standardized, queryable structured chunks**.

### Format
- **Sections File**: JSON array of section objects
- **Metadata**: JSON (document-level enrichment)

### Directory Structure
```
storage/silver/
└── <document_id>/
    ├── sections.json         # All sections (array)
    └── metadata.json         # Document metadata
```

### Section Schema (Silver)

```json
{
  "section_id": "string (required, unique, format: <doc_id>_s001)",
  "section_number": "string (e.g., '1', '1.1', '5.2.3')",
  "title": "string (section heading/title)",
  "body": "string (section content, verbatim)",
  "level": "integer (1=Part, 2=Division, 3=Section, 4=Subsection)",
  "parent_id": "string | null (hierarchical parent)",
  "start_char": "integer (character offset in original text)",
  "end_char": "integer (character offset in original text)",
  "metadata": {
    "document_id": "string",
    "document_type": "string (Act | Regulation | Guideline | Policy | Standard)",
    "jurisdiction": "string (Canada | United States | United Kingdom | EU)",
    "source_file": "string",
    "processed_date": "string (ISO 8601 UTC)"
  }
}
```

### Document Metadata Schema (Silver)

```json
{
  "document_id": "string (required)",
  "document_type": "string (Act | Regulation | Guideline | Policy | Standard)",
  "jurisdiction": "string",
  "regulator": "string (optional, e.g., OSFI, SEC, FCA)",
  "effective_date": "string (ISO 8601, optional)",
  "last_amended": "string (ISO 8601, optional)",
  "version": "string (e.g., '1.0', '2024-R1')",
  "source_url": "string (optional)",
  "topics": ["array of strings (AML, Privacy, Cybersecurity, etc.)"],
  "section_count": "integer",
  "processed_date": "string (ISO 8601 UTC)"
}
```

### Standards Reference
- **Document Types**: Custom taxonomy (aligned with legal document categories)
- **Jurisdictions**: ISO 3166-1 alpha-2 codes + full names
- **Numbering**: Hierarchical section numbering (legal convention)

### Silver Rules
✅ **Deterministic segmentation**
✅ **Metadata inference allowed**
✅ **Structural normalization**
✅ **Preserve legal text verbatim in `body` field**
❌ **No semantic interpretation**
❌ **No opinions or summaries**

---

## 3. GOLD LAYER - Semantic Intelligence

### Purpose
Make content **ready for intelligent reasoning** with embeddings, classifications, and relationships.

### Format
- **Embeddings**: NumPy arrays or binary vectors
- **Metadata**: JSON with semantic labels
- **Index Files**: FAISS index files

### Directory Structure (Proposed)
```
storage/gold/
└── <document_id>/
    ├── embeddings.npy        # NumPy array (N sections × 384 dims)
    ├── sections.json         # Sections with semantic labels
    └── metadata.json         # Model info + labels
```

### Gold Section Schema (Proposed)

```json
{
  "section_id": "string (same as Silver)",
  "embedding": "[array of floats, length = embedding_dimension]",
  "embedding_model": "string (e.g., 'sentence-transformers/all-MiniLM-L6-v2')",
  "embedding_dimension": "integer (e.g., 384)",

  "semantic_labels": {
    "obligation_type": "string (obligation | permission | prohibition | definition | null)",
    "risk_level": "string (critical | high | medium | low | unknown)",
    "operational_area": "string (compliance | risk | audit | governance | operations)",
    "enforceability": "boolean (is this enforceable?)",
    "confidence": "float (0.0-1.0, confidence in labels)"
  },

  "relationships": [
    {
      "target_section_id": "string",
      "relationship_type": "string (cites | requires | conflicts_with | amends)",
      "confidence": "float (0.0-1.0)"
    }
  ],

  "extracted_entities": {
    "dates": ["array of ISO 8601 dates"],
    "amounts": ["array of monetary amounts"],
    "references": ["array of cited regulations/sections"]
  }
}
```

### Standards Reference
- **Embeddings**: Dense vectors (sentence-transformers standard)
- **Vector Format**: IEEE 754 floating-point
- **Similarity Metric**: Cosine similarity (normalized dot product)

### Gold Rules
✅ **Interpretation allowed**
✅ **Obligation extraction**
✅ **Risk classification**
✅ **Relationship mapping**
✅ **High-confidence labels only** (threshold: 0.75)
⚠️ **Uncertain labels → `uncertain_labels` field**

---

## 4. Knowledge Graph

### Format
**YAML** (human-readable, LLM-friendly, version-controllable)

### Schema

**nodes.yaml**
```yaml
- id: "BA-6-1"
  type: "regulation"
  act: "Bank Act"
  section: "6(1)"
  domains: ["banking", "licensing"]
  text: "A bank shall not..."
  metadata:
    risk_level: "high"
    enforceable: true
    effective_date: "2024-01-01"
```

**edges.yaml**
```yaml
- from: "BA-6-1"
  to: "PCMLTFA-9"
  type: "requires_alignment"
  description: "Licensing triggers AML requirements"
  confidence: 0.85
```

**domains.yaml**
```yaml
domains:
  - name: "Anti-Money Laundering (AML)"
    abbreviation: "AML"
    regulators: ["FINTRAC", "FinCEN"]

  - name: "Privacy & Data Protection"
    abbreviation: "Privacy"
    regulators: ["OPC", "ICO", "CNIL"]
```

---

## 5. Comparison to Industry Standards

### Akoma Ntoso (XML for legislative documents)
- **Used by**: EU Parliament, African Union, UK Parliament
- **Format**: XML with strict schema
- **Our approach**: JSON (more ML-friendly, easier to parse)
- **Interoperability**: Can export to Akoma Ntoso if needed

### LegalRuleML
- **Purpose**: Machine-readable legal rules
- **Format**: XML-based
- **Our approach**: JSON with semantic labels
- **Mapping**: Our `obligation_type` maps to LegalRuleML rule types

### Dublin Core Metadata
- **Purpose**: Standard metadata elements
- **Our mapping**:
  - `dc:title` → `title`
  - `dc:identifier` → `document_id`
  - `dc:date` → `effective_date`
  - `dc:coverage` → `jurisdiction`
  - `dc:type` → `document_type`

---

## 6. Versioning & Change Management

### Document Versioning
Every document includes:
```json
{
  "document_id": "bank_act_canada",
  "version": "1.0",
  "version_date": "2024-01-15T00:00:00Z",
  "hash": "sha256:abc123...",
  "supersedes": "bank_act_canada@0.9",
  "changelog": "Added sections 15-18"
}
```

### Schema Versioning
All JSON schemas include:
```json
{
  "schema_version": "1.0.0",
  "schema_name": "covenant_silver_section"
}
```

---

## 7. Quality Assurance

### Validation Rules

**Bronze:**
- UTF-8 encoding validation
- Hash verification (SHA-256)
- File size > 0

**Silver:**
- JSON schema validation
- Required fields present
- Section numbering consistency
- No empty `body` fields
- Character count > `min_section_length`

**Gold:**
- Embedding dimension matches model
- Confidence scores in [0.0, 1.0]
- Vector norms validated (if normalized)

---

## 8. Export Formats

We can export to multiple formats:

| Format | Use Case | Implementation Status |
|--------|----------|----------------------|
| JSON | Default, ML pipelines | ✅ Implemented |
| JSONL | Streaming, large datasets | 🔄 Planned |
| Parquet | Analytics, data science | 🔄 Planned |
| CSV | Simple analysis | 🔄 Planned |
| XML (Akoma Ntoso) | Interoperability | 🔄 Planned |
| RDF/Turtle | Knowledge graphs | 🔄 Planned |

---

## References

- **ISO 8601**: Date/time format
- **RFC 3629**: UTF-8 encoding
- **FIPS 180-4**: SHA-256 hashing
- **IEEE 754**: Floating-point arithmetic
- **JSON Schema**: http://json-schema.org/
- **Akoma Ntoso**: http://www.akomantoso.org/
- **Dublin Core**: https://www.dublincore.org/