# Blood & Grit — Project Handoff & Preferences

Import this file into the project so a fresh chat can pick up exactly where we left off.
For onboarding a fresh Project, hand over **the current loose files from the repo** — the
builders (`build_player.py` / `build_keeper.py` / `build_bestiary.py`), the shared modules
(`nav_tools.py`, `perdition_map.py`, `pag_patch.py`), `assets/`, and whatever else the task
touches — not a packaged snapshot. (Packaged snapshots go stale silently: the old
`blood-and-grit-sources.zip`, deleted 2026-07-23, sat at its day-one 2026-07-11 contents
while the build architecture moved on underneath it.)

**Current versions: Player's Book v2.21 · Keeper's Book v2.9 · Bestiary v2.8 ·
GritKeeper app v1.15.0 (renamed from "The Keeper's Table" in v1.5.0; self-contained,
crash-hardened, Authenticode-signed, exe `GritKeeper.exe`).**

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
```
(`/XD bin obj publish` keeps the .NET build output out of the deliverable; robocopy exit
codes 0–7 are success.) Then drop the published `GritKeeper.exe` into `GritKeeper\app\` and
re-zip to `GritKeeper.zip`. If this ever gets scripted — alongside `sign.ps1`, or as a new
`package.ps1` — fold the copy step in there so it can't be skipped.

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
| The Player's Book | v2.21 | 200 | one inline SVG map (Appendix E) + cover emblem |
| The Keeper's Book (GM guide) | v2.9 | 101 | one inline SVG map (Ch. XIII) + cover emblem |
| The Bestiary | v2.8 | 164 | none (150 creatures) |

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
  The plate *images* still sit unused in `assets/` (img02–img19), so plates can be restored
  later; nothing was destroyed.
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
| `assets/` | The images. **`img20.png`** is the cover emblem (transparent bg + transparent lever holes) — the only asset currently used. `img01.png` (old parchment texture) and `img02–img19` (old Player plates) are present but **unused**; keep them only if you might restore plates. |
| **`build_keeper.py`** | Keeper's Book — edit this (chapter prose lives inside as HTML strings). Reads `blood-and-grit.html` directly. Holds the Player-version **cascade tuples** and the `_chq` chapter-epigraph dict. |
| **`build_bestiary.py`** | Bestiary — edit this (section text + `sb(...)` / `creature(...)` calls). Reads `blood-and-grit.html` directly. Also holds the Player-version cascade tuples, **and** (since 2026-07-18, when `bestiary_extra.py` was merged in) the 25 ordinary-beast stat blocks + field-guide lore (`LIVING_LORE`), the per-section tier/name **sorter** (`sort_sections`), and the **appendix generator** (`gen_appendix`). To add a creature, edit this one file. |
| `pag_patch.py` | Shared paginator patch (imported by keeper + bestiary builds). Generalizes `splitContainer` so prose boxes, two-column blocks, stat blocks, **and creature entries** split across page boundaries to fill whitespace instead of moving whole. |
| **`nav_tools.py`** | Shared navigation generators, imported by all three builds. `add_detailed_toc(html)` grows the simple chapter `<ul class="toc">` into a flat, splittable two-level `<ul class="toc2">` (chapters + their `<h2>` sub-heads), auto-id-ing any headings that lack ids and re-using the `ix-*` anchors; section-opener `<h2>`s anchor to their section id (the paginator stamps the section id onto its first block). `build_index(html, curated, creatures=…)` appends a letter-grouped two-column `<ul class="ix">` in a new `id="bookindex"` section (Bestiary auto-lists all `<p class="cr-name">` creatures; both books add curated concept/place entries) and inserts its Contents line. |
| **`perdition_map.py`** | Draws the **Perdition Basin** map as inline SVG from one coordinate model. `player_map_html()` = the clean honest map (river, wells, three towns, mission, trails, mesas); `keeper_map_html()` = the same base + a secrets overlay (well states bound/failing/broken, the ring of nails, faction washes, the two starter-adventure pins). Run `python perdition_map.py both` to write `_map_preview.html`. Imported by `build_player.py` (fills the `<!--PERDITION_MAP-->` placeholder in Appendix E) and `build_keeper.py` (Ch. XIII). |
| `add_detail.py` | One-shot that already baked earlier additions into the builds. **Do not re-run.** |
| `add_index.py` | One-shot that baked the v2.9 Index into `player-src.html` (anchor ids, index section, TOC line, `.ix` CSS, version cascade). Guarded against re-running, but **do not re-run** anyway. |
| `measure_index.py` | **Player's Book verification tool** (Windows; needs `pip install playwright` + Edge): builds the Player's Book, renders it headless at desktop+mobile widths, asserts page parity / zero clipping / zero h-scroll / no unresolved TOC **and** index anchors, reports TOC drift, and re-patches the static Index page numbers from the rendered truth. Run after any Player's Book content change. (Clip check forces `zoom:1` on **each `.page`**, per the note below.) |
| **`measure_book.py`** | **General verification tool** — `python measure_book.py <built-file.html>`. Renders any built book headless, asserts desktop/mobile page parity, zero true-scale clipping (mobile forces `zoom:1` per `.page`; sub-10px desktop-flow clips are tolerated as sub-pixel rounding), zero mobile h-scroll, and that every `.toc2` and `.ix` anchor resolves live. Read-only (never patches). Use for the Keeper's Book and Bestiary. |
| `audit_whitespace.py` | **Whitespace audit** (2026-07-18) — `python audit_whitespace.py <built-file.html> [gap-px]`. Renders a book and lists every page whose bottom gap exceeds the threshold (default 140px), with the block that moved to the next page. Interpretation guide: gaps before a chapter/appendix start are deliberate page breaks; small gaps before a heading are orphan control; only mid-flow gaps are candidates for splitting work. |
| `extract_creatures.py` | **App data extractor** (2026-07-18) — `python extract_creatures.py bestiary.html GK/source/Data/creatures.json`. Re-extracts the Keeper's Table app's creature data from the built Bestiary (balanced-div walk over `.creature` blocks, tags stripped, entities decoded). Run whenever Bestiary creature content changes; sanity-check with a diff against the previous JSON before shipping. |
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
hard-coded (currently "…Version 2.13…" / "…v2.13…", four per script).

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

---

## The Player's Book (v2.21) — structure

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
the artwork is still in `assets/` (img02–img19). **Placement bug to avoid if you re-add
any:** inserting a `<figure>` *before* a `<section class="page" id=X>` opener drops it
between sections where the paginator silently discards it — figures must go *inside* a
section (before the preceding `</section>`, or before an inner `<h2>`). Always re-count
rendered `figure.plate img` after moving/adding plates.

---

## The Keeper's Book (v2.9) — structure

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

## The Bestiary (v2.8) — structure & conventions

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

## GritKeeper (v1.11.0) — the C# desktop app

A standalone Keeper-facing utility for running games at the table, built in **C#/.NET 8,
Windows Forms**. Not part of the HTML book pipeline — separate source tree, separate build.
**Renamed from "The Keeper's Table" to GritKeeper in v1.5.0** — exe `GritKeeper.exe`,
product/title/About/README all updated; the **internal namespace stays
`BloodAndGritKeeper`** (deliberately — embedded-resource names derive from it). As of
2026-07-19 (v1.6.0) the folders match the name too: working tree **`GK/`** (was `KT/`),
delivered folder **`GritKeeper/`**, zip **`GritKeeper.zip`** (were
`BloodAndGrit-Keepers-Table`). The last "Keeper's Table" strings inside the app (session
file-dialog filters, crash-report captions) were also renamed in v1.6.0.

### Source-tree layout (IMPORTANT — read before editing the app)
There are **two** app directories under `BloodAndGrit/`. The working/master tree is **`GK/`**:
`GK/source/` (the `.cs`, `.csproj`, `Data/`), `GK/smoke/` (the headless logic-test project),
and `GK/source/publish/` (the self-contained build output). **Edit `GK/source`, build/test in
`GK/`.**

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

### Universal Undo/Redo (v1.6)
Snapshot-based, over the same `GameSession` shape File → Save/Load already uses:
`party`/`tracker`/`encounter`/`clocks` (the four `BindingList`s) each push a JSON
snapshot onto an undo stack on any `ListChanged` (add/remove/edit), capped at 50 deep;
`Undo`/`Redo` restore via `ApplySession`, which now suppresses re-capture during its own
bulk rebuild so a restore is one step, not N. Reachable from **Edit ▸ Undo/Redo**
(Ctrl+Z/Ctrl+Y) or matching buttons pinned in the status bar, so it's live no matter
which tab is open. Session notes deliberately aren't captured — the textbox's own native
undo covers it, since snapshotting every keystroke would flood the stack.

### What it does — ten tabs
- **Posse** — full party sheet (Blood, Defense, saves, Nerve, Grit, Mark 0–6, Taint 0–4),
  inline damage/heal spinners, Spend Grit, Mark/Taint advance, per-soul or whole-posse Dread
  Checks with the real Nerve-loss ladder, New Session reset, **Rest ▾ (long rest — restore
  Blood & Nerve to full, whole posse or selected soul)**, send-to-Tracker. v1.5: **▲ ▼
  reorder**, **double-click a soul (or the far-right Ledger button) → their Ledger window**,
  **double-click the Notes cell → full-note editor dialog**. v1.9: a **Gender** column
  (persisted; shown on every Ledger row, member or sheet). v1.10: **✦ Level up** — advance
  a New Soul–built soul one level through a dialog that offers only what the new level
  unlocks (Blood roll, 5th/10th boost, odd-level Edge + Gunhand combat Edge, 3/5/7/9 skill
  increase, 3rd-level subpath, new Signs), each drawn from the generator's eligibility
  helpers; the same button rides on each Ledger window. Backed by `CharGen.LevelUp`, which
  clones the sheet and appends exactly the new level's growth (lower levels byte-stable,
  result `Validate`-clean) — see the New Soul entry.
- **Dice** — expression roller (`2d6+3`, `1d8+1d6+2`) with a (v1.4) **builder keypad**:
  `+d4`…`+d100` stack dice (same die clicked again bumps the count; the v1.5 **× spinner**
  adds several at once — `Rules.ExprAddDie` takes a count), ＋/−/digits build the
  modifier, ⌫/C edit — pure logic in `Rules.ExprAddDie`/`ExprAppend` (smoke-tested). Plus
  quick dice, a d20 four-degrees checker, shared roll/event log, and (v1.2) a **dice
  tray** above the log: every roll's dice tumble (owner-drawn, 40 ms timer, ~half a
  second) and settle on the true per-die results from `Rules.RollExprFull`; shows up to
  8 dice, "+N more" beyond that. v1.5: **every die wears its color** (user-specified:
  d4 green · d6 blue · d8 orange · d10 white · d12 yellow · d20 red · d100 purple) on
  buttons (`DieBtn`) and tray faces — best face rings gold, a 1 rings near-black. v1.6:
  the roll log itself is **color-coded** (owner-drawn `ListBox`, `StyleRollLog`) — a
  four-degrees result is graded by its degree word (crit success gold bold, crit failure
  near-black bold, success verdigris, failure rust), a bare quick-die line by whether it
  landed on its max/min face, any other roll (`ROLL <expr>`) gets a neutral steel-blue
  tag, and plain event lines (posse/tracker/session) stay the default ink.
- **Bestiary** — all **150 creatures**, machine-extracted from the rendered Bestiary HTML
  (so lore/stats/witness quotes/keeper notes are word-for-word faithful to the book).
  Search, tier/chapter filters, one click to Encounter or Tracker. **Double-click a creature
  (v1.2) to pop it out into its own resizable/maximizable window** with A−/A＋ text zoom
  (`RichTextBox.ZoomFactor`) and its own → Tracker button — one window per creature, reused
  if already open, cascading placement, so several horrors can sit side by side.
- **Encounter** — the book's actual budget math (4 pts/PC; Even 4 / Mook 1 / Standout 8)
  costed live against party level, verdict bar, safe-table rule flagged. v1.2: an
  **"Add a creature" type-ahead picker (× N) right on the tab** (you no longer have to know
  to come from the Bestiary), the budget line says souls are counted from the Posse tab, and
  an **empty-state hint explains what the tab is for** (it reads as the book's "Long Odds").
- **Tracker** — initiative, rounds, damage/heal (two-way synced with the Posse sheet),
  conditions, double-click combat cards. **Flexible Sort ▾ (initiative / name / Blood, each
  asc or desc), ＋ Add (ad-hoc combatant or NPC by hand), ＋ Condition ▾ (tag the selected
  combatant from Appendix B's list), New fight (clear foes, keep the posse, back to Round 1),
  and Clear field (full wipe).** Foes arrive three ways: the Bestiary `× N` → Tracker, the
  v1.2 **Foe type-ahead box (× N) directly on the Tracker bar**, or ＋ Add by hand.
- **Map** *(v1.5 — "Trail Maps")* — seeded procedural frontier surveys: ground (the nine
  Grounds) × scale (gunfight → weeks of trail) × hour × water, with trail/rail/settlement/
  grid/Keeper's-secrets toggles. Deterministic per seed (note the map's N° to get it
  back), Ctrl+G for a fresh one. Exports: SVG (file/clipboard) and one-page
  landscape-Letter **PDF** — the GDI preview, the SVG, and the PDF all replay the same
  primitive list (`MapGen.Generate` → `Prim[]`), so they always match. v1.6: **zoom &
  pan** (mouse wheel zooms at the cursor 1×–8×, drag empty ground to pan, 🔍＋/🔍−/Fit
  buttons; view state only, never exported) and **tactical markers** — ＋ Marker ▾ drops
  a posse soul (green), NPC (gold), or creature (red) at the view center, **Tracker →
  Map** columns the whole tracker onto the field (posse west, foes east; skips labels
  already standing), markers **drag** into position (one undo step per drag), right-click
  renames/removes, Clear markers confirms. Markers live in map-model coords in
  `session.json` (`GameSession.MapMarkers`, `MapMarker` in Core.cs) and survive reseeds —
  they're session state, deliberately not part of the deterministic map. v1.7: **✥
  Landmarks** toggle — the survey's named landmarks become draggable (dashed gold grab
  rings; symbol + label move as one via `MapGen.MoveLandmark`, pure + smoke-proved;
  right-click puts one or all back, "all" confirmed). Placements keyed to the map
  number in `lmEdits`, re-applied on same-seed regens, cleared on a new seed; exports
  carry them. Also v1.7: rivers/creeks/trails/rails are **clipped to the inner
  neatline at generation** (`ClipPolyline`, Liang–Barsky) — they're deliberately
  generated overshooting the edges, and the SVG viewBox used to hide what the GDI
  preview and PDF showed. v1.8: **per-feature random streams** (`R(salt)` in
  `Generate`) — one shared stream used to make any overlay toggle reshuffle the whole
  map (user-reported); now every checkbox is pure ink-on/ink-off, the settlement
  claims its ground even unshown, and exports are exactly what's displayed. **Fords
  snap to the river** (mid-polyline vertex) or lake shore. **Secrets are movable** like
  landmarks (`MapModel.Secrets`, `MoveSecret`, keyed by index — lines can repeat; red
  rings under ✥ when the Keeper's layer is shown). The bar is three rows by intent:
  survey / Show+Zoom / table+Export.
- **New Soul** *(v1.3; overhauled v1.5)* — a strictly-by-the-book character maker: Ch. III's
  eight steps end to end at any level 1–10, both ability methods (Honest Array /
  4d6-drop-lowest), all 17 Callings and 10 Origins with their cross-constraints honored
  (no Gambler origin for Faith, no Hedge Magic for Faith or for sign-working Callings,
  Marks where imposed, Gunhand's bonus combat Edges, 3rd-level Trades/Schools/Oaths/
  Bargains/Devotions, Signs for the Old Dark and Miracles for the five Callings of Faith —
  each ranked and list-gated, and never both on one soul — coin rolled on the Ch. X dice and
  spent at printed prices). Rules data lives in **`Data/chargen.json`** — transcribed
  from the Player's Book (regenerate/update it when Ch. III–IV, VI, VIII–X, XIII–XIV
  change). `CharGen.Generate` builds, `CharGen.Validate` independently re-derives every
  number and returns violations (shown in-app if ever non-empty); the smoke suite
  generates and validates hundreds of sheets per run. Since v2.17 the per-level `atk`
  and save columns are a *transcription of a formula*, not free values: each Calling
  carries an `attackRank`, and `Validate` re-derives every row from
  `CharGen.AttackFor`/`StrongSave`/`WeakSave` (Player's Book Ch. XIV) — so a bad
  transcription fails the smoke suite instead of silently drifting from the book. The same
  discipline now covers armor (v2.18 — `ArmorFrom`, folded into `ReckonNumbers` so Defense
  and Speed have exactly one author), the Signs (v2.19 — `SignRankAt`/`SignsFor`, with
  `Validate` rejecting any Sign off the Calling's lists or above the Rank its level opened),
  and the Miracles (v2.20 — the faith-side counterpart: `MiraclesFor` on the shared `RankAt`
  spine, and `Validate` refusing any soul that works both Signs and Miracles, or a Miracle
  off its Calling's lists).
  **→ Posse** seats the result
  directly at the table. v1.5: the sheet renders on **the book's Ledger** (`LedgerView`),
  characters carry **gender** (rolled, name drawn from gender-matched lists in
  `chargen.json`; the books carry gender only in prose — reviewed 2026-07-18), a
  **nine-step wizard** (`TabsWizard.cs`; pure assembly in `CharGen.Assemble(AssembleSpec)`
  sharing `ReckonNumbers`/edge-eligibility with the generator, random fallback for any
  unanswered choice), **✎ Tweak** (edit anything; re-validated, never blocked —
  `HandTweaked` flag renders as a Ledger notice), **Save PDF…** (`Pdf.TextSheet`), and
  the full sheet rides into the posse via `PartyMember.Sheet` (persists in session.json).
  v1.6: the `chargen.json` flavor pools (`givenWomen`/`givenMen`/`vices`/`lost`/`seen`/
  `moving`) nearly doubled (16→30 names each, 8–10→16–20 flavor lines each), so generated
  and wizard-built souls repeat far less over a long campaign.
- **Generators** — every Ch. XII rollable table (town/NPC/rumor/trail/plunder/omen) plus
  all nine Grounds terrain tables and the Hand Behind It villain picker, safe-table rule
  applied automatically. v1.2: **every table expanded** with new results in the book's voice
  via `Data/tables_extra.json` (merged at load by `Db.MergeTables`; kept separate so a book
  re-extraction can never clobber the app-side additions; all new terrain entries reference
  real creatures, smoke-tested). v1.6: the single-roll tables (rumors/trail/plunder/omens
  — the ones without the town/face generators' combinatorial multi-roll structure) grew by
  10–12 entries apiece, and the Grounds terrain tables picked up every ordinary Bestiary
  beast that wasn't already cited anywhere (badger, bobcat, coyote, black bear, gray wolf,
  mountain lion, wild boar, bison bull, grizzly bear, old tusker, stampede — the White
  Bison stays off every table on purpose, per its Ch. XII "gone quiet" rumor). Also
  v1.6: **"The Hand Behind It" left the Grounds dropdown** — it's the villain picker,
  not a terrain, and read like a stray creature there (user-reported); it now has its
  own button under the terrain roller, same safe-table logic.
- **Reference** — rebuilt in v1.4 as an **11-leaf paged Keeper's screen** (◀ ▶ buttons or
  Left/Right arrows — captured in `ProcessCmdKey` so focus doesn't matter; the deck wraps).
  Each leaf is monospace tables with Blood-red header bands (`RTbl` helper; last column
  word-wraps): four degrees + DC ladder, Iron Code, wounds + Lasting Injuries, the full
  Appendix-B Conditions, Nerve/Dread + recovery, Mark & Taint, Signs & Grit, the Long
  Odds, **arms**, **goods & printed prices**, and skills/saves/abilities. The arms, goods,
  signs, and skills leaves render live from `Data/chargen.json` so they can't drift.
  All rules text taken faithfully from the books, as before.
- **Session** — free-form Keeper's notes + named 4/6/8-segment progress clocks. Autosaves
  to `session.json` beside the exe on exit **and every 5 minutes**; reloads on launch. First
  run seeds the Appendix D pregens so it's useful immediately. v1.2: a **Stamp the date**
  button drops a dated header in the ledger, an always-visible hint explains what threads &
  clocks are for, the New-thread dialog offers ready trouble patterns (editable combo), and
  every clock row has a ✎ rename button.

### Files
| File | Role |
|---|---|
| `BloodAndGritKeeper.csproj` | Project file. `net8.0-windows`, `UseWindowsForms`, `EnableWindowsTargeting` (lets it cross-compile on Linux, since it can't run there). Also carries the **self-contained single-file publish settings** (RID win-x64, `SelfContained`, `PublishSingleFile`, compression) so `dotnet publish` always yields a zero-dependency exe. |
| **`Core.cs`** | Models (`PartyMember`, `Combatant`, `CampaignClock` — all `INotifyPropertyChanged` with clamped setters), the `Rules` static class (dice parser, four-degrees, Nerve-loss ladder, encounter cost), and `Db` (loads the JSON data). |
| **`MainForm.cs`** | App shell, theme constants, the deferred-splitter `Split()` helper (see below), the emblem/icon loaders + the `Watermark()` painter (v1.4; reworked v1.6 to center in whatever background space is free and scale with the window instead of being confined to a pane's bottom half), context keyboard shortcuts + `ProcessCmdKey` Reference paging, Posse tab, Dice tab (incl. the builder keypad + v1.6's `StyleRollLog` color-coded log), persistence (`Snapshot`/`ApplySession`/autosave/autoload), demo-posse seed, and (v1.6) the universal undo/redo engine (`CaptureUndo`/`Undo`/`Redo`). |
| **`Menus.cs`** | (v1.4) The menu bar (File/View/Help), session Save-as/Load dialogs, the five-minute lesson + shortcuts windows, About box. |
| **`Tabs.cs`** | Bestiary, Encounter, Tracker, Generators, Reference (the 11-leaf paged deck + `RTbl` table renderer), Session tabs. |
| **`TabsChargen.cs`** | The New Soul tab (generate / wizard / tweak buttons, → Posse, PDF export) + the ✎ Tweak dialog. |
| **`TabsWizard.cs`** | (v1.5) The nine-step chargen wizard (`SoulWizard`, nested in MainForm) — collects an `AssembleSpec` for `CharGen.Assemble`. |
| **`CharGen.cs`** | Chargen data model, `Generate` (random), `Assemble` (wizard spec, shared `ReckonNumbers`/edge-eligibility), `Validate`, text `Render`. Compiled into the smoke rig. |
| **`Ledger.cs`** | (v1.5) `LedgerView` — the book's Ledger sheet as an owner-drawn, zoomable control — plus the per-soul pop-out windows (`ShowSoulCard`) and sheet↔member sync. |
| **`MapGen.cs`** | (v1.5) Trail Maps generator — pure, no WinForms types (compiled into the smoke rig); emits `Prim` lists + `ToSvg`. |
| **`TabsMap.cs`** | (v1.5) The Map tab UI + the GDI primitive replayer. |
| **`Pdf.cs`** | (v1.5) From-scratch PDF 1.4 writer, no packages: `TextSheet` (portrait soul sheet) and `MapPdf` (landscape map). Compiled into the smoke rig. |
| `Program.cs` | Entry point. Wraps startup in global exception handlers that write `startup-error.txt` beside the exe (or `%TEMP%`) on any crash — so failures are never silent. |
| `app.ico` / `Assets/emblem.png` | (v1.4) The cover emblem as a multi-size Windows icon (full emblem 256/128/64/48, skull-crop 32/24/16 — regenerate from `assets/img20.png` if the emblem changes) and as the watermark PNG. Both embedded; `app.ico` is also the csproj `<ApplicationIcon>` (exe file icon). |
| `Data/creatures.json` | All 150 creatures, extracted from `bestiary.html` by a one-off Python parser (balanced-div walk + per-tag capture). Re-extract and drop in fresh if the Bestiary content changes — no code changes needed. **Embedded into the exe** (`<EmbeddedResource>`), so the published build carries it inside the single file. |
| `Data/tables.json` | The 17 simple tables (13 from Ch. XII + 4 city tables from Ch. XIV) + 11 Grounds terrain tables (incl. The Ordinary Country and The Lamplit City), same extraction approach. **Book-faithful — never hand-edit; a re-extraction replaces it wholesale.** |
| `Data/tables_extra.json` | (v1.2) The app's own generator expansions — new entries for the 13 Ch. XII simple tables + extra terrain entries per ground, in the book's voice. Merged after `tables.json` by `Db.MergeTables`, so re-extraction can't eat them. Every terrain entry here must name a real creature (the smoke suite asserts it). |

### Build & run
```bash
# Requires the official Microsoft .NET 8 SDK (Ubuntu's apt package lacks
# WindowsDesktop targets) — install via https://dot.net/v1/dotnet-install.sh if needed.
cd GK/source
dotnet build -c Release

