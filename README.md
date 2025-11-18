# Covenant Compliance Engine — AI-Ready Regulatory Intelligence Platform
The Covenant Compliance Engine is an end-to-end AI system for parsing, structuring, retrieving, and evaluating legal + regulatory documents against internal or customer policies. It provides:

	•	A full ingestion + parsing stack (PDF → sections → structured nodes → embeddings)
	•	Multi-stage hybrid retrieval (BM25 + semantic + rerankers)
	•	Explainable agentic reasoning
	•	A regulatory Knowledge Graph (YAML-based)
	•	Scored compliance evaluations with confidence
	•	API endpoints for integrations
	•	Benchmarks, validation suites, and dashboards

The system follows a strict Bronze → Silver → Gold data architecture and is designed for enterprise-grade transparency, auditability, and regulator-friendly explanations.


## 1. System Overview

The system converts raw laws and policies into a machine-processable legal substrate, enabling:

	•	Compliance checking
	•	Policy gap analysis
	•	Explainable reasoning traces
	•	Audit-ready reports
	•	Retrieval-augmented regulatory search
	•	Automatic metadata + domain tagging
	•	Knowledge graph-driven context expansion

Core value proposition:

Turn unstructured regulation into structured insights, searchable sections, and trustworthy AI-generated evaluations.

## 2. Architecture

The platform has six major layers:

- data      →    ingestion    →    storage      →    ai  
(raw laws)         (parsing)            (bronze/silver/gold)   (retrieval + agent reasoning)

  →    api       →    dashboard
       (backend)          (UI + analytics)

## 2.1 High-Level Architectural Diagram

"""
          ┌──────────────────────────┐
          │  Raw Regulations (PDF)   │
          └──────────────┬───────────┘
                         ▼
         ┌──────────────────────────────┐
         │ ingestion (OCR + Parsing) │
         │ - PDF extraction             │
         │ - Section segmentation       │
         │ - Cleaning + normalization   │
         └──────────────┬───────────────┘
                        ▼
    ┌────────────────────────────────────────┐
    │ storage (Bronze → Silver → Gold)    │
    │ - Bronze: raw text                     │
    │ - Silver: structured sections          │
    │ - Gold: embeddings + metadata          │
    └──────────────────┬─────────────────────┘
                       ▼
     ┌───────────────────────────────────────┐
     │ ai (Retrieval + Reasoning Engine)  │
     │ - Hybrid retriever (BM25+Semantic)    │
     │ - Reranker                            │
     │ - Knowledge Graph expansion           │
     │ - Agentic multi-step evaluation       │
     │ - Evidence trace + explainability     │
     └───────────────────┬───────────────────┘
                         ▼
        ┌─────────────────────────────────┐
        │ api (FastAPI backend)        │
        │ - Evaluate policies             │
        │ - Retrieve relevant regulations │
        │ - Generate audit reports        │
        └─────────────────────┬───────────┘
                              ▼
             ┌──────────────────────────┐
             │ dashboard (UI)        │
             │ - Reasoning trace viewer │
             │ - Gap analysis           │
             │ - Similar-case browser   │
             └──────────────────────────┘
"""

## 3. Folder Structure
'''
/
├── README.md

├── data/
│   ├── regulations/
│   │   ├── raw/
│   │   ├── processed/
│   │   └── metadata/
│   ├── policies/
│   │   ├── raw/
│   │   └── processed/
│   └── validation/
│       ├── expert/
│       ├── synthetic/
│       └── benchmarks/

├── ingestion/
│   ├── extract/
│   ├── ocr/
│   ├── transform/
│   ├── segment/
│   ├── embed/
│   └── utils/

├── storage/
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   ├── postgres/
│   ├── vector_db/
│   └── hybrid/
│
│   └── knowledge_graph/
│       ├── nodes.yaml
│       ├── edges.yaml
│       ├── domains.yaml
│       └── embeddings/

├── ai/
│   ├── retrieval/
│   ├── reasoning/
│   ├── agents/
│   ├── evaluation/
│   ├── models/
│   └── comparison/

├── api/
│   ├── fastapi/
│   │   ├── routes/
│   │   └── schemas/
│   └── tests/

└── dashboard/
    ├── dashboards/
    ├── components/
    └── audit/

└── configs/
    ├── settings.yaml
    ├── retrieval_modes.yaml
    ├── thresholds.yaml
    └── .env.example
'''

## 4. Data Architecture (Bronze / Silver / Gold)

Bronze (Raw Layer)

	•	Raw text extracted from PDFs
	•	No transformations
	•	Includes OCR’d text where required
	•	Stored exactly as received
	•	Ground truth archive for audits

Silver (Structured Legal Layer)

	•	Parsed sections, clauses, definitions
	•	Hierarchical structure (Part → Division → Section)
	•	Cleaned formatting, normalized whitespace
	•	Linked to metadata:
	•	jurisdiction
	•	effective dates
	•	regulatory domain taxonomy

Gold (Semantic Intelligence Layer)

	•	Embeddings (OpenAI, Azure, or Llama)
	•	Tokenized chunks ready for retrieval
	•	Knowledge Graph relations applied
	•	Domain + risk scoring precomputed
	•	Dense + sparse indexes (FAISS + BM25)

