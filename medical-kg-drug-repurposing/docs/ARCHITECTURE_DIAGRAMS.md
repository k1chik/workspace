# Architecture Diagrams - Modular Breakdown

This document provides architecture diagrams broken down into logical, digestible pieces. Use these as templates for Draw.io, Excalidraw, or other diagramming tools.

---

## Diagram 1: Data Collection Layer

**Purpose:** Show how raw data is collected from external APIs

```
┌─────────────────────────────────────────────────┐
│           EXTERNAL DATA SOURCES                 │
└─────────────────────────────────────────────────┘
          │                      │
          │                      │
    PubMed API              PubChem API
    (Papers)                (Drugs)
          │                      │
          ▼                      ▼
┌──────────────────┐   ┌──────────────────┐
│ collect_pubmed   │   │ collect_pubchem  │
│     .py          │   │     .py          │
└────────┬─────────┘   └────────┬─────────┘
         │                      │
         ▼                      ▼
┌──────────────────┐   ┌──────────────────┐
│ pubmed_abstracts │   │ pubchem_drugs    │
│     .json        │   │     .csv         │
│                  │   │                  │
│  924 papers      │   │  107 drugs       │
└──────────────────┘   └──────────────────┘
```

**Components:**
- 2 External APIs (PubMed, PubChem)
- 2 Python scripts (collectors)
- 2 Output files (JSON, CSV)

**Key Metrics:**
- PubMed: 924 research papers
- PubChem: 107 FDA-approved drugs

---

## Diagram 2: NLP Processing Pipeline

**Purpose:** Show how unstructured text becomes structured knowledge

```
┌──────────────────────────────────────────────┐
│        pubmed_abstracts.json                 │
│        (924 unstructured papers)             │
└────────────────┬─────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │   BC5CDR      │
         │   NLP Model   │
         └───────┬───────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌───────────────┐  ┌──────────────┐
│extract_       │  │extract_      │
│entities.py    │  │relationships │
│               │  │    .py       │
└───────┬───────┘  └──────┬───────┘
        │                 │
        ▼                 ▼
┌───────────────┐  ┌──────────────┐
│ entities.csv  │  │relationships │
│               │  │    .csv      │
│ 1,514 items   │  │ 666 items    │
│ (718 drugs +  │  │              │
│  796 diseases)│  │              │
└───────┬───────┘  └──────┬───────┘
        │                 │
        └────────┬────────┘
                 ▼
      ┌──────────────────┐
      │create_knowledge_ │
      │    base.py       │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ knowledge_base   │
      │     .json        │
      │                  │
      │ Validated KB     │
      └──────────────────┘
```

**Processing Steps:**
1. Named Entity Recognition (NER)
2. Pattern Matching ("X treats Y")
3. Co-occurrence Analysis
4. Deduplication & Normalization
5. Validation & Quality Control

**Outputs:**
- 1,514 unique biomedical entities
- 666 drug-disease relationships
- Combined knowledge base (JSON)

---

## Diagram 3: Knowledge Graph Construction

**Purpose:** Show transformation from CSV to graph database

```
┌──────────────┐       ┌──────────────┐
│entities.csv  │       │relationships │
│              │       │    .csv      │
└──────┬───────┘       └──────┬───────┘
       │                      │
       └──────────┬───────────┘
                  │
                  ▼
         ┌────────────────┐
         │ load_to_neo4j  │
         │     .py        │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────────────┐
         │   Neo4j Database       │
         ├────────────────────────┤
         │                        │
         │  NODES:                │
         │  ┌──────────────┐     │
         │  │ :Drug (718)  │     │
         │  └──────────────┘     │
         │  ┌──────────────┐     │
         │  │:Disease (796)│     │
         │  └──────────────┘     │
         │                        │
         │  RELATIONSHIPS:        │
         │  ──[:TREATS]──▶ (663) │
         │                        │
         │  PROPERTIES:           │
         │  • Constraints         │
         │  • Indexes             │
         │  • Cypher Queries      │
         └────────────────────────┘
```

**Schema:**
- Node Types: Drug, Disease
- Relationship Type: TREATS
- Properties: name, frequency, num_papers, confidence

**Performance:**
- Batch size: 500 nodes
- Load time: 2.54 seconds
- Success rate: 99.5%

---

## Diagram 4: Machine Learning Pipeline

**Purpose:** Show GNN training workflow from graph to predictions

