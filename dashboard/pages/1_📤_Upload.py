"""
Document Upload Page

Upload and process PDF documents through the ingestion pipeline.
"""

import streamlit as st
import sys
from pathlib import Path
import tempfile
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingestion.pipeline import IngestionPipeline

st.set_page_config(page_title="Upload Document", page_icon="📤", layout="wide")

st.title("📤 Upload Regulatory Document")
st.markdown("Process PDF documents through the Bronze → Silver pipeline")

# Initialize pipeline
@st.cache_resource
def get_pipeline():
    return IngestionPipeline(
        bronze_path="storage/bronze",
        silver_path="storage/silver",
    )

pipeline = get_pipeline()

# File uploader
uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
    help="Upload a regulatory document (Act, Regulation, Guideline, etc.)"
)

if uploaded_file:
    # Document settings
    st.markdown("### ⚙️ Processing Options")

    col1, col2 = st.columns(2)

    with col1:
        doc_id = st.text_input(
            "Document ID (optional)",
            placeholder="e.g., bank_act_canada",
            help="Leave blank to auto-generate from filename"
        )

        doc_type = st.selectbox(
            "Document Type",
            ["Act", "Regulation", "Guideline", "Policy", "Standard", "Framework"],
            help="Type of regulatory document"
        )

    with col2:
        jurisdiction = st.selectbox(
            "Jurisdiction",
            ["Canada", "United States", "United Kingdom", "European Union", "International", "Unknown"],
            help="Geographic jurisdiction"
        )

        is_bilingual = st.checkbox(
            "Bilingual PDF (English/French)",
            value=False,
            help="Check if PDF has dual columns (English left, French right)"
        )

    st.markdown("---")

    # Process button
    if st.button("🚀 Process Document", type="primary"):
        with st.spinner("Processing document..."):
            try:
                # Save uploaded file to temp location
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                # Create progress container
                progress_container = st.container()

                with progress_container:
                    st.markdown("### 📊 Processing Status")

                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Step 1: Extract
                    status_text.text("Step 1/3: Extracting text from PDF...")
                    progress_bar.progress(33)

                    # Process document
                    result = pipeline.process_document(
                        pdf_path=tmp_path,
                        document_id=doc_id if doc_id else None,
                        document_type=doc_type,
                        jurisdiction=jurisdiction,
                        is_bilingual=is_bilingual,
                    )

                    progress_bar.progress(100)
                    status_text.text("✅ Processing complete!")

                # Display results
                st.success("✅ Document processed successfully!")

                st.markdown("### 📋 Results Summary")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Document ID", result['document_id'])
                with col2:
                    st.metric("Total Characters", f"{result['total_chars']:,}")
                with col3:
                    st.metric("Sections Extracted", result['sections_count'])

                # Show locations
                st.markdown("### 📁 Storage Locations")

                st.markdown(f"""
                **Bronze Layer:**
                ```
                {result['bronze']['bronze_file']}
                ```

                **Silver Layer:**
                ```
                {result['silver']['silver_file']}
                ```
                """)

                # Show sample sections
                st.markdown("### 📖 Sample Sections")

                sections_file = Path(result['silver']['silver_file'])
                if sections_file.exists():
                    with open(sections_file, 'r', encoding='utf-8') as f:
                        sections = json.load(f)

                    # Display first 3 sections
                    for i, section in enumerate(sections[:3]):
                        with st.expander(f"Section {section['section_number']}: {section['title'][:50]}..."):
                            st.markdown(f"**ID:** `{section['section_id']}`")
                            st.markdown(f"**Level:** {section['level']}")
                            st.markdown(f"**Body:**")
                            st.text(section['body'][:500] + "..." if len(section['body']) > 500 else section['body'])

                    if len(sections) > 3:
                        st.info(f"✨ Plus {len(sections) - 3} more sections. View all in the Silver Layer page.")

                # Next steps
                st.markdown("### 🎯 Next Steps")
                st.markdown("""
                1. 📦 **View Bronze Layer** to see the raw extracted text
                2. 🔷 **View Silver Layer** to browse all structured sections
                3. ⬅️ Go to the sidebar and select a layer to explore
                """)

                # Cleanup
                Path(tmp_path).unlink()

            except Exception as e:
                st.error(f"❌ Error processing document: {str(e)}")
                st.exception(e)

else:
    # Instructions
    st.info("""
    👆 **Upload a PDF to get started**

    Supported documents:
    - 📜 Acts and Regulations
    - 📋 Guidelines and Frameworks
    - 📄 Policies and Standards

    The system will:
    1. Extract text (with OCR if needed)
    2. Segment into structured sections
    3. Infer metadata (jurisdiction, type, etc.)
    4. Save to Bronze and Silver layers
    """)

    # Example
    with st.expander("📚 Example: Bank Act of Canada"):
        st.markdown("""
        If you have the Bank Act PDF in `storage/bronze/bank_act_canada.pdf`, you can test with:

        ```bash
        python3 test_ingestion.py storage/bronze/bank_act_canada.pdf
        ```

        Or upload it here using the file uploader above.
        """)