⸻

## 5. Knowledge Graph (YAML-based)

Knowledge Graph is stored in YAML for readability, flexibility, and LLM interpretability.

### Purpose

The Knowledge Graph enables:
- **Cross-document navigation**: Bank Act → OSFI Guidelines → Internal Policies
- **Relationship detection**: cites, requires, implements, conflicts_with
- **Context expansion**: During retrieval, follow edges to find related sections
- **Gap analysis**: Find missing policy coverage
- **Impact analysis**: What changes if regulation X is amended?

### Node Types

The graph supports multiple node types:
- **regulation**: Sections from acts/regulations
- **clause**: Specific clauses/subsections
- **obligation**: Extracted requirements
- **prohibition**: Extracted restrictions
- **permission**: Extracted allowances
- **definition**: Legal term definitions
- **control**: Internal controls/procedures
- **policy**: Company policies

### nodes.yaml

Contains every regulatory and policy node.
```yaml
- id: BA-6-1
  type: regulation
  source_document: "Bank Act (Canada)"
  section: "6(1)"
  text: "A bank shall not carry on business as a bank, except in accordance with this Act."
  domains: ["banking", "licensing"]
  metadata:
    jurisdiction: "Canada"
    regulator: "OSFI"
    risk_level: high
    enforceable: true
    effective_date: "2024-01-01"
```

### edges.yaml

Represents cross-references and semantic/legal relationships.

```yaml
- from: BA-6-1
  to: PCMLTFA-9
  type: requires_alignment
  description: "Bank licensing triggers AML compliance requirements under PCMLTFA"
  confidence: 0.87
  source: "legal_analysis"
  date_created: "2024-11-16"
```

**Relationship Types:**
- `cites`: Section A references Section B
- `requires`: Section A mandates compliance with Section B
- `implements`: Policy implements regulation
- `conflicts_with`: Potential conflict detected
- `supersedes`: New regulation replaces old one
- `amends`: Regulation modifies another

### domains.yaml

Domain taxonomy used for compliance area classification.

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

### KG Construction Pipeline

```
Silver Sections → Entity Extraction → Relationship Detection → KG Nodes/Edges
                   (LLM/NER)           (Rule-based + LLM)
```

1. Extract entities (sections, references, dates)
2. Detect relationships (regex patterns + LLM analysis)
3. Generate KG entries (YAML format)
4. Validate schema (ensure no broken edges)
5. Embed KG nodes for semantic search

### KG-Enhanced Retrieval

```
User Query → Vector Search → Retrieve Top-K sections
                ↓
           KG Expansion (follow edges: cites, requires)
                ↓
           Add neighbor nodes for context
                ↓
           Return enriched results with relationships
```

## 6. Retrieval Architecture

Multi-stage hybrid retriever

1. Sparse retrieval (BM25)
→ High recall on exact matches

2. Dense semantic retrieval
→ Captures meaning & paraphrase

3. Hybrid fusion
→ Merges both vectors via rank aggregation

4. Reranker (Cross Encoder)
→ Final precision improvement

5. Graph-based Expansion
→ Add neighboring KG nodes for context

## 7. Agentic Reasoning Architecture

The agent runs a multi-step reasoning workflow:
	1.	Retrieve candidate sections
	2.	Verify relevance using a verifier prompt
	3.	Expand context using Knowledge Graph
	4.	Evaluate policy statement
	5.	Generate a reasoning trace
	6.	Produce compliance scoring
	7.	Provide regulator-friendly explanations

The final output includes:
- Verdict (Compliant / Non-Compliant / Unknown)
- Confidence score
- Evidence-set (citations)
- Reasoning trace
- Suggested remediation

## 8. API Layer

API is implemented using FastAPI:

Key routes:

- POST /evaluate_policy
- POST /retrieve_sections
- GET  /similar_cases
- GET  /explain/{evaluation_id}
- GET  /audit/{evaluation_id}
Payloads are schema-validated using Pydantic.

## 9. Validation, Benchmarking, QA

Benchmark Suite
	•	Precision / Recall / F1 on retrieval
	•	Compliance scoring accuracy
	•	Latency and performance metrics

Validation Sets
	•	Expert-reviewed cases
	•	Synthetic edge cases
	•	Known-failure regression tests

Quality Gates
	•	Model output thresholds
	•	Retrieval recall floors
	•	Reranker precision minimums

## 10. Deployment Blueprint

Recommended stack:

	•	Backend: FastAPI
	•	Workers: Celery or Prefect
	•	Vector DB: FAISS GPU
	•	Search DB: Elasticsearch
	•	Database: Postgres
	•	Orchestration: Airflow
  •	Container: Docker
	•	Frontend: Next.js + Tailwind

## 11. Roadmap

### v1
	•	Full ingestion pipeline
	•	Hybrid retrieval
	•	Compliance scoring engine
	•	YAML knowledge graph
	•	FastAPI backend

### v2
	•	Agentic workflows
	•	Explainability UI
	•	GAP analysis engine
	•	Similar-case retrieval

### v3
	•	LLM fine-tuning
	•	Continuous benchmark runner
	•	Policy drafting assistant
