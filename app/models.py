from pydantic import BaseModel
from typing import List, Optional


class ChapterInfo(BaseModel):
    """Chapter information for table of contents."""
    id: int
    title: str
    index: int


class NovelInfo(BaseModel):
    """Novel information for search results."""
    id: int
    title: str
    author: Optional[str] = None
    file_path: str
    chapter_count: int
    last_chapter: str = ""
    cover_url: str = "/static/book_cover.jpg"


class NovelChapters(BaseModel):
    """Novel with its chapters list."""
    id: int
    title: str
    chapter_count: int
    chapters: List[ChapterInfo]


class ChapterContent(BaseModel):
    """Chapter content."""
    id: int
    title: str
    content: str
    index: int
    novel_id: int
    novel_title: str


class SearchResponse(BaseModel):
    """Search response."""
    results: List[NovelInfo]


class FolderSearchResponse(BaseModel):
    """Folder search response."""
    results: List[NovelInfo]
    folder_name: str


class StatusResponse(BaseModel):
    """Status response."""
    status: str = "running"
