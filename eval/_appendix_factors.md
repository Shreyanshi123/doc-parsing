## Appendix E. The review factors, parser by parser

Same factors as the Azure IDP vs OpenDataLoader review: Text, Table, Chart, Infographic, Numeric, Structure, Completeness and the Hallucination penalty. Differences to the e-mail review: the e-mail scores by hand from 1 to 5; here the code scores from 0 to 5 against a written answer file. The hallucination penalty is shown as a negative number as in the e-mail (0 = nothing invented, -1 = everything extra): penalty = -(1 - precision/5). Total = the seven metrics added up + the penalty (the e-mail's 27 for Azure = 4+4+4+3+5+4+4-1). A metric that an answer file cannot test (no chart in the document, for example) is left out, so the total is also shown scaled to 8 metrics (sum x 8 / number of metrics tested).

### E1a. Every parser on the 12 tough PDFs

Merged-cell tables, nested table, forms, a scan, charts and photos, a 20-page report (Azure DI alone was not run on these; ADI + vision was). Averages over the runs that gave an output; failed, empty and timed-out runs are counted in *Failed*, not in the averages.

| Parser | Docs | Failed | Text | Table | Chart | Infographic | Numeric | Structure | Complete | Hallucination penalty | Total (sum) | Metrics tested | Total scaled to 8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ADI + vision (paid) | 12 | 0 | 4.7 | 4.4 | 5.0 | - | 4.7 | 4.0 | 4.9 | -0.08 | 27.6 | 7 | **31.6** |
| smart_pdf | 12 | 0 | 4.1 | 3.0 | 5.0 | - | 4.1 | 3.6 | 4.8 | -0.22 | 24.4 | 7 | **27.9** |
| PyMuPDF4LLM | 12 | 0 | 4.9 | 3.7 | 1.1 | - | 4.8 | 4.7 | 4.9 | -0.03 | 23.9 | 7 | **27.4** |
| OpenDataLoader | 12 | 1 | 4.8 | 4.3 | 0.0 | - | 4.7 | 4.2 | 4.7 | -0.01 | 22.6 | 7 | **25.9** |
| Docling | 12 | 0 | 4.6 | 4.2 | 0.0 | - | 4.5 | 4.5 | 4.6 | -0.06 | 22.4 | 7 | **25.6** |
| PyMuPDF | 12 | 1 | 4.5 | 3.4 | 0.0 | - | 4.4 | 4.0 | 4.8 | -0.13 | 21.0 | 7 | **24.0** |
| pdfplumber | 12 | 1 | 4.9 | 3.9 | 0.0 | - | 4.8 | 2.2 | 4.8 | -0.03 | 20.6 | 7 | **23.5** |
| hybrid_pdf | 12 | 0 | 4.4 | 3.1 | 0.0 | - | 4.3 | 3.8 | 4.6 | -0.12 | 20.1 | 7 | **22.9** |
| MarkItDown | 12 | 1 | 4.9 | 1.4 | 0.0 | - | 4.8 | 2.2 | 4.8 | -0.01 | 18.1 | 7 | **20.7** |
| Unstructured | 12 | 0 | 4.8 | 0.0 | 0.0 | - | 4.7 | 2.1 | 4.7 | -0.02 | 16.3 | 7 | **18.6** |
| Tesseract OCR | 12 | 0 | 4.2 | 0.0 | 1.1 | - | 3.8 | 2.0 | 3.8 | -0.03 | 14.9 | 7 | **17.0** |

### E1b. Every parser on the 6 research reports

Colleague's reports (9 to 66 pages). The answer files cover key pages only, so absolute values are low for every parser (the hallucination penalty is near -0.9 for all of them because most of each report is not in the answer file); compare parsers with each other. Failed, empty and timed-out runs are counted in *Failed*.

| Parser | Docs | Failed | Text | Table | Chart | Infographic | Numeric | Structure | Complete | Hallucination penalty | Total (sum) | Metrics tested | Total scaled to 8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Azure DI (paid) | 6 | 0 | 0.8 | 1.7 | - | - | 1.1 | 0.8 | 5.0 | -0.91 | 8.5 | 6 | **11.3** |
| ADI + vision (paid) | 6 | 0 | 0.8 | 1.7 | - | - | 1.1 | 0.9 | 5.0 | -0.92 | 8.5 | 6 | **11.3** |
| Docling | 6 | 2 | 0.9 | 1.4 | - | - | 1.3 | 1.0 | 4.6 | -0.89 | 8.4 | 6 | **11.2** |
| PyMuPDF4LLM | 6 | 0 | 0.7 | 1.5 | - | - | 1.1 | 0.8 | 4.9 | -0.92 | 8.1 | 6 | **10.8** |
| OpenDataLoader | 6 | 0 | 0.8 | 1.2 | - | - | 1.4 | 0.8 | 4.7 | -0.91 | 8.0 | 6 | **10.7** |
| pdfplumber | 6 | 0 | 0.7 | 1.2 | - | - | 1.2 | 0.7 | 4.8 | -0.92 | 7.8 | 6 | **10.4** |
| MarkItDown | 6 | 0 | 0.8 | 1.0 | - | - | 1.3 | 0.8 | 4.4 | -0.91 | 7.4 | 6 | **9.8** |
| smart_pdf | 6 | 0 | 0.6 | 1.1 | - | - | 1.0 | 0.7 | 4.7 | -0.92 | 7.1 | 6 | **9.5** |
| PyMuPDF | 6 | 0 | 0.6 | 0.8 | - | - | 1.1 | 0.7 | 4.8 | -0.92 | 7.0 | 6 | **9.4** |
| hybrid_pdf | 6 | 0 | 0.6 | 0.8 | - | - | 1.1 | 0.7 | 4.8 | -0.92 | 7.0 | 6 | **9.4** |
| EasyOCR | 6 | 3 | 1.1 | 0.0 | - | - | 1.6 | 0.8 | 4.3 | -0.87 | 6.9 | 6 | **9.2** |
| Unstructured | 6 | 1 | 0.9 | 0.0 | - | - | 1.5 | 0.7 | 4.4 | -0.89 | 6.6 | 6 | **8.8** |
| pdfminer | 6 | 0 | 0.8 | 0.0 | - | - | 1.6 | 0.7 | 4.2 | -0.90 | 6.5 | 6 | **8.6** |
| LangChain / LlamaIndex / Haystack loaders | 18 | 0 | 0.8 | 0.0 | - | - | 1.3 | 0.8 | 4.5 | -0.91 | 6.5 | 6 | **8.6** |
| Tesseract OCR | 6 | 0 | 0.8 | 0.0 | - | - | 1.2 | 0.8 | 4.6 | -0.91 | 6.4 | 6 | **8.6** |

Parsers that were not run on a set do not appear in its table (pdfminer, EasyOCR and the loaders only ran on the first 62 documents and the research reports).

### E2. Research reports: Azure DI vs OpenDataLoader (e-mail layout)

The six research reports from a colleague (answer files cover key pages only, so absolute values are low). Scale 0 to 5 per metric.

| Metric | Azure DI (paid) | OpenDataLoader | ADI + vision (paid) | PyMuPDF4LLM | Docling |
|---|---|---|---|---|---|
| Text Accuracy | 0.78 | 0.80 | 0.78 | 0.72 | 0.95 |
| Table Reconstruction | 1.72 | 1.25 | 1.67 | 1.47 | 1.45 |
| Chart Understanding | - | - | - | - | - |
| Infographic Parsing | - | - | - | - | - |
| Entity & Numeric Fidelity | 1.12 | 1.37 | 1.10 | 1.13 | 1.30 |
| Structure | 0.83 | 0.78 | 0.87 | 0.77 | 0.97 |
| Completeness | 4.95 | 4.72 | 4.95 | 4.93 | 4.62 |
| Hallucination penalty | -0.91 | -0.91 | -0.92 | -0.92 | -0.89 |
| **Total (sum)** | **8.5** | **8.0** | **8.5** | **8.1** | **8.4** |
| Metrics tested | 6 | 6 | 6 | 6 | 6 |

In the e-mail review the strengths were: Azure IDP better on tables and structure, OpenDataLoader more complete on narrative text and footnotes. On these six native reports the two are close; the table above shows where they differ.

### E3. Key issues per document (where parsers differed a lot)

Found by automatic checks on the saved outputs, not by reading every output by hand:

- **Structure:** tables found in the output vs tables in the answer file; rows where the same cell text is repeated 3 or more times in a row (a merged cell copied across columns).
- **Artifacts:** share of repeated lines (duplicated content), placeholder columns such as Col2, empty output.
- **Numbers:** numbers of the answer file that are missing in the output, with up to 3 examples.
- **Charts:** chart values of the answer file found in the output.
- **Strong at:** metrics scored 4.5 or more.

### annual_report_spread.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| smart_pdf (best) | 4.53 | 3 tables found, 4 expected; 1 rows with a cell repeated across columns | none found | 1 of 32 numbers missing (2.) | 7 of 7 chart values found | Text, Chart, Numeric, Complete |
| ADI + vision (paid) | 4.45 | 3 tables found, 4 expected | none found | 2 of 32 numbers missing (1., 2.) | 7 of 7 chart values found | Chart, Numeric, Complete |
| OpenDataLoader | 3.50 | 2 tables found, 4 expected; 1 rows with a cell repeated across columns | none found | 10 of 32 numbers missing (2., 120, 150) | 0 of 7 chart values found | - |
| PyMuPDF4LLM | 4.05 | 1 tables found, 4 expected; 1 rows with a cell repeated across columns | none found | 3 of 32 numbers missing (2., 3, 310) | 5 of 7 chart values found | Text, Complete |
| Docling | 3.42 | 2 tables found, 4 expected; 1 rows with a cell repeated across columns | none found | 12 of 32 numbers missing (1, 2, 2.) | 0 of 7 chart values found | - |
| PyMuPDF | 3.69 | 1 tables found, 4 expected; 1 rows with a cell repeated across columns | none found | 10 of 32 numbers missing (2., 120, 150) | 0 of 7 chart values found | Text |
| Unstructured | 2.81 | 0 tables found, 4 expected | 20% of lines repeated | 10 of 32 numbers missing (2., 120, 150) | 0 of 7 chart values found | - |

### bom_wide_table.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| Docling (best) | 5.00 | 1 tables found, 1 expected | none found | 0 of 92 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| smart_pdf | 4.93 | 1 tables found, 1 expected; 6 rows with a cell repeated across columns | none found | 0 of 92 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| ADI + vision (paid) | 4.58 | 1 tables found, 1 expected | none found | 0 of 92 numbers missing | no chart in answer file | Text, Table, Numeric, Complete |
| OpenDataLoader | 4.99 | 1 tables found, 1 expected; 3 rows with a cell repeated across columns | none found | 0 of 92 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| PyMuPDF4LLM | 4.77 | 1 tables found, 1 expected; 2 rows with a cell repeated across columns | none found | 0 of 92 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| PyMuPDF | 4.93 | 1 tables found, 1 expected; 6 rows with a cell repeated across columns | none found | 0 of 92 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| Tesseract OCR | 2.90 | 0 tables found, 1 expected | none found | 31 of 92 numbers missing (01, 02, 23) | no chart in answer file | - |

### clinical_trial_table.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| PyMuPDF4LLM (best) | 5.00 | 1 tables found, 1 expected; 1 rows with a cell repeated across columns | none found | 0 of 59 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| smart_pdf | 3.01 | 5 tables found, 1 expected; 8 rows with a cell repeated across columns; table split into fragments | 29% of lines repeated; 2 placeholder columns (Col2...) | 0 of 59 numbers missing | no chart in answer file | Complete |
| ADI + vision (paid) | 4.42 | 1 tables found, 1 expected | none found | 0 of 59 numbers missing | no chart in answer file | Text, Numeric, Complete |
| OpenDataLoader | 4.43 | 1 tables found, 1 expected; 1 rows with a cell repeated across columns | none found | 0 of 59 numbers missing | no chart in answer file | Text, Table, Numeric, Complete |
| Docling | 4.82 | 1 tables found, 1 expected | none found | 1 of 59 numbers missing (27) | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| PyMuPDF | 4.08 | 4 tables found, 1 expected; 8 rows with a cell repeated across columns; table split into fragments | 2 placeholder columns (Col2...) | 0 of 59 numbers missing | no chart in answer file | Text, Numeric, Complete |

### financial_statement_multiheader.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| ADI + vision (paid) (best) | 4.96 | 1 tables found, 1 expected | none found | 0 of 75 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| smart_pdf | 2.96 | 6 tables found, 1 expected; 15 rows with a cell repeated across columns; table split into fragments | 6 placeholder columns (Col2...) | 0 of 75 numbers missing | no chart in answer file | Complete |
| OpenDataLoader | 4.51 | 1 tables found, 1 expected; 1 rows with a cell repeated across columns | none found | 0 of 75 numbers missing | no chart in answer file | Text, Table, Numeric, Complete |
| PyMuPDF4LLM | 4.86 | 1 tables found, 1 expected; 1 rows with a cell repeated across columns | none found | 1 of 75 numbers missing (2025) | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| Docling | 4.75 | 1 tables found, 1 expected | none found | 3 of 75 numbers missing (1, 2, 2.) | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| PyMuPDF | 3.94 | 5 tables found, 1 expected; 15 rows with a cell repeated across columns; table split into fragments | 6 placeholder columns (Col2...) | 0 of 75 numbers missing | no chart in answer file | Numeric, Complete |

### invoice_complex.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| OpenDataLoader (best) | 4.85 | 2 tables found, 2 expected; 4 rows with a cell repeated across columns | none found | 0 of 47 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| smart_pdf | 4.47 | 2 tables found, 2 expected; 4 rows with a cell repeated across columns | none found | 0 of 47 numbers missing | no chart in answer file | Text, Numeric, Complete |
| ADI + vision (paid) | 4.68 | 2 tables found, 2 expected | none found | 0 of 47 numbers missing | no chart in answer file | Text, Table, Numeric, Complete |
| PyMuPDF4LLM | 4.67 | 2 tables found, 2 expected; 3 rows with a cell repeated across columns | none found | 0 of 47 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| Docling | 4.71 | 2 tables found, 2 expected | none found | 0 of 47 numbers missing | no chart in answer file | Text, Numeric, Complete |
| PyMuPDF | 4.61 | 2 tables found, 2 expected; 4 rows with a cell repeated across columns | none found | 0 of 47 numbers missing | no chart in answer file | Text, Numeric, Complete |
| Tesseract OCR | 2.62 | 0 tables found, 2 expected | none found | 17 of 47 numbers missing (220, 3, 4) | no chart in answer file | - |

### ledger_repeated_header.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| Docling (best) | 5.00 | 3 tables found, 1 expected | none found | 0 of 369 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| smart_pdf | 4.86 | 3 tables found, 1 expected; 6 rows with a cell repeated across columns | none found | 0 of 369 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| ADI + vision (paid) | 4.58 | 3 tables found, 1 expected | none found | 0 of 369 numbers missing | no chart in answer file | Text, Table, Numeric, Complete |
| OpenDataLoader | 4.95 | 3 tables found, 1 expected; 6 rows with a cell repeated across columns | none found | 0 of 369 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| PyMuPDF4LLM | 4.86 | 3 tables found, 1 expected; 6 rows with a cell repeated across columns | none found | 0 of 369 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| PyMuPDF | 4.86 | 3 tables found, 1 expected; 6 rows with a cell repeated across columns | none found | 0 of 369 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| Tesseract OCR | 3.01 | 0 tables found, 1 expected | none found | 145 of 369 numbers missing (2602, 9275, 79146) | no chart in answer file | - |

### mixed_table_chart_photo.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| ADI + vision (paid) (best) | 4.00 | 3 tables found, 2 expected | 20% of lines repeated | 1 of 18 numbers missing (1.) | 4 of 4 chart values found | Chart, Complete |
| smart_pdf | 3.90 | 3 tables found, 2 expected; 1 rows with a cell repeated across columns | 14% of lines repeated; 1 placeholder columns (Col2...) | 0 of 18 numbers missing | 4 of 4 chart values found | Chart, Complete |
| OpenDataLoader | 3.51 | 1 tables found, 2 expected; 1 rows with a cell repeated across columns | none found | 8 of 18 numbers missing (1, 120, 2) | 0 of 4 chart values found | Text |
| PyMuPDF4LLM | 3.55 | 1 tables found, 2 expected; 1 rows with a cell repeated across columns | none found | 0 of 18 numbers missing | 3 of 4 chart values found | Text, Complete |
| Docling | 3.44 | 1 tables found, 2 expected | none found | 8 of 18 numbers missing (1, 120, 2) | 0 of 4 chart values found | - |
| PyMuPDF | 3.35 | 1 tables found, 2 expected; 1 rows with a cell repeated across columns | 1 placeholder columns (Col2...) | 7 of 18 numbers missing (1, 120, 2) | 0 of 4 chart values found | - |
| Tesseract OCR | 2.09 | 0 tables found, 2 expected | none found | 14 of 18 numbers missing (6420, 5180, 1.2) | 0 of 4 chart values found | - |

### policy_schedule_nested.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| OpenDataLoader (best) | 4.77 | 1 tables found, 1 expected; 1 rows with a cell repeated across columns | none found | 0 of 12 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| smart_pdf | 2.92 | 1 tables found, 1 expected; 6 rows with a cell repeated across columns | 5 placeholder columns (Col2...) | 0 of 12 numbers missing | no chart in answer file | Complete |
| ADI + vision (paid) | 3.89 | 3 tables found, 1 expected | none found | 0 of 12 numbers missing | no chart in answer file | Structure, Complete |
| PyMuPDF4LLM | 4.77 | 1 tables found, 1 expected; 1 rows with a cell repeated across columns | none found | 0 of 12 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| Docling | 3.62 | 1 tables found, 1 expected; 5 rows with a cell repeated across columns | none found | 0 of 12 numbers missing | no chart in answer file | Complete |
| PyMuPDF | 2.92 | 1 tables found, 1 expected; 6 rows with a cell repeated across columns | 5 placeholder columns (Col2...) | 0 of 12 numbers missing | no chart in answer file | Complete |

### scanned_financial_statement.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| ADI + vision (paid) (best) | 4.96 | 1 tables found, 1 expected | none found | 0 of 75 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| smart_pdf | 2.36 | 0 tables found, 1 expected | none found | 51 of 75 numbers missing (18, 19, 1240.55) | no chart in answer file | - |
| OpenDataLoader | 0.00 | no output (empty) | - | - | - | - |
| PyMuPDF4LLM | 4.49 | 1 tables found, 1 expected; 2 rows with a cell repeated across columns | none found | 1 of 75 numbers missing (2025) | no chart in answer file | Text, Numeric, Complete |
| Docling | 4.41 | 1 tables found, 1 expected; 3 rows with a cell repeated across columns | none found | 3 of 75 numbers missing (1, 2, 2.) | no chart in answer file | Numeric, Complete |
| PyMuPDF | 0.00 | no output (empty) | - | - | - | - |

### annual_report_income_statement.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| OpenDataLoader (best) | 4.77 | 1 tables found, 1 expected; 2 rows with a cell repeated across columns | none found | 0 of 48 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| smart_pdf | 4.33 | 1 tables found, 1 expected; 7 rows with a cell repeated across columns | 6 placeholder columns (Col2...) | 0 of 48 numbers missing | no chart in answer file | Numeric, Structure, Complete |
| PyMuPDF4LLM | 4.71 | 1 tables found, 1 expected; 1 rows with a cell repeated across columns | none found | 0 of 48 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| Docling | 4.60 | 1 tables found, 1 expected; 1 rows with a cell repeated across columns | none found | 0 of 48 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| PyMuPDF | 4.33 | 1 tables found, 1 expected; 7 rows with a cell repeated across columns | 6 placeholder columns (Col2...) | 0 of 48 numbers missing | no chart in answer file | Numeric, Structure, Complete |
| Tesseract OCR | 2.32 | 0 tables found, 1 expected | none found | 37 of 48 numbers missing (2024, 2023, 44870) | no chart in answer file | - |

### bank_statement.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| PyMuPDF4LLM (best) | 4.77 | 3 tables found, 3 expected; 3 rows with a cell repeated across columns | none found | 0 of 180 numbers missing | no chart in answer file | Text, Table, Numeric, Complete |
| smart_pdf | 4.68 | 3 tables found, 3 expected; 3 rows with a cell repeated across columns | none found | 4 of 180 numbers missing (22175.00, 231850.75, 10050.00) | no chart in answer file | Text, Table, Numeric, Complete |
| OpenDataLoader | 4.76 | 3 tables found, 3 expected; 3 rows with a cell repeated across columns | none found | 3 of 180 numbers missing (1, 3, 2) | no chart in answer file | Text, Table, Numeric, Complete |
| Docling | 4.71 | 3 tables found, 3 expected | none found | 3 of 180 numbers missing (1, 3, 2) | no chart in answer file | Text, Table, Numeric, Complete |
| PyMuPDF | 4.68 | 3 tables found, 3 expected; 3 rows with a cell repeated across columns | none found | 4 of 180 numbers missing (22175.00, 231850.75, 10050.00) | no chart in answer file | Text, Table, Numeric, Complete |
| Tesseract OCR | 2.99 | 0 tables found, 3 expected | none found | 73 of 180 numbers missing (262581, 34800.00, 83600.75) | no chart in answer file | - |

### bill_of_lading.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| OpenDataLoader (best) | 4.56 | 1 tables found, 1 expected; 1 rows with a cell repeated across columns | none found | 0 of 12 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| smart_pdf | 3.85 | 1 tables found, 1 expected; 3 rows with a cell repeated across columns | 2 placeholder columns (Col2...) | 0 of 12 numbers missing | no chart in answer file | Structure, Complete |
| PyMuPDF4LLM | 4.38 | 1 tables found, 1 expected; 1 rows with a cell repeated across columns | none found | 0 of 12 numbers missing | no chart in answer file | Text, Numeric, Structure |
| Docling | 4.45 | 1 tables found, 1 expected | none found | 0 of 12 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| PyMuPDF | 3.85 | 1 tables found, 1 expected; 3 rows with a cell repeated across columns | 2 placeholder columns (Col2...) | 0 of 12 numbers missing | no chart in answer file | Structure, Complete |
| Tesseract OCR | 3.30 | 0 tables found, 1 expected | none found | 2 of 12 numbers missing (8830415, 7115) | no chart in answer file | Text |

### lab_report.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| Docling (best) | 4.93 | 2 tables found, 1 expected | none found | 0 of 31 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| smart_pdf | 4.85 | 2 tables found, 1 expected; 2 rows with a cell repeated across columns | none found | 0 of 31 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| OpenDataLoader | 4.55 | 2 tables found, 1 expected; 2 rows with a cell repeated across columns | none found | 0 of 31 numbers missing | no chart in answer file | Text, Numeric, Complete |
| PyMuPDF4LLM | 4.88 | 1 tables found, 1 expected; 2 rows with a cell repeated across columns | none found | 0 of 31 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| PyMuPDF | 4.85 | 2 tables found, 1 expected; 2 rows with a cell repeated across columns | none found | 0 of 31 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| Tesseract OCR | 3.02 | 0 tables found, 1 expected | none found | 9 of 31 numbers missing (41, 88213094, 10) | no chart in answer file | - |

### payslip.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| Docling (best) | 4.69 | 3 tables found, 2 expected | none found | 0 of 15 numbers missing | no chart in answer file | Text, Numeric, Complete |
| smart_pdf | 4.05 | 1 tables found, 2 expected; 1 rows with a cell repeated across columns | none found | 0 of 15 numbers missing | no chart in answer file | Text, Numeric, Complete |
| OpenDataLoader | 3.94 | 1 tables found, 2 expected; 1 rows with a cell repeated across columns | none found | 0 of 15 numbers missing | no chart in answer file | Text, Numeric, Complete |
| PyMuPDF4LLM | 4.62 | 2 tables found, 2 expected; 2 rows with a cell repeated across columns | none found | 0 of 15 numbers missing | no chart in answer file | Text, Numeric, Complete |
| PyMuPDF | 4.05 | 1 tables found, 2 expected; 1 rows with a cell repeated across columns | none found | 0 of 15 numbers missing | no chart in answer file | Text, Numeric, Complete |
| Tesseract OCR | 3.53 | 0 tables found, 2 expected | none found | 1 of 15 numbers missing (20418) | no chart in answer file | Text, Numeric, Complete |

### purchase_order.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| OpenDataLoader (best) | 4.96 | 1 tables found, 1 expected; 2 rows with a cell repeated across columns | none found | 0 of 39 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| smart_pdf | 4.79 | 1 tables found, 1 expected; 2 rows with a cell repeated across columns | none found | 0 of 39 numbers missing | no chart in answer file | Text, Table, Numeric, Complete |
| PyMuPDF4LLM | 4.79 | 1 tables found, 1 expected; 1 rows with a cell repeated across columns | none found | 0 of 39 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| Docling | 4.79 | 1 tables found, 1 expected | none found | 0 of 39 numbers missing | no chart in answer file | Text, Table, Numeric, Complete |
| PyMuPDF | 4.79 | 1 tables found, 1 expected; 2 rows with a cell repeated across columns | none found | 0 of 39 numbers missing | no chart in answer file | Text, Table, Numeric, Complete |
| Tesseract OCR | 3.06 | 0 tables found, 1 expected | none found | 14 of 39 numbers missing (500, 3.20, 1600.00) | no chart in answer file | - |

### research_two_column.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| smart_pdf (best) | 4.43 | 3 tables found, 2 expected; 2 rows with a cell repeated across columns | 1 placeholder columns (Col2...) | 0 of 22 numbers missing | 4 of 4 chart values found | Text, Chart, Numeric, Complete |
| OpenDataLoader | 3.72 | 1 tables found, 2 expected; 1 rows with a cell repeated across columns | none found | 7 of 22 numbers missing (120, 2, 150) | 0 of 4 chart values found | Text, Complete |
| PyMuPDF4LLM | 3.74 | 1 tables found, 2 expected; 1 rows with a cell repeated across columns | none found | 1 of 22 numbers missing (310) | 2 of 4 chart values found | Text, Structure, Complete |
| Docling | 3.79 | 1 tables found, 2 expected | none found | 7 of 22 numbers missing (120, 2, 150) | 0 of 4 chart values found | Text, Complete |
| PyMuPDF | 3.50 | 2 tables found, 2 expected; 2 rows with a cell repeated across columns | 1 placeholder columns (Col2...) | 6 of 22 numbers missing (120, 150, 3) | 0 of 4 chart values found | Text, Complete |
| Unstructured | 2.14 | 0 tables found, 2 expected | none found | 16 of 22 numbers missing (82, 1420, 960) | 0 of 4 chart values found | - |

### scanned_purchase_order_phone.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| Docling (best) | 4.67 | 1 tables found, 1 expected | none found | 0 of 39 numbers missing | no chart in answer file | Text, Numeric, Structure, Complete |
| smart_pdf | 2.30 | 0 tables found, 1 expected | none found | 24 of 39 numbers missing (4500187723, 22, 400001) | no chart in answer file | - |
| OpenDataLoader | 0.00 | no output (empty) | - | - | - | - |
| PyMuPDF4LLM | 3.58 | 1 tables found, 1 expected; 1 rows with a cell repeated across columns | none found | 8 of 39 numbers missing (3.20, 1600.00, 41.50) | no chart in answer file | Text, Complete |
| PyMuPDF | 0.00 | no output (empty) | - | - | - | - |

### utility_bill.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| smart_pdf (best) | 4.49 | 2 tables found, 2 expected | none found | 0 of 21 numbers missing | 6 of 6 chart values found | Text, Table, Chart, Numeric, Complete |
| OpenDataLoader | 3.49 | 1 tables found, 2 expected | none found | 5 of 21 numbers missing (410, 385, 430) | 1 of 6 chart values found | Text |
| PyMuPDF4LLM | 3.58 | 1 tables found, 2 expected; 1 rows with a cell repeated across columns | none found | 0 of 21 numbers missing | 6 of 6 chart values found | Text, Complete |
| Docling | 3.45 | 1 tables found, 2 expected | none found | 5 of 21 numbers missing (410, 385, 430) | 1 of 6 chart values found | Text |
| PyMuPDF | 3.44 | 1 tables found, 2 expected | none found | 5 of 21 numbers missing (410, 385, 430) | 1 of 6 chart values found | - |
| Tesseract OCR | 2.70 | 0 tables found, 2 expected | none found | 5 of 21 numbers missing (410, 385, 430) | 1 of 6 chart values found | Text |

### annual_report_60p.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| PyMuPDF4LLM (best) | 4.18 | 55 tables found, 64 expected; 55 rows with a cell repeated across columns | 20% of lines repeated | 1 of 620 numbers missing (92) | 27 of 36 chart values found | Text, Table, Numeric, Structure, Complete |
| smart_pdf | 4.18 | 63 tables found, 64 expected; 546 rows with a cell repeated across columns | 20% of lines repeated; 213 placeholder columns (Col2...) | 4 of 620 numbers missing (79, 317, 60) | 34 of 36 chart values found | Complete |
| OpenDataLoader | 3.91 | 55 tables found, 64 expected; 55 rows with a cell repeated across columns | 10% of lines repeated | 50 of 620 numbers missing (6, 11, 12) | 0 of 36 chart values found | Text, Complete |
| Docling | 0.00 | no output (timeout) | - | - | - | - |
| PyMuPDF | 3.46 | 55 tables found, 64 expected; 602 rows with a cell repeated across columns | 25% of lines repeated; 514 placeholder columns (Col2...) | 32 of 620 numbers missing (121, 338, 261) | 0 of 36 chart values found | Complete |
| Tesseract OCR | 3.12 | 0 tables found, 64 expected | none found | 68 of 620 numbers missing (4963, 36.9, 7333) | 25 of 36 chart values found | Text, Numeric, Complete |

### scanned_report_30p.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| Docling (best) | 4.58 | 30 tables found, 30 expected; 26 rows with a cell repeated across columns | none found | 0 of 255 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| smart_pdf | 2.66 | 0 tables found, 30 expected | none found | 221 of 255 numbers missing (1.1, 40.9, 1.2) | no chart in answer file | - |
| OpenDataLoader | 0.00 | no output (empty) | - | - | - | - |
| PyMuPDF4LLM | 3.67 | 27 tables found, 30 expected; 28 rows with a cell repeated across columns | none found | 45 of 255 numbers missing (2.1, 2.2, 2.3) | no chart in answer file | - |
| PyMuPDF | 0.00 | no output (empty) | - | - | - | - |

### transaction_ledger_100p.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| OpenDataLoader (best) | 5.00 | 100 tables found, 100 expected; 200 rows with a cell repeated across columns | none found | 0 of 7439 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| smart_pdf | 0.00 | no output (timeout) | - | - | - | - |
| PyMuPDF4LLM | 4.99 | 100 tables found, 100 expected; 200 rows with a cell repeated across columns | none found | 0 of 7439 numbers missing | no chart in answer file | Text, Table, Numeric, Structure, Complete |
| Docling | 0.00 | no output (timeout) | - | - | - | - |
| PyMuPDF | 3.01 | 100 tables found, 100 expected; 9137 rows with a cell repeated across columns | 1200 placeholder columns (Col2...) | 0 of 7439 numbers missing | no chart in answer file | Complete |
| Tesseract OCR | 2.10 | 2 tables found, 100 expected | none found | 4297 of 7439 numbers missing (2601, 4901, 248400.00) | no chart in answer file | - |

### operations_report_36p.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| Docling (best) | 4.66 | 30 tables found, 44 expected; 9 rows with a cell repeated across columns | 10% of lines repeated | 1 of 247 numbers missing (45) | 20 of 20 chart values found | Text, Chart, Numeric, Complete |
| smart_pdf | 0.00 | no output (timeout) | - | - | - | - |
| OpenDataLoader | 4.24 | 19 tables found, 44 expected; 14 rows with a cell repeated across columns | none found | 48 of 247 numbers missing (1.1, 83.2, 1.2) | 20 of 20 chart values found | Text, Chart |
| PyMuPDF4LLM | 4.64 | 30 tables found, 44 expected; 29 rows with a cell repeated across columns | 10% of lines repeated | 14 of 247 numbers missing (2.1, 2.2, 2.3) | 20 of 20 chart values found | Text, Chart, Numeric, Complete |
| PyMuPDF | 4.11 | 28 tables found, 44 expected; 81 rows with a cell repeated across columns | 19% of lines repeated; 101 placeholder columns (Col2...) | 47 of 247 numbers missing (1.1, 83.2, 1.2) | 20 of 20 chart values found | Chart |
| Tesseract OCR | 2.82 | 0 tables found, 44 expected | none found | 87 of 247 numbers missing (2025, 62, 37) | 14 of 20 chart values found | Text, Complete |

### tender_pack_30p.pdf

| Parser | Score | Structure | Artifacts | Numbers | Charts | Strong at |
|---|---|---|---|---|---|---|
| Docling (best) | 4.07 | 18 tables found, 18 expected | none found | 22 of 179 numbers missing (270, 202, 287) | 0 of 24 chart values found | Text, Numeric, Structure, Complete |
| smart_pdf | 3.65 | 21 tables found, 18 expected; 51 rows with a cell repeated across columns | 11% of lines repeated; 46 placeholder columns (Col2...) | 11 of 179 numbers missing (043, 270, 202) | 13 of 24 chart values found | Complete |
| OpenDataLoader | 3.72 | 18 tables found, 18 expected; 12 rows with a cell repeated across columns | none found | 39 of 179 numbers missing (028, 029, 030) | 0 of 24 chart values found | Text, Structure, Complete |
| PyMuPDF4LLM | 3.90 | 18 tables found, 18 expected; 12 rows with a cell repeated across columns | 13% of lines repeated | 5 of 179 numbers missing (110, 63, 101) | 13 of 24 chart values found | Text, Numeric, Complete |
| PyMuPDF | 3.29 | 18 tables found, 18 expected; 57 rows with a cell repeated across columns | 12% of lines repeated; 76 placeholder columns (Col2...) | 23 of 179 numbers missing (043, 270, 202) | 0 of 24 chart values found | Complete |
| Tesseract OCR | 2.95 | 0 tables found, 18 expected | none found | 45 of 179 numbers missing (4.4, 59, 2.1) | 13 of 24 chart values found | Text, Complete |

23 documents are listed: the ones where the best parser was at least 0.6 above the median, or 1.5 above the worst.

