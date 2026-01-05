# Knowledge Graph Schema
**Version**: 1.0
**Created**: December 30, 2024
**Purpose**: Drug Repurposing Knowledge Graph

---

## 📊 Schema Overview

This knowledge graph captures drug-disease relationships extracted from biomedical literature (924 PubMed abstracts, 2020-2024) for drug repurposing discovery.

### Graph Statistics
- **Nodes**: 1,514 total (718 Drugs + 796 Diseases)
- **Relationships**: 666 TREATS edges
- **Source**: PubMed abstracts via BC5CDR NER + relationship extraction
- **Evidence**: All relationships include source PMIDs and evidence text

---

## 🎨 Schema Diagram

```
┌─────────────────────────┐
│      Drug (718)         │
│  ┌──────────────────┐   │
│  │ Properties:      │   │
│  │ - id            │   │
│  │ - name          │   │
│  │ - frequency     │   │
│  │ - num_papers    │   │
│  │ - source_pmids  │   │
│  └──────────────────┘   │
└───────────┬─────────────┘
            │
            │ TREATS (666)
            │ ┌─────────────────────┐
            │ │ Properties:         │
            │ │ - confidence        │
            │ │ - evidence_text     │
            │ │ - evidence_pmids    │
            │ │ - num_papers        │
            │ │ - extraction_methods│
            │ └─────────────────────┘
            │
            ▼
┌─────────────────────────┐
│    Disease (796)        │
│  ┌──────────────────┐   │
│  │ Properties:      │   │
│  │ - id            │   │
│  │ - name          │   │
│  │ - frequency     │   │
│  │ - num_papers    │   │
│  │ - source_pmids  │   │
│  └──────────────────┘   │
└─────────────────────────┘
```

---

## 📦 Node Types

### 1. Drug (Label: `:Drug`)

**Description**: Pharmaceutical compounds extracted from literature as CHEMICAL entities

**Properties**:

| Property | Type | Description | Example | Required |
|----------|------|-------------|---------|----------|
| `id` | String | Unique entity ID | "DRUG_0016" | Yes |
| `name` | String | Drug name (lowercase, normalized) | "metformin" | Yes |
| `frequency` | Integer | Total mentions across all papers | 23 | Yes |
| `num_papers` | Integer | Number of papers mentioning drug | 16 | Yes |
| `source_pmids` | List[String] | PubMed IDs where drug appears | ["31730760", "32144994", ...] | Yes |

**Example Drug Node**:
```cypher
(:Drug {
  id: "DRUG_0016",
  name: "metformin",
  frequency: 23,
  num_papers: 16,
  source_pmids: ["31730760", "32144994", "33314257", ...]
})
```

**Constraints**:
- `id` must be unique
- `name` must be unique (post-normalization)

**Indexes**:
- Index on `id` for fast lookups
- Index on `name` for text search

---

### 2. Disease (Label: `:Disease`)

**Description**: Medical conditions extracted from literature as DISEASE entities

**Properties**:

| Property | Type | Description | Example | Required |
|----------|------|-------------|---------|----------|
| `id` | String | Unique entity ID | "DISEASE_0001" | Yes |
| `name` | String | Disease name (lowercase, normalized) | "cancer" | Yes |
| `frequency` | Integer | Total mentions across all papers | 493 | Yes |
| `num_papers` | Integer | Number of papers mentioning disease | 184 | Yes |
| `source_pmids` | List[String] | PubMed IDs where disease appears | ["31451894", "31546010", ...] | Yes |

**Example Disease Node**:
```cypher
(:Disease {
  id: "DISEASE_0001",
  name: "cancer",
  frequency: 493,
  num_papers: 184,
  source_pmids: ["31451894", "31546010", "31562955", ...]
})
```

**Constraints**:
- `id` must be unique
- `name` must be unique (post-normalization)

**Indexes**:
- Index on `id` for fast lookups
- Index on `name` for text search

---

## 🔗 Relationship Types

### 1. TREATS

**Description**: Indicates that a drug has therapeutic potential for treating a disease

**Direction**: `Drug → Disease` (always directional)

**Properties**:

| Property | Type | Description | Example | Required |
|----------|------|-------------|---------|----------|
| `confidence` | Float | Confidence score 0-1 | 0.9 | Yes |
| `evidence_text` | String | Supporting sentence from paper | "Metformin treats diabetes..." | Yes |
| `evidence_pmids` | List[String] | PubMed IDs supporting relationship | ["31730760", "34848445"] | Yes |
| `num_papers` | Integer | Number of papers supporting relationship | 3 | Yes |
| `extraction_methods` | List[String] | How relationship was extracted | ["pattern", "cooccurrence"] | Yes |

