"""Colours, WCAG contrast, and the ink-for-this-background decision.

Everything here is pure arithmetic on ``(r, g, b[, a])`` tuples in 0–255, so it
costs nothing to import and is easy to test.

>>> contrast_ratio((255, 255, 255), (0, 0, 0))
21.0
>>> ink_for(luminance=0.9)   # light background -> dark ink
(17, 17, 17)
>>> ink_for(luminance=0.1)   # dark background -> light ink
(255, 255, 255)
"""

from __future__ import annotations

from typing import Sequence, Union

RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]
Color = Union[RGB, RGBA, str]

WHITE: RGB = (255, 255, 255)
BLACK: RGB = (0, 0, 0)
NEAR_BLACK: RGB = (17, 17, 17)  # #111 — reads as black without the harshness
OFF_WHITE: RGB = (245, 245, 243)  # a warm paper white for solid title cards
CREDITS_BLACK: RGB = (8, 8, 10)

# WCAG 2.x thresholds (AA): 4.5:1 for normal text, 3:1 for large text
WCAG_NORMAL_MIN = 4.5
WCAG_LARGE_MIN = 3.0
# "Large" text per WCAG is >= 18pt regular or >= 14pt bold; on a 1080p canvas
# every tituli default is well above that, so 3:1 is the operative floor and
# 4.5:1 is what we *aim* for.

_SRGB_THRESHOLD = 0.03928
_SRGB_LINEAR_DIVISOR = 12.92
_SRGB_GAMMA = 2.4
_SRGB_OFFSET = 0.055
_SRGB_SCALE = 1.055
_LUMA_R, _LUMA_G, _LUMA_B = 0.2126, 0.7152, 0.0722
_CONTRAST_OFFSET = 0.05


def parse_color(color: Color) -> RGBA:
    """Accept ``"#rgb"``, ``"#rrggbb"``, ``"#rrggbbaa"``, a Pillow name or a tuple.

    >>> parse_color("#fff")
    (255, 255, 255, 255)
    >>> parse_color((10, 20, 30))
    (10, 20, 30, 255)
    """
    if isinstance(color, str):
        s = color.strip()
        if s.startswith("#"):
            h = s[1:]
            if len(h) in (3, 4):
                h = "".join(c * 2 for c in h)
            if len(h) == 6:
                h += "ff"
            if len(h) != 8:
                raise ValueError(f"bad hex colour: {color!r}")
            return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4, 6))  # type: ignore[return-value]
        from PIL import ImageColor

        return ImageColor.getcolor(s, "RGBA")  # type: ignore[return-value]
    t = tuple(int(c) for c in color)
    if len(t) == 3:
        return (*t, 255)  # type: ignore[return-value]
    if len(t) == 4:
        return t  # type: ignore[return-value]
    raise ValueError(f"bad colour tuple: {color!r}")


def _channel(c: int) -> float:
    v = c / 255.0
    if v <= _SRGB_THRESHOLD:
        return v / _SRGB_LINEAR_DIVISOR
    return ((v + _SRGB_OFFSET) / _SRGB_SCALE) ** _SRGB_GAMMA


def relative_luminance(color: Color) -> float:
    """WCAG relative luminance in 0..1.

    >>> round(relative_luminance((255, 255, 255)), 3)
    1.0
    >>> relative_luminance((0, 0, 0))
    0.0
    """
    r, g, b, _ = parse_color(color)
    return _LUMA_R * _channel(r) + _LUMA_G * _channel(g) + _LUMA_B * _channel(b)


def contrast_ratio(a: Color, b: Color) -> float:
    """WCAG contrast ratio between two colours (1..21).

    >>> round(contrast_ratio("#777", "#fff"), 2)
    4.48
    """
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + _CONTRAST_OFFSET) / (lo + _CONTRAST_OFFSET), 4)


def contrast_from_luminance(ink: Color, luminance: float) -> float:
    """Contrast of ``ink`` over a background of known relative luminance."""
    li = relative_luminance(ink)
    hi, lo = max(li, luminance), min(li, luminance)
    return (hi + _CONTRAST_OFFSET) / (lo + _CONTRAST_OFFSET)


def ink_for(
    *,
    luminance: float,
    light: RGB = WHITE,
    dark: RGB = NEAR_BLACK,
) -> RGB:
    """Pick the ink (light or dark) with more contrast against ``luminance``."""
    if contrast_from_luminance(light, luminance) >= contrast_from_luminance(
        dark, luminance
    ):
        return light
    return dark


def needs_scrim(
    ink: Color, luminance: float, *, minimum: float = WCAG_NORMAL_MIN
) -> bool:
    """Whether ``ink`` over that background falls short of ``minimum`` contrast.

    >>> needs_scrim((255, 255, 255), luminance=0.5)
    True
    >>> needs_scrim((255, 255, 255), luminance=0.02)
    False
    """
    return contrast_from_luminance(ink, luminance) < minimum


def mix(a: Color, b: Color, t: float) -> RGBA:
    """Linear blend, ``t=0`` -> ``a``, ``t=1`` -> ``b``."""
    pa, pb = parse_color(a), parse_color(b)
    return tuple(round(x + (y - x) * t) for x, y in zip(pa, pb))  # type: ignore[return-value]


def with_alpha(color: Color, alpha: float) -> RGBA:
    """Same colour with opacity ``alpha`` in 0..1.

    >>> with_alpha("#000", 0.5)
    (0, 0, 0, 128)
    """
    r, g, b, _ = parse_color(color)
    return (r, g, b, round(255 * alpha))


def mean_luminance(pixels: Sequence[RGB]) -> float:
    """Mean relative luminance of a pixel sample."""
    if not pixels:
        return 0.0
    return sum(relative_luminance(p) for p in pixels) / len(pixels)
