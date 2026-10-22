"""Builds a corpus of industrial-style documents WITH a known correct answer for each (<file>.truth.md).

    python scripts/make_industrial_corpus.py        # writes eval/industrial/

The documents are synthetic (invoices, bank statements, contracts, forms, scans, receipts, ...), so the truth is exact.
Synthetic is not the same as real: scans are simulated with skew, noise and blur; "handwriting" is a handwriting-style font.
"""
from __future__ import annotations

import io
import json
import random
import sys
from pathlib import Path

import cv2
import fitz
import matplotlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "eval" / "industrial"
FONTS = Path("C:/Windows/Fonts")
random.seed(7)
np.random.seed(7)

CSS = ("body{font-family:sans-serif;font-size:10pt} h1{font-size:20pt} h2{font-size:14pt} h3{font-size:11pt} "
       "table{border-collapse:collapse;width:100%} td,th{border:1px solid #444;padding:3px;font-size:9pt} th{background:#ddd}")


# ----------------------------------------------------------------------------- helpers
def md_table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def html_table(headers: list[str], rows: list[list], right: tuple = ()) -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f'<td{" style=\"text-align:right\"" if i in right else ""}>{c}</td>' for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f"<table><tr>{th}</tr>{body}</table>"


def save_pdf_from_html(html: str, name: str, landscape: bool = False, css: str = CSS, archive: Path | None = None) -> Path:
    path = OUT / name
    story = fitz.Story(html=html, user_css=css, archive=fitz.Archive(str(archive)) if archive else None)
    mediabox = fitz.paper_rect("a4-l" if landscape else "a4")
    where = mediabox + (45, 45, -45, -45)
    writer = fitz.DocumentWriter(str(path))
    more = 1
    while more:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()
    return path


def truth(name: str, text: str) -> None:
    (OUT / f"{name}.truth.md").write_text(text.strip() + "\n", encoding="utf-8")


def pdf_page_png(pdf: Path, page: int = 0, dpi: int = 200) -> Image.Image:
    d = fitz.open(pdf)
    pix = d[page].get_pixmap(dpi=dpi)
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


def images_to_pdf(images: list[Image.Image], path: Path, jpeg_quality: int = 70) -> None:
    doc = fitz.open()
    for im in images:
        buf = io.BytesIO()
        im.convert("RGB").save(buf, "JPEG", quality=jpeg_quality)
        page = doc.new_page(width=595, height=842)
        page.insert_image(page.rect, stream=buf.getvalue())
    doc.save(path)


def degrade(im: Image.Image, angle=0.0, noise=0.0, blur=0.0, contrast=1.0, scale=1.0) -> Image.Image:
    if scale != 1.0:
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    if angle:
        im = im.rotate(angle, expand=True, fillcolor=(235, 235, 235), resample=Image.BICUBIC)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(im).astype(np.float32)
    if contrast != 1.0:
        a = 128 + (a - 128) * contrast
    if noise:
        a += np.random.normal(0, noise, a.shape)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ----------------------------------------------------------------------------- shared content
ITEMS = [("Hydraulic pump HP-220", 4, 1250.00), ("Pressure valve PV-8", 12, 86.50), ("Steel flange 6in", 30, 24.75),
         ("Seal kit SK-14", 25, 18.20), ("Control cable 10m", 8, 142.00), ("Gasket set GS-3", 40, 6.35)]


def money(x: float) -> str:
    return f"{x:,.2f}"


def invoice_parts():
    rows = [[d, q, money(p), money(q * p)] for d, q, p in ITEMS]
    sub = sum(q * p for _, q, p in ITEMS)
    tax = round(sub * 0.18, 2)
    return rows, sub, tax, sub + tax


def invoice_html() -> str:
    rows, sub, tax, total = invoice_parts()
    return (f"<h1>INVOICE</h1><p><b>Northwind Industrial Supplies Pvt Ltd</b><br>14 Foundry Road, Pune 411019</p>"
            f"<p>Invoice No: INV-2026-0417<br>Invoice Date: 14 March 2026<br>Due Date: 13 April 2026</p>"
            f"<p><b>Bill To:</b> Apex Machinery Works, Plot 8, MIDC Chakan, Pune</p>"
            + html_table(["Description", "Qty", "Unit price", "Amount"], rows, right=(1, 2, 3)) +
            f"<p>Subtotal: {money(sub)}<br>GST 18%: {money(tax)}<br><b>Total Due: {money(total)}</b></p>"
            f"<p>Payment terms: net 30 days. Bank: First Industrial Bank, A/C 004455667788.</p>")


def invoice_truth() -> str:
    rows, sub, tax, total = invoice_parts()
    return ("# INVOICE\n\nNorthwind Industrial Supplies Pvt Ltd\n14 Foundry Road, Pune 411019\n\n"
            "Invoice No: INV-2026-0417\nInvoice Date: 14 March 2026\nDue Date: 13 April 2026\n\n"
            "Bill To: Apex Machinery Works, Plot 8, MIDC Chakan, Pune\n\n"
            + md_table(["Description", "Qty", "Unit price", "Amount"], rows) +
            f"\n\nSubtotal: {money(sub)}\nGST 18%: {money(tax)}\nTotal Due: {money(total)}\n\n"
            "Payment terms: net 30 days. Bank: First Industrial Bank, A/C 004455667788.")


