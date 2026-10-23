"""
Smart Extract: cut a document into parts (headings, text, tables, figures, scanned pages) and
give every part to the parser that is best for that kind of part.

    extract_document(bytes, name, options) -> {segments, pages, markdown, summary, ...}

Which parser for which part (evidence: eval/REPORT.md, eval/BENCHMARK_REPORT.md):
  heading / text   -> pymupdf       99-100% on digital text in 1-2 s; the others only add time
  table            -> pymupdf4llm   80% of table cells in the 15-page paper (pymupdf: 12%); docling 93% but 50-250x slower
                      (docling goes first when "prefer quality" is on; Azure DI first when "include paid" is on)
  figure           -> vision model  turns a chart into a data table, a diagram into boxes and arrows
                      (no vision model: OCR for pictures, the PDF's own text for drawn charts)
  scanned page     -> pymupdf4llm   93% on a clean scan (docling 98% but slower), then OCR
  Word/Excel/PPT   -> the native parser (1.0 in the scored tests); each element becomes a part
  image file       -> easyocr       cleanest UI text, then tesseract

Every part keeps the list of parsers that were tried, so the UI can show why one was chosen.
The compare tab (app/compare.py) is not used or changed by this module, except for the table counter.
"""
from __future__ import annotations

import base64
import dataclasses
import logging
import os
import tempfile
import time
from collections import Counter
from typing import Callable, Optional

from app.compare import count_tables
from app.config import settings
from app.models import IMAGE, TABLE, TEXT, ParseOptions
from app.normalizer import normalize_document
from app.parsers import get_parser_class
from app.parsers.pymupdf_parser import extract_page_elements
from app.parsers.smart_pdf_parser import (DECORATION_FRAC, DROP_TEXT_KINDS, MAX_CHART_CHARS, MAX_LABEL_LEN,
                                          MIN_TABLE_FILL, _center_inside)
from app.parsers.utils import limit_pages
from app.routing import learned
from app.routing.analyzer import analyze
from app.routing.file_type import resolve_file_type

log = logging.getLogger("extract")

PREVIEW_PAGES = 15        # page pictures sent to the UI (the extraction itself covers every page)
PREVIEW_DPI = 80
MAX_FIGURE_THUMBS = 12    # cropped figure pictures sent to the UI

KINDS = ("heading", "text", "table", "figure", "scanned", "image")


# --------------------------------------------------------------------------- running one parser
_docling_converter = None


def _docling_markdown(data: bytes, suffix: str) -> str:
    """Docling builds its models on every DocumentConverter(); keep one so each table crop does not pay for that again."""
    global _docling_converter
    if _docling_converter is None:
        from docling.document_converter import DocumentConverter

        _docling_converter = DocumentConverter()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
        path = f.name
    try:
        return _docling_converter.convert(path).document.export_to_markdown()
    finally:
        os.unlink(path)


def _run(name: str, data: bytes, file_type: str, options: ParseOptions) -> str:
    if name == "docling":
        return _docling_markdown(data, ".pdf" if file_type == "pdf" else ".png")
    doc = normalize_document(get_parser_class(name)().parse(data, f"part.{ 'pdf' if file_type == 'pdf' else 'png'}", file_type, options))
    return doc.markdown


def _usable(names: list[str], file_type: str) -> list[str]:
    """The parsers in `names` that support this file type and are installed (a quick check: no heavy library is imported here)."""
    out = []
    for n in names:
        if n not in out and learned._usable(n, file_type, True):
            out.append(n)
    return out


def _chain(chain: list[str], data: bytes, file_type: str, options: ParseOptions, accept: Callable[[str], bool]):
    """Try the parsers in order; the first one whose output passes `accept` wins. -> (parser, markdown, tried)"""
    tried = []
    for name in chain:
        t = time.perf_counter()
        try:
            md = _run(name, data, file_type, options).strip()
            ms = int((time.perf_counter() - t) * 1000)
            if accept(md):
                tried.append({"parser": name, "status": "ok", "ms": ms})
                return name, md, tried
            tried.append({"parser": name, "status": "empty", "ms": ms})
        except Exception as e:  # noqa: BLE001 - one failing parser must not stop the part
            tried.append({"parser": name, "status": "error", "ms": int((time.perf_counter() - t) * 1000),
                          "error": f"{type(e).__name__}: {e}"})
    return None, "", tried


