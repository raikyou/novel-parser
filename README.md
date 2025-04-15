# Novel Parser System

A system for parsing and monitoring TXT novel files, with an API for searching and retrieving novel content.

## Features

- Automatically parses TXT novel files to identify chapters and their content
- Monitors a novel directory (and subdirectories) for file changes (new, modified, deleted, renamed)
- Provides an API to:
  - Search novels by keyword
  - View a novel's table of contents (chapters)
  - View the content of specific chapters

## Requirements

- Python 3.6+
- Dependencies listed in `requirements.txt`

## Installation

### Method 1: Manual Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Method 2: Docker

```bash
# Pull the image
docker pull ghcr.io/yourusername/novel-parser:latest

# Run the container
docker run -d \
  -p 5000:5000 \
  -v /path/to/novels:/app/docs \
  --name novel-parser \
  ghcr.io/yourusername/novel-parser:latest
```

## Usage

### Starting the System

```bash
python main.py --novel-dirs docs --port 5000
```

Options:
- `--novel-dirs`: Directories to monitor for novel files (default: docs)
- `--db-path`: Path to the SQLite database file (default: novels.db)
- `--host`: Host to bind the API server (default: 0.0.0.0)
- `--port`: Port to bind the API server (default: 5000)

### API Endpoints

#### Search Novels

```
GET /api/novels/search?q=<query>
```

Example:
```
GET /api/novels/search?q=小说
```

Response:
```json
{
  "results": [
    {
      "id": 1,
      "title": "小说样本",
      "file_path": "docs/小说样本.txt",
      "chapter_count": 3
    }
  ]
}
```

#### Get Novel Chapters

```
GET /api/novels/<novel_id>/chapters
```

Example:
```
GET /api/novels/1/chapters
```

Response:
```json
{
  "id": 1,
  "title": "小说样本",
  "file_path": "docs/小说样本.txt",
  "chapter_count": 3,
  "chapters": [
    {
      "id": 1,
      "title": "第一章 相遇",
      "index": 0
    },
    {
      "id": 2,
      "title": "第二章 我们",
      "index": 1
    },
    {
      "id": 3,
      "title": "尾声",
      "index": 2
    }
  ]
}
```

#### Get Chapter Content

```
GET /api/chapters/<chapter_id>
```

Example:
```
GET /api/chapters/2
```

Response:
```json
{
  "id": 2,
  "title": "第二章 我们",
  "content": "第二段测试样本",
  "index": 1,
  "novel_id": 1,
  "novel_title": "小说样本"
}
```

## How It Works

1. The system monitors the specified directories for TXT files
2. When a new file is detected, it parses the content to identify chapters
3. When a file is modified, it re-parses the content and updates the database
4. When a file is deleted, it removes the corresponding novel from the database
5. When a file is renamed, it updates the file path in the database
6. The parsed data is stored in an SQLite database
7. The API provides access to the stored data

## Chapter Detection

The system uses regular expressions to detect common chapter patterns, such as:
- 第X章 Title
- 第X节 Title
- Chapter X
- 序章, 前言, 后记, 尾声, etc.

If no chapters are detected, the entire content is treated as a single chapter.

## License

MIT
