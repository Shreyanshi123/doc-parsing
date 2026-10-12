"""Parse one local file from the command line (no server needed).

    python scripts/parse_file.py samples/report.docx
    python scripts/parse_file.py samples/scanned.pdf --parser ocr --out out.json
    python scripts/parse_file.py scan.pdf --prefer-quality --max-pages 2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import ParseOptions  # noqa: E402
from app.pipeline import ParseFailed, build_output, parse_bytes  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--parser", default="auto")
    ap.add_argument("--prefer-quality", action="store_true")
    ap.add_argument("--extract-images", action="store_true")
    ap.add_argument("--max-pages", type=int)
    ap.add_argument("--out", help="write JSON here (default: print markdown)")
    a = ap.parse_args()

    p = Path(a.file)
    opts = ParseOptions(prefer_quality=a.prefer_quality, extract_images=a.extract_images, max_pages=a.max_pages)
    try:
        res = parse_bytes(p.read_bytes(), p.name, opts, a.parser)
    except Exception as e:  # noqa: BLE001
        sys.exit(f"ERROR: {e}")
    out = build_output(res, file_id=p.name, tenant_id="cli", include_images=True)
    print(f"# engine={out['metadata']['engine']} reason={out['routing']['reason']} stats={out['stats']}", file=sys.stderr)
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"JSON written to {a.out}", file=sys.stderr)
    else:
        print(out["content"])


if __name__ == "__main__":
    main()
