"""
Policy-to-Regulation Comparison Engine

Compares company policy sections against regulatory obligations using
semantic similarity (embeddings + cosine similarity). No LLM calls needed.

IMPORTANT — ontology:
  Regulations own NO risk. This module computes residual_risk as a property
  of the mapping edge between a policy clause and a regulatory obligation:

      residual_risk = f(severity_signal, coverage_status, coverage_score)

  severity_signal is a language-strength label on the regulation text
  itself (definitional / procedural / mandatory / punitive). Residual risk
  is what remains for the company AFTER coverage is taken into account.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

STORAGE = Path("storage")
THRESHOLD = 0.5         # >= THRESHOLD => covered; < THRESHOLD => gap
PARTIAL_THRESHOLD = 0.35  # [PARTIAL_THRESHOLD, THRESHOLD) => partial


# ──────────────────────────────────────────────────────────────────────────
# Residual risk model
# ──────────────────────────────────────────────────────────────────────────
# severity_signal is language strength on the regulation. residual_risk is
# derived from severity combined with how well the policy covers the
# obligation. A gap against a punitive obligation is the worst case; a
# full match against a definitional section is the best case.

_RESIDUAL_RISK_MATRIX: Dict[str, Dict[str, str]] = {
    # severity_signal → coverage_status → residual_risk
    "punitive":     {"covered": "medium", "partial": "high",   "gap": "critical"},
    "mandatory":    {"covered": "low",    "partial": "medium", "gap": "high"},
    "procedural":   {"covered": "low",    "partial": "low",    "gap": "medium"},
    "definitional": {"covered": "low",    "partial": "low",    "gap": "low"},
}


def compute_residual_risk(severity_signal: Optional[str], coverage_status: str) -> str:
    """Compute residual risk for one policy ↔ regulation mapping edge."""
    sig = severity_signal or "mandatory"
    return _RESIDUAL_RISK_MATRIX.get(sig, _RESIDUAL_RISK_MATRIX["mandatory"]).get(
        coverage_status, "medium"
    )


def classify_coverage(score: float, threshold: float = THRESHOLD) -> str:
    if score >= threshold:
        return "covered"
    if score >= PARTIAL_THRESHOLD:
        return "partial"
    return "gap"


# ──────────────────────────────────────────────────────────────────────────
# Parsing
# ──────────────────────────────────────────────────────────────────────────
def parse_text_to_sections(text: str) -> List[Dict]:
    """Split a plain text policy into sections by numbered headers or ALL-CAPS headers."""
    lines = text.strip().split("\n")
    sections: List[Dict] = []
    current_title = ""
    current_body_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        is_numbered = re.match(r"^\d+\.?\s+[A-Z]", stripped)
        is_allcaps = stripped.isupper() and 3 < len(stripped) < 80 and not stripped.startswith("VERSION")

        if is_numbered or is_allcaps:
            if current_title and current_body_lines:
                body = "\n".join(current_body_lines).strip()
                if len(body) > 20:
                    sections.append({
                        "section_id": f"policy-s{len(sections)+1:03d}",
                        "title": current_title,
                        "body": body,
                    })
            current_title = stripped
            current_body_lines = []
        else:
            if stripped:
                current_body_lines.append(stripped)

    if current_title and current_body_lines:
        body = "\n".join(current_body_lines).strip()
        if len(body) > 20:
            sections.append({
                "section_id": f"policy-s{len(sections)+1:03d}",
                "title": current_title,
                "body": body,
            })

    return sections


def load_regulation_sections(regulation_id: str) -> List[Dict]:
    """Load Gold layer sections for a regulation."""
    sections_file = STORAGE / "gold" / regulation_id / "sections.json"
    if not sections_file.exists():
        raise FileNotFoundError(f"Regulation not found: {regulation_id}")
    sections = json.loads(sections_file.read_text())
    return sections if isinstance(sections, list) else []


def get_obligation_sections(sections: List[Dict]) -> List[Dict]:
    """Filter to obligation and prohibition sections — the ones that matter for compliance."""
    results = []
    for s in sections:
        cls = s.get("classification", {})
        label = cls.get("label", "") if isinstance(cls, dict) else ""
        if label in ("obligation", "prohibition"):
            results.append(s)
    return results


# ──────────────────────────────────────────────────────────────────────────
# Core comparison
# ──────────────────────────────────────────────────────────────────────────
def compare_policy_to_regulation(
    policy_sections: List[Dict],
    regulation_id: str = "pipeda",
    threshold: float = THRESHOLD,
    policy_id: str = "uploaded_policy",
    embedder: Optional[object] = None,
    policy_embeddings: Optional[np.ndarray] = None,
) -> Dict:
    """Compare company policy sections against a regulation.

    For each regulation obligation/prohibition, find the best matching
    policy section using cosine similarity of embeddings, then compute
    a residual_risk value on the resulting mapping edge.

    Pass `embedder` and `policy_embeddings` to reuse across multiple
    regulation comparisons (avoids reloading the model and re-embedding
    the policy for each regulation).
    """
    reg_sections = load_regulation_sections(regulation_id)
    obligations = get_obligation_sections(reg_sections)

    evaluated_at = datetime.utcnow().isoformat() + "Z"

    if not obligations:
        return {
            "policy_id": policy_id,
            "regulation_id": regulation_id,
            "evaluated_at": evaluated_at,
            "overall_coverage": 0.0,
            "score": 0,
            "total_obligations": 0,
            "covered": 0,
            "gaps": 0,
            "partial": 0,
            "matches": [],
            "gap_details": [],
            "coverage_by_area": {},
            "threshold": threshold,
        }

    if embedder is None:
        from ingestion.embed.embedder import get_embedder
        embedder = get_embedder()

    if policy_embeddings is None:
        policy_texts = [s.get("body", s.get("title", "")) for s in policy_sections]
        policy_embeddings = embedder.embed_texts(policy_texts)

    reg_texts = [s.get("body", s.get("title", "")) for s in obligations]
    reg_embeddings = embedder.embed_texts(reg_texts)

    policy_norms = policy_embeddings / (np.linalg.norm(policy_embeddings, axis=1, keepdims=True) + 1e-10)
    reg_norms = reg_embeddings / (np.linalg.norm(reg_embeddings, axis=1, keepdims=True) + 1e-10)
    similarity_matrix = np.dot(reg_norms, policy_norms.T)

    matches: List[Dict] = []
    gap_details: List[Dict] = []
    partial_details: List[Dict] = []
    area_coverage: Dict[str, Dict] = {}

    for i, reg_section in enumerate(obligations):
        best_idx = int(np.argmax(similarity_matrix[i]))
        best_score = float(similarity_matrix[i][best_idx])
        coverage_status = classify_coverage(best_score, threshold)
        is_covered = coverage_status == "covered"

        cls = reg_section.get("classification", {}) or {}
        label = cls.get("label", "obligation") if isinstance(cls, dict) else "obligation"

        # severity_signal may live at the top level (new shape) or
        # nowhere (migrated data without it). Fall back to "mandatory".
        severity_signal = reg_section.get("severity_signal") or "mandatory"
        op_areas = reg_section.get("operational_areas", []) or []

        residual_risk = compute_residual_risk(severity_signal, coverage_status)

        entry = {
            # Regulation side
            "regulation_section_id": reg_section.get("section_id", ""),
            "regulation_title": reg_section.get("title", ""),
            "regulation_body": reg_section.get("body", "")[:300],
            "classification": label,
            "severity_signal": severity_signal,
            "operational_areas": op_areas,
            # Mapping edge
            "coverage_status": coverage_status,
            "coverage_score": round(best_score, 4),
            "best_match_score": round(best_score, 4),  # alias for legacy clients
            "residual_risk": residual_risk,
            "is_covered": is_covered,
            # Policy side (only exposed when a real match exists)
            "matched_policy_section": (
                policy_sections[best_idx].get("title", "")
                if best_score >= PARTIAL_THRESHOLD
                else None
            ),
            "matched_policy_body": (
                policy_sections[best_idx].get("body", "")[:200]
                if best_score >= PARTIAL_THRESHOLD
                else None
            ),
            "evidence_policy_section_ids": (
                [policy_sections[best_idx].get("section_id", "")]
                if best_score >= PARTIAL_THRESHOLD
                else []
            ),
        }

        if coverage_status == "covered":
            matches.append(entry)
        elif coverage_status == "partial":
            partial_details.append(entry)
        else:
            gap_details.append(entry)

        for area in op_areas:
            bucket = area_coverage.setdefault(area, {"total": 0, "covered": 0})
            bucket["total"] += 1
            if is_covered:
                bucket["covered"] += 1

    covered = len(matches)
    partial = len(partial_details)
    gaps = len(gap_details)
    total = covered + partial + gaps
    score = round((covered / total) * 100, 1) if total > 0 else 0
    overall_coverage = round(covered / total, 4) if total > 0 else 0.0

    # Sort gaps by residual risk desc, then by score asc.
    risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    gap_details.sort(key=lambda x: (risk_order.get(x["residual_risk"], 3), x["coverage_score"]))
    partial_details.sort(key=lambda x: (risk_order.get(x["residual_risk"], 3), -x["coverage_score"]))

    coverage_by_area: Dict[str, Dict] = {}
    for area, counts in area_coverage.items():
        coverage_by_area[area] = {
            "total": counts["total"],
            "covered": counts["covered"],
            "percentage": round((counts["covered"] / counts["total"]) * 100, 1)
            if counts["total"] > 0 else 0,
        }

    return {
        # New contract (used by /api/compliance/coverage)
        "policy_id": policy_id,
        "regulation_id": regulation_id,
        "evaluated_at": evaluated_at,
        "overall_coverage": overall_coverage,
        "by_domain": [
            {"domain": a, "coverage": v["percentage"] / 100.0, **v}
            for a, v in coverage_by_area.items()
        ],
        "gaps": gaps,                # count (legacy)
        "gap_details": gap_details,
        "partial_details": partial_details,
        # Legacy shape (kept for /api/compare consumers)
        "score": score,
        "total_obligations": total,
        "covered": covered,
        "partial": partial,
        "matches": matches,
        "coverage_by_area": coverage_by_area,
        "threshold": threshold,
    }
