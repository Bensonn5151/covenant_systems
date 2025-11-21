"""
Quick test of AdvancedSegmenter on PCMLTFA

Run this to see if section boundaries are correctly detected.
"""

from pathlib import Path
from ingestion.segment.advanced_segmenter import AdvancedSegmenter

# Read bronze text
bronze_file = Path("storage/bronze/acts/s.c.2000,_c._17_-_proceeds_of_crime_(money_laundering)_and_terrorist_financing_act/raw_text.txt")

if not bronze_file.exists():
    print(f"❌ Bronze file not found: {bronze_file}")
    print("Run ingestion first or check path")
    exit(1)

text = bronze_file.read_text(encoding="utf-8")

print(f"✓ Loaded {len(text)} characters from {bronze_file.name}")
print(f"\nRunning AdvancedSegmenter...")

# Run segmenter
segmenter = AdvancedSegmenter()
sections = segmenter.segment(
    text=text,
    document_id="pcmltfa_test",
    metadata={"document_type": "Act"}
)

print(f"\n✓ Found {len(sections)} sections\n")

# Show first 10 sections
print("="*80)
print("FIRST 10 SECTIONS:")
print("="*80)

for i, section in enumerate(sections[:10]):
    print(f"\n[Section {i+1}]")
    print(f"  Number: {section.section_number}")
    print(f"  Type: {section.section_type.value}")
    print(f"  Level: {section.level}")
    print(f"  Title: {section.title[:100]}...")
    print(f"  Body length: {len(section.body)} chars")
    if section.citations:
        print(f"  Citations: {section.citations}")

# Look for sections 6.1 and 7 specifically
print("\n" + "="*80)
print("CHECKING SECTIONS 6.1 AND 7 (the problematic ones):")
print("="*80)

for section in sections:
    if section.section_number in ["6.1", "7", "7.1"]:
        print(f"\n[Section {section.section_number}]")
        print(f"  Type: {section.section_type.value}")
        print(f"  Title: {section.title}")
        print(f"  Body (first 300 chars):\n{section.body[:300]}")
        print(f"  Body (last 200 chars):\n...{section.body[-200:]}")

print("\n" + "="*80)
print("DONE")
print("="*80)