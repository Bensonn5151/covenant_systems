import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}

def test_email_signup_submission():
    url = f"{BASE_URL}/api/submit-email"

    # Test valid email submission
    valid_payload = {"email": "test@example.com"}
    try:
        response = requests.post(url, json=valid_payload, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected status 200 for valid email but got {response.status_code}"
        json_resp = response.json()
        assert "success" in json_resp, "'success' key not in response"
        assert json_resp["success"] is True, "Expected success true for valid email submission"
    except requests.RequestException as e:
        assert False, f"Request failed for valid email: {e}"

    # Test invalid email submissions
    invalid_emails = ["not-an-email", "missing_at_symbol.com", "@missingusername.com", "plainaddress"]
    for invalid_email in invalid_emails:
        invalid_payload = {"email": invalid_email}
        try:
            response = requests.post(url, json=invalid_payload, headers=HEADERS, timeout=TIMEOUT)
            assert response.status_code == 400, f"Expected status 400 for invalid email '{invalid_email}' but got {response.status_code}"
        except requests.RequestException as e:
            assert False, f"Request failed for invalid email '{invalid_email}': {e}"

    # Test server error handling by simulating a server error scenario:
    # Since no details given on how to trigger a 500, we perform a request with missing email field
    try:
        response = requests.post(url, json={}, headers=HEADERS, timeout=TIMEOUT)
        # We expect 400 or 422 (validation error) or 500 - if 500 occurs, test passes for server error handling
        assert response.status_code in (400, 422, 500), f"Expected 400, 422 or 500 status for missing email field but got {response.status_code}"
    except requests.RequestException as e:
        assert False, f"Request failed for missing email field: {e}"

test_email_signup_submission()
