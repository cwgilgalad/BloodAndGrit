# Blood & Grit — The Keeper's Table

A desktop utility for running **Blood & Grit** at the table. Built in C# (.NET 8 /
Windows Forms), with the complete Bestiary and all the Keeper's rollable tables baked in,
extracted directly from the books (Player's Book v2.14 · Keeper's Book v2.6 · Bestiary v2.6).

**App version 1.4.0.**

---

## Running it (Windows laptop)

**No installation required.** This build is fully self-contained — the .NET runtime is
bundled inside the app folder.

1. **Before extracting:** right-click the downloaded zip → **Properties** → check
   **Unblock** → OK. (Windows tags downloaded files, and SmartScreen can silently refuse
   to launch a blocked exe — this clears it.)
2. Extract the whole zip anywhere.
3. Open the `app/` folder and double-click **`BloodAndGritKeeper.exe`**. The exe is a
   genuine single file — runtime and data are embedded — so it can travel alone.

Since v1.3.0 the exe is **Authenticode-signed by Cole Williams** (see `source/sign.ps1`),
with full version metadata, so it no longer reads as an anonymous unsigned binary. On this
household's machines the certificate is installed and trusted; on a new machine Windows
may still show SmartScreen once (the certificate is self-issued, not from a paid CA) —
click **More info → Run anyway**, and note the publisher now reads *Cole Williams*.

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

## The nine tabs

**Posse** — the party sheet. Every soul's Blood, Defense, saves, Nerve, Grit, Mark
(0–6), and Taint (0–4), all editable in place. One-click Damage/Heal, Spend Grit,
Mark +1 (warns when the Mark is full), per-soul or whole-posse **Dread Checks** on the
horror's tier ladder (1 / 1d4 / 1d6 / 1d10, doubled on a critical failure), **New
Session** (refill Nerve, reset Grit) and **Rest ▾** (a long rest — Blood *and* Nerve to
full, whole posse or one soul).

**Dice** — an expression roller (`2d6+3`, `1d8+1d6+2`…) with a **build-it-by-button
keypad** *(v1.4)*: `+d4`…`+d100` add dice (clicking the same die stacks it — d6, 2d6,
3d6), and ＋/−/digit keys build the modifier, so no typing is needed at the table. Plus
quick-dice buttons that roll one die instantly, a d20 **four-degrees check**, a running
roll log shared across the whole app — and a **dice tray** above the log where every
roll tumbles and lands on its true faces (best face rings green, a 1 rings red).

**Bestiary** — all **110 creatures**, searchable by name or Found-text, filterable by
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
Double-click any creature for its pop-out card. **New fight** clears the foes but keeps
the posse; **Clear field** wipes everything.

**Generators** — the Country in Your Pocket, one click each: a town in three rolls, a
face in four, bar-talk rumors, trail events by day and night, plunder, and wrong-note
omens — plus the Grounds terrain encounter tables (all nine, including the Hand Behind
It villain picker), with the safe-table rule applied automatically against your party
level. v1.2 expands every one of these tables with new results in the book's voice
(`Data/tables_extra.json`).

**New Soul** *(new in v1.3)* — a complete random character sheet at the press of a
button, built strictly by the book: Chapter III's eight steps end to end. Pick a level
(1–10), an ability method (the Honest Array or the 4d6-drop-lowest Gamble), and — if you
care to — a Calling and Origin, or leave both on Random. The sheet carries abilities and
modifiers, Blood/Defense/saves/Nerve/Grit reckoned exactly as Chapter III says, trained
skills (Calling number + WIT, Origin grants included), features by level with their
3rd-level Trade/School/Oath/Bargain, legal Edges (prerequisites honored, the Gunhand's
bonus combat Edges included), Signs for the Old Dark (never for Faith), the Mark where
the book imposes it, starting coin rolled on the Calling's dice and spent at printed
prices, and the Four Questions. Every generated sheet is re-validated against
`Data/chargen.json` before it is shown, and **→ Posse** seats the new soul at the table
directly. The rules data is transcribed from the Player's Book; the smoke suite
generates and rule-checks hundreds of sheets per run.

