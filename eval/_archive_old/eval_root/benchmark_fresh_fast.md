# Parser scorecard (0-5 per metric, total /40)

Run fresh on every PDF in eval/ that has an answer key. '-' = nothing to test that metric with.

## Overall

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s | s/page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **pymupdf4llm** | 4.2 | 4.2 | 1.6 | 2.5 | 4.3 | 4.0 | 4.7 | 4.2 | **29.7** | 21.3 | 8.1 |
| **azure_di** | 4.3 | 4.4 | 0.7 | 2.5 | 4.3 | 4.3 | 4.7 | 4.2 | **29.3** | 11.4 | 4.4 |
| **hybrid_pdf** | 4.3 | 3.4 | 0.9 | 2.5 | 4.3 | 3.7 | 4.5 | 4.4 | **28.1** | 9.1 | 3.5 |
| **pymupdf** | 3.5 | 3.4 | 0.9 | 2.5 | 3.8 | 3.3 | 3.7 | 3.6 | **24.6** | 3.8 | 1.5 |
| **opendataloader** | 3.3 | 3.5 | 0.9 | 2.5 | 3.6 | 3.1 | 3.4 | 3.4 | **23.8** | 8.8 | 3.4 |
| **pdfplumber** | 3.5 | 3.4 | 0.9 | 2.5 | 3.8 | 1.8 | 3.7 | 3.6 | **23.1** | 1.0 | 0.4 |
| **markitdown** | 3.4 | 2.1 | 0.0 | 2.5 | 3.8 | 1.8 | 3.5 | 3.4 | **20.5** | 1.3 | 0.5 |
| **pdfminer** | 3.1 | 0.0 | 0.0 | 2.5 | 3.4 | 1.6 | 3.3 | 3.2 | **17.1** | 0.5 | 0.2 |

## digital  (7 docs: AI_agent_p1-3.pdf, contract.pdf, form_fields.pdf, long_report.pdf, multilingual.pdf, resume.pdf, rotated_pages.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s | s/page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **hybrid_pdf** | 4.3 | - | - | - | 5.0 | 4.5 | 5.0 | 4.3 | **23.0** | 6.2 | 1.6 |
| **pymupdf** | 4.3 | - | - | - | 5.0 | 4.5 | 5.0 | 4.3 | **23.0** | 7.5 | 1.9 |
| **azure_di** | 4.2 | - | - | - | 4.9 | 4.3 | 4.8 | 4.2 | **22.4** | 14.7 | 3.7 |
| **pymupdf4llm** | 3.9 | - | - | - | 4.6 | 4.1 | 4.5 | 4.3 | **21.5** | 9.7 | 2.4 |
| **pdfplumber** | 4.1 | - | - | - | 5.0 | 2.6 | 4.8 | 4.1 | **20.6** | 1.4 | 0.4 |
| **markitdown** | 3.6 | - | - | - | 5.0 | 2.7 | 4.5 | 3.6 | **19.5** | 2.0 | 0.5 |
| **opendataloader** | 3.4 | - | - | - | 4.1 | 3.5 | 4.0 | 3.6 | **18.7** | 10.3 | 2.6 |
| **pdfminer** | 3.2 | - | - | - | 4.3 | 2.4 | 4.1 | 3.1 | **17.0** | 0.6 | 0.1 |

## digital + charts/images  (7 docs: Generative_AI_p1-6.pdf, Overview of Amazon Web Services - Overview of Amazon Web Services.pdf, PIB_home_p1-6.pdf, SOP  Income Tax Computation Sheet-2026-27.pdf, chart_report.pdf, chart_sample.pdf, slides.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s | s/page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **hybrid_pdf** | 4.1 | 3.2 | 0.9 | 2.5 | 4.0 | 3.3 | 4.3 | 4.2 | **26.6** | 4.2 | 1.1 |
| **pymupdf** | 4.1 | 3.2 | 0.9 | 2.5 | 4.0 | 3.3 | 4.3 | 4.2 | **26.6** | 3.4 | 0.9 |
| **opendataloader** | 4.0 | 3.2 | 0.9 | 2.5 | 4.0 | 3.3 | 4.1 | 4.2 | **26.2** | 6.0 | 1.6 |
| **pdfplumber** | 4.1 | 3.2 | 0.9 | 2.5 | 3.9 | 2.0 | 4.3 | 4.3 | **25.2** | 1.3 | 0.4 |
| **pymupdf4llm** | 3.6 | 3.2 | 1.6 | 2.5 | 3.2 | 3.1 | 4.7 | 3.2 | **25.1** | 20.1 | 5.4 |
| **azure_di** | 3.5 | 3.2 | 0.7 | 2.5 | 2.9 | 3.4 | 4.6 | 3.1 | **23.8** | 10.9 | 2.9 |
| **markitdown** | 4.1 | 2.6 | 0.0 | 2.5 | 4.0 | 1.9 | 4.3 | 4.2 | **23.6** | 1.8 | 0.5 |
| **pdfminer** | 4.1 | 0.0 | 0.0 | 2.5 | 3.8 | 1.9 | 4.3 | 4.2 | **20.8** | 1.0 | 0.3 |

