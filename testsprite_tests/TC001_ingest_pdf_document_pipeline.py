import requests
from requests.exceptions import RequestException

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_ingest_pdf_document_pipeline():
    ingest_url = f"{BASE_URL}/ingest"

    # Valid request payload includes all required fields
    valid_payload = {
        "pdf_path": "data/raw/acts/R.S.C., 1985, c. P-21 - Privacy Act.pdf",
        "document_type": "act",
        "jurisdiction": "Canada",
        "is_bilingual": True
    }

    # Invalid request payloads
    invalid_payloads = [
        # Bad path
        {
            "pdf_path": "data/raw/acts/nonexistent.pdf",
            "document_type": "act",
            "jurisdiction": "Canada"
        },
        # Missing parameters
        {
            "pdf_path": "data/raw/acts/R.S.C., 1985, c. P-21 - Privacy Act.pdf"
            # missing document_type, jurisdiction, is_bilingual
        },
        {
            "document_type": "act",
            "jurisdiction": "Canada"
            # missing pdf_path, is_bilingual
        },
        {
            # empty payload
        }
    ]

    # Test successful ingestion with expected response keys
    try:
        response = requests.post(ingest_url, json=valid_payload, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        json_resp = response.json()
        expected_keys = {"document_id", "sections_count", "status"}
        # Assert required keys present (allow extra keys)
        assert expected_keys.issubset(set(json_resp.keys())), f"Response keys missing required keys. Expected at least keys {expected_keys}, got {set(json_resp.keys())}"
        # Check types
        assert isinstance(json_resp["document_id"], str), "document_id should be string"
        assert isinstance(json_resp["sections_count"], int), "sections_count should be integer"
        assert json_resp["status"] == "processed", f"status should be 'processed', got {json_resp['status']}"
    except RequestException as e:
        assert False, f"RequestException during valid ingest test: {e}"
    except ValueError:
        assert False, "Response is not valid JSON for valid ingest test"

    # Test error handling for invalid payloads (expect 400)
    for payload in invalid_payloads:
        try:
            resp = requests.post(ingest_url, json=payload, timeout=TIMEOUT)
            assert resp.status_code == 400, f"Expected 400 for payload {payload}, got {resp.status_code}"
            # No strict assertion on response content text
        except RequestException as e:
            assert False, f"RequestException during invalid ingest test with payload {payload}: {e}"
        except Exception as e:
            assert False, f"Unexpected exception during invalid ingest test with payload {payload}: {e}"


test_ingest_pdf_document_pipeline()
