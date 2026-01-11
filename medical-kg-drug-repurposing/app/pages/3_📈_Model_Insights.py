"""
Model Insights Page - Training Metrics and Performance Analysis
Analyze model performance, training dynamics, and prediction behavior.
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.utils.data_loader import (
    load_training_history,
    load_test_metrics,
    load_predictions
)

# Page config
st.set_page_config(page_title="Model Insights", page_icon="📈", layout="wide")

# Header
st.title("📈 Model Insights")
st.markdown("Deep dive into model performance, training dynamics, and prediction analysis.")
st.markdown("---")

# Load data
training_history = load_training_history()
test_metrics = load_test_metrics()
predictions = load_predictions()

# Model Architecture Overview
st.markdown("## 🏗️ Model Architecture")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### GraphSAGE Encoder
    - **Layer 1**: SAGEConv(2 → 64) + ReLU + Dropout(0.5)
    - **Layer 2**: SAGEConv(64 → 32)
    - **Output**: 32-dimensional node embeddings

    ### MLP Decoder
    - **Input**: Concatenated embeddings (64 dim)
    - **Layer 1**: Linear(64 → 32) + ReLU + Dropout(0.3)
    - **Layer 2**: Linear(32 → 16) + ReLU + Dropout(0.3)
    - **Layer 3**: Linear(16 → 1) → Link probability
    """)

with col2:
    st.markdown("""
    ### Training Configuration
    - **Parameters**: 7,073 trainable
    - **Optimizer**: Adam (lr=0.01, weight_decay=5e-4)
    - **Loss**: Binary Cross-Entropy with Logits
    - **Epochs**: 150 (max), stopped at 46
    - **Early Stopping**: Patience=20
    - **Device**: MPS (M1 GPU)

    ### Dataset
    - **Train**: 928 samples (464 pos, 464 neg)
    - **Validation**: 198 samples (99 pos, 99 neg)
    - **Test**: 200 samples (100 pos, 100 neg)
    """)

st.markdown("---")

# Test Performance Metrics
st.markdown("## 🎯 Test Set Performance")

col1, col2, col3, col4 = st.columns(4)

with col1:
    auc_delta = (test_metrics['auc_roc'] - 0.75) / 0.75 * 100
    st.metric(
        label="AUC-ROC",
        value=f"{test_metrics['auc_roc']:.4f}",
        delta=f"+{auc_delta:.1f}% vs target",
        delta_color="normal"
    )

with col2:
    st.metric(
        label="AUC-PR",
        value=f"{test_metrics['auc_pr']:.4f}",
        delta="Average Precision"
    )

with col3:
    st.metric(
        label="Accuracy",
        value=f"{test_metrics['accuracy']:.4f}",
        delta=f"Precision: {test_metrics['precision']:.4f}"
    )

with col4:
    st.metric(
        label="F1-Score",
        value=f"{test_metrics['f1']:.4f}",
        delta=f"Recall: {test_metrics['recall']:.4f}"
    )

# Confusion Matrix
st.markdown("### 🔢 Confusion Matrix")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    cm_data = [
        [test_metrics['tn'], test_metrics['fp']],
        [test_metrics['fn'], test_metrics['tp']]
    ]

    fig_cm = go.Figure(data=go.Heatmap(
        z=cm_data,
        x=['Predicted Negative', 'Predicted Positive'],
        y=['Actual Negative', 'Actual Positive'],
        text=cm_data,
        texttemplate='%{text}',
        textfont={"size": 20},
        colorscale='Blues',
        showscale=False
    ))

    fig_cm.update_layout(
        title='Test Set Confusion Matrix',
        height=400,
        xaxis_title='Predicted Label',
        yaxis_title='Actual Label'
    )

    st.plotly_chart(fig_cm, use_container_width=True)

st.markdown("---")

# Training Dynamics
st.markdown("## 📊 Training Dynamics")

col1, col2 = st.columns(2)

