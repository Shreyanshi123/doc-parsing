# Parser scorecard (0-5 per metric, total /40)

Run fresh on every PDF in eval/ that has an answer key. '-' = no document tested that metric.

## Overall

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s |
|---|---|---|---|---|---|---|---|---|---|---|
| **azure_di** | 4.3 | 4.2 | 0.0 | 2.5 | 4.0 | 4.3 | 4.8 | 4.1 | **28.2** | 10.5 |

## digital  (1 docs: AI_agent_p1-3.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s |
|---|---|---|---|---|---|---|---|---|---|---|
| **azure_di** | 5.0 | - | - | - | 4.9 | 4.9 | 5.0 | 4.9 | **24.7** | 9.7 |

## digital + charts/images  (5 docs: Generative_AI_p1-6.pdf, Overview of Amazon Web Services - Overview of Amazon Web Services.pdf, PIB_home_p1-6.pdf, SOP  Income Tax Computation Sheet-2026-27.pdf, chart_sample.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s |
|---|---|---|---|---|---|---|---|---|---|---|
| **azure_di** | 3.4 | 2.5 | 0.0 | 2.5 | 2.8 | 3.3 | 4.6 | 2.9 | **22.0** | 11.2 |

## digital + tables  (1 docs: digital.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s |
|---|---|---|---|---|---|---|---|---|---|---|
| **azure_di** | 5.0 | 5.0 | - | - | 5.0 | 5.0 | 5.0 | 5.0 | **30.0** | 6.9 |

## mixed  (2 docs: AI_agent_mixed.pdf, mixed.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s |
|---|---|---|---|---|---|---|---|---|---|---|
| **azure_di** | 5.0 | 5.0 | - | - | 5.0 | 4.9 | 5.0 | 5.0 | **29.8** | 11.9 |

## scanned  (3 docs: AI_agent_scanned_clean.pdf, AI_agent_scanned_noisy.pdf, scanned.pdf)

| parser | Text Accuracy | Table Reconstruction | Chart Understanding | Infographic Parsing | Entity & Numeric Fidelity | Structure | Completeness | Hallucination Penalty | **Total /40** | avg s |
|---|---|---|---|---|---|---|---|---|---|---|
| **azure_di** | 5.0 | - | - | - | 4.9 | 5.0 | 5.0 | 5.0 | **24.9** | 9.8 |