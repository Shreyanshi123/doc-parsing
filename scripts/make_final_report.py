"""Writes eval/HEAD_TO_HEAD_REPORT.md from the finished test results (no number is typed by hand).

    python scripts/make_final_report.py

Sources: app/routing/measured_scores.json (means per document group), eval/head_to_head/results.jsonl (every run),
eval/industrial/results.jsonl (Smart Extract on documents that mix content types).
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.routing import learned  # noqa: E402

MEASURED = json.loads((ROOT / "app" / "routing" / "measured_scores.json").read_text(encoding="utf-8"))
H2H = [json.loads(l) for l in (ROOT / "eval" / "head_to_head" / "results.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
H2H = [r for r in H2H if r.get("doc") != "*" and r["status"] != "unavailable"]
IND = [json.loads(l) for l in (ROOT / "eval" / "industrial" / "results.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
GROUP_DOCS = defaultdict(list)
for d, g in json.loads((ROOT / "eval" / "head_to_head" / "doc_groups.json").read_text(encoding="utf-8")).items():
    GROUP_DOCS[g].append(d)

LABEL = {"digital": "Digital text PDF", "digital + tables": "Digital PDF with tables", "mixed": "Mixed PDF (text pages and scanned pages)",
         "scanned": "Scanned PDF", "digital + charts/images": "PDF with charts, figures or images", "image": "Image files",
         "docx": "Word", "docx + charts": "Word with charts", "pptx": "PowerPoint", "pptx + charts": "PowerPoint with charts (real chart objects)", "xlsx": "Excel", "xlsx + charts": "Excel with charts (real chart objects)", "csv": "CSV", "text": "Plain text"}
ORDER = ["digital", "digital + tables", "digital + charts/images", "mixed", "scanned", "image", "docx", "docx + charts", "pptx", "pptx + charts", "xlsx", "xlsx + charts", "csv", "text"]
M = ["Text Accuracy", "Table Reconstruction", "Chart Understanding", "Infographic Parsing", "Entity & Numeric Fidelity", "Structure", "Completeness", "Hallucination Penalty"]
PAID = {"smart_pdf", "azure_di"}
HIDDEN = {"vlm"}   # switched off in the app (one LLM call per page): not part of any ranking in this report
MADE_OF = {"hybrid_pdf": "PyMuPDF + Tesseract OCR", "smart_pdf": "PyMuPDF + Tesseract OCR + a vision model for charts and figures"}
NOTE = {"vlm": " (paid, switched off in the app)"}


def overall(m: list) -> float | None:
    v = [x for x in m if x is not None]
    return sum(v) / len(v) if v else None


def f(x, nd=2) -> str:
    return "-" if x is None else f"{x:.{nd}f}"


def pick(group: str, paid: bool) -> dict | None:
    ft = "pdf" if group in ("digital", "digital + tables", "digital + charts/images", "mixed", "scanned") else group.split(" + ")[0]
    r = learned.prefer_native(learned.rank([group], file_type=ft, include_paid=paid), ft)   # the same order Smart Extract really uses
    return r[0] if r else None


def main() -> None:
    n_docs = len({r["doc"] for r in H2H})
    st = Counter((r["parser"], r["status"]) for r in H2H)
    L = []
    w = L.append
    w("# Which parser is best for which document: a fresh head-to-head test")
    w("")
    w(f"Date: {time.strftime('%Y-%m-%d')}. {n_docs} test documents, {len(H2H)} runs. Nothing from older reports or scorecards was used: every parser was run on every document it supports and scored against a hand-written answer file.")
    w("")
    w("## The answer in one table")
    w("")
    w("What Smart Extract (By document mode) now uses for each kind of document. Rule: the highest score wins; parsers within 0.1 points of the best are tied and the fastest of them goes first. Paid parsers are only used when \"Include paid parsers\" is ticked. **vlm is switched off everywhere in the app** (Smart Extract, Compare, Benchmark runs and Single parse): it sends every page to the Azure OpenAI model (one API call per page), which would mean a huge number of API hits. It is still measured below, and it scored well on scans, but nothing runs it unless VLM_PARSER_ENABLED is set to true.")
    w("")
    w("| Document type | Documents tested | Free mode: first parser | Score | Paid allowed: first parser | Score |")
    w("|---|---|---|---|---|---|")
    for g in ORDER:
        if g not in MEASURED["groups"]:
            continue
        a, b = pick(g, False), pick(g, True)
        w(f"| {LABEL[g]} | {MEASURED['groups'][g]['docs']} | {a['parser'] if a else '-'} | {f(a['score']) if a else '-'} | {b['parser'] if b else '-'} | {f(b['score']) if b else '-'} |")
    w("")
    w("Scores are 0 to 5 (average of the parameters a document can test). By part mode uses the same data per part: tables go to the parser with the best table-reconstruction score, scanned pages to the best scanned score, pictures to the best image score; charts and figures are read by the vision model; text and headings come from the first PyMuPDF pass.")
    w("")
    w("## Parser against parser, per document type")
    w("")
    w("Higher is better. A crash or a timeout counts as 0 on every parameter the document can test. Seconds are the median per document.")
    for g in ORDER:
        grp = MEASURED["groups"].get(g)
        if not grp:
            continue
        docs = sorted(x.replace(".pdf", "") for x in GROUP_DOCS.get(g, []))
        w("")
        w(f"### {LABEL[g]} ({grp['docs']} documents)")
        w("")
        if docs:
            w("Documents: " + ", ".join(docs) + ".")
            w("")
        w("| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |")
        w("|---|---|---|---|---|---|---|---|---|")
        rows = sorted(((p, e) for p, e in grp["parsers"].items() if p not in HIDDEN), key=lambda kv: -(overall(kv[1]["m"]) or 0))
        for p, e in rows[:9]:
            m = e["m"]
            w(f"| {p}{(' (' + MADE_OF[p] + ')') if p in MADE_OF else ''}{' (paid)' if p in PAID else ''} | {f(overall(m))} | {f(m[0])} | {f(m[1])} | {f(m[2])} | {f(m[5])} | {e['s']:.1f} | {e['fail']} | {e['n']} |")
        if len(rows) > 9:
            w(f"| ... {len(rows) - 9} more parsers scored lower | | | | | | | | |")
    w("")
    w("")
    w("## What our two combinations are made of")
    w("")
    w("- **hybrid_pdf** = PyMuPDF reads the pages that have text, **Tesseract OCR** reads the pages that are only a picture.")
    w("- **smart_pdf** = the same as hybrid_pdf, plus a **vision model** that reads charts, diagrams and pictures (at most 8 figures per document). Tables are read by PyMuPDF's table finder, never by the vision model; scanned pages are read by Tesseract OCR, not by the vision model.")
    w("")
    w("## Tables in documents that also have charts or photos")
    w("")
    w("Table-reconstruction score (0 to 5) per document, for the documents of the group \"PDF with charts, figures or images\" that contain a table. Where the table is a normal text table (datasheet_with_photo, flowchart_doc, product_brochure, slides) every parser reads it, and smart_pdf ties with the others, except on slides. Where smart_pdf is clearly ahead (annual_report_page, chart_report, chart_sample) the answer file also lists the values read from the chart as a table, which only a vision model can supply. So smart_pdf's higher table average in this group comes from chart values, not from better normal tables.")
    w("")
    cols = ["smart_pdf", "pymupdf4llm", "docling", "opendataloader", "pymupdf"]
    tbl = defaultdict(dict)
    for r in H2H:
        if r["doc"] in GROUP_DOCS.get("digital + charts/images", []) and r["parser"] in cols:
            v = (r.get("card") or {}).get("Table Reconstruction")
            if v is not None:
                tbl[r["doc"]][r["parser"]] = v
    w("| Document | " + " | ".join(cols) + " |")
    w("|---|" + "---|" * len(cols))
    for d in sorted(tbl):
        w(f"| {d.replace('.pdf', '')} | " + " | ".join(f(tbl[d].get(c), 1) for c in cols) + " |")
    w("")
    w("## Failures, timeouts and what they mean")
    w("")
    bad = [(k, v) for k, v in sorted(st.items()) if k[1] in ("error", "timeout") and k[0] not in HIDDEN]
    if bad:
        w("| Parser | Problem | Documents |")
        w("|---|---|---|")
        for (p, s), v in bad:
            w(f"| {p} | {s} | {v} |")
    else:
        w("No parser crashed or timed out.")
    w("")
    w("Timeouts mean one document took longer than 400 seconds. easyocr is the slow one (about a minute per document on this CPU-only laptop).")
    w("")
    w("## Smart Extract on documents that mix text, tables, charts, photos and diagrams")
    w("")
    w("These were run through the real app (By document with paid parsers allowed, By part with paid parsers allowed, and By document with free parsers only), with the final routing table. Azure Document Intelligence was blocked in this test. Score is 0 to 5 against the hand-written answer.")
    w("")
    combined_prefix = tuple(f"{i:02d}_" for i in range(1, 11)) + ("annual_report_page", "scanned_report_page", "product_brochure", "flowchart_doc", "infographic",
                                                                   "datasheet_with_photo", "report_with_figures", "dashboard", "sales_with_chart")
    comb = defaultdict(dict)
    for r in IND:
        if r["file"].startswith(combined_prefix):
            comb[r["file"]][r["cfg"]] = r
    if comb:
        w("| Document | By document (paid allowed) | By part (paid allowed) | By document (free only) |")
        w("|---|---|---|---|")
        for name in sorted(comb):
            cells = []
            for cfg in ("A", "B", "C"):
                r = comb[name].get(cfg)
                if not r:
                    cells.append("-")
                elif r["status"] != "ok":
                    cells.append(f"error: {str(r.get('detail', ''))[:40]}")
                else:
                    ps = ", ".join(r["parsers"]) if isinstance(r.get("parsers"), dict) else "-"
                    cells.append(f"{f(r.get('score'))} ({ps[:40]})")
            w(f"| {name} | " + " | ".join(cells) + " |")
        ok = [r for rs in comb.values() for r in rs.values() if r["status"] == "ok" and r.get("score") is not None]
        by_cfg = defaultdict(list)
        for rs in comb.values():
            for cfg, r in rs.items():
                if r["status"] == "ok" and r.get("score") is not None:
                    by_cfg[cfg].append(r["score"])
        w("")
        w("Average score over these documents: " + ", ".join(f"{ {'A': 'By document', 'B': 'By part', 'C': 'By document, free only'}[c] }: {sum(v) / len(v):.2f} ({len(v)} documents)" for c, v in sorted(by_cfg.items())) + ".")
        both = [(n, rs["A"], rs["C"]) for n, rs in comb.items() if "A" in rs and "C" in rs and rs["A"].get("score") is not None and rs["C"].get("score") is not None]
        if both:
            free_wins = [n for n, a, c in both if c["score"] > a["score"] + 0.05]
            paid_wins = [n for n, a, c in both if a["score"] > c["score"] + 0.05]
            w("")
            w(f"**What this shows.** On the {len(both)} documents that were run both ways, the free parsers scored higher on {len(free_wins)} ({', '.join(x.replace('.pdf', '') for x in free_wins) or 'none'}) and the paid vision path on {len(paid_wins)} ({', '.join(x.replace('.pdf', '') for x in paid_wins) or 'none'}). The vision model clearly helps when the values only exist inside a chart, and it costs points when the document is mostly text with photos or diagrams, because the model adds descriptions that are not in the answer. The \"charts and figures\" routing group mixes both kinds, so its first pick (smart_pdf when paid parsers are allowed) is right on average but not on every document.")
            w("")
            w("**Reading the scores.** The ten Copilot documents (names starting 01 to 10) score lower for every parser, because their answer files are summaries and not the full text. Compare parsers on the same document, not documents with each other.")
    w("")
    w("## Cost, honestly")
    w("")
    w("- **vlm** sends every page to Azure OpenAI (GPT-4.1): one API call per page. It ran on all test documents, so the Azure bill shows those calls. **The vlm parser is now off in the whole app** (setting VLM_PARSER_ENABLED, default off), to keep API hits low.")
    w("- **smart_pdf** sends every figure it finds to the vision model (up to 8 per document). Smart Extract only uses it when \"Include paid parsers\" is ticked, and By part mode also reads figures with the vision model.")
    w("- Azure Document Intelligence was **not** run, so it is not in any ranking here.")
    w("")
    w("## Limits of this test")
    w("")
    w("- The documents are synthetic (generated, plus the ten from the Copilot set). They are cleaner than most real files. Scans are simulated with skew, noise and blur.")
    w("- One run per parser and document. Differences under about 0.1 are noise, which is why such parsers are treated as tied.")
    w("- The answer files were written by hand. The Copilot answer files are summaries: they leave out headers and footers and include chart values that exist only inside the picture, so they under-score correct output a little and reward parsers that read charts.")
    w("- The \"tables\" group means clean digital PDFs with simple tables. Merged cells, tilted tables and tables inside photos are not covered.")
    w("- Timings are not exact: models load on first use, the laptop slept during part of the run and the disk was nearly full. Use them only to break ties.")
    w("- Not tested: Azure Document Intelligence, LlamaParse (no API key), MinerU, Marker, documents of 100 pages or more, real client files.")
    out = ROOT / "eval" / "HEAD_TO_HEAD_REPORT.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
