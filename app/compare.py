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


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_`]", "", s)).strip().lower()


def _headings(md: str) -> list[str]:
    return [_norm(l.lstrip("#")) for l in md.splitlines() if l.lstrip().startswith("#")]


def _table_cells(md: str) -> list[str]:
    cells = []
    for line in md.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.fullmatch(r"[|\-:\s]+", line):
            continue
        cells += [_norm(c) for c in line.strip("|").split("|") if _norm(c)]
    return cells


def _list_f1(truth: list[str], got: list[str]) -> float:
    a, b = Counter(truth), Counter(got)
    overlap = sum((a & b).values())
    if not overlap:
        return 0.0
    p, r = overlap / sum(b.values()), overlap / sum(a.values())
    return 2 * p * r / (p + r)


def score_against_truth(truth: str, out: str) -> dict:
    """text = word F1, headings = F1 of heading lines, tables = F1 of table cells (the last two only
    when the truth has any). score = average of the parts that apply (0..1)."""
    s = {"text": word_f1(truth, out)}
    th = _headings(truth)
    if th:
        s["headings"] = _list_f1(th, _headings(out))
    tc = _table_cells(truth)
    if tc:
        s["tables"] = _list_f1(tc, _table_cells(out))
    s["score"] = sum(s.values()) / len(s)
    return {k: round(v, 3) for k, v in s.items()}


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
            # Keep the complete extraction so the comparison view can show what
            # each parser actually returned, not just a short sample.
            row["output"] = doc.markdown
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
            sc = score_against_truth(reference_text, mine)  # separate keys: 'headings'/'tables' already hold parser counts
            row.update(score=sc["score"], text_score=sc["text"], headings_score=sc.get("headings"), tables_score=sc.get("tables"))
        elif row.get("heuristic") is not None:
            row["score"] = row["heuristic"]

    key = "score"
    ranked = sorted([r for r in rows if r.get("status") == "ok" and r.get(key) is not None],
                    key=lambda r: (-r[key], r["elapsed_ms"]))
    return {
        "file_name": file_name,
        "file_type": file_type,
        "profile": profile.to_dict(),
        "router_would_pick": auto_pick,
        "has_reference": bool(reference_text),
        "ranked_by": "score vs your reference text (words + headings + tables)" if reference_text else "heuristic = coverage x agreement (NO ground truth - provide reference_text for a real ranking)",
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
        "| parser | status | ms | pages | words | headings | tables | images | coverage | agreement | f1 | score |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in cmp["results"]:
        lines.append(
            f"| {r['parser']} | {r['status']} | {r.get('elapsed_ms','')} | {r.get('pages','')} | {r.get('words','')} | "
            f"{r.get('headings','')} | {r.get('tables','')} | {r.get('images','')} | {r.get('coverage','')} | {r.get('agreement','')} | {r.get('f1','')} | {r.get('score','')} |"
        )
        if r["status"] == "error":
            lines.append(f"|  | ↳ {r['error']} | | | | | | | | | |")
    return "\n".join(lines)
