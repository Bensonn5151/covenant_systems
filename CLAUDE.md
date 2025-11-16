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

Gold includes:

	•	High-quality embeddings per section
	•	Additional classifier labels:
	•	obligation / permission / prohibition
	•	risk type
	•	operational area
	•	RAG-ready vectors
	•	Eval responses from LLMs
	•	Cross-document mappings (e.g., Bank Act → OSFI B-13 → Internal Policies)

Gold is what powers the actual AI compliance engine.



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
	3.	Extract content
	4.	Identify sections using hierarchical markers:
	•	“1.”, “2.”
	•	“1.1”, “1.2.3”
	•	“Section 5”
	•	“Part II”
	5.	Produce section-level JSON for Silver
	6.	Embed sections for Gold

If extractor fails → fallback to a large document splitter + manual section detection.

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


## 11. We can work with an MVP then scale up from there: 
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