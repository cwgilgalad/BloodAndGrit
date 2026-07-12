#!/usr/bin/env python3
"""Render the built Player's Book headlessly (Edge), verify layout, and patch
the static index/TOC page numbers in player-src.html from the rendered truth.

Usage: python measure_index.py            (measure + verify + patch + rebuild + recheck)
"""
import hashlib, re, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PY = sys.executable

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

# ---- verify the source's simple-TOC chapter statics vs rendered detailed TOC ----
src = open("player-src.html", encoding="utf-8").read()
toc2map = {e["a"]: e["pg"] for e in desk["toc2"]}
for m in re.finditer(r'<li><a href="(#[\w-]+)">[^<]*</a><span class="pg">(\d+)</span></li>', src):
    href, stat = m.group(1), m.group(2)
    if href in toc2map and href != "#index" and toc2map[href] != stat:
        print(f"  TOC drift: {href} static {stat} vs rendered {toc2map[href]}")

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
open("player-src.html", "w", encoding="utf-8", newline="").write(src)

# ---- rebuild, idempotency, recheck ----
build(); h1 = md5("blood-and-grit.html")
build(); h2 = md5("blood-and-grit.html")
assert h1 == h2, "build not idempotent"

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="msedge")
    final = render(b.new_page(viewport={"width": 1400, "height": 1000}), url)
    b.close()
assert final["pages"] == desk["pages"], "page count changed after patch"
print(f"patched {len(desk['ix'])} index entries; TOC Index -> p.{tocpg}; "
      f"final {final['pages']} pages; build idempotent ({h1[:8]})")
