import re
from pathlib import Path
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

from ..models.base import NovelMetadata, ChapterMetadata


class EpubParser:
    def parse_file(self, file_path: Path) -> NovelMetadata | None:
        file_path = Path(file_path)
        if not file_path.exists():
            return None

        book = epub.read_epub(str(file_path))

        title, author = self._extract_metadata(book, file_path)
        chapters = self._extract_chapters(book)

        return NovelMetadata(
            title=title,
            author=author,
            file_path=str(file_path),
            chapter_count=len(chapters),
            chapters=chapters
        )

    def _extract_metadata(self, book, file_path: Path) -> tuple[str, str | None]:
        title_meta = book.get_metadata('DC', 'title')
        title = title_meta[0][0] if title_meta else file_path.stem

        author_meta = book.get_metadata('DC', 'creator')
        author = author_meta[0][0] if author_meta else None

        if not author:
            author_pattern = re.compile(r'(.+)\s作者：(.+)')
            match = author_pattern.match(file_path.stem)
            if match:
                title = match.group(1).strip()
                author = match.group(2).strip()

        return title, author

    def _extract_chapters(self, book) -> list[ChapterMetadata]:
        chapters = []
        chapter_index = 0

        # Get spine items in reading order
        spine_items = [book.get_item_with_id(item_id)
                      for item_id, _ in book.spine]

        # Extract chapters in spine order
        for item in spine_items:
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Get chapter title
                content = item.get_content()
                try:
                    html_content = content.decode('utf-8')
                except UnicodeDecodeError:
                    html_content = content.decode('gb18030')

                soup = BeautifulSoup(html_content, 'html.parser')
                title_tag = soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                title = title_tag.get_text().strip() if title_tag else f"第{chapter_index + 1}章"

                chapters.append(ChapterMetadata(
                    title=title,
                    chapter_index=chapter_index,
                    spine_id=item.id  # Store spine ID separately
                ))
                chapter_index += 1

        return chapters

    def get_chapter_content(self, file_path: Path, chapter_id: str) -> str | None:
        """Get chapter content by chapter ID"""
        try:
            book = epub.read_epub(str(file_path))
            item = book.get_item_with_id(chapter_id)
            if not item or item.get_type() != ebooklib.ITEM_DOCUMENT:
                return None

            content = item.get_content()
            try:
                return self._clean_html_content(content.decode('utf-8'))
            except UnicodeDecodeError:
                return self._clean_html_content(content.decode('gb18030'))
        except Exception:
            return None

    def _clean_html_content(self, html_content: str | bytes) -> str:
        # Handle both str and bytes input
        if isinstance(html_content, bytes):
            try:
                html_content = html_content.decode('utf-8')
            except UnicodeDecodeError:
                html_content = html_content.decode('gb18030')

        soup = BeautifulSoup(html_content, 'html.parser')

        # 移除脚本和样式标签
        for script in soup(["script", "style"]):
            script.decompose()

        # 获取文本内容，保持段落结构
        text = soup.get_text()

        # 清理文本，保持换行结构
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line:  # 只保留非空行
                lines.append(line)

        # 用换行符连接，保持段落结构
        return '\n'.join(lines)




