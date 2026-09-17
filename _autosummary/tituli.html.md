# tituli

tituli — text in video: title cards, credits, captions and calligrams.

One model underneath: a [`Layout`](#tituli.Layout) of placed `Run`s on a
:class:`Frame` that knows as much (or as little) about the picture as you tell
it. Everything else is a convenience over that.

Quick start:

```default
from tituli import Frame, title_card, caption, credits_crawl, on_path, render

frame = Frame.blank((1920, 1080), color="#101014")
render(title_card("Il pleut", "Apollinaire, 1918", frame=frame), frame).save("title.png")

frame = Frame.from_image("still.jpg", delivery="youtube")   # add avoid=burns.salient_box
render(caption("Eliza Hamilton", "Ralph Earl, 1787 · public domain", frame=frame), frame).save("cap.png")
```

Optional layers, none imported here: `tituli[shaping]` (HarfBuzz engine),
`tituli[saliency]` (`burns` subject avoidance), `tituli[lacing]` (the
text-overlay body schema), `tituli[cli]` (`python -m tituli`).

### Functions

| [`title_card`](#tituli.title_card)(title[, subtitle, kicker, ...])         | An opening card: optional kicker, title, optional subtitle.                                                                                    |
|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| [`caption`](#tituli.caption)(text[, attribution, anchor, style, ...])   | A museum label over a picture: what is on screen, plus a tiny credit line.                                                                     |
| [`lower_third`](#tituli.lower_third)(name[, role, anchor, ...])             | Who is speaking: a name and a role, left-anchored, scrimmed if needed.                                                                         |
| [`note`](#tituli.note)(lines, \*, frame[, headline, anchor, ...])    | An editorial context card: an optional headline over equal-weight lines.                                                                       |
| [`intertitle`](#tituli.intertitle)(text, \*, frame[, style])               | A silent-film style card: serif italic prose, centred on the frame.                                                                            |
| [`fit`](#tituli.fit)(text, style, frame_height, \*, max_width, ...) | Wrap `text` complete, shrinking the type until it fits — never cutting it.                                                                     |
| [`truncate`](#tituli.truncate)(text, style, frame_height, \*, ...)       | Wrap and hard-truncate with an ellipsis at `max_lines` lines.                                                                                  |
| [`decide_ink`](#tituli.decide_ink)(frame, box, \*[, preferred])            | Choose ink and whether a scrim is needed under `box`.                                                                                          |
| [`credits_cards`](#tituli.credits_cards)(credits, \*, frame[, style, ...])    | Paginate the roll into cards that each fit the safe area, centred.                                                                             |
| [`credits_crawl`](#tituli.credits_crawl)(credits, \*, frame[, style])         | One tall layout and its total height in pixels (for [`tituli.video.crawl()`](tituli.video.html.md#tituli.video.crawl)). |
| [`credits_frame`](#tituli.credits_frame)(size[, style])                       | The canonical credits frame: near-black, so ink defaults to white.                                                                             |
| [`on_path`](#tituli.on_path)(text, \*[, shape, style, box, ...])        | Set `text` along a shape inside `box` (default: the safe area, inset).                                                                         |
| [`rain`](#tituli.rain)(lines, \*, frame[, style, box, slants, ...])  | *Il pleut*: each line a streak of upright letters falling across the frame.                                                                    |
| [`in_shape`](#tituli.in_shape)(text, mask, \*, frame[, style, box, ...]) | Pour prose into a silhouette (light = inside).                                                                                                 |
| [`resolve_shape`](#tituli.resolve_shape)(shape, box)                          | Turn a name, an SVG `d` string or a Path into a Path fitted to `box`.                                                                          |
| [`block`](#tituli.block)(text, style, frame, \*[, max_width, x, ...]) | Lay out prose as lines from the top-left corner `(x, y)`.                                                                                      |
| [`along_path`](#tituli.along_path)(text, path, style, frame, \*[, ...])    | Set `text` glyph by glyph along `path` (the path is the baseline).                                                                             |
| [`wrap`](#tituli.wrap)(text, style, frame_height, \*, max_width)     | Greedy word wrap on measured widths.                                                                                                           |
| [`measure`](#tituli.measure)(text, style, frame_height)                 | Width in pixels of `text` set in `style` on a frame of that height.                                                                            |
| [`fit_size`](#tituli.fit_size)(text, style, frame_height, \*, max_width) | Shrink `style.size` until `text` wraps within the given bounds.                                                                                |
| [`render`](#tituli.render)(layout, frame, \*[, t, engine])             | Render onto the frame: RGBA overlay if it has no background, else RGB.                                                                         |
| [`render_overlay`](#tituli.render_overlay)(layout, size, \*[, t, engine])      | The layout on a transparent canvas of `size` (RGBA).                                                                                           |
| [`frames`](#tituli.frames)(layout, frame, \*, duration[, fps, ...])    | Yield one image per video frame, honouring the runs' reveal envelopes.                                                                         |
| [`make_engine`](#tituli.make_engine)([name])                                | Resolve an engine by name: `"pillow"` (default) or `"harfbuzz"`.                                                                               |
| [`schedule_labels`](#tituli.schedule_labels)(spans, label_for, \*[, ...])       | One label per span, held `hold_s`, with the three rules built in.                                                                              |
| [`resolve`](#tituli.resolve)(overlays, \*[, min_readable_s])            | Enforce one overlay per slot at a time: the heavier wins, the lighter yields.                                                                  |
| [`families`](#tituli.families)()                                         | Sorted family names installed on this machine.                                                                                                 |
| [`find_font`](#tituli.find_font)(family, \*[, weight, italic, condensed]) | First installed family in the preference list, at the closest style.                                                                           |
| [`resolve_face`](#tituli.resolve_face)([family, weight, italic, condensed])  | Resolve a typeface request to a sized `Face`; never fails.                                                                                     |
| [`contrast_ratio`](#tituli.contrast_ratio)(a, b)                               | WCAG contrast ratio between two colours (1..21).                                                                                               |
| [`ink_for`](#tituli.ink_for)(\*, luminance[, light, dark])              | Pick the ink (light or dark) with more contrast against `luminance`.                                                                           |
| [`parse_color`](#tituli.parse_color)(color)                                 | Accept `"#rgb"`, `"#rrggbb"`, `"#rrggbbaa"`, a Pillow name or a tuple.                                                                         |
| [`safe_area`](#tituli.safe_area)(width, height, \*[, fraction])           | The centred box holding `fraction` of each dimension.                                                                                          |
| [`reserved_zones`](#tituli.reserved_zones)(delivery)                           | Normalised boxes a delivery target keeps for itself.                                                                                           |
| [`cover_fit`](#tituli.cover_fit)(img, size)                               | Scale `img` to fill `size` and crop the overflow, centred.                                                                                     |

### Classes

| [`Frame`](#tituli.Frame)(width, height[, color, image, avoid, ...])   | Size plus whatever else is known about the picture text will sit on.   |
|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| [`Layout`](#tituli.Layout)([runs, plates, meta])                       | Everything the renderer needs: runs on top of plates, in frame pixels. |
| [`Run`](#tituli.Run)(text, x, y, face, color[, angle, ...])         | A string drawn from a baseline origin, possibly rotated.               |
| [`Plate`](#tituli.Plate)(box, color[, kind, radius, solid])           | A backdrop drawn under the runs: a scrim, a box, a rule.               |
| [`Box`](#tituli.Box)(x0, y0, x1, y1)                                | A pixel-space rectangle `(x0, y0, x1, y1)`; edges are floats.          |
| [`Path`](#tituli.Path)(points)                                       | A polyline with an arc-length parameterisation.                        |
| [`TextStyle`](#tituli.TextStyle)([family, size, weight, italic, ...])     | How a run of text looks.                                               |
| [`Face`](#tituli.Face)(family, style, size, path[, index])           | A resolved, sized font ready to measure and draw with Pillow.          |
| [`Credits`](#tituli.Credits)([sections, title, closing, meta])          | The whole roll.                                                        |
| [`CreditsStyle`](#tituli.CreditsStyle)([title, heading, role, name, ...])    | The type ramp for a roll.                                              |
| [`Entry`](#tituli.Entry)(name[, role])                                | One credit line: `role` + `name`, a bare `name`, or prose.             |
| [`Section`](#tituli.Section)([heading, entries, kind])                  | A heading over a run of entries.                                       |
| [`Label`](#tituli.Label)(text[, attribution, key])                    | What goes on a museum label: the thing, and where it came from.        |
| [`Span`](#tituli.Span)(start, end, key[, data])                      | A time range of the cut showing one picture.                           |
| [`TimedOverlay`](#tituli.TimedOverlay)(layout, start, end[, slot, ...])      | A layout (or a thing to lay out) on screen from `start` to `end`.      |

### Exceptions

| [`TextDoesNotFit`](#tituli.TextDoesNotFit)(text, tried_size, ...)   | The text cannot be set completely without going below legibility.   |
|------------------------------------------------------------------------------------------|---------------------------------------------------------------------|

### *class* tituli.Box(x0, y0, x1, y1)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A pixel-space rectangle `(x0, y0, x1, y1)`; edges are floats.

#### *classmethod* from_norm(nb, width, height)

Scale a normalised `(x, y, w, h)` into a frame of that size.

* **Return type:**
  [`Box`](tituli.geometry.html.md#tituli.geometry.Box)

#### *classmethod* from_size(x, y, w, h)

Build from an origin and a size.

* **Return type:**
  [`Box`](tituli.geometry.html.md#tituli.geometry.Box)

#### inset(dx, dy=None)

Shrink by `dx` horizontally and `dy` (default `dx`) vertically.

* **Return type:**
  [`Box`](tituli.geometry.html.md#tituli.geometry.Box)

#### overlap_fraction(other)

Fraction of *this* box’s area covered by `other`.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

```pycon
>>> Box(0, 0, 10, 10).overlap_fraction(Box(5, 0, 20, 10))
0.5
```

#### to_norm(width, height)

The inverse of [`from_norm()`](#tituli.Box.from_norm).

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

### *class* tituli.Credits(sections=(), title='', closing=(), meta=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The whole roll.

#### *classmethod* from_dict(d)

Build from `{"title", "sections": [{"heading", "entries", "kind"}], "closing"}`.

The caller owns making the text presentable: tituli sets whatever it is
given, so a raw manifest — camera filenames as roles, `"Unknown
authorUnknown author"` from a concatenated field — comes out as a
designed card of raw manifest strings. Map titles, artists and
licences into readable roles and names first.

* **Return type:**
  [`Credits`](tituli.credits.html.md#tituli.credits.Credits)

#### *classmethod* from_lines(lines, , heading='Credits', title='')

The plain-list case (what `braidio.video.credits_card` takes).

Each line is set as prose, verbatim. Lines built from a fetch manifest
(`"<file> — <author> — <licence>"`) read as a terminal dump however
well they are typeset; prefer [`from_dict()`](#tituli.Credits.from_dict) with `{"role", "name"}`
entries (“Portrait of Eliza Hamilton”, “Ralph Earl, 1787 · public domain”).

* **Return type:**
  [`Credits`](tituli.credits.html.md#tituli.credits.Credits)

### *class* tituli.CreditsStyle(title=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.06, weight=700, italic=False, condensed=False, color=(255, 255, 255), tracking=-0.005, leading=1.2, case='as-is', align='center', opacity=1.0), heading=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.024, weight=500, italic=False, condensed=False, color=(255, 255, 255), tracking=0.22, leading=1.2, case='upper', align='center', opacity=0.75), role=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.026, weight=400, italic=False, condensed=False, color=(255, 255, 255), tracking=0.03, leading=1.2, case='as-is', align='right', opacity=0.8), name=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.032, weight=600, italic=False, condensed=False, color=(255, 255, 255), tracking=0.0, leading=1.2, case='as-is', align='left', opacity=1.0), line=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.03, weight=400, italic=False, condensed=False, color=(255, 255, 255), tracking=0.0, leading=1.4, case='as-is', align='center', opacity=1.0), ink=(255, 255, 255), background=(8, 8, 10))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The type ramp for a roll. One object so a film is one design.

### *class* tituli.Entry(name, role='')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One credit line: `role` + `name`, a bare `name`, or prose.

### *class* tituli.Face(family, style, size, path, index=0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A resolved, sized font ready to measure and draw with Pillow.

#### *property* ascent *: [int](https://docs.python.org/3/builtins/functions.html#int)*

Ascent in pixels.

#### *property* descent *: [int](https://docs.python.org/3/builtins/functions.html#int)*

Descent in pixels.

#### length(text)

Advance width of `text` in pixels.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### *property* line_height *: [int](https://docs.python.org/3/builtins/functions.html#int)*

Ascent + descent.

#### *property* pil *: FreeTypeFont*

The Pillow font object (cached per `(path, index, size)`).

#### with_size(size)

Same face at another pixel size.

* **Return type:**
  [`Face`](tituli.fonts.html.md#tituli.fonts.Face)

### *class* tituli.Frame(width, height, color=None, image=None, avoid=(), reserved=(), samples=())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Size plus whatever else is known about the picture text will sit on.

#### *classmethod* blank(size=(1920, 1080), , color=None)

Rung (a) when `color` is None, rung (b) when it is given.

* **Return type:**
  [`Frame`](tituli.frame.html.md#tituli.frame.Frame)

#### *classmethod* from_image(image, , avoid=None, size=None, delivery=None)

Rung (c), and rung (d) when `avoid` is given.

`image` may also be a **sequence** of frames (the stills a camera move
will pass through under the text): the first is what gets composited,
all of them feed [`luminance_stats()`](#tituli.Frame.luminance_stats), which then reports the *worst*
instant — so a scrim is as light as the whole window allows, not as
heavy as one frame demands.

`avoid` is normalised boxes, or a callable taking the PIL image and
returning one box or several (`burns.salient_box` fits directly). It
runs on every sampled frame. `size` cover-fits the picture(s) to the
frame first. `delivery` names a target whose reserved zones
(`"youtube"`: subtitle band + control bar) placement must keep clear.

* **Return type:**
  [`Frame`](tituli.frame.html.md#tituli.frame.Frame)

#### luminance_stats(box)

`(mean, stddev)` of relative luminance under `box`; None if unknown.

A high stddev means a busy patch — even a well-contrasted mean will not
keep every glyph readable, which is when a scrim earns its place.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### luminance_under(box)

Mean relative luminance of the pixels under `box`; None if unknown.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### *classmethod* over(stills, , avoid=None, size=None, delivery=None)

The frame a caption will sit on *over a time window* of stills.

The named entry point for the sequence case: the first still is what
gets composited, all of them are sampled, and `luminance_stats`
reports the worst instant — so a scrim over a Ken Burns move is as
light as the whole window allows. (`from_image` accepts a sequence
too; this name says what it is for.)

* **Return type:**
  [`Frame`](tituli.frame.html.md#tituli.frame.Frame)

#### overlap(box)

Fraction of `box` that covers something in `avoid` (0 when nothing).

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### place(size, , anchor='auto', region=None)

Where to put a block of `size`: a named anchor and its pixel box.

`anchor` may be one name, a preference list, or `"auto"` (the default
order). With rung (d) knowledge the candidate that least covers the
subject wins; ties fall to preference order.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Box`](tituli.geometry.html.md#tituli.geometry.Box)]

```pycon
>>> f = Frame.blank((1000, 500))
>>> f.place((200, 50), anchor="bottom")[0]
'bottom'
```

#### *property* safe *: [Box](tituli.geometry.html.md#tituli.geometry.Box)*

The title-safe box (SMPTE ST 2046-1, 90 %).

#### with_avoid(avoid)

Same frame with (additional) regions to keep clear.

* **Return type:**
  [`Frame`](tituli.frame.html.md#tituli.frame.Frame)

#### with_delivery(delivery)

Same frame, placement keeping clear of that target’s reserved zones.

* **Return type:**
  [`Frame`](tituli.frame.html.md#tituli.frame.Frame)

### *class* tituli.Label(text, attribution='', key=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What goes on a museum label: the thing, and where it came from.

### *class* tituli.Layout(runs=(), plates=(), meta=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Everything the renderer needs: runs on top of plates, in frame pixels.

#### bbox()

Bounds of the runs (plates excluded).

* **Return type:**
  [`Box`](tituli.geometry.html.md#tituli.geometry.Box)

#### *property* duration_hint *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Latest `t_full` among the runs (0 when untimed).

#### moved_to(box)

Translate so the runs’ bbox top-left lands on `box`’s top-left.

* **Return type:**
  [`Layout`](tituli.layout.html.md#tituli.layout.Layout)

#### staggered(, start=0.0, step, ramp)

Reveal runs one after another: run `i` starts at `start + i*step`.

* **Return type:**
  [`Layout`](tituli.layout.html.md#tituli.layout.Layout)

#### with_timing(t_in, t_full)

Give every run the same reveal envelope.

* **Return type:**
  [`Layout`](tituli.layout.html.md#tituli.layout.Layout)

### *class* tituli.Path(points)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A polyline with an arc-length parameterisation.

Build one with the constructors (`line()`, [`arc()`](#tituli.Path.arc), [`wave()`](#tituli.Path.wave),
[`bezier()`](#tituli.Path.bezier), `polyline()`, [`from_svg()`](#tituli.Path.from_svg), [`from_function()`](#tituli.Path.from_function)) and
query it by distance along the curve: `point(s)` and `angle(s)` (degrees,
clockwise-positive on screen because y points down).

#### angle(s)

Tangent direction at `s` in degrees (0 = rightwards, 90 = down).

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### *classmethod* arc(center, radius, start_deg, end_deg, , samples=512)

Circular arc; angles in degrees, 0 = right, 90 = down (screen coords).

* **Return type:**
  [`Path`](tituli.geometry.html.md#tituli.geometry.Path)

#### *classmethod* bezier(\*controls, samples=512)

A Bézier curve of any degree through `controls` (De Casteljau).

* **Return type:**
  [`Path`](tituli.geometry.html.md#tituli.geometry.Path)

#### *classmethod* circle(center, radius, , start_deg=-90.0)

A full circle starting at the top by default, running clockwise.

* **Return type:**
  [`Path`](tituli.geometry.html.md#tituli.geometry.Path)

#### *property* closed *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Whether the path ends where it starts (a circle, a closed SVG path).

```pycon
>>> Path.circle((0, 0), 10).closed, Path.line((0, 0), (1, 1)).closed
(True, False)
```

#### fit(box, , keep_aspect=True)

Scale and translate so the path’s bounding box fills `box`.

Degenerate axes (a horizontal line has zero height) are centred rather
than scaled.

* **Return type:**
  [`Path`](tituli.geometry.html.md#tituli.geometry.Path)

#### *classmethod* from_function(fn, , samples=512)

Sample `fn(t)` for `t` in `[0, 1]`.

* **Return type:**
  [`Path`](tituli.geometry.html.md#tituli.geometry.Path)

#### *classmethod* from_svg(d)

Parse an SVG path `d` string (M L H V C S Q T Z, absolute or relative).

Arcs (`A`) are not supported — approximate them with a Bézier.

* **Return type:**
  [`Path`](tituli.geometry.html.md#tituli.geometry.Path)

```pycon
>>> Path.from_svg("M 0 0 L 10 0 L 10 10").length
20.0
```

#### point(s)

Position at arc length `s` (clamped to the path).

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### *classmethod* wave(start, end, , amplitude, cycles=1.0, samples=512)

A sine wave along the segment `start -> end`.

* **Return type:**
  [`Path`](tituli.geometry.html.md#tituli.geometry.Path)

### *class* tituli.Plate(box, color, kind='box', radius=0.0, solid=(0.5, 0.5))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A backdrop drawn under the runs: a scrim, a box, a rule.

### *class* tituli.Run(text, x, y, face, color, angle=0.0, opacity=1.0, tracking=0.0, unit='line', index=0, t_in=None, t_full=None, tags=())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A string drawn from a baseline origin, possibly rotated.

#### bbox()

Axis-aligned bounds (ignores rotation — fine for placement).

* **Return type:**
  [`Box`](tituli.geometry.html.md#tituli.geometry.Box)

### *class* tituli.Section(heading='', entries=(), kind='auto')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A heading over a run of entries. `kind` picks the treatment:

`"pairs"` role/name on a gutter (cast, crew); `"list"` centred names;
`"prose"` wrapped small text (licences, thanks).

### *class* tituli.Span(start, end, key, data=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A time range of the cut showing one picture. `key` identifies the picture.

(Named `Span` rather than `Panel` so it never collides with
`braidio.video.Panel`, which callers of both will import alongside it.)

### *exception* tituli.TextDoesNotFit(text, tried_size, lines_at_min, max_lines)

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

The text cannot be set completely without going below legibility.

Raised rather than truncating, because the caller is the only one who can
decide what to do: shorten the wording (“1981 · Central Park, live” ->
“1981 · Central Park”, or “1981”), give it more lines, widen the box, or
drop the overlay. Silently ellipsising picks the one option nobody wants —
a label that is *wrong* rather than absent.

#### text

what could not be set.

#### tried_size

the smallest size attempted, as a fraction of frame height.

#### lines_at_min

how many lines it still needed there.

#### max_lines

how many were allowed.

### *class* tituli.TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.04, weight=400, italic=False, condensed=False, color=(255, 255, 255), tracking=0.0, leading=1.2, case='as-is', align='center', opacity=1.0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

How a run of text looks. All fields keyword-only; build variants with `with_`.

#### face(frame_height)

The resolved, sized font for this style.

* **Return type:**
  [`Face`](tituli.fonts.html.md#tituli.fonts.Face)

#### px(frame_height)

Font size in pixels for a frame of that height.

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

#### with_(\*\*changes)

A copy with some fields replaced.

* **Return type:**
  [`TextStyle`](tituli.style.html.md#tituli.style.TextStyle)

```pycon
>>> TextStyle().with_(weight=700).weight
700
```

### *class* tituli.TimedOverlay(layout, start, end, slot='top-left', weight=1, fade=0.45, payload=None, meta=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A layout (or a thing to lay out) on screen from `start` to `end`.

`slot` names the region it occupies; `weight` orders overlays that
contend for a slot — the heavier suppresses the lighter, never stacks.
`payload` is whatever the caller wants to carry to rendering (a
[`Label`](#tituli.Label), a dict, …); `layout` is filled in once rendered.

### tituli.along_path(text, path, style, frame, , start=0.0, align='start', offset=0.0, upright=False, color=None, tags=())

Set `text` glyph by glyph along `path` (the path is the baseline).

Each glyph’s origin is the point at its arc length and it is rotated to the
tangent there — unless `upright` (a calligram convention: letters stay
vertical while their *positions* follow the shape). `offset` shifts the
baseline perpendicular to the path (negative = above, in screen terms).
`align` positions the whole string on the path from `start`.

Text longer than the path keeps its spacing and runs off the end — that is
reported in `meta["overflow"]` rather than silently squeezed.

* **Return type:**
  [`Layout`](tituli.layout.html.md#tituli.layout.Layout)

### tituli.block(text, style, frame, , max_width=None, x=0.0, y=0.0, color=None, unit='line', tags=())

Lay out prose as lines from the top-left corner `(x, y)`.

`text` is a string (wrapped to `max_width` when given) or pre-broken
lines. Alignment follows `style.align` within `max_width` (or the widest
line when no width is given). `unit="glyph"` emits one run per character
(needed for tracking and for per-glyph reveals).

* **Return type:**
  [`Layout`](tituli.layout.html.md#tituli.layout.Layout)

### tituli.caption(text, attribution='', , frame, anchor='auto', style=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.04, weight=600, italic=False, condensed=False, color=(255, 255, 255), tracking=0.0, leading=1.25, case='as-is', align='left', opacity=1.0), attribution_style=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.02, weight=400, italic=False, condensed=False, color=(255, 255, 255), tracking=0.03, leading=1.2, case='as-is', align='left', opacity=0.85), max_lines=3, max_width=0.55, ink=None, scrim=None, accent=True, on_overflow='fit')

A museum label over a picture: what is on screen, plus a tiny credit line.

`text` is wrapped to `max_width` of the safe box and **shrunk to fit**
within `max_lines` rather than cut; `attribution` is set small and
slightly transparent — present enough to credit, small enough not to
compete. If the words cannot be set legibly this raises
[`TextDoesNotFit`](#tituli.TextDoesNotFit); pass `on_overflow="truncate"` for text whose
length you do not control (see `OVERFLOW_POLICIES`). Placement avoids the
frame’s `avoid` boxes and its delivery target’s reserved zones; the
scrim is a 2-D corner falloff cut to the measured block.

* **Return type:**
  [`Layout`](tituli.layout.html.md#tituli.layout.Layout)

### tituli.contrast_ratio(a, b)

WCAG contrast ratio between two colours (1..21).

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

```pycon
>>> round(contrast_ratio("#777", "#fff"), 2)
4.48
```

### tituli.cover_fit(img, size)

Scale `img` to fill `size` and crop the overflow, centred.

* **Return type:**
  `Image`

```pycon
>>> cover_fit(Image.new("RGB", (100, 50)), (50, 50)).size
(50, 50)
```

### tituli.credits_cards(credits, , frame, style=CreditsStyle(title=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.06, weight=700, italic=False, condensed=False, color=(255, 255, 255), tracking=-0.005, leading=1.2, case='as-is', align='center', opacity=1.0), heading=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.024, weight=500, italic=False, condensed=False, color=(255, 255, 255), tracking=0.22, leading=1.2, case='upper', align='center', opacity=0.75), role=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.026, weight=400, italic=False, condensed=False, color=(255, 255, 255), tracking=0.03, leading=1.2, case='as-is', align='right', opacity=0.8), name=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.032, weight=600, italic=False, condensed=False, color=(255, 255, 255), tracking=0.0, leading=1.2, case='as-is', align='left', opacity=1.0), line=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.03, weight=400, italic=False, condensed=False, color=(255, 255, 255), tracking=0.0, leading=1.4, case='as-is', align='center', opacity=1.0), ink=(255, 255, 255), background=(8, 8, 10)), max_cards=None)

Paginate the roll into cards that each fit the safe area, centred.

A heading is never orphaned at the bottom of a card. Raises when
`max_cards` would force truncation — losing an attribution silently is a
licence failure invisible to the person responsible for it.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Layout`](tituli.layout.html.md#tituli.layout.Layout)]

### tituli.credits_crawl(credits, , frame, style=CreditsStyle(title=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.06, weight=700, italic=False, condensed=False, color=(255, 255, 255), tracking=-0.005, leading=1.2, case='as-is', align='center', opacity=1.0), heading=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.024, weight=500, italic=False, condensed=False, color=(255, 255, 255), tracking=0.22, leading=1.2, case='upper', align='center', opacity=0.75), role=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.026, weight=400, italic=False, condensed=False, color=(255, 255, 255), tracking=0.03, leading=1.2, case='as-is', align='right', opacity=0.8), name=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.032, weight=600, italic=False, condensed=False, color=(255, 255, 255), tracking=0.0, leading=1.2, case='as-is', align='left', opacity=1.0), line=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.03, weight=400, italic=False, condensed=False, color=(255, 255, 255), tracking=0.0, leading=1.4, case='as-is', align='center', opacity=1.0), ink=(255, 255, 255), background=(8, 8, 10)))

One tall layout and its total height in pixels (for [`tituli.video.crawl()`](tituli.video.html.md#tituli.video.crawl)).

The layout starts one frame-height down and ends one frame-height before
its bottom, so the crawl enters from an empty frame and leaves to one.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Layout`](tituli.layout.html.md#tituli.layout.Layout), [`int`](https://docs.python.org/3/builtins/functions.html#int)]

### tituli.credits_frame(size, style=CreditsStyle(title=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.06, weight=700, italic=False, condensed=False, color=(255, 255, 255), tracking=-0.005, leading=1.2, case='as-is', align='center', opacity=1.0), heading=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.024, weight=500, italic=False, condensed=False, color=(255, 255, 255), tracking=0.22, leading=1.2, case='upper', align='center', opacity=0.75), role=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.026, weight=400, italic=False, condensed=False, color=(255, 255, 255), tracking=0.03, leading=1.2, case='as-is', align='right', opacity=0.8), name=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.032, weight=600, italic=False, condensed=False, color=(255, 255, 255), tracking=0.0, leading=1.2, case='as-is', align='left', opacity=1.0), line=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.03, weight=400, italic=False, condensed=False, color=(255, 255, 255), tracking=0.0, leading=1.4, case='as-is', align='center', opacity=1.0), ink=(255, 255, 255), background=(8, 8, 10)))

The canonical credits frame: near-black, so ink defaults to white.

* **Return type:**
  [`Frame`](tituli.frame.html.md#tituli.frame.Frame)

### tituli.decide_ink(frame, box, , preferred=None)

Choose ink and whether a scrim is needed under `box`.

Rung (a) (nothing known): white on a dark scrim, the universal default.
Rung (b)/(c): the ink with more contrast; a scrim only when contrast is still
short of WCAG 4.5:1 or the patch is busy. `preferred` is honoured when it
already has enough contrast.

* **Return type:**
  [`InkDecision`](tituli.compose.html.md#tituli.compose.InkDecision)

### tituli.families()

Sorted family names installed on this machine.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### tituli.find_font(family, , weight=400, italic=False, condensed=False)

First installed family in the preference list, at the closest style.

`family` may be one name or a preference list. A path to a font file is
accepted too, and wins outright.

* **Return type:**
  [`FontFile`](tituli.fonts.html.md#tituli.fonts.FontFile) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

```pycon
>>> find_font("definitely-not-installed-xyz") is None
True
```

### tituli.fit(text, style, frame_height, , max_width, max_lines, min_size=0.022)

Wrap `text` complete, shrinking the type until it fits — never cutting it.

Returns the wrapped text and the (possibly smaller) style to set it in.

\*\*Why this exists rather than [`truncate()`](#tituli.truncate).\*\* Type here is sized as a
fraction of frame *height* but has to fit the frame’s *width*. On a portrait
frame those pull apart hard: a lower third at 0.042 of height is 81px tall on
a 1080x1920 frame and has to fit inside ~1080px of width, so a perfectly
ordinary line overflows. Truncating then produced a shipped caption reading
`1981 · Centr…` — which is not a shortened label, it is a wrong one.

Shrinking is tried first because it is invisible to the viewer and costs
nothing. Only when shrinking would make the text unreadable does this raise
[`TextDoesNotFit`](#tituli.TextDoesNotFit), handing the decision back to whoever wrote the words.

* **Parameters:**
  * **text** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – the words, set in full or not at all.
  * **style** ([`TextStyle`](tituli.style.html.md#tituli.style.TextStyle)) – the style to start from; its `size` is the ceiling.
  * **frame_height** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – pixels, for resolving em sizes.
  * **max_width** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – pixels available.
  * **max_lines** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – how many lines the design allows.
  * **min_size** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – legibility floor, as a fraction of frame height.
* **Raises:**
  [**TextDoesNotFit**](#tituli.TextDoesNotFit) – when even `min_size` needs more than `max_lines`.
* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`TextStyle`](tituli.style.html.md#tituli.style.TextStyle)]

### Examples

```pycon
>>> from tituli.style import TextStyle
>>> st = TextStyle(size=0.05)
>>> body, used = fit("short", st, 1000.0, max_width=900, max_lines=1)
>>> body, used.size == st.size
('short', True)
```

### tituli.fit_size(text, style, frame_height, , max_width, max_height=None, min_size=0.012, step=0.9)

Shrink `style.size` until `text` wraps within the given bounds.

Shrinks geometrically by `step` and never below `min_size` (a fraction
of frame height, like `size` itself).

* **Return type:**
  [`TextStyle`](tituli.style.html.md#tituli.style.TextStyle)

### tituli.frames(layout, frame, , duration, fps=30.0, engine=None, hold_after=0.0)

Yield one image per video frame, honouring the runs’ reveal envelopes.

`duration` is the whole clip; the last reveal completes at
`layout.duration_hint` and the layout then holds. Frames are rendered
lazily so a long clip never sits in memory at once.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[`Image`]

### tituli.in_shape(text, mask, , frame, style=TextStyle(family=('Georgia', 'Palatino', 'Baskerville', 'Liberation Serif', 'DejaVu Serif', 'Times New Roman'), size=0.035, weight=400, italic=False, condensed=False, color=(17, 17, 17), tracking=0.0, leading=1.2, case='as-is', align='left', opacity=1.0), box=None, repeat=True)

Pour prose into a silhouette (light = inside). See [`tituli.layout.fill_shape()`](tituli.layout.html.md#tituli.layout.fill_shape).

* **Return type:**
  [`Layout`](tituli.layout.html.md#tituli.layout.Layout)

### tituli.ink_for(, luminance, light=(255, 255, 255), dark=(17, 17, 17))

Pick the ink (light or dark) with more contrast against `luminance`.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)]

### tituli.intertitle(text, , frame, style=None)

A silent-film style card: serif italic prose, centred on the frame.

* **Return type:**
  [`Layout`](tituli.layout.html.md#tituli.layout.Layout)

### tituli.lower_third(name, role='', , frame, anchor='bottom-left', name_style=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.042, weight=700, italic=False, condensed=False, color=(255, 255, 255), tracking=0.0, leading=1.2, case='as-is', align='left', opacity=1.0), role_style=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.026, weight=400, italic=False, condensed=False, color=(255, 255, 255), tracking=0.04, leading=1.2, case='as-is', align='left', opacity=0.9), ink=None, scrim=None, on_overflow='fit')

Who is speaking: a name and a role, left-anchored, scrimmed if needed.

Respects the frame’s delivery zones — with `delivery="youtube"` the block
moves above the subtitle band rather than into it.

The name and role are **shrunk to fit** rather than cut, and
[`TextDoesNotFit`](#tituli.TextDoesNotFit) is raised if they cannot be set legibly. A lower
third reading `1981 · Centr…` once shipped in a finished film; that is not
a shortened label but a false one.

* **Return type:**
  [`Layout`](tituli.layout.html.md#tituli.layout.Layout)

### tituli.make_engine(name='pillow')

Resolve an engine by name: `"pillow"` (default) or `"harfbuzz"`.

* **Return type:**
  `Engine`

### tituli.measure(text, style, frame_height)

Width in pixels of `text` set in `style` on a frame of that height.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### tituli.note(lines, , frame, headline='', anchor='top-left', headline_style=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.055, weight=700, italic=False, condensed=False, color=(255, 255, 255), tracking=0.0, leading=1.15, case='as-is', align='left', opacity=1.0), line_style=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.03, weight=400, italic=False, condensed=False, color=(255, 255, 255), tracking=0.0, leading=1.4, case='as-is', align='left', opacity=0.92), max_width=0.62, ink=None, scrim=None, accent=True, on_overflow='fit')

An editorial context card: an optional headline over equal-weight lines.

The block for what the audio assumes and a cold viewer does not have
(“what *Hamilton* is”, “Philip died at 19”). Heavier than a caption —
schedule it with a higher `weight` so the two never share a corner. Each
line wraps to `max_width` of the safe box, shrinking to fit within
`_NOTE_MAX_LINES` rows rather than being cut; every line shares the
smallest size any of them needed, so the block reads as one block.
Raises [`TextDoesNotFit`](#tituli.TextDoesNotFit) if a line cannot be set legibly.

* **Return type:**
  [`Layout`](tituli.layout.html.md#tituli.layout.Layout)

### tituli.on_path(text, , shape='wave', frame, style=TextStyle(family=('Georgia', 'Palatino', 'Baskerville', 'Liberation Serif', 'DejaVu Serif', 'Times New Roman'), size=0.035, weight=400, italic=False, condensed=False, color=(17, 17, 17), tracking=0.0, leading=1.2, case='as-is', align='left', opacity=1.0), box=None, upright=False, align='center', fit_text=True)

Set `text` along a shape inside `box` (default: the safe area, inset).

With `fit_text` the type is shrunk until the whole string fits the path
length (never clipped); the resulting size is in `meta["size"]`.

* **Return type:**
  [`Layout`](tituli.layout.html.md#tituli.layout.Layout)

### tituli.parse_color(color)

Accept `"#rgb"`, `"#rrggbb"`, `"#rrggbbaa"`, a Pillow name or a tuple.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)]

```pycon
>>> parse_color("#fff")
(255, 255, 255, 255)
>>> parse_color((10, 20, 30))
(10, 20, 30, 255)
```

### tituli.rain(lines, , frame, style=TextStyle(family=('Georgia', 'Palatino', 'Baskerville', 'Liberation Serif', 'DejaVu Serif', 'Times New Roman'), size=0.035, weight=400, italic=False, condensed=False, color=(17, 17, 17), tracking=0.0, leading=1.2, case='as-is', align='left', opacity=1.0), box=None, slants=(0.186, 0.22, 0.257, 0.298, 0.353), head_offsets=(0.0, 7.0, 11.7, 16.4, 19.3), size_ratio=0.86)

*Il pleut*: each line a streak of upright letters falling across the frame.

Wants a portrait frame. `slants` (dx per step down) and `head_offsets`
(where each streak starts, in slot units) are shape parameters, not
coordinates — the defaults are Apollinaire’s.

* **Return type:**
  [`Layout`](tituli.layout.html.md#tituli.layout.Layout)

### tituli.render(layout, frame, , t=None, engine=None)

Render onto the frame: RGBA overlay if it has no background, else RGB.

`engine` is the rasteriser seam (default Pillow; see [`tituli.shaping`](tituli.shaping.html.md#module-tituli.shaping)).

* **Return type:**
  `Image`

### tituli.render_overlay(layout, size, , t=None, engine=None)

The layout on a transparent canvas of `size` (RGBA).

* **Return type:**
  `Image`

### tituli.reserved_zones(delivery)

Normalised boxes a delivery target keeps for itself.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)], [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

```pycon
>>> reserved_zones("youtube")
((0.0, 0.78, 1.0, 0.22),)
>>> reserved_zones(None)
()
```

### tituli.resolve(overlays, , min_readable_s=1.5)

Enforce one overlay per slot at a time: the heavier wins, the lighter yields.

A lighter overlay is truncated to the time before the heavier one starts
and dropped only if what remains is under `min_readable_s` (see
`_yield_to`). Equal weights that collide raise — that is an authoring
error, not a rule. Use this on a hand-built list to guarantee two weights
never stack.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`TimedOverlay`](tituli.schedule.html.md#tituli.schedule.TimedOverlay)]

### tituli.resolve_face(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), , size, weight=400, italic=False, condensed=False)

Resolve a typeface request to a sized `Face`; never fails.

Falls back to Pillow’s embedded Aileron when nothing in the list is installed,
so a render on a fontless CI box still produces a real (if plainer) result.

* **Return type:**
  [`Face`](tituli.fonts.html.md#tituli.fonts.Face)

### tituli.resolve_shape(shape, box)

Turn a name, an SVG `d` string or a Path into a Path fitted to `box`.

Names: `"line"`, `"circle"`, `"arc"`, `"wave"`, `"diagonal"`,
`"s-curve"`. Anything starting with `M`/`m` is parsed as SVG.

* **Return type:**
  [`Path`](tituli.geometry.html.md#tituli.geometry.Path)

### tituli.safe_area(width, height, , fraction=0.9)

The centred box holding `fraction` of each dimension.

* **Return type:**
  [`Box`](tituli.geometry.html.md#tituli.geometry.Box)

```pycon
>>> safe_area(1000, 500)
Box(x0=50.0, y0=25.0, x1=950.0, y1=475.0)
```

### tituli.schedule_labels(spans, label_for, , suppressed_by=(), hold_s=4.6, repeat_gap_s=150.0, min_readable_s=1.5, slot='top-left', weight=1)

One label per span, held `hold_s`, with the three rules built in.

* **first appearance**: a picture is labelled the first time it is shown;
* **repeat gap**: and again only if `repeat_gap_s` has passed since;
* **suppression**: a heavier overlay in the same slot owns that moment. The
  label is *truncated* to the time before the heavier one starts, and
  skipped only if what remains is shorter than `min_readable_s` — and a
  skipped label is *not recorded as shown*, so it gets its next chance.

`label_for` returns a [`Label`](#tituli.Label) or `UNLABELLED`; `None` raises.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`TimedOverlay`](tituli.schedule.html.md#tituli.schedule.TimedOverlay)]

### tituli.title_card(title, subtitle='', , frame, kicker='', anchor='center', title_style=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.075, weight=700, italic=False, condensed=False, color=(255, 255, 255), tracking=-0.01, leading=1.1, case='as-is', align='center', opacity=1.0), subtitle_style=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.032, weight=400, italic=False, condensed=False, color=(255, 255, 255), tracking=0.02, leading=1.3, case='as-is', align='center', opacity=1.0), kicker_style=TextStyle(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), size=0.022, weight=500, italic=False, condensed=False, color=(255, 255, 255), tracking=0.18, leading=1.2, case='upper', align='center', opacity=1.0), ink=None, scrim=None)

An opening card: optional kicker, title, optional subtitle.

Fits the title to 80 % of the safe width (shrinking, never clipping), stacks
the parts with a gap proportional to the type, places the block at
`anchor` (subject-avoiding when the frame knows the picture), and picks
ink by the frame’s contrast. `scrim` forces a scrim on/off; None decides.

* **Return type:**
  [`Layout`](tituli.layout.html.md#tituli.layout.Layout)

### tituli.truncate(text, style, frame_height, , max_width, max_lines)

Wrap and hard-truncate with an ellipsis at `max_lines` lines.

For text whose length you do not control (a licence template blob pasted
into an artist field). The result always fits.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### tituli.wrap(text, style, frame_height, , max_width)

Greedy word wrap on measured widths. Explicit newlines are honoured.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

```pycon
>>> from tituli.style import CAPTION
>>> lines = wrap("one two three four five six", CAPTION, 1080, max_width=300)
>>> len(lines) >= 2 and all(measure(l, CAPTION, 1080) <= 300 for l in lines)
True
```

### Modules

| [`bodies`](tituli.bodies.html.md#module-tituli.bodies)       | A lacing body schema for a rendered caption (`pip install tituli[lacing]`).             |
|------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| [`calligram`](tituli.calligram.html.md#module-tituli.calligram) | Calligrams and concrete poems: text whose shape is part of the meaning.                 |
| [`color`](tituli.color.html.md#module-tituli.color)         | Colours, WCAG contrast, and the ink-for-this-background decision.                       |
| [`compose`](tituli.compose.html.md#module-tituli.compose)     | The composed pieces: title cards, captions with attribution, lower thirds.              |
| [`credits`](tituli.credits.html.md#module-tituli.credits)     | Credits: structured data in, designed cards or a crawl out.                             |
| [`fonts`](tituli.fonts.html.md#module-tituli.fonts)         | Font discovery with no bundled fonts.                                                   |
| [`frame`](tituli.frame.html.md#module-tituli.frame)         | The frame: what the layout engine is allowed to know about the picture.                 |
| [`geometry`](tituli.geometry.html.md#module-tituli.geometry)   | Boxes, anchors, safe areas and parametric paths — the coordinate vocabulary.            |
| [`layout`](tituli.layout.html.md#module-tituli.layout)       | The layout model: placed runs of text, and the engines that place them.                 |
| [`schedule`](tituli.schedule.html.md#module-tituli.schedule)   | When overlays appear: timed overlays, and a scheduler that owns the rules.              |
| [`shaping`](tituli.shaping.html.md#module-tituli.shaping)     | Optional engine: HarfBuzz shaping + FreeType rendering (`pip install tituli[shaping]`). |
| [`style`](tituli.style.html.md#module-tituli.style)         | Text styles and the tasteful presets.                                                   |
| [`tools`](tituli.tools.html.md#module-tituli.tools)         | The SSOT of dispatchable operations: flat, JSON-able in, JSON-able out.                 |
| [`video`](tituli.video.html.md#module-tituli.video)         | Video output through ffmpeg: stills to clips, overlays onto footage, crawls.            |
