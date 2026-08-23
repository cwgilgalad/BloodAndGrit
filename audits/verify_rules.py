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
import html
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


# ------------------------------------------------- the Calling prose beside the tables

# Added 2026-08-19, and this one is worth the paragraph. The Calling *tables* were guarded from the
# beginning; the prose printed beside them was not. Every value in a Calling's featureDescs is a
# hand transcription of a heading and its paragraphs in the Player's Book, and twenty-six of them
# had been cut off at exactly 420 characters -- mid-word, mid-rule -- while every test in this repo
# stayed green. A player reading the Prospector's Powderman in GritKeeper was told his blast rose
# "to 3d6 at 4th level, 4d6 at 7th, and 5d6 at 10" and nothing after that. Seven more had gone
# quietly stale: the app still described Signs the way the book described them before the Common
# Signs and the Bargain were split into Ranks, so the app and the book gave a Hexer two different
# lists to choose from. Three had swallowed the pull-quote that follows the feature, attribution
# and all, and printed it as if it were a rule.
#
# So read the prose the way a reader reads it -- heading by heading, to the next heading -- and
# hold the transcription up against it. Pull-quotes and stat tables are cut on the way through: a
# quote is not a rule, and a table is read from the table.

HEAD_RE = re.compile(r"<h([234])\b[^>]*>(.*?)</h\1>", re.S)
QUOTE_RE = re.compile(r'<div class="quote">.*?</div>', re.S)
TABLE_RE = re.compile(r"<table\b.*?</table>", re.S)
BLOCK_END_RE = re.compile(r"</(?:p|li|h[1-6]|div|td|tr|ul|ol)>")
TAG_RE = re.compile(r"<[^>]+>")

# The book prints curly quotes; chargen.json is typed with straight ones. Compare across the
# difference rather than pretending it is drift.
CURLY = {0x2018: "'", 0x2019: "'", 0x201c: '"', 0x201d: '"'}

# A level table names a feature in as few words as fit the column; the prose heads its own section
# in full. Where the two differ on purpose, say so here rather than renaming one of them.
FEATURE_ALIAS = {("Witch Hunter", "Zeal"): "Zeal & the Consecrations"}


def _prose(chunk):
    chunk = QUOTE_RE.sub(" ", chunk)
    chunk = TABLE_RE.sub(" ", chunk)
    chunk = BLOCK_END_RE.sub(" ", chunk)
    return _tidy(TAG_RE.sub("", chunk))


def _tidy(s):
    return re.sub(r"\s+", " ", html.unescape(s).translate(CURLY)).strip()


def load_book_features():
    """{Calling: {heading: the prose under it}} -- everything from an h2 id="ix-c-..." to the next h2."""
    text = (ROOT / "blood-and-grit.html").read_text(encoding="utf-8")
    starts = [m.start() for m in re.finditer(r"<h2\b", text)]
    out = {}
    for m in re.finditer(r'<h2 id="ix-c-[^"]*">(.*?)</h2>', text, re.S):
        stop = next((p for p in starts if p > m.start()), len(text))
        section = text[m.end():stop]
        heads = list(HEAD_RE.finditer(section))
        feats = {}
        for i, h in enumerate(heads):
            nxt = heads[i + 1].start() if i + 1 < len(heads) else len(section)
            body = _prose(section[h.end():nxt])
            if body:
                feats.setdefault(_tidy(TAG_RE.sub("", h.group(2))), body)
        out[_tidy(TAG_RE.sub("", m.group(1)))] = feats
    return out


# The picker used to tell a player everything about a Calling except what it is, which is how a
# table ends up with someone who picked the Sawbones without knowing the word means a doctor. Each
# Calling now carries a blurb, and a blurb is DERIVED, not typed: the Calling's opening paragraph
# in the book, whole sentences, until there are at least ninety characters. Ninety is what it takes
# to carry the short ones -- "Where the Preacher improvises, the Padre inherits" says nothing on
# its own -- without dragging the Shaman's entire first breath into a tooltip.

BLURB_MIN = 90
SENTENCE_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z"])')


def blurb_from(opening):
    out = ""
    for part in SENTENCE_RE.split(opening):
        out = (out + " " + part).strip()
        if len(out) >= BLURB_MIN:
            break
    return out


def load_book_blurbs():
    """{Calling: the opening words the picker should be showing}."""
    text = (ROOT / "blood-and-grit.html").read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r'<h2 id="ix-c-[^"]*">(.*?)</h2>(.*?)<table class="lvl">', text, re.S):
        paras = [p for p in re.findall(r"<p>(.*?)</p>", m.group(2), re.S) if 'class="statline"' not in p]
        if paras:
            out[_tidy(TAG_RE.sub("", m.group(1)))] = blurb_from(_tidy(TAG_RE.sub("", paras[0])))
    return out


