"""Storage adapter interface - the "Storage Adapter / Document loader" box."""
from __future__ import annotations

from abc import ABC, abstractmethod


class StorageError(Exception):
    pass


class StorageAdapter(ABC):
    """Reads raw bytes from some location identified by a URI/path string."""

    @abstractmethod
    def read(self, uri: str) -> bytes: ...
