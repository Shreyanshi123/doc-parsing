"""pymupdf4llm: PyMuPDF's own Markdown exporter (headings, bold, lists, tables). Fast, local, digital PDFs."""
from __future__ import annotations

from app.models import TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register
from app.parsers.utils import limit_pages


@register
class PyMuPDF4LLMParser(BaseParser):
    name = "pymupdf4llm"
    description = "pymupdf4llm Markdown exporter built on PyMuPDF (richer Markdown than the plain 'pymupdf' parser)."
    supported_types = {"pdf"}

    @classmethod
    def is_available(cls):
        try:
            import fitz  # noqa: F401
            import pymupdf4llm  # noqa: F401
            return True, ""
        except ImportError:
            return False, "pip install pymupdf pymupdf4llm"

    def parse(self, data, file_name, file_type, options):
        import fitz
        import pymupdf4llm

        doc = fitz.open(stream=data, filetype="pdf")
        n = limit_pages(len(doc), options.max_pages)
        chunks = pymupdf4llm.to_markdown(doc, pages=list(range(n)), page_chunks=True)
        out = ParsedDocument(file_name, file_type, self.name)
        for i, c in enumerate(chunks):
            text = c.get("text", "") if isinstance(c, dict) else str(c)
            out.pages.append(Page(i + 1, [Element(TEXT, text)]))
        return out
