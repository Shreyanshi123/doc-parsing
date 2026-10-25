"""Enterprise-style, deliberately difficult documents with a known correct answer for each, written to eval/enterprise/.

    python scripts/make_enterprise_docs.py

What makes them hard: tables with two levels of header and merged cells, a table that repeats its header over several pages, a 12 column
landscape table, nested tables, form grids, logos / stamps / QR codes / watermarks, header and footer on every page, two columns with
sidebars, tables next to charts and photos, a scanned financial statement, a 20 page report, and Excel / Word files with merged cells,
hidden columns, formulas and nested lists. Synthetic, so the answer is exact; real files are messier.
"""
from __future__ import annotations

import io
import random
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_industrial_corpus as m  # noqa: E402  (fonts, degrade, chart_png, ...)

ROOT = Path(__file__).resolve().parent.parent
ENT = ROOT / "eval" / "enterprise"
IMG = ENT / "_img"
random.seed(11)

CSS = ("body{font-family:sans-serif;font-size:9pt} h1{font-size:16pt;margin:0 0 6pt 0} h2{font-size:12pt} h3{font-size:10pt} "
       "table{border-collapse:collapse;width:100%} td,th{border:1px solid #555;padding:2.5pt;font-size:8pt;vertical-align:top} "
       "th{background-color:#d9e2f3} .n{text-align:right} .sec{background-color:#eeeeee;font-weight:bold} .nb td,.nb th{border:0} small{font-size:6.5pt;color:#555}")


def neg(x: float) -> str:
    return f"({abs(x):,.2f})" if x < 0 else f"{x:,.2f}"


def rows_md(rows: list[list]) -> str:
    return "\n".join("| " + " | ".join(str(c) for c in r) + " |" for r in rows)


def write_truth(name: str, text: str) -> None:
    (ENT / f"{name}.truth.md").write_text(text.strip() + "\n", encoding="utf-8")


def save_pdf(html: str, name: str, landscape: bool = False, archive: Path | None = None, css: str = CSS) -> Path:
    path = ENT / name
    story = fitz.Story(html=html, user_css=css, archive=fitz.Archive(str(archive)) if archive else None)
    box = fitz.paper_rect("a4-l" if landscape else "a4")
    writer = fitz.DocumentWriter(str(path))
    more = 1
    while more:
        dev = writer.begin_page(box)
        more, _ = story.place(box + (36, 36, -36, -36))
        story.draw(dev)
        writer.end_page()
    writer.close()
    return path


def stamp_pages(path: Path, header: str | None, footer_fmt: str | None, watermark: str | None = None) -> None:
    """Header / footer on every page (and an optional diagonal watermark) drawn on top of the finished PDF."""
    doc = fitz.open(path)
    n = len(doc)
    for i, page in enumerate(doc):
        w, h = page.rect.width, page.rect.height
        if header:
            page.insert_text((36, 22), header, fontsize=7.5, color=(0.35, 0.35, 0.35))
        if footer_fmt:
            page.insert_text((w - 110, h - 16), footer_fmt.format(i + 1, n), fontsize=7.5, color=(0.35, 0.35, 0.35))
        if watermark and i == 0:
            c = fitz.Point(w * 0.28, h * 0.62)
            page.insert_text(c, watermark, fontsize=96, color=(0.8, 0.2, 0.2), fill_opacity=0.16, morph=(c, fitz.Matrix(35)))
    tmp = path.with_suffix(".tmp.pdf")
    doc.save(tmp)
    doc.close()
    tmp.replace(path)


def logo(name="logo.png") -> None:
    im = Image.new("RGB", (220, 80), "white")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, 76, 76], 14, fill=(20, 60, 130))
    d.text((40, 40), "NW", font=m.font("arialbd.ttf", 34), fill="white", anchor="mm")
    d.text((92, 24), "NORTHWIND", font=m.font("arialbd.ttf", 24), fill=(20, 60, 130))
    d.text((92, 52), "Industrial Supplies", font=m.font("arial.ttf", 17), fill=(90, 90, 90))
    im.save(IMG / name)


def qr(name="qr.png") -> None:
    cells, sz = 25, 8
    im = Image.new("RGB", (cells * sz, cells * sz), "white")
    d = ImageDraw.Draw(im)
    for y in range(cells):
        for x in range(cells):
            finder = (x < 7 and y < 7) or (x > cells - 8 and y < 7) or (x < 7 and y > cells - 8)
            if finder or random.random() < 0.5:
                d.rectangle([x * sz, y * sz, x * sz + sz - 1, y * sz + sz - 1], fill="black")
    im.save(IMG / name)


def signature(name="signature.png") -> None:
    im = Image.new("RGB", (200, 70), "white")
    d = ImageDraw.Draw(im)
    pts = [(10, 50), (30, 20), (45, 55), (62, 18), (80, 52), (105, 30), (130, 48), (150, 22), (190, 40)]
    d.line(pts, fill=(20, 20, 120), width=3, joint="curve")
    im.save(IMG / name)


