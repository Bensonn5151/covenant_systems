"""
Legislative Mapper Module

Automated retrieval and mapping of Canadian federal legislation from laws-lois.justice.gc.ca.

Components:
- JusticeClient: HTTP client with polite crawling
- MetadataParser: Extract metadata from HTML pages
- Downloader: Download and validate PDFs
- ManifestGenerator: Generate manifest.yaml from discovered documents
"""

from .justice_client import JusticeClient
from .metadata_parser import MetadataParser
from .downloader import Downloader
from .manifest_generator import ManifestGenerator

__all__ = [
    "JusticeClient",
    "MetadataParser",
    "Downloader",
    "ManifestGenerator",
]