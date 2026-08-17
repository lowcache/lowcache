"""Drawing-set primitives for the LOWCACHE profile sheets.

Shared vocabulary with wiki.infernalcode.com: same tokens, same fonts, same
line weights. Every helper returns an SVG fragment string.

Two rules this module exists to enforce:

1. Nothing is positioned by a hand-typed magic number. Callers pass canonical
   canvas dimensions and geometry is derived, so resizing a sheet cannot leave
   dependent geometry behind (see .memory/mistakes.md, 2026-07-09).
2. Text advance widths are measured from the real font metrics, never guessed,
   so text cannot silently overflow its container.

Stdlib only. Font subsetting lives in build_fonts.py and its output is committed
to assets/fonts/cache/, so rendering a sheet needs no third-party packages.
Run `make fonts` if the cache is missing.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"
CACHE_DIR = FONT_DIR / "cache"

# ---------------------------------------------------------------- tokens ----
# Lifted verbatim from wiki.infernalcode.com's --dw-* custom properties so the
# two surfaces are one document set rather than two lookalikes.
PAPER = "#0b1016"
PAPER2 = "#101823"
PAPER3 = "#16202d"
INK = "#dfe6ef"
INK2 = "#97a3b4"
INK3 = "#7c8899"
HAIR = "#26313f"
MARK = "#ff3d8e"       # redline / annotation
CONS = "#5fb0d0"       # construction line

LW_HAIR = 0.5
LW_THIN = 1.0
LW_MED = 1.5
LW_HEAVY = 2.5

EASE = "cubic-bezier(0.16,1,0.3,1)"

# Faces available to sheets. Key -> (file, css family, weight).
FACES = {
    "bc700": ("barlow-condensed-700.woff2", "BC", 700),
    "bc600": ("barlow-condensed-600.woff2", "BC", 600),
    "bc500": ("barlow-condensed-500.woff2", "BC", 500),
    "bw400": ("barlow-400.woff2", "BW", 400),
    "bw500": ("barlow-500.woff2", "BW", 500),
    "jb400": ("jetbrains-mono-400.woff2", "JB", 400),
    "jb700": ("jetbrains-mono-400.woff2", "JB", 700),
}

# Glyph coverage for the subsets. Kept explicit so a stray character in copy
# shows up as a build-time warning rather than a tofu box in the render.
GLYPHS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    " .,:;!?'\"/\\|()[]{}<>-_=+*#$%&@^~`"
    "·—–°×±…’"
)


# ------------------------------------------------------------ font plumbing ----
class CacheMissing(RuntimeError):
    pass


def _cache_file(name: str) -> Path:
    p = CACHE_DIR / name
    if not p.exists():
        raise CacheMissing(
            f"font cache entry {name!r} is missing from "
            f"{CACHE_DIR.relative_to(ROOT)}. Run `make fonts` to regenerate it "
            f"(that step needs fontTools + brotli; rendering does not)."
        )
    return p


@lru_cache(maxsize=None)
def _subset_b64(key: str) -> str:
    return _cache_file(f"{key}.b64").read_text(encoding="ascii").strip()


@lru_cache(maxsize=None)
def _widths() -> dict:
    """{face key: {char: advance in em}}, produced by build_fonts.py."""
    return json.loads(_cache_file("metrics.json").read_text(encoding="utf-8"))


def text_width(s: str, key: str, size: float, tracking: float = 0.0) -> float:
    """Measured advance width in user units. Tracking is per-gap, as SVG applies it."""
    table = _widths().get(key)
    if table is None:
        raise CacheMissing(f"no metrics for face {key!r}; run `make fonts`")
    total = 0.0
    missing = []
    for ch in s:
        adv = table.get(ch)
        if adv is None:
            missing.append(ch)
            continue
        total += adv * size
    if missing:
        raise ValueError(
            f"characters {missing!r} in {s!r} are not in the {key} subset; "
            f"add them to drawset.GLYPHS, run `make fonts`, or change the copy"
        )
    return total + tracking * max(0, len(s) - 1)


def wrap(s: str, key: str, size: float, limit: float, tracking: float = 0.0) -> list[str]:
    """Greedy word wrap against measured advance widths.

    Copy is stored once as a single string and wrapped per layout, so the wide
    and narrow variants of a sheet cannot drift apart in wording. A word too
    long for `limit` raises rather than silently overflowing.
    """
    words = s.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}" if cur else w
        if text_width(trial, key, size, tracking) <= limit:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        if text_width(w, key, size, tracking) > limit:
            raise ValueError(
                f"the word {w!r} is {text_width(w, key, size, tracking):.1f}u wide at "
                f"{size}px and cannot fit a {limit:.1f}u column"
            )
        cur = w
    if cur:
        lines.append(cur)
    return lines


def paragraph(x: float, y: float, s: str, key: str, size: float, limit: float,
              lh: float, colour: str = INK, tracking: float = 0.0):
    """Wrapped body copy. Returns (svg, next_y) so callers can stack blocks."""
    lines = wrap(s, key, size, limit, tracking)
    out = [body(x, y + i * lh, ln, size, colour, key=key) for i, ln in enumerate(lines)]
    return "".join(out), y + len(lines) * lh


def fit(s: str, key: str, size: float, tracking: float, limit: float, label: str) -> str:
    """Assert measured text fits `limit`. Raises with numbers, so overflow is a build error."""
    w = text_width(s, key, size, tracking)
    if w > limit:
        raise ValueError(
            f"{label}: {s!r} measures {w:.1f}u at {size}px but the box is {limit:.1f}u "
            f"(over by {w - limit:.1f}u). Shorten the copy or reduce the size."
        )
    return s


def font_css(keys) -> str:
    """@font-face block. Data URIs render inside <img>-embedded SVG; external URLs do not."""
    out = []
    for k in keys:
        _fn, family, weight = FACES[k]
        out.append(
            f"@font-face{{font-family:{family};font-style:normal;font-weight:{weight};"
            f"font-display:block;src:url(data:font/woff2;base64,{_subset_b64(k)}) format(\"woff2\")}}"
        )
    return "".join(out)


# ------------------------------------------------------------------ escaping ----
def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def f(v: float) -> str:
    """Trim float noise out of the emitted path data."""
    return f"{v:.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


# ---------------------------------------------------------------- primitives ----
def grid(w: float, h: float, major: float = 40.0) -> str:
    """Blueprint underlay. Two <pattern>s beat thousands of <line>s."""
    return (
        f'<pattern id="gmin" width="{f(major/5)}" height="{f(major/5)}" patternUnits="userSpaceOnUse">'
        f'<path d="M{f(major/5)} 0V{f(major/5)}H0" fill="none" stroke="#ffffff" '
        f'stroke-opacity="0.022" stroke-width="{LW_HAIR}"/></pattern>'
        f'<pattern id="gmaj" width="{f(major)}" height="{f(major)}" patternUnits="userSpaceOnUse">'
        f'<rect width="{f(major)}" height="{f(major)}" fill="url(#gmin)"/>'
        f'<path d="M{f(major)} 0V{f(major)}H0" fill="none" stroke="#ffffff" '
        f'stroke-opacity="0.045" stroke-width="{LW_HAIR}"/></pattern>'
    )


def hatch(idn: str, color: str, opacity: float = 0.16, step: float = 6.0) -> str:
    """45° section hatching, as on the wiki's caution notes."""
    return (
        f'<pattern id="{idn}" width="{f(step)}" height="{f(step)}" '
        f'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<line x1="0" y1="0" x2="0" y2="{f(step)}" stroke="{color}" '
        f'stroke-opacity="{opacity}" stroke-width="{LW_THIN}"/></pattern>'
    )


