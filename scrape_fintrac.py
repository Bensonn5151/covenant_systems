"""
FINTRAC HTML Guidance Scraper

Fetches FINTRAC HTML guidance pages and saves content.
Can extract main content and save as:
- Clean HTML
- Markdown (optional)
- Text

Usage:
    python3 scrape_fintrac.py data/raw/fintrac_guidance_manifest.yaml --format text
    python3 scrape_fintrac.py data/raw/fintrac_guidance_manifest.yaml --format html

Instructions:
    After scraping, manually convert HTML/text to PDF:
    - Open in browser
    - Print → Save as PDF
    - Save to data/raw/guidance/fintrac/
"""

import sys
import yaml
import argparse
import requests
import time
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, Optional


class FINTRACscraper:
    """Scrapes FINTRAC HTML guidance pages."""

    def __init__(self, output_dir: str = "data/raw/guidance/fintrac/html"):
        """
        Initialize scraper.

        Args:
            output_dir: Directory to save scraped content
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CovenantAI FINTRAC Scraper/1.0 (Compliance Research)",
            "Accept": "text/html",
        })

        self.stats = {
            "fetched": 0,
            "errors": 0,
            "skipped": 0,
        }

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch HTML page.

        Args:
            url: Page URL

        Returns:
            HTML content or None if failed
        """
        try:
            time.sleep(1.5)  # Polite delay
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                return response.text
            else:
                print(f"  ❌ HTTP {response.status_code}: {url}")
                return None

        except Exception as e:
            print(f"  ❌ Error fetching {url}: {e}")
            return None

    def extract_main_content(self, html: str) -> Dict[str, str]:
        """
        Extract main content from FINTRAC page.

        Args:
            html: HTML content

        Returns:
            Dict with title and main content
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = None
        title_elem = soup.find("h1", {"id": "wb-cont"})
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Extract main content area
        # FINTRAC uses <main> tag or class "container"
        main_content = soup.find("main")
        if not main_content:
            main_content = soup.find("div", class_="container")

        # Remove navigation, footers, etc.
        if main_content:
            for unwanted in main_content.find_all(["nav", "footer", "script", "style"]):
                unwanted.decompose()

        content_html = str(main_content) if main_content else html

        return {
            "title": title or "Untitled",
            "html": content_html,
            "text": main_content.get_text(separator="\n", strip=True) if main_content else "",
        }

    def extract_update_date(self, html: str) -> Optional[str]:
        """
        Extract "New as of" or "Updated on" date from page.

        Args:
            html: HTML content

        Returns:
            Date string or None
        """
        soup = BeautifulSoup(html, "html.parser")

        # Look for "New as of" or "Updated on" text
        import re

        text = soup.get_text()

        # Pattern: "New as of October 1, 2025" or "Updated on September 9, 2025"
        patterns = [
            r"New as of ([A-Za-z]+ \d{1,2}, \d{4})",
            r"Updated on ([A-Za-z]+ \d{1,2}, \d{4})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def save_content(
        self,
        content: Dict,
        filename: str,
        output_format: str = "html"
    ):
        """
        Save content to file.

        Args:
            content: Content dict from extract_main_content()
            filename: Base filename (without extension)
            output_format: "html" or "text"
        """
        if output_format == "html":
            output_file = self.output_dir / f"{filename}.html"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"<html><head><meta charset='utf-8'><title>{content['title']}</title></head><body>")
                f.write(content["html"])
                f.write("</body></html>")

        elif output_format == "text":
            output_file = self.output_dir / f"{filename}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"{content['title']}\n")
                f.write("=" * len(content['title']) + "\n\n")
                f.write(content["text"])

        print(f"  ✅ Saved: {output_file.name}")

    def scrape_from_manifest(self, manifest_path: str, output_format: str = "html"):
        """
        Scrape all URLs from FINTRAC manifest.

        Args:
            manifest_path: Path to fintrac_guidance_manifest.yaml
            output_format: "html" or "text"
        """
        print(f"\n{'=' * 60}")
        print("FINTRAC GUIDANCE SCRAPER")
        print(f"{'=' * 60}")
        print(f"Manifest: {manifest_path}")
        print(f"Output: {self.output_dir}")
        print(f"Format: {output_format}")
        print(f"{'=' * 60}\n")

        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        documents = manifest.get("documents", [])
        total = len(documents)

        print(f"Found {total} FINTRAC guidance documents\n")

        for i, doc in enumerate(documents, 1):
            title = doc.get("title", "Untitled")
            url = doc.get("source_url")
            filename_base = doc.get("filename", "").replace(".pdf", "")

            print(f"[{i}/{total}] {title}")
            print(f"  URL: {url}")

            if not url:
                print(f"  ⚠️  No source_url found")
                self.stats["skipped"] += 1
                continue

            # Check if already exists
            if output_format == "html":
                output_file = self.output_dir / f"{filename_base}.html"
            else:
                output_file = self.output_dir / f"{filename_base}.txt"

            if output_file.exists():
                print(f"  ⏩ Skipping (already exists)")
                self.stats["skipped"] += 1
                continue

            # Fetch page
            html = self.fetch_page(url)

            if not html:
                self.stats["errors"] += 1
                continue

            # Extract content
            content = self.extract_main_content(html)

            # Check for update date
            update_date = self.extract_update_date(html)
            if update_date:
                print(f"  📅 Last updated: {update_date}")

            # Save
            self.save_content(content, filename_base, output_format)
            self.stats["fetched"] += 1

            print()

        # Summary
        print(f"\n{'=' * 60}")
        print("SCRAPING SUMMARY")
        print(f"{'=' * 60}")
        print(f"Fetched: {self.stats['fetched']}")
        print(f"Skipped: {self.stats['skipped']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"{'=' * 60}\n")

        print("Next steps:")
        print("1. Review HTML/text files in:", self.output_dir)
        print("2. Convert to PDF:")
        print(f"   - Open {self.output_dir}/<file>.html in browser")
        print("   - Print → Save as PDF")
        print("   - Save to data/raw/guidance/fintrac/")
        print("3. Run: python3 batch_ingest.py data/raw/fintrac_guidance_manifest.yaml")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Scrape FINTRAC HTML guidance pages"
    )
    parser.add_argument(
        "manifest",
        help="Path to fintrac_guidance_manifest.yaml"
    )
    parser.add_argument(
        "--format",
        choices=["html", "text"],
        default="html",
        help="Output format (default: html)"
    )
    parser.add_argument(
        "--output",
        default="data/raw/guidance/fintrac/html",
        help="Output directory (default: data/raw/guidance/fintrac/html)"
    )

    args = parser.parse_args()

    # Set output directory based on format if using default
    output_dir = args.output
    if args.output == "data/raw/guidance/fintrac/html":
        # User is using default, adjust based on format
        if args.format == "text":
            output_dir = "data/raw/guidance/fintrac/txt"
        else:
            output_dir = "data/raw/guidance/fintrac/html"

    scraper = FINTRACscraper(output_dir=output_dir)
    scraper.scrape_from_manifest(args.manifest, output_format=args.format)


if __name__ == "__main__":
    main()