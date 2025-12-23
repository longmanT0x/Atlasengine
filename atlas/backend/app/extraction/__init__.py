"""
Extraction Module

Extracts structured information from unstructured research data.

Design Decisions:
- Conservative extraction - only extracts explicit, clear statements
- Uses pattern matching (regex) rather than LLM for reliability
- All extracted facts include context sentences for verification
- Marks facts as inferred if no explicit numeric data found
- Preserves original source references for all extracted facts
"""

from typing import List, Dict, Any, Optional
from app.extraction.patterns import (
    extract_market_size,
    extract_growth_rates,
    extract_pricing,
    extract_competitors,
    extract_regulatory_mentions
)
from app.extraction.storage import (
    store_extracted_fact,
    get_sources_for_extraction,
    get_extracted_facts_by_source
)


def extract_from_source(source_text: str, source_url: str) -> Dict[str, Any]:
    """
    Extract all types of facts from a source text.
    
    Args:
        source_text: Text content from the source
        source_url: URL of the source
        
    Returns:
        Dictionary with extraction results:
        - market_size: List of extracted market size facts
        - growth_rates: List of extracted growth rate facts
        - pricing: List of extracted pricing facts
        - competitors: List of extracted competitor names
        - regulatory: List of extracted regulatory mentions
        - has_numeric_data: Boolean indicating if any numeric data was found
    """
    results = {
        'market_size': [],
        'growth_rates': [],
        'pricing': [],
        'competitors': [],
        'regulatory': [],
        'has_numeric_data': False
    }
    
    # Extract market size
    market_sizes = extract_market_size(source_text)
    for fact in market_sizes:
        fact_id = store_extracted_fact(
            fact_type='market_size',
            value=fact['value'],
            unit=fact['unit'],
            context_sentence=fact['context'],
            source_url=source_url,
            is_inferred=False
        )
        if fact_id:
            results['market_size'].append(fact_id)
            results['has_numeric_data'] = True
    
    # Extract growth rates
    growth_rates = extract_growth_rates(source_text)
    for fact in growth_rates:
        fact_id = store_extracted_fact(
            fact_type='growth_rate',
            value=fact['value'],
            unit=fact['unit'],
            context_sentence=fact['context'],
            source_url=source_url,
            is_inferred=False
        )
        if fact_id:
            results['growth_rates'].append(fact_id)
            results['has_numeric_data'] = True
    
    # Extract pricing
    pricing = extract_pricing(source_text)
    for fact in pricing:
        fact_id = store_extracted_fact(
            fact_type='pricing',
            value=fact['value'],
            unit=fact['unit'],
            context_sentence=fact['context'],
            source_url=source_url,
            is_inferred=False
        )
        if fact_id:
            results['pricing'].append(fact_id)
            results['has_numeric_data'] = True
    
    # Extract competitors
    competitors = extract_competitors(source_text)
    for fact in competitors:
        fact_id = store_extracted_fact(
            fact_type='competitor',
            value=fact['value'],
            unit=fact['unit'],
            context_sentence=fact['context'],
            source_url=source_url,
            is_inferred=False
        )
        if fact_id:
            results['competitors'].append(fact_id)
    
    # Extract regulatory mentions
    regulatory = extract_regulatory_mentions(source_text)
    for fact in regulatory:
        fact_id = store_extracted_fact(
            fact_type='regulatory',
            value=fact['value'],
            unit=fact['unit'],
            context_sentence=fact['context'],
            source_url=source_url,
            is_inferred=False
        )
        if fact_id:
            results['regulatory'].append(fact_id)
    
    # If no numeric data found, store an inferred fact explaining why
    if not results['has_numeric_data']:
        inference_reason = (
            "No explicit numeric data (market size, growth rates, or pricing) "
            "found in source text. Extraction patterns require explicit keywords "
            "and numeric values to ensure accuracy."
        )
        fact_id = store_extracted_fact(
            fact_type='market_size',  # Use market_size as default for inferred
            value=None,
            unit=None,
            context_sentence="No numeric market data found in source.",
            source_url=source_url,
            is_inferred=True,
            inference_reason=inference_reason
        )
        if fact_id:
            results['market_size'].append(fact_id)
    
    return results


async def extract_from_all_sources() -> Dict[str, Any]:
    """
    Extract facts from all stored sources.
    
    Returns:
        Dictionary with summary of extraction results
    """
    sources = get_sources_for_extraction()
    
    if not sources:
        return {
            'sources_processed': 0,
            'total_facts_extracted': 0,
            'message': 'No sources found for extraction.'
        }
    
    total_facts = 0
    sources_with_data = 0
    sources_without_data = 0
    
    for source in sources:
        results = extract_from_source(
            source['extracted_text'],
            source['url']
        )
        
        facts_count = (
            len(results['market_size']) +
            len(results['growth_rates']) +
            len(results['pricing']) +
            len(results['competitors']) +
            len(results['regulatory'])
        )
        total_facts += facts_count
        
        if results['has_numeric_data']:
            sources_with_data += 1
        else:
            sources_without_data += 1
    
    return {
        'sources_processed': len(sources),
        'total_facts_extracted': total_facts,
        'sources_with_numeric_data': sources_with_data,
        'sources_without_numeric_data': sources_without_data,
        'message': f'Processed {len(sources)} sources, extracted {total_facts} facts.'
    }


async def extract_from_source_ids(source_ids: List[str]) -> Dict[str, Any]:
    """
    Extract facts from specific sources by their IDs.
    
    Args:
        source_ids: List of source IDs to process
        
    Returns:
        Dictionary with extraction results per source
    """
    from app.storage.database import get_db_connection
    
    results = {}
    
    for source_id in source_ids:
        # Get source from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.row_factory = lambda cursor, row: {
            'id': row[0],
            'url': row[1],
            'title': row[2],
            'extracted_text': row[3]
        }
        
        try:
            cursor.execute("""
                SELECT id, url, title, extracted_text
                FROM sources
                WHERE id = ?
            """, (source_id,))
            source = cursor.fetchone()
            
            if source:
                extraction_results = extract_from_source(
                    source['extracted_text'],
                    source['url']
                )
                results[source_id] = extraction_results
        finally:
            conn.close()
    
    return results
