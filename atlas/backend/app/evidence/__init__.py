"""
Evidence Module

Manages evidence storage and traceability throughout the decision process.

Design Decisions:
- Every factual claim must be traceable to a source
- Evidence is immutable once stored
- Supports evidence chains (evidence derived from other evidence)
- All assumptions are stored as evidence with special marking
- Confidence scoring based on source quality, agreement, freshness, and data extraction quality
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone
from app.evidence.confidence import calculate_confidence_score


class Evidence(BaseModel):
    """Represents a piece of evidence with full traceability."""
    id: str
    content: str
    source: str  # URL, document, or other source identifier
    source_type: str  # "research", "extraction", "assumption", etc.
    timestamp: datetime
    confidence: float  # 0.0 to 1.0
    assumptions: List[str]  # Any assumptions associated with this evidence
    derived_from: Optional[List[str]] = None  # IDs of parent evidence if derived


class ConfidenceScore(BaseModel):
    """Represents a confidence score with explanation."""
    score: float  # 0-100
    explanation: str  # Detailed explanation of why score is high or low
    factor_scores: Dict[str, float]  # Individual factor scores
    factor_explanations: Dict[str, List[str]]  # Explanations for each factor


def get_confidence_score() -> ConfidenceScore:
    """
    Calculate confidence score (0-100) based on evidence quality.
    
    Considers:
    - Number of independent sources
    - Agreement between sources
    - Freshness of data
    - Proportion of inferred vs extracted numeric data
    
    Returns:
        ConfidenceScore with score and detailed explanation
    """
    result = calculate_confidence_score()
    return ConfidenceScore(**result)


def store_evidence(
    content: str,
    source: str,
    source_type: str,
    confidence: float,
    assumptions: Optional[List[str]] = None,
    derived_from: Optional[List[str]] = None
) -> Evidence:
    """
    Store a piece of evidence with full traceability.
    
    Args:
        content: The evidence content
        source: Source identifier
        source_type: Type of source
        confidence: Confidence level (0.0 to 1.0)
        assumptions: Optional list of assumptions
        derived_from: Optional list of parent evidence IDs
        
    Returns:
        Stored Evidence object
    """
    import uuid
    import json
    from app.storage.database import get_db_connection
    
    evidence_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)
    
    # Serialize assumptions and derived_from as JSON
    assumptions_json = json.dumps(assumptions) if assumptions else None
    derived_from_json = json.dumps(derived_from) if derived_from else None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO evidence 
            (id, content, source, source_type, timestamp, confidence, assumptions, derived_from)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            evidence_id,
            content,
            source,
            source_type,
            timestamp,
            confidence,
            assumptions_json,
            derived_from_json
        ))
        
        conn.commit()
        
        return Evidence(
            id=evidence_id,
            content=content,
            source=source,
            source_type=source_type,
            timestamp=timestamp,
            confidence=confidence,
            assumptions=assumptions or [],
            derived_from=derived_from
        )
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Failed to store evidence: {str(e)}")
    finally:
        conn.close()


def get_evidence_chain(evidence_id: str) -> List[Evidence]:
    """
    Retrieve full evidence chain for a given evidence ID.
    
    Args:
        evidence_id: ID of the evidence
        
    Returns:
        List of Evidence objects in the chain (including parents)
    """
    import json
    from app.storage.database import get_db_connection
    
    chain = []
    visited = set()
    
    def retrieve_evidence(ev_id: str):
        """Recursively retrieve evidence and its parents."""
        if ev_id in visited:
            return  # Avoid cycles
        
        visited.add(ev_id)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, content, source, source_type, timestamp, confidence, assumptions, derived_from
                FROM evidence
                WHERE id = ?
            """, (ev_id,))
            
            row = cursor.fetchone()
            if not row:
                return
            
            # Parse JSON fields
            assumptions = json.loads(row[6]) if row[6] else []
            derived_from = json.loads(row[7]) if row[7] else None
            
            # Parse timestamp
            timestamp_str = row[4]
            if isinstance(timestamp_str, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            else:
                timestamp = timestamp_str
            
            evidence = Evidence(
                id=row[0],
                content=row[1],
                source=row[2],
                source_type=row[3],
                timestamp=timestamp,
                confidence=row[5],
                assumptions=assumptions,
                derived_from=derived_from
            )
            
            # Add to chain (add current evidence first, then parents)
            chain.append(evidence)
            
            # Recursively retrieve parent evidence
            if derived_from:
                for parent_id in derived_from:
                    retrieve_evidence(parent_id)
        finally:
            conn.close()
    
    retrieve_evidence(evidence_id)
    
    # Reverse to show chain from root to leaf
    return list(reversed(chain))
