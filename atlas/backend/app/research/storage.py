"""
Research Storage Module

Handles storing research sources in SQLite database.

Design Decisions:
- Each source is stored with full traceability
- Duplicate URLs are prevented
- Timestamps are automatically set
"""

from typing import Optional, Dict, Any
import uuid
import sqlite3
from datetime import datetime
from app.storage.database import get_db_connection


def store_source(
    url: str,
    title: str,
    extracted_text: str,
    credibility_score: str
) -> Optional[str]:
    """
    Store a research source in the database.
    
    Args:
        url: Source URL
        title: Source title
        extracted_text: Clean extracted text content
        credibility_score: Credibility score ('high', 'medium', or 'low')
        
    Returns:
        Source ID if successful, None if URL already exists or error occurs
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        source_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO sources (id, url, title, extracted_text, credibility_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (source_id, url, title, extracted_text, credibility_score, datetime.utcnow()))
        
        conn.commit()
        return source_id
    except sqlite3.IntegrityError:
        # URL already exists
        conn.rollback()
        return None
    except Exception as e:
        print(f"Error storing source: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def source_exists(url: str) -> bool:
    """
    Check if a source URL already exists in the database.
    
    Args:
        url: Source URL to check
        
    Returns:
        True if source exists, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT 1 FROM sources WHERE url = ?", (url,))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def get_source_by_url(url: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a source by URL.
    
    Args:
        url: Source URL
        
    Returns:
        Source dictionary or None if not found
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'url': row[1],
        'title': row[2],
        'extracted_text': row[3],
        'timestamp': row[4],
        'credibility_score': row[5]
    }
    
    try:
        cursor.execute("""
            SELECT id, url, title, extracted_text, timestamp, credibility_score
            FROM sources WHERE url = ?
        """, (url,))
        row = cursor.fetchone()
        return row
    finally:
        conn.close()

