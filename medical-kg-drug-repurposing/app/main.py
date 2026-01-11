"""
Medical Knowledge Graph - Drug Repurposing Dashboard
Interactive Streamlit dashboard for exploring GNN predictions.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Page config
st.set_page_config(
    page_title="Drug Repurposing Dashboard",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("# 💊 Navigation")
    st.markdown("---")
    st.markdown("""
    ### About This Dashboard

    This interactive dashboard showcases a **Graph Neural Network (GNN)**
    model for drug repurposing built on a medical knowledge graph.

    **Key Features:**
    - 📊 Explore 1,514 biomedical entities
    - 🔗 Navigate 663 drug-disease relationships
    - 🎯 Browse 100 novel predictions
    - 🔬 View literature validation results
    - 📈 Analyze model performance

    **Navigate using the pages above** ↑
    """)

    st.markdown("---")
    st.markdown("""
    ### Tech Stack
    - GraphSAGE GNN (PyTorch Geometric)
    - Neo4j Graph Database
    - BC5CDR NER Model
    - PubMed API Validation
    """)

# Main content
st.markdown('<div class="main-header">💊 Drug Repurposing Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Discovering Novel Therapeutic Opportunities with Graph Neural Networks</div>', unsafe_allow_html=True)

st.markdown("---")

# Quick start section
st.markdown("## 🚀 Quick Start")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📊 Explore Data
    Navigate to **Graph Explorer** to visualize the knowledge graph and
    browse drug-disease relationships extracted from PubMed literature.
    """)

with col2:
    st.markdown("""
    ### 🎯 View Predictions
    Check out **Predictions** to explore 100 novel drug repurposing
    candidates identified by our GNN model.
    """)

with col3:
    st.markdown("""
    ### 📈 Model Performance
    Visit **Model Insights** to analyze training metrics, evaluation
    results, and understand model behavior.
    """)

st.markdown("---")

# Project overview
st.markdown("## 📖 Project Overview")

st.markdown("""
This portfolio project demonstrates a complete machine learning pipeline for **drug repurposing**
using Graph Neural Networks (GNNs). The project combines:

1. **Data Collection**: 924 PubMed abstracts on Alzheimer's, diabetes, and cardiovascular disease
2. **NLP Pipeline**: Extracted 1,514 entities and 666 relationships using BC5CDR model
3. **Knowledge Graph**: Built graph database in Neo4j with Drug and Disease nodes
4. **GNN Training**: Trained GraphSAGE model achieving **0.8693 test AUC** (16% above target)
5. **Prediction**: Generated 100 high-confidence novel drug-disease predictions
6. **Validation**: Classified predictions using PubMed literature search

### 🎯 Key Results

- **Test AUC**: 0.8693 (target: 0.75)
- **Precision@10**: 1.0000 (perfect!)
- **Precision@20**: 1.0000
- **Novel Predictions**: Identified multiple candidates with no existing literature

### 🔬 Scientific Impact

The model discovered **novel therapeutic opportunities** by learning from graph structure.
Top candidates include repurposing existing antibiotics for cancer treatment and
anti-inflammatory uses - predictions with biological plausibility but no prior research.
""")

st.markdown("---")

# Footer
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>Medical Knowledge Graph Drug Repurposing Project</strong></p>
    <p>Built with PyTorch Geometric, Neo4j, and Streamlit | 2025</p>
</div>
""", unsafe_allow_html=True)
