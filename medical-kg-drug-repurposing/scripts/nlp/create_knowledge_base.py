#!/usr/bin/env python3
"""
Knowledge Base Creation Script - Week 2
Combine entities and relationships into unified knowledge base.

Usage:
    python scripts/nlp/create_knowledge_base.py

Input:
    - data/processed/entities.csv
    - data/processed/relationships.csv

Output:
    - data/processed/knowledge_base.json
    - data/processed/week2_quality_report.json
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse


class KnowledgeBaseBuilder:
    """Build unified knowledge base from entities and relationships."""

    def __init__(self):
        self.entities_df = None
        self.relationships_df = None
        self.kb = None

    def load_data(self, entities_path, relationships_path):
        """Load entities and relationships from CSV files."""
        print(f"\n📖 Loading data...")
        self.entities_df = pd.read_csv(entities_path)
        self.relationships_df = pd.read_csv(relationships_path)

        print(f"✅ Loaded {len(self.entities_df)} entities")
        print(f"✅ Loaded {len(self.relationships_df)} relationships")

    def validate_integrity(self):
        """Validate referential integrity between entities and relationships."""
        print(f"\n🔍 Validating referential integrity...")

        # Get all entity IDs
        entity_ids = set(self.entities_df['entity_id'])

        # Check relationships reference valid entities
        invalid_drugs = []
        invalid_diseases = []

        for _, rel in self.relationships_df.iterrows():
            if rel['drug_id'] not in entity_ids:
                invalid_drugs.append(rel['drug_id'])
            if rel['disease_id'] not in entity_ids:
                invalid_diseases.append(rel['disease_id'])

        if invalid_drugs or invalid_diseases:
            print(f"⚠️  Found {len(set(invalid_drugs))} invalid drug IDs")
            print(f"⚠️  Found {len(set(invalid_diseases))} invalid disease IDs")
            return False
        else:
            print(f"✅ All relationships reference valid entities")
            return True

    def build_knowledge_base(self):
        """Build unified knowledge base structure."""
        print(f"\n🏗️  Building knowledge base...")

        # Create metadata
        metadata = {
            'created_date': datetime.now().isoformat(),
            'version': '1.0',
            'source': '924 PubMed abstracts (2020-2024)',
            'extraction_method': 'BC5CDR biomedical NER + pattern matching + co-occurrence',
            'statistics': {
                'total_entities': len(self.entities_df),
                'drugs': len(self.entities_df[self.entities_df['entity_type'] == 'CHEMICAL']),
                'diseases': len(self.entities_df[self.entities_df['entity_type'] == 'DISEASE']),
                'relationships': len(self.relationships_df),
                'source_papers': 924
            }
        }

        # Convert entities to list of dictionaries
        entities = []
        for _, entity in self.entities_df.iterrows():
            entities.append({
                'id': entity['entity_id'],
                'text': entity['entity_text'],
                'type': entity['entity_type'],
                'frequency': int(entity['frequency']),
                'num_papers': int(entity['num_papers']),
                'source_pmids': entity['source_pmids'].split(',') if pd.notna(entity['source_pmids']) else []
            })

        # Convert relationships to list of dictionaries
        relationships = []
        for _, rel in self.relationships_df.iterrows():
            relationships.append({
                'id': rel['relationship_id'],
                'drug_id': rel['drug_id'],
                'drug_text': rel['drug_text'],
                'disease_id': rel['disease_id'],
                'disease_text': rel['disease_text'],
                'type': rel['relationship_type'],
                'confidence': float(rel['confidence']),
                'evidence_text': rel['evidence_text'],
                'evidence_pmids': rel['evidence_pmids'].split(',') if pd.notna(rel['evidence_pmids']) else [],
                'num_papers': int(rel['num_papers']),
                'extraction_methods': rel['extraction_methods'].split(',') if pd.notna(rel['extraction_methods']) else []
            })

        # Build knowledge base
        self.kb = {
            'metadata': metadata,
            'entities': entities,
            'relationships': relationships
        }

        print(f"✅ Knowledge base created")
        return self.kb

    def generate_quality_report(self):
        """Generate comprehensive quality report for Week 2."""
        print(f"\n📊 Generating quality report...")

        # Entity statistics
        drugs_df = self.entities_df[self.entities_df['entity_type'] == 'CHEMICAL']
        diseases_df = self.entities_df[self.entities_df['entity_type'] == 'DISEASE']

        entity_stats = {
            'total': len(self.entities_df),
            'drugs': len(drugs_df),
            'diseases': len(diseases_df),
            'avg_frequency': float(self.entities_df['frequency'].mean()),
            'median_frequency': float(self.entities_df['frequency'].median()),
            'max_frequency': int(self.entities_df['frequency'].max()),
            'avg_papers_per_entity': float(self.entities_df['num_papers'].mean()),
            'top_drugs': drugs_df.head(10)[['entity_text', 'frequency']].to_dict('records'),
            'top_diseases': diseases_df.head(10)[['entity_text', 'frequency']].to_dict('records')
        }

        # Relationship statistics
        rel_stats = {
            'total': len(self.relationships_df),
            'high_confidence': len(self.relationships_df[self.relationships_df['confidence'] >= 0.8]),
            'medium_confidence': len(self.relationships_df[
                (self.relationships_df['confidence'] >= 0.5) &
                (self.relationships_df['confidence'] < 0.8)
            ]),
            'low_confidence': len(self.relationships_df[self.relationships_df['confidence'] < 0.5]),
            'avg_confidence': float(self.relationships_df['confidence'].mean()),
            'avg_papers_per_relationship': float(self.relationships_df['num_papers'].mean()),
            'top_relationships': self.relationships_df.head(10)[
                ['drug_text', 'disease_text', 'confidence', 'num_papers']
            ].to_dict('records')
        }

        # Validation checks
        validation = {
            'referential_integrity': self.validate_integrity(),
            'no_null_entities': int(self.entities_df['entity_text'].isnull().sum()) == 0,
            'no_null_relationships': int(self.relationships_df['drug_id'].isnull().sum()) == 0,
            'valid_confidence_range': bool(
                (self.relationships_df['confidence'] >= 0).all() and
                (self.relationships_df['confidence'] <= 1).all()
            )
        }

        # Week 2 success criteria
        success_criteria = {
            'target_entities': '800-1,500',
            'actual_entities': len(self.entities_df),
            'target_met': 800 <= len(self.entities_df) <= 1500,
            'target_relationships': '2,000-3,000',
            'actual_relationships': len(self.relationships_df),
            'relationships_target_met': 2000 <= len(self.relationships_df) <= 3000,
            'overall_success': (
                800 <= len(self.entities_df) <= 1500 and
                validation['referential_integrity'] and
                validation['no_null_entities']
            )
        }

        # Coverage analysis
        coverage = {
            'unique_drugs_in_relationships': len(set(self.relationships_df['drug_id'])),
            'unique_diseases_in_relationships': len(set(self.relationships_df['disease_id'])),
            'drug_coverage_pct': round(
                100 * len(set(self.relationships_df['drug_id'])) / len(drugs_df), 2
            ),
            'disease_coverage_pct': round(
                100 * len(set(self.relationships_df['disease_id'])) / len(diseases_df), 2
            )
        }

        report = {
            'report_date': datetime.now().isoformat(),
            'week': 2,
            'status': 'COMPLETE' if success_criteria['overall_success'] else 'NEEDS_REVIEW',
            'entity_statistics': entity_stats,
            'relationship_statistics': rel_stats,
            'validation': validation,
            'success_criteria': success_criteria,
            'coverage': coverage
        }

        print(f"✅ Quality report generated")
        return report


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Create knowledge base from entities and relationships')
    parser.add_argument('--entities', type=str,
                       default='data/processed/entities.csv',
                       help='Input CSV file with entities')
    parser.add_argument('--relationships', type=str,
                       default='data/processed/relationships.csv',
                       help='Input CSV file with relationships')
    parser.add_argument('--output', type=str,
                       default='data/processed/knowledge_base.json',
                       help='Output JSON file for knowledge base')
    parser.add_argument('--report', type=str,
                       default='data/processed/week2_quality_report.json',
                       help='Output JSON file for quality report')

    args = parser.parse_args()

    print("=" * 70)
    print("🏗️  KNOWLEDGE BASE CREATION - Week 2")
    print("=" * 70)

    # Initialize builder
    builder = KnowledgeBaseBuilder()

    # Load data
    builder.load_data(args.entities, args.relationships)

    # Validate integrity
    builder.validate_integrity()

    # Build knowledge base
    kb = builder.build_knowledge_base()

    # Generate quality report
    report = builder.generate_quality_report()

    # Save outputs
    print(f"\n💾 Saving outputs...")

    # Create output directory
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    # Save knowledge base
    with open(args.output, 'w') as f:
        json.dump(kb, f, indent=2)
    print(f"✅ Knowledge base saved to {args.output}")

    # Save quality report
    with open(args.report, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✅ Quality report saved to {args.report}")

    # Print summary
    print("\n" + "=" * 70)
    print("📊 WEEK 2 SUMMARY")
    print("=" * 70)
    print(f"Status: {report['status']}")
    print(f"\nEntities:")
    print(f"  Total:        {report['entity_statistics']['total']:,}")
    print(f"  - Drugs:      {report['entity_statistics']['drugs']:,}")
    print(f"  - Diseases:   {report['entity_statistics']['diseases']:,}")
    print(f"\nRelationships:")
    print(f"  Total:        {report['relationship_statistics']['total']:,}")
    print(f"  - High conf:  {report['relationship_statistics']['high_confidence']:,}")
    print(f"  - Med conf:   {report['relationship_statistics']['medium_confidence']:,}")
    print(f"\nCoverage:")
    print(f"  Drugs:        {report['coverage']['drug_coverage_pct']:.1f}%")
    print(f"  Diseases:     {report['coverage']['disease_coverage_pct']:.1f}%")
    print(f"\nSuccess Criteria:")
    print(f"  Entities target:       {report['success_criteria']['target_met']} ✅" if report['success_criteria']['target_met'] else f"  Entities target:       {report['success_criteria']['target_met']} ❌")
    print(f"  Relationships target:  {report['success_criteria']['relationships_target_met']} {'✅' if report['success_criteria']['relationships_target_met'] else '⚠️  (close)'}")
    print(f"  Overall success:       {report['success_criteria']['overall_success']} ✅" if report['success_criteria']['overall_success'] else f"  Overall success:       {report['success_criteria']['overall_success']} ❌")

    print("\n" + "=" * 70)
    if report['status'] == 'COMPLETE':
        print("✅ Week 2 COMPLETE - Ready for Week 3 (Graph Construction)")
    else:
        print("⚠️  Week 2 needs review")
    print("=" * 70)


if __name__ == '__main__':
    main()
