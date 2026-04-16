import requests
import json

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_post_batch_ingest_process_multiple_documents_from_manifest():
    # Valid manifest test
    valid_manifest_path = "/manifests/manifest.yaml"
    url = f"{BASE_URL}/batch-ingest"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {"manifest_path": valid_manifest_path}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"HTTP request failed: {e}"

    # Validate success response
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    try:
        data = response.json()
    except json.JSONDecodeError:
        assert False, "Response is not valid JSON"

    # Validate keys in response
    assert isinstance(data, dict), "Response JSON root is not a dictionary"
    assert "processed_count" in data, "processed_count missing in response"
    assert "failed_count" in data, "failed_count missing in response"
    assert "results" in data, "results missing in response"
    assert isinstance(data["results"], list), "results is not a list"
    # Each result should be a dict with document_id and status keys
    for result in data["results"]:
        assert isinstance(result, dict), "Each result should be a dict"
        assert "document_id" in result, "document_id missing in per-document result"
        assert "status" in result, "status missing in per-document result"
        # status should be string and one of expected values (processed or failure)
        assert isinstance(result["status"], str), "status is not a string"

    # Validate counts are numeric and coherent
    processed_count = data["processed_count"]
    failed_count = data["failed_count"]
    assert isinstance(processed_count, int) and processed_count >= 0, "processed_count not a non-negative int"
    assert isinstance(failed_count, int) and failed_count >= 0, "failed_count not a non-negative int"
    assert processed_count + failed_count == len(data["results"]), "Sum of processed and failed counts must equal results length"

    # Error handling: manifest with missing files or pipeline errors should produce 500
    error_manifest_path = "/manifests/manifest_with_missing_file.yaml"
    error_payload = {"manifest_path": error_manifest_path}

    try:
        error_response = requests.post(url, headers=headers, json=error_payload, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"HTTP request failed for error test: {e}"

    # Should return HTTP 500 for pipeline error
    assert error_response.status_code == 500, f"Expected 500 but got {error_response.status_code} for error manifest"

    # Response content (optional) check for error message
    try:
        error_data = error_response.json()
    except json.JSONDecodeError:
        # Sometimes error responses may not be JSON, skip JSON validation in that case
        error_data = None

    if error_data:
        # if error_data is dict, check message
        assert any("error" in k.lower() or "message" in k.lower() for k in error_data), "Error response missing error message key"

test_post_batch_ingest_process_multiple_documents_from_manifest()