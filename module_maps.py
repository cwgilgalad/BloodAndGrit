#!/usr/bin/env python3
"""The three module maps, drawn from one coordinate model apiece.

Same discipline as `perdition_map.py`: the map is not an image somebody drew and then described,
it is geometry declared once and rendered outward. That matters more here than it did there,
because a module map has to agree with a module — every place the map names is a scene the Keeper
will run, and a map that shows a tack room the adventure never keys is a map that will get a table
lost. So each feature carries the anchor of the scene it belongs to (`data-scene`), and
`audit_maps.py` walks both sides and fails if either names something the other does not.

Two outputs from the same model:
  * `map_html(slug)` — inline SVG for the module book, with a download control beside it.
  * `python module_maps.py` — writes `map-<slug>.svg` beside the books, so the map can be handed
    to a table on its own, printed, or dropped into a virtual tabletop.

The inline copy and the standalone file are the same serialization, so they cannot disagree.
"""
import html as _html

# ---------------------------------------------------------------- palette
# Print-first. These maps are meant to survive a home printer in black and white, so every feature
# is distinguished by shape and label as well as by ink — colour is the last cue, never the only one.
INK      = "#2a1f19"
INK_SOFT = "#6b5a4b"
PAPER    = "#f2ead6"
BLOOD    = "#8f2a22"
GOLD     = "#9a7b3f"
WATER    = "#5f7f86"
STONE    = "#c9bda2"


def esc(s):
    return _html.escape(str(s), quote=True)


# ---------------------------------------------------------------- primitives

def _lab(x, y, text, size=13, anchor="middle", cls="lab", weight=700, ink=INK, dy=0):
    return (f'<text x="{x}" y="{y + dy}" class="{cls}" text-anchor="{anchor}" '
            f'font-size="{size}" font-weight="{weight}" fill="{ink}">{esc(text)}</text>')


def feature(key, scene, label, body, lx, ly, size=13, anchor="middle"):
    """One keyed place. The `data-key`/`data-scene` pair is what the auditor reads; the `<title>`
    is what a screen reader and a hover tooltip read. All three say the same thing on purpose."""
    return (f'<g class="feat" data-key="{esc(key)}" data-scene="{esc(scene)}">'
            f'<title>{esc(label)}</title>{body}'
            f'{_lab(lx, ly, label, size=size, anchor=anchor)}</g>')


def building(x, y, w, h, fill=STONE, rot=0):
    t = f' transform="rotate({rot} {x + w / 2} {y + h / 2})"' if rot else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
            f'stroke="{INK}" stroke-width="2"{t}/>')


def hut(x, y, w=34, h=26):
    return (f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{STONE}" stroke="{INK}" '
            f'stroke-width="1.8"/><path d="M{x - 4} {y} L{x + w / 2} {y - 13} L{x + w + 4} {y}" '
            f'fill="{STONE}" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/></g>')


def cross(x, y, s=13):
    return (f'<path d="M{x} {y - s} V{y + s} M{x - s * 0.62} {y - s * 0.34} H{x + s * 0.62}" '
            f'stroke="{INK}" stroke-width="2.6" stroke-linecap="round" fill="none"/>')


def wellsym(x, y, r=9):
    return (f'<g><circle cx="{x}" cy="{y}" r="{r}" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>'
            f'<circle cx="{x}" cy="{y}" r="{r * 0.42}" fill="{WATER}"/></g>')


def grave(x, y, open_=False):
    fill = "#241a15" if open_ else PAPER
    dash = ' stroke-dasharray="5 3"' if open_ else ""
    return (f'<g><rect x="{x - 11}" y="{y - 7}" width="22" height="15" fill="{fill}" '
            f'stroke="{INK}" stroke-width="1.7"{dash}/>'
            f'<path d="M{x - 11} {y - 7} a11 11 0 0 1 22 0" fill="{fill}" stroke="{INK}" '
            f'stroke-width="1.7"{dash}/></g>')


def trail(d, dash="9 7", w=2.6, ink=INK_SOFT):
    return f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{w}" stroke-dasharray="{dash}" stroke-linecap="round"/>'


def rough(d, ink=INK_SOFT, w=1.8):
    return f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{w}" stroke-linecap="round"/>'


