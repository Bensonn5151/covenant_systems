import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}


def test_legislation_discovery_and_download():
    # Test successful discovery of a known act "bank-act"
    url = f"{BASE_URL}/discover"
    payload = {"acts": ["bank-act"]}

    try:
        response = requests.post(url, json=payload, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    # Validate success response
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    assert "discovered_count" in data and isinstance(data["discovered_count"], int) and data["discovered_count"] > 0
    assert "manifest_entries" in data and isinstance(data["manifest_entries"], list) and len(data["manifest_entries"]) > 0
    for entry in data["manifest_entries"]:
        assert "act" in entry and entry["act"] == "bank-act"
        assert "source_url" in entry and entry["source_url"].startswith("https://")
        assert "saved_path" in entry and entry["saved_path"].startswith("/data/regulations/raw/")

    # Test discovery with a nonexistent act, expect 404 error
    payload_nonexistent = {"acts": ["nonexistent-act"]}
    try:
        response_nonexistent = requests.post(url, json=payload_nonexistent, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    assert response_nonexistent.status_code == 404, f"Expected 404 but got {response_nonexistent.status_code}"
    try:
        error_data = response_nonexistent.json()
    except ValueError:
        # Sometimes error details might not be JSON, so just pass if JSON decode fails
        error_data = None

    # If error_data exists, try to check for error message containing "not found"
    if error_data and isinstance(error_data, dict):
        msg = error_data.get("detail") or error_data.get("message") or ""
        assert "not found" in msg.lower() or "not found" in str(error_data).lower()


test_legislation_discovery_and_download()