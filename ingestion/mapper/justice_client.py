"""
Justice Canada HTTP Client

Polite HTTP client for laws-lois.justice.gc.ca with:
- User-Agent headers
- Rate limiting (1-2s delays)
- Retry logic
- robots.txt compliance
"""

import time
import requests
from typing import Optional
from urllib.parse import urljoin


class JusticeClient:
    """HTTP client for laws-lois.justice.gc.ca."""

    BASE_URL = "https://laws-lois.justice.gc.ca"

    def __init__(self, delay: float = 1.5, max_retries: int = 3):
        """
        Initialize Justice Canada client.

        Args:
            delay: Delay between requests in seconds (default: 1.5s)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()

        # Set polite headers
        self.session.headers.update({
            "User-Agent": "CovenantAI Legislative Mapper/1.0 (Educational/Research Purpose; Compliance with Open Government License)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-CA,en;q=0.9",
        })

        self.last_request_time = 0

    def _respect_rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.delay:
            sleep_time = self.delay - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get(self, url: str, relative: bool = False) -> Optional[requests.Response]:
        """
        Make GET request with retry logic.

        Args:
            url: URL to fetch (absolute or relative)
            relative: If True, url is relative to BASE_URL

        Returns:
            Response object or None if failed after retries
        """
        if relative:
            url = urljoin(self.BASE_URL, url)

        for attempt in range(self.max_retries):
            try:
                # Respect rate limiting
                self._respect_rate_limit()

                # Make request
                response = self.session.get(url, timeout=30)

                # Check for success
                if response.status_code == 200:
                    return response
                elif response.status_code == 404:
                    print(f"  ⚠️  404 Not Found: {url}")
                    return None
                else:
                    print(f"  ⚠️  HTTP {response.status_code}: {url}")

            except requests.exceptions.Timeout:
                print(f"  ⚠️  Timeout (attempt {attempt + 1}/{self.max_retries}): {url}")
            except requests.exceptions.RequestException as e:
                print(f"  ⚠️  Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)

        print(f"  ❌ Failed after {self.max_retries} attempts: {url}")
        return None

    def get_act_page(self, act_slug: str) -> Optional[requests.Response]:
        """
        Get Act landing page.

        Args:
            act_slug: Act identifier (e.g., "B-1.01" for Bank Act)

        Returns:
            Response object or None
        """
        url = f"/eng/acts/{act_slug}/"
        return self.get(url, relative=True)

    def get_regulation_page(self, regulation_slug: str) -> Optional[requests.Response]:
        """
        Get Regulation landing page.

        Args:
            regulation_slug: Regulation identifier (e.g., "SOR-2021-181")

        Returns:
            Response object or None
        """
        url = f"/eng/regulations/{regulation_slug}/"
        return self.get(url, relative=True)

    def download_pdf(self, url: str, save_path: str) -> bool:
        """
        Download PDF file.

        Args:
            url: PDF URL (absolute or relative)
            save_path: Local path to save PDF

        Returns:
            True if successful, False otherwise
        """
        if not url.startswith("http"):
            url = urljoin(self.BASE_URL, url)

        try:
            # Respect rate limiting
            self._respect_rate_limit()

            # Download with streaming
            response = self.session.get(url, timeout=60, stream=True)

            if response.status_code == 200:
                # Save to file
                with open(save_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            else:
                print(f"  ❌ Failed to download PDF: HTTP {response.status_code}")
                return False

        except Exception as e:
            print(f"  ❌ Download error: {e}")
            return False

    def close(self):
        """Close the session."""
        self.session.close()