# --------------------------------------------------------------------------- the policy
# Which parser reads which kind of part comes from our head-to-head test (routing/learned.py + routing/measured_scores.json):
# for tables the parser with the best "table reconstruction" score on documents that contain tables, for scanned pages the best
# overall score on scanned documents, for pictures the best score on image files. Best score wins; within a tie the fastest.
# The hand-written lists below are only the tail of each chain, used when the measured ones fail or there is no data.
TABLE_GROUPS = ["digital + tables", "mixed", "digital + charts/images"]   # test documents that contain tables
SCANNED_GROUPS = ["scanned"]


def _measured_chain(label: str, groups: list[str], metric: Optional[str], file_type: str, options: ParseOptions, include_paid: bool,
                    backup: list[str]) -> tuple[list[str], str]:
    ranked = learned.rank(groups, metric, file_type=file_type, include_paid=include_paid, prefer_quality=options.prefer_quality)
    names = [r["parser"] for r in ranked[:4]] + backup
    if include_paid:
        names.insert(0, "azure_di")   # you ticked "Include paid parsers": Azure DI goes first, as before
    chain = _usable(names, file_type)
    if not ranked or not chain:
        return chain, f"{label}: no measured scores for the available parsers, so the hand-written order is used."
    if chain[0] == "azure_di":
        return chain, f"{label}: Azure Document Intelligence (paid) first because you ticked 'Include paid parsers'; the best free parsers follow."
    top = next((r for r in ranked if r["parser"] == chain[0]), None)
    if top is None:
        return chain, f"{label}: {chain[0]} (hand-written fallback, it was not in the measured ranking)."
    how = "fastest of the parsers tied for best" if top.get("tied") else "best score"
    return chain, f"{label}: {chain[0]} - {how}; {learned.evidence(top, groups[0] if len(groups) == 1 else 'table-bearing', metric)}."


def table_chain(file_type: str, options: ParseOptions, include_paid: bool) -> tuple[list[str], str]:
    return _measured_chain("Tables", TABLE_GROUPS, "Table Reconstruction", file_type, options, include_paid, ["pymupdf4llm"])


def scanned_chain(file_type: str, options: ParseOptions, include_paid: bool) -> tuple[list[str], str]:
    return _measured_chain("Scanned page", SCANNED_GROUPS, None, file_type, options, include_paid, ["pymupdf4llm", "ocr", "easyocr", "vlm"])


def routing_evidence(profile: dict, file_type: str, options: ParseOptions, include_paid: bool, mode: str = "part", chosen: Optional[str] = None) -> dict:
    """What the UI shows under 'Scorecard behind these choices': the measured scores, with the parser actually used starred."""
    group = learned.group_for(profile, file_type)
    kw = dict(file_type=file_type, include_paid=True, prefer_quality=True)

    def block(label, groups, metric, chosen):
        ranked = [dict(r) for r in learned.rank(groups, metric, **kw)]
        top = ranked[:4]
        if chosen and chosen not in [r["parser"] for r in top]:
            top += [r for r in ranked if r["parser"] == chosen]
        return {"label": label, "metric": metric.lower() if metric else "overall score", "chosen": chosen, "ranking": top}

    from app.routing.analyzer import DocProfile
    from app.routing.router import route
    try:
        doc_pick = chosen or route(DocProfile(**{k: v for k, v in profile.items() if k in DocProfile.__dataclass_fields__}), options, include_paid=include_paid).selected
    except Exception:  # noqa: BLE001
        doc_pick = None
    out = {"group": group, "document": block(f"Whole document ({group})", [group], None, doc_pick)}
    if file_type == "pdf" and mode == "part":
        tc, sc = table_chain("pdf", options, include_paid)[0], scanned_chain("pdf", options, include_paid)[0]
        out["tables"] = block("Tables", TABLE_GROUPS, "Table Reconstruction", tc[0] if tc else None)
        out["scanned"] = block("Scanned pages", ["scanned"], None, sc[0] if sc else None)
    return out


