import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_validate_endpoint():
    url = f"{BASE_URL}/validate"
    try:
        response = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /validate endpoint failed: {e}"

    if response.status_code == 200:
        try:
            data = response.json()
        except ValueError:
            assert False, "Response body is not valid JSON"

        # Validate expected keys in the response
        assert isinstance(data, dict), "Response JSON is not a dictionary"
        assert "valid" in data, "'valid' key missing in response"
        assert isinstance(data["valid"], bool), "'valid' is not a boolean"
        assert "errors" in data, "'errors' key missing in response"
        assert isinstance(data["errors"], list), "'errors' is not a list"
        assert "warnings" in data, "'warnings' key missing in response"
        assert isinstance(data["warnings"], list), "'warnings' is not a list"

    elif response.status_code == 500:
        # Expecting service unavailability or backend errors
        content = response.text.lower()
        assert "validation service unavailable" in content or "error" in content, \
            "500 response does not indicate service unavailable or backend error"
    else:
        assert False, f"Unexpected status code {response.status_code} received from /validate"

test_get_validate_endpoint()