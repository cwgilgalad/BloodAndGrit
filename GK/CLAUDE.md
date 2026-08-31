# GritKeeper — the C# app

Loaded whenever work touches anything under `GK/`. Split out of the root `CLAUDE.md` on
2026-07-30: it was ~35,000 characters of app detail sitting in every session's context, including
sessions that never opened a `.cs` file. The root file keeps the two landmines that can ruin a
release (`SplitContainer` geometry, `dotnet publish -o`) and points here for the rest.

A standalone Keeper-facing utility for running games at the table, built in **C#/.NET 10, Windows
Forms**. Not part of the HTML book pipeline — separate source tree, separate build. **Renamed from
"The Keeper's Table" to GritKeeper in v1.5.0** — exe `GritKeeper.exe`, product/title/About/README
all updated; the **internal namespace stays `BloodAndGritKeeper`** (deliberately — embedded-resource
names derive from it). As of 2026-07-19 (v1.6.0) the folders match the name too: working tree
**`GK/`** (was `KT/`), delivered folder **`GritKeeper/`**, zip **`GritKeeper.zip`**. The last
"Keeper's Table" strings inside the app (session file-dialog filters, crash-report captions) were
also renamed in v1.6.0.

## Source-tree layout (read before editing the app)

The working/master tree is **`GK/`**, and since v1.28.0 it holds **three** projects:
`GK/rules/` (the `net10.0` rules library — the eight headless `.cs` files and `Data/*.json`),
`GK/source/` (the WinForms app: the UI `.cs`, its `.csproj`, `app.ico`, `Assets/`), and
`GK/smoke/` (the headless logic-test project). The app and the smoke rig both reference the
library. **Edit `GK/rules` for rules and data, `GK/source` for UI; build/test in `GK/`.**

**Which tree does a change belong in?** If the smoke rig should be able to test it, it goes in
`GK/rules` — that is now the whole criterion, and it is enforced by the compiler rather than by
remembering to add a line to `smoke.csproj`. Anything touching `System.Windows.Forms` or
`System.Drawing` cannot go there and belongs in `GK/source`. (This is why `Rules.ResetForNewFight`,
`MapGen.SettingTerrains` and `Db.RollAdventure` live where they do — logic that sat in `Tabs.cs`
was untestable, and that is exactly how the v1.24.2 `NewFight()` bug escaped.)

**The build output is `GK/source/bin/Release/net10.0-windows/win-x64/` — RID-qualified, and the
assembly is named `GritKeeper`, not `BloodAndGritKeeper`.** The published single file lands in
`…/win-x64/publish/GritKeeper.exe`, which is what `sign.ps1` and `package.ps1` default to. There
is no `GK/publish/` and no `GK/source/publish/`; both were stale paths from older flows and were
cleared out on 2026-07-26 (`GK/publish/` still held a 155 MB Jul-22 exe). A run of Jul-12
`BloodAndGritKeeper.{exe,dll,pdb,…}` files one directory up from `win-x64/` went with them —
they were a v1.2.2 build under the old assembly name, and running one by mistake looks exactly
like the app hanging.

