#!/usr/bin/env python3
"""The book↔data drift guard — the last seam in the single-source discipline.

The rest of the chain is already self-checking: the GritKeeper app reads every number from
`GK/source/Data/chargen.json`, and `CharGen.Validate` re-derives each one from the formula, so
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

ROOT = Path(__file__).resolve().parent


def attack_for(rank, level):
    return {"Practiced": level, "Steady": level - 1, "Slight": max(0, level - 2)}[rank]


def strong(level):  return 2 + level // 2
def weak(level):    return level // 3


def load_data():
    d = json.loads((ROOT / "GK/source/Data/chargen.json").read_text(encoding="utf-8"))
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
    if problems:
        print(f"DRIFT - {len(problems)} disagreement(s) between the book, the data, and the formula:")
        for p in problems[:40]:
            print("  " + p)
        return 1
    print(f"book <-> data <-> formula: in step across {len(data)} Callings "
          f"({checks} cross-checks, 0 drift).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
