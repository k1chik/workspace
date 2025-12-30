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

### High-Level Architecture

```mermaid
graph TB
    subgraph "Data Sources"
        A1[PubMed API<br/>Research Papers]
        A2[PubChem API<br/>Drug Information]
        A3[DisGeNET<br/>Gene-Disease Data]
    end

    subgraph "Data Collection Layer"
        B1[PubMed Scraper<br/>Python/Requests]
        B2[PubChem Client<br/>Python/Requests]
        B3[DisGeNET Loader<br/>CSV Parser]
    end

    subgraph "Data Processing Layer"
        C1[Raw Data Storage<br/>JSON/CSV Files]
        C2[NLP Pipeline<br/>SciSpacy/BC5CDR]
        C3[Entity Extraction<br/>Drugs, Diseases, Genes]
        C4[Relationship Extraction<br/>Pattern Matching]
        C5[Processed Data<br/>Structured CSV]
    end

    subgraph "Knowledge Graph Layer"
        D1[Neo4j Graph DB]
        D2[Graph Schema<br/>Nodes: Drug, Disease, Gene<br/>Edges: TREATS, CAUSES, etc.]
        D3[Cypher Queries]
    end

    subgraph "Machine Learning Layer"
        E1[Feature Engineering<br/>Node Embeddings]
        E2[Graph Neural Network<br/>GraphSAGE]
        E3[Link Prediction Model<br/>PyTorch Geometric]
        E4[Model Training<br/>M1 GPU/MPS]
        E5[Trained Model<br/>Checkpoints]
    end

    subgraph "Application Layer"
        F1[Streamlit Web App]
        F2[Interactive Visualizations<br/>NetworkX/Plotly]
        F3[Prediction Explorer]
        F4[Graph Browser]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B3

    B1 --> C1
    B2 --> C1
    B3 --> C1

    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> C5

    C5 --> D1
    D1 --> D2
    D2 --> D3

    D1 --> E1
    E1 --> E2
    E2 --> E3
    E3 --> E4
    E4 --> E5

    E5 --> F1
    D1 --> F1
    F1 --> F2
    F1 --> F3
    F1 --> F4

    style A1 fill:#e1f5ff
    style A2 fill:#e1f5ff
    style A3 fill:#e1f5ff
    style D1 fill:#ffe1e1
    style E3 fill:#e1ffe1
    style F1 fill:#fff4e1
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

## 🔄 Sequence Diagrams

### Data Collection Workflow

```mermaid
sequenceDiagram
    participant User
    participant Script as Collection Script
    participant PubMed as PubMed API
    participant PubChem as PubChem API
    participant Storage as File System

    User->>Script: Run collect_pubmed.py
    Script->>PubMed: Search for papers<br/>(query: "drug repurposing")
    PubMed-->>Script: Return PMIDs<br/>(paper identifiers)

    loop For each batch of PMIDs
        Script->>PubMed: Fetch abstracts<br/>(batch of 200)
        Note over Script,PubMed: Rate limit: 0.4s delay
        PubMed-->>Script: Return XML data
        Script->>Script: Parse XML<br/>Extract title, abstract, metadata
    end

    Script->>Storage: Save to pubmed_abstracts.json
    Storage-->>User: 924 papers collected

    User->>Script: Run collect_pubchem.py

    loop For each drug in curated list
        Script->>PubChem: Query drug by name
        PubChem-->>Script: Return compound data<br/>(CID, formula, properties)
        Script->>Script: Extract relevant fields
    end

    Script->>Storage: Save to pubchem_drugs.csv
    Storage-->>User: 107 drugs collected
```

### NLP Processing Workflow

```mermaid
sequenceDiagram
    participant User
    participant Script as NLP Script
    participant Data as Raw Data Files
    participant NLP as SciSpacy/BC5CDR
    participant Output as Processed Data

    User->>Script: Run entity extraction
    Script->>Data: Load pubmed_abstracts.json
    Data-->>Script: 924 paper abstracts

    loop For each abstract
        Script->>NLP: Process text
        NLP->>NLP: Tokenization
        NLP->>NLP: Named Entity Recognition
        NLP-->>Script: Return entities<br/>(CHEMICAL, DISEASE)

        Script->>Script: Extract drug-disease pairs
        Script->>Script: Pattern matching<br/>("X treats Y", "X reduces Y")
    end

    Script->>Script: Deduplicate entities
    Script->>Script: Normalize names

    Script->>Output: Save entities.csv
    Script->>Output: Save relationships.csv
    Output-->>User: Structured knowledge base ready
