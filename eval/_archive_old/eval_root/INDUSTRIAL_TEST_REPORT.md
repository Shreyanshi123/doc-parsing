# Smart Extract on industrial-style documents

Date: 2026-10-22. 41 documents, 64 runs. Raw results: `eval/industrial/results.jsonl`. Documents and answer files: `eval/industrial/`. Generator: `scripts/make_industrial_corpus.py`. Runner: `scripts/run_industrial_suite.py`.

## Short answer

- **Clean business documents work well.** Invoices, purchase orders, bank statements, balance sheets, contracts, lab reports, datasheets, forms, two-column papers, resumes, Hindi and Chinese text, rotated pages and a 130-row table over several pages all scored 4.75 to 5.0 out of 5.
- **Photos and normal scans work.** A clean scanned invoice, a skewed and noisy scan, a receipt photo, an ID card, a screenshot and a handwriting-style note scored 4.3 to 5.0.
- **Three things clearly fail or mislead:** a low-quality scan (score 0.86 and 0.02), files that return nothing without saying so, and error handling for protected, corrupted and blank PDFs.
- **Vision on charts helps in one case and hurts in another:** chart report 3.18 without vision against 3.97 with it; slides 4.06 without vision against 3.52 with it.
- **Word and Excel lose formatting detail:** numbered lists, merged cells, heading levels, dates.
- **Unsupported formats are refused cleanly** with HTTP 415 and a clear message (json, xml, html, eml, old .doc and .xls).

## How it was tested

- 41 synthetic documents with a hand-written correct answer for each. Synthetic means the answer is exact, but the files are cleaner than real client files. Scans are simulated (skew, noise, blur, low resolution), and the "handwriting" is a handwriting-style font.
- Each PDF ran in By document mode with paid parsers allowed (A) and in By part mode (B). Two chart files also ran By document with free parsers only (C). Non-PDF files ran once.
- Azure Document Intelligence was blocked, so no per-page cost. The Azure OpenAI vision model was on, capped at 8 figures per document.
- Scores are the usual 8-parameter scorecard, averaged over the parameters each document can test, 0 to 5.
- Files the app should refuse were sent to the web API, so the real status codes are recorded.

## Results (score 0 to 5)

### Digital business documents

| Document | A: By document | B: By part | Parser used (A) |
|---|---|---|---|
| Invoice | 4.86 | 4.75 | pymupdf4llm |
| Purchase order | 5.0 | 5.0 | pymupdf4llm |
| Bank statement (70 rows) | 5.0 | 5.0 | pymupdf4llm |
| Balance sheet (negatives in brackets) | 5.0 | 5.0 | pymupdf4llm |
| Contract (numbered clauses) | 4.82 | 4.82 | pymupdf |
| Lab report | 4.88 | 4.88 | pymupdf4llm |
| Datasheet (units, symbols) | 5.0 | 4.81 | pymupdf4llm |
| Form with fields | 5.0 | 5.0 | pymupdf |
| Two-column paper | 4.99 | 4.71 | pymupdf4llm |
| Resume with sidebar | 4.82 | 4.82 | pymupdf |
| English, Hindi, Chinese text | 5.0 | 5.0 | pymupdf |
| Rotated pages (0, 90, 180) | 5.0 | 5.0 | pymupdf |
| 130-row table over several pages | 5.0 | 5.0 | pymupdf4llm |
| Long report (18 pages, 12,924 words) | not scored | not scored | pymupdf |

The long report ran fine, but its answer file only lists the headings, so a score would mean nothing.

### Charts and slides

| Document | A: with vision | B: By part | C: free only |
|---|---|---|---|
| Chart report (bar, pie, line charts) | 3.97 (smart_pdf) | 3.95 | 3.18 (pymupdf4llm) |
| Slides exported to PDF | 3.52 (smart_pdf) | 3.52 | 4.06 (pymupdf4llm) |

On the chart report, chart understanding went from 3.2 to 5.0 and tables from 2.1 to 4.6 with vision. On the slides, vision lowered the score because it added descriptive text that is not in the answer key (no-invent 2.4 against 3.3).

