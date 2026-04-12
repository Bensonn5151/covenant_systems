import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_knowledge_graph_building_from_manifest():
    manifest_good = "data/raw/manifest.yaml"
    manifest_corrupt = "data/raw/corrupt_manifest.yaml"

    url = f"{BASE_URL}/build-kg"
    headers = {"Content-Type": "application/json"}

    # Test successful KG build with valid manifest
    try:
        resp = requests.post(url, json={"manifest_path": manifest_good}, headers=headers, timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "nodes_count" in data and isinstance(data["nodes_count"], int), "Missing or invalid nodes_count"
        assert "edges_count" in data and isinstance(data["edges_count"], int), "Missing or invalid edges_count"
    except requests.RequestException as e:
        assert False, f"Request failed for valid manifest: {e}"

    # Test error handling with corrupt manifest causing KG build error
    try:
        resp = requests.post(url, json={"manifest_path": manifest_corrupt}, headers=headers, timeout=TIMEOUT)
        # Expecting 400 error due to manifest not found (server-side)
        assert resp.status_code == 400, f"Expected 400 error for corrupt manifest, got {resp.status_code}: {resp.text}"
    except requests.RequestException as e:
        assert False, f"Request failed for corrupt manifest: {e}"

test_knowledge_graph_building_from_manifest()
