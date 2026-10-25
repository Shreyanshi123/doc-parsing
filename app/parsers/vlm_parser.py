"""
Vision-LLM parser (the "LVM" option). Free when run locally through Ollama:

    ollama pull qwen2.5vl:7b        # or llava, minicpm-v, llama3.2-vision ...

Each PDF page (or the image) is rendered to PNG and sent to the model with a
"convert to Markdown" prompt. Slow on CPU, strong on messy layouts / handwriting / charts.
"""
from __future__ import annotations

import base64
import io
import re
import time

import requests

from app.config import settings
from app.models import TEXT, Element, Page, ParsedDocument
from app.parsers.base import BaseParser
from app.parsers.registry import register
from app.parsers.utils import limit_pages

PROMPT = (
    "You are a document parser. Convert this page into clean GitHub-flavoured Markdown. "
    "Keep headings (#), lists and reading order. Render tables as Markdown tables. "
    "Describe charts/figures in one short line starting with 'Figure:'. "
    "Do not add commentary. Output only the Markdown."
)

_cache = {"t": 0.0, "ok": False, "reason": ""}


@register
class VlmParser(BaseParser):
    name = "vlm"
    description = "Vision LLM: Azure OpenAI (GPT-4.1) if AZURE_OPENAI_* is set, else local Ollama (qwen2.5vl:7b). Best for complex/scanned/handwritten layouts and charts; slowest. Azure use costs money per page."
    supported_types = {"pdf", "image"}
    cost = "paid"   # may call Azure OpenAI (billed per page); also keeps it out of "Compare all" unless paid parsers are ticked

    @classmethod
    def is_available(cls):
        if not settings.vlm_parser_enabled:
            return False, "disabled: this parser sends every page of the document to the vision LLM (one API call per page). Set VLM_PARSER_ENABLED=true to allow it."
        from app.vision import azure_ready

        if azure_ready():
            return True, ""
        return cls.ollama_ready()

    @classmethod
    def ollama_ready(cls):
        """Is the local Ollama vision model reachable? (used by app/vision.py to read single figures; not a switch for this parser)"""
        if time.time() - _cache["t"] < 15:  # don't hit the network on every call
            return _cache["ok"], _cache["reason"]
        try:
            r = requests.get(f"{settings.ollama_url}/api/tags", timeout=1.5)
            r.raise_for_status()
            names = [m.get("name", "") for m in r.json().get("models", [])]
            want = settings.vlm_model
            if not any(n == want or n.split(":")[0] == want.split(":")[0] for n in names):
                _cache.update(t=time.time(), ok=False, reason=f"model '{want}' not pulled (ollama pull {want})")
            else:
                _cache.update(t=time.time(), ok=True, reason="")
        except Exception:
            _cache.update(t=time.time(), ok=False, reason=f"Ollama not reachable at {settings.ollama_url}")
        return _cache["ok"], _cache["reason"]

    def parse(self, data, file_name, file_type, options):
        from app.vision import azure_ready

        model = settings.azure_openai_deployment if azure_ready() else (options.vlm_model or settings.vlm_model)
        out = ParsedDocument(file_name, file_type, f"{self.name}:{model}")
        if file_type == "image":
            out.pages.append(Page(1, [Element(TEXT, self._ask(model, data))]))
            return out

        import fitz

        doc = fitz.open(stream=data, filetype="pdf")
        cap = options.max_pages or settings.vlm_max_pages
        n = limit_pages(len(doc), cap)
        if n < len(doc):
            out.warnings.append(f"VLM processed only the first {n} of {len(doc)} pages (VLM_MAX_PAGES).")
        for i in range(n):
            png = doc[i].get_pixmap(dpi=150).tobytes("png")
            out.pages.append(Page(i + 1, [Element(TEXT, self._ask(model, png), metadata={"vlm": True})]))
        return out

    def _ask(self, model: str, image_bytes: bytes) -> str:
        from app.vision import ask_azure, azure_ready

        if azure_ready():
            return ask_azure(image_bytes, PROMPT)
        payload = {
            "model": model,
            "prompt": PROMPT,
            "images": [base64.b64encode(image_bytes).decode()],
            "stream": False,
            "options": {"temperature": 0},
        }
        r = requests.post(f"{settings.ollama_url}/api/generate", json=payload, timeout=settings.vlm_timeout)
        r.raise_for_status()
        text = r.json().get("response", "").strip()
        # models sometimes wrap everything in ```markdown fences
        return re.sub(r"^```(?:markdown|md)?\s*\n|\n```\s*$", "", text).strip()
