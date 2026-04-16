# Covenant Systems — Regulatory Intelligence Platform

**Version:** 0.5.0  
**Last Updated:** 2026-04-16

---

## What It Does

Covenant Systems is a **RegTech compliance engine** that ingests federal regulatory documents (Acts, Regulations, Guidance), structures them into a searchable knowledge base, and lets organizations **compare their internal policies against regulatory obligations** — surfacing coverage gaps and residual risk.

The platform answers one question: **where is my organization exposed?**

A compliance analyst uploads a policy document. The system runs it against all 9 Canadian privacy regulations using **LLM-powered reasoning** (Groq Llama 3.3 70B), and returns a **risk heatmap** showing exactly where the policy falls short — with per-obligation verdicts, evidence, and reasoning.

---

## Architecture

```
  Company Policy (PDF/TXT)
        │
        ▼
┌─────────────────────────────────────────────────────┐
│              GROQ LLM COMPARISON ENGINE             │
│                                                     │
│  Policy text + regulation obligations →             │
│  LLM reads both → returns per-obligation verdict:   │
│  covered / partial / gap + matched clause + reason  │
│                                                     │
│  Runs against ALL 9 regulations in one request      │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              RISK HEATMAP (the product)             │
│                                                     │
│  8 operational areas × 9 regulations                │
│  Each cell: worst residual risk of uncovered items  │
│  Color: green (low) → amber → red → critical       │
│  Click cell → filtered gap details with reasoning   │
└─────────────────────────────────────────────────────┘

  Regulation corpus powered by:
┌──────────────────────────────────────┐
│ Bronze → Silver → Gold pipeline      │
│ 509 sections in Supabase Postgres    │
│ Knowledge Graph (509 nodes, 848 edges)│
│ FAISS vector index for semantic search│
└──────────────────────────────────────┘
```

### Compliance Reasoning Model

Regulations are ground truth — they own **no risk**. Risk is relational and lives on the mapping edge between a company policy and a regulatory obligation:

| Entity | Owns | Never owns |
|---|---|---|
| Regulation / Section | text, citation, jurisdiction | risk |
| Obligation / Prohibition | severity_signal (punitive / mandatory / procedural / definitional) | risk |
| **Policy ↔ Regulation Mapping** | coverage_status, coverage_score, **residual_risk** | — |

`residual_risk = f(severity_signal, coverage_status)`

A gap against a punitive obligation → **critical**. A covered definitional section → **low**.

See `CLAUDE.md §13` for the full ontology contract.

---

## Stack

| Layer | Technology | Hosting |
|---|---|---|
| Frontend | Next.js 16.2, Tailwind v4 | **Vercel** (free) |
| Auth | Clerk | Clerk hosted |
| Backend API | FastAPI 0.109 | **Render** (free tier) |
| LLM | Groq Llama 3.3 70B (free tier) | Groq cloud |
| Database | Supabase Postgres (8 tables, 509 regulation sections) | **Supabase** (free tier) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (384-dim) | Fallback only |
| Vector Index | FAISS (flat, cosine) | File-based on backend |

---

## Dashboard

Single-view compliance analysis, designed for a CCO / compliance officer:

1. **Upload** a company policy (PDF or text), or select a sample policy
2. **Run Compliance Analysis** — LLM compares the policy against all 9 regulations
3. **Risk Heatmap** — 8 operational areas × 9 regulations, colored by worst residual risk. Click any cell to filter gap details.
4. **Score Cards** — regulations analyzed, average coverage, total gaps, critical exposures
5. **Compliance Gaps** — each gap shows the LLM's reasoning: why the policy fails that obligation
6. **Covered Obligations** — each match shows: regulation requirement, matched policy clause, reasoning

---

## Regulatory Coverage

**Canada (Privacy focus)**:
- 2 Acts: Privacy Act, PIPEDA
- 2 Regulations: SOR-2018-64 (Breach Safeguards), SOR-2001-7 (PIPEDA Regs)
- 5 OPC Guidance: Meaningful Consent, Privacy & AI, Inappropriate Data Practices, Breach Reporting, Ten Fair Information Principles

**509 sections** across 9 documents, classified as obligations (129), prohibitions (12), permissions, definitions, or procedural. Stored in Supabase Postgres.

---

## Quick Start (Local Development)

### Backend

```bash
# 1. Activate virtualenv
source venv/bin/activate

# 2. Copy env and add your keys
cp .env.example .env
# Edit .env — add GROQ_API_KEY and DATABASE_URL

# 3. Start the API
uvicorn api.fastapi.main:app --reload --port 8000
```

### Frontend

```bash
cd web

# 1. Copy env template and fill in Clerk keys
cp .env.example .env.local
# Edit .env.local — add Clerk keys from dashboard.clerk.com

# 2. Install deps and run
bun install
bun dev
```

Open `http://localhost:3000`. Sign in via Clerk → dashboard.

### Database Setup

