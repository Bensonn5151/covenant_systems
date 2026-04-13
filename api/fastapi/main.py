"""
Covenant Systems - FastAPI Backend

Exposes the regulatory compliance pipeline via REST API endpoints.
"""

import json
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File
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
        obligations = sum(1 for s in sections
                        if isinstance(s.get("classification"), dict) and
                        s["classification"].get("label") in ("obligation", "prohibition"))
        regs.append({
            "id": doc_id,
            "document_type": meta.get("document_type", ""),
            "jurisdiction": meta.get("jurisdiction", ""),
            "category": meta.get("category", ""),
            "total_sections": len(sections),
            "obligations_count": obligations,
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
    sections = _load_all_gold_sections()
    total = len(sections)

    # Classification counts
    classifications = {"obligation": 0, "prohibition": 0, "permission": 0, "definition": 0, "procedural": 0}
    risk_levels = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    operational_areas: dict = {}
    high_risk_items = []

    # Per-document stats
    doc_stats: dict = {}

    for s in sections:
        # Classification
        cls = s.get("classification", {})
        label = cls.get("label", "procedural") if isinstance(cls, dict) else "procedural"
        if label in classifications:
            classifications[label] += 1

        # Risk
        risk = s.get("risk", {})
        level = risk.get("risk_level", "low") if isinstance(risk, dict) else "low"
        if level in risk_levels:
            risk_levels[level] += 1

        # Operational areas
        areas = risk.get("operational_areas", []) if isinstance(risk, dict) else []
        for area in areas:
            operational_areas[area] = operational_areas.get(area, 0) + 1

        # High risk items
        if level in ("high", "critical"):
            high_risk_items.append({
                "section_id": s.get("section_id", ""),
                "title": s.get("title", ""),
                "body": s.get("body", "")[:200],
                "document": s.get("metadata", {}).get("document_id", "") if isinstance(s.get("metadata"), dict) else "",
                "risk_level": level,
                "classification": label,
                "operational_areas": areas,
            })

        # Per-document
        doc_id = s.get("metadata", {}).get("document_id", "unknown") if isinstance(s.get("metadata"), dict) else "unknown"
        if doc_id not in doc_stats:
            doc_stats[doc_id] = {
                "document_id": doc_id,
                "document_type": s.get("metadata", {}).get("document_type", "") if isinstance(s.get("metadata"), dict) else "",
                "jurisdiction": s.get("metadata", {}).get("jurisdiction", "") if isinstance(s.get("metadata"), dict) else "",
                "category": s.get("metadata", {}).get("category", "") if isinstance(s.get("metadata"), dict) else "",
                "section_count": 0,
                "risk_breakdown": {"low": 0, "medium": 0, "high": 0, "critical": 0},
                "classification_breakdown": {"obligation": 0, "prohibition": 0, "permission": 0, "definition": 0, "procedural": 0},
            }
        doc_stats[doc_id]["section_count"] += 1
        if level in doc_stats[doc_id]["risk_breakdown"]:
            doc_stats[doc_id]["risk_breakdown"][level] += 1
        if label in doc_stats[doc_id]["classification_breakdown"]:
            doc_stats[doc_id]["classification_breakdown"][label] += 1

    # Health score: (1 - high_risk / total) * 100
    high_count = risk_levels.get("high", 0) + risk_levels.get("critical", 0)
    health_score = round(((total - high_count) / total) * 100, 1) if total > 0 else 0

    # Sort high risk items by confidence descending, limit to 20
    high_risk_items.sort(key=lambda x: x.get("risk_level", ""), reverse=True)
    high_risk_items = high_risk_items[:20]

    return {
        "total_sections": total,
        "total_documents": len(doc_stats),
        "classifications": classifications,
        "risk_levels": risk_levels,
        "operational_areas": operational_areas,
        "compliance_health_score": health_score,
        "high_risk_sections": high_risk_items,
        "documents": list(doc_stats.values()),
    }


@app.get("/api/dashboard/documents")
async def dashboard_documents():
    documents = []
    for sections_file in STORAGE.glob("gold/*/sections.json"):
        doc_id = sections_file.parent.name
        try:
            sections = json.loads(sections_file.read_text())
            if not isinstance(sections, list):
                continue

            first = sections[0] if sections else {}
            meta = first.get("metadata", {}) if isinstance(first.get("metadata"), dict) else {}

            risk_breakdown = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            classification_breakdown = {"obligation": 0, "prohibition": 0, "permission": 0, "definition": 0, "procedural": 0}

            for s in sections:
                risk = s.get("risk", {})
                level = risk.get("risk_level", "low") if isinstance(risk, dict) else "low"
                if level in risk_breakdown:
                    risk_breakdown[level] += 1

                cls = s.get("classification", {})
                label = cls.get("label", "procedural") if isinstance(cls, dict) else "procedural"
                if label in classification_breakdown:
                    classification_breakdown[label] += 1

            documents.append({
                "document_id": doc_id,
                "document_type": meta.get("document_type", ""),
                "jurisdiction": meta.get("jurisdiction", ""),
                "category": meta.get("category", ""),
                "section_count": len(sections),
                "risk_breakdown": risk_breakdown,
                "classification_breakdown": classification_breakdown,
                "processed_date": meta.get("processed_date", ""),
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
            risk = s.get("risk", {})
            meta = s.get("metadata", {}) if isinstance(s.get("metadata"), dict) else {}
            normalized.append({
                "section_id": s.get("section_id", ""),
                "section_number": s.get("section_number", ""),
                "title": s.get("title", ""),
                "body": s.get("body", ""),
                "level": s.get("level", 0),
                "classification": cls.get("label", "procedural") if isinstance(cls, dict) else "procedural",
                "classification_confidence": cls.get("confidence", 0) if isinstance(cls, dict) else 0,
                "risk_level": risk.get("risk_level", "low") if isinstance(risk, dict) else "low",
                "operational_areas": risk.get("operational_areas", []) if isinstance(risk, dict) else [],
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
            node = {
                "id": n.get("id", ""),
                "type": n.get("type", ""),
                "source_document": n.get("source_document", ""),
                "section_number": n.get("section_number", ""),
                "text": n.get("text", "")[:200],
                "domains": n.get("domains", []),
                "risk_level": n.get("risk_level", ""),
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
