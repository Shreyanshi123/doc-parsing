"""PyMuPDF: fast, free, best for digital (text-layer) PDFs. Detects headings by font size
and tables via PyMuPDF's built-in table finder."""
from __future__ import annotations

import statistics

from app.models import IMAGE, TABLE, TEXT, Element, Page, ParseOptions, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register
from app.parsers.utils import limit_pages, rows_to_markdown


def extract_page_elements(doc, page, options: ParseOptions) -> list[Element]:
    """Shared by the pymupdf and hybrid parsers. Returns elements for ONE page."""
    elements: list[Element] = []

    # ---- tables ----
    table_bboxes = []
    try:
        for t in page.find_tables().tables:
            md = ""
            try:
                md = t.to_markdown()
            except Exception:
                md = rows_to_markdown(t.extract())
            if md.strip():
                table_bboxes.append((fitz_rect(t.bbox), md))
    except Exception:
        pass  # older PyMuPDF without find_tables

    # ---- text blocks with font-size based headings ----
    d = page.get_text("dict", sort=True)
    sizes = [
        s["size"]
        for b in d["blocks"] if b.get("type") == 0
        for ln in b["lines"] for s in ln["spans"] if s["text"].strip()
    ]
    body = statistics.median(sizes) if sizes else 11.0

    items: list[tuple[float, Element]] = []   # (y position, element) for reading order
    for b in d["blocks"]:
        if b.get("type") != 0:
            continue
        x0, y0, x1, y1 = b["bbox"]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if any(r[0] <= cx <= r[2] and r[1] <= cy <= r[3] for r, _ in table_bboxes):
            continue  # already represented by the table element
        parts, max_size, bold = [], 0.0, False
        for ln in b["lines"]:
            txt = "".join(s["text"] for s in ln["spans"]).strip()
            if not txt:
                continue
            parts.append(txt)
            for s in ln["spans"]:
                max_size = max(max_size, s["size"])
                bold = bold or bool(s["flags"] & 16)
        if not parts:
            continue
        text = " ".join(parts)
        ratio = max_size / body if body else 1
        if len(text) < 150:
            if ratio >= 1.5:
                text = "# " + text
            elif ratio >= 1.25:
                text = "## " + text
            elif ratio >= 1.1 and bold:
                text = "### " + text
        items.append((y0, Element(TEXT, text)))

    for rect, md in table_bboxes:
        items.append((rect[1], Element(TABLE, md)))
    items.sort(key=lambda t: t[0])
    elements.extend(e for _, e in items)

    # ---- embedded images ----
    if options.extract_images:
        for img in page.get_images(full=True):
            try:
                info = doc.extract_image(img[0])
                if info["width"] < 50 or info["height"] < 50 or len(info["image"]) < 3000:
                    continue  # skip icons / bullets
                elements.append(
                    Element(IMAGE, "", info["image"], info["ext"], {"width": info["width"], "height": info["height"]})
                )
            except Exception:
                continue
    return elements


def fitz_rect(bbox):
    return (bbox[0], bbox[1], bbox[2], bbox[3])


@register
class PyMuPDFParser(BaseParser):
    name = "pymupdf"
    description = "PyMuPDF text-layer extraction + table finder. Fast; no OCR (scanned PDFs return little/no text)."
    supported_types = {"pdf"}

    @classmethod
    def is_available(cls):
        try:
            import fitz  # noqa: F401
            return True, ""
        except ImportError:
            return False, "pip install pymupdf"

    def parse(self, data, file_name, file_type, options):
        import fitz

        doc = fitz.open(stream=data, filetype="pdf")
        out = ParsedDocument(file_name, file_type, self.name)
        for i in range(limit_pages(len(doc), options.max_pages)):
            out.pages.append(Page(i + 1, extract_page_elements(doc, doc[i], options)))
        out.metadata["source_page_count"] = len(doc)
        return out
