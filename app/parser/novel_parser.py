import re
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NovelParser:
    """
    Parser for TXT novel files that identifies chapters and their content.
    """

    # Regular expression patterns for chapter detection
    # Advanced patterns for matching various chapter formats in Chinese novels
    CHAPTER_PATTERNS = [
        # 第X章/节 - 最常见的章节格式
        r'^.{0,2}第[\d〇零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟]+[章节回卷].{0,10}$',

        # 序章、终章、尾声等特殊章节
        r'^.{0,2}[序终尾楔引前后][章言声子记].{0,10}$',

        # 正文、番外等特殊章节
        r'^.{0,2}[正番内文][文外容章].{0,10}$',

        # 上部、中篇、下卷等特殊章节
        r'^.{0,2}[上中下外][部篇卷].{0,10}$',

        # 数字加点/顶格式 1.目录
        r'^.{0,2}\d+[、\.].{0,10}$',

        # 英文章节
        r'^.{0,2}[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\d+.{0,10}$',

        # 特殊标记章节
        r'^.{0,2}[☆★✦✧].{0,10}$',

        # 分隔线章节
        r'^.{0,2}={2,4}.{0,10}$'
    ]

    def __init__(self):
        # Compile the regex patterns for better performance
        # 使用re.MULTILINE标志使^$匹配行首行尾
        self.chapter_regex = re.compile('|'.join(f'({pattern})' for pattern in self.CHAPTER_PATTERNS), re.MULTILINE)

    def parse_file(self, file_path):
        """
        Parse a novel file and extract chapters and their content.

        Args:
            file_path: Path to the novel file

        Returns:
            dict: A dictionary containing novel metadata and chapters
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists() or not file_path.is_file():
                logger.error(f"File not found: {file_path}")
                return None

            # Get basic file info
            file_name = file_path.name
            file_size = file_path.stat().st_size

            # Read the file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract novel title (using filename without extension)
            novel_title = file_path.stem

            chapters = self._extract_chapters(content)

            # Create novel metadata
            novel_data = {
                'title': novel_title,
                'file_path': str(file_path),
                'file_size': file_size,
                'chapter_count': len(chapters),
                'chapters': chapters
            }

            logger.info(f"Successfully parsed novel: {novel_title} with {len(chapters)} chapters")
            return novel_data

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
            return None

    def _extract_chapters(self, content):
        """
        Extract chapters and their content from the novel text.

        Args:
            content: The full text content of the novel

        Returns:
            list: A list of chapter dictionaries with title and content
        """
        # Split content into lines for line-by-line processing
        lines = content.split('\n')

        # Find all chapter headings and their positions
        chapter_positions = []

        for i, line in enumerate(lines):
            line_no_space = line.replace(' ', '')

            # Skip empty lines
            if not line:
                continue

            # Check if the line matches any of our chapter patterns
            # We need to use re.fullmatch to ensure the entire line matches the pattern
            if any(re.fullmatch(pattern, line_no_space) for pattern in self.CHAPTER_PATTERNS):
                chapter_positions.append((i, line))

        # If no chapters found, treat the entire content as a single chapter
        if not chapter_positions:
            return [{
                'title': '全文',
                'content': content.strip()
            }]

        # Process chapters
        chapters = []

        # Process each chapter
        for i, (line_num, chapter_title) in enumerate(chapter_positions):
            # Determine the start line for the chapter content (next line after the title)
            start_line = line_num + 1

            # Determine the end line (start of next chapter or end of content)
            if i < len(chapter_positions) - 1:
                end_line = chapter_positions[i + 1][0]
            else:
                end_line = len(lines)

            # Extract chapter content
            chapter_content = '\n'.join(lines[start_line:end_line]).strip()

            chapters.append({
                'title': chapter_title,
                'content': chapter_content
            })

        return chapters

