"""
Normalized parsed-output model (the "DataClass" box in the architecture diagram).

Every parser - whatever engine it wraps - must return a `ParsedDocument`.
Shape of the final JSON (see ParsedDocument.to_dict):

{
  "metadata": {"file_name", "file_type", "engine", "page_count", ...},
  "content":  "<whole document as Markdown>",
  "pages": [
     {"page_number": 1,
      "content": "<page markdown>",
      "elements": [
         {"content_type": "text|table|image", "content": "<markdown>",
          "image": "<base64 bytes, only for images>", "metadata": {...}}
      ]}
  ],
  "warnings": []
}
"""
from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Any, Optional

TEXT = "text"
TABLE = "table"
IMAGE = "image"


@dataclass
class ParseOptions:
    """Knobs the caller can set per request. All optional."""

    ocr_lang: str = ""              # empty -> settings.ocr_lang
    ocr_dpi: int = 0                # 0 -> settings.ocr_dpi
    extract_images: bool = False    # also return embedded images as bytes
    prefer_quality: bool = False    # router prefers slower/better engines (VLM) when available
    min_chars_per_page: int = 40    # below this a PDF page is treated as "scanned"
    max_pages: Optional[int] = None # cap pages processed (useful for slow engines)
    vlm_model: str = ""             # empty -> settings.vlm_model

    @classmethod
    def from_dict(cls, d: Optional[dict]) -> "ParseOptions":
        d = d or {}
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass
class Element:
    content_type: str                      # "text" | "table" | "image"
    content: str = ""                      # Markdown (for images: OCR/alt text if any)
    image: Optional[bytes] = None          # raw bytes for content_type == "image"
    image_format: Optional[str] = None     # "png", "jpeg", ...
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_images: bool = True) -> dict[str, Any]:
        d: dict[str, Any] = {
            "content_type": self.content_type,
            "content": self.content,
            "metadata": self.metadata,
        }
        if self.image is not None:
            d["image_format"] = self.image_format
            d["image_size_bytes"] = len(self.image)
            if include_images:
                d["image"] = base64.b64encode(self.image).decode("ascii")
        return d


@dataclass
class Page:
    page_number: int
    elements: list[Element] = field(default_factory=list)

    @property
    def markdown(self) -> str:
        return "\n\n".join(e.content.strip() for e in self.elements if e.content and e.content.strip())

    def to_dict(self, include_images: bool = True) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "content": self.markdown,
            "elements": [e.to_dict(include_images) for e in self.elements],
        }


@dataclass
class ParsedDocument:
    file_name: str
    file_type: str
    engine: str
    pages: list[Page] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def markdown(self) -> str:
        return "\n\n".join(p.markdown for p in self.pages if p.markdown)

    def stats(self) -> dict[str, int]:
        els = [e for p in self.pages for e in p.elements]
        md = self.markdown
        return {
            "pages": len(self.pages),
            "chars": len(md),
            "words": len(md.split()),
            "tables": sum(1 for e in els if e.content_type == TABLE),
            "images": sum(1 for e in els if e.content_type == IMAGE),
            "headings": sum(1 for line in md.splitlines() if line.lstrip().startswith("#")),
            "empty_pages": sum(1 for p in self.pages if not p.markdown.strip()),
        }

    def to_dict(self, include_images: bool = True) -> dict[str, Any]:
        meta = {
            "file_name": self.file_name,
            "file_type": self.file_type,
            "engine": self.engine,
            "page_count": len(self.pages),
            **self.metadata,
        }
        return {
            "metadata": meta,
            "content": self.markdown,
            "pages": [p.to_dict(include_images) for p in self.pages],
            "warnings": self.warnings,
        }
