import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}


def test_web_scraping_of_regulatory_content():
    scrape_url = f"{BASE_URL}/scrape"

    # Test successful scraping from configured sources: FINTRAC, OPC
    for source in ["FINTRAC", "OPC"]:
        try:
            response = requests.post(
                scrape_url,
                json={"source": source},
                headers=HEADERS,
                timeout=TIMEOUT,
            )
        except requests.RequestException as e:
            assert False, f"Request failed for source {source}: {e}"

        # Assert success status code
        assert response.status_code == 200, f"Expected 200 for source {source}, got {response.status_code}"

        data = response.json()

        # Validate response contains pages_scraped and files_saved
        assert isinstance(data, dict), f"Response is not a dict for source {source}"
        assert "pages_scraped" in data, f"'pages_scraped' missing in response for source {source}"
        assert isinstance(data["pages_scraped"], int) and data["pages_scraped"] > 0, f"Invalid 'pages_scraped' for source {source}"

        assert "files_saved" in data, f"'files_saved' missing in response for source {source}"
        assert isinstance(data["files_saved"], list), f"'files_saved' is not a list for source {source}"
        assert all(isinstance(f, str) and f for f in data["files_saved"]), f"'files_saved' list contains invalid entries for source {source}"

    # Test error handling for unsupported source
    unsupported_source = "unsupported_source"
    try:
        response = requests.post(
            scrape_url,
            json={"source": unsupported_source},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
    except requests.RequestException as e:
        assert False, f"Request failed for unsupported source: {e}"

    # Expecting a 500 error for unsupported source scraping error
    assert response.status_code == 500, f"Expected 500 for unsupported source, got {response.status_code}"

    error_data = response.json()
    # The response schema for error is "Scraping error"
    assert isinstance(error_data, dict), "Error response is not a dict"
    assert any("error" in k.lower() or "scraping" in k.lower() for k in error_data.keys()) or "scraping error" in str(error_data).lower(), \
        f"Expected scraping error indication in response for unsupported source, got: {error_data}"


test_web_scraping_of_regulatory_content()