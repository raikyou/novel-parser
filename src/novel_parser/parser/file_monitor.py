import time
import sqlite3
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .novel_parser import NovelParser
from .epub_parser import EpubParser
from ..storage.novel_storage import NovelStorage


class NovelFileHandler(FileSystemEventHandler):
    def __init__(self, novel_storage: NovelStorage):
        self.storage = novel_storage
        self.txt_parser = NovelParser()
        self.epub_parser = EpubParser()
        self.supported_extensions = {
            ".txt": self.txt_parser,
            ".epub": self.epub_parser
        }

    def on_created(self, event):
        if not event.is_directory and self._is_supported_file(event.src_path):
            self._process_novel_file(event.src_path)

    def on_modified(self, event):
        print(f"File modified event: {event.src_path}")
        if not event.is_directory and self._is_supported_file(event.src_path):
                    self._process_novel_file(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and self._is_supported_file(event.src_path):
            self.storage.delete_novel(event.src_path)

    def on_moved(self, event):
        if not event.is_directory and self._is_supported_file(event.dest_path):
            if Path(event.src_path).parent == Path(event.dest_path).parent:
                self.storage.update_novel_path(event.src_path, event.dest_path)
            else:
                self.storage.delete_novel(event.src_path)
                self._process_novel_file(event.dest_path)

    def _is_supported_file(self, file_path: str) -> bool:
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.supported_extensions

    def _process_novel_file(self, file_path: str):
        file_path_obj = Path(file_path)
        file_ext = file_path_obj.suffix.lower()

        if file_ext not in self.supported_extensions:
            return

        parser = self.supported_extensions[file_ext]
        novel_data = parser.parse_file(file_path_obj)

        if novel_data:
            self.storage.save_novel(novel_data)


class NovelMonitor:
    def __init__(self, novel_dirs: list[str], novel_storage: NovelStorage):
        self.novel_dirs = [Path(d).resolve() for d in novel_dirs]
        self.storage = novel_storage
        self.observer = Observer()
        self.handler = NovelFileHandler(novel_storage)
        self._is_running = False

    def start(self):
        self._clean_orphaned_records()
        self._scan_existing_files()

        for novel_dir in self.novel_dirs:
            if novel_dir.exists():
                self.observer.schedule(self.handler, str(novel_dir), recursive=True)

        self.observer.start()
        self._is_running = True

        try:
            while self._is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def _clean_orphaned_records(self):
        """Clean up database records for files that no longer exist"""
        return self.storage.clean_orphaned_records()

    def stop(self):
        self._is_running = False
        self.observer.stop()
        self.observer.join()

    def _scan_existing_files(self):
        for novel_dir in self.novel_dirs:
            if not novel_dir.exists():
                continue

            for file_path in novel_dir.glob('**/*.txt'):
                self.handler._process_novel_file(str(file_path))

            for file_path in novel_dir.glob('**/*.epub'):
                self.handler._process_novel_file(str(file_path))
