"""
Universal PDF Ingestion Test Script

Processes any PDF through the ingestion pipeline.
Auto-detects bilingual PDFs and extracts accordingly.

Usage:
    python3 test_ingestion.py <pdf_path> [--bilingual]

Examples:
    python3 test_ingestion.py data/raw/bank_act.pdf --bilingual
    python3 test_ingestion.py data/raw/sec_regulation.pdf
    python3 test_ingestion.py storage/bronze/bank_act_canada.pdf --bilingual
"""

import sys
import json
from pathlib import Path
from ingestion.pipeline import IngestionPipeline


def detect_bilingual_pdf(pdf_path: str) -> bool:
    """
    Auto-detect if PDF is likely bilingual by checking text distribution.

    Simple heuristic: if PDF has significant text in both left and right halves,
    it's likely bilingual.
    """
    try:
        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            # Sample first page
            if len(pdf.pages) == 0:
                return False

            page = pdf.pages[0]
            words = page.extract_words()

            if not words:
                return False

            page_width = page.width
            midpoint = page_width / 2

            # Count words in left vs right half
            left_words = sum(1 for w in words if w["x0"] < midpoint)
            right_words = sum(1 for w in words if w["x0"] >= midpoint)

            # If both halves have significant text, likely bilingual
            total_words = left_words + right_words
            if total_words == 0:
                return False

            left_ratio = left_words / total_words
            right_ratio = right_words / total_words

            # Both sides have >30% of words -> bilingual
            if left_ratio > 0.3 and right_ratio > 0.3:
                return True

    except Exception as e:
        print(f"Warning: Could not auto-detect bilingual layout: {e}")

    return False


def infer_metadata(pdf_path: str):
    """
    Infer document metadata from filename.
    """
    filename = Path(pdf_path).stem.lower()

    # Detect document type
    doc_type = "unknown"
    if "act" in filename or "_act_" in filename:
        doc_type = "Act"
    elif "regulation" in filename or "reg" in filename:
        doc_type = "Regulation"
    elif "guideline" in filename or "guidance" in filename:
        doc_type = "Guideline"
    elif "policy" in filename or "policies" in filename:
        doc_type = "Policy"
    elif "standard" in filename:
        doc_type = "Standard"

    # Detect jurisdiction
    jurisdiction = "unknown"
    if "canada" in filename or "canadian" in filename or "osfi" in filename or "pcmltfa" in filename:
        jurisdiction = "Canada"
    elif "us" in filename or "usa" in filename or "sec" in filename or "glba" in filename or "nydfs" in filename:
        jurisdiction = "United States"
    elif "uk" in filename or "fca" in filename:
        jurisdiction = "United Kingdom"
    elif "eu" in filename or "gdpr" in filename or "eba" in filename:
        jurisdiction = "European Union"

    return doc_type, jurisdiction


def main():
    """Main test function."""

    # Parse arguments
    if len(sys.argv) < 2:
        print("Error: No PDF path provided")
        print("\nUsage:")
        print("  python3 test_ingestion.py <pdf_path> [--bilingual]")
        print("\nExamples:")
        print("  python3 test_ingestion.py data/raw/bank_act.pdf --bilingual")
        print("  python3 test_ingestion.py storage/bronze/bank_act_canada.pdf --bilingual")
        sys.exit(1)

    pdf_path = sys.argv[1]
    force_bilingual = "--bilingual" in sys.argv

    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    # Auto-detect bilingual if not forced
    if force_bilingual:
        is_bilingual = True
        print("Using bilingual extraction (forced)")
    else:
        print("Auto-detecting PDF layout...")
        is_bilingual = detect_bilingual_pdf(pdf_path)
        if is_bilingual:
            print("✓ Bilingual PDF detected - will extract English only")
        else:
            print("✓ Regular PDF detected - will extract all text")

    # Infer metadata
    doc_type, jurisdiction = infer_metadata(pdf_path)
    print(f"Inferred document type: {doc_type}")
    print(f"Inferred jurisdiction: {jurisdiction}")

    # Initialize pipeline
    pipeline = IngestionPipeline(
        bronze_path="storage/bronze",
        silver_path="storage/silver",
    )

    # Process the document
    print("\n" + "=" * 60)
    print(f"PROCESSING: {Path(pdf_path).name}")
    print("=" * 60)

    result = pipeline.process_document(
        pdf_path=pdf_path,
        document_type=doc_type,
        jurisdiction=jurisdiction,
        is_bilingual=is_bilingual,
    )

    # Display results
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Document ID: {result['document_id']}")
    print(f"Total characters: {result['total_chars']:,}")
    print(f"Sections extracted: {result['sections_count']}")
    print(f"Needed OCR: {result['needs_ocr']}")
    print(f"Bilingual extraction: {is_bilingual}")
    print(f"\nBronze location: {result['bronze']['bronze_file']}")
    print(f"Silver location: {result['silver']['silver_file']}")
    print("=" * 60)

    # Show sample sections
    print("\nFIRST 3 SECTIONS:")
    print("-" * 60)

    sections_file = Path(result['silver']['silver_file'])
    if sections_file.exists():
        with open(sections_file, "r", encoding="utf-8") as f:
            sections = json.load(f)

        for i, section in enumerate(sections[:3]):
            print(f"\n[Section {i+1}]")
            print(f"  ID: {section['section_id']}")
            print(f"  Number: {section['section_number']}")
            print(f"  Title: {section['title'][:80]}...")
            print(f"  Body: {section['body'][:150]}...")
            print(f"  Level: {section['level']}")

        if len(sections) > 3:
            print(f"\n... and {len(sections) - 3} more sections")

    print("\n" + "=" * 60)
    print("✓ Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()