def photo(name="photo.jpg") -> None:
    im = Image.new("RGB", (420, 260), (150, 190, 230))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 170, 420, 260], fill=(80, 100, 70))
    for x0, hh in ((30, 90), (150, 120), (290, 70)):
        d.rectangle([x0, 170 - hh, x0 + 90, 170], fill=(125, 125, 135))
    im.save(IMG / name, quality=85)


# ---------------------------------------------------------------------------------------------------------------- documents
FIN_ROWS = [  # label, note, FY26 standalone, FY26 consolidated, FY25 standalone, FY25 consolidated
    ("sec", "Income"),
    ("Revenue from operations", "18", 48250.10, 61320.45, 41780.00, 53110.20),
    ("Other income", "19", 1240.55, 1875.30, 980.10, 1402.75),
    ("Total income", "", 49490.65, 63195.75, 42760.10, 54512.95),
    ("sec", "Expenses"),
    ("Cost of materials consumed", "20", 21400.20, 27650.00, 19120.40, 24730.60),
    ("Employee benefits expense", "21", 8905.35, 11240.90, 8011.20, 10122.45),
    ("Finance costs", "22", 1310.00, 1655.25, 1488.50, 1790.10),
    ("Depreciation and amortisation", "23", 2175.80, 2698.40, 2001.35, 2480.00),
    ("Other expenses", "24", 6342.15, 8110.70, 5870.65, 7395.30),
    ("Total expenses", "", 40133.50, 51355.25, 36492.10, 46518.45),
    ("Profit before tax", "", 9357.15, 11840.50, 6268.00, 7994.50),
    ("sec", "Tax expense"),
    ("Current tax", "25", 2310.40, 2905.10, 1544.25, 1988.00),
    ("Deferred tax", "25", -118.65, -142.30, 96.40, 110.15),
    ("Profit for the year", "", 7165.40, 9077.70, 4627.35, 5896.35),
    ("sec", "Earnings per share (INR)"),
    ("Basic", "26", 14.33, 18.16, 9.25, 11.79),
    ("Diluted", "26", 14.21, 18.01, 9.18, 11.70),
]
FIN_FOOT = ["(1) Figures are in INR lakhs unless stated otherwise.", "(2) Consolidated figures include the subsidiaries listed in Note 2."]


def fin_html() -> str:
    h = ("<h1>Consolidated Statement of Profit and Loss</h1><p>For the year ended 31 March 2026</p><table>"
         "<tr><th rowspan='2'>Particulars</th><th rowspan='2'>Note</th><th colspan='2'>Year ended 31 March 2026</th><th colspan='2'>Year ended 31 March 2025</th></tr>"
         "<tr><th>Standalone</th><th>Consolidated</th><th>Standalone</th><th>Consolidated</th></tr>")
    for r in FIN_ROWS:
        if r[0] == "sec":
            h += f"<tr class='sec'><td colspan='6' class='sec'>{r[1]}</td></tr>"
        else:
            h += f"<tr><td>{r[0]}</td><td>{r[1]}</td>" + "".join(f"<td class='n'>{neg(v)}</td>" for v in r[2:]) + "</tr>"
    return h + "</table>" + "".join(f"<p><small>{f}</small></p>" for f in FIN_FOOT)


def fin_truth() -> str:
    rows = [["Particulars", "Note", "Year ended 31 March 2026", "Year ended 31 March 2025"], ["Standalone", "Consolidated", "Standalone", "Consolidated"]]
    for r in FIN_ROWS:
        rows.append([r[1]] if r[0] == "sec" else [r[0], r[1]] + [neg(v) for v in r[2:]])
    return "# Consolidated Statement of Profit and Loss\n\nFor the year ended 31 March 2026\n\n" + rows_md(rows) + "\n\n" + "\n".join(FIN_FOOT)


def e1_financial() -> None:
    save_pdf(fin_html(), "financial_statement_multiheader.pdf", landscape=True)
    write_truth("financial_statement_multiheader.pdf", fin_truth())


def e8_scanned_financial() -> None:
    d = fitz.open(ENT / "financial_statement_multiheader.pdf")
    base = Image.open(io.BytesIO(d[0].get_pixmap(dpi=200).tobytes("png"))).convert("RGB")
    im = m.degrade(base, angle=1.2, noise=12, blur=0.6)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=68)
    out = fitz.open()
    pg = out.new_page(width=842, height=595)
    pg.insert_image(pg.rect, stream=buf.getvalue())
    out.save(ENT / "scanned_financial_statement.pdf")
    write_truth("scanned_financial_statement.pdf", fin_truth())


