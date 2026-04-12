"""
Covenant Systems - FastAPI Backend

Exposes the regulatory compliance pipeline via REST API endpoints.
"""

import json
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

app = FastAPI(
    title="Covenant Systems API",
    description="AI Regulatory Compliance Platform - Bronze/Silver/Gold Pipeline",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
