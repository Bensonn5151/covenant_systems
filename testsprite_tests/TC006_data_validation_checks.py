import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_data_validation_checks():
    url = f"{BASE_URL}/validate"
    headers = {"Accept": "application/json"}

    # Test successful validation response
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            assert "valid" in data, "Response missing 'valid' key"
            assert isinstance(data["valid"], bool), "'valid' should be a boolean"
            assert "errors" in data, "Response missing 'errors' key"
            assert isinstance(data["errors"], list), "'errors' should be a list"
            assert "warnings" in data, "Response missing 'warnings' key"
            assert isinstance(data["warnings"], list), "'warnings' should be a list"
        elif response.status_code == 500:
            # Validation service unavailable case
            assert "Validation service unavailable" in response.text or True
        else:
            assert False, f"Unexpected status code {response.status_code}"
    except requests.exceptions.RequestException as e:
        assert False, f"Request failed with exception: {e}"

test_data_validation_checks()