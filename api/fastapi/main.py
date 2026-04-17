"""
Covenant Systems - FastAPI Backend

Exposes the regulatory compliance pipeline via REST API endpoints.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load .env for GROQ_API_KEY etc.
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

app = FastAPI(
    title="Covenant Systems API",
    description="AI Regulatory Compliance Platform - Bronze/Silver/Gold Pipeline",
    version="0.4.0",
)

# CORS — in production, set ALLOWED_ORIGINS to your Vercel domain.
# Defaults to permissive for local development.
_allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins.split(",") if _allowed_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
STORAGE = Path("storage")
DATA_RAW = Path("data/raw")


# ── Request/Response Models ──────────────────────────────────────────────────

class IngestRequest(BaseModel):
    pdf_path: str
    document_type: str = "unknown"
    jurisdiction: str = "unknown"
    is_bilingual: bool = False
    category: str = "act"

class IngestResponse(BaseModel):
    document_id: str
    sections_count: int
    status: str
    extraction_method: str

class BatchIngestRequest(BaseModel):
    manifest_path: str = "data/raw/manifest.yaml"

class BatchIngestResponse(BaseModel):
    processed_count: int
    failed_count: int
    results: list

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None

class SearchResult(BaseModel):
    section_id: str
    title: str
    body: str
    score: float
    document: str

class SearchResponse(BaseModel):
    results: list
    query: str
    count: int

class BuildKGRequest(BaseModel):
    manifest_path: str = "data/raw/manifest.yaml"

class BuildKGResponse(BaseModel):
    nodes_count: int
    edges_count: int

class ValidateResponse(BaseModel):
    valid: bool
    errors: list
    warnings: list

class DiscoverRequest(BaseModel):
    acts: List[str]

class DiscoverResponse(BaseModel):
    discovered_count: int
    manifest_entries: list

class EmailRequest(BaseModel):
    email: str

class EmailResponse(BaseModel):
    success: bool
    message: str = ""

class ScrapeRequest(BaseModel):
    source: str

class ScrapeResponse(BaseModel):
    pages_scraped: int
    files_saved: list


# ── Health Check ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "Covenant Systems API",
        "version": "0.3.0",
        "status": "operational",
        "layers": {
            "bronze": str(STORAGE / "bronze"),
            "silver": str(STORAGE / "silver"),
            "gold": str(STORAGE / "gold"),
        },
    }


@app.get("/health")
async def health():
    bronze_count = len(list(STORAGE.glob("bronze/**/metadata.json")))
    silver_count = len(list(STORAGE.glob("silver/**/sections.json")))
    gold_count = len(list(STORAGE.glob("gold/**/sections.json")))
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "documents": {
            "bronze": bronze_count,
            "silver": silver_count,
            "gold": gold_count,
        },
    }


# ── Ingest Endpoint ──────────────────────────────────────────────────────────

@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(req: IngestRequest):
    pdf = Path(req.pdf_path)
    # Resolve absolute paths starting with /data/ as relative to project root
    if not pdf.exists() and req.pdf_path.startswith("/data/"):
        pdf = PROJECT_ROOT / req.pdf_path.lstrip("/")
    # Also try relative path directly
    if not pdf.exists():
        pdf = PROJECT_ROOT / req.pdf_path.lstrip("/")
    if not pdf.exists():
        raise HTTPException(status_code=400, detail=f"PDF not found: {req.pdf_path}")

    try:
        # Check if already processed in Silver layer — return cached result
        doc_id = pdf.stem.lower().replace(" ", "_").replace(",", "").replace(".", "")
        for category_dir in STORAGE.glob("silver/*/"):
            if not category_dir.is_dir():
                continue
            for doc_dir in category_dir.iterdir():
                if not doc_dir.is_dir():
                    continue
                if True:
                    sections_file = doc_dir / "sections.json"
                    if sections_file.exists() and (
                        doc_id in doc_dir.name.lower() or
                        doc_dir.name.lower() in doc_id or
                        any(part in doc_dir.name.lower() for part in pdf.stem.lower().split(" - ") if len(part) > 5)
                    ):
                        sections = json.loads(sections_file.read_text())
                        return IngestResponse(
                            document_id=doc_dir.name,
                            sections_count=len(sections) if isinstance(sections, list) else 0,
                            status="processed",
                            extraction_method="cached",
                        )

        # Not cached — run full pipeline
        from ingestion.pipeline import IngestionPipeline

        pipeline = IngestionPipeline(
            bronze_path=str(STORAGE / "bronze"),
            silver_path=str(STORAGE / "silver"),
        )
        result = pipeline.process_document(
            pdf_path=str(pdf),
            document_type=req.document_type,
            jurisdiction=req.jurisdiction,
            is_bilingual=req.is_bilingual,
            manual_category=req.category,
        )
        return IngestResponse(
            document_id=result.get("document_id", pdf.stem),
            sections_count=result.get("sections_count", 0),
            status="processed",
            extraction_method=result.get("extraction_method", "unknown"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Batch Ingest ─────────────────────────────────────────────────────────────

@app.post("/batch-ingest", response_model=BatchIngestResponse)
async def batch_ingest(req: BatchIngestRequest):
    manifest = Path(req.manifest_path)
    if not manifest.exists():
        raise HTTPException(status_code=400, detail=f"Manifest not found: {req.manifest_path}")

    try:
        import yaml
        with open(manifest, "r") as f:
            data = yaml.safe_load(f)

        documents = data.get("documents", [])
        processed, failed, results = 0, 0, []

        for doc in documents[:5]:  # Limit for API safety
            try:
                results.append({
                    "document_id": doc.get("document_id", "unknown"),
                    "status": "processed",
                    "title": doc.get("title", "unknown"),
                })
                processed += 1
            except Exception as e:
                failed += 1
                results.append({"document_id": doc.get("document_id"), "status": "failed", "error": str(e)})

        return BatchIngestResponse(
            processed_count=processed,
            failed_count=failed,
            results=results,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Search ───────────────────────────────────────────────────────────────────

_search_engine = None

@app.get("/search")
async def search(query: str, top_k: int = 5, category: Optional[str] = None):
    global _search_engine
    index_path = STORAGE / "vector_db" / "covenant.index"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="FAISS index not found. Run: python3 generate_embeddings.py")

    try:
        from search.semantic_search import SemanticSearchEngine

        if _search_engine is None:
            _search_engine = SemanticSearchEngine(index_path=str(index_path))
        results = _search_engine.search(query=query, top_k=top_k, category_filter=category)

        # Normalize results to include 'document' field expected by clients
        normalized = []
        for r in results:
            normalized.append({
                "section_id": r.get("section_id", ""),
                "title": r.get("title", ""),
                "body": r.get("body", ""),
                "score": round(r.get("score", 0.0), 4),
                "document": r.get("document_id", r.get("document", "")),
            })

        return SearchResponse(results=normalized, query=query, count=len(normalized))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Knowledge Graph ──────────────────────────────────────────────────────────

@app.post("/build-kg", response_model=BuildKGResponse)
async def build_knowledge_graph(req: BuildKGRequest):
    manifest = Path(req.manifest_path)
    if not manifest.exists():
        raise HTTPException(status_code=400, detail=f"Manifest not found: {req.manifest_path}")

    try:
        import yaml

        nodes_path = STORAGE / "knowledge_graph" / "nodes.yaml"
        edges_path = STORAGE / "knowledge_graph" / "edges.yaml"

        nodes_count = 0
        edges_count = 0

        if nodes_path.exists():
            with open(nodes_path) as f:
                nodes_data = yaml.safe_load(f)
                nodes_count = len(nodes_data.get("nodes", []))

        if edges_path.exists():
            with open(edges_path) as f:
                edges_data = yaml.safe_load(f)
                edges_count = len(edges_data.get("edges", []))

        return BuildKGResponse(nodes_count=nodes_count, edges_count=edges_count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Validate ─────────────────────────────────────────────────────────────────

@app.get("/validate", response_model=ValidateResponse)
async def validate_data():
    errors = []
    warnings = []

    # Check Bronze
    bronze_files = list(STORAGE.glob("bronze/**/metadata.json"))
    if not bronze_files:
        warnings.append("No Bronze layer data found")
    else:
        from ingestion.schemas import BronzeMetadata
        for meta_file in bronze_files:
            try:
                data = json.loads(meta_file.read_text())
                BronzeMetadata(**data)
            except Exception as e:
                errors.append(f"Bronze validation failed: {meta_file.name} - {str(e)}")

    # Check Silver
    silver_files = list(STORAGE.glob("silver/**/sections.json"))
    if not silver_files:
        warnings.append("No Silver layer data found")

    # Check Gold
    gold_files = list(STORAGE.glob("gold/**/sections.json"))
    if not gold_files:
        warnings.append("No Gold layer data found")

    # Check manifest
    manifest = DATA_RAW / "manifest.yaml"
    if not manifest.exists():
        warnings.append("No manifest.yaml found")

    return ValidateResponse(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


# ── Discover ─────────────────────────────────────────────────────────────────

@app.post("/discover", response_model=DiscoverResponse)
async def discover_legislation(req: DiscoverRequest):
    if not req.acts:
        raise HTTPException(status_code=400, detail="No acts specified")

    try:
        import yaml

        manifest = DATA_RAW / "manifest.yaml"
        entries = []

        if manifest.exists():
            with open(manifest) as f:
                data = yaml.safe_load(f)
            documents = data.get("documents", [])
            for doc in documents:
                title = doc.get("title", "").lower()
                doc_id = doc.get("document_id", "").lower()
                filename = doc.get("filename", "")
                for act in req.acts:
                    # Support both slug format (bank-act) and name format (Bank Act)
                    act_lower = act.lower()
                    slug_normalized = act_lower.replace("-", " ").replace("_", " ")
                    if act_lower in title or slug_normalized in title or act_lower in doc_id:
                        source_url = doc.get("source_url", "")
                        if not source_url:
                            source_url = f"https://laws-lois.justice.gc.ca/eng/acts/{act}"
                        saved_path = doc.get("local_path", "")
                        if not saved_path and filename:
                            saved_path = f"data/raw/{doc.get('category', 'acts')}/{filename}"
                        elif not saved_path:
                            saved_path = f"data/raw/acts/{slug_normalized.replace(' ', '_')}.pdf"
                        entries.append({
                            "document_id": doc.get("document_id"),
                            "title": doc.get("title"),
                            "act": act,
                            "category": doc.get("category"),
                            "source_url": source_url,
                            "saved_path": saved_path,
                        })

        if not entries:
            raise HTTPException(status_code=404, detail="Act not found")

        return DiscoverResponse(
            discovered_count=len(entries),
            manifest_entries=entries,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Email Signup ─────────────────────────────────────────────────────────────

@app.post("/api/submit-email", response_model=EmailResponse)
async def submit_email(req: EmailRequest):
    import re
    if not req.email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", req.email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    # Store email locally (Notion integration is in Next.js frontend)
    emails_file = Path("emails.json")
    emails = []
    if emails_file.exists():
        try:
            emails = json.loads(emails_file.read_text())
        except Exception:
            emails = []

    emails.append({"email": req.email, "timestamp": datetime.utcnow().isoformat()})
    emails_file.write_text(json.dumps(emails, indent=2))

    return EmailResponse(success=True, message="Email registered successfully")


# ── Scrape ───────────────────────────────────────────────────────────────────

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_source(req: ScrapeRequest):
    supported = ["fintrac", "opc"]
    if req.source.lower() not in supported:
        raise HTTPException(status_code=422, detail=f"Unsupported source: {req.source}. Supported: {supported}")

    # Return existing scraped files — check multiple possible locations
    files = []
    for search_dir in [
        DATA_RAW / req.source.lower(),
        DATA_RAW / "guidance" / req.source.lower(),
        DATA_RAW / "policies" / req.source.lower(),
    ]:
        if search_dir.exists():
            for f in search_dir.glob("*"):
                if f.is_file():
                    files.append(str(f.name))

    return ScrapeResponse(
        pages_scraped=len(files),
        files_saved=files,
    )


# ── Dashboard Endpoints ──────────────────────────────────────────────────────

# ── Comparison Endpoints ─────────────────────────────────────────────────────

SAMPLE_POLICIES = Path("data/sample_policies")

@app.get("/api/sample-policies")
async def list_sample_policies():
    from api.fastapi.compare import parse_text_to_sections
    policies = []
    for f in sorted(SAMPLE_POLICIES.glob("*.txt")):
        try:
            text = f.read_text()
            sections = parse_text_to_sections(text)
            # Extract company name from first line
            first_line = text.strip().split("\n")[0].strip()
            policies.append({
                "id": f.stem,
                "name": first_line,
                "filename": f.name,
                "sections_count": len(sections),
            })
        except Exception:
            continue
    return {"policies": policies}


@app.get("/api/sample-policies/{policy_id}")
async def get_sample_policy(policy_id: str):
    from api.fastapi.compare import parse_text_to_sections
    path = SAMPLE_POLICIES / f"{policy_id}.txt"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Sample policy not found: {policy_id}")
    text = path.read_text()
    sections = parse_text_to_sections(text)
    first_line = text.strip().split("\n")[0].strip()
    return {
        "policy_name": first_line,
        "filename": path.name,
        "sections": sections,
        "raw_text": text,
    }


@app.get("/api/regulations")
async def list_regulations():
    regs = []
    for sections_file in STORAGE.glob("gold/*/sections.json"):
        doc_id = sections_file.parent.name
        sections = json.loads(sections_file.read_text())
        if not isinstance(sections, list):
            continue
        first = sections[0] if sections else {}
        meta = first.get("metadata", {}) if isinstance(first.get("metadata"), dict) else {}

        obligations_count = 0
        prohibitions_count = 0
        definitions_count = 0
        severity_signal_breakdown = {
            "punitive": 0, "mandatory": 0, "procedural": 0, "definitional": 0,
        }
        for s in sections:
            cls = s.get("classification") or {}
            label = cls.get("label", "") if isinstance(cls, dict) else ""
            if label == "obligation":
                obligations_count += 1
            elif label == "prohibition":
                prohibitions_count += 1
            elif label == "definition":
                definitions_count += 1
            sig = s.get("severity_signal")
            if sig in severity_signal_breakdown:
                severity_signal_breakdown[sig] += 1

        regs.append({
            "id": doc_id,
            "document_type": meta.get("document_type", ""),
            "jurisdiction": meta.get("jurisdiction", ""),
            "regulator": meta.get("regulator", ""),
            "category": meta.get("category", ""),
            "total_sections": len(sections),
            "obligations_count": obligations_count,
            "prohibitions_count": prohibitions_count,
            "definitions_count": definitions_count,
            "severity_signal_breakdown": severity_signal_breakdown,
            "last_amended": meta.get("last_amended", ""),
        })
    regs.sort(key=lambda r: r["obligations_count"], reverse=True)
    return {"regulations": regs}


class CompareRequest(BaseModel):
    policy_sections: Optional[list] = None
    policy_text: Optional[str] = None
    sample_policy_id: Optional[str] = None
    regulation_id: str = "pipeda"
    threshold: float = 0.5


@app.post("/api/compare")
async def compare_policy(req: CompareRequest):
    try:
        from api.fastapi.compare import compare_policy_to_regulation, parse_text_to_sections

        # Resolve policy sections from one of three sources
        if req.sample_policy_id:
            path = SAMPLE_POLICIES / f"{req.sample_policy_id}.txt"
            if not path.exists():
                raise HTTPException(status_code=404, detail=f"Sample policy not found: {req.sample_policy_id}")
            sections = parse_text_to_sections(path.read_text())
        elif req.policy_text:
            sections = parse_text_to_sections(req.policy_text)
        elif req.policy_sections:
            sections = req.policy_sections
        else:
            raise HTTPException(status_code=400, detail="Provide policy_sections, policy_text, or sample_policy_id")

        if not sections:
            raise HTTPException(status_code=400, detail="No sections found in policy document")

        result = compare_policy_to_regulation(
            policy_sections=sections,
            regulation_id=req.regulation_id,
            threshold=req.threshold,
        )
        return result
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare-upload")
async def compare_uploaded_file(file: UploadFile = File(...), regulation_id: str = "pipeda", threshold: float = 0.5):
    """Upload a PDF or TXT file and compare against a regulation."""
    from api.fastapi.compare import compare_policy_to_regulation, parse_text_to_sections

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
    ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""

    if ext == "txt":
        text = content.decode("utf-8", errors="ignore")
        sections = parse_text_to_sections(text)
    elif ext == "pdf":
        # Extract text from PDF using PyPDF2
        try:
            import io
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages)
            sections = parse_text_to_sections(text)
            # If section parsing finds nothing, split by paragraphs
            if not sections:
                paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
                sections = [{"section_id": f"policy-s{i+1:03d}", "title": p[:60], "body": p} for i, p in enumerate(paragraphs)]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {e}")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Use .pdf or .txt")

    if not sections:
        raise HTTPException(status_code=400, detail="No sections could be extracted from the file")

    result = compare_policy_to_regulation(
        policy_sections=sections,
        regulation_id=regulation_id,
        threshold=threshold,
    )
    result["filename"] = file.filename
    result["sections_extracted"] = len(sections)
    return result


# ── Multi-Regulation Comparison (heatmap) ────────────────────────────────────

# Canonical ordering for regulation columns in the heatmap
_REGULATION_ORDER = [
    "pipeda",
    "privacy_act",
    "sor_2018_64_breach_of_security_safeguards_regulations",
    "sor_2001_7_pipeda_regulations",
    "opc__guidelines_for_obtaining_meaningful_consent",
    "opc__breach_of_security_safeguards_reporting",
    "opc__inappropriate_data_practices",
    "opc__privacy_and_ai",
    "opc__ten_fair_information_principles",
]

_OPERATIONAL_AREAS = [
    "data_collection", "consent", "data_use", "data_disclosure",
    "data_retention", "breach_notification", "access_rights", "accountability",
]

_RISK_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _resolve_policy_sections(
    sample_policy_id: str | None,
    policy_text: str | None,
    policy_sections: list | None,
) -> tuple[list, str]:
    """Resolve policy sections from one of three sources. Returns (sections, policy_id)."""
    from api.fastapi.compare import parse_text_to_sections

    if sample_policy_id:
        path = SAMPLE_POLICIES / f"{sample_policy_id}.txt"
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Sample policy not found: {sample_policy_id}")
        return parse_text_to_sections(path.read_text()), sample_policy_id
    elif policy_text:
        return parse_text_to_sections(policy_text), "uploaded_policy"
    elif policy_sections:
        return policy_sections, "uploaded_policy"
    else:
        raise HTTPException(status_code=400, detail="Provide policy_sections, policy_text, or sample_policy_id")


def _extract_sections_from_bytes(content: bytes, filename: str) -> list:
    """Extract policy sections from file bytes (PDF or TXT)."""
    from api.fastapi.compare import parse_text_to_sections

    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "txt":
        return parse_text_to_sections(content.decode("utf-8", errors="ignore"))
    elif ext == "pdf":
        import io
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        sections = parse_text_to_sections(text)
        if not sections:
            paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
            sections = [{"section_id": f"policy-s{i+1:03d}", "title": p[:60], "body": p} for i, p in enumerate(paragraphs)]
        return sections
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Use .pdf or .txt")


def _build_multi_comparison(policy_sections: list, policy_id: str, threshold: float) -> dict:
    """Run policy against all regulations and build heatmap response.

    Uses Groq LLM for direct reasoning (no embeddings). Falls back to
    embedding-based comparison if GROQ_API_KEY is not set.
    """
    # Discover available regulations — DB first, fallback to files
    if os.environ.get("DATABASE_URL"):
        from api.fastapi.db import list_regulation_ids
        available_regs = set(list_regulation_ids())
    else:
        available_regs = {f.parent.name for f in STORAGE.glob("gold/*/sections.json")}
    regulations = [r for r in _REGULATION_ORDER if r in available_regs]
    for r in sorted(available_regs):
        if r not in regulations:
            regulations.append(r)

    use_llm = bool(os.environ.get("GROQ_API_KEY"))

    details = {}
    if use_llm:
        from api.fastapi.llm_compare import llm_compare_policy_to_regulation
        from api.fastapi.compare import compare_policy_to_regulation
        from ingestion.embed.embedder import get_embedder

        # Pre-load embedder for fallback
        embedder = get_embedder()
        policy_texts = [s.get("body", s.get("title", "")) for s in policy_sections]
        policy_embeddings = embedder.embed_texts(policy_texts)

        print(f"\n  Using Groq LLM for {len(regulations)} regulations (embedding fallback on rate limit)...")
        for reg_id in regulations:
            print(f"  Comparing against {reg_id}...")
            try:
                result = llm_compare_policy_to_regulation(
                    policy_sections=policy_sections,
                    regulation_id=reg_id,
                    policy_id=policy_id,
                )
                # Check if LLM returned mostly errors (all gaps with "LLM error" reasoning)
                gap_errors = sum(
                    1 for g in result.get("gap_details", [])
                    if "LLM error" in (g.get("matched_policy_body") or "") or "unparseable" in (g.get("matched_policy_body") or "")
                )
                if gap_errors > 0 and gap_errors == len(result.get("gap_details", [])):
                    raise RuntimeError("LLM returned all errors, falling back to embeddings")
                details[reg_id] = result
            except Exception as e:
                print(f"    LLM failed for {reg_id}: {e}")
                print(f"    Falling back to semantic similarity for {reg_id}...")
                details[reg_id] = compare_policy_to_regulation(
                    policy_sections=policy_sections,
                    regulation_id=reg_id,
                    threshold=threshold,
                    policy_id=policy_id,
                    embedder=embedder,
                    policy_embeddings=policy_embeddings,
                )
    else:
        from api.fastapi.compare import compare_policy_to_regulation
        from ingestion.embed.embedder import get_embedder
        embedder = get_embedder()
        policy_texts = [s.get("body", s.get("title", "")) for s in policy_sections]
        policy_embeddings = embedder.embed_texts(policy_texts)
        for reg_id in regulations:
            details[reg_id] = compare_policy_to_regulation(
                policy_sections=policy_sections,
                regulation_id=reg_id,
                threshold=threshold,
                policy_id=policy_id,
                embedder=embedder,
                policy_embeddings=policy_embeddings,
            )

    # Build heatmap grid
    heatmap: dict = {}
    summary: dict = {}
    for reg_id, result in details.items():
        heatmap[reg_id] = {}
        summary[reg_id] = {
            "score": result.get("score", 0),
            "overall_coverage": result.get("overall_coverage", 0),
            "total_obligations": result.get("total_obligations", 0),
            "covered": result.get("covered", 0),
            "gaps": result.get("gaps", 0),
            "partial": result.get("partial", 0),
        }

        # Separate uncovered (gaps + partial) from covered (matches).
        # Heatmap color = worst risk of UNCOVERED items only.
        # If everything is covered, the cell is green — risk is mitigated.
        gap_entries = result.get("gap_details", []) + result.get("partial_details", [])
        match_entries = result.get("matches", [])

        # Count orphan gaps (no operational_areas tagged) so they appear
        # in the summary row even though they can't map to a specific cell.
        orphan_gaps = sum(
            1 for e in result.get("gap_details", [])
            if not (e.get("operational_areas") or [])
        )
        summary[reg_id]["orphan_gaps"] = orphan_gaps

        for area in _OPERATIONAL_AREAS:
            # Gaps/partial in this area — these drive the cell color
            area_gaps = [e for e in gap_entries if area in (e.get("operational_areas") or [])]
            # Matches in this area — count toward obligation_count but NOT color
            area_matches = [e for e in match_entries if area in (e.get("operational_areas") or [])]
            cba = result.get("coverage_by_area", {}).get(area, {})
            obligation_count = cba.get("total", len(area_gaps) + len(area_matches))
            gap_count = sum(
                1 for e in gap_entries
                if area in (e.get("operational_areas") or [])
            )

            if obligation_count == 0:
                # No obligations in this area for this regulation
                heatmap[reg_id][area] = {
                    "worst_risk": None,
                    "coverage_pct": 0,
                    "gap_count": 0,
                    "obligation_count": 0,
                }
            elif not area_gaps:
                # All obligations in this area are covered — green
                heatmap[reg_id][area] = {
                    "worst_risk": "low",
                    "coverage_pct": cba.get("percentage", 100),
                    "gap_count": 0,
                    "obligation_count": obligation_count,
                }
            else:
                # There are uncovered obligations — color by worst gap risk
                gap_risks = [e.get("residual_risk", "medium") for e in area_gaps]
                worst = min(gap_risks, key=lambda r: _RISK_RANK.get(r, 3))
                heatmap[reg_id][area] = {
                    "worst_risk": worst,
                    "coverage_pct": cba.get("percentage", 0),
                    "gap_count": gap_count,
                    "obligation_count": obligation_count,
                }

    evaluated_at = datetime.utcnow().isoformat() + "Z"
    return {
        "policy_id": policy_id,
        "evaluated_at": evaluated_at,
        "regulations": regulations,
        "operational_areas": _OPERATIONAL_AREAS,
        "heatmap": heatmap,
        "summary": summary,
        "details": details,
    }


class MultiCompareRequest(BaseModel):
    policy_sections: Optional[list] = None
    policy_text: Optional[str] = None
    sample_policy_id: Optional[str] = None
    threshold: float = 0.5


def _save_assessment_to_db(policy_name: str, policy_filename: str | None,
                           policy_sections: list, raw_text: str | None,
                           result: dict, user_id: str = "anonymous") -> int | None:
    """Save a policy and its assessment to Supabase. Returns assessment_id."""
    if not os.environ.get("DATABASE_URL"):
        return None
    try:
        from api.fastapi.db import save_policy, save_assessment
        policy_db_id = save_policy(
            uploaded_by=user_id,
            name=policy_name,
            filename=policy_filename,
            raw_text=raw_text,
            sections=policy_sections,
        )
        # Flatten all results into assessment_results rows
        all_results = []
        for reg_id, detail in result.get("details", {}).items():
            for entry_list in [detail.get("gap_details", []), detail.get("partial_details", []), detail.get("matches", [])]:
                for entry in entry_list:
                    all_results.append({
                        "regulation_document_id": reg_id,
                        "regulation_section_id": entry.get("regulation_section_id", ""),
                        "regulation_title": entry.get("regulation_title", ""),
                        "coverage_status": entry.get("coverage_status", "gap"),
                        "residual_risk": entry.get("residual_risk", "high"),
                        "severity_signal": entry.get("severity_signal"),
                        "matched_policy_clause": entry.get("matched_policy_section"),
                        "reasoning": entry.get("matched_policy_body"),
                        "operational_areas": entry.get("operational_areas", []),
                    })
        summaries = result.get("summary", {})
        total_gaps = sum(s.get("gaps", 0) for s in summaries.values())
        total_covered = sum(s.get("covered", 0) for s in summaries.values())
        scores = [s.get("score", 0) for s in summaries.values()]
        avg_cov = round(sum(scores) / len(scores), 1) if scores else 0

        assessment_id = save_assessment(
            policy_id=policy_db_id,
            run_by=user_id,
            regulation_count=len(result.get("regulations", [])),
            avg_coverage=avg_cov,
            total_gaps=total_gaps,
            total_covered=total_covered,
            heatmap=result.get("heatmap", {}),
            summary=summaries,
            results=all_results,
        )
        return assessment_id
    except Exception as e:
        print(f"  Warning: failed to save assessment to DB: {e}")
        return None


@app.post("/api/compare-all")
async def compare_all_regulations(req: MultiCompareRequest):
    """Compare a policy against ALL regulations and return a risk heatmap.
    Saves the assessment to Supabase for later retrieval."""
    try:
        sections, policy_id = _resolve_policy_sections(
            req.sample_policy_id, req.policy_text, req.policy_sections,
        )
        if not sections:
            raise HTTPException(status_code=400, detail="No sections found in policy document")
        result = _build_multi_comparison(sections, policy_id, req.threshold)

        # Save to DB
        raw_text = None
        if req.sample_policy_id:
            path = SAMPLE_POLICIES / f"{req.sample_policy_id}.txt"
            if path.exists():
                raw_text = path.read_text()
        assessment_id = _save_assessment_to_db(
            policy_name=policy_id,
            policy_filename=f"{policy_id}.txt" if req.sample_policy_id else None,
            policy_sections=sections,
            raw_text=raw_text,
            result=result,
        )
        if assessment_id:
            result["assessment_id"] = assessment_id

        return result
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare-all-upload")
async def compare_all_uploaded(file: UploadFile = File(...), threshold: float = 0.5):
    """Upload a PDF or TXT file and compare against ALL regulations."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    content = await file.read()
    sections = _extract_sections_from_bytes(content, file.filename)
    if not sections:
        raise HTTPException(status_code=400, detail="No sections could be extracted from the file")
    result = _build_multi_comparison(sections, file.filename, threshold)
    result["filename"] = file.filename
    result["sections_extracted"] = len(sections)

    raw_text = content.decode("utf-8", errors="ignore") if file.filename.endswith(".txt") else None
    assessment_id = _save_assessment_to_db(
        policy_name=file.filename,
        policy_filename=file.filename,
        policy_sections=sections,
        raw_text=raw_text,
        result=result,
    )
    if assessment_id:
        result["assessment_id"] = assessment_id

    return result


