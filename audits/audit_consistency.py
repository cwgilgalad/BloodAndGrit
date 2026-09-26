#!/usr/bin/env python3
"""audit_consistency.py: does the game play the same way in every place it is written down?

`verify_rules.py` already guards the PLAYER's side: the Calling tables, the arms table,
the feature prose, the 3rd-level paths, and Ch. IV's encounter budget. That leaves the Keeper's
side, which is where the same number appears in the most places and where nothing has ever held
them together. Two tables in particular are printed in the Bestiary, restated in `CLAUDE.md`, and
compiled into the app as arrays, and until this file existed, editing any one of the three and
not the others produced a clean build, a green audit run, and a Keeper reading one number off the
page while the app on the table showed another.

What it holds together:

  1. THREAT BY TIER: the Bestiary's benchmark table, `Rules.TierRow`, and `CLAUDE.md`'s copy.
     Defense, Attack, Blood, both saves, damage die and Dread DC, five Tiers, three sites.
  2. SIGN & SPOOR: the Bestiary's Grounds table against `Rules.SpoorRow`. This one carries the
     safe-table rule, which is the promise that a horror too big for the posse arrives as a trace
     rather than as a fight, so it is the last table in the book that should be allowed to drift.
  3. THE BESTIARY AND ITS OWN DATA: `creatures.json` re-extracted from the built book and diffed
     against the committed file. The app reads the JSON and nothing re-extracts it automatically,
     so a Bestiary edit shipped without running `extract_creatures.py` leaves the app quoting the
     previous edition's stat block. Nothing caught that before this.
  4. THE ROLL, BY TIER: the generated appendix against the creature data it is generated from.
     It cannot drift while the book is freshly built; it drifts the moment the book is not.
  5. THE GROUNDS: every creature named in the eleven terrain tables must exist, and the Tier in
     parentheses beside it must be that creature's actual Tier. 143 entries, hand-written, each
     one an invitation to mistype a name or misremember a Tier.
  6. CONDITIONS: every condition a stat block, a table or a rule anywhere in the seven books
     names must be defined in the Player's Book Appendix B. A rule that inflicts something the
     glossary never names is a rule the table cannot look up. This read only the stat blocks
     until 2026-09-25, when Cole found the Keeper's hazards table inflicting "Stupefied".
  7. THE BENCHMARKS AGAINST THE POPULATION: the printed Tier row says what a Tier III thing
     should look like; check that the Tier III things look like it. Reported as spread, and
     failed only where a creature sits outside its own Tier's band by more than the neighbouring
     Tiers' width, since the book is explicit that the benchmarks are a starting point.
  8. PERDITION BASIN: the county every book uses as its example must be one county. Retired
     facts (a silver camp, a mission "a ruin fifty years", "Padre Ildefonso") may not come back,
     and the list of what a rider knows reads the same in the Player's Book and all three modules.
  9. HOW MANY CREATURES THERE ARE: the one number that is typed into more places than any
     other. `creatures.json` is the count; seventeen copies of it sit in prose across eight
     files, including the README that ships inside the zip. Fourteen of them were two
     Bestiary expansions out of date on 2026-09-23 and every check in this repo passed.
 10. THE LEGENDS IN BOTH BOOKS: Keeper's Ch. XVI names the Book of Legends heading each of its
     legends is filed under, and counts how many are there. `build_keeper.py` derives the count
     and holds its lists to its own headings; the Book of Legends is built after it, so the
     headings on that side are held here. Ch. XVI once said two of the three were there when
     all three were.

Usage:
    python audits/audit_consistency.py            # every check
    python audits/audit_consistency.py --verbose  # and the per-creature numbers behind check 7

Reads built books, so build first. Read-only: writes nothing, ever.
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import extract_rules as X            # noqa: E402  the books as data
import extract_creatures             # noqa: E402  the Bestiary as the app reads it

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}
FAILURES = []
CHECKS = [0]


def fail(what):
    FAILURES.append(what)
    print(f"    FAIL  {what}")


def ok(line):
    print(f"    ok    {line}")


def nums(s):
    """Every integer in a cell, as a tuple. The comparison unit for anything written differently
    in different places: the Bestiary's Dread column reads "— / 10–13" where CLAUDE.md's reads
    "10–13", and those two say the same thing. Comparing the numbers rather than the string keeps
    the audit about the rules instead of about typography."""
    return tuple(int(n) for n in re.findall(r"\d+", s or ""))


# ---------------------------------------------------------------- sources


def bestiary_table(dig, where_contains, header_starts):
    """One table, found by where it sits and what its first column is called.

    Matches on chapter AND section joined, because the Bestiary's appendices put the name in
    either slot depending on the appendix: "The Roll, by Tier" is its own chapter with the table
    directly under it, while "Threat by Tier" is an h2 inside "Appendix: Building Your Own Dead".
    Searching only the section found the first and silently missed the second."""
    for ch, sec, tb in X.all_tables(dig["books"]["bestiary.html"]):
        if where_contains.lower() in f"{ch} {sec}".lower() and tb["headers"][:1] == [header_starts]:
            return tb
    return None


def cs_tuples(src, decl):
    """The rows of a C# array-of-tuples initialiser, as lists of raw fields.

    Deliberately a text parse and not a build-and-reflect. This audit has to run in a tree with no
    .NET SDK (that is the whole reason `audits/` is Python) and `Rules.TierRow` is a literal with
    no arithmetic in it, so reading it is honest. It would stop being honest the day somebody
    computes a row, which is what the assert below is for."""
    i = src.find(decl)
    if i < 0:
        return None
    body = src[src.index("{", i) + 1:src.index("};", i)]
    rows = []
    for line in body.splitlines():
        line = line.strip().rstrip(",")
        if not line.startswith("("):
            continue
        fields, depth, cur, instr = [], 0, "", False
        for ch in line[1:]:
            if ch == '"':
                instr = not instr
            if not instr and ch == "(":
                depth += 1
            if not instr and ch == ")":
                if depth == 0:
                    break
                depth -= 1
            if ch == "," and depth == 0 and not instr:
                fields.append(cur.strip())
                cur = ""
                continue
            cur += ch
        fields.append(cur.strip())
        rows.append([f.strip().strip('"') for f in fields])
    return rows


def claude_md_table(text, header_first_cell):
    for block in re.findall(r"(?:^\|.*\n)+", text, re.M):
        rows = [[c.strip() for c in ln.strip().strip("|").split("|")]
                for ln in block.strip().splitlines()]
        rows = [r for r in rows if not all(set(c) <= set("-: ") for c in r)]
        if rows and rows[0][:1] == [header_first_cell]:
            return rows[0], rows[1:]
    return None, None


# ---------------------------------------------------------------- checks


def check_threat_by_tier(dig, core, claude):
    print("\nThreat by Tier: the Bestiary, Rules.TierRow, and CLAUDE.md")
    tb = bestiary_table(dig, "Building Your Own Dead", "Tier")
    rows_cs = cs_tuples(core, "TierRow =")
    _hdr, rows_md = claude_md_table(claude, "Tier")
    if tb is None or rows_cs is None or rows_md is None:
        fail("one of the three sites could not be read "
             f"(book={tb is not None}, app={rows_cs is not None}, doc={rows_md is not None})")
        return
    # How many Tiers there are is a fact about the ladder, not about this check. It was typed as
    # 5 here, so the day all three sites agreed at 8 this failed for saying so (B6, 2026-08-30).
    tiers = len(tb["rows"])
    if not (tiers == len(rows_cs) == len(rows_md)) or tiers < 5:
        fail(f"row counts differ: book {tiers}, app {len(rows_cs)}, doc {len(rows_md)}")
        return
    # book cols:  Tier Defense Attack Blood Saves Damage Dread
    # app tuple:  def atk blood hi lo dmg dread
    n = 0
    for i, (br, ar, mr) in enumerate(zip(tb["rows"], rows_cs, rows_md), start=1):
        tier = list(ROMAN)[i - 1]
        book = {"defense": nums(br[1]), "attack": nums(br[2]), "blood": nums(br[3]),
                "saves": nums(br[4]), "damage": br[5].strip(), "dread": nums(br[6])}
        app = {"defense": nums(ar[0]), "attack": nums(ar[1]), "blood": nums(ar[2]),
               "saves": (int(ar[3]), int(ar[4])), "damage": ar[5].strip(), "dread": nums(ar[6])}
        doc = {"defense": nums(mr[1]), "attack": nums(mr[2]), "blood": nums(mr[3]),
               "saves": nums(mr[4]), "damage": mr[5].strip(), "dread": nums(mr[6])}
        # A printed em dash yields no numbers; the C# tuple has to write something and writes 0.
        # They are the same statement -- "no number belongs here" -- in the two notations available.
        for side in (book, doc):
            for field in ("defense", "blood"):
                if side[field] == () and app[field] == (0,):
                    side[field] = (0,)
        for field in ("defense", "attack", "blood", "saves", "damage", "dread"):
            CHECKS[0] += 2
            n += 2
            if book[field] != app[field]:
                fail(f"Tier {tier} {field}: book {book[field]!r} vs app {app[field]!r}")
            if book[field] != doc[field]:
                fail(f"Tier {tier} {field}: book {book[field]!r} vs CLAUDE.md {doc[field]!r}")
    ok(f"{tiers} Tiers x 6 fields agree across all three sites ({n} comparisons)")


def check_spoor(dig, core):
    print("\nSign & spoor: the Bestiary's Grounds table and Rules.SpoorRow")
    tb = bestiary_table(dig, "Sign & Spoor", "Tier of the thing")
    rows_cs = cs_tuples(core, "SpoorRow =")
    if tb is None or rows_cs is None:
        fail(f"could not read both sites (book={tb is not None}, app={rows_cs is not None})")
        return
    if len(tb["rows"]) != len(rows_cs):
        fail(f"row counts differ: book {len(tb['rows'])}, app {len(rows_cs)}")
        return
    for i, (br, ar) in enumerate(zip(tb["rows"], rows_cs), start=1):
        tier = list(ROMAN)[i - 1]
        CHECKS[0] += 3
        if nums(br[1]) != (int(ar[0]),):
            fail(f"Tier {tier} read DC: book {br[1]!r} vs app {ar[0]}")
        book_dread = nums(br[2])
        app_dread = int(ar[1])
        # A Tier I trace costs no Nerve. The book writes that as an em dash and the app as a 0,
        # which is the same statement in two notations and must not be read as disagreement.
        if (book_dread or (0,)) != (app_dread,) and not (not book_dread and app_dread == 0):
            fail(f"Tier {tier} Dread DC: book {br[2]!r} vs app {app_dread}")
        if br[3].strip() != ar[2].strip():
            fail(f"Tier {tier} what is left:\n            book: {br[3]}\n            app : {ar[2]}")
    ok(f"5 Tiers x 3 fields agree between the book and the app ({len(rows_cs) * 3} comparisons)")


def check_creatures_current(creatures):
    print("\ncreatures.json against the built Bestiary")
    fresh = extract_creatures.parse(str(ROOT / "bestiary.html"))
    CHECKS[0] += 1
    if len(fresh) != len(creatures):
        fail(f"the built book holds {len(fresh)} creatures, the JSON holds {len(creatures)}: "
             "run `python extract_creatures.py bestiary.html GK/rules/Data/creatures.json`")
        return
    drift = []
    for a, b in zip(fresh, creatures):
        for k in a:
            CHECKS[0] += 1
            if a[k] != b.get(k):
                drift.append((a["name"], k))
    if drift:
        seen = {}
        for name, k in drift:
            seen.setdefault(name, []).append(k)
        fail(f"{len(drift)} field(s) across {len(seen)} creature(s) differ from the built book: "
             "creatures.json is stale, re-extract it")
        for name, ks in list(seen.items())[:8]:
            print(f"          {name}: {', '.join(ks)}")
        return
    ok(f"{len(fresh)} creatures, every field identical to the book the app quotes")


def check_roll_by_tier(dig, creatures):
    print("\nThe Roll, by Tier: the generated appendix against the creature data")
    tb = bestiary_table(dig, "The Roll, by Tier", "Tier")
    if tb is None:
        fail("the appendix table could not be read")
        return
    listed = {}
    for row in tb["rows"]:
        t = ROMAN[re.match(r"([IVX]+)", row[0]).group(1)]
        for name in row[1].split(", "):
            listed.setdefault(name.strip(), set()).add(t)
    actual = {}
    for c in creatures:
        actual.setdefault(c["name"], set()).add(c["tier"])
    CHECKS[0] += len(listed) + len(actual)
    missing = sorted(set(actual) - set(listed))
    extra = sorted(set(listed) - set(actual))
    wrong = sorted(n for n in set(listed) & set(actual) if not (listed[n] & actual[n]))
    for n in missing[:6]:
        fail(f"{n} is in the Bestiary and not in the appendix")
    for n in extra[:6]:
        fail(f"{n} is in the appendix and not in the Bestiary")
    for n in wrong[:6]:
        fail(f"{n} is listed at Tier {sorted(listed[n])} and is Tier {sorted(actual[n])}")
    if not (missing or extra or wrong):
        ok(f"all {len(actual)} creatures indexed once, at the Tier their stat block gives")


def check_grounds(dig, creatures):
    print("\nThe Grounds: every creature named in the terrain tables")
    by_name = {c["name"]: c for c in creatures}
    unknown, mistier, total = [], [], 0
    for _ch, sec, tb in X.all_tables(dig["books"]["bestiary.html"]):
        if "Sign & Spoor" in sec:
            continue
        for row in tb["rows"]:
            for cell in row:
                if not cell or cell.isdigit():
                    continue
                m = re.match(r"(.+?)\s*\((I{1,3}|IV|V)(?:[–-](I{1,3}|IV|V))?\)", cell)
                if not m:
                    continue
                total += 1
                CHECKS[0] += 2
                name = m.group(1).strip()
                lo, hi = ROMAN[m.group(2)], ROMAN[m.group(3) or m.group(2)]
                c = by_name.get(name)
                if c is None:
                    unknown.append((sec, cell))
                elif not lo <= c["tier"] <= hi:
                    mistier.append((sec, cell, c["tier"]))
    for sec, cell in unknown[:8]:
        fail(f"{sec}: \"{cell}\" names no creature in the Bestiary")
    for sec, cell, t in mistier[:8]:
        fail(f"{sec}: \"{cell}\" is Tier {t}, not the Tier this table gives it")
    if not (unknown or mistier):
        ok(f"{total} table entries: every name real, every Tier the creature's own")


# The names a condition goes by in the d20 family, whether or not this game uses them. Most come
# from Pathfinder's list, which is the one a writer who knows the family reaches for without
# noticing. Appendix B's vocabulary is closed and small, so a rule that names one of these and
# finds it missing from the glossary has invented a condition, and that is the finding. The ones
# Appendix B defines are listed as well, so that a condition dropped from the glossary is caught
# everywhere it is still used, and the check fails if the glossary gains one this set lacks. A
# hyphenated name is one word to the scan: Off-Guard, and Flat-Footed, which is what Pathfinder
# called it first.
CONDITION_WORDS = {
    "Bleeding", "Blinded", "Clumsy", "Drained", "Dying", "Enfeebled", "Fatigued", "Frightened",
    "Grabbed", "Lost", "Marked", "Off-Guard", "Prone", "Sickened", "Slowed", "Stunned",
    "Broken", "Charmed", "Concealed", "Confused", "Controlled", "Cursed", "Dazed", "Dazzled",
    "Deafened", "Doomed", "Encumbered", "Entangled", "Exhausted", "Fascinated", "Flat-Footed",
    "Fleeing", "Hidden", "Immobilised", "Immobilized", "Invisible", "Nauseated", "Panicked",
    "Paralysed", "Paralyzed", "Persistent", "Petrified", "Poisoned", "Quickened", "Restrained",
    "Shaken", "Staggered", "Stupefied", "Unconscious", "Undetected", "Weakened", "Wounded",
}
_TITLE = r"\b([A-Z][a-z]{2,13}(?:-[A-Z][a-z]{1,13})?)\b"
_OPENS = set(".!?\u2026\"\u201c\u2018'\u201d\u2019\u2014\u2013")


def _rules_text(src):
    """A built book as lines of text, minus its script, style, Contents and Index. A table row's
    cells are split by TABs, so the scan can tell a cell (rules text from its first word) from a
    paragraph (which may open on any word it likes). The digest is not used for this because it
    keeps only paragraphs, list items and tables, and the Keeper's notes and the modules' stat
    blocks are neither."""
    src = re.sub(r"<(script|style)\b.*?</\1>", " ", src, flags=re.S | re.I)
    keep = []
    for sec in re.split(r"(?=<section\b)", src):
        sid = re.match(r'<section\b[^>]*\bid="([^"]*)"', sec)
        h1 = re.search(r'<h1 class="chapter"[^>]*>(.*?)</h1>', sec, re.S)
        if (sid and sid.group(1) in ("contents", "bookindex")) or (
                h1 and X.text_of(h1.group(1)) in ("Contents", "Index")):
            continue
        keep.append(sec)
    s = re.sub(r"</?t[hd]\b[^>]*>", "\t", "".join(keep))
    s = re.sub(r"</?(?:p|li|div|h[1-6]|tr|table|section|ul|ol|br|blockquote)\b[^>]*>", "\n", s)
    s = X.H.unescape(re.sub(r"<[^>]+>", " ", s))
    for line in s.split("\n"):
        if "\t" in line:
            for cell in line.split("\t"):
                yield True, re.sub(r"\s+", " ", cell).strip()
        else:
            yield False, re.sub(r"\s+", " ", line).strip()


def _as_conditions(text, cell):
    """The condition words a passage uses AS conditions. A word counts when it is capitalised
    mid-sentence ("is left Stupefied", "Fatigued, then 1d6 Blood"), or anywhere in a table cell;
    a sentence that opens on "Wounded," is prose. A word joined to a capitalised neighbour by a
    space, hyphen or slash is part of a name (the Cursed Man, the Moon-Cursed, the Petrified Man
    at Wilcox, Fledgling / Weakened) and is left alone."""
    for m in re.finditer(_TITLE, text):
        w = m.group(1)
        if w not in CONDITION_WORDS:
            continue
        before, after = text[:m.start()], text[m.end():]
        if (re.match(r"(?: ?[-/] ?| )[A-Z]", after)
                or re.search(r"[A-Z][\w'\u2019]*(?: ?[-/] ?| )$", before)):
            continue
        prev = before.rstrip()
        if not cell and (not prev or prev[-1] in _OPENS):
            continue
        yield w, text[max(0, m.start() - 40):m.end() + 30].strip()


def check_conditions(dig, creatures):
    print("\nConditions: every one a stat block, a table or a rule names is defined in Appendix B")
    defined = []
    for _ch, _sec, tb in X.all_tables(dig["books"]["blood-and-grit.html"]):
        if tb["headers"][:1] == ["Condition"]:
            defined = [r[0] for r in tb["rows"]]
    if not defined:
        fail("Appendix B's condition table could not be read")
        return
    # A condition is named in Title Case, which is what makes this findable at all. The stat blocks
    # are read word by word, as they always were, since every word in one is a rule. The books are
    # read through _as_conditions, which keeps a sentence's opening word and a name out of it, so
    # that a lore paragraph may still say "blinded by the dust" and the Bestiary may keep its Cursed
    # Man. Until 2026-09-25 only the stat blocks were read, and "Stupefied" sat in the Keeper's
    # hazards table with nothing to find it.
    known = {d.split()[0] for d in defined}
    unlisted = sorted(known - CONDITION_WORDS)
    for w in unlisted:
        fail(f"Appendix B defines \"{w}\" and CONDITION_WORDS does not list it, so the books were "
             "never read for it. Add it.")
    invented, used, books = {}, set(), 0
    for c in creatures:
        blob = " ".join([c.get("special", ""), c.get("attacks", ""),
                         c.get("puttingItDown", ""), c.get("mark", "")])
        for w in re.findall(_TITLE, blob):
            CHECKS[0] += 1
            if w in known:
                used.add(w)
            elif w in CONDITION_WORDS:
                invented.setdefault(w, []).append(f"the {c['name']} stat block")
    for name in X.BOOKS:
        path = ROOT / name
        if not path.is_file():
            fail(f"{name} is not built, so its tables and rules went unread")
            continue
        books += 1
        for cell, text in _rules_text(path.read_text(encoding="utf-8")):
            for w, where in _as_conditions(text, cell):
                CHECKS[0] += 1
                if w in known:
                    used.add(w)
                else:
                    invented.setdefault(w, []).append(f"{name}: \u201c{where}\u201d")
    for w, where in sorted(invented.items()):
        fail(f"\"{w}\" is named as a condition {len(where)} time(s) and Appendix B does not "
             f"define it. First at {where[0]}")
    if not (invented or unlisted):
        ok(f"{len(defined)} conditions defined; the {len(used)} that the stat blocks and the tables "
           f"and rules of all {books} books name are all among them, and none invents one")


def check_benchmarks(dig, creatures, verbose):
    print("\nThe benchmarks against the population they describe")
    tb = bestiary_table(dig, "Building Your Own Dead", "Tier")
    if tb is None:
        fail("the benchmark table could not be read")
        return
    # A Tier may print an em dash rather than a number, and Tier VIII prints one for Blood on
    # purpose (B6, 2026-08-30): nothing has ever emptied one, so a benchmark there would be a
    # promise the ladder cannot keep. A missing benchmark means that field is not measured at that
    # Tier, rather than an IndexError halfway through the run.
    def _first(cell):
        v = nums(cell)
        return v[0] if v else None

    bench = {i: {"defense": _first(r[1]), "blood": _first(r[3])}
             for i, r in enumerate(tb["rows"], start=1)}
    # The band. The book calls these benchmarks and says outright that a creature may sit off them,
    # so a tight band would fail on design rather than on error. The band used is the distance to
    # the NEIGHBOURING Tier's benchmark: a Tier III thing may be tougher or softer than the Tier III
    # row, and only becomes a finding when it has walked all the way into Tier II or Tier IV
    # territory and past it. That is the difference between a creature with character and a typo.
    lo_t, hi_t = min(bench), max(bench)
    out = []
    for c in creatures:
        t = c["tier"]
        CHECKS[0] += 2
        for field, key in (("defense", "defense"), ("blood", "blood")):
            v = nums(c.get(key, ""))
            if not v:
                continue
            v = v[0]
            here = bench[t][field]
            if here is None:
                continue
            below = bench[max(lo_t, t - 1)][field] or here
            above = bench[min(hi_t, t + 1)][field] or here
            span = max(here - below, above - here, 2)
            if not (here - 2 * span <= v <= here + 2 * span):
                out.append((c["name"], t, field, v, here))
    for name, t, field, v, here in out[:10]:
        fail(f"{name} (Tier {t}) has {field} {v}, more than two Tiers from the benchmark {here}")
    if verbose or out:
        for t in sorted(bench):
            vals = sorted(nums(c.get("blood", ""))[0] for c in creatures
                          if c["tier"] == t and nums(c.get("blood", "")))
            if bench[t]["blood"] is None:
                continue
            if vals:
                mid = vals[len(vals) // 2]
                print(f"          Tier {t}: {len(vals):>3} creatures, Blood {vals[0]}-{vals[-1]}, "
                      f"median {mid}, benchmark {bench[t]['blood']}")
    if not out:
        ok(f"{len(creatures)} creatures all sit within their Tier's band for Defense and Blood")


# The parent system's vocabulary, and what this game calls the same thing. Blood & Grit is
# Pathfinder-2E-derived, so its ancestor's words are the ones that leak: a session writing a new
# creature reaches for "Armor Class" without noticing, and the stat block reads fluently and sends
# a Keeper to look up a term the glossary has never heard of. "Enfeebled" arrived exactly that way
# and sat in two stat blocks until this audit was written. Left side is what must never appear;
# right side is what the books actually say.
FOREIGN = {
    "Armor Class": "Defense",
    "hero point": "Grit",
    "spell slot": "the Sign or Faith pool",
    "spellcaster": "the Calling that works them",
    "cantrip": "a Rank 1 Sign",
    "attack of opportunity": "a Reaction",
    "ability score increase": "the level-up boosts",
    "Perception check": "a Notice check",
    "Diplomacy check": "a Persuade check",
    "Bluff check": "a Deceive check",
    "Will save DC": "your Sign DC",
}

# Borrowed words that ARE legitimate here, reported so a human can glance at them and never
# failed on. The first version of this check failed on all of them and was wrong about every one:
# "Your Blood is your hit points" is the book teaching a reader who arrived from another game,
# "Nerve and the Mark are the truest hit points in this game" is a deliberate figure, and
# "Wisdom in this country is a wound that does not close" is simply the English word. A checker
# that fires on good prose gets ignored, and then it is not a checker. What stays hard above is
# the set with no honest English or metaphorical use at all. Nobody writes "Armor Class 17" by
# accident in a sentence that means anything else.
FOREIGN_SOFT = {"hit points": "Blood", "Hit Points": "Blood", "saving throw": "save",
                "sanity": "Nerve", "experience points": "levels"}

# Features the app models and the books describe, held to each other by name. A row is a promise
# that BOTH sides carry the thing: the book states the rule, the app tracks the state. When the
# audit reports one side missing, the fix is to build the missing half rather than to delete the
# row. A rule printed in a book the app cannot run is a rule the Keeper does by hand at a table
# where everything else is done for them, and app state the books never explain is a number nobody
# can check. Add a row the day a feature lands on either side.
PARITY = [
    ("the Mark", r"track of six steps", r"\bpublic int Mark\b"),
    ("Taint", r"\bTaint\b", r"\bpublic int Taint\b"),
    ("Grit", r"\bGrit\b", r"\bpublic int Grit\b"),
    ("Nerve", r"\bNerve\b", r"\bpublic int NerveCur\b"),
    ("Blood", r"\bBlood\b", r"\bpublic int BloodCur\b"),
    ("the Calling pools", r"\bFaith\b", r"\bpublic string PoolName\b"),
    ("the spoor clock", r"sign and spoor|sign & spoor", r"SpoorClockSegments"),
    ("the Pact-Sworn's Debts", r"on your third Debt", r"\bTallyOwed\b"),
    ("the Witch's familiar", r"A small beast is bound to you",
     r"\bpublic string FamiliarKind\b"),
    ("the familiar on the field", r"scouts and\s+spies at your bidding",
     r"\bpublic string FamiliarOf\b"),
    ("the Familiar-Bound's spirit-carry", r"carries your spirit to a new dawn",
     r"\bpublic bool FamiliarCarried\b"),
    # Added 2026-08-31. The first is G2's finding: Ch. IV makes two corrections to the encounter
    # budget and the app carried one of them. The other two are B6b's: a rule that lived only in
    # a C# switch statement until the book printed the table it decides from.
    ("Ch. IV's dearer pricing", r"price a fight one rung", r"\bPriceDearerFrom\b"),
    ("the table of familiars", r"from the table of familiars", r"\bCgFamiliar\b"),
    ("the Binding rite", r"\bThe Binding\b", r"\bCgFamiliarRite\b"),
]


def check_shared_vocabulary(dig):
    print(f"\nOne vocabulary: the {len(dig['books'])} books, and the parent system's words "
          "that must not appear")
    hits, soft = 0, []
    for name, book in dig["books"].items():
        for ch, sec, para in X.all_text(book):
            for foreign, ours in FOREIGN.items():
                CHECKS[0] += 1
                if re.search(r"\b" + re.escape(foreign) + r"\b", para, re.I):
                    hits += 1
                    where = f"{name}, {ch}" + (f" / {sec}" if sec else "")
                    fail(f"{where}: \"{foreign}\" should be \"{ours}\"")
                    idx = para.lower().find(foreign.lower())
                    print(f"          …{para[max(0, idx - 60):idx + 60]}…")
            for foreign, ours in FOREIGN_SOFT.items():
                CHECKS[0] += 1
                if re.search(r"\b" + re.escape(foreign) + r"\b", para):
                    soft.append((name, ch, foreign, ours, para))
    if not hits:
        ok(f"{len(FOREIGN)} borrowed terms checked across all {len(dig['books'])} books: none of them appears")
    if soft:
        print(f"    note  {len(soft)} legitimate borrowing(s), reported and not failed, glosses "
              "for a reader arriving from another game:")
        for name, ch, foreign, ours, para in soft:
            idx = para.find(foreign)
            print(f"          {name}, {ch}: \"{foreign}\" ({ours})")
            print(f"            …{para[max(0, idx - 55):idx + 55]}…")




# Repeats that are meant to be there. Kept short and each one earns its line, because an allow-list
# is how a check stops finding things.
OK_TWICE = {
    # The Bestiary's rule of thumb, printed once in the by-Tier appendix's opening and again as the
    # caption over the Threat-by-Tier table. A Keeper reads one or the other, rarely both.
    "A creature is a fair, hard fight for a party of twice its Tier in levels.",
}


# Abbreviations that end in a full stop and are not the end of a sentence. Splitting on the stop
# alone chops "by Mr. Laidlaw, who was in liquor" into a fragment ending "by Mr.", and two reports
# that differ after the name then read as the same sentence. Found 2026-09-19 by the Book of
# Legends, which prints a marshal's report and the amended version of it and differs in the second
# half of the opening line. The check was reporting a repeat that was not there and, worse, was
# comparing fragments rather than sentences everywhere else in every book.
_ABBR = (r"Mr|Mrs|Ms|Dr|Rev|Fr|Sr|Jr|St|Ch|No|Co|Capt|Lieut|Col|Gen|Sgt|Maj|Hon|Esq|Prof"
         r"|Jan|Feb|Mch|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec"
         r"|lb|oz|ft|yd|in|viz|inst|ult|approx|vol|fig|pp|cf")
_PROTECT = re.compile(rf"\b({_ABBR})\.(?=\s)", re.I)
_SENT = re.compile(r"(?<=[.!?])\s+")


def sentences(text):
    """Split prose into sentences without breaking at an abbreviation's full stop."""
    guarded = _PROTECT.sub("\\1\x00", text)
    return [s.replace("\x00", ".") for s in _SENT.split(guarded)]


