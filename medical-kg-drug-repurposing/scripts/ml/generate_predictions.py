#!/usr/bin/env python3
"""
Generate Novel Predictions - Week 4
Generate drug repurposing candidates using trained GNN model.

Usage:
    python scripts/ml/generate_predictions.py --top-k 100
"""

import torch
import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import sys
sys.path.append('.')
from models.gnn_link_predictor import create_model


class PredictionGenerator:
    """Generate novel drug-disease link predictions."""

    def __init__(self, model_path='models/checkpoints/best_model.pt', device='cpu'):
        self.device = device

        # Load model
        print(f"\n📖 Loading trained model from {model_path}...")
        checkpoint = torch.load(model_path, map_location=device)

        self.model = create_model(
            in_channels=2,
            hidden_channels=64,
            out_channels=32,
            dropout=0.5
        ).to(device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()

        print(f"✅ Model loaded (epoch {checkpoint['epoch']}, val AUC: {checkpoint['val_auc']:.4f})")

    def load_entity_mapping(self):
        """Load entity ID to index mapping and metadata."""
        print(f"\n📖 Loading entity data...")

        # Load graph data for node features
        graph_data = torch.load('data/processed/graph_data.pt')

        # Load original entities for metadata
        entities_df = pd.read_csv('data/processed/entities.csv')

        # Create entity mapping (index -> entity info)
        entity_map = {}
        for idx, row in entities_df.iterrows():
            entity_map[idx] = {
                'entity_id': row['entity_id'],
                'entity_text': row['entity_text'],
                'entity_type': row['entity_type'],
                'frequency': row['frequency'],
                'num_papers': row['num_papers']
            }

        # Get drug and disease indices
        drug_indices = [idx for idx, info in entity_map.items() if info['entity_type'] == 'CHEMICAL']
        disease_indices = [idx for idx, info in entity_map.items() if info['entity_type'] == 'DISEASE']

        print(f"   ✅ Loaded {len(entity_map)} entities")
        print(f"   ✅ Drugs: {len(drug_indices)}, Diseases: {len(disease_indices)}")

        return graph_data, entity_map, drug_indices, disease_indices

    def get_existing_edges(self):
        """Get all existing drug-disease edges (to exclude from predictions)."""
        print(f"\n📖 Loading existing relationships...")

        # Load all data splits
        train_data = torch.load('data/processed/train_data.pt')
        val_data = torch.load('data/processed/val_data.pt')
        test_data = torch.load('data/processed/test_data.pt')

        # Collect all positive edges
        existing_edges = set()

        for data in [train_data, val_data, test_data]:
            edge_index = data['edge_index']
            labels = data['labels']

            # Only keep positive edges
            pos_mask = labels == 1
            pos_edges = edge_index[:, pos_mask]

            for i in range(pos_edges.shape[1]):
                src, dst = pos_edges[0, i].item(), pos_edges[1, i].item()
                existing_edges.add((src, dst))
                existing_edges.add((dst, src))  # Undirected

        print(f"   ✅ Found {len(existing_edges) // 2} existing relationships")

        return existing_edges

    @torch.no_grad()
    def predict_batch(self, graph_data, edge_candidates, batch_size=1000):
        """
        Predict probabilities for a batch of edge candidates.

        Args:
            graph_data: Graph structure and node features
            edge_candidates: List of (src, dst) tuples
            batch_size: Batch size for prediction

        Returns:
            Array of prediction probabilities
        """
        x = graph_data['x'].to(self.device)
        full_edge_index = graph_data['edge_index'].to(self.device)

        all_probs = []

        for i in range(0, len(edge_candidates), batch_size):
            batch = edge_candidates[i:i + batch_size]

            # Create edge_label_index
            edge_label_index = torch.tensor(batch, dtype=torch.long).t().to(self.device)

            # Predict
            logits = self.model(x, full_edge_index, edge_label_index)
            probs = torch.sigmoid(logits).cpu().numpy()

            all_probs.extend(probs)

        return np.array(all_probs)

    def generate_candidates(self, graph_data, entity_map, drug_indices, disease_indices,
                          existing_edges, top_k=100):
        """
        Generate top-K novel drug-disease predictions.

        Args:
            graph_data: Graph structure and node features
            entity_map: Entity metadata
            drug_indices: List of drug node indices
            disease_indices: List of disease node indices
            existing_edges: Set of existing edges to exclude
            top_k: Number of top predictions to return

        Returns:
            DataFrame of top predictions
        """
        print(f"\n🔮 Generating predictions for all novel drug-disease pairs...")

        # Generate all possible drug-disease pairs
        all_candidates = []
        for drug_idx in drug_indices:
            for disease_idx in disease_indices:
                # Skip if edge already exists
                if (drug_idx, disease_idx) not in existing_edges:
                    all_candidates.append((drug_idx, disease_idx))

        print(f"   Total candidate pairs: {len(all_candidates):,}")

        # Predict in batches
        print(f"   Predicting in batches...")
        probabilities = self.predict_batch(graph_data, all_candidates, batch_size=2000)

        # Rank by probability
        print(f"   Ranking predictions...")
        top_indices = np.argsort(probabilities)[::-1][:top_k]

        # Create results dataframe
        predictions = []
        for rank, idx in enumerate(top_indices, 1):
            drug_idx, disease_idx = all_candidates[idx]
            prob = probabilities[idx]

            drug_info = entity_map[drug_idx]
            disease_info = entity_map[disease_idx]

            predictions.append({
                'rank': rank,
                'drug': drug_info['entity_text'],
                'drug_id': drug_info['entity_id'],
                'disease': disease_info['entity_text'],
                'disease_id': disease_info['entity_id'],
                'confidence': float(prob),
                'drug_frequency': drug_info['frequency'],
                'disease_frequency': disease_info['frequency'],
                'drug_num_papers': drug_info['num_papers'],
                'disease_num_papers': disease_info['num_papers']
            })

        predictions_df = pd.DataFrame(predictions)

        print(f"   ✅ Generated top {len(predictions_df)} predictions")
        print(f"   Confidence range: [{predictions_df['confidence'].min():.4f}, {predictions_df['confidence'].max():.4f}]")

        return predictions_df


def main():
    parser = argparse.ArgumentParser(description='Generate drug repurposing predictions')
    parser.add_argument('--top-k', type=int, default=100, help='Number of top predictions')
    parser.add_argument('--device', type=str, default='auto', help='Device (cpu/mps/cuda/auto)')

    args = parser.parse_args()

    # Determine device
    if args.device == 'auto':
        if torch.cuda.is_available():
            device = 'cuda'
        elif torch.backends.mps.is_available():
            device = 'mps'
        else:
            device = 'cpu'
    else:
        device = args.device

    print(f"🔧 Using device: {device}")

    # Initialize generator
    generator = PredictionGenerator(device=device)

    # Load data
    graph_data, entity_map, drug_indices, disease_indices = generator.load_entity_mapping()
    existing_edges = generator.get_existing_edges()

    # Generate predictions
    print("\n" + "=" * 70)
    print("🎯 GENERATING NOVEL DRUG-DISEASE PREDICTIONS")
    print("=" * 70)

    predictions_df = generator.generate_candidates(
        graph_data=graph_data,
        entity_map=entity_map,
        drug_indices=drug_indices,
        disease_indices=disease_indices,
        existing_edges=existing_edges,
        top_k=args.top_k
    )

    # Save predictions
    print(f"\n💾 Saving predictions...")
    output_path = 'data/results/novel_predictions.csv'
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    predictions_df.to_csv(output_path, index=False)
    print(f"   ✅ Saved to {output_path}")

    # Print sample predictions
    print("\n" + "=" * 70)
    print(f"🏆 TOP 10 DRUG REPURPOSING CANDIDATES")
    print("=" * 70)
    print(f"{'Rank':<6} {'Drug':<25} {'Disease':<30} {'Confidence':<12}")
    print("-" * 70)

    for _, row in predictions_df.head(10).iterrows():
        drug = row['drug'][:23] + '..' if len(row['drug']) > 25 else row['drug']
        disease = row['disease'][:28] + '..' if len(row['disease']) > 30 else row['disease']
        print(f"{row['rank']:<6} {drug:<25} {disease:<30} {row['confidence']:<12.4f}")

    print("=" * 70)

    # Print statistics
    print(f"\n📊 PREDICTION STATISTICS")
    print(f"Total predictions: {len(predictions_df)}")
    print(f"High confidence (≥0.8): {(predictions_df['confidence'] >= 0.8).sum()}")
    print(f"Medium confidence (0.6-0.8): {((predictions_df['confidence'] >= 0.6) & (predictions_df['confidence'] < 0.8)).sum()}")
    print(f"Lower confidence (<0.6): {(predictions_df['confidence'] < 0.6).sum()}")

    print(f"\n✅ Prediction generation complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
