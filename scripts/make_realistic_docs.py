"""Business documents laid out the way real ones are (bank statement, annual-report income statement, purchase order, payslip, lab report,
utility bill, bill of lading, RFP requirement matrix, board minutes, two-column research paper, a phone photo of a purchase order, plus an
Excel workbook, a Word SOP and a PowerPoint deck with chart objects). Written to eval/realistic/ with a hand-written answer file for each.

    python scripts/make_realistic_docs.py

They are still generated (no real company's files can be shared here); the layouts copy common real-world formats and are messier than
eval/enterprise: dot-leaders, dollar signs in their own cells, running balances, side-by-side tables, stamps, tilt and noise.
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
REAL = ROOT / "eval" / "realistic"
e.ENT = REAL
e.IMG = REAL / "_img"
CSS, neg, rows_md, write_truth, save_pdf, stamp_pages = e.CSS, e.neg, e.rows_md, e.write_truth, e.save_pdf, e.stamp_pages
INK = "color:#222"


def money(x: float) -> str:
    return f"{x:,.2f}"


def r1_bank() -> None:
    rnd = random.Random(41)
    head = ["Date", "Description", "Ref", "Withdrawals", "Deposits", "Balance"]
    bal, n, chunks, truth_rows = 48250.75, 0, [], []
    descs = ["UPI/Apex Metals/payment", "NEFT CR Globex Logistics", "ATM WDL Pune Camp", "POS Hooli Software subscription", "IMPS DR Vandelay Imports", "Cheque deposit 004411",
             "Salary credit Northwind", "Electricity bill Mahavitaran", "Card payment Stark Components", "Interest credit"]
    html = ("<h1>First Industrial Bank</h1><table class='nb'><tr><td width='50%'><b>Account statement</b><br>Account name: Apex Machinery Works<br>Account number: 004455667788<br>"
            "Branch: Chakan, Pune</td><td>Statement period: 01 Apr 2026 to 30 Jun 2026<br>Currency: INR<br>Opening balance: 48,250.75</td></tr></table>")
    truth = ("# First Industrial Bank\n\nAccount statement\nAccount name: Apex Machinery Works\nAccount number: 004455667788\nBranch: Chakan, Pune\n"
             "Statement period: 01 Apr 2026 to 30 Jun 2026\nCurrency: INR\nOpening balance: 48,250.75\n\n")
    for pg in range(3):
        rows = []
        for _ in range(16):
            n += 1
            w = d = 0.0
            if rnd.random() < 0.5:
                d = float(rnd.randint(40, 900) * 100)
            else:
                w = float(rnd.randint(10, 400) * 100 + rnd.choice([0, 50, 75]))
            bal += d - w
            rows.append([f"{1 + n % 28:02d}-{['Apr', 'May', 'Jun'][pg]}-2026", rnd.choice(descs), f"{rnd.randint(100000, 999999)}", money(w) if w else "", money(d) if d else "", money(bal)])
        truth_rows += [head] + rows if pg == 0 else [head] + rows
        html += ("<p style='page-break-before:always'></p>" if pg else "") + m.html_table(head, rows, right=(3, 4, 5))
    html += f"<p><b>Closing balance: {money(bal)}</b></p><p><small>This is a computer generated statement and does not require a signature. Please report discrepancies within 30 days.</small></p>"
    p = save_pdf(html, "bank_statement.pdf")
    stamp_pages(p, "First Industrial Bank | Statement of account 004455667788", "Page {} of {}")
    pages_n = len(fitz.open(p))
    out = truth
    for pg in range(3):
        out += rows_md(truth_rows[pg * 17:(pg + 1) * 17]) + "\n\n"
    out += f"Closing balance: {money(bal)}\n\nThis is a computer generated statement and does not require a signature. Please report discrepancies within 30 days.\n\n"
    out += "\n".join(f"First Industrial Bank | Statement of account 004455667788\nPage {i} of {pages_n}" for i in range(1, pages_n + 1))
    write_truth("bank_statement.pdf", out)


def r2_income() -> None:
    lines = [("Net sales", 48210, 44870, 41325), ("Cost of sales", -29410, -27960, -26180), ("Gross profit", 18800, 16910, 15145), ("sec", "Operating expenses"),
             ("Research and development", -3120, -2870, -2540), ("Selling, general and administrative", -5460, -5210, -4890), ("Restructuring charges", -310, -95, 0),
             ("Total operating expenses", -8890, -8175, -7430), ("Operating income", 9910, 8735, 7715), ("Interest expense", -640, -710, -780), ("Other income, net", 215, 180, 96),
             ("Income before income taxes", 9485, 8205, 7031), ("Provision for income taxes", -2180, -1890, -1620), ("Net income", 7305, 6315, 5411)]
    html = "<h1>NORTHSTAR INDUSTRIES</h1><h2>CONSOLIDATED STATEMENTS OF OPERATIONS</h2><p>(In millions, except per share data)</p><table><tr><th rowspan='2'>&nbsp;</th><th colspan='6'>Years ended December 31,</th></tr><tr><th colspan='2'>2025</th><th colspan='2'>2024</th><th colspan='2'>2023</th></tr>"
    truth_rows = [["", "2025", "2024", "2023"]]
    for ln in lines:
        if ln[0] == "sec":
            html += f"<tr><td colspan='7'><b>{ln[1]}:</b></td></tr>"
            truth_rows.append([ln[1] + ":"])
            continue
        tot = ln[0] in ("Gross profit", "Operating income", "Net income", "Total operating expenses")
        cells = "".join(f"<td>$</td><td class='n'>{neg(v)[:-3] if v else '-'}</td>" if tot else f"<td></td><td class='n'>{neg(v)[:-3] if v else '-'}</td>" for v in ln[1:])
        html += f"<tr><td>{'<b>' if tot else ''}{ln[0]}{'</b>' if tot else ''}</td>{cells}</tr>"
        truth_rows.append([ln[0]] + [neg(v)[:-3] if v else "-" for v in ln[1:]])
    eps = [("Basic", 4.12, 3.55, 3.02), ("Diluted", 4.07, 3.50, 2.98)]
    html += "<tr><td colspan='7'><b>Earnings per share:</b></td></tr>" + "".join(f"<tr><td>{a}</td>" + "".join(f"<td>$</td><td class='n'>{x:.2f}</td>" for x in v) + "</tr>" for a, *v in eps)
    truth_rows += [["Earnings per share:"]] + [[a] + [f"{x:.2f}" for x in v] for a, *v in eps]
    html += "</table><p><small>The accompanying notes are an integral part of these consolidated financial statements. Amounts in parentheses are losses or expenses.</small></p>"
    save_pdf(html, "annual_report_income_statement.pdf")
    write_truth("annual_report_income_statement.pdf", "# NORTHSTAR INDUSTRIES\n\n## CONSOLIDATED STATEMENTS OF OPERATIONS\n\n(In millions, except per share data)\n\nYears ended December 31,\n\n" + rows_md(truth_rows)
                + "\n\nThe accompanying notes are an integral part of these consolidated financial statements. Amounts in parentheses are losses or expenses.")


def r3_po() -> None:
    e.logo()
    items = [("Hex bolt M12 x 60, zinc plated", "HB-1260", 500, 3.2), ("Bearing 6205-2RS", "BR-6205", 120, 41.5), ("Hydraulic hose 1/2 inch, 3 m", "HH-0503", 24, 118.0), ("Gasket kit for pump PA-770", "GK-770", 40, 64.75)]
    rows, tot = [], 0.0
    for i, (d, sku, q, pr) in enumerate(items, 1):
        amt = round(q * pr, 2)
        tot += amt
        rows.append([i, sku, d, q, money(pr), money(amt)])
    html = ("<table class='nb'><tr><td width='45%'><img src='logo.png' width='160'></td><td><h1>PURCHASE ORDER</h1>PO number: 4500187723<br>Date: 02 June 2026<br>Page 1 of 1</td></tr></table>"
            "<table><tr><td width='33%'><b>Vendor</b><br>Globex Logistics Ltd<br>22 Port Road, Mumbai 400001</td><td width='33%'><b>Ship to</b><br>Apex Machinery Works<br>Plot 8, MIDC Chakan, Pune 410501</td>"
            "<td><b>Bill to</b><br>Apex Machinery Works, Accounts<br>PO Box 114, Pune 411001</td></tr></table><p></p>"
            + m.html_table(["Line", "Item code", "Description", "Qty", "Unit price", "Amount"], rows, right=(3, 4, 5))
            + f"<p style='text-align:right'>Total order value: <b>INR {money(tot)}</b></p><h3>Terms and conditions</h3>"
            "<p>1. Delivery within 21 days of the order date. 2. Payment within 45 days of receipt of a correct invoice. 3. Goods are subject to inspection and may be rejected within 10 days. "
            "4. The vendor must quote the PO number on every invoice and delivery note.</p><table class='nb'><tr><td>Authorised by: ____________<br>Procurement Manager</td><td>Accepted by vendor: ____________</td></tr></table>")
    save_pdf(html, "purchase_order.pdf", archive=e.IMG)
    write_truth("purchase_order.pdf", "# PURCHASE ORDER\n\nPO number: 4500187723\nDate: 02 June 2026\nPage 1 of 1\n\nVendor\nGlobex Logistics Ltd\n22 Port Road, Mumbai 400001\n"
                "Ship to\nApex Machinery Works\nPlot 8, MIDC Chakan, Pune 410501\nBill to\nApex Machinery Works, Accounts\nPO Box 114, Pune 411001\n\n"
                + rows_md([["Line", "Item code", "Description", "Qty", "Unit price", "Amount"]] + rows) + f"\n\nTotal order value: INR {money(tot)}\n\n## Terms and conditions\n\n"
                "1. Delivery within 21 days of the order date. 2. Payment within 45 days of receipt of a correct invoice. 3. Goods are subject to inspection and may be rejected within 10 days. "
                "4. The vendor must quote the PO number on every invoice and delivery note.\n\nAuthorised by: ____________\nProcurement Manager\nAccepted by vendor: ____________")


def r4_payslip() -> None:
    earn = [["Basic salary", "62,500.00"], ["House rent allowance", "25,000.00"], ["Special allowance", "18,400.00"], ["Conveyance", "1,600.00"], ["Gross earnings", "107,500.00"]]
    ded = [["Provident fund", "7,500.00"], ["Professional tax", "200.00"], ["Income tax (TDS)", "11,350.00"], ["Medical premium", "950.00"], ["Total deductions", "20,000.00"]]
    html = ("<h1>PAYSLIP FOR THE MONTH OF JUNE 2026</h1><table><tr><td width='25%'><b>Employee name</b></td><td>Meera Joshi</td><td width='25%'><b>Employee ID</b></td><td>EMP-20418</td></tr>"
            "<tr><td><b>Designation</b></td><td>Senior Accountant</td><td><b>Department</b></td><td>Finance</td></tr><tr><td><b>PAN</b></td><td>ABCPJ1234K</td><td><b>Bank account</b></td><td>XXXX7788</td></tr></table><p></p>"
            "<table class='nb'><tr><td width='49%'>" + m.html_table(["Earnings", "Amount (INR)"], earn, right=(1,)) + "</td><td width='2%'></td><td>" + m.html_table(["Deductions", "Amount (INR)"], ded, right=(1,)) + "</td></tr></table>"
            "<p><b>Net pay: INR 87,500.00</b></p><p>Net pay in words: Rupees Eighty Seven Thousand Five Hundred only.</p><p><small>This is a system generated payslip and does not need a signature.</small></p>")
    save_pdf(html, "payslip.pdf")
    write_truth("payslip.pdf", "# PAYSLIP FOR THE MONTH OF JUNE 2026\n\nEmployee name Meera Joshi\nEmployee ID EMP-20418\nDesignation Senior Accountant\nDepartment Finance\nPAN ABCPJ1234K\nBank account XXXX7788\n\n"
                + rows_md([["Earnings", "Amount (INR)"]] + earn) + "\n\n" + rows_md([["Deductions", "Amount (INR)"]] + ded)
                + "\n\nNet pay: INR 87,500.00\n\nNet pay in words: Rupees Eighty Seven Thousand Five Hundred only.\n\nThis is a system generated payslip and does not need a signature.")


def r5_lab() -> None:
    rows = [["Haemoglobin", "13.1", "g/dL", "13.0 - 17.0", ""], ["Total leucocyte count", "11.8", "x10^3/uL", "4.0 - 10.0", "H"], ["Platelet count", "262", "x10^3/uL", "150 - 410", ""],
            ["Fasting glucose", "108", "mg/dL", "70 - 99", "H"], ["Total cholesterol", "182", "mg/dL", "< 200", ""], ["LDL cholesterol", "131", "mg/dL", "< 100", "H"],
            ["HDL cholesterol", "38", "mg/dL", "> 40", "L"], ["Creatinine", "0.92", "mg/dL", "0.70 - 1.30", ""], ["TSH", "2.40", "uIU/mL", "0.40 - 4.20", ""]]
    html = ("<h1>MetroCare Diagnostics: Laboratory Report</h1><table><tr><td width='25%'><b>Patient</b></td><td>Rohan Mehta, 41 Y / Male</td><td width='25%'><b>Sample ID</b></td><td>SID 88213094</td></tr>"
            "<tr><td><b>Referred by</b></td><td>Dr. A. Kulkarni</td><td><b>Reported on</b></td><td>12 June 2026, 18:40</td></tr></table><p></p>"
            + m.html_table(["Test", "Result", "Unit", "Reference range", "Flag"], rows, right=(1,))
            + "<p><small>H = above reference range, L = below reference range. Results relate only to the sample tested. Clinical correlation is advised.</small></p><p>Verified by: Dr. S. Iyer, MD Pathology</p>")
    save_pdf(html, "lab_report.pdf")
    write_truth("lab_report.pdf", "# MetroCare Diagnostics: Laboratory Report\n\nPatient Rohan Mehta, 41 Y / Male\nSample ID SID 88213094\nReferred by Dr. A. Kulkarni\nReported on 12 June 2026, 18:40\n\n"
                + rows_md([["Test", "Result", "Unit", "Reference range", "Flag"]] + rows) + "\n\nH = above reference range, L = below reference range. Results relate only to the sample tested. Clinical correlation is advised.\n\nVerified by: Dr. S. Iyer, MD Pathology")


def r6_utility() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    months, kwh = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], [410, 385, 430, 520, 610, 575]
    fig, ax = plt.subplots(figsize=(5, 2.6))
    ax.bar(months, kwh, color="#2c7fb8")
    for i, v in enumerate(kwh):
        ax.text(i, v + 8, str(v), ha="center", fontsize=8)
    ax.set_title("Monthly consumption (kWh)")
    ax.set_ylim(0, 700)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    e.IMG.mkdir(parents=True, exist_ok=True)
    (e.IMG / "usage.png").write_bytes(buf.getvalue())
    charges = [["Energy charge (575 kWh)", "4,312.50"], ["Fixed charge", "480.00"], ["Fuel adjustment", "287.50"], ["Electricity duty (16%)", "812.16"], ["Total amount due", "5,892.16"]]
    html = ("<h1>MahaPower Electricity Bill</h1><table><tr><td width='50%'><b>Consumer</b><br>Apex Machinery Works<br>Consumer no. 170230998812<br>Meter no. MT-554120</td>"
            "<td><b>Bill date</b> 05 July 2026<br><b>Due date</b> 20 July 2026<br><b>Billing period</b> 01 June to 30 June 2026</td></tr></table><p></p>"
            "<img src='usage.png' width='330'><p><small>Figure 1. Monthly consumption for the last six months.</small></p>" + m.html_table(["Charges", "Amount (INR)"], charges, right=(1,))
            + "<p><b>Pay by 20 July 2026 to avoid a late fee of INR 150.</b></p>")
    save_pdf(html, "utility_bill.pdf", archive=e.IMG)
    write_truth("utility_bill.pdf", "# MahaPower Electricity Bill\n\nConsumer Apex Machinery Works\nConsumer no. 170230998812\nMeter no. MT-554120\nBill date 05 July 2026\nDue date 20 July 2026\nBilling period 01 June to 30 June 2026\n\n"
                "Figure 1. Monthly consumption for the last six months.\n\n" + rows_md([["Charges", "Amount (INR)"]] + charges) + "\n\nPay by 20 July 2026 to avoid a late fee of INR 150.\n\n"
                "## Bar chart: Monthly consumption (kWh)\n\n| Month | kWh |\n|---|---|\n" + "\n".join(f"| {a} | {b} |" for a, b in zip(months, kwh)))


def r7_bol() -> None:
    html = ("<h1>BILL OF LADING</h1><table><tr><td colspan='2'><small>Shipper</small><br><b>Northwind Industrial Supplies Pvt Ltd</b><br>14 Foundry Road, Pune</td><td><small>B/L number</small><br><b>MAEU 227781903</b></td></tr>"
            "<tr><td colspan='2'><small>Consignee</small><br><b>Apex Trading LLC</b><br>Jebel Ali, Dubai, UAE</td><td><small>Vessel / voyage</small><br><b>MSC Aurora 026E</b></td></tr>"
            "<tr><td><small>Port of loading</small><br><b>Nhava Sheva</b></td><td><small>Port of discharge</small><br><b>Jebel Ali</b></td><td><small>Freight</small><br><b>Prepaid</b></td></tr>"
            "<tr><th>Container no.</th><th>Description of goods</th><th>Gross weight (kg)</th></tr>"
            "<tr><td>MSKU 4412907</td><td rowspan='2'>Industrial pumps and spare parts, 38 cartons, HS 8413</td><td class='n'>9,420</td></tr><tr><td>TCNU 8830415</td><td class='n'>7,115</td></tr>"
            "<tr><td colspan='2'><b>Total</b></td><td class='n'><b>16,535</b></td></tr></table><p><small>Shipped on board in apparent good order and condition. Date of issue: 18 June 2026.</small></p>")
    save_pdf(html, "bill_of_lading.pdf")
    write_truth("bill_of_lading.pdf", "# BILL OF LADING\n\nShipper Northwind Industrial Supplies Pvt Ltd 14 Foundry Road, Pune\nB/L number MAEU 227781903\nConsignee Apex Trading LLC Jebel Ali, Dubai, UAE\nVessel / voyage MSC Aurora 026E\n"
                "Port of loading Nhava Sheva\nPort of discharge Jebel Ali\nFreight Prepaid\n\n" + rows_md([["Container no.", "Description of goods", "Gross weight (kg)"], ["MSKU 4412907", "Industrial pumps and spare parts, 38 cartons, HS 8413", "9,420"],
                                                                                                              ["TCNU 8830415", "Industrial pumps and spare parts, 38 cartons, HS 8413", "7,115"], ["Total", "", "16,535"]])
                + "\n\nShipped on board in apparent good order and condition. Date of issue: 18 June 2026.")


def r8_rfp() -> None:
    cats = [("Security", [("SEC-01", "The system shall encrypt data at rest using AES-256.", "Must"), ("SEC-02", "The system shall support single sign-on through SAML 2.0.", "Must"), ("SEC-03", "Audit logs shall be retained for 7 years.", "Should")]),
            ("Integration", [("INT-01", "Provide a REST API for all master data objects.", "Must"), ("INT-02", "Support scheduled export to CSV and XML.", "Should")]),
            ("Reporting", [("REP-01", "Provide a dashboard with drill-down by plant and month.", "Must"), ("REP-02", "Allow users to schedule PDF reports by email.", "Could"), ("REP-03", "Support ad-hoc queries without developer help.", "Should")]),
            ("Support", [("SUP-01", "24x7 support for severity 1 incidents with a 1 hour response.", "Must"), ("SUP-02", "Named customer success manager.", "Could")])]
    html = "<h1>Request for Proposal RFP-2026-014: Requirements Matrix</h1><p>Vendors must mark each requirement as Compliant (C), Partially compliant (P) or Not compliant (N).</p><table><tr><th>Category</th><th>ID</th><th>Requirement</th><th>Priority</th><th>C / P / N</th></tr>"
    truth_rows = [["Category", "ID", "Requirement", "Priority", "C / P / N"]]
    for c, reqs in cats:
        for i, (rid, text, pr) in enumerate(reqs):
            html += "<tr>" + (f"<td rowspan='{len(reqs)}'><b>{c}</b></td>" if i == 0 else "") + f"<td>{rid}</td><td>{text}</td><td>{pr}</td><td>[ ] [ ] [ ]</td></tr>"
            truth_rows.append([c, rid, text, pr, "[ ] [ ] [ ]"])
    html += "</table><p><small>Submit responses by 31 July 2026 to procurement@northwind.example.</small></p>"
    save_pdf(html, "rfp_requirements_matrix.pdf")
    write_truth("rfp_requirements_matrix.pdf", "# Request for Proposal RFP-2026-014: Requirements Matrix\n\nVendors must mark each requirement as Compliant (C), Partially compliant (P) or Not compliant (N).\n\n" + rows_md(truth_rows)
                + "\n\nSubmit responses by 31 July 2026 to procurement@northwind.example.")


def r9_minutes() -> None:
    acts = [["1", "Approve revised capex plan for Line C", "R. Kulkarni", "15 Jul 2026", "Open"], ["2", "Share supplier audit findings", "A. Rao", "30 Jun 2026", "Closed"], ["3", "Update risk register for currency exposure", "S. Iyer", "31 Jul 2026", "Open"]]
    html = ("<h1>Northwind Industrial Supplies: Minutes of the Board Meeting</h1><p>Date: 12 June 2026. Venue: Head office, Pune. Chair: R. Kulkarni.</p><h2>1. Attendance</h2><p>Present: R. Kulkarni, A. Rao, S. Iyer, N. Shah. Apologies: M. Joshi.</p>"
            "<h2>2. Approval of previous minutes</h2><p>The minutes of the meeting held on 14 March 2026 were approved without change.</p><h2>3. Financial results</h2>"
            "<p>The CFO reported revenue of INR 482.6 crore for the year, an increase of eleven percent, and a gross margin of 14.2 percent. The Board noted the results.</p>"
            "<h2>4. Resolutions</h2><p>RESOLVED THAT the capital expenditure of INR 12 crore for Line C be approved, subject to final vendor quotes.</p><h2>5. Action items</h2>"
            + m.html_table(["No.", "Action", "Owner", "Due", "Status"], acts) + "<p>There being no other business, the meeting closed at 17:30.</p>")
    save_pdf(html, "board_minutes.pdf")
    write_truth("board_minutes.pdf", "# Northwind Industrial Supplies: Minutes of the Board Meeting\n\nDate: 12 June 2026. Venue: Head office, Pune. Chair: R. Kulkarni.\n\n## 1. Attendance\n\nPresent: R. Kulkarni, A. Rao, S. Iyer, N. Shah. Apologies: M. Joshi.\n\n"
                "## 2. Approval of previous minutes\n\nThe minutes of the meeting held on 14 March 2026 were approved without change.\n\n## 3. Financial results\n\nThe CFO reported revenue of INR 482.6 crore for the year, an increase of eleven percent, "
                "and a gross margin of 14.2 percent. The Board noted the results.\n\n## 4. Resolutions\n\nRESOLVED THAT the capital expenditure of INR 12 crore for Line C be approved, subject to final vendor quotes.\n\n## 5. Action items\n\n"
                + rows_md([["No.", "Action", "Owner", "Due", "Status"]] + acts) + "\n\nThere being no other business, the meeting closed at 17:30.")


def r10_paper() -> None:
    (e.IMG / "bar.png").write_bytes(m.chart_png("bar"))
    abstract = "We study the effect of predictive maintenance on unplanned downtime in discrete manufacturing plants. Across twelve plants, downtime fell by thirty one percent."
    left = ("<h2>1. Introduction</h2><p>Unplanned downtime remains the largest single source of lost output in discrete manufacturing. Condition monitoring is widely deployed but rarely linked to maintenance planning.</p>"
            "<h2>2. Method</h2><p>We instrumented 214 machines with vibration and temperature sensors and trained a gradient boosted model to predict bearing failure seven days ahead.</p>")
    res = [["Plant group", "Machines", "Downtime before (h)", "Downtime after (h)"], ["Pumps", "82", "1,420", "960"], ["Gearboxes", "64", "1,115", "790"], ["Compressors", "68", "1,360", "905"]]
    right = ("<h2>3. Results</h2><p>Table 1 reports downtime before and after the programme.</p>" + m.html_table(res[0], res[1:], right=(1, 2, 3)) + "<p><small>Table 1. Unplanned downtime by plant group.</small></p>"
             "<img src='bar.png' width='235'><p><small>Figure 1. Revenue by quarter (USD m).</small></p><h2>4. Conclusion</h2><p>Predictive maintenance reduced downtime in every plant group.</p>")
    doc = fitz.open()
    pg = doc.new_page()
    pg.insert_htmlbox(fitz.Rect(40, 36, 555, 76), "<h1>Predictive Maintenance and Unplanned Downtime</h1>", css=CSS)
    pg.insert_htmlbox(fitz.Rect(40, 80, 555, 120), f"<p><i>Abstract.</i> {abstract}</p>", css=CSS)
    pg.insert_htmlbox(fitz.Rect(40, 130, 288, 780), left, css=CSS)
    pg.insert_htmlbox(fitz.Rect(305, 130, 555, 780), right, css=CSS, archive=fitz.Archive(str(e.IMG)))
    doc.save(REAL / "research_two_column.pdf")
    write_truth("research_two_column.pdf", f"# Predictive Maintenance and Unplanned Downtime\n\nAbstract. {abstract}\n\n## 1. Introduction\n\nUnplanned downtime remains the largest single source of lost output in discrete manufacturing. "
                "Condition monitoring is widely deployed but rarely linked to maintenance planning.\n\n## 2. Method\n\nWe instrumented 214 machines with vibration and temperature sensors and trained a gradient boosted model to predict bearing failure seven days ahead.\n\n"
                "## 3. Results\n\nTable 1 reports downtime before and after the programme.\n\n" + rows_md(res) + "\n\nTable 1. Unplanned downtime by plant group.\n\nFigure 1. Revenue by quarter (USD m).\n\n## 4. Conclusion\n\n"
                "Predictive maintenance reduced downtime in every plant group.\n\n## Bar chart: Revenue by quarter\n\n| Quarter | Revenue |\n|---|---|\n| Q1 | 120 |\n| Q2 | 150 |\n| Q3 | 200 |\n| Q4 | 310 |")


def r11_phone_scan() -> None:
    src = fitz.open(REAL / "purchase_order.pdf")
    base = Image.open(io.BytesIO(src[0].get_pixmap(dpi=170).tobytes("png"))).convert("RGB")
    im = m.degrade(base, angle=2.6, noise=14, blur=0.9, contrast=0.85)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=55)
    out = fitz.open()
    pg = out.new_page(width=595, height=842)
    pg.insert_image(pg.rect, stream=buf.getvalue())
    out.save(REAL / "scanned_purchase_order_phone.pdf")
    write_truth("scanned_purchase_order_phone.pdf", (REAL / "purchase_order.pdf.truth.md").read_text(encoding="utf-8"))


def r12_excel() -> None:
    import xlsxwriter

    wb = xlsxwriter.Workbook(str(REAL / "hr_headcount_report.xlsx"))
    b, num, pct = wb.add_format({"bold": True, "align": "center", "bg_color": "#D9E2F3", "border": 1}), wb.add_format({"num_format": "#,##0", "border": 1}), wb.add_format({"num_format": "0.0%", "border": 1})
    cell = wb.add_format({"border": 1})
    ws = wb.add_worksheet("Headcount")
    ws.merge_range("A1:G1", "Headcount and attrition by function, FY2026", wb.add_format({"bold": True, "font_size": 14}))
    ws.merge_range("B3:C3", "Headcount", b); ws.merge_range("D3:E3", "Joiners / leavers", b)
    ws.write("A3", "Function", b); ws.write("F3", "Attrition %", b); ws.write("G3", "Comment", b)
    for col, h in zip("BCDE", ["Opening", "Closing", "Joiners", "Leavers"]):
        ws.write(f"{col}4", h, b)
    ws.write("A4", "", b); ws.write("F4", "", b); ws.write("G4", "", b)
    data = [("Operations", 820, 842, 96, 74), ("Sales", 210, 205, 38, 43), ("Engineering", 340, 372, 61, 29), ("Finance", 64, 66, 7, 5), ("HR", 28, 29, 4, 3)]
    truth = [["Function", "Headcount Opening", "Headcount Closing", "Joiners", "Leavers", "Attrition %", "Comment"]]
    for i, (fn, o, c, j, l) in enumerate(data):
        r = 5 + i
        ws.write(f"A{r}", fn, cell)
        for col, v in zip("BCDE", (o, c, j, l)):
            ws.write(f"{col}{r}", v, num)
        att = round(l / ((o + c) / 2), 4)
        ws.write_formula(f"F{r}", f"=E{r}/AVERAGE(B{r}:C{r})", pct, att)
        note = "High attrition, review exit survey" if att > 0.15 else ""
        ws.write(f"G{r}", note, cell)
        truth.append([fn, o, c, j, l, f"{att * 100:.1f}%", note])
    tot = [sum(x[k] for x in data) for k in range(1, 5)]
    ws.write("A10", "Total", b)
    for col, v in zip("BCDE", tot):
        ws.write_formula(f"{col}10", f"=SUM({col}5:{col}9)", num, v)
    tatt = round(tot[3] / ((tot[0] + tot[1]) / 2), 4)
    ws.write_formula("F10", "=E10/AVERAGE(B10:C10)", pct, tatt); ws.write("G10", "", cell)
    truth.append(["Total"] + tot + [f"{tatt * 100:.1f}%", ""])
    ws.set_column("A:A", 18); ws.set_column("G:G", 34)
    ch = wb.add_chart({"type": "column"})
    ch.add_series({"name": "Closing headcount", "categories": "=Headcount!$A$5:$A$9", "values": "=Headcount!$C$5:$C$9"})
    ch.set_title({"name": "Closing headcount by function"})
    ws.insert_chart("A13", ch)
    ws2 = wb.add_worksheet("Notes")
    ws2.write("A1", "Attrition is leavers divided by average headcount. Contractors are excluded.")
    wb.close()
    write_truth("hr_headcount_report.xlsx", "# Headcount and attrition by function, FY2026\n\n" + rows_md(truth) + "\n\n# Notes\n\nAttrition is leavers divided by average headcount. Contractors are excluded.\n\n"
                "## Column chart: Closing headcount by function\n\n| Function | Closing headcount |\n|---|---|\n" + "\n".join(f"| {d[0]} | {d[2]} |" for d in data))


def r13_word() -> None:
    from docx import Document
    from docx.enum.text import WD_BREAK  # noqa: F401
    from docx.shared import Inches

    (e.IMG / "bar.png").write_bytes(m.chart_png("bar"))
    doc = Document()
    doc.sections[0].header.paragraphs[0].text = "Northwind Industrial Supplies | SOP-014 Goods Receipt"
    doc.sections[0].footer.paragraphs[0].text = "Uncontrolled when printed. Revision 3, effective 01 May 2026"
    doc.add_heading("Standard Operating Procedure: Goods Receipt", 0)
    doc.add_heading("1. Purpose", 1)
    doc.add_paragraph("This procedure describes how incoming goods are received, inspected and booked into stock.")
    doc.add_heading("2. Procedure", 1)
    for t in ("Check the delivery note against the purchase order.", "Inspect packaging for damage and record any damage on the delivery note.", "Move the goods to the quarantine bay."):
        doc.add_paragraph(t, style="List Number")
    for t in ("Count cartons.", "Photograph any damage."):
        doc.add_paragraph(t, style="List Bullet")
    doc.add_heading("3. Responsibilities", 1)
    tb = doc.add_table(rows=4, cols=3)
    tb.style = "Table Grid"
    for j, h in enumerate(["Step", "Owner", "Record"]):
        tb.cell(0, j).text = h
    tb.cell(1, 0).text = "Receipt"; tb.cell(1, 1).text = "Store keeper"; tb.cell(1, 2).text = "GRN form"
    tb.cell(2, 0).text = "Inspection"; tb.cell(2, 1).merge(tb.cell(3, 1)).text = "Quality inspector"; tb.cell(2, 2).text = "Inspection report"
    tb.cell(3, 0).text = "Release"; tb.cell(3, 2).text = "Stock ledger entry"
    doc.add_picture(str(e.IMG / "bar.png"), width=Inches(3.2))
    doc.add_paragraph("Figure 1. Receipts by quarter.")
    doc.save(REAL / "sop_goods_receipt.docx")
    write_truth("sop_goods_receipt.docx", "Northwind Industrial Supplies | SOP-014 Goods Receipt\n\n# Standard Operating Procedure: Goods Receipt\n\n## 1. Purpose\n\nThis procedure describes how incoming goods are received, inspected and booked into stock.\n\n"
                "## 2. Procedure\n\n1. Check the delivery note against the purchase order.\n2. Inspect packaging for damage and record any damage on the delivery note.\n3. Move the goods to the quarantine bay.\n- Count cartons.\n- Photograph any damage.\n\n"
                "## 3. Responsibilities\n\n" + rows_md([["Step", "Owner", "Record"], ["Receipt", "Store keeper", "GRN form"], ["Inspection", "Quality inspector", "Inspection report"], ["Release", "Quality inspector", "Stock ledger entry"]])
                + "\n\nFigure 1. Receipts by quarter.\n\nUncontrolled when printed. Revision 3, effective 01 May 2026")


def r14_pptx() -> None:
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.util import Inches

    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = "Q2 Business Review: Revenue"
    cd = CategoryChartData(); cd.categories = ["North", "South", "East", "West"]; cd.add_series("Revenue (INR crore)", (142, 96, 118, 87))
    s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.5), Inches(1.5), Inches(5), Inches(3.5), cd)
    tb = s.shapes.add_table(4, 3, Inches(5.8), Inches(1.6), Inches(3.8), Inches(1.6)).table
    rows = [["Region", "Revenue", "Growth"], ["North", "142", "+12%"], ["South", "96", "+6%"], ["East", "118", "+9%"]]
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            tb.cell(i, j).text = v
    s.notes_slide.notes_text_frame.text = "North grew fastest; South needs a recovery plan."
    s2 = prs.slides.add_slide(prs.slide_layouts[1])
    s2.shapes.title.text = "Next steps"
    s2.placeholders[1].text = "Approve Line C capex\nClose supplier audit findings\nLaunch predictive maintenance in two more plants"
    prs.save(REAL / "quarterly_review.pptx")
    write_truth("quarterly_review.pptx", "# Q2 Business Review: Revenue\n\n" + rows_md(rows) + "\n\n## Column chart: Revenue (INR crore)\n\n| Region | Revenue |\n|---|---|\n| North | 142 |\n| South | 96 |\n| East | 118 |\n| West | 87 |\n\n"
                "Notes: North grew fastest; South needs a recovery plan.\n\n# Next steps\n\n- Approve Line C capex\n- Close supplier audit findings\n- Launch predictive maintenance in two more plants")


def main() -> None:
    REAL.mkdir(parents=True, exist_ok=True)
    e.IMG.mkdir(exist_ok=True)
    for fn in (r1_bank, r2_income, r3_po, r4_payslip, r5_lab, r6_utility, r7_bol, r8_rfp, r9_minutes, r10_paper, r11_phone_scan, r12_excel, r13_word, r14_pptx):
        fn()
        print("done", fn.__name__, flush=True)
    files = [p for p in REAL.iterdir() if p.is_file() and not p.name.endswith(".truth.md")]
    print(f"{len(files)} documents written to {REAL}")


if __name__ == "__main__":
    main()
