"""Document loaders (Task 1: PDF support, plus the original .txt support)."""

import logging
import re
from pathlib import Path
from typing import List, Tuple

from langchain_core.documents import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".txt"}

# pypdf logs harmless "Ignoring wrong pointing object" warnings for slightly malformed PDFs
logging.getLogger("pypdf").setLevel(logging.ERROR)


def clean_text(text: str) -> str:
    """Normalise whitespace produced by PDF text extraction."""
    text = text.replace("\x00", "").replace(" ", " ")
    text = re.sub(r"-\n(?=[a-z])", "", text)        # re-join hyphenated line breaks
    text = re.sub(r"[ \t]+", " ", text)              # collapse runs of spaces
    text = re.sub(r" *\n *", "\n", text)             # trim spaces around newlines
    text = re.sub(r"\n{3,}", "\n\n", text)           # at most one blank line
    return text.strip()


def load_pdf(path: Path) -> Tuple[List[Document], List[int]]:
    """Extract text page by page. Returns (documents, page numbers with no text).

    One Document per page keeps the page number in metadata so answers can cite it.
    Pages with no extractable text are usually scans or images and would need OCR.
    """
    reader = PdfReader(str(path))
    docs, empty_pages = [], []
    for page_no, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if len(text) < 20:
            empty_pages.append(page_no)
            continue
        docs.append(Document(
            page_content=text,
            metadata={"source": path.name, "page": page_no, "type": "pdf"},
        ))
    return docs, empty_pages


def load_txt(path: Path) -> List[Document]:
    text = clean_text(path.read_text(encoding="utf-8", errors="ignore"))
    return [Document(page_content=text, metadata={"source": path.name, "page": 0, "type": "txt"})]


def list_source_files(directory: Path) -> List[Path]:
    return sorted(
        p for p in Path(directory).iterdir()
        if p.is_file()
        and p.suffix.lower() in SUPPORTED_EXTENSIONS
        and not p.name.startswith(("~$", "."))   # skip Office lock files / hidden files
    )


def load_directory(directory: Path, verbose: bool = True) -> List[Document]:
    documents: List[Document] = []
    for path in list_source_files(directory):
        if path.suffix.lower() == ".pdf":
            docs, empty = load_pdf(path)
            if verbose:
                msg = f"  Loaded PDF: {path.name} ({len(docs)} pages with text)"
                if empty:
                    msg += f" - no extractable text on pages {empty} (would need OCR)"
                print(msg)
        else:
            docs = load_txt(path)
            if verbose:
                print(f"  Loaded TXT: {path.name}")
        documents.extend(docs)
    return documents
