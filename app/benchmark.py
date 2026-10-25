"""
Live benchmark: every "Compare parsers" run that was scored (against your reference text or Azure DI)
is saved here as one small record. The Benchmark tab averages the records per document type, so the
scorecard grows with every document you compare. Nothing is hard-coded.

Record = one document: its type, and for every parser the 8 scorecard values (0-5), total, seconds,
tables / figures it found. Parser outputs are NOT stored (the file stays small).
"""
from __future__ import annotations

import json
import statistics
import threading
import time
import uuid
from statistics import mean
from pathlib import Path
from typing import Optional

from app.config import settings

METRICS = ["Text Accuracy", "Table Reconstruction", "Chart Understanding", "Infographic Parsing",
           "Entity & Numeric Fidelity", "Structure", "Completeness", "Hallucination Penalty"]
GROUPS = ["digital", "digital + tables", "mixed", "scanned", "digital + charts/images", "other"]
_lock = threading.Lock()


def _path():
    d = settings.data_dir / "benchmark"
    d.mkdir(parents=True, exist_ok=True)
    return d / "runs.jsonl"


def group_of(profile: dict, file_type: str) -> str:
    if file_type != "pdf":
        return "other"
    cls, traits = profile.get("classification"), profile.get("traits") or []
    if cls == "scanned":
        return "scanned"
    if cls == "mixed":
        return "mixed"
    if "figures" in traits:
        return "digital + charts/images"
    if "tables" in traits:
        return "digital + tables"
    return "digital"


def runs() -> list[dict]:
    p = _path()
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def _write(items: list[dict]) -> None:
    _path().write_text("".join(json.dumps(r) + "\n" for r in items), encoding="utf-8")


def record(cmp: dict) -> Optional[dict]:
    """Save a finished comparison. Returns the record, or None when nothing was scored (no reference to score against)."""
    rows = []
    for r in cmp.get("results", []):
        if r.get("status") != "ok":
            continue
        card = r.get("scorecard")
        if not card and not r.get("is_reference"):
            continue
        rows.append({
            "p": r["parser"], "cost": r.get("cost", "free"), "ref": bool(r.get("is_reference")) or r["parser"] == "azure_di",
            "m": [card.get(m) for m in METRICS] if card else [None] * 8,
            "t": r.get("total") if card else None,
            "s": round(float(r.get("elapsed_ms", 0)) / 1000, 2), "pages": r.get("pages") or 0,
            "tables_found": r.get("tables_found", 0), "figures_found": r.get("figures_found", 0),
            "cell_match": r.get("tables_score"),
        })
    if not any(x["t"] is not None for x in rows):
        return None
    # A parser that crashed or timed out was attempted, so it scores 0 on every parameter this document can test.
    # (Skipping it would let an engine climb the table by bailing out on the hard documents.)
    tested = [any(x["m"][i] is not None for x in rows) for i in range(len(METRICS))]
    for r in cmp.get("results", []):
        if r.get("status") == "error":
            rows.append({"p": r["parser"], "cost": r.get("cost", "free"), "ref": r["parser"] == "azure_di", "failed": True,
                         "error": (r.get("error") or "")[:160], "m": [0.0 if tested[i] else None for i in range(len(METRICS))],
                         "t": 0.0, "s": round(float(r.get("elapsed_ms", 0)) / 1000, 2), "pages": 0,
                         "tables_found": 0, "figures_found": 0, "cell_match": None})
    prof = cmp.get("profile", {})
    rec = {"id": uuid.uuid4().hex[:8], "ts": int(time.time()), "file_name": cmp["file_name"], "file_type": cmp["file_type"],
           "group": group_of(prof, cmp["file_type"]), "pages": prof.get("page_count", 0),
           "reference_kind": cmp.get("reference_kind") or "", "rows": rows}
    with _lock:
        items = [x for x in runs() if x["file_name"] != rec["file_name"]]   # same document again = fresh result replaces the old
        items.append(rec)
        _write(items)
    return rec


def delete(run_id: str) -> int:
    with _lock:
        items = runs()
        keep = [x for x in items if x["id"] != run_id]
        _write(keep)
        return len(items) - len(keep)


def clear() -> None:
    with _lock:
        _write([])