def mesa(x, y, w, h):
    return (f'<path d="M{x} {y} L{x + w * 0.14} {y - h} L{x + w * 0.86} {y - h} L{x + w} {y} Z" '
            f'fill="#dcd0b4" stroke="{INK_SOFT}" stroke-width="1.6"/>')


def compass(x, y, r=24):
    return (f'<g class="compass"><circle cx="{x}" cy="{y}" r="{r}" fill="{PAPER}" stroke="{INK}" '
            f'stroke-width="1.6"/><path d="M{x} {y - r + 4} L{x + 6} {y + 5} L{x} {y + 1} '
            f'L{x - 6} {y + 5} Z" fill="{BLOOD}" stroke="{INK}" stroke-width="1"/>'
            f'{_lab(x, y + r + 13, "N", size=13)}</g>')


def scalebar(x, y, px, label):
    """A stated scale, which is the difference between a map and a picture."""
    return (f'<g class="scalebar"><path d="M{x} {y} H{x + px}" stroke="{INK}" stroke-width="2.4"/>'
            f'<path d="M{x} {y - 5} V{y + 5} M{x + px} {y - 5} V{y + 5} '
            f'M{x + px / 2} {y - 4} V{y + 4}" stroke="{INK}" stroke-width="2"/>'
            f'{_lab(x + px / 2, y + 18, label, size=12, weight=600, ink=INK_SOFT)}</g>')


def legend(x, y, rows, w=196):
    h = 24 + 19 * len(rows)
    out = [f'<g class="legend"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PAPER}" '
           f'stroke="{INK}" stroke-width="1.6" opacity="0.96"/>',
           _lab(x + 10, y + 16, "Legend", size=12.5, anchor="start", ink=BLOOD)]
    for i, (mark, text) in enumerate(rows):
        cy = y + 34 + 19 * i
        out.append(mark(x + 18, cy))
        out.append(_lab(x + 34, cy + 4, text, size=11.5, anchor="start", weight=500, ink=INK))
    out.append("</g>")
    return "".join(out)


def _m_square(c):
    return lambda x, y: f'<rect x="{x - 7}" y="{y - 6}" width="14" height="12" fill="{c}" stroke="{INK}" stroke-width="1.5"/>'


def _m_well(x, y):
    return wellsym(x, y, r=6.5)


def _m_grave(x, y):
    return grave(x, y)


def _m_open(x, y):
    return grave(x, y, open_=True)


def _m_cross(x, y):
    return cross(x, y, s=8)


def _m_trail(x, y):
    return f'<path d="M{x - 9} {y} H{x + 9}" stroke="{INK_SOFT}" stroke-width="2.4" stroke-dasharray="6 5"/>'


def _m_fight(x, y):
    return (f'<path d="M{x - 7} {y - 7} L{x + 7} {y + 7} M{x + 7} {y - 7} L{x - 7} {y + 7}" '
            f'stroke="{BLOOD}" stroke-width="2.8" stroke-linecap="round"/>')


def _m_water(x, y):
    return f'<path d="M{x - 9} {y} q4.5 -5 9 0 q4.5 5 9 0" stroke="{WATER}" stroke-width="2.4" fill="none"/>'


def fightmark(x, y, n):
    """Where a keyed fight happens. Crossed sabres, numbered to the scene."""
    return (f'<g>{_m_fight(x, y)}<circle cx="{x + 13}" cy="{y - 11}" r="9" fill="{BLOOD}"/>'
            f'{_lab(x + 13, y - 7, n, size=11.5, ink=PAPER)}</g>')


def pin(x, y, n):
    """A numbered scene pin — the number is the scene number printed in the module's margin."""
    return (f'<g><circle cx="{x}" cy="{y}" r="10.5" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>'
            f'{_lab(x, y + 4, n, size=12, ink=INK)}</g>')


# ---------------------------------------------------------------- map I