**Example Relationship**:
```cypher
(:Drug {name: "metformin"})-[:TREATS {
  confidence: 0.6,
  evidence_text: "In this article, the limitations and probability of using metformin...",
  evidence_pmids: ["31730760", "34848445", "39333445"],
  num_papers: 3,
  extraction_methods: ["cooccurrence"]
}]->(:Disease {name: "cancer"})
```

**Constraints**:
- Each (Drug, Disease) pair can have only one TREATS relationship
- Confidence must be between 0 and 1
- At least one evidence PMID required

**Confidence Levels**:
- **0.9-1.0**: High confidence (pattern-based extraction)
- **0.5-0.8**: Medium confidence (co-occurrence + multiple papers)
- **<0.5**: Low confidence (single paper co-occurrence)

**Extraction Methods**:
- `pattern`: Regex pattern matching ("Drug X treats Disease Y")
- `cooccurrence`: Drug and disease mentioned in same sentence

---

## 🔍 Indexes and Constraints

### Uniqueness Constraints

```cypher
-- Ensure Drug IDs are unique
CREATE CONSTRAINT drug_id_unique IF NOT EXISTS
FOR (d:Drug) REQUIRE d.id IS UNIQUE;

-- Ensure Disease IDs are unique
CREATE CONSTRAINT disease_id_unique IF NOT EXISTS
FOR (dis:Disease) REQUIRE dis.id IS UNIQUE;

-- Ensure Drug names are unique
CREATE CONSTRAINT drug_name_unique IF NOT EXISTS
FOR (d:Drug) REQUIRE d.name IS UNIQUE;

-- Ensure Disease names are unique
CREATE CONSTRAINT disease_name_unique IF NOT EXISTS
FOR (dis:Disease) REQUIRE dis.name IS UNIQUE;
```

### Performance Indexes

```cypher
-- Index on Drug ID for fast lookups
CREATE INDEX drug_id_index IF NOT EXISTS
FOR (d:Drug) ON (d.id);

-- Index on Disease ID for fast lookups
CREATE INDEX disease_id_index IF NOT EXISTS
FOR (dis:Disease) ON (dis.id);

-- Index on Drug name for text search
CREATE INDEX drug_name_index IF NOT EXISTS
FOR (d:Drug) ON (d.name);

-- Index on Disease name for text search
CREATE INDEX disease_name_index IF NOT EXISTS
FOR (dis:Disease) ON (dis.name);

-- Index on frequency for filtering/sorting
CREATE INDEX drug_frequency_index IF NOT EXISTS
FOR (d:Drug) ON (d.frequency);

CREATE INDEX disease_frequency_index IF NOT EXISTS
FOR (dis:Disease) ON (dis.frequency);
```

---

## 📝 Design Decisions

### 1. Why Two Node Types (Drug vs Disease)?

**Alternatives Considered**:
- Single `:Entity` node with `entity_type` property
- Separate node types

**Decision**: Separate node types (`:Drug`, `:Disease`)

**Reasoning**:
- ✅ **Type Safety**: Prevents invalid relationships (Drug→Drug, Disease→Disease)
- ✅ **Query Clarity**: `MATCH (d:Drug)-[:TREATS]->(dis:Disease)` is self-documenting
- ✅ **Performance**: Neo4j indexes by label, faster queries
- ✅ **Extensibility**: Can add drug-specific or disease-specific properties later
- ✅ **Schema Validation**: Easier to enforce constraints

### 2. Why TREATS Relationship?

**Alternatives Considered**:
- `ASSOCIATED_WITH`: Too generic
- `MENTIONED_WITH`: Doesn't imply therapeutic intent
- `TARGETS`: Better for molecular targets, not diseases
- `INDICATED_FOR`: Clinical language, less suitable for research

**Decision**: `:TREATS`

**Reasoning**:
- ✅ Clear semantic meaning (therapeutic relationship)
- ✅ Domain-appropriate for drug repurposing
- ✅ Intuitive for non-experts
- ✅ Aligns with biomedical literature terminology

### 3. Why Include Evidence Provenance?

**Decision**: Include `evidence_text` and `evidence_pmids` on all relationships

