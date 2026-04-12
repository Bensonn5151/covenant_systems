import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_legislation_discovery_and_download():
    headers = {"Content-Type": "application/json"}

    # Test successful discovery of an existing act "bank-act"
    payload_existing = {"acts": ["bank-act"]}
    try:
        response = requests.post(f"{BASE_URL}/discover", json=payload_existing, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "discovered_count" in data, "discovered_count missing in response"
        assert data["discovered_count"] >= 1, f"Expected discovered_count >= 1, got {data['discovered_count']}"
        assert "manifest_entries" in data, "manifest_entries missing in response"
        assert isinstance(data["manifest_entries"], list), "manifest_entries is not a list"
        assert len(data["manifest_entries"]) == data["discovered_count"], \
            f"Expected manifest_entries length {data['discovered_count']}, got {len(data['manifest_entries'])}"
        entry = data["manifest_entries"][0]
        assert "act" in entry and entry["act"] == "bank-act", f"Expected act 'bank-act', got {entry.get('act')}"
        assert "source_url" in entry and isinstance(entry["source_url"], str) and entry["source_url"].startswith("http"), \
            "source_url missing or invalid"
        assert "saved_path" in entry and entry["saved_path"].endswith("bank_act.pdf"), \
            "saved_path missing or does not end with 'bank_act.pdf'"
    except requests.exceptions.RequestException as e:
        assert False, f"Request failed for existing act: {e}"

    # Test discovery of a nonexistent act returns 404
    payload_nonexistent = {"acts": ["nonexistent-act"]}
    try:
        response = requests.post(f"{BASE_URL}/discover", json=payload_nonexistent, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 404, f"Expected 404 for nonexistent act, got {response.status_code}"
        try:
            data = response.json()
            # Optionally assert error message present
            assert "Act not found" in str(data) or "error" in data, "Expected 'Act not found' error message"
        except Exception:
            # If no JSON, pass since 404 is confirmed
            pass
    except requests.exceptions.RequestException as e:
        assert False, f"Request failed for nonexistent act: {e}"

test_legislation_discovery_and_download()
