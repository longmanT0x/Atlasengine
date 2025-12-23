"""
Research Module

Handles market research data collection from external sources.

Design Decisions:
- All research must be traceable to a source
- No invented numbers - only real data from sources
- Uses DuckDuckGo search (no API key required)
- Prioritizes government, academic, and industry sources
- Stores sources in SQLite with full traceability
- Does NOT summarize or analyze - only collects and persists evidence
"""

from typing import Optional, Dict, Any, List
from app.research.query_expansion import expand_idea_into_queries
from app.research.search import search_multiple_queries
from app.research.source_prioritization import prioritize_sources, filter_high_quality_sources
from app.research.text_extraction import extract_clean_text
from app.research.storage import store_source, source_exists
from app.evidence.ledger import store_claim
from datetime import datetime


async def research_market(
    idea: str,
    industry: str,
    geography: str,
    customer_type: str
) -> Dict[str, Any]:
    """
    Research market data for a startup idea.
    
    This function:
    1. Expands the idea into multiple search queries
    2. Searches DuckDuckGo for sources
    3. Prioritizes high-quality sources (government, academic, industry)
    4. Extracts clean text from each source
    5. Stores sources in SQLite database
    
    Args:
        idea: Startup idea description
        industry: Industry classification
        geography: Target geography
        customer_type: Type of target customers
        
    Returns:
        Dictionary containing:
        - sources_found: Number of sources found and stored
        - source_ids: List of stored source IDs
        - queries_used: List of search queries executed
        
    Raises:
        ValueError: If no valid sources found
    """
    # Step 1: Expand idea into multiple queries
    queries = expand_idea_into_queries(idea, industry, geography, customer_type)
    
    # Step 2: Search for sources
    search_results = search_multiple_queries(queries, max_results_per_query=10)
    
    if not search_results:
        raise ValueError("No search results found. Try different search terms.")
    
    # Step 3: Prioritize sources
    prioritized_sources = prioritize_sources(search_results)
    
    # Step 4: Filter to high-quality sources (5-8 sources)
    high_quality_sources = filter_high_quality_sources(
        prioritized_sources,
        min_credibility='medium',
        max_results=8
    )
    
    if not high_quality_sources:
        raise ValueError("No high-quality sources found after filtering.")
    
    # Step 5: Extract text and store sources
    stored_source_ids = []
    sources_stored = 0
    
    for source in high_quality_sources:
        url = source.get('url', '')
        title = source.get('title', '')
        credibility = source.get('credibility', 'medium')
        
        # Skip if already stored
        if source_exists(url):
            continue
        
        # Extract clean text
        extracted_text = await extract_clean_text(url)
        
        if not extracted_text:
            # If text extraction fails, use snippet as fallback
            extracted_text = source.get('snippet', 'Text extraction failed.')
        
        # Store source
        source_id = store_source(url, title, extracted_text, credibility)
        
        if source_id:
            stored_source_ids.append(source_id)
            sources_stored += 1
            
            # Store claim in evidence ledger
            # Use first 500 chars as excerpt
            excerpt = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
            claim_text = f"Source: {title}"
            store_claim(
                claim_text=claim_text,
                claim_type='source',
                source_url=url,
                excerpt=excerpt,
                credibility_score=credibility,
                retrieved_at=datetime.utcnow()
            )
        
        # Stop if we have enough sources
        if sources_stored >= 8:
            break
    
    if sources_stored == 0:
        raise ValueError("Failed to store any sources. All sources may already exist or extraction failed.")
    
    return {
        "sources_found": sources_stored,
        "source_ids": stored_source_ids,
        "queries_used": queries,
        "message": f"Successfully collected and stored {sources_stored} research sources."
    }

