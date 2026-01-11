"""
GNN Link Predictor Model - Week 4
GraphSAGE-based model for predicting drug-disease relationships.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv


class GraphSAGEEncoder(nn.Module):
    """
    Graph SAGE encoder for node embeddings.

    Args:
        in_channels: Input feature dimension
        hidden_channels: Hidden layer dimensions
        out_channels: Output embedding dimension
        dropout: Dropout probability
    """

    def __init__(self, in_channels, hidden_channels, out_channels, dropout=0.5):
        super(GraphSAGEEncoder, self).__init__()

        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, out_channels)
        self.dropout = dropout

    def forward(self, x, edge_index):
        """
        Forward pass to compute node embeddings.

        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge connectivity [2, num_edges]

        Returns:
            Node embeddings [num_nodes, out_channels]
        """
        # First GraphSAGE layer
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        # Second GraphSAGE layer
        x = self.conv2(x, edge_index)

        return x


class EdgeDecoder(nn.Module):
    """
    MLP-based edge decoder for link prediction.

    Args:
        in_channels: Input dimension (2 * node_embedding_dim)
        hidden_channels: Hidden layer dimensions
        dropout: Dropout probability
    """

    def __init__(self, in_channels, hidden_channels=32, dropout=0.3):
        super(EdgeDecoder, self).__init__()

        self.mlp = nn.Sequential(
            nn.Linear(in_channels, hidden_channels),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels, 16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, 1)
        )

    def forward(self, z_src, z_dst):
        """
        Predict link probability between source and destination nodes.

        Args:
            z_src: Source node embeddings [num_edges, embedding_dim]
            z_dst: Destination node embeddings [num_edges, embedding_dim]

        Returns:
            Link probabilities [num_edges]
        """
        # Concatenate source and destination embeddings
        edge_features = torch.cat([z_src, z_dst], dim=-1)

        # Pass through MLP
        out = self.mlp(edge_features).squeeze()

        return out


class GNNLinkPredictor(nn.Module):
    """
    Complete GNN model for link prediction.

    Combines GraphSAGE encoder and MLP decoder.
    """

    def __init__(self, in_channels=2, hidden_channels=64, out_channels=32, dropout=0.5):
        super(GNNLinkPredictor, self).__init__()

        # Node encoder (GraphSAGE)
        self.encoder = GraphSAGEEncoder(
            in_channels=in_channels,
            hidden_channels=hidden_channels,
            out_channels=out_channels,
            dropout=dropout
        )

        # Edge decoder (MLP)
        self.decoder = EdgeDecoder(
            in_channels=out_channels * 2,  # Concatenated embeddings
            hidden_channels=32,
            dropout=0.3
        )

    def encode(self, x, edge_index):
        """Compute node embeddings."""
        return self.encoder(x, edge_index)

    def decode(self, z, edge_label_index):
        """
        Predict links for given edge indices.

        Args:
            z: Node embeddings [num_nodes, embedding_dim]
            edge_label_index: Edge indices to predict [2, num_edges]

        Returns:
            Link predictions [num_edges]
        """
        # Get source and destination node embeddings
        z_src = z[edge_label_index[0]]
        z_dst = z[edge_label_index[1]]

        # Decode edges
        return self.decoder(z_src, z_dst)

    def forward(self, x, edge_index, edge_label_index):
        """
        Full forward pass: encode nodes, then decode edges.

        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Graph structure [2, num_edges]
            edge_label_index: Edges to predict [2, num_pred_edges]

        Returns:
            Link predictions [num_pred_edges]
        """
        # Encode nodes
        z = self.encode(x, edge_index)

        # Decode edges
        return self.decode(z, edge_label_index)


def create_model(in_channels=2, hidden_channels=64, out_channels=32, dropout=0.5):
    """
    Factory function to create GNN link predictor.

    Args:
        in_channels: Input feature dimension
        hidden_channels: Hidden layer size
        out_channels: Embedding dimension
        dropout: Dropout rate

    Returns:
        GNNLinkPredictor model
    """
    model = GNNLinkPredictor(
        in_channels=in_channels,
        hidden_channels=hidden_channels,
        out_channels=out_channels,
        dropout=dropout
    )

    return model


def count_parameters(model):
    """Count trainable parameters in model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == '__main__':
    # Test model creation
    print("Testing GNN Link Predictor model...")

    model = create_model(
        in_channels=2,
        hidden_channels=64,
        out_channels=32,
        dropout=0.5
    )

    print(f"\n✅ Model created successfully!")
    print(f"   Total parameters: {count_parameters(model):,}")
    print(f"\n📐 Model architecture:")
    print(model)

    # Test forward pass
    print(f"\n🧪 Testing forward pass...")
    x = torch.randn(1514, 2)  # 1514 nodes, 2 features
    edge_index = torch.randint(0, 1514, (2, 1000))  # Random edges
    edge_label_index = torch.randint(0, 1514, (2, 100))  # Edges to predict

    model.eval()
    with torch.no_grad():
        out = model(x, edge_index, edge_label_index)

    print(f"   Input shape: {x.shape}")
    print(f"   Edge index shape: {edge_index.shape}")
    print(f"   Edge label index shape: {edge_label_index.shape}")
    print(f"   Output shape: {out.shape}")
    print(f"   Output range: [{out.min():.3f}, {out.max():.3f}]")
    print(f"\n✅ Forward pass successful!")
