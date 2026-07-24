# Changelog — Blood & Grit

All notable changes to the three books and the GritKeeper app, newest first. Any commit
that changes content or behavior adds an entry here — and bumps the affected component's
version — in the same commit. Version bumps are tagged `component-vX.Y` at the commit that
ships them. (Moved out of CLAUDE.md on 2026-07-18 when tracking was standardized across all
Desktop\Git repos.)

---

- **README — a front door instead of a build sheet (2026-07-23, user-requested).** The root
  `README.md` was purely build instructions: how to run the builders, how to verify. Nothing
  said what Blood & Grit *is*, and nothing linked to a single finished thing. Added a pitch
  above the technical content — the game in a paragraph (western horror on a PF2E-derived d20
  hybrid; Nerve and the Mark as the two tracks that are ours), a one-line-each table of the
  three books, and what GritKeeper actually does at the table.

  **Four links to the current release of each deliverable.** The three book PDFs go to their
  `blob/main` URLs, which GitHub renders inline in its own viewer — click and read, no
  download. They're unversioned filenames living on `main`, so they stay current by
  themselves. GritKeeper goes to `/releases/latest`, which never needs touching on a version
  bump. The self-contained HTML books get a note rather than a link: GitHub serves raw `.html`
  as plain text for security reasons, so a link would show source instead of the book — no
  third-party viewer dependency was added for it.

  **Deliberately version-agnostic prose** ("the current edition," "the latest release," "a
  whole mundane half" rather than a creature count) so a version bump never leaves the README
  lying. The build/verify instructions are unchanged below the fold, plus a `GK/` entry in
  "What's what" and the app's name corrected to GritKeeper. No version bumps.

- **Repo cleanup — the onboarding artifacts that drifted (2026-07-23, user-requested).**
  Housekeeping only: **no version bumps**, no content or behavior change to any book or to
  the app. Worked from a written assessment of the repo; the project itself was in good
  shape, but several files a fresh session reads *first* had quietly gone stale.

  **The `/session-start` command was describing the pre-rename project.** It still said to
  edit `KT/source`, called the delivered folder `BloodAndGrit-Keepers-Table/`, and named the
  app "The Keeper's Table" throughout — paths that stopped existing at the 2026-07-19 rename.
  A session following it literally would have written to the wrong tree. Rewritten against
  current conventions (`GK/`, `GritKeeper/`, `GritKeeper.zip`, GritKeeper), with the PDF rule
  and the `CHANGELOG.md` split folded in.

  **`preferences.md` deleted.** It was supposed to be a duplicate of `CLAUDE.md` — 687 of its
  815 lines had diverged, freezing it at roughly the 2026-07-11 state: Player's Book v2.12,
  app "The Keeper's Table" v1.2.2, none of the standing rules added since. `session-start.md`
  told you to "read one," so it was a coin flip whether a session picked up context 12 days
  and two renames out of date. `CLAUDE.md` is now the only handoff doc.

  **Onboarding no longer points at a packaged snapshot.** `CLAUDE.md`'s first line told you to
  import `blood-and-grit-sources.zip` into a fresh Project — a zip dated 2026-07-11 carrying
  the old thin `build_player.py`, a standalone `bestiary_extra.py`, and instructions for a
  `player-src.html` that was retired on 2026-07-18. Following it would have produced a broken
  build. Replaced with "hand over the current loose files," which can't go stale.

  **~3.9 MB of dead weight removed** (~11% of the repo): the nine root-level versioned book
  snapshots (`-v2.4/2.5/2.6` Bestiary and Keeper's, `-v2.12/2.13/2.14` Player's — all two or
  more versions behind, produced by no documented build, referenced by no script or doc), and
  the root copy of `img20.png` (byte-identical to `assets/img20.png`, which is the one the
  build actually inlines). `add_index.py` deliberately kept — documented-intentional dead
  code, not clutter.

  **`GritKeeper/source/` is now generated, not tracked.** It was a byte-identical second copy
  of `GK/source` living in git for no build reason — and the exact seam that silently diverged
  once before (2026-07-10). Now git-ignored like `GritKeeper/app/` already was, and rewritten
  from the master tree at package time (`robocopy GK\source GritKeeper\source /MIR /XD bin obj
  publish`). "Don't edit the delivered folder" still holds; the reason is now "it gets
  overwritten," not "it'll diverge." Verified byte-identical against `GK/source` before the
  untracking landed.

  Verified: `build_player.py` rebuilds byte-identical to `main` (the emblem still inlines from
  `assets/`), and twice in a row to itself.

- **Books v2.16 / v2.8 / v2.8 + GritKeeper v1.11.0 — the mundane frontier, the city, and
  the people who were actually out here (2026-07-22, user-requested).** One release, four
  asks.

  **Forty "normal" creatures, so the Bestiary can carry a slow burn.** The Bestiary goes
  110 → **150**. Twenty more honest animals join **Ch. VIII** (25 → 45): the Mad Dog and
  its hydrophobia, the Prairie Dog Town that breaks a horse's leg, the Snake Den, the Sow
  and Cubs, the Wild Cattle of the Brasada, the Stock-Killer Wolf with a name and a price
  on it. Twenty more become a **new Ch. IX, "Hard Men & Hard Country"** — ordinary men
  (rustlers, claim-jumpers, a saloon brawl, a lynch mob, deserters, Comancheros, a hired
  gun, an outlaw gang, a bounty killer, the Regulators) and the country itself (bad water,
  a norther, a prairie fire, a river crossing, a flash flood, a blizzard). Tiers skew low
  on purpose — 14 at Tier I, 14 at II, 10 at III, 2 at IV — because this is early-campaign
  material. Like the living beasts, **none of it costs a point of Nerve or moves the Mark**,
  and that is the whole design: run it for a month and the table learns the country is
  dangerous on its own terms, so the first genuinely wrong thing has nowhere to be filed.
  Mundane entries are now **65 of 150**, against 25 of 110 before. New Grounds table,
  **The Ordinary Country (d20)**; the Keeper's Ch. V now points at both mundane chapters
  and says what they are for.

  **The peoples of the frontier.** The Player's Book Ch. IV is titled *Origins & the
  Peoples of the Frontier* and carried careful long-form sections on **The First Peoples**
  and **The Mexican Frontier** — and nothing on two of the four peoples it most owed. Added
  in the same shape, same length, same rules-of-the-road box: **Black Westerners** (one
  trail hand in four, the Exodus of '79, Nicodemus, the Ninth and Tenth Cavalry) and **The
  Chinese on the Frontier** (nine men in ten on the Central Pacific grade, the Exclusion Act
  of '82, the district associations, Rock Springs this very year). Keeper's Book Ch. VIII
  gains **"Who Is Actually Out Here"** — the trade's Spanish vocabulary, the real
  proportions, and the instruction that this needs *names and jobs*, not a speech — plus a
  note on running horrors that come out of living belief. Bestiary Ch. IX carries the same
  in its own voice, and the Comancheros, Claim-Jumpers, Lynch Mob, Longhorn Herd, Wild
  Cattle and Regulators entries were rewritten where the history is exact. Two new rollable
  name tables in Ch. XII, and the app's `npcGiven`/`npcSurname` grew 20 → 48 and 20 → 46 to
  match, so the generators stop contradicting the page.

  **Cities.** New Keeper's Book **Ch. XIV, "The Lamplit City"** — running the game in Dodge,
  Kansas City, San Francisco, Butte, Tombstone, Omaha, Denver, Virginia City, Cheyenne and
  Leadville without losing the tone. Its argument is that a city is *better* ground for the
  dark, not worse: anonymity beats isolation (a thing that empties a town of 200 by Tuesday
  feeds in Kansas City forever), the crowd is cover, and indifference does the work fear used
  to. Six things change at the table and only six — guns checked at the deadline, gunfire
  that costs an inquest, witnesses and the press, institutions that commit you rather than
  disbelieve you, paper as the new tracking, and Dread moved indoors and underground. Each
  Bestiary chapter gets a paragraph on how it bends downtown, and **the Dark Cultist
  incorporates**: it charters as a benevolent society with a lawyer, a brass plate, and the
  coroner on its membership roll, so the final scene of a city campaign is an exposure rather
  than a gunfight. Ten real cities keyed, a build-your-own-city checklist, three new tables,
  and a closing note on keeping the party's country competence valuable. New Bestiary Grounds
  table, **The Lamplit City (d12)**; new app tables `cityQuarter` / `cityMachine` /
  `cityWrongNote` / `cityJob` behind a **"A city, in four rolls"** generator button.

  **An editor's pass and a whitespace audit.** Cross-checked every shared number across both
  books and `Core.cs` and found one real drift: the Bestiary's Threat-by-Tier table gave Tier
  I's Dread DC as "10–13" where the Keeper's Book and the app both say "— / 10–13" (a Tier I
  thing may have no Dread at all). Fixed in the Bestiary. All three books: 0 dead anchors, 0
  duplicate ids, 0 die-size/row-count mismatches. `audit_whitespace.py` now **classifies**
  gaps instead of listing them — a page that ends short because the next one opens a chapter
  is the design working, not a defect. Of 44 gaps over 140px across 439 pages, 36 are chapter
  starts and the remaining 8 are heading-orphan avoidance at 143–227px. Nothing to reclaim.

  Page counts 170 → **174** / 88 → **101** / 131 → **164**; all three measure clean (parity,
  zero true-scale clip, zero mobile h-scroll, every anchor resolved) and all three builds are
  idempotent. **PDFs regenerated on explicit request** — 174 / 101 / 164 pages, 612×792pt,
  verified page-for-sheet.

- **GritKeeper v1.11.0 — the Level up button works, and launch is 3x faster (2026-07-22,
  user-reported).**

  **The dead Level up button.** Reported as "I used it once, but now it seems broken," and it
  was: the first-launch demo posse seeded by builds older than v1.9.0 persists in
  `session.json` as six rows with `Sheet: null`, and `LevelUpMember` answered a sheetless row
  with one line in the roll log — on a different tab. The user's own live session had all six.
  Now a sheetless row is offered a repair: GritKeeper draws a rules-legal sheet for the row's
  Calling at its current level (keeping name and gender, and *not* inventing a gender the row
  never had) and levels them. Every other way out of that button now says so in a dialog.

  **Startup.** The v1.10.0 "startup pass" reasoned about JIT in the abstract and made launch
  worse. Measured four publish configurations to first window, each first launch on a
  brand-new copy of the exe so Defender's first-execution scan counts:

  | config | exe | first launch | every launch after |
  |---|---|---|---|
  | ReadyToRun + compression (v1.10.0) | 73 MB | 18.0 s | 1.64 s |
  | ReadyToRun, no compression | 172 MB | 14.5 s | 0.88 s |
  | **no ReadyToRun, no compression** | **155 MB** | **5.1 s** | **1.00 s** |

  Compression is the expensive one — ~39 MB of native libraries inflated and written to
  `%TEMP%\.net\GritKeeper` on the first run of every new build, then scanned. R2R doubles what
  goes through it. Shipping neither. **The zip shrinks** (71.3 → 65.4 MB) because Deflate does
  the same job once, at download time. `IncludeNativeLibrariesForSelfExtract=false` was tried
  and never opens a window; the csproj records that so nobody tries it again.

  **Tab loading.** Building all ten tabs up front cost 379 ms of a ~1,000 ms launch (Bestiary
  91, Posse 71, Map 61, Dice 46, Reference 45) for nine tabs nobody was looking at. Nine are
  now built on first visit; the roll log, the session ledger and the encounter party level
  moved behind fields first, so an unbuilt tab can't swallow them. Shipped and signed, the
  app now opens in **6.1 s first / 0.86 s after**, against 18.0 s / 1.64 s.

  **Five review findings, fixed.** `session.json` is written staged-then-moved — the old
  truncate-in-place could tear on a kill or a crash-time save, and `TryAutoLoad`'s fallback
  for an unparseable file was `SeedDemo()`, which silently replaced the Keeper's whole table
  with the demo posse and then autosaved over it. An unreadable session is now set aside as
  `session-unreadable.json` and reported. Open Ledger pop-outs close with the table they
  describe on load/undo (they were keyed to `PartyMember` instances that Load and Undo
  replace, so they went stale and leaked their dictionary entries). The encounter grid stopped
  allocating a `Font` per cell paint. Two hot regexes cached. The coin ledger parses prices as
  invariant.

  Also: `creatures.json` was **stale** — it still carried the pre-editorial prose for seven
  creatures from the 2026-07-21 pass, so the app and the book disagreed. Re-extracted. Smoke
  4569 → **4612**, 0 failed, with new guards on the creature count, the eight chapters, the 65
  mundane entries costing no Nerve and no Mark, every creature carrying lore and a Found line,
  and the four city tables.

- **GritKeeper v1.10.1 — book-version label sync (2026-07-21).** The status-bar and
  About-box labels now read **Player's Book v2.15 · Keeper's Book v2.7 · Bestiary v2.7**,
  matching the books' human-voice editorial pass. No behavior or embedded-content change
  (the app's creature/table data was never affected by that copyedit); build 0/0, smoke
  4569/4569, exe re-signed. Released with the signed exe.

- **Books v2.15 / v2.7 / v2.7 — editorial pass for a human voice (2026-07-21,
  user-requested).** A line-editor's read of all three books to strip the tells of
  machine prose, with the author's voice preserved tightly. The main target was
  **negative parallelism** — the "it's not X, it's Y" antithesis, which had quietly
  become a habit in the Bestiary's Keeper notes (the "Not a fight — a flood" construction
  alone appeared three times). The iconic flagships were kept ("this is not a thing you
  kill, it is a thing you resolve"; "a house that is a ghost"; "these are not killed, they
  are shut out"); the repetitions were varied so no single figure recurs enough to read as
  a formula. Every "not merely" (a formal/AI tic) across the Player's and Keeper's books
  was recast. No creature, rule, or table content changed — page counts hold at 170 / 88 /
  131, every book still measures clean (parity, zero true-scale clip, zero mobile h-scroll,
  all TOC/index anchors resolved), and all three builds are idempotent. (GritKeeper embeds
  no changed content, so its data is untouched; its README book-version labels were updated
  to match, and only the compiled status-bar label lags until the app's next build.)

- **GritKeeper v1.10.0 — souls level up at the table, and a faster cold start (2026-07-21).**
  - **Level up (Posse tab · Ledger window).** A New Soul–built soul can now advance one
    level at a time through a ✦ Level up button — on the Posse action bar (acts on the
    selected soul) and on each soul's Ledger window. The dialog shows only what the new
    level unlocks: the Hit-Die Blood roll (roll it or set the face; CON mod added), the
    5th/10th-level ability boost, the odd-level Edge (plus the Gunhand's bonus combat
    Edge), the 3/5/7/9 skill increase, the 3rd-level subpath, and any new Signs — each
    populated from the generator's own eligibility helpers so it can never offer an
    illegal pick, and each defaulting to "let the book choose." The soul's new Blood and
    Nerve are granted to current as well as maximum (leveling isn't a heal, but the new
    capacity is theirs), and any open Ledger refreshes in place. A hand-entered row (no
    character sheet) is told to build the soul out first; a 10th-level soul is told it's
    at the frontier's ceiling.
  - **How it works (`CharGen.LevelUp`).** Rather than reconstruct the wizard's
    `AssembleSpec` and re-walk from 1st — `Assemble` re-rolls every prior level's Blood and
    has no way to be handed the old rolls, so that path would quietly destabilize the
    levels below — `LevelUp` clones the finished sheet and appends exactly the new level's
    growth, mirroring `Generate`'s own per-level walk (boost → Blood → features → Edge(s)
    → skill increase → subpath → Signs → reckon). Everything below the new level is
    byte-stable, and the result passes `CharGen.Validate` clean. `PreviewLevelUp` drives
    the dialog's controls and option lists off a clone advanced by the level's
    deterministic part, so Edge/skill eligibility reflects the new level.
  - **Startup pass.** The self-contained publish now precompiles with **ReadyToRun**
    (cold start skips most JIT) and runs with **InvariantGlobalization** (no ICU culture
    load at launch) — the latter is safe because every coordinate the PDF/SVG exporters
    write already goes through an explicit `CultureInfo.InvariantCulture` formatter, so a
    comma-decimal locale can't corrupt an export. Single-file compression stays on so the
    release binary stays one modest file; `TieredPGO` stays at its default. The owner-drawn
    Ledger and map controls were audited for per-paint GDI churn — both were already
    double-buffered with cached brushes/pens, so no change was warranted, and the deeper
    map-bitmap cache was deliberately deferred (a mis-invalidated cache would risk a real
    visual bug on a surface that isn't animated).
  - Smoke suite **2348 → 4569** asserts (the level-up walk is proved conformant across
    every calling × ability method × level 1→10, with byte-stable lower levels, fixed-seed
    reproducibility, honored explicit choices, and the Gunhand/​caster growth paths). Build 0/0.

- **GritKeeper v1.9.0 — gender on every soul, and a first-launch posse with real sheets
  (2026-07-21).**
  - **Gender fills the Ledger on every row (follow-on to v1.8.0's box-filling).** The
    Ledger's Gender box now reads from the member as well as the sheet, so a hand-entered
    soul that carries a gender shows it instead of an em-dash; `PartyMember` gained a
    `Gender` property (change-notified, persisted in `session.json`), the Posse grid gained
    a **Gender** column, and both New Soul → Posse and the sheet→member resync carry it
    across. (Genuinely-unknown gender still reads as a muted em-dash.)
  - **The first-launch demo posse is now six full, rules-legal character sheets** rather
    than bare stat rows — each Appendix-D pregen opens a complete Ledger (abilities, saves,
    Signs, gear, the Four Questions), because `SeedDemo` now builds them through
    `CharGen.Generate` with a fixed Calling and the pregen's own name and gender. A fixed
    seed makes that opening posse identical for everyone; `Rules.Reseed`/`ReseedEntropy`
    bracket the seeding so play dice stay unpredictable afterward. Every seeded soul
    validates clean (0 violations). It persists after first launch exactly as before.
  - Smoke suite **2348** asserts, all passing; build 0/0.

- **GritKeeper v1.8.0 — the map holds still: per-feature random streams, WYSIWYG
  exports, movable secrets, fords on the water, a three-row Map bar, and the Ledger
  fills its boxes (2026-07-19, user-requested).**
  - **The toggle bug (user-reported: checking/unchecking a view box showed a different
    map).** Root cause: one shared `Random` stream — drawing the rail consumed numbers
    the land would otherwise have used, so any overlay toggle reshuffled symbols,
    landmarks, even the title. `Generate` now derives an independent stream per feature
    (water/trail/rail/town/land/landmarks/hour/secrets/name) from the seed, and the
    settlement claims its name and ground even when unshown. Every checkbox is pure
    ink-on/ink-off. Smoke-proved: flipping each of the five overlays leaves the title
    and every landmark byte-identical. (Seeds draw differently than v1.7 — the streams
    changed; determinism per seed+settings is unchanged and still asserted.)
  - **Exports are exactly what you see** — a corollary of the fix: Save SVG/PDF/Copy
    SVG export the displayed model, so checked overlays (grid, Keeper's layer), moved
    landmarks, and moved secrets all ride along. Tooltips now say so.
  - **Fords snap to the water (user-requested):** a Ford landmark places on the river's
    middle stretch (a vertex of the clipped polyline) or on the lake shore — never out
    in the sagebrush. Smoke asserts every generated ford touches the river.
  - **The Keeper's red marks are movable (user-requested):** secrets are recorded like
    landmarks (`MapModel.Secrets`, keyed by index since their lines can repeat) and,
    with ✥ pressed and the Keeper's layer shown, ring in red and drag like landmarks;
    right-click puts one back, "put everything back" covers both kinds (confirmed).
    Their labels also clamp inside the neatline now.
  - **Map bar: three rows by intent (user-requested)** — row 1 the survey (Ground/
    Scale/Hour/Water/Landmarks/Seed/New map), row 2 Show + Zoom (overlay checkboxes ·
    zoom/Fit), row 3 at-the-table + Export (✥ Landmarks, markers, Tracker → Map · the
    three exports), with thin rule separators between groups.
  - **Ledger pop-ups fill their boxes (user-reported):** souls without a full character
    record (hand-entered rows, the seeded Appendix D pregens) showed bare white boxes
    for Abilities/Speed/Init./Attack/Origin/Gender. Everything derivable now fills in —
    RES is recovered from Nerve − Level, Init. shows the DEX modifier on full sheets —
    and the genuinely unknown reads as a muted em-dash. (Init. was empty even on full
    sheets; now it's the DEX mod.)
  - Smoke suite 2339 → **2348** asserts, all passing.

- **GritKeeper v1.7.0 — movable landmarks, and the ink respects the border
  (2026-07-19, user-requested).**
  - **✥ Landmarks (Map tab):** a pressed-state toggle that lets the Keeper customize
    the survey's randomly-placed landmarks. While on, every named landmark wears a
    dashed gold grab ring; drag one and its whole ink (symbol + label) moves together —
    `MapModel` now records each landmark's name, anchor, generated position, and its
    contiguous prim range, and the pure `MapGen.MoveLandmark` translates exactly that
    range and nothing else (smoke-proved: own prims shift by exactly the delta, every
    other prim byte-identical, move-back restores the original ink). Right-click a
    landmark → "put it back where the survey drew it," or "put every landmark back"
    (confirmed, per the standing rule). Placements are kept per map number and
    re-applied when the same seed regenerates (hour/layer/water toggles), cleared on a
    genuinely new map; SVG/PDF exports carry the custom placement. Hover shows a hand
    cursor over anything grabbable (markers included — new to this pass).
  - **Border containment fix (user-reported: rivers ran past the map edge).** Rivers,
    creeks, trail legs + forks, and rail lines are deliberately generated from 12
    units off one edge to 12 off the other so they read as passing through the
    country — the SVG viewBox quietly clipped that overhang, but the GDI preview and
    the PDF drew it, so ink crossed the border frame. Now a Liang–Barsky polyline
    clipper trims them to the inner neatline at *generation* time, so all three
    renderers agree by construction; wide strokes' round caps stay inside the outer
    frame (clip inset 15, frames at 8/15). New smoke sweep: 5 seeds × all 6 water
    kinds with trail+rail+secrets on — zero Line-prim points beyond the paper.
  - Smoke suite 2333 → **2339** asserts, all passing.

- **GritKeeper v1.6.0 — universal undo/redo, a smarter watermark, a color-coded dice
  log, confirmations closed out everywhere, and bigger random generators (2026-07-19).**
  A user-requested UX pass:
  - **Universal Undo/Redo**: snapshot-based over the same `GameSession` shape File →
    Save/Load already uses. The four `BindingList`s (`party`/`tracker`/`encounter`/
    `clocks`) each push a JSON snapshot onto a 50-deep undo stack on any add/remove/edit;
    `ApplySession` now suppresses re-capture during its own bulk rebuild so a restore is
    one step, not N. Reachable via **Edit ▸ Undo/Redo** (Ctrl+Z/Ctrl+Y) and matching
    buttons pinned in the status bar, so it's live from any tab. Session notes keep the
    textbox's own native undo instead — snapshotting every keystroke would flood the stack.
  - **The emblem watermark scales with the window**: previously forced into the bottom
    half of a pane regardless of how much background space was actually free; now
    centers in whatever's free below the real content and grows/shrinks with the pane's
    own size, capped at a dignified share of the width.
  - **The Dice tab's roll log is color-coded** (`StyleRollLog`, an owner-drawn
    `ListBox`): a four-degrees result (CHECK/DREAD) is graded by its degree word —
    critical success gold and bold, critical failure near-black and bold, a plain
    success verdigris, a plain failure rust — a bare quick-die roll by whether it landed
    on its max or min face, any other roll gets a neutral steel-blue tag, and plain
    posse/tracker/session lines stay the default ink.
  - **Confirmation dialogs closed out on the last unguarded clears**: "Clear log" (Dice),
    "Clear" (Generators output), and "Clear" (New Soul sheet) now confirm before wiping,
    matching every other destructive action in the app.
  - **Random generators widened**: the `chargen.json` flavor pools (given names,
    vices, lost/seen/moving) roughly doubled (16→30 names each); the single-roll
    Country-in-Your-Pocket tables (rumors/trail/plunder/omens — the ones without the
    town/face generators' combinatorial multi-roll structure) grew by 10–12 entries
    apiece in `tables_extra.json`; and the Grounds terrain tables picked up every
    ordinary Bestiary beast that wasn't already cited anywhere (badger, bobcat, coyote,
    black bear, gray wolf, mountain lion, wild boar, bison bull, grizzly bear, old
    tusker, stampede — the Tier V White Bison stays off every table on purpose, per its
    Ch. XII "gone quiet" rumor).
  - **Map tab: tactical markers + zoom & pan (same session, user-requested).**
    ＋ Marker ▾ drops a posse soul (green) / NPC (gold) / creature (red) at the view
    center; **Tracker → Map** columns the whole tracker onto the field (posse west,
    trouble east, skips names already standing); markers drag into position (one undo
    step per completed drag), right-click renames or removes, Clear markers confirms.
    Markers live in map-model coordinates in `session.json` (`GameSession.MapMarkers`)
    so they survive restarts AND reseeds — session state, deliberately not part of the
    deterministic map. Zoom: mouse wheel at the cursor (1×–8×), drag empty ground to
    pan, 🔍＋/🔍−/Fit buttons; view state only, never in exports.
  - **Generators: "The Hand Behind It" left the Grounds dropdown (user-reported).**
    It's the villain picker, not a terrain — listed among the grounds it read like a
    stray creature. Now its own button under the terrain roller, same safe-table check.
  - **Expert-review pass on the session's own code, three real defects fixed before
    merge:** (1) the color-coded log's owner-draw handler disposed the ListBox's own
    Font on every non-bold line (worked only by TextRenderer's handle cache — latent
    crash); a cached bold variant now lives as long as the log. (2) Undo captured once
    per ListChanged event, so one click (Damage → posse edit + tracker mirror) made two
    steps with a desynced middle, and New Session flooded 2×posse-size steps; captures
    now coalesce via BeginInvoke — one user action, one undo step, always a consistent
    snapshot. (3) The Ctrl+Z/Ctrl+Y menu shortcuts intercepted the keys before any
    focused TextBox saw them, so typing in Session notes + Ctrl+Z would yank the whole
    table instead of undoing typing; Undo/Redo now route to the focused text field's
    native undo first, and no-op while a grid cell editor is open. Plus two smaller
    ones: owner-drawn ListBoxes don't auto-compute HorizontalExtent (long log lines
    couldn't h-scroll — now measured in Log()), and StatusStrip tooltips needed
    ShowItemToolTips.
  - **The name finished its move (user-requested):** working tree `KT/` → **`GK/`**,
    delivered folder `BloodAndGrit-Keepers-Table/` → **`GritKeeper/`**, zip →
    **`GritKeeper.zip`** — plus the last in-app "Keeper's Table" strings (session
    file-dialog filters, crash-report captions) → GritKeeper.
  - Smoke suite grew from 2322 to 2333 asserts (one per new terrain entry's
    real-creature-name check); all passing. Published, signed, mirrored to the
    deliverable, and rezipped.

- **GritKeeper v1.5.0 — the app renamed, the Map tab shipped, the Ledger everywhere,
  a chargen wizard, hand-tweaks, gender, colored dice (2026-07-18/19).** The app is now
  **GritKeeper** (exe `GritKeeper.exe`, product/title/About/README updated; the internal
  namespace stays `BloodAndGritKeeper` so embedded-resource names and the source tree
  hold still). One long user-request session:
  - **Map tab finished and wired in** (the previous session's `MapGen.cs`/`TabsMap.cs`/
    `Pdf.cs` were complete but never added to the tab strip): Trail Maps — seeded
    procedural frontier surveys by ground/scale/hour/water, trail/rail/settlement/grid/
    Keeper's-secrets toggles, deterministic per seed, Ctrl+G for a fresh map, export as
    SVG (file or clipboard) or **one-page landscape-Letter PDF** (per explicit user
    request). PDF writer proven with PyMuPDF (page count/size) and rendered visually.
  - **The Ledger, on glass** (`Ledger.cs`, new): the Player's Book's character sheet
    redrawn as a live WinForms control (`LedgerView`) — name/**gender**/calling/level/
    origin row, the six abilities, reckoned numbers, the Mark's six boxes, the Four
    Questions, all seventeen skills with proficiency ticks, edges & path, arms & gear &
    coin. The New Soul tab now renders every sheet on it (A−/A＋ zoom), replacing the
    plain-text view.
  - **Soul pop-out windows**: double-click a posse member (or their far-right **Ledger
    button**, also on the Tracker for posse souls — never for creatures or ad-hoc rows)
    to open their Ledger in a modeless window with the exact Bestiary-card configuration:
    one window per soul, reused, cascading, A−/A＋, → Tracker, and ✎ Tweak when a full
    sheet exists. Members carry their whole `CharacterSheet` in `PartyMember.Sheet`
    through `session.json` (sheet converted to auto-properties for serialization;
    round-trip smoke-tested).
  - **Notes expand**: double-click a truncated Posse Notes cell to read/edit the whole
    note in a resizable dialog (Enter stays a newline; explicit Save).
  - **Posse reorder**: ▲ ▼ move the selected soul, selection follows.
  - **Colored dice** (user-specified palette): d4 green · d6 blue · d8 orange · d10
    white · d12 yellow · d20 red · d100 purple — applied to the keypad and quick-dice
    buttons (`DieBtn`, FlatStyle.Flat) and the tray's tumbling faces; best face now
    rings gold and a 1 rings near-black (the old verdigris/blood rings vanished on
    colored faces). Fixed the keypad's +d100 label clipping at width 54.
  - **Dice quantity**: a × spinner on the keypad row — `Rules.ExprAddDie` takes a count
    (× 4 then +d6 → 4d6; stacks: 2d6 + ×3 → 5d6), clamped 1–100, smoke-tested.
  - **New Soul, three roads**: 🎲 generate (as before, now with **gender** rolled and
    the given name drawn from gender-matched lists in `chargen.json`; Ch. III review
    confirmed the book carries gender only in prose, so the app now records it
    explicitly) · **🧭 Wizard** (`TabsWizard.cs`, new — nine steps: level/method/name/
    gender, Calling, Origin, ability assignment with Suggest + 5th/10th boosts, skills +
    increases, Edges from lists filtered by live legality, Signs/path/calling-choice,
    coin + shopping the printed price list against a hard budget, the Four Questions;
    every unanswered choice falls back to the book's own random draw) · **✎ Tweak**
    (every number and list editable; sheet re-validated but never blocked — the Ledger
    notes "hand-tweaked" instead). Wizard assembly is pure logic in
    `CharGen.Assemble(AssembleSpec)` and re-uses the same `ReckonNumbers`/eligibility
    code as the generator, so the two roads can't disagree.
  - **Soul sheet → PDF**: Save PDF… on the New Soul tab writes the sheet as a printable
    Letter PDF (`Pdf.TextSheet`, previously written but never wired; footer em-dash
    WinAnsi bug fixed).
  - Ten tabs now: Ctrl+0 reaches the tenth, the five-minute lesson/shortcut card/status
    bar rewritten, View-menu shortcut labels fixed for tab 10.
  - Verified: build 0/0; smoke **2,322/0** (Assemble conformance sweeps incl. junk-choice
    fuzzing, gendered-name checks, sheet session round-trips, map generation/SVG/PDF
    structural + determinism, × count builder cases); PDFs validated with PyMuPDF and
    rendered; app driven and screenshot-verified (rename, Map, colored dice + × spinner,
    Ledger render with gender, posse ▲▼/double-click/Ledger buttons, Tracker button
    only on posse rows). Branch `session/2026-07-18-gritkeeper-ux`.

- **Keeper's Table v1.4.0 — menu bar, dice keypad, Reference deck, real icons, watermark,
  keyboard pass (2026-07-18).** Two user request batches in one session:
  - **Menu bar** (`Menus.cs`, new): **File** — Save session (Ctrl+S), Save session as…
    (Ctrl+Shift+S), Load session… (Ctrl+O; writes `session-backup.json` beside the exe
    before replacing the table, and validates the file before asking), Exit. **View** —
    all nine tabs with their Ctrl+N shortcuts shown. **Help** — *The five-minute lesson*
    (F1; a modeless, zoomable in-app walkthrough of all nine tabs, saving, and the
    session rhythm), *Keyboard shortcuts*, and *About* (emblem, app + book versions).
    Persistence refactored into shared `Snapshot()`/`ApplySession()` so autosave,
    save-as, load, and startup auto-load all ride one code path.
  - **Dice-tab expression keypad**: `+d4`…`+d100` buttons build the expression (clicking
    the same die stacks its count — d6 → 2d6 → 3d6), ＋/−/digits build the modifier,
    ⌫/C edit it; operators never double up. Logic lives in `Rules.ExprAddDie`/`ExprAppend`
    (pure, in `Core.cs`) with 63 new smoke asserts including builds-always-parse sweeps.
  - **Reference tab rebuilt as an 11-leaf Keeper's screen**, paged with ◀ ▶ or Left/Right
    (the arrow keys are captured in `ProcessCmdKey`, so they work regardless of focus;
    the deck wraps around). Every leaf is real tables (monospace, Blood-red header bands,
    last-column word-wrap): the Roll & DC ladder · Iron Code · wounds & Lasting Injuries ·
    Conditions · Nerve & Dread (+ recovery) · Mark & Taint · Signs & Grit · the Long
    Odds · **Arms of the Frontier** · **Goods & Provisions** · skills/saves/abilities.
    The arms, goods, signs, and skills leaves render live from `Data/chargen.json` —
    the printed prices and dice can never drift from the book. (RichTextBox landmine
    documented in `RTbl`: selection formatting must be re-asserted before *every*
    append or later lines silently fall back to the proportional default and the
    columns shear.)
  - **Keyboard pass** (20-year-UX discretion): Ctrl+D/Ctrl+H damage/heal on Posse *and*
    Tracker (scoped to the active tab, suppressed while a grid cell is mid-edit),
    Ctrl+I initiative + Ctrl+R next round on the Tracker, Ctrl+F to the Bestiary search,
    Enter pops out the selected creature. Deliberately NOT keyed: destructive clears
    (stay click-and-confirm) and generator browse buttons (Tab+Space serves them).
    Tooltips name their shortcuts; the Help shortcut card covers all of it.
  - **Real icons**: new multi-size `app.ico` built from the cover emblem (full emblem at
    256/128/64/48, a skull-tight crop at 32/24/16 so the small sizes stay readable) —
    `<ApplicationIcon>` gives the exe its Explorer/desktop icon, and the embedded copy
    feeds every window title bar (main, creature pop-outs, lesson/shortcuts). The small
    fixed dialogs drop the stock icon instead (`ShowIcon=false`). A desktop shortcut
    **"The Keeper's Table"** now points at the delivered exe.
  - **Watermark**: the emblem, ghost-faint (≈5% alpha), in the dead space bottom-right of
    the busier panes (Posse/Encounter/Tracker grids + empty-state hints, Dice and
    Generators button panels, Session clocks, New Soul hint). It sizes itself to the free
    space and vanishes entirely when content comes within reach — never behind rows or
    text.
  - Verified: build 0/0; smoke **1,960/0** (63 new builder asserts); launched and
    screenshot-verified (menu bar, icons, watermark restraint, keypad wiring via the
    smoke-tested pure functions, Reference paging by arrow key including wrap-around,
    Ctrl+R/Ctrl+I on the Tracker); published self-contained exe signed **Valid**
    (same CN=Cole Williams cert). Branch `session/2026-07-18-kt-menus-icon-ux`.

- **Keeper's Table v1.3.0 — New Soul character generator, padding/UX pass, clear-everywhere,
  signed exe (2026-07-18).** Five user requests in one session:
  - **New Soul tab (9th tab, Ctrl+1–9)** — a whole random character sheet, strictly
    conformant to the books: Ch. III's eight steps at any level 1–10, both ability methods,
    all 17 Callings × 10 Origins with every cross-constraint enforced (Faith may not take
    the Gambler origin or work Signs; Hedge Magic barred to Faith *and* to the four
    sign-working Callings per its own "you are not a Hexer" text; Hexer/Dark Cultist/Came
    Back Wrong Marks; the Dark Cultist's Patron named at 3rd as the book says, not at 1st;
    Gunhand's Edge bonus combat picks; Edges' ability/edge/skill prerequisites; 3rd-level
    subpaths; per-level Blood rolls; coin rolled on the Ch. X dice and spent only at
    printed prices). Rules data transcribed into `Data/chargen.json` (embedded like the
    rest); `CharGen.Validate` re-derives every figure independently and the smoke suite
    generates + validates ~370 sheets per run (all callings × levels × methods + random
    sweep + Appendix-D-style spot checks). Sheet renders in the pregens' format, four
    questions and Compass included; **→ Posse** seats the soul directly.
  - **Padding/UX pass** (user: words against the window edge don't conform to good UX).
    WinForms RichTextBoxes ignore their own `Padding`, so every text pane was flush to the
    chrome. New `Pad()` host-panel helper wraps the Bestiary reading pane (14px), the
    creature pop-out windows (16px), Reference (14px), Generators output (12px), the New
    Soul sheet (16px), and the Dice log panel (10px).
  - **A fresh start everywhere** (user request): every roster/record now has a confirmed
    clear — new "Clear posse", "Clear ledger", "Clear threads", Bestiary filter "Reset",
    New Soul "Clear", joining the existing Encounter/Tracker/Dice/Generators clears.
  - **Expert UX evaluation** (user request) with two fixes applied: the fixed 1280×820
    startup size exceeded this laptop's 1366×768 working area and clipped the bottom
    button row — now clamped to `Screen.WorkingArea`; and the creature pop-out was
    discoverable only via double-click + tooltip — a visible "⧉ Pop out" button now sits
    on the Bestiary bar. Remaining recommendations recorded in the session notes.
  - **Signed, metadata-complete exe** (user: Windows/firewall/Cortex warnings). New
    `KT/source/sign.ps1` creates/reuses a self-signed **CN=Cole Williams** code-signing
    certificate (10-year, reused across releases so the publisher identity is stable),
    installs it to this machine's LocalMachine Root + TrustedPublisher, signs with SHA-256
    + RFC3161 timestamp, and refuses success unless `Get-AuthenticodeSignature` reports
    Valid. csproj now carries honest metadata (Company/Product/Description/Copyright,
    v1.3.0). Published exe signs Valid and launch-checks clean. (SmartScreen on *other*
    machines still needs a CA cert or reputation — documented in sign.ps1 and README.)
  - Verified: build 0/0; smoke **1,897/0 × 5 consecutive runs**; app launched, all nine
    tabs + generated sheet + padded pop-out screenshot-verified; deliverable re-mirrored
    (stale duplicate root exe dropped) and re-zipped (63.4 MB). Released as GitHub Release
    `keepers-table-v1.3.0` with the signed exe as the release asset (binaries stay out of
    the tree). Branch `session/2026-07-18-kt-padding-chargen`.

- **2026-07-18 — Tracking standardized across all Desktop\Git repos (infrastructure).**
  Changelog moved from CLAUDE.md into this file; current versions tagged (`players-v2.14`,
  `keepers-v2.6`, `bestiary-v2.6` at the books commit, `keepers-table-v1.2.3` at the app-sync
  commit); canonical `autosync.ps1` / `register_autosync_task.ps1` installed (identical in
  every repo: auto-commit always, push only when an `origin` remote exists). Shared
  conventions documented in CLAUDE.md. No book or app changes; versions unchanged.

- **Player v2.14 / Keeper v2.6 / Bestiary v2.6 + app v1.2.3 — content expansion, Serling
  slow-burn pass, whitespace audit, and the app brought in sync (2026-07-18).** Four jobs in
  one session (all user-requested):
  - **Keeper's Table app synced — and a standing rule made of it** ("sync up the app and
    continue to do so"). Reference tab's DC ladder updated to the unified seven-step ladder;
    status bar + README to the current book versions; app version 1.2.2 → **1.2.3**.
    `Data/creatures.json` re-extracted from the current Bestiary with a new repo tool,
    **`extract_creatures.py`** — proven faithful by first re-extracting the *old* HTML and
    diffing against the shipped JSON (0 content diffs), which also revealed and fixed a
    latent gap: the original extraction had dropped the statblock **Mark** line, so 18
    creatures' Mark entries were empty in the app; they're populated now (the Bestiary popout
    already rendered the field). Built + smoke suite **1360/0 locally on Windows** (SDK 9),
    published, deliverable folder re-mirrored, zip rebuilt (63 MB). The standing rule is at
    the top of this doc.
  - **"The Patrons at the Table"** — new Keeper's Book section after The Dark's Wages: a
    veteran-Keeper essay per Patron on how and *when* each approaches players (each waits at
    a different door — want, the question, hurt, the grave, the strike, the flock), plus a
    "veteran's rules" closing note (offer only at the owned moment of weakness, speak through
    intermediaries, one waking Patron per campaign, no must always be a real answer). Indexed.
  - **Items** (Player's Book Ch. X): six new Uncommon Goods (camera & wet-plate kit,
    lead-lined coffin, Pinkerton file on a name, blasting machine & wire, galvanic battery,
    surveyor's transit — first three with mechanical notes); three new lesser relics
    (Coyote's Tooth, Widow's Locket, Church-Door Nail); four new artifacts (the Padre's
    Lantern, the Bone Fiddle, the Meridian Chain, the Ferryman's Dollar). All seven
    relics/artifacts added to the Index.
  - **Serling slow-burn tone pass across all three books** ("modify them as if you were Rod
    Serling… starts out feeling like a typical TTRPG about westerns"). Ch. I restructured to
    enact the descent: it now opens as a straight handbill western and closes with the turn
    (The Three Truths + the survey quote moved to chapter end); the cosmic thesis lines were
    split — "the land is occupied" stays as Ch. I's closing reveal, "it is not peace, it is
    patience" relocated to the Ch. XII narrator block where it lands hardest. A new
    **narrator thread ("the Compiler")** — `.narr` styled blocks, italic with a tilde mark —
    escalates at act boundaries: Player Ch. VII (the threshold), Ch. XII (the reveal), end of
    App. E (the "for your consideration" sign-off); Keeper Ch. I (host-to-host: let the first
    night stay a western), Ch. VI (the campaign quietly changes its nature), Ch. XIII
    ("Submitted for your consideration: one county…"); Bestiary Ch. I (the field-book road
    runs downhill), Ch. V (the remedies stopped mentioning the rifle), Ch. VII ("It has
    already noticed you reading"). No rules text touched.
  - **Whitespace audit** (user granted permission to break tables): new repo tool
    **`audit_whitespace.py`** measures every rendered page's bottom gap and names the block
    that moved. Findings: tables/lists/boxes/statblocks already split; the big gaps are
    deliberate chapter-start page breaks and orphan control (left alone — breaking those
    *would* hurt readability). The real fix: **`.quote` and `.narr` blocks are now
    word-splittable** like paragraphs (shell `isParaLike`), which closed the genuine
    mid-flow gaps (Bestiary flagged pages 11 → 8; the survivors are all intentional breaks).
  Final state: Player **v2.14, 170 pp** · Keeper **v2.6, 88 pp** · Bestiary **v2.6, 131 pp**,
  all render-verified (parity, zero clip, zero h-scroll, anchors resolve, idempotent);
  versioned copies rotated (kept three per book; v2.11/v2.3/v2.3 removed).

- **Build-system reconciliation — one builder per book (2026-07-18)** (user-requested: "the
  Player's Handbook is not built the same way as the other two … reconcile it, and combine the
  two Bestiary py builders into one"). All three books now follow the same pattern — **each
  book is a single `build_<book>.py` that carries its own content and runs standalone**:
  - `build_player.py` now embeds the entire Player's Book HTML as a raw string `SRC` (edit the
    book there); **`player-src.html` is retired** (deleted from the tree; full history in git).
  - `bestiary_extra.py` was **merged verbatim into `build_bestiary.py`** (ordinary beasts,
    `LIVING_LORE`, `sort_sections`, `gen_appendix`) and deleted — adding a creature now means
    editing that one file.
  - `build_keeper.py` and `build_bestiary.py` **read `blood-and-grit.html` directly** — the
    manual `cp blood-and-grit.html <target> &&` step is gone; each book builds with just
    `python build_<book>.py` (player first, since it produces the shared shell).
  - `measure_index.py` now patches the static Index page numbers into `build_player.py`'s
    `SRC` (same regexes, new target file); README, session-start command, and this doc updated.
  **Integrity proof:** every step was verified byte-identical — the converted `build_player.py`
  reproduces `blood-and-grit.html` md5-exact, and the rewired/merged Keeper and Bestiary builds
  reproduce their books md5-exact; `measure_index.py` re-run green end-to-end (168 pp, parity,
  zero true-scale clip, zero h-scroll, idempotent). No book content changed in this step.

- **Player v2.13 / Keeper v2.5 / Bestiary v2.5 — Editorial pass, 19 of 20 findings applied
  (2026-07-17/18).** A cover-to-cover editorial read of all three books produced 20 proposed
  changes, reviewed by Cole in an approve/deny artifact; 19 approved, R3 denied-with-note
  (recorded in `editorial-denials.md`). Applied:
  - **Rules (7).** The two books taught **different DC ladders** — the Player's Book now
    carries the Keeper's finer ladder everywhere (Trivial 10 · Easy 13 · Average 15 · Hard 18 ·
    Very Hard 20 · Punishing 25 · Beyond 30; Ch. II table re-pitched, Appendix C, and the Ch. X
    surgery DC relabeled). The **attack-formula contradiction** ("level + weapon rank" vs the
    Calling tables) resolved in the tables' favor in Ch. II / III / V / XI — attack *and save*
    proficiencies are now read straight from the Calling tables, the +2/+4/+6 rank formula
    applies to skills (the artifact's R2 text said "skills and saves"; the tables show saves on
    their own track, so the installed wording keeps tables authoritative for both). **Ability
    boost timing** unified to one point at **5th and 10th** in Ch. IX and Ch. XIV (per Cole's
    R3 note — the denied proposal had been 4th/8th). Cap-and-ball reload standardized to
    **three rounds** (Ch. XI now matches Ch. X). Both **Grit quick references** completed to
    all five uses (Appendix C + Keeper's Screen). **Venom save DCs** added (Rattlesnake Fort
    DC 13, Great Serpent Fort DC 18). Ch. XII Afflictions prose now points at the Keeper's
    full table.
  - **Prices (5).** Duplicate-row drift fixed: fine saddle horse $90+ both tables, mule $30,
    saddle scabbard $4, bedroll & tarp $2; the Camp & Trail "Saddlebags / panniers" row is now
    "Panniers (pair)" so it's honestly a different good from the $3 Tack saddlebags.
  - **Names (4).** Prospector Edge renamed **"Laid By"** (was a collision with the Pay Dirt
    class feature); the Wendigo's subtitle is now **"the deep winter given a body"** (its old
    subtitle was the Tier III entry's name); its Putting-It-Down line no longer puns on "iron
    heart"; the orphaned PF2E term "fortune bonus" removed from Stack the Odds.
  - **Magnitudes (6 in one).** Vague bonuses given numbers: Herb-Lore +2, Mend the Body 2d8
    per further point, Draw Out the Sickness +4 / 3 Vital Breath to cure, Call Back the Breath
    half maximum Vital Breath (rounded up), Hard Ride +10 ft, Honeyed Word +3.
  - **Style (3).** Three "was X once — until Y" origin pivots rewritten (Hollow Prophet,
    Dollmaker's Children, Stone Giant) to thin the Bestiary's densest formula cluster; nine
    self-praise adjectives stripped from How-to-Play notes ("brilliant"/"fantastic"/
    "masterclass"); the Prospector's two J. Halloran epigraphs differentiated (first byline
    now "testimony given at the Widow's Comfort inquest") so the bookend reads as one story
    in two halves.
  All three books rebuilt and render-verified (Player 168 pp — one page over v2.12 from the
  added lines; Keeper 84; Bestiary 131; parity, zero true-scale clip, zero h-scroll, all
  anchors resolve, idempotent builds; 204 Player index statics re-patched). *(The Keeper's
  Table follow-up flagged here — stale Reference-tab DC ladder and status-bar versions — was
  done on 2026-07-18; see the app-sync entry above.)*

- **Keeper's Table — true single-file standalone (embedded data) + first GitHub Release
  (2026-07-16).** The self-contained exe still needed its `Data/*.json` sitting in a `Data/`
  folder beside it (`creatures.json` is mandatory — the app crashed on launch without it), so a
  lone `.exe` download was broken. Fixed by **embedding the three JSON files into the exe**
  (`<EmbeddedResource>` in the csproj; `Db.ReadData` now reads them from the assembly and falls
  back to `Data/` on disk for the smoke rig / dev build). The published exe is now genuinely one
  file — no runtime, no data folder — and writes only `session.json` beside itself. Verified:
  build 0/0, embedded resources present + parseable (110 creatures, all tables), smoke 1360/1360,
  flagless publish emits exe-only (no `Data/`). Refreshed `publish/` + delivered `app/`, rebuilt
  the zip. **Published the exe as a GitHub Release** (tag `v1.2.2`) since binaries are git-ignored
  and don't belong in the repo tree — this is why the user saw no `.exe` on GitHub before. Done on
  `session/2026-07-16-kt-embed-data-standalone`.

- **Keeper's Table — self-contained single-file publish baked into the csproj (2026-07-15).**
  Made the app's zero-.NET-dependency packaging durable and cleaner. The self-contained flags
  used to live only on the publish *command line* (`-r win-x64 --self-contained true`), so a
  publish that forgot them would ship framework-dependent again — which is exactly what bit the
  very first delivery (it needed the Desktop Runtime installed). Verified the current build was
  already self-contained, then moved the settings **into `BloodAndGritKeeper.csproj`**
  (`RuntimeIdentifier=win-x64`, `SelfContained`, `PublishSingleFile`,
  `IncludeNativeLibrariesForSelfExtract`, `EnableCompressionInSingleFile`) so a bare
  `dotnet publish -c Release` can never regress. Because the app resolves every path via
  `AppContext.BaseDirectory` (never `Assembly.Location`), single-file is safe — the deliverable
  collapsed from **~258 files to a single 69 MB `BloodAndGritKeeper.exe` + `Data/`**. Synced the
  same csproj into the delivered `source/` mirror, regenerated `publish/` and the delivered
  `app/`, and rebuilt `BloodAndGrit-Keepers-Table.zip` (72 → 63 MB). Verified: build 0/0, smoke
  1360/1360, flagless publish produces the single-file self-contained exe. No app version bump
  (build-infrastructure only; behaviour unchanged). Done on
  `session/2026-07-15-kt-selfcontained-csproj`.

- **Infrastructure — relocated under `Desktop\Git\` (2026-07-15)** (user-requested: gather all
  local git repos into one `Git` folder on the desktop). The repo moved from
  `C:\Users\Cole\Desktop\BloodAndGrit` to **`C:\Users\Cole\Desktop\Git\BloodAndGrit`** (alongside
  `TideWatch` and the newly-imported `DebForge`). Two path fixes were needed: `autosync.ps1` had
  the repo root **hardcoded** to the old path (`$repo = "…\Desktop\BloodAndGrit"`), so it now
  derives it from `$PSScriptRoot` — portable, survives future moves (the same fix TideWatch's
  scripts already had); and the `/session-start` command's path was updated. Added the previously
  missing **`register_autosync_task.ps1`** (self-locating, "BloodAndGrit AutoSync"). The "BloodAndGrit
  AutoSync" scheduled task stores an absolute path to `autosync.ps1`, so it must be **re-registered
  from an elevated shell** to point at the new location: `pwsh -File
  "C:\Users\Cole\Desktop\Git\BloodAndGrit\register_autosync_task.ps1"`. Git repo, remote, and
  history are unaffected by the move. Done on `session/2026-07-15-relocate-under-git`.

- **Infrastructure — session-branch workflow (2026-07-12)** (user-requested: changes start on
  a branch, merge to main on success). `autosync.ps1` rewritten branch-aware: it commits and
  pushes whatever branch is checked out (upstream set on first push, rebase against the
  branch's own remote counterpart, detached-HEAD guard) so session branches are backed up to
  GitHub like main. Convention documented under "How I like to work"; full lifecycle
  dry-run-tested (branch → autosync push → `--no-ff` merge → branch deleted local + origin).
  Git global user.name/email configured on the machine — merges need a committer identity.

- **Player v2.12 / Keeper v2.4 / Bestiary v2.4 / app v1.2.2 — Books copyedit pass +
  feathering port + fresh PDFs (2026-07-12)** ("give the same treatment to the three books,
  and since the app quotes from the book, edit it accordingly as well" + "save the most
  recent builds of all books as .pdf and remove older PDF versions"). Three parts:
  - **Feathering paginator ported to sources** (prerequisite — see the resolved-divergence
    note at the top of this doc). The new script block was spliced verbatim from the
    delivered v2.11 into `player-src.html` (plus the `.sb-cont` CSS rule), the version
    cascade tuples in both build scripts were re-anchored, and `pag_patch.py` now detects
    the feathering engine and no-ops. Proof: rebuilt Player's Book was **byte-identical**
    to the delivered v2.11; Keeper/Bestiary matched except line-ending/CSS-position
    artifacts of the old hand-patching (script regions hash-identical).
  - **Copyedit (professor's rules: real errors only; the frontier voice stays).**
    Player's Book: "A Word on the Rules" no longer lists the gun rules as both adapted
    *and* original; a double-"and" list in the Ch. V intro; a double bolt-on "And" in the
    Ch. VI intro; "sickened" → "Sickened" in the Witch's Hex; and **five pregens in
    Appendix D used skills that don't exist in this game** (PF2E leakage: Deception→Deceive,
    Diplomacy→Persuade, Society→Insight, Nature→Animal Handling, Lore (Scripture)→Lore
    (Occult)). Keeper's Book: two stray `</p>` tags in keeper-notes (Ch. II, Ch. XI);
    "call for Presence, Deception, or Intimidation" → "Persuade, Deceive, or Intimidate";
    "better than eighty" creatures → "better than a hundred" (twice; the Bestiary holds
    110); "a name cut in a board hill" → "a boot-hill board" (Ch. I epigraph). Bestiary:
    remarkably clean — one clarification, the ordinary-beasts note now reads *marked "—"
    to say so*. `perdition_map.py` labels checked, clean. **App impact: none of the
    corrected passages live in `creatures.json`/`tables.json` or the Reference tab**, so
    app data is untouched; the app got the version-string bump only (status bar + README →
    v2.12/v2.4/v2.4, csproj 1.2.2), build 0/0, smoke 1360/1360, republished + re-zipped.
  - **Verification & PDFs.** All three books rebuilt idempotently (double-build md5) and
    render-verified: Player 167 pp (feathering absorbed 8 pages vs. the old 175; 204 index
    statics re-patched), Keeper 84 pp, Bestiary 131 pp — desktop/mobile parity, zero
    true-scale clip, zero h-scroll, all `toc2`/`ix` anchors resolve. `make_pdf.py`
    recreated for the Windows toolchain (it existed only on the old Linux box) and all
    three PDFs regenerated in place over the stale v2.11-era set, PyMuPDF-verified
    (167/84/131 pages, 612×792 pt).

- **Keeper's Table v1.2.1 — Copyedit pass over the UI (2026-07-12)** ("go over the user
  interface and correct any spelling or grammatical errors as if you were an English
  professor"). Reviewed every user-facing string in `MainForm.cs`, `Tabs.cs`, `Core.cs`,
  `Program.cs`, `README.md`, and `Data/tables_extra.json`, checking Reference-tab text
  against the books before touching it (book wording wins). Fixed:
  - *Recovering Nerve* (Reference): "…or a point of Grit each buy back a measure." had
    dropped the book's modal — restored "**can** each buy back a measure **of steadiness**"
    (with "or," the bare "each buy" is a subject–verb agreement error).
  - *Nonlethal* (Reference): "declare it before the roll; fists and clubs do so by
    default, most other arms take −2…" — "do so" pointed at "declare it" and the comma
    spliced two clauses. Now mirrors the book: "declare before the roll that you strike
    nonlethally; fists and a club do so by default; most other arms take −2…".
  - *Grit* (Reference): "act while Bleeding Out, or shrug a condition" — "Bleeding Out"
    is not a book term (the conditions are Bleeding/Dying) and "a condition" overstates
    the book's "a fright." Rewritten to the Player's Book Ch. II list (add 1d6 / re-roll /
    refuse to fall / shrug a fright / soften a crit fail). Matching fix to the Posse tab's
    Spend-Grit tooltip.
  - Dice-tab parse error: "try like 2d6+3" → "try something like 2d6+3."
  - Tracker empty-state: "pick a foe … or drop **them** in" → "drop **one** in"
    (pronoun agreement).
  - Encounter empty verdict still said creatures could only be added from the Bestiary
    tab (stale since the v1.2 on-tab picker) — now "add creatures above, or send them
    over from the Bestiary tab."
  - Status bar + README book versions were stale (v2.10/v2.2/v2.2 → v2.11/v2.3/v2.3).
  Book-extracted text (`creatures.json`, `tables.json`, Reference wording that matches
  the books) deliberately left as the books print it. Loop: build 0/0 → smoke 1360/1360 →
  publish → delivered `app/` + `source/` synced → zip rebuilt (68.9 MB) → launch-checked
  (no `startup-error.txt`). **Discovered while proofing:** the built books on disk are
  v2.11/v2.3/v2.3 with a feathering paginator that never made it back into the lean
  sources — see the ⚠️ OPEN ISSUE at the top of this doc.

- **Infrastructure — GitHub sync live (2026-07-12).** The project now lives in a **private**
  repo: https://github.com/cwgilgalad/blood-and-grit (account `cwgilgalad`, HTTPS). Local
  `main` tracks `origin/main`; auth is the GitHub CLI (`gh auth setup-git` wired
  `gh auth git-credential` in as git's credential helper for github.com, token in the Windows
  keyring, so headless pushes work). The **"BloodAndGrit AutoSync" scheduled task** (every
  30 min + at logon, running `autosync.ps1`) commits & pushes any local changes — so edits
  made on the laptop reach GitHub within half an hour with no manual step. `.gitignore`
  excludes regenerated build output, the ~160 MB delivered `app/` folder, the deliverable
  zip, and per-table runtime state (`session.json`); the lean sources, build scripts, books,
  and `KT/source` + `KT/smoke` are all tracked.

- **Keeper's Table v1.2 — Seven-tab feature pass** (the user's own wishlist: dice animation,
  bestiary pop-outs, a comprehensible Encounter tab, tracker foe dropdown, bigger generators,
  bigger reference, a clearer Session tab, then a logic review). All built, 1360/1360 smoke
  asserts green, and every feature launched and screenshot-verified on the Windows laptop:
  - **Dice tray** (Dice tab, above the roll log): every roll — expression, quick dice, d20
    check — tumbles owner-drawn dice for ~½ s and settles on the true per-die faces (new
    `Rules.RollExprFull` returns `(sides, value, sign)` per die; fonts cached, panel
    double-buffered; max face rings verdigris, a natural 1 rings red; 8 dice shown, "+N more").
  - **Bestiary pop-out windows**: double-click a creature → its own resizable, maximizable
    window with A−/A＋ text zoom and → Tracker; one window per creature (re-focused if open),
    cascade-placed; replaces the old single reused card, and the Tracker/Encounter
    double-click cards now use the same windows.
  - **Encounter tab de-mystified**: an "Add a creature" type-ahead picker (× N) on the tab
    itself, budget line reworded ("4 pts per soul in the posse (Posse tab)"), and an
    empty-state overlay that explains the whole loop (plan → verdict → Send all → Tracker).
    (The "can't add souls" confusion was real: adding lived only on the Bestiary tab.)
  - **Tracker Foe box**: the same type-ahead creature picker (× N) directly on the Tracker
    bar, so foes can be fielded without leaving the tab.
  - **Generators expanded**: new `Data/tables_extra.json` (merged after `tables.json` by the
    new `Db.MergeTables`, deliberately a separate file so book re-extraction can't clobber
    it) — new entries for all 13 simple tables (~10 towns, 24 NPC names, 8 wants, 8 tells,
    12 rumors, 8+8 trail, 8 plunder, 10 omens…) plus 2–6 new entries per terrain ground and
    4 new Hand-Behind-It villains, all in the book's voice and all naming real Bestiary
    creatures (smoke-asserted so the safe-table rule keeps firing).
  - **Reference doubled**: added the DC ladder, a turn in the Iron Code, Blood/Dying/Grievous
    Wounds + the d6 Lasting Injury table, the complete Appendix-B Conditions table,
    Recovering Nerve, and the Sign DC formula — all faithful to the books.
  - **Session tab**: "Stamp the date" ledger button, an always-visible explainer under
    Threads & clocks, trouble-pattern suggestions in the New-thread dialog, ✎ rename per
    clock, and the ledger title now admits it also autosaves every five minutes.
  - **Real layout bug found & fixed while verifying**: the top action bars (Bestiary
    filters, Posse, Encounter, Tracker) were fixed-height FlowLayoutPanels — at panel widths
    where the controls wrap to 3+ rows, the overflow row was silently clipped (the Bestiary's
    🎲 Random / → Encounter / → Tracker buttons were invisible at default window size). All
    four bars are now `AutoSize = true`.
  - Housekeeping: status bar book versions corrected to v2.10/v2.2/v2.2 (was stale at
    v2.9/v2.1), csproj `Version` 1.2.0, README rewritten for v1.2, smoke rig now loads
    `Data/` and rolls forward to the machine's .NET 9 runtime (`RollForward` — test rig
    only). **Note:** the delivered zip is fully v1.2; the unzipped
    `BloodAndGrit-Keepers-Table\app\` folder was still running v1.1 during the session, so
    a background waiter syncs it from `KT/source/publish` the moment that instance closes —
    if it didn't get the chance, re-copy `KT/source/publish\*` over `app\` by hand.

- **Player v2.10 / Keeper v2.2 / Bestiary v2.2 — Navigation + the sample county.** Three things,
  all built and render-verified on the Windows/Edge toolchain (`measure_book.py`, new general
  verifier; `measure_index.py` for the Player's Book):
  - **Detailed two-level Contents in all three books.** A shared `nav_tools.py:add_detailed_toc()`
    regenerates each book's simple chapter TOC into a flat, splittable `<ul class="toc2">` listing
    chapters + their `<h2>` sub-heads, generated from the assembled HTML at build time so it can
    never drift; page numbers resolve live. Two paginator facts pinned down doing this: `.toc`
    lists are deliberately *non-splittable* (they move whole — hence the new class `toc2`, which
    the split-fill code treats like the `.ix` index and flows across pages), and the paginator
    stamps a `<section>`'s id onto its *first block*, so a section-opening `<h2>` must be indexed by
    its section id, not a fresh one. Also corrected the clip test to force `zoom:1` on **each
    `.page`** (the note always said to; the script had been setting it on the container, which
    produced phantom ~20px "clips" on many-line TOC pages).
  - **Indexes for the Keeper's Book and Bestiary** (the Player's got one in v2.9), via
    `nav_tools.py:build_index()`. The Bestiary index auto-lists all 110 creatures (drift-proof) +
    curated terms; the Keeper index is curated craft/campaign/Perdition-Basin entries. New section
    `id="bookindex"` (the Bestiary's Roll-by-Tier appendix keeps `id="index"`).
  - **Perdition Basin — a worked sample county** (the biggest published-games gap on the old
    roadmap). One dry county whose spine is the padres' failing silver "nail" bindings on the wells
    (deliberately the Ch. XI Salt Valley seed, drawn out), with **Coffin Wells** (Ch. IX) and
    **Saltlick Station** (Ch. X) as two of its keyed sites. `perdition_map.py` draws a **two-layer
    inline-SVG map** from one coordinate model: a clean, secrets-free **player map** (Player's Book
    Appendix E, an in-world gazette) and a secrets-annotated **Keeper map** (Keeper's Book Ch. XIII,
    the full gazetteer — locations, three factions, the well-by-well campaign clock, ties to both
    adventures). The First Peoples (the Painted Mesa) are written as people with agency and
    grievance, not mystical props. Pages: Player 172→175, Keeper 77→89, Bestiary 133→136 (detailed
    TOC accounts for the first few pages each; the map/gazetteer for the Keeper's larger jump). All
    three pass parity / zero-clip / all-anchors-resolve / idempotent.

- **Keeper's Table v1.1 — Tracker/Posse flexibility pass** (in response to "more features on
  the GUI that make the program more flexible," with the Tracker's missing reset as the model).
  Added, all built and visually verified by launching the app natively on the user's Windows
  laptop (build clean 0/0; 930/930 headless logic assertions still green since `Core.cs` was
  untouched):
  - **Tracker "New fight"** — clears the foes, keeps the posse on the field, wipes per-fight
    conditions off the survivors, and resets to Round 1. This is the headline fix: "Clear field"
    (full wipe) was the only reset before, so you couldn't line up the next encounter without
    nuking and re-sending the party. Confirmed working on-screen (3 foes cleared, 2 PCs kept,
    Round 3→1, Frightened cleared).
  - **Flexible Sort ▾** — the old single "Sort" (always init-desc) is now a dropdown: Initiative
    high→low / low→high, Name A→Z / Z→A, Blood most→least / least→most. It commits any half-typed
    Init before sorting and refreshes the grid. The last mode sticks; "Roll initiative" forces
    init-desc.
  - **＋ Add** (Tracker) — an ad-hoc combatant/NPC dialog (name, Blood, Defense, PC? flag) for
    anything not in the Bestiary.
  - **× N quantity** on the Bestiary "→ Tracker" — drop several copies of a foe at once (numbered
    #1..#N; a lone first copy stays unnumbered, preserving prior behavior).
  - **＋ Condition ▾** (Tracker) — tag the selected combatant with any Appendix-B condition from a
    menu (Frightened/Slowed offer their steps; a valued step supersedes its siblings), plus a
    "— Clear all —" entry, instead of free-typing the Conditions cell.
  - **Rest ▾** (Posse) — a long rest restoring Blood **and** Nerve to full, whole-posse or
    selected soul (the old "New session" only did Nerve + Grit; Blood had no bulk restore).
  - Implementation: a shared `MenuBtn(text, w, tip, params (label, handler)[])` dropdown-button
    helper in `MainForm.cs` (a "-" label → separator) backs Sort, Condition, and Rest. The
    Tracker toolbar is now two rows (`SetFlowBreak`). Also fixed a stale status-bar string
    (Player's Book v2.8 → v2.9). **Discovered and reconciled a two-source-tree divergence** — see
    the Keeper's Table "Source-tree layout" note above; `KT/source` is now the single master and
    the delivered `BloodAndGrit-Keepers-Table/` + zip were regenerated from it (so the shipped
    build now also finally carries last session's uncommitted autosave-timer and two-tier
    crash-recovery work). Republished self-contained (win-x64, ~67 MB zip); published exe
    confirmed to launch standalone with no `startup-error.txt`.
- **Player v2.9 — Added the Index.** A full back-of-book index as a new section after The Ledger:
  ~200 entries (every rule concept, all 17 Callings, all 10 Origins, all 29 general Edges by name,
  all 8 Signs, all 5 Old Rites, all 14 relics/artifacts by name), two-column with letter heads and
  dotted leaders in the TOC's design language. Implementation: ~168 anchor ids (`ix-*`) added to
  headings, list items, and table rows across `player-src.html`; entries use the TOC's
  `<a href="#anchor">…</a><span class="pg">` structure, so **the existing paginator resolves every
  index page number live at render time** — no JS changes needed, and the numbers can never drift.
  A one-shot (`add_index.py`, kept, do-not-re-run) baked it all in with assert-guarded string
  edits. The extra Contents line overflowed the contents page (the paginator moves an unsplittable
  `.toc` list whole), fixed by tightening `.toc li` padding 2px — contents is one page again.
  Cascade done (`v2.8→v2.9` match strings in both other build scripts); Keeper/Bestiary rebuilt on
  the new shell and verified unchanged (74/132 pages as rendered here, covers still v2.1, no index
  leakage — note the Bestiary's own "Roll, by Tier" appendix has always used `id="index"`, which is
  fine since the Player index is spliced out of the other two books). Verified via headless Edge
  (`measure_index.py`, kept as a tool): 169/169 desktop/mobile page parity, 0 clipping at true
  scale, 0 h-scroll at natural zoom, no unresolved anchors, idempotent double-build. **Discovery
  worth keeping: pagination is environment-dependent** — the untouched v2.8 renders 164 pages on
  this Windows laptop vs 163 on the old Linux environment (one extra page inside Ch. XI; Keeper
  73→74, Bestiary 130→132 likewise) purely from platform font metrics. Live-resolved page numbers
  make this harmless; static fallbacks are approximate by design. Also this session: recreated the
  missing `build_player.py` on this machine (verified byte-identical output against the delivered
  v2.8 file) and installed real Python 3.12 + Playwright for the Windows toolchain.
- **Keeper's Table v1.0 — Ampersand mnemonic fix (first real visual verification pass).**
  Ran Claude Code CLI natively on the user's Windows laptop for the first time — built and
  actually launched the app, screenshotted all 8 tabs. Everything rendered correctly (palette,
  wiring, layout, DPI) except two labels that silently swallowed their `&`: WinForms treats a
  bare `&` in a `Label`/`GroupBox` `.Text` as a mnemonic-accelerator prefix (underlines the next
  letter, drops the `&`), so "Roll & event log" (Dice tab) rendered as "Roll  event log" and
  "Threads & clocks" (Session tab) rendered as "Threads _clocks." `Button.Text` has the same
  behavior, but the one existing button label with an ampersand ("Plunder & finds") had already
  been correctly escaped as `&&` — only the `Label` in `MainForm.cs` and the `GroupBox` in
  `Tabs.cs` had been missed. Fixed both by escaping to `&&`; re-verified both tabs render the
  ampersand correctly post-fix. Republished self-contained and re-zipped. No other layout/DPI
  issues found across the eight tabs.
- **Keeper's Table v1.0 — Crash fix.** A real Windows launch threw
  `SplitterDistance must be between Panel1MinSize and Width - Panel2MinSize` in
  `BuildDiceTab()`, immediately on startup — every tab using a `SplitContainer` had the same
  latent bug (geometry set before the control was laid out). Fixed by introducing a
  `Split()` helper that defers `SplitterDistance`/min-sizes to the control's first real
  `SizeChanged` event; applied to all four affected tabs (Dice, Bestiary, Generators,
  Session). Republished self-contained. This class of bug is now flagged as a standing
  landmine in this doc's Keeper's Table section so it isn't reintroduced.
- **Keeper's Table v1.0 — Full logic & UX audit** (in response to "check the logic, make
  sure the UI follows best practices, make sure everything is wired up"). Found and fixed
  real bugs: the four-degrees stepping logic had a signed-band gap at zero that made a
  natural 20 on a failing roll register as a *critical failure* instead of stepping up to
  success — rewritten on an ordered 0–3 scale with regression tests locking both edge
  cases. Made `PartyMember`/`Combatant`/`CampaignClock` implement
  `INotifyPropertyChanged` with clamped setters (Mark 0–6, Taint 0–4, Grit 0–9, Blood/Nerve
  ≥ 0) — they were plain classes in `BindingList`s before, so model edits made in code
  didn't reliably reach the grids. Added Nerve auto-recompute (`RES + level`). Made
  Tracker↔Posse Blood sync two-way (was one-way). UX rewrite: replaced blocking prompt
  dialogs for Damage/Heal/Dread with inline spinners on each tab's action bar; added
  danger-colour coding (Blood/Nerve amber under a third, red at zero; Mark/Taint as filled
  pips; downed/PC row tinting on the Tracker); confirmations on all destructive actions;
  numeric-cell input validation; Ctrl+1–8 tab shortcuts; Enter-to-roll; tooltips on every
  button; a themed New-Thread dialog with Cancel; an encounter-budget progress bar; and a
  consistent frontier-book palette replacing the plain spreadsheet look. Verified: clean
  build, 34/34 headless logic tests, static wiring audit (43 buttons, 10 inputs all
  confirmed connected).
- **Keeper's Table v1.0 — Initial build.** Built "Blood & Grit: The Keeper's Table," a
  C#/.NET 8 WinForms desktop app, from scratch: 8 tabs (Posse, Dice, Bestiary, Encounter,
  Tracker, Generators, Reference, Session), all 110 creatures and 22 tables extracted from
  the rendered books into JSON, session autosave/autoload, Appendix D pregens seeded on
  first run. Cross-compiled for `win-x64` using the official Microsoft .NET SDK (the Ubuntu
  apt package lacks WindowsDesktop targets). Delivered as a zip with a framework-dependent
  build; later republished self-contained (see the crash-fix entry above) after a user
  report showed the framework-dependent build wouldn't launch without the exact Desktop
  Runtime installed.
- **Keeper v2.1 / Bestiary v2.1 — Cross-book consistency audit.** Checked all rules numbers,
  creature references, chapter cross-references, and formulas across the three books. Fixed
  five inconsistencies: (1) Keeper's Alienist reference pointed at Ch. IX (Edges) — the
  Alienist is a Sawbones art, now cited as Player's Book Ch. V; (2) Keeper's Taint-clock
  reference said Chapter XIII — the Taint lives in Ch. XII (Nerve & the Uncanny); (3)
  Keeper's Threat-by-Tier Tier-I Dread cell said "—/10" while the Bestiary workshop and the
  actual stat blocks run — / 10–13, now aligned; (4) Grounds appendix "The Servant of the
  Deep Dark" → entry's real name "Servant of the Deep Dark"; (5) Grounds villain picker
  "The Hollow Prophet & his flock (III)" → the actual entry "Dark Cultist & the Hollow
  Prophet (II–III)". Verified consistent: Threat-by-Tier combat numbers, encounter budget
  (4 pts/PC; mook 1 / standout 8), Nerve = RES + level, Sign DC formula, Grit 3/session,
  Mark six steps, silver ammo in Ch. X, all 90 Grounds creature references, Bestiary→Keeper
  Ch. III/IV references, and the pregens' Signs. Page counts unchanged (73 / 130).
- **Bestiary v2.0 — Whitespace pass.** Registered `.creature` as a splittable block in
  `pag_patch.py` so creature entries flow continuously and split across page boundaries
  (with "(cont.)" headers, stat blocks kept intact, no orphaned headings). Bestiary
  148→130 pages; mean trailing whitespace 238→106px; big gaps 61→18 (mostly chapter-ends).
  Bestiary-only bump (no Player cascade). Keeper unaffected (no creature entries).
- **Player v2.8 / Keeper v2.0 / Bestiary v1.9 — Added more quotes.** Player: 4 new chapter
  epigraphs (III Making a Character, IX Edges, A Example of Play, B Conditions). Keeper:
  epigraph for the Screen appendix (added `screen` to `_chq`). Bestiary: 5 in-voice
  **witness quotes** on iconic creatures (Risen, Nightwalker, Skin-Walker, Thunderbird,
  Wendigo) via a new `witness=` param on `creature()`. Pages: Player 162→163, Bestiary
  143→148, Keeper 73. TOCs re-measured.
- **Player v2.7 / Keeper v1.9 / Bestiary v1.8 — Removed all 18 Player's Book plates** for
  cross-book design continuity (Player only; images retained unused in `assets/`). Player
  169→162 pages, ~5.4 MB→~0.40 MB.
- **Player v2.6 — Fixed Opal Vance** in the posse from Witch to **Hexer** (fits her Mark 1
  and bargain backstory); abilities/derived stats unchanged. Player only.
- **Player v2.5 / Keeper v1.9 / Bestiary v1.8 — Cover subtitle font** restyled to match the
  top kicker (EB Garamond small-caps, bold, upright, 24px). All three (shared shell).
- **Player v2.4 / Keeper v1.8 / Bestiary v1.7 — Removed the parchment page texture**
  (`img01.png`) from all three; pages now flat `--paper` + vignette. **Made the emblem's
  rifle-lever holes transparent.**
- **Player v2.3 / Keeper v1.7 / Bestiary v1.6 — Lowered/centered the cover emblem** in the
  blank lower cover area (flexbox `margin:auto`). All three (shared shell).
- **Player v2.2 / Keeper v1.6 / Bestiary v1.5 — Replaced the cover emblem** with
  `assets/img20.png` (raster steer-skull + crossed rifles, transparent background). All three.
- **Player v2.1 / Keeper v1.5 / Bestiary v1.4 — Re-laid-out the Player's 18 plates** for
  spacing (min gap 7, most 9–13) and thematic section fit.
- **Player v2.0 / Keeper v1.5 / Bestiary v1.4 — Playability pass.** Player: Appendix D
  pregens. Keeper: Ch. XII rollable tables (and Ch. XI Keeper's Year). Bestiary: The Grounds
  + Building Your Own Dead appendices, plus the creature-lore expansion to all 110 entries.

*Current as of the July 2026 sessions. Versions: **Player's Book v2.14 · Keeper's Book v2.6 ·
Bestiary v2.6 · The Keeper's Table app v1.2.3 (self-contained, crash-hardened).***
