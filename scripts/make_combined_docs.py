"""Adds documents that mix content types (text + tables + charts + photos + diagrams) to eval/industrial, each with a truth file.

    python scripts/make_combined_docs.py

Only writes NEW files, so it is safe to run while a test run is reading the older documents.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_industrial_corpus as m  # noqa: E402  (helpers: md_table, html_table, save_pdf_from_html, truth, degrade, ...)

OUT, IMG = m.OUT, m.OUT / "_img"
IMG.mkdir(exist_ok=True)


def photo(name: str, w=560, h=320, seed=1) -> None:
    """A photo-like picture with no text: sky, plant buildings, chimneys, noise."""
    rng = np.random.default_rng(seed)
    a = np.zeros((h, w, 3), np.float32)
    for y in range(h):
        a[y, :] = (120 + y * 0.3, 170 + y * 0.2, 230 - y * 0.15)
    im = Image.fromarray(a.astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rectangle([0, int(h * 0.7), w, h], fill=(70, 90, 60))
    for x0, hh in ((40, 110), (170, 150), (330, 90), (450, 130)):
        d.rectangle([x0, int(h * 0.7) - hh, x0 + 90, int(h * 0.7)], fill=(130, 130, 140))
    d.rectangle([260, 60, 285, int(h * 0.7)], fill=(150, 80, 70))
    arr = np.asarray(im).astype(np.float32) + rng.normal(0, 7, (h, w, 3))
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(IMG / name, quality=85)


def make() -> None:
    for k in ("bar", "pie", "line"):
        if not (IMG / f"{k}.png").exists():
            (IMG / f"{k}.png").write_bytes(m.chart_png(k))
    photo("plant.jpg")
    photo("product.jpg", 420, 300, seed=5)

    kpi = [["Revenue (USD m)", "310", "200"], ["Operating margin", "14.2%", "11.8%"], ["Employees", "4,820", "4,510"], ["Plants", "3", "3"]]
    css = m.CSS
    # 1. annual report page: text + table + two charts + photo + footnote
    html = ("<h1>Annual Report 2025</h1><p>Northwind had a strong year. Revenue grew by 55 percent as demand for pumps and valves recovered, and the new Chakan plant reached full output.</p>"
            "<img src='plant.jpg' width='300'><p>Photo 1. The Chakan plant.</p><h2>Key figures</h2>" + m.html_table(["Measure", "2025", "2024"], kpi, right=(1, 2)) +
            "<img src='bar.png' width='330'><p>Figure 1. Revenue by quarter (USD m).</p><p style='page-break-before:always'></p><img src='line.png' width='330'><p>Figure 2. Profit by year (USD m).</p>"
            "<p>Note: figures are unaudited and rounded.</p>")
    m.save_pdf_from_html(html, "annual_report_page.pdf", css=css, archive=IMG)
    truth_text = ("# Annual Report 2025\n\nNorthwind had a strong year. Revenue grew by 55 percent as demand for pumps and valves recovered, and the new Chakan plant reached full output.\n\n"
                  "Photo 1. The Chakan plant.\n\n## Key figures\n\n" + m.md_table(["Measure", "2025", "2024"], kpi) +
                  "\n\nFigure 1. Revenue by quarter (USD m).\n\nFigure 2. Profit by year (USD m).\n\nNote: figures are unaudited and rounded.\n\n"
                  "## Bar chart: Revenue by quarter\n\n| Quarter | Revenue |\n|---|---|\n| Q1 | 120 |\n| Q2 | 150 |\n| Q3 | 200 |\n| Q4 | 310 |\n\n"
                  "## Line chart: Profit by year\n\n| Year | Profit |\n|---|---|\n| 2021 | 12 |\n| 2022 | 18 |\n| 2023 | 30 |\n| 2024 | 52 |")
    m.truth("annual_report_page.pdf", truth_text)

    # 2. the same page, scanned (table + charts + photo inside a picture)
    n_pages = len(fitz.open(OUT / "annual_report_page.pdf"))
    images = [m.degrade(m.pdf_page_png(OUT / "annual_report_page.pdf", i, 200), angle=1.5, noise=10, blur=0.6) for i in range(n_pages)]
    m.images_to_pdf(images, OUT / "scanned_report_page.pdf", 70)
    m.truth("scanned_report_page.pdf", truth_text)

    # 3. product brochure: two columns, product photos, bullets, spec table
    spec = [["Flow rate", "220 l/min"], ["Max pressure", "16 bar"], ["Motor power", "5.5 kW"], ["Weight", "42 kg"]]
    doc = fitz.open()
    page = doc.new_page()
    arch = fitz.Archive(str(IMG))
    page.insert_htmlbox(fitz.Rect(40, 40, 555, 110), "<h1>HP-220 Hydraulic Pump</h1><p>Built for continuous duty in demanding plants.</p>", css=css)
    page.insert_htmlbox(fitz.Rect(40, 120, 290, 520), "<img src='product.jpg' width='230'><p>Figure 1. HP-220 pump, front view.</p><h2>Features</h2><ul><li>Low noise operation</li><li>Sealed bearings</li><li>Two year warranty</li></ul>", css=css, archive=arch)
    page.insert_htmlbox(fitz.Rect(305, 120, 555, 520), "<h2>Specifications</h2>" + m.html_table(["Parameter", "Value"], spec) + "<h2>Contact</h2><p>sales@northwind.example<br>+91 20 5555 0101</p>", css=css)
    doc.save(OUT / "product_brochure.pdf")
    m.truth("product_brochure.pdf", "# HP-220 Hydraulic Pump\n\nBuilt for continuous duty in demanding plants.\n\nFigure 1. HP-220 pump, front view.\n\n## Features\n\n- Low noise operation\n- Sealed bearings\n- Two year warranty\n\n## Specifications\n\n"
                                    + m.md_table(["Parameter", "Value"], spec) + "\n\n## Contact\n\nsales@northwind.example\n+91 20 5555 0101")

    # 4. flowchart document: a process diagram drawn as a picture, with a legend table
    steps = {"Receive order": (40, 60), "Check stock": (300, 60), "Pack items": (560, 20), "Reorder stock": (560, 140), "Ship": (820, 20), "Send invoice": (1080, 20)}
    edges = [("Receive order", "Check stock"), ("Check stock", "Pack items"), ("Check stock", "Reorder stock"), ("Pack items", "Ship"), ("Ship", "Send invoice")]
    fc = Image.new("RGB", (1300, 230), "white")
    d = ImageDraw.Draw(fc)
    f = m.font("arial.ttf", 22)
    for n, (x, y) in steps.items():
        d.rectangle([x, y, x + 200, y + 70], outline="black", width=3, fill=(230, 240, 255))
        d.text((x + 100, y + 35), n, font=f, fill="black", anchor="mm")
    for a, b in edges:
        (xa, ya), (xb, yb) = steps[a], steps[b]
        d.line([(xa + 200, ya + 35), (xb, yb + 35)], fill="black", width=3)
        d.polygon([(xb, yb + 35), (xb - 14, yb + 27), (xb - 14, yb + 43)], fill="black")
    fc.save(IMG / "flow.png")
    legend = [["Receive order", "Sales"], ["Check stock", "Warehouse"], ["Ship", "Logistics"]]
    m.save_pdf_from_html("<h1>Order Fulfilment Process</h1><p>The diagram shows how an order moves through the plant.</p><img src='flow.png' width='500'><p>Figure 1. Order flow.</p><h2>Owners</h2>"
                         + m.html_table(["Step", "Owner"], legend), "flowchart_doc.pdf", css=css, archive=IMG)
    m.truth("flowchart_doc.pdf", "# Order Fulfilment Process\n\nThe diagram shows how an order moves through the plant.\n\nFigure 1. Order flow.\n\n"
            + "\n".join(f"{a} -> {b}" for a, b in edges) + "\n\n## Owners\n\n" + m.md_table(["Step", "Owner"], legend))

    # 5. infographic: big numbers, shapes and short captions inside one picture
    ig = Image.new("RGB", (800, 900), (245, 247, 252))
    d = ImageDraw.Draw(ig)
    d.text((400, 50), "PLANT 2025 AT A GLANCE", font=m.font("arialbd.ttf", 40), fill=(20, 50, 120), anchor="mm")
    cards = [("1,240", "units produced per day"), ("98.2%", "on-time delivery"), ("3", "plants across India"), ("4,820", "employees")]
    for i, (big, cap) in enumerate(cards):
        x, y = 40 + (i % 2) * 380, 130 + (i // 2) * 250
        d.rounded_rectangle([x, y, x + 340, y + 210], 24, fill=(255, 255, 255), outline=(150, 170, 220), width=3)
        d.ellipse([x + 20, y + 20, x + 80, y + 80], fill=(70, 120, 210))
        d.text((x + 170, y + 125), big, font=m.font("arialbd.ttf", 56), fill=(20, 50, 120), anchor="mm")
        d.text((x + 170, y + 180), cap, font=m.font("arial.ttf", 22), fill=(80, 80, 90), anchor="mm")
    d.text((400, 700), "Source: internal operations report", font=m.font("arial.ttf", 22), fill=(110, 110, 120), anchor="mm")
    ig.save(IMG / "infographic.png")
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(fitz.Rect(30, 30, 565, 640), filename=str(IMG / "infographic.png"))
    doc.save(OUT / "infographic.pdf")
    m.truth("infographic.pdf", "PLANT 2025 AT A GLANCE\n\n" + "\n".join(f"{b}\n{c}" for b, c in cards) + "\n\nSource: internal operations report")

    # 6. datasheet with a product photo and a dimension drawing
    dr = Image.new("RGB", (520, 300), "white")
    d = ImageDraw.Draw(dr)
    d.rectangle([90, 70, 410, 230], outline="black", width=4)
    d.line([(90, 260), (410, 260)], fill="black", width=2)
    d.text((250, 280), "120 mm", font=m.font("arial.ttf", 22), fill="black", anchor="mm")
    d.line([(450, 70), (450, 230)], fill="black", width=2)
    d.text((488, 150), "80 mm", font=m.font("arial.ttf", 22), fill="black", anchor="mm")
    d.text((250, 40), "Top view", font=m.font("arial.ttf", 22), fill="black", anchor="mm")
    dr.save(IMG / "dimension.png")
    ds = [["Model", "RM-24"], ["Supply voltage", "24 V DC"], ["Height", "35 mm"]]
    m.save_pdf_from_html("<h1>Relay Module RM-24</h1><img src='product.jpg' width='260'><p>Photo 1. RM-24 module.</p>" + m.html_table(["Parameter", "Value"], ds)
                         + "<img src='dimension.png' width='330'><p>Figure 2. Dimensions of the housing.</p>", "datasheet_with_photo.pdf", css=css, archive=IMG)
    m.truth("datasheet_with_photo.pdf", "# Relay Module RM-24\n\nPhoto 1. RM-24 module.\n\n" + m.md_table(["Parameter", "Value"], ds) + "\n\nFigure 2. Dimensions of the housing.\n\nTop view\n120 mm\n80 mm")

    # 7. Word with a table, a chart picture, a photo and captions
    from docx import Document
    from docx.shared import Inches
    doc = Document()
    doc.add_heading("Quarterly Review", 0)
    doc.add_paragraph("Revenue grew in every quarter of the year.")
    t = doc.add_table(rows=3, cols=2)
    t.style = "Table Grid"
    for i, row in enumerate([["Quarter", "Revenue"], ["Q1", "120"], ["Q4", "310"]]):
        for j, v in enumerate(row):
            t.cell(i, j).text = v
    doc.add_picture(str(IMG / "bar.png"), width=Inches(3.6))
    doc.add_paragraph("Figure 1. Revenue by quarter (USD m).")
    doc.add_picture(str(IMG / "plant.jpg"), width=Inches(3.0))
    doc.add_paragraph("Photo 1. The Chakan plant.")
    doc.save(OUT / "report_with_figures.docx")
    m.truth("report_with_figures.docx", "# Quarterly Review\n\nRevenue grew in every quarter of the year.\n\n| Quarter | Revenue |\n|---|---|\n| Q1 | 120 |\n| Q4 | 310 |\n\nFigure 1. Revenue by quarter (USD m).\n\nPhoto 1. The Chakan plant.\n\n"
            "## Bar chart: Revenue by quarter\n\n| Quarter | Revenue |\n|---|---|\n| Q1 | 120 |\n| Q2 | 150 |\n| Q3 | 200 |\n| Q4 | 310 |")

    # 8. PowerPoint with a native chart, a table and a picture
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.util import Inches as PI
    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = "Revenue by quarter"
    cd = CategoryChartData()
    cd.categories = ["Q1", "Q2", "Q3", "Q4"]
    cd.add_series("Revenue", (120, 150, 200, 310))
    s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, PI(1), PI(1.8), PI(7), PI(4.5), cd)
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = "Plant and KPIs"
    s.shapes.add_picture(str(IMG / "plant.jpg"), PI(0.5), PI(1.6), width=PI(4))
    tb = s.shapes.add_table(3, 2, PI(5), PI(1.8), PI(4), PI(1.5)).table
    for i, row in enumerate([["Measure", "2025"], ["Margin", "14.2%"], ["Plants", "3"]]):
        for j, v in enumerate(row):
            tb.cell(i, j).text = v
    prs.save(OUT / "dashboard.pptx")
    m.truth("dashboard.pptx", "# Revenue by quarter\n\n## Bar chart: Revenue\n\n| Quarter | Revenue |\n|---|---|\n| Q1 | 120 |\n| Q2 | 150 |\n| Q3 | 200 |\n| Q4 | 310 |\n\n# Plant and KPIs\n\n| Measure | 2025 |\n|---|---|\n| Margin | 14.2% |\n| Plants | 3 |")

    # 9. Excel with a table and a native chart
    import xlsxwriter
    wb = xlsxwriter.Workbook(str(OUT / "sales_with_chart.xlsx"))
    ws = wb.add_worksheet("Sales")
    for j, h in enumerate(["Quarter", "Revenue"]):
        ws.write(0, j, h)
    for i, (q, v) in enumerate([("Q1", 120), ("Q2", 150), ("Q3", 200), ("Q4", 310)]):
        ws.write(1 + i, 0, q)
        ws.write(1 + i, 1, v)
    ch = wb.add_chart({"type": "column"})
    ch.add_series({"categories": "=Sales!$A$2:$A$5", "values": "=Sales!$B$2:$B$5", "name": "Revenue"})
    ws.insert_chart("D2", ch)
    wb.close()
    m.truth("sales_with_chart.xlsx", "# Sales\n\n| Quarter | Revenue |\n|---|---|\n| Q1 | 120 |\n| Q2 | 150 |\n| Q3 | 200 |\n| Q4 | 310 |")
    print("combined documents written")


if __name__ == "__main__":
    make()
