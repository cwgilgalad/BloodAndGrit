# Blood & Grit — Project Handoff & Preferences

Import this file into the project so a fresh chat can pick up exactly where we left off.
For onboarding a fresh Project, hand over **the current loose files from the repo** — the
builders (`build_player.py` / `build_keeper.py` / `build_bestiary.py`), the shared modules
(`nav_tools.py`, `perdition_map.py`, `pag_patch.py`), `assets/`, and whatever else the task
touches — not a packaged snapshot. (Packaged snapshots go stale silently: the old
`blood-and-grit-sources.zip`, deleted 2026-07-23, sat at its day-one 2026-07-11 contents
while the build architecture moved on underneath it.)

**Current versions: Player's Book v2.25 · Keeper's Book v2.12 · Bestiary v2.11 ·
GritKeeper app v1.29.2 (renamed from "The Keeper's Table" in v1.5.0; self-contained,
crash-hardened, Authenticode-signed, exe `GritKeeper.exe`).**

**The rules are their own library (since v1.28.0).** `GK/rules/BloodAndGrit.Rules.csproj` is a plain
`net8.0` class library — no WinForms — holding the six headless files (`Core.cs`, `CharGen.cs`,
`IronCode.cs`, `Horror.cs`, `MapGen.cs`, `Pdf.cs`) **and the five `Data/*.json`**. `GK/source` is
the WinForms app on top of it; it and `GK/smoke` both reach it by `<ProjectReference>`. This
replaced `smoke.csproj`'s hand-listed `<Compile Include>` per file, which could silently fall out
of step with what the app contained — a seventh headless file, unlisted, went untested forever.
**The JSON had to move with `Core.cs` and this is forced, not stylistic:** `Db.ReadData` resolves
resources off `typeof(Db).Assembly`, so embedding it anywhere but beside `Db` makes the lookup
find nothing and fall back to a `Data/` folder a standalone exe doesn't have — a break that shows
up only in the published build. `CharGen.FlavorList` stays `internal`; the smoke rig reaches it
through `<InternalsVisibleTo Include="smoke" />`.

**Sign & spoor — the safe-table rule (v1.20.0):** the numbers live once, in `Rules.SpoorRow` /
`SpoorRead` / `SpoorClockSegments` (`Core.cs`), and everything renders from there — the Reference
deck's Long Odds leaf and the Generators tab's ground roll. The books carry the same table by
hand (Bestiary → Appendix: The Grounds → *Sign & Spoor*; Keeper's Book Ch. IV → *The Safe-Table
Rule*; Player's Book Ch. VIII under *Reading the country*). The claim that binds them is "the
Dread DC is one rung below meeting the thing", and the smoke suite asserts exactly that against
`Rules.TierRow[i-1].dread` — so a change to one Tier's Dread DC fails the build rather than
quietly desynchronising book and app.

**Map weather & landforms (v1.19.0):** `MapSpec.Weather` indexes `MapGen.Weathers` (0 = "as the
sky wills"); `WeatherFor(pick, ti, rng)` resolves it against `WeatherByGround`, `WeatherLine`
gives the cartouche's wording, and `DrawWeather` inks it over the hour on its own stream
(`R(10)`) so forcing the sky moves nothing else — asserted. The resolved sky is on
`MapModel.Weather`. Landforms (`mountain`, `range`, `ridge`, `bluff`, `butte`, `hoodoo`,
`forest`, `pinestand`, `hills`, `marsh`, `orchard`, `spring`) are `Sym()` cases like any other.
`GroundLandmarks(ti)` gives each ground its own named places; **those names are final** — they
go into `ownName` and skip the "The Crooked …"/"Pryor's …" decorator, which is what produced
"The Crooked The Wall". Weather ink is inset so no stroke lands past the neatline (a smoke test
walks every sky). The cartouche is sized to the longer of title and subtitle.

**Turn state on the tracker (v1.19.0):** `Combatant.Acting` (persisted) and the derived
`NextStrike` ("clean" / "−5" / "−10"). `BeginTurn()` sets Beats 3, MapStep 1, Acting true;
clearing everyone else is the caller's job (`BeginTurnForSelected`). The tracker shows it three
ways — a gold bold row (`ActingRow` + the cached `trkBold`), a **Next strike** column, and
`UpdateTurnLine()` beside the round. `NextRound` clears Acting.

**Every control says what it is, and it is a failing check (v1.29.0).** `--selftest` walks all ten
realized tabs and every step of the wizard **for all seventeen Callings**, and fails on any
interactive control carrying no tooltip. One walker, shared (`MainForm.WalkForTips` / `WantsTip`) —
a wizard held to one standard and ten tabs held to another is two standards, and the looser one wins.
`ButtonBase` rather than `Button` so checkboxes count; containers are walked *through* but anything
that wants a tip is never walked *into* (a `NumericUpDown` holds its own TextBox and spin buttons).
Prose labels are exempt; a caption carrying a **live number** is not prose and opts in with
`Tag = "readout"`. **What this caught that reading the source did not:** `ItemTips` set a list's
tooltip only from `MouseMove`, so all five wizard lists had *no* resting tip and cleared themselves
over the blank ground below the last row — meaning the two lists that silently refuse a click (past
the trained-skill cap, past what the coin covers) never said why. `ItemTips` now takes a `resting`
tip that is the list's own instructions.

**Every modal dialog answers Esc (v1.29.0).** Wiring `AcceptButton` and leaving `CancelButton` unset
compiles, looks finished, and produces a modal that ignores the one key everybody presses first —
which reads as a hung window, not as a firm question. Four had drifted that way, two of them the
**Strike and Dread** dialogs. Where cancelling is meaningless (the die prompt, the run-mode chooser),
point `CancelButton` at the commit button: Esc should still close the thing, and doing what the title
bar's ✕ already does is honest. `audit_ui.py` checks every locally-built Form that is `ShowDialog`n
(19 of them). **Button order:** commit LEFT, Cancel RIGHT — and in a `FlowDirection.RightToLeft` bar
that means adding **Cancel first**.

**The tab strip is owner-drawn (v1.29.0),** for one reason: under the Windows visual style the
selected tab differed from the other nine by a couple of pixels of height and nothing else, so the
app's answer to "which of the ten am I on" was almost invisible. `StyleTabs` paints the live tab on
`Paper` under a 3px `Blood` rule with its name in bold Blood; the rest sit back on `TabRest`.
`TabDrawMode.OwnerDrawFixed` still lets the control size each tab to its own text — the ten labels
are ten different lengths — and nothing here touches the pages.

**Contrast is a palette decision, not a per-site one (v1.29.0).** `Gold` measures ~3.5:1 on `Paper`,
which is right for a heading and too light for a sentence — and the app sets whole explanatory
paragraphs in it. **`GoldDeep`** is the same hue carried to ~5:1: use `Gold` for headings and short
labels, `GoldDeep` for anything that is a sentence. **`Faint`** replaced a hand-written
`Color.FromArgb(122,112,96)` for "nothing is happening yet" ink. Also: **do not use ⧖ (U+29D6)** —
it is not in Segoe UI on this machine and renders as "≥". The glyphs that do render are
▶ ▾ ◀ ▸ ◂ ✕ ＋ ✎ ✦ ✝ ◈ ✚ ✥ ⟲ ⟳ 🔍 🎲 🧭.

**The turn hourglass (v1.29.0)** — `TurnClock` in the rules library is pure and is FED elapsed
milliseconds by its caller, which is the only reason a five-minute turn can be tested in a
millisecond; `HourglassView` in `GK/source` is ink and nothing else. Three deliberate choices worth
keeping: it is **opt-in** (`Prefs.Data.TurnTimer`, off by default); its **length is a preference**,
not session state, because it is a house rule about how a table plays; and it **never acts on the
game** — it logs and turns red, and does not end a turn or take a Beat, because nothing in the books
says a slow player loses their action. The sand level drops by **√time**, so the *area* the eye reads
as "how much is left" falls off linearly. The animation timer runs only while sand is actually
falling (`SyncTicker`).

**Dialogs are measured, never laid out to constants (v1.19.0).** The Strike dialog's prose
changes with the run mode and with creature-vs-soul, and fixed heights clipped it. `Para()`
sizes a block with `TextRenderer.MeasureText`, everything below is placed off `.Bottom`, and
`ClientSize` comes last. Do the same for any new dialog that carries variable text.

**Rides — mounts & vehicles (v1.18.0):** the Posse tab is a `Split(Orientation.Horizontal, …)`
with the posse above and *the corral & the yard* below (`TabsRides.cs`). `Ride` in `Core.cs` is
an `INotifyPropertyChanged` model in a `BindingList<Ride>`; the roster is `Data/rides.json`
(embedded like the rest), built by `Db.MakeRide`. New rides are named by `Db.FreeRideName` —
the lowest FREE number, not a count of that type, or selling the middle of three mints a
duplicate. Rides ride in `session.json` and go to the tracker as ordinary `Combatant`s.

**Right-click menus (v1.18.0):** `GridMenu<T>` / `ListMenu<T>` + `MI`/`MISep`/`MIHead` in
`MainForm.cs` wire a per-row menu onto every list (posse, rides, tracker, encounter, bestiary,
roll log). They **select the row first, then build**, so each menu line calls the same handler
the tab's button calls — a menu that reimplements a button is a menu that will disagree with it.
That's why `SpendGrit`/`AdvanceMark`/`DeepenTaint`/`AddSoulToTracker`/`RenameRide`/`RideToTracker`
exist as methods rather than button lambdas. `audit_ui.py` still passes (128 buttons).

**Map marker ink (v1.18.0):** `MapInk` in `Core.cs` holds the book's color per kind, the Keeper's
standing override (persisted as `Prefs.Data.MarkerInk`), the 10-color palette, and `Hex()` for the
exporters. Plain ARGB ints, never `Color` — `Core.cs` must stay drawing-free for the smoke rig.
`MapMarker.Argb` is one marker's own choice (0 = take the kind's). `MapGen.MarkerPrims` renders
markers as `Prim`s and both writers take them as an **optional overlay** (`ToSvg(m, overlay)`,
`Pdf.MapPdf(m, overlay)`) — never appended to the model, so the survey the Map tab holds is never
mutated by an export. The **with markers** checkbox is off by default.

**GritKeeper run modes (v1.17.0):** launch shows a chooser — `RunMode.Player` (a player's
pared-down view: only New Soul / Dice / Reference tabs), `RunMode.KeeperDice` (Keeper rolls
physical dice and enters the die; a `d20` field appears in the Strike/Dread dialogs and feeds
`forcedDie`), `RunMode.KeeperEngine` (the app rolls everything). Persisted in `prefs.json`
beside the exe (`Prefs` in `Core.cs`); changeable live from the **Table** menu (`SetMode` →
`ApplyModeTabs` + `RebuildMenu`). `MainForm.EngineRolls` is the live read the dialogs branch on.
The book-edition strings the status bar shows now come from one place — `MainForm.PlayerBookVer`
/`KeeperBookVer`/`BestiaryVer` consts (keep them current with the books). `--selftest` constructs
all three modes.

**Creature attacks (v1.17.0):** a creature on the tracker Strikes with its OWN attacks, parsed
from the Bestiary's free-text `attacks` line by `CreatureAttack.Parse` in `IronCode.cs` (pure,
smoke-tested across all 150 creatures) — no data-format change; the free-text stays the source
of truth, like `WeaponTraits`. `CombatFlow.StrikeAndApply` has a `CreatureAttack` overload;
`IronCode.Strike` takes an optional `forceType` so an elemental touch types past worn-armor DR.

