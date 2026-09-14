"""Core guardrails: geometry, colour, fonts, layout, the frame ladder."""

import math

import pytest
from PIL import Image

from tituli import (
    ANCHORS,
    Box,
    Frame,
    Path,
    TextStyle,
    along_path,
    block,
    contrast_ratio,
    fit_size,
    ink_for,
    measure,
    parse_color,
    render,
    render_overlay,
    resolve_face,
    safe_area,
    wrap,
)
from tituli.color import needs_scrim, relative_luminance
from tituli.fonts import FALLBACK_FAMILY, families, find_font
from tituli.frame import reserved_zones
from tituli.style import CAPTION, TITLE


# --- colour --------------------------------------------------------------------


def test_wcag_contrast_extremes():
    assert contrast_ratio("#000", "#fff") == 21.0
    assert contrast_ratio("#777", "#777") == 1.0


def test_ink_for_flips_at_mid_luminance():
    assert ink_for(luminance=0.95) != ink_for(luminance=0.02)
    assert ink_for(luminance=0.02) == (255, 255, 255)


def test_needs_scrim_on_mid_tones_only():
    assert needs_scrim((255, 255, 255), luminance=0.4)
    assert not needs_scrim((255, 255, 255), luminance=0.01)


def test_parse_color_forms():
    assert parse_color("#abc") == (170, 187, 204, 255)
    assert parse_color((1, 2, 3, 4)) == (1, 2, 3, 4)
    assert parse_color("white") == (255, 255, 255, 255)
    with pytest.raises(ValueError):
        parse_color("#12345")


# --- geometry --------------------------------------------------------------------


def test_safe_area_is_title_safe_90pct():
    b = safe_area(1920, 1080)
    assert (b.x0, b.y0) == (pytest.approx(96.0), pytest.approx(54.0))
    assert math.isclose(b.width / 1920, 0.9)


def test_anchor_grid_has_nine_positions():
    assert len(ANCHORS) == 9


def test_path_arc_length_and_angle():
    p = Path.line((0, 0), (0, 100))
    assert p.length == 100
    assert p.angle(50) == 90.0  # pointing down on screen
    c = Path.circle((0, 0), 10)
    assert c.closed
    assert math.isclose(c.length, 2 * math.pi * 10, rel_tol=1e-3)


def test_svg_path_parsing_relative_and_curves():
    p = Path.from_svg("M0 0 l10 0 v10 h-10 Z")
    assert p.closed and math.isclose(p.length, 40.0)
    q = Path.from_svg("M0 0 C 0 10, 10 10, 10 0")
    assert q.length > 10
    with pytest.raises(ValueError):
        Path.from_svg("M0 0 A 5 5 0 0 1 10 10")


def test_path_fit_keeps_aspect_and_centres():
    p = Path.line((0, 0), (100, 0)).fit(Box(0, 0, 50, 50))
    bb = p.bbox()
    assert math.isclose(bb.width, 50) and math.isclose(bb.center[1], 25)


# --- fonts ---------------------------------------------------------------------


def test_resolve_face_never_fails():
    face = resolve_face(["no-such-family-xyz"], size=40)
    assert face.family == FALLBACK_FAMILY and face.size == 40
    assert face.length("Hello") > 0


def test_find_font_returns_none_for_unknown():
    assert find_font("no-such-family-xyz") is None


def test_families_is_a_sorted_list():
    fams = families()
    assert fams == sorted(fams)


# --- layout ---------------------------------------------------------------------


def test_style_size_is_fraction_of_height():
    assert TITLE.px(1080) == round(0.075 * 1080)
    assert TITLE.px(2160) == 2 * TITLE.px(1080)


def test_wrap_respects_measured_width():
    text = "the quick brown fox jumps over the lazy dog " * 3
    lines = wrap(text, CAPTION, 1080, max_width=400)
    assert len(lines) > 3
    assert all(measure(l, CAPTION, 1080) <= 400 for l in lines)


def test_fit_size_shrinks_until_it_fits():
    st = fit_size("Unshrinkable", TITLE, 1080, max_width=300)  # one word, wider than the box
    assert st.size < TITLE.size
    assert measure("Unshrinkable", st, 1080) <= 300


def test_block_alignment_and_units():
    plain = TextStyle(size=0.05)
    lay = block("ab\ncd", plain.with_(align="right"), 1080, max_width=500)
    assert len(lay.runs) == 2 and all(r.unit == "line" for r in lay.runs)
    glyphs = block("abc", plain, 1080, unit="glyph")
    assert [r.text for r in glyphs.runs] == ["a", "b", "c"]
    words = block("one two", plain, 1080, unit="word")
    assert [r.text for r in words.runs] == ["one", "two"]


def test_tracking_emits_glyph_runs():
    lay = block("abc", TITLE.with_(tracking=0.1), 1080)
    assert all(r.unit == "glyph" for r in lay.runs)
    assert lay.runs[1].x > lay.runs[0].x