## digital + tables  (9 docs: balance_sheet.pdf, bank_statement.pdf, datasheet.pdf, digital.pdf, invoice.pdf, lab_report.pdf, multipage_table.pdf, purchase_order.pdf, two_column_paper.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s | s/page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **azure_di** | 5.0 | 4.9 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **29.8** | 10.0 | 6.9 |
| **pymupdf4llm** | 5.0 | 5.0 | - | - | 5.0 | 4.9 | 5.0 | 5.0 | **29.8** | 3.7 | 2.5 |
| **opendataloader** | 5.0 | 5.0 | - | - | 5.0 | 4.9 | 5.0 | 5.0 | **29.7** | 8.8 | 6.1 |
| **hybrid_pdf** | 4.9 | 4.8 | - | - | 5.0 | 4.7 | 4.9 | 4.9 | **29.2** | 3.5 | 2.4 |
| **pymupdf** | 4.9 | 4.8 | - | - | 5.0 | 4.7 | 4.9 | 4.9 | **29.2** | 3.2 | 2.2 |
| **pdfplumber** | 5.0 | 4.9 | - | - | 5.0 | 2.2 | 5.0 | 4.9 | **27.0** | 0.8 | 0.5 |
| **markitdown** | 4.9 | 2.5 | - | - | 5.0 | 2.4 | 4.8 | 4.9 | **24.5** | 0.9 | 0.6 |
| **pdfminer** | 4.4 | 0.0 | - | - | 4.4 | 1.7 | 4.4 | 4.4 | **19.4** | 0.4 | 0.3 |

## mixed  (3 docs: AI_agent_mixed.pdf, mixed.pdf, mixed_digital_scanned.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s | s/page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **azure_di** | 4.3 | 5.0 | - | - | 4.7 | 4.0 | 5.0 | 4.0 | **27.1** | 11.1 | 4.8 |
| **pymupdf4llm** | 4.3 | 4.6 | - | - | 4.7 | 4.0 | 4.9 | 4.0 | **26.5** | 79.4 | 34.0 |
| **hybrid_pdf** | 4.2 | 2.5 | - | - | 4.3 | 3.3 | 4.7 | 4.0 | **23.0** | 14.5 | 6.2 |
| **pymupdf** | 3.1 | 2.5 | - | - | 3.2 | 2.8 | 2.7 | 3.7 | **18.0** | 1.8 | 0.8 |
| **opendataloader** | 3.1 | 2.5 | - | - | 3.2 | 2.7 | 2.7 | 3.7 | **17.9** | 5.4 | 2.3 |
| **pdfplumber** | 3.1 | 2.5 | - | - | 3.2 | 1.5 | 2.7 | 3.7 | **16.7** | 1.6 | 0.7 |
| **markitdown** | 3.1 | 2.5 | - | - | 3.2 | 1.5 | 2.7 | 3.7 | **16.7** | 1.6 | 0.7 |
| **pdfminer** | 3.1 | 0.0 | - | - | 3.2 | 1.5 | 2.7 | 3.7 | **14.1** | 0.6 | 0.3 |

## scanned  (6 docs: AI_agent_scanned_clean.pdf, AI_agent_scanned_noisy.pdf, scanned.pdf, scanned_invoice_clean.pdf, scanned_invoice_low_quality.pdf, scanned_invoice_skewed_noisy.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s | s/page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **azure_di** | 4.2 | 3.3 | - | - | 4.0 | 4.6 | 4.2 | 4.3 | **24.6** | 10.5 | 6.3 |
| **pymupdf4llm** | 4.1 | 2.7 | - | - | 4.0 | 3.7 | 4.1 | 4.1 | **22.7** | 33.4 | 20.1 |
| **hybrid_pdf** | 3.8 | 0.0 | - | - | 2.9 | 2.0 | 3.6 | 4.1 | **16.4** | 24.1 | 14.4 |
| **opendataloader** | 0.0 | 0.0 | - | - | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 12.0 | 7.2 |
| **pymupdf** | 0.0 | 0.0 | - | - | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 2.1 | 1.2 |
| **pdfplumber** | 0.0 | 0.0 | - | - | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 | 0.0 |
| **pdfminer** | 0.0 | 0.0 | - | - | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 | 0.0 |
| **markitdown** | 0.0 | 0.0 | - | - | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.4 | 0.2 |