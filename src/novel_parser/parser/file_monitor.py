import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .txt_parser import NovelParser
from .epub_parser import EpubParser
from ..storage.database_interface import DatabaseInterface


class NovelFileHandler(FileSystemEventHandler):
    def __init__(self, novel_storage: DatabaseInterface):
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
            # 获取文件修改时间并转换为ISO格式
            mtime = file_path_obj.stat().st_mtime
            modified_time = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(mtime))
            self.storage.save_novel(novel_data, modified_time)


class NovelMonitor:
    def __init__(self, novel_dirs: list[str], novel_storage: DatabaseInterface):
        self.novel_dirs = [Path(d).resolve() for d in novel_dirs]
        self.storage = novel_storage
        self.observer = Observer()
        self.handler = NovelFileHandler(novel_storage)
        self._is_running = False

    def start(self):
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

    def stop(self):
        self._is_running = False
        self.observer.stop()
        self.observer.join()

    def _scan_existing_files(self):
        # 1. 收集所有监控目录下的文件
        existing_files = set()
        for novel_dir in self.novel_dirs:
            if not novel_dir.exists():
                continue

            for file_path in novel_dir.rglob('*'):
                if not file_path.is_file() or not self.handler._is_supported_file(str(file_path)):
                    continue
                existing_files.add(str(file_path.resolve()))

        # 2. 获取数据库中的所有记录
        db_records = {novel['file_path']: novel for novel in self.storage.search_novels()}

        # 3. 清理已删除文件的记录
        for db_path in db_records:
            if db_path not in existing_files:
                self.storage.delete_novel(db_path)

        # 4. 处理新文件和已修改的文件
        for file_path in existing_files:
            path_obj = Path(file_path)
            current_mtime = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(path_obj.stat().st_mtime))

            if file_path in db_records:
                # 文件存在于数据库中，检查是否需要更新
                stored_mtime = db_records[file_path].get('modified_time', '')
                if current_mtime != stored_mtime:
                    self.handler._process_novel_file(file_path)
            else:
                # 新文件，添加到数据库
                self.handler._process_novel_file(file_path)