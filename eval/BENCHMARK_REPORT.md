# Parser benchmark report: which parser is best, and what replaces Azure DI

## The short answer

Two kinds of entries are compared. **Ready-made tools** are published parsers (Azure DI, pymupdf4llm, Docling and so on). **Our combos** (`hybrid_pdf`, `smart_pdf`) are written in this repo and glue existing pieces together: hybrid_pdf = PyMuPDF + Tesseract OCR; smart_pdf = PyMuPDF + Tesseract OCR + a vision model (Azure OpenAI) for figures. A combo winning means the combination works, not that a new parser exists.

- **Reference:** Azure Document Intelligence (ADI) scored **28.2 / 40** overall and is the best ready-made tool.
- **Best free ready-made alternative to ADI: pymupdf4llm** (27.9 / 40, 13.6 s per document). On mixed and scanned PDFs it is within 0.3 to 0.7 points of ADI.
- **Docling** (ready-made) matches ADI on quality (mixed 29.9, scanned 24.6) but is about 4 times slower than pymupdf4llm (56 s per document on average, 91 s on figure-heavy files).
- **Our combo hybrid_pdf** is the fastest option for digital PDFs and PDFs with tables (ties ADI: 25.0 on digital, 30.0 on a table PDF, 0.5 to 1.4 s). It is weak on scans (no headings).
- **Charts and diagrams: no ready-made parser reads them, including ADI** (Charts = 0). Only **our combo smart_pdf** did (Charts 4.5, Diagrams 5.0), because it adds a vision model. It costs one vision call per figure, so it is not a like-for-like comparison with the ready-made tools.
- **Not worth keeping:** LangChain, LlamaIndex and Haystack loaders (15.2: no OCR, no tables), OpenDataLoader (18.4: nothing on scans), pdfminer, pdfplumber, markitdown, pymupdf (cannot read scans at all).

### Overall ranking, ready-made tools only

| # | parser | Total /40 | secs per document |
|---|---|---|---|
| 1 | **azure_di** (paid) | 28.2 | 10.5 |
| 2 | **pymupdf4llm** | 27.9 | 13.6 |
| 3 | **docling** | 25.1 | 56.4 |
| 4 | **easyocr** | 21.2 | 199.7 |
| 5 | **ocr** (Tesseract) | 21.1 | 8.0 |
| 6 | **pymupdf** | 18.6 | 1.9 |
| 7 | **opendataloader** | 18.4 | 2.5 |
| 8 | **markitdown, pdfplumber** | 17.4 | 0.4 to 0.8 |
| 9 | **langchain, llamaindex, haystack loaders** | 15.2 | 0.2 |
| 10 | **pdfminer** | 15.1 | 0.3 |

### Our combos

| combo | built from | Total /40 | secs per document |
|---|---|---|---|
| **smart_pdf** | PyMuPDF + Tesseract OCR + vision model | 34.7 | 15.3 |
| **hybrid_pdf** | PyMuPDF + Tesseract OCR | 28.4 | 3.6 |

## How the scoring works

Every parser ran on every PDF that has a hand-written answer key. Eight parameters, 0 to 5 each (same parameters as the Azure IDP vs OpenDataLoader email): Text, Tables, Charts, Diagrams (infographic), Numbers (entity and numeric fidelity), Structure, Complete, No-invent (5 = nothing made up). A parameter only counts when the document has something to test it with, so the total /40 is only comparable inside one table.

## Overall (all documents)

