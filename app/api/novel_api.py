from flask import Flask, jsonify, request
import logging

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
        self.app = Flask(__name__, static_folder="/app/app/static")
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.app.route('/api/novels/search', methods=['GET'])
        def search_novels():
            # Get query parameter
            query = request.args.get('q', '')
            logger.info(f"Received search query: {query}")

            # Use the storage.search_novels method directly
            results = self.storage.search_novels(query)

            for novel in results:
                novel['cover_url'] = "/static/book_cover.jpg"

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

        @self.app.route('/api/folders/search/<folder_name>', methods=['GET'])
        def search_novels_by_folder_name(folder_name):
            """Search for novels in a folder by folder name."""
            try:
                logger.info(f"Searching for novels in folder named: {folder_name}")

                # Search all novels in the folder with the given name (no query filter)
                results = self.storage.search_novels_by_folder_name(folder_name, '')

                # Add cover URL to each result
                for novel in results:
                    novel['cover_url'] = "/static/book_cover.jpg"

                logger.info(f"Found {len(results)} novels in folder named '{folder_name}'")
                return jsonify({'results': results, 'folder_name': folder_name})

            except Exception as e:
                logger.error(f"Error searching novels by folder name: {str(e)}")
                return jsonify({'error': 'Failed to search novels by folder name'}), 500

    def start(self):
        """Start the API server."""
        logger.info(f"Starting Novel API server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port)

    def get_app(self):
        """Get the Flask app instance."""
        return self.app
