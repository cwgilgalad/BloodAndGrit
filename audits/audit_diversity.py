#!/usr/bin/env python3
"""audit_diversity.py — is every possibility the rules offer a possibility the game can reach?

The other audits ask whether the game is *correct*. This one asks whether it is as wide as it
claims. Those are different failures. A skill printed in the skill list that no Calling ever wants
and no Origin ever grants is not wrong — every number about it checks out — it is simply a door
with no corridor behind it. The reader spends attention on it and gets nothing back, and the day
somebody notices, what they have learned is that the list is padded. That is the fault this file
looks for, and the line it draws is deliberately narrow:

    **A thing fails here only when no path in the game can reach it.** Everything else is
    measured, printed, and left to a designer.

That second half matters as much as the first. "Enough variety" is a judgement — how many Callings
should share a chassis, how many monsters should answer to fire — and a checker that guesses at
the answer is a checker that fires on good design, gets argued with once, and is ignored forever
after. So the distributions below are reported with their numbers and never counted against the
exit code. They are here to be *read*: the Faith Callings sharing one spine is a fact worth
knowing before writing the sixth one, whether or not it is a fault today.

What it measures, and what can fail:

  1. SKILLS — every skill must be reachable: some Calling prefers it, or some Origin trains it.
     FAILS on an unreachable skill, because the app's builder can then never produce a character
     who has it and the printed list is longer than the game.
  2. CONDITIONS — every condition defined in Appendix B must be causable by something. FAILS on
     a condition that appears nowhere but its own definition. The app carries a toggle for all
     fifteen; a toggle for a state no rule inflicts is a control that can never legitimately be
     used.
  3. CALLING SPINES — the (group, hit die, attack rank, strong saves) chassis, and how many
     Callings share each. FAILS only where two Callings are identical in chassis AND resource
     pool AND Sign access, which would make them the same character with two names.
  4. CALLING-EDGES — every Calling must have at least one of its own. FAILS on a Calling with
     none, since its 3rd-level Edge slot would then draw from the general list alone.
  5. SIGNS AND MIRACLES — every list must reach rank 5. FAILS on a list that stops early: a
     caster who commits to it would climb to a ceiling nobody built.
  6. ORIGINS — every ability must be liftable by some Origin. FAILS on an ability no background
     can raise.
  7. EDGE GROUPS — every group must be wanted by some Calling, and every Calling must want more
     than one group. FAILS either way.
  8. THE BESTIARY'S SHAPE — creatures per Tier and per chapter, as a grid.
  9. DREAD — which chapters roll it and which do not, and whether the DC climbs with the Tier.
 10. THE WAYS A THING ENDS — how many distinct counters the Bestiary offers, and how often each.
 11. THE GROUNDS' REACH — what share of the Bestiary a Keeper can actually roll into.

Checks 8-11 report and never fail. They are the map, not the fence.

Usage:
    python audits/audit_diversity.py            # the measurements and the verdict
    python audits/audit_diversity.py --verbose  # and the names behind every number

Reads the built books and the app's data files. Read-only: writes nothing, ever.
"""
import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import extract_rules as X            # noqa: E402  the books as data

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FAILURES = []
COUNTED = [0]


def fail(what):
    FAILURES.append(what)
    print(f"    FAIL  {what}")


def ok(line):
    print(f"    ok    {line}")


def note(line):
    print(f"    note  {line}")


def bar(n, of, width=28):
    """A count as a proportion you can see. The histograms below are the point of half this file,
    and a column of bare integers is a column nobody reads twice."""
    filled = 0 if not of else round(width * n / of)
    return "█" * filled + "·" * (width - filled)


# ---------------------------------------------------------------- 1. skills


