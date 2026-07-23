# GritKeeper — Blood & Grit

**GritKeeper** (formerly *The Keeper's Table*) is a desktop utility for running
**Blood & Grit** at the table. Built in C# (.NET 8 / Windows Forms), with the complete
Bestiary and all the Keeper's rollable tables baked in, extracted directly from the books
(Player's Book v2.15 · Keeper's Book v2.7 · Bestiary v2.8).

**App version 1.10.1.**

---

## Running it (Windows laptop)

**No installation required.** This build is fully self-contained — the .NET runtime is
bundled inside the app folder.

1. **Before extracting:** right-click the downloaded zip → **Properties** → check
   **Unblock** → OK. (Windows tags downloaded files, and SmartScreen can silently refuse
   to launch a blocked exe — this clears it.)
2. Extract the whole zip anywhere.
3. Open the `app/` folder and double-click **`GritKeeper.exe`**. The exe is a
   genuine single file — runtime and data are embedded — so it can travel alone.

The exe is **Authenticode-signed by Cole Williams** (see `source/sign.ps1`),
with full version metadata, so it doesn't read as an anonymous unsigned binary. On this
household's machines the certificate is installed and trusted; on a new machine Windows
may still show SmartScreen once (the certificate is self-issued, not from a paid CA) —
click **More info → Run anyway**, and note the publisher reads *Cole Williams*.

**If it still won't start**, the app writes a `startup-error.txt` beside the exe (or in
`%TEMP%\BloodAndGrit-startup-error.txt`) describing exactly what went wrong — send me its
contents and I'll fix it.

**From source (optional, needs the .NET 8 SDK):**
```
cd source
dotnet run
```

Your table state auto-saves to `session.json` beside the exe on exit **and every five
minutes**, and reloads on launch. First launch seeds the ready-made posse from the
Player's Book Appendix D so everything is usable immediately.

## The ten tabs

**Posse** — the party sheet. Every soul's Blood, Defense, saves, Nerve, Grit, Mark
(0–6), and Taint (0–4), all editable in place, and **▲ ▼ reorder the posse** to taste.
One-click Damage/Heal, Spend Grit, Mark +1 (warns when the Mark is full), per-soul or
whole-posse **Dread Checks** on the horror's tier ladder (1 / 1d4 / 1d6 / 1d10, doubled
on a critical failure), **New Session** (refill Nerve, reset Grit) and **Rest ▾** (a long
rest — Blood *and* Nerve to full, whole posse or one soul). *(v1.5)* **Double-click a
soul (or hit the far-right Ledger button) to open their character sheet** — the book's
own Ledger — **in its own window**, the same modeless pop-out pattern as the Bestiary's
creature cards; **double-click the Notes cell** to read and edit the whole note in a
proper editor instead of squinting at the truncated cell. *(v1.9)* a **Gender** column,
shown on every soul's row and Ledger. *(v1.10)* **✦ Level up** — advance a soul built on
the New Soul tab one level at a time; the dialog offers only what the new level actually
unlocks (roll the new Hit Die, the 5th/10th ability boost, the odd-level Edge and the
Gunhand's bonus combat Edge, the 3/5/7/9 skill increase, the 3rd-level path, and any new
Signs), every list drawn from the character rules so it can't offer an illegal pick — and
the same button rides on each Ledger window. The new Blood and Nerve are yours in full,
and it's one press of Undo if you change your mind.

**Dice** — an expression roller (`2d6+3`, `1d8+1d6+2`…) with a **build-it-by-button
keypad**: `+d4`…`+d100` add dice (clicking the same die stacks it — d6, 2d6, 3d6), the
*(v1.5)* **× spinner adds several at once** (set × 4, click +d6, get 4d6), and ＋/−/digit
keys build the modifier, so no typing is needed at the table. Plus quick-dice buttons
that roll one die instantly, a d20 **four-degrees check**, a running roll log shared
across the whole app — and a **dice tray** above the log where every roll tumbles and
lands on its true faces. *(v1.5)* **Every die wears its own color** — green d4, blue d6,
orange d8, white d10, yellow d12, red d20, purple d100 — on the buttons and in the tray
alike; a best face rings gold, a 1 rings black. *(v1.6)* **The log itself is
color-coded**: a critical success rings gold and bold, a critical failure rings
near-black and bold, a plain success is verdigris green, a plain failure is rust, and
any other roll gets a neutral steel-blue tag — so a result reads at a glance instead of
by squinting at the words.

