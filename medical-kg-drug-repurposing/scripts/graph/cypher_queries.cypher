// ========================================================================
// CYPHER QUERY EXAMPLES - Drug Repurposing Knowledge Graph
// ========================================================================
//
// These queries demonstrate how to explore and analyze the knowledge graph
// Run these in Neo4j Browser: http://localhost:7474
//
// Graph: 1,514 nodes (718 drugs + 796 diseases) + 663 relationships
// ========================================================================

// ========================================================================
// 1. BASIC EXPLORATION QUERIES
// ========================================================================

// 1.1 Get graph overview (counts)
// Returns total counts of nodes and relationships
MATCH (d:Drug)
WITH count(d) as drug_count
MATCH (dis:Disease)
WITH drug_count, count(dis) as disease_count
MATCH ()-[r:TREATS]->()
RETURN drug_count, disease_count, count(r) as relationship_count;

// 1.2 Sample the graph (random 25 nodes and relationships)
// Useful for getting a feel for the graph structure
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
RETURN d, r, dis
LIMIT 25;

// 1.3 Find a specific drug
// Example: Find metformin
MATCH (d:Drug {name: 'metformin'})
RETURN d;

// 1.4 Find all diseases that a specific drug treats
// Example: What does metformin treat?
MATCH (d:Drug {name: 'metformin'})-[r:TREATS]->(dis:Disease)
RETURN dis.name as disease,
       r.confidence as confidence,
       r.num_papers as evidence_papers,
       r.evidence_text as evidence
ORDER BY r.confidence DESC;

// 1.5 Find all drugs for a specific disease
// Example: What drugs treat cancer?
MATCH (d:Drug)-[r:TREATS]->(dis:Disease {name: 'cancer'})
RETURN d.name as drug,
       r.confidence as confidence,
       r.num_papers as evidence_papers
ORDER BY r.confidence DESC, r.num_papers DESC
LIMIT 20;


// ========================================================================
// 2. DRUG REPURPOSING INSIGHTS
// ========================================================================

// 2.1 Most versatile drugs (treat multiple diseases)
// Find drugs that could be repurposed for many conditions
MATCH (d:Drug)-[:TREATS]->(dis:Disease)
WITH d, count(dis) as disease_count, collect(dis.name) as diseases
WHERE disease_count >= 5
RETURN d.name as drug,
       disease_count,
       d.frequency as mentions_in_papers,
       diseases[0..5] as sample_diseases
ORDER BY disease_count DESC
LIMIT 10;

// 2.2 Diseases with multiple treatment options
// Find diseases with many potential repurposing candidates
MATCH (d:Drug)-[:TREATS]->(dis:Disease)
WITH dis, count(d) as drug_count, collect(d.name) as drugs
WHERE drug_count >= 10
RETURN dis.name as disease,
       drug_count,
       drugs[0..5] as sample_drugs
ORDER BY drug_count DESC
LIMIT 10;

// 2.3 High-confidence repurposing opportunities
// Find the most reliable drug-disease relationships
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
WHERE r.confidence >= 0.8
RETURN d.name as drug,
       dis.name as disease,
       r.confidence as confidence,
       r.num_papers as supporting_papers,
       r.evidence_text as evidence
ORDER BY r.confidence DESC, r.num_papers DESC;

// 2.4 Well-studied drugs (mentioned in many papers)
// Identify drugs with strong research backing
MATCH (d:Drug)
WHERE d.num_papers >= 10
RETURN d.name as drug,
       d.num_papers as paper_count,
       d.frequency as total_mentions
ORDER BY d.num_papers DESC
LIMIT 15;

// 2.5 Rare disease treatments (diseases with few drug options)
// Find opportunities to repurpose drugs for under-served diseases
MATCH (d:Drug)-[:TREATS]->(dis:Disease)
WITH dis, count(d) as drug_count, collect(d.name) as drugs
WHERE drug_count <= 3 AND drug_count > 0
RETURN dis.name as rare_disease,
       drug_count as available_drugs,
       drugs
