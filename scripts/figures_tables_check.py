"""How many tables and figures does each parser find on big documents, and are the tables right?

    python scripts/figures_tables_check.py --dir <folder with PDFs> --files a.pdf,b.pdf --out-dir <where to save outputs>

For every parser it saves the Markdown output and counts:
  tables found     Markdown or HTML tables in the output
  table cells      cells inside those tables
  cells vs ADI     F1 of the cell values against Azure DI's tables (how close the tables are, not proof of correctness)
  figures marked   figure / image markers left in the output (<figure>, <!-- image -->, ![ ], **Figure ...)
  figures read     figures whose content was turned into text or values (smart_pdf only)
Figures the PDF really holds are counted separately with app/figures.find_figures (a layout heuristic, not a truth).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pymupdf  # noqa: E402

from app.compare import _list_f1, _table_cells, count_tables, figure_markers  # noqa: E402
from app.figures import find_figures  # noqa: E402
from app.models import ParseOptions  # noqa: E402
from app.normalizer import normalize_document  # noqa: E402
from app.parsers import get_parser_class  # noqa: E402


def figures_read(md: str) -> int:
    n = 0
    for m in re.finditer(r"^\*\*Figure \(page.*$", md, flags=re.M):
        line = m.group(0).lower()
        if "skipped" not in line and "not read" not in line and "found;" not in line:
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--files", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--parsers", default="azure_di,pymupdf4llm,hybrid_pdf,opendataloader,smart_pdf,markitdown,pdfplumber,docling")
    a = ap.parse_args()
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    opts = ParseOptions()
    report = {}
    for f in a.files.split(","):
        p = Path(a.dir) / f
        data = p.read_bytes()
        doc = pymupdf.open(stream=data, filetype="pdf")
        layout_figs = sum(len(find_figures(pg, [])) for pg in doc)
        print(f"[{f}] {doc.page_count} pages, {layout_figs} figures by layout heuristic", flush=True)
        res, adi_cells = {}, []
        for name in a.parsers.split(","):
            ok, why = get_parser_class(name).is_available()
            if not ok:
                print(f"   skipping {name}: {why}", flush=True)
                continue
            t = time.perf_counter()
            try:
                md = normalize_document(get_parser_class(name)().parse(data, f, "pdf", opts)).markdown
                err = None
            except Exception as e:  # noqa: BLE001
                md, err = "", f"{type(e).__name__}: {str(e)[:120]}"
            (out_dir / f"{p.stem}__{name}.md").write_text(md, encoding="utf-8")
            cells = _table_cells(md)
            if name == "azure_di":
                adi_cells = cells
            res[name] = {"tables": count_tables(md), "cells": len(cells), "figures_marked": figure_markers(md),
                         "figures_read": figures_read(md), "words": len(md.split()), "secs": round(time.perf_counter() - t, 1),
                         "error": err, "_cells": cells}
            print(f"   {name:15} tables={res[name]['tables']:3} cells={len(cells):5} figs_marked={res[name]['figures_marked']:3} "
                  f"read={res[name]['figures_read']:3} {res[name]['secs']:7.1f}s {err or ''}", flush=True)
        for name, r in res.items():
            r["cells_vs_adi"] = None if name == "azure_di" or not adi_cells else round(_list_f1(adi_cells, r.pop("_cells")), 3)
            r.pop("_cells", None)
        report[f] = {"pages": doc.page_count, "layout_figures": layout_figs, "parsers": res}
        (out_dir / "figures_tables.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\nwrote", out_dir / "figures_tables.json")


if __name__ == "__main__":
    main()
