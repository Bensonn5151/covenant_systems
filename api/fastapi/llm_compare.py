"""
LLM-Powered Policy-to-Regulation Comparison Engine

Replaces embedding-based cosine similarity with direct LLM reasoning.
The model reads both the policy text and regulation obligations, then
returns a structured verdict for each obligation: covered/partial/gap,
with evidence (which policy clause) and reasoning.

Uses Groq's free tier (Llama 3.3 70B) for fast inference.
"""

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from groq import Groq

STORAGE = Path("storage")
THRESHOLD = 0.5
PARTIAL_THRESHOLD = 0.35

# Groq config
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_FALLBACK_MODEL = "llama-3.1-8b-instant"

_groq_client: Optional[Groq] = None


def get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set. Add it to .env")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


# ── Residual risk (same matrix as compare.py) ────────────────────────────────

_RESIDUAL_RISK_MATRIX: Dict[str, Dict[str, str]] = {
    "punitive":     {"covered": "medium", "partial": "high",   "gap": "critical"},
    "mandatory":    {"covered": "low",    "partial": "medium", "gap": "high"},
    "procedural":   {"covered": "low",    "partial": "low",    "gap": "medium"},
    "definitional": {"covered": "low",    "partial": "low",    "gap": "low"},
}


def compute_residual_risk(severity_signal: Optional[str], coverage_status: str) -> str:
    sig = severity_signal or "mandatory"
    return _RESIDUAL_RISK_MATRIX.get(sig, _RESIDUAL_RISK_MATRIX["mandatory"]).get(
        coverage_status, "medium"
    )


# ── Loaders ──────────────────────────────────────────────────────────────────

def load_regulation_sections(regulation_id: str) -> List[Dict]:
    """Load regulation sections — from Supabase if DATABASE_URL is set, else JSON files."""
    if os.environ.get("DATABASE_URL"):
        from api.fastapi.db import get_regulation_sections
        sections = get_regulation_sections(regulation_id)
        if not sections:
            raise FileNotFoundError(f"Regulation not found: {regulation_id}")
        return sections
    # Fallback to file-based
    sections_file = STORAGE / "gold" / regulation_id / "sections.json"
    if not sections_file.exists():
        raise FileNotFoundError(f"Regulation not found: {regulation_id}")
    sections = json.loads(sections_file.read_text())
    return sections if isinstance(sections, list) else []


def get_obligation_sections(sections: List[Dict]) -> List[Dict]:
    results = []
    for s in sections:
        # DB rows have classification as a string; JSON rows have it as a dict
        cls = s.get("classification", {})
        if isinstance(cls, str):
            label = cls
        elif isinstance(cls, dict):
            label = cls.get("label", "")
        else:
            label = ""
        if label in ("obligation", "prohibition"):
            results.append(s)
    return results


def build_policy_text(policy_sections: List[Dict]) -> str:
    """Build a readable text from policy sections."""
    parts = []
    for s in policy_sections:
        title = s.get("title", "")
        body = s.get("body", "")
        if title:
            parts.append(f"## {title}\n{body}")
        else:
            parts.append(body)
    return "\n\n".join(parts)


# ── LLM Comparison ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert regulatory compliance analyst. Your job is to determine whether a company's privacy policy adequately addresses specific regulatory obligations.

For each obligation, you must return a JSON object with:
- "status": one of "covered", "partial", or "gap"
  - "covered": the policy has a clause that clearly and fully addresses this obligation
  - "partial": the policy touches on this topic but doesn't fully satisfy the obligation
  - "gap": the policy does not address this obligation at all
- "matched_clause": the title or first sentence of the policy section that best addresses this obligation (null if gap)
- "reasoning": one sentence explaining your verdict

Be strict. A policy clause must specifically address the regulatory requirement, not just mention related words. If the policy is vague where the regulation is specific, that's "partial" not "covered"."""


