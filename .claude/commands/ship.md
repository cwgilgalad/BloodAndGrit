---
description: Cut a release of GritKeeper, the books, or the modules — the ordered walk, with the gate in front of it
argument-hint: gritkeeper | books | modules  (or leave blank and I will read the diff)
---

# /ship

The ordered actions for cutting a release out of this repo. **This file is the only ordered list**
— `CLAUDE.md` carries the rules and the reasons behind them and deliberately does not restate the
sequence, because a second copy of a runbook is how the two drift. Where a step has a reason worth
knowing, it names the section of `CLAUDE.md` that holds it rather than repeating it here.

Component to ship: **$ARGUMENTS** (if that is empty, read `git log main..HEAD` and `git diff` and
say which component moved before doing anything).

Nothing below is optional and nothing below is reorderable. Every one of these steps exists
because skipping it has already cost something on this project at least once.

---

## 0. The gate

```bash
python audits/verify_all.py --release
```

Green, or stop and fix. Read the numbers even when it passes — a check that passes still prints
the figure it passed on, and drift shows up in the figure long before it shows up in a failure.

If this is a **books or modules** ship and the app has not moved, `--release` is more than is
needed; `python audits/verify_all.py --full` is the honest gate. Say which one you ran.

**Two of these checks cannot pass on an uncommitted tree, so on a session branch that still has
work in it the gate runs here and again after step 5.** `audit_built_matches_committed.py`
compares every built `.html` against its committed copy, and `--delivered` compares the packaged
exe's build commit against HEAD — both are red until the sources are committed and the exe is
built from that commit. The order that works, found the hard way on 2026-08-23:

1. **Commit every source change first** — builders, `.cs`, data, docs. Nothing left in the tree.
2. **Then** `dotnet publish` → `sign` → `package` (step 5), so the exe stamps *that* commit.
3. Commit the packaging output. `app_changed_since()` is scoped to `GK/source` and `GK/rules`, so
   a commit that only touches `GritKeeper/` and the PDFs leaves the delivered check green.
4. **Then** run `--release`. It is the gate on what is about to be tagged, not on a work tree.

Packaging before committing stamps the exe with the *previous* commit and the gate says so by
name — same version, older build. That is the check working, not a false alarm.

## 1. The version is bumped, and it is bumped in one place

- **The app:** `<Version>` in `GK/source/BloodAndGritKeeper.csproj`, and nowhere else.
  `MainForm.AppVersion` reads it off the assembly and `package.ps1` names the tag from the built
  exe's `FileVersion`.
- **A book:** the four version strings in its own `build_*.py`, all on the right of the retext
  tuples. The Player's half is derived from the shell now, so a Player's Book bump cascades
  nowhere — see *The version cascade* in `CLAUDE.md`.
- **A book, in the app:** `PlayerBookVer` / `KeeperBookVer` / `BestiaryVer` in
  `GK/source/MainForm.cs`. A book bump without these is a patch release of the app; that is what
  v1.43.1 was.
- `bundle` versions (`books-vX.Y`, `modules-vX.Y`) are release numbers and belong to no book. Do
  not try to make one track the other.

## 2. `CHANGELOG.md` gets its entry, in the same commit as the bump

Newest first. What changed, what it cost, and what was found on the way — the entries on this
project carry the reasoning, not a bullet list, and a future session reads them as the record.

## 3. The docs catch up

`.githooks/pre-commit` runs `update_readme.py` and re-stages the four files whose version claims
are anchored. It does **not** reach the version table's page counts in `CLAUDE.md`, the
`## The Keeper's Book (vX.Y)` style headings, or anything in `GK/CLAUDE.md`. Walk those by hand.

`verify_release.py` inside the gate is what catches a miss here, so a red gate at this step is the
system working.

## 4. Commit, merge, and let the hook push

```bash
git add -A && git commit           # on the session branch
git checkout main
git merge --no-ff session/<yyyy-mm-dd>-<topic>
git branch -d session/<yyyy-mm-dd>-<topic>
```

`.githooks/post-merge` pushes `main` and only ever `main`. A session branch lives on this laptop
until it is merged, on purpose.

## 5. Build the artifact

**For the app** — and never pass `-o`; see *NEVER pass `-o`* in `CLAUDE.md`:

```bash
cd GK/source && dotnet publish -c Release
cd ../.. && ./sign.ps1 && ./package.ps1
```

`package.ps1` re-mirrors `GK/` into `GritKeeper/`, refreshes `GritKeeper/app/`, and writes
`GritKeeper.zip`. It refuses an unsigned exe unless forced, so sign first. If a copy of GritKeeper
is running out of `GritKeeper/app/`, it says so by name and switches to `-Staged` itself.

