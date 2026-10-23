# A Multimodal Benchmark for Layout-Aware

# Extraction

Synthetic document created for document-parsing evaluation.

# Abstract

This synthetic study evaluates text, table, equation, and figure extraction under controlled layout variation. The source contains Greek symbols, subscripts represented as text, citations, and compact quantitative statements.

# 1. Method

Precision P and recall R are combined using the harmonic mean:

# F1 = 2PR / (P + R)

A standardized measurement is calculated as z = (x - mu) / sigma, where mu is the sample mean and sigma is the sample standard deviation.

|Dataset|Pages|Precision|Recall|F1|
|---|---|---|---|---|
|A|1,250|0.94|0.91|0.925|
|B|900|0.89|0.87|0.880|
|C|650|0.85|0.79|0.819|

**Figure (page 1, line chart)**

Chart:
Title: Synthetic quality index across six reporting quarters
Axis labels:
- X-axis: Quarter (Q1 25, Q2 25, Q3 25, Q4 25, Q1 26, Q2 26)
- Y-axis: Index

| Quarter | Index |
|---------|-------|
| Q1 25 | ~42 |
| Q2 25 | ~58 |
| Q3 25 | ~53 |
| Q4 25 | ~67 |
| Q1 26 | ~74 |
| Q2 26 | ~82 |

# Figure 1. Synthetic quality index across six reporting quarters. References

[1] Example Author. Layout Evaluation Protocol. 2025. [2] Sample Research Group. Structured Extraction Tests. 2026.

Synthetic benchmark document - no real personal or commercial data Page 1