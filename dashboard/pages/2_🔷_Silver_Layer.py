"""
Silver Layer Viewer

Browse and search structured sections from processed documents.
"""

import streamlit as st
import json
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="Silver Layer", page_icon="🔷", layout="wide")

st.title("🔷 Silver Layer - Structured Sections")
st.markdown("Browse parsed sections from regulatory documents")

# Get all documents in silver
silver_path = Path("storage/silver")

if not silver_path.exists():
    st.warning("⚠️ No documents found in Silver layer. Upload a document first!")
    st.stop()

# Get list of documents
documents = [d for d in silver_path.iterdir() if d.is_dir()]

if not documents:
    st.info("📭 No documents found. Upload a document to get started!")
    st.stop()

# Document selector
st.markdown("### 📂 Select Document")

doc_names = [d.name for d in documents]
selected_doc = st.selectbox("Document", doc_names)

if selected_doc:
    # Load document
    doc_path = silver_path / selected_doc
    sections_file = doc_path / "sections.json"
    metadata_file = doc_path / "metadata.json"

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

        # Pagination
        items_per_page = st.selectbox("Sections per page", [10, 25, 50, 100], index=0)
        total_pages = (len(filtered_sections) - 1) // items_per_page + 1

        if total_pages > 0:
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)

            start_idx = (page - 1) * items_per_page
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
                    file_name=f"{selected_doc}_sections.json",
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
                    file_name=f"{selected_doc}_sections.csv",
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
                    file_name=f"{selected_doc}_sections.txt",
                    mime="text/plain"
                )

    else:
        st.error(f"❌ Sections file not found for {selected_doc}")

# Stats sidebar
with st.sidebar:
    st.markdown("### 📊 Statistics")

    if documents:
        total_docs = len(documents)
        total_sections = 0

        for doc in documents:
            sections_file = doc / "sections.json"
            if sections_file.exists():
                with open(sections_file, 'r') as f:
                    total_sections += len(json.load(f))

        st.metric("Total Documents", total_docs)
        st.metric("Total Sections", total_sections)

        if total_sections > 0:
            st.metric("Avg Sections/Doc", round(total_sections / total_docs))