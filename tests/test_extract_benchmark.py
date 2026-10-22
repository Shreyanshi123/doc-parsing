"""Smart Extract, the live benchmark and the isolated-parser timeout."""
import tempfile
import unittest
from pathlib import Path

from app import benchmark
from app.config import settings
from app.isolate import ParserTimeout, run_isolated
from app.models import ParseOptions

ROOT = Path(__file__).resolve().parent.parent
DIGITAL = ROOT / "eval" / "digital.pdf"


def _cmp(name, rows, group_pages=1):
    """A minimal compare_parsers() result."""
    return {"file_name": name, "file_type": "pdf", "reference_kind": "your reference text",
            "profile": {"classification": "digital", "traits": ["tables"], "page_count": group_pages}, "results": rows}


def _ok(p, total, m, ms=1000):
    return {"parser": p, "cost": "free", "status": "ok", "elapsed_ms": ms, "pages": 1, "scorecard": m, "total": total}


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self._old = settings.data_dir
        self._tmp = tempfile.TemporaryDirectory()
        settings.data_dir = Path(self._tmp.name)

    def tearDown(self):
        settings.data_dir = self._old
        self._tmp.cleanup()

    def test_unscored_run_is_not_recorded(self):
        self.assertIsNone(benchmark.record(_cmp("a.pdf", [{"parser": "pymupdf", "status": "ok", "elapsed_ms": 5}])))

    def test_crashed_parser_counts_as_zero(self):
        card = {"Text Accuracy": 4.0, "Completeness": 4.0}
        benchmark.record(_cmp("a.pdf", [_ok("good", 8.0, card),
                                        {"parser": "bad", "cost": "free", "status": "error", "elapsed_ms": 9, "error": "timeout after 5s"}]))
        rows = {r["p"]: r for r in benchmark.aggregate()["groups"]["Overall"]["rows"]}
        self.assertEqual(rows["bad"]["failed"], 1)
        self.assertEqual(rows["bad"]["m"][0], 0.0)      # tested on this document -> 0, not skipped
        self.assertIsNone(rows["bad"]["m"][2])          # nothing could test charts -> still not applicable

    def test_same_document_replaces_old_result(self):
        card = {"Text Accuracy": 3.0}
        benchmark.record(_cmp("a.pdf", [_ok("p", 3.0, card)]))
        benchmark.record(_cmp("a.pdf", [_ok("p", 4.0, {"Text Accuracy": 4.0})]))
        self.assertEqual(benchmark.aggregate()["groups"]["Overall"]["docs"], 1)

    def test_groups(self):
        self.assertEqual(benchmark.group_of({"classification": "scanned"}, "pdf"), "scanned")
        self.assertEqual(benchmark.group_of({"classification": "digital", "traits": ["figures", "tables"]}, "pdf"), "digital + charts/images")
        self.assertEqual(benchmark.group_of({"classification": "native_office"}, "docx"), "other")


def _in_fresh_process(code: str) -> dict:
    """importing pymupdf4llm changes PyMuPDF's behaviour for the whole process, so keep it away from the other tests"""
    import json
    import os
    import subprocess
    import sys

    r = subprocess.run([sys.executable, "-W", "ignore", "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=300,
                       env={**os.environ, "PYTHONPATH": str(ROOT)})
    assert r.returncode == 0, r.stderr[-800:]
    return json.loads(r.stdout.strip().splitlines()[-1])


@unittest.skipUnless(DIGITAL.exists(), "needs eval/digital.pdf")
class ExtractTests(unittest.TestCase):
    def test_digital_pdf_is_cut_into_parts(self):
        r = _in_fresh_process(
            "import json\nfrom app.extract import extract_document\nfrom app.models import ParseOptions\n"
            "r = extract_document(open('eval/digital.pdf','rb').read(), 'digital.pdf', ParseOptions())\n"
            "print(json.dumps({'kinds': sorted({s['kind'] for s in r['segments']}), 'md': r['markdown'],"
            "'complete': all(s['why'] and s['parser'] and s['tried'] for s in r['segments'])}))")
        self.assertIn("heading", r["kinds"])
        self.assertIn("table", r["kinds"])
        self.assertIn("Quarterly Sales Report", r["md"])
        self.assertTrue(r["complete"])

    def test_progress_events(self):
        r = _in_fresh_process(
            "import json\nfrom app.extract import extract_document\nfrom app.models import ParseOptions\nev = []\n"
            "extract_document(open('eval/digital.pdf','rb').read(), 'digital.pdf', ParseOptions(), progress=ev.append)\n"
            "print(json.dumps({'first': ev[0]['event'], 'segments': sum(e['event'] == 'segment' for e in ev)}))")
        self.assertEqual(r["first"], "start")
        self.assertGreater(r["segments"], 0)

@unittest.skipUnless(DIGITAL.exists(), "needs eval/digital.pdf")
class IsolateTests(unittest.TestCase):
    def test_runs_in_child_process(self):
        d = run_isolated("pymupdf", DIGITAL.read_bytes(), "digital.pdf", "pdf", ParseOptions(), 120)
        self.assertIn("Quarterly", d.markdown)

    def test_timeout(self):
        with self.assertRaises(ParserTimeout):
            run_isolated("docling", DIGITAL.read_bytes(), "digital.pdf", "pdf", ParseOptions(), 1)

    def test_unknown_parser_is_an_error_not_a_hang(self):
        with self.assertRaises(RuntimeError):
            run_isolated("nope", DIGITAL.read_bytes(), "digital.pdf", "pdf", ParseOptions(), 60)


if __name__ == "__main__":
    unittest.main()
