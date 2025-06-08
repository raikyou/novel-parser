__version__ = "2.0.0"

from .storage import NovelStorage
from .parser import NovelParser, EpubParser, NovelMonitor
from .api import create_app
from .models import (
    NovelInfo,
    ChapterInfo,
    ChapterContent,
)

__all__ = [
    "NovelStorage",
    "NovelParser",
    "EpubParser",
    "NovelMonitor",
    "create_app",
    "NovelInfo",
    "ChapterInfo",
    "ChapterContent",
]
