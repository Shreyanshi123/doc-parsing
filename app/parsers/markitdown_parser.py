"""Microsoft MarkItDown: one converter for PDF/DOCX/PPTX/XLSX/CSV -> Markdown. Simple baseline for LLM pipelines."""
from __future__ import annotations

import io

from app.models import TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register

_EXT = {"pdf": ".pdf", "docx": ".docx", "pptx": ".pptx", "xlsx": ".xlsx", "csv": ".csv"}


@register
class MarkItDownParser(BaseParser):
    name = "markitdown"
    description = "Microsoft MarkItDown (pip install 'markitdown[pdf,docx,pptx,xlsx]'): generic file -> Markdown. No OCR, no page split."
    supported_types = set(_EXT)

    @classmethod
    def is_available(cls):
        try:
            import markitdown  # noqa: F401
            return True, ""
        except ImportError:
            return False, "pip install 'markitdown[pdf,docx,pptx,xlsx]'"

    def parse(self, data, file_name, file_type, options):
        from markitdown import MarkItDown

        md = MarkItDown()
        ext = _EXT[file_type]
        try:  # newer API
            from markitdown import StreamInfo

            res = md.convert_stream(io.BytesIO(data), stream_info=StreamInfo(extension=ext))
        except (ImportError, TypeError):  # older API
            res = md.convert_stream(io.BytesIO(data), file_extension=ext)
        out = ParsedDocument(file_name, file_type, self.name)
        out.pages.append(Page(1, [Element(TEXT, res.text_content or "")]))
        out.warnings.append("MarkItDown returns the whole file as one block; no page numbers.")
        return out
