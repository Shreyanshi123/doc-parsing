"""
FastAPI entrypoint.

                     ┌─────────────── synchronous (quick POC testing) ───────────────┐
  UPLOAD  (now)  →   POST /api/parse/upload      POST /api/compare/upload
  BLOB URL (later) → POST /api/parse             POST /api/compare
                     ├─────────────── asynchronous (production-like flow) ───────────┤
  UPLOAD         →   POST /api/jobs/upload
  BLOB URL       →   POST /api/jobs            GET /api/jobs/{id}   GET /api/jobs/{id}/result
                     └───────────────────────────────────────────────────────────────┘
  GET /api/providers  -> every parser + availability
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from app import benchmark
from app.compare import compare_parsers, report_markdown
from app.config import settings
from app.extract import extract_document
from app.jobs.store import COMPLETED, JobStore
from app.jobs.worker import WorkerPool
from app.models import ParseOptions
from app.parsers import list_parsers
from app.pipeline import ParseFailed, build_output, parse_bytes
from app.routing.file_type import UnsupportedFileType
from app.routing.router import NoParserAvailable
from app.schemas import CompareRequest, OptionsIn, ParseRequest
from app.storage.base import StorageError
from app.storage.factory import read_document
from app.storage.output_store import get_output_store

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("api")

store = JobStore()
workers = WorkerPool(store)


@asynccontextmanager
async def lifespan(app: FastAPI):
    workers.start()
    yield
    workers.stop()


app = FastAPI(title="Document Parsing POC", version="0.1.0", lifespan=lifespan)

# Known user-facing errors -> proper HTTP codes
_ERRORS = {
    UnsupportedFileType: 415,
    NoParserAvailable: 422,
    StorageError: 404,
    ParseFailed: 500,
    KeyError: 400,
}


def _http(e: Exception) -> HTTPException:
    if isinstance(e, HTTPException):
        return e
    for cls, code in _ERRORS.items():
        if isinstance(e, cls):
            return HTTPException(code, str(e))
    log.exception("unexpected error")
    return HTTPException(500, f"{type(e).__name__}: {e}")


def _opts(options_json: str) -> OptionsIn:
    try:
        return OptionsIn(**json.loads(options_json or "{}"))
    except Exception as e:
        raise HTTPException(400, f"options must be a JSON object: {e}")


def _remember(cmp: dict) -> None:
    """Every scored comparison also feeds the Benchmark tab."""
    try:
        rec = benchmark.record(cmp)
        cmp["benchmark_run"] = rec["id"] if rec else None
    except Exception:  # noqa: BLE001 - the benchmark must never break a comparison
        log.exception("could not save benchmark record")


async def _save_upload(file: UploadFile) -> tuple[bytes, str, str]:
    """Reads the upload and also stores a copy in data/uploads (so it can be queued as a job)."""
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    name = Path(file.filename or "upload.bin").name
    path = settings.uploads_dir / f"{uuid.uuid4().hex[:8]}_{name}"
    path.write_bytes(data)
    return data, name, str(path)


# ----------------------------------------------------------------------------- info
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/providers")
def providers():
    return list_parsers()


# ----------------------------------------------------------------------------- sync: upload
@app.post("/api/parse/upload")
async def parse_upload(
    file: UploadFile = File(...),
    tenant_id: str = Form("local-test"),
    file_id: str = Form(""),
    parser: str = Form("auto"),
    options: str = Form("{}"),
    include_images: bool = Form(False),
):
    data, name, _ = await _save_upload(file)
    try:
        opts = _opts(options).to_options()
        # parsing is CPU/IO heavy -> run off the event loop so other requests stay responsive
        res = await run_in_threadpool(parse_bytes, data, name, opts, parser)
        return build_output(res, file_id=file_id or name, tenant_id=tenant_id, include_images=include_images)
    except Exception as e:
        raise _http(e)


@app.post("/api/compare/upload")
async def compare_upload(
    file: UploadFile = File(...),
    options: str = Form("{}"),
    reference_text: str = Form(""),
    parsers: str = Form(""),
    include_paid: bool = Form(False),
):
    data = await file.read()
    name = Path(file.filename or "upload.bin").name
    try:
        cmp = await run_in_threadpool(
            compare_parsers, data, name, _opts(options).to_options(), reference_text or None,
            [p.strip() for p in parsers.split(",") if p.strip()] or None, include_paid,
        )
        cmp["report_markdown"] = report_markdown(cmp)
        _remember(cmp)
        return cmp
    except Exception as e:
        raise _http(e)


@app.post("/api/compare/upload/stream")
async def compare_upload_stream(
    file: UploadFile = File(...),
    options: str = Form("{}"),
    reference_text: str = Form(""),
    parsers: str = Form(""),
    include_paid: bool = Form(False),
):
    """Same as /api/compare/upload, but streams one JSON line per step (start, running, parser, scoring) and ends with {"event":"done","result":...}.
    The UI uses it to show live progress; the plain endpoint above is unchanged."""
    data = await file.read()
    name = Path(file.filename or "upload.bin").name
    loop = asyncio.get_running_loop()
    q: asyncio.Queue = asyncio.Queue()

    def push(item):
        loop.call_soon_threadsafe(q.put_nowait, item)

    def work():
        try:
            cmp = compare_parsers(data, name, _opts(options).to_options(), reference_text or None,
                                  [p.strip() for p in parsers.split(",") if p.strip()] or None, include_paid, progress=push)
            cmp["report_markdown"] = report_markdown(cmp)
            _remember(cmp)
            push({"event": "done", "result": cmp})
        except Exception as e:  # noqa: BLE001
            push({"event": "error", "detail": str(e)})
        push(None)

    threading.Thread(target=work, daemon=True).start()

    async def gen():
        while True:
            item = await q.get()
            if item is None:
                break
            yield json.dumps(item, default=str) + chr(10)

    return StreamingResponse(gen(), media_type="application/x-ndjson", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ----------------------------------------------------------------------------- benchmark (built from comparison runs)
@app.get("/api/benchmark")
def benchmark_get():
    return benchmark.aggregate()


@app.delete("/api/benchmark/runs/{run_id}")
def benchmark_delete(run_id: str):
    return {"deleted": benchmark.delete(run_id)}


@app.delete("/api/benchmark")
def benchmark_clear():
    benchmark.clear()
    return {"deleted": "all"}


# ----------------------------------------------------------------------------- smart extract (best parser per part)
@app.post("/api/extract/upload")
async def extract_upload(
    file: UploadFile = File(...),
    options: str = Form("{}"),
    include_paid: bool = Form(False),
    mode: str = Form("document"),
):
    """mode "document": one parser (the scorecard's pick for this type of document) reads the whole file.
    mode "part": cuts the document into parts (headings, text, tables, figures, scanned pages) and reads each with the best parser for it."""
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    name = Path(file.filename or "upload.bin").name
    try:
        return await run_in_threadpool(extract_document, data, name, _opts(options).to_options(), include_paid, None, mode)
    except Exception as e:
        raise _http(e)


@app.post("/api/extract/upload/stream")
async def extract_upload_stream(
    file: UploadFile = File(...),
    options: str = Form("{}"),
    include_paid: bool = Form(False),
    mode: str = Form("document"),
):
    """Same as /api/extract/upload, but streams one JSON line per step and ends with {"event":"done","result":...}."""
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    name = Path(file.filename or "upload.bin").name
    opts = _opts(options).to_options()
    loop = asyncio.get_running_loop()
    q: asyncio.Queue = asyncio.Queue()

    def push(item):
        loop.call_soon_threadsafe(q.put_nowait, item)

    def work():
        try:
            push({"event": "done", "result": extract_document(data, name, opts, include_paid, progress=push, mode=mode)})
        except Exception as e:  # noqa: BLE001
            push({"event": "error", "detail": f"{type(e).__name__}: {e}"})
        push(None)

    threading.Thread(target=work, daemon=True).start()

    async def gen():
        while True:
            item = await q.get()
            if item is None:
                break
            yield json.dumps(item, default=str) + chr(10)

    return StreamingResponse(gen(), media_type="application/x-ndjson", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ----------------------------------------------------------------------------- sync: payload (blob URL / path)
@app.post("/api/parse")
def parse_payload(req: ParseRequest):
    try:
        data = read_document(req.file_path)
        res = parse_bytes(data, req.file_name, req.options.to_options(), req.parser)
        return build_output(res, file_id=req.file_id, tenant_id=req.tenant_id, include_images=req.include_images)
    except Exception as e:
        raise _http(e)


@app.post("/api/compare")
def compare_payload(req: CompareRequest):
    try:
        data = read_document(req.file_path)
        cmp = compare_parsers(data, req.file_name, req.options.to_options(), req.reference_text, req.parsers, req.include_paid)
        cmp["report_markdown"] = report_markdown(cmp)
        _remember(cmp)
        return cmp
    except Exception as e:
        raise _http(e)


# ----------------------------------------------------------------------------- async jobs
@app.post("/api/jobs", status_code=202)
def create_job(req: ParseRequest):
    """Request JSON -> API -> SQL insert. A worker thread does the rest."""
    job_id = store.create(
        tenant_id=req.tenant_id, file_id=req.file_id, file_name=req.file_name,
        source_uri=req.file_path, parser=req.parser, options=req.options.model_dump(),
    )
    return {"job_id": job_id, "status": "QUEUED"}


@app.post("/api/jobs/upload", status_code=202)
async def create_job_upload(
    file: UploadFile = File(...),
    tenant_id: str = Form("local-test"),
    file_id: str = Form(""),
    parser: str = Form("auto"),
    options: str = Form("{}"),
):
    _, name, saved = await _save_upload(file)
    job_id = store.create(
        tenant_id=tenant_id, file_id=file_id or name, file_name=name, source_uri=saved,
        parser=parser, options=_opts(options).model_dump(),
    )
    return {"job_id": job_id, "status": "QUEUED"}


@app.get("/api/jobs")
def list_jobs(tenant_id: Optional[str] = None, limit: int = 50):
    return store.list(tenant_id, limit)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = store.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job


@app.get("/api/jobs/{job_id}/result")
def get_job_result(job_id: str):
    job = store.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    if job["status"] != COMPLETED:
        raise HTTPException(409, f"job is {job['status']}" + (f": {job['error']}" if job["error"] else ""))
    return JSONResponse(content=json.loads(get_output_store().load(job["output_uri"])))


# ----------------------------------------------------------------------------- UI
_static = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=_static), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(_static / "index.html")
