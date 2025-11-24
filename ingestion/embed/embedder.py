"""
Embedding Generation Module

Generates vector embeddings for text sections using sentence-transformers.
Transforms Silver (structured sections) → Gold (embeddings + semantic labels).

Uses sentence-transformers/all-MiniLM-L6-v2 by default (384 dimensions).
Fast, efficient, and good quality for regulatory text.
"""

# Set threading environment variables before imports
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import numpy as np
from typing import List, Dict, Optional, Union
from pathlib import Path
import json

try:
    from sentence_transformers import SentenceTransformer
    import torch
    # Disable PyTorch multiprocessing
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
except ImportError as e:
    raise ImportError(
        "Embedding dependencies not installed. "
        "Run: pip install sentence-transformers torch"
    ) from e


class Embedder:
    """Generate embeddings for text sections."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        batch_size: int = 32,
        normalize: bool = True,
    ):
        """
        Initialize embedder.

        Args:
            model_name: Sentence transformer model name
            device: Device to use (cpu, cuda, mps)
            batch_size: Batch size for encoding
            normalize: Whether to normalize embeddings (for cosine similarity)
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.normalize = normalize

        print(f"Loading embedding model: {model_name}")
        self.model = self._load_model()
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"✓ Model loaded. Dimension: {self.dimension}")

    def _load_model(self) -> SentenceTransformer:
        """Load sentence transformer model."""
        try:
            model = SentenceTransformer(self.model_name)

            # Move to device
            if self.device == "cuda" and torch.cuda.is_available():
                model = model.to("cuda")
                print(f"✓ Using GPU: {torch.cuda.get_device_name(0)}")
            elif self.device == "mps" and torch.backends.mps.is_available():
                model = model.to("mps")
                print("✓ Using Apple Metal (MPS)")
            else:
                model = model.to("cpu")
                print("✓ Using CPU")

            return model

        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model: {e}")

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            Embedding array
        """
        embedding = self.model.encode(
            [text],
            batch_size=1,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
        )

        if isinstance(embedding, torch.Tensor):
            embedding = embedding.cpu().numpy()

        return embedding[0]

    def embed_texts(
        self,
        texts: List[str],
        show_progress: bool = True,
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            show_progress: Show progress bar

        Returns:
            Array of embeddings (N x dimension)
        """
        # Disable multiprocessing to avoid conflicts with FAISS
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize,
            show_progress_bar=show_progress,
            convert_to_numpy=True,  # Force numpy output
        )

        # Ensure float32 and C-contiguous for FAISS
        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)

        return embeddings

    def embed_sections(
        self,
        sections: List[Dict],
        text_field: str = "body",
        show_progress: bool = True,
    ) -> tuple[List[Dict], np.ndarray]:
        """
        Generate embeddings for a list of sections.

        Args:
            sections: List of section dictionaries
            text_field: Field name containing text to embed
            show_progress: Show progress bar

        Returns:
            Tuple of (enriched_sections, embeddings_array)
        """
        # Extract texts
        texts = [section.get(text_field, "") for section in sections]

        print(f"Generating embeddings for {len(texts)} sections...")

        # Generate embeddings
        embeddings = self.embed_texts(texts, show_progress=show_progress)

        # Add embeddings to sections
        enriched_sections = []
        for section, embedding in zip(sections, embeddings):
            enriched = section.copy()
            enriched["embedding"] = embedding.tolist()
            enriched["embedding_model"] = self.model_name
            enriched["embedding_dimension"] = self.dimension
            enriched_sections.append(enriched)

        print(f"✓ Generated {len(embeddings)} embeddings")

        return enriched_sections, embeddings

    def save_embeddings(
        self,
        embeddings: np.ndarray,
        output_path: str,
        sections: Optional[List[Dict]] = None,
    ):
        """
        Save embeddings to disk.

        Args:
            embeddings: Embeddings array
            output_path: Path to save embeddings
            sections: Optional sections to save alongside
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save embeddings as numpy array
        np.save(output_path, embeddings)
        print(f"✓ Saved embeddings: {output_path}")

        # Save metadata
        metadata = {
            "model": self.model_name,
            "dimension": self.dimension,
            "count": len(embeddings),
            "normalized": self.normalize,
        }

        metadata_path = output_path.parent / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ Saved metadata: {metadata_path}")

        # Save sections if provided
        if sections:
            sections_path = output_path.parent / "sections.json"
            with open(sections_path, "w", encoding="utf-8") as f:
                json.dump(sections, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved sections: {sections_path}")

    def load_embeddings(self, embeddings_path: str) -> np.ndarray:
        """
        Load embeddings from disk.

        Args:
            embeddings_path: Path to embeddings file

        Returns:
            Embeddings array
        """
        embeddings = np.load(embeddings_path)
        print(f"✓ Loaded {len(embeddings)} embeddings from {embeddings_path}")
        return embeddings

    def similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Cosine similarity score
        """
        # Ensure numpy arrays
        if isinstance(embedding1, list):
            embedding1 = np.array(embedding1)
        if isinstance(embedding2, list):
            embedding2 = np.array(embedding2)

        # Calculate cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


# Convenience functions
def embed_document(
    sections_path: str,
    output_path: str,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> tuple[List[Dict], np.ndarray]:
    """
    Generate embeddings for a document's sections.

    Args:
        sections_path: Path to sections.json file
        output_path: Path to save embeddings
        model_name: Embedding model name

    Returns:
        Tuple of (enriched_sections, embeddings)
    """
    # Load sections
    with open(sections_path, "r", encoding="utf-8") as f:
        sections = json.load(f)

    # Generate embeddings
    embedder = Embedder(model_name=model_name)
    enriched_sections, embeddings = embedder.embed_sections(sections)

    # Save
    embedder.save_embeddings(embeddings, output_path, enriched_sections)

    return enriched_sections, embeddings
