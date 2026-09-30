# tituli.shaping

Optional engine: HarfBuzz shaping + FreeType rendering (`pip install tituli[shaping]`).

The Pillow default handles Latin text well and rotates glyph *bitmaps*. This
engine shapes the run with HarfBuzz (kerning, ligatures, Arabic/Devanagari
joining) and asks FreeType to apply the rotation to the **outline** before
rasterising, which is the typographically correct order. Same `Run`
in, same canvas out — it is the `engine=` seam of `tituli.render.render()`.

Import cost is paid only when constructed; the module itself imports nothing
optional at top level.

### Functions

| [`shape`](#tituli.shaping.shape)(text, path, index, size, \*[, features])   | `[(glyph_id, x_advance, y_advance, x_offset, y_offset), ...]` in pixels.   |
|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|

### Classes

| [`HarfBuzzEngine`](#tituli.shaping.HarfBuzzEngine)()   | Draw runs through HarfBuzz + FreeType.   |
|---------------------------------------------------------------------|------------------------------------------|

### *class* tituli.shaping.HarfBuzzEngine

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Draw runs through HarfBuzz + FreeType. Falls back to Pillow for the embedded font.

### tituli.shaping.shape(text, path, index, size, , features=None)

`[(glyph_id, x_advance, y_advance, x_offset, y_offset), ...]` in pixels.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]
