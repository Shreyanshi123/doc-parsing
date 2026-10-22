# Parser scorecard (0-5 per metric, total /40)

Big documents, no answer key: every parser is scored against azure_di's output, so this measures closeness to azure_di, not absolute correctness. '-' = nothing to test that metric with.

## Overall

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s | s/page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **pymupdf4llm** | 4.9 | 2.4 | - | 0.1 | 4.9 | 4.5 | 4.9 | 4.9 | **26.6** | 184.7 | 2.9 |
| **docling** | 4.7 | 2.4 | - | 0.1 | 4.1 | 4.3 | 4.5 | 4.9 | **24.9** | 15108.1 | 236.1 |
| **hybrid_pdf** | 4.9 | 1.3 | - | 0.1 | 4.8 | 3.4 | 4.8 | 5.0 | **24.4** | 71.3 | 1.1 |
| **pymupdf** | 4.9 | 1.3 | - | 0.1 | 4.8 | 3.4 | 4.8 | 5.0 | **24.4** | 111.7 | 1.7 |
| **smart_pdf** | 4.9 | 1.3 | - | 0.1 | 4.8 | 3.3 | 4.9 | 4.9 | **24.2** | 176.3 | 2.8 |
| **markitdown** | 3.3 | 1.6 | - | 0.0 | 4.6 | 1.8 | 3.1 | 3.9 | **18.4** | 68.1 | 1.1 |
| **pdfplumber** | 3.2 | 0.3 | - | 0.0 | 4.6 | 1.8 | 2.8 | 3.9 | **16.7** | 71.9 | 1.1 |
| **opendataloader** | 2.4 | 0.0 | 0.0 | 0.1 | 2.3 | 1.9 | 2.4 | 2.5 | **11.7** | 31.7 | 0.5 |
| **azure_di** | - | - | - | - | - | - | - | - | reference | 43.0 | 0.7 |

## digital + charts/images  (2 docs: llama2_paper.pdf, un_sdg_report_2024.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s | s/page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **pymupdf4llm** | 4.9 | 2.4 | - | 0.1 | 4.9 | 4.5 | 4.9 | 4.9 | **26.6** | 184.7 | 2.9 |
| **docling** | 4.7 | 2.4 | - | 0.1 | 4.1 | 4.3 | 4.5 | 4.9 | **24.9** | 15108.1 | 236.1 |
| **hybrid_pdf** | 4.9 | 1.3 | - | 0.1 | 4.8 | 3.4 | 4.8 | 5.0 | **24.4** | 71.3 | 1.1 |
| **pymupdf** | 4.9 | 1.3 | - | 0.1 | 4.8 | 3.4 | 4.8 | 5.0 | **24.4** | 111.7 | 1.7 |
| **smart_pdf** | 4.9 | 1.3 | - | 0.1 | 4.8 | 3.3 | 4.9 | 4.9 | **24.2** | 176.3 | 2.8 |
| **markitdown** | 3.3 | 1.6 | - | 0.0 | 4.6 | 1.8 | 3.1 | 3.9 | **18.4** | 68.1 | 1.1 |
| **pdfplumber** | 3.2 | 0.3 | - | 0.0 | 4.6 | 1.8 | 2.8 | 3.9 | **16.7** | 71.9 | 1.1 |
| **opendataloader** | 2.4 | 0.0 | 0.0 | 0.1 | 2.3 | 1.9 | 2.4 | 2.5 | **11.7** | 31.7 | 0.5 |
| **azure_di** | - | - | - | - | - | - | - | - | reference | 43.0 | 0.7 |