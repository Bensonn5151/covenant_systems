"""
Covenant Systems - Streamlit Dashboard

Main entry point for the Streamlit UI.
"""

import streamlit as st
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Covenant Compliance Engine",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f9fafb;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
    }
    .success-box {
        background-color: #d1fae5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10b981;
    }
    .warning-box {
        background-color: #fef3c7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f59e0b;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">⚖️ Covenant Compliance Engine</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-Powered Regulatory Intelligence Platform</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x50/1f2937/ffffff?text=Covenant", use_column_width=True)
    st.markdown("---")

    st.markdown("### 📊 System Status")

    # Check if storage exists
    bronze_path = Path("storage/bronze")
    silver_path = Path("storage/silver")
    gold_path = Path("storage/gold")

    st.metric("Documents (Bronze)", len(list(bronze_path.glob("*"))) if bronze_path.exists() else 0)
    st.metric("Documents (Silver)", len(list(silver_path.glob("*"))) if silver_path.exists() else 0)
    st.metric("Documents (Gold)", len(list(gold_path.glob("*"))) if gold_path.exists() else 0)

    st.markdown("---")
    st.markdown("### 📖 Quick Links")
    st.markdown("""
    - [Documentation](docs/DATA_STANDARDS.md)
    - [Pipeline Stages](docs/PIPELINE_STAGES.md)
    - [Frontend Plan](docs/FRONTEND_PLAN.md)
    """)

# Main content
st.markdown("## 🚀 Welcome")

st.markdown("""
This dashboard provides an interactive interface for the Covenant Compliance Engine.

**Current Status:** Phase 1 - Bronze → Silver Pipeline

Navigate using the sidebar to:
- 📤 **Upload Documents**: Ingest new regulatory PDFs
- 📦 **Bronze Layer**: View raw extracted text
- 🔷 **Silver Layer**: Browse structured sections
""")

# System Overview
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="metric-card">
        <h3>📦 Bronze Layer</h3>
        <p>Raw document storage</p>
        <ul>
            <li>PDF extraction</li>
            <li>OCR processing</li>
            <li>Text preservation</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <h3>🔷 Silver Layer</h3>
        <p>Structured sections</p>
        <ul>
            <li>Section segmentation</li>
            <li>Metadata inference</li>
            <li>Hierarchy detection</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <h3>🌟 Gold Layer</h3>
        <p>Semantic intelligence</p>
        <ul>
            <li>Embeddings (Coming Soon)</li>
            <li>Semantic labels</li>
            <li>RAG-ready vectors</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Quick Start
st.markdown("## ⚡ Quick Start")

st.markdown("""
1. **Upload a Document**: Go to "📤 Upload" in the sidebar
2. **View Bronze**: Check the raw extracted text
3. **Explore Silver**: Browse the structured sections
4. **Test Retrieval**: (Coming in Phase 3)
5. **Evaluate Compliance**: (Coming in Phase 4)
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6b7280; font-size: 0.9rem;'>
    Covenant Systems v0.1.0-mvp | Built with Streamlit
</div>
""", unsafe_allow_html=True)