# Which parser is best for which document: a fresh head-to-head test

Date: 2026-10-23. 62 test documents, 786 runs. Nothing from older reports or scorecards was used: every parser was run on every document it supports and scored against a hand-written answer file.

## The answer in one table

What Smart Extract (By document mode) now uses for each kind of document. Rule: the highest score wins; parsers within 0.1 points of the best are tied and the fastest of them goes first. Paid parsers are only used when "Include paid parsers" is ticked. **vlm is switched off everywhere in the app** (Smart Extract, Compare, Benchmark runs and Single parse): it sends every page to the Azure OpenAI model (one API call per page), which would mean a huge number of API hits. It is still measured below, and it scored well on scans, but nothing runs it unless VLM_PARSER_ENABLED is set to true.

| Document type | Documents tested | Free mode: first parser | Score | Paid allowed: first parser | Score |
|---|---|---|---|---|---|
| Digital text PDF | 6 | pymupdf | 4.94 | pymupdf | 4.94 |
| Digital PDF with tables | 15 | opendataloader | 4.45 | opendataloader | 4.45 |
| PDF with charts, figures or images | 13 | pymupdf4llm | 3.29 | smart_pdf | 3.86 |
| Mixed PDF (text pages and scanned pages) | 3 | pymupdf4llm | 4.42 | pymupdf4llm | 4.42 |
| Scanned PDF | 8 | docling | 3.47 | docling | 3.47 |
| Image files | 4 | docling | 4.85 | docling | 4.85 |
| Word | 3 | docx | 4.10 | docx | 4.10 |
| PowerPoint | 2 | pptx | 4.86 | pptx | 4.86 |
| PowerPoint with charts (real chart objects) | 1 | docling | 4.79 | docling | 4.79 |
| Excel | 2 | spreadsheet | 4.33 | spreadsheet | 4.33 |
| Excel with charts (real chart objects) | 1 | spreadsheet | 5.00 | spreadsheet | 5.00 |
| CSV | 2 | spreadsheet | 5.00 | spreadsheet | 5.00 |
| Plain text | 2 | text | 5.00 | text | 5.00 |

Scores are 0 to 5 (average of the parameters a document can test). By part mode uses the same data per part: tables go to the parser with the best table-reconstruction score, scanned pages to the best scanned score, pictures to the best image score; charts and figures are read by the vision model; text and headings come from the first PyMuPDF pass.

## Parser against parser, per document type

Higher is better. A crash or a timeout counts as 0 on every parameter the document can test. Seconds are the median per document.

### Digital text PDF (6 documents)

Documents: AI_agent_p1-3, contract, form_fields, multilingual, resume, rotated_pages.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| pymupdf | 4.94 | 4.97 | - | - | 4.77 | 0.0 | 0 | 6 |
| hybrid_pdf (PyMuPDF + Tesseract OCR) | 4.94 | 4.97 | - | - | 4.77 | 0.1 | 0 | 6 |
| smart_pdf (PyMuPDF + Tesseract OCR + a vision model for charts and figures) (paid) | 4.94 | 4.97 | - | - | 4.77 | 0.1 | 0 | 6 |
| opendataloader | 4.75 | 4.80 | - | - | 4.48 | 2.7 | 0 | 6 |
| haystack_converter | 4.63 | 4.97 | - | - | 3.22 | 0.1 | 0 | 6 |
| langchain_loader | 4.63 | 4.97 | - | - | 3.22 | 0.3 | 0 | 6 |
| llamaindex_reader | 4.63 | 4.97 | - | - | 3.22 | 0.4 | 0 | 6 |
| pymupdf4llm | 4.60 | 4.58 | - | - | 4.42 | 1.5 | 0 | 6 |
| pdfplumber | 4.47 | 4.80 | - | - | 2.97 | 0.1 | 0 | 6 |
| ... 6 more parsers scored lower | | | | | | | | |

### Digital PDF with tables (15 documents)

