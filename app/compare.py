"""
POC evaluation harness: run EVERY applicable free parser on the same document and
produce comparable metrics. Optionally score against a reference text you provide.

Metrics
  - elapsed_ms, pages, chars, words, headings, tables, images, empty_pages
  - coverage: words captured / words of the most complete parser (detects dropped scanned pages)
  - agreement: average word-level F1 vs. the other non-empty parsers (no ground truth needed)
  - heuristic: coverage x agreement - a rough guide ONLY; consensus is not correctness
  - f1 / similarity: vs. `reference_text` when supplied (ground truth)
"""
from __future__ import annotations

import difflib
import re
import time
from collections import Counter
from typing import Optional

from app.models import ParseOptions
from app.normalizer import normalize_document
from app.parsers import get_parser_class, parsers_for
from app.routing.analyzer import analyze
from app.routing.file_type import resolve_file_type
from app.routing.router import route


def _tokens(text: str) -> list[str]:
    text = re.sub(r"[#*|>`_\-]+", " ", text.lower())  # ignore markdown syntax
    return re.findall(r"\w+", text)


def word_f1(a: str, b: str) -> float:
    ta, tb = Counter(_tokens(a)), Counter(_tokens(b))
    if not ta or not tb:
        return 0.0
    overlap = sum((ta & tb).values())
    if overlap == 0:
        return 0.0
    p, r = overlap / sum(tb.values()), overlap / sum(ta.values())
    return 2 * p * r / (p + r)


def similarity(a: str, b: str, limit: int = 20000) -> float:
    return difflib.SequenceMatcher(None, " ".join(_tokens(a))[:limit], " ".join(_tokens(b))[:limit], autojunk=False).ratio()


def compare_parsers(
    data: bytes,
    file_name: str,
    options: Optional[ParseOptions] = None,
    reference_text: Optional[str] = None,
    parsers: Optional[list[str]] = None,
    include_paid: bool = False,
) -> dict:
    options = options or ParseOptions()
    file_type = resolve_file_type(data, file_name)
    profile = analyze(data, file_type, options)
    try:
        auto_pick = route(profile, options).selected
    except Exception:
        auto_pick = None

    if parsers:
        classes = [get_parser_class(p) for p in parsers]
    else:
        classes = [c for c in parsers_for(file_type) if include_paid or c.cost not in ("paid", "cloud")]

    rows, outputs = [], {}
    for cls in classes:
        row = {"parser": cls.name, "cost": cls.cost}
        t = time.perf_counter()
        try:
            doc = normalize_document(cls().parse(data, file_name, file_type, options))
            row["elapsed_ms"] = int((time.perf_counter() - t) * 1000)
            row.update(doc.stats())
            row["status"] = "ok"
            outputs[cls.name] = doc.markdown
            row["preview"] = doc.markdown[:500]
        except Exception as e:  # noqa: BLE001
            row.update(status="error", error=f"{type(e).__name__}: {e}",
                       elapsed_ms=int((time.perf_counter() - t) * 1000))
        rows.append(row)

    # scoring -------------------------------------------------------------
    ok_names = list(outputs)
    non_empty = [n for n in ok_names if outputs[n].strip()]
    max_words = max((len(outputs[n].split()) for n in non_empty), default=0)
    for row in rows:
        if row["status"] != "ok":
            continue
        mine = outputs[row["parser"]]
        # coverage: how much text did this parser capture vs the most complete one (catches dropped scanned pages)
        row["coverage"] = round(len(mine.split()) / max_words, 3) if max_words else 0.0
        # agreement: avg word-F1 vs other NON-EMPTY outputs
        others = [n for n in non_empty if n != row["parser"]]
        row["agreement"] = (
            round(sum(word_f1(outputs[o], mine) for o in others) / len(others), 3) if others and mine.strip() else None
        )
        # heuristic (only used when there is no reference text)
        row["heuristic"] = round(row["coverage"] * (row["agreement"] if row["agreement"] is not None else 1.0), 3)
        if reference_text:
            row["f1"] = round(word_f1(reference_text, mine), 3)
            row["similarity"] = round(similarity(reference_text, mine), 3)

    key = "f1" if reference_text else "heuristic"
    ranked = sorted([r for r in rows if r.get("status") == "ok" and r.get(key) is not None],
                    key=lambda r: (-r[key], r["elapsed_ms"]))
    return {
        "file_name": file_name,
        "file_type": file_type,
        "profile": profile.to_dict(),
        "router_would_pick": auto_pick,
        "ranked_by": "f1 (vs your reference text)" if reference_text else "heuristic = coverage x agreement (NO ground truth - provide reference_text for a real ranking)",
        "ranking": [r["parser"] for r in ranked],
        "results": rows,
    }


def report_markdown(cmp: dict) -> str:
    lines = [
        f"# Parser comparison - {cmp['file_name']}",
        f"- type: **{cmp['file_type']}**, classification: **{cmp['profile']['classification']}**, pages: {cmp['profile']['page_count']}",
        f"- router would pick: **{cmp['router_would_pick']}**",
        f"- ranked by: {cmp['ranked_by']}",
        f"- ranking: {' > '.join(cmp['ranking']) or 'n/a'}",
        "",
        "| parser | status | ms | pages | words | headings | tables | images | coverage | agreement | f1 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in cmp["results"]:
        lines.append(
            f"| {r['parser']} | {r['status']} | {r.get('elapsed_ms','')} | {r.get('pages','')} | {r.get('words','')} | "
            f"{r.get('headings','')} | {r.get('tables','')} | {r.get('images','')} | {r.get('coverage','')} | {r.get('agreement','')} | {r.get('f1','')} |"
        )
        if r["status"] == "error":
            lines.append(f"|  | ↳ {r['error']} | | | | | | | | | |")
    return "\n".join(lines)
