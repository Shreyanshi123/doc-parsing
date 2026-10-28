"""Long documents that mix everything, written to eval/mixed_long/ with an exact answer file for each.

    python scripts/make_mixed_long_docs.py

operations_report_36p.pdf  36 pages: text, simple tables, merged-header tables, two tables side by side, a table inside a table, bar and pie
                           charts, photos, and 6 scanned pages (only pictures of pages, tilt + noise) in the middle
tender_pack_30p.pdf        about 30 pages: two-column text, a requirements matrix with spanning cells that runs over many pages, form grids,
                           photos with captions
"""
from __future__ import annotations

import io
import random
import sys
from pathlib import Path

import fitz
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_enterprise_docs as e  # noqa: E402
import make_industrial_corpus as m  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "eval" / "mixed_long"
e.ENT = OUT
e.IMG = OUT / "_img"
rows_md, write_truth, neg = e.rows_md, e.write_truth, e.neg
WORDS = ("plant output quality safety supplier delivery maintenance audit energy sensor schedule customer inventory training budget risk control process review "
         "capacity demand cost margin contract payment vendor shipment warehouse compliance policy target growth region product service report").split()
TOPICS = ["Safety", "Quality", "Delivery", "Cost", "People", "Energy", "Suppliers", "Customers", "Projects", "Risks"]
BREAK = "<p style='page-break-before:always'></p>"


def para(rnd, n=100):
    w = [rnd.choice(WORDS) for _ in range(n)]
    w[0] = w[0].capitalize()
    return " ".join(w) + "."


def chart(kind: str, tag: str, rnd) -> tuple[str, str, list]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5, 2.8))
    if kind == "bar":
        cats, vals = ["Q1", "Q2", "Q3", "Q4"], [rnd.randint(40, 400) for _ in range(4)]
        ax.bar(cats, vals, color="#2c7fb8")
        for i, v in enumerate(vals):
            ax.text(i, v + 5, str(v), ha="center", fontsize=8)
        ax.set_ylim(0, max(vals) * 1.2)
        title = f"Output index, {tag}"
    else:
        cats, vals = ["Pumps", "Valves", "Seals"], [45, 30, 25]
        rnd.shuffle(vals)
        ax.pie(vals, labels=[f"{c} {v}%" for c, v in zip(cats, vals)])
        title = f"Sales mix, {tag}"
    ax.set_title(title)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110)
    plt.close(fig)
    name = f"{kind}_{tag.replace(' ', '_')}.png"
    (e.IMG / name).write_bytes(buf.getvalue())
    return name, title, list(zip(cats, vals))


def chart_truth(title, data, kind):
    head = "Bar chart" if kind == "bar" else "Pie chart"
    col = "Value" if kind == "bar" else "Percentage"
    return f"## {head}: {title}\n\n| Category | {col} |\n|---|---|\n" + "\n".join(f"| {c} | {v}{'%' if kind == 'pie' else ''} |" for c, v in data) + "\n\n"


