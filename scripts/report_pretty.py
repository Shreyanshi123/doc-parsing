"""Renders eval/COMPLETE_REPORT.md as a plain HTML report and as a PDF (printed from the same HTML with Chrome, so both look the same).

    python scripts/report_pretty.py                      # eval/COMPLETE_REPORT.md -> .html and .pdf
    python scripts/report_pretty.py in.md out_stem

Plain style on purpose: white page, black text, thin grey table lines, pale colour only inside score cells.
"""
from __future__ import annotations

import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "eval" / "COMPLETE_REPORT.md"
STEM = ROOT / "eval" / "COMPLETE_REPORT"
if len(sys.argv) == 3:
    SRC, STEM = Path(sys.argv[1]), Path(sys.argv[2])

HEAT = ["#f6cfd3", "#fbe1c0", "#f3efb8", "#d3ecce", "#a9deaf"]
SCORE_HEADS = {"overall", "score", "text", "table", "chart", "numbers", "structure", "complete", "no extras", "average score", "by document, paid", "by part, paid", "by document, free"}
CHROME = next((p for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe") if Path(p).exists()), None)

CSS = """
body{font-family:"Segoe UI",Arial,Helvetica,sans-serif;font-size:14px;line-height:1.5;color:#111;background:#fff;margin:0}
.page{max-width:1060px;margin:0 auto;padding:24px 28px 60px}
h1{font-size:24px;margin:0 0 4px}
h2{font-size:18px;margin:30px 0 8px;padding-bottom:4px;border-bottom:1px solid #999}
h3{font-size:15px;margin:20px 0 6px}
h4{font-size:14px;margin:14px 0 4px}
p,li{margin:5px 0}
ul,ol{padding-left:22px}
.sub{color:#444;margin:0 0 14px}
nav.toc{margin:10px 0 6px;font-size:13px}
nav.toc a{color:#1a4fa0;text-decoration:none;margin-right:14px;white-space:nowrap}
table{border-collapse:collapse;width:100%;margin:8px 0 12px;font-size:13px}
th,td{border:1px solid #b5b5b5;padding:4px 7px;text-align:left;vertical-align:top}
th{background:#ececec;font-weight:600}
code{font-family:Consolas,monospace;font-size:12.5px;background:#f1f1f1;padding:0 3px}
details{border:1px solid #c8c8c8;margin:8px 0;padding:0 10px}
summary{cursor:pointer;font-weight:600;padding:6px 0}
.eq{color:#1b6e3c;font-weight:600}.win{color:#1a4fa0;font-weight:600}.bad{color:#b4233c;font-weight:600}
.legend{font-size:12.5px;color:#333;margin:8px 0 12px}
.legend span.k{display:inline-block;padding:1px 8px;margin-right:4px;border:1px solid #bbb}
@page{size:A4;margin:12mm}
@media print{body{font-size:12px}table{font-size:10.5px}th,td{padding:3px 5px}.toc{display:none}details{border:0;padding:0}summary{display:none}.page{max-width:none;padding:0}h2{break-after:avoid}h3,h4{break-after:avoid}tr{break-inside:avoid}}
"""
JS = "if(location.search.indexOf('print')>=0){document.querySelectorAll('details').forEach(function(d){d.open=true;});}"


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def blocks(md: str) -> list[dict]:
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            out.append({"t": "table", "rows": rows})
            continue
        m = re.match(r"^(#{1,4}) (.*)", ln)
        if m:
            out.append({"t": "h", "n": len(m.group(1)), "text": m.group(2).strip()})
        elif re.match(r"^\d+\. ", ln) or ln.startswith("- "):
            tag = "ol" if ln[0].isdigit() else "ul"
            items = []
            while i < len(lines) and (re.match(r"^\d+\. ", lines[i]) or lines[i].startswith("- ")):
                items.append(re.sub(r"^(\d+\.|-) ", "", lines[i]))
                i += 1
            out.append({"t": tag, "items": items})
            continue
        elif ln.strip():
            out.append({"t": "p", "text": ln.strip()})
        i += 1
    return out


def heat(v: float) -> int:
    return 4 if v >= 4.5 else 3 if v >= 3.5 else 2 if v >= 2.5 else 1 if v >= 1.2 else 0


def num(s: str):
    s = s.replace("**", "").strip()
    return float(s) if re.fullmatch(r"\d(\.\d+)?", s) else None


def chipify(raw: str) -> str:
    """Words like 'equal to best' / 'clear winner' / timeout / empty get a colour (text only)."""
    t = inline(raw)
    t = re.sub(r"<b>equal to best</b>", '<span class="eq">equal to best</span>', t)
    t = re.sub(r"<b>clear winner</b>", '<span class="win">clear winner</span>', t)
    t = re.sub(r"\(EQUAL to best\)", '<span class="eq">(equal to best)</span>', t)
    t = re.sub(r"\(clear winner\)", '<span class="win">(clear winner)</span>', t)
    t = re.sub(r"^EQUAL( \(within 0\.1\))?:", '<span class="eq">EQUAL</span> (within 0.1):', t)
    t = re.sub(r"^clear best:", '<span class="win">clear best</span>:', t)
    t = re.sub(r"\((timeout|empty|empty output)\)", lambda m: f'<span class="bad">({m.group(1)})</span>', t)
    return t


def cell(head: str, raw: str) -> tuple[str, str]:
    """-> (inner html, td style)"""
    h = head.lower()
    v = num(raw)
    if (h in SCORE_HEADS or h.startswith("score") or h.endswith("score")) and v is not None and v <= 5:
        return raw.replace("**", ""), f"background:{HEAT[heat(v)]};white-space:nowrap"
    mm = re.match(r"^\*{0,2}(\d\.\d\d)\*{0,2}\s*(\(.*\))$", raw.strip())
    if mm and (h in SCORE_HEADS or h.startswith("by ")):
        return f"{mm.group(1)} {html.escape(mm.group(2))}", f"background:{HEAT[heat(float(mm.group(1)))]}"
    return chipify(raw), ""


def table_html(rows: list[list[str]]) -> str:
    head = rows[0]
    th = "".join(f"<th>{inline(c)}</th>" for c in head)
    body = []
    for r in rows[1:]:
        tds = []
        for j, c in enumerate(r):
            inner, style = cell(head[j] if j < len(head) else "", c)
            tds.append(f'<td style="{style}">{inner}</td>' if style else f"<td>{inner}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f"<table><tr>{th}</tr>{''.join(body)}</table>"


def block_html(b: dict) -> str:
    t = b["t"]
    if t == "table":
        return table_html(b["rows"])
    if t in ("ul", "ol"):
        return f"<{t}>" + "".join(f"<li>{chipify(x)}</li>" for x in b["items"]) + f"</{t}>"
    if t == "p":
        return f"<p>{chipify(b['text'])}</p>"
    return ""


LEGEND = ('<div class="legend">Score colours: <span class="k" style="background:%s">4.5 and above</span><span class="k" style="background:%s">3.5 to 4.5</span>'
          '<span class="k" style="background:%s">2.5 to 3.5</span><span class="k" style="background:%s">1.2 to 2.5</span><span class="k" style="background:%s">below 1.2</span> &nbsp; '
          '<span class="eq">equal to best</span> = within 0.1 of the best, not ranked against each other; <span class="win">clear winner</span> = more than 0.1 ahead.</div>') % (
    HEAT[4], HEAT[3], HEAT[2], HEAT[1], HEAT[0])


def render_html(md: str) -> str:
    bl = blocks(md)
    h1 = next(b for b in bl if b["t"] == "h" and b["n"] == 1)["text"]
    sub = next((b["text"] for b in bl if b["t"] == "p"), "")
    sections, cur = [], None
    for b in bl:
        if b["t"] == "h" and b["n"] == 1:
            continue
        if b["t"] == "h" and b["n"] == 2:
            cur = {"title": b["text"], "items": []}
            sections.append(cur)
        elif cur is not None:
            cur["items"].append(b)
    toc = "".join(f'<a href="#s{i}">{html.escape(s["title"])}</a>' for i, s in enumerate(sections))
    body = []
    for i, s in enumerate(sections):
        appendix = s["title"].startswith("Appendix")
        out, open_d = [], False
        for b in s["items"]:
            if b["t"] == "h" and appendix and b["n"] >= 3:
                if open_d:
                    out.append("</details>")
                out.append(f"<details><summary>{inline(b['text'])}</summary>")
                open_d = True
            elif b["t"] == "h":
                n = min(b["n"], 4)
                out.append(f"<h{n}>{inline(b['text'])}</h{n}>")
            else:
                out.append(block_html(b))
        if open_d:
            out.append("</details>")
        body.append(f'<h2 id="s{i}">{inline(s["title"])}</h2>{"".join(out)}')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(h1)}</title>'
            f'<style>{CSS}</style></head><body><div class="page"><h1>{inline(h1)}</h1><p class="sub">{inline(sub)}</p><nav class="toc">{toc}</nav>{LEGEND}{"".join(body)}</div><script>{JS}</script></body></html>')


def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    if not CHROME:
        raise SystemExit("Chrome or Edge not found: cannot make the PDF")
    prof = tempfile.mkdtemp(prefix="pdfprof_")
    url = html_path.resolve().as_uri() + "?print"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={prof}", f"--print-to-pdf={pdf_path.resolve()}", url],
                   check=False, capture_output=True, timeout=240)


def main() -> None:
    md = SRC.read_text(encoding="utf-8")
    h = STEM.with_suffix(".html")
    h.write_text(render_html(md), encoding="utf-8")
    html_to_pdf(h, STEM.with_suffix(".pdf"))
    print("wrote", h, "and", STEM.with_suffix(".pdf"))


if __name__ == "__main__":
    main()
