# Blood & Grit — Project Handoff & Preferences

Import this file (and `blood-and-grit-sources.zip` / `BloodAndGrit-Keepers-Table.zip`) into
the project so a fresh chat can pick up exactly where we left off.

**Current versions: Player's Book v2.12 · Keeper's Book v2.4 · Bestiary v2.4 ·
The Keeper's Table app v1.2.2 (self-contained, crash-hardened build).**

*(The 2026-07-11 "feathering" paginator divergence is resolved: the multi-pass
feathering engine now lives in `player-src.html`'s script block, and `pag_patch.py`
detects it and no-ops — its old anchors remain as a fallback for old shells. A rebuild
from sources reproduces the delivered books; verified byte-identical against the
delivered v2.11 before any new edits were made.)*
*(Keep this doc updated with every change — see the Changelog at the bottom.)*

This project has two halves: **the three companion books** (HTML/CSS/JS, built by Python
scripts) and **The Keeper's Table** (a C#/.NET 8 WinForms desktop app for running the game
at the table). They're independent deliverables — different source trees, different build
tools — documented in their own sections below.

---

## How I like to work

- **I'm on a mobile phone.** Deliverables should be things I can download/open on mobile.
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
- **Do NOT save to PDF unless I explicitly ask.** Default deliverables are the lean sources
  and the self-contained HTML. Only run the PDF pipeline when I say "save to PDF" (or
  similar) in so many words.
- **Keep this handoff doc current.** When I make changes, update the version table, the
  Changelog, and any affected section so a fresh chat is never working from stale facts.
- **The Keeper's Table app is built and tested blind.** Claude's environment is Linux, so
  C# builds compile and run headless logic tests successfully there, but nobody can see the
  actual WinForms window render before I do. Real UI/layout bugs (like a bad SplitContainer
  crash we hit once — see Changelog) only surface when I actually run it on Windows. If
  something looks or crashes wrong, paste the `startup-error.txt` it writes, or describe
  what's on screen, and Claude will fix it blind again. Running Claude Code CLI natively on
  my Windows laptop would let Claude actually launch and see the app — worth doing for any
  serious UI work on it.

---

## The project

**Blood & Grit** — a western-horror tabletop RPG (Pathfinder-2E-derived d20 hybrid).
Three companion books share one HTML engine (cover + client-side paginator + print CSS):

| Book | Version | Pages† | Images |
|---|---|---|---|
| The Player's Book | v2.12 | 167 | one inline SVG map (Appendix E) + cover emblem |
| The Keeper's Book (GM guide) | v2.4 | 84 | one inline SVG map (Ch. XIII) + cover emblem |
| The Bestiary | v2.4 | 131 | none (110 creatures) |

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

## Files — what's in `blood-and-grit-sources.zip`

Each book's cheapest editable form is **bolded**.

