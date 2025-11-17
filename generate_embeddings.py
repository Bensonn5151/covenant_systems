"""
Generate Embeddings for All Documents

Processes all Silver layer documents and generates:
1. Embeddings for each section
2. Gold layer storage
3. FAISS index for fast search

Usage:
    python3 generate_embeddings.py
    python3 generate_embeddings.py --document bank_act_canada
"""

import argparse
from pathlib import Path
import json
import sys

from ingestion.embed.embedder import Embedder
from storage.vector_db.faiss_manager import FAISSManager


def process_document(doc_path: Path, embedder: Embedder):
    """
    Process a single document: Silver → Gold.

    Args:
        doc_path: Path to Silver document directory
        embedder: Embedder instance
    """
    document_id = doc_path.name
    print(f"\n{'='*60}")
    print(f"Processing: {document_id}")
    print(f"{'='*60}")

    # Load Silver sections
    sections_file = doc_path / "sections.json"
    if not sections_file.exists():
        print(f"⚠️  Sections file not found: {sections_file}")
        return None

    with open(sections_file, "r", encoding="utf-8") as f:
        sections = json.load(f)

    print(f"Loaded {len(sections)} sections")

    # Generate embeddings
    enriched_sections, embeddings = embedder.embed_sections(sections)

    # Create Gold layer directory
    gold_path = Path("storage/gold") / document_id
    gold_path.mkdir(parents=True, exist_ok=True)

    # Save embeddings
    embeddings_file = gold_path / "embeddings.npy"
    embedder.save_embeddings(
        embeddings,
        embeddings_file,
        enriched_sections,
    )

    print(f"✓ Created Gold layer: {gold_path}")

    return {
        "document_id": document_id,
        "embeddings": embeddings,
        "sections": enriched_sections,
        "gold_path": gold_path,
    }


def build_global_index(gold_documents: list):
    """
    Build a global FAISS index across all documents.

    Uses incremental addition to avoid memory issues with large vstacks.

    Args:
        gold_documents: List of processed document results
    """
    print(f"\n{'='*60}")
    print("Building Global FAISS Index")
    print(f"{'='*60}")

    # Get dimension from first document
    if not gold_documents:
        print("❌ No documents to index")
        return None

    import numpy as np

    first_embedding = gold_documents[0]["embeddings"]
    dimension = first_embedding.shape[1]

    total_sections = sum(len(doc["sections"]) for doc in gold_documents)
    print(f"Total sections: {total_sections}")
    print(f"Embedding dimension: {dimension}")

    # Create FAISS index FIRST
    manager = FAISSManager(
        dimension=dimension,
        index_type="Flat",
        metric="cosine",
    )

    print("Adding embeddings incrementally (per document)...")

    # Add embeddings document by document (avoid large vstack)
    for i, doc in enumerate(gold_documents, 1):
        doc_embeddings = doc["embeddings"]
        doc_sections = doc["sections"]
        doc_id = doc["document_id"]

        # Ensure proper format for this batch
        if doc_embeddings.dtype != np.float32:
            doc_embeddings = doc_embeddings.astype(np.float32)

        if not doc_embeddings.flags['C_CONTIGUOUS']:
            doc_embeddings = np.ascontiguousarray(doc_embeddings)

        print(f"  [{i}/{len(gold_documents)}] Adding {len(doc_sections)} sections from {doc_id}...")
        manager.add_embeddings(doc_embeddings, doc_sections)

    print(f"✓ Added all {manager.section_count} sections to index")

    # Save index
    index_path = Path("storage/vector_db/covenant.index")
    manager.save(index_path)

    print(f"✓ Global index saved: {index_path}")

    return manager


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Generate embeddings for documents")
    parser.add_argument(
        "--document",
        type=str,
        help="Process specific document (e.g., bank_act_canada)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding model name",
    )

    args = parser.parse_args()

    # Check if Silver layer exists
    silver_path = Path("storage/silver")
    if not silver_path.exists():
        print("❌ Error: Silver layer not found. Process documents first.")
        sys.exit(1)

    # Get documents to process
    if args.document:
        documents = [silver_path / args.document]
        if not documents[0].exists():
            print(f"❌ Error: Document not found: {args.document}")
            sys.exit(1)
    else:
        # Process all documents
        documents = [d for d in silver_path.iterdir() if d.is_dir()]

    if not documents:
        print("❌ Error: No documents found in Silver layer")
        sys.exit(1)

    print(f"\nFound {len(documents)} document(s) to process")

    # Initialize embedder
    print("\n" + "="*60)
    print("Initializing Embedding Model")
    print("="*60)

    embedder = Embedder(model_name=args.model)

    # Process each document
    results = []
    for doc_path in documents:
        result = process_document(doc_path, embedder)
        if result:
            results.append(result)

    # Build global index
    if results:
        build_global_index(results)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Documents processed: {len(results)}")
    print(f"Total sections: {sum(len(r['sections']) for r in results)}")
    print(f"\nGold layer location: storage/gold/")
    print(f"FAISS index: storage/vector_db/covenant.index")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()