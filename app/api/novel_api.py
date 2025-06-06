from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
import logging
from typing import Optional

from ..models import (
    SearchResponse,
    NovelChapters,
    ChapterContent,
    StatusResponse,
    FolderSearchResponse,
    NovelInfo
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_app(novel_storage):
    """Create FastAPI application with novel storage."""
    app = FastAPI(
        title="Novel Parser API",
        description="API for parsing and accessing novel content",
        version="1.0.0"
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.get("/api/novels/search", response_model=SearchResponse)
    async def search_novels(q: Optional[str] = Query("", description="Search query")):
        """Search for novels by title or author."""
        logger.info(f"Received search query: {q}")

        # Use the storage.search_novels method directly
        results = novel_storage.search_novels(q)

        # Convert to NovelInfo objects and add cover URL
        novel_infos = []
        for novel in results:
            novel_info = NovelInfo(**novel)
            novel_infos.append(novel_info)

        logger.info(f"Search for '{q}' returned {len(novel_infos)} novels")
        return SearchResponse(results=novel_infos)

    @app.get("/api/novels/{novel_id}/chapters", response_model=NovelChapters)
    async def get_novel_chapters(novel_id: int):
        """Get chapters list for a novel."""
        novel = novel_storage.get_novel_chapters(novel_id)
        if not novel:
            raise HTTPException(status_code=404, detail="Novel not found")

        return NovelChapters(**novel)

    @app.get("/api/chapters/{chapter_id}", response_model=ChapterContent)
    async def get_chapter_content(chapter_id: int):
        """Get content of a specific chapter."""
        chapter = novel_storage.get_chapter_content(chapter_id)
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")

        return ChapterContent(**chapter)

    @app.get("/api/status", response_model=StatusResponse)
    async def get_status():
        """Get API status."""
        return StatusResponse()

    @app.get("/api/folders/search/{folder_name}", response_model=FolderSearchResponse)
    async def search_novels_by_folder_name(folder_name: str):
        """Search for novels in a folder by folder name."""
        try:
            logger.info(f"Searching for novels in folder named: {folder_name}")

            # Search all novels in the folder with the given name (no query filter)
            results = novel_storage.search_novels_by_folder_name(folder_name, '')

            # Convert to NovelInfo objects
            novel_infos = []
            for novel in results:
                novel_info = NovelInfo(**novel)
                novel_infos.append(novel_info)

            logger.info(f"Found {len(novel_infos)} novels in folder named '{folder_name}'")
            return FolderSearchResponse(results=novel_infos, folder_name=folder_name)

        except Exception as e:
            logger.error(f"Error searching novels by folder name: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to search novels by folder name")

    return app