**Reasoning**:
- ✅ **Explainability**: Users can see why AI predicts a relationship
- ✅ **Trust**: Verifiable sources increase credibility
- ✅ **Validation**: Can trace back to original papers
- ✅ **Portfolio Value**: Demonstrates rigor and attention to detail
- ✅ **Debugging**: Helps identify extraction errors

### 4. Why Include Frequency Metrics?

**Decision**: Include `frequency` and `num_papers` on all nodes

**Reasoning**:
- ✅ **Ranking**: Can prioritize well-studied drugs/diseases
- ✅ **Filtering**: Remove rare mentions (potential noise)
- ✅ **GNN Training**: Can weight training by frequency
- ✅ **Insights**: Identify research trends (e.g., COVID-19 spike)

---

## 🎯 Common Query Patterns

### 1. Find Drug by Name
```cypher
MATCH (d:Drug {name: 'metformin'})
RETURN d
```

### 2. Find Diseases Treated by Drug
```cypher
MATCH (d:Drug {name: 'metformin'})-[r:TREATS]->(dis:Disease)
RETURN dis.name, r.confidence, r.num_papers
ORDER BY r.confidence DESC
```

### 3. Find Drugs for Disease
```cypher
MATCH (d:Drug)-[r:TREATS]->(dis:Disease {name: 'cancer'})
RETURN d.name, r.confidence, r.num_papers
ORDER BY r.confidence DESC
```

### 4. Find High-Confidence Relationships
```cypher
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
WHERE r.confidence >= 0.8
RETURN d.name, dis.name, r.confidence, r.evidence_text
ORDER BY r.confidence DESC
```

### 5. Find Most Versatile Drugs (treat multiple diseases)
```cypher
MATCH (d:Drug)-[:TREATS]->(dis:Disease)
WITH d, count(dis) as disease_count
WHERE disease_count >= 5
RETURN d.name, disease_count
ORDER BY disease_count DESC
LIMIT 10
```

---

## 🔄 Future Extensions (Week 4+)

### Potential New Node Types
- `:Gene` - Add gene-disease associations
- `:Protein` - Drug targets
- `:Pathway` - Biological pathways
- `:ClinicalTrial` - Link to ongoing trials

### Potential New Relationship Types
- `:TARGETS` - Drug → Gene/Protein
- `:INVOLVES` - Disease → Gene
- `:PARTICIPATES_IN` - Gene → Pathway
- `:TESTED_IN` - Drug → ClinicalTrial

### Potential Property Enhancements
- Drug: `molecular_weight`, `smiles`, `drug_class`
- Disease: `disease_class`, `icd_code`
- Relationship: `clinical_phase`, `adverse_events`

---

## 📊 Graph Characteristics

### Expected Graph Properties

| Property | Value | Notes |
|----------|-------|-------|
| **Nodes** | 1,514 | 718 drugs + 796 diseases |
| **Edges** | 666 | TREATS relationships |
| **Avg Degree** | ~0.88 | Sparse graph (typical for KGs) |
| **Max Degree** | ~20-30 | Cancer likely has most drugs |
| **Density** | ~0.06% | 666 / (718 × 796) × 100 |
| **Connected** | No | Multiple components expected |
| **Bipartite** | Yes | Two distinct node sets |

### Why is the Graph Sparse?

1. **Limited Relationships**: Only 666 out of 571,528 possible pairs (718 × 796)
2. **Extraction Limitations**: NLP only captures mentioned relationships
3. **Research Gaps**: Not all drugs tested against all diseases
4. **Normal for KGs**: Real-world knowledge graphs are sparse
5. **GNN Opportunity**: Week 4 GNN will predict missing edges!

---

## ✅ Schema Validation Checklist

- [x] All node types defined with clear descriptions
- [x] All properties documented with types and examples
- [x] All relationship types defined with direction
- [x] Constraints specified for data integrity
- [x] Indexes defined for query performance
- [x] Design decisions documented
- [x] Example queries provided
- [x] Future extensions identified

---

## 📚 References

- Neo4j Graph Data Modeling: https://neo4j.com/developer/data-modeling/
- Cypher Query Language: https://neo4j.com/docs/cypher-manual/
- BC5CDR Biomedical NER: https://github.com/allenai/scispacy
- Knowledge Graph Best Practices: https://neo4j.com/blog/knowledge-graphs/

---

*Schema Version 1.0 - December 30, 2024*
