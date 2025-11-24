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

# Custom CSS for better UI
st.markdown("""
<style>
    .upload-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f0f9ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #f0fdf4;
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="upload-header">
    <h1 style="margin:0;">📤 Upload & Process Documents</h1>
    <p style="margin:0.5rem 0 0 0; opacity:0.9;">Upload PDFs or process existing Bronze text files into structured sections</p>
</div>
""", unsafe_allow_html=True)

# Mode selector
st.markdown("### 🔄 Processing Mode")
processing_mode = st.radio(
    "Choose input source",
    ["Upload New PDF", "Process Existing Bronze File"],
    horizontal=True,
    help="Upload a new PDF or process an existing Bronze text file"
)

# Initialize pipeline (uses project root storage)
@st.cache_resource
def get_pipeline():
    # Get project root (3 levels up from this file: pages -> dashboard -> project)
    project_root = Path(__file__).parent.parent.parent

    # Use project root storage (same as batch_ingest.py)
    bronze_path = str(project_root / "storage" / "bronze")
    silver_path = str(project_root / "storage" / "silver")
    taxonomy_path = str(project_root / "configs" / "taxonomy.yaml")

    # Debug: Show paths in sidebar
    with st.sidebar:
        st.success("""
        **📁 Storage Locations**

        Bronze: `storage/bronze`

        Silver: `storage/silver`
        """)

        st.info("""
        **🔄 Cached Pipeline**

        If changes don't appear, use:
        Menu → Clear cache
        """)

    return IngestionPipeline(
        bronze_path=bronze_path,
        silver_path=silver_path,
        taxonomy_path=taxonomy_path,
    )

pipeline = get_pipeline()

# Conditional input based on processing mode
if processing_mode == "Upload New PDF":
    # PDF Upload Mode
    st.markdown("### 📄 Step 1: Select PDF File")

    uploaded_file = st.file_uploader(
        "Drop your PDF here or click to browse",
        type=["pdf"],
        help="Supported: Acts, Regulations, Guidelines, Company Policies",
        label_visibility="collapsed"
    )
    bronze_file_path = None

elif processing_mode == "Process Existing Bronze File":
    # Bronze File Selection Mode
    st.markdown("### 📦 Step 1: Select Bronze Text File")

    # Get project root
    project_root = Path(__file__).parent.parent.parent
    bronze_path = project_root / "storage" / "bronze"

    # Find all Bronze text files
    def find_bronze_files(base_path):
        """Find all raw_text.txt files in Bronze layer"""
        bronze_files = []
        categories = ["acts", "regulations", "guidance", "company_policies"]

        for category in categories:
            category_path = base_path / category
            if category_path.exists():
                # For guidance, check regulator subdirectories
                if category == "guidance":
                    for regulator_dir in category_path.iterdir():
                        if regulator_dir.is_dir():
                            for doc_dir in regulator_dir.iterdir():
                                raw_text = doc_dir / "raw_text.txt"
                                if raw_text.exists():
                                    bronze_files.append({
                                        "path": str(raw_text),
                                        "display": f"[{category}] {doc_dir.name}",
                                        "category": category,
                                        "doc_name": doc_dir.name,
                                        "regulator": regulator_dir.name
                                    })
                # For company_policies, check company subdirectories
                elif category == "company_policies":
                    for company_dir in category_path.iterdir():
                        if company_dir.is_dir():
                            for doc_dir in company_dir.iterdir():
                                raw_text = doc_dir / "raw_text.txt"
                                if raw_text.exists():
                                    bronze_files.append({
                                        "path": str(raw_text),
                                        "display": f"[{category}] {doc_dir.name}",
                                        "category": category,
                                        "doc_name": doc_dir.name,
                                        "company_id": company_dir.name
                                    })
                # For acts and regulations
                else:
                    for doc_dir in category_path.iterdir():
                        raw_text = doc_dir / "raw_text.txt"
                        if raw_text.exists():
                            bronze_files.append({
                                "path": str(raw_text),
                                "display": f"[{category}] {doc_dir.name}",
                                "category": category,
                                "doc_name": doc_dir.name
                            })

        return bronze_files

    bronze_files = find_bronze_files(bronze_path)

    if not bronze_files:
        st.warning("⚠️ No Bronze text files found. Upload a PDF first to create Bronze files.")
        st.stop()

    # Sort by category and name
    bronze_files.sort(key=lambda x: (x["category"], x["doc_name"]))

    # File selector
    file_displays = [f["display"] for f in bronze_files]
    selected_idx = st.selectbox(
        "Select Bronze file to process",
        range(len(bronze_files)),
        format_func=lambda i: file_displays[i],
        label_visibility="collapsed"
    )

    selected_bronze = bronze_files[selected_idx]
    bronze_file_path = selected_bronze["path"]

    st.success(f"✅ Selected: **{selected_bronze['doc_name']}**")
    st.info(f"📍 Location: `{bronze_file_path}`")

    uploaded_file = None  # No uploaded file in this mode

