#!/usr/bin/env python3
"""The map of Perdition Basin — a hand-authored period map, drawn as inline SVG
so it inlines byte-cheap into any of the books and scales crisply on a phone.

One shared base (`_base`) draws the honest geography a character would know:
the Calvary River and its wells, the three towns, the ruined mission, the mesas,
the trails. `player_map_html()` ships that alone. `keeper_map_html()` adds the
secrets overlay — which wells are bound / failing / broken, the ring of nails,
what sleeps beneath, faction reach, and the two starter-adventure sites — drawn
from the same coordinate model so the two layers register exactly.

Both books import this; nothing is baked into the HTML sources, so the map is
edited here and regenerated at build time.
"""

# ---- palette (matches the books' CSS custom properties) ----
INK = "#2b2118"; INK_S = "#4a3c2c"
BLOOD = "#8b1a1a"; BLOOD_D = "#6c1212"
GOLD = "#9c7a3c"; GOLD_D = "#7d5f2a"
SHADE = "#3a2616"
PAPER = "#e7d8ab"; PAPER_L = "#efe6cf"
WATER = "#5f7a78"
AMBER = "#b5762a"

W, H = 960, 620

# ---- the shared coordinate model (label anchor points) ----
LOC = {
    "crossing": (500, 286),   # Calvary Crossing — county seat, at the river ford
    "coffin":   (315, 405),   # Coffin Wells — dying cattle town (Adventure 1)
    "saltlick": (782, 176),   # Saltlick Station — stage relay (Adventure 2)
    "mission":  (430, 452),   # Mission San Clavo — the ruined cursed heart
    "homestead":(392, 346),   # the outlying homesteads (the feeding shows here first)
    "mesa":     (720, 452),   # the Painted Mesa — the First Peoples' ground
}

# wells / springs of the binding ring: (x, y, name, state)   state: bound|failing|broken
WELLS = [
    (315, 405, "Coffin Wells",   "broken"),   # the Nightwalker — Adventure 1
    (430, 452, "the Mission spring", "failing"),
    (500, 286, "Crossing well",  "bound"),
    (782, 176, "Saltlick well",  "failing"),   # the Skin-Walker's ground — Adventure 2
    (720, 452, "Painted spring", "bound"),
    (352, 150, "the North seep", "bound"),
    (636, 232, "Roadman's well", "bound"),
    (560, 520, "the South well", "broken"),
]


def _label(x, y, text, size=15, font="'EB Garamond',Georgia,serif", color=INK,
           anchor="middle", weight="600", caps=False, italic=False, dy=0):
    style = (f"font-family:{font};font-size:{size}px;font-weight:{weight};"
             f"fill:{color};")
    if caps:
        style += "font-variant:small-caps;letter-spacing:.06em;"
    if italic:
        style += "font-style:italic;"
    # paint a paper-coloured halo behind the glyphs for legibility over linework
    return (f'<text x="{x}" y="{y+dy}" text-anchor="{anchor}" style="{style}" '
            f'stroke="{PAPER_L}" stroke-width="3" paint-order="stroke" '
            f'stroke-linejoin="round">{text}</text>')


def _town(x, y, seat=False):
    if seat:
        # county seat — a ringed cluster with a church cross
        return (f'<g stroke="{INK}" stroke-width="1.6" fill="{PAPER_L}">'
                f'<circle cx="{x}" cy="{y}" r="9"/>'
                f'<circle cx="{x}" cy="{y}" r="4.5" fill="{BLOOD_D}" stroke="none"/>'
                f'</g>'
                f'<path d="M{x} {y-20} V{y-9} M{x-4} {y-16} H{x+4}" '
                f'stroke="{INK}" stroke-width="1.6" fill="none"/>')
    # ordinary town — a small filled square (a cluster of roofs)
    return (f'<g stroke="{INK}" stroke-width="1.4" fill="{PAPER_L}">'
            f'<rect x="{x-6}" y="{y-6}" width="12" height="12"/>'
            f'<rect x="{x-1.5}" y="{y-1.5}" width="7" height="7" '
            f'fill="{INK_S}" stroke="none"/></g>')


