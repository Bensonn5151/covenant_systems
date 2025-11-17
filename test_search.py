"""
Test Semantic Search

Test the FAISS index with natural language queries.

Usage:
    python3 test_search.py "Can a bank operate without a license?"
    python3 test_search.py "privacy data collection requirements"
"""

import sys
import argparse
from pathlib import Path

from ingestion.embed.embedder import Embedder
from storage.vector_db.faiss_manager import FAISSManager


def search(query: str, top_k: int = 5, threshold: float = 0.0):
    """
    Search for relevant sections using semantic similarity.

    Args:
        query: Natural language query
        top_k: Number of results to return
        threshold: Minimum similarity score
    """
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")

    # Check if index exists
    index_path = Path("storage/vector_db/covenant.index")
    if not index_path.exists():
        print("❌ Error: FAISS index not found.")
        print("Run: python3 generate_embeddings.py")
        sys.exit(1)

    # Load embedder
    print("Loading embedding model...")
    embedder = Embedder()

    # Generate query embedding
    print("Generating query embedding...")
    query_embedding = embedder.embed_text(query)

    # Load FAISS index
    print("Loading FAISS index...")
    manager = FAISSManager()
    manager.load(index_path)

    # Search
    print(f"Searching for top {top_k} results...\n")
    results = manager.search(
        query_embedding,
        top_k=top_k,
        score_threshold=threshold,
    )

    # Display results
    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} results:\n")

    for i, result in enumerate(results):
        score = result['score']
        section = result['section']

        print(f"[Result {i+1}] Score: {score:.4f}")
        print(f"Document: {section['metadata']['document_id']}")
        print(f"Section: {section['section_number']} - {section['title'][:60]}")
        print(f"Body preview:")
        print(f"  {section['body'][:200]}...")
        print()

    print("="*60)


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Search regulatory documents")
    parser.add_argument(
        "query",
        type=str,
        help="Search query (natural language)"
    )
    parser.add_argument(
        "-k", "--top-k",
        type=int,
        default=5,
        help="Number of results to return (default: 5)"
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=0.0,
        help="Minimum similarity score (default: 0.0)"
    )

    args = parser.parse_args()

    search(args.query, args.top_k, args.threshold)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: python3 test_search.py <query>")
        print("\nExamples:")
        print('  python3 test_search.py "Can a bank operate without a license?"')
        print('  python3 test_search.py "privacy data collection" -k 10')
        print('  python3 test_search.py "consent requirements" -t 0.7')
        sys.exit(1)

    main()