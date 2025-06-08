from pathlib import Path


class FileReader:
    @staticmethod
    def read_content_by_lines(file_path: Path, start_line: int, end_line: int) -> str:
        """Read content between line numbers (start_line inclusive, end_line exclusive)"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return ''.join(lines[start_line:end_line])

    @staticmethod
    def read_full_content(file_path: Path) -> str:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
