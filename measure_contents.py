#!/usr/bin/env python3
r"""Check (and optionally fix) the hand-authored Contents page numbers in any built book.

Usage: python measure_contents.py --check          every book that has statics
       python measure_contents.py --fix            patch the builders, then rebuild

WHY THIS EXISTS, 2026-08-27. Two kinds of page number live in these books and only one of them
is safe. `nav_tools.py` builds the `.toc2` detail list and the `.ix` index as FLAT lists the
client-side paginator resolves live at render time, so those "never need patching and cannot go
stale" -- its own words. The hand-authored `<ul class="toc">` at the front of a book is different:
its numbers are static text sitting in the builder, and something has to re-derive them whenever
pagination moves.

For the Player's Book that something is `measure_index.py`, and on 2026-08-27 it turned out not to
have been run after B5 added eleven pages: the Contents was five pages out at the back. The guard
added for it covers the Player's Book alone, which was the whole of the fault as understood at the
time.

It was not the whole of it. The Keeper's Book carries 15 static numbers and the Bestiary 12, both
hand-authored the same way, and neither had ever been checked by anything. `measure_book.py`
renders them and asserts that every anchor RESOLVES, which is a different question from whether the
number printed beside it is the page it resolves to.

So this reads all three from one place. `--check` writes nothing and exits 1 on drift; verify_all
runs it in the full and release tiers.
"""
import re
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent

# builder, built file, and the builder that must be re-run after a patch
BOOKS = [
    ("build_player.py",   "blood-and-grit.html"),
    ("build_keeper.py",   "keeper-handbook.html"),
    ("build_bestiary.py", "bestiary.html"),
]

# The live truth: for every anchor the book links to, which rendered page it lands on.
JS = """() => {
  const pages=[...document.querySelectorAll('.book.pages .page')];
  const pageOf=el=>{ const p=el.closest('.page'); return p? pages.indexOf(p)+1 : null; };
  const out={};
  for (const a of document.querySelectorAll('.toc2 li a, .toc li a')) {
    const href=a.getAttribute('href'); if(!href||!href.startsWith('#')) continue;
    const t=document.getElementById(href.slice(1)); if(!t) continue;
    out[href]=pageOf(t);
  }
  return {pages:pages.length, map:out};
}"""

TOC_LI = re.compile(r'(<li[^>]*><a href="(#[\w-]+)">.*?</a><span class="pg">)(\d+)(</span>)', re.S)


def render(pw, path):
    b = pw.chromium.launch(channel="msedge")
    pg = b.new_page(viewport={"width": 1400, "height": 1000})
    pg.goto((ROOT / path).as_uri())
    pg.wait_for_selector(".book.pages.ready", timeout=60000)
    pg.wait_for_timeout(600)
    got = pg.evaluate(JS)
    b.close()
    return got


def main():
    fix = "--fix" in sys.argv
    if not fix and "--check" not in sys.argv:
        sys.exit("say --check or --fix")

    drift, patched = [], []
    with sync_playwright() as pw:
        for builder, built in BOOKS:
            if not (ROOT / built).exists():
                sys.exit(f"{built} is not built")
            live = render(pw, built)["map"]
            src = (ROOT / builder).read_text(encoding="utf-8")
            tu = src.find('<ul class="toc">')
            if tu < 0:
                print(f"  {builder}: no hand-authored Contents, nothing to check")
                continue
            te = src.index("</ul>", tu)
            moved = []

            def one(m):
                href, stat = m.group(2), m.group(3)
                want = live.get(href)
                if want is None or str(want) == stat:
                    return m.group(0)
                moved.append((href, stat, want))
                return m.group(1) + str(want) + m.group(4)

            block = TOC_LI.sub(one, src[tu:te])
            for href, was, now in moved:
                print(f"  {built}: {href} printed {was}, actually {now}")
            if not moved:
                print(f"  {built}: every Contents line is on the right page")
                continue
            drift.append((built, len(moved)))
            if fix:
                (ROOT / builder).write_text(src[:tu] + block + src[te:],
                                            encoding="utf-8", newline="")
                patched.append(builder)

    if fix and patched:
        for builder in patched:
            subprocess.run([sys.executable, str(ROOT / builder)], cwd=str(ROOT), check=True)
        print(f"\npatched and rebuilt: {', '.join(patched)}")
        print("re-run --check to confirm it converged")
        return
    if drift:
        print("\nDRIFT: " + ", ".join(f"{b} ({n} line{'s' if n > 1 else ''})" for b, n in drift))
        print("Fix: python measure_contents.py --fix   (then commit the builders and the rebuilt HTML)")
        sys.exit(1)
    print("\ncheck: every hand-authored Contents number in every book is the true one.")


if __name__ == "__main__":
    main()
