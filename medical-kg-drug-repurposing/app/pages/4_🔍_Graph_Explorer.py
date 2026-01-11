"""
Graph Explorer Page - Browse the Knowledge Graph
Explore entities and relationships in the medical knowledge graph.
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.utils.data_loader import (
    load_entities,
    load_relationships,
    get_graph_stats
)

# Page config
st.set_page_config(page_title="Graph Explorer", page_icon="🔍", layout="wide")

# Header
st.title("🔍 Knowledge Graph Explorer")
st.markdown("Explore the medical knowledge graph built from PubMed literature.")
st.markdown("---")

# Load data
entities = load_entities()
relationships = load_relationships()
graph_stats = get_graph_stats()

# Graph Statistics
st.markdown("## 📊 Graph Statistics")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="Total Nodes", value=f"{graph_stats['total_nodes']:,}")

with col2:
    st.metric(label="Drugs", value=f"{graph_stats['total_drugs']:,}")

with col3:
    st.metric(label="Diseases", value=f"{graph_stats['total_diseases']:,}")

with col4:
    st.metric(label="Relationships", value=f"{graph_stats['total_relationships']:,}")

with col5:
    density = graph_stats['total_relationships'] / (graph_stats['total_drugs'] * graph_stats['total_diseases'])
    st.metric(label="Graph Density", value=f"{density:.4f}")

st.markdown("---")

# Entity Distribution
st.markdown("## 📈 Entity Distribution")

col1, col2 = st.columns(2)

with col1:
    # Frequency distribution for drugs
    drugs = entities[entities['entity_type'] == 'CHEMICAL']
    fig_drug_freq = px.histogram(
        drugs,
        x='frequency',
        nbins=50,
        title='Drug Frequency Distribution',
        labels={'frequency': 'Frequency (mentions in abstracts)', 'count': 'Number of Drugs'},
        color_discrete_sequence=['#1f77b4']
    )
    fig_drug_freq.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_drug_freq, use_container_width=True)

with col2:
    # Frequency distribution for diseases
    diseases = entities[entities['entity_type'] == 'DISEASE']
    fig_disease_freq = px.histogram(
        diseases,
        x='frequency',
        nbins=50,
        title='Disease Frequency Distribution',
        labels={'frequency': 'Frequency (mentions in abstracts)', 'count': 'Number of Diseases'},
        color_discrete_sequence=['#ff7f0e']
    )
    fig_disease_freq.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_disease_freq, use_container_width=True)

st.markdown("---")

# Top Entities
st.markdown("## 🏆 Most Frequent Entities")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Top 15 Drugs")
    top_drugs = entities[entities['entity_type'] == 'CHEMICAL'].nlargest(15, 'frequency')

    fig_top_drugs = px.bar(
        top_drugs,
        x='frequency',
        y='entity_text',
        orientation='h',
        labels={'frequency': 'Frequency', 'entity_text': 'Drug'},
        color='frequency',
        color_continuous_scale='Blues'
    )
    fig_top_drugs.update_layout(showlegend=False, height=500, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_top_drugs, use_container_width=True)

with col2:
    st.markdown("### Top 15 Diseases")
    top_diseases = entities[entities['entity_type'] == 'DISEASE'].nlargest(15, 'frequency')

    fig_top_diseases = px.bar(
        top_diseases,
        x='frequency',
        y='entity_text',
        orientation='h',
        labels={'frequency': 'Frequency', 'entity_text': 'Disease'},
        color='frequency',
        color_continuous_scale='Reds'
    )
    fig_top_diseases.update_layout(showlegend=False, height=500, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_top_diseases, use_container_width=True)

st.markdown("---")

# Relationship Analysis
st.markdown("## 🔗 Relationship Analysis")

# Confidence distribution
fig_conf = px.histogram(
    relationships,
    x='confidence',
    nbins=30,
    title='Relationship Confidence Distribution',
    labels={'confidence': 'Confidence Score', 'count': 'Number of Relationships'},
    color_discrete_sequence=['#2ecc71']
)
fig_conf.update_layout(height=400, showlegend=False)
st.plotly_chart(fig_conf, use_container_width=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Avg Confidence",
        value=f"{relationships['confidence'].mean():.2f}"
    )

with col2:
    high_conf = (relationships['confidence'] >= 2.0).sum()
    st.metric(
        label="High Confidence",
        value=f"{high_conf}",
        delta="≥2.0"
    )

with col3:
    st.metric(
        label="Median Confidence",
        value=f"{relationships['confidence'].median():.2f}"
    )

st.markdown("---")

# Entity Search and Details
st.markdown("## 🔎 Entity Search")

col1, col2 = st.columns(2)

with col1:
    search_type = st.radio("Entity Type", options=['Drug', 'Disease'])

with col2:
    search_query = st.text_input("Search by name", "")

# Filter entities
if search_type == 'Drug':
    filtered_entities = entities[entities['entity_type'] == 'CHEMICAL']
else:
    filtered_entities = entities[entities['entity_type'] == 'DISEASE']

if search_query:
    filtered_entities = filtered_entities[
        filtered_entities['entity_text'].str.contains(search_query, case=False, na=False)
    ]

# Display results
st.markdown(f"### Search Results ({len(filtered_entities)} entities)")

if len(filtered_entities) > 0:
    # Sort by frequency
    filtered_entities_sorted = filtered_entities.sort_values('frequency', ascending=False)

    # Display table
    st.dataframe(
        filtered_entities_sorted[['entity_text', 'entity_type', 'frequency', 'num_papers']].style.format({
            'frequency': '{:,.0f}',
            'num_papers': '{:,.0f}'
        }),
        use_container_width=True,
        height=400
    )

    # Entity details on selection
    if len(filtered_entities_sorted) > 0:
        selected_entity = st.selectbox(
            "Select entity for details",
            options=filtered_entities_sorted['entity_text'].tolist()
        )

        if selected_entity:
            entity_data = filtered_entities_sorted[filtered_entities_sorted['entity_text'] == selected_entity].iloc[0]

            st.markdown("### Entity Details")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(label="Name", value=entity_data['entity_text'])

            with col2:
                st.metric(label="Type", value=entity_data['entity_type'])

            with col3:
                st.metric(label="Frequency", value=f"{entity_data['frequency']:,.0f}")

            with col4:
                st.metric(label="Papers", value=f"{entity_data['num_papers']:,.0f}")

            # Display PubChem chemical information for validated drugs
            if entity_data['entity_type'] == 'CHEMICAL' and 'pubchem_cid' in entity_data and pd.notna(entity_data.get('pubchem_cid')):
                st.markdown("---")
                st.markdown("### 🧪 Chemical Information (PubChem)")

                col1, col2, col3 = st.columns(3)

                with col1:
                    cid = int(entity_data['pubchem_cid'])
                    pubchem_url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
                    st.markdown(f"**PubChem CID:** [{cid}]({pubchem_url})")

                    if pd.notna(entity_data.get('molecular_formula')):
                        st.markdown(f"**Molecular Formula:** {entity_data['molecular_formula']}")

                with col2:
                    if pd.notna(entity_data.get('molecular_weight')):
                        st.markdown(f"**Molecular Weight:** {entity_data['molecular_weight']:.2f} g/mol")

                    if pd.notna(entity_data.get('validated')):
                        validation_status = "✅ Validated" if entity_data['validated'] else "⚠️ Unvalidated"
                        st.markdown(f"**Status:** {validation_status}")

                with col3:
                    if pd.notna(entity_data.get('iupac_name')):
                        st.markdown(f"**IUPAC Name:** {entity_data['iupac_name'][:50]}...")

                if pd.notna(entity_data.get('canonical_smiles')):
                    with st.expander("Chemical Structure (SMILES)"):
                        st.code(entity_data['canonical_smiles'], language=None)

            # Find relationships for this entity
            entity_id = entity_data['entity_id']

            # Get relationships where this entity is involved
            entity_rels = relationships[
                (relationships['drug_id'] == entity_id) | (relationships['disease_id'] == entity_id)
            ]

            if len(entity_rels) > 0:
                st.markdown(f"### Related Entities ({len(entity_rels)} relationships)")

                # For each relationship, get the connected entity
                related_entities = []
                for _, rel in entity_rels.iterrows():
                    if rel['drug_id'] == entity_id:
                        connected_id = rel['disease_id']
                    else:
                        connected_id = rel['drug_id']

                    connected_entity = entities[entities['entity_id'] == connected_id]
                    if len(connected_entity) > 0:
                        connected_data = connected_entity.iloc[0]
                        related_entities.append({
                            'entity': connected_data['entity_text'],
                            'type': connected_data['entity_type'],
                            'confidence': rel['confidence'],
                            'num_papers': rel['num_papers']
                        })

                related_df = pd.DataFrame(related_entities)
                if len(related_df) > 0:
                    st.dataframe(
                        related_df.sort_values('confidence', ascending=False).style.format({
                            'confidence': '{:.2f}',
                            'num_papers': '{:.0f}'
                        }),
                        use_container_width=True
                    )
            else:
                st.info("No relationships found for this entity in the graph.")
else:
    st.info("No entities found matching your search.")

st.markdown("---")

# Degree Distribution
st.markdown("## 📊 Network Topology")

st.markdown("""
### Node Degree Distribution
Node degree represents how many relationships each entity has.
""")

# Calculate degree for each entity
entity_degrees = Counter()

for _, rel in relationships.iterrows():
    entity_degrees[rel['drug_id']] += 1
    entity_degrees[rel['disease_id']] += 1

# Create degree dataframe
degree_data = []
for entity_id, degree in entity_degrees.items():
    entity_info = entities[entities['entity_id'] == entity_id]
    if len(entity_info) > 0:
        degree_data.append({
            'entity_id': entity_id,
            'entity_text': entity_info.iloc[0]['entity_text'],
            'entity_type': entity_info.iloc[0]['entity_type'],
            'degree': degree
        })

degree_df = pd.DataFrame(degree_data)

col1, col2 = st.columns(2)

with col1:
    # Degree distribution
    fig_degree = px.histogram(
        degree_df,
        x='degree',
        nbins=30,
        title='Degree Distribution',
        labels={'degree': 'Node Degree', 'count': 'Number of Nodes'},
        color_discrete_sequence=['#9b59b6']
    )
    fig_degree.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_degree, use_container_width=True)

with col2:
    # Top connected entities
    st.markdown("### Top 10 Most Connected Entities")
    top_connected = degree_df.nlargest(10, 'degree')

    fig_connected = px.bar(
        top_connected,
        x='degree',
        y='entity_text',
        orientation='h',
        labels={'degree': 'Number of Connections', 'entity_text': 'Entity'},
        color='degree',
        color_continuous_scale='Purples'
    )
    fig_connected.update_layout(showlegend=False, height=400, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_connected, use_container_width=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Avg Degree",
        value=f"{degree_df['degree'].mean():.2f}"
    )

with col2:
    st.metric(
        label="Max Degree",
        value=f"{degree_df['degree'].max():.0f}"
    )

with col3:
    st.metric(
        label="Median Degree",
        value=f"{degree_df['degree'].median():.0f}"
    )

st.markdown("---")

# Data export
st.markdown("## 📥 Export Data")

col1, col2, col3 = st.columns(3)

with col1:
    entities_csv = entities.to_csv(index=False)
    st.download_button(
        label="Download Entities CSV",
        data=entities_csv,
        file_name="entities.csv",
        mime="text/csv"
    )

with col2:
    relationships_csv = relationships.to_csv(index=False)
    st.download_button(
        label="Download Relationships CSV",
        data=relationships_csv,
        file_name="relationships.csv",
        mime="text/csv"
    )

with col3:
    if len(degree_df) > 0:
        degree_csv = degree_df.to_csv(index=False)
        st.download_button(
            label="Download Degree Data CSV",
            data=degree_csv,
            file_name="degree_data.csv",
            mime="text/csv"
        )