def sections(prefix: str, start: int, count: int, rnd, charts: list, chart_table: bool = True):
    """HTML + answer text for `count` mixed sections."""
    html, truth = "", ""
    for k in range(count):
        s = start + k
        topic = TOPICS[s % len(TOPICS)]
        title = f"Section {s}: {topic} review"
        p1 = para(rnd)
        html += f"{BREAK}<h2>{title}</h2><p>{p1}</p>"
        truth += f"## {title}\n\n{p1}\n\n"
        kind = s % 6
        if kind == 0:   # simple table
            rows = [[f"{topic} metric {i}", rnd.randint(100, 9999), f"{rnd.randint(1, 99)}.{rnd.randint(0, 9)}%", rnd.choice(["On track", "Watch", "Action"])] for i in range(1, 7)]
            html += m.html_table(["Metric", "Value", "Change", "Status"], rows, right=(1, 2))
            truth += rows_md([["Metric", "Value", "Change", "Status"]] + rows) + "\n\n"
        elif kind == 1:  # merged two-row header
            rows = [[f"{topic} {r}", rnd.randint(10, 99), rnd.randint(10, 99), rnd.randint(10, 99), rnd.randint(10, 99)] for r in ("North", "South", "East", "West")]
            html += ("<table><tr><th rowspan='2'>Region</th><th colspan='2'>Year 2026</th><th colspan='2'>Year 2025</th></tr><tr><th>Plan</th><th>Actual</th><th>Plan</th><th>Actual</th></tr>"
                     + "".join("<tr><td>" + str(r[0]) + "</td>" + "".join(f"<td class='n'>{v}</td>" for v in r[1:]) + "</tr>" for r in rows) + "</table>")
            truth += rows_md([["Region", "Year 2026", "Year 2025"], ["", "Plan", "Actual", "Plan", "Actual"]] + rows) + "\n\n"
        elif kind == 2:  # two tables side by side
            a = [[f"Item {i}", f"{rnd.randint(1000, 9999)}.00"] for i in range(1, 5)]
            b = [[f"Deduction {i}", f"{rnd.randint(100, 999)}.00"] for i in range(1, 5)]
            html += ("<table class='nb'><tr><td width='49%'>" + m.html_table(["Earnings", "Amount"], a, right=(1,)) + "</td><td width='2%'></td><td>"
                     + m.html_table(["Deductions", "Amount"], b, right=(1,)) + "</td></tr></table>")
            truth += rows_md([["Earnings", "Amount"]] + a) + "\n\n" + rows_md([["Deductions", "Amount"]] + b) + "\n\n"
        elif kind == 3:  # bar chart + small table
            name, ctitle, data = chart("bar", f"section {s}", rnd)
            charts.append((ctitle, data, "bar"))
            rows = [[f"Q{i + 1}", v] for i, (_, v) in enumerate(data)]
            html += f"<img src='{name}' width='300'><p><small>Figure {s}. {ctitle}.</small></p>" + (m.html_table(["Quarter", "Value"], rows, right=(1,)) if chart_table else "")
            truth += f"Figure {s}. {ctitle}.\n\n" + (rows_md([["Quarter", "Value"]] + rows) + "\n\n" if chart_table else "")
        elif kind == 4:  # photo + nested table
            e.photo()
            inner = [["Cover", "Sum insured", "Deductible"], ["Fire", "5,000,000", "1,000"], ["Theft", "1,500,000", "2,500"]]
            html += (f"<img src='photo.jpg' width='230'><p><small>Photo {s}. Site inspection, section {s}.</small></p><table><tr><td width='35%'><b>Policy</b></td><td>POL-{rnd.randint(1000, 9999)}</td></tr>"
                     "<tr><td><b>Coverage</b></td><td>" + m.html_table(inner[0], inner[1:], right=(1, 2)) + "</td></tr></table>")
            truth += f"Photo {s}. Site inspection, section {s}.\n\n" + rows_md([["Policy", "POL"], ["Coverage"]]) + "\n\n" + rows_md(inner) + "\n\n"
        else:           # pie chart
            name, ctitle, data = chart("pie", f"section {s}", rnd)
            charts.append((ctitle, data, "pie"))
            html += f"<img src='{name}' width='260'><p><small>Figure {s}. {ctitle}.</small></p><p>{para(rnd, 60)}</p>"
            truth += f"Figure {s}. {ctitle}.\n\n"
    return html, truth


