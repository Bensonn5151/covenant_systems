import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_data_validation_endpoint_reports_integrity_status():
    url = f"{BASE_URL}/validate"
    try:
        response = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /validate failed: {e}"

    if response.status_code == 200:
        try:
            data = response.json()
        except ValueError:
            assert False, "Response is not valid JSON"

        assert isinstance(data, dict), "Response JSON must be an object"
        assert "valid" in data, "'valid' field missing in response"
        assert isinstance(data["valid"], bool), "'valid' field must be boolean"

        assert "errors" in data, "'errors' field missing in response"
        assert isinstance(data["errors"], list), "'errors' field must be a list"

        assert "warnings" in data, "'warnings' field missing in response"
        assert isinstance(data["warnings"], list), "'warnings' field must be a list"

    else:
        # Handle error cases gracefully and validate error response structure
        try:
            err_data = response.json()
        except ValueError:
            assert False, f"Error response is not valid JSON, status code: {response.status_code}"

        assert "error" in err_data, "'error' field missing in error response"
        assert isinstance(err_data["error"], str), "'error' field must be a string"
        # Optionally check for reason field if present
        if "reason" in err_data:
            assert isinstance(err_data["reason"], str), "'reason' field must be a string if present"


test_data_validation_endpoint_reports_integrity_status()