def check_skills(chargen):
    print("\nSkills — every one on the list reachable by some Calling or some Origin")
    skills = [s["name"] for s in chargen["skills"]]
    pref = collections.Counter()
    for c in chargen["callings"]:
        for s in c["skillPrefs"]:
            pref[s] += 1
    origin = collections.Counter()
    for o in chargen["origins"]:
        for s in o.get("trained", []) + o.get("trainedChoice", []):
            origin[s] += 1

    dead = [s for s in skills if not pref[s] and not origin[s]]
    COUNTED[0] += len(skills)
    for s in dead:
        fail(f'"{s}" is on the skill list and no Calling prefers it and no Origin trains it — '
             f"the builder can never produce a character who has it")
    if not dead:
        ok(f"all {len(skills)} skills reachable")
    thin = [s for s in skills if pref[s] + origin[s] == 1]
    if thin:
        note(f"reachable by exactly one path: {', '.join(thin)}")
    return skills, pref, origin


def report_skill_spread(skills, pref, origin, verbose):
    top = max(pref.values()) if pref else 1
    if verbose:
        for s in skills:
            print(f"        {s:<18}{bar(pref[s], top)} {pref[s]:>2} Calling(s)"
                  f"{'  +' + str(origin[s]) + ' Origin(s)' if origin[s] else ''}")
    else:
        ranked = sorted(skills, key=lambda s: -(pref[s] + origin[s]))
        note(f"most wanted: {', '.join(f'{s} ({pref[s]})' for s in ranked[:3])}; "
             f"least: {', '.join(f'{s} ({pref[s]})' for s in ranked[-3:])}")


# ---------------------------------------------------------------- 2. conditions


def check_conditions(dig, creatures, chargen, verbose):
    print("\nConditions — every one defined in Appendix B causable by something in the game")
    conds = []
    for _ch, _sec, tb in X.all_tables(dig["books"]["blood-and-grit.html"]):
        if tb["headers"][:1] == ["Condition"]:
            conds = [r[0] for r in tb["rows"]]
    if not conds:
        fail("Appendix B's condition table was not found — the check cannot run")
        return

    # Count raw occurrences across the built markup rather than the parsed prose: a condition
    # applied inside a stat-block table cell or a subpath's boon is applied just as surely as one
    # applied in a paragraph, and the parse drops the difference. One occurrence means the
    # glossary row and nothing else.
    books = {f: (ROOT / f).read_text(encoding="utf-8") for f in X.BOOKS if (ROOT / f).is_file()}
    data = json.dumps(creatures, ensure_ascii=False) + json.dumps(chargen, ensure_ascii=False)

    rows = []
    for c in conds:
        COUNTED[0] += 1
        pat = re.compile(r"\b" + re.escape(c.split()[0]) + r"\b")
        per = {f: len(pat.findall(src)) for f, src in books.items()}
        in_data = len(pat.findall(data))
        rows.append((c, per, in_data))
        elsewhere = sum(per.values()) - 1 + in_data       # -1 for its own Appendix B row
        if elsewhere <= 0:
            fail(f'"{c}" is defined in Appendix B and named nowhere else in any book, any stat '
                 f"block, or any Sign, Miracle or Edge — nothing in the game can inflict it")
    if not FAILURES:
        ok(f"all {len(conds)} conditions inflicted by something")

    by_creature = [c for c, _p, d in rows if d and re.search(
        r"\b" + re.escape(c.split()[0]) + r"\b", json.dumps(creatures, ensure_ascii=False))]
    note(f"{len(by_creature)} of {len(conds)} appear in a creature's stat block "
         f"({', '.join(by_creature)}) — the rest come from the players' side of the table")
    if verbose:
        print(f"        {'condition':<12}" + "".join(f"{f.split('-')[0][:6]:>8}" for f in books)
              + f"{'data':>7}")
        for c, per, d in rows:
            print(f"        {c:<12}" + "".join(f"{per[f]:>8}" for f in books) + f"{d:>7}")


# ---------------------------------------------------------------- 3-7. character options


