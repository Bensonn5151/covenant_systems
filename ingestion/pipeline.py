"""
Ingestion Pipeline Orchestrator

Coordinates the full Bronze → Silver transformation:
1. Extract text from PDF (Bronze)
2. Apply OCR if needed (Bronze)
3. Segment into sections (Silver)
4. Save to appropriate storage layers

This is the main entry point for document ingestion.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from ingestion.extract.pdf_extractor import PDFExtractor
from ingestion.extract.bilingual_extractor import BilingualExtractor
from ingestion.ocr.ocr_processor import OCRProcessor
from ingestion.segment.section_segmenter import SectionSegmenter
from ingestion.classify.document_classifier import DocumentClassifier


class IngestionPipeline:
    """Orchestrates document ingestion from raw PDF to structured sections."""

    def __init__(
        self,
        bronze_path: str = "storage/bronze",
        silver_path: str = "storage/silver",
        taxonomy_path: str = "configs/taxonomy.yaml",
    ):
        """
        Initialize ingestion pipeline.

        Args:
            bronze_path: Path to bronze storage (raw)
            silver_path: Path to silver storage (structured)
            taxonomy_path: Path to taxonomy configuration
        """
        self.bronze_path = Path(bronze_path)
        self.silver_path = Path(silver_path)

        # Initialize components
        self.extractor = PDFExtractor()
        self.bilingual_extractor = BilingualExtractor()
        self.ocr_processor = OCRProcessor()
        self.segmenter = SectionSegmenter()
        self.classifier = DocumentClassifier(taxonomy_path=taxonomy_path)

        # Ensure storage paths exist
        self.bronze_path.mkdir(parents=True, exist_ok=True)
        self.silver_path.mkdir(parents=True, exist_ok=True)

    def process_document(
        self,
        pdf_path: str,
        document_id: Optional[str] = None,
        document_type: Optional[str] = None,
        jurisdiction: str = "unknown",
        is_bilingual: bool = False,
        manual_category: Optional[str] = None,
        regulator: Optional[str] = None,
        parent_act: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> Dict:
        """
        Process a document through the full pipeline.

        Bronze: Extract text (with OCR if needed)
        Silver: Segment into structured sections
        Classification: Auto-detect category or use manual override

        Args:
            pdf_path: Path to PDF file
            document_id: Optional document ID
            document_type: Type of document (Act, Regulation, etc.)
            jurisdiction: Jurisdiction (Canada, US, etc.)
            is_bilingual: Whether PDF has dual columns (EN/FR)
            manual_category: Manual category override (act, regulation, guidance, policy)
            regulator: Regulator code (for guidance documents)
            parent_act: Parent act (for regulations)
            company_id: Company ID (for policies)

        Returns:
            Dictionary with processing results
        """
        print(f"\n{'='*60}")
        print(f"PROCESSING: {Path(pdf_path).name}")
        print(f"{'='*60}\n")

        # ============================================
        # STEP 1: EXTRACT (BRONZE)
        # ============================================
        if is_bilingual:
            print("STEP 1: Extracting text from BILINGUAL PDF (English only)...")
            bilingual_result = self.bilingual_extractor.extract(pdf_path)

            # Generate document ID if not provided
            if not document_id:
                document_id = Path(pdf_path).stem.lower().replace(" ", "_")

            extracted_text = bilingual_result["text"]
            needs_ocr = False  # Bilingual extraction doesn't support OCR detection yet

            extraction_metadata = {
                "document_id": document_id,
                **bilingual_result["metadata"],
            }

            print(f"  ✓ Extracted {len(extracted_text)} characters (English column)")
            print(f"  ✓ Pages: {extraction_metadata['page_count']}")
            print(f"  ✓ Column boundary: {extraction_metadata.get('column_boundary', 'auto-detected')}")
        else:
            print("STEP 1: Extracting text from PDF...")
            extraction_result = self.extractor.extract(pdf_path, document_id)

            document_id = extraction_result["metadata"]["document_id"]
            extracted_text = extraction_result["text"]
            needs_ocr = extraction_result["needs_ocr"]
            extraction_metadata = extraction_result["metadata"]

            print(f"  ✓ Extracted {len(extracted_text)} characters")
            print(f"  ✓ Pages: {extraction_metadata['page_count']}")
            print(f"  ✓ Needs OCR: {needs_ocr}")

        # ============================================
        # CLASSIFICATION: Manual category (required for MVP)
        # ============================================
        if not manual_category:
            raise ValueError("manual_category is required. Please specify: act, regulation, guidance, or policy")

        category = manual_category
        print(f"\n✓ Document Category: {category}")

        # Print category-specific info
        if regulator:
            print(f"  ✓ Regulator: {regulator}")
        if parent_act:
            print(f"  ✓ Parent Act: {parent_act}")
        if company_id:
            print(f"  ✓ Company ID: {company_id}")

        # Save to Bronze (raw extraction) with taxonomy-based path
        bronze_result = self._save_to_bronze(
            document_id=document_id,
            text=extracted_text,
            metadata=extraction_metadata,
            category=category,
            regulator=regulator,
            company_id=company_id,
        )
        print(f"  ✓ Saved to Bronze: {bronze_result['bronze_file']}")

        # ============================================
        # STEP 2: OCR (if needed)
        # ============================================
        final_text = extracted_text

        if needs_ocr:
            print("\nSTEP 2: Applying OCR (scanned PDF detected)...")
            ocr_result = self.ocr_processor.process_pdf(pdf_path, document_id)

            if ocr_result.get("error"):
                print(f"  ⚠ OCR failed: {ocr_result['error']}")
            else:
                final_text = ocr_result["text"]
                avg_confidence = ocr_result["metadata"].get("avg_confidence", 0)
                print(f"  ✓ OCR completed: {len(final_text)} characters")
                print(f"  ✓ Average confidence: {avg_confidence:.2f}%")

                # Save OCR result to Bronze (with same taxonomy params)
                ocr_bronze_result = self._save_to_bronze(
                    document_id=f"{document_id}_ocr",
                    text=final_text,
                    metadata=ocr_result["metadata"],
                    category=category,
                    regulator=regulator,
                    company_id=company_id,
                )
                print(f"  ✓ Saved OCR to Bronze: {ocr_bronze_result['bronze_file']}")
        else:
            print("\nSTEP 2: OCR not needed (digital PDF)")

        # ============================================
        # STEP 3: SEGMENTATION (SILVER)
        # ============================================
        print("\nSTEP 3: Segmenting into structured sections...")

        # Prepare metadata for sections
        section_metadata = {
            "document_id": document_id,
            "document_type": document_type or "unknown",
            "jurisdiction": jurisdiction,
            "source_file": str(pdf_path),
            "processed_date": datetime.utcnow().isoformat(),
            "category": category,
        }

        # Add category-specific metadata
        if regulator:
            section_metadata["regulator"] = regulator
        if parent_act:
            section_metadata["parent_act"] = parent_act
        if company_id:
            section_metadata["company_id"] = company_id

        sections = self.segmenter.segment(
            text=final_text,
            document_id=document_id,
            metadata=section_metadata,
        )

        print(f"  ✓ Identified {len(sections)} sections")

        # Convert sections to dictionaries
        section_dicts = [section.to_dict() for section in sections]

        # Save to Silver (structured sections) with taxonomy-based path
        silver_result = self._save_to_silver(
            document_id=document_id,
            sections=section_dicts,
            metadata=section_metadata,
            category=category,
            regulator=regulator,
            company_id=company_id,
        )
        print(f"  ✓ Saved to Silver: {silver_result['silver_file']}")

        # ============================================
        # SUMMARY
        # ============================================
        print(f"\n{'='*60}")
        print("PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Document ID: {document_id}")
        print(f"Bronze Layer: {bronze_result['bronze_file']}")
        print(f"Silver Layer: {silver_result['silver_file']}")
        print(f"Sections: {len(sections)}")
        print(f"{'='*60}\n")

        return {
            "document_id": document_id,
            "bronze": bronze_result,
            "silver": silver_result,
            "sections_count": len(sections),
            "needs_ocr": needs_ocr,
            "total_chars": len(final_text),
            "category": category,
            "regulator": regulator,
            "parent_act": parent_act,
            "company_id": company_id,
        }

    def _save_to_bronze(
        self,
        document_id: str,
        text: str,
        metadata: Dict,
        category: Optional[str] = None,
        regulator: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> Dict:
        """
        Save to Bronze layer (raw text + metadata) with taxonomy-based path.

        Args:
            document_id: Document ID
            text: Raw extracted text
            metadata: Extraction metadata
            category: Document category (act, regulation, guidance, policy)
            regulator: Regulator code (for guidance documents)
            company_id: Company ID (for policies)

        Returns:
            Dict with file paths
        """
        # Determine taxonomy-based path
        if category:
            # Use defaults for None values to prevent path errors
            storage_path = self.classifier.get_storage_path(
                category=category,
                document_id=document_id,
                layer="bronze",
                regulator=regulator or "unknown",
                company_id=company_id or "default",
            )
            doc_dir = Path(storage_path)
        else:
            # Fallback to flat structure if no category
            doc_dir = self.bronze_path / document_id

        doc_dir.mkdir(parents=True, exist_ok=True)

        # Save raw text
        text_file = doc_dir / "raw_text.txt"
        text_file.write_text(text, encoding="utf-8")

        # Save metadata
        metadata_file = doc_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return {
            "bronze_file": str(text_file),
            "metadata_file": str(metadata_file),
        }

    def _save_to_silver(
        self,
        document_id: str,
        sections: list,
        metadata: Dict,
        category: Optional[str] = None,
        regulator: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> Dict:
        """
        Save to Silver layer (structured sections) with taxonomy-based path.

        Args:
            document_id: Document ID
            sections: List of section dictionaries
            metadata: Document metadata
            category: Document category (act, regulation, guidance, policy)
            regulator: Regulator code (for guidance documents)
            company_id: Company ID (for policies)

        Returns:
            Dict with file paths
        """
        # Determine taxonomy-based path
        if category:
            # Use defaults for None values to prevent path errors
            storage_path = self.classifier.get_storage_path(
                category=category,
                document_id=document_id,
                layer="silver",
                regulator=regulator or "unknown",
                company_id=company_id or "default",
            )
            doc_dir = Path(storage_path)
        else:
            # Fallback to flat structure if no category
            doc_dir = self.silver_path / document_id

        doc_dir.mkdir(parents=True, exist_ok=True)

        # Save sections
        sections_file = doc_dir / "sections.json"
        with open(sections_file, "w", encoding="utf-8") as f:
            json.dump(sections, f, indent=2, ensure_ascii=False)

        # Save metadata
        metadata_file = doc_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return {
            "silver_file": str(sections_file),
            "metadata_file": str(metadata_file),
        }


# Convenience function
def ingest_document(
    pdf_path: str,
    document_id: Optional[str] = None,
    document_type: Optional[str] = None,
    jurisdiction: str = "unknown",
) -> Dict:
    """
    Ingest a document through the pipeline.

    Args:
        pdf_path: Path to PDF file
        document_id: Optional document ID
        document_type: Document type
        jurisdiction: Jurisdiction

    Returns:
        Processing results
    """
    pipeline = IngestionPipeline()
    return pipeline.process_document(
        pdf_path=pdf_path,
        document_id=document_id,
        document_type=document_type,
        jurisdiction=jurisdiction,
    )
