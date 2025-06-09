import re
from pathlib import Path
from ..models.base import NovelMetadata, ChapterMetadata


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


class NovelParser:
    CHAPTER_PATTERNS = [
        r'^第[\d〇零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟]+[章节回卷].{0,30}$',
        r'^[序终尾楔引前后][章言声子记].{0,30}$',
        r'^(正文|番外).{0,30}$',
        r'^[上中下外][部篇卷].{0,30}$',
        r'^\d{1,4}[^\.：、&].{0,30}$',
        r'^Chapter.{0,30}$',
        r'^[☆★].{0,30}$',
        r'^卷[\d〇零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟]+.{0,30}$'
    ]

    def parse_file(self, file_path: Path) -> NovelMetadata | None:
        file_path = Path(file_path)
        if not file_path.exists():
            return None

        content = FileReader.read_full_content(file_path)
        if not content:
            return None

        novel_title, author = self._extract_title_author(file_path)
        chapters = self._extract_chapters_with_lines(content)

        return NovelMetadata(
            title=novel_title,
            author=author,
            file_path=str(file_path),
            chapter_count=len(chapters),
            chapters=chapters
        )

    def _extract_title_author(self, file_path: Path) -> tuple[str, str | None]:
        file_name = file_path.stem
        author_pattern = re.compile(r'(.+)\s作者：(.+)')
        match = author_pattern.match(file_name)

        if match:
            return match.group(1).strip(), match.group(2).strip()
        return file_name, None

    def _extract_chapters_with_lines(self, content: str) -> list[ChapterMetadata]:
        lines = content.split('\n')
        chapter_positions = []

        for i, line in enumerate(lines):
            line = line.strip()
            if any(re.fullmatch(pattern, line) for pattern in self.CHAPTER_PATTERNS):
                chapter_positions.append((i, line))

        if not chapter_positions:  # If no chapters found, treat the entire content as a single chapter
            return [ChapterMetadata(
                title='正文',
                start_line=0,
                end_line=len(lines),
                chapter_index=0
            )]

        chapters = []
        for i, (line_num, chapter_title) in enumerate(chapter_positions):
            start_line = line_num + 1  # Content starts after chapter title

            if i < len(chapter_positions) - 1:
                end_line = chapter_positions[i + 1][0]  # Ends at next chapter title
            else:
                end_line = len(lines)  # Last chapter ends at end of file

            chapters.append({
                'title': chapter_title,
                'start_line': start_line,
                'end_line': end_line
            })

        if chapter_positions[0][0] > 0:  # Add intro if there are lines before first chapter
            chapters.insert(0, {
                'title': '简介',
                'start_line': 0,
                'end_line': chapter_positions[0][0]
            })

        return [
            ChapterMetadata(
                title=chapter_info['title'],
                start_line=chapter_info['start_line'],
                end_line=chapter_info['end_line'],
                chapter_index=i
            )
            for i, chapter_info in enumerate(chapters)
        ]
