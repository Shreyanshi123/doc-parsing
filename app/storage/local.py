"""Local file reader. Used for the "I upload the file myself" POC mode."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse, unquote

from app.config import settings
from app.storage.base import StorageAdapter, StorageError


class LocalStorage(StorageAdapter):
    def _allowed_roots(self) -> list[Path]:
        roots = [Path(r).resolve() for r in settings.local_allowed_roots]
        roots.append(settings.uploads_dir.resolve())
        return roots

    def read(self, uri: str) -> bytes:
        if uri.startswith("file://"):
            uri = unquote(urlparse(uri).path)
        path = Path(uri).resolve()
        # Safety: only read inside allowed folders (prevents "../../etc/passwd" style requests)
        if not any(path == r or r in path.parents for r in self._allowed_roots()):
            raise StorageError(f"Path not inside LOCAL_ALLOWED_ROOTS: {path}")
        if not path.is_file():
            raise StorageError(f"File not found: {path}")
        return path.read_bytes()
