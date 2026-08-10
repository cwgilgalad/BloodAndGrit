#!/usr/bin/env python3
"""The built books in the working tree must match what is committed.

This was one line of shell inside .github/workflows/verify.yml:

    git diff --exit-code -- '*.html' '*.svg'

It is a file now, for the same reason as its neighbour: a check nobody can run by
name is a check nobody runs.

WHAT IT CATCHES

A build script edited without rebuilding. The repo's HTML then describes the book as
it was, while build_player.py describes the book as it is meant to be -- and the two
never argue out loud, because nothing reads both. It matters more here than in most
projects: the PDFs are printed from the built HTML, and the app's creature data is
extracted from the built Bestiary. A stale build propagates into two other artifacts
and looks fine in all three.

The honest way to use it is right after audits/audit_idempotent_build.py, which
rebuilds everything. Run in that order the pair reads: "rebuilding changes nothing,
and what is committed is what a rebuild produces." Run alone, this only tells you
whether your working tree is clean -- worth knowing, but a smaller claim.

    python audits/audit_built_matches_committed.py       # from the repo root
    python audits/audit_built_matches_committed.py --stat

Exit 0 if no built artifact differs from its committed copy, 1 otherwise.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The generated artifacts, and only those. Sources are excluded on purpose: an
# uncommitted edit to a builder is normal mid-session and is not this check's business.
PATHSPECS = ["*.html", "*.svg"]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stat", action="store_true", help="show a diffstat for each file")
    args = ap.parse_args()

    probe = git("rev-parse", "--is-inside-work-tree")
    if probe.returncode != 0:
        print("NOT A GIT CHECKOUT: nothing to compare against.")
        return 1

    # Staged and unstaged both. `git diff` alone misses a built book that was
    # rebuilt and then `git add`-ed without being committed -- which is exactly the
    # state a half-finished session leaves behind.
    changed = set()
    for extra in ([], ["--cached"]):
        r = git("diff", *extra, "--name-only", "--", *PATHSPECS)
        if r.returncode != 0:
            print("git diff failed:")
            print((r.stderr or "").strip())
            return 1
        changed.update(n for n in r.stdout.splitlines() if n.strip())

    # A brand-new built artifact that was never committed is the same failure wearing
    # different clothes: the repo does not carry the book it claims to.
    r = git("ls-files", "--others", "--exclude-standard", "--", *PATHSPECS)
    untracked = sorted(n for n in r.stdout.splitlines() if n.strip())

    if not changed and not untracked:
        print("OK: every built .html and .svg matches its committed copy.")
        return 0

    for n in sorted(changed):
        print(f"  STALE OR UNCOMMITTED: {n}")
        if args.stat:
            d = git("diff", "--stat", "--", n).stdout.strip()
            for line in d.splitlines():
                print(f"      {line}")
    for n in untracked:
        print(f"  BUILT BUT NEVER COMMITTED: {n}")

    total = len(changed) + len(untracked)
    print(f"\nFAIL: {total} built artifact(s) differ from what is committed.")
    print("Either a builder was edited without rebuilding, or a rebuild was not")
    print("committed. Rebuild, look at the diff, and commit it with the change that")
    print("caused it -- the built books are part of the deliverable, not a by-product.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
