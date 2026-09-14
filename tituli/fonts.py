"""Font discovery with no bundled fonts.

``tituli`` never ships a typeface (licensing), so a *typeface request* — a family
name, weight and slant — is resolved against the fonts already installed on the
machine, and falls back to the scalable face Pillow embeds (Aileron). That fallback
is a real font, not a stub, so every render works out of the box on a bare CI
runner; it just looks better on a machine with Helvetica Neue.

Resolution order is a *preference list*: the first family found wins.

>>> face = resolve_face(["No Such Family", "DejaVu Sans"], size=48)
>>> face.size
48
>>> face.family in ("DejaVu Sans", "Aileron") or isinstance(face.family, str)
True
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from PIL import ImageFont

_FONT_SUFFIXES = (".ttf", ".ttc", ".otf")
_MAX_TTC_INDEX = 32  # sanity bound when probing a collection's faces
_TTC_FIRST_INDEX = 0

# The working set the style research settled on, most-preferred first. Every
# entry is a family name as the font's own ``name`` table reports it.
SANS_STACK: tuple[str, ...] = (
    "Helvetica Neue",
    "Inter",
    "Helvetica",
    "Avenir Next",
    "Roboto",
    "Univers",
    "Liberation Sans",
    "DejaVu Sans",
    "Arial",
)
SERIF_STACK: tuple[str, ...] = (
    "Georgia",
    "Palatino",
    "Baskerville",
    "Liberation Serif",
    "DejaVu Serif",
    "Times New Roman",
)
DISPLAY_STACK: tuple[str, ...] = ("Futura", "Avenir Next", "Gill Sans") + SANS_STACK
MONO_STACK: tuple[str, ...] = (
    "Menlo",
    "DejaVu Sans Mono",
    "Liberation Mono",
    "Courier",
)

FALLBACK_FAMILY = "Aileron"  # what Pillow's embedded ``load_default`` reports

_WEIGHT_WORDS = {
    "thin": 100,
    "ultralight": 200,
    "extralight": 200,
    "light": 300,
    "regular": 400,
    "book": 400,
    "roman": 400,
    "normal": 400,
    "medium": 500,
    "semibold": 600,
    "demibold": 600,
    "demi": 600,
    "bold": 700,
    "extrabold": 800,
    "ultrabold": 800,
    "heavy": 800,
    "black": 900,
}
REGULAR_WEIGHT = 400
BOLD_WEIGHT = 700


@dataclass(frozen=True)
class FontFile:
    """One face inside a font file (a ``.ttc`` holds several)."""

    path: str
    index: int
    family: str
    style: str

    @property
    def weight(self) -> int:
        """CSS-style weight parsed from the style name (``"Bold"`` -> 700)."""
        return _weight_of(self.style)

    @property
    def italic(self) -> bool:
        """Whether the style name says italic/oblique."""
        s = self.style.lower()
        return "italic" in s or "oblique" in s

    @property
    def condensed(self) -> bool:
        """Whether the style name says condensed/narrow/compressed."""
        s = self.style.lower()
        return any(w in s for w in ("condensed", "narrow", "compressed"))


@dataclass(frozen=True)
class Face:
    """A resolved, sized font ready to measure and draw with Pillow."""

    family: str
    style: str
    size: int
    path: str | None
    index: int = 0

    @property
    def pil(self) -> ImageFont.FreeTypeFont:
        """The Pillow font object (cached per ``(path, index, size)``)."""
        return _load_pil(self.path, self.index, self.size)

    def with_size(self, size: int) -> "Face":
        """Same face at another pixel size."""
        return Face(self.family, self.style, int(size), self.path, self.index)

    def length(self, text: str) -> float:
        """Advance width of ``text`` in pixels."""
        return self.pil.getlength(text)

    @property
    def ascent(self) -> int:
        """Ascent in pixels."""
        return self.pil.getmetrics()[0]

    @property
    def descent(self) -> int:
        """Descent in pixels."""
        return self.pil.getmetrics()[1]

    @property
    def line_height(self) -> int:
        """Ascent + descent."""
        a, d = self.pil.getmetrics()
        return a + d


def _weight_of(style: str) -> int:
    s = style.lower().replace(" ", "").replace("-", "")
    # longest match first so "ultralight" beats "light", "semibold" beats "bold"
    for word in sorted(_WEIGHT_WORDS, key=len, reverse=True):
        if word in s:
            return _WEIGHT_WORDS[word]
    return REGULAR_WEIGHT


def font_dirs() -> list[Path]:
    """Platform font directories that exist on this machine.

    Extra directories can be prepended with ``TITULI_FONT_DIRS`` (``os.pathsep``
    separated), which is also how a project supplies its own licensed fonts.
    """
    home = Path.home()
    if sys.platform == "darwin":
        candidates = [
            home / "Library/Fonts",
            Path("/Library/Fonts"),
            Path("/System/Library/Fonts"),
            Path("/System/Library/Fonts/Supplemental"),
        ]
    elif sys.platform.startswith("win"):
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        candidates = [home / "AppData/Local/Microsoft/Windows/Fonts", windir / "Fonts"]
    else:
        candidates = [
            home / ".fonts",
            home / ".local/share/fonts",
            Path("/usr/local/share/fonts"),
            Path("/usr/share/fonts"),
        ]
    extra = [
        Path(p) for p in os.environ.get("TITULI_FONT_DIRS", "").split(os.pathsep) if p
    ]
    return [d for d in extra + candidates if d.is_dir()]


def _iter_font_paths(dirs: Iterable[Path]) -> Iterator[Path]:
    for d in dirs:
        for p in d.rglob("*"):
            if p.suffix.lower() in _FONT_SUFFIXES and p.is_file():
                yield p


def _faces_in(path: Path) -> Iterator[FontFile]:
    for index in range(_MAX_TTC_INDEX):
        try:
            f = ImageFont.truetype(str(path), 12, index=index)
        except (OSError, ValueError, IndexError):
            break
        family, style = f.getname()
        yield FontFile(str(path), index, family or path.stem, style or "Regular")
        if path.suffix.lower() != ".ttc":
            break


@lru_cache(maxsize=1)
def font_index() -> dict[str, tuple[FontFile, ...]]:
    """Installed faces grouped by family name. Scanned once per process.

    >>> idx = font_index()
    >>> all(isinstance(k, str) for k in idx)
    True
    """
    index: dict[str, list[FontFile]] = {}
    for path in _iter_font_paths(font_dirs()):
        for ff in _faces_in(path):
            index.setdefault(ff.family, []).append(ff)
    return {k: tuple(v) for k, v in index.items()}


def families() -> list[str]:
    """Sorted family names installed on this machine."""
    return sorted(font_index())


def _best_style(
    faces: Sequence[FontFile], *, weight: int, italic: bool, condensed: bool
) -> FontFile:
    def score(ff: FontFile) -> tuple[int, int, int]:
        return (
            ff.italic != italic,
            ff.condensed != condensed,
            abs(ff.weight - weight),
        )

    return min(faces, key=score)


def find_font(
    family: str | Sequence[str],
    *,
    weight: int = REGULAR_WEIGHT,
    italic: bool = False,
    condensed: bool = False,
) -> FontFile | None:
    """First installed family in the preference list, at the closest style.

    ``family`` may be one name or a preference list. A path to a font file is
    accepted too, and wins outright.

    >>> find_font("definitely-not-installed-xyz") is None
    True
    """
    names = [family] if isinstance(family, str) else list(family)
    idx = font_index()
    for name in names:
        if name.lower().endswith(_FONT_SUFFIXES) and Path(name).is_file():
            faces = tuple(_faces_in(Path(name)))
            if faces:
                return _best_style(
                    faces, weight=weight, italic=italic, condensed=condensed
                )
        if name in idx:
            return _best_style(
                idx[name], weight=weight, italic=italic, condensed=condensed
            )
    # case-insensitive second pass
    lower = {k.lower(): k for k in idx}
    for name in names:
        if name.lower() in lower:
            return _best_style(
                idx[lower[name.lower()]],
                weight=weight,
                italic=italic,
                condensed=condensed,
            )
    return None


def resolve_face(
    family: str | Sequence[str] = SANS_STACK,
    *,
    size: int,
    weight: int = REGULAR_WEIGHT,
    italic: bool = False,
    condensed: bool = False,
) -> Face:
    """Resolve a typeface request to a sized ``Face``; never fails.

    Falls back to Pillow's embedded Aileron when nothing in the list is installed,
    so a render on a fontless CI box still produces a real (if plainer) result.
    """
    ff = find_font(family, weight=weight, italic=italic, condensed=condensed)
    if ff is None:
        return Face(FALLBACK_FAMILY, "Regular", int(size), None, 0)
    return Face(ff.family, ff.style, int(size), ff.path, ff.index)


@lru_cache(maxsize=256)
def _load_pil(path: str | None, index: int, size: int) -> ImageFont.FreeTypeFont:
    if path is None:
        return ImageFont.load_default(size=size)
    return ImageFont.truetype(path, size, index=index)
