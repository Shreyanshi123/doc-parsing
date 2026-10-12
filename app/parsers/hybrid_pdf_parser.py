"""Hybrid: per page, use the text layer when it exists, OCR only the pages that are scans.
Best default for 'mixed' PDFs (e.g. a digital report with a few scanned appendix pages)."""
from __future__ import annotations

from app.models import TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.ocr_parser import _tesseract_ready, ocr_pdf_page
from app.parsers.pymupdf_parser import extract_page_elements
from app.parsers.registry import register
from app.parsers.utils import limit_pages


@register
class HybridPdfParser(BaseParser):
    name = "hybrid_pdf"
    description = "PyMuPDF for pages with a text layer + Tesseract OCR for scanned pages (decided page by page)."
    supported_types = {"pdf"}

    @classmethod
    def is_available(cls):
        try:
            import fitz  # noqa: F401
        except ImportError:
            return False, "pip install pymupdf"
        return _tesseract_ready()

    def parse(self, data, file_name, file_type, options):
        import fitz

        doc = fitz.open(stream=data, filetype="pdf")
        out = ParsedDocument(file_name, file_type, self.name)
        ocr_pages = []
        for i in range(limit_pages(len(doc), options.max_pages)):
            page = doc[i]
            els = extract_page_elements(doc, page, options)
            chars = sum(len(e.content.strip()) for e in els if e.content_type in ("text", "table"))
            if chars < options.min_chars_per_page:
                els = [Element(TEXT, ocr_pdf_page(page, options), metadata={"ocr": True})] + [
                    e for e in els if e.content_type == "image"
                ]
                ocr_pages.append(i + 1)
            out.pages.append(Page(i + 1, els))
        out.metadata["ocr_pages"] = ocr_pages
        return out
