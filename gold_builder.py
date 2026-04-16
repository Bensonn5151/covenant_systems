"""
Gold Layer Builder

Orchestrates the complete Silver → Gold transformation:
1. Generate embeddings (via existing Embedder)
2. Classify sections (obligation/permission/prohibition/definition/procedural)
3. Score severity signal (definitional/procedural/mandatory/punitive)
   — language strength of the regulation text, NOT risk
4. Detect cross-references
5. Build knowledge graph entries (no risk on regulation nodes)
6. Persist Gold artifacts
7. Build fresh FAISS index

Risk is relational and belongs on policy_implements_regulation edges
computed by api/fastapi/compare.py — never on regulation sections.

Usage:
    python3 gold_builder.py
    python3 gold_builder.py --document pipeda
    python3 gold_builder.py --skip-embeddings
"""

import argparse
import json
import yaml
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import Counter

from ingestion.embed.embedder import Embedder
from ingestion.classify.section_classifier import SectionClassifier
from ingestion.classify.severity_signal import SeveritySignalScorer
from ingestion.classify.cross_reference import CrossReferenceDetector
from storage.vector_db.faiss_manager import FAISSManager


class GoldBuilder:
    """Build the complete Gold layer from Silver sections."""

    def __init__(
        self,
        silver_path: str = "storage/silver",
        gold_path: str = "storage/gold",
        kg_path: str = "storage/knowledge_graph",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.silver_path = Path(silver_path)
        self.gold_path = Path(gold_path)
        self.kg_path = Path(kg_path)
        self.model_name = model_name

        self.classifier = SectionClassifier()
        self.severity_scorer = SeveritySignalScorer()
        self.embedder = None  # lazy-loaded
        self.all_sections = []

    def discover_documents(self, document_filter: Optional[str] = None) -> List[Path]:
        """Find all Silver document directories containing sections.json."""
        doc_paths = []
        for category in ["acts", "regulations", "guidance"]:
            category_path = self.silver_path / category
            if not category_path.exists():
                continue
            for path in sorted(category_path.rglob("sections.json")):
                doc_dir = path.parent
                if document_filter and document_filter not in doc_dir.name:
                    continue
                doc_paths.append(doc_dir)
        return doc_paths

    def load_all_sections(self, doc_paths: List[Path]) -> Dict[str, List[Dict]]:
        """Load all sections keyed by document_id. Filter TOC sections."""
        docs = {}
        for path in doc_paths:
            with open(path / "sections.json", encoding="utf-8") as f:
                sections = json.load(f)
            non_toc = [s for s in sections if not s.get("metadata", {}).get("is_toc", False)]
            if not non_toc:
                continue
            doc_id = non_toc[0].get("metadata", {}).get("document_id", path.name)
            docs[doc_id] = non_toc
            self.all_sections.extend(non_toc)
        return docs

    def generate_embeddings(self, sections: List[Dict]) -> np.ndarray:
        """Generate embeddings for a batch of sections."""
        if self.embedder is None:
            self.embedder = Embedder(model_name=self.model_name)
        _, embeddings = self.embedder.embed_sections(sections)
        return embeddings

    def classify_sections(self, sections: List[Dict]) -> List[Dict]:
        """Classify all sections."""
        return self.classifier.classify_batch(sections)

    def score_severity_signals(self, sections: List[Dict], classifications: List[Dict]) -> List[Dict]:
        """Score language-strength signals for all sections."""
        return self.severity_scorer.score_batch(sections, classifications)

    def build_gold_sections(
        self,
        sections: List[Dict],
        classifications: List[Dict],
        severity_scores: List[Dict],
    ) -> List[Dict]:
        """Merge Silver section + classification + severity_signal into a Gold
        record (no embeddings inside the JSON)."""
        gold_sections = []
        for i, section in enumerate(sections):
            gold = section.copy()
            gold["classification"] = classifications[i]
            sig = severity_scores[i] or {}
            gold["severity_signal"] = sig.get("severity_signal")
            gold["operational_areas"] = sig.get("operational_areas", [])
            gold["gold_created"] = datetime.utcnow().isoformat()
            gold_sections.append(gold)
        return gold_sections

    def persist_gold(self, doc_id: str, gold_sections: List[Dict], embeddings: np.ndarray):
        """Save Gold artifacts for one document."""
        doc_gold_path = self.gold_path / doc_id
        doc_gold_path.mkdir(parents=True, exist_ok=True)

        # Save embeddings.npy
        np.save(doc_gold_path / "embeddings.npy", embeddings)

        # Save metadata.json
        metadata = {
            "model": self.model_name,
            "dimension": 384,
            "count": len(gold_sections),
            "normalized": True,
            "created": datetime.utcnow().isoformat(),
        }
        with open(doc_gold_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        # Save sections.json (Gold sections without raw embedding arrays)
        with open(doc_gold_path / "sections.json", "w", encoding="utf-8") as f:
            json.dump(gold_sections, f, indent=2, ensure_ascii=False)

        # Save semantic_labels.json
        labels = []
        for gs in gold_sections:
            labels.append({
                "section_id": gs["section_id"],
                "classification": gs["classification"],
                "severity_signal": gs.get("severity_signal"),
                "operational_areas": gs.get("operational_areas", []),
            })
        with open(doc_gold_path / "semantic_labels.json", "w") as f:
            json.dump(labels, f, indent=2)

        # Save uncertain_labels.json separately
        uncertain = [l for l in labels if l["classification"].get("uncertain", False)]
        if uncertain:
            with open(doc_gold_path / "uncertain_labels.json", "w") as f:
                json.dump(uncertain, f, indent=2)

    def build_faiss_index(self, all_gold_docs: Dict[str, dict]):
        """Build fresh FAISS index from all Gold documents."""
        # Delete stale files
        for f in ["covenant.index", "id_to_section.json", "index_metadata.json"]:
            stale = Path("storage/vector_db") / f
            if stale.exists():
                stale.unlink()

        manager = FAISSManager(dimension=384, metric="cosine", index_type="Flat")

        for doc_id, doc_data in all_gold_docs.items():
            embeddings = doc_data["embeddings"]
            sections = doc_data["gold_sections"]
            if embeddings.dtype != np.float32:
                embeddings = embeddings.astype(np.float32)
            if not embeddings.flags["C_CONTIGUOUS"]:
                embeddings = np.ascontiguousarray(embeddings)
            manager.add_embeddings(embeddings, sections)

        manager.save("storage/vector_db/covenant.index")
        print(f"\n  FAISS index: {manager.section_count} vectors")

    def build_knowledge_graph(self, all_gold_docs: Dict[str, dict]):
        """Build section-level KG nodes and cross-reference edges."""
        all_sections_flat = []
        for doc_data in all_gold_docs.values():
            all_sections_flat.extend(doc_data["gold_sections"])

        detector = CrossReferenceDetector(all_sections_flat)

        # Map classification label to KG node type
        kg_type_map = {
            "obligation": "obligation",
            "prohibition": "prohibition",
            "permission": "permission",
            "definition": "definition",
            "procedural": "section",
        }

        # Build nodes.
        # IMPORTANT: regulation/section/obligation/prohibition nodes never
        # carry risk_level. Risk only exists on policy_implements_regulation
        # edges, which are computed when a company policy is compared to a
        # regulation (see api/fastapi/compare.py).
        nodes = []
        for gs in all_sections_flat:
            cls = gs.get("classification", {})
            node_type = kg_type_map.get(cls.get("label", "section"), "section")
            metadata = {
                "jurisdiction": gs.get("metadata", {}).get("jurisdiction", "Canada"),
                "classification_confidence": cls.get("confidence", 0),
                "operational_areas": gs.get("operational_areas", []),
            }
            # severity_signal only on obligation/prohibition nodes.
            if node_type in ("obligation", "prohibition") and gs.get("severity_signal"):
                metadata["severity_signal"] = gs["severity_signal"]
            nodes.append({
                "id": gs["section_id"],
                "type": node_type,
                "source_document": gs.get("metadata", {}).get("document_id", ""),
                "section_number": gs.get("section_number", ""),
                "text": gs.get("body", "")[:500],
                "domains": ["privacy"],
                "metadata": metadata,
            })

        # Build edges
        all_edges = []
        for gs in all_sections_flat:
            edges = detector.detect(gs)
            all_edges.extend(edges)

        # Save
        self.kg_path.mkdir(parents=True, exist_ok=True)
        with open(self.kg_path / "nodes.yaml", "w") as f:
            yaml.dump({"nodes": nodes}, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        with open(self.kg_path / "edges.yaml", "w") as f:
            yaml.dump({"edges": all_edges}, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"  KG: {len(nodes)} nodes, {len(all_edges)} edges")

    def build(self, document_filter: Optional[str] = None, skip_embeddings: bool = False):
        """Execute the full Gold layer build."""
        print("=" * 60)
        print("GOLD LAYER BUILDER")
        print("=" * 60)

        doc_paths = self.discover_documents(document_filter)
        print(f"\nFound {len(doc_paths)} documents in Silver\n")

        doc_sections = self.load_all_sections(doc_paths)
        all_gold_docs = {}
        label_counts = Counter()
        severity_counts = Counter()
        total_sections = 0

        for doc_id, sections in doc_sections.items():
            print(f"--- {doc_id} ({len(sections)} sections) ---")

            # 1. Embeddings
            gold_emb_path = self.gold_path / doc_id / "embeddings.npy"
            if skip_embeddings and gold_emb_path.exists():
                print("  Embeddings: loaded from cache")
                embeddings = np.load(gold_emb_path)
            else:
                embeddings = self.generate_embeddings(sections)

            # 2. Classification
            classifications = self.classify_sections(sections)
            for c in classifications:
                label_counts[c["label"]] += 1

            # 3. Severity signal scoring (language strength, NOT risk)
            severity_scores = self.score_severity_signals(sections, classifications)
            for s in severity_scores:
                sig = s.get("severity_signal")
                if sig:
                    severity_counts[sig] += 1

            # 4. Merge into Gold records
            gold_sections = self.build_gold_sections(sections, classifications, severity_scores)

            # 5. Persist
            self.persist_gold(doc_id, gold_sections, embeddings)
            print(f"  Saved to storage/gold/{doc_id}/")

            all_gold_docs[doc_id] = {
                "embeddings": embeddings,
                "gold_sections": gold_sections,
            }
            total_sections += len(sections)

        # 6. Build fresh FAISS index
        print(f"\nBuilding FAISS index...")
        self.build_faiss_index(all_gold_docs)

        # 7. Build knowledge graph
        print("Building knowledge graph...")
        self.build_knowledge_graph(all_gold_docs)

        # 8. Summary
        print(f"\n{'=' * 60}")
        print("GOLD LAYER COMPLETE")
        print(f"{'=' * 60}")
        print(f"Documents: {len(all_gold_docs)}")
        print(f"Sections:  {total_sections}")
        print(f"\nClassification:")
        for label, count in label_counts.most_common():
            print(f"  {label:15} {count:>4}")
        print(f"\nSeverity signals (obligations + prohibitions):")
        for level, count in severity_counts.most_common():
            print(f"  {level:15} {count:>4}")
        print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(description="Build Gold layer from Silver sections")
    parser.add_argument("--document", type=str, help="Process specific document only")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip if embeddings.npy exists")
    args = parser.parse_args()

    builder = GoldBuilder()
    builder.build(document_filter=args.document, skip_embeddings=args.skip_embeddings)


if __name__ == "__main__":
    main()
