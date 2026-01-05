# File Dependencies Reference

This document shows the exact file inputs and outputs for each script in the project pipeline.

---

## Week 1: Data Collection

### Script: `scripts/data/collect_pubmed.py`

**Inputs:**
- None (queries PubMed API directly)

**Outputs:**
- `data/raw/pubmed_abstracts.json` - 924 research paper abstracts

**Format:**
```json
{
  "query": "...",
  "total_results": 924,
  "abstracts": [
    {
      "pmid": "12345678",
      "title": "...",
      "abstract": "...",
      "authors": [...],
      "journal": "...",
      "pub_date": "2024-01-15"
    }
  ]
}
```

---

### Script: `scripts/data/collect_pubchem.py`

**Inputs:**
- Hardcoded list of drug names in script

**Outputs:**
- `data/raw/pubchem_drugs.csv` - 107 drugs with chemical properties

**Format:**
```csv
name,cid,molecular_formula,molecular_weight,canonical_smiles,iupac_name
aspirin,2244,C9H8O4,180.16,CC(=O)OC1=CC=CC=C1C(=O)O,...
```

---

## Week 2: NLP Processing

### Script: `scripts/nlp/extract_entities.py`

**Inputs:**
- `data/raw/pubmed_abstracts.json` (from Week 1)

**Outputs:**
- `data/processed/entities.csv` - 1,514 unique entities

**Format:**
```csv
entity_id,entity_text,entity_type,frequency,num_papers
DRUG_0001,aspirin,CHEMICAL,45,12
DISEASE_0001,alzheimer's disease,DISEASE,89,34
```

**Processing:**
- Uses BC5CDR model for Named Entity Recognition
- Extracts CHEMICAL (drugs) and DISEASE entities
- Deduplicates and normalizes (lowercase)
- Counts frequency and number of papers

---

### Script: `scripts/nlp/extract_relationships.py`

**Inputs:**
- `data/raw/pubmed_abstracts.json` (from Week 1)
- `data/processed/entities.csv` (from previous step)

**Outputs:**
- `data/processed/relationships.csv` - 666 drug-disease relationships

**Format:**
```csv
source,target,source_type,target_type,relationship_type,confidence,num_papers,evidence
DRUG_0001,DISEASE_0001,CHEMICAL,DISEASE,TREATS,2.5,3,pattern_match|cooccurrence
```

**Processing:**
- Pattern-based extraction (e.g., "X treats Y", "X reduces Y")
- Co-occurrence analysis (same sentence proximity)
- Aggregates confidence scores and evidence

---

### Script: `scripts/nlp/create_knowledge_base.py`

**Inputs:**
- `data/processed/entities.csv`
- `data/processed/relationships.csv`

**Outputs:**
- `data/processed/knowledge_base.json` - Combined knowledge base

**Format:**
```json
{
  "entities": [...],
  "relationships": [...],
  "statistics": {
    "total_entities": 1514,
    "total_relationships": 666,
    "drugs": 718,
    "diseases": 796
  }
}
```

**Processing:**
- Validates referential integrity (all relationship endpoints exist)
- Generates quality report
- Combines entities and relationships into single structure

---

## Week 3: Graph Construction

### Script: `scripts/graph/load_to_neo4j.py`

**Inputs:**
- `data/processed/entities.csv`
- `data/processed/relationships.csv`

**Outputs:**
- Neo4j Graph Database
  - 1,514 nodes (718 :Drug, 796 :Disease)
  - 663 :TREATS relationships

**Neo4j Schema:**
```cypher
// Nodes
(:Drug {
  entity_id: "DRUG_0001",
  name: "aspirin",
  frequency: 45,
  num_papers: 12
})

(:Disease {
  entity_id: "DISEASE_0001",
  name: "alzheimer's disease",
  frequency: 89,
  num_papers: 34
})

// Relationships
(:Drug)-[:TREATS {
  confidence: 2.5,
  num_papers: 3,
  evidence: "pattern_match|cooccurrence"
}]->(:Disease)
```

**Processing:**
- Batch loading (500 nodes/batch) for performance
- Creates constraints and indexes
- Transaction management with error handling
- Validates data integrity

---

### File: `scripts/graph/cypher_queries.cypher`

**Purpose:** Pre-written queries for graph exploration

**Categories:**
- Basic exploration (count nodes, list entities)
- Drug repurposing insights (top drugs, rare diseases)
- Network analysis (degree distribution, paths)
- Statistical analysis (confidence scores, relationships)
- Validation checks (orphan nodes, duplicate edges)

---

## Week 4: Machine Learning

### Script: `scripts/ml/export_graph_data.py`

**Inputs:**
- Neo4j Graph Database (live connection)

**Outputs:**
- `data/processed/graph_data.pt` - PyTorch Geometric format