| File | Role |
|---|---|
| **`player-src.html`** | Player's Book — edit this (~309 KB lean text; any images would be `src="assets/…"` refs, not base64). Currently references only the cover emblem. |
| `assets/` | The images. **`img20.png`** is the cover emblem (transparent bg + transparent lever holes) — the only asset currently used. `img01.png` (old parchment texture) and `img02–img19` (old Player plates) are present but **unused**; keep them only if you might restore plates. |
| `build_player.py` | Re-inlines any `assets/imgNN.ext` **referenced in the source** → the self-contained `blood-and-grit.html`. It discovers images by regex on the source, so it automatically inlines new refs and skips unreferenced ones (round-trips byte-identical / idempotent). |
| **`build_keeper.py`** | Keeper's Book — edit this (chapter prose lives inside as HTML strings). Holds the Player-version **cascade tuples** and the `_chq` chapter-epigraph dict. |
| **`build_bestiary.py`** | Bestiary — edit this (section text + `sb(...)` / `creature(...)` calls). Also holds the Player-version cascade tuples. |
| **`bestiary_extra.py`** | Required by `build_bestiary.py`. Holds the 25 ordinary-beast stat blocks + their field-guide lore (`LIVING_LORE`), the per-section tier/name **sorter** (`sort_sections`), and the **appendix generator** (`gen_appendix`). |
| `pag_patch.py` | Shared paginator patch (imported by keeper + bestiary builds). Generalizes `splitContainer` so prose boxes, two-column blocks, stat blocks, **and creature entries** split across page boundaries to fill whitespace instead of moving whole. |
| **`nav_tools.py`** | Shared navigation generators, imported by all three builds. `add_detailed_toc(html)` grows the simple chapter `<ul class="toc">` into a flat, splittable two-level `<ul class="toc2">` (chapters + their `<h2>` sub-heads), auto-id-ing any headings that lack ids and re-using the `ix-*` anchors; section-opener `<h2>`s anchor to their section id (the paginator stamps the section id onto its first block). `build_index(html, curated, creatures=…)` appends a letter-grouped two-column `<ul class="ix">` in a new `id="bookindex"` section (Bestiary auto-lists all `<p class="cr-name">` creatures; both books add curated concept/place entries) and inserts its Contents line. |
| **`perdition_map.py`** | Draws the **Perdition Basin** map as inline SVG from one coordinate model. `player_map_html()` = the clean honest map (river, wells, three towns, mission, trails, mesas); `keeper_map_html()` = the same base + a secrets overlay (well states bound/failing/broken, the ring of nails, faction washes, the two starter-adventure pins). Run `python perdition_map.py both` to write `_map_preview.html`. Imported by `build_player.py` (fills the `<!--PERDITION_MAP-->` placeholder in Appendix E) and `build_keeper.py` (Ch. XIII). |
| `add_detail.py` | One-shot that already baked earlier additions into the builds. **Do not re-run.** |
| `add_index.py` | One-shot that baked the v2.9 Index into `player-src.html` (anchor ids, index section, TOC line, `.ix` CSS, version cascade). Guarded against re-running, but **do not re-run** anyway. |
| `measure_index.py` | **Player's Book verification tool** (Windows; needs `pip install playwright` + Edge): builds the Player's Book, renders it headless at desktop+mobile widths, asserts page parity / zero clipping / zero h-scroll / no unresolved TOC **and** index anchors, reports TOC drift, and re-patches the static Index page numbers from the rendered truth. Run after any Player's Book content change. (Clip check forces `zoom:1` on **each `.page`**, per the note below.) |
| **`measure_book.py`** | **General verification tool** — `python measure_book.py <built-file.html>`. Renders any built book headless, asserts desktop/mobile page parity, zero true-scale clipping (mobile forces `zoom:1` per `.page`; sub-10px desktop-flow clips are tolerated as sub-pixel rounding), zero mobile h-scroll, and that every `.toc2` and `.ix` anchor resolves live. Read-only (never patches). Use for the Keeper's Book and Bestiary. |
| `make_pdf.py` | Prints all three to true 8.5×11 US-Letter PDFs. **Only run on explicit request.** |
| `README.md` | Short workflow notes. |

The per-book source files are interdependent (they need the shell + helper modules), so
**to actually build, keep the whole bundle together.**

---

## How to make a change (per book)

```bash
# Player's Book → edit player-src.html, then:
python3 build_player.py                  # → blood-and-grit.html (self-contained shell)

# Keeper's Book → edit build_keeper.py, then:
cp blood-and-grit.html keeper-handbook.html && python3 build_keeper.py

# Bestiary → edit build_bestiary.py (and/or bestiary_extra.py), then:
cp blood-and-grit.html bestiary.html && python3 build_bestiary.py

# PDFs of all three — ONLY when I explicitly ask:
python3 make_pdf.py
```

After any content change: **re-measure and patch the contents page numbers** (adding/cutting
content shifts where chapters land), run the verification checks below, **bump the book's
version on the cover**, and **update this doc's version table + Changelog.**

### The version cascade (important, easy to miss)
`build_keeper.py` and `build_bestiary.py` splice each book's own cover onto the Player shell
by **string-replacing the Player's version strings** with their own. Those match strings are
hard-coded (currently "…Version 2.8…" / "…v2.8…", four per script).

