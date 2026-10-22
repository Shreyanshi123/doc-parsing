"""Runs Smart Extract over the industrial corpus (eval/industrial) and writes eval/industrial/results.jsonl.

    python scripts/run_industrial_suite.py                       # every file, resumable
    python scripts/run_industrial_suite.py --server http://127.0.0.1:8890

Each (file, configuration) runs in its own process with a timeout, so one hang cannot stall the rest.
  A  By document, paid parsers allowed (vision model on if configured)
  B  By part, paid parsers allowed
  C  By document, free parsers only (only for files with charts)
  http  the web API, used for files the app should refuse (unsupported / protected / corrupted / blank)
Azure Document Intelligence is blocked here on purpose: no per-page cost.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "eval" / "industrial"
RESULTS = CORPUS / "results.jsonl"
OUTDIR = CORPUS / "_out"
TIMEOUT = 900

HTTP_ONLY = {"config.json", "report.html", "data.xml", "message.eml", "legacy_report.doc", "legacy_sheet.xls", "protected.pdf", "corrupted.pdf", "blank.pdf"}
WITH_C = {"chart_report.pdf", "slides.pdf"}


def jobs() -> list[tuple[str, str]]:
    out = []
    for p in sorted(CORPUS.iterdir()):
        if not p.is_file() or p.name.endswith(".truth.md") or p.name in ("results.jsonl",):
            continue
        if p.name in HTTP_ONLY:
            out.append((p.name, "http"))
        elif p.suffix == ".pdf":
            out += [(p.name, "A"), (p.name, "B")] + ([(p.name, "C")] if p.name in WITH_C else [])
        else:
            out.append((p.name, "A"))
    return out


def run_one(name: str, cfg: str) -> dict:
    sys.path.insert(0, str(ROOT))
    import app.extract as ex
    from app.compare import count_tables
    from app.models import ParseOptions
    from app.scorecard import score

    orig = ex._usable
    ex._usable = lambda names, ft: [n for n in orig(names, ft) if n != "azure_di"]
    path = CORPUS / name
    paid, mode = {"A": (True, "document"), "B": (True, "part"), "C": (False, "document")}[cfg]
    t0 = time.time()
    r = ex.extract_document(path.read_bytes(), name, ParseOptions(), paid, None, mode)
    md, sm = r["markdown"], r["summary"]
    rec = {"file": name, "cfg": cfg, "status": "ok", "mode_used": sm.get("mode"), "parsers": sm["parsers_used"], "parts": sm["segments"],
           "pages": len(r["pages"]), "words": sm["words"], "secs": round(time.time() - t0, 1), "tables": count_tables(md),
           "figures_read": sum(1 for s in r["segments"] if s["kind"] == "figure" and s["status"] == "ok"),
           "warnings": [w[:200] for w in r["warnings"]],
           "profile": {k: r["profile"].get(k) for k in ("classification", "traits", "figure_count", "page_count")}}
    tp = CORPUS / f"{name}.truth.md"
    if tp.exists() and md.strip():
        card = score(tp.read_text(encoding="utf-8"), md)
        v = [x for x in card.values() if x is not None]
        rec["score"] = round(5 * sum(v) / len(v), 2) if v else None
        rec["card"] = {k: (round(5 * x, 1) if x is not None else None) for k, x in card.items()}
    elif tp.exists():
        rec["score"] = 0.0
    OUTDIR.mkdir(exist_ok=True)
    (OUTDIR / f"{name}__{cfg}.md").write_text(md, encoding="utf-8")
    return rec


def run_http(name: str, server: str) -> dict:
    t0 = time.time()
    cmd = ["curl", "-s", "-m", "300", "-o", "-", "-w", "\n__HTTP__%{http_code}", "-F", f"file=@{CORPUS / name}", "-F", "options={}", "-F", "include_paid=false", "-F", "mode=document", f"{server}/api/extract/upload"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    body, _, code = p.stdout.rpartition("\n__HTTP__")
    rec = {"file": name, "cfg": "http", "http": int(code or 0), "secs": round(time.time() - t0, 1)}
    try:
        j = json.loads(body)
        if "summary" in j:
            rec.update(status="ok", words=j["summary"]["words"], parsers=j["summary"]["parsers_used"])
        else:
            rec.update(status="refused", detail=str(j.get("detail", j))[:300])
    except ValueError:
        rec.update(status="error", detail=body[:300])
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--one", nargs=2, metavar=("FILE", "CFG"))
    ap.add_argument("--server", default="http://127.0.0.1:8890")
    a = ap.parse_args()
    if a.one:
        try:
            rec = run_one(*a.one)
        except Exception as e:  # noqa: BLE001
            rec = {"file": a.one[0], "cfg": a.one[1], "status": "error", "detail": f"{type(e).__name__}: {e}"[:300]}
        print("\n@@" + json.dumps(rec, default=str))
        return
    done = set()
    if RESULTS.exists():
        for line in RESULTS.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done.add((r["file"], r["cfg"]))
    todo = [j for j in jobs() if j not in done]
    print(f"{len(todo)} jobs to run, {len(done)} already done", flush=True)
    with open(RESULTS, "a", encoding="utf-8") as out:
        for name, cfg in todo:
            t0 = time.time()
            if cfg == "http":
                rec = run_http(name, a.server)
            else:
                try:
                    p = subprocess.run([sys.executable, __file__, "--one", name, cfg], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT, cwd=ROOT)
                    line = [l for l in p.stdout.splitlines() if l.startswith("@@")]
                    rec = json.loads(line[-1][2:]) if line else {"file": name, "cfg": cfg, "status": "error", "detail": (p.stderr or "no output")[-300:]}
                except subprocess.TimeoutExpired:
                    rec = {"file": name, "cfg": cfg, "status": "timeout", "secs": TIMEOUT}
            out.write(json.dumps(rec, default=str) + "\n")
            out.flush()
            print(f"{name:34s} {cfg:5s} {rec.get('status'):8s} score={rec.get('score')} {time.time() - t0:.0f}s", flush=True)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