def corner_marks(x: float, y: float, w: float, h: float, arm: float = 26.0,
                 color: str = INK3, width: float = LW_MED) -> str:
    """Registration brackets at the sheet corners."""
    r = x + w
    b = y + h
    d = (
        f"M{f(x)} {f(y+arm)}V{f(y)}H{f(x+arm)}"
        f"M{f(r-arm)} {f(y)}H{f(r)}V{f(y+arm)}"
        f"M{f(r)} {f(b-arm)}V{f(b)}H{f(r-arm)}"
        f"M{f(x+arm)} {f(b)}H{f(x)}V{f(b-arm)}"
    )
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-opacity="0.55"/>'


def rule(x1: float, y: float, x2: float, color: str = HAIR, width: float = LW_THIN,
         dash: str | None = None) -> str:
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{f(x1)}" y1="{f(y)}" x2="{f(x2)}" y2="{f(y)}" '
            f'stroke="{color}" stroke-width="{width}"{da}/>')


def vrule(x: float, y1: float, y2: float, color: str = HAIR, width: float = LW_THIN,
          dash: str | None = None) -> str:
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{f(x)}" y1="{f(y1)}" x2="{f(x)}" y2="{f(y2)}" '
            f'stroke="{color}" stroke-width="{width}"{da}/>')