def e2_ledger() -> None:
    random.seed(21)
    vendors = ["Apex Metals", "Globex Logistics", "Initech Services", "Hooli Software", "Vandelay Imports", "Stark Components"]
    bal, pages, truth_rows = 125000.0, [], []
    head = ["Date", "Voucher", "Narration", "Ref", "Debit", "Credit", "Balance"]
    n = 0
    html = "<h1>General Ledger: Account 4401 Trade Payables</h1>"
    for pg in range(3):
        chunk = "<table><tr>" + "".join(f"<th>{c}</th>" for c in head) + "</tr>"
        truth_rows.append(head)
        for _ in range(20):
            n += 1
            deb, cred = (0.0, 0.0)
            if random.random() < 0.55:
                cred = float(random.randint(8, 95) * 100)
            else:
                deb = float(random.randint(5, 60) * 100)
            bal += cred - deb
            narr = f"{random.choice(vendors)} invoice {random.randint(1000, 9999)} against purchase order {random.randint(10000, 99999)} for the month of {random.choice(['April', 'May', 'June'])}"
            row = [f"{1 + n % 28:02d}/0{4 + pg}/2026", f"JV{2600 + n}", narr, f"REF{random.randint(100, 999)}", neg(deb) if deb else "", neg(cred) if cred else "", neg(bal)]
            truth_rows.append(row)
            chunk += "<tr>" + "".join(f"<td{' class=\"n\"' if i >= 4 else ''}>{c}</td>" for i, c in enumerate(row)) + "</tr>"
        chunk += "</table>"
        html += (f"<p style='page-break-before:always'></p>" if pg else "") + chunk
    save_pdf(html, "ledger_repeated_header.pdf")
    write_truth("ledger_repeated_header.pdf", "# General Ledger: Account 4401 Trade Payables\n\n" + rows_md(truth_rows))


def e3_bom() -> None:
    random.seed(31)
    head = ["Item", "Part no", "Description", "Material", "Qty", "Unit", "Unit wt (kg)", "Total wt (kg)", "Supplier", "Lead time (days)", "Standard", "Remarks"]
    parts = ["Mounting bracket", "Drive shaft", "Bearing housing", "Gasket set", "Hex bolt M12", "Control valve", "Pressure sensor", "Coupling flange", "Seal kit", "Cable harness",
             "Cooling fan", "Filter element", "Hydraulic hose", "Gear box cover", "Motor base plate", "Guard panel", "Terminal block", "Relief valve"]
    mats = ["Steel", "Aluminium", "Rubber", "Copper", "Stainless steel", "Cast iron"]
    sups = ["Apex", "Globex", "Initech", "Hooli", "Stark"]
    rows = []
    for i, p in enumerate(parts, 1):
        q, w = random.randint(1, 24), round(random.uniform(0.2, 18), 2)
        rows.append([f"{i:02d}", f"PRT-{4000 + i * 7}", f"{p} for assembly line {random.randint(1, 9)}", random.choice(mats), q, "pcs", w, round(q * w, 2),
                     random.choice(sups), random.randint(5, 60), random.choice(["ISO 9001", "DIN 931", "ASTM A36", "IS 2062"]), random.choice(["", "Long lead", "Critical", "Alt. source"])])
    html = "<h1>Bill of Materials: Pump Assembly PA-770</h1>" + m.html_table(head, rows, right=(4, 6, 7, 9))
    save_pdf(html, "bom_wide_table.pdf", landscape=True, css=CSS.replace("font-size:8pt", "font-size:6.6pt"))
    write_truth("bom_wide_table.pdf", "# Bill of Materials: Pump Assembly PA-770\n\n" + rows_md([head] + rows))


def e4_invoice() -> None:
    logo(); qr(); signature()
    items = [("Hydraulic pump HP-220 with mounting kit, 3-phase motor, ISO flange", "84137010", 4, 1250.00, 5),
             ("Pressure relief valve PV-8, stainless steel body, 16 bar rated", "84811000", 12, 86.50, 0),
             ("Steel flange 6 inch, forged, with spiral wound gasket and studs", "73079190", 30, 24.75, 10),
             ("Control cable 10 m, shielded, 8 core, UV resistant jacket", "85444999", 8, 142.00, 0)]
    rows, taxable = [], {}
    for i, (d, hsn, q, r, disc) in enumerate(items, 1):
        amt = round(q * r * (1 - disc / 100), 2)
        rows.append([i, d, hsn, q, neg(r), f"{disc}%", neg(amt)])
        taxable[hsn] = amt
    sub = sum(taxable.values())
    tax_rows = [[h, neg(v), "9%", neg(round(v * 0.09, 2)), "9%", neg(round(v * 0.09, 2)), neg(round(v * 0.18, 2))] for h, v in taxable.items()]
    tax = round(sub * 0.18, 2)
    total = sub + tax
    html = ("<table class='nb'><tr><td width='50%'><img src='logo.png' width='170'></td><td><h1>TAX INVOICE</h1>Invoice No: NW/2026/04417<br>Date: 14 March 2026<br>Place of supply: Maharashtra (27)</td></tr></table>"
            "<table><tr><td width='50%'><b>Seller</b><br>Northwind Industrial Supplies Pvt Ltd<br>14 Foundry Road, Pune 411019<br>GSTIN 27AABCN1234F1Z5</td>"
            "<td><b>Buyer</b><br>Apex Machinery Works<br>Plot 8, MIDC Chakan, Pune 410501<br>GSTIN 27AAACA9876K1Z2</td></tr></table><p></p>"
            + m.html_table(["#", "Description", "HSN", "Qty", "Rate", "Disc", "Amount"], rows, right=(3, 4, 5, 6)) + "<p></p><h3>Tax summary</h3>"
            + m.html_table(["HSN", "Taxable value", "CGST rate", "CGST", "SGST rate", "SGST", "Total tax"], tax_rows, right=(1, 3, 5, 6))
            + f"<p>Sub total: {neg(sub)}<br>Total tax: {neg(tax)}<br><b>Grand total: INR {neg(total)}</b></p>"
            "<p>Bank: First Industrial Bank, A/C 004455667788, IFSC FIIB0000123</p>"
            "<table class='nb'><tr><td><img src='qr.png' width='90'><br><small>Scan to pay</small></td><td><img src='signature.png' width='140'><br>Authorised signatory</td></tr></table>")
    p = save_pdf(html, "invoice_complex.pdf", archive=IMG)
    stamp_pages(p, None, None, watermark="PAID")
    write_truth("invoice_complex.pdf", "# TAX INVOICE\n\nInvoice No: NW/2026/04417\nDate: 14 March 2026\nPlace of supply: Maharashtra (27)\n\nSeller\nNorthwind Industrial Supplies Pvt Ltd\n14 Foundry Road, Pune 411019\nGSTIN 27AABCN1234F1Z5\n\n"
                "Buyer\nApex Machinery Works\nPlot 8, MIDC Chakan, Pune 410501\nGSTIN 27AAACA9876K1Z2\n\n" + rows_md([["#", "Description", "HSN", "Qty", "Rate", "Disc", "Amount"]] + rows)
                + "\n\n## Tax summary\n\n" + rows_md([["HSN", "Taxable value", "CGST rate", "CGST", "SGST rate", "SGST", "Total tax"]] + tax_rows)
                + f"\n\nSub total: {neg(sub)}\nTotal tax: {neg(tax)}\nGrand total: INR {neg(total)}\n\nBank: First Industrial Bank, A/C 004455667788, IFSC FIIB0000123\n\nScan to pay\nAuthorised signatory\n\nPAID")


