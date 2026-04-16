import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_post_scrape_regulatory_content_from_specified_source():
    scrape_url = f"{BASE_URL}/scrape"
    headers = {
        "Content-Type": "application/json"
    }

    # Test with supported source "FINTRAC"
    fintrac_payload = {"source": "FINTRAC"}
    fintrac_response = requests.post(scrape_url, json=fintrac_payload, headers=headers, timeout=TIMEOUT)
    try:
        assert fintrac_response.status_code == 200, f"Expected status 200, got {fintrac_response.status_code}"
        data = fintrac_response.json()
        assert isinstance(data, dict), "Response JSON is not a dictionary"
        assert "pages_scraped" in data, "'pages_scraped' missing in response"
        assert isinstance(data["pages_scraped"], int) and data["pages_scraped"] >= 0, "'pages_scraped' is not a non-negative int"
        assert "files_saved" in data, "'files_saved' missing in response"
        assert isinstance(data["files_saved"], list), "'files_saved' is not a list"
        for file_path in data["files_saved"]:
            assert isinstance(file_path, str) and file_path.strip() != "", "Invalid file path in 'files_saved'"
    except Exception as e:
        raise AssertionError(f"FINTRAC scrape test failed: {e}")

    # Test with supported source "OPC"
    opc_payload = {"source": "OPC"}
    opc_response = requests.post(scrape_url, json=opc_payload, headers=headers, timeout=TIMEOUT)
    try:
        assert opc_response.status_code == 200, f"Expected status 200, got {opc_response.status_code}"
        data = opc_response.json()
        assert isinstance(data, dict), "Response JSON is not a dictionary"
        assert "pages_scraped" in data, "'pages_scraped' missing in response"
        assert isinstance(data["pages_scraped"], int) and data["pages_scraped"] >= 0, "'pages_scraped' is not a non-negative int"
        assert "files_saved" in data, "'files_saved' missing in response"
        assert isinstance(data["files_saved"], list), "'files_saved' is not a list"
        for file_path in data["files_saved"]:
            assert isinstance(file_path, str) and file_path.strip() != "", "Invalid file path in 'files_saved'"
    except Exception as e:
        raise AssertionError(f"OPC scrape test failed: {e}")

    # Test with unsupported source "unsupported_source"
    unsupported_payload = {"source": "unsupported_source"}
    unsupported_response = requests.post(scrape_url, json=unsupported_payload, headers=headers, timeout=TIMEOUT)
    try:
        assert unsupported_response.status_code == 500, f"Expected status 500 for unsupported source, got {unsupported_response.status_code}"
        # Optional: check error message contains 'Scraping error'
        error_text = unsupported_response.text.lower()
        assert "scraping error" in error_text or "error" in error_text, "Error message does not indicate scraping error"
    except Exception as e:
        raise AssertionError(f"Unsupported source scrape test failed: {e}")

test_post_scrape_regulatory_content_from_specified_source()
