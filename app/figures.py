"""
Finds charts / diagrams / pictures on a digital PDF page and cuts them out as PNG.

Two kinds of figure are looked for (PyMuPDF only, no extra packages):
  - raster : a picture embedded in the PDF          (page.get_image_info)
  - vector : a chart drawn with lines and shapes    (page.cluster_drawings)
Table areas, page-sized backgrounds, tiny icons and thin banners are ignored.
"""
from __future__ import annotations

MIN_W, MIN_H = 90.0, 70.0          # points (1 pt = 1/72 inch): smaller = icon / logo
MIN_AREA_FRAC = 0.015              # of the page area
MAX_AREA_FRAC = 0.90               # bigger = page background / scan
MAX_ASPECT = 8.0                   # wider/taller than this = banner or rule
MIN_VECTOR_PATHS = 6               # a drawn chart / flowchart has several paths; a rule or one button does not
MERGE_GAP = 6.0                    # join figure parts that are closer than this
CROP_DPI = 150
MAX_SIDE_PX = 1600                 # keeps the image (and the vision bill) small


def _inside(r, outer, frac=0.5) -> bool:
    inter = r & outer
    return (not inter.is_empty) and (inter.width * inter.height) >= frac * (r.width * r.height)


def _merge(items):
    """items: [(Rect, kind)] -> [(Rect, {kinds})]; parts that touch or lie within MERGE_GAP become one figure."""
    import pymupdf

    groups = [[pymupdf.Rect(r), {k}] for r, k in items]
    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                a, b = groups[i][0], groups[j][0]
                grown = pymupdf.Rect(a.x0 - MERGE_GAP, a.y0 - MERGE_GAP, a.x1 + MERGE_GAP, a.y1 + MERGE_GAP)
                if not (grown & b).is_empty:
                    groups[i] = [a | b, groups[i][1] | groups[j][1]]
                    del groups[j]
                    changed = True
                    break
            if changed:
                break
    return [(r, kinds) for r, kinds in groups]


def find_figures(page, table_rects=(), ignore_xrefs=frozenset()):
    """Return [(rect, kinds)] for the figures on this page, top to bottom. kinds is a set of 'raster' / 'vector'."""
    import pymupdf

    page_rect = page.rect
    area = page_rect.width * page_rect.height
    found = []   # (rect, kind)

    for info in page.get_image_info(xrefs=True):
        if info.get("xref") in ignore_xrefs:
            continue     # the same picture on many pages = logo / page decoration
        found.append((pymupdf.Rect(info["bbox"]), "raster"))

    try:
        clusters = list(page.cluster_drawings())
    except Exception:
        clusters = []
    if clusters:
        paths = [d["rect"] for d in page.get_drawings()]
        for c in clusters:
            c = pymupdf.Rect(c)
            # count by centre point: a straight line has a zero-height rectangle and would otherwise not count
            n = sum(1 for p in paths if c.x0 - 1 <= (p.x0 + p.x1) / 2 <= c.x1 + 1 and c.y0 - 1 <= (p.y0 + p.y1) / 2 <= c.y1 + 1)
            if n >= MIN_VECTOR_PATHS:
                found.append((c, "vector"))

    keep = []
    for r, kind in found:
        r = r & page_rect
        if r.is_empty or r.width < MIN_W or r.height < MIN_H:
            continue
        a = r.width * r.height
        if a < MIN_AREA_FRAC * area or a > MAX_AREA_FRAC * area:
            continue
        if max(r.width / r.height, r.height / r.width) > MAX_ASPECT:
            continue
        if any(_inside(r, pymupdf.Rect(t)) for t in table_rects):
            continue
        keep.append((r, kind))

    merged = [(r, k) for r, k in _merge(keep) if r.width >= MIN_W and r.height >= MIN_H]
    return sorted(merged, key=lambda rk: (rk[0].y0, rk[0].x0))


def crop_png(page, rect) -> bytes:
    """Render just this rectangle of the page to a PNG (long side capped at MAX_SIDE_PX)."""
    longest_pt = max(rect.width, rect.height)
    dpi = min(CROP_DPI, MAX_SIDE_PX / longest_pt * 72) if longest_pt else CROP_DPI
    return page.get_pixmap(clip=rect, dpi=int(max(dpi, 40))).tobytes("png")


def padded(page, rect, left=14.0, top=28.0, right=14.0, bottom=24.0):
    """The drawn part of a chart is smaller than the chart: its title and axis labels sit just outside it."""
    import pymupdf

    return pymupdf.Rect(rect.x0 - left, rect.y0 - top, rect.x1 + right, rect.y1 + bottom) & page.rect


MIN_TABLE_FILL = 0.2   # a detected "table" with fewer filled cells than this is a chart's grid lines, not a table


def table_fill(table) -> float:
    """Share of cells that hold text. A real table is mostly filled; a chart's grid lines give an almost empty grid."""
    try:
        cells = [c for row in table.extract() for c in row]
        return sum(1 for c in cells if c and str(c).strip()) / len(cells) if cells else 1.0
    except Exception:
        return 1.0
