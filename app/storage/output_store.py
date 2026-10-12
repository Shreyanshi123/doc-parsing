"""Where the final JSON goes ("output upload" step). Local folder now, Azure Blob later."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import settings
from app.storage.base import StorageError


def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", s)[:120] or "x"


class OutputStore(ABC):
    @abstractmethod
    def save(self, tenant_id: str, file_id: str, job_id: str, payload: bytes) -> str:
        """Save JSON bytes and return a URI that `load` understands."""

    @abstractmethod
    def load(self, uri: str) -> bytes: ...


class LocalOutputStore(OutputStore):
    def save(self, tenant_id, file_id, job_id, payload):
        folder = settings.outputs_dir / _safe(tenant_id)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{_safe(file_id)}__{_safe(job_id)}.json"
        path.write_bytes(payload)
        return str(path)

    def load(self, uri):
        p = Path(uri).resolve()
        if settings.outputs_dir.resolve() not in p.parents:
            raise StorageError("Output path outside outputs dir")
        return p.read_bytes()


class AzureOutputStore(OutputStore):
    def _client(self):
        from azure.storage.blob import BlobServiceClient

        if not settings.azure_conn_str:
            raise StorageError("AZURE_STORAGE_CONNECTION_STRING is not set.")
        svc = BlobServiceClient.from_connection_string(settings.azure_conn_str)
        cont = svc.get_container_client(settings.azure_output_container)
        try:
            cont.create_container()
        except Exception:
            pass  # already exists
        return cont

    def save(self, tenant_id, file_id, job_id, payload):
        name = f"{_safe(tenant_id)}/{_safe(file_id)}__{_safe(job_id)}.json"
        self._client().upload_blob(name, payload, overwrite=True)
        return f"azure://{settings.azure_output_container}/{name}"

    def load(self, uri):
        container, _, blob = uri.removeprefix("azure://").partition("/")
        from azure.storage.blob import BlobServiceClient

        svc = BlobServiceClient.from_connection_string(settings.azure_conn_str)
        return svc.get_blob_client(container, blob).download_blob().readall()


def get_output_store() -> OutputStore:
    return AzureOutputStore() if settings.output_backend == "azure" else LocalOutputStore()