def _map_salt():
    W, H = 1000, 660
    s = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="{PAPER}"/>']

    # country: the creek, the road east, two mesas
    s.append(rough(f"M40 470 q120 -34 210 -12 q130 32 250 -6 q140 -46 250 -10 q100 30 210 8",
                   ink=WATER, w=3.4))
    s.append(_lab(196, 496, "Perdition Creek", size=12, weight=500, ink=WATER))
    s.append(mesa(760, 214, 190, 74))
    s.append(_lab(855, 152, "Ladder Mesa", size=12, weight=500, ink=INK_SOFT))
    s.append(mesa(58, 208, 150, 60))
    s.append(_lab(133, 160, "The Sisters", size=12, weight=500, ink=INK_SOFT))

    s.append(trail("M262 330 H612"))
    s.append(_lab(437, 318, "the mission road — four miles", size=11.5, weight=500, ink=INK_SOFT))
    s.append(trail("M196 356 L236 452 L318 520"))
    s.append(_lab(276, 546, "the Pell road", size=11.5, weight=500, ink=INK_SOFT))

    # ---- Coffin Wells
    s.append(f'<rect x="70" y="236" width="196" height="150" rx="6" fill="#e7dcc0" '
             f'stroke="{GOLD}" stroke-width="2" stroke-dasharray="7 5"/>')
    s.append(feature("town", "hook", "Coffin Wells",
                     wellsym(168, 258), 168, 236 - 10))

    s.append(feature("saloon", "a1-saloon", "The Ipswich House",
                     building(92, 286, 62, 34) + pin(84, 282, "1"), 123, 336, size=12))
    s.append(feature("vane", "a1-vane", "Vane's House",
                     building(190, 286, 54, 34) + pin(246, 282, "2"), 217, 336, size=12))
    s.append(feature("store", "cast", "Tuttle's Store",
                     building(120, 342, 52, 28), 146, 382, size=11.5))

    s.append(feature("boothill", "a1-boothill", "The Boot-Hill",
                     grave(300, 244) + grave(332, 250) + grave(364, 244, open_=True)
                     + grave(316, 274) + grave(350, 278) + pin(392, 240, "3"),
                     332, 302, size=12))

    # ---- the Pell place
    s.append(feature("pell", "a2-arrive", "The Pell Place",
                     hut(330, 528, 52, 34) + hut(400, 540, 40, 26) + pin(310, 524, "5")
                     + fightmark(414, 586, "6"), 384, 604, size=12.5))
    s.append(feature("cellar", "a2-cellar", "The Cellar",
                     f'<path d="M336 562 l14 22 h30 l-14 -22 Z" fill="#241a15" stroke="{INK}" '
                     f'stroke-width="1.7"/>' + pin(300, 586, "7"), 300, 616, size=11.5))

    # ---- the mission
    s.append(f'<rect x="628" y="352" width="286" height="196" rx="6" fill="#e7dcc0" '
             f'stroke="{GOLD}" stroke-width="2" stroke-dasharray="7 5"/>')
    s.append(feature("mission", "a3-mission", "Mission San Clavo",
                     building(650, 380, 128, 84) + cross(714, 356) + pin(636, 376, "8"),
                     714, 484, size=13))
    s.append(feature("wall", "a3-mission", "The Carved Wall",
                     f'<path d="M650 380 V464" stroke="{BLOOD}" stroke-width="5.5" '
                     f'stroke-linecap="round"/>', 618, 428, size=11.5, anchor="end"))
    s.append(feature("graveyard", "a3-vane", "The East Ground",
                     grave(812, 396) + grave(846, 402) + grave(880, 396) + grave(828, 428)
                     + pin(896, 428, "9"), 846, 386, size=12))
    s.append(feature("opengrave", "a3-thing", "The Opened Grave",
                     grave(866, 430, open_=True) + fightmark(866, 468, "10"),
                     852, 512, size=12))

    s.append(compass(940, 92))
    s.append(scalebar(628, 604, 150, "one mile"))
    # y=486, not 546: six rows stand 138 tall and the sheet is 660, so the old origin ran the box
    # 24px off the bottom edge. It looked fine in a browser, which scales the viewBox to fit.
    s.append(legend(52, 486, [
        (_m_square(STONE), "building"),
        (_m_well, "well or water"),
        (_m_grave, "grave, undisturbed"),
        (_m_open, "grave, opened"),
        (_m_fight, "a keyed fight"),
        (_m_trail, "trail or road"),
    ], w=186))

    return W, H, "".join(s), "The Night at Coffin Wells"


# ---------------------------------------------------------------- map II

