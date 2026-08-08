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
`GK/rules/` (the `net8.0` rules library — the eight headless `.cs` files and `Data/*.json`),
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
| `Program.cs` | Entry point. Wraps startup in global exception handlers that write `startup-error.txt` beside the exe (or `%TEMP%`) on any crash — so failures are never silent. Opens the `Daybook` (and points it at `daybook.txt` under `--verbose`), and folds its dump into both error reports. Also hosts `--selftest`. |
| **`Daybook.cs`** | The capped record of what the app just did — rolls, checks, session saves/loads, mode switches, generated souls — for the failure that never throws and so writes no error file. **Inert until `Open()`**, which only the app calls: the smoke rig fuzzes the paths it listens to thousands of times per build. Ring of `Cap` (400), fails soft on every write, `Dump()` says "not recording" rather than reading as an empty night. Surfaced at **Help ▸ Save a diagnostic log…**. |
| `app.ico` / `Assets/emblem.png` | The cover emblem as a multi-size Windows icon (regenerate from `assets/img20.png` if the emblem changes) and as the watermark PNG. Both embedded. |
| `Data/creatures.json` | All 150 creatures, extracted from `bestiary.html` by `extract_creatures.py`. Re-extract and drop in fresh if the Bestiary content changes — no code changes needed. **Embedded into the exe.** |
| `Data/tables.json` | The 17 simple tables + 11 Grounds terrain tables, same extraction approach. **Book-faithful — never hand-edit; a re-extraction replaces it wholesale.** |
| `Data/tables_extra.json` | The app's own generator expansions. Merged after `tables.json` by `Db.MergeTables`, so re-extraction can't eat them. |
| **`Look.cs`** | What a soul looks like — `SoulLook` (the description, carried on `CharacterSheet.Look`) and `Look.Roll`. Pure, in the rules library, drawing-free. The two rules that govern it are below, under *What a soul looks like*. |
| `Data/appearance.json` | 28 peoples, 19 whole styles of dress, and the shared pools for build, bearing, face, marks, voice, hair, whiskers, wear and the one memorable detail. **The app's own, not the books'** — like `tables_extra.json`, and for the same reason: `chargen.json` is a transcription and must stay one. **Embedded**, like the rest. |

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
  `CancelButton` so it answers Esc. Three UX checks joined it in v1.29.2: a **24px minimum target**
  (the floor WCAG 2.5.8 AA and Microsoft's control guidance agree on), **destructive buttons must be
  recoverable** (a `Confirm()`, or an edit to one of the six lists `ListChanged += CaptureUndo`
  covers — an undoable action does not need a prompt, and prompting on all of them trains a Keeper
  to click through the one that matters), and **no two items in one menu claim the same Alt key**
  (Windows demotes a collision from "activate" to "cycle", so a learned shortcut dies silently).
  Currently 134 buttons, 20 dialogs, 22 access keys. (It was 132 until v1.32.0 turned the Tracker's
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

`GK/rules/BloodAndGrit.Rules.csproj` is a plain `net8.0` class library — no WinForms — holding the
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
line by `CreatureAttack.Parse` in `IronCode.cs` (pure, smoke-tested across all 150 creatures) — no
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
