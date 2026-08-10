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

## What each one checks

| File | Checks | Cost | Needs |
|---|---|---|---|
| `audit_names.py` | No two modules share a name. Hard-fails on a distinctive word shared between two titles **or a shared title grammar**; lists shared proper nouns for a human to judge; cross-checks `names.json`'s spent-word list against the shipped titles. | instant | built modules |
| `verify_release.py` | One version everywhere (csproj ↔ CHANGELOG ↔ README ↔ CLAUDE.md), and every GritKeeper version in the CHANGELOG except the newest has a `gritkeeper-vX.Y.Z` tag. `--delivered` adds the local-only check that the packaged exe carries the source's version. | instant | git tags (a shallow clone sees none) |
| `verify_rules.py` | 697 cross-checks of the printed Player's Book against `chargen.json` against the spine formula. The guard the whole project rests on. | instant | `blood-and-grit.html` |
| `audit_ui.py` | Every interactive control in the app is wired and tipped; every modal dialog answers Esc; nothing refuses in silence. | instant | `GK/source/*.cs` |
| `audit_maps.py` | Cartographer and engineer in one. Anchors resolve, pin numbers match numbered scenes, the standalone `.svg` is byte-for-byte the drawing in the book; scale bar, north arrow, legend, nothing outside the frame, no two labels overlapping. | instant | built modules + `module_maps.py` |
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
