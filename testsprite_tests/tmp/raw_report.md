
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
  File "<string>", line 63, in test_ingest_pdf_document_pipeline
AssertionError: Expected 400 for payload {'pdf_path': 'data/raw/acts/R.S.C., 1985, c. P-21 - Privacy Act.pdf'}, got 200

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 71, in <module>
  File "<string>", line 68, in test_ingest_pdf_document_pipeline
AssertionError: Unexpected exception during invalid ingest test with payload {'pdf_path': 'data/raw/acts/R.S.C., 1985, c. P-21 - Privacy Act.pdf'}: Expected 400 for payload {'pdf_path': 'data/raw/acts/R.S.C., 1985, c. P-21 - Privacy Act.pdf'}, got 200

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/098f5706-db52-4f83-ad06-ed643d29838a/a633d6b9-8832-43c5-8323-532bc6082c3a
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC002 batch_document_processing_from_manifest
- **Test Code:** [TC002_batch_document_processing_from_manifest.py](./TC002_batch_document_processing_from_manifest.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/098f5706-db52-4f83-ad06-ed643d29838a/45ace18f-3dfb-452e-a02e-2cf27d6c9cb5
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC003 legislation_discovery_and_download
- **Test Code:** [TC003_legislation_discovery_and_download.py](./TC003_legislation_discovery_and_download.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/098f5706-db52-4f83-ad06-ed643d29838a/116699e7-5825-401a-b90a-92e2f32f2c89
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC004 semantic_search_over_gold_embeddings
- **Test Code:** [TC004_semantic_search_over_gold_embeddings.py](./TC004_semantic_search_over_gold_embeddings.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 42, in <module>
  File "<string>", line 35, in test_semantic_search_over_gold_embeddings
AssertionError: Expected 500 for index not loaded but got 200

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/098f5706-db52-4f83-ad06-ed643d29838a/38fc35e4-c3a4-4ac9-9a0a-22af4fb81059
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC005 knowledge_graph_building_from_manifest
- **Test Code:** [TC005_knowledge_graph_building_from_manifest.py](./TC005_knowledge_graph_building_from_manifest.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/098f5706-db52-4f83-ad06-ed643d29838a/6e283463-190b-4c65-9114-c18b211934f6
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC006 data_validation_checks
- **Test Code:** [TC006_data_validation_checks.py](./TC006_data_validation_checks.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/098f5706-db52-4f83-ad06-ed643d29838a/72e5f7b8-5fd3-4906-b62a-081c97d6c12f
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC007 email_signup_submission
- **Test Code:** [TC007_email_signup_submission.py](./TC007_email_signup_submission.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/098f5706-db52-4f83-ad06-ed643d29838a/f3becce3-f2bd-4d28-82a4-37449530d5d3
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC008 web_scraping_regulatory_content
- **Test Code:** [TC008_web_scraping_regulatory_content.py](./TC008_web_scraping_regulatory_content.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/098f5706-db52-4f83-ad06-ed643d29838a/b697df19-7641-434f-9593-96c895c6c004
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---


## 3️⃣ Coverage & Matching Metrics

- **75.00** of tests passed

| Requirement        | Total Tests | ✅ Passed | ❌ Failed  |
|--------------------|-------------|-----------|------------|
| ...                | ...         | ...       | ...        |
---


## 4️⃣ Key Gaps / Risks
{AI_GNERATED_KET_GAPS_AND_RISKS}
---