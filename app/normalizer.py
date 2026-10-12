"""Markdown normalizer - "unifies engine output" so every engine produces comparable Markdown."""
from __future__ import annotations

import re

from app.models import IMAGE, ParsedDocument

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def normalize_markdown(text: str) -> str:
    if not text:
        return ""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = _CTRL.sub("", t)
    t = t.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    t = re.sub(r"[ \t]+\n", "\n", t)             # trailing spaces
    t = re.sub(r"(?<=\S)[ \t]{2,}(?=\S)", " ", t)  # runs of spaces inside lines
    t = re.sub(r"\n{3,}", "\n\n", t)              # max one blank line
    # make sure headings are separated from the previous paragraph
    t = re.sub(r"([^\n])\n(#{1,6} )", r"\1\n\n\2", t)
    return t.strip()


def normalize_document(doc: ParsedDocument) -> ParsedDocument:
    for page in doc.pages:
        kept = []
        for el in page.elements:
            el.content = normalize_markdown(el.content)
            if el.content_type != IMAGE and not el.content:
                continue  # drop empty text elements
            el.metadata.setdefault("engine", doc.engine)
            el.metadata.setdefault("file_name", doc.file_name)
            kept.append(el)
        page.elements = kept
    doc.pages.sort(key=lambda p: p.page_number)
    return doc
