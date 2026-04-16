import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_dashboard_document_detail_returns_section_level_information_or_404():
    valid_document_id = "pipeda"
    invalid_document_id = "unknown-reg"

    # Test valid document_id returns 200 with section-level details
    url_valid = f"{BASE_URL}/api/dashboard/documents/{valid_document_id}"
    try:
        resp_valid = requests.get(url_valid, timeout=TIMEOUT)
        assert resp_valid.status_code == 200, f"Expected 200 for valid document_id but got {resp_valid.status_code}"
        data_valid = resp_valid.json()

        # Validate top-level keys
        assert "document_id" in data_valid, "Missing 'document_id' in response"
        assert data_valid["document_id"] == valid_document_id, f"Expected document_id '{valid_document_id}', got '{data_valid['document_id']}'"
        assert "sections" in data_valid, "Missing 'sections' in response"
        assert isinstance(data_valid["sections"], list), "'sections' should be a list"
        assert "total_sections" in data_valid, "Missing 'total_sections' in response"
        assert isinstance(data_valid["total_sections"], int) and data_valid["total_sections"] >= 0, "'total_sections' should be a non-negative integer"

        # Validate structure of sections if any
        for section in data_valid["sections"]:
            assert isinstance(section, dict), "Each section should be a dict"
            assert "section_id" in section, "Each section must have 'section_id'"
            assert "title" in section, "Each section must have 'title'"
            assert "body" in section, "Each section must have 'body'"
            assert "classification" in section, "Each section must have 'classification'"
            assert "severity_signal" in section, "Each section must have 'severity_signal'"
            assert "operational_areas" in section, "Each section must have 'operational_areas'"

    except requests.RequestException as e:
        assert False, f"Request to valid document_id endpoint failed: {e}"

    # Test unknown document_id returns 404 with appropriate error message
    url_invalid = f"{BASE_URL}/api/dashboard/documents/{invalid_document_id}"
    try:
        resp_invalid = requests.get(url_invalid, timeout=TIMEOUT)
        assert resp_invalid.status_code == 404, f"Expected 404 for unknown document_id but got {resp_invalid.status_code}"
        data_invalid = resp_invalid.json()
        assert "error" in data_invalid, "Expected 'error' key in 404 response"
        assert data_invalid["error"].lower() == "document not found", f"Expected error message 'Document not found', got '{data_invalid['error']}'"

    except requests.RequestException as e:
        assert False, f"Request to invalid document_id endpoint failed: {e}"

test_dashboard_document_detail_returns_section_level_information_or_404()