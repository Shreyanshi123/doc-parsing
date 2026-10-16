"""
Figure reader: turns the picture of a chart / diagram into text a RAG system can use.

    describe_figure(png_bytes) -> FigureText | None

Backends (see settings.vision_backend):
  - azure_openai : a vision-capable Azure OpenAI deployment (e.g. GPT-4.1). Costs money per image.
  - ollama       : a local vision model (default qwen2.5vl:7b). Free, but slow on CPU.
Results are cached on disk by image hash, so the same figure is never sent (or paid for) twice.
"""
from __future__ import annotations

import base64
import hashlib
import logging
import re
from dataclasses import dataclass
from typing import Optional

import requests

from app.config import settings

log = logging.getLogger("vision")

PROMPT_VERSION = "v1"
PROMPT = (
    "You are reading one figure that was cut out of a PDF page.\n"
    "First line: 'Type: ' followed by one of: bar chart, line chart, pie chart, scatter plot, "
    "table image, flowchart, architecture diagram, photo, screenshot, logo, other.\n"
    "Then:\n"
    "- Chart: give the title, the axis labels with units, and a Markdown table with ALL data values. "
    "Use the numbers printed on the chart. If a value has to be read from the bar or line height, "
    "put ~ in front of it.\n"
    "- Diagram or flowchart: list every box or entity, then every connection as 'A -> B' "
    "(add the arrow label if there is one).\n"
    "- Anything else: describe it in one sentence.\n"
    "Do not add commentary. Do not invent values that are not visible."
)


@dataclass
class FigureText:
    kind: str       # "bar chart", "flowchart", ...
    body: str       # the Markdown the model returned (without the Type line)
    backend: str


def pick_backend() -> Optional[str]:
    mode = (settings.vision_backend or "auto").lower()
    if mode == "off":
        return None
    azure_ok = azure_ready()
    if mode == "azure_openai":
        return "azure_openai" if azure_ok else None
    if mode == "ollama":
        return "ollama" if _ollama_ready() else None
    if azure_ok:
        return "azure_openai"
    return "ollama" if _ollama_ready() else None


def _ollama_ready() -> bool:
    from app.parsers.vlm_parser import VlmParser

    return VlmParser.is_available()[0]


def _cache_path(png: bytes, backend: str):
    h = hashlib.sha256(png + f"|{backend}|{PROMPT_VERSION}".encode()).hexdigest()[:32]
    d = settings.data_dir / "cache" / "vision"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{h}.txt"


def _split_type(text: str) -> tuple[str, str]:
    m = re.match(r"\s*Type:\s*(.+?)\s*\n+(.*)", text, re.S | re.I)
    if m:
        return m.group(1).strip().lower(), m.group(2).strip()
    return "figure", text.strip()


def describe_figure(png: bytes) -> Optional[FigureText]:
    """Returns None when no backend is configured. Raises on a backend error (caller decides)."""
    backend = pick_backend()
    if backend is None:
        return None
    cache = _cache_path(png, backend)
    if cache.exists():
        raw = cache.read_text(encoding="utf-8")
    else:
        raw = ask_azure(png) if backend == "azure_openai" else _ask_ollama(png)
        cache.write_text(raw, encoding="utf-8")
    kind, body = _split_type(raw)
    return FigureText(kind, body, backend)


def _strip_fences(text: str) -> str:
    return re.sub(r"^```(?:markdown|md)?\s*\n|\n```\s*$", "", text.strip()).strip()


def azure_ready() -> bool:
    return all([settings.azure_openai_endpoint, settings.azure_openai_key, settings.azure_openai_deployment])


def ask_azure(png: bytes, prompt: str = PROMPT) -> str:
    url = (
        f"{settings.azure_openai_endpoint.rstrip('/')}/openai/deployments/"
        f"{settings.azure_openai_deployment}/chat/completions?api-version={settings.azure_openai_api_version}"
    )
    payload = {
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}},
            ],
        }],
        "temperature": 0,
        "max_tokens": 1000,
    }
    r = requests.post(url, headers={"api-key": settings.azure_openai_key}, json=payload, timeout=120)
    r.raise_for_status()
    return _strip_fences(r.json()["choices"][0]["message"]["content"])


def _ask_ollama(png: bytes) -> str:
    payload = {
        "model": settings.vlm_model,
        "prompt": PROMPT,
        "images": [base64.b64encode(png).decode()],
        "stream": False,
        "options": {"temperature": 0},
    }
    r = requests.post(f"{settings.ollama_url}/api/generate", json=payload, timeout=settings.vlm_timeout)
    r.raise_for_status()
    return _strip_fences(r.json().get("response", ""))
