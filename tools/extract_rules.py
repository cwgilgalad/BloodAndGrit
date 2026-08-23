#!/usr/bin/env python3
"""Convert the six built books into one machine-readable digest — the materials as data.

**Why this exists.** Every check in `audits/` that reads a book re-invents the same three hundred
lines: find the chapters, find the headings under them, pull the tables into rows, strip the tags
without wrecking the offsets. `verify_rules.py` has a copy, `audit_maps.py` has a copy,
`extract_creatures.py` has a copy, and each one drifted into its own dialect of the same job. This
is that job, once. A book goes in as HTML and comes out as chapters, sections, paragraphs and
tables, and everything downstream reads the digest instead of the markup.

It is also an export. `--out` writes the whole set to JSON, which is the format a Discord bot, a
search index or a VTT importer would want — the roadmap's online-play rungs all start by needing
the books in something other than a 700 KB self-contained page. Nothing in the repo consumes that
file today; the audits import `digest()` and hold the data in memory, so there is no second copy
of the books to keep in step. The file is git-ignored for exactly that reason.

    python tools/extract_rules.py                    # summarise what it can see
    python tools/extract_rules.py --out rules-digest.json
    python tools/extract_rules.py --book bestiary.html --chapter "The Old Dark"

**What it does NOT do:** interpret. It has no opinion about whether a number is right; it puts the
number somewhere a checker can find it. `audit_consistency.py` holds the opinions.
"""
import argparse
import hashlib
import html as H
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BOOKS = [
    "blood-and-grit.html",
    "keeper-handbook.html",
    "bestiary.html",
    "module-salt-at-coffin-wells.html",
    "module-a-face-not-his-own.html",
    "module-what-the-water-answers.html",
]

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9,
         "X": 10, "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15}


def text_of(fragment):
    """Tags out, entities decoded, whitespace collapsed. Not length-preserving — this one is for
    reading, and the audits that need true offsets do their own stripping."""
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", H.unescape(s)).strip()


def parse_table(block):
    """One <table> to {caption, headers, rows}. Row cells keep their order and nothing else."""
    cap = re.search(r"<caption[^>]*>(.*?)</caption>", block, re.S)
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", block, re.S):
        cells = [text_of(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)]
        if cells:
            rows.append(cells)
    headers = []
    if rows and re.search(r"<th\b", block):
        first = re.search(r"<tr[^>]*>(.*?)</tr>", block, re.S)
        if first and re.search(r"<th\b", first.group(1)):
            headers, rows = rows[0], rows[1:]
    return {"caption": text_of(cap.group(1)) if cap else "", "headers": headers, "rows": rows}


def book_version(src):
    """A book's own version, and only its own.

    Order matters. The three books stamp `Edition of 1885 · Version X.Y` and that is checked
    first; the modules do not, and carry the Player's Book's number on their covers besides — so a
    loose search would hand back the shell's version and call it the module's, which is precisely
    the failure `modules_common.py` shipped twice in August. The module form is `· Version X.Y`
    with no edition line, and the Player's mention beside it is spelled `v2.28`, which is why the
    third pattern can be as loose as it is without picking up the wrong number.
    """
    for pat in (r"Edition of 1885 (?:·|&middot;) Version (\d+\.\d+)",
                r"(?:·|&middot;)\s*Version (\d+\.\d+)",
                r"Version (\d+\.\d+)"):
        m = re.search(pat, src)
        if m:
            return m.group(1)
    return ""


def book_title(src):
    m = re.search(r"<title[^>]*>(.*?)</title>", src, re.S | re.I)
    return text_of(m.group(1)) if m else ""