def check_calling_spines(chargen, verbose):
    print("\nCallings — how many genuinely different chassis the seventeen are built on")
    callings = chargen["callings"]
    spine = collections.defaultdict(list)
    for c in callings:
        spine[(c["group"], c["hitDie"], c["attackRank"], c["strongSaves"])].append(c["name"])
    COUNTED[0] += len(callings)

    # Sharing a chassis is normal and often right; being the same character is not. The first
    # version of this stopped at chassis + pool + Sign access and called Marshal and Mountain Man
    # the same Calling, which is false to anyone who has played either — one runs a posse on a
    # reputation, the other sets traps forty miles from the nearest posse. What actually separates
    # two Callings is what they *do*, so the features they get at 1st level are part of the
    # fingerprint. A checker that fires on good design is a checker that gets ignored, and then it
    # is not a checker.
    def fingerprint(c):
        p = c.get("pool") or {}
        first = tuple(sorted(r["features"] for r in c["rows"] if r["level"] == 1)[0]) \
            if any(r["level"] == 1 for r in c["rows"]) else ()
        return (c["group"], c["hitDie"], c["attackRank"], c["strongSaves"],
                p.get("name"), p.get("formula"), bool(c.get("signsKnownAt")), first)

    dup = collections.defaultdict(list)
    for c in callings:
        dup[fingerprint(c)].append(c["name"])
    for names in dup.values():
        if len(names) > 1:
            fail(f"{' and '.join(names)} are identical in chassis, pool and Sign access — "
                 f"two names for one character")
    if not any(len(v) > 1 for v in dup.values()):
        ok(f"{len(callings)} Callings, {len(spine)} distinct chassis, "
           f"{len(dup)} distinct once pool and Signs are counted — no two the same")

    shared = sorted(((k, v) for k, v in spine.items() if len(v) > 1), key=lambda kv: -len(kv[1]))
    for k, names in shared:
        note(f"{len(names)} share the {k[0]} d{k[1]} / {k[2]} / {k[3]} chassis: "
             f"{', '.join(names)}")
    for grp in sorted({c["group"] for c in callings}):
        saves = sorted({c["strongSaves"] for c in callings if c["group"] == grp})
        if len(saves) == 1:
            note(f"every {grp} Calling has the same strong saves ({saves[0]}) — "
                 f"the group has one defensive shape")
    if verbose:
        for k, names in sorted(spine.items()):
            print(f"        {k[0]:<9} d{k[1]:<3}{k[2]:<11}{k[3]:<20}{', '.join(names)}")


def check_calling_edges(chargen):
    print("\nCalling-Edges — every Calling with something only it can take")
    per = collections.Counter(e.get("calling", "?") for e in chargen["callingEdges"])
    COUNTED[0] += len(chargen["callings"])
    missing = [c["name"] for c in chargen["callings"] if not per[c["name"]]]
    for m in missing:
        fail(f"{m} has no Calling-Edge of its own — its 3rd-level Edge draws from the general "
             f"list alone")
    if not missing:
        ok(f"{len(chargen['callingEdges'])} Calling-Edges across all "
           f"{len(chargen['callings'])} Callings")
    hi = [f"{k} ({v})" for k, v in per.most_common() if v > 1]
    if hi:
        note(f"more than one: {', '.join(hi)} — the rest have exactly one")


def check_powers(chargen, verbose):
    print("\nSigns and Miracles — every list climbing the whole way to rank 5")
    for kind in ("signs", "miracles"):
        grid = collections.defaultdict(collections.Counter)
        for s in chargen[kind]:
            grid[s["list"]][s["rank"]] += 1
        COUNTED[0] += len(grid) * 5
        holes = []
        for name, ranks in sorted(grid.items()):
            gap = [r for r in range(1, 6) if not ranks[r]]
            if gap:
                holes.append((name, gap))
        for name, gap in holes:
            fail(f'the {kind[:-1]} list "{name}" has nothing at rank '
                 f"{', '.join(str(g) for g in gap)} — a caster who commits to it climbs to a "
                 f"ceiling nobody built")
        if not holes:
            ok(f"{len(chargen[kind])} {kind} across {len(grid)} list(s), every list ranks 1-5")
        if verbose:
            for name, ranks in sorted(grid.items()):
                print(f"        {name:<14}" + "".join(f"r{r}:{ranks[r]:<4}" for r in range(1, 6)))


