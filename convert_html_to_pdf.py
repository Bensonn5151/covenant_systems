#!/usr/bin/env python3
"""
HTML to PDF Batch Converter for FINTRAC Guidance Documents

Converts all HTML files in data/raw/guidance/fintrac/html/ to PDFs
and saves them to data/raw/guidance/fintrac/

Usage:
    python3 convert_html_to_pdf.py
    python3 convert_html_to_pdf.py --check-only  # Just list what would be converted
"""

import os
import sys
from pathlib import Path
import argparse

def check_dependencies():
    """Check if required libraries are installed."""
    try:
        import weasyprint
        return True, "weasyprint"
    except ImportError:
        pass

    try:
        import pdfkit
        return True, "pdfkit"
    except ImportError:
        pass

    return False, None


def convert_with_weasyprint(html_path: Path, pdf_path: Path) -> bool:
    """Convert HTML to PDF using weasyprint."""
    try:
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def convert_with_pdfkit(html_path: Path, pdf_path: Path) -> bool:
    """Convert HTML to PDF using pdfkit."""
    try:
        import pdfkit
        pdfkit.from_file(str(html_path), str(pdf_path))
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert FINTRAC HTML guidance to PDF")
    parser.add_argument("--check-only", action="store_true", help="Only list files, don't convert")
    parser.add_argument("--force", action="store_true", help="Overwrite existing PDFs")
    args = parser.parse_args()

    # Check dependencies
    has_converter, converter_name = check_dependencies()
    if not has_converter:
        print("❌ No PDF conversion library found!")
        print("\nPlease install one of the following:")
        print("  1. pip install weasyprint  (Recommended)")
        print("  2. pip install pdfkit")
        print("\nFor weasyprint, you may also need:")
        print("  macOS: brew install pango")
        print("  Ubuntu: sudo apt-get install libpango-1.0-0")
        sys.exit(1)

    print(f"✓ Using {converter_name} for PDF conversion\n")

    # Set paths
    html_dir = Path("data/raw/guidance/fintrac/html")
    pdf_dir = Path("data/raw/guidance/fintrac")

    # Check if directories exist
    if not html_dir.exists():
        print(f"❌ HTML directory not found: {html_dir}")
        sys.exit(1)

    pdf_dir.mkdir(parents=True, exist_ok=True)

    # Get all HTML files
    html_files = sorted(html_dir.glob("*.html"))

    if not html_files:
        print(f"❌ No HTML files found in {html_dir}")
        sys.exit(1)

    print("="*60)
    print("HTML TO PDF CONVERTER")
    print("="*60)
    print(f"Source: {html_dir}")
    print(f"Target: {pdf_dir}")
    print(f"Found {len(html_files)} HTML files")
    print("="*60)
    print()

    if args.check_only:
        print("CHECK MODE - No files will be converted\n")
        for i, html_file in enumerate(html_files, 1):
            pdf_file = pdf_dir / html_file.with_suffix('.pdf').name
            exists = "✓ EXISTS" if pdf_file.exists() else "  "
            print(f"[{i}/{len(html_files)}] {exists} {html_file.name}")
        print(f"\nTotal: {len(html_files)} files")
        return

    # Convert files
    converted = 0
    skipped = 0
    failed = 0

    for i, html_file in enumerate(html_files, 1):
        pdf_file = pdf_dir / html_file.with_suffix('.pdf').name

        print(f"[{i}/{len(html_files)}] {html_file.name}")

        # Check if PDF already exists
        if pdf_file.exists() and not args.force:
            print(f"  ⏩ Skipping (already exists)")
            skipped += 1
            continue

        # Convert
        print(f"  → Converting to PDF...")

        if converter_name == "weasyprint":
            success = convert_with_weasyprint(html_file, pdf_file)
        elif converter_name == "pdfkit":
            success = convert_with_pdfkit(html_file, pdf_file)
        else:
            success = False

        if success:
            size_kb = pdf_file.stat().st_size / 1024
            print(f"  ✓ Saved: {pdf_file.name} ({size_kb:.1f} KB)")
            converted += 1
        else:
            failed += 1

    # Summary
    print()
    print("="*60)
    print("CONVERSION SUMMARY")
    print("="*60)
    print(f"Converted: {converted}")
    print(f"Skipped:   {skipped}")
    print(f"Failed:    {failed}")
    print(f"Total:     {len(html_files)}")
    print("="*60)

    if converted > 0:
        print("\nNext step:")
        print("  python3 batch_ingest.py data/raw/milestone_1_fintrac_pcmltfa.yaml --continue-on-error")


if __name__ == "__main__":
    main()