ORDER BY drug_count ASC, dis.frequency DESC
LIMIT 20;

// 2.6 Multi-paper validated relationships
// Relationships supported by multiple independent studies
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
WHERE r.num_papers >= 3
RETURN d.name as drug,
       dis.name as disease,
       r.num_papers as supporting_papers,
       r.confidence as confidence,
       r.evidence_pmids as pmids
ORDER BY r.num_papers DESC, r.confidence DESC
LIMIT 15;


// ========================================================================
// 3. NETWORK ANALYSIS & PATH FINDING
// ========================================================================

// 3.1 Find shared drugs between two diseases
// Example: What drugs treat both breast cancer and alzheimer's disease?
MATCH (d:Drug)-[:TREATS]->(dis1:Disease {name: 'breast cancer'}),
      (d)-[:TREATS]->(dis2:Disease {name: "alzheimer's disease"})
RETURN d.name as shared_drug,
       d.num_papers as research_papers
ORDER BY d.num_papers DESC;

// 3.2 Find diseases that share drug treatments
// Useful for identifying disease similarity based on treatment overlap
MATCH (d:Drug)-[:TREATS]->(dis1:Disease),
      (d)-[:TREATS]->(dis2:Disease)
WHERE id(dis1) < id(dis2)
WITH dis1, dis2, count(d) as shared_drugs
WHERE shared_drugs >= 3
RETURN dis1.name as disease1,
       dis2.name as disease2,
       shared_drugs
ORDER BY shared_drugs DESC
LIMIT 10;

// 3.3 Find drugs treating similar diseases (drug similarity)
// Drugs are similar if they treat similar diseases
MATCH (d1:Drug)-[:TREATS]->(dis:Disease)<-[:TREATS]-(d2:Drug)
WHERE id(d1) < id(d2)
WITH d1, d2, count(dis) as shared_diseases
WHERE shared_diseases >= 2
RETURN d1.name as drug1,
       d2.name as drug2,
       shared_diseases
ORDER BY shared_diseases DESC
LIMIT 10;

// 3.4 Find shortest path between a drug and a disease (via other drugs/diseases)
// Example: Indirect connections - not direct TREATS relationships
MATCH path = shortestPath((d:Drug {name: 'metformin'})-[*]-(dis:Disease {name: 'breast cancer'}))
WHERE none(r in relationships(path) WHERE type(r) = 'TREATS' AND startNode(r) = d AND endNode(r) = dis)
RETURN path
LIMIT 5;

// 3.5 Ego network for a drug (1-hop neighborhood)
// Show all direct connections from a specific drug
MATCH (center:Drug {name: 'metformin'})-[r:TREATS]->(dis:Disease)
RETURN center, r, dis;


// ========================================================================
// 4. STATISTICAL ANALYSIS
// ========================================================================

// 4.1 Degree distribution (relationship count per node)
// How many relationships does each drug have?
MATCH (d:Drug)
OPTIONAL MATCH (d)-[:TREATS]->()
WITH d, count(*) as degree
RETURN degree, count(d) as num_drugs
ORDER BY degree DESC;

// 4.2 Confidence score distribution
// Analyze the distribution of confidence scores
MATCH ()-[r:TREATS]->()
WITH r.confidence as confidence
RETURN
  count(*) as total_relationships,
  min(confidence) as min_confidence,
  max(confidence) as max_confidence,
  avg(confidence) as avg_confidence,
  percentileCont(confidence, 0.5) as median_confidence,
  percentileCont(confidence, 0.25) as q1_confidence,
  percentileCont(confidence, 0.75) as q3_confidence;

// 4.3 Top drugs by combined metrics (frequency + relationships)
// Identify the most important drugs in the graph
MATCH (d:Drug)
OPTIONAL MATCH (d)-[:TREATS]->(dis:Disease)
WITH d, count(dis) as rel_count
RETURN d.name as drug,
       d.frequency as mentions,
       d.num_papers as papers,
       rel_count as diseases_treated,
       (d.frequency * rel_count) as importance_score
