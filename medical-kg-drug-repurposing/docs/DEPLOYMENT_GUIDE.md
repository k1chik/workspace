# Deployment Guide

This guide covers how to run the Medical Knowledge Graph Drug Repurposing Explorer locally and deploy it to production environments.

---

## Table of Contents

1. [Local Deployment](#local-deployment)
2. [Environment Setup](#environment-setup)
3. [Running the Dashboard](#running-the-dashboard)
4. [Neo4j Configuration](#neo4j-configuration-optional)
5. [Cloud Deployment](#cloud-deployment)
6. [Troubleshooting](#troubleshooting)
7. [Performance Optimization](#performance-optimization)

---

## Local Deployment

### Prerequisites

- **Python**: 3.11 or higher
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: ~10GB free disk space
- **OS**: macOS (M1/M2/M3), Linux, or Windows (WSL recommended)
- **Neo4j**: Optional (dashboard works without it using cached data)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/medical-kg-drug-repurposing.git
cd medical-kg-drug-repurposing

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Run the dashboard
streamlit run app/main.py
```

The dashboard will open automatically at `http://localhost:8501`

---

## Environment Setup

### Installing Python 3.11+

**macOS (using Homebrew):**
```bash
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv
```

**Windows:**
- Download from [python.org](https://www.python.org/downloads/)
- Or use Windows Subsystem for Linux (WSL)

### Creating Virtual Environment

```bash
# Create environment
python3.11 -m venv venv

# Activate environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows
```

### Installing Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
python -c "import streamlit; import torch; import neo4j; print('All packages installed!')"
```

### Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `streamlit` | 1.52+ | Dashboard framework |
| `torch` | 2.0+ | PyTorch (ML framework) |
| `torch-geometric` | 2.3+ | Graph neural networks |
| `neo4j` | 5.0+ | Graph database driver |
| `pandas` | 2.0+ | Data manipulation |
| `plotly` | 5.0+ | Interactive visualizations |
| `scispacy` | 0.5+ | Biomedical NLP |

---

## Running the Dashboard

### Standard Launch

```bash
# From project root
streamlit run app/main.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.x:8501
```

### Custom Port

```bash
# Run on different port
streamlit run app/main.py --server.port 8080
```

### Production Mode

```bash
# Disable development features
streamlit run app/main.py --server.headless true --server.enableCORS false
```

### Configuration Options

Create `.streamlit/config.toml` in project root:

```toml
[server]
port = 8501
headless = true
enableCORS = false
maxUploadSize = 200

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

---

## Neo4j Configuration (Optional)

The dashboard works without Neo4j using pre-loaded data files. However, for live graph queries:

### Option 1: Neo4j Desktop (Recommended for Local Development)

1. **Download**: [Neo4j Desktop](https://neo4j.com/download/)
2. **Create Database**:
   - Click "New" → "Create Graph"
   - Set password (e.g., `your_password`)
   - Click "Start"
3. **Load Data**:
   ```bash
   python scripts/graph/load_to_neo4j.py
   ```

### Option 2: Neo4j Docker

```bash
# Run Neo4j container
docker run -d \
  --name neo4j-medical-kg \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:5.0

# Wait for startup (30 seconds)
sleep 30

# Load data
python scripts/graph/load_to_neo4j.py
```

### Option 3: Neo4j AuraDB (Cloud)

1. **Create free instance**: [Neo4j Aura](https://neo4j.com/cloud/aura-free/)
2. **Save credentials**: Connection URI, username, password
3. **Set environment variables**:
   ```bash
   export NEO4J_URI="neo4j+s://xxxxx.databases.neo4j.io"
   export NEO4J_USER="neo4j"
   export NEO4J_PASSWORD="your_password"
   ```
4. **Load data**:
   ```bash
   python scripts/graph/load_to_neo4j.py
   ```

### Verifying Neo4j Connection

```bash
# Test connection
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'your_password'))
with driver.session() as session:
    result = session.run('MATCH (n) RETURN count(n) as count')
    print(f'Nodes: {result.single()[\"count\"]}')
driver.close()
"
```

**Expected output:**
```
Nodes: 1514
```

### Dashboard Without Neo4j

The dashboard uses these fallback data files if Neo4j is unavailable:
- `data/processed/entities.csv`
- `data/processed/relationships.csv`
- `data/processed/graph_data.pt`
- `data/results/novel_predictions.csv`
- `data/results/validation_report.csv`

All visualizations and features work without Neo4j.

---

## Cloud Deployment

### Option 1: Streamlit Cloud (Easiest, Free)

**Prerequisites:**
- GitHub repository (public or private)
- Streamlit Cloud account (free)

**Steps:**

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Deploy**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select repository: `yourusername/medical-kg-drug-repurposing`
   - Main file path: `app/main.py`
   - Python version: 3.11
   - Click "Deploy"

3. **Configure Secrets** (if using Neo4j):
   - Go to app settings → Secrets
   - Add:
     ```toml
     [neo4j]
     uri = "bolt://your-neo4j-host:7687"
     user = "neo4j"
     password = "your_password"
     ```

**Limitations:**
- 1GB RAM limit
- Public apps are publicly accessible
- No persistent storage (use Neo4j Aura for database)

---

### Option 2: Docker Deployment

**Create `Dockerfile`:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run app
ENTRYPOINT ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Build and run:**

```bash
# Build image
docker build -t medical-kg-dashboard .

# Run container
docker run -p 8501:8501 medical-kg-dashboard
```

**With Neo4j (Docker Compose):**

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.0
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/your_password
    volumes:
      - neo4j-data:/data

  dashboard:
    build: .
    ports:
      - "8501:8501"
    environment:
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: your_password
    depends_on:
      - neo4j

volumes:
  neo4j-data:
```

**Run both services:**

```bash
docker-compose up -d
```

---

### Option 3: AWS Deployment (EC2)

**Launch EC2 Instance:**

1. **Create instance**:
   - AMI: Ubuntu 22.04 LTS
   - Instance type: t3.medium (2 vCPU, 4GB RAM minimum)
   - Security group: Allow ports 22 (SSH), 8501 (Streamlit), 7687 (Neo4j)

2. **Connect and setup**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip

   # Install dependencies
   sudo apt update
   sudo apt install -y python3.11 python3.11-venv git

   # Clone repository
   git clone https://github.com/yourusername/medical-kg-drug-repurposing.git
   cd medical-kg-drug-repurposing

   # Setup virtual environment
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

   # Run with nohup (persists after logout)
   nohup streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0 &
   ```

3. **Access**: `http://your-ec2-ip:8501`

**Production setup with systemd:**

Create `/etc/systemd/system/medical-kg.service`:

```ini
[Unit]
Description=Medical KG Dashboard
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/medical-kg-drug-repurposing
Environment="PATH=/home/ubuntu/medical-kg-drug-repurposing/venv/bin"
ExecStart=/home/ubuntu/medical-kg-drug-repurposing/venv/bin/streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable medical-kg
sudo systemctl start medical-kg
sudo systemctl status medical-kg
```

---

### Option 4: Heroku Deployment

**Setup files:**

1. **Create `Procfile`:**
   ```
   web: streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0
   ```

2. **Create `setup.sh`:**
   ```bash
   mkdir -p ~/.streamlit/
   echo "\
   [server]\n\
   headless = true\n\
   port = $PORT\n\
   enableCORS = false\n\
   \n\
   " > ~/.streamlit/config.toml
   ```

3. **Update `Procfile`:**
   ```
   web: sh setup.sh && streamlit run app/main.py
   ```

**Deploy:**

```bash
# Login to Heroku
heroku login

# Create app
heroku create medical-kg-dashboard

# Set buildpack
heroku buildpacks:set heroku/python

# Deploy
git push heroku main

# Open app
heroku open
```

---

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError: No module named 'streamlit'

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

---

#### 2. Port 8501 already in use

**Solution:**
```bash
# Find and kill process
lsof -ti:8501 | xargs kill -9

# Or run on different port
streamlit run app/main.py --server.port 8080
```

---

#### 3. FileNotFoundError: data/results/novel_predictions.csv

**Solution:**
```bash
# Ensure you're in project root
cd medical-kg-drug-repurposing

# Verify data files exist
ls data/results/

# If missing, regenerate predictions
python scripts/ml/generate_predictions.py
```

---

#### 4. Neo4j connection error

**Solution:**
```bash
# Check Neo4j is running
neo4j status  # or check Docker container

# Verify connection settings
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
print('Connected!')
driver.close()
"

# Dashboard will work without Neo4j using cached data
```

---

#### 5. PyTorch/CUDA issues on GPU

**Solution:**
```bash
# For CPU-only (sufficient for inference)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# For CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

#### 6. Memory issues (dashboard crashes)

**Solution:**
```bash
# Reduce data caching
# Edit app/utils/data_loader.py:
# Change @st.cache_data(ttl=3600) to ttl=600

# Or increase system memory
# Or deploy to larger instance (8GB+ RAM)
```

---

#### 7. Slow dashboard loading

**Solutions:**
- Enable caching (should be default)
- Reduce visualization complexity
- Use smaller dataset for development
- Deploy to faster server

---

## Performance Optimization

### 1. Data Caching

Ensure all data loaders use caching:

```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_predictions():
    return pd.read_csv('data/results/novel_predictions.csv')
```

### 2. Streamlit Configuration

Optimize `.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 200
maxMessageSize = 200
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

### 3. Production Deployment Checklist

- [ ] Use Python 3.11+ for performance improvements
- [ ] Enable data caching with appropriate TTL
- [ ] Minimize data loading on each page
- [ ] Use Plotly's efficient rendering modes
- [ ] Deploy on server with adequate RAM (8GB+)
- [ ] Use CDN for static assets if applicable
- [ ] Enable HTTPS in production
- [ ] Set up monitoring (Datadog, New Relic, etc.)
- [ ] Configure error logging
- [ ] Regular backups of Neo4j database

### 4. Monitoring

**Streamlit built-in metrics:**
- Navigate to `http://localhost:8501/_stcore/health`
- Shows cache performance, memory usage

**Custom monitoring:**
```python
import time
import streamlit as st

start_time = time.time()
# ... load data ...
load_time = time.time() - start_time
st.sidebar.metric("Data Load Time", f"{load_time:.2f}s")
```

---

## Security Best Practices

### 1. Environment Variables

Never hardcode credentials. Use environment variables:

```bash
# .env file (add to .gitignore)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password
```

```python
# Load in Python
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")
```

### 2. Secrets Management

**Streamlit Cloud:**
- Use Secrets management in dashboard
- Access via `st.secrets["neo4j"]["password"]`

**Docker:**
```bash
docker run -p 8501:8501 \
  -e NEO4J_URI=$NEO4J_URI \
  -e NEO4J_PASSWORD=$NEO4J_PASSWORD \
  medical-kg-dashboard
```

### 3. Access Control

For production deployment:
- Use authentication (Streamlit authenticator)
- Enable HTTPS/TLS
- Restrict network access with firewall rules
- Use VPN for sensitive data

---

## Deployment Checklist

### Pre-Deployment

- [ ] All data files present in `data/` directories
- [ ] Dependencies listed in `requirements.txt`
- [ ] Virtual environment tested locally
- [ ] Dashboard runs without errors locally
- [ ] Neo4j connection tested (if using)
- [ ] Environment variables configured
- [ ] `.gitignore` includes sensitive files

### Deployment

- [ ] Repository pushed to GitHub
- [ ] Deployment platform configured
- [ ] Secrets/environment variables set
- [ ] Health check endpoint verified
- [ ] HTTPS enabled (production)
- [ ] Error logging configured

### Post-Deployment

- [ ] Dashboard accessible via public URL
- [ ] All pages load correctly
- [ ] Visualizations render properly
- [ ] Data export functions work
- [ ] Neo4j queries succeed (if applicable)
- [ ] Performance acceptable (<3s load time)
- [ ] Mobile responsiveness checked

---

## Support & Resources

### Documentation
- [Streamlit Documentation](https://docs.streamlit.io)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [PyTorch Geometric](https://pytorch-geometric.readthedocs.io/)

### Project Documentation
- [README.md](../README.md) - Project overview
- [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) - System architecture
- [FILE_DEPENDENCIES.md](FILE_DEPENDENCIES.md) - Data flow and dependencies

### Community
- Streamlit Community: [discuss.streamlit.io](https://discuss.streamlit.io)
- Neo4j Community: [community.neo4j.com](https://community.neo4j.com)

---

## Quick Reference

### Useful Commands

```bash
# Start dashboard
streamlit run app/main.py

# With custom port
streamlit run app/main.py --server.port 8080

# Production mode
streamlit run app/main.py --server.headless true

# Check Streamlit version
streamlit --version

# Clear Streamlit cache
streamlit cache clear

# Neo4j status (Desktop)
neo4j status

# Neo4j start (Desktop)
neo4j start

# Docker Neo4j logs
docker logs neo4j-medical-kg

# Kill process on port 8501
lsof -ti:8501 | xargs kill -9
```

### Directory Structure

```
medical-kg-drug-repurposing/
├── app/
│   ├── main.py              # Dashboard entry point
│   ├── pages/               # Multi-page app
│   └── utils/               # Helper functions
├── data/
│   ├── raw/                 # Original data
│   ├── processed/           # Cleaned data
│   └── results/             # Model outputs
├── scripts/                 # Data pipeline scripts
├── models/                  # Trained models
├── docs/                    # Documentation
├── requirements.txt         # Python dependencies
└── .streamlit/              # Streamlit config
    └── config.toml
```

---

**Last Updated:** January 1, 2026
