"""The composed pieces: title cards, captions with attribution, lower thirds.

Each function turns a few strings into a :class:`~tituli.layout.Layout` placed
on a :class:`~tituli.frame.Frame`, applying the ink-and-scrim decision the frame's
knowledge allows. The pipeline order is fixed and matters: **shape/wrap →
measure → decide ink → cut the scrim to the measured block → compose**. A scrim
sized before the text is measured is how a three-line caption ends up hanging
off its own backdrop.

>>> from tituli.frame import Frame
>>> lay = title_card("The Apple", "a concrete poem", frame=Frame.blank((1920, 1080)))
>>> "".join(r.text for r in lay.runs)      # tracked styles set one run per glyph
'The Applea concrete poem'
>>> lay.meta["anchor"], lay.meta["ink"]
('center', 'background unknown: white on dark scrim')
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from tituli.color import (
    WCAG_NORMAL_MIN,
    WHITE,
    RGBA,
    contrast_from_luminance,
    ink_for,
    parse_color,
    with_alpha,
)
from tituli.frame import Frame
from tituli.geometry import Box
from tituli.layout import Layout, Plate, Run, block, fit_size, measure, wrap
from tituli.style import (
    ATTRIBUTION,
    CAPTION,
    KICKER,
    LOWER_THIRD_NAME,
    LOWER_THIRD_ROLE,
    NOTE_HEADLINE,
    NOTE_LINE,
    SUBTITLE,
    TITLE,
    TextStyle,
)

# Scrim tuning. Opacity is what a dark scrim needs to carry white text over
# white paper (the worst case a found-image film throws at it) — the corner
# falloff keeps it from dimming the whole frame on everything else.
SCRIM_DARK: RGBA = (6, 7, 10, 210)
SCRIM_LIGHT: RGBA = (250, 249, 246, 210)
_BUSY_STD = 0.12  # luminance stddev above which a patch is "busy"
_SCRIM_PAD_EM = 1.0  # full-strength margin around a block, in em of its largest face
_SCRIM_BLEED_EM = 9.0  # the falloff beyond that margin, in em
_GAP_EM = 0.55  # vertical gap between the parts of a card, in em
_TITLE_MAX_WIDTH = 0.8  # fraction of the safe box a title may span
_CAPTION_MAX_WIDTH = 0.55
_LOWER_THIRD_MAX_WIDTH = 0.6
_NOTE_MAX_WIDTH = 0.62
_NOTE_MAX_LINES = 4  # per line of the note, after wrapping
_ELLIPSIS = "…"
_ACCENT: RGBA = (214, 170, 94, 255)  # a warm gold, used only for the accent rule
_RULE_EM = (1.6, 0.09)  # accent rule length and thickness, in em of the title face


@dataclass(frozen=True)
class InkDecision:
    """What the frame told us to do about legibility."""

    ink: RGBA
    scrim: RGBA | None  # None = no scrim needed
    luminance: float | None
    reason: str


def decide_ink(frame: Frame, box: Box, *, preferred: RGBA | None = None) -> InkDecision:
    """Choose ink and whether a scrim is needed under ``box``.

    Rung (a) (nothing known): white on a dark scrim, the universal default.
    Rung (b)/(c): the ink with more contrast; a scrim only when contrast is still
    short of WCAG 4.5:1 or the patch is busy. ``preferred`` is honoured when it
    already has enough contrast.
    """
    stats = frame.luminance_stats(box)
    if stats is None:
        return InkDecision(WHITE, SCRIM_DARK, None, "background unknown: white on dark scrim")
    lum, std = stats
    if preferred is not None and contrast_from_luminance(preferred, lum) >= WCAG_NORMAL_MIN and std < _BUSY_STD:
        return InkDecision(preferred, None, lum, "preferred ink has enough contrast")
    ink = ink_for(luminance=lum)
    ok = contrast_from_luminance(ink, lum) >= WCAG_NORMAL_MIN
    if ok and std < _BUSY_STD:
        return InkDecision(ink, None, lum, "background contrast sufficient")
    scrim = SCRIM_DARK if ink == WHITE else SCRIM_LIGHT
    why = "busy background" if ok else "insufficient contrast"
    return InkDecision(ink, scrim, lum, f"{why}: scrim added")


def _scrim_plate(block_box: Box, frame: Frame, scrim: RGBA, *, em: float, anchor: str) -> Plate:
    """A 2-D corner (or edge) falloff cut to the block, bleeding away from it."""
    pad = em * _SCRIM_PAD_EM
    bleed = em * _SCRIM_BLEED_EM
    core = Box(block_box.x0 - pad, block_box.y0 - pad, block_box.x1 + pad, block_box.y1 + pad)
    horizontal = "left" in anchor or "right" in anchor
    vertical = "top" in anchor or "bottom" in anchor
    # The plate runs from the frame edge the block hugs, through the core, and
    # `bleed` further; `solid` is the core's share of that extent per axis.
    x0 = 0.0 if "left" in anchor else core.x0 - bleed
    x1 = float(frame.width) if "right" in anchor else core.x1 + bleed
    y0 = 0.0 if "top" in anchor else core.y0 - bleed
    y1 = float(frame.height) if "bottom" in anchor else core.y1 + bleed
    if not horizontal:
        x0, x1 = 0.0, float(frame.width)
    if not vertical:
        y0, y1 = core.y0 - bleed, core.y1 + bleed
    b = Box(x0, y0, x1, y1).intersection(frame.bounds)
    solid_x = (core.x1 if "left" in anchor else b.x1 - core.x0) / max(1.0, b.width)
    solid_y = (core.y1 if "top" in anchor else b.y1 - core.y0) / max(1.0, b.height)
    solid = (min(1.0, solid_x), min(1.0, solid_y))
    if horizontal and vertical:
        return Plate(b, scrim, f"corner-{anchor}", solid=solid)  # type: ignore[arg-type]
    if "bottom" in anchor:
        return Plate(b, scrim, "gradient-bottom", solid=solid)
    if "top" in anchor:
        return Plate(b, scrim, "gradient-top", solid=solid)
    return Plate(b, scrim, "box", radius=em * 0.3)


def truncate(text: str, style: TextStyle, frame_height: float, *, max_width: float, max_lines: int) -> str:
    """Wrap and hard-truncate with an ellipsis at ``max_lines`` lines.

    For text whose length you do not control (a licence template blob pasted
    into an artist field). The result always fits.
    """
    lines = wrap(text, style, frame_height, max_width=max_width)
    if len(lines) <= max_lines:
        return "\n".join(lines)
    kept = lines[:max_lines]
    last = kept[-1]
    while last and measure(last + _ELLIPSIS, style, frame_height) > max_width:
        last = last[:-1].rstrip()
    kept[-1] = last + _ELLIPSIS
    return "\n".join(kept)


def _stack(parts: Sequence[tuple[str, TextStyle]], frame: Frame, *, max_width: float, align: str | None = None) -> Layout:
    """Lay out several (text, style) blocks top-to-bottom with style-sized gaps."""
    y = 0.0
    out = Layout()
    for i, (text, style) in enumerate(parts):
        if not text:
            continue
        st = style.with_(align=align) if align else style
        lay = block(text, st, frame, max_width=max_width, y=y)
        out = out + lay
        y += len(text.split("\n")) * lay.meta["line_height"] + st.face(frame.height).size * _GAP_EM
    return out


def title_card(
    title: str,
    subtitle: str = "",
    *,
    frame: Frame,
    kicker: str = "",
    anchor: str = "center",
    title_style: TextStyle = TITLE,
    subtitle_style: TextStyle = SUBTITLE,
    kicker_style: TextStyle = KICKER,
    ink: RGBA | None = None,
    scrim: bool | None = None,
) -> Layout:
    """An opening card: optional kicker, title, optional subtitle.

    Fits the title to 80 % of the safe width (shrinking, never clipping), stacks
    the parts with a gap proportional to the type, places the block at
    ``anchor`` (subject-avoiding when the frame knows the picture), and picks
    ink by the frame's contrast. ``scrim`` forces a scrim on/off; None decides.
    """
    safe = frame.safe
    max_w = safe.width * _TITLE_MAX_WIDTH
    tstyle = fit_size(title, title_style, frame.height, max_width=max_w, max_height=safe.height * 0.6)
    parts = [(kicker, kicker_style), (title, tstyle), (subtitle, subtitle_style)]
    align = "center" if anchor in ("top", "center", "bottom") else ("left" if "left" in anchor else "right")
    lay = _stack(parts, frame, max_width=max_w, align=align)
    bb = lay.bbox()
    where, box = frame.place((bb.width, bb.height), anchor=anchor)
    lay = lay.moved_to(box)
    return _finish(lay, frame, where, ink=ink, scrim=scrim, em=tstyle.face(frame.height).size, preferred=parse_color(title_style.color))


def caption(
    text: str,
    attribution: str = "",
    *,
    frame: Frame,
    anchor: str | Sequence[str] = "auto",
    style: TextStyle = CAPTION,
    attribution_style: TextStyle = ATTRIBUTION,
    max_lines: int = 3,
    max_width: float = _CAPTION_MAX_WIDTH,
    ink: RGBA | None = None,
    scrim: bool | None = None,
    accent: bool = True,
) -> Layout:
    """A museum label over a picture: what is on screen, plus a tiny credit line.

    ``text`` is wrapped to ``max_width`` of the safe box and hard-truncated at
    ``max_lines``; ``attribution`` is set small and slightly transparent — present
    enough to credit, small enough not to compete. Placement avoids the
    frame's ``avoid`` boxes and its delivery target's reserved zones; the
    scrim is a 2-D corner falloff cut to the measured block.
    """
    safe = frame.safe
    max_w = safe.width * max_width
    body = truncate(text, style, frame.height, max_width=max_w, max_lines=max_lines)
    credit = truncate(attribution, attribution_style, frame.height, max_width=max_w, max_lines=1) if attribution else ""
    # Try the layout at each candidate anchor's alignment; alignment follows the side.
    lay = _stack([(body, style), (credit, attribution_style)], frame, max_width=max_w, align="left")
    bb = lay.bbox()
    where, box = frame.place((bb.width, bb.height), anchor=anchor)
    if "right" in where:
        lay = _stack([(body, style), (credit, attribution_style)], frame, max_width=max_w, align="right")
    elif where in ("top", "center", "bottom"):
        lay = _stack([(body, style), (credit, attribution_style)], frame, max_width=max_w, align="center")
    bb = lay.bbox()
    lay = lay.moved_to(box)
    em = style.face(frame.height).size
    out = _finish(lay, frame, where, ink=ink, scrim=scrim, em=em, preferred=parse_color(style.color))
    if accent:
        out = _with_accent_rule(out, em, where)
    return out


def lower_third(
    name: str,
    role: str = "",
    *,
    frame: Frame,
    anchor: str = "bottom-left",
    name_style: TextStyle = LOWER_THIRD_NAME,
    role_style: TextStyle = LOWER_THIRD_ROLE,
    ink: RGBA | None = None,
    scrim: bool | None = None,
) -> Layout:
    """Who is speaking: a name and a role, left-anchored, scrimmed if needed.

    Respects the frame's delivery zones — with ``delivery="youtube"`` the block
    moves above the subtitle band rather than into it.
    """
    max_w = frame.safe.width * _LOWER_THIRD_MAX_WIDTH
    name_t = truncate(name, name_style, frame.height, max_width=max_w, max_lines=1)
    role_t = truncate(role, role_style, frame.height, max_width=max_w, max_lines=1) if role else ""
    lay = _stack([(name_t, name_style), (role_t, role_style)], frame, max_width=max_w, align="left")
    bb = lay.bbox()
    where, box = frame.place((bb.width, bb.height), anchor=anchor)
    lay = lay.moved_to(box)
    em = name_style.face(frame.height).size
    out = _finish(lay, frame, where, ink=ink, scrim=scrim, em=em, preferred=parse_color(name_style.color))
    return _with_accent_rule(out, em, where)


def note(
    lines: Sequence[str] | str,
    *,
    frame: Frame,
    headline: str = "",
    anchor: str | Sequence[str] = "top-left",
    headline_style: TextStyle = NOTE_HEADLINE,
    line_style: TextStyle = NOTE_LINE,
    max_width: float = _NOTE_MAX_WIDTH,
    ink: RGBA | None = None,
    scrim: bool | None = None,
    accent: bool = True,
) -> Layout:
    """An editorial context card: an optional headline over equal-weight lines.

    The block for what the audio assumes and a cold viewer does not have
    ("what *Hamilton* is", "Philip died at 19"). Heavier than a caption —
    schedule it with a higher ``weight`` so the two never share a corner. Each
    line wraps to ``max_width`` of the safe box and is truncated at
    ``_NOTE_MAX_LINES`` rows; lines are laid out as written, so keep them short.
    """
    if isinstance(lines, str):
        lines = [l for l in lines.split("\n") if l.strip()]
    max_w = frame.safe.width * max_width
    body = [truncate(l, line_style, frame.height, max_width=max_w, max_lines=_NOTE_MAX_LINES) for l in lines]
    head = truncate(headline, headline_style, frame.height, max_width=max_w, max_lines=2) if headline else ""
    parts = [(head, headline_style)] + [(b, line_style) for b in body]
    align = "left"
    lay = _stack(parts, frame, max_width=max_w, align=align)
    bb = lay.bbox()
    where, box = frame.place((bb.width, bb.height), anchor=anchor)
    if "right" in where or where in ("top", "center", "bottom"):
        align = "right" if "right" in where else "center"
        lay = _stack(parts, frame, max_width=max_w, align=align)
    lay = lay.moved_to(box)
    em = (headline_style if head else line_style).face(frame.height).size
    out = _finish(lay, frame, where, ink=ink, scrim=scrim, em=em, preferred=parse_color(line_style.color))
    return _with_accent_rule(out, em, where) if accent else out


def _with_accent_rule(lay: Layout, em: float, anchor: str) -> Layout:
    bb = lay.bbox()
    length, thick = em * _RULE_EM[0], max(2.0, em * _RULE_EM[1])
    gap = em * 0.45
    if "right" in anchor:
        x0 = bb.x1 - length
    elif "left" in anchor:
        x0 = bb.x0
    else:
        x0 = (bb.x0 + bb.x1 - length) / 2
    rule = Plate(Box(x0, bb.y0 - gap - thick, x0 + length, bb.y0 - gap), _ACCENT, "box")
    return lay.with_plates(rule)


def _finish(
    lay: Layout,
    frame: Frame,
    anchor: str,
    *,
    ink: RGBA | None,
    scrim: bool | None,
    em: float,
    preferred: RGBA,
) -> Layout:
    """Apply the ink decision and, if needed, the scrim — after measuring."""
    bb = lay.bbox()
    decision = decide_ink(frame, bb, preferred=preferred)
    chosen = ink if ink is not None else decision.ink
    runs = tuple(
        Run(**{**r.__dict__, "color": with_alpha(chosen, r.color[3] / 255)}) for r in lay.runs
    )
    lay = Layout(runs, lay.plates, {**lay.meta, "ink": decision.reason, "anchor": anchor})
    want_scrim = decision.scrim is not None if scrim is None else scrim
    if want_scrim:
        color = decision.scrim or (SCRIM_DARK if chosen == WHITE else SCRIM_LIGHT)
        plate = _scrim_plate(bb, frame, color, em=em, anchor=anchor)
        lay = Layout(lay.runs, (plate,) + lay.plates, lay.meta)
    return lay


def intertitle(text: str, *, frame: Frame, style: TextStyle | None = None) -> Layout:
    """A silent-film style card: serif italic prose, centred on the frame."""
    from tituli.style import INTERTITLE

    st = style or INTERTITLE
    safe = frame.safe
    st = fit_size(text, st, frame.height, max_width=safe.width * 0.7, max_height=safe.height * 0.7)
    lay = block(text, st, frame, max_width=safe.width * 0.7)
    bb = lay.bbox()
    _, box = frame.place((bb.width, bb.height), anchor="center")
    lay = lay.moved_to(box)
    return _finish(lay, frame, "center", ink=None, scrim=None, em=st.face(frame.height).size, preferred=parse_color(st.color))


__all__ = [
    "InkDecision",
    "decide_ink",
    "truncate",
    "title_card",
    "caption",
    "lower_third",
    "note",
    "intertitle",
    "SCRIM_DARK",
    "SCRIM_LIGHT",
]
