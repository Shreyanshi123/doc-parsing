"""Appendix E of the complete report: the factors of the Azure IDP vs OpenDataLoader review, for every parser and every document.

    python scripts/report_factors.py        # writes eval/_appendix_factors.md (read by make_complete_report.py)

E1  per parser: the 8 metrics, hallucination penalty as a negative number, total as a sum (same layout as the e-mail review)
E2  Azure DI vs OpenDataLoader vs ADI + vision on the research reports, in the e-mail layout
E3  per document where parsers differed a lot: key issues (structure, artifacts, numbers, charts) found by automatic checks on the saved outputs
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.compare import _table_cells, count_tables  # noqa: E402
from app.scorecard import chart_pairs, numbers  # noqa: E402

EV = ROOT / "eval"
SETS = ["enterprise", "realistic", "long", "mixed_long", "shared"]
HIDE = {"vlm"}
M7 = ["Text Accuracy", "Table Reconstruction", "Chart Understanding", "Infographic Parsing", "Entity & Numeric Fidelity", "Structure", "Completeness"]
SHORT = {"Text Accuracy": "Text", "Table Reconstruction": "Table", "Chart Understanding": "Chart", "Infographic Parsing": "Infographic",
         "Entity & Numeric Fidelity": "Numeric", "Structure": "Structure", "Completeness": "Complete"}
PRETTY = {"pymupdf": "PyMuPDF", "pymupdf4llm": "PyMuPDF4LLM", "docling": "Docling", "opendataloader": "OpenDataLoader", "unstructured": "Unstructured", "markitdown": "MarkItDown",
          "pdfplumber": "pdfplumber", "ocr": "Tesseract OCR", "hybrid_pdf": "hybrid_pdf", "smart_pdf": "smart_pdf", "docx": "native Word", "pptx": "native PowerPoint",
          "spreadsheet": "native Excel", "text": "plain text", "azure_di": "Azure DI (paid)", "adi_vision": "ADI + vision (paid)", "pdfminer": "pdfminer", "easyocr": "EasyOCR",
          "haystack_converter": "Haystack loader", "langchain_loader": "LangChain loader", "llamaindex_reader": "LlamaIndex reader"}
LOADERS = {"haystack_converter", "langchain_loader", "llamaindex_reader"}


def load(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def pn(n: str) -> str:
    return PRETTY.get(n, n)


def penalty(card: dict) -> float | None:
    v = card.get("Hallucination Penalty")
    return None if v is None else -(1 - v / 5)          # 0 = nothing invented, -1 = everything in the output is extra


def totals(avg: dict[str, float | None], pen: float | None) -> tuple[float, int, float]:
    vals = [v for k, v in avg.items() if v is not None]
    n = len(vals) + (1 if pen is not None else 0)
    s = sum(vals) + (pen or 0)
    return s, n, (s * 8 / n if n else 0.0)


# ------------------------------------------------------------------------------------------------------------------------------ E1 / E2
ALL = []        # (set, record)
for r in load(EV / "head_to_head" / "results.jsonl"):
    ALL.append(("62", r))
for s in SETS:
    for r in load(EV / f"{s}_results" / "results.jsonl"):
        ALL.append((s, r))


def per_parser(records) -> dict[str, dict]:
    by = defaultdict(lambda: {"docs": 0, "failed": 0, "cards": []})
    for _, r in records:
        if r["parser"] in HIDE or r["doc"] == "*":
            continue
        p = "loaders" if r["parser"] in LOADERS else r["parser"]
        by[p]["docs"] += 1
        if r["status"] == "ok" and r.get("card"):
            by[p]["cards"].append(r["card"])
        else:
            by[p]["failed"] += 1
    return by


def averages(cards: list[dict]) -> tuple[dict, float | None]:
    avg = {}
    for m in M7:
        v = [c[m] for c in cards if c.get(m) is not None]
        avg[m] = sum(v) / len(v) if v else None
    pens = [penalty(c) for c in cards if penalty(c) is not None]
    return avg, (sum(pens) / len(pens) if pens else None)


def fmt(x, nd=1) -> str:
    return "-" if x is None else f"{x:.{nd}f}"


out: list[str] = []
add = out.append
add("## Appendix E. The review factors, parser by parser")
add("")
add("Same factors as the Azure IDP vs OpenDataLoader review: Text, Table, Chart, Infographic, Numeric, Structure, Completeness and the Hallucination penalty. Differences to the e-mail review: the e-mail scores by hand from 1 to 5; here the code scores from 0 to 5 against a written answer file. The hallucination penalty is shown as a negative number as in the e-mail (0 = nothing invented, -1 = everything extra): penalty = -(1 - precision/5). Total = the seven metrics added up + the penalty (the e-mail's 27 for Azure = 4+4+4+3+5+4+4-1). A metric that an answer file cannot test (no chart in the document, for example) is left out, so the total is also shown scaled to 8 metrics (sum x 8 / number of metrics tested).")
add("")
def e1_table(title: str, intro: str, records) -> None:
    add(title)
    add("")
    add(intro)
    add("")
    add("| Parser | Docs | Failed | Text | Table | Chart | Infographic | Numeric | Structure | Complete | Hallucination penalty | Total (sum) | Metrics tested | Total scaled to 8 |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    rows = []
    for p, d in per_parser(records).items():
        if not d["cards"]:
            continue
        avg, pen = averages(d["cards"])
        s_, n, sc = totals(avg, pen)
        rows.append((sc, p, d, avg, pen, s_, n))
    for sc, p, d, avg, pen, s_, n in sorted(rows, key=lambda x: -x[0]):
        name = "LangChain / LlamaIndex / Haystack loaders" if p == "loaders" else pn(p)
        add(f"| {name} | {d['docs']} | {d['failed']} | " + " | ".join(fmt(avg[m]) for m in M7) + f" | {fmt(pen, 2)} | {s_:.1f} | {n} | **{sc:.1f}** |")
    add("")


e1_table("### E1a. Every parser on the 12 tough PDFs",
         "Merged-cell tables, nested table, forms, a scan, charts and photos, a 20-page report (Azure DI alone was not run on these; ADI + vision was). Averages over the runs that gave an output; failed, empty and timed-out runs are counted in *Failed*, not in the averages.",
         [(s, r) for s, r in ALL if s == "enterprise" and r["doc"].endswith(".pdf")])
e1_table("### E1b. Every parser on the 6 research reports",
         "Colleague's reports (9 to 66 pages). The answer files cover key pages only, so absolute values are low for every parser (the hallucination penalty is near -0.9 for all of them because most of each report is not in the answer file); compare parsers with each other. Failed, empty and timed-out runs are counted in *Failed*.",
         [(s, r) for s, r in ALL if s == "shared"])
add("Parsers that were not run on a set do not appear in its table (pdfminer, EasyOCR and the loaders only ran on the first 62 documents and the research reports).")
add("")

shared = [(s, r) for s, r in ALL if s == "shared"]
add("### E2. Research reports: Azure DI vs OpenDataLoader (e-mail layout)")
add("")
add("The six research reports from a colleague (answer files cover key pages only, so absolute values are low). Scale 0 to 5 per metric.")
add("")
pp = per_parser(shared)
cols = [("azure_di", "Azure DI (paid)"), ("opendataloader", "OpenDataLoader"), ("adi_vision", "ADI + vision (paid)"), ("pymupdf4llm", "PyMuPDF4LLM"), ("docling", "Docling")]
res = {}
for k, _ in cols:
    if k in pp and pp[k]["cards"]:
        avg, pen = averages(pp[k]["cards"])
        res[k] = (avg, pen, totals(avg, pen))
add("| Metric | " + " | ".join(n for k, n in cols if k in res) + " |")
add("|---|" + "---|" * len(res))
for m in M7:
    add(f"| {m} | " + " | ".join(fmt(res[k][0][m], 2) for k, _ in cols if k in res) + " |")
add("| Hallucination penalty | " + " | ".join(fmt(res[k][1], 2) for k, _ in cols if k in res) + " |")
add("| **Total (sum)** | " + " | ".join(f"**{res[k][2][0]:.1f}**" for k, _ in cols if k in res) + " |")
add("| Metrics tested | " + " | ".join(str(res[k][2][1]) for k, _ in cols if k in res) + " |")
add("")
add("In the e-mail review the strengths were: Azure IDP better on tables and structure, OpenDataLoader more complete on narrative text and footnotes. On these six native reports the two are close; the table above shows where they differ.")
add("")

# ------------------------------------------------------------------------------------------------------------------------------ E3
add("### E3. Key issues per document (where parsers differed a lot)")
add("")
add("Found by automatic checks on the saved outputs, not by reading every output by hand:")
add("")
add("- **Structure:** tables found in the output vs tables in the answer file; rows where the same cell text is repeated 3 or more times in a row (a merged cell copied across columns).")
add("- **Artifacts:** share of repeated lines (duplicated content), placeholder columns such as Col2, empty output.")
add("- **Numbers:** numbers of the answer file that are missing in the output, with up to 3 examples.")
add("- **Charts:** chart values of the answer file found in the output.")
add("- **Strong at:** metrics scored 4.5 or more.")
add("")


def doc_cards(set_name):
    by = defaultdict(dict)
    for r in load(EV / f"{set_name}_results" / "results.jsonl"):
        if r["parser"] not in HIDE and r["doc"] != "*":
            by[r["doc"]][r["parser"]] = r
    return by


def issues(set_name: str, doc: str, parser: str, rec: dict, truth: str) -> list[str]:
    if rec["status"] != "ok":
        return ["no output (" + rec["status"] + ")"] + ["-"] * 3 + ["-"]
    f = EV / f"{set_name}_results" / "_out" / f"{parser}__{doc}.md"
    md = f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""
    if not md.strip():
        return ["-", "empty output", "-", "-", "-"]
    # structure
    t_truth, t_out = count_tables(truth), count_tables(md)
    st = [f"{t_out} tables found, {t_truth} expected"]
    rep = len(re.findall(r"\|\s*([^|\n]{2,})\s*\|\s*\1\s*\|\s*\1\s*\|", md))
    if rep:
        st.append(f"{rep} rows with a cell repeated across columns")
    if t_truth and t_out > 3 * t_truth:
        st.append("table split into fragments")
    # artifacts
    lines = [re.sub(r"\W+", " ", l).strip().lower() for l in md.splitlines()]
    lines = [l for l in lines if len(l) > 25]
    dup = (len(lines) - len(set(lines))) / len(lines) if lines else 0
    art = []
    if dup >= 0.1:
        art.append(f"{dup:.0%} of lines repeated")
    ph = len(re.findall(r"\bCol\d+\b", md))
    if ph:
        art.append(f"{ph} placeholder columns (Col2...)")
    if "�" in md:
        art.append("broken characters")
    # numbers
    tn = numbers(truth)
    on = Counter(numbers(md))
    miss = [x for x in dict.fromkeys(tn) if x not in on]
    num = f"{len(miss)} of {len(set(tn))} numbers missing" + (" (" + ", ".join(miss[:3]) + ")" if miss else "") if tn else "-"
    # charts
    pairs = chart_pairs(truth)
    if pairs:
        low = md.lower()
        got = sum(1 for a, b in pairs if a.lower() in low and re.search(rf"(?<![\w.]){re.escape(b)}(?![\w])", low))
        ch = f"{got} of {len(pairs)} chart values found"
    else:
        ch = "no chart in answer file"
    strong = [SHORT[m] for m in M7 if rec["card"].get(m) is not None and rec["card"][m] >= 4.5]
    return ["; ".join(st), "; ".join(art) or "none found", num, ch, ", ".join(strong) or "-"]


shown = 0
for set_name in SETS:
    cards = doc_cards(set_name)
    for doc, runs in cards.items():
        ok = sorted([r for r in runs.values() if r["status"] == "ok" and r.get("score") is not None], key=lambda r: -r["score"])
        truth_p = EV / set_name / f"{doc}.truth.md"
        if len(ok) < 4 or not truth_p.exists() or not doc.endswith(".pdf"):
            continue
        scores = [r["score"] for r in ok]
        if scores[0] - scores[len(scores) // 2] < 0.6 and scores[0] - scores[-1] < 1.5:
            continue
        truth = truth_p.read_text(encoding="utf-8")
        pick = []
        for p in [ok[0]["parser"], "smart_pdf", "adi_vision", "azure_di", "opendataloader", "pymupdf4llm", "docling", "pymupdf", ok[-1]["parser"]]:
            if p in runs and p not in pick and len(pick) < 7:
                pick.append(p)
        add(f"### {doc}")
        add("")
        add("| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |")
        add("|---|---|---|---|---|---|---|")
        for p in pick:
            r = runs[p]
            cells = issues(set_name, doc, p, r, truth)
            sc = fmt(r.get("score"), 2) if r["status"] == "ok" else "0.00"
            add(f"| {pn(p)}{' (best)' if p == ok[0]['parser'] else ''} | {sc} | " + " | ".join(c.replace("|", "/") for c in cells) + " |")
        add("")
        shown += 1
add(f"{shown} documents are listed: the ones where the best parser was at least 0.6 above the median, or 1.5 above the worst.")
add("")
(EV / "_appendix_factors.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("wrote", EV / "_appendix_factors.md", len(out), "lines;", shown, "documents")
