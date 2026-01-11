#!/usr/bin/env python3
"""
Export Graph Data from Neo4j - Week 4
Convert Neo4j knowledge graph to PyTorch Geometric format for GNN training.

Usage:
    python scripts/ml/export_graph_data.py
"""

import torch
import pandas as pd
import numpy as np
from neo4j import GraphDatabase
import json
from pathlib import Path
from collections import defaultdict


class GraphDataExporter:
    """Export graph data from Neo4j to PyTorch Geometric format."""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="drugrepurposing2024"):
        """Initialize Neo4j connection."""
        print(f"\n🔌 Connecting to Neo4j at {uri}...")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"✅ Connected")

    def close(self):
        """Close Neo4j connection."""
        self.driver.close()

    def export_nodes(self):
        """Export all nodes with features."""
        print("\n📦 Exporting nodes...")

        with self.driver.session() as session:
            # Get all Drug nodes
            drugs = session.run("""
                MATCH (d:Drug)
                RETURN d.id as id,
                       d.name as name,
                       d.frequency as frequency,
                       d.num_papers as num_papers
                ORDER BY d.id
            """).data()

            # Get all Disease nodes
            diseases = session.run("""
                MATCH (dis:Disease)
                RETURN dis.id as id,
                       dis.name as name,
                       dis.frequency as frequency,
                       dis.num_papers as num_papers
                ORDER BY dis.id
            """).data()

        print(f"   - Drugs: {len(drugs)}")
        print(f"   - Diseases: {len(diseases)}")

        return drugs, diseases

    def create_node_mappings(self, drugs, diseases):
        """Create mapping from node ID to integer index."""
        print("\n🗺️  Creating node mappings...")

        # Create ID to index mapping
        node_to_idx = {}
        idx_to_node = {}
        node_features = []
        node_labels = []  # 0 for drug, 1 for disease

        idx = 0

        # Add drugs
        for drug in drugs:
            node_to_idx[drug['id']] = idx
            idx_to_node[idx] = {
                'id': drug['id'],
                'name': drug['name'],
                'type': 'drug'
            }
            node_features.append([
                float(drug['frequency']),
                float(drug['num_papers'])
            ])
            node_labels.append(0)  # Drug
            idx += 1

        # Add diseases
        for disease in diseases:
            node_to_idx[disease['id']] = idx
            idx_to_node[idx] = {
                'id': disease['id'],
                'name': disease['name'],
                'type': 'disease'
            }
            node_features.append([
                float(disease['frequency']),
                float(disease['num_papers'])
            ])
            node_labels.append(1)  # Disease
            idx += 1

        print(f"   - Total nodes: {len(node_to_idx)}")

        return node_to_idx, idx_to_node, node_features, node_labels

    def export_edges(self, node_to_idx):
        """Export all TREATS relationships."""
        print("\n🔗 Exporting edges...")

        with self.driver.session() as session:
            edges = session.run("""
                MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
                RETURN d.id as drug_id,
                       dis.id as disease_id,
                       r.confidence as confidence,
                       r.num_papers as num_papers
            """).data()

        print(f"   - Total edges: {len(edges)}")

        # Convert to edge indices
        edge_index = []
        edge_attr = []

        for edge in edges:
            drug_idx = node_to_idx.get(edge['drug_id'])
            disease_idx = node_to_idx.get(edge['disease_id'])

            if drug_idx is not None and disease_idx is not None:
                edge_index.append([drug_idx, disease_idx])
                edge_attr.append([
                    float(edge['confidence']),
                    float(edge['num_papers'])
                ])

        print(f"   - Valid edges: {len(edge_index)}")

        return edge_index, edge_attr

    def normalize_features(self, features):
        """Normalize node features (z-score normalization)."""
        features = np.array(features, dtype=np.float32)
        mean = features.mean(axis=0)
        std = features.std(axis=0)
        std[std == 0] = 1  # Avoid division by zero
        features = (features - mean) / std
        return features, mean, std

    def export_graph(self, output_path='data/processed/graph_data.pt'):
        """Export complete graph data."""
        print("=" * 70)
        print("📊 EXPORTING GRAPH DATA FROM NEO4J")
        print("=" * 70)

        # Export nodes
        drugs, diseases = self.export_nodes()

        # Create mappings
        node_to_idx, idx_to_node, node_features, node_labels = \
            self.create_node_mappings(drugs, diseases)

        # Export edges
        edge_index, edge_attr = self.export_edges(node_to_idx)

        # Normalize features
        print("\n🔧 Normalizing features...")
        node_features_norm, feat_mean, feat_std = self.normalize_features(node_features)

        # Convert to PyTorch tensors
        print("\n🔥 Converting to PyTorch tensors...")
        data = {
            'x': torch.FloatTensor(node_features_norm),
            'edge_index': torch.LongTensor(edge_index).t().contiguous(),
            'edge_attr': torch.FloatTensor(edge_attr),
            'node_labels': torch.LongTensor(node_labels),
            'node_to_idx': node_to_idx,
            'idx_to_node': idx_to_node,
            'feature_mean': feat_mean.tolist(),
            'feature_std': feat_std.tolist(),
            'num_drugs': len(drugs),
            'num_diseases': len(diseases)
        }

        # Save to disk
        print(f"\n💾 Saving to {output_path}...")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(data, output_path)

        # Save node mapping as JSON for reference
        mapping_path = output_path.replace('.pt', '_mapping.json')
        with open(mapping_path, 'w') as f:
            json.dump({
                'idx_to_node': {str(k): v for k, v in idx_to_node.items()},
                'statistics': {
                    'total_nodes': len(node_to_idx),
                    'num_drugs': len(drugs),
                    'num_diseases': len(diseases),
                    'total_edges': len(edge_index)
                }
            }, f, indent=2)

        print(f"✅ Mapping saved to {mapping_path}")

        # Print summary
        print("\n" + "=" * 70)
        print("📊 EXPORT SUMMARY")
        print("=" * 70)
        print(f"Total Nodes:        {data['x'].shape[0]:,}")
        print(f"  - Drugs:          {len(drugs):,}")
        print(f"  - Diseases:       {len(diseases):,}")
        print(f"Node Features:      {data['x'].shape[1]}")
        print(f"Total Edges:        {data['edge_index'].shape[1]:,}")
        print(f"Edge Features:      {data['edge_attr'].shape[1]}")
        print(f"\nFeature Dimensions:")
        print(f"  - Frequency (normalized)")
        print(f"  - Num Papers (normalized)")
        print("=" * 70)
        print(f"✅ Graph data exported successfully!")
        print("=" * 70)

        return data


def main():
    """Main execution."""
    exporter = GraphDataExporter()

    try:
        data = exporter.export_graph()

        print("\n🔍 Quick validation:")
        print(f"   Node features shape: {data['x'].shape}")
        print(f"   Edge index shape: {data['edge_index'].shape}")
        print(f"   Edge attributes shape: {data['edge_attr'].shape}")
        print(f"\n✅ Ready for training data preparation!")

    finally:
        exporter.close()


if __name__ == '__main__':
    main()
