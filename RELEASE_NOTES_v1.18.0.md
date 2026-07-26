## GritKeeper v1.18.0

A session's worth of table feedback: the posse's horses and wagons are finally tracked, every list answers a right-click, and the markers on your trail map are yours to color.

### What the posse rides

The Posse tab has a second half now — **the corral & the yard** — for everything the posse rides, drives, or takes passage on: saddle horses and mules, the stagecoach, freight and buckboard wagons, a ferry, a sternwheeler, the cars.

- Each one carries its own **Blood, Defense, Speed, and capacity**, and takes a rider or a driver from the posse.
- Hurt it, mend it, and send it to the **combat tracker** — a wagon is what a Tier-III thing goes for first, and it can be shot at like anything else.
- A wrecked wagon or a downed horse reads **red at a glance**, the same as the tracker.
- Name them. A horse the table knows by name is a horse the table will miss.

### Right-click anything in a list

The posse, the corral, the tracker, the encounter plan, the Bestiary, and the roll log now answer a right-click with exactly what can be done to the row under the cursor — damage and heal, spend Grit, a Dread check, the Steady remedies, conditions, the stat block, send it to the tracker, take it off.

It's the same operations as the buttons above each list, calling the same code, so the menu can never quietly become a second set of features that disagrees with the first. The row is selected before the menu draws, so what you point at is what the app acts on. The Bestiary also gained **copy the stat block as text**, for pasting into notes or a chat window.

### Marker colors are yours

Four riders all drawn the same verdigris are four dots the table argues about.

- **Right-click a marker** to give that one its own ink — ten colors, or mix your own.
- **Marker colors ▾** re-inks a whole kind — the posse, NPCs, creatures — and remembers it between sessions.
- A marker's own color travels with the session file; the standing choice lives in `prefs.json`.

### Markers in exports — your call

A saved map used to be the survey alone, and nothing told you the markers you'd spent ten minutes arranging weren't in it. There's now a **with markers** box beside the save buttons. It's **off by default** — a map handed to the players shouldn't show them where the ambush is — and the log says which way it went either way.

### Under the floor

- **A latent map bug:** the water test measured to the river's *vertices* rather than its channel, so a spot mid-stream on a long straight reach was called dry ground. It only ever worked because every caller happened to pass a wide enough margin. Now true point-to-segment distance.
- Naming a new ride takes the lowest free number rather than a count, so selling the middle horse of three no longer mints a duplicate name.
- A menu and font leaked on every right-click across five sites; the encounter budget bar is double-buffered; `Prefs.Save` reads before it writes, so changing the run mode can't drop preferences it doesn't know about.

Smoke suite **10,113 assertions, all green**; self-test **13/13**, UI constructs in all three modes; the button audit reports **118 buttons, every one with a handler and a tooltip**.

**Install:** download `GritKeeper.zip`, unzip, run `GritKeeper.exe`. Self-contained and Authenticode-signed — no .NET install, nothing to configure.
