"""Text styles and the tasteful presets.

A :class:`TextStyle` is resolution-independent: ``size`` is a **fraction of the
frame height** (``0.04`` is 43 px at 1080p, 86 px at 4K) so the same style reads
identically at any resolution. It is resolved to pixels by :meth:`TextStyle.face`
once a frame is known.

The presets encode the style research (see ``misc/docs/style.md``): sans-serif
working set, >= 36 px-equivalent at 1080p for anything meant to be read,
title-safe margins, tracked small caps for labels, generous leading.

>>> s = TITLE.with_(size=0.1)
>>> s.size, s.weight
(0.1, 700)
>>> s.px(1080)
108
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Literal, Sequence

from tituli import fonts
from tituli.color import NEAR_BLACK, WHITE, Color

Align = Literal["left", "center", "right"]
Case = Literal["as-is", "upper", "lower", "title"]

# Named weights so callers never write a magic number.
THIN, LIGHT, REGULAR, MEDIUM, SEMIBOLD, BOLD, BLACK_WEIGHT = 100, 300, 400, 500, 600, 700, 900

_DEFAULT_LEADING = 1.2
_MIN_FONT_PX = 8


@dataclass(frozen=True)
class TextStyle:
    """How a run of text looks. All fields keyword-only; build variants with ``with_``."""

    family: Sequence[str] = fonts.SANS_STACK
    size: float = 0.04  # fraction of frame height
    weight: int = REGULAR
    italic: bool = False
    condensed: bool = False
    color: Color = WHITE
    tracking: float = 0.0  # extra advance per glyph, in em
    leading: float = _DEFAULT_LEADING  # line height as a multiple of size
    case: Case = "as-is"
    align: Align = "center"
    opacity: float = 1.0

    def with_(self, **changes: Any) -> "TextStyle":
        """A copy with some fields replaced.

        >>> TextStyle().with_(weight=700).weight
        700
        """
        return replace(self, **changes)

    def px(self, frame_height: float) -> int:
        """Font size in pixels for a frame of that height."""
        return max(_MIN_FONT_PX, round(self.size * frame_height))

    def face(self, frame_height: float) -> fonts.Face:
        """The resolved, sized font for this style."""
        return fonts.resolve_face(
            self.family,
            size=self.px(frame_height),
            weight=self.weight,
            italic=self.italic,
            condensed=self.condensed,
        )

    def apply_case(self, text: str) -> str:
        if self.case == "upper":
            return text.upper()
        if self.case == "lower":
            return text.lower()
        if self.case == "title":
            return text.title()
        return text


# --- Presets --------------------------------------------------------------------
# Sizes are fractions of frame height. At 1080p: TITLE 81 px, SUBTITLE 35 px,
# CAPTION 43 px, ATTRIBUTION 22 px, credits names 35 px / roles 28 px.

TITLE = TextStyle(size=0.075, weight=BOLD, tracking=-0.01, leading=1.1)
SUBTITLE = TextStyle(size=0.032, weight=REGULAR, tracking=0.02, leading=1.3)
KICKER = TextStyle(size=0.022, weight=MEDIUM, tracking=0.18, case="upper")
INTERTITLE = TextStyle(
    family=fonts.SERIF_STACK, size=0.05, weight=REGULAR, italic=True, leading=1.35
)

CAPTION = TextStyle(size=0.04, weight=SEMIBOLD, leading=1.25, align="left")
NOTE_HEADLINE = TextStyle(size=0.055, weight=BOLD, leading=1.15, align="left")
NOTE_LINE = TextStyle(size=0.03, weight=REGULAR, leading=1.4, align="left", opacity=0.92)
ATTRIBUTION = TextStyle(size=0.02, weight=REGULAR, tracking=0.03, align="left", opacity=0.85)
LOWER_THIRD_NAME = TextStyle(size=0.042, weight=BOLD, align="left")
LOWER_THIRD_ROLE = TextStyle(size=0.026, weight=REGULAR, tracking=0.04, align="left", opacity=0.9)

CREDITS_HEADING = TextStyle(size=0.024, weight=MEDIUM, tracking=0.22, case="upper", opacity=0.75)
CREDITS_ROLE = TextStyle(size=0.026, weight=REGULAR, tracking=0.03, align="right", opacity=0.8)
CREDITS_NAME = TextStyle(size=0.032, weight=SEMIBOLD, align="left")
CREDITS_TITLE = TextStyle(size=0.06, weight=BOLD, tracking=-0.005)
CREDITS_LINE = TextStyle(size=0.03, weight=REGULAR, leading=1.4)

CALLIGRAM = TextStyle(
    family=fonts.SERIF_STACK, size=0.035, weight=REGULAR, color=NEAR_BLACK, align="left"
)
