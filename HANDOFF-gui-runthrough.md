# GritKeeper v1.16.1 — GUI run-through (≈10 minutes)

A checklist to confirm the new table-side tools behave in the live app. The **logic** behind
all of this is covered by ~8,000 automated checks; what these can't test headlessly is the
**WinForms wiring** — the dialogs, the grid columns, the click flow. That's all this verifies.
If everything below does what it says, v1.16.1 is good to sign and ship.

## Launch

Run the fresh build:

```
GritKeeper\app\GritKeeper.exe
```

It's the unsigned v1.16.1 (that's why we're testing before signing), so Windows SmartScreen
may say "unrecognized app" → **More info → Run anyway**. On launch you should get the ready-made
demo posse (Ruth, Doc Aurelia, Elias, Anni, Addison, Opal). Confirm the title bar / About shows
**1.16.1**.

> If anything is wrong, note the step number and what happened, and hand it back — don't fight it.

---

## A. Strike ▸ (the Iron Code, adjudicated)

1. **Posse** tab → select all → send the posse to the **Tracker** (the "send to tracker" button),
   or just switch to the Tracker tab and use its **＋ Foe** to drop in a creature (type a few
   letters, e.g. "ghoul", → **＋ Foe**).
2. On the **Tracker**, select **Ruth** (a PC row). Click **Strike ▸**.
   - [ ] A dialog opens titled *"Ruth "Six-Finger" Calloway strikes"*.
   - [ ] **Target** dropdown lists the other combatants; **Weapon** is pre-filled to her revolver;
     **To hit** is pre-filled (a small number off her sheet); a red line reads roughly
     *"MAP this Strike: none (clean) · Beats left 3"*.
3. Pick the foe as the target, click **Strike ▸** inside the dialog.
   - [ ] A log line appears, e.g. *"Ruth → Ghoul: Success — 6 Blood. Ghoul at 34."* (or a miss).
   - [ ] The **foe's Blood drops** on the tracker by the amount logged.
   - [ ] Ruth's **Beats** cell drops to **2**; the dialog's MAP line now shows about
     *"MAP -5 · Beats left 2"*.
4. Click **Strike ▸** again (second Strike this turn).
   - [ ] The log shows *"(MAP -5)"* on this one — the Multiple Attack Penalty is applied.
5. Keep striking until you see a **CRITICAL** (double damage + a bigger "Fatal" number) and,
   with a revolver, an occasional **"the iron JAMS"** on a natural 1 — both are correct.

---

## B. Dread ▸ (the horror economy)

1. On the **Tracker**, select a PC soul (say **Opal**). Note her **Nerve** on the Posse tab.
2. Click **Dread ▸**.
   - [ ] Dialog reads *"Will save +N vs the Dread DC. Nerve now X/Y."* with a **DC** field, five
     quick-pick buttons (a fresh corpse … a world unmade), and **Check ▸**.
3. Click **"The walking dead (16)"** (DC jumps to 16), then **Check ▸** a few times.
   - [ ] Log lines like *"Opal: Dread 16: Failure — 4 Nerve lost."* / *"… Success — held."*
   - [ ] On a **failure**, Opal's **Nerve drops** (check the Posse tab).
   - [ ] On a **critical failure**, her tracker row gains **Frightened 1** in Conditions.
4. Keep checking (or bump the DC to 25) until her **Nerve hits 0**.
   - [ ] A **break** line appears (*"Opal breaks (d6=…): …"*), and on a 6 it says **+1 Mark**
     (and her Mark ticks up on the Posse tab).

---

## C. Beats & Begin turn

1. On the Tracker, confirm there's a **Beats** column showing **3** for a fresh combatant.
2. Select someone whose Beats you spent in test A, click **Begin turn**.
   - [ ] Their **Beats reset to 3**, and a Strike from them is "clean" (no MAP) again.

---

## D. The pool, and a long rest

1. **Posse** tab: confirm a **Pool** column. A caster/believer shows a number
   (Elias the Preacher ≈ **3 / 3**, Opal the Hexer, etc.); a Gunhand/Bounty Hunter shows **0 / 0**.
2. Edit a believer's **Pool** current down a point or two (as if they worked a Miracle/Sign).
3. Click **Rest** (long rest for the posse).
   - [ ] **Pool refills to its max**, alongside Blood and Nerve.

---

## E. The rename-safe link (the one real bug this fixes)

1. Send the posse to the Tracker. On the **Posse** tab, **rename** a soul — e.g. change
   *"Ruth "Six-Finger" Calloway"* to *"Ruth Calloway"*.
2. On the **Tracker**, apply **Damage** to that soul's row (select it, set an Amt, **Damage**).
   - [ ] Back on the **Posse** tab, **that same soul's Blood drops** — the mirror followed the
     rename. (Before this fix it silently stopped matching once the name changed.)
3. Add a second soul and name it the **same** as an existing one; send both to the tracker.
   - [ ] They stay as **two separate rows**, not one collapsed row.

---

## When it passes

Everything ticked → sign the published exe with your cert, run `.\package.ps1`, and upload
`GritKeeper.zip` to the GitHub Release with `RELEASE_NOTES_v1.16.1.md`.

Anything off → jot the step and the behavior; it'll be a quick fix.
