"""Scorecard for PDF parsers, using the same 8 parameters as the Azure IDP vs OpenDataLoader review.

    python scripts/benchmark.py                       # every parser that can run
    python scripts/benchmark.py --parsers azure_di,docling,pymupdf4llm

Each PDF in eval/ needs an answer key: <file>.truth.md (or <name>.values.md for chart_sample).
Every metric is 0..5 (5 = best), averaged over the documents it applies to. Total = /40.

  Text Accuracy              right words present (word F1)
  Table Reconstruction       table cells correct (HTML or Markdown tables both count)
  Chart Understanding        chart value kept WITH its label (e.g. 2021 -> 120)
  Infographic Parsing        flowchart boxes found + arrows kept
  Entity & Numeric Fidelity  numbers match the answer key
  Structure                  headings found + reading order
  Completeness               share of the answer key that is present (recall)
  Hallucination Penalty      5 = nothing invented (precision); lower = extra / wrong content

Output: eval/benchmark.md. Nothing is reused from older runs.
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.models import ParseOptions  # noqa: E402
from app.normalizer import normalize_document  # noqa: E402
from app.parsers import get_parser_class, parsers_for  # noqa: E402
from app.scorecard import METRICS, score  # noqa: E402
from app.routing.analyzer import analyze  # noqa: E402

EVAL = ROOT / "eval"
def group_of(profile) -> str:
    if "figures" in profile.traits:
        return f"{profile.classification} + charts/images"
    if profile.classification == "digital" and "tables" in profile.traits:
        return "digital + tables"
    return profile.classification


def run(name, data, fname, opts):
    t = time.perf_counter()
    for attempt in range(3):  # retry only network blips (ADI is a cloud call)
        try:
            out = normalize_document(get_parser_class(name)().parse(data, fname, "pdf", opts)).markdown
            return out, time.perf_counter() - t, None
        except Exception as e:  # noqa: BLE001
            if attempt < 2 and "Service" in type(e).__name__ + str(e)[:80] + "Connection":
                time.sleep(3)
                continue
            return "", time.perf_counter() - t, f"{type(e).__name__}: {e}"


def truth_file(p: Path):
    for f in (EVAL / f"{p.name}.truth.md", EVAL / f"{p.stem}.values.md"):
        if f.exists():
            return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parsers", default="all")
    ap.add_argument("--out", default="benchmark.md", help="file name inside eval/")
    ap.add_argument("--files", help="comma list of PDFs in eval/ (default: every PDF that has an answer key)")
    ap.add_argument("--dir", help="folder holding the --files PDFs (default: eval/)")
    ap.add_argument("--reference", help="no answer key: use this parser's output as the yardstick (e.g. azure_di)")
    a = ap.parse_args()
    wanted = [c.name for c in parsers_for("pdf", only_available=False)] if a.parsers == "all" else a.parsers.split(",")
    names = []
    for n in wanted:
        ok, why = get_parser_class(n).is_available()
        if ok:
            names.append(n)
        else:
            print(f"skipping {n}: {why}")

    opts = ParseOptions()
    results = []  # (group, file, parser, {metric: 0..1|None}, seconds, error)
    pages = {}
    if a.files:
        todo = [Path(a.dir or EVAL) / f for f in a.files.split(",")]
    else:
        todo = sorted(x for x in EVAL.glob("*.pdf") if truth_file(x))
    for p in todo:
        data = p.read_bytes()
        profile = analyze(data, "pdf", opts)
        group, pages[p.name] = group_of(profile), max(profile.page_count, 1)
        print(f"[{group}] {p.name} ({pages[p.name]} pages)", flush=True)
        outs = {}
        if a.reference:  # yardstick = the reference parser's own output; it is timed but not scored
            outs[a.reference] = run(a.reference, data, p.name, opts)
            truth = outs[a.reference][0]
            if not truth.strip():
                print(f"   reference {a.reference} failed on {p.name}: {outs[a.reference][2]}; skipping document", flush=True)
                continue
        else:
            truth = truth_file(p).read_text(encoding="utf-8")
        for n in names:
            out, secs, err = outs.get(n) or run(n, data, p.name, opts)
            if a.reference and n == a.reference:
                results.append((group, p.name, n, {m: None for m in METRICS}, secs, err))
                print(f"   {n:18} {secs:6.1f}s  (reference)", flush=True)
                continue
            sc = score(truth, out)
            results.append((group, p.name, n, sc, secs, err))
            tot = sum(v for v in sc.values() if v is not None)
            print(f"   {n:18} {secs:6.1f}s  {tot / max(sum(v is not None for v in sc.values()), 1):.2f} avg  {err or ''}", flush=True)

    def card(sub):
        agg = defaultdict(lambda: defaultdict(list))
        secs, spp = defaultdict(list), defaultdict(list)
        for _, f, n, sc, t, _ in sub:
            secs[n].append(t)
            spp[n].append((t, pages.get(f, 1)))
            for m, v in sc.items():
                if v is not None:
                    agg[n][m].append(v)
        table = {n: {m: 5 * sum(v) / len(v) for m, v in ms.items()} for n, ms in agg.items()}
        order = sorted(table, key=lambda n: -sum(table[n].values()))
        order += [n for n in secs if n not in table]  # e.g. the reference parser: timed, not scored
        head = "| parser | " + " | ".join(METRICS) + " | **Total /40** | avg s | s/page |"
        L = [head, "|---|" + "---|" * (len(METRICS) + 3)]
        for n in order:
            cells = [f"{table[n][m]:.1f}" if m in table.get(n, {}) else "-" for m in METRICS]
            tot = f"**{sum(table[n].values()):.1f}**" if n in table else "reference"
            sp = sum(t for t, _ in spp[n]) / sum(pg for _, pg in spp[n])
            L.append(f"| **{n}** | " + " | ".join(cells) + f" | {tot} | {sum(secs[n])/len(secs[n]):.1f} | {sp:.1f} |")
        return L

    L = ["# Parser scorecard (0-5 per metric, total /40)", "",
         (f"Big documents, no answer key: every parser is scored against {a.reference}'s output, so this measures closeness to {a.reference}, not absolute correctness. " if a.reference else "Run fresh on every PDF in eval/ that has an answer key. ") + "'-' = nothing to test that metric with.", "",
         "## Overall", ""] + card(results)
    for g in sorted({r[0] for r in results}):
        sub = [r for r in results if r[0] == g]
        L += ["", f"## {g}  ({len({r[1] for r in sub})} docs: {', '.join(sorted({r[1] for r in sub}))})", ""] + card(sub)
    errs = [r for r in results if r[5]]
    if errs:
        L += ["", "## Errors", ""] + [f"- {r[2]} on {r[1]}: {r[5]}" for r in errs]
    (EVAL / a.out).write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote eval/{a.out}")


if __name__ == "__main__":
    main()