# Self-contained single-file Windows exe. The publish settings (RuntimeIdentifier=win-x64,
# SelfContained, PublishSingleFile, compression) are BAKED INTO THE CSPROJ as of 2026-07-15,
# so no flags are needed and a publish can never silently regress to framework-dependent:
dotnet publish -c Release -o publish
```
Deliverable = **just `publish/GritKeeper.exe`** (~69 MB) — a **true single-file
standalone**: the .NET runtime is bundled *and* the `Data/*.json` (creatures + tables) are
**embedded in the exe** (as of 2026-07-16), so it runs on any Windows machine with **no .NET
install and no `Data/` folder beside it**. `Db.ReadData` loads the JSON from the assembly, and
falls back to `Data/` on disk for the smoke rig / dev build (whose assemblies aren't embedded).
The exe writes only `session.json` beside itself (via `AppContext.BaseDirectory`). Published on
GitHub via **Releases** (`gh release …`), not committed — the binary is git-ignored. The
`GritKeeper.zip` (exe + full `source/` tree + `README.md`) is the source bundle.

### Known landmine: SplitContainer must not get geometry at construction time
**Hit once, cost a full crash-on-launch on real Windows — avoid repeating.** Setting
`SplitterDistance`/`Panel1MinSize`/`Panel2MinSize` on a `SplitContainer` *before* it's been
docked and laid out throws `SplitterDistance must be between Panel1MinSize and Width -
Panel2MinSize`, because at construction time the control's width is some tiny placeholder,
not its real docked size. This compiles fine and passes headless logic tests — it only
throws when the window actually renders, which Claude's Linux environment can't do, so it
reached the user before it was caught.

**The fix, already in `MainForm.cs`:** a `Split(orientation, p1Min, p2Min, ratio)` helper
that creates the SplitContainer bare and defers all geometry to a one-shot `SizeChanged`
handler, which only fires once the control has a real size, clamps mins against small
windows, and unsubscribes itself after succeeding. **Always build new splitters through
this helper, never by setting `SplitterDistance` etc. directly in an initializer.**

### Verification standard for this app
- `dotnet build -c Release` → 0 warnings, 0 errors.
- **Headless logic tests** (separate console test project, `Core.cs` compiled in directly,
  `Data/` linked beside the test binary since v1.2): dice-range checks, all four-degrees edge
  cases (including the nat-20-on-a-failure / nat-1-on-a-success regression cases — there was
  a real bug here once, a signed band scale with a gap at zero; fixed by moving to an ordered
  0–3 scale), `RollExprFull` per-die/total agreement, encounter costs, the Nerve ladder,
  model clamping, Nerve recompute on RES/Level change, `INotifyPropertyChanged` firing,
  serialization round-trips, and (v1.2) full data-load checks: 150 creatures parse, table
  merge counts, no duplicate entries, and **every terrain-table entry resolves to a real
  creature by name**. v1.5 adds: `CharGen.Assemble` conformance sweeps (incl. junk-choice
  fuzzing), gendered-name checks, `PartyMember.Sheet` session round-trips, Trail Maps
  generation/SVG/PDF structural + determinism checks (the rig now also compiles
  `MapGen.cs` + `Pdf.cs` and writes sample PDFs to `%TEMP%\gritkeeper-smoke` for external
  validation). Currently **4569/4569** passing (2322 → 2333 in v1.6, → 2339 in v1.7, → 2348
  in v1.8/v1.9, → **4569 in v1.10** with the level-up conformance sweep: `CharGen.LevelUp`
  is proved across every calling × ability method × level 1→10 — each step `Validate`-clean,
  the levels below byte-stable, fixed-seed reproducible, explicit choices honored, and the
  Gunhand/​caster growth paths checked) — re-run after any
  `Core.cs`/`CharGen.cs`/data change.
  Note: this machine has only the .NET 9 runtime for plain console apps, so `smoke.csproj`
  carries `<RollForward>LatestMajor</RollForward>` (test rig only; the app itself is
  published self-contained and unaffected).
- **Static wiring audit**: grep-confirm every `Btn(...)` call supplies a handler and every
  input control (`NumericUpDown`/`ComboBox`/`TextBox` driving logic) is referenced by at
  least one event handler — cheap and has caught orphaned controls before.
- Cannot visually verify layout from this environment — see the note in "How I like to
  work" above about the blind-build limitation and the `startup-error.txt` mechanism.

---

## Roadmap / open threads (not yet built)

- ~~**A named sample territory with an SVG map**~~ — **DONE (v2.10/v2.2):** Perdition Basin, a
  one-county worked example with a two-layer in-engine SVG map (clean player map in the Player's
  Book Appendix E; secrets-annotated Keeper map + full gazetteer in the Keeper's Book Ch. XIII).
  See `perdition_map.py`. Could still grow into a thin fourth book if you want more territory.
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
  git-ignored.
- **HRHS Scripts is local-only by design** — no remote, never push it to GitHub. Every other
  repo syncs to `github.com/cwgilgalad`.

## Changelog

Moved to [CHANGELOG.md](CHANGELOG.md) on 2026-07-18, when tracking was standardized across
all `Desktop\Git` repos.
