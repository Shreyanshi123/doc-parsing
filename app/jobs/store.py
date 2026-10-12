"""
SQL job table (SQLite for the POC). Mirrors the flow:
    Request JSON -> API -> SQL insert -> worker -> blob read -> parser -> output upload -> status update

To move to Azure SQL / Postgres later, replace this class only (same method names).
"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import settings

QUEUED, PROCESSING, COMPLETED, FAILED = "QUEUED", "PROCESSING", "COMPLETED", "FAILED"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id      TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    file_id     TEXT NOT NULL,
    file_name   TEXT NOT NULL,
    source_uri  TEXT NOT NULL,
    parser      TEXT NOT NULL DEFAULT 'auto',
    options     TEXT NOT NULL DEFAULT '{}',
    status      TEXT NOT NULL,
    engine      TEXT,
    output_uri  TEXT,
    error       TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status, created_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class JobStore:
    def __init__(self, path=None):
        self.path = str(path or settings.db_path)
        self._lock = threading.Lock()
        with self._conn() as c:
            c.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path, timeout=30)
        c.row_factory = sqlite3.Row
        return c

    # ---- API side ----
    def create(self, *, tenant_id, file_id, file_name, source_uri, parser="auto", options=None) -> str:
        job_id = uuid.uuid4().hex
        now = _now()
        with self._lock, self._conn() as c:
            c.execute(
                "INSERT INTO jobs(job_id,tenant_id,file_id,file_name,source_uri,parser,options,status,created_at,updated_at)"
                " VALUES(?,?,?,?,?,?,?,?,?,?)",
                (job_id, tenant_id, file_id, file_name, source_uri, parser, json.dumps(options or {}), QUEUED, now, now),
            )
        return job_id

    def get(self, job_id: str) -> Optional[dict[str, Any]]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        return self._row(row)

    def list(self, tenant_id: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
        q, args = "SELECT * FROM jobs", []
        if tenant_id:
            q += " WHERE tenant_id=?"
            args.append(tenant_id)
        q += " ORDER BY created_at DESC LIMIT ?"
        args.append(limit)
        with self._conn() as c:
            return [self._row(r) for r in c.execute(q, args).fetchall()]

    # ---- worker side ----
    def claim_next(self) -> Optional[dict[str, Any]]:
        """Atomically move the oldest QUEUED job to PROCESSING."""
        with self._lock, self._conn() as c:
            row = c.execute("SELECT * FROM jobs WHERE status=? ORDER BY created_at LIMIT 1", (QUEUED,)).fetchone()
            if not row:
                return None
            cur = c.execute(
                "UPDATE jobs SET status=?, updated_at=? WHERE job_id=? AND status=?",
                (PROCESSING, _now(), row["job_id"], QUEUED),
            )
            if cur.rowcount != 1:
                return None
            return self._row(c.execute("SELECT * FROM jobs WHERE job_id=?", (row["job_id"],)).fetchone())

    def complete(self, job_id: str, engine: str, output_uri: str) -> None:
        self._update(job_id, status=COMPLETED, engine=engine, output_uri=output_uri, error=None)

    def fail(self, job_id: str, error: str) -> None:
        self._update(job_id, status=FAILED, error=error[:2000])

    def requeue_stuck(self) -> int:
        """On startup: jobs left in PROCESSING by a crashed process go back to QUEUED."""
        with self._lock, self._conn() as c:
            return c.execute("UPDATE jobs SET status=?, updated_at=? WHERE status=?", (QUEUED, _now(), PROCESSING)).rowcount

    # ---- helpers ----
    def _update(self, job_id: str, **fields) -> None:
        fields["updated_at"] = _now()
        cols = ", ".join(f"{k}=?" for k in fields)
        with self._lock, self._conn() as c:
            c.execute(f"UPDATE jobs SET {cols} WHERE job_id=?", (*fields.values(), job_id))

    @staticmethod
    def _row(row) -> Optional[dict[str, Any]]:
        if row is None:
            return None
        d = dict(row)
        d["options"] = json.loads(d["options"] or "{}")
        return d
