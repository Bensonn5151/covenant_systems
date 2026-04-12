import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_batch_document_processing_from_manifest():
    url = f"{BASE_URL}/batch-ingest"
    headers = {"Content-Type": "application/json"}

    # Test successful batch ingest with a valid manifest
    valid_payload = {
        "manifest_path": "data/raw/manifest.yaml"
    }

    response = requests.post(url, json=valid_payload, headers=headers, timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200 OK but got {response.status_code}"
    data = response.json()

    assert "processed_count" in data, "Response missing processed_count"
    assert "failed_count" in data, "Response missing failed_count"
    assert "results" in data and isinstance(data["results"], list), "Response missing or invalid results list"

    # Validate processed_count and failed_count sensible according to result entries
    processed_count = data["processed_count"]
    failed_count = data["failed_count"]
    results = data["results"]

    assert processed_count >= 0, "processed_count should be non-negative"
    assert failed_count >= 0, "failed_count should be non-negative"
    assert processed_count + failed_count == len(results), "Sum of processed_count and failed_count must equal results length"

    for result in results:
        assert "document_id" in result, "Result missing document_id"
        assert "status" in result, "Result missing status"
        assert result["status"] == "processed", f"Each document status expected to be 'processed', got {result['status']}"
        assert "title" in result, "Result missing title"

    # Test error handling with manifest that contains missing files or causes pipeline errors
    # According to PRD, bad manifest returns 400 or 500 (pipeline processing error)
    # Testing with a known corrupt manifest path
    bad_payload = {
        "manifest_path": "data/raw/manifest_with_missing_file.yaml"
    }

    response_bad = requests.post(url, json=bad_payload, headers=headers, timeout=TIMEOUT)
    # The PRD mentions 500 Pipeline processing error for missing files in manifest, test accordingly
    assert response_bad.status_code in (400, 500), f"Expected 400 or 500 error but got {response_bad.status_code}"

test_batch_document_processing_from_manifest()