| parser | Text | Tables | Charts | Diagrams | Numbers | Structure | Complete | No-invent | **Total /40** | secs |
|---|---|---|---|---|---|---|---|---|---|---|
| **smart_pdf** (our combo: PyMuPDF + Tesseract + vision model) | 4.3 | 4.9 | 4.5 | 5.0 | 3.8 | 3.3 | 4.9 | 4.0 | **34.7** | 15.3 |
| **hybrid_pdf** (our combo: PyMuPDF + Tesseract) | 4.6 | 4.2 | 0.0 | 2.5 | 4.3 | 3.5 | 4.8 | 4.5 | **28.4** | 3.6 |
| **azure_di** | 4.3 | 4.2 | 0.0 | 2.5 | 4.0 | 4.3 | 4.8 | 4.1 | **28.2** | 10.5 |
| **pymupdf4llm** | 4.2 | 4.2 | 0.0 | 2.5 | 4.2 | 4.0 | 4.8 | 4.0 | **27.9** | 13.6 |
| **docling** | 4.2 | 4.2 | 0.0 | 0.0 | 3.9 | 4.1 | 4.6 | 4.2 | **25.1** | 56.4 |
| **easyocr** | 4.2 | 0.0 | 0.0 | 2.5 | 3.6 | 2.0 | 4.7 | 4.1 | **21.2** | 199.7 |
| **ocr** | 4.3 | 0.0 | 0.0 | 2.5 | 3.4 | 2.1 | 4.7 | 4.1 | **21.1** | 8.0 |
| **pymupdf** | 3.2 | 2.1 | 0.0 | 0.6 | 3.3 | 2.7 | 3.3 | 3.3 | **18.6** | 1.9 |
| **opendataloader** | 3.2 | 2.1 | 0.0 | 0.6 | 3.3 | 2.7 | 3.2 | 3.3 | **18.4** | 2.5 |
| **markitdown** | 3.2 | 2.1 | 0.0 | 0.6 | 3.3 | 1.5 | 3.3 | 3.3 | **17.4** | 0.8 |
| **pdfplumber** | 3.2 | 2.1 | 0.0 | 0.6 | 3.3 | 1.6 | 3.3 | 3.3 | **17.4** | 0.4 |
| **langchain_loader** | 3.2 | 0.0 | 0.0 | 0.6 | 3.3 | 1.5 | 3.3 | 3.3 | **15.2** | 0.2 |
| **llamaindex_reader** | 3.2 | 0.0 | 0.0 | 0.6 | 3.3 | 1.5 | 3.3 | 3.3 | **15.2** | 0.2 |
| **haystack_converter** | 3.2 | 0.0 | 0.0 | 0.6 | 3.3 | 1.5 | 3.3 | 3.3 | **15.2** | 0.2 |
| **pdfminer** | 3.2 | 0.0 | 0.0 | 0.6 | 3.2 | 1.5 | 3.3 | 3.3 | **15.1** | 0.3 |

## Digital PDF (1 document)

| parser | Text | Tables | Charts | Diagrams | Numbers | Structure | Complete | No-invent | **Total /40** | secs |
|---|---|---|---|---|---|---|---|---|---|---|
| **hybrid_pdf** (our combo: PyMuPDF + Tesseract) | 5.0 | - | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **25.0** | 1.4 |
| **smart_pdf** (our combo: PyMuPDF + Tesseract + vision model) | 5.0 | - | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **25.0** | 1.5 |
| **pymupdf** | 5.0 | - | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **25.0** | 1.5 |
| **docling** | 5.0 | - | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **25.0** | 27.6 |
| **opendataloader** | 5.0 | - | - | - | 5.0 | 4.9 | 5.0 | 5.0 | **24.9** | 2.2 |
| **azure_di** | 5.0 | - | - | - | 4.9 | 4.9 | 5.0 | 4.9 | **24.7** | 9.7 |
| **pymupdf4llm** | 4.8 | - | - | - | 4.9 | 4.8 | 5.0 | 4.6 | **24.2** | 2.2 |
| **pdfplumber** | 5.0 | - | - | - | 5.0 | 2.5 | 5.0 | 5.0 | **22.5** | 1.3 |
| **markitdown** | 5.0 | - | - | - | 5.0 | 2.5 | 5.0 | 5.0 | **22.5** | 2.1 |
| **pdfminer** | 5.0 | - | - | - | 5.0 | 2.5 | 5.0 | 5.0 | **22.5** | 0.8 |
| **langchain_loader** | 5.0 | - | - | - | 5.0 | 2.5 | 5.0 | 5.0 | **22.5** | 0.3 |
| **llamaindex_reader** | 5.0 | - | - | - | 5.0 | 2.5 | 5.0 | 5.0 | **22.5** | 0.2 |
| **haystack_converter** | 5.0 | - | - | - | 5.0 | 2.5 | 5.0 | 5.0 | **22.5** | 0.2 |
| **easyocr** | 4.9 | - | - | - | 4.6 | 2.5 | 4.9 | 4.8 | **21.6** | 201.2 |
| **ocr** | 4.9 | - | - | - | 3.7 | 2.5 | 4.9 | 4.9 | **20.8** | 8.4 |