if not uploaded_file and not bronze_file_path:
    # Show instructions when no file is uploaded
    st.markdown("""
    <div class="info-box">
        <h4>📋 Supported Document Types</h4>
        <ul>
            <li><strong>Acts</strong>: Primary legislation (e.g., Bank Act, PIPEDA)</li>
            <li><strong>Regulations</strong>: Secondary legislation</li>
            <li><strong>Guidance</strong>: Regulator guidelines (OSFI, FINTRAC, etc.)</li>
            <li><strong>Policies</strong>: Internal company policies</li>
        </ul>

        <h4>🌍 Bilingual PDFs</h4>
        <p>For dual-column English/French PDFs, check the "Bilingual PDF" option to extract English text only.</p>
    </div>
    """, unsafe_allow_html=True)

if uploaded_file:
    st.success(f"✅ File uploaded: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
    # Document settings
    st.markdown("---")
    st.markdown("### ⚙️ Step 2: Document Information")

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
            help="Check if PDF has dual columns (English left, French right). Uses Adobe to extract left column only."
        )

    st.markdown("---")

    # Category Classification (Manual - Required for MVP)
    st.markdown("### 📑 Step 3: Classification & Metadata")

    col1, col2 = st.columns(2)

    with col1:
        manual_category = st.selectbox(
            "Document Category",
            ["act", "regulation", "guidance", "policy"],
            help="Select the document category (manual classification ensures accuracy)",
            format_func=lambda x: {
                "act": "Act (Primary Legislation)",
                "regulation": "Regulation (Secondary Legislation)",
                "guidance": "Guidance (Regulator Guidelines)",
                "policy": "Policy (Company Policy)"
            }[x]
        )

    with col2:
        # Conditional fields based on category
        regulator = None
        parent_act = None
        company_id = None

        if manual_category == "guidance":
            regulator = st.selectbox(
                "Regulator",
                ["OSFI", "FINTRAC", "OPC", "FCAC"],
                help="Which regulator issued this guidance?"
            )

        elif manual_category == "regulation":
            parent_act = st.selectbox(
                "Parent Act",
                ["Bank Act", "PCMLTFA", "PIPEDA"],
                help="Which act does this regulation fall under?"
            )

        elif manual_category == "policy":
            company_id = st.text_input(
                "Company ID",
                placeholder="e.g., acme_corp",
                help="Unique identifier for your organization"
            )

    st.markdown("---")

    # Process button with better visibility
    st.markdown("### 🚀 Step 4: Process Document")

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        process_button = st.button("▶️ Process Now", type="primary", use_container_width=True)

    if process_button:
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
                        manual_category=manual_category,
                        regulator=regulator,
                        parent_act=parent_act,
                        company_id=company_id,
                    )

                    progress_bar.progress(100)
                    status_text.text("✅ Processing complete!")

                # Display results
                st.success("✅ Document processed successfully!")

                st.markdown("### 📋 Results Summary")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Document ID", result['document_id'])
                with col2:
                    st.metric("Category", result['category'].upper())
                with col3:
                    st.metric("Total Characters", f"{result['total_chars']:,}")
                with col4:
                    st.metric("Sections Extracted", result['sections_count'])

                # Show category-specific info
                if result.get('regulator'):
                    st.info(f"📊 Regulator: **{result['regulator']}**")
                elif result.get('parent_act'):
                    st.info(f"📜 Parent Act: **{result['parent_act']}**")
                elif result.get('company_id'):
                    st.info(f"🏢 Company ID: **{result['company_id']}**")

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

