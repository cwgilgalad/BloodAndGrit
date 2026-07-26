## GritKeeper v1.19.0

Weather over the trail maps, real country under them, and a turn at the table you can actually watch happen.

### The country has a shape now

The map generator used to furnish the whole frontier with hills, mesas and the occasional snowy peak. It can now say what the ground actually is:

- **Mountains, whole ranges, ridges, bluffs and escarpments, buttes and hoodoos, hardwood forests and pine stands, marsh, orchards, springs.**
- Each ground draws its own, weighted so a county reads as country with a shape to it — timber along the north, a run of hills through the middle — instead of one of everything scattered evenly.

### And it names its own places

Every ground now has six to nine named places of its own, on top of the wells and hanging trees and boot hills that turn up anywhere.

- **The high country:** The Divide · Lonesome Peak · The Palisades · Devil's Backbone · The Pinery · The Notch · Bald Knob
- **The badlands:** Chimney Butte · The Goblins · The Wall · The Tanks · The Spine · The Sand Hills
- **The river bottoms:** The Sloughs · The Landing · Drowned Ground · Cypress Stand · Snag Bend
- and the same for mining country, settled country, the fields of the dead, and the old places.

A place that arrives already named is left alone. That was a real bug: the decorator was producing *The Crooked The Wall* and *Pryor's The Spine*.

### Weather

**Fair · sunny and hot · overcast · rain · thunderstorm · fog · wind and blowing dust · snow · a blizzard · hail · hard freeze.** Each one is inked over the survey with its own wash and its own marks — slanting rain, a lightning fork, banded fog on the ground, blowing dust in long curves, a blizzard you have to read the map through. It's named in the cartouche and in the roll log.

Leave it on **as the sky wills** and the country rolls what it would really get: the high country will hand you a blizzard, the badlands never will, and the river bottoms are fogbound.

Forcing the sky doesn't move a single rock. The weather draws off its own random stream, so the same map number is the same county in every kind of weather — which is the point, if you want to run the same ground in July and in February.

### Begin turn does something you can see

It always worked. Nothing on screen said so, which is a fair reason to think a button is broken.

- The combatant whose turn it is now **lights gold and bold** on the tracker.
- A **Next strike** column says what the next one costs — *clean*, then *−5*, then *−10*.
- A line beside the round reads **"Ruth is up — 3 Beats left, next Strike clean."**
- **Next round** clears it, because a new round is nobody's turn yet.

### The Strike dialog stopped cutting itself off

Its text changes with the run mode and with whether a creature or a soul is swinging, and it was laid out to fixed heights — so the last line of the instructions, and the **Beats left** readout, ran off the right edge. That readout is the one thing a Keeper needs mid-fight. Everything in the dialog is now measured and sized to its own words, at any display scale.

### Undo and Redo look like buttons

They were always there — pinned in the status bar so they're live on every tab, plus **Edit ▸ Undo/Redo** and Ctrl+Z / Ctrl+Y. But flat text in a status bar reads as a caption, not as something you can press. They now wear a raised face and a border.

### Bigger tables everywhere else

| Table | Was | Now |
|---|---|---|
| Rumors | 44 | 56 |
| Trail — day / night | 30 each | 40 each |
| Plunder | 30 | 40 |
| Omens | 42 | 52 |
| What ails a town / what it hides | 20 each | 28 each |
| An NPC's want / their tell | 20 each | 28 each |
| Given names / surnames | 60 / 58 | 72 / 70 |

The town roller now has over a million combinations; the face roller nearly four million.

Every creature in the Bestiary except the **White Bison** — off every table on purpose, per its Ch. XII "gone quiet" rumor — is now reachable from a terrain table. That closed twenty gaps, including the whole of Ch. IX's hard men and hard country: the Comancheros, the Deserters, the Outlaw Gang, the Cattle Baron's Men, the Bounty Killer, the Regulators, the Flash Flood, and the Blizzard itself.

Smoke suite **10,372 assertions, all green**; self-test **13/13**, UI constructs in all three modes; the button audit reports **118 buttons, every one with a handler and a tooltip**.

**Install:** download `GritKeeper.zip`, unzip, run `GritKeeper.exe`. Self-contained and Authenticode-signed — no .NET install, nothing to configure.