def _build_user_prompt(policy_text: str, obligations: List[Dict]) -> str:
    """Build the user prompt with policy text and obligations list."""
    ob_lines = []
    for i, ob in enumerate(obligations):
        sid = ob.get("section_id", f"ob-{i}")
        title = ob.get("title", "")
        body = ob.get("body", "")[:400]
        cls = ob.get("classification", "obligation")
        label = cls.get("label", "obligation") if isinstance(cls, dict) else cls if isinstance(cls, str) else "obligation"
        ob_lines.append(f'[{sid}] ({label}) {title}\n{body}')

    obligations_text = "\n\n".join(ob_lines)

    return f"""Here is the company's privacy policy:

---POLICY START---
{policy_text[:12000]}
---POLICY END---

Evaluate each of the following {len(obligations)} regulatory obligations against the policy above. Return a JSON array with one object per obligation, in the same order. Each object must have: "section_id", "status", "matched_clause", "reasoning".

---OBLIGATIONS START---
{obligations_text}
---OBLIGATIONS END---

Return ONLY valid JSON. No markdown fences, no explanation outside the JSON array."""


def _parse_llm_response(text: str, obligations: List[Dict]) -> List[Dict]:
    """Parse LLM response into structured verdicts."""
    # Strip markdown fences if present
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        verdicts = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON array in the response
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                verdicts = json.loads(match.group())
            except json.JSONDecodeError:
                # Fallback: treat everything as gaps
                return [
                    {"section_id": ob.get("section_id", ""), "status": "gap",
                     "matched_clause": None, "reasoning": "LLM response unparseable"}
                    for ob in obligations
                ]
        else:
            return [
                {"section_id": ob.get("section_id", ""), "status": "gap",
                 "matched_clause": None, "reasoning": "LLM response unparseable"}
                for ob in obligations
            ]

    if not isinstance(verdicts, list):
        verdicts = [verdicts]

    # Pad if LLM returned fewer results than obligations
    while len(verdicts) < len(obligations):
        verdicts.append({
            "section_id": obligations[len(verdicts)].get("section_id", ""),
            "status": "gap",
            "matched_clause": None,
            "reasoning": "Not evaluated by LLM",
        })

    return verdicts


