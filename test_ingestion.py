"""
Universal PDF Ingestion Test Script

Processes any PDF through the ingestion pipeline using Adobe PDF Services.
Supports bilingual PDFs (English/French dual columns).

Usage:
    python3 test_ingestion.py <pdf_path> --category <category> [--bilingual] [--regulator <regulator>] [--parent-act <act>] [--company-id <id>]

Examples:
    python3 test_ingestion.py data/raw/privacy_act.pdf --category act --bilingual
    python3 test_ingestion.py data/raw/osfi_b13.pdf --category guidance --regulator OSFI
    python3 test_ingestion.py data/raw/policy.pdf --category policy --company-id acme_corp
"""

import sys
import json
import argparse
from pathlib import Path
from ingestion.pipeline import IngestionPipeline


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
    parser = argparse.ArgumentParser(description="Process PDF through ingestion pipeline")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--category", required=True, choices=["act", "regulation", "guidance", "policy"],
                        help="Document category (required)")
    parser.add_argument("--bilingual", action="store_true",
                        help="PDF has dual columns (English/French) - extract left column only using Adobe")
    parser.add_argument("--regulator", choices=["OSFI", "FINTRAC", "OPC", "FCAC"],
                        help="Regulator (required for guidance documents)")
    parser.add_argument("--parent-act", choices=["Bank Act", "PCMLTFA", "PIPEDA"],
                        help="Parent act (required for regulations)")
    parser.add_argument("--company-id", help="Company ID (required for policies)")

    args = parser.parse_args()

    # Validate category-specific requirements
    if args.category == "guidance" and not args.regulator:
        parser.error("--regulator is required when category is 'guidance'")
    if args.category == "regulation" and not args.parent_act:
        parser.error("--parent-act is required when category is 'regulation'")
    if args.category == "policy" and not args.company_id:
        parser.error("--company-id is required when category is 'policy'")

    # Check if file exists
    if not Path(args.pdf_path).exists():
        print(f"Error: File not found: {args.pdf_path}")
        sys.exit(1)

    # Infer metadata
    doc_type, jurisdiction = infer_metadata(args.pdf_path)
    print(f"Inferred document type: {doc_type}")
    print(f"Inferred jurisdiction: {jurisdiction}")
    print(f"Category: {args.category}")

    # Initialize pipeline
    pipeline = IngestionPipeline(
        bronze_path="storage/bronze",
        silver_path="storage/silver",
    )

    # Process the document
    print("\n" + "=" * 60)
    print(f"PROCESSING: {Path(args.pdf_path).name}")
    print("=" * 60)

    result = pipeline.process_document(
        pdf_path=args.pdf_path,
        document_type=doc_type,
        jurisdiction=jurisdiction,
        is_bilingual=args.bilingual,
        manual_category=args.category,
        regulator=args.regulator,
        parent_act=args.parent_act,
        company_id=args.company_id,
    )

    # Display results
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Document ID: {result['document_id']}")
    print(f"Total characters: {result['total_chars']:,}")
    print(f"Sections extracted: {result['sections_count']}")
    print(f"Needed OCR: {result['needs_ocr']}")
    print(f"Bilingual extraction: {args.bilingual}")
    print(f"Extraction method: Adobe PDF Services")
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