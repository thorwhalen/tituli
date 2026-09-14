"""``python -m tituli`` — the CLI over :data:`tituli.tools._dispatch_funcs`."""

from tituli.tools import _dispatch_funcs

if __name__ == "__main__":
    import cw

    raise SystemExit(cw.dispatch(_dispatch_funcs))
