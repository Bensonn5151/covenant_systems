import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_knowledge_graph_building_from_manifest():
    # Test successful KG build from valid manifest
    valid_manifest_payload = {"manifest_path": "/manifests/manifest.yaml"}
    build_kg_url = f"{BASE_URL}/build-kg"
    try:
        response = requests.post(build_kg_url, json=valid_manifest_payload, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200 OK but got {response.status_code}"
        json_resp = response.json()
        assert "nodes_count" in json_resp and isinstance(json_resp["nodes_count"], int), "Missing or invalid nodes_count"
        assert "edges_count" in json_resp and isinstance(json_resp["edges_count"], int), "Missing or invalid edges_count"
    except requests.RequestException as e:
        assert False, f"Request failed with exception: {e}"

    # Test error handling for corrupt manifest causing KG build error
    corrupt_manifest_payload = {"manifest_path": "/manifests/corrupt_manifest.yaml"}
    try:
        response = requests.post(build_kg_url, json=corrupt_manifest_payload, timeout=TIMEOUT)
        assert response.status_code == 500, f"Expected 500 error for corrupt manifest but got {response.status_code}"
    except requests.RequestException as e:
        assert False, f"Request failed with exception: {e}"

test_knowledge_graph_building_from_manifest()