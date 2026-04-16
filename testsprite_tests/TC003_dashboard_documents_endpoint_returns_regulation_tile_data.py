import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_dashboard_documents_endpoint_returns_regulation_tile_data():
    url = f"{BASE_URL}/api/dashboard/documents"
    headers = {
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"HTTP request failed: {e}"

    # Validate response status code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # Validate top-level keys
    assert isinstance(data, dict), "Response JSON is not an object"
    assert "documents" in data, "Missing 'documents' key in response"
    assert "total" in data, "Missing 'total' key in response"

    documents = data["documents"]
    total = data["total"]

    assert isinstance(documents, list), "'documents' should be a list"
    assert isinstance(total, int), "'total' should be an integer"
    assert total == len(documents), "'total' does not match length of 'documents' array"
    assert total > 0, "'documents' array is empty"

    # Check required fields in each document item
    required_fields = [
        "document_id",
        "document_type",
        "jurisdiction",
        "regulator",
        "section_count",
        "classification_breakdown",
        "severity_signal_breakdown"
    ]

    for doc in documents:
        assert isinstance(doc, dict), "Each document item should be an object"
        for field in required_fields:
            assert field in doc, f"Document missing required field: {field}"

        # Validate types of fields where reasonable
        assert isinstance(doc["document_id"], str), "document_id should be a string"
        assert isinstance(doc["document_type"], str), "document_type should be a string"
        assert isinstance(doc["jurisdiction"], str), "jurisdiction should be a string"
        assert isinstance(doc["regulator"], str), "regulator should be a string"
        assert isinstance(doc["section_count"], int), "section_count should be an integer"
        assert isinstance(doc["classification_breakdown"], dict), "classification_breakdown should be an object/dict"
        assert isinstance(doc["severity_signal_breakdown"], dict), "severity_signal_breakdown should be an object/dict"


test_dashboard_documents_endpoint_returns_regulation_tile_data()