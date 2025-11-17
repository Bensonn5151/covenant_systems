# Frontend Development Plan

Phased frontend development aligned with backend pipeline stages.

---

## Tech Stack Decision

### Option A: Streamlit (Recommended for MVP)
**Pros:**
- ✅ Fastest development (pure Python)
- ✅ No JavaScript required
- ✅ Built-in components (file upload, charts, etc.)
- ✅ Perfect for internal tools & demos
- ✅ Auto-reload on code changes
- ✅ Easy deployment

**Cons:**
- ❌ Not suitable for production user-facing apps
- ❌ Limited customization
- ❌ No offline support

**Best for:** MVP, internal testing, demos

---

### Option B: Next.js + React (Production)
**Pros:**
- ✅ Production-ready
- ✅ Full customization
- ✅ SEO-friendly
- ✅ Modern UI (Tailwind, shadcn/ui)
- ✅ TypeScript support
- ✅ API routes built-in

**Cons:**
- ❌ Slower development
- ❌ Requires JavaScript/TypeScript knowledge
- ❌ More complex deployment

**Best for:** Production, customer-facing apps

---

## Recommended Approach

**Phase 1-3: Streamlit** (fast iteration)
**Phase 4+: Migrate to Next.js** (production polish)

---

## Phase 1 Frontend: Document Ingestion UI

### Goal
Visualize Bronze → Silver pipeline in real-time

### Features

#### 1.1 PDF Upload
```
┌─────────────────────────────────────┐
│  📄 Upload Regulatory Document      │
├─────────────────────────────────────┤
│  Drag & drop PDF or click to browse│
│                                     │
│  ☑ Auto-detect bilingual layout    │
│  ☑ Apply OCR if needed              │
│                                     │
│  [Upload & Process]                 │
└─────────────────────────────────────┘
```

**Implementation:**
```python
import streamlit as st

uploaded_file = st.file_uploader("Upload PDF", type="pdf")
bilingual = st.checkbox("Bilingual PDF (English/French)", value=True)
apply_ocr = st.checkbox("Apply OCR if needed", value=True)

if st.button("Process Document"):
    # Call ingestion pipeline
    result = pipeline.process_document(
        pdf_path=uploaded_file,
        is_bilingual=bilingual
    )
```

#### 1.2 Processing Status
```
┌─────────────────────────────────────┐
│  ⏳ Processing: bank_act_canada.pdf │
├─────────────────────────────────────┤
│  ✓ Step 1: Extracting text          │
│  ✓ Step 2: OCR (skipped)             │
│  ⏳ Step 3: Segmenting sections...   │
│  ⭘ Step 4: Saving to storage         │
└─────────────────────────────────────┘
```

#### 1.3 Bronze Layer View
```
┌─────────────────────────────────────┐
│  📦 BRONZE LAYER                    │
├─────────────────────────────────────┤
│  Document ID: bank_act_canada       │
│  Pages: 245                         │
│  Characters: 782,450                │
│  Hash: a7f3d2e8...                  │
│                                     │
│  [View Raw Text] [View Metadata]    │
└─────────────────────────────────────┘
```

#### 1.4 Silver Layer View
```
┌─────────────────────────────────────┐
│  🔷 SILVER LAYER                    │
├─────────────────────────────────────┤
│  Sections: 1,087                    │
│  Document Type: Act                 │
│  Jurisdiction: Canada               │
│                                     │
│  📋 Sections:                       │
│  ├─ Section 1: Short Title          │
│  ├─ Section 2: Definitions          │
│  ├─ Section 3: Application          │
│  └─ ... (1,084 more)                │
│                                     │
│  [View Section] [Export JSON]       │
└─────────────────────────────────────┘
```

#### 1.5 Section Inspector
```
┌─────────────────────────────────────┐
│  Section 6: Restriction on Business│
├─────────────────────────────────────┤
│  ID: bank_act_canada_s006           │
│  Number: 6                          │
│  Level: 3 (Section)                 │
│  Characters: 87                     │
│                                     │
│  Body:                              │
│  "A bank shall not carry on         │
│   business as a bank, except in     │
│   accordance with this Act."        │
│                                     │
│  Metadata:                          │
│  - Jurisdiction: Canada             │
│  - Document Type: Act               │
│  - Parent: None                     │
└─────────────────────────────────────┘
```

**Pages:**
- `dashboard/pages/1_upload.py` - Document upload
- `dashboard/pages/2_bronze_viewer.py` - Raw text viewer
- `dashboard/pages/3_silver_viewer.py` - Section browser

---

## Phase 2 Frontend: Embeddings & Gold Layer

