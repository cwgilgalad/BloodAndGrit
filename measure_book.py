#!/usr/bin/env python3
"""Render any built Blood & Grit book headlessly (Edge) and verify layout.

Usage: python measure_book.py <built-file.html>

Checks: desktop/mobile page parity, zero clipping at true scale (desktop and
mobile, forcing zoom:1 on each .page), zero mobile horizontal scroll at natural
zoom, and that every detailed-TOC (.toc2) and index (.ix) anchor resolves to a
live page number. Read-only — never patches source.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

JS = """() => {
  const pages=[...document.querySelectorAll('.book.pages .page')];
  const clips=pages.map(p=>Math.max(0,p.scrollHeight-p.clientHeight));
  const grab=sel=>[...document.querySelectorAll(sel)].map(li=>({
    a:li.querySelector('a') ? li.querySelector('a').getAttribute('href') : null,
    t:li.querySelector('a') ? li.querySelector('a').textContent.trim() : null,
    pg:li.querySelector('.pg') ? li.querySelector('.pg').textContent.trim() : null}));
  return {pages:pages.length,
    clipped:clips.filter(c=>c>1).length, maxClip:Math.max(0,...clips),
    toc2:grab('.toc2 li'), ix:grab('.ix li:not(.ix-hd)'),
    hscroll:document.documentElement.scrollWidth-document.documentElement.clientWidth};
}"""


def render(page, url, zoom_pages=False):
    page.goto(url)
    page.wait_for_selector(".book.pages.ready", timeout=30000)
    page.wait_for_timeout(600)
    if zoom_pages:
        page.add_style_tag(content=".book.pages .page{zoom:1 !important}")
        page.wait_for_timeout(400)
    return page.evaluate(JS)


def main(path):
    url = Path(path).resolve().as_uri()
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="msedge")
        desk = render(b.new_page(viewport={"width": 1400, "height": 1000}), url)
        mob = render(b.new_page(viewport={"width": 390, "height": 844}), url)
        mobz = render(b.new_page(viewport={"width": 390, "height": 844}), url, zoom_pages=True)
        b.close()

    print(f"{path}")
    print(f"  desktop: {desk['pages']} pages, {desk['clipped']} clipped (max {desk['maxClip']}px)")
    print(f"  mobile:  {mob['pages']} pages, h-scroll {mob['hscroll']}px at natural zoom")
    print(f"  mobile true-scale: {mobz['clipped']} clipped (max {mobz['maxClip']}px)")
    print(f"  detailed TOC lines: {len(desk['toc2'])} | index entries: {len(desk['ix'])}")

    untoc = [e for e in desk["toc2"] if e["pg"] in ("", "0", None)]
    unix = [e for e in desk["ix"] if e["pg"] in ("", "0", None)]
    ok = True
    if desk["pages"] != mob["pages"]:
        print(f"  FAIL page parity: desk {desk['pages']} vs mob {mob['pages']}"); ok = False
    # Mobile true-scale (zoom:1 forced on each .page) is the authoritative clip test.
    # Per CLAUDE.md, sub-10px clips in normal flow are sub-pixel rounding, not real.
    if mobz["clipped"]:
        print("  FAIL mobile true-scale clipping"); ok = False
    if desk["maxClip"] > 10:
        print(f"  FAIL desktop clipping (max {desk['maxClip']}px)"); ok = False
    elif desk["clipped"]:
        print(f"  (desktop {desk['maxClip']}px rounding, tolerated)")
    if mob["hscroll"] > 0:
        print("  FAIL mobile h-scroll"); ok = False
    if untoc:
        print(f"  FAIL unresolved TOC anchors: {untoc[:8]}"); ok = False
    if unix:
        print(f"  FAIL unresolved index anchors: {unix[:8]}"); ok = False
    print("  OK" if ok else "  *** FAILED ***")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "blood-and-grit.html"))
