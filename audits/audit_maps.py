#!/usr/bin/env python3
"""Cross-check each module map against the module it belongs to.

Two auditors in one file, because a map can fail two entirely different ways.

**The software engineer** asks whether the two artifacts agree. Every feature on a map carries the
anchor of the scene it belongs to; every numbered pin carries a scene number. So: does each anchor
resolve to a real id in the built book, and does each pin number match a real numbered scene
heading, and does the map's own inline copy match the standalone `.svg` byte for byte? A map that
names a room the adventure does not key will send a table looking for a scene the Keeper does not
have, and nothing else in this repo would ever catch it.

**The cartographer** asks whether the drawing is a map at all. Is there a scale and a north arrow?
Does the legend name marks the map actually uses? Is everything inside the frame? Do any two labels
sit on top of each other? None of those are caught by the first auditor, and a map that fails them
is unusable at a table even when every anchor resolves.

Run: `python audit_maps.py`
"""
import re
import sys
from pathlib import Path

# module_maps lives at the repo ROOT, and running `python audits/audit_maps.py`
# puts audits/ at sys.path[0] -- so without this the import fails for a reason
# that has nothing to do with maps.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import module_maps  # noqa: E402  -- must follow the sys.path line above

# This file lives in audits/, so the repo root is one level up. Every path
# below hangs off it -- including the cwd handed to git -- so this one line is
# what makes the move to audits/ a move and not a rewrite.
ROOT = Path(__file__).resolve().parent.parent

# Which built book each map belongs to.
PAIRS = [
    ("salt-at-coffin-wells", "module-salt-at-coffin-wells.html"),
    ("a-face-not-his-own", "module-a-face-not-his-own.html"),
    ("what-the-water-answers", "module-what-the-water-answers.html"),
]

# Features are found by splitting rather than by a balanced match: a feature contains nested <g>
# elements (every pin is one), so a non-greedy `(.*?)</g>` stops at the first inner close and a
# lookahead for the next sibling silently swallows whole neighbours. It did exactly that on the
# first run and reported three features as carrying pins belonging to the feature after them.
FEAT_HEAD = re.compile(r'<g class="feat" data-key="([^"]+)" data-scene="([^"]+)">')
TEXT = re.compile(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*text-anchor="(\w+)"[^>]*'
                  r'font-size="([\d.]+)"[^>]*>(.*?)</text>', re.S)


def features(svg):
    """(key, scene, body) per feature, each body running to the start of the next one."""
    heads = list(FEAT_HEAD.finditer(svg))
    out = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(svg)
        out.append((m.group(1), m.group(2), svg[m.end():end]))
    return out
ID = re.compile(r'\bid="([^"]+)"')
# A keyed scene heading: "<h2 id="a2-tack">8. The Tack Room</h2>"
SCENE_H2 = re.compile(r'<h2[^>]*\bid="([^"]+)"[^>]*>\s*(\d+)\.\s', re.S)
PIN_N = re.compile(r'<circle[^>]*r="10\.5"[^>]*/>\s*<text[^>]*>(\d+)</text>')
FIGHT_N = re.compile(r'<circle[^>]*r="9"[^>]*/>\s*<text[^>]*>(\d+)</text>')

fails = []


def bad(slug, msg):
    fails.append(f"{slug}: {msg}")
    print(f"  FAIL  {msg}")