```
┌────────────────┐
│  Neo4j Graph   │
│   Database     │
└───────┬────────┘
        │
        │ export_graph_data.py
        ▼
┌────────────────┐
│ graph_data.pt  │
│ (PyTorch)      │
└───────┬────────┘
        │
        │ prepare_training_data.py
        ▼
┌──────────────────────────────┐
│  Training Datasets           │
├──────────────────────────────┤
│ train_data.pt (70% - 928)    │
│ val_data.pt   (15% - 198)    │
│ test_data.pt  (15% - 200)    │
└──────────┬───────────────────┘
           │
           │ train_gnn.py
           ▼
    ┌──────────────┐
    │  GraphSAGE   │
    │  Training    │
    ├──────────────┤
    │ • 66 epochs  │
    │ • M1 GPU     │
    │ • 7K params  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ best_model   │
    │    .pt       │
    │              │
    │ Val AUC:     │
    │  0.8601      │
    └──────┬───────┘
           │
           ├─────────────────┐
           │                 │
           │ evaluate_gnn.py │ generate_predictions.py
           ▼                 ▼
    ┌──────────────┐  ┌──────────────┐
    │test_metrics  │  │novel_        │
    │   .json      │  │predictions   │
    │              │  │   .csv       │
    │ Test AUC:    │  │              │
    │  0.8693 ✓    │  │ Top 100      │
    │ P@10: 1.0 ✓  │  │ candidates   │
    └──────────────┘  └──────────────┘
```

**Model Architecture:**
```
Input: [1514, 2] node features
  ↓
SAGEConv(2 → 64) + ReLU + Dropout(0.5)
  ↓
SAGEConv(64 → 32)
  ↓
Concatenate node pairs [64]
  ↓
MLP Decoder (64 → 32 → 16 → 1)
  ↓
Output: Link probability [0, 1]
```

**Training:**
- Loss: Binary Cross-Entropy
- Optimizer: Adam (lr=0.01)
- Device: M1 GPU (MPS)
- Early stopping: patience=20

---

## Diagram 5: Application Layer

**Purpose:** Show dashboard architecture and data flow

```
┌─────────────────────────────────────────────┐
│         DATA SOURCES (Read-only)            │
├─────────────────────────────────────────────┤
│ • novel_predictions.csv                     │
│ • validation_report.csv                     │
│ • test_metrics.json                         │
│ • training_history.json                     │
│ • Neo4j Database (live queries)             │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│        STREAMLIT APPLICATION                 │
│         (app/main.py)                        │
├──────────────────────────────────────────────┤
│                                              │
│  ┌────────────────────────────────────┐     │
│  │  Data Loaders (Cached)             │     │
│  │  • load_predictions()              │     │
│  │  • load_validation()               │     │
│  │  • load_metrics()                  │     │
│  │  • get_neo4j_connection()          │     │
│  └────────────┬───────────────────────┘     │
│               │                              │
│               ▼                              │
│  ┌────────────────────────────────────┐     │
│  │         PAGE ROUTER                │     │
│  └────────────┬───────────────────────┘     │
│               │                              │
│       ┌───────┼───────┬─────────┐           │
│       │       │       │         │           │
│       ▼       ▼       ▼         ▼           │
│  ┌──────┐┌──────┐┌──────┐┌──────────┐      │
│  │ Home ││Pred- ││Model ││  Graph   │      │
│  │ Page ││ict- ││Insig-││ Explorer │      │
│  │  📊  ││ions ││hts   ││    🔍    │      │
│  │      ││ 🎯  ││ 📈   ││          │      │
│  └──────┘└──────┘└──────┘└──────────┘      │
│                                              │
│  Features per page:                         │
│  • Interactive filters                      │
│  • Plotly visualizations                    │
│  • Search & recommendations                 │
│  • CSV export                               │
│                                              │
└──────────────┬───────────────────────────────┘
               │
               ▼
        ┌──────────────┐
        │    USER      │
        │   Browser    │
        │              │
        │ localhost:   │
        │    8501      │
        └──────────────┘
```

**Pages:**
1. **Home (📊)**: Overview, stats, quick links
2. **Predictions (🎯)**: Browse 100 candidates, filters, validation status
3. **Model Insights (📈)**: Training curves, metrics, performance analysis
4. **Graph Explorer (🔍)**: Entity search, relationships, network topology

**Technologies:**
- Framework: Streamlit 1.52
- Visualizations: Plotly
- Data: Pandas, PyTorch
- Database: Neo4j (optional)

---

## Diagram 6: Complete End-to-End System

**Purpose:** High-level view of entire pipeline

