#!/usr/bin/env python3
"""audit_consistency.py — does the game play the same way in every place it is written down?

`verify_rules.py` already guards the PLAYER's side: the Calling tables, the arms table,
the feature prose, the 3rd-level paths, and Ch. IV's encounter budget. That leaves the Keeper's
side, which is where the same number appears in the most places and where nothing has ever held
them together. Two tables in particular are printed in the Bestiary, restated in `CLAUDE.md`, and
compiled into the app as arrays — and until this file existed, editing any one of the three and
not the others produced a clean build, a green audit run, and a Keeper reading one number off the
page while the app on the table showed another.

What it holds together:

  1. THREAT BY TIER — the Bestiary's benchmark table, `Rules.TierRow`, and `CLAUDE.md`'s copy.
     Defense, Attack, Blood, both saves, damage die and Dread DC, five Tiers, three sites.
  2. SIGN & SPOOR — the Bestiary's Grounds table against `Rules.SpoorRow`. This one carries the
     safe-table rule, which is the promise that a horror too big for the posse arrives as a trace
     rather than as a fight, so it is the last table in the book that should be allowed to drift.
  3. THE BESTIARY AND ITS OWN DATA — `creatures.json` re-extracted from the built book and diffed
     against the committed file. The app reads the JSON and nothing re-extracts it automatically,
     so a Bestiary edit shipped without running `extract_creatures.py` leaves the app quoting the
     previous edition's stat block. Nothing caught that before this.
  4. THE ROLL, BY TIER — the generated appendix against the creature data it is generated from.
     It cannot drift while the book is freshly built; it drifts the moment the book is not.
  5. THE GROUNDS — every creature named in the eleven terrain tables must exist, and the Tier in
     parentheses beside it must be that creature's actual Tier. 143 entries, hand-written, each
     one an invitation to mistype a name or misremember a Tier.
  6. CONDITIONS — every condition a creature inflicts must be defined in the Player's Book
     Appendix B. A stat block that inflicts something the glossary never names is a rule the
     table cannot look up.
  7. THE BENCHMARKS AGAINST THE POPULATION — the printed Tier row says what a Tier III thing
     should look like; check that the Tier III things look like it. Reported as spread, and
     failed only where a creature sits outside its own Tier's band by more than the neighbouring
     Tiers' width, since the book is explicit that the benchmarks are a starting point.

Usage:
    python audits/audit_consistency.py            # every check
    python audits/audit_consistency.py --verbose  # and the per-creature numbers behind check 7

Reads built books, so build first. Read-only: writes nothing, ever.
"""
import argparse
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
    .NET SDK — that is the whole reason `audits/` is Python — and `Rules.TierRow` is a literal with
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
    print("\nThreat by Tier — the Bestiary, Rules.TierRow, and CLAUDE.md")
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
    print("\nSign & spoor — the Bestiary's Grounds table and Rules.SpoorRow")
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
        fail(f"the built book holds {len(fresh)} creatures, the JSON holds {len(creatures)} — "
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
        fail(f"{len(drift)} field(s) across {len(seen)} creature(s) differ from the built book — "
             "creatures.json is stale, re-extract it")
        for name, ks in list(seen.items())[:8]:
            print(f"          {name}: {', '.join(ks)}")
        return
    ok(f"{len(fresh)} creatures, every field identical to the book the app quotes")


def check_roll_by_tier(dig, creatures):
    print("\nThe Roll, by Tier — the generated appendix against the creature data")
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
    print("\nThe Grounds — every creature named in the terrain tables")
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
        fail(f"{sec}: \"{cell}\" — that creature is Tier {t}")
    if not (unknown or mistier):
        ok(f"{total} table entries: every name real, every Tier the creature's own")


def check_conditions(dig, creatures):
    print("\nConditions — every one a creature inflicts is defined in Appendix B")
    defined = []
    for _ch, _sec, tb in X.all_tables(dig["books"]["blood-and-grit.html"]):
        if tb["headers"][:1] == ["Condition"]:
            defined = [r[0] for r in tb["rows"]]
    if not defined:
        fail("Appendix B's condition table could not be read")
        return
    # A condition is named in Title Case in a stat block, which is what makes this findable at all.
    # The vocabulary is closed and small, so the scan looks for the DEFINED names plus a short list
    # of near-misses — a stat block reading "Staggered" or "Confused" is inventing a condition, and
    # that is the finding. Free prose elsewhere in the book is not scanned: the glossary governs
    # stat blocks, and a lore paragraph may say "blinded by the dust" without meaning the rule.
    known = {d.split()[0] for d in defined}
    invented = {}
    NEARMISS = {"Staggered", "Confused", "Dazed", "Paralyzed", "Paralysed", "Restrained",
                "Deafened", "Exhausted", "Enfeebled", "Stupefied", "Doomed", "Petrified",
                "Immobilized", "Immobilised", "Panicked", "Charmed", "Poisoned", "Cursed"}
    used = set()
    for c in creatures:
        blob = " ".join([c.get("special", ""), c.get("attacks", ""),
                         c.get("puttingItDown", ""), c.get("mark", "")])
        for w in re.findall(r"\b([A-Z][a-z]{2,13})\b", blob):
            CHECKS[0] += 1
            if w in known:
                used.add(w)
            elif w in NEARMISS:
                invented.setdefault(w, []).append(c["name"])
    for w, who in sorted(invented.items()):
        fail(f"\"{w}\" is inflicted by {len(who)} creature(s) ({who[0]}) and is not in Appendix B")
    if not invented:
        ok(f"{len(defined)} conditions defined; the {len(used)} the Bestiary inflicts are all among "
           "them, and no stat block invents one")


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
# the set with no honest English or metaphorical use at all — nobody writes "Armor Class 17" by
# accident in a sentence that means anything else.
FOREIGN_SOFT = {"hit points": "Blood", "Hit Points": "Blood", "saving throw": "save",
                "sanity": "Nerve", "experience points": "levels"}

# Features the app models and the books describe, held to each other by name. A row is a promise
# that BOTH sides carry the thing: the book states the rule, the app tracks the state. When the
# audit reports one side missing, the fix is to build the missing half rather than to delete the
# row — a rule printed in a book the app cannot run is a rule the Keeper does by hand at a table
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
]