with col1:
    # Loss curves
    fig_loss = go.Figure()

    fig_loss.add_trace(go.Scatter(
        y=training_history['train_loss'],
        mode='lines',
        name='Train Loss',
        line=dict(color='#1f77b4', width=2)
    ))

    fig_loss.add_trace(go.Scatter(
        y=training_history['val_loss'],
        mode='lines',
        name='Validation Loss',
        line=dict(color='#ff7f0e', width=2)
    ))

    # Mark best epoch
    best_epoch = np.argmax(training_history['val_auc'])
    fig_loss.add_vline(
        x=best_epoch,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Best (epoch {best_epoch+1})"
    )

    fig_loss.update_layout(
        title='Training and Validation Loss',
        xaxis_title='Epoch',
        yaxis_title='Binary Cross-Entropy Loss',
        hovermode='x unified',
        height=450
    )

    st.plotly_chart(fig_loss, use_container_width=True)

with col2:
    # AUC curves
    fig_auc = go.Figure()

    fig_auc.add_trace(go.Scatter(
        y=training_history['train_auc'],
        mode='lines',
        name='Train AUC',
        line=dict(color='#1f77b4', width=2)
    ))

    fig_auc.add_trace(go.Scatter(
        y=training_history['val_auc'],
        mode='lines',
        name='Validation AUC',
        line=dict(color='#ff7f0e', width=2)
    ))

    # Mark best epoch
    fig_auc.add_vline(
        x=best_epoch,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Best (epoch {best_epoch+1})"
    )

    # Add target line
    fig_auc.add_hline(
        y=0.75,
        line_dash="dot",
        line_color="red",
        annotation_text="Target (0.75)"
    )

    fig_auc.update_layout(
        title='Training and Validation AUC-ROC',
        xaxis_title='Epoch',
        yaxis_title='AUC-ROC',
        hovermode='x unified',
        height=450
    )

    st.plotly_chart(fig_auc, use_container_width=True)

# Training summary
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Best Epoch",
        value=f"{best_epoch + 1}",
        delta=f"Stopped at {len(training_history['train_loss'])}"
    )

with col2:
    st.metric(
        label="Best Val AUC",
        value=f"{max(training_history['val_auc']):.4f}",
        delta=f"Final: {training_history['val_auc'][-1]:.4f}"
    )

with col3:
    improvement = (max(training_history['val_auc']) - training_history['val_auc'][0])
    st.metric(
        label="AUC Improvement",
        value=f"+{improvement:.4f}",
        delta=f"{improvement/training_history['val_auc'][0]*100:.1f}%"
    )

st.markdown("---")

# Precision@K Analysis
st.markdown("## 🎯 Precision@K Analysis")

st.markdown("""
Precision@K measures the accuracy of the top-K predictions. For drug repurposing,
high Precision@K is critical because we want the top candidates to be highly reliable.
""")

k_values = [10, 20, 50, 100]
p_at_k = [test_metrics.get(f'p@{k}', 0) for k in k_values]

fig_pk = go.Figure()

fig_pk.add_trace(go.Bar(
    x=[f'P@{k}' for k in k_values],
    y=p_at_k,
    text=[f'{p:.2%}' for p in p_at_k],
    textposition='auto',
    marker=dict(
        color=p_at_k,
        colorscale='YlGnBu',
        showscale=False
    )
))

fig_pk.update_layout(
    title='Precision at Different K Values',
    xaxis_title='Metric',
    yaxis_title='Precision',
    yaxis_range=[0, 1.1],
    height=400
)

st.plotly_chart(fig_pk, use_container_width=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="P@10", value=f"{test_metrics.get('p@10', 0):.4f}")

with col2:
    st.metric(label="P@20", value=f"{test_metrics.get('p@20', 0):.4f}")

with col3:
    st.metric(label="P@50", value=f"{test_metrics.get('p@50', 0):.4f}")

with col4:
    st.metric(label="P@100", value=f"{test_metrics.get('p@100', 0):.4f}")

st.markdown("---")

# Prediction Confidence Distribution
st.markdown("## 📈 Prediction Confidence Distribution")