def check_no_accidental_repeats(dig):
    """The same sentence printed twice in one book, which is a copy rather than a refrain.

    Written 2026-09-02, after two keeper-notes in Ch. XV were found duplicated. The cause was a
    re-runnable patch helper whose "already applied" guard was `old not in s and new in s` -- which
    never fires when `new` contains `old`, and "append a sentence to this paragraph" is exactly that
    shape. Nothing else in the repo asks whether a book repeats itself.

    Exactly twice is the signature. Genuine refrains repeat more than that: the Disciplines boiler-
    plate 15 times, the Signs ladder 5, the safety line 3. Creature furniture is cut first, because
    a module prints a creature's Found line in its roster and again in its stat block on purpose.
    """
    print("\nNo accidental repeats: a sentence printed twice in one book is a copy, not a refrain")
    # Creature text repeats BY DESIGN. A module prints a stat block generated from creatures.json in
    # its roster and again where the fight happens, so the same Found line and the same Putting It
    # Down land in two sections on purpose. Rather than guess at markup, ask the source: anything
    # already in creatures.json is generated furniture rather than authored prose.
    generated = set()
    for c in json.loads((ROOT / "GK/rules/Data/creatures.json").read_text(encoding="utf-8")):
        for v in c.values():
            for piece in (v if isinstance(v, list) else [v]):
                if not isinstance(piece, str):
                    continue
                for t in sentences(piece):
                    t = re.sub(r"\s+", " ", t).strip()
                    if len(t) >= 70:
                        # Indexed by the TAIL, because a module prints these under a run-in label
                        # ("Putting it down Draw it onto dry land and end it there...") and the
                        # extractor hands back label and sentence as one string. The tail is the
                        # part that is verbatim from the data either way.
                        generated.add(t[-40:])
    found = 0
    for name, book in dig["books"].items():
        counts = {}
        for ch, sec, para in X.all_text(book):
            for s in sentences(para):
                s = re.sub(r"\s+", " ", s).strip()
                # A stat line is data, not prose: two Callings legitimately share
                # "Hit Die d10 · Trained Skills 4 + WIT · ...". The middot is this house's
                # separator for those and appears in no running sentence.
                if (len(s) >= 70 and "·" not in s and s[-1] in ".!?"
                        and s not in OK_TWICE and s[-40:] not in generated):
                    counts.setdefault(s, []).append(f"{ch}" + (f" / {sec}" if sec else ""))
        for s, where in counts.items():
            CHECKS[0] += 1
            if len(where) == 2:
                found += 1
                fail(f"{name}: printed twice, \"{s[:96]}…\"")
                print(f"          {where[0]}")
                print(f"          {where[1]}")
    if not found:
        ok(f"no sentence of 70 characters or more appears exactly twice in any of the "
           f"{len(dig['books'])} books")


