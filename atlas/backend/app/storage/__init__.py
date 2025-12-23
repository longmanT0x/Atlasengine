"""
Storage Module

Handles persistent storage using SQLite database.

Design Decisions:
- SQLite for simplicity and portability
- All data includes timestamps for audit trails
- Supports evidence, research, models, and decisions storage
- Database schema enforces source traceability
"""

from app.storage.database import init_db, get_db_connection, DB_PATH

__all__ = ["init_db", "get_db_connection", "DB_PATH"]

