import requests

def test_dashboard_stats_endpoint_returns_aggregate_metrics():
    base_url = "http://localhost:8000"
    url = f"{base_url}/api/dashboard/stats"
    headers = {
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON."

    # Validate required keys presence
    required_keys = [
        "total_sections",
        "total_documents",
        "classifications",
        "severity_signals",
        "operational_areas",
        "punitive_obligations"
    ]
    for key in required_keys:
        assert key in data, f"Response JSON missing required key: '{key}'"

    # Validate types and reasonable values
    assert isinstance(data["total_sections"], int) and data["total_sections"] >= 0, "Invalid total_sections"
    assert isinstance(data["total_documents"], int) and data["total_documents"] >= 0, "Invalid total_documents"

    assert isinstance(data["classifications"], dict), "classifications should be a dict"
    assert isinstance(data["severity_signals"], dict), "severity_signals should be a dict"
    assert isinstance(data["operational_areas"], dict), "operational_areas should be a dict"

    # punitive_obligations type not guaranteed. Just check it exists.

    # Further check that classifications dict is not empty
    assert len(data["classifications"]) > 0, "classifications dictionary is empty"
    assert len(data["severity_signals"]) > 0, "severity_signals dictionary is empty"
    assert len(data["operational_areas"]) > 0, "operational_areas dictionary is empty"


test_dashboard_stats_endpoint_returns_aggregate_metrics()
