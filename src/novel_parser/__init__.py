__version__ = "2.0.0"

from .storage import SQLiteStorage, PostgreSQLStorage, DatabaseInterface
from .parser import NovelParser, EpubParser, NovelMonitor
from .api import create_app
from .models import (
    NovelInfo,
    ChapterInfo,
    ChapterContent,
)

__all__ = [
    "SQLiteStorage",
    "PostgreSQLStorage",
    "DatabaseInterface",
    "NovelParser",
    "EpubParser",
    "NovelMonitor",
    "create_app",
    "NovelInfo",
    "ChapterInfo",
    "ChapterContent",
]
