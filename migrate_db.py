#!/usr/bin/env python3
"""
Database Migration Tool for Novel Parser

This script migrates data from SQLite to PostgreSQL database.
It handles all tables, maintains data integrity, and provides progress tracking.
"""

import sys
import argparse
import sqlite3
import psycopg2
import psycopg2.extras
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment variables from {env_file}")
    else:
        print("No .env file found, using system environment variables")
except ImportError:
    print("python-dotenv not installed, using system environment variables only")

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from novel_parser.config import Config


class DatabaseMigrator:
    """Handles migration from SQLite to PostgreSQL."""

    def __init__(self, sqlite_path: str, postgres_url: str, dry_run: bool = False):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.dry_run = dry_run
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('migration')
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # File handler
        log_file = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    def connect_sqlite(self) -> sqlite3.Connection:
        """Connect to SQLite database."""
        if not Path(self.sqlite_path).exists():
            raise FileNotFoundError(f"SQLite database not found: {self.sqlite_path}")

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def connect_postgres(self) -> psycopg2.extensions.connection:
        """Connect to PostgreSQL database."""
        conn = psycopg2.connect(self.postgres_url)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn

    def get_sqlite_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract all data from SQLite database."""
        self.logger.info("Extracting data from SQLite database...")

        sqlite_conn = self.connect_sqlite()
        cursor = sqlite_conn.cursor()

        data = {}

        # Get novels
        cursor.execute("SELECT * FROM novels ORDER BY id")
        novels = [dict(row) for row in cursor.fetchall()]
        data['novels'] = novels
        self.logger.info(f"Found {len(novels)} novels")

        # Get chapters
        cursor.execute("SELECT * FROM chapters ORDER BY novel_id, chapter_index")
        chapters = [dict(row) for row in cursor.fetchall()]
        data['chapters'] = chapters
        self.logger.info(f"Found {len(chapters)} chapters")

        sqlite_conn.close()
        return data

    def create_postgres_tables(self) -> None:
        """Create PostgreSQL tables."""
        self.logger.info("Creating PostgreSQL tables...")

        if self.dry_run:
            self.logger.info("DRY RUN: Would create PostgreSQL tables")
            return

        postgres_conn = self.connect_postgres()
        cursor = postgres_conn.cursor()

        # Drop existing tables if they exist
        cursor.execute("DROP TABLE IF EXISTS chapters CASCADE")
        cursor.execute("DROP TABLE IF EXISTS novels CASCADE")

        # Create novels table
        cursor.execute('''
        CREATE TABLE novels (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            file_path TEXT UNIQUE NOT NULL,
            chapter_count INTEGER NOT NULL,
            modified_time TEXT NOT NULL
        )
        ''')

        # Create chapters table
        cursor.execute('''
        CREATE TABLE chapters (
            id SERIAL PRIMARY KEY,
            novel_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            start_line INTEGER,
            end_line INTEGER,
            chapter_index INTEGER NOT NULL,
            spine_id TEXT,
            FOREIGN KEY (novel_id) REFERENCES novels (id) ON DELETE CASCADE
        )
        ''')

        postgres_conn.commit()
        postgres_conn.close()
        self.logger.info("PostgreSQL tables created successfully")

    def migrate_data(self, data: Dict[str, List[Dict[str, Any]]]) -> None:
        """Migrate data to PostgreSQL."""
        self.logger.info("Migrating data to PostgreSQL...")

        if self.dry_run:
            self.logger.info("DRY RUN: Would migrate data to PostgreSQL")
            self.logger.info(f"Would migrate {len(data['novels'])} novels and {len(data['chapters'])} chapters")
            return

        postgres_conn = self.connect_postgres()
        cursor = postgres_conn.cursor()

        try:
            # Migrate novels
            novel_id_mapping = {}
            for i, novel in enumerate(data['novels']):
                cursor.execute('''
                INSERT INTO novels (title, author, file_path, chapter_count, modified_time)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
                ''', (novel['title'], novel['author'], novel['file_path'],
                      novel['chapter_count'], novel['modified_time']))

                new_id = cursor.fetchone()['id']
                novel_id_mapping[novel['id']] = new_id

                if (i + 1) % 100 == 0:
                    self.logger.info(f"Migrated {i + 1}/{len(data['novels'])} novels")

            self.logger.info(f"Migrated all {len(data['novels'])} novels")

            # Migrate chapters
            for i, chapter in enumerate(data['chapters']):
                new_novel_id = novel_id_mapping[chapter['novel_id']]
                cursor.execute('''
                INSERT INTO chapters (novel_id, title, start_line, end_line, chapter_index, spine_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ''', (new_novel_id, chapter['title'], chapter['start_line'],
                      chapter['end_line'], chapter['chapter_index'], chapter['spine_id']))

                if (i + 1) % 1000 == 0:
                    self.logger.info(f"Migrated {i + 1}/{len(data['chapters'])} chapters")

            self.logger.info(f"Migrated all {len(data['chapters'])} chapters")

            postgres_conn.commit()
            self.logger.info("Data migration completed successfully")

        except Exception as e:
            postgres_conn.rollback()
            self.logger.error(f"Migration failed: {e}")
            raise
        finally:
            postgres_conn.close()

    def verify_migration(self, original_data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Verify migration integrity."""
        self.logger.info("Verifying migration integrity...")

        if self.dry_run:
            self.logger.info("DRY RUN: Would verify migration integrity")
            return True

        postgres_conn = self.connect_postgres()
        cursor = postgres_conn.cursor()

        try:
            # Check novels count
            cursor.execute("SELECT COUNT(*) as count FROM novels")
            novels_count = cursor.fetchone()['count']
            expected_novels = len(original_data['novels'])

            if novels_count != expected_novels:
                self.logger.error(f"Novel count mismatch: expected {expected_novels}, got {novels_count}")
                return False

            # Check chapters count
            cursor.execute("SELECT COUNT(*) as count FROM chapters")
            chapters_count = cursor.fetchone()['count']
            expected_chapters = len(original_data['chapters'])

            if chapters_count != expected_chapters:
                self.logger.error(f"Chapter count mismatch: expected {expected_chapters}, got {chapters_count}")
                return False

            self.logger.info("Migration verification passed")
            return True

        except Exception as e:
            self.logger.error(f"Verification failed: {e}")
            return False
        finally:
            postgres_conn.close()

    def migrate(self) -> bool:
        """Perform the complete migration process."""
        try:
            self.logger.info("Starting database migration...")
            self.logger.info(f"Source: SQLite ({self.sqlite_path})")
            self.logger.info(f"Target: PostgreSQL ({self.postgres_url})")
            self.logger.info(f"Dry run: {self.dry_run}")

            # Extract data from SQLite
            data = self.get_sqlite_data()

            # Create PostgreSQL tables
            self.create_postgres_tables()

            # Migrate data
            self.migrate_data(data)

            # Verify migration
            if not self.verify_migration(data):
                self.logger.error("Migration verification failed")
                return False

            self.logger.info("Database migration completed successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Migrate Novel Parser database from SQLite to PostgreSQL")
    parser.add_argument("--sqlite-path", default="data/novels.db", help="Path to SQLite database")
    parser.add_argument("--postgres-url", help="PostgreSQL connection URL")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without actual migration")
    parser.add_argument("--use-env", action="store_true", help="Use environment variables for PostgreSQL connection")

    args = parser.parse_args()

    # Determine PostgreSQL URL
    if args.use_env:
        postgres_url = Config.get_database_url()
        if Config.DATABASE_TYPE != "postgresql":
            print("Error: DATABASE_TYPE must be 'postgresql' when using --use-env")
            sys.exit(1)
    elif args.postgres_url:
        postgres_url = args.postgres_url
    else:
        print("Error: Either --postgres-url or --use-env must be specified")
        sys.exit(1)

    # Create migrator and run migration
    migrator = DatabaseMigrator(args.sqlite_path, postgres_url, args.dry_run)
    success = migrator.migrate()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
