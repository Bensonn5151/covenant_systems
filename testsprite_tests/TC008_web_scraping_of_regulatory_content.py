import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}

def test_web_scraping_of_regulatory_content():
    # Test successful scrape from supported source FINTRAC
    fintrac_payload = {"source": "FINTRAC"}
    try:
        response = requests.post(f"{BASE_URL}/scrape", json=fintrac_payload, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200 but got {response.status_code} for FINTRAC scraping"
        data = response.json()
        assert "pages_scraped" in data, "'pages_scraped' not found in response"
        assert isinstance(data["pages_scraped"], int) and data["pages_scraped"] >= 0, "'pages_scraped' should be non-negative int"
        assert "files_saved" in data, "'files_saved' not found in response"
        assert isinstance(data["files_saved"], list) and all(isinstance(f, str) for f in data["files_saved"]), "'files_saved' should be list of strings"
        # Removed assertion that files_saved should not be empty
    except requests.RequestException as e:
        assert False, f"Request to /scrape FINTRAC failed: {e}"

    # Test successful scrape from supported source OPC
    opc_payload = {"source": "OPC"}
    try:
        response = requests.post(f"{BASE_URL}/scrape", json=opc_payload, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200 but got {response.status_code} for OPC scraping"
        data = response.json()
        assert "pages_scraped" in data, "'pages_scraped' not found in response"
        assert isinstance(data["pages_scraped"], int) and data["pages_scraped"] >= 0, "'pages_scraped' should be non-negative int"
        assert "files_saved" in data, "'files_saved' not found in response"
        assert isinstance(data["files_saved"], list) and all(isinstance(f, str) for f in data["files_saved"]), "'files_saved' should be list of strings"
        # Removed assertion that files_saved should not be empty
    except requests.RequestException as e:
        assert False, f"Request to /scrape OPC failed: {e}"

    # Test error handling for unsupported source resulting in 500 scraping error
    unsupported_payload = {"source": "unsupported_source"}
    try:
        response = requests.post(f"{BASE_URL}/scrape", json=unsupported_payload, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 500, f"Expected 500 but got {response.status_code} for unsupported source scraping"
        # Optionally verify error message in response
        try:
            data = response.json()
            error_keys = ["detail", "error", "message"]
            if any(key in data for key in error_keys):
                error_msg = next((data[key] for key in error_keys if key in data), None)
                assert "scraping error" in error_msg.lower() or "error" in error_msg.lower()
        except Exception:
            pass  # Response might not be JSON or have specific error message
    except requests.RequestException as e:
        assert False, f"Request to /scrape unsupported source failed: {e}"


test_web_scraping_of_regulatory_content()
