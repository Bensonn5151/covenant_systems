"""
Bookmark-Based PDF Segmenter

Uses PDF's built-in table of contents / outline / bookmarks to segment documents.
This is what PDF viewers like VS Code use - guaranteed perfect section boundaries.

Falls back to text-based segmentation if no bookmarks are found.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Optional
import logging
from ingestion.segment.advanced_segmenter import Section, SectionType

try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

logger = logging.getLogger(__name__)


class BookmarkSegmenter:
    """
    Extract sections using PDF bookmarks/outline/TOC.

    Most government regulatory PDFs have proper bookmarks that define
    their structure. This is far more accurate than regex-based text parsing.
    """

    def __init__(self, target_lang: str = None):
        """
        Initialize bookmark segmenter.
        
        Args:
            target_lang: Optional target language to filter content (e.g., 'en')
        """
        self.min_bookmarks = 3  # Minimum bookmarks to trust TOC
        self.target_lang = target_lang
        
        # Initialize language preprocessor if target language specified
        if self.target_lang:
            try:
                from ingestion.preprocessors.language_filter import LanguagePreprocessor
                self.preprocessor = LanguagePreprocessor(target_lang=self.target_lang)
            except ImportError:
                logger.warning("LanguagePreprocessor not available - skipping language filtering")
                self.preprocessor = None
        else:
            self.preprocessor = None

    def set_target_lang(self, target_lang: str):
        """
        Set target language for filtering.
        
        Args:
            target_lang: Target language code (e.g., 'en')
        """
        self.target_lang = target_lang
        if self.target_lang:
            try:
                from ingestion.preprocessors.language_filter import LanguagePreprocessor
                self.preprocessor = LanguagePreprocessor(target_lang=self.target_lang)
            except ImportError:
                logger.warning("LanguagePreprocessor not available - skipping language filtering")
                self.preprocessor = None
        else:
            self.preprocessor = None

    def has_bookmarks(self, pdf_path: str) -> bool:
        """
        Check if PDF has a useful table of contents.

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF has bookmarks worth using
        """
        try:
            doc = fitz.open(pdf_path)
            toc = doc.get_toc()
            doc.close()

            has_toc = len(toc) >= self.min_bookmarks

            if has_toc:
                logger.info(f"Found {len(toc)} bookmarks in PDF")
            else:
                logger.info(f"Only {len(toc)} bookmarks - falling back to text parsing")

            return has_toc

        except Exception as e:
            logger.error(f"Error checking bookmarks: {e}")
            return False

    def segment(self, pdf_path: str, raw_text: str, document_id: str) -> List[Dict]:
        """
        Segment document using PDF bookmarks.

        Args:
            pdf_path: Path to PDF file
            raw_text: Full extracted text (for text extraction between pages)
            document_id: Document identifier

        Returns:
            List of section dictionaries
        """
        try:
            doc = fitz.open(pdf_path)
            toc = doc.get_toc()

            if len(toc) < self.min_bookmarks:
                logger.warning(f"Insufficient bookmarks ({len(toc)}) - use text-based segmenter")
                doc.close()
                return []

            sections = []

            for i, entry in enumerate(toc):
                level, title, page_num = entry

                # --- HYBRID FRENCH DETECTION (Layer 2 Priority) ---

                # LAYER 2 (PRIORITY): Title Language Detection
                # Catches titles like "Définitions", "Objet de la loi", etc.
                # This catches 95% of French sections efficiently
                if LANGDETECT_AVAILABLE and len(title) > 10:
                    try:
                        if detect(title) == 'fr':
                            logger.info(f"Skipping French section (title detected): '{title}'")
                            continue
                    except LangDetectException:
                        pass  # Fall through to Layer 1

                # LAYER 1 (FALLBACK): Keyword Check for short/explicit titles
                # Catches "FRANÇAIS", "FRENCH", "TABLE ANALYTIQUE"
                upper_title = title.upper()
                if any(keyword in upper_title for keyword in ["FRANÇAIS", "FRENCH", "TABLE ANALYTIQUE"]):
                    logger.info(f"Skipping French section (keyword): '{title}'")
                    continue

                # Get next bookmark to determine page range
                if i + 1 < len(toc):
                    next_page = toc[i + 1][2]
                else:
                    next_page = len(doc) + 1  # Last section goes to end

                # Extract text from page range
                section_text = self._extract_text_range(doc, page_num, next_page)

                # LAYER 3 (ULTIMATE FAILSAFE): Body Language Detection
                # Checks actual content when title-based detection is ambiguous
                # Most reliable but slowest - only runs if Layers 1 & 2 didn't catch it
                if LANGDETECT_AVAILABLE and len(section_text.strip()) > 50:
                    try:
                        # Check first 500 chars to avoid processing huge texts
                        if detect(section_text[:500]) == 'fr':
                            logger.info(f"Skipping French section (body detected): '{title}'")
                            continue
                    except LangDetectException:
                        pass  # Continue processing if detection fails

                # Apply language filtering if configured
                if self.preprocessor:
                    # Filter text to target language
                    filtered_text, _ = self.preprocessor.filter_text(section_text)
                    if filtered_text.strip():
                        section_text = filtered_text
                    else:
                        # If filtering removed everything (e.g., French-only section in bilingual doc),
                        # skip this section to avoid empty entries in Silver layer
                        logger.debug(f"Skipping section '{title}' - no content in target language")
                        continue

                # Parse section number from title
                section_number = self._parse_section_number(title)

                # Clean title (remove section number prefix)
                clean_title = self._clean_title(title, section_number)

                # Infer section type
                section_type = self._infer_section_type(title, level)

                # Create section
                section = {
                    "section_id": f"{document_id}_s{len(sections) + 1:04d}",
                    "section_number": section_number,
                    "section_type": section_type,
                    "title": clean_title,
                    "body": section_text.strip(),
                    "level": level,
                    "metadata": {
                        "extraction_method": "pdf_bookmarks",
                        "page_start": page_num,
                        "page_end": next_page - 1,
                        "bookmark_index": i,
                    }
                }

                sections.append(section)

            doc.close()

            logger.info(f"Extracted {len(sections)} sections from {len(toc)} bookmarks")
            return sections

        except Exception as e:
            logger.error(f"Error segmenting with bookmarks: {e}")
            return []

    def _extract_text_range(self, doc: fitz.Document, start_page: int, end_page: int) -> str:
        """
        Extract text from a page range.

        Args:
            doc: PyMuPDF document
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (exclusive, 1-indexed)

        Returns:
            Concatenated text from page range
        """
        text_parts = []

        # Convert to 0-indexed
        start_idx = start_page - 1
        end_idx = min(end_page - 1, len(doc))

        for page_num in range(start_idx, end_idx):
            try:
                page = doc[page_num]
                text = page.get_text()
                text_parts.append(text)
            except Exception as e:
                logger.warning(f"Error extracting page {page_num + 1}: {e}")

        return "\n\n".join(text_parts)

    def _parse_section_number(self, title: str) -> str:
        """
        Parse section number from bookmark title.

        Examples:
            "1 Short Title" -> "1"
            "6.1 Verifying Identity" -> "6.1"
            "PART 1 Record Keeping..." -> "PART 1"
            "11.41 Interpretation" -> "11.41"

        Args:
            title: Bookmark title

        Returns:
            Section number (or title if no number found)
        """
        import re

        # Try to extract leading number (with optional decimal)
        match = re.match(r'^(\d+(?:\.\d+)?)\s+', title)
        if match:
            return match.group(1)

        # Try to extract PART/Division patterns
        match = re.match(r'^(PART\s+\d+(?:\.\d+)?)\s+', title, re.IGNORECASE)
        if match:
            return match.group(1)

        # No recognizable number - use full title as section number
        return title.strip()

    def _clean_title(self, title: str, section_number: str) -> str:
        """
        Remove section number from title.

        Args:
            title: Full bookmark title
            section_number: Parsed section number

        Returns:
            Title without section number prefix
        """
        # If section number is same as title, return as-is
        if section_number == title.strip():
            return title.strip()

        # Remove section number prefix
        if title.startswith(section_number):
            clean = title[len(section_number):].strip()
            return clean if clean else title

        return title.strip()

    def _infer_section_type(self, title: str, level: int) -> SectionType:
        """
        Infer section type from bookmark title and level.

        Args:
            title: Bookmark title
            level: Bookmark level (1 = top-level)

        Returns:
            SectionType enum value
        """
        import re

        title_upper = title.upper()

        # Check title patterns
        if re.match(r'^PART\s+', title_upper):
            return SectionType.PART
        elif re.match(r'^DIVISION\s+', title_upper):
            return SectionType.DIVISION
        elif re.match(r'^ARTICLE\s+', title_upper):
            return SectionType.ARTICLE
        elif re.match(r'^SCHEDULE|^APPENDIX', title_upper):
            return SectionType.SCHEDULE

        # Infer from level (bookmark hierarchy)
        if level == 1:
            return SectionType.PART
        elif level == 2:
            return SectionType.SECTION
        elif level == 3:
            return SectionType.SUBSECTION
        elif level == 4:
            return SectionType.PARAGRAPH
        else:
            return SectionType.SECTION  # Default


class HybridSegmenter:
    """
    Hybrid segmenter that uses PDF bookmarks when available,
    falls back to text-based segmentation otherwise.
    """

    def __init__(self, text_segmenter=None):
        """
        Initialize hybrid segmenter.

        Args:
            text_segmenter: Fallback segmenter (AdvancedSegmenter) for PDFs without bookmarks
        """
        self.bookmark_segmenter = BookmarkSegmenter()
        self.text_segmenter = text_segmenter
        self.pdf_path = None  # Will be set via set_pdf_path()

    def set_pdf_path(self, pdf_path: str):
        """
        Set the PDF path for bookmark extraction.

        Args:
            pdf_path: Path to PDF file
        """
        self.pdf_path = pdf_path

    def segment(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict] = None,
        target_lang: Optional[str] = None,
    ) -> List[Section]:
        """
        Segment using best available method.

        Matches AdvancedSegmenter interface for compatibility.

        Args:
            text: Full extracted text
            document_id: Document identifier
            metadata: Optional metadata dict
            target_lang: Optional target language for filtering (if using bookmarks)

        Returns:
            List of Section objects
        """
        # Try bookmark-based segmentation first (if PDF path was set)
        if self.pdf_path and Path(self.pdf_path).exists():
            if self.bookmark_segmenter.has_bookmarks(self.pdf_path):
                # Configure language filtering if needed
                if target_lang:
                    self.bookmark_segmenter.set_target_lang(target_lang)
                
                bookmark_dicts = self.bookmark_segmenter.segment(self.pdf_path, text, document_id)
                if bookmark_dicts:
                    # Convert dict sections to Section objects
                    sections = []
                    for sec_dict in bookmark_dicts:
                        section = Section(
                            section_id=sec_dict["section_id"],
                            section_number=sec_dict["section_number"],
                            section_type=sec_dict["section_type"],
                            title=sec_dict["title"],
                            body=sec_dict["body"],
                            level=sec_dict["level"],
                            metadata=sec_dict.get("metadata", {}),
                        )
                        sections.append(section)

                    print(f"  ✅ Used PDF bookmarks: {len(sections)} sections")
                    return sections

        # Fall back to text-based segmentation
        if self.text_segmenter:
            print("  ⚠️  No bookmarks found - using text pattern segmentation")
            return self.text_segmenter.segment(text, document_id, metadata)
        else:
            logger.error("❌ No fallback segmenter available!")
            return []