def _mean(v: list) -> Optional[float]:
    v = [x for x in v if x is not None]
    return round(mean(v), 1) if v else None


def aggregate() -> dict:
    items = runs()
    by_group: dict[str, list[dict]] = {}
    for r in items:
        by_group.setdefault(r["group"], []).append(r)
        by_group.setdefault("Overall", []).append(r)

    def table(recs: list[dict]) -> list[dict]:
        per: dict[str, list[dict]] = {}
        for rec in recs:
            for row in rec["rows"]:
                per.setdefault(row["p"], []).append(row)
        out = []
        for p, rows in per.items():
            scored = [x for x in rows if x["t"] is not None]
            out.append({"p": p, "cost": rows[0]["cost"], "ref": p == "azure_di", "n": len(rows), "scored": len(scored),
                        "failed": sum(1 for x in rows if x.get("failed")),
                        "m": [_mean([x["m"][i] for x in scored]) for i in range(8)],
                        "t": _mean([x["t"] for x in scored]), "s": _mean([x["s"] for x in rows])})
        out.sort(key=lambda r: (r["t"] is None, -(r["t"] or 0), r["s"] or 0))
        return out

    groups = {k: {"docs": len(v), "rows": table(v)} for k, v in by_group.items()}

    # speed per page and tables / figures, over every document
    per: dict[str, list[dict]] = {}
    for rec in items:
        for row in rec["rows"]:
            per.setdefault(row["p"], []).append(row)
    speed, tf = [], []
    for p, rows in per.items():
        pp = [x["s"] / x["pages"] for x in rows if x["pages"]]
        speed.append({"p": p, "cost": rows[0]["cost"], "ref": p == "azure_di", "n": len(rows), "s_page": _mean(pp), "s_doc": _mean([x["s"] for x in rows])})
        tf.append({"p": p, "cost": rows[0]["cost"], "ref": p == "azure_di", "n": len(rows), "tables": _mean([x["tables_found"] for x in rows]),
                   "cell_match": _mean([x["cell_match"] for x in rows if x["cell_match"] is not None]),
                   "figures": _mean([x["figures_found"] for x in rows])})
    speed.sort(key=lambda r: (r["s_page"] is None, r["s_page"] or 0))
    tf.sort(key=lambda r: -(r["cell_match"] or 0))
    kinds: dict[str, int] = {}
    for r in items:
        kinds[r["reference_kind"] or "unknown"] = kinds.get(r["reference_kind"] or "unknown", 0) + 1
    return {
        "groups": groups, "speed": speed, "tables_figures": tf, "reference_kinds": kinds,
        "pages": sum(r["pages"] for r in items),
        "runs": [{k: r[k] for k in ("id", "ts", "file_name", "group", "pages", "reference_kind")} | {"parsers": len(r["rows"])} for r in sorted(items, key=lambda r: -r["ts"])],
    }


# ----------------------------------------------------------------------------- the head-to-head test
_ROOT = Path(__file__).resolve().parent.parent
H2H_SCORES = _ROOT / "app" / "routing" / "measured_scores.json"
H2H_RESULTS = _ROOT / "eval" / "head_to_head" / "results.jsonl"
H2H_GROUPS = _ROOT / "eval" / "head_to_head" / "doc_groups.json"
_H2H_FILES = [_ROOT / "eval" / "industrial", _ROOT / "eval" / "copilot_industry", _ROOT / "eval"]


_PDF_GROUPS = {"digital", "digital + tables", "mixed", "scanned", "digital + charts/images"}
_HIDDEN = {"vlm"}   # switched off in the app (one LLM call per page): not shown in the ranking


def _doc_pages(name: str) -> int:
    for d in _H2H_FILES:
        f = d / name
        if f.exists():
            if f.suffix.lower() == ".pdf":
                try:
                    import fitz

                    return len(fitz.open(f))
                except Exception:  # noqa: BLE001
                    return 1
            return 1
    return 1


