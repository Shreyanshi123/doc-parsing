"""pdfplumber: pdfminer-based, good rule-based table extraction. Digital PDFs only (no OCR)."""
from __future__ import annotations

import io

from app.models import TABLE, TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register
from app.parsers.utils import limit_pages, rows_to_markdown


@register
class PdfPlumberParser(BaseParser):
    name = "pdfplumber"
    description = "pdfplumber: text + rule-based table extraction for digital PDFs (no OCR)."
    supported_types = {"pdf"}

    @classmethod
    def is_available(cls):
        try:
            import pdfplumber  # noqa: F401
            return True, ""
        except ImportError:
            return False, "pip install pdfplumber"

    def parse(self, data, file_name, file_type, options):
        import pdfplumber

        out = ParsedDocument(file_name, file_type, self.name)
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for i in range(limit_pages(len(pdf.pages), options.max_pages)):
                page = pdf.pages[i]
                els, boxes = [], []
                for t in page.find_tables():
                    md = rows_to_markdown(t.extract())
                    if md:
                        boxes.append(t.bbox)
                        els.append((t.bbox[1], Element(TABLE, md)))

                def outside_tables(obj, boxes=boxes):
                    return not any(
                        obj.get("x0", 0) >= b[0] - 1 and obj.get("x1", 0) <= b[2] + 1
                        and obj.get("top", 0) >= b[1] - 1 and obj.get("bottom", 0) <= b[3] + 1
                        for b in boxes
                    )

                text = (page.filter(outside_tables) if boxes else page).extract_text() or ""
                if text.strip():
                    els.append((-1, Element(TEXT, text)))      # text first, then tables in page order
                els.sort(key=lambda t: t[0])
                out.pages.append(Page(i + 1, [e for _, e in els]))
        return out