elif bronze_file_path:
    # Bronze file processing mode
    st.markdown("---")
    st.markdown("### ⚙️ Step 2: Document Information")

    col1, col2 = st.columns(2)

    with col1:
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

    st.markdown("---")

    # Category Classification (Manual - Required for MVP)
    st.markdown("### 📑 Step 3: Classification & Metadata")

    col1, col2 = st.columns(2)

    with col1:
        # Auto-detect category from Bronze file path and normalize to singular
        detected_category = selected_bronze.get("category", "act")

        # Map plural to singular
        category_map = {
            "acts": "act",
            "regulations": "regulation",
            "guidance": "guidance",
            "company_policies": "policy"
        }
        detected_category = category_map.get(detected_category, detected_category)

        manual_category = st.selectbox(
            "Document Category",
            ["act", "regulation", "guidance", "policy"],
            index=["act", "regulation", "guidance", "policy"].index(detected_category),
            help="Select the document category (auto-detected from Bronze location)",
            format_func=lambda x: {
                "act": "Act (Primary Legislation)",
                "regulation": "Regulation (Secondary Legislation)",
                "guidance": "Guidance (Regulator Guidelines)",
                "policy": "Policy (Company Policy)"
            }[x]
        )

    with col2:
        # Conditional fields based on category
        regulator = None
        parent_act = None
        company_id = None

        if manual_category == "guidance":
            # Pre-fill from Bronze path if available
            default_regulator = selected_bronze.get("regulator", "OSFI")
            regulator_list = ["OSFI", "FINTRAC", "OPC", "FCAC"]
            regulator_idx = regulator_list.index(default_regulator) if default_regulator in regulator_list else 0

            regulator = st.selectbox(
                "Regulator",
                regulator_list,
                index=regulator_idx,
                help="Which regulator issued this guidance?"
            )

        elif manual_category == "regulation":
            parent_act = st.selectbox(
                "Parent Act",
                ["Bank Act", "PCMLTFA", "PIPEDA"],
                help="Which act does this regulation fall under?"
            )

        elif manual_category == "policy":
            # Pre-fill from Bronze path if available
            default_company = selected_bronze.get("company_id", "")
            company_id = st.text_input(
                "Company ID",
                value=default_company,
                placeholder="e.g., acme_corp",
                help="Unique identifier for your organization"
            )

    st.markdown("---")

    # Process button
    st.markdown("### 🚀 Step 4: Process Bronze → Silver")

    st.info("📦 This will parse the clean Bronze text directly into structured Silver sections (no PDF re-extraction)")

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        process_button = st.button("▶️ Process Bronze", type="primary", use_container_width=True)

    if process_button:
        with st.spinner("Processing Bronze text file..."):
            try:
                # Create progress container
                progress_container = st.container()

                with progress_container:
                    st.markdown("### 📊 Processing Status")

                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Step 1: Load Bronze
                    status_text.text("Step 1/2: Reading Bronze text file...")
                    progress_bar.progress(50)

                    # Process Bronze file
                    result = pipeline.process_document(
                        pdf_path=bronze_file_path,  # Pass .txt path
                        document_type=doc_type,
                        jurisdiction=jurisdiction,
                        manual_category=manual_category,
                        regulator=regulator,
                        parent_act=parent_act,
                        company_id=company_id,
                    )

                    progress_bar.progress(100)
                    status_text.text("✅ Processing complete!")

                # Display results
                st.success("✅ Bronze file processed successfully!")

                st.markdown("### 📋 Results Summary")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Document ID", result['document_id'])
                with col2:
                    st.metric("Category", result['category'].upper())
                with col3:
                    st.metric("Total Characters", f"{result['total_chars']:,}")
                with col4:
                    st.metric("Sections Extracted", result['sections_count'])

                # Show category-specific info
                if result.get('regulator'):
                    st.info(f"📊 Regulator: **{result['regulator']}**")
                elif result.get('parent_act'):
                    st.info(f"📜 Parent Act: **{result['parent_act']}**")
                elif result.get('company_id'):
                    st.info(f"🏢 Company ID: **{result['company_id']}**")

                # Show locations
                st.markdown("### 📁 Storage Locations")

                st.markdown(f"""
                **Bronze Layer (source):**
                ```
                {bronze_file_path}
                ```

                **Silver Layer (output):**
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
                1. 🔷 **View Silver Layer** to browse all structured sections
                2. ⬅️ Go to the sidebar to explore your processed documents
                """)

            except Exception as e:
                st.error(f"❌ Error processing Bronze file: {str(e)}")
                st.exception(e)

else:
    # Instructions
    st.info("""
    👆 **Upload a PDF to get started**

    Supported documents:
    - 📜 Acts and Regulations
    - 📋 Guidelines and Frameworks
    - 📄 Policies and Standards

    The system uses **Adobe PDF Services** for:
    1. High-accuracy text extraction (95-99% accuracy)
    2. Automatic table detection
    3. Built-in OCR for scanned documents
    4. Structure-aware parsing

    Processing steps:
    1. Extract text using Adobe PDF Services
    2. Segment into structured sections
    3. Save to Bronze and Silver layers
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