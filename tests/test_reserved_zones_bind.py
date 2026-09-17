"""A reserved zone binds whatever anchor the caller named.

`Frame.with_delivery("youtube")` declares that the bottom ~22% of the frame
belongs to the platform — the subtitle track and the control bar, and on a
vertical Short the title, channel line and action rail. `lower_third`'s
docstring has always promised the block "moves above the subtitle band rather
than into it".

It did so only for `anchor="auto"`. `place()` filtered the candidate anchors
down to the ones clear of the reserved zones, and when *no* candidate was clear
— which is every time the caller named a single anchor, since there is then
nothing to choose between — it fell back to the full list and placed the block
inside the band. `lower_third` names `"bottom-left"`, so every lower third ever
composited sat at 95% of frame height, under YouTube's own furniture.

It is the same shape of defect as the truncation one: a rule that holds on the
path that was tested and quietly does not hold on the path that ships.
"""

import pytest

import tituli
from tituli import Frame
from tituli.geometry import ANCHORS, Box

PORTRAIT = (1080, 1920)
LANDSCAPE = (1920, 1080)


def _reserved(frame):
    return frame.reserved[0]


# --- the regression ----------------------------------------------------------


@pytest.mark.parametrize("size", [PORTRAIT, LANDSCAPE, (1280, 720)])
def test_a_lower_third_stays_out_of_the_subtitle_band(size):
    f = Frame.blank(size).with_delivery("youtube")
    lay = tituli.lower_third("1981 · Central Park, live", frame=f)
    assert lay.bbox().y1 <= _reserved(f).y0 + 0.5


def test_the_block_lands_just_above_the_band_not_somewhere_arbitrary():
    """Shortest way out — so a bottom anchor still reads as a bottom anchor."""
    f = Frame.blank(PORTRAIT).with_delivery("youtube")
    lay = tituli.lower_third("Name", "Role", frame=f)
    band = _reserved(f)
    assert lay.bbox().y1 == pytest.approx(band.y0, abs=1.0)


@pytest.mark.parametrize("anchor", sorted(ANCHORS))
def test_no_named_anchor_can_put_a_caption_in_a_reserved_zone(anchor):
    f = Frame.blank(PORTRAIT).with_delivery("youtube")
    lay = tituli.caption("Central Park", "public domain", frame=f, anchor=anchor)
    assert lay.bbox().y1 <= _reserved(f).y0 + 0.5


# --- place() itself ----------------------------------------------------------


def test_place_moves_a_named_anchor_out_of_the_way():
    f = Frame.blank(LANDSCAPE).with_delivery("youtube")
    where, box = f.place((400.0, 80.0), anchor="bottom-left")
    assert where == "bottom-left"  # the caller's choice is honoured, only moved
    assert box.y1 <= _reserved(f).y0 + 0.5


def test_place_is_unchanged_when_nothing_is_reserved():
    f = Frame.blank(LANDSCAPE)
    where, box = f.place((400.0, 80.0), anchor="bottom-left")
    assert where == "bottom-left" and box.y1 == pytest.approx(f.safe.y1)


def test_auto_still_prefers_a_clear_anchor_over_a_moved_one():
    """Moving is the fallback; picking an anchor that already fits is better."""
    f = Frame.blank(LANDSCAPE).with_delivery("youtube")
    where, box = f.place((400.0, 80.0))
    assert "bottom" not in where
    assert box.y1 <= _reserved(f).y0 + 0.5


def test_a_block_too_big_to_clear_is_left_alone_rather_than_pushed_off_frame():
    """Refusing to place it is the caller's decision, not a silent shove."""
    f = Frame.blank((400, 400))
    f = Frame(f.width, f.height, f.color, None, (), (Box(0, 0, 400, 400),), ())
    where, box = f.place((100.0, 50.0), anchor="bottom-left")
    assert box.x0 >= -0.5 and box.y0 >= -0.5
    assert box.x1 <= 400.5 and box.y1 <= 400.5


def test_a_side_band_is_cleared_sideways():
    """Reserved zones are edge bands; the axis to move along follows the band."""
    f = Frame.blank((1000, 1000))
    f = Frame(f.width, f.height, f.color, None, (), (Box(700, 0, 1000, 1000),), ())
    _, box = f.place((200.0, 100.0), anchor="right")
    assert box.x1 <= 700.5
