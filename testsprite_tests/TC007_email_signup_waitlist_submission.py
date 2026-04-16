import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_email_signup_waitlist_submission():
    url = f"{BASE_URL}/api/submit-email"
    headers = {"Content-Type": "application/json"}

    # Test valid email submission (success case)
    valid_payload = {"email": "user@example.com"}
    try:
        response = requests.post(url, json=valid_payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed for valid email submission: {e}"
    assert response.status_code == 200, f"Expected status 200 but got {response.status_code}"
    json_resp = response.json()
    assert "success" in json_resp, "Response JSON missing 'success' key on valid submission"
    assert json_resp["success"] is True, "Expected success true on valid email submission"

    # Test invalid email format (validation error)
    invalid_payload = {"email": "not-an-email"}
    try:
        response = requests.post(url, json=invalid_payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed for invalid email submission: {e}"
    assert response.status_code == 400, f"Expected status 400 for invalid email but got {response.status_code}"
    # Response body might contain error info, no strict schema given, so just check presence of error text or json
    try:
        json_resp = response.json()
        # Could be an error message or validation error details
        assert isinstance(json_resp, dict), "Invalid response JSON structure for invalid email"
    except Exception:
        # If response body not JSON, accept as well since 400 is correct response code
        pass

    # Test server error handling (simulate by sending malformed payload)
    malformed_payload = {"email": None}  # Possibly triggers server error
    try:
        response = requests.post(url, json=malformed_payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed for malformed payload submission: {e}"
    # Accept 400, 422 or 500 as server might validate or error out
    assert response.status_code in (400, 422, 500), f"Expected status 400, 422 or 500 for malformed payload but got {response.status_code}"

test_email_signup_waitlist_submission()
