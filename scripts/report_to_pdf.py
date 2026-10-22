"""Render eval/REPORT.md to eval/REPORT.pdf (PyMuPDF only, no extra installs).

    python scripts/report_to_pdf.py
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "eval" / "REPORT.md", ROOT / "eval" / "REPORT.pdf"
if len(sys.argv) == 3:  # python scripts/report_to_pdf.py in.md out.pdf
    SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])

CSS = """
body { font-family: sans-serif; font-size: 9.5pt; color: #1d2330; }
h1 { font-size: 20pt; margin: 0 0 6pt 0; color: #14307a; }
h2 { font-size: 13.5pt; margin: 14pt 0 4pt 0; color: #14307a; }
p, li { margin: 3pt 0; line-height: 1.3; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; }
th { background-color: #e8edfb; text-align: left; font-weight: bold; }
th, td { border: 0.6pt solid #b8c0d4; padding: 3pt 4pt; font-size: 8.3pt; vertical-align: top; }
code { font-family: monospace; font-size: 8.6pt; background-color: #f0f2f6; }
"""


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def md_to_html(md: str) -> str:
    out, lines, i = [], md.splitlines(), 0
    list_tag = None

    def close_list():
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    while i < len(lines):
        line = lines[i]
        if line.startswith("|"):
            close_list()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            out.append("<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in rows[0]) + "</tr>")
            for r in rows[1:]:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("</table>")
            continue
        m = re.match(r"^(#{1,3}) (.*)", line)
        if m:
            close_list()
            n = min(len(m.group(1)), 2)
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
        elif re.match(r"^\d+\. ", line) or line.startswith("- "):
            tag = "ol" if line[0].isdigit() else "ul"
            if list_tag != tag:
                close_list()
                out.append(f"<{tag}>")
                list_tag = tag
            out.append(f"<li>{inline(re.sub(r'^(\d+\.|-) ', '', line))}</li>")
        elif line.strip():
            close_list()
            out.append(f"<p>{inline(line)}</p>")
        i += 1
    close_list()
    return "\n".join(out)


def main():
    story = pymupdf.Story(html=md_to_html(SRC.read_text(encoding="utf-8")), user_css=CSS)
    writer = pymupdf.DocumentWriter(str(OUT))
    mediabox = pymupdf.paper_rect("a4-l")  # landscape: the tables are wide
    where = mediabox + (36, 36, -36, -36)
    more = True
    while more:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
