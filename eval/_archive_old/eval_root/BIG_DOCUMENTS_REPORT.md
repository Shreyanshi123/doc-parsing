# Large-document test: Llama 2 paper and UN SDG Report 2024

## Result

**pymupdf4llm is the closest free parser to Azure DI on both large documents, and it needs about 3 seconds per page.** Docling is second on quality but was the slowest by a wide margin. Closeness to Azure DI is not the same as correctness: these two PDFs have no hand-written answer key, so Azure DI's own output is the yardstick.

| Document | Pages | What it contains | Source |
|---|---|---|---|
| Llama 2 paper | 77 | Many charts, tables and equations (36 figures found) | arxiv.org/pdf/2307.09288 |
| UN SDG Report 2024 | 51 | Infographics and charts (71 figures found) | unstats.un.org SDG Report 2024 PDF |

## Overall, both documents together (128 pages)

Total out of 40 against Azure DI's output. Charts, Diagrams and Tables are not counted here: Azure DI does not read chart values, and these two PDFs held few tables.

| Rank | Parser | Total /40 | Seconds per page |
|---|---|---|---|
| 1 | **pymupdf4llm** | 26.6 | 2.9 |
| 2 | **docling** | 24.9 | 6.5 (UN report only, see note) |
| 3 | **hybrid_pdf** (our combo: PyMuPDF + Tesseract) | 24.4 | 1.1 |
| 3 | **pymupdf** | 24.4 | 1.7 |
| 5 | **smart_pdf** (our combo: PyMuPDF + Tesseract + vision model) | 24.2 | 2.8 |
| 6 | **markitdown** | 18.4 | 1.1 |
| 7 | **pdfplumber** | 16.7 | 1.1 |
| 8 | **opendataloader** | 11.7 | 0.5 (Java ran out of memory on the UN report) |
| ref | **azure_di** | reference | 0.7 |

## Per document

Average score = mean of the parameters that apply, 0 to 1, against Azure DI's output. Time is the whole document.

### Llama 2 paper (77 pages)

| Parser | Seconds | Seconds per page | Average score |
|---|---|---|---|
| azure_di (reference) | 58.5 | 0.8 | reference |
| pymupdf4llm | 303.3 | 3.9 | 0.82 |
| docling | not valid (see note) | not valid | 0.79 |
| hybrid_pdf | 119.0 | 1.5 | 0.71 |
| pymupdf | 191.8 | 2.5 | 0.71 |
| smart_pdf | 250.0 | 3.2 | 0.70 |
| opendataloader | 21.9 | 0.3 | 0.67 |
| markitdown | 85.3 | 1.1 | 0.44 |
| pdfplumber | 86.0 | 1.1 | 0.37 |

### UN SDG Report 2024 (51 pages)

| Parser | Seconds | Seconds per page | Average score |
|---|---|---|---|
| azure_di (reference) | 27.5 | 0.5 | reference |
| pymupdf4llm | 66.1 | 1.3 | 0.70 |
| hybrid_pdf | 23.5 | 0.5 | 0.69 |
| pymupdf | 31.7 | 0.6 | 0.69 |
| smart_pdf | 102.6 | 2.0 | 0.68 |
| docling | 329.1 | 6.5 | 0.64 |
| markitdown | 50.9 | 1.0 | 0.61 |
| pdfplumber | 57.8 | 1.1 | 0.58 |
| opendataloader | 41.4 | 0.8 | 0.00 (failed: Java ran out of memory) |

## Notes

- **Docling on Llama 2:** the recorded time of 29,887 seconds (8 hours) is wrong. The laptop went to sleep during that run. The score (0.79) is valid, the time is discarded. On the UN report Docling took 329 seconds, 6.5 seconds per page, which is 5 times pymupdf4llm on the same file.
- **OpenDataLoader on the UN report:** the Java process ran out of memory and returned nothing. That is a system limit, not a quality score, but it shows the tool can fail on large inputs without more memory.
- **Figures were only partly read.** smart_pdf reads at most 8 figures per document by default (a cost cap), so of the 107 figures in these two PDFs it read 16. Its chart-reading ability is therefore not tested here; see the main report for the chart test.
- **No answer key.** A parser that copies Azure DI's mistakes scores well here. These results show which parsers behave like Azure DI and how long they take, not which are correct.
- **Cost of this run:** Azure DI was called once per document (128 pages) and the vision model for at most 16 figures. Timings come from one Windows laptop with no GPU.
