"""Cards, captions, credits, calligrams, scheduling — the use cases."""

import pytest
from PIL import Image

from tituli import (
    UNLABELLED,
    Credits,
    Frame,
    Label,
    Span,
    TimedOverlay,
    caption,
    credits_cards,
    credits_crawl,
    credits_frame,
    in_shape,
    intertitle,
    lower_third,
    on_path,
    rain,
    render,
    resolve,
    schedule_labels,
    title_card,
    truncate,
)
from tituli.compose import SCRIM_DARK, TextDoesNotFit, decide_ink
from tituli.credits import CreditsStyle, Entry, Section
from tituli.geometry import Box
from tituli.style import CAPTION, TextStyle


# --- ink decisions ---------------------------------------------------------------


def test_unknown_background_means_white_on_scrim():
    d = decide_ink(Frame.blank((100, 100)), Box(0, 0, 50, 50))
    assert d.ink == (255, 255, 255) and d.scrim == SCRIM_DARK


def test_solid_background_picks_ink_without_scrim():
    d = decide_ink(Frame.blank((100, 100), color="#fff"), Box(0, 0, 50, 50))
    assert d.ink != (255, 255, 255) and d.scrim is None
    d = decide_ink(Frame.blank((100, 100), color="#000"), Box(0, 0, 50, 50))
    assert d.ink == (255, 255, 255) and d.scrim is None


def test_mid_grey_picture_gets_a_scrim():
    f = Frame.from_image(Image.new("RGB", (100, 100), (120, 120, 120)))
    assert decide_ink(f, Box(0, 0, 100, 100)).scrim is not None


def test_busy_picture_gets_a_scrim_even_if_mean_is_fine():
    img = Image.new("RGB", (200, 100), (0, 0, 0))
    for x in range(0, 200, 20):
        img.paste((255, 255, 255), (x, 0, x + 10, 100))
    f = Frame.from_image(img)
    d = decide_ink(f, Box(0, 0, 200, 100))
    assert d.scrim is not None and ("busy" in d.reason or "insufficient" in d.reason)


# --- title card -------------------------------------------------------------------


def test_title_card_parts_and_fit():
    f = Frame.blank((1920, 1080), color="#101014")
    lay = title_card(
        "An Extraordinarily Long Title That Must Shrink To Fit The Frame",
        "sub",
        kicker="ep 1",
        frame=f,
    )
    kicker = "".join(r.text for r in lay.runs if r.unit == "glyph" and r.face.size < 30)
    assert kicker == "EP 1" and "sub" in "".join(r.text for r in lay.runs)
    assert lay.bbox().x0 >= f.safe.x0 and lay.bbox().x1 <= f.safe.x1
    assert lay.meta["anchor"] == "center"


def test_title_card_over_picture_avoids_subject_and_scrims_if_needed():
    img = Image.new("RGB", (1920, 1080), (120, 120, 120))  # neither ink reaches 4.5:1
    f = Frame.from_image(img, avoid=[(0.0, 0.0, 0.5, 1.0)])
    lay = title_card("Title", frame=f, anchor="auto")
    assert "right" in lay.meta["anchor"]
    assert lay.plates  # mid grey -> scrim


# --- caption -----------------------------------------------------------------------


def test_caption_truncates_uncontrolled_text():
    """Truncation survives, but only where it is asked for by name.

    The default is now ``on_overflow="fit"`` — shrink, and raise rather than
    ship a cut label. This call site is the case truncation was written for:
    a licence template that some upstream pasted into an artist field, whose
    length nobody controls and whose tail nobody needs.
    """
    f = Frame.blank((1920, 1080))
    blob = (
        "This is an artist field that some template filled with far too many words " * 6
    )
    lay = caption(blob, "credit", frame=f, max_lines=2, on_overflow="truncate")
    body = [r.text for r in lay.runs if r.face.size == CAPTION.px(1080)]
    assert len(body) == 2 and body[-1].endswith("…")


def test_caption_refuses_uncontrolled_text_by_default():
    f = Frame.blank((1920, 1080))
    blob = (
        "This is an artist field that some template filled with far too many words " * 6
    )
    with pytest.raises(TextDoesNotFit):
        caption(blob, "credit", frame=f, max_lines=2)


def test_an_unknown_overflow_policy_is_rejected():
    with pytest.raises(ValueError, match="on_overflow"):
        caption("hi", frame=Frame.blank((1920, 1080)), on_overflow="chop")


