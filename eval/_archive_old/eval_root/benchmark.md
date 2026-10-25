# Parser scorecard (0-5 per metric, total /40)

Run fresh on every PDF in eval/ that has an answer key. '-' = no document tested that metric.

**Note:** Azure DI rows were re-scored after fixing the scorer to ignore HTML tags (ADI returns tables/figures as HTML, which was wrongly counted as extra words). All other rows come from the first full run. Original: eval/benchmark_full_run.md.

## Overall

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s |
|---|---|---|---|---|---|---|---|---|---|---|
| **smart_pdf** | 4.3 | 4.9 | 4.5 | 5.0 | 3.8 | 3.3 | 4.9 | 4.0 | **34.7** | 15.3 |
| **hybrid_pdf** | 4.6 | 4.2 | 0.0 | 2.5 | 4.3 | 3.5 | 4.8 | 4.5 | **28.4** | 3.6 |
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

## digital  (1 docs: AI_agent_p1-3.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s |
|---|---|---|---|---|---|---|---|---|---|---|
| **hybrid_pdf** | 5.0 | - | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **25.0** | 1.4 |
| **smart_pdf** | 5.0 | - | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **25.0** | 1.5 |
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

## digital + charts/images  (5 docs: Generative_AI_p1-6.pdf, Overview of Amazon Web Services - Overview of Amazon Web Services.pdf, PIB_home_p1-6.pdf, SOP  Income Tax Computation Sheet-2026-27.pdf, chart_sample.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s |
|---|---|---|---|---|---|---|---|---|---|---|
| **smart_pdf** | 3.4 | 4.6 | 4.5 | 5.0 | 3.0 | 2.9 | 4.8 | 2.7 | **30.9** | 30.8 |
| **hybrid_pdf** | 4.2 | 2.5 | 0.0 | 2.5 | 4.0 | 3.1 | 4.6 | 4.0 | **25.0** | 2.6 |
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

## digital + tables  (1 docs: digital.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s |
|---|---|---|---|---|---|---|---|---|---|---|
| **docling** | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **30.0** | 10.4 |
| **opendataloader** | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **30.0** | 1.7 |
| **pymupdf4llm** | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **30.0** | 1.1 |
| **hybrid_pdf** | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **30.0** | 0.5 |
| **smart_pdf** | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **30.0** | 0.5 |
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

## mixed  (2 docs: AI_agent_mixed.pdf, mixed.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s |
|---|---|---|---|---|---|---|---|---|---|---|
| **docling** | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **29.9** | 40.3 |
| **azure_di** | 5.0 | 5.0 | - | - | 5.0 | 4.9 | 5.0 | 5.0 | **29.8** | 11.9 |
| **pymupdf4llm** | 4.9 | 5.0 | - | - | 4.9 | 5.0 | 4.9 | 4.8 | **29.5** | 6.8 |
| **hybrid_pdf** | 5.0 | 5.0 | - | - | 4.8 | 4.2 | 5.0 | 5.0 | **28.9** | 2.7 |
| **smart_pdf** | 5.0 | 5.0 | - | - | 4.8 | 4.2 | 5.0 | 5.0 | **28.9** | 2.6 |
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

## scanned  (3 docs: AI_agent_scanned_clean.pdf, AI_agent_scanned_noisy.pdf, scanned.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s |
|---|---|---|---|---|---|---|---|---|---|---|
| **azure_di** | 5.0 | - | - | - | 4.9 | 5.0 | 5.0 | 5.0 | **24.9** | 9.8 |
| **docling** | 4.9 | - | - | - | 5.0 | 4.9 | 4.9 | 4.9 | **24.6** | 33.9 |
| **pymupdf4llm** | 4.9 | - | - | - | 4.9 | 4.7 | 4.8 | 4.9 | **24.2** | 18.2 |
| **easyocr** | 4.8 | - | - | - | 4.1 | 2.3 | 4.8 | 4.8 | **20.9** | 101.7 |
| **hybrid_pdf** | 4.9 | - | - | - | 3.6 | 2.5 | 4.9 | 4.9 | **20.6** | 7.9 |
| **smart_pdf** | 4.9 | - | - | - | 3.6 | 2.5 | 4.9 | 4.9 | **20.6** | 7.8 |
| **ocr** | 4.9 | - | - | - | 3.6 | 2.5 | 4.9 | 4.9 | **20.6** | 6.0 |
| **opendataloader** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 3.3 |
| **markitdown** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.1 |
| **pdfplumber** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
| **pdfminer** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
| **pymupdf** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.4 |
| **langchain_loader** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
| **llamaindex_reader** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
| **haystack_converter** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
