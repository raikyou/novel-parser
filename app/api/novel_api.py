from flask import Flask, jsonify, request
import logging
import sqlite3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NovelAPI:
    """
    API for accessing novel data.
    """

    def __init__(self, novel_storage, host='0.0.0.0', port=5000):
        """
        Initialize the API with storage.

        Args:
            novel_storage: Instance of NovelStorage
            host: Host to bind the API server
            port: Port to bind the API server
        """
        self.storage = novel_storage
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.app.route('/api/novels/search', methods=['GET'])
        def search_novels():
            # Get all novels first
            conn = sqlite3.connect(self.storage.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            all_novels = []

            try:
                cursor.execute('''
                SELECT id, title, file_path, chapter_count
                FROM novels
                ORDER BY title
                ''')

                for row in cursor.fetchall():
                    all_novels.append({
                        'id': row['id'],
                        'title': row['title'],
                        'file_path': row['file_path'],
                        'chapter_count': row['chapter_count']
                    })
            except Exception as e:
                logger.error(f"Error fetching novels: {str(e)}")
            finally:
                conn.close()

            # Get query parameter
            query = request.args.get('q', '')
            logger.info(f"Received search query: {query}")

            # If query is empty, return empty results
            if not query or not query.strip():
                logger.info("Empty query, returning no results")
                return jsonify({'results': []})

            # Filter novels by title
            results = []
            for novel in all_novels:
                # Convert query to bytes and back to handle encoding issues
                try:
                    # Try different encodings
                    encodings = ['utf-8', 'latin-1', 'iso-8859-1']
                    for encoding in encodings:
                        try:
                            # Try to encode and decode the query
                            decoded_query = query.encode(encoding).decode('utf-8')
                            if decoded_query in novel['title']:
                                results.append(novel)
                                break
                        except UnicodeError:
                            continue
                except Exception as e:
                    logger.warning(f"Error handling encoding: {str(e)}")

            # If no results with encoding tricks, try direct matching
            if not results:
                for novel in all_novels:
                    if query.lower() in novel['title'].lower():
                        results.append(novel)

            logger.info(f"Search for '{query}' returned {len(results)} novels")
            return jsonify({'results': results})

        @self.app.route('/api/novels/<int:novel_id>/chapters', methods=['GET'])
        def get_novel_chapters(novel_id):
            novel = self.storage.get_novel_chapters(novel_id)
            if not novel:
                return jsonify({'error': 'Novel not found'}), 404

            return jsonify(novel)

        @self.app.route('/api/chapters/<int:chapter_id>', methods=['GET'])
        def get_chapter_content(chapter_id):
            chapter = self.storage.get_chapter_content(chapter_id)
            if not chapter:
                return jsonify({'error': 'Chapter not found'}), 404

            return jsonify(chapter)

        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            return jsonify({'status': 'running'})

    def start(self):
        """Start the API server."""
        logger.info(f"Starting Novel API server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port)

    def get_app(self):
        """Get the Flask app instance."""
        return self.app
