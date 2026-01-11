#!/usr/bin/env python3
"""
Validate Predictions - Week 5
Validate GNN predictions against PubMed literature.

Usage:
    python scripts/validation/validate_predictions.py --top-k 100
"""

import pandas as pd
import json
import time
from pathlib import Path
import argparse
from Bio import Entrez
from collections import defaultdict
import sys

# Set email for NCBI (required by PubMed API)
Entrez.email = "student@example.com"


class PredictionValidator:
    """Validate drug-disease predictions against PubMed literature."""

    def __init__(self, predictions_path='data/results/novel_predictions.csv'):
        print(f"\n📖 Loading predictions from {predictions_path}...")
        self.predictions_df = pd.read_csv(predictions_path)
        print(f"   ✅ Loaded {len(self.predictions_df)} predictions")

    def search_pubmed(self, drug, disease, max_results=100):
        """
        Search PubMed for articles mentioning both drug and disease.

        Args:
            drug: Drug name
            disease: Disease name
            max_results: Maximum articles to retrieve

        Returns:
            dict with count and article titles
        """
        # Create search query
        query = f'("{drug}"[Title/Abstract]) AND ("{disease}"[Title/Abstract])'

        try:
            # Search PubMed
            handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
            record = Entrez.read(handle)
            handle.close()

            count = int(record["Count"])
            id_list = record["IdList"]

            # Fetch article titles if there are results
            titles = []
            if id_list:
                # Fetch details for up to 5 articles
                fetch_handle = Entrez.efetch(db="pubmed", id=id_list[:5], rettype="medline", retmode="text")
                articles = fetch_handle.read()
                fetch_handle.close()

                # Simple title extraction
                for line in articles.split('\n'):
                    if line.startswith('TI  - '):
                        titles.append(line[6:].strip())

            return {
                'count': count,
                'titles': titles[:5]  # Top 5 titles
            }

        except Exception as e:
            print(f"   ⚠️  Error searching for '{drug}' + '{disease}': {e}")
            return {'count': 0, 'titles': []}

    def classify_prediction(self, count):
        """
        Classify prediction based on literature support.

        Categories:
        - Confirmed: Strong evidence (≥5 papers)
        - Emerging: Some evidence (1-4 papers)
        - Novel: No direct evidence (0 papers) - highest value!
        - Uncertain: Reserved for manual review
        """
        if count >= 5:
            return 'Confirmed'
        elif count >= 1:
            return 'Emerging'
        else:
            return 'Novel'

    def validate_predictions(self, top_k=100, rate_limit_delay=0.5):
        """
        Validate top-K predictions against PubMed.

        Args:
            top_k: Number of predictions to validate
            rate_limit_delay: Delay between API calls (seconds)

        Returns:
            DataFrame with validation results
        """
        print(f"\n🔍 Validating top {top_k} predictions against PubMed...")
        print(f"   This may take ~{int(top_k * rate_limit_delay / 60)} minutes due to API rate limits")
        print()

        validation_results = []

        for idx, row in self.predictions_df.head(top_k).iterrows():
            drug = row['drug']
            disease = row['disease']
            confidence = row['confidence']
            rank = row['rank']

            print(f"   [{rank}/{top_k}] Searching: {drug} + {disease}...", end='')

            # Search PubMed
            pubmed_result = self.search_pubmed(drug, disease)
            count = pubmed_result['count']
            titles = pubmed_result['titles']

            # Classify
            validation_status = self.classify_prediction(count)

            print(f" {count} papers → {validation_status}")

            validation_results.append({
                'rank': rank,
                'drug': drug,
                'disease': disease,
                'confidence': confidence,
                'pubmed_count': count,
                'validation_status': validation_status,
                'sample_titles': titles
            })

            # Rate limiting
            time.sleep(rate_limit_delay)

        validation_df = pd.DataFrame(validation_results)
        return validation_df

    def generate_summary(self, validation_df):
        """Generate validation summary statistics."""
        summary = {
            'total_validated': len(validation_df),
            'confirmed': (validation_df['validation_status'] == 'Confirmed').sum(),
            'emerging': (validation_df['validation_status'] == 'Emerging').sum(),
            'novel': (validation_df['validation_status'] == 'Novel').sum(),
            'avg_confidence': float(validation_df['confidence'].mean()),
            'avg_pubmed_count': float(validation_df['pubmed_count'].mean()),
            'max_pubmed_count': int(validation_df['pubmed_count'].max()),
            'validation_by_status': {}
        }

        # Breakdown by status
        for status in ['Confirmed', 'Emerging', 'Novel']:
            status_df = validation_df[validation_df['validation_status'] == status]
            if len(status_df) > 0:
                summary['validation_by_status'][status] = {
                    'count': len(status_df),
                    'avg_confidence': float(status_df['confidence'].mean()),
                    'avg_pubmed_count': float(status_df['pubmed_count'].mean()),
                    'top_predictions': status_df.head(5)[['drug', 'disease', 'confidence']].to_dict('records')
                }

        return summary


