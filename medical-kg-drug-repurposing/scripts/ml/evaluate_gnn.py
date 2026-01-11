#!/usr/bin/env python3
"""
Evaluate GNN Model - Week 4
Evaluate trained model on test set and generate metrics.

Usage:
    python scripts/ml/evaluate_gnn.py
"""

import torch
import torch.nn.functional as F
from sklearn.metrics import (roc_auc_score, average_precision_score,
                            accuracy_score, precision_score, recall_score,
                            f1_score, confusion_matrix, roc_curve,
                            precision_recall_curve)
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
sys.path.append('.')
from models.gnn_link_predictor import create_model


class ModelEvaluator:
    """Evaluate GNN link predictor on test set."""

    def __init__(self, model_path='models/checkpoints/best_model.pt', device='cpu'):
        self.device = device

        # Load model
        print(f"\n📖 Loading model from {model_path}...")
        checkpoint = torch.load(model_path, map_location=device)

        self.model = create_model(
            in_channels=2,
            hidden_channels=64,
            out_channels=32,
            dropout=0.5
        ).to(device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()

        print(f"✅ Model loaded (trained epoch {checkpoint['epoch']}, val AUC: {checkpoint['val_auc']:.4f})")

    @torch.no_grad()
    def predict(self, data, full_edge_index):
        """Get model predictions."""
        x = data['x'].to(self.device)
        edge_label_index = data['edge_index'].to(self.device)
        full_edge_index = full_edge_index.to(self.device)

        # Forward pass
        logits = self.model(x, full_edge_index, edge_label_index)
        probs = torch.sigmoid(logits)

        return probs.cpu().numpy()

    def compute_metrics(self, y_true, y_pred_probs, threshold=0.5):
        """Compute classification metrics."""
        y_pred = (y_pred_probs >= threshold).astype(int)

        metrics = {
            'auc_roc': float(roc_auc_score(y_true, y_pred_probs)),
            'auc_pr': float(average_precision_score(y_true, y_pred_probs)),
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'precision': float(precision_score(y_true, y_pred, zero_division=0)),
            'recall': float(recall_score(y_true, y_pred, zero_division=0)),
            'f1': float(f1_score(y_true, y_pred, zero_division=0))
        }

        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        metrics['tn'] = int(cm[0, 0])
        metrics['fp'] = int(cm[0, 1])
        metrics['fn'] = int(cm[1, 0])
        metrics['tp'] = int(cm[1, 1])

        return metrics

    def compute_precision_at_k(self, y_true, y_pred_probs, k_values=[10, 20, 50, 100]):
        """Compute Precision@K."""
        precision_at_k = {}

        # Get top-K predictions
        top_k_indices = np.argsort(y_pred_probs)[::-1]

        for k in k_values:
            if k > len(y_true):
                continue

            top_k_labels = y_true[top_k_indices[:k]]
            precision = top_k_labels.sum() / k
            precision_at_k[f'p@{k}'] = float(precision)

        return precision_at_k

    def plot_roc_curve(self, y_true, y_pred_probs, save_path='data/visualizations/roc_curve.png'):
        """Plot ROC curve."""
        fpr, tpr, thresholds = roc_curve(y_true, y_pred_probs)
        auc = roc_auc_score(y_true, y_pred_probs)

        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {auc:.4f})', linewidth=2)
        plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier', linewidth=1)
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title('ROC Curve - Drug-Disease Link Prediction', fontsize=14, fontweight='bold')
        plt.legend(fontsize=11)
        plt.grid(alpha=0.3)
        plt.tight_layout()

        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300)
        print(f"   ✅ ROC curve saved to {save_path}")
        plt.close()

    def plot_pr_curve(self, y_true, y_pred_probs, save_path='data/visualizations/pr_curve.png'):
        """Plot Precision-Recall curve."""
        precision, recall, thresholds = precision_recall_curve(y_true, y_pred_probs)
        ap = average_precision_score(y_true, y_pred_probs)

        plt.figure(figsize=(8, 6))
        plt.plot(recall, precision, label=f'PR Curve (AP = {ap:.4f})', linewidth=2)
        plt.xlabel('Recall', fontsize=12)
        plt.ylabel('Precision', fontsize=12)
        plt.title('Precision-Recall Curve - Drug-Disease Link Prediction', fontsize=14, fontweight='bold')
        plt.legend(fontsize=11)
        plt.grid(alpha=0.3)
        plt.tight_layout()

        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300)
        print(f"   ✅ PR curve saved to {save_path}")
        plt.close()

    def evaluate(self, test_data, full_edge_index):
        """Full evaluation on test set."""
        print("\n" + "=" * 70)
        print("📊 EVALUATING ON TEST SET")
        print("=" * 70)

        # Get predictions
        print(f"\n🔮 Generating predictions...")
        y_pred_probs = self.predict(test_data, full_edge_index)
        y_true = test_data['labels'].numpy()

        print(f"   Test samples: {len(y_true)}")
        print(f"   Positive: {y_true.sum():.0f}, Negative: {(1-y_true).sum():.0f}")

        # Compute metrics
        print(f"\n📈 Computing metrics...")
        metrics = self.compute_metrics(y_true, y_pred_probs)
        precision_at_k = self.compute_precision_at_k(y_true, y_pred_probs)
        metrics.update(precision_at_k)

        # Plot curves
        print(f"\n📊 Generating plots...")
        self.plot_roc_curve(y_true, y_pred_probs)
        self.plot_pr_curve(y_true, y_pred_probs)

        # Save metrics
        print(f"\n💾 Saving metrics...")
        with open('data/results/test_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"   ✅ Saved to data/results/test_metrics.json")

        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST SET RESULTS")
        print("=" * 70)
        print(f"AUC-ROC:          {metrics['auc_roc']:.4f}")
        print(f"AUC-PR:           {metrics['auc_pr']:.4f}")
        print(f"Accuracy:         {metrics['accuracy']:.4f}")
        print(f"Precision:        {metrics['precision']:.4f}")
        print(f"Recall:           {metrics['recall']:.4f}")
        print(f"F1-Score:         {metrics['f1']:.4f}")
        print(f"\nConfusion Matrix:")
        print(f"  TN: {metrics['tn']:<6} FP: {metrics['fp']:<6}")
        print(f"  FN: {metrics['fn']:<6} TP: {metrics['tp']:<6}")
        print(f"\nPrecision@K:")
        for k, v in precision_at_k.items():
            print(f"  {k}: {v:.4f}")
        print("=" * 70)

        if metrics['auc_roc'] >= 0.75:
            print(f"\n✅ SUCCESS! Test AUC ({metrics['auc_roc']:.4f}) exceeds target (0.75)")
        else:
            print(f"\n⚠️  Test AUC ({metrics['auc_roc']:.4f}) below target (0.75)")

        print("=" * 70)

        return metrics


def main():
    # Determine device
    if torch.cuda.is_available():
        device = 'cuda'
    elif torch.backends.mps.is_available():
        device = 'mps'
    else:
        device = 'cpu'

    print(f"\n🔧 Using device: {device}")

    # Load test data
    print(f"\n📖 Loading test data...")
    test_data = torch.load('data/processed/test_data.pt')
    train_data = torch.load('data/processed/train_data.pt')

    print(f"   ✅ Test samples: {len(test_data['labels'])}")

    # Use training edges for message passing
    train_positive_edges = train_data['edge_index'][:, :train_data['num_pos']]

    # Evaluate
    evaluator = ModelEvaluator(device=device)
    metrics = evaluator.evaluate(test_data, train_positive_edges)


if __name__ == '__main__':
    main()
