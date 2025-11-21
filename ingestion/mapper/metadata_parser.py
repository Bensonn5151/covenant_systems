"""
Metadata Parser for Justice Canada Pages

Extracts metadata from HTML pages based on actual structure from laws-lois.justice.gc.ca.

Example structure from real page:
    Title: "Canada Occupational Health and Safety Regulations (SOR/86-304)"
    "Regulations are current to 2025-10-28 and last amended on 2025-03-26"
    "Enabling Act: CANADA LABOUR CODE"
"""

from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re


class MetadataParser:
    """Parses HTML pages from laws-lois.justice.gc.ca."""

    @staticmethod
    def parse_regulation_page(html: str) -> Dict:
        """
        Parse Regulation landing page to extract metadata.

        Real example from SOR-86-304:
            Title: "Canada Occupational Health and Safety Regulations (SOR/86-304)"
            Current to: "2025-10-28"
            Last amended: "2025-03-26"
            Enabling Act: "CANADA LABOUR CODE"

        Args:
            html: HTML content of Regulation page

        Returns:
            Dict with metadata including enabling acts
        """
        soup = BeautifulSoup(html, "html.parser")

        metadata = {
            "title": None,
            "citation": None,
            "current_to": None,
            "last_amended": None,
            "enabling_acts": [],
            "pdf_url": None,
        }

        # Extract title (h1 with id="wb-cont")
        title_elem = soup.find("h1", {"id": "wb-cont"})
        if title_elem:
            full_title = title_elem.get_text(strip=True)
            metadata["title"] = full_title

            # Extract citation from title (format: "Title (SOR/YYYY-NNN)")
            citation_match = re.search(r"\((SOR/[\d-]+|CRC/c\.\s*\d+)\)", full_title)
            if citation_match:
                metadata["citation"] = citation_match.group(1)
            else:
                # Try to extract from page text
                citation_match = re.search(r"(SOR/[\d-]+|CRC/c\.\s*\d+)", html)
                if citation_match:
                    metadata["citation"] = citation_match.group(1)

        # Extract "current to" and "last amended" dates
        # Format: "Regulations are current to 2025-10-28 and last amended on 2025-03-26"
        date_text = soup.find(string=re.compile(r"current to.*last amended", re.IGNORECASE))
        if date_text:
            # Extract "current to" date
            current_match = re.search(r"current to (\d{4}-\d{2}-\d{2})", date_text, re.IGNORECASE)
            if current_match:
                metadata["current_to"] = current_match.group(1)

            # Extract "last amended" date
            amended_match = re.search(r"last amended on (\d{4}-\d{2}-\d{2})", date_text, re.IGNORECASE)
            if amended_match:
                metadata["last_amended"] = amended_match.group(1)

        # Extract enabling act
        # Format: "Enabling Act: CANADA LABOUR CODE"
        enabling_text = soup.find(string=re.compile(r"Enabling Act:", re.IGNORECASE))
        if enabling_text:
            # Get the text after "Enabling Act:"
            match = re.search(r"Enabling Act:\s*(.+?)(?:\n|$)", enabling_text.parent.get_text(), re.IGNORECASE)
            if match:
                act_name = match.group(1).strip()
                metadata["enabling_acts"].append(act_name)

        # Extract PDF URL
        # Strategy 1: Look for any link ending in .pdf
        pdf_link = soup.find("a", href=re.compile(r"\.pdf$", re.IGNORECASE))
        
        if pdf_link:
            metadata["pdf_url"] = pdf_link.get("href")
        else:
            # Strategy 2: Fallback - Construct URL from ID if possible
            # Example: /eng/acts/A-1/A-1.pdf
            # We need the ID from the URL or citation to do this effectively, 
            # but here we only have HTML. The caller (JusticeClient) handles URL construction better.
            pass

        return metadata

    @staticmethod
    def parse_act_page(html: str) -> Dict:
        """
        Parse Act landing page to extract metadata and related regulations.

        Real example from A-1:
            Title: "Access to Information Act (R.S.C., 1985, c. A-1)"
            "Act current to 2025-10-28 and last amended on 2025-06-02"

        Args:
            html: HTML content of Act page

        Returns:
            Dict with metadata and list of related regulation slugs
        """
        soup = BeautifulSoup(html, "html.parser")

        metadata = {
            "title": None,
            "citation": None,
            "current_to": None,
            "last_amended": None,
            "related_regulations": [],
            "pdf_url": None,
        }

        # Extract title (h1 with id="wb-cont")
        title_elem = soup.find("h1", {"id": "wb-cont"})
        if title_elem:
            full_title = title_elem.get_text(strip=True)
            metadata["title"] = full_title

            # Extract citation from title
            # Formats: "(R.S.C., 1985, c. A-1)" or "(S.C. 2023, c. 26)"
            citation_match = re.search(r"\((R\.S\.C\.,\s*\d{4},\s*c\.\s*[A-Z]-?\d+|S\.C\.\s*\d{4},\s*c\.\s*\d+)\)", full_title)
            if citation_match:
                metadata["citation"] = citation_match.group(1)

        # Extract "current to" and "last amended" dates
        # Format: "Act current to 2025-10-28 and last amended on 2025-06-02"
        date_text = soup.find(string=re.compile(r"Act current to.*last amended", re.IGNORECASE))
        if date_text:
            # Extract "current to" date
            current_match = re.search(r"current to (\d{4}-\d{2}-\d{2})", date_text, re.IGNORECASE)
            if current_match:
                metadata["current_to"] = current_match.group(1)

            # Extract "last amended" date
            amended_match = re.search(r"last amended on (\d{4}-\d{2}-\d{2})", date_text, re.IGNORECASE)
            if amended_match:
                metadata["last_amended"] = amended_match.group(1)

        # Extract related regulations
        # Look for links to regulations pages
        regulation_links = soup.find_all("a", href=re.compile(r"/eng/regulations/[^/]+/?$"))
        for link in regulation_links:
            href = link.get("href", "")
            # Extract regulation slug (e.g., "SOR-2021-181")
            match = re.search(r"/eng/regulations/([^/]+)", href)
            if match:
                reg_slug = match.group(1)
                if reg_slug not in metadata["related_regulations"]:
                    metadata["related_regulations"].append(reg_slug)

        # Extract PDF URL
        # Strategy 1: Look for any link ending in .pdf
        pdf_link = soup.find("a", href=re.compile(r"\.pdf$", re.IGNORECASE))
        
        if pdf_link:
            metadata["pdf_url"] = pdf_link.get("href")
        
        return metadata

    @staticmethod
    def sanitize_filename(title: str, citation: str) -> str:
        """
        Create safe filename from title and citation.

        Format: "SOR-86-304 - Canada Occupational Health and Safety Regulations.pdf"

        Args:
            title: Document title
            citation: Citation (e.g., "SOR/86-304")

        Returns:
            Sanitized filename
        """
        # Remove citation from title if present
        clean_title = re.sub(r"\([^)]+\)$", "", title).strip()

        # Normalize citation (replace / with -)
        clean_citation = citation.replace("/", "-")

        # Combine
        filename = f"{clean_citation} - {clean_title}.pdf"

        # Remove invalid filename characters
        filename = re.sub(r'[<>:"/\\|?*]', "", filename)

        # Limit length
        if len(filename) > 200:
            clean_title = clean_title[:150]
            filename = f"{clean_citation} - {clean_title}.pdf"

        return filename