# ------------------------------------------------- the 3rd-level paths beside the features

# Found on the same day and by the same reasoning as the feature prose above, and the damage was
# worse. Every Calling offers a handful of paths at 3rd level -- Games of the Gambler, Oaths of
# Office, Witch's Crafts -- and each one is a bolded list item in the book copied by hand into
# chargen.json. Seventeen of the fifty-six had swallowed the PAGE FURNITURE on the way out: a
# player choosing The Mechanic read "...take the better result on every roll for a round. 13
# V. Worldly CallingsBlood & Grit", folio and running head and all, as though it were part of the
# rule. Three more stopped dead at exactly 400 characters. Nothing read them, so nothing said so.

BOLD_LI_RE = re.compile(r"<li\b[^>]*>\s*<strong>(.*?)</strong>(.*?)</li>", re.S)


def load_book_boons():
    """{bolded name: [the text that follows it]} -- a name can be printed more than once."""
    text = (ROOT / "blood-and-grit.html").read_text(encoding="utf-8")
    out = {}
    for m in BOLD_LI_RE.finditer(text):
        out.setdefault(_tidy(TAG_RE.sub("", m.group(1))).rstrip("."), []).append(_prose(m.group(2)))
    return out


def check_subpaths(problems):
    book = load_book_boons()
    data = json.loads((ROOT / "GK/rules/Data/chargen.json").read_text(encoding="utf-8"))
    checks = 0
    for c in data["callings"]:
        sub = c.get("subpath")
        if not sub:
            problems.append(f"{c['name']}: no 3rd-level path in the data")
            continue
        for opt in sub.get("options", []):
            checks += 1
            said = _tidy(opt.get("boon") or "")
            printed = book.get(_tidy(opt["name"]).rstrip("."))
            if not printed:
                problems.append(f"{c['name']} / {opt['name']}: the book prints no such path")
            elif said not in printed:
                best = max(printed, key=lambda p: len(set(p.split()) & set(said.split())))
                at = next((i for i in range(min(len(best), len(said))) if best[i] != said[i]),
                          min(len(best), len(said)))
                what = ("the app stops early" if best.startswith(said) else
                        "the app runs past the book" if said.startswith(best) else
                        "the wording differs")
                problems.append(f"{c['name']} / {opt['name']}: {what} at character {at} "
                                f"(book {len(best)} chars, data {len(said)}); "
                                f"book: ...{best[at:at + 70]!r}")
    return checks


def check_features(problems):
    book = load_book_features()
    blurbs = load_book_blurbs()
    data = json.loads((ROOT / "GK/rules/Data/chargen.json").read_text(encoding="utf-8"))
    checks = 0
    for c in data["callings"]:
        checks += 1
        want = blurbs.get(c["name"])
        if want is None:
            problems.append(f"{c['name']}: no opening paragraph found in the book")
        elif _tidy(c.get("blurb") or "") != want:
            problems.append(f"{c['name']}: blurb is not the book's opening words; "
                            f"book says {want!r}")
        feats = book.get(c["name"])
        if feats is None:
            problems.append(f"{c['name']}: no Calling section found in the book")
            continue
        for key, said in (c.get("featureDescs") or {}).items():
            checks += 1
            heading = FEATURE_ALIAS.get((c["name"], _tidy(key)), _tidy(key))
            prints = feats.get(heading)
            if prints is None:
                problems.append(f"{c['name']} / {key}: the book has no such heading")
            elif prints != _tidy(said):
                said = _tidy(said)
                at = next((i for i in range(min(len(prints), len(said))) if prints[i] != said[i]),
                          min(len(prints), len(said)))
                what = ("the app stops early" if prints.startswith(said) else
                        "the app runs past the book" if said.startswith(prints) else
                        "the wording differs")
                problems.append(f"{c['name']} / {key}: {what} at character {at} "
                                f"(book {len(prints)} chars, data {len(said)}); "
                                f"book: ...{prints[at:at + 70]!r}")
    return checks


# ---------------------------------------------------------------- the encounter budget
# Ch. IV's ladder is printed in TWO books and typed into the app, and until v1.44.0 nothing held
# the three together. That is not a hypothetical: the repricing to 4 · 8 · 16 was decided on
# 2026-08-16 off a measured harness sweep and was still unshipped six days later in every one of
# the five places, because no check could tell anybody they disagreed. The app end reads
# Rules.BudgetRungs by design, so the whole app is one copy; this holds that copy to both books,
# and each book to itself.
RUNG_ORDER = ("Mook", "Even foe", "Standout")

CS_PER_SOUL = re.compile(r"public const int BudgetPerSoul = (\d+);")
CS_RUNGS    = re.compile(r"BudgetRungs\s*=\s*\{(.*?)\};", re.S)
CS_RUNG     = re.compile(r'new\("([^"]+)",\s*"[^"]*",\s*(\d+)\)')


