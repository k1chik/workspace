#!/usr/bin/env python3
"""
Train GNN Model - Week 4
Train GraphSAGE model for drug-disease link prediction.

Usage:
    python scripts/ml/train_gnn.py --epochs 150 --lr 0.01
"""

import torch
import torch.nn.functional as F
from sklearn.metrics import roc_auc_score, average_precision_score
import numpy as np
import json
from pathlib import Path
import argparse
import sys
sys.path.append('.')
from models.gnn_link_predictor import create_model, count_parameters


class GNNTrainer:
    """Train and validate GNN link prediction model."""

    def __init__(self, model, device='cpu'):
        self.model = model.to(device)
        self.device = device
        self.history = {
            'train_loss': [],
            'train_auc': [],
            'val_loss': [],
            'val_auc': [],
            'val_ap': []
        }
        self.best_val_auc = 0
        self.patience_counter = 0

    def train_epoch(self, data, optimizer, full_edge_index):
        """Train for one epoch."""
        self.model.train()
        optimizer.zero_grad()

        # Move data to device
        x = data['x'].to(self.device)
        edge_label_index = data['edge_index'].to(self.device)
        labels = data['labels'].to(self.device)
        full_edge_index = full_edge_index.to(self.device)

        # Forward pass - use full graph structure for message passing
        out = self.model(x, full_edge_index, edge_label_index)

        # Compute loss
        loss = F.binary_cross_entropy_with_logits(out, labels)

        # Backward pass
        loss.backward()
        optimizer.step()

        # Compute metrics
        with torch.no_grad():
            pred_probs = torch.sigmoid(out).cpu().numpy()
            labels_np = labels.cpu().numpy()

            # AUC
            if len(np.unique(labels_np)) > 1:  # Need both classes
                auc = roc_auc_score(labels_np, pred_probs)
            else:
                auc = 0.0

        return loss.item(), auc

    @torch.no_grad()
    def evaluate(self, data, full_edge_index):
        """Evaluate on validation/test set."""
        self.model.eval()

        # Move data to device
        x = data['x'].to(self.device)
        edge_label_index = data['edge_index'].to(self.device)
        labels = data['labels'].to(self.device)
        full_edge_index = full_edge_index.to(self.device)

        # Forward pass
        out = self.model(x, full_edge_index, edge_label_index)

        # Compute loss
        loss = F.binary_cross_entropy_with_logits(out, labels)

        # Compute metrics
        pred_probs = torch.sigmoid(out).cpu().numpy()
        labels_np = labels.cpu().numpy()

        # AUC-ROC
        if len(np.unique(labels_np)) > 1:
            auc = roc_auc_score(labels_np, pred_probs)
            ap = average_precision_score(labels_np, pred_probs)
        else:
            auc = 0.0
            ap = 0.0

        return loss.item(), auc, ap

    def train(self, train_data, val_data, full_edge_index, epochs=100, lr=0.01,
              patience=20, save_path='models/checkpoints/best_model.pt'):
        """
        Full training loop with early stopping.

        Args:
            train_data: Training dataset
            val_data: Validation dataset
            full_edge_index: Full graph structure for message passing
            epochs: Number of training epochs
            lr: Learning rate
            patience: Early stopping patience
            save_path: Path to save best model
        """
        print("\n" + "=" * 70)
        print("🚀 TRAINING GNN LINK PREDICTOR")
        print("=" * 70)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=5e-4)

        print(f"\nModel parameters: {count_parameters(self.model):,}")
        print(f"Device: {self.device}")
        print(f"Learning rate: {lr}")
        print(f"Epochs: {epochs}")
        print(f"Early stopping patience: {patience}")
        print(f"\nTraining samples: {len(train_data['labels']):,}")
        print(f"Validation samples: {len(val_data['labels']):,}")

        print("\n" + "-" * 70)
        print(f"{'Epoch':<8} {'Train Loss':<12} {'Train AUC':<12} {'Val Loss':<12} {'Val AUC':<12} {'Val AP':<12}")
        print("-" * 70)

        for epoch in range(1, epochs + 1):
            # Train
            train_loss, train_auc = self.train_epoch(train_data, optimizer, full_edge_index)

            # Validate
            val_loss, val_auc, val_ap = self.evaluate(val_data, full_edge_index)

            # Record history
            self.history['train_loss'].append(train_loss)
            self.history['train_auc'].append(train_auc)
            self.history['val_loss'].append(val_loss)
            self.history['val_auc'].append(val_auc)
            self.history['val_ap'].append(val_ap)

            # Print progress
            if epoch % 10 == 0 or epoch == 1:
                print(f"{epoch:<8} {train_loss:<12.4f} {train_auc:<12.4f} {val_loss:<12.4f} {val_auc:<12.4f} {val_ap:<12.4f}")

            # Early stopping and checkpointing
            if val_auc > self.best_val_auc:
                self.best_val_auc = val_auc
                self.patience_counter = 0

                # Save best model
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_auc': val_auc,
                    'val_ap': val_ap,
                }, save_path)

                if epoch % 10 == 0:
                    print(f"         ✅ New best model saved (AUC: {val_auc:.4f})")
            else:
                self.patience_counter += 1

            # Early stopping
            if self.patience_counter >= patience:
                print(f"\n⚠️  Early stopping triggered at epoch {epoch}")
                print(f"   Best validation AUC: {self.best_val_auc:.4f}")
                break

        print("-" * 70)
        print(f"\n✅ Training complete!")
        print(f"   Best validation AUC: {self.best_val_auc:.4f}")
        print(f"   Model saved to: {save_path}")

        return self.history


