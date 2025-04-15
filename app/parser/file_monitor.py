import time
import os
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.parser.novel_parser import NovelParser
from app.storage.novel_storage import NovelStorage

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NovelFileHandler(FileSystemEventHandler):
    """
    Handler for novel file system events (creation, modification, deletion, move/rename).
    """

    def __init__(self, novel_parser, novel_storage):
        """
        Initialize the handler with parser and storage.

        Args:
            novel_parser: Instance of NovelParser
            novel_storage: Instance of NovelStorage
        """
        self.parser = novel_parser
        self.storage = novel_storage
        self.txt_extension = ".txt"

    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and self._is_txt_file(event.src_path):
            logger.info(f"New novel file detected: {event.src_path}")
            self._process_novel_file(event.src_path)

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and self._is_txt_file(event.src_path):
            logger.info(f"Novel file modified: {event.src_path}")
            self._process_novel_file(event.src_path)

    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory and self._is_txt_file(event.src_path):
            logger.info(f"Novel file deleted: {event.src_path}")
            self.storage.delete_novel(event.src_path)

    def on_moved(self, event):
        """Handle file move/rename events."""
        # Check if both source and destination are TXT files
        if not event.is_directory and self._is_txt_file(event.src_path) and self._is_txt_file(event.dest_path):
            logger.info(f"Novel file moved/renamed: {event.src_path} -> {event.dest_path}")

            # If it's a rename within the same directory (just changing the filename)
            if os.path.dirname(event.src_path) == os.path.dirname(event.dest_path):
                # Update the file path in the database
                self.storage.update_novel_path(event.src_path, event.dest_path)
            else:
                # For moves between directories, treat as delete + create
                # This ensures all metadata is updated correctly
                self.storage.delete_novel(event.src_path)
                self._process_novel_file(event.dest_path)

    def _is_txt_file(self, file_path):
        """Check if the file is a TXT file."""
        return file_path.lower().endswith(self.txt_extension)

    def _process_novel_file(self, file_path):
        """Parse and store a novel file."""
        novel_data = self.parser.parse_file(file_path)
        if novel_data:
            self.storage.save_novel(novel_data)


class NovelMonitor:
    """
    Monitor for novel directories to detect file changes.
    """

    def __init__(self, novel_dirs, novel_storage):
        """
        Initialize the monitor with directories to watch.

        Args:
            novel_dirs: List of directories to monitor
            novel_storage: Instance of NovelStorage
        """
        self.novel_dirs = [Path(d).resolve() for d in novel_dirs]
        self.parser = NovelParser()
        self.storage = novel_storage
        self.observer = Observer()
        self.handler = NovelFileHandler(self.parser, self.storage)

    def start(self):
        """Start monitoring the novel directories."""
        for novel_dir in self.novel_dirs:
            if not novel_dir.exists() or not novel_dir.is_dir():
                logger.warning(f"Directory does not exist: {novel_dir}")
                continue

            logger.info(f"Starting to monitor directory: {novel_dir}")
            self.observer.schedule(self.handler, str(novel_dir), recursive=True)

        self.observer.start()
        logger.info("Novel monitor started")

        try:
            # Initial scan of existing files
            self._scan_existing_files()

            # Keep the thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop monitoring."""
        self.observer.stop()
        self.observer.join()
        logger.info("Novel monitor stopped")

    def _scan_existing_files(self):
        """Scan existing novel files in the monitored directories."""
        for novel_dir in self.novel_dirs:
            logger.info(f"Scanning existing files in: {novel_dir}")
            for file_path in novel_dir.glob('**/*.txt'):
                logger.info(f"Processing existing file: {file_path}")
                novel_data = self.parser.parse_file(file_path)
                if novel_data:
                    self.storage.save_novel(novel_data)