def label(x: float, y: float, s: str, key: str = "jb400", size: float = 11.0,
          tracking: float = 1.9, color: str = INK3, anchor: str = "start",
          weight: int | None = None) -> str:
    """Tracked mono sheet label. The drawing set's small-caps voice."""
    fam = FACES[key][1]
    wt = weight if weight is not None else FACES[key][2]
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return (
        f'<text x="{f(x)}" y="{f(y)}" font-family="{fam},ui-monospace,monospace" '
        f'font-size="{f(size)}" font-weight="{wt}" letter-spacing="{f(tracking)}" '
        f'fill="{color}"{a}>{esc(s)}</text>'
    )


def display(x: float, y: float, s: str, size: float, color: str = INK,
            tracking: float | None = None, key: str = "bc700",
            anchor: str = "start") -> str:
    """Barlow Condensed display type. Tracking defaults to the wiki's -0.028em."""
    if tracking is None:
        tracking = -0.028 * size
    fam = FACES[key][1]
    wt = FACES[key][2]
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return (
        f'<text x="{f(x)}" y="{f(y)}" font-family="{fam},sans-serif" '
        f'font-size="{f(size)}" font-weight="{wt}" letter-spacing="{f(tracking)}" '
        f'fill="{color}"{a}>{esc(s)}</text>'
    )


def body(x: float, y: float, s: str, size: float = 15.0, color: str = INK,
         key: str = "bw400", anchor: str = "start") -> str:
    fam = FACES[key][1]
    wt = FACES[key][2]
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return (
        f'<text x="{f(x)}" y="{f(y)}" font-family="{fam},sans-serif" '
        f'font-size="{f(size)}" font-weight="{wt}" fill="{color}"{a}>{esc(s)}</text>'
    )


def balloon(cx: float, cy: float, n: str, r: float = 13.0, active: bool = False) -> str:
    """Numbered callout balloon keyed to the parts list."""
    if active:
        circle = (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{MARK}" '
                  f'stroke="{MARK}" stroke-width="{LW_THIN}"/>')
        num_fill = PAPER
    else:
        circle = (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{PAPER}" '
                  f'fill-opacity="0.9" stroke="{INK3}" stroke-width="{LW_THIN}"/>')
        num_fill = INK2
    fam = FACES["jb700"][1]
    return (
        circle
        + f'<text x="{f(cx)}" y="{f(cy + r*0.33)}" text-anchor="middle" '
        f'font-family="{fam},ui-monospace,monospace" font-size="{f(r*0.85)}" '
        f'font-weight="700" letter-spacing="0.3" fill="{num_fill}">{esc(n)}</text>'
    )


