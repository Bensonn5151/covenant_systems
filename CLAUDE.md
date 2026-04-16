# COVENANT SYSTEMS - AI Regulatory Compliance Specification

This document defines how Claude must behave inside this repository. It establishes the overall architecture, folder structure, and operational rules for the Legal AI Compliance Platform.

Claude must follow these instructions strictly.

## 1. Project Purpose
Build a full regulatory ingestion, normalization, and reasoning pipeline for:

	•	Acts
	•	Regulations
	•	Guidance documents
	•	Policies / Terms
	•	Internal documents
	•	PDFs, webpages, scanned materials

  The output is used for:

	•	Compliance mapping
	•	Section-level RAG
	•	Gap analysis
	•	Controls suggestions
	•	AI-assisted auditing
	•	Regtech automation

The system follows a Bronze → Silver → Gold layered architecture.

## 2. BRONZE–SILVER–GOLD ARCHITECTURE
### 2.1 Bronze (Raw Layer)

Goal: Store documents EXACTLY as ingested, with zero transformation.
  - Bronze: Raw files as ingested (PDFs, HTML, images) + minimal file-level metadata
  - Bronze OCR: If OCR is needed, store BOTH the original scanned file AND the OCR text output separately

Bronze contains:

	•	Raw PDFs
	•	Raw text dumps
	•	Raw HTML dumps
	•	Raw OCR output (if needed)
	•	JSON metadata only for file-level description, not interpretation
	•	No normalization
	•	No structure beyond simple metadata

Why can JSON appear in bronze?

Because the JSON is metadata, not processed content.


Bronze JSON = 
{
  "source": "CompanyX Privacy Policy",
  "document_type": "PrivacyAgreement",
  "jurisdiction": "unknown",
  "uploaded_by": "CompanyX",
  "date_uploaded": "2025-11-05"
}

Jurisdiction is not automatically inferred.
It is filled later in Silver after the model makes a determination.

### 2.2 Silver (Semantic Segmentation Layer)
Goal: Transform raw documents into standardized, queryable structured chunks.

Silver tasks:

	•	Apply OCR if the PDF is scanned
	•	Run automatic section segmentation
	•	Standardize:
	•	title
	•	section_number
	•	heading
	•	body_text
	•	Infer:
	•	document_type
	•	jurisdiction
	•	regulator
	•	topic_taxonomy (privacy, AML, cybersecurity, etc.)

Silver emits section-level JSON, e.g.:

{
  "document_id": "bank_act_2025",
  "section_id": "s-001",
  "section_number": "1",
  "title": "Short Title",
  "body": "This Act may be cited as...",
  "jurisdiction": "Canada",
  "topics": ["Banking", "Federal Law"]
}

### 2.3 Gold (Embedding + Interpretation Layer)

Goal: Make the content ready for intelligent reasoning.

Gold holds:

	•	High-quality embeddings per section
	•	Classifier labels about the text itself: obligation / permission / prohibition / definition / procedural
	•	severity_signal (obligations and prohibitions only) — a description of the regulation's language strength: definitional / procedural / mandatory / punitive. **This is not risk.** It characterizes how the law is written, not the consequences to any particular company.
	•	operational_areas — semantic tags (consent, breach_notification, etc.)
	•	Extraction-quality signals (confidence, needs_human_review, reason) — internal only; these must never surface on public regulation tiles or cards.
	•	Cross-document citation edges

Gold does **not** hold risk. Risk is relational — it lives only on the
`policy_implements_regulation` edge (see §11.4 and §13). Anything tagged
"high risk" without a named policy context is a bug.



## 3. WHEN TO APPLY OCR?

OCR is used when:
	•	PDF is scanned
	•	PDF contains only images
	•	No text layer exists
	•	Text extraction returns < 50 characters but file > 100KB

OCR is not used when:
	•	PDF already has extractable text
	•	It’s a digital regulation (most government sites)


## 4. HOW TO EXTRACT PDFS (CLAUDE INSTRUCTIONS)

