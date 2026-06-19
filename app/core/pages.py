"""
`page_count` for document page counting. Call `count_pages(filepath)`, returns:
int, the number of pages/sheets/slides found in the document.
Validates the document first via `validate_document`; raises the same
`NoPrintableContentError` on invalid or unsupported files.

Supported types: pdf, docx, xlsx, pptx, txt, csv, html, xml, rtf, and all image types
Page semantics per type:
  - pdf   → number of PDF pages
  - docx  → number of pages (via w:sectPr / page-break heuristic)
  - xlsx  → number of visible worksheets
  - pptx  → number of slides
  - txt / csv / html / xml / rtf → lines divided by a configurable page size
                                   (default: 50 lines per page, min 1)
  - images (jpg, png, gif, etc.) → always returns 1 (single image)
"""

from __future__ import annotations

import math
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from openpyxl import load_workbook
from pptx import Presentation
from pypdf import PdfReader
from PIL import Image

from app.core.dtypes import validate_document, NoPrintableContentError

LINES_PER_PAGE: int = 50

# Image file types that we support
IMAGE_TYPES = {
    "jpg",
    "jpeg",
    "png",
    "gif",
    "webp",
    "tiff",
    "bmp",
    "svg",
    "heic",
    "heif",
    "ico",
}


def _count_pdf(filepath: str) -> int:
    try:
        return len(PdfReader(filepath).pages)
    except Exception as e:
        raise NoPrintableContentError(f"Could not read PDF pages: {e}") from e


def _count_docx(filepath: str) -> int:
    try:
        with zipfile.ZipFile(filepath) as archive:
            if "docProps/app.xml" in archive.namelist():
                app_xml = archive.read("docProps/app.xml")
                root = ET.fromstring(app_xml)
                for el in root.iter():
                    if el.tag.endswith("}Pages") or el.tag == "Pages":
                        try:
                            pages = int(el.text or 0)
                            if pages > 0:
                                return pages
                        except ValueError:
                            pass

            doc_xml = archive.read("word/document.xml")

        root = ET.fromstring(doc_xml)
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        breaks = root.findall(f".//{{{W}}}br[@{{{W}}}type='page']")
        return max(len(breaks) + 1, 1)

    except NoPrintableContentError:
        raise
    except Exception as e:
        raise NoPrintableContentError(f"Could not read DOCX pages: {e}") from e


def _count_xlsx(filepath: str) -> int:
    try:
        workbook = load_workbook(filepath, read_only=True, data_only=True)
        visible = [ws for ws in workbook.worksheets if ws.sheet_state != "hidden"]
        return max(len(visible), 1)
    except Exception as e:
        raise NoPrintableContentError(f"Could not read XLSX sheets: {e}") from e


def _count_pptx(filepath: str) -> int:
    try:
        return max(len(Presentation(filepath).slides), 1)
    except Exception as e:
        raise NoPrintableContentError(f"Could not read PPTX slides: {e}") from e


def _count_text(filepath: str) -> int:
    try:
        lines = Path(filepath).read_text(errors="ignore").splitlines()
        # Count non-empty lines, but if file is empty, still return 1
        non_empty = [l for l in lines if l.strip()]
        count = math.ceil(len(non_empty) / LINES_PER_PAGE) if non_empty else 1
        return max(count, 1)
    except Exception as e:
        raise NoPrintableContentError(f"Could not read text file: {e}") from e


def _count_image(filepath: str) -> int:
    """Images are single pages/documents."""
    try:
        # Verify the image is valid (already done in validate_document)
        with Image.open(filepath) as img:
            img.verify()
        return 1
    except Exception as e:
        raise NoPrintableContentError(f"Could not verify image: {e}") from e


_COUNTERS = {
    "pdf": _count_pdf,
    "docx": _count_docx,
    "xlsx": _count_xlsx,
    "pptx": _count_pptx,
    "txt": _count_text,
    "csv": _count_text,
    "html": _count_text,
    "xml": _count_text,
    "rtf": _count_text,
    # Image types
    "jpg": _count_image,
    "jpeg": _count_image,
    "png": _count_image,
    "gif": _count_image,
    "webp": _count_image,
    "tiff": _count_image,
    "bmp": _count_image,
    "svg": _count_image,
    "heic": _count_image,
    "heif": _count_image,
    "ico": _count_image,
}


def count_pages(filepath: str) -> int:
    """
    Count pages/units in a document.

    Args:
        filepath: Path to the document

    Returns:
        int: Number of pages/sheets/slides (minimum 1)

    Raises:
        NoPrintableContentError: If the document is corrupted or unsupported
    """
    file_type = validate_document(filepath)

    counter = _COUNTERS.get(file_type)
    if not counter:
        raise NoPrintableContentError(
            f"Page counting not implemented for '{file_type}'"
        )

    return counter(filepath)


if __name__ == "__main__":
    import sys

    test_files = [
        "brainstorm/2025_2026 final_project_proposals Comp 493.xlsx",
        "test.pdf",
        "test.docx",
        "test.pptx",
        "image.jpg",
        "empty.txt",
    ]

    for path in test_files:
        try:
            pages = count_pages(path)
            print(f"{path}: {pages} page(s)")
        except NoPrintableContentError as exc:
            print(f"Error with {path}: {exc}", file=sys.stderr)
        except FileNotFoundError:
            print(f"File not found: {path}", file=sys.stderr)
