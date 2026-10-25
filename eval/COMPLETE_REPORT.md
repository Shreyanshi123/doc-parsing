# Document parsing project: what we tested, what we found, and what it means

*A plain-language report. It starts from the first question and covers every kind of document we tested: digital PDFs, PDFs with tables, charts and photos, scans, Word, PowerPoint, Excel, CSV, plain text and images, then tough, real-world style and very long documents.*

## 1. The whole story in one page

- **The question.** For a given document, which parser (the software that reads the file and turns it into text) gives the best result? And can the app pick that parser by itself, based on measured results, not on guesses?
- **What was wrong at the start.** The app chose parsers with fixed rules that nobody had measured. Some choices looked random, for example OpenDataLoader for almost every table document.
- **What we did.** (1) A fresh test: 62 documents, every parser on every document, each result scored against an answer file written by hand. (2) The app now picks parsers from those scores. (3) Then we tried to break it with 34 harder documents: tough tables, real-world style business documents, and long documents of 30 to 100 pages.
- **The main finding.** There is no best parser for everything. Plain text and simple tables are fine with fast parsers. Charts need the vision model (smart_pdf). Scans need OCR or a layout model (Docling). Merged cells and tables inside tables need a layout-aware parser (PyMuPDF4LLM, OpenDataLoader or Docling).
- **What still goes wrong.** A few documents lose a lot in Smart Extract (about 3.0 instead of 4.5 to 5.0). The causes are known and listed in section 8. Nothing in the routing has been changed because of the new tests.

### Quick answer: which parser for which document

| Document type | Best choice from the tests | Watch out for |
|---|---|---|
| Digital PDF, mostly text | PyMuPDF (fast, scores 4.9) | Nothing special. |
| Digital PDF with tables | OpenDataLoader, PyMuPDF4LLM or Docling (all about 4.5) | Merged cells and nested tables: plain PyMuPDF, hybrid_pdf and smart_pdf are weaker. |
| PDF with charts or photos | smart_pdf when the chart values matter | On documents with only photos or diagrams, the free parsers can score higher because the vision model adds descriptions. |
| Scanned PDF or photo of a page | Docling | Parsers without OCR return nothing. Tesseract alone loses table structure. |
| Image files (png, jpg) | Docling (4.85) | - |
| Word | Unstructured or Docling; the native reader is slightly lower | Native reader dropped the page header on one file. |
| PowerPoint | Native reader; Docling when the deck has real charts | Native reader cannot read chart values. |
| Excel / CSV | Native reader (CSV 5.0) | Merged cells and charts need checking. |
| Plain text | Plain text reader (5.0) | Do not send it to other parsers. |

## 2. How we scored (in simple words)

Every parser output was compared with an answer file written by hand. The score is from 0 to 5 and is the average of up to eight questions:

| Question | In simple words |
|---|---|
| Text | Are the words right? |
| Table | Are the rows and columns right? |
| Chart | Were the chart values read? |
| Infographic | Were the labels in a diagram read? |
| Numbers | Are the numbers, dates and names exact? |
| Structure | Are headings, lists and order kept? |
| Complete | Is anything missing? |
| No extras | Did the parser add things that are not there? |

A crash, a timeout or an empty result counts as 0. Parsers within 0.1 of the best are treated as equal, and then the fastest one wins. Questions that do not apply to a document (for example Chart on a text page) are left out of its average.

## 3. The parsers and what they are

| Parser | What it is | Good at | Weak at |
|---|---|---|---|
| PyMuPDF | Very fast reader for PDFs that have a text layer | Plain text, simple tables | Merged cells, nested tables, scans (returns nothing) |
| PyMuPDF4LLM | PyMuPDF plus layout rules that write Markdown | Merged headers, long reports | Slower on big files |
| OpenDataLoader | Layout-aware PDF reader | Tables, forms | Scans (nothing), some side-by-side tables |
| Docling | Layout model with OCR | Scans, tables, slides, images | Slow (minutes on long files) |
| Unstructured | General document splitter | Word, Excel | PDF tables, plain text |
| MarkItDown | Converts Office files to Markdown | Excel, CSV | PDF tables |
| pdfplumber | PDF text and table finder | Simple tables | Structure |
| Tesseract OCR | Reads text from pictures | Scans | Tables (becomes plain lines) |
| hybrid_pdf | PyMuPDF + Tesseract OCR | Mixed text and scanned pages | Same table weaknesses as PyMuPDF |
| smart_pdf | PyMuPDF + Tesseract OCR + a vision model that looks at charts, diagrams and photos (at most 8 per document) | Reading chart values | Merged-header tables; adds descriptions of photos |
| Native readers | Word, PowerPoint, Excel and text readers built into the app | Clean Office files | Charts inside Office files |

Two parsers are kept out of the app on purpose: **vlm** (it sends every page to the Azure OpenAI model, too many API calls) and **Azure Document Intelligence** (paid; it can run next to the others as a comparison but was not part of these tests).

## 4. How Smart Extract works

Smart Extract looks at the document first, decides what kind it is, and picks parsers from the measured scores.

- **By document:** the whole file goes to the best parser for its type. If that parser fails, the next one is tried.
- **By part:** the file is split into pieces. Text and headings stay with PyMuPDF. Tables go to the parser that scored best on tables. Scanned pages go to the best scanned-page parser. Charts and photos go to the vision model (at most 8 per document).
- **Free or paid:** with *Include paid parsers* ticked, smart_pdf and the vision model can be used, and Azure Document Intelligence runs as an extra comparison tab. The result shown is always the best-ranked parser, never Azure by default.
- **Prefer quality:** turns off the tie rule, so the highest score wins even if it is slower.

## 5. First test: 62 documents

Every parser was run on every document it can open (786 runs). The table shows what Smart Extract uses first for each kind of document.

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

Full parser-against-parser tables for all 13 document types are in Appendix A.

**What the first test showed**

- Digital text PDFs: PyMuPDF, hybrid_pdf and smart_pdf tie at 4.94, and PyMuPDF is the fastest.
- PDFs with tables: Docling 4.50, OpenDataLoader 4.45 and PyMuPDF4LLM 4.44 are tied within 0.1; plain PyMuPDF is lower (4.31).
- PDFs with charts or photos: smart_pdf is first (3.88) because it reads chart values; the next best is 3.32.
- Scans: Docling 3.47 is first; PyMuPDF and pdfminer return nothing.
- Images: Docling 4.85. Word 4.1 to 4.2 (all close). PowerPoint: native 4.86. Excel and CSV: native is at or near the top. Plain text: native 5.0.

### Documents that mix text, tables, charts and photos

These were run through the real app, three ways.

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

## 6. The three new test sets

All three sets were generated by scripts in this project (`make_enterprise_docs.py`, `make_realistic_docs.py`, `make_long_docs.py`), each with a hand-written answer file. **None of them are real company files**; real files cannot be shared here. The layouts copy common real formats.

| Set | Documents | What it contains |
|---|---|---|
| Tough documents | 14 | merged-cell tables, a table inside a table, a table over many pages, wide tables, forms, a scan, charts with photos, Excel and Word |
| Real-world style | 14 | bank statement, income statement, purchase order, payslip, lab report, electricity bill with chart, bill of lading, RFP matrix, board minutes, two-column paper, a tilted phone photo of a purchase order, Excel with chart, Word SOP, PowerPoint with chart |
| Long documents | 6 | 56-page annual report with 10 charts, 100-page ledger (2,500 rows), 46-page contract, 31 scanned pages, 40-section Word handbook, 5-sheet Excel workbook |

### How the three sets did, in numbers

Smart Extract average score (0 to 5) over the PDFs in each set:

| Set | PDFs | By document, paid | By part, paid | By document, free |
|---|---|---|---|---|
| Tough documents | 12 | 4.32 (12) | 4.05 (12) | 4.59 (12) |
| Real-world style documents | 11 | 4.59 (11) | 4.26 (11) | 4.44 (11) |
| Long documents | 0 | - | - | - |

The number in brackets is how many documents finished. A smaller number means some runs are still going or did not finish.

## 7. Chapter by document type

### Digital PDFs (mostly text)

The easy case. Every parser with a text layer scores well, so speed decides. On the long contract and long report, PyMuPDF4LLM and Docling lead; the PyMuPDF family is a little lower.

| Document | Set | Pages | Best parser | Smart Extract: By document, By part, free | What happened |
|---|---|---|---|---|---|
| `contract_nested_clauses.pdf` | Tough documents | 3 | Docling 4.67 | 4.41 / 4.16 / 4.41 | Docling keeps the clause numbering best. |
| `long_annual_report_20p.pdf` | Tough documents | 19 | PyMuPDF4LLM 5.00 (tied: Docling) | 4.89 / 4.49 / 4.89 | PyMuPDF4LLM and Docling are perfect (5.0). |
| `board_minutes.pdf` | Real-world style documents | 1 | PyMuPDF4LLM 5.00 (tied: Docling, PyMuPDF, hybrid_pdf) | 4.61 / 4.91 / 4.61 | Mostly text. PyMuPDF4LLM and Docling are perfect. By document picked OpenDataLoader (4.61) because its rule is per document type, not per file. |
| `contract_45p.pdf` | Long documents | 46 | PyMuPDF4LLM 4.99 (tied: PyMuPDF, hybrid_pdf) | - / - / - | Result is in the ranking table in Appendix B; see the note below the table. |


### Digital PDFs with tables, forms and statements

