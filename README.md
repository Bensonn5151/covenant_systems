# Covenant Systems — Regulatory Intelligence Platform

**Version:** 0.4.0  
**Last Updated:** 2026-04-16

---

## What It Does

Covenant Systems is a **RegTech compliance engine** that ingests federal regulatory documents (Acts, Regulations, Guidance), structures them into a searchable knowledge base, and lets organizations **compare their internal policies against regulatory obligations** — surfacing coverage gaps and residual risk.

The platform answers one question: **where is my organization exposed?**

---

## Architecture

```
                        ┌──────────────────────────────────────┐
  PDFs / HTML           │         INGESTION PIPELINE           │
  (laws.justice.gc.ca   │                                      │
   FINTRAC, OPC)        │  Bronze (raw) → Silver (sections)    │
        │               │        → Gold (embeddings +          │
        └──────────────►│          classification +            │
                        │          severity signals)           │
                        └───────────────┬──────────────────────┘
                                        │
                        ┌───────────────▼──────────────────────┐
                        │        KNOWLEDGE GRAPH               │
                        │  509 nodes · 848 citation edges      │
                        │  YAML-driven (nodes.yaml, edges.yaml)│
                        └───────────────┬──────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
  ┌───────▼────────┐     ┌──────────────▼───────────┐   ┌────────────▼──────────┐
  │  SEMANTIC SEARCH│     │  COMPLIANCE COMPARISON   │   │   REGULATION CATALOG  │
  │  FAISS + cosine │     │  Policy ↔ Regulation     │   │   Browse sections,    │
  │  384-dim vectors│     │  Residual risk on gaps   │   │   obligations, signals│
  └────────────────┘     └──────────────────────────┘   └───────────────────────┘
                                    │
                          ┌─────────▼──────────┐
                          │   RESIDUAL RISK     │
                          │   (the product)     │
                          │                     │
                          │ severity_signal ×   │
                          │ coverage_status →   │
                          │ residual_risk       │
                          └────────────────────┘
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
| Frontend | Next.js 16, Tailwind v4, Recharts | **Vercel** (free) |
| Auth | Clerk (free tier) | Clerk hosted |
| Backend API | FastAPI, sentence-transformers, FAISS | **Render** (free tier) |
| Database | Supabase Postgres | **Supabase** (free tier) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (384-dim, CPU) | Bundled with backend |
| Vector Index | FAISS (flat, cosine) | File-based on backend |

---

## Dashboard

Three views, designed for a CCO / compliance officer:

1. **Analysis** — Upload a company policy (PDF or text), compare it against PIPEDA (or any ingested regulation). See: overall coverage score, coverage by operational area, compliance gaps sorted by residual risk, matched sections with side-by-side evidence.

2. **Regulations** — Browse the regulation catalog. Each tile shows sections, obligations, prohibitions, definitions, and a language-strength bar. No risk on regulation tiles — risk only appears when a policy is compared.

3. **Search** — Semantic search across all regulation text. Natural language queries, top-K retrieval.

---

## Regulatory Coverage

**Canada (Privacy & AML focus)**:
- 2 Acts: Privacy Act, PIPEDA
- 2 Regulations: SOR-2018-64 (Breach Safeguards), SOR-2001-7 (PIPEDA Regs)
- 5 OPC Guidance: Meaningful Consent, Privacy & AI, Inappropriate Data Practices, Breach Reporting, Ten Fair Information Principles

**509 sections** classified as obligations, prohibitions, permissions, definitions, or procedural.

---

## Quick Start (Local Development)

### Backend

```bash
# 1. Activate virtualenv
source venv/bin/activate

# 2. Start the API
uvicorn api.fastapi.main:app --reload --port 8000
```

### Frontend

```bash
cd web

# 1. Copy env template and fill in Clerk keys
cp .env.example .env.local
# Edit .env.local — add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY and CLERK_SECRET_KEY
# Get keys from: https://dashboard.clerk.com

# 2. Install deps and run
bun install
bun dev
```

Open `http://localhost:3000`. Sign in via Clerk → redirected to `/dashboard`.

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

1. Push repo to GitHub
2. Import in Vercel → set root directory to `web/`
3. Add environment variables:
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
   - `CLERK_SECRET_KEY`
   - `NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in`
   - `NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up`
   - `NEXT_PUBLIC_API_URL=https://covenant-api.onrender.com`

### Backend → Render

1. In Render dashboard → New → Blueprint → select this repo
2. Render reads `render.yaml` and creates the service
3. Set `ALLOWED_ORIGINS` to your Vercel domain (e.g., `https://covenant-systems.vercel.app`)
4. The free tier sleeps after 15 min inactivity (~30s cold start on next request)

### Database → Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Copy the connection string from Settings → Database
3. Add `DATABASE_URL` to Render env vars (when DB integration is ready)

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
ALLOWED_ORIGINS=http://localhost:3000
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## Project Structure

```
covenant_systems/
├── api/fastapi/          # REST API (FastAPI)
│   ├── main.py           # All routes
│   └── compare.py        # Policy ↔ regulation comparison engine
├── ingestion/            # ETL pipeline
│   ├── classify/         # Section classifier + severity signal scorer
│   ├── embed/            # Embedding generation
│   ├── extract/          # PDF extraction (Adobe, PyPDF2, bilingual)
│   └── schemas.py        # Pydantic data contracts
├── storage/              # Bronze / Silver / Gold layers + KG + FAISS
├── search/               # Semantic search engine
├── configs/              # Ontology, classification rules, settings
├── scripts/              # Migration scripts
├── web/                  # Next.js frontend
│   └── src/
│       ├── app/          # Pages (dashboard, sign-in, sign-up)
│       ├── components/   # UI components
│       └── lib/          # API client, types
├── Dockerfile            # Backend container for Render
├── render.yaml           # Render Blueprint
├── requirements.txt      # Python dependencies
└── CLAUDE.md             # AI behavior contract + compliance ontology
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/regulations` | List all regulations with classification + severity breakdown |
| GET | `/api/dashboard/documents` | Regulation tiles (no risk — risk is relational) |
| GET | `/api/dashboard/documents/{id}` | Section-level detail for a regulation |
| GET | `/api/compliance/coverage?policy_id=...&regulation_id=...` | Policy ↔ regulation mapping with residual risk |
| POST | `/api/compare` | Compare policy text/sections against a regulation |
| POST | `/api/compare-upload` | Upload PDF/TXT policy and compare |
| GET | `/api/sample-policies` | List bundled sample policies |
| GET | `/search?query=...&top_k=5` | Semantic search |
| GET | `/health` | Health check with layer counts |

---

## License

Proprietary — Covenant Systems

---

## Contact

For investor materials, technical documentation, or partnership inquiries, contact the Covenant Systems team.