**Bestiary** — all **150 creatures**, searchable by name or Found-text, filterable by
tier and chapter, with the full book entry displayed. **Double-click any creature to pop
it out into its own window** — resize it, maximize it, and step the text size up and
down (A− / A＋); open as many creatures side by side as the fight needs. One click sends
a creature to the Encounter builder or straight onto the battlefield (`× N` copies at
once).

**Encounter** — plan a fight *before* you run it, with the budget calculator from the
Keeper's Book: 4 points per soul in the posse, each creature auto-costed against the
party's level (Even foe 4 / Mook 1 / Standout 8) and a running verdict from "under
budget" to "you had better mean it." Add creatures right on the tab with the type-ahead
picker (× N), or send them over from the Bestiary. Creatures two or more Tiers over the
posse are flagged with the **safe-table rule**. Happy with the odds? **Send all →
Tracker.**

**Tracker** — initiative and battle. Roll initiative for the whole field, **Sort ▾**
(initiative / name / Blood, each ascending or descending), advance rounds, deal damage
and healing (PC damage mirrors back to the Posse sheet), tag **conditions ▾** from the
Appendix B list, remove the fallen. Add foes three ways: the **Foe type-ahead box**
right on the tab, the Bestiary's `→ Tracker` (× N), or **＋ Add** for ad-hoc NPCs.
Double-click any creature for its pop-out stat block — and *(v1.5)* **posse souls get
their Ledger instead** (double-click, or the far-right Ledger button that only appears
on rows that have a sheet to show). **New fight** clears the foes but keeps the posse;
**Clear field** wipes everything.

**Generators** — the Country in Your Pocket, one click each: a town in three rolls, a
face in four, bar-talk rumors, trail events by day and night, plunder, and wrong-note
omens — plus the Grounds terrain encounter tables (all nine, including the Hand Behind
It villain picker), with the safe-table rule applied automatically against your party
level, and every table expanded with new results in the book's voice
(`Data/tables_extra.json`). *(v1.6)* **The single-roll tables grew further** — a dozen
or more new rumors, trail events, finds, and omens apiece — and the Grounds tables
picked up every ordinary beast from the Bestiary that wasn't already on a terrain table
(badger, bobcat, coyote, black bear, gray wolf, mountain lion, wild boar, bison bull,
grizzly bear, old tusker, stampede), so a re-roll turns up something new far more often.
Also *(v1.6)*: **The Hand Behind It** — the villain picker — left the terrain dropdown
(where it read like a stray creature) and got its own button under the terrain roller.

**Map** *(new in v1.5)* — **Trail Maps, a drafting table for frontier surveys.** Set the
ground (the Bestiary's nine Grounds), the scale (a single gunfight up to weeks of
trail), the hour (night maps come with stars and a moon), and the water; tick a trail, a
rail line, a settlement, a battle grid; and **🎲 New map (Ctrl+G)** draws a named survey
in the book's hand — landmarks, a scale bar, a compass rose and all. **The same seed and
settings always draw the same map**, so note the map's number and you can have it back
next session. The **Keeper's layer** adds the secrets in red — old blood in the ground,
something buried, sign of the beast — leave it off before showing players. Export as
**SVG** (file or clipboard) or a **one-page landscape-Letter PDF**; the on-screen
drawing, the SVG, and the PDF all replay the same primitives, so they always match.

*(v1.6)* The survey became a **battle board**. **Zoom & pan**: roll the mouse wheel
over the map to zoom at the cursor (up to 8×), drag empty ground to pan, and 🔍＋ / 🔍− /
**Fit** live on the bar; the view never leaks into exports. **Tactical markers**:
**＋ Marker ▾** drops a posse soul (green), an NPC (gold), or a creature (red) at the
center of your view; **Tracker → Map** puts everyone on the tracker onto the field in
two columns — posse west, trouble east — skipping anyone already standing; **drag** a
marker to move it (each completed drag is one undo step); **right-click** a marker to
rename or remove it; **Clear markers** asks first. Markers ride in `session.json` and
hold their ground across restarts and even fresh map seeds — they're your fight, not
the map's.

