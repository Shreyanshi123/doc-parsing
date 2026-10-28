"""
ADI + vision: Azure Document Intelligence reads the text and the tables, a vision model reads only the charts and photos.

Per document:
  1. Azure Document Intelligence (prebuilt-layout) reads the whole PDF: text, headings and tables as Markdown.
  2. The figures (charts, diagrams, photos) are found with PyMuPDF, cut out as small PNGs and read by the vision model
     (app/vision.py), at most settings.max_figures per document. A page is never sent as a whole to the model.
  3. Where Azure marked a figure (its own <figure> block), that block is replaced by the vision reading; a figure Azure did
     not mark is added at the end of its page.

cost = "paid": Azure charges per page and the vision step may call a paid API. It is never picked by the automatic routing
and it stays out of "Compare all parsers" unless "include paid parsers" is ticked.
Without a vision backend the result is simply Azure's own output.
"""
from __future__ import annotations

from app.config import settings
from app.figures import crop_png, find_figures, padded
from app.models import IMAGE, TEXT, Element, Page, ParsedDocument
from app.parsers.azure_di_parser import AzureDocIntelParser
from app.parsers.base import BaseParser
from app.parsers.registry import register
from app.vision import describe_figure, pick_backend


def _rect(polygon, scale):
    xs, ys = polygon[0::2], polygon[1::2]
    return (min(xs) * scale, min(ys) * scale, max(xs) * scale, max(ys) * scale)


def _centre_inside(a, b) -> bool:
    cx, cy = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
    return b[0] <= cx <= b[2] and b[1] <= cy <= b[3]


@register
class AdiVisionParser(BaseParser):
    name = "adi_vision"
    description = "Azure Document Intelligence for text and tables + a vision model for charts and photos only (paid)."
    supported_types = {"pdf"}
    cost = "paid"

    @classmethod
    def is_available(cls):
        ok, why = AzureDocIntelParser.is_available()
        if not ok:
            return ok, why
        try:
            import fitz  # noqa: F401
        except ImportError:
            return False, "pip install pymupdf"
        return True, ""

    def parse(self, data, file_name, file_type, options):
        import fitz

        result = AzureDocIntelParser()._analyze(data)
        content = result.content or ""
        doc = fitz.open(stream=data, filetype="pdf")
        out = ParsedDocument(file_name, file_type, self.name)
        backend = pick_backend()
        budget = settings.max_figures
        found = read = 0

        pages = list(result.pages or [])
        adi_figs: dict[int, list] = {}          # page number -> [(rect in PDF points, offset, length)]
        for fig in getattr(result, "figures", None) or []:
            if not fig.bounding_regions or not fig.spans:
                continue
            region = fig.bounding_regions[0]
            pg = next((p for p in pages if p.page_number == region.page_number), None)
            if pg is None or not pg.width or region.page_number > len(doc):
                continue
            scale = doc[region.page_number - 1].rect.width / pg.width
            span = min(fig.spans, key=lambda s: s.offset)
            adi_figs.setdefault(region.page_number, []).append((_rect(region.polygon, scale), span.offset, span.length))
        adi_tables: dict[int, list] = {}
        for tb in getattr(result, "tables", None) or []:
            for region in tb.bounding_regions or []:
                pg = next((p for p in pages if p.page_number == region.page_number), None)
                if pg and pg.width and region.page_number <= len(doc):
                    adi_tables.setdefault(region.page_number, []).append(_rect(region.polygon, doc[region.page_number - 1].rect.width / pg.width))

        for pg in sorted(pages, key=lambda p: p.page_number):
            n = pg.page_number
            replacements, extra = [], []            # (offset, length, markdown) and figures Azure did not mark
            if backend is not None and n <= len(doc):
                page = doc[n - 1]
                for rect, kinds in find_figures(page, adi_tables.get(n, [])):
                    found += 1
                    if budget <= 0:
                        continue
                    budget -= 1
                    png = crop_png(page, padded(page, rect))
                    try:
                        fig = describe_figure(png)
                    except Exception as e:  # noqa: BLE001 - one figure must not fail the page
                        out.warnings.append(f"page {n}: figure could not be read: {type(e).__name__}: {e}")
                        continue
                    if fig is None:
                        continue
                    read += 1
                    md = f"**Figure (page {n}, {fig.kind})**\n\n{fig.body}"
                    mine = tuple(rect)
                    hit = next((f for f in adi_figs.get(n, []) if _centre_inside(mine, f[0]) or _centre_inside(f[0], mine)), None)
                    if hit and all(r[0] != hit[1] for r in replacements):
                        replacements.append((hit[1], hit[2], md))
                    else:
                        extra.append(Element(IMAGE, md, png, "png", {"figure": True, "page": n}))
            # the page's own text, with the figure blocks swapped for the vision reading
            spans = sorted(pg.spans or [], key=lambda s: s.offset)
            text = ""
            for s in spans:
                piece, start = content[s.offset: s.offset + s.length], s.offset
                for off, ln, md in sorted(r for r in replacements if start <= r[0] < start + s.length):
                    piece = piece.replace(content[off: off + ln], md, 1)
                text += piece
            els = [Element(TEXT, text)] if text.strip() else []
            out.pages.append(Page(n, els + extra))

        if not out.pages:
            out.pages.append(Page(1, [Element(TEXT, content)]))
        if found and backend is None:
            out.warnings.append(f"{found} figure(s) found but no vision model is configured; the result is Azure's own output.")
        out.metadata.update(figures_found=found, figures_read=read, vision_backend=backend)
        return out
