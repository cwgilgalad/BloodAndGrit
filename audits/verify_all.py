#!/usr/bin/env python3
"""Run the checks in `audits/` from one place, and say plainly what passed.

**Why this is a script and not a slash command.** A slash command runs when somebody types it,
inside Claude Code. This has to run for Cole at a prompt, for CI, for a git hook, and for Claude
alike — a verification entry point that only works when one particular tool is driving is the first
thing in this repo that stops working the day that tool is not. A `/verify` wrapper that shells out
to this is fine; it just is not the substance.

**It re-implements nothing.** Every check is still its own file with its own reasons written at the
top, and this runs those files as subprocesses and collects their exit codes. There is exactly one
copy of every check, which is the same rule the rest of the project lives by. Adding a check means
adding a file to `audits/` and a row to `CHECKS` below, and `--list` will then show it.

    python audits/verify_all.py                # the read-only checks: nothing slow, nothing writes
    python audits/verify_all.py --quick        # the instant ones only
    python audits/verify_all.py --app          # ... and build, the smoke suite, the self-test
    python audits/verify_all.py --full         # ... and the ones that rebuild or take minutes
    python audits/verify_all.py --release      # everything, which is the gate /ship reads
    python audits/verify_all.py --list         # what would run, and in what order

Exit code 0 means every check that can fail did not. **Advisory checks never affect it** —
`audit_whitespace.py` measures page gaps and a Keeper decides whether a gap is a fault, so it is
reported and never counted. Nothing here is a substitute for reading the output: a check that
passes still prints the number it passed on, and those numbers are how drift gets noticed early.

**One ordering matters.** `audit_idempotent_build.py` then `audit_built_matches_committed.py`,
because together they say *rebuilding changes nothing, and what is committed is what a rebuild
produces*, and either alone says much less. `CHECKS` is in run order for that reason.
"""
import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Windows hands a bare console cp1252, and half these checks report in prose full of em dashes and
# arrows. Printing one killed the run at check nine on the first --release, past the point where a
# reader would have believed the earlier oks. Reconfigure rather than sanitise at each print: the
# characters are the point, and a summary that silently drops them is a summary to distrust.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

INSTANT, SECONDS, SLOW = "instant", "seconds", "slow"

# name, script + args, tier, writes?, advisory?, one line of what it answers
CHECKS = [
    ("rules",     ["verify_rules.py"],                 INSTANT, False, False,
     "the printed books, chargen.json and the spine formula are one"),
    ("release",   ["verify_release.py"],               INSTANT, False, False,
     "one version everywhere, and every past release actually cut"),
    ("ui",        ["audit_ui.py"],                     INSTANT, False, False,
     "every control wired, tipped, hittable and never silent"),
    ("names",     ["audit_names.py"],                  INSTANT, False, False,
     "no two modules share a name, and the docs name files that exist"),
    ("maps",      ["audit_maps.py"],                   INSTANT, False, False,
     "every map agrees with its module, and reads as cartography"),
    ("consistency", ["audit_consistency.py"],          INSTANT, False, False,
     "the Keeper-side rules read the same in every book and in the app"),
    ("diversity", ["audit_diversity.py"],              INSTANT, False, False,
     "every option the rules print is one some path can reach"),
    ("prose",     ["audit_ai_tells.py", "--commits"],  SECONDS, False, False,
     "the repo's own prose reads as written rather than generated"),
    # These two are a pair and this is the order: rebuild, then compare against what is committed.
    ("idempotent", ["audit_idempotent_build.py"],      SLOW,    True,  False,
     "building twice yields byte-identical output"),
    ("committed", ["audit_built_matches_committed.py"], INSTANT, False, False,
     "every built file in the tree matches its committed copy"),
    ("whitespace", ["audit_whitespace.py"],            SLOW,    False, True,
     "per-page bottom gaps, for a human to judge"),
    # Added 2026-08-27. The Player's Book shipped with its Contents five pages out at the back:
    # B5 added eleven pages, the book was rebuilt, and measure_index.py -- the only thing that
    # re-derives those numbers from the rendered page -- was not re-run. It lives at the repo root
    # rather than in audits/ because its normal mode patches build_player.py; --check is the
    # read-only half. Never in CI: pagination is environment-dependent and a cloud runner measures
    # a different page count than the laptop the books are proofed on.
    ("statics",   ["../measure_index.py", "--check"],  SLOW,    False, False,
     "the Player's printed Contents and Index page numbers are the true ones"),
]

BOOKS = ["blood-and-grit.html", "keeper-handbook.html", "bestiary.html",
         "module-salt-at-coffin-wells.html", "module-a-face-not-his-own.html",
         "module-what-the-water-answers.html"]


