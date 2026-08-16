#!/usr/bin/env python3
"""The book↔data drift guard — the last seam in the single-source discipline.

The rest of the chain is already self-checking: the GritKeeper app reads every number from
`GK/rules/Data/chargen.json`, and `CharGen.Validate` re-derives each one from the formula, so
the data and the app can never quietly disagree (the smoke suite fails first). The one seam left
to a human hand is the *printed book* — the Player's Book prints seventeen Calling tables that I
transcribe into chargen.json. This checks that transcription automatically: it parses the built
`blood-and-grit.html`, reads each Calling's statline rank and its ten rows of attack and saves,
and asserts the book agrees with the data AND both agree with the one spine formula (Ch. XIV):

    attack:  Practiced = level · Steady = level − 1 · Slight = max(0, level − 2)
    saves:   strong = 2 + level//2 · weak = level//3

Run it in the verify step (it needs a current blood-and-grit.html). Exit code 0 = the book, the
data, and the formula are one; non-zero = a drift the eye would have missed.
"""
import json
import re
import sys
from pathlib import Path

# This file lives in audits/, so the repo root is one level up. Every path
# below hangs off it -- including the cwd handed to git -- so this one line is
# what makes the move to audits/ a move and not a rewrite.
ROOT = Path(__file__).resolve().parent.parent


def attack_for(rank, level):
    return {"Practiced": level, "Steady": level - 1, "Slight": max(0, level - 2)}[rank]


def strong(level):  return 2 + level // 2
def weak(level):    return level // 3


def load_data():
    d = json.loads((ROOT / "GK/rules/Data/chargen.json").read_text(encoding="utf-8"))
    out = {}
    for c in d["callings"]:
        out[c["name"]] = {
            "rank": c.get("attackRank"),
            "rows": {r["level"]: (r["atk"], r["fort"], r["ref"], r["will"]) for r in c["rows"]},
        }
    return out


ROW_RE = re.compile(
    r'<tr><td>(\d+)</td><td class="c">\+?(-?\d+)</td><td class="c">\+?(-?\d+)</td>'
    r'<td class="c">\+?(-?\d+)</td><td class="c">\+?(-?\d+)</td>')
STAT_RE = re.compile(r'<p class="statline">[^<]*Attack (\w+)</p>')
H2_RE = re.compile(r'<h2 id="ix-c-[^"]*">([^<]+)</h2>')
TBL_RE = re.compile(r'<table class="lvl">.*?</table>', re.S)


def load_book():
    html = (ROOT / "blood-and-grit.html").read_text(encoding="utf-8")
    callings = {}
    for m in TBL_RE.finditer(html):
        head = html[:m.start()]
        name = H2_RE.findall(head)[-1].strip()
        rank_matches = STAT_RE.findall(head)
        rank = rank_matches[-1] if rank_matches else None
        rows = {int(l): (int(a), int(f), int(r), int(w))
                for l, a, f, r, w in ROW_RE.findall(m.group(0))}
        callings[name] = {"rank": rank, "rows": rows}
    return callings


# ---------------------------------------------------------------- the arms table
#
# Added 2026-08-16, and the reason is worth keeping. Nothing here read the arms table, so when the
# weapons were transcribed the book's Range, Cap. and Reload columns were simply left behind -- and
# every test in the repo stayed green while the Iron Code's range increments and reload actions sat
# unimplementable for want of the numbers. Fists / Boots had gone missing outright, and the
# cap-and-ball's "slow" reload had been folded into its TRAITS string, where it read as a trait only
# one gun has. The Calling tables were guarded and the arms table was not; that asymmetry is the
# whole bug.

FIREARM_RE = re.compile(
    r'<tr><td>([^<]+)</td><td class="c">([^<]+)</td><td class="c">(\d+)</td>'
    r'<td class="c">(\d+)</td><td class="c">([^<]+)</td><td>([^<]*)</td>'
    r'<td class="c">\$?([\d.]+)</td></tr>')

# The same seven columns, but with a Cap. or Reload the book prints as an em dash. These are the
# thrown things -- dynamite, a coal-oil bomb, a throwing knife -- which have no cylinder to fill and
# whose damage is not always one dice expression ("1d6 fire", "1d4 / 1d6"). They are deliberately
# out of scope here, and they are COUNTED AND NAMED rather than quietly skipped: a row this file
# does not read is a row nothing checks, and the whole reason this section exists is that a table
# nothing checked lost three columns without a single test going red.
THROWN_RE = re.compile(
    r'<tr><td>([^<]+)</td><td class="c">([^<]+)</td><td class="c">([^<]+)</td>'
    r'<td class="c">—</td><td class="c">—</td><td>([^<]*)</td>'
    r'<td class="c">([^<]+)</td></tr>')

BLADE_RE = re.compile(
    r'<tr><td>([^<]+)</td><td class="c">(\d+d\d+)</td><td>([^<]*)</td></tr>')


def _unescape(s):
    return (s.replace("&amp;", "&").replace("&rsquo;", "’")
             .replace("&ndash;", "–").replace("&mdash;", "—").strip())


