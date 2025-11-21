"""
PDF Downloader with Checksum Validation

Downloads PDFs from laws-lois.justice.gc.ca with:
- Progress tracking
- Checksum validation (SHA256)
- Skip existing files (unless force=True)
"""

import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime


class Downloader:
    """Handles PDF downloading with validation."""

    def __init__(self, output_dir: str = "data/raw"):
        """
        Initialize downloader.

        Args:
            output_dir: Directory to save downloaded PDFs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download(
        self,
        client,
        pdf_url: str,
        filename: str,
        category: str = "acts",
        force: bool = False
    ) -> Optional[dict]:
        """
        Download PDF file with validation.

        Args:
            client: JusticeClient instance
            pdf_url: PDF URL (relative or absolute)
            filename: Target filename
            category: Subdirectory (acts, regulations, guidance)
            force: If True, re-download even if file exists

        Returns:
            Dict with download metadata or None if failed
        """
        # Create category subdirectory
        category_dir = self.output_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = category_dir / filename

        # Check if file already exists
        if file_path.exists() and not force:
            print(f"  ⏩ Skipping (already exists): {filename}")
            return {
                "filename": filename,
                "file_path": str(file_path),
                "status": "skipped",
                "checksum": self._calculate_checksum(file_path),
            }

        print(f"  ⬇️  Downloading: {filename}")

        # Download PDF
        success = client.download_pdf(pdf_url, str(file_path))

        if not success:
            return None

        # Calculate checksum
        checksum = self._calculate_checksum(file_path)
        file_size = file_path.stat().st_size

        print(f"  ✅ Downloaded: {filename} ({file_size:,} bytes)")

        return {
            "filename": filename,
            "file_path": str(file_path),
            "status": "downloaded",
            "checksum": checksum,
            "file_size": file_size,
            "downloaded_at": datetime.utcnow().isoformat() + "Z",
        }

    @staticmethod
    def _calculate_checksum(file_path: Path) -> str:
        """
        Calculate SHA256 checksum of file.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal SHA256 checksum
        """
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)

        return sha256.hexdigest()