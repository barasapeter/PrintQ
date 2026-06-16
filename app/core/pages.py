"""
`page_count` for document page counting. Call `count_pages(filepath)`, returns:
int, the number of pages/sheets/slides found in the document.
Validates the document first via `validate_document`; raises the same
`NoPrintableContentError` on invalid or unsupported files.

Supported types: pdf, docx, xlsx, pptx, txt, csv, html, xml, rtf
Page semantics per type:
  - pdf   → number of PDF pages
  - docx  → number of pages (via w:sectPr / page-break heuristic)
  - xlsx  → number of visible worksheets
  - pptx  → number of slides
  - txt / csv / html / xml / rtf → lines divided by a configurable page size
                                   (default: 50 lines per page, min 1)
"""

from __future__ import annotations

import math
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from openpyxl import load_workbook
from pptx import Presentation
from pypdf import PdfReader

from app.core.dtypes import validate_document, NoPrintableContentError

LINES_PER_PAGE: int = 50


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
        return len(breaks) + 1

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
        return len(Presentation(filepath).slides)
    except Exception as e:
        raise NoPrintableContentError(f"Could not read PPTX slides: {e}") from e


def _count_text(filepath: str) -> int:
    """Estimates pages from line count using LINES_PER_PAGE."""
    try:
        lines = Path(filepath).read_text(errors="ignore").splitlines()
        non_empty = [l for l in lines if l.strip()]
        return max(math.ceil(len(non_empty) / LINES_PER_PAGE), 1)
    except Exception as e:
        raise NoPrintableContentError(f"Could not read text file: {e}") from e


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
}


def count_pages(filepath: str) -> int:
    file_type = validate_document(filepath)

    counter = _COUNTERS.get(file_type)
    if not counter:
        raise NoPrintableContentError(
            f"Page counting not implemented for '{file_type}'"
        )

    return counter(filepath)


if __name__ == "__main__":
    import sys

    path = "brainstorm/2025_2026 final_project_proposals Comp 493.xlsx"
    try:
        pages = count_pages(path)
        print(f"{path}: {pages} page(s)")
    except NoPrintableContentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