def _map_face():
    W, H = 1000, 660
    s = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="{PAPER}"/>']

    s.append(rough("M0 128 q180 -30 340 4 q200 42 380 -6 q150 -40 280 -6", ink=INK_SOFT, w=1.6))
    s.append(_lab(150, 106, "open flat, no cover for a mile", size=11.5, weight=500, ink=INK_SOFT))

    s.append(trail("M0 208 H1000", dash="12 9", w=3.2))
    s.append(feature("road", "hook", "The Coach Road — Calvary Crossing to the north line",
                     "", 500, 194, size=12, anchor="middle"))

    # the yard, which everything faces
    s.append(f'<rect x="196" y="264" width="600" height="304" rx="8" fill="#e9dfc4" '
             f'stroke="{GOLD}" stroke-width="2" stroke-dasharray="8 6"/>')
    s.append(feature("yard", "a3-yard", "The Yard",
                     fightmark(492, 430, "11"), 492, 484, size=13.5))

    s.append(feature("station", "a1-house", "The Station House",
                     building(214, 286, 208, 118) + pin(200, 282, "1"), 318, 424, size=12.5))
    s.append(feature("common", "a1-common", "The Common Room",
                     f'<rect x="228" y="300" width="122" height="90" fill="#ded2b4" '
                     f'stroke="{INK}" stroke-width="1.4"/>' + pin(238, 396, "2"),
                     306, 316, size=11.5))
    s.append(feature("bunks", "a2-bunks", "The Bunk Row",
                     f'<rect x="356" y="300" width="58" height="90" fill="#ded2b4" '
                     f'stroke="{INK}" stroke-width="1.4"/>'
                     + rough("M362 316 H408 M362 334 H408 M362 352 H408 M362 370 H408")
                     + pin(430, 300, "6"), 386, 316, size=11.5))

    s.append(feature("tack", "a2-tack", "The Tack Room",
                     building(214, 436, 118, 96, fill="#d7c9a8") + fightmark(272, 484, "8")
                     + pin(200, 432, "8"), 272, 552, size=12.5))

    s.append(feature("barn", "a1-barn", "The Barn",
                     building(586, 286, 172, 136) + rough("M586 354 H758", w=1.5)
                     + pin(772, 282, "3"), 672, 444, size=12.5))
    s.append(feature("stalls", "a1-barn", "The Stalls",
                     rough("M600 300 V352 M628 300 V352 M656 300 V352 M684 300 V352 M712 300 V352", w=1.5),
                     672, 316, size=11.5))

    s.append(feature("corral", "a1-corral", "The Corral",
                     f'<path d="M586 452 H772 V556 H586 Z" fill="none" stroke="{INK}" '
                     f'stroke-width="2.2" stroke-dasharray="3 6"/>' + pin(786, 448, "4"),
                     680, 580, size=12))

    s.append(feature("well", "a2-well", "The Well",
                     wellsym(492, 300, r=13) + pin(524, 288, "5"), 492, 340, size=12))

    s.append(feature("ice", "a2-ice", "The Ice House",
                     building(400, 486, 84, 62, fill="#cfd8d4") + pin(390, 482, "7"),
                     442, 566, size=12))

    s.append(feature("privy", "a3-privy", "The Privy, and the Ash Line",
                     building(516, 496, 40, 44)
                     + f'<path d="M500 486 q60 -22 120 0" stroke="{GOLD}" stroke-width="3.4" '
                       f'stroke-dasharray="2 5" fill="none"/>' + pin(568, 492, "12"),
                     560, 566, size=11.5))

    s.append(compass(940, 96))
    s.append(scalebar(214, 620, 160, "forty paces"))
    s.append(legend(806, 470, [
        (_m_square(STONE), "roofed building"),
        (_m_square("#d7c9a8"), "outbuilding"),
        (_m_well, "the well"),
        (_m_fight, "a keyed fight"),
        (_m_trail, "road"),
    ], w=178))

    return W, H, "".join(s), "Saltlick Station"


# ---------------------------------------------------------------- map III

