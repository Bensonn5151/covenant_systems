import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_sample_policies_list_and_retrieve_specific_policy():
    # Test GET /api/sample-policies returns HTTP 200 with a list of sample policies
    try:
        list_resp = requests.get(f"{BASE_URL}/api/sample-policies", timeout=TIMEOUT)
        assert list_resp.status_code == 200, f"Expected 200 got {list_resp.status_code}"
        list_data = list_resp.json()
        assert "policies" in list_data and isinstance(list_data["policies"], list), "Missing or invalid policies list"
        # Check if 'quicklend_privacy_notice' is in the list
        policy_ids = [p.get("id") for p in list_data["policies"] if "id" in p]
        assert "quicklend_privacy_notice" in policy_ids, "'quicklend_privacy_notice' policy not found in sample policies"

        # Test GET /api/sample-policies/quicklend_privacy_notice returns HTTP 200 with policy details
        policy_resp = requests.get(f"{BASE_URL}/api/sample-policies/quicklend_privacy_notice", timeout=TIMEOUT)
        assert policy_resp.status_code == 200, f"Expected 200 got {policy_resp.status_code}"
        policy_data = policy_resp.json()
        # Validate required fields
        for field in ["policy_name", "filename", "sections", "raw_text"]:
            assert field in policy_data, f"Missing field '{field}' in policy details"
        assert isinstance(policy_data["sections"], list), "'sections' is not a list"

        # Test GET /api/sample-policies/nonexistent returns HTTP 404 with error message
        nonexistent_resp = requests.get(f"{BASE_URL}/api/sample-policies/nonexistent", timeout=TIMEOUT)
        assert nonexistent_resp.status_code == 404, f"Expected 404 for nonexistent policy got {nonexistent_resp.status_code}"
        error_data = nonexistent_resp.json()
        assert "error" in error_data and error_data["error"] == "Sample policy not found", "Unexpected error message for nonexistent policy"

    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

test_sample_policies_list_and_retrieve_specific_policy()
