from __future__ import annotations

from pathlib import Path
from typing import Union, IO
import base64
import shutil
import uuid

from fastapi import UploadFile


class StorageError(Exception):
    pass


class FileStorage:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self._ensure_base_dir()

    def _ensure_base_dir(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, filepath: str) -> Path:
        safe_path = Path(filepath).as_posix().lstrip("/")
        return self.base_dir / safe_path

    def _ensure_dir(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

    async def write(
        self,
        file_object: Union[UploadFile, bytes, str, IO[bytes], Path],
        filepath: str,
    ) -> str:
        path = self._resolve_path(filepath)
        self._ensure_dir(path)

        file_type = type(file_object).__name__

        if file_type == "UploadFile" or (
            hasattr(file_object, "filename") and hasattr(file_object, "file")
        ):
            await self._save_upload(file_object, path)

        elif isinstance(file_object, bytes):
            self._save_bytes(file_object, path)

        elif isinstance(file_object, str):
            self._save_string(file_object, path)

        elif isinstance(file_object, Path):
            self._save_path(file_object, path)

        elif hasattr(file_object, "read"):
            self._save_stream_sync(file_object, path)

        else:
            raise StorageError(f"Unsupported file type: {type(file_object)}")

        return str(path)

    async def save(self, file_object: Union[UploadFile, bytes, str, IO[bytes], Path], basename_uuid: str) -> str:
        extension = Path(file_object.filename).suffix if file_object.filename else ""
        filename = f"{basename_uuid}{extension}"
        return await self.write(file_object, filename)

    async def _save_upload(self, file: UploadFile, path: Path) -> None:
        try:
            if hasattr(file, "file") and hasattr(file.file, "seek"):
                file.file.seek(0)

            with path.open("wb") as buffer:
                while True:
                    chunk = await file.read(8192)
                    if not chunk:
                        break
                    buffer.write(chunk)

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
        try:
            with path.open("wb") as buffer:
                shutil.copyfileobj(stream, buffer)
        except Exception as e:
            raise StorageError(f"Failed to save stream: {e}") from e

    def _save_path(self, src: Path, dest: Path) -> None:
        if not src.exists():
            raise StorageError(f"Source file does not exist: {src}")
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

    def delete(self, filepath: str) -> None:
        path = self._resolve_path(filepath)
        if path.exists():
            path.unlink()

    def exists(self, filepath: str) -> bool:
        return self._resolve_path(filepath).exists()

    def read(self, filepath: str) -> bytes:
        return self._resolve_path(filepath).read_bytes()

    def get_full_path(self, filepath: str) -> Path:
        return self._resolve_path(filepath)

    def list_files(self, directory: str = "") -> list[Path]:
        search_path = self._resolve_path(directory)
        if not search_path.exists():
            return []
        return [f for f in search_path.rglob("*") if f.is_file()]