def scanned_part(rnd, n_pages: int, start: int = 1):
    head = "Appendix: Inspection log" if start == 1 else f"Appendix: Inspection log (continued from {start - 1})"
    html, truth = f"<h1>{head}</h1>", f"# {head}\n\n"
    for i in range(start, start + n_pages):
        p1 = para(rnd, 90)
        rows = [[f"Check {i}.{k}", rnd.choice(["Pass", "Fail", "Pass"]), f"{rnd.randint(1, 99)}.{rnd.randint(0, 9)}"] for k in range(1, 5)]
        html += f"{BREAK}<h2>Inspection {i}</h2><p>{p1}</p>" + m.html_table(["Check", "Result", "Reading"], rows, right=(2,))
        truth += f"## Inspection {i}\n\n{p1}\n\n" + rows_md([["Check", "Result", "Reading"]] + rows) + "\n\n"
    src = e.save_pdf(html, "_scan_source.pdf")
    d = fitz.open(src)
    out = fitz.open()
    for pg in d:
        im = Image.open(io.BytesIO(pg.get_pixmap(dpi=130).tobytes("png"))).convert("RGB")
        im = m.degrade(im, angle=rnd.choice([-1.2, 0.8, 1.5]), noise=12, blur=0.6)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=62)
        o = out.new_page(width=595, height=842)
        o.insert_image(o.rect, stream=buf.getvalue())
    d.close()
    src.unlink()
    return out, truth


def operations_report() -> None:
    rnd = random.Random(71)
    charts: list = []
    htA, trA = sections("a", 1, 14, rnd, charts)
    htB, trB = sections("b", 15, 14, rnd, charts)
    cover = "<h1>Operations Report 2026</h1><p>Northstar Industries. Sections 1 to 28 follow; the inspection log at the end of section 14 is a scanned appendix.</p>"
    pa = e.save_pdf(cover + htA, "_part1.pdf", archive=e.IMG)
    pb = e.save_pdf(htB[len(BREAK):] if htB.startswith(BREAK) else htB, "_part2.pdf", archive=e.IMG)
    scan, trS = scanned_part(rnd, 6)
    final = fitz.open()
    final.insert_pdf(fitz.open(pa))
    final.insert_pdf(scan)
    final.insert_pdf(fitz.open(pb))
    final.save(OUT / "operations_report_36p.pdf")
    n = len(final)
    for p in (pa, pb):
        p.unlink()
    truth = ("# Operations Report 2026\n\nNorthstar Industries. Sections 1 to 28 follow; the inspection log at the end of section 14 is a scanned appendix.\n\n" + trA + trS + trB)
    for t, data, kind in charts:
        truth += chart_truth(t, data, kind)
    write_truth("operations_report_36p.pdf", truth)
    print("operations_report pages", n, flush=True)


def group_report_100p() -> None:
    rnd = random.Random(73)
    charts: list = []
    htA, trA = sections("a", 1, 41, rnd, charts, chart_table=False)
    htB, trB = sections("b", 42, 41, rnd, charts, chart_table=False)
    cover = "<h1>Group Operations Report 2026</h1><p>Northstar Industries. Sections 1 to 82 follow, with two scanned inspection logs.</p>"
    pa = e.save_pdf(cover + htA, "_p100a.pdf", archive=e.IMG)
    pb = e.save_pdf(htB[len(BREAK):] if htB.startswith(BREAK) else htB, "_p100b.pdf", archive=e.IMG)
    scan1, trS1 = scanned_part(rnd, 7, 1)
    scan2, trS2 = scanned_part(rnd, 7, 8)
    final = fitz.open()
    for part in (fitz.open(pa), scan1, fitz.open(pb), scan2):
        final.insert_pdf(part)
    final.save(OUT / "group_report_100p.pdf")
    n = len(final)
    for p in (pa, pb):
        p.unlink()
    truth = "# Group Operations Report 2026\n\nNorthstar Industries. Sections 1 to 82 follow, with two scanned inspection logs.\n\n" + trA + trS1 + trB + trS2
    for t, data, kind in charts:
        truth += chart_truth(t, data, kind)
    write_truth("group_report_100p.pdf", truth)
    print("group_report pages", n, flush=True)