Documents: 02_invoice_purchase_order, 03_legal_contract, 05_healthcare_discharge_summary, 06_insurance_claim_form, 07_logistics_shipping_manifest, 08_software_incident_report, balance_sheet, bank_statement, datasheet, digital, invoice, lab_report, multipage_table, purchase_order, two_column_paper.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| docling | 4.50 | 4.45 | 4.99 | - | 4.22 | 27.5 | 0 | 15 |
| opendataloader | 4.45 | 4.37 | 4.97 | - | 4.15 | 2.7 | 0 | 15 |
| pymupdf4llm | 4.44 | 4.37 | 4.96 | - | 4.17 | 2.8 | 0 | 15 |
| pymupdf | 4.31 | 4.23 | 4.77 | - | 3.98 | 0.2 | 0 | 15 |
| hybrid_pdf (PyMuPDF + Tesseract OCR) | 4.31 | 4.23 | 4.77 | - | 3.98 | 0.4 | 0 | 15 |
| smart_pdf (PyMuPDF + Tesseract OCR + a vision model for charts and figures) (paid) | 4.31 | 4.23 | 4.77 | - | 3.98 | 0.3 | 0 | 15 |
| pdfplumber | 4.10 | 4.35 | 4.84 | - | 2.30 | 0.2 | 0 | 15 |
| markitdown | 3.76 | 4.29 | 2.56 | - | 2.68 | 0.5 | 0 | 15 |
| haystack_converter | 3.37 | 4.36 | 0.00 | - | 2.73 | 0.1 | 0 | 15 |
| ... 6 more parsers scored lower | | | | | | | | |

### PDF with charts, figures or images (13 documents)

Documents: 01_corporate_annual_report, 04_scientific_research_paper, 10_mixed_parser_killer, Generative_AI_p1-6, Overview of Amazon Web Services - Overview of Amazon Web Services, PIB_home_p1-6, annual_report_page, chart_report, chart_sample, datasheet_with_photo, flowchart_doc, product_brochure, slides.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| smart_pdf (PyMuPDF + Tesseract OCR + a vision model for charts and figures) (paid) | 3.88 | 3.26 | 4.54 | 4.83 | 2.72 | 0.5 | 0 | 13 |
| pymupdf4llm | 3.32 | 3.92 | 3.94 | 1.07 | 3.33 | 7.4 | 0 | 13 |
| opendataloader | 3.17 | 3.83 | 3.94 | 0.60 | 3.24 | 3.4 | 0 | 13 |
| pymupdf | 3.02 | 3.63 | 3.80 | 0.60 | 3.02 | 0.3 | 0 | 13 |
| hybrid_pdf (PyMuPDF + Tesseract OCR) | 3.02 | 3.63 | 3.80 | 0.60 | 3.02 | 0.3 | 0 | 13 |
| pdfplumber | 3.01 | 3.84 | 3.96 | 0.60 | 1.98 | 0.3 | 0 | 13 |
| docling | 2.92 | 3.65 | 3.94 | 0.60 | 3.41 | 28.7 | 0 | 13 |
| markitdown | 2.53 | 3.67 | 1.10 | 0.00 | 2.04 | 0.7 | 0 | 13 |
| haystack_converter | 2.52 | 3.78 | 0.00 | 0.60 | 2.12 | 0.2 | 0 | 13 |
| ... 6 more parsers scored lower | | | | | | | | |

### Mixed PDF (text pages and scanned pages) (3 documents)

Documents: AI_agent_mixed, mixed, mixed_digital_scanned.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| docling | 4.51 | 4.30 | 5.00 | - | 4.00 | 42.5 | 0 | 3 |
| pymupdf4llm | 4.42 | 4.30 | 4.55 | - | 4.00 | 8.0 | 0 | 3 |
| hybrid_pdf (PyMuPDF + Tesseract OCR) | 3.83 | 4.20 | 2.50 | - | 3.33 | 4.3 | 0 | 3 |
| smart_pdf (PyMuPDF + Tesseract OCR + a vision model for charts and figures) (paid) | 3.83 | 4.20 | 2.50 | - | 3.33 | 9.6 | 0 | 3 |
| easyocr | 3.32 | 4.30 | 0.00 | - | 2.07 | 64.1 | 0 | 3 |
| ocr | 3.11 | 4.13 | 0.00 | - | 2.07 | 8.4 | 0 | 3 |
| pymupdf | 2.99 | 3.03 | 2.50 | - | 2.77 | 0.1 | 0 | 3 |
| opendataloader | 2.98 | 3.03 | 2.50 | - | 2.70 | 2.7 | 0 | 3 |
| pdfplumber | 2.79 | 3.07 | 2.50 | - | 1.53 | 0.1 | 0 | 3 |
| ... 6 more parsers scored lower | | | | | | | | |