### Goal
Visualize embeddings and semantic clustering

### Features

#### 2.1 Embedding Status
```
┌─────────────────────────────────────┐
│  🌟 GOLD LAYER                      │
├─────────────────────────────────────┤
│  Model: all-MiniLM-L6-v2            │
│  Dimensions: 384                    │
│  Sections Embedded: 1,087           │
│                                     │
│  [Generate Embeddings]              │
│  [View FAISS Index]                 │
└─────────────────────────────────────┘
```

#### 2.2 Embedding Visualization
```
┌─────────────────────────────────────┐
│  📊 Embedding Clusters (t-SNE)      │
├─────────────────────────────────────┤
│         ·                           │
│      ·  · ·    Licensing            │
│         ·      ·                    │
│                    · · AML          │
│   · ·                ·              │
│  Governance    · ·                  │
│                                     │
│  [Hover for section details]        │
└─────────────────────────────────────┘
```

**Implementation:**
```python
import plotly.express as px
from sklearn.manifold import TSNE

# Reduce to 2D for visualization
embeddings_2d = TSNE(n_components=2).fit_transform(embeddings)

fig = px.scatter(
    x=embeddings_2d[:, 0],
    y=embeddings_2d[:, 1],
    hover_data=['section_id', 'title'],
    color='domain'
)
st.plotly_chart(fig)
```

**Pages:**
- `dashboard/pages/4_embeddings.py` - Embedding status
- `dashboard/pages/5_clustering.py` - Visual clusters

---

## Phase 3 Frontend: Retrieval Testing Interface

### Goal
Test semantic, lexical, and hybrid retrieval

### Features

#### 3.1 Query Interface
```
┌─────────────────────────────────────┐
│  🔍 Retrieval Testing                │
├─────────────────────────────────────┤
│  Query:                             │
│  ┌─────────────────────────────────┐│
│  │ Can a bank operate without a    ││
│  │ license?                        ││
│  └─────────────────────────────────┘│
│                                     │
│  Retrieval Mode:                    │
│  ⚫ Semantic  ○ BM25  ○ Hybrid       │
│                                     │
│  Top-K: [10]                        │
│  Threshold: [0.70]                  │
│                                     │
│  [Search]                           │
└─────────────────────────────────────┘
```

#### 3.2 Results View
```
┌─────────────────────────────────────┐
│  📋 Results (10 sections)           │
├─────────────────────────────────────┤
│  1. Section 6 | Score: 0.87         │
│     "A bank shall not carry on..."  │
│     [View Full] [Add to Context]    │
│                                     │
│  2. Section 14 | Score: 0.82        │
│     "No person shall carry on..."   │
│     [View Full] [Add to Context]    │
│                                     │
│  ... (8 more)                       │
└─────────────────────────────────────┘
```

#### 3.3 Comparison Mode
```
┌─────────────────────────────────────┐
│  ⚖️ Compare Retrieval Methods        │
├─────────────────────────────────────┤
│  Semantic  │  BM25     │  Hybrid    │
│  ─────────────────────────────────  │
│  Sec 6     │  Sec 6    │  Sec 6     │
│  (0.87)    │  (15.2)   │  (0.89)    │
│            │           │            │
│  Sec 14    │  Sec 5    │  Sec 14    │
│  (0.82)    │  (12.3)   │  (0.84)    │
│                                     │
│  Overlap: 70%                       │
└─────────────────────────────────────┘
```

**Pages:**
- `dashboard/pages/6_retrieval.py` - Query interface
- `dashboard/pages/7_comparison.py` - Method comparison

---

## Phase 4 Frontend: Compliance Evaluation UI

### Goal
Full compliance checking interface

### Features

#### 4.1 Policy Upload
```
┌─────────────────────────────────────┐
│  📝 Evaluate Policy Compliance      │
├─────────────────────────────────────┤
│  Upload Internal Policy:            │
│  [Choose File] privacy_policy.pdf   │
│                                     │
│  Or paste text:                     │
│  ┌─────────────────────────────────┐│
│  │ We collect user data for...     ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Evaluate Against:                  │
│  ☑ PIPEDA                           │
│  ☑ GDPR                             │
│  ☐ CCPA                             │
│                                     │
│  [Evaluate]                         │
└─────────────────────────────────────┘
```

#### 4.2 Compliance Dashboard
```
┌─────────────────────────────────────┐
│  ✅ Compliance Score: 78%           │
├─────────────────────────────────────┤
│  Status by Domain:                  │
│                                     │
│  Privacy          ████████░░  82%   │
│  Consent          ██████░░░░  65%   │
│  Data Security    █████████░  91%   │
│  Breach Notice    ████░░░░░░  45%   │
│                                     │
│  ⚠️  3 Critical Gaps                │
│  ⚠️  5 Medium Risks                 │
│  ✓  12 Compliant Areas              │
└─────────────────────────────────────┘
```

