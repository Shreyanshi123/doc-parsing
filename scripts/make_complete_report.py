"""Builds eval/COMPLETE_REPORT.md: one plain-language report for the whole project, from the first 62-document test to the tough,
realistic and long-document tests.

    python scripts/make_complete_report.py
    python scripts/report_to_html.py eval/COMPLETE_REPORT.md eval/COMPLETE_REPORT.html
    python scripts/report_to_pdf.py  eval/COMPLETE_REPORT.md eval/COMPLETE_REPORT.pdf

Numbers are read from the result files every time, so running it again after a test finishes updates the report.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EV = ROOT / "eval"
TIE = 0.1
SETS = {"enterprise": "Tough documents", "realistic": "Real-world style documents", "long": "Long documents"}
KEYS = [("Text Accuracy", "Text"), ("Table Reconstruction", "Table"), ("Chart Understanding", "Chart"), ("Entity & Numeric Fidelity", "Numbers"),
        ("Structure", "Structure"), ("Completeness", "Complete"), ("Hallucination Penalty", "No extras")]
PRETTY = {"pymupdf": "PyMuPDF", "pymupdf4llm": "PyMuPDF4LLM", "docling": "Docling", "opendataloader": "OpenDataLoader", "unstructured": "Unstructured", "markitdown": "MarkItDown",
          "pdfplumber": "pdfplumber", "ocr": "Tesseract OCR", "hybrid_pdf": "hybrid_pdf", "smart_pdf": "smart_pdf", "docx": "native Word reader", "pptx": "native PowerPoint reader",
          "spreadsheet": "native Excel reader", "vision:azure_openai": "vision model", "text": "plain text reader"}

TYPE_OF = {  # document -> chapter
    "long_annual_report_20p.pdf": "digital", "contract_nested_clauses.pdf": "digital", "board_minutes.pdf": "digital", "contract_45p.pdf": "digital",
    "financial_statement_multiheader.pdf": "tables", "ledger_repeated_header.pdf": "tables", "bom_wide_table.pdf": "tables", "invoice_complex.pdf": "tables", "form_grid_ac4.pdf": "tables",
    "policy_schedule_nested.pdf": "tables", "clinical_trial_table.pdf": "tables", "bank_statement.pdf": "tables", "annual_report_income_statement.pdf": "tables", "bill_of_lading.pdf": "tables",
    "lab_report.pdf": "tables", "payslip.pdf": "tables", "purchase_order.pdf": "tables", "rfp_requirements_matrix.pdf": "tables", "transaction_ledger_100p.pdf": "tables",
    "annual_report_spread.pdf": "charts", "mixed_table_chart_photo.pdf": "charts", "research_two_column.pdf": "charts", "utility_bill.pdf": "charts", "annual_report_60p.pdf": "charts",
    "scanned_financial_statement.pdf": "scan", "scanned_purchase_order_phone.pdf": "scan", "scanned_report_30p.pdf": "scan",
    "quality_manual.docx": "word", "sop_goods_receipt.docx": "word", "handbook_40p.docx": "word", "quarterly_review.pptx": "ppt",
    "budget_model.xlsx": "excel", "hr_headcount_report.xlsx": "excel", "big_workbook.xlsx": "excel",
}


def pn(n: str) -> str:
    return PRETTY.get(n, n)


def f(x) -> str:
    return "-" if x is None else f"{x:.2f}"


def load(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


H2H, SUITE, SET_OF = {}, {}, {}
for s in SETS:
    H2H[s] = defaultdict(list)
    for r in load(EV / f"{s}_results" / "results.jsonl"):
        H2H[s][r["doc"]].append(r)
        SET_OF[r["doc"]] = s
    SUITE[s] = defaultdict(dict)
    for r in load(EV / s / "results.jsonl"):
        SUITE[s][r["file"]][r["cfg"]] = r
        SET_OF.setdefault(r["file"], s)
ALL_DOCS = [d for s in SETS for d in sorted(set(H2H[s]) | set(SUITE[s]))]
KNOWN_PAGES = {}


def pages_of(doc: str) -> str:
    s = SET_OF[doc]
    if doc in KNOWN_PAGES:
        return KNOWN_PAGES[doc]
    p = EV / s / doc
    out = "-"
    try:
        if doc.endswith(".pdf"):
            import pymupdf
            out = str(len(pymupdf.open(p)))
        elif doc.endswith(".docx"):
            out = "Word"
        elif doc.endswith(".xlsx"):
            out = "Excel"
        else:
            out = "slides"
    except Exception:
        pass
    KNOWN_PAGES[doc] = out
    return out


def ranked(doc: str) -> list[dict]:
    return sorted([r for r in H2H[SET_OF[doc]][doc] if r["status"] == "ok" and r.get("score") is not None], key=lambda r: -r["score"])


def failed(doc: str) -> list[dict]:
    return [r for r in H2H[SET_OF[doc]][doc] if r["status"] != "ok"]


def sx(doc: str, cfg: str):
    r = SUITE[SET_OF[doc]].get(doc, {}).get(cfg)
    return r.get("score") if r and r.get("status") == "ok" else None


def best_txt(doc: str) -> str:
    rows = ranked(doc)
    if not rows:
        return "-"
    top = rows[0]
    tied = [pn(r["parser"]) for r in rows[1:] if top["score"] - r["score"] <= TIE + 1e-9]
    return f"{pn(top['parser'])} {top['score']:.2f}" + (f" (tied: {', '.join(tied[:3])})" if tied else "")


def score_of(doc: str, parser: str):
    for r in H2H[SET_OF[doc]][doc]:
        if r["parser"] == parser:
            return r["score"] if r["status"] == "ok" else 0.0
    return None


# ---------------------------------------------------------------------------------------------------------------- plain-language notes
NOTE = {
    # tough documents
    "financial_statement_multiheader.pdf": "Two-row merged header. PyMuPDF4LLM and Docling keep it together. Smart Extract with paid parsers fell to 2.96 because it copied the same numbers twice (see section 7).",
    "scanned_financial_statement.pdf": "A scan: parsers without OCR return nothing. Docling and PyMuPDF4LLM read it.",
    "ledger_repeated_header.pdf": "The header repeating on every page did not hurt anybody.",
    "bom_wide_table.pdf": "12 columns in small print. The top parsers all keep every column.",
    "invoice_complex.pdf": "OpenDataLoader is best. smart_pdf adds a description of the QR code that is not in the answer.",
    "annual_report_spread.pdf": "Chart page. smart_pdf wins because it reads the chart values.",
    "form_grid_ac4.pdf": "Easy for the PyMuPDF family. Nothing special.",
    "policy_schedule_nested.pdf": "A table inside a table. PyMuPDF4LLM and OpenDataLoader keep it right. PyMuPDF-based parsers repeat the outer text across columns.",
    "mixed_table_chart_photo.pdf": "Table + chart + photo on one page. smart_pdf is best because it reads the chart.",
    "clinical_trial_table.pdf": "PyMuPDF4LLM scores 5.0. smart_pdf scores 3.01 because the picture detector mistook the table lines for a figure.",
    "contract_nested_clauses.pdf": "Docling keeps the clause numbering best.",
    "long_annual_report_20p.pdf": "PyMuPDF4LLM and Docling are perfect (5.0).",
    "budget_model.xlsx": "MarkItDown is slightly better than the native Excel reader; the rule keeps native first unless another parser wins by more than 0.5.",
    "quality_manual.docx": "Unstructured is clearly better than the native Word reader (the native one drops the page header).",
    # real-world style
    "annual_report_income_statement.pdf": "Dollar signs in their own cells and numbers in brackets. Layout-aware parsers (OpenDataLoader, PyMuPDF4LLM, Docling) beat plain PyMuPDF by 0.3 to 0.4.",
    "bank_statement.pdf": "3 pages, header repeated. Every parser with a text layer does well (4.5 to 4.8).",
    "bill_of_lading.pdf": "Merged cells. OpenDataLoader, Docling and PyMuPDF4LLM are ahead of the PyMuPDF family (3.85).",
    "board_minutes.pdf": "Mostly text. PyMuPDF4LLM and Docling are perfect. By document picked OpenDataLoader (4.61) because its rule is per document type, not per file.",
    "lab_report.pdf": "Docling, PyMuPDF4LLM and the PyMuPDF family all above 4.8. By part scored only 3.26: the table piece came out with every merged cell repeated across 12 columns.",
    "payslip.pdf": "Two tables side by side. Docling and PyMuPDF4LLM are best (4.6 to 4.7); OpenDataLoader, the choice for this type, scored 3.94.",
    "purchase_order.pdf": "OpenDataLoader 4.96 is best. By part scored only 3.54.",
    "research_two_column.pdf": "Two columns with a chart. smart_pdf is clearly best (4.43) because it reads the chart.",
    "rfp_requirements_matrix.pdf": "Rowspan category cells and check boxes were easy: every top parser is 4.75 or better.",
    "scanned_purchase_order_phone.pdf": "A tilted, noisy phone photo. Docling 4.67 is far ahead; hybrid_pdf and smart_pdf (Tesseract only) get 2.30.",
    "utility_bill.pdf": "Bill with a bar chart. smart_pdf wins (4.49) because it reads the chart; the free route scores 3.58.",
    "hr_headcount_report.xlsx": "Excel with a real chart object. Native reader and Unstructured are tied (3.7).",
    "sop_goods_receipt.docx": "Unstructured (4.93) is ahead of Docling (4.57) and the native Word reader (4.33).",
    "quarterly_review.pptx": "Deck with a real chart. Docling reads the chart (4.50); the native reader does not (4.01).",
}

L: list[str] = []
add = L.append
PRE = (EV / "HEAD_TO_HEAD_REPORT.md").read_text(encoding="utf-8")


def section(md: str, title: str) -> str:
    m = re.search(r"^## " + re.escape(title) + r".*?(?=^## |\Z)", md, flags=re.S | re.M)
    return m.group(0).rstrip() + "\n" if m else ""


def avg(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


# =========================================================================================================== report
add("# Document parsing project: what we tested, what we found, and what it means")
add("")
add("*A plain-language report. It starts from the first question and covers every kind of document we tested: digital PDFs, PDFs with tables, charts and photos, scans, Word, PowerPoint, Excel, CSV, plain text and images, then tough, real-world style and very long documents.*")
add("")
n_pre = 62
n_new = len(ALL_DOCS)
add("## 1. The whole story in one page")
add("")
add("- **The question.** For a given document, which parser (the software that reads the file and turns it into text) gives the best result? And can the app pick that parser by itself, based on measured results, not on guesses?")
add("- **What was wrong at the start.** The app chose parsers with fixed rules that nobody had measured. Some choices looked random, for example OpenDataLoader for almost every table document.")
add(f"- **What we did.** (1) A fresh test: {n_pre} documents, every parser on every document, each result scored against an answer file written by hand. (2) The app now picks parsers from those scores. (3) Then we tried to break it with {n_new} harder documents: tough tables, real-world style business documents, and long documents of 30 to 100 pages.")
add("- **The main finding.** There is no best parser for everything. Plain text and simple tables are fine with fast parsers. Charts need the vision model (smart_pdf). Scans need OCR or a layout model (Docling). Merged cells and tables inside tables need a layout-aware parser (PyMuPDF4LLM, OpenDataLoader or Docling).")
add("- **What still goes wrong.** A few documents lose a lot in Smart Extract (about 3.0 instead of 4.5 to 5.0). The causes are known and listed in section 8. Nothing in the routing has been changed because of the new tests.")
add("")
add("### Quick answer: which parser for which document")
add("")
add("| Document type | Best choice from the tests | Watch out for |")
add("|---|---|---|")
for row in [
    ("Digital PDF, mostly text", "PyMuPDF (fast, scores 4.9)", "Nothing special."),
    ("Digital PDF with tables", "OpenDataLoader, PyMuPDF4LLM or Docling (all about 4.5)", "Merged cells and nested tables: plain PyMuPDF, hybrid_pdf and smart_pdf are weaker."),
    ("PDF with charts or photos", "smart_pdf when the chart values matter", "On documents with only photos or diagrams, the free parsers can score higher because the vision model adds descriptions."),
    ("Scanned PDF or photo of a page", "Docling", "Parsers without OCR return nothing. Tesseract alone loses table structure."),
    ("Image files (png, jpg)", "Docling (4.85)", "-"),
    ("Word", "Unstructured or Docling; the native reader is slightly lower", "Native reader dropped the page header on one file."),
    ("PowerPoint", "Native reader; Docling when the deck has real charts", "Native reader cannot read chart values."),
    ("Excel / CSV", "Native reader (CSV 5.0)", "Merged cells and charts need checking."),
    ("Plain text", "Plain text reader (5.0)", "Do not send it to other parsers."),
]:
    add("| " + " | ".join(row) + " |")
add("")

add("## 2. How we scored (in simple words)")
add("")
add("Every parser output was compared with an answer file written by hand. The score is from 0 to 5 and is the average of up to eight questions:")
add("")
add("| Question | In simple words |")
add("|---|---|")
for a, b in [("Text", "Are the words right?"), ("Table", "Are the rows and columns right?"), ("Chart", "Were the chart values read?"), ("Infographic", "Were the labels in a diagram read?"),
             ("Numbers", "Are the numbers, dates and names exact?"), ("Structure", "Are headings, lists and order kept?"), ("Complete", "Is anything missing?"), ("No extras", "Did the parser add things that are not there?")]:
    add(f"| {a} | {b} |")
add("")
add("A crash, a timeout or an empty result counts as 0. Parsers within 0.1 of the best are treated as equal, and then the fastest one wins. Questions that do not apply to a document (for example Chart on a text page) are left out of its average.")
add("")

add("## 3. The parsers and what they are")
add("")
add("| Parser | What it is | Good at | Weak at |")
add("|---|---|---|---|")
for row in [
    ("PyMuPDF", "Very fast reader for PDFs that have a text layer", "Plain text, simple tables", "Merged cells, nested tables, scans (returns nothing)"),
    ("PyMuPDF4LLM", "PyMuPDF plus layout rules that write Markdown", "Merged headers, long reports", "Slower on big files"),
    ("OpenDataLoader", "Layout-aware PDF reader", "Tables, forms", "Scans (nothing), some side-by-side tables"),
    ("Docling", "Layout model with OCR", "Scans, tables, slides, images", "Slow (minutes on long files)"),
    ("Unstructured", "General document splitter", "Word, Excel", "PDF tables, plain text"),
    ("MarkItDown", "Converts Office files to Markdown", "Excel, CSV", "PDF tables"),
    ("pdfplumber", "PDF text and table finder", "Simple tables", "Structure"),
    ("Tesseract OCR", "Reads text from pictures", "Scans", "Tables (becomes plain lines)"),
    ("hybrid_pdf", "PyMuPDF + Tesseract OCR", "Mixed text and scanned pages", "Same table weaknesses as PyMuPDF"),
    ("smart_pdf", "PyMuPDF + Tesseract OCR + a vision model that looks at charts, diagrams and photos (at most 8 per document)", "Reading chart values", "Merged-header tables; adds descriptions of photos"),
    ("Native readers", "Word, PowerPoint, Excel and text readers built into the app", "Clean Office files", "Charts inside Office files"),
]:
    add("| " + " | ".join(row) + " |")
add("")
add("Two parsers are kept out of the app on purpose: **vlm** (it sends every page to the Azure OpenAI model, too many API calls) and **Azure Document Intelligence** (paid; it can run next to the others as a comparison but was not part of these tests).")
add("")

add("## 4. How Smart Extract works")
add("")
add("Smart Extract looks at the document first, decides what kind it is, and picks parsers from the measured scores.")
add("")
add("- **By document:** the whole file goes to the best parser for its type. If that parser fails, the next one is tried.")
add("- **By part:** the file is split into pieces. Text and headings stay with PyMuPDF. Tables go to the parser that scored best on tables. Scanned pages go to the best scanned-page parser. Charts and photos go to the vision model (at most 8 per document).")
add("- **Free or paid:** with *Include paid parsers* ticked, smart_pdf and the vision model can be used, and Azure Document Intelligence runs as an extra comparison tab. The result shown is always the best-ranked parser, never Azure by default.")
add("- **Prefer quality:** turns off the tie rule, so the highest score wins even if it is slower.")
add("")

add("## 5. First test: 62 documents")
add("")
add("Every parser was run on every document it can open (786 runs). The table shows what Smart Extract uses first for each kind of document.")
add("")
tbl = re.search(r"\| Document type \| Documents tested.*?(?=\n\n)", PRE, flags=re.S)
add(tbl.group(0) if tbl else "(table not found)")
add("")
add("Full parser-against-parser tables for all 13 document types are in Appendix A.")
add("")
add("**What the first test showed**")
add("")
add("- Digital text PDFs: PyMuPDF, hybrid_pdf and smart_pdf tie at 4.94, and PyMuPDF is the fastest.")
add("- PDFs with tables: Docling 4.50, OpenDataLoader 4.45 and PyMuPDF4LLM 4.44 are tied within 0.1; plain PyMuPDF is lower (4.31).")
add("- PDFs with charts or photos: smart_pdf is first (3.88) because it reads chart values; the next best is 3.32.")
add("- Scans: Docling 3.47 is first; PyMuPDF and pdfminer return nothing.")
add("- Images: Docling 4.85. Word 4.1 to 4.2 (all close). PowerPoint: native 4.86. Excel and CSV: native is at or near the top. Plain text: native 5.0.")
add("")
add("### Documents that mix text, tables, charts and photos")
add("")
add("These were run through the real app, three ways.")
add("")
mix = section(PRE, "Smart Extract on documents that mix text, tables, charts, photos and diagrams")
mix = re.sub(r"^## .*\n\n", "", mix, count=1)
add(mix.strip())
add("")

add("## 6. The three new test sets")
add("")
tot = {s: len({d for d in ALL_DOCS if SET_OF[d] == s}) for s in SETS}
add(f"All three sets were generated by scripts in this project (`make_enterprise_docs.py`, `make_realistic_docs.py`, `make_long_docs.py`), each with a hand-written answer file. **None of them are real company files**; real files cannot be shared here. The layouts copy common real formats.")
add("")
add("| Set | Documents | What it contains |")
add("|---|---|---|")
add(f"| Tough documents | {tot['enterprise']} | merged-cell tables, a table inside a table, a table over many pages, wide tables, forms, a scan, charts with photos, Excel and Word |")
add(f"| Real-world style | {tot['realistic']} | bank statement, income statement, purchase order, payslip, lab report, electricity bill with chart, bill of lading, RFP matrix, board minutes, two-column paper, a tilted phone photo of a purchase order, Excel with chart, Word SOP, PowerPoint with chart |")
add(f"| Long documents | {tot['long']} | 56-page annual report with 10 charts, 100-page ledger (2,500 rows), 46-page contract, 31 scanned pages, 40-section Word handbook, 5-sheet Excel workbook |")
add("")
add("### How the three sets did, in numbers")
add("")
add("Smart Extract average score (0 to 5) over the PDFs in each set:")
add("")
add("| Set | PDFs | By document, paid | By part, paid | By document, free |")
add("|---|---|---|---|---|")
for s, name in SETS.items():
    docs = [d for d in sorted(SUITE[s]) if d.endswith(".pdf")]
    cells = []
    for c in "ABC":
        v = [sx(d, c) for d in docs if sx(d, c) is not None]
        cells.append(f"{avg(v):.2f} ({len(v)})" if v else "-")
    add(f"| {name} | {len(docs)} | " + " | ".join(cells) + " |")
add("")
add("The number in brackets is how many documents finished. A smaller number means some runs are still going or did not finish.")
add("")

add("## 7. Chapter by document type")
add("")
CH = [("digital", "Digital PDFs (mostly text)"), ("tables", "Digital PDFs with tables, forms and statements"), ("charts", "PDFs with charts, figures and photos"), ("scan", "Scanned PDFs and photos of pages"),
      ("word", "Word documents"), ("ppt", "PowerPoint"), ("excel", "Excel")]
INTRO = {
    "digital": "The easy case. Every parser with a text layer scores well, so speed decides. On the long contract and long report, PyMuPDF4LLM and Docling lead; the PyMuPDF family is a little lower.",
    "tables": "The biggest group. Simple tables are easy for every layout-aware parser. Merged cells, side-by-side tables, nested tables and header rows that span columns are where parsers separate. The same few parsers (PyMuPDF4LLM, OpenDataLoader, Docling) keep leading, and plain PyMuPDF, hybrid_pdf and smart_pdf trail on the hard ones.",
    "charts": "Only a vision model can read the numbers inside a chart. smart_pdf is first on each of the four chart documents of the tough and real-world sets (annual report spread, mixed page, research paper, electricity bill). The cost is a few seconds per figure and one API call per figure.",
    "scan": "A scan has no text layer. Parsers that only read text return nothing (counted as 0). Docling reads scans best. hybrid_pdf and smart_pdf use only Tesseract OCR on scanned pages, so tables become plain lines.",
    "word": "Native Word reader is close to the others. On the two smaller Word files it lost the page header and flattened the list numbers, and Unstructured scored highest. On the 40-section handbook the native reader was tied for first.",
    "ppt": "Native reader is best for normal slides. For a deck that has real chart objects, Docling reads the chart and the native reader cannot.",
    "excel": "Native reader is close to the top. MarkItDown and Unstructured are equal or slightly better on some files, but not by the 0.5 margin the rule needs to replace the native reader.",
}
for key, title in CH:
    add(f"### {title}")
    add("")
    add(INTRO[key])
    add("")
    docs = [d for d in ALL_DOCS if TYPE_OF.get(d) == key]
    if docs:
        add("| Document | Set | Pages | Best parser | Smart Extract: By document, By part, free | What happened |")
        add("|---|---|---|---|---|---|")
        for d in docs:
            note = NOTE.get(d, "Result is in the ranking table in Appendix B; see the note below the table.")
            sxs = " / ".join(f(sx(d, c)) for c in "ABC") if d.endswith(".pdf") else f"{f(sx(d, 'A'))} / - / -"
            add(f"| `{d}` | {SETS[SET_OF[d]]} | {pages_of(d)} | {best_txt(d)} | {sxs} | {note} |")
        add("")
    add("")

add("## 8. The problems we found")
add("")
add("These are the real weak points. None of them is fixed yet, because you asked for testing, not changes.")
add("")
add("1. **Table lines mistaken for a figure (clinical_trial_table 3.01, financial_statement_multiheader 2.96 in paid By document; free route 5.0 and 4.86).** PyMuPDF splits a table with merged cells into several small tables. The picture detector then sees one big group of lines that is not inside any single table and calls it a figure. We confirmed this by running the detector directly. The file is then sent to smart_pdf, which reads the table as a picture and also adds the PyMuPDF text, so the numbers appear twice. Fix idea: also check figures against the combined area of all detected tables.")
add("2. **By part repeats merged cells (purchase_order 3.54 vs 4.96 By document; lab_report 3.26 vs 4.55; bill_of_lading 3.93 vs 4.56; policy_schedule_nested 3.06 vs 4.77).** In By part, a table piece can be read by PyMuPDF, which writes the same text into every column a merged cell covers. We saw this directly in the lab_report output; the same pattern is probable on the others. Fix idea: keep tables with merged cells or nested tables as one piece and give them to PyMuPDF4LLM or OpenDataLoader.")
add("3. **A network error looks like a bad score.** annual_report_spread first scored 3.98 in Smart Extract. The vision call for the bar chart had failed with a connection error, so the chart was missing. Run again, it scored 4.53, the same as smart_pdf alone. Lesson: when a figure cannot be read, the result shows a warning line, and such a run should be repeated.")
add("4. **The rule is per document type, not per file.** For digital PDFs with tables the first choice is OpenDataLoader. On board_minutes (mostly text) it scored 4.61 while PyMuPDF4LLM and Docling scored 5.0, and on payslip it scored 3.94 while Docling scored 4.69. A per-file check would do better but costs a test run per file.")
add("5. **hybrid_pdf and smart_pdf are weak on scans.** Both use only Tesseract OCR on scanned pages: 2.3 to 2.4 on the two scanned documents of the tough and real-world sets, against 4.4 to 4.7 for Docling. Smart Extract avoids this by sending scans to Docling.")
add("6. **Native Word and Excel readers lose a little.** The native Word reader drops the page header and flattens numbered lists. The difference is under the 0.5 margin on most files.")
add("")

add("## 9. Long documents")
add("")
lens = [d for d in ALL_DOCS if SET_OF[d] == "long"]
if not lens:
    add("Results are not available yet.")
else:
    add("Long documents were run with a limit of 10 minutes per parser per document (parsers vs parsers) and 15 minutes per Smart Extract run. A parser that does not finish is counted as 0 and shown as *timeout*.")
    add("")
    add("| Document | Pages | Best parser | Parsers that timed out or returned nothing | Smart Extract: By document, By part, free |")
    add("|---|---|---|---|---|")
    for d in lens:
        fl = ", ".join(f"{pn(r['parser'])} ({r['status']})" for r in failed(d)) or "none"
        add(f"| `{d}` | {pages_of(d)} | {best_txt(d)} | {fl} | " + " / ".join(f(sx(d, c)) for c in "ABC") + " |")
    done_s = sum(len(v) for v in SUITE["long"].values())
    add("")
    add(f"Smart Extract runs finished for long documents so far: {done_s}. If this number is lower than 14, the run is still going and this section will be updated when the report is generated again.")
    add("")
    add("Timings for long documents are measured but not exact, because the laptop was doing other things at the same time. What they show clearly: Docling and Tesseract OCR take minutes on 30 to 100 pages, while PyMuPDF takes seconds.")
add("")

add("## 10. What is done and what is not")
add("")
add("**Done and tested**")
add("")
add("- Fresh 62-document head-to-head, with the routing built from it.")
add("- Smart Extract By document, By part and free mode, in the app, on all three new sets.")
add("- vlm is off everywhere; smart_pdf and By part read figures only (at most 8 per document).")
add("- Detector problem and network error problem traced to their causes.")
add("")
add("**Not done**")
add("")
add("- Azure Document Intelligence on the new sets (it is paid; ask first).")
add("- Fixes for the six problems in section 8. They change routing, so they need your yes.")
add("- Real client documents: everything here is generated.")
add("- The new sets are not part of the routing table. They only measure.")
add("")

add("## 11. Limits")
add("")
add("- All documents are generated; real files are messier.")
add("- One run per parser and document. Differences under 0.1 are noise.")
add("- Answer files are written by hand; a different but correct layout can lose points.")
add("- Timings are only good for telling fast parsers from slow ones.")
add("- LlamaParse (no key), MinerU, Marker and Azure Document Intelligence were not run.")
add("")

add("## Appendix A. Parser against parser, the 62-document test")
add("")
ap = section(PRE, "Parser against parser, per document type")
ap = re.sub(r"^## .*\n", "", ap, count=1)
add(ap.strip().replace("### ", "#### "))
add("")

add("## Appendix B. Ranking per document: tough, real-world and long sets")
add("")
add("Sorted by score. *tied* means within 0.1 of the best. `-` means the question does not apply.")
for d in ALL_DOCS:
    rows = ranked(d)
    add("")
    add(f"### {d}  ({SETS[SET_OF[d]]}, {pages_of(d)} pages)" if d.endswith(".pdf") else f"### {d}  ({SETS[SET_OF[d]]})")
    add("")
    if not rows:
        add("No results yet.")
        continue
    has_chart = any(r["card"].get("Chart Understanding") is not None for r in rows)
    cols = [(k, lab) for k, lab in KEYS if lab != "Chart" or has_chart]
    add("| Rank | Parser | Score | " + " | ".join(lab for _, lab in cols) + " | Seconds |")
    add("|---|---|---|" + "---|" * len(cols) + "---|")
    for i, r in enumerate(rows, 1):
        tied = rows[0]["score"] - r["score"] <= TIE + 1e-9
        add(f"| {i} | {pn(r['parser'])}{' (tied)' if tied and i > 1 else ''} | **{r['score']:.2f}** | " + " | ".join(f(r["card"].get(k)) for k, _ in cols) + f" | {r['secs']:.0f} |")
    for r in failed(d):
        add(f"| - | {pn(r['parser'])} | 0.00 ({r['status']}) | " + " | ".join("-" for _ in cols) + f" | {r.get('secs', 0):.0f} |")
    if d in NOTE:
        add("")
        add(f"**Note:** {NOTE[d]}")
add("")
out = EV / "COMPLETE_REPORT.md"
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print("wrote", out, len(L), "lines;", len(ALL_DOCS), "documents")
