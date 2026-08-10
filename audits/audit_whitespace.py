#!/usr/bin/env python3
"""Whitespace audit: render a built book headlessly (Edge) and report pages
whose bottom gap exceeds a threshold, with the block that moved to the next
page (the split candidate).

Gaps are split into two piles, because the raw list is mostly noise. A page that
ends short because the NEXT page opens a chapter, an appendix, or the index is
doing exactly what the design asks — chapters start on a fresh page, and the
trailing gap is the cost of that rule, not a defect. Those are reported as
"by design" and excluded from the count that matters. What is left — a page that
ends short in the middle of running text — is the reclaimable whitespace.

Usage: python audit_whitespace.py <book.html> [gap-px-threshold, default 140]
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

JS = """(thresh) => {
  const pages=[...document.querySelectorAll('.book.pages .page')];
  const out=[];
  pages.forEach((p,idx)=>{
    const kids=[...p.children].filter(c=>!c.classList.contains('pageno')&&!c.classList.contains('runhead'));
    if(!kids.length) return;
    const pr=p.getBoundingClientRect();
    const cs=getComputedStyle(p);
    const avail=pr.bottom-parseFloat(cs.paddingBottom);
    let bottom=pr.top;
    kids.forEach(c=>{const r=c.getBoundingClientRect(); if(r.bottom>bottom) bottom=r.bottom;});
    const gap=Math.round(avail-bottom);
    if(gap>thresh){
      const last=kids[kids.length-1];
      const np=pages[idx+1];
      let nxt=null;
      if(np){
        const nk=[...np.children].filter(c=>!c.classList.contains('pageno')&&!c.classList.contains('runhead'));
        if(nk.length){const c=nk[0];
          // A fresh chapter, appendix, or index on the next page makes this gap deliberate:
          // those always begin a page, so the short page before one is the design working.
          const opensChapter = c.matches('h1.chapter') || !!c.querySelector('h1.chapter');
          nxt={tag:c.tagName,cls:c.className,txt:(c.textContent||'').trim().slice(0,70),chapter:opensChapter};}
      }
      out.push({page:idx+1,gap,
        lastTag:last.tagName,lastCls:last.className,
        lastTxt:(last.textContent||'').trim().slice(0,70),next:nxt});
    }
  });
  return {total:pages.length, gaps:out};
}"""

path = sys.argv[1]
thresh = int(sys.argv[2]) if len(sys.argv) > 2 else 140
url = Path(path).resolve().as_uri()

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="msedge")
    page = b.new_page(viewport={"width": 1400, "height": 1000})
    page.goto(url)
    page.wait_for_selector(".book.pages.ready", timeout=30000)
    page.wait_for_timeout(600)
    r = page.evaluate(JS, thresh)
    b.close()

def by_design(g):
    # last page of the book has no successor; a trailing gap there is the end of the text
    if not g["next"]:
        return True
    return bool(g["next"].get("chapter"))

gaps = sorted(r["gaps"], key=lambda x: -x["gap"])
design = [g for g in gaps if by_design(g)]
real   = [g for g in gaps if not by_design(g)]
print(f"{path}: {r['total']} pages, {len(gaps)} with bottom gap > {thresh}px "
      f"({len(design)} by design, {len(real)} reclaimable)")
if real:
    print("  -- reclaimable (page ends short inside running text) --")
    for g in real:
        print(f"  p.{g['page']:>3}  gap {g['gap']}px  last=<{g['lastTag'].lower()} {g['lastCls']}> \"{g['lastTxt']}\"")
        print(f"         next-page starts: <{g['next']['tag'].lower()} {g['next']['cls']}> \"{g['next']['txt']}\"")
else:
    print("  -- no reclaimable gaps --")
print(f"  -- by design (next page opens a chapter/appendix/index, or end of book): {len(design)} --")
for g in design:
    nxt = g["next"]["txt"] if g["next"] else "(end of book)"
    print(f"  p.{g['page']:>3}  gap {g['gap']}px  -> {nxt}")