**Standing rule (2026-07-18): the GritKeeper app is synced in the same session as any
book change that touches it** — status-bar/README version strings every time the books bump,
`Data/creatures.json` re-extracted whenever Bestiary creature content changes (extractor
lives in the repo as `extract_creatures.py` — verify with a diff against the previous JSON),
and the Reference tab whenever a rule it quotes changes. Then build, smoke, publish,
**re-mirror `GritKeeper/`**, and rezip.

**"Re-mirror" means overwrite, not sync-and-diff.** `GritKeeper/source/` is a *generated*
copy of `GK/source` (git-ignored since 2026-07-23, same as `GritKeeper/app/`) — blow it away
and rewrite it from the master tree every package:
```powershell
robocopy GK\source GritKeeper\source /MIR /XD bin obj publish
robocopy GK\rules  GritKeeper\rules  /MIR /XD bin obj publish
```
Both trees, and they ship as **siblings** — the app's `<ProjectReference>` points at `..\rules\`,
so flattening or renaming either one leaves the delivered source unable to build. `package.ps1`
does both in a loop and its zip check asserts `rules/Core.cs` and `rules/Data/creatures.json`.
(`/XD bin obj publish` keeps the .NET build output out of the deliverable; robocopy exit
codes 0–7 are success.) Then drop the published `GritKeeper.exe` into `GritKeeper\app\` and
re-zip to `GritKeeper.zip`.

**Counts that appear in prose must be derived, not typed (v1.20.1).** The app told Keepers its
reference screen held eleven leaves for two releases while it held thirteen. `RefLeafCount` is now
`RefLeafTitles.Length`, the deck is built by zipping those titles with the renderers, and every
mention interpolates it (the five-minute lesson in `Menus.cs`, `GK/source/README.md`, this doc).
`--selftest` builds the deck on purpose — tabs are realized lazily, so nothing else touches it —
and checks each title has a renderer. Apply the same shape to any other number the prose quotes.

**`package.ps1` handles a running app (v1.20.1).** If GritKeeper is running out of `GritKeeper\app\`
it holds its own exe, and the copy step used to die on a raw file-lock error mid-release. The script
now finds the process, names it with pid and start time, and falls back to a staging tree so the zip
is still correct — the running instance is never touched, and it says plainly that `GritKeeper\app`
stays on its old build until closed. Pass `-Staged` to force that path. It also verifies the zip's
contents before declaring itself ready and prints the matching `gh release create` line.

**This is now scripted: `sign.ps1` + `package.ps1`.** `sign.ps1` Authenticode-signs the
published exe with the code-signing cert in `CurrentUser\My` (native
`Set-AuthenticodeSignature`, no Windows SDK / signtool needed; timestamped when a server is
reachable). `package.ps1` then copies the signed exe into `GritKeeper\app\` (dropping the
runtime `session.json`), re-mirrors `GritKeeper\source`, and writes `GritKeeper.zip` — refusing
an unsigned exe unless you pass `-Force` (a local test build). So a release is:
`dotnet publish -c Release` → `.\sign.ps1` → `.\package.ps1` → upload the zip with the matching
`RELEASE_NOTES_vX.Y.Z.md`. The zip, the `app/` exe, the `source/` mirror **and the notes file
itself** are all git-ignored (release assets, never committed). The notes file is scratch: write
it, paste it into the Release, leave it on disk. Once published, the text lives on the Release
and the durable history lives in `CHANGELOG.md` — a copy in the repo root is a third place to
drift. (Seven had accumulated there by v1.20.1; removed 2026-07-27.)

*(Build architecture as of 2026-07-18: **one builder per book, content inside the
builder** — `build_player.py` carries the whole Player's Book HTML as its embedded
`SRC` string (the old `player-src.html` is retired), `build_bestiary.py` absorbed
`bestiary_extra.py`, and the Keeper/Bestiary builders read `blood-and-grit.html`
directly (no more manual `cp` step). The conversion was verified byte-identical for
all three books. The multi-pass feathering paginator lives in the Player `SRC`'s
script block, and `pag_patch.py` detects it and no-ops.)*
*(Keep this doc updated with every change — see CHANGELOG.md.)*

This project has two halves: **the three companion books** (HTML/CSS/JS, built by Python
scripts) and **GritKeeper** (a C#/.NET 8 WinForms desktop app for running the game
at the table). They're independent deliverables — different source trees, different build
tools — documented in their own sections below.

---

## How I like to work

- **I work primarily in Claude Code CLI with PowerShell on the Windows laptop now** (updated
  2026-07-13; this project began phone-first). **Responsive design is still a priority:**
  deliverables must render well on a phone — keep the mobile checks in every verification
  pass (page parity, zero true-scale clip, zero h-scroll at natural zoom) and keep artifacts
  reasonably small.
- **I direct in plain words** ("add a Tier-III creature called X," "rewrite the Afflictions
  intro," "cut the Pursuit section," "move that plate," "tighten the whitespace"). You do the
  whole loop: edit the source → rebuild → re-measure the contents page numbers → verify →
  hand back the files. Don't make me do the fiddly parts.
- **Keep the rich book design.** Never convert these to plain markdown — that throws away the
  layout, covers, stat-block styling, and paginator. The look is the point.
- **Default to the cheapest-to-version form.** Edit lean text sources + external image assets
  + build scripts. The big self-contained HTML and the PDFs are generated artifacts, never
  the thing to hand-edit. Ranking, cheapest → most expensive to version:
  **lean source + external assets  ›  self-contained HTML  ›  PDF.**
- **PDFs: automatic here, on request everywhere else (updated 2026-07-22).** When the work is
  being done **in Claude Code / PowerShell CLI on my laptop**, regenerate the PDFs as part of
  any change that touches book content — run `python make_pdf.py` once the books build and
  measure clean, and hand them back with the HTML. No need to ask. **In any other
  environment, the old rule stands:** don't run the PDF pipeline unless I say "save to PDF"
  (or similar) in so many words. Either way the lean sources and the self-contained HTML
  remain the primary deliverables; the PDFs are an extra, never a replacement.
- **Keep this handoff doc current.** When I make changes, update the version table, the
  Changelog, and any affected section so a fresh chat is never working from stale facts.
- **Work on session branches, merge on success — every edit, no exceptions.** Before making
  any change in a session (code, books, docs, scripts), create
  `session/<yyyy-mm-dd>-<short-topic>` and work there. The autosync task is branch-aware and
  backs the branch up to GitHub every 30 minutes. When the session's changes are verified
  (build 0/0, smoke suite green, books measure clean — or, for doc edits, simply read back
  correct), merge into `main` with `--no-ff` and delete the branch (local + origin). If the
  changes go bad, abandon the branch — `main` stays clean.
- **The GritKeeper app now builds natively on this Windows laptop** (verified
  2026-07-18: .NET SDK 9 is installed; `dotnet build` / `dotnet publish` / the smoke suite
  all run locally, and the WinForms window can actually be launched here). The old
  "built and tested blind on Linux" caveat is history — but the SplitContainer landmine
  note in the app section still applies. If a crash does slip through, the app writes
  `startup-error.txt` beside the exe.

---

## The project

**Blood & Grit** — a western-horror tabletop RPG (Pathfinder-2E-derived d20 hybrid).
Three companion books share one HTML engine (cover + client-side paginator + print CSS):

| Book | Version | Pages† | Images |
|---|---|---|---|
| The Player's Book | v2.25 | 200 | one inline SVG map (Appendix E) + cover emblem |
| The Keeper's Book (GM guide) | v2.12 | 101 | one inline SVG map (Ch. XIII) + cover emblem |
| The Bestiary | v2.11 | 166 | none (150 creatures) |

All three now carry a **generated two-level detailed Contents** (chapters + their sub-headings,
built at build time by `nav_tools.py` so it never drifts) and a **back-of-book Index** (the
Player's since v2.9; the Keeper's and Bestiary's new in v2.2/v2.2). Both navigation aids resolve
every page number live via the paginator, exactly like the original TOC. New in this pass: a
worked sample county, **Perdition Basin** (`perdition_map.py` draws its two-layer SVG map — a
clean player map and a secrets-annotated Keeper map — from one shared coordinate model).

† Page counts as rendered on the user's Windows laptop (Edge/Chromium, July 2026). **Pagination
is environment-dependent:** the Linux/cloud environment that measured earlier counts (163/73/130)
paginates 1–2 pages tighter than Windows because font metrics differ per platform. This is not a
bug — the books self-paginate and self-number at render time (all TOC/index `span.pg` numbers are
resolved live by the paginator), so readers always see correct numbers. The *static* numbers baked
into the source are a no-JS fallback only; the pre-index chapter statics still carry the Linux
baseline, while the Index entries carry Windows-measured values.

Covers form a triad — **gold** (Player) / **oxblood** (Keeper) / **verdigris** (Bestiary) —
all sharing the **steer-skull-and-crossed-rifles emblem** and the subtitle "A Roleplaying
Game of the Haunted Frontier." The Player's Book is the shell: the other two are built by
cloning it and splicing in their own content.

### Current design state (the old doc was wrong on all of this)
- **All three book interiors are illustration-free.** The Player's Book's 18 plates were
  removed for visual continuity across the set (the Keeper and Bestiary never had plates).
  **The plate images are not in this repo** — `assets/` holds `img20.png` (the
  cover emblem) and nothing else, and git has never tracked anything else there. Restoring
  plates means generating new artwork, not recovering old files. (Corrected 2026-07-26; this
  doc claimed for weeks that img02–img19 were sitting in `assets/` waiting.)
- **Cover emblem** = `assets/img20.png` (940×485, ~67 KB): gold rifles + bone-white steer
  skull, transparent background **and** transparent rifle-lever holes so the cover ground
  shows through. It replaced an older inline-SVG emblem. Centered in the blank lower area of
  each cover via flexbox (`margin:auto` inside a flex-column title page), so each cover
  self-centers it in its own free space.
- **Cover subtitle** ("A Roleplaying Game of the Haunted Frontier") is styled to match the
  top kicker line: EB Garamond, small-caps, bold, upright, 24px.
- **The parchment paper texture is GONE.** Pages use a flat warm `--paper` color plus a
  subtle radial-vignette gradient — no tiled background image. The old texture, `img01.png`,
  is no longer referenced anywhere; it still sits in `assets/` but is unused and can be
  deleted.
- Because the Player's Book no longer inlines 18 plates, its self-contained HTML is now
  **~0.40 MB** (was ~5–10 MB). All three books are now small enough to be comfortable on a
  phone.

---

## Files — the book sources

Each book's cheapest editable form is **bolded**.

| File | Role |
|---|---|
| **`build_player.py`** | Player's Book — edit this. The whole book's HTML lives inside as the embedded raw string `SRC` (~350 KB; any images are `src="assets/…"` refs, not base64 — currently only the cover emblem). The build drops in the Perdition map, grows the detailed Contents, inlines referenced assets → the self-contained `blood-and-grit.html` (idempotent). `measure_index.py` patches the static Index numbers directly into `SRC`. Replaced `player-src.html` on 2026-07-18 (byte-identical conversion). |
| `assets/` | The images — **`img20.png`** (the cover emblem, transparent bg + transparent lever holes) and nothing else. The old parchment texture (`img01`) and the 18 Player plates (`img02–img19`) are **gone from the repo and were never committed to it**; don't plan on recovering them. |
| **`build_keeper.py`** | Keeper's Book — edit this (chapter prose lives inside as HTML strings). Reads `blood-and-grit.html` directly. Holds the Player-version **cascade tuples** and the `_chq` chapter-epigraph dict. |
| **`build_bestiary.py`** | Bestiary — edit this (section text + `sb(...)` / `creature(...)` calls). Reads `blood-and-grit.html` directly. Also holds the Player-version cascade tuples, **and** (since 2026-07-18, when `bestiary_extra.py` was merged in) the 25 ordinary-beast stat blocks + field-guide lore (`LIVING_LORE`), the per-section tier/name **sorter** (`sort_sections`), and the **appendix generator** (`gen_appendix`). To add a creature, edit this one file. |
| `pag_patch.py` | Shared paginator patch (imported by keeper + bestiary builds). Generalizes `splitContainer` so prose boxes, two-column blocks, stat blocks, **and creature entries** split across page boundaries to fill whitespace instead of moving whole. |
| **`nav_tools.py`** | Shared navigation generators, imported by all three builds. `add_detailed_toc(html)` grows the simple chapter `<ul class="toc">` into a flat, splittable two-level `<ul class="toc2">` (chapters + their `<h2>` sub-heads), auto-id-ing any headings that lack ids and re-using the `ix-*` anchors; section-opener `<h2>`s anchor to their section id (the paginator stamps the section id onto its first block). `build_index(html, curated, creatures=…)` appends a letter-grouped two-column `<ul class="ix">` in a new `id="bookindex"` section (Bestiary auto-lists all `<p class="cr-name">` creatures; both books add curated concept/place entries) and inserts its Contents line. |
| **`perdition_map.py`** | Draws the **Perdition Basin** map as inline SVG from one coordinate model. `player_map_html()` = the clean honest map (river, wells, three towns, mission, trails, mesas); `keeper_map_html()` = the same base + a secrets overlay (well states bound/failing/broken, the ring of nails, faction washes, the two starter-adventure pins). Run `python perdition_map.py both` to write `_map_preview.html`. Imported by `build_player.py` (fills the `<!--PERDITION_MAP-->` placeholder in Appendix E) and `build_keeper.py` (Ch. XIII). |
| `add_detail.py` | One-shot that already baked earlier additions into the builds. **Do not re-run.** |
| ~~`add_index.py`~~ | Dead one-shot (baked the v2.9 Index into `player-src.html`, a file retired 2026-07-18). Still on disk, **git-ignored since 2026-07-29**, do not re-run. |
| `measure_index.py` | **Player's Book verification tool** (Windows; needs `pip install playwright` + Edge): builds the Player's Book, renders it headless at desktop+mobile widths, asserts page parity / zero clipping / zero h-scroll / no unresolved TOC **and** index anchors, reports TOC drift, and re-patches the static Index page numbers from the rendered truth. Run after any Player's Book content change. (Clip check forces `zoom:1` on **each `.page`**, per the note below.) |
| **`measure_book.py`** | **General verification tool** — `python measure_book.py <built-file.html>`. Renders any built book headless, asserts desktop/mobile page parity, zero true-scale clipping (mobile forces `zoom:1` per `.page`; sub-10px desktop-flow clips are tolerated as sub-pixel rounding), zero mobile h-scroll, and that every `.toc2` and `.ix` anchor resolves live. Read-only (never patches). Use for the Keeper's Book and Bestiary. |
| `audit_whitespace.py` | **Whitespace audit** (2026-07-18) — `python audit_whitespace.py <built-file.html> [gap-px]`. Renders a book and lists every page whose bottom gap exceeds the threshold (default 140px), with the block that moved to the next page. Interpretation guide: gaps before a chapter/appendix start are deliberate page breaks; small gaps before a heading are orphan control; only mid-flow gaps are candidates for splitting work. |
| `extract_creatures.py` | **App data extractor** (2026-07-18) — `python extract_creatures.py bestiary.html GK/rules/Data/creatures.json`. Re-extracts the Keeper's Table app's creature data from the built Bestiary (balanced-div walk over `.creature` blocks, tags stripped, entities decoded). Run whenever Bestiary creature content changes; sanity-check with a diff against the previous JSON before shipping. |
| `make_pdf.py` | Prints all three to true 8.5×11 US-Letter PDFs. **Only run on explicit request.** |
| `README.md` | Short workflow notes. |

The per-book source files are interdependent (they need the shell + helper modules), so
**to actually build, keep the whole bundle together.**

---

## How to make a change (per book)

```bash
# Player's Book → edit the SRC string in build_player.py, then:
python build_player.py                  # → blood-and-grit.html (the shared shell — build first)

