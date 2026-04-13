"""
Policy-to-Regulation Comparison Engine

Compares company policy sections against regulatory obligations using
semantic similarity (embeddings + cosine similarity). No LLM calls needed.
"""

import json
import re
import numpy as np
from pathlib import Path
from typing import List, Dict

STORAGE = Path("storage")
THRESHOLD = 0.5  # Score > 0.5 = covered, < 0.5 = gap


def parse_text_to_sections(text: str) -> List[Dict]:
    """Split a plain text policy into sections by numbered headers or ALL-CAPS headers."""
    lines = text.strip().split("\n")
    sections = []
    current_title = ""
    current_body_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        # Detect section headers: "1. TITLE", "SECTION TITLE" (all caps, short)
        is_numbered = re.match(r"^\d+\.?\s+[A-Z]", stripped)
        is_allcaps = stripped.isupper() and 3 < len(stripped) < 80 and not stripped.startswith("VERSION")

        if is_numbered or is_allcaps:
            # Save previous section
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

    # Save last section
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


def compare_policy_to_regulation(
    policy_sections: List[Dict],
    regulation_id: str = "pipeda",
    threshold: float = THRESHOLD,
) -> Dict:
    """
    Compare company policy sections against a regulation.

    For each regulation obligation/prohibition, find the best matching
    policy section using cosine similarity of embeddings.

    Returns:
        {
            score: float (0-100),
            total_obligations: int,
            covered: int,
            gaps: int,
            matches: [...],
            gap_details: [...],
            coverage_by_area: {...},
        }
    """
    from ingestion.embed.embedder import Embedder

    # Load regulation sections
    reg_sections = load_regulation_sections(regulation_id)
    obligations = get_obligation_sections(reg_sections)

    if not obligations:
        return {"score": 0, "total_obligations": 0, "covered": 0, "gaps": 0,
                "matches": [], "gap_details": [], "coverage_by_area": {}}

    # Initialize embedder
    embedder = Embedder()

    # Embed policy sections
    policy_texts = [s.get("body", s.get("title", "")) for s in policy_sections]
    policy_embeddings = embedder.embed_texts(policy_texts)

    # Embed regulation obligations
    reg_texts = [s.get("body", s.get("title", "")) for s in obligations]
    reg_embeddings = embedder.embed_texts(reg_texts)

    # Normalize for cosine similarity
    policy_norms = policy_embeddings / (np.linalg.norm(policy_embeddings, axis=1, keepdims=True) + 1e-10)
    reg_norms = reg_embeddings / (np.linalg.norm(reg_embeddings, axis=1, keepdims=True) + 1e-10)

    # Compute similarity matrix: (num_obligations x num_policy_sections)
    similarity_matrix = np.dot(reg_norms, policy_norms.T)

    matches = []
    gap_details = []
    area_coverage: Dict[str, Dict] = {}  # area -> {total, covered}

    for i, reg_section in enumerate(obligations):
        best_idx = int(np.argmax(similarity_matrix[i]))
        best_score = float(similarity_matrix[i][best_idx])
        is_covered = best_score >= threshold

        cls = reg_section.get("classification", {})
        risk = reg_section.get("risk", {})
        label = cls.get("label", "obligation") if isinstance(cls, dict) else "obligation"
        risk_level = risk.get("risk_level", "low") if isinstance(risk, dict) else "low"
        op_areas = risk.get("operational_areas", []) if isinstance(risk, dict) else []

        entry = {
            "regulation_section_id": reg_section.get("section_id", ""),
            "regulation_title": reg_section.get("title", ""),
            "regulation_body": reg_section.get("body", "")[:300],
            "classification": label,
            "risk_level": risk_level,
            "operational_areas": op_areas,
            "best_match_score": round(best_score, 4),
            "matched_policy_section": policy_sections[best_idx].get("title", "") if is_covered else None,
            "matched_policy_body": policy_sections[best_idx].get("body", "")[:200] if is_covered else None,
            "is_covered": is_covered,
        }

        if is_covered:
            matches.append(entry)
        else:
            gap_details.append(entry)

        # Track coverage by operational area
        for area in op_areas:
            if area not in area_coverage:
                area_coverage[area] = {"total": 0, "covered": 0}
            area_coverage[area]["total"] += 1
            if is_covered:
                area_coverage[area]["covered"] += 1

    covered = len(matches)
    gaps = len(gap_details)
    total = covered + gaps
    score = round((covered / total) * 100, 1) if total > 0 else 0

    # Sort gaps by risk level (high first)
    risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    gap_details.sort(key=lambda x: risk_order.get(x["risk_level"], 3))

    # Format coverage by area
    coverage_by_area = {}
    for area, counts in area_coverage.items():
        coverage_by_area[area] = {
            "total": counts["total"],
            "covered": counts["covered"],
            "percentage": round((counts["covered"] / counts["total"]) * 100, 1) if counts["total"] > 0 else 0,
        }

    return {
        "score": score,
        "total_obligations": total,
        "covered": covered,
        "gaps": gaps,
        "matches": matches,
        "gap_details": gap_details,
        "coverage_by_area": coverage_by_area,
        "regulation_id": regulation_id,
        "threshold": threshold,
    }