def check_chapter_refs(dig):
    print("\nCross-references: every chapter a book points at is a chapter that exists")
    have = {}
    for name, book in dig["books"].items():
        have[name] = {c["roman"] for c in book["chapters"] if c["roman"]}
    spine = have.get("blood-and-grit.html", set())
    # A reference may name the book it points at, and that form is the easiest of all to check
    # against the right book -- which this did not do until 2026-08-30, when the Bestiary's new
    # apex entries were failed for citing "Keeper's Book Ch. XV", a chapter that exists.
    NAMED = {"keeper": "keeper-handbook.html", "player": "blood-and-grit.html",
             "bestiary": "bestiary.html"}
    bad = 0
    for name, book in dig["books"].items():
        own = have[name]
        for ch, sec, para in X.all_text(book):
            for m in re.finditer(r"(?:(Keeper|Player|Bestiary)(?:&rsquo;s|'s|\u2019s)?\s+Book\s+)?"
                                 r"\bCh(?:apter|\.)\s+([IVXL]+)\b", para):
                CHECKS[0] += 1
                n = ROMAN.get(m.group(2)) or X.ROMAN.get(m.group(2))
                if n is None:
                    continue
                named = NAMED.get((m.group(1) or "").lower())
                if named:
                    # it said which book: resolve against that one and nothing else
                    if n not in have.get(named, set()):
                        bad += 1
                        fail(f"{name}, {ch}: \"{m.group(1)}'s Book Chapter {m.group(2)}\" is not a "
                             f"chapter of {named}")
                    continue
                # A bare reference resolves against the book it is in, or against the Player's
                # Book, which is the shared spine every other book is built on and cites by default.
                if n not in own and n not in spine:
                    bad += 1
                    fail(f"{name}, {ch}: \"Chapter {m.group(2)}\" exists in neither this book "
                         f"(I–{max(own) if own else 0}) nor the Player's Book")
    if not bad:
        ok(f"every Chapter reference in all {len(dig['books'])} books resolves "
           f"(Player's I–{max(spine)}, and each book's own)")