**Format:**
```python
{
  'x': tensor([[...]], shape=[1514, 2]),  # Node features
  'edge_index': tensor([[...]], shape=[2, 663]),  # Edge indices
  'edge_attr': tensor([[...]], shape=[663, 2]),  # Edge attributes
  'node_mapping': {...},  # Entity ID → integer index
  'reverse_mapping': {...}  # Integer index → entity ID
}
```

**Node Features:**
- Feature 0: Frequency (z-score normalized)
- Feature 1: Number of papers (z-score normalized)

---

### Script: `scripts/ml/prepare_training_data.py`

**Inputs:**
- `data/processed/graph_data.pt`

**Outputs:**
- `data/processed/train_data.pt` - Training set (928 edges: 464 pos, 464 neg)
- `data/processed/val_data.pt` - Validation set (198 edges: 99 pos, 99 neg)
- `data/processed/test_data.pt` - Test set (200 edges: 100 pos, 100 neg)

**Format:**
```python
{
  'x': tensor([...]),  # Node features
  'edge_index': tensor([...]),  # Edges to predict
  'labels': tensor([...]),  # 0 or 1 (negative or positive)
  'num_pos': int,  # Number of positive samples
  'num_neg': int  # Number of negative samples
}
```

**Processing:**
- 70/15/15 train/val/test split
- 1:1 negative sampling (balanced classes)
- No overlap between splits
- Ensures all node types represented

---

### Script: `scripts/ml/train_gnn.py`

**Inputs:**
- `data/processed/train_data.pt`
- `data/processed/val_data.pt`
- `data/processed/graph_data.pt` (for message passing)

**Outputs:**
- `models/checkpoints/best_model.pt` - Trained model checkpoint
- `data/results/training_history.json` - Training curves

**Model Checkpoint Format:**
```python
{
  'epoch': 46,
  'model_state_dict': {...},
  'optimizer_state_dict': {...},
  'val_auc': 0.8601,
  'val_ap': 0.8785
}
```

**Training History Format:**
```json
{
  "train_loss": [0.674, 0.645, ...],
  "train_auc": [0.593, 0.729, ...],
  "val_loss": [0.611, 0.589, ...],
  "val_auc": [0.833, 0.833, ...],
  "val_ap": [0.847, 0.847, ...]
}
```

---

### Script: `scripts/ml/evaluate_gnn.py`

**Inputs:**
- `models/checkpoints/best_model.pt`
- `data/processed/test_data.pt`
- `data/processed/train_data.pt` (for message passing edges)

**Outputs:**
- `data/results/test_metrics.json` - Test set metrics
- `data/visualizations/roc_curve.png` - ROC curve plot
- `data/visualizations/pr_curve.png` - Precision-Recall curve plot

**Test Metrics Format:**
```json
{
  "auc_roc": 0.8693,
  "auc_pr": 0.8750,
  "accuracy": 0.7750,
  "precision": 0.8313,
  "recall": 0.6900,
  "f1": 0.7541,
  "confusion_matrix": [[86, 14], [31, 69]],
  "tn": 86, "fp": 14, "fn": 31, "tp": 69,
  "p@10": 1.0000,
  "p@20": 1.0000,
  "p@50": 0.9200,
  "p@100": 0.8000
}
```

---

### Script: `scripts/ml/generate_predictions.py`

**Inputs:**
- `models/checkpoints/best_model.pt`
- `data/processed/graph_data.pt`
- `data/processed/entities.csv`
- `data/processed/train_data.pt`, `val_data.pt`, `test_data.pt` (to exclude existing edges)

**Outputs:**
- `data/results/novel_predictions.csv` - Top 100 predictions

**Format:**
```csv
rank,drug,drug_id,disease,disease_id,confidence,drug_frequency,disease_frequency,drug_num_papers,disease_num_papers
1,fusidic acid,DRUG_0720,carbapenem-resistant a. baumannii,DISEASE_0719,0.9999994,1,1,1,1
```

**Processing:**
- Evaluates all 571,232 possible drug-disease pairs
- Excludes existing relationships from train/val/test
- Ranks by model confidence
- Returns top 100

---

## Week 5: Validation & Dashboard

### Script: `scripts/validation/validate_predictions.py`

**Inputs:**
- `data/results/novel_predictions.csv`

**Outputs:**
- `data/results/validation_report.csv` - Validation results
- `data/results/validation_summary.json` - Statistics

**Validation Report Format:**
```csv
rank,drug,disease,confidence,pubmed_count,validation_status,sample_titles
1,fusidic acid,carbapenem-resistant a. baumannii,0.9999994,0,Novel,"[]"
8,fusidic acid,allergic,0.9999885,7,Confirmed,"['Title 1', 'Title 2', ...]"
```

**Validation Summary Format:**
```json
{
  "total_validated": 20,
  "confirmed": 2,
  "emerging": 5,
  "novel": 13,
  "avg_confidence": 0.9999658,
  "avg_pubmed_count": 1.15,
  "max_pubmed_count": 7,
  "validation_by_status": {...}
}
```