def _station(x, y):
    # a lone building — trapezoid roof + box
    return (f'<g stroke="{INK}" stroke-width="1.4" fill="{PAPER_L}">'
            f'<rect x="{x-7}" y="{y-2}" width="14" height="10"/>'
            f'<path d="M{x-9} {y-2} L{x-4} {y-9} H{x+4} L{x+9} {y-2} Z"/></g>')


def _mission(x, y):
    # a ruined mission — a broken facade with a leaning cross
    return (f'<g stroke="{INK}" stroke-width="1.5" fill="{PAPER_L}">'
            f'<path d="M{x-11} {y+8} V{y-6} L{x} {y-13} L{x+11} {y-6} V{y+8}" '
            f'stroke-linejoin="round"/>'
            f'<path d="M{x-4} {y+8} V{y-2} H{x+4} V{y+8}" fill="{INK_S}" stroke="none"/>'
            f'</g>'
            f'<path d="M{x} {y-24} V{y-13} M{x-3.5} {y-20} H{x+3.5}" '
            f'stroke="{INK}" stroke-width="1.6" fill="none" transform="rotate(9 {x} {y-18})"/>')


def _well(x, y):
    # a plain well ring (base map — no state shown)
    return (f'<circle cx="{x}" cy="{y}" r="4.4" fill="none" stroke="{INK}" '
            f'stroke-width="1.4"/><circle cx="{x}" cy="{y}" r="1.3" fill="{INK}"/>')


def _mesa(x, y, w=64, h=30):
    # a flat-topped mesa with hachured flanks
    top = h * 0.42
    left, right = x - w / 2, x + w / 2
    body = (f'<path d="M{left+8} {y} L{left+14} {y-top} H{right-14} L{right-8} {y} Z" '
            f'fill="{PAPER_L}" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round"/>')
    hatch = "".join(
        f'<line x1="{left+14+i*((w-28)/6)}" y1="{y-top}" '
        f'x2="{left+8+i*((w-16)/6)}" y2="{y}" stroke="{INK_S}" stroke-width="0.8"/>'
        for i in range(7))
    return f'<g>{body}{hatch}</g>'


def _compass(x, y, r=30):
    tip, w = r - 3, 6
    parts = [f'<circle r="{r}" fill="{PAPER_L}" stroke="{INK}" stroke-width="1.2"/>',
             f'<circle r="{r-5}" fill="none" stroke="{GOLD_D}" stroke-width="0.8"/>']
    # minor (diagonal) points, thin and light
    mtip = (r - 3) * 0.66
    for rot in (45, 135, 225, 315):
        parts.append(f'<g transform="rotate({rot})">'
                     f'<path d="M0 {-mtip:.1f} L3 0 L-3 0 Z" fill="{PAPER_L}" '
                     f'stroke="{INK_S}" stroke-width="0.6" stroke-linejoin="round"/></g>')
    # the four cardinal points, each faceted light (left) / dark (right)
    for rot in (0, 90, 180, 270):
        parts.append(f'<g transform="rotate({rot})">'
                     f'<path d="M0 {-tip} L{w} 0 L0 0 Z" fill="{INK}"/>'
                     f'<path d="M0 {-tip} L{-w} 0 L0 0 Z" fill="{PAPER_L}" '
                     f'stroke="{INK}" stroke-width="0.7" stroke-linejoin="round"/></g>')
    parts.append(f'<circle r="1.8" fill="{INK}"/>')
    parts.append(f'<text x="0" y="{-r-7}" text-anchor="middle" fill="{BLOOD_D}" '
                 f'style="font-family:\'Rye\',Georgia,serif;font-size:13px">N</text>')
    return f'<g transform="translate({x},{y})">{"".join(parts)}</g>'