The biggest group. Simple tables are easy for every layout-aware parser. Merged cells, side-by-side tables, nested tables and header rows that span columns are where parsers separate. The same few parsers (PyMuPDF4LLM, OpenDataLoader, Docling) keep leading, and plain PyMuPDF, hybrid_pdf and smart_pdf trail on the hard ones.

| Document | Set | Pages | Best parser | Smart Extract: By document, By part, free | What happened |
|---|---|---|---|---|---|
| `bom_wide_table.pdf` | Tough documents | 1 | Docling 5.00 (tied: OpenDataLoader, PyMuPDF, hybrid_pdf) | 4.99 / 4.89 / 4.99 | 12 columns in small print. The top parsers all keep every column. |
| `clinical_trial_table.pdf` | Tough documents | 1 | PyMuPDF4LLM 5.00 | 3.01 / 3.02 / 5.00 | PyMuPDF4LLM scores 5.0. smart_pdf scores 3.01 because the picture detector mistook the table lines for a figure. |
| `financial_statement_multiheader.pdf` | Tough documents | 1 | PyMuPDF4LLM 4.86 | 2.96 / 3.12 / 4.86 | Two-row merged header. PyMuPDF4LLM and Docling keep it together. Smart Extract with paid parsers fell to 2.96 because it copied the same numbers twice (see section 7). |
| `form_grid_ac4.pdf` | Tough documents | 1 | PyMuPDF 4.55 (tied: hybrid_pdf, smart_pdf, OpenDataLoader) | 4.52 / 4.42 / 4.52 | Easy for the PyMuPDF family. Nothing special. |
| `invoice_complex.pdf` | Tough documents | 1 | OpenDataLoader 4.85 | 4.47 / 4.38 / 4.67 | OpenDataLoader is best. smart_pdf adds a description of the QR code that is not in the answer. |
| `ledger_repeated_header.pdf` | Tough documents | 3 | Docling 5.00 (tied: OpenDataLoader) | 4.95 / 4.86 / 4.95 | The header repeating on every page did not hurt anybody. |
| `policy_schedule_nested.pdf` | Tough documents | 1 | OpenDataLoader 4.77 (tied: PyMuPDF4LLM) | 4.77 / 3.06 / 4.77 | A table inside a table. PyMuPDF4LLM and OpenDataLoader keep it right. PyMuPDF-based parsers repeat the outer text across columns. |
| `annual_report_income_statement.pdf` | Real-world style documents | 1 | OpenDataLoader 4.77 (tied: PyMuPDF4LLM) | 4.77 / 4.25 / 4.77 | Dollar signs in their own cells and numbers in brackets. Layout-aware parsers (OpenDataLoader, PyMuPDF4LLM, Docling) beat plain PyMuPDF by 0.3 to 0.4. |
| `bank_statement.pdf` | Real-world style documents | 3 | PyMuPDF4LLM 4.77 (tied: OpenDataLoader, Docling, PyMuPDF) | 4.76 / 4.68 / 4.76 | 3 pages, header repeated. Every parser with a text layer does well (4.5 to 4.8). |
| `bill_of_lading.pdf` | Real-world style documents | 1 | OpenDataLoader 4.56 | 4.56 / 3.93 / 4.56 | Merged cells. OpenDataLoader, Docling and PyMuPDF4LLM are ahead of the PyMuPDF family (3.85). |
| `lab_report.pdf` | Real-world style documents | 1 | Docling 4.93 (tied: PyMuPDF4LLM, PyMuPDF, hybrid_pdf) | 4.55 / 3.26 / 4.55 | Docling, PyMuPDF4LLM and the PyMuPDF family all above 4.8. By part scored only 3.26: the table piece came out with every merged cell repeated across 12 columns. |
| `payslip.pdf` | Real-world style documents | 1 | Docling 4.69 (tied: PyMuPDF4LLM) | 3.94 / 3.86 / 3.94 | Two tables side by side. Docling and PyMuPDF4LLM are best (4.6 to 4.7); OpenDataLoader, the choice for this type, scored 3.94. |
| `purchase_order.pdf` | Real-world style documents | 1 | OpenDataLoader 4.96 | 4.96 / 3.54 / 4.96 | OpenDataLoader 4.96 is best. By part scored only 3.54. |
| `rfp_requirements_matrix.pdf` | Real-world style documents | 1 | Docling 5.00 (tied: PyMuPDF, hybrid_pdf, smart_pdf) | 4.75 / 4.92 / 4.75 | Rowspan category cells and check boxes were easy: every top parser is 4.75 or better. |
| `transaction_ledger_100p.pdf` | Long documents | 100 | OpenDataLoader 5.00 (tied: PyMuPDF4LLM) | - / - / - | Result is in the ranking table in Appendix B; see the note below the table. |


### PDFs with charts, figures and photos

Only a vision model can read the numbers inside a chart. smart_pdf is first on each of the four chart documents of the tough and real-world sets (annual report spread, mixed page, research paper, electricity bill). The cost is a few seconds per figure and one API call per figure.

| Document | Set | Pages | Best parser | Smart Extract: By document, By part, free | What happened |
|---|---|---|---|---|---|
| `annual_report_spread.pdf` | Tough documents | 2 | smart_pdf 4.53 | 4.53 / 3.96 / 4.05 | Chart page. smart_pdf wins because it reads the chart values. |
| `mixed_table_chart_photo.pdf` | Tough documents | 1 | smart_pdf 3.90 | 3.90 / 3.79 / 3.55 | Table + chart + photo on one page. smart_pdf is best because it reads the chart. |
| `research_two_column.pdf` | Real-world style documents | 1 | smart_pdf 4.43 | 4.43 / 4.32 / 3.74 | Two columns with a chart. smart_pdf is clearly best (4.43) because it reads the chart. |
| `utility_bill.pdf` | Real-world style documents | 1 | smart_pdf 4.49 | 4.49 / 4.50 / 3.58 | Bill with a bar chart. smart_pdf wins (4.49) because it reads the chart; the free route scores 3.58. |
| `annual_report_60p.pdf` | Long documents | 56 | PyMuPDF4LLM 4.18 | - / - / - | Result is in the ranking table in Appendix B; see the note below the table. |


### Scanned PDFs and photos of pages

A scan has no text layer. Parsers that only read text return nothing (counted as 0). Docling reads scans best. hybrid_pdf and smart_pdf use only Tesseract OCR on scanned pages, so tables become plain lines.

| Document | Set | Pages | Best parser | Smart Extract: By document, By part, free | What happened |
|---|---|---|---|---|---|
| `scanned_financial_statement.pdf` | Tough documents | 1 | PyMuPDF4LLM 4.49 (tied: Docling) | 4.41 / 4.41 / 4.41 | A scan: parsers without OCR return nothing. Docling and PyMuPDF4LLM read it. |
| `scanned_purchase_order_phone.pdf` | Real-world style documents | 1 | Docling 4.67 | 4.67 / 4.67 / 4.67 | A tilted, noisy phone photo. Docling 4.67 is far ahead; hybrid_pdf and smart_pdf (Tesseract only) get 2.30. |
| `scanned_report_30p.pdf` | Long documents | 31 | Docling 4.58 | - / - / - | Result is in the ranking table in Appendix B; see the note below the table. |


### Word documents

Native Word reader is close to the others but lost the page header and flattened the list numbers on both Word files; Unstructured scored highest on both.

| Document | Set | Pages | Best parser | Smart Extract: By document, By part, free | What happened |
|---|---|---|---|---|---|
| `quality_manual.docx` | Tough documents | Word | Unstructured 4.86 | 4.09 / - / - | Unstructured is clearly better than the native Word reader (the native one drops the page header). |
| `sop_goods_receipt.docx` | Real-world style documents | Word | Unstructured 4.93 | 4.33 / - / - | Unstructured (4.93) is ahead of Docling (4.57) and the native Word reader (4.33). |
| `handbook_40p.docx` | Long documents | Word | native Word reader 5.00 (tied: Unstructured, Docling, MarkItDown) | - / - / - | Result is in the ranking table in Appendix B; see the note below the table. |


### PowerPoint

Native reader is best for normal slides. For a deck that has real chart objects, Docling reads the chart and the native reader cannot.

| Document | Set | Pages | Best parser | Smart Extract: By document, By part, free | What happened |
|---|---|---|---|---|---|
| `quarterly_review.pptx` | Real-world style documents | slides | Docling 4.50 | 4.50 / - / - | Deck with a real chart. Docling reads the chart (4.50); the native reader does not (4.01). |


### Excel

Native reader is close to the top. MarkItDown and Unstructured are equal or slightly better on some files, but not by the 0.5 margin the rule needs to replace the native reader.

| Document | Set | Pages | Best parser | Smart Extract: By document, By part, free | What happened |
|---|---|---|---|---|---|
| `budget_model.xlsx` | Tough documents | Excel | MarkItDown 4.31 | 4.04 / - / - | MarkItDown is slightly better than the native Excel reader; the rule keeps native first unless another parser wins by more than 0.5. |
| `hr_headcount_report.xlsx` | Real-world style documents | Excel | Unstructured 3.75 (tied: native Excel reader) | 3.73 / - / - | Excel with a real chart object. Native reader and Unstructured are tied (3.7). |
| `big_workbook.xlsx` | Long documents | Excel | native Excel reader 4.99 | - / - / - | Result is in the ranking table in Appendix B; see the note below the table. |


## 8. The problems we found

These are the real weak points. None of them is fixed yet, because you asked for testing, not changes.