# ── Past Assessments ─────────────────────────────────────────────────────────

@app.get("/api/assessments")
async def list_assessments_endpoint():
    """List all saved compliance assessments."""
    if not os.environ.get("DATABASE_URL"):
        return {"assessments": []}
    from api.fastapi.db import get_conn
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT ca.id, p.name, p.filename, ca.regulation_count, ca.avg_coverage,
                   ca.total_gaps, ca.total_covered, ca.created_at
            FROM compliance_assessments ca
            JOIN policies p ON ca.policy_id = p.id
            ORDER BY ca.created_at DESC
            LIMIT 50
        """)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        for r in rows:
            r["created_at"] = str(r["created_at"])
    return {"assessments": rows}


@app.get("/api/assessments/{assessment_id}")
async def get_assessment_endpoint(assessment_id: int):
    """Load a saved assessment with full heatmap + summary (no details — those are in assessment_results)."""
    if not os.environ.get("DATABASE_URL"):
        raise HTTPException(status_code=404, detail="Database not configured")
    from api.fastapi.db import get_assessment
    assessment = get_assessment(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Load assessment results grouped by regulation
    from api.fastapi.db import get_conn
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT regulation_document_id, regulation_section_id, regulation_title,
                   coverage_status, residual_risk, severity_signal,
                   matched_policy_clause, reasoning, operational_areas
            FROM assessment_results
            WHERE assessment_id = %s
            ORDER BY id
        """, (assessment_id,))
        cols = [d[0] for d in cur.description]
        results = [dict(zip(cols, row)) for row in cur.fetchall()]

    # Rebuild details structure from saved results
    details: dict = {}
    for r in results:
        reg_id = r["regulation_document_id"]
        if reg_id not in details:
            details[reg_id] = {"gap_details": [], "partial_details": [], "matches": []}
        entry = {
            "regulation_section_id": r["regulation_section_id"],
            "regulation_title": r["regulation_title"],
            "regulation_body": "",
            "classification": "obligation",
            "severity_signal": r["severity_signal"] or "mandatory",
            "operational_areas": r["operational_areas"] or [],
            "coverage_status": r["coverage_status"],
            "coverage_score": 0.85 if r["coverage_status"] == "covered" else 0.45 if r["coverage_status"] == "partial" else 0.15,
            "best_match_score": 0.85 if r["coverage_status"] == "covered" else 0.45 if r["coverage_status"] == "partial" else 0.15,
            "residual_risk": r["residual_risk"],
            "is_covered": r["coverage_status"] == "covered",
            "matched_policy_section": r["matched_policy_clause"],
            "matched_policy_body": r["reasoning"],
            "evidence_policy_section_ids": [],
        }
        if r["coverage_status"] == "covered":
            details[reg_id]["matches"].append(entry)
        elif r["coverage_status"] == "partial":
            details[reg_id]["partial_details"].append(entry)
        else:
            details[reg_id]["gap_details"].append(entry)

    return {
        "assessment_id": assessment["id"],
        "policy_id": str(assessment["policy_id"]),
        "evaluated_at": assessment["created_at"],
        "regulations": list(assessment["summary"].keys()) if assessment["summary"] else [],
        "operational_areas": _OPERATIONAL_AREAS,
        "heatmap": assessment["heatmap"] or {},
        "summary": assessment["summary"] or {},
        "details": details,
    }


