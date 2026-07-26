## Blood & Grit — Player's Book v2.24 · Keeper's Book v2.11 · Bestiary v2.10 · GritKeeper v1.20.0

The safe-table rule stops being a sentence and becomes a rule you can run, and a wording pass over everything finds the fault in the app rather than the books.

### Sign & Spoor

The Bestiary said that a horror two or more Tiers over the posse "arrives as sign and spoor, not in the flesh" — and stopped there. That tells a Keeper what *not* to run and leaves them to invent the scene at the table. The Grounds appendix now runs it properly.

**What the words mean.** *Spoor* is the physical trace: the track, the scat, the hair caught on wire, the blood, the scrape on a tree at a height you would rather not measure. *Sign* is everything wider — the kill, the silence where there were birds an hour ago, the stock that will not go back in the barn. The word appeared in three books and the app and had never once been defined.

**Reading it.** A Survival check against the *thing's* Tier, not the party's:

| Tier of the thing | Read the sign | Dread Check | What is left of it |
|---|---|---|---|
| I | Survival DC 12 | — | Tracks, and a killed animal that was eaten properly |
| II | Survival DC 14 | DC 10 | A killed animal that was not eaten, and was not left the way a beast leaves one |
| III | Survival DC 16 | DC 13 | A killed man, and the manner of it plain in what's left |
| IV | Survival DC 18 | DC 16 | A killed party, and one survivor who will not go back |
| V | Survival DC 20 | DC 20 | A place unmade — ground, weather, and the people in it, all wrong together |

The Dread DC is **one rung below meeting the thing itself**, because reading an aftermath is not standing in front of the animal. A Tier I trace costs nothing at all: out here a cougar kills a calf, and that is weather.

**The four degrees** each buy something different — a critical success gets what it is, how many, how long ago, which way, and whether it already knows about them; a critical failure has them reading it backward, and the Keeper is told to play the wrong answer straight.

**Then it becomes a thread.** Start a four-segment clock and name it for the horror. Each fresh sign fills a segment. A full clock is the night it arrives in the flesh — by which time the posse is a Tier stronger, or holds a plan, or has decided to be somewhere else. That is the whole trade the rule offers: the monster they cannot fight becomes the reason they get strong enough to.

The **Keeper's Book** never mentioned the safe-table rule at all — in the one chapter a Keeper reads to learn how to build a fight. Ch. IV now carries it, with a Keeper's-eye note on why it is a pacing tool and not a restriction.

### In the app

The Reference deck's **Long Odds** leaf gained a **Safe-Table Rule — Sign & Spoor** block with the definition, the table, and the four degrees. Rolling a ground on the **Generators** tab now prints the whole scene — the trace, the Survival DC, the Dread Check, the clock — where before it only flagged that the rule applied and left you there.

All of it renders from one place in the code, and the "one rung below" claim is asserted against the book's own Threat-by-Tier Dread DCs, so book and app cannot drift apart.

### The wording pass

Every marker for machine-written prose, measured across all three books: negative parallelism, stock vocabulary, conversational filler, rhetorical shapes, hedging density, triad density, sentence-length variance.

**The books came back clean.** Burstiness 0.91–1.52 against a generated-text threshold near 0.45; hedging under 1.4 per thousand words; zero hits on every filler pattern tested. Nothing needed rewriting.

**The app's table entries did.** Measured against the book's own entries, every single app-side addition ran longer — 21% to 88% — and single-clause entries had collapsed from 75% to 25%. Each one carried a trailing clause explaining what it had already implied: *"…and they've heard where one is buried"*, *"…and the depot keeps the worst of them"*. The book's voice stops; these explained. **129 entries rewritten** across all thirteen prose tables.

Smoke suite **10,418 assertions, all green**. Books measure clean at 200 / 101 / 166 pages — page parity, zero true-scale clipping, zero mobile horizontal scroll, every Contents and Index anchor resolving live. Whitespace audit shows no mid-flow gaps. PDFs regenerated and verified at 612×792pt.

**Install:** download `GritKeeper.zip`, unzip, run `GritKeeper.exe`. Self-contained and Authenticode-signed — no .NET install, nothing to configure.
