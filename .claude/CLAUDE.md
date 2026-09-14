# tituli — agent & contributor guide

Text in video: title cards, credits, captions + attribution, lower thirds, notes, calligrams. One `Layout` of placed `Run`s over `Plate`s on a `Frame`; Pillow rasterises, ffmpeg composites. See README for the API and the seam table.

## Seams (current default → replacement)

1. `Frame.from_image(avoid=)` — none → `burns.salient_box` / any `FacesDetector` (`[saliency]`)
2. `render(engine=)` — `PillowEngine` → `tituli.shaping.HarfBuzzEngine` (`[shaping]`)
3. `on_path(shape=)` — named presets → SVG `d` / `Path`
4. `Frame(delivery=)` — none → `DELIVERY_RESERVED["youtube"]` (add a target, never a caller-side rule)
5. `tituli.bodies` — plain dict → `annot://schema/text-overlay/v1` in lacing (`[lacing]`)

Surfaces built: CLI (`python -m tituli` over `tituli.tools._dispatch_funcs`), shipped skill. MCP/HTTP would project the same list — never author a second one.

## Invariants (tests pin these — change deliberately)

- `import tituli` pulls no surface library and no optional dependency (`tests/test_surfaces.py`).
- **Nothing is silently left off the film.** `label_for` returning `None` raises (`UNLABELLED` is the explicit choice); credits paginate and raise rather than truncate; `video.overlay` renders every overlay or raises *naming* the ones it cannot; equal-weight collisions raise.
- One suppression rule for both scheduling paths: `_yield_to` — a heavier overlay takes the time it needs; the lighter keeps what is left if still readable. `schedule_labels` and `resolve` must agree (invariant test).
- Pipeline order: wrap → measure → ink → scrim cut to the block → compose. A scrim sized before measuring is the bug this order exists to prevent.
- Sizes are fractions of frame height; time is seconds; boxes crossing a boundary are normalised `(x, y, w, h)`.
- Never burn text into stills a camera move will pan; composite onto the finished motion video.
- A **tracked** style (`tracking != 0`) lays out one run per glyph (Pillow cannot track) — tests that count runs must use an untracked style.
- No fonts ship in the package. Discovery + Pillow's embedded Aileron fallback.

## Reviewing

A description of a design and the code that implements it are different artifacts; reviewing the first says nothing about the second. This package's first review found three real defects that its (accurate) API report could not show — one of them the silent-drop the scheduler was built to prevent, reintroduced one layer down in `video.overlay`. Read the code path a consumer will actually take, end to end, before calling it done. (Same lesson as braidio's `nw#27` note: check the artifact, not the log.)

## Neighbours

`burns` (saliency, Ken Burns), `mixing` (SRT burn-in — not tituli), `braidio.video.credits_card` (plain-list credits: `Credits.from_lines`), `muvid` (lyric vocabulary; its `calligram` solver is `tituli.rain`), `an` (motion as structure; an#155 is the boundary), `illustration` (sourcing the stills captions describe).