## Digital PDF with tables (1 document)

| parser | Text | Tables | Charts | Diagrams | Numbers | Structure | Complete | No-invent | **Total /40** | secs |
|---|---|---|---|---|---|---|---|---|---|---|
| **docling** | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **30.0** | 10.4 |
| **opendataloader** | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **30.0** | 1.7 |
| **pymupdf4llm** | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **30.0** | 1.1 |
| **hybrid_pdf** (our combo: PyMuPDF + Tesseract) | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **30.0** | 0.5 |
| **smart_pdf** (our combo: PyMuPDF + Tesseract + vision model) | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **30.0** | 0.5 |
| **pymupdf** | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **30.0** | 0.4 |
| **azure_di** | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **30.0** | 6.9 |
| **markitdown** | 5.0 | 5.0 | - | - | 5.0 | 2.5 | 5.0 | 5.0 | **27.5** | 0.2 |
| **pdfplumber** | 5.0 | 5.0 | - | - | 5.0 | 2.5 | 5.0 | 5.0 | **27.5** | 0.0 |
| **easyocr** | 5.0 | 0.0 | - | - | 5.0 | 2.5 | 5.0 | 5.0 | **22.5** | 29.6 |
| **langchain_loader** | 5.0 | 0.0 | - | - | 5.0 | 2.5 | 5.0 | 5.0 | **22.5** | 0.0 |
| **llamaindex_reader** | 5.0 | 0.0 | - | - | 5.0 | 2.5 | 5.0 | 5.0 | **22.5** | 0.0 |
| **haystack_converter** | 5.0 | 0.0 | - | - | 5.0 | 2.5 | 5.0 | 5.0 | **22.5** | 0.0 |
| **pdfminer** | 5.0 | 0.0 | - | - | 5.0 | 2.2 | 5.0 | 5.0 | **22.2** | 0.0 |
| **ocr** | 4.9 | 0.0 | - | - | 4.8 | 2.5 | 4.9 | 4.9 | **21.9** | 1.0 |

## Mixed PDF, digital plus scanned pages (2 documents)

| parser | Text | Tables | Charts | Diagrams | Numbers | Structure | Complete | No-invent | **Total /40** | secs |
|---|---|---|---|---|---|---|---|---|---|---|
| **docling** | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **29.9** | 40.3 |
| **azure_di** | 5.0 | 5.0 | - | - | 5.0 | 4.9 | 5.0 | 5.0 | **29.8** | 11.9 |
| **pymupdf4llm** | 4.9 | 5.0 | - | - | 4.9 | 5.0 | 4.9 | 4.8 | **29.5** | 6.8 |
| **hybrid_pdf** (our combo: PyMuPDF + Tesseract) | 5.0 | 5.0 | - | - | 4.8 | 4.2 | 5.0 | 5.0 | **28.9** | 2.7 |
| **smart_pdf** (our combo: PyMuPDF + Tesseract + vision model) | 5.0 | 5.0 | - | - | 4.8 | 4.2 | 5.0 | 5.0 | **28.9** | 2.6 |
| **pymupdf** | 4.0 | 5.0 | - | - | 4.6 | 3.6 | 3.3 | 5.0 | **25.4** | 0.8 |
| **opendataloader** | 4.0 | 5.0 | - | - | 4.6 | 3.5 | 3.3 | 5.0 | **25.3** | 1.6 |
| **pdfplumber** | 4.0 | 5.0 | - | - | 4.6 | 1.9 | 3.3 | 5.0 | **23.8** | 0.3 |
| **markitdown** | 4.0 | 5.0 | - | - | 4.6 | 1.9 | 3.3 | 5.0 | **23.8** | 0.4 |
| **easyocr** | 4.9 | 0.0 | - | - | 4.8 | 2.5 | 4.9 | 4.9 | **22.1** | 130.6 |
| **ocr** | 4.9 | 0.0 | - | - | 4.2 | 2.5 | 4.9 | 4.9 | **21.4** | 4.6 |
| **langchain_loader** | 4.0 | 0.0 | - | - | 4.6 | 1.9 | 3.3 | 5.0 | **18.8** | 0.2 |
| **llamaindex_reader** | 4.0 | 0.0 | - | - | 4.6 | 1.9 | 3.3 | 5.0 | **18.8** | 0.2 |
| **haystack_converter** | 4.0 | 0.0 | - | - | 4.6 | 1.9 | 3.3 | 5.0 | **18.8** | 0.2 |
| **pdfminer** | 4.0 | 0.0 | - | - | 4.6 | 1.8 | 3.3 | 5.0 | **18.7** | 0.1 |