# ----------------------------------------------------------------------------- digital PDFs
def make_digital() -> None:
    save_pdf_from_html(invoice_html(), "invoice.pdf")
    truth("invoice.pdf", invoice_truth())

    # purchase order
    po_rows = [[f"PRT-{1000 + i}", d, q, "pcs", money(p)] for i, (d, q, p) in enumerate(ITEMS)]
    html = ("<h1>PURCHASE ORDER</h1><p>PO Number: PO-77821<br>Vendor: Northwind Industrial Supplies Pvt Ltd<br>"
            "Ship To: Apex Machinery Works, Chakan Plant 2<br>Required by: 30 April 2026</p>"
            + html_table(["Part no", "Description", "Qty", "Unit", "Unit price"], po_rows, right=(2, 4)) +
            "<h2>Terms</h2><p>Delivery must be made on pallets with the PO number on every carton. Late delivery attracts a penalty of 0.5 percent per week. "
            "Goods are subject to inspection within 7 days of receipt.</p>")
    save_pdf_from_html(html, "purchase_order.pdf")
    truth("purchase_order.pdf", "# PURCHASE ORDER\n\nPO Number: PO-77821\nVendor: Northwind Industrial Supplies Pvt Ltd\nShip To: Apex Machinery Works, Chakan Plant 2\n"
          "Required by: 30 April 2026\n\n" + md_table(["Part no", "Description", "Qty", "Unit", "Unit price"], po_rows) +
          "\n\n## Terms\n\nDelivery must be made on pallets with the PO number on every carton. Late delivery attracts a penalty of 0.5 percent per week. "
          "Goods are subject to inspection within 7 days of receipt.")

    # bank statement, 3 pages
    bal, tx = 250000.00, []
    for i in range(70):
        d = f"{1 + i // 3:02d}/03/2026"
        if i % 3 == 0:
            cr, db = random.randint(5, 90) * 100.0, 0.0
        else:
            cr, db = 0.0, random.randint(2, 60) * 50.0
        bal += cr - db
        tx.append([d, f"{random.choice(['NEFT','UPI','POS','CHQ','ATM'])} {random.randint(100000, 999999)} {random.choice(['Acme','Globex','Initech','Hooli','Vandelay'])}",
                   money(db) if db else "", money(cr) if cr else "", money(bal)])
    html = "<h1>Account Statement</h1><p>Account: 004455667788 | Period: 01 Mar 2026 to 31 Mar 2026 | Opening balance 250,000.00</p>" + html_table(["Date", "Description", "Debit", "Credit", "Balance"], tx, right=(2, 3, 4))
    save_pdf_from_html(html, "bank_statement.pdf")
    truth("bank_statement.pdf", "# Account Statement\n\nAccount: 004455667788 | Period: 01 Mar 2026 to 31 Mar 2026 | Opening balance 250,000.00\n\n" + md_table(["Date", "Description", "Debit", "Credit", "Balance"], tx))

    # balance sheet (nested rows, negatives in brackets)
    bs = [["Assets", "", ""], ["Cash and equivalents", "12,450", "9,870"], ["Trade receivables", "34,120", "29,880"], ["Inventory", "21,300", "24,100"],
          ["Property, plant and equipment", "88,900", "84,250"], ["Total assets", "156,770", "148,100"],
          ["Liabilities", "", ""], ["Trade payables", "(18,440)", "(16,720)"], ["Long-term debt", "(45,000)", "(50,000)"], ["Total liabilities", "(63,440)", "(66,720)"],
          ["Equity", "", ""], ["Retained earnings", "93,330", "81,380"]]
    html = "<h1>Consolidated Balance Sheet</h1><p>As at 31 March 2026, in thousands of rupees</p>" + html_table(["Item", "2026", "2025"], bs, right=(1, 2))
    save_pdf_from_html(html, "balance_sheet.pdf")
    truth("balance_sheet.pdf", "# Consolidated Balance Sheet\n\nAs at 31 March 2026, in thousands of rupees\n\n" + md_table(["Item", "2026", "2025"], bs))

    # contract
    clauses = [("Definitions", "In this Agreement the Supplier means Northwind Industrial Supplies Pvt Ltd and the Buyer means Apex Machinery Works."),
               ("Term", "This Agreement starts on 1 April 2026 and continues for twenty four months unless terminated earlier under clause 9."),
               ("Supply", "The Supplier shall deliver the goods listed in each purchase order within the agreed lead time."),
               ("Price", "Prices are fixed for the first twelve months and may then be revised by up to five percent."),
               ("Payment", "The Buyer shall pay each undisputed invoice within thirty days of receipt."),
               ("Warranty", "The Supplier warrants that the goods are free from defects for a period of eighteen months."),
               ("Liability", "Neither party is liable for indirect or consequential loss arising from this Agreement."),
               ("Confidentiality", "Each party shall keep the terms of this Agreement and all technical information confidential."),
               ("Termination", "Either party may terminate this Agreement by giving ninety days written notice."),
               ("Governing law", "This Agreement is governed by the laws of India and the courts of Pune have exclusive jurisdiction.")]
    html = "<h1>SUPPLY AGREEMENT</h1><p>This Supply Agreement is made on 1 April 2026 between the parties named below.</p>" + "".join(f"<h2>{i}. {t}</h2><p>{b}</p>" for i, (t, b) in enumerate(clauses, 1)) + "<p>Signed for the Supplier: ____________ Signed for the Buyer: ____________</p>"
    save_pdf_from_html(html, "contract.pdf")
    truth("contract.pdf", "# SUPPLY AGREEMENT\n\nThis Supply Agreement is made on 1 April 2026 between the parties named below.\n\n" + "\n\n".join(f"## {i}. {t}\n\n{b}" for i, (t, b) in enumerate(clauses, 1)) + "\n\nSigned for the Supplier: ____________ Signed for the Buyer: ____________")

    # two-column paper
    left = ("Condition monitoring of rotating machinery relies on vibration signals. In this study we compare three feature sets on a bearing fault data set. "
            "The first feature set uses time domain statistics such as root mean square and kurtosis. The second uses spectral band energies.")
    right = ("The third feature set combines both with envelope analysis. A random forest classifier achieved the best accuracy on the held out test set. "
             "Results are summarised in Table 1. We conclude that combined features give the most robust diagnosis across operating speeds.")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_htmlbox(fitz.Rect(40, 40, 555, 120), "<h1>Bearing Fault Diagnosis with Combined Features</h1><p><i>A. Rao and S. Iyer</i></p>", css=CSS)
    page.insert_htmlbox(fitz.Rect(40, 130, 290, 420), f"<h2>1. Introduction</h2><p>{left}</p>", css=CSS)
    page.insert_htmlbox(fitz.Rect(305, 130, 555, 420), f"<h2>2. Method and results</h2><p>{right}</p>", css=CSS)
    res = [["Time domain", "88.2"], ["Spectral", "91.5"], ["Combined", "96.3"]]
    page.insert_htmlbox(fitz.Rect(40, 430, 555, 700), "<p>Table 1. Accuracy by feature set (percent)</p>" + html_table(["Feature set", "Accuracy"], res), css=CSS)
    doc.save(OUT / "two_column_paper.pdf")
    truth("two_column_paper.pdf", f"# Bearing Fault Diagnosis with Combined Features\n\nA. Rao and S. Iyer\n\n## 1. Introduction\n\n{left}\n\n## 2. Method and results\n\n{right}\n\nTable 1. Accuracy by feature set (percent)\n\n" + md_table(["Feature set", "Accuracy"], res))

    # form with label: value pairs
    fields = [("Applicant name", "Ravi Kumar Sharma"), ("Date of birth", "12 August 1988"), ("Employee ID", "EMP-30918"), ("Department", "Quality Assurance"),
              ("Requested leave", "10 days from 5 May 2026"), ("Reason", "Family function"), ("Approving manager", "Neha Verma")]
    html = "<h1>Leave Application Form</h1>" + "".join(f"<p><b>{k}:</b> {v}</p>" for k, v in fields)
    save_pdf_from_html(html, "form_fields.pdf")
    truth("form_fields.pdf", "# Leave Application Form\n\n" + "\n".join(f"{k}: {v}" for k, v in fields))

    # lab report
    labs = [["Haemoglobin", "13.2", "g/dL", "13.0 - 17.0", ""], ["WBC count", "11.8", "x10^3/uL", "4.0 - 11.0", "High"], ["Platelets", "245", "x10^3/uL", "150 - 450", ""],
            ["Fasting glucose", "104", "mg/dL", "70 - 99", "High"], ["Creatinine", "0.9", "mg/dL", "0.7 - 1.3", ""]]
    html = "<h1>Pathology Laboratory Report</h1><p>Patient: Anil Mehta, 46 M | Sample ID: LB-558201 | Collected: 02 Feb 2026</p>" + html_table(["Test", "Result", "Unit", "Reference range", "Flag"], labs)
    save_pdf_from_html(html, "lab_report.pdf")
    truth("lab_report.pdf", "# Pathology Laboratory Report\n\nPatient: Anil Mehta, 46 M | Sample ID: LB-558201 | Collected: 02 Feb 2026\n\n" + md_table(["Test", "Result", "Unit", "Reference range", "Flag"], labs))

    # datasheet with units and symbols
    spec = [["Supply voltage", "24", "V DC"], ["Operating temperature", "-20 to 70", "°C"], ["Coil resistance", "320", "Ω"], ["Response time", "12", "ms"], ["Insulation resistance", "100", "MΩ"], ["Weight", "180", "g"]]
    html = "<h1>Relay Module RM-24 Datasheet</h1><p>General purpose control relay for industrial panels.</p><h2>Specifications</h2>" + html_table(["Parameter", "Value", "Unit"], spec) + "<h2>Notes</h2><p>Tolerance on coil resistance is ±10 percent. Do not exceed 30 V DC.</p>"
    save_pdf_from_html(html, "datasheet.pdf")
    truth("datasheet.pdf", "# Relay Module RM-24 Datasheet\n\nGeneral purpose control relay for industrial panels.\n\n## Specifications\n\n" + md_table(["Parameter", "Value", "Unit"], spec) + "\n\n## Notes\n\nTolerance on coil resistance is ±10 percent. Do not exceed 30 V DC.")

    # resume with sidebar
    doc = fitz.open()
    page = doc.new_page()
    side = "<h2>Contact</h2><p>priya.nair@example.com<br>+91 98765 43210<br>Bengaluru</p><h2>Skills</h2><p>Python<br>SQL<br>Power BI<br>Docker</p>"
    main = ("<h1>Priya Nair</h1><h3>Data Engineer</h3><h2>Experience</h2><p><b>Senior Data Engineer, Acme Analytics</b> 2022 to present. Built batch pipelines processing 2 TB daily.</p>"
            "<p><b>Data Engineer, Globex</b> 2019 to 2022. Migrated reporting to a cloud warehouse.</p><h2>Education</h2><p>B.Tech Computer Science, 2019</p>")
    page.insert_htmlbox(fitz.Rect(30, 40, 190, 500), side, css=CSS)
    page.insert_htmlbox(fitz.Rect(210, 40, 560, 500), main, css=CSS)
    doc.save(OUT / "resume.pdf")
    truth("resume.pdf", "# Priya Nair\n\nData Engineer\n\n## Experience\n\nSenior Data Engineer, Acme Analytics 2022 to present. Built batch pipelines processing 2 TB daily.\n\nData Engineer, Globex 2019 to 2022. Migrated reporting to a cloud warehouse.\n\n## Education\n\nB.Tech Computer Science, 2019\n\n## Contact\n\npriya.nair@example.com\n+91 98765 43210\nBengaluru\n\n## Skills\n\nPython\nSQL\nPower BI\nDocker")

    # multilingual
    doc = fitz.open()
    page = doc.new_page()
    hi, zh = "यह एक औद्योगिक परियोजना की मासिक रिपोर्ट है।", "本月生产线运行稳定，产量达到计划的百分之一百零二。"
    page.insert_font("hi", str(FONTS / "Nirmala.ttc"))
    page.insert_font("zh", str(FONTS / "msyh.ttc"))
    page.insert_text((50, 80), "Monthly plant report (English)", fontsize=14)
    page.insert_text((50, 110), "Production was stable and reached 102 percent of plan.", fontsize=11)
    page.insert_text((50, 160), hi, fontname="hi", fontsize=13)
    page.insert_text((50, 210), zh, fontname="zh", fontsize=13)
    doc.save(OUT / "multilingual.pdf")
    truth("multilingual.pdf", f"Monthly plant report (English)\n\nProduction was stable and reached 102 percent of plan.\n\n{hi}\n\n{zh}")

    # rotated pages
    doc = fitz.open()
    for i, rot in enumerate((0, 90, 180)):
        p = doc.new_page()
        p.insert_text((60, 100), f"Rotated page {i + 1}: inspection checklist item {i + 1} passed.", fontsize=14)
        p.set_rotation(rot)
    doc.save(OUT / "rotated_pages.pdf")
    truth("rotated_pages.pdf", "\n\n".join(f"Rotated page {i + 1}: inspection checklist item {i + 1} passed." for i in range(3)))

    # table that spans several pages
    inv = [[f"SKU-{2000 + i}", f"Item {i} bracket", random.randint(1, 500), f"Rack {random.choice('ABCDEF')}{random.randint(1, 20)}"] for i in range(130)]
    save_pdf_from_html("<h1>Warehouse Inventory</h1>" + html_table(["SKU", "Description", "Stock", "Location"], inv, right=(2,)), "multipage_table.pdf")
    truth("multipage_table.pdf", "# Warehouse Inventory\n\n" + md_table(["SKU", "Description", "Stock", "Location"], inv))

    # long document (60 pages)
    words = "the plant process quality shift output maintenance line safety audit supplier delivery control sensor schedule report".split()
    secs, tparts = [], []
    for i in range(1, 41):
        para = " ".join(random.choice(words) for _ in range(160)) + "."
        secs.append(f"<h2>Section {i}</h2><p>{para}</p><p>{para[::-1][:0]}{' '.join(random.choice(words) for _ in range(160))}.</p>")
        tparts.append((i, para))
    save_pdf_from_html("<h1>Annual Operations Review</h1>" + "".join(secs), "long_report.pdf")
    # long truth is approximate by construction (second paragraph regenerated); scored on structure only, see runner
    (OUT / "long_report.pdf.truth.md").write_text("# Annual Operations Review\n\n" + "\n\n".join(f"## Section {i}" for i in range(1, 41)) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------- charts and slides
def chart_png(kind: str) -> bytes:
    fig, ax = plt.subplots(figsize=(5, 3))
    if kind == "bar":
        ax.bar(["Q1", "Q2", "Q3", "Q4"], [120, 150, 200, 310])
        for i, v in enumerate([120, 150, 200, 310]):
            ax.text(i, v + 5, str(v), ha="center")
        ax.set_title("Revenue by quarter (USD m)")
    elif kind == "pie":
        ax.pie([45, 30, 25], labels=["Pumps 45%", "Valves 30%", "Seals 25%"])
        ax.set_title("Sales mix")
    else:
        ax.plot([2021, 2022, 2023, 2024], [12, 18, 30, 52], marker="o")
        for x, y in zip([2021, 2022, 2023, 2024], [12, 18, 30, 52]):
            ax.annotate(str(y), (x, y), textcoords="offset points", xytext=(0, 6), ha="center")
        ax.set_title("Profit by year (USD m)")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def make_charts() -> None:
    d = OUT / "_img"
    d.mkdir(exist_ok=True)
    for k in ("bar", "pie", "line"):
        (d / f"{k}.png").write_bytes(chart_png(k))
    html = ("<h1>Quarterly Performance Report</h1><p>Revenue grew every quarter.</p><img src='bar.png' width='360'><p>Figure 1. Revenue by quarter.</p>"
            "<p style='page-break-before:always'></p><img src='pie.png' width='300'><p>Figure 2. Sales mix by product.</p><img src='line.png' width='360'><p>Figure 3. Profit by year.</p>"
            + html_table(["Quarter", "Revenue"], [["Q1", 120], ["Q2", 150], ["Q3", 200], ["Q4", 310]]))
    save_pdf_from_html(html, "chart_report.pdf", archive=d)
    truth("chart_report.pdf", "# Quarterly Performance Report\n\nRevenue grew every quarter.\n\nFigure 1. Revenue by quarter.\n\nFigure 2. Sales mix by product.\n\nFigure 3. Profit by year.\n\n"
          + md_table(["Quarter", "Revenue"], [["Q1", 120], ["Q2", 150], ["Q3", 200], ["Q4", 310]])
          + "\n\n## Bar chart: Revenue by quarter\n\n| Quarter | Revenue |\n|---|---|\n| Q1 | 120 |\n| Q2 | 150 |\n| Q3 | 200 |\n| Q4 | 310 |\n\n"
          "## Pie chart: Sales mix\n\n| Product | Share |\n|---|---|\n| Pumps | 45 |\n| Valves | 30 |\n| Seals | 25 |\n\n"
          "## Line chart: Profit\n\n| Year | Profit |\n|---|---|\n| 2021 | 12 |\n| 2022 | 18 |\n| 2023 | 30 |\n| 2024 | 52 |")

    # slides exported to PDF (landscape)
    html = ("<h1>Plant Review Q4</h1><p>Operations team</p><h1>Highlights</h1><ul><li>Output up 12 percent</li><li>Scrap down to 1.4 percent</li><li>Two new suppliers qualified</li></ul>"
            "<h1>Cost summary</h1>" + html_table(["Area", "Budget", "Actual"], [["Energy", 90, 84], ["Labour", 210, 215], ["Maintenance", 60, 71]]) + "<h1>Revenue trend</h1><img src='bar.png' width='420'>")
    save_pdf_from_html(html, "slides.pdf", landscape=True, archive=d)
    truth("slides.pdf", "# Plant Review Q4\n\nOperations team\n\n# Highlights\n\n- Output up 12 percent\n- Scrap down to 1.4 percent\n- Two new suppliers qualified\n\n# Cost summary\n\n"
          + md_table(["Area", "Budget", "Actual"], [["Energy", 90, 84], ["Labour", 210, 215], ["Maintenance", 60, 71]]) + "\n\n# Revenue trend")


# ----------------------------------------------------------------------------- scans and photos
def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def make_scans() -> None:
    base = pdf_page_png(OUT / "invoice.pdf", 0, dpi=200)
    images_to_pdf([base], OUT / "scanned_invoice_clean.pdf", 85)
    truth("scanned_invoice_clean.pdf", invoice_truth())
    images_to_pdf([degrade(base, angle=2.5, noise=14, blur=0.8)], OUT / "scanned_invoice_skewed_noisy.pdf", 55)
    truth("scanned_invoice_skewed_noisy.pdf", invoice_truth())
    images_to_pdf([degrade(base, angle=-1.2, noise=22, blur=2.0, contrast=0.6, scale=0.45)], OUT / "scanned_invoice_low_quality.pdf", 35)
    truth("scanned_invoice_low_quality.pdf", invoice_truth())

    # mixed: page 1 digital, page 2 scanned
    d = fitz.open()
    d.insert_pdf(fitz.open(OUT / "contract.pdf"), from_page=0, to_page=0)
    buf = io.BytesIO()
    degrade(base, angle=1.0, noise=10).save(buf, "JPEG", quality=70)
    p = d.new_page(width=595, height=842)
    p.insert_image(p.rect, stream=buf.getvalue())
    d.save(OUT / "mixed_digital_scanned.pdf")
    first_page_truth = "# SUPPLY AGREEMENT\n\nThis Supply Agreement is made on 1 April 2026 between the parties named below."
    truth("mixed_digital_scanned.pdf", first_page_truth + "\n\n" + invoice_truth())

    # receipt photo: narrow mono text, perspective + vignette
    lines = ["FRESH MART", "Store 118, MG Road", "Date 03/04/2026 18:42", "------------------------", "Rice 5kg          310.00", "Milk 2L            118.00", "Soap x3             96.00", "Tea 500g          245.00",
             "------------------------", "TOTAL             769.00", "GST incl           36.62", "Paid by UPI", "Thank you, visit again"]
    im = Image.new("RGB", (420, 640), (250, 250, 245))
    dr = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        dr.text((24, 30 + i * 40), l, font=font("consola.ttf", 22), fill=(25, 25, 25))
    a = np.asarray(im)
    h, w = a.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[18, 12], [w - 6, 0], [w - 24, h - 10], [4, h - 2]])
    warped = cv2.warpPerspective(a, cv2.getPerspectiveTransform(src, dst), (w, h), borderValue=(60, 60, 60))
    yy, xx = np.mgrid[0:h, 0:w]
    vign = 1 - 0.45 * (((xx - w / 2) / w) ** 2 + ((yy - h / 2) / h) ** 2) * 2
    warped = np.clip(warped * vign[..., None] + np.random.normal(0, 6, warped.shape), 0, 255).astype(np.uint8)
    Image.fromarray(warped).rotate(3, expand=True, fillcolor=(70, 70, 70)).save(OUT / "receipt_photo.jpg", quality=72)
    truth("receipt_photo.jpg", "\n".join(lines))

    # ID card
    card = Image.new("RGB", (860, 540), (225, 238, 250))
    dr = ImageDraw.Draw(card)
    dr.rectangle([0, 0, 860, 70], fill=(30, 70, 140))
    dr.text((24, 18), "REPUBLIC OF EXAMPLE  NATIONAL ID CARD", font=font("arialbd.ttf", 30), fill="white")
    dr.rectangle([30, 110, 240, 380], fill=(170, 170, 170))
    idf = [("Name", "ARJUN MEHTA"), ("Date of birth", "04 JUN 1990"), ("ID number", "7731 2290 5518"), ("Address", "22 Lake View, Pune 411001"), ("Valid until", "31 DEC 2034")]
    for i, (k, v) in enumerate(idf):
        dr.text((280, 110 + i * 62), k, font=font("arial.ttf", 20), fill=(70, 70, 70))
        dr.text((280, 134 + i * 62), v, font=font("arialbd.ttf", 28), fill=(10, 10, 10))
    card.save(OUT / "id_card.png")
    truth("id_card.png", "REPUBLIC OF EXAMPLE NATIONAL ID CARD\n\n" + "\n".join(f"{k}: {v}" for k, v in idf))

    # handwriting-style note on lined paper (simulated with a handwriting font)
    note = ["Check pump P-4 bearing noise", "Replace filter before Friday", "Call vendor about delayed valves", "Shift handover at 6 pm"]
    paper = Image.new("RGB", (900, 420), (252, 250, 238))
    dr = ImageDraw.Draw(paper)
    for y in range(70, 420, 70):
        dr.line([(30, y), (870, y)], fill=(170, 190, 220), width=2)
    for i, l in enumerate(note):
        dr.text((50 + random.randint(-4, 4), 25 + i * 70 + random.randint(-3, 3)), l, font=font("Inkfree.ttf", 38), fill=(25, 35, 120))
    degrade(paper, angle=-1.0, noise=6).save(OUT / "handwritten_note.png")
    truth("handwritten_note.png", "\n".join(note))

    # screenshot of an application
    shot = Image.new("RGB", (1000, 560), (240, 240, 240))
    dr = ImageDraw.Draw(shot)
    dr.rectangle([0, 0, 1000, 36], fill=(45, 45, 60))
    dr.text((12, 8), "Maintenance Console - Plant 2", font=font("arial.ttf", 18), fill="white")
    for i, m in enumerate(["File", "Edit", "View", "Reports", "Help"]):
        dr.text((16 + i * 90, 50), m, font=font("arial.ttf", 18), fill=(20, 20, 20))
    rows = [("Pump P-4", "Running", "72 C"), ("Pump P-5", "Stopped", "31 C"), ("Valve V-12", "Open", "45 C"), ("Fan F-2", "Fault E31", "88 C")]
    dr.text((30, 110), "Asset        Status        Temperature", font=font("consola.ttf", 20), fill=(0, 0, 0))
    for i, (a_, s_, t_) in enumerate(rows):
        dr.text((30, 150 + i * 36), f"{a_:<13}{s_:<14}{t_}", font=font("consola.ttf", 20), fill=(0, 0, 0))
    dr.rectangle([30, 340, 190, 385], fill=(40, 110, 200))
    dr.text((55, 352), "Acknowledge", font=font("arial.ttf", 18), fill="white")
    shot.save(OUT / "screenshot.png")
    truth("screenshot.png", "Maintenance Console - Plant 2\n\nFile Edit View Reports Help\n\nAsset Status Temperature\n" + "\n".join(f"{a_} {s_} {t_}" for a_, s_, t_ in rows) + "\n\nAcknowledge")

    # a picture with no text at all
    pic = np.zeros((400, 600, 3), np.uint8)
    for x in range(600):
        pic[:, x] = (x * 255 // 600, 120, 255 - x * 255 // 600)
    cv2.circle(pic, (300, 200), 90, (255, 255, 255), -1)
    Image.fromarray(pic).save(OUT / "photo_no_text.jpg")


# ----------------------------------------------------------------------------- office and data files
def make_office() -> None:
    from docx import Document
    from docx.shared import Inches
    from openpyxl import Workbook  # noqa: F401  (kept for parity; xlsx written with xlsxwriter below)
    import xlsxwriter
    from pptx import Presentation
    from pptx.util import Inches as PI

    d = OUT / "_img"
    doc = Document()
    doc.sections[0].header.paragraphs[0].text = "Confidential - Plant Safety Procedure"
    doc.add_heading("Hot Work Safety Procedure", 0)
    doc.add_heading("1. Purpose", 1)
    doc.add_paragraph("This procedure sets out the controls required before any welding or cutting is carried out.")
    doc.add_heading("2. Requirements", 1)
    for t in ("Obtain a hot work permit", "Remove flammable material within 10 metres", "Keep a fire extinguisher at the work area"):
        doc.add_paragraph(t, style="List Bullet")
    doc.add_heading("3. Steps", 1)
    for t in ("Inspect the area", "Issue the permit", "Monitor for 30 minutes after work"):
        doc.add_paragraph(t, style="List Number")
    tbl = doc.add_table(rows=3, cols=3)
    tbl.style = "Table Grid"
    tbl.cell(0, 0).merge(tbl.cell(0, 2)).text = "Permit register"
    for j, h in enumerate(["Permit", "Area", "Status"]):
        tbl.cell(1, j).text = h
    for j, v in enumerate(["HW-101", "Workshop 3", "Closed"]):
        tbl.cell(2, j).text = v
    doc.add_picture(str(d / "bar.png"), width=Inches(3.5))
    doc.save(OUT / "procedure.docx")
    truth("procedure.docx", "# Hot Work Safety Procedure\n\n## 1. Purpose\n\nThis procedure sets out the controls required before any welding or cutting is carried out.\n\n## 2. Requirements\n\n- Obtain a hot work permit\n- Remove flammable material within 10 metres\n- Keep a fire extinguisher at the work area\n\n"
          "## 3. Steps\n\n1. Inspect the area\n2. Issue the permit\n3. Monitor for 30 minutes after work\n\nPermit register\n\n| Permit | Area | Status |\n|---|---|---|\n| HW-101 | Workshop 3 | Closed |")

    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[0])
    s.shapes.title.text, s.placeholders[1].text = "Maintenance Review", "Plant 2 - Q1 2026"
    s = prs.slides.add_slide(prs.slide_layouts[1])
    s.shapes.title.text = "Key points"
    s.placeholders[1].text_frame.text = "Downtime fell by 18 percent"
    for t in ("Predictive alerts introduced", "Spare parts stock reviewed"):
        s.placeholders[1].text_frame.add_paragraph().text = t
    s.notes_slide.notes_text_frame.text = "Speaker note: mention the new vibration sensors."
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = "Downtime by line"
    gt = s.shapes.add_table(3, 2, PI(1), PI(2), PI(6), PI(1.5)).table
    for i, row in enumerate([["Line", "Hours"], ["Line A", "14"], ["Line B", "9"]]):
        for j, v in enumerate(row):
            gt.cell(i, j).text = v
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = "Revenue by quarter"
    s.shapes.add_picture(str(d / "bar.png"), PI(1.5), PI(1.8), width=PI(6))
    prs.save(OUT / "slides.pptx")
    truth("slides.pptx", "# Maintenance Review\n\nPlant 2 - Q1 2026\n\n# Key points\n\n- Downtime fell by 18 percent\n- Predictive alerts introduced\n- Spare parts stock reviewed\n\nSpeaker note: mention the new vibration sensors.\n\n# Downtime by line\n\n| Line | Hours |\n|---|---|\n| Line A | 14 |\n| Line B | 9 |\n\n# Revenue by quarter")

    wb = xlsxwriter.Workbook(str(OUT / "multi_sheet.xlsx"))
    bold = wb.add_format({"bold": True})
    datef = wb.add_format({"num_format": "dd-mmm-yyyy"})
    ws = wb.add_worksheet("Sales")
    ws.merge_range("A1:E1", "Sales Q1 2026", bold)
    for j, h in enumerate(["Date", "Product", "Units", "Price", "Revenue"]):
        ws.write(1, j, h, bold)
    sales = [("2026-01-05", "Pump", 4, 1250), ("2026-01-19", "Valve", 12, 86.5), ("2026-02-02", "Seal", 25, 18.2), ("2026-02-23", "Cable", 8, 142), ("2026-03-09", "Gasket", 40, 6.35)]
    import datetime as dt
    for i, (d_, p_, u, pr) in enumerate(sales):
        r = 2 + i
        ws.write_datetime(r, 0, dt.datetime.strptime(d_, "%Y-%m-%d"), datef)
        ws.write(r, 1, p_)
        ws.write(r, 2, u)
        ws.write(r, 3, pr)
        ws.write_formula(r, 4, f"=C{r + 1}*D{r + 1}", None, u * pr)
    ws2 = wb.add_worksheet("Costs")
    for j, h in enumerate(["Item", "Cost"]):
        ws2.write(0, j, h, bold)
    costs = [("Raw material", 5200), ("Labour", 3100), ("Freight", 780)]
    for i, (k, v) in enumerate(costs):
        ws2.write(1 + i, 0, k)
        ws2.write(1 + i, 1, v)
    ws3 = wb.add_worksheet("Notes")
    ws3.write(0, 0, "Figures exclude tax. Prepared by finance.")
    wb.close()

    def fmt(x):
        return f"{x:g}"
    t = "# Sales Q1 2026\n\n| Date | Product | Units | Price | Revenue |\n|---|---|---|---|---|\n"
    for d_, p_, u, pr in sales:
        t += f"| {dt.datetime.strptime(d_, '%Y-%m-%d').strftime('%d-%b-%Y')} | {p_} | {u} | {fmt(pr)} | {fmt(u * pr)} |\n"
    t += "\n# Costs\n\n| Item | Cost |\n|---|---|\n" + "".join(f"| {k} | {v} |\n" for k, v in costs) + "\n# Notes\n\nFigures exclude tax. Prepared by finance."
    truth("multi_sheet.xlsx", t)

    rows = [[i, f'"Bracket, type {i % 7}"', random.randint(10, 999), f"{random.randint(100, 9999) / 100:.2f}"] for i in range(1, 301)]
    csv = "\ufeffid,description,qty,price\n" + "\n".join(f'{r[0]},{r[1]},{r[2]},{r[3]}' for r in rows)
    (OUT / "parts.csv").write_text(csv, encoding="utf-8")
    truth("parts.csv", md_table(["id", "description", "qty", "price"], [[r[0], r[1].strip('"'), r[2], r[3]] for r in rows]))
    (OUT / "parts.tsv").write_text("id\tdescription\tqty\n" + "\n".join(f"{r[0]}\tBracket type {r[0] % 7}\t{r[2]}" for r in rows[:50]), encoding="utf-8")
    truth("parts.tsv", md_table(["id", "description", "qty"], [[r[0], f"Bracket type {r[0] % 7}", r[2]] for r in rows[:50]]))