def test_along_path_rotates_to_tangent_and_reports_overflow():
    p = Path.line((0, 100), (0, 200))  # straight down
    lay = along_path("hi", p, TextStyle(size=0.05), 1080)
    assert all(math.isclose(r.angle, 90.0) for r in lay.runs)
    short = Path.line((0, 0), (5, 0))
    assert along_path("overflowing text", short, TextStyle(size=0.05), 1080).meta["overflow"] > 0


def test_along_path_upright_keeps_angle_zero():
    lay = along_path("hi", Path.circle((100, 100), 50), TextStyle(size=0.05), 1080, upright=True)
    assert all(r.angle == 0.0 for r in lay.runs)


def test_layout_timing_helpers():
    lay = block("a b c", TextStyle(size=0.05), 1080, unit="word").staggered(step=0.5, ramp=0.2)
    assert [r.t_in for r in lay.runs] == [0.0, 0.5, 1.0]
    assert lay.duration_hint == pytest.approx(1.2)


# --- frame ladder -----------------------------------------------------------------


def test_rung_a_knows_nothing():
    f = Frame.blank((100, 100))
    assert f.luminance_under(f.safe) is None and f.overlap(f.safe) == 0.0


def test_rung_b_solid_colour():
    assert Frame.blank((100, 100), color="#000").luminance_under(Box(0, 0, 10, 10)) == 0.0


def test_rung_c_samples_pixels():
    img = Image.new("RGB", (100, 100), (255, 255, 255))
    img.paste((0, 0, 0), (0, 0, 50, 100))
    f = Frame.from_image(img)
    assert f.luminance_under(Box(0, 0, 40, 100)) < 0.05
    assert f.luminance_under(Box(60, 0, 100, 100)) > 0.95


def test_rung_c_worst_case_over_a_window_of_frames():
    dark = Image.new("RGB", (100, 100), (0, 0, 0))
    mid = Image.new("RGB", (100, 100), (128, 128, 128))
    f = Frame.from_image([dark, mid])
    lum, _ = f.luminance_stats(Box(0, 0, 100, 100))
    assert lum == pytest.approx(relative_luminance((128, 128, 128)))


def test_rung_d_avoid_accepts_boxes_and_callables():
    img = Image.new("RGB", (100, 100), (200, 200, 200))
    f1 = Frame.from_image(img, avoid=[(0.0, 0.0, 0.5, 1.0)])
    f2 = Frame.from_image(img, avoid=lambda im: (0.0, 0.0, 0.5, 1.0))
    f3 = Frame.from_image(img, avoid=lambda im: [(0.0, 0.0, 0.5, 1.0), (0.6, 0.6, 0.1, 0.1)])
    assert f1.avoid == f2.avoid and len(f3.avoid) == 2
    assert f1.overlap(Box(0, 0, 50, 100)) == 1.0
    assert f1.overlap(Box(60, 0, 100, 100)) == 0.0


def test_place_avoids_the_subject():
    img = Image.new("RGB", (1000, 1000))
    f = Frame.from_image(img, avoid=[(0.0, 0.0, 0.5, 1.0)])  # subject fills the left half
    where, box = f.place((200, 100), anchor="auto")
    assert "right" in where and box.x0 >= 500


def test_reserved_zones_exclude_the_bottom_for_youtube():
    assert reserved_zones("youtube")[0][1] > 0.7
    f = Frame.blank((1920, 1080)).with_delivery("youtube")
    where, box = f.place((300, 100), anchor=["bottom-left", "top-left"])
    assert where == "top-left"
    with pytest.raises(ValueError):
        reserved_zones("vhs")


def test_place_rejects_unknown_anchor():
    with pytest.raises(ValueError):
        Frame.blank((10, 10)).place((1, 1), anchor="middle-ish")


# --- render ---------------------------------------------------------------------


def test_render_modes_follow_frame_knowledge():
    lay = block("Hi", TITLE, 200)
    assert render(lay, Frame.blank((300, 200))).mode == "RGBA"
    assert render(lay, Frame.blank((300, 200), color="#000")).mode == "RGB"
    assert render(lay, Frame.from_image(Image.new("RGB", (300, 200)))).mode == "RGB"


def test_render_actually_draws_pixels():
    lay = block("Hi", TITLE.with_(color="#fff"), 200)
    img = render_overlay(lay, (300, 200))
    assert img.getbbox() is not None  # something non-transparent was drawn


def test_rotated_run_lands_near_its_origin():
    p = Path.line((150, 20), (150, 180))
    lay = along_path("I", p, TextStyle(size=0.3, color="#fff"), 200)
    img = render_overlay(lay, (300, 200))
    x0, y0, x1, y1 = img.getbbox()
    assert 100 < (x0 + x1) / 2 < 200 and 20 <= y0 and y1 <= 200


def test_reveal_envelope_hides_runs_before_t_in():
    lay = block("Hi", TITLE.with_(color="#fff"), 200).with_timing(1.0, 1.5)
    assert render_overlay(lay, (300, 200), t=0.5).getbbox() is None
    assert render_overlay(lay, (300, 200), t=2.0).getbbox() is not None
