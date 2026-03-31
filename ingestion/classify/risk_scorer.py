"""
Risk Scorer for Gold Layer

Assigns high/medium/low risk to classified sections.
Classification-informed: prohibitions boost to high, obligations boost to medium.

Used by gold_builder.py.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List


class RiskScorer:
    """Score sections by compliance risk level."""

    def __init__(self, config_path: str = "configs/section_classification.yaml"):
        config = yaml.safe_load(open(config_path))
        self.risk_config = config["risk_scoring"]
        self.area_config = config.get("operational_areas", {})
        self._risk_patterns = {}
        self._area_patterns = {}
        self._compile()

    def _compile(self):
        for level in ["high", "medium", "low"]:
            self._risk_patterns[level] = [
                re.compile(p, re.IGNORECASE) for p in self.risk_config[level]["patterns"]
            ]
        for area, rules in self.area_config.items():
            self._area_patterns[area] = [
                re.compile(p, re.IGNORECASE) for p in rules["patterns"]
            ]

    def score(self, section: Dict, classification: Dict) -> Dict:
        """
        Score risk for a single section.

        Args:
            section: Silver section dict
            classification: Output from SectionClassifier.classify()

        Returns:
            Dict with: risk_level, risk_counts, operational_areas
        """
        body = section.get("body", "")
        title = section.get("title", "")
        text = f"{title} {body}"
        label = classification.get("label", "procedural")

        risk_counts = {}
        for level in ["high", "medium", "low"]:
            risk_counts[level] = sum(
                1 for p in self._risk_patterns[level] if p.search(text)
            )

        # Classification-informed boosting
        if label == "prohibition":
            risk_counts["high"] += 2
        elif label == "obligation":
            risk_counts["medium"] += 1

        if risk_counts["high"] > 0:
            risk_level = "high"
        elif risk_counts["medium"] > 0:
            risk_level = "medium"
        else:
            risk_level = "low"

        areas = [
            area for area, patterns in self._area_patterns.items()
            if any(p.search(text) for p in patterns)
        ]

        return {
            "risk_level": risk_level,
            "risk_counts": risk_counts,
            "operational_areas": areas,
        }

    def score_batch(self, sections: List[Dict], classifications: List[Dict]) -> List[Dict]:
        """Score risk for all sections."""
        return [self.score(s, c) for s, c in zip(sections, classifications)]
