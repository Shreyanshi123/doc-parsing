"""Amazon Textract parser (paid, optional).

Textract performs OCR plus table and key/value extraction. Its synchronous API
accepts one page at a time, so PDFs are rendered locally and each page is sent as
a PNG. That keeps this POC simple: no S3 bucket or async job polling is needed.
"""
from __future__ import annotations

from app.config import settings
from app.models import TABLE, TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register


def _child_text(block: dict, blocks: dict[str, dict]) -> str:
    """Return words and selection marks referenced by a Textract block."""
    parts: list[str] = []
    for relation in block.get("Relationships", []):
        if relation.get("Type") != "CHILD":
            continue
        for child_id in relation.get("Ids", []):
            child = blocks.get(child_id, {})
            if child.get("BlockType") == "SELECTION_ELEMENT":
                if child.get("SelectionStatus") == "SELECTED":
                    parts.append("[x]")
            elif child.get("Text"):
                parts.append(child["Text"])
    return " ".join(parts)


def _table_markdown(table: dict, blocks: dict[str, dict]) -> str:
    cells: dict[tuple[int, int], str] = {}
    max_row = max_col = 0
    for relation in table.get("Relationships", []):
        if relation.get("Type") != "CHILD":
            continue
        for cell_id in relation.get("Ids", []):
            cell = blocks.get(cell_id, {})
            if cell.get("BlockType") != "CELL":
                continue
            row, col = cell.get("RowIndex", 1), cell.get("ColumnIndex", 1)
            cells[(row, col)] = _child_text(cell, blocks)
            max_row, max_col = max(max_row, row), max(max_col, col)
    if not max_row or not max_col:
        return ""
    rows = [[cells.get((row, col), "") for col in range(1, max_col + 1)] for row in range(1, max_row + 1)]
    header = rows[0]
    return "\n".join([
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
        *["| " + " | ".join(row) + " |" for row in rows[1:]],
    ])


@register
class TextractParser(BaseParser):
    name = "textract"
    description = "Amazon Textract OCR with table and form-field extraction (paid AWS service)."
    supported_types = {"pdf", "image"}
    cost = "paid"

    @classmethod
    def is_available(cls):
        if not settings.aws_region:
            return False, "set AWS_REGION"
        try:
            import boto3  # noqa: F401
            return True, ""
        except ImportError:
            return False, "pip install boto3 (or pip install -r requirements-extra.txt)"

    def _client(self):
        import boto3
        session = boto3.Session(profile_name=settings.aws_profile or None, region_name=settings.aws_region)
        return session.client("textract")

    @staticmethod
    def _pdf_pages(data: bytes, max_pages: int | None):
        import fitz
        pdf = fitz.open(stream=data, filetype="pdf")
        try:
            limit = min(len(pdf), max_pages) if max_pages else len(pdf)
            for index in range(limit):
                pix = pdf[index].get_pixmap(matrix=fitz.Matrix(200 / 72, 200 / 72), alpha=False)
                yield index + 1, pix.tobytes("png")
        finally:
            pdf.close()

    def _pages(self, data: bytes, file_type: str, max_pages: int | None):
        if file_type == "pdf":
            yield from self._pdf_pages(data, max_pages)
        else:
            yield 1, data

    def parse(self, data, file_name, file_type, options):
        client = self._client()
        out = ParsedDocument(file_name, file_type, self.name)
        confidences: list[float] = []
        for page_number, image in self._pages(data, file_type, options.max_pages):
            response = client.analyze_document(
                Document={"Bytes": image}, FeatureTypes=["TABLES", "FORMS", "LAYOUT"]
            )
            blocks_list = response.get("Blocks", [])
            blocks = {block.get("Id"): block for block in blocks_list if block.get("Id")}
            lines = [block.get("Text", "") for block in blocks_list if block.get("BlockType") == "LINE"]
            confidences.extend(float(block["Confidence"]) for block in blocks_list if block.get("BlockType") == "WORD" and "Confidence" in block)
            elements = [Element(TEXT, "\n".join(lines))] if lines else []
            for table in (block for block in blocks_list if block.get("BlockType") == "TABLE"):
                markdown = _table_markdown(table, blocks)
                if markdown:
                    elements.append(Element(TABLE, markdown))
            values: dict[str, str] = {}
            for key in (block for block in blocks_list if block.get("BlockType") == "KEY_VALUE_SET" and "KEY" in block.get("EntityTypes", [])):
                label = _child_text(key, blocks)
                for relation in key.get("Relationships", []):
                    if relation.get("Type") == "VALUE":
                        for value_id in relation.get("Ids", []):
                            values[label] = _child_text(blocks.get(value_id, {}), blocks)
            if values:
                elements.append(Element(TEXT, "\n".join(f"**{key}:** {value}" for key, value in values.items()), metadata={"form_fields": values}))
            out.pages.append(Page(page_number, elements))
        if not out.pages:
            out.warnings.append("Textract returned no pages.")
        if confidences:
            out.metadata["average_word_confidence"] = round(sum(confidences) / len(confidences), 2)
        out.metadata["textract_mode"] = "synchronous per-page analysis"
        return out
