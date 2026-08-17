#!/usr/bin/env python3
"""Generate assets/avatar.svg (+ .png) — the profile avatar, in drawing-set tokens.

    make avatar

Design constraints, which are different from the sheets':

  * It is displayed in a CIRCLE. Corners are cut, so nothing lives there --
    no registration marks, no frame, no title rail.
  * It is displayed at ~40px in feeds and comments. From a 512px source that is
    0.078x, at which ANY stroke weight disappears. So the artwork is solid
    filled shapes with high contrast against the ground, not outlined drawing.
    This is why it cannot simply reuse a sheet's hairline vocabulary.
  * GitHub will not accept an SVG avatar upload, so a PNG is emitted too. The
    SVG is the source of truth.

Concept: the three-plate reduction of LC-000's assembly, with the volatile layer
in redline. Same idea as the hero drawing, stripped to what survives 40px.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import drawset as d  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "assets"

S = 512                  # canonical canvas; every coordinate derives from it
CENTRE = S / 2
PLATE = 245.0            # plate width and depth (square in plan)
THICK = 16.0
PITCH = 78.0             # vertical gap between plate centres

# Solid fills. Side faces are darkened so the extrusion still reads without
# relying on outlines, which vanish at avatar scale.
CYAN_TOP, CYAN_SIDE = "#5fb0d0", "#3a7d97"
MARK_TOP, MARK_SIDE = "#ff3d8e", "#bf2a68"


def build() -> str:
    # Vertical extent, so the stack can be optically centred rather than guessed.
    half_h = (PLATE * 2) * d.SIN30 / 2
    c = CENTRE - THICK / 2
    top_y = (c - PITCH) - half_h
    bot_y = (c + PITCH) + half_h + THICK
    assert abs(((top_y + bot_y) / 2) - CENTRE) < 0.5, "stack is not optically centred"

    # Every vertex must sit inside the inscribed circle or the circular crop
    # clips it. The rhombus vertices lie on the axes, so the widest point is the
    # horizontal one.
    half_w = (PLATE * 2) * d.COS30 / 2
    assert half_w < CENTRE - 24, f"stack half-width {half_w:.0f} risks the circular crop"

    layers = [  # bottom-first
        (CYAN_TOP, CYAN_SIDE),
        (MARK_TOP, MARK_SIDE),
        (CYAN_TOP, CYAN_SIDE),
    ]

    body = [f'<rect width="{S}" height="{S}" fill="{d.PAPER}"/>']
    for i, (ftop, fside) in enumerate(layers):
        cy = (c + PITCH) - i * PITCH
        g, _anchors = d.plate(
            CENTRE, cy, PLATE, PLATE, THICK, 1.0,
            stroke=ftop,          # stroke matches fill: crisp edges, no outline
            fill_top=ftop, fill_side=fside, opacity=1.0, lw=1.0,
        )
        body.append(g)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" '
        f'viewBox="0 0 {S} {S}" role="img" aria-labelledby="t">'
        f'<title id="t">Lowcache — three-plate exploded assembly, volatile layer '
        f'in redline</title>'
        + "".join(body)
        + "</svg>"
    )


def main() -> None:
    svg_path = OUT / "avatar.svg"
    svg_path.write_text(build(), encoding="utf-8")
    print(f"avatar.svg          {svg_path.stat().st_size:>6,} bytes")

    # PNG for the actual upload; librsvg is ImageMagick's SVG delegate here.
    png = OUT / "avatar.png"
    subprocess.run(
        ["magick", "-background", "none", f"{svg_path}",
         "-resize", "512x512", str(png)],
        check=True,
    )
    print(f"avatar.png          {png.stat().st_size:>6,} bytes")


if __name__ == "__main__":
    main()
