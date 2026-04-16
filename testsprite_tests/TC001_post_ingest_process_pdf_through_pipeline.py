import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
INGEST_ENDPOINT = f"{BASE_URL}/ingest"


def test_post_ingest_process_pdf_through_pipeline():
    # Valid payload for a bilingual PDF document expected to be processed successfully
    valid_payload = {
        "pdf_path": "/data/regulations/raw/bank_act.pdf",
        "document_type": "act",
        "jurisdiction": "Canada",
        "is_bilingual": True
    }

    # Payload variants for error cases
    invalid_pdf_payload = {
        "pdf_path": "/data/missing.pdf",
        "document_type": "act"
    }
    missing_parameters_payloads = [
        {},  # completely empty
        {"pdf_path": "/data/regulations/raw/bank_act.pdf"},  # missing required keys
        {"document_type": "act"}  # missing pdf_path
    ]

    # 1. Test valid ingestion
    try:
        response = requests.post(INGEST_ENDPOINT, json=valid_payload, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /ingest failed with exception: {e}"

    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    try:
        json_resp = response.json()
    except Exception as e:
        assert False, f"Response is not valid JSON: {e}"

    # Validate presence and types of response fields
    assert "document_id" in json_resp and isinstance(json_resp["document_id"], str) and json_resp["document_id"], "Missing or invalid document_id"
    assert "sections_count" in json_resp and isinstance(json_resp["sections_count"], int) and json_resp["sections_count"] > 0, "Missing or invalid sections_count"
    assert "status" in json_resp and json_resp["status"] == "processed", "Missing or invalid status"

    # 2. Test invalid PDF or missing parameters - expect 400 error

    # Invalid PDF path
    try:
        resp_invalid_pdf = requests.post(INGEST_ENDPOINT, json=invalid_pdf_payload, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /ingest with invalid pdf failed with exception: {e}"

    assert resp_invalid_pdf.status_code == 400, f"Expected 400 but got {resp_invalid_pdf.status_code} for invalid PDF"
    assert "Invalid PDF" in resp_invalid_pdf.text or "missing parameters" in resp_invalid_pdf.text, f"Unexpected error message for invalid PDF: {resp_invalid_pdf.text}"

    # Missing parameters tests
    for payload in missing_parameters_payloads:
        try:
            resp_missing = requests.post(INGEST_ENDPOINT, json=payload, timeout=TIMEOUT)
        except requests.RequestException as e:
            assert False, f"Request to /ingest with missing parameters failed with exception: {e}"
        assert resp_missing.status_code == 400, f"Expected 400 but got {resp_missing.status_code} for missing parameters payload: {payload}"
        assert "missing" in resp_missing.text.lower() or "invalid" in resp_missing.text.lower(), f"Unexpected error message for missing parameters: {resp_missing.text}"


test_post_ingest_process_pdf_through_pipeline()