from fastapi import APIRouter, HTTPException, Query, Depends, Path as FastAPIPath
from fastapi.responses import FileResponse
from pathlib import Path
import mimetypes
import os
import urllib.parse
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db_session
from app.services.workorders import PrintJobService


router = APIRouter()

FILE_DIRECTORY = Path("./storage")
os.makedirs(FILE_DIRECTORY, exist_ok=True)

MIME_TYPES = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".rtf": "application/rtf",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".csv": "text/csv",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".odp": "application/vnd.oasis.opendocument.presentation",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".txt": "text/plain",
    ".html": "text/html",
    ".htm": "text/html",
    ".json": "application/json",
    ".xml": "application/xml",
    ".zip": "application/zip",
}

for ext, mime_type in MIME_TYPES.items():
    mimetypes.add_type(mime_type, ext)

INLINE_VIEWABLE = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/rtf",
    "text/html",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.oasis.opendocument.text",
    "application/vnd.oasis.opendocument.spreadsheet",
    "application/vnd.oasis.opendocument.presentation",
}

desc = "Set to true to force download instead of view"
download_query = Query(False, description=desc)


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


@router.get("/{workorder_uuid}")
async def serve_file(
    workorder_uuid: str = FastAPIPath(..., description="The UUID of the workorder"),
    download: bool = download_query,
    db: AsyncSession = Depends(get_db_session),
):
    if not is_valid_uuid(workorder_uuid):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid resource identifier: '{workorder_uuid}' is not a valid UUID",
        )

    printjob_service = PrintJobService(db)
    printjob = await printjob_service.get(workorder_uuid)

    if not printjob:
        raise HTTPException(
            status_code=404,
            detail=f"Workorder with UUID '{workorder_uuid}' does not exist.",
        )

    if not hasattr(printjob, "properties") or not printjob.properties:
        raise HTTPException(status_code=400, detail="Printjob properties not found")

    file_metadata = printjob.properties.get("file_metadata")
    if not file_metadata:
        raise HTTPException(
            status_code=400, detail="File metadata not found in printjob properties"
        )

    original_filename = file_metadata.get("filename")
    if not original_filename:
        raise HTTPException(
            status_code=400, detail="Filename not found in file metadata"
        )

    file_extension = Path(original_filename).suffix.lower()
    file_path = (
        FILE_DIRECTORY
        / str(printjob.customer_uuid)
        / f"{str(printjob.uuid)}{file_extension}"
    )

    try:
        resolved_path = file_path.resolve()
        storage_dir = FILE_DIRECTORY.resolve()
        if not str(resolved_path).startswith(str(storage_dir)):
            raise HTTPException(status_code=400, detail="Invalid file path")
    except (OSError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid file path: {str(e)}")

    if not resolved_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not resolved_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    content_type, _ = mimetypes.guess_type(str(resolved_path))
    if not content_type:
        content_type = "application/octet-stream"

    if download:
        disposition = "attachment"
    else:
        is_viewable = content_type in INLINE_VIEWABLE or file_extension in MIME_TYPES
        disposition = "inline" if is_viewable else "attachment"

    encoded_filename = urllib.parse.quote(original_filename)

    return FileResponse(
        path=str(resolved_path),
        filename=original_filename,
        media_type=content_type,
        headers={
            "Content-Disposition": (
                f"{disposition}; "
                f'filename="{encoded_filename}"; '
                f"filename*=UTF-8''{encoded_filename}"
            ),
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=3600",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox",
        },
    )
