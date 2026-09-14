"""Video output through ffmpeg: stills to clips, overlays onto footage, crawls.

Everything here composites **rendered PNGs**; ffmpeg never draws text. That is
deliberate twice over: the system ffmpeg on a developer Mac commonly lacks
``drawtext``/``libass`` (this one does), and typographically ``drawtext`` is
crude. What ffmpeg is good at — ``overlay``, ``fade``, ``crop``, encoding — is
all it is asked to do, and :func:`require_filters` fails loudly if even that
is missing rather than emitting a text-free video.

The overlay chain follows the shape verified in production on a found-image
film: each PNG is a looped input **with its own duration** (a shorter input
silently vanishes under ``eof_action=pass``), faded on its own clock, shifted
with ``setpts``, gated with ``enable=between(t, …)``, and the audio is
stream-copied so the finished mix is never re-encoded.

Never burn text into stills that a camera move will pan and zoom — composite
onto the finished motion video, which is what :func:`overlay` does.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image

from tituli.schedule import TimedOverlay

FFMPEG_ENV_VAR = "TITULI_FFMPEG"
DEFAULT_FPS = 30
DEFAULT_CRF = 18
DEFAULT_PRESET = "medium"
DEFAULT_FADE_S = 0.4
_MIN_HOLD_S = 0.1
_FADE_SHARE = 2.5  # a fade never exceeds hold / this
_REQUIRED_FILTERS = ("overlay", "fade", "crop", "format", "setpts")
# YouTube rejects an `elst` edit list that `+faststart` alone leaves behind.
_MOV_FLAGS = "+faststart+negative_cts_offsets"
_ENCODE = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", _MOV_FLAGS, "-use_editlist", "0"]


class FfmpegError(RuntimeError):
    """ffmpeg is missing, or lacks a filter tituli needs."""


def ffmpeg_path() -> str:
    """The ffmpeg binary: ``$TITULI_FFMPEG`` or the first on PATH."""
    cand = os.environ.get(FFMPEG_ENV_VAR) or shutil.which("ffmpeg")
    if not cand:
        raise FfmpegError(
            "ffmpeg not found. Install it (https://ffmpeg.org, `brew install ffmpeg`, "
            f"`apt install ffmpeg`) or set ${FFMPEG_ENV_VAR} to the binary."
        )
    return cand


@lru_cache(maxsize=4)
def available_filters(binary: str | None = None) -> frozenset[str]:
    """Names of the filters this ffmpeg build has."""
    binary = binary or ffmpeg_path()
    out = subprocess.run([binary, "-hide_banner", "-filters"], capture_output=True, text=True, check=False).stdout
    names = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] and all(c in "TSC." for c in parts[0]):
            names.add(parts[1])
    return frozenset(names)


def require_filters(*names: str) -> None:
    """Raise :class:`FfmpegError` naming any missing filter."""
    have = available_filters()
    missing = [n for n in names if n not in have]
    if missing:
        raise FfmpegError(f"this ffmpeg build lacks filter(s) {missing}; tituli needs {list(names)}")


def _run(args: Sequence[str]) -> None:
    proc = subprocess.run(list(args), capture_output=True, text=True)
    if proc.returncode != 0:
        raise FfmpegError(f"ffmpeg failed ({proc.returncode}):\n{proc.stderr[-2000:]}")


def _even(n: int) -> int:
    return n if n % 2 == 0 else n - 1


def _size_args(size: tuple[int, int]) -> list[str]:
    w, h = _even(size[0]), _even(size[1])
    return ["-vf", f"scale={w}:{h}"]


def still(
    image: str | Path | Image.Image,
    dst: str | Path,
    *,
    duration: float,
    fps: float = DEFAULT_FPS,
    fade_in: float = DEFAULT_FADE_S,
    fade_out: float = DEFAULT_FADE_S,
    audio: str | Path | None = None,
    crf: int = DEFAULT_CRF,
) -> Path:
    """A still held for ``duration`` seconds with fades — a title or credits card.

    Transparent PNGs are flattened onto black.
    """
    require_filters("fade", "format")
    src, tmp = _as_png(image, dst)
    fade_in = min(fade_in, duration / _FADE_SHARE)
    fade_out = min(fade_out, duration / _FADE_SHARE)
    vf = (
        f"format=rgba,fade=t=in:st=0:d={fade_in:.3f},"
        f"fade=t=out:st={max(0.0, duration - fade_out):.3f}:d={fade_out:.3f},format=yuv420p"
    )
    args = [ffmpeg_path(), "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(fps), "-i", str(src)]
    if audio:
        args += ["-i", str(audio)]
    args += ["-t", f"{duration:.3f}", "-vf", vf, *_ENCODE, "-crf", str(crf), "-preset", DEFAULT_PRESET]
    if audio:
        args += ["-c:a", "aac", "-shortest"]
    args += [str(dst)]
    try:
        _run(args)
    finally:
        if tmp:
            tmp.unlink(missing_ok=True)
    return Path(dst)


def _as_png(image: str | Path | Image.Image, near: str | Path) -> tuple[Path, Path | None]:
    if isinstance(image, Image.Image):
        tmp = Path(near).with_suffix(".tituli-tmp.png")
        img = image
        if img.mode == "RGBA":
            flat = Image.new("RGB", img.size, (0, 0, 0))
            flat.paste(img, mask=img.split()[3])
            img = flat
        img.save(tmp)
        return tmp, tmp
    return Path(image), None


def overlay(
    video: str | Path,
    overlays: Sequence[TimedOverlay],
    dst: str | Path,
    *,
    size: tuple[int, int] | None = None,
    frame: "Frame | None" = None,
    delivery: str | None = "youtube",
    workdir: str | Path | None = None,
    crf: int = DEFAULT_CRF,
    preset: str = DEFAULT_PRESET,
    engine=None,
) -> Path:
    """Composite timed overlays onto ``video`` in one ffmpeg pass; audio copied.

    Every overlay is rendered: one with a ``layout`` as it is; one with only a
    ``payload`` (a :class:`~tituli.schedule.Label` from ``schedule_labels``, or
    a dict with ``text``/``attribution``/``kind``) is laid out here against
    ``frame`` (default: a blank frame of the video's size with ``delivery``'s
    reserved zones) at its ``slot``. Anything that cannot be rendered makes
    the call **raise, naming it** — nothing is ever silently left off the film.
    """
    from tituli.render import render_overlay

    require_filters(*_REQUIRED_FILTERS)
    video, dst = Path(video), Path(dst)
    if not overlays:
        raise ValueError("overlay() needs at least one TimedOverlay")
    size = size or probe_size(video)
    items = materialize(overlays, frame=frame or _blank_frame(size, delivery))
    workdir = Path(workdir) if workdir else dst.parent / f"_{dst.stem}_overlays"
    workdir.mkdir(parents=True, exist_ok=True)
    pngs: list[Path] = []
    for i, o in enumerate(items):
        p = workdir / f"ov{i:03d}.png"
        render_overlay(o.layout, size, engine=engine).save(p)
        pngs.append(p)

    args = [ffmpeg_path(), "-y", "-loglevel", "error", "-i", str(video)]
    for p, o in zip(pngs, items):
        args += ["-loop", "1", "-t", f"{max(_MIN_HOLD_S, o.duration):.3f}", "-i", str(p)]
    steps: list[str] = []
    current = "0:v"
    for i, o in enumerate(items):
        hold = max(_MIN_HOLD_S, o.duration)
        fade = min(o.fade, hold / _FADE_SHARE)
        steps.append(
            f"[{i + 1}:v]format=rgba,"
            f"fade=t=in:st=0:d={fade:.3f}:alpha=1,"
            f"fade=t=out:st={hold - fade:.3f}:d={fade:.3f}:alpha=1,"
            f"setpts=PTS+{o.start:.3f}/TB[ov{i}]"
        )
        nxt = f"v{i}"
        steps.append(
            f"[{current}][ov{i}]overlay=0:0:eof_action=pass:"
            f"enable='between(t,{o.start:.3f},{o.end:.3f})'[{nxt}]"
        )
        current = nxt
    args += [
        "-filter_complex", ";".join(steps),
        "-map", f"[{current}]", "-map", "0:a?",
        *_ENCODE, "-crf", str(crf), "-preset", preset,
        "-c:a", "copy",
        str(dst),
    ]
    _run(args)
    return dst


def _blank_frame(size: tuple[int, int], delivery: str | None):
    from tituli.frame import Frame

    return Frame.blank(size).with_delivery(delivery)


def materialize(overlays: Sequence[TimedOverlay], *, frame) -> list[TimedOverlay]:
    """Give every overlay a layout, rendering payloads; raise naming any that can't be.

    >>> from tituli.frame import Frame
    >>> from tituli.schedule import Label, TimedOverlay
    >>> f = Frame.blank((640, 360))
    >>> done = materialize([TimedOverlay(None, 0, 2, payload=Label("Eliza", "Earl, 1787"))], frame=f)
    >>> done[0].layout is not None
    True
    """
    from tituli.compose import caption, lower_third, note, title_card
    from tituli.schedule import Label

    out: list[TimedOverlay] = []
    unrenderable: list[str] = []
    for i, o in enumerate(overlays):
        if o.layout is not None:
            out.append(o)
            continue
        p = o.payload
        lay = None
        if isinstance(p, Label):
            lay = caption(p.text, p.attribution, frame=frame, anchor=o.slot)
        elif isinstance(p, dict) and "text" in p:
            kind = p.get("kind", "caption")
            if kind == "lower_third":
                lay = lower_third(p["text"], p.get("role", ""), frame=frame, anchor=o.slot)
            elif kind == "note":
                lay = note(p.get("lines", ()), headline=p["text"], frame=frame, anchor=o.slot)
            elif kind == "title":
                lay = title_card(p["text"], p.get("subtitle", ""), frame=frame, anchor=o.slot)
            else:
                lay = caption(p["text"], p.get("attribution", ""), frame=frame, anchor=o.slot)
        if lay is None:
            unrenderable.append(f"#{i} [{o.start:.2f}, {o.end:.2f}] slot={o.slot!r} payload={p!r}")
        else:
            out.append(o.with_layout(lay))
    if unrenderable:
        raise ValueError(
            "overlay(): these overlays have no layout and no renderable payload "
            "(a Label, or a dict with 'text'); render them first or they would be "
            "silently missing from the film:\n  " + "\n  ".join(unrenderable)
        )
    return out


def crawl(
    tall: Image.Image | str | Path,
    dst: str | Path,
    *,
    size: tuple[int, int],
    speed_px_s: float,
    fps: float = DEFAULT_FPS,
    audio: str | Path | None = None,
    crf: int = DEFAULT_CRF,
) -> Path:
    """Scroll a tall image up through a ``size`` window at ``speed_px_s``.

    The image should already carry its own lead-in and tail (as
    :func:`tituli.credits.credits_crawl` does), so the clip starts and ends on
    an empty frame. Duration is ``(image height - window height) / speed``.
    """
    require_filters("crop")
    w, h = _even(size[0]), _even(size[1])
    src, tmp = _as_png(tall, dst)
    with Image.open(src) as im:
        ih = im.height
    travel = max(1, ih - h)
    duration = travel / speed_px_s
    vf = f"crop={w}:{h}:0:'min(t*{speed_px_s:.4f},{travel})',format=yuv420p"
    args = [ffmpeg_path(), "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(fps), "-i", str(src)]
    if audio:
        args += ["-i", str(audio)]
    args += ["-t", f"{duration:.3f}", "-vf", vf, *_ENCODE, "-crf", str(crf), "-preset", DEFAULT_PRESET]
    if audio:
        args += ["-c:a", "aac", "-shortest"]
    args += [str(dst)]
    try:
        _run(args)
    finally:
        if tmp:
            tmp.unlink(missing_ok=True)
    return Path(dst)


def frames_to_video(
    frames: Iterable[Image.Image],
    dst: str | Path,
    *,
    size: tuple[int, int],
    fps: float = DEFAULT_FPS,
    audio: str | Path | None = None,
    crf: int = DEFAULT_CRF,
) -> Path:
    """Encode a lazy stream of RGB frames (the kinetic path: per-glyph reveals)."""
    w, h = _even(size[0]), _even(size[1])
    args = [
        ffmpeg_path(), "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
    ]
    if audio:
        args += ["-i", str(audio)]
    args += [*_ENCODE, "-crf", str(crf), "-preset", DEFAULT_PRESET]
    if audio:
        args += ["-c:a", "aac", "-shortest"]
    args += [str(dst)]
    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for f in frames:
            if f.size != (w, h):
                f = f.resize((w, h))
            proc.stdin.write(f.convert("RGB").tobytes())
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        proc.wait()
    if proc.returncode != 0:
        raise FfmpegError(f"ffmpeg failed ({proc.returncode}):\n{err[-2000:]}")
    return Path(dst)


def probe_size(video: str | Path) -> tuple[int, int]:
    """``(width, height)`` of the first video stream, via ffprobe."""
    ffprobe = shutil.which("ffprobe") or str(Path(ffmpeg_path()).with_name("ffprobe"))
    out = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
         "-of", "csv=p=0", str(video)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    w, h = out.split(",")[:2]
    return int(w), int(h)


__all__ = [
    "FfmpegError",
    "materialize",
    "ffmpeg_path",
    "available_filters",
    "require_filters",
    "still",
    "overlay",
    "crawl",
    "frames_to_video",
    "probe_size",
]

