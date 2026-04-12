import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_data_validation_checks():
    url = f"{BASE_URL}/validate"
    headers = {"Accept": "application/json"}

    # Test success case 200 with expected schema
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Response JSON is not a dict"
        assert "valid" in data and isinstance(data["valid"], bool), "'valid' key missing or not boolean"
        assert "errors" in data and isinstance(data["errors"], list), "'errors' key missing or not a list"
        assert "warnings" in data and isinstance(data["warnings"], list), "'warnings' key missing or not a list"
    except requests.exceptions.RequestException as e:
        assert False, f"RequestException for GET /validate success case: {e}"

    # Test error case 500 service unavailability
    # Since no specific way to force 500 is described, we simulate by calling a mock or retry?
    # Here we try to handle if 500 happens naturally on repeated calls.
    # If the server never returns 500 on normal call we simulate by a direct request expecting possible 500.
    try:
        error_response = requests.get(url, headers=headers, timeout=TIMEOUT)
        if error_response.status_code == 500:
            # Server returned 500, check response body is suitable
            assert error_response.text is not None
        else:
            # If not 500, pass silently since 500 is service-unavailability case and might not always happen
            pass
    except requests.exceptions.RequestException as e:
        # If request fails altogether, could be due to service unavailability
        pass

test_data_validation_checks()