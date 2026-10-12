# Code Guide

This guide explains what every file does, how the pieces map to your two diagrams, and how to run the POC evaluation.

---

## 1. How the code maps to your diagrams

**Diagram 1 – "Document Extraction" box**

| Diagram box | Where it lives |
|---|---|
| Input (file path, file name, file id, tenant id) | `app/schemas.py` → `ParseRequest` |
| Storage adapter / document loader (blob, local, GCS…) | `app/storage/` |
| File type resolver | `app/routing/file_type.py` |
| Registry | `app/parsers/registry.py` |
| Config loader | `app/config.py` + `.env` |
| Parser engines (Azure DI, PyMuPDF, LlamaParse, …) | `app/parsers/*.py` |
| Markdown normalizer | `app/normalizer.py` |
| Output (content, image bytes, page number, content type, metadata) | `app/models.py` → `ParsedDocument` |

**Diagram 2 – "Parsing (Abstract Class)" → "Normalized parsed output model"**

* Abstract class → `app/parsers/base.py` (`BaseParser`)
* Concrete tools → `pymupdf`, `pdfminer`, `ocr`, `vlm`, `azure_di`, … each is one file
* DataClass → `app/models.py`

**Flow line: Request JSON → API → SQL insert → worker → blob read → parser → output upload → status update**

| Step | Code |
|---|---|
| Request JSON | `POST /api/jobs` (`app/main.py`) |
| SQL insert | `JobStore.create()` (`app/jobs/store.py`) |
| worker | `WorkerPool` (`app/jobs/worker.py`) |
| blob read | `read_document()` (`app/storage/factory.py`) |
| parser | `parse_bytes()` (`app/pipeline.py`) |
| output upload | `get_output_store().save()` (`app/storage/output_store.py`) |
| status update | `JobStore.complete()` / `fail()` |

---

## 2. Request lifecycle (what happens to one document)

```
bytes ──► resolve_file_type ──► analyze ──► route ──► parse ──► normalize ──► build_output (JSON)
          (magic bytes)        (digital?    (ordered   (try candidates
                                scanned?)    list)      until one works)
```

1. **Resolve type** – looks at magic bytes first, extension second (so a mis-named file still works).
2. **Analyze** – for PDFs, samples up to 20 pages and classifies the document as `digital` (real text layer), `scanned` (pages are pictures) or `mixed`. It also estimates table count. Office files and images are classified without heavy work.
3. **Route** – turns the profile into an **ordered list of parsers** with a reason for each.
4. **Parse with fallback** – tries the first candidate; if it errors or returns empty content, the next one is tried. Every attempt is recorded under `routing.attempts` in the output.
5. **Normalize** – cleans whitespace/control characters, drops empty elements, stamps `engine` and `file_name` into each element's metadata.
6. **Output** – the JSON contract (section 5).

### Default routing rules (`app/routing/router.py`)

| Document | Chosen first | Fallbacks |
|---|---|---|
| Digital PDF | `pymupdf` | `pdfminer`, `hybrid_pdf`, `ocr` |
| Scanned PDF | `ocr` | `vlm` |
| Mixed PDF | `hybrid_pdf` (text layer per page, OCR only on scanned pages) | `ocr`, `pymupdf` |
| Image | `ocr` | `vlm` |
| DOCX / PPTX | `docx` / `pptx` | `docling` (if installed) |
| XLSX / CSV | `spreadsheet` | – |
| TXT / MD | `text` | – |