def tender_pack() -> None:
    rnd = random.Random(72)
    html, truth = "<h1>Tender Pack TP-2026-031</h1><p>Supply and maintenance of industrial pumps for Plant B.</p>", "# Tender Pack TP-2026-031\n\nSupply and maintenance of industrial pumps for Plant B.\n\n"
    cats = ["Technical", "Commercial", "Legal", "Delivery", "Support"]
    req_rows = []
    n = 0
    for s in range(1, 31):
        topic = TOPICS[s % len(TOPICS)]
        title = f"Part {s}: {topic} requirements"
        html += f"{BREAK}<h2>{title}</h2>"
        truth += f"## {title}\n\n"
        k = s % 5
        if k == 0:   # two-column text
            left, right = para(rnd, 130), para(rnd, 130)
            html += f"<table class='nb'><tr><td width='49%'>{left}</td><td width='2%'></td><td>{right}</td></tr></table>"
            truth += left + "\n\n" + right + "\n\n"
        elif k == 1:  # matrix with spanning category cells (one block per part)
            h = "<table><tr><th>Category</th><th>ID</th><th>Requirement</th><th>Priority</th></tr>"
            tr = [["Category", "ID", "Requirement", "Priority"]]
            for c in rnd.sample(cats, 3):
                reqs = [(f"R{s:02d}-{n + i:03d}", para(rnd, 14), rnd.choice(["Must", "Should", "Could"])) for i in range(1, 4)]
                n += 3
                for i, (rid, text, pr) in enumerate(reqs):
                    h += "<tr>" + (f"<td rowspan='3'><b>{c}</b></td>" if i == 0 else "") + f"<td>{rid}</td><td>{text}</td><td>{pr}</td></tr>"
                    tr.append([c, rid, text, pr])
            html += h + "</table>"
            truth += rows_md(tr) + "\n\n"
        elif k == 2:  # form grid
            cells = [("Bidder name", f"Bidder {s} Engineering Pvt Ltd"), ("Registration no.", f"U{rnd.randint(10000, 99999)}MH2010PTC{rnd.randint(100000, 999999)}"), ("Quoted price (INR)", f"{rnd.randint(1000000, 9999999):,}"),
                     ("Delivery (days)", str(rnd.randint(30, 120))), ("Warranty (months)", str(rnd.choice([12, 18, 24]))), ("Signatory", "Authorised representative")]
            html += "<table>" + "".join("<tr>" + "".join(f"<td width='50%'><small>{a}</small><br><b>{b}</b></td>" for a, b in cells[i:i + 2]) + "</tr>" for i in range(0, 6, 2)) + "</table>"
            html += "<p>[X] Technical bid enclosed &nbsp; [ ] Samples enclosed</p>"
            truth += "\n".join(f"{a} {b}" for a, b in cells) + "\n[X] Technical bid enclosed [ ] Samples enclosed\n\n"
        elif k == 3:  # photo + caption + table
            e.photo()
            rows = [[f"Pump {i}", rnd.randint(10, 90), f"{rnd.randint(1, 9)}.{rnd.randint(0, 9)}"] for i in range(1, 5)]
            html += f"<img src='photo.jpg' width='230'><p><small>Photo {s}. Reference installation {s}.</small></p>" + m.html_table(["Model", "Flow (m3/h)", "Head (m)"], rows, right=(1, 2))
            truth += f"Photo {s}. Reference installation {s}.\n\n" + rows_md([["Model", "Flow (m3/h)", "Head (m)"]] + rows) + "\n\n"
        else:        # text + bar chart
            p1 = para(rnd, 70)
            name, ctitle, data = chart("bar", f"part {s}", rnd)
            html += f"<p>{p1}</p><img src='{name}' width='290'><p><small>Figure {s}. {ctitle}.</small></p>"
            truth += f"{p1}\n\nFigure {s}. {ctitle}.\n\n"
            req_rows.append((ctitle, data))
    p = e.save_pdf(html, "tender_pack_30p.pdf", archive=e.IMG)
    for t, data in req_rows:
        truth += chart_truth(t, data, "bar")
    write_truth("tender_pack_30p.pdf", truth)
    print("tender pages", len(fitz.open(p)), flush=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    e.IMG.mkdir(exist_ok=True)
    if "--only100" in sys.argv:
        group_report_100p()
        return
    operations_report()
    tender_pack()


if __name__ == "__main__":
    main()
