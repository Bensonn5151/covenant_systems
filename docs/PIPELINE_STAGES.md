# Pipeline Stages Documentation

Visual documentation of data transformation at each stage.

---

## Stage 0: Input (Raw PDF)

```
┌─────────────────────────────────────┐
│  bank_act_canada.pdf                │
│                                     │
│  📄 Bilingual PDF                   │
│  ├─ English (left column)           │
│  └─ French (right column)           │
│                                     │
│  Size: 2.3 MB                       │
│  Pages: 245                         │
└─────────────────────────────────────┘
```

**Tools Used:**
- File system access
- PDF metadata reader

---

## Stage 1: BRONZE LAYER (Raw Extraction)

### Input → Bronze Transformation

```
PDF → pdfplumber (detect columns) → PyMuPDF (extract left) → Bronze
```

### Bronze Output Structure

```
storage/bronze/bank_act_canada/
├── raw_text.txt                  ← Extracted English text (verbatim)
└── metadata.json                 ← Extraction metadata
```

### Sample Bronze Files

**raw_text.txt** (first 300 chars):
```
Bank Act

PART I
INTERPRETATION

Marginal note:Short title
1. This Act may be cited as the Bank Act.

Marginal note:Definitions
2. (1) In this Act,
bank means a body corporate to which this Act applies...
```

**metadata.json**:
```json
{
  "document_id": "bank_act_canada",
  "source_file": "storage/bronze/bank_act_canada.pdf",
  "file_size_bytes": 2411723,
  "file_hash": "a7f3d2e89c1b5f4e3a2d8c9b7e6f5a4d3c2b1a0e9f8d7c6b5a4e3d2c1b0a9f8e",
  "page_count": 245,
  "char_count": 782450,
  "extraction_date": "2024-11-16T19:30:00Z",
  "extraction_method": "bilingual_column",
  "column_boundary": 306.5
}
```

**Data Characteristics:**
- ✅ **Zero transformation**: Text exactly as extracted
- ✅ **Complete**: All English content preserved
- ✅ **Reproducible**: Hash ensures integrity
- ❌ **No structure**: Plain text, no sections yet

---

## Stage 2: SILVER LAYER (Structured Sections)

### Bronze → Silver Transformation

```
Raw Text → Regex Pattern Matching → Section Segmentation → Silver
           ├─ "PART I"
           ├─ "Section 1"
           ├─ "1.", "2.", "3."
           └─ "1.1", "2.3.4"
```

### Silver Output Structure

```
storage/silver/bank_act_canada/
├── sections.json                 ← Array of structured sections
└── metadata.json                 ← Document metadata
```

### Sample Silver Files

**sections.json** (excerpt):
```json
[
  {
    "section_id": "bank_act_canada_s001",
    "section_number": "1",
    "title": "Short title",
    "body": "This Act may be cited as the Bank Act.",
    "level": 3,
    "parent_id": null,
    "start_char": 45,
    "end_char": 89,
    "metadata": {
      "document_id": "bank_act_canada",
      "document_type": "Act",
      "jurisdiction": "Canada",
      "source_file": "storage/bronze/bank_act_canada.pdf",
      "processed_date": "2024-11-16T19:30:15Z"
    }
  },
  {
    "section_id": "bank_act_canada_s002",
    "section_number": "2",
    "title": "Definitions",
    "body": "(1) In this Act,\n\nbank means a body corporate to which this Act applies pursuant to section 14;\n\nbanking means the business of banking as defined in subsection 2.4(1)...",
    "level": 3,
    "parent_id": null,
    "start_char": 90,
    "end_char": 3542,
    "metadata": {
      "document_id": "bank_act_canada",
      "document_type": "Act",
      "jurisdiction": "Canada",
      "source_file": "storage/bronze/bank_act_canada.pdf",
      "processed_date": "2024-11-16T19:30:15Z"
    }
  }
]
```

**metadata.json**:
```json
{
  "document_id": "bank_act_canada",
  "document_type": "Act",
  "jurisdiction": "Canada",
  "regulator": "OSFI",
  "source_url": "https://laws-lois.justice.gc.ca/eng/acts/B-1.01/",
  "version": "2024-01",
  "section_count": 1087,
  "topics": ["Banking", "Financial Regulation", "Federal Law"],
  "processed_date": "2024-11-16T19:30:15Z"
}
```

**Data Characteristics:**
- ✅ **Structured**: Sections clearly delineated
- ✅ **Queryable**: Can search by section number
- ✅ **Hierarchical**: Parent-child relationships
- ✅ **Metadata enriched**: Type, jurisdiction inferred
- ✅ **Verbatim content**: `body` unchanged from Bronze
- ❌ **No semantic labels**: No obligation/risk classification yet

---

## Stage 3: GOLD LAYER (Semantic Intelligence)

### Silver → Gold Transformation