def e5_annual_spread() -> None:
    m.chart_png  # noqa: B018  (charts come from the shared helper)
    for k in ("bar", "pie"):
        (IMG / f"{k}.png").write_bytes(m.chart_png(k))
    intro = ("Northstar Industries delivered a year of disciplined growth. Revenue rose by eleven percent, helped by stronger demand in the pumps and valves businesses, while "
             "operating cost grew more slowly than sales.")
    strat = "Our strategy rests on three pillars: reliability of supply, investment in automation, and closer partnerships with our largest customers."
    risk = "Principal risks remain commodity prices, currency movements and the pace of the warehouse migration."
    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_htmlbox(fitz.Rect(40, 40, 555, 90), "<h1>Annual Report 2026</h1>", css=CSS)
    p1.insert_htmlbox(fitz.Rect(40, 100, 290, 470), f"<h2>Chairman's message</h2><p>{intro}</p><h2>Strategy</h2><p>{strat}</p><h2>Risks</h2><p>{risk}</p>", css=CSS)
    p1.insert_htmlbox(fitz.Rect(305, 100, 555, 470), "<table><tr><th>Highlights</th></tr><tr><td>Revenue up 11 percent</td></tr><tr><td>Margin 14.2 percent</td></tr><tr><td>Three new plants</td></tr></table>"
                      "<p></p><img src='bar.png' width='240'><p><small>Figure 1. Revenue by quarter (USD m).</small></p>", css=CSS, archive=fitz.Archive(str(IMG)))
    p2 = doc.new_page()
    seg = [["Pumps", "Industrial", "310.4", "281.0", "+10.5%"], ["", "Domestic", "122.8", "118.2", "+3.9%"], ["Valves", "Process", "205.1", "176.9", "+15.9%"],
           ["", "Marine", "64.0", "70.5", "-9.2%"], ["Seals", "All", "88.2", "80.1", "+10.1%"]]
    tbl = ("<h2>Segment results</h2><table><tr><th>Segment</th><th>Product line</th><th>FY2026</th><th>FY2025</th><th>Change</th></tr>"
           "<tr><td rowspan='2'>Pumps</td><td>Industrial</td><td class='n'>310.4</td><td class='n'>281.0</td><td class='n'>+10.5%</td></tr><tr><td>Domestic</td><td class='n'>122.8</td><td class='n'>118.2</td><td class='n'>+3.9%</td></tr>"
           "<tr><td rowspan='2'>Valves</td><td>Process</td><td class='n'>205.1</td><td class='n'>176.9</td><td class='n'>+15.9%</td></tr><tr><td>Marine</td><td class='n'>64.0</td><td class='n'>70.5</td><td class='n'>-9.2%</td></tr>"
           "<tr><td>Seals</td><td>All</td><td class='n'>88.2</td><td class='n'>80.1</td><td class='n'>+10.1%</td></tr></table>"
           "<p><small>(1) Segment results are in USD million. (2) Marine valves were affected by one delayed order.</small></p>")
    p2.insert_htmlbox(fitz.Rect(40, 50, 555, 330), tbl, css=CSS)
    p2.insert_htmlbox(fitz.Rect(40, 340, 555, 560), "<img src='pie.png' width='260'><p><small>Figure 2. Sales mix by product.</small></p>", css=CSS, archive=fitz.Archive(str(IMG)))
    p = ENT / "annual_report_spread.pdf"
    doc.save(p)
    doc.close()
    stamp_pages(p, "Northstar Industries | Annual Report 2026", "Page {} of {}")
    write_truth("annual_report_spread.pdf", "Northstar Industries | Annual Report 2026\n\n# Annual Report 2026\n\n## Chairman's message\n\n" + intro + "\n\n## Strategy\n\n" + strat + "\n\n## Risks\n\n" + risk
                + "\n\n" + rows_md([["Highlights"], ["Revenue up 11 percent"], ["Margin 14.2 percent"], ["Three new plants"]]) + "\n\nFigure 1. Revenue by quarter (USD m).\n\nPage 1 of 2\n\n"
                "Northstar Industries | Annual Report 2026\n\n## Segment results\n\n" + rows_md([["Segment", "Product line", "FY2026", "FY2025", "Change"]] + seg)
                + "\n\n(1) Segment results are in USD million. (2) Marine valves were affected by one delayed order.\n\nFigure 2. Sales mix by product.\n\nPage 2 of 2\n\n"
                "## Bar chart: Revenue by quarter\n\n| Quarter | Revenue |\n|---|---|\n| Q1 | 120 |\n| Q2 | 150 |\n| Q3 | 200 |\n| Q4 | 310 |\n\n"
                "## Pie chart: Sales mix\n\n| Product | Share |\n|---|---|\n| Pumps | 45 |\n| Valves | 30 |\n| Seals | 25 |")


