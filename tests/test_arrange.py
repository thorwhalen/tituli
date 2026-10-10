"""Multi-block pages (tituli#6): stack/grid/glossed, list-aware wrap, timed images."""

import shutil
import subprocess

import pytest
from PIL import Image

from tituli import (
    Frame,
    Layout,
    TextStyle,
    TimedOverlay,
    block,
    glossed,
    grid,
    measure,
    render,
    stack,
    wrap,
)
from tituli.geometry import Box
from tituli.layout import Plate

F = Frame.blank((1920, 1080), color="#14161f")
S = TextStyle(size=0.04)


# --- stack -------------------------------------------------------------------------


def test_stack_returns_one_layout_with_every_run_in_order():
    parts = [block(t, S, F) for t in ("one", "two", "three")]
    page = stack(parts, frame=F)
    assert isinstance(page, Layout)
    assert [r.text for r in page.runs] == ["one", "two", "three"]
    ys = [r.bbox().y0 for r in page.runs]
    assert ys == sorted(ys)


def test_stack_gaps_are_fractions_of_frame_height_per_seam():
    parts = [block(t, S, F) for t in ("a", "b", "c")]
    page = stack(parts, frame=F, gap=[0.01, 0.05], anchor=None)
    a, b, c = (r.bbox() for r in page.runs)
    assert b.y0 - a.y1 == pytest.approx(0.01 * 1080)
    assert c.y0 - b.y1 == pytest.approx(0.05 * 1080)


def test_stack_wrong_number_of_gaps_raises():
    with pytest.raises(ValueError, match="one per seam"):
        stack([block("a", S, F), block("b", S, F)], frame=F, gap=[0.1, 0.2])


@pytest.mark.parametrize("align", ["left", "center", "right"])
def test_stack_aligns_within_the_widest(align):
    wide, narrow = block("a much wider line", S, F), block("x", S, F)
    page = stack([wide, narrow], frame=F, align=align, anchor=None)
    w, n = (r.bbox() for r in page.runs)
    key = {"left": "x0", "right": "x1"}.get(align)
    if key:
        assert getattr(w, key) == pytest.approx(getattr(n, key))
    else:
        assert w.center[0] == pytest.approx(n.center[0])


def test_stack_is_placed_in_the_frame_by_anchor():
    page = stack([block("Title", S, F), block("sub", S, F)], frame=F, anchor="center")
    bb = page.bbox()
    assert bb.center[0] == pytest.approx(960, abs=1)
    assert bb.center[1] == pytest.approx(540, abs=1)
    top = stack([block("Title", S, F)], frame=F, anchor="top")
    assert top.bbox().y0 == pytest.approx(F.safe.y0)


def test_stack_nests_and_carries_plates():
    plate = Plate(Box(0, 0, 10, 10), (0, 0, 0, 128))
    inner = stack(
        [block("a", S, F).with_plates(plate), block("b", S, F)], frame=F, anchor=None
    )
    outer = stack([block("head", S, F), inner], frame=F)
    assert [r.text for r in outer.runs] == ["head", "a", "b"]
    assert len(outer.plates) == 1


def test_a_plate_without_runs_is_refused_not_dropped():
    with pytest.raises(ValueError, match="plates but no runs"):
        stack([Layout(plates=(Plate(Box(0, 0, 5, 5), (0, 0, 0, 255)),))], frame=F)


# --- grid / glossed ----------------------------------------------------------------


def test_grid_keeps_one_pitch_whatever_the_item_widths():
    cells = [block(t, S, F) for t in ("i", "WWWWW", "m")]
    g = grid(cells, frame=F, gap=0.02, anchor=None)
    centers = [r.bbox().center[0] for r in g.runs]
    assert centers[1] - centers[0] == pytest.approx(centers[2] - centers[1])


def test_grid_wraps_into_rows():
    cells = [block(t, S, F) for t in "abcde"]
    g = grid(cells, frame=F, columns=2)
    assert g.meta["rows"] == 3 and g.meta["columns"] == 2
    tops = sorted({round(r.bbox().y0) for r in g.runs})
    assert len(tops) == 3


def test_glossed_centres_each_reading_under_its_glyph():
    pairs = [("カ", "ka"), ("ス", "su"), ("ン", "n")]
    lay = glossed(pairs, frame=F)
    glyphs = [r for r in lay.runs if r.tags[0].startswith("glyph:")]
    glosses = [r for r in lay.runs if r.tags[0].startswith("gloss:")]
    assert [r.text for r in glyphs] == ["カ", "ス", "ン"]
    for g, r in zip(glyphs, glosses):
        assert g.bbox().center[0] == pytest.approx(r.bbox().center[0], abs=1)
        assert r.bbox().y0 > g.bbox().y1
    assert len({round(r.y) for r in glyphs}) == 1  # one baseline


