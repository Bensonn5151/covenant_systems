"""
Knowledge Graph Builder from Manifest

Automatically builds knowledge graph (nodes.yaml and edges.yaml) from manifest relationships.

Extracts:
- parent_act → regulation relationships
- implements → policy relationships
- related_acts → guidance relationships

Usage:
    python3 build_kg_from_manifest.py data/raw/manifest.yaml [--output storage/knowledge_graph]

Example:
    python3 build_kg_from_manifest.py data/raw/manifest.yaml
"""

import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class KnowledgeGraphBuilder:
    """Builds knowledge graph from manifest relationships."""

    def __init__(self, manifest_path: str, output_dir: str = "storage/knowledge_graph"):
        """
        Initialize KG builder.

        Args:
            manifest_path: Path to manifest.yaml file
            output_dir: Directory to save nodes.yaml and edges.yaml
        """
        self.manifest_path = Path(manifest_path)
        self.output_dir = Path(output_dir)
        self.manifest_data = None
        self.nodes: List[Dict] = []
        self.edges: List[Dict] = []

    def load_manifest(self) -> bool:
        """Load manifest file."""
        if not self.manifest_path.exists():
            print(f"❌ Manifest file not found: {self.manifest_path}")
            return False

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self.manifest_data = yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            print(f"❌ YAML parsing error: {e}")
            return False

    def build_nodes(self):
        """Build nodes from manifest documents."""
        documents = self.manifest_data.get("documents", [])

        for doc in documents:
            filename = doc.get("filename", "")
            category = doc.get("category", "unknown")
            title = doc.get("title", filename)

            # Create node ID from title (sanitized)
            node_id = self._create_node_id(title)

            node = {
                "id": node_id,
                "type": category,
                "title": title,
                "filename": filename,
                "metadata": {},
            }

            # Add category-specific metadata
            if "jurisdiction" in doc:
                node["metadata"]["jurisdiction"] = doc["jurisdiction"]

            if "regulator" in doc:
                node["metadata"]["regulator"] = doc["regulator"]

            if "citation" in doc:
                node["metadata"]["citation"] = doc["citation"]

            if "source_url" in doc:
                node["metadata"]["source_url"] = doc["source_url"]

            if "company_id" in doc:
                node["metadata"]["company_id"] = doc["company_id"]

            self.nodes.append(node)

        print(f"✓ Created {len(self.nodes)} nodes")

    def build_edges(self):
        """Build edges from manifest relationships."""
        documents = self.manifest_data.get("documents", [])

        # Create title → node_id mapping
        title_to_id = {
            doc.get("title"): self._create_node_id(doc.get("title"))
            for doc in documents
            if "title" in doc
        }

        for doc in documents:
            title = doc.get("title")
            if not title:
                continue

            from_id = title_to_id[title]

            # 1. parent_act → regulation relationship
            if "parent_act" in doc:
                parent = doc["parent_act"]
                if parent in title_to_id:
                    to_id = title_to_id[parent]
                    self.edges.append({
                        "from": from_id,
                        "to": to_id,
                        "type": "derives_from",
                        "description": f"{title} is a regulation under {parent}",
                        "confidence": 1.0,
                        "source": "manifest",
                        "date_created": datetime.utcnow().isoformat(),
                    })

            # 2. implements → policy relationship
            if "implements" in doc:
                implements = doc["implements"]
                for impl_title in implements:
                    if impl_title in title_to_id:
                        to_id = title_to_id[impl_title]
                        self.edges.append({
                            "from": from_id,
                            "to": to_id,
                            "type": "implements",
                            "description": f"{title} implements {impl_title}",
                            "confidence": 1.0,
                            "source": "manifest",
                            "date_created": datetime.utcnow().isoformat(),
                        })

            # 3. related_acts → guidance relationship
            if "related_acts" in doc:
                related = doc["related_acts"]
                for related_title in related:
                    if related_title in title_to_id:
                        to_id = title_to_id[related_title]
                        self.edges.append({
                            "from": from_id,
                            "to": to_id,
                            "type": "relates_to",
                            "description": f"{title} provides guidance for {related_title}",
                            "confidence": 1.0,
                            "source": "manifest",
                            "date_created": datetime.utcnow().isoformat(),
                        })

        print(f"✓ Created {len(self.edges)} edges")

    def _create_node_id(self, title: str) -> str:
        """
        Create node ID from title.

        Args:
            title: Document title

        Returns:
            Sanitized node ID (e.g., "bank_act", "osfi_b13")
        """
        # Simple sanitization: lowercase, replace spaces with underscores, remove special chars
        node_id = title.lower()
        node_id = node_id.replace(" ", "_")
        node_id = node_id.replace("(", "").replace(")", "")
        node_id = node_id.replace("-", "_")
        node_id = node_id.replace(".", "")
        node_id = node_id.replace(",", "")
        node_id = node_id.replace(":", "")

        # Shorten long IDs
        if len(node_id) > 50:
            node_id = node_id[:50]

        return node_id

    def save_knowledge_graph(self):
        """Save nodes and edges to YAML files."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Save nodes
        nodes_file = self.output_dir / "nodes.yaml"
        with open(nodes_file, "w", encoding="utf-8") as f:
            yaml.dump(
                {"nodes": self.nodes},
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        print(f"✓ Saved nodes to: {nodes_file}")

        # Save edges
        edges_file = self.output_dir / "edges.yaml"
        with open(edges_file, "w", encoding="utf-8") as f:
            yaml.dump(
                {"edges": self.edges},
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        print(f"✓ Saved edges to: {edges_file}")

    def build(self) -> bool:
        """Build complete knowledge graph."""
        print("\n" + "=" * 60)
        print("BUILDING KNOWLEDGE GRAPH FROM MANIFEST")
        print("=" * 60)
        print(f"Manifest: {self.manifest_path}")
        print(f"Output: {self.output_dir}")
        print()

        if not self.load_manifest():
            return False

        # Build nodes and edges
        self.build_nodes()
        self.build_edges()

        # Save to files
        self.save_knowledge_graph()

        # Print summary
        self._print_summary()

        return True

    def _print_summary(self):
        """Print knowledge graph summary."""
        print("\n" + "=" * 60)
        print("KNOWLEDGE GRAPH SUMMARY")
        print("=" * 60)

        # Node breakdown by type
        node_types = {}
        for node in self.nodes:
            node_type = node["type"]
            node_types[node_type] = node_types.get(node_type, 0) + 1

        print(f"\nNodes: {len(self.nodes)}")
        for node_type in sorted(node_types.keys()):
            print(f"  • {node_type}: {node_types[node_type]}")

        # Edge breakdown by type
        edge_types = {}
        for edge in self.edges:
            edge_type = edge["type"]
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

        print(f"\nEdges: {len(self.edges)}")
        for edge_type in sorted(edge_types.keys()):
            print(f"  • {edge_type}: {edge_types[edge_type]}")

        # Sample relationships
        if self.edges:
            print("\nSample relationships:")
            for edge in self.edges[:5]:
                from_node = next((n for n in self.nodes if n["id"] == edge["from"]), None)
                to_node = next((n for n in self.nodes if n["id"] == edge["to"]), None)

                if from_node and to_node:
                    print(f"  • {from_node['title']} --[{edge['type']}]--> {to_node['title']}")

            if len(self.edges) > 5:
                print(f"  ... and {len(self.edges) - 5} more")

        print("=" * 60)


def main():
    """Main KG building function."""
    parser = argparse.ArgumentParser(
        description="Build knowledge graph from manifest relationships"
    )
    parser.add_argument("manifest", help="Path to manifest.yaml file")
    parser.add_argument(
        "--output",
        default="storage/knowledge_graph",
        help="Output directory for nodes.yaml and edges.yaml (default: storage/knowledge_graph)"
    )

    args = parser.parse_args()

    builder = KnowledgeGraphBuilder(args.manifest, args.output)
    success = builder.build()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()