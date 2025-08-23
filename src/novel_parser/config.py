import os
from typing import Literal

DatabaseType = Literal["sqlite", "postgresql"]


class Config:
    """Configuration class for the novel parser application."""
    
    # Database configuration
    DATABASE_TYPE: DatabaseType = os.getenv("DATABASE_TYPE", "sqlite").lower()
    
    # SQLite configuration
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "data/novels.db")
    
    # PostgreSQL configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "novel_parser")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "novel_parser")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    
    # Application configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "5001"))
    DOCS_DIR: str = os.getenv("DOCS_DIR", "docs")
    
    @classmethod
    def get_postgres_url(cls) -> str:
        """Get PostgreSQL connection URL."""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate configuration settings."""
        if cls.DATABASE_TYPE not in ["sqlite", "postgresql"]:
            raise ValueError(f"Invalid DATABASE_TYPE: {cls.DATABASE_TYPE}. Must be 'sqlite' or 'postgresql'")
        
        if cls.DATABASE_TYPE == "postgresql":
            required_postgres_vars = [
                "POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"
            ]
            missing_vars = []
            for var in required_postgres_vars:
                if not getattr(cls, var):
                    missing_vars.append(var)
            
            if missing_vars:
                raise ValueError(f"Missing required PostgreSQL configuration: {', '.join(missing_vars)}")