# Perdition Basin is the example every book reaches for (2026-09-19), and until then it was told
# four slightly different ways. The modules had Coffin Wells as "a silver camp gone sour, four days
# south" and the mission "on the east wall"; both core books had a cattle town a day south-west and a
# mission "a ruin fifty years"; the Keeper's Book bound the thing "a century ago" and gave the ring's
# keeper as "Padre Ildefonso, or the layfamily", while Module III is built on 1809, the fire of 1811
# and Esperanza Rios. Every one of those was written in good faith against a copy of the facts. The
# place list is one source now (perdition_map.RIDER_KNOWS); this holds the rest.
BASIN_RETIRED = [
    (r"silver camp gone sour", "Coffin Wells is a cattle town"),
    (r"four days south", "Coffin Wells is a day south and west of the Crossing, 27 miles on the map"),
    (r"a ruin (?:for )?fifty years", "the mission burned in 1811 and has been a ruin since"),
    (r"(?:a century (?:ago|back))[^.]{0,80}\bpadres\b|\bpadres\b[^.]{0,80}a century (?:ago|back)",
     "the padres came in 1809"),
    (r"Padre Ildefonso", "the ring's last keeper is Esperanza Ríos (Module III)"),
    (r"railhead at Calvary Crossing", "the railroad is still surveying the basin"),
    (r"San Clavo[^.]{0,60}on the east wall|on the east wall[^.]{0,60}San Clavo",
     "the mission is 15 miles east of Coffin Wells, mid-basin"),
]
RIDER_LIST_IN = ["blood-and-grit.html", "module-salt-at-coffin-wells.html",
                 "module-a-face-not-his-own.html", "module-what-the-water-answers.html"]