def _map_water():
    W, H = 1000, 760
    s = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="{PAPER}"/>']

    # ---------- upper panel: the ground
    s.append(f'<rect x="24" y="24" width="952" height="392" rx="6" fill="none" '
             f'stroke="{INK_SOFT}" stroke-width="1.4"/>')
    s.append(_lab(60, 50, "Above — the mission and the road to it", size=13,
                  anchor="start", ink=BLOOD))

    s.append(rough("M40 330 q140 -26 250 -6 q140 26 250 -10 q120 -32 240 -4", ink=WATER, w=3.2))
    s.append(_lab(190, 356, "Perdition Creek, running wrong", size=11.5, weight=500, ink=WATER))

    s.append(trail("M212 246 H648"))
    s.append(feature("road", "hook", "The Mission Road — six miles, uphill the whole way",
                     "", 430, 232, size=12))

    s.append(feature("homestead", "a1-house", "The Cardoza Place",
                     hut(96, 214, 54, 36) + hut(160, 228, 40, 26) + pin(84, 210, "1"),
                     140, 288, size=12.5))
    s.append(feature("cardoza", "a1-well", "The Cardoza Well",
                     wellsym(140, 158, r=15) + fightmark(180, 150, "3") + pin(102, 148, "2"),
                     140, 122, size=12.5))

    # the mission compound
    s.append(f'<rect x="654" y="96" width="300" height="288" rx="6" fill="#e7dcc0" '
             f'stroke="{GOLD}" stroke-width="2" stroke-dasharray="7 5"/>')
    s.append(feature("nave", "a2-nave", "The Nave",
                     building(674, 126, 178, 116) + cross(763, 102)
                     + fightmark(763, 184, "6") + pin(662, 122, "5"), 763, 262, size=12.5))
    s.append(feature("sacristy", "a2-ledger", "The Sacristy — the padres' ledger",
                     building(862, 126, 74, 74, fill="#d7c9a8") + pin(944, 122, "7"),
                     880, 220, size=11.5, anchor="middle"))
    s.append(feature("court", "a2-court", "The Courtyard",
                     f'<rect x="674" y="270" width="178" height="92" fill="none" stroke="{INK}" '
                     f'stroke-width="2" stroke-dasharray="4 6"/>' + pin(664, 356, "4"),
                     763, 322, size=12))
    s.append(feature("wellhead", "a3-shaft", "The First Well — the shaft head",
                     wellsym(898, 300, r=17) + pin(940, 288, "8"), 898, 350, size=11.5))

    s.append(compass(60, 130, r=21))
    s.append(scalebar(300, 386, 150, "one mile"))

    # ---------- lower panel: the section
    s.append(f'<rect x="24" y="436" width="952" height="300" rx="6" fill="none" '
             f'stroke="{INK_SOFT}" stroke-width="1.4"/>')
    s.append(_lab(60, 462, "Below — a section through the first well, drawn to its own scale",
                  size=13, anchor="start", ink=BLOOD))

    s.append(f'<rect x="60" y="486" width="880" height="228" fill="#e2d7ba"/>')
    s.append(rough("M60 486 H940", ink=INK, w=2.6))
    s.append(_lab(112, 506, "grade", size=11, weight=500, ink=INK_SOFT, ))

    # the shaft
    s.append(feature("shaft", "a3-descent", "The Shaft — a hundred and forty feet, wet the whole way",
                     f'<rect x="452" y="486" width="76" height="150" fill="{PAPER}" '
                     f'stroke="{INK}" stroke-width="2.2"/>'
                     + rough("M452 526 H528 M452 566 H528 M452 606 H528", w=1.2)
                     + pin(560, 508, "9"), 640, 546, size=11.5, anchor="start"))

    s.append(feature("nail", "a3-nail", "The Silver Nail, and the sixth binding",
                     f'<path d="M490 594 V636" stroke="{GOLD}" stroke-width="6" '
                     f'stroke-linecap="round"/>'
                     f'<circle cx="490" cy="590" r="7" fill="{GOLD}" stroke="{INK}" stroke-width="1.6"/>'
                     + pin(414, 606, "10"), 440, 628, size=11.5, anchor="end"))

    s.append(feature("water", "a3-bottom", "Standing Water",
                     f'<rect x="452" y="636" width="76" height="26" fill="{WATER}" opacity="0.62"/>'
                     + f'<path d="M456 646 q9 -6 19 0 q9 6 19 0 q9 -6 19 0" stroke="{WATER}" '
                       f'stroke-width="2" fill="none"/>', 640, 652, size=11.5, anchor="start"))

    s.append(feature("bottom", "a3-bottom", "The Bottom of the Basin",
                     f'<path d="M300 662 q90 42 190 42 q100 0 190 -42 L680 714 H300 Z" '
                     f'fill="#241a15" stroke="{INK}" stroke-width="2"/>'
                     + fightmark(490, 692, "11") + pin(286, 682, "11"), 490, 730, size=12.5))

    s.append(scalebar(724, 700, 120, "forty feet"))
    s.append(legend(60, 528, [
        (_m_square(STONE), "standing wall"),
        (_m_water, "water, or where it was"),
        (_m_fight, "a keyed fight"),
        (lambda x, y: f'<circle cx="{x}" cy="{y}" r="6" fill="{GOLD}" stroke="{INK}" stroke-width="1.5"/>',
         "a padres' silver nail"),
    ], w=196))

    return W, H, "".join(s), "Mission San Clavo, Above and Below"


