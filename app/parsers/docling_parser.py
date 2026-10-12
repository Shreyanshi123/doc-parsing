"""
Docling (IBM, open source, free): strong layout + table understanding, runs on CPU.
OPTIONAL and heavy (pip install docling -> pulls torch + models). Worth including in the
POC comparison because it is the closest free alternative to paid layout engines.

NOTE: not exercised in the POC sandbox; adjust `parse` if your Docling version differs.
"""
from __future__ import annotations

import os
import tempfile

from app.models import TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register

_EXT = {"pdf": ".pdf", "docx": ".docx", "pptx": ".pptx", "xlsx": ".xlsx", "image": ".png"}


@register
class DoclingParser(BaseParser):
    name = "docling"
    description = "Docling layout/table-aware converter (free, optional heavy install)."
    supported_types = {"pdf", "docx", "pptx", "xlsx", "image"}

    @classmethod
    def is_available(cls):
        try:
            import docling  # noqa: F401
            return True, ""
        except ImportError:
            return False, "pip install docling (optional, large)"

    def parse(self, data, file_name, file_type, options):
        from docling.document_converter import DocumentConverter

        out = ParsedDocument(file_name, file_type, self.name)
        with tempfile.NamedTemporaryFile(suffix=_EXT.get(file_type, ".bin"), delete=False) as f:
            f.write(data)
            path = f.name
        try:
            doc = DocumentConverter().convert(path).document
        finally:
            os.unlink(path)
        page_nos = sorted(getattr(doc, "pages", {}).keys()) if hasattr(doc, "pages") else []
        for n in page_nos[: options.max_pages or None]:
            try:
                out.pages.append(Page(n, [Element(TEXT, doc.export_to_markdown(page_no=n))]))
            except TypeError:
                out.pages = []
                break
        if not out.pages:
            out.pages.append(Page(1, [Element(TEXT, doc.export_to_markdown())]))
            out.warnings.append("Docling output not split by page in this version.")
        return out