def check_basin(dig):
    print("\nPerdition Basin: one county, told the same way in every book")
    import html as _html
    from perdition_map import RIDER_KNOWS
    bad = 0
    for name, book in dig["books"].items():
        text = "\n".join(t for _c, _s, t in X.all_text(book))
        for pat, why in BASIN_RETIRED:
            CHECKS[0] += 1
            for m in re.finditer(pat, text, re.I):
                bad += 1
                fail(f"{name}: \"{m.group(0)[:70]}\" contradicts the basin ({why})")
    for name in RIDER_LIST_IN:
        book = dig["books"].get(name)
        if book is None:
            bad += 1
            fail(f"{name} is not built, so its list of places cannot be checked")
            continue
        text = re.sub(r"\s+", " ", "\n".join(t for _c, _s, t in X.all_text(book)))
        for place, blurb in RIDER_KNOWS:
            CHECKS[0] += 1
            said = re.sub(r"\s+", " ", _html.unescape(blurb))
            if said not in text:
                bad += 1
                fail(f"{name}: what a rider knows about {place} is not the shared line "
                     f"(perdition_map.RIDER_KNOWS)")
    if not bad:
        ok(f"no retired basin fact in any book ({len(BASIN_RETIRED)} watched), and the "
           f"{len(RIDER_KNOWS)} places read the same in all {len(RIDER_LIST_IN)} books that list them")


