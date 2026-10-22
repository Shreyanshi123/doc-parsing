"""
Run one parser in a child process so a hang or a native crash cannot take the comparison down.

Why: a Python thread cannot be killed. One wedged engine (docling on a big scan, a JVM that ran out of
memory, Tesseract crashing) used to block "Compare all parsers" forever, with no way to tell a slow
engine from a stuck one. In a child process the run can be stopped at a time limit and the parser is
reported as "timeout after N s" while the others carry on. (Idea taken from the ParserBench project.)
"""
from __future__ import annotations

import dataclasses
import multiprocessing as mp
import queue
import time

from app.models import ParseOptions, ParsedDocument

# Engines that load big models, call native code or run a JVM. The light ones stay in-process (no start-up cost).
ISOLATED = {"docling", "easyocr", "opendataloader", "unstructured", "ocr", "vlm", "smart_pdf", "hybrid_pdf"}


class ParserTimeout(Exception):
    pass


def _child(q, name, data, file_name, file_type, opts):
    try:
        import app.parsers  # noqa: F401 - registers every parser in this new process
        from app.normalizer import normalize_document
        from app.parsers import get_parser_class

        q.put(("ok", normalize_document(get_parser_class(name)().parse(data, file_name, file_type, ParseOptions.from_dict(opts)))))
    except BaseException as e:  # noqa: BLE001 - report it, never die silently
        q.put(("error", f"{type(e).__name__}: {e}"))


def run_isolated(name: str, data: bytes, file_name: str, file_type: str, options: ParseOptions, timeout: int) -> ParsedDocument:
    """Parse in a child process. Raises ParserTimeout, or RuntimeError if the engine failed or crashed."""
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=_child, args=(q, name, data, file_name, file_type, dataclasses.asdict(options)), daemon=True)
    p.start()
    deadline = time.monotonic() + timeout if timeout else None
    try:
        while True:
            try:
                kind, payload = q.get(timeout=0.5)   # read BEFORE joining: a big result can fill the pipe and block the child
                break
            except queue.Empty:
                if deadline and time.monotonic() > deadline:
                    raise ParserTimeout(f"timeout after {timeout}s")
                if not p.is_alive():
                    try:
                        kind, payload = q.get(timeout=1)
                        break
                    except queue.Empty:
                        raise RuntimeError(f"process died (exit code {p.exitcode}): native crash in the engine")
    finally:
        if p.is_alive():
            p.terminate()
        p.join(5)
    if kind == "error":
        raise RuntimeError(payload)
    return payload