def arrow(x: float, y: float, direction: str, size: float = 5.0, color: str = INK3) -> str:
    """Solid dimension arrowhead."""
    s = size
    pts = {
        "left": f"{f(x)},{f(y)} {f(x+s*1.8)},{f(y-s*0.6)} {f(x+s*1.8)},{f(y+s*0.6)}",
        "right": f"{f(x)},{f(y)} {f(x-s*1.8)},{f(y-s*0.6)} {f(x-s*1.8)},{f(y+s*0.6)}",
        "up": f"{f(x)},{f(y)} {f(x-s*0.6)},{f(y+s*1.8)} {f(x+s*0.6)},{f(y+s*1.8)}",
        "down": f"{f(x)},{f(y)} {f(x-s*0.6)},{f(y-s*1.8)} {f(x+s*0.6)},{f(y-s*1.8)}",
    }[direction]
    return f'<polygon points="{pts}" fill="{color}"/>'


def vdim(x: float, y1: float, y2: float, text: str, color: str = INK3,
         side: str = "left", ext: float = 7.0) -> str:
    """Vertical dimension: extension ticks, arrowheads, rotated caption."""
    out = [
        vrule(x, y1, y2, color, LW_HAIR),
        rule(x - ext, y1, x + ext, color, LW_HAIR),
        rule(x - ext, y2, x + ext, color, LW_HAIR),
        arrow(x, y1, "up", 4.5, color),
        arrow(x, y2, "down", 4.5, color),
    ]
    mid = (y1 + y2) / 2
    fam = FACES["jb400"][1]
    dx = -6 if side == "left" else 10
    out.append(
        f'<text transform="translate({f(x+dx)},{f(mid)}) rotate(-90)" text-anchor="middle" '
        f'font-family="{fam},ui-monospace,monospace" font-size="9.5" letter-spacing="1.4" '
        f'fill="{color}">{esc(text)}</text>'
    )
    return "".join(out)


def caution(x: float, y: float, w: float, title: str, lines, colour: str = MARK,
            hatch_id: str = "cauthatch", lh: float = 21.0, pad: float = 18.0) -> str:
    """Bordered note with a 45° hatched header band, as on the wiki's cautions.

    Height is derived from the line count, so adding a line cannot silently
    overflow the box.
    """
    band = 30.0
    h = band + pad + len(lines) * lh + pad - 6
    out = [
        f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{PAPER2}" '
        f'stroke="{colour}" stroke-width="{LW_THIN}"/>',
        f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(band)}" fill="url(#{hatch_id})"/>',
        f'<line x1="{f(x)}" y1="{f(y+band)}" x2="{f(x+w)}" y2="{f(y+band)}" '
        f'stroke="{colour}" stroke-width="{LW_THIN}"/>',
    ]
    # warning glyph: a triangle with a bang, drawn rather than typed
    gx, gy = x + pad, y + band / 2
    out.append(
        f'<path d="M{f(gx)} {f(gy+6)}L{f(gx+7)} {f(gy-6.5)}L{f(gx+14)} {f(gy+6)}Z" '
        f'fill="none" stroke="{colour}" stroke-width="{LW_THIN}"/>'
        f'<line x1="{f(gx+7)}" y1="{f(gy-2.5)}" x2="{f(gx+7)}" y2="{f(gy+1.5)}" '
        f'stroke="{colour}" stroke-width="{LW_THIN}"/>'
        f'<circle cx="{f(gx+7)}" cy="{f(gy+3.6)}" r="0.9" fill="{colour}"/>'
    )
    out.append(label(gx + 24, gy + 4, title, "jb700", 10.5, 1.9, colour))
    for i, ln in enumerate(lines):
        out.append(body(x + pad, y + band + pad + 8 + i * lh, ln, 14, INK))
    return "".join(out), h


def leader(x1: float, y1: float, x2: float, y2: float, color: str = INK3,
           dash: str = "3 3") -> str:
    """Callout leader: short angled kick, then horizontal run to the balloon."""
    knee = x1 + (x2 - x1) * 0.22
    return (
        f'<path d="M{f(x1)} {f(y1)}L{f(knee)} {f(y2)}H{f(x2)}" fill="none" '
        f'stroke="{color}" stroke-width="{LW_HAIR}" stroke-dasharray="{dash}" '
        f'stroke-opacity="0.85"/>'
        f'<circle cx="{f(x1)}" cy="{f(y1)}" r="1.8" fill="{color}"/>'
    )


