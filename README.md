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

- Python 3.12+
- uv package manager
- SQLite (default) or PostgreSQL (optional)

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

### Method 2: Docker with SQLite (Default)

```bash
# Build the image
docker build -t novel-parser .

# Run with SQLite (default)
docker run -d \
  -p 5001:5001 \
  -v /path/to/novels:/app/docs \
  -v /path/to/data:/app/data \
  --name novel-parser \
  novel-parser
```

### Method 3: Docker Compose

#### Using SQLite (Default)
```bash
# Copy environment file and customize if needed
cp .env.example .env

# Start with SQLite
docker-compose up -d novel-parser
```

#### Using PostgreSQL
```bash
# Copy environment file and configure for PostgreSQL
cp .env.example .env

# Edit .env file:
# DATABASE_TYPE=postgresql
# POSTGRES_PASSWORD=your_secure_password

# Start with PostgreSQL
docker-compose --profile postgresql up -d
```

## Usage

### Starting the System

```bash
uv run python main.py
```

## Configuration

The system supports both SQLite and PostgreSQL databases. Configuration is handled through environment variables:

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_TYPE` | `sqlite` | Database type: `sqlite` or `postgresql` |
| `SQLITE_DB_PATH` | `data/novels.db` | Path to SQLite database file |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `novel_parser` | PostgreSQL database name |
| `POSTGRES_USER` | `novel_parser` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `password` | PostgreSQL password |
| `POSTGRES_SCHEMA` | `public` | PostgreSQL schema name for data isolation |
| `POSTGRES_SKIP_SCHEMA_CREATION` | `false` | Skip automatic schema creation (assume schema exists) |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `5001` | API server port |
| `DOCS_DIR` | `docs` | Directory to monitor for novel files |

### Default Configuration
- Monitors the `docs` directory for novel files
- Uses SQLite database at `data/novels.db` by default
- Runs the API server on `0.0.0.0:5001`

The application creates the following directories if they don't exist:
- `data/`: For the SQLite database (when using SQLite)
- `docs/`: For novel files (configurable via `DOCS_DIR`)

### PostgreSQL Schema Support

When using PostgreSQL, you can specify a custom schema using the `POSTGRES_SCHEMA` environment variable. This enables multiple projects to share a single PostgreSQL database instance while maintaining data isolation:

**Benefits:**
- **Data Isolation**: Each project's data is stored in a separate schema
- **Resource Optimization**: Share a single PostgreSQL instance across multiple projects
- **Easy Management**: All schemas within the same database for simplified backup/restore

**Usage Examples:**
```bash
# Project 1 using 'project1' schema
POSTGRES_SCHEMA=project1

# Project 2 using 'project2' schema
POSTGRES_SCHEMA=project2

# Default public schema (if not specified)
POSTGRES_SCHEMA=public
```

**Schema Management:**
- Schemas are automatically created if they don't exist
- Tables are created within the specified schema
- All database operations are isolated to the schema
- Migration tool supports schema-specific migrations

**Permission Handling:**
If your database user doesn't have schema creation permissions, you can:
1. Create the schema manually in your database
2. Set `POSTGRES_SKIP_SCHEMA_CREATION=true` in your environment
3. Use `--skip-schema-creation` flag with the migration tool

```bash
# For users without schema creation permissions
POSTGRES_SKIP_SCHEMA_CREATION=true

# Migration with existing schema
python migrate_db.py --use-env --skip-schema-creation
```

## Database Migration

If you want to migrate from SQLite to PostgreSQL, use the provided migration tool:

### Method 1: Direct Migration

```bash
# Install dependencies
uv sync

# Run migration (dry run first to test)
python migrate_db.py --dry-run --use-env

# Run actual migration
python migrate_db.py --use-env
```

### Method 2: Docker Migration

```bash
# Set up environment variables for PostgreSQL
cp .env.example .env
# Edit .env to configure PostgreSQL settings

# Run migration using Docker
docker-compose -f docker-compose.migration.yml up migration

# After successful migration, start the application with PostgreSQL
# Edit .env: DATABASE_TYPE=postgresql
docker-compose --profile postgresql up -d
```

### Migration Options

- `--sqlite-path`: Path to SQLite database (default: `data/novels.db`)
- `--postgres-url`: PostgreSQL connection URL (alternative to `--use-env`)
- `--schema`: PostgreSQL schema name (defaults to environment variable or 'public')
- `--use-env`: Use environment variables for PostgreSQL connection
- `--dry-run`: Perform a test run without actual data migration

### Schema-Specific Migration Examples

```bash
# Migrate to a specific schema
python migrate_db.py --use-env --schema project1

# Migrate using custom connection and schema
python migrate_db.py --postgres-url "postgresql://user:pass@host:5432/db" --schema project2

# Test migration to custom schema (dry run)
python migrate_db.py --dry-run --use-env --schema test_project
```

The migration tool:
- Preserves all novel metadata and chapter information
- Maintains data integrity with foreign key relationships
- Provides progress tracking and detailed logging
- Includes rollback capabilities in case of errors
- Verifies migration completeness

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
6. The parsed data is stored in either SQLite (default) or PostgreSQL database
7. The FastAPI-based REST API provides access to the stored data with automatic OpenAPI documentation

### Database Support

The application supports two database backends:

- **SQLite** (default): Lightweight, file-based database perfect for single-user deployments
- **PostgreSQL**: Full-featured relational database ideal for multi-user environments and production deployments

Both databases use the same schema and provide identical functionality. The choice between them depends on your deployment requirements and scalability needs.

## Quick Start Examples

### Using SQLite (Default)
```bash
# No configuration needed - just run
uv run python main.py
```

### Using PostgreSQL
```bash
# Set environment variables
export DATABASE_TYPE=postgresql
export POSTGRES_HOST=localhost
export POSTGRES_DB=novel_parser
export POSTGRES_USER=your_user
export POSTGRES_PASSWORD=your_password

# Run the application
uv run python main.py
```

### Using Docker with PostgreSQL
```bash
# Create .env file
cat > .env << EOF
DATABASE_TYPE=postgresql
POSTGRES_PASSWORD=secure_password
EOF

# Start PostgreSQL and the application
docker-compose --profile postgresql up -d
```

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
