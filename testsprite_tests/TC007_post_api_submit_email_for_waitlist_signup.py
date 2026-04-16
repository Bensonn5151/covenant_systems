import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_post_api_submit_email_waitlist_signup():
    url = f"{BASE_URL}/api/submit-email"
    headers = {"Content-Type": "application/json"}

    # Test valid email submission
    valid_email_payload = {"email": "user@example.com"}
    try:
        response = requests.post(url, json=valid_email_payload, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        json_resp = response.json()
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
        assert "success" in json_resp and json_resp["success"] is True, f"Expected success true in response, got {json_resp}"
    except requests.exceptions.RequestException as e:
        assert False, f"Valid email submission request failed: {e}"

    # Test invalid email submission
    invalid_email_payload = {"email": "not-an-email"}
    try:
        response = requests.post(url, json=invalid_email_payload, headers=headers, timeout=TIMEOUT)
        # Expecting a 400 response, so do not raise for status here
        assert response.status_code == 400, f"Expected status 400 for invalid email, got {response.status_code}"
        json_resp = response.json()
        # Response body may vary but should indicate validation error; at least some message expected
        assert isinstance(json_resp, dict), "Expected JSON response for validation error"
    except requests.exceptions.RequestException as e:
        assert False, f"Invalid email submission request failed unexpectedly: {e}"

    # Test server error handling by submitting a payload that might cause a 500
    # Since no explicit special payload triggers 500 provided, simulate with empty payload to test server error handling
    try:
        response = requests.post(url, json={}, headers=headers, timeout=TIMEOUT)
        if response.status_code == 500:
            json_resp = response.json()
            assert isinstance(json_resp, dict), "Expected JSON response on server error"
        else:
            # If not 500, it might be 422 or 400 depending on backend validation; accept that as well
            assert response.status_code in (400,422), f"Expected 400/422/500 status, got {response.status_code}"
    except requests.exceptions.RequestException as e:
        assert False, f"Server error simulation request failed: {e}"

test_post_api_submit_email_waitlist_signup()