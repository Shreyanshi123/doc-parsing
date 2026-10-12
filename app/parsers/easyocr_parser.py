"""
EasyOCR (deep-learning OCR, free). Often better than Tesseract on photos/odd fonts; slower and heavy
(pulls PyTorch, downloads models on first run).   pip install easyocr
"""
from __future__ import annotations

import io

from app.config import settings
from app.models import TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.ocr_parser import render_pdf_page
from app.parsers.registry import register
from app.parsers.utils import limit_pages

_LANG = {"eng": "en", "hin": "hi", "fra": "fr", "deu": "de", "spa": "es", "ita": "it", "por": "pt"}
_readers: dict[tuple, object] = {}


def _reader(options):
    import easyocr

    codes = tuple(_LANG.get(c, c) for c in (options.ocr_lang or settings.ocr_lang).split("+")) or ("en",)
    if codes not in _readers:
        _readers[codes] = easyocr.Reader(list(codes), gpu=False)
    return _readers[codes]


@register
class EasyOcrParser(BaseParser):
    name = "easyocr"
    description = "EasyOCR deep-learning OCR (CPU). Alternative to Tesseract; heavy install, slower."
    supported_types = {"pdf", "image"}

    @classmethod
    def is_available(cls):
        try:
            import easyocr  # noqa: F401
            import numpy  # noqa: F401
            return True, ""
        except ImportError:
            return False, "pip install easyocr (optional, large)"

    def parse(self, data, file_name, file_type, options):
        import numpy as np
        from PIL import Image

        reader = _reader(options)
        out = ParsedDocument(file_name, file_type, self.name)

        def ocr(img) -> str:
            lines = reader.readtext(np.array(img.convert("RGB")), detail=0, paragraph=True)
            return "\n\n".join(lines)

        if file_type == "image":
            out.pages.append(Page(1, [Element(TEXT, ocr(Image.open(io.BytesIO(data))))]))
            return out
        import fitz

        doc = fitz.open(stream=data, filetype="pdf")
        for i in range(limit_pages(len(doc), options.max_pages)):
            img = render_pdf_page(doc[i], options.ocr_dpi or settings.ocr_dpi)
            out.pages.append(Page(i + 1, [Element(TEXT, ocr(img), metadata={"ocr": True})]))
        return out