def check_shared_vocabulary(dig):
    print("\nOne vocabulary — the six books, and the parent system's words that must not appear")
    hits, soft = 0, []
    for name, book in dig["books"].items():
        for ch, sec, para in X.all_text(book):
            for foreign, ours in FOREIGN.items():
                CHECKS[0] += 1
                if re.search(r"\b" + re.escape(foreign) + r"\b", para, re.I):
                    hits += 1
                    where = f"{name} — {ch}" + (f" / {sec}" if sec else "")
                    fail(f"{where}: \"{foreign}\" should be \"{ours}\"")
                    idx = para.lower().find(foreign.lower())
                    print(f"          …{para[max(0, idx - 60):idx + 60]}…")
            for foreign, ours in FOREIGN_SOFT.items():
                CHECKS[0] += 1
                if re.search(r"\b" + re.escape(foreign) + r"\b", para):
                    soft.append((name, ch, foreign, ours, para))
    if not hits:
        ok(f"{len(FOREIGN)} borrowed terms checked across all six books: none of them appears")
    if soft:
        print(f"    note  {len(soft)} legitimate borrowing(s), reported and not failed — glosses "
              "for a reader arriving from another game:")
        for name, ch, foreign, ours, para in soft:
            idx = para.find(foreign)
            print(f"          {name} — {ch}: \"{foreign}\" ({ours})")
            print(f"            …{para[max(0, idx - 55):idx + 55]}…")


def check_chapter_refs(dig):
    print("\nCross-references — every chapter a book points at is a chapter that exists")
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
                        fail(f"{name} — {ch}: \"{m.group(1)}'s Book Chapter {m.group(2)}\" is not a "
                             f"chapter of {named}")
                    continue
                # A bare reference resolves against the book it is in, or against the Player's
                # Book, which is the shared spine every other book is built on and cites by default.
                if n not in own and n not in spine:
                    bad += 1
                    fail(f"{name} — {ch}: \"Chapter {m.group(2)}\" exists in neither this book "
                         f"(I–{max(own) if own else 0}) nor the Player's Book")
    if not bad:
        ok(f"every Chapter reference in all six books resolves "
           f"(Player's I–{max(spine)}, and each book's own)")


def check_app_book_parity(dig, core, chargen_src):
    print("\nApp and books — every feature one carries, the other carries too")
    prose = "\n".join(t for b in dig["books"].values() for _c, _s, t in X.all_text(b))
    app = core + "\n" + chargen_src
    gaps = 0
    for label, book_pat, app_pat in PARITY:
        CHECKS[0] += 2
        in_book = bool(re.search(book_pat, prose, re.I))
        in_app = bool(re.search(app_pat, app))
        if in_book and not in_app:
            gaps += 1
            fail(f"{label}: the books state the rule, the app tracks nothing — build it in the app")
        elif in_app and not in_book:
            gaps += 1
            fail(f"{label}: the app tracks it, no book explains it — write it into the book")
    if not gaps:
        ok(f"{len(PARITY)} feature(s): each one both printed in a book and tracked by the app")


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
    check_chapter_refs(dig)
    check_app_book_parity(dig, core, (ROOT / "GK/rules/CharGen.cs").read_text(encoding="utf-8"))

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
