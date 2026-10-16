"""Build scanned / noisy-scanned / mixed test PDFs from an existing digital PDF in eval/.
The ground truth is the same as the source's, so the reference stays exact.

    python scripts/make_scan_tests.py
"""
from __future__ import annotations

import io
import shutil
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageFilter

EVAL = Path(__file__).resolve().parent.parent / "eval"
SRC = EVAL / "AI_agent_p1-3.pdf"
TRUTH = EVAL / "AI_agent_p1-3.pdf.truth.md"
rng = np.random.default_rng(7)


def render(page, dpi: int) -> Image.Image:
    pix = page.get_pixmap(dpi=dpi)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def make_noisy(img: Image.Image) -> Image.Image:
    """Looks like a bad phone/office scan: tilted, shadowed, grainy, blurred, JPEG-compressed."""
    img = img.rotate(1.8, resample=Image.BICUBIC, expand=True, fillcolor=(235, 235, 232))
    a = np.asarray(img).astype(np.float32)
    h, w, _ = a.shape
    shadow = np.linspace(0.86, 1.0, w)[None, :, None]           # darker on the left edge
    a = a * shadow
    a += rng.normal(0, 9, a.shape)                              # grain
    a = np.clip(a, 0, 255).astype(np.uint8)
    img = Image.fromarray(a).filter(ImageFilter.GaussianBlur(0.9))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=55)                           # compression artefacts
    return Image.open(io.BytesIO(buf.getvalue())).convert("RGB")


def add_image_page(doc: pymupdf.Document, img: Image.Image, size) -> None:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    page = doc.new_page(width=size.width, height=size.height)
    page.insert_image(page.rect, stream=buf.getvalue())


def main() -> None:
    src = pymupdf.open(SRC)
    outputs = {}

    clean = pymupdf.open()
    for p in src:
        add_image_page(clean, render(p, 150), p.rect)
    outputs["AI_agent_scanned_clean.pdf"] = clean

    noisy = pymupdf.open()
    for p in src:
        add_image_page(noisy, make_noisy(render(p, 150)), p.rect)
    outputs["AI_agent_scanned_noisy.pdf"] = noisy

    mixed = pymupdf.open()          # page 1 digital, page 2 scanned, page 3 digital
    mixed.insert_pdf(src, from_page=0, to_page=0)
    add_image_page(mixed, render(src[1], 150), src[1].rect)
    mixed.insert_pdf(src, from_page=2, to_page=2)
    outputs["AI_agent_mixed.pdf"] = mixed

    for name, doc in outputs.items():
        doc.save(EVAL / name)
        shutil.copy(TRUTH, EVAL / f"{name}.truth.md")
        print("wrote", name, f"({len(doc)} pages)")


if __name__ == "__main__":
    main()