Claude must:
	1.	Detect whether PDF contains text
	2.	If scanned → apply OCR
	3.	If bilingual (Canadian jurisdiction) → use BilingualExtractor for spatial column extraction
	4.	Extract content
	5.	Identify sections using hierarchical markers:
	•	“1.”, “2.”
	•	“1.1”, “1.2.3”
	•	“Section 5”
	•	“Part II”
	6.	Produce section-level JSON for Silver
	7.	Embed sections for Gold

If extractor fails → fallback to a large document splitter + manual section detection.

### 4.1 Bilingual Extraction (Canadian Documents)

Canadian government PDFs have English (left) and French (right) columns side-by-side.
These MUST be extracted using spatial column clipping, NOT language detection.

Extraction priority:
	1.	BilingualExtractor (ingestion/extract/bilingual_extractor.py) — pdfplumber + PyMuPDF, local, no API
	2.	Adobe PDF Services with extract_left_column_only=True — cloud API fallback
	3.	langdetect (ingestion/preprocessors/language_filter.py) — ONLY for documents where EN/FR are in separate paragraphs (e.g., HTML guidance docs). Does NOT work on side-by-side column PDFs.

See docs/PIPELINE_STAGES.md for detailed comparison and results.

## 5. FOLDER STRUCTURE

/
├── README.md                       # High-level overview & Claude instructions

├── data/                        # All source documents + validation sets
│   ├── regulations/                # Laws, regs, guidance
│   │   ├── raw/                    # Original PDFs, HTML, text
│   │   ├── processed/              # Parsed sections
│   │   └── metadata/               # Inferred metadata
│   ├── policies/                   # Customer/internal policies
│   │   ├── raw/
│   │   └── processed/
│   └── validation/                 # Evaluation datasets
│       ├── expert/                 # Human-labeled examples
│       ├── synthetic/              # AI-generated cases
│       └── benchmarks/             # Fixed evaluation suite

├── ingestion/                   # ETL: ingest → parse → segment → embed
│   ├── airflow_dags/
│   ├── extract/                    # API/web scrapers
│   ├── ocr/                        # OCR utilities
│   ├── transform/                  # Cleaning, splitting
│   ├── segment/                    # Chunking strategies
│   ├── embed/                      # Embedding generation
│   └── utils/

storage/                            # Data lake + indexing layer
│
├── bronze/                         # Raw extracted artifacts
│   ├── pdf/                        # Raw PDFs (original source)
│   ├── text/                       # Raw OCR / text dumps
│   ├── metadata/                   # Auto-captured metadata (source, date, etc.)
│   └── logs/                       # Extraction logs
│
├── silver/                         # Clean structured data
│   ├── sections/                   # Parsed legal sections/clauses
│   ├── json/                       # Normalized JSON output
│   ├── tables/                     # Tabular forms (for SQL)
│   └── validation/                 # Validation reports
│
├── gold/                           # ML-ready enriched layers
│   ├── embeddings/                 # Embeddings from LLM models
│   ├── semantic_labels/            # Domain tags, classifications
│   ├── summaries/                  # LLM long-context summaries
│   └── canonical/                  # Canonicalized unified regulation format
│
├── knowledge_graph/                # Regulatory knowledge graph (YAML-driven)
│   ├── nodes.yaml                  # All sections, clauses, policies as nodes
│   ├── edges.yaml                  # Cross-references & relationships
│   ├── domains.yaml                # Compliance taxonomy (AML, KYC, PIPEDA, etc.)
│   └── embeddings/                 # Vectorized KG nodes (for hybrid RAG)
│
├── postgres/                       # Relational warehouse layer
│   ├── ddl/                        # Database schema + migrations
│   ├── seeds/                      # Initial seed data
│   └── queries/                    # Prebuilt SQL queries/views
│
├── vector_db/                      # Vector database layer
│   ├── qdrant/                     # Qdrant config + collections
│   └── faiss/                      # FAISS indexes (local)
│
└── hybrid/                         # Hybrid search indexes
    ├── bm25/                       # BM25/Elasticsearch or Lucene indexes
    ├── rerankers/                  # Cross-encoder / LLM rerankers
    └── pipelines/                  # Retrieval pipelines configs

