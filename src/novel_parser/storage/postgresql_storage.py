import psycopg2
import psycopg2.extras
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from ..models.base import NovelMetadata
from .database_interface import DatabaseInterface


def get_file_reader():
    from ..parser.txt_parser import FileReader
    return FileReader


def get_epub_parser():
    from ..parser.epub_parser import EpubParser
    return EpubParser()


class PostgreSQLStorage(DatabaseInterface):
    """PostgreSQL implementation of the database interface."""
    
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.init_db()
    
    def connect(self) -> Any:
        """Create and return a database connection."""
        conn = psycopg2.connect(self.connection_url)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    
    def close_connection(self, conn: Any) -> None:
        """Close a database connection."""
        if conn:
            conn.close()
    
    def init_db(self) -> None:
        """Initialize database schema."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS novels (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            file_path TEXT UNIQUE NOT NULL,
            chapter_count INTEGER NOT NULL,
            modified_time TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chapters (
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
        
        conn.commit()
        self.close_connection(conn)
    
    def save_novel(self, novel_data: NovelMetadata, modified_time: str) -> Optional[int]:
        """Save or update novel data."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM novels WHERE file_path = %s", (novel_data.file_path,))
        existing = cursor.fetchone()
        
        if existing:
            novel_id = existing['id']
            cursor.execute('''
            UPDATE novels
            SET title = %s, author = %s, chapter_count = %s, modified_time = %s
            WHERE id = %s
            ''', (novel_data.title, novel_data.author, novel_data.chapter_count,
                  modified_time, novel_id))
            cursor.execute("DELETE FROM chapters WHERE novel_id = %s", (novel_id,))
        else:
            cursor.execute('''
            INSERT INTO novels (title, author, file_path, chapter_count, modified_time)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
            ''', (novel_data.title, novel_data.author, novel_data.file_path,
                  novel_data.chapter_count, modified_time))
            novel_id = cursor.fetchone()['id']
        
        for chapter in novel_data.chapters:
            cursor.execute('''
            INSERT INTO chapters (novel_id, title, start_line, end_line, chapter_index, spine_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ''', (novel_id, chapter.title, chapter.start_line,
                  chapter.end_line, chapter.chapter_index, chapter.spine_id))
        
        conn.commit()
        self.close_connection(conn)
        return novel_id
    
    def search_novels(self, query: str = "") -> List[Dict]:
        """Search novels by title or author."""
        conn = self.connect()
        cursor = conn.cursor()
        
        if query.strip():
            cursor.execute('''
            SELECT id, title, author, file_path, chapter_count
            FROM novels
            WHERE title ILIKE %s OR author ILIKE %s
            ''', (f'%{query}%', f'%{query}%'))
        else:
            cursor.execute('''
            SELECT id, title, author, file_path, chapter_count
            FROM novels
            ''')
        
        results = []
        for row in cursor.fetchall():
            novel_dict = dict(row)
            results.append(novel_dict)
        
        self.close_connection(conn)
        return results
    
    def search_folders(self, folder_name: str) -> List[Dict]:
        """Search novels by folder path."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, title, author, file_path, chapter_count
        FROM novels
        WHERE file_path LIKE %s
        ''', (f'%/{folder_name}/%',))
        
        results = []
        for row in cursor.fetchall():
            novel_dict = dict(row)
            results.append(novel_dict)
        
        self.close_connection(conn)
        return results
    
    def get_novel_chapters(self, novel_id: int) -> Optional[List[Dict]]:
        """Get chapters for a novel."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, title, chapter_index
        FROM chapters
        WHERE novel_id = %s
        ORDER BY chapter_index
        ''', (novel_id,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'title': row['title'],
                'index': row['chapter_index']
            })
        
        self.close_connection(conn)
        return results
    
    def get_chapter_content(self, chapter_id: int) -> Optional[Dict]:
        """Get chapter content and metadata."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT c.id, c.title, c.start_line, c.end_line, c.spine_id, c.chapter_index, c.spine_id, n.file_path
        FROM chapters c
        JOIN novels n ON c.novel_id = n.id
        WHERE c.id = %s
        ''', (chapter_id,))
        
        row = cursor.fetchone()
        if not row or not row['file_path']:
            self.close_connection(conn)
            return None
        
        file_path = Path(row['file_path'])
        if file_path.suffix.lower() == '.epub':
            parser = get_epub_parser()
            content = parser.get_chapter_content(file_path, row['spine_id'])
        else:
            parser = get_file_reader()
            content = parser.read_content_by_lines(
                file_path, row['start_line'], row['end_line']
            )
        if content is None:
            self.close_connection(conn)
            return None
        
        self.close_connection(conn)
        return {
            'id': row['id'],
            'title': row['title'],
            'content': content,
            'index': row['chapter_index']
        }
    
    def delete_novel(self, file_path: str) -> Optional[Tuple[int, str]]:
        """Delete a novel by file path."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, title FROM novels WHERE file_path = %s", (file_path,))
        novel = cursor.fetchone()
        
        if novel:
            novel_id = novel['id']
            title = novel['title']
            cursor.execute("DELETE FROM novels WHERE id = %s", (novel_id,))
            cursor.execute("DELETE FROM chapters WHERE novel_id = %s", (novel_id,))
            conn.commit()
            self.close_connection(conn)
            return (novel_id, title)
        
        self.close_connection(conn)
        return None
    
    def update_novel_path(self, old_path: str, new_path: str) -> bool:
        """Update novel file path."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE novels SET file_path = %s WHERE file_path = %s
        ''', (new_path, old_path))
        
        success = cursor.rowcount > 0
        conn.commit()
        self.close_connection(conn)
        return success
