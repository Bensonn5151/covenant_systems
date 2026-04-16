import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_post_build_kg_construct_knowledge_graph_from_manifest():
    url = f"{BASE_URL}/build-kg"
    headers = {"Content-Type": "application/json"}

    # Test case: successful KG build with valid manifest
    valid_manifest_payload = {"manifest_path": "/manifests/manifest.yaml"}
    try:
        response = requests.post(url, json=valid_manifest_payload, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200 OK but got {response.status_code}"
        data = response.json()
        assert "nodes_count" in data and isinstance(data["nodes_count"], int), "nodes_count missing or invalid"
        assert "edges_count" in data and isinstance(data["edges_count"], int), "edges_count missing or invalid"
        assert data["nodes_count"] > 0, "nodes_count should be greater than 0"
        assert data["edges_count"] > 0, "edges_count should be greater than 0"
    except requests.RequestException as e:
        assert False, f"Request failed during valid manifest test: {e}"

    # Test case: error handling for corrupt manifest that causes KG build error
    corrupt_manifest_payload = {"manifest_path": "/manifests/corrupt_manifest.yaml"}
    try:
        response = requests.post(url, json=corrupt_manifest_payload, headers=headers, timeout=TIMEOUT)
        # Expecting a 500 error for corrupt manifest
        assert response.status_code == 500, f"Expected 500 KG build error but got {response.status_code}"
        # Optionally check for error message in response text or json
    except requests.RequestException as e:
        assert False, f"Request failed during corrupt manifest test: {e}"


test_post_build_kg_construct_knowledge_graph_from_manifest()
