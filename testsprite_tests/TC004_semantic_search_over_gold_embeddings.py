import requests
from requests.exceptions import RequestException, Timeout

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_semantic_search_over_gold_embeddings():
    try:
        # Normal success case: perform a semantic search with query and top_k parameters
        params = {"query": "money laundering", "top_k": 2}
        response = requests.get(f"{BASE_URL}/search", params=params, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
        data = response.json()
        assert "results" in data, "Response JSON missing 'results' key"
        results = data["results"]
        assert isinstance(results, list), "'results' should be a list"
        # Assert that top_k results are returned (or fewer but not zero)
        assert 0 < len(results) <= 2, f"'results' length expected between 1 and 2 but got {len(results)}"
        for item in results:
            # Validate all required fields in each result
            for field in ("section_id", "title", "body", "score", "document"):
                assert field in item, f"Result missing field '{field}'"
            # Validate types
            assert isinstance(item["section_id"], str), "'section_id' should be a string"
            assert isinstance(item["title"], str), "'title' should be a string"
            assert isinstance(item["body"], str), "'body' should be a string"
            assert isinstance(item["score"], (float, int)), "'score' should be a number"
            assert 0.0 <= float(item["score"]) <= 1.0, "'score' should be between 0 and 1"
            assert isinstance(item["document"], str), "'document' should be a string"

        # Error case: query expected to trigger 500 when index not loaded
        # The PRD example indicates that "data retention policy" query causes this
        params_error = {"query": "data retention policy", "top_k": 5}
        error_response = requests.get(f"{BASE_URL}/search", params=params_error, timeout=TIMEOUT)
        assert error_response.status_code == 500, f"Expected 500 for index not loaded but got {error_response.status_code}"
        error_json = error_response.json()
        # Response body may be a message or error explanation, not strictly defined but assert presence
        assert error_json is not None, "Expected JSON response for 500 error"
    except (RequestException, Timeout) as e:
        assert False, f"Request failed with exception: {e}"

test_semantic_search_over_gold_embeddings()