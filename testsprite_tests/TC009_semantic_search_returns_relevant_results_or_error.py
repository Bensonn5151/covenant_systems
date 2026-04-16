import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_semantic_search_returns_relevant_results_or_error():
    query = "breach notification requirements"
    params = {"query": query, "top_k": 5}
    url = f"{BASE_URL}/search"

    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /search failed: {e}"

    if response.status_code == 200:
        try:
            data = response.json()
        except ValueError:
            assert False, "Response is not valid JSON."
        # Validate main keys
        assert "results" in data, "Key 'results' not in response"
        assert "query" in data, "Key 'query' not in response"
        assert "count" in data, "Key 'count' not in response"
        assert data["query"] == query

        results = data["results"]
        assert isinstance(results, list), "'results' is not a list"
        # Validate each result contains required fields
        for item in results:
            assert isinstance(item, dict), "Each result item should be a dict"
            assert "section_id" in item, "Missing 'section_id' in a result item"
            assert "title" in item, "Missing 'title' in a result item"
            assert "body" in item, "Missing 'body' in a result item"
            assert "score" in item, "Missing 'score' in a result item"
            assert "document" in item, "Missing 'document' in a result item"
    elif response.status_code == 500:
        try:
            data = response.json()
        except ValueError:
            assert False, "Response is not valid JSON."
        # Validate error message matches expected
        assert "error" in data, "Key 'error' not in 500 response"
        assert data["error"] == "FAISS index not found"
    else:
        assert False, f"Unexpected status code: {response.status_code}, response: {response.text}"

test_semantic_search_returns_relevant_results_or_error()