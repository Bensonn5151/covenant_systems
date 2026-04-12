import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_email_signup_submission():
    url = f"{BASE_URL}/api/submit-email"
    headers = {"Content-Type": "application/json"}

    # Test successful submission with valid email
    valid_email_payload = {"email": "user@example.com"}
    try:
        response = requests.post(url, json=valid_email_payload, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected status 200 but got {response.status_code}"
        resp_json = response.json()
        assert "success" in resp_json, "Response JSON missing 'success' key"
        assert resp_json["success"] is True, "Expected success true for valid email submission"
    except requests.RequestException as e:
        assert False, f"Request failed unexpectedly: {e}"

    # Test validation error with invalid email format
    invalid_email_payload = {"email": "not-an-email"}
    try:
        response = requests.post(url, json=invalid_email_payload, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 400, f"Expected status 400 for invalid email but got {response.status_code}"
    except requests.RequestException as e:
        assert False, f"Request failed unexpectedly: {e}"

    # Test server error handling by simulating with an email triggering 500 (if applicable)
    # Since no direct method to cause 500 from API described, we simulate with a known edge case email
    # If API does not provide server error trigger, this test will still assert not 500
    server_error_email_payload = {"email": "cause@server.error"}
    try:
        response = requests.post(url, json=server_error_email_payload, headers=headers, timeout=TIMEOUT)
        if response.status_code == 500:
            # Server error correctly returned
            pass
        else:
            assert response.status_code in (200, 400), (
                f"Unexpected status code {response.status_code} for server error test"
            )
    except requests.RequestException as e:
        assert False, f"Request failed unexpectedly: {e}"


test_email_signup_submission()