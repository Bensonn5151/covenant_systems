import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_legislation_discovery_and_download():
    headers = {"Content-Type": "application/json"}

    # Test successful discovery with act name "Privacy Act"
    payload_success = {"acts": ["Privacy Act"]}
    try:
        response = requests.post(
            f"{BASE_URL}/discover",
            json=payload_success,
            headers=headers,
            timeout=TIMEOUT,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # Validate discovered_count is 1
        assert "discovered_count" in data, "discovered_count missing in response"
        assert data["discovered_count"] == 1, f"Expected discovered_count 1, got {data['discovered_count']}"
        # Validate manifest_entries list present and has at least one entry
        assert "manifest_entries" in data, "manifest_entries missing in response"
        assert isinstance(data["manifest_entries"], list), "manifest_entries is not a list"
        assert len(data["manifest_entries"]) >= 1, "manifest_entries list is empty"

        # Check each manifest entry has act, source_url, and saved_path keys with non-empty string values
        for entry in data["manifest_entries"]:
            assert isinstance(entry.get("act"), str) and entry["act"], "Invalid or missing act in manifest entry"
            assert isinstance(entry.get("source_url"), str) and entry["source_url"].startswith("https://"), \
                "Invalid or missing source_url in manifest entry"
            assert isinstance(entry.get("saved_path"), str) and entry["saved_path"], "Invalid or missing saved_path in manifest entry"

    except (requests.RequestException, AssertionError) as e:
        raise AssertionError(f"Failed success discovery test: {e}")

    # Test handling of nonexistent act returns 404
    payload_not_found = {"acts": ["nonexistent-act"]}
    try:
        response = requests.post(
            f"{BASE_URL}/discover",
            json=payload_not_found,
            headers=headers,
            timeout=TIMEOUT,
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        # Optionally check the response body for the error message
        try:
            data = response.json()
            assert ("Act not found" in str(data) or "act not found" in str(data).lower()), \
                "Error message does not mention 'Act not found'"
        except Exception:
            # If response is not JSON or no message, just pass
            pass
    except requests.RequestException as e:
        raise AssertionError(f"Failed 404 act not found test: {e}")

test_legislation_discovery_and_download()