#!/usr/bin/env python3
"""Shared navigation post-processors for the Blood & Grit book builds.

`add_detailed_toc(html)` upgrades a book's simple chapter-level Contents into a
two-level detailed Contents, generated from the document's own headings so it can
never drift:

  * every `<h2>` in the body is guaranteed an `id` (existing ids are kept; the
    `ix-*` anchors already placed for the indexes are reused, nothing collides);
  * the existing hand-authored `<ul class="toc">` (chapter lines, with their
    curated titles / subtitles / static page numbers) is turned into a flat,
    splittable `<ul class="toc2">` where each chapter line is followed by its
    `<h2>` sub-headings as indented sibling lines.

The list is *flat* (chapter and sub lines are siblings, not nested) and carries a
class other than `toc`, so the client-side paginator treats it exactly like the
`.ix` index list: it splits across page boundaries instead of moving whole, and
every `<span class="pg">` is resolved live at render time. Page numbers therefore
never need patching and cannot go stale.

Idempotent: the builds always read a constant lean source, so a given input maps
to one deterministic output.
"""
import html as _htmllib
import re

__all__ = ["add_detailed_toc", "build_index"]

_TAG = re.compile(r"<[^>]+>")


def _plain(inner: str) -> str:
    """Heading inner-HTML -> plain text (for slug generation only)."""
    return _htmllib.unescape(_TAG.sub("", inner)).strip()


def _slug(text: str, used: set, prefix: str = "t-") -> str:
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "sec"
    base = prefix + base[:48]
    s, i = base, 2
    while s in used:
        s = f"{base}-{i}"
        i += 1
    used.add(s)
    return s


def _sortkey(display: str) -> str:
    """Case-insensitive sort key, ignoring a leading article and any markup."""
    t = _plain(display).lower()
    t = re.sub(r"^(the|a|an)\s+", "", t)
    return re.sub(r"[^a-z0-9 ]", "", t)


def _ensure_h2_ids(html: str, used: set) -> str:
    """Give every <h2> without an id a stable, unique slug id."""
    def repl(m: "re.Match") -> str:
        attrs, inner = m.group(1), m.group(2)
        if re.search(r"\bid\s*=", attrs):
            return m.group(0)
        sid = _slug(_plain(inner), used)
        return f"<h2{attrs} id=\"{sid}\">{inner}</h2>"

    return re.sub(r"<h2\b([^>]*)>(.*?)</h2>", repl, html, flags=re.S)


_TOC_BLOCK = re.compile(r'<ul class="toc">(.*?)</ul>', re.S)
_TOC_ENTRY = re.compile(
    r'<li><a href="#([^"]+)">(.*?)</a>\s*<span class="pg">(.*?)</span></li>', re.S
)
_H2 = re.compile(r'<h2\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</h2>', re.S)
_NEXT_CHAPTER = re.compile(r'<h1 class="chapter"')
_SECTION = re.compile(r'<section\b[^>]*>')
_OPENER = re.compile(r'\s*(?:<div class="runhead">.*?</div>)?\s*<h2\b[^>]*\bid="([^"]+)"', re.S)


def _section_opener_map(html: str) -> dict:
    """Map each section-opening <h2>'s own id -> its section's id.

    The paginator stamps a section's id onto its first content block, so an <h2>
    that opens an `id`-bearing section loses its own id at render time; the TOC
    must anchor to the section id instead.
    """
    m = {}
    for sm in _SECTION.finditer(html):
        sid = re.search(r'\bid="([^"]+)"', sm.group(0))
        if not sid:
            continue
        om = _OPENER.match(html, sm.end())
        if om:
            m[om.group(1)] = sid.group(1)
    return m


def add_detailed_toc(html: str) -> str:
    """Return `html` with its `<ul class="toc">` replaced by a detailed `toc2`.

    No-op (returns input unchanged) if there is no simple Contents list to grow.
    """
    tm = _TOC_BLOCK.search(html)
    if not tm:
        return html

    used = set(re.findall(r'id="([^"]+)"', html))
    html = _ensure_h2_ids(html, used)

    # The block moved (ids inserted), so re-find it on the updated string.
    tm = _TOC_BLOCK.search(html)
    entries = _TOC_ENTRY.findall(tm.group(1))
    opener = _section_opener_map(html)

    lines = []
    for anchor, title, pg in entries:
        title = title.strip()
        lines.append(
            f'<li class="ch"><a href="#{anchor}">{title}</a>'
            f'<span class="pg">{pg.strip()}</span></li>'
        )
        # Sub-headings live between this section's own chapter <h1> and the next.
        ap = html.find(f'id="{anchor}"')
        if ap == -1:
            continue
        own = _NEXT_CHAPTER.search(html, ap)  # this section's own chapter heading
        if not own:
            continue
        nxt = _NEXT_CHAPTER.search(html, own.end())  # the following chapter
        block = html[own.end():nxt.start()] if nxt else html[own.end():]
        for sid, sinner in _H2.findall(block):
            stitle = sinner.strip()
            href = opener.get(sid, sid)  # section-opener h2s anchor to the section
            lines.append(
                f'<li class="sub"><a href="#{href}">{stitle}</a>'
                f'<span class="pg">0</span></li>'
            )

    new_toc = '<ul class="toc2">\n    ' + "\n    ".join(lines) + "\n  </ul>"
    return html[: tm.start()] + new_toc + html[tm.end():]


