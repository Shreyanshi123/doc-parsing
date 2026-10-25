# Parser scorecard (0-5 per metric, total /40)

Big documents, no answer key: every parser is scored against azure_di's output, so this measures closeness to azure_di, not absolute correctness. '-' = nothing to test that metric with.

## Overall

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s | s/page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **pymupdf4llm** | 4.7 | - | - | 0.8 | 4.4 | 4.3 | 4.6 | 4.7 | **23.5** | 61.4 | 2.5 |
| **hybrid_pdf** | 4.7 | - | - | 0.8 | 4.1 | 3.6 | 4.6 | 4.8 | **22.7** | 38.0 | 1.5 |
| **pymupdf** | 4.7 | - | - | 0.8 | 4.0 | 3.6 | 4.6 | 4.9 | **22.5** | 35.9 | 1.5 |
| **opendataloader** | 4.6 | - | - | 0.8 | 3.9 | 3.9 | 4.4 | 4.8 | **22.4** | 8.1 | 0.3 |
| **smart_pdf** | 4.5 | - | - | 0.8 | 4.0 | 3.4 | 4.7 | 4.3 | **21.7** | 65.4 | 2.7 |
| **markitdown** | 4.6 | - | - | 0.8 | 4.0 | 2.2 | 4.5 | 4.8 | **20.8** | 11.2 | 0.5 |
| **pdfplumber** | 4.6 | - | - | 0.8 | 4.0 | 2.2 | 4.4 | 4.8 | **20.7** | 10.1 | 0.4 |
| **docling** | 4.2 | - | - | 0.8 | 3.2 | 3.9 | 4.5 | 4.0 | **20.6** | 414.1 | 16.8 |
| **ocr** | 4.4 | - | - | 0.8 | 3.9 | 2.2 | 4.2 | 4.6 | **20.0** | 224.8 | 9.1 |
| **azure_di** | - | - | - | - | - | - | - | - | reference | 18.7 | 0.8 |

## digital  (1 docs: AI_agent.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s | s/page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **hybrid_pdf** | 5.0 | - | - | 1.2 | 4.6 | 4.9 | 5.0 | 5.0 | **25.8** | 47.0 | 2.0 |
| **smart_pdf** | 5.0 | - | - | 1.2 | 4.6 | 4.9 | 5.0 | 5.0 | **25.8** | 21.8 | 0.9 |
| **pymupdf** | 5.0 | - | - | 1.2 | 4.6 | 4.9 | 5.0 | 5.0 | **25.8** | 18.9 | 0.8 |
| **pymupdf4llm** | 5.0 | - | - | 1.2 | 4.6 | 4.9 | 5.0 | 5.0 | **25.6** | 27.7 | 1.2 |
| **opendataloader** | 5.0 | - | - | 1.2 | 4.6 | 4.8 | 5.0 | 5.0 | **25.5** | 8.6 | 0.4 |
| **docling** | 4.9 | - | - | 1.2 | 4.6 | 4.9 | 5.0 | 4.7 | **25.4** | 321.9 | 13.4 |
| **pdfplumber** | 5.0 | - | - | 1.2 | 4.6 | 2.5 | 5.0 | 5.0 | **23.3** | 13.7 | 0.6 |
| **markitdown** | 5.0 | - | - | 1.2 | 4.6 | 2.5 | 5.0 | 5.0 | **23.3** | 14.6 | 0.6 |
| **ocr** | 4.9 | - | - | 1.2 | 4.5 | 2.5 | 4.9 | 4.9 | **22.8** | 167.7 | 7.0 |
| **azure_di** | - | - | - | - | - | - | - | - | reference | 18.8 | 0.8 |

## digital + charts/images  (1 docs: Generative_AI.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s | s/page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **pymupdf4llm** | 5.0 | - | - | 0.8 | 4.6 | 4.9 | 5.0 | 5.0 | **25.1** | 66.4 | 1.7 |
| **docling** | 4.9 | - | - | 0.8 | 4.5 | 4.8 | 4.9 | 4.8 | **24.7** | 207.9 | 5.3 |
| **hybrid_pdf** | 5.0 | - | - | 0.8 | 4.6 | 4.2 | 4.9 | 5.0 | **24.5** | 38.1 | 1.0 |
| **pymupdf** | 5.0 | - | - | 0.8 | 4.6 | 4.2 | 4.9 | 5.0 | **24.5** | 44.2 | 1.1 |
| **opendataloader** | 4.9 | - | - | 0.8 | 4.5 | 4.0 | 4.9 | 5.0 | **24.2** | 7.6 | 0.2 |
| **smart_pdf** | 4.9 | - | - | 0.8 | 4.6 | 3.9 | 5.0 | 4.9 | **24.0** | 54.6 | 1.4 |
| **markitdown** | 5.0 | - | - | 0.8 | 4.6 | 2.3 | 4.9 | 5.0 | **22.6** | 13.2 | 0.3 |
| **pdfplumber** | 5.0 | - | - | 0.8 | 4.6 | 2.3 | 4.9 | 5.0 | **22.5** | 10.9 | 0.3 |
| **ocr** | 4.9 | - | - | 0.8 | 4.4 | 2.3 | 4.8 | 4.9 | **22.0** | 455.5 | 11.7 |
| **azure_di** | - | - | - | - | - | - | - | - | reference | 22.6 | 0.6 |

## mixed + charts/images  (1 docs: Home_ Press Information Office.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s | s/page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **pymupdf4llm** | 4.1 | - | - | 0.2 | 4.0 | 3.1 | 3.9 | 4.3 | **19.6** | 90.0 | 8.2 |
| **hybrid_pdf** | 4.2 | - | - | 0.2 | 3.2 | 1.8 | 3.8 | 4.5 | **17.7** | 28.8 | 2.6 |
| **opendataloader** | 3.9 | - | - | 0.2 | 2.6 | 2.8 | 3.4 | 4.5 | **17.4** | 8.2 | 0.7 |
| **pymupdf** | 4.2 | - | - | 0.2 | 2.6 | 1.8 | 3.8 | 4.7 | **17.3** | 44.4 | 4.0 |
| **markitdown** | 3.9 | - | - | 0.2 | 2.6 | 1.7 | 3.5 | 4.5 | **16.5** | 5.7 | 0.5 |
| **pdfplumber** | 3.9 | - | - | 0.2 | 2.6 | 1.7 | 3.4 | 4.5 | **16.3** | 5.6 | 0.5 |
| **smart_pdf** | 3.5 | - | - | 0.2 | 2.9 | 1.5 | 4.0 | 3.1 | **15.3** | 119.8 | 10.9 |
| **ocr** | 3.4 | - | - | 0.2 | 2.8 | 1.8 | 2.9 | 4.0 | **15.2** | 51.3 | 4.7 |
| **docling** | 2.9 | - | - | 0.2 | 0.6 | 2.1 | 3.5 | 2.4 | **11.7** | 712.3 | 64.8 |
| **azure_di** | - | - | - | - | - | - | - | - | reference | 14.7 | 1.3 |