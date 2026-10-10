"""Layout combinators: several blocks composed into one :class:`Layout`.

``title_card`` and ``note`` each set one block. A page with a headline, a row of
glossed glyphs, a wrapped list and a footnote is several blocks — and composing
them by hand means measuring each ``bbox()``, translating, and compositing one
rendered image per block. These combinators take :class:`Layout`\\ s and return
one ``Layout``, so the page renders once and ``tituli.video.overlay`` can time
it like any other overlay.

* :func:`stack` — blocks top to bottom, aligned left/centre/right;
* :func:`grid` — blocks in uniform cells, row-major (one row by default);
* :func:`glossed` — the glossed-glyph row: big glyph over a small reading,
  centred per column (a grid of two-block stacks).

Gaps are fractions of frame **height**, like every size in tituli. A combinator
given a :class:`~tituli.frame.Frame` places its result with ``frame.place`` (so
the title-safe area and any delivery reservation bind); given a bare height, or
``anchor=None``, it leaves the result at the origin for an outer combinator to
place — nesting is the point.

>>> from tituli.frame import Frame
>>> from tituli.layout import block
>>> from tituli.style import TextStyle
>>> f = Frame.blank((1920, 1080))
>>> head = block("Heading", TextStyle(size=0.06), f)
>>> body = block("body text", TextStyle(size=0.03), f)
>>> page = stack([head, body], frame=f, gap=0.02)
>>> [r.text for r in page.runs]
['Heading', 'body text']
>>> b0, b1 = (r.bbox() for r in page.runs)
>>> round(b1.y0 - b0.y1) == round(0.02 * 1080)      # the gap, in frame height
True
"""

from __future__ import annotations

from dataclasses import replace
from typing import Literal, Sequence

from tituli.frame import Frame
from tituli.geometry import Box
from tituli.layout import Layout, block
from tituli.style import GLOSS, GLOSS_GLYPH, TextStyle

HAlign = Literal["left", "center", "right"]

DEFAULT_STACK_GAP = 0.02  # fraction of frame height between stacked blocks
DEFAULT_GRID_GAP = 0.03  # between grid cells, both axes
DEFAULT_GLOSS_GAP = 0.012  # between a glyph and its gloss
DEFAULT_GLOSS_COLUMN_GAP = 0.08  # between glossed columns


def _height(frame: Frame | float) -> float:
    return frame.height if isinstance(frame, Frame) else float(frame)


def _measurable(items: Sequence[Layout]) -> None:
    """Refuse a layout that has plates but no runs: it has no size to place by."""
    bad = [i for i, lay in enumerate(items) if lay.plates and not lay.runs]
    if bad:
        raise ValueError(
            f"items {bad} have plates but no runs, so they cannot be measured "
            "and would be left off the page; add the plate to a block with text "
            "(Layout.with_plates) instead"
        )


def _gaps(gap: float | Sequence[float], n: int) -> list[float]:
    """One gap per seam between ``n`` items (a scalar is repeated)."""
    if isinstance(gap, (int, float)):
        return [float(gap)] * max(0, n - 1)
    gaps = [float(g) for g in gap]
    if len(gaps) != max(0, n - 1):
        raise ValueError(
            f"gap has {len(gaps)} values for {n} items; give one per seam "
            f"({max(0, n - 1)}) or a single number"
        )
    return gaps


def _x_in(width: float, item_width: float, align: HAlign) -> float:
    if align == "left":
        return 0.0
    if align == "right":
        return width - item_width
    if align == "center":
        return (width - item_width) / 2
    raise ValueError(f"unknown align {align!r}; choose 'left', 'center' or 'right'")


def _placed(
    lay: Layout, frame: Frame | float, anchor: str | Sequence[str] | None
) -> Layout:
    """Move ``lay`` (its runs' bbox at the origin) to where ``frame`` puts it."""
    if anchor is None or not isinstance(frame, Frame) or not lay.runs:
        return lay
    bb = lay.bbox()
    where, box = frame.place((bb.width, bb.height), anchor=anchor)
    out = lay.moved_to(box)
    return replace(out, meta={**out.meta, "anchor": where, "box": box})


def _at_origin(lay: Layout) -> Layout:
    bb = lay.bbox()
    return lay.translated(-bb.x0, -bb.y0)