```
Sections → Embedding Model → Vector DB → Classifiers → Gold
           (sentence-transformers)  (FAISS)    (LLM/ML)

           ├─ Generate embeddings (384-dim vectors)
           ├─ Classify obligations (obligation/permission/prohibition)
           ├─ Extract entities (dates, amounts, references)
           └─ Map relationships (cites, requires, conflicts)
```

### Gold Output Structure (Proposed)

```
storage/gold/bank_act_canada/
├── embeddings.npy                ← NumPy array (1087 × 384)
├── sections.json                 ← Sections with semantic labels
├── metadata.json                 ← Model info + label stats
└── faiss.index                   ← FAISS vector index
```

### Sample Gold Files (Proposed)

**sections.json** (excerpt):
```json
[
  {
    "section_id": "bank_act_canada_s006",
    "section_number": "6",
    "title": "Restriction on carrying on business",
    "body": "A bank shall not carry on business as a bank, except in accordance with this Act.",

    "embedding": [0.023, -0.145, 0.089, ... (384 values)],
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dimension": 384,

    "semantic_labels": {
      "obligation_type": "prohibition",
      "risk_level": "high",
      "operational_area": "licensing",
      "enforceability": true,
      "confidence": 0.92
    },

    "relationships": [
      {
        "target_section_id": "bank_act_canada_s014",
        "relationship_type": "references",
        "confidence": 0.87
      }
    ],

    "extracted_entities": {
      "obligations": ["shall not carry on business"],
      "conditions": ["except in accordance with this Act"],
      "references": ["this Act"]
    }
  }
]
```

**metadata.json**:
```json
{
  "document_id": "bank_act_canada",
  "embedding_stats": {
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "dimension": 384,
    "total_sections": 1087,
    "avg_similarity": 0.42,
    "embedding_date": "2024-11-16T19:35:00Z"
  },
  "label_distribution": {
    "obligation": 342,
    "prohibition": 128,
    "permission": 89,
    "definition": 156,
    "procedural": 372
  },
  "risk_distribution": {
    "critical": 23,
    "high": 145,
    "medium": 398,
    "low": 521
  }
}
```

**Data Characteristics:**
- ✅ **Semantic vectors**: Ready for similarity search
- ✅ **Classified**: Obligation types labeled
- ✅ **Risk-scored**: Sections prioritized by risk
- ✅ **Relationships mapped**: Cross-references identified
- ✅ **RAG-ready**: Can be queried with natural language
- ✅ **Explainable**: Confidence scores included

---

## Data Flow Summary

```
┌──────────────┐
│   Raw PDF    │ 245 pages, 2.3 MB
└──────┬───────┘
       │ Extract (pdfplumber + PyMuPDF)
       ▼
┌──────────────┐
│    BRONZE    │ 782K chars, plain text
│  raw_text    │ ✓ Verbatim  ✓ Hash verified
└──────┬───────┘
       │ Segment (regex patterns)
       ▼
┌──────────────┐
│    SILVER    │ 1,087 sections, structured JSON
│  sections    │ ✓ Parsed  ✓ Metadata enriched
└──────┬───────┘
       │ Embed + Classify (ML models)
       ▼
┌──────────────┐
│     GOLD     │ 1,087 vectors (384-dim each)
│  embeddings  │ ✓ Semantic  ✓ RAG-ready
└──────────────┘
```

---

## Quality Metrics at Each Stage

| Stage  | Metric | Target | Measurement |
|--------|--------|--------|-------------|
| Bronze | Hash integrity | 100% | SHA-256 verification |
| Bronze | Text coverage | >95% | Chars extracted / PDF chars |
| Silver | Section detection | >90% | Sections found / Expected sections |
| Silver | Hierarchy accuracy | >85% | Correct parent-child links |
| Gold | Embedding quality | >0.7 | Avg cosine similarity to ground truth |
| Gold | Label confidence | >0.75 | Avg confidence score |

---

## Example: End-to-End for One Section

### Input (PDF)
```
Page 15, Column 1 (English):
"6. A bank shall not carry on business as a bank, except in accordance with this Act."
```

### Bronze
```
File: storage/bronze/bank_act_canada/raw_text.txt
Content: "6. A bank shall not carry on business as a bank, except in accordance with this Act."
```

### Silver
```json
{
  "section_id": "bank_act_canada_s006",
  "section_number": "6",
  "title": "Restriction on carrying on business",
  "body": "A bank shall not carry on business as a bank, except in accordance with this Act.",
  "level": 3
}
```

### Gold
```json
{
  "section_id": "bank_act_canada_s006",
  "embedding": [0.023, -0.145, ...],
  "semantic_labels": {
    "obligation_type": "prohibition",
    "risk_level": "high",
    "confidence": 0.92
  }
}
```

### Queryable Result
```
User Query: "Can a bank operate without a license?"
Retrieved Section: bank_act_canada_s006 (similarity: 0.87)
Answer: "No. Section 6 states: A bank shall not carry on business as a bank,
         except in accordance with this Act."
```

---

## References
- See `DATA_STANDARDS.md` for detailed schemas
- See `CLAUDE.md` for architectural rules
- See `README.md` for system overview