_CRNAME = re.compile(r'<p class="cr-name"([^>]*)>(.*?)</p>', re.S)


def _index_creatures(html: str, used: set):
    """Give every `<p class="cr-name">` an id and return index entries for them."""
    entries = []

    def repl(m):
        attrs, name = m.group(1), m.group(2)
        idm = re.search(r'\bid="([^"]+)"', attrs)
        if idm:
            cid = idm.group(1)
            new = m.group(0)
        else:
            cid = _slug(_plain(name), used, prefix="cr-")
            new = f'<p class="cr-name"{attrs} id="{cid}">{name}</p>'
        entries.append((_sortkey(name), _plain(name), cid))
        return new

    html = _CRNAME.sub(repl, html)
    return html, entries


def build_index(html: str, curated=(), creatures: bool = False,
                subtitle: str = "Every name in its place, and the page where it waits.",
                intro: str = ""):
    """Append a letter-grouped, two-column index and add its Contents line.

    `curated` is an iterable of (display_html, anchor) pairs; `creatures=True`
    also auto-lists every `<p class="cr-name">`. Page numbers resolve live via
    the paginator, exactly like the TOC and the Player's Book index.
    """
    used = set(re.findall(r'id="([^"]+)"', html))
    entries = []
    if creatures:
        html, cent = _index_creatures(html, used)
        entries += cent
    for disp, anchor in curated:
        entries.append((_sortkey(disp), disp.strip(), anchor.lstrip("#")))

    # de-duplicate identical (display, anchor) pairs; sort; group by first letter
    seen = set()
    uniq = []
    for key, disp, anchor in sorted(entries, key=lambda e: (e[0], _plain(e[1]).lower())):
        sig = (disp, anchor)
        if sig in seen:
            continue
        seen.add(sig)
        uniq.append((key, disp, anchor))

    lines, letter = [], None
    for key, disp, anchor in uniq:
        first = (key[:1] or "#").upper()
        if not first.isalpha():
            first = "#"
        if first != letter:
            letter = first
            lines.append(f'<li class="ix-hd">{letter}</li>')
        lines.append(f'<li><a href="#{anchor}">{disp}</a><span class="pg">0</span></li>')

    runhead = ('<div class="runhead"><span class="l">Blood &amp; Grit</span>'
               '<span>Index</span></div>')
    intro_html = f'<p class="note">{intro}</p>\n  ' if intro else ""
    section = (
        f'\n<!-- ===================== INDEX ===================== -->\n'
        f'<section class="page" id="bookindex">\n  {runhead}\n'
        f'  <h1 class="chapter">Index</h1>\n'
        f'  <p class="chapter-sub">{subtitle}</p>\n'
        f'  <div class="divider"></div>\n  {intro_html}'
        f'<ul class="ix">\n    ' + "\n    ".join(lines) + "\n  </ul>\n</section>\n")

    # insert the index section just before the book's closing </div> (before <script>)
    si = html.rfind("<script")
    dc = html.rfind("</div>", 0, si if si != -1 else len(html))
    html = html[:dc] + section + html[dc:]

    # add the Index line to the simple Contents list (so the detailed TOC lists it)
    tm = _TOC_BLOCK.search(html)
    if tm:
        insert_at = tm.start() + tm.group(0).rfind("</li>") + len("</li>")
        toc_line = '\n    <li><a href="#bookindex">Index</a><span class="pg">0</span></li>'
        html = html[:insert_at] + toc_line + html[insert_at:]
    return html


if __name__ == "__main__":
    import sys

    src = sys.argv[1] if len(sys.argv) > 1 else "blood-and-grit.html"
    data = open(src, encoding="utf-8").read()
    out = add_detailed_toc(data)
    subs = out.count('<li class="sub">')
    chs = out.count('<li class="ch">')
    print(f"{src}: {chs} chapter lines, {subs} sub-heading lines in detailed TOC")