def make_textual_and_edge() -> None:
    notes = "Shift notes 03 April\nLine 2 stopped for 20 minutes due to a sensor fault.\nSpare sensor fitted. Line restarted at 14:10.\nNo safety incidents."
    (OUT / "shift_notes.txt").write_text(notes, encoding="utf-8")
    truth("shift_notes.txt", notes)
    md = "# Runbook\n\n## Restart the line\n\n1. Clear the alarm\n2. Press start\n\n| Step | Owner |\n|---|---|\n| Clear alarm | Operator |"
    (OUT / "runbook.md").write_text(md, encoding="utf-8")
    truth("runbook.md", md)
    log = "\n".join(f"2026-04-03 14:{i:02d}:11 INFO sensor_{i % 4} reading={20 + i % 9}.{i % 10}" for i in range(40))
    (OUT / "machine.log").write_text(log, encoding="utf-8")
    truth("machine.log", log)
    # formats the app does not list as supported: expected to be refused cleanly
    (OUT / "config.json").write_text(json.dumps({"plant": "Pune-2", "lines": [{"id": "A", "rate": 120}, {"id": "B", "rate": 95}]}, indent=2), encoding="utf-8")
    (OUT / "report.html").write_text("<html><body><h1>Daily report</h1><p>Output 1,240 units.</p><table><tr><th>Line</th><th>Units</th></tr><tr><td>A</td><td>640</td></tr></table></body></html>", encoding="utf-8")
    (OUT / "data.xml").write_text("<plant><line id='A'><rate>120</rate></line><line id='B'><rate>95</rate></line></plant>", encoding="utf-8")
    (OUT / "message.eml").write_text("From: ops@example.com\nTo: plant@example.com\nSubject: Line 2 downtime\nContent-Type: text/plain\n\nLine 2 was down for 20 minutes today.\n", encoding="utf-8")
    (OUT / "legacy_report.doc").write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 600)
    (OUT / "legacy_sheet.xls").write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 600)

    # robustness: password protected, truncated, blank
    src = fitz.open(OUT / "invoice.pdf")
    src.save(OUT / "protected.pdf", encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="secret", owner_pw="owner")
    raw = (OUT / "invoice.pdf").read_bytes()
    (OUT / "corrupted.pdf").write_bytes(raw[: int(len(raw) * 0.55)])
    blank = fitz.open()
    blank.new_page()
    blank.save(OUT / "blank.pdf")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_img").mkdir(exist_ok=True)
    for step in (make_digital, make_charts, make_scans, make_office, make_textual_and_edge):
        step()
        print("done", step.__name__)
    n = len([p for p in OUT.iterdir() if p.is_file() and not p.name.endswith(".truth.md")])
    print(f"{n} documents written to {OUT}")


if __name__ == "__main__":
    sys.exit(main())