def load_app_budget(problems):
    """The app's ladder, off Rules.BudgetRungs — the one array everything in the app prices from."""
    src = (ROOT / "GK/rules/Core.cs").read_text(encoding="utf-8")
    per = CS_PER_SOUL.search(src)
    block = CS_RUNGS.search(src)
    if not per or not block:
        problems.append("Core.cs: could not find BudgetPerSoul and/or the BudgetRungs array")
        return None, None
    rungs = {name: int(cost) for name, cost in CS_RUNG.findall(block.group(1))}
    if tuple(rungs) != RUNG_ORDER:
        problems.append(f"Core.cs: BudgetRungs reads {tuple(rungs)}, expected {RUNG_ORDER} in that order")
    return int(per.group(1)), rungs


def _flat(p):
    return re.sub(r"\s+", " ", (ROOT / p).read_text(encoding="utf-8"))


def check_budget(problems):
    per_soul, app = load_app_budget(problems)
    if app is None:
        return 0
    checks = 1

    keeper, bestiary = _flat("keeper-handbook.html"), _flat("bestiary.html")

    # --- the Keeper's Book, Ch. IV: the budget line and the three rungs it is spent on
    m = re.search(r"budget of <strong>(\d+) points per character</strong>", keeper)
    if not m:
        problems.append("Keeper's Book: Ch. IV's 'N points per character' budget line not found")
    elif int(m.group(1)) != per_soul:
        problems.append(f"Keeper's Book: budget {m.group(1)} points per character, "
                        f"app has BudgetPerSoul {per_soul}")
    checks += 1

    for label, book_name in (("Mook", "A mook"), ("Even foe", "An even foe"), ("Standout", "A standout")):
        m = re.search(r"<strong>" + book_name + r"</strong>[^<]*: <strong>(\d+) points?</strong>", keeper)
        if not m:
            problems.append(f"Keeper's Book: Ch. IV rung {book_name!r} not found")
        elif int(m.group(1)) != app[label]:
            problems.append(f"Keeper's Book: {book_name} costs {m.group(1)}, app prices "
                            f"{label} at {app[label]}")
        checks += 1

    # --- and the Keeper's Book quick-reference card, which is the same rule printed twice in the
    #     same book. A book disagreeing with ITSELF is what shipped in books-v1.2.
    m = re.search(r"Budget (\d+) points/PC; even foe (\d+), mook (\d+), standout (\d+)\.", keeper)
    if not m:
        problems.append("Keeper's Book: the Threat-by-Tier quick-reference budget line not found")
    else:
        card = (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))
        want = (per_soul, app["Even foe"], app["Mook"], app["Standout"])
        if card != want:
            problems.append(f"Keeper's Book: the quick-reference card reads {card}, "
                            f"Ch. IV and the app say {want}")
    checks += 1

    # --- the Bestiary states the same rule from the creature's end
    m = re.search(r"<strong>The encounter budget:</strong> (\d+) points per player character\. "
                  r"An even-Tier foe costs (\d+); a mook [^;]*costs (\d+); "
                  r"a standout [^.]*costs (\d+)\.", bestiary)
    if not m:
        problems.append("Bestiary: the encounter-budget paragraph not found (or reworded)")
    else:
        got = (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))
        want = (per_soul, app["Even foe"], app["Mook"], app["Standout"])
        if got != want:
            problems.append(f"Bestiary: the encounter budget reads {got}, "
                            f"the Keeper's Book and the app say {want}")
    checks += 1

    # --- and this repo's own handoff doc, which states the ladder a fifth time for a reader who
    #     never opens either book. It is prose, so it is held loosely: the four numbers, in order.
    m = re.search(r"\*\*Encounter budget:\*\* (\d+) points/PC; an even foe = (\d+), "
                  r"a mook = (\d+), a standout = (\d+)\.", _flat("CLAUDE.md"))
    if not m:
        problems.append("CLAUDE.md: the encounter-budget line not found (or reworded)")
    else:
        got = tuple(int(g) for g in m.groups())
        want = (per_soul, app["Even foe"], app["Mook"], app["Standout"])
        if got != want:
            problems.append(f"CLAUDE.md: the encounter budget reads {got}, the books and the app "
                            f"say {want}")
    checks += 1

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
    checks += check_features(problems)
    checks += check_subpaths(problems)
    checks += check_budget(problems)
    if problems:
        print(f"DRIFT - {len(problems)} disagreement(s) between the book, the data, and the formula:")
        for p in problems[:40]:
            print("  " + p)
        return 1
    print(f"book <-> data <-> formula: in step across {len(data)} Callings, their feature "
          f"prose, their 3rd-level paths, the arms table, and Ch. IV's encounter budget "
          f"across both books ({checks} cross-checks, 0 drift).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