def load_arms():
    """The two Ch. X tables, as the printed book has them."""
    html = (ROOT / "blood-and-grit.html").read_text(encoding="utf-8")
    guns = {}
    for name, dmg, rng, cap, reload_, traits, cost in FIREARM_RE.findall(html):
        guns[_unescape(name)] = {
            "dmg": _unescape(dmg), "range": int(rng), "cap": int(cap),
            "reload": _unescape(reload_), "traits": _unescape(traits), "cost": float(cost),
        }
    blades = {}
    for name, dmg, notes in BLADE_RE.findall(html):
        blades[_unescape(name)] = {"dmg": _unescape(dmg), "notes": _unescape(notes)}
    thrown = [_unescape(m[0]) for m in THROWN_RE.findall(html)]
    return guns, blades, thrown


def _matches(data_name, book_name):
    """The data abbreviates some of the book's paired names -- "Club" for "Club / Rifle-Butt",
    "Saber" for "Saber / Cavalry Sword" -- while carrying others whole ("Knife / Bowie"). Either
    the full name or its first alternative counts as the same weapon; nothing else does."""
    return data_name == book_name or data_name == book_name.split(" / ")[0].strip()


def check_arms(problems):
    guns, blades, thrown = load_arms()
    if not guns or not blades:
        problems.append(f"parsed {len(guns)} firearms and {len(blades)} blades from the book; "
                        "expected both tables to be found")
        return 0
    if thrown:
        print(f"  ({len(thrown)} thrown item(s) read past, having no Cap. or Reload to check: "
              f"{', '.join(thrown)})")

    d = json.loads((ROOT / "GK/rules/Data/chargen.json").read_text(encoding="utf-8"))
    weapons = d["weapons"]
    checks = 0

    def find(book_name):
        return next((w for w in weapons if _matches(w["name"], book_name)), None)

    for name, b in guns.items():
        w = find(name)
        if w is None:
            problems.append(f"{name}: printed in the book's firearms table and absent from the data")
            continue
        for col, want, got in (("damage", b["dmg"], w.get("dmg")),
                               ("range",  b["range"], w.get("range")),
                               ("cap",    b["cap"], w.get("cap")),
                               ("reload", b["reload"], w.get("reload")),
                               ("traits", b["traits"], w.get("traits")),
                               ("cost",   b["cost"], float(w.get("cost", 0)))):
            checks += 1
            if want != got:
                problems.append(f"{name}: book {col} {want!r} != data {got!r}")

    for name, b in blades.items():
        w = find(name)
        if w is None:
            problems.append(f"{name}: printed in the book's blades table and absent from the data")
            continue
        checks += 1
        if b["dmg"] != w.get("dmg"):
            problems.append(f"{name}: book damage {b['dmg']!r} != data {w.get('dmg')!r}")

    # A blade has no Range, Cap. or Reload column, so carrying one would be an invention.
    for w in weapons:
        if w.get("kind") == "melee":
            checks += 1
            if w.get("range") or w.get("cap") or w.get("reload"):
                problems.append(f"{w['name']}: a blade carrying gun columns "
                                f"(range={w.get('range')}, cap={w.get('cap')}, reload={w.get('reload')!r})")
    return checks


def main():
    data, book = load_data(), load_book()
    problems = []

    if len(book) != 17:
        problems.append(f"parsed {len(book)} attack tables from the book, expected 17")

    for name, d in data.items():
        b = book.get(name)
        if b is None:
            problems.append(f"{name}: no attack table found in the book")
            continue
        if b["rank"] != d["rank"]:
            problems.append(f"{name}: book statline rank {b['rank']!r} != data attackRank {d['rank']!r}")
        for level in range(1, 11):
            ba = b["rows"].get(level)
            da = d["rows"].get(level)
            if ba is None or da is None:
                problems.append(f"{name} L{level}: missing row (book={ba}, data={da})")
                continue
            if ba != da:
                problems.append(f"{name} L{level}: book row {ba} != data row {da}")
            # both must equal the one formula
            want_atk = attack_for(d["rank"], level)
            if ba[0] != want_atk:
                problems.append(f"{name} L{level}: attack {ba[0]} != {d['rank']} formula {want_atk}")
            for label, val in zip(("Fort", "Ref", "Will"), ba[1:]):
                if val not in (strong(level), weak(level)):
                    problems.append(f"{name} L{level}: {label} {val} is neither strong "
                                    f"({strong(level)}) nor weak ({weak(level)})")

    checks = sum(1 + 10 * 4 for _ in data)   # rank + 10 levels × (atk + 3 saves), per Calling
    checks += check_arms(problems)
    if problems:
        print(f"DRIFT - {len(problems)} disagreement(s) between the book, the data, and the formula:")
        for p in problems[:40]:
            print("  " + p)
        return 1
    print(f"book <-> data <-> formula: in step across {len(data)} Callings and the arms table "
          f"({checks} cross-checks, 0 drift).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