```

### Graph Construction Workflow

```mermaid
sequenceDiagram
    participant User
    participant Script as Graph Builder
    participant Data as Processed Data
    participant Neo4j as Neo4j Database

    User->>Script: Run graph construction
    Script->>Data: Load entities.csv
    Script->>Data: Load relationships.csv

    Script->>Neo4j: Connect to database
    Neo4j-->>Script: Connection established

    Script->>Neo4j: Create constraints<br/>(unique drug names, etc.)

    loop For each unique drug
        Script->>Neo4j: CREATE (d:Drug {name, formula, ...})
    end

    loop For each unique disease
        Script->>Neo4j: CREATE (di:Disease {name, ...})
    end

    loop For each relationship
        Script->>Neo4j: MATCH (drug), (disease)<br/>CREATE (drug)-[:TREATS]->(disease)
    end

    Script->>Neo4j: Create indexes
    Neo4j-->>Script: Graph construction complete

    Script->>Neo4j: MATCH (n) RETURN count(n)
    Neo4j-->>User: 1,500+ nodes, 5,000+ relationships
```

### Model Training Workflow

```mermaid
sequenceDiagram
    participant User
    participant Script as Training Script
    participant Neo4j as Neo4j Database
    participant PyG as PyTorch Geometric
    participant Model as GNN Model
    participant GPU as M1 GPU (MPS)

    User->>Script: Run train_model.py
    Script->>Neo4j: Query graph structure
    Neo4j-->>Script: Nodes and edges

    Script->>Script: Prepare training data
    Script->>Script: Split: train/val/test<br/>(70%/15%/15%)
    Script->>Script: Generate negative samples<br/>(non-existent edges)

    Script->>PyG: Create Data object
    PyG->>PyG: Initialize node features

    Script->>Model: Initialize GraphSAGE<br/>(2 conv layers)
    Script->>GPU: Move model to MPS device

    loop Training epochs (50-100)
        Script->>Model: Forward pass
        Model->>GPU: Compute on M1 GPU
        GPU-->>Model: Predictions

        Script->>Script: Compute loss<br/>(Binary Cross Entropy)
        Script->>Model: Backward pass
        Script->>Model: Update weights

        alt Every 10 epochs
            Script->>Script: Evaluate on validation set
            Script->>User: Log metrics<br/>(AUC-ROC, Loss)
        end
    end

    Script->>Script: Evaluate on test set
    Script-->>User: Final AUC-ROC: 0.80

    Script->>Script: Save model checkpoint
    Script-->>User: Model saved to models/trained/
```

### Prediction & Demo Workflow

```mermaid
sequenceDiagram
    participant User
    participant App as Streamlit App
    participant Model as Trained GNN
    participant Neo4j as Neo4j Database

    User->>App: Launch streamlit app
    App->>Model: Load trained model
    App->>Neo4j: Connect to graph DB

    User->>App: Search for drug<br/>(e.g., "Aspirin")
    App->>Neo4j: MATCH (d:Drug {name: "Aspirin"})
    Neo4j-->>App: Drug node + existing relationships

    App->>Model: Predict new links<br/>(Aspirin → all diseases)
    Model->>Model: Generate embeddings
    Model->>Model: Compute edge scores
    Model-->>App: Top 10 predictions<br/>with confidence scores

    App->>App: Render interactive graph
    App->>App: Show prediction table
    App-->>User: Display results

    User->>App: Click on prediction
    App->>Neo4j: Find explanation paths<br/>MATCH path = (drug)-[*1..3]-(disease)
    Neo4j-->>App: Return shortest paths

    App->>App: Visualize explanation<br/>(drug → gene → disease)
    App-->>User: Show reasoning path
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

## 📊 Current Status

**Phase 1: Data Collection** ✅ Complete
- 924 PubMed research papers (2020-2024)
- 107 FDA-approved drugs with metadata
- Data quality validated and ready

**Phase 2: NLP Processing** 🔄 In Progress
- Entity extraction pipeline
- Relationship extraction
- Knowledge base construction

**Phase 3: Graph Construction** ⏳ Upcoming
- Neo4j schema design
- Data loading scripts
- Graph validation

**Phase 4: Model Training** ⏳ Upcoming
- GraphSAGE implementation
- Training pipeline
- Model evaluation

**Phase 5: Demo Application** ⏳ Upcoming
- Streamlit web interface
- Interactive visualizations
- Prediction explorer

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