├── ai/                          # Retrieval, reasoning, evaluation
│   ├── retrieval/                  # Multi-stage retrieval
│   │   ├── semantic.py
│   │   ├── lexical.py
│   │   ├── hybrid.py
│   │   └── rerank.py
│   ├── reasoning/                  # Explainable reasoning
│   │   ├── trace.py
│   │   ├── builder.py
│   │   └── evidence.py
│   ├── agents/                     # Agentic workflows
│   │   ├── workflows/
│   │   └── steps/
│   ├── evaluation/                 # Evaluators + metrics
│   ├── models/                     # Prompts + fine-tuning
│   └── comparison/                 # Policy ↔ regulation comparison logic

├── api/                         # Backend + endpoints
│   ├── fastapi/                    # REST API
│   │   ├── routes/
│   │   └── schemas/
│   └── tests/                      # Integration tests

├── dashboard/                   # Analytics & UI
│   ├── dashboards/                 # Streamlit/PowerBI
│   ├── components/                 # React components
│   └── audit/                      # Compliance audit visualizations

└── configs/                        # All configurations
    ├── settings.yaml
    ├── retrieval_modes.yaml
    ├── thresholds.yaml
    └── .env.example

## 6. CLAUDE INSTRUCTIONS (VERY IMPORTANT)

Claude MUST follow these rules when interacting with this repo:

### 6.1 DO NOT hallucinate missing metadata

If jurisdiction cannot be inferred, set it to:

"jurisdiction": "unknown"

### 6.2 Do not create laws that do not exist

### 6.3 Do not summarize inside Bronze
Bronze is raw only

### 6.4 Silver must be deterministically structured
	•	No interpretation
	•	No opinions
	•	Only structural segmentation + metadata inference

### 6.5 Gold allows interpretation

Gold is where:

	•	reasoning
	•	obligations extraction
	•	compliance mapping
	•	control suggestions
are allowed.

### 6.6 Maintain 1:1 mapping between Silver and Gold sections

Every Silver section must produce exactly one Gold vector.

### 6.7 Always log failures

If Claude cannot parse something:

{
  "error": "segmentation_failed",
  "reason": "irregular numbering format"
}

## 7. SCOPE OF PROJECT

Regulatory Sources

	•	Canada (Bank Act, PCMLTFA, PIPEDA, OSFI B-series guidelines)
	•	U.S. (GLBA, SOX, NYDFS 500, etc.)
	•	UK (GDPR UK, FCA regs)
	•	EU (EBA, EIOPA, GDPR)

Use Cases

	•	Compliance gap analysis
	•	Policy generation
	•	Regulatory mapping
	•	Audit automation
	•	RAG compliance assistant
	•	Evidence linking
	•	Control library generation
	•	Risk classification

Long-term Expansion

	•	Workflow engine
	•	Case management
	•	Monitoring + alerts
	•	Enterprise-grade governance

## 8. PIPELINE OVERVIEW

PDF → Bronze (raw)
     → OCR (if needed)
     → Silver (sections + metadata)
     → Gold (embeddings + labels + eval)
     → RAG (query-ready)
     → Compliance Engine (reasoning)

## 9. QUALITY RULES

Claude must:

	•	Validate numbering consistency
	•	Avoid merging unrelated sections
	•	Preserve all legal text verbatim
	•	Never rewrite laws
	•	Never lose text
	•	Minimize hallucinations using a conservative mode
	•	Only provide high-confidence labels in Gold
	•	Defer uncertain items to uncertain_labels

⸻

## 10. VERSIONING RULES

Every document has:

	•	document_id
	•	version (1.0, 1.1…)
	•	last_updated
	•	source_url
	•	hash (SHA256 of raw text)

This ensures reproducibility.


## 11. KNOWLEDGE GRAPH ARCHITECTURE

The Knowledge Graph (KG) is a critical component that maps relationships between regulations, sections, and policies.

### 11.1 Purpose

The KG enables:
	•	Cross-document navigation (e.g., Bank Act → OSFI B-13 → Internal Policy)
	•	Automatic relationship detection (cites, requires, conflicts_with)
	•	Context expansion during retrieval
	•	Gap analysis (find missing policy coverage)
	•	Impact analysis (what changes if regulation X is amended?)

### 11.2 Storage Format: YAML

