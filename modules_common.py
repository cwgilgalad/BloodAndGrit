#!/usr/bin/env python3
"""The machinery three adventure modules share.

Same architecture as the other two companion books: the Player's Book is the shell, and a builder
reads `blood-and-grit.html`, retexts the cover, swaps the body for its own, and writes a sibling.
`build_keeper.py` and `build_bestiary.py` each carry their own copy of that transform because they
are one-of-a-kind books. Three modules are not one-of-a-kind — they differ in their content and in
one accent colour — so the transform lives here once, the way `nav_tools.py` and `pag_patch.py`
already do, and each builder carries only its own adventure.

The statblocks are the load-bearing part. A module that retypes a creature's Defense is a module
that will one day disagree with the Bestiary, and this project has a name for that: two authorities
for one number. `statblock(name)` reads `GK/rules/Data/creatures.json` — the same file the app
embeds — and generates the block. A name that does not resolve raises, so a module can never cite
a creature the Bestiary does not have. That has already caught three bad names once.
"""
import json
import re

BESTIARY = "GK/rules/Data/creatures.json"
_CREATURES = None


def creatures():
    global _CREATURES
    if _CREATURES is None:
        _CREATURES = {c["name"].lower(): c for c in json.load(open(BESTIARY, encoding="utf-8"))}
    return _CREATURES


def creature(name):
    """The Bestiary's own entry, or a loud failure. Never a plausible substitute."""
    c = creatures().get(name.lower())
    if c is None:
        import difflib
        near = difflib.get_close_matches(name, [x["name"] for x in creatures().values()], n=3, cutoff=0.4)
        raise SystemExit(f"module cites '{name}', which the Bestiary does not have."
                         + (f" Did you mean: {', '.join(near)}?" if near else ""))
    return c


ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}


def statblock(name, note=None):
    """One creature's block, generated from the Bestiary. The Keeper never has to leave the module
    to run the fight, and the numbers cannot drift from the book they came out of."""
    c = creature(name)
    rows = [
        ("Defense", c["defense"]), ("Blood", c["blood"]), ("Speed", c["speed"]),
        ("Saves", c["saves"]), ("Attacks", c["attacks"]),
    ]
    if c.get("special"):
        rows.append(("Special", c["special"]))
    rows += [("Dread", c["dread"]), ("Putting it down", c["puttingItDown"])]
    if c.get("mark"):
        rows.append(("Mark", c["mark"]))
    body = "".join(f'<p><span class="sb-tag">{k}</span> {v}</p>' for k, v in rows)
    if note:
        body += f'<p class="sb-cont">{note}</p>'
    return (f'<div class="statblock"><div class="sb-head">'
            f'<span class="sb-name">{c["name"]}</span>'
            f'<span class="sb-tier">Tier {ROMAN.get(c["tier"], c["tier"])} &middot; {c["tierText"]}</span>'
            f'</div>{body}</div>')


def found(name):
    """What the posse finds before they find the thing — the Bestiary's own `found` line."""
    return f'<div class="cr-found"><span class="cf-tag">Sign of it.</span> {creature(name)["found"]}</div>'


# ---------------------------------------------------------------- page furniture

def runhead(short):
    return f'<div class="runhead"><span class="l">Blood &amp; Grit</span><span>{short}</span></div>'


def quote(text, src):
    return f'<div class="quote">{text}<span class="src">— {src}</span></div>'


def readaloud(text):
    """Boxed text. Every module in the world has it; this one keeps it short, because a Keeper who
    is reading a paragraph aloud is a Keeper whose table has stopped playing."""
    return f'<div class="readaloud">{text}</div>'


def keeper(text, tag="Keeper"):
    return f'<div class="keeper-note"><span class="kn-tag">{tag}</span>{text}</div>'


def clock(name, segments, what):
    pips = "".join('<span class="pip"></span>' for _ in range(segments))
    return (f'<div class="clock"><div class="ck-head"><span class="ck-name">{name}</span>'
            f'<span class="ck-seg">{segments} segments</span></div>'
            f'<div class="ck-pips">{pips}</div><p>{what}</p></div>')


def npc(name, want, lever, line):
    """Ch. VIII's NPC in three lines — a want, a lever, and a line they say. The Keeper's Book
    builds every person this way, so a module that builds them any other way is a module the
    Keeper has to translate."""
    return (f'<div class="npc"><span class="np-name">{name}</span>'
            f'<p><span class="np-tag">Wants</span> {want}</p>'
            f'<p><span class="np-tag">Lever</span> {lever}</p>'
            f'<p class="np-line">&ldquo;{line}&rdquo;</p></div>')


