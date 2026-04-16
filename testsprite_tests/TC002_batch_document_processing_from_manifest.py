import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_batch_document_processing_from_manifest():
    url = f"{BASE_URL}/batch-ingest"
    headers = {"Content-Type": "application/json"}

    # Test case 1: Valid manifest processing
    valid_payload = {"manifest_path": "/manifests/manifest.yaml"}
    try:
        valid_response = requests.post(url, json=valid_payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /batch-ingest with valid manifest failed: {e}"

    assert valid_response.status_code == 200, f"Expected 200 OK, got {valid_response.status_code}"
    try:
        data = valid_response.json()
    except Exception as e:
        assert False, f"Response JSON parsing failed: {e}"

    assert "processed_count" in data and isinstance(data["processed_count"], int), "Missing or invalid processed_count"
    assert "failed_count" in data and isinstance(data["failed_count"], int), "Missing or invalid failed_count"
    assert "results" in data and isinstance(data["results"], list), "Missing or invalid results list"

    # Each result should have document_id and status
    for result in data["results"]:
        assert "document_id" in result and isinstance(result["document_id"], str), "Result missing document_id"
        assert "status" in result and isinstance(result["status"], str), "Result missing status"
        # Status should be processed or failed or similar valid status strings
        assert result["status"] in ["processed", "failed", "error", "skipped"], f"Unexpected status value: {result['status']}"

    # Test case 2: Manifest with missing file causing pipeline error
    error_payload = {"manifest_path": "/manifests/manifest_with_missing_file.yaml"}
    try:
        error_response = requests.post(url, json=error_payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /batch-ingest with error manifest failed: {e}"

    assert error_response.status_code == 500, f"Expected 500 Pipeline processing error, got {error_response.status_code}"


test_batch_document_processing_from_manifest()