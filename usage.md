   # Auto-detect everything (recommended)
   
   python3 test_ingestion.py <pdf_path>

   # Force bilingual extraction
  python3 test_ingestion.py <pdf_path> --bilingual

  Examples

  # Canadian Bank Act (auto-detects bilingual + metadata)
  python3 test_ingestion.py storage/bronze/bank_act_canada.pdf

  # US SEC regulation
  python3 test_ingestion.py data/raw/sec_regulation_2024.pdf

  # Force bilingual mode
  python3 test_ingestion.py data/raw/osfi_b13_guideline.pdf --bilingual


  What it does automatically

  1. Bilingual Detection:
  - Analyzes first page word distribution
  - If both left/right halves have >30% of words → bilingual
  - Extracts only left column (English)

  2. Metadata Inference from filename:
  - Document Type: Looks for "act", "regulation", "guideline", "policy", "standard"
  - Jurisdiction: Looks for "canada", "us", "uk", "eu", or regulator names (OSFI, SEC, FCA, etc.)

  3. Processing:
  - Bronze: Raw text extraction
  - OCR: If needed (scanned PDFs)
  - Silver: Section segmentation
  - Shows first 3 sections as preview


  # Install dependencies
  pip install PyPDF2 pdfplumber PyMuPDF

  # Test with your Bank Act PDF