def contents(entries):
    """The simple Contents list, which `nav_tools.add_detailed_toc` then grows into a detailed one
    by walking each section's h2s.

    Two things here are load-bearing and both were learned by getting them wrong. The page span is
    not decoration — `_TOC_ENTRY` keys on it, and a list written without one grows into a TOC of a
    single line. And the `<li>` must be bare: the entry pattern is `<li><a href=…`, so an `<li>`
    that helpfully carries `class="ch"` matches nothing. The classes are the grower's to add, since
    it is the one that knows which lines are chapters and which are the headings underneath them."""
    li = "\n    ".join(
        f'<li><a href="#{a}">{t}</a><span class="pg">0</span></li>' for a, t in entries)
    return '<ul class="toc">\n    ' + li + "\n  </ul>"


def scene(n, title, body):
    return f'<h3 id="sc-{n}">{n}. {title}</h3>\n{body}'


# ---------------------------------------------------------------- the shell transform

MODULE_CSS = """
  /* ---- Adventure-module additions ---- */
  .statblock{ background:#efe6cf; border:1px solid var(--gold-d); border-left:4px solid var(--blood); padding:9px 13px 11px; margin:1.0em 0; }
  .statblock .sb-head{ display:flex; justify-content:space-between; align-items:baseline; gap:10px; border-bottom:1.5px solid var(--gold-d); padding-bottom:4px; margin-bottom:6px; }
  .statblock .sb-name{ font-family:var(--display); font-weight:700; color:var(--blood-d); font-size:17px; letter-spacing:.01em; }
  .statblock .sb-tier{ font-style:italic; color:var(--ink-soft); font-size:12.5px; white-space:nowrap; }
  .statblock p{ margin:.28em 0; font-size:13.8px; line-height:1.32; }
  .statblock .sb-tag{ font-variant:small-caps; letter-spacing:.05em; color:var(--blood-d); font-weight:700; font-size:12.5px; }
  .statblock .sb-cont{ font-style:italic; font-weight:400; color:var(--ink-soft); font-size:12px; letter-spacing:0; }
  .keeper-note{ background:#ece2c8; border-left:3px solid var(--gold-d); padding:8px 12px; margin:1em 0; font-size:14.5px; }
  .keeper-note .kn-tag{ font-variant:small-caps; letter-spacing:.06em; color:var(--blood-d); font-weight:700; display:block; font-size:12.5px; margin-bottom:2px; }
  .cr-found{ font-size:13.5px; line-height:1.4; margin:.6em 0; background:#ede3ca; border-left:3px solid var(--blood); padding:6px 11px; }
  .cr-found .cf-tag{ font-variant:small-caps; letter-spacing:.05em; color:var(--blood-d); font-weight:700; }
  /* Boxed text: what the Keeper says out loud. Set apart by rule and indent rather than by a
     screen, so it stays legible printed on a home printer in black and white. */
  .readaloud{ border-top:2px solid var(--blood); border-bottom:1px solid var(--gold-d); background:#f2ead6;
              padding:9px 14px; margin:1.1em 0; font-size:14.6px; line-height:1.46; font-style:italic; }
  .clock{ background:#efe6cf; border:1px solid var(--gold-d); padding:8px 12px 10px; margin:1em 0; }
  .clock .ck-head{ display:flex; justify-content:space-between; align-items:baseline; border-bottom:1px solid var(--gold-d); padding-bottom:3px; margin-bottom:6px; }
  .clock .ck-name{ font-family:var(--display); font-weight:700; color:var(--blood-d); font-size:15px; }
  .clock .ck-seg{ font-style:italic; color:var(--ink-soft); font-size:12px; }
  .clock .ck-pips{ display:flex; gap:5px; margin-bottom:5px; }
  .clock .pip{ width:13px; height:13px; border:1.5px solid var(--blood-d); border-radius:50%; display:inline-block; }
  .clock p{ margin:0; font-size:13.5px; line-height:1.36; }
  .npc{ margin:.9em 0; padding-left:11px; border-left:3px solid var(--gold-d); }
  .npc .np-name{ font-family:var(--display); font-weight:700; color:var(--blood-d); font-size:15.5px; }
  .npc p{ margin:.2em 0; font-size:13.8px; line-height:1.34; }
  .npc .np-tag{ font-variant:small-caps; letter-spacing:.05em; color:var(--shade); font-weight:700; }
  .npc .np-line{ font-style:italic; color:var(--ink-soft); }
  /* The playtest table — numbers the engine produced, printed as numbers. */
  table.playtest{ width:100%; border-collapse:collapse; margin:1em 0; font-size:13.2px; }
  table.playtest th{ background:var(--blood-d); color:#f2ead6; font-variant:small-caps; letter-spacing:.05em; padding:4px 7px; text-align:left; }
  table.playtest td{ border-bottom:1px solid var(--gold-d); padding:4px 7px; }
</style>"""


