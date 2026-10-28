"""Fresh head-to-head: every parser on every document that has a hand-written answer file. Nothing from older reports is used.

    python scripts/run_head_to_head.py                  # all parsers, resumable
    python scripts/run_head_to_head.py --only pymupdf,docling

Parsers run ONE AT A TIME (so timings are comparable). Each parser runs in its own worker process that walks through the
documents it supports; if one document takes longer than TIMEOUT the worker is killed, the document is recorded as a
timeout and the worker restarts on the next one. Results: eval/head_to_head/results.jsonl (one line per parser x document).
Skipped on purpose: azure_di (paid, per page) and llamaparse (no API key).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "eval" / "head_to_head"
RESULTS = OUT / "results.jsonl"
TIMEOUT = int(os.environ.get("H2H_TIMEOUT", 400))
SKIP = {"azure_di", "adi_vision", "llamaparse"} - set(filter(None, os.environ.get("H2H_ALLOW", "").split(",")))   # H2H_ALLOW=azure_di runs the paid parser
ORDER = ["text", "spreadsheet", "docx", "pptx", "pdfminer", "pdfplumber", "pymupdf", "markitdown", "haystack_converter", "langchain_loader",
         "llamaindex_reader", "opendataloader", "pymupdf4llm", "hybrid_pdf", "ocr", "unstructured", "docling", "easyocr", "vlm", "smart_pdf", "adi_vision"]

EV, IN = ROOT / "eval", ROOT / "eval" / "industrial"
# document -> content type (used for the summary)
DOCS = {
    # digital text
    "contract.pdf": ("digital text", IN), "form_fields.pdf": ("digital text", IN), "multilingual.pdf": ("digital text", IN), "rotated_pages.pdf": ("digital text", IN),
    "resume.pdf": ("digital text, columns", IN), "two_column_paper.pdf": ("digital text, columns", IN),
    "AI_agent_p1-3.pdf": ("digital text", EV), "Generative_AI_p1-6.pdf": ("digital text", EV),
    # tables
    "invoice.pdf": ("digital tables", IN), "purchase_order.pdf": ("digital tables", IN), "bank_statement.pdf": ("digital tables", IN), "balance_sheet.pdf": ("digital tables", IN),
    "lab_report.pdf": ("digital tables", IN), "datasheet.pdf": ("digital tables", IN), "multipage_table.pdf": ("digital tables", IN), "digital.pdf": ("digital tables", EV),
    # mixed
    "mixed_digital_scanned.pdf": ("mixed text + scan", IN), "mixed.pdf": ("mixed text + scan", EV), "AI_agent_mixed.pdf": ("mixed text + scan", EV),
    # scanned
    "scanned_invoice_clean.pdf": ("scanned", IN), "scanned_invoice_skewed_noisy.pdf": ("scanned", IN), "scanned_invoice_low_quality.pdf": ("scanned, low quality", IN),
    "AI_agent_scanned_clean.pdf": ("scanned", EV), "AI_agent_scanned_noisy.pdf": ("scanned", EV),
    # charts, figures, web pages
    "chart_report.pdf": ("charts and figures", IN), "slides.pdf": ("charts and figures", IN), "chart_sample.pdf": ("charts and figures", EV),
    "PIB_home_p1-6.pdf": ("web page with images", EV), "Overview of Amazon Web Services - Overview of Amazon Web Services.pdf": ("web page with images", EV),
    # photos and images
    "receipt_photo.jpg": ("photo or image", IN), "id_card.png": ("photo or image", IN), "handwritten_note.png": ("photo or image", IN), "screenshot.png": ("photo or image", IN),
    # office and data
    "procedure.docx": ("word", IN), "report.docx": ("word", EV), "slides.pptx": ("powerpoint", IN), "deck.pptx": ("powerpoint", EV),
    "multi_sheet.xlsx": ("excel", IN), "sales.xlsx": ("excel", EV), "parts.csv": ("csv", IN), "sales.csv": ("csv", EV),
    "shift_notes.txt": ("plain text", IN), "runbook.md": ("plain text", IN),
    # content types mixed in one document
    "annual_report_page.pdf": ("all together: text, tables, charts, photo", IN), "scanned_report_page.pdf": ("scanned: table, charts, photo", IN),
    "product_brochure.pdf": ("columns, photo, table", IN), "flowchart_doc.pdf": ("diagram / flowchart", IN), "infographic.pdf": ("infographic (picture)", IN),
    "datasheet_with_photo.pdf": ("photo, table, drawing", IN), "report_with_figures.docx": ("word with charts and photos", IN),
    "dashboard.pptx": ("powerpoint with chart, table, picture", IN), "sales_with_chart.xlsx": ("excel with chart", IN),
    # Copilot industry set
    "01_corporate_annual_report.pdf": ("copilot: annual report with chart", IN), "02_invoice_purchase_order.pdf": ("copilot: invoice", IN),
    "03_legal_contract.pdf": ("copilot: contract", IN), "04_scientific_research_paper.pdf": ("copilot: paper with equations and chart", IN),
    "05_healthcare_discharge_summary.pdf": ("copilot: clinical form", IN), "06_insurance_claim_form.pdf": ("copilot: claim form", IN),
    "07_logistics_shipping_manifest.pdf": ("copilot: manifest, rotated label", IN), "08_software_incident_report.pdf": ("copilot: incident report with logs", IN),
    "09_scanned_maintenance_order.pdf": ("copilot: scanned page", IN), "10_mixed_parser_killer.pdf": ("copilot: mixed content, formula, code", IN),
}


if os.environ.get("H2H_SET") in ("enterprise", "realistic", "long", "mixed_long", "shared"):     # extra document sets: separate results, the routing table is not changed
    _SET = os.environ["H2H_SET"]
    OUT = ROOT / "eval" / f"{_SET}_results"
    RESULTS = OUT / "results.jsonl"
    _ENT = ROOT / "eval" / _SET
    DOCS = {p.name: (f"{_SET}: " + p.stem.replace("_", " "), _ENT) for p in sorted(_ENT.iterdir())
            if p.is_file() and not p.name.endswith(".truth.md") and (_ENT / (p.name + ".truth.md")).exists()}


if os.environ.get("H2H_DOCS"):      # run only these documents (comma separated names)
    _keep = set(os.environ["H2H_DOCS"].split(","))
    DOCS = {k: v for k, v in DOCS.items() if k in _keep}


def doc_path(name: str) -> Path:
    return DOCS[name][1] / name


def truth_path(name: str) -> Path:
    return EV / "chart_sample.values.md" if name == "chart_sample.pdf" else DOCS[name][1] / f"{name}.truth.md"


def worker(parser_name: str) -> None:
    sys.path.insert(0, str(ROOT))
    from app.compare import count_tables
    from app.models import ParseOptions
    from app.normalizer import normalize_document
    from app.parsers import get_parser_class
    from app.routing.file_type import resolve_file_type
    from app.scorecard import score

    done = {(r["parser"], r["doc"]) for r in map(json.loads, RESULTS.read_text(encoding="utf-8").splitlines())} if RESULTS.exists() else set()
    skip_file = OUT / "skip.txt"      # parsers listed here are left for later (one name per line); delete the line to run them
    if skip_file.exists() and parser_name in skip_file.read_text(encoding="utf-8").split():
        return
    cls = get_parser_class(parser_name)
    out = open(RESULTS, "a", encoding="utf-8")

    def write(rec):
        out.write(json.dumps(rec, default=str) + "\n")
        out.flush()

    ok, why = cls.is_available()
    if not ok:
        write({"parser": parser_name, "doc": "*", "status": "unavailable", "detail": why[:200]})
        return
    progress = OUT / f"progress_{parser_name}.txt"
    (OUT / "_out").mkdir(exist_ok=True)
    for name in DOCS:
        if (parser_name, name) in done:
            continue
        data = doc_path(name).read_bytes()
        ft = resolve_file_type(data, name)
        if ft not in cls.supported_types:
            continue
        progress.write_text(f"{name}\t{time.time()}", encoding="utf-8")
        t0 = time.time()
        rec = {"parser": parser_name, "doc": name, "type": DOCS[name][0]}
        try:
            md = normalize_document(cls().parse(data, name, ft, ParseOptions())).markdown
            rec.update(status="ok" if md.strip() else "empty", words=len(md.split()), tables=count_tables(md))
            card = score(truth_path(name).read_text(encoding="utf-8"), md)
            v = [x for x in card.values() if x is not None]
            rec["score"] = round(5 * sum(v) / len(v), 2) if v else None
            rec["card"] = {k: (round(5 * x, 1) if x is not None else None) for k, x in card.items()}
            (OUT / "_out" / f"{parser_name}__{name}.md").write_text(md, encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            rec.update(status="error", detail=f"{type(e).__name__}: {e}"[:200], score=0.0)
        rec["secs"] = round(time.time() - t0, 1)
        write(rec)
    progress.unlink(missing_ok=True)


def run_parser(parser_name: str) -> None:
    progress = OUT / f"progress_{parser_name}.txt"
    while True:
        p = subprocess.Popen([sys.executable, __file__, "--worker", parser_name], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        killed = None
        while p.poll() is None:
            time.sleep(4)
            if progress.exists():
                try:
                    doc, started = progress.read_text(encoding="utf-8").split("\t")
                except ValueError:
                    continue
                if time.time() - float(started) > TIMEOUT:
                    p.kill()
                    p.wait()
                    killed = doc
                    break
        if killed:
            with open(RESULTS, "a", encoding="utf-8") as f:
                f.write(json.dumps({"parser": parser_name, "doc": killed, "type": DOCS[killed][0], "status": "timeout", "secs": TIMEOUT, "score": 0.0}) + "\n")
            progress.unlink(missing_ok=True)
            continue  # restart on the next document
        if p.returncode not in (0, None):  # worker crashed outright: record and move on
            doc = progress.read_text(encoding="utf-8").split("\t")[0] if progress.exists() else None
            if doc:
                with open(RESULTS, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"parser": parser_name, "doc": doc, "type": DOCS[doc][0], "status": "error", "detail": f"worker crashed (exit {p.returncode})", "score": 0.0, "secs": 0}) + "\n")
                progress.unlink(missing_ok=True)
                continue
        break


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker")
    ap.add_argument("--only")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.worker:
        worker(a.worker)
        return
    sys.path.insert(0, str(ROOT))
    import app.parsers  # noqa: F401
    from app.parsers.registry import _REGISTRY

    names = [n for n in ORDER if n in _REGISTRY] + sorted(n for n in _REGISTRY if n not in ORDER)
    names = [n for n in names if n not in SKIP]
    if a.only:
        names = [n for n in names if n in a.only.split(",")]
    print("parsers:", names, flush=True)
    for n in names:
        t = time.time()
        run_parser(n)
        print(f"{n:20s} finished in {time.time() - t:.0f}s", flush=True)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