def audit(slug, book):
    print(f"\n{module_maps.filename(slug)}  vs  {book}")
    svg = module_maps.svg(slug)
    W, H = module_maps.MAPS[slug]()[0], module_maps.MAPS[slug]()[1]
    html = (ROOT / book).read_text(encoding="utf-8")
    ids = set(ID.findall(html))
    scenes = {int(n): a for a, n in SCENE_H2.findall(html)}

    # ---------------------------------------------------------- engineer
    feats = features(svg)
    if not feats:
        bad(slug, "no keyed features on the map at all")
        return
    print(f"  {len(feats)} keyed features, {len(scenes)} numbered scenes in the book")

    for key, scene, body in feats:
        if scene not in ids:
            bad(slug, f"feature '{key}' points at #{scene}, which is not an id in {book}")

    # Every numbered pin and fight mark must name a scene the book actually keys, at that number.
    for n in sorted({int(x) for x in PIN_N.findall(svg)} | {int(x) for x in FIGHT_N.findall(svg)}):
        if n not in scenes:
            bad(slug, f"pin {n} is on the map, but the book has no scene numbered {n}")

    # A feature may legitimately carry more than one number — the Pell place is scene 5 and the
    # fight in its yard is scene 6, drawn on the same building. What it may NOT do is carry a set
    # of numbers none of which is its own scene: that is a pin renumbered on one side only.
    for key, scene, body in feats:
        nums = {int(x) for x in PIN_N.findall(body)} | {int(x) for x in FIGHT_N.findall(body)}
        if nums and not any(scenes.get(n) == scene for n in nums):
            named = ", ".join(f"{n}=#{scenes.get(n, '?')}" for n in sorted(nums))
            bad(slug, f"feature '{key}' points at #{scene} but its pins are {named}")

    # The inline copy and the downloadable file must be the same drawing.
    f = ROOT / module_maps.filename(slug)
    if not f.is_file():
        bad(slug, f"{f.name} has not been generated — run `python module_maps.py`")
    else:
        standalone = f.read_text(encoding="utf-8")
        if module_maps.svg(slug, standalone=True) not in standalone:
            bad(slug, f"{f.name} on disk differs from what module_maps.py draws now")
        if module_maps.filename(slug) not in html:
            bad(slug, f"the book does not offer {f.name} for download")
    if f'data-map="{slug}"' not in html:
        bad(slug, "the book does not carry this map inline")

    # ---------------------------------------------------------- cartographer
    if 'class="scalebar"' not in svg:
        bad(slug, "no scale bar: this is a picture, not a map")
    if 'class="compass"' not in svg:
        bad(slug, "no north arrow")
    if 'class="legend"' not in svg:
        bad(slug, "no legend")

    texts = TEXT.findall(svg)
    # Everything drawn must be inside the frame, labels included.
    for x, y, anchor, size, t in texts:
        x, y, size = float(x), float(y), float(size)
        if not (0 <= x <= W and 0 <= y <= H):
            bad(slug, f'label "{t[:40]}" is outside the {W}x{H} frame at ({x:.0f},{y:.0f})')
    for m in re.finditer(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"', svg):
        x, y, w, h = (float(g) for g in m.groups())
        if x < 0 or y < 0 or x + w > W or y + h > H:
            bad(slug, f"a rect runs outside the {W}x{H} frame: {x:.0f},{y:.0f} {w:.0f}x{h:.0f}")

    # Label collisions. Estimated boxes, generous on height and mean glyph width, so this reports
    # real overlaps rather than near misses — a map whose labels touch is a map somebody misreads.
    boxes = []
    for x, y, anchor, size, t in texts:
        x, y, size = float(x), float(y), float(size)
        txt = re.sub(r"&[a-z]+;", "x", t).strip()
        w = len(txt) * size * 0.46
        # Respect the anchor. Treating every label as centred put phantom overlaps on the two
        # end-anchored labels and would have had a person moving labels that were already clear.
        left = {"middle": x - w / 2, "start": x, "end": x - w}[anchor]
        boxes.append((left, y - size, left + w, y + size * 0.34, txt))
    hits = 0
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 6 and oy > 4:
                hits += 1
                if hits <= 6:
                    bad(slug, f'labels overlap: "{a[4][:30]}" / "{b[4][:30]}"')
    if hits > 6:
        bad(slug, f"...and {hits - 6} further label overlaps")

    # A legend that names a mark the map never draws is worse than no legend.
    used = set(re.findall(r'fill="(#[0-9a-fA-F]{6})"', svg))
    for c in (module_maps.STONE, module_maps.WATER):
        if c not in used:
            bad(slug, f"legend colour {c} is not used anywhere on the map")

    print(f"  labels {len(texts)}, overlaps {hits}, frame {W}x{H}")


for slug, book in PAIRS:
    if not (ROOT / book).is_file():
        print(f"{book}: not built — run the module builders first")
        fails.append(book)
        continue
    audit(slug, book)

print()
if fails:
    print(f"*** {len(fails)} map finding(s) ***")
    sys.exit(1)
print("every map agrees with its module, and every map is a map.")
