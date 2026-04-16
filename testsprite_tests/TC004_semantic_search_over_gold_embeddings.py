import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_semantic_search_over_gold_embeddings():
    # Test successful search query
    params = {
        "query": "breach notification requirements",
        "top_k": 5
    }
    try:
        response = requests.get(f"{BASE_URL}/search", params=params, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /search failed with exception: {e}"

    if response.status_code == 200:
        json_resp = response.json()
        assert "results" in json_resp, "Response JSON missing 'results'"
        results = json_resp["results"]
        assert isinstance(results, list), "'results' should be a list"
        assert len(results) <= 5, "Returned more results than requested top_k=5"
        for result in results:
            assert isinstance(result, dict), "Each result should be a dict"
            for field in ["section_id", "title", "body", "score", "document"]:
                assert field in result, f"Result missing field '{field}'"
            score = result["score"]
            assert isinstance(score, (float, int)), "'score' should be a number"
            assert 0.0 <= score <= 1.0, "'score' should be between 0.0 and 1.0"
    elif response.status_code == 500:
        # Possible index not loaded error, fail test since this is unexpected here
        assert False, "Search returned 500 error unexpectedly during normal query"
    else:
        assert False, f"Unexpected status code {response.status_code} for valid search query"

    # Test error handling when index not loaded
    # Use a query that is likely to cause index not loaded error per PRD example ("data retention policy")
    params_error = {
        "query": "data retention policy",
        "top_k": 5
    }
    try:
        error_response = requests.get(f"{BASE_URL}/search", params=params_error, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /search failed with exception: {e}"

    # Accept 500 or 200 status code here since server might actually serve results or error
    assert error_response.status_code in (200, 500), f"Expected status 200 or 500 when index not loaded, got {error_response.status_code}"

test_semantic_search_over_gold_embeddings()
