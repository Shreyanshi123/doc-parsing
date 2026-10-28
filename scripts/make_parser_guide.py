"""One simple guide: for each kind of document SITUATION we tested (merged-cell tables, a table inside a table, two tables side by side,
noisy scans, charts, ...), which parsers did well and which did not.

    python scripts/make_parser_guide.py        # writes eval/PARSER_GUIDE.html and eval/PARSER_GUIDE.pdf

Every test document is placed in one or more situations below. A parser's score for a situation is its average over those documents
(crash, timeout or empty output = 0). "62" means the first 62-document test; the other sets are enterprise, realistic and long.
"""
from __future__ import annotations

import html
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import report_pretty as rp  # noqa: E402  (CSS and colours)

ROOT = Path(__file__).resolve().parent.parent
EV = ROOT / "eval"


def D(setname, *names):
    return [(setname, n) for n in names]


# (id, group, title, what it is, tip, documents)
SITUATIONS = [
    ("text", "Text documents", "Plain text pages", "Reports, contracts, letters, resumes, meeting minutes.",
     "Every parser with a text layer does well. Pick the fastest.",
     D("62", "AI_agent_p1-3.pdf", "contract.pdf", "resume.pdf", "multilingual.pdf", "rotated_pages.pdf") + D("realistic", "board_minutes.pdf")),
    ("long", "Text documents", "Long documents with nested numbering", "Contracts and reports of 4 to 46 pages, clauses like 1.2.1, header and footer on every page.",
     "Length is not a problem for the fast parsers. Docling and PyMuPDF4LLM lead; Docling takes minutes on the long ones.",
     D("enterprise", "contract_nested_clauses.pdf", "long_annual_report_20p.pdf") + D("long", "contract_45p.pdf") + D("62", "03_legal_contract.pdf")),
    ("simple", "Tables", "Simple clean tables", "One normal grid: balance sheet, invoice, datasheet, lab report, purchase order.",
     "Most layout-aware parsers are good. Plain text-only readers lose the structure.",
     D("62", "balance_sheet.pdf", "invoice.pdf", "digital.pdf", "datasheet.pdf", "bank_statement.pdf", "lab_report.pdf", "purchase_order.pdf", "02_invoice_purchase_order.pdf")),
    ("multipage", "Tables", "One table over many pages", "A ledger or statement that continues for 3 to 100 pages, header repeated on each page.",
     "Pages do not break the good parsers. PyMuPDF and hybrid_pdf are much lower on the 100-page ledger; Docling and smart_pdf did not finish it.",
     D("62", "multipage_table.pdf") + D("enterprise", "ledger_repeated_header.pdf") + D("realistic", "bank_statement.pdf") + D("long", "transaction_ledger_100p.pdf")),
    ("wide", "Tables", "Very wide table (12 columns)", "Bill of materials in small print.",
     "The top parsers keep every column. MarkItDown and Unstructured lose columns.",
     D("enterprise", "bom_wide_table.pdf")),
    ("merged", "Tables", "Merged cells and two-row headers", "Financial statements, clinical results, bill of lading, requirement matrix with spanning cells.",
     "Use PyMuPDF4LLM, OpenDataLoader or Docling. PyMuPDF, hybrid_pdf and smart_pdf break the table apart or repeat the text.",
     D("enterprise", "financial_statement_multiheader.pdf", "clinical_trial_table.pdf") + D("realistic", "annual_report_income_statement.pdf", "bill_of_lading.pdf", "rfp_requirements_matrix.pdf")),
    ("nested", "Tables", "A table inside a table", "Policy schedule: the coverage cell holds its own table.",
     "Only PyMuPDF4LLM and OpenDataLoader kept it right. Docling is weaker. One document only, so treat this as a hint.",
     D("enterprise", "policy_schedule_nested.pdf")),
    ("side", "Tables", "Two tables side by side", "Payslip: earnings on the left, deductions on the right.",
     "Docling and PyMuPDF4LLM are best. OpenDataLoader, the app's usual table parser, is clearly lower here. One document only.",
     D("realistic", "payslip.pdf")),
    ("forms", "Tables", "Forms with boxes and check marks", "Compliance form, insurance claim, discharge summary, fillable form.",
     "The PyMuPDF family and OpenDataLoader are fine. Check marks and boxes are easy.",
     D("enterprise", "form_grid_ac4.pdf") + D("62", "06_insurance_claim_form.pdf", "05_healthcare_discharge_summary.pdf", "form_fields.pdf")),
    ("invoice", "Tables", "Invoices and orders with logo, QR code, stamp", "Tax invoice, purchase order, manifest.",
     "OpenDataLoader is best on the complex invoice. smart_pdf adds a description of the QR code that is not in the answer.",
     D("enterprise", "invoice_complex.pdf") + D("realistic", "purchase_order.pdf") + D("62", "07_logistics_shipping_manifest.pdf")),
    ("charts", "Charts and pictures", "Charts with numbers", "Annual reports, utility bill, research paper with a bar chart or pie chart.",
     "Only smart_pdf reads the numbers inside a chart (it uses a vision model). Every other parser reads only the words printed on the chart.",
     D("62", "chart_report.pdf", "chart_sample.pdf", "annual_report_page.pdf", "01_corporate_annual_report.pdf", "04_scientific_research_paper.pdf")
     + D("enterprise", "annual_report_spread.pdf", "mixed_table_chart_photo.pdf") + D("realistic", "utility_bill.pdf", "research_two_column.pdf") + D("long", "annual_report_60p.pdf")),
    ("photos", "Charts and pictures", "Photos, diagrams, brochures, slides (no chart values)", "Datasheet with a photo, flowchart, brochure, slides saved as PDF, web pages.",
     "Free parsers (PyMuPDF4LLM) can score higher than smart_pdf here: the vision model adds descriptions that are not in the answer.",
     D("62", "datasheet_with_photo.pdf", "flowchart_doc.pdf", "product_brochure.pdf", "slides.pdf", "10_mixed_parser_killer.pdf", "PIB_home_p1-6.pdf", "Generative_AI_p1-6.pdf",
       "Overview of Amazon Web Services - Overview of Amazon Web Services.pdf")),
    ("twocol", "Charts and pictures", "Two-column layout", "Research paper with two columns and a table.",
     "Reading order matters. smart_pdf and the layout-aware parsers do best.",
     D("62", "two_column_paper.pdf") + D("realistic", "research_two_column.pdf")),
    ("research", "Charts and pictures", "Dense financial research reports (9 to 66 pages)", "Broker and market-research PDFs with many wide tables (some on rotated pages), charts and small text boxes.",
     "Most parsers are equal (within 0.1); OpenDataLoader, pdfplumber, PyMuPDF4LLM and MarkItDown are the fast ones. Docling takes minutes and did not finish the 61 and 66 page files in 25 minutes; EasyOCR did not finish 3 of 6. Azure DI (paid) is first on one report only. smart_pdf does not help here. Answer files cover key pages only, so use the scores for comparing parsers, not as absolute values.",
     D("shared", "bernstein_novo_66p.pdf", "tbrc_mash_market_61p.pdf", "piper_madrigal_10p.pdf", "nh_bio_sector_14p.pdf", "hcw_madrigal_10p.pdf", "alphasense_mash_report_9p.pdf")),
    ("longmixed", "Charts and pictures", "Long documents that mix everything", "31 to 99 pages with text, merged-cell tables, side-by-side tables, nested tables, charts, photos, two columns and scanned pages in one file.",
     "On the two shorter files Docling and PyMuPDF4LLM lead (4.07 to 4.66). Tables are the weak spot: OpenDataLoader and PyMuPDF score only 2.6 to 2.9 on tables. smart_pdf did not finish the 36-page file with scanned pages in 10 minutes and scored lower on the other (photo descriptions). By part did not finish in 15 minutes on the file with scans. On the 99-page file (tested without Docling and Tesseract OCR, too slow) PyMuPDF4LLM was best (3.93) and smart_pdf read only 8 of about 27 charts (cap of 8 per document).",
     D("mixed_long", "operations_report_36p.pdf", "tender_pack_30p.pdf", "group_report_100p.pdf")),
    ("scanclean", "Scans and images", "Clean scans", "Scanned invoice, report page, maintenance order.",
     "Docling is best. PyMuPDF and the text-only parsers return nothing; Tesseract alone loses tables.",
     D("62", "AI_agent_scanned_clean.pdf", "scanned_invoice_clean.pdf", "scanned_report_page.pdf", "09_scanned_maintenance_order.pdf")),
    ("scannoisy", "Scans and images", "Noisy, tilted or low-quality scans, phone photos", "Skewed, blurred, grainy scans and a phone photo of a purchase order.",
     "Docling is clearly ahead. hybrid_pdf and smart_pdf (Tesseract only) fall to about 2.3.",
     D("62", "AI_agent_scanned_noisy.pdf", "scanned_invoice_low_quality.pdf", "scanned_invoice_skewed_noisy.pdf") + D("enterprise", "scanned_financial_statement.pdf") + D("realistic", "scanned_purchase_order_phone.pdf")),
    ("scanlong", "Scans and images", "Long scan (31 pages)", "A report that is only photos of pages.",
     "Only Docling scores well, but it takes about 6 minutes.",
     D("long", "scanned_report_30p.pdf")),
    ("mixed", "Scans and images", "Pages with text and pages that are scans", "Some pages digital, some pictures.",
     "Docling or PyMuPDF4LLM. hybrid_pdf and smart_pdf lose the tables on the scanned pages.",
     D("62", "AI_agent_mixed.pdf", "mixed.pdf", "mixed_digital_scanned.pdf")),
    ("image", "Scans and images", "Image files (png, jpg)", "Receipt, ID card, screenshot, handwritten note.",
     "Docling is best; the OCR engines are close.",
     D("62", "handwritten_note.png", "id_card.png", "receipt_photo.jpg", "screenshot.png")),
    ("word", "Office files", "Word", "Manuals, procedures, handbook (3 to 40 sections), lists and a merged table row.",
     "Unstructured and Docling are a little ahead of the native reader, which drops the page header and flattens list numbers.",
     D("62", "procedure.docx", "report.docx", "report_with_figures.docx") + D("enterprise", "quality_manual.docx") + D("realistic", "sop_goods_receipt.docx") + D("long", "handbook_40p.docx")),
    ("ppt", "Office files", "PowerPoint", "Decks, with or without real chart objects.",
     "Native reader and Docling are both good. Docling reads real charts; the native reader cannot.",
     D("62", "deck.pptx", "slides.pptx", "dashboard.pptx") + D("realistic", "quarterly_review.pptx")),
    ("excel", "Office files", "Excel", "Several sheets, formulas, merged title cells, a hidden column, charts, up to 1,500 rows.",
     "The native reader is at or near the top. MarkItDown and Unstructured are about equal.",
     D("62", "multi_sheet.xlsx", "sales.xlsx", "sales_with_chart.xlsx") + D("enterprise", "budget_model.xlsx") + D("realistic", "hr_headcount_report.xlsx") + D("long", "big_workbook.xlsx")),
    ("csv", "Office files", "CSV", "Plain data files.", "Every reader gets it right.", D("62", "parts.csv", "sales.csv")),
    ("plain", "Office files", "Plain text and Markdown", "Notes and runbooks.", "Use the plain text reader only. Other parsers can fail on odd text files.", D("62", "runbook.md", "shift_notes.txt")),
]

