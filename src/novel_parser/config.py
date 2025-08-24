import os
from typing import Literal

DatabaseType = Literal["sqlite", "postgresql"]


class Config:
    """Configuration class for the novel parser application."""

    # Database configuration
    DATABASE_TYPE: DatabaseType = os.getenv("DATABASE_TYPE", "sqlite").lower()

    # SQLite configuration (kept for backward compatibility)
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "data/novels.db")

    # PostgreSQL configuration - single DATABASE_URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://novel_parser:password@localhost:5432/novel_parser")

    # Application configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "5001"))
    DOCS_DIR: str = os.getenv("DOCS_DIR", "docs")

    @classmethod
    def get_database_url(cls) -> str:
        """Get database connection URL based on database type."""
        if cls.DATABASE_TYPE == "sqlite":
            return cls.SQLITE_DB_PATH
        elif cls.DATABASE_TYPE == "postgresql":
            return cls.DATABASE_URL
        else:
            raise ValueError(f"Unsupported database type: {cls.DATABASE_TYPE}")

    @classmethod
    def validate_config(cls) -> None:
        """Validate configuration settings."""
        if cls.DATABASE_TYPE not in ["sqlite", "postgresql"]:
            raise ValueError(f"Invalid DATABASE_TYPE: {cls.DATABASE_TYPE}. Must be 'sqlite' or 'postgresql'")

        if cls.DATABASE_TYPE == "postgresql":
            if not cls.DATABASE_URL:
                raise ValueError("DATABASE_URL is required when using PostgreSQL")

            # Basic validation that DATABASE_URL looks like a PostgreSQL URL
            if not cls.DATABASE_URL.startswith(("postgresql://", "postgres://")):
                raise ValueError("DATABASE_URL must be a valid PostgreSQL connection string starting with 'postgresql://' or 'postgres://'")
