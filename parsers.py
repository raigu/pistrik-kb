"""Document parsers. Each takes a file path (or string for HTML), returns plain text."""

from pathlib import Path

import pymupdf
from docx import Document
from markdownify import markdownify
from bs4 import BeautifulSoup


SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx", ".html"}


def parse_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_html(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return markdownify(str(soup)).strip()


def parse_pdf(path: Path) -> str:
    doc = pymupdf.open(str(path))
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts).strip()


def parse_docx(path: Path) -> str:
    doc = Document(str(path))
    parts = []
    for para in doc.paragraphs:
        if para.style.name.startswith("Heading"):
            level = para.style.name.replace("Heading ", "")
            try:
                prefix = "#" * int(level) + " "
            except ValueError:
                prefix = "# "
            parts.append(f"{prefix}{para.text}")
        else:
            parts.append(para.text)
    return "\n\n".join(parts).strip()


def parse_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


_DISPATCH = {
    ".md": parse_markdown,
    ".txt": parse_text,
    ".pdf": parse_pdf,
    ".docx": parse_docx,
}


def parse_file(path: Path) -> str:
    path = Path(path)
    ext = path.suffix.lower()
    parser = _DISPATCH.get(ext)
    if parser is None:
        raise ValueError(f"Unsupported file format: {ext}")
    return parser(path)
