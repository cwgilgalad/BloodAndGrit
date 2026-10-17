#!/usr/bin/env python3
"""audit_playtest.py: is PLAYTEST.md what the engine actually says today?

Every difficulty number printed in the three module books comes out of `GK/playtest` and nowhere
else, by way of `PLAYTEST.md`: `modules_common.night_costs()` reads that file at build time and
generates each *What the Night Costs* table from it. That is the right architecture (one source,
generated outward) and it has exactly one hole, which is that **nothing re-runs the harness**.

The hole cost three releases. On 2026-08-27 the B5 pass added *Not While I Stand*, a Rank 2
Common Blessing. A 3rd-level Preacher draws from Ranks 1 and 2, so the new Miracle entered the
harness posse's eligible pool and shifted every draw after it. The harness is seeded and
deterministic, so this was not noise: from that commit on, `PLAYTEST.md` recorded a night that no
engine in the repo would play. Modules v1.4, v1.5 and v1.6 all shipped a *What the Night Costs*
table for *A Face Not His Own* claiming a Tier III fight had been cleared once in nine runs, when
the engine's answer was never.

Nothing went red. `audit_names.py` checks that `PLAYTEST.md` has a section per module and that the
titles match, which is a different question. The books measured clean, the rules cross-check
passed, and the number a Keeper reads when deciding whether to run a night for a fresh posse was
simply wrong.

So: run the harness, and hold the file to it. The run is deterministic under a fixed base seed, so
a difference is always a real difference. Either the engine moved and the file did not, or
somebody edited a generated file by hand.

The harness is only as honest as the night it is handed, and that hole stood open for weeks. The
ladder pass (d8e3286) repriced every Dread line the modules print, and every Dread beat in
`GK/playtest/Adventures.cs` stayed on its old number: Module I's Pell place printed DC 13 and 1d4
while the harness rolled DC 16 for 1 Nerve, and its scene 6 priced a third check the harness never
rolled at all. A seeded, reproducible run of the wrong night is still the wrong night. So before the
harness runs, and without dotnet, this reads the Dread beats out of Adventures.cs and the Dread lines
out of the three built modules and fails on any difference in count, order, DC or die. The die is
read through `Rules.NerveLoss` in `GK/rules/Core.cs`, so the ladder is not typed a second time. It
also reads the line PLAYTEST.md keeps of the Dread Checks it was played on, so a file played on
other beats shows as stale without a harness run.

Usage:
    python audits/audit_playtest.py               # Dread beats, then re-run and compare; exit 1 on drift
    python audits/audit_playtest.py --write        # re-run and update PLAYTEST.md, then check the beats
    python audits/audit_playtest.py --dread-only   # only the Dread check: no dotnet, instant
"""
import difflib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
TRACKED = ROOT / "PLAYTEST.md"
ADVENTURES = ROOT / "GK/playtest/Adventures.cs"
CORE = ROOT / "GK/rules/Core.cs"

# The modules print their Dread lines in one shape, and the act notes are counted with the same
# pattern. Reading the books with it means the audit and the builders cannot disagree about what a
# Dread line is.
sys.path.insert(0, str(ROOT))
from modules_common import DREAD_LINE, DREAD_ANY  # noqa: E402


def nerve_ladder():
    """Rules.NerveLoss's switch, read out of Core.cs, as a function from rung to the die it names."""
    src = CORE.read_text(encoding="utf-8")
    m = re.search(r"NerveLoss\(int tier\)\s*=>\s*tier switch\s*\{(.*?)\};", src, re.S)
    arms = re.findall(r"(<=\s*\d+|\d+|_)\s*=>\s*\(\"([^\"]+)\"", m.group(1)) if m else []
    if not arms:
        raise SystemExit("FAIL: Rules.NerveLoss is no longer a switch this audit can read in GK/rules/Core.cs.")

    def die(rung):
        for arm, label in arms:
            if arm == "_" or (arm.startswith("<=") and rung <= int(arm[2:].strip())) \
                    or (arm.isdigit() and rung == int(arm)):
                return label
        return f"rung {rung}"
    return die


def harness_dread():
    """Each adventure's Dread beats in Adventures.cs, in play order: {slug: (title, [(name, dc, rung)])}."""
    src = ADVENTURES.read_text(encoding="utf-8")
    heads = list(re.finditer(r'public static readonly Adventure \w+ = new\(\s*"([a-z0-9-]+)",\s*"([^"]+)"', src))
    out, unread = {}, []
    for i, h in enumerate(heads):
        body = src[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(src)]
        beats = re.findall(r'new\s+Beat\(\s*BeatKind\.Dread\s*,\s*"([^"]*)"\s*,\s*'
                           r'DreadDc:\s*(\d+)\s*,\s*DreadTier:\s*(\d+)', body)
        if len(beats) != body.count("BeatKind.Dread"):
            unread.append(h.group(2))
        out[h.group(1)] = (h.group(2), [(n, int(dc), int(t)) for n, dc, t in beats])
    return out, unread


def played_dread(md, title):
    """The Dread Checks PLAYTEST.md says it was played on, under `## title`, or None if it never says."""
    m = re.search(r"^## " + re.escape(title) + r"\s*$(.*?)(?=^## |\Z)", md, re.M | re.S)
    line = m and re.search(r"^- Dread Checks played, in order: (.*)$", m.group(1), re.M)
    if not line:
        return None
    return [(int(dc), loss) for dc, loss in re.findall(r"DC (\d+) \(lose ([^)\s]+)\)", line.group(1))]


