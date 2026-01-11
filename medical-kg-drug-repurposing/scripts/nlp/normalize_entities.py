#!/usr/bin/env python3
"""
Drug Entity Normalization - PubChem Integration

This script normalizes drug entities by matching them to PubChem drugs
and filtering out false positives.

Usage:
    python scripts/nlp/normalize_entities.py

Input:
    - data/processed/entities.csv (raw extracted entities)
    - data/raw/pubchem_drugs.csv (PubChem reference drugs)

Output:
    - data/processed/entities_normalized.csv (cleaned & enriched entities)
    - data/processed/normalization_report.json (statistics)
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict
import argparse


def load_pubchem_data(pubchem_file):
    """
    Load PubChem drugs and create synonym mappings.

    Returns:
        dict: Mapping from drug name/synonym -> PubChem record
    """
    print(f"📥 Loading PubChem data from {pubchem_file}...")

    df = pd.read_csv(pubchem_file)
    print(f"   Loaded {len(df)} PubChem drugs")

    # Create synonym mapping
    drug_mapping = {}

    for _, row in df.iterrows():
        canonical_name = row['name'].lower()
        cid = row['cid']

        # Add canonical name
        drug_mapping[canonical_name] = {
            'canonical_name': row['name'],
            'cid': cid,
            'molecular_formula': row.get('molecular_formula', ''),
            'molecular_weight': row.get('molecular_weight', ''),
            'canonical_smiles': row.get('canonical_smiles', ''),
            'iupac_name': row.get('iupac_name', ''),
            'synonyms': row.get('synonyms', '')
        }

        # Add synonyms
        if pd.notna(row.get('synonyms')):
            synonyms = str(row['synonyms']).split('|')
            for syn in synonyms[:20]:  # First 20 synonyms
                syn_lower = syn.strip().lower()
                if syn_lower and syn_lower not in drug_mapping:
                    drug_mapping[syn_lower] = drug_mapping[canonical_name]

    print(f"   Created mapping with {len(drug_mapping)} drug names/synonyms")
    return drug_mapping


def normalize_entities(entities_df, drug_mapping):
    """
    Normalize drug entities using PubChem mapping.

    Args:
        entities_df: DataFrame with extracted entities
        drug_mapping: PubChem synonym mapping

    Returns:
        DataFrame: Normalized entities with PubChem info
    """
    print(f"\n🔄 Normalizing entities...")

    # Separate drugs and diseases
    drugs = entities_df[entities_df['entity_type'] == 'CHEMICAL'].copy()
    diseases = entities_df[entities_df['entity_type'] == 'DISEASE'].copy()

    print(f"   Original: {len(drugs)} drugs, {len(diseases)} diseases")

    # Normalize drug names
    normalized_drugs = []
    matched_count = 0
    unmatched_drugs = []

    for _, drug in drugs.iterrows():
        drug_name_lower = drug['entity_text'].lower()

        if drug_name_lower in drug_mapping:
            # Matched to PubChem!
            pubchem_info = drug_mapping[drug_name_lower]
            matched_count += 1

            normalized_drugs.append({
                'entity_id': drug['entity_id'],
                'entity_text': pubchem_info['canonical_name'],  # Use canonical name
                'entity_type': 'CHEMICAL',
                'frequency': drug['frequency'],
                'num_papers': drug['num_papers'],
                # Add PubChem info
                'pubchem_cid': pubchem_info['cid'],
                'molecular_formula': pubchem_info['molecular_formula'],
                'molecular_weight': pubchem_info['molecular_weight'],
                'canonical_smiles': pubchem_info['canonical_smiles'],
                'iupac_name': pubchem_info['iupac_name'],
                'validated': True
            })
        else:
            # Not found in PubChem
            unmatched_drugs.append(drug['entity_text'])

            # Keep but mark as unvalidated
            normalized_drugs.append({
                'entity_id': drug['entity_id'],
                'entity_text': drug['entity_text'],
                'entity_type': 'CHEMICAL',
                'frequency': drug['frequency'],
                'num_papers': drug['num_papers'],
                'pubchem_cid': None,
                'molecular_formula': None,
                'molecular_weight': None,
                'canonical_smiles': None,
                'iupac_name': None,
                'validated': False
            })

    # Convert to DataFrame
    drugs_normalized = pd.DataFrame(normalized_drugs)

    # Merge duplicates (same canonical name)
    print(f"\n   Merging duplicate drug names...")
    drugs_merged = drugs_normalized.groupby('entity_text').agg({
        'entity_id': 'first',
        'entity_type': 'first',
        'frequency': 'sum',  # Sum frequencies
        'num_papers': 'sum',  # Sum paper counts
        'pubchem_cid': 'first',
        'molecular_formula': 'first',
        'molecular_weight': 'first',
        'canonical_smiles': 'first',
        'iupac_name': 'first',
        'validated': 'first'
    }).reset_index()

    # Add diseases (unchanged)
    diseases_normalized = diseases.copy()
    diseases_normalized['pubchem_cid'] = None
    diseases_normalized['molecular_formula'] = None
    diseases_normalized['molecular_weight'] = None
    diseases_normalized['canonical_smiles'] = None
    diseases_normalized['iupac_name'] = None
    diseases_normalized['validated'] = True  # Diseases are always valid

    # Combine
    all_entities = pd.concat([drugs_merged, diseases_normalized], ignore_index=True)

    # Statistics
    validated_drugs = drugs_merged[drugs_merged['validated'] == True]
    unvalidated_drugs = drugs_merged[drugs_merged['validated'] == False]

    print(f"\n✅ Normalization complete:")
    print(f"   • Drugs matched to PubChem: {len(validated_drugs)} ({matched_count} original)")
    print(f"   • Drugs NOT in PubChem: {len(unvalidated_drugs)}")
    print(f"   • Diseases: {len(diseases)}")
    print(f"   • Total entities: {len(all_entities)}")
    print(f"   • Reduction: {len(entities_df)} → {len(all_entities)} (-{len(entities_df) - len(all_entities)})")

    report = {
        'original_entities': len(entities_df),
        'original_drugs': len(drugs),
        'original_diseases': len(diseases),
        'normalized_entities': len(all_entities),
        'normalized_drugs': len(drugs_merged),
        'validated_drugs': len(validated_drugs),
        'unvalidated_drugs': len(unvalidated_drugs),
        'diseases': len(diseases),
        'drugs_merged': len(drugs) - len(drugs_merged),
        'matched_to_pubchem': matched_count,
        'unmatched_drugs_sample': unmatched_drugs[:20]
    }

    return all_entities, report


def main():
    parser = argparse.ArgumentParser(description='Normalize entities with PubChem data')
    parser.add_argument(
        '--entities',
        default='data/processed/entities.csv',
        help='Input entities CSV'
    )
    parser.add_argument(
        '--pubchem',
        default='data/raw/pubchem_drugs.csv',
        help='PubChem drugs CSV'
    )
    parser.add_argument(
        '--output',
        default='data/processed/entities_normalized.csv',
        help='Output normalized entities CSV'
    )

    args = parser.parse_args()

    # Check files exist
    entities_file = Path(args.entities)
    pubchem_file = Path(args.pubchem)

    if not entities_file.exists():
        print(f"❌ Entities file not found: {entities_file}")
        return

    if not pubchem_file.exists():
        print(f"❌ PubChem file not found: {pubchem_file}")
        return

    # Load data
    entities_df = pd.read_csv(entities_file)
    print(f"📥 Loaded {len(entities_df)} entities from {entities_file}")

    drug_mapping = load_pubchem_data(pubchem_file)

    # Normalize
    normalized_entities, report = normalize_entities(entities_df, drug_mapping)

    # Save normalized entities
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    normalized_entities.to_csv(output_file, index=False)
    print(f"\n💾 Saved normalized entities to: {output_file}")

    # Save report
    report_file = output_file.parent / 'normalization_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"📊 Saved report to: {report_file}")

    # Show sample
    print(f"\n📋 Sample normalized drugs:")
    validated_sample = normalized_entities[
        (normalized_entities['entity_type'] == 'CHEMICAL') &
        (normalized_entities['validated'] == True)
    ][['entity_text', 'pubchem_cid', 'molecular_formula', 'frequency']].head(10)
    print(validated_sample.to_string())

    print(f"\n⚠️  Sample unvalidated drugs:")
    unvalidated_sample = normalized_entities[
        (normalized_entities['entity_type'] == 'CHEMICAL') &
        (normalized_entities['validated'] == False)
    ][['entity_text', 'frequency', 'num_papers']].head(5)
    if len(unvalidated_sample) > 0:
        print(unvalidated_sample.to_string())
    else:
        print("   None! All drugs validated ✅")


if __name__ == "__main__":
    main()
