# Smart Extract test report: different document types, with and without images

Date: 2026-10-22. Tested: the two Smart Extract modes ("By document" and "By part") on 19 files of different types.

## Short answer

- **Text, tables, mixed and scanned PDFs, Word, PowerPoint, Excel, CSV:** the parser choice works. "By document" and "By part" give the same score (differences of 0.02 or less, except one table-heavy report, see below).
- **Charts and diagrams:** the vision model clearly helps. On `chart_sample.pdf` chart understanding went from 0.0 to 4.5 out of 5 and diagrams from 2.5 to 5.0.
- **Pictures and photos (no charts):** "By document" picks smart_pdf (paid vision) too eagerly. On the web page with images the free parser scored higher (4.45 against 3.9), and every such file triggers paid vision calls. This needs a rule change (see "What to fix").
- **A real report with charts** (`Free alternatives to Azure Document Intelligence.pdf`): inconclusive. The vision model read only 3 of 9 figures, and the free parser found the same 5 of 8 chart values.

## How it was tested

- Each file was run in up to three ways:
  - **A:** By document, paid parsers allowed (so smart_pdf and the Azure OpenAI vision model can be used).
  - **B:** By part, paid parsers allowed.
  - **C:** By document, free parsers only (run only on files with images or charts).
- **Azure Document Intelligence was blocked** in this test, so no per-page cost was incurred. The vision model (Azure OpenAI) was on; it added 4 new vision calls (the cache grew from 62 to 66 entries). Each document is limited to 8 figures.
- **Scoring:** where an answer file exists, the same 8-parameter scorecard as in the earlier reports (average of the parameters the document can test, 0 to 5). Files without an answer file (tax sheet, the two Downloads PDFs, scan image) are compared by what they returned, not scored.

## Results (score 0 to 5, higher is better)

| Document | Type | A: By document | B: By part | C: Free only |
|---|---|---|---|---|
| AI agent, 3 pages | digital text | 5.0 (pymupdf) | 5.0 | |
| Generative AI, 6 pages | digital text, 6 pictures | 4.64 (smart_pdf) | 4.64 | |
| Digital with tables | tables | 5.0 (pymupdf4llm) | 5.0 | |
| Mixed text and scan | mixed | 5.0 (pymupdf4llm) | 5.0 | |
| AI agent, mixed | mixed | 4.88 (pymupdf4llm) | 4.9 | |
| Scanned, clean | scanned | 4.77 (pymupdf4llm) | 4.77 | |
| Scanned, noisy | scanned | 4.81 (pymupdf4llm) | 4.81 | |
| Chart sample | charts, flowchart, table | 3.48 (smart_pdf) | 3.55 | 2.67 (pymupdf4llm) |
| Web page with images | web page, 3 images | 3.9 (smart_pdf) | 3.9 | **4.45** (pymupdf) |
| AWS docs page | web page | 2.73 (smart_pdf) | 2.73 | |
| Benchmark report PDF | report, 11 tables | 4.36 (smart_pdf) | 4.53 | |
| Word report | docx | 5.0 (docx) | | |
| PowerPoint deck | pptx | 4.76 (pptx) | | |
| Excel sales | xlsx | 4.83 (spreadsheet) | | |
| CSV sales | csv | 5.0 (spreadsheet) | | |

Not scored (no answer file):

| Document | A: By document | B: By part | C: Free only |
|---|---|---|---|
| Tax computation sheet | smart_pdf, 830 words, 10 figures read | 993 words, 10 figures read | |
| Free alternatives (charts) | smart_pdf, 2,368 words, 3 of 9 figures read, 5/8 chart values | 2,385 words, 5/8 | 2,628 words, 5/8 |
| Parser Scorecard | pymupdf4llm, 333 words | 395 words | |
| Scan image (png) | easyocr, 26 words | | |

## What the results show

1. **Text, scans, mixed, Office files: no problem.** The recommended parser was chosen and the modes tie. The native parsers for Word, PowerPoint, Excel and CSV scored 4.76 to 5.0.

2. **Charts and diagrams: vision works.** On `chart_sample.pdf`:

   | Parameter | With vision (A) | Free only (C) |
   |---|---|---|
   | Chart understanding | 4.5 | 0.0 |
   | Diagrams | 5.0 | 2.5 |
   | Tables | 4.6 | 2.5 |
   | Overall | 3.48 | 2.67 |

   The overall score is held down because the vision model adds descriptive text that is not in the answer key (the "no-invent" parameter fell to 1.9 against 3.2).

3. **Pictures without charts: smart_pdf is chosen too often.** The rule "figures found, so use smart_pdf" fires on any picture, not only on charts. Evidence:
   - Web page with images: free pymupdf scored 4.45 and smart_pdf 3.9 (text accuracy 4.9 against 4.2, no-invent 4.9 against 3.7).
   - Benchmark report PDF: smart_pdf was chosen although the vision model read none of its figures, and scored 4.36 against 4.53 for By part.
   - Generative AI: six pictures triggered smart_pdf and six vision calls for the same score as By part.
   - Each such file uses paid vision calls.

4. **The real chart report is inconclusive.** The vision model read only 3 of the 9 figures it detected, and the free parser found the same 5 of 8 expected chart values. The test counts a value only if its label and number sit on the same line, which is crude. This document needs a hand-written answer file to judge fairly.

5. **The tax sheet (a form) was treated as having 11 figures** and 10 were read by the vision model. That looks like the figure detector mistaking boxes and lines for pictures. This was not verified by eye.

## What to fix (not done yet)

1. **Choose smart_pdf only when charts or diagrams are found**, not when there are only pictures or photos. For pictures, keep pymupdf4llm (or pymupdf for plain text).
2. **Check the figure detector on forms** such as the tax sheet, so boxes and lines are not counted as figures.
3. **Add a hand-written answer file** for the real chart report so charts in real documents can be scored.

## Limits of this test

- One run per file and mode. Differences under about 0.1 are noise.
- **Timings are not reliable.** The vision calls (first run, then cached) and a laptop that went to sleep distorted them. For example, `scan.png` shows 33,861 seconds, which is a clock artefact. Do not quote any times from this run.
- The answer files are the ones from the earlier reports; only `chart_sample.pdf` has real chart values.
- The browser page was not clicked through in this test; it was run through the same code the page uses.
