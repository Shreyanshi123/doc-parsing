"""
Azure Document Intelligence (prebuilt-layout) - PAID. Included so you can compare the free
engines against it later. Disabled automatically unless AZURE_DI_ENDPOINT / AZURE_DI_KEY are set.

NOTE: written against azure-ai-documentintelligence >= 1.0; not exercised in the POC sandbox.
If your SDK version differs, only `_analyze` needs adjusting.
"""
from __future__ import annotations

from app.config import settings
from app.models import TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register


@register
class AzureDocIntelParser(BaseParser):
    name = "azure_di"
    description = "Azure Document Intelligence prebuilt-layout (paid). Reference quality for comparison."
    supported_types = {"pdf", "image", "docx", "pptx", "xlsx"}
    cost = "paid"

    @classmethod
    def is_available(cls):
        if not (settings.azure_di_endpoint and settings.azure_di_key):
            return False, "set AZURE_DI_ENDPOINT and AZURE_DI_KEY"
        try:
            import azure.ai.documentintelligence  # noqa: F401
            return True, ""
        except ImportError:
            return False, "pip install azure-ai-documentintelligence"

    def parse(self, data, file_name, file_type, options):
        result = self._analyze(data)
        out = ParsedDocument(file_name, file_type, self.name)
        content = result.content or ""
        for pg in result.pages or []:
            # slice the markdown by the page's span offsets
            text = "".join(content[s.offset : s.offset + s.length] for s in (pg.spans or []))
            out.pages.append(Page(pg.page_number, [Element(TEXT, text)]))
        if not out.pages:
            out.pages.append(Page(1, [Element(TEXT, content)]))
        return out

    def _analyze(self, data: bytes):
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential

        client = DocumentIntelligenceClient(settings.azure_di_endpoint, AzureKeyCredential(settings.azure_di_key))
        poller = client.begin_analyze_document(
            "prebuilt-layout", body=data, content_type="application/octet-stream", output_content_format="markdown"
        )
        return poller.result()