#### 4.3 Gap Analysis
```
┌─────────────────────────────────────┐
│  ⚠️ Critical Gap: Breach Notification│
├─────────────────────────────────────┤
│  Requirement (PIPEDA 10.1):         │
│  "Organizations must notify          │
│   individuals of breaches..."       │
│                                     │
│  Your Policy:                       │
│  ❌ No mention of breach notification│
│                                     │
│  Recommendation:                    │
│  Add clause: "In the event of a     │
│  data breach affecting personal     │
│  information, we will notify..."    │
│                                     │
│  [Accept] [Edit] [Dismiss]          │
└─────────────────────────────────────┘
```

#### 4.4 Evidence Viewer
```
┌─────────────────────────────────────┐
│  📜 Evidence Chain                  │
├─────────────────────────────────────┤
│  Claim: "User consent is obtained"  │
│                                     │
│  Evidence:                          │
│  1. Policy Section 3.2              │
│     "Users must opt-in..."          │
│     Relevance: 0.92                 │
│                                     │
│  2. PIPEDA Section 6.1 (Cited)      │
│     "Consent must be meaningful"    │
│     Relevance: 0.88                 │
│                                     │
│  Knowledge Graph:                   │
│  Policy 3.2 → implements → PIPEDA 6.1│
│             → cites → GDPR Art. 7   │
└─────────────────────────────────────┘
```

**Pages:**
- `dashboard/pages/8_evaluate.py` - Compliance evaluation
- `dashboard/pages/9_gaps.py` - Gap analysis
- `dashboard/pages/10_evidence.py` - Evidence viewer

---

## Phase 5 Frontend: Knowledge Graph Visualization

### Goal
Interactive KG explorer

### Features

#### 5.1 Graph Viewer
```
┌─────────────────────────────────────┐
│  🕸️ Knowledge Graph Explorer        │
├─────────────────────────────────────┤
│                                     │
│      PIPEDA ────cites────> GDPR     │
│        │                    │       │
│    requires               requires  │
│        │                    │       │
│        ↓                    ↓       │
│   Internal Policy ← implements      │
│                                     │
│  [Focus] [Expand] [Export]          │
└─────────────────────────────────────┘
```

**Implementation:**
```python
import networkx as nx
import plotly.graph_objects as go

# Build graph
G = nx.DiGraph()
G.add_edges_from([(edge['from'], edge['to']) for edge in edges])

# Plot
pos = nx.spring_layout(G)
fig = go.Figure(data=[...])
st.plotly_chart(fig)
```

**Pages:**
- `dashboard/pages/11_knowledge_graph.py` - Graph explorer

---

## Streamlit Implementation Plan

### Project Structure
```
dashboard/
├── app.py                      # Main entry point
├── pages/
│   ├── 1_upload.py            # Phase 1
│   ├── 2_bronze_viewer.py
│   ├── 3_silver_viewer.py
│   ├── 4_embeddings.py        # Phase 2
│   ├── 5_clustering.py
│   ├── 6_retrieval.py         # Phase 3
│   ├── 7_comparison.py
│   ├── 8_evaluate.py          # Phase 4
│   ├── 9_gaps.py
│   ├── 10_evidence.py
│   └── 11_knowledge_graph.py  # Phase 5
├── components/
│   ├── header.py
│   ├── sidebar.py
│   └── metrics.py
└── utils/
    ├── data_loader.py
    └── visualizations.py
```

### Installation
```bash
pip install streamlit plotly pandas networkx scikit-learn
```

### Running
```bash
streamlit run dashboard/app.py
```

---

## Timeline

| Phase | Backend | Frontend | Total |
|-------|---------|----------|-------|
| 1 | 4 hours | 2 hours | 6 hours |
| 2 | 3 hours | 2 hours | 5 hours |
| 3 | 3 hours | 2 hours | 5 hours |
| 4 | 4 hours | 3 hours | 7 hours |
| 5 | 2 hours | 2 hours | 4 hours |

**Total MVP:** ~27 hours

---

## Next Steps

1. **Create basic Streamlit app** (30 min)
2. **Add Phase 1 UI** (2 hours)
   - Document upload
   - Bronze/Silver viewers
3. **Test with bank_act_canada.pdf**
4. **Iterate based on feedback**

Ready to build the Phase 1 frontend?