**Processing:**
- Searches PubMed API for each drug-disease pair
- Classifies: Novel (0 papers), Emerging (1-4), Confirmed (≥5)
- Rate limited to respect API limits

---

### Application: `app/main.py` (Streamlit Dashboard)

**Inputs:**
- `data/processed/entities.csv`
- `data/processed/relationships.csv`
- `data/processed/graph_data.pt`
- `data/results/novel_predictions.csv`
- `data/results/validation_report.csv`
- `data/results/validation_summary.json`
- `data/results/training_history.json`
- `data/results/test_metrics.json`
- Neo4j Database (optional, for live queries)

**Outputs:**
- Interactive web application on `http://localhost:8501`
- 4 pages:
  - Home (📊)
  - Predictions (🎯)
  - Model Insights (📈)
  - Graph Explorer (🔍)

**Features:**
- Interactive filters and search
- 15+ Plotly visualizations
- Data export (CSV downloads)
- Recommendation engine

---

## Complete File Dependency Chain

```
Week 1: Data Collection
PubMed API → pubmed_abstracts.json
PubChem API → pubchem_drugs.csv

Week 2: NLP Processing
pubmed_abstracts.json → extract_entities.py → entities.csv
pubmed_abstracts.json + entities.csv → extract_relationships.py → relationships.csv
entities.csv + relationships.csv → create_knowledge_base.py → knowledge_base.json

Week 3: Graph Construction
entities.csv + relationships.csv → load_to_neo4j.py → Neo4j Database

Week 4: Machine Learning
Neo4j Database → export_graph_data.py → graph_data.pt
graph_data.pt → prepare_training_data.py → train/val/test_data.pt
train/val/test_data.pt → train_gnn.py → best_model.pt + training_history.json
best_model.pt + test_data.pt → evaluate_gnn.py → test_metrics.json + plots
best_model.pt + graph_data.pt → generate_predictions.py → novel_predictions.csv

Week 5: Dashboard
novel_predictions.csv → validate_predictions.py → validation_report.csv + summary.json
All Week 4-5 outputs → Streamlit app → Interactive Dashboard
```

---

## Critical Files Summary

| File | Size | Description | Dependencies |
|------|------|-------------|--------------|
| `pubmed_abstracts.json` | ~3.5 MB | 924 papers | PubMed API |
| `entities.csv` | ~100 KB | 1,514 entities | pubmed_abstracts.json |
| `relationships.csv` | ~50 KB | 666 relationships | pubmed_abstracts.json, entities.csv |
| `graph_data.pt` | ~200 KB | PyTorch graph | Neo4j DB |
| `train_data.pt` | ~50 KB | Training set | graph_data.pt |
| `val_data.pt` | ~15 KB | Validation set | graph_data.pt |
| `test_data.pt` | ~15 KB | Test set | graph_data.pt |
| `best_model.pt` | ~100 KB | Trained GNN | train/val_data.pt |
| `training_history.json` | ~10 KB | Training curves | train_gnn.py |
| `test_metrics.json` | ~2 KB | Evaluation metrics | evaluate_gnn.py |
| `novel_predictions.csv` | ~10 KB | Top 100 predictions | best_model.pt, graph_data.pt |
| `validation_report.csv` | ~5 KB | Validation results | novel_predictions.csv |

---

## Data Flow Summary

1. **APIs → Raw Data** (Week 1)
   - External APIs provide research papers and drug information
   - Stored as JSON and CSV files

2. **Raw Data → Structured Data** (Week 2)
   - NLP extracts entities and relationships
   - Creates knowledge base in CSV format

3. **Structured Data → Graph Database** (Week 3)
   - CSV files loaded into Neo4j
   - Creates queryable graph structure

4. **Graph Database → ML Dataset** (Week 4)
   - Neo4j exports to PyTorch format
   - Split into train/validation/test sets

5. **ML Dataset → Trained Model** (Week 4)
   - GNN trained on graph data
   - Generates predictions and metrics

6. **Model + Data → Dashboard** (Week 5)
   - All outputs combined in Streamlit
   - Interactive exploration and visualization

---

## Running the Complete Pipeline

```bash
# Week 1: Data Collection
python scripts/data/collect_pubmed.py
python scripts/data/collect_pubchem.py

# Week 2: NLP Processing
python scripts/nlp/extract_entities.py
python scripts/nlp/extract_relationships.py
python scripts/nlp/create_knowledge_base.py

# Week 3: Graph Construction
python scripts/graph/load_to_neo4j.py

# Week 4: Machine Learning
python scripts/ml/export_graph_data.py
python scripts/ml/prepare_training_data.py
python scripts/ml/train_gnn.py
python scripts/ml/evaluate_gnn.py
python scripts/ml/generate_predictions.py

# Week 5: Validation & Dashboard
python scripts/validation/validate_predictions.py
streamlit run app/main.py
```

---

**Last Updated:** December 31, 2025
