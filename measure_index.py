#!/usr/bin/env python3
"""Render the built Player's Book headlessly (Edge), verify layout, and patch
the static index/TOC page numbers in build_player.py's embedded SRC from the
rendered truth.

Usage: python measure_index.py            (measure + verify + patch + rebuild + recheck)
       python measure_index.py --check    (measure + report; writes nothing, exit 1 on drift)

`--check` reports whether the SOURCE placeholders match the render. It does not report whether the
book is right: the paginator resolves every `.pg` live at render time, so what this file patches is
never displayed. Added 2026-08-27 under the mistaken belief that a mismatch here was a fault in the
printed book; see the CHANGELOG entry for v2.38 for the retraction. Deliberately not in the release
gate.
"""
import hashlib, re, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PY = sys.executable
CHECK = "--check" in sys.argv          # read-only: report drift, write nothing, exit 1

JS = """() => {
  const pages=[...document.querySelectorAll('.book.pages .page')];
  const clips=pages.map(p=>Math.max(0,p.scrollHeight-p.clientHeight));
  const grab=sel=>[...document.querySelectorAll(sel)].map(li=>({
    a:(li.querySelector('a')||{}).getAttribute ? li.querySelector('a').getAttribute('href') : null,
    t:li.querySelector('a') ? li.querySelector('a').textContent.trim() : null,
    pg:li.querySelector('.pg') ? li.querySelector('.pg').textContent.trim() : null}));
  return {pages:pages.length,
    clipped:clips.filter(c=>c>1).length, maxClip:Math.max(0,...clips),
    ix:grab('.ix li:not(.ix-hd)'), toc:grab('.toc li'), toc2:grab('.toc2 li'),
    hscroll:document.documentElement.scrollWidth-document.documentElement.clientWidth};
}"""

def render(page, url):
    page.goto(url)
    page.wait_for_selector(".book.pages.ready", timeout=30000)
    page.wait_for_timeout(600)
    return page.evaluate(JS)

def build():
    subprocess.run([PY, "build_player.py"], check=True, capture_output=True)

def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()

build()
url = Path("blood-and-grit.html").resolve().as_uri()

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="msedge")
    desk = render(b.new_page(viewport={"width": 1400, "height": 1000}), url)
    mpage = b.new_page(viewport={"width": 390, "height": 844})
    mob = render(mpage, url)
    mpage.add_style_tag(content=".book.pages .page{zoom:1 !important}")
    mpage.wait_for_timeout(400)
    mobz = mpage.evaluate(JS)
    b.close()

print(f"desktop: {desk['pages']} pages, {desk['clipped']} clipped (max {desk['maxClip']}px)")
print(f"mobile:  {mob['pages']} pages, h-scroll {mob['hscroll']}px at natural zoom")
print(f"mobile true-scale: {mobz['clipped']} clipped (max {mobz['maxClip']}px)")
assert desk["pages"] == mob["pages"], "PAGE PARITY FAILED"
assert desk["clipped"] == 0, "desktop clipping"
assert mobz["clipped"] == 0, "mobile true-scale clipping"
assert mob["hscroll"] <= 0, "mobile horizontal scroll"

unresolved = [e for e in desk["ix"] if e["pg"] in ("", "0", None)]
assert not unresolved, f"unresolved index anchors: {unresolved[:8]}"

# Every detailed-TOC anchor (chapter + generated sub-headings) must resolve live.
untoc = [e for e in desk["toc2"] if e["pg"] in ("", "0", None)]
assert not untoc, f"unresolved detailed-TOC anchors: {untoc[:8]}"
print(f"detailed TOC: {len(desk['toc2'])} lines, all anchors resolved")

# ---- patch the source's simple-TOC chapter statics from the rendered detailed TOC ----
# Reported rather than patched until 2026-08-19, which let the contents page drift by as much as
# thirty-two pages: it offered Callings on 29 when they render on 38, and the Ledger on 164 when it
# is on 196. Every one of these is rewritten from the real page the moment the book opens in a
# browser, so nobody reading it on a screen ever saw the wrong number -- and the one reader who
# does see it, the one who has printed the file or turned JavaScript off, is the reader a fallback
# exists for. Scoped to the <ul class="toc"> block so the index below it keeps its own pass.
src = open("build_player.py", encoding="utf-8").read()
before = src                            # --check compares against this and never writes
toc2map = {e["a"]: e["pg"] for e in desk["toc2"]}
tu = src.index('<ul class="toc">'); te = src.index("</ul>", tu)
moved = []


def _toc(m):
    href, stat = m.group(2), m.group(3)
    want = toc2map.get(href)
    if want is None or href == "#index" or want == stat:
        return m.group(0)
    moved.append((href, stat, want))
    return m.group(1) + want + m.group(4)


src = (src[:tu]
       + re.sub(r'(<li><a href="(#[\w-]+)">[^<]*</a><span class="pg">)(\d+)(</span></li>)',
                _toc, src[tu:te])
       + src[te:])
for href, was, now in moved:
    print(f"  contents: {href} {was} -> {now}")
if not moved:
    print("  contents: every chapter line already on the right page")

# ---- patch index statics + TOC index line ----
iu = src.index('<ul class="ix">'); ie = src.index("</ul>", iu)
block = src[iu:ie]
pgmap = {e["a"]: e["pg"] for e in desk["ix"]}
def sub(m):
    return f'{m.group(1)}{pgmap[m.group(2)]}{m.group(3)}'
block2 = re.sub(r'(<a href="(#[\w-]+)">[^<]*</a><span class="pg">)\d+(</span>)',
                lambda m: m.group(1) + pgmap[m.group(2)] + m.group(3), block)
src = src[:iu] + block2 + src[ie:]
tocpg = next(e["pg"] for e in desk["toc2"] if e["a"] == "#index")
src = re.sub(r'(<a href="#index">Index</a><span class="pg">)\d+(</span>)',
             rf"\g<1>{tocpg}\g<2>", src, count=1)
if CHECK:
    if src != before:
        print("\nDRIFT: build_player.py's static page numbers disagree with the rendered book.")
        for href, was, now in moved:
            print(f"  contents {href}: printed {was}, actually {now}")
        if not moved:
            print("  the Contents is right; one or more Index entries are not.")
        print("\nFix: python measure_index.py   (then commit build_player.py and the rebuilt HTML)")
        sys.exit(1)
    print("check: every Contents and Index page number matches the rendered book.")
    sys.exit(0)

open("build_player.py", "w", encoding="utf-8", newline="").write(src)

# ---- rebuild, idempotency, recheck ----
build(); h1 = md5("blood-and-grit.html")
build(); h2 = md5("blood-and-grit.html")
assert h1 == h2, "build not idempotent"

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="msedge")
    final = render(b.new_page(viewport={"width": 1400, "height": 1000}), url)
    b.close()
assert final["pages"] == desk["pages"], "page count changed after patch"
print(f"patched {len(desk['ix'])} index entries and {len(moved)} contents line(s); "
      f"TOC Index -> p.{tocpg}; final {final['pages']} pages; build idempotent ({h1[:8]})")