**Reference** *(rebuilt in v1.4)* — a **Keeper's screen in eleven leaves**, paged with
the ◀ ▶ buttons or the Left/Right arrow keys, every leaf formatted as proper tables:
the four degrees and the DC ladder · a turn in the Iron Code · Blood/Dying/Grievous
Wounds with the Lasting Injury table · the complete **Conditions table from Appendix
B** · the Nerve/Dread ladder and every way to recover Nerve · the Mark's six steps and
the Taint clock (DCs 13/16/20) · the eight Signs with costs and the Sign DC formula,
plus Grit's five spends · the Threat-by-Tier benchmarks and the encounter budget · the
book's **arms tables** (guns and steel, damage/cost/traits) · the **Goods & Provisions
printed prices** · and skills, saves, and abilities. The arms, goods, signs, and skills
leaves render live from `Data/chargen.json`, so they can never drift from the book.

**Session** — the Keeper's ledger (free-form notes, with a **Stamp the date** button
for session headers) and **threads & clocks**: named progress clocks of 4/6/8 segments —
tick ＋ when the world moves toward the trouble; when the last segment fills, it comes
due. New threads offer ready patterns, and every thread can be renamed (✎) as the story
turns. Everything persists between sessions.

---

## Interaction & UX

The interface follows desktop conventions so it stays out of the way mid-session:

- **No pop-up prompts for numbers.** Damage, healing, and Dread DC/Tier use inline
  spinners on each tab's action bar — set the amount once, then click.
- **Read-the-table-at-a-glance colouring.** On the Posse sheet, Blood and Nerve cells turn
  amber below a third and red at zero; the Mark and Taint render as filled pips. On the
  Tracker, downed combatants highlight red and PCs tint green.
- **Two-way sync.** Damage dealt on the Tracker writes back to the Posse sheet and vice
  versa, so a character's Blood is never out of step between tabs.
- **Guard-railed input.** Numeric grid cells reject non-numbers; every value clamps to its
  legal range (Mark 0–6, Taint 0–4, Grit 0–9, Blood/Nerve never negative).
- **Confirmations on destructive actions** — removing a soul, clearing the field or the
  encounter, deleting a thread.
- **A fresh start everywhere** *(v1.3)*: every roster and record has its own clear —
  Clear posse, Clear field, New fight, Clear (encounter), Clear log, Clear (generators),
  Clear (sheet), Clear ledger, Clear threads — each confirmed before anything is lost.
- **Text panes breathe** *(v1.3)*: the Bestiary reading pane, creature pop-out windows,
  Reference, and the generator output all carry a proper reading margin instead of
  pressing the first character against the window edge.
- **A real menu bar** *(v1.4)*: **File** (Save session Ctrl+S · Save session as… ·
  Load session… — with an automatic `session-backup.json` before any load) · **View**
  (every tab with its shortcut) · **Help** (the **five-minute lesson** on F1, a keyboard
  shortcuts card, and About).
- **Keyboard-first** *(expanded in v1.4)*: Ctrl+1–9 switches tabs; Enter rolls the dice
  expression, commits the creature pickers, and pops out the selected creature; Ctrl+D /
  Ctrl+H damage and heal on the Posse and Tracker; Ctrl+I rolls initiative and Ctrl+R
  advances the round; Ctrl+F jumps to the Bestiary search; Left/Right turn the Reference
  deck. Destructive clears deliberately stay click-and-confirm.
- **The emblem, everywhere it should be** *(v1.4)*: the steer-skull-and-rifles emblem is
  the app's window and taskbar icon and the exe's file icon, and sits as a ghost-faint
  watermark in the dead space of the busier tabs — drawn only when there's genuinely
  room, never behind rows or text.
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
enforces.
