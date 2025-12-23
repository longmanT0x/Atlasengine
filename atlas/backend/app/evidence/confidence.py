"""
Confidence Scoring Module

Calculates confidence scores (0-100) based on multiple evidence quality factors.

Design Decisions:
- Considers number of independent sources
- Evaluates agreement between sources
- Assesses data freshness
- Accounts for proportion of inferred vs extracted data
- Provides detailed explanations for scores
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta, timezone
from app.storage.database import get_db_connection


def get_all_sources() -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'url': row[1],
        'timestamp': row[2],
        'credibility_score': row[3]
    }
    
    try:
        cursor.execute("""
            SELECT id, url, timestamp, credibility_score
            FROM sources
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    finally:
        conn.close()


def get_all_extracted_facts() -> List[Dict[str, Any]]:
    """
    Get all extracted facts from the database.
    
    Returns:
        List of extracted fact dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'fact_type': row[1],
        'value': row[2],
        'unit': row[3],
        'source_url': row[4],
        'is_inferred': bool(row[5]),
        'timestamp': row[6]
    }
    
    try:
        cursor.execute("""
            SELECT id, fact_type, value, unit, source_url, is_inferred, timestamp
            FROM extracted_facts
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    finally:
        conn.close()


def score_source_count(sources: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    """
    Score based on number of independent sources.
    
    Args:
        sources: List of source dictionaries
        
    Returns:
        Tuple of (score 0-100, explanation notes)
    """
    num_sources = len(sources)
    notes = []
    
    if num_sources == 0:
        score = 0.0
        notes.append("No sources found - cannot assess confidence")
    elif num_sources == 1:
        score = 30.0
        notes.append(f"Only 1 source - single point of failure risk")
    elif num_sources == 2:
        score = 50.0
        notes.append(f"2 sources - limited validation")
    elif num_sources == 3:
        score = 65.0
        notes.append(f"3 sources - moderate validation")
    elif num_sources >= 4 and num_sources < 8:
        score = 80.0
        notes.append(f"{num_sources} sources - good source diversity")
    else:  # 8+
        score = 95.0
        notes.append(f"{num_sources} sources - excellent source diversity")
    
    return min(100.0, max(0.0, score)), notes


def score_source_agreement(facts: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    """
    Score based on agreement between sources for numeric facts.
    
    Args:
        facts: List of extracted fact dictionaries
        
    Returns:
        Tuple of (score 0-100, explanation notes)
    """
    notes = []
    
    # Group numeric facts by type and unit
    numeric_facts = [f for f in facts if f.get('value') is not None and not f.get('is_inferred', False)]
    
    if len(numeric_facts) < 2:
        score = 50.0
        notes.append("Insufficient numeric data for agreement assessment (< 2 facts)")
        return score, notes
    
    # Group by fact_type and unit
    grouped_facts = defaultdict(list)
    for fact in numeric_facts:
        fact_type = fact.get('fact_type', '')
        unit = fact.get('unit', '')
        key = f"{fact_type}_{unit}"
        grouped_facts[key].append(fact)
    
    # Calculate agreement for each group
    agreement_scores = []
    for key, group_facts in grouped_facts.items():
        if len(group_facts) < 2:
            continue
        
        values = [f.get('value') for f in group_facts if f.get('value') is not None]
        if len(values) < 2:
            continue
        
        # Calculate coefficient of variation (CV) = std_dev / mean
        mean_val = statistics.mean(values)
        if mean_val == 0:
            continue
        
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        cv = std_dev / abs(mean_val) if mean_val != 0 else 1.0
        
        # Lower CV = better agreement
        # CV < 0.1 = excellent agreement (score 100)
        # CV < 0.2 = good agreement (score 80)
        # CV < 0.5 = moderate agreement (score 60)
        # CV >= 0.5 = poor agreement (score 40)
        if cv < 0.1:
            agreement_scores.append(100.0)
        elif cv < 0.2:
            agreement_scores.append(80.0)
        elif cv < 0.5:
            agreement_scores.append(60.0)
        else:
            agreement_scores.append(40.0)
    
    if not agreement_scores:
        score = 50.0
        notes.append("Cannot assess agreement - insufficient comparable numeric data")
    else:
        score = statistics.mean(agreement_scores)
        num_groups = len(agreement_scores)
        notes.append(f"Agreement assessed across {num_groups} fact type(s) - average agreement score: {score:.1f}/100")
        
        # Add specific notes about agreement quality
        if score >= 80:
            notes.append("High agreement between sources - values are consistent")
        elif score >= 60:
            notes.append("Moderate agreement between sources - some variation present")
        else:
            notes.append("Low agreement between sources - significant variation in values")
    
    return min(100.0, max(0.0, score)), notes


def score_data_freshness(sources: List[Dict[str, Any]], facts: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    """
    Score based on freshness of data (how recent are the sources).
    
    Args:
        sources: List of source dictionaries with timestamps
        facts: List of extracted fact dictionaries with timestamps
        
    Returns:
        Tuple of (score 0-100, explanation notes)
    """
    notes = []
    now = datetime.now(timezone.utc)
    
    # Get most recent source timestamp
    source_timestamps = []
    for source in sources:
        timestamp_str = source.get('timestamp')
        if timestamp_str:
            try:
                if isinstance(timestamp_str, str):
                    # Try ISO format first
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        # Try SQLite datetime format
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                else:
                    timestamp = timestamp_str
                
                # Ensure timestamp is timezone-aware
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                
                source_timestamps.append(timestamp)
            except Exception:
                pass
    
    # Get most recent fact timestamp
    fact_timestamps = []
    for fact in facts:
        timestamp_str = fact.get('timestamp')
        if timestamp_str:
            try:
                if isinstance(timestamp_str, str):
                    # Try ISO format first
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        # Try SQLite datetime format
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                else:
                    timestamp = timestamp_str
                
                # Ensure timestamp is timezone-aware
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                
                fact_timestamps.append(timestamp)
            except Exception:
                pass
    
    all_timestamps = source_timestamps + fact_timestamps
    
    if not all_timestamps:
        score = 30.0
        notes.append("Cannot assess freshness - no timestamps available")
        return score, notes
    
    # Get most recent timestamp
    most_recent = max(all_timestamps)
    age_days = (now - most_recent).days
    
    # Score based on age
    if age_days <= 30:
        score = 95.0
        notes.append(f"Very fresh data - most recent source is {age_days} day(s) old")
    elif age_days <= 90:
        score = 80.0
        notes.append(f"Recent data - most recent source is {age_days} day(s) old")
    elif age_days <= 180:
        score = 65.0
        notes.append(f"Moderately fresh data - most recent source is {age_days} day(s) old")
    elif age_days <= 365:
        score = 50.0
        notes.append(f"Somewhat dated data - most recent source is {age_days} day(s) old")
    elif age_days <= 730:
        score = 35.0
        notes.append(f"Dated data - most recent source is {age_days} day(s) old")
    else:
        score = 20.0
        notes.append(f"Very dated data - most recent source is {age_days} day(s) old")
    
    # Also check average age
    if all_timestamps:
        avg_age_days = sum((now - ts).days for ts in all_timestamps) / len(all_timestamps)
        if avg_age_days > 365:
            score *= 0.8  # Reduce score if average is old
            notes.append(f"Average data age is {avg_age_days:.0f} days - some sources may be outdated")
    
    return min(100.0, max(0.0, score)), notes


def score_inferred_proportion(facts: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    """
    Score based on proportion of inferred vs extracted numeric data.
    
    Args:
        facts: List of extracted fact dictionaries
        
    Returns:
        Tuple of (score 0-100, explanation notes)
    """
    notes = []
    
    if not facts:
        score = 0.0
        notes.append("No facts available - cannot assess data quality")
        return score, notes
    
    # Count inferred vs extracted
    total_facts = len(facts)
    inferred_count = sum(1 for f in facts if f.get('is_inferred', False))
    extracted_count = total_facts - inferred_count
    
    # Count numeric facts specifically
    numeric_facts = [f for f in facts if f.get('value') is not None]
    numeric_inferred = sum(1 for f in numeric_facts if f.get('is_inferred', False))
    numeric_extracted = len(numeric_facts) - numeric_inferred
    
    if total_facts == 0:
        score = 0.0
        notes.append("No facts found")
    elif numeric_facts == 0:
        score = 30.0
        notes.append("No numeric facts found - all data is non-numeric")
    else:
        inferred_proportion = numeric_inferred / len(numeric_facts) if numeric_facts else 1.0
        
        # Score inversely related to inferred proportion
        # 0% inferred = 100 score
        # 100% inferred = 0 score
        score = (1.0 - inferred_proportion) * 100.0
        
        if inferred_proportion == 0:
            notes.append(f"All {len(numeric_facts)} numeric fact(s) are extracted (0% inferred) - high data quality")
        elif inferred_proportion < 0.1:
            notes.append(f"Low inferred proportion ({inferred_proportion*100:.1f}%) - {numeric_extracted} extracted, {numeric_inferred} inferred")
        elif inferred_proportion < 0.3:
            notes.append(f"Moderate inferred proportion ({inferred_proportion*100:.1f}%) - {numeric_extracted} extracted, {numeric_inferred} inferred")
        else:
            notes.append(f"High inferred proportion ({inferred_proportion*100:.1f}%) - {numeric_extracted} extracted, {numeric_inferred} inferred - data quality concerns")
    
    return min(100.0, max(0.0, score)), notes


def calculate_confidence_score() -> Dict[str, Any]:
    """
    Calculate overall confidence score (0-100) based on all factors.
    
    Returns:
        Dictionary with:
        - score: Overall confidence score (0-100)
        - explanation: Detailed explanation of why score is high or low
        - factor_scores: Individual factor scores
        - factor_explanations: Explanations for each factor
    """
    # Get data
    sources = get_all_sources()
    facts = get_all_extracted_facts()
    
    # Score each factor
    source_count_score, source_count_notes = score_source_count(sources)
    agreement_score, agreement_notes = score_source_agreement(facts)
    freshness_score, freshness_notes = score_data_freshness(sources, facts)
    inferred_score, inferred_notes = score_inferred_proportion(facts)
    
    # Calculate weighted overall score
    # Source count and agreement are most important
    weights = {
        'source_count': 0.30,
        'agreement': 0.30,
        'freshness': 0.20,
        'inferred': 0.20
    }
    
    overall_score = (
        source_count_score * weights['source_count'] +
        agreement_score * weights['agreement'] +
        freshness_score * weights['freshness'] +
        inferred_score * weights['inferred']
    )
    
    # Generate explanation
    explanation_parts = []
    
    # Overall assessment
    if overall_score >= 80:
        explanation_parts.append(f"High confidence score ({overall_score:.1f}/100) - evidence quality is strong.")
    elif overall_score >= 60:
        explanation_parts.append(f"Moderate confidence score ({overall_score:.1f}/100) - evidence quality is acceptable with some concerns.")
    elif overall_score >= 40:
        explanation_parts.append(f"Low confidence score ({overall_score:.1f}/100) - evidence quality has significant concerns.")
    else:
        explanation_parts.append(f"Very low confidence score ({overall_score:.1f}/100) - evidence quality is poor.")
    
    # Factor-by-factor explanation
    explanation_parts.append("\nFactor breakdown:")
    explanation_parts.append(f"  • Source count ({source_count_score:.1f}/100): {'; '.join(source_count_notes)}")
    explanation_parts.append(f"  • Source agreement ({agreement_score:.1f}/100): {'; '.join(agreement_notes)}")
    explanation_parts.append(f"  • Data freshness ({freshness_score:.1f}/100): {'; '.join(freshness_notes)}")
    explanation_parts.append(f"  • Inferred data proportion ({inferred_score:.1f}/100): {'; '.join(inferred_notes)}")
    
    # Key strengths and weaknesses
    strengths = []
    weaknesses = []
    
    if source_count_score >= 70:
        strengths.append("good source diversity")
    elif source_count_score < 50:
        weaknesses.append("limited source count")
    
    if agreement_score >= 70:
        strengths.append("high agreement between sources")
    elif agreement_score < 50:
        weaknesses.append("low agreement between sources")
    
    if freshness_score >= 70:
        strengths.append("recent data")
    elif freshness_score < 50:
        weaknesses.append("dated data")
    
    if inferred_score >= 70:
        strengths.append("mostly extracted (not inferred) data")
    elif inferred_score < 50:
        weaknesses.append("high proportion of inferred data")
    
    if strengths:
        explanation_parts.append(f"\nKey strengths: {', '.join(strengths)}")
    if weaknesses:
        explanation_parts.append(f"Key weaknesses: {', '.join(weaknesses)}")
    
    explanation = "\n".join(explanation_parts)
    
    return {
        'score': round(overall_score, 1),
        'explanation': explanation,
        'factor_scores': {
            'source_count': round(source_count_score, 1),
            'agreement': round(agreement_score, 1),
            'freshness': round(freshness_score, 1),
            'inferred': round(inferred_score, 1)
        },
        'factor_explanations': {
            'source_count': source_count_notes,
            'agreement': agreement_notes,
            'freshness': freshness_notes,
            'inferred': inferred_notes
        }
    }

