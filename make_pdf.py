#!/usr/bin/env python3
"""Print the three built books to true 8.5x11 US-Letter PDFs. ONLY on explicit request.

Per the standing spec in CLAUDE.md: headless Chromium (system Edge) print-to-PDF
with prefer_css_page_size + print_background and zero margins; the books define
@page { size: Letter; margin: 0 } and fixed 8.5x11in sheets, so one sheet = one
PDF page. Before printing: wait for .book.pages.ready and fonts, then force-decode
every <img>. Verified with PyMuPDF: page count == rendered sheet count, 612x792pt.
"""
import pathlib, sys
import fitz
from playwright.sync_api import sync_playwright

BOOKS = [
    ("blood-and-grit.html",   "Blood-and-Grit-Players-Book.pdf"),
    ("keeper-handbook.html",  "Blood-and-Grit-Keepers-Book.pdf"),
    ("bestiary.html",         "Blood-and-Grit-Bestiary.pdf"),
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
        page.pdf(path=out, prefer_css_page_size=True, print_background=True,
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        doc = fitz.open(out)
        n, r = doc.page_count, doc[0].rect
        ok = (n == sheets and abs(r.width - 612) < 1 and abs(r.height - 792) < 1)
        print(f"{out}: {n} pages (sheets {sheets}), {r.width:.0f}x{r.height:.0f}pt "
              f"{'OK' if ok else 'MISMATCH'}")
        doc.close()
        if not ok:
            sys.exit(f"verification failed for {out}")
    browser.close()
print("all PDFs verified")
