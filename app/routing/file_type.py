"""File type resolver - the "File type resolver -> pdf, docx, ppt, word, excel" box.
Uses magic bytes first (so a wrongly named file still works), extension second."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path


class UnsupportedFileType(Exception):
    pass


EXT_MAP = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".pptx": "pptx",
    ".xlsx": "xlsx", ".xlsm": "xlsx",
    ".csv": "csv", ".tsv": "csv",
    ".txt": "text", ".md": "text", ".log": "text",
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".tif": "image",
    ".tiff": "image", ".bmp": "image", ".gif": "image", ".webp": "image",
}
LEGACY = {".doc": "docx", ".ppt": "pptx", ".xls": "xlsx"}


def resolve_file_type(data: bytes, file_name: str) -> str:
    head = data[:16]
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith((b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"BM", b"II*\x00", b"MM\x00*")) or (
        head[:4] == b"RIFF" and data[8:12] == b"WEBP"
    ):
        return "image"
    if head.startswith(b"PK"):  # OOXML containers are zip files
        try:
            names = zipfile.ZipFile(io.BytesIO(data)).namelist()
            if any(n.startswith("word/") for n in names):
                return "docx"
            if any(n.startswith("ppt/") for n in names):
                return "pptx"
            if any(n.startswith("xl/") for n in names):
                return "xlsx"
        except zipfile.BadZipFile:
            pass
    if head.startswith(b"\xd0\xcf\x11\xe0"):  # legacy OLE2: .doc/.ppt/.xls
        ext = Path(file_name).suffix.lower()
        raise UnsupportedFileType(
            f"Legacy Office format ({ext or 'OLE2'}). Convert to {LEGACY.get(ext, 'docx/pptx/xlsx')} "
            "first (e.g. `libreoffice --headless --convert-to docx file.doc`)."
        )

    ext = Path(file_name).suffix.lower()
    if ext in EXT_MAP:
        return EXT_MAP[ext]
    raise UnsupportedFileType(f"Unsupported file type: '{ext or 'unknown'}'")
