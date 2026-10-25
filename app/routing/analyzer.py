"""
Document analyzer: looks *inside* the document (cheaply) and produces a profile that
the router uses to choose a parsing method.

For PDFs we sample up to 20 pages and decide: digital (real text layer), scanned
(pages are pictures), or mixed.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any

from app.models import ParseOptions

SAMPLE_PAGES = 20


@dataclass
class DocProfile:
    file_type: str
    size_bytes: int
    classification: str = "unknown"   # digital | scanned | mixed | native_office | image | text
    page_count: int = 0
    sampled_pages: int = 0
    text_pages: int = 0
    scanned_pages: int = 0
    avg_chars_per_page: float = 0.0
    est_tables: int = 0            # real tables (a chart's grid lines are not counted)
    table_pages: int = 0
    figure_count: int = 0          # charts / diagrams / pictures on the text pages
    figure_pages: int = 0
    traits: list[str] = field(default_factory=list)   # what is IN the document: "tables", "figures"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["avg_chars_per_page"] = round(self.avg_chars_per_page, 1)
        return d


def analyze(data: bytes, file_type: str, options: ParseOptions) -> DocProfile:
    p = DocProfile(file_type=file_type, size_bytes=len(data))
    if file_type == "pdf":
        _analyze_pdf(data, p, options)
    elif file_type == "image":
        p.classification, p.page_count = "image", 1
    elif file_type in ("docx", "pptx", "xlsx", "csv"):
        p.classification = "native_office"
        if file_type != "csv" and _has_chart_objects(data):
            p.traits.append("charts")
    else:
        p.classification = "text"
    return p


def _has_chart_objects(data: bytes) -> bool:
    """True when a Word / PowerPoint / Excel file contains real chart objects (their data is stored as XML, not as a picture)."""
    import io
    import zipfile

    try:
        return any("/charts/chart" in n for n in zipfile.ZipFile(io.BytesIO(data)).namelist())
    except zipfile.BadZipFile:
        return False


def _analyze_pdf(data: bytes, p: DocProfile, options: ParseOptions) -> None:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        _analyze_pdf_pdfminer(data, p, options)
        return

    doc = fitz.open(stream=data, filetype="pdf")
    p.page_count = len(doc)
    n = min(len(doc), SAMPLE_PAGES)
    p.sampled_pages = n
    total_chars = 0
    for i in range(n):
        page = doc[i]
        chars = len(page.get_text("text").strip())
        total_chars += chars
        if chars >= options.min_chars_per_page:
            p.text_pages += 1
            _look_for_tables_and_figures(page, p)
        else:
            p.scanned_pages += 1
    _finish_pdf(p, total_chars, n)


def _look_for_tables_and_figures(page, p: DocProfile) -> None:
    """Only for pages that have a text layer. Cheap checks with PyMuPDF; any failure just means 'nothing found'."""
    from app.figures import find_figures, table_fill, MIN_TABLE_FILL

    table_rects = []
    try:
        real = [t for t in page.find_tables().tables if table_fill(t) >= MIN_TABLE_FILL]
        if real:
            p.table_pages += 1
            p.est_tables += len(real)
            table_rects = [tuple(t.bbox) for t in real]
    except Exception:
        pass
    try:
        figs = find_figures(page, table_rects)
        if figs:
            p.figure_pages += 1
            p.figure_count += len(figs)
    except Exception:
        pass


def _analyze_pdf_pdfminer(data: bytes, p: DocProfile, options: ParseOptions) -> None:
    """Fallback when PyMuPDF is not installed."""
    import io
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer

    total_chars = n = 0
    for page_layout in extract_pages(io.BytesIO(data), maxpages=SAMPLE_PAGES):
        n += 1
        chars = sum(len(e.get_text().strip()) for e in page_layout if isinstance(e, LTTextContainer))
        total_chars += chars
        if chars >= options.min_chars_per_page:
            p.text_pages += 1
        else:
            p.scanned_pages += 1
    p.page_count, p.sampled_pages = n, n
    p.notes.append("PyMuPDF missing - analysis done with pdfminer (no table estimate).")
    _finish_pdf(p, total_chars, n)


def _finish_pdf(p: DocProfile, total_chars: int, n: int) -> None:
    p.avg_chars_per_page = total_chars / n if n else 0.0
    if p.est_tables:
        p.traits.append("tables")
    if p.figure_count:
        p.traits.append("figures")
    if n == 0:
        p.classification = "unknown"
    elif p.scanned_pages == 0:
        p.classification = "digital"
    elif p.text_pages == 0:
        p.classification = "scanned"
    else:
        p.classification = "mixed"