**Any time you bump the Player's Book version, you must also update those match strings in
both build scripts** — e.g.:
```bash
sed -i 's/v2.8/v2.9/g; s/Version 2.8/Version 2.9/g' player-src.html build_keeper.py build_bestiary.py
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

## The Player's Book (v2.12) — structure

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

## The Keeper's Book (v2.4) — structure

Chapters I–XIII plus the Keeper's Screen appendix and a back-of-book Index:
I. The Keeper's Chair · II. Running the Game · III. Fear, Nerve & the Mark ·
IV. The Long Odds (Building the Fight) · V. A Bestiary of the Frontier ·
VI. Cursed Ground, Hazards & Bad Medicine · VII. Rewards & Reckonings · VIII. The Cast ·
IX. A First Reckoning (starter adventure) · X. A Second Reckoning (starter adventure) ·
**XI. The Keeper's Year** (running a campaign — three campaign frames, the rhythm of a year,
three ready campaign seeds) · **XII. The Country in Your Pocket** (rollable tables: towns,
NPCs, rumors, trail events, plunder, omens) · **XIII. Perdition Basin** (new in v2.2 — the
fully-keyed sample county + the secrets-annotated Keeper map; realizes the Ch. XI "Salt Valley"
Haunted-County seed and is the home ground of both starter adventures) · Appendix: The Keeper's
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

## The Bestiary (v2.4) — structure & conventions

New in v2.2: a **generated two-level detailed Contents** and a back-of-book **Index**
(`id="bookindex"`) that auto-lists all **110 creatures** by name (from every `<p class="cr-name">`,
so it can never drift) plus ~19 curated chapter/concept entries. Note the long-standing
Roll-by-Tier appendix keeps `id="index"` — the alphabetical index is a separate `id="bookindex"`.


Eight creature chapters (110 creatures, each with lore + Found line + stat block + run-it
guidance) plus three appendices:
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
  `gen_appendix()` — so it can't drift. All 110 are always indexed; the dual flock/prophet
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

## The Keeper's Table (v1.2) — the C# desktop app

A standalone Keeper-facing utility for running games at the table, built in **C#/.NET 8,
Windows Forms**. Not part of the HTML book pipeline — separate source tree, separate build.

### Source-tree layout (IMPORTANT — read before editing the app)
There are **two** app directories under `BloodAndGrit/`. The working/master tree is **`KT/`**:
`KT/source/` (the `.cs`, `.csproj`, `Data/`), `KT/smoke/` (the headless logic-test project),
and `KT/source/publish/` (the self-contained build output). **Edit `KT/source`, build/test in
`KT/`.** The `BloodAndGrit-Keepers-Table/` folder is the *packaged deliverable* — its `source/`
mirrors `KT/source` and its `app/` holds the published build; it is regenerated from `KT/` and
then zipped to `BloodAndGrit-Keepers-Table.zip`. (History note: as of 2026-07-10 these two trees
had silently diverged — `KT/source` carried post-delivery work the zip never got. They're now
reconciled; `KT/source` won. Don't edit the delivered folder directly.)

### What it does — eight tabs
- **Posse** — full party sheet (Blood, Defense, saves, Nerve, Grit, Mark 0–6, Taint 0–4),
  inline damage/heal spinners, Spend Grit, Mark/Taint advance, per-soul or whole-posse Dread
  Checks with the real Nerve-loss ladder, New Session reset, **Rest ▾ (long rest — restore
  Blood & Nerve to full, whole posse or selected soul)**, send-to-Tracker.
- **Dice** — expression roller (`2d6+3`, `1d8+1d6+2`), quick dice, a d20 four-degrees
  checker, shared roll/event log, and (v1.2) a **dice tray** above the log: every roll's
  dice tumble (owner-drawn, 40 ms timer, ~half a second) and settle on the true per-die
  results from `Rules.RollExprFull` — best face rings verdigris, a 1 rings blood-red; shows
  up to 8 dice, "+N more" beyond that.
- **Bestiary** — all **110 creatures**, machine-extracted from the rendered Bestiary HTML
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
- **Generators** — every Ch. XII rollable table (town/NPC/rumor/trail/plunder/omen) plus
  all nine Grounds terrain tables and the Hand Behind It villain picker, safe-table rule
  applied automatically. v1.2: **every table expanded** with new results in the book's voice
  via `Data/tables_extra.json` (merged at load by `Db.MergeTables`; kept separate so a book
  re-extraction can never clobber the app-side additions; all new terrain entries reference
  real creatures, smoke-tested).
- **Reference** — expanded in v1.2 to a full mid-scene crib: four degrees, the DC ladder
  (Trivial 5 … Nigh-Impossible 30), a turn in the Iron Code (Beats, MAP, Fatal die),
  Threat-by-Tier, budget, Blood/Dying/Grievous Wounds + the d6 Lasting Injury table,
  the complete Appendix-B Conditions table, Nerve/Dread, Recovering Nerve, Mark, Taint,
  the Sign DC formula, and Grit — all taken faithfully from the books.
- **Session** — free-form Keeper's notes + named 4/6/8-segment progress clocks. Autosaves
  to `session.json` beside the exe on exit **and every 5 minutes**; reloads on launch. First
  run seeds the Appendix D pregens so it's useful immediately. v1.2: a **Stamp the date**
  button drops a dated header in the ledger, an always-visible hint explains what threads &
  clocks are for, the New-thread dialog offers ready trouble patterns (editable combo), and
  every clock row has a ✎ rename button.

### Files
| File | Role |
|---|---|
| `BloodAndGritKeeper.csproj` | Project file. `net8.0-windows`, `UseWindowsForms`, `EnableWindowsTargeting` (lets it cross-compile on Linux, since it can't run there). |
| **`Core.cs`** | Models (`PartyMember`, `Combatant`, `CampaignClock` — all `INotifyPropertyChanged` with clamped setters), the `Rules` static class (dice parser, four-degrees, Nerve-loss ladder, encounter cost), and `Db` (loads the JSON data). |
| **`MainForm.cs`** | App shell, theme constants, the deferred-splitter `Split()` helper (see below), Posse tab, Dice tab, persistence (autosave/autoload), demo-posse seed. |
| **`Tabs.cs`** | Bestiary, Encounter, Tracker, Generators, Reference, Session tabs. |
| `Program.cs` | Entry point. Wraps startup in global exception handlers that write `startup-error.txt` beside the exe (or `%TEMP%`) on any crash — so failures are never silent. |
| `Data/creatures.json` | All 110 creatures, extracted from `bestiary.html` by a one-off Python parser (balanced-div walk + per-tag capture). Re-extract and drop in fresh if the Bestiary content changes — no code changes needed. |
| `Data/tables.json` | The 13 Ch. XII simple tables + 9 Grounds terrain tables, same extraction approach. **Book-faithful — never hand-edit; a re-extraction replaces it wholesale.** |
| `Data/tables_extra.json` | (v1.2) The app's own generator expansions — new entries for all 13 simple tables + extra terrain entries per ground, in the book's voice. Merged after `tables.json` by `Db.MergeTables`, so re-extraction can't eat them. Every terrain entry here must name a real creature (the smoke suite asserts it). |

### Build & run
```bash
# Requires the official Microsoft .NET 8 SDK (Ubuntu's apt package lacks
# WindowsDesktop targets) — install via https://dot.net/v1/dotnet-install.sh if needed.
cd BloodAndGritKeeper
dotnet build -c Release

# Self-contained single-file Windows exe (bundles the runtime — no install needed on the
# target machine, ~65 MB but zero-dependency):
dotnet publish -c Release -r win-x64 --self-contained true -o publish
```
Deliverable = `publish/BloodAndGritKeeper.exe` + `publish/Data/` (keep them together),
zipped with the full `source/` tree and `README.md` as `BloodAndGrit-Keepers-Table.zip`.

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
  serialization round-trips, and (v1.2) full data-load checks: 110 creatures parse, table
  merge counts, no duplicate entries, and **every terrain-table entry resolves to a real
  creature by name**. Currently 1360/1360 passing — re-run after any `Core.cs`/data change.
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

## Changelog (newest first)

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

*Current as of the July 2026 sessions. Versions: **Player's Book v2.12 · Keeper's Book v2.4 ·
Bestiary v2.4 · The Keeper's Table app v1.2.2 (self-contained, crash-hardened).***