### Scanned PDF (8 documents)

Documents: 09_scanned_maintenance_order, AI_agent_scanned_clean, AI_agent_scanned_noisy, infographic, scanned_invoice_clean, scanned_invoice_low_quality, scanned_invoice_skewed_noisy, scanned_report_page.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| docling | 3.47 | 4.21 | 3.10 | 0.00 | 3.80 | 37.6 | 0 | 8 |
| pymupdf4llm | 3.25 | 4.24 | 2.05 | 0.00 | 3.76 | 10.2 | 0 | 8 |
| unstructured | 2.88 | 4.04 | 0.00 | 1.20 | 3.44 | 15.5 | 0 | 8 |
| easyocr | 2.70 | 4.19 | 0.00 | 0.00 | 2.48 | 68.4 | 0 | 8 |
| hybrid_pdf (PyMuPDF + Tesseract OCR) | 2.53 | 3.90 | 0.00 | 0.00 | 2.56 | 3.0 | 0 | 8 |
| ocr | 2.53 | 3.90 | 0.00 | 0.00 | 2.56 | 3.2 | 0 | 8 |
| smart_pdf (PyMuPDF + Tesseract OCR + a vision model for charts and figures) (paid) | 2.53 | 3.90 | 0.00 | 0.00 | 2.56 | 7.5 | 0 | 8 |
| pymupdf | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0 | 0 | 8 |
| pdfminer | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0 | 0 | 8 |
| ... 6 more parsers scored lower | | | | | | | | |

### Image files (4 documents)

Documents: handwritten_note.png, id_card.png, receipt_photo.jpg, screenshot.png.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| docling | 4.85 | 4.85 | - | - | 4.90 | 12.6 | 0 | 4 |
| easyocr | 4.68 | 4.75 | - | - | 4.55 | 8.2 | 0 | 4 |
| ocr | 4.51 | 4.50 | - | - | 4.75 | 0.6 | 0 | 4 |
| unstructured | 4.44 | 4.47 | - | - | 4.60 | 3.7 | 0 | 4 |

### Word (3 documents)

Documents: procedure.docx, report.docx, report_with_figures.docx.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| unstructured | 4.20 | 4.60 | 4.10 | 2.50 | 4.53 | 0.4 | 0 | 3 |
| docling | 4.17 | 4.60 | 3.90 | 2.50 | 4.53 | 0.8 | 0 | 3 |
| docx | 4.10 | 4.53 | 3.90 | 2.50 | 4.53 | 0.1 | 0 | 3 |
| markitdown | 3.96 | 4.47 | 4.10 | 2.50 | 3.53 | 0.6 | 0 | 3 |

### PowerPoint (2 documents)

Documents: deck.pptx, slides.pptx.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| pptx | 4.86 | 4.75 | 5.00 | - | 4.85 | 0.0 | 0 | 2 |
| docling | 4.62 | 4.30 | 5.00 | - | 4.65 | 0.3 | 0 | 2 |
| unstructured | 4.56 | 4.30 | 5.00 | - | 4.25 | 0.2 | 0 | 2 |
| markitdown | 4.51 | 4.75 | 5.00 | - | 4.35 | 0.2 | 0 | 2 |

### PowerPoint with charts (real chart objects) (1 documents)

Documents: dashboard.pptx.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| docling | 4.79 | 4.80 | 4.80 | 5.00 | 4.30 | 1.3 | 0 | 1 |
| markitdown | 3.84 | 4.00 | 3.40 | 5.00 | 3.70 | 0.7 | 0 | 1 |
| pptx | 2.76 | 3.30 | 2.70 | 0.00 | 3.70 | 0.0 | 0 | 1 |
| unstructured | 2.76 | 3.30 | 2.70 | 0.00 | 3.70 | 0.4 | 0 | 1 |

### Excel (2 documents)

Documents: multi_sheet.xlsx, sales.xlsx.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| unstructured | 4.45 | 4.50 | 4.65 | - | 4.15 | 1.4 | 0 | 2 |
| spreadsheet | 4.33 | 4.40 | 4.40 | - | 4.20 | 0.0 | 0 | 2 |
| markitdown | 4.33 | 4.35 | 4.50 | - | 4.15 | 0.2 | 0 | 2 |
| docling | 4.26 | 4.45 | 4.45 | - | 3.50 | 0.4 | 0 | 2 |

