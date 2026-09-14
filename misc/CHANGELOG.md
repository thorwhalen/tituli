# Changelog

## 2026-09-14 — 0.0.1

First release. Frame-knowledge ladder (`Frame`), `Layout`/`Run`/`Plate` model, Pillow renderer with rotated glyph tiles, optional HarfBuzz+FreeType engine, title card / caption / lower third / note / intertitle, structured credits (cards + crawl, never truncating), calligrams (`on_path`, `rain`, `in_shape`), scheduler with first-appearance / repeat-gap / suppression inside the loop, ffmpeg output (`still`, `overlay`, `crawl`, `frames_to_video`), CLI via `cw`, lacing body `annot://schema/text-overlay/v1`, shipped `tituli` skill.

## 2026-09-14 — 0.0.3

Credits: a wrapped role/name row now advances by its measured height (was one line height — wrapped roles collided with the row beneath); cards are balanced to an even fill instead of greedy-then-nearly-empty; `from_lines`/`from_dict` document that the caller owns presentable text. Review fixes before this: `video.overlay` renders payload-only overlays or raises naming them; `Panel` → `Span`; `note()`; truncate-then-check suppression shared by `schedule_labels` and `resolve`.