# Keeper's Book → edit build_keeper.py, then:
python build_keeper.py                  # reads blood-and-grit.html → keeper-handbook.html

# Bestiary → edit build_bestiary.py (creatures included), then:
python build_bestiary.py                # reads blood-and-grit.html → bestiary.html

# PDFs of all three — ONLY when I explicitly ask:
python make_pdf.py
```

After any content change: **re-measure and patch the contents page numbers** (adding/cutting
content shifts where chapters land), run the verification checks below, **bump the book's
version on the cover**, and **update this doc's version table + Changelog.**

### The version cascade (important, easy to miss)
`build_keeper.py` and `build_bestiary.py` splice each book's own cover onto the Player shell
by **string-replacing the Player's version strings** with their own. Those match strings are
hard-coded (currently "…Version 2.25…" / "…v2.25…", four per script). They are the Player's
version, never the splicing book's own — check them against `build_player.py` rather than
against this line, which has gone stale before.

**Any time you bump the Player's Book version, you must also update those match strings in
both build scripts** — e.g.:
```bash
sed -i 's/v2.13/v2.14/g; s/Version 2.13/Version 2.14/g' build_player.py build_keeper.py build_bestiary.py
```
— or the Keeper/Bestiary covers will silently keep the Player's version. Bumping only the
Keeper or only the Bestiary needs no cascade (their version strings are only on the *right*
side of the tuples; bump them directly in their own build script).

---

## "Save to PDF" — my standing preference

Only when I explicitly ask. Generate via headless Chromium print-to-PDF (Playwright
`page.pdf`) with `prefer_css_page_size=True`, `print_background=True`, margins 0. The books
already define `@page { size: Letter; margin: 0 }` and fixed 8.5×11in sheets, so one sheet =
one US-Letter PDF page. Before printing: wait for `.book.pages.ready` and fonts loaded, then
**force-decode every `<img>` (`img.decode()`)** so any images don't blank. Verify with
PyMuPDF: page count == sheet count, page size 612×792pt.

Output names (written beside the sources in the project folder):
`Blood-and-Grit-Players-Book.pdf` · `Blood-and-Grit-Keepers-Book.pdf` · `Blood-and-Grit-Bestiary.pdf`

*(`make_pdf.py` was rewritten for the Windows toolchain on 2026-07-12 — Playwright driving
system Edge, PyMuPDF verification built in: page count == rendered sheet count, 612×792 pt.
Regenerating overwrites the three PDFs in place.)*

---

## Verification standards (run on every change)

- **Page parity** — desktop and mobile must paginate to the same page count.
- **No clipping at true scale** — desktop clip 0; on mobile, force `zoom:1 !important` on
  every `.page` element (setting the `--book-zoom` CSS var does *not* work — effective zoom
  stays ~0.458) to confirm the true-scale clip is 0. The 1–10px "clips" seen at fractional
  zoom are just rounding.
- **No horizontal scroll on mobile** — check at *natural* zoom (should be 0). Note: a test
  that forces `zoom:1` will report ~426px h-scroll; that's an artifact of the forced scale,
  not real overflow. Confirm h-scroll at natural zoom.
- **Whitespace near the floor** (Bestiary now ~106px mean); remaining big gaps should only be
  intentional chapter/section openers.
- **Contents page numbers** re-measured against the rendered sheets and patched.
- **JS valid** — extract the `<script>` and run `node --check`.
- **Idempotent build** — rebuilding twice yields byte-identical output (`md5sum`).
- **No rules drift** — `python verify_rules.py` parses the built Player's Book and checks its
  seventeen Calling tables against `chargen.json` and the spine formula (697 cross-checks).
- **The prose reads as written** — `python audit_ai_tells.py --commits 40`. The books have had this
  standard from the start; as of 2026-07-29 the **repository's own docs** are held to it too, because
  the README and this file are what a reader meets first. Two signals: **burstiness** (sd/mean of
  sentence length; 0.55+ human-like, under 0.45 is the tell) and a scan for generated cadences,
  **negative parallelism** above all. Currently README 0.82 · CLAUDE.md 0.78 · CHANGELOG 0.80 ·
  commit messages 0.63, zero hard tells.
  Three things about that script are worth not re-learning: its markup stripping is
  **length-preserving**, because collapsing spans made every reported line number fiction and sent
  you to rewrite innocent prose; **quoted** spans are reported apart and never fail, since both real
  hits were the books' own rules text quoted back into a changelog and rewriting either would
  falsify the record; and the quote pattern takes **double quotes only**, because admitting the
  apostrophe makes "don't … it's" read as a quoted span and *masks* genuine tells — the one failure
  mode worse than a false positive. Proper nouns that collide with corporate vocabulary
  (`Vital Breath`, `landscape-Letter`) are blanked before the soft-word count.

### One source of truth, and disagreement is a failing test

The standing discipline behind the numbers: **each rule is encoded once, both the book and the
app are generated/checked from it, and any disagreement fails a build.** Concretely — the attack
spine (rank → level) and the save formulas live in Ch. XIV; `chargen.json` transcribes them and
carries each Calling's `attackRank`; `CharGen.Validate` re-derives every row from
`AttackFor`/`StrongSave`/`WeakSave` (so data↔app can't drift — the smoke suite fails first); and
`verify_rules.py` checks the *printed book* against the data and the formula (so book↔data can't
drift). The same shape governs armor (`ArmorFrom`, folded into `ReckonNumbers`), the Signs and
Miracles (`SignsFor`/`MiraclesFor` gated by the shared `RankAt`), the faith/sign pool
(`PoolMax` re-derived in `Validate`), and the Iron Code weapon traits (`WeaponTraits.Parse` reads
the book's own free-text `traits`, and a smoke test asserts the parse). When you add a rule that
appears in more than one place, wire it this way: one source, generated outward, checked back.

---

## The Player's Book (v2.25) — structure

Chapters: I. The Country · II. How the Game Is Played · III. Making a Character ·
IV. Origins & the Peoples of the Frontier · V. Worldly Callings · VI. Callings of Faith ·
VII. Callings of the Old Dark · VIII. Skills · IX. Edges · X. Goods & Provisions ·
XI. Conflict & the Iron Code · XII. Nerve & the Uncanny · XIII. Signs & Old Rites ·
XIV. Advancement. Appendices: A. Example of Play · B. Conditions · C. Quick Reference ·
**D. A Posse, Ready-Made** · **E. The Country — Perdition Basin** (new in v2.10: the in-world,
secrets-free gazette of the sample county + the clean player map, injected into the
`<!--PERDITION_MAP-->` placeholder by `build_player.py`) · then The Ledger · then **the Index**
(since v2.9: ~200 entries, two-column, letter-grouped; every entry's page number is resolved live
by the paginator like the TOC's, via anchor ids — `ix-*` on headings/list items/table rows across
the whole book). The **detailed two-level Contents** (v2.10) is generated by `nav_tools.py`.

**Ch. IV's "Peoples of the Frontier" sections.** After the ten Origins the chapter carries a
run of long-form sections on the real peoples of the West, each in the same shape — two
history paragraphs, a boxed *Playing a … Character* with five rules of the road, then a
"mechanically, any Origin and Calling" closer. **The First Peoples** and **The Mexican
Frontier** date from earlier versions; **Black Westerners** and **The Chinese on the
Frontier** were added in v2.16 to complete the set (they were the two the chapter's own
subtitle promised and did not deliver). Keep the shape if any more are added, and keep the
design line the whole set observes: these peoples appear as people and professionals, never
as new monsters, and the game's invented dark is never pinned to a living religion.

### Appendix D — "A Posse, Ready-Made" (six pregens)
Six finished 1st-level characters, math-verified against the chargen rules (Honest Array
15/14/13/12/10/8 + Origin gifts), each with the Four Questions pre-answered:
- **Ruth "Six-Finger" Calloway** — Gunhand · the Outlaw
- **Doc Aurelia Mercer** — Sawbones · the Fallen Gentry
- **Brother Elias Crow** — Preacher · the Freed
- **Anni Halvorsen** — Mountain Man · the Scout
- **Addison Quill** — Bounty Hunter · the Veteran
- **Opal Vance** — **Hexer** · the Homesteader (begins at Mark 1 — fits the Hexer, who is
  always already touched; knows Signs *Borrowed Breath* and *Salt & Iron*; companion crow
  "Deuteronomy")

Chapter epigraphs exist on every chapter; the four added most recently are III (Making a
Character), IX (Edges), A (Example of Play), and B (Conditions).

### Plates
**Removed** (18 of them) for design continuity with the other two books. If restoring later:
the artwork would have to be generated fresh — it is not in `assets/` and never
was. **Placement bug to avoid if you re-add
any:** inserting a `<figure>` *before* a `<section class="page" id=X>` opener drops it
between sections where the paginator silently discards it — figures must go *inside* a
section (before the preceding `</section>`, or before an inner `<h2>`). Always re-count
rendered `figure.plate img` after moving/adding plates.

---

## The Keeper's Book (v2.12) — structure

Chapters I–XIV plus the Keeper's Screen appendix and a back-of-book Index:
I. The Keeper's Chair · II. Running the Game · III. Fear, Nerve & the Mark ·
IV. The Long Odds (Building the Fight) · V. A Bestiary of the Frontier ·
VI. Cursed Ground, Hazards & Bad Medicine · VII. Rewards & Reckonings · VIII. The Cast ·
IX. A First Reckoning (starter adventure) · X. A Second Reckoning (starter adventure) ·
**XI. The Keeper's Year** (running a campaign — three campaign frames, the rhythm of a year,
three ready campaign seeds) · **XII. The Country in Your Pocket** (rollable tables: towns,
NPCs, rumors, trail events, plunder, omens) · **XIII. Perdition Basin** (new in v2.2 — the
fully-keyed sample county + the secrets-annotated Keeper map; realizes the Ch. XI "Salt Valley"
Haunted-County seed and is the home ground of both starter adventures) · **XIV. The Lamplit City**
(new in v2.8 — running the game in Dodge, Kansas City, San Francisco, Butte and the rest: why the
dark prefers a crowd, the six things that change at the table, how each Bestiary chapter bends to
a city, the Dark-Cultist-as-chartered-benevolent-society, ten real cities keyed, and a
build-your-own-city checklist plus three d10/d12 tables) · Appendix: The Keeper's
Screen · **Index** (new in v2.2; `id="bookindex"`, distinct from the Bestiary-style `id="index"`).
The **detailed two-level Contents** is generated by `nav_tools.py`.

**Ch. XIII Perdition Basin** is `CH13` in `build_keeper.py` (spliced into `BODY` before the Screen
appendix), embeds `keeper_map_html()`, and carries anchor ids (`basin`, `basin-truth`,
`basin-wells`, `basin-crossing`, `basin-coffin`, `basin-saltlick`, `basin-mission`, `basin-mesa`,
`basin-homesteads`, `basin-hands`, `basin-running`) the Keeper index links to. Its spine — the
padres' silver "nails" binding a Patron under the wells, now failing well by well — is deliberately
the same as the Ch. XI Salt Valley seed.

**Chapter epigraphs** are injected by the `_chq` dict at the bottom of `build_keeper.py`
(via `_inject_quote`, which drops a `quote()` after each chapter's `<div class="divider">`).
Every chapter + the Screen appendix now carries one. (Ch. V already has an inline quote, so
it's deliberately *not* in the dict — don't add it there or it'll double.)

---

## The Bestiary (v2.11) — structure & conventions

New in v2.2: a **generated two-level detailed Contents** and a back-of-book **Index**
(`id="bookindex"`) that auto-lists all **150 creatures** by name (from every `<p class="cr-name">`,
so it can never drift) plus ~19 curated chapter/concept entries. Note the long-standing
Roll-by-Tier appendix keeps `id="index"` — the alphabetical index is a separate `id="bookindex"`.


Eight creature chapters (150 creatures, each with lore + Found line + stat block + run-it
guidance) plus three appendices. **Ch. VIII (Beasts of the Living World, 45) and Ch. IX
(Hard Men & Hard Country, 20) are the mundane half — 65 of the 150 — and cost no Nerve and
never move the Mark; they exist so a Keeper can run a slow burn before anything gets up that
shouldn't.** Ch. IX (new in v2.8) is ordinary men (rustlers, a lynch mob, a hired gun, the
Regulators) and hard country (bad water, a norther, a river crossing, a blizzard):
I. How to Read the Dead · II. The Restless Dead (15) · III. Cursed Beasts & Wild Things (17) ·
IV. Men, and the Shapes of Men (16) · V. Spirits & Hauntings (12) · VI. The Wild & the
Weather (10) · VII. The Old Dark (15) · VIII. Beasts of the Living World (25) ·
Appendix: **The Roll, by Tier** · Appendix: **The Grounds** (encounters by terrain — nine
rollable tables + a villain picker, with the "safe-table rule") · Appendix: **Building Your
Own Dead** (the from-scratch workshop + the Threat-by-Tier table).

### Conventions (keep these)
- **Creature entries flow continuously and pack tightly** (as of Bestiary v2.0). The paginator splits
  a `<div class="creature">` across a page boundary when it would otherwise strand
  whitespace, using the creature's name line as a repeating head so a continuation reads
  "The Wendigo (cont.)". Stat blocks are never broken across a page edge, and the built-in
  `notAlone` guard moves a creature whole rather than orphan its heading. Result: no
  one-creature-per-page waste; mean trailing whitespace ~106px.
- Every creature section is **sorted by tier ascending, then name ascending** (leading
  "The/A/An" ignored; a creature's tier = the first roman numeral in its header; range
  creatures sort at their lower tier). Done at build time by `sort_sections()`.
- **`sort_sections()` asserts on any non-creature content *between* creatures** — so a stray
  quote or note inserted mid-section will break the build. Content is only safe in a
  section's prefix (before the first creature), its suffix (after the last), or *inside* a
  creature block.
- The **"The Roll, by Tier" appendix is generated** from the actual stat blocks by
  `gen_appendix()` — so it can't drift. All 150 are always indexed; the dual flock/prophet
  entry is listed in both its tiers. (The Grounds and Building-Your-Own-Dead appendices sit
  *outside* the sorter/generator scope, so they're safe to hand-author.)
- **Ordinary beasts** (Section VIII) cost **no Nerve and never move the Mark** — Dread line
  reads "—", no "How to Play It" note; their field-guide lore + Found line come from
  `LIVING_LORE` in `bestiary_extra.py`. Keep that rule for any new natural animals.
- **Two per-creature wrappers:** `sb(...)` builds a bare stat block; `creature(...)` wraps
  lore + optional witness quote + Found + `sb(...)` + optional keeper note into one sortable
  `<div class="creature">` unit. `creature()` signature:
  `creature(stat_html, lore, found, keeper, kn_tag="How to Play It", witness=None)` — pass
  `witness=(text, source)` to seed an in-voice witness quote between the lore and the Found
  line (used on the Risen, Nightwalker, Skin-Walker, Thunderbird, Wendigo). Because the quote
  lives inside the creature div, it travels with the creature through sorting.

---

## System reference (for writing stat blocks)

- **Abilities:** STR / DEX / CON / WIT (Wits) / RES (Resolve) / PRE (Presence);
  mod = (score − 10) / 2.
- **Saves:** Fort (CON) / Ref (DEX) / Will (RES). **Blood** = HP. **Defense** = AC.
- **Four degrees:** crit success (beat DC by 10 / nat 20) · success · failure · crit failure
  (miss by 10 / nat 1).
- **Grit** = hero points (3/session). **Nerve** = RES + level; lost on Dread Checks (Will
  save vs the Dread DC). **The Mark** = a 6-step corruption track. **Taint** = cursed-ground
  clock.

`sb()` signature (in `build_bestiary.py`):
```
sb(name, tier, Defense, Blood, Speed, Fort, Ref, Will, Attacks, Special, Dread, PuttingItDown, mark=None)
```

**Threat-by-Tier benchmarks** (a creature's Tier is a fair, hard fight for a party of **twice
its Tier in levels**):

| Tier | Defense | Attack | Blood | Saves (high / low) | Damage | Dread DC |
|---|---|---|---|---|---|---|
| I | 13 | +4 | 12 | +6 / +2 | 1d6+2 | 10–13 |
| II | 15 | +6 | 22 | +8 / +3 | 1d8+3 | 13 |
| III | 17 | +9 | 40 | +11 / +5 | 2d6+4 | 16 |
| IV | 20 | +13 | 70 | +15 / +8 | 2d8+6 | 20 |
| V | 23 | +17 | 110 | +19 / +11 | 3d8+8 | 25 |

**Encounter budget:** 4 points/PC; an even foe = 4, a mook = 1, a standout = 8.

---

## GritKeeper (v1.29.2) — the C# desktop app

A standalone Keeper-facing utility for running games at the table, built in **C#/.NET 8, Windows
Forms**. Not part of the HTML book pipeline — separate source tree, separate build. The working
tree is **`GK/`** (three projects since v1.28.0: `GK/rules` the headless library, `GK/source` the
WinForms app, `GK/smoke` the logic tests); **`GritKeeper/` is the generated deliverable, never
source.** A Linux package is **planned**, with no date — the engine half already runs there.

**The app's own detail lives in [`GK/CLAUDE.md`](GK/CLAUDE.md)** — source-tree layout and which
tree a change belongs in, the ten tabs, the file table, build & run, the verification standard,
and the drawn-text landmine. That file loads automatically whenever work touches anything under
`GK/`, which is exactly when any of it applies. It was split out on 2026-07-30: ~35,000 characters
of app detail were loading into every session, including the ones that never opened a `.cs` file.

Two things stay here, because both can ruin a release before you ever open the app's source:

- **NEVER pass `-o` to `dotnet publish`.** The publish settings are baked into the csproj, and
  `sign.ps1` / `package.ps1` both default to the RID-qualified path
  `bin/Release/net8.0-windows/win-x64/publish/`. `-o` diverts the build elsewhere and they will
  happily sign and ship the **previous version's exe**. This happened during the v1.18.0 release
  and was caught only on the version check.
- **Never give a `SplitContainer` geometry at construction time.** Setting `SplitterDistance` or
  either `PanelNMinSize` before the control is docked and laid out throws on a real Windows render
  — it compiles clean and passes headless tests, so it reaches the user. Always build splitters
  through the `Split(orientation, p1Min, p2Min, ratio)` helper in `MainForm.cs`, which defers
  geometry to a one-shot `SizeChanged`.

And the standing sync rule: **the app is synced in the same session as any book change that
touches it** — status-bar and `GK/source/README.md` version strings every time the books bump,
`Data/creatures.json` re-extracted (`extract_creatures.py`, diffed against the previous JSON)
whenever Bestiary creature content changes, and the Reference tab whenever a rule it quotes
changes. Then build, smoke, publish, re-mirror `GritKeeper/`, and rezip.


## Roadmap / open threads (not yet built)

- ~~**A named sample territory with an SVG map**~~ — **DONE (v2.10/v2.2):** Perdition Basin, a
  one-county worked example with a two-layer in-engine SVG map (clean player map in the Player's
  Book Appendix E; secrets-annotated Keeper map + full gazetteer in the Keeper's Book Ch. XIII).
  See `perdition_map.py`. Could still grow into a thin fourth book if you want more territory.
- **Discord / online play** — proposed but not built. The full write-up is **`DESIGN-online-play.md`**, which lives on the working machine only (git-ignored since 2026-07-29); its substance is here.
  Four rungs, cheapest first: a webhook output sink → a slash-command bot rolling the real rules
  (ephemeral replies fit the Mark and Nerve tracks unusually well) → shared live state, either a
  LAN-hosted responsive page served by the app itself or Discord-as-state-surface → a full VTT
  (recommended against; the Trail Maps SVG already drops into Owlbear/Foundry/Roll20 today). The
  The enabling refactor is **DONE (v1.28.0)**: `GK/rules/BloodAndGrit.Rules.csproj` is a real
  `net8.0` class library, so the drift risk is gone and there is a Linux-runnable engine to build
  a bot or a server against. Every remaining rung is still unbuilt and undecided.
  Two gotchas recorded there: `Rules.Rng` is a process-wide static that `Reseed` swaps wholesale
  (fine for one table, a hazard for two), and webhook URLs / bot tokens are bearer credentials
  that belong in `prefs.json`, never `session.json`.
- A one-sheet **"teach it in ten minutes"** player handout.
- **Higher-level play support** — the Advancement chapter is thin past level 5.
- **The Keeper's Table** got its first full visual pass on 2026-07-09 (Claude Code CLI
  running natively on the user's Windows laptop, all 8 tabs screenshotted) — found and fixed
  an ampersand-mnemonic label bug (see Changelog), nothing else wrong. Still worth another
  look sometime at DPI scaling on a non-100%-scale display, since this pass was at whatever
  the laptop's default scale was.
- **Illustrations** are currently removed from all three interiors by choice. If reintroduced
  later, generate plates with an external AI tool using a fixed style-reference for
  consistency, recompress to ~1200px / q80 before inlining, and consider re-enabling the
  (currently stubbed) `plate()` function in the Keeper/Bestiary builds so those two can carry
  plates too. Any reintroduction should be applied consistently across all three for the
  cross-book continuity we established.

---

## Shared tracking conventions (all Desktop\Git repos — keep identical)

Every repo under `C:\Users\Cole\Desktop\Git\` is tracked the same way; when one changes,
change them all:

- Branch `main`. Every edit happens on a session branch (`session/<yyyy-mm-dd>-<topic>`),
  merged into `main` with `--no-ff` when verified, then the branch is deleted. Never rewrite
  history on `main`.
- **`CHANGELOG.md`** (separate file, newest first) is the version record. Any commit that
  changes content or behavior adds an entry — and bumps the affected component's version — in
  the same commit. References to "the Changelog" elsewhere in this doc mean `CHANGELOG.md`.
- Version bumps are **tagged** `component-vX.Y[.Z]` at the commit that ships them.
- **`README.md` stays current by itself.** Its prose is version-agnostic and its links point at
  `blob/main/*.pdf` and `/releases/latest`; the one drifting part — the *current editions* line
  and *latest change* note — lives in an `AUTO:editions` block regenerated by **`update_readme.py`**
  from the build-script version strings and `CHANGELOG.md`. The tracked **`.githooks/pre-commit`**
  hook runs it and re-stages `README.md` on every commit (never blocks a commit). Enable once per
  clone: `git config core.hooksPath .githooks`. Don't hand-edit inside the AUTO markers.
- `autosync.ps1` + `register_autosync_task.ps1` are canonical and identical in every repo.
  The "<folder name> AutoSync" scheduled task (every 30 min + at logon) auto-commits the
  checked-out branch and pushes only when an `origin` remote exists. `autosync.log` is
  git-ignored. **Since 2026-07-29 the pair — and `.claude/` — are git-IGNORED in all three
  repos** (BloodAndGrit, TideWatch, DebForge). They are still on disk, still byte-identical,
  and still run; they are simply not published, because they describe this laptop rather than
  any of the software. "Identical in every repo" therefore holds of the files AND of what is
  tracked. Verify with `Get-FileHash` across the three before editing either one.
- **Untrack on `main`, never on a session branch.** See the landmine below: `git rm --cached` on a
  branch reads as harmless and turns into a real working-tree delete at merge time. TideWatch and
  DebForge were done directly on `main` for exactly this reason.

### What GitHub carries (BloodAndGrit — standing rule, 2026-07-29)

**Only the three books, GritKeeper, and the files that build or check them** — *"on GitHub, only
the files necessary to support the three game books and GritKeeper should remain."* Applied
2026-07-29 by `git rm --cached` + `.gitignore`, so every file stayed on disk and every one is
recoverable from history.

| Group | Verdict | Why |
|---|---|---|
| The 3 PDFs + 3 built HTML + `build_*.py` + `nav_tools`/`perdition_map`/`pag_patch`/`make_pdf`/`extract_creatures`/`update_readme` + `assets/` | **keep** | The deliverables and the pipeline that makes them. |
| `GK/rules`, `GK/source`, `GK/smoke`, `sign.ps1`, `package.ps1`, `GritKeeper/README.md` | **keep** | The app and how it is built, signed and packaged. |
| `measure_index.py`, `measure_book.py`, `verify_rules.py`, `audit_whitespace.py`, `audit_ui.py` | **keep** | These are how the deliverables are *supported*: you need them to CHANGE a book or the app safely, even if not to read one. `verify_rules.py` is the guard that stops the printed book and the app's data drifting — the discipline the whole project is built on. Cutting them would leave the repo's own quality claims uncheckable. |
| `CLAUDE.md`, `CHANGELOG.md`, `README.md`, `.gitignore`, `.githooks/pre-commit` | **keep** | CLAUDE.md is what makes the books buildable by anyone who clones — the version cascade, the SplitContainer landmine and the re-mirror rule are written down nowhere else. |
| `DESIGN-online-play.md`, `editorial-denials.md` | **untracked** | Process, not product: an unbuilt proposal and a log of declined edits. The proposal's substance is summarized in the roadmap below, so nothing is lost. |
| `autosync.ps1`, `register_autosync_task.ps1`, `.claude/` | **untracked** | This laptop's setup — a backup task and a session command. They build nothing. |
| `add_index.py` | **untracked** | Dead: a one-shot against `player-src.html`, a file retired 2026-07-18, marked "do not re-run" since. |

The repo is **PUBLIC and stays public** — that is deliberate; don't offer to change it.

**Landmine, hit on 2026-07-29: `git rm --cached` on a session branch DELETES THE FILE when that
branch is merged.** `--cached` only touches the index, so on the branch the working file survives
and everything looks right. But what the commit records is *the path being removed from the tree* —
and merging that into `main`, where the file is still tracked, makes git perform a real
working-tree deletion. All six files above vanished off the disk at the `--no-ff` merge, including
`autosync.ps1` (breaking the scheduled backup) and `.claude/commands/session-start.md`.

Recovery, and the right way to do it byte-exactly — `Set-Content` on a piped `git cat-file` is NOT
byte-exact, because PowerShell's string pipeline rewrites the line endings:
```powershell
git checkout <pre-merge-sha> -- <paths>     # restores the working file exactly (and stages it)
git reset -q HEAD -- <paths>                # unstage, so HEAD keeps "deleted" and the file stays
```
Then confirm with `git hash-object <path>` against `git rev-parse <sha>:<path>` — equal hashes or it
isn't restored. **Next time: untrack on `main` directly, or re-verify every untracked path is still
on disk AFTER the merge, not just after the `rm --cached`.**
- **HRHS Scripts is local-only by design** — no remote, never push it to GitHub. Every other
  repo syncs to `github.com/cwgilgalad`.

## Changelog

Moved to [CHANGELOG.md](CHANGELOG.md) on 2026-07-18, when tracking was standardized across
all `Desktop\Git` repos.
