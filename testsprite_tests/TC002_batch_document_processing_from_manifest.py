import requests
import json

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_batch_document_processing_from_manifest():
    headers = {"Content-Type": "application/json"}

    # Test with a valid manifest path that exists and includes real PDFs
    valid_manifest_path = "data/raw/manifest.yaml"
    valid_payload = {"manifest_path": valid_manifest_path}

    try:
        # POST /batch-ingest with valid manifest
        response = requests.post(f"{BASE_URL}/batch-ingest", headers=headers, json=valid_payload, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /batch-ingest with valid manifest failed: {e}"

    assert response.status_code == 200, f"Expected 200 OK but got {response.status_code}"
    try:
        data = response.json()
    except json.JSONDecodeError:
        assert False, "Response is not valid JSON"

    assert "processed_count" in data and isinstance(data["processed_count"], int), "Missing or invalid processed_count"
    assert "failed_count" in data and isinstance(data["failed_count"], int), "Missing or invalid failed_count"
    assert "results" in data and isinstance(data["results"], list), "Missing or invalid results list"

    # Each result should have document_id and status keys, status should be 'processed', 'failed' or 'queued'
    for doc_result in data["results"]:
        assert "document_id" in doc_result and isinstance(doc_result["document_id"], str), "Missing or invalid document_id in result"
        assert "status" in doc_result and doc_result["status"] in {"processed", "failed", "queued"}, f"Invalid status value: {doc_result.get('status')}"

    # Test error handling with a manifest that contains missing files or causes pipeline errors
    error_manifest_path = "data/raw/manifest_with_missing_file.yaml"
    error_payload = {"manifest_path": error_manifest_path}

    try:
        error_response = requests.post(f"{BASE_URL}/batch-ingest", headers=headers, json=error_payload, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /batch-ingest with error manifest failed: {e}"

    # Expect a 400 error due to invalid PDF or missing parameters as per PRD user flow
    assert error_response.status_code == 400, f"Expected 400 Invalid PDF or missing parameters but got {error_response.status_code}"

    # Optionally verify error message in response body
    try:
        error_data = error_response.json()
        # The specification doesn't detail error response body, so no strict assertion here
    except json.JSONDecodeError:
        # It's acceptable if no JSON content on error
        pass


test_batch_document_processing_from_manifest()
