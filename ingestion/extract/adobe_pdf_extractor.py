"""
Adobe PDF Services Extractor

Production-grade PDF extraction using Adobe PDF Services API.
Provides 95-99% accuracy for regulatory documents with:
- Structured text blocks
- Table extraction
- Hierarchy detection
- Font/style information
"""

import os
import json
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Optional, List
import logging

try:
    from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
    from adobe.pdfservices.operation.pdf_services import PDFServices
    from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
    from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
    from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
    from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
    from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult
    from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
    from adobe.pdfservices.operation.io.stream_asset import StreamAsset
except ImportError as e:
    raise ImportError(
        "Adobe PDF Services SDK not installed. "
        "Run: pip install pdfservices-sdk==4.2.0 (requires Python 3.10+)"
    ) from e


class AdobePDFExtractor:
    """Extract text, tables, and structure from PDFs using Adobe PDF Services."""

    def __init__(self, credentials_path: str = None):
        """
        Initialize Adobe PDF extractor.

        Args:
            credentials_path: Path to pdfservices-api-credentials.json
        """
        if credentials_path is None:
            # Try default locations
            possible_paths = [
                "PDFServicesSDK/pdfservices-api-credentials.json",
                "../PDFServicesSDK/pdfservices-api-credentials.json",
                "pdfservices-api-credentials.json",
            ]

            for path in possible_paths:
                if Path(path).exists():
                    credentials_path = path
                    break

            if credentials_path is None:
                raise FileNotFoundError(
                    "Adobe credentials not found. Please provide path to "
                    "pdfservices-api-credentials.json"
                )

        self.credentials_path = Path(credentials_path)

        # Load credentials JSON for SDK v4.2.0
        with open(self.credentials_path, 'r') as f:
            creds_data = json.load(f)

        # Create ServicePrincipalCredentials with client credentials
        self.credentials = ServicePrincipalCredentials(
            client_id=creds_data['client_credentials']['client_id'],
            client_secret=creds_data['client_credentials']['client_secret']
        )

        # Initialize PDF Services
        self.pdf_services = PDFServices(credentials=self.credentials)

        logging.info(f"✓ Adobe PDF Services v4.2.0 initialized with credentials from {self.credentials_path}")

    def extract(
        self,
        pdf_path: str,
        document_id: str = None,
        extract_tables: bool = True,
        extract_styling: bool = True,
        extract_left_column_only: bool = False,
    ) -> Dict:
        """
        Extract text, tables, and structure from PDF using Adobe API.

        Args:
            pdf_path: Path to PDF file
            document_id: Optional document ID
            extract_tables: Whether to extract tables
            extract_styling: Whether to include styling information
            extract_left_column_only: If True, extract only left column (for bilingual PDFs)

        Returns:
            Dictionary containing:
                - text: Extracted plain text
                - structured_data: Full Adobe JSON with elements, tables, etc.
                - metadata: Document metadata including document_id
                - tables: List of extracted tables
                - page_count: Number of pages
                - needs_ocr: Always False (Adobe handles OCR internally)
        """
        # Generate document ID if not provided
        if not document_id:
            document_id = Path(pdf_path).stem.lower().replace(" ", "_")
        logging.info(f"Extracting PDF with Adobe PDF Services: {pdf_path}")

        try:
            # Upload PDF to Adobe (v4.2.0 API)
            logging.info("  Uploading PDF to Adobe...")
            with open(pdf_path, 'rb') as input_stream:
                input_asset = self.pdf_services.upload(
                    input_stream=input_stream,
                    mime_type=PDFServicesMediaType.PDF
                )

            # Build extract parameters
            extract_elements = [ExtractElementType.TEXT]
            if extract_tables:
                extract_elements.append(ExtractElementType.TABLES)

            extract_pdf_params = ExtractPDFParams(
                elements_to_extract=extract_elements,
                add_char_info=extract_styling
            )

            # Create and submit extract job
            logging.info("  Sending PDF to Adobe for extraction...")
            extract_pdf_job = ExtractPDFJob(
                input_asset=input_asset,
                extract_pdf_params=extract_pdf_params
            )

            # Get job location and poll for result
            location = self.pdf_services.submit(extract_pdf_job)
            pdf_services_response = self.pdf_services.get_job_result(
                location,
                ExtractPDFResult
            )

            # Get result asset and download
            result_asset = pdf_services_response.get_result().get_resource()
            stream_asset = self.pdf_services.get_content(result_asset)

            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
                tmp_zip.write(stream_asset.get_input_stream())
                zip_path = tmp_zip.name

            logging.info(f"  ✓ Extraction complete, processing results...")

            # Extract and parse the ZIP file
            extracted_data = self._process_adobe_output(zip_path, document_id, extract_left_column_only)

            # Cleanup
            Path(zip_path).unlink()

            logging.info(f"  ✓ Extracted {len(extracted_data['text'])} characters")

            return extracted_data

        except Exception as e:
            logging.error(f"Adobe PDF extraction failed: {e}")
            raise

    def _process_adobe_output(self, zip_path: str, document_id: str, extract_left_column_only: bool = False) -> Dict:
        """
        Process the Adobe output ZIP file.

        Args:
            zip_path: Path to ZIP file from Adobe
            document_id: Document identifier
            extract_left_column_only: If True, filter to left column only (for bilingual PDFs)

        Returns:
            Processed extraction data
        """
        with tempfile.TemporaryDirectory() as extract_dir:
            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # Find the structuredData.json file
            json_file = Path(extract_dir) / "structuredData.json"

            if not json_file.exists():
                raise FileNotFoundError("Adobe output missing structuredData.json")

            # Load structured data
            with open(json_file, 'r', encoding='utf-8') as f:
                structured_data = json.load(f)

            # Determine page width for column filtering (if needed)
            page_width = None
            if extract_left_column_only and structured_data.get("pages"):
                # Get width from first page
                first_page = structured_data["pages"][0]
                # Try both "width" (lowercase) and "Width" (uppercase) for compatibility
                if "width" in first_page:
                    page_width = first_page["width"]
                    logging.info(f"  Bilingual mode: Page width = {page_width}, filtering left column only")
                elif "Width" in first_page:
                    page_width = first_page["Width"]
                    logging.info(f"  Bilingual mode: Page width = {page_width}, filtering left column only")
                else:
                    logging.warning(f"  ⚠ Bilingual mode requested but no width found in page data. Available keys: {list(first_page.keys())}")

            if extract_left_column_only and not page_width:
                logging.warning("  ⚠ Bilingual filtering requested but page width could not be determined. Extracting all text.")

            # Extract plain text from elements
            text_blocks = []
            tables = []
            filtered_count = 0
            total_text_elements = 0

            for element in structured_data.get("elements", []):
                # Extract text elements
                if element.get("Text"):
                    total_text_elements += 1
                    # Check if we need to filter by column
                    if extract_left_column_only and page_width:
                        # Get element bounds (x0, y0, x1, y1)
                        bounds = element.get("Bounds")
                        if bounds and len(bounds) >= 4:
                            x0 = bounds[0]
                            midpoint = page_width / 2
                            # Only include if element starts in left half
                            if x0 < midpoint:
                                text_blocks.append(element["Text"])
                            else:
                                filtered_count += 1
                                # Debug: log first few filtered elements
                                if filtered_count <= 3:
                                    logging.debug(f"  Filtered (x={x0:.1f} >= {midpoint:.1f}): {element['Text'][:50]}...")
                        else:
                            # No bounds info, include it (fallback)
                            text_blocks.append(element["Text"])
                            if filtered_count == 0:  # Log once
                                logging.warning(f"  ⚠ Element has no Bounds data. Available keys: {list(element.keys())}")
                    else:
                        # Not filtering, include all text
                        text_blocks.append(element["Text"])

                # Extract tables (only from left column if filtering)
                elif element.get("Path") and "table" in element["Path"].lower():
                    if extract_left_column_only and page_width:
                        bounds = element.get("Bounds")
                        if bounds and len(bounds) >= 4:
                            x0 = bounds[0]
                            if x0 < page_width / 2:
                                tables.append(element)
                    else:
                        tables.append(element)

            if extract_left_column_only and page_width:
                logging.info(f"  Bilingual filtering: kept {len(text_blocks)}/{total_text_elements} elements, filtered {filtered_count}")

            full_text = "\n\n".join(text_blocks)

            # Add filtering info to metadata
            extraction_mode = "bilingual_left_column" if extract_left_column_only else "full_page"

            # Get metadata
            metadata = {
                "document_id": document_id,
                "page_count": len(structured_data.get("pages", [])),
                "element_count": len(structured_data.get("elements", [])),
                "table_count": len(tables),
                "extraction_method": "Adobe PDF Services",
                "extraction_mode": extraction_mode,
                "version": structured_data.get("version", "unknown"),
            }

            return {
                "text": full_text,
                "structured_data": structured_data,
                "metadata": metadata,
                "tables": tables,
                "page_count": metadata["page_count"],
                "needs_ocr": False,  # Adobe handles OCR internally
            }


# Convenience function
def extract_pdf_with_adobe(
    pdf_path: str,
    credentials_path: str = None,
) -> Dict:
    """
    Extract PDF using Adobe PDF Services (convenience wrapper).

    Args:
        pdf_path: Path to PDF file
        credentials_path: Path to Adobe credentials

    Returns:
        Extraction results
    """
    extractor = AdobePDFExtractor(credentials_path=credentials_path)
    return extractor.extract(pdf_path)