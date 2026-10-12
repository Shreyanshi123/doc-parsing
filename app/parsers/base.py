"""
Parsing (Abstract Class) from the architecture diagram.

To add a new engine: subclass BaseParser, decorate with @register, import the module in
app/parsers/__init__.py. That is all - the router, API, compare tool and UI pick it up.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from app.models import ParseOptions, ParsedDocument


class ParserUnavailable(Exception):
    pass


class BaseParser(ABC):
    name: ClassVar[str] = "base"
    description: ClassVar[str] = ""
    supported_types: ClassVar[set[str]] = set()
    cost: ClassVar[str] = "free"        # "free" | "free-local-gpu" | "paid"

    @classmethod
    def is_available(cls) -> tuple[bool, str]:
        """Return (ok, reason_if_not). Must be cheap and must not raise."""
        return True, ""

    @abstractmethod
    def parse(
        self, data: bytes, file_name: str, file_type: str, options: ParseOptions
    ) -> ParsedDocument:
        """Parse raw bytes into a ParsedDocument. Raise on failure; the pipeline will fall back."""
