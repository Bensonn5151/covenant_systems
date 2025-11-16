"""
Bilingual PDF Extractor

Handles dual-column bilingual PDFs (English/French) common in Canadian regulations.
Extracts only the English (left column) text.

Uses:
- pdfplumber: Column detection and layout analysis
- PyMuPDF (fitz): Precise region-based text extraction
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pdfplumber
import fitz  # PyMuPDF


class BilingualExtractor:
    """Extract English text from dual-column English/French PDFs."""

    def __init__(
        self,
        column_split_ratio: float = 0.5,
        detect_columns: bool = True,
    ):
        """
        Initialize bilingual extractor.

        Args:
            column_split_ratio: Where to split page (0.5 = middle)
            detect_columns: Auto-detect column boundaries
        """
        self.column_split_ratio = column_split_ratio
        self.detect_columns = detect_columns

    def extract(self, pdf_path: str) -> Dict:
        """
        Extract English (left column) text from bilingual PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with extracted text and metadata
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Try to detect column layout first
        if self.detect_columns:
            column_boundary = self._detect_column_boundary(pdf_path)
        else:
            column_boundary = None

        # Extract text from left column
        text, page_count = self._extract_left_column(pdf_path, column_boundary)

        metadata = {
            "extraction_method": "bilingual_column",
            "column_boundary": column_boundary,
            "page_count": page_count,
            "char_count": len(text),
        }

        return {
            "text": text,
            "metadata": metadata,
        }

    def _detect_column_boundary(self, pdf_path: Path) -> Optional[float]:
        """
        Detect column boundary using pdfplumber.

        Args:
            pdf_path: Path to PDF

        Returns:
            X-coordinate of column boundary (in points)
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Sample first few pages to detect layout
                sample_pages = min(3, len(pdf.pages))
                boundaries = []

                for page_num in range(sample_pages):
                    page = pdf.pages[page_num]
                    page_width = page.width

                    # Get text words with positions
                    words = page.extract_words()

                    if not words:
                        continue

                    # Cluster words by X position
                    x_positions = [w["x0"] for w in words]

                    # Find the gap (middle empty space)
                    # Sort X positions and look for large gaps
                    x_sorted = sorted(set(x_positions))

                    max_gap = 0
                    boundary_x = page_width / 2

                    for i in range(len(x_sorted) - 1):
                        gap = x_sorted[i + 1] - x_sorted[i]
                        if gap > max_gap and x_sorted[i] > page_width * 0.3:
                            max_gap = gap
                            boundary_x = (x_sorted[i] + x_sorted[i + 1]) / 2

                    boundaries.append(boundary_x)

                # Average boundary across sample pages
                if boundaries:
                    avg_boundary = sum(boundaries) / len(boundaries)
                    return avg_boundary

        except Exception as e:
            print(f"Warning: Column detection failed: {e}")

        return None

    def _extract_left_column(
        self,
        pdf_path: Path,
        column_boundary: Optional[float] = None,
    ) -> Tuple[str, int]:
        """
        Extract text from left column using PyMuPDF.

        Args:
            pdf_path: Path to PDF
            column_boundary: X-coordinate to split columns

        Returns:
            Tuple of (text, page_count)
        """
        text_parts = []

        try:
            # Open with PyMuPDF for precise extraction
            doc = fitz.open(pdf_path)
            page_count = len(doc)

            for page_num in range(page_count):
                page = doc[page_num]
                page_rect = page.rect

                # Determine column boundary
                if column_boundary:
                    split_x = column_boundary
                else:
                    # Use midpoint
                    split_x = page_rect.width * self.column_split_ratio

                # Define left column region
                left_column_rect = fitz.Rect(
                    0,  # x0 (left edge)
                    0,  # y0 (top edge)
                    split_x,  # x1 (column boundary)
                    page_rect.height,  # y1 (bottom edge)
                )

                # Extract text from left column only
                page_text = page.get_text("text", clip=left_column_rect)
                text_parts.append(page_text)

            doc.close()

            text = "\n\n".join(text_parts)
            return text, page_count

        except Exception as e:
            raise RuntimeError(f"Column extraction failed: {e}")

    def extract_both_columns(self, pdf_path: str) -> Dict:
        """
        Extract both English and French columns separately.

        Args:
            pdf_path: Path to PDF

        Returns:
            Dictionary with both language texts
        """
        pdf_path = Path(pdf_path)

        # Detect boundary
        column_boundary = self._detect_column_boundary(pdf_path)

        if not column_boundary:
            raise RuntimeError("Could not detect column boundary")

        # Extract both columns
        doc = fitz.open(pdf_path)
        english_parts = []
        french_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_rect = page.rect

            # Left column (English)
            left_rect = fitz.Rect(0, 0, column_boundary, page_rect.height)
            english_text = page.get_text("text", clip=left_rect)
            english_parts.append(english_text)

            # Right column (French)
            right_rect = fitz.Rect(column_boundary, 0, page_rect.width, page_rect.height)
            french_text = page.get_text("text", clip=right_rect)
            french_parts.append(french_text)

        doc.close()

        return {
            "english": "\n\n".join(english_parts),
            "french": "\n\n".join(french_parts),
            "metadata": {
                "column_boundary": column_boundary,
                "page_count": len(doc),
            },
        }


# Convenience function
def extract_english_only(pdf_path: str) -> str:
    """
    Extract only English text from bilingual PDF.

    Args:
        pdf_path: Path to PDF

    Returns:
        English text
    """
    extractor = BilingualExtractor()
    result = extractor.extract(pdf_path)
    return result["text"]