INDUSTRY DOCUMENT PARSING BENCHMARK

This package contains 10 synthetic PDFs and one ground-truth TXT file for each PDF.

01 Corporate annual report: prose, KPI cards, charts, risk tables, footnotes.
02 Invoice and purchase order: identifiers, line items, currency, tax, totals.
03 Legal contract: clauses, cross-references, SLA table, signatures.
04 Scientific paper: equations, citations, metrics, chart.
05 Healthcare discharge summary: clinical-style fields, observations, medications.
06 Insurance claim form: form layout, checklist, amounts, declaration.
07 Logistics shipping manifest: identifiers, package table, rotated handling label.
08 Software incident report: timeline, percentages, logs, code-like text.
09 Scanned maintenance order: raster-only page with skew, blur, and noise for OCR.
10 Mixed parser killer: charts, nested table, formula, JSON, columns, rotated stamp.

USAGE
1. Upload one PDF to the parser comparison UI.
2. Paste the matching *_ground_truth.txt content into Reference text for scoring.
3. Run all parsers using the same options.
4. Compare text similarity separately from layout, table, figure, OCR, and metadata quality.

All organizations, people, IDs, amounts, addresses, clinical details, and events are fictional.
