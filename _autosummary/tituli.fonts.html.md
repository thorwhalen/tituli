# tituli.fonts

Font discovery with no bundled fonts.

`tituli` never ships a typeface (licensing), so a *typeface request* — a family
name, weight and slant — is resolved against the fonts already installed on the
machine, and falls back to the scalable face Pillow embeds (Aileron). That fallback
is a real font, not a stub, so every render works out of the box on a bare CI
runner; it just looks better on a machine with Helvetica Neue.

Resolution order is a *preference list*: the first family found wins.

```pycon
>>> face = resolve_face(["No Such Family", "DejaVu Sans"], size=48)
>>> face.size
48
>>> face.family in ("DejaVu Sans", "Aileron") or isinstance(face.family, str)
True
```

### Functions

| [`families`](#tituli.fonts.families)()                                         | Sorted family names installed on this machine.                       |
|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`find_font`](#tituli.fonts.find_font)(family, \*[, weight, italic, condensed]) | First installed family in the preference list, at the closest style. |
| [`font_dirs`](#tituli.fonts.font_dirs)()                                        | Platform font directories that exist on this machine.                |
| [`font_index`](#tituli.fonts.font_index)()                                       | Installed faces grouped by family name.                              |
| [`resolve_face`](#tituli.fonts.resolve_face)([family, weight, italic, condensed])  | Resolve a typeface request to a sized `Face`; never fails.           |

### Classes

| [`Face`](#tituli.fonts.Face)(family, style, size, path[, index])   | A resolved, sized font ready to measure and draw with Pillow.   |
|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| [`FontFile`](#tituli.fonts.FontFile)(path, index, family, style)       | One face inside a font file (a `.ttc` holds several).           |

### *class* tituli.fonts.Face(family, style, size, path, index=0)

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
  [`Face`](#tituli.fonts.Face)

### *class* tituli.fonts.FontFile(path, index, family, style)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One face inside a font file (a `.ttc` holds several).

#### *property* condensed *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Whether the style name says condensed/narrow/compressed.

#### *property* italic *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Whether the style name says italic/oblique.

#### *property* weight *: [int](https://docs.python.org/3/builtins/functions.html#int)*

CSS-style weight parsed from the style name (`"Bold"` -> 700).

### tituli.fonts.families()

Sorted family names installed on this machine.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### tituli.fonts.find_font(family, , weight=400, italic=False, condensed=False)

First installed family in the preference list, at the closest style.

`family` may be one name or a preference list. A path to a font file is
accepted too, and wins outright.

* **Return type:**
  [`FontFile`](#tituli.fonts.FontFile) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

```pycon
>>> find_font("definitely-not-installed-xyz") is None
True
```

### tituli.fonts.font_dirs()

Platform font directories that exist on this machine.

Extra directories can be prepended with `TITULI_FONT_DIRS` (`os.pathsep`
separated), which is also how a project supplies its own licensed fonts.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]

### tituli.fonts.font_index()

Installed faces grouped by family name. Scanned once per process.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`FontFile`](#tituli.fonts.FontFile), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]]

```pycon
>>> idx = font_index()
>>> all(isinstance(k, str) for k in idx)
True
```

### tituli.fonts.resolve_face(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), , size, weight=400, italic=False, condensed=False)

Resolve a typeface request to a sized `Face`; never fails.

Falls back to Pillow’s embedded Aileron when nothing in the list is installed,
so a render on a fontless CI box still produces a real (if plainer) result.

* **Return type:**
  [`Face`](#tituli.fonts.Face)