def _scalebar(x, y):
    seg = 40
    parts = [f'<line x1="{x}" y1="{y}" x2="{x+seg*2}" y2="{y}" stroke="{INK}" stroke-width="2"/>']
    for i in range(2):
        fill = INK if i % 2 == 0 else PAPER_L
        parts.append(f'<rect x="{x+i*seg}" y="{y-3}" width="{seg}" height="6" '
                     f'fill="{fill}" stroke="{INK}" stroke-width="1"/>')
    parts.append(_label(x, y+16, "0", 11))
    parts.append(_label(x+seg, y+16, "5", 11))
    parts.append(_label(x+seg*2, y+16, "10 miles", 11, anchor="middle"))
    return "<g>" + "".join(parts) + "</g>"


# ---- the shared base map ----
def _base():
    p = []
    # aged-linen panel + double frame (echoes the book page frame)
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{PAPER_L}"/>')
    p.append(f'<rect x="10" y="10" width="{W-20}" height="{H-20}" fill="none" '
             f'stroke="{BLOOD_D}" stroke-width="3"/>')
    p.append(f'<rect x="16" y="16" width="{W-32}" height="{H-32}" fill="none" '
             f'stroke="{GOLD_D}" stroke-width="1"/>')

    # the Calvary River — wet (solid) in the north, drying (dashed) to the south
    river_wet = "M410 54 C 380 96, 352 124, 352 150 S 440 248, 500 286"
    river_dry = "M500 286 C 528 340, 548 430, 560 520 S 572 578, 566 600"
    p.append(f'<path d="{river_wet}" fill="none" stroke="{WATER}" stroke-width="4.5" '
             f'stroke-linecap="round"/>')
    p.append(f'<path d="{river_wet}" fill="none" stroke="{WATER}" stroke-width="8" '
             f'stroke-linecap="round" opacity="0.18"/>')
    p.append(f'<path d="{river_dry}" fill="none" stroke="{WATER}" stroke-width="3.2" '
             f'stroke-dasharray="2 6" stroke-linecap="round" opacity="0.8"/>')
    p.append(_label(268, 214, "the Calvary River", 13.5, color=WATER, italic=True,
                    anchor="start", weight="500"))

    # a faint basin contour (the rim of the low country)
    p.append(f'<path d="M120 250 C 180 120, 420 70, 620 110 C 830 150, 900 320, '
             f'820 470 C 740 600, 380 600, 220 500 C 90 420, 80 360, 120 250 Z" '
             f'fill="none" stroke="{GOLD_D}" stroke-width="1" stroke-dasharray="1 7" '
             f'opacity="0.7"/>')

    # mesas / buttes and a badlands field
    p.append(_mesa(*LOC["mesa"], w=86, h=40))
    p.append(_mesa(844, 300, w=58, h=26))
    p.append(_mesa(206, 232, w=50, h=22))
    # badlands stipple, south-central (below the dry river, clear of the legend)
    seed = 1
    stip = []
    for i in range(52):
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        sx = 452 + (seed % 168)
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        sy = 540 + (seed % 48)
        stip.append(f'<path d="M{sx} {sy} l3 -4 l3 4" fill="none" stroke="{INK_S}" '
                    f'stroke-width="0.7"/>')
    p.append('<g opacity="0.7">' + "".join(stip) + "</g>")
    p.append(_label(536, 534, "the Badlands", 12.5, color=INK_S, italic=True, anchor="middle"))

    # trails (dashed, with the stage road heavier)
    def trail(a, b, mid=None, heavy=False, dash="7 5"):
        ax, ay = LOC[a]; bx, by = LOC[b]
        d = f"M{ax} {ay} " + (f"Q{mid[0]} {mid[1]} {bx} {by}" if mid else f"L{bx} {by}")
        wsu = 2.6 if heavy else 1.6
        return (f'<path d="{d}" fill="none" stroke="{SHADE}" stroke-width="{wsu}" '
                f'stroke-dasharray="{dash}" stroke-linecap="round" opacity="0.85"/>')
    p.append(trail("crossing", "saltlick", mid=(636, 210), heavy=True))   # the Stage Road
    p.append(trail("coffin", "crossing", mid=(388, 360)))                 # cattle trail
    p.append(trail("coffin", "mission", mid=(360, 448)))
    p.append(trail("crossing", "mesa", mid=(624, 388)))
    p.append(trail("homestead", "coffin"))
    p.append(_label(642, 196, "the Stage Road", 12.5, color=SHADE, italic=True,
                    anchor="middle", dy=-6))

    # settlements + sites
    cx, cy = LOC["crossing"]; p.append(_town(cx, cy, seat=True))
    p.append(_label(cx, cy + 26, "Calvary Crossing", 16, color=BLOOD_D, caps=True, weight="700"))
    p.append(_label(cx, cy + 40, "county seat", 11.5, color=INK_S, italic=True))

    fx, fy = LOC["coffin"]; p.append(_town(fx, fy))
    p.append(_label(fx, fy + 24, "Coffin Wells", 15, color=INK, caps=True, weight="700"))

    sx, sy = LOC["saltlick"]; p.append(_station(sx, sy))
    p.append(_label(sx, sy + 24, "Saltlick Station", 14.5, color=INK, caps=True, weight="700"))

    mx, my = LOC["mission"]; p.append(_mission(mx, my))
    p.append(_label(mx - 4, my + 24, "Mission San Clavo", 13.5, color=SHADE, italic=True))

    hx, hy = LOC["homestead"]
    for ox, oy in ((-8, -4), (6, 2), (-2, 10)):
        p.append(f'<rect x="{hx+ox-3}" y="{hy+oy-3}" width="6" height="6" '
                 f'fill="{PAPER_L}" stroke="{INK}" stroke-width="1"/>')
    p.append(_label(hx - 12, hy - 12, "homesteads", 12, color=INK_S, italic=True, anchor="middle"))

    mesx, mesy = LOC["mesa"]
    p.append(_label(mesx, mesy + 4, "the Painted Mesa", 13, color=INK, caps=True,
                    weight="600", anchor="middle"))

    # wells of the ring (plain on the base map)
    for wx, wy, name, _state in WELLS:
        if (wx, wy) in [LOC["crossing"], LOC["coffin"], LOC["saltlick"], LOC["mesa"]]:
            continue  # these coincide with a settlement marker
        p.append(_well(wx, wy))

    # furniture
    p.append(_compass(884, 108))
    p.append(_scalebar(724, 566))

    # title cartouche, top-left
    p.append(f'<g>'
             f'<rect x="40" y="42" width="330" height="62" rx="3" fill="{PAPER}" '
             f'stroke="{GOLD_D}" stroke-width="1.5"/>'
             f'<rect x="45" y="47" width="320" height="52" rx="2" fill="none" '
             f'stroke="{BLOOD_D}" stroke-width="0.8"/>'
             f'<text x="205" y="78" text-anchor="middle" '
             f'style="font-family:\'Rye\',Georgia,serif;font-size:27px;fill:{BLOOD_D}">'
             f'Perdition Basin</text>'
             f'<text x="205" y="95" text-anchor="middle" '
             f'style="font-family:\'EB Garamond\',serif;font-size:12px;font-style:italic;'
             f'fill:{INK_S}">the Calvary Wells country</text></g>')
    return "".join(p)