def shell(*, foot, kicker, tiny_edition, tiny_blurb, colophon, version,
          cover_bg, cover_key, cover_foot_ink, cover_sub_ink, epigraphs):
    """The Player's Book, retexted into a module's covers. Returns the HTML to splice a body into."""
    H = open("blood-and-grit.html", encoding="utf-8").read()

    from pag_patch import patch_paginator
    H = patch_paginator(H)

    css = MODULE_CSS + f"""
  .title-page{{ background:{cover_bg}; box-shadow:0 0 0 4px {cover_bg} inset, 0 0 0 5px {cover_key} inset, 0 14px 40px rgba(0,0,0,.66); }}
  .title-page .t-foot{{ color:{cover_foot_ink}; }}
  .title-page .t-sub{{ color:{cover_sub_ink}; }}
</style>"""
    if ".statblock{" not in H:
        H = H.replace("</style>", css, 1)

    meta = [
        ("<!-- Blood & Grit — The Player's Book · Version 2.25 -->",
         f"<!-- Blood & Grit — {foot} · Version {version} -->"),
        ("<title>Blood &amp; Grit — The Player's Book (Revised &amp; Expanded · v2.25)</title>",
         f"<title>Blood &amp; Grit — {foot} (v{version})</title>"),
        ('<div class="kicker">Being a Field Manual for the Living</div>',
         f'<div class="kicker">{kicker}</div>'),
        ("<div class=\"t-foot\">The Player's Book</div>",
         f'<div class="t-foot">{foot}</div>'),
        ('<div class="t-tiny">Revised &amp; Expanded · Compiled in the Territories · Edition of 1885 · Version 2.25</div>',
         f'<div class="t-tiny">{tiny_edition} · Version {version}</div>'),
        ('<div class="t-tiny">Most rules herein are adapted from Pathfinder Second Edition, with some unique rules &amp; systems of its own</div>',
         f'<div class="t-tiny">{tiny_blurb}</div>'),
        ('<p class="note" style="text-align:center; margin:0;">Blood &amp; Grit · The Player\'s Book · Version 2.25 · First Complete Edition</p>',
         f'<p class="note" style="text-align:center; margin:0;">{colophon}</p>'),
    ]
    for a, b in meta:
        if a in H:
            H = H.replace(a, b, 1)

    old1 = ('"We came west to be made new, and found instead that the country was older\n'
            '    than newness, older than God, and had been waiting a long while in the quiet for company."\n'
            '    <span class="src">— from the burned journal of Eliza Hart, Surveyor</span>')
    old2 = ('"Keep your powder dry, your salt close, and your accounts with the dark paid up.\n'
            '    The country settles every debt in the end."\n'
            '    <span class="src">— a saying common to the trail, author unknown</span>')
    for a, b in zip((old1, old2), epigraphs):
        if a in H:
            H = H.replace(a, b, 1)
    return H


def splice(H, BODY):
    start_marker = "<!-- ===================== CONTENTS ===================== -->"
    si = H.find(start_marker)
    assert si != -1, "contents marker not found"
    sci = H.find("<script>")
    assert sci != -1
    assert H.rfind("</div>", si, sci) != -1
    return H[:si] + BODY + "\n</div>\n" + H[sci:]


def finish(html, *, curated, subtitle, intro, out):
    from nav_tools import add_detailed_toc, build_index
    html = build_index(html, curated=curated, creatures=False, subtitle=subtitle, intro=intro)
    html = add_detailed_toc(html)
    open(out, "w", encoding="utf-8").write(html)
    return html


def report(out, html):
    print(f"{out}: statblocks {html.count('class=\"statblock\"')} "
          f"| read-aloud {html.count('class=\"readaloud\"')} "
          f"| clocks {html.count('class=\"clock\"')} "
          f"| size {len(html)}")