def e6_form_grid() -> None:
    cells = [("1. Name of the entity", "ACME INDUSTRIES LIMITED"), ("2. Registration number", "L28920MH2004PLC147890"), ("3. Date of incorporation", "12 March 2004"),
             ("4. Registered office", "Plot 14, Phase 2, Industrial Area, Pune 411019"), ("5. Financial year", "2025-26"), ("6. Annual turnover (INR crore)", "482.60"),
             ("7. Number of employees", "1,240"), ("8. Authorised signatory", "Meera Joshi, Company Secretary")]
    html = "<h1>Annual Compliance Return: Form AC-4</h1><table>"
    for i in range(0, len(cells), 2):
        html += "<tr>" + "".join(f"<td width='50%'><small>{k}</small><br><b>{v}</b></td>" for k, v in cells[i:i + 2]) + "</tr>"
    html += "</table><p></p><table><tr><td><small>9. Status</small><br>[X] Listed &nbsp; [ ] Unlisted</td><td><small>10. Audit qualified?</small><br>[ ] Yes &nbsp; [X] No</td></tr></table>"
    html += "<p></p><table><tr><th>Declaration</th><th>Signature</th><th>Date</th></tr><tr><td>The information given above is true and complete.</td><td>____________</td><td>30 June 2026</td></tr></table>"
    save_pdf(html, "form_grid_ac4.pdf")
    write_truth("form_grid_ac4.pdf", "# Annual Compliance Return: Form AC-4\n\n" + "\n".join(f"{k} {v}" for k, v in cells) + "\n9. Status [X] Listed [ ] Unlisted\n10. Audit qualified? [ ] Yes [X] No\n\n"
                + rows_md([["Declaration", "Signature", "Date"], ["The information given above is true and complete.", "____________", "30 June 2026"]]))


def e7_policy_nested() -> None:
    inner = [["Fire and allied perils", "5,000,000", "1,000"], ["Burglary", "1,500,000", "2,500"], ["Machinery breakdown", "3,200,000", "5,000"]]
    html = ("<h1>Policy Schedule</h1><table><tr><td width='35%'><b>Policy number</b></td><td>POL-2026-778812</td></tr><tr><td><b>Insured</b></td><td>Apex Machinery Works</td></tr>"
            "<tr><td><b>Period</b></td><td>01 April 2026 to 31 March 2027</td></tr><tr><td><b>Coverage details</b></td><td>"
            + m.html_table(["Cover", "Sum insured (INR)", "Deductible (INR)"], inner, right=(1, 2)) + "</td></tr><tr><td><b>Total premium</b></td><td>INR 184,250.00 including GST</td></tr></table>")
    save_pdf(html, "policy_schedule_nested.pdf")
    write_truth("policy_schedule_nested.pdf", "# Policy Schedule\n\nPolicy number POL-2026-778812\nInsured Apex Machinery Works\nPeriod 01 April 2026 to 31 March 2027\nCoverage details\n\n"
                + rows_md([["Cover", "Sum insured (INR)", "Deductible (INR)"]] + inner) + "\n\nTotal premium INR 184,250.00 including GST")


