# Document Parsing POC

A FastAPI-based document parsing and comparison platform that routes uploaded files or blob URLs through multiple parsing engines, normalizes output to Markdown, and lets you benchmark engines side by side.

This project is designed for evaluating which parser performs best on a given document type, with support for:
- PDF, DOCX, PPTX, XLSX, and image-based document ingestion
- OCR and vision-assisted parsing
- parser comparison and scoring reports
- async job execution for background processing
- local or Azure-backed storage flows
- browser-based comparison and benchmark views

## What this project does

The application accepts document input, chooses a parser (or compares many), and produces structured Markdown output suitable for downstream extraction and analysis.

The repo includes multiple parser families and evaluation modes:
- PyMuPDF and PyMuPDF4LLM
- PDFMiner and PDFPlumber
- Tesseract OCR
- MarkItDown
- OpenDataLoader
- Unstructured / Docling style integration options
- optional local vision LLM parsing through Ollama
- comparison and benchmarking workflows across engines

## Architecture

```text
doc-parsing/
├── app/
│   ├── static/               # frontend/static UI assets
│   ├── benchmark.py          # benchmark recording and aggregation
│   ├── compare.py            # compare parser outputs and score them
│   ├── config.py             # settings and env config
│   ├── extract.py            # smart extraction by document part
│   ├── jobs/                 # async job queue and worker pool
│   ├── models.py             # schemas/models
│   ├── pipeline.py           # core parse orchestration
│   ├── routing/              # parser selection and file-type logic
│   ├── storage/              # input/output storage handling
│   ├── parsers.py            # parser registry
│   └── main.py               # FastAPI app entrypoint
├── eval/
│   └── ...                   # evaluation-related logic
├── scripts/
│   ├── compare.py            # command-line comparison tool
│   ├── make_samples.py       # sample generation helper
│   └── parse_file.py         # quick single-file parsing CLI
├── samples/
│   └── ...                   # sample documents for testing
├── tests/
│   └── ...                   # unit/integration tests
├── data/
│   └── ...                   # runtime data and outputs
├── .env.example              # example configuration
├── Dockerfile
├── GUIDE.md                  # deeper repo walkthrough
├── requirements.txt
├── requirements-extra.txt
├── README.md
├── .gitignore
└── ...
```

## API overview

The FastAPI app exposes both synchronous and async flows.

### Core endpoints

- `GET /api/health` — health check
- `GET /api/providers` — list available parsers and readiness
- `POST /api/parse/upload` — parse an uploaded file
- `POST /api/parse` — parse from a blob URL or path-backed source
- `POST /api/compare/upload` — compare multiple parsers on one uploaded document
- `POST /api/extract/upload` — smart extraction using the best parser per section
- `POST /api/jobs` — enqueue background parse jobs
- `POST /api/jobs/upload` — enqueue a background job from uploaded file
- `GET /api/jobs` — list jobs
- `GET /api/jobs/{job_id}` — get job status
- `GET /api/jobs/{job_id}/result` — fetch finished result

### Streaming endpoints

The app also exposes streaming variants for live progress:
- `POST /api/compare/upload/stream`
- `POST /api/extract/upload/stream`

## Quick start

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install OCR support

Tesseract is required for OCR-based parsing.

- Ubuntu/Debian:

```bash
sudo apt install tesseract-ocr
```

- macOS:

```bash
brew install tesseract
```

- Windows:
  - install Tesseract from the Windows build and set `TESSERACT_CMD` in `.env`

### 4. Configure environment

```bash
cp .env.example .env
```

The sample config includes settings for:
- local storage
- Azure Blob input/output
- OCR
- Ollama-based vision LLM access
- optional paid integrations
- async worker settings

### 5. Run the app

```bash
uvicorn app.main:app --reload
```

Open:
- http://localhost:8000
- Swagger docs: http://localhost:8000/docs

## Parser comparison workflow

The project is built around comparing parser performance on the same document.

Example CLI usage:

```bash
python scripts/make_samples.py
python scripts/parse_file.py samples/report.docx
python scripts/compare.py samples/*.pdf
python -m unittest discover -s tests -v
```

This is useful for determining which parser gives the best results for:
- scanned PDFs
- structured tables
- image-heavy documents
- forms and invoices
- mixed-content files

## Supported parser families

The core requirements include a large set of parsing libraries, including:

- `pymupdf`
- `pymupdf4llm`
- `pdfminer`
- `pdfplumber`
- `pytesseract`
- `markitdown`
- `openpyxl` / Excel parsing support
- `python-docx` / `python-pptx`
- optional OpenDataLoader-based PDF parsing
- optional local vision LLM parser via Ollama

Heavy/cloud/paid integrations are kept in `requirements-extra.txt`.

## Docker

```bash
docker build -t doc-parsing-poc .
docker run -p 8000:8000 --env-file .env -v $(pwd)/data:/srv/data doc-parsing-poc
```

## Notes

- Input can be uploaded directly or supplied as a blob URL/path.
- Jobs are queued in the background for production-like processing.
- Parser availability is exposed through `/api/providers`.
- The project is oriented toward experimental evaluation and “best parser per document type” selection.

## Extra docs

For deeper implementation details, architecture notes, and parser comparison guidance, see:

- `GUIDE.md`

## License

No explicit license file is present in the repository root. If you intend to reuse or redistribute this project, confirm the licensing terms with the repository owner before publishing or deploying it externally.
