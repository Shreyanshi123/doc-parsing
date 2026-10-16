"""Build eval/chart_sample.pdf: text + a drawn bar chart + a picture line chart + a flowchart + a table,
with the true chart values written to eval/chart_sample.values.md.

    python scripts/make_chart_sample.py
"""
from __future__ import annotations

import io
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

EVAL = Path(__file__).resolve().parent.parent / "eval"
YEARS = [2021, 2022, 2023, 2024, 2025]
REVENUE = [120, 150, 200, 310, 400]      # bar chart (drawn with vector shapes)
PROFIT = [12, 18, 30, 52, 80]            # line chart (inserted as a picture)
TABLE = [["Region", "2024", "2025"], ["APAC", "90", "150"], ["EMEA", "110", "140"], ["Americas", "110", "110"]]
FLOW = ["Collect data", "Clean data", "Publish report"]
FLOW_EXTRA = "Quality check"        # sits below "Clean data"


def bar_chart(page, x0=72, y0=200, w=250, h=170):
    base = y0 + h
    page.insert_text((x0, y0 - 14), "Revenue (USD m)", fontsize=10)
    page.draw_line((x0, y0), (x0, base), width=1)                       # y axis
    page.draw_line((x0, base), (x0 + w, base), width=1)                 # x axis
    for k in range(1, 5):                                                # grid lines
        y = base - k * h / 4.4
        page.draw_line((x0, y), (x0 + w, y), color=(0.8, 0.8, 0.8), width=0.5)
    slot = w / len(YEARS)
    for i, (yr, v) in enumerate(zip(YEARS, REVENUE)):
        bh = v / max(REVENUE) * (h - 20)
        bx = x0 + i * slot + slot * 0.2
        page.draw_rect(pymupdf.Rect(bx, base - bh, bx + slot * 0.6, base), color=(0.1, 0.3, 0.7), fill=(0.2, 0.45, 0.85))
        page.insert_text((bx + 4, base - bh - 4), str(v), fontsize=9)
        page.insert_text((bx + 2, base + 12), str(yr), fontsize=9)


def line_chart_png() -> bytes:
    W, H = 520, 340
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((10, 8), "Profit (USD m)", fill="black")
    l, t, r, b = 50, 40, W - 20, H - 40
    d.line([(l, t), (l, b), (r, b)], fill="black", width=2)
    pts = []
    for i, (yr, v) in enumerate(zip(YEARS, PROFIT)):
        x = l + i * (r - l) / (len(YEARS) - 1)
        y = b - v / max(PROFIT) * (b - t - 20)
        pts.append((x, y))
        d.text((x - 10, b + 8), str(yr), fill="black")
    d.line(pts, fill=(200, 40, 40), width=3)
    for (x, y), v in zip(pts, PROFIT):
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(200, 40, 40))
        d.text((x - 8, y - 20), str(v), fill="black")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def flowchart(page, x0=72, y=560):
    bw, bh, gap = 110, 44, 40
    for i, label in enumerate(FLOW):
        bx = x0 + i * (bw + gap)
        page.draw_rect(pymupdf.Rect(bx, y, bx + bw, y + bh), color=(0, 0, 0), fill=(0.93, 0.93, 0.98), width=1.2)
        page.insert_text((bx + 10, y + 27), label, fontsize=10)
        if i < len(FLOW) - 1:
            ax = bx + bw
            page.draw_line((ax, y + bh / 2), (ax + gap - 8, y + bh / 2), width=1.5)
            page.draw_polyline([(ax + gap - 8, y + bh / 2 - 5), (ax + gap, y + bh / 2), (ax + gap - 8, y + bh / 2 + 5)],
                               color=(0, 0, 0), fill=(0, 0, 0))
    # a second row: "Clean data" -> "Quality check"
    cx = x0 + (bw + gap)
    by = y + bh + 36
    page.draw_line((cx + bw / 2, y + bh), (cx + bw / 2, by - 8), width=1.5)
    page.draw_polyline([(cx + bw / 2 - 5, by - 8), (cx + bw / 2, by), (cx + bw / 2 + 5, by - 8)], color=(0, 0, 0), fill=(0, 0, 0))
    page.draw_rect(pymupdf.Rect(cx, by, cx + bw, by + bh), color=(0, 0, 0), fill=(0.98, 0.93, 0.93), width=1.2)
    page.insert_text((cx + 10, by + 27), FLOW_EXTRA, fontsize=10)


def table(page, x0=72, y=430):
    for r in TABLE:
        for i, c in enumerate(r):
            rect = pymupdf.Rect(x0 + i * 100, y, x0 + (i + 1) * 100, y + 22)
            page.draw_rect(rect, color=(0, 0, 0), width=0.6)
            page.insert_text((rect.x0 + 6, rect.y0 + 15), c, fontsize=10)
        y += 22


def main():
    doc = pymupdf.open()
    p = doc.new_page()
    p.insert_text((72, 80), "Annual Revenue Report", fontsize=24)
    p.insert_textbox(pymupdf.Rect(72, 100, 520, 160),
                     "Sales grew in every year between 2021 and 2025. The bar chart shows revenue and the "
                     "line chart shows profit, both in millions of US dollars.", fontsize=11)
    bar_chart(p)
    p.insert_image(pymupdf.Rect(340, 175, 540, 305), stream=line_chart_png())
    p.insert_text((72, 415), "Revenue by region (USD m)", fontsize=12)
    table(p)
    p.insert_text((72, 545), "Reporting process", fontsize=12)
    flowchart(p)
    doc.save(EVAL / "chart_sample.pdf")

    md = ["# Chart sample: true values", "", "## Bar chart (drawn with shapes): Revenue (USD m)", "",
          "| Year | Revenue |", "|---|---|"] + [f"| {y} | {v} |" for y, v in zip(YEARS, REVENUE)]
    md += ["", "## Line chart (picture): Profit (USD m)", "", "| Year | Profit |", "|---|---|"] + \
          [f"| {y} | {v} |" for y, v in zip(YEARS, PROFIT)]
    md += ["", "## Flowchart", "", " -> ".join(FLOW), f"{FLOW[1]} -> {FLOW_EXTRA}", "", "## Table", ""] + \
          ["| " + " | ".join(TABLE[0]) + " |", "|---|---|---|"] + ["| " + " | ".join(r) + " |" for r in TABLE[1:]]
    (EVAL / "chart_sample.values.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("wrote eval/chart_sample.pdf and eval/chart_sample.values.md")


if __name__ == "__main__":
    main()
