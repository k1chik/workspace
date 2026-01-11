#!/usr/bin/env python3
"""
Collect drug information from PubChem for common repurposing drugs.

This script:
1. Uses a curated list of ~120 FDA-approved drugs frequently studied for repurposing
2. Queries PubChem API for detailed drug information
3. Saves to CSV

Usage:
    python collect_pubchem.py --output data/raw/pubchem_drugs.csv --max-drugs 200
"""
"""command line arg parser"""
import argparse

import time
from pathlib import Path

"""http requests"""
import requests
import pandas as pd
from tqdm import tqdm


PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def get_curated_drug_list():
    """
    Return a curated list of drugs commonly mentioned in drug repurposing research.
    These are FDA-approved drugs that have been extensively studied for repurposing.
    """
    print("Using curated list of common repurposing drugs...")

    drugs = [
        # Diabetes drugs (studied for cancer, Alzheimer's, etc.)
        "Metformin", "Pioglitazone", "Glipizide", "Glyburide",

        # Cardiovascular drugs
        "Aspirin", "Atorvastatin", "Simvastatin", "Losartan", "Carvedilol",
        "Propranolol", "Verapamil", "Digoxin", "Warfarin",

        # Anti-inflammatory/Immunomodulatory
        "Ibuprofen", "Naproxen", "Celecoxib", "Dexamethasone", "Prednisone",
        "Hydroxychloroquine", "Colchicine", "Sulfasalazine",

        # Antibiotics (studied for cancer, viral infections)
        "Doxycycline", "Azithromycin", "Clarithromycin", "Tetracycline",
        "Minocycline", "Ciprofloxacin",

        # Antiviral/Antimalarial
        "Remdesivir", "Ribavirin", "Oseltamivir", "Chloroquine", "Ivermectin",

        # Cancer drugs (studied for other diseases)
        "Tamoxifen", "Paclitaxel", "Doxorubicin", "Cisplatin", "Imatinib",
        "Bevacizumab", "Sunitinib",

        # Neurological/Psychiatric
        "Fluoxetine", "Sertraline", "Venlafaxine", "Amitriptyline",
        "Valproic acid", "Lithium", "Memantine", "Donepezil", "Rivastigmine",

        # Erectile dysfunction (studied for heart disease, pulmonary hypertension)
        "Sildenafil", "Tadalafil", "Vardenafil",

        # Anticoagulants
        "Heparin", "Enoxaparin", "Rivaroxaban", "Apixaban",

        # Antifungal
        "Itraconazole", "Fluconazole", "Ketoconazole",

        # Other repurposing candidates
        "Thalidomide", "Rapamycin", "Everolimus", "Niclosamide",
        "Disulfiram", "Artemisinin", "Melatonin", "Vitamin D",
        "N-acetylcysteine", "Curcumin", "Resveratrol",

        # Antihistamines
        "Diphenhydramine", "Cetirizine", "Loratadine",

        # Proton pump inhibitors
        "Omeprazole", "Pantoprazole", "Esomeprazole",

        # Anticonvulsants
        "Phenytoin", "Carbamazepine", "Gabapentin", "Topiramate",

        # Antidiabetic (newer)
        "Liraglutide", "Sitagliptin", "Empagliflozin",

        # Immunosuppressants
        "Cyclosporine", "Tacrolimus", "Mycophenolate",

        # Antimalarials
        "Quinine", "Primaquine", "Artesunate",

        # Anti-parasitic
        "Albendazole", "Mebendazole", "Praziquantel",

        # Hormones
        "Estrogen", "Progesterone", "Testosterone", "Levothyroxine",
        "Insulin",

        # Antipsychotics
        "Haloperidol", "Chlorpromazine", "Risperidone", "Olanzapine",

        # Muscle relaxants
        "Baclofen", "Tizanidine",

        # Others with repurposing potential
        "Allopurinol", "Febuxostat", "Montelukast", "Ranitidine",
        "Cimetidine", "Propofol", "Ketamine", "Lidocaine"
    ]
    
    return drugs


