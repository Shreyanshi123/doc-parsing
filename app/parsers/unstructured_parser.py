"""
Unstructured (open source): element-level partitioning (Title, NarrativeText, ListItem, Table...).
Heavy optional install:  pip install "unstructured[pdf,docx,pptx,xlsx]"
Uses the default 'auto' strategy (fast for digital PDFs; may call OCR/layout models for scans if those extras exist).
"""
from __future__ import annotations

import io
from html.parser import HTMLParser

from app.config import settings
from app.models import TABLE, TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register
from app.parsers.utils import rows_to_markdown


class _TableHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self._row, self._cell, self._in = [], None, [], False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._cell, self._in = [], True

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._row is not None:
            self._row.append("".join(self._cell).strip()); self._in = False
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row); self._row = None

    def handle_data(self, data):
        if self._in:
            self._cell.append(data)


def html_table_to_markdown(html: str) -> str:
    p = _TableHTML()
    p.feed(html)
    return rows_to_markdown(p.rows)


@register
class UnstructuredParser(BaseParser):
    name = "unstructured"
    description = "Unstructured partition(): element types (titles, lists, tables) with page numbers. Heavy optional install."
    supported_types = {"pdf", "docx", "pptx", "xlsx", "csv", "text", "image"}

    @classmethod
    def is_available(cls):
        try:
            import unstructured.partition.auto  # noqa: F401
            return True, ""
        except ImportError:
            return False, 'pip install "unstructured[pdf,docx,pptx,xlsx]" (optional, large)'

    def parse(self, data, file_name, file_type, options):
        # Unstructured uses its own pytesseract package for OCR. Point it at the
        # same executable configured for this app, which may not be on PATH.
        if settings.tesseract_cmd:
            import unstructured_pytesseract.pytesseract as tesseract

            tesseract.tesseract_cmd = settings.tesseract_cmd

        from unstructured.partition.auto import partition

        elements = partition(file=io.BytesIO(data), metadata_filename=file_name)
        pages: dict[int, Page] = {}
        for el in elements:
            n = getattr(el.metadata, "page_number", None) or 1
            if options.max_pages and n > options.max_pages:
                continue
            page = pages.setdefault(n, Page(n))
            cat, text = el.category, (el.text or "").strip()
            if cat == "Table":
                html = getattr(el.metadata, "text_as_html", None)
                md = html_table_to_markdown(html) if html else text
                page.elements.append(Element(TABLE, md or text))
            elif not text:
                continue
            elif cat == "Title":
                page.elements.append(Element(TEXT, f"## {text}"))
            elif cat == "ListItem":
                page.elements.append(Element(TEXT, f"- {text}"))
            else:
                page.elements.append(Element(TEXT, text))
        out = ParsedDocument(file_name, file_type, self.name, sorted(pages.values(), key=lambda p: p.page_number))
        return out
