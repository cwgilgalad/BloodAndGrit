# Getting Blood & Grit onto Discord, and onto other people's screens

A proposal, 2026-07-27. Nothing here is built. It exists so the decision can be made with the
actual shape of the codebase in view rather than from a standing start.

---

## First: three things about this codebase that make it cheaper than it looks

**1. The rules engine is already headless, and already proven.** `GK/smoke/smoke.csproj`
compiles exactly six files — `Core.cs`, `CharGen.cs`, `IronCode.cs`, `Horror.cs`, `MapGen.cs`,
`Pdf.cs` — with **no WinForms reference at all**, and runs ~12,150 assertions against them every
build. That is not "a rules engine we could extract one day". That *is* the rules engine, already
separated, already tested, already building for a plain `net8.0` target that runs on Linux. Making
it a class library the desktop app and a bot both reference is a `.csproj` change, not a refactor.

**2. The app already knows how to draw the things you'd want to send.** `LedgerView` renders a
whole character sheet to a bitmap (verified — the screenshots taken while fixing the fonts this
session were made exactly that way, via `DrawToBitmap`). `MapGen.ToSvg` and `Pdf.MapPdf` already
produce shareable map files. Posting a soul's sheet or the night's map into a channel is mostly
plumbing, not rendering work.

**3. `RunMode.Player` already exists.** The app already has a coherent notion of *a pared-down
view for someone who is not the Keeper* (New Soul / Dice / Reference only). Whatever a remote
player sees is a descendant of that idea, not a new one.

And one thing that makes it more expensive than it looks:

**`Rules.Rng` is a process-wide static** (`Core.cs:540`), and `Rules.Reseed(int)` swaps it
wholesale — that's how the Trail Maps get their determinism. On one desktop for one table that is
exactly right. On a shared server handling two tables at once it is a live hazard: table B
reseeding for a map would silently take over table A's dice. **Anything server-shaped needs
per-session RNG before it needs anything else.**

---

## These are two different asks

They get run together and they shouldn't be:

- **"Discord integration"** — the game reaches into a chat channel people are already sitting in.
  Rolls, handouts, sheets, maps. It is mostly a *distribution* problem.
- **"Online play"** — people who are not in the room can play. Shared, live state; everyone sees
  the same tracker; a player acts and the Keeper's screen changes. It is a *state* problem, and
  strictly harder.

Discord can serve as the transport for a surprising amount of the second one, which is what makes
the ladder below worth walking in order instead of jumping to the end.

---

## The ladder

### Rung 0 — Discord as an output sink (webhook). *Smallest useful thing.*

The app posts to a channel through an incoming webhook URL pasted into settings. One-way. No bot,
no hosting, no OAuth, no accounts, no always-on process.

What goes out: the roll log as it happens, four-degrees results with the degree named, a Dread
Check and what it cost, the generated adventure, a Ledger as a **PNG**, a Trail Map as SVG/PDF.

- **Buys you:** the table — including people on the couch and the one player who's remote
  tonight — sees what happened, in a place they already have open, on their phone, with history
  they can scroll back through. Handouts stop being "I'll email it after".
- **Doesn't buy you:** players can't *do* anything. It's a broadcast.
- **Cost:** small. `HttpClient`, a JSON body, multipart for files. A settings field and a
  "post to Discord" toggle on the roll log.
- **Note:** this is the one rung that puts networking inside `GritKeeper.exe`. Keep it strictly
  optional and fail-soft — the app's current virtue of working perfectly at a table with no wifi
  must survive.

### Rung 1 — a Discord bot that rolls under the real rules. *Best value per unit of work.*

A **separate** small console app (Discord.Net or DSharpPlus) referencing the extracted rules
library. `/roll 2d6+3`, `/check dc:16 skill:Survival`, `/dread tier:3`, `/strike`, `/grit`,
`/sheet`.

Two things make this better than a generic dice bot, and they're the whole point:

- It rolls **Blood & Grit's** dice — the four degrees with crit-on-beat-by-10 and nat-20/nat-1
  handled the way `Core.cs` handles them, the real Nerve-loss ladder, the real Mark break table.
  The same code the books are checked against.
- **Ephemeral replies.** Discord can show a response *only to the person who typed it*
  (`flags: 64`). For a horror game that is not a nicety — a player can take a Dread Check and
  learn what it cost them without the table learning it, while the Keeper gets the truth. The
  Mark and Taint tracks are built for exactly that kind of privacy.

- **Buys you:** every player rolls from their phone, under the book's rules, with no new UI to
  design and no app for them to install. This lands squarely on the stated
  responsive/phone-friendly priority at close to zero front-end cost.
- **Doesn't buy you:** shared live state. The bot doesn't know who's on the tracker.
- **Cost:** moderate — bot token handling, slash-command registration, and the library
  extraction below. Can run on the Keeper's own PC during a session; doesn't need hosting.

### Rung 2 — shared live state. *Where "online play" actually begins.*

Two routes, and the cheap one is better than it sounds.

