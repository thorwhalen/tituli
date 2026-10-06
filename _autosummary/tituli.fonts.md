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

### Module Attributes

| [`EMBEDDED`](#tituli.fonts.EMBEDDED)   | A family request that means *Pillow's embedded face, and never the system*.   |
|-------------------------------------------------------------|-------------------------------------------------------------------------------|

### Functions

| [`face_bytes`](#tituli.fonts.face_bytes)(face)                                   | The bytes of the font file behind `face` — the embedded face's too.                                             |
|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| [`face_digest`](#tituli.fonts.face_digest)(face)                                  | `sha256` of [`face_bytes()`](#tituli.fonts.face_bytes) — what makes two faces the same face. |
| [`families`](#tituli.fonts.families)()                                         | Sorted family names installed on this machine.                                                                  |
| [`find_font`](#tituli.fonts.find_font)(family, \*[, weight, italic, condensed]) | First installed family in the preference list, at the closest style.                                            |
| [`font_dirs`](#tituli.fonts.font_dirs)()                                        | Platform font directories that exist on this machine.                                                           |
| [`font_index`](#tituli.fonts.font_index)()                                       | Installed faces grouped by family name.                                                                         |
| [`resolve_face`](#tituli.fonts.resolve_face)([family, weight, italic, ...])        | Resolve a typeface request to a sized `Face`; never fails.                                                      |

### Classes

| [`Face`](#tituli.fonts.Face)(family, style, size, path[, index, ...])   | A resolved, sized font ready to measure and draw with Pillow.   |
|--------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| [`FontFile`](#tituli.fonts.FontFile)(path, index, family, style)            | One face inside a font file (a `.ttc` holds several).           |

### tituli.fonts.EMBEDDED *= 'tituli:embedded'*

A family request that means *Pillow’s embedded face, and never the system*.
In a preference list it is a stop: the names before it are looked up as
usual, and if none is installed the embedded face is used without scanning
further. Alone (or first) it never scans the system at all, so the result is
the same bytes on every machine with the same Pillow — the deterministic
choice for a caller whose output must not depend on the installed fonts.
(Asking for `"Aileron"` by name is not the same thing: a machine that has
Aileron installed would resolve to *that* file.)

### *class* tituli.fonts.Face(family, style, size, path, index=0, features=())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A resolved, sized font ready to measure and draw with Pillow.

#### *property* applied_features *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), ...]*

The requested [`features`](#tituli.fonts.Face.features) this font has, so the ones measured and
outlined with; a requested tag missing here was not applied.

```pycon
>>> resolve_face(EMBEDDED, size=12).applied_features
()
```

#### *property* ascent *: [int](https://docs.python.org/3/builtins/functions.html#int)*

Ascent in pixels.

#### *property* descent *: [int](https://docs.python.org/3/builtins/functions.html#int)*

Descent in pixels.

#### features *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), ...]* *= ()*

OpenType feature tags the style asked for (tituli#4); which of them the
font has is [`applied_features`](#tituli.fonts.Face.applied_features).

#### length(text)

Advance width of `text` in pixels.

With [`applied_features`](#tituli.fonts.Face.applied_features), the advances of the substituted glyphs
([`tituli.features.featured_length()`](tituli.features.md#tituli.features.featured_length)): the font’s design advances,
without hinting or kerning, which is what tabular figures are for.

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

### tituli.fonts.face_bytes(face)

The bytes of the font file behind `face` — the embedded face’s too.

Pillow keeps the embedded face’s bytes on the font object it builds
(`font_bytes`), so the fallback has an identity like any file does.

* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)

```pycon
>>> face_bytes(resolve_face(EMBEDDED, size=12))[:4] in (b"\x00\x01\x00\x00", b"true", b"OTTO")
True
```

### tituli.fonts.face_digest(face)

`sha256` of [`face_bytes()`](#tituli.fonts.face_bytes) — what makes two faces the same face.

A family name is not an identity (two machines can install different files
under one name, and the embedded face can change with Pillow); the bytes are.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

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

### tituli.fonts.resolve_face(family=('Helvetica Neue', 'Inter', 'Helvetica', 'Avenir Next', 'Roboto', 'Univers', 'Liberation Sans', 'DejaVu Sans', 'Arial'), , size, weight=400, italic=False, condensed=False, features=())

Resolve a typeface request to a sized `Face`; never fails.

`features` are OpenType feature tags to apply (`("tnum",)`), carried by
the face; see [`Face.applied_features`](#tituli.fonts.Face.applied_features) for which the font has.

Falls back to Pillow’s embedded Aileron when nothing in the list is installed,
so a render on a fontless CI box still produces a real (if plainer) result.
[`EMBEDDED`](#tituli.fonts.EMBEDDED) in the list stops the search there (see its comment):

* **Return type:**
  [`Face`](#tituli.fonts.Face)

```pycon
>>> resolve_face(EMBEDDED, size=20).path is None
True
>>> resolve_face(["definitely-not-installed-xyz", EMBEDDED], size=20).family
'Aileron'
```