### Excel with charts (real chart objects) (1 documents)

Documents: sales_with_chart.xlsx.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| spreadsheet | 5.00 | 5.00 | 5.00 | - | 5.00 | 0.1 | 0 | 1 |
| markitdown | 5.00 | 5.00 | 5.00 | - | 5.00 | 0.5 | 0 | 1 |
| unstructured | 4.43 | 4.80 | 5.00 | - | 2.30 | 2.4 | 0 | 1 |
| docling | 3.05 | 3.10 | 3.40 | - | 1.60 | 1.0 | 0 | 1 |

### CSV (2 documents)

Documents: parts.csv, sales.csv.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| spreadsheet | 5.00 | 5.00 | 5.00 | - | 5.00 | 0.8 | 0 | 2 |
| markitdown | 5.00 | 5.00 | 5.00 | - | 5.00 | 1.8 | 0 | 2 |
| unstructured | 5.00 | 5.00 | 5.00 | - | 5.00 | 2.2 | 0 | 2 |

### Plain text (2 documents)

Documents: runbook.md, shift_notes.txt.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| text | 5.00 | 5.00 | 5.00 | - | 5.00 | 0.0 | 0 | 2 |
| unstructured | 2.08 | 2.50 | 0.00 | - | 2.50 | 0.1 | 1 | 2 |


## What our two combinations are made of

- **hybrid_pdf** = PyMuPDF reads the pages that have text, **Tesseract OCR** reads the pages that are only a picture.
- **smart_pdf** = the same as hybrid_pdf, plus a **vision model** that reads charts, diagrams and pictures (at most 8 figures per document). Tables are read by PyMuPDF's table finder, never by the vision model; scanned pages are read by Tesseract OCR, not by the vision model.

## Tables in documents that also have charts or photos

Table-reconstruction score (0 to 5) per document, for the documents of the group "PDF with charts, figures or images" that contain a table. Where the table is a normal text table (datasheet_with_photo, flowchart_doc, product_brochure, slides) every parser reads it, and smart_pdf ties with the others, except on slides. Where smart_pdf is clearly ahead (annual_report_page, chart_report, chart_sample) the answer file also lists the values read from the chart as a table, which only a vision model can supply. So smart_pdf's higher table average in this group comes from chart values, not from better normal tables.

| Document | smart_pdf | pymupdf4llm | docling | opendataloader | pymupdf |
|---|---|---|---|---|---|
| annual_report_page | 4.1 | 3.0 | 3.0 | 3.0 | 3.0 |
| chart_report | 4.6 | 2.1 | 2.1 | 2.1 | 2.1 |
| chart_sample | 4.6 | 2.5 | 2.5 | 2.5 | 1.5 |
| datasheet_with_photo | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| flowchart_doc | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| product_brochure | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| slides | 3.5 | 5.0 | 5.0 | 5.0 | 5.0 |

## Failures, timeouts and what they mean

| Parser | Problem | Documents |
|---|---|---|
| docling | error | 1 |
| easyocr | timeout | 8 |
| unstructured | error | 1 |

Timeouts mean one document took longer than 400 seconds. easyocr is the slow one (about a minute per document on this CPU-only laptop).

## Smart Extract on documents that mix text, tables, charts, photos and diagrams

These were run through the real app (By document with paid parsers allowed, By part with paid parsers allowed, and By document with free parsers only), with the final routing table. Azure Document Intelligence was blocked in this test. Score is 0 to 5 against the hand-written answer.

