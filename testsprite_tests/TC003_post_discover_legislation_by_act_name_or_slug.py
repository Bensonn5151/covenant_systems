import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_post_discover_legislation_by_act_name_or_slug():
    url = f"{BASE_URL}/discover"
    headers = {"Content-Type": "application/json"}

    # Test Case 1: Act found (success case)
    payload_found = {"acts": ["bank-act"]}
    try:
        response = requests.post(url, json=payload_found, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed for existing act: {e}"

    assert response.status_code == 200, f"Expected 200 OK for existing act, got {response.status_code}"
    data = response.json()
    assert "discovered_count" in data and isinstance(data["discovered_count"], int), "Missing or invalid 'discovered_count'"
    assert data["discovered_count"] > 0, "discovered_count should be greater than 0 when acts found"
    assert "manifest_entries" in data and isinstance(data["manifest_entries"], list), "Missing or invalid 'manifest_entries'"
    assert all(
        all(key in entry for key in ("act", "source_url", "saved_path"))
        for entry in data["manifest_entries"]
    ), "Each manifest entry must have 'act', 'source_url', and 'saved_path'"

    # Test Case 2: Act not found (404 case)
    payload_not_found = {"acts": ["nonexistent-act"]}
    try:
        response_not_found = requests.post(url, json=payload_not_found, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed for nonexistent act: {e}"

    assert response_not_found.status_code == 404, f"Expected 404 Not Found for nonexistent act, got {response_not_found.status_code}"
    # Response body may contain error message "Act not found"
    try:
        error_response = response_not_found.json()
        if isinstance(error_response, dict):
            # Check if error message indicative of not found
            error_messages = [str(v).lower() for v in error_response.values()]
            assert any("not found" in msg for msg in error_messages), "404 response must contain 'not found' message"
    except ValueError:
        # Response is not JSON, that's acceptable but no content check
        pass

test_post_discover_legislation_by_act_name_or_slug()