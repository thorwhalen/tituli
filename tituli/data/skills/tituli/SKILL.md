---
name: tituli
description: Put tasteful text on video or stills with the `tituli` Python package — title cards, end credits from structured data, captions with a tiny source attribution that stay off the subject, lower thirds, editorial context notes, and calligrams / concrete poems (text along a circle, wave, SVG path, or falling like Apollinaire's "Il pleut"). Use when asked to "add credits", "add a title card", "caption this image", "label these stills", "put a name and role on screen", "add context cards", "overlay text on this video", "make a calligram", "text on a path", or when a film needs on-screen text that looks designed rather than debug-dumped. Owns placement (title-safe, subject-avoiding, YouTube subtitle band reserved), ink/scrim by contrast, wrapping and truncation, scheduling of captions against heavier cards, and ffmpeg compositing. Not for SRT subtitles (use `mixing`).
license: MIT
metadata:
  audience: users
---

# tituli — text in video

`pip install tituli` (Pillow only). Video output needs `ffmpeg` on PATH (only `overlay`/`fade`/`crop`; never `drawtext`). Extras: `[saliency]` (burns, subject avoidance), `[shaping]` (HarfBuzz), `[lacing]`, `[cli]`.

## The one model

Every call returns a `Layout`; `render(layout, frame)` gives an image; `tituli.video.*` puts images on footage. A `Frame` says how much is known about the picture:

```python
from tituli import Frame
Frame.blank((1920, 1080))                       # knows only its size -> white on a dark scrim
Frame.blank((1920, 1080), color="#101014")      # solid colour -> ink by contrast, no scrim
Frame.from_image("still.jpg", delivery="youtube")               # samples pixels; keeps the subtitle band clear
Frame.from_image("still.jpg", avoid=burns.salient_box)          # ...and keeps off the subject
Frame.over(["f01.jpg", "f02.jpg", "f03.jpg"], avoid=burns.salient_box)   # the frames under a camera move; worst instant wins
```

## Recipes

**Title card** (PNG, or MP4 with a duration):
```python
from tituli import Frame, title_card, render
f = Frame.blank((1920, 1080), color="#101014")
render(title_card("The Apple", "a concrete poem", kicker="Episode 3", frame=f), f).save("title.png")
# video: tituli.video.still(image, "title.mp4", duration=4)
```

**Caption + tiny attribution on a still** — text is wrapped and truncated for you; attribution is small on purpose:
```python
from tituli import Frame, caption, render
f = Frame.from_image("still.jpg", delivery="youtube")          # add avoid=burns.salient_box if burns is installed
lay = caption("Angelica Schuyler Church", "John Trumbull, 1785 · public domain", frame=f)
render(lay, f).save("captioned.png")             # or render_overlay(lay, f.size) for a transparent PNG
```

**Lower third / context note**: `lower_third("Eliza Hamilton", "née Schuyler", frame=f)`; `note(["What Hamilton is", "Who Chernow is"], headline="Before we go on", frame=f)`.

**Credits** — structured, never a wall of filenames, never truncated:
```python
from tituli import Credits, credits_cards, credits_crawl, credits_frame, render, Frame
cr = Credits.from_dict({"title": "The Apple",
    "sections": [{"heading": "Voices", "entries": [["Narrator", "T. Whalen"]]},
                 {"heading": "Images", "entries": ["Still Life — Cézanne — public domain"]}],
    "closing": ["Made with tituli"]})
f = credits_frame((1920, 1080))
for i, card in enumerate(credits_cards(cr, frame=f)): render(card, f).save(f"credits_{i}.png")
lay, total = credits_crawl(cr, frame=f)           # then tituli.video.crawl(render(lay, Frame.blank((1920, total), color=f.color)), "credits.mp4", size=(1920,1080), speed_px_s=97)
```
`Credits.from_lines(lines)` takes a plain list (braidio's `credits_card` shape).

**Captions on a finished film** (composite onto the motion video, never into the stills):
```python
from tituli import Span, Label, UNLABELLED, schedule_labels, TimedOverlay, resolve, note
from tituli.video import overlay
f = Frame.blank((1920, 1080)).with_delivery("youtube")
cards = [TimedOverlay(note([...], headline="...", frame=f), 12.0, 18.0, slot="top-left", weight=2)]
spans = [Span(start, end, key=still_id) for ...]                  # your cut
labels = schedule_labels(spans, lambda s: Label(text, attribution) if known else UNLABELLED, suppressed_by=cards)
overlay("film.mp4", resolve([*cards, *labels]), "film_captioned.mp4")   # renders Label payloads itself; raises naming anything it can't
```
Rules built in: label on first appearance, again only after 150 s, truncated (not dropped) against a heavier card, and a suppressed label is not counted as shown. Returning `None` from `label_for` raises — say `UNLABELLED` when a still is deliberately unlabelled.

**Calligram**: `on_path(text, shape="circle"|"wave"|"arc"|"M 0 0 C ..."|Path, frame=f, upright=False)`; `rain(lines, frame=Frame.blank((1080, 1920), color="#f4f1e8"))` (portrait); `in_shape(text, mask_image, frame=f)`. A glyph-by-glyph reveal: `lay.staggered(step=0.05, ramp=0.2)` → `tituli.video.frames_to_video(frames(lay, f, duration=6), "out.mp4", size=f.size)`.

## CLI

`python -m tituli title_card "Title" "sub" --background "#101014" --out t.png` · `python -m tituli caption still.jpg "text" "source" --out c.png` · `python -m tituli credits spec.json --mode crawl --out credits.mp4` · `python -m tituli calligram "text" --shape circle --out c.png` · `python -m tituli overlay_video film.mp4 overlays.json --out out.mp4` · `python -m tituli fonts Helvetica`.

## Taste rules the defaults already follow

Title-safe 90 %; WCAG 4.5:1 target; sans working set (Helvetica Neue → Inter → … → DejaVu Sans) with Pillow's Aileron as the last fallback; ≥ 36 px-equivalent at 1080p for anything meant to be read; attribution ~22 px and 85 % opacity; credits hold ≥ 3 s / crawl ≈ 97 px/s; reveals 0.4 s; corner-falloff scrim cut to the text block, only when contrast or busyness demands it. Sizes are fractions of frame height, so the same call is right at 720p and 4K. Don't override these unless asked.