def llm_compare_policy_to_regulation(
    policy_sections: List[Dict],
    regulation_id: str = "pipeda",
    policy_id: str = "uploaded_policy",
) -> Dict:
    """Compare a policy against a regulation using LLM reasoning.

    Returns the same shape as compare_policy_to_regulation() for
    backward compatibility with the dashboard.
    """
    client = get_groq_client()

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
            "partial_details": [],
            "coverage_by_area": {},
            "threshold": THRESHOLD,
        }

    policy_text = build_policy_text(policy_sections)
    prompt = _build_user_prompt(policy_text, obligations)

    # Call Groq with retry on rate limit
    verdicts = []
    # Batch obligations into chunks to stay within context limits
    batch_size = 20
    for batch_start in range(0, len(obligations), batch_size):
        batch_obs = obligations[batch_start:batch_start + batch_size]
        batch_prompt = _build_user_prompt(policy_text, batch_obs)

        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": batch_prompt},
                    ],
                    temperature=0.1,
                    max_tokens=4000,
                )
                raw = response.choices[0].message.content or "[]"
                batch_verdicts = _parse_llm_response(raw, batch_obs)
                verdicts.extend(batch_verdicts)
                break
            except Exception as e:
                err_str = str(e).lower()
                if "rate_limit" in err_str or "429" in err_str:
                    wait = 15 * (attempt + 1)
                    print(f"  Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                elif attempt == 2:
                    # Final attempt failed — mark batch as gaps
                    print(f"  LLM call failed after 3 attempts: {e}")
                    verdicts.extend([
                        {"section_id": ob.get("section_id", ""), "status": "gap",
                         "matched_clause": None, "reasoning": f"LLM error: {str(e)[:100]}"}
                        for ob in batch_obs
                    ])
                else:
                    # Try fallback model
                    try:
                        response = client.chat.completions.create(
                            model=GROQ_FALLBACK_MODEL,
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": batch_prompt},
                            ],
                            temperature=0.1,
                            max_tokens=4000,
                        )
                        raw = response.choices[0].message.content or "[]"
                        batch_verdicts = _parse_llm_response(raw, batch_obs)
                        verdicts.extend(batch_verdicts)
                        break
                    except Exception:
                        time.sleep(5)

        # Small delay between batches to respect rate limits
        if batch_start + batch_size < len(obligations):
            time.sleep(2)

    # Build the response in the same shape as the embedding-based compare
    matches = []
    gap_details = []
    partial_details = []
    area_coverage: Dict[str, Dict] = {}

    for i, ob in enumerate(obligations):
        verdict = verdicts[i] if i < len(verdicts) else {"status": "gap", "matched_clause": None, "reasoning": "Not evaluated"}
        status = verdict.get("status", "gap")
        if status not in ("covered", "partial", "gap"):
            status = "gap"

        cls = ob.get("classification", {}) or {}
        label = cls.get("label", "obligation") if isinstance(cls, dict) else "obligation"
        severity_signal = ob.get("severity_signal") or "mandatory"
        op_areas = ob.get("operational_areas", []) or []
        residual_risk = compute_residual_risk(severity_signal, status)

        # Map status to a synthetic coverage_score for UI compatibility
        score_map = {"covered": 0.85, "partial": 0.45, "gap": 0.15}
        coverage_score = score_map.get(status, 0.15)

        entry = {
            "regulation_section_id": ob.get("section_id", ""),
            "regulation_title": ob.get("title", ""),
            "regulation_body": ob.get("body", "")[:300],
            "classification": label,
            "severity_signal": severity_signal,
            "operational_areas": op_areas,
            "coverage_status": status,
            "coverage_score": coverage_score,
            "best_match_score": coverage_score,
            "residual_risk": residual_risk,
            "is_covered": status == "covered",
            "matched_policy_section": verdict.get("matched_clause"),
            "matched_policy_body": verdict.get("reasoning"),
            "evidence_policy_section_ids": [],
        }

        if status == "covered":
            matches.append(entry)
        elif status == "partial":
            partial_details.append(entry)
        else:
            gap_details.append(entry)

        for area in op_areas:
            bucket = area_coverage.setdefault(area, {"total": 0, "covered": 0})
            bucket["total"] += 1
            if status == "covered":
                bucket["covered"] += 1

    covered = len(matches)
    partial = len(partial_details)
    gaps = len(gap_details)
    total = covered + partial + gaps
    score = round((covered / total) * 100, 1) if total > 0 else 0
    overall_coverage = round(covered / total, 4) if total > 0 else 0.0

    risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    gap_details.sort(key=lambda x: risk_order.get(x["residual_risk"], 3))
    partial_details.sort(key=lambda x: risk_order.get(x["residual_risk"], 3))

    coverage_by_area = {}
    for area, counts in area_coverage.items():
        coverage_by_area[area] = {
            "total": counts["total"],
            "covered": counts["covered"],
            "percentage": round((counts["covered"] / counts["total"]) * 100, 1)
            if counts["total"] > 0 else 0,
        }

    return {
        "policy_id": policy_id,
        "regulation_id": regulation_id,
        "evaluated_at": evaluated_at,
        "overall_coverage": overall_coverage,
        "by_domain": [
            {"domain": a, "coverage": v["percentage"] / 100.0, **v}
            for a, v in coverage_by_area.items()
        ],
        "gaps": gaps,
        "gap_details": gap_details,
        "partial_details": partial_details,
        "score": score,
        "total_obligations": total,
        "covered": covered,
        "partial": partial,
        "matches": matches,
        "coverage_by_area": coverage_by_area,
        "threshold": THRESHOLD,
    }
