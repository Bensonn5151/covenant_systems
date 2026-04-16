import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_regulations_api_lists_all_regulations_with_classification_and_severity():
    url = f"{BASE_URL}/api/regulations"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not in JSON format"

    assert "regulations" in data, "'regulations' key not in response JSON"
    assert isinstance(data["regulations"], list), "'regulations' is not a list"

    expected_fields = {
        "id",
        "document_type",
        "jurisdiction",
        "regulator",
        "total_sections",
        "obligations_count",
        "prohibitions_count",
        "definitions_count",
        "severity_signal_breakdown"
    }

    for regulation in data["regulations"]:
        assert isinstance(regulation, dict), "Each regulation should be a dictionary"
        missing_fields = expected_fields - regulation.keys()
        assert not missing_fields, f"Regulation is missing fields: {missing_fields}"

        # Validate types for some fields
        assert isinstance(regulation["id"], str), "id should be a string"
        assert isinstance(regulation["document_type"], str), "document_type should be a string"
        assert isinstance(regulation["jurisdiction"], str), "jurisdiction should be a string"
        assert isinstance(regulation["regulator"], str), "regulator should be a string"
        assert isinstance(regulation["total_sections"], int), "total_sections should be an integer"
        assert isinstance(regulation["obligations_count"], int), "obligations_count should be an integer"
        assert isinstance(regulation["prohibitions_count"], int), "prohibitions_count should be an integer"
        assert isinstance(regulation["definitions_count"], int), "definitions_count should be an integer"
        assert isinstance(regulation["severity_signal_breakdown"], dict), "severity_signal_breakdown should be a dictionary"

test_regulations_api_lists_all_regulations_with_classification_and_severity()