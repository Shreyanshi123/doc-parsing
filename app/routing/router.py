"""
Router: profile + options -> ordered list of parsers to try.

THIS IS THE FILE TO EDIT when you learn from the POC which engine wins for which data.
Each rule appends (parser_name, reason). The pipeline tries them in order (fallback chain).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.models import ParseOptions
from app.parsers import get_parser_class
from app.routing.analyzer import DocProfile


@dataclass
class RoutingDecision:
    selected: str
    candidates: list[str]
    reason: str
    overridden: bool = False
    skipped: dict[str, str] = field(default_factory=dict)  # parser -> why not usable

    def to_dict(self):
        return {
            "selected": self.selected,
            "candidates": self.candidates,
            "reason": self.reason,
            "overridden": self.overridden,
            "skipped": self.skipped,
        }


class NoParserAvailable(Exception):
    pass


def _rules(profile: DocProfile, options: ParseOptions) -> list[tuple[str, str]]:
    ft, cls = profile.file_type, profile.classification
    q = options.prefer_quality

    if ft == "pdf":
        if cls == "digital":
            r = [("pymupdf", "PDF has a real text layer -> fastest, most accurate extraction"),
                 ("pdfminer", "fallback text engine")]
            if q:
                r.insert(0, ("vlm", "prefer_quality=true -> vision LLM first"))
            return r + [("hybrid_pdf", "fallback"), ("ocr", "last resort")]
        if cls == "scanned":
            r = [("ocr", "pages are images (no text layer) -> OCR"),
                 ("vlm", "vision LLM alternative for scans")]
            if q:
                r.reverse()
            return r
        # mixed / unknown
        r = [("hybrid_pdf", "some pages have text, some are scans -> decide per page"),
             ("ocr", "OCR everything"), ("pymupdf", "text layer only")]
        if q:
            r.insert(0, ("vlm", "prefer_quality=true -> vision LLM first"))
        return r
    if ft == "image":
        r = [("ocr", "image file -> OCR"), ("vlm", "vision LLM alternative")]
        return list(reversed(r)) if q else r
    if ft == "docx":
        return [("docx", "native Word parser keeps headings/lists/tables"), ("docling", "fallback")]
    if ft == "pptx":
        return [("pptx", "native PowerPoint parser (one page per slide)"), ("docling", "fallback")]
    if ft in ("xlsx", "csv"):
        return [("spreadsheet", "native spreadsheet parser")]
    return [("text", "plain text")]


def route(profile: DocProfile, options: ParseOptions, override: str | None = None) -> RoutingDecision:
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
    for name, why in _rules(profile, options):
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
    return RoutingDecision(
        selected=chosen[0][0],
        candidates=[c for c, _ in chosen],
        reason=chosen[0][1],
        skipped=skipped,
    )