def stack(
    items: Sequence[Layout],
    *,
    frame: Frame | float,
    gap: float | Sequence[float] = DEFAULT_STACK_GAP,
    align: HAlign = "center",
    anchor: str | Sequence[str] | None = "center",
) -> Layout:
    """Blocks top to bottom, ``gap`` apart, aligned within the widest.

    ``gap`` is a fraction of frame height: one number for every seam, or one
    per seam (``len(items) - 1`` values) when the page needs a rhythm. A block
    with no runs is kept as a zero-height item, so per-seam gaps still line up.
    Plates travel with their block.

    >>> from tituli.layout import block
    >>> from tituli.style import TextStyle
    >>> a = block("wide line of text", TextStyle(size=0.05), 1080)
    >>> b = block("x", TextStyle(size=0.05), 1080)
    >>> s = stack([a, b], frame=1080, align="left")
    >>> s.runs[0].bbox().x0 == s.runs[1].bbox().x0
    True
    """
    _measurable(items)
    fh = _height(frame)
    gaps = _gaps(gap, len(items))
    width = max((lay.bbox().width for lay in items if lay.runs), default=0.0)
    out = Layout()
    y = 0.0
    for i, lay in enumerate(items):
        if lay.runs:
            bb = lay.bbox()
            x = _x_in(width, bb.width, align)
            out = out + _at_origin(lay).translated(x, y)
            y += bb.height
        if i < len(gaps):
            y += gaps[i] * fh
    out = replace(out, meta={**out.meta, "block_width": width})
    return _placed(out, frame, anchor)


def grid(
    items: Sequence[Layout],
    *,
    frame: Frame | float,
    columns: int | None = None,
    gap: float | tuple[float, float] = DEFAULT_GRID_GAP,
    align: HAlign = "center",
    anchor: str | Sequence[str] | None = "center",
) -> Layout:
    """Blocks in uniform cells, row-major; one row when ``columns`` is None.

    Every cell is as wide as the widest item (so a row of glyphs keeps one
    pitch whatever each glyph's advance), each row as tall as its tallest
    item; items are aligned ``align`` within their cell and to its top.
    ``gap`` is a fraction of frame height, or ``(column_gap, row_gap)``.

    >>> from tituli.layout import block
    >>> from tituli.style import TextStyle
    >>> cells = [block(t, TextStyle(size=0.05), 1080) for t in "a b c d".split()]
    >>> g = grid(cells, frame=1080, columns=2)
    >>> tops = [round(r.bbox().y0) for r in g.runs]
    >>> tops[0] == tops[1] < tops[2] == tops[3]      # two rows of two
    True
    """
    fh = _height(frame)
    n = len(items)
    if n == 0:
        return Layout()
    _measurable(items)
    cols = n if columns is None else int(columns)
    if cols < 1:
        raise ValueError(f"columns must be >= 1, got {columns!r}")
    col_gap, row_gap = (gap, gap) if isinstance(gap, (int, float)) else gap
    boxes = [lay.bbox() if lay.runs else Box(0, 0, 0, 0) for lay in items]
    cell_w = max(b.width for b in boxes)
    rows = [list(range(r, min(r + cols, n))) for r in range(0, n, cols)]
    out = Layout()
    y = 0.0
    for row in rows:
        row_h = max(boxes[i].height for i in row)
        for c, i in enumerate(row):
            if not items[i].runs:
                continue
            x = c * (cell_w + col_gap * fh) + _x_in(cell_w, boxes[i].width, align)
            out = out + _at_origin(items[i]).translated(x, y)
        y += row_h + row_gap * fh
    out = replace(
        out, meta={**out.meta, "cell_width": cell_w, "columns": cols, "rows": len(rows)}
    )
    return _placed(out, frame, anchor)


def glossed(
    pairs: Sequence[tuple[str, str]],
    *,
    frame: Frame | float,
    glyph: TextStyle = GLOSS_GLYPH,
    gloss: TextStyle = GLOSS,
    gap: float = DEFAULT_GLOSS_GAP,
    column_gap: float = DEFAULT_GLOSS_COLUMN_GAP,
    columns: int | None = None,
    anchor: str | Sequence[str] | None = "center",
) -> Layout:
    """A row of big glyphs, each with a small reading centred under it.

    ``pairs`` is ``[(glyph, gloss), ...]`` — ``[("カ", "ka"), ("ス", "su")]``.
    Columns share one pitch (the widest column), so readings line up under
    their glyphs and the row reads as a row. ``columns`` wraps a long row into
    several. Runs are tagged ``glyph:i`` / ``gloss:i`` (for staggered reveals).

    >>> lay = glossed([("カ", "ka"), ("ス", "su")], frame=1080)
    >>> [r.text for r in lay.runs]
    ['カ', 'ka', 'ス', 'su']
    >>> [r.tags for r in lay.runs][:2]
    [('glyph:0',), ('gloss:0',)]
    """
    fh = _height(frame)
    cells = [
        stack(
            [
                block(g, glyph, fh, tags=(f"glyph:{i}",)),
                block(r, gloss, fh, tags=(f"gloss:{i}",)),
            ],
            frame=fh,
            gap=gap,
            anchor=None,
        )
        for i, (g, r) in enumerate(pairs)
    ]
    return grid(
        cells,
        frame=frame,
        columns=columns,
        gap=(column_gap, DEFAULT_GRID_GAP),
        anchor=anchor,
    )


__all__ = ["stack", "grid", "glossed"]
