#!/usr/bin/env python3
"""The book↔data drift guard — the last seam in the single-source discipline.

The rest of the chain is already self-checking: the GritKeeper app reads every number from
`GK/rules/Data/chargen.json`, and `CharGen.Validate` re-derives each one from the formula, so
the data and the app can never quietly disagree (the smoke suite fails first). The one seam left
to a human hand is the *printed book* — the Player's Book prints nineteen Calling tables that I
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

    # --- and the APP'S OWN READMEs, which is the site this check did not read and which therefore
    #     drifted. The v1.44.0 repricing reached Core.cs, both books and CLAUDE.md; GK/CLAUDE.md and
    #     three READMEs went on printing the old 1 / 4 / 8 for three days, and the comment beside
    #     the CLAUDE.md check above claimed the rule was written nowhere this auditor could not see.
    #     A guard that names its own completeness has to be able to back it.
    for path in ("GK/source/README.md", "GritKeeper/README.md", "GK/CLAUDE.md"):
        text = _flat(path)
        if not text:
            continue                      # GritKeeper/ is generated; a clean tree may not have it
        m = re.search(r"mook (\d+)[,·\s]+even foe (\d+)[,·\s]+standout (\d+)", text, re.I)
        if not m:
            problems.append(f"{path}: states no encounter ladder (or reworded) — it named one "
                            "before, so a silent disappearance is the same drift by another route")
        else:
            got = tuple(int(g) for g in m.groups())
            want = (app["Mook"], app["Even foe"], app["Standout"])
            if got != want:
                problems.append(f"{path}: the encounter ladder reads {got}, the app says {want}")
        checks += 1

    return checks


# ---------------------------------------------------------------- the Origins
# Ch. IV's Origins are prose in chargen.json AND prose in the book, transcribed by hand between
# the two, and until 2026-08-26 nothing held them together at all -- the Callings had a guard, the
# arms table had a guard, and the ten Origins had none. That mattered more than it looked: the app
# does not merely display an Origin, it MINES it. CharGen.OriginFeatures pulls the rationed halves
# ("once per scene ...") out of the boon and burden text into tracked rows, and CharGen.OriginEdges
# pulls the standing modifiers into chips. So a +2 that reads one way in the book and another in
# the data is not a typo, it is the app handing a player a different character than the book
# describes.
#
# Three things are checked, and deliberately not a fourth. The names must match as a set; the
# printed Gift must be exactly the data's gifts; every trained skill the data grants must be named
# in the book's paragraph; and every signed modifier in the data's boon and burden must appear in
# the book's. What is NOT checked is that the two prose texts are identical, because they are not
# meant to be -- the data carries a terser form of the same rule, and demanding they match word for
# word would either fail on ten Origins that are correct today or force the book to write like a
# data file.
ORIGIN_RE = re.compile(r'<h3 id="ix-o-([a-z]+)">([^<]+)</h3>\s*<p>(.*?)</p>', re.S)
GIFT_RE = re.compile(r'([+−-])(\d+)\s+(STR|DEX|CON|WIT|RES|PRE)')
MOD_RE = re.compile(r'([+−-])(\d+)')


def _mods(text):
    """Signed modifiers as a sorted list, so two prose passages can be compared on their numbers."""
    return sorted(int(("-" if sign in "−-" else "") + n) for sign, n in MOD_RE.findall(text))


def check_origins(problems):
    d = json.loads((ROOT / "GK/rules/Data/chargen.json").read_text(encoding="utf-8"))
    origins = {o["name"]: o for o in d["origins"]}
    page = (ROOT / "blood-and-grit.html").read_text(encoding="utf-8")

    book = {}
    for slug, name, body in ORIGIN_RE.findall(page):
        book[html.unescape(name).strip()] = html.unescape(body)

    missing = set(origins) - set(book)
    extra = set(book) - set(origins)
    for n in sorted(missing):
        problems.append(f"Origin {n!r}: in chargen.json, no <h3> in the book")
    for n in sorted(extra):
        problems.append(f"Origin {n!r}: printed in the book, absent from chargen.json")

    checks = 0
    for name, o in origins.items():
        body = book.get(name)
        if body is None:
            continue

        # the three spans the entry is written in
        gift = body.split("Boon:")[0].split("Gift:")[-1]
        boon = body.split("Boon:")[-1].split("Burden:")[0] if "Boon:" in body else ""
        burden = body.split("Burden:")[-1] if "Burden:" in body else ""

        printed = {ab: int(n) * (-1 if sign in "−-" else 1)
                   for sign, n, ab in GIFT_RE.findall(gift)}
        checks += 1
        if printed != o["gifts"]:
            problems.append(f"Origin {name}: printed Gift {printed} != data gifts {o['gifts']}")

        for skill in o.get("trained", []) + o.get("trainedChoice", []):
            checks += 1
            # "Lore (Frontier)" is printed as "Lore (Frontier or Occult, your choice)", so the
            # words are what must be present, not the exact parenthesised form.
            if not all(w in body for w in re.findall(r"[A-Za-z]+", skill)):
                problems.append(f"Origin {name}: data trains {skill!r}, the book never names it")

        for half, text in (("boon", boon), ("burden", burden)):
            want = _mods(o.get(half, ""))
            checks += 1
            if not want:
                continue
            got = _mods(text)
            if any(w not in got for w in want):
                problems.append(f"Origin {name}: data {half} carries {want}, "
                                f"the printed {half} carries {got}")
    return checks

# ------------------------------------------------------------------- the nineteen Perks
# A Perk is the one thing a Calling alone does, printed as a band above its level table and typed
# into chargen.json so the app can sell the Calling in the picker the same way the page does. It is
# the third surface to be written twice (after the features and the Origins), so it gets the same
# treatment: the book is the source, and the two are held word for word. Unlike an Origin's boon,
# there is no reason for the data to carry a terser form -- one sentence is one sentence -- so this
# check is exact.

PERK_RE = re.compile(
    r'<h2 id="ix-c-[^"]*">(?P<cal>[^<]+)</h2>.*?'
    r'<p class="perk"><span class="lbl">Perk</span>'
    r'<span class="nm">(?P<name>.*?)\.</span>(?P<desc>.*?)</p>', re.S)

PREGEN_RE = re.compile(
    r'<h4>[^<]*(?:—|&mdash;)\s*([A-Za-z ]+?)\s*(?:·|&middot;)'
    r'.*?<strong>Perk:</strong>\s*([^<.]+)\.', re.S)


def check_perks(problems):
    d = json.loads((ROOT / "GK/rules/Data/chargen.json").read_text(encoding="utf-8"))
    page = (ROOT / "blood-and-grit.html").read_text(encoding="utf-8")

    book = {_tidy(m.group("cal")): (_tidy(TAG_RE.sub("", m.group("name"))),
                                    _prose(m.group("desc")))
            for m in PERK_RE.finditer(page)}
    d_by_name = {c["name"]: c for c in d["callings"]}

    checks = 0
    for c in d["callings"]:
        checks += 1
        perk = c.get("perk")
        printed = book.get(c["name"])
        if not perk or not perk.get("name") or not perk.get("desc"):
            problems.append(f"{c['name']}: chargen.json carries no Perk")
            continue
        if printed is None:
            problems.append(f"{c['name']}: the book prints no Perk band above its table")
            continue
        name, desc = printed
        if name != _tidy(perk["name"]):
            problems.append(f"{c['name']}: the book calls the Perk {name!r}, "
                            f"the data calls it {_tidy(perk['name'])!r}")
        said = _tidy(perk["desc"])
        if desc != said:
            at = next((i for i in range(min(len(desc), len(said))) if desc[i] != said[i]),
                      min(len(desc), len(said)))
            what = ("the app stops early" if desc.startswith(said) else
                    "the app runs past the book" if said.startswith(desc) else
                    "the wording differs")
            problems.append(f"{c['name']} / Perk: {what} at character {at} "
                            f"(book {len(desc)} chars, data {len(said)}); "
                            f"book: ...{desc[at:at + 70]!r}")

    for name in sorted(set(book) - {c["name"] for c in d["callings"]}):
        problems.append(f"{name}: a Perk is printed for a Calling chargen.json does not have")

    # Appendix D's six ready-made souls name their Perk on the same line as their features, which
    # is a second hand-typed copy of it and so a second place for it to drift.
    posse = page[page.index('id="posse"'):]
    named = PREGEN_RE.findall(posse)
    if len(named) != 6:
        problems.append(f"Appendix D: {len(named)} ready-made souls name a Perk, expected 6")
    for cal, perk in named:
        checks += 1
        cal = _tidy(cal)
        want = _tidy(((d_by_name.get(cal) or {}).get("perk") or {}).get("name") or "")
        if not want:
            problems.append(f"Appendix D: a soul is built as a {cal!r}, which is no Calling")
        elif _tidy(perk) != want:
            problems.append(f"Appendix D / {cal}: the pregen names the Perk {_tidy(perk)!r}, "
                            f"the Calling's is {want!r}")

    # two Callings sharing a Perk name means one of them was copied and not rewritten
    seen = {}
    for c in d["callings"]:
        n = _tidy((c.get("perk") or {}).get("name") or "")
        if n and n in seen:
            problems.append(f"{c['name']} and {seen[n]} both call their Perk {n!r}")
        seen[n] = c["name"]
    checks += 1
    return checks

# --------------------------------------------------- where the budget stops being arithmetic
# B4 measured that the encounter budget holds to Tier III and not past it, and the answer was to
# say so rather than retune anything: a Tier IV creature is a problem with an answer, not a fight
# with a bigger number. That statement now lives in FOUR places -- Keeper's Book Ch. IV, the
# Bestiary beside Threat by Tier, the Player's Book Ch. XI, and Rules.ArithmeticStopsAt, which the
# Encounter tab prints. Four copies of one rule is exactly the shape this project has been burned
# by, so all four are held together here.

CS_STOPS = re.compile(r"public const int ArithmeticStopsAt = (\d+);")


def check_arithmetic_stops(problems):
    src = (ROOT / "GK/rules/Core.cs").read_text(encoding="utf-8")
    m = CS_STOPS.search(src)
    if not m:
        problems.append("Core.cs: no ArithmeticStopsAt constant")
        return 0
    app = int(m.group(1))
    checks = 1

    # The books state it in Roman, because that is how a Tier is written in every one of them.
    roman = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}.get(app)
    if roman is None:
        problems.append(f"Core.cs: ArithmeticStopsAt is {app}, which is no Tier the books print")
        return checks

    # The Player's Book states the rule and must NOT name the Tier: "Tier" is Keeper vocabulary and
    # appears nowhere in that book, by design. Only the two Keeper-side books are held to the
    # number. This distinction was found by the check's own first run, which demanded a Tier in a
    # book that has never printed one.
    for book, where, names_tier in (
            ("keeper-handbook.html", "Where the arithmetic stops", True),
            ("bestiary.html", "the budget is honest to Tier", True),
            ("blood-and-grit.html", "Some Things You Do Not Shoot", False)):
        checks += 1
        text = _flat(book)
        if where not in text:
            problems.append(f"{book}: does not carry {where!r} — the Tier {roman} rule is unsaid here")
            continue
        if names_tier and f"Tier <strong>{roman}</strong>" not in text and f"Tier {roman}" not in text:
            problems.append(f"{book}: states the rule but never names Tier {roman}, "
                            f"which Core.cs's ArithmeticStopsAt is set to")
        if not names_tier and re.search(r"\bTier\s+[IVX]+", text):
            problems.append(f"{book}: prints a Tier, which is Keeper vocabulary this book "
                            f"has always kept out of the players' hands")
    return checks

# ------------------------------------------------------- the ninety-four Signs and Miracles
# The largest surface in the book with no guard on it at all, found on 2026-08-27 while adding
# eight workings: the Callings' features, their Perks, their paths, the arms table, Ch. IV's
# Origins and the encounter ladder were all held to the data, and the two chapters the game is
# named for were not. Every working is printed in the Player's Book and typed into chargen.json,
# and nothing compared them.
#
# It bit on its first run, on the entries this very session had written: eight workings were
# reworded in the data after the book entries were generated from them, and the book went on
# printing the earlier draft.
#
# Held: the Rank, the cost line, and the prose, word for word. There is no reason for the data to
# carry a terser form the way an Origin's boon does -- the book and the app print the same sentence
# to the same reader -- so this check is exact.

WORKING_RE = re.compile(
    r'<h3 id="ix-(?P<kind>[sm])-[^"]*">(?P<name>[^<]+)</h3>\s*'
    r'<p><em>Rank (?P<rank>\d+) · (?P<cost>[^<]*?)\.</em>(?P<desc>.*?)</p>', re.S)


def check_workings(problems):
    d = json.loads((ROOT / "GK/rules/Data/chargen.json").read_text(encoding="utf-8"))
    page = (ROOT / "blood-and-grit.html").read_text(encoding="utf-8")

    book = {}
    for m in WORKING_RE.finditer(page):
        book[_tidy(m.group("name"))] = (m.group("kind"), int(m.group("rank")),
                                        _tidy(m.group("cost")), _prose(m.group("desc")))

    checks = 0
    for kind, key in (("s", "signs"), ("m", "miracles")):
        for w in d[key]:
            checks += 1
            printed = book.get(_tidy(w["name"]))
            if printed is None:
                problems.append(f"{w['name']} ({key[:-1]}): in chargen.json, not printed in the book")
                continue
            bk, brank, bcost, bdesc = printed
            if bk != kind:
                problems.append(f"{w['name']}: printed as a {'Sign' if bk == 's' else 'Miracle'}, "
                                f"the data files it under {key}")
            if brank != w["rank"]:
                problems.append(f"{w['name']}: the book prints Rank {brank}, the data says {w['rank']}")
            if bcost != _tidy(w["cost"]):
                problems.append(f"{w['name']}: the book's cost line reads {bcost!r}, "
                                f"the data says {_tidy(w['cost'])!r}")
            said = _tidy(w["desc"])
            if bdesc != said:
                at = next((i for i in range(min(len(bdesc), len(said))) if bdesc[i] != said[i]),
                          min(len(bdesc), len(said)))
                what = ("the app stops early" if bdesc.startswith(said) else
                        "the app runs past the book" if said.startswith(bdesc) else
                        "the wording differs")
                problems.append(f"{w['name']}: {what} at character {at} "
                                f"(book {len(bdesc)} chars, data {len(said)}); "
                                f"book: ...{bdesc[at:at + 70]!r}")

    named = {_tidy(w["name"]) for w in d["signs"] + d["miracles"]}
    for name in sorted(set(book) - named):
        problems.append(f"{name}: printed as a working the app has never heard of")
    return checks

# ------------------------------------------------------------------ the fight ledger
# Added 2026-08-27 with the ledger itself. Each Calling prints what it does in a round and what
# it pays to do it, in a two-part band under the Perk. Both halves come from chargen.json so the
# app can show the same sentences, which means both halves can drift.

FIGHT_RE = re.compile(
    r'<p class="perk"><span class="lbl">Perk</span><span class="nm">(?P<perk>[^<]+)</span>.*?</p>\s*'
    r'<div class="fight">\s*'
    r'<div class="brings"><span class="k">In a fight</span>(?P<brings>.*?)</div>\s*'
    r'<div class="pays"><span class="k">You pay</span>(?P<pays>.*?)</div>', re.S)


def check_fight_ledger(problems):
    d = json.loads((ROOT / "GK/rules/Data/chargen.json").read_text(encoding="utf-8"))
    page = (ROOT / "blood-and-grit.html").read_text(encoding="utf-8")

    # keyed by the Perk name, which is what the band above it prints and is unique per Calling
    book = {_tidy(TAG_RE.sub("", m.group("perk"))).rstrip("."):
            (_prose(m.group("brings")), _prose(m.group("pays")))
            for m in FIGHT_RE.finditer(page)}

    checks = 0
    for c in d["callings"]:
        checks += 1
        fight = c.get("fight")
        if not fight or not fight.get("brings") or not fight.get("costs"):
            problems.append(f"{c['name']}: chargen.json carries no fight ledger")
            continue
        printed = book.get(_tidy(c["perk"]["name"]))
        if printed is None:
            problems.append(f"{c['name']}: the book prints no fight ledger under its Perk")
            continue
        for half, said in (("In a fight", fight["brings"]), ("You pay", fight["costs"])):
            got = printed[0 if half == "In a fight" else 1]
            want = _tidy(said)
            if got != want:
                at = next((i for i in range(min(len(got), len(want))) if got[i] != want[i]),
                          min(len(got), len(want)))
                what = ("the app stops early" if got.startswith(want) else
                        "the app runs past the book" if want.startswith(got) else
                        "the wording differs")
                problems.append(f"{c['name']} / {half}: {what} at character {at} "
                                f"(book {len(got)} chars, data {len(want)}); "
                                f"book: ...{got[at:at + 70]!r}")

    if len(book) != len(d["callings"]):
        problems.append(f"the book prints {len(book)} fight ledgers, "
                        f"chargen.json has {len(d['callings'])} Callings")

    # The ledger exists to be honest, so an all-praise entry is a fault the same way a missing one
    # is: a "You pay" half that names no actual cost has quietly become a second Perk.
    for c in d["callings"]:
        f = c.get("fight") or {}
        if f.get("costs") and len(f["costs"]) < 40:
            problems.append(f"{c['name']}: the 'You pay' half is too short to be an honest price")
    return checks

# ------------------------------------------------------------------ the Index, alphabetised
# 331 rows under 23 letter headings, and until 2026-08-27 nothing checked either that a row sat
# under its own letter or that the rows inside a letter were in order. Both had drifted.

IX_ITEM = re.compile(r'    <li(?P<hd> class="ix-hd")?>(?P<inner>.*?)</li>\n', re.S)


def _ix_text(inner):
    # the page number lives in a <span> inside the row; leaving it attached turns "Edges" into
    # "edges137" and manufactures inversions that are not there.
    t = re.sub(r'<span class="pg">.*?</span>', '', inner, flags=re.S)
    return re.sub(r'&[a-z]+;', '', re.sub(r'<[^>]+>', '', t)).strip()


def _ix_key(t):
    return re.sub(r'^(the|a|an)\s+', '', t.lower().strip()).lstrip('"“')


def check_index_order(problems):
    page = (ROOT / "blood-and-grit.html").read_text(encoding="utf-8")
    m = re.search(r'<ul class="ix">\n(.*?)  </ul>', page, re.S)
    if not m:
        problems.append("the Player's Book has no Index block")
        return 0

    letter, prev, checks = None, None, 0
    for it in IX_ITEM.finditer(m.group(1)):
        t = _ix_text(it.group("inner"))
        if it.group("hd"):
            letter, prev = t, None
            continue
        checks += 1
        k = _ix_key(t)
        if not k:
            continue
        if letter and k[0].upper() != letter.upper():
            problems.append(f"Index: {t!r} is printed under {letter}, "
                            f"and belongs under {k[0].upper()}")
        if prev is not None and prev > k:
            problems.append(f"Index, under {letter}: {prev!r} is printed before {k!r}")
        prev = k
    if checks < 300:
        problems.append(f"Index: only {checks} rows parsed, which is too few to be the whole of it")
    return checks


def main():
    data, book = load_data(), load_book()
    problems = []

    if len(book) != 19:
        problems.append(f"parsed {len(book)} attack tables from the book, expected 19")

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
    checks += check_origins(problems)
    checks += check_perks(problems)
    checks += check_arithmetic_stops(problems)
    checks += check_workings(problems)
    checks += check_fight_ledger(problems)
    checks += check_index_order(problems)
    if problems:
        print(f"DRIFT - {len(problems)} disagreement(s) between the book, the data, and the formula:")
        for p in problems[:40]:
            print("  " + p)
        return 1
    print(f"book <-> data <-> formula: in step across {len(data)} Callings, their feature "
          f"prose, their Perks, their fight ledgers, their 3rd-level paths, every Sign and "
          f"Miracle, the arms table, "
          f"Ch. IV's Origins, the Index's own alphabet, and its encounter budget across both books "
          f"({checks} cross-checks, 0 drift).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
