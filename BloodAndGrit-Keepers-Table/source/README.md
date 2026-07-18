# Blood & Grit — The Keeper's Table

A desktop utility for running **Blood & Grit** at the table. Built in C# (.NET 8 /
Windows Forms), with the complete Bestiary and all the Keeper's rollable tables baked in,
extracted directly from the books (Player's Book v2.14 · Keeper's Book v2.6 · Bestiary v2.6).

**App version 1.2.3.**

---

## Running it (Windows laptop)

**No installation required.** This build is fully self-contained — the .NET runtime is
bundled inside the app folder.

1. **Before extracting:** right-click the downloaded zip → **Properties** → check
   **Unblock** → OK. (Windows tags downloaded files, and SmartScreen can silently refuse
   to launch a blocked exe — this clears it.)
2. Extract the whole zip anywhere.
3. Open the `app/` folder and double-click **`BloodAndGritKeeper.exe`**.
   Keep the exe together with its DLLs and the `Data/` folder — don't copy the exe out alone.

If Windows shows a blue SmartScreen panel, click **More info → Run anyway** (the app is
unsigned, which is normal for a homemade tool).

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

## The eight tabs

**Posse** — the party sheet. Every soul's Blood, Defense, saves, Nerve, Grit, Mark
(0–6), and Taint (0–4), all editable in place. One-click Damage/Heal, Spend Grit,
Mark +1 (warns when the Mark is full), per-soul or whole-posse **Dread Checks** on the
horror's tier ladder (1 / 1d4 / 1d6 / 1d10, doubled on a critical failure), **New
Session** (refill Nerve, reset Grit) and **Rest ▾** (a long rest — Blood *and* Nerve to
full, whole posse or one soul).

**Dice** — an expression roller (`2d6+3`, `1d8+1d6+2`…), quick-dice buttons, and a
d20 **four-degrees check**, with a running roll log shared across the whole app — and a
**dice tray** above the log where every roll tumbles and lands on its true faces (best
face rings green, a 1 rings red).

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

**Reference** — the rules that matter mid-scene: the four degrees, the DC ladder, a
turn in the Iron Code (Beats, MAP, crits), the full Threat-by-Tier benchmark table, the
encounter budget, Blood/Dying/Grievous Wounds with the Lasting Injury table, the
complete **Conditions table from Appendix B**, the Nerve/Dread ladder and every way to
recover Nerve, the Mark's six steps, the Taint clock (DCs 13/16/20), the Sign DC
formula, and Grit.

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
- **Keyboard-first.** Ctrl+1–8 switches tabs; Enter rolls the dice expression and commits
  the creature pickers.
- **Tooltips** on every button explain what it does.
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
