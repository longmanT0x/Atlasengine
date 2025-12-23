"""
Extraction Storage Module

Handles storing extracted facts in SQLite database.

Design Decisions:
- Each extracted fact is stored with full source traceability
- Facts are marked as inferred if no numeric data found
- Context sentences are preserved for verification
"""

from typing import Optional, Dict, Any, List
import uuid
import sqlite3
from datetime import datetime
from app.storage.database import get_db_connection
from app.evidence.ledger import store_claim
from app.research.storage import get_source_by_url


def store_extracted_fact(
    fact_type: str,
    value: Any,
    unit: Optional[str],
    context_sentence: str,
    source_url: str,
    is_inferred: bool = False,
    inference_reason: Optional[str] = None
) -> Optional[str]:
    """
    Store an extracted fact in the database.
    
    Args:
        fact_type: Type of fact ('market_size', 'growth_rate', 'pricing', 'competitor', 'regulatory')
        value: Extracted value (float for numeric, str for text)
        unit: Unit of measurement (if applicable)
        context_sentence: Sentence containing the extracted fact
        source_url: URL of the source document
        is_inferred: Whether the fact is inferred (no explicit numeric data)
        inference_reason: Reason for inference (if applicable)
        
    Returns:
        Fact ID if successful, None if error occurs
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        fact_id = str(uuid.uuid4())
        
        # Convert value to appropriate type
        if isinstance(value, str):
            # For non-numeric values (competitors, regulatory), store as NULL in value column
            numeric_value = None
        else:
            numeric_value = float(value) if value is not None else None
        
        cursor.execute("""
            INSERT INTO extracted_facts 
            (id, fact_type, value, unit, context_sentence, source_url, is_inferred, inference_reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fact_id,
            fact_type,
            numeric_value,
            unit,
            context_sentence,
            source_url,
            1 if is_inferred else 0,
            inference_reason,
            datetime.now(datetime.UTC)
        ))
        
        conn.commit()
        
        # Store claim in evidence ledger
        # Get source credibility score
        source = get_source_by_url(source_url)
        credibility_score = source.get('credibility_score', 'medium') if source else 'medium'
        
        # Create claim text
        if numeric_value is not None:
            claim_text = f"{fact_type}: {numeric_value} {unit or ''}".strip()
        else:
            claim_text = f"{fact_type}: {context_sentence[:100]}"
        
        # Store in ledger
        store_claim(
            claim_text=claim_text,
            claim_type='extracted_fact',
            source_url=source_url,
            excerpt=context_sentence,
            credibility_score=credibility_score,
            value=numeric_value,
            unit=unit,
            retrieved_at=datetime.now(datetime.UTC)
        )
        
        return fact_id
    except Exception as e:
        print(f"Error storing extracted fact: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_sources_for_extraction() -> List[Dict[str, Any]]:
    """
    Get all sources that need extraction.
    
    Returns:
        List of source dictionaries with id, url, title, extracted_text
    """
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
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    finally:
        conn.close()


def get_extracted_facts_by_source(source_url: str) -> List[Dict[str, Any]]:
    """
    Get all extracted facts for a specific source.
    
    Args:
        source_url: Source URL
        
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
        'context_sentence': row[4],
        'source_url': row[5],
        'is_inferred': bool(row[6]),
        'inference_reason': row[7],
        'timestamp': row[8]
    }
    
    try:
        cursor.execute("""
            SELECT id, fact_type, value, unit, context_sentence, source_url, is_inferred, inference_reason, timestamp
            FROM extracted_facts
            WHERE source_url = ?
            ORDER BY timestamp DESC
        """, (source_url,))
        return cursor.fetchall()
    finally:
        conn.close()