def check_app_book_parity(dig, core, chargen_src):
    print("\nApp and books: every feature one carries, the other carries too")
    prose = "\n".join(t for b in dig["books"].values() for _c, _s, t in X.all_text(b))
    app = core + "\n" + chargen_src
    gaps = 0
    for label, book_pat, app_pat in PARITY:
        CHECKS[0] += 2
        in_book = bool(re.search(book_pat, prose, re.I))
        in_app = bool(re.search(app_pat, app))
        if in_book and not in_app:
            gaps += 1
            fail(f"{label}: the books state the rule, the app tracks nothing; build it in the app")
        elif in_app and not in_book:
            gaps += 1
            fail(f"{label}: the app tracks it, no book explains it; write it into the book")
    if not gaps:
        ok(f"{len(PARITY)} feature(s): each one both printed in a book and tracked by the app")


# Every number README.md spells out about the game, and the file that actually carries it.
# Written 2026-09-22, after the front page was found saying "nineteen Callings" (the Medicine
# Man merged with the Shaman at v1.56.0, so there have been eighteen since), "seventeen Calling
# tables", and "three books" in four places with the Book of Legends sitting in the table right
# below. None of it was wrong when it was written and all of it was wrong by the time a stranger
# read it, which is the whole argument for counting rather than typing. README's version claims
# have been generated since 2026-08-08; its counts were the half nobody had automated.
# Number words, including the compounds, so a claim like "fifty-six Signs" can be read back.
_ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
         "fifteen sixteen seventeen eighteen nineteen").split()
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
         "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
WORDS = {w: i for i, w in enumerate(_ONES)}
WORDS.update(_TENS)
WORDS.update({f"{t}-{o}": tv + ov
              for t, tv in _TENS.items()
              for ov, o in enumerate(_ONES) if 0 < ov < 10})

# Every number a front page spells out in words, and the key in `truth` that settles it. The root
# README is what a stranger meets on GitHub; GK/source/README.md is what they meet inside the zip,
# and it is mirrored to GritKeeper/README.md, which is the copy that actually ships.
FRONT_PAGE = [
    (r"(\w+) Callings, (\w+) Origins",                        ("callings", "origins")),
    (r"checks its (\w+)\s+Calling tables",                    ("callings",)),
    (r"off (\w+) books, (\w+) ready-to-run",                  ("books", "modules")),
    (r"\(The (\w+) books are PDFs",                           ("books",)),
    (r"(\w+) companion volumes",                               ("books",)),
    (r"indexes for all (\w+) books and the (\w+) modules",    ("books", "modules")),
    (r"prints all (\w+) documents \((\w+) books, (\w+) modules\)",
     ("documents", "books", "modules")),
    # The Book of Legends' papers, in digits. Added 2026-09-24: v1.3 took the book from 98 papers to
    # 157, and three typed copies of the 98 had nothing holding them to it.
    (r"(\d+) in-world papers",                              ("papers",)),
]

APP_README = [
    (r"\(The (\w+) books\s+are PDFs",                        ("books",)),
    (r"## The (\w+) tabs",                                   ("tabs",)),
    (r"Keeper's screen in (\w+) leaves",                      ("leaves",)),
    (r"the ([\w-]+) Signs in (\w+) lists",                   ("signs", "signlists")),
    (r"(\w+) skills with proficiency ticks",                  ("skills",)),
]

# CLAUDE.md types the same counts three times, in the book table, the builder's row and the Book of
# Legends' own section, so it is held to the built book the same way.
CLAUDE_MD = [
    (r"none \((\d+) documents\)",                          ("papers",)),
    (r"it is (\d+) in-world documents",                     ("papers",)),
    (r"`(\d+)` documents, `(\d+)` provenance notes, `(\d+)` editor's notes",
     ("papers", "glosses", "ednotes")),
]

PAGES = [("README.md", FRONT_PAGE), ("GK/source/README.md", APP_README), ("CLAUDE.md", CLAUDE_MD)]