def check_origins(chargen):
    print("\nOrigins — every ability something in your past can have lifted")
    gifts = collections.Counter()
    for o in chargen["origins"]:
        for a, n in o["gifts"].items():
            gifts[a] += n
    abilities = ["STR", "DEX", "CON", "WIT", "RES", "PRE"]
    COUNTED[0] += len(abilities)
    dead = [a for a in abilities if not gifts[a]]
    for a in dead:
        fail(f"no Origin raises {a} — a background can never have made you strong in it")
    if not dead:
        ok(f"{len(chargen['origins'])} Origins raise all six abilities "
           f"({', '.join(f'{a} {gifts[a]}' for a in abilities)})")
    top, low = max(gifts.values()), min(gifts[a] for a in abilities)
    if top >= low * 3:
        hi = [a for a in abilities if gifts[a] == top]
        lo = [a for a in abilities if gifts[a] == low]
        note(f"the Origins lean hard: {'/'.join(hi)} gets {top} point(s) across the ten, "
             f"{'/'.join(lo)} gets {low}")


def check_edge_groups(chargen):
    print("\nEdge groups — every one wanted by some Calling, every Calling wanting more than one")
    groups = sorted({e["group"] for e in chargen["edges"]})
    wanted = collections.Counter()
    for c in chargen["callings"]:
        for g in c["edgePrefs"]:
            wanted[g] += 1
    COUNTED[0] += len(groups) + len(chargen["callings"])
    bad = False
    for g in groups:
        if not wanted[g]:
            bad = True
            fail(f'the "{g}" Edge group is wanted by no Calling — the builder never offers it')
    for c in chargen["callings"]:
        if len(c["edgePrefs"]) < 2:
            bad = True
            fail(f"{c['name']} wants only one Edge group — every build of it takes the same Edges")
    if not bad:
        counts = collections.Counter(e["group"] for e in chargen["edges"])
        ok(f"{len(chargen['edges'])} Edges in {len(groups)} groups "
           f"({', '.join(f'{g} {counts[g]}' for g in groups)}), each wanted by "
           f"{min(wanted[g] for g in groups)}-{max(wanted[g] for g in groups)} Callings")


# ---------------------------------------------------------------- 8-11. the Bestiary


def report_bestiary_shape(creatures):
    print("\nThe Bestiary's shape — what a Keeper has to reach for, and at which Tier")
    tiers = collections.Counter(c["tier"] for c in creatures)
    chapters = sorted({c["chapter"] for c in creatures})
    COUNTED[0] += 5
    for t in range(1, 6):
        if not tiers[t]:
            fail(f"no creature at Tier {t} — a whole band of the campaign has nothing in it")
    if all(tiers[t] for t in range(1, 6)):
        ok(f"{len(creatures)} creatures across {len(chapters)} chapters, all five Tiers filled")
    print(f"        {'chapter':<32}{'I':>4}{'II':>4}{'III':>4}{'IV':>4}{'V':>4}{'all':>6}")
    for ch in chapters:
        row = collections.Counter(c["tier"] for c in creatures if c["chapter"] == ch)
        print(f"        {ch:<32}" + "".join(f"{row[t]:>4}" for t in range(1, 6))
              + f"{sum(row.values()):>6}")
    print(f"        {'':<32}" + "".join(f"{tiers[t]:>4}" for t in range(1, 6))
          + f"{len(creatures):>6}")
    thin = [t for t in range(1, 6) if tiers[t] < len(creatures) / 20]
    if thin:
        note("thinnest bands: " + ", ".join(f"Tier {t} ({tiers[t]})" for t in thin)
             + " — the top of a campaign has the fewest things in it")


