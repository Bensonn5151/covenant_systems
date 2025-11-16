"""
OCR Processing Module

Performs Optical Character Recognition on scanned PDFs using Tesseract.
Only invoked when PDF extraction returns insufficient text.

Follows Bronze Layer principles: preserve OCR output verbatim, log confidence.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
except ImportError as e:
    print(f"Warning: OCR dependencies not installed: {e}")


class OCRProcessor:
    """Process scanned documents using Tesseract OCR."""

    def __init__(
        self,
        tesseract_cmd: Optional[str] = None,
        dpi: int = 300,
        language: str = "eng",
    ):
        """
        Initialize OCR processor.

        Args:
            tesseract_cmd: Path to tesseract executable
            dpi: DPI for image conversion
            language: Language code for OCR (eng, fra, etc.)
        """
        self.dpi = dpi
        self.language = language

        # Set tesseract command path if provided
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def process_pdf(self, pdf_path: str, document_id: str) -> Dict:
        """
        Process scanned PDF with OCR.

        Args:
            pdf_path: Path to PDF file
            document_id: Document identifier

        Returns:
            Dictionary containing:
                - text: OCR extracted text
                - metadata: OCR metadata
                - page_data: Per-page OCR results
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            # Convert PDF to images
            images = self._pdf_to_images(pdf_path)

            # Process each page
            page_data = []
            text_parts = []

            for i, image in enumerate(images):
                page_result = self._process_page(image, i + 1)
                page_data.append(page_result)
                text_parts.append(page_result["text"])

            # Combine all text
            full_text = "\n\n".join(text_parts)

            # Calculate average confidence
            confidences = [p["confidence"] for p in page_data if p["confidence"] is not None]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            metadata = {
                "document_id": document_id,
                "source_file": str(pdf_path),
                "ocr_engine": "tesseract",
                "ocr_language": self.language,
                "dpi": self.dpi,
                "page_count": len(images),
                "char_count": len(full_text),
                "avg_confidence": avg_confidence,
                "ocr_date": datetime.utcnow().isoformat(),
            }

            return {
                "text": full_text,
                "metadata": metadata,
                "page_data": page_data,
            }

        except Exception as e:
            return {
                "text": "",
                "metadata": {
                    "document_id": document_id,
                    "error": str(e),
                    "ocr_date": datetime.utcnow().isoformat(),
                },
                "page_data": [],
                "error": f"OCR processing failed: {e}",
            }

    def _pdf_to_images(self, pdf_path: Path) -> List[Image.Image]:
        """
        Convert PDF pages to images.

        Args:
            pdf_path: Path to PDF

        Returns:
            List of PIL Image objects
        """
        try:
            images = convert_from_path(
                str(pdf_path),
                dpi=self.dpi,
                fmt="png",
            )
            return images

        except Exception as e:
            raise RuntimeError(f"PDF to image conversion failed: {e}")

    def _process_page(self, image: Image.Image, page_number: int) -> Dict:
        """
        Process single page image with OCR.

        Args:
            image: PIL Image object
            page_number: Page number (1-indexed)

        Returns:
            Dictionary with page OCR results
        """
        try:
            # Extract text with confidence data
            ocr_data = pytesseract.image_to_data(
                image,
                lang=self.language,
                output_type=pytesseract.Output.DICT,
            )

            # Extract just the text
            text = pytesseract.image_to_string(image, lang=self.language)

            # Calculate average confidence for this page
            confidences = [
                int(conf) for conf in ocr_data["conf"] if conf != "-1"
            ]
            avg_confidence = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )

            return {
                "page_number": page_number,
                "text": text.strip(),
                "confidence": avg_confidence,
                "word_count": len(text.split()),
            }

        except Exception as e:
            return {
                "page_number": page_number,
                "text": "",
                "confidence": None,
                "error": str(e),
            }

    def process_image(self, image_path: str) -> Dict:
        """
        Process single image file with OCR.

        Args:
            image_path: Path to image file

        Returns:
            OCR result dictionary
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            image = Image.open(image_path)
            result = self._process_page(image, 1)

            metadata = {
                "source_file": str(image_path),
                "ocr_engine": "tesseract",
                "ocr_language": self.language,
                "ocr_date": datetime.utcnow().isoformat(),
            }

            return {
                "text": result["text"],
                "metadata": metadata,
                "confidence": result["confidence"],
            }

        except Exception as e:
            return {
                "text": "",
                "metadata": {
                    "source_file": str(image_path),
                    "error": str(e),
                },
                "error": f"Image OCR failed: {e}",
            }


# Convenience function
def ocr_pdf(pdf_path: str, document_id: str) -> Dict:
    """
    Process scanned PDF with OCR.

    Args:
        pdf_path: Path to PDF file
        document_id: Document identifier

    Returns:
        OCR result dictionary
    """
    processor = OCRProcessor()
    return processor.process_pdf(pdf_path, document_id)