def check_front_page(chargen):
    print("\nThe front pages: every number they spell out, against the file that carries it")
    # The two bundle manifests, read as text rather than imported: make_bundles.py builds both
    # zips at import time, and an audit that writes a deliverable is not an audit.
    manifest = (ROOT / "tools/make_bundles.py").read_text(encoding="utf-8")
    truth = {
        "callings": len(chargen["callings"]),
        "origins": len(chargen["origins"]),
        "skills": len(chargen["skills"]),
        "signs": len(chargen["signs"]),
        "signlists": len({s["list"] for s in chargen["signs"]}),
    }
    for key, var in (("books", "BOOKS"), ("modules", "MODULES")):
        block = re.search(rf"^{var} = {{(.*?)^}}", manifest, re.S | re.M)
        if block is None:
            fail(f"tools/make_bundles.py has no {var} manifest to count")
            return
        truth[key] = len(re.findall(r'"[^"]+\.html":', block.group(1)))
    truth["documents"] = truth["books"] + truth["modules"]
    # Counted off the built book the way build_legends.py counts them when it prints its summary line.
    legends = ROOT / "legends.html"
    if legends.is_file():
        built = legends.read_text(encoding="utf-8")
        truth.update(papers=built.count('class="paper'), glosses=built.count('class="gloss"'),
                     ednotes=built.count('class="ednote"'))
    else:
        fail("legends.html is not built, so the Book of Legends counts the docs quote cannot be checked")
        return

    # The tabs are counted off the constructor calls that name one. MainForm.LazyTab builds its
    # shell with `new TabPage(title)`, an unquoted argument, so the helper does not count itself.
    tabs_src = "".join((ROOT / "GK/source" / f).read_text(encoding="utf-8")
                       for f in ("MainForm.cs", "Tabs.cs", "TabsChargen.cs", "TabsMap.cs"))
    truth["tabs"] = len(re.findall(r'new TabPage\("', tabs_src))
    leaves = re.search(r"RefLeafTitles\s*=\s*\{(.*?)\};",
                       (ROOT / "GK/source/Tabs.cs").read_text(encoding="utf-8"), re.S)
    if leaves is None:
        fail("GK/source/Tabs.cs has no RefLeafTitles array to count")
        return
    truth["leaves"] = leaves.group(1).count('"') // 2

    bad = 0
    for name, claims in PAGES:
        page = (ROOT / name).read_bytes().decode("utf-8")
        for pattern, names in claims:
            CHECKS[0] += 1
            m = re.search(pattern, page)
            if not m:
                bad += 1
                fail(f"{name} no longer says {pattern!r}, so this check is guarding nothing. "
                     f"The claim moved or went: repoint it or take it out.")
                continue
            for said, key in zip(m.groups(), names):
                CHECKS[0] += 1
                count = int(said) if said.isdigit() else WORDS.get(said.lower())
                if count != truth[key]:
                    bad += 1
                    fail(f'{name} says "{said} {key}" and there are {truth[key]}: '
                         f'"{" ".join(m.group(0).split())[:60]}"')

    # The delivered copy is the one inside GritKeeper.zip, and it is a mirror, not a source.
    CHECKS[0] += 1
    if (ROOT / "GK/source/README.md").read_bytes() != (ROOT / "GritKeeper/README.md").read_bytes():
        bad += 1
        fail("GK/source/README.md and GritKeeper/README.md have drifted. The second is the copy "
             "that ships, so a stranger downloading the app reads the stale one. Re-mirror it.")

    if not bad:
        ok(f"{sum(len(c) for _, c in PAGES)} counted claim(s) across "
           f"{len(PAGES)} front page(s), and the app README mirrors: "
           + ", ".join(f"{v} {k}" for k, v in truth.items()))


# How many creatures there are is a fact with one home, `GK/rules/Data/creatures.json`, and
# check_creatures_current above proves that file is still the built Bestiary. Everywhere else the
# number is TYPED, into prose nothing compiles and nothing counts. On 2026-09-23 a read of the
# books for the playtest found fourteen such copies, every one of them still saying 175 or 150,
# two Bestiary expansions out of date. One was `GK/source/README.md`, which is mirrored into the
# zip, so every download told a Keeper the app held 175 creatures while the exe beside it held
# 182. The app's own standing rule is that a count appearing in prose must be derived; prose in a
# Markdown file and a C# comment cannot derive anything, so it is held to the count instead.
COUNT_CLAIMS = [
    ("CLAUDE.md",             r"All (\d+) are always indexed"),
    ("GK/CLAUDE.md",          r"all \*\*(\d+) creatures\*\*"),
    ("GK/CLAUDE.md",          r"All (\d+) creatures, extracted"),
    ("GK/CLAUDE.md",          r"the Bestiary's (\d+) entries are horrors"),
    ("GK/CLAUDE.md",          r"\((\d+) creatures parse"),
    ("GK/CLAUDE.md",          r"across all (\d+) creatures"),
    ("GK/CLAUDE.md",          r"all (\d+) entries are written"),
    ("GK/CLAUDE.md",          r"the Bestiary's (\d+) spends"),
    ("GK/rules/Core.cs",      r"the Bestiary's (\d+) entries are horrors"),
    ("GK/rules/Core.cs",      r"Every one of the (\d+)"),
    ("GK/rules/Core.cs",      r"(\d+) entries is written"),
    ("GK/rules/Core.cs",      r"the (\d+)\. So unless"),
    ("GK/source/MainForm.cs", r"of (\d+) spends four and a half thousand"),
    ("GK/source/README.md",   r"all \*\*(\d+) creatures\*\*"),
    ("GritKeeper/README.md",  r"all \*\*(\d+) creatures\*\*"),
    ("audits/README.md",      r"against the (\d+) creatures"),
    ("audits/audit_ui.py",    r"# (\d+) creatures spent four"),
]


def check_creature_count(creatures):
    print("\nHow many creatures there are, in every place that says so")
    truth = len(creatures)
    bad = 0
    for name, pattern in COUNT_CLAIMS:
        CHECKS[0] += 1
        found = re.findall(pattern, (ROOT / name).read_text(encoding="utf-8"))
        if len(found) != 1:
            bad += 1
            fail(f"{name} matches {pattern!r} {len(found)} times, not once, so this check is "
                 f"guarding nothing or guarding two things. Repoint it or take it out.")
            continue
        if int(found[0]) != truth:
            bad += 1
            fail(f"{name} says {found[0]} creatures and there are {truth}: {pattern!r}")
    if not bad:
        ok(f"{len(COUNT_CLAIMS)} typed copies of the creature count across "
           f"{len({n for n, _ in COUNT_CLAIMS})} files, all reading {truth}")


# The counts the Player's Book spells out in words about itself, and the key in `truth` that
# settles each one. check_front_page does this for the two READMEs and check_creature_count for
# the numerals typed into prose files; these are the same rot inside the book, where it is worst,
# because a number written as a word looks like writing rather than like a fact, and a proofreader
# slides straight over it. On 2026-09-23 the Signs chapter counted itself at fifty-five against
# fifty-six, and Ch. XIII called the Callings of Faith six when the book prints five.
# The last number is how many times the sentence is expected to appear. The Sign ceiling is
# stated twice -- in Ch. VII, where a player meets the Old Dark, and again in Ch. XIII, where
# the ladder is printed -- and on 2026-09-23 the two copies disagreed, so both are read.
BOOK_COUNTS = [
    (r"There are ([\w-]+) of them here", "signs", 1),
    (r"Each of the ([\w-]+) Callings of Faith", "faith", 1),
    (r"Every Sign carries a Rank from one to ([\w-]+)", "top_rank", 2),
    (r"Every Miracle carries a Rank from one to ([\w-]+)", "top_rank", 1),
]

# The two notes that say how thin the top of each ladder is. The Signs note says Ranks Six and
# Seven hold the same number "apiece", which is a claim of its own; the Miracles note was copied
# from it and never recounted, and since 2026-09-23 it counts each Rank separately, because Six
# and Seven differ there. Either shape is read, and every Rank it names is held to the data.
SHELVES = [("Signs", "signs"), ("Miracles", "miracles")]
SHELF_RES = [
    (r"Ranks Six and Seven hold ([\w-]+) {noun} apiece and Rank Eight holds ([\w-]+)", (6, 7), (8,)),
    (r"Rank Six holds ([\w-]+) {noun}, Rank Seven ([\w-]+),? and Rank Eight ([\w-]+)", (6,), (7,), (8,)),
]


def _reading(name):
    """A book as a reader sees it: no tags, no entities, no line breaks."""
    import html as _html
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ",
                                                     (ROOT / name).read_text(encoding="utf-8"))))