1. **Table lines mistaken for a figure (clinical_trial_table 3.01, financial_statement_multiheader 2.96 in paid By document; free route 5.0 and 4.86).** PyMuPDF splits a table with merged cells into several small tables. The picture detector then sees one big group of lines that is not inside any single table and calls it a figure. We confirmed this by running the detector directly. The file is then sent to smart_pdf, which reads the table as a picture and also adds the PyMuPDF text, so the numbers appear twice. Fix idea: also check figures against the combined area of all detected tables.
2. **By part repeats merged cells (purchase_order 3.54 vs 4.96 By document; lab_report 3.26 vs 4.55; bill_of_lading 3.93 vs 4.56; policy_schedule_nested 3.06 vs 4.77).** In By part, a table piece can be read by PyMuPDF, which writes the same text into every column a merged cell covers. We saw this directly in the lab_report output; the same pattern is probable on the others. Fix idea: keep tables with merged cells or nested tables as one piece and give them to PyMuPDF4LLM or OpenDataLoader.
3. **A network error looks like a bad score.** annual_report_spread first scored 3.98 in Smart Extract. The vision call for the bar chart had failed with a connection error, so the chart was missing. Run again, it scored 4.53, the same as smart_pdf alone. Lesson: when a figure cannot be read, the result shows a warning line, and such a run should be repeated.
4. **The rule is per document type, not per file.** For digital PDFs with tables the first choice is OpenDataLoader. On board_minutes (mostly text) it scored 4.61 while PyMuPDF4LLM and Docling scored 5.0, and on payslip it scored 3.94 while Docling scored 4.69. A per-file check would do better but costs a test run per file.
5. **hybrid_pdf and smart_pdf are weak on scans.** Both use only Tesseract OCR on scanned pages: 2.3 to 2.4 on the two scanned documents of the tough and real-world sets, against 4.4 to 4.7 for Docling. Smart Extract avoids this by sending scans to Docling.
6. **Native Word and Excel readers lose a little.** The native Word reader drops the page header and flattens numbered lists. The difference is under the 0.5 margin on most files.

## 9. Long documents

Long documents were run with a limit of 10 minutes per parser per document (parsers vs parsers) and 15 minutes per Smart Extract run. A parser that does not finish is counted as 0 and shown as *timeout*.

| Document | Pages | Best parser | Parsers that timed out or returned nothing | Smart Extract: By document, By part, free |
|---|---|---|---|---|
| `annual_report_60p.pdf` | 56 | PyMuPDF4LLM 4.18 | Docling (timeout) | - / - / - |
| `big_workbook.xlsx` | Excel | native Excel reader 4.99 | none | - / - / - |
| `contract_45p.pdf` | 46 | PyMuPDF4LLM 4.99 (tied: PyMuPDF, hybrid_pdf) | none | - / - / - |
| `handbook_40p.docx` | Word | native Word reader 5.00 (tied: Unstructured, Docling, MarkItDown) | none | - / - / - |
| `scanned_report_30p.pdf` | 31 | Docling 4.58 | pdfplumber (empty), PyMuPDF (empty), MarkItDown (empty), OpenDataLoader (empty) | - / - / - |
| `transaction_ledger_100p.pdf` | 100 | OpenDataLoader 5.00 (tied: PyMuPDF4LLM) | none | - / - / - |

Smart Extract runs finished for long documents so far: 0. If this number is lower than 14, the run is still going and this section will be updated when the report is generated again.

Timings for long documents are measured but not exact, because the laptop was doing other things at the same time. What they show clearly: Docling and Tesseract OCR take minutes on 30 to 100 pages, while PyMuPDF takes seconds.

## 10. What is done and what is not

**Done and tested**

- Fresh 62-document head-to-head, with the routing built from it.
- Smart Extract By document, By part and free mode, in the app, on all three new sets.
- vlm is off everywhere; smart_pdf and By part read figures only (at most 8 per document).
- Detector problem and network error problem traced to their causes.

**Not done**

- Azure Document Intelligence on the new sets (it is paid; ask first).
- Fixes for the six problems in section 8. They change routing, so they need your yes.
- Real client documents: everything here is generated.
- The new sets are not part of the routing table. They only measure.

## 11. Limits

- All documents are generated; real files are messier.
- One run per parser and document. Differences under 0.1 are noise.
- Answer files are written by hand; a different but correct layout can lose points.
- Timings are only good for telling fast parsers from slow ones.
- LlamaParse (no key), MinerU, Marker and Azure Document Intelligence were not run.

## Appendix A. Parser against parser, the 62-document test

Higher is better. A crash or a timeout counts as 0 on every parameter the document can test. Seconds are the median per document.

#### Digital text PDF (6 documents)

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

#### Digital PDF with tables (15 documents)

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

#### PDF with charts, figures or images (13 documents)

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

#### Mixed PDF (text pages and scanned pages) (3 documents)

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

#### Scanned PDF (8 documents)

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

#### Image files (4 documents)

Documents: handwritten_note.png, id_card.png, receipt_photo.jpg, screenshot.png.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| docling | 4.85 | 4.85 | - | - | 4.90 | 12.6 | 0 | 4 |
| easyocr | 4.68 | 4.75 | - | - | 4.55 | 8.2 | 0 | 4 |
| ocr | 4.51 | 4.50 | - | - | 4.75 | 0.6 | 0 | 4 |
| unstructured | 4.44 | 4.47 | - | - | 4.60 | 3.7 | 0 | 4 |

#### Word (3 documents)

Documents: procedure.docx, report.docx, report_with_figures.docx.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| unstructured | 4.20 | 4.60 | 4.10 | 2.50 | 4.53 | 0.4 | 0 | 3 |
| docling | 4.17 | 4.60 | 3.90 | 2.50 | 4.53 | 0.8 | 0 | 3 |
| docx | 4.10 | 4.53 | 3.90 | 2.50 | 4.53 | 0.1 | 0 | 3 |
| markitdown | 3.96 | 4.47 | 4.10 | 2.50 | 3.53 | 0.6 | 0 | 3 |

#### PowerPoint (2 documents)

Documents: deck.pptx, slides.pptx.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| pptx | 4.86 | 4.75 | 5.00 | - | 4.85 | 0.0 | 0 | 2 |
| docling | 4.62 | 4.30 | 5.00 | - | 4.65 | 0.3 | 0 | 2 |
| unstructured | 4.56 | 4.30 | 5.00 | - | 4.25 | 0.2 | 0 | 2 |
| markitdown | 4.51 | 4.75 | 5.00 | - | 4.35 | 0.2 | 0 | 2 |

#### PowerPoint with charts (real chart objects) (1 documents)

Documents: dashboard.pptx.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| docling | 4.79 | 4.80 | 4.80 | 5.00 | 4.30 | 1.3 | 0 | 1 |
| markitdown | 3.84 | 4.00 | 3.40 | 5.00 | 3.70 | 0.7 | 0 | 1 |
| pptx | 2.76 | 3.30 | 2.70 | 0.00 | 3.70 | 0.0 | 0 | 1 |
| unstructured | 2.76 | 3.30 | 2.70 | 0.00 | 3.70 | 0.4 | 0 | 1 |

#### Excel (2 documents)

Documents: multi_sheet.xlsx, sales.xlsx.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| unstructured | 4.45 | 4.50 | 4.65 | - | 4.15 | 1.4 | 0 | 2 |
| spreadsheet | 4.33 | 4.40 | 4.40 | - | 4.20 | 0.0 | 0 | 2 |
| markitdown | 4.33 | 4.35 | 4.50 | - | 4.15 | 0.2 | 0 | 2 |
| docling | 4.26 | 4.45 | 4.45 | - | 3.50 | 0.4 | 0 | 2 |

#### Excel with charts (real chart objects) (1 documents)

Documents: sales_with_chart.xlsx.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| spreadsheet | 5.00 | 5.00 | 5.00 | - | 5.00 | 0.1 | 0 | 1 |
| markitdown | 5.00 | 5.00 | 5.00 | - | 5.00 | 0.5 | 0 | 1 |
| unstructured | 4.43 | 4.80 | 5.00 | - | 2.30 | 2.4 | 0 | 1 |
| docling | 3.05 | 3.10 | 3.40 | - | 1.60 | 1.0 | 0 | 1 |

#### CSV (2 documents)

Documents: parts.csv, sales.csv.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| spreadsheet | 5.00 | 5.00 | 5.00 | - | 5.00 | 0.8 | 0 | 2 |
| markitdown | 5.00 | 5.00 | 5.00 | - | 5.00 | 1.8 | 0 | 2 |
| unstructured | 5.00 | 5.00 | 5.00 | - | 5.00 | 2.2 | 0 | 2 |

#### Plain text (2 documents)

Documents: runbook.md, shift_notes.txt.

| Parser | Overall | Text | Tables | Charts | Structure | Seconds | Failed | Runs |
|---|---|---|---|---|---|---|---|---|
| text | 5.00 | 5.00 | 5.00 | - | 5.00 | 0.0 | 0 | 2 |
| unstructured | 2.08 | 2.50 | 0.00 | - | 2.50 | 0.1 | 1 | 2 |

## Appendix B. Ranking per document: tough, real-world and long sets

Sorted by score. *tied* means within 0.1 of the best. `-` means the question does not apply.

### annual_report_spread.pdf  (Tough documents, 2 pages)