def _legend(rows, title):
    x, y, w = 40, 460, 302
    h = 32 + len(rows) * 23
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{PAPER}" '
             f'stroke="{GOLD_D}" stroke-width="1.2" opacity="0.97"/>',
             f'<text x="{x+14}" y="{y+22}" style="font-family:\'Playfair Display\',serif;'
             f'font-size:14px;font-weight:700;fill:{SHADE}">{title}</text>']
    for i, (glyph, text) in enumerate(rows):
        ly = y + 46 + i * 23
        # <b>..</b> is not valid inside SVG <text>; use <tspan> for emphasis
        text = text.replace("<b>", '<tspan style="font-weight:700">').replace("</b>", "</tspan>")
        parts.append(f'<g transform="translate({x+22},{ly-4})">{glyph}</g>')
        parts.append(f'<text x="{x+46}" y="{ly}" style="font-family:\'EB Garamond\',serif;'
                     f'font-size:12.5px;fill:{INK}">{text}</text>')
    return "<g>" + "".join(parts) + "</g>"


def _svg(inner, cls):
    return (f'<svg viewBox="0 0 {W} {H}" class="{cls}" role="img" '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'preserveAspectRatio="xMidYMid meet">{inner}</svg>')


def player_map_html():
    legend = _legend([
        (f'<g stroke="{INK}" stroke-width="1.4" fill="{PAPER_L}"><circle r="6"/>'
         f'<circle r="3" fill="{BLOOD_D}" stroke="none"/></g>', "town &amp; county seat"),
        (_well(0, 0), "a well or spring"),
        (f'<line x1="-8" y1="0" x2="8" y2="0" stroke="{SHADE}" stroke-width="2" '
         f'stroke-dasharray="6 4"/>', "wagon road &amp; trail"),
        (f'<path d="M-8 4 C -2 -4, 2 4, 8 -2" fill="none" stroke="{WATER}" '
         f'stroke-width="3"/>', "the river (dry in the south)"),
    ], "The Country")
    inner = _base() + legend
    return ('<figure class="map map-full">' + _svg(inner, "bg-map") +
            '<figcaption>Perdition Basin &mdash; the honest country, as any soul who has '
            'ridden it could draw it in the dirt.</figcaption></figure>')


