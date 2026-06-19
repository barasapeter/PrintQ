"""
`dtypes` for `document_types`. Call `validate_document(filepath)`, returns:
string, eg "pdf" as values declared on `MIME_MAP` dictionary.
Else: Raises an error for corrupted/unreadable documents.
"""

from pathlib import Path
import mimetypes
import zipfile
import xml.etree.ElementTree as ET

from openpyxl import load_workbook
from pptx import Presentation

import magic
from pypdf import PdfReader
from PIL import Image


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
    "image/x-icon": "ico",
    "image/vnd.microsoft.icon": "ico",
}


def _resolve_file_type(filepath: str) -> str | None:
    mime_type = magic.from_file(filepath, mime=True)
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(filepath)
    return MIME_MAP.get(mime_type)


class NoPrintableContentError(ValueError):
    pass


def _validate_text(filepath: str) -> None:
    """Validate text files - accept if readable, reject only if corrupted"""
    try:
        Path(filepath).read_text(errors="ignore")
        # No need to check for content - empty text files are valid
    except Exception as e:
        raise NoPrintableContentError(f"Unable to read text document: {e}") from e


def _validate_docx(filepath: str) -> None:
    """Validate DOCX files - accept if readable, reject only if corrupted"""
    try:
        with zipfile.ZipFile(filepath) as archive:
            archive.read("word/document.xml")
        # No need to check for content - empty documents are valid
    except Exception as e:
        raise NoPrintableContentError(f"Invalid or corrupted DOCX document: {e}") from e


def _validate_xlsx(filepath: str) -> None:
    """Validate XLSX files - accept if readable, reject only if corrupted"""
    try:
        load_workbook(filepath, read_only=True, data_only=True)
        # No need to check for content - empty spreadsheets are valid
    except Exception as e:
        raise NoPrintableContentError(f"Invalid or corrupted XLSX document: {e}") from e


def _validate_pptx(filepath: str) -> None:
    """Validate PPTX files - accept if readable, reject only if corrupted"""
    try:
        Presentation(filepath)
        # No need to check for content - empty presentations are valid
    except Exception as e:
        raise NoPrintableContentError(f"Invalid or corrupted PPTX document: {e}") from e


def _validate_pdf(filepath: str) -> None:
    """Validate PDF files - accept if readable, reject only if corrupted"""
    try:
        PdfReader(filepath)
        # No need to check for content - PDFs can have no text and still be valid
    except Exception as e:
        raise NoPrintableContentError(f"Invalid or corrupted PDF document: {e}") from e


def _validate_image(filepath: str) -> None:
    """Validate image files - accept if readable, reject only if corrupted"""
    try:
        with Image.open(filepath) as img:
            img.verify()  # Verify integrity
        # Also try to actually load the image to catch more corruption issues
        with Image.open(filepath) as img:
            img.load()
    except Exception as e:
        raise NoPrintableContentError(f"Invalid or corrupted image file: {e}") from e


_VALIDATORS = {
    # Text-based formats
    "txt": _validate_text,
    "csv": _validate_text,
    "html": _validate_text,
    "xml": _validate_text,
    "rtf": _validate_text,
    # Office documents
    "docx": _validate_docx,
    "xlsx": _validate_xlsx,
    "pptx": _validate_pptx,
    "pdf": _validate_pdf,
    # Image formats
    "jpg": _validate_image,
    "png": _validate_image,
    "gif": _validate_image,
    "webp": _validate_image,
    "tiff": _validate_image,
    "bmp": _validate_image,
    "svg": _validate_image,
    "heic": _validate_image,
    "heif": _validate_image,
    "ico": _validate_image,
}


def validate_document(filepath: str) -> str:
    """
    Validate that a document is readable and not corrupted.
    
    Returns the file type extension if valid.
    Raises NoPrintableContentError if the file is corrupted or unreadable.
    
    Note: Empty files and files without text content are considered valid
    as long as they can be opened correctly.
    """
    file_type = _resolve_file_type(filepath)

    if not file_type:
        raise NoPrintableContentError("Unsupported or unrecognized file type")

    validator = _VALIDATORS.get(file_type)

    if not validator:
        raise NoPrintableContentError(
            f"Validation not implemented for '{file_type}'"
        )

    validator(filepath)
    return file_type


if __name__ == "__main__":
    # Test with various file types
    test_files = [
        "Dockerfile",  # Should fail - unsupported
        "empty.txt",   # Should pass - empty but readable
        "image.jpg",   # Should pass - valid image
        "document.pdf", # Should pass - valid PDF
    ]
    for test_file in test_files:
        try:
            print(f"{test_file}: {validate_document(test_file)}")
        except NoPrintableContentError as e:
            print(f"{test_file}: ERROR - {e}")