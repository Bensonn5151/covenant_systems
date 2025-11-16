"""
Section Segmentation Module

Parses regulatory documents into structured sections using hierarchical markers.
Transforms Bronze (raw text) → Silver (structured sections).

Identifies section boundaries using patterns like:
- "1.", "2.", "3."
- "1.1", "1.2.3"
- "Section 5"
- "Part II", "Article 3"

Preserves legal text verbatim - no summarization or interpretation.
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Section:
    """Represents a parsed section from a regulatory document."""

    section_id: str
    section_number: str
    title: str
    body: str
    level: int  # Hierarchy level (1 = Part, 2 = Section, 3 = Subsection)
    parent_id: Optional[str] = None
    start_char: int = 0
    end_char: int = 0
    metadata: Dict = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        if self.metadata is None:
            data["metadata"] = {}
        return data


class SectionSegmenter:
    """Segment regulatory documents into structured sections."""

    # Regex patterns for section markers
    PATTERNS = {
        # "Part I", "Part II", "PART 1"
        "part": re.compile(r"^(PART|Part)\s+([IVXLCDMivxlcdm0-9]+)\b", re.MULTILINE),
        # "Article 5", "ARTICLE 10"
        "article": re.compile(r"^(ARTICLE|Article)\s+(\d+)\b", re.MULTILINE),
        # "Division 3", "DIVISION 2"
        "division": re.compile(r"^(DIVISION|Division)\s+(\d+)\b", re.MULTILINE),
        # "Section 12", "SECTION 5"
        "section": re.compile(r"^(SECTION|Section)\s+(\d+)\b", re.MULTILINE),
        # "12.", "5.", "1." (at start of line)
        "numbered": re.compile(r"^(\d+)\.\s+", re.MULTILINE),
        # "12.3", "5.2.1" (hierarchical numbering)
        "hierarchical": re.compile(r"^(\d+(?:\.\d+)+)\s+", re.MULTILINE),
    }

    def __init__(
        self,
        min_section_length: int = 20,
        max_section_length: int = 5000,
    ):
        """
        Initialize section segmenter.

        Args:
            min_section_length: Minimum characters for a valid section
            max_section_length: Maximum characters before splitting
        """
        self.min_section_length = min_section_length
        self.max_section_length = max_section_length

    def segment(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict] = None,
    ) -> List[Section]:
        """
        Segment document text into structured sections.

        Args:
            text: Document text
            document_id: Document identifier
            metadata: Optional metadata to attach to sections

        Returns:
            List of Section objects
        """
        if not text or not text.strip():
            return []

        # Find all section markers
        markers = self._find_section_markers(text)

        if not markers:
            # No markers found - treat as single section
            return self._create_fallback_section(text, document_id, metadata)

        # Extract sections based on markers
        sections = self._extract_sections(text, markers, document_id, metadata)

        # Filter out sections that are too short
        sections = [s for s in sections if len(s.body) >= self.min_section_length]

        return sections

    def _find_section_markers(self, text: str) -> List[Dict]:
        """
        Find all section markers in text.

        Args:
            text: Document text

        Returns:
            List of marker dictionaries with position and metadata
        """
        markers = []

        for pattern_name, pattern in self.PATTERNS.items():
            for match in pattern.finditer(text):
                marker = {
                    "type": pattern_name,
                    "position": match.start(),
                    "end_position": match.end(),
                    "full_match": match.group(0),
                    "number": self._extract_number(match),
                    "level": self._get_marker_level(pattern_name),
                }
                markers.append(marker)

        # Sort by position
        markers.sort(key=lambda x: x["position"])

        return markers

    def _extract_number(self, match: re.Match) -> str:
        """Extract section number from regex match."""
        groups = match.groups()
        if len(groups) >= 2:
            return groups[1]  # Second group is usually the number
        return groups[0] if groups else ""

    def _get_marker_level(self, pattern_name: str) -> int:
        """
        Determine hierarchy level for marker type.

        Levels:
        1 = Part
        2 = Division/Article
        3 = Section
        4 = Numbered (1., 2.)
        5 = Hierarchical (1.1, 1.2.3)
        """
        level_map = {
            "part": 1,
            "article": 2,
            "division": 2,
            "section": 3,
            "numbered": 4,
            "hierarchical": 5,
        }
        return level_map.get(pattern_name, 4)

    def _extract_sections(
        self,
        text: str,
        markers: List[Dict],
        document_id: str,
        metadata: Optional[Dict],
    ) -> List[Section]:
        """
        Extract section content between markers.

        Args:
            text: Full document text
            markers: List of section markers
            document_id: Document ID
            metadata: Document metadata

        Returns:
            List of Section objects
        """
        sections = []

        for i, marker in enumerate(markers):
            # Determine section boundaries
            start_pos = marker["position"]
            end_pos = markers[i + 1]["position"] if i + 1 < len(markers) else len(text)

            # Extract section content
            section_text = text[start_pos:end_pos].strip()

            # Split into title and body
            title, body = self._split_title_body(section_text)

            # Generate section ID
            section_id = f"{document_id}_s{i+1:03d}"

            # Create Section object
            section = Section(
                section_id=section_id,
                section_number=marker["number"],
                title=title,
                body=body,
                level=marker["level"],
                start_char=start_pos,
                end_char=end_pos,
                metadata=metadata or {},
            )

            sections.append(section)

        return sections

    def _split_title_body(self, section_text: str) -> tuple[str, str]:
        """
        Split section text into title and body.

        Args:
            section_text: Full section text

        Returns:
            Tuple of (title, body)
        """
        lines = section_text.split("\n", 1)

        if len(lines) == 1:
            # No newline - first sentence is title
            sentences = section_text.split(". ", 1)
            if len(sentences) > 1:
                return sentences[0], sentences[1]
            return section_text[:100], section_text

        # First line is title
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""

        return title, body

    def _create_fallback_section(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict],
    ) -> List[Section]:
        """
        Create fallback section when no markers found.

        Args:
            text: Full text
            document_id: Document ID
            metadata: Document metadata

        Returns:
            List containing single section
        """
        # Try to extract a title from first line/paragraph
        lines = text.split("\n", 1)
        title = lines[0][:200] if lines else "Untitled Document"
        body = lines[1] if len(lines) > 1 else text

        section = Section(
            section_id=f"{document_id}_s001",
            section_number="1",
            title=title,
            body=body,
            level=1,
            start_char=0,
            end_char=len(text),
            metadata=metadata or {},
        )

        return [section]


# Convenience function
def segment_document(
    text: str,
    document_id: str,
    metadata: Optional[Dict] = None,
) -> List[Dict]:
    """
    Segment document into sections.

    Args:
        text: Document text
        document_id: Document identifier
        metadata: Optional metadata

    Returns:
        List of section dictionaries
    """
    segmenter = SectionSegmenter()
    sections = segmenter.segment(text, document_id, metadata)
    return [section.to_dict() for section in sections]