| Rank | Parser | Score | Text | Table | Chart | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | smart_pdf | **4.53** | 4.60 | 4.10 | 5.00 | 4.80 | 4.10 | 4.90 | 4.30 | 5 |
| 2 | PyMuPDF4LLM | **4.05** | 4.70 | 3.60 | 2.10 | 4.30 | 4.30 | 4.60 | 4.70 | 74 |
| 3 | PyMuPDF | **3.69** | 4.60 | 3.80 | 0.00 | 4.10 | 4.20 | 4.20 | 4.90 | 2 |
| 4 | hybrid_pdf | **3.69** | 4.60 | 3.80 | 0.00 | 4.10 | 4.20 | 4.20 | 4.90 | 0 |
| 5 | OpenDataLoader | **3.50** | 4.30 | 3.90 | 0.00 | 3.60 | 4.10 | 3.70 | 5.00 | 19 |
| 6 | Docling | **3.42** | 4.10 | 4.00 | 0.00 | 3.40 | 3.90 | 3.50 | 5.00 | 189 |
| 7 | pdfplumber | **3.40** | 4.60 | 3.90 | 0.00 | 4.10 | 2.00 | 4.20 | 5.00 | 3 |
| 8 | MarkItDown | **3.07** | 4.60 | 1.40 | 0.00 | 4.10 | 2.10 | 4.20 | 5.00 | 2 |
| 9 | Tesseract OCR | **2.84** | 4.20 | 0.00 | 2.10 | 3.10 | 2.10 | 3.80 | 4.50 | 4 |
| 10 | Unstructured | **2.81** | 4.20 | 0.00 | 0.00 | 4.10 | 2.70 | 3.80 | 4.80 | 17 |

**Note:** Chart page. smart_pdf wins because it reads the chart values.

### bom_wide_table.pdf  (Tough documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Docling | **5.00** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 82 |
| 2 | OpenDataLoader (tied) | **4.99** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 20 |
| 3 | PyMuPDF (tied) | **4.93** | 4.90 | 4.90 | 5.00 | 5.00 | 5.00 | 4.90 | 14 |
| 4 | hybrid_pdf (tied) | **4.93** | 4.90 | 4.90 | 5.00 | 5.00 | 5.00 | 4.90 | 3 |
| 5 | smart_pdf (tied) | **4.93** | 4.90 | 4.90 | 5.00 | 5.00 | 5.00 | 4.90 | 2 |
| 6 | PyMuPDF4LLM | **4.77** | 5.00 | 3.60 | 5.00 | 5.00 | 5.00 | 5.00 | 9 |
| 7 | pdfplumber | **4.53** | 4.90 | 4.90 | 5.00 | 2.50 | 5.00 | 4.90 | 14 |
| 8 | MarkItDown | **3.54** | 5.00 | 0.00 | 5.00 | 1.30 | 5.00 | 5.00 | 4 |
| 9 | Unstructured | **3.54** | 5.00 | 0.00 | 5.00 | 1.30 | 5.00 | 5.00 | 1 |
| 10 | Tesseract OCR | **2.90** | 3.90 | 0.00 | 3.60 | 1.90 | 3.30 | 4.80 | 4 |

**Note:** 12 columns in small print. The top parsers all keep every column.

### budget_model.xlsx  (Tough documents)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | MarkItDown | **4.31** | 4.60 | 4.10 | 4.00 | 4.10 | 4.60 | 4.60 | 3 |
| 2 | native Excel reader | **4.04** | 4.30 | 3.80 | 3.50 | 3.90 | 4.60 | 4.00 | 8 |
| 3 | Unstructured | **3.97** | 4.30 | 3.80 | 3.50 | 3.50 | 4.60 | 4.00 | 4 |
| 4 | Docling | **3.71** | 4.20 | 3.80 | 3.50 | 2.20 | 4.60 | 3.90 | 187 |

**Note:** MarkItDown is slightly better than the native Excel reader; the rule keeps native first unless another parser wins by more than 0.5.

### clinical_trial_table.pdf  (Tough documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PyMuPDF4LLM | **5.00** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 6 |
| 2 | Docling | **4.82** | 4.70 | 5.00 | 5.00 | 4.80 | 4.50 | 5.00 | 367 |
| 3 | OpenDataLoader | **4.43** | 4.90 | 4.50 | 5.00 | 2.50 | 4.90 | 4.80 | 18 |
| 4 | pdfplumber | **4.26** | 4.90 | 4.10 | 4.90 | 2.00 | 5.00 | 4.70 | 1 |
| 5 | PyMuPDF | **4.08** | 4.60 | 3.60 | 4.80 | 2.20 | 4.90 | 4.30 | 2 |
| 6 | hybrid_pdf | **4.08** | 4.60 | 3.60 | 4.80 | 2.20 | 4.90 | 4.30 | 1 |
| 7 | MarkItDown | **3.66** | 4.90 | 0.00 | 5.00 | 2.20 | 4.90 | 4.90 | 1 |
| 8 | Unstructured | **3.56** | 4.90 | 0.00 | 5.00 | 1.60 | 4.90 | 4.90 | 0 |
| 9 | Tesseract OCR | **3.35** | 4.50 | 0.00 | 4.30 | 2.30 | 4.10 | 4.90 | 4 |
| 10 | smart_pdf | **3.01** | 3.20 | 2.70 | 3.20 | 1.60 | 4.90 | 2.40 | 0 |

**Note:** PyMuPDF4LLM scores 5.0. smart_pdf scores 3.01 because the picture detector mistook the table lines for a figure.

### contract_nested_clauses.pdf  (Tough documents, 3 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Docling | **4.67** | 4.70 | 5.00 | 4.10 | 4.80 | 4.40 | 5.00 | 108 |
| 2 | PyMuPDF4LLM | **4.45** | 5.00 | 2.00 | 5.00 | 4.70 | 5.00 | 5.00 | 12 |
| 3 | OpenDataLoader | **4.41** | 4.50 | 5.00 | 4.10 | 3.60 | 4.30 | 4.90 | 20 |
| 4 | PyMuPDF | **4.21** | 4.90 | 1.70 | 5.00 | 4.10 | 4.90 | 4.80 | 5 |
| 5 | hybrid_pdf | **4.21** | 4.90 | 1.70 | 5.00 | 4.10 | 4.90 | 4.80 | 1 |
| 6 | smart_pdf | **4.21** | 4.90 | 1.70 | 5.00 | 4.10 | 4.90 | 4.80 | 0 |
| 7 | pdfplumber | **3.96** | 5.00 | 1.70 | 5.00 | 2.20 | 5.00 | 4.90 | 2 |
| 8 | Unstructured | **3.70** | 4.90 | 0.00 | 5.00 | 2.60 | 4.90 | 4.90 | 0 |
| 9 | Tesseract OCR | **3.67** | 5.00 | 0.00 | 5.00 | 2.20 | 4.90 | 5.00 | 9 |
| 10 | MarkItDown | **3.64** | 4.90 | 0.00 | 5.00 | 2.20 | 4.90 | 4.90 | 1 |

**Note:** Docling keeps the clause numbering best.

### financial_statement_multiheader.pdf  (Tough documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PyMuPDF4LLM | **4.86** | 4.90 | 4.70 | 4.80 | 5.00 | 4.90 | 4.90 | 20 |
| 2 | Docling | **4.75** | 4.70 | 4.70 | 4.80 | 4.80 | 4.60 | 4.80 | 159 |
| 3 | OpenDataLoader | **4.51** | 4.90 | 4.80 | 5.00 | 2.50 | 4.90 | 4.90 | 15 |
| 4 | pdfplumber | **4.41** | 4.90 | 4.50 | 4.90 | 2.20 | 5.00 | 4.90 | 5 |
| 5 | MarkItDown | **4.29** | 5.00 | 3.30 | 5.00 | 2.50 | 5.00 | 5.00 | 1 |
| 6 | PyMuPDF | **3.94** | 4.30 | 3.60 | 4.80 | 2.10 | 4.90 | 3.90 | 4 |
| 7 | hybrid_pdf | **3.94** | 4.30 | 3.60 | 4.80 | 2.10 | 4.90 | 3.90 | 4 |
| 8 | Unstructured | **3.54** | 4.90 | 0.00 | 5.00 | 1.50 | 4.90 | 4.90 | 1 |
| 9 | Tesseract OCR | **3.20** | 4.40 | 0.00 | 3.80 | 2.20 | 4.10 | 4.80 | 5 |
| 10 | smart_pdf | **2.96** | 3.10 | 2.70 | 3.20 | 1.50 | 5.00 | 2.30 | 0 |

**Note:** Two-row merged header. PyMuPDF4LLM and Docling keep it together. Smart Extract with paid parsers fell to 2.96 because it copied the same numbers twice (see section 7).

### form_grid_ac4.pdf  (Tough documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PyMuPDF | **4.55** | 4.90 | 2.50 | 5.00 | 5.00 | 4.90 | 4.90 | 1 |
| 2 | hybrid_pdf (tied) | **4.55** | 4.90 | 2.50 | 5.00 | 5.00 | 4.90 | 4.90 | 0 |
| 3 | smart_pdf (tied) | **4.55** | 4.90 | 2.50 | 5.00 | 5.00 | 4.90 | 4.90 | 0 |
| 4 | OpenDataLoader (tied) | **4.52** | 4.90 | 2.50 | 5.00 | 5.00 | 4.90 | 4.90 | 13 |
| 5 | Docling | **4.43** | 5.00 | 1.60 | 5.00 | 5.00 | 5.00 | 5.00 | 16 |
| 6 | pdfplumber | **4.17** | 5.00 | 2.50 | 5.00 | 2.50 | 5.00 | 5.00 | 1 |
| 7 | PyMuPDF4LLM | **4.10** | 4.60 | 1.20 | 4.70 | 5.00 | 4.70 | 4.50 | 5 |
| 8 | Unstructured | **3.69** | 4.90 | 0.00 | 5.00 | 2.50 | 4.90 | 4.90 | 0 |
| 9 | Tesseract OCR | **3.62** | 4.90 | 0.00 | 5.00 | 2.10 | 4.80 | 4.90 | 2 |
| 10 | MarkItDown | **3.60** | 4.90 | 0.00 | 5.00 | 2.00 | 4.90 | 4.90 | 1 |

