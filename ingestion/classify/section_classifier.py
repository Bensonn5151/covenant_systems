"""
Section-Level Classifier for Gold Layer

Classifies Silver sections as: obligation, permission, prohibition, definition, procedural.
Rule-based approach using regex patterns on legal modal verbs.

Used by gold_builder.py to enrich Silver sections with semantic labels.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List


class SectionClassifier:
    """Classify regulatory sections by legal function."""

    def __init__(self, config_path: str = "configs/section_classification.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.classification_rules = self.config["classification"]
        self._compiled = {}
        self._compile_patterns()

    def _load_config(self) -> Dict:
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def _compile_patterns(self):
        for label, rules in self.classification_rules.items():
            self._compiled[label] = [
                re.compile(p, re.IGNORECASE) for p in rules["patterns"]
            ]

    def classify(self, section: Dict) -> Dict:
        """
        Classify a single section.

        Args:
            section: Silver section dict with body, title, section_type fields

        Returns:
            Dict with: label, confidence, all_matches, uncertain, short_section
        """
        body = section.get("body", "")
        title = section.get("title", "")
        text = f"{title} {body}"

        scores = {}
        match_details = {}

        for label, patterns in self._compiled.items():
            matches = []
            for pattern in patterns:
                found = pattern.findall(text)
                matches.extend(found)
            scores[label] = len(matches)
            match_details[label] = matches

        is_short = len(body) < 50

        # No matches at all
        if sum(scores.values()) == 0:
            return {
                "label": "procedural",
                "confidence": 0.30 if is_short else 0.40,
                "all_matches": {},
                "uncertain": True,
                "short_section": is_short,
            }

        # Prohibition must be checked before obligation:
        # "shall not" contains "shall" — deduct prohibition matches from obligation
        if scores.get("prohibition", 0) > 0 and scores.get("obligation", 0) > 0:
            scores["obligation"] = max(0, scores["obligation"] - scores["prohibition"])

        # "may not" matched both prohibition and permission — deduct
        if scores.get("prohibition", 0) > 0 and scores.get("permission", 0) > 0:
            scores["permission"] = max(0, scores["permission"] - scores["prohibition"])

        if sum(scores.values()) == 0:
            return {
                "label": "procedural",
                "confidence": 0.40,
                "all_matches": {k: v for k, v in match_details.items() if v},
                "uncertain": True,
                "short_section": is_short,
            }

        best_label = max(scores, key=scores.get)
        total_matches = sum(scores.values())
        raw_confidence = scores[best_label] / total_matches if total_matches > 0 else 0

        min_conf = self.classification_rules[best_label].get("min_confidence", 0.5)
        confidence = max(raw_confidence, min_conf) if scores[best_label] > 0 else 0.4

        if is_short:
            confidence = min(confidence, 0.50)

        uncertain = confidence < 0.75

        return {
            "label": best_label,
            "confidence": round(confidence, 3),
            "all_matches": {k: v for k, v in match_details.items() if v},
            "uncertain": uncertain,
            "short_section": is_short,
        }

    def classify_batch(self, sections: List[Dict]) -> List[Dict]:
        """Classify all sections."""
        return [self.classify(s) for s in sections]
