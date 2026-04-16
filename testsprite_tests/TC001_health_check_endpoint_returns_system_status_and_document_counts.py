import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_health_check_endpoint_returns_system_status_and_document_counts():
    url = f"{BASE_URL}/health"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        # Assert status code 200
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        # Assert required keys exist
        assert "status" in data, "'status' key not found in response"
        assert "timestamp" in data, "'timestamp' key not found in response"
        assert "documents" in data, "'documents' key not found in response"
        documents = data["documents"]
        # Assert documents contain bronze, silver, gold keys
        for layer in ["bronze", "silver", "gold"]:
            assert layer in documents, f"'{layer}' key not found in documents"
            assert isinstance(documents[layer], int), f"'{layer}' count should be int"
        # Assert timestamp is non-empty string (basic check)
        assert isinstance(data["timestamp"], str) and data["timestamp"], "'timestamp' is empty or not a string"
        # Assert status is a non-empty string (e.g. "healthy")
        assert isinstance(data["status"], str) and data["status"], "'status' is empty or not a string"
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

test_health_check_endpoint_returns_system_status_and_document_counts()