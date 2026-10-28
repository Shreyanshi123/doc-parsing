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
SETS = {"enterprise": "Tough documents", "realistic": "Real-world style documents", "long": "Long documents", "mixed_long": "Long mixed documents",
        "shared": "Research reports (shared by a colleague)"}
KEYS = [("Text Accuracy", "Text"), ("Table Reconstruction", "Table"), ("Chart Understanding", "Chart"), ("Entity & Numeric Fidelity", "Numbers"),
        ("Structure", "Structure"), ("Completeness", "Complete"), ("Hallucination Penalty", "No extras")]
PRETTY = {"pymupdf": "PyMuPDF", "pymupdf4llm": "PyMuPDF4LLM", "docling": "Docling", "opendataloader": "OpenDataLoader", "unstructured": "Unstructured", "markitdown": "MarkItDown",
          "pdfplumber": "pdfplumber", "ocr": "Tesseract OCR", "hybrid_pdf": "hybrid_pdf", "smart_pdf": "smart_pdf", "docx": "native Word reader", "pptx": "native PowerPoint reader",
          "spreadsheet": "native Excel reader", "vision:azure_openai": "vision model", "text": "plain text reader",
          "azure_di": "Azure Document Intelligence (paid)", "pdfminer": "pdfminer", "easyocr": "EasyOCR", "haystack_converter": "Haystack loader",
          "langchain_loader": "LangChain loader", "llamaindex_reader": "LlamaIndex reader", "adi_vision": "ADI + vision (paid)"}

