#!/usr/bin/env python3
"""audit_playtest.py — is PLAYTEST.md what the engine actually says today?

Every difficulty number printed in the three module books comes out of `GK/playtest` and nowhere
else, by way of `PLAYTEST.md`: `modules_common.night_costs()` reads that file at build time and
generates each *What the Night Costs* table from it. That is the right architecture — one source,
generated outward — and it has exactly one hole, which is that **nothing re-runs the harness**.

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
a difference is always a real difference — either the engine moved and the file did not, or
somebody edited a generated file by hand.

Usage:
    python audits/audit_playtest.py            # re-run and compare, exit 1 on drift
    python audits/audit_playtest.py --write     # re-run and update PLAYTEST.md in place
"""
import difflib
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
TRACKED = ROOT / "PLAYTEST.md"


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

    with tempfile.TemporaryDirectory() as td:
        fresh = Path(td) / "PLAYTEST.md"
        if not run_harness(fresh):
            return 1
        new = fresh.read_text(encoding="utf-8")

    old = TRACKED.read_text(encoding="utf-8")
    if old == new:
        runs = old.count("posses =") or old.count("posses")
        print(f"OK: PLAYTEST.md is what the engine plays today "
              f"({len(old.splitlines())} lines, reproduced exactly).")
        return 0

    if write:
        TRACKED.write_text(new, encoding="utf-8", newline="")
        print("PLAYTEST.md rewritten from the harness. Rebuild the three modules: "
              "their What the Night Costs tables are generated from it.")
        return 0

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