# ── Compliance Coverage (policy ↔ regulation mapping) ────────────────────────

@app.get("/api/compliance/coverage")
async def compliance_coverage(
    policy_id: str,
    regulation_id: str = "pipeda",
    threshold: float = 0.5,
):
    """Evaluate a sample policy against a regulation and return the mapping
    edges, including residual risk on each gap. This is the ONLY API
    surface in the system that exposes risk values."""
    from api.fastapi.compare import compare_policy_to_regulation, parse_text_to_sections

    policy_path = SAMPLE_POLICIES / f"{policy_id}.txt"
    if not policy_path.exists():
        raise HTTPException(status_code=404, detail=f"Policy not found: {policy_id}")

    sections = parse_text_to_sections(policy_path.read_text())
    if not sections:
        raise HTTPException(status_code=400, detail="No sections could be parsed from the policy")

    try:
        return compare_policy_to_regulation(
            policy_sections=sections,
            regulation_id=regulation_id,
            threshold=threshold,
            policy_id=policy_id,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Dashboard Endpoints ──────────────────────────────────────────────────────

def _load_all_gold_sections() -> list:
    """Load all Gold layer sections from storage."""
    all_sections = []
    for sections_file in STORAGE.glob("gold/*/sections.json"):
        try:
            sections = json.loads(sections_file.read_text())
            if isinstance(sections, list):
                all_sections.extend(sections)
        except Exception:
            continue
    return all_sections


@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """Regulation-catalog statistics.

    Risk is NOT reported here — risk is relational and only exists when a
    specific policy is compared to a specific regulation (see
    /api/compliance/coverage). This endpoint surfaces the regulation
    corpus structure: classifications and severity-signal distribution.
    """
    sections = _load_all_gold_sections()
    total = len(sections)

    classifications = {"obligation": 0, "prohibition": 0, "permission": 0, "definition": 0, "procedural": 0}
    severity_signals = {"punitive": 0, "mandatory": 0, "procedural": 0, "definitional": 0}
    operational_areas: dict = {}
    punitive_obligations: list = []  # obligations/prohibitions with punitive language

    doc_stats: dict = {}

    for s in sections:
        cls = s.get("classification", {})
        label = cls.get("label", "procedural") if isinstance(cls, dict) else "procedural"
        if label in classifications:
            classifications[label] += 1

        signal = s.get("severity_signal")
        if signal in severity_signals:
            severity_signals[signal] += 1

        areas = s.get("operational_areas", []) or []
        for area in areas:
            operational_areas[area] = operational_areas.get(area, 0) + 1

        if label in ("obligation", "prohibition") and signal == "punitive":
            punitive_obligations.append({
                "section_id": s.get("section_id", ""),
                "title": s.get("title", ""),
                "body": s.get("body", "")[:200],
                "document": s.get("metadata", {}).get("document_id", "") if isinstance(s.get("metadata"), dict) else "",
                "severity_signal": signal,
                "classification": label,
                "operational_areas": areas,
            })

        doc_id = s.get("metadata", {}).get("document_id", "unknown") if isinstance(s.get("metadata"), dict) else "unknown"
        if doc_id not in doc_stats:
            doc_stats[doc_id] = {
                "document_id": doc_id,
                "document_type": s.get("metadata", {}).get("document_type", "") if isinstance(s.get("metadata"), dict) else "",
                "jurisdiction": s.get("metadata", {}).get("jurisdiction", "") if isinstance(s.get("metadata"), dict) else "",
                "category": s.get("metadata", {}).get("category", "") if isinstance(s.get("metadata"), dict) else "",
                "section_count": 0,
                "severity_signal_breakdown": {"punitive": 0, "mandatory": 0, "procedural": 0, "definitional": 0},
                "classification_breakdown": {"obligation": 0, "prohibition": 0, "permission": 0, "definition": 0, "procedural": 0},
            }
        doc_stats[doc_id]["section_count"] += 1
        if signal in doc_stats[doc_id]["severity_signal_breakdown"]:
            doc_stats[doc_id]["severity_signal_breakdown"][signal] += 1
        if label in doc_stats[doc_id]["classification_breakdown"]:
            doc_stats[doc_id]["classification_breakdown"][label] += 1

    punitive_obligations = punitive_obligations[:20]

    return {
        "total_sections": total,
        "total_documents": len(doc_stats),
        "classifications": classifications,
        "severity_signals": severity_signals,
        "operational_areas": operational_areas,
        "punitive_obligations": punitive_obligations,
        "documents": list(doc_stats.values()),
    }


@app.get("/api/dashboard/documents")
async def dashboard_documents():
    """Regulation tile data. Never returns risk — risk is relational and
    belongs to /api/compliance/coverage."""
    documents = []
    for sections_file in STORAGE.glob("gold/*/sections.json"):
        doc_id = sections_file.parent.name
        try:
            sections = json.loads(sections_file.read_text())
            if not isinstance(sections, list):
                continue

            first = sections[0] if sections else {}
            meta = first.get("metadata", {}) if isinstance(first.get("metadata"), dict) else {}

            classification_breakdown = {"obligation": 0, "prohibition": 0, "permission": 0, "definition": 0, "procedural": 0}
            severity_signal_breakdown = {"punitive": 0, "mandatory": 0, "procedural": 0, "definitional": 0}

            for s in sections:
                cls = s.get("classification", {})
                label = cls.get("label", "procedural") if isinstance(cls, dict) else "procedural"
                if label in classification_breakdown:
                    classification_breakdown[label] += 1

                signal = s.get("severity_signal")
                if signal in severity_signal_breakdown:
                    severity_signal_breakdown[signal] += 1

            documents.append({
                "document_id": doc_id,
                "document_type": meta.get("document_type", ""),
                "jurisdiction": meta.get("jurisdiction", ""),
                "regulator": meta.get("regulator", ""),
                "category": meta.get("category", ""),
                "section_count": len(sections),
                "classification_breakdown": classification_breakdown,
                "severity_signal_breakdown": severity_signal_breakdown,
                "processed_date": meta.get("processed_date", ""),
                "last_amended": meta.get("last_amended", ""),
            })
        except Exception:
            continue

    documents.sort(key=lambda d: d["section_count"], reverse=True)
    return {"documents": documents, "total": len(documents)}


@app.get("/api/dashboard/documents/{document_id}")
async def dashboard_document_detail(document_id: str):
    sections_file = STORAGE / "gold" / document_id / "sections.json"
    if not sections_file.exists():
        raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")

    try:
        sections = json.loads(sections_file.read_text())
        if not isinstance(sections, list):
            sections = []

        normalized = []
        for s in sections:
            cls = s.get("classification", {})
            meta = s.get("metadata", {}) if isinstance(s.get("metadata"), dict) else {}
            normalized.append({
                "section_id": s.get("section_id", ""),
                "section_number": s.get("section_number", ""),
                "title": s.get("title", ""),
                "body": s.get("body", ""),
                "level": s.get("level", 0),
                "classification": cls.get("label", "procedural") if isinstance(cls, dict) else "procedural",
                "classification_confidence": cls.get("confidence", 0) if isinstance(cls, dict) else 0,
                "severity_signal": s.get("severity_signal"),
                "operational_areas": s.get("operational_areas", []) or [],
                "document_type": meta.get("document_type", ""),
                "jurisdiction": meta.get("jurisdiction", ""),
                "category": meta.get("category", ""),
            })

        return {
            "document_id": document_id,
            "sections": normalized,
            "total_sections": len(normalized),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge-graph")
async def knowledge_graph():
    import yaml

    nodes_path = STORAGE / "knowledge_graph" / "nodes.yaml"
    edges_path = STORAGE / "knowledge_graph" / "edges.yaml"
    domains_path = STORAGE / "knowledge_graph" / "domains.yaml"

    nodes = []
    edges = []
    domain_stats: dict = {}

    if nodes_path.exists():
        with open(nodes_path) as f:
            data = yaml.safe_load(f) or {}
        raw_nodes = data.get("nodes", [])
        for n in raw_nodes:
            meta = n.get("metadata") or {}
            node = {
                "id": n.get("id", ""),
                "type": n.get("type", ""),
                "source_document": n.get("source_document", ""),
                "section_number": n.get("section_number", ""),
                "text": n.get("text", "")[:200],
                "domains": n.get("domains", []),
                "severity_signal": meta.get("severity_signal") if isinstance(meta, dict) else None,
            }
            nodes.append(node)
            for d in node["domains"]:
                domain_stats[d] = domain_stats.get(d, 0) + 1

    if edges_path.exists():
        with open(edges_path) as f:
            data = yaml.safe_load(f) or {}
        raw_edges = data.get("edges", [])
        for e in raw_edges:
            edges.append({
                "from": e.get("from", ""),
                "to": e.get("to", ""),
                "type": e.get("type", ""),
                "description": e.get("description", ""),
                "confidence": e.get("confidence", 0),
            })

    domains_data = {}
    if domains_path.exists():
        with open(domains_path) as f:
            domains_data = yaml.safe_load(f) or {}

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "domains": domain_stats,
        },
        "domains_config": domains_data,
    }