NAME = {"pymupdf": "PyMuPDF", "pymupdf4llm": "PyMuPDF4LLM", "docling": "Docling", "opendataloader": "OpenDataLoader", "unstructured": "Unstructured", "markitdown": "MarkItDown",
        "pdfplumber": "pdfplumber", "pdfminer": "pdfminer", "ocr": "Tesseract OCR", "easyocr": "EasyOCR", "hybrid_pdf": "hybrid_pdf", "smart_pdf": "smart_pdf",
        "docx": "native Word reader", "pptx": "native PowerPoint reader", "spreadsheet": "native Excel reader", "text": "plain text reader", "loaders": "LangChain / LlamaIndex / Haystack loaders", "azure_di": "Azure Document Intelligence (paid)", "adi_vision": "ADI + vision (paid)"}
LOADERS = {"haystack_converter", "langchain_loader", "llamaindex_reader"}
HIDE = {"vlm"}
# what the app picks first for each kind of file (from the measured routing table; paid parsers allowed)
PICK_62 = {"digital": "pymupdf", "digital + tables": "opendataloader", "digital + charts/images": "smart_pdf", "mixed": "pymupdf4llm", "scanned": "docling", "image": "docling",
           "docx": "docx", "pptx": "pptx", "pptx + charts": "docling", "xlsx": "spreadsheet", "xlsx + charts": "spreadsheet", "csv": "spreadsheet", "text": "text"}


