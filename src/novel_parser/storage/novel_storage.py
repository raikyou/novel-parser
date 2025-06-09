import sqlite3
from pathlib import Path
from ..models.base import NovelMetadata


# 延迟导入解决循环依赖
def get_file_reader():
    from ..parser.txt_parser import FileReader
    return FileReader


def get_epub_parser():
    from ..parser.epub_parser import EpubParser
    return EpubParser()


class NovelStorage:
    def __init__(self, db_path: str = 'data/novels.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS novels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            file_path TEXT UNIQUE NOT NULL,
            chapter_count INTEGER NOT NULL
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        conn.close()

    def save_novel(self, novel_data: NovelMetadata) -> int | None:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM novels WHERE file_path = ?", (novel_data.file_path,))
        existing = cursor.fetchone()

        if existing:
            novel_id = existing['id']
            cursor.execute('''
            UPDATE novels
            SET title = ?, author = ?, chapter_count = ?
            WHERE id = ?
            ''', (novel_data.title, novel_data.author, novel_data.chapter_count, novel_id))
            cursor.execute("DELETE FROM chapters WHERE novel_id = ?", (novel_id,))
        else:
            cursor.execute('''
            INSERT INTO novels (title, author, file_path, chapter_count)
            VALUES (?, ?, ?, ?)
            ''', (novel_data.title, novel_data.author, novel_data.file_path,
                  novel_data.chapter_count))
            novel_id = cursor.lastrowid

        for chapter in novel_data.chapters:
            cursor.execute('''
            INSERT INTO chapters (novel_id, title, start_line, end_line, chapter_index, spine_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (novel_id, chapter.title, chapter.start_line,
                  chapter.end_line, chapter.chapter_index, chapter.spine_id))

        conn.commit()
        conn.close()
        return novel_id

    def search_novels(self, query: str = "") -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if query.strip():
            cursor.execute('''
            SELECT id, title, author, file_path, chapter_count
            FROM novels
            WHERE title LIKE ? OR author LIKE ?
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

        conn.close()
        return results

    def search_folders(self, folder_name: str) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
        SELECT id, title, author, file_path, chapter_count
        FROM novels
        WHERE file_path LIKE ?
        ''', (f'%/{folder_name}/%',))

        results = []
        for row in cursor.fetchall():
            novel_dict = dict(row)
            results.append(novel_dict)

        conn.close()
        return results

    def get_novel_chapters(self, novel_id: int) ->list[dict] | None:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
        SELECT id, title, chapter_index
        FROM chapters
        WHERE novel_id = ?
        ORDER BY chapter_index
        ''', (novel_id,))

        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'title': row['title'],
                'index': row['chapter_index']
            })

        conn.close()
        return results

    def get_chapter_content(self, chapter_id: int) -> dict | None:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
        SELECT c.id, c.title, c.start_line, c.end_line, c.spine_id, c.chapter_index, c.spine_id, n.file_path
        FROM chapters c
        JOIN novels n ON c.novel_id = n.id
        WHERE c.id = ?
        ''', (chapter_id,))

        row = cursor.fetchone()
        if not row or not row['file_path']:
            conn.close()
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
            conn.close()
            return None

        conn.close()
        return {
            'id': row['id'],
            'title': row['title'],
            'content': content,
            'index': row['chapter_index']
        }

    def delete_novel(self, file_path: str) -> tuple[int, str] | None:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, title FROM novels WHERE file_path = ?", (file_path,))
        novel = cursor.fetchone()

        if novel:
            novel_id = novel['id']
            title = novel['title']
            cursor.execute("DELETE FROM novels WHERE id = ?", (novel_id,))
            cursor.execute("DELETE FROM chapters WHERE novel_id = ?", (novel_id,))
            conn.commit()
            conn.close()
            return (novel_id, title)

        conn.close()
        return None

    def update_novel_path(self, old_path: str, new_path: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE novels SET file_path = ? WHERE file_path = ?
        ''', (new_path, old_path))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def get_all_file_paths(self) -> list[str]:
        """Get all file paths stored in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM novels")
        paths = [row[0] for row in cursor.fetchall()]
        conn.close()
        return paths

    def clean_orphaned_records(self) -> int:
        """Delete records for files that no longer exist"""
        orphaned_count = 0
        for file_path in self.get_all_file_paths():
            if not Path(file_path).exists():
                if self.delete_novel(file_path):
                    orphaned_count += 1
        print(f"Deleted {orphaned_count} orphaned records")
        return orphaned_count
