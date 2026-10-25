"""Documents with many pages, written to eval/long/ with an exact answer file for each.

    python scripts/make_long_docs.py

annual_report_60p.pdf      60 pages: headings, paragraphs, a table on every page, a chart every sixth page (10 charts)
transaction_ledger_100p.pdf 100 pages: one table of 2,500 rows, the header repeated on every page
contract_45p.pdf           45 pages of nested clauses with a header and a page number on every page
scanned_report_30p.pdf     30 pages that are only photos of pages (no text layer): tilt, noise, blur
handbook_40p.docx          Word, 40 sections each starting on a new page, a table in each
big_workbook.xlsx          Excel, 5 sheets x 300 rows with formulas
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
LONG = ROOT / "eval" / "long"
e.ENT = LONG
e.IMG = LONG / "_img"
neg, rows_md, write_truth, save_pdf, stamp_pages = e.neg, e.rows_md, e.write_truth, e.save_pdf, e.stamp_pages
WORDS = ("plant output quality safety supplier delivery maintenance audit energy sensor schedule customer inventory training budget risk control process review "
         "capacity demand cost margin contract payment vendor shipment warehouse compliance policy target growth region product service report").split()


def para(rnd: random.Random, n: int = 110) -> str:
    w = [rnd.choice(WORDS) for _ in range(n)]
    w[0] = w[0].capitalize()
    return " ".join(w) + "."


def r1_annual() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rnd = random.Random(61)
    LONG.mkdir(parents=True, exist_ok=True)
    e.IMG.mkdir(exist_ok=True)
    html, truth, charts = "<h1>Northstar Industries Annual Report 2026</h1><p>Contents are listed by section number.</p>", "# Northstar Industries Annual Report 2026\n\nContents are listed by section number.\n\n", []
    for s in range(1, 56):
        title = f"Section {s}: {rnd.choice(['Safety', 'Quality', 'Delivery', 'Cost', 'People', 'Energy', 'Suppliers', 'Customers', 'Projects', 'Risks'])} review"
        p1, p2 = para(rnd), para(rnd, 90)
        rows = [[f"{title.split(': ')[1]} metric {k}", rnd.randint(100, 9999), f"{rnd.randint(1, 99)}.{rnd.randint(0, 9)}%", rnd.choice(["On track", "Watch", "Action"])] for k in range(1, 6)]
        html += f"<p style='page-break-before:always'></p><h2>{title}</h2><p>{p1}</p><p>{p2}</p>" + m.html_table(["Metric", "Value", "Change", "Status"], rows, right=(1, 2))
        truth += f"## {title}\n\n{p1}\n\n{p2}\n\n" + rows_md([["Metric", "Value", "Change", "Status"]] + rows) + "\n\n"
        if s % 6 == 0:
            vals = [rnd.randint(40, 400) for _ in range(4)]
            fig, ax = plt.subplots(figsize=(5, 2.8))
            ax.bar(["Q1", "Q2", "Q3", "Q4"], vals, color="#2c7fb8")
            for i, v in enumerate(vals):
                ax.text(i, v + 5, str(v), ha="center", fontsize=8)
            ax.set_title(f"Output index, section {s}")
            ax.set_ylim(0, max(vals) * 1.2)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=110)
            plt.close(fig)
            (e.IMG / f"c{s}.png").write_bytes(buf.getvalue())
            html += f"<img src='c{s}.png' width='300'><p><small>Figure {s // 6}. Output index by quarter, section {s}.</small></p>"
            truth += f"Figure {s // 6}. Output index by quarter, section {s}.\n\n"
            charts.append((s, vals))
    p = save_pdf(html, "annual_report_60p.pdf", archive=e.IMG)
    stamp_pages(p, "Northstar Industries | Annual Report 2026", "Page {} of {}")
    n = len(fitz.open(p))
    truth += "\n".join(f"Northstar Industries | Annual Report 2026\nPage {i} of {n}" for i in range(1, n + 1)) + "\n\n"
    for s, vals in charts:
        truth += f"## Bar chart: Output index, section {s}\n\n| Quarter | Value |\n|---|---|\n" + "\n".join(f"| Q{i + 1} | {v} |" for i, v in enumerate(vals)) + "\n\n"
    write_truth("annual_report_60p.pdf", truth)
    print("annual_report_60p pages", n, flush=True)


def r2_ledger() -> None:
    rnd = random.Random(62)
    head = ["Date", "Voucher", "Narration", "Ref", "Debit", "Credit", "Balance"]
    vend = ["Apex Metals", "Globex Logistics", "Initech Services", "Hooli Software", "Vandelay Imports", "Stark Components"]
    bal, n, html, truth = 250000.0, 0, "<h1>General Ledger: Account 4401 Trade Payables</h1>", "# General Ledger: Account 4401 Trade Payables\n\n"
    for pg in range(100):
        rows = []
        for _ in range(25):
            n += 1
            deb = cred = 0.0
            if rnd.random() < 0.55:
                cred = float(rnd.randint(8, 95) * 100)
            else:
                deb = float(rnd.randint(5, 60) * 100)
            bal += cred - deb
            rows.append([f"{1 + n % 28:02d}/{1 + pg % 12:02d}/2026", f"JV{2600 + n}", f"{rnd.choice(vend)} invoice {rnd.randint(1000, 9999)}", f"REF{rnd.randint(100, 999)}", neg(deb) if deb else "", neg(cred) if cred else "", neg(bal)])
        html += ("<p style='page-break-before:always'></p>" if pg else "") + m.html_table(head, rows, right=(4, 5, 6))
        truth += rows_md([head] + rows) + "\n\n"
    save_pdf(html, "transaction_ledger_100p.pdf", css=e.CSS.replace("font-size:8pt", "font-size:7.5pt").replace("padding:2.5pt", "padding:1.5pt"))
    write_truth("transaction_ledger_100p.pdf", truth)
    print("ledger pages", len(fitz.open(LONG / "transaction_ledger_100p.pdf")), flush=True)


def r3_contract() -> None:
    rnd = random.Random(63)
    topics = ["Definitions", "Services", "Term", "Fees", "Payment", "Confidentiality", "Intellectual property", "Warranties", "Liability", "Termination", "Data protection", "General"]
    html, truth = "<h1>MASTER SERVICES AGREEMENT</h1><p>Agreement No. MA-2026-91 between Northwind Industrial Supplies Pvt Ltd and Apex Machinery Works.</p>", "# MASTER SERVICES AGREEMENT\n\nAgreement No. MA-2026-91 between Northwind Industrial Supplies Pvt Ltd and Apex Machinery Works.\n\n"
    for c in range(1, 46):
        t = f"{c}. {topics[(c - 1) % 12]}"
        html += f"<p style='page-break-before:always'></p><h2>{t}</h2>"
        truth += f"## {t}\n\n"
        for k in range(1, 5):
            body = f"{c}.{k} " + para(rnd, 55)
            html += f"<p>{body}</p>"
            truth += body + "\n\n"
            for j in range(1, 3):
                sub = f"{c}.{k}.{j} " + para(rnd, 28)
                html += f"<p style='margin-left:12pt'>{sub}</p>"
                truth += sub + "\n\n"
    p = save_pdf(html, "contract_45p.pdf")
    hdr = "CONFIDENTIAL | Master Services Agreement MA-2026-91"
    stamp_pages(p, hdr, "Page {} of {}")
    n = len(fitz.open(p))
    write_truth("contract_45p.pdf", truth + "\n".join(f"{hdr}\nPage {i} of {n}" for i in range(1, n + 1)))
    print("contract pages", n, flush=True)


def r4_scanned() -> None:
    rnd = random.Random(64)
    html, truth = "<h1>Plant Inspection Report 2026</h1>", "# Plant Inspection Report 2026\n\n"
    for s in range(1, 31):
        p1 = para(rnd, 95)
        rows = [[f"Check {s}.{k}", rnd.choice(["Pass", "Fail", "Pass"]), f"{rnd.randint(1, 99)}.{rnd.randint(0, 9)}"] for k in range(1, 5)]
        html += f"<p style='page-break-before:always'></p><h2>Inspection {s}</h2><p>{p1}</p>" + m.html_table(["Check", "Result", "Reading"], rows, right=(2,))
        truth += f"## Inspection {s}\n\n{p1}\n\n" + rows_md([["Check", "Result", "Reading"]] + rows) + "\n\n"
    src = save_pdf(html, "_scan_source.pdf")
    d = fitz.open(src)
    out = fitz.open()
    for i, pg in enumerate(d):
        im = Image.open(io.BytesIO(pg.get_pixmap(dpi=130).tobytes("png"))).convert("RGB")
        im = m.degrade(im, angle=rnd.choice([-1.2, 0.8, 1.5]), noise=12, blur=0.6)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=62)
        o = out.new_page(width=595, height=842)
        o.insert_image(o.rect, stream=buf.getvalue())
    out.save(LONG / "scanned_report_30p.pdf")
    d.close()
    src.unlink()
    write_truth("scanned_report_30p.pdf", truth)
    print("scan pages", len(out), flush=True)


def r5_handbook() -> None:
    from docx import Document

    rnd = random.Random(65)
    doc = Document()
    doc.sections[0].header.paragraphs[0].text = "Northwind Industrial Supplies | Employee Handbook"
    doc.sections[0].footer.paragraphs[0].text = "Controlled document HB-001"
    doc.add_heading("Employee Handbook", 0)
    truth = "Northwind Industrial Supplies | Employee Handbook\n\n# Employee Handbook\n\n"
    for s in range(1, 41):
        if s > 1:
            doc.add_page_break()
        doc.add_heading(f"{s}. Policy {s}", 1)
        p = para(rnd, 100)
        doc.add_paragraph(p)
        tb = doc.add_table(rows=4, cols=3)
        tb.style = "Table Grid"
        rows = [["Item", "Owner", "Days"]] + [[f"Step {s}.{k}", rnd.choice(["HR", "Finance", "Plant head"]), str(rnd.randint(1, 30))] for k in range(1, 4)]
        for i, r in enumerate(rows):
            for j, v in enumerate(r):
                tb.cell(i, j).text = v
        truth += f"## {s}. Policy {s}\n\n{p}\n\n" + rows_md(rows) + "\n\n"
    doc.save(LONG / "handbook_40p.docx")
    write_truth("handbook_40p.docx", truth + "Controlled document HB-001")


def r6_workbook() -> None:
    import xlsxwriter

    rnd = random.Random(66)
    wb = xlsxwriter.Workbook(str(LONG / "big_workbook.xlsx"))
    bold, cur = wb.add_format({"bold": True}), wb.add_format({"num_format": "#,##0.00"})
    truth = ""
    for name in ["North", "South", "East", "West", "Export"]:
        ws = wb.add_worksheet(name)
        head = ["Date", "Order", "Customer", "Units", "Price", "Revenue"]
        for j, h in enumerate(head):
            ws.write(0, j, h, bold)
        rows = [head]
        for i in range(300):
            u, pr = rnd.randint(1, 200), round(rnd.uniform(5, 500), 2)
            r = [f"2026-{1 + i % 12:02d}-{1 + i % 28:02d}", f"SO-{name[0]}{1000 + i}", rnd.choice(["Apex", "Globex", "Initech", "Hooli", "Stark"]), u, pr, round(u * pr, 2)]
            for j in range(5):
                ws.write(i + 1, j, r[j], cur if j == 4 else None)
            ws.write_formula(i + 1, 5, f"=D{i + 2}*E{i + 2}", cur, r[5])
            rows.append(r)
        truth += f"# {name}\n\n" + rows_md(rows) + "\n\n"
    wb.close()
    write_truth("big_workbook.xlsx", truth)


def main() -> None:
    LONG.mkdir(parents=True, exist_ok=True)
    e.IMG.mkdir(exist_ok=True)
    for fn in (r1_annual, r2_ledger, r3_contract, r4_scanned, r5_handbook, r6_workbook):
        fn()
        print("done", fn.__name__, flush=True)


if __name__ == "__main__":
    main()
