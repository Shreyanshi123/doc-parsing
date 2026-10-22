"""
Live benchmark: every "Compare parsers" run that was scored (against your reference text or Azure DI)
is saved here as one small record. The Benchmark tab averages the records per document type, so the
scorecard grows with every document you compare. Nothing is hard-coded.

Record = one document: its type, and for every parser the 8 scorecard values (0-5), total, seconds,
tables / figures it found. Parser outputs are NOT stored (the file stays small).
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from statistics import mean
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
