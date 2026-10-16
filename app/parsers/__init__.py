"""Importing this package registers every parser (each module uses @register)."""
from app.parsers import (  # noqa: F401
    azure_di_parser,
    docling_parser,
    docx_parser,
    easyocr_parser,
    framework_parsers,
    hybrid_pdf_parser,
    llamaparse_parser,
    markitdown_parser,
    ocr_parser,
    opendataloader_parser,
    pdfminer_parser,
    pdfplumber_parser,
    pptx_parser,
    pymupdf4llm_parser,
    pymupdf_parser,
    smart_pdf_parser,
    spreadsheet_parser,
    unstructured_parser,
    vlm_parser,
)
from app.parsers.registry import get_parser_class, list_parsers, parsers_for  # noqa: F401