# --- list-aware wrapping -----------------------------------------------------------

PAIRS = (
    "バス bus · スープ soup · スプーン spoon · カップ cup · ハート heart · "
    "スター star · ダンス dance · パパ papa · スーパー supermarket · カード card · "
    "スカート skirt · ハンバーガー hamburger · トースト toast · ストップ stop"
)


def test_break_at_never_splits_a_pair():
    lines = wrap(PAIRS, S, 1080, max_width=900, break_at=" · ")
    assert len(lines) > 1
    items = [i.strip() for i in PAIRS.split("·")]
    for line in lines:
        for chunk in line.rstrip(" ·").split(" · "):
            assert chunk in items, (chunk, lines)
    assert all(measure(l, S, 1080) <= 900 for l in lines)
    assert all(l.endswith(" ·") for l in lines[:-1])  # the mark closes its line


def test_plain_wrap_would_split_pairs():
    """The regression the option exists for (the hand-made title page did this)."""
    lines = wrap(PAIRS, S, 1080, max_width=900)
    items = [i.strip() for i in PAIRS.split("·")]
    chunks = [c for l in lines for c in l.strip(" ·").split(" · ")]
    assert any(c not in items for c in chunks)


def test_an_item_wider_than_the_line_is_word_wrapped_not_cut():
    text = "x · " + "word " * 12 + "· y"
    lines = wrap(text, S, 1080, max_width=300, break_at=" · ")
    assert " ".join(lines).split() == text.split()
    assert not any(l.startswith("·") for l in lines)  # no orphaned mark


def test_no_break_space_binds_words():
    assert wrap("a b c", S, 1080, max_width=1) == ["a b", "c"]


def test_block_passes_break_at_through():
    lay = block(PAIRS, S, F, max_width=900, break_at=" · ")
    assert all(not r.text.endswith(("バス", "カップ")) for r in lay.runs)


# --- timed images onto video -------------------------------------------------------

ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not on PATH")


def _probe(path, entries, stream="v:0"):
    return subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            stream,
            "-show_entries",
            entries,
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _frame_at(path, t, tmp_path):
    out = tmp_path / f"f{t}.png"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-ss",
            str(t),
            "-i",
            str(path),
            "-frames:v",
            "1",
            str(out),
        ],
        check=True,
    )
    return Image.open(out).convert("RGB")


@ffmpeg
def test_overlay_times_an_image_over_a_padded_intro(tmp_path):
    from tituli import video

    size = (320, 180)
    src = tmp_path / "src.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=320x180:r=10:d=1",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(src),
        ],
        check=True,
    )
    title = Image.new("RGB", size, (220, 30, 30))
    out = video.overlay(
        src,
        [TimedOverlay(None, 0.0, 0.8, image=title, fade_in=0, fade_out=0.1)],
        tmp_path / "out.mp4",
        pad_start=0.5,
        workdir=tmp_path / "w",
    )
    vdur = float(_probe(out, "stream=duration"))
    assert vdur == pytest.approx(1.5, abs=0.15)
    adur = float(_probe(out, "stream=duration", stream="a:0"))
    assert adur == pytest.approx(1.5, abs=0.15)  # audio delayed by the pad
    r, g, b = _frame_at(out, 0.0, tmp_path).getpixel((160, 90))
    assert r > 150 and b < 100  # the title is up on the very first frame
    r, g, b = _frame_at(out, 1.3, tmp_path).getpixel((160, 90))
    assert b > 150 and r < 100  # and gone, the film underneath


@ffmpeg
def test_overlay_refuses_a_wrong_sized_image(tmp_path):
    from tituli import video

    with pytest.raises(ValueError, match="must match the video size"):
        video.overlay(
            "x.mp4",
            [TimedOverlay(None, 0, 1, image=Image.new("RGB", (10, 10)))],
            tmp_path / "o.mp4",
            size=(20, 20),
        )


def test_render_of_a_composed_page_is_one_image():
    page = stack(
        [block("Head", S, F), glossed([("カ", "ka")], frame=F, anchor=None)], frame=F
    )
    img = render(page, F)
    assert img.size == F.size