The `GritKeeper/` folder is the *packaged deliverable*, and **both halves of it are generated
build output, not source** — `source/` is a mirror of `GK/source`, `app/` holds the published
build, and the pair is zipped to `GritKeeper.zip`. Since 2026-07-23 `GritKeeper/source/` is
**git-ignored** (it was previously tracked as a byte-identical second copy of `GK/source` —
2,900 lines of C# sitting in git for no build reason). Only `GritKeeper/README.md` is still
tracked there.

**Don't edit the delivered folder directly** — the rule hasn't changed, but the reason has.
It used to be "the two trees will diverge"; now it's simply that your edits get overwritten
by the next `robocopy` at package time and were never in git to begin with. `GK/source` is
the only source of truth. (History note: as of 2026-07-10 these two trees *had* silently
diverged — `GK/source` carried post-delivery work the zip never got. Making the delivered
copy generated-only closes that seam for good.)

## Universal Undo/Redo (v1.6)

Snapshot-based, over the same `GameSession` shape File → Save/Load already uses: the seven
`BindingList`s each push a JSON snapshot onto an undo stack on any `ListChanged`
(add/remove/edit), capped at 50 deep; `Undo`/`Redo` restore via `ApplySession`, which
suppresses re-capture during its own bulk rebuild so a restore is one step, not N.
Reachable from **Edit ▸ Undo/Redo** (Ctrl+Z/Ctrl+Y) or matching buttons pinned in the
status bar, so it's live no matter which tab is open.

**The one invariant, and the only bug class this has ever had.** Once a change has settled,
`undoBaseline` equals the current snapshot. Anything that is *in* `Snapshot()` and captures
by no route breaks it — and the way it fails is not "undo does nothing". The stale baseline
sits there until the **next** captured action pushes it, so undoing that action silently
reverts the uncaptured change as well. v1.47.0 found three fields like that (session notes,
the round, the encounter level) and v1.48.0 found three more (`FeatureSpent`, `TallyOwed`,
and the whole `Sheet` — all mutated through their own objects, which fire no
`PropertyChanged`).

Three rules came out of those two releases, and they are the whole of what keeps this true:

- **Capture where the mutation happens, never at the call sites.** `round` is a property
  with a capturing setter; `mapMarkers` is a `BindingList`; a soul's side-stores announce
  themselves through `PartyMember.Touched`, called by `CharGen.SpendFeature`,
  `UnspendFeature`, `RefreshFeatures`, `TakeTally` and `ForgiveTally`. Before that the
  markers' capture rested on **fourteen** hand-written call sites. A rule that depends on
  fourteen people remembering has a date on it.
- **Announce AFTER the mutation.** Notifying first tells the app to look at a table that has
  not changed yet, and with no window handle to defer through — the self-test rig, and any
  early-startup path — the capture happens on the spot and the real change lands behind it,
  unseen. `AuditUndo` caught exactly this in v1.48.0's own first attempt.
- **Session notes DO capture — on `Leave`, not per keystroke.** The original reasoning (a
  snapshot per keystroke would flood a fifty-deep stack in one sentence) was right and still
  stands; what it missed is that notes are in `Snapshot()`, so declining to capture them did
  not exempt them from undo, it made them collateral. One step per finished edit, and a
  typist mid-word still gets the textbox's own native undo.

**`MainForm.AuditUndo()` is the guard, and it runs in `--selftest`.** It walks every field of
the session, changes it *through the path the app uses*, and checks the baseline kept up —
then makes a change, undoes it, redoes it, and checks the bytes come back both ways. Probe
through the real mutator or the probe proves only that the probe works: driving a raw list
behind the UI is how the map markers once passed a check they should have failed.

## The ten tabs

Per-version feature history lives in `CHANGELOG.md`, which is the version record; what follows is
what each tab *is*, plus the decisions worth not re-deriving.

- **Posse** — full party sheet (Blood, Defense, saves, Nerve, Grit, Mark 0–6, Taint 0–4),
  **＋ Add soul ▾** (v1.52.0, G7: build one by hand through the soul wizard, roll one at a level and
  Calling you pick, take the New Soul tab's sheet, or a blank row for typing a paper sheet in — all
  four land through one `SeatSoul`), inline damage/heal spinners, Spend Grit, Mark/Taint advance, per-soul or whole-posse Dread Checks with
  the real Nerve-loss ladder, New Session reset, Rest ▾ (long rest), send-to-Tracker, ▲▼ reorder,
  a **Gender** column (persisted), double-click for a soul's Ledger window or the Notes editor, and
  **✦ Level up** — a dialog offering only what the new level unlocks, drawn from the generator's
  eligibility helpers. Backed by `CharGen.LevelUp`, which clones the sheet and appends exactly the
  new level's growth (lower levels byte-stable, result `Validate`-clean).
- **Dice** — expression roller (`2d6+3`) with a builder keypad; pure logic in
  `Rules.ExprAddDie`/`ExprAppend` (smoke-tested). Quick dice, a d20 four-degrees checker, a shared
  roll/event log, and an owner-drawn dice tray settling on the true per-die results from
  `Rules.RollExprFull`. Every die wears its colour (d4 green · d6 blue · d8 orange · d10 white ·
  d12 yellow · d20 red · d100 purple); the roll log is colour-coded by degree (`StyleRollLog`).
- **Bestiary** — all **175 creatures**, machine-extracted from the rendered Bestiary HTML, so
  lore/stats/witness quotes/keeper notes are word-for-word faithful to the book. Search, tier and
  chapter filters, one click to Encounter or Tracker, double-click to pop a creature into its own
  resizable window with A−/A＋ zoom — one window per creature, reused if open, cascading placement.
- **Encounter** — the book's budget math (4 pts/PC; mook 4 · even foe 8 · standout 16, from `Rules.BudgetRungs`) costed live
  against party level, verdict bar, safe-table rule flagged. Type-ahead picker (× N) on the tab,
  and an empty-state hint explaining what the tab is for.
- **Tracker** — initiative, rounds, damage/heal (two-way synced with Posse), conditions,
  double-click combat cards, flexible Sort ▾, ＋ Add, ＋ Condition ▾, New fight, Clear field.
  Several things here are load-bearing:
  - **The safe-table rule runs here.** Every route onto the field funnels through
    `AddCreatureToTracker`, which asks `Rules.SignOnly(tier, partyLevel)` first; a horror two or
    more Tiers over the posse offers to go on the **trail** instead of the field.
  - **A sign is NOT a tracker row** — it lives in its own `signs` BindingList (persisted as
    `GameSession.Signs`; traces saved inside `Tracker` migrate out on load) and draws in the
    THREADS ON THE TRAIL strip. **Rebuild the strip with `RefreshThreads()`** after anything that
    touches `signs` or a clock.
  - **Signs, Miracles and creature powers are tracked where they land.** A soul offers only what
    is on their sheet; **a creature offers the power its Bestiary `special` line names**
    (`Rules.ParsePower` — all 150 entries are written "Short name. What it does.", so the parse
    depends on that shape holding). `Rules.ParseCost` pulls the printed cost apart, so working a
    Sign spends the real pools. The effect rides on the **target** as `Combatant.Worked`.
    `RoundsLeft = -1` means "until it is ended", which is what the book's "for a scene" is.
  - **▶ Next turn** (Ctrl+Space) hands the turn on by initiative and rolls the round over by
    itself. `Combatant.HasActed` is the spine; `Rules.NextUp`/`CanAct`/`RoundSpent`/`NewRound` are
    the pure logic — the downed are skipped, traces never counted, the dead never handed a turn, and
    a soul standing on Grit **is** (see *Dying, bleeding and death*). The round is a **spinner**,
    not a label: the app keeps it, the Keeper can correct it. `Rules.BleedOut` runs on the same
    rollover and every result it returns is logged by name.
  - **The field repaints because the FIELD CHANGED**, not because a caller remembered:
    `tracker.ListChanged` invalidates the grid, wired once where the grid is built. `SortTracker`'s
    trailing `Refresh()` is one call site of several and does nothing while the tab is hidden — and
    the tab is hidden on the commonest route there is, since *Send all → Tracker* is a button on the
    **Encounter** tab.
  - **One ordering, and it lives in `Rules.InTurnOrder` (v1.35.0).** `Init desc → souls first →
    name, ordinal`. Both the grid's init sort and `NextUp` read it, and **nothing else may sort the
    field by initiative.** They used to differ on the last tiebreak — the grid put souls first, the
    turn went alphabetical — so the two agreed until somebody tied, and then the turn jumped to a
    row that was not the next one down. A Keeper reported it as the app ignoring initiative. Two
    orderings for one order is the same bug as two authorities for one number.
  - **Anything that changes a place in the order has to move the row.** `AddToField` seats an
    arrival by its rolled initiative instead of appending it (`ArrivalInit` gives it a real one
    whenever the field has rolled, and it was then landing at the bottom of the grid regardless),
    and a hand-typed Init re-sorts on `CellEndEdit`, deferred through `BeginInvoke` so the grid is
    out of its edit cycle before the list underneath it is rebuilt. Before anybody has rolled,
    every Init is 0 and the hand-built order is the Keeper's — leave it alone.
  - **Every button in the app is `FlatStyle.Flat`** as of v1.33.0 — `Btn` dresses it that way, and
    `PrimaryBtn` / `DangerBtn` / `QuietBtn` are that same face with different ink. Flat is the only
    style that honours `BackColor` and `FlatAppearance` at all; under the old `FlatStyle.System` a
    button could not be coloured, which is why those variants had to switch it themselves. Anything
    built by hand rather than through a helper — every dialog's OK and Cancel, every checkbox and
    radio — is caught by **`MainForm.DressControls`**, a walk run from `Sheet.OnLoad` and from
    `RealizeTab`; it only touches controls still on a system `FlatStyle`, so a coloured or
    already-dressed control keeps its own face. In the grid, an editable column carries ✎
    in its header and its cells stand on ground lifted 42% toward paper by `Writable(color)`,
    applied *after* the row colour so it composes with posse green / foe rust / acting gold.
    Only the Tracker gets this: every Posse column is editable, so marking all eighteen is noise.
- **Map** — seeded procedural frontier surveys: ground × scale × hour × water, with
  trail/rail/settlement/grid/secrets toggles. Deterministic per seed. Exports SVG and a one-page
  landscape-Letter PDF — the GDI preview, the SVG and the PDF all replay the same primitive list
  (`MapGen.Generate` → `Prim[]`), so they always match. Zoom & pan, tactical markers (map-model
  coords in `session.json`, so they survive reseeds), draggable ✥ Landmarks and Secrets.
  **Per-feature random streams** (`R(salt)`): one shared stream used to make any overlay toggle
  reshuffle the whole map, so every checkbox is now pure ink-on/ink-off. Rivers/trails are
  **clipped to the inner neatline at generation** (`ClipPolyline`) — they are deliberately
  generated overshooting, and the SVG viewBox used to hide what the preview and PDF showed.
- **New Soul** — a strictly-by-the-book character maker: Ch. III's eight steps at any level 1–10,
  both ability methods, all 19 Callings and 16 Origins with their cross-constraints honored.
  Rules data lives in **`Data/chargen.json`**, transcribed from the Player's Book.
  `CharGen.Generate` builds, `CharGen.Validate` independently re-derives every number.
  **The per-level `atk` and save columns are a transcription of a formula, not free values** —
  each Calling carries an `attackRank` and `Validate` re-derives every row, so a bad transcription
  fails the smoke suite instead of drifting from the book. The same discipline covers armor
  (`ArmorFrom`), the Signs (`SignRankAt`/`SignsFor`) and the Miracles (`MiraclesFor`), with
  `Validate` refusing any soul that works both Signs and Miracles.
  The nine-step wizard is `TabsWizard.cs`; pure assembly in `CharGen.Assemble(AssembleSpec)`.
  **The general store sells more than one of a thing:** the count rides as **repeated
  `Gear`/`WeaponsCarried` entries**, which is why `Validate`'s coin ledger needed no change — it
  already priced gear by counting — and **`CharGen.Tally` is the single place** those entries
  become lines again ("Lantern × 3"), shared by the Ledger, the text sheet and the PDF. Buying a
  second suit of armor grants no second DR.
- **Generators** — every Ch. XII rollable table plus all nine Grounds terrain tables and the Hand
  Behind It villain picker, safe-table rule applied automatically. Expansions live in
  `Data/tables_extra.json`, merged at load by `Db.MergeTables` and **kept separate so a book
  re-extraction can never clobber the app-side additions**; every terrain entry there must name a
  real creature (the smoke suite asserts it). **The White Bison stays off every table on purpose**,
  per its Ch. XII "gone quiet" rumor.
- **Reference** — a paged Keeper's screen (**13 leaves**, counted from `RefLeafTitles`), ◀ ▶ or
  arrow keys captured in `ProcessCmdKey` so focus doesn't matter. Typewriter tables with Blood-red
  header bands (`RTbl`), laid to the width of the pane — see *The Reference deck is laid to the
  pane* below. The arms, goods, signs and skills leaves render live from `Data/chargen.json` so
  they can't drift.
- **Session** — free-form Keeper's notes + named 4/6/8-segment progress clocks. Autosaves to
  `session.json` beside the exe on exit **and every 5 minutes**; reloads on launch. First run seeds
  the Appendix D pregens so it's useful immediately.

## Files

| File | Role |
|---|---|
| `BloodAndGritKeeper.csproj` | Project file. `net10.0-windows`, `UseWindowsForms`, `EnableWindowsTargeting`. Also carries the **self-contained single-file publish settings** (RID win-x64, `SelfContained`, `PublishSingleFile`) so `dotnet publish` always yields a zero-dependency exe. |
| **`Core.cs`** | Models (`PartyMember`, `Combatant`, `CampaignClock` — all `INotifyPropertyChanged` with clamped setters), the `Rules` static class (dice parser, four-degrees, Nerve-loss ladder, encounter cost), `TurnClock`, and `Db` (loads the JSON data). |
| **`MainForm.cs`** | App shell, theme constants, the deferred-splitter `Split()` helper, the emblem/icon loaders + `Watermark()`, context keyboard shortcuts + `ProcessCmdKey` Reference paging, Posse tab, Dice tab, persistence (`Snapshot`/`ApplySession`/autosave/autoload), demo-posse seed, the undo/redo engine, and the tooltip walker (`WalkForTips`/`WantsTip`). |
| **`Menus.cs`** | The menu bar (File/View/Help), session Save-as/Load dialogs, the five-minute lesson + shortcuts windows, About box, `ShowRequirements`. |
| **`Tabs.cs`** | Bestiary, Encounter, Tracker, Generators, Reference (the 13-leaf deck + `RTbl`), Session tabs, and the turn hourglass. |
| **`TabsChargen.cs`** | The New Soul tab + the ✎ Tweak dialog. |
| **`TabsWizard.cs`** | The nine-step chargen wizard (`SoulWizard`) — collects an `AssembleSpec` for `CharGen.Assemble`. Every control and list row carries a tooltip built from `chargen.json`; `RealizeEveryStep` builds all nine pages for `--selftest`. |
| **`CharGen.cs`** | Chargen data model, `Generate`, `Assemble`, `Validate`, text `Render`. Compiled into the smoke rig. |
| **`Ledger.cs`** | `LedgerView` — the book's Ledger sheet as an owner-drawn, zoomable control — plus the per-soul pop-out windows (`ShowSoulCard`) and sheet↔member sync. |
| **`MapGen.cs`** | Trail Maps generator — pure, no WinForms types (compiled into the smoke rig); emits `Prim` lists + `ToSvg`. |
| **`TabsMap.cs`** | The Map tab UI + the GDI primitive replayer. |
| **`Hourglass.cs`** | `HourglassView` — owner-drawn sand, ink only. Draws no text, so the drawn-text landmine below does not apply. |
| **`Pdf.cs`** | From-scratch PDF 1.4 writer, no packages: `TextSheet` (portrait soul sheet) and `MapPdf` (landscape map). Compiled into the smoke rig. |
| `Program.cs` | Entry point. Wraps startup in global exception handlers that write `startup-error.txt` beside the exe (or `%TEMP%`) on any crash — so failures are never silent. Opens the `Daybook` (and points it at `daybook.txt` under `--verbose`), and folds its dump into both error reports. Also hosts `--selftest`. |
| **`Daybook.cs`** | The capped record of what the app just did — rolls, checks, session saves/loads, mode switches, generated souls, and **turn handoffs** (who went, on what initiative, who was still to go — the `turn` channel, added in v1.35.0, which is how the ordering fix was proved in the running app rather than only in the test rig) — for the failure that never throws and so writes no error file. **Inert until `Open()`**, which only the app calls: the smoke rig fuzzes the paths it listens to thousands of times per build. Ring of `Cap` (400), fails soft on every write, `Dump()` says "not recording" rather than reading as an empty night. Surfaced at **Help ▸ Save a diagnostic log…**. |
| `app.ico` / `Assets/emblem.png` | The cover emblem as a multi-size Windows icon (regenerate from `assets/img20.png` if the emblem changes) and as the watermark PNG. Both embedded. |
| `Data/creatures.json` | All 175 creatures, extracted from `bestiary.html` by `extract_creatures.py`. Re-extract and drop in fresh if the Bestiary content changes — no code changes needed. **Embedded into the exe.** |
| `Data/tables.json` | The 17 simple tables + 11 Grounds terrain tables, same extraction approach. **Book-faithful — never hand-edit; a re-extraction replaces it wholesale.** |
| `Data/tables_extra.json` | The app's own generator expansions. Merged after `tables.json` by `Db.MergeTables`, so re-extraction can't eat them. |
| **`Look.cs`** | What a soul looks like — `SoulLook` (the description, carried on `CharacterSheet.Look`) and `Look.Roll`. Pure, in the rules library, drawing-free. The two rules that govern it are below, under *What a soul looks like*. |
| **`Names.cs`** | **What things are called** — `Namer` (seeded, spends what it draws) and `Names` (loads the stock). Pure, drawing-free, in the rules library. Two defences that fail separately: **breadth** reaches across seeds, **memory** reaches within one. It spends title **shapes** as readily as words, which is the half that was broken — *The Salt at Coffin Wells* and *The Reckoning of the Wells* collided on the word AND on the grammar, so widening the vocabulary alone would have produced the identical fault in a better coat. **Exactly one `rng.Next` per draw** and this is forced, not stylistic: `MapGen`'s `rngLm` names *and* places landmarks off one `Random`, so a rejection loop costing two rolls instead of one would silently move every rock on the sheet. `Reserve()` spends a word consuming no randomness, so an exclusion never shifts a seed. |
| `Data/names.json` | The naming stock — 21 title templates and the word pools they fill, plus `spent` (words already on published work, refused on first draw). **App-side data like `tables_extra.json` and `appearance.json`, not a book transcription**, so it may be widened freely. Note `actor`/`actorp` and `verb3`/`verb` are split for **subject–verb agreement**: one list would generate "Until the Homesteaders Pays". `motion3` exists because an arrival template handed an intransitive verb produces "Something Forgets to Chalk Section". **Embedded**, like the rest. |
| `Data/appearance.json` | 28 peoples, 19 whole styles of dress, and the shared pools for build, bearing, face, marks, voice, hair, whiskers, wear and the one memorable detail. **The app's own, not the books'** — like `tables_extra.json`, and for the same reason: `chargen.json` is a transcription and must stay one. **Embedded**, like the rest. |

## Build & run

```bash
# Requires the official Microsoft .NET 10 SDK (Ubuntu's apt package lacks WindowsDesktop targets).
cd GK/source
dotnet build -c Release

# Self-contained single-file Windows exe. The publish settings (RuntimeIdentifier=win-x64,
# SelfContained, PublishSingleFile) are BAKED INTO THE CSPROJ as of 2026-07-15, so no flags
# are needed and a publish can never silently regress to framework-dependent.
dotnet publish -c Release
```

**NEVER pass `-o`.** `sign.ps1` and `package.ps1` both default to the RID-qualified publish path;
`-o` diverts the build somewhere else and they will happily sign and ship the PREVIOUS version's
exe instead. This happened during the v1.18.0 release and was caught only on the version check.

Deliverable = **just `bin/Release/net10.0-windows/win-x64/publish/GritKeeper.exe`** (~112.5 MB;
`EnableCompressionInSingleFile` and `PublishReadyToRun` are deliberately **off** for startup speed
and Defender scan time, which is why it is not the ~50 MB a compressed publish would be — the zip
comes out ~46 MB) — a **true single-file standalone**: the .NET runtime is bundled *and* the
`Data/*.json` are **embedded in the exe**, so it runs on any Windows machine with no .NET install
and no `Data/` folder beside it. `Db.ReadData` loads the JSON from the assembly, and falls back to
`Data/` on disk for the smoke rig / dev build. The exe writes only `session.json` beside itself
(via `AppContext.BaseDirectory`). Published on GitHub via **Releases**, never committed — the
binary is git-ignored.

**Bumping the version is the START of shipping, not the end of it** (learned the hard way,
2026-08-02). A build in `bin/` changes nothing about what anybody runs: the desktop shortcut points
at **`GritKeeper\app\GritKeeper.exe`**, which only `package.ps1` ever writes. v1.32.0 was written,
verified against all four checks, merged, and entered in the CHANGELOG as a shipped release — and
was never published, signed, packaged or tagged, so the Keeper's desktop stayed on v1.31.0 for a day
and a half and the app was two releases behind before anyone looked. **The whole loop is
`dotnet publish -c Release` → `.\sign.ps1` → `.\package.ps1` → tag → GitHub Release**, and
**`python verify_release.py --delivered`** is the one command that answers "is the app on this
machine actually the version we think it is". `.githooks/pre-push` runs it when `main` is pushed;
CI runs the half it can see, and fails once a version stops being the newest without a tag.

**A Linux package is planned** (decided 2026-07-29). The engine half has been done since v1.28.0:
`GK/rules` is a plain `net10.0` library with no Windows reference — exactly what the headless smoke
rig builds against — so the rules, chargen, map generator and PDF writer all run on Linux today.
What a Linux build has to answer is the **UI**: `GK/source` is `net10.0-windows` + WinForms and
cannot cross that line, so this means a second front-end against the same library, not a port.
Anything added to the rules library should stay drawing-free and WinForms-free for that reason.
**Until something ships, every mention of it says "planned" and gives no date**: the standing rule
that the app never promises what it cannot keep applies to a roadmap as much as to a feature. The
places carrying the note, which must be kept in step, are `README.md`, `GK/source/README.md`, and
the app's own **Help ▸ What it needs to run** (`ShowRequirements` in `Menus.cs`).

## Dying, bleeding and death (v1.38.0) — and why Blood never goes negative

Ch. XI in full: 0 Blood is Dying, a Blood a round, dead at −CON, stopped by a Fortitude save or a
Medicine check at DC 15; Ch. II's Grit buys one more round on your feet. `Combatant` carries
`Bleed` / `DeathAt` / `Stable` / `Upright`; `Rules.BleedOut`, `RefuseToFall`, `Stabilize` and
`DeathThresholdFor` are the pure half.

Four decisions worth not re-deriving:

- **`BloodCur` stays 0..max.** Every screen, save, bar and clamp in the app reads it that way, so
  the ground below zero is a separate count rather than a sign change nothing else was written for.
- **`DeathAt` is 0 by default and the rule simply does not run on that row.** The book writes this
  for characters; the Bestiary's answer to a horror at 0 Blood is its own `puttingItDown` line. A
  soul takes CON off their sheet on the way onto the field, and `ApplySession` backfills rows from
  sessions written before this, only ever upward from zero.
- **`Upright` cannot be derived.** At 0 Blood `Down` is true and `CanAct` refuses the turn, so
  refusing to fall had to become a fact of its own — cleared by `BleedOut`, which is what "one more
  round" means. It does not stop the bleeding: the book buys consciousness with Grit, not time.
- **Overkill carries.** A blow past zero keeps counting toward −CON. This is a READING, not a
  quotation — "reach –CON" only parses if Blood is a real number that goes negative — and it is
  recorded as one in `Wound`. Without it a cannonball and a slap are identical to a soul on 1 Blood.

`ResetForNewFight` deliberately clears **none** of it except `Upright`: dying is Blood, and Blood
carries between fights. `FightResidue` matches, so New fight cannot say "nothing to clear" over it.

## The row grounds are separated by CAST, not by brightness (v1.38.0)

Seven grounds now say what a tracker row is, and the rule that keeps them apart is that **no two
differ only in lightness**. `Writable()` lifts an editable cell toward paper, and a lift washes a
pale colour toward white — which is exactly how the old palette failed: `PcRow` and a near-white
`FoeRow` differed by about nine points of luminance, and `Writable` at 42% put a posse row's four
editable columns nearer the foe colour than the posse colour was to it. Read them as R-vs-G: the
posse's green sits G above R, a foe's clay sits R above G, and no lift crosses that. Down is a quiet
grey, dying is the only loud ground in the app, dead is ash. **Anything added here has to obey the
same rule**; a new ground that is merely a different brightness fails silently. The seventh, `FamiliarRow`
(v1.48.0), is the worked example: the posse's green and a foe's clay are argued out in R against
G and both put **blue lowest**, so blue was the free direction and the bound beast took it — B
above R by 26, where PcRow is B *below* R by 8 and FoeRow by 28.

## The Iron Code is run, not read out (v1.40.0)

Ch. XI was audited against the engine and nine gaps closed. Six decisions worth not re-deriving:

- **`Rules.BeatActions` is the one list of the seven actions**, and the Tracker's *Act ▾* menu and
  the Reference deck's Iron Code leaf both render from it. They were two lists before, and for six
  releases the leaf printed six actions to the Keeper while the app could spend a Beat on one of
  them. Add an action here and both surfaces get it; add it to either surface alone and you have
  recreated the bug.
- **The Keeper is asked only what the app cannot see.** `IronCode.Shot` carries the distance, the
  cover, into-melee, concealment and the pulled blow, because the app models no ground. Everything
  else the chapter charges for is read off the rows by `StrikeAndApply` itself — the gait, whether
  the target is mounted or Prone, the Aim held, the recoil standing. Asking for either of those
  would be asking the Keeper to type in something the app already knows, and a typed answer that
  disagrees with the row is a bug with two authorities.
- **Off-Guard and the Aim are paid in exactly one place each**, and `IronCode.Reckon` documents why
  it does not charge them: the Burden already pays Off-Guard as −2 Defense, and `Combatant.Aimed`
  already pays the Aim. A smoke test asserts the absence. This is the same double-apply the derived
  Burden was built to prevent in v1.39.0.
- **`Combatant.Recoiling` is engine-written and `Conditions` is not.** The unbraced-Kickback rule is
  unconditional — no save, nobody's judgement — so the engine may both set it and clear it at
  `BeginTurn`. Anything that hangs on a save the Keeper has to call stays *offered*, the way a
  creature's attack rider is. `Rules.DiveForCover` hands its Prone back for the same reason.
- **`Combatant.Str` is 0 when nobody has said**, exactly as `DeathAt` is, and is read through
  `Strength`. A stored default of ten would be indistinguishable from a soul who really is average,
  and would hand the shotgun's recoil to somebody the book exempts. `ApplySession` backfills it only
  ever upward from zero.
- **A long gun is identified by NAME**, in `IronCode.IsLongGun`. Ch. X's glossary defines a
  Two-Handed trait and then prints it on no weapon in either table, so there is no trait to read;
  Ch. XI names them the same way ("a two-handed long gun (rifle, carbine, shotgun)"). Following the
  book beat inventing a data column it does not have.

**The arms table is now audited, and it is the reason all of this was unbuildable.**
`audits/verify_rules.py` guarded the Calling tables and read the arms table not at all, so
the transcription had lost **Range, Cap. and Reload** for every gun, folded the cap-and-ball's *slow*
into its traits string, and left out Fists / Boots and the book's whole second table. 791
cross-checks now, up from 697. **Any new book table transcribed into `chargen.json` gets an auditor
in the same session** — that is the lesson, and it is cheaper than the six months this one cost.

## The prose beside the tables is audited too (2026-08-19)

Same lesson, second helping. The Calling tables were guarded and the paragraphs printed next to
them were not, so a hand transcription rotted in place: twenty of the 116 `featureDescs` stopped
dead at exactly 420 characters, most of them mid-word. A Prospector reading Powderman in this app
was told his blast rises "to 3d6 at 4th level, 4d6 at 7th, and 5d6 at 10" — and that was the end
of the sentence, the feature, and his understanding of it. Seven more had gone stale against the
book: the app still described Signs the way Ch. XIII read before the Common Signs and the Bargain
were split into Ranks, so a Hexer picking from the app and a Hexer picking from the book were
choosing off two different lists. Three had swallowed the pull-quote that follows the feature,
attribution and all, and printed a dead Marshal's epitaph as if it were a rule.

`check_features` in `audits/verify_rules.py` reads the book the way a reader does — heading to
heading — cutting pull-quotes and stat tables on the way through, and holds every transcription
up against it. It also re-derives each Calling's **blurb**, the opening words the wizard's picker
shows, by rule rather than by trust: the opening paragraph, whole sentences, until there are
ninety characters. Ninety is what it takes to carry the short ones — *"Where the Preacher
improvises, the Padre inherits"* means nothing standing alone — without dragging the Shaman's
entire first breath into a tooltip.

`check_subpaths` reads the 3rd-level paths the same way, and found worse. Seventeen of the
fifty-six boons had swallowed the printed page's furniture: a player choosing The Mechanic was
told his mastery lets him *"take the better result on every roll for a round. 13 V. Worldly
CallingsBlood & Grit"* — folio, running head and book title, sitting inside the rule where a
sentence should end. Three more stopped at exactly 400 characters. 980 cross-checks now.

The blurb exists because the picker could tell you a Sawbones rolls a d8 for Blood and could not
tell you what a sawbones **is**. It is the frontier's word for a doctor, after the saw in the bag,
and a player who has never met the word now reads that before they choose.

## The Callings are playable from the Tracker (v1.42.0)

Every number a posse soul has was on the Tracker and every rule they had was not. A Marshal's
player asking "can I still Last Stand?" was asking a question the app held all the parts of — the
Calling, the level, the book's own sentence — and had nowhere to put.

**`CharGen.ReadLimit` reads how often a feature may be used out of the feature's own prose**, and
that is deliberate: a `uses` column typed into `chargen.json` beside the description would be a
second copy of a fact, and the twenty descriptions repaired the same day are what a second copy
does when nobody audits it. Thirty-one of the hundred and sixteen features state a limit on an
*activation* — "Once per session, when an ally within sight would drop to 0 Blood…", "Usable a
number of times per scene equal to your PRE modifier (minimum 1)" — and those are what the reader
matches. Sentences about something ongoing are deliberately left alone: *"allies inside recover
Nerve each round"* is not a thing anybody presses, and a counter beside a feature nobody activates
teaches a Keeper to stop trusting the counters that matter.

`FeatureCadence` is ordered on purpose — Turn, Round, Scene, Dawn, Trigger, Session — because the
reset rule is "everything at or below the boundary that just passed comes back". A scene returns
the turn, round and scene features and leaves the once-a-session ones spent. **Trigger** is the odd
one and the book has two: the Witch Hunter's Judgment returns "when you name a new quarry" and the
Sawbones' Field Surgery is "once per wound". No clock returns those, so nothing but the Keeper's
hand and a new session does either.

**What returns a feature is a boundary the app already had.** New fight and Restore field are the
scene; Rest is the dawn; New session is the night. `NextTurn` hands back the once-a-turn features
on its own and `NextRound` the once-a-round ones for the whole posse, so nobody presses anything
for those. Nothing new was invented for a Keeper to remember.

Two seams worth knowing about, both found by writing the reader:

- **`CharGen.FeatureKey` is the one place a level table's name and a prose heading are reconciled.**
  The table prints the die in the column — "Judgment 3d8", "Dead Aim +1d6" — and three features can
  share one heading, as the Drifter's *Ghost / Uncanny Step / Vanish* does. Those three chained
  lookups used to sit inline in `CharGen.Render`, where nothing else could reach them.
- **The 3rd-level path is found by the suffix the book prints**, not by "this name has no
  description". Every Calling has a `<Word>` at 3rd and a `<Word> Mastery` at 10th — `(Greater)` at
  9th for the three of the Old Dark — and the rules live in `subpath.options`, one boon apiece.
  The Dark Cultist is why the rule has to be structural: their table prints **Devotion** at 1st for
  the pool they spend and **Devotion** again at 3rd for the path they walk, and a rule that keys off
  a missing description gives the second one the first one's text.

`PartyMember.FeatureSpent` stores what has been spent rather than what is left, so a soul who levels
up into more uses does not need topping up: the maximum is re-derived from the sheet every time the
strip is drawn. It is a public property, so it rides along in `session.json` without being told.

One trap, and it cost half an hour: **`audits/audit_ui.py` walks a call character by character and
reads an apostrophe as the start of a char literal.** A comment about "a Marshal's Last Stand"
written between the parentheses of a `Btn(...)` call swallows everything after it, and the tooltip
behind the comment vanishes from the audit. Keep prose comments above the call.

## What a soul OWES is not a ration (v1.44.0)

The Calling strip counts two different things and draws them differently on purpose.

A **ration** is a thing you have and spend, and a boundary hands it back: `FeatureLimit`,
`CharGen.ReadLimit`, `PartyMember.FeatureSpent`, returned by `CharGen.RefreshFeatures`. That is
v1.42.0 and it covers thirty-one of the hundred and sixteen features.

A **tally** climbs and nothing hands it back. `FeatureTally`, `CharGen.ReadTally`,
`PartyMember.TallyOwed`, moved only by `TakeTally` and `ForgiveTally`. The book states exactly one:
the Hexer's Pact-Sworn bargain, *"on your third Debt the Patron calls it in — a demand, and +1
Mark."* A sweep of all 116 features and all 56 paths finds no second one, and a smoke test holds
the data to that so a new Calling cannot put an uncounted card on the strip.

Four decisions worth not re-deriving:

- **The two stores are separate so that no boundary can reach a Debt.** `RefreshFeatures` walks
  `FeatureSpent` alone. That is the design, not an oversight — a Debt is owed until the Patron
  collects it, and the app must never be the reason one quietly went away. Six smoke assertions
  walk every cadence and check the count still stands. **This is the recurring-bug class run
  backwards:** the usual fault here is state added late that older reset paths never learned about,
  and the guard is a test that fails if a reset path ever *does* learn about this one.
- **The threshold is read out of the prose, never typed into `chargen.json`.** Same reason
  `ReadLimit` is: a second copy of a fact is what the twenty repaired descriptions of 2026-08-19
  were. The pattern is deliberately narrow — *"on your <ordinal> <Capitalised noun>"* — because a
  looser one reads "on your first turn" as a debt, and a counter the app invented is worse than one
  it lacks.
- **The count is not clamped at the threshold.** Four Debts is a legitimate state; the Patron
  collecting is the Keeper's move. The card says *"Debts — 4 owed"* past it rather than *"4 of 3"*,
  which is the same number said in a way that reads.
- **`CharGen.ShortFeatureName` is display only.** A 3rd-level path is keyed section-colon-option so
  the key is unique across every Calling; at 158px both of a Hexer's Bargain cards ellipsised
  to the same twenty-four characters. The card drops the section, the head line above having
  already named the Calling. `FeatureSpent` and `TallyOwed` keep the whole string, so trimming for
  the eye cannot orphan a saved session.

## The Witch's familiar is a creature, not a sheet field (v1.48.0)

v1.45.0 put the bound beast of Ch. VII on the character sheet — its kind, its standing +2, a flag
for when it dies — and none of it did anything. This is the half the book actually legislates.
Five decisions worth not re-deriving:

- **A fact that is only printable stops being true.** The sheet said "+2 Notice" and every number
  the app worked out ignored it, because the skill's name existed *only* inside a sentence written
  for a reader. `CharGen.FamiliarSkillFor` holds the skill on its own, `FamiliarBoonFor` builds the
  sentence from it, and `SkillBonus` adds it — so one change lands everywhere the app already
  reckons a skill. A Witch's initiative is a Notice check, so a living crow moves her place in the
  order. This is the same shape as `ReadLimit` reading a limit out of prose rather than a second
  `uses` column: whenever one of a pair of facts is only printable, the other one goes quietly
  wrong.
- **The familiar is a FOURTH CAST, and deliberately not `IsPC`.** `Combatant.FamiliarOf` holds its
  Witch's `PartyMember.Id`. It is not `PcId` with a flag beside it, because `IsSoul` keys the
  posse-to-tracker Blood mirror off PcId — a familiar carrying its Witch's PcId would have her
  Blood written onto it on every posse edit, and the beast having a Blood of its own is the entire
  point. Everything that walks the posse asks for a soul and correctly finds nothing here.
- **The book gives the beast no stat block and the app does not pretend otherwise.** Ch. VII says
  what the familiar *does*; the Bestiary's 175 entries are horrors, not livestock. `Rules`
  derives a default from figures the book *does* state — Blood a third of its Witch's, **half**
  once she has taken the Familiar-Bound ("grows clever and hardy"), floored at four; Defense hers,
  and two better with the Craft — and the card's tooltip says out loud that this is the app's
  default rather than a rule from the book. Do not print a familiar stat table into the books to
  "fix" this: that is a rules change and needs Cole's say-so.
- **At 0 Blood the beast is dead, not down**, which is the reading the app already gives every
  creature. The dying rule is written for characters, and a cat with a count running toward its CON
  is a rule the book does not have. Noticed in `CheckFalling` (`FamiliarFell`), because that is
  where every route that takes Blood off anything already arrives — and written to read the state
  rather than the caller's word for it, since two of that method's seven callers pass
  `wasDown: false` for reasons of their own and a version that trusted the flag would Sicken a
  Witch twice over one dead crow.
- **The rite is an act, not a boundary.** "Sickened until you can bind another over a long night's
  rite" is `BindNewFamiliar`, on the Calling strip and the row menu. It is deliberately NOT hung on
  Rest or on any dawn: every other boundary in this app hands something back because a clock turned
  over, and a Sickened that lifted by itself overnight would quietly say the loss cost nothing.

The greater boon's **spirit-carry** lives on the character sheet (`FamiliarCarried`), not in
`FeatureSpent`, for exactly the reason the Pact-Sworn's Debts do not: `RefreshFeatures` walks
`FeatureSpent` at every boundary, and a once-in-a-life thing kept there would come back the first
time somebody pressed New fight. A smoke assertion runs a session boundary over it and checks it
stays spent. The Craft's two levels come from `CharGen.SubpathLevels`, read off the level table —
3rd and 9th for the three of the Old Dark, 10th for everybody else — so no familiar rule carries a
literal 3 or 9.

## The Returned — Hunger is the payoff AND the doom (v1.49.0)

Came Back Wrong was one paragraph in Ch. IV and a `startMark` of 1. It is now a subsystem, and it
exists to answer a design question Cole put plainly: **what makes a player want the damned option
over a Padre?**

The honest reading of the books before this: nothing did. The Faith Callings pay for Miracles out
of a pool that refills free at dawn; the Old Dark pays for Signs in **Nerve** — the same track that
measures sanity, restored 1d6 a safe night and needing *a week of true peace* for all of it — and a
Rank 5 Sign costs a **Mark**, permanent, on a six-step track whose end is the player losing the
character. The dark pays strictly more for comparable effects, and its compensation (Taint
immunity, Dread easing at Mark 4) only lands once it is two thirds of the way to the ending.
**Costs front-loaded, payoff back-loaded past the point of no return.**

Hunger is the shape that fixes it, and the fix is that **one track is both halves**. Mending is the
only healing a Returned soul has — not rest, not medicine, not a Miracle worked over them — and it
costs a step. So the resource that keeps you standing is the resource that takes you away, and the
player makes that trade knowingly, every fight, for real power. That is a bargain somebody *wants*.
Cole's call on 2026-08-25 was to leave the Faith economy untouched and fix the curve by making the
dark better; nothing in Ch. VI or the 40 Miracles moved.

Six decisions worth not re-deriving:

- **Hunger lives on `CharacterSheet`, not on `PartyMember` beside Mark and Taint.** Those two are
  asked of every soul in the posse and have grid columns; one Origin in ten carries a Hunger, and a
  column would be eighteen empty cells. Same argument as `FamiliarKind`.
- **Nothing hands a Hunger back.** Not Rest, not a dawn, not New session — `RefreshFeatures` never
  touches it, and a smoke assertion runs a session boundary over it and checks. Feeding is the only
  way down and it is a **scene the Keeper adjudicates**, never an action on a turn. Identical
  reasoning to the Witch's rite (v1.48.0) and the Pact-Sworn's Debts (v1.44.0): a track that eases
  overnight says the cost was nothing.
- **Mending at the last rung is warned about and PERMITTED.** `WhyNotMend` refuses only at
  Consumed; Hunger 5 gets a `Confirm`, not a locked door. A player bleeding out who spends their
  last step to stay upright one more round is the whole reason this Origin exists, and the app's
  job is to make sure nobody arrives there uninformed.
- **The +2 on Dread and the numbness at Hunger 3 REACH A ROLL.** `Horror.DreadCheck` takes an
  optional `CharacterSheet` and both call sites pass it. This is the v1.48.0 familiar lesson run on
  a second subsystem: a fact that is only printable stops being true. The bonus is added to the
  **Will**, not subtracted from the DC, so the four degrees are worked out against the number the
  book prints.
- **Numbness spares the Nerve and nothing else.** A numb soul still fails, is still Frightened, and
  still takes the DC-25 Affliction — those are things done *to* a soul. Only the Nerve is spared,
  because Nerve is the one that measures still being able to care. The book prints it as a gift and
  says in the same breath that it is not one, and `DreadOutcome.Numb` is what lets the log say so.
- **`soul.Touched(nameof(soul.Sheet))` after every Hunger mutation, announced AFTER the change.**
  Hunger rides inside the Sheet, which is in `Snapshot()` and fires no `PropertyChanged` — exactly
  the three fields v1.48.0 found. Without it, Undo silently reverts a mend along with whatever is
  captured next.

The four **Shapes of Return** (Risen, Sanguine, Hollow, Tolled) are transcribed into
`chargen.json` as `shapes` on the one Origin that has them, and `Validate` refuses a Shape the book
does not print, refuses a Returned soul with no Shape, and refuses a Hunger on anybody else — that
last one because a track with an ending sitting on a Gunhand is not a small error.

**The book carries a safety box and it is not optional.** Three of the four Shapes feed on people
who did not volunteer, so Ch. XII says plainly that a Keeper may rule any Shape's feeding bloodless
or off-screen and the rules lose nothing by it. Same standing line as the Ch. IV safety note.

## Ch. IV's encounter ladder is one array (v1.44.0)

`Rules.BudgetRungs` — mook 4, even foe 8, standout 16 — and `Rules.BudgetPerSoul` = 4. `Rules.Cost`
prices from it, the Encounter tab's header line builds from it, `Tour.cs` reads it, and the
Reference deck's Long Odds leaf renders its table from it. Before v1.44.0 those were four typed
copies in the app and three more in the two books, which is precisely how a repricing Cole approved
on 2026-08-16 was still unshipped in every one of them six days later.

**The numbers came off the harness, not off taste.** Spending the budget exactly wiped a posse of
four 76–100% of the time at every level from 1 to 6, gritted and aimed; swept rung by rung, the
fight such a posse still wins about three times in four while paying for it prices at 4 · 8 · 16.
`AUDIT-encounter-budget.md` holds the tables and `_combatlab/Balance.cs` regenerates them
(`dotnet run -c Release -- prices`).

**`audits/verify_rules.py::check_budget` is what stops it drifting again.** It reads the array out
of `Core.cs` and holds it against Ch. IV's list, the Keeper's Book quick-reference card, and the
Bestiary's paragraph. Two of those are the same rule printed twice in one book, which is the fault
that shipped in `books-v1.2`. Prove any change to it against a synthetic drift before believing it.

## The Beats are enforced, and a refusal says why (v1.38.0)

`Rules.CanSpendBeats(c, n)` and `Rules.WhyNoBeats(c, n)` are a pair on purpose: the answer and the
reason have to agree, because a button that goes grey without saying why is reported as broken.
`Rules.BeatsFor(time)` reads the printed cost line — `1 Beat` costs one, `10 minutes` costs none.
Both dialogs that spend a turn (Strike, Work) gate their commit button on it, relabel the cancel to
*Back to the field*, and point `AcceptButton` at whichever is live. **Reserve the refusal line's
height whether or not it is speaking** — both dialogs stay open for a follow-up, so a block that
appears once the Beats run out would walk the buttons around under the Keeper's hand.

`StrikeAndApply` was left alone deliberately: `GK/playtest` drives fights through it on a
`while (up.Beats > 0)` loop, and a refusal inside the engine would change what the modules' *What
the Night Costs* numbers were measured against. The gate is the UI's.

## The Reference deck is laid to the pane (v1.38.0)

Tables are padded monospace and that is forced, not stylistic: the padding is what carries the
Blood-red header band to the right edge, and Georgia is a text-figure face whose 3 4 5 7 9 descend,
so a column of figures will not line up in it (same reason `LedgerView` has `NumFace`). The face is
**Courier New**, not Consolas — a period document would have been struck on one, and Consolas is a
code face used nowhere else in this project.

`RefColumns()` measures how many characters fit *now*; `RefFit()` widens the authored widths to it.
Two rules: the surplus goes to the **last** column only (the one carrying the rule text — widening a
DC column just opens a gulf between a label and its sentence), and it is capped at
`RefMeasureCap` = 90 characters, past which a line stops being easier to read. Leftovers stay as
margin. The deck re-deals on resize **only when the character count changes**, so a resize drag does
not redraw thirteen leaves a second.

## Known landmine: SplitContainer must not get geometry at construction time

**Hit once, cost a full crash-on-launch on real Windows.** Setting
`SplitterDistance`/`Panel1MinSize`/`Panel2MinSize` on a `SplitContainer` *before* it's been docked
and laid out throws `SplitterDistance must be between Panel1MinSize and Width - Panel2MinSize`,
because at construction time the control's width is some tiny placeholder, not its real docked
size. This compiles fine and passes headless logic tests — it only throws when the window actually
renders.

**The fix, already in `MainForm.cs`:** a `Split(orientation, p1Min, p2Min, ratio, preferred)` helper
that creates the SplitContainer bare and defers all geometry to a `SizeChanged` handler, which only
fires once the control has a real size and clamps mins against small windows. **Always build new
splitters through this helper.**

**One-shot is right for a ratio and wrong for a measurement (v1.38.0).** A ratio splitter seats once
and is left alone, because re-seating on every resize would undo a Keeper's drag. A **measured** one
— `preferred` returning `MeasuredColumnWidth(panel)`, for a fixed-width column of buttons — keeps
listening until the Keeper moves it themselves, and takes `FixedPanel.Panel1` so its column holds
its pixel width. That is not a nicety: unsubscribing on the first success is how the Generators
splitter came to sit at 27% of about 2,700px on a 1,264px tab, because for a lazily-realized tab the
first `SizeChanged` arrives at whatever width the control passes through on the way to being laid
out. `applying` tells our own assignment apart from a drag.

## Known landmine: drawn text — the hint, the figures, and the box

Three separate traps, all found in one screenshot of the Ledger, all worth avoiding in any new
owner-drawn surface (`TabsMap.cs` replays primitives the same way):

- **`TextRenderingHint.AntiAliasGridFit` eats word spaces at small sizes.** Hinting rounds each
  glyph advance to a whole pixel, and Georgia's word space at 9.5pt rounds to nothing — the
  subtitle rendered "A Reckoning of **OneSoul**". It clears up by ~14pt, which is why it looks
  intermittent. Use plain `AntiAlias` for body-size drawn text. **And measure under the same hint
  you paint under** — `PerformLayoutPass` used a fresh `Graphics` with the default hint, which is
  how a measured height comes to disagree with the ink.
- **Georgia is a text-figure face.** Its 3 4 5 7 9 descend and its 0 1 2 sit at x-height, so "30"
  reads as "3o" and a column of numbers doesn't line up. GDI+ has no way to request a font's
  lining-figure set, so **figures are drawn in a different face** — `LedgerView.NumFace`, the first
  installed of Cambria / Palatino Linotype / Times New Roman. `FirstInstalled` exists because GDI+
  **silently substitutes Microsoft Sans Serif** for a missing family; the substitute reports its
  own name, which is the only way to detect it. Keep prose in Georgia.
- **`DrawString(text, font, brush, x, y)` has no width and will not stop.** Overflow gets painted
  over by whatever is drawn next, which reads as a truncation with no cause. Draw into a
  `RectangleF` with a trimming `StringFormat`. This applies to **labels as much as values** —
  "BLOOD / MAX" was the one that got missed.

**Do not use ⧖ (U+29D6)** — it is not in Segoe UI on this machine and renders as "≥". The glyphs
that do render are ▶ ▾ ◀ ▸ ◂ ✕ ＋ ✎ ✦ ✝ ◈ ✚ ✥ ⟲ ⟳ 🔍 🎲 🧭.

## Known landmine: a Font is a native handle, and `.Font = new Font(…)` on a repeating path leaks it

Found in the v1.30.0 six-month sweep, in the two hottest paths in the app: the Dice tab's result card
minted a headline font on **every roll**, and `RenderCreature` about **thirty per creature**, so
arrowing down the Bestiary's 150 spends ~4,500 GDI handles in seconds. Neither disposed anything.
The finalizer does eventually reclaim them, which is exactly why an hour of testing looks clean and a
long evening does not — and why this survived every assertion the app has.

**`MainForm.Face(family, size, style)` is the shelf.** It memoizes into a static dictionary and is
never emptied on purpose: the set of triples the app draws with is small and fixed, so it settles at a
few dozen fonts for the life of the process. Take fonts from it anywhere the font is drawn with
repeatedly. A `new Font(...)` assigned once at construction, and owned by the control, is fine and is
what most of the UI does — the rule is about **repeating** paths. (Two existing sites got this right
and are worth copying: `StyleRollLog` mints one bold variant and disposes it on `Disposed`;
`StyleTabs` disposes the bold face it makes per paint.)

## A grid that is not double-buffered is the slowest thing on a tab (v1.52.0)

Cole reported that switching tabs felt slow. `GritKeeper.exe --timetabs` is the answer to that
class of report: it shows a real window and times both costs separately, because two different
things hide inside "slow" and they want opposite fixes.

* **First selection** of a tab runs its builder. Once per session, 200–1000 ms. Already deferred
  on purpose (see the ctor's note) — that third of the launch is paid a tab at a time instead.
* **Every later selection** is WinForms layout and paint of a page that already exists. No amount
  of lazy building touches this one.

The measurement that decided the fix: **Release and Debug timed the same** (133.4 ms against
134.8). CPU-bound managed code does not do that, so the cost was paint, and tightening the code
behind those tabs would have moved nothing. The three slowest tabs were the three carrying a
`DataGridView` — Posse 325 ms, Tracker 214, Encounter 140 — against 25 ms for Reference, which
carries none.

`DataGridView.DoubleBuffered` is **protected**, which is why it is so often left off. `BufferGrid`
sets it by reflection and `StyleGrid` calls it, so all four grids get it from one place. After:
mean **133 → 95 ms**, Posse **325 → 145**.

**Two things not to redo.** The same treatment on the `TabControl` measured as nothing (99 ms
against 94.8, inside a ~10% run-to-run spread) — a TabControl owner-draws only its strip, so the
back-buffer covers the whole page area and saves none of the work that costs; the comment beside
`StyleTabs` records the attempt. And **5 rounds is inside the noise** — `--timetabs` runs 15.

Switch time tracks the control count of a tab at roughly 2 ms a control on this laptop, so the
remaining lever is fewer controls per page, not faster code.

## A red button is a promise, and it has to be kept on every tab (v1.54.0)

A critic's pass on 2026-08-30 — ten tabs driven out of the Debug build and photographed with
`PrintWindow`, then looked at — found six buttons that empty something a Keeper built by hand and
wear the ordinary grey face. `Clear posse` sat flush against `Heal` in identical grey on the tab a
Keeper spends the whole session on.

The Tracker had it right since v1.19 and its own comment says why: *"that means '＋ Add' never
lands on 'Clear field' — they were adjacent and identical before."* Nothing carried that reasoning
to the other five tabs, because nothing could: `audit_ui.py` asked only the FORWARD question, that
a `DangerBtn` be recoverable, and never the reverse one, that a button which empties the table be
a `DangerBtn` at all.

It asks both now, and **found a seventh on its first run** (`Clear threads`) that the screenshots
had missed. `Clear log` is deliberately exempt: the roll log is a record of what happened rather
than a thing the table is built from, and painting every clear-shaped button red is how red stops
meaning anything.

The other half of that pass is the more general lesson, and it is the same one four builders taught
in the same session: **a ceiling written as a literal survives the raise.** `Rules.Roman` stopped
at V, so every Tier VI creature printed as "T6"; the Bestiary's tier filter was a typed list ending
at "Tier V", so the seven apex creatures could not be filtered to at all; and the New Soul tab said
"Eight steps" for as long as the wizard has had nine, which is precisely the fault `CLAUDE.md`
already records against the Reference screen's leaf count. All three are derived now, and the
self-test holds the wizard to the number the tab prints rather than to a floor of eight — `>= 8`
being exactly the assertion that let the wrong number stand.

## Verification standard for this app

- `dotnet build -c Release` → 0 warnings, 0 errors (`-warnaserror` in CI).
- **`python verify_release.py`** — one version everywhere, and every past release actually cut.
  Add `--delivered` on this machine to include the exe the desktop shortcut runs. Everything else
  on this list checks the SOURCE; this is the only one that asks whether the source ever became
  something a Keeper can open.
- **Headless logic tests** (`GK/smoke`, `dotnet run -c Release`): dice-range checks, all
  four-degrees edge cases (including the nat-20-on-a-failure / nat-1-on-a-success regression cases
  — there was a real bug here once, a signed band scale with a gap at zero; fixed by moving to an
  ordered 0–3 scale), `RollExprFull` per-die/total agreement, encounter costs, the Nerve ladder,
  model clamping, `INotifyPropertyChanged` firing, serialization round-trips, full data-load checks
  (175 creatures parse, table merge counts, no duplicates, **every terrain-table entry resolves to
  a real creature by name**), `CharGen.Assemble` conformance sweeps with junk-choice fuzzing,
  `LevelUp` proved across every calling × ability method × level 1→10, Trail Maps
  generation/SVG/PDF structural + determinism checks, and `TurnClock`. Re-run after any
  `rules/`-side or data change. **Read the failures, not the total** — it drifts by a few dozen run
  to run because several sweeps assert once per random draw. Growth by release is in `CHANGELOG.md`.
  Note: this machine has only the .NET 9 runtime for plain console apps, so `smoke.csproj` carries
  `<RollForward>LatestMajor</RollForward>` (test rig only).
- **`--selftest`** constructs all three run modes, walks all ten realized tabs and every wizard step
  **for every Calling**, and fails on any interactive control carrying no tooltip. It also
  builds the Reference deck on purpose (tabs are realized lazily, so nothing else touches it) and
  checks each title has a renderer.
- **Static wiring audit**: `python audit_ui.py` — every `Btn(...)` supplies a handler and a tooltip,
  every input control is referenced by a handler, and every locally-built `ShowDialog`n Form sets
  `CancelButton` so it answers Esc. Three UX checks joined it in v1.29.2: a **24px minimum target**
  (the floor WCAG 2.5.8 AA and Microsoft's control guidance agree on), **destructive buttons must be
  recoverable** (a `Confirm()`, or an edit to one of the six lists `ListChanged += CaptureUndo`
  covers — an undoable action does not need a prompt, and prompting on all of them trains a Keeper
  to click through the one that matters), and **no two items in one menu claim the same Alt key**
  (Windows demotes a collision from "activate" to "cycle", so a learned shortcut dies silently).
  A fourth joined them in v1.36.0: **a button may refuse, but it may not refuse in silence.** Every
  handler's early `return` is read for a guard that bails without saying anything — the failure that
  is indistinguishable, from the far side of the table, from a dead button. It found six, including
  three Posse buttons and the Tracker's New fight. Two things the check itself had to be taught:
  a guard that hands off to a method which does the talking is not silent (`speaks_for_itself`
  follows one call deep), and a structural null — `mapHost.Parent` before the tab is realized — is
  unreachable from a press and is not a refusal. Both were principled rules rather than an exemption
  list, deliberately: `mapPanel.Model` looks identical to the compiler and *is* a real refusal a
  Keeper needs told, so an exemption list would have suppressed it too.
  Currently 141 buttons, 127 refusal-checked handlers, 24 dialogs, 23 access keys — measured
  2026-08-22, and it had drifted from a typed 134/20, which is this file failing the very rule the
  app is held to (*counts that appear in prose must be derived*). Read the numbers off
  `audits/audit_ui.py` before quoting them. (It was 132 until v1.32.0 turned the Tracker's
  ＋ Turn glass button into a `CheckBox` toggle — a drop of one here means a `Btn` became something
  else, so check that before assuming a control went missing. It went to 134 in v1.33.0 when the
  tour callout's three buttons were rebuilt on `MainForm.Btn` and `TourBtn` was registered in
  `HELPERS`: they had been a bare `new Button` since v1.22, invisible to this audit, and that is
  precisely how they kept their Windows theme through the release that flattened every other bar.
  **A helper the audit does not know about is a set of buttons nobody checks** — register new ones.)
  All three UX checks pass today, so they are
  regression guards — if you add another, prove it against a synthetic source file first, the way
  these were.
- **Dead code is a build error** (v1.29.2). `GK/.editorconfig` sets IDE0051 / IDE0052 / IDE0005 /
  CA1508 to `warning` and both csprojs carry `EnforceCodeStyleInBuild`, so under `-warnaserror` an
  unused private member, a field written and never read, an unnecessary using, or a dead conditional
  stops the build. The sweep that motivated it found a tracker sort mode stored and never read back,
  a Ledger font minted per zoom step and never drawn with, and a null check on `new` — all three
  compiled clean and read as live code. **IDE0005 will not report unless the build generates XML
  docs**, and emits its own build error saying so, so `GenerateDocumentationFile` is on in every
  configuration with `PublishDocumentationFile=false` keeping the `.xml` out of the single-file
  publish. Making it Debug-only looks tidier and breaks the Release build on the demand itself.
- **Look at it.** The app builds and runs natively here, so layout is verifiable and should be
  verified — the v1.19.0 clipped Strike dialog and the "The Crooked The Wall" landmark names both
  passed every assertion and were caught only by rendering. Two safe ways: capture a single window
  with `PrintWindow` (**never a full-screen grab of the user's desktop**), and drive **your own**
  instance through UI Automation's Invoke/SelectionItem patterns rather than synthesizing input.
  Close it with `CloseMainWindow()`, or post `WM_CLOSE` to each window when a modal is up —
  **never `Stop-Process`**, and never touch the user's own running copy. Only ever touch instances
  running out of `GK\source\bin\`, never one running from `GritKeeper\app\`. For maps, the smoke rig
  writes one SVG per sky and per ground to `%TEMP%\gritkeeper-smoke\weather`; render them and look.

## Dialogs are measured, never laid out to constants

The Strike dialog's prose changes with the run mode and with creature-vs-soul, and fixed heights
clipped it. `Para()` sizes a block with `TextRenderer.MeasureText`, everything below is placed off
`.Bottom`, and `ClientSize` comes last. Do the same for any new dialog carrying variable text.

**Button order:** commit LEFT, Cancel RIGHT — and in a `FlowDirection.RightToLeft` bar that means
adding **Cancel first**. Where cancelling is meaningless (the die prompt, the run-mode chooser),
point `CancelButton` at the commit button: Esc should still close the thing.

---

*(Everything below moved down from the root `CLAUDE.md` on 2026-08-03, for the reason this file
was split out in the first place: it is app detail, and it was sitting in every session's context
including the ones that only touch a book. Nothing was rewritten — where a block already had a
counterpart here, the two were merged rather than stacked.)*

## The rules library, and why the JSON had to move with it

`GK/rules/BloodAndGrit.Rules.csproj` is a plain `net10.0` class library — no WinForms — holding the
eight headless files (`Core.cs`, `CharGen.cs`, `IronCode.cs`, `Horror.cs`, `MapGen.cs`, `Pdf.cs`,
`Look.cs`, `Daybook.cs`) **and the six `Data/*.json`**. This replaced `smoke.csproj`'s hand-listed
`<Compile Include>` per file, which could silently fall out of step with what the app contained —
a seventh headless file, unlisted, went untested forever.

**The JSON had to move with `Core.cs` and this is forced, not stylistic:** `Db.ReadData` resolves
resources off `typeof(Db).Assembly`, so embedding it anywhere but beside `Db` makes the lookup find
nothing and fall back to a `Data/` folder a standalone exe doesn't have — a break that shows up only
in the published build. `CharGen.FlavorList` stays `internal`; the smoke rig reaches it through
`<InternalsVisibleTo Include="smoke" />`.

## Sign & spoor — the safe-table rule (v1.20.0)

The numbers live once, in `Rules.SpoorRow` / `SpoorRead` / `SpoorClockSegments` (`Core.cs`), and
everything renders from there — the Reference deck's Long Odds leaf and the Generators tab's ground
roll. The books carry the same table by hand (Bestiary → Appendix: The Grounds → *Sign & Spoor*;
Keeper's Book Ch. IV → *The Safe-Table Rule*; Player's Book Ch. VIII under *Reading the country*).
The claim that binds them is "the Dread DC is one rung below meeting the thing", and the smoke suite
asserts exactly that against `Rules.TierRow[i-1].dread` — so a change to one Tier's Dread DC fails
the build rather than quietly desynchronising book and app.

## Map weather & landforms (v1.19.0)

`MapSpec.Weather` indexes `MapGen.Weathers` (0 = "as the sky wills"); `WeatherFor(pick, ti, rng)`
resolves it against `WeatherByGround`, `WeatherLine` gives the cartouche's wording, and `DrawWeather`
inks it over the hour on its own stream (`R(10)`) so forcing the sky moves nothing else — asserted.
The resolved sky is on `MapModel.Weather`. Landforms (`mountain`, `range`, `ridge`, `bluff`, `butte`,
`hoodoo`, `forest`, `pinestand`, `hills`, `marsh`, `orchard`, `spring`) are `Sym()` cases like any
other. `GroundLandmarks(ti)` gives each ground its own named places; **those names are final** — they
go into `ownName` and skip the "The Crooked …"/"Pryor's …" decorator, which is what produced "The
Crooked The Wall". Weather ink is inset so no stroke lands past the neatline (a smoke test walks every
sky). The cartouche is sized to the longer of title and subtitle.

## Map marker ink (v1.18.0)

`MapInk` in `Core.cs` holds the book's color per kind, the Keeper's standing override (persisted as
`Prefs.Data.MarkerInk`), the 10-color palette, and `Hex()` for the exporters. Plain ARGB ints, never
`Color` — `Core.cs` must stay drawing-free for the smoke rig. `MapMarker.Argb` is one marker's own
choice (0 = take the kind's). `MapGen.MarkerPrims` renders markers as `Prim`s and both writers take
them as an **optional overlay** (`ToSvg(m, overlay)`, `Pdf.MapPdf(m, overlay)`) — never appended to
the model, so the survey the Map tab holds is never mutated by an export. The **with markers**
checkbox is off by default.

## Turn state on the tracker (v1.19.0)

`Combatant.Acting` (persisted) and the derived `NextStrike` ("clean" / "−5" / "−10"). `BeginTurn()`
sets Beats 3, MapStep 1, Acting true; clearing everyone else is the caller's job
(`BeginTurnForSelected`). The tracker shows it three ways — a gold bold row (`ActingRow` + the cached
`trkBold`), a **Next strike** column, and `UpdateTurnLine()` beside the round. `NextRound` clears
Acting.

## The turn hourglass (v1.29.0)

`TurnClock` in the rules library is pure and is FED elapsed milliseconds by its caller, which is the
only reason a five-minute turn can be tested in a millisecond; `HourglassView` in `GK/source` is ink
and nothing else. Three deliberate choices worth keeping: it is **opt-in** (`Prefs.Data.TurnTimer`,
off by default); its **length is a preference**, not session state, because it is a house rule about
how a table plays; and it **never acts on the game** — it logs and turns red, and does not end a turn
or take a Beat, because nothing in the books says a slow player loses their action. The sand level
drops by **√time**, so the *area* the eye reads as "how much is left" falls off linearly. The
animation timer runs only while sand is actually falling (`SyncTicker`).

## Rides — mounts & vehicles (v1.18.0)

The Posse tab is a `Split(Orientation.Horizontal, …)` with the posse above and *the corral & the
yard* below (`TabsRides.cs`). `Ride` in `Core.cs` is an `INotifyPropertyChanged` model in a
`BindingList<Ride>`; the roster is `Data/rides.json` (embedded like the rest), built by `Db.MakeRide`.
New rides are named by `Db.FreeRideName` — the lowest FREE number, not a count of that type, or
selling the middle of three mints a duplicate. Rides ride in `session.json` and go to the tracker as
ordinary `Combatant`s.

## Creature attacks (v1.17.0)

A creature on the tracker Strikes with its OWN attacks, parsed from the Bestiary's free-text `attacks`
line by `CreatureAttack.Parse` in `IronCode.cs` (pure, smoke-tested across all 175 creatures) — no
data-format change; the free-text stays the source of truth, like `WeaponTraits`.
`CombatFlow.StrikeAndApply` has a `CreatureAttack` overload; `IronCode.Strike` takes an optional
`forceType` so an elemental touch types past worn-armor DR.

## Right-click menus (v1.18.0)

`GridMenu<T>` / `ListMenu<T>` + `MI`/`MISep`/`MIHead` in `MainForm.cs` wire a per-row menu onto every
list (posse, rides, tracker, encounter, bestiary, roll log). They **select the row first, then
build**, so each menu line calls the same handler the tab's button calls — a menu that reimplements a
button is a menu that will disagree with it. That's why
`SpendGrit`/`AdvanceMark`/`DeepenTaint`/`AddSoulToTracker`/`RenameRide`/`RideToTracker` exist as
methods rather than button lambdas.

## Run modes (v1.17.0)

Launch shows a chooser — `RunMode.Player` (a player's pared-down view: only New Soul / Dice /
Reference tabs), `RunMode.KeeperDice` (Keeper rolls physical dice and enters the die; a `d20` field
appears in the Strike/Dread dialogs and feeds `forcedDie`), `RunMode.KeeperEngine` (the app rolls
everything). Persisted in `prefs.json` (`Prefs` in `Core.cs`); changeable live from the **Table** menu
(`SetMode` → `ApplyModeTabs` + `RebuildMenu`). `MainForm.EngineRolls` is the live read the dialogs
branch on. The book-edition strings the status bar shows come from one place —
`MainForm.PlayerBookVer`/`KeeperBookVer`/`BestiaryVer` consts (keep them current with the books).
`--selftest` constructs all three modes.

## The tab strip is owner-drawn (v1.29.0)

For one reason: under the Windows visual style the selected tab differed from the other nine by a
couple of pixels of height and nothing else, so the app's answer to "which of the ten am I on" was
almost invisible. `StyleTabs` paints the live tab on `Paper` under a 3px `Blood` rule with its name in
bold Blood; the rest sit back on `TabRest`. `TabDrawMode.OwnerDrawFixed` still lets the control size
each tab to its own text — the ten labels are ten different lengths — and nothing here touches the
pages.

## Contrast is a palette decision, not a per-site one (v1.29.0)

`Gold` measures ~3.5:1 on `Paper`, which is right for a heading and too light for a sentence — and the
app sets whole explanatory paragraphs in it. **`GoldDeep`** is the same hue carried to ~5:1: use
`Gold` for headings and short labels, `GoldDeep` for anything that is a sentence. **`Faint`** replaced
a hand-written `Color.FromArgb(122,112,96)` for "nothing is happening yet" ink. (For the glyphs that
render on this machine, see the drawn-text landmine above.)

## Every control says what it is, and it is a failing check (v1.29.0)

`--selftest`'s tooltip walk is described under the verification standard above; what is worth not
re-learning is how it is built and what it caught. One walker, shared (`MainForm.WalkForTips` /
`WantsTip`) — a wizard held to one standard and ten tabs held to another is two standards, and the
looser one wins. `ButtonBase` rather than `Button` so checkboxes count; containers are walked
*through* but anything that wants a tip is never walked *into* (a `NumericUpDown` holds its own
TextBox and spin buttons). Prose labels are exempt; a caption carrying a **live number** is not prose
and opts in with `Tag = "readout"`.

**What this caught that reading the source did not:** `ItemTips` set a list's tooltip only from
`MouseMove`, so all five wizard lists had *no* resting tip and cleared themselves over the blank
ground below the last row — meaning the two lists that silently refuse a click (past the trained-skill
cap, past what the coin covers) never said why. `ItemTips` now takes a `resting` tip that is the
list's own instructions.

## What a soul looks like (v1.30.0)

`GK/rules/Look.cs` + `Data/appearance.json` — the seventh headless file and the first that is not the
books' rules. Two rules govern it and both are load-bearing.

**Nothing here is worth a point:** it touches no number, gates no Origin or Calling, and the books'
standing line holds — the peoples of the West appear as people, described and never costed.

**The draws are conditioned, not shuffled:** complexion, hair and eyes come out of ONE people's own
lists and every garment out of ONE style's wardrobe (`LkStyle`), because six independent lists produce
a Norwegian in a charro jacket over mining boots and that reads as a machine talking. `callingStyles`
steers the wardrobe 80% of the time and lets the country surprise you the rest.

**The name and the people are one decision:** the look is drawn BEFORE the name and
`FullName(gender, look)` follows it, because `chargen.json`'s whole-name pools used to be reached on a
bare 12% roll answerable to nothing — which was invisible until the app started saying where people
were from, and then produced "Rafferty Luján, Chinese, out of Guangdong" on the first soul it ever
drew on screen. A REDRAW passes `nameIsFixed: true` and leaves out the peoples whose names come whole,
since it is only allowed half the decision. `CharacterSheet.Look` is null on every sheet saved before
this, so every consumer tests `Look?.Any` and no `session.json` migration exists.

## Six-month faults (v1.30.0) — the class of bug a day's testing cannot reach

Four were found by looking for them on purpose. The fourth — fonts minted on repeating paths — has its
own landmine section above; the other three are worth not re-introducing:

1. **`GameSession.IsUntouched`** decides whether the demo posse may be seeded over a loaded session;
   launch used to ask only whether the PARTY was empty, and then not apply the session at all — losing
   the ledger, clocks, rides, map markers and tracker of any all-NPC night. It lives in the rules
   library so the smoke rig holds it.
2. **`AutoSave` returns whether it landed** and says so once per new reason; swallowing the failure was
   right, being silent about it meant a `session.json` unwritable for months looked identical to one
   saving perfectly.
3. Anything that **reparents** a control unwinds in a `finally`. That failure arrives with nothing to
   read: no exception, no dialog, just a tab that stays blank until the app is restarted.

## Counts that appear in prose must be derived, not typed (v1.20.1)

The app told Keepers its reference screen held eleven leaves for two releases while it held thirteen.
`RefLeafCount` is now `RefLeafTitles.Length`, the deck is built by zipping those titles with the
renderers, and every mention interpolates it (the five-minute lesson in `Menus.cs`,
`GK/source/README.md`, the root CLAUDE.md). `--selftest` builds the deck on purpose — tabs are
realized lazily, so nothing else touches it — and checks each title has a renderer.

## Where a Keeper's things live (v1.31.0): `AppState.Dir`, not "beside the exe"

Resolved in three steps — a `portable.txt` beside the exe wins; failing that an existing
`session.json` beside the exe is honoured (nobody is moved off a folder they already use); otherwise
`%APPDATA%\GritKeeper\`, which no build, publish or package step can reach. `session.json`,
`prefs.json`, `session-backup.json` and `session-unreadable.json` all follow it.

**Three things deliberately do NOT:** `startup-error.txt` and `selftest-report.txt`, because a crash
report has to land somewhere findable when the profile is the thing that is broken, and the `Data/`
lookup, which is a read and which the smoke rig depends on. `AppState.Resolve` is pure so the smoke
rig can walk every combination of its inputs.

**The rule for anything new:** if a Keeper would be upset to lose it, it goes through `AppState.Dir`;
if it is a diagnostic about THIS COPY of the exe, it stays beside the exe. Because the state no longer
sits beside the binary, `GritKeeper\app\GritKeeper.exe` is now a perfectly good thing to play from —
it is refreshed by `package.ps1` on every release.

## `GritKeeper\app\` is sanitised on every package, so nothing is kept there (2026-08-01)

Step 1 of `package.ps1` clears `session.json`, `prefs.json`, `startup-error.txt` and
`selftest-report.txt` out of that folder — deliberately, because v1.20.1 shipped with the packager's
own `prefs.json` and every download launched into someone else's table. It **moves** them to
`.package-aside\<timestamp>\` now rather than deleting them: it used `Remove-Item`, which skips the
Recycle Bin, and GritKeeper stages saves to `session.json.new` and keeps no `.bak`, so packaging a
release destroyed the table of anyone playing out of that folder. It did exactly that on 2026-08-01.

Since v1.31.0 moved the state to `AppState.Dir` this is belt-and-braces rather than the only thing
between a Keeper and a lost table, and **`GritKeeper\app\GritKeeper.exe` is the one local copy to play
from** — `package.ps1` refreshes it on every release, so it cannot go stale. There is a
`GritKeeper.lnk` shortcut on the Desktop pointing at it. A second hand-synced copy was tried on
2026-08-01 and deleted the same day: it was a 156 MB duplicate that had already drifted a version
behind, which is what any copy nothing keeps current does.

## "Re-mirror" means overwrite, not sync-and-diff

`GritKeeper/source/` is a *generated* copy of `GK/source` (git-ignored since 2026-07-23, same as
`GritKeeper/app/`) — blow it away and rewrite it from the master tree every package:

```powershell
robocopy GK\source GritKeeper\source /MIR /XD bin obj publish
robocopy GK\rules  GritKeeper\rules  /MIR /XD bin obj publish
```

Both trees, and they ship as **siblings** — the app's `<ProjectReference>` points at `..\rules\`, so
flattening or renaming either one leaves the delivered source unable to build. `package.ps1` does both
in a loop and its zip check asserts `rules/Core.cs` and `rules/Data/creatures.json`.
(`/XD bin obj publish` keeps the .NET build output out of the deliverable; robocopy exit codes 0–7 are
success.) Then drop the published `GritKeeper.exe` into `GritKeeper\app\` and re-zip to
`GritKeeper.zip`.

## `sign.ps1` and `package.ps1` — the scripted half of a release

`sign.ps1` Authenticode-signs the published exe with the code-signing cert in `CurrentUser\My`
(native `Set-AuthenticodeSignature`, no Windows SDK / signtool needed; timestamped when a server is
reachable). `package.ps1` then copies the signed exe into `GritKeeper\app\`, re-mirrors
`GritKeeper\source`, and writes `GritKeeper.zip` — refusing an unsigned exe unless you pass `-Force`
(a local test build). It verifies the zip's contents before declaring itself ready and prints the
matching `gh release create` line.

The zip, the `app/` exe, the `source/` mirror **and the `RELEASE_NOTES_vX.Y.Z.md` file itself** are
all git-ignored (release assets, never committed). The notes file is scratch: write it, paste it into
the Release, leave it on disk. Once published, the text lives on the Release and the durable history
lives in `CHANGELOG.md` — a copy in the repo root is a third place to drift. (Seven had accumulated
there by v1.20.1; removed 2026-07-27.)

**`package.ps1` handles a running app (v1.20.1).** If GritKeeper is running out of `GritKeeper\app\`
it holds its own exe, and the copy step used to die on a raw file-lock error mid-release. The script
now finds the process, names it with pid and start time, and falls back to a staging tree so the zip
is still correct — the running instance is never touched, and it says plainly that `GritKeeper\app`
stays on its old build until closed. Pass `-Staged` to force that path.
