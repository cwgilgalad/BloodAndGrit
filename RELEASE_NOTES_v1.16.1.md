# GritKeeper v1.16.1

The Keeper's side of *Blood & Grit* in one window — now with the whole Iron Code and the
horror economy adjudicated for you, not just displayed. Unzip, run `GritKeeper.exe`. No .NET
install, no data folder, nothing to configure; it autosaves the session beside itself.

This release folds in everything since v1.11 — a run of work that moved the app from a tracker
and character generator into a table-side rules engine.

## New at the table

- **Strike ▸** — resolve an attack through the Iron Code engine: to-hit, the four degrees, the
  Multiple Attack Penalty at the attacker's current step, the Fatal die on a critical hit,
  Misfire jams, and the target's Damage Reduction by type — Blood taken, Beat spent, off one
  log line. A PC's to-hit is read straight off their sheet.
- **The Beat tracker** — every combatant carries three Beats and a MAP step; **Begin turn**
  resets them, and the tracker shows them live.
- **Dread ▸** — roll a Dread Check for the selected soul: Will save vs the Dread DC, Nerve off
  the ladder, Frightened on a critical failure, and the break table (and its Mark) at 0 Nerve.
  Quick-picks for the five sights, from a fresh corpse to a world unmade.
- **The faith/sign pool, tracked live** — Grace, Conviction, Breath, Vital Breath, and the
  Witch Hunter's Zeal ride on the posse and refresh with a long rest, beside Blood and Nerve.

## New in the character generator

- **Both magic traditions, in full** — the Old Dark's **40 Signs** (three lists, five Ranks)
  and the Faithful's **40 Miracles** (six lists, same Rank spine), each ranked, list-gated by
  Calling, and gated to the level that opens the Rank. No soul works both.
- **Arms and armor as real gear** — armor sits on the sheet with its DR (vs blades and small
  shot), folded into Defense and Speed, and generated souls buy it at their Calling's priorities.
- Every generated sheet is still re-derived and rules-checked end to end — a mistyped number
  fails the build, not the table.

## Under the hood

- **A rename can't break the posse↔tracker link.** Souls are matched by a stable id, so
  renaming a character mid-session keeps their Blood mirrored and never collapses two
  same-named souls into one row.
- The gun rules, the Dread ladder, and the whole character math are covered by ~8,000
  automated checks; the printed books, the app's data, and the rules are proven in step.

---

*Everything here is data-driven from the same source as the books, so the app and the printed
page can't quietly disagree. Found a rough edge? It's a young tool — say so.*