| Document | By document (paid allowed) | By part (paid allowed) | By document (free only) |
|---|---|---|---|
| 01_corporate_annual_report.pdf | 2.53 (smart_pdf) | 2.54 (pymupdf, vision:azure_openai, smart_pdf) | 2.45 (pymupdf4llm) |
| 02_invoice_purchase_order.pdf | 3.75 (opendataloader) | 3.75 (pymupdf, smart_pdf) | - |
| 03_legal_contract.pdf | 3.63 (opendataloader) | 3.47 (pymupdf, smart_pdf) | - |
| 04_scientific_research_paper.pdf | 2.84 (smart_pdf) | 2.84 (pymupdf, smart_pdf, vision:azure_openai) | 3.19 (pymupdf4llm) |
| 05_healthcare_discharge_summary.pdf | 3.22 (opendataloader) | 3.22 (pymupdf, smart_pdf) | - |
| 06_insurance_claim_form.pdf | 3.19 (opendataloader) | 3.19 (pymupdf, smart_pdf) | - |
| 07_logistics_shipping_manifest.pdf | 3.57 (opendataloader) | 3.33 (pymupdf, smart_pdf) | - |
| 08_software_incident_report.pdf | 3.18 (opendataloader) | 3.18 (pymupdf, smart_pdf) | - |
| 09_scanned_maintenance_order.pdf | 5.00 (docling) | 5.00 (docling) | - |
| 10_mixed_parser_killer.pdf | 2.23 (smart_pdf) | 1.99 (pymupdf, vision:azure_openai, smart_pdf) | 2.72 (pymupdf4llm) |
| annual_report_page.pdf | 3.84 (smart_pdf) | 3.84 (pymupdf, vision:azure_openai, smart_pdf) | 3.25 (pymupdf4llm) |
| dashboard.pptx | 4.80 (docling) | - | - |
| datasheet_with_photo.pdf | 3.87 (smart_pdf) | 3.87 (pymupdf, vision:azure_openai, smart_pdf) | 4.94 (pymupdf4llm) |
| flowchart_doc.pdf | 4.12 (smart_pdf) | 4.12 (pymupdf, vision:azure_openai, smart_pdf) | 4.40 (pymupdf4llm) |
| infographic.pdf | 4.78 (docling) | 4.78 (docling) | 4.78 (docling) |
| product_brochure.pdf | 4.11 (smart_pdf) | 4.11 (pymupdf, vision:azure_openai, smart_pdf) | 4.92 (pymupdf4llm) |
| report_with_figures.docx | 3.44 (unstructured) | - | - |
| sales_with_chart.xlsx | 5.00 (spreadsheet) | - | - |
| scanned_report_page.pdf | 3.16 (docling) | 3.16 (docling) | 3.16 (docling) |

Average score over these documents: By document: 3.70 (19 documents), By part: 3.52 (16 documents), By document, free only: 3.76 (9 documents).

**What this shows.** On the 9 documents that were run both ways, the free parsers scored higher on 5 (04_scientific_research_paper, 10_mixed_parser_killer, datasheet_with_photo, flowchart_doc, product_brochure) and the paid vision path on 2 (01_corporate_annual_report, annual_report_page). The vision model clearly helps when the values only exist inside a chart, and it costs points when the document is mostly text with photos or diagrams, because the model adds descriptions that are not in the answer. The "charts and figures" routing group mixes both kinds, so its first pick (smart_pdf when paid parsers are allowed) is right on average but not on every document.

**Reading the scores.** The ten Copilot documents (names starting 01 to 10) score lower for every parser, because their answer files are summaries and not the full text. Compare parsers on the same document, not documents with each other.

## Cost, honestly

- **vlm** sends every page to Azure OpenAI (GPT-4.1): one API call per page. It ran on all test documents, so the Azure bill shows those calls. **The vlm parser is now off in the whole app** (setting VLM_PARSER_ENABLED, default off), to keep API hits low.
- **smart_pdf** sends every figure it finds to the vision model (up to 8 per document). Smart Extract only uses it when "Include paid parsers" is ticked, and By part mode also reads figures with the vision model.
- Azure Document Intelligence was **not** run, so it is not in any ranking here.

## Limits of this test

- The documents are synthetic (generated, plus the ten from the Copilot set). They are cleaner than most real files. Scans are simulated with skew, noise and blur.
- One run per parser and document. Differences under about 0.1 are noise, which is why such parsers are treated as tied.
- The answer files were written by hand. The Copilot answer files are summaries: they leave out headers and footers and include chart values that exist only inside the picture, so they under-score correct output a little and reward parsers that read charts.
- The "tables" group means clean digital PDFs with simple tables. Merged cells, tilted tables and tables inside photos are not covered.
- Timings are not exact: models load on first use, the laptop slept during part of the run and the disk was nearly full. Use them only to break ties.
- Not tested: Azure Document Intelligence, LlamaParse (no API key), MinerU, Marker, documents of 100 pages or more, real client files.