`prefer_quality: true` moves the vision-LLM (`vlm`) to the front for PDFs and images. A caller can also force any parser with `"parser": "<name>"` (no fallback in that case, so you see that engine's true behaviour).

**These rules are a starting hypothesis.** The point of the POC is to replace them with rules backed by your comparison results.

---

## 3. File-by-file reference

```
doc_parsing_poc/
├── README.md              quick start
├── GUIDE.md               this file
├── requirements.txt       core dependencies
├── requirements-extra.txt heavy / cloud / paid engines (docling, unstructured, easyocr, llama-parse, azure DI)
├── .env.example           all settings (copy to .env)
├── Dockerfile             container with Tesseract preinstalled
├── app/
│   ├── main.py            FastAPI endpoints
│   ├── config.py          settings from env vars
│   ├── models.py          ParsedDocument / Page / Element / ParseOptions
│   ├── schemas.py         API request models (pydantic)
│   ├── pipeline.py        the "black box": parse_bytes() and build_output()
│   ├── normalizer.py      Markdown cleanup
│   ├── compare.py         POC evaluation harness
│   ├── routing/
│   │   ├── file_type.py   magic-byte file type detection
│   │   ├── analyzer.py    digital / scanned / mixed classification
│   │   └── router.py      profile → ordered parser list   ← edit rules here
│   ├── parsers/
│   │   ├── base.py            BaseParser abstract class
│   │   ├── registry.py        @register + lookup + availability
│   │   ├── utils.py           rows → Markdown table helper
│   │   ├── pymupdf_parser.py  digital PDFs, headings, tables, images
│   │   ├── pdfminer_parser.py second-opinion text engine
│   │   ├── ocr_parser.py      Tesseract (scanned PDFs, images)
│   │   ├── hybrid_pdf_parser.py  text layer + OCR per page
│   │   ├── vlm_parser.py      vision LLM through local Ollama
│   │   ├── docx_parser.py     Word
│   │   ├── pptx_parser.py     PowerPoint
│   │   ├── spreadsheet_parser.py  XLSX / CSV  (+ plain-text parser)
│   │   ├── pymupdf4llm_parser.py  PyMuPDF Markdown exporter
│   │   ├── pdfplumber_parser.py   rule-based tables
│   │   ├── opendataloader_parser.py  OpenDataLoader PDF (Java) via LangChain
│   │   ├── markitdown_parser.py   Microsoft MarkItDown
│   │   ├── unstructured_parser.py Unstructured (optional, heavy)
│   │   ├── easyocr_parser.py      EasyOCR (optional, heavy)
│   │   ├── docling_parser.py      Docling (optional, heavy)
│   │   ├── llamaparse_parser.py   LlamaParse CLOUD api
│   │   └── azure_di_parser.py     Azure Document Intelligence (PAID)
│   ├── storage/
│   │   ├── base.py        StorageAdapter interface
│   │   ├── local.py       uploaded / local files (allow-listed folders only)
│   │   ├── azure_blob.py  Azure blob URL (SAS), azure://, or any https URL
│   │   ├── factory.py     chooses adapter from the path
│   │   └── output_store.py  where result JSON is saved (local or Azure)
│   ├── jobs/
│   │   ├── store.py       SQL jobs table (SQLite for the POC)
│   │   └── worker.py      background worker threads
│   └── static/index.html  test UI
├── scripts/
│   ├── make_samples.py    generate test documents
│   ├── parse_file.py      CLI: parse one file
│   └── compare.py         CLI: compare all parsers, write reports
├── tests/test_pipeline.py unit/integration tests
├── samples/               test documents
└── data/                  runtime: uploads/, outputs/, jobs.db
```

### Core

**`app/models.py`** – the normalized output model. Every parser must return a `ParsedDocument` → list of `Page` → list of `Element`. An `Element` has a `content_type` (`text` / `table` / `image`), `content` (Markdown), optional `image` bytes, and `metadata`. `ParseOptions` holds per-request knobs (OCR language/DPI, `extract_images`, `prefer_quality`, `max_pages`, …). It is a plain dataclass so the core pipeline has no web-framework dependency.

**`app/pipeline.py`** – `parse_bytes(data, file_name, options, parser)` runs the lifecycle in section 2 and returns a `PipelineResult`. `build_output()` turns that into the final JSON dict. This is the only function the API, the worker and the CLI scripts all call.

**`app/normalizer.py`** – makes different engines comparable: unified newlines, no control characters, collapsed blank lines, headings separated from paragraphs, empty elements dropped.

**`app/config.py`** – reads `.env`. Nothing else in the code touches `os.environ`.

### Routing

**`file_type.py`** – returns `pdf | docx | pptx | xlsx | csv | text | image`. Legacy `.doc/.ppt/.xls` raise a clear error with a LibreOffice conversion hint.

**`analyzer.py`** – the "intelligence" that identifies what kind of document this is. Threshold: a PDF page with fewer than `min_chars_per_page` (default 40) text characters counts as scanned. If PyMuPDF is missing it falls back to pdfminer.

**`router.py`** – `_rules()` is a readable list of `(parser, reason)` per document class. `route()` filters out unavailable parsers (and records why in `routing.skipped`).

### Parsers

Each parser declares `name`, `description`, `supported_types`, `cost`, `is_available()` and `parse()`.

| Parser | Strengths | Weaknesses |
|---|---|---|
| `pymupdf` | very fast; headings via font size; table finder; image extraction | no OCR |
| `pdfminer` | good reading order on complex digital PDFs | slower; no tables |
| `ocr` | works on scans and photos | plain text only; quality depends on DPI/language |
| `hybrid_pdf` | best default for mixed PDFs | needs both PyMuPDF and Tesseract |
| `vlm` | handles messy layouts, handwriting, charts; can output Markdown tables | slow (esp. CPU), can hallucinate, page-capped by `VLM_MAX_PAGES` |
| `docx` / `pptx` / `spreadsheet` | native structure (headings, lists, tables, slides, sheets) | DOCX has no real pages (split at explicit page breaks only) |
| `pymupdf4llm` | richer Markdown than plain `pymupdf` (headings, bold, lists, tables) | digital PDFs only |
| `pdfplumber` | rule-based table extraction; tested here: finds ruled tables that pdfminer misses | digital PDFs only; no OCR |
| `opendataloader` | local, deterministic, layout/reading-order aware; via LangChain loader | needs Java 11+; whole page = one Markdown block |
| `markitdown` | one converter for PDF/DOCX/PPTX/XLSX/CSV; good baseline | no OCR, no page numbers |
| `unstructured` | element types (Title, ListItem, Table) with page numbers | heavy install |
| `easyocr` | deep-learning OCR, often better than Tesseract on photos | heavy (PyTorch), slow on CPU |
| `docling` (free, optional) | strong layout/table understanding | large install; adapter untested |
| `llamaparse` (**cloud**) | managed GenAI parser, credit-limited free tier | **uploads the document to LlamaIndex cloud**; needs API key |
| `azure_di` (**paid**) | strong layout/tables; your existing parser, i.e. the reference to compare against | costs money; needs keys |

`cost` labels: `free` (runs locally), `free-local-gpu` (local vision LLM), `cloud` (data leaves your network), `paid`. Comparisons skip `cloud` and `paid` parsers unless you pass `include_paid` (so real tenant documents are never sent out by accident).

### Storage

`factory.get_storage(uri)` is the single switch between "uploaded locally" and "in blob":

* plain path / `file://` → `LocalStorage` (only inside `LOCAL_ALLOWED_ROOTS`, so a request cannot read `/etc/passwd`)
* `https://…blob.core.windows.net/…?sig=…` (SAS) → plain HTTP download
* `https://…blob.core.windows.net/…` without SAS, or `azure://container/blob` → uses `AZURE_STORAGE_CONNECTION_STRING`
* any other `https://` URL → plain HTTP download (restrict with `ALLOWED_URL_HOSTS`)

`output_store.py` writes the result JSON to `data/outputs/<tenant>/…` (default) or uploads it to the Azure container `AZURE_OUTPUT_CONTAINER` when `OUTPUT_BACKEND=azure`.

### Jobs

`store.py` is a small SQL table (`QUEUED → PROCESSING → COMPLETED | FAILED`) using SQLite. `claim_next()` is atomic so several worker threads never take the same job. On start-up, jobs left in `PROCESSING` by a crash go back to `QUEUED`. `worker.py` implements: blob read → parse → output upload → status update. To move to Azure SQL/Postgres, re-implement `JobStore` with the same methods.

### API (`app/main.py`)

| Endpoint | Purpose |
|---|---|
| `GET /api/providers` | every parser, supported types, cost, available or not (and why not) |
| `POST /api/parse/upload` | **upload mode**, synchronous |
| `POST /api/parse` | **blob/JSON mode**, synchronous |
| `POST /api/compare/upload`, `POST /api/compare` | run all parsers on one file and compare |
| `POST /api/jobs/upload`, `POST /api/jobs` | async queue |
| `GET /api/jobs`, `/api/jobs/{id}`, `/api/jobs/{id}/result` | status and results |

---

## 4. Running the POC evaluation (your first goal)

1. Collect ~10–20 representative documents per category: digital PDFs, scanned PDFs, mixed PDFs, table-heavy PDFs, invoices, forms, DOCX, PPTX, XLSX, photos of documents.
2. For the ones you care about most, write a **reference text file** (the correct content, typed or copy-pasted from the source). Even 5–10 per category makes the results meaningful.
3. Run:
   ```bash
   python scripts/compare.py my_docs/invoice1.pdf --reference my_docs/invoice1.txt
   python scripts/compare.py my_docs/*.pdf                 # no reference → heuristic ranking
   ```
   or use **Compare all parsers** in the UI. Reports land in `data/outputs/compare/` as `.md` and `.json`.
4. Read the metrics:
   * `f1` / `similarity` – word-level match against your reference. **This is the real quality signal.**
   * `coverage` – words captured vs. the most complete parser. Low coverage on a scanned/mixed doc means the parser silently dropped pages.
   * `agreement` – how similar a parser is to the others. **Consensus is not correctness**; two text-only engines can agree while both missing a scanned page. That's why the heuristic (coverage × agreement) is only used when no reference exists.
   * `tables`, `headings` – structure retained. Word-F1 does *not* measure table structure; open the Markdown preview for table-heavy documents.
   * `elapsed_ms` – speed/cost trade-off.
5. Update `_rules()` in `router.py` with what you learned (for example "invoices → `vlm`", "tables-heavy digital PDFs → `docling`").
6. Later: add `--include-paid` (or `"include_paid": true` in the compare API) to put Azure Document Intelligence in the same table and see whether it justifies its cost.

**Tip for the VLM:** use `max_pages` while testing; a 7B vision model on CPU can take minutes per page.

---

## 5. Output JSON contract

```json
{
  "metadata": { "file_name": "x.pdf", "file_type": "pdf", "engine": "pymupdf",
                "page_count": 2, "file_id": "f-001", "tenant_id": "tenant-42" },
  "content": "# Title\n\nWhole document as Markdown …",
  "pages": [
    { "page_number": 1,
      "content": "page Markdown",
      "elements": [
        { "content_type": "text",  "content": "## Heading", "metadata": { "engine": "pymupdf", "file_name": "x.pdf" } },
        { "content_type": "table", "content": "| a | b |\n|---|---|\n| 1 | 2 |", "metadata": {} },
        { "content_type": "image", "content": "", "image_format": "png",
          "image_size_bytes": 20480, "image": "<base64 bytes>", "metadata": {} }
      ] }
  ],
  "routing": { "selected": "pymupdf", "reason": "…", "candidates": ["pymupdf","pdfminer"],
               "attempts": [ { "parser": "pymupdf", "status": "ok", "ms": 38 } ],
               "profile": { "classification": "digital", "page_count": 2, "…": "…" } },
  "stats": { "pages": 2, "words": 410, "tables": 1, "images": 1, "headings": 5, "empty_pages": 0 },
  "timings_ms": { "analyze_route": 12, "parse": 40, "total": 52 },
  "warnings": []
}
```

Images are JSON-safe base64 (`include_images=true` on the sync API; always included in job outputs). Raw bytes are available in-process via `Element.image`.

---

## 6. Common tasks

**Add a new parser (e.g. LlamaParse, Unstructured, Marker)**
1. Create `app/parsers/my_parser.py`, subclass `BaseParser`, set `name`, `supported_types`, implement `is_available()` and `parse()` returning a `ParsedDocument`, decorate with `@register`.
2. Add the module to the import list in `app/parsers/__init__.py`.
3. It now appears in `/api/providers`, the UI dropdown and the compare table automatically. To let the router use it, add it to `_rules()`.

**Switch from upload to blob URL**
No code change. Send the JSON body to `POST /api/parse` (or `/api/jobs`) with `file_path` set to the blob URL. For private blobs either append a SAS token to the URL or set `AZURE_STORAGE_CONNECTION_STRING` and use the plain URL / `azure://container/blob`. Set `OUTPUT_BACKEND=azure` to write outputs back to blob storage.

**Change the OCR language** – `"options": {"ocr_lang": "eng+hin"}` (the Tesseract language pack must be installed).

**Use a different vision model** – `ollama pull llava` then `"options": {"vlm_model": "llava"}` or set `VLM_MODEL`.

---

## 7. Known limitations (be aware before trusting the numbers)

* **Parsers tested for real here:** `pdfminer`, `pdfplumber`, `markitdown` (PDF), `ocr`, `docx`, `pptx`, `spreadsheet`, `text`. **Written from current docs but never executed:** `pymupdf`, `pymupdf4llm`, `hybrid_pdf` (PyMuPDF calls), `opendataloader`, `llamaparse`, `unstructured`, `easyocr`, `docling`, `vlm`, `azure_di`. Install each and run `python scripts/compare.py <file>` – failures show up as an `error` row with the reason, they do not crash the run.
* **Testing status.** In the sandbox where this was built, PyMuPDF/FastAPI could not be installed (no network). The following were run and pass: file-type detection, analyzer logic, routing, DOCX/PPTX/XLSX/CSV/text/image-OCR parsers, pdfminer, normalizer, comparison harness, job store + worker, storage safety checks, and the PDF routing flow (digital → scanned → mixed) using a small stand-in for PyMuPDF. **Not executed on real libraries (details in the bullet above):** the PyMuPDF-specific calls (`find_tables`, font-size headings, image extraction), the FastAPI app and UI, the Ollama VLM call, Azure Blob access, `azure_di` and `docling`. Run `python -m unittest discover -s tests -v` and the UI on your machine first; with PyMuPDF installed the two PDF tests also run.
* The `azure_di` and `docling` parsers are written against current SDK docs; if your installed version differs, only their `_analyze` / `parse` bodies need adjusting.
* Heading detection in PDFs is a font-size heuristic; the VLM or Docling will generally do better on complex layouts.
* Multi-column PDFs, rotated pages and forms are where engines differ most – include some in your test set.
* SQLite and in-process worker threads are POC-grade. For production use a real queue (Azure Queue/Service Bus) and Azure SQL/Postgres.
* Add authentication before exposing the API; `ALLOWED_URL_HOSTS` should be set to your storage account host.