def parse_book(path):
    """One built book to chapters -> sections -> paragraphs, plus every table, in reading order.

    Chapters are `<h1 class="chapter">`; sections are the `<h2>`s under them. Both carry ids
    already, because `nav_tools.py` id-s anything that lacks one so the detailed Contents can
    anchor to it — which is the reason this parse is as short as it is. Anything ahead of the
    first chapter (the cover, the Contents) lands in a chapter named "" so nothing is silently
    dropped; a table on the cover would otherwise vanish without a word.
    """
    src = Path(path).read_text(encoding="utf-8")
    marks = [(m.start(), m.end(), "h1",
              re.search(r'id="([^"]+)"', m.group(0)).group(1) if 'id="' in m.group(0) else "",
              text_of(m.group(1)))
             for m in re.finditer(r'<h1 class="chapter"[^>]*>(.*?)</h1>', src, re.S)]
    marks += [(m.start(), m.end(), "h2",
               re.search(r'id="([^"]+)"', m.group(0)).group(1) if 'id="' in m.group(0) else "",
               text_of(m.group(1)))
              for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", src, re.S)]
    marks.sort()

    chapters, cur, sec = [], None, None

    def flush_span(a, b):
        """Everything between two headings: its prose and its tables, attributed to where it sat."""
        span = src[a:b]
        target = sec if sec is not None else (cur["intro"] if cur else None)
        if target is None:
            return
        for p in re.findall(r"<p[^>]*>(.*?)</p>", span, re.S):
            t = text_of(p)
            if t:
                target["paragraphs"].append(t)
        for tb in re.findall(r"<table[^>]*>.*?</table>", span, re.S):
            target["tables"].append(parse_table(tb))
        for li in re.findall(r"<li[^>]*>(.*?)</li>", span, re.S):
            t = text_of(li)
            if t:
                target["items"].append(t)

    def new_body(sid, title):
        return {"id": sid, "title": title, "paragraphs": [], "tables": [], "items": []}

    cur = {"n": 0, "id": "", "title": "", "roman": None,
           "intro": new_body("", ""), "sections": []}
    chapters.append(cur)
    prev_end = 0
    for start, end, kind, hid, title in marks:
        flush_span(prev_end, start)
        prev_end = end
        if kind == "h1":
            rm = re.match(r"([IVXL]+)\.\s*(.*)", title)
            cur = {"n": len(chapters), "id": hid, "title": rm.group(2) if rm else title,
                   "roman": ROMAN.get(rm.group(1)) if rm else None,
                   "intro": new_body(hid, title), "sections": []}
            chapters.append(cur)
            sec = None
        else:
            sec = new_body(hid, title)
            cur["sections"].append(sec)
    flush_span(prev_end, len(src))

    return {
        "file": Path(path).name,
        "title": book_title(src),
        "version": book_version(src),
        "sha1": hashlib.sha1(src.encode("utf-8")).hexdigest()[:12],
        "chapters": [c for c in chapters if c["title"] or c["sections"] or c["intro"]["paragraphs"]],
    }


def digest(files=None, root=None):
    """The whole set, keyed by filename. Missing books are skipped and named in `missing`, so a
    caller running against a half-built tree gets a partial answer plus a list, rather than an
    exception forty lines into somebody else's audit."""
    root = Path(root or ROOT)
    files = files or BOOKS
    out, missing = {}, []
    for f in files:
        p = root / f
        if p.is_file():
            out[f] = parse_book(p)
        else:
            missing.append(f)
    return {"books": out, "missing": missing}


def all_text(book):
    """Every paragraph and list item in one book, in order. What a probe scans."""
    for ch in book["chapters"]:
        for body in [ch["intro"]] + ch["sections"]:
            for t in body["paragraphs"] + body["items"]:
                yield ch["title"], body["title"], t


def all_tables(book):
    for ch in book["chapters"]:
        for body in [ch["intro"]] + ch["sections"]:
            for tb in body["tables"]:
                yield ch["title"], body["title"], tb


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="write the digest to this JSON file")
    ap.add_argument("--book", help="only this one book")
    ap.add_argument("--chapter", help="print one chapter's structure and stop")
    args = ap.parse_args()

    d = digest([args.book] if args.book else None)
    if d["missing"]:
        print(f"not built, skipped: {', '.join(d['missing'])}\n")

    if args.chapter:
        for name, b in d["books"].items():
            for ch in b["chapters"]:
                if args.chapter.lower() in ch["title"].lower():
                    print(f"{name} — {ch['title']}  (#{ch['id']})")
                    for s in ch["sections"]:
                        print(f"   {s['title']}  ({len(s['paragraphs'])}p, {len(s['tables'])}t)")
        return 0

    total_ch = total_sec = total_p = total_t = 0
    print(f"{'book':<38}{'ver':>6}{'chapters':>10}{'sections':>10}{'paras':>8}{'tables':>8}")
    print("-" * 80)
    for name, b in d["books"].items():
        nsec = sum(len(c["sections"]) for c in b["chapters"])
        npar = sum(len(bd["paragraphs"])
                   for c in b["chapters"] for bd in [c["intro"]] + c["sections"])
        ntab = sum(len(bd["tables"])
                   for c in b["chapters"] for bd in [c["intro"]] + c["sections"])
        nch = len([c for c in b["chapters"] if c["title"]])
        total_ch, total_sec, total_p, total_t = (total_ch + nch, total_sec + nsec,
                                                 total_p + npar, total_t + ntab)
        print(f"{name:<38}{b['version']:>6}{nch:>10}{nsec:>10}{npar:>8}{ntab:>8}")
    print("-" * 80)
    print(f"{'':<38}{'':>6}{total_ch:>10}{total_sec:>10}{total_p:>8}{total_t:>8}")

    if args.out:
        Path(args.out).write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
        kb = Path(args.out).stat().st_size / 1024
        print(f"\nwrote {args.out} ({kb:,.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
