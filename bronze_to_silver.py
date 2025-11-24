"""
Bronze → Silver Re-processing Script

Processes existing Bronze text files directly into Silver layer.
Skips PDF extraction, uses clean Bronze text as source of truth.
"""

from pathlib import Path
from ingestion.pipeline import IngestionPipeline
import json


def process_bronze_file(
    bronze_text_path: str,
    manual_category: str,
    document_type: str = None,
    jurisdiction: str = "Canada",
    parent_act: str = None,
    regulator: str = None,
    company_id: str = None,
):
    """
    Process a single Bronze text file → Silver.

    Args:
        bronze_text_path: Path to Bronze raw_text.txt
        manual_category: act, regulation, guidance, or policy
        document_type: Act, Regulation, Guidance, Policy
        jurisdiction: Canada, US, UK, etc.
        parent_act: For regulations (e.g., "PCMLTFA")
        regulator: For guidance (e.g., "FINTRAC")
        company_id: For policies
    """
    pipeline = IngestionPipeline()

    print(f"\n{'='*80}")
    print(f"BRONZE → SILVER: {Path(bronze_text_path).parent.name}")
    print(f"{'='*80}")

    try:
        result = pipeline.process_document(
            pdf_path=bronze_text_path,
            document_type=document_type,
            jurisdiction=jurisdiction,
            manual_category=manual_category,
            parent_act=parent_act,
            regulator=regulator,
            company_id=company_id,
        )

        print(f"\n✅ SUCCESS")
        print(f"   Silver: {result['silver']['silver_file']}")
        print(f"   Sections: {result['sections_count']}")
        print(f"   Characters: {result['total_chars']:,}")

        return result

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_all_bronze_acts():
    """Process all Bronze acts → Silver."""
    bronze_acts = Path("storage/bronze/acts")

    if not bronze_acts.exists():
        print("No Bronze acts found")
        return []

    results = []
    for act_dir in bronze_acts.iterdir():
        if not act_dir.is_dir():
            continue

        raw_text = act_dir / "raw_text.txt"
        if not raw_text.exists():
            print(f"⚠️  Skipping {act_dir.name} - no raw_text.txt")
            continue

        result = process_bronze_file(
            bronze_text_path=str(raw_text),
            manual_category="act",
            document_type="Act",
            jurisdiction="Canada",
        )
        results.append(result)

    return results


def process_all_bronze_regulations():
    """Process all Bronze regulations → Silver."""
    bronze_regs = Path("storage/bronze/regulations")

    if not bronze_regs.exists():
        print("No Bronze regulations found")
        return []

    results = []
    for reg_dir in bronze_regs.iterdir():
        if not reg_dir.is_dir():
            continue

        raw_text = reg_dir / "raw_text.txt"
        if not raw_text.exists():
            print(f"⚠️  Skipping {reg_dir.name} - no raw_text.txt")
            continue

        # Try to infer parent act from name
        parent_act = None
        if "pcmltfa" in reg_dir.name.lower() or "proceeds_of_crime" in reg_dir.name.lower():
            parent_act = "PCMLTFA"

        result = process_bronze_file(
            bronze_text_path=str(raw_text),
            manual_category="regulation",
            document_type="Regulation",
            jurisdiction="Canada",
            parent_act=parent_act,
        )
        results.append(result)

    return results


def process_all_bronze_guidance():
    """Process all Bronze guidance documents → Silver."""
    bronze_guidance = Path("storage/bronze/guidance")

    if not bronze_guidance.exists():
        print("No Bronze guidance found")
        return []

    results = []
    for guid_dir in bronze_guidance.iterdir():
        if not guid_dir.is_dir():
            continue

        raw_text = guid_dir / "raw_text.txt"
        if not raw_text.exists():
            print(f"⚠️  Skipping {guid_dir.name} - no raw_text.txt")
            continue

        # Try to infer regulator from directory structure
        regulator = guid_dir.parent.name if guid_dir.parent.name != "guidance" else "unknown"

        result = process_bronze_file(
            bronze_text_path=str(raw_text),
            manual_category="guidance",
            document_type="Guidance",
            jurisdiction="Canada",
            regulator=regulator,
        )
        results.append(result)

    return results


def main():
    """Main entry point - process all Bronze files."""
    print("="*80)
    print("BRONZE → SILVER BATCH PROCESSOR")
    print("="*80)

    all_results = []

    # Process Acts
    print("\n\n📜 PROCESSING ACTS...")
    act_results = process_all_bronze_acts()
    all_results.extend([r for r in act_results if r])

    # Process Regulations
    print("\n\n📋 PROCESSING REGULATIONS...")
    reg_results = process_all_bronze_regulations()
    all_results.extend([r for r in reg_results if r])

    # Process Guidance
    print("\n\n📘 PROCESSING GUIDANCE...")
    guid_results = process_all_bronze_guidance()
    all_results.extend([r for r in guid_results if r])

    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total processed: {len(all_results)}")
    print(f"Acts: {len([r for r in act_results if r])}")
    print(f"Regulations: {len([r for r in reg_results if r])}")
    print(f"Guidance: {len([r for r in guid_results if r])}")
    print(f"\nTotal sections: {sum(r['sections_count'] for r in all_results)}")
    print("="*80)


if __name__ == "__main__":
    # Option 1: Process all Bronze files
    main()

    # Option 2: Process single file (uncomment to use)
    # process_bronze_file(
    #     bronze_text_path="storage/bronze/regulations/sor-2002-184_-_proceeds_of_crime_(money_laundering)_and_terrorist_financing_regulations/raw_text.txt",
    #     manual_category="regulation",
    #     document_type="Regulation",
    #     jurisdiction="Canada",
    #     parent_act="PCMLTFA",
    # )