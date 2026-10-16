"""Score every free parser against ground truth and recommend a parser per document type.

    python scripts/evaluate.py                 # everything in eval/
    python scripts/evaluate.py --parsers pymupdf,pdfplumber,ocr
    python scripts/evaluate.py --include-paid

Layout: eval/<file>  +  eval/<file>.truth.md  (the correct content as Markdown).

Per document each parser gets three scores (0..1), compared with the truth:
  text     word-level F1 (are the right words there?)
  headings F1 over heading lines             (only if truth has headings)
  tables   F1 over table cell values         (only if truth has tables)
score = average of the scores that apply. Errors / empty output = 0.
Results: eval/results.md and eval/results.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.compare import compare_parsers, score_against_truth as score  # noqa: E402
from app.models import ParseOptions  # noqa: E402

EVAL = ROOT / "eval"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(EVAL))
    ap.add_argument("--parsers")
    ap.add_argument("--include-paid", action="store_true")
    a = ap.parse_args()
    root = Path(a.dir)

    docs = sorted(p for p in root.iterdir() if p.is_file() and not p.name.endswith((".truth.md", ".md", ".json")))
    detail, by_group = [], defaultdict(lambda: defaultdict(list))
    for p in docs:
        tf = root / f"{p.name}.truth.md"
        if not tf.exists():
            print(f"skip {p.name}: no {tf.name}")
            continue
        truth = tf.read_text(encoding="utf-8")
        print(f"evaluating {p.name} ...", flush=True)
        cmp = compare_parsers(p.read_bytes(), p.name, ParseOptions(), truth,
                              a.parsers.split(",") if a.parsers else None, a.include_paid)
        group = cmp["file_type"] + ("/" + cmp["profile"]["classification"] if cmp["file_type"] in ("pdf", "image") else "")
        rows = []
        for r in cmp["results"]:
            sc = score(truth, r["output"]) if r["status"] == "ok" else {"score": 0.0}
            rows.append({"parser": r["parser"], "status": r["status"], "ms": r.get("elapsed_ms"), **sc,
                         **({"error": r["error"]} if r["status"] != "ok" else {})})
            by_group[group][r["parser"]].append((sc["score"], r.get("elapsed_ms") or 0))
        detail.append({"file": p.name, "group": group, "router_would_pick": cmp["router_would_pick"], "results": rows})

    # ---- report -----------------------------------------------------------
    L = ["# Parser evaluation (scored against ground truth)", ""]
    L += ["## Recommendation per document type", "",
          "| document type | best | backup | avg score (best) | docs |", "|---|---|---|---|---|"]
    summary = {}
    for g, ps in sorted(by_group.items()):
        rank = sorted(((sum(s for s, _ in v) / len(v), sum(m for _, m in v) / len(v), n) for n, v in ps.items()),
                      key=lambda x: (-x[0], x[1]))
        n_docs = len(next(iter(ps.values())))
        summary[g] = [{"parser": n, "avg_score": round(sc, 3), "avg_ms": int(ms)} for sc, ms, n in rank]
        best = rank[0]
        backup = rank[1][2] if len(rank) > 1 else "-"
        L.append(f"| {g} | **{best[2]}** | {backup} | {best[0]:.2f} | {n_docs} |")
    L += ["", "## Per-document detail", ""]
    for d in detail:
        L += [f"### {d['file']}  ({d['group']}, router would pick: {d['router_would_pick']})", "",
              "| parser | status | ms | text | headings | tables | score |", "|---|---|---|---|---|---|---|"]
        for r in sorted(d["results"], key=lambda r: -r["score"]):
            L.append(f"| {r['parser']} | {r['status']} | {r['ms']} | {r.get('text','')} | "
                     f"{r.get('headings','-')} | {r.get('tables','-')} | **{r['score']}** |")
        L.append("")
    md = "\n".join(L)
    (root / "results.md").write_text(md, encoding="utf-8")
    (root / "results.json").write_text(json.dumps({"summary": summary, "detail": detail}, indent=2), encoding="utf-8")
    print("\n" + md)


if __name__ == "__main__":
    main()
