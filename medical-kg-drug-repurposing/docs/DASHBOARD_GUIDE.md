# Drug Repurposing Dashboard Guide

## Overview

Interactive Streamlit dashboard for exploring the medical knowledge graph and GNN predictions for drug repurposing.

## Features

### 📊 Home Page
- Project overview and key statistics
- Knowledge graph metrics
- Model performance summary
- Quick navigation to all features

### 🎯 Predictions Page
- Browse 100 novel drug repurposing candidates
- Filter by confidence score
- Filter by validation status (Confirmed/Emerging/Novel)
- Search for specific drugs or diseases
- View top predictions by category
- Download filtered results as CSV
- Interactive recommendation tool

### 📈 Model Insights Page
- Model architecture details
- Training dynamics and learning curves
- Test set performance metrics
- Confusion matrix visualization
- Precision@K analysis
- Prediction confidence distribution
- Comparison to baseline methods

### 🔍 Graph Explorer Page
- Knowledge graph statistics
- Entity frequency distributions
- Top drugs and diseases
- Relationship analysis
- Entity search with details
- Network topology analysis
- Degree distribution
- Export data functionality

## Running the Dashboard

### Prerequisites
- Python 3.8+
- Virtual environment with required packages
- Neo4j database running (optional, for live queries)

### Quick Start

1. **Activate virtual environment:**
```bash
source venv/bin/activate
```

2. **Run the dashboard:**
```bash
streamlit run app/main.py
```

3. **Access the dashboard:**
- Open your browser to `http://localhost:8501`
- Dashboard will automatically load with all data

### Alternative: Specify Port

```bash
streamlit run app/main.py --server.port 8502
```

### Headless Mode (for servers)

```bash
streamlit run app/main.py --server.headless true
```

## Dashboard Structure

```
app/
├── main.py                 # Main entry point (landing page)
├── pages/
│   ├── 1_📊_Home.py       # Home page with statistics
│   ├── 2_🎯_Predictions.py # Predictions browser
│   ├── 3_📈_Model_Insights.py # Model performance
│   └── 4_🔍_Graph_Explorer.py # Graph exploration
└── utils/
    └── data_loader.py      # Data loading utilities
```

## Data Sources

The dashboard loads data from:
- `data/processed/entities.csv` - Extracted entities (drugs, diseases)
- `data/processed/relationships.csv` - Drug-disease relationships
- `data/processed/graph_data.pt` - PyTorch graph data
- `data/results/novel_predictions.csv` - GNN predictions
- `data/results/validation_report.csv` - Literature validation (if available)
- `data/results/training_history.json` - Training metrics
- `data/results/test_metrics.json` - Evaluation metrics

## Key Capabilities

### Filtering and Search
- **Confidence Threshold**: Filter predictions by minimum confidence score
- **Validation Status**: Show only Confirmed/Emerging/Novel predictions
- **Text Search**: Find specific drugs or diseases
- **Interactive Tables**: Sort and explore all data

### Visualizations
- **Training Curves**: Loss and AUC over epochs
- **Confusion Matrix**: Test set performance breakdown
- **Precision@K**: Top-K prediction accuracy
- **Frequency Distributions**: Entity occurrence patterns
- **Degree Distribution**: Network connectivity analysis
- **Confidence Histograms**: Prediction score distributions

### Download Options
- Export filtered predictions as CSV
- Download entity data
- Download relationship data
- Download network topology metrics

## Usage Tips

### For Drug Repurposing Research
1. Start with **Predictions** page
2. Filter for "Novel" predictions (no existing literature)
3. Sort by confidence score
4. Review top candidates for your area of interest
5. Use recommendation tool to find treatments for specific diseases

### For Model Analysis
1. Visit **Model Insights** page
2. Review test AUC and Precision@K metrics
3. Analyze training curves for overfitting
4. Compare to baseline methods
5. Understand confidence score distribution

### For Graph Exploration
1. Go to **Graph Explorer** page
2. Browse entity frequency distributions
3. Search for specific drugs or diseases
4. View related entities and relationships
5. Export data for further analysis

## Performance Notes

- **Caching**: Data is cached using `@st.cache_data` for fast loading
- **Large Datasets**: Tables are paginated automatically
- **Responsive**: Dashboard adapts to different screen sizes
- **Real-time**: Filters update instantly

## Troubleshooting

### Dashboard won't start
- Ensure virtual environment is activated
- Check that all required packages are installed: `pip install -r requirements.txt`
- Verify data files exist in expected locations

### Missing data
- Run data collection: `python scripts/data/collect_pubmed.py`
- Run NLP pipeline: `python scripts/nlp/create_knowledge_base.py`
- Run GNN training: `python scripts/ml/train_gnn.py`
- Generate predictions: `python scripts/ml/generate_predictions.py`

### Validation data not showing
- Run validation script: `python scripts/validation/validate_predictions.py`
- Wait for validation to complete (~1 minute for 100 predictions)
- Refresh dashboard

### Neo4j connection error
- Ensure Neo4j is running: `neo4j status`
- Check credentials in `app/utils/data_loader.py`
- Dashboard works without Neo4j (uses cached data)

## Customization

### Change Theme
Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### Modify Filters
Edit `app/pages/2_🎯_Predictions.py` to add new filters or change defaults.

### Add New Pages
Create new file in `app/pages/` with format: `N_Icon_PageName.py`

## Production Deployment

### Streamlit Cloud (Recommended)
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Deploy with one click
4. Share public URL

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app/main.py", "--server.headless", "true"]
```

### AWS/GCP/Azure
- Use Streamlit Cloud for simplest deployment
- Or containerize with Docker and deploy to cloud platform
- Configure firewall rules for port 8501

## Support

For issues or questions:
- Review error messages in terminal
- Check Streamlit documentation: https://docs.streamlit.io
- Verify data file integrity
- Ensure Python version compatibility (3.8+)

## License

This dashboard is part of the Medical Knowledge Graph Drug Repurposing portfolio project.

---

**Built with:**
- Streamlit 1.52.2
- Plotly for interactive visualizations
- Pandas for data manipulation
- PyTorch for model integration
