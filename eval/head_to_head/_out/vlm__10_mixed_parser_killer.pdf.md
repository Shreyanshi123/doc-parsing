# Cross-Industry Mixed Content Dossier

Synthetic document created for document-parsing evaluation.

## Section A - Executive memo

The review combines finance, operations, compliance, and technical evidence. The page uses headings, prose, a chart, and a caption. Repeated values test whether a parser duplicates content.

Figure: Weighted quality index line chart.

# Section B - Nested program table

| Program | Stream | Tasks | Complete | Open |
|---------|----------|-------|----------|------|
| Orion | Data | 12 | 9 | 3 |
| | Platform | 8 | 5 | 3 |
| | Controls | 6 | 6 | 0 |
| TOTAL | | 26 | 20 | 6 |

# Section C - Formula and code

*Weighted score: S = 0.40A + 0.35O + 0.25T*

```json
{
  "document_id": "MIX-2026-001",
  "language": "en",
  "pages": 4,
  "contains": ["tables", "charts", "image", "code", "rotated_text"]
}

# Section D - Two-column action register

| Priority actions | Ownership and dates |
|----------------------------------------------------|----------------------------|
| 1. Validate table reconstruction. | **Owner** | **Due** |
| 2. Review OCR exceptions. | Alpha | 30 Oct 2026 |
| 3. Confirm chart captions. | Beta | 5 Nov 2026 |
| | Gamma | 12 Nov 2026 |

# Section E - Image crop and rotated stamp

Figure: Bar chart showing revenue (USD M) for North, South, East, and West regions, with a rotated "CONTROLLED COPY 2026" stamp on the right.