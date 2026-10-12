"""Background worker threads: poll the SQL table, process jobs, write status back."""
from __future__ import annotations

import json
import logging
import threading
import time

from app.config import settings
from app.jobs.store import JobStore
from app.models import ParseOptions
from app.pipeline import build_output, parse_bytes
from app.storage.factory import read_document
from app.storage.output_store import get_output_store

log = logging.getLogger("worker")


def process_job(store: JobStore, job: dict) -> None:
    """blob read -> parser -> output upload -> status update"""
    try:
        data = read_document(job["source_uri"])                                   # blob read
        result = parse_bytes(data, job["file_name"], ParseOptions.from_dict(job["options"]), job["parser"])  # parser
        payload = build_output(result, file_id=job["file_id"], tenant_id=job["tenant_id"], include_images=True)
        uri = get_output_store().save(                                            # output upload
            job["tenant_id"], job["file_id"], job["job_id"], json.dumps(payload, ensure_ascii=False).encode("utf-8")
        )
        store.complete(job["job_id"], result.routing.selected, uri)               # status update
        log.info("job %s COMPLETED via %s", job["job_id"], result.routing.selected)
    except Exception as e:  # noqa: BLE001
        log.exception("job %s FAILED", job["job_id"])
        store.fail(job["job_id"], f"{type(e).__name__}: {e}")


class WorkerPool:
    def __init__(self, store: JobStore):
        self.store = store
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        n = self.store.requeue_stuck()
        if n:
            log.info("re-queued %d stuck jobs", n)
        for i in range(max(1, settings.worker_threads)):
            t = threading.Thread(target=self._loop, name=f"worker-{i}", daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.is_set():
            job = self.store.claim_next()
            if job is None:
                time.sleep(settings.worker_poll_sec)
                continue
            process_job(self.store, job)