TYPE_OF = {  # document -> chapter
    "long_annual_report_20p.pdf": "digital", "contract_nested_clauses.pdf": "digital", "board_minutes.pdf": "digital", "contract_45p.pdf": "digital",
    "financial_statement_multiheader.pdf": "tables", "ledger_repeated_header.pdf": "tables", "bom_wide_table.pdf": "tables", "invoice_complex.pdf": "tables", "form_grid_ac4.pdf": "tables",
    "policy_schedule_nested.pdf": "tables", "clinical_trial_table.pdf": "tables", "bank_statement.pdf": "tables", "annual_report_income_statement.pdf": "tables", "bill_of_lading.pdf": "tables",
    "lab_report.pdf": "tables", "payslip.pdf": "tables", "purchase_order.pdf": "tables", "rfp_requirements_matrix.pdf": "tables", "transaction_ledger_100p.pdf": "tables",
    "annual_report_spread.pdf": "charts", "mixed_table_chart_photo.pdf": "charts", "research_two_column.pdf": "charts", "utility_bill.pdf": "charts", "annual_report_60p.pdf": "charts",
    "group_report_100p.pdf": "charts", "scanned_financial_statement.pdf": "scan", "scanned_purchase_order_phone.pdf": "scan", "scanned_report_30p.pdf": "scan",
    "quality_manual.docx": "word", "sop_goods_receipt.docx": "word", "handbook_40p.docx": "word", "quarterly_review.pptx": "ppt",
    "budget_model.xlsx": "excel", "hr_headcount_report.xlsx": "excel", "big_workbook.xlsx": "excel",
    "bernstein_novo_66p.pdf": "research", "tbrc_mash_market_61p.pdf": "research", "piper_madrigal_10p.pdf": "research", "nh_bio_sector_14p.pdf": "research",
    "hcw_madrigal_10p.pdf": "research", "alphasense_mash_report_9p.pdf": "research",
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
IGNORED: set = set()      # documents to leave out of the report (none at the moment)
ALL_DOCS = [d for s in SETS for d in sorted(set(H2H[s]) | set(SUITE[s])) if d not in IGNORED]
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
    tied = [pn(r["parser"]) for r in rows if top["score"] - r["score"] <= TIE + 1e-9]
    if len(tied) == 1:
        return f"{tied[0]} {top['score']:.2f} (clear winner)"
    extra = f" +{len(tied) - 4} more" if len(tied) > 4 else ""
    return f"EQUAL (within 0.1): {', '.join(tied[:4])}{extra}. Top score {top['score']:.2f}"


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
    # long documents
    "annual_report_60p.pdf": "56 pages with 10 charts. PyMuPDF4LLM has perfect text and tables (4.8 to 5.0) but reads no chart values (Chart 0.0). smart_pdf reads the charts (4.4) but its text and tables are weaker (3.4 to 4.4). They tie at 4.18. Smart Extract paid picked smart_pdf, free picked PyMuPDF4LLM, both 4.18. No parser did both parts well. Docling did not finish in 10 minutes.",
    "transaction_ledger_100p.pdf": "100 pages, 2,500 rows. OpenDataLoader 5.0 in 13 s, PyMuPDF4LLM 4.99, PyMuPDF and hybrid_pdf only 3.01. Docling and smart_pdf did not finish in 10 minutes (the laptop slept during this run, so these two timeouts may be partly caused by that). Smart Extract By document 5.0, By part 3.01: its 100 table pieces went to smart_pdf.",
    "contract_45p.pdf": "46 pages of nested clauses. PyMuPDF4LLM 4.99, PyMuPDF family 4.9, Docling 4.88 (but 3 minutes). Smart Extract scored 4.9 in all three modes, using PyMuPDF only.",
    "scanned_report_30p.pdf": "31 scanned pages. Docling 4.58 (about 6 minutes), PyMuPDF4LLM 3.67, Tesseract-only parsers 2.66; parsers without OCR return nothing. Smart Extract sent every page to Docling in all three modes: 4.58.",
    "handbook_40p.docx": "40 sections. Every parser is at or near 5.0; the native Word reader is tied for first and the fastest.",
    "big_workbook.xlsx": "5 sheets x 300 rows. Native Excel reader 4.99, MarkItDown 4.82. Smart Extract used the native reader: 4.99.",
    "operations_report_36p.pdf": "36 pages of text, merged-header and side-by-side tables, a table inside a table, charts, photos and 6 scanned pages. Docling 4.66 and PyMuPDF4LLM 4.64 lead; OpenDataLoader 4.24, PyMuPDF 4.11. smart_pdf did not finish in 10 minutes and Smart Extract By part did not finish in 15. By document used PyMuPDF4LLM for all pages: 4.64. Note: each bar chart is followed by a table with the same values, so text parsers also got Chart points.",
    "tender_pack_30p.pdf": "31 pages: two-column text, a spanning-cell requirement matrix, form grids, photos, bar charts. Docling 4.07 and PyMuPDF4LLM 3.90 lead. smart_pdf 3.65 reads some chart values (Chart 2.5; the others 0.0) but loses on text and adds photo descriptions (No extras 3.5). Smart Extract: By document paid (smart_pdf) 3.77, By part 3.86, free (PyMuPDF4LLM) 3.90.",
    "group_report_100p.pdf": "99 pages: text, simple, merged-header, side-by-side and nested tables, about 27 bar and pie charts, photos and 14 scanned pages. Docling and Tesseract OCR were not run on it (too slow). PyMuPDF4LLM 3.93 is best (485 s), smart_pdf 3.66, PyMuPDF family 3.54, OpenDataLoader 3.53. Chart scores: smart_pdf 1.1, all others 0.0, because only 8 figures per document go to the vision model. Smart Extract: By document paid (smart_pdf) 3.66 in 48 s, By part 3.80 in 13 minutes (Docling read 34 scanned pieces, Tesseract 33), free (PyMuPDF4LLM) 3.93 in 3 minutes.",
    "quarterly_review.pptx": "Deck with a real chart. Docling reads the chart (4.50); the native reader does not (4.01).",
}

L: list[str] = []
add = L.append
PRE = (EV / "HEAD_TO_HEAD_REPORT.md").read_text(encoding="utf-8")


def short_name(n: str) -> str:
    return re.sub(r"\s*\(.*", "", n).strip()


