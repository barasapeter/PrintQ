from __future__ import annotations

from pathlib import Path
from typing import Union, IO, Optional
import base64
import shutil
import uuid

from fastapi import UploadFile


class StorageError(Exception):
    pass


class FileStorage:
    """
    Local filesystem storage handler. all paths are relative to `base_dir`.
    """

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

    def _resolve_path(self, file_path: str) -> Path:
        """
        Convert a relative file path into an absolute safe path
        inside the base directory.
        """
        # normalize path to prevent traversal like ../
        safe_path = Path(file_path).as_posix().lstrip("/")
        return self.base_dir / safe_path

    def _ensure_dir(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

    async def save(
        self,
        file: Union[UploadFile, bytes, str, IO[bytes], Path],
        file_path: Optional[str] = None,
    ) -> str:
        """
        Save a file from multiple input types.

        Supported inputs:
        - UploadFile (FastAPI multipart upload)
        - bytes (raw binary)
        - str (base64 or data URI)
        - IO[bytes] (file-like stream)
        - Path (existing file on disk)

        Returns:
            str: saved file path (relative to base_dir)
        """

        if file_path is None:
            file_path = f"{uuid.uuid4().hex}"

        path = self._resolve_path(file_path)
        self._ensure_dir(path)

        # Check for UploadFile by class name or type
        # This is more reliable than isinstance in some cases
        file_type = type(file).__name__

        if (
            file_type == "UploadFile"
            or hasattr(file, "filename")
            and hasattr(file, "file")
        ):
            await self._save_upload(file, path)
        elif isinstance(file, bytes):
            self._save_bytes(file, path)
        elif isinstance(file, str):
            self._save_string(file, path)
        elif isinstance(file, Path):
            self._save_path(file, path)
        elif hasattr(file, "read"):
            # Synchronous stream
            self._save_stream_sync(file, path)
        else:
            raise StorageError(f"Unsupported file type: {type(file)}")

        return str(path)

    async def _save_upload(self, file: UploadFile, path: Path) -> None:
        """Save UploadFile asynchronously by reading chunks."""
        try:
            # Reset file position to beginning if seeking is supported
            if hasattr(file, "file") and hasattr(file.file, "seek"):
                file.file.seek(0)

            with path.open("wb") as buffer:
                # Read file in chunks asynchronously
                while True:
                    chunk = await file.read(8192)
                    if not chunk:
                        break
                    buffer.write(chunk)

            # Reset for any future reads
            if hasattr(file, "file") and hasattr(file.file, "seek"):
                file.file.seek(0)

        except Exception as e:
            raise StorageError(f"Failed to save upload: {e}") from e

    def _save_bytes(self, data: bytes, path: Path) -> None:
        try:
            with path.open("wb") as f:
                f.write(data)
        except Exception as e:
            raise StorageError(f"Failed to save bytes: {e}") from e

    def _save_stream_sync(self, stream: IO[bytes], path: Path) -> None:
        """Save synchronous file-like object to disk."""
        try:
            with path.open("wb") as buffer:
                shutil.copyfileobj(stream, buffer)
        except Exception as e:
            raise StorageError(f"Failed to save stream: {e}") from e

    def _save_path(self, src: Path, dest: Path) -> None:
        """copy an existing file into storage."""
        if not src.exists():
            raise StorageError("Source file does not exist")
        try:
            shutil.copy2(src, dest)
        except Exception as e:
            raise StorageError(f"Failed to copy file: {e}") from e

    def _save_string(self, data: str, path: Path) -> None:
        try:
            decoded = self._decode_base64(data)
            with path.open("wb") as f:
                f.write(decoded)
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to save string: {e}") from e

    def _decode_base64(self, data: str) -> bytes:
        try:
            if "," in data:
                data = data.split(",", 1)[1]

            return base64.b64decode(data, validate=False)

        except Exception as e:
            raise StorageError("Invalid base64 input") from e

    def delete(self, file_path: str) -> None:
        path = self._resolve_path(file_path)
        if path.exists():
            path.unlink()

    def exists(self, file_path: str) -> bool:
        return self._resolve_path(file_path).exists()

    def read(self, file_path: str) -> bytes:
        """Read file contents as bytes."""
        return self._resolve_path(file_path).read_bytes()
