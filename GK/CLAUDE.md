# GritKeeper — the C# app

Loaded whenever work touches anything under `GK/`. Split out of the root `CLAUDE.md` on
2026-07-30: it was ~35,000 characters of app detail sitting in every session's context, including
sessions that never opened a `.cs` file. The root file keeps the two landmines that can ruin a
release (`SplitContainer` geometry, `dotnet publish -o`) and points here for the rest.

A standalone Keeper-facing utility for running games at the table, built in **C#/.NET 8, Windows
Forms**. Not part of the HTML book pipeline — separate source tree, separate build. **Renamed from
"The Keeper's Table" to GritKeeper in v1.5.0** — exe `GritKeeper.exe`, product/title/About/README
all updated; the **internal namespace stays `BloodAndGritKeeper`** (deliberately — embedded-resource
names derive from it). As of 2026-07-19 (v1.6.0) the folders match the name too: working tree
**`GK/`** (was `KT/`), delivered folder **`GritKeeper/`**, zip **`GritKeeper.zip`**. The last
"Keeper's Table" strings inside the app (session file-dialog filters, crash-report captions) were
also renamed in v1.6.0.

## Source-tree layout (read before editing the app)

The working/master tree is **`GK/`**, and since v1.28.0 it holds **three** projects:
`GK/rules/` (the `net8.0` rules library — the six headless `.cs` files and `Data/*.json`),
`GK/source/` (the WinForms app: the UI `.cs`, its `.csproj`, `app.ico`, `Assets/`), and
`GK/smoke/` (the headless logic-test project). The app and the smoke rig both reference the
library. **Edit `GK/rules` for rules and data, `GK/source` for UI; build/test in `GK/`.**

**Which tree does a change belong in?** If the smoke rig should be able to test it, it goes in
`GK/rules` — that is now the whole criterion, and it is enforced by the compiler rather than by
remembering to add a line to `smoke.csproj`. Anything touching `System.Windows.Forms` or
`System.Drawing` cannot go there and belongs in `GK/source`. (This is why `Rules.ResetForNewFight`,
`MapGen.SettingTerrains` and `Db.RollAdventure` live where they do — logic that sat in `Tabs.cs`
was untestable, and that is exactly how the v1.24.2 `NewFight()` bug escaped.)

**The build output is `GK/source/bin/Release/net8.0-windows/win-x64/` — RID-qualified, and the
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

Snapshot-based, over the same `GameSession` shape File → Save/Load already uses:
`party`/`tracker`/`encounter`/`clocks` (the four `BindingList`s) each push a JSON
snapshot onto an undo stack on any `ListChanged` (add/remove/edit), capped at 50 deep;
`Undo`/`Redo` restore via `ApplySession`, which now suppresses re-capture during its own
bulk rebuild so a restore is one step, not N. Reachable from **Edit ▸ Undo/Redo**
(Ctrl+Z/Ctrl+Y) or matching buttons pinned in the status bar, so it's live no matter
which tab is open. Session notes deliberately aren't captured — the textbox's own native
undo covers it, since snapshotting every keystroke would flood the stack.

## The ten tabs

Per-version feature history lives in `CHANGELOG.md`, which is the version record; what follows is
what each tab *is*, plus the decisions worth not re-deriving.

- **Posse** — full party sheet (Blood, Defense, saves, Nerve, Grit, Mark 0–6, Taint 0–4), inline
  damage/heal spinners, Spend Grit, Mark/Taint advance, per-soul or whole-posse Dread Checks with
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
- **Bestiary** — all **150 creatures**, machine-extracted from the rendered Bestiary HTML, so
  lore/stats/witness quotes/keeper notes are word-for-word faithful to the book. Search, tier and
  chapter filters, one click to Encounter or Tracker, double-click to pop a creature into its own
  resizable window with A−/A＋ zoom — one window per creature, reused if open, cascading placement.
- **Encounter** — the book's budget math (4 pts/PC; Even 4 / Mook 1 / Standout 8) costed live
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
    itself. `Combatant.HasActed` is the spine; `Rules.NextUp`/`CanAct`/`RoundSpent` are the pure
    logic — the downed are skipped, traces never counted, ties broken by name so the order never
    wobbles. The round is a **spinner**, not a label: the app keeps it, the Keeper can correct it.
  - **`Btn` is `FlatStyle.System`, which silently ignores `BackColor` and `FlatAppearance`.**
    `PrimaryBtn` / `DangerBtn` exist for exactly this reason — both switch to `FlatStyle.Flat`,
    the only way to actually colour a WinForms button. In the grid, an editable column carries ✎
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
  both ability methods, all 17 Callings and 10 Origins with their cross-constraints honored.
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
  arrow keys captured in `ProcessCmdKey` so focus doesn't matter. Monospace tables with Blood-red
  header bands (`RTbl`). The arms, goods, signs and skills leaves render live from
  `Data/chargen.json` so they can't drift.
- **Session** — free-form Keeper's notes + named 4/6/8-segment progress clocks. Autosaves to
  `session.json` beside the exe on exit **and every 5 minutes**; reloads on launch. First run seeds
  the Appendix D pregens so it's useful immediately.

## Files