**Note:** Easy for the PyMuPDF family. Nothing special.

### invoice_complex.pdf  (Tough documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | OpenDataLoader | **4.85** | 5.00 | 4.80 | 5.00 | 4.50 | 5.00 | 5.00 | 22 |
| 2 | Docling | **4.71** | 5.00 | 4.40 | 5.00 | 3.90 | 4.90 | 5.00 | 28 |
| 3 | PyMuPDF4LLM | **4.67** | 4.80 | 3.90 | 4.90 | 4.80 | 5.00 | 4.70 | 20 |
| 4 | PyMuPDF | **4.61** | 4.90 | 4.00 | 5.00 | 4.10 | 5.00 | 4.80 | 3 |
| 5 | hybrid_pdf | **4.61** | 4.90 | 4.00 | 5.00 | 4.10 | 5.00 | 4.80 | 1 |
| 6 | smart_pdf | **4.47** | 4.60 | 4.00 | 5.00 | 4.00 | 5.00 | 4.30 | 0 |
| 7 | pdfplumber | **4.38** | 4.80 | 4.70 | 5.00 | 2.10 | 5.00 | 4.70 | 2 |
| 8 | MarkItDown | **4.05** | 4.90 | 2.10 | 5.00 | 2.40 | 5.00 | 4.90 | 1 |
| 9 | Unstructured | **3.68** | 4.90 | 0.00 | 5.00 | 2.30 | 4.90 | 4.90 | 1 |
| 10 | Tesseract OCR | **2.62** | 3.40 | 0.00 | 3.40 | 1.60 | 2.60 | 4.70 | 2 |

**Note:** OpenDataLoader is best. smart_pdf adds a description of the QR code that is not in the answer.

### ledger_repeated_header.pdf  (Tough documents, 3 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Docling | **5.00** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 105 |
| 2 | OpenDataLoader (tied) | **4.95** | 5.00 | 4.70 | 5.00 | 5.00 | 5.00 | 5.00 | 39 |
| 3 | PyMuPDF | **4.86** | 5.00 | 4.20 | 5.00 | 5.00 | 5.00 | 5.00 | 40 |
| 4 | PyMuPDF4LLM | **4.86** | 5.00 | 4.20 | 5.00 | 5.00 | 5.00 | 5.00 | 35 |
| 5 | hybrid_pdf | **4.86** | 5.00 | 4.20 | 5.00 | 5.00 | 5.00 | 5.00 | 23 |
| 6 | smart_pdf | **4.86** | 5.00 | 4.20 | 5.00 | 5.00 | 5.00 | 5.00 | 12 |
| 7 | pdfplumber | **4.45** | 5.00 | 4.20 | 5.00 | 2.50 | 5.00 | 5.00 | 47 |
| 8 | MarkItDown | **3.74** | 5.00 | 0.00 | 5.00 | 2.40 | 5.00 | 5.00 | 36 |
| 9 | Unstructured | **3.66** | 5.00 | 0.00 | 5.00 | 2.00 | 5.00 | 5.00 | 6 |
| 10 | Tesseract OCR | **3.01** | 3.90 | 0.10 | 4.00 | 1.90 | 3.20 | 4.90 | 20 |

**Note:** The header repeating on every page did not hurt anybody.

### long_annual_report_20p.pdf  (Tough documents, 19 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PyMuPDF4LLM | **5.00** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 114 |
| 2 | Docling (tied) | **5.00** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 116 |
| 3 | OpenDataLoader | **4.89** | 5.00 | 4.40 | 5.00 | 5.00 | 5.00 | 5.00 | 268 |
| 4 | pdfplumber | **4.58** | 5.00 | 5.00 | 5.00 | 2.50 | 5.00 | 5.00 | 136 |
| 5 | smart_pdf | **4.48** | 4.70 | 4.00 | 4.00 | 4.80 | 5.00 | 4.40 | 35 |
| 6 | PyMuPDF | **4.46** | 4.70 | 3.90 | 3.90 | 4.80 | 5.00 | 4.40 | 152 |
| 7 | hybrid_pdf | **4.46** | 4.70 | 3.90 | 3.90 | 4.80 | 5.00 | 4.40 | 79 |
| 8 | Unstructured | **3.86** | 5.00 | 0.00 | 5.00 | 3.20 | 5.00 | 5.00 | 16 |
| 9 | MarkItDown | **3.73** | 5.00 | 0.00 | 5.00 | 2.40 | 5.00 | 5.00 | 152 |
| 10 | Tesseract OCR | **3.55** | 4.90 | 0.00 | 4.20 | 2.50 | 4.80 | 4.90 | 141 |

**Note:** PyMuPDF4LLM and Docling are perfect (5.0).

### mixed_table_chart_photo.pdf  (Tough documents, 1 pages)

| Rank | Parser | Score | Text | Table | Chart | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | smart_pdf | **3.90** | 3.60 | 3.60 | 5.00 | 4.00 | 3.20 | 5.00 | 2.90 | 9 |
| 2 | PyMuPDF4LLM | **3.55** | 4.50 | 3.60 | 0.00 | 4.20 | 3.70 | 4.60 | 4.30 | 4 |
| 3 | OpenDataLoader | **3.51** | 4.50 | 3.90 | 0.00 | 3.70 | 3.50 | 4.10 | 5.00 | 77 |
| 4 | Docling | **3.44** | 4.40 | 3.30 | 0.00 | 3.70 | 3.80 | 4.10 | 4.90 | 14 |
| 5 | PyMuPDF | **3.35** | 4.20 | 3.10 | 0.00 | 3.90 | 3.80 | 4.10 | 4.30 | 0 |
| 6 | hybrid_pdf | **3.35** | 4.20 | 3.10 | 0.00 | 3.90 | 3.80 | 4.10 | 4.30 | 0 |
| 7 | MarkItDown | **3.33** | 4.50 | 3.90 | 0.00 | 3.70 | 2.20 | 4.10 | 5.00 | 1 |
| 8 | pdfplumber | **3.08** | 4.30 | 3.30 | 0.00 | 3.70 | 1.70 | 4.10 | 4.50 | 1 |
| 9 | Unstructured | **2.79** | 4.40 | 0.00 | 0.00 | 3.70 | 2.60 | 4.00 | 4.90 | 0 |
| 10 | Tesseract OCR | **2.09** | 3.40 | 0.00 | 0.00 | 2.10 | 1.70 | 2.70 | 4.70 | 4 |

**Note:** Table + chart + photo on one page. smart_pdf is best because it reads the chart.

### policy_schedule_nested.pdf  (Tough documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | OpenDataLoader | **4.77** | 5.00 | 3.60 | 5.00 | 5.00 | 5.00 | 5.00 | 58 |
| 2 | PyMuPDF4LLM (tied) | **4.77** | 5.00 | 3.60 | 5.00 | 5.00 | 5.00 | 5.00 | 2 |
| 3 | MarkItDown | **4.58** | 5.00 | 5.00 | 5.00 | 2.50 | 5.00 | 5.00 | 1 |
| 4 | pdfplumber | **4.36** | 5.00 | 3.60 | 5.00 | 2.50 | 5.00 | 5.00 | 0 |
| 5 | Tesseract OCR | **3.67** | 5.00 | 0.00 | 5.00 | 2.20 | 4.90 | 5.00 | 2 |
| 6 | Docling | **3.62** | 3.60 | 2.70 | 3.20 | 4.30 | 5.00 | 2.80 | 13 |
| 7 | Unstructured | **3.58** | 5.00 | 0.00 | 5.00 | 1.50 | 5.00 | 5.00 | 0 |
| 8 | PyMuPDF | **2.92** | 2.70 | 1.90 | 2.20 | 3.80 | 5.00 | 1.90 | 1 |
| 9 | hybrid_pdf | **2.92** | 2.70 | 1.90 | 2.20 | 3.80 | 5.00 | 1.90 | 0 |
| 10 | smart_pdf | **2.92** | 2.70 | 1.90 | 2.20 | 3.80 | 5.00 | 1.90 | 0 |

**Note:** A table inside a table. PyMuPDF4LLM and OpenDataLoader keep it right. PyMuPDF-based parsers repeat the outer text across columns.

### quality_manual.docx  (Tough documents)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Unstructured | **4.86** | 4.90 | 4.80 | 4.60 | 5.00 | 5.00 | 4.90 | 0 |
| 2 | MarkItDown | **4.40** | 4.50 | 4.80 | 3.90 | 4.30 | 4.30 | 4.60 | 4 |
| 3 | Docling | **4.19** | 4.20 | 4.30 | 3.60 | 4.60 | 4.20 | 4.20 | 1 |
| 4 | native Word reader | **4.09** | 4.20 | 4.30 | 3.20 | 4.60 | 4.20 | 4.20 | 3 |

