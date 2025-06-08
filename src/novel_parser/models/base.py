from pydantic import BaseModel
from typing import Optional


class ChapterInfo(BaseModel):
    id: int
    title: str
    index: int


class NovelInfo(BaseModel):
    id: int
    title: str
    author: Optional[str] = None
    file_path: str
    chapter_count: int
    cover_url: str = "/static/book_cover.jpg"


class ChapterContent(BaseModel):
    id: int
    title: str
    content: str
    index: int


class NovelMetadata(BaseModel):
    title: str
    author: Optional[str] = None
    file_path: str
    chapter_count: int
    chapters: list['ChapterMetadata']


class ChapterMetadata(BaseModel):
    title: str
    start_line: int | None = None  # Line number where chapter content starts (1-based)
    end_line: int | None = None    # Line number where chapter content ends (exclusive)
    chapter_index: int
    spine_id: str | None = None  # EPUB spine item ID for content retrieval