def query_pubchem_by_name(drug_name):
    """
    Query PubChem API to get drug information by name.

    Returns:
        Dictionary with drug information or None if not found
    """
    try:
        search_url = f"{PUBCHEM_BASE}/compound/name/{drug_name}/JSON"
        response = requests.get(search_url, timeout=10)

        if response.status_code == 404:
            return None  # Drug not found

        response.raise_for_status()
        data = response.json()

        if 'PC_Compounds' in data and len(data['PC_Compounds']) > 0:
            compound = data['PC_Compounds'][0]

            # Extract CID
            cid = compound['id']['id']['cid']

            # Extract properties
            props = {}
            if 'props' in compound:
                for prop in compound['props']:
                    urn = prop.get('urn', {})
                    label = urn.get('label', '')
                    value_key = 'sval' if 'sval' in prop['value'] else 'fval'
                    value = prop['value'].get(value_key, '')

                    if label == 'IUPAC Name':
                        props['iupac_name'] = value
                    elif label == 'Molecular Formula':
                        props['molecular_formula'] = value
                    elif label == 'Molecular Weight':
                        props['molecular_weight'] = value
                    elif label == 'Canonical SMILES':
                        props['canonical_smiles'] = value
                    elif label == 'InChI':
                        props['inchi'] = value

            # Get synonyms (alternative names)
            synonyms = []
            if 'synonyms' in compound:
                synonyms = compound['synonyms'][:10]  # First 10 synonyms

            # Get description from PubChem
            description = ""
            try:
                desc_url = f"{PUBCHEM_BASE}/compound/cid/{cid}/description/JSON"
                desc_response = requests.get(desc_url, timeout=5)
                if desc_response.status_code == 200:
                    desc_data = desc_response.json()
                    if 'InformationList' in desc_data:
                        info_list = desc_data['InformationList']['Information']
                        if len(info_list) > 0:
                            description = info_list[0].get('Description', '')
            except Exception:
                pass  # Description is optional

            return {
                'cid': cid,
                'name': drug_name,
                'iupac_name': props.get('iupac_name', ''),
                'molecular_formula': props.get('molecular_formula', ''),
                'molecular_weight': props.get('molecular_weight', ''),
                'canonical_smiles': props.get('canonical_smiles', ''),
                'inchi': props.get('inchi', ''),
                'description': description,
                'synonyms': '|'.join(synonyms)
            }

        return None

    except Exception as e:
        print(f"Error fetching {drug_name}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Collect drug information from PubChem'
    )
    parser.add_argument(
        '--output', '-o',
        default='data/raw/pubchem_drugs.csv',
        help='Output CSV file'
    )
    parser.add_argument(
        '--max-drugs', '-m',
        type=int,
        default=None,
        help='Maximum number of drugs to collect'
    )

    args = parser.parse_args()

    # Get curated drug list
    drugs = get_curated_drug_list()

    if args.max_drugs:
        drugs = drugs[:args.max_drugs]
        print(f"   Limiting to {args.max_drugs} drugs")


    # Collect drug information
    drug_data = []
    for drug_name in tqdm(drugs, desc="Fetching drugs"):
        drug_info = query_pubchem_by_name(drug_name)

        if drug_info:
            drug_data.append(drug_info)
        else:
            print(f"   ⚠️  Could not find: {drug_name}")

        # Rate limiting - be nice to PubChem API
        time.sleep(0.2)


    # Save to CSV
    if drug_data:
        df = pd.DataFrame(drug_data)
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(output_file, index=False)
        print(f"✅ Saved to: {output_file}")

        # Show sample
        print(f"\n📊 Sample drugs:")
        print(df[['cid', 'name', 'molecular_formula']].head(5))

        # Statistics
        print(f"\n📊 Statistics:")
        print(f"   • Total drugs: {len(df)}")
        print(f"   • With IUPAC names: {df['iupac_name'].notna().sum()}")
        print(f"   • With molecular formulas: {df['molecular_formula'].notna().sum()}")
        print(f"   • With synonyms: {df['synonyms'].notna().sum()}")

    else:
        print("❌ No drug data collected")


if __name__ == "__main__":
    main()
