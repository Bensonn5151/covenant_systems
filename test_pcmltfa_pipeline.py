"""
Quick Test: Complete Pipeline on PCMLTFA

Tests the full pipeline with:
1. Adobe PDF extraction (left column only for bilingual)
2. Language filtering (English only)
3. Advanced segmentation

This verifies the Section 6.1 vs Section 7 bug is fixed.
"""

from pathlib import Path
from ingestion.pipeline import IngestionPipeline

# PCMLTFA path
pdf_path = "data/raw/acts/S.C.2000, c. 17 - Proceeds of Crime (Money Laundering) and Terrorist Financing Act.pdf"

if not Path(pdf_path).exists():
    print(f"❌ File not found: {pdf_path}")
    exit(1)

print("="*80)
print("TESTING COMPLETE PIPELINE ON PCMLTFA (BILINGUAL)")
print("="*80)
print(f"\nPDF: {pdf_path}")
print("Expected improvements:")
print("  1. Adobe PDF extraction with left column only")
print("  2. Language filtering removes French content")
print("  3. Advanced segmenter properly segments sections")
print("  4. Section 6.1 and 7 are separated (not merged)")
print("\nStarting pipeline...\n")

# Initialize pipeline
pipeline = IngestionPipeline(
    bronze_path="storage/bronze",
    silver_path="storage/silver",
)

# Process with bilingual flag
result = pipeline.process_document(
    pdf_path=pdf_path,
    document_type="Act",
    jurisdiction="Canada",
    is_bilingual=True,  # This triggers left-column extraction + language filtering
    manual_category="act",
)

print("\n" + "="*80)
print("PIPELINE TEST RESULTS")
print("="*80)
print(f"Document ID: {result['document_id']}")
print(f"Total sections: {result['sections_count']}")
print(f"Total characters: {result['total_chars']:,}")
print(f"Needs OCR: {result['needs_ocr']}")
print(f"\nBronze file: {result['bronze']['bronze_file']}")
print(f"Silver file: {result['silver']['silver_file']}")

# Load and check specific sections
import json
silver_file = Path(result['silver']['silver_file'])
sections = json.loads(silver_file.read_text(encoding='utf-8'))

print(f"\n{'='*80}")
print("CHECKING CRITICAL SECTIONS (6.1 and 7)")
print("="*80)

for section in sections:
    if section['section_number'] in ['6.1', '7', '7.1']:
        print(f"\n[Section {section['section_number']}]")
        print(f"  Type: {section['section_type']}")
        print(f"  Title: {section['title'][:100]}")
        print(f"  Body length: {len(section['body'])} chars")
        print(f"  Body preview (first 200 chars):")
        print(f"    {section['body'][:200].replace(chr(10), ' ')}")

print(f"\n{'='*80}")
print("TEST COMPLETE")
print("="*80)

# Check for common issues
section_numbers = [s['section_number'] for s in sections]
if '6.1' in section_numbers and '7' in section_numbers:
    print("✅ Sections 6.1 and 7 are both present (not merged)")
else:
    print("❌ WARNING: Section 6.1 or 7 is missing!")

# Check for French content leakage
french_indicators = ['Loi', 'règlement', 'déclaration', 'financier']
french_count = 0
for section in sections[:50]:  # Check first 50 sections
    body_lower = section['body'].lower()
    for indicator in french_indicators:
        if indicator.lower() in body_lower:
            french_count += 1
            break

if french_count > 5:
    print(f"⚠️  WARNING: {french_count} sections may contain French content")
else:
    print(f"✅ Language filtering effective ({french_count} potential French sections)")

print("\n" + "="*80)