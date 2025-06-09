"""
Parser components for the novel parser system.
"""
from .txt_parser import NovelParser
from .epub_parser import EpubParser
from .file_monitor import NovelMonitor

__all__ = ["NovelParser", "EpubParser", "NovelMonitor"]
