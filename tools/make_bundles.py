#!/usr/bin/env python3
"""Build the two release bundles: BloodAndGrit-Books.zip and BloodAndGrit-Modules.zip.

Both were assembled by hand until 2026-08-20, which is how the books zip came to be sitting on
disk holding a Bestiary three chapters out of date. A zip is a deliverable like any other here,
so it gets built from a declared list and checked rather than remembered.

Two checks worth the trouble:

  * every listed file must exist -- a bundle quietly missing a book is worse than no bundle;
  * every built .html must show the version its own builder stamps, which is the exact failure
    that left a stale zip on disk. The file was there. It was just three chapters behind.

Modification times are deliberately NOT used for this. A `git checkout` rewrites a working
tree's mtimes wholesale, so "the builder is newer than the book" fires after any branch switch
and means nothing. The PDFs are verified where they are made -- `make_pdf.py` checks each one
page by page against the rendered sheet count -- so build the bundle in the session that printed
them, and read back the page counts this script prints.

Usage:  python tools/make_bundles.py [books|modules]      (default: both)
"""
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# file -> the script that generates it (None for hand-written files, which have no build step)
BOOKS = {
    "blood-and-grit.html":                "build_player.py",
    "keeper-handbook.html":               "build_keeper.py",
    "bestiary.html":                      "build_bestiary.py",
    "Blood-and-Grit-Players-Book.pdf":    "build_player.py",
    "Blood-and-Grit-Keepers-Book.pdf":    "build_keeper.py",
    "Blood-and-Grit-Bestiary.pdf":        "build_bestiary.py",
    "LICENSE":                            None,
    "NOTICE":                             None,
}

MODULES = {
    "module-salt-at-coffin-wells.html":                        "build_module_salt.py",
    "module-a-face-not-his-own.html":                          "build_module_face.py",
    "module-what-the-water-answers.html":                      "build_module_water.py",
    "Blood-and-Grit-Module-I-The-Salt-at-Coffin-Wells.pdf":    "build_module_salt.py",
    "Blood-and-Grit-Module-II-A-Face-Not-His-Own.pdf":         "build_module_face.py",
    "Blood-and-Grit-Module-III-What-the-Water-Answers.pdf":    "build_module_water.py",
    "map-salt-at-coffin-wells.svg":                            None,
    "map-a-face-not-his-own.svg":                              None,
    "map-what-the-water-answers.svg":                          None,
    "PLAYTEST.md":                                             None,
    "LICENSE":                                                 None,
    "NOTICE":                                                  None,
}

BUNDLES = {
    "books":   ("BloodAndGrit-Books.zip",   BOOKS),
    "modules": ("BloodAndGrit-Modules.zip", MODULES),
}

# The book builders stamp their own cover; a module builder carries a VERSION constant. Both
# shapes are tried in order, most specific first, so build_player.py -- which is the shell every
# other builder retexts -- is read off its own cover line rather than somebody else's.
STAMPS = (
    r"The Keeper's Book · Version (\d+\.\d+) -->",
    r"The Bestiary · Version (\d+\.\d+) -->",
    r"Edition of 1885 · Version (\d+\.\d+)</div>",
    r'VERSION = "([\d.]+)"',
)


def shown_version(html):
    """Every version number the built document shows a reader. One, if it was built right."""
    return set(re.findall(r"Version (\d+\.\d+)", html)) | set(re.findall(r"v(\d+\.\d+)\)", html))


def stamped_version(builder):
    src = (ROOT / builder).read_text(encoding="utf-8")
    for pat in STAMPS:
        m = re.search(pat, src)
        if m:
            return m.group(1)
    return None


def pdf_pages(path):
    import fitz
    with fitz.open(path) as d:
        return d.page_count


def build(name):
    out, files = BUNDLES[name]
    bad = []
    for f, builder in files.items():
        p = ROOT / f
        if not p.is_file():
            sys.exit(f"{name}: {f} is not there")
        if not (builder and f.endswith(".html")):
            continue
        want = stamped_version(builder)
        shown = shown_version(p.read_text(encoding="utf-8"))
        if want is None:
            bad.append(f"{builder} stamps no version this script knows how to find")
        elif shown != {want}:
            got = ", ".join("v" + v for v in sorted(shown)) or "nothing"
            bad.append(f"{f} shows {got}, {builder} stamps v{want} -- rebuild it")
    if bad:
        sys.exit(f"{name}: not bundling --\n  " + "\n  ".join(bad))

    path = ROOT / out
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(ROOT / f, f)
    print(f"{out}: {len(files)} files, {path.stat().st_size:,} bytes")
    for f in files:
        note = ""
        if f.endswith(".html"):
            note = "  v" + sorted(shown_version((ROOT / f).read_text(encoding="utf-8")))[0]
        elif f.endswith(".pdf"):
            note = f"  {pdf_pages(ROOT / f)} pages"
        print(f"    {f}{note}")


for which in (sys.argv[1:] or list(BUNDLES)):
    if which not in BUNDLES:
        sys.exit(f"unknown bundle {which!r}; expected one of {', '.join(BUNDLES)}")
    build(which)
