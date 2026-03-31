"""
Cross-Reference Detector for Gold Layer

Detects intra-document and inter-document references between sections.
Produces edges for the knowledge graph.

Used by gold_builder.py.
"""

import re
from typing import Dict, List
from datetime import datetime


class CrossReferenceDetector:
    """Detect cross-references between regulatory sections."""

    REFERENCE_PATTERNS = [
        # "section 5", "subsection 4(3)", "paragraph 7(1)(a)", "clause 4.7"
        re.compile(
            r'(?:section|subsection|paragraph|clause|subclause)\s+'
            r'(\d+[\(\)\.0-9a-z]*)',
            re.IGNORECASE,
        ),
        # "under PIPEDA", "under the Privacy Act"
        re.compile(
            r'under\s+(?:the\s+)?'
            r'(PIPEDA|Privacy Act|Personal Information Protection)',
            re.IGNORECASE,
        ),
        # "Schedule 1", "Part 1"
        re.compile(r'(?:Schedule|Part)\s+(\d+|[IVXLCDM]+)', re.IGNORECASE),
    ]

    def __init__(self, all_sections: List[Dict]):
        """
        Args:
            all_sections: All Gold sections across all documents for resolution.
        """
        self.section_index = {}
        self.doc_sections = {}
        for s in all_sections:
            doc_id = s.get("metadata", {}).get("document_id", "")
            sec_num = s.get("section_number", "")
            sec_id = s.get("section_id", "")
            self.section_index[(doc_id, sec_num)] = sec_id
            self.doc_sections.setdefault(doc_id, []).append(s)

    def detect(self, section: Dict) -> List[Dict]:
        """
        Detect cross-references in a single section.

        Returns list of edge dicts for the knowledge graph.
        """
        body = section.get("body", "")
        doc_id = section.get("metadata", {}).get("document_id", "")
        from_id = section.get("section_id", "")
        edges = []

        for pattern in self.REFERENCE_PATTERNS:
            for match in pattern.finditer(body):
                ref_text = match.group(0)
                ref_number = match.group(1) if match.lastindex else ""

                # Try to resolve within same document first
                target_id = self.section_index.get((doc_id, ref_number))

                # Cross-document resolution for explicit act references
                if not target_id and "PIPEDA" in ref_text.upper():
                    target_id = self.section_index.get(("pipeda", ref_number))
                if not target_id and "Privacy Act" in ref_text:
                    target_id = self.section_index.get(("privacy_act", ref_number))

                if target_id and target_id != from_id:
                    edges.append({
                        "from": from_id,
                        "to": target_id,
                        "type": "cites",
                        "description": f"References {ref_text}",
                        "confidence": 0.85,
                        "source": "cross_reference_detector",
                        "date_created": datetime.utcnow().isoformat(),
                    })

        # Deduplicate
        seen = set()
        unique_edges = []
        for e in edges:
            key = (e["from"], e["to"], e["type"])
            if key not in seen:
                seen.add(key)
                unique_edges.append(e)

        return unique_edges

    def detect_batch(self, sections: List[Dict]) -> List[List[Dict]]:
        """Detect cross-references for all sections."""
        return [self.detect(s) for s in sections]
