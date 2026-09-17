"""Overlay text is set complete, or not at all — never silently cut.

A shipped short carried a lower third reading ``1981 · Centr…``. That is not a
shortened label, it is a *wrong* one: the viewer is told the recording is from
somewhere called Centr. The cause was ``truncate`` with ``max_lines=1``.

The mechanism is worth keeping in mind because it is invisible on the aspect
people usually test: type is sized as a fraction of frame **height** but has to
fit the frame's **width**. On 1920x1080 a lower third at 0.042 em is 45px tall
against 1920px of width and fits easily; on 1080x1920 the same style is 81px
tall against 1080px of width, and overflows.
"""

import re

import pytest

import tituli
from tituli import Frame
from tituli.compose import MIN_LEGIBLE_SIZE, TextDoesNotFit, fit, truncate
from tituli.style import TextStyle

TAG = "1981 · Central Park, live"
PORTRAIT = (1080, 1920)
LANDSCAPE = (1920, 1080)
WIDE_SHORT = (1280, 720)


def _text(layout) -> str:
    """Everything the layout will actually draw, whitespace removed.

    tituli emits *placed glyphs*: a wrapped block comes back as one run per
    line, while a tracked style comes back as one run per character — and a
    wrap point between two glyph runs leaves no run at all. So there is no
    faithful way to rebuild the spaces, and these tests compare
    whitespace-insensitively: what matters is that every character survived,
    not where the line broke.
    """
    return re.sub(r"\s+", "", "".join(r.text for r in layout.runs))


def _shows(layout, phrase: str) -> bool:
    return re.sub(r"\s+", "", phrase) in _text(layout)


# --- the regression ----------------------------------------------------------


@pytest.mark.parametrize("size", [PORTRAIT, LANDSCAPE, WIDE_SHORT])
def test_a_recording_tag_is_never_cut(size):
    lay = tituli.lower_third(TAG, frame=Frame.blank(size).with_delivery("youtube"))
    assert "…" not in _text(lay)
    assert _shows(lay, "Central Park")


def test_the_portrait_case_that_shipped_broken():
    lay = tituli.lower_third(TAG, frame=Frame.blank(PORTRAIT).with_delivery("youtube"))
    assert _text(lay) == re.sub(r"\s+", "", TAG)


@pytest.mark.parametrize("size", [PORTRAIT, LANDSCAPE])
def test_a_caption_and_its_attribution_are_never_cut(size):
    frame = Frame.blank(size).with_delivery("youtube")
    title = "The Beach Boys in Central Park, 1971"
    credit = "Chester Higgins, Jr. · public domain"
    lay = tituli.caption(title, credit, frame=frame)
    assert "…" not in _text(lay)
    assert _shows(lay, "Central Park, 1971")
    assert _shows(lay, "public domain")


def test_a_caption_too_long_for_a_narrow_frame_refuses_rather_than_lying():
    """The designed outcome when shrinking runs out: hand the choice back.

    A 69-character title in three lines does not fit a portrait safe box at a
    legible size. Truncating it would put a false label on screen; raising lets
    the caller shorten the wording, allow more lines, or show nothing.
    """
    frame = Frame.blank(PORTRAIT).with_delivery("youtube")
    long_title = (
        "A Central Park concert audience, Schaefer Bandstand — not this concert"
    )
    with pytest.raises(TextDoesNotFit):
        tituli.caption(long_title, frame=frame)
    # the caller's fix: fewer words, same meaning
    lay = tituli.caption("A Central Park audience — not this concert", frame=frame)
    assert _shows(lay, "not this concert")


def test_note_lines_are_never_cut():
    frame = Frame.blank(PORTRAIT).with_delivery("youtube")
    lines = ["A short line", "A considerably longer line that would previously be cut"]
    lay = tituli.note(lines, headline="Before we go on", frame=frame)
    assert "…" not in _text(lay)
    assert _shows(lay, "previously be cut")


# --- fit() itself ------------------------------------------------------------


def test_text_that_already_fits_keeps_its_size():
    st = TextStyle(size=0.05)
    body, used = fit("short", st, 1000.0, max_width=900, max_lines=1)
    assert body == "short"
    assert used.size == st.size


def test_text_that_does_not_fit_is_shrunk_not_cut():
    st = TextStyle(size=0.08)
    body, used = fit(TAG, st, 1920.0, max_width=900, max_lines=1)
    assert body == TAG
    assert used.size < st.size
    assert used.size >= MIN_LEGIBLE_SIZE


def test_shrinking_stops_at_the_legibility_floor():
    st = TextStyle(size=0.08)
    with pytest.raises(TextDoesNotFit) as exc:
        fit("x " * 400, st, 1920.0, max_width=400, max_lines=1)
    assert exc.value.tried_size == pytest.approx(MIN_LEGIBLE_SIZE)


def test_the_refusal_carries_what_the_caller_needs_to_decide():
    st = TextStyle(size=0.05)
    with pytest.raises(TextDoesNotFit) as exc:
        fit("word " * 200, st, 1920.0, max_width=400, max_lines=1)
    e = exc.value
    assert e.max_lines == 1
    assert e.lines_at_min > e.max_lines
    assert e.text.startswith("word")
    # and the message tells a human what their options are
    assert "Shorten the text" in str(e)


def test_more_lines_can_rescue_text_that_one_line_cannot_hold():
    st = TextStyle(size=0.04)
    long = "A considerably longer line of explanatory text than one row can hold"
    with pytest.raises(TextDoesNotFit):
        fit(long, st, 1920.0, max_width=500, max_lines=1)
    body, _ = fit(long, st, 1920.0, max_width=500, max_lines=6)
    assert body.replace("\n", " ") == long


def test_a_caller_may_lower_the_floor_deliberately():
    st = TextStyle(size=0.05)
    text = "word " * 8
    with pytest.raises(TextDoesNotFit):
        fit(text, st, 1920.0, max_width=400, max_lines=1)
    body, used = fit(text, st, 1920.0, max_width=400, max_lines=1, min_size=0.008)
    assert body == text.strip()  # wrap() strips the trailing space
    assert used.size < MIN_LEGIBLE_SIZE  # their call, explicitly made


def test_shrinking_has_a_hard_floor_the_rasteriser_imposes():
    """Lowering min_size is not unlimited: the font face bottoms out around 8px.

    Worth pinning because it makes the failure mode honest — past that point
    `fit` raises no matter how small a min_size is asked for, so a caller cannot
    accidentally ship something that is present but unreadable.
    """
    st = TextStyle(size=0.05)
    # measured: the face bottoms out at 8px, reached by ~0.002 of a 1920 frame
    assert (
        st.with_(size=0.002).face(1920.0).size
        == st.with_(size=0.0005).face(1920.0).size
    )
    with pytest.raises(TextDoesNotFit):
        fit("word " * 30, st, 1920.0, max_width=400, max_lines=1, min_size=1e-6)


# --- truncate stays, for the case it was written for -------------------------


def test_truncate_is_still_available_for_uncontrolled_text():
    """A licence blob pasted into an artist field still has to fit somehow."""
    st = TextStyle(size=0.05)
    out = truncate("licence " * 60, st, 1920.0, max_width=400, max_lines=1)
    assert out.endswith("…")


def test_fit_and_the_error_are_exported():
    assert tituli.fit is fit
    assert tituli.TextDoesNotFit is TextDoesNotFit
    assert tituli.MIN_LEGIBLE_SIZE == MIN_LEGIBLE_SIZE