```bash
# 1. Create Supabase project at supabase.com
# 2. Run schema
psql $DATABASE_URL < postgres/ddl/001_schema.sql

# 3. Migrate regulation data from Gold layer
python3 scripts/migrate_gold_to_supabase.py
```

### Pipeline (if you need to re-process documents)

```bash
# Bronze → Silver
python3 batch_ingest.py data/raw/manifest.yaml --continue-on-error

# Silver → Gold (embeddings + classification + severity signals)
python3 gold_builder.py --skip-embeddings

# Migrate storage (if upgrading from pre-0.4.0)
python3 scripts/migrate_strip_risk_from_regulations.py
```

---

## Deployment

### Frontend → Vercel

1. Import repo in Vercel → set root directory to `web/`
2. Add environment variables:
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
   - `CLERK_SECRET_KEY`
   - `NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in`
   - `NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up`
   - `NEXT_PUBLIC_API_URL=https://your-render-url.onrender.com`

### Backend → Render

1. New → Blueprint → select this repo (reads `render.yaml`)
2. Add environment variables:
   - `GROQ_API_KEY` — from console.groq.com
   - `DATABASE_URL` — Supabase connection string (transaction pooler)
   - `ALLOWED_ORIGINS` — your Vercel domain
3. Free tier sleeps after 15 min inactivity (~50s cold start)

### Database → Supabase

1. Create project at supabase.com
2. Run `postgres/ddl/001_schema.sql` in the SQL editor
3. Run `python3 scripts/migrate_gold_to_supabase.py` to seed regulation data

---

## Environment Variables

### Frontend (`web/.env.local`)

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (`.env`)

```env
GROQ_API_KEY=gsk_...
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres
ALLOWED_ORIGINS=http://localhost:3000
```

---

## Project Structure

```
covenant_systems/
├── api/fastapi/          # REST API (FastAPI)
│   ├── main.py           # All routes + multi-reg heatmap endpoint
│   ├── compare.py        # Embedding-based comparison (fallback)
│   ├── llm_compare.py    # Groq LLM comparison engine (primary)
│   └── db.py             # Supabase connection pool + queries
├── ingestion/            # ETL pipeline
│   ├── classify/         # Section classifier + severity signal scorer
│   ├── embed/            # Embedding generation + singleton
│   ├── extract/          # PDF extraction (Adobe, PyPDF2, bilingual)
│   └── schemas.py        # Pydantic data contracts
├── postgres/ddl/         # Database schema (001_schema.sql)
├── scripts/              # Migration scripts
├── storage/              # Bronze / Silver / Gold layers + KG + FAISS
├── search/               # Semantic search engine (FAISS)
├── configs/              # Ontology, classification rules, settings
├── web/                  # Next.js frontend
│   └── src/
│       ├── app/          # Pages (dashboard, sign-in, sign-up)
│       ├── components/   # UI (RiskHeatmap, SeverityBadge, etc.)
│       └── lib/          # API client, types
├── testsprite_tests/     # AI-generated test cases + reports
├── Dockerfile            # Backend container for Render
├── render.yaml           # Render Blueprint
├── requirements.txt      # Python dependencies
└── CLAUDE.md             # AI behavior contract + compliance ontology (§13)
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check with layer counts |
| GET | `/api/regulations` | List all regulations with classification + severity breakdown |
| GET | `/api/dashboard/documents` | Regulation tiles (no risk — risk is relational) |
| GET | `/api/dashboard/documents/{id}` | Section-level detail for a regulation |
| GET | `/api/dashboard/stats` | Aggregate stats: classifications, severity signals, areas |
| GET | `/api/sample-policies` | List bundled sample policies |
| GET | `/api/sample-policies/{id}` | Get a sample policy with sections |
| POST | `/api/compare` | Compare policy against a single regulation (LLM) |
| POST | `/api/compare-upload` | Upload PDF/TXT and compare against one regulation |
| POST | `/api/compare-all` | Compare policy against ALL regulations → risk heatmap |
| POST | `/api/compare-all-upload` | Upload file and compare against ALL regulations |
| GET | `/api/compliance/coverage` | Policy ↔ regulation mapping with residual risk |
| GET | `/search?query=...&top_k=5` | Semantic search (FAISS) |
| GET | `/validate` | Data integrity validation |

---

## Testing

Tested with [TestSprite MCP](https://testsprite.com) across 4 rounds:

| Round | Date | Pass Rate | Key Changes |
|---|---|---|---|
| 1 | 2026-04-04 | 25.0% (2/8) | Baseline |
| 2 | 2026-04-04 | 62.5% (5/8) | Fixed email, error codes, paths |
| 3 | 2026-04-16 | 37.5% (3/8) | Stale test plan against legacy endpoints |
| 4 | 2026-04-16 | 66.7% (6/9) | New product endpoints, 3 failures are test-convention mismatches |

All test cases and reports in `testsprite_tests/`.

---

## License

Proprietary — Covenant Systems

---

## Contact

For investor materials, technical documentation, or partnership inquiries, contact the Covenant Systems team.
