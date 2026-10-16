"""
Document-loading FRAMEWORKS wrapped as parsers, so they can be compared with the rest:

  langchain_loader   LangChain  PyPDFLoader                (one Document per page)
  llamaindex_reader  LlamaIndex PDFReader                  (one Document per page)
  haystack_converter Haystack   PyPDFToDocument            (one Document, pages split by form-feed)

All three read the PDF's text layer with the same library (pypdf), so they return plain text:
no headings, no tables, no OCR. What the frameworks add on top (chunking, embeddings, search) is
outside parsing and is not measured here. OpenDataLoader and Unstructured are frameworks too and
already have their own parser files.

Each parser turns the framework's Document objects into the shared Page / Element shape.
"""
from __future__ import annotations

from pathlib import Path

from app.models import TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register
from app.parsers.utils import limit_pages, temp_file


def _pages_to_document(name, file_name, file_type, texts, options) -> ParsedDocument:
    out = ParsedDocument(file_name, file_type, name)
    for i in range(limit_pages(len(texts), options.max_pages)):
        out.pages.append(Page(i + 1, [Element(TEXT, texts[i])]))
    out.metadata["source_page_count"] = len(texts)
    return out


@register
class LangChainLoaderParser(BaseParser):
    name = "langchain_loader"
    description = "LangChain PyPDFLoader (pypdf). Plain text per page; no headings, tables or OCR."
    supported_types = {"pdf"}

    @classmethod
    def is_available(cls):
        try:
            from langchain_community.document_loaders import PyPDFLoader  # noqa: F401
            import pypdf  # noqa: F401
        except ImportError:
            return False, "pip install langchain-community pypdf"
        return True, ""

    def parse(self, data, file_name, file_type, options):
        from langchain_community.document_loaders import PyPDFLoader

        with temp_file(data, ".pdf") as path:
            docs = PyPDFLoader(path).load()
        return _pages_to_document(self.name, file_name, file_type, [d.page_content for d in docs], options)


@register
class LlamaIndexReaderParser(BaseParser):
    name = "llamaindex_reader"
    description = "LlamaIndex PDFReader (pypdf). Plain text per page; no headings, tables or OCR."
    supported_types = {"pdf"}

    @classmethod
    def is_available(cls):
        try:
            from llama_index.readers.file import PDFReader  # noqa: F401
        except ImportError:
            return False, "pip install llama-index-readers-file"
        return True, ""

    def parse(self, data, file_name, file_type, options):
        from llama_index.readers.file import PDFReader

        with temp_file(data, ".pdf") as path:
            docs = PDFReader().load_data(Path(path))
        return _pages_to_document(self.name, file_name, file_type, [d.text for d in docs], options)


@register
class HaystackConverterParser(BaseParser):
    name = "haystack_converter"
    description = "Haystack PyPDFToDocument (pypdf). Plain text per page; no headings, tables or OCR."
    supported_types = {"pdf"}

    @classmethod
    def is_available(cls):
        try:
            from haystack.components.converters import PyPDFToDocument  # noqa: F401
        except ImportError:
            return False, "pip install haystack-ai pypdf"
        return True, ""

    def parse(self, data, file_name, file_type, options):
        from haystack.components.converters import PyPDFToDocument

        with temp_file(data, ".pdf") as path:
            docs = PyPDFToDocument().run(sources=[path])["documents"]
        text = "\n".join(d.content or "" for d in docs)
        pages = text.split("\f")                 # Haystack separates pages with a form-feed character
        if pages and not pages[-1].strip():
            pages = pages[:-1]
        return _pages_to_document(self.name, file_name, file_type, pages, options)
