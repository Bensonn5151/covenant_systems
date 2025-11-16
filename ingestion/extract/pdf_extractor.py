"""
PDF Text Extraction Module

Extracts text from PDF documents with automatic detection of scanned vs digital PDFs.
Routes scanned PDFs to OCR pipeline when needed.

Follows Bronze Layer principles: minimal transformation, preservation of original content.
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

import PyPDF2
import pdfplumber


class PDFExtractor:
    """Extract text from PDF documents."""

    def __init__(
        self,
        ocr_threshold_chars: int = 50,
        ocr_threshold_filesize_kb: int = 100,
        max_pages: int = 1000,
    ):
        """
        Initialize PDF extractor.

        Args:
            ocr_threshold_chars: If extracted text < this, trigger OCR
            ocr_threshold_filesize_kb: Minimum file size to consider for OCR
            max_pages: Maximum number of pages to process
        """
        self.ocr_threshold_chars = ocr_threshold_chars
        self.ocr_threshold_filesize_kb = ocr_threshold_filesize_kb
        self.max_pages = max_pages

    def extract(
        self, pdf_path: str, document_id: Optional[str] = None
    ) -> Dict:
        """
        Extract text and metadata from PDF.

        Args:
            pdf_path: Path to PDF file
            document_id: Optional document identifier

        Returns:
            Dictionary containing:
                - text: Extracted text
                - metadata: File metadata
                - needs_ocr: Boolean indicating if OCR is needed
                - extraction_method: Method used for extraction
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Generate document ID if not provided
        if not document_id:
            document_id = self._generate_document_id(pdf_path)

        # Extract text using pdfplumber (better for complex PDFs)
        text, page_count = self._extract_with_pdfplumber(pdf_path)

        # Check if PDF needs OCR
        needs_ocr = self._needs_ocr(pdf_path, text)

        # Generate file hash for versioning
        file_hash = self._compute_hash(pdf_path)

        # Collect metadata
        metadata = {
            "document_id": document_id,
            "source_file": str(pdf_path),
            "file_size_bytes": pdf_path.stat().st_size,
            "file_hash": file_hash,
            "page_count": page_count,
            "char_count": len(text),
            "extraction_date": datetime.utcnow().isoformat(),
            "extraction_method": "pdfplumber",
        }

        return {
            "text": text,
            "metadata": metadata,
            "needs_ocr": needs_ocr,
            "extraction_method": "pdfplumber",
        }

    def _extract_with_pdfplumber(self, pdf_path: Path) -> Tuple[str, int]:
        """
        Extract text using pdfplumber.

        Args:
            pdf_path: Path to PDF

        Returns:
            Tuple of (extracted_text, page_count)
        """
        text_parts = []
        page_count = 0

        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)

                # Limit pages if needed
                pages_to_process = min(page_count, self.max_pages)

                for i, page in enumerate(pdf.pages[:pages_to_process]):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            text = "\n\n".join(text_parts)
            return text, page_count

        except Exception as e:
            # Fallback to PyPDF2 if pdfplumber fails
            return self._extract_with_pypdf2(pdf_path)

    def _extract_with_pypdf2(self, pdf_path: Path) -> Tuple[str, int]:
        """
        Fallback extraction using PyPDF2.

        Args:
            pdf_path: Path to PDF

        Returns:
            Tuple of (extracted_text, page_count)
        """
        text_parts = []

        try:
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                page_count = len(reader.pages)

                pages_to_process = min(page_count, self.max_pages)

                for i in range(pages_to_process):
                    page = reader.pages[i]
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            text = "\n\n".join(text_parts)
            return text, page_count

        except Exception as e:
            raise RuntimeError(f"PDF extraction failed: {e}")

    def _needs_ocr(self, pdf_path: Path, extracted_text: str) -> bool:
        """
        Determine if PDF needs OCR processing.

        OCR is needed when:
        1. Extracted text is below character threshold
        2. File size suggests it should have more content

        Args:
            pdf_path: Path to PDF
            extracted_text: Text extracted from PDF

        Returns:
            Boolean indicating if OCR is needed
        """
        char_count = len(extracted_text.strip())
        file_size_kb = pdf_path.stat().st_size / 1024

        # If very little text extracted but file is large, likely scanned
        if (
            char_count < self.ocr_threshold_chars
            and file_size_kb > self.ocr_threshold_filesize_kb
        ):
            return True

        return False

    def _compute_hash(self, pdf_path: Path) -> str:
        """
        Compute SHA256 hash of PDF file.

        Args:
            pdf_path: Path to PDF

        Returns:
            Hexadecimal hash string
        """
        sha256_hash = hashlib.sha256()

        with open(pdf_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def _generate_document_id(self, pdf_path: Path) -> str:
        """
        Generate document ID from filename.

        Args:
            pdf_path: Path to PDF

        Returns:
            Document ID
        """
        # Use filename without extension as base ID
        # Convert to lowercase, replace spaces/special chars with underscores
        base_name = pdf_path.stem
        doc_id = base_name.lower().replace(" ", "_").replace("-", "_")

        # Remove multiple underscores
        while "__" in doc_id:
            doc_id = doc_id.replace("__", "_")

        return doc_id


# Convenience function
def extract_pdf(pdf_path: str, document_id: Optional[str] = None) -> Dict:
    """
    Extract text from PDF file.

    Args:
        pdf_path: Path to PDF file
        document_id: Optional document identifier

    Returns:
        Extraction result dictionary
    """
    extractor = PDFExtractor()
    return extractor.extract(pdf_path, document_id)