"""
Database Module

Database initialization and connection management.

This module is separated from __init__.py to allow for easier testing
and potential future migration to other database backends.
"""

from typing import Optional, Dict, Any
import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "atlas.db"

def init_db():
    """
    Initialize the SQLite database with required tables.
    
    Creates tables for:
    - evidence: Stores all evidence with source traceability
    - research: Stores raw research data
    - models: Stores market models
    - decisions: Stores viability decisions
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Evidence table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            source_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            confidence REAL NOT NULL,
            assumptions TEXT,  -- JSON array
            derived_from TEXT  -- JSON array of evidence IDs
        )
    """)
    
    # Research table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research (
            id TEXT PRIMARY KEY,
            keywords TEXT NOT NULL,
            industry TEXT,
            raw_data TEXT NOT NULL,
            source TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Sources table - stores individual research sources
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            extracted_text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            credibility_score TEXT NOT NULL CHECK(credibility_score IN ('high', 'medium', 'low'))
        )
    """)
    
    # Create index on URL for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sources_url ON sources(url)
    """)
    
    # Extracted facts table - stores structured data extracted from sources
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS extracted_facts (
            id TEXT PRIMARY KEY,
            fact_type TEXT NOT NULL CHECK(fact_type IN ('market_size', 'growth_rate', 'pricing', 'competitor', 'regulatory')),
            value REAL,
            unit TEXT,
            context_sentence TEXT NOT NULL,
            source_url TEXT NOT NULL,
            is_inferred INTEGER DEFAULT 0 CHECK(is_inferred IN (0, 1)),
            inference_reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_url) REFERENCES sources(url)
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_extracted_facts_type ON extracted_facts(fact_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_extracted_facts_source ON extracted_facts(source_url)
    """)
    
    # Evidence Ledger table - stores all claims with full traceability
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_ledger (
            id TEXT PRIMARY KEY,
            claim_text TEXT NOT NULL,
            claim_type TEXT NOT NULL CHECK(claim_type IN ('market_size', 'growth_rate', 'pricing', 'competitor', 'regulatory', 'source', 'extracted_fact')),
            value REAL,
            unit TEXT,
            source_url TEXT NOT NULL,
            excerpt TEXT NOT NULL,
            retrieved_at DATETIME NOT NULL,
            credibility_score TEXT NOT NULL CHECK(credibility_score IN ('high', 'medium', 'low')),
            claim_confidence TEXT DEFAULT 'medium' CHECK(claim_confidence IN ('high', 'medium', 'low')),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_url) REFERENCES sources(url)
        )
    """)
    
    # Create indexes for evidence ledger
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_evidence_ledger_type ON evidence_ledger(claim_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_evidence_ledger_source ON evidence_ledger(source_url)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_evidence_ledger_credibility ON evidence_ledger(credibility_score)
    """)
    
    # Models table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id TEXT PRIMARY KEY,
            market_size_min REAL,
            market_size_max REAL,
            growth_rate_min REAL,
            growth_rate_max REAL,
            assumptions TEXT,  -- JSON array
            evidence_sources TEXT,  -- JSON array
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Decisions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id TEXT PRIMARY KEY,
            viability_score_min REAL NOT NULL,
            viability_score_max REAL NOT NULL,
            recommendation TEXT NOT NULL,
            confidence REAL NOT NULL,
            key_factors TEXT,  -- JSON array
            risks TEXT,  -- JSON array
            assumptions TEXT,  -- JSON array
            model_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES models(id)
        )
    """)
    
    conn.commit()
    conn.close()

def get_db_connection():
    """
    Get a database connection.
    
    Returns:
        sqlite3.Connection object
    """
    return sqlite3.connect(DB_PATH)

__all__ = ["init_db", "get_db_connection", "DB_PATH"]

