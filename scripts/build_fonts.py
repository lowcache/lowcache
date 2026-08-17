#!/usr/bin/env python3
"""Generate the committed font cache in assets/fonts/cache/.

    make fonts

Writes, for each face in drawset.FACES:
  * <key>.b64        base64-encoded subset woff2, ready to inline in an SVG
  * metrics.json     per-character advance widths in em units, for text_width()

Why a committed cache rather than subsetting on every build:

  1. The woff2/brotli encoder is not deterministic. Re-encoding per build made
     every sheet differ by ~100 bytes on identical source, so `make sheets`
     produced a full-file git diff every single time. Freezing the encoded
     bytes in the repo makes sheet output reproducible.
  2. It removes fontTools + brotli from the render path. drawset.py is then
     stdlib-only, so .github/workflows/stats.yml can rebuild the stats sheet in
     CI with no extra dependencies.

Only run this when the source woff2 files or drawset.GLYPHS change. Committing
the result is the point; do not gitignore it.
"""

from __future__ import annotations

import base64
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import drawset as d  # noqa: E402

# Fixed font timestamp (seconds since the 1904-01-01 Mac epoch). fontTools
# stamps head.modified with the current time on save otherwise.
EPOCH = 3_849_984_000


def build_face(key: str) -> tuple[bytes, dict[str, float]]:
    from fontTools import subset
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    fname, _family, weight = d.FACES[key]
    font = TTFont(d.FONT_DIR / fname)

    # JetBrains Mono ships as a variable font and the wiki serves the same file
    # for 400 and 700, so the weight has to come from instancing, not the name.
    if "fvar" in font:
        font = instancer.instantiateVariableFont(
            font, {"wght": weight}, inplace=False, updateFontNames=False
        )

    opt = subset.Options()
    opt.layout_features = ["kern"]
    opt.name_IDs = [1, 2]
    opt.name_legacy = False
    opt.glyph_names = False
    opt.hinting = False
    opt.legacy_kern = False
    opt.notdef_outline = False
    opt.recalc_bounds = True
    opt.prune_unicode_ranges = True
    opt.drop_tables += [
        "FFTM", "DSIG", "LTSH", "hdmx", "VDMX", "gasp", "PCLT",
        "vhea", "vmtx", "MVAR", "STAT", "fvar", "HVAR", "avar",
    ]
    sub = subset.Subsetter(options=opt)
    sub.populate(text=d.GLYPHS)
    sub.subset(font)

    head = font["head"]
    head.created = head.modified = EPOCH

    # Advance widths, normalised to em, measured before serialising.
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upm = head.unitsPerEm
    widths: dict[str, float] = {}
    missing = []
    for ch in d.GLYPHS:
        gname = cmap.get(ord(ch))
        if gname is None:
            missing.append(ch)
            continue
        widths[ch] = hmtx[gname][0] / upm
    if missing:
        print(f"  ! {key}: no glyph for {''.join(missing)!r}", file=sys.stderr)

    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue(), widths


def main() -> None:
    d.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    metrics: dict[str, dict[str, float]] = {}
    total = 0
    for key in d.FACES:
        raw, widths = build_face(key)
        b64 = base64.b64encode(raw).decode("ascii")
        (d.CACHE_DIR / f"{key}.b64").write_text(b64, encoding="ascii")
        metrics[key] = widths
        total += len(b64)
        print(f"  {key:8} {len(raw):>6,}B woff2  {len(b64):>7,} chars b64")

    (d.CACHE_DIR / "metrics.json").write_text(
        json.dumps(metrics, separators=(",", ":"), sort_keys=True), encoding="utf-8"
    )
    print(f"  {'total':8} {total:>21,} chars b64 across {len(d.FACES)} faces")
    print(f"  cache -> {d.CACHE_DIR.relative_to(d.ROOT)}")


if __name__ == "__main__":
    main()
