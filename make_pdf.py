#!/usr/bin/env python3
"""Print the six built documents to true 8.5x11 US-Letter PDFs.

Run this at step 5 of every ship, without being asked (Cole, 2026-08-27), and leave it alone
between ships. The PDFs stopped being tracked on 2026-08-27 and are how README serves the
books, so a stale print is a stale front page rather than a stale extra.

Per the standing spec in CLAUDE.md: headless Chromium (system Edge) print-to-PDF
with prefer_css_page_size + print_background and zero margins; the books define
@page { size: Letter; margin: 0 } and fixed 8.5x11in sheets, so one sheet = one
PDF page. Before printing: wait for .book.pages.ready and fonts, then force-decode
every <img>. Verified with PyMuPDF: page count == rendered sheet count, 612x792pt.

The three modules print through the same loop and need no special case: each is built
from the Player's Book shell by `modules_common.py`, so it carries the same paginator,
the same @page rule, and the same title page -- cover emblem, big title, kicker and all
-- differing only in the three lines that name the adventure. (Added 2026-08-20; until
then the modules shipped as HTML only, and GitHub serves raw .html as plain text.)
"""
import os
import pathlib, sys
import fitz
from playwright.sync_api import sync_playwright

def link_pass(doc):
    """Rewrite every named-destination link as an explicit page destination.

    Chromium emits `/Dest (anchor-id)` for every `href="#id"`, which is legal and which many
    readers -- phone viewers above all -- decline to follow, because following it means walking the
    document's /Names tree. The link is present, the tap does nothing, and no check can see it.
    Measured on the v1.55.0 prints: 1,195 links across the six books, every one of them named, every
    one of them resolvable, and not one of them a plain page reference.

    The name tree is left alone, so whatever was already working keeps working.
    """
    names = doc.resolve_names()
    named = fixed = 0
    for pno in range(doc.page_count):
        p = doc[pno]
        for l in p.get_links():
            if l.get("kind") != fitz.LINK_NAMED:
                continue
            named += 1
            dest = l.get("nameddest")
            tgt, to = l.get("page", -1), l.get("to")
            if (tgt is None or tgt < 0) and dest in names:
                d = names[dest]
                tgt, to = d.get("page", -1), fitz.Point(*d.get("to", (0, 0)))
            if tgt is None or tgt < 0 or tgt >= doc.page_count:
                continue                       # leave it named rather than point it somewhere wrong
            p.delete_link(l)
            p.insert_link({"kind": fitz.LINK_GOTO, "from": fitz.Rect(l["from"]),
                           "page": tgt, "to": to or fitz.Point(0, 0)})
            fixed += 1
    return named, fixed


BOOKS = [
    ("blood-and-grit.html",   "Blood-and-Grit-Players-Book.pdf"),
    ("keeper-handbook.html",  "Blood-and-Grit-Keepers-Book.pdf"),
    ("bestiary.html",         "Blood-and-Grit-Bestiary.pdf"),
    # the three adventures, in module order rather than filename order
    ("module-salt-at-coffin-wells.html",  "Blood-and-Grit-Module-I-The-Salt-at-Coffin-Wells.pdf"),
    ("module-a-face-not-his-own.html",    "Blood-and-Grit-Module-II-A-Face-Not-His-Own.pdf"),
    ("module-what-the-water-answers.html","Blood-and-Grit-Module-III-What-the-Water-Answers.pdf"),
]

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1700, "height": 1100})
    for src, out in BOOKS:
        page.goto(pathlib.Path(src).resolve().as_uri())
        page.wait_for_selector(".book.pages.ready", timeout=120_000)
        page.evaluate("document.fonts.ready.then(() => {})")
        page.evaluate("Promise.all([...document.images].map(i => i.decode().catch(() => {})))")
        sheets = page.eval_on_selector_all(".book.pages > .page", "els => els.length")
        # Taken while the browser still has the paginated DOM, so the outline agrees with the
        # Contents by construction rather than by re-parsing the finished PDF.
        chapters = page.evaluate("() => {\n  const sheets = [...document.querySelectorAll('.book.pages > .page')];\n  const out = [];\n  for (const h of document.querySelectorAll('.book.pages h1.chapter')) {\n    const sheet = h.closest('.page');\n    const i = sheets.indexOf(sheet);\n    if (i < 0) continue;\n    const t = (h.textContent || '').replace(/\\s+/g, ' ').trim();\n    if (t) out.push([t, i + 1]);\n  }\n  return out;\n}")
        page.pdf(path=out, prefer_css_page_size=True, print_background=True,
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        doc = fitz.open(out)
        n, r = doc.page_count, doc[0].rect
        ok = (n == sheets and abs(r.width - 612) < 1 and abs(r.height - 792) < 1)
        print(f"{out}: {n} pages (sheets {sheets}), {r.width:.0f}x{r.height:.0f}pt "
              f"{'OK' if ok else 'MISMATCH'}")
        named, fixed = link_pass(doc)
        if chapters:
            doc.set_toc([[1, t, n] for t, n in chapters])
        tmp = out + ".tmp"
        doc.save(tmp, garbage=3, deflate=True)
        doc.close()
        os.replace(tmp, out)
        print(f"    {fixed} of {named} links made explicit; outline: {len(chapters)} chapters")
        if not ok:
            sys.exit(f"verification failed for {out}")
    browser.close()
print("all PDFs verified")
