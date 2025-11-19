"""
Document Classifier

Automatically classifies documents into categories using taxonomy rules.
Supports: Acts, Regulations, Guidance, Company Policies
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import uuid


class DocumentClassifier:
    """Classify documents based on taxonomy rules."""

    def __init__(self, taxonomy_path: str = "configs/taxonomy.yaml"):
        """
        Initialize classifier with taxonomy configuration.

        Args:
            taxonomy_path: Path to taxonomy.yaml
        """
        self.taxonomy_path = Path(taxonomy_path)
        self.config = self._load_taxonomy()

        self.categories = self.config["categories"]
        self.regulators = self.config["regulators"]
        self.acts = self.config["acts"]
        self.rules = self.config["classification_rules"]

    def _load_taxonomy(self) -> Dict:
        """Load taxonomy configuration."""
        with open(self.taxonomy_path, "r") as f:
            return yaml.safe_load(f)

    def classify(
        self,
        title: str,
        content: Optional[str] = None,
        filename: Optional[str] = None,
        manual_category: Optional[str] = None,
    ) -> Dict:
        """
        Classify a document into a category.

        Args:
            title: Document title
            content: Document content (for content-based classification)
            filename: Original filename
            manual_category: Manual override (if provided)

        Returns:
            Classification result with category, confidence, metadata
        """
        # Manual override takes precedence
        if manual_category and manual_category in self.categories:
            return self._create_result(
                category=manual_category,
                confidence=1.0,
                method="manual",
                title=title,
            )

        # Try title-based classification first
        category, confidence = self._classify_by_title(title, filename)

        # If low confidence, try content-based
        if confidence < 0.7 and content:
            content_category, content_confidence = self._classify_by_content(content)
            if content_confidence > confidence:
                category = content_category
                confidence = content_confidence

        return self._create_result(
            category=category,
            confidence=confidence,
            method="automatic",
            title=title,
        )

    def _classify_by_title(
        self, title: str, filename: Optional[str] = None
    ) -> Tuple[str, float]:
        """Classify based on title patterns."""
        scores = {cat: 0.0 for cat in self.categories.keys()}

        # Check title patterns
        for category, patterns in self.rules["title_patterns"].items():
            for pattern in patterns:
                if re.search(pattern, title, re.IGNORECASE):
                    scores[category] += 0.4

        # Check filename if provided
        if filename:
            for category, patterns in self.rules["title_patterns"].items():
                for pattern in patterns:
                    if re.search(pattern, filename, re.IGNORECASE):
                        scores[category] += 0.2

        # Get best match
        best_category = max(scores, key=scores.get)
        confidence = min(scores[best_category], 1.0)

        # Default to policy if confidence too low
        if confidence < 0.3:
            return "policy", 0.5

        return best_category, confidence

    def _classify_by_content(self, content: str) -> Tuple[str, float]:
        """Classify based on content patterns."""
        scores = {cat: 0.0 for cat in self.categories.keys()}

        # Check first 2000 characters for efficiency
        content_sample = content[:2000]

        # Check content patterns
        for category, patterns in self.rules["content_patterns"].items():
            for pattern in patterns:
                if re.search(pattern, content_sample, re.IGNORECASE):
                    scores[category] += 0.3

        best_category = max(scores, key=scores.get)
        confidence = min(scores[best_category], 1.0)

        return best_category, confidence

    def detect_regulator(self, title: str, content: Optional[str] = None) -> Optional[str]:
        """
        Detect which regulator issued the document.

        Args:
            title: Document title
            content: Document content

        Returns:
            Regulator code (OSFI, FINTRAC, OPC, FCAC) or None
        """
        text = f"{title}\n{content[:1000] if content else ''}"

        for regulator, config in self.regulators.items():
            for keyword in config["keywords"]:
                if keyword.lower() in text.lower():
                    return regulator

        return None

    def detect_parent_act(self, title: str, content: Optional[str] = None) -> Optional[str]:
        """
        Detect parent act for regulations.

        Args:
            title: Document title
            content: Document content

        Returns:
            Parent act short name or None
        """
        text = f"{title}\n{content[:1000] if content else ''}"

        for act_id, act_config in self.acts.items():
            for keyword in act_config["keywords"]:
                if keyword.lower() in text.lower():
                    return act_config["short_name"]

        return None

    def detect_jurisdiction(self, title: str, content: Optional[str] = None) -> str:
        """
        Detect jurisdiction (federal, provincial, internal).

        Args:
            title: Document title
            content: Document content

        Returns:
            Jurisdiction code
        """
        text = f"{title}\n{content[:1000] if content else ''}"

        # Check for federal indicators
        federal_indicators = ["S.C.", "Parliament of Canada", "Governor in Council"]
        if any(ind in text for ind in federal_indicators):
            return "federal"

        # Check for provincial indicators
        provincial_indicators = ["Ontario", "Quebec", "British Columbia", "Alberta"]
        if any(prov in text for prov in provincial_indicators):
            return "provincial"

        # Default to internal for company policies
        return "internal"

    def create_metadata(
        self,
        title: str,
        category: str,
        filename: Optional[str] = None,
        content: Optional[str] = None,
        version: str = "1.0",
        company_id: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        """
        Create full metadata object for a document.

        Args:
            title: Document title
            category: Document category (act, regulation, guidance, policy)
            filename: Original filename
            content: Document content
            version: Document version
            company_id: Company ID (for policies)
            **kwargs: Additional metadata fields

        Returns:
            Complete metadata dictionary
        """
        doc_id = str(uuid.uuid4())

        metadata = {
            "doc_id": doc_id,
            "category": category,
            "title": title,
            "version": version,
            "ingested_at": datetime.utcnow().isoformat(),
            "source_type": "pdf" if filename and filename.endswith(".pdf") else "unknown",
        }

        # Add jurisdiction
        metadata["jurisdiction"] = self.detect_jurisdiction(title, content)

        # Category-specific fields
        if category == "regulation":
            parent_act = self.detect_parent_act(title, content)
            if parent_act:
                metadata["parent_act"] = parent_act

        elif category == "guidance":
            regulator = self.detect_regulator(title, content)
            if regulator:
                metadata["regulator"] = regulator

        elif category == "policy":
            if company_id:
                metadata["company_id"] = company_id

        # Add any additional fields
        metadata.update(kwargs)

        return metadata

    def get_storage_path(
        self, category: str, document_id: str, layer: str = "bronze", **kwargs
    ) -> Path:
        """
        Get storage path for a document based on category and layer.

        Args:
            category: Document category
            document_id: Document ID
            layer: Storage layer (bronze, silver, gold)
            **kwargs: Additional path components (regulator, company_id)

        Returns:
            Path object for storage location
        """
        base_path = Path("storage") / layer

        if category == "guidance":
            regulator = kwargs.get("regulator", "unknown")
            return base_path / "guidance" / regulator.lower() / document_id

        elif category == "policy":
            company_id = kwargs.get("company_id", "default")
            return base_path / "company_policies" / company_id / document_id

        else:
            # acts, regulations
            storage_path = self.categories[category]["storage_path"]
            return base_path / storage_path / document_id

    def _create_result(
        self, category: str, confidence: float, method: str, title: str
    ) -> Dict:
        """Create classification result."""
        return {
            "category": category,
            "confidence": confidence,
            "method": method,
            "title": title,
            "category_name": self.categories[category]["name"],
            "storage_path": self.categories[category]["storage_path"],
        }


# Convenience functions
def classify_document(
    title: str,
    content: Optional[str] = None,
    filename: Optional[str] = None,
    manual_category: Optional[str] = None,
) -> Dict:
    """
    Classify a document (convenience wrapper).

    Args:
        title: Document title
        content: Document content
        filename: Original filename
        manual_category: Manual override

    Returns:
        Classification result
    """
    classifier = DocumentClassifier()
    return classifier.classify(title, content, filename, manual_category)