## Scanned PDF (3 documents)

| parser | Text | Tables | Charts | Diagrams | Numbers | Structure | Complete | No-invent | **Total /40** | secs |
|---|---|---|---|---|---|---|---|---|---|---|
| **azure_di** | 5.0 | - | - | - | 4.9 | 5.0 | 5.0 | 5.0 | **24.9** | 9.8 |
| **docling** | 4.9 | - | - | - | 5.0 | 4.9 | 4.9 | 4.9 | **24.6** | 33.9 |
| **pymupdf4llm** | 4.9 | - | - | - | 4.9 | 4.7 | 4.8 | 4.9 | **24.2** | 18.2 |
| **easyocr** | 4.8 | - | - | - | 4.1 | 2.3 | 4.8 | 4.8 | **20.9** | 101.7 |
| **hybrid_pdf** (our combo: PyMuPDF + Tesseract) | 4.9 | - | - | - | 3.6 | 2.5 | 4.9 | 4.9 | **20.6** | 7.9 |
| **smart_pdf** (our combo: PyMuPDF + Tesseract + vision model) | 4.9 | - | - | - | 3.6 | 2.5 | 4.9 | 4.9 | **20.6** | 7.8 |
| **ocr** | 4.9 | - | - | - | 3.6 | 2.5 | 4.9 | 4.9 | **20.6** | 6.0 |
| **opendataloader** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 3.3 |
| **markitdown** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.1 |
| **pdfplumber** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
| **pdfminer** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
| **pymupdf** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.4 |
| **langchain_loader** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
| **llamaindex_reader** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
| **haystack_converter** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |

## PDFs with charts, figures, images and a tax table (5 documents)

| parser | Text | Tables | Charts | Diagrams | Numbers | Structure | Complete | No-invent | **Total /40** | secs |
|---|---|---|---|---|---|---|---|---|---|---|
| **smart_pdf** (our combo: PyMuPDF + Tesseract + vision model) | 3.4 | 4.6 | 4.5 | 5.0 | 3.0 | 2.9 | 4.8 | 2.7 | **30.9** | 30.8 |
| **hybrid_pdf** (our combo: PyMuPDF + Tesseract) | 4.2 | 2.5 | 0.0 | 2.5 | 4.0 | 3.1 | 4.6 | 4.0 | **25.0** | 2.6 |
| **pymupdf** | 4.2 | 2.5 | 0.0 | 2.5 | 4.0 | 3.1 | 4.6 | 4.0 | **25.0** | 3.7 |
| **opendataloader** | 4.0 | 2.5 | 0.0 | 2.5 | 4.0 | 3.1 | 4.4 | 4.0 | **24.5** | 2.5 |
| **markitdown** | 4.2 | 2.7 | 0.0 | 2.5 | 4.0 | 1.9 | 4.6 | 4.0 | **23.8** | 1.3 |
| **pdfplumber** | 4.1 | 2.6 | 0.0 | 2.5 | 4.0 | 2.0 | 4.6 | 3.9 | **23.7** | 0.7 |
| **azure_di** | 3.4 | 2.5 | 0.0 | 2.5 | 2.8 | 3.3 | 4.6 | 2.9 | **22.0** | 11.2 |
| **pymupdf4llm** | 3.3 | 2.5 | 0.0 | 2.5 | 3.3 | 2.9 | 4.8 | 2.7 | **21.9** | 18.3 |
| **langchain_loader** | 4.2 | 0.0 | 0.0 | 2.5 | 4.0 | 1.8 | 4.6 | 4.0 | **21.0** | 0.3 |
| **llamaindex_reader** | 4.2 | 0.0 | 0.0 | 2.5 | 4.0 | 1.8 | 4.6 | 4.0 | **21.0** | 0.3 |
| **haystack_converter** | 4.2 | 0.0 | 0.0 | 2.5 | 4.0 | 1.8 | 4.6 | 4.0 | **21.0** | 0.3 |
| **pdfminer** | 4.1 | 0.0 | 0.0 | 2.5 | 3.8 | 1.9 | 4.5 | 4.0 | **20.9** | 0.5 |
| **docling** | 3.3 | 2.5 | 0.0 | 0.0 | 2.5 | 3.0 | 4.0 | 3.1 | **18.4** | 91.4 |
| **ocr** | 3.4 | 0.0 | 0.0 | 2.5 | 2.8 | 1.5 | 4.4 | 3.1 | **17.7** | 11.7 |
| **easyocr** | 3.3 | 0.0 | 0.0 | 2.5 | 2.4 | 1.5 | 4.5 | 3.0 | **17.2** | 319.8 |

