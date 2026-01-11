"""
Data Loader Utilities
Load and cache data for Streamlit dashboard.
"""

import streamlit as st
import pandas as pd
import json
import torch
from neo4j import GraphDatabase
from pathlib import Path


@st.cache_data
def load_predictions():
    """Load GNN predictions."""
    predictions_path = 'data/results/novel_predictions.csv'
    return pd.read_csv(predictions_path)


@st.cache_data
def load_validation_results():
    """Load validation results if available."""
    validation_path = 'data/results/validation_report.csv'
    if Path(validation_path).exists():
        return pd.read_csv(validation_path)
    return None


@st.cache_data
def load_validation_summary():
    """Load validation summary if available."""
    summary_path = 'data/results/validation_summary.json'
    if Path(summary_path).exists():
        with open(summary_path, 'r') as f:
            return json.load(f)
    return None


@st.cache_data
def load_training_history():
    """Load model training history."""
    history_path = 'data/results/training_history.json'
    with open(history_path, 'r') as f:
        return json.load(f)


@st.cache_data
def load_test_metrics():
    """Load test set evaluation metrics."""
    metrics_path = 'data/results/test_metrics.json'
    with open(metrics_path, 'r') as f:
        return json.load(f)


@st.cache_data
def load_entities():
    """Load entity data (normalized with PubChem info)."""
    # Try normalized entities first (with PubChem data)
    normalized_path = 'data/processed/entities_normalized.csv'
    if Path(normalized_path).exists():
        return pd.read_csv(normalized_path)
    # Fallback to regular entities
    entities_path = 'data/processed/entities.csv'
    return pd.read_csv(entities_path)


@st.cache_data
def load_pubchem_data():
    """Load PubChem reference data."""
    pubchem_path = 'data/raw/pubchem_drugs.csv'
    if Path(pubchem_path).exists():
        return pd.read_csv(pubchem_path)
    return None


@st.cache_data
def load_relationships():
    """Load relationship data."""
    relationships_path = 'data/processed/relationships.csv'
    return pd.read_csv(relationships_path)


@st.cache_data
def load_graph_data():
    """Load PyTorch graph data."""
    graph_path = 'data/processed/graph_data.pt'
    return torch.load(graph_path)


class Neo4jConnection:
    """Neo4j database connection for live queries."""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="drugrepurposing2024"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query(self, query, parameters=None):
        """Execute Cypher query and return results."""
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]


@st.cache_resource
def get_neo4j_connection():
    """Get cached Neo4j connection."""
    return Neo4jConnection()


def get_graph_stats():
    """Get knowledge graph statistics."""
    entities = load_entities()
    relationships = load_relationships()

    stats = {
        'total_nodes': len(entities),
        'total_drugs': (entities['entity_type'] == 'CHEMICAL').sum(),
        'total_diseases': (entities['entity_type'] == 'DISEASE').sum(),
        'total_relationships': len(relationships),
        'avg_confidence': relationships['confidence'].mean() if 'confidence' in relationships.columns else 0,
        'unique_papers': entities['num_papers'].sum()
    }

    return stats


def get_model_stats():
    """Get model performance statistics."""
    metrics = load_test_metrics()

    stats = {
        'test_auc': metrics.get('auc_roc', 0),
        'test_ap': metrics.get('auc_pr', 0),
        'test_accuracy': metrics.get('accuracy', 0),
        'test_precision': metrics.get('precision', 0),
        'test_recall': metrics.get('recall', 0),
        'test_f1': metrics.get('f1', 0),
        'p_at_10': metrics.get('p@10', 0),
        'p_at_20': metrics.get('p@20', 0),
        'p_at_50': metrics.get('p@50', 0),
        'p_at_100': metrics.get('p@100', 0)
    }

    return stats


def get_prediction_stats():
    """Get prediction statistics."""
    predictions = load_predictions()
    validation = load_validation_results()

    stats = {
        'total_predictions': len(predictions),
        'avg_confidence': predictions['confidence'].mean(),
        'min_confidence': predictions['confidence'].min(),
        'max_confidence': predictions['confidence'].max(),
        'high_confidence_count': (predictions['confidence'] >= 0.9).sum()
    }

    if validation is not None:
        stats['validated_count'] = len(validation)
        stats['confirmed_count'] = (validation['validation_status'] == 'Confirmed').sum()
        stats['emerging_count'] = (validation['validation_status'] == 'Emerging').sum()
        stats['novel_count'] = (validation['validation_status'] == 'Novel').sum()

    return stats