ORDER BY importance_score DESC
LIMIT 20;

// 4.4 Node centrality (most connected nodes)
// Combine both drug and disease perspectives
MATCH (d:Drug)-[:TREATS]->(dis:Disease)
WITH d.name as entity, 'Drug' as type, count(dis) as connections
RETURN entity, type, connections
ORDER BY connections DESC
LIMIT 10
UNION
MATCH (d:Drug)-[:TREATS]->(dis:Disease)
WITH dis.name as entity, 'Disease' as type, count(d) as connections
RETURN entity, type, connections
ORDER BY connections DESC
LIMIT 10;

// 4.5 Extraction method breakdown
// Which methods found the most relationships?
MATCH ()-[r:TREATS]->()
UNWIND r.extraction_methods as method
RETURN method, count(*) as relationship_count
ORDER BY relationship_count DESC;


// ========================================================================
// 5. VALIDATION & QUALITY CHECKS
// ========================================================================

// 5.1 Find relationships without evidence
// Quality check: All relationships should have evidence
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
WHERE r.evidence_text IS NULL OR r.evidence_text = ''
RETURN d.name, dis.name, r.confidence
LIMIT 10;

// 5.2 Find nodes without any relationships (isolated nodes)
// Identify drugs or diseases not connected to anything
MATCH (n)
WHERE NOT (n)-[:TREATS]-() AND NOT ()-[:TREATS]-(n)
RETURN labels(n) as node_type, count(n) as isolated_count;

// 5.3 Check for duplicate relationships (should be 0)
// Ensure data integrity
MATCH (d:Drug)-[r1:TREATS]->(dis:Disease)
MATCH (d)-[r2:TREATS]->(dis)
WHERE id(r1) < id(r2)
RETURN d.name, dis.name, count(*) as duplicate_count;

// 5.4 Evidence provenance audit
// Sample relationships with their evidence
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
RETURN d.name as drug,
       dis.name as disease,
       r.num_papers as papers,
       size(r.evidence_pmids) as pmid_count,
       r.evidence_pmids[0] as first_pmid
LIMIT 20;


// ========================================================================
// 6. DRUG REPURPOSING SPECIFIC QUERIES
// ========================================================================

// 6.1 COVID-19 / Pandemic related drug candidates
// Find drugs mentioned with pandemic/coronavirus
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
WHERE dis.name CONTAINS 'pandemic' OR dis.name CONTAINS 'coronavirus'
RETURN d.name as drug,
       dis.name as disease,
       r.confidence as confidence,
       r.evidence_text as evidence
ORDER BY r.confidence DESC;

// 6.2 Cancer treatment candidates
// Find all drugs with potential for cancer treatment
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
WHERE dis.name CONTAINS 'cancer' OR dis.name CONTAINS 'tumor'
RETURN d.name as drug,
       dis.name as cancer_type,
       r.confidence as confidence,
       r.num_papers as papers
ORDER BY r.confidence DESC, r.num_papers DESC
LIMIT 25;

// 6.3 Neurological disease drug candidates
// Alzheimer's, Parkinson's, etc.
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
WHERE dis.name CONTAINS 'alzheimer'
   OR dis.name CONTAINS 'parkinson'
   OR dis.name CONTAINS 'neurological'
   OR dis.name CONTAINS 'neurodegenerative'
RETURN d.name as drug,
       dis.name as disease,
       r.confidence as confidence,
       r.num_papers as papers
ORDER BY r.confidence DESC;

// 6.4 Identify drugs treating both infectious diseases and cancer
// Interesting for immune system modulation
MATCH (d:Drug)-[:TREATS]->(infectious:Disease),
      (d)-[:TREATS]->(cancer:Disease)
WHERE (infectious.name CONTAINS 'infection' OR infectious.name CONTAINS 'viral')
  AND (cancer.name CONTAINS 'cancer' OR cancer.name CONTAINS 'tumor')
