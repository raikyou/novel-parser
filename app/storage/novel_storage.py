import logging
import sqlite3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NovelStorage:
    """
    Storage for parsed novels using SQLite database.
    """

    def __init__(self, db_path='novels.db'):
        """
        Initialize the storage with database path.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create novels table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS novels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            file_path TEXT UNIQUE NOT NULL,
            file_size INTEGER NOT NULL,
            chapter_count INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create chapters table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            novel_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            chapter_index INTEGER NOT NULL,
            FOREIGN KEY (novel_id) REFERENCES novels (id) ON DELETE CASCADE
        )
        ''')

        # Drop existing search index if it exists to avoid issues
        try:
            cursor.execute('DROP TABLE IF EXISTS novel_search')
        except sqlite3.OperationalError:
            pass

        # Create search index with tokenize=unicode61 for better CJK support
        cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS novel_search
        USING fts5(title, content, novel_id UNINDEXED, tokenize='unicode61')
        ''')

        conn.commit()
        conn.close()

        logger.info(f"Database initialized at {self.db_path}")

    def save_novel(self, novel_data):
        """
        Save a novel and its chapters to the database.

        Args:
            novel_data: Dictionary containing novel metadata and chapters
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Check if novel already exists
            cursor.execute("SELECT id FROM novels WHERE file_path = ?", (novel_data['file_path'],))
            existing_novel = cursor.fetchone()

            if existing_novel:
                # Update existing novel
                novel_id = existing_novel['id']
                cursor.execute('''
                UPDATE novels
                SET title = ?, author = ?, file_size = ?, chapter_count = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (novel_data['title'], novel_data.get('author'), novel_data['file_size'], novel_data['chapter_count'], novel_id))

                # Delete existing chapters
                cursor.execute("DELETE FROM chapters WHERE novel_id = ?", (novel_id,))
                cursor.execute("DELETE FROM novel_search WHERE novel_id = ?", (novel_id,))

                logger.info(f"Updated existing novel: {novel_data['title']}")
            else:
                # Insert new novel
                cursor.execute('''
                INSERT INTO novels (title, author, file_path, file_size, chapter_count)
                VALUES (?, ?, ?, ?, ?)
                ''', (novel_data['title'], novel_data.get('author'), novel_data['file_path'], novel_data['file_size'], novel_data['chapter_count']))

                novel_id = cursor.lastrowid
                logger.info(f"Inserted new novel: {novel_data['title']}")

            # Insert chapters
            for i, chapter in enumerate(novel_data['chapters']):
                cursor.execute('''
                INSERT INTO chapters (novel_id, title, content, chapter_index)
                VALUES (?, ?, ?, ?)
                ''', (novel_id, chapter['title'], chapter['content'], i))

                # Add to search index
                cursor.execute('''
                INSERT INTO novel_search (title, content, novel_id)
                VALUES (?, ?, ?)
                ''', (chapter['title'], chapter['content'], novel_id))

            conn.commit()
            logger.info(f"Saved {len(novel_data['chapters'])} chapters for novel: {novel_data['title']}")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving novel {novel_data['title']}: {str(e)}")
        finally:
            conn.close()

    def delete_novel(self, file_path):
        """
        Delete a novel from the database.

        Args:
            file_path: Path of the novel file to delete

        Returns:
            tuple: (novel_id, title) if novel was found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT id, title FROM novels WHERE file_path = ?", (file_path,))
            novel = cursor.fetchone()

            if novel:
                novel_id = novel['id']
                title = novel['title']

                # Delete novel and related chapters (cascade)
                cursor.execute("DELETE FROM novels WHERE id = ?", (novel_id,))
                cursor.execute("DELETE FROM novel_search WHERE novel_id = ?", (novel_id,))

                conn.commit()
                logger.info(f"Deleted novel: {title}")
                return (novel_id, title)
            else:
                logger.warning(f"Novel not found for deletion: {file_path}")
                return None

        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting novel {file_path}: {str(e)}")
            return None
        finally:
            conn.close()

    def search_novels(self, query):
        """
        Search for novels by title or author only.

        Args:
            query: Search query string. If empty, returns all novels.

        Returns:
            list: List of matching novels with metadata
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        results = []

        try:
            if not query or not query.strip():
                # If query is empty, return all novels
                cursor.execute('''
                SELECT n.id, n.title, n.author, n.file_path, n.chapter_count, c.title as last_chapter
                FROM novels n
                LEFT JOIN chapters c ON n.id = c.novel_id AND c.chapter_index = (SELECT MAX(chapter_index) FROM chapters WHERE novel_id = n.id)
                ORDER BY n.title
                ''')
            else:
                # Log the raw query for debugging
                logger.info(f"Raw search query: {query}")

                # Search by title or author only
                cursor.execute('''
                SELECT n.id, n.title, n.author, n.file_path, n.chapter_count, c.title as last_chapter
                FROM novels n
                LEFT JOIN chapters c ON n.id = c.novel_id AND c.chapter_index = (SELECT MAX(chapter_index) FROM chapters WHERE novel_id = n.id)
                WHERE n.title LIKE ? OR n.author LIKE ?
                ORDER BY n.title
                ''', (f'%{query}%', f'%{query}%'))

            # Process results
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'title': row['title'],
                    'author': row['author'],
                    'file_path': row['file_path'],
                    'chapter_count': row['chapter_count'],
                    'last_chapter': row['last_chapter'] if row['last_chapter'] else ''
                })

            logger.info(f"Search for '{query}' returned {len(results)} results")

        except Exception as e:
            logger.error(f"Error searching for '{query}': {str(e)}")
        finally:
            conn.close()

        return results

    def get_novel_chapters(self, novel_id):
        """
        Get the table of contents for a novel.

        Args:
            novel_id: ID of the novel

        Returns:
            dict: Novel metadata with chapter titles
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Get novel metadata (only essential fields)
            cursor.execute('''
            SELECT id, title, chapter_count
            FROM novels
            WHERE id = ?
            ''', (novel_id,))

            novel_row = cursor.fetchone()
            if not novel_row:
                logger.warning(f"Novel not found: {novel_id}")
                return None

            novel = {
                'id': novel_row['id'],
                'title': novel_row['title'],
                'chapter_count': novel_row['chapter_count'],
                'chapters': []
            }

            # Get chapter titles
            cursor.execute('''
            SELECT id, title, chapter_index
            FROM chapters
            WHERE novel_id = ?
            ORDER BY chapter_index
            ''', (novel_id,))

            for row in cursor.fetchall():
                novel['chapters'].append({
                    'id': row['id'],
                    'title': row['title'],
                    'index': row['chapter_index']
                })

            logger.info(f"Retrieved {len(novel['chapters'])} chapters for novel: {novel['title']}")
            return novel

        except Exception as e:
            logger.error(f"Error getting chapters for novel {novel_id}: {str(e)}")
            return None
        finally:
            conn.close()

    def update_novel_path(self, old_path, new_path):
        """
        Update the file path of a novel in the database.

        Args:
            old_path: Original path of the novel file
            new_path: New path of the novel file

        Returns:
            bool: True if the update was successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Check if novel exists with old path
            cursor.execute("SELECT id, title FROM novels WHERE file_path = ?", (old_path,))
            novel = cursor.fetchone()

            if not novel:
                logger.warning(f"Novel not found for path update: {old_path}")
                return False

            novel_id = novel['id']
            title = novel['title']

            # Update the file path
            cursor.execute('''
            UPDATE novels
            SET file_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (new_path, novel_id))

            conn.commit()
            logger.info(f"Updated file path for novel '{title}': {old_path} -> {new_path}")
            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating novel path {old_path} -> {new_path}: {str(e)}")
            return False
        finally:
            conn.close()

    def get_chapter_content(self, chapter_id):
        """
        Get the content of a specific chapter.

        Args:
            chapter_id: ID of the chapter

        Returns:
            dict: Chapter data with content
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute('''
            SELECT c.id, c.title, c.content, c.chapter_index, n.title as novel_title, n.id as novel_id
            FROM chapters c
            JOIN novels n ON c.novel_id = n.id
            WHERE c.id = ?
            ''', (chapter_id,))

            row = cursor.fetchone()
            if not row:
                logger.warning(f"Chapter not found: {chapter_id}")
                return None

            chapter = {
                'id': row['id'],
                'title': row['title'],
                'content': row['content'],
                'index': row['chapter_index'],
                'novel_id': row['novel_id'],
                'novel_title': row['novel_title']
            }

            logger.info(f"Retrieved content for chapter: {chapter['title']}")
            return chapter

        except Exception as e:
            logger.error(f"Error getting content for chapter {chapter_id}: {str(e)}")
            return None
        finally:
            conn.close()

    def search_novels_by_folder_name(self, folder_name, query=''):
        """
        Search for novels in a folder by folder name (not full path).

        Args:
            folder_name: Name of the folder to search in
            query: Search query string. If empty, returns all novels in the folder.

        Returns:
            list: List of matching novels in the specified folder
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        results = []

        try:
            # Find all novels whose file_path contains the folder name
            if not query or not query.strip():
                # If query is empty, return all novels in folders with the given name
                cursor.execute('''
                SELECT n.id, n.title, n.author, n.file_path, n.chapter_count, c.title as last_chapter
                FROM novels n
                LEFT JOIN chapters c ON n.id = c.novel_id AND c.chapter_index = (SELECT MAX(chapter_index) FROM chapters WHERE novel_id = n.id)
                WHERE n.file_path LIKE ?
                ORDER BY n.title
                ''', (f'%/{folder_name}/%',))
            else:
                # Search by title or author in folders with the given name
                cursor.execute('''
                SELECT n.id, n.title, n.author, n.file_path, n.chapter_count, c.title as last_chapter
                FROM novels n
                LEFT JOIN chapters c ON n.id = c.novel_id AND c.chapter_index = (SELECT MAX(chapter_index) FROM chapters WHERE novel_id = n.id)
                WHERE n.file_path LIKE ? AND (n.title LIKE ? OR n.author LIKE ?)
                ORDER BY n.title
                ''', (f'%/{folder_name}/%', f'%{query}%', f'%{query}%'))

            # Process results
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'title': row['title'],
                    'author': row['author'],
                    'file_path': row['file_path'],
                    'chapter_count': row['chapter_count'],
                    'last_chapter': row['last_chapter'] if row['last_chapter'] else ''
                })

            logger.info(f"Search for '{query}' in folder named '{folder_name}' returned {len(results)} results")

        except Exception as e:
            logger.error(f"Error searching for '{query}' in folder named '{folder_name}': {str(e)}")
        finally:
            conn.close()

        return results