*(v1.8)* **The map holds still, and everything answers to you.** Fixed a real bug:
checking or unchecking any overlay (Trail, Rail, Settlement, Grid, the Keeper's layer)
used to quietly regenerate a *different* countryside, because every feature drew from
one shared random stream. Each feature now has its own seed-derived stream, so a
checkbox is pure ink-on/ink-off — and **exports are exactly what you see**: SVG and PDF
carry whatever overlays are checked, your moved landmarks included. **Fords now sit on
the water** (mid-river, or on the lake shore) instead of out in the sagebrush. **The
Keeper's red marks drag too**: with ✥ pressed and the Keeper's layer shown, the red
circles ring in red and move just like landmarks — put the trouble where it actually
is. And the bar was reorganized into three sane rows: the survey (what the map is),
Show/Zoom (how you view it), and table tools + Export (what you do with it).

*(v1.7)* **The landmarks answer to you now.** Press **✥ Landmarks** and every named
landmark wears a dashed gold ring — drag one to put the Hanging Tree where your table
needs it (symbol and label travel together); right-click it to put it back where the
survey drew it, or to put them all back. Custom placements hold while you stay on that
map number — toggling the hour or the Keeper's layer won't shake them loose — and your
SVG/PDF exports carry them. And **the ink respects the border now**: rivers, creeks,
trails, and rails are clipped to the map's inner neatline at generation, so nothing
runs off the paper in the preview, the SVG, or the PDF (rivers used to).

**New Soul** *(overhauled in v1.5)* — a complete character at any level 1–10, displayed
on **the book's own Ledger sheet** (the character sheet from the back of the Player's
Book, redrawn live and filled in — name, **gender**, calling, origin, abilities,
reckoned numbers, the Mark's six boxes, the Four Questions, all seventeen skills with
proficiency ticks, edges & path, arms & gear & coin). Three roads to a soul:

- **🎲 Make a soul** — rolled strictly by Chapter III's eight steps: abilities (Honest
  Array or the 4d6-drop-lowest Gamble), Calling and Origin with their cross-constraints
  honored, skills, legal Edges, Signs for the Old Dark only, the Mark where the book
  imposes it, coin rolled on the Calling's dice and spent at printed prices, gender and
  a name drawn to match, and the Four Questions. Pin the Calling or Origin if you have
  one in mind.
- **🧭 Wizard…** — build a custom character choice by choice through nine steps: level,
  method and name · Calling · Origin · assign the six abilities (with a Suggest button
  and 5th/10th-level boosts) · pick trained skills and skill increases · pick every Edge
  from lists filtered to what's legal so far · Signs, path and calling choices · roll
  the coin and shop the printed price list against a live balance · answer the Four
  Questions. Anything left on "(let the book pick)" is rolled by the same rules as the
  generator.
- **✎ Tweak** — hand-adjust any number or any list on a finished sheet. Tweaks are the
  Keeper's word against the book's: the sheet is re-checked but never blocked, and the
  Ledger simply notes it was hand-tweaked.

Every sheet is validated against `Data/chargen.json` before it's shown. **→ Posse**
seats the soul at the table — the full sheet rides along into `session.json`, so their
Ledger window keeps everything forever. **Copy sheet** takes the text anywhere, and
*(v1.5)* **Save PDF…** writes a printable Letter sheet. *(v1.6)* The given-name pools
(and the vice/lost/seen/moving flavor tables) nearly doubled, so generated and
wizard-built souls repeat far less across a long campaign.

**Reference** — a **Keeper's screen in eleven leaves**, paged with the ◀ ▶ buttons or
the Left/Right arrow keys, every leaf formatted as proper tables: the four degrees and
the DC ladder · a turn in the Iron Code · Blood/Dying/Grievous Wounds with the Lasting
Injury table · the complete **Conditions table from Appendix B** · the Nerve/Dread
ladder and every way to recover Nerve · the Mark's six steps and the Taint clock (DCs
13/16/20) · the eight Signs with costs and the Sign DC formula, plus Grit's five spends
· the Threat-by-Tier benchmarks and the encounter budget · the book's **arms tables**
(guns and steel, damage/cost/traits) · the **Goods & Provisions printed prices** · and
skills, saves, and abilities. The arms, goods, signs, and skills leaves render live from
`Data/chargen.json`, so they can never drift from the book.

