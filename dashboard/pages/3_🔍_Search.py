"""
Semantic Search Page

Search across all regulatory documents using semantic similarity.
Powered by FAISS vector search and sentence-transformers.
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from search.semantic_search import SemanticSearchEngine

# Page config
st.set_page_config(
    page_title="Semantic Search",
    page_icon="🔍",
    layout="wide",
)

# Custom CSS
st.markdown("""
<style>
    .search-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }

    .result-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .result-score {
        background: #4CAF50;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
    }

    .result-category {
        background: #2196F3;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
        margin-left: 0.5rem;
    }

    .result-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #333;
        margin: 0.5rem 0;
    }

    .result-body {
        color: #666;
        line-height: 1.6;
        margin-top: 0.5rem;
    }

    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="search-header">
    <h1 style="margin:0;">🔍 Semantic Search</h1>
    <p style="margin:0.5rem 0 0 0; opacity:0.9;">Search across all regulatory documents using AI-powered semantic similarity</p>
</div>
""", unsafe_allow_html=True)

# Initialize search engine (cached)
@st.cache_resource
def get_search_engine():
    """Load search engine (cached)."""
    # Get absolute path to index (relative to project root)
    project_root = Path(__file__).parent.parent.parent
    index_path = project_root / "storage" / "vector_db" / "covenant.index"

    try:
        return SemanticSearchEngine(index_path=str(index_path))
    except FileNotFoundError as e:
        st.error(f"❌ {e}")
        st.info("💡 Run `python3 generate_embeddings.py` from the project root to create the search index")
        st.markdown(f"**Looking for:** `{index_path}`")
        st.stop()

engine = get_search_engine()

# Display stats
stats = engine.get_stats()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-box">
        <h3 style="margin:0;">{stats['total_sections']:,}</h3>
        <p style="margin:0.25rem 0 0 0; opacity:0.9;">Sections Indexed</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-box">
        <h3 style="margin:0;">{stats['embedding_dimension']}</h3>
        <p style="margin:0.25rem 0 0 0; opacity:0.9;">Embedding Dimension</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-box">
        <h3 style="margin:0;">{stats['index_type']}</h3>
        <p style="margin:0.25rem 0 0 0; opacity:0.9;">Index Type</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-box">
        <h3 style="margin:0;">{stats['metric'].upper()}</h3>
        <p style="margin:0.25rem 0 0 0; opacity:0.9;">Similarity Metric</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Search interface
st.markdown("### 🔎 Search Query")

col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "Enter your search query",
        placeholder="e.g., What are the customer due diligence requirements?",
        label_visibility="collapsed",
    )

with col2:
    search_button = st.button("🔍 Search", type="primary", use_container_width=True)

# Advanced options (collapsible)
with st.expander("⚙️ Advanced Options"):
    col1, col2, col3 = st.columns(3)

    with col1:
        top_k = st.slider("Number of results", min_value=1, max_value=50, value=10)

    with col2:
        score_threshold = st.slider(
            "Minimum similarity score",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
            help="Filter results below this similarity score"
        )

    with col3:
        category_filter = st.selectbox(
            "Filter by category",
            ["All", "act", "regulation", "guidance", "policy"],
        )
        if category_filter == "All":
            category_filter = None

# Perform search
if search_button and query:
    with st.spinner("Searching..."):
        results = engine.search(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            category_filter=category_filter,
        )

    st.markdown("---")

    # Results summary
    st.markdown(f"### 📊 Results ({len(results)} found)")

    if not results:
        st.warning("No results found. Try adjusting your query or lowering the similarity threshold.")
    else:
        # Export options
        col1, col2, col3 = st.columns([4, 1, 1])

        with col2:
            # Export as JSON
            results_json = json.dumps(results, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 JSON",
                data=results_json,
                file_name=f"search_results_{query[:20]}.json",
                mime="application/json",
            )

        with col3:
            # Export as CSV
            df = pd.DataFrame([{
                "Score": r["score"],
                "Category": r["category"],
                "Section": r["section_number"],
                "Title": r["title"],
                "Body": r["body"][:200],
                "Document": r["document_id"],
            } for r in results])

            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 CSV",
                data=csv,
                file_name=f"search_results_{query[:20]}.csv",
                mime="text/csv",
            )

        # Display results
        for i, result in enumerate(results, 1):
            with st.container():
                # Score and category badges
                col1, col2 = st.columns([6, 1])

                with col1:
                    st.markdown(f"""
                    <div style="margin-bottom: 0.5rem;">
                        <span class="result-score">Score: {result['score']:.4f}</span>
                        <span class="result-category">{result['category'].upper()}</span>
                    </div>
                    """, unsafe_allow_html=True)

                # Result card
                with st.expander(
                    f"**{i}. Section {result['section_number']}: {result['title'][:80]}{'...' if len(result['title']) > 80 else ''}**",
                    expanded=(i <= 3)  # Expand first 3 results
                ):
                    # Metadata
                    st.markdown(f"**Document:** `{result['document_id']}`")
                    st.markdown(f"**Jurisdiction:** {result['jurisdiction']}")
                    st.markdown(f"**Section ID:** `{result['section_id']}`")

                    st.markdown("---")

                    # Body text
                    st.markdown("**Content:**")
                    st.markdown(f"<div class='result-body'>{result['body']}</div>", unsafe_allow_html=True)

                    # Metadata toggle (using checkbox instead of nested expander)
                    st.markdown("---")
                    show_metadata = st.checkbox(
                        "🔍 Show Full Metadata",
                        key=f"metadata_{i}_{result['section_id']}"
                    )

                    if show_metadata:
                        st.json(result["metadata"])

        # Pagination info
        if len(results) == top_k:
            st.info(f"💡 Showing top {top_k} results. Increase 'Number of results' in Advanced Options to see more.")

elif search_button and not query:
    st.warning("⚠️ Please enter a search query")

# Instructions
if not search_button or not query:
    st.markdown("---")
    st.markdown("### 💡 Search Tips")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Query Examples:**
        - "What are the KYC requirements for financial institutions?"
        - "Money laundering reporting obligations"
        - "Customer due diligence procedures"
        - "Terrorist financing prevention measures"
        - "Record keeping requirements for MSBs"
        """)

    with col2:
        st.markdown("""
        **Search Features:**
        - 🎯 **Semantic Search**: Finds conceptually similar content, not just keywords
        - 📊 **Relevance Scoring**: Results ranked by similarity (0-1)
        - 🏷️ **Category Filtering**: Filter by act, regulation, guidance, or policy
        - 💾 **Export**: Download results as JSON or CSV
        - 📖 **Context**: View full section content and metadata
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; opacity: 0.7; font-size: 0.9rem;">
    Powered by FAISS + sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
</div>
""", unsafe_allow_html=True)