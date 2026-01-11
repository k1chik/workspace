#!/usr/bin/env python3
"""
Prepare Training Data - Week 4
Create train/val/test splits with negative sampling for link prediction.

Usage:
    python scripts/ml/prepare_training_data.py
"""

import torch
import numpy as np
from pathlib import Path
import json
from sklearn.model_selection import train_test_split


class TrainingDataPreparator:
    """Prepare training, validation, and test data for link prediction."""

    def __init__(self, graph_data_path='data/processed/graph_data.pt'):
        """Load graph data."""
        print(f"\n📖 Loading graph data from {graph_data_path}...")
        self.data = torch.load(graph_data_path)
        print(f"✅ Loaded: {self.data['x'].shape[0]} nodes, {self.data['edge_index'].shape[1]} edges")

        self.num_drugs = self.data['num_drugs']
        self.num_diseases = self.data['num_diseases']

    def generate_negative_samples(self, num_negatives, existing_edges_set, seed=42):
        """
        Generate negative samples (non-existing drug-disease pairs).

        Args:
            num_negatives: Number of negative samples to generate
            existing_edges_set: Set of existing (drug_idx, disease_idx) tuples
            seed: Random seed

        Returns:
            List of negative edge indices [[drug_idx, disease_idx], ...]
        """
        print(f"\n🎲 Generating {num_negatives} negative samples...")

        np.random.seed(seed)
        negative_edges = []

        # Drug indices: 0 to num_drugs-1
        # Disease indices: num_drugs to num_drugs+num_diseases-1
        drug_indices = list(range(self.num_drugs))
        disease_indices = list(range(self.num_drugs, self.num_drugs + self.num_diseases))

        attempts = 0
        max_attempts = num_negatives * 10

        while len(negative_edges) < num_negatives and attempts < max_attempts:
            # Random drug and disease
            drug_idx = np.random.choice(drug_indices)
            disease_idx = np.random.choice(disease_indices)

            # Check if this edge doesn't exist
            if (drug_idx, disease_idx) not in existing_edges_set:
                negative_edges.append([drug_idx, disease_idx])
                existing_edges_set.add((drug_idx, disease_idx))  # Avoid duplicates

            attempts += 1

        if len(negative_edges) < num_negatives:
            print(f"   ⚠️  Only generated {len(negative_edges)} negative samples (wanted {num_negatives})")
        else:
            print(f"   ✅ Generated {len(negative_edges)} negative samples")

        return negative_edges

    def prepare_splits(self, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, neg_ratio=1.0, seed=42):
        """
        Create train/val/test splits with negative sampling.

        Args:
            train_ratio: Fraction of edges for training
            val_ratio: Fraction of edges for validation
            test_ratio: Fraction of edges for testing
            neg_ratio: Ratio of negative to positive samples (1.0 = equal)
            seed: Random seed
        """
        print("\n" + "=" * 70)
        print("📊 PREPARING TRAINING DATA")
        print("=" * 70)

        # Get positive edges (existing TREATS relationships)
        positive_edges = self.data['edge_index'].t().numpy()  # [num_edges, 2]
        num_pos = len(positive_edges)

        print(f"\nPositive edges: {num_pos}")
        print(f"Train/Val/Test split: {train_ratio}/{val_ratio}/{test_ratio}")
        print(f"Negative sampling ratio: {neg_ratio}:1")

        # Create set of existing edges for fast lookup
        existing_edges_set = set(map(tuple, positive_edges))

        # Split positive edges
        print(f"\n📐 Splitting positive edges...")
        train_pos, temp = train_test_split(
            positive_edges,
            train_size=train_ratio,
            random_state=seed
        )

        val_size = val_ratio / (val_ratio + test_ratio)
        val_pos, test_pos = train_test_split(
            temp,
            train_size=val_size,
            random_state=seed
        )

        print(f"   - Train positive: {len(train_pos)}")
        print(f"   - Val positive:   {len(val_pos)}")
        print(f"   - Test positive:  {len(test_pos)}")

        # Generate negative samples for each split
        num_train_neg = int(len(train_pos) * neg_ratio)
        num_val_neg = int(len(val_pos) * neg_ratio)
        num_test_neg = int(len(test_pos) * neg_ratio)

        train_neg = self.generate_negative_samples(num_train_neg, existing_edges_set.copy(), seed=seed)
        val_neg = self.generate_negative_samples(num_val_neg, existing_edges_set.copy(), seed=seed+1)
        test_neg = self.generate_negative_samples(num_test_neg, existing_edges_set.copy(), seed=seed+2)

        # Combine positive and negative edges
        train_edges = np.vstack([train_pos, train_neg])
        val_edges = np.vstack([val_pos, val_neg])
        test_edges = np.vstack([test_pos, test_neg])

        # Create labels (1 for positive, 0 for negative)
        train_labels = np.concatenate([
            np.ones(len(train_pos)),
            np.zeros(len(train_neg))
        ])
        val_labels = np.concatenate([
            np.ones(len(val_pos)),
            np.zeros(len(val_neg))
        ])
        test_labels = np.concatenate([
            np.ones(len(test_pos)),
            np.zeros(len(test_neg))
        ])

        # Shuffle
        np.random.seed(seed)
        train_perm = np.random.permutation(len(train_edges))
        val_perm = np.random.permutation(len(val_edges))
        test_perm = np.random.permutation(len(test_edges))

        train_edges = train_edges[train_perm]
        train_labels = train_labels[train_perm]
        val_edges = val_edges[val_perm]
        val_labels = val_labels[val_perm]
        test_edges = test_edges[test_perm]
        test_labels = test_labels[test_perm]

        # Convert to PyTorch tensors
        train_data = {
            'x': self.data['x'],  # Node features (shared across splits)
            'edge_index': torch.LongTensor(train_edges).t().contiguous(),
            'labels': torch.FloatTensor(train_labels),
            'num_pos': len(train_pos),
            'num_neg': len(train_neg)
        }

        val_data = {
            'x': self.data['x'],
            'edge_index': torch.LongTensor(val_edges).t().contiguous(),
            'labels': torch.FloatTensor(val_labels),
            'num_pos': len(val_pos),
            'num_neg': len(val_neg)
        }

        test_data = {
            'x': self.data['x'],
            'edge_index': torch.LongTensor(test_edges).t().contiguous(),
            'labels': torch.FloatTensor(test_labels),
            'num_pos': len(test_pos),
            'num_neg': len(test_neg)
        }

        # Save splits
        print(f"\n💾 Saving data splits...")
        torch.save(train_data, 'data/processed/train_data.pt')
        torch.save(val_data, 'data/processed/val_data.pt')
        torch.save(test_data, 'data/processed/test_data.pt')

        print(f"   ✅ Train data: data/processed/train_data.pt")
        print(f"   ✅ Val data:   data/processed/val_data.pt")
        print(f"   ✅ Test data:  data/processed/test_data.pt")

        # Save statistics
        stats = {
            'train': {
                'total': len(train_edges),
                'positive': int(len(train_pos)),
                'negative': int(len(train_neg)),
                'pos_ratio': float(len(train_pos) / len(train_edges))
            },
            'val': {
                'total': len(val_edges),
                'positive': int(len(val_pos)),
                'negative': int(len(val_neg)),
                'pos_ratio': float(len(val_pos) / len(val_edges))
            },
            'test': {
                'total': len(test_edges),
                'positive': int(len(test_pos)),
                'negative': int(len(test_neg)),
                'pos_ratio': float(len(test_pos) / len(test_edges))
            },
            'parameters': {
                'train_ratio': train_ratio,
                'val_ratio': val_ratio,
                'test_ratio': test_ratio,
                'neg_ratio': neg_ratio,
                'seed': seed
            }
        }

        with open('data/processed/split_statistics.json', 'w') as f:
            json.dump(stats, f, indent=2)

        # Print summary
        print("\n" + "=" * 70)
        print("📊 DATA SPLIT SUMMARY")
        print("=" * 70)
        print(f"\n{'Split':<10} {'Total':<10} {'Positive':<10} {'Negative':<10} {'Pos %':<10}")
        print("-" * 70)
        print(f"{'Train':<10} {stats['train']['total']:<10} {stats['train']['positive']:<10} "
              f"{stats['train']['negative']:<10} {stats['train']['pos_ratio']*100:<10.1f}")
        print(f"{'Val':<10} {stats['val']['total']:<10} {stats['val']['positive']:<10} "
              f"{stats['val']['negative']:<10} {stats['val']['pos_ratio']*100:<10.1f}")
        print(f"{'Test':<10} {stats['test']['total']:<10} {stats['test']['positive']:<10} "
              f"{stats['test']['negative']:<10} {stats['test']['pos_ratio']*100:<10.1f}")
        print("=" * 70)
        print("✅ Training data preparation complete!")
        print("=" * 70)

        return train_data, val_data, test_data, stats


def main():
    """Main execution."""
    preparator = TrainingDataPreparator()
    train_data, val_data, test_data, stats = preparator.prepare_splits(
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        neg_ratio=1.0,  # Equal number of positive and negative samples
        seed=42
    )

    print("\n🔍 Quick validation:")
    print(f"   Train edges shape: {train_data['edge_index'].shape}")
    print(f"   Train labels shape: {train_data['labels'].shape}")
    print(f"   Label distribution: {train_data['labels'].sum():.0f} positive, "
          f"{(1-train_data['labels']).sum():.0f} negative")
    print(f"\n✅ Ready for model training!")


if __name__ == '__main__':
    main()