def check_dread() -> bool:
    """Hold Adventures.cs's Dread beats to the Dread lines the built modules print, and PLAYTEST.md's
    record to Adventures.cs. Needs the three modules built; needs no dotnet."""
    die = nerve_ladder()
    adventures, unread = harness_dread()
    drift, stale = [], []
    for title in unread:
        drift.append(f"{title}: a Dread beat in Adventures.cs is not in the shape "
                     f"'new Beat(BeatKind.Dread, \"...\", DreadDc: N, DreadTier: T' and was not read")
    md = TRACKED.read_text(encoding="utf-8") if TRACKED.exists() else ""
    total = 0
    for slug, (title, beats) in adventures.items():
        book = ROOT / f"module-{slug}.html"
        if not book.exists():
            drift.append(f"{title}: {book.name} is not built; run build_module_*.py first")
            continue
        html = book.read_text(encoding="utf-8")
        printed = [(int(dc), loss) for dc, loss in DREAD_LINE.findall(html)]
        if len(printed) != len(DREAD_ANY.findall(html)):
            drift.append(f"{title}: {book.name} prints a Dread line outside the ladder's shape "
                         f"('<strong>Dread Check, DC N, Will save.</strong> Lose X Nerve')")
        played = [(dc, die(t)) for _n, dc, t in beats]
        total += len(printed)
        for i in range(max(len(played), len(printed))):
            h = played[i] if i < len(played) else None
            b = printed[i] if i < len(printed) else None
            if h == b:
                continue
            name = beats[i][0] if i < len(beats) else None
            said_h = f"DC {h[0]}, lose {h[1]}" if h else "nothing"
            said_b = f"DC {b[0]}, lose {b[1]}" if b else "nothing"
            drift.append(f"{title}, Dread Check {i + 1}: the module prints {said_b}; "
                         f"the harness rolls {said_h}" + (f" ('{name}')" if name else ""))
        recorded = played_dread(md, title)
        if recorded is None:
            stale.append(f"{title}: PLAYTEST.md does not say which Dread Checks it was played on")
        elif recorded != played:
            stale.append(f"{title}: PLAYTEST.md was played on "
                         + (" · ".join(f"DC {dc} (lose {x})" for dc, x in recorded) or "no Dread Checks")
                         + "; Adventures.cs now holds "
                         + " · ".join(f"DC {dc} (lose {x})" for dc, x in played))
    if drift:
        print(f"FAIL: the harness and the modules disagree on {len(drift)} Dread Check(s).")
        print("The harness has to play the night the Keeper is told to run, or its numbers describe")
        print("some other night.\n")
        for line in drift:
            print("  " + line)
        print("\nFix: put the beat in GK/playtest/Adventures.cs on the module's printed DC and die (or")
        print("print the line the beat plays), then python audits/audit_playtest.py --write.")
    else:
        print(f"OK: every Dread beat in Adventures.cs is a Dread line the modules print "
              f"({total} across {len(adventures)} modules, same order, same DC, same die).")
    if stale:
        print(f"FAIL: PLAYTEST.md is stale on the Dread Checks it was played on ({len(stale)} of "
              f"{len(adventures)} modules).")
        for line in stale:
            print("  " + line)
        print("Fix: python audits/audit_playtest.py --write, then rebuild the three modules.")
    return not drift and not stale


def run_harness(out: Path) -> bool:
    """Play all three adventures on the current rules library, into `out`."""
    r = subprocess.run(
        ["dotnet", "run", "--project", str(ROOT / "GK/playtest"), "--", "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not out.exists():
        print("FAIL: the playtest harness did not run.")
        print((r.stderr or r.stdout or "").strip()[-2000:])
        return False
    return True


def main() -> int:
    write = "--write" in sys.argv
    if not TRACKED.exists():
        print(f"FAIL: {TRACKED.name} is missing; the modules build their cost tables from it.")
        return 1
    if "--dread-only" in sys.argv:
        return 0 if check_dread() else 1

    # Compare mode checks the beats first: a harness run of the wrong night proves nothing. Write
    # mode regenerates first, so the record it checks is the one it has just written.
    beats_ok = True if write else check_dread()

    with tempfile.TemporaryDirectory() as td:
        fresh = Path(td) / "PLAYTEST.md"
        if not run_harness(fresh):
            return 1
        new = fresh.read_text(encoding="utf-8")

    old = TRACKED.read_text(encoding="utf-8")
    if old == new:
        print(f"OK: PLAYTEST.md is what the engine plays today "
              f"({len(old.splitlines())} lines, reproduced exactly).")
        return 0 if beats_ok and (not write or check_dread()) else 1

    if write:
        TRACKED.write_text(new, encoding="utf-8", newline="")
        print("PLAYTEST.md rewritten from the harness. Rebuild the three modules: "
              "their What the Night Costs tables are generated from it.")
        return 0 if check_dread() else 1

    diff = list(difflib.unified_diff(old.splitlines(), new.splitlines(),
                                     "PLAYTEST.md (committed)", "the engine, just now",
                                     lineterm="", n=1))
    print(f"FAIL: PLAYTEST.md disagrees with the engine ({sum(1 for d in diff if d[:1] in '+-' and d[:2] not in ('++', '--'))} lines).")
    print("\nEvery difficulty number in the three module books is generated from this file, so a")
    print("stale copy prints stale numbers into three shipped books and nothing else notices.\n")
    for line in diff[:60]:
        print("  " + line)
    if len(diff) > 60:
        print(f"  … {len(diff) - 60} more diff lines")
    print("\nFix: python audits/audit_playtest.py --write, then rebuild the three modules.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
