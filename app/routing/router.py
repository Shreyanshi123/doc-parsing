"""
Router: profile + options -> ordered list of parsers to try.

THIS IS THE FILE TO EDIT when you learn from the POC which engine wins for which data.
Each rule appends (parser_name, reason). The pipeline tries them in order (fallback chain).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.models import ParseOptions
from app.parsers import get_parser_class
from app.routing import learned
from app.routing.analyzer import DocProfile


@dataclass
class RoutingDecision:
    selected: str
    candidates: list[str]
    reason: str
    overridden: bool = False
    skipped: dict[str, str] = field(default_factory=dict)  # parser -> why not usable
    notes: list[str] = field(default_factory=list)         # things worth knowing, e.g. "charts found, values not read"

    def to_dict(self):
        return {
            "selected": self.selected,
            "candidates": self.candidates,
            "reason": self.reason,
            "overridden": self.overridden,
            "skipped": self.skipped,
            "notes": self.notes,
        }


class NoParserAvailable(Exception):
    pass


def smart_pdf_ok(include_paid: bool) -> bool:
    """smart_pdf is only worth choosing when a vision model can actually read the figures: a free local one,
    or Azure OpenAI (which costs money, so only when paid parsers are allowed)."""
    return learned._usable("smart_pdf", "pdf", include_paid)


def _rules(profile: DocProfile, options: ParseOptions, include_paid: bool = False) -> list[tuple[str, str]]:
    """The parsers that scored best on documents like this in our head-to-head test come first (best score; within a tie the
    fastest). The hand-written rules below are only the tail of the chain, used if the measured ones all fail or there is no data."""
    group = learned.group_for(profile.to_dict(), profile.file_type)
    measured = []
    for i, e in enumerate(learned.rank([group], file_type=profile.file_type, include_paid=include_paid, prefer_quality=options.prefer_quality)[:5]):
        how = ("fastest of the parsers tied for best" if e.get("tied") else "highest score") if i == 0 else "next best"
        measured.append((e["parser"], f"{how} for a '{group}' document: {learned.evidence(e, group)}"))
    return measured + _report_rules(profile, options, include_paid)


def _report_rules(profile: DocProfile, options: ParseOptions, include_paid: bool = False) -> list[tuple[str, str]]:
    """FALLBACK ONLY: the older hand-written recommendation, used when the measured table has no usable parser for this document."""
    ft, cls = profile.file_type, profile.classification
    q = options.prefer_quality

    if ft == "pdf":
        tables = "tables" in profile.traits
        r: list[tuple[str, str]] = []
        if profile.figure_count and smart_pdf_ok(include_paid):
            r.append(("smart_pdf", "charts / diagrams found -> smart_pdf, the only parser that read chart values and diagram arrows (BENCHMARK_REPORT: charts 4.5/5, diagrams 5.0/5; every ready-made parser 0)"))
        if cls == "digital":
            if tables:
                r += [("pymupdf4llm", "digital PDF with tables / columns -> pymupdf4llm (REPORT: kept 80% of table cells in the 15-page paper, pymupdf only 12%)"),
                      ("docling", "backup: most accurate on tables (95%) but ~15x slower"),
                      ("hybrid_pdf", "backup: ties on simple tables (BENCHMARK_REPORT 30.0) but weak on multi-column layouts"),
                      ("pymupdf", "last resort for tables: fast but loses table structure")]
            else:
                r += [("pymupdf", "simple digital PDF (text, no tables) -> pymupdf (REPORT: 99-100% on both Wikipedia tests in 1-2 s)"),
                      ("hybrid_pdf", "backup: same result (BENCHMARK_REPORT 25.0, 1.4 s)"),
                      ("pymupdf4llm", "backup: same text, richer Markdown")]
            if q:
                r.insert(0, ("docling", "prefer quality -> docling (most accurate in REPORT, 30-250x slower)"))
            return r + [("ocr", "last resort")]
        if cls == "scanned":
            r += [("pymupdf4llm", "scanned PDF -> pymupdf4llm (REPORT: 93% in 21 s; BENCHMARK_REPORT 24.2 vs Azure DI 24.9)"),
                  ("docling", "backup: best free quality on scans (98%) but slowest"),
                  ("ocr", "plain-text OCR: reads the words (97%) but no headings"),
                  ("vlm", "vision LLM alternative for scans")]
            if q:
                r.insert(0, ("docling", "prefer quality -> docling (98% on the scan test, 24.6 in BENCHMARK_REPORT)"))
            return r
        # mixed / unknown
        r += [("pymupdf4llm", "mixed PDF (text pages + scanned pages) -> pymupdf4llm (REPORT: scored 1.0; pymupdf drops the scanned page; BENCHMARK_REPORT 29.5 vs Azure DI 29.8)"),
              ("hybrid_pdf", "backup: decides per page, but the scanned page comes back without headings (0.89)"),
              ("ocr", "OCR everything")]
        if q:
            r.insert(0, ("docling", "prefer quality -> docling (BENCHMARK_REPORT: 29.9 on mixed, the best free score, ~6x slower)"))
        return r
    if ft == "image":
        r = [("easyocr", "image file -> easyocr (REPORT: read UI text most cleanly)"), ("ocr", "backup: 3-18x faster, noisier"), ("vlm", "vision LLM alternative")]
        return [r[2], r[0], r[1]] if q else r
    if ft == "docx":
        return [("docx", "native Word parser keeps headings/lists/tables (REPORT: 1.0)"), ("docling", "fallback")]
    if ft == "pptx":
        return [("pptx", "native PowerPoint parser, one page per slide (REPORT: 0.96)"), ("docling", "fallback")]
    if ft in ("xlsx", "csv"):
        return [("spreadsheet", "native spreadsheet parser (REPORT: ~1.0, 0.1 s)")]
    return [("text", "plain text")]


def route(profile: DocProfile, options: ParseOptions, override: str | None = None, include_paid: bool = False) -> RoutingDecision:
    if override and override != "auto":
        cls = get_parser_class(override)
        ok, why = cls.is_available()
        if not ok:
            raise NoParserAvailable(f"Parser '{override}' is not available: {why}")
        if profile.file_type not in cls.supported_types:
            raise NoParserAvailable(f"Parser '{override}' does not support '{profile.file_type}'")
        return RoutingDecision(override, [override], "caller forced this parser", overridden=True)

    chosen: list[tuple[str, str]] = []
    skipped: dict[str, str] = {}
    for name, why in _rules(profile, options, include_paid):
        try:
            cls = get_parser_class(name)
        except KeyError:
            continue
        ok, reason = cls.is_available()
        if ok and profile.file_type in cls.supported_types and name not in [c for c, _ in chosen]:
            chosen.append((name, why))
        elif not ok:
            skipped[name] = reason
    if not chosen:
        raise NoParserAvailable(f"No available parser for {profile.file_type}/{profile.classification}. Skipped: {skipped}")
    decision = RoutingDecision(
        selected=chosen[0][0],
        candidates=[c for c, _ in chosen],
        reason=chosen[0][1],
        skipped=skipped,
    )
    if profile.figure_count and decision.selected not in ("smart_pdf", "vlm"):
        decision.notes.append(
            f"{profile.figure_count} figure(s) (charts / diagrams / pictures) on {profile.figure_pages} page(s): "
            f"{decision.selected} does not read chart values. Use smart_pdf or vlm (paid, needs a vision model) if you need them."
        )
    return decision