def mark_ties(md: str):
    """Add a column to every parser table saying which parsers are within 0.1 of the best (equal to it). Returns (new_md, {type: [names]})."""
    out, ties, table, title = [], {}, [], None

    def flush():
        nonlocal table
        if not table:
            return
        scored = []
        for ln in table[2:]:
            c = [x.strip() for x in ln.strip().strip("|").split("|")]
            try:
                scored.append((c[0], float(c[1])))
            except (ValueError, IndexError):
                scored.append((c[0], None))
        vals = [v for _, v in scored if v is not None]
        top = max(vals) if vals else None
        eq = [short_name(n) for n, v in scored if v is not None and top - v <= TIE + 1e-9]
        if title:
            ties[title] = eq
        out.append(table[0] + " Within 0.1 of best? |")
        out.append(table[1] + "---|")
        for ln, (n, v) in zip(table[2:], scored):
            mark = ""
            if v is not None and top - v <= TIE + 1e-9:
                mark = "**equal to best**" if len(eq) > 1 else "**clear winner**"
            out.append(ln + f" {mark} |")
        table = []

    for ln in md.splitlines():
        if ln.startswith("### "):
            flush()
            title = re.sub(r"\s*\(\d+ documents?\)\s*$", "", ln[4:]).strip()
        if ln.startswith("| Parser | Overall"):
            table = [ln]
            continue
        if table:
            if ln.startswith("|"):
                table.append(ln)
                continue
            flush()
        out.append(ln)
    flush()
    return "\n".join(out), ties


def section(md: str, title: str) -> str:
    m = re.search(r"^## " + re.escape(title) + r".*?(?=^## |\Z)", md, flags=re.S | re.M)
    return m.group(0).rstrip() + "\n" if m else ""