**Note:** Unstructured is clearly better than the native Word reader (the native one drops the page header).

### scanned_financial_statement.pdf  (Tough documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PyMuPDF4LLM | **4.49** | 4.80 | 4.00 | 4.80 | 3.70 | 4.80 | 4.80 | 11 |
| 2 | Docling (tied) | **4.41** | 4.40 | 4.30 | 4.80 | 4.20 | 4.70 | 4.10 | 29 |
| 3 | Unstructured | **3.03** | 4.20 | 0.00 | 3.70 | 1.90 | 3.90 | 4.50 | 20 |
| 4 | hybrid_pdf | **2.36** | 3.30 | 0.00 | 2.40 | 1.30 | 2.50 | 4.80 | 12 |
| 5 | Tesseract OCR | **2.36** | 3.30 | 0.00 | 2.40 | 1.30 | 2.50 | 4.80 | 7 |
| 6 | smart_pdf | **2.36** | 3.30 | 0.00 | 2.40 | 1.30 | 2.50 | 4.80 | 8 |
| - | pdfplumber | 0.00 (empty) | - | - | - | - | - | - | 0 |
| - | PyMuPDF | 0.00 (empty) | - | - | - | - | - | - | 0 |
| - | MarkItDown | 0.00 (empty) | - | - | - | - | - | - | 1 |
| - | OpenDataLoader | 0.00 (empty) | - | - | - | - | - | - | 23 |

**Note:** A scan: parsers without OCR return nothing. Docling and PyMuPDF4LLM read it.

### annual_report_income_statement.pdf  (Real-world style documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | OpenDataLoader | **4.77** | 4.90 | 4.30 | 5.00 | 4.50 | 4.90 | 4.90 | 4 |
| 2 | PyMuPDF4LLM (tied) | **4.71** | 4.90 | 3.50 | 5.00 | 5.00 | 4.90 | 4.90 | 5 |
| 3 | Docling | **4.60** | 4.70 | 4.10 | 4.60 | 4.80 | 5.00 | 4.40 | 32 |
| 4 | pdfplumber | **4.36** | 4.90 | 4.20 | 4.90 | 2.10 | 5.00 | 4.90 | 0 |
| 5 | MarkItDown | **4.34** | 5.00 | 3.50 | 5.00 | 2.50 | 5.00 | 5.00 | 0 |
| 6 | PyMuPDF | **4.33** | 4.40 | 3.70 | 4.50 | 4.60 | 4.90 | 3.90 | 0 |
| 7 | hybrid_pdf | **4.33** | 4.40 | 3.70 | 4.50 | 4.60 | 4.90 | 3.90 | 0 |
| 8 | smart_pdf | **4.33** | 4.40 | 3.70 | 4.50 | 4.60 | 4.90 | 3.90 | 1 |
| 9 | Unstructured | **3.62** | 4.90 | 0.00 | 5.00 | 1.90 | 4.90 | 4.90 | 10 |
| 10 | Tesseract OCR | **2.32** | 3.20 | 0.00 | 1.80 | 1.90 | 2.40 | 4.60 | 1 |

**Note:** Dollar signs in their own cells and numbers in brackets. Layout-aware parsers (OpenDataLoader, PyMuPDF4LLM, Docling) beat plain PyMuPDF by 0.3 to 0.4.

### bank_statement.pdf  (Real-world style documents, 3 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PyMuPDF4LLM | **4.77** | 5.00 | 5.00 | 5.00 | 3.60 | 5.00 | 5.00 | 4 |
| 2 | OpenDataLoader (tied) | **4.76** | 4.90 | 4.90 | 4.90 | 4.00 | 4.80 | 5.00 | 5 |
| 3 | Docling (tied) | **4.71** | 4.90 | 5.00 | 4.90 | 3.70 | 4.80 | 5.00 | 35 |
| 4 | PyMuPDF (tied) | **4.68** | 4.80 | 4.70 | 4.90 | 3.90 | 4.90 | 4.80 | 2 |
| 5 | hybrid_pdf (tied) | **4.68** | 4.80 | 4.70 | 4.90 | 3.90 | 4.90 | 4.80 | 1 |
| 6 | smart_pdf (tied) | **4.68** | 4.80 | 4.70 | 4.90 | 3.90 | 4.90 | 4.80 | 2 |
| 7 | pdfplumber | **4.54** | 5.00 | 5.00 | 5.00 | 2.20 | 5.00 | 5.00 | 1 |
| 8 | MarkItDown | **3.98** | 5.00 | 1.60 | 5.00 | 2.30 | 5.00 | 5.00 | 2 |
| 9 | Unstructured | **3.57** | 5.00 | 0.00 | 5.00 | 1.40 | 5.00 | 5.00 | 2 |
| 10 | Tesseract OCR | **2.99** | 4.00 | 0.00 | 3.80 | 1.90 | 3.40 | 4.80 | 4 |

**Note:** 3 pages, header repeated. Every parser with a text layer does well (4.5 to 4.8).

### bill_of_lading.pdf  (Real-world style documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | OpenDataLoader | **4.56** | 4.80 | 3.60 | 4.60 | 4.90 | 4.50 | 5.00 | 5 |
| 2 | Docling | **4.45** | 4.50 | 3.40 | 4.80 | 4.80 | 5.00 | 4.20 | 7 |
| 3 | PyMuPDF4LLM | **4.38** | 4.50 | 3.30 | 4.60 | 4.80 | 4.40 | 4.70 | 2 |
| 4 | PyMuPDF | **3.85** | 4.00 | 2.30 | 4.00 | 4.50 | 4.60 | 3.60 | 0 |
| 5 | hybrid_pdf | **3.85** | 4.00 | 2.30 | 4.00 | 4.50 | 4.60 | 3.60 | 0 |
| 6 | smart_pdf | **3.85** | 4.00 | 2.30 | 4.00 | 4.50 | 4.60 | 3.60 | 0 |
| 7 | pdfplumber | **3.84** | 4.60 | 2.80 | 4.60 | 2.00 | 4.50 | 4.60 | 0 |
| 8 | MarkItDown | **3.66** | 4.80 | 1.10 | 4.60 | 2.00 | 4.50 | 5.00 | 0 |
| 9 | Unstructured | **3.46** | 4.80 | 0.00 | 4.60 | 1.90 | 4.50 | 5.00 | 0 |
| 10 | Tesseract OCR | **3.30** | 4.50 | 0.00 | 4.20 | 1.90 | 4.20 | 4.90 | 1 |

**Note:** Merged cells. OpenDataLoader, Docling and PyMuPDF4LLM are ahead of the PyMuPDF family (3.85).

### board_minutes.pdf  (Real-world style documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PyMuPDF4LLM | **5.00** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 2 |
| 2 | Docling (tied) | **5.00** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 7 |
| 3 | PyMuPDF (tied) | **4.91** | 4.90 | 4.80 | 5.00 | 5.00 | 4.90 | 4.90 | 0 |
| 4 | hybrid_pdf (tied) | **4.91** | 4.90 | 4.80 | 5.00 | 5.00 | 4.90 | 4.90 | 0 |
| 5 | smart_pdf (tied) | **4.91** | 4.90 | 4.80 | 5.00 | 5.00 | 4.90 | 4.90 | 0 |
| 6 | OpenDataLoader | **4.61** | 4.90 | 4.80 | 5.00 | 3.20 | 4.90 | 4.90 | 3 |
| 7 | pdfplumber | **4.56** | 5.00 | 5.00 | 5.00 | 2.30 | 5.00 | 5.00 | 0 |
| 8 | Unstructured | **3.69** | 4.90 | 0.00 | 5.00 | 2.40 | 4.90 | 4.90 | 0 |
| 9 | MarkItDown | **3.65** | 4.90 | 0.00 | 5.00 | 2.20 | 4.90 | 4.90 | 0 |
| 10 | Tesseract OCR | **3.64** | 4.80 | 0.00 | 4.90 | 2.40 | 4.70 | 5.00 | 1 |

**Note:** Mostly text. PyMuPDF4LLM and Docling are perfect. By document picked OpenDataLoader (4.61) because its rule is per document type, not per file.

### hr_headcount_report.xlsx  (Real-world style documents)

| Rank | Parser | Score | Text | Table | Chart | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Unstructured | **3.75** | 3.60 | 3.50 | 5.00 | 3.70 | 3.10 | 3.20 | 4.00 | 1 |
| 2 | native Excel reader (tied) | **3.73** | 3.70 | 3.50 | 5.00 | 3.70 | 2.90 | 3.30 | 4.10 | 0 |
| 3 | Docling | **3.56** | 3.50 | 3.80 | 5.00 | 3.80 | 1.50 | 4.20 | 3.00 | 0 |
| 4 | MarkItDown | **3.40** | 3.30 | 2.80 | 5.00 | 3.40 | 2.70 | 3.50 | 3.10 | 0 |

**Note:** Excel with a real chart object. Native reader and Unstructured are tied (3.7).