def head_to_head() -> Optional[dict]:
    """The fresh head-to-head test (every parser on every test document, hand-written answers), in the same shape as aggregate()
    so the Benchmark tab can show it. Built from app/routing/measured_scores.json + eval/head_to_head/results.jsonl."""
    if not (H2H_SCORES.exists() and H2H_RESULTS.exists() and H2H_GROUPS.exists()):
        return None
    from app.parsers import get_parser_class

    def cost(name: str) -> str:
        try:
            return "paid" if get_parser_class(name).cost in ("paid", "cloud") else "free"
        except KeyError:
            return "free"

    table = json.loads(H2H_SCORES.read_text(encoding="utf-8"))["groups"]
    results = [r for r in map(json.loads, H2H_RESULTS.read_text(encoding="utf-8").splitlines())
               if r.get("doc") != "*" and r["status"] != "unavailable" and r["parser"] not in _HIDDEN]
    doc_group = json.loads(H2H_GROUPS.read_text(encoding="utf-8"))
    pages = {d: _doc_pages(d) for d in doc_group}

    def t_of(m: list) -> Optional[float]:
        v = [x for x in m if x is not None]
        return round(mean(v), 1) if v else None

    groups: dict = {}
    pooled: dict[str, list] = {}
    for g, v in table.items():
        rows = []
        for p, e in v["parsers"].items():
            if p in _HIDDEN:
                continue
            rows.append({"p": p, "cost": cost(p), "ref": False, "n": e["n"], "scored": e["n"], "failed": e["fail"],
                         "m": [round(x, 1) if x is not None else None for x in e["m"]], "t": t_of(e["m"]), "s": e["s"]})
            if g in _PDF_GROUPS:     # the overall ranking is for PDFs only: Word, Excel and plain-text parsers ran on a few easy files
                pooled.setdefault(p, []).append(e)
        rows.sort(key=lambda r: (r["t"] is None, -(r["t"] or 0), r["s"] or 0))
        groups[g] = {"docs": v["docs"], "rows": rows}
    over = []
    for p, es in pooled.items():
        n = sum(e["n"] for e in es)
        m = []
        for i in range(8):
            pairs = [(e["m"][i], e["n"]) for e in es if e["m"][i] is not None]
            m.append(round(sum(x * w for x, w in pairs) / sum(w for _, w in pairs), 1) if pairs else None)
        over.append({"p": p, "cost": cost(p), "ref": False, "n": n, "scored": n, "failed": sum(e["fail"] for e in es), "m": m, "t": t_of(m),
                     "s": round(sum(e["s"] * e["n"] for e in es) / n, 1)})
    over.sort(key=lambda r: (r["t"] is None, -(r["t"] or 0), r["s"] or 0))
    groups["Overall"] = {"docs": sum(v["docs"] for g, v in table.items() if g in _PDF_GROUPS), "rows": over}

    per: dict[str, list] = {}
    for r in results:
        per.setdefault(r["parser"], []).append(r)
    speed, tf = [], []
    for p, rs in per.items():
        secs = [x["secs"] for x in rs if x.get("secs") is not None]
        pg = sum(pages.get(x["doc"], 1) for x in rs)
        speed.append({"p": p, "cost": cost(p), "ref": False, "n": len(rs), "s_page": round(sum(secs) / pg, 2) if pg else None, "s_doc": round(mean(secs), 1) if secs else None})
        tr = [(x.get("card") or {}).get("Table Reconstruction") for x in rs]
        tr = [v for v in tr if v is not None]
        tf.append({"p": p, "cost": cost(p), "ref": False, "n": len(rs), "tables": round(mean(x.get("tables", 0) for x in rs), 1),
                   "cell_match": round(mean(tr) / 5, 3) if tr else None, "figures": None})
    speed.sort(key=lambda r: (r["s_page"] is None, r["s_page"] or 0))
    tf.sort(key=lambda r: -(r["cell_match"] or 0))
    ts = int(H2H_RESULTS.stat().st_mtime)
    runs = [{"id": "", "ts": ts, "file_name": d, "group": g, "pages": pages.get(d, 1), "reference_kind": "hand-written answer file",
             "parsers": sum(1 for r in results if r["doc"] == d)} for d, g in sorted(doc_group.items())]
    return {"source": "head_to_head", "groups": groups, "speed": speed, "tables_figures": tf,
            "reference_kinds": {"hand-written answer file": len(doc_group)}, "pages": sum(pages.values()), "runs": runs}
