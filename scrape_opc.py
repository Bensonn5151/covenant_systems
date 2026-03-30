"""
OPC (Office of the Privacy Commissioner) HTML Guidance Scraper

Fetches OPC guidance pages from priv.gc.ca and saves content.
Modeled after scrape_fintrac.py — manifest-driven with polite rate-limiting.

Usage:
    python3 scrape_opc.py data/raw/opc_guidance_manifest.yaml --format text
    python3 scrape_opc.py data/raw/opc_guidance_manifest.yaml --format html

After scraping, ingest via:
    python3 batch_ingest.py data/raw/opc_guidance_manifest.yaml
"""

import sys
import yaml
import argparse
import requests
import time
import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, Optional


class OPCScraper:
    """Scrapes OPC HTML guidance pages from priv.gc.ca."""

    def __init__(self, output_dir: str = "data/raw/guidance/opc/html"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CovenantAI OPC Scraper/1.0 (Compliance Research)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-CA,en;q=0.9",
        })

        self.stats = {
            "fetched": 0,
            "errors": 0,
            "skipped": 0,
        }

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML page with polite delay."""
        try:
            time.sleep(1.5)
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                return response.text
            else:
                print(f"  HTTP {response.status_code}: {url}")
                return None

        except Exception as e:
            print(f"  Error fetching {url}: {e}")
            return None

    def extract_main_content(self, html: str) -> Dict[str, str]:
        """Extract main content from OPC guidance page."""
        soup = BeautifulSoup(html, "html.parser")

        # Extract title — OPC uses h1#wb-cont (standard GC Web Experience Toolkit)
        title = None
        title_elem = soup.find("h1", {"id": "wb-cont"})
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Extract main content — OPC uses <main> tag
        main_content = soup.find("main")
        if not main_content:
            main_content = soup.find("div", {"id": "wb-main"})
        if not main_content:
            main_content = soup.find("div", class_="container")

        # Remove navigation, sidebar, footers, scripts
        if main_content:
            for unwanted in main_content.find_all(
                ["nav", "footer", "script", "style", "aside"]
            ):
                unwanted.decompose()

            # Remove GC branding / breadcrumbs
            for bc in main_content.find_all("div", class_="breadcrumb"):
                bc.decompose()
            for bc in main_content.find_all("ol", class_="breadcrumb"):
                bc.decompose()

        content_html = str(main_content) if main_content else html
        content_text = (
            main_content.get_text(separator="\n", strip=True) if main_content else ""
        )

        return {
            "title": title or "Untitled",
            "html": content_html,
            "text": content_text,
        }

    def extract_update_date(self, html: str) -> Optional[str]:
        """Extract date modified from OPC page metadata."""
        soup = BeautifulSoup(html, "html.parser")

        # GC WET standard: <time property="dateModified">
        time_elem = soup.find("time", {"property": "dateModified"})
        if time_elem:
            return time_elem.get_text(strip=True) or time_elem.get("datetime")

        # Fallback: look for text patterns
        text = soup.get_text()
        patterns = [
            r"Date modified:\s*(\d{4}-\d{2}-\d{2})",
            r"Last updated:\s*([A-Za-z]+ \d{1,2}, \d{4})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def save_content(self, content: Dict, filename: str, output_format: str = "html"):
        """Save extracted content to file."""
        if output_format == "html":
            output_file = self.output_dir / f"{filename}.html"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(
                    f"<html><head><meta charset='utf-8'><title>{content['title']}</title></head><body>"
                )
                f.write(content["html"])
                f.write("</body></html>")

        elif output_format == "text":
            output_file = self.output_dir / f"{filename}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"{content['title']}\n")
                f.write("=" * len(content["title"]) + "\n\n")
                f.write(content["text"])

        print(f"  Saved: {output_file.name}")

    def scrape_from_manifest(self, manifest_path: str, output_format: str = "html"):
        """Scrape all URLs from OPC guidance manifest."""
        print(f"\n{'=' * 60}")
        print("OPC GUIDANCE SCRAPER")
        print(f"{'=' * 60}")
        print(f"Manifest: {manifest_path}")
        print(f"Output: {self.output_dir}")
        print(f"Format: {output_format}")
        print(f"{'=' * 60}\n")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        documents = manifest.get("documents", [])
        total = len(documents)

        print(f"Found {total} OPC guidance documents\n")

        for i, doc in enumerate(documents, 1):
            title = doc.get("title", "Untitled")
            url = doc.get("source_url")
            filename_base = doc.get("filename", "").replace(".pdf", "")

            print(f"[{i}/{total}] {title}")
            print(f"  URL: {url}")

            if not url:
                print(f"  No source_url found")
                self.stats["skipped"] += 1
                continue

            # Check if already exists
            ext = "html" if output_format == "html" else "txt"
            output_file = self.output_dir / f"{filename_base}.{ext}"

            if output_file.exists():
                print(f"  Skipping (already exists)")
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
                print(f"  Last modified: {update_date}")

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
        print("1. Review files in:", self.output_dir)
        print("2. Run: python3 batch_ingest.py data/raw/opc_guidance_manifest.yaml")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape OPC HTML guidance pages from priv.gc.ca"
    )
    parser.add_argument("manifest", help="Path to opc_guidance_manifest.yaml")
    parser.add_argument(
        "--format",
        choices=["html", "text"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (default: data/raw/guidance/opc/{format})",
    )

    args = parser.parse_args()

    output_dir = args.output
    if output_dir is None:
        output_dir = f"data/raw/guidance/opc/{args.format}"

    scraper = OPCScraper(output_dir=output_dir)
    scraper.scrape_from_manifest(args.manifest, output_format=args.format)


if __name__ == "__main__":
    main()
