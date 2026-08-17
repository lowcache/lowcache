#!/usr/bin/env python3
"""Compose the LOWCACHE profile sheets into assets/*.svg.

    nix-shell -p 'python3.withPackages(p:[p.fonttools p.brotli])' \
      --run 'python3 scripts/build_sheets.py'

Design constraints these sheets are built against, all verified in Chromium 151:

  * Inlined subset WOFF2 (data: URI) DOES render inside <img>-embedded SVG.
    External font URLs do not. Hence drawset.font_css().
  * Neither SMIL nor CSS animation runs inside <img>-embedded SVG. Every sheet
    must therefore be complete and correct as a static render. Nothing is ever
    gated behind an animation; motion is added as pure enhancement only.
  * GitHub serves README images through a proxy that passes bytes unchanged,
    so <style> and data URIs survive, but the SVG gets no pointer events.
    Links live in the README markdown, never in the SVG.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import drawset as d  # noqa: E402
from drawset import (  # noqa: E402
    CONS, HAIR, INK, INK2, INK3, MARK, PAPER, PAPER2, PAPER3,
    LW_HAIR, LW_MED, LW_THIN,
)

OUT = Path(__file__).resolve().parent.parent / "assets"
REV = "2026-08-17"

# --------------------------------------------------------------- sheet layout ----
W = 880           # canonical sheet width; every x derives from this
MARGIN = 14       # frame inset
PAD = 40          # content left edge
RIGHT = W - PAD   # content right edge

# The assembly in physical order, BOTTOM FIRST -- index 0 is the bottom plate.
# Balloon numbers run top-down so the parts list reads in document order, which
# is why the numbers descend as the list ascends. `active` marks the volatile
# layer in redline. Iterate LAYERS as-is to stack; reverse it to list.
LAYERS = [
    # (balloon, name, category, note, active)
    ("05", "Hardware",   "CHASSIS",        "ASUS TUF A16 — AMD iGPU + NVIDIA RTX 4050, switched per workload.", False),
    ("04", "/persist",   "DURABLE STATE",  "The only writes that survive a reboot. Mapped here by name.", False),
    ("03", "tmpfs root", "VOLATILE ROOT",  "The root filesystem lives in RAM and is destroyed on every boot.", True),
    ("02", "Nix",        "DECLARATIVE",    "Flakes, derivations, home-manager. The tree rebuilds from one command.", False),
    ("01", "Agents",     "TOOLING",        "Isolated containers for MCP servers; project memory that outlives context.", False),
]

# Right-hand data block, beside the nameplate.
IDENT = [
    ("HANDLE", "lowcache"),
    ("STATUS", "freelance"),
    ("CERT", "comptia a+ · linux+"),
    ("EDU", "ba english"),
]

NOTES = [
    "Self-taught. Ten-plus years on Linux, currently freelance.",
    "The assembly below is drawn as the machine actually runs: a NixOS",
    "workstation whose root filesystem lives in RAM and is destroyed on",
    "every boot. Everything durable is mapped by name; everything else is",
    "re-derived from a flake — including the tooling I build for agents.",
]

REVISIONS = [
    ("C", "2026-08-17", "agent tooling"),
    ("B", "2026-07-13", "phone tier"),
    ("A", "2026-07-03", "first issue"),
]


def section_head(x: float, y: float, text: str, x2: float) -> str:
    """Tracked sheet-note heading with a rule running to the right margin.

    These are real drawing-sheet section names (GENERAL NOTES / PARTS LIST /
    REVISIONS), reused from the wiki as a named system -- not decorative
    eyebrows stacked above every block.
    """
    w = d.text_width(text, "jb700", 11, 2.3)
    return (
        d.label(x, y, text, "jb700", 11, 2.3, INK2)
        + d.rule(x + w + 14, y - 4, x2, HAIR, LW_HAIR)
    )


# ============================================================ SHEET LC-000 ====
def sheet_lc000() -> str:
    # -- vertical rhythm, declared once ------------------------------------
    y_rail = 44
    y_rail_rule = 58
    y_title = 152          # baseline of the 92px display word
    y_sub = 186
    y_sub_rule = 206
    y_notes_head = 240
    y_notes = 266          # first body baseline
    notes_lh = 23
    y_draw_head = 408
    y_stack_base = 706     # top-face centre of the bottom plate
    plate_gap = 40
    y_parts_head = 872
    y_parts = 896
    parts_lh = 38

    # Sheet height is DERIVED from where the last parts-list row ends, not typed
    # in. Hardcoding it clipped the fifth row's description below the frame.
    last_row_bottom = y_parts + (len(LAYERS) - 1) * parts_lh + 19 + 6
    H = last_row_bottom + 28 + MARGIN

    body: list[str] = []

    # -- sheet frame ------------------------------------------------------
    body.append(
        f'<rect x="{MARGIN}" y="{MARGIN}" width="{W-2*MARGIN}" height="{H-2*MARGIN}" '
        f'fill="none" stroke="{HAIR}" stroke-width="{LW_THIN}"/>'
    )
    body.append(d.corner_marks(MARGIN, MARGIN, W - 2 * MARGIN, H - 2 * MARGIN))

    # -- top rail ---------------------------------------------------------
    body.append(d.label(PAD, y_rail, "LC-000", "jb700", 11.5, 2.4, MARK))
    body.append(d.label(PAD + 74, y_rail, "GENERAL ARRANGEMENT", "jb400", 11.5, 2.4, INK3))
    body.append(d.label(RIGHT, y_rail, f"REV {REV}", "jb400", 11.5, 2.4, INK3, anchor="end"))
    body.append(d.rule(PAD, y_rail_rule, RIGHT))

    # -- nameplate --------------------------------------------------------
    d.fit("Lowcache", "bc700", 92, -2.58, 460, "LC-000 display")
    body.append(d.display(PAD - 2, y_title, "Lowcache", 92))
    body.append(d.label(PAD, y_sub, "JARRED ROBINSON — SELF-TAUGHT", "bc600", 21, 2.5, INK2))
    body.append(d.rule(PAD, y_sub_rule, RIGHT))

    # -- identity block, beside the nameplate -----------------------------
    rx = 620
    for i, (k, v) in enumerate(IDENT):
        yy = 116 + i * 23
        body.append(d.label(rx, yy, k, "jb400", 9.5, 1.7, INK3))
        d.fit(v, "bw500", 14, 0, RIGHT - (rx + 84), f"LC-000 ident {k}")
        body.append(d.body(rx + 84, yy, v, 14, INK2, key="bw500"))
    body.append(d.vrule(rx - 22, 104, 104 + len(IDENT) * 23 - 6, HAIR, LW_THIN))

    # -- general notes ----------------------------------------------------
    body.append(section_head(PAD, y_notes_head, "GENERAL NOTES", 560))
    for i, line in enumerate(NOTES):
        d.fit(line, "bw400", 15.5, 0, 520, f"LC-000 note {i+1}")
        body.append(d.body(PAD, y_notes + i * notes_lh, line, 15.5, INK))

    # -- revision block (right of the notes) ------------------------------
    body.append(section_head(rx, y_notes_head, "REVISIONS", RIGHT))
    body.append(d.label(rx, y_notes - 6, "REV", "jb400", 9.5, 1.6, INK3))
    body.append(d.label(rx + 40, y_notes - 6, "DATE", "jb400", 9.5, 1.6, INK3))
    body.append(d.label(rx + 122, y_notes - 6, "NOTE", "jb400", 9.5, 1.6, INK3))
    body.append(d.rule(rx, y_notes + 1, RIGHT, HAIR, LW_HAIR))
    for i, (rev, date, note) in enumerate(REVISIONS):
        yy = y_notes + 22 + i * 25
        colour = MARK if i == 0 else INK2
        body.append(d.label(rx, yy, rev, "jb700", 11, 1.4, colour))
        body.append(d.label(rx + 40, yy, date, "jb400", 10.5, 0.5, INK2))
        d.fit(note, "bw400", 13, 0, RIGHT - (rx + 122), f"LC-000 rev {rev}")
        body.append(d.body(rx + 122, yy, note, 13, INK3))
        body.append(d.rule(rx, yy + 8, RIGHT, HAIR, LW_HAIR))

    # -- exploded axonometric --------------------------------------------
    body.append(section_head(PAD, y_draw_head, "ASSEMBLY — EXPLODED, NTS", RIGHT))

    cx = 262
    pw, pd, pt = 150.0, 96.0, 9.0
    scale = 1.0
    # half-extent of the projected top face, needed for datum + dimension lines
    half_w = (pw + pd) * d.COS30 * scale / 2

    # LAYERS is already bottom-first, so index == height in the stack.
    n = len(LAYERS)
    y_top_centre = y_stack_base - (n - 1) * plate_gap

    # Exploded-view centreline, drawn behind the plates so it shows in the gaps.
    body.append(d.vrule(cx, y_top_centre - 74, y_stack_base + 74, INK3, LW_HAIR, dash="3 5"))

    plates: list[tuple] = []   # (balloon, name, cy, anchors, active)
    for i, (num, name, cat, note, active) in enumerate(LAYERS):
        cy = y_stack_base - i * plate_gap
        stroke = MARK if active else INK2
        ftop = "url(#markhatch)" if active else PAPER3
        g, anchors = d.plate(cx, cy, pw, pd, pt, scale, stroke, ftop, PAPER2,
                             opacity=1.0, lw=LW_MED if active else LW_THIN)
        body.append(g)
        plates.append((num, name, cy, anchors, active))

    # Datum line: volatile above / durable below. Sits in the gap between the
    # tmpfs plate (index 2) and /persist (index 1), clear of both leader rows.
    y_datum = (plates[2][2] + plates[1][2]) / 2 - pt
    body.append(d.rule(cx - half_w - 30, y_datum, 574, CONS, LW_HAIR, dash="7 5"))
    body.append(d.label(396, y_datum - 9, "VOLATILE ABOVE", "jb700", 10, 1.9, CONS))
    body.append(d.body(396, y_datum + 15, "re-derived every boot", 12.5, INK3))

    # vertical dimension spanning the whole stack
    dim_x = cx - half_w - 60
    y_top_plate = plates[-1][3]["back"][1]
    y_bot_plate = plates[0][3]["bottom_front"][1]
    body.append(d.vdim(dim_x, y_top_plate, y_bot_plate, "10+ YEARS ON LINUX", INK3))

    # leaders + balloons, one per plate
    bx = 660
    for num, name, cy, anchors, active in plates:
        ay = cy - pt
        ax = anchors["right"][0]
        body.append(d.leader(ax, ay, bx - 15, ay, MARK if active else INK3))
        body.append(d.balloon(bx, ay, num, 13, active))
        lbl = name.upper()
        d.fit(lbl, "jb700", 11, 1.8, RIGHT - (bx + 24), f"LC-000 callout {num}")
        body.append(d.label(bx + 24, ay + 4, lbl, "jb700" if active else "jb400",
                            11, 1.8, MARK if active else INK2))

    # -- parts list -------------------------------------------------------
    body.append(section_head(PAD, y_parts_head, "PARTS LIST", RIGHT))
    for i, (num, name, cat, note, active) in enumerate(reversed(LAYERS)):
        yy = y_parts + i * parts_lh
        body.append(d.balloon(PAD + 14, yy + 2, num, 12, active))
        body.append(d.display(PAD + 40, yy + 1, name, 19, INK if not active else MARK,
                              tracking=-0.35, key="bc700"))
        nw = d.text_width(name, "bc700", 19, -0.35)
        body.append(d.label(PAD + 46 + nw + 8, yy, cat, "jb400", 9.5, 1.7, INK3))
        d.fit(note, "bw400", 13.5, 0, 470, f"LC-000 part {num}")
        body.append(d.body(PAD + 40, yy + 19, note, 13.5, INK2))
        if i < len(LAYERS) - 1:
            body.append(d.rule(PAD, yy + 27, RIGHT, HAIR, LW_HAIR))

    defs = d.hatch("markhatch", MARK, 0.20, 6.0)
    return (
        d.svg_open(
            W, H,
            ["bc700", "bc600", "bw400", "bw500", "jb400", "jb700"],
            "Lowcache — sheet LC-000, general arrangement",
            "Technical drawing sheet. Jarred Robinson, self-taught, ten-plus years on "
            "Linux, currently freelance. An exploded isometric assembly of the "
            "workstation: hardware, /persist durable state, a volatile tmpfs root "
            "highlighted in redline, Nix, and agent tooling, with a datum line "
            "marking volatile above and durable below.",
            extra_defs=defs,
        )
        + "".join(body)
        + d.svg_close()
    )


# ============================================================ SHEET LC-100 ====
REPOS = [
    # (sheet code, name, contents, stack)
    ("LC-101", "volnixos", "NixOS workstation — tmpfs root, impermanence, secure boot", "nix"),
    ("LC-102", "mcp-box", "Isolated Linux containers built for MCP servers", "shell"),
    ("LC-103", "memd", "Project memory for coding agents", "python"),
    ("LC-104", "volinit", "Shell-init sysinfo fetch with custom ASCII artwork", "nim"),
    ("LC-105", "noctalia-claude-plugin", "Claude Code plugin for the Noctalia desktop shell", "ts"),
]

TOOLING_NOTE = [
    "Generative AI is in the loop here and I don't pretend otherwise. It holds",
    "the work; I hold the judgement. Nothing ships that I can't explain line",
    "by line — which is why the reasoning is committed alongside the code.",
]


def sheet_lc100() -> str:
    y_rail, y_rail_rule = 44, 58
    y_title = 118
    y_title_rule = 142
    y_head = 172
    y_head_rule = 180
    y_rows = 210
    pitch = 46

    # column grid, declared once
    c_sheet = PAD
    c_title = PAD + 96
    c_desc = PAD + 306

    # Build the note first so the sheet height can be derived from it.
    y_note = y_rows + len(REPOS) * pitch + 22
    note, note_h = d.caution(
        PAD, y_note, RIGHT - PAD, "GENERAL NOTE — ON TOOLING", TOOLING_NOTE,
    )
    H = y_note + note_h + 28 + MARGIN

    body: list[str] = []
    body.append(
        f'<rect x="{MARGIN}" y="{MARGIN}" width="{W-2*MARGIN}" height="{H-2*MARGIN}" '
        f'fill="none" stroke="{HAIR}" stroke-width="{LW_THIN}"/>'
    )
    body.append(d.corner_marks(MARGIN, MARGIN, W - 2 * MARGIN, H - 2 * MARGIN))

    body.append(d.label(PAD, y_rail, "LC-100", "jb700", 11.5, 2.4, MARK))
    body.append(d.label(PAD + 74, y_rail, "SHEET INDEX", "jb400", 11.5, 2.4, INK3))
    body.append(d.label(RIGHT, y_rail, f"REV {REV}", "jb400", 11.5, 2.4, INK3, anchor="end"))
    body.append(d.rule(PAD, y_rail_rule, RIGHT))

    d.fit("Repositories", "bc700", 58, -1.62, 520, "LC-100 display")
    body.append(d.display(PAD - 1, y_title, "Repositories", 58))
    body.append(d.rule(PAD, y_title_rule, RIGHT))

    # column heads
    for x, t in ((c_sheet, "SHEET"), (c_title, "TITLE"), (c_desc, "CONTENTS")):
        body.append(d.label(x, y_head, t, "jb400", 9.5, 1.7, INK3))
    body.append(d.label(RIGHT, y_head, "STACK", "jb400", 9.5, 1.7, INK3, anchor="end"))
    body.append(d.rule(PAD, y_head_rule, RIGHT, HAIR, LW_THIN))

    for i, (code, name, desc, stack) in enumerate(REPOS):
        yy = y_rows + i * pitch
        body.append(d.label(c_sheet, yy, code, "jb700", 11.5, 1.2, MARK))
        d.fit(name, "bc700", 22, -0.4, c_desc - c_title - 14, f"LC-100 name {code}")
        body.append(d.display(c_title, yy + 2, name, 22, INK, tracking=-0.4))
        d.fit(desc, "bw400", 13.5, 0, RIGHT - c_desc - 62, f"LC-100 desc {code}")
        body.append(d.body(c_desc, yy, desc, 13.5, INK2))
        body.append(d.label(RIGHT, yy, stack, "jb400", 10.5, 1.2, INK3, anchor="end"))
        body.append(d.rule(PAD, yy + 16, RIGHT, HAIR, LW_HAIR))

    body.append(note)

    return (
        d.svg_open(
            W, H,
            ["bc700", "bw400", "jb400", "jb700"],
            "Lowcache — sheet LC-100, repository index",
            "Sheet index listing five repositories: volnixos, mcp-box, memd, volinit "
            "and noctalia-claude-plugin, with their contents and primary stack. "
            "Closes with a note on generative AI being used openly in the work.",
            extra_defs=d.hatch("cauthatch", MARK, 0.20, 6.0),
        )
        + "".join(body)
        + d.svg_close()
    )


# ============================================================ SHEET LC-200 ====
# Data comes from assets/stats.json (scripts/gen-stats.py). Rendering lives here
# so all drawing-set styling stays in one place.
#
# Colour reasoning: language share is a SEQUENTIAL measure (one quantity, ranked),
# not a categorical one, so every bar takes a single hue -- the construction blue
# -- rather than six competing colours. Values and names wear ink tokens; the
# redline accent stays reserved for annotation, as on every other sheet. Checked
# with the dataviz validator against the #0b1016 surface: contrast passes, and the
# two mark colours stay separable under deuteranopia (dE 10.0).
BAR_HUE = CONS


def sheet_lc200() -> str:
    import json

    src = OUT / "stats.json"
    if not src.exists():
        raise SystemExit(
            f"{src.relative_to(OUT.parent)} is missing. Run `make stats` first "
            f"(it fetches from the GitHub API; set GITHUB_TOKEN to avoid rate limits)."
        )
    data = json.loads(src.read_text(encoding="utf-8"))
    langs = data["languages"]
    # This sheet refreshes daily, so it carries the survey date rather than the
    # set-wide revision, which would go stale the moment the cron ran.
    rev = data.get("generated", REV)

    y_rail, y_rail_rule = 44, 58
    y_title = 118
    y_title_rule = 142
    y_tile_label = 174
    y_tile_value = 212
    y_tiles_rule = 234
    y_bars_head = 264
    y_bars = 292
    pitch = 34
    bar_h = 12

    bar_x, bar_w = 186, 512
    name_x = PAD

    tiles = [
        ("PUBLIC REPOS", str(data["repos"])),
        ("STARS", str(data["stars"])),
        ("LANGUAGES", str(len(langs))),
        ("ON GITHUB SINCE", data["since"]),
    ]

    y_axis = y_bars + len(langs) * pitch + 4
    H = y_axis + 40 + MARGIN

    body: list[str] = []
    body.append(
        f'<rect x="{MARGIN}" y="{MARGIN}" width="{W-2*MARGIN}" height="{H-2*MARGIN}" '
        f'fill="none" stroke="{HAIR}" stroke-width="{LW_THIN}"/>'
    )
    body.append(d.corner_marks(MARGIN, MARGIN, W - 2 * MARGIN, H - 2 * MARGIN))

    body.append(d.label(PAD, y_rail, "LC-200", "jb700", 11.5, 2.4, MARK))
    body.append(d.label(PAD + 74, y_rail, "SURVEY", "jb400", 11.5, 2.4, INK3))
    body.append(d.label(RIGHT, y_rail, f"SURVEYED {rev}", "jb400", 11.5, 2.4, INK3, anchor="end"))
    body.append(d.rule(PAD, y_rail_rule, RIGHT))

    d.fit("Survey", "bc700", 58, -1.62, 420, "LC-200 display")
    body.append(d.display(PAD - 1, y_title, "Survey", 58))
    body.append(d.rule(PAD, y_title_rule, RIGHT))

    # -- stat tiles: hero numbers, divided by hairlines rather than boxed in ----
    tile_w = (RIGHT - PAD) / len(tiles)
    for i, (k, v) in enumerate(tiles):
        tx = PAD + i * tile_w
        body.append(d.label(tx, y_tile_label, k, "jb400", 9.5, 1.7, INK3))
        d.fit(v, "bc700", 40, -1.12, tile_w - 20, f"LC-200 tile {k}")
        body.append(d.display(tx - 1, y_tile_value, v, 40, INK))
        if i:
            body.append(d.vrule(tx - 22, y_tile_label - 16, y_tile_value + 6, HAIR, LW_THIN))
    body.append(d.rule(PAD, y_tiles_rule, RIGHT))

    # -- language distribution -------------------------------------------------
    body.append(section_head(PAD, y_bars_head,
                             "LANGUAGE DISTRIBUTION — BY WEIGHT, ALL PUBLIC REPOS", RIGHT))

    scale_max = 100.0
    for i, ln in enumerate(langs):
        yy = y_bars + i * pitch
        name = ln["name"].lower()
        pct = float(ln["pct"])
        w = max(bar_w * pct / scale_max, 3.0)
        d.fit(name, "bw500", 14, 0, bar_x - name_x - 16, f"LC-200 lang {name}")
        body.append(d.body(name_x, yy + bar_h - 1, name, 14, INK, key="bw500"))
        # recessive track, then the measured fill with a rounded data end
        body.append(
            f'<rect x="{d.f(bar_x)}" y="{d.f(yy)}" width="{d.f(bar_w)}" height="{bar_h}" '
            f'fill="{PAPER3}"/>'
        )
        body.append(
            f'<rect x="{d.f(bar_x)}" y="{d.f(yy)}" width="{d.f(w)}" height="{bar_h}" '
            f'rx="3" fill="{BAR_HUE}"/>'
        )
        body.append(d.label(RIGHT, yy + bar_h - 1, f"{pct:.1f}%", "jb400", 11.5, 0.4,
                            INK2, anchor="end"))

    # -- axis: hairline ticks, recessive labels --------------------------------
    body.append(d.rule(bar_x, y_axis + 8, bar_x + bar_w, HAIR, LW_THIN))
    for t in (0, 25, 50, 75, 100):
        tx = bar_x + bar_w * t / scale_max
        body.append(d.vrule(tx, y_axis + 8, y_axis + 13, HAIR, LW_THIN))
        body.append(d.label(tx, y_axis + 26, f"{t}", "jb400", 9.5, 1.2, INK3,
                            anchor="middle" if t else "start"))
    body.append(d.label(RIGHT, y_axis + 26, "PERCENT", "jb400", 9.5, 1.7,
                        INK3, anchor="end"))

    return (
        d.svg_open(
            W, H,
            ["bc700", "bw400", "bw500", "jb400", "jb700"],
            "Lowcache — sheet LC-200, survey",
            "Profile statistics: "
            + ", ".join(f"{k.lower()} {v}" for k, v in tiles)
            + ". Language distribution by weight across all public repositories: "
            + ", ".join(f"{l['name']} {l['pct']}%" for l in langs) + ".",
        )
        + "".join(body)
        + d.svg_close()
    )


# ============================================================ SHEET LC-900 ====
TITLE_BLOCK = [
    ("TITLE", "Lowcache — general arrangement"),
    ("DRAWN", "lowcache"),
    ("SHEET", "LC-000 THRU LC-900"),
    ("REV", REV),
    ("SCALE", "NTS"),
]

LINKS = [
    ("BLOG", "infernalcode.com"),
    ("WIKI", "wiki.infernalcode.com"),
    ("CODE", "github.com/lowcache"),
]


def sheet_lc900() -> str:
    H = 214
    body: list[str] = []
    body.append(
        f'<rect x="{MARGIN}" y="{MARGIN}" width="{W-2*MARGIN}" height="{H-2*MARGIN}" '
        f'fill="none" stroke="{HAIR}" stroke-width="{LW_THIN}"/>'
    )
    body.append(d.corner_marks(MARGIN, MARGIN, W - 2 * MARGIN, H - 2 * MARGIN, arm=20))

    # title block: label/value pairs, two rows of the sheet's own metadata
    y0 = 54
    lh = 26
    for i, (k, v) in enumerate(TITLE_BLOCK):
        yy = y0 + i * lh
        body.append(d.label(PAD, yy, k, "jb400", 9.5, 1.7, INK3))
        key = "bc700" if i == 0 else "bw400"
        size = 19 if i == 0 else 14
        d.fit(v, key, size, 0, 300, f"LC-900 {k}")
        if i == 0:
            body.append(d.display(PAD + 62, yy + 2, v, size, INK, tracking=-0.4))
        else:
            body.append(d.body(PAD + 62, yy, v, size, INK2))

    # divider + links column
    lx = 520
    body.append(d.vrule(lx - 34, 40, H - 40, HAIR, LW_THIN))
    body.append(d.label(lx, 40, "REFERENCE", "jb700", 10.5, 2.0, INK2))
    for i, (k, v) in enumerate(LINKS):
        yy = 70 + i * 26
        body.append(d.label(lx, yy, k, "jb400", 9.5, 1.7, INK3))
        d.fit(v, "jb400", 12.5, 0.2, RIGHT - (lx + 52), f"LC-900 link {k}")
        body.append(d.label(lx + 52, yy, v, "jb400", 12.5, 0.2, CONS))

    body.append(d.rule(PAD, H - 46, RIGHT, HAIR, LW_HAIR))
    body.append(d.label(PAD, H - 28, "END OF SET", "jb400", 9.5, 2.2, INK3))
    body.append(d.label(RIGHT, H - 28, "DRAWN BY HAND · NO TEMPLATE", "jb400", 9.5, 2.2,
                        INK3, anchor="end"))

    return (
        d.svg_open(
            W, H,
            ["bc700", "bw400", "jb400", "jb700"],
            "Lowcache — sheet LC-900, title block",
            "Drawing title block: title, drawn by lowcache, sheet range LC-000 to "
            "LC-900, revision 2026-08-17, scale not to scale. Reference links to "
            "infernalcode.com, wiki.infernalcode.com and github.com/lowcache.",
        )
        + "".join(body)
        + d.svg_close()
    )


# --------------------------------------------------------------------- main ----
SHEETS = {
    "sheet-lc000.svg": sheet_lc000,
    "sheet-lc100.svg": sheet_lc100,
    "sheet-lc200.svg": sheet_lc200,
    "sheet-lc900.svg": sheet_lc900,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in SHEETS.items():
        svg = fn()
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"{name:24} {len(svg):>8,} bytes")


if __name__ == "__main__":
    main()