def main():
    parser = argparse.ArgumentParser(description='Validate predictions against PubMed')
    parser.add_argument('--top-k', type=int, default=100, help='Number of predictions to validate')
    parser.add_argument('--rate-limit', type=float, default=0.5, help='Delay between API calls (seconds)')

    args = parser.parse_args()

    print("=" * 70)
    print("🔬 PREDICTION VALIDATION - PubMed Literature Search")
    print("=" * 70)

    # Initialize validator
    validator = PredictionValidator()

    # Validate predictions
    validation_df = validator.validate_predictions(
        top_k=args.top_k,
        rate_limit_delay=args.rate_limit
    )

    # Generate summary
    print(f"\n📊 Generating summary...")
    summary = validator.generate_summary(validation_df)

    # Save results
    print(f"\n💾 Saving results...")

    # Save validation report
    validation_path = 'data/results/validation_report.csv'
    Path(validation_path).parent.mkdir(parents=True, exist_ok=True)
    validation_df.to_csv(validation_path, index=False)
    print(f"   ✅ Validation report: {validation_path}")

    # Save summary
    summary_path = 'data/results/validation_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"   ✅ Summary: {summary_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Total predictions validated: {summary['total_validated']}")
    print(f"\nValidation Status Breakdown:")
    print(f"  ✅ Confirmed (≥5 papers):  {summary['confirmed']:>3} ({summary['confirmed']/summary['total_validated']*100:.1f}%)")
    print(f"  🔬 Emerging (1-4 papers):   {summary['emerging']:>3} ({summary['emerging']/summary['total_validated']*100:.1f}%)")
    print(f"  🆕 Novel (0 papers):        {summary['novel']:>3} ({summary['novel']/summary['total_validated']*100:.1f}%)")

    print(f"\nAverage PubMed articles per prediction: {summary['avg_pubmed_count']:.1f}")
    print(f"Maximum PubMed articles for a prediction: {summary['max_pubmed_count']}")

    # Show top novel predictions
    novel_df = validation_df[validation_df['validation_status'] == 'Novel']
    if len(novel_df) > 0:
        print(f"\n🆕 TOP 10 NOVEL PREDICTIONS (No Existing Literature)")
        print("=" * 70)
        print(f"{'Rank':<6} {'Drug':<25} {'Disease':<30} {'Confidence':<12}")
        print("-" * 70)

        for _, row in novel_df.head(10).iterrows():
            drug = row['drug'][:23] + '..' if len(row['drug']) > 25 else row['drug']
            disease = row['disease'][:28] + '..' if len(row['disease']) > 30 else row['disease']
            print(f"{row['rank']:<6} {drug:<25} {disease:<30} {row['confidence']:<12.4f}")

    # Show top confirmed predictions
    confirmed_df = validation_df[validation_df['validation_status'] == 'Confirmed']
    if len(confirmed_df) > 0:
        print(f"\n✅ TOP 10 CONFIRMED PREDICTIONS (Strong Literature Support)")
        print("=" * 70)
        print(f"{'Rank':<6} {'Drug':<25} {'Disease':<25} {'Papers':<8} {'Conf':<8}")
        print("-" * 70)

        for _, row in confirmed_df.head(10).iterrows():
            drug = row['drug'][:23] + '..' if len(row['drug']) > 25 else row['drug']
            disease = row['disease'][:23] + '..' if len(row['disease']) > 25 else row['disease']
            print(f"{row['rank']:<6} {drug:<25} {disease:<25} {row['pubmed_count']:<8} {row['confidence']:<8.4f}")

    print("=" * 70)
    print(f"\n✅ Validation complete!")
    print(f"   Novel predictions (highest value): {summary['novel']}")
    print(f"   These represent potential drug repurposing opportunities!")
    print("=" * 70)


if __name__ == '__main__':
    main()
