import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}


def test_single_regulation_comparison_returns_comparison_results_or_errors():
    compare_url = f"{BASE_URL}/api/compare"

    # Test 200 OK with valid sample_policy_id and regulation_id
    payload_valid = {
        "sample_policy_id": "quicklend_privacy_notice",
        "regulation_id": "pipeda",
        "threshold": 0.8
    }
    try:
        resp_valid = requests.post(compare_url, json=payload_valid, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed for valid payload: {e}"

    assert resp_valid.status_code == 200, f"Expected 200, got {resp_valid.status_code}"
    json_valid = resp_valid.json()

    # Validate presence and types of expected keys in 200 response
    expected_keys = [
        "score",
        "total_obligations",
        "covered",
        "gaps",
        "partial",
        "matches",
        "gap_details",
        "partial_details",
        "coverage_by_area",
    ]
    for key in expected_keys:
        assert key in json_valid, f"Key '{key}' missing in response"
    # Additional sanity checks on types
    assert isinstance(json_valid["score"], (float, int))
    assert isinstance(json_valid["covered"], int) or isinstance(json_valid["covered"], float)
    assert isinstance(json_valid["gaps"], int) or isinstance(json_valid["gaps"], float)
    assert isinstance(json_valid["partial"], int) or isinstance(json_valid["partial"], float)
    assert isinstance(json_valid["matches"], int) or isinstance(json_valid["matches"], float)
    assert isinstance(json_valid["gap_details"], (list, dict))
    assert isinstance(json_valid["partial_details"], (list, dict))
    assert isinstance(json_valid["coverage_by_area"], (list, dict))

    # Test 404 Not Found if policy or regulation not found
    payload_not_found = {
        "sample_policy_id": "quicklend_privacy_notice",
        "regulation_id": "unknown_reg",
        "threshold": 0.8
    }
    try:
        resp_404 = requests.post(compare_url, json=payload_not_found, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed for 404 test payload: {e}"

    assert resp_404.status_code == 404, f"Expected 404, got {resp_404.status_code}"
    json_404 = resp_404.json()
    assert "error" in json_404, "Error message missing in 404 response"
    assert json_404["error"] == "Policy or regulation not found"

    # Test 400 Bad Request if no policy_text or sample_policy_id provided
    payload_bad_request = {}
    try:
        resp_400 = requests.post(compare_url, json=payload_bad_request, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed for 400 test payload: {e}"

    assert resp_400.status_code == 400, f"Expected 400, got {resp_400.status_code}"
    json_400 = resp_400.json()
    assert "error" in json_400, "Error message missing in 400 response"
    assert json_400["error"] == "No sections found"


test_single_regulation_comparison_returns_comparison_results_or_errors()