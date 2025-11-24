"""
Silver Layer Viewer

Browse and search structured sections from processed documents.
"""

import streamlit as st
import json
from pathlib import Path
import pandas as pd
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="Silver Layer", page_icon="🔷", layout="wide")

st.title("🔷 Silver Layer - Structured Sections")
st.markdown("Browse parsed sections from regulatory documents")

# Get project root and silver path (main storage directory)
project_root = Path(__file__).parent.parent.parent
silver_path = project_root / "storage" / "silver"

if not silver_path.exists():
    st.warning("⚠️ No documents found in Silver layer. Upload a document first!")
    st.stop()

# Get all documents across all taxonomy categories
def find_all_documents(base_path):
    """Recursively find all document directories with sections.json"""
    documents = []

    # Check taxonomy categories
    categories = ["acts", "regulations", "guidance", "company_policies"]

    for category in categories:
        category_path = base_path / category
        if category_path.exists():
            # For guidance, need to check regulator subdirectories
            if category == "guidance":
                for regulator_dir in category_path.iterdir():
                    if regulator_dir.is_dir():
                        for doc_dir in regulator_dir.iterdir():
                            if doc_dir.is_dir() and (doc_dir / "sections.json").exists():
                                documents.append({
                                    "path": doc_dir,
                                    "name": doc_dir.name,
                                    "category": category,
                                    "regulator": regulator_dir.name,
                                    "display_name": doc_dir.name
                                })
            # For company_policies, check company subdirectories
            elif category == "company_policies":
                for company_dir in category_path.iterdir():
                    if company_dir.is_dir():
                        for doc_dir in company_dir.iterdir():
                            if doc_dir.is_dir() and (doc_dir / "sections.json").exists():
                                documents.append({
                                    "path": doc_dir,
                                    "name": doc_dir.name,
                                    "category": category,
                                    "company_id": company_dir.name,
                                    "display_name": doc_dir.name
                                })
            # For acts and regulations, direct subdirectories
            else:
                for doc_dir in category_path.iterdir():
                    if doc_dir.is_dir() and (doc_dir / "sections.json").exists():
                        documents.append({
                            "path": doc_dir,
                            "name": doc_dir.name,
                            "category": category,
                            "display_name": doc_dir.name
                        })

    # Also check for old flat structure documents (backward compatibility)
    for item in base_path.iterdir():
        if item.is_dir() and item.name not in categories and (item / "sections.json").exists():
            documents.append({
                "path": item,
                "name": item.name,
                "category": "legacy",
                "display_name": item.name
            })

    return documents

documents = find_all_documents(silver_path)

if not documents:
    st.info("📭 No documents found. Upload a document to get started!")
    st.stop()

# Document selector with category grouping
st.markdown("### 📂 Select Document")

# Sort by category, then by name
documents.sort(key=lambda x: (x["category"], x["name"]))

doc_display_names = [d["display_name"] for d in documents]
selected_idx = st.selectbox("Document", range(len(documents)), format_func=lambda i: doc_display_names[i])
selected_doc_info = documents[selected_idx]

