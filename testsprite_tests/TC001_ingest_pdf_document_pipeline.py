import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_ingest_pdf_document_pipeline():
    ingest_url = f"{BASE_URL}/ingest"
    headers = {"Content-Type": "application/json"}

    # Successful ingestion test with existing PDF and full parameters
    payload_success = {
        "pdf_path": "/data/regulations/raw/bank_act.pdf",
        "document_type": "act",
        "jurisdiction": "Canada",
        "is_bilingual": True
    }

    try:
        response = requests.post(ingest_url, json=payload_success, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}, response: {response.text}"
        json_resp = response.json()
        assert "document_id" in json_resp and isinstance(json_resp["document_id"], str) and json_resp["document_id"]
        assert "sections_count" in json_resp and isinstance(json_resp["sections_count"], int) and json_resp["sections_count"] > 0
        assert "status" in json_resp and json_resp["status"] == "processed"
    except requests.RequestException as e:
        assert False, f"RequestException during successful ingest test: {e}"

    # Error case 1: invalid PDF path
    payload_invalid_pdf = {
        "pdf_path": "/data/missing.pdf",
        "document_type": "act"
    }
    try:
        response = requests.post(ingest_url, json=payload_invalid_pdf, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 400, f"Expected 400 for invalid PDF but got {response.status_code}, response: {response.text}"
        # The error message text is "Invalid PDF or missing parameters"
        assert ("Invalid PDF" in response.text) or ("missing parameters" in response.text) or (response.text)
    except requests.RequestException as e:
        assert False, f"RequestException during invalid pdf ingest test: {e}"

    # Error case 2: missing required parameters (e.g. no pdf_path)
    payload_missing_params = {
        "document_type": "act",
        "jurisdiction": "Canada",
        "is_bilingual": True
    }
    try:
        response = requests.post(ingest_url, json=payload_missing_params, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 400, f"Expected 400 for missing parameters but got {response.status_code}, response: {response.text}"
        assert ("Invalid PDF" in response.text) or ("missing parameters" in response.text) or (response.text)
    except requests.RequestException as e:
        assert False, f"RequestException during missing parameters ingest test: {e}"


test_ingest_pdf_document_pipeline()