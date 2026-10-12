"""python-docx: headings, lists, tables, page breaks, embedded images (in document order)."""
from __future__ import annotations

import io

from app.models import IMAGE, TABLE, TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register
from app.parsers.utils import rows_to_markdown


@register
class DocxParser(BaseParser):
    name = "docx"
    description = "python-docx native parser: headings, bullet/numbered lists, tables, page breaks."
    supported_types = {"docx"}

    @classmethod
    def is_available(cls):
        try:
            import docx  # noqa: F401
            return True, ""
        except ImportError:
            return False, "pip install python-docx"

    def parse(self, data, file_name, file_type, options):
        import docx
        from docx.table import Table
        from docx.text.paragraph import Paragraph

        d = docx.Document(io.BytesIO(data))
        out = ParsedDocument(file_name, file_type, self.name)
        pages: list[Page] = [Page(1)]

        for child in d.element.body.iterchildren():
            tag = child.tag.split("}")[-1]
            if tag == "p":
                para = Paragraph(child, d)
                text = para.text.strip()
                if text:
                    self._append_text(pages[-1], self._style(para, text))
                if options.extract_images:
                    for blip in child.xpath(".//a:blip"):
                        rid = blip.get(
                            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                        )
                        part = d.part.related_parts.get(rid) if rid else None
                        if part is not None:
                            fmt = part.content_type.split("/")[-1]
                            pages[-1].elements.append(Element(IMAGE, "", part.blob, fmt))
                if child.xpath('.//w:br[@w:type="page"]'):
                    pages.append(Page(len(pages) + 1))  # explicit page break -> new page
            elif tag == "tbl":
                table = Table(child, d)
                rows = [[c.text.strip() for c in row.cells] for row in table.rows]
                md = rows_to_markdown(rows)
                if md:
                    pages[-1].elements.append(Element(TABLE, md))

        out.pages = [p for p in pages if p.elements] or pages[:1]
        for n, p in enumerate(out.pages, 1):
            p.page_number = n
        out.warnings.append("DOCX has no fixed pagination; pages are split only at explicit page breaks.")
        return out

    @staticmethod
    def _append_text(page: Page, md: str) -> None:
        """Consecutive list items are merged into one element so the Markdown list stays tight."""
        is_item = md.startswith(("- ", "1. "))
        if is_item and page.elements:
            last = page.elements[-1]
            if last.content_type == TEXT and last.content.startswith(("- ", "1. ")):
                last.content += "\n" + md
                return
        page.elements.append(Element(TEXT, md))

    @staticmethod
    def _style(para, text: str) -> str:
        style = (para.style.name or "").lower() if para.style is not None else ""
        if style == "title":
            return f"# {text}"
        if style.startswith("heading"):
            digits = "".join(ch for ch in style if ch.isdigit())
            level = min(int(digits), 6) if digits else 1
            return f"{'#' * level} {text}"
        if "list bullet" in style:
            return f"- {text}"
        if "list number" in style:
            return f"1. {text}"
        return text
