"""Picks the right adapter from the path/URL. This is the ONLY place that needs to know
the difference between "uploaded locally" and "lives in blob"."""
from __future__ import annotations

from app.storage.azure_blob import AzureBlobStorage
from app.storage.base import StorageAdapter
from app.storage.local import LocalStorage


def get_storage(uri: str) -> StorageAdapter:
    low = uri.lower()
    if low.startswith(("http://", "https://", "azure://")):
        return AzureBlobStorage()
    return LocalStorage()  # plain path or file://


def read_document(uri: str) -> bytes:
    return get_storage(uri).read(uri)