RETURN DISTINCT d.name as versatile_drug,
       collect(DISTINCT infectious.name)[0..3] as infections,
       collect(DISTINCT cancer.name)[0..3] as cancers
LIMIT 10;


// ========================================================================
// 7. ADVANCED GRAPH ALGORITHMS (Neo4j GDS)
// ========================================================================
// Note: These require Neo4j Graph Data Science library
// Installation: https://neo4j.com/docs/graph-data-science/current/installation/

// 7.1 PageRank - Find most "important" nodes
// (Requires GDS library - shown for reference)
/*
CALL gds.pageRank.stream('myGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC
LIMIT 10;
*/

// 7.2 Community Detection - Find clusters
// (Requires GDS library - shown for reference)
/*
CALL gds.louvain.stream('myGraph')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).name AS name, communityId
ORDER BY communityId
LIMIT 50;
*/


// ========================================================================
// 8. EXPORT & REPORTING
// ========================================================================

// 8.1 Export top drug-disease pairs to CSV format
// Copy results to create reports
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
WHERE r.confidence >= 0.5
RETURN d.name as Drug,
       dis.name as Disease,
       r.confidence as Confidence,
       r.num_papers as Papers,
       r.evidence_pmids[0] as FirstPMID
ORDER BY r.confidence DESC, r.num_papers DESC
LIMIT 100;

// 8.2 Graph summary statistics for reporting
MATCH (d:Drug)
WITH count(d) as total_drugs
MATCH (dis:Disease)
WITH total_drugs, count(dis) as total_diseases
MATCH ()-[r:TREATS]->()
WITH total_drugs, total_diseases, count(r) as total_relationships
RETURN
  total_drugs,
  total_diseases,
  total_drugs + total_diseases as total_nodes,
  total_relationships,
  round(total_relationships * 1.0 / (total_drugs + total_diseases), 2) as avg_degree,
  round(total_relationships * 100.0 / (total_drugs * total_diseases), 4) as graph_density_pct;


// ========================================================================
// 9. VISUALIZATION QUERIES
// ========================================================================

// 9.1 Visualize high-confidence network (≥0.6 confidence)
// Good for Neo4j Browser visualization
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
WHERE r.confidence >= 0.6
RETURN d, r, dis
LIMIT 50;

// 9.2 Visualize cancer treatment network
// Focus on one disease for clarity
MATCH (d:Drug)-[r:TREATS]->(dis:Disease {name: 'cancer'})
RETURN d, r, dis
LIMIT 30;

// 9.3 Visualize top drugs and their targets
// Show the most versatile drugs
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
WITH d, count(*) as degree
WHERE degree >= 7
MATCH (d)-[r:TREATS]->(dis:Disease)
RETURN d, r, dis;


// ========================================================================
// 10. CUSTOM ANALYSIS TEMPLATES
// ========================================================================

// 10.1 Template: Find repurposing candidates for YOUR disease
// Replace 'YOUR_DISEASE' with target disease
MATCH (d:Drug)-[r:TREATS]->(dis:Disease {name: 'YOUR_DISEASE'})
RETURN d.name as drug_candidate,
       r.confidence as confidence,
       r.num_papers as evidence_strength,
       r.evidence_text as rationale
ORDER BY r.confidence DESC, r.num_papers DESC;

// 10.2 Template: Analyze a specific drug's therapeutic potential
// Replace 'YOUR_DRUG' with target drug
MATCH (d:Drug {name: 'YOUR_DRUG'})-[r:TREATS]->(dis:Disease)
RETURN dis.name as potential_indication,
       r.confidence as confidence,
       r.num_papers as papers,
       r.evidence_text as evidence
ORDER BY r.confidence DESC;

// ========================================================================
// END OF QUERY EXAMPLES
// ========================================================================
//
// For more Neo4j/Cypher resources:
// - Neo4j Browser Guide: http://localhost:7474/browser/
// - Cypher Manual: https://neo4j.com/docs/cypher-manual/
// - Graph Algorithms: https://neo4j.com/docs/graph-data-science/
//
// ========================================================================
