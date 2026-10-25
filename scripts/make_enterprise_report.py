"""Builds eval/ENTERPRISE_REPORT.md from the tough-document runs (parsers vs parsers + Smart Extract).

    python scripts/make_enterprise_report.py
    python scripts/report_to_html.py eval/ENTERPRISE_REPORT.md eval/ENTERPRISE_REPORT.html
    python scripts/report_to_pdf.py  eval/ENTERPRISE_REPORT.md eval/ENTERPRISE_REPORT.pdf
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
H2H = [json.loads(l) for l in (ROOT / "eval/enterprise_results/results.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
SUITE = [json.loads(l) for l in (ROOT / "eval/enterprise/results.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
TIE = 0.1

DOCS = {  # file: (what it is, why it is tough)
    "financial_statement_multiheader.pdf": ("Profit and loss statement, landscape, 1 page", "two-row header with merged cells (year spans Standalone / Consolidated), section rows spanning all columns, negative numbers in brackets, footnotes"),
    "scanned_financial_statement.pdf": ("The same statement, printed and scanned (tilt, noise, blur)", "no text layer at all: only OCR or a layout model can read it"),
    "ledger_repeated_header.pdf": ("General ledger, 3 pages, 60 rows", "one table that continues over 3 pages with the header repeated on every page, long narration column, 7 columns"),
    "bom_wide_table.pdf": ("Bill of materials, landscape, 12 columns x 18 rows", "very wide table in small type, easy to cut columns or merge neighbours"),
    "invoice_complex.pdf": ("GST tax invoice with logo, QR code, signature, PAID watermark", "two-column seller / buyer block, line-item table, tax-summary table, images, a watermark over the text"),
    "annual_report_spread.pdf": ("Annual report, 2 pages, header / footer, two columns", "text column next to a highlights table and a bar chart; page 2 has a merged-cell segment table (rowspan) and a pie chart"),
    "form_grid_ac4.pdf": ("Compliance form (Form AC-4) with grid boxes", "label-above-value cells, check boxes ([X] Listed), declaration table with a signature line"),
    "policy_schedule_nested.pdf": ("Insurance policy schedule", "a table inside a table: the Coverage-details cell holds a 3-column cover table"),
    "mixed_table_chart_photo.pdf": ("Plant performance page: table + bar chart + photo", "merged-header table, a chart and a photo on the same page, two-column layout"),
    "clinical_trial_table.pdf": ("Clinical trial results table (Table 2)", "section rows that span all columns, confidence intervals inside cells, footnote symbols, p-values"),
    "contract_nested_clauses.pdf": ("Master services agreement, 4 pages", "nested clause numbering (1. / 1.1 / 1.2.1), header and footer on every page, signature table"),
    "long_annual_report_20p.pdf": ("Operations annual report, 20 pages", "contents list, 18 sections each with a paragraph and a small table, page breaks"),
    "budget_model.xlsx": ("Excel budget model, 3 sheets", "merged title cell, formulas, a hidden column, frozen header row, 30-row detail sheet, notes sheet"),
    "quality_manual.docx": ("Word quality manual", "header / footer, numbered and nested lists, a table with a merged title row, an embedded chart picture"),
}
ORDER = list(DOCS)
KEYS = [("Text Accuracy", "Text"), ("Table Reconstruction", "Table"), ("Chart Understanding", "Chart"), ("Entity & Numeric Fidelity", "Numeric"),
        ("Structure", "Structure"), ("Completeness", "Complete"), ("Hallucination Penalty", "Precision")]
PRETTY = {"pymupdf": "PyMuPDF", "pymupdf4llm": "PyMuPDF4LLM", "docling": "Docling", "opendataloader": "OpenDataLoader", "unstructured": "Unstructured", "markitdown": "MarkItDown",
          "pdfplumber": "pdfplumber", "ocr": "Tesseract OCR", "hybrid_pdf": "hybrid_pdf (PyMuPDF + Tesseract OCR)", "smart_pdf": "smart_pdf (PyMuPDF + Tesseract OCR + vision model)",
          "docx": "native docx", "pptx": "native pptx", "spreadsheet": "native spreadsheet", "vision:azure_openai": "vision model (figures only)"}


def pn(n: str) -> str:
    return PRETTY.get(n, n)


def short(n: str) -> str:
    return pn(n).split(" (")[0]


def f(x) -> str:
    return "-" if x is None else f"{x:.2f}"


by_doc = defaultdict(list)
for r in H2H:
    by_doc[r["doc"]].append(r)
suite = defaultdict(dict)
for r in SUITE:
    suite[r["file"]][r["cfg"]] = r
pages = {r["file"]: (r.get("profile") or {}).get("page_count") for r in SUITE}


def ranked(doc: str) -> list[dict]:
    return sorted([r for r in by_doc[doc] if r["status"] == "ok" and r.get("score") is not None], key=lambda r: -r["score"])


WHY = {
    "financial_statement_multiheader.pdf": "Merged two-row headers were the test. PyMuPDF4LLM (4.86), Docling (4.75) and OpenDataLoader (4.51) kept the header and the 6 columns together. Plain PyMuPDF splits the table into 5 fragments (Structure 2.1). smart_pdf scored 2.96: it read the page as a figure with the vision model and then also appended the PyMuPDF fragments, so the same numbers appear twice (Precision 2.3, Structure 1.5).",
    "scanned_financial_statement.pdf": "A scan has no text layer, so PyMuPDF, pdfplumber, MarkItDown and OpenDataLoader returned nothing (empty, counted as 0). PyMuPDF4LLM (4.49) and Docling (4.41) read it. Tesseract OCR, hybrid_pdf and smart_pdf (2.36) OCR the whole page as plain text with no table logic, so the table turns into loose lines.",
    "ledger_repeated_header.pdf": "Easy for every parser with a text layer: the repeated header did not break the table. Docling 5.0, OpenDataLoader 4.95, the PyMuPDF family 4.86. The gap is small, so speed should decide.",
    "bom_wide_table.pdf": "Twelve columns in small type did not break the top parsers: Docling 5.0, OpenDataLoader 4.99, PyMuPDF / hybrid / smart_pdf 4.93 (all within 0.1, so tied). MarkItDown and Unstructured (3.54) lose columns.",
    "invoice_complex.pdf": "OpenDataLoader 4.85, Docling 4.71, PyMuPDF4LLM 4.67, PyMuPDF / hybrid 4.61. smart_pdf (4.47) is lower because the QR code was sent to the vision model and its description (\"A QR code with the label Scan to pay...\") was added to the text; that text is not in the answer file.",
    "annual_report_spread.pdf": "The chart document. smart_pdf (4.53) is first, 0.48 above PyMuPDF4LLM (4.05): the vision model reads the bar and pie chart values, while text parsers keep only the words printed on the chart.",
    "form_grid_ac4.pdf": "Label-above-value cells and check boxes are easy: PyMuPDF, hybrid and smart_pdf tie at 4.55, OpenDataLoader 4.52, Docling 4.43. PyMuPDF4LLM is lower here (4.10).",
    "policy_schedule_nested.pdf": "A table inside a table. PyMuPDF4LLM and OpenDataLoader (4.77) kept the inner table in the right cell. PyMuPDF, hybrid and smart_pdf (2.92) repeated the outer cell text across the columns and cut the inner table apart (Table 1.9). Docling scored 3.62 (Table 2.7).",
    "mixed_table_chart_photo.pdf": "Table + chart + photo on one page. smart_pdf (3.90) is first, 0.35 above PyMuPDF4LLM (3.55), because it reads the bar chart values. All scores are low compared with the other documents.",
    "clinical_trial_table.pdf": "Section rows that span all columns plus long cells. PyMuPDF4LLM scored a perfect 5.0, Docling 4.82. smart_pdf scored 3.01 (last): the figure detector reported 1 figure on a one-page PDF that has no picture in it, so the vision model read the whole table and the PyMuPDF fragments were added after it, duplicating the numbers (Structure 1.6, Precision 2.4).",
    "contract_nested_clauses.pdf": "Docling 4.67 keeps the clause numbering best; PyMuPDF4LLM 4.45, OpenDataLoader 4.41, PyMuPDF family 4.21.",
    "long_annual_report_20p.pdf": "PyMuPDF4LLM and Docling are perfect (5.0), OpenDataLoader 4.89. The PyMuPDF family is 4.46 to 4.48 on this long document.",
    "budget_model.xlsx": "MarkItDown (4.31) is 0.27 above the native spreadsheet reader (4.04). The routing keeps native first unless another parser wins by more than 0.5, so native stays. Docling took 187 s for this file.",
    "quality_manual.docx": "Unstructured (4.86) is 0.77 above the native docx reader (4.09), more than the 0.5 margin. The native output has no header line (\"Northwind Industrial Supplies | Quality Manual\"), repeats the merged table title in all 4 columns and numbers every list item \"1.\".",
}

L: list[str] = []
add = L.append
add("# Tough documents test: which parser did best, and why")
add("")
add("*Fourteen enterprise-style documents (merged-cell tables, nested tables, tables that continue over pages, forms, a scan, charts + photos, Excel and Word). Every parser was run on the documents it can open and scored against a hand-written answer file.*")
add("")
add("## 1. The short answer")
add("")
add("- **No single parser wins everywhere.** The best parser changes with the document: PyMuPDF4LLM on merged-header and long documents, Docling and OpenDataLoader on wide and nested tables, smart_pdf on charts, Unstructured on the Word file, MarkItDown on the Excel file.")
add("- **Simple tables, ledgers, forms, wide tables, long reports:** all parsers with a text layer score 4.4 to 5.0, so the differences are small and speed should decide.")
add("- **Charts:** smart_pdf is first on both chart documents (annual report spread 4.53, mixed page 3.90).")
add("- **Merged-header and nested tables:** PyMuPDF4LLM, OpenDataLoader and Docling are best; plain PyMuPDF, hybrid_pdf and smart_pdf are weak (2.9 to 3.9).")
add("- **Scan:** PyMuPDF4LLM and Docling read it; parsers without OCR return nothing.")
add("- **Smart Extract on these documents:** By document with paid parsers scored 4.4 to 5.0 on 8 of 14, 3.9 to 4.1 on 4 (annual report, mixed page, Excel, Word), and about 3.0 on two merged-header tables. By part scored 3.06 on the nested table. Causes are in section 6.")
add("")
add("## 2. How the test was done")
add("")
add("- **Documents:** 14 documents generated by `scripts/make_enterprise_docs.py`. They are synthetic, built to be tough, not copies of real company files. Each has a hand-written answer file.")
add("- **Parsers vs parsers:** every document was run through every parser that can open its type (PyMuPDF, PyMuPDF4LLM, Docling, OpenDataLoader, Unstructured, MarkItDown, pdfplumber, Tesseract OCR, hybrid_pdf, smart_pdf, native docx / spreadsheet). 128 runs.")
add("- **Score:** 0 to 5, average of the 8 parameters that apply (Text, Table, Chart, Infographic, Numeric, Structure, Completeness, Precision). A crash, timeout or empty output counts as 0.")
add("- **Smart Extract:** every PDF three ways (A = By document with paid parsers allowed, B = By part with paid parsers allowed, C = By document with free parsers only); Excel and Word once. 38 runs.")
add("- **Not tested:** Azure Document Intelligence (paid, left out on purpose) and the vlm parser (sends every page to the LLM, switched off everywhere).")
add("- **Seconds** come from runs where the machine was sometimes busy (the 3-page ledger and 20-page report show inflated times). Use them only to tell fast parsers from very slow ones (Docling is the slowest on most files), not as exact numbers.")
add("")
add("## 3. The documents")
add("")
add("| # | Document | What it is | Pages | What makes it tough |")
add("|---|---|---|---|---|")
for i, d in enumerate(ORDER, 1):
    add(f"| {i} | `{d}` | {DOCS[d][0]} | {pages.get(d) or '-'} | {DOCS[d][1]} |")
add("")
add("## 4. Ranking per document (parsers vs parsers)")
add("")
add("Sorted by score. **Tied** means within 0.1 of the best: by the routing rule, tied parsers are equal and the fastest of them wins. Parameters are 0 to 5; `-` means the parameter does not apply to that document.")
for d in ORDER:
    rows = ranked(d)
    empty = [r for r in by_doc[d] if r["status"] != "ok"]
    add("")
    add(f"### {d}")
    add("")
    add(f"*{DOCS[d][0]}. {DOCS[d][1][0].upper() + DOCS[d][1][1:]}.*")
    add("")
    has_chart = any(r["card"].get("Chart Understanding") is not None for r in rows)
    cols = [(k, lab) for k, lab in KEYS if lab != "Chart" or has_chart]
    add("| Rank | Parser | Score | " + " | ".join(lab for _, lab in cols) + " | Tables found | Seconds |")
    add("|---|---|---|" + "---|" * len(cols) + "---|---|")
    for i, r in enumerate(rows, 1):
        tied = rows[0]["score"] - r["score"] <= TIE + 1e-9
        add(f"| {i} | {pn(r['parser'])}{' (tied)' if tied and i > 1 else ''} | **{r['score']:.2f}** | " + " | ".join(f(r["card"].get(k)) for k, _ in cols) + f" | {r['tables']} | {r['secs']:.0f} |")
    for r in empty:
        add(f"| - | {pn(r['parser'])} | 0.00 (empty output) | " + " | ".join("-" for _ in cols) + f" | 0 | {r['secs']:.0f} |")
    add("")
    add("**Why:** " + WHY[d])

add("")
add("## 5. Parser summary across the 14 documents")
add("")
agg = defaultdict(list)
for r in H2H:
    agg[r["parser"]].append(r)
rows = []
for p, rs in agg.items():
    sc = [(r["score"] if r["status"] == "ok" and r.get("score") is not None else 0.0, r["doc"]) for r in rs]
    rows.append((sum(s for s, _ in sc) / len(sc), p, len(rs), min(sc)))
add("| Parser | Documents run | Average score | Worst result |")
add("|---|---|---|---|")
for avg, p, n, worst in sorted(rows, reverse=True):
    add(f"| {pn(p)} | {n} | {avg:.2f} | {worst[0]:.2f} on `{worst[1]}` |")
add("")
add("Averages cover different documents (the native docx / spreadsheet readers ran on one file only), so compare them with care. Empty output counts as 0.")

add("")
add("## 6. Smart Extract on the same documents")
add("")
add("| Document | By document, paid (A) | By part, paid (B) | By document, free (C) | Best single parser (section 4) |")
add("|---|---|---|---|---|")
for d in ORDER:
    s = suite[d]
    best = ranked(d)[0]
    cell = lambda c: f(s[c].get("score")) if c in s else "-"  # noqa: E731
    add(f"| `{d}` | {cell('A')} | {cell('B')} | {cell('C')} | {short(best['parser'])} {best['score']:.2f} |")
add("")
add("### Where Smart Extract did well")
add("")
add("- Wide table, ledger, form, contract, 20-page report, invoice, nested table (By document) and the scan: 4.4 to 5.0, close to the best single parser. The scan scored 4.41 in all three configurations.")
add("- Mixed page with chart and photo: By document paid 3.90, higher than By part (3.79) and free (3.55), because the vision model reads the chart.")
add("")
add("### Where it lost points, and the cause")
add("")
add("1. **clinical_trial_table (3.01 paid, 5.0 free) and financial_statement_multiheader (2.96 paid, 4.86 free).** The figure detector reported 1 figure on a one-page PDF that contains no picture, so the file was routed to the charts-and-images group, where smart_pdf is the measured winner. smart_pdf then read the table as a figure with the vision model and also appended the PyMuPDF text and table fragments; the same numbers appear twice, which lowers Precision and Structure. With free parsers only, the file goes to PyMuPDF4LLM and scores 5.0 and 4.86. Note: the cause (table graphics counted as a figure) is inferred from the figure count and the output; I did not step through the detector.")
add("2. **policy_schedule_nested (4.77 By document, 3.06 By part).** By part splits the page into pieces; the pieces were read by PyMuPDF and OpenDataLoader separately, so the inner table was cut apart and the outer cell text was repeated across columns.")
add("3. **annual_report_spread (3.98 paid, 3.96 By part, 4.05 free) is below smart_pdf run directly (4.53).** Smart Extract did not reproduce the direct smart_pdf score here. Not investigated.")
add("4. **Excel and Word (4.04 and 4.09).** The native readers are kept first by the `prefer_native` rule (another parser must win by more than 0.5). MarkItDown (+0.27, below the margin) and Unstructured (+0.77, above the margin) scored higher.")
add("")
add("### Parsers used in each run")
add("")
add("The number is how many pieces (By part) or pages / documents (By document) each parser handled. The vision model reads figures only; it never receives a whole document.")
add("")
add("| Document | By document, paid (A) | By part, paid (B) | By document, free (C) |")
add("|---|---|---|---|")


def used(r: dict | None) -> str:
    if not r:
        return "-"
    return ", ".join(f"{short(k)} x{v}" for k, v in sorted(r["parsers"].items(), key=lambda t: -t[1]))


for d in ORDER:
    s = suite[d]
    add(f"| `{d}` | {used(s.get('A'))} | {used(s.get('B'))} | {used(s.get('C'))} |")
add("")
add("### What By part used, by kind of piece")
add("")
cnt = Counter()
for d in ORDER:
    for k, v in (suite[d].get("B") or {"parsers": {}})["parsers"].items():
        cnt[k] += v
tot = sum(cnt.values())
use = {"pymupdf": "text and headings (always the first pass)", "opendataloader": "tables", "pymupdf4llm": "tables", "docling": "tables or scanned pages",
       "smart_pdf": "pieces where it measured best", "vision:azure_openai": "figures only (charts, diagrams, pictures)", "ocr": "scanned pages / figures without a vision model"}
add("| Parser in By part | Pieces | Share | Used for |")
add("|---|---|---|---|")
for k, v in cnt.most_common():
    add(f"| {short(k)} | {v} | {100 * v / tot:.0f}% | {use.get(k, '')} |")
add("")
add("In By part mode, text and headings stay with PyMuPDF; scanned pages, tables and figures go to the parser that measured best for that kind of piece; at most 8 figures per document go to the vision model.")

add("")
add("## 7. What could be changed (nothing has been changed yet)")
add("")
add("1. **Figure detector:** do not count table borders / shaded rows as a figure. That alone should send both merged-header tables to a good parser (they scored 5.0 and 4.86 on the free route).")
add("2. **smart_pdf duplicates:** when the vision model has read a figure, do not append the PyMuPDF fragments of the same area.")
add("3. **Nested tables in By part:** keep a table that contains a table as one piece and read it with PyMuPDF4LLM or OpenDataLoader.")
add("4. **Word:** test two or three more Word files before changing the native-first rule.")
add("")
add("## 8. Limits of this test")
add("")
add("- 14 synthetic documents, one copy of each: good for finding weaknesses, not enough for final scores per document type.")
add("- Answer files are hand-written; a different but valid layout of the same content can lose points.")
add("- Azure Document Intelligence was not run, so there is no paid-parser comparison on these documents.")
add("- These scores are not merged into the routing table (`measured_scores.json`).")
out = ROOT / "eval" / "ENTERPRISE_REPORT.md"
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print("wrote", out, len(L), "lines")
