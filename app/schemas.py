"""API request/response models (pydantic). The core pipeline itself has no pydantic dependency."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models import ParseOptions


class OptionsIn(BaseModel):
    ocr_lang: str = ""
    ocr_dpi: int = 0
    extract_images: bool = False
    prefer_quality: bool = False
    min_chars_per_page: int = 40
    max_pages: Optional[int] = None
    vlm_model: str = ""

    def to_options(self) -> ParseOptions:
        return ParseOptions(**self.model_dump())


class ParseRequest(BaseModel):
    """The one request body used for every document - the same shape as the architecture 'Input' box."""

    file_id: str = Field(..., examples=["f-001"])
    file_name: str = Field(..., examples=["invoice.pdf"])
    file_path: str = Field(
        ...,
        description="Azure blob URL (SAS) / azure://container/blob / local path under data/uploads",
        examples=["https://acct.blob.core.windows.net/docs/invoice.pdf?sv=...&sig=..."],
    )
    tenant_id: str = Field(..., examples=["tenant-42"])
    parser: str = Field("auto", description="'auto' (router decides) or a parser name from /api/providers")
    options: OptionsIn = OptionsIn()
    include_images: bool = False


class CompareRequest(ParseRequest):
    reference_text: Optional[str] = None
    parsers: Optional[list[str]] = None
    include_paid: bool = False