def e9_mixed_page() -> None:
    photo()
    (IMG / "bar.png").write_bytes(m.chart_png("bar"))
    doc = fitz.open()
    pg = doc.new_page(width=842, height=595)
    arch = fitz.Archive(str(IMG))
    pg.insert_htmlbox(fitz.Rect(36, 30, 806, 70), "<h1>Plant Performance Review</h1>", css=CSS)
    left = ("<p>Output improved in every region during the second half. The table shows production by region and line.</p><table><tr><th rowspan='2'>Region</th><th colspan='2'>Output (units)</th><th rowspan='2'>Scrap %</th></tr>"
            "<tr><th>Line A</th><th>Line B</th></tr><tr><td>North</td><td class='n'>6,420</td><td class='n'>5,180</td><td class='n'>1.2</td></tr><tr><td>South</td><td class='n'>4,950</td><td class='n'>4,310</td><td class='n'>1.8</td></tr>"
            "<tr><td>East</td><td class='n'>7,130</td><td class='n'>6,020</td><td class='n'>0.9</td></tr></table><p><small>Source: plant MES, unaudited.</small></p>")
    pg.insert_htmlbox(fitz.Rect(36, 80, 420, 560), left, css=CSS)
    pg.insert_htmlbox(fitz.Rect(440, 80, 806, 560), "<img src='bar.png' width='300'><p><small>Figure 1. Revenue by quarter (USD m).</small></p><img src='photo.jpg' width='260'><p><small>Photo 1. Line A, Chakan plant.</small></p>", css=CSS, archive=arch)
    p = ENT / "mixed_table_chart_photo.pdf"
    doc.save(p)
    write_truth("mixed_table_chart_photo.pdf", "# Plant Performance Review\n\nOutput improved in every region during the second half. The table shows production by region and line.\n\n"
                + rows_md([["Region", "Output (units)", "Scrap %"], ["Line A", "Line B"], ["North", "6,420", "5,180", "1.2"], ["South", "4,950", "4,310", "1.8"], ["East", "7,130", "6,020", "0.9"]])
                + "\n\nSource: plant MES, unaudited.\n\nFigure 1. Revenue by quarter (USD m).\n\nPhoto 1. Line A, Chakan plant.\n\n"
                "## Bar chart: Revenue by quarter\n\n| Quarter | Revenue |\n|---|---|\n| Q1 | 120 |\n| Q2 | 150 |\n| Q3 | 200 |\n| Q4 | 310 |")


def e10_clinical() -> None:
    rows = [("sec", "Primary endpoint"), ("Change in HbA1c at week 24 (%)", "-1.42 (-1.58, -1.26)", "-0.31 (-0.47, -0.15)", "-1.11 (-1.33, -0.89)", "<0.001"),
            ("sec", "Secondary endpoints"), ("Change in body weight (kg) †", "-3.80 (-4.35, -3.25)", "-0.90 (-1.42, -0.38)", "-2.90 (-3.66, -2.14)", "<0.001"),
            ("Fasting plasma glucose (mmol/L)", "-2.15 (-2.40, -1.90)", "-0.48 (-0.73, -0.23)", "-1.67 (-2.02, -1.32)", "<0.001"),
            ("Systolic blood pressure (mmHg) ‡", "-5.20 (-6.80, -3.60)", "-1.90 (-3.50, -0.30)", "-3.30 (-5.56, -1.04)", "0.004"),
            ("sec", "Safety"), ("Any adverse event, n (%)", "231 (56.1)", "209 (51.6)", "4.5 (-2.1, 11.1)", "0.18"), ("Serious adverse events, n (%)", "18 (4.4)", "15 (3.7)", "0.7 (-2.2, 3.6)", "0.64")]
    head = ["Outcome", "Treatment (n=412)", "Placebo (n=405)", "Difference (95% CI)", "p-value"]
    html = "<h1>Table 2. Efficacy and safety outcomes</h1><table><tr>" + "".join(f"<th>{c}</th>" for c in head) + "</tr>"
    truth_rows = [head]
    for r in rows:
        if r[0] == "sec":
            html += f"<tr><td colspan='5' class='sec'>{r[1]}</td></tr>"
            truth_rows.append([r[1]])
        else:
            html += "<tr>" + f"<td>{r[0]}</td>" + "".join(f"<td class='n'>{c}</td>" for c in r[1:]) + "</tr>"
            truth_rows.append(list(r))
    foot = ["† Measured in participants with baseline BMI of 27 or more.", "‡ Seated measurement, mean of three readings.", "CI, confidence interval."]
    html += "</table>" + "".join(f"<p><small>{f}</small></p>" for f in foot)
    save_pdf(html, "clinical_trial_table.pdf")
    write_truth("clinical_trial_table.pdf", "# Table 2. Efficacy and safety outcomes\n\n" + rows_md(truth_rows) + "\n\n" + "\n".join(foot))