def test_truncate_always_fits():
    t = truncate("word " * 50, CAPTION, 1080, max_width=300, max_lines=1)
    assert t.endswith("…") and "\n" not in t


def test_caption_respects_youtube_reserved_zone():
    f = Frame.blank((1920, 1080)).with_delivery("youtube")
    lay = caption("Who is this", "source", frame=f)
    assert lay.bbox().y1 < 1080 * 0.78
    assert lay.meta["anchor"] == "top-left"


def test_caption_layout_precedes_scrim():
    f = Frame.blank((1920, 1080))
    lay = caption(
        "Three lines of caption text that wrap around a fair bit here",
        "src",
        frame=f,
        max_lines=3,
    )
    scrim = [p for p in lay.plates if p.kind != "box"][0]
    bb = lay.bbox()
    assert scrim.box.y0 <= bb.y0 and scrim.box.y1 >= bb.y1  # cut to the measured block


def test_attribution_is_small_and_present():
    f = Frame.blank((1920, 1080), color="#000")
    lay = caption("Caption", "Tiny credit", frame=f)
    sizes = sorted({r.face.size for r in lay.runs})
    assert (
        sizes[0] < sizes[-1] / 1.6
    )  # the credit line is much smaller than the caption


def test_lower_third_and_intertitle_render():
    f = Frame.blank((1280, 720), color="#222")
    assert render(lower_third("Name", "Role", frame=f), f).size == (1280, 720)
    assert render(intertitle("Meanwhile.", frame=f), f).size == (1280, 720)


# --- credits ----------------------------------------------------------------------


def _roll(n_images: int = 40) -> Credits:
    return Credits.from_dict(
        {
            "title": "A Film",
            "sections": [
                {
                    "heading": "Cast",
                    "entries": [["Narrator", "Someone"], ["Reader", "Someone Else"]],
                },
                {
                    "heading": "Images",
                    "entries": [
                        f"Picture {i} — Artist Number {i} — CC BY-SA 4.0 (Wikimedia Commons)"
                        for i in range(n_images)
                    ],
                },
            ],
            "closing": ["Made with tituli"],
        }
    )


def test_credits_from_dict_and_lines():
    c = _roll(3)
    assert c.title == "A Film" and c.sections[0].resolved_kind == "pairs"
    assert c.sections[1].resolved_kind == "prose"
    assert Credits.from_lines(["a", "b"]).line_count == 2
    assert (
        Entry.of(("Role", "Name")).role == "Role"
        and Entry.of({"name": "N"}).name == "N"
    )


def test_credits_cards_paginate_never_truncate():
    f = credits_frame((1920, 1080))
    c = _roll(60)
    cards = credits_cards(c, frame=f)
    assert len(cards) > 1
    drawn = [r.text for card in cards for r in card.runs]
    for i in range(60):
        assert any(f"Picture {i} " in t for t in drawn), f"attribution {i} lost"
    for card in cards:
        bb = card.bbox()
        assert bb.y0 >= f.safe.y0 - 1 and bb.y1 <= f.safe.y1 + 1


def test_credits_cards_raise_when_capped():
    with pytest.raises(ValueError, match="never truncates"):
        credits_cards(_roll(60), frame=credits_frame((1920, 1080)), max_cards=1)


def test_credits_crawl_has_lead_and_tail():
    f = credits_frame((1920, 1080))
    lay, total = credits_crawl(_roll(5), frame=f)
    assert lay.bbox().y0 >= 1080 - 2 and total >= lay.bbox().y1 + 1080 - 2


def test_credits_style_is_one_ramp():
    st = CreditsStyle(ink="#ffcc00").inked()
    assert st.name.color == (255, 204, 0, 255) == st.role.color
    s = Section("X", (Entry("n", "r"),), kind="list")
    assert s.resolved_kind == "list"


# --- calligram -------------------------------------------------------------------


def test_on_path_presets_and_fit():
    f = Frame.blank((800, 800), color="#fff")
    for shape in (
        "line",
        "circle",
        "arc",
        "wave",
        "diagonal",
        "s-curve",
        "M0 0 L 100 0 L 100 100",
    ):
        lay = on_path("a short text", shape=shape, frame=f)
        assert lay.runs and lay.meta["overflow"] == 0
    long = on_path("word " * 200, shape="line", frame=f)
    assert long.meta["size"] < TextStyle().size or long.meta["overflow"] == 0
    with pytest.raises(ValueError):
        on_path("x", shape="dodecahedron", frame=f)


