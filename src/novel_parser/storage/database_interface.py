from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from ..models.base import NovelMetadata


class DatabaseInterface(ABC):
    """Abstract interface for database operations."""

    @abstractmethod
    def connect(self) -> Any:
        """Create and return a database connection."""
        pass

    @abstractmethod
    def close_connection(self, conn: Any) -> None:
        """Close a database connection."""
        pass

    @abstractmethod
    def init_db(self) -> None:
        """Initialize database schema."""
        pass

    @abstractmethod
    def save_novel(self, novel_data: NovelMetadata, modified_time: str) -> Optional[int]:
        """Save or update novel data."""
        pass

    @abstractmethod
    def search_novels(self, query: str = "") -> List[Dict]:
        """Search novels by title or author."""
        pass

    @abstractmethod
    def search_folders(self, folder_name: str) -> List[Dict]:
        """Search novels by folder path."""
        pass

    @abstractmethod
    def get_novel_chapters(self, novel_id: int) -> Optional[List[Dict]]:
        """Get chapters for a novel."""
        pass

    @abstractmethod
    def get_chapter_content(self, chapter_id: int) -> Optional[Dict]:
        """Get chapter content and metadata."""
        pass

    @abstractmethod
    def delete_novel(self, file_path: str) -> Optional[Tuple[int, str]]:
        """Delete a novel by file path."""
        pass

    @abstractmethod
    def update_novel_path(self, old_path: str, new_path: str) -> bool:
        """Update novel file path."""
        pass


class DatabaseFactory:
    """Factory class for creating database instances."""

    @staticmethod
    def create_database(db_type: str, **kwargs) -> DatabaseInterface:
        """Create a database instance based on type."""
        if db_type.lower() == "sqlite":
            from .sqlite_storage import SQLiteStorage
            return SQLiteStorage(**kwargs)
        elif db_type.lower() == "postgresql":
            from .postgresql_storage import PostgreSQLStorage
            return PostgreSQLStorage(**kwargs)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
