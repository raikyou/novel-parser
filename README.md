# Novel Parser System

A system for parsing and monitoring TXT and EPUB novel files, with a FastAPI-based API for searching and retrieving novel content. It can be used as a standalone application or as a backend for a novel reading application.

## Features

- Automatically parses TXT and EPUB novel files to identify chapters and their content
- For EPUB files, uses the built-in table of contents when available
- Extracts author information from metadata (EPUB) or filenames with the format "xxx 作者：xx" (optional)
- Monitors the `docs` directory (and subdirectories) for file changes (new, modified, deleted, renamed)
- Provides a FastAPI-based REST API to:
  - Search novels by title or author (no full-text search)
  - View a novel's table of contents (chapters)
  - View the content of specific chapters
  - Search novels by folder name

## Requirements

- Python 3.9+
- uv package manager

## Installation

### Method 1: Using uv (Recommended)

1. Clone the repository
2. Install uv if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. Install dependencies:
   ```bash
   uv sync
   ```

### Method 2: Docker

```bash
# Build the image
docker build -t novel-parser .

# Run the container
docker run -d \
  -p 5001:5001 \
  -v /path/to/novels:/app/docs \
  -v /path/to/data:/app/data \
  --name novel-parser \
  novel-parser
```

## Usage

### Starting the System

```bash
uv run python main.py
```

The system uses fixed configuration:
- Monitors the `docs` directory for novel files
- Uses `data/novels.db` for the SQLite database
- Runs the API server on `0.0.0.0:5001`

The application creates the following directories if they don't exist:
- `logs/`: For log files
- `data/`: For the SQLite database

### API Endpoints

The API is now built with FastAPI and includes automatic OpenAPI documentation available at `http://localhost:5001/docs`.

#### Search Novels

Search novels by title or author (no full-text search):

```
GET /api/novels/search?q=<query>
```

Response:
```json
{
  "results": [
    {
      "id": 1,
      "title": "小说样本",
      "author": "作者名",
      "file_path": "docs/小说样本 作者：作者名.txt",
      "chapter_count": 3,
      "last_chapter": "尾声",
      "cover_url": "/static/book_cover.jpg"
    }
  ]
}
```

#### Get Novel Chapters

```
GET /api/novels/{novel_id}/chapters
```

Response:
```json
{
  "id": 1,
  "title": "小说样本",
  "chapter_count": 3,
  "chapters": [
    {
      "id": 1,
      "title": "第一章",
      "index": 0
    }
  ]
}
```

#### Get Chapter Content

```
GET /api/chapters/{chapter_id}
```

Response:
```json
{
  "id": 2,
  "title": "第二章",
  "content": "第二段测试样本",
  "index": 1,
  "novel_id": 1,
  "novel_title": "小说样本"
}
```

#### Search Novels by Folder

```
GET /api/folders/search/{folder_name}
```

Response:
```json
{
  "results": [
    {
      "id": 1,
      "title": "小说样本",
      "author": "作者名",
      "file_path": "docs/folder_name/小说样本.txt",
      "chapter_count": 3,
      "last_chapter": "尾声",
      "cover_url": "/static/book_cover.jpg"
    }
  ],
  "folder_name": "folder_name"
}
```

#### API Status

```
GET /api/status
```

Response:
```json
{
  "status": "running"
}
```

## How It Works

1. The system monitors the `docs` directory for TXT and EPUB files
2. When a new file is detected, it parses the content to identify chapters
3. When a file is modified, it re-parses the content and updates the database
4. When a file is deleted, it removes the corresponding novel from the database
5. When a file is renamed, it updates the file path in the database
6. The parsed data is stored in an SQLite database
7. The FastAPI-based REST API provides access to the stored data with automatic OpenAPI documentation

## Chapter Detection

### TXT Files
The system uses regular expressions to detect common chapter patterns, such as:
- 第X章 Title
- 第X节 Title
- Chapter X
- 序章, 前言, 后记, 尾声, etc.

If no chapters are detected, the entire content is treated as a single chapter.

### EPUB Files
For EPUB files, the system:
1. Uses the built-in table of contents (TOC) if available
2. If no TOC is available, attempts to extract chapters from the spine
3. If no chapters can be identified, treats the entire content as a single chapter
4. Content that appears before the first chapter (like cover pages or introductions) is captured as a separate chapter titled "正文" (Main Text)

## Troubleshooting

### Docker Permission Issues

If you encounter permission errors when running the Docker container, make sure:

1. The container has access to write to the mounted volumes:
   ```bash
   # Create directories with appropriate permissions
   mkdir -p data logs
   chmod 777 data logs
   ```

2. Use the provided `docker-run.sh` script which handles directory creation and permissions.

3. Check container logs for specific errors:
   ```bash
   docker logs novel-parser
   ```

## License

MIT
