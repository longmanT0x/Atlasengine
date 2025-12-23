"""
Evidence Ledger Module

Manages the evidence ledger system that tracks all claims with full traceability.

Design Decisions:
- Every claim is stored with source URL, excerpt, and credibility score
- Claim IDs are used internally for traceability
- Low credibility sources automatically lower claim confidence and widen ranges
- Claims can be retrieved by type, source, or credibility level
"""

from typing import Optional, Dict, Any, List
import uuid
import sqlite3
from datetime import datetime
from app.storage.database import get_db_connection


def store_claim(
    claim_text: str,
    claim_type: str,
    source_url: str,
    excerpt: str,
    credibility_score: str,
    value: Optional[float] = None,
    unit: Optional[str] = None,
    retrieved_at: Optional[datetime] = None
) -> Optional[str]:
    """
    Store a claim in the evidence ledger.
    
    Args:
        claim_text: The text of the claim
        claim_type: Type of claim ('market_size', 'growth_rate', 'pricing', 'competitor', 'regulatory', 'source', 'extracted_fact')
        source_url: URL of the source
        excerpt: Excerpt from source supporting the claim
        credibility_score: Credibility of the source ('high', 'medium', 'low')
        value: Optional numeric value
        unit: Optional unit of measurement
        retrieved_at: When the claim was retrieved (defaults to now)
        
    Returns:
        Claim ID if successful, None if error occurs
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        claim_id = str(uuid.uuid4())
        
        # Determine claim confidence based on credibility
        # Low credibility sources automatically get low claim confidence
        if credibility_score == 'low':
            claim_confidence = 'low'
        elif credibility_score == 'medium':
            claim_confidence = 'medium'
        else:
            claim_confidence = 'high'
        
        if retrieved_at is None:
            retrieved_at = datetime.utcnow()
        
        cursor.execute("""
            INSERT INTO evidence_ledger 
            (id, claim_text, claim_type, value, unit, source_url, excerpt, retrieved_at, credibility_score, claim_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            claim_id,
            claim_text,
            claim_type,
            value,
            unit,
            source_url,
            excerpt,
            retrieved_at,
            credibility_score,
            claim_confidence
        ))
        
        conn.commit()
        return claim_id
    except Exception as e:
        print(f"Error storing claim in evidence ledger: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_claims_by_type(claim_type: str) -> List[Dict[str, Any]]:
    """
    Get all claims of a specific type.
    
    Args:
        claim_type: Type of claim to retrieve
        
    Returns:
        List of claim dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'claim_text': row[1],
        'claim_type': row[2],
        'value': row[3],
        'unit': row[4],
        'source_url': row[5],
        'excerpt': row[6],
        'retrieved_at': row[7],
        'credibility_score': row[8],
        'claim_confidence': row[9]
    }
    
    try:
        cursor.execute("""
            SELECT id, claim_text, claim_type, value, unit, source_url, excerpt, retrieved_at, credibility_score, claim_confidence
            FROM evidence_ledger
            WHERE claim_type = ?
            ORDER BY retrieved_at DESC
        """, (claim_type,))
        return cursor.fetchall()
    finally:
        conn.close()


def get_claims_by_source(source_url: str) -> List[Dict[str, Any]]:
    """
    Get all claims from a specific source.
    
    Args:
        source_url: Source URL
        
    Returns:
        List of claim dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'claim_text': row[1],
        'claim_type': row[2],
        'value': row[3],
        'unit': row[4],
        'source_url': row[5],
        'excerpt': row[6],
        'retrieved_at': row[7],
        'credibility_score': row[8],
        'claim_confidence': row[9]
    }
    
    try:
        cursor.execute("""
            SELECT id, claim_text, claim_type, value, unit, source_url, excerpt, retrieved_at, credibility_score, claim_confidence
            FROM evidence_ledger
            WHERE source_url = ?
            ORDER BY retrieved_at DESC
        """, (source_url,))
        return cursor.fetchall()
    finally:
        conn.close()


def get_all_claims() -> List[Dict[str, Any]]:
    """
    Get all claims from the evidence ledger.
    
    Returns:
        List of all claim dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'claim_text': row[1],
        'claim_type': row[2],
        'value': row[3],
        'unit': row[4],
        'source_url': row[5],
        'excerpt': row[6],
        'retrieved_at': row[7],
        'credibility_score': row[8],
        'claim_confidence': row[9]
    }
    
    try:
        cursor.execute("""
            SELECT id, claim_text, claim_type, value, unit, source_url, excerpt, retrieved_at, credibility_score, claim_confidence
            FROM evidence_ledger
            ORDER BY retrieved_at DESC
        """)
        return cursor.fetchall()
    finally:
        conn.close()


def get_claims_by_credibility(credibility_score: str) -> List[Dict[str, Any]]:
    """
    Get all claims from sources with a specific credibility score.
    
    Args:
        credibility_score: Credibility level ('high', 'medium', 'low')
        
    Returns:
        List of claim dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'claim_text': row[1],
        'claim_type': row[2],
        'value': row[3],
        'unit': row[4],
        'source_url': row[5],
        'excerpt': row[6],
        'retrieved_at': row[7],
        'credibility_score': row[8],
        'claim_confidence': row[9]
    }
    
    try:
        cursor.execute("""
            SELECT id, claim_text, claim_type, value, unit, source_url, excerpt, retrieved_at, credibility_score, claim_confidence
            FROM evidence_ledger
            WHERE credibility_score = ?
            ORDER BY retrieved_at DESC
        """, (credibility_score,))
        return cursor.fetchall()
    finally:
        conn.close()


def get_claim_by_id(claim_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific claim by ID.
    
    Args:
        claim_id: Claim ID
        
    Returns:
        Claim dictionary or None if not found
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'claim_text': row[1],
        'claim_type': row[2],
        'value': row[3],
        'unit': row[4],
        'source_url': row[5],
        'excerpt': row[6],
        'retrieved_at': row[7],
        'credibility_score': row[8],
        'claim_confidence': row[9]
    }
    
    try:
        cursor.execute("""
            SELECT id, claim_text, claim_type, value, unit, source_url, excerpt, retrieved_at, credibility_score, claim_confidence
            FROM evidence_ledger
            WHERE id = ?
        """, (claim_id,))
        result = cursor.fetchone()
        return result
    finally:
        conn.close()


def has_low_credibility_claims(claim_type: Optional[str] = None) -> bool:
    """
    Check if there are any low credibility claims.
    
    Args:
        claim_type: Optional claim type to filter by
        
    Returns:
        True if low credibility claims exist, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if claim_type:
            cursor.execute("""
                SELECT COUNT(*) FROM evidence_ledger
                WHERE credibility_score = 'low' AND claim_type = ?
            """, (claim_type,))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM evidence_ledger
                WHERE credibility_score = 'low'
            """)
        
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        conn.close()