def e11_contract() -> None:
    clauses = [("1.", "Definitions", ["1.1 \"Services\" means the services described in Schedule 1.", "1.2 \"Affiliate\" means any entity that controls, is controlled by or is under common control with a party.",
                                      "1.2.1 Control means the power to direct the management of an entity."]),
               ("2.", "Term", ["2.1 This Agreement starts on the Effective Date and continues for thirty six months.", "2.2 It renews for successive twelve month periods unless either party gives ninety days notice."]),
               ("3.", "Fees and payment", ["3.1 The Customer shall pay the fees set out in Schedule 2.", "3.2 Undisputed invoices are payable within thirty days.", "3.2.1 Late payments bear interest at one percent per month.",
                                           "3.3 All fees exclude applicable taxes."]),
               ("4.", "Confidentiality", ["4.1 Each party shall protect the other party's Confidential Information.", "4.2 This obligation survives termination for five years."]),
               ("5.", "Liability", ["5.1 Neither party is liable for indirect loss.", "5.2 Total liability is limited to the fees paid in the preceding twelve months."]),
               ("6.", "General", ["6.1 This Agreement is governed by the laws of India.", "6.2 The courts of Mumbai have exclusive jurisdiction."])]
    html = "<h1>MASTER SERVICES AGREEMENT</h1><p>Agreement No. MA-2026-77, made on 1 May 2026 between Northwind Industrial Supplies Pvt Ltd and Apex Machinery Works.</p>"
    truth = "# MASTER SERVICES AGREEMENT\n\nAgreement No. MA-2026-77, made on 1 May 2026 between Northwind Industrial Supplies Pvt Ltd and Apex Machinery Works.\n\n"
    for i, (num, title, subs) in enumerate(clauses):
        html += ("<p style='page-break-before:always'></p>" if i in (2, 4) else "") + f"<h2>{num} {title}</h2>"
        truth += f"## {num} {title}\n\n"
        for s in subs:
            ind = 10 * s.split(" ")[0].count(".") if s.split(" ")[0].count(".") > 1 else 0
            html += f"<p style='margin-left:{ind}pt'>{s}</p>"
            truth += s + "\n\n"
    html += "<h2>Signatures</h2><table><tr><th>For Northwind</th><th>For Apex</th></tr><tr><td>Name: R. Kulkarni<br>Title: Director</td><td>Name: S. Deshmukh<br>Title: Managing Director</td></tr></table>"
    truth += "## Signatures\n\n" + rows_md([["For Northwind", "For Apex"], ["Name: R. Kulkarni Title: Director", "Name: S. Deshmukh Title: Managing Director"]]) + "\n\n"
    p = save_pdf(html, "contract_nested_clauses.pdf")
    stamp_pages(p, "CONFIDENTIAL | Master Services Agreement MA-2026-77", "Page {} of {}")
    n = len(fitz.open(p))
    hdr = "CONFIDENTIAL | Master Services Agreement MA-2026-77"
    write_truth("contract_nested_clauses.pdf", truth + "\n".join(f"{hdr}\nPage {i} of {n}" for i in range(1, n + 1)))


def e12_long_report() -> None:
    rnd = random.Random(5)
    words = "plant output quality safety supplier delivery maintenance audit energy sensor schedule customer inventory training budget".split()
    html, truth = "<h1>Operations Annual Report</h1><h2>Contents</h2>", "# Operations Annual Report\n\n## Contents\n\n"
    sections = [f"Section {i}: {t}" for i, t in enumerate(["Safety", "Quality", "Delivery", "Cost", "People", "Maintenance", "Energy", "Suppliers", "Inventory", "Customers", "Projects",
                                                           "Training", "Audits", "Risks", "Capital", "Outlook", "Governance", "Appendix"], 1)]
    for s in sections:
        html += f"<p>{s}</p>"
        truth += s + "\n\n"
    for s in sections:
        para = " ".join(rnd.choice(words) for _ in range(120)) + "."
        rows = [[f"{s.split(':')[1].strip()} metric {k}", rnd.randint(10, 999), f"{rnd.randint(1, 99)}.{rnd.randint(0, 9)}%"] for k in range(1, 5)]
        html += f"<p style='page-break-before:always'></p><h2>{s}</h2><p>{para}</p>" + m.html_table(["Metric", "Value", "Change"], rows, right=(1, 2))
        truth += f"## {s}\n\n{para}\n\n" + rows_md([["Metric", "Value", "Change"]] + rows) + "\n\n"
    save_pdf(html, "long_annual_report_20p.pdf")
    write_truth("long_annual_report_20p.pdf", truth)