# --------------------------------------------------------------------------- helpers
def _seg(page: int, n: int, kind: str, bboxes, parser: str, why: str, content: str, tried=None, ms=0, **extra) -> dict:
    return {"id": f"p{page}-{n}", "page": page, "kind": kind, "bboxes": [[round(float(v), 1) for v in b] for b in bboxes],
            "parser": parser, "why": why, "content": content, "tried": tried or [], "ms": ms,
            "words": len(content.split()), "status": "ok" if content.strip() else "empty", **extra}


def _page_pdf(doc, pno: int, rect=None) -> bytes:
    """A one-page PDF of page `pno`, optionally cropped to `rect` so a parser sees only that region."""
    import fitz

    new = fitz.open()
    new.insert_pdf(doc, from_page=pno, to_page=pno)
    if rect is not None:
        new[0].set_cropbox(fitz.Rect(*rect) & new[0].rect)
    data = new.tobytes()
    new.close()
    return data


def _text_kind(md: str) -> str:
    return "heading" if md.lstrip().startswith("#") else "text"


def _table_accept(first_pass: str) -> Callable[[str], bool]:
    """A better table reading must still be a table AND must not lose the words PyMuPDF already found in it."""
    import re

    def words(t: str) -> set[str]:
        return set(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", t.lower())))

    base = words(first_pass)

    def ok(md: str) -> bool:
        return count_tables(md) >= 1 and (not base or len(base & words(md)) / len(base) >= 0.8)

    return ok


# --------------------------------------------------------------------------- PDF
def _extract_pdf(data: bytes, file_name: str, options: ParseOptions, include_paid: bool, emit) -> tuple[list[dict], list[dict], list[str], dict]:
    import fitz

    from app.figures import crop_png, find_figures, padded
    from app.parsers.ocr_parser import ocr_pil_image
    from app.vision import describe_figure, pick_backend

    doc = fitz.open(stream=data, filetype="pdf")
    n_pages = limit_pages(len(doc), options.max_pages)
    backend = pick_backend()
    budget = settings.max_figures
    segments: list[dict] = []
    pages: list[dict] = []
    warnings: list[str] = []
    thumbs = 0
    opts = dataclasses.replace(options, extract_images=False)

    t_chain, t_why = table_chain("pdf", opts, include_paid)
    s_chain, s_why = scanned_chain("pdf", opts, include_paid)
    ocr_ok = bool(_usable(["ocr"], "image"))

    seen = Counter()
    for i in range(n_pages):
        seen.update({info["xref"] for info in doc[i].get_image_info(xrefs=True) if info.get("xref")})
    repeating = {x for x, c in seen.items() if c >= 3 and c >= 0.5 * n_pages}   # logos / page decoration

    def add(seg: dict):
        segments.append(seg)
        emit({"event": "segment", "segment": {k: v for k, v in seg.items() if k != "image"}, "has_image": "image" in seg})

    for pno in range(n_pages):
        page, n = doc[pno], pno + 1
        emit({"event": "page", "page": n, "pages": n_pages})
        counter = 0

        def nid():
            nonlocal counter
            counter += 1
            return counter

        page_info = {"page": n, "width": round(page.rect.width, 1), "height": round(page.rect.height, 1)}
        if pno < PREVIEW_PAGES:
            try:
                page_info["preview"] = "data:image/jpeg;base64," + base64.b64encode(page.get_pixmap(dpi=PREVIEW_DPI).tobytes("jpeg")).decode()
            except Exception:  # noqa: BLE001 - a missing preview must not stop the extraction
                pass
        pages.append(page_info)

        els = extract_page_elements(doc, page, opts)
        chars = sum(len(e.content.strip()) for e in els if e.content_type in (TEXT, TABLE))

        # ---- a page that is only a picture: whole page goes to the scanned-page parser
        if chars < options.min_chars_per_page:
            emit({"event": "working", "page": n, "kind": "scanned", "parser": (s_chain or ["none"])[0]})
            t = time.perf_counter()
            name, md, tried = _chain(s_chain, _page_pdf(doc, pno), "pdf", opts, lambda m: bool(m.strip()))
            if name is None:
                warnings.append(f"page {n}: no text layer and no OCR / scanned-page parser worked ({tried})")
            add(_seg(n, nid(), "scanned", [tuple(page.rect)], name or "none", s_why, md, tried, int((time.perf_counter() - t) * 1000)))
            continue

        # ---- split the page into parts
        fake = [e for e in els if e.content_type == TABLE and e.metadata.get("fill", 1.0) < MIN_TABLE_FILL]
        els = [e for e in els if e not in fake]
        for e in fake:   # a mostly empty "table" is a chart's grid lines: keep its text, let the figure step handle the chart
            box = e.metadata["bbox"]
            txt = " ".join(page.get_text("text", clip=fitz.Rect(*box)).split())
            if txt:
                els.append(dataclasses.replace(e, content_type=TEXT, content=txt, metadata={"y": box[1], "bbox": box, "chart_text": True}))
        table_els = [e for e in els if e.content_type == TABLE and "bbox" in e.metadata]
        figure_parts = []
        for rect, kinds in find_figures(page, [tuple(e.metadata["bbox"]) for e in table_els], repeating):
            inside = [e for e in els if e.content_type == TEXT and "bbox" in e.metadata and _center_inside(e.metadata["bbox"], rect)]
            chars_inside = sum(len(e.content) for e in inside)
            longest = max((len(e.content) for e in inside), default=0)
            if "raster" not in kinds:
                if longest > MAX_LABEL_LEN or chars_inside > MAX_CHART_CHARS:
                    continue
                if chars_inside == 0 and rect.width * rect.height < DECORATION_FRAC * page.rect.width * page.rect.height:
                    continue
            figure_parts.append((rect, kinds, chars_inside))

        drop_rects = []   # (figure rect, padded crop): text inside is replaced by the figure's own reading
        parts: list[tuple[float, dict]] = []   # (y, finished segment) for reading order

        # ---- figures
        for rect, kinds, chars_inside in figure_parts:
            emit({"event": "working", "page": n, "kind": "figure", "parser": "vision model" if backend else "ocr"})
            t = time.perf_counter()
            crop = padded(page, rect)
            png = crop_png(page, crop)
            tried, parser, md, kind_label, note = [], "none", "", None, ""
            if backend and budget > 0:
                budget -= 1
                try:
                    fig = describe_figure(png)
                    if fig is not None:
                        parser, kind_label = f"vision:{fig.backend}", fig.kind
                        md = f"**Figure (page {n}, {fig.kind})**\n\n{fig.body}"
                        tried.append({"parser": parser, "status": "ok", "ms": int((time.perf_counter() - t) * 1000)})
                        if any(w in fig.kind for w in DROP_TEXT_KINDS):
                            drop_rects.append((rect, crop))
                except Exception as e:  # noqa: BLE001
                    tried.append({"parser": f"vision:{backend}", "status": "error", "error": f"{type(e).__name__}: {e}", "ms": int((time.perf_counter() - t) * 1000)})
                    warnings.append(f"page {n}: figure could not be read by the vision model: {type(e).__name__}: {e}")
            if not md:
                if "raster" in kinds and chars_inside < 20 and ocr_ok:
                    # a picture (screenshot, scan) has no text layer of its own -> OCR it
                    try:
                        from PIL import Image
                        import io

                        txt = ocr_pil_image(Image.open(io.BytesIO(png)), options)
                        tried.append({"parser": "ocr", "status": "ok" if txt else "empty", "ms": int((time.perf_counter() - t) * 1000)})
                        if txt:
                            parser, md = "ocr", f"**Figure (page {n}, picture) - text read by OCR**\n\n{txt}"
                            drop_rects.append((rect, crop))
                    except Exception as e:  # noqa: BLE001
                        tried.append({"parser": "ocr", "status": "error", "error": f"{type(e).__name__}: {e}", "ms": 0})
                if not md:
                    # A note about the parse is not content from the document: it goes in `note`, never into the extracted text.
                    parser = "pymupdf" if chars_inside else "none"
                    note = ("Drawn chart or diagram, not turned into values: its text labels are kept as normal text. "
                            "Set up a vision model (Azure OpenAI or Ollama) to read it as a data table.") if chars_inside else \
                           "Picture found but not read (no vision model or OCR available)."
            why = ("Figure: a vision model reads charts as data tables and diagrams as boxes and arrows"
                   if parser.startswith("vision") else
                   "Figure: no vision model configured - pictures go to OCR, drawn charts keep the PDF's own text labels")
            extra = {"figure_kind": kind_label} if kind_label else {}
            if not md:
                extra.update(note=note, status="unread")
            if thumbs < MAX_FIGURE_THUMBS:
                extra["image"] = "data:image/png;base64," + base64.b64encode(png).decode()
                thumbs += 1
            parts.append((rect.y0, _seg(n, 0, "figure", [tuple(rect)], parser, why, md, tried, int((time.perf_counter() - t) * 1000), **extra)))

        # ---- tables: re-read each one in isolation with the best table parser
        for e in table_els:
            box = e.metadata["bbox"]
            emit({"event": "working", "page": n, "kind": "table", "parser": (t_chain or ["pymupdf"])[0]})
            t = time.perf_counter()
            name, md, tried = None, "", []
            if t_chain:
                pad = 3
                crop = (box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad)
                name, md, tried = _chain(t_chain, _page_pdf(doc, pno, crop), "pdf", opts, _table_accept(e.content))
            if name is None:
                name, md = "pymupdf", e.content   # nothing better produced a table: keep PyMuPDF's own reading
                tried.append({"parser": "pymupdf", "status": "ok", "ms": 0, "note": "fallback: first-pass table"})
            parts.append((box[1], _seg(n, 0, "table", [box], name, t_why if name != "pymupdf" else
                                       "Table: no table parser could improve on PyMuPDF's first pass for this one", md, tried,
                                       int((time.perf_counter() - t) * 1000))))

        # ---- headings and text stay with PyMuPDF (already extracted); consecutive text blocks become one part
        run: list = []

        def flush():
            if run:
                md = "\n\n".join(e.content for e in run)
                parts.append((run[0].metadata["y"], _seg(n, 0, _text_kind(md) if len(run) == 1 else "text",
                                                          [e.metadata["bbox"] for e in run], "pymupdf",
                                                          "Headings and text: pymupdf - 99-100% on digital text in 1-2 s, nothing else was more accurate", md, [{"parser": "pymupdf", "status": "ok", "ms": 0}])))
                run.clear()

        for e in sorted((e for e in els if e.content_type == TEXT and "bbox" in e.metadata), key=lambda e: e.metadata["y"]):
            # inside the figure itself, or a short label (axis title, tick, legend) in the margin the figure was cropped with
            if any(_center_inside(e.metadata["bbox"], r) or
                   ((e.metadata.get("chart_text") or (len(e.content) <= MAX_LABEL_LEN / 3 and not e.content.lower().startswith(("fig", "table", "source", "#"))))
                    and _center_inside(e.metadata["bbox"], c))
                   for r, c in drop_rects):
                continue
            if _text_kind(e.content) == "heading":
                flush()
                run.append(e)
                flush()
            else:
                run.append(e)
        flush()

        for _, seg in sorted(parts, key=lambda p: p[0]):
            seg["id"] = f"p{n}-{nid()}"
            add(seg)
    meta = {"vision_backend": backend, "pages_processed": n_pages, "pages_total": len(doc)}
    return segments, pages, warnings, meta


# --------------------------------------------------------------------------- PDF, one parser for the whole document
def _page_previews(data: bytes, n_pages: int) -> list[dict]:
    import fitz

    doc = fitz.open(stream=data, filetype="pdf")
    pages = []
    for i in range(n_pages):
        page = doc[i]
        info = {"page": i + 1, "width": round(page.rect.width, 1), "height": round(page.rect.height, 1)}
        if i < PREVIEW_PAGES:
            try:
                info["preview"] = "data:image/jpeg;base64," + base64.b64encode(page.get_pixmap(dpi=PREVIEW_DPI).tobytes("jpeg")).decode()
            except Exception:  # noqa: BLE001 - a missing preview must not stop the extraction
                pass
        pages.append(info)
    return pages


def _extract_pdf_whole(data: bytes, file_name: str, profile, options: ParseOptions, include_paid: bool, emit):
    """Classify the PDF, take the parser the scorecard / reports recommend for that type and run it on the whole file.
    If it fails or returns nothing the next one in the chain is tried."""
    import fitz

    from app.routing.router import _rules, route

    candidates = list(route(profile, options, include_paid=include_paid).candidates)
    reasons = dict(_rules(profile, options, include_paid))
    if include_paid and _usable(["azure_di"], "pdf") and "azure_di" not in candidates:
        candidates.insert(0, "azure_di")
        reasons["azure_di"] = "you ticked 'Include paid parsers': Azure Document Intelligence (paid) is tried first"
    group = learned.group_for(profile.to_dict(), "pdf")

    tried, doc, chosen = [], None, None
    for name in candidates:
        emit({"event": "working", "page": 1, "kind": "document", "parser": name})
        t = time.perf_counter()
        try:
            d = normalize_document(get_parser_class(name)().parse(data, file_name, "pdf", options))
        except Exception as e:  # noqa: BLE001 - one failing parser must not stop the document
            tried.append({"parser": name, "status": "error", "ms": int((time.perf_counter() - t) * 1000), "error": f"{type(e).__name__}: {e}"})
            continue
        ms = int((time.perf_counter() - t) * 1000)
        if not any(el.content.strip() for pg in d.pages for el in pg.elements):
            tried.append({"parser": name, "status": "empty", "ms": ms})
            continue
        tried.append({"parser": name, "status": "ok", "ms": ms})
        doc, chosen = d, name
        break
    if doc is None:
        raise RuntimeError(f"no parser produced any content: {tried}")

    why = f"{chosen}: {reasons.get(chosen, 'next parser in the chain')}."
    if len(tried) > 1:
        why += " Tried before it: " + ", ".join(f"{t['parser']} ({t['status']})" for t in tried[:-1]) + "."

    n_pages = limit_pages(len(fitz.open(stream=data, filetype="pdf")), options.max_pages)
    pages = _page_previews(data, n_pages)
    segments: list[dict] = []
    for page in doc.pages:
        emit({"event": "page", "page": page.page_number, "pages": len(doc.pages)})
        k = 0
        for e in page.elements:
            if not e.content.strip():
                continue
            k += 1
            md = e.content.strip()
            kind = {TABLE: "table", IMAGE: "figure"}.get(e.content_type) or ("heading" if md.startswith("#") and "\n" not in md else "text")
            seg = _seg(page.page_number, k, kind, [], chosen, why, md, tried)
            segments.append(seg)
            emit({"event": "segment", "segment": seg, "has_image": False})
    from app.vision import pick_backend

    meta = {"engine": chosen, "mode": "document", "pages_processed": n_pages, "pages_total": n_pages,
            "vision_backend": pick_backend() if chosen == "smart_pdf" else None}
    warnings = list(doc.warnings)
    if profile.figure_count and chosen != "smart_pdf":
        warnings.append(
            f"{profile.figure_count} figure(s) (charts, diagrams or pictures) on {profile.figure_pages} page(s): {chosen} reads the words in them "
            "but not chart values. smart_pdf reads them when a vision model is set up (Azure OpenAI also needs 'Include paid parsers'); "
            "the 'By part' mode reads each figure with the vision model too.")
    return segments, pages, warnings, meta


# --------------------------------------------------------------------------- everything that is not a PDF
def _extract_other(data: bytes, file_name: str, file_type: str, options: ParseOptions, include_paid: bool, emit):
    """Word / PowerPoint / Excel / CSV / image: the router's native parser reads the file; each of its elements becomes a part."""
    from app.pipeline import parse_bytes

    if file_type == "image":
        chain, img_why = _measured_chain("Image file", ["image"], None, "image", options, False, ["vlm", "easyocr", "ocr"] if options.prefer_quality else ["easyocr", "ocr"])
        emit({"event": "working", "page": 1, "kind": "image", "parser": (chain or ["none"])[0]})
        t = time.perf_counter()
        name, md, tried = _chain(chain, data, "image", options, lambda m: bool(m.strip()))
        seg = _seg(1, 1, "image", [], name or "none", img_why, md, tried, int((time.perf_counter() - t) * 1000))
        emit({"event": "segment", "segment": seg, "has_image": False})
        return [seg], [{"page": 1}], [], {}

    res = parse_bytes(data, file_name, options)
    engine = res.document.engine
    why = f"{file_type.upper()} file: the native {engine} parser keeps headings, lists and tables (scored 0.96-1.0 in our tests)"
    segments, pages = [], []
    for page in res.document.pages:
        emit({"event": "page", "page": page.page_number, "pages": len(res.document.pages)})
        pages.append({"page": page.page_number})
        k, run = 0, []

        def flush():
            nonlocal k
            if run:
                k += 1
                md = "\n\n".join(run)
                seg = _seg(page.page_number, k, "text", [], engine, why, md, [{"parser": engine, "status": "ok", "ms": 0}])
                segments.append(seg)
                emit({"event": "segment", "segment": seg, "has_image": False})
                run.clear()

        for e in page.elements:
            if not e.content.strip():
                continue
            if e.content_type == TEXT and not _text_kind(e.content) == "heading":
                run.append(e.content.strip())
                continue
            flush()
            k += 1
            kind = {TABLE: "table", IMAGE: "figure"}.get(e.content_type, "heading")
            seg = _seg(page.page_number, k, kind, [], engine, why, e.content.strip(), [{"parser": engine, "status": "ok", "ms": 0}])
            segments.append(seg)
            emit({"event": "segment", "segment": seg, "has_image": False})
        flush()
    return segments, pages, list(res.document.warnings), {"engine": engine}


# --------------------------------------------------------------------------- entry point
def extract_document(data: bytes, file_name: str, options: Optional[ParseOptions] = None,
                     include_paid: bool = False, progress: Optional[Callable[[dict], None]] = None, mode: str = "part") -> dict:
    """`progress`, if given, gets small dicts as the work goes (start, page, working, segment) so the UI can show live status."""
    options = options or ParseOptions()
    emit = progress or (lambda _e: None)
    t0 = time.perf_counter()
    file_type = resolve_file_type(data, file_name)
    profile = analyze(data, file_type, options)
    emit({"event": "start", "file_type": file_type, "profile": profile.to_dict()})
    warnings0: list[str] = []
    mode = "document" if mode == "document" and file_type == "pdf" else "part"
    if file_type == "pdf" and mode == "document":
        try:
            segments, pages, warnings, meta = _extract_pdf_whole(data, file_name, profile, options, include_paid, emit)
        except Exception as e:  # noqa: BLE001 - fall back to the per-part route rather than failing
            log.exception("by-document extraction failed")
            warnings0.append(f"Reading the whole document with one parser failed ({e}); it was read part by part instead.")
            mode = "part"
    if file_type == "pdf" and mode == "part":
        segments, pages, warnings, meta = _extract_pdf(data, file_name, options, include_paid, emit)
        meta = {**meta, "mode": "part"}
    elif file_type != "pdf":
        segments, pages, warnings, meta = _extract_other(data, file_name, file_type, options, include_paid, emit)
        meta = {**meta, "mode": "native"}
    warnings = warnings0 + warnings
    try:
        routing = routing_evidence(profile.to_dict(), file_type, options, include_paid, mode, meta.get("engine") if mode == "document" else None)
    except Exception:  # noqa: BLE001 - the evidence panel is informational; it must never stop an extraction
        log.exception("could not build the routing evidence")
        routing = None

    page_md: dict[int, list[str]] = {}
    for s in segments:
        if s["content"].strip():
            page_md.setdefault(s["page"], []).append(s["content"].strip())
    for p in pages:
        p["content"] = "\n\n".join(page_md.get(p["page"], []))
    markdown = "\n\n".join(p["content"] for p in pages if p["content"])

    by_kind: dict[str, dict] = {}
    parsers_used: Counter = Counter()
    for s in segments:
        k = by_kind.setdefault(s["kind"], {"count": 0, "parsers": {}, "words": 0})
        k["count"] += 1
        k["words"] += s["words"]
        k["parsers"][s["parser"]] = k["parsers"].get(s["parser"], 0) + 1
        parsers_used[s["parser"]] += 1
    empty = [s["id"] for s in segments if s["status"] == "empty"]
    unread = [s["id"] for s in segments if s["status"] == "unread"]
    if unread:
        warnings.append(f"{len(unread)} figure(s) were found but not read ({', '.join(unread)}). They are flagged, not written into the text.")
    return {
        "file_name": file_name, "file_type": file_type, "profile": profile.to_dict(),
        "segments": segments, "pages": pages, "markdown": markdown, "warnings": warnings,
        "summary": {"segments": len(segments), "by_kind": by_kind, "parsers_used": dict(parsers_used),
                    "empty_segments": empty, "unread_figures": unread, "words": len(markdown.split()), "routing": routing,
                    "total_ms": int((time.perf_counter() - t0) * 1000), **meta},
    }