MAPS = {
    "salt-at-coffin-wells": _map_salt,
    "a-face-not-his-own": _map_face,
    "what-the-water-answers": _map_water,
}


# ---------------------------------------------------------------- serialization

_STYLE = (f'<style>.lab{{font-family:Georgia,"EB Garamond",serif;letter-spacing:.01em;}}'
          f'.feat text{{paint-order:stroke;stroke:{PAPER};stroke-width:3.2px;stroke-linejoin:round;}}'
          f'</style>')


def svg(slug, standalone=False):
    W, H, body, title = MAPS[slug]()
    ns = ' xmlns="http://www.w3.org/2000/svg"' if standalone else ""
    return (f'<svg{ns} viewBox="0 0 {W} {H}" role="img" data-map="{slug}" '
            f'aria-label="{esc(title)}" preserveAspectRatio="xMidYMid meet">'
            f'<title>{esc(title)}</title>{_STYLE}{body}</svg>')


def map_title(slug):
    return MAPS[slug]()[3]


def filename(slug):
    return f"map-{slug}.svg"


MAP_CSS = """
  /* ---- Module maps ---- */
  .mapwrap{ margin:1.1em 0 1.3em; }
  .mapwrap svg{ display:block; width:100%; height:auto; max-height:660px;
                border:1px solid var(--gold-d); background:#f2ead6; }
  .mapwrap .map-cap{ font-size:12.5px; font-style:italic; color:var(--ink-soft);
                     margin:.45em 0 0; text-align:center; }
  .mapwrap .map-dl{ display:inline-block; margin:.5em auto 0; font-family:inherit; font-size:12.5px;
                    font-variant:small-caps; letter-spacing:.05em; cursor:pointer;
                    background:#efe6cf; color:var(--blood-d); font-weight:700;
                    border:1px solid var(--gold-d); border-left:3px solid var(--blood);
                    padding:4px 12px; }
  .mapwrap .map-dl:hover{ background:#e6d9ba; }
  .mapwrap .dl-row{ text-align:center; }
  @media print{ .mapwrap .dl-row{ display:none; } }
"""

# The download control. It serializes the map that is already on the page rather than fetching a
# file, so it works from a book opened off a thumb drive with no network and no sibling files —
# which is the state most of these books will actually be read in.
_DL = (
    "var w=b.closest('.mapwrap'),s=w.querySelector('svg').cloneNode(true);"
    "s.setAttribute('xmlns','http://www.w3.org/2000/svg');"
    "var t='<?xml version=\\'1.0\\' encoding=\\'UTF-8\\'?>\\n'+new XMLSerializer().serializeToString(s);"
    "var u=URL.createObjectURL(new Blob([t],{type:'image/svg+xml;charset=utf-8'}));"
    "var a=document.createElement('a');a.href=u;a.download=b.getAttribute('data-file');"
    "document.body.appendChild(a);a.click();a.remove();"
    "setTimeout(function(){URL.revokeObjectURL(u);},2000);"
)


def map_html(slug, caption):
    f = filename(slug)
    return (f'<div class="mapwrap">{svg(slug)}'
            f'<p class="map-cap">{esc(map_title(slug))} &mdash; {caption}</p>'
            f'<p class="dl-row"><button type="button" class="map-dl" data-file="{f}" '
            f'onclick="(function(b){{{_DL}}})(this)">&#10515; Download this map (SVG)</button></p>'
            f'</div>')


if __name__ == "__main__":
    for slug in MAPS:
        out = filename(slug)
        open(out, "w", encoding="utf-8").write(
            '<?xml version="1.0" encoding="UTF-8"?>\n' + svg(slug, standalone=True) + "\n")
        W, H, _, title = MAPS[slug]()
        print(f"{out}: {title} — {W}x{H}")