def check_book_counts(chargen):
    print("\nThe counts the Player's Book spells out about itself")
    book = _reading("blood-and-grit.html")
    by_rank = {which: {r: sum(1 for w in chargen[which] if w["rank"] == r)
                       for r in {w["rank"] for w in chargen[which]}}
               for _, which in SHELVES}
    truth = {
        "signs": len(chargen["signs"]),
        "faith": sum(1 for c in chargen["callings"] if c.get("group") == "Faith"),
        "top_rank": max(max(c) for c in by_rank.values()),
    }
    bad = 0
    for pattern, key, hits in BOOK_COUNTS:
        CHECKS[0] += 1
        found = re.findall(pattern, book)
        if len(found) != hits:
            bad += 1
            fail(f"the Player's Book matches {pattern!r} {len(found)} times, not {hits}, so this "
                 f"check is guarding nothing or guarding something it was not pointed at. "
                 f"Repoint it or take it out.")
            continue
        for said in found:
            CHECKS[0] += 1
            if WORDS.get(said.lower()) != truth[key]:
                bad += 1
                fail(f'the Player\'s Book says "{said}" where there are '
                     f"{truth[key]}: {pattern!r}")

    for noun, which in SHELVES:
        CHECKS[0] += 1
        counts = by_rank[which]
        found = [(m, ranks) for pattern, *ranks in SHELF_RES
                 for m in re.findall(pattern.format(noun=noun), book)]
        if len(found) != 1:
            bad += 1
            fail(f"the note on how many {noun} the top Ranks hold matched {len(found)} times, "
                 f"not once. Repoint it or take it out.")
            continue
        said, ranks = found[0]
        for word, group in zip(said, ranks):
            for r in group:
                CHECKS[0] += 1
                if WORDS.get(word.lower()) != counts[r]:
                    bad += 1
                    fail(f"the book says Rank {_ONES.split()[r].title()} holds {word} {noun} and it holds "
                         f"{counts[r]}")

    if not bad:
        ok(f"{len(BOOK_COUNTS) + len(SHELVES)} count(s) the book spells out about itself: "
           + ", ".join(f"{v} {k}" for k, v in truth.items())
           + ", and the top three Ranks of both ladders")


def _keeper_lists():
    """XV_POWERS and XVI_LEGENDS as build_keeper.py declares them, read without running it."""
    tree = ast.parse((ROOT / "build_keeper.py").read_text(encoding="utf-8"))
    out = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in ("XV_POWERS", "XVI_LEGENDS")):
            out[node.targets[0].id] = ast.literal_eval(node.value)
    return out


def check_legends_both_books():
    print("\nThe legends: Keeper's Ch. XVI against the Book of Legends it sends the Keeper to")
    lists = _keeper_lists()
    if set(lists) != {"XV_POWERS", "XVI_LEGENDS"}:
        fail("build_keeper.py no longer declares XV_POWERS and XVI_LEGENDS where this check can "
             "read them. Repoint it or take it out.")
        return
    missing = [n for n in ("keeper-handbook.html", "legends.html") if not (ROOT / n).is_file()]
    if missing:
        fail(f"{' and '.join(missing)} not built, so the legends went unchecked")
        return
    keeper = (ROOT / "keeper-handbook.html").read_text(encoding="utf-8")
    heads = {X.text_of(h) for h in re.findall(r"<h2[^>]*>(.*?)</h2>",
                                             (ROOT / "legends.html").read_text(encoding="utf-8"),
                                             re.S)}
    bad = 0
    CHECKS[0] += 2
    written = re.findall(r'<h2 id="(legends-[^"]+)"', keeper)
    if written != [lg[0] for lg in lists["XVI_LEGENDS"]]:
        bad += 1
        fail(f"the built Keeper's Book has legends {written}, and XVI_LEGENDS lists "
             f"{[lg[0] for lg in lists['XVI_LEGENDS']]}. Rebuild it.")
    powers = [a for a in re.findall(r'<h2 id="(powers-[^"]+)"', keeper) if a != "powers-together"]
    if powers != lists["XV_POWERS"]:
        bad += 1
        fail(f"the built Keeper's Book has Powers {powers}, and XV_POWERS lists "
             f"{lists['XV_POWERS']}. Rebuild it.")
    held = 0
    for _anchor, here, short, there in lists["XVI_LEGENDS"]:
        CHECKS[0] += 1
        if there and there not in heads:
            bad += 1
            fail(f"Ch. XVI files {short} under \u201c{there}\u201d in the Book of Legends, and that "
                 f"book has no heading by that name")
        elif not there and here in heads:
            bad += 1
            fail(f"XVI_LEGENDS says the Book of Legends doesn't carry {short}, and it has a "
                 f"heading \u201c{here}\u201d")
        held += bool(there and there in heads)
    text = _reading("keeper-handbook.html")
    said = re.findall(r"\b(All|[A-Z][a-z-]+ of the) ([a-z-]+) legends below are in it", text)
    CHECKS[0] += 1
    if len(said) != 1:
        bad += 1
        fail(f"Ch. XVI's count of the legends in the Book of Legends matched {len(said)} times, "
             "not once. Repoint this check or take it out.")
    else:
        lead, total = said[0]
        says_held = WORDS.get(total) if lead == "All" else WORDS.get(lead.split()[0].lower())
        if WORDS.get(total) != len(written) or says_held != held:
            bad += 1
            fail(f"Ch. XVI says \u201c{lead} {total} legends below are in it\u201d, and the "
                 f"Book of Legends carries {held} of the {len(written)}")
    for n in re.findall(r"\bthe ([a-z-]+) Powers\b", text):
        CHECKS[0] += 1
        if n in WORDS and WORDS[n] != len(powers):
            bad += 1
            fail(f"the Keeper's Book says \u201cthe {n} Powers\u201d, and Ch. XV has {len(powers)}")
    if not bad:
        ok(f"{len(written)} legends, {held} of them in the Book of Legends under the headings "
           f"Ch. XVI gives, and {len(powers)} Powers, as the Keeper's Book counts them")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verbose", action="store_true",
                    help="print the per-Tier spread behind the benchmark check")
    args = ap.parse_args()

    dig = X.digest(root=ROOT)
    if "bestiary.html" in dig["missing"] or "blood-and-grit.html" in dig["missing"]:
        print("The books are not built. Run build_player.py and build_bestiary.py first.")
        return 1
    creatures = json.loads((ROOT / "GK/rules/Data/creatures.json").read_text(encoding="utf-8"))
    core = (ROOT / "GK/rules/Core.cs").read_text(encoding="utf-8")
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    print("Does the game play the same way in every place it is written down?")
    check_threat_by_tier(dig, core, claude)
    check_spoor(dig, core)
    check_creatures_current(creatures)
    check_roll_by_tier(dig, creatures)
    check_grounds(dig, creatures)
    check_conditions(dig, creatures)
    check_benchmarks(dig, creatures, args.verbose)
    check_shared_vocabulary(dig)
    check_no_accidental_repeats(dig)
    check_chapter_refs(dig)
    check_basin(dig)
    check_app_book_parity(dig, core, (ROOT / "GK/rules/CharGen.cs").read_text(encoding="utf-8"))
    check_front_page(json.loads(
        (ROOT / "GK/rules/Data/chargen.json").read_text(encoding="utf-8")))
    check_creature_count(creatures)
    check_book_counts(json.loads(
        (ROOT / "GK/rules/Data/chargen.json").read_text(encoding="utf-8")))
    check_legends_both_books()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} inconsistenc{'y' if len(FAILURES) == 1 else 'ies'} across "
              f"{CHECKS[0]:,} checks. A rule that reads two ways at the table is a rule the "
              "Keeper has to rule on mid-scene.")
        return 1
    print(f"book <-> book <-> app: the Keeper-side rules agree everywhere they are written "
          f"({CHECKS[0]:,} cross-checks, 0 drift).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
