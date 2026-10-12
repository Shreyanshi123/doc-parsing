"""
The "black box": bytes in -> routed -> parsed -> normalized -> structured JSON out.

    resolve type -> analyze -> route -> parse (with fallback chain) -> normalize -> output dict
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

from app.models import ParseOptions, ParsedDocument
from app.normalizer import normalize_document
from app.parsers import get_parser_class
from app.routing.analyzer import DocProfile, analyze
from app.routing.file_type import resolve_file_type
from app.routing.router import RoutingDecision, route

log = logging.getLogger("pipeline")


class ParseFailed(Exception):
    pass


@dataclass
class PipelineResult:
    document: ParsedDocument
    profile: DocProfile
    routing: RoutingDecision
    attempts: list[dict[str, Any]]
    timings_ms: dict[str, int]


def _has_content(doc: ParsedDocument) -> bool:
    return any(p.markdown.strip() for p in doc.pages)


def parse_bytes(
    data: bytes,
    file_name: str,
    options: Optional[ParseOptions] = None,
    parser: Optional[str] = None,
) -> PipelineResult:
    options = options or ParseOptions()
    t0 = time.perf_counter()
    file_type = resolve_file_type(data, file_name)
    profile = analyze(data, file_type, options)
    t1 = time.perf_counter()
    decision = route(profile, options, parser)
    log.info("route %s (%s) -> %s", file_name, profile.classification, decision.candidates)

    attempts: list[dict[str, Any]] = []
    final: Optional[ParsedDocument] = None
    t_parse = time.perf_counter()
    for name in decision.candidates:
        started = time.perf_counter()
        try:
            doc = get_parser_class(name)().parse(data, file_name, file_type, options)
            doc = normalize_document(doc)
            ms = int((time.perf_counter() - started) * 1000)
            if not _has_content(doc) and not decision.overridden:
                attempts.append({"parser": name, "status": "empty", "ms": ms})
                continue  # try next candidate
            attempts.append({"parser": name, "status": "ok", "ms": ms})
            final = doc
            decision.selected = name
            break
        except Exception as e:  # noqa: BLE001 - any parser failure triggers fallback
            log.warning("parser %s failed: %s", name, e)
            attempts.append(
                {"parser": name, "status": "error", "error": f"{type(e).__name__}: {e}",
                 "ms": int((time.perf_counter() - started) * 1000)}
            )
    if final is None:
        raise ParseFailed(f"All parsers failed/empty for '{file_name}': {attempts}")

    t_end = time.perf_counter()
    return PipelineResult(
        final, profile, decision, attempts,
        {"analyze_route": int((t1 - t0) * 1000), "parse": int((t_end - t_parse) * 1000),
         "total": int((t_end - t0) * 1000)},
    )


def build_output(
    result: PipelineResult,
    *,
    file_id: str = "",
    tenant_id: str = "",
    include_images: bool = True,
) -> dict[str, Any]:
    """Final JSON contract returned by the API / saved to the output store."""
    out = result.document.to_dict(include_images=include_images)
    out["metadata"].update({"file_id": file_id, "tenant_id": tenant_id})
    out["routing"] = {**result.routing.to_dict(), "profile": result.profile.to_dict(), "attempts": result.attempts}
    out["stats"] = result.document.stats()
    out["timings_ms"] = result.timings_ms
    return out