def main():
    parser = argparse.ArgumentParser(description='Train GNN link predictor')
    parser.add_argument('--epochs', type=int, default=150, help='Number of epochs')
    parser.add_argument('--lr', type=float, default=0.01, help='Learning rate')
    parser.add_argument('--hidden', type=int, default=64, help='Hidden dimension')
    parser.add_argument('--embedding', type=int, default=32, help='Embedding dimension')
    parser.add_argument('--dropout', type=float, default=0.5, help='Dropout rate')
    parser.add_argument('--patience', type=int, default=20, help='Early stopping patience')
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

    print(f"\n🔧 Using device: {device}")

    # Load data
    print(f"\n📖 Loading datasets...")
    train_data = torch.load('data/processed/train_data.pt')
    val_data = torch.load('data/processed/val_data.pt')
    graph_data = torch.load('data/processed/graph_data.pt')

    print(f"   ✅ Train: {len(train_data['labels'])} samples")
    print(f"   ✅ Val: {len(val_data['labels'])} samples")

    # For message passing, we need to use training edges only
    # (to avoid data leakage from validation/test edges)
    train_positive_edges = train_data['edge_index'][:, :train_data['num_pos']]

    # Create model
    print(f"\n🏗️  Creating model...")
    model = create_model(
        in_channels=2,
        hidden_channels=args.hidden,
        out_channels=args.embedding,
        dropout=args.dropout
    )
    print(f"   ✅ Model created: {count_parameters(model):,} parameters")

    # Train
    trainer = GNNTrainer(model, device=device)
    history = trainer.train(
        train_data=train_data,
        val_data=val_data,
        full_edge_index=train_positive_edges,
        epochs=args.epochs,
        lr=args.lr,
        patience=args.patience,
        save_path='models/checkpoints/best_model.pt'
    )

    # Save training history
    print(f"\n💾 Saving training history...")
    with open('data/results/training_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    print(f"   ✅ Saved to data/results/training_history.json")

    # Print final summary
    print("\n" + "=" * 70)
    print("📊 TRAINING SUMMARY")
    print("=" * 70)
    print(f"Best Validation AUC:  {trainer.best_val_auc:.4f}")
    print(f"Best Validation AP:   {max(history['val_ap']):.4f}")
    print(f"Final Train AUC:      {history['train_auc'][-1]:.4f}")
    print(f"Final Val AUC:        {history['val_auc'][-1]:.4f}")
    print(f"\n{'✅ TARGET ACHIEVED!' if trainer.best_val_auc >= 0.75 else '⚠️  Target not reached (need AUC ≥ 0.75)'}")
    print("=" * 70)


if __name__ == '__main__':
    main()
