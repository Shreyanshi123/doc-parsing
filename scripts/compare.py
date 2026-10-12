"""Compare all free parsers on one or many files and write a report.

    python scripts/compare.py samples/*.pdf
    python scripts/compare.py invoice.pdf --reference invoice_truth.txt
    python scripts/compare.py scan.pdf --parsers ocr,vlm --include-paid

Reports are written to data/outputs/compare/<file>.md and .json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.compare import compare_parsers, report_markdown  # noqa: E402
from app.config import settings  # noqa: E402
from app.models import ParseOptions  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--reference", help="text file with the ground-truth content (single file only)")
    ap.add_argument("--parsers", help="comma separated subset")
    ap.add_argument("--include-paid", action="store_true")
    ap.add_argument("--max-pages", type=int)
    a = ap.parse_args()

    ref = Path(a.reference).read_text(encoding="utf-8") if a.reference else None
    out_dir = settings.outputs_dir / "compare"
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in a.files:
        p = Path(f)
        cmp = compare_parsers(
            p.read_bytes(), p.name, ParseOptions(max_pages=a.max_pages), ref,
            a.parsers.split(",") if a.parsers else None, a.include_paid,
        )
        md = report_markdown(cmp)
        (out_dir / f"{p.stem}.md").write_text(md, encoding="utf-8")
        (out_dir / f"{p.stem}.json").write_text(json.dumps(cmp, indent=2, ensure_ascii=False), encoding="utf-8")
        print(md, "\n")
    print(f"Reports saved in {out_dir}")


if __name__ == "__main__":
    main()
