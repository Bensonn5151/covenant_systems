import requests

BASE_URL = "http://localhost:8000"


def test_ingest_pdf_document_pipeline():
    ingest_url = f"{BASE_URL}/ingest"
    timeout = 30

    # Valid payload for bilingual PDF document ingestion
    valid_payload = {
        "pdf_path": "/data/regulations/raw/bank_act.pdf",
        "document_type": "act",
        "jurisdiction": "Canada",
        "is_bilingual": True
    }

    # Test successful ingestion
    try:
        response = requests.post(ingest_url, json=valid_payload, timeout=timeout)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # Assert required fields
        assert "document_id" in data and isinstance(data["document_id"], str) and data["document_id"]
        assert "sections_count" in data and isinstance(data["sections_count"], int) and data["sections_count"] > 0
        assert "status" in data and data["status"] == "processed"
    except requests.RequestException as e:
        assert False, f"Request failed during valid ingestion test: {e}"

    # Test error: invalid PDF path
    invalid_pdf_payload = {
        "pdf_path": "/data/missing.pdf",
        "document_type": "act"
        # missing jurisdiction and is_bilingual - to provoke error or bad PDF
    }
    try:
        response = requests.post(ingest_url, json=invalid_pdf_payload, timeout=timeout)
        # Expecting 400 error for invalid PDF or missing parameters
        assert response.status_code == 400, f"Expected 400 for invalid PDF, got {response.status_code}"
        assert "Invalid PDF" in response.text or "missing parameters" in response.text.lower()
    except requests.RequestException as e:
        assert False, f"Request failed during invalid PDF test: {e}"

    # Test error: missing required parameters (empty payload)
    empty_payload = {}
    try:
        response = requests.post(ingest_url, json=empty_payload, timeout=timeout)
        assert response.status_code == 400, f"Expected 400 for missing parameters, got {response.status_code}"
        assert "missing parameters" in response.text.lower()
    except requests.RequestException as e:
        assert False, f"Request failed during missing parameters test: {e}"


test_ingest_pdf_document_pipeline()