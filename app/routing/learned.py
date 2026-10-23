"""
Evidence-based routing: which parser is best for which kind of document, taken from a fresh head-to-head test.

Two sources, merged per (document group, parser):
  - measured_scores.json  built by scripts/build_routing_table.py from eval/head_to_head/results.jsonl: every parser run on every
                          test document with a hand-written answer file. Nothing from older reports is used.
  - live runs             every "Compare parsers" run in the UI that was scored against YOUR reference text
                          (runs scored against Azure DI are ignored: they measure imitation, not correctness)
So the table gets better every time you compare a document with a reference. Nothing here is hard-coded per parser.

Choice rule: highest score wins; parsers within TIE points of the best are treated as tied and the FASTEST of
them goes first. With "prefer quality" TIE is 0, so speed only breaks an exact tie.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import time
from pathlib import Path
from typing import Optional

from app import benchmark
from app.parsers import get_parser_class

TIE = 0.1             # score points (0-5 scale) inside which two parsers count as tied
REFERENCE_KIND = "your reference text"
ALL = "all documents"   # pool over every test document: used for the parameters that only some documents can test (tables)
METRICS = benchmark.METRICS
# our own pipelines glued from the other engines (PyMuPDF + OCR [+ vision model]); they compete like any other parser
COMBOS = {"smart_pdf", "hybrid_pdf"}

_SEED = Path(__file__).with_name("measured_scores.json")


def group_for(profile: dict, file_type: str) -> str:
    """PDFs are grouped by what is inside them (digital, tables, mixed, scanned, figures); other files by their type."""
    return benchmark.group_of(profile, file_type) if file_type == "pdf" else file_type


def _seed() -> dict:
    try:
        return json.loads(_SEED.read_text(encoding="utf-8"))["groups"]
    except (OSError, ValueError, KeyError):
        return {}


def _live() -> dict:
    """group -> parser -> {'ms': [metric lists], 's': [seconds]} from runs scored against a user-supplied reference."""
    out: dict = {}
    for rec in benchmark.runs():
        if rec.get("reference_kind") != REFERENCE_KIND:
            continue
        for row in rec["rows"]:
            if row.get("ref") or all(v is None for v in row["m"]):
                continue
            for g in (rec["group"], ALL):    # every document also counts toward the all-documents pool
                e = out.setdefault(g, {}).setdefault(row["p"], {"ms": [], "s": []})
                e["ms"].append(row["m"])
                e["s"].append(row["s"])
    return out


def _avg(pairs: list[tuple[float, float]]) -> Optional[float]:
    """weighted mean of (value, weight), skipping missing values"""
    pairs = [(v, w) for v, w in pairs if v is not None]
    w = sum(w for _, w in pairs)
    return sum(v * w for v, w in pairs) / w if w else None


def table() -> dict:
    """group -> parser -> {'m': [8 values or None], 's': seconds, 'docs': n, 'live': n_live_docs}"""
    seed, live = _seed(), _live()
    merged: dict = {}
    for g in set(seed) | set(live):
        sg = seed.get(g, {"docs": 0, "parsers": {}})
        for p in set(sg["parsers"]) | set(live.get(g, {})):
            parts = []     # (metrics, seconds, weight)
            if p in sg["parsers"]:
                parts.append((sg["parsers"][p]["m"], sg["parsers"][p]["s"], sg["parsers"][p].get("n", sg["docs"])))
            lv = live.get(g, {}).get(p)
            if lv:
                n = len(lv["ms"])
                parts.append(([_avg([(ms[i], 1) for ms in lv["ms"]]) for i in range(8)], sum(lv["s"]) / n, n))
            merged.setdefault(g, {})[p] = {
                "m": [_avg([(m[i], w) for m, _, w in parts]) for i in range(8)],
                "s": _avg([(s, w) for _, s, w in parts]),
                "docs": sum(w for *_, w in parts), "live": len(lv["ms"]) if lv else 0,
            }
    return merged


def _score(m: list, metric: Optional[str]) -> Optional[float]:
    if metric:
        return m[METRICS.index(metric)]
    vals = [v for v in m if v is not None]
    return sum(vals) / len(vals) if vals else None


# is_available() of most parsers imports the whole library (torch, langchain, llama_index, haystack...): minutes on a cold start.
# For ranking it is enough to know the library is installed; if it then fails on a document the chain moves to the next parser.
_FAST_SPEC = {"pymupdf": "fitz", "pymupdf4llm": "pymupdf4llm", "docling": "docling", "easyocr": "easyocr", "unstructured": "unstructured",
              "markitdown": "markitdown", "pdfplumber": "pdfplumber", "pdfminer": "pdfminer", "langchain_loader": "langchain_community",
              "llamaindex_reader": "llama_index", "haystack_converter": "haystack", "hybrid_pdf": "fitz", "smart_pdf": "fitz",
              "docx": "docx", "pptx": "pptx", "spreadsheet": "openpyxl"}
_avail_cache: dict[str, tuple[float, bool]] = {}


def _usable(name: str, file_type: str, include_paid: bool) -> bool:
    try:
        cls = get_parser_class(name)
    except KeyError:
        return False
    if file_type not in cls.supported_types:
        return False
    if name == "smart_pdf":
        # labelled "paid" only because its vision step MAY call a paid API: a free local model (Ollama) costs nothing, Azure OpenAI
        # needs paid parsers to be allowed, and with no vision model at all it cannot read charts, so it must not be ranked
        from app.vision import pick_backend

        backend = pick_backend()
        if backend is None or not (include_paid or backend == "ollama"):
            return False
    elif not (include_paid or cls.cost not in ("paid", "cloud")):
        return False
    now = time.time()
    hit = _avail_cache.get(name)
    if hit and now - hit[0] < 300:
        return hit[1]
    if name in _FAST_SPEC:
        ok = importlib.util.find_spec(_FAST_SPEC[name]) is not None   # installed? without importing it
    elif name == "opendataloader":
        ok = bool(shutil.which("java")) and importlib.util.find_spec("langchain_opendataloader_pdf") is not None
    else:
        ok = cls.is_available()[0]
    _avail_cache[name] = (now, ok)
    return ok


def rank(groups: list[str], metric: Optional[str] = None, *, file_type: str = "pdf", include_paid: bool = False,
         prefer_quality: bool = False, exclude: set[str] = frozenset()) -> list[dict]:
    """Parsers best-first for these document groups (pooled by document count), judged on one metric or on all of them.
    Each entry: parser, score (0-5), secs, docs, live (docs from your own comparisons), tied (True if it won on speed)."""
    tbl = table()
    pooled: dict[str, list] = {}
    for g in groups:
        for p, e in tbl.get(g, {}).items():
            sc = _score(e["m"], metric)
            if sc is not None and p not in exclude and _usable(p, file_type, include_paid):
                pooled.setdefault(p, []).append((sc, e["s"], e["docs"], e["live"]))
    rows = []
    for p, v in pooled.items():
        rows.append({"parser": p, "score": round(_avg([(a, d) for a, _, d, _ in v]), 2),
                     "secs": round(_avg([(s, d) for _, s, d, _ in v]) or 0.0, 1),
                     "docs": sum(d for *_, d, _ in v), "live": sum(x for *_, x in v)})
    if not rows:
        return []
    best = max(r["score"] for r in rows)
    tol = 0.0 if prefer_quality else TIE
    pool = sorted((r for r in rows if r["score"] >= best - tol), key=lambda r: (r["secs"], -r["score"]))
    rest = sorted((r for r in rows if r["score"] < best - tol), key=lambda r: (-r["score"], r["secs"]))
    for r in pool:
        r["tied"] = len(pool) > 1
    return pool + rest


def evidence(entry: dict, group: str, metric: Optional[str] = None) -> str:
    what = metric.lower() if metric else "overall score"
    src = f", {entry['live']} from your own comparisons" if entry.get("live") else ""
    return f"{entry['score']:.2f}/5 {what} on {entry['docs']} '{group}' test document(s) in our head-to-head test{src}, {entry['secs']:.1f}s"
