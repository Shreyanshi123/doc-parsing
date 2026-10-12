from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from typing import Iterable, Sequence


def _cell(v) -> str:
    s = "" if v is None else str(v)
    return s.replace("|", "\\|").replace("\r", " ").replace("\n", "<br>").strip()


def rows_to_markdown(rows: Sequence[Sequence]) -> str:
    """Convert a list-of-rows into a GitHub-style Markdown table (first row = header)."""
    rows = [list(r) for r in rows if r is not None]
    rows = [r for r in rows if any(str(c).strip() for c in r if c is not None)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    header, body = rows[0], rows[1:]
    lines = ["| " + " | ".join(_cell(c) for c in header) + " |", "|" + "---|" * width]
    lines += ["| " + " | ".join(_cell(c) for c in r) + " |" for r in body]
    return "\n".join(lines)


def limit_pages(total: int, max_pages) -> int:
    return min(total, max_pages) if max_pages else total


@contextmanager
def temp_file(data: bytes, suffix: str):
    """Some libraries only accept a file path; write bytes to a temp file and clean up afterwards."""
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        f.write(data)
        f.close()
        yield f.name
    finally:
        try:
            os.unlink(f.name)
        except OSError:
            pass
