"""
Severity Signal Scorer for Gold Layer

Emits a language-strength label (definitional | procedural | mandatory |
punitive) for obligation / prohibition sections based on the regulation
text. This describes HOW the law is written — it is NOT a risk rating.

Risk is relational and belongs on policy_implements_regulation edges
(see api/fastapi/compare.py and CLAUDE.md §13).

Used by gold_builder.py.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List


SEVERITY_PRIORITY = ["punitive", "mandatory", "procedural", "definitional"]


class SeveritySignalScorer:
    """Classify obligation/prohibition sections by the strength of their language."""

    def __init__(self, config_path: str = "configs/section_classification.yaml"):
        config = yaml.safe_load(open(config_path))
        self.signal_config = config["severity_signals"]
        self.area_config = config.get("operational_areas", {})
        self._signal_patterns: Dict[str, list] = {}
        self._area_patterns: Dict[str, list] = {}
        self._compile()

    def _compile(self):
        for level in SEVERITY_PRIORITY:
            self._signal_patterns[level] = [
                re.compile(p, re.IGNORECASE)
                for p in self.signal_config[level]["patterns"]
            ]
        for area, rules in self.area_config.items():
            self._area_patterns[area] = [
                re.compile(p, re.IGNORECASE) for p in rules["patterns"]
            ]

    def score(self, section: Dict, classification: Dict) -> Dict:
        """Score severity signal + operational areas for a single section.

        Returns a dict with:
          severity_signal: str (one of SEVERITY_PRIORITY) or None for
                            non-obligation/prohibition classifications
          signal_counts:   dict counting pattern hits by level (debug)
          operational_areas: list[str]
        """
        body = section.get("body", "")
        title = section.get("title", "")
        text = f"{title} {body}"
        label = classification.get("label", "procedural")

        signal_counts = {
            level: sum(1 for p in self._signal_patterns[level] if p.search(text))
            for level in SEVERITY_PRIORITY
        }

        # Classification-informed boost: prohibition language is inherently
        # stronger than a generic obligation, so nudge it up a tier.
        if label == "prohibition":
            signal_counts["punitive"] += 2
        elif label == "obligation":
            signal_counts["mandatory"] += 1

        # Pick the highest-priority bucket that has any hits.
        severity_signal = None
        if label in ("obligation", "prohibition"):
            for level in SEVERITY_PRIORITY:
                if signal_counts[level] > 0:
                    severity_signal = level
                    break
            if severity_signal is None:
                severity_signal = "mandatory"  # fallback for obligation/prohibition

        areas = [
            area for area, patterns in self._area_patterns.items()
            if any(p.search(text) for p in patterns)
        ]

        return {
            "severity_signal": severity_signal,
            "signal_counts": signal_counts,
            "operational_areas": areas,
        }

    def score_batch(self, sections: List[Dict], classifications: List[Dict]) -> List[Dict]:
        return [self.score(s, c) for s, c in zip(sections, classifications)]