def e13_excel() -> None:
    import datetime as dt
    import xlsxwriter

    wb = xlsxwriter.Workbook(str(ENT / "budget_model.xlsx"))
    bold, pct, cur = wb.add_format({"bold": True}), wb.add_format({"num_format": "0.0%"}), wb.add_format({"num_format": "#,##0.00"})
    ws = wb.add_worksheet("Summary")
    ws.merge_range("A1:F1", "FY2026 Budget Model", bold)
    for j, h in enumerate(["Department", "Budget", "Actual", "Variance", "Variance %", "Owner"]):
        ws.write(2, j, h, bold)
    depts = [("Operations", 5200000, 5385000, "R. Kulkarni"), ("Sales", 2100000, 1980000, "A. Rao"), ("R&D", 1800000, 1925000, "S. Iyer"), ("Finance", 640000, 610000, "N. Shah")]
    summ = []
    for i, (d, b, a, o) in enumerate(depts):
        r = 3 + i
        ws.write(r, 0, d); ws.write(r, 1, b, cur); ws.write(r, 2, a, cur)
        ws.write_formula(r, 3, f"=C{r + 1}-B{r + 1}", cur, a - b)
        ws.write_formula(r, 4, f"=D{r + 1}/B{r + 1}", pct, (a - b) / b)
        ws.write(r, 5, o)
        summ.append([d, b, a, a - b, round((a - b) / b, 4), o])
    ws.set_column("G:G", None, None, {"hidden": True}); ws.write(2, 6, "internal code", bold)
    for i in range(4):
        ws.write(3 + i, 6, f"X{i}")
    ws2 = wb.add_worksheet("Detail")
    ws2.freeze_panes(1, 0)
    head = ["Date", "Cost centre", "Category", "Vendor", "Amount", "Tax", "Total", "Approved"]
    for j, h in enumerate(head):
        ws2.write(0, j, h, bold)
    rnd = random.Random(8)
    det = []
    datef = wb.add_format({"num_format": "yyyy-mm-dd"})
    for i in range(30):
        d = dt.datetime(2026, 1 + i % 6, 1 + i % 27)
        amt = float(rnd.randint(500, 90000))
        tax = round(amt * 0.18, 2)
        row = [d.strftime("%Y-%m-%d"), f"CC{100 + i % 7}", rnd.choice(["Freight", "Software", "Consulting", "Spares"]), rnd.choice(["Apex", "Globex", "Initech", "Hooli"]), amt, tax, round(amt + tax, 2), rnd.choice(["Yes", "No"])]
        ws2.write_datetime(1 + i, 0, d, datef)
        for j in range(1, 6):
            ws2.write(1 + i, j, row[j])
        ws2.write_formula(1 + i, 6, f"=E{i + 2}+F{i + 2}", cur, row[6]); ws2.write(1 + i, 7, row[7])
        det.append(row)
    ws3 = wb.add_worksheet("Notes")
    ws3.write(0, 0, "Variance is actual minus budget. Figures exclude capital expenditure.")
    wb.close()
    write_truth("budget_model.xlsx", "# FY2026 Budget Model\n\n" + rows_md([["Department", "Budget", "Actual", "Variance", "Variance %", "Owner"]] + summ) + "\n\n# Detail\n\n"
                + rows_md([head] + [[r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]] for r in det]) + "\n\n# Notes\n\nVariance is actual minus budget. Figures exclude capital expenditure.")


def e14_word() -> None:
    from docx import Document
    from docx.shared import Inches

    (IMG / "bar.png").write_bytes(m.chart_png("bar"))
    doc = Document()
    doc.sections[0].header.paragraphs[0].text = "Northwind Industrial Supplies | Quality Manual"
    doc.sections[0].footer.paragraphs[0].text = "Controlled document QM-001 revision 4"
    doc.add_heading("Quality Manual", 0)
    doc.add_heading("1. Scope", 1)
    doc.add_paragraph("This manual applies to all manufacturing sites and to every supplier of safety critical parts.")
    doc.add_heading("2. Responsibilities", 1)
    for t in ("Plant head", "Quality manager"):
        doc.add_paragraph(t, style="List Number")
    for t in ("Approves the audit plan", "Reviews corrective actions"):
        doc.add_paragraph(t, style="List Number 2")
    doc.add_heading("3. Audit schedule", 1)
    tb = doc.add_table(rows=4, cols=4)
    tb.style = "Table Grid"
    tb.cell(0, 0).merge(tb.cell(0, 3)).text = "Audit schedule 2026"
    for j, h in enumerate(["Site", "Quarter", "Auditor", "Status"]):
        tb.cell(1, j).text = h
    for j, v in enumerate(["Pune", "Q2", "R. Kulkarni", "Planned"]):
        tb.cell(2, j).text = v
    for j, v in enumerate(["Chakan", "Q3", "A. Rao", "Open"]):
        tb.cell(3, j).text = v
    doc.add_picture(str(IMG / "bar.png"), width=Inches(3.4))
    doc.add_paragraph("Figure 1. Non-conformances by quarter.")
    doc.save(ENT / "quality_manual.docx")
    write_truth("quality_manual.docx", "Northwind Industrial Supplies | Quality Manual\n\n# Quality Manual\n\n## 1. Scope\n\nThis manual applies to all manufacturing sites and to every supplier of safety critical parts.\n\n"
                "## 2. Responsibilities\n\n1. Plant head\n2. Quality manager\n- Approves the audit plan\n- Reviews corrective actions\n\n## 3. Audit schedule\n\nAudit schedule 2026\n\n"
                + rows_md([["Site", "Quarter", "Auditor", "Status"], ["Pune", "Q2", "R. Kulkarni", "Planned"], ["Chakan", "Q3", "A. Rao", "Open"]]) + "\n\nFigure 1. Non-conformances by quarter.\n\nControlled document QM-001 revision 4")


def main() -> None:
    ENT.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(exist_ok=True)
    for fn in (e1_financial, e8_scanned_financial, e2_ledger, e3_bom, e4_invoice, e5_annual_spread, e6_form_grid, e7_policy_nested, e9_mixed_page, e10_clinical, e11_contract,
               e12_long_report, e13_excel, e14_word):
        fn()
        print("done", fn.__name__, flush=True)
    files = [p for p in ENT.iterdir() if p.is_file() and not p.name.endswith(".truth.md")]
    print(f"{len(files)} documents written to {ENT}")


if __name__ == "__main__":
    main()
