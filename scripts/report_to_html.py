"""Render a Markdown report to one self-contained HTML file (no extra installs).

    python scripts/report_to_html.py eval/INDUSTRIAL_TEST_REPORT.md eval/INDUSTRIAL_TEST_REPORT.html
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_to_pdf import md_to_html  # noqa: E402

CSS = """
:root { --bg:#f6f8fc; --card:#fff; --fg:#1d2330; --muted:#5a6578; --line:#d9dfec; --accent:#14307a; --head:#e8edfb; --code:#eef1f7; }
@media (prefers-color-scheme: dark) { :root { --bg:#0e1118; --card:#161b26; --fg:#e6eaf3; --muted:#9aa5ba; --line:#2a3245; --accent:#8fb0ff; --head:#1f2a44; --code:#1c2333; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.6 Inter, "Segoe UI", system-ui, sans-serif; }
main { max-width:1040px; margin:0 auto; padding:28px 16px 64px; }
h1 { font-size:2rem; color:var(--accent); margin:0 0 .4em; letter-spacing:-.02em; }
h2 { font-size:1.3rem; color:var(--accent); margin:1.8em 0 .4em; padding-top:.4em; border-top:1px solid var(--line); }
p, li { margin:.35em 0; }
ul, ol { padding-left:1.4em; }
.tablewrap { overflow-x:auto; margin:.8em 0; border:1px solid var(--line); border-radius:10px; background:var(--card); }
table { border-collapse:collapse; width:100%; font-size:.88rem; }
th, td { padding:7px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { background:var(--head); font-weight:650; white-space:nowrap; }
tr:last-child td { border-bottom:0; }
code { font-family:"JetBrains Mono", Consolas, monospace; font-size:.85em; background:var(--code); padding:1px 5px; border-radius:5px; }
@media (max-width:600px) { body { font-size:14px; } h1 { font-size:1.55rem; } }
"""


def main() -> None:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    md = src.read_text(encoding="utf-8")
    body = md_to_html(md).replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
    title = next((l.lstrip("# ").strip() for l in md.splitlines() if l.startswith("#")), src.stem)
    out.write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                   f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main>{body}</main></body></html>", encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