**2a — the LAN companion. Recommended first move for real play.**
GritKeeper hosts a tiny local web server (Kestrel, or even `HttpListener`) and serves a single
responsive HTML page. Players on the same wifi open `http://<keeper's-ip>:8080` on their phones
and get their own Ledger, their Blood/Nerve/Grit, and buttons that do something. State lives where
it already lives — in the Keeper's `GameSession` — and the page polls or holds a WebSocket.

Why this fits *this* project specifically: no hosting bill, no accounts, no auth story, no cloud
state, no privacy question, and the HTML/CSS work is the thing this project is already best at —
the same responsive discipline that goes into the books. For an in-person table it is arguably the
*correct* answer, not the cheap one. For remote play, put a Cloudflare Tunnel in front of it and
the same page works from anywhere.

**2b — Discord as the state surface.**
The bot keeps one pinned message per channel showing the live tracker and edits it as the fight
moves. Turn order, Blood bars, conditions, whose turn it is. Discord rate-limits message edits
(roughly 5 per 5 seconds per channel), which sounds fatal and isn't — this is a turn-based game
where the tracker changes a few times a minute. Threads map neatly onto the existing "threads on
the trail" (`signs`), one Discord thread per trace.

- **Buys you:** genuine remote play. Players act; the Keeper's screen updates.
- **Cost:** the largest step on the ladder. Needs per-session RNG, a state-authority decision,
  and reconnection handling.

### Rung 3 — a full virtual tabletop. *Recommend against.*

Tokens, fog of war, drag-and-drop on a live map. This is a different product with a different
maintenance burden, and it competes with tools that have years of head start.

**The 80% already exists for free:** the Trail Maps SVG/PDF export drops straight into Owlbear
Rodeo, Foundry or Roll20 as a map image today. Document that in the README and the itch is
largely scratched.

---

## The one enabling refactor, and why it pays for itself anyway

Split `GK/source` into:

- **`BloodAndGrit.Rules`** — a plain `net8.0` class library: the same six files the smoke rig
  already compiles, plus `Data/*.json` embedded. Runs on Linux. No WinForms.
- **`GritKeeper`** — the WinForms app, referencing it.
- **`GritKeeper.Bot`** (later) — referencing the same library.

This is worth doing **whether or not any of the above gets built**. Right now `smoke.csproj`
maintains a hand-listed `<Compile Include="..\source\*.cs" />` for each file, which is a list that
can silently fall out of date with what the app actually contains — add a seventh headless file
and forget to list it and it simply goes untested. A project reference can't drift that way. It
also makes "the rules are one thing, the UI is another" structural rather than a convention, which
is the same discipline CLAUDE.md already insists on for the numbers.

**Do this first regardless.** It's the cheapest item on this page and the only one that improves
the current build.

---

## Recommended order

1. **Extract the rules library.** Small, pays for itself immediately, unblocks everything else.
2. **Rung 0, the webhook.** A weekend. Immediately useful at the next session. Tells you whether
   Discord is actually where this group lives before you build anything for it.
3. **Rung 1, the bot.** Only if step 2 gets used. This is the one that changes how it feels to
   play.
4. **Then decide between 2a and 2b** based on something you'll only know by then: whether the
   problem is *people in the room on their phones* (→ 2a, the LAN companion) or *people who aren't
   in the room at all* (→ 2b, or 2a behind a tunnel).

Stopping after 2 is a perfectly good outcome. Stopping after 3 probably is too.

---

## Decisions that need making before Rung 1, not during it

- **Who is the authority on state?** If the bot can roll and the app can roll, they will
  eventually disagree, and this project's own standing rule is that two authorities for one fact
  is a bug. Pick one: the Keeper's app owns the session and the bot is a client of it. Write that
  down before writing code.
- **Where do secrets live?** A webhook URL and a bot token are bearer credentials — anyone holding
  the webhook URL can post as you, forever, until it's rotated. They belong in `prefs.json` beside
  the exe (already outside git), never in `session.json`, which gets saved, loaded and shared.
  Worth a line in the UI saying so.
- **Per-session RNG.** Before anything serves two tables. `Rules.Rng` static → an instance
  threaded through, or `[ThreadStatic]`, or a session-scoped context object. The determinism the
  maps rely on has to survive the change, and the smoke rig's fixed-seed tests will tell you
  whether it did.
- **Does the desktop app stay useful offline?** It should. That's a real feature at a real table.
  Any networking in `GritKeeper.exe` itself stays optional and fails quietly.

---

## What this proposal deliberately doesn't recommend

- Rewriting the app as a web app. The desktop app is finished, signed, self-contained and good.
- Putting Discord.Net inside `GritKeeper.exe`. Keep the bot a separate process so the app keeps
  its zero-dependency, no-network character.
- Accounts, logins, or a hosted service with users. The moment there are user accounts there is a
  privacy policy, a password reset flow, and a bill. Discord already solved identity; the LAN
  companion doesn't need identity at all.