**For the books or the modules:**

```bash
python tools/make_bundles.py books      # or: modules
```

Built from a declared list, and it reads each book back to check it shows the version its own
builder stamps. **That check reaches the HTML only.** The PDFs are in the same manifest and are
bundled on trust, so a zip can ship a PDF that disagrees with its own HTML and nothing goes red.

**So reprint them here, every ship, without being asked** (Cole, 2026-08-27: *"keep up on that
please"*). This is the one place the PDF pipeline runs on its own initiative; an ordinary book edit
still leaves it alone.

```bash
python make_pdf.py
```

It prints each PDF's page count beside the rendered sheet count and fails on a mismatch. Say the
figures in the report.

The reason this step is not optional: the PDFs stopped being tracked files on 2026-08-27, and
README's six "Read" links point at `/releases/latest/download/<name>.pdf`. The Release asset is the
only way a stranger reads a book, so shipping a stale PDF ships a stale front page. Build the
bundles **after** this, or the zips carry the old prints.

## 6. Write the release notes

`RELEASE_NOTES_<tag>.md` at the repo root. It is git-ignored scratch: write it, paste it into the
Release, leave it on disk. Written for somebody who does not read this repo — what changed and why
it matters at a table, not a diff summary.

## 7. Tag, push the tag, cut the one Release

```bash
git tag <tag>
git push origin <tag>
gh release create <tag>   GritKeeper.zip BloodAndGrit-Books.zip BloodAndGrit-Modules.zip   Blood-and-Grit-Players-Book.pdf Blood-and-Grit-Keepers-Book.pdf Blood-and-Grit-Bestiary.pdf   Blood-and-Grit-Module-I-The-Salt-at-Coffin-Wells.pdf   Blood-and-Grit-Module-II-A-Face-Not-His-Own.pdf   Blood-and-Grit-Module-III-What-the-Water-Answers.pdf   --title "Blood & Grit — GritKeeper vX.Y.Z · Books vA.B · Modules vC.D"   --notes-file RELEASE_NOTES_<tag>.md
```

Tag the component that actually moved: `gritkeeper-vX.Y.Z` · `books-vX.Y` · `modules-vX.Y`.

**Attach all nine assets every time, including the parts that did not change.** GitHub carries one
Release page and it is the only page, so anything left off it is a thing a stranger cannot
download. Re-upload the unchanged zips and PDFs from disk; they are cheap and the alternative is a
page that serves half a game.

The zips exist because GitHub serves raw `.html` as plain text, so without one a stranger cannot
get a book in a click. The six PDFs are attached loose as well as inside the zips, because
`README.md` links each book at `/releases/latest/download/<name>.pdf` — a link that reads in the
browser and never goes stale.

**A tag with no Release, or a Release with no zip, is not a shipped version.** v1.32.0 was merged
and changelogged as shipped and never published, and every check in the repo stayed green.

## 8. Retire the page the new one supersedes

```bash
gh release delete <old-tag> --yes --cleanup-tag=false
```

The **tag stays**, so `git checkout <old-tag>` still gets that tree exactly as it shipped. Only the
page goes. `--cleanup-tag=false` is not optional.

## 9. Nothing to do about `Latest`

There used to be a step here, and consolidating the pages on 2026-08-27 is what removed it.

Three per-component pages meant GitHub handed `Latest` to whichever shipped most recently, while
`README.md`'s download button pointed at `/releases/latest` — so a books release silently sent
everyone who came for the app to a zip of PDFs, and `gh release edit gritkeeper-vX.Y.Z --latest`
had to be remembered afterwards. It was forgotten once, on 2026-08-09, and no check would have
caught it. With one page there is no flag to move: the newest release is the only release, and it
carries everything.

## 10. Regenerate the index — **after** the pages exist, never by hand

```bash
python tools/release_index.py
```

`RELEASES.md` is generated from the GitHub API merged with its own last version. Hand-editing it
is how it comes to disagree with the repo; running it *before* a delete is how it once went from
thirty-four rows to three. Commit it on its own short session branch and merge.

## 11. Say what shipped

Report the tag, the Release URL, the gate's numbers, and anything left undone. If a component was
deliberately not shipped, say which and why — a silent omission reads as "everything went out".

---

## The two live rules this runbook will not let you forget

- **There is one Release page and it carries all nine assets.** Attach the unchanged zips and PDFs
  too. Every version stays reachable by tag, and `RELEASES.md` is the index.
- **PDFs are reprinted every ship, at step 5, without being asked** (2026-08-27). Between ships, leave them alone. They are the only way anybody outside this laptop reads a book.
