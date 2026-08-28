#!/usr/bin/env python3
r"""Keep the placeholder Contents page numbers in the `build_*.py` sources tidy.

READ THIS BEFORE TRUSTING ITS OUTPUT. The numbers this tool compares are NOT what a reader
sees. `nav_tools.py` turns each hand-authored `<ul class="toc">` into a flat `<ul class="toc2">`
that the client-side paginator resolves live at render time, and its docstring is explicit:
*page numbers therefore never need patching and cannot go stale*. The PDFs are printed from the
rendered page, so they carry the live numbers too.

So a "drift" reported here is a disagreement between a placeholder and the truth. It is
untidiness in a source file. It is not a fault in a book, and it must not gate a release.

This file was written on 2026-08-27 believing the opposite, and the CHANGELOG entry for
v2.38/v2.20/v2.16 carries the retraction. Measured properly afterwards: 681 rendered page
numbers across the Player's Book and the Bestiary, before any of that day's changes, zero
wrong. If you want to check what a reader actually sees, compare the RENDERED `.pg` text
against the page the anchor lands on -- both come from the browser, and neither comes from
these sources.

Usage: python measure_contents.py --check     report placeholder drift, write nothing
       python measure_contents.py --fix       patch the builders, then rebuild
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
                print(f"  {builder}: placeholder for {href} reads {was}; "
                      f"the render puts it on {now}")
            if not moved:
                print(f"  {builder}: placeholders already agree with the render")
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
        print("\nPLACEHOLDERS OUT OF DATE: "
              + ", ".join(f"{b} ({n})" for b, n in drift))
        print("Cosmetic. The rendered books are unaffected, because the paginator resolves\n"
              "every page number live. Do not gate a release on this.")
        print("Tidy up with: python measure_contents.py --fix")
        sys.exit(1)
    print("\ncheck: every source placeholder agrees with the render. This says nothing about\n"
          "the books themselves, which resolve their page numbers live and were never at risk.")


if __name__ == "__main__":
    main()