# --------------------------------------------------------- axonometric plate ----
COS30 = math.cos(math.radians(30))
SIN30 = math.sin(math.radians(30))


def iso(x: float, y: float, z: float, cx: float, cy: float, scale: float = 1.0):
    """True 30° isometric projection into screen space."""
    return (cx + (x - z) * COS30 * scale, cy + (x + z) * SIN30 * scale - y * scale)


def plate(cx: float, cy: float, w: float, d: float, t: float, scale: float = 1.0,
          stroke: str = INK2, fill_top: str = PAPER3, fill_side: str = PAPER2,
          opacity: float = 1.0, lw: float = LW_THIN):
    """One extruded isometric plate. Returns (svg, anchors) where anchors are the
    screen-space points a leader line can attach to."""
    hw, hd = w / 2, d / 2
    P = lambda x, y, z: iso(x, y, z, cx, cy, scale)

    # top face, clockwise from back corner
    tb = P(-hw, t, -hd)   # back
    tr = P(hw, t, -hd)    # right-back
    tf = P(hw, t, hd)      # front
    tl = P(-hw, t, hd)     # left-front
    # bottom edge of the two visible side faces
    br = P(hw, 0, -hd)
    bf = P(hw, 0, hd)
    bl = P(-hw, 0, hd)

    top = f"M{f(tb[0])} {f(tb[1])}L{f(tr[0])} {f(tr[1])}L{f(tf[0])} {f(tf[1])}L{f(tl[0])} {f(tl[1])}Z"
    right = f"M{f(tr[0])} {f(tr[1])}L{f(tf[0])} {f(tf[1])}L{f(bf[0])} {f(bf[1])}L{f(br[0])} {f(br[1])}Z"
    left = f"M{f(tl[0])} {f(tl[1])}L{f(tf[0])} {f(tf[1])}L{f(bf[0])} {f(bf[1])}L{f(bl[0])} {f(bl[1])}Z"

    g = (
        f'<g opacity="{opacity}">'
        f'<path d="{left}" fill="{fill_side}" stroke="{stroke}" stroke-width="{lw}" stroke-opacity="0.7"/>'
        f'<path d="{right}" fill="{fill_side}" stroke="{stroke}" stroke-width="{lw}" stroke-opacity="0.7"/>'
        f'<path d="{top}" fill="{fill_top}" stroke="{stroke}" stroke-width="{lw}"/>'
        f"</g>"
    )
    anchors = {
        "back": tb, "right": tr, "front": tf, "left": tl,
        "bottom_front": bf, "bottom_left": bl,
        "top_mid": ((tb[0] + tf[0]) / 2, (tb[1] + tf[1]) / 2),
    }
    return g, anchors


# ----------------------------------------------------------------- document ----
def svg_open(w: float, h: float, faces, title: str, desc: str,
             extra_defs: str = "", extra_css: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(w)}" height="{f(h)}" '
        f'viewBox="0 0 {f(w)} {f(h)}" role="img" '
        f'aria-labelledby="t d" font-kerning="normal" '
        f'text-rendering="geometricPrecision">'
        f"<title id=\"t\">{esc(title)}</title><desc id=\"d\">{esc(desc)}</desc>"
        f"<defs>{grid(w, h)}{extra_defs}</defs>"
        f"<style>{font_css(faces)}"
        f"text{{white-space:pre}}{extra_css}</style>"
        f'<rect width="{f(w)}" height="{f(h)}" fill="{PAPER}"/>'
        f'<rect width="{f(w)}" height="{f(h)}" fill="url(#gmaj)"/>'
    )


def svg_close() -> str:
    return "</svg>"