def run(label, cmd, cwd=None):
    """One check. Returns (label, ok, seconds, tail) and streams nothing — the tail is what a
    reader wants when it passed, and the whole output is what they want when it did not."""
    t0 = time.monotonic()
    p = subprocess.run(cmd, cwd=str(cwd or ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    secs = time.monotonic() - t0
    out = ((p.stdout or "") + (p.stderr or "")).rstrip()
    return label, p.returncode == 0, secs, out


def verdict_line(out):
    """The line a check ends on that carries its numbers.

    Not simply the last line: `audit_idempotent_build.py` signs off with "OK: all 9 artifacts are
    byte-identical" and then adds a two-line Note about having rebuilt the books, so the naive
    answer reported the footnote and hid the verdict. Everything from the first `Note:` onward is
    an aside by convention in this directory, so it is dropped before looking.
    """
    lines = out.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("Note:"):
            lines = lines[:i]
            break
    return next((ln.strip() for ln in reversed(lines) if ln.strip()), "")


def build_plan(args):
    """What will run, in order, as a list of (label, argv, cwd, advisory, note)."""
    tiers = {INSTANT}
    if not args.quick:
        tiers.add(SECONDS)
    if args.full or args.release:
        tiers.add(SLOW)

    plan = []
    for name, argv, tier, writes, advisory, note in CHECKS:
        if tier not in tiers:
            continue
        if writes and not (args.full or args.release):
            continue
        argv = list(argv)
        if name == "prose":
            argv.append(str(args.commits))
        if name == "release" and args.delivered:
            argv.append("--delivered")
        if name == "whitespace":
            # It takes one filename, so it is really six runs. Fold them into one label.
            for book in BOOKS:
                plan.append((f"whitespace:{book.split('.')[0][:22]}",
                             [sys.executable, str(ROOT / "audits" / argv[0]), book],
                             ROOT, advisory, note))
            continue
        plan.append((name, [sys.executable, str(ROOT / "audits" / argv[0])] + argv[1:],
                     ROOT, advisory, note))

    if args.app or args.release:
        dotnet = shutil.which("dotnet") or r"C:\Program Files\dotnet\dotnet.exe"
        exe = ROOT / "GK/source/bin/Release/net10.0-windows/win-x64/GritKeeper.exe"
        plan.append(("build", [dotnet, "build", "-c", "Release", "-warnaserror"],
                     ROOT / "GK/source", False, "0 warnings, 0 errors"))
        plan.append(("smoke", [dotnet, "run", "-c", "Release"],
                     ROOT / "GK/smoke", False, "the headless logic suite"))
        plan.append(("selftest", [str(exe), "--selftest"],
                     ROOT, False, "every tab, every wizard step, every Calling"))
    return plan


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true",
                    help="the instant checks only; skips the prose scan")
    ap.add_argument("--app", action="store_true",
                    help="also build the app, run the smoke suite and the self-test")
    ap.add_argument("--full", action="store_true",
                    help="also the slow ones, including the rebuild-and-compare pair")
    ap.add_argument("--release", action="store_true",
                    help="everything: --full --app --delivered. What /ship reads.")
    ap.add_argument("--delivered", action="store_true",
                    help="have the release check also read the packaged exe (local only)")
    ap.add_argument("--commits", type=int, default=40,
                    help="how many commit messages the prose scan reads (default 40)")
    ap.add_argument("--list", action="store_true", help="print the plan and stop")
    args = ap.parse_args()
    if args.release:
        args.delivered = True

    plan = build_plan(args)
    if args.list:
        print(f"{len(plan)} check(s) would run, in this order:\n")
        for label, argv, cwd, advisory, note in plan:
            flag = "  (advisory)" if advisory else ""
            print(f"  {label:<26} {note}{flag}")
        return 0

    print(f"verify_all: {len(plan)} check(s)\n")
    results, failed, advisory_failed = [], [], []
    for label, argv, cwd, advisory, note in plan:
        label, ok, secs, out = run(label, argv, cwd)
        results.append((label, ok, secs, advisory))
        mark = "ok  " if ok else ("note" if advisory else "FAIL")
        tail = verdict_line(out)
        print(f"  {mark}  {label:<26} {secs:6.1f}s  {tail[:96]}")
        if not ok:
            (advisory_failed if advisory else failed).append((label, out))

    print()
    for label, out in failed:
        print("=" * 78)
        print(f"FAILED — {label}")
        print("=" * 78)
        print(out)
        print()

    total = sum(r[2] for r in results)
    counted = [r for r in results if not r[3]]
    passed = sum(1 for r in counted if r[1])
    line = f"{passed}/{len(counted)} counted check(s) passed in {total:.0f}s"
    if advisory_failed:
        line += f"; {len(advisory_failed)} advisory check(s) had something to say"
    print(line)
    if failed:
        print("Read the output above. Nothing here is a lint — every one of these was written "
              "because something got past the others.")
        return 1
    print("Green. This is not permission to skip reading the numbers above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
