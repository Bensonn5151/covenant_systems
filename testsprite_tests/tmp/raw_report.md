
# TestSprite AI Testing Report(MCP)

---

## 1️⃣ Document Metadata
- **Project Name:** covenant_systems
- **Date:** 2026-04-12
- **Prepared by:** TestSprite AI Team

---

## 2️⃣ Requirement Validation Summary

#### Test TC001 ingest_pdf_document_pipeline
- **Test Code:** [TC001_ingest_pdf_document_pipeline.py](./TC001_ingest_pdf_document_pipeline.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 56, in <module>
  File "<string>", line 21, in test_ingest_pdf_document_pipeline
AssertionError: Expected 200 but got 400, response: {"detail":"PDF not found: /data/regulations/raw/bank_act.pdf"}

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/3e1a7871-a985-428a-8d02-ee8abb14b720/67603927-b2da-46a5-9631-a3af440ce4f2
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC002 batch_document_processing_from_manifest
- **Test Code:** [TC002_batch_document_processing_from_manifest.py](./TC002_batch_document_processing_from_manifest.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/3e1a7871-a985-428a-8d02-ee8abb14b720/57a349e4-906e-4297-8c18-1a2e67383999
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC003 legislation_discovery_and_download
- **Test Code:** [TC003_legislation_discovery_and_download.py](./TC003_legislation_discovery_and_download.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 45, in <module>
  File "<string>", line 16, in test_legislation_discovery_and_download
AssertionError: Expected discovered_count >= 1, got 0

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/3e1a7871-a985-428a-8d02-ee8abb14b720/0a4826df-b85b-4c50-897a-8d8e7018664d
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC004 semantic_search_over_gold_embeddings
- **Test Code:** [TC004_semantic_search_over_gold_embeddings.py](./TC004_semantic_search_over_gold_embeddings.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 46, in <module>
  File "<string>", line 41, in test_semantic_search_over_gold_embeddings
AssertionError: Expected status 500 but got 200

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/3e1a7871-a985-428a-8d02-ee8abb14b720/8c4362b9-d315-4f39-9b27-4e890e3b6cfd
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC005 knowledge_graph_building_from_manifest
- **Test Code:** [TC005_knowledge_graph_building_from_manifest.py](./TC005_knowledge_graph_building_from_manifest.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/3e1a7871-a985-428a-8d02-ee8abb14b720/cdec777a-7ffd-42a9-8a4b-2950e97a979d
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC006 data_validation_checks
- **Test Code:** [TC006_data_validation_checks.py](./TC006_data_validation_checks.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/3e1a7871-a985-428a-8d02-ee8abb14b720/ce1389bc-92ab-49c9-8f2e-b2e64f62473c
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC007 email_signup_submission
- **Test Code:** [TC007_email_signup_submission.py](./TC007_email_signup_submission.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/3e1a7871-a985-428a-8d02-ee8abb14b720/c2bda70e-af24-4a4d-8a70-55af41c0fbf2
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC008 web_scraping_of_regulatory_content
- **Test Code:** [TC008_web_scraping_of_regulatory_content.py](./TC008_web_scraping_of_regulatory_content.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/3e1a7871-a985-428a-8d02-ee8abb14b720/fb0085a0-8506-46ed-a56c-82e5661490ce
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---


## 3️⃣ Coverage & Matching Metrics

- **62.50** of tests passed

| Requirement        | Total Tests | ✅ Passed | ❌ Failed  |
|--------------------|-------------|-----------|------------|
| ...                | ...         | ...       | ...        |
---


## 4️⃣ Key Gaps / Risks
{AI_GNERATED_KET_GAPS_AND_RISKS}
---