## Which parser for which document

| Document | Pick | Why | Free alternative to ADI |
|---|---|---|---|
| Digital text PDF | hybrid_pdf (our combo) | ties ADI (25.0 vs 24.7), 1.4 s | pymupdf (same score, 1.5 s) |
| PDF with many tables | hybrid_pdf or pymupdf4llm | 30.0, same as ADI, under 1.5 s | pymupdf4llm (keeps Markdown tables) |
| Mixed (digital + scanned) | pymupdf4llm | 29.5 vs ADI 29.8, 6.8 s | docling (29.9) if time does not matter |
| Scanned PDF | pymupdf4llm | 24.2 vs ADI 24.9, 18 s | docling (24.6, 34 s) |
| Charts, diagrams, infographics | smart_pdf (our combo, needs a vision model) | only option that reads values and arrows | none free without a vision model |

## Limits of this test (read before deciding)

- **The test set is small:** 1 digital, 1 table, 2 mixed, 3 scanned and 5 figure documents. Treat small gaps (under about 1 point) as ties.
- **Charts and diagrams are scored on a single PDF** (`chart_sample.pdf`). Their result is a first look, not a proof.
- **smart_pdf's "No-invent" score drops on figure-heavy documents** (2.7) because the vision model adds descriptions that are not in the answer key. That is partly a scoring artefact, not necessarily errors.
- **Not tested:** LlamaParse (API key empty), Unstructured (crashes on import on this machine), MinerU and Marker (not installed), Databricks ai_parse_document (paid, no access).
- **ADI was re-scored** after fixing the scorer so that HTML tags are not counted as words; the other rows come from the first run (their output has almost no HTML).
- **Speed** was measured on one Windows laptop and is only comparable inside this report.

## Large documents (no answer key: closeness to Azure DI, so not absolute accuracy)

Run 1: three PDFs of 24, 39 and 11 pages (74 pages). Run 2: Llama 2 paper (77 pages) and UN SDG Report 2024 (51 pages). Totals are out of 40 against Azure DI's own output; Charts, Diagrams and Tables are left out because they cannot be measured this way.

| Parser | Run 1 total | Run 1 s/page | Run 2 total | Run 2 s/page |
|---|---|---|---|---|
| **pymupdf4llm** | 23.5 | 2.5 | 26.6 | 2.9 |
| **hybrid_pdf** (our combo: PyMuPDF + Tesseract) | 22.7 | 1.5 | 24.4 | 1.1 |
| **pymupdf** | 22.5 | 1.5 | 24.4 | 1.7 |
| **smart_pdf** (our combo: PyMuPDF + Tesseract + vision model) | 21.7 | 2.7 | 24.2 | 2.8 |
| **opendataloader** | 22.4 | 0.3 | 11.7 (Java ran out of memory on the UN report) | 0.5 |
| **docling** | 20.6 | 16.8 | 24.9 | 6.5 on the UN report only |
| **markitdown** | 20.8 | 0.5 | 18.4 | 1.1 |
| **pdfplumber** | 20.7 | 0.4 | 16.7 | 1.1 |
| **azure_di** | reference | 0.8 | reference | 0.7 |

Docling's Llama 2 time is discarded: the laptop went to sleep during that run and the clock read 8 hours. The full report with charts and diagrams is the Claude doc "Free alternatives to Azure Document Intelligence".
