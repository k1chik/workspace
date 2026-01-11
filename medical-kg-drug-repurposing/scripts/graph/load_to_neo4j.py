#!/usr/bin/env python3
"""
Neo4j Data Loading Script - Week 3
Load entities and relationships from Week 2 into Neo4j knowledge graph.

Usage:
    python scripts/graph/load_to_neo4j.py [--dry-run] [--clear]

Arguments:
    --dry-run: Test connection and show stats without loading data
    --clear: Clear existing data before loading (DESTRUCTIVE)
"""

import argparse
import pandas as pd
from neo4j import GraphDatabase
from pathlib import Path
from tqdm import tqdm
import time
from datetime import datetime


class Neo4jLoader:
    """Load knowledge graph data into Neo4j database."""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="neo4j"):
        """Initialize Neo4j connection."""
        print(f"\n🔌 Connecting to Neo4j at {uri}...")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            print(f"✅ Connected successfully")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print(f"\n💡 Troubleshooting:")
            print(f"   1. Make sure Neo4j is running: neo4j status")
            print(f"   2. Check connection URI: {uri}")
            print(f"   3. Verify credentials (default: neo4j/neo4j)")
            raise

    def close(self):
        """Close Neo4j connection."""
        self.driver.close()

    def clear_database(self):
        """Clear all nodes and relationships (DESTRUCTIVE!)."""
        print("\n🗑️  Clearing existing data...")
        with self.driver.session() as session:
            # Delete all relationships first
            session.run("MATCH ()-[r]->() DELETE r")
            # Then delete all nodes
            session.run("MATCH (n) DELETE n")
        print("✅ Database cleared")

    def create_constraints_and_indexes(self):
        """Create uniqueness constraints and performance indexes."""
        print("\n📋 Creating constraints and indexes...")

        constraints_and_indexes = [
            # Uniqueness constraints
            "CREATE CONSTRAINT drug_id_unique IF NOT EXISTS FOR (d:Drug) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT disease_id_unique IF NOT EXISTS FOR (dis:Disease) REQUIRE dis.id IS UNIQUE",

            # Performance indexes
            "CREATE INDEX drug_name_index IF NOT EXISTS FOR (d:Drug) ON (d.name)",
            "CREATE INDEX disease_name_index IF NOT EXISTS FOR (dis:Disease) ON (dis.name)",
            "CREATE INDEX drug_frequency_index IF NOT EXISTS FOR (d:Drug) ON (d.frequency)",
            "CREATE INDEX disease_frequency_index IF NOT EXISTS FOR (dis:Disease) ON (dis.frequency)",
        ]

        with self.driver.session() as session:
            for stmt in constraints_and_indexes:
                try:
                    session.run(stmt)
                except Exception as e:
                    # Constraint/index might already exist
                    if "already exists" not in str(e).lower():
                        print(f"⚠️  Warning: {e}")

        print("✅ Constraints and indexes created")

    def load_nodes(self, entities_df, batch_size=500):
        """Load Drug and Disease nodes from entities DataFrame."""
        print(f"\n📦 Loading nodes (batch size: {batch_size})...")

        # Separate drugs and diseases
        drugs_df = entities_df[entities_df['entity_type'] == 'CHEMICAL'].copy()
        diseases_df = entities_df[entities_df['entity_type'] == 'DISEASE'].copy()

        print(f"   - {len(drugs_df)} Drug nodes")
        print(f"   - {len(diseases_df)} Disease nodes")

        # Load Drug nodes
        print("\n   Loading Drug nodes...")
        self._load_node_batch(drugs_df, 'Drug', batch_size)

        # Load Disease nodes
        print("   Loading Disease nodes...")
        self._load_node_batch(diseases_df, 'Disease', batch_size)

        print(f"✅ All {len(entities_df)} nodes loaded")

    def _load_node_batch(self, df, label, batch_size):
        """Load nodes in batches for better performance."""
        total_batches = (len(df) + batch_size - 1) // batch_size

        with self.driver.session() as session:
            for i in tqdm(range(0, len(df), batch_size),
                         desc=f"   {label} batches",
                         total=total_batches):
                batch = df.iloc[i:i+batch_size]

                # Convert batch to list of dicts
                nodes = []
                for _, row in batch.iterrows():
                    # Convert source_pmids string to list
                    pmids = row['source_pmids'].split(',') if pd.notna(row['source_pmids']) else []

                    node_data = {
                        'id': row['entity_id'],
                        'name': row['entity_text'],
                        'frequency': int(row['frequency']),
                        'num_papers': int(row['num_papers']),
                        'source_pmids': pmids
                    }

                    # Add PubChem properties for validated drugs
                    if label == 'Drug' and 'pubchem_cid' in row and pd.notna(row['pubchem_cid']):
                        node_data['pubchem_cid'] = int(row['pubchem_cid'])
                        node_data['validated'] = bool(row.get('validated', False))

                        if pd.notna(row.get('molecular_formula')):
                            node_data['molecular_formula'] = str(row['molecular_formula'])
                        if pd.notna(row.get('molecular_weight')):
                            node_data['molecular_weight'] = float(row['molecular_weight'])
                        if pd.notna(row.get('canonical_smiles')):
                            node_data['canonical_smiles'] = str(row['canonical_smiles'])
                        if pd.notna(row.get('iupac_name')):
                            node_data['iupac_name'] = str(row['iupac_name'])
                    elif label == 'Drug':
                        # Mark as unvalidated if no PubChem data
                        node_data['validated'] = False

                    nodes.append(node_data)

                # Batch insert using UNWIND
                query = f"""
                UNWIND $nodes AS node
                CREATE (n:{label})
                SET n = node
                """
                session.run(query, nodes=nodes)

    def load_relationships(self, relationships_df, batch_size=500):
        """Load TREATS relationships."""
        print(f"\n🔗 Loading {len(relationships_df)} relationships (batch size: {batch_size})...")

        total_batches = (len(relationships_df) + batch_size - 1) // batch_size

        with self.driver.session() as session:
            for i in tqdm(range(0, len(relationships_df), batch_size),
                         desc="   Relationship batches",
                         total=total_batches):
                batch = relationships_df.iloc[i:i+batch_size]

                # Convert batch to list of dicts
                relationships = []
                for _, row in batch.iterrows():
                    # Convert comma-separated strings to lists
                    pmids = row['evidence_pmids'].split(',') if pd.notna(row['evidence_pmids']) else []
                    methods = row['extraction_methods'].split(',') if pd.notna(row['extraction_methods']) else []

                    relationships.append({
                        'drug_id': row['drug_id'],
                        'disease_id': row['disease_id'],
                        'confidence': float(row['confidence']),
                        'evidence_text': row['evidence_text'] if pd.notna(row['evidence_text']) else "",
                        'evidence_pmids': pmids,
                        'num_papers': int(row['num_papers']),
                        'extraction_methods': methods
                    })

                # Batch insert relationships
                query = """
                UNWIND $relationships AS rel
                MATCH (d:Drug {id: rel.drug_id})
                MATCH (dis:Disease {id: rel.disease_id})
                CREATE (d)-[r:TREATS]->(dis)
                SET r.confidence = rel.confidence,
                    r.evidence_text = rel.evidence_text,
                    r.evidence_pmids = rel.evidence_pmids,
                    r.num_papers = rel.num_papers,
                    r.extraction_methods = rel.extraction_methods
                """
                session.run(query, relationships=relationships)

        print(f"✅ All {len(relationships_df)} relationships loaded")

    def validate_data(self):
        """Validate loaded data integrity."""
        print("\n🔍 Validating loaded data...")

        with self.driver.session() as session:
            # Count nodes
            drug_count = session.run("MATCH (d:Drug) RETURN count(d) as count").single()['count']
            disease_count = session.run("MATCH (dis:Disease) RETURN count(dis) as count").single()['count']
            total_nodes = drug_count + disease_count

            # Count relationships
            rel_count = session.run("MATCH ()-[r:TREATS]->() RETURN count(r) as count").single()['count']

            # Check for orphaned relationships (shouldn't happen)
            orphan_check = session.run("""
                MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
                WHERE d.id IS NULL OR dis.id IS NULL
                RETURN count(r) as orphan_count
            """).single()['orphan_count']

            # Get sample relationship
            sample_rel = session.run("""
                MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
                RETURN d.name as drug, dis.name as disease, r.confidence as confidence
                LIMIT 1
            """).single()

        print(f"\n   📊 Validation Results:")
        print(f"   - Drug nodes:       {drug_count:,}")
        print(f"   - Disease nodes:    {disease_count:,}")
        print(f"   - Total nodes:      {total_nodes:,}")
        print(f"   - Relationships:    {rel_count:,}")
        print(f"   - Orphaned rels:    {orphan_check:,} (should be 0)")

        if sample_rel:
            print(f"\n   🔬 Sample relationship:")
            print(f"   - {sample_rel['drug']} → {sample_rel['disease']}")
            print(f"   - Confidence: {sample_rel['confidence']}")

        # Validation checks
        validation_passed = orphan_check == 0

        if validation_passed:
            print(f"\n✅ Validation PASSED")
        else:
            print(f"\n❌ Validation FAILED - orphaned relationships detected")

        return validation_passed, {
            'drug_count': drug_count,
            'disease_count': disease_count,
            'total_nodes': total_nodes,
            'relationship_count': rel_count,
            'orphaned_relationships': orphan_check
        }

    def get_statistics(self):
        """Get graph statistics."""
        print("\n📈 Computing graph statistics...")

        with self.driver.session() as session:
            # Top drugs by relationship count
            top_drugs = session.run("""
                MATCH (d:Drug)-[:TREATS]->()
                WITH d, count(*) as rel_count
                RETURN d.name as drug, rel_count
                ORDER BY rel_count DESC
                LIMIT 5
            """).values()

            # Top diseases by relationship count
            top_diseases = session.run("""
                MATCH ()-[:TREATS]->(dis:Disease)
                WITH dis, count(*) as rel_count
                RETURN dis.name as disease, rel_count
                ORDER BY rel_count DESC
                LIMIT 5
            """).values()

            # High confidence relationships
            high_conf = session.run("""
                MATCH ()-[r:TREATS]->()
                WHERE r.confidence >= 0.8
                RETURN count(r) as high_conf_count
            """).single()['high_conf_count']

            # Average confidence
            avg_conf = session.run("""
                MATCH ()-[r:TREATS]->()
                RETURN avg(r.confidence) as avg_confidence
            """).single()['avg_confidence']

        print(f"\n   🔝 Top 5 Drugs by Relationships:")
        for drug, count in top_drugs:
            print(f"      - {drug}: {count} diseases")

        print(f"\n   🔝 Top 5 Diseases by Relationships:")
        for disease, count in top_diseases:
            print(f"      - {disease}: {count} drugs")

        print(f"\n   📊 Relationship Statistics:")
        print(f"      - High confidence (≥0.8): {high_conf}")
        print(f"      - Average confidence:     {avg_conf:.3f}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Load knowledge graph data into Neo4j')
    parser.add_argument('--entities', type=str,
                       default='data/processed/entities_normalized.csv',
                       help='Input CSV file with entities (normalized with PubChem data)')
    parser.add_argument('--relationships', type=str,
                       default='data/processed/relationships.csv',
                       help='Input CSV file with relationships')
    parser.add_argument('--uri', type=str,
                       default='bolt://localhost:7687',
                       help='Neo4j connection URI')
    parser.add_argument('--user', type=str,
                       default='neo4j',
                       help='Neo4j username')
    parser.add_argument('--password', type=str,
                       default='neo4j',
                       help='Neo4j password')
    parser.add_argument('--dry-run', action='store_true',
                       help='Test connection without loading data')
    parser.add_argument('--clear', action='store_true',
                       help='Clear existing data before loading (DESTRUCTIVE)')
    parser.add_argument('--batch-size', type=int,
                       default=500,
                       help='Batch size for loading')

    args = parser.parse_args()

    print("=" * 70)
    print("🚀 NEO4J DATA LOADER - Week 3")
    print("=" * 70)

    # Load CSV files
    print(f"\n📖 Loading CSV files...")
    entities_df = pd.read_csv(args.entities)
    relationships_df = pd.read_csv(args.relationships)
    print(f"✅ Loaded {len(entities_df)} entities")
    print(f"✅ Loaded {len(relationships_df)} relationships")

    # Connect to Neo4j
    loader = Neo4jLoader(args.uri, args.user, args.password)

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No data will be loaded")
        print(f"\n   Would load:")
        print(f"   - {len(entities_df[entities_df['entity_type'] == 'CHEMICAL'])} Drug nodes")
        print(f"   - {len(entities_df[entities_df['entity_type'] == 'DISEASE'])} Disease nodes")
        print(f"   - {len(relationships_df)} TREATS relationships")
        loader.close()
        return

    try:
        start_time = time.time()

        # Clear database if requested
        if args.clear:
            confirm = input("\n⚠️  This will DELETE all data in Neo4j. Continue? (yes/no): ")
            if confirm.lower() == 'yes':
                loader.clear_database()
            else:
                print("❌ Aborted")
                loader.close()
                return

        # Create constraints and indexes
        loader.create_constraints_and_indexes()

        # Load nodes
        loader.load_nodes(entities_df, batch_size=args.batch_size)

        # Load relationships
        loader.load_relationships(relationships_df, batch_size=args.batch_size)

        # Validate data
        validation_passed, stats = loader.validate_data()

        # Get statistics
        loader.get_statistics()

        end_time = time.time()
        duration = end_time - start_time

        print("\n" + "=" * 70)
        print("📊 LOADING SUMMARY")
        print("=" * 70)
        print(f"Status:           {'✅ SUCCESS' if validation_passed else '❌ FAILED'}")
        print(f"Time taken:       {duration:.2f} seconds")
        print(f"Nodes loaded:     {stats['total_nodes']:,}")
        print(f"Relationships:    {stats['relationship_count']:,}")
        print(f"")
        print(f"🌐 Access Neo4j Browser: http://localhost:7474")
        print(f"")
        print("Sample queries to try:")
        print("  MATCH (d:Drug)-[r:TREATS]->(dis:Disease) RETURN d, r, dis LIMIT 25")
        print("  MATCH (d:Drug {name: 'metformin'})-[r:TREATS]->(dis) RETURN d, r, dis")
        print("=" * 70)

        if validation_passed:
            print("\n✅ Knowledge graph loaded successfully!")
        else:
            print("\n❌ Validation failed - please check the data")

    finally:
        loader.close()


if __name__ == '__main__':
    main()