def report_dread(creatures):
    print("\nDread — which things are frightening, and whether the fear grows with the Tier")
    with_dc, without = [], []
    for c in creatures:
        (with_dc if re.search(r"DC\s*\d+", c.get("dread") or "") else without).append(c)
    COUNTED[0] += len(creatures)
    silent = [c["name"] for c in creatures if not (c.get("dread") or "").strip()]
    for s in silent:
        fail(f"{s} has no Dread line at all — the Keeper cannot tell whether to call for the roll")
    if not silent:
        ok(f"{len(with_dc)} of {len(creatures)} creatures roll Dread; the other {len(without)} "
           f"say in words why they do not")
    for ch in sorted({c["chapter"] for c in creatures}):
        n = [c for c in creatures if c["chapter"] == ch]
        have = sum(1 for c in n if re.search(r"DC\s*\d+", c.get("dread") or ""))
        print(f"        {ch:<32}{bar(have, len(n), 20)} {have:>3}/{len(n):<4}")
    meds = []
    for t in range(1, 6):
        v = sorted(int(m.group(1)) for c in creatures if c["tier"] == t
                   for m in [re.search(r"DC\s*(\d+)", c.get("dread") or "")] if m)
        meds.append(v[len(v) // 2] if v else None)
    shown = " -> ".join(str(m) for m in meds if m is not None)
    if all(a <= b for a, b in zip([m for m in meds if m], [m for m in meds if m][1:])):
        note(f"median Dread DC by Tier climbs and never falls back: {shown}")
    else:
        note(f"median Dread DC by Tier: {shown}")


# The families of answer the Bestiary actually offers. Grouped rather than listed word by word
# because "burn it", "fire", and "a pyre before dawn" are one lever at the table and three strings
# in the prose, and counting the strings would say the book is more varied than it plays.
COUNTERS = {
    "fire":       r"\bfire\b|\bburn|\bpyre\b|\bcremat|\bflame",
    "iron":       r"\biron\b",
    "silver":     r"\bsilver\b",
    "salt":       r"\bsalt\b",
    "sunlight":   r"\bsun\b|\bsunlight\b|\bdaylight\b|\bdawn\b",
    "water":      r"running water|\briver\b|\bdrown|\bstream\b",
    "burial":     r"\bbury\b|\bburied\b|\breinter|\bgrave\b",
    "the head":   r"\bbehead|sever the head|\bthe neck\b|\bdecapitat",
    "rite/word":  r"\brite\b|\bprayer\b|\bconsecrat|\bblessing\b|\bscripture\b|\bthe Word\b",
    "its name":   r"\bits (?:true )?name\b|\bname it\b|\bnaming\b",
    "plain lead": r"\bbullet|\blead\b|\bshoot|\bshot\b|\bgun\b",
    "a bargain":  r"\bbargain\b|\bterms\b|\bthe price\b|\bdebt\b",
    "waiting":    r"\boutliv|\bwait it out\b|\bstarve|\bit ends when\b",
}


def report_counters(creatures, verbose):
    print("\nThe ways a thing ends — how many answers the book gives, and how often each")
    hits = collections.Counter()
    per_creature = {}
    for c in creatures:
        blob = c.get("puttingItDown") or ""
        found = [k for k, pat in COUNTERS.items() if re.search(pat, blob, re.I)]
        per_creature[c["name"]] = found
        for k in found:
            hits[k] += 1
    COUNTED[0] += len(creatures)
    top = max(hits.values()) if hits else 1
    for k, _pat in sorted(COUNTERS.items(), key=lambda kv: -hits[kv[0]]):
        print(f"        {k:<12}{bar(hits[k], top)} {hits[k]:>3}")
    ok(f"{len(COUNTERS)} distinct answers offered across {len(creatures)} creatures; "
       f"a creature names {sum(len(v) for v in per_creature.values()) / len(creatures):.1f} "
       f"on average")
    lead = max(hits, key=lambda k: hits[k])
    if hits[lead] > len(creatures) / 3:
        note(f'"{lead}" answers {hits[lead]} of {len(creatures)} — it is the frontier\'s '
             f"first thought, which is right, but a table that reaches for it every time is "
             f"a table with one idea")
    for t in range(1, 6):
        fam = {k for c in creatures if c["tier"] == t for k in per_creature[c["name"]]}
        n = sum(1 for c in creatures if c["tier"] == t)
        print(f"        Tier {t}: {len(fam):>2} distinct answer(s) across {n:>3} creature(s)")
    if verbose:
        for name, found in sorted(per_creature.items()):
            if not found:
                print(f"        no named counter: {name}")


def report_grounds_reach(dig, creatures, verbose):
    print("\nThe Grounds' reach — how much of the Bestiary a Keeper can roll into")
    tables = collections.defaultdict(set)
    for ch, sec, tb in X.all_tables(dig["books"]["bestiary.html"]):
        if ch != "Appendix: The Grounds" or "Sign & Spoor" in sec:
            continue
        for row in tb["rows"]:
            for cell in row:
                m = re.match(r"(.+?)\s*\((I{1,3}|IV|V)(?:[–-](I{1,3}|IV|V))?\)", cell or "")
                if m:
                    tables[sec].add(m.group(1).strip())
    names = {c["name"] for c in creatures}
    reach = set().union(*tables.values()) if tables else set()
    COUNTED[0] += len(names)
    ok(f"{len(tables)} terrain tables put {len(reach & names)} of {len(names)} creatures "
       f"({100 * len(reach & names) // max(len(names), 1)}%) within a die roll")
    orphan = sorted(names - reach)
    by_ch = collections.Counter(next(c["chapter"] for c in creatures if c["name"] == n)
                                for n in orphan)
    for ch, n in by_ch.most_common():
        total = sum(1 for c in creatures if c["chapter"] == ch)
        print(f"        {ch:<32}{bar(n, total, 20)} {n:>3}/{total:<4} off every table")
    note(f"{len(orphan)} creatures appear on no terrain table — they are reachable by a Keeper "
         f"who goes looking, never by one who rolls")
    if verbose:
        for n in orphan:
            print(f"        off-table: {n}")


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verbose", action="store_true",
                    help="print the names behind every count")
    args = ap.parse_args()

    dig = X.digest(root=ROOT)
    if dig["missing"]:
        print(f"not built: {', '.join(dig['missing'])} — build the books first")
        return 1
    chargen = json.loads((ROOT / "GK/rules/Data/chargen.json").read_text(encoding="utf-8"))
    creatures = json.loads((ROOT / "GK/rules/Data/creatures.json").read_text(encoding="utf-8"))

    print("Is every possibility the rules offer a possibility the game can reach?")
    skills, pref, origin = check_skills(chargen)
    report_skill_spread(skills, pref, origin, args.verbose)
    check_conditions(dig, creatures, chargen, args.verbose)
    check_calling_spines(chargen, args.verbose)
    check_calling_edges(chargen)
    check_powers(chargen, args.verbose)
    check_origins(chargen)
    check_edge_groups(chargen)
    report_bestiary_shape(creatures)
    report_dread(creatures)
    report_counters(creatures, args.verbose)
    report_grounds_reach(dig, creatures, args.verbose)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} dead option(s) across {COUNTED[0]:,} checks. Something printed "
              f"as a choice that no path in the game can reach is a promise the book does not "
              f"keep — cut it, or build the corridor behind the door.")
        return 1
    print(f"every option the rules print is an option some path reaches ({COUNTED[0]:,} checks). "
          f"The distributions above are for reading, not for passing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
