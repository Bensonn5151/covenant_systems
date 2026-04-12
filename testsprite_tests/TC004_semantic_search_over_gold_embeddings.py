import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_semantic_search_over_gold_embeddings():
    # Test successful search with valid query, top_k and category
    params_success = {
        "query": "customer due diligence AML requirements",
        "top_k": 5,
        "category": "AML"
    }
    try:
        response = requests.get(f"{BASE_URL}/search", params=params_success, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected status 200 but got {response.status_code}"
        json_resp = response.json()
        assert "results" in json_resp, "Response JSON missing 'results' field"
        results = json_resp["results"]
        assert isinstance(results, list), "'results' should be a list"
        assert len(results) <= params_success["top_k"], f"Returned more results than top_k={params_success['top_k']}"
        for item in results:
            assert all(key in item for key in ("section_id", "title", "body", "score", "document")), \
                "Each result must have 'section_id', 'title', 'body', 'score', and 'document'"
            assert isinstance(item["section_id"], str), "'section_id' should be a string"
            assert isinstance(item["title"], str), "'title' should be a string"
            assert isinstance(item["body"], str), "'body' should be a string"
            assert isinstance(item["score"], (float, int)), "'score' should be a float or int"
            assert 0 <= item["score"] <= 1, "'score' should be between 0 and 1"
            assert isinstance(item["document"], str), "'document' should be a string"
    except requests.RequestException as e:
        assert False, f"RequestException during successful search test: {e}"

    # Test error case: index not loaded (expect 500)
    params_error = {
        "query": "data retention policy",
        "top_k": 5
    }
    try:
        response = requests.get(f"{BASE_URL}/search", params=params_error, timeout=TIMEOUT)
        # We expect a 500 error indicating index not loaded
        assert response.status_code == 500, f"Expected status 500 but got {response.status_code}"
        # Response body can be checked for error message presence but not mandatory as per PRD
    except requests.RequestException as e:
        assert False, f"RequestException during error case test: {e}"

test_semantic_search_over_gold_embeddings()
