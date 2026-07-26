## GritKeeper v1.19.1

The last two generators nobody had grown, and a housekeeping pass over the repo.

### The city roller

It was the thinnest table set in the app — four tables, 12,000 combinations, against the town roller's million — and the only one that had never had app-side additions at all. All four are doubled:

- **Quarters** — the brewery flats and the caves under them · the old cemetery the streets were laid over · the medical college and what it needs · the freight tunnels under the wholesale district · the pest house on the far bank.
- **Who really runs it** — the waterworks board, which decides who gets a main · the undertakers' trust · the coroner · the two rival fire companies, and whichever arrives second · the Ladies' Aid Society, and the ledger it keeps.
- **Its wrong note** — the city directory lists forty households at one address · the new main was laid *around* something · two men were hanged for it and the killings did not stop · somebody has been paying the pest house's bills for eleven years.
- **Work for a posse** — stand at an exhumation and see it done honestly · trace a shipment of ice that arrived warm · keep a lamp lit on one corner from midnight to dawn.

**192,000 combinations**, up from 12,000.

### A soul reads differently now

The chargen flavor pools are what a generated character actually reads like on the Ledger, and over a long campaign they were repeating. A soul's **vice** 20 → 32, what they **lost** 16 → 28, what they've **seen** 16 → 28, what **moves** them 16 → 28, plus twelve more given names on each side.

### The tables can't quietly thin out

`tables_extra.json` — the app's own additions — is merged on top of the book's `tables.json`. If a re-extraction ever landed without it, the app would still boot and still roll, just from a much thinner deck, and nothing would say so. Every generator table and every flavor pool now has a **depth floor the smoke suite enforces**.

There's also a new check that **every creature in the Bestiary is reachable from some terrain table** — bar the White Bison, which is off every table on purpose per its Ch. XII "gone quiet" rumor.

### Housekeeping

Nothing in this section changes the app; it changes what's lying around it.

- Deleted a stale `GK/publish/GritKeeper.exe` — **155 MB**, dated 22 July, sitting in a path the release flow no longer uses.
- Deleted five `BloodAndGritKeeper.*` files from 12 July under the app's old assembly name. Running one of those by mistake looks exactly like the app hanging, which cost real time during the v1.18.0 release.
- Deleted `origin/session/2026-07-24-code-review`, fully merged into main and never cleaned up.
- **Corrected five stale claims in the project handoff doc**, including one that mattered: the build instructions still said `dotnet publish -c Release -o publish`, and that `-o` is exactly what diverted the v1.18.0 release into signing and shipping the *previous* version's exe. It also listed the app section at v1.11.0, put the deliverable at ~69 MB when compression is deliberately off and it's ~155 MB, carried a smoke count four releases old, and stated three separate times that the 18 removed Player's Book plates were still sitting in `assets/` waiting to be restored. They are not there, and git has never tracked them.

Smoke suite **10,391 assertions, all green**; the button audit reports **118 buttons, every one with a handler and a tooltip**; `verify_rules.py` reports **697 cross-checks, 0 drift**.

**Install:** download `GritKeeper.zip`, unzip, run `GritKeeper.exe`. Self-contained and Authenticode-signed — no .NET install, nothing to configure.
