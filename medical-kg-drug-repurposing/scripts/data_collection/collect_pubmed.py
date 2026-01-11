#!/usr/bin/env python3
"""
Collect PubMed abstracts for drug repurposing research.

This script uses the PubMed E-utilities API (free, no account needed!)
to collect research paper abstracts.

Usage:
    python collect_pubmed.py --query "drug repurposing" --max 1000
"""

import argparse
import json
import time
from pathlib import Path
import requests
from tqdm import tqdm

# PubMed E-utilities base URL
PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def search_pubmed(query, max_results=1000):
    """
    Search PubMed for papers matching the query.

    Returns list of PubMed IDs (PMIDs).
    """
    print(f"🔍 Searching PubMed for: '{query}'")
    print(f"   Requesting up to {max_results} papers...")

    search_url = f"{PUBMED_BASE}esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
        # Recent papers (2020-2024) - more relevant for drug repurposing
        "mindate": "2020/01/01",
        "maxdate": "2024/12/31",
        "datetype": "pdat"
    }

    response = requests.get(search_url, params=params)
    response.raise_for_status()

    data = response.json()
    pmids = data.get("esearchresult", {}).get("idlist", [])

    print(f"✅ Found {len(pmids)} papers")
    return pmids


def fetch_abstracts(pmids, batch_size=200):
    """
    Fetch abstracts for a list of PubMed IDs.

    PubMed API allows fetching in batches for efficiency.
    """
    print(f"\n📥 Fetching abstracts for {len(pmids)} papers...")
    print(f"   (This will take ~{len(pmids) // batch_size + 1} requests)")

    fetch_url = f"{PUBMED_BASE}efetch.fcgi"
    all_papers = []

    # Process in batches to respect API limits
    for i in tqdm(range(0, len(pmids), batch_size), desc="Fetching batches"):
        batch_pmids = pmids[i:i + batch_size]

        params = {
            "db": "pubmed",
            "id": ",".join(batch_pmids),
            "retmode": "xml",
            "rettype": "abstract"
        }

        # Be nice to NCBI servers - rate limit
        time.sleep(0.4)  # ~2.5 requests per second (well under 3/sec limit)

        try:
            response = requests.get(fetch_url, params=params)
            response.raise_for_status()

            # Parse XML response (simple approach - just extract text)
            papers = parse_pubmed_xml(response.text, batch_pmids)
            all_papers.extend(papers)

        except Exception as e:
            print(f"⚠️  Error fetching batch {i//batch_size + 1}: {e}")
            continue

    print(f"\n✅ Successfully fetched {len(all_papers)} abstracts")
    return all_papers


def parse_pubmed_xml(xml_text, pmids):
    """
    Parse PubMed XML response to extract paper information.

    Note: This is a simplified parser. For production, use BioPython.
    """
    import xml.etree.ElementTree as ET

    papers = []

    try:
        root = ET.fromstring(xml_text)

        for article in root.findall('.//PubmedArticle'):
            try:
                # PMID
                pmid_elem = article.find('.//PMID')
                pmid = pmid_elem.text if pmid_elem is not None else ""

                # Title
                title_elem = article.find('.//ArticleTitle')
                title = title_elem.text if title_elem is not None else ""

                # Abstract
                abstract_elem = article.find('.//AbstractText')
                abstract = abstract_elem.text if abstract_elem is not None else ""

                # Publication date
                year_elem = article.find('.//PubDate/Year')
                year = year_elem.text if year_elem is not None else ""

                # Journal
                journal_elem = article.find('.//Journal/Title')
                journal = journal_elem.text if journal_elem is not None else ""

                # Authors
                authors = []
                for author in article.findall('.//Author'):
                    lastname = author.find('.//LastName')
                    forename = author.find('.//ForeName')
                    if lastname is not None and forename is not None:
                        authors.append(f"{forename.text} {lastname.text}")

                # Only keep papers with abstracts
                if abstract:
                    papers.append({
                        "pmid": pmid,
                        "title": title,
                        "abstract": abstract,
                        "year": year,
                        "journal": journal,
                        "authors": authors[:3]  # First 3 authors
                    })

            except Exception as e:
                continue

    except Exception as e:
        print(f"⚠️  Error parsing XML: {e}")

    return papers


def main():
    parser = argparse.ArgumentParser(
        description='Collect PubMed abstracts for drug repurposing'
    )
    parser.add_argument(
        '--query', '-q',
        default='drug repurposing',
        help='Search query (default: "drug repurposing")'
    )
    parser.add_argument(
        '--max', '-m',
        type=int,
        default=1000,
        help='Maximum number of papers (default: 1000)'
    )
    parser.add_argument(
        '--output', '-o',
        default='data/raw/pubmed_abstracts.json',
        help='Output JSON file'
    )

    args = parser.parse_args()

    # Search PubMed
    pmids = search_pubmed(args.query, args.max)

    if not pmids:
        print("❌ No papers found. Try a different query.")
        return

    # Fetch abstracts
    papers = fetch_abstracts(pmids)

    if not papers:
        print("❌ No abstracts fetched. Something went wrong.")
        return

    # Save to JSON
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved {len(papers)} papers to: {output_file}")

    # Show sample
    print("\n📄 Sample paper:")
    if papers:
        sample = papers[0]
        print(f"   Title: {sample['title'][:80]}...")
        print(f"   Year: {sample['year']}")
        print(f"   Journal: {sample['journal'][:50]}")
        print(f"   Abstract: {sample['abstract'][:150]}...")

    # Statistics
    print(f"\n📊 Statistics:")
    years = [p.get('year', '') for p in papers if p.get('year')]
    if years:
        from collections import Counter
        year_counts = Counter(years).most_common(5)
        print("   Papers by year (top 5):")
        for year, count in year_counts:
            print(f"      {year}: {count} papers")


if __name__ == "__main__":
    main()
