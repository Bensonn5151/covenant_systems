
# TestSprite AI Testing Report(MCP)

---

## 1️⃣ Document Metadata
- **Project Name:** covenant_systems
- **Date:** 2026-04-16
- **Prepared by:** TestSprite AI Team

---

## 2️⃣ Requirement Validation Summary

#### Test TC001 health check endpoint returns_system_status_and_document_counts
- **Test Code:** [TC001_health_check_endpoint_returns_system_status_and_document_counts.py](./TC001_health_check_endpoint_returns_system_status_and_document_counts.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7db45cf8-5c39-407c-8048-5d9e9c35ccaf/8046b0df-5823-4efa-b50f-0eee5fe4605a
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC002 regulations_api_lists_all_regulations_with_classification_and_severity
- **Test Code:** [TC002_regulations_api_lists_all_regulations_with_classification_and_severity.py](./TC002_regulations_api_lists_all_regulations_with_classification_and_severity.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7db45cf8-5c39-407c-8048-5d9e9c35ccaf/d053ea7f-0df2-4fdd-808a-81be83e42912
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC003 dashboard_documents_endpoint_returns_regulation_tile_data
- **Test Code:** [TC003_dashboard_documents_endpoint_returns_regulation_tile_data.py](./TC003_dashboard_documents_endpoint_returns_regulation_tile_data.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7db45cf8-5c39-407c-8048-5d9e9c35ccaf/176f3615-6612-4ff3-befe-760ab089eef4
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC004 dashboard_document_detail_returns_section_level_information_or_404
- **Test Code:** [TC004_dashboard_document_detail_returns_section_level_information_or_404.py](./TC004_dashboard_document_detail_returns_section_level_information_or_404.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 50, in <module>
  File "<string>", line 44, in test_dashboard_document_detail_returns_section_level_information_or_404
AssertionError: Expected 'error' key in 404 response

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7db45cf8-5c39-407c-8048-5d9e9c35ccaf/d9e51315-395c-481a-9b28-606db9e2b031
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC005 dashboard_stats_endpoint_returns_aggregate_metrics
- **Test Code:** [TC005_dashboard_stats_endpoint_returns_aggregate_metrics.py](./TC005_dashboard_stats_endpoint_returns_aggregate_metrics.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7db45cf8-5c39-407c-8048-5d9e9c35ccaf/5571c24b-343a-40cb-b1bd-8bb63cc2749c
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC006 sample_policies_list_and_retrieve_specific_policy
- **Test Code:** [TC006_sample_policies_list_and_retrieve_specific_policy.py](./TC006_sample_policies_list_and_retrieve_specific_policy.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 35, in <module>
  File "<string>", line 30, in test_sample_policies_list_and_retrieve_specific_policy
AssertionError: Unexpected error message for nonexistent policy

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7db45cf8-5c39-407c-8048-5d9e9c35ccaf/15e4275e-a2d4-4865-97f6-1649027960ea
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC007 single_regulation_comparison_returns_comparison_results_or_errors
- **Test Code:** [TC007_single_regulation_comparison_returns_comparison_results_or_errors.py](./TC007_single_regulation_comparison_returns_comparison_results_or_errors.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 534, in _make_request
    response = conn.getresponse()
               ^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/connection.py", line 571, in getresponse
    httplib_response = super().getresponse()
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/http/client.py", line 1430, in getresponse
    response.begin()
  File "/var/lang/lib/python3.12/http/client.py", line 331, in begin
    version, status, reason = self._read_status()
                              ^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/http/client.py", line 292, in _read_status
    line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/socket.py", line 720, in readinto
    return self._sock.recv_into(b)
           ^^^^^^^^^^^^^^^^^^^^^^^
TimeoutError: timed out

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/var/lang/lib/python3.12/site-packages/requests/adapters.py", line 667, in send
    resp = conn.urlopen(
           ^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 841, in urlopen
    retries = retries.increment(
              ^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/util/retry.py", line 490, in increment
    raise reraise(type(error), error, _stacktrace)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/util/util.py", line 39, in reraise
    raise value
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 787, in urlopen
    response = self._make_request(
               ^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 536, in _make_request
    self._raise_timeout(err=e, url=url, timeout_value=read_timeout)
  File "/var/lang/lib/python3.12/site-packages/urllib3/connectionpool.py", line 367, in _raise_timeout
    raise ReadTimeoutError(
urllib3.exceptions.ReadTimeoutError: HTTPConnectionPool(host='tun.testsprite.com', port=8080): Read timed out. (read timeout=30)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<string>", line 18, in test_single_regulation_comparison_returns_comparison_results_or_errors
  File "/var/lang/lib/python3.12/site-packages/requests/api.py", line 115, in post
    return request("post", url, data=data, json=json, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/api.py", line 59, in request
    return session.request(method=method, url=url, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/sessions.py", line 589, in request
    resp = self.send(prep, **send_kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/sessions.py", line 703, in send
    r = adapter.send(request, **kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/lang/lib/python3.12/site-packages/requests/adapters.py", line 713, in send
    raise ReadTimeout(e, request=request)
requests.exceptions.ReadTimeout: HTTPConnectionPool(host='tun.testsprite.com', port=8080): Read timed out. (read timeout=30)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 78, in <module>
  File "<string>", line 20, in test_single_regulation_comparison_returns_comparison_results_or_errors
AssertionError: Request failed for valid payload: HTTPConnectionPool(host='tun.testsprite.com', port=8080): Read timed out. (read timeout=30)

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7db45cf8-5c39-407c-8048-5d9e9c35ccaf/55f5b904-35fa-41e3-b3b7-c0eed2f26f46
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC009 semantic_search_returns_relevant_results_or_error
- **Test Code:** [TC009_semantic_search_returns_relevant_results_or_error.py](./TC009_semantic_search_returns_relevant_results_or_error.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7db45cf8-5c39-407c-8048-5d9e9c35ccaf/337a703d-846c-4f30-a4bd-aba3f3825cf9
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC010 data_validation_endpoint_reports_integrity_status
- **Test Code:** [TC010_data_validation_endpoint_reports_integrity_status.py](./TC010_data_validation_endpoint_reports_integrity_status.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7db45cf8-5c39-407c-8048-5d9e9c35ccaf/47f04983-7f84-4feb-bdfa-c128e8dc57c0
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---


## 3️⃣ Coverage & Matching Metrics

- **66.67** of tests passed

| Requirement        | Total Tests | ✅ Passed | ❌ Failed  |
|--------------------|-------------|-----------|------------|
| ...                | ...         | ...       | ...        |
---


## 4️⃣ Key Gaps / Risks
{AI_GNERATED_KET_GAPS_AND_RISKS}
---