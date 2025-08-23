"""
Storage layer for the novel parser system.
"""
from .novel_storage import NovelStorage
from .database_interface import DatabaseInterface, DatabaseFactory
from .sqlite_storage import SQLiteStorage
from .postgresql_storage import PostgreSQLStorage

__all__ = [
    "NovelStorage",
    "DatabaseInterface",
    "DatabaseFactory",
    "SQLiteStorage",
    "PostgreSQLStorage"
]
