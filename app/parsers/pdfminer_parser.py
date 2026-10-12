"""pdfminer.six: pure-python text extraction. Slower than PyMuPDF but a good second opinion
on reading order for complex digital PDFs. No table detection, no OCR."""
from __future__ import annotations

import io

from app.models import TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register


@register
class PdfMinerParser(BaseParser):
    name = "pdfminer"
    description = "pdfminer.six layout-aware text extraction. Digital PDFs only; no tables/OCR."
    supported_types = {"pdf"}

    @classmethod
    def is_available(cls):
        try:
            import pdfminer  # noqa: F401
            return True, ""
        except ImportError:
            return False, "pip install pdfminer.six"

    def parse(self, data, file_name, file_type, options):
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextContainer

        out = ParsedDocument(file_name, file_type, self.name)
        for i, layout in enumerate(extract_pages(io.BytesIO(data), maxpages=options.max_pages or 0)):
            elements = []
            for el in layout:
                if isinstance(el, LTTextContainer):
                    # join soft line wraps inside a text box into one paragraph
                    text = " ".join(l.strip() for l in el.get_text().splitlines() if l.strip())
                    if text:
                        elements.append(Element(TEXT, text))
            out.pages.append(Page(i + 1, elements))
        return out
