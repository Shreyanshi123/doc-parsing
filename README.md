# Document Parsing POC

Upload (or point to a blob URL) → router picks the best **free** parser → normalized Markdown → structured JSON.
Includes a harness to **compare every parser** on the same document so you can decide which engine wins for which data.

> Full explanation of every file: **[GUIDE.md](GUIDE.md)**

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# OCR engine (system package, not pip):
#   Ubuntu/Debian: sudo apt install tesseract-ocr
#   macOS:         brew install tesseract
#   Windows:       https://github.com/UB-Mannheim/tesseract/wiki  (then set TESSERACT_CMD in .env)

cp .env.example .env
uvicorn app.main:app --reload
```

Open **http://localhost:8000** (test UI) or **http://localhost:8000/docs** (Swagger).

Parsers included (18): `pymupdf`, `pymupdf4llm`, `pdfminer`, `pdfplumber`, `ocr` (Tesseract), `easyocr`, `hybrid_pdf`, `vlm` (Ollama), `opendataloader`, `docling`, `unstructured`, `markitdown`, `llamaparse` (cloud), `azure_di` (paid), `docx`, `pptx`, `spreadsheet`, `text`.
Heavy/cloud/paid ones: `pip install -r requirements-extra.txt`. OpenDataLoader also needs **Java 11+**. Check `/api/providers` to see which are ready on your machine.

Optional vision-LLM parser (free, local):
```bash
ollama pull qwen2.5vl:7b      # then it shows up as "ready" in the UI
```

## Try it without the server

```bash
python scripts/make_samples.py                       # creates test docs in ./samples
python scripts/parse_file.py samples/report.docx     # auto-routed parse -> Markdown
python scripts/compare.py samples/*.pdf              # every parser, side by side
python -m unittest discover -s tests -v              # tests
```

## The two input modes

| Mode | When | Endpoint |
|---|---|---|
| **Upload** (now) | you upload files yourself | `POST /api/parse/upload` (multipart) |
| **Blob URL** (later) | payload points at Azure Blob | `POST /api/parse` (JSON) |

Same payload shape for every document:

```json
{
  "file_id": "f-001",
  "file_name": "invoice.pdf",
  "file_path": "https://acct.blob.core.windows.net/docs/invoice.pdf?sv=...&sig=...",
  "tenant_id": "tenant-42",
  "parser": "auto",
  "options": { "extract_images": false, "prefer_quality": false, "max_pages": null }
}
```

Async (queue + worker) versions: `POST /api/jobs` and `POST /api/jobs/upload`, then `GET /api/jobs/{id}` and `GET /api/jobs/{id}/result`.

## Docker

```bash
docker build -t doc-parsing-poc .
docker run -p 8000:8000 --env-file .env -v $(pwd)/data:/srv/data doc-parsing-poc
```