| File | Role |
|---|---|
| `BloodAndGritKeeper.csproj` | Project file. `net8.0-windows`, `UseWindowsForms`, `EnableWindowsTargeting`. Also carries the **self-contained single-file publish settings** (RID win-x64, `SelfContained`, `PublishSingleFile`) so `dotnet publish` always yields a zero-dependency exe. |
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
| `Program.cs` | Entry point. Wraps startup in global exception handlers that write `startup-error.txt` beside the exe (or `%TEMP%`) on any crash — so failures are never silent. Also hosts `--selftest`. |
| `app.ico` / `Assets/emblem.png` | The cover emblem as a multi-size Windows icon (regenerate from `assets/img20.png` if the emblem changes) and as the watermark PNG. Both embedded. |
| `Data/creatures.json` | All 150 creatures, extracted from `bestiary.html` by `extract_creatures.py`. Re-extract and drop in fresh if the Bestiary content changes — no code changes needed. **Embedded into the exe.** |
| `Data/tables.json` | The 17 simple tables + 11 Grounds terrain tables, same extraction approach. **Book-faithful — never hand-edit; a re-extraction replaces it wholesale.** |
| `Data/tables_extra.json` | The app's own generator expansions. Merged after `tables.json` by `Db.MergeTables`, so re-extraction can't eat them. |

## Build & run

```bash
# Requires the official Microsoft .NET 8 SDK (Ubuntu's apt package lacks WindowsDesktop targets).
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

Deliverable = **just `bin/Release/net8.0-windows/win-x64/publish/GritKeeper.exe`** (~155 MB;
`EnableCompressionInSingleFile` and `PublishReadyToRun` are deliberately **off** for startup speed
and Defender scan time, which is why it is not the ~69 MB a compressed publish would be — the zip
comes out ~63 MB) — a **true single-file standalone**: the .NET runtime is bundled *and* the
`Data/*.json` are **embedded in the exe**, so it runs on any Windows machine with no .NET install
and no `Data/` folder beside it. `Db.ReadData` loads the JSON from the assembly, and falls back to
`Data/` on disk for the smoke rig / dev build. The exe writes only `session.json` beside itself
(via `AppContext.BaseDirectory`). Published on GitHub via **Releases**, never committed — the
binary is git-ignored.

**A Linux package is planned** (decided 2026-07-29). The engine half has been done since v1.28.0:
`GK/rules` is a plain `net8.0` library with no Windows reference — exactly what the headless smoke
rig builds against — so the rules, chargen, map generator and PDF writer all run on Linux today.
What a Linux build has to answer is the **UI**: `GK/source` is `net8.0-windows` + WinForms and
cannot cross that line, so this means a second front-end against the same library, not a port.
Anything added to the rules library should stay drawing-free and WinForms-free for that reason.
**Until something ships, every mention of it says "planned" and gives no date**: the standing rule
that the app never promises what it cannot keep applies to a roadmap as much as to a feature. The
places carrying the note, which must be kept in step, are `README.md`, `GK/source/README.md`, and
the app's own **Help ▸ What it needs to run** (`ShowRequirements` in `Menus.cs`).

## Known landmine: SplitContainer must not get geometry at construction time

**Hit once, cost a full crash-on-launch on real Windows.** Setting
`SplitterDistance`/`Panel1MinSize`/`Panel2MinSize` on a `SplitContainer` *before* it's been docked
and laid out throws `SplitterDistance must be between Panel1MinSize and Width - Panel2MinSize`,
because at construction time the control's width is some tiny placeholder, not its real docked
size. This compiles fine and passes headless logic tests — it only throws when the window actually
renders.

**The fix, already in `MainForm.cs`:** a `Split(orientation, p1Min, p2Min, ratio)` helper that
creates the SplitContainer bare and defers all geometry to a one-shot `SizeChanged` handler, which
only fires once the control has a real size, clamps mins against small windows, and unsubscribes
itself after succeeding. **Always build new splitters through this helper.**

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

## Verification standard for this app

- `dotnet build -c Release` → 0 warnings, 0 errors (`-warnaserror` in CI).
- **Headless logic tests** (`GK/smoke`, `dotnet run -c Release`): dice-range checks, all
  four-degrees edge cases (including the nat-20-on-a-failure / nat-1-on-a-success regression cases
  — there was a real bug here once, a signed band scale with a gap at zero; fixed by moving to an
  ordered 0–3 scale), `RollExprFull` per-die/total agreement, encounter costs, the Nerve ladder,
  model clamping, `INotifyPropertyChanged` firing, serialization round-trips, full data-load checks
  (150 creatures parse, table merge counts, no duplicates, **every terrain-table entry resolves to
  a real creature by name**), `CharGen.Assemble` conformance sweeps with junk-choice fuzzing,
  `LevelUp` proved across every calling × ability method × level 1→10, Trail Maps
  generation/SVG/PDF structural + determinism checks, and `TurnClock`. Re-run after any
  `rules/`-side or data change. **Read the failures, not the total** — it drifts by a few dozen run
  to run because several sweeps assert once per random draw. Growth by release is in `CHANGELOG.md`.
  Note: this machine has only the .NET 9 runtime for plain console apps, so `smoke.csproj` carries
  `<RollForward>LatestMajor</RollForward>` (test rig only).
- **`--selftest`** constructs all three run modes, walks all ten realized tabs and every wizard step
  **for all seventeen Callings**, and fails on any interactive control carrying no tooltip. It also
  builds the Reference deck on purpose (tabs are realized lazily, so nothing else touches it) and
  checks each title has a renderer.
- **Static wiring audit**: `python audit_ui.py` — every `Btn(...)` supplies a handler and a tooltip,
  every input control is referenced by a handler, and every locally-built `ShowDialog`n Form sets
  `CancelButton` so it answers Esc. Currently 128 buttons, 19 dialogs.
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
