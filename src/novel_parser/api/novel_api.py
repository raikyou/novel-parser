from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from ..models import (
    NovelInfo,
    ChapterInfo,
    ChapterContent,
)
from ..storage.novel_storage import NovelStorage


def create_app(novel_storage: NovelStorage) -> FastAPI:
    app = FastAPI(title="Novel Parser API", version="2.0.0")

    static_path = Path(__file__).parent.parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    @app.get("/api/novels/search", response_model=list[NovelInfo])
    async def search_novels(q: str = Query("", description="Search query")):
        results = novel_storage.search_novels(q)
        return results

    @app.get("/api/folders/search/{foldername}", response_model=list[NovelInfo])
    async def search_folders(foldername: str):
        results = novel_storage.search_folders(foldername)
        return results

    @app.get("/api/novels/{novel_id}/chapters", response_model=list[ChapterInfo])
    async def get_novel_chapters(novel_id: int):
        results = novel_storage.get_novel_chapters(novel_id)
        return results

    @app.get("/api/chapters/{chapter_id}", response_model=ChapterContent)
    async def get_chapter_content(chapter_id: int):
        content = novel_storage.get_chapter_content(chapter_id)
        if content is None:
            raise HTTPException(
                status_code=404,
                detail=f"Chapter {chapter_id} not found or content unavailable"
            )
        return ChapterContent(**content)

    return app
