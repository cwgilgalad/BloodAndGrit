# Changelog — Blood & Grit

All notable changes to the three books and The Keeper's Table app, newest first. Any commit
that changes content or behavior adds an entry here — and bumps the affected component's
version — in the same commit. Version bumps are tagged `component-vX.Y` at the commit that
ships them. (Moved out of CLAUDE.md on 2026-07-18 when tracking was standardized across all
Desktop\Git repos.)

---

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