### lab_report.pdf  (Real-world style documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Docling | **4.93** | 5.00 | 4.60 | 5.00 | 5.00 | 5.00 | 5.00 | 10 |
| 2 | PyMuPDF4LLM (tied) | **4.88** | 4.90 | 4.40 | 5.00 | 5.00 | 5.00 | 4.90 | 2 |
| 3 | PyMuPDF (tied) | **4.85** | 4.90 | 4.50 | 5.00 | 4.90 | 5.00 | 4.80 | 0 |
| 4 | hybrid_pdf (tied) | **4.85** | 4.90 | 4.50 | 5.00 | 4.90 | 5.00 | 4.80 | 0 |
| 5 | smart_pdf (tied) | **4.85** | 4.90 | 4.50 | 5.00 | 4.90 | 5.00 | 4.80 | 0 |
| 6 | OpenDataLoader | **4.55** | 4.70 | 4.30 | 5.00 | 4.00 | 5.00 | 4.40 | 4 |
| 7 | pdfplumber | **4.38** | 5.00 | 4.50 | 5.00 | 1.90 | 5.00 | 4.90 | 0 |
| 8 | MarkItDown | **4.26** | 5.00 | 3.00 | 5.00 | 2.50 | 5.00 | 5.00 | 0 |
| 9 | Unstructured | **3.68** | 4.90 | 0.00 | 5.00 | 2.20 | 5.00 | 4.90 | 0 |
| 10 | Tesseract OCR | **3.02** | 4.00 | 0.00 | 3.90 | 2.20 | 3.80 | 4.30 | 1 |

**Note:** Docling, PyMuPDF4LLM and the PyMuPDF family all above 4.8. By part scored only 3.26: the table piece came out with every merged cell repeated across 12 columns.

### payslip.pdf  (Real-world style documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Docling | **4.69** | 5.00 | 4.00 | 5.00 | 4.20 | 5.00 | 5.00 | 10 |
| 2 | PyMuPDF4LLM (tied) | **4.62** | 5.00 | 4.00 | 5.00 | 3.70 | 5.00 | 5.00 | 2 |
| 3 | MarkItDown | **4.34** | 5.00 | 4.00 | 5.00 | 2.00 | 5.00 | 5.00 | 0 |
| 4 | PyMuPDF | **4.05** | 4.90 | 0.90 | 5.00 | 3.70 | 5.00 | 4.80 | 0 |
| 5 | hybrid_pdf | **4.05** | 4.90 | 0.90 | 5.00 | 3.70 | 5.00 | 4.80 | 0 |
| 6 | smart_pdf | **4.05** | 4.90 | 0.90 | 5.00 | 3.70 | 5.00 | 4.80 | 0 |
| 7 | OpenDataLoader | **3.94** | 5.00 | 0.00 | 5.00 | 3.70 | 5.00 | 5.00 | 2 |
| 8 | pdfplumber | **3.67** | 4.90 | 0.90 | 5.00 | 1.40 | 5.00 | 4.80 | 0 |
| 9 | Unstructured | **3.61** | 5.00 | 0.00 | 5.00 | 1.70 | 5.00 | 5.00 | 0 |
| 10 | Tesseract OCR | **3.53** | 4.80 | 0.00 | 4.80 | 1.90 | 4.60 | 5.00 | 1 |

**Note:** Two tables side by side. Docling and PyMuPDF4LLM are best (4.6 to 4.7); OpenDataLoader, the choice for this type, scored 3.94.

### purchase_order.pdf  (Real-world style documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | OpenDataLoader | **4.96** | 5.00 | 4.80 | 5.00 | 5.00 | 5.00 | 5.00 | 4 |
| 2 | PyMuPDF | **4.79** | 4.90 | 4.50 | 5.00 | 4.40 | 5.00 | 4.90 | 0 |
| 3 | PyMuPDF4LLM | **4.79** | 4.70 | 4.60 | 5.00 | 4.90 | 4.90 | 4.60 | 8 |
| 4 | hybrid_pdf | **4.79** | 4.90 | 4.50 | 5.00 | 4.40 | 5.00 | 4.90 | 0 |
| 5 | Docling | **4.79** | 5.00 | 5.00 | 5.00 | 3.80 | 5.00 | 5.00 | 11 |
| 6 | smart_pdf | **4.79** | 4.90 | 4.50 | 5.00 | 4.40 | 5.00 | 4.90 | 0 |
| 7 | pdfplumber | **4.30** | 4.90 | 4.50 | 5.00 | 1.50 | 5.00 | 4.90 | 0 |
| 8 | MarkItDown | **4.02** | 5.00 | 1.90 | 5.00 | 2.20 | 5.00 | 5.00 | 0 |
| 9 | Unstructured | **3.80** | 5.00 | 0.00 | 5.00 | 2.80 | 5.00 | 5.00 | 0 |
| 10 | Tesseract OCR | **3.06** | 4.20 | 0.00 | 3.80 | 1.90 | 3.70 | 4.70 | 1 |

**Note:** OpenDataLoader 4.96 is best. By part scored only 3.54.

### quarterly_review.pptx  (Real-world style documents)

| Rank | Parser | Score | Text | Table | Chart | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Docling | **4.50** | 4.40 | 4.70 | 5.00 | 5.00 | 3.70 | 3.90 | 4.90 | 0 |
| 2 | MarkItDown | **4.12** | 4.70 | 3.60 | 5.00 | 2.90 | 3.30 | 4.70 | 4.60 | 0 |
| 3 | native PowerPoint reader | **4.01** | 4.20 | 3.50 | 3.80 | 3.90 | 4.20 | 3.70 | 4.90 | 0 |
| 4 | Unstructured | **3.72** | 3.70 | 3.50 | 3.80 | 3.90 | 3.30 | 2.90 | 5.00 | 0 |

**Note:** Deck with a real chart. Docling reads the chart (4.50); the native reader does not (4.01).

### research_two_column.pdf  (Real-world style documents, 1 pages)

| Rank | Parser | Score | Text | Table | Chart | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | smart_pdf | **4.43** | 4.50 | 3.70 | 5.00 | 4.80 | 4.00 | 5.00 | 4.10 | 4 |
| 2 | Docling | **3.79** | 4.80 | 3.80 | 0.00 | 4.00 | 4.40 | 4.60 | 4.90 | 8 |
| 3 | PyMuPDF4LLM | **3.74** | 4.70 | 3.10 | 0.00 | 4.30 | 4.60 | 4.80 | 4.70 | 7 |
| 4 | OpenDataLoader | **3.72** | 4.70 | 3.80 | 0.00 | 4.00 | 4.10 | 4.50 | 5.00 | 4 |
| 5 | PyMuPDF | **3.50** | 4.50 | 2.60 | 0.00 | 4.20 | 4.10 | 4.50 | 4.60 | 0 |
| 6 | hybrid_pdf | **3.50** | 4.50 | 2.60 | 0.00 | 4.20 | 4.10 | 4.50 | 4.60 | 0 |
| 7 | pdfplumber | **3.24** | 4.60 | 2.90 | 0.00 | 4.00 | 1.90 | 4.50 | 4.80 | 0 |
| 8 | Tesseract OCR | **2.57** | 4.40 | 0.00 | 0.00 | 2.70 | 2.20 | 4.30 | 4.40 | 1 |
| 9 | MarkItDown | **2.23** | 3.60 | 0.00 | 0.00 | 2.20 | 2.40 | 3.10 | 4.20 | 1 |
| 10 | Unstructured | **2.14** | 3.40 | 0.00 | 0.00 | 2.20 | 2.10 | 2.80 | 4.40 | 0 |

**Note:** Two columns with a chart. smart_pdf is clearly best (4.43) because it reads the chart.

### rfp_requirements_matrix.pdf  (Real-world style documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Docling | **5.00** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 10 |
| 2 | PyMuPDF (tied) | **4.95** | 5.00 | 4.90 | 5.00 | 5.00 | 5.00 | 4.90 | 0 |
| 3 | hybrid_pdf (tied) | **4.95** | 5.00 | 4.90 | 5.00 | 5.00 | 5.00 | 4.90 | 0 |
| 4 | smart_pdf (tied) | **4.95** | 5.00 | 4.90 | 5.00 | 5.00 | 5.00 | 4.90 | 0 |
| 5 | PyMuPDF4LLM | **4.89** | 4.90 | 4.70 | 5.00 | 4.90 | 4.80 | 5.00 | 3 |
| 6 | OpenDataLoader | **4.75** | 4.90 | 4.70 | 5.00 | 4.10 | 4.80 | 5.00 | 3 |
| 7 | pdfplumber | **4.40** | 4.90 | 4.60 | 5.00 | 2.20 | 4.80 | 4.90 | 0 |
| 8 | MarkItDown | **3.66** | 4.90 | 0.00 | 5.00 | 2.30 | 4.80 | 5.00 | 1 |
| 9 | Unstructured | **3.66** | 4.90 | 0.00 | 5.00 | 2.20 | 4.80 | 5.00 | 0 |
| 10 | Tesseract OCR | **3.64** | 4.90 | 0.00 | 5.00 | 2.20 | 4.70 | 5.00 | 1 |

**Note:** Rowspan category cells and check boxes were easy: every top parser is 4.75 or better.

