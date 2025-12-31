# Medical Knowledge Graph: Drug Repurposing Explorer

> **Educational Project**: A student-led exploration of Graph Neural Networks and biomedical knowledge graphs for learning modern ML/AI techniques

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.0+-green.svg)](https://neo4j.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## ⚠️ Important Notice

**This is a personal learning and portfolio project, NOT a rigorous scientific research effort.**

This project is designed to:
- **Learn** modern ML/AI techniques (Graph Neural Networks, NLP, Knowledge Graphs)
- **Demonstrate** end-to-end software engineering skills
- **Showcase** technical capabilities for internship/job applications
- **Explore** biomedical informatics as an interesting problem domain

**NOT intended for:**
- ❌ Clinical decision making
- ❌ Medical research or drug discovery
- ❌ Production deployment in healthcare settings
- ❌ Peer-reviewed scientific publication

The biomedical domain provides a rich, real-world dataset to learn GNN and knowledge graph techniques that transfer to many other applications (recommendation systems, social networks, fraud detection, etc.).

---

## 🎯 Project Overview

Drug development traditionally takes 10+ years and costs $2.6 billion. This project explores how **Graph Neural Networks** and **biomedical knowledge graphs** could be used to identify new uses for existing FDA-approved drugs.

This is a **proof-of-concept implementation** to learn and demonstrate:
1. How to extract structured information from unstructured text using NLP
2. How to build and query knowledge graphs with Neo4j
3. How to apply Graph Neural Networks for link prediction
4. How to build end-to-end ML pipelines from data collection to web deployment

### What This Project Demonstrates

**Technical Skills:**
- REST API integration (PubMed, PubChem)
- Biomedical NLP using SciSpacy and transformers
- Graph database design and Cypher queries
- PyTorch and PyTorch Geometric for GNNs
- Full ML pipeline (data → model → evaluation → deployment)
- Interactive web applications with Streamlit

**Software Engineering:**
- Clean, modular code architecture
- Data pipeline development
- Version control with Git
- Documentation and testing
- End-to-end feature ownership

---

## 🏗️ System Architecture

This section provides the complete technical architecture of the solution.

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES (External APIs)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  PubMed API              PubChem API                                         │
│  (Research Papers)       (Drug Properties)                                   │
└──────┬──────────────────────┬────────────────────────────────────────────────┘
       │                      │
       ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATA COLLECTION                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  collect_pubmed.py  ──▶  pubmed_abstracts.json (924 papers)                 │
│  collect_pubchem.py ──▶  pubchem_drugs.csv (107 drugs)                      │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      NLP PROCESSING & ENTITY EXTRACTION                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  extract_entities.py       ──▶  entities.csv (1,514 entities)               │
│  extract_relationships.py  ──▶  relationships.csv (666 relationships)       │
│  create_knowledge_base.py  ──▶  knowledge_base.json                         │
│                                                                               │
│  Tools: BC5CDR NER Model, Pattern Matching, Co-occurrence Analysis          │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE GRAPH CONSTRUCTION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  load_to_neo4j.py  ──▶  Neo4j Graph Database                                │
│                                                                               │
│  Structure:                                                                  │
│    • 1,514 Nodes: 718 Drugs + 796 Diseases                                  │
│    • 663 TREATS Relationships                                                │
│    • Constraints, Indexes, 60+ Cypher Queries                               │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   MACHINE LEARNING & LINK PREDICTION                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  export_graph_data.py       ──▶  graph_data.pt (PyTorch format)             │
│  prepare_training_data.py   ──▶  train/val/test splits (70/15/15)           │
│  train_gnn.py               ──▶  best_model.pt (GraphSAGE, 7K params)       │
│  evaluate_gnn.py            ──▶  test_metrics.json (AUC: 0.8693 ✓)          │
│  generate_predictions.py    ──▶  novel_predictions.csv (100 candidates)     │
│                                                                               │
│  Model: GraphSAGE GNN | Device: M1 GPU (MPS) | Epochs: 66                   │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 VALIDATION & INTERACTIVE DASHBOARD                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  validate_predictions.py  ──▶  validation_report.csv (13 novel, 5 emerging) │
│  streamlit run app        ──▶  Interactive Web Dashboard (4 pages)          │
│                                                                               │
│  Features: Predictions Browser, Model Insights, Graph Explorer              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Pipeline: Script → File Flow

```
PHASE 1: Data Collection
=========================
collect_pubmed.py
    └─▶ data/raw/pubmed_abstracts.json
         • 924 research papers
         • JSON format with title, abstract, metadata

collect_pubchem.py
    └─▶ data/raw/pubchem_drugs.csv
         • 107 FDA-approved drugs
         • Molecular formula, SMILES, properties

────────────────────────────────────────────────────────────

PHASE 2: NLP Processing & Entity Extraction
============================================
extract_entities.py
    ├─◀ data/raw/pubmed_abstracts.json
    └─▶ data/processed/entities.csv
         • 1,514 biomedical entities
         • 718 Drugs (CHEMICAL) + 796 Diseases (DISEASE)
         • Frequency counts, paper references

extract_relationships.py
    ├─◀ data/raw/pubmed_abstracts.json
    ├─◀ data/processed/entities.csv
    └─▶ data/processed/relationships.csv
         • 666 drug-disease relationships
         • Confidence scores, evidence types
         • Pattern matching + co-occurrence

create_knowledge_base.py
    ├─◀ data/processed/entities.csv
    ├─◀ data/processed/relationships.csv
    └─▶ data/processed/knowledge_base.json
         • Combined structured knowledge base
         • Validated referential integrity

────────────────────────────────────────────────────────────

PHASE 3: Knowledge Graph Construction
======================================
load_to_neo4j.py
    ├─◀ data/processed/entities.csv
    ├─◀ data/processed/relationships.csv
    └─▶ Neo4j Graph Database
         • 1,514 nodes (:Drug, :Disease)
         • 663 :TREATS relationships
         • Batch loading, constraints, indexes
         • 2.54 seconds load time

cypher_queries.cypher
    └─▶ 60+ pre-written Cypher queries
         • Graph exploration
         • Network analysis
         • Drug repurposing insights

────────────────────────────────────────────────────────────

PHASE 4: Machine Learning & Link Prediction
============================================
export_graph_data.py
    ├─◀ Neo4j Graph Database
    └─▶ data/processed/graph_data.pt
         • PyTorch Geometric format
         • Node features: [1514, 2]
         • Edge index: [2, 663]
         • Z-score normalized features

prepare_training_data.py
    ├─◀ data/processed/graph_data.pt
    └─▶ data/processed/train_data.pt (928 edges: 464 pos, 464 neg)
    └─▶ data/processed/val_data.pt   (198 edges: 99 pos, 99 neg)
    └─▶ data/processed/test_data.pt  (200 edges: 100 pos, 100 neg)
         • 70/15/15 split
         • 1:1 negative sampling

train_gnn.py
    ├─◀ data/processed/train_data.pt
    ├─◀ data/processed/val_data.pt
    └─▶ models/checkpoints/best_model.pt
    └─▶ data/results/training_history.json
         • GraphSAGE architecture (7,073 params)
         • 66 epochs, early stopping
         • Best val AUC: 0.8601

evaluate_gnn.py
    ├─◀ models/checkpoints/best_model.pt
    ├─◀ data/processed/test_data.pt
    └─▶ data/results/test_metrics.json
    └─▶ data/visualizations/roc_curve.png
    └─▶ data/visualizations/pr_curve.png
         • Test AUC: 0.8693 ✓
         • Precision@10: 1.0000 ✓
         • Precision@20: 1.0000 ✓

generate_predictions.py
    ├─◀ models/checkpoints/best_model.pt
    ├─◀ data/processed/graph_data.pt
    └─▶ data/results/novel_predictions.csv
         • Top 100 drug repurposing candidates
         • Evaluated 571,232 possible pairs
         • Confidence scores: 0.9998 - 1.0000

────────────────────────────────────────────────────────────

PHASE 5: Validation & Interactive Dashboard
============================================
validate_predictions.py
    ├─◀ data/results/novel_predictions.csv
    └─▶ data/results/validation_report.csv
    └─▶ data/results/validation_summary.json
         • PubMed literature validation
         • 13 Novel (0 papers)
         • 5 Emerging (1-4 papers)
         • 2 Confirmed (≥5 papers)

streamlit run app/main.py
    ├─◀ All Phase 4-5 outputs
    ├─◀ Neo4j Database
    └─▶ http://localhost:8501
         • 4 pages: Home, Predictions, Model Insights, Graph Explorer
         • 15+ interactive visualizations
         • Filters, search, recommendations
         • CSV export functionality
```

### Component Details

#### 1. Data Collection Layer
- **PubMed Scraper**: Collects research paper abstracts via E-utilities API
- **PubChem Client**: Fetches drug information and chemical properties
- **DisGeNET Loader**: Processes gene-disease association data

#### 2. Data Processing Layer
- **NLP Pipeline**: BC5CDR model for biomedical entity recognition
- **Entity Extraction**: Identifies CHEMICAL (drugs) and DISEASE entities
- **Relationship Extraction**: Pattern-based extraction of drug-disease associations
- **Data Storage**: JSON for raw data, CSV for processed relationships

#### 3. Knowledge Graph Layer
- **Database**: Neo4j graph database
- **Schema**:
  - Nodes: Drug, Disease, Gene, Protein
  - Relationships: TREATS, CAUSES, TARGETS, ASSOCIATED_WITH
- **Query Language**: Cypher for graph traversal and pattern matching

#### 4. Machine Learning Layer
- **Model**: GraphSAGE (Graph Sample and Aggregate)
- **Task**: Link prediction (predict missing TREATS relationships)
- **Framework**: PyTorch Geometric
- **Training**: M1 GPU with MPS backend
- **Evaluation**: AUC-ROC, Precision@K metrics

#### 5. Application Layer
- **Web Framework**: Streamlit
- **Visualizations**: NetworkX for graph layout, Plotly for interactive charts
- **Features**: Prediction explorer, graph browser, entity search

---

## 🔄 Execution Workflows

### Data Collection & NLP Processing

```
┌──────────────┐
│     USER     │  Run: python collect_pubmed.py
└──────┬───────┘
       │
       ▼
┌──────────────┐     Search "drug repurposing"
│ PubMed API   │◀──────────────────────────────────
└──────┬───────┘     + 200 paper batch requests
       │
       │ PMIDs + Abstracts (XML)
       ▼
┌──────────────┐
│   SCRIPT     │  Parse → Clean → Save
└──────┬───────┘
       │
       ▼
    pubmed_abstracts.json (924 papers) ✓

───────────────────────────────────────────────────

┌──────────────┐
│     USER     │  Run: python extract_entities.py
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  BC5CDR NLP  │  Named Entity Recognition
└──────┬───────┘  (CHEMICAL, DISEASE)
       │
       │ For each abstract:
       │  • Tokenize
       │  • Extract entities
       │  • Pattern match "X treats Y"
       │  • Co-occurrence analysis
       ▼
    entities.csv (1,514 entities) ✓
    relationships.csv (666 relationships) ✓
```

### Graph Database Construction

```
┌──────────────┐
│     USER     │  Run: python load_to_neo4j.py
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────┐
│  LOAD entities.csv               │
│  LOAD relationships.csv          │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  CONNECT to Neo4j                │
│  CREATE constraints              │
└──────┬───────────────────────────┘
       │
       │ Batch processing:
       ├─▶ CREATE 718 Drug nodes
       ├─▶ CREATE 796 Disease nodes
       └─▶ CREATE 663 TREATS relationships
       │
       ▼
┌──────────────────────────────────┐
│  Neo4j Graph Database            │
│  • 1,514 nodes                   │
│  • 663 edges                     │
│  • Indexed & queryable           │
└──────────────────────────────────┘
    Load time: 2.54 seconds ✓
```

### GNN Training Pipeline

```
Neo4j DB
   │
   │ export_graph_data.py
   ▼
graph_data.pt (PyTorch format)
   │
   │ prepare_training_data.py
   ▼
┌──────────────────────────────────┐
│  train_data.pt   (70% - 928)     │
│  val_data.pt     (15% - 198)     │
│  test_data.pt    (15% - 200)     │
└──────┬───────────────────────────┘
       │
       │ train_gnn.py
       ▼
┌──────────────────────────────────┐
│  TRAINING LOOP (66 epochs)       │
│                                  │
│  For each epoch:                 │
│    1. Forward pass on M1 GPU     │
│    2. Compute BCE loss           │
│    3. Backward propagation       │
│    4. Update weights             │
│    5. Validate (every 10)        │
│                                  │
│  Early stopping at epoch 46      │
│  Best val AUC: 0.8601            │
└──────┬───────────────────────────┘
       │
       ▼
best_model.pt + training_history.json ✓
   │
   │ evaluate_gnn.py
   ▼
Test Results:
  • AUC: 0.8693 ✓
  • P@10: 1.0000 ✓
  • P@20: 1.0000 ✓
   │
   │ generate_predictions.py
   ▼
novel_predictions.csv (100 candidates) ✓
```

### Dashboard Launch

```
┌──────────────────────────────────┐
│  streamlit run app/main.py       │
└──────┬───────────────────────────┘
       │
       ├─▶ Load predictions.csv
       ├─▶ Load test_metrics.json
       ├─▶ Load training_history.json
       ├─▶ Connect to Neo4j
       │
       ▼
┌──────────────────────────────────┐
│  DASHBOARD (localhost:8501)      │
│                                  │
│  Pages:                          │
│  • 📊 Home (stats & overview)    │
│  • 🎯 Predictions (browse & filter) │
│  • 📈 Model Insights (performance) │
│  • 🔍 Graph Explorer (entities)   │
│                                  │
│  User actions:                   │
│  ├─ Filter by confidence         │
│  ├─ Search drug/disease          │
│  ├─ View validation status       │
│  └─ Download CSV                 │
└──────────────────────────────────┘
   Interactive Web App Ready! ✓
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Data Collection** | Python `requests`, REST APIs | PubMed, PubChem data fetching |
| **NLP** | SciSpacy, BC5CDR, Transformers | Biomedical entity extraction |
| **Data Storage** | JSON, CSV, Pandas | Raw and processed data |
| **Graph Database** | Neo4j 5.x, Cypher | Knowledge graph storage & queries |
| **ML Framework** | PyTorch 2.9+, PyTorch Geometric | Graph Neural Networks |
| **Compute** | M1 GPU (MPS backend) | Model training acceleration |
| **Web App** | Streamlit | Interactive demo interface |
| **Visualization** | NetworkX, Plotly, Matplotlib | Graph and data visualization |
| **Environment** | Python 3.11, venv | Dependency management |

---

## 📊 Project Status

**Data Collection** ✅ Complete
- 924 PubMed research papers (2020-2024)
- 107 FDA-approved drugs with metadata
- Data quality validated and ready

**NLP Processing & Entity Extraction** ✅ Complete
- Entity extraction: 1,514 entities (718 drugs, 796 diseases)
- Relationship extraction: 666 drug-disease relationships
- Knowledge base constructed and validated

**Knowledge Graph Construction** ✅ Complete
- Neo4j database with 1,514 nodes, 663 edges
- Graph schema implemented (Drug, Disease nodes; TREATS relationships)
- 60+ Cypher queries for graph exploration

**Machine Learning & Link Prediction** ✅ Complete
- GraphSAGE GNN with 7,073 parameters
- Test AUC: **0.8693** (exceeds target of 0.75 by 16%)
- Precision@10: **1.0000** (perfect top predictions!)
- 100 novel drug repurposing predictions generated

**Validation & Interactive Dashboard** ✅ Complete
- Literature validation: 13 novel, 5 emerging, 2 confirmed predictions
- Interactive Streamlit dashboard with 4 pages
- 15+ interactive visualizations
- Production-ready web application

**Documentation & Polish** 🔄 In Progress
- Technical documentation
- Architecture diagrams
- Deployment guide

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- 16GB RAM recommended (8GB minimum)
- macOS (M1/M2/M3) or Linux
- ~10GB free disk space

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/medical-kg-drug-repurposing.git
cd medical-kg-drug-repurposing

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download biomedical NLP model
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.1/en_ner_bc5cdr_md-0.5.1.tar.gz

# Install and start Neo4j (macOS)
brew install neo4j
brew services start neo4j
# Access Neo4j Browser at http://localhost:7474
# Default credentials: neo4j/neo4j
```

### Validate Setup

```bash
# Test environment
python test_setup.py

# Expected output: All checks pass ✅
```

---

## 📁 Project Structure

```
medical-kg-drug-repurposing/
├── data/
│   ├── raw/                    # Raw data from APIs
│   │   ├── pubmed_abstracts.json    (924 papers)
│   │   └── pubchem_drugs.csv        (107 drugs)
│   ├── processed/              # Cleaned, structured data
│   │   ├── entities.csv
│   │   └── relationships.csv
│   └── samples/                # Small samples for testing
│
├── scripts/
│   ├── data_collection/        # Data fetching scripts
│   │   ├── collect_pubmed.py
│   │   └── collect_pubchem.py
│   ├── preprocessing/          # NLP and data processing
│   ├── training/               # Model training scripts
│   └── evaluation/             # Model evaluation
│
├── notebooks/
│   ├── exploratory/            # Data exploration
│   ├── development/            # Model development
│   └── demo/                   # Demo notebooks
│
├── app/
│   ├── main.py                 # Streamlit app entry point
│   ├── components/             # UI components
│   ├── pages/                  # Multi-page app
│   └── utils/                  # Helper functions
│
├── models/
│   ├── checkpoints/            # Training checkpoints
│   └── trained/                # Final trained models
│
├── tests/                      # Unit and integration tests
├── requirements.txt            # Python dependencies
├── test_setup.py              # Environment validation
└── README.md                  # This file
```

---

## 📚 Data Sources

All data sources are publicly available and free to use for educational purposes:

| Source | Content | Size | License |
|--------|---------|------|---------|
| [PubMed](https://pubmed.ncbi.nlm.nih.gov/) | Research paper abstracts | 924 papers | Public Domain |
| [PubChem](https://pubchem.ncbi.nlm.nih.gov/) | Drug chemical properties | 107 drugs | Public Domain |
| [DisGeNET](https://www.disgenet.org/) | Gene-disease associations | Optional | CC BY-NC-SA 4.0 |

**Note**: While data is publicly available, this project uses small subsets for educational purposes only.

---

## 🧠 Learning Resources

This project helped me learn:

**Graph Neural Networks**:
- [PyTorch Geometric Tutorials](https://pytorch-geometric.readthedocs.io/)
- GraphSAGE paper: [Hamilton et al., 2017](https://arxiv.org/abs/1706.02216)

**Biomedical NLP**:
- [SciSpacy Documentation](https://allenai.github.io/scispacy/)
- BC5CDR dataset for entity recognition

**Knowledge Graphs**:
- [Neo4j Graph Academy](https://graphacademy.neo4j.com/)
- Cypher query language

**End-to-End ML**:
- Data collection → Processing → Modeling → Deployment
- Best practices for reproducibility

---

## 🎓 Skills Demonstrated

### Technical
- ✅ REST API integration and data collection
- ✅ Natural Language Processing (NLP) for entity extraction
- ✅ Graph database design and Cypher queries
- ✅ Graph Neural Networks (PyTorch Geometric)
- ✅ ML pipeline development (data → model → evaluation)
- ✅ Web application development (Streamlit)
- ✅ GPU-accelerated training (M1 MPS)

### Software Engineering
- ✅ Clean, modular code architecture
- ✅ Version control (Git)
- ✅ Documentation and testing
- ✅ Virtual environment management
- ✅ End-to-end feature ownership

### Problem Solving
- ✅ Working with unfamiliar domains (biomedical informatics)
- ✅ Handling large, unstructured datasets
- ✅ Building explainable AI systems
- ✅ Balancing scope vs. timeline (pragmatic approach)

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

**Dataset Licenses**:
- PubMed abstracts: Public Domain (U.S. Government work)
- PubChem data: Public Domain (U.S. Government work)
- DisGeNET: CC BY-NC-SA 4.0 (if used)

---

## 🙏 Acknowledgments

**Data Sources**:
- [PubMed/NIH](https://pubmed.ncbi.nlm.nih.gov/) for biomedical literature
- [PubChem](https://pubchem.ncbi.nlm.nih.gov/) for drug information

**Open Source Libraries**:
- [PyTorch](https://pytorch.org/) and [PyTorch Geometric](https://pytorch-geometric.readthedocs.io/)
- [Neo4j](https://neo4j.com/) graph database
- [SciSpacy](https://allenai.github.io/scispacy/) for biomedical NLP
- [Streamlit](https://streamlit.io/) for rapid web app development

**Inspiration**:
- Research on computational drug repurposing
- Graph ML community and tutorials

---

## 📧 Contact

**Karan Kukadia** - [kkukadia@iu.edu](mailto:kkukadia@iu.edu)

Project Link: [https://github.com/yourusername/medical-kg-drug-repurposing](https://github.com/yourusername/medical-kg-drug-repurposing)

---

## 📌 Disclaimer

This project is for **educational and portfolio purposes only**. It is not intended for:
- Medical diagnosis or treatment recommendations
- Clinical decision support
- Drug discovery or pharmaceutical research
- Any production healthcare applications

The techniques demonstrated here (Graph Neural Networks, NLP, Knowledge Graphs) are broadly applicable to many domains beyond healthcare, including recommendation systems, fraud detection, social network analysis, and more.

**Always consult qualified healthcare professionals for medical advice.**

---

**Status**: 🟢 Active Development | **Type**: Learning & Portfolio Project | **Timeline**: 5-6 weeks