def keeper_map_html():
    over = []
    # faction reach — low-opacity washes
    # the Land-and-Cattle money (west, around the ranch towns and homesteads)
    over.append(f'<path d="M232 336 C 300 288, 470 292, 528 344 C 556 448, 400 528, '
                f'292 494 C 210 466, 200 392, 232 336 Z" fill="{GOLD}" opacity="0.11"/>')
    # the Painted Mesa people (south-east)
    over.append(f'<path d="M566 372 C 648 384, 792 420, 812 486 C 770 566, 620 548, '
                f'596 506 C 560 470, 540 412, 566 372 Z" fill="#4c6b3a" opacity="0.13"/>')
    # the Mission's taint, spreading from San Clavo
    over.append(f'<circle cx="430" cy="452" r="66" fill="{BLOOD}" opacity="0.08"/>')

    # the ring of nails — a dotted blood ring through the bound wells
    bound = [(wx, wy) for wx, wy, _n, s in WELLS if s != "broken"]
    ring = "M" + " L".join(f"{x} {y}" for x, y in sorted(bound, key=lambda p: (
        (p[0]-480)**2 + (p[1]-320)**2)))
    # draw ring as a smooth-ish closed loop around the basin instead (ordered by angle)
    import math
    cxr, cyr = 500, 330
    ordered = sorted(bound, key=lambda p: math.atan2(p[1]-cyr, p[0]-cxr))
    ringd = "M" + " L".join(f"{x} {y}" for x, y in ordered) + " Z"
    over.append(f'<path d="{ringd}" fill="none" stroke="{BLOOD_D}" stroke-width="1.4" '
                f'stroke-dasharray="1 8" stroke-linecap="round" opacity="0.85"/>')

    # well states
    def bound_mark(x, y):
        return (f'<circle cx="{x}" cy="{y}" r="7" fill="none" stroke="{GOLD_D}" '
                f'stroke-width="2"/><circle cx="{x}" cy="{y}" r="2" fill="{GOLD_D}"/>')
    def failing_mark(x, y):
        return (f'<circle cx="{x}" cy="{y}" r="7" fill="none" stroke="{AMBER}" '
                f'stroke-width="2" stroke-dasharray="3 3"/>'
                f'<path d="M{x} {y-7} L{x+2} {y} L{x-2} {y+2} L{x} {y+7}" fill="none" '
                f'stroke="{AMBER}" stroke-width="1.2"/>')
    def broken_mark(x, y):
        return (f'<circle cx="{x}" cy="{y}" r="7" fill="{BLOOD}" opacity="0.25"/>'
                f'<path d="M{x-6} {y-6} L{x+6} {y+6} M{x+6} {y-6} L{x-6} {y+6}" '
                f'stroke="{BLOOD_D}" stroke-width="2"/>')
    for wx, wy, name, state in WELLS:
        mark = {"bound": bound_mark, "failing": failing_mark, "broken": broken_mark}[state]
        over.append(mark(wx, wy))

    # what sleeps beneath the broken wells / the truths
    over.append(_label(315, 372, "Nightwalker &mdash; risen", 11, color=BLOOD_D,
                       weight="700", anchor="middle"))
    over.append(_label(560, 500, "the South well: gone", 11, color=BLOOD_D,
                       weight="700", anchor="middle"))
    over.append(_label(430, 500, "the seal is cracking", 10.5, color=BLOOD_D,
                       italic=True, anchor="middle"))
    over.append(_label(782, 216, "a face not its own", 10.5, color=AMBER,
                       weight="700", anchor="middle"))

    # adventure-site pins
    def pin(x, y, n):
        return (f'<circle cx="{x}" cy="{y}" r="10" fill="{BLOOD_D}" stroke="{PAPER_L}" '
                f'stroke-width="1.5"/><text x="{x}" y="{y+4}" text-anchor="middle" '
                f'stroke="none" fill="{PAPER_L}" style="font-family:\'Playfair Display\','
                f'serif;font-weight:700;font-size:12px">{n}</text>')
    over.append(pin(282, 388, "1"))   # Coffin Wells — The Salt at Coffin Wells
    over.append(pin(816, 148, "2"))   # Saltlick — A Face Not His Own

    legend = _legend([
        (bound_mark(0, 0), "well still <b>bound</b> (nail holds)"),
        (failing_mark(0, 0), "binding <b>failing</b>"),
        (broken_mark(0, 0), "well <b>broken</b> &mdash; something woke"),
        (f'<path d="M-8 0 L8 0" stroke="{BLOOD_D}" stroke-width="1.4" '
         f'stroke-dasharray="1 6"/>', "the ring of nails (the padres&rsquo; seal)"),
        (pin(0, 0, "&#9679;"), "starter-adventure site"),
    ], "The Keeper's Country")
    inner = _base() + '<g>' + "".join(over) + '</g>' + legend
    return ('<figure class="map map-full">' + _svg(inner, "bg-map") +
            '<figcaption>Perdition Basin &mdash; the same country with its wounds shown: '
            'the failing seal, and what each broken well let up.</figcaption></figure>')


if __name__ == "__main__":
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    page = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Playfair+Display:wght@400;700&family=Rye&display=swap" rel="stylesheet">
<style>body{background:#e7d8ab;margin:0;padding:16px}.map{margin:0 0 24px}svg{width:100%;height:auto;display:block}
figcaption{font-family:'EB Garamond',serif;font-style:italic;color:#4a3c2c;font-size:14px;text-align:center;margin-top:6px}</style>
</head><body>__BODY__</body></html>"""
    body = ""
    if which in ("player", "both"):
        body += player_map_html()
    if which in ("keeper", "both"):
        body += keeper_map_html()
    open("_map_preview.html", "w", encoding="utf-8").write(page.replace("__BODY__", body))
    print("wrote _map_preview.html")
