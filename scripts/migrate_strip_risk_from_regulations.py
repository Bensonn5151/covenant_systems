#!/usr/bin/env python3
"""
Migration: strip risk from regulation-layer artifacts.

After this migration:
  - storage/gold/*/sections.json    — no section has a `risk` key.
                                      Obligations/prohibitions gain a
                                      `severity_signal` field; all sections
                                      gain an `operational_areas` field.
  - storage/gold/*/semantic_labels.json — no `risk` key; severity_signal
                                      present on obligation/prohibition.
  - storage/knowledge_graph/nodes.yaml — no `metadata.risk_level`. Obligation
                                      and prohibition nodes gain
                                      `metadata.severity_signal` where it
                                      can be derived from an existing risk
                                      rating.

Risk is now a relational property on policy_implements_regulation edges;
it is computed on demand by api/fastapi/compare.py when a policy is
evaluated against a regulation.

Run from repo root:
    python3 scripts/migrate_strip_risk_from_regulations.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = ROOT / "storage" / "gold"
KG_DIR = ROOT / "storage" / "knowledge_graph"
LOG_DIR = ROOT / "storage" / "migrations"

# Mapping: old coarse risk rating -> closest severity_signal.
# These were derived from keyword patterns describing regulation language,
# so a "high" rating reliably indicated punitive language (penalties,
# prohibitions, breach), "medium" indicated mandatory shall/must language,
# and "low" indicated definitional/permissive language.
RISK_TO_SIGNAL = {
    "critical": "punitive",
    "high": "punitive",
    "medium": "mandatory",
    "low": "definitional",
}


def migrate_gold_sections() -> dict:
    """Rewrite every storage/gold/*/sections.json and semantic_labels.json."""
    counts = {
        "files_rewritten": 0,
        "sections_updated": 0,
        "severity_signal_derived": 0,
        "risk_keys_removed": 0,
    }
    for sections_file in GOLD_DIR.glob("*/sections.json"):
        sections = json.loads(sections_file.read_text())
        if not isinstance(sections, list):
            continue
        dirty = False
        for s in sections:
            cls = s.get("classification") or {}
            label = cls.get("label", "") if isinstance(cls, dict) else ""
            old_risk = s.pop("risk", None)
            if old_risk is not None:
                counts["risk_keys_removed"] += 1
                dirty = True
                areas = []
                if isinstance(old_risk, dict):
                    areas = old_risk.get("operational_areas", []) or []
                # Promote operational_areas onto the section itself so
                # downstream code has one place to read it from.
                if areas and not s.get("operational_areas"):
                    s["operational_areas"] = areas
                # Derive a severity_signal for obligation/prohibition only.
                if label in ("obligation", "prohibition") and isinstance(old_risk, dict):
                    old_level = old_risk.get("risk_level")
                    sig = RISK_TO_SIGNAL.get(old_level)
                    if sig and not s.get("severity_signal"):
                        s["severity_signal"] = sig
                        counts["severity_signal_derived"] += 1
            # Ensure operational_areas exists as a list.
            s.setdefault("operational_areas", [])
            counts["sections_updated"] += 1

        if dirty:
            sections_file.write_text(
                json.dumps(sections, indent=2, ensure_ascii=False)
            )
            counts["files_rewritten"] += 1

        # Rewrite semantic_labels.json so it mirrors the new shape.
        labels_file = sections_file.parent / "semantic_labels.json"
        if labels_file.exists():
            labels = [
                {
                    "section_id": s["section_id"],
                    "classification": s.get("classification"),
                    "severity_signal": s.get("severity_signal"),
                    "operational_areas": s.get("operational_areas", []),
                }
                for s in sections
            ]
            labels_file.write_text(json.dumps(labels, indent=2))

    return counts


def migrate_kg_nodes() -> dict:
    """Rewrite storage/knowledge_graph/nodes.yaml without metadata.risk_level."""
    nodes_path = KG_DIR / "nodes.yaml"
    counts = {"nodes_seen": 0, "risk_level_removed": 0, "severity_signal_derived": 0}
    if not nodes_path.exists():
        return counts
    data = yaml.safe_load(nodes_path.read_text()) or {}
    nodes = data.get("nodes", []) or []
    for node in nodes:
        counts["nodes_seen"] += 1
        meta = node.get("metadata") or {}
        if not isinstance(meta, dict):
            continue
        old_level = meta.pop("risk_level", None)
        if old_level is not None:
            counts["risk_level_removed"] += 1
            if node.get("type") in ("obligation", "prohibition"):
                sig = RISK_TO_SIGNAL.get(old_level)
                if sig and not meta.get("severity_signal"):
                    meta["severity_signal"] = sig
                    counts["severity_signal_derived"] += 1
        node["metadata"] = meta
    nodes_path.write_text(
        yaml.dump(
            {"nodes": nodes},
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
    )
    return counts


def main() -> int:
    if not GOLD_DIR.exists():
        print(f"ERROR: {GOLD_DIR} does not exist. Run from repo root.", file=sys.stderr)
        return 1

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("MIGRATION: strip_regulation_risk")
    print("=" * 60)

    gold_counts = migrate_gold_sections()
    print(f"\nGold sections:")
    for k, v in gold_counts.items():
        print(f"  {k:32} {v}")

    kg_counts = migrate_kg_nodes()
    print(f"\nKG nodes.yaml:")
    for k, v in kg_counts.items():
        print(f"  {k:32} {v}")

    stamp = datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
    log_path = LOG_DIR / f"{stamp}_strip_regulation_risk.log"
    log_path.write_text(
        json.dumps(
            {
                "migration": "strip_regulation_risk",
                "executed_at": stamp,
                "gold": gold_counts,
                "kg": kg_counts,
            },
            indent=2,
        )
    )
    print(f"\nLog: {log_path.relative_to(ROOT)}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
