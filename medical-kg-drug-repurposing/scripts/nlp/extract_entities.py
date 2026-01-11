#!/usr/bin/env python3
"""
Entity Extraction Script - Week 2
Extract drugs (CHEMICAL) and diseases (DISEASE) from PubMed abstracts using BC5CDR model.

Usage:
    python scripts/nlp/extract_entities.py

Input:
    - data/raw/pubmed_abstracts.json (924 abstracts)

Output:
    - data/processed/entities.csv
    - data/processed/entity_extraction_stats.json
"""

import json
import pandas as pd
import spacy
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm
import argparse
from datetime import datetime


class EntityExtractor:
    """Extract biomedical entities from PubMed abstracts using BC5CDR model."""

    def __init__(self, model_name='en_ner_bc5cdr_md'):
        """Initialize the BC5CDR NER model."""
        print(f"Loading {model_name} model...")
        try:
            self.nlp = spacy.load(model_name)
            print(f"✅ Model loaded successfully")
        except OSError:
            print(f"❌ Model {model_name} not found. Installing...")
            import subprocess
            subprocess.run(['pip', 'install',
                          'https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.1/en_ner_bc5cdr_md-0.5.1.tar.gz'])
            self.nlp = spacy.load(model_name)
            print(f"✅ Model installed and loaded")

    def extract_from_text(self, text, pmid):
        """
        Extract entities from a single text.

        Args:
            text: Abstract text
            pmid: PubMed ID

        Returns:
            List of (entity_text, entity_type, pmid) tuples
        """
        if not text or not isinstance(text, str):
            return []

        # Process text with NER model
        doc = self.nlp(text)

        entities = []
        for ent in doc.ents:
            # Normalize entity text (lowercase, strip whitespace)
            entity_text = ent.text.strip().lower()
            entity_type = ent.label_

            # Only keep CHEMICAL and DISEASE entities
            if entity_type in ['CHEMICAL', 'DISEASE'] and len(entity_text) > 2:
                entities.append((entity_text, entity_type, pmid))

        return entities

    def extract_from_abstracts(self, abstracts):
        """
        Extract entities from all abstracts.

        Args:
            abstracts: List of abstract dictionaries

        Returns:
            Dictionary mapping (entity_text, entity_type) -> {pmids: set, frequency: int}
        """
        print(f"\n🔬 Processing {len(abstracts)} abstracts...")

        # Dictionary to store entity information
        # Key: (entity_text, entity_type)
        # Value: {'pmids': set(), 'frequency': int}
        entity_data = defaultdict(lambda: {'pmids': set(), 'frequency': 0})

        # Process each abstract
        for abstract in tqdm(abstracts, desc="Extracting entities"):
            pmid = abstract.get('pmid', 'unknown')
            title = abstract.get('title', '')
            abstract_text = abstract.get('abstract', '')

            # Combine title and abstract for better coverage
            full_text = f"{title}. {abstract_text}"

            # Extract entities
            entities = self.extract_from_text(full_text, pmid)

            # Update entity dictionary
            for entity_text, entity_type, entity_pmid in entities:
                key = (entity_text, entity_type)
                entity_data[key]['pmids'].add(entity_pmid)
                entity_data[key]['frequency'] += 1

        return entity_data

    def create_entity_dataframe(self, entity_data):
        """
        Convert entity dictionary to pandas DataFrame.

        Args:
            entity_data: Dictionary from extract_from_abstracts()

        Returns:
            DataFrame with columns: entity_id, entity_text, entity_type, frequency, source_pmids
        """
        rows = []

        # Sort by frequency (descending) for consistent ordering
        sorted_entities = sorted(entity_data.items(),
                                key=lambda x: x[1]['frequency'],
                                reverse=True)

        for idx, ((entity_text, entity_type), data) in enumerate(sorted_entities, 1):
            # Create entity ID with type prefix
            prefix = 'DRUG' if entity_type == 'CHEMICAL' else 'DISEASE'
            entity_id = f"{prefix}_{idx:04d}"

            # Convert pmid set to comma-separated string
            source_pmids = ','.join(sorted(data['pmids']))

            rows.append({
                'entity_id': entity_id,
                'entity_text': entity_text,
                'entity_type': entity_type,
                'frequency': data['frequency'],
                'source_pmids': source_pmids,
                'num_papers': len(data['pmids'])
            })

        return pd.DataFrame(rows)

    def generate_statistics(self, df, abstracts):
        """Generate extraction statistics."""
        stats = {
            'extraction_date': datetime.now().isoformat(),
            'input': {
                'total_abstracts': len(abstracts),
                'source': 'PubMed abstracts (2020-2024)'
            },
            'output': {
                'total_entities': len(df),
                'unique_drugs': len(df[df['entity_type'] == 'CHEMICAL']),
                'unique_diseases': len(df[df['entity_type'] == 'DISEASE']),
                'total_mentions': int(df['frequency'].sum())
            },
            'statistics': {
                'avg_frequency': float(df['frequency'].mean()),
                'median_frequency': float(df['frequency'].median()),
                'max_frequency': int(df['frequency'].max()),
                'avg_papers_per_entity': float(df['num_papers'].mean())
            },
            'top_drugs': df[df['entity_type'] == 'CHEMICAL']
                          .head(10)[['entity_text', 'frequency']]
                          .to_dict('records'),
            'top_diseases': df[df['entity_type'] == 'DISEASE']
                             .head(10)[['entity_text', 'frequency']]
                             .to_dict('records')
        }

        return stats


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Extract entities from PubMed abstracts')
    parser.add_argument('--input', type=str,
                       default='data/raw/pubmed_abstracts.json',
                       help='Input JSON file with abstracts')
    parser.add_argument('--output', type=str,
                       default='data/processed/entities.csv',
                       help='Output CSV file for entities')
    parser.add_argument('--stats', type=str,
                       default='data/processed/entity_extraction_stats.json',
                       help='Output JSON file for statistics')

    args = parser.parse_args()

    print("=" * 70)
    print("🧬 ENTITY EXTRACTION - Week 2")
    print("=" * 70)

    # Load abstracts
    print(f"\n📖 Loading abstracts from {args.input}...")
    with open(args.input, 'r') as f:
        abstracts = json.load(f)
    print(f"✅ Loaded {len(abstracts)} abstracts")

    # Initialize extractor
    extractor = EntityExtractor()

    # Extract entities
    entity_data = extractor.extract_from_abstracts(abstracts)

    # Create DataFrame
    print(f"\n📊 Creating entity DataFrame...")
    df = extractor.create_entity_dataframe(entity_data)

    # Generate statistics
    print(f"\n📈 Generating statistics...")
    stats = extractor.generate_statistics(df, abstracts)

    # Save outputs
    print(f"\n💾 Saving outputs...")

    # Create output directory if it doesn't exist
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    # Save entities CSV
    df.to_csv(args.output, index=False)
    print(f"✅ Entities saved to {args.output}")

    # Save statistics JSON
    with open(args.stats, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Statistics saved to {args.stats}")

    # Print summary
    print("\n" + "=" * 70)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 70)
    print(f"Total Entities:        {stats['output']['total_entities']:,}")
    print(f"  - Drugs (CHEMICAL):  {stats['output']['unique_drugs']:,}")
    print(f"  - Diseases:          {stats['output']['unique_diseases']:,}")
    print(f"Total Mentions:        {stats['output']['total_mentions']:,}")
    print(f"Avg Frequency:         {stats['statistics']['avg_frequency']:.2f}")
    print(f"Avg Papers/Entity:     {stats['statistics']['avg_papers_per_entity']:.2f}")

    print(f"\n🔝 Top 5 Drugs:")
    for drug in stats['top_drugs'][:5]:
        print(f"   - {drug['entity_text']}: {drug['frequency']} mentions")

    print(f"\n🔝 Top 5 Diseases:")
    for disease in stats['top_diseases'][:5]:
        print(f"   - {disease['entity_text']}: {disease['frequency']} mentions")

    print("\n" + "=" * 70)
    print("✅ Entity extraction complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
