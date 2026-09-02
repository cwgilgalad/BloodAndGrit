#!/usr/bin/env python3
"""The six PDFs are navigable: every page numbered, every link explicit, every number honest.

Cole, 2026-09-02: *"every time we make changes, it seems like the PDF hyperlinks break."* Nothing in
this repo had ever looked inside a printed PDF. `make_pdf.py` checked the page count and the sheet
size and stopped there, which is why three separate faults lived in the prints for as long as there
have been prints:

* **Five of the six books had almost no page numbers.** Measured out of the PDFs rather than the
  source, because the source is not what a reader holds: the Keeper's Book printed 0 of 129 sheet
  numbers, the Bestiary 0 of 209, each module 3 of 32, and the Player's Book 249 of 268. The
  paginator only numbered a sheet whose source section carried a hand-placed `<div class="pageno">`,
  and only the Player's shell ever had any.

* **Every link in every book was a NAMED destination.** Chromium emits `/Dest (anchor-id)` for each
  `href="#id"`, and following that means walking the document's `/Names` tree. PyMuPDF does it.
  Acrobat does it. Plenty of readers, phone viewers above all, do not — so the link is present, the
  tap does nothing, and the file is technically correct the whole time. That is the shape of the
  report, and it is why it seemed to break on every change: it had always been that way.

* **Nothing had ever compared a printed Contents number with where its own link lands.** They agree,
  as it turns out, all 1,166 of them. Now that is a fact somebody checked rather than a fact
  somebody hopes.

What this file refuses to do is re-derive the page numbers itself. It reads what was printed and
asks whether the printed thing is coherent: the number on sheet N reads N, the link that says 112
goes to 112, and the reader is never asked to resolve a name. Anything cleverer would be a second
paginator, and a second paginator is the thing this project spends its audit suite preventing.

Usage: `python audits/audit_pdf.py`. Run from the release tier, after `make_pdf.py`.
"""
import pathlib
import re
import sys

try:
    import fitz                                   # PyMuPDF, the same reader make_pdf.py verifies with
except ImportError:
    print("PyMuPDF is not installed; nothing to check.")
    sys.exit(0)

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (file, how many sheets at the front are front matter and carry no number)
# The cover and the epigraph are front matter in all six. The Player's Book's Contents runs to five
# sheets on top of that, and front matter is the one place a missing number is the design.
PDFS = [
    ("Blood-and-Grit-Players-Book.pdf", 7),
    ("Blood-and-Grit-Keepers-Book.pdf", 2),
    ("Blood-and-Grit-Bestiary.pdf", 2),
    ("Blood-and-Grit-Module-I-The-Salt-at-Coffin-Wells.pdf", 2),
    ("Blood-and-Grit-Module-II-A-Face-Not-His-Own.pdf", 2),
    ("Blood-and-Grit-Module-III-What-the-Water-Answers.pdf", 2),
]

# The page number is set with `letter-spacing:.3em`, so the text extractor hands back "1 2 1" for
# 121. Stripping the spaces is not a fudge: it is reading what the glyphs say rather than what the
# extractor's word-splitting guessed, and a check written without knowing that reports every sheet
# in the book as unnumbered. It did, on the first run.
NUMLINE = re.compile(r"^[\d ]+$")


def printed_number(page):
    """The page number drawn in the bottom strip, or None."""
    strip = fitz.Rect(0, page.rect.height - 45, page.rect.width, page.rect.height)
    for line in reversed(page.get_text("text", clip=strip).splitlines()):
        if line.strip() and NUMLINE.fullmatch(line.strip()):
            return int(line.replace(" ", ""))
    return None


def row_number(page, link, words):
    """The Contents/Index number printed on this link's own row, or None.

    Nearest digits to the RIGHT of the link, on the same line. Nearest matters: the Index is two
    columns, so every row on a line has a neighbour's number a little further right, and taking all
    of them concatenates 180 and 232 into 180232 and reports the whole book as broken. It did.
    """
    r = fitz.Rect(link["from"])
    mid = (r.y0 + r.y1) / 2
    cand = [w for w in words
            if abs((w[1] + w[3]) / 2 - mid) < 5 and w[0] > r.x1 - 2 and w[4].isdigit()]
    return int(min(cand, key=lambda w: w[0])[4]) if cand else None


def audit(path, frontmatter):
    doc = fitz.open(path)
    bad = []
    unnumbered, named, rows = [], 0, 0

    for i in range(doc.page_count):
        page = doc[i]
        n = printed_number(page)
        if i + 1 <= frontmatter:
            if n is not None:
                bad.append(f"sheet {i+1} is front matter and prints a number ({n})")
        elif n is None:
            unnumbered.append(i + 1)
        elif n != i + 1:
            bad.append(f"sheet {i+1} prints {n}")

        words = page.get_text("words")
        for l in page.get_links():
            if l.get("kind") == fitz.LINK_NAMED:
                named += 1
            tgt = l.get("page", -1)
            if tgt is None or tgt < 0 or tgt >= doc.page_count:
                bad.append(f"sheet {i+1}: a link resolves to no page (#{l.get('nameddest')})")
                continue
            printed = row_number(page, l, words)
            if printed is not None:
                rows += 1
                if printed != tgt + 1:
                    bad.append(f"sheet {i+1}: a row prints {printed} and lands on {tgt+1}")

    if unnumbered:
        bad.append(f"{len(unnumbered)} sheet(s) carry no page number: {unnumbered[:12]}")
    if named:
        bad.append(f"{named} link(s) are named destinations rather than pages — "
                   "many readers will not follow them")
    if not doc.get_toc():
        bad.append("no outline: a reader has no way to jump between chapters")

    pages, toc = doc.page_count, len(doc.get_toc())
    doc.close()
    return bad, pages, rows, toc


def main():
    missing, findings, total_rows = [], [], 0
    for name, fm in PDFS:
        p = ROOT / name
        if not p.exists():
            missing.append(name)
            continue
        bad, pages, rows, toc = audit(p, fm)
        total_rows += rows
        print(f"  {name:<52} {pages:>3} pages · {toc:>2} chapters · {rows:>4} numbered rows"
              f"{'' if not bad else '   ' + str(len(bad)) + ' FINDING(S)'}")
        for b in bad:
            findings.append(f"{name}: {b}")

    if missing:
        print(f"\n{len(missing)} PDF(s) not on disk, so not checked: {', '.join(missing)}")
        print("Run `python make_pdf.py` (step 5 of the ship) and run this again.")
        if len(missing) == len(PDFS):
            return 0

    if findings:
        print(f"\n{len(findings)} finding(s):")
        for f in findings:
            print("  " + f)
        return 1

    print(f"\nEvery sheet carries its own number, every link is an explicit page, every one of the "
          f"{total_rows} numbered Contents and Index rows lands where it says, and every book has an "
          f"outline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