if selected_doc_info:
    # Load document
    doc_path = selected_doc_info["path"]
    sections_file = doc_path / "sections.json"
    metadata_file = doc_path / "metadata.json"

    # Show category badge
    category_emoji = {
        "acts": "📜",
        "regulations": "📋",
        "guidance": "📊",
        "company_policies": "🏢",
        "legacy": "📁"
    }
    st.info(f"{category_emoji.get(selected_doc_info['category'], '📄')} **Category:** {selected_doc_info['category'].replace('_', ' ').title()}")

    # Load sections
    if sections_file.exists():
        with open(sections_file, 'r', encoding='utf-8') as f:
            sections = json.load(f)

        # Load metadata
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        # Display metadata
        st.markdown("### 📋 Document Metadata")

        # Row 1: Basic Info
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Sections", len(sections))
        with col2:
            st.metric("Document Type", metadata.get('document_type', 'Unknown'))
        with col3:
            st.metric("Jurisdiction", metadata.get('jurisdiction', 'Unknown'))
        with col4:
            total_chars = sum(len(s['body']) for s in sections)
            st.metric("Total Characters", f"{total_chars:,}")

        # Row 2: Extraction & OCR Details
        st.markdown("#### 🔍 Extraction Details")
        col1, col2, col3, col4 = st.columns(4)
        
        # Extraction Method
        extraction_method = metadata.get('extraction_method', 'Unknown')
        with col1:
            st.metric("Extraction Method", extraction_method)

        # OCR Status & Confidence
        needs_ocr = metadata.get('needs_ocr', False)
        avg_confidence = metadata.get('avg_confidence', 0)
        
        with col2:
            st.metric("OCR Applied", "Yes" if needs_ocr else "No")
        
        with col3:
            if needs_ocr:
                st.metric("OCR Confidence", f"{avg_confidence:.1f}%")
            else:
                st.metric("OCR Confidence", "N/A")

        # Preprocessing Status
        preprocessing = metadata.get('preprocessing', 'None')
        with col4:
             st.metric("Preprocessing", preprocessing if needs_ocr else "N/A")

        st.markdown("---")

        # Search and filter
        st.markdown("### 🔍 Search & Filter")

        col1, col2 = st.columns([3, 1])

        with col1:
            search_query = st.text_input(
                "Search sections",
                placeholder="e.g., bank, license, shall not...",
                help="Search in section titles and body text"
            )

        with col2:
            level_filter = st.multiselect(
                "Filter by Level",
                options=sorted(set(s['level'] for s in sections)),
                help="1=Part, 2=Division, 3=Section, 4=Subsection"
            )

        # Filter sections
        filtered_sections = sections

        if search_query:
            filtered_sections = [
                s for s in filtered_sections
                if search_query.lower() in s['title'].lower()
                or search_query.lower() in s['body'].lower()
            ]

        if level_filter:
            filtered_sections = [
                s for s in filtered_sections
                if s['level'] in level_filter
            ]

        st.info(f"📊 Showing {len(filtered_sections)} of {len(sections)} sections")

        st.markdown("---")

        # Display sections
        st.markdown("### 📖 Sections")

        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            items_per_page = st.selectbox("Sections per page", [10, 25, 50, 100], index=0)

        total_pages = max(1, (len(filtered_sections) - 1) // items_per_page + 1)

        # Initialize page state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1

        if total_pages > 0:
            # Page navigation buttons
            with col2:
                nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1, 1, 2, 1, 1])

                with nav_col1:
                    if st.button("⏮️ First", disabled=(st.session_state.current_page == 1)):
                        st.session_state.current_page = 1
                        st.rerun()

                with nav_col2:
                    if st.button("◀️ Prev", disabled=(st.session_state.current_page == 1)):
                        st.session_state.current_page -= 1
                        st.rerun()

                with nav_col3:
                    st.markdown(f"<div style='text-align: center; padding-top: 8px;'><b>Page {st.session_state.current_page} of {total_pages}</b></div>", unsafe_allow_html=True)

                with nav_col4:
                    if st.button("Next ▶️", disabled=(st.session_state.current_page == total_pages)):
                        st.session_state.current_page += 1
                        st.rerun()

                with nav_col5:
                    if st.button("Last ⏭️", disabled=(st.session_state.current_page == total_pages)):
                        st.session_state.current_page = total_pages
                        st.rerun()

            # Ensure current_page is within bounds BEFORE using it
            st.session_state.current_page = max(1, min(st.session_state.current_page, total_pages))

            with col3:
                # Jump to page
                jump_page = st.number_input("Jump to page", min_value=1, max_value=total_pages, value=st.session_state.current_page, key="page_jump")
                if jump_page != st.session_state.current_page:
                    st.session_state.current_page = jump_page
                    st.rerun()

            start_idx = (st.session_state.current_page - 1) * items_per_page
            end_idx = start_idx + items_per_page

            page_sections = filtered_sections[start_idx:end_idx]

            # Display sections
            for section in page_sections:
                with st.expander(
                    f"📄 Section {section['section_number']}: {section['title'][:80]}"
                    + ("..." if len(section['title']) > 80 else "")
                ):
                    # Section details
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f"**ID:** `{section['section_id']}`")
                    with col2:
                        st.markdown(f"**Level:** {section['level']}")
                    with col3:
                        st.markdown(f"**Characters:** {len(section['body'])}")

                    st.markdown("---")

                    # Title
                    st.markdown(f"**Title:** {section['title']}")

                    # Body
                    st.markdown("**Body:**")
                    st.text_area(
                        "Section text",
                        value=section['body'],
                        height=200,
                        key=f"body_{section['section_id']}",
                        label_visibility="collapsed"
                    )

                    # Metadata (no nested expander - just show directly)
                    if section.get('metadata'):
                        st.markdown("**Metadata:**")
                        st.json(section['metadata'], expanded=False)

            # Pagination info
            st.markdown(f"Showing sections {start_idx + 1} - {min(end_idx, len(filtered_sections))} of {len(filtered_sections)}")

        # Export options
        st.markdown("---")
        st.markdown("### 💾 Export")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Export as JSON
            if st.button("📄 Export as JSON"):
                json_str = json.dumps(filtered_sections, indent=2, ensure_ascii=False)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"{selected_doc_info['name']}_sections.json",
                    mime="application/json"
                )

        with col2:
            # Export as CSV
            if st.button("📊 Export as CSV"):
                # Convert to DataFrame
                df = pd.DataFrame([
                    {
                        'section_id': s['section_id'],
                        'section_number': s['section_number'],
                        'title': s['title'],
                        'body': s['body'],
                        'level': s['level'],
                    }
                    for s in filtered_sections
                ])
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{selected_doc_info['name']}_sections.csv",
                    mime="text/csv"
                )

        with col3:
            # Export as text
            if st.button("📝 Export as Text"):
                text_content = "\n\n".join([
                    f"Section {s['section_number']}: {s['title']}\n{s['body']}"
                    for s in filtered_sections
                ])
                st.download_button(
                    label="Download Text",
                    data=text_content,
                    file_name=f"{selected_doc_info['name']}_sections.txt",
                    mime="text/plain"
                )

    else:
        st.error(f"❌ Sections file not found for {selected_doc_info['name']}")

# Stats sidebar
with st.sidebar:
    st.markdown("### 📊 Statistics")

    if documents:
        total_docs = len(documents)
        total_sections = 0

        for doc_info in documents:
            sections_file = doc_info["path"] / "sections.json"
            if sections_file.exists():
                with open(sections_file, 'r') as f:
                    total_sections += len(json.load(f))

        st.metric("Total Documents", total_docs)
        st.metric("Total Sections", total_sections)

        if total_sections > 0:
            st.metric("Avg Sections/Doc", round(total_sections / total_docs))