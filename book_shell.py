#!/usr/bin/env python3
"""The shell transform: the Player's Book in, any other book out.

Every book but the Player's is built by taking the Player's Book as a shell (its cover, its print
CSS, its paginator) and swapping in a cover and a body of its own. Until 2026-09-29 each builder
carried its own copy of that swap: build_keeper.py, build_bestiary.py and build_legends.py, three
copies of the same seven cover strings, the same epigraph regex and the same splice. The Book of
Legends' docstring said that a fifth book should lift the transform into one module and leave the
CSS per-book, and the Keeper's Companion to the Book of Legends is the fifth. So it lives here now,
and the CSS stays where it was.

What moved, and what did not:

  * The Player's Book version is read off the shell, as each builder already did. Bumping the
    Player's Book cascades nowhere.
  * The seven cover strings are matched and replaced in the order every builder used, and a string
    that stops matching stops the build. A silent no-op here is how three modules once shipped
    wearing the Player's Book's name.
  * The epigraph swap comes in the two forms the builders actually used: the regex on the quote's
    margin (Keeper's Book, Bestiary) and the exact-string swap (Book of Legends, Bestiary). Both are
    kept, byte for byte, because the point of the move was that no built book changes by a byte.
  * The splice cuts from the shell's Contents marker to the book's closing div and drops a body in.

The modules keep modules_common.py, which is a transform of its own for three books that share a
shape. This module is for the one-of-a-kind books.
"""
import re

SHELL = "blood-and-grit.html"

# The two epigraphs the Player's Book carries, exactly as it prints them. A book that swaps them by
# exact string matches against these.
PLAYER_EPIGRAPH_1 = ('"We came west to be made new, and found instead that the country was older\n'
                     '    than newness, older than God, and had been waiting a long while in the quiet for company."\n'
                     '    <span class="src">— from the burned journal of Eliza Hart, Surveyor</span>')
PLAYER_EPIGRAPH_2 = ('"Keep your powder dry, your salt close, and your accounts with the dark paid up.\n'
                     '    The country settles every debt in the end."\n'
                     '    <span class="src">— a saying common to the trail, author unknown</span>')

CONTENTS_MARKER = "<!-- ===================== CONTENTS ===================== -->"


def load(path=SHELL):
    """The built Player's Book, which every other book starts from."""
    return open(path, encoding="utf-8").read()


def player_version(html):
    """The Player's Book version, read off its cover line rather than typed anywhere."""
    return re.search(r"Edition of 1885 · Version (\d+\.\d+)</div>", html).group(1)


def retext_cover(html, *, comment, title, kicker, foot, tiny, tiny2, note):
    """Swap the Player's Book's seven cover and meta strings for a book's own.

    Each argument is the whole replacement string, markup included, because the books word their
    fine print differently and a template would only move the differences somewhere harder to
    read."""
    pv = player_version(html)
    pairs = [
        (f"<!-- Blood & Grit — The Player's Book · Version {pv} -->", comment),
        (f"<title>Blood &amp; Grit — The Player's Book (Revised &amp; Expanded · v{pv})</title>", title),
        ('<div class="kicker">Being a Field Manual for the Living</div>', kicker),
        ('<div class="t-foot">The Player\'s Book</div>', foot),
        (f'<div class="t-tiny">Revised &amp; Expanded · Compiled in the Territories · Edition of 1885 · '
         f'Version {pv}</div>', tiny),
        ('<div class="t-tiny">Most rules herein are adapted from Pathfinder Second Edition, with some unique '
         'rules &amp; systems of its own</div>', tiny2),
        (f'<p class="note" style="text-align:center; margin:0;">Blood &amp; Grit · The Player\'s Book · '
         f'Version {pv} · First Complete Edition</p>', note),
    ]
    for old, new in pairs:
        # A cover string that stops matching used to be a silent no-op, and on 2026-08-19 that
        # shipped three modules wearing the Player's Book title. Say so instead of guessing.
        assert old in html, "the Player's Book cover no longer carries: " + old[:70]
        html = html.replace(old, new, 1)
    return html


def swap_epigraphs(html, pairs):
    """Exact-string epigraph swaps, each made once if its old text is present."""
    for old, new in pairs:
        if old in html:
            html = html.replace(old, new, 1)
    return html


def set_epigraph(html, margin_top, text, src):
    """Replace the epigraph set at `margin_top` (the shell sets its two at 120px and 90px)."""
    pat = re.compile(r'<div class="quote" style="margin-top:' + margin_top + r';">.*?</div>', re.DOTALL)
    new = ('<div class="quote" style="margin-top:' + margin_top + ';">\n    ' + text +
           '\n    <span class="src">— ' + src + '</span>\n  </div>')
    html, n = pat.subn(new, html, count=1)
    assert n == 1, "epigraph " + margin_top + " not found"
    return html


def splice(html, body):
    """Put a book's body in place of the Player's Book's, from its Contents to its closing div."""
    si = html.find(CONTENTS_MARKER)
    assert si != -1, "contents marker not found"
    sci = html.find("<script>")
    assert sci != -1
    assert html.rfind("</div>", si, sci) != -1, "book closing div not found"
    return html[:si] + body + "\n</div>\n" + html[sci:]
