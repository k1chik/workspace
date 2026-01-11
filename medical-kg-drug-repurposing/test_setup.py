#!/usr/bin/env python3
"""Test M1 setup for Medical Knowledge Graph project"""

print("Testing imports...\n")

# Test NumPy
try:
    import numpy as np
    print(f"✅ NumPy {np.__version__}")
except Exception as e:
    print(f"❌ NumPy failed: {e}")

# Test Pandas
try:
    import pandas as pd
    print(f"✅ Pandas {pd.__version__}")
except Exception as e:
    print(f"❌ Pandas failed: {e}")

# Test PyTorch
try:
    import torch
    print(f"✅ PyTorch {torch.__version__}")
except Exception as e:
    print(f"❌ PyTorch failed: {e}")

# Test MPS (M1 GPU)
try:
    import torch
    if torch.backends.mps.is_available():
        print(f"✅ MPS (M1 GPU) available")
        # Quick GPU test
        x = torch.randn(100, 100, device="mps")
        y = torch.randn(100, 100, device="mps")
        z = torch.mm(x, y)
        print(f"✅ MPS computation successful")
    else:
        print(f"⚠️  MPS not available (CPU only)")
except Exception as e:
    print(f"⚠️  MPS test failed: {e}")

# Test PyTorch Geometric
try:
    import torch_geometric
    print(f"✅ PyTorch Geometric {torch_geometric.__version__}")
except Exception as e:
    print(f"❌ PyTorch Geometric failed: {e}")

# Test Transformers
try:
    import transformers
    print(f"✅ Transformers {transformers.__version__}")
except Exception as e:
    print(f"❌ Transformers failed: {e}")

# Test SpaCy
try:
    import spacy
    print(f"✅ SpaCy {spacy.__version__}")
    # Test loading models
    try:
        nlp = spacy.load('en_core_web_sm')
        print(f"✅ SpaCy model 'en_core_web_sm' loaded")
    except:
        print(f"⚠️  SpaCy model 'en_core_web_sm' not found")

    try:
        nlp_sci = spacy.load('en_core_sci_sm')
        print(f"✅ SciSpacy model 'en_core_sci_sm' loaded")
    except:
        print(f"⚠️  SciSpacy model 'en_core_sci_sm' not found")
except Exception as e:
    print(f"❌ SpaCy failed: {e}")

# Test NetworkX
try:
    import networkx as nx
    print(f"✅ NetworkX {nx.__version__}")
except Exception as e:
    print(f"❌ NetworkX failed: {e}")

# Test Neo4j driver
try:
    import neo4j
    print(f"✅ Neo4j driver {neo4j.__version__}")
except Exception as e:
    print(f"❌ Neo4j driver failed: {e}")

# Test Streamlit
try:
    import streamlit as st
    print(f"✅ Streamlit {st.__version__}")
except Exception as e:
    print(f"❌ Streamlit failed: {e}")

# Test Matplotlib
try:
    import matplotlib
    print(f"✅ Matplotlib {matplotlib.__version__}")
except Exception as e:
    print(f"❌ Matplotlib failed: {e}")

# Test Seaborn
try:
    import seaborn as sns
    print(f"✅ Seaborn {sns.__version__}")
except Exception as e:
    print(f"❌ Seaborn failed: {e}")

# Test Plotly
try:
    import plotly
    print(f"✅ Plotly {plotly.__version__}")
except Exception as e:
    print(f"❌ Plotly failed: {e}")

# Test Jupyter
try:
    import jupyter
    print(f"✅ Jupyter {jupyter.__version__}")
except Exception as e:
    print(f"❌ Jupyter failed: {e}")

print("\n" + "="*50)
print("✅ Setup test complete! You're ready to start.")
print("="*50)