### Scans, photos and images

| Document | Score | Parser |
|---|---|---|
| Scanned invoice, clean | 4.86 | pymupdf4llm |
| Scanned invoice, skewed and noisy | 4.51 | pymupdf4llm |
| **Scanned invoice, low quality** | **0.86 (A), 0.02 (B)** | docling returned 1 word; easyocr returned 6 |
| Mixed (digital contract page + scanned invoice page) | 4.83 (A), 4.72 (B) | pymupdf4llm |
| Receipt photo | 4.3 | easyocr |
| ID card image | 5.0 | easyocr |
| Handwriting-style note | 4.69 | easyocr |
| Application screenshot | 4.7 | easyocr |
| Picture with no text | empty (expected) | none |

The mixed document first scored 3.44 because I wrote its answer file wrongly (it listed only the title and intro of the contract page). With the correct answer it scores 4.83.

### Word, PowerPoint, Excel, data and text

| Document | Score | Note |
|---|---|---|
| Word procedure | 4.51 | see "Formatting loss" below |
| PowerPoint (4 slides, with notes) | 4.93 | |
| Excel (3 sheets, merged cell, formulas, dates) | 3.85 | see "Formatting loss" below |
| CSV (300 rows, quoted commas, BOM) | 5.0 | |
| TSV | 5.0 | |
| .txt, .md, .log | 5.0 | |

### Files the app should refuse or handle carefully (web API)

| File | Result | Verdict |
|---|---|---|
| .json, .xml, .html, .eml | HTTP 415, "Unsupported file type" | Clean |
| Old .doc and .xls | HTTP 415, tells you to convert to docx or xlsx | Clean |
| Password-protected PDF | **HTTP 500**, "ValueError: document closed or encrypted" | Not clean: should be a 4xx saying the PDF needs a password |
| Corrupted PDF (truncated) | **HTTP 200**, empty result, 100 seconds | Should fail fast with an error |
| Blank PDF | **HTTP 200**, 2 words, read by the vlm parser | A blank page was sent to a vision model; it should return empty |

## What went wrong, in order of importance

1. **Near-empty results count as success.** On the low-quality scan, pymupdf4llm returned nothing, docling returned 1 word, and that was accepted, so the OCR parser was never tried. In By part mode, easyocr returned 6 words. Neither mode warned the user. The same silence applies to the picture with no text.
2. **Error handling:** protected PDFs give HTTP 500, corrupted PDFs take 100 seconds and return an empty success, and a blank PDF reaches a vision model.
3. **Vision is not always an improvement.** It helped on the chart report and hurt on the slides. The "figures found, so use smart_pdf" rule cannot tell the two cases apart.
4. **Word files:** numbered lists all come out as "1.", a merged cell repeats in every column it spans, and the Title and Heading 1 both become "#".
5. **Excel files:** dates come out as `2026-01-05 00:00:00` instead of the displayed format, numbers as `1038.0`, and the merged title row is treated as the table header. Formula results are correct.

## Suggested fixes (none made yet)

1. Treat a result with very few words as a failure and continue down the chain. Show a warning when the final result is empty or near-empty.
2. Return a clear 4xx for protected PDFs, fail fast on corrupted PDFs, and do not send blank pages to a vision model.
3. Use smart_pdf only for charts and diagrams, not for every picture.
4. Fix the Word numbering, merged cells and heading levels, and keep Excel date formats.
5. Try preprocessing (deskew, denoise, upscale) before OCR on low-quality scans, and test whether it helps.

## Limits of this test

- All documents are synthetic and cleaner than most real client files. Handwriting is simulated with a font and real handwriting was not tested.
- One run per file and mode. Differences under about 0.1 are noise.
- The answer files were written by hand by me. Two were wrong at first (the mixed document and the long report) and are handled as described above.
- **Timings are not usable.** Each run started a fresh process that loaded the models, and the disk was 99% full (4 GB free of 476 GB), which caused one run to fail with "No space left on device" (it passed when re-run).
- Not tested: Azure Document Intelligence, the "Prefer quality" path (docling first), documents of 100 pages or more, real client files, and the web page in a browser.
