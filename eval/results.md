# Parser evaluation (scored against ground truth)

## Recommendation per document type

| document type | best | backup | avg score (best) | docs |
|---|---|---|---|---|
| csv | **spreadsheet** | unstructured | 1.00 | 1 |
| docx | **docx** | unstructured | 1.00 | 1 |
| image/image | **unstructured** | docling | 1.00 | 1 |
| pdf/digital | **hybrid_pdf** | pymupdf | 1.00 | 1 |
| pdf/mixed | **pymupdf4llm** | docling | 1.00 | 1 |
| pdf/scanned | **pymupdf4llm** | unstructured | 1.00 | 1 |
| pptx | **pptx** | docling | 0.96 | 1 |
| xlsx | **docling** | unstructured | 1.00 | 1 |

## Per-document detail

### deck.pptx  (pptx, router would pick: pptx)

| parser | status | ms | text | headings | tables | score |
|---|---|---|---|---|---|---|
| pptx | ok | 19 | 0.929 | 1.0 | - | **0.964** |
| docling | ok | 39623 | 0.818 | 1.0 | - | **0.909** |
| markitdown | ok | 174 | 0.867 | 0.667 | - | **0.767** |
| unstructured | ok | 6053 | 0.818 | 0.667 | - | **0.742** |

### digital.pdf  (pdf/digital, router would pick: pymupdf)

| parser | status | ms | text | headings | tables | score |
|---|---|---|---|---|---|---|
| docling | ok | 37426 | 1.0 | 1.0 | 1.0 | **1.0** |
| pymupdf | ok | 1435 | 1.0 | 1.0 | 1.0 | **1.0** |
| hybrid_pdf | ok | 588 | 1.0 | 1.0 | 1.0 | **1.0** |
| opendataloader | ok | 7336 | 1.0 | 1.0 | 1.0 | **1.0** |
| pymupdf4llm | ok | 3151 | 1.0 | 1.0 | 1.0 | **1.0** |
| markitdown | ok | 237 | 1.0 | 0.0 | 1.0 | **0.667** |
| pdfplumber | ok | 20 | 1.0 | 0.0 | 1.0 | **0.667** |
| unstructured | ok | 12931 | 1.0 | 0.222 | 0.0 | **0.407** |
| easyocr | ok | 35632 | 1.0 | 0.0 | 0.0 | **0.333** |
| pdfminer | ok | 16 | 1.0 | 0.0 | 0.0 | **0.333** |
| ocr | ok | 1502 | 0.976 | 0.0 | 0.0 | **0.325** |

### mixed.pdf  (pdf/mixed, router would pick: hybrid_pdf)

| parser | status | ms | text | headings | tables | score |
|---|---|---|---|---|---|---|
| docling | ok | 23279 | 1.0 | 1.0 | 1.0 | **1.0** |
| pymupdf4llm | ok | 5500 | 1.0 | 1.0 | 1.0 | **1.0** |
| hybrid_pdf | ok | 1710 | 1.0 | 0.667 | 1.0 | **0.889** |
| pymupdf | ok | 775 | 0.764 | 0.667 | 1.0 | **0.81** |
| opendataloader | ok | 1530 | 0.764 | 0.667 | 1.0 | **0.81** |
| markitdown | ok | 93 | 0.764 | 0.0 | 1.0 | **0.588** |
| pdfplumber | ok | 39 | 0.764 | 0.0 | 1.0 | **0.588** |
| easyocr | ok | 61194 | 1.0 | 0.0 | 0.0 | **0.333** |
| ocr | ok | 1878 | 0.985 | 0.0 | 0.0 | **0.328** |
| unstructured | ok | 69 | 0.764 | 0.2 | 0.0 | **0.321** |
| pdfminer | ok | 24 | 0.764 | 0.0 | 0.0 | **0.255** |

### report.docx  (docx, router would pick: docx)

| parser | status | ms | text | headings | tables | score |
|---|---|---|---|---|---|---|
| docling | ok | 647 | 1.0 | 1.0 | 1.0 | **1.0** |
| docx | ok | 21 | 1.0 | 1.0 | 1.0 | **1.0** |
| unstructured | ok | 90 | 1.0 | 1.0 | 1.0 | **1.0** |
| markitdown | ok | 380 | 1.0 | 0.667 | 1.0 | **0.889** |

### sales.csv  (csv, router would pick: spreadsheet)

| parser | status | ms | text | headings | tables | score |
|---|---|---|---|---|---|---|
| markitdown | ok | 96 | 1.0 | - | 1.0 | **1.0** |
| spreadsheet | ok | 1 | 1.0 | - | 1.0 | **1.0** |
| unstructured | ok | 40 | 1.0 | - | 1.0 | **1.0** |

### sales.xlsx  (xlsx, router would pick: spreadsheet)

| parser | status | ms | text | headings | tables | score |
|---|---|---|---|---|---|---|
| docling | ok | 397 | 1.0 | - | 1.0 | **1.0** |
| unstructured | ok | 1738 | 1.0 | - | 1.0 | **1.0** |
| markitdown | ok | 122 | 0.952 | - | 1.0 | **0.976** |
| spreadsheet | ok | 13 | 0.952 | - | 1.0 | **0.976** |

### scan.png  (image/image, router would pick: ocr)

| parser | status | ms | text | headings | tables | score |
|---|---|---|---|---|---|---|
| docling | ok | 22241 | 1.0 | 1.0 | - | **1.0** |
| unstructured | ok | 3725 | 1.0 | 1.0 | - | **1.0** |
| ocr | ok | 861 | 1.0 | 0.0 | - | **0.5** |
| easyocr | ok | 14353 | 1.0 | 0.0 | - | **0.5** |

### scanned.pdf  (pdf/scanned, router would pick: ocr)

| parser | status | ms | text | headings | tables | score |
|---|---|---|---|---|---|---|
| docling | ok | 10530 | 1.0 | 1.0 | - | **1.0** |
| pymupdf4llm | ok | 2706 | 1.0 | 1.0 | - | **1.0** |
| unstructured | ok | 3413 | 1.0 | 1.0 | - | **1.0** |
| ocr | ok | 974 | 1.0 | 0.0 | - | **0.5** |
| easyocr | ok | 29991 | 1.0 | 0.0 | - | **0.5** |
| hybrid_pdf | ok | 1102 | 1.0 | 0.0 | - | **0.5** |
| pymupdf | ok | 212 | 0.0 | 0.0 | - | **0.0** |
| markitdown | ok | 64 | 0.0 | 0.0 | - | **0.0** |
| opendataloader | ok | 1110 | 0.0 | 0.0 | - | **0.0** |
| pdfminer | ok | 1 | 0.0 | 0.0 | - | **0.0** |
| pdfplumber | ok | 2 | 0.0 | 0.0 | - | **0.0** |