def test_rain_one_glyph_per_letter_upright():
    f = Frame.blank((600, 1000), color="#fff")
    lay = rain(["il pleut", "des voix"], frame=f)
    assert len(lay.runs) == len("ilpleut") + len("desvoix")
    assert all(r.angle == 0 for r in lay.runs) and lay.meta["streaks"] == 2
    assert all(f.safe.x0 - 1 <= r.x and r.bbox().y1 <= f.safe.y1 + 1 for r in lay.runs)


def test_in_shape_fills_only_inside():
    f = Frame.blank((400, 400), color="#fff")
    mask = Image.new("L", (100, 100), 0)
    mask.paste(255, (0, 50, 100, 100))  # bottom half is inside
    lay = in_shape("the apple falls " * 5, mask, frame=f)
    assert lay.runs and all(r.y > 200 for r in lay.runs)
    once = in_shape("one two", mask, frame=f, repeat=False)
    assert once.meta["unplaced"] == []


# --- scheduling ------------------------------------------------------------------


def test_suppressed_label_is_not_recorded_as_shown():
    """The Eliza regression: the first panel loses to a card; the second must still get it."""
    panels = [Span(0, 6, "eliza"), Span(6, 12, "eliza")]
    cards = [TimedOverlay(None, 0, 4, slot="top-left", weight=2)]
    out = schedule_labels(panels, lambda p: Label("Eliza"), suppressed_by=cards)
    assert len(out) == 1 and out[0].start == 6


def test_repeat_gap_and_first_appearance():
    panels = [
        Span(0, 6, "a"),
        Span(6, 12, "a"),
        Span(200, 206, "a"),
        Span(206, 210, "b"),
    ]
    out = schedule_labels(panels, lambda p: Label(p.key.upper()))
    assert [(o.payload.text, o.start) for o in out] == [
        ("A", 0),
        ("A", 200),
        ("B", 206),
    ]


def test_none_label_is_refused_and_unlabelled_is_explicit():
    panels = [Span(0, 6, "a")]
    with pytest.raises(ValueError, match="UNLABELLED"):
        schedule_labels(panels, lambda p: None)
    assert schedule_labels(panels, lambda p: UNLABELLED) == []


def test_too_brief_panels_are_skipped():
    assert schedule_labels([Span(0, 1.0, "a")], lambda p: Label("A")) == []


def test_resolve_enforces_one_per_slot():
    light = TimedOverlay(None, 0, 5, slot="top-left", weight=1)
    heavy = TimedOverlay(None, 2, 4, slot="top-left", weight=2)
    other = TimedOverlay(None, 2, 4, slot="bottom-left", weight=1)
    kept = resolve([light, heavy, other])
    assert heavy in kept and other in kept and light not in kept
    with pytest.raises(ValueError, match="collide"):
        resolve([light, TimedOverlay(None, 1, 2, slot="top-left", weight=1)])


def test_note_block_headline_and_equal_lines():
    from tituli import note

    f = Frame.blank((1920, 1080)).with_delivery("youtube")
    lay = note(
        [
            "Hamilton is a 2015 musical.",
            "Ron Chernow wrote the biography.",
            "Philip died at 19.",
        ],
        headline="Before we go on",
        frame=f,
    )
    texts = [r.text for r in lay.runs]
    assert texts[0] == "Before we go on" and len(texts) == 4
    sizes = {r.face.size for r in lay.runs[1:]}
    assert len(sizes) == 1  # equal-weight lines
    assert lay.meta["anchor"] == "top-left"


def test_resolve_truncates_before_dropping():
    light = TimedOverlay(None, 18.0, 22.6, slot="top-left", weight=1)
    card = TimedOverlay(None, 21.0, 25.0, slot="top-left", weight=2)
    kept = resolve([light, card])
    cut = [o for o in kept if o.weight == 1][0]
    assert cut.start == 18.0 and cut.end == 21.0
    brief = TimedOverlay(
        None, 20.0, 22.6, slot="top-left", weight=1
    )  # only 1s would remain
    assert all(o.weight == 2 for o in resolve([brief, card]))