Why YAML?
	•	Human-readable and editable
	•	Version-controllable (Git-friendly)
	•	LLM-interpretable (Claude can read/write it)
	•	Easy schema validation
	•	Can export to RDF/Neo4j if needed

### 11.3 Node Types

nodes.yaml contains:
	•	regulation: Sections from acts/regulations
	•	clause: Specific clauses/subsections
	•	obligation: Extracted requirements
	•	prohibition: Extracted restrictions
	•	permission: Extracted allowances
	•	definition: Legal term definitions
	•	control: Internal controls/procedures
	•	policy: Company policies

Example node (an obligation — note: no risk_level):
```yaml
- id: "BA-6-1"
  type: "obligation"
  source_document: "Bank Act (Canada)"
  section: "6(1)"
  text: "A bank shall not carry on business as a bank, except in accordance with this Act."
  domains: ["banking", "licensing"]
  metadata:
    jurisdiction: "Canada"
    regulator: "OSFI"
    severity_signal: "punitive"   # describes the text's language strength, not a risk rating
    enforceable: true
    effective_date: "2024-01-01"
```

**Prohibition: never store `risk_level` on a regulation, section,
obligation, permission, or prohibition node.** Risk only exists on the
`policy_implements_regulation` edge — see §11.4 and §13. `severity_signal`
is the only near-risk-looking attribute permitted on a node, and it only
applies to obligations and prohibitions; it describes the text's language,
not consequences.

### 11.4 Edge Types

edges.yaml contains relationships:
	•	cites: Section A references Section B
	•	requires_alignment: Section A implicitly depends on Section B
	•	conflicts_with: Potential conflict detected
	•	supersedes: New regulation replaces old one
	•	amends: Regulation modifies another
	•	references: General reference/mention
	•	policy_implements_regulation: A company policy clause implements a regulatory obligation (fully, partially, or not at all) — the only edge type that carries risk
	•	mitigates: A control reduces residual_risk on a policy_implements_regulation edge

Example citation edge:
```yaml
- from: "BA-6-1"
  to: "PCMLTFA-9"
  type: "requires_alignment"
  description: "Bank licensing triggers AML compliance requirements under PCMLTFA"
  confidence: 0.87
  source: "legal_analysis"
  date_created: "2024-11-16"
```

Example mapping edge (the only place risk lives):
```yaml
- from: "companyx_privacy_v3_s0044"   # policy clause
  to: "pipeda_s0017"                  # regulatory obligation
  type: "policy_implements_regulation"
  coverage_status: "partial"          # covered | partial | gap
  coverage_score: 0.62                # 0.0–1.0 cosine similarity
  residual_risk: "medium"             # low | medium | high | critical
  evidence_policy_section_ids: ["companyx_privacy_v3_s0044"]
  confidence: 0.81
  last_evaluated: "2026-04-15"
```

Residual risk on a mapping edge is a function of the obligation's
`severity_signal` and the policy's `coverage_status`. A gap against a
punitive obligation is `critical`; a full cover of a definitional
section is `low`.

### 11.5 Domain Taxonomy

domains.yaml defines compliance areas:
```yaml
domains:
  - name: "Anti-Money Laundering (AML)"
    abbreviation: "AML"
    regulators: ["FINTRAC", "FinCEN"]
    applicable_jurisdictions: ["Canada", "United States"]
    related_acts: ["PCMLTFA", "Bank Secrecy Act"]

  - name: "Privacy & Data Protection"
    abbreviation: "Privacy"
    regulators: ["OPC", "ICO", "CNIL"]
    applicable_jurisdictions: ["Canada", "UK", "EU"]
    related_acts: ["PIPEDA", "GDPR", "UK DPA"]
```

### 11.6 KG Construction Pipeline

```
Silver Sections → Entity Extraction → Relationship Detection → KG Nodes/Edges
                   (LLM/NER)           (Rule-based + LLM)
```

Steps:
1. Extract entities (sections, references, dates)
2. Detect relationships (regex patterns + LLM analysis)
3. Generate KG entries (YAML format)
4. Validate schema (ensure no broken edges)
5. Embed KG nodes for semantic search

### 11.7 KG-Enhanced Retrieval

