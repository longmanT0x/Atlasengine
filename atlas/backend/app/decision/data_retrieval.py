from __future__ import annotations
"""
Data Retrieval Module for Decision Analysis

Retrieves extracted facts needed for competitor and risk analysis.
"""

from typing import Dict, List, Any
from app.storage.database import get_db_connection


def get_competitor_facts() -> List[Dict[str, Any]]:
    """
    Get all competitor facts from extracted data.
    
    Returns:
        List of competitor fact dictionaries with context sentences
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'value': row[1],  # Competitor name
        'context_sentence': row[2],
        'source_url': row[3]
    }
    
    try:
        cursor.execute("""
            SELECT id, value, context_sentence, source_url
            FROM extracted_facts
            WHERE fact_type = 'competitor'
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    finally:
        conn.close()


def get_regulatory_facts() -> List[Dict[str, Any]]:
    """
    Get all regulatory facts from extracted data.
    
    Returns:
        List of regulatory fact dictionaries with context sentences
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'value': row[1],  # Regulatory mention
        'context_sentence': row[2],
        'source_url': row[3]
    }
    
    try:
        cursor.execute("""
            SELECT id, value, context_sentence, source_url
            FROM extracted_facts
            WHERE fact_type = 'regulatory'
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    finally:
        conn.close()


def get_market_size_facts() -> List[Dict[str, Any]]:
    """
    Get market size facts for market risk analysis.
    
    Returns:
        List of market size fact dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'value': row[1],
        'unit': row[2],
        'context_sentence': row[3],
        'source_url': row[4]
    }
    
    try:
        cursor.execute("""
            SELECT id, value, unit, context_sentence, source_url
            FROM extracted_facts
            WHERE fact_type = 'market_size' AND is_inferred = 0
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    finally:
        conn.close()


def get_growth_rate_facts() -> List[Dict[str, Any]]:
    """
    Get growth rate facts for market risk analysis.
    
    Returns:
        List of growth rate fact dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'value': row[1],
        'context_sentence': row[2],
        'source_url': row[3]
    }
    
    try:
        cursor.execute("""
            SELECT id, value, context_sentence, source_url
            FROM extracted_facts
            WHERE fact_type = 'growth_rate' AND is_inferred = 0
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    finally:
        conn.close()


def get_pricing_facts() -> List[Dict[str, Any]]:
    """
    Get pricing facts for distribution risk analysis.
    
    Returns:
        List of pricing fact dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: {
        'id': row[0],
        'value': row[1],
        'unit': row[2],
        'context_sentence': row[3],
        'source_url': row[4]
    }
    
    try:
        cursor.execute("""
            SELECT id, value, unit, context_sentence, source_url
            FROM extracted_facts
            WHERE fact_type = 'pricing' AND is_inferred = 0
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()
    finally:
        conn.close()

