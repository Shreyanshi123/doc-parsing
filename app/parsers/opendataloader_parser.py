"""
OpenDataLoader PDF (open source, local, deterministic, no GPU). Wrapped through its LangChain
loader - the "langchain wrapper" box in the architecture diagram.

Install:  pip install langchain-opendataloader-pdf     AND   Java 11+ on PATH
"""
from __future__ import annotations

import shutil

from app.models import TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register
from app.parsers.utils import temp_file


@register
class OpenDataLoaderParser(BaseParser):
    name = "opendataloader"
    description = "OpenDataLoader PDF via LangChain loader: layout-aware Markdown, tables, reading order. Local; needs Java 11+."
    supported_types = {"pdf"}

    @classmethod
    def is_available(cls):
        if not shutil.which("java"):
            return False, "Java 11+ not found on PATH"
        try:
            import langchain_opendataloader_pdf  # noqa: F401
            return True, ""
        except ImportError:
            return False, "pip install langchain-opendataloader-pdf"

    def parse(self, data, file_name, file_type, options):
        from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader

        with temp_file(data, ".pdf") as path:
            docs = OpenDataLoaderPDFLoader(file_path=[path], format="markdown", split_pages=True, quiet=True).load()
        out = ParsedDocument(file_name, file_type, self.name)
        for i, d in enumerate(docs):
            n = d.metadata.get("page") or (i + 1)
            if options.max_pages and n > options.max_pages:
                continue
            out.pages.append(Page(int(n), [Element(TEXT, d.page_content)]))
        out.warnings.append("OpenDataLoader emits a whole page as one Markdown element (tables are inside the text).")
        return out
