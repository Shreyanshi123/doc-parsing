"""Turns the head-to-head results into the routing table Smart Extract uses.

    python scripts/build_routing_table.py            # reads eval/head_to_head/results.jsonl, writes app/routing/measured_scores.json
    python scripts/build_routing_table.py --summary  # also prints a ranking per document group

For every document group and parser it stores the mean of each of the 8 scorecard parameters, the median seconds, how many
documents it ran on and how many it failed. A crash, a timeout or an empty result counts as 0 on every parameter that document can test.
The group of each document is decided by the SAME analyzer Smart Extract runs on an upload, so test and routing agree.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RESULTS = ROOT / "eval" / "head_to_head" / "results.jsonl"
GROUP_CACHE = ROOT / "eval" / "head_to_head" / "doc_groups.json"
OUT = ROOT / "app" / "routing" / "measured_scores.json"
SEARCH = [ROOT / "eval" / "industrial", ROOT / "eval" / "copilot_industry", ROOT / "eval"]
METRICS = ["Text Accuracy", "Table Reconstruction", "Chart Understanding", "Infographic Parsing",
           "Entity & Numeric Fidelity", "Structure", "Completeness", "Hallucination Penalty"]


def find(name: str) -> Path:
    for d in SEARCH:
        if (d / name).exists():
            return d / name
    raise FileNotFoundError(name)


def doc_groups(names: list[str]) -> dict[str, str]:
    """document -> routing group, using the analyzer Smart Extract uses (cached: the analyzer is slow on chart-heavy PDFs)."""
    cache = json.loads(GROUP_CACHE.read_text(encoding="utf-8")) if GROUP_CACHE.exists() else {}
    todo = [n for n in names if n not in cache]
    if todo:
        from app import benchmark
        from app.models import ParseOptions
        from app.routing.analyzer import analyze
        from app.routing.file_type import resolve_file_type

        for n in todo:
            data = find(n).read_bytes()
            ft = resolve_file_type(data, n)
            cache[n] = benchmark.group_of(analyze(data, ft, ParseOptions()).to_dict(), ft) if ft == "pdf" else ft
            GROUP_CACHE.write_text(json.dumps(cache, indent=1), encoding="utf-8")
            print(f"  grouped {n}: {cache[n]}", flush=True)
    return cache


def build() -> dict:
    rows = [json.loads(l) for l in RESULTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r["doc"] != "*" and r["status"] != "unavailable"]
    groups_of = doc_groups(sorted({r["doc"] for r in rows}))
    # parameters each document can test = those any parser got a number for
    testable: dict[str, set[int]] = defaultdict(set)
    for r in rows:
        for i, m in enumerate(METRICS):
            if (r.get("card") or {}).get(m) is not None:
                testable[r["doc"]].add(i)
    cells: dict[tuple[str, str], dict] = defaultdict(lambda: {"vals": [[] for _ in METRICS], "secs": [], "n": 0, "fail": 0})
    docs_in_group: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        g, p = groups_of[r["doc"]], r["parser"]
        docs_in_group[g].add(r["doc"])
        c = cells[(g, p)]
        c["n"] += 1
        c["secs"].append(r.get("secs") or 0)
        card = r.get("card")
        failed = r["status"] in ("error", "timeout") or not card
        c["fail"] += 1 if r["status"] in ("error", "timeout") else 0
        for i, m in enumerate(METRICS):
            if i in testable[r["doc"]]:
                c["vals"][i].append(0.0 if failed else (card.get(m) or 0.0) if card.get(m) is not None else None)
    out: dict = {}
    for (g, p), c in cells.items():
        m = [round(statistics.mean(v for v in vals if v is not None), 2) if any(v is not None for v in vals) else None for vals in c["vals"]]
        out.setdefault(g, {"docs": len(docs_in_group[g]), "parsers": {}})["parsers"][p] = {
            "m": m, "s": round(statistics.median(c["secs"]), 1), "n": c["n"], "fail": c["fail"]}
    return {"_source": "eval/head_to_head/results.jsonl: fresh head-to-head, hand-written answer files, nothing from older reports",
            "_documents": len({r["doc"] for r in rows}), "groups": out}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    table = build()
    OUT.write_text(json.dumps(table, indent=1), encoding="utf-8")
    print(f"wrote {OUT} ({table['_documents']} documents, {len(table['groups'])} groups)")
    if a.summary:
        for g, v in sorted(table["groups"].items()):
            ranked = sorted(v["parsers"].items(), key=lambda kv: -(sum(x for x in kv[1]["m"] if x is not None) / max(1, sum(x is not None for x in kv[1]["m"]))))
            print(f"\n{g}  ({v['docs']} docs)")
            for p, e in ranked[:6]:
                vals = [x for x in e["m"] if x is not None]
                print(f"  {p:20s} {sum(vals) / len(vals):.2f}  {e['s']:>6.1f}s  n={e['n']} fail={e['fail']}")


if __name__ == "__main__":
    main()
