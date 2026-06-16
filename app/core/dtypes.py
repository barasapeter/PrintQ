"""
`dtypes` for `document_types`. Call `validate_document(filepath)`, returns:
string, eg "pdf" as values declared on `MIME_MAP` dictionary.
Else: Raises an error for unprintable documents.
"""

from pathlib import Path
import mimetypes
import zipfile
import xml.etree.ElementTree as ET

from openpyxl import load_workbook
from pptx import Presentation

import magic
from pypdf import PdfReader


MIME_MAP = {
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.ms-powerpoint": "ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/vnd.ms-excel": "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.oasis.opendocument.text": "odt",
    "application/vnd.oasis.opendocument.presentation": "odp",
    "application/vnd.oasis.opendocument.spreadsheet": "ods",
    "application/rtf": "rtf",
    "text/rtf": "rtf",
    "text/plain": "txt",
    "text/csv": "csv",
    "text/html": "html",
    "application/xml": "xml",
    "text/xml": "xml",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/tiff": "tiff",
    "image/bmp": "bmp",
    "image/svg+xml": "svg",
    "image/heic": "heic",
    "image/heif": "heif",
}


def _resolve_file_type(filepath: str) -> str | None:
    mime_type = magic.from_file(filepath, mime=True)
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(filepath)
        print("Mime Type:", mime_type)
    return MIME_MAP.get(mime_type)


class NoPrintableContentError(ValueError):
    pass


def _validate_text(filepath: str) -> None:
    try:
        text = Path(filepath).read_text(errors="ignore")
        if not text.strip():
            raise NoPrintableContentError("Document contains no printable content")
    except NoPrintableContentError:
        raise
    except Exception as e:
        raise NoPrintableContentError(f"Unable to read document: {e}") from e


def _validate_docx(filepath: str) -> None:
    try:
        with zipfile.ZipFile(filepath) as archive:
            xml_data = archive.read("word/document.xml")
        root = ET.fromstring(xml_data)
        text = "".join(
            node.text or "" for node in root.iter() if node.tag.endswith("}t")
        ).strip()
        if not text:
            raise NoPrintableContentError("DOCX contains no printable content")
    except NoPrintableContentError:
        raise
    except Exception as e:
        raise NoPrintableContentError(f"Invalid DOCX document: {e}") from e


def _validate_xlsx(filepath: str) -> None:
    try:
        workbook = load_workbook(filepath, read_only=True, data_only=True)
        for sheet in workbook.worksheets:
            for row in sheet.iter_rows(values_only=True):
                if any(value not in (None, "") for value in row):
                    return
        raise NoPrintableContentError("XLSX contains no printable content")
    except NoPrintableContentError:
        raise
    except Exception as e:
        raise NoPrintableContentError(f"Invalid XLSX document: {e}") from e


def _validate_pptx(filepath: str) -> None:
    try:
        presentation = Presentation(filepath)
        for slide in presentation.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    return
        raise NoPrintableContentError("PPTX contains no printable content")
    except NoPrintableContentError:
        raise
    except Exception as e:
        raise NoPrintableContentError(f"Invalid PPTX document: {e}") from e


def _validate_pdf(filepath: str) -> None:
    try:
        reader = PdfReader(filepath)
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                return
        raise NoPrintableContentError("PDF contains no printable text")
    except NoPrintableContentError:
        raise
    except Exception as e:
        raise NoPrintableContentError(f"Invalid PDF document: {e}") from e


_VALIDATORS = {
    "txt": _validate_text,
    "csv": _validate_text,
    "html": _validate_text,
    "xml": _validate_text,
    "rtf": _validate_text,
    "docx": _validate_docx,
    "xlsx": _validate_xlsx,
    "pptx": _validate_pptx,
    "pdf": _validate_pdf,
}


def validate_document(filepath: str) -> str:
    file_type = _resolve_file_type(filepath)

    if not file_type:
        raise NoPrintableContentError("Unsupported file type")

    validator = _VALIDATORS.get(file_type)

    if not validator:
        raise NoPrintableContentError(
            f"Printable-content validation not implemented for '{file_type}'"
        )

    validator(filepath)
    return file_type


if __name__ == "__main__":
    print(validate_document("Dockerfile"))