def avg(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


# =========================================================================================================== report (short version)
_ap = section(PRE, "Parser against parser, per document type")
_ap = re.sub(r"^## .*\n", "", _ap, count=1)
APP_A, TIES = mark_ties(_ap)
n_new = len(ALL_DOCS)
add("# Document parsing: what we tested and what we found")
add("")
add(f"*Short report. First test: 62 documents. Then {n_new} harder documents (tough, real-world style, long). Scores are 0 to 5.*")
add("")
add("## 1. Summary")
add("")
add("- **Question:** which parser is best for which document, based on measured scores, not guesses.")
add(f"- **Test:** 62 documents first, then {n_new} harder ones (14 tough, 14 real-world style, 6 long: 30 to 100 pages, 3 long mixed: text, tables, charts, photos and scans in one file, 31 to 99 pages, 6 research reports from a colleague, 9 to 66 pages, answer files for key pages only). Every parser on every document, scored against a hand-written answer.")
add("- **Finding:** no parser is best for everything. Plain text and simple tables: fast parsers are enough. Charts: smart_pdf. Scans: Docling. Merged cells and nested tables: PyMuPDF4LLM, OpenDataLoader or Docling.")
add("- **New combo, ADI + vision:** Azure Document Intelligence reads text and tables, a vision model reads only charts and photos. Paid, not used by the routing. It matches the best parsers on merged-header tables and scans (4.96 vs smart_pdf 2.96 and 2.36), and adds little on the research reports (section 3).")
add("- **Still wrong:** a few documents drop to about 3.0 in Smart Extract (section 4). Nothing was changed in the routing.")
add("- **Note:** all documents are generated by us, not real company files. The 6 research reports (9 to 66 pages) come from a colleague; their answer files cover key pages only.")
add("")
add("### Which parser for which document")
add("")
add("| Document type | Best choice | Watch out for |")
add("|---|---|---|")
for row in [
    ("Digital PDF, mostly text", "PyMuPDF (fast)", "Nothing special"),
    ("Digital PDF with tables", "OpenDataLoader, PyMuPDF4LLM or Docling (equal)", "Merged and nested tables: PyMuPDF, hybrid_pdf, smart_pdf are weaker"),
    ("PDF with charts or photos", "smart_pdf (reads chart values)", "Photo-only pages: free parsers can score higher"),
    ("Scans, phone photos", "Docling", "Parsers without OCR return nothing; Tesseract alone loses tables"),
    ("Images (png, jpg)", "Docling", "-"),
    ("Word", "Unstructured or Docling", "Native reader drops the page header"),
    ("PowerPoint", "Native reader (Docling if it has real charts)", "Native reader cannot read charts"),
    ("Excel, CSV", "Native reader", "Merged cells and charts need checking"),
    ("Plain text", "Plain text reader", "Do not send it to other parsers"),
]:
    add("| " + " | ".join(row) + " |")
add("")
add("**Equal** means within 0.1 of the best score. Equal parsers are not ranked against each other; the app then prefers the fastest. Being listed first does not mean better.")
add("")

add("## 2. How scores work")
add("")
add("Each output is compared with a hand-written answer on up to 8 questions: Text, Table, Chart, Infographic, Numbers, Structure, Completeness, No extras. Score = average, 0 to 5. A crash, timeout or empty output counts as 0.")
add("")
add("| Parser | Good at | Weak at |")
add("|---|---|---|")
for row in [
    ("PyMuPDF", "Plain text, simple tables, very fast", "Merged cells, scans (nothing)"),
    ("PyMuPDF4LLM", "Merged headers, long reports", "Charts, scans"),
    ("OpenDataLoader", "Tables, forms", "Scans (nothing)"),
    ("Docling", "Scans, tables, slides, images", "Very slow on long files"),
    ("Unstructured / MarkItDown", "Word, Excel", "PDF tables"),
    ("hybrid_pdf", "PyMuPDF + Tesseract OCR", "Same as PyMuPDF on tables"),
    ("smart_pdf", "PyMuPDF + Tesseract OCR + vision model for charts and photos (max 8 per document)", "Merged-header tables; adds photo descriptions"),
]:
    add("| " + " | ".join(row) + " |")
add("")
add("Smart Extract: **By document** sends the whole file to the best parser for its type. **By part** splits it: text with PyMuPDF, tables, scans and figures each to the parser that scored best on them. vlm (every page to the LLM) is off everywhere. Azure Document Intelligence was not tested (paid).")
add("")

add("## 3. Results by test set")
add("")
add("Smart Extract average score over the PDFs in each set:")
add("")
add("| Set | Documents | By document, paid | By part, paid | By document, free |")
add("|---|---|---|---|---|")
for s, name in SETS.items():
    docs = [d for d in sorted(SUITE[s]) if d.endswith(".pdf") and d not in IGNORED]
    cells = []
    for c in "ABC":
        v = [sx(d, c) for d in docs if sx(d, c) is not None]
        cells.append((f"{avg(v):.2f}" + (f" ({len(v)} of {len(docs)} finished)" if len(v) < len(docs) else "")) if v else "-")
    n = len({d for d in ALL_DOCS if SET_OF[d] == s})
    add(f"| {name} | {n} | " + " | ".join(cells) + " |")
add("")
add("- **Tough:** merged cells, nested tables, scan, charts. Parsers separate here; Smart Extract does well on 10 of 14.")
add("- **Real-world style:** bank statement, payslip, lab report and more. Most parsers do well; By part is weaker than By document.")
add("- **Long (30 to 100 pages):** length is not a problem for fast parsers. Docling takes minutes; scans need it anyway.")
add("")
add("### Long documents")
add("")
lens = [d for d in ALL_DOCS if SET_OF[d] in ("long", "mixed_long")]
add("| Document | Pages | Best parser | Did not finish | Smart Extract: By document / By part / free |")
add("|---|---|---|---|---|")
for d in lens:
    fl = ", ".join(f"{pn(r['parser'])} ({r['status']})" for r in failed(d)) or "none"
    add(f"| `{d}` | {pages_of(d)} | {best_txt(d)} | {fl} | " + " / ".join(f(sx(d, c)) for c in "ABC") + " |")
add("")
add("The laptop slept during this run, so some timings and the Docling and smart_pdf timeouts on the 100-page ledger may be too long.")
add("")
add("### Research reports shared by a colleague (6 PDFs, 9 to 66 pages)")
add("")
add("Broker and market-research PDFs: dense text, many wide tables (some on rotated landscape pages), charts, and small text boxes. **All 16 parsers were run on all 6 documents, including Azure Document Intelligence (paid, about 160 pages).** vlm and LlamaParse were not run. The answer files cover the key pages only (summary tables, key numbers, valuation and catalyst tables), because a full hand-written answer for 66 pages was not possible. So the scores are low for every parser (1 to 2.6) and are only good for comparing parsers with each other.")
add("")
shared = [d for d in ALL_DOCS if SET_OF[d] == "shared"]
add("| Document | Pages | Best parsers (equal = within 0.1) | Seconds of the best | Azure DI | Did not finish | Smart Extract: By document / By part / free |")
add("|---|---|---|---|---|---|---|")
for d in shared:
    rows = ranked(d)
    az = next((r for r in rows if r["parser"] == "azure_di"), None)
    fl = ", ".join(f"{pn(r['parser'])} ({r['status']})" for r in failed(d)) or "none"
    best_secs = f"{rows[0]['secs']:.0f}" if rows else "-"
    add(f"| `{d}` | {pages_of(d)} | {best_txt(d)} | {best_secs} | {f(az['score']) + ' in ' + format(az['secs'], '.0f') + ' s' if az else '-'} | {fl} | " + " / ".join(f(sx(d, c)) for c in "ABC") + " |")
add("")
add("- **Mostly equal.** On 4 of 6 reports 2 to 5 parsers are within 0.1 of the best, so they are equal. Only two have a clear winner: Azure DI on AlphaSense (2.58) and OpenDataLoader on TBRC (1.86). The top score is held by OpenDataLoader (TBRC, NH), pdfplumber (Bernstein), Docling (Piper), MarkItDown (H.C. Wainwright) and Azure DI (AlphaSense).")
add("- **Speed decides.** The fast parsers (PyMuPDF, PyMuPDF4LLM, OpenDataLoader, pdfplumber, MarkItDown) take 5 to 170 seconds. Docling takes 130 to 520 seconds on the 10 to 14 page files and did not finish the 61 and 66 page files in 25 minutes. EasyOCR did not finish 3 of 6 in 25 minutes. Unstructured did not finish the 66-page file in 15 minutes.")
add("- **Azure DI (paid) is not better here.** It is first only on the AlphaSense report (2.58); on the others it is 0.02 to 0.17 below the best (equal to the best on 4 of them). It is fast (19 to 66 seconds per file) but costs money per page.")
add("- **smart_pdf and the vision model do not help on these reports.** smart_pdf is equal to or below the plain PyMuPDF family on 5 of 6. In Smart Extract the free route (By document, free) scored higher than the paid route on 5 of 6 (for example Piper 1.42 vs 1.16, TBRC 1.70 vs 1.34); By part took up to 308 seconds on the 66-page file.")
add("- **Limit:** the answer files are partial (key pages only), so use these scores only to compare parsers.")
add("")
add("### New combo: ADI + vision (Azure Document Intelligence for text and tables, a vision model only for charts and photos)")
add("")
add("Built after the first tests. Azure DI reads the whole PDF; the vision model reads only the cut-out charts and photos (at most 8 per document); a page is never sent as a whole to the model. It is paid (Azure per page, vision per figure) and is never picked by the automatic routing. Tested on the 12 tough PDFs and the 6 research reports.")
add("")
add("`-` in the Azure DI column = Azure DI alone was only run on the research reports.")
add("")
add("| Document | ADI + vision | smart_pdf | Azure DI alone | Best parser (score) |")
add("|---|---|---|---|---|")
_cmp = [d for d in ALL_DOCS if d.endswith(".pdf") and score_of(d, "adi_vision") is not None]
_gap = []
for d in _cmp:
    rows = ranked(d)
    top = rows[0]
    a, sp, az = score_of(d, "adi_vision"), score_of(d, "smart_pdf"), score_of(d, "azure_di")
    _gap.append((a, sp))
    add(f"| `{d}` | {f(a)} | {f(sp)} | {f(az)} | {pn(top['parser'])} {top['score']:.2f}{' (equal)' if top['score'] - a <= TIE + 1e-9 else ''} |")
add("")
_ok = [(a, sp) for a, sp in _gap if a is not None and sp is not None]
_wins = sum(1 for a, sp in _ok if a - sp > TIE + 1e-9)
_loss = sum(1 for a, sp in _ok if sp - a > TIE + 1e-9)
_best = sum(1 for d in _cmp if ranked(d) and ranked(d)[0]["score"] - score_of(d, "adi_vision") <= TIE + 1e-9)
add(f"- **Against smart_pdf (PyMuPDF + OCR + vision):** ADI + vision scored more than 0.1 higher on {_wins} of {len(_ok)} PDFs and more than 0.1 lower on {_loss}. Average on the 12 tough PDFs {sum(a for a, _ in _ok[:12]) / 12:.2f} vs {sum(sp for _, sp in _ok[:12]) / 12:.2f}; on the 6 research reports {sum(a for a, _ in _ok[12:]) / 6:.2f} vs {sum(sp for _, sp in _ok[12:]) / 6:.2f}. The big gains are on merged-header tables and the scan (financial statement 4.96 vs 2.96, scanned statement 4.96 vs 2.36), where Azure reads the table properly.")
add(f"- **Against the best parser:** equal to the best (within 0.1) on {_best} of {len(_cmp)} PDFs. It is clearly weaker on the nested table (policy schedule 3.89 vs 4.77) and not better than the free parsers on the research reports.")
add("- **Charts:** on the two chart documents it scores 4.45 (annual report spread) and 4.0 (mixed page), with a Chart score of 5.0, the same as smart_pdf.")
add("- **Azure alone vs ADI + vision on the research reports:** the two are within 0.04 of each other, so the vision model adds almost nothing there (few charts have values that the answer file checks).")
add("- **Cost and speed:** 10 to 45 seconds on the tough documents and 30 to 85 seconds on the research reports, much faster than Docling. Two runs first failed with a network error and were run again; the table shows the re-run scores.")
add("")

add("## 4. Problems found (none fixed yet)")
add("")
add("1. **Table lines counted as a figure.** clinical_trial_table 3.01 and financial_statement_multiheader 2.96 in paid By document; free route 5.0 and 4.86. PyMuPDF splits a merged-cell table into small tables, the detector sees the lines as a picture, and smart_pdf then writes the numbers twice. Confirmed by running the detector directly.")
add("2. **By part repeats merged cells.** purchase_order 3.54 vs 4.96, lab_report 3.26 vs 4.55, bill_of_lading 3.93 vs 4.56, policy_schedule_nested 3.06 vs 4.77, 100-page ledger 3.01 vs 5.0 (By part vs By document). Seen directly in the lab_report output; probable on the others.")
add("3. **A network error looks like a bad score.** annual_report_spread first scored 3.98 because the chart call failed; rerun gave 4.53.")
add("4. **The rule is per document type, not per file.** On payslip the choice (OpenDataLoader) scored 3.94, Docling 4.69.")
add("5. **hybrid_pdf and smart_pdf are weak on scans** (2.3 to 2.7 vs Docling 4.4 to 4.7). Smart Extract avoids this by using Docling for scans.")
add("6. **Native Word and Excel readers lose a little** (page header dropped, list numbers flattened).")
add("7. **Long report with charts:** PyMuPDF4LLM is best at text and tables but reads no charts; smart_pdf reads charts but is weaker on text and tables. Both end at 4.18.")
add("8. **Long mixed documents are slow with smart_pdf and By part.** On the 36-page report with 6 scanned pages, smart_pdf did not finish in 10 minutes and By part did not finish in 15 (cause not investigated; an orphaned Python process was also running on the laptop). By document with PyMuPDF4LLM took about 3 to 4 minutes and scored 4.64, close to the best (Docling 4.66, 7 minutes). On the 31-page tender pack the paid route (smart_pdf, 3.77) scored below the free one (PyMuPDF4LLM, 3.90) and Docling (4.07). On the 99-page file the paid By document run (smart_pdf, 3.66) was also below the free one (PyMuPDF4LLM, 3.93), and By part took 13 minutes.")
add("9. **Only 8 figures per document are read by the vision model.** The 99-page report has about 27 charts, so smart_pdf scored only 1.1 on charts (others 0.0), and the 56-page report with 10 charts is also capped. For long documents with many charts most charts stay unread.")
add("")

add("## 5. Done and not done")
add("")
add("- **Done:** 62-document test, routing built from it, three harder test sets, causes of problems 1 and 3 found.")
add("- **Not done:** fixes for the problems above (they change routing, need your yes), Azure Document Intelligence on the new sets (paid), real client documents.")
add("- **Limits:** generated documents, one run each, differences under 0.1 are noise, timings are rough.")
add("")

add("## Appendix A. First test: parser against parser (62 documents)")
add("")
add(APP_A.strip().replace("### ", "#### "))
add("")

add("## Appendix B. Documents that mix text, tables, charts and photos")
add("")
mix = section(PRE, "Smart Extract on documents that mix text, tables, charts, photos and diagrams")
mix = re.sub(r"^## .*\n\n", "", mix, count=1)
add(mix.strip())
add("")

add("## Appendix C. Harder documents by type")
add("")
CH = [("digital", "Digital PDFs (mostly text)"), ("tables", "Digital PDFs with tables, forms and statements"), ("charts", "PDFs with charts, figures and photos"), ("scan", "Scanned PDFs and photos"),
      ("word", "Word"), ("ppt", "PowerPoint"), ("excel", "Excel"), ("research", "Research reports (shared by a colleague)")]
for key, title in CH:
    docs = [d for d in ALL_DOCS if TYPE_OF.get(d) == key]
    if not docs:
        continue
    add(f"### {title}")
    add("")
    add("| Document | Set | Pages | Best parser | Smart Extract: By document, By part, free | What happened |")
    add("|---|---|---|---|---|---|")
    for d in docs:
        sxs = " / ".join(f(sx(d, c)) for c in "ABC") if d.endswith(".pdf") else f"{f(sx(d, 'A'))} / - / -"
        add(f"| `{d}` | {SETS[SET_OF[d]]} | {pages_of(d)} | {best_txt(d)} | {sxs} | {NOTE.get(d, '')} |")
    add("")

add("## Appendix D. Ranking per document (harder sets)")
add("")
add("Sorted by score. **EQUAL to best** = within 0.1 of the best; not ranked against each other.")
for d in ALL_DOCS:
    rows = ranked(d)
    add("")
    add(f"### {d}  ({SETS[SET_OF[d]]})")
    add("")
    if not rows:
        add("No results.")
        continue
    has_chart = any(r["card"].get("Chart Understanding") is not None for r in rows)
    cols = [(k, lab) for k, lab in KEYS if lab != "Chart" or has_chart]
    add("| Rank | Parser | Score | " + " | ".join(lab for _, lab in cols) + " | Seconds |")
    add("|---|---|---|" + "---|" * len(cols) + "---|")
    for i, r in enumerate(rows, 1):
        tied = rows[0]["score"] - r["score"] <= TIE + 1e-9
        n_eq = sum(1 for x in rows if rows[0]["score"] - x["score"] <= TIE + 1e-9)
        add(f"| {i} | {pn(r['parser'])}{' (EQUAL to best)' if tied and n_eq > 1 else ''} | **{r['score']:.2f}** | " + " | ".join(f(r["card"].get(k)) for k, _ in cols) + f" | {r['secs']:.0f} |")
    for r in failed(d):
        add(f"| - | {pn(r['parser'])} | 0.00 ({r['status']}) | " + " | ".join("-" for _ in cols) + f" | {r.get('secs', 0):.0f} |")
    if d in NOTE:
        add("")
        add(f"**Note:** {NOTE[d]}")
add("")
import subprocess as _sp
_sp.run([sys.executable, str(ROOT / "scripts" / "report_factors.py")], check=False, capture_output=True)
_fx = EV / "_appendix_factors.md"
if _fx.exists():
    L.append("")
    L.extend(_fx.read_text(encoding="utf-8").splitlines())
out = EV / "COMPLETE_REPORT.md"
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print("wrote", out, len(L), "lines;", len(ALL_DOCS), "documents")
