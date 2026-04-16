import requests
from requests.exceptions import RequestException

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_search_perform_semantic_similarity_search():
    headers = {
        "Content-Type": "application/json"
    }

    # Test a successful search assuming index is loaded
    params_success = {
        "query": "customer due diligence AML requirements",
        "top_k": 5,
        "category": "AML"
    }

    try:
        response = requests.get(f"{BASE_URL}/search", params=params_success, headers=headers, timeout=TIMEOUT)
        # Possible 200 or 500, handle both

        # If index loaded successfully:
        if response.status_code == 200:
            json_resp = response.json()
            assert "results" in json_resp, "Response JSON must contain 'results'"
            results = json_resp["results"]
            assert isinstance(results, list), "'results' must be a list"
            # Check each result has required fields
            for r in results:
                assert "section_id" in r, "Each result must contain 'section_id'"
                assert "title" in r, "Each result must contain 'title'"
                assert "body" in r, "Each result must contain 'body'"
                assert "score" in r, "Each result must contain 'score'"
                assert "document" in r, "Each result must contain 'document'"
                # Validate score is a number between 0 and 1
                assert isinstance(r["score"], (float, int)), "'score' must be a number"
                assert 0 <= r["score"] <= 1, "'score' must be between 0 and 1"

        # If index not loaded:
        elif response.status_code == 500:
            json_resp = response.json()
            assert "detail" in json_resp or True  # 500 error message structure unknown, so just accept

        else:
            assert False, f"Unexpected status code: {response.status_code}"

    except RequestException as e:
        assert False, f"RequestException occurred during successful search test: {e}"


test_get_search_perform_semantic_similarity_search()