```
┌──────────────────────────────────────────────────────┐
│                 EXTERNAL WORLD                       │
│  PubMed API  │  PubChem API  │  End Users           │
└────┬─────────┴───────┬────────────────▲──────────────┘
     │                 │                │
     ▼                 ▼                │
┌────────────────────────────────────┐  │
│     WEEK 1: DATA COLLECTION        │  │
│  Scripts: collect_*.py             │  │
│  Output: JSON, CSV (raw data)      │  │
└────────────┬───────────────────────┘  │
             │                           │
             ▼                           │
┌────────────────────────────────────┐  │
│     WEEK 2: NLP PROCESSING         │  │
│  Scripts: extract_*.py             │  │
│  Tool: BC5CDR NER                  │  │
│  Output: Structured entities, KB   │  │
└────────────┬───────────────────────┘  │
             │                           │
             ▼                           │
┌────────────────────────────────────┐  │
│  WEEK 3: GRAPH DATABASE            │  │
│  Script: load_to_neo4j.py          │  │
│  Database: Neo4j                   │  │
│  Output: 1,514 nodes, 663 edges    │  │
└────────────┬───────────────────────┘  │
             │                           │
             ▼                           │
┌────────────────────────────────────┐  │
│  WEEK 4: MACHINE LEARNING          │  │
│  Scripts: train_gnn.py, etc.       │  │
│  Model: GraphSAGE GNN              │  │
│  Output: Trained model, 100 preds  │  │
└────────────┬───────────────────────┘  │
             │                           │
             ▼                           │
┌────────────────────────────────────┐  │
│  WEEK 5: DASHBOARD                 │  │
│  App: Streamlit                    │  │
│  Features: Browse, Filter, Export  │  │
│  Output: Interactive web app       │──┘
└────────────────────────────────────┘
```

**Flow:**
- Vertical: Week-by-week progression
- Horizontal: Data transformation stages
- Output: Usable drug repurposing insights

---

## Draw.io Tips

### For Clean Diagrams:

1. **Use Consistent Shapes:**
   - Rectangles for files/data
   - Rounded rectangles for processes/scripts
   - Cylinders for databases
   - Clouds for external APIs

2. **Color Coding:**
   - Blue: Data sources
   - Green: Processing scripts
   - Yellow: Outputs/Results
   - Red: Databases
   - Gray: External services

3. **Layout:**
   - Top-to-bottom flow (like ASCII diagrams)
   - Left-to-right for parallel processes
   - Group related components in containers

4. **Labels:**
   - Keep short (≤3 words)
   - Include key metrics
   - Use icons/emojis sparingly

### Example Color Scheme:

```
APIs:           #E3F2FD (Light Blue)
Scripts:        #E8F5E9 (Light Green)
Data Files:     #FFF9C4 (Light Yellow)
Databases:      #FFEBEE (Light Red)
ML Models:      #F3E5F5 (Light Purple)
Dashboard:      #FFF3E0 (Light Orange)
```

### Recommended Tools:

1. **Draw.io** (diagrams.net)
   - Free, web-based
   - GitHub integration
   - Export: PNG, SVG, PDF

2. **Excalidraw**
   - Hand-drawn style
   - Modern, clean look
   - Export: PNG, SVG

3. **Lucidchart**
   - Professional templates
   - Collaboration features
   - Export: PNG, PDF

4. **Miro**
   - Whiteboard style
   - Great for brainstorming
   - Export: PNG, PDF

---

## Next Steps

1. **Choose a tool** (Draw.io recommended for GitHub)
2. **Create diagrams** using the layouts above as templates
3. **Export as PNG** with transparent background
4. **Save to** `docs/images/` directory
5. **Update README** with image links:

```markdown
![Data Collection](docs/images/diagram1-data-collection.png)
![NLP Pipeline](docs/images/diagram2-nlp-pipeline.png)
![Knowledge Graph](docs/images/diagram3-knowledge-graph.png)
![ML Pipeline](docs/images/diagram4-ml-pipeline.png)
![Dashboard](docs/images/diagram5-dashboard.png)
![Complete System](docs/images/diagram6-complete-system.png)
```

---

**Template Files:**
- Create `.drawio` files in `docs/diagrams/` (optional)
- Commit both `.drawio` and exported `.png` files
- GitHub can preview `.drawio` files natively

**Recommended Sizes:**
- Width: 1200-1600px
- Height: Auto
- DPI: 300 for print, 150 for web
- Format: PNG with transparency
