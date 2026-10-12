"""
LlamaParse (LlamaIndex cloud API). Needs LLAMA_CLOUD_API_KEY. Free tier is credit-limited.
!! The document is UPLOADED to LlamaIndex's cloud - check your data policy before using real tenant data.
Marked cost="cloud" so it is excluded from comparisons unless include_paid is set.

Install: pip install llama-parse      (thin wrapper over llama-cloud-services; both import paths are tried)
"""
from __future__ import annotations

from app.config import settings
from app.models import TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register


def _import_llamaparse():
    try:
        from llama_cloud_services import LlamaParse
    except ImportError:
        from llama_parse import LlamaParse
    return LlamaParse


@register
class LlamaParseParser(BaseParser):
    name = "llamaparse"
    description = "LlamaParse cloud parser (API key, credit-limited free tier). Sends the document to LlamaIndex cloud."
    supported_types = {"pdf", "docx", "pptx", "xlsx", "image"}
    cost = "cloud"

    @classmethod
    def is_available(cls):
        if not settings.llama_api_key:
            return False, "set LLAMA_CLOUD_API_KEY"
        try:
            _import_llamaparse()
            return True, ""
        except ImportError:
            return False, "pip install llama-parse"

    def parse(self, data, file_name, file_type, options):
        LlamaParse = _import_llamaparse()
        parser = LlamaParse(api_key=settings.llama_api_key, result_type="markdown")
        docs = parser.load_data(data, extra_info={"file_name": file_name})
        out = ParsedDocument(file_name, file_type, self.name)
        for i, d in enumerate(docs):
            if options.max_pages and i + 1 > options.max_pages:
                break
            out.pages.append(Page(i + 1, [Element(TEXT, getattr(d, "text", "") or "")]))
        if len(docs) == 1:
            out.warnings.append("LlamaParse returned one document; page boundaries may not be preserved.")
        return out