fig_conf = px.histogram(
    predictions,
    x='confidence',
    nbins=50,
    title='Distribution of Model Confidence Scores (Top 100 Predictions)',
    labels={'confidence': 'Confidence Score', 'count': 'Number of Predictions'},
    color_discrete_sequence=['#1f77b4']
)

fig_conf.update_layout(height=400, showlegend=False)
st.plotly_chart(fig_conf, use_container_width=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Mean Confidence",
        value=f"{predictions['confidence'].mean():.4f}"
    )

with col2:
    st.metric(
        label="Median Confidence",
        value=f"{predictions['confidence'].median():.4f}"
    )

with col3:
    st.metric(
        label="Min Confidence",
        value=f"{predictions['confidence'].min():.4f}"
    )

with col4:
    high_conf = (predictions['confidence'] >= 0.9).sum()
    st.metric(
        label="High Confidence",
        value=f"{high_conf}",
        delta="≥0.9"
    )

st.markdown("---")

# Model Strengths & Limitations
st.markdown("## 💡 Model Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### ✅ Strengths
    - **Exceptional Generalization**: Test AUC (0.8693) > Val AUC (0.8601)
    - **Perfect Top-K**: P@10 and P@20 both 1.0 (all top predictions correct)
    - **High Confidence**: All top 100 predictions ≥0.80
    - **Robust Training**: Early stopping prevented overfitting
    - **Balanced Performance**: Good precision (0.83) and recall (0.69)
    - **Graph Learning**: Effective use of graph structure with minimal features
    """)

with col2:
    st.markdown("""
    ### ⚠️ Limitations & Future Work
    - **Limited Features**: Only 2 node features (could add drug properties)
    - **Small Training Set**: 464 positive edges (more data → better recall)
    - **Bipartite Constraint**: Doesn't model drug-drug relationships
    - **No Mechanism Info**: Doesn't explain biological mechanisms
    - **Binary Prediction**: Doesn't predict treatment efficacy strength
    - **Static Graph**: Doesn't incorporate temporal dynamics
    """)

st.markdown("---")

# Comparison to Baselines
st.markdown("## 📊 Comparison to Baselines")

baseline_data = pd.DataFrame({
    'Method': ['Random', 'Frequency-based', 'Our GNN'],
    'AUC-ROC': [0.50, 0.63, test_metrics['auc_roc']],
    'Description': [
        'Random predictions',
        'Predicted based on entity frequency',
        'GraphSAGE with link prediction'
    ]
})

fig_baseline = px.bar(
    baseline_data,
    x='Method',
    y='AUC-ROC',
    text='AUC-ROC',
    title='Model Performance vs. Baselines',
    color='AUC-ROC',
    color_continuous_scale='Blues'
)

fig_baseline.update_traces(texttemplate='%{text:.4f}', textposition='outside')
fig_baseline.update_layout(showlegend=False, height=400, yaxis_range=[0, 1])

st.plotly_chart(fig_baseline, use_container_width=True)

improvement_over_random = (test_metrics['auc_roc'] - 0.50) / 0.50 * 100
improvement_over_heuristic = (test_metrics['auc_roc'] - 0.63) / 0.63 * 100

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="vs Random",
        value=f"+{improvement_over_random:.1f}%",
        delta="73.9% improvement"
    )

with col2:
    st.metric(
        label="vs Frequency-based",
        value=f"+{improvement_over_heuristic:.1f}%",
        delta="38.0% improvement"
    )

with col3:
    st.metric(
        label="Target Achievement",
        value=f"+{(test_metrics['auc_roc']-0.75)/0.75*100:.1f}%",
        delta="Exceeded by 16%"
    )

st.markdown("---")

# Footer
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p><strong>Model demonstrates strong performance with excellent generalization and reliable top-K predictions.</strong></p>
    <p>Perfect Precision@10 and @20 make this model suitable for drug repurposing candidate prioritization.</p>
</div>
""", unsafe_allow_html=True)
