"""
Reads documents from Azure Blob Storage (or any plain http(s) URL).

Supported inputs
  1. https://<acct>.blob.core.windows.net/<container>/<blob>?<SAS token>   -> plain HTTP GET
  2. https://<acct>.blob.core.windows.net/<container>/<blob>  (no SAS)    -> needs AZURE_STORAGE_CONNECTION_STRING
  3. azure://<container>/<blob>                                            -> needs AZURE_STORAGE_CONNECTION_STRING
  4. any other https:// URL                                                -> plain HTTP GET
"""
from __future__ import annotations

from urllib.parse import urlparse, unquote

import requests

from app.config import settings
from app.storage.base import StorageAdapter, StorageError

MAX_BYTES = 100 * 1024 * 1024  # 100 MB guard for the POC


class AzureBlobStorage(StorageAdapter):
    def read(self, uri: str) -> bytes:
        parsed = urlparse(uri)

        if settings.allowed_url_hosts and parsed.scheme in ("http", "https"):
            if parsed.hostname not in settings.allowed_url_hosts:
                raise StorageError(f"Host not allowed: {parsed.hostname}")

        if parsed.scheme == "azure":
            return self._read_with_connection_string(parsed.netloc, parsed.path.lstrip("/"))

        has_sas = "sig=" in (parsed.query or "")
        is_blob_host = (parsed.hostname or "").endswith(".blob.core.windows.net")
        if is_blob_host and not has_sas:
            if not settings.azure_conn_str:
                raise StorageError(
                    "Blob URL has no SAS token and AZURE_STORAGE_CONNECTION_STRING is not set."
                )
            container, _, blob = parsed.path.lstrip("/").partition("/")
            return self._read_with_connection_string(container, unquote(blob))

        return self._http_get(uri)

    # ------------------------------------------------------------------
    def _http_get(self, url: str) -> bytes:
        try:
            r = requests.get(url, timeout=60, stream=True)
            r.raise_for_status()
            buf = bytearray()
            for chunk in r.iter_content(1024 * 1024):
                buf.extend(chunk)
                if len(buf) > MAX_BYTES:
                    raise StorageError("File exceeds 100 MB POC limit")
            return bytes(buf)
        except requests.RequestException as e:
            raise StorageError(f"Download failed: {e}") from e

    def _read_with_connection_string(self, container: str, blob: str) -> bytes:
        if not settings.azure_conn_str:
            raise StorageError("AZURE_STORAGE_CONNECTION_STRING is not set.")
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError as e:
            raise StorageError("pip install azure-storage-blob") from e
        client = BlobServiceClient.from_connection_string(settings.azure_conn_str)
        return client.get_blob_client(container=container, blob=blob).download_blob().readall()
