# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Novel Parser System is a FastAPI-based application for parsing and monitoring TXT and EPUB novel files. It supports both SQLite (default) and PostgreSQL databases and provides a REST API for searching and retrieving novel content.

## Common Commands

### Development Commands
```bash
# Install dependencies
uv sync

# Run the application
uv run python main.py
# or
uv run python src/novel_parser/main.py

# Run with custom entry point
uv run novel-parser

# Run tests
uv run pytest
```

### Docker Commands
```bash
# Build and run with SQLite (default)
docker build -t novel-parser .
docker run -d -p 5001:5001 -v /path/to/novels:/app/docs -v /path/to/data:/app/data --name novel-parser novel-parser

# Run with docker-compose (SQLite)
docker-compose up -d novel-parser

# Run with PostgreSQL
docker-compose --profile postgresql up -d
```

### Database Migration
```bash
# Migrate from SQLite to PostgreSQL
python migrate_db.py --dry-run --use-env  # Test migration
python migrate_db.py --use-env            # Actual migration
```

## Architecture

### Core Components

- **Main Entry Point**: `src/novel_parser/main.py` - Application startup, signal handling, and FastAPI server
- **Configuration**: `src/novel_parser/config.py` - Environment-based configuration with support for SQLite/PostgreSQL
- **Storage Layer**: `src/novel_parser/storage/` - Database abstraction with factory pattern
  - `DatabaseInterface` - Abstract base class
  - `SQLiteStorage` and `PostgreSQLStorage` - Concrete implementations
  - `NovelStorage` - High-level storage operations
- **Parser Layer**: `src/novel_parser/parser/` - File parsing and monitoring
  - `NovelParser` - TXT file parsing with regex-based chapter detection
  - `EpubParser` - EPUB parsing using TOC or spine extraction
  - `NovelMonitor` - File system monitoring with watchdog
- **API Layer**: `src/novel_parser/api/novel_api.py` - FastAPI endpoints with automatic OpenAPI docs

### Key Patterns

- **Database Factory Pattern**: Use `DatabaseFactory.create_database()` to get storage instances
- **Configuration**: All settings via environment variables through `Config` class
- **Threading**: File monitor runs in separate daemon thread
- **Signal Handling**: Graceful shutdown on SIGINT/SIGTERM

### Database Structure

Both SQLite and PostgreSQL use identical table structures:
- `novels` table: metadata (title, author, file_path, etc.)
- `chapters` table: chapter content with foreign key to novels
- Automatic directory creation for `data/` and `docs/`

### File Structure

- `src/novel_parser/` - Main source code
- `data/` - SQLite database location (auto-created)
- `docs/` - Novel files directory (configurable via DOCS_DIR)
- `tests/` - Test files
- `static/` - Static assets (book covers)

## Environment Configuration

Key environment variables:
- `DATABASE_TYPE`: "sqlite" (default) or "postgresql"
- `SQLITE_DB_PATH`: Path to SQLite file (default: "data/novels.db")
- `DATABASE_URL`: Complete PostgreSQL connection string (e.g., "postgresql://user:pass@host:port/db")
  - Can include custom search path: "postgresql://user:pass@host:port/db?options=-csearch_path=myschema"

## API Endpoints

- FastAPI automatic documentation: `http://localhost:5001/docs`
- Novel search: `GET /api/novels/search?q=<query>`
- Chapter listing: `GET /api/novels/{novel_id}/chapters`
- Chapter content: `GET /api/chapters/{chapter_id}`
- Folder search: `GET /api/folders/search/{folder_name}`

## Development Notes

- Uses `uv` package manager for dependency management
- Python 3.12+ required
- File monitoring supports TXT and EPUB formats
- Chapter detection uses regex patterns for TXT files
- EPUB parsing prioritizes TOC over spine extraction
- Database migration tool preserves all data integrity