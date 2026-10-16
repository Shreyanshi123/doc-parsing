"""
Smart PDF: one parser for pages that mix text, tables, charts and diagrams.

Per page:
  1. text, headings and tables  -> PyMuPDF (fast).  A page that is only a picture -> OCR, like hybrid_pdf.
  2. figures (charts, diagrams, pictures) are found, cut out as PNG and read by a vision model
     (app/vision.py): a chart becomes a Markdown table of values, a diagram becomes a list of
     boxes and arrows.
  3. everything is put back in reading order, so the Markdown follows the page.

Without a vision backend the figures are still found and marked, but their content is not read.
cost = "paid" because the vision step may call a paid API; that also keeps this parser out of
"Compare all parsers" unless "include paid parsers" is ticked.
"""
from __future__ import annotations

import dataclasses
from collections import Counter

from app.config import settings
from app.figures import crop_png, find_figures, padded
from app.models import IMAGE, TABLE, TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.pymupdf_parser import extract_page_elements
from app.parsers.registry import register
from app.parsers.utils import limit_pages
from app.vision import describe_figure, pick_backend


MAX_LABEL_LEN = 150       # a chart label is short; a longer text block means this is not a chart
MAX_CHART_CHARS = 350     # total text allowed inside a drawn chart
DECORATION_FRAC = 0.08    # drawn shapes with no text and smaller than this share of the page = decoration
DROP_TEXT_KINDS = ("chart", "plot", "diagram", "table")   # only then is the text inside the figure replaced
MIN_TABLE_FILL = 0.2   # share of non-empty cells below which a detected table is treated as a chart


def _center_inside(bbox, rect) -> bool:
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    return rect.x0 <= cx <= rect.x1 and rect.y0 <= cy <= rect.y1


@register
class SmartPdfParser(BaseParser):
    name = "smart_pdf"
    description = (
        "PyMuPDF text/tables/headings + charts and diagrams cut out and read by a vision model "
        "(Azure OpenAI or local Ollama). Without a vision backend, figures are only marked."
    )
    supported_types = {"pdf"}
    cost = "paid"

    @classmethod
    def is_available(cls):
        try:
            import fitz  # noqa: F401
        except ImportError:
            return False, "pip install pymupdf"
        return True, ""

    def parse(self, data, file_name, file_type, options):
        import fitz

        doc = fitz.open(stream=data, filetype="pdf")
        out = ParsedDocument(file_name, file_type, self.name)
        opts = dataclasses.replace(options, extract_images=False)
        backend = pick_backend()
        budget = settings.max_figures
        ocr_pages, found, read = [], 0, 0

        n_pages = limit_pages(len(doc), options.max_pages)
        seen = Counter()
        for i in range(n_pages):
            seen.update({info["xref"] for info in doc[i].get_image_info(xrefs=True) if info.get("xref")})
        repeating = {x for x, c in seen.items() if c >= 3 and c >= 0.5 * n_pages}   # logos, page decoration

        for i in range(n_pages):
            page, n = doc[i], i + 1
            els = extract_page_elements(doc, page, opts)
            chars = sum(len(e.content.strip()) for e in els if e.content_type in (TEXT, TABLE))

            if chars < options.min_chars_per_page:          # the page is a picture -> OCR it
                from app.parsers.ocr_parser import ocr_pdf_page

                try:
                    els = [Element(TEXT, ocr_pdf_page(page, options), metadata={"ocr": True})]
                    ocr_pages.append(n)
                except Exception as e:  # noqa: BLE001 - OCR engine missing or failing
                    out.warnings.append(f"page {n}: no text layer and OCR failed ({type(e).__name__}: {e})")
                out.pages.append(Page(n, els))
                continue

            # a "table" that is mostly empty cells is really a chart's grid lines: drop it, the figure step reads the chart
            fake = [e for e in els if e.content_type == TABLE and e.metadata.get("fill", 1.0) < MIN_TABLE_FILL]
            els = [e for e in els if e not in fake]
            for t in fake:   # keep the chart's own text (values, labels); it is dropped later if the vision model reads the figure
                box = t.metadata["bbox"]
                txt = " ".join(page.get_text("text", clip=fitz.Rect(*box)).split())
                if txt:
                    els.append(Element(TEXT, txt, metadata={"y": box[1], "bbox": box, "chart_text": True}))
            table_rects = [tuple(e.metadata["bbox"]) for e in els if e.content_type == TABLE and "bbox" in e.metadata]
            figure_els = []
            for rect, kinds in find_figures(page, table_rects, repeating):
                inside = [e for e in els if e.content_type == TEXT and "bbox" in e.metadata
                          and _center_inside(e.metadata["bbox"], rect)]
                chars_inside = sum(len(e.content) for e in inside)
                longest = max((len(e.content) for e in inside), default=0)
                if "raster" not in kinds:
                    # drawn shapes only: page chrome (menus, footers) and decoration are not charts
                    if longest > MAX_LABEL_LEN or chars_inside > MAX_CHART_CHARS:
                        continue          # long text inside = a text area, not a chart
                    if chars_inside == 0 and rect.width * rect.height < DECORATION_FRAC * page.rect.width * page.rect.height:
                        continue          # small, no text at all = decoration
                found += 1
                meta = {"y": round(rect.y0, 1), "bbox": [round(v, 1) for v in rect], "figure": True, "page": n}
                if backend is None:
                    md = f"**Figure (page {n}):** figure found; no vision model is configured, so its content was not read."
                    png = crop_png(page, padded(page, rect))
                elif budget <= 0:
                    md = f"**Figure (page {n}):** figure found; skipped (limit of {settings.max_figures} figures per document)."
                    png = None
                else:
                    budget -= 1
                    png = crop_png(page, padded(page, rect))
                    try:
                        fig = describe_figure(png)
                        if fig is None:
                            md = f"**Figure (page {n}):** figure found; no vision model is configured."
                        else:
                            md = f"**Figure (page {n}, {fig.kind})**\n\n{fig.body}"
                            meta.update(kind=fig.kind, vision=fig.backend)
                            read += 1
                            if any(w in fig.kind for w in DROP_TEXT_KINDS):   # it really is a chart / diagram
                                els = [e for e in els if not (e.content_type == TEXT and "bbox" in e.metadata
                                                              and _center_inside(e.metadata["bbox"], rect))]
                    except Exception as e:  # noqa: BLE001 - a failed figure must not fail the page
                        md = f"**Figure (page {n}):** figure found; could not be read ({type(e).__name__})."
                        out.warnings.append(f"page {n}: figure could not be read: {type(e).__name__}: {e}")
                figure_els.append(Element(IMAGE, md, png, "png" if png else None, meta))

            merged = sorted(els + figure_els, key=lambda e: e.metadata.get("y", 1e9))
            out.pages.append(Page(n, merged))

        if found and backend is None:
            out.warnings.append(
                f"{found} figure(s) found but no vision model is configured "
                "(set AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_KEY / AZURE_OPENAI_DEPLOYMENT, or run Ollama)."
            )
        out.metadata.update(figures_found=found, figures_read=read, vision_backend=backend, ocr_pages=ocr_pages)
        return out
