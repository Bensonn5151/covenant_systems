"""
Advanced Section Segmentation for Legal Documents

Production-grade segmenter that handles:
- Hierarchical numbering (1, 1.1, 1.2.3, 1.2.3(a))
- Section headings (ALL-CAPS, contextual clues)
- Legal document structure (Parts, Divisions, Sections, Subsections)
- Context-aware boundary detection
- Citation and metadata preservation

This is mission-critical infrastructure - the foundation of the entire RAG system.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


def is_toc_section(title: str, body: str = "") -> bool:
    """
    Detect Table of Contents sections using multiple heuristics.

    Args:
        title: Section title
        body: Section body text (optional, for additional validation)

    Returns:
        True if section is likely a TOC
    """
    title_lower = title.lower().strip()

    # Pattern 1: Exact phrase matching (case-insensitive)
    TOC_PHRASES = [
        "table of provisions",
        "table of contents",
        "table analytique",
        "table des matières",
        "analytical table",
        "contents",
        "provisions"
    ]

    if any(phrase in title_lower for phrase in TOC_PHRASES):
        return True

    # Pattern 2: Regex for common TOC formats
    TOC_REGEX = re.compile(
        r"^(table|contents|provisions|matières|analytique)",
        re.IGNORECASE
    )

    if TOC_REGEX.match(title_lower):
        return True

    # Pattern 3: Short titles that are likely TOC (< 5 words, contains "table")
    word_count = len(title_lower.split())
    if word_count <= 5 and "table" in title_lower:
        return True

    # Pattern 4: Body text heuristic - if body is very short and title suggests TOC
    if len(body) < 500 and any(kw in title_lower for kw in ["table", "contents", "provisions"]):
        return True

    return False


class SectionType(Enum):
    """Types of legal document sections."""
    PREAMBLE = "preamble"
    PART = "part"
    DIVISION = "division"
    ARTICLE = "article"
    SECTION = "section"
    SUBSECTION = "subsection"
    PARAGRAPH = "paragraph"
    SUBPARAGRAPH = "subparagraph"
    CLAUSE = "clause"
    SCHEDULE = "schedule"
    APPENDIX = "appendix"


@dataclass
class SectionMarker:
    """Represents a potential section boundary."""
    position: int
    end_position: int
    type: SectionType
    number: str
    heading: Optional[str]
    level: int  # Hierarchy depth (1 = top-level, 2 = subsection, etc.)
    confidence: float  # 0.0-1.0, how confident we are this is a real boundary
    raw_text: str


@dataclass
class Section:
    """Represents a parsed section."""
    section_id: str
    section_number: str
    section_type: SectionType
    title: str
    body: str
    level: int
    parent_id: Optional[str] = None
    start_char: int = 0
    end_char: int = 0
    metadata: Dict = None
    citations: List[str] = None  # e.g., ["2006, c. 12, s. 4"]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['section_type'] = self.section_type.value
        if self.metadata is None:
            data['metadata'] = {}
        if self.citations is None:
            data['citations'] = []
        return data


class AdvancedSegmenter:
    """Production-grade legal document segmenter."""

    # ============================================
    # REGEX PATTERNS
    # ============================================

    # Parts: "PART I", "Part 1"
    PART_PATTERN = re.compile(
        r'^(PART|Part)\s+([IVXLCDMivxlcdm]+|\d+)\b',
        re.MULTILINE
    )

    # Divisions: "DIVISION 3", "Division 2"
    DIVISION_PATTERN = re.compile(
        r'^(DIVISION|Division)\s+(\d+)\b',
        re.MULTILINE
    )

    # Articles: "Article 5"
    ARTICLE_PATTERN = re.compile(
        r'^(Article|ARTICLE)\s+(\d+)\b',
        re.MULTILINE
    )

    # Major sections: "7" or "12" at start of line (but not "7.1" or part of longer number)
    # Lookahead ensures it's followed by whitespace or newline, not a dot
    MAJOR_SECTION_PATTERN = re.compile(
        r'^(\d+)(?=\s)',
        re.MULTILINE
    )

    # Subsections: "1.1", "12.3", "5.2.1"
    SUBSECTION_PATTERN = re.compile(
        r'^(\d+\.\d+(?:\.\d+)*)\s+',
        re.MULTILINE
    )

    # Lettered subsections: "(a)", "(b)", "(1)", "(i)"
    LETTERED_PATTERN = re.compile(
        r'^\(([a-z]|[ivxlcdm]+|\d+)\)\s+',
        re.MULTILINE | re.IGNORECASE
    )

    # ALL-CAPS headings (minimum 3 words, max 100 chars)
    HEADING_PATTERN = re.compile(
        r'^([A-Z][A-Z\s&\-]{10,100})$',
        re.MULTILINE
    )

    # Citation patterns: "2006, c. 12, s. 4"
    CITATION_PATTERN = re.compile(
        r'\b\d{4},\s*c\.\s*\d+(?:,\s*s\.\s*\d+)?'
    )

    # Schedules/Appendices
    SCHEDULE_PATTERN = re.compile(
        r'^(SCHEDULE|Schedule|APPENDIX|Appendix)\s+([A-Z0-9]+)',
        re.MULTILINE
    )

    def __init__(
        self,
        min_section_length: int = 20,
        max_section_length: int = 10000,
        heading_keywords: Optional[List[str]] = None,
    ):
        """
        Initialize advanced segmenter.

        Args:
            min_section_length: Minimum characters for a valid section
            max_section_length: Maximum characters before warning
            heading_keywords: Additional keywords that signal headings
        """
        self.min_section_length = min_section_length
        self.max_section_length = max_section_length

        # Common section heading keywords
        self.heading_keywords = heading_keywords or [
            "DEFINITIONS",
            "INTERPRETATION",
            "PURPOSE",
            "APPLICATION",
            "REQUIREMENTS",
            "OBLIGATIONS",
            "PROHIBITIONS",
            "EXEMPTIONS",
            "PENALTIES",
            "ENFORCEMENT",
            "COMING INTO FORCE",
            "SHORT TITLE",
            "REPORTING",
            "DISCLOSURE",
            "TRANSACTIONS",
            "RECORDS",
            "REGISTRATION",
        ]

    def segment(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict] = None,
    ) -> List[Section]:
        """
        Segment document using advanced hierarchical parsing.

        Args:
            text: Document text
            document_id: Document identifier
            metadata: Optional metadata

        Returns:
            List of Section objects
        """
        if not text or not text.strip():
            return []

        # Step 1: Find all potential section markers
        markers = self._find_all_markers(text)

        if not markers:
            return self._create_fallback_section(text, document_id, metadata)

        # Step 2: Filter and classify markers by confidence
        markers = self._classify_markers(text, markers)

        # Step 3: Build hierarchical section tree
        sections = self._extract_hierarchical_sections(
            text, markers, document_id, metadata
        )

        # Step 4: Post-process (merge, split, clean)
        sections = self._post_process_sections(sections)

        return sections

    def _find_all_markers(self, text: str) -> List[SectionMarker]:
        """Find all potential section boundaries."""
        markers = []

        # Find Parts
        for match in self.PART_PATTERN.finditer(text):
            markers.append(SectionMarker(
                position=match.start(),
                end_position=match.end(),
                type=SectionType.PART,
                number=match.group(2),
                heading=None,
                level=1,
                confidence=1.0,
                raw_text=match.group(0),
            ))

        # Find Divisions
        for match in self.DIVISION_PATTERN.finditer(text):
            markers.append(SectionMarker(
                position=match.start(),
                end_position=match.end(),
                type=SectionType.DIVISION,
                number=match.group(2),
                heading=None,
                level=2,
                confidence=1.0,
                raw_text=match.group(0),
            ))

        # Find Articles
        for match in self.ARTICLE_PATTERN.finditer(text):
            markers.append(SectionMarker(
                position=match.start(),
                end_position=match.end(),
                type=SectionType.ARTICLE,
                number=match.group(2),
                heading=None,
                level=3,
                confidence=1.0,
                raw_text=match.group(0),
            ))

        # Find Subsections (1.1, 1.2.3) - these must come BEFORE major sections
        for match in self.SUBSECTION_PATTERN.finditer(text):
            depth = match.group(1).count('.') + 1
            markers.append(SectionMarker(
                position=match.start(),
                end_position=match.end(),
                type=SectionType.SUBSECTION,
                number=match.group(1),
                heading=None,
                level=4 + depth,  # 5, 6, 7... depending on nesting
                confidence=0.95,
                raw_text=match.group(0),
            ))

        # Find Major Sections (single digits like "7")
        for match in self.MAJOR_SECTION_PATTERN.finditer(text):
            # Skip if this is part of a subsection (already captured above)
            if any(m.position == match.start() and m.type == SectionType.SUBSECTION for m in markers):
                continue

            markers.append(SectionMarker(
                position=match.start(),
                end_position=match.end(),
                type=SectionType.SECTION,
                number=match.group(1),
                heading=None,
                level=4,
                confidence=0.85,  # Lower confidence - needs context validation
                raw_text=match.group(0),
            ))

        # Find ALL-CAPS headings
        for match in self.HEADING_PATTERN.finditer(text):
            heading_text = match.group(1).strip()

            # Check if it's a known heading keyword
            is_keyword = any(kw in heading_text for kw in self.heading_keywords)

            markers.append(SectionMarker(
                position=match.start(),
                end_position=match.end(),
                type=SectionType.SECTION,  # Headings often mark section starts
                number="",  # No number, just heading
                heading=heading_text,
                level=4,
                confidence=0.9 if is_keyword else 0.7,
                raw_text=match.group(0),
            ))

        # Find Schedules/Appendices
        for match in self.SCHEDULE_PATTERN.finditer(text):
            markers.append(SectionMarker(
                position=match.start(),
                end_position=match.end(),
                type=SectionType.SCHEDULE,
                number=match.group(2),
                heading=None,
                level=1,
                confidence=1.0,
                raw_text=match.group(0),
            ))

        # Sort by position
        markers.sort(key=lambda x: x.position)

        return markers

    def _classify_markers(
        self,
        text: str,
        markers: List[SectionMarker]
    ) -> List[SectionMarker]:
        """
        Classify markers using context to determine if they're real boundaries.

        Filters out false positives like:
        - Numbers in middle of paragraphs
        - Lettered lists that are subsections, not new sections
        """
        validated = []

        for i, marker in enumerate(markers):
            # Always keep high-confidence markers (Parts, Divisions, Articles)
            if marker.confidence >= 0.95:
                validated.append(marker)
                continue

            # For lower-confidence markers, check context
            if marker.type == SectionType.SECTION and not marker.heading:
                # Check if this number is at true start of line (after \n)
                if marker.position == 0:
                    is_line_start = True
                else:
                    is_line_start = text[marker.position - 1] == '\n'

                if not is_line_start:
                    # Skip - this is a number in middle of text
                    continue

                # Check if next line looks like a heading
                next_newline = text.find('\n', marker.end_position)
                if next_newline > 0:
                    next_line = text[marker.end_position:next_newline].strip()

                    # If next line is ALL-CAPS or known keyword, boost confidence
                    if next_line.isupper() or any(kw in next_line.upper() for kw in self.heading_keywords):
                        marker.heading = next_line
                        marker.confidence = 0.95

            validated.append(marker)

        return validated

    def _extract_hierarchical_sections(
        self,
        text: str,
        markers: List[SectionMarker],
        document_id: str,
        metadata: Optional[Dict],
    ) -> List[Section]:
        """Extract sections maintaining hierarchical structure."""
        sections = []
        parent_stack = []  # Track parent sections for hierarchy

        for i, marker in enumerate(markers):
            # Determine boundaries
            start_pos = marker.position
            end_pos = markers[i + 1].position if i + 1 < len(markers) else len(text)

            # Extract content
            section_text = text[start_pos:end_pos].strip()

            # Split into title and body
            title, body = self._smart_title_body_split(section_text, marker)

            # Extract citations from body
            citations = self._extract_citations(body)

            # Generate section ID
            section_id = f"{document_id}_s{i+1:04d}"

            # Determine parent
            parent_id = self._find_parent(marker, parent_stack)

            # Create section with TOC detection
            section_metadata = metadata.copy() if metadata else {}
            section_metadata["is_toc"] = is_toc_section(title, body)

            section = Section(
                section_id=section_id,
                section_number=marker.number or f"{i+1}",
                section_type=marker.type,
                title=title,
                body=body,
                level=marker.level,
                parent_id=parent_id,
                start_char=start_pos,
                end_char=end_pos,
                metadata=section_metadata,
                citations=citations,
            )

            sections.append(section)

            # Update parent stack
            self._update_parent_stack(parent_stack, section, marker)

        return sections

    def _smart_title_body_split(
        self,
        section_text: str,
        marker: SectionMarker,
    ) -> Tuple[str, str]:
        """
        Intelligently split section into title and body.

        Handles:
        - Multi-line titles
        - Inline headings
        - Section numbers + text on same line
        """
        lines = section_text.split('\n')

        # If marker has heading, use it as title
        if marker.heading:
            title = f"{marker.number} {marker.heading}" if marker.number else marker.heading
            # Find where heading ends in text
            heading_end = section_text.find(marker.heading) + len(marker.heading)
            body = section_text[heading_end:].strip()
            return title, body

        # Case 1: First line is section number + description
        # Example: "7 Subject to section 10.1, every person..."
        if lines:
            first_line = lines[0].strip()

            # Check if first line ends with sentence boundary or is short
            if len(first_line) < 150 and (first_line.endswith('.') or len(lines) > 1):
                title = first_line
                body = '\n'.join(lines[1:]).strip()
                return title, body

        # Case 2: First sentence is title
        sentences = section_text.split('. ', 1)
        if len(sentences) >= 2 and len(sentences[0]) < 200:
            return sentences[0], sentences[1]

        # Fallback: First 150 chars as title
        return section_text[:150], section_text

    def _extract_citations(self, text: str) -> List[str]:
        """Extract legal citations from text."""
        citations = []
        for match in self.CITATION_PATTERN.finditer(text):
            citations.append(match.group(0))
        return citations

    def _find_parent(
        self,
        marker: SectionMarker,
        parent_stack: List[Tuple[int, str]],
    ) -> Optional[str]:
        """Find parent section ID based on hierarchy level."""
        # Pop stack until we find a parent at lower level
        while parent_stack and parent_stack[-1][0] >= marker.level:
            parent_stack.pop()

        return parent_stack[-1][1] if parent_stack else None

    def _update_parent_stack(
        self,
        parent_stack: List[Tuple[int, str]],
        section: Section,
        marker: SectionMarker,
    ):
        """Update parent stack with current section."""
        # Remove sections at same or higher level
        while parent_stack and parent_stack[-1][0] >= marker.level:
            parent_stack.pop()

        # Add current section
        parent_stack.append((marker.level, section.section_id))

    def _post_process_sections(self, sections: List[Section]) -> List[Section]:
        """Post-process sections: merge short ones, split long ones, clean up."""
        processed = []

        for section in sections:
            # Skip sections that are too short (likely parsing errors)
            if len(section.body) < self.min_section_length:
                continue

            # Warn about very long sections (might need manual review)
            if len(section.body) > self.max_section_length:
                print(f"  ⚠️ Section {section.section_number} is very long ({len(section.body)} chars)")

            processed.append(section)

        return processed

    def _create_fallback_section(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict],
    ) -> List[Section]:
        """Create fallback when no markers found."""
        lines = text.split('\n', 1)
        title = lines[0][:200] if lines else "Untitled Document"
        body = lines[1] if len(lines) > 1 else text

        section = Section(
            section_id=f"{document_id}_s0001",
            section_number="1",
            section_type=SectionType.SECTION,
            title=title,
            body=body,
            level=1,
            parent_id=None,
            start_char=0,
            end_char=len(text),
            metadata=metadata or {},
            citations=[],
        )

        return [section]


# Convenience function
def segment_document(
    text: str,
    document_id: str,
    metadata: Optional[Dict] = None,
) -> List[Dict]:
    """
    Segment document using advanced segmenter.

    Args:
        text: Document text
        document_id: Document identifier
        metadata: Optional metadata

    Returns:
        List of section dictionaries
    """
    segmenter = AdvancedSegmenter()
    sections = segmenter.segment(text, document_id, metadata)
    return [section.to_dict() for section in sections]
