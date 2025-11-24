"""
Semantic Search Engine

Provides semantic search capabilities over the Gold layer embeddings using FAISS.
Integrates with Streamlit dashboard and can be extended with LLM synthesis.
"""

from pathlib import Path
from typing import List, Dict, Optional
import json

from storage.vector_db.faiss_manager import FAISSManager
from ingestion.embed.embedder import Embedder


class SemanticSearchEngine:
    """Semantic search engine for regulatory documents."""

    def __init__(
        self,
        index_path: str = "storage/vector_db/covenant.index",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """
        Initialize search engine.

        Args:
            index_path: Path to FAISS index
            model_name: Embedding model name
        """
        self.index_path = Path(index_path)
        self.model_name = model_name

        # Check if index exists
        if not self.index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {index_path}\n"
                "Run: python3 generate_embeddings.py"
            )

        # Load FAISS index
        print(f"Loading FAISS index from {index_path}...")
        self.manager = FAISSManager()
        self.manager.load(str(self.index_path))
        print(f"✓ Loaded {self.manager.section_count} sections")

        # Load embedder
        print(f"Loading embedding model: {model_name}...")
        self.embedder = Embedder(model_name=model_name)
        print("✓ Search engine ready")

    def search(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.0,
        category_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search for relevant sections.

        Args:
            query: Search query
            top_k: Number of results to return
            score_threshold: Minimum similarity score (0-1)
            category_filter: Filter by category (act, regulation, guidance)

        Returns:
            List of results with scores and metadata
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)

        # Search FAISS index
        results = self.manager.search(
            query_embedding,
            top_k=top_k * 3 if category_filter else top_k,  # Get more for filtering
            score_threshold=score_threshold,
        )

        # Apply category filter if specified
        if category_filter:
            results = [
                r for r in results
                if r["section"].get("metadata", {}).get("category") == category_filter
            ][:top_k]

        # Enrich results with document info
        enriched_results = []
        for result in results:
            section = result["section"]
            enriched = {
                "score": result["score"],
                "section_id": section.get("section_id", ""),
                "section_number": section.get("section_number", ""),
                "title": section.get("title", ""),
                "body": section.get("body", ""),
                "level": section.get("level", 0),
                "metadata": section.get("metadata", {}),
                "document_id": section.get("metadata", {}).get("document_id", ""),
                "category": section.get("metadata", {}).get("category", ""),
                "jurisdiction": section.get("metadata", {}).get("jurisdiction", ""),
            }
            enriched_results.append(enriched)

        return enriched_results

    def get_stats(self) -> Dict:
        """Get search engine statistics."""
        return {
            "total_sections": self.manager.section_count,
            "embedding_dimension": self.manager.dimension,
            "index_type": self.manager.index_type,
            "metric": self.manager.metric,
            "model": self.model_name,
        }


class SearchResult:
    """Search result wrapper for easy display."""

    def __init__(self, result_dict: Dict):
        self.score = result_dict["score"]
        self.section_id = result_dict["section_id"]
        self.section_number = result_dict["section_number"]
        self.title = result_dict["title"]
        self.body = result_dict["body"]
        self.level = result_dict["level"]
        self.metadata = result_dict["metadata"]
        self.document_id = result_dict["document_id"]
        self.category = result_dict["category"]
        self.jurisdiction = result_dict["jurisdiction"]

    def __repr__(self):
        return f"SearchResult(score={self.score:.4f}, section={self.section_number}, title='{self.title[:50]}...')"

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "score": self.score,
            "section_id": self.section_id,
            "section_number": self.section_number,
            "title": self.title,
            "body": self.body,
            "level": self.level,
            "metadata": self.metadata,
            "document_id": self.document_id,
            "category": self.category,
            "jurisdiction": self.jurisdiction,
        }


# Convenience function
def search_documents(
    query: str,
    top_k: int = 10,
    score_threshold: float = 0.0,
) -> List[Dict]:
    """
    Quick search function.

    Args:
        query: Search query
        top_k: Number of results
        score_threshold: Minimum score

    Returns:
        List of results
    """
    engine = SemanticSearchEngine()
    return engine.search(query, top_k, score_threshold)


if __name__ == "__main__":
    # Test search
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 search/semantic_search.py 'your query here'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    print(f"\n{'='*60}")
    print(f"Searching for: {query}")
    print(f"{'='*60}\n")

    engine = SemanticSearchEngine()
    results = engine.search(query, top_k=5)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']:.4f} | {result['category'].upper()}")
        print(f"   Section: {result['section_number']} - {result['title']}")
        print(f"   Document: {result['document_id']}")
        print(f"   Body: {result['body'][:200]}...")

    print(f"\n{'='*60}\n")