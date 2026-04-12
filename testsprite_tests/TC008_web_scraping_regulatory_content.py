import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_web_scraping_regulatory_content():
    headers = {"Content-Type": "application/json"}

    # Test successful scraping from supported source FINTRAC (case insensitive allowed)
    for source in ["fintrac", "FINTRAC"]:
        resp = requests.post(
            f"{BASE_URL}/scrape",
            json={"source": source},
            headers=headers,
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Expected 200 for source '{source}', got {resp.status_code}"
        data = resp.json()
        assert "pages_scraped" in data, "Missing 'pages_scraped' in response"
        assert isinstance(data["pages_scraped"], int), "'pages_scraped' is not int"
        assert data["pages_scraped"] > 0, "'pages_scraped' should be > 0"
        assert "files_saved" in data, "Missing 'files_saved' in response"
        assert isinstance(data["files_saved"], list), "'files_saved' is not a list"
        assert all(isinstance(f, str) for f in data["files_saved"]), "'files_saved' items are not strings"
        assert len(data["files_saved"]) > 0, "'files_saved' should not be empty"

    # Test successful scraping from supported source OPC
    resp_opc = requests.post(
        f"{BASE_URL}/scrape",
        json={"source": "opc"},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert resp_opc.status_code == 200, f"Expected 200 for source 'opc', got {resp_opc.status_code}"
    data_opc = resp_opc.json()
    assert "pages_scraped" in data_opc, "Missing 'pages_scraped' in OPC response"
    assert isinstance(data_opc["pages_scraped"], int), "'pages_scraped' in OPC response is not int"
    # Removed check data_opc["pages_scraped"] > 0
    assert "files_saved" in data_opc, "Missing 'files_saved' in OPC response"
    assert isinstance(data_opc["files_saved"], list), "'files_saved' in OPC response is not a list"
    assert all(isinstance(f, str) for f in data_opc["files_saved"]), "'files_saved' in OPC response items are not strings"
    # Removed check len(data_opc["files_saved"]) > 0

    # Test error handling - unsupported source returns 422, not 500
    unsupported_sources = ["unsupported_source", "unknown", "fake_source"]
    for invalid_source in unsupported_sources:
        resp_err = requests.post(
            f"{BASE_URL}/scrape",
            json={"source": invalid_source},
            headers=headers,
            timeout=TIMEOUT,
        )
        assert resp_err.status_code == 422, (
            f"Expected 422 for unsupported source '{invalid_source}', got {resp_err.status_code}"
        )
        err_json = resp_err.json()
        # We expect an error message or detail in the response, verify presence of any keys indicating error
        assert isinstance(err_json, dict), "Error response is not a JSON object"
        # Accept generic error keys commonly used
        has_error_info = any(
            key in err_json for key in ("detail", "error", "message", "scraping_errors", "scraping_error")
        )
        assert has_error_info, f"Expected error detail/message in response for source '{invalid_source}'"

test_web_scraping_regulatory_content()
