"""The 8-parameter scorecard (same parameters as the Azure IDP vs OpenDataLoader review).

score(truth, output) -> {metric: 0..1 or None}   (None = the answer key cannot test that metric)
Used by scripts/benchmark.py and by the UI's "Compare all parsers".
"""
from __future__ import annotations

import re
from collections import Counter

from app.compare import _headings, _list_f1, _table_cells, _tokens, similarity, word_f1

METRICS = ["Text Accuracy", "Table Reconstruction", "Chart Understanding", "Infographic Parsing",
           "Entity & Numeric Fidelity", "Structure", "Completeness", "Hallucination Penalty"]


def _rows_text(md: str) -> list[str]:
    """Output as flat lines; HTML table rows become 'a | b | c' so a row can be matched as a unit."""
    md = re.sub(r"</t[dh]>", " | ", md, flags=re.I)
    md = re.sub(r"</tr>|<br\s*/?>|</p>|</figcaption>", "\n", md, flags=re.I)
    md = re.sub(r"<[^>]+>", " ", md)
    return [re.sub(r"[*_`#]", "", l).lower() for l in md.splitlines() if l.strip()]


def _has(line: str, token: str) -> bool:
    return re.search(rf"(?<![\w.]){re.escape(token.lower())}(?![\w])", line) is not None


def chart_pairs(truth: str) -> list[tuple[str, str]]:
    """(label, value) rows from truth sections whose heading mentions 'chart'."""
    pairs, in_chart = [], False
    for l in truth.splitlines():
        if l.startswith("#"):
            in_chart = "chart" in l.lower() and "flow" not in l.lower()
        elif in_chart and l.startswith("|") and not re.fullmatch(r"[|\-:\s]+", l):
            c = [x.strip() for x in l.strip("|").split("|")]
            if len(c) == 2 and re.fullmatch(r"[\d.,]+", c[1]):
                pairs.append((c[0], c[1]))
    return pairs


def flow_edges(truth: str) -> list[tuple[str, str]]:
    edges = []
    for l in truth.splitlines():
        if "->" in l:
            p = [x.strip() for x in l.split("->")]
            edges += list(zip(p, p[1:]))
    return edges


def numbers(s: str) -> list[str]:
    return re.findall(r"\d[\d,]*\.?\d*", s.replace(",", ""))


def score(truth: str, out: str) -> dict[str, float | None]:
    """Each metric 0..1, or None when the answer key has nothing to test it with."""
    s: dict[str, float | None] = dict.fromkeys(METRICS)
    if not out.strip():  # nothing came back: 0 on every parameter the answer key can test, None on the rest
        tests = {"Text Accuracy": True, "Completeness": True, "Hallucination Penalty": True, "Structure": True,
                 "Table Reconstruction": bool(_table_cells(truth)), "Entity & Numeric Fidelity": bool(numbers(truth)),
                 "Chart Understanding": bool(chart_pairs(truth)), "Infographic Parsing": bool(flow_edges(truth))}
        return {m: (0.0 if tests[m] else None) for m in METRICS}
    tt, ot = Counter(_tokens(truth)), Counter(_tokens(out))
    overlap = sum((tt & ot).values())
    s["Text Accuracy"] = word_f1(truth, out)
    s["Completeness"] = overlap / max(sum(tt.values()), 1)
    s["Hallucination Penalty"] = overlap / max(sum(ot.values()), 1)
    if (tc := _table_cells(truth)):
        s["Table Reconstruction"] = _list_f1(tc, _table_cells(out))
    if (tn := numbers(truth)):
        s["Entity & Numeric Fidelity"] = _list_f1(tn, numbers(out))
    parts = [similarity(truth, out)]  # order-sensitive
    if (th := _headings(truth)):
        parts.append(_list_f1(th, _headings(out)))
    s["Structure"] = sum(parts) / len(parts)
    lines = _rows_text(out)
    if (pairs := chart_pairs(truth)):
        s["Chart Understanding"] = sum(any(_has(l, a) and _has(l, b) for l in lines) for a, b in pairs) / len(pairs)
    if (edges := flow_edges(truth)):
        nodes = {n for e in edges for n in e}
        blob = " ".join(lines)
        node_score = sum(n.lower() in blob for n in nodes) / len(nodes)
        edge_score = sum(any(a.lower() in l and b.lower() in l and ("->" in l or "→" in l) for l in lines)
                         for a, b in edges) / len(edges)
        s["Infographic Parsing"] = (node_score + edge_score) / 2
    return s
