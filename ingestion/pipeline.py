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
import re
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from ingestion.extract.pdf_extractor import PDFExtractor
from ingestion.extract.adobe_pdf_extractor import AdobePDFExtractor
from ingestion.ocr.ocr_processor import OCRProcessor
from ingestion.preprocessors.language_filter import LanguagePreprocessor
from ingestion.segment.advanced_segmenter import AdvancedSegmenter
from ingestion.segment.bookmark_segmenter import HybridSegmenter
from ingestion.classify.document_classifier import DocumentClassifier


class IngestionPipeline:
    """Orchestrates document ingestion from raw PDF to structured sections."""

    def __init__(
        self,
        bronze_path: str = "storage/bronze",
        silver_path: str = "storage/silver",
        taxonomy_path: str = "configs/taxonomy.yaml",
        adobe_credentials_path: Optional[str] = None,
    ):
        """
        Initialize ingestion pipeline.

        Args:
            bronze_path: Path to bronze storage (raw)
            silver_path: Path to silver storage (structured)
            taxonomy_path: Path to taxonomy configuration
            adobe_credentials_path: Path to Adobe credentials (auto-detected if not provided)
        """
        self.bronze_path = Path(bronze_path)
        self.silver_path = Path(silver_path)

        # Initialize Adobe PDF Services as primary extractor
        try:
            self.extractor = AdobePDFExtractor(credentials_path=adobe_credentials_path)
            self.extraction_method = "Adobe PDF Services"
            print("✓ Adobe PDF Services initialized (95-99% accuracy)")
        except Exception as e:
            print(f"⚠ Adobe PDF Services unavailable: {e}")
            print("  Falling back to PyPDF2 (70-80% accuracy)")
            self.extractor = PDFExtractor()
            self.extraction_method = "PyPDF2"

        self.ocr_processor = OCRProcessor()

        # Use hybrid segmenter: PDF bookmarks first, text patterns as fallback
        text_segmenter = AdvancedSegmenter()
        self.segmenter = HybridSegmenter(text_segmenter=text_segmenter)

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
            is_bilingual: Whether PDF has dual columns (EN/FR) - extracts left column only
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
        # Check if input is already a text file (re-processing Bronze)
        is_text_file = str(pdf_path).lower().endswith('.txt')

        if is_text_file:
            print("STEP 1: Reading existing Bronze text (skipping extraction)...")
            try:
                raw_text = Path(pdf_path).read_text(encoding='utf-8')
                print(f"  ✓ Read {len(raw_text)} characters from {pdf_path}")

                # Clean Adobe artifacts from Bronze text
                print("  → Cleaning Adobe extraction artifacts...")
                extracted_text = self._clean_bronze_text(raw_text)
                print(f"  ✓ Cleaned text: {len(extracted_text)} characters")

                # Try to load existing metadata
                metadata_path = Path(pdf_path).parent / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        extraction_metadata = json.load(f)
                    print(f"  ✓ Loaded existing metadata from {metadata_path}")
                else:
                    extraction_metadata = {
                        "document_id": document_id or Path(pdf_path).parent.name,
                        "extraction_method": "existing_bronze",
                        "page_count": 0,
                    }
                    print("  ⚠️  No metadata file found, using default")

                # Ensure document_id is set
                if not document_id:
                    document_id = extraction_metadata.get("document_id", Path(pdf_path).parent.name)

                needs_ocr = False

                # Construct bronze_result for consistency
                bronze_result = {
                    "bronze_file": str(pdf_path),
                    "metadata_file": str(metadata_path) if metadata_path.exists() else None
                }

            except Exception as e:
                raise ValueError(f"Failed to read text file: {e}")

        else:
            # Normal PDF extraction flow
            print("STEP 1: Extracting text from PDF...")
            # NOTE: For bilingual documents, we use spatial filtering (left column only)
            # This is cleaner than extracting full page and filtering later

            try:
                # Pass bilingual flag to Adobe extractor if applicable
                if isinstance(self.extractor, AdobePDFExtractor):
                    extraction_result = self.extractor.extract(
                        pdf_path,
                        document_id,
                        extract_left_column_only=is_bilingual
                    )
                else:
                    extraction_result = self.extractor.extract(pdf_path, document_id)
            except Exception as e:
                # Adobe PDF Services failed - fall back to PyPDF2
                print(f"  ⚠ Adobe PDF Services failed: {e}")
                print("  → Falling back to PyPDF2...")

                fallback_extractor = PDFExtractor()
                extraction_result = fallback_extractor.extract(pdf_path, document_id)

                # Mark as fallback in metadata
                extraction_result["metadata"]["extraction_method"] = "PyPDF2 (Fallback)"
                extraction_result["metadata"]["fallback_reason"] = str(e)

            document_id = extraction_result["metadata"]["document_id"]
            extracted_text = extraction_result["text"]
            needs_ocr = extraction_result["needs_ocr"]
            extraction_metadata = extraction_result["metadata"]

            print(f"  ✓ Extracted {len(extracted_text)} characters")
            print(f"  ✓ Pages: {extraction_metadata['page_count']}")
            print(f"  ✓ Extraction method: {extraction_metadata.get('extraction_method', self.extraction_method)}")
            print(f"  ✓ Extraction mode: {extraction_metadata.get('extraction_mode', 'full_page')}")
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

        # Save to Bronze (unless we already read from Bronze)
        if not is_text_file:
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
        # STEP 2.5: LANGUAGE FILTERING (for bilingual docs)
        # ============================================
        # NOTE: We filter here at the document level, so no need to filter again during segmentation
        text_already_filtered = False

        # Auto-detect bilingual for Canadian documents if not explicitly set
        if not is_bilingual and jurisdiction.lower() in ("canada", "federal"):
            if self._detect_bilingual(final_text):
                is_bilingual = True
                print("\nSTEP 2.5: Auto-detected bilingual document (Canadian jurisdiction)")

        if is_bilingual:
            print("\nSTEP 2.5: Filtering to English (bilingual document detected)...")
            lang_preprocessor = LanguagePreprocessor(target_lang='en')

            filtered_text, lang_metadata = lang_preprocessor.filter_text(
                final_text,
                chunk_by='sentence'
            )

            # Print stats
            stats = lang_metadata['language_filter']['stats']
            print(f"  ✓ Filtered {stats['total_blocks']} blocks")
            print(f"  ✓ Kept {stats['kept_blocks']} English blocks")
            print(f"  ✓ Dropped {stats['filtered_blocks']} non-English blocks")

            if stats['languages_detected']:
                print(f"  ✓ Languages detected: {', '.join(stats['languages_detected'].keys())}")

            # Use filtered text for segmentation
            final_text = filtered_text
            text_already_filtered = True  # Don't filter again in segmenter

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

        # Set PDF path for bookmark extraction (only if processing a PDF)
        # For text files, skip bookmarks and use text-based segmentation directly
        if not is_text_file and hasattr(self.segmenter, 'set_pdf_path'):
            self.segmenter.set_pdf_path(pdf_path)
        elif is_text_file and hasattr(self.segmenter, 'set_pdf_path'):
            # Clear PDF path to force text-based segmentation for Bronze files
            self.segmenter.set_pdf_path(None)

        # Don't pass target_lang if we already filtered in STEP 2.5
        # This prevents redundant filtering during segmentation
        sections = self.segmenter.segment(
            text=final_text,
            document_id=document_id,
            metadata=section_metadata,
            target_lang=None,  # Text already filtered in STEP 2.5 if needed
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

    @staticmethod
    def _detect_bilingual(text: str) -> bool:
        """
        Detect if text is bilingual (English/French) Canadian government document.

        Uses two signals:
        1. French function word ratio in the text
        2. Presence of known bilingual header patterns (e.g. parallel EN/FR titles)

        Args:
            text: Document text to analyze

        Returns:
            True if document appears bilingual
        """
        sample = text[:20000]
        words = sample.split()
        if len(words) < 50:
            return False

        # Signal 1: French function words ratio (threshold 0.08 — these docs are ~10% French words)
        french_indicators = re.findall(
            r'\b(la|le|les|des|une|est|sont|aux|dans|sur|par|pour|cette|avec|qui|que|du|en|ou|'
            r'Loi|loi|article|alinéa|paragraphe|règlement|partie|chapitre|dispositions|'
            r'renseignements|personnels|protection|commissaire)\b',
            sample,
        )
        ratio = len(french_indicators) / len(words)

        # Signal 2: Bilingual header markers typical of Justice Canada publications
        bilingual_markers = [
            r'À jour au',
            r'Dernière modification le',
            r'Codification',
            r'L\.C\.\s+\d{4}',
            r'ch\.\s+\d+',
            r'Publié par le ministre',
            r'PARTIE\s+\d+',
            r'ANNEXE\s+\d+',
        ]
        marker_count = sum(
            1 for p in bilingual_markers if re.search(p, sample)
        )

        return ratio > 0.07 or marker_count >= 3

    def _clean_bronze_text(self, text: str) -> str:
        """
        Clean Adobe extraction artifacts from Bronze text.

        Removes:
        - (<>) markers from Adobe PDF Services
        - Extra whitespace and formatting artifacts

        Args:
            text: Raw Bronze text with Adobe artifacts

        Returns:
            Cleaned text ready for section parsing
        """
        import re

        # Remove (<>) markers from Adobe
        cleaned = re.sub(r'\(<>\)', '', text)

        # Clean up excessive whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # Max 2 consecutive newlines
        cleaned = re.sub(r' +', ' ', cleaned)  # Multiple spaces to single

        return cleaned.strip()


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