**Session** — the Keeper's ledger (free-form notes, with a **Stamp the date** button
for session headers) and **threads & clocks**: named progress clocks of 4/6/8 segments —
tick ＋ when the world moves toward the trouble; when the last segment fills, it comes
due. New threads offer ready patterns, and every thread can be renamed (✎) as the story
turns. Everything persists between sessions.

---

## Interaction & UX

The interface follows desktop conventions so it stays out of the way mid-session:

- **Universal Undo/Redo** *(new in v1.6)*: **Edit ▸ Undo / Redo** (Ctrl+Z / Ctrl+Y), also
  pinned as buttons in the status bar so they're reachable from any tab. Covers the
  posse, tracker, encounter builder, and campaign threads/clocks — any add, remove, or
  edit to any of them is one step back. Session notes keep the textbox's own native
  undo instead (snapshotting every keystroke would flood the stack).
- **No pop-up prompts for numbers.** Damage, healing, and Dread DC/Tier use inline
  spinners on each tab's action bar — set the amount once, then click.
- **Read-the-table-at-a-glance colouring.** On the Posse sheet, Blood and Nerve cells turn
  amber below a third and red at zero; the Mark and Taint render as filled pips. On the
  Tracker, downed combatants highlight red and PCs tint green. On the Dice tab, every die
  wears its color.
- **Two-way sync.** Damage dealt on the Tracker writes back to the Posse sheet and vice
  versa, so a character's Blood is never out of step between tabs.
- **Guard-railed input.** Numeric grid cells reject non-numbers; every value clamps to its
  legal range (Mark 0–6, Taint 0–4, Grit 0–9, Blood/Nerve never negative).
- **Confirmations on destructive actions** — removing a soul, clearing the field or the
  encounter, deleting a thread.
- **A fresh start everywhere**: every roster and record has its own clear —
  Clear posse, Clear field, New fight, Clear (encounter), Clear log, Clear (generators),
  Clear (sheet), Clear ledger, Clear threads — each confirmed before anything is lost.
- **Text panes breathe**: the Bestiary reading pane, creature and soul pop-out windows,
  Reference, and the generator output all carry a proper reading margin instead of
  pressing the first character against the window edge.
- **A real menu bar**: **File** (Save session Ctrl+S · Save session as… ·
  Load session… — with an automatic `session-backup.json` before any load) · **View**
  (every tab with its shortcut) · **Help** (the **five-minute lesson** on F1, a keyboard
  shortcuts card, and About).
- **Keyboard-first**: Ctrl+1–9 switches tabs and Ctrl+0 reaches the tenth; Enter rolls
  the dice expression, commits the creature pickers, and pops out the selected creature;
  Ctrl+D / Ctrl+H damage and heal on the Posse and Tracker; Ctrl+I rolls initiative and
  Ctrl+R advances the round; Ctrl+F jumps to the Bestiary search; Ctrl+G draws a fresh
  map; Left/Right turn the Reference deck. Destructive clears deliberately stay
  click-and-confirm.
- **The emblem, everywhere it should be**: the steer-skull-and-rifles emblem is
  the app's window and taskbar icon and the exe's file icon, and sits as a ghost-faint
  watermark in the dead space of the busier tabs — drawn only when there's genuinely
  room, never behind rows or text. *(v1.6)* It's no longer confined to the bottom half
  of the pane: it centers in whatever background space is actually free and scales with
  the window, so it reads as a real watermark on a big screen instead of a fixed-size
  sticker.
- **Tooltips** on every button explain what it does (and name its shortcut, where one
  exists).
- A consistent frontier-book palette (aged paper, oxblood headers, gold accents) ties the
  tool to the books.

## Data fidelity

`Data/creatures.json` and `Data/tables.json` were machine-extracted from the rendered
books, so every stat block, lore paragraph, keeper note, witness quote, and table entry
matches the published text word for word. If the books change, re-extract and drop in
new JSON — no code changes needed. The app's own table expansions live separately in
`Data/tables_extra.json` (merged at load), so a re-extraction can never overwrite them —
and every terrain entry there references a real Bestiary creature, which the test suite
enforces. `Data/chargen.json` is the character-rules transcription (Ch. III–IV,
VIII–X, XIII–XIV) — the generator, the wizard, the validator, and four Reference leaves
all read from it, and the smoke suite (2,300+ asserts) proves every generated and
wizard-assembled sheet conformant on every run.
