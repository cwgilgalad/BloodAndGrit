## GritKeeper v1.17.0

Three changes, all from table feedback — creatures fight for real, cities read right, and there are now three ways to run the game.

### Creatures fight with their own attacks
A creature dropped onto the tracker used to Strike only with the **posse's** weapons — a ghoul firing your revolver. Now GritKeeper reads each creature's own attacks straight from its Bestiary stat block and fights with **those**, through the same Iron Code engine the guns use:

- A ghoul claws at **+6 (1d8+3)**; a wraith's freezing grip drains; a fiery touch types as **fire**, so worn-armor DR doesn't stop it.
- The creature's **special maneuvers and auras** (drags you under, calls more dead, festers) are surfaced right in the Strike dialog for you to narrate.
- A stat audit across all 150 creatures confirmed the numbers were already tier-true — the gap was the app ignoring them, not thin stat blocks.

### City maps read as one place
On a ward map, rivers and lakes were drawn first and then paved over by building blocks — blue scraps between roofs — and structures could land in the water. Now a city:

- Leaves the **waterway open** and redraws the water **over** the blocks, so a river reads as one continuous course the city is built along.
- Keeps depots and landmarks **out of** the water.
- **Labels** the scattered works — *works, depot, pens, chapel, landing* — so it's plain what each mark is.

### Three ways to run the table
GritKeeper now asks how you're playing the moment it opens (changeable any time from the **Table** menu, and remembered):

- **Player's table** — a player's own pared-down view: build and run your character, roll your dice, look up the rules.
- **Keeper — with dice & books** — you roll real dice; the app is your referee and ledger. Enter the die you rolled and it reads the degrees, penalties, damage, and DR, and keeps everyone's Blood and Nerve.
- **Keeper — on the engine** — no dice, no sheets. The app rolls everything, so the whole game can be played anywhere — a phone, a porch.

Also: fixed a stale status-bar version string (now sourced from one constant). Self-test constructs the UI in all three modes — **13/13 checks passed**; the pure logic rig runs **9,600+ assertions**, all green.

**Install:** download `GritKeeper.zip`, unzip, run `GritKeeper.exe`. Self-contained and Authenticode-signed — no .NET install, nothing to configure.
