# audits/

Every check in this project, one file each, **run on request and not otherwise**.

Nothing in here builds anything or edits anything (with one stated exception —
see `audit_idempotent_build.py`). They read the repo and report. Run them from
the **repo root**, by name:

```bash
python audits/audit_names.py
```

They were loose in the root alongside the builders until 2026-08-10, and all
eight ran as one CI job on every push — including pushes of half-finished
session branches, which is how a red X came to mean "somebody is mid-sentence"
about as often as it meant "something is broken". They are separate, reviewable
files now, and which ones run is a decision somebody makes.

## Running them together

`verify_all.py` runs these as subprocesses and collects the exit codes. It is a
runner, not a check: it re-implements nothing, and it is not in the table below
for that reason. Adding a check means adding a file here and a row to its
`CHECKS` table, after which `--list` shows it.

```bash
python audits/verify_all.py            # the read-only checks: nothing slow, nothing writes
python audits/verify_all.py --quick    # the instant ones only
python audits/verify_all.py --app      # ... and build, the smoke suite, the self-test
python audits/verify_all.py --full     # ... and the ones that rebuild or take minutes
python audits/verify_all.py --release  # everything, which is the gate /ship reads
python audits/verify_all.py --list     # what would run, and in what order
```

It is a script rather than a slash command on purpose: this has to run at a
prompt, in a git hook, in CI and for Claude alike, and an entry point that only
works while one particular tool is driving is the first thing here to stop
working the day that tool is not. Advisory checks — `audit_whitespace.py`, which
measures gaps a Keeper has to judge — are reported and never counted, so they
cannot turn the exit code red.

## What each one checks

| File | Checks | Cost | Needs |
|---|---|---|---|
| `audit_names.py` | No two modules share a name. Hard-fails on a distinctive word shared between two titles **or a shared title grammar**; lists shared proper nouns for a human to judge; cross-checks `names.json`'s spent-word list against the shipped titles; holds `GK/playtest/Adventures.cs` and `PLAYTEST.md` to the titles the modules actually ship under, and every `module-*.html` named in the repo's docs to a file that exists. | instant | built modules, `Adventures.cs`, `PLAYTEST.md`, `README.md`, `CLAUDE.md` |
| `verify_release.py` | One version everywhere (csproj ↔ CHANGELOG ↔ README ↔ CLAUDE.md), and every GritKeeper version in the CHANGELOG except the newest has a `gritkeeper-vX.Y.Z` tag. `--delivered` adds the local-only check that the packaged exe carries the source's version. | instant | git tags (a shallow clone sees none) |
| `verify_rules.py` | 988 cross-checks of the printed Player's Book against `chargen.json` against the spine formula — the Calling tables, the arms table, the **feature prose, the 3rd-level paths and the picker blurbs** beside them, and since 2026-08-22 **Ch. IV's encounter budget** in both Keeper-side books against `Rules.BudgetRungs`. The guard the whole project rests on. | instant | `blood-and-grit.html`, `keeper-handbook.html`, `bestiary.html` |
| `audit_consistency.py` | 80,831 cross-checks of the **Keeper's** side, which `verify_rules.py` does not reach: Threat by Tier and Sign & Spoor across book/app/`CLAUDE.md`, `creatures.json` still current with the built Bestiary, the Roll-by-Tier appendix, all 143 Grounds entries, every condition a creature inflicts defined in Appendix B, the printed benchmarks against the 175 creatures that are supposed to match them, one shared vocabulary across all six books, every chapter cross-reference, and **app↔book feature parity** — anything one carries that the other does not. | instant | all six built books, `Core.cs`, `CharGen.cs`, `creatures.json` |
| `audit_diversity.py` | Is every possibility the rules offer one some path can reach? Fails only on **dead surface** — a skill no Calling wants and no Origin grants, a condition nothing inflicts, a power list that stops short of rank 5, an ability no Origin raises. Everything else (the Bestiary's Tier grid, the Dread spread, how many ways a thing can be put down, what share of the Bestiary the Grounds tables reach) is measured and printed for a designer, and never touches the exit code. | instant | all six built books, `chargen.json`, `creatures.json` |
| `audit_ui.py` | Every interactive control in the app is wired and tipped; every modal dialog answers Esc; nothing refuses in silence. | instant | `GK/source/*.cs` |
| `audit_maps.py` | Cartographer and engineer in one. Anchors resolve, pin numbers match numbered scenes, the standalone `.svg` is byte-for-byte the drawing in the book; scale bar, north arrow, legend, nothing outside the frame, no two labels overlapping. | instant | built modules + `module_maps.py` |
| `audit_playtest.py` | `PLAYTEST.md` is what the engine plays today. Re-runs the harness (36 full adventures, fixed seed) and holds the file to it, because every difficulty number in the three module books is generated from that file. `--write` updates it. | seconds | `GK/playtest`, a working `dotnet` |
| `audit_ai_tells.py` | The repo's own prose reads as written. Burstiness, generated cadences (negative parallelism above all), em dashes per thousand words, punctuation variety, sentence-opener diversity. `--commits N` reads the last N commit messages too. | seconds | git history for `--commits` |
| `audit_idempotent_build.py` | Building twice yields byte-identical output. **This one rebuilds the books** — it is the exception to "nothing here writes". | minutes | a working build toolchain |
| `audit_built_matches_committed.py` | Every built `.html` / `.svg` in the tree matches its committed copy. Meaningful right after the idempotence check; alone it only says the tree is clean. | instant | git checkout |
| `audit_whitespace.py` | Per-page bottom gaps in a built book, over a threshold. Takes a filename: `python audits/audit_whitespace.py bestiary.html [gap-px]`. Interpretive, never a pass/fail gate. | slow | Playwright + Edge |

## The order that means something

`audit_idempotent_build.py` then `audit_built_matches_committed.py`. Together
they say *rebuilding changes nothing, and what is committed is what a rebuild
produces.* Either alone says much less.

## What is deliberately NOT here

`measure_book.py`, `measure_index.py` and the `build_*.py` scripts stay at the
repo root. The rule is what a file does, not what it is called: **anything that
only reads and reports lives here; anything that builds, measures-and-patches,
or is part of making a change stays with the builders.** `measure_index.py`
writes page numbers back into `build_player.py`, so it is a build step wearing a
verification hat.

## Paths

Each of these derives the repo root as `Path(__file__).resolve().parent.parent`,
because they live one level down. `audit_maps.py` additionally puts the repo
root on `sys.path` — it imports `module_maps`, a root-level module, and running
`python audits/audit_maps.py` otherwise puts `audits/` first on the path and the
import fails for a reason that has nothing to do with maps. If you add an audit
that imports anything from the root, copy that line.
