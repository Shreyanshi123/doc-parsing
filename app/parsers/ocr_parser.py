"""Tesseract OCR: free. For scanned PDFs (pages are rendered to images first) and image files."""
from __future__ import annotations

import io
import shutil

from app.config import settings
from app.models import IMAGE, TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register
from app.parsers.utils import limit_pages


def _tesseract_ready() -> tuple[bool, str]:
    try:
        import pytesseract  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        return False, "pip install pytesseract pillow"
    cmd = settings.tesseract_cmd or shutil.which("tesseract")
    if not cmd:
        return False, "tesseract binary not found (apt install tesseract-ocr / set TESSERACT_CMD)"
    return True, ""


def ocr_pil_image(img, options) -> str:
    import pytesseract

    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    lang = options.ocr_lang or settings.ocr_lang
    return pytesseract.image_to_string(img, lang=lang, config="--psm 3").strip()


def render_pdf_page(page, dpi: int):
    """PyMuPDF page -> PIL image."""
    from PIL import Image

    pix = page.get_pixmap(dpi=dpi)
    return Image.open(io.BytesIO(pix.tobytes("png")))


def ocr_pdf_page(page, options) -> str:
    dpi = options.ocr_dpi or settings.ocr_dpi
    return ocr_pil_image(render_pdf_page(page, dpi), options)


@register
class OcrParser(BaseParser):
    name = "ocr"
    description = "Tesseract OCR (pages rendered to images). For scanned PDFs and images. Plain text only - no tables/headings."
    supported_types = {"pdf", "image"}

    @classmethod
    def is_available(cls):
        ok, reason = _tesseract_ready()
        if not ok:
            return ok, reason
        try:
            import fitz  # noqa: F401
        except ImportError:
            return True, ""  # images still work; PDFs need PyMuPDF (checked at parse time)
        return True, ""

    def parse(self, data, file_name, file_type, options):
        out = ParsedDocument(file_name, file_type, self.name)
        if file_type == "image":
            from PIL import Image

            img = Image.open(io.BytesIO(data))
            elements = [Element(TEXT, ocr_pil_image(img, options))]
            if options.extract_images:
                elements.append(Element(IMAGE, "", data, (img.format or "png").lower(),
                                        {"width": img.width, "height": img.height}))
            out.pages.append(Page(1, elements))
            return out

        try:
            import fitz
        except ImportError as e:
            raise RuntimeError("OCR of PDFs needs PyMuPDF to render pages: pip install pymupdf") from e
        doc = fitz.open(stream=data, filetype="pdf")
        for i in range(limit_pages(len(doc), options.max_pages)):
            out.pages.append(Page(i + 1, [Element(TEXT, ocr_pdf_page(doc[i], options), metadata={"ocr": True})]))
        return out