def test_scheduled_labels_and_cards_all_reach_the_film(tmp_path):
    """Regression for the layer-below Eliza bug: layout-less labels must be rendered, never skipped."""
    from tituli.video import materialize

    f = Frame.blank((640, 360)).with_delivery("youtube")
    cards = [TimedOverlay(caption("card", frame=f), 0, 3, slot="top-left", weight=2)]
    spans = [Span(0, 6, "eliza"), Span(6, 12, "eliza"), Span(12, 18, "map")]
    labels = schedule_labels(
        spans, lambda s: Label(s.key.title(), "src"), suppressed_by=cards
    )
    done = materialize(resolve([*cards, *labels]), frame=f)
    assert len(done) == 1 + len(labels) and all(o.layout is not None for o in done)
    assert {o.payload.text for o in done if o.payload} == {"Eliza", "Map"}
    with pytest.raises(ValueError, match="silently missing"):
        materialize([TimedOverlay(None, 0, 1, payload=object())], frame=f)


def test_scheduled_and_hand_built_labels_yield_identically():
    """The invariant: one suppression rule, whichever path an overlay took."""
    card = TimedOverlay(None, 21.0, 25.0, slot="top-left", weight=2)
    hand = TimedOverlay(None, 18.0, 22.6, slot="top-left", weight=1, payload=Label("x"))
    via_resolve = [o for o in resolve([hand, card]) if o.weight == 1]
    via_schedule = schedule_labels(
        [Span(18.0, 22.6, "x")], lambda s: Label("x"), suppressed_by=[card], hold_s=10
    )
    assert (
        [(o.start, o.end) for o in via_resolve]
        == [(o.start, o.end) for o in via_schedule]
        == [(18.0, 21.0)]
    )
    # and both drop it when what remains is unreadable
    late = TimedOverlay(None, 20.0, 22.6, slot="top-left", weight=1, payload=Label("x"))
    assert [o for o in resolve([late, card]) if o.weight == 1] == []
    assert (
        schedule_labels(
            [Span(20.0, 22.6, "x")],
            lambda s: Label("x"),
            suppressed_by=[card],
            hold_s=10,
        )
        == []
    )


def _rows_of(card):
    """Group a card's runs into rows by their first baseline, in reading order."""
    from tituli.geometry import Box

    rows: dict[float, Box] = {}
    for r in card.runs:
        key = round(r.y, 1)
        rows[key] = rows[key].union(r.bbox()) if key in rows else r.bbox()
    return [rows[k] for k in sorted(rows)]


def test_credits_wrapped_roles_do_not_collide():
    """A role that wraps to two lines must advance the row by its measured height."""
    long_roles = [
        (
            "2019.08.08 National Theater and Concert Hall, Taipei — evening performance",
            "Photographer One",
        ),
        (
            "Audio-Technica turntable playing a coloured vinyl record in a living room",
            "Photographer Two",
        ),
        ("Short role", "Photographer Three"),
        (
            "Blue (2011-11-29 by Ian T. McFarland) — a long descriptive title from Commons",
            "Photographer Four",
        ),
    ] * 3
    cr = Credits.from_dict(
        {
            "title": "Images",
            "sections": [
                {
                    "heading": "Commons",
                    "entries": [{"role": r, "name": n} for r, n in long_roles],
                }
            ],
        }
    )
    f = credits_frame((1920, 1080))
    for card in credits_cards(cr, frame=f):
        # every run's box must be disjoint from every run's box on another baseline
        runs = list(card.runs)
        for a in runs:
            for b in runs:
                if abs(a.y - b.y) > 1 and a.bbox().intersection(b.bbox()).area > 0:
                    # boxes on different baselines overlap: the row advance was too small
                    assert a.bbox().x1 <= b.bbox().x0 or b.bbox().x1 <= a.bbox().x0, (
                        a.text,
                        b.text,
                    )


def test_credits_cards_are_balanced():
    rows = [(f"Role number {i} of this roll", f"Name {i}") for i in range(20)]
    cr = Credits.from_dict(
        {
            "title": "Images",
            "sections": [
                {
                    "heading": "Commons",
                    "entries": [{"role": r, "name": n} for r, n in rows],
                }
            ],
            "closing": "…",
        }
    )
    f = credits_frame((1920, 1080))
    cards = credits_cards(cr, frame=f)
    assert len(cards) >= 2
    heights = [c.bbox().height for c in cards]
    assert max(heights) - min(heights) < f.safe.height * 0.3