### scanned_purchase_order_phone.pdf  (Real-world style documents, 1 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Docling | **4.67** | 5.00 | 3.30 | 5.00 | 4.80 | 5.00 | 4.90 | 13 |
| 2 | PyMuPDF4LLM | **3.58** | 4.50 | 0.50 | 4.00 | 3.60 | 4.50 | 4.40 | 7 |
| 3 | Unstructured | **2.90** | 3.80 | 0.00 | 3.30 | 2.50 | 3.30 | 4.50 | 9 |
| 4 | hybrid_pdf | **2.30** | 3.20 | 0.00 | 2.30 | 1.60 | 2.80 | 3.80 | 2 |
| 5 | Tesseract OCR | **2.30** | 3.20 | 0.00 | 2.30 | 1.60 | 2.80 | 3.80 | 2 |
| 6 | smart_pdf | **2.30** | 3.20 | 0.00 | 2.30 | 1.60 | 2.80 | 3.80 | 5 |
| - | pdfplumber | 0.00 (empty) | - | - | - | - | - | - | 0 |
| - | PyMuPDF | 0.00 (empty) | - | - | - | - | - | - | 0 |
| - | MarkItDown | 0.00 (empty) | - | - | - | - | - | - | 0 |
| - | OpenDataLoader | 0.00 (empty) | - | - | - | - | - | - | 2 |

**Note:** A tilted, noisy phone photo. Docling 4.67 is far ahead; hybrid_pdf and smart_pdf (Tesseract only) get 2.30.

### sop_goods_receipt.docx  (Real-world style documents)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Unstructured | **4.93** | 4.90 | 4.80 | 5.00 | 5.00 | 4.90 | 5.00 | 0 |
| 2 | Docling | **4.57** | 4.60 | 5.00 | 3.90 | 4.80 | 4.20 | 5.00 | 0 |
| 3 | MarkItDown | **4.34** | 4.40 | 4.80 | 3.70 | 4.30 | 4.10 | 4.80 | 1 |
| 4 | native Word reader | **4.33** | 4.50 | 5.00 | 2.80 | 4.80 | 4.10 | 4.90 | 0 |

**Note:** Unstructured (4.93) is ahead of Docling (4.57) and the native Word reader (4.33).

### utility_bill.pdf  (Real-world style documents, 1 pages)

| Rank | Parser | Score | Text | Table | Chart | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | smart_pdf | **4.49** | 4.60 | 4.50 | 5.00 | 4.90 | 3.10 | 5.00 | 4.30 | 4 |
| 2 | PyMuPDF4LLM | **3.58** | 4.70 | 3.20 | 0.00 | 4.30 | 3.40 | 4.80 | 4.60 | 2 |
| 3 | OpenDataLoader | **3.49** | 4.50 | 3.00 | 0.00 | 4.30 | 3.50 | 4.10 | 5.00 | 3 |
| 4 | Docling | **3.45** | 4.60 | 3.20 | 0.00 | 4.30 | 2.80 | 4.20 | 5.00 | 9 |
| 5 | PyMuPDF | **3.44** | 4.40 | 2.90 | 0.00 | 4.30 | 3.50 | 4.10 | 4.90 | 0 |
| 6 | hybrid_pdf | **3.44** | 4.40 | 2.90 | 0.00 | 4.30 | 3.50 | 4.10 | 4.90 | 0 |
| 7 | pdfplumber | **3.19** | 4.40 | 2.90 | 0.00 | 4.30 | 1.70 | 4.10 | 4.90 | 0 |
| 8 | MarkItDown | **2.84** | 4.50 | 0.00 | 0.00 | 4.30 | 2.00 | 4.10 | 5.00 | 1 |
| 9 | Unstructured | **2.73** | 4.50 | 0.00 | 0.00 | 4.30 | 1.20 | 4.10 | 5.00 | 0 |
| 10 | Tesseract OCR | **2.70** | 4.50 | 0.00 | 0.00 | 3.80 | 1.70 | 4.40 | 4.60 | 1 |

**Note:** Bill with a bar chart. smart_pdf wins (4.49) because it reads the chart; the free route scores 3.58.

### annual_report_60p.pdf  (Long documents, 56 pages)

| Rank | Parser | Score | Text | Table | Chart | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PyMuPDF4LLM | **4.18** | 5.00 | 4.80 | 0.00 | 4.90 | 4.70 | 5.00 | 5.00 | 52 |
| 2 | OpenDataLoader | **3.91** | 4.90 | 4.10 | 0.00 | 4.30 | 4.30 | 4.80 | 5.00 | 20 |
| 3 | pdfplumber | **3.86** | 5.00 | 4.80 | 0.00 | 4.80 | 2.40 | 5.00 | 5.00 | 18 |
| 4 | MarkItDown | **3.56** | 5.00 | 2.80 | 0.00 | 4.80 | 2.40 | 5.00 | 5.00 | 13 |
| 5 | PyMuPDF | **3.46** | 4.40 | 3.00 | 0.00 | 3.30 | 4.40 | 5.00 | 4.00 | 24 |
| 6 | hybrid_pdf | **3.46** | 4.40 | 3.00 | 0.00 | 3.30 | 4.40 | 5.00 | 4.00 | 25 |
| 7 | Unstructured | **3.17** | 5.00 | 0.00 | 0.00 | 4.80 | 2.40 | 5.00 | 5.00 | 22 |
| 8 | Tesseract OCR | **3.12** | 4.90 | 0.00 | 0.00 | 4.70 | 2.40 | 4.90 | 5.00 | 144 |
| - | Docling | 0.00 (timeout) | - | - | - | - | - | - | - | 600 |

### big_workbook.xlsx  (Long documents)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | native Excel reader | **4.99** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 13 |
| 2 | MarkItDown | **4.82** | 4.80 | 4.70 | 4.70 | 5.00 | 4.80 | 4.80 | 19 |
| 3 | Docling | **4.58** | 5.00 | 5.00 | 5.00 | 2.50 | 5.00 | 5.00 | 41 |
| 4 | Unstructured | **4.56** | 5.00 | 4.90 | 5.00 | 2.50 | 5.00 | 5.00 | 18 |

### contract_45p.pdf  (Long documents, 46 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PyMuPDF4LLM | **4.99** | 5.00 | - | 5.00 | 4.90 | 5.00 | 5.00 | 22 |
| 2 | PyMuPDF (tied) | **4.90** | 5.00 | - | 5.00 | 4.50 | 5.00 | 5.00 | 14 |
| 3 | hybrid_pdf (tied) | **4.90** | 5.00 | - | 5.00 | 4.50 | 5.00 | 5.00 | 14 |
| 4 | Docling | **4.88** | 4.90 | - | 4.60 | 5.00 | 4.90 | 5.00 | 176 |
| 5 | OpenDataLoader | **4.79** | 4.90 | - | 4.60 | 4.60 | 4.90 | 5.00 | 11 |
| 6 | pdfplumber | **4.49** | 5.00 | - | 5.00 | 2.40 | 5.00 | 5.00 | 16 |
| 7 | MarkItDown | **4.49** | 5.00 | - | 5.00 | 2.40 | 5.00 | 5.00 | 14 |
| 8 | Tesseract OCR | **4.49** | 5.00 | - | 5.00 | 2.40 | 5.00 | 5.00 | 196 |
| 9 | Unstructured | **4.49** | 5.00 | - | 5.00 | 2.40 | 5.00 | 5.00 | 10 |

### handbook_40p.docx  (Long documents)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | native Word reader | **5.00** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5 |
| 2 | Unstructured (tied) | **5.00** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 6 |
| 3 | Docling (tied) | **5.00** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 14 |
| 4 | MarkItDown (tied) | **4.99** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 6 |

### scanned_report_30p.pdf  (Long documents, 31 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Docling | **4.58** | 4.50 | 4.70 | 4.80 | 4.50 | 4.50 | 4.50 | 387 |
| 2 | PyMuPDF4LLM | **3.67** | 3.90 | 2.50 | 4.10 | 3.60 | 3.70 | 4.20 | 138 |
| 3 | Unstructured | **3.02** | 4.10 | 0.00 | 1.10 | 4.40 | 3.50 | 5.00 | 160 |
| 4 | hybrid_pdf | **2.66** | 4.20 | 0.00 | 1.10 | 2.10 | 3.60 | 5.00 | 74 |
| 5 | Tesseract OCR | **2.66** | 4.20 | 0.00 | 1.10 | 2.10 | 3.60 | 5.00 | 124 |
| - | pdfplumber | 0.00 (empty) | - | - | - | - | - | - | 0 |
| - | PyMuPDF | 0.00 (empty) | - | - | - | - | - | - | 0 |
| - | MarkItDown | 0.00 (empty) | - | - | - | - | - | - | 0 |
| - | OpenDataLoader | 0.00 (empty) | - | - | - | - | - | - | 1 |

### transaction_ledger_100p.pdf  (Long documents, 100 pages)

| Rank | Parser | Score | Text | Table | Numbers | Structure | Complete | No extras | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | OpenDataLoader | **5.00** | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 | 13 |
| 2 | PyMuPDF4LLM (tied) | **4.99** | 5.00 | 4.90 | 5.00 | 5.00 | 5.00 | 5.00 | 62 |
| 3 | pdfplumber | **4.58** | 5.00 | 5.00 | 5.00 | 2.50 | 5.00 | 5.00 | 40 |
| 4 | MarkItDown | **3.60** | 5.00 | 0.00 | 5.00 | 1.60 | 5.00 | 5.00 | 47 |
| 5 | Unstructured | **3.60** | 5.00 | 0.00 | 5.00 | 1.60 | 5.00 | 5.00 | 55 |
| 6 | PyMuPDF | **3.01** | 2.60 | 2.70 | 2.60 | 3.40 | 5.00 | 1.70 | 294 |
| 7 | hybrid_pdf | **3.01** | 2.60 | 2.70 | 2.60 | 3.40 | 5.00 | 1.70 | 292 |
| 8 | Tesseract OCR | **2.10** | 2.50 | 0.00 | 2.60 | 1.30 | 1.80 | 4.40 | 160 |

