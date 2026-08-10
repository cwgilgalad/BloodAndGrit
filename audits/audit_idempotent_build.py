#!/usr/bin/env python3
"""Building twice must yield byte-identical output.

This check existed only as eleven lines of shell inside .github/workflows/verify.yml,
which meant it could not be run by hand without reading the YAML and retyping it, and
it could not be reviewed as code. It is a file now, like every other check.

WHAT IT PROVES

A builder that is not idempotent hides a real defect: something in it depends on the
clock, on dict ordering, on a file it wrote last time, or on the machine. That kind of
build produces a diff on every run, so `git diff --exit-code` becomes noise, so nobody
reads it, so a genuine stale-book change sails through. Idempotence is what makes the
built-vs-committed check below it mean anything.

BUILD ORDER IS LOAD-BEARING

blood-and-grit.html (the Player's Book) is the shared shell. The Keeper's Book, the
Bestiary and all three modules read it. Build them out of order and you are hashing a
book built against the previous shell -- which is a different failure wearing this
one's clothes.

WHAT IT COSTS

Six book builds twice over, plus the maps. Minutes, not seconds. That is the reason it
is not something to run casually, and the reason it is worth having as its own file:
you can run the cheap checks without paying for this one.

    python audits/audit_idempotent_build.py            # from the repo root
    python audits/audit_idempotent_build.py --keep     # leave the rebuilt files in place

Exit 0 if every artifact hashed the same twice, 1 otherwise.
"""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# In dependency order. The Player's Book first, always: it is the shell the rest read.
BUILDERS = [
    "build_player.py",
    "build_keeper.py",
    "build_bestiary.py",
    "module_maps.py",
    "build_module_salt.py",
    "build_module_face.py",
    "build_module_water.py",
]

ARTIFACTS = ("*.html", "*.svg")


def build_all() -> bool:
    """Run every builder in order. False on the first one that fails."""
    for b in BUILDERS:
        script = ROOT / b
        if not script.is_file():
            print(f"  MISSING BUILDER: {b}")
            return False
        r = subprocess.run([sys.executable, str(script)], cwd=ROOT,
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  BUILD FAILED: {b} (exit {r.returncode})")
            tail = (r.stderr or r.stdout or "").strip().splitlines()[-12:]
            for line in tail:
                print(f"      {line}")
            return False
        print(f"  built {b}")
    return True


def snapshot() -> dict:
    """sha256 of every built artifact, keyed by name."""
    out = {}
    for pattern in ARTIFACTS:
        for f in sorted(ROOT.glob(pattern)):
            out[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keep", action="store_true",
                    help="do not warn about leaving rebuilt files in the working tree")
    args = ap.parse_args()

    print("PASS 1")
    if not build_all():
        return 1
    first = snapshot()
    if not first:
        print("  NOTHING TO HASH: no .html or .svg was produced. Something is wrong.")
        return 1
    print(f"  {len(first)} artifact(s) hashed")

    print("\nPASS 2")
    if not build_all():
        return 1
    second = snapshot()
    print(f"  {len(second)} artifact(s) hashed")

    print()
    added = sorted(set(second) - set(first))
    gone = sorted(set(first) - set(second))
    differ = sorted(n for n in set(first) & set(second) if first[n] != second[n])

    for n in added:
        print(f"  APPEARED ONLY ON THE SECOND BUILD: {n}")
    for n in gone:
        print(f"  VANISHED ON THE SECOND BUILD: {n}")
    for n in differ:
        print(f"  NOT IDEMPOTENT: {n}")
        print(f"      first  {first[n][:16]}")
        print(f"      second {second[n][:16]}")

    bad = len(added) + len(gone) + len(differ)
    if bad:
        print(f"\nFAIL: {bad} artifact(s) did not survive being built twice.")
        print("Something in a builder depends on the clock, the filesystem, or its own")
        print("previous output. Find it before trusting any diff of the built books.")
        return 1

    print(f"OK: all {len(first)} artifacts are byte-identical across two builds.")
    if not args.keep:
        print("\nNote: the books in your working tree have just been rebuilt. That is")
        print("normally a no-op, but `git status` will show them if anything drifted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