def load(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


groups = json.loads((EV / "head_to_head" / "doc_groups.json").read_text(encoding="utf-8"))
score = defaultdict(dict)       # (set, doc) -> parser -> score
for r in load(EV / "head_to_head" / "results.jsonl"):
    if r["parser"] in HIDE:
        continue
    p = "loaders" if r["parser"] in LOADERS else r["parser"]
    v = r["score"] if r["status"] == "ok" and r.get("score") is not None else 0.0
    score[("62", r["doc"])].setdefault(p, []).append(v)
for s in ("enterprise", "realistic", "long", "mixed_long", "shared"):
    for r in load(EV / f"{s}_results" / "results.jsonl"):
        if r["parser"] in HIDE:
            continue
        score[(s, r["doc"])].setdefault(r["parser"], []).append(r["score"] if r["status"] == "ok" and r.get("score") is not None else 0.0)
score = {k: {p: sum(v) / len(v) for p, v in d.items()} for k, d in score.items()}

# the app's first pick per new document: by file type, as the routing does it
NEW_PICK = {"digital": "pymupdf", "tables": "opendataloader"}


def app_pick(key) -> str:
    s, name = key
    if s == "62":
        return PICK_62.get(groups.get(name, ""), "")
    if name.endswith(".docx"):
        return "docx"
    if name.endswith(".xlsx"):
        return "spreadsheet"
    if name.endswith(".pptx"):
        return "docling"           # the deck has real chart objects
    return {"scanned_financial_statement.pdf": "docling", "scanned_purchase_order_phone.pdf": "docling", "scanned_report_30p.pdf": "docling"}.get(name, {
        "annual_report_spread.pdf": "smart_pdf", "mixed_table_chart_photo.pdf": "smart_pdf", "research_two_column.pdf": "smart_pdf", "utility_bill.pdf": "smart_pdf", "annual_report_60p.pdf": "smart_pdf",
        "operations_report_36p.pdf": "pymupdf4llm", "tender_pack_30p.pdf": "smart_pdf", "bernstein_novo_66p.pdf": "smart_pdf", "tbrc_mash_market_61p.pdf": "smart_pdf", "piper_madrigal_10p.pdf": "smart_pdf", "nh_bio_sector_14p.pdf": "smart_pdf", "hcw_madrigal_10p.pdf": "smart_pdf", "alphasense_mash_report_9p.pdf": "smart_pdf", "group_report_100p.pdf": "smart_pdf","long_annual_report_20p.pdf": "opendataloader", "board_minutes.pdf": "opendataloader", "contract_45p.pdf": "pymupdf", "contract_nested_clauses.pdf": "opendataloader"}.get(name, "opendataloader"))


def classify(docs):
    have = [d for d in docs if d in score]
    pool = defaultdict(list)
    for d in have:
        for p, v in score[d].items():
            pool[p].append(v)
    avg = {p: (sum(v) / len(v), len(v)) for p, v in pool.items() if len(v) >= max(1, len(have) // 2)}
    if not avg:
        return {}, {}, have
    top = max(a for a, _ in avg.values())
    out = {"best": [], "good": [], "weak": [], "fails": []}
    for p, (a, n) in sorted(avg.items(), key=lambda kv: -kv[1][0]):
        row = (NAME.get(p, p), a, p)
        if a >= top - 0.1 - 1e-9:
            out["best"].append(row)
        elif a >= top - 0.6:
            out["good"].append(row)
        elif a >= 1.0:
            out["weak"].append(row)
        else:
            out["fails"].append(row)
    return out, {p: a for p, (a, _) in avg.items()}, have


RES = []
for sid, grp, title, what, tip, docs in SITUATIONS:
    c, avg, have = classify(docs)
    picks = Counter(app_pick(d) for d in have)
    pick = picks.most_common(1)[0][0] if picks else ""
    top = max(avg.values()) if avg else 0
    pa = avg.get(pick)
    if pa is None:
        verdict = ("none", "")
    elif pa >= top - 0.1 - 1e-9:
        verdict = ("ok", f"{NAME.get(pick, pick)} scores {pa:.2f}, within 0.1 of the best")
    elif pick in ("docx", "pptx", "spreadsheet") and top - pa <= 0.5:
        verdict = ("kept", f"{NAME.get(pick, pick)} scores {pa:.2f}, {top - pa:.2f} below the best ({top:.2f}). Kept first on purpose: another parser must win by more than 0.5 to replace the native reader")
    else:
        verdict = ("bad", f"{NAME.get(pick, pick)} scores {pa:.2f}, {top - pa:.2f} below the best ({top:.2f})")
    RES.append(dict(id=sid, grp=grp, title=title, what=what, tip=tip, docs=have, c=c, pick=NAME.get(pick, pick), verdict=verdict))


LEVELS = (("best", "Best (equal)", "#d3ecce"), ("good", "Also good", "#dbe6f7"), ("weak", "Weak", "#fbe1c0"), ("fails", "Fails / empty", "#f6cfd3"))


def docs_label(r) -> str:
    names = [n.replace(".pdf", "").replace(".docx", "").replace(".xlsx", "").replace(".pptx", "") for _, n in r["docs"]]
    return ", ".join(names[:6]) + (f" +{len(names) - 6} more" if len(names) > 6 else "")


def verdict_text(r):
    k, t = r["verdict"]
    if k == "none":
        return ""
    mark = {"ok": "OK here", "kept": "Slightly below the best, on purpose", "bad": "NOT the best here"}[k]
    cls = {"ok": "eq", "kept": "win", "bad": "bad"}[k]
    return f'<p><b>App pick:</b> <span class="{cls}">{mark}.</span> The app picks {html.escape(r["pick"])} for this type of file: {html.escape(t)}.</p>'


def situation_html(r) -> str:
    c = r["c"]
    rows = ""
    for key, lab, col in LEVELS:
        if c.get(key):
            rows += f'<tr><td style="background:{col};white-space:nowrap"><b>{lab}</b></td><td>' + ", ".join(f"{html.escape(x[0])} {x[1]:.2f}" for x in c[key]) + "</td></tr>"
    n = len(r["docs"])
    ev = f"{n} document{'s' if n != 1 else ''}" + (" (one document only: a hint, not proof)" if n == 1 else "")
    return (f'<h4>{html.escape(r["title"])}</h4><p>{html.escape(r["what"])}</p><table><tr><th style="width:130px">Level</th><th>Parsers (average score, 0 to 5)</th></tr>{rows}</table>'
            f'<p><b>Tip:</b> {html.escape(r["tip"])}</p>{verdict_text(r)}<p style="color:#555;font-size:12.5px">Tested on {ev}: {html.escape(docs_label(r))}.</p>')


def cheat_table() -> str:
    body, last = "", None
    for r in RES:
        if r["grp"] != last:
            body += f'<tr><td colspan="5" style="background:#ececec"><b>{html.escape(r["grp"])}</b></td></tr>'
            last = r["grp"]
        c = r["c"]
        best = ", ".join(x[0] for x in c.get("best", [])) or "-"
        bad = ", ".join(x[0] for x in (c.get("weak", []) + c.get("fails", []))[:4]) or "-"
        k, _ = r["verdict"]
        flag = {"bad": '<span class="bad">no</span>', "ok": '<span class="eq">yes</span>', "kept": '<span class="win">native, on purpose</span>'}.get(k, "")
        body += (f'<tr><td><b>{html.escape(r["title"])}</b></td><td style="background:#d3ecce">{html.escape(best)}</td><td style="background:#f9dfe2">{html.escape(bad)}</td>'
                 f"<td>{html.escape(r['pick'])}</td><td>{flag}</td></tr>")
    return f'<table><tr><th>Situation</th><th>Best parsers</th><th>Weak or fails</th><th>App picks (by file type)</th><th>Is that pick good here?</th></tr>{body}</table>'


def render_html() -> str:
    detail, last = "", None
    for r in RES:
        if r["grp"] != last:
            detail += f'<h3>{html.escape(r["grp"])}</h3>'
            last = r["grp"]
        detail += situation_html(r)
    n_bad = sum(1 for r in RES if r["verdict"][0] == "bad")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Which parser for which document</title>'
            f'<style>{rp.CSS}</style></head><body><div class="page"><h1>Which parser for which document</h1>'
            f'<p class="sub">Every kind of document situation we tested, from plain text to a table inside a table and noisy scans: the parsers that did best and the ones to avoid. '
            f'{len(RES)} situations, 62 + {len({d for r in RES for d in r['docs'] if d[0] != '62'})} test documents. In {n_bad} situations the app\'s first pick is not the best.</p>'
            f'<h2>1. Cheat sheet</h2>{cheat_table()}'
            f'<p><b>Best (equal)</b> = within 0.1 of the top score; those parsers are tied. <b>Also good</b> = within 0.6. <b>Weak</b> = lower. <b>Fails</b> = average below 1 (returns nothing or crashes on most files). '
            f'Scores are the average over the test documents of that situation, 0 to 5.</p>'
            f'<h2>2. Details for each situation</h2>{detail}'
            f'<h2>3. Good to know</h2><ul>'
            f'<li>"App picks" is the first parser Smart Extract tries for that type of file. It chooses by file type, not by the situation inside the file, so it can miss (for example two tables side by side).</li>'
            f'<li>hybrid_pdf = PyMuPDF + Tesseract OCR. smart_pdf = the same plus a vision model that reads charts and photos (max 8 per document, needs "Include paid parsers").</li>'
            f'<li>adi_vision = Azure Document Intelligence reads text and tables, a vision model reads only charts and photos (max 8 per document; never a whole page). Paid, never picked automatically. It matches the best parsers on merged-header tables and scans, and is weaker on nested tables.</li><li>Docling is often best but slow: minutes on documents of 30 to 100 pages.</li>'
            f'<li>Some situations rest on one or two documents; the text says so. All documents were generated by us, not real company files. Differences under 0.1 are noise.</li>'
            f'<li>Not tested: Azure Document Intelligence (paid). vlm (sends every page to the LLM) is switched off.</li></ul></div></body></html>')


def main() -> None:
    h = EV / "PARSER_GUIDE.html"
    h.write_text(render_html(), encoding="utf-8")
    rp.html_to_pdf(h, EV / "PARSER_GUIDE.pdf")
    for r in RES:
        c = r["c"]
        print(f"{r['title'][:44]:44s} n={len(r['docs']):2d} best: " + ", ".join(f"{x[0]} {x[1]:.2f}" for x in c.get("best", [])) + f" | app: {r['pick']} -> {r['verdict'][0]}")
    print("wrote PARSER_GUIDE.html / .pdf")


if __name__ == "__main__":
    main()
