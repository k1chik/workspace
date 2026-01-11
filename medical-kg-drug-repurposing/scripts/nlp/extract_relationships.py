#!/usr/bin/env python3
"""
Relationship Extraction Script - Week 2
Extract drug-disease relationships from PubMed abstracts using pattern matching and co-occurrence.

Usage:
    python scripts/nlp/extract_relationships.py

Input:
    - data/raw/pubmed_abstracts.json (924 abstracts)
    - data/processed/entities.csv (1,514 entities)

Output:
    - data/processed/relationships.csv
    - data/processed/relationship_extraction_stats.json
"""

import json
import pandas as pd
import spacy
from spacy.matcher import Matcher
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm
import argparse
from datetime import datetime


class RelationshipExtractor:
    """Extract drug-disease relationships from PubMed abstracts."""

    def __init__(self):
        """Initialize the BC5CDR NER model and spaCy Matcher for pattern matching."""
        print("Loading BC5CDR model...")
        self.nlp = spacy.load('en_ner_bc5cdr_md')
        print("✅ Model loaded")

        # Initialize spaCy Matcher for pattern-based extraction
        self.matcher = Matcher(self.nlp.vocab)

        # Define treatment patterns (much more readable than regex!)
        # Each pattern is a list of token specifications
        treatment_patterns = [
            # Pattern 1: "Drug treats disease"
            # Example: "Metformin treats diabetes"
            [
                {"ENT_TYPE": "CHEMICAL"},
                {"LEMMA": {"IN": ["treat", "cure", "prevent", "help"]}},
                {"ENT_TYPE": "DISEASE"}
            ],

            # Pattern 2: "Drug for treatment of disease"
            # Example: "Aspirin for treatment of headache"
            [
                {"ENT_TYPE": "CHEMICAL"},
                {"LOWER": {"IN": ["for", "against"]}},
                {"IS_ALPHA": True, "OP": "?"},  # Optional "the"
                {"LOWER": {"IN": ["treatment", "therapy"]}},
                {"LOWER": "of"},
                {"ENT_TYPE": "DISEASE"}
            ],

            # Pattern 3: "Treatment of disease with drug"
            # Example: "Treatment of cancer with cisplatin"
            [
                {"LOWER": {"IN": ["treatment", "therapy"]}},
                {"LOWER": {"IN": ["of", "for"]}},
                {"ENT_TYPE": "DISEASE"},
                {"LOWER": {"IN": ["with", "using"]}},
                {"ENT_TYPE": "CHEMICAL"}
            ],

            # Pattern 4: "Drug is effective for disease"
            # Example: "Metformin is effective for diabetes"
            [
                {"ENT_TYPE": "CHEMICAL"},
                {"LEMMA": {"IN": ["be"]}},  # is/are/was/were
                {"LOWER": {"IN": ["used", "effective", "beneficial"]}},
                {"LOWER": {"IN": ["for", "in", "against"]}},
                {"ENT_TYPE": "DISEASE"}
            ],

            # Pattern 5: "Drug can treat disease"
            # Example: "Aspirin can prevent heart attack"
            [
                {"ENT_TYPE": "CHEMICAL"},
                {"LOWER": {"IN": ["can", "may", "could", "might"]}},
                {"LEMMA": {"IN": ["treat", "help", "cure", "prevent"]}},
                {"ENT_TYPE": "DISEASE"}
            ],

            # Pattern 6: "Drug therapy for disease"
            # Example: "Metformin therapy for diabetes"
            [
                {"ENT_TYPE": "CHEMICAL"},
                {"LOWER": {"IN": ["therapy", "treatment"]}},
                {"LOWER": {"IN": ["for", "in", "of"]}},
                {"ENT_TYPE": "DISEASE"}
            ],

            # Pattern 7: "Repurposing drug for disease"
            # Example: "Repurposing ivermectin for COVID-19"
            [
                {"LEMMA": "repurpose"},
                {"ENT_TYPE": "CHEMICAL"},
                {"LOWER": {"IN": ["for", "against"]}},
                {"ENT_TYPE": "DISEASE"}
            ],

            # Pattern 8: "Drug repurposed for disease"
            # Example: "Ivermectin repurposed for COVID-19"
            [
                {"ENT_TYPE": "CHEMICAL"},
                {"LEMMA": "repurpose"},
                {"LOWER": {"IN": ["for", "against"]}},
                {"ENT_TYPE": "DISEASE"}
            ],

            # Pattern 9: "Drug for disease" (simple)
            # Example: "Aspirin for headache"
            [
                {"ENT_TYPE": "CHEMICAL"},
                {"LOWER": "for"},
                {"ENT_TYPE": "DISEASE"}
            ],

            # Pattern 10: "Disease treated with drug"
            # Example: "Diabetes treated with metformin"
            [
                {"ENT_TYPE": "DISEASE"},
                {"LEMMA": "treat"},
                {"LOWER": {"IN": ["with", "using"]}},
                {"ENT_TYPE": "CHEMICAL"}
            ],
        ]

        # Add all patterns to matcher
        self.matcher.add("TREATMENT", treatment_patterns)
        print(f"✅ Loaded {len(treatment_patterns)} treatment patterns")

    def load_entities(self, entities_path):
        """Load extracted entities and create lookup dictionaries."""
        print(f"\n📖 Loading entities from {entities_path}...")
        df = pd.read_csv(entities_path)

        # Create sets for fast lookup (lowercase for matching)
        self.drugs = set(df[df['entity_type'] == 'CHEMICAL']['entity_text'].str.lower())
        self.diseases = set(df[df['entity_type'] == 'DISEASE']['entity_text'].str.lower())

        # Create mapping from normalized text to entity_id
        self.entity_to_id = {}
        for _, row in df.iterrows():
            normalized = row['entity_text'].lower()
            self.entity_to_id[normalized] = {
                'id': row['entity_id'],
                'text': row['entity_text'],
                'type': row['entity_type']
            }

        print(f"✅ Loaded {len(self.drugs)} drugs and {len(self.diseases)} diseases")

    def extract_entities_from_sentence(self, sentence):
        """Extract drug and disease entities from a sentence using NER."""
        doc = self.nlp(sentence)

        drugs = []
        diseases = []

        for ent in doc.ents:
            entity_text = ent.text.strip().lower()

            # Only keep if it's in our extracted entities
            if ent.label_ == 'CHEMICAL' and entity_text in self.drugs:
                drugs.append(entity_text)
            elif ent.label_ == 'DISEASE' and entity_text in self.diseases:
                diseases.append(entity_text)

        return list(set(drugs)), list(set(diseases))

    def pattern_based_extraction(self, text, pmid):
        """
        Extract relationships using spaCy Matcher pattern matching.

        Returns:
            List of (drug, disease, evidence, confidence) tuples
        """
        relationships = []

        # Process text with NER
        doc = self.nlp(text)

        # Process each sentence separately for cleaner evidence extraction
        for sent in doc.sents:
            # Run matcher on sentence
            sent_doc = self.nlp(sent.text)
            matches = self.matcher(sent_doc)

            # Extract relationships from matches
            for match_id, start, end in matches:
                matched_span = sent_doc[start:end]

                # Extract drug and disease entities from the matched span
                drug = None
                disease = None

                for token in matched_span:
                    if token.ent_type_ == "CHEMICAL":
                        drug_candidate = token.text.strip().lower()
                        # Verify it's in our entity list
                        if drug_candidate in self.drugs:
                            drug = drug_candidate
                    elif token.ent_type_ == "DISEASE":
                        disease_candidate = token.text.strip().lower()
                        # Verify it's in our entity list
                        if disease_candidate in self.diseases:
                            disease = disease_candidate

                # Only add if both drug and disease found
                if drug and disease:
                    relationships.append({
                        'drug': drug,
                        'disease': disease,
                        'evidence': sent.text.strip(),
                        'pmid': pmid,
                        'method': 'pattern',
                        'confidence': 0.9  # High confidence for pattern matches
                    })

        return relationships

    def cooccurrence_extraction(self, text, pmid):
        """
        Extract relationships using co-occurrence in same sentence.

        Returns:
            List of (drug, disease, evidence, confidence) tuples
        """
        relationships = []

        # Process text in sentences
        doc = self.nlp(text)

        for sent in doc.sents:
            sent_text = sent.text

            # Extract entities from sentence
            drugs, diseases = self.extract_entities_from_sentence(sent_text)

            # Create relationships for all drug-disease pairs in sentence
            for drug in drugs:
                for disease in diseases:
                    relationships.append({
                        'drug': drug,
                        'disease': disease,
                        'evidence': sent_text.strip(),
                        'pmid': pmid,
                        'method': 'cooccurrence',
                        'confidence': 0.5  # Lower confidence for co-occurrence
                    })

        return relationships

    def extract_from_abstracts(self, abstracts):
        """
        Extract all relationships from abstracts.

        Args:
            abstracts: List of abstract dictionaries

        Returns:
            List of relationship dictionaries
        """
        print(f"\n🔬 Extracting relationships from {len(abstracts)} abstracts...")

        all_relationships = []

        for abstract in tqdm(abstracts, desc="Processing abstracts"):
            pmid = abstract.get('pmid', 'unknown')
            title = abstract.get('title', '')
            abstract_text = abstract.get('abstract', '')

            # Combine title and abstract
            full_text = f"{title}. {abstract_text}"

            # Extract using both methods
            pattern_rels = self.pattern_based_extraction(full_text, pmid)
            cooccur_rels = self.cooccurrence_extraction(full_text, pmid)

            all_relationships.extend(pattern_rels)
            all_relationships.extend(cooccur_rels)

        return all_relationships

    def deduplicate_and_aggregate(self, relationships):
        """
        Deduplicate relationships and aggregate evidence.

        Args:
            relationships: List of relationship dictionaries

        Returns:
            DataFrame with deduplicated relationships
        """
        print("\n🔄 Deduplicating and aggregating relationships...")

        # Group by (drug, disease)
        grouped = defaultdict(lambda: {
            'pmids': set(),
            'evidences': [],
            'methods': set(),
            'max_confidence': 0.0
        })

        for rel in relationships:
            key = (rel['drug'], rel['disease'])
            grouped[key]['pmids'].add(rel['pmid'])
            grouped[key]['evidences'].append(rel['evidence'])
            grouped[key]['methods'].add(rel['method'])
            grouped[key]['max_confidence'] = max(
                grouped[key]['max_confidence'],
                rel['confidence']
            )

        # Create DataFrame
        rows = []
        for idx, ((drug, disease), data) in enumerate(sorted(grouped.items()), 1):
            # Get entity IDs
            drug_id = self.entity_to_id.get(drug, {}).get('id', 'UNKNOWN')
            disease_id = self.entity_to_id.get(disease, {}).get('id', 'UNKNOWN')

            # Select best evidence (shortest, most informative)
            evidences = sorted(data['evidences'], key=len)
            best_evidence = evidences[0] if evidences else ""

            # Boost confidence if multiple papers mention the relationship
            num_papers = len(data['pmids'])
            confidence = data['max_confidence']
            if num_papers >= 3:
                confidence = min(1.0, confidence + 0.1)
            elif num_papers >= 2:
                confidence = min(1.0, confidence + 0.05)

            rows.append({
                'relationship_id': f'REL_{idx:05d}',
                'drug_id': drug_id,
                'drug_text': drug,
                'disease_id': disease_id,
                'disease_text': disease,
                'relationship_type': 'TREATS',
                'confidence': round(confidence, 2),
                'evidence_text': best_evidence[:500],  # Limit length
                'evidence_pmids': ','.join(sorted(data['pmids'])[:10]),  # Limit to 10 PMIDs
                'num_papers': num_papers,
                'extraction_methods': ','.join(sorted(data['methods']))
            })

        df = pd.DataFrame(rows)

        # Sort by confidence and num_papers
        df = df.sort_values(['confidence', 'num_papers'],
                           ascending=[False, False])
        df = df.reset_index(drop=True)

        return df

    def generate_statistics(self, df, raw_relationships):
        """Generate extraction statistics."""
        stats = {
            'extraction_date': datetime.now().isoformat(),
            'raw_extractions': len(raw_relationships),
            'output': {
                'total_relationships': len(df),
                'pattern_based': len([r for r in raw_relationships if r['method'] == 'pattern']),
                'cooccurrence': len([r for r in raw_relationships if r['method'] == 'cooccurrence']),
                'high_confidence': len(df[df['confidence'] >= 0.8]),
                'medium_confidence': len(df[(df['confidence'] >= 0.5) & (df['confidence'] < 0.8)]),
                'low_confidence': len(df[df['confidence'] < 0.5])
            },
            'statistics': {
                'avg_confidence': float(df['confidence'].mean()),
                'median_confidence': float(df['confidence'].median()),
                'avg_papers_per_relationship': float(df['num_papers'].mean()),
                'max_papers_per_relationship': int(df['num_papers'].max())
            },
            'top_relationships': df.head(10)[['drug_text', 'disease_text', 'confidence', 'num_papers']]
                                  .to_dict('records')
        }

        return stats


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Extract relationships from PubMed abstracts')
    parser.add_argument('--abstracts', type=str,
                       default='data/raw/pubmed_abstracts.json',
                       help='Input JSON file with abstracts')
    parser.add_argument('--entities', type=str,
                       default='data/processed/entities.csv',
                       help='Input CSV file with entities')
    parser.add_argument('--output', type=str,
                       default='data/processed/relationships.csv',
                       help='Output CSV file for relationships')
    parser.add_argument('--stats', type=str,
                       default='data/processed/relationship_extraction_stats.json',
                       help='Output JSON file for statistics')

    args = parser.parse_args()

    print("=" * 70)
    print("🔗 RELATIONSHIP EXTRACTION - Week 2")
    print("=" * 70)

    # Load abstracts
    print(f"\n📖 Loading abstracts from {args.abstracts}...")
    with open(args.abstracts, 'r') as f:
        abstracts = json.load(f)
    print(f"✅ Loaded {len(abstracts)} abstracts")

    # Initialize extractor
    extractor = RelationshipExtractor()

    # Load entities
    extractor.load_entities(args.entities)

    # Extract relationships
    raw_relationships = extractor.extract_from_abstracts(abstracts)
    print(f"\n✅ Extracted {len(raw_relationships)} raw relationship mentions")

    # Deduplicate and aggregate
    df = extractor.deduplicate_and_aggregate(raw_relationships)

    # Generate statistics
    print(f"\n📈 Generating statistics...")
    stats = extractor.generate_statistics(df, raw_relationships)

    # Save outputs
    print(f"\n💾 Saving outputs...")

    # Create output directory if needed
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    # Save relationships CSV
    df.to_csv(args.output, index=False)
    print(f"✅ Relationships saved to {args.output}")

    # Save statistics JSON
    with open(args.stats, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Statistics saved to {args.stats}")

    # Print summary
    print("\n" + "=" * 70)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 70)
    print(f"Raw Mentions:              {stats['raw_extractions']:,}")
    print(f"Unique Relationships:      {stats['output']['total_relationships']:,}")
    print(f"  - Pattern-based:         {stats['output']['pattern_based']:,}")
    print(f"  - Co-occurrence:         {stats['output']['cooccurrence']:,}")
    print(f"\nConfidence Distribution:")
    print(f"  - High (≥0.8):           {stats['output']['high_confidence']:,}")
    print(f"  - Medium (0.5-0.8):      {stats['output']['medium_confidence']:,}")
    print(f"  - Low (<0.5):            {stats['output']['low_confidence']:,}")
    print(f"\nAvg Confidence:            {stats['statistics']['avg_confidence']:.2f}")
    print(f"Avg Papers/Relationship:   {stats['statistics']['avg_papers_per_relationship']:.2f}")

    print(f"\n🔝 Top 5 Relationships:")
    for rel in stats['top_relationships'][:5]:
        print(f"   - {rel['drug_text']} → {rel['disease_text']}")
        print(f"     (confidence: {rel['confidence']}, papers: {rel['num_papers']})")

    print("\n" + "=" * 70)
    print("✅ Relationship extraction complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