```
User Query → Vector Search → Retrieve Top-K sections
                ↓
           KG Expansion (follow edges: cites, requires)
                ↓
           Add neighbor nodes for context
                ↓
           Return enriched results with relationships
```

### 11.8 KG Maintenance Rules

Claude must:
	•	Validate all edges (ensure 'from' and 'to' nodes exist)
	•	Prevent circular dependencies
	•	Log confidence scores for auto-generated edges (<0.75 = uncertain)
	•	Allow manual review/override of low-confidence edges
	•	Version the KG (track changes over time)
	•	Never create relationships that don't exist

### 11.9 Export Formats

The KG can be exported to:
	•	Neo4j (property graph database)
	•	RDF/Turtle (semantic web standard)
	•	GraphML (graph visualization tools)
	•	JSON-LD (linked data format)

⸻

## 13. COMPLIANCE REASONING MODEL (ontology contract)

This is the single source of truth for the compliance ontology. Any code,
schema, API response, or UI that drifts from this contract is a bug.

**Entity classes and what each one owns**

| Entity                           | Owns                                                                 | Never owns       |
|----------------------------------|----------------------------------------------------------------------|------------------|
| Regulation (ground truth)        | text, citation, jurisdiction, regulator, effective_date, last_amended | risk             |
| Section                          | section_number, text, embeddings                                     | risk             |
| Obligation / Prohibition (Gold)  | duty/restriction text, severity_signal, operational_areas            | risk             |
| Permission / Definition (Gold)   | text, metadata                                                       | risk             |
| Policy (customer input)          | title, owner, last_review                                            | risk             |
| PolicyClause (customer input)    | title, body, parent_policy_id                                        | risk             |
| **PolicyImplementsRegulation**   | coverage_status, coverage_score, **residual_risk**, evidence, confidence, last_evaluated | —                |
| Control                          | description, type, frequency                                         | risk             |

**Definitions**

- `severity_signal` is a language-strength label on a regulation obligation
  or prohibition. Values: `definitional | procedural | mandatory | punitive`.
  It describes the TEXT (does this section mention penalties? does it use
  shall/must?) — it is not a risk rating. Computed in
  `ingestion/classify/severity_signal.py` and stored on Gold sections and
  KG obligation/prohibition nodes.

- `coverage_status` is a mapping-edge attribute: `covered | partial | gap`.
  Computed by comparing a policy clause to a regulation obligation
  (semantic similarity; see `api/fastapi/compare.py`).

- `residual_risk` is a mapping-edge attribute: `low | medium | high | critical`.
  Computed from `severity_signal × coverage_status`. A gap against a
  punitive obligation is `critical`; a fully-covered definitional section
  is `low`. This is the ONLY risk value in the system.

**Corollaries Claude must enforce**

1. A regulation tile, card, list row, or summary that surfaces risk without
   a named policy context is a bug. Remove it.
2. A regulation section's JSON/YAML that contains `risk_level` or a `risk`
   object is stale — run `scripts/migrate_strip_risk_from_regulations.py`.
3. "Needs review" is an extraction-quality state (confidence on the
   classifier, OCR errors, etc.) and must never be conflated with risk or
   shown on public regulation surfaces. It belongs behind an admin route.
4. Risk-bearing outputs (dashboards, reports, emails) must name the policy
   being evaluated and the regulation it was evaluated against. No orphan
   risk values.

**Where each concept lives in code**

- Severity signal config: `configs/section_classification.yaml` → `severity_signals`
- Severity signal scorer: `ingestion/classify/severity_signal.py`
- Mapping edge schema: `ingestion/schemas.py` → `PolicyRegulationMapping`
- Residual risk matrix: `api/fastapi/compare.py` → `_RESIDUAL_RISK_MATRIX`
- Compliance API: `GET /api/compliance/coverage` (the only endpoint that
  returns risk)

## 14. We can work with an MVP then scale up from there: 
/
├── data/
|---regulations/
│     ├── raw/
│     ├── processed/
│     └── validation/

├── ingestion/
├── storage/                        # bronze/silver/gold
├── ai/                             # retrieval + agents + evaluation
├── api/
└── dashboard/