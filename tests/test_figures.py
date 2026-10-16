"""Tests for the smart_pdf parser: finding charts / diagrams and merging what the vision model returns.

The vision model is replaced by a fake, so these tests are free and need no network.
Run with:  python -m pytest tests/test_figures.py -v
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="docpoc_"))

import pymupdf  # noqa: E402

import make_chart_sample as sample  # noqa: E402
from app.config import settings  # noqa: E402
from app.models import ParseOptions  # noqa: E402
from app.normalizer import normalize_document  # noqa: E402
from app.parsers.smart_pdf_parser import SmartPdfParser  # noqa: E402
from app.vision import FigureText  # noqa: E402


def chart_pdf() -> bytes:
    doc = pymupdf.open()
    p = doc.new_page()
    p.insert_text((72, 80), "Annual Revenue Report", fontsize=24)
    p.insert_textbox(pymupdf.Rect(72, 100, 520, 160), "Sales grew in every year between 2021 and 2025.", fontsize=11)
    sample.bar_chart(p)
    p.insert_image(pymupdf.Rect(340, 175, 540, 305), stream=sample.line_chart_png())
    p.insert_text((72, 415), "Revenue by region (USD m)", fontsize=12)
    sample.table(p)
    p.insert_text((72, 545), "Reporting process", fontsize=12)
    sample.flowchart(p)
    return doc.tobytes()


def parse(backend_name, describe):
    with mock.patch("app.parsers.smart_pdf_parser.pick_backend", return_value=backend_name), \
         mock.patch("app.parsers.smart_pdf_parser.describe_figure", side_effect=describe):
        return normalize_document(SmartPdfParser().parse(chart_pdf(), "c.pdf", "pdf", ParseOptions()))


def fake_vision(png):
    return FigureText("bar chart", "| Year | Revenue |\n|---|---|\n| 2025 | 400 |", "fake")


class SmartPdfTests(unittest.TestCase):
    def test_finds_all_three_figures_and_keeps_the_real_table(self):
        doc = parse(None, fake_vision)
        figures = [e for p in doc.pages for e in p.elements if e.content_type == "image"]
        self.assertEqual(len(figures), 3)                       # bar chart (drawn), line chart (picture), flowchart
        tables = [e for p in doc.pages for e in p.elements if e.content_type == "table"]
        self.assertEqual(len(tables), 1)                        # the chart's grid lines are not a table
        self.assertIn("APAC", tables[0].content)

    def test_without_a_vision_model_figures_are_marked_and_warned(self):
        doc = parse(None, fake_vision)
        self.assertIn("no vision model", doc.markdown)
        self.assertTrue(any("no vision model" in w for w in doc.warnings))
        self.assertEqual(doc.metadata["figures_read"], 0)
        self.assertIn("120 150 200 310 400", doc.markdown)     # the chart's own text is kept when nothing reads it

    def test_vision_result_replaces_the_text_inside_the_chart(self):
        doc = parse("fake", fake_vision)
        self.assertEqual(doc.metadata["figures_read"], 3)
        self.assertIn("Figure (page 1, bar chart)", doc.markdown)
        self.assertIn("| 2025 | 400 |", doc.markdown)
        self.assertNotIn("120 150 200 310 400", doc.markdown)   # replaced by the model's table
        self.assertIn("Annual Revenue Report", doc.markdown)    # ordinary text is untouched

    def test_figure_sits_in_reading_order(self):
        md = parse("fake", fake_vision).markdown
        self.assertLess(md.index("Annual Revenue Report"), md.index("Figure (page 1"))
        self.assertLess(md.index("Figure (page 1"), md.index("Reporting process"))

    def test_a_failing_vision_call_does_not_fail_the_page(self):
        def boom(png):
            raise RuntimeError("quota exceeded")

        doc = parse("fake", boom)
        self.assertIn("Annual Revenue Report", doc.markdown)
        self.assertIn("could not be read", doc.markdown)
        self.assertTrue(any("quota exceeded" in w for w in doc.warnings))

    def test_figure_limit_caps_vision_calls(self):
        calls = []

        def counting(png):
            calls.append(1)
            return fake_vision(png)

        old = settings.max_figures
        settings.max_figures = 1
        try:
            doc = parse("fake", counting)
        finally:
            settings.max_figures = old
        self.assertEqual(len(calls), 1)
        self.assertIn("skipped (limit of 1 figures", doc.markdown)

    def test_text_is_not_dropped_when_the_model_says_it_is_not_a_chart(self):
        def screenshot(png):
            return FigureText("screenshot", "A web page.", "fake")

        doc = parse("fake", screenshot)
        self.assertIn("120 150 200 310 400", doc.markdown)


if __name__ == "__main__":
    unittest.main()
