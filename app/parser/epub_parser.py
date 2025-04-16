import logging
import re
from pathlib import Path
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EpubParser:
    """
    Parser for EPUB novel files that extracts chapters and their content.
    """

    def __init__(self):
        """Initialize the EPUB parser."""
        pass

    def parse_file(self, file_path):
        """
        Parse an EPUB file and extract chapters and their content.

        Args:
            file_path: Path to the EPUB file

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

            # Read the EPUB file
            book = epub.read_epub(str(file_path))

            # Extract metadata
            novel_title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else file_path.stem
            author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else None

            # If no author in metadata, try to extract from filename (same as TXT parser)
            if not author:
                author_pattern = re.compile(r'(.+)\s作者：(.+)')
                match = author_pattern.match(file_path.stem)
                if match:
                    novel_title = match.group(1).strip()
                    author = match.group(2).strip()

            # Extract chapters from the EPUB's table of contents
            chapters = self._extract_chapters(book)

            # Create novel metadata
            novel_data = {
                'title': novel_title,
                'author': author,
                'file_path': str(file_path),
                'file_size': file_size,
                'chapter_count': len(chapters),
                'chapters': chapters
            }

            logger.info(f"Successfully parsed EPUB: {novel_title} with {len(chapters)} chapters")
            return novel_data

        except Exception as e:
            logger.error(f"Error parsing EPUB file {file_path}: {str(e)}")
            return None

    def _extract_chapters(self, book):
        """
        Extract chapters and their content from the EPUB book.

        Args:
            book: The ebooklib Book object

        Returns:
            list: A list of chapter dictionaries with title and content
        """
        chapters = []
        toc = book.toc

        # Check if there's content before the first chapter (cover, introduction, etc.)
        # For EPUB, we'll look at the first item in the spine
        if book.spine and len(book.spine) > 0:
            first_item_id = book.spine[0]
            first_item = book.get_item_with_id(first_item_id)

            if first_item and first_item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Extract content from the first item
                first_content = self._clean_html_content(first_item.get_content())

                # Check if this is likely to be a cover or introduction
                # by looking for common patterns in the content
                if len(first_content) > 0 and not any(marker in first_content.lower()
                                                    for marker in ['chapter', '章', '节']):
                    # This looks like introductory content, add it as "简介"
                    chapters.append({
                        'title': '简介',
                        'content': first_content
                    })
                    logger.info(f"Added first EPUB item as '简介' chapter with {len(first_content)} characters")

        # If the book has a table of contents, use it
        if toc:
            toc_chapters = self._process_toc(book, toc)
            # If we already have a "简介" chapter, append the TOC chapters
            if chapters and chapters[0]['title'] == '简介':
                chapters.extend(toc_chapters)
            else:
                chapters = toc_chapters
            logger.info(f"Extracted {len(toc_chapters)} chapters from table of contents")
        else:
            # If no TOC, try to extract chapters from the spine
            spine_chapters = self._process_spine(book)
            # If we already have a "简介" chapter, append the spine chapters
            if chapters and chapters[0]['title'] == '简介':
                chapters.extend(spine_chapters)
            else:
                chapters = spine_chapters
            logger.info(f"Extracted {len(spine_chapters)} chapters from spine")

        # If still no chapters found, treat the entire book as a single chapter
        if not chapters:
            content = self._extract_all_content(book)
            chapters = [{
                'title': '全文',
                'content': content
            }]

        return chapters

    def _process_toc(self, book, toc, level=0):
        """
        Process the table of contents recursively.

        Args:
            book: The ebooklib Book object
            toc: The table of contents (list or tuple)
            level: Current nesting level

        Returns:
            list: A list of chapter dictionaries
        """
        chapters = []

        for item in toc:
            if isinstance(item, tuple):
                # This is a section with subsections
                section_title, section_href, section_children = item

                # Add the section as a chapter
                if section_href:
                    content = self._extract_item_content(book, section_href, section_title)
                    chapters.append({
                        'title': section_title,
                        'content': content
                    })

                # Process children recursively
                if section_children:
                    child_chapters = self._process_toc(book, section_children, level + 1)
                    chapters.extend(child_chapters)

            elif isinstance(item, epub.Link):
                # This is a direct link to a chapter
                content = self._extract_item_content(book, item.href, item.title)
                chapters.append({
                    'title': item.title,
                    'content': content
                })

        return chapters

    def _process_spine(self, book):
        """
        Process the book's spine to extract chapters when no TOC is available.

        Args:
            book: The ebooklib Book object

        Returns:
            list: A list of chapter dictionaries
        """
        chapters = []

        # Skip the first item if we've already processed it as a "简介" chapter
        start_index = 1 if (book.spine and len(book.spine) > 0 and
                            any(marker not in self._clean_html_content(book.get_item_with_id(book.spine[0]).get_content()).lower()
                                for marker in ['chapter', '章', '节'])) else 0

        for i, item_id in enumerate(book.spine):
            # Skip the first item if we're starting from index 1
            if i < start_index:
                continue

            item = book.get_item_with_id(item_id)
            if item is not None and item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Try to extract title from the HTML content
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                title_tag = soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                title = title_tag.get_text().strip() if title_tag else f"Chapter {len(chapters) + 1}"

                # Get content and remove the title
                content = self._clean_html_content(item.get_content())
                content = self._remove_title_from_content(content, title)

                chapters.append({
                    'title': title,
                    'content': content
                })

        return chapters

    def _extract_item_content(self, book, href, title=None):
        """
        Extract content from an item in the EPUB book.

        Args:
            book: The ebooklib Book object
            href: The href of the item
            title: The title to remove from content (optional)

        Returns:
            str: The text content of the item with title removed
        """
        item = book.get_item_with_href(href)
        if item is None:
            return ""

        content = self._clean_html_content(item.get_content())

        # Remove the title from the content if provided
        if title:
            content = self._remove_title_from_content(content, title)

        return content

    def _clean_html_content(self, html_content):
        """
        Clean HTML content and extract text.

        Args:
            html_content: The HTML content as bytes

        Returns:
            str: The cleaned text content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Special handling for headings - we'll process them separately
            # to help with title removal later
            heading_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for tag in heading_tags:
                # We don't remove them here, but we'll make them easier to identify
                # by adding newlines around them
                if tag.string:
                    tag.insert_before(soup.new_string('\n'))
                    tag.insert_after(soup.new_string('\n'))

            # Get text
            text = soup.get_text()

            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())

            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return text
        except Exception as e:
            logger.error(f"Error cleaning HTML content: {str(e)}")
            return ""

    def _remove_title_from_content(self, content, title):
        """
        Remove the title from the content.

        Args:
            content: The content text
            title: The title to remove

        Returns:
            str: Content with title removed
        """
        if not content or not title:
            return content

        # Try exact match first
        if content.startswith(title):
            # Remove the title and any whitespace/newlines immediately after it
            content = content[len(title):].lstrip()
            return content

        # Try case-insensitive match
        title_lower = title.lower()
        content_lower = content.lower()
        if content_lower.startswith(title_lower):
            # Find the actual title in the original content (preserving case)
            actual_title = content[:len(title)]
            content = content[len(actual_title):].lstrip()
            return content

        # Try to find the title with some flexibility (e.g., with chapter prefix/suffix)
        lines = content.split('\n', 5)  # Split into at most 5 parts to check first few lines

        # Check the first few lines for the title
        for i, line in enumerate(lines[:3]):  # Check first three lines
            # Exact match
            if line.strip() == title.strip():
                return '\n'.join(lines[i+1:]).lstrip()

            # Title is contained in the line
            if title in line:
                return '\n'.join(lines[i+1:]).lstrip()

            # Case-insensitive match
            if title.lower() in line.lower():
                return '\n'.join(lines[i+1:]).lstrip()

        # If we have at least 2 lines and the first line looks like a heading
        # (short line followed by a blank line), remove it
        if len(lines) >= 2 and len(lines[0].strip()) < 100 and not lines[1].strip():
            return '\n'.join(lines[2:]).lstrip()

        return content

    def _extract_all_content(self, book):
        """
        Extract all content from the EPUB book.

        Args:
            book: The ebooklib Book object

        Returns:
            str: The full text content of the book
        """
        all_content = []

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = self._clean_html_content(item.get_content())
                all_content.append(content)

        return '\n\n'.join(all_content)
