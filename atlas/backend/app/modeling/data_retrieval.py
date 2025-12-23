"""
Data Retrieval Module

Retrieves extracted facts from database for modeling.

Design Decisions:
- Separates data retrieval from modeling logic
- Filters out inferred facts for numeric calculations
- Groups facts by type for easy access
"""

from typing import Dict, List, Any
from app.storage.database import get_db_connection
from app.evidence.ledger import has_low_credibility_claims, get_claims_by_type


def get_extracted_facts() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all extracted facts grouped by type.
    
    Returns:
        Dictionary with keys: market_size, growth_rate, pricing, competitor, regulatory
        Each value is a list of fact dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'fact_type': row[1],
        'value': row[2],
        'unit': row[3],
        'context_sentence': row[4],
        'source_url': row[5],
        'is_inferred': bool(row[6]),
        'inference_reason': row[7]
    }
    
    try:
        cursor.execute("""
            SELECT id, fact_type, value, unit, context_sentence, source_url, is_inferred, inference_reason
            FROM extracted_facts
            WHERE is_inferred = 0
            ORDER BY fact_type, timestamp DESC
        """)
        all_facts = cursor.fetchall()
        
        # Group by fact type
        grouped = {
            'market_size': [],
            'growth_rate': [],
            'pricing': [],
            'competitor': [],
            'regulatory': []
        }
        
        for fact in all_facts:
            fact_type = fact['fact_type']
            if fact_type in grouped:
                grouped[fact_type].append(fact)
        
        return grouped
    finally:
        conn.close()


def get_market_size_facts() -> List[Dict[str, Any]]:
    """Get only market size facts."""
    facts = get_extracted_facts()
    return facts.get('market_size', [])


def get_pricing_facts() -> List[Dict[str, Any]]:
    """Get only pricing facts."""
    facts = get_extracted_facts()
    return facts.get('pricing', [])


def assess_data_quality(facts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Assess the quality of extracted facts.
    
    Checks for low credibility sources and adjusts quality score accordingly.
    If low credibility claims exist, quality is automatically lowered and ranges should be widened.
    
    Args:
        facts: List of extracted facts
        
    Returns:
        Dictionary with quality metrics:
        - count: Number of facts
        - has_numeric_data: Boolean
        - unit_consistency: Boolean (if all units match)
        - source_diversity: Number of unique sources
        - quality_score: 'high', 'medium', or 'low'
        - has_low_credibility: Boolean indicating if low credibility sources exist
        - should_widen_ranges: Boolean indicating if ranges should be widened
    """
    if not facts:
        return {
            'count': 0,
            'has_numeric_data': False,
            'unit_consistency': False,
            'source_diversity': 0,
            'quality_score': 'low',
            'has_low_credibility': False,
            'should_widen_ranges': False
        }
    
    # Count facts with numeric values
    numeric_facts = [f for f in facts if f.get('value') is not None]
    
    # Check unit consistency
    units = set(f.get('unit') for f in numeric_facts if f.get('unit'))
    unit_consistent = len(units) <= 1
    
    # Count unique sources
    sources = set(f.get('source_url') for f in facts)
    source_diversity = len(sources)
    
    # Check for low credibility claims
    has_low_cred = has_low_credibility_claims()
    
    # Calculate quality score
    quality_score = 'low'
    if len(numeric_facts) >= 3 and source_diversity >= 2 and unit_consistent and not has_low_cred:
        quality_score = 'high'
    elif len(numeric_facts) >= 1 and source_diversity >= 1:
        quality_score = 'medium'
    
    # If low credibility sources exist, downgrade quality and flag for range widening
    if has_low_cred:
        if quality_score == 'high':
            quality_score = 'medium'
        elif quality_score == 'medium':
            quality_score = 'low'
    
    return {
        'count': len(facts),
        'has_numeric_data': len(numeric_facts) > 0,
        'unit_consistency': unit_consistent,
        'source_diversity': source_diversity,
        'quality_score': quality_score,
        'has_low_credibility': has_low_cred,
        'should_widen_ranges': has_low_cred
    }

