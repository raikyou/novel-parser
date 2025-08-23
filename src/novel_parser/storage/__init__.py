"""
Storage layer for the novel parser system.
"""
from .sqlite_storage import SQLiteStorage
from .database_interface import DatabaseInterface, DatabaseFactory
from .postgresql_storage import PostgreSQLStorage

__all__ = [
    "SQLiteStorage",
    "DatabaseInterface",
    "DatabaseFactory",
    "PostgreSQLStorage"
]
