# Changelog — Blood & Grit

All notable changes to the three books and the GritKeeper app, newest first. Any commit
that changes content or behavior adds an entry here — and bumps the affected component's
version — in the same commit. Version bumps are tagged `component-vX.Y` at the commit that
ships them. (Moved out of CLAUDE.md on 2026-07-18 when tracking was standardized across all
Desktop\Git repos.)

---

- **GritKeeper v1.38.0 — a soul can die now, a turn has an end, and the field says who is who
  (2026-08-11).** Four things the Keeper reported, plus the one they asked for on the Reference
  screen. Three of the four were rules the app already *printed* and did not *run*.

  **Dying, bleeding and death (Player's Book Ch. XI).** *"At 0 Blood you fall, Dying and bleeding
  — losing 1 Blood each round — until someone stabilizes you or you reach –CON, at which point you
  are dead, and out here dead is dead."* The Reference deck has carried that since v1.4 and the
  app implemented none of it: Blood clamped at zero, `Down` meant nothing beyond "at zero", nobody
  bled and nobody could die. So the moment the whole game is built around was the one moment the
  Keeper ran on paper. Now `Combatant` carries `Bleed`, `DeathAt`, `Stable` and `Upright`; the
  round takes a Blood off everyone on the ground and says whose by name; a soul reaching −CON dies
  and the app stops to say so. **Blood itself never goes negative** — every screen, save and bar in
  the app reads it as 0..max — so the ground below zero is a separate count. Grit's *refuse to
  fall* (Ch. II) is in with it, and it could not be derived: at 0 Blood `Down` is true and `CanAct`
  refuses the turn, so standing on Grit had to become a fact of its own, cleared when the round
  turns over. Stabilizing is a Fortitude save or somebody's Medicine check, both DC 15, on the
  row's right-click menu and under **✚ Restore ▾**; a critical success also brings them round on 1
  Blood. **One reading is recorded as a reading**: a blow that carries past zero keeps counting, so
  a shot taking a soul from 4 to −14 has reached −CON. The chapter only makes sense if Blood is a
  real number that goes negative, and the alternative would make a cannonball and a slap identical
  to somebody standing on 1 Blood. 74 new assertions hold all of it, including the exact boundary
  (dead **at** −CON, not one short and not one past) and that a session written before this has
  nobody dying. Deliberately **not** done: the Gut-Shot Lasting Injury's "Dying at once" is still
  the Keeper's to apply by hand.

  **The Beats are spent now.** Three Beats were counted on screen and never enforced —
  `StrikeAndApply` guarded the subtraction and not the attack, so a fourth, fifth and sixth Strike
  in one turn were free and the MAP step climbed past anything the book prints. And working a Sign
  cost nothing at all, though the app has parsed `1 Beat` off its printed cost line since v1.20.
  `Rules.CanSpendBeats` / `WhyNoBeats` answer both halves — whether, and why not — so the Strike
  and Work dialogs grey their commit button **and say which of the three reasons it is**, with the
  way out relabelled *Back to the field* and Enter following it. The refusal line is reserved
  whether or not it is speaking, because these dialogs stay open for a follow-up and a block that
  appears on the third Strike would move the buttons out from under the Keeper's hand.

  **The field's colours could not carry who was who** (user-reported: reordering the field "makes
  encountered creatures look like posse members"). Nothing was mis-decided. `PcRow` was
  (232,241,224) against a near-white `FoeRow` (250,250,247), so the whole distinction rested on
  about nine points of luminance — and then `Writable()` lifted every editable cell 42% toward
  paper, putting a posse row's Init, Blood, Beats and Conditions at (241,246,237): measurably
  **closer to the foe colour (distance 14) than the posse colour was to it (31)**. Four of a posse
  row's ten columns were, to the eye, wearing the foe's ground. The grounds are now separated by
  **cast rather than brightness** — the posse's green sits G above R, a foe's clay sits R above G —
  because lightening a pale colour drags it toward white and destroys a luminance difference while
  leaving a hue difference standing; the lift came down to 28% to match. Three new grounds go with
  the dying work: down is a quiet warm grey (nothing is happening here), dying is the loudest
  ground in the app and the only loud one, dead is ash. The first attempt made dying only a little
  deeper than down and put four near-identical pinks down one grid.

  Two things were fixed underneath it. The tracker now repaints **because the field changed**
  (`tracker.ListChanged`), not because a caller remembered — the repaint was a `Refresh()` at the
  end of `SortTracker`, one call site of several, which does nothing at all while the tab is
  hidden, and the tab is hidden on the commonest route of the lot: *Send all → Tracker* is a button
  on the **Encounter** tab. And the row's ground is read from the row's own bound item rather than
  from the list at the row's index — hardening, since the two agree today, and worth having because
  the whole fault was a row and an index being treated as the same thing.

  **The Reference deck reads like the book now.** Its prose was always Georgia, but the tables —
  most of what is on every leaf — were **Consolas**, a face drawn for reading source code, used
  nowhere else in this app or these books. At about eighty characters they also filled a little
  under half a 1,280px window. The tables are now struck in Courier New at 11.5pt and laid to the
  width actually on screen, headings and prose are up to 16.5/12.5pt, and the bar's title and count
  came off Segoe UI onto the book's own face. The columns stay monospaced and that is not a
  preference: the padding is what carries the Blood-red header band out to the right edge, and
  Georgia's 3 4 5 7 9 descend so a column of figures will not line up. Surplus width goes to the
  column carrying the rule text and **nowhere else** — the first version spread it over every
  column and put thirty-six characters under a heading reading "Degree" — capped at ninety
  characters, past which a line stops being easier to read. Checked on the seven-column Threat
  table and on Arms at both 1,040 and 1,280.

  **The Generators splitter sits against its own menu** (user-reported). Every control in that
  column is 230px wide by construction, so a fraction of the window could only ever be right at one
  size. The real fault was underneath: `Split()`'s one-shot unsubscribed on its first success, and
  for a lazily-realized tab the first `SizeChanged` arrives at whatever intermediate width the
  control passes through — the splitter was seated at 27% of about 2,700px and left there, 729px on
  a 1,264px tab. A measured splitter now keeps re-seating until the Keeper drags it themselves, and
  holds its panel's pixel width when the window is resized.

  Verified: build 0/0 under `-warnaserror`, 12,627 assertions, `--selftest` 37/37, `audit_ui.py`
  clean at 134 buttons / 121 refusal-checked handlers / **21** dialogs (the stabilize check
  registering itself) / 23 access keys, and every claim above about a colour, a width or a dialog
  was read off a rendering rather than off the source.

- **The checks moved to `audits/`, and nothing runs on a timer any more (2026-08-10).**
  Seven auditors left the repo root — `audit_ui`, `audit_ai_tells`, `audit_maps`,
  `audit_names`, `audit_whitespace`, `verify_rules`, `verify_release` — and two checks that
  existed **only as shell inside `.github/workflows/verify.yml`** became files beside them:
  `audit_idempotent_build.py` and `audit_built_matches_committed.py`. Nine files, each with a
  name, each runnable alone. `audits/README.md` says what each checks, what it costs, and
  which two are only meaningful in sequence.

  **The `books` CI job is gone.** It ran all eight on every push, and that was wrong twice
  over. It ran against half-written work: a scheduled task pushed the checked-out branch every
  30 minutes, so the red X coming back was reporting on a state nobody had claimed was
  finished. And eight checks under one job name meant any one failing read as *the books are
  broken*, while the job called `books` was also auditing the C# UI, the release tags and the
  repo's own prose. The `app` job stays automatic — compiling and running ~12,000 assertions is
  what a machine should do unasked — with triggers narrowed to `main`, pull requests and manual
  dispatch.

  The move needed a real fix, not just `git mv`. Every one of those scripts derived the repo
  root from `Path(__file__).resolve().parent`, which after the move is `audits/`, so all of them
  would have looked for the books, the C# tree and `GK/rules/Data/*.json` one level too deep —
  and `audit_maps.py` would have failed to `import module_maps` besides, because running
  `python audits/audit_maps.py` puts `audits/` first on `sys.path`. Each root is `.parent.parent`
  now and `audit_maps.py` puts the repo root on the path explicitly. Two of the nine were run to
  prove it; the rest were syntax-checked only, on purpose.

  `autosync.ps1`, `register_autosync_task.ps1` and the `BloodAndGrit AutoSync` task are deleted.
  Syncing happens at the one moment the work is declared finished: a tracked
  **`.githooks/post-merge`** hook that pushes when, and only when, a merge lands on `main`. It
  no-ops on any other branch and in any repo with no `origin`, and a failed push is not fatal —
  the merge has already happened and working offline stays legal. **Said plainly: a session
  branch now exists only on this laptop until it is merged.** That is the intent, and it is also
  the loss of an off-machine backup that nothing else replaces. `--follow-tags` carries tags
  that already exist and a tag is cut *after* the merge, so the ship loop ends
  `merge, tag, git push --follow-tags origin main`.

  One latent bug found on the way: `.gitattributes` had no rule for `.githooks/`, so
  `* text=auto` handed them CRLF on a Windows checkout. `.githooks/pre-commit` was CRLF on disk
  and worked only because Git Bash tolerates it — anywhere else that is `bad interpreter`.
  Hooks are pinned to LF.

- **GritKeeper v1.37.0 & Modules v1.1 — two adventures had the same name, and nothing was looking
  (2026-08-09).** Modules I and III shipped as *The Salt at Coffin Wells* and *The Reckoning of the
  Wells*. Every auditor in this repo reads one artifact and asks whether it is sound; none of them
  could be asked whether two artifacts are **distinct**, so the collision went out in a release.
  Module III is now **What the Water Answers**.

  The rename is the small half. The cause was the naming stock: 24 title words, 16 × 16 = 256 town
  combinations, 10 landmark owners — and the birthday bound puts the first repeat at about twenty
  draws, which is one campaign. The adventure generator was worse, because its variety was a lie of
  arithmetic: `advTitleA` × `advTitleB` is 400 combinations *in a single grammar*, so every roll
  came out "The Long Debt", "A Bad Harvest", "The Quiet Verdict". It also rolled off the ambient
  `Rules.Rng`, so a night a Keeper liked could never be found again.

  **`GK/rules/Names.cs` + `Data/names.json`** replace all of it. Two defences, because they fail
  separately: **breadth** reaches across seeds (nothing one run remembers stops two evenings drawing
  the same word — pools are now 60–79 deep and the town stock multiplies past 5,800), and **memory**
  reaches within one (a `Namer` spends every distinctive word it hands out and will not hand it out
  twice). It spends **shapes** too, which is the part that was actually broken: the two titles
  collided on the word *Wells* AND on the grammar `The <abstract> <prep> <place>`, so widening the
  word lists alone would have produced "The Ashes at Gallows Fork" beside "The Judgment of the
  Hollow" — the identical fault in a better coat. Titles now come from **21 templates**.

  **Exactly one `rng.Next` per draw**, deliberately: MapGen's landmark stream names *and* places
  from one `Random`, so a rejection-sampling loop that cost two rolls instead of one would silently
  move every rock on the sheet. The draw picks a start index and scans forward for the first unspent
  entry, which is one roll whatever it finds. `Reserve()` spends a word without consuming any
  randomness, so excluding something never shifts a seed.

  `RollAdventure(partyLevel, seed)` is reproducible whole — and was not, at first. The first cut
  seeded the namer and the monster and left twelve table reads on the ambient RNG, so a "seeded"
  adventure reproduced its title and nothing else. The smoke rig caught it, which is what it is for.
  `Db.Pick(Random, table)` exists so no generator has to reach for ambient state again. The town
  still comes off the book's own Ch. XII tables — those are a transcription and stay one — but is
  reserved into the namer, so a title can no longer echo its own town.

  Three faults in the new work, all found by tests rather than by reading: two in **`audit_names.py`
  itself** (it took the part of `<title>` *before* the em dash, which is the series name, and
  reported three confident meaningless clashes; and it read the whole document, so a stat block's
  "Attacks" and a map's "Download" counted as characters — 85 shared "names" of which six were
  names), and one in a smoke test that asserted no word may repeat anywhere on a map. That last one
  failed on hand-authored landmarks — the open range offers "Line Camp" beside "Cold Camp", and
  "Signal Hill" beside "Boot Hill". A surveyor drawing two camps has not made a mistake. **A word
  being in a draw pool is not evidence the namer drew it**, and only provenance settles it.

  **`audit_names.py`** is the standing guard: it reads all three modules and fails on a shared
  distinctive word or a shared title grammar, lists shared proper nouns for a human to judge (18
  today, all deliberate cross-references — Perdition Basin is one country), and cross-checks
  `names.json`'s `spent` list against the shipped titles so retiring a word and recording it cannot
  drift apart. Smoke coverage: pool-breadth floors, every template's slots resolving, seed
  determinism, `Reserve` costing no randomness, twelve titles off one namer sharing no word, and a
  title never echoing its town across 200 seeds. 12,549 assertions, 0 failed.

  *Maps generated before this will not reproduce* — the pools they drew from no longer exist. That
  is the price of widening them, and it is paid once.

- **Modules I–III v1.0 — three adventures, played before they were written (2026-08-09).**
  Three new books, built on the same shell as the other three: **The Salt at Coffin Wells** (four
  souls at 1st level), **A Face Not His Own** (3rd), and **The Reckoning of the Wells** (5th). Each
  is a keyed one-night adventure with a truth page, three acts, a cast built to Ch. VIII's want /
  lever / line, full stat blocks generated out of `Data/creatures.json`, and a downloadable map.

  What makes them different from an adventure somebody wrote down: **every fight in all three was
  played on the engine first.** `GK/playtest` is a fourth consumer of `BloodAndGrit.Rules` — the
  same library the app runs on — and it ran 3 adventures × 12 posses, twice over, cold and tended,
  at base seed `20260809`. `PLAYTEST.md` is the raw report and the *What the Night Costs* page in
  each module prints those numbers as numbers. They were not comfortable reading. Not one of the
  thirty-six posses finished a night standing, and the Tier III fight in every module was cleared
  zero times by shooting at it. That is now the argument each module makes: the answer to the last
  act is the creature's own **Putting It Down** line, quoted from the Bestiary rather than
  paraphrased, and each module keys the things that line asks for into the ground the posse is
  already standing on.

  The harness earned its keep twice before it produced a number worth printing. Nerve was being
  summed over standing souls only, so a bad night reported nothing lost and nobody broken at the
  same time; and every foe was focus-firing one soul, which is three Risen agreeing which of four
  to pull down — perfect coordination, not a pack. The targeting fix alone moved every fight from a
  slaughter to a fight.

  **Maps.** `module_maps.py` draws one per module from a coordinate model, the way `perdition_map.py`
  already does for the Basin, and each book carries its map inline with a download control that
  serializes the drawing on the page — so it works from a book opened off a thumb drive with no
  network. `python module_maps.py` also writes the three standalone `.svg` files.

  **`audit_maps.py`** is the new check, and it is two auditors. The engineer asks whether the map
  and the module agree: every feature carries the anchor of the scene it belongs to, every pin
  carries a scene number, and the downloadable file must be the drawing the book actually shows.
  The cartographer asks whether the drawing is a map at all — scale bar, north arrow, legend,
  nothing outside the frame, no two labels on top of each other. It found five real faults on its
  first run, including a legend standing 24px off the bottom of the sheet (invisible in a browser,
  which scales the viewBox to fit) and three colliding labels. It also found two faults in itself,
  which are written up in its own source.

- **`audit_ai_tells.py` — the dash column was measuring the wrong thing, in the wrong unit
  (2026-08-09).** Two faults, and the second hid the first. The em-dash figure was per thousand
  *characters* while the published human baseline it is read against is per thousand *words*, so
  the column ran about six times low. And `strip_html` blanked HTML entities along with the tags —
  but all six books write their dashes as `&mdash;`, so the metric had never once seen the
  punctuation it was named for. It was counting the handful of literal dashes that arrive through
  creature data and quote attributions, which is why the Bestiary read 0.7 and the Player's Book
  read 13.7 for prose written the same way by the same hand.

  Corrected, against Freeburg 2026 (3.23 per thousand words across 57k words of published human
  essays; 10.62 for GPT-4.1): the three modules read **8.6 / 9.2 / 9.4** and the three books read
  **15.2 / 16.7 / 16.6**. Two further measures joined the scan, both from the same body of work —
  punctuation variety (the share of marks that are `; : ? ! ( )`, where generated prose leans on a
  narrow inventory) and sentence-opener diversity. Burstiness and the tell scan are unchanged.

  The modules were then edited against the corrected number: about fifty em dashes became colons,
  semicolons, parentheses and full stops, which is why they now sit lowest in the repo. **The three
  books have not been touched** and are the outstanding item — they are five times the human
  baseline and half again GPT-4.1's, on the one signal current work still finds worth reading.

- **GritKeeper v1.36.0 — a button may refuse, but it may not refuse in silence (2026-08-09).**
  The Tracker's **New fight** was reported as a button that never works. It worked. It asked
  whether there were foes on the field, sign on the trail, or effects still working, found none of
  the three because the Keeper had already taken the last foe off by hand, and returned without a
  word — over a posse still Frightened, still out of Beats, still standing mid-turn. From the far
  side of the table a guard that returns quietly and a button wired to nothing look exactly alike.

  The guard was also wrong twice over, which is the older fault underneath: it asked about three
  things while the reset it protects clears nine. **`Rules.FightResidue`** is now the reset's own
  inventory — a condition, spent Beats, a MAP step, a turn in progress or already taken, the note
  of what just happened, anything still working — and both the guard and the confirmation read it,
  so the two can never again disagree about what a fight leaves behind. The pairing is now a test
  rather than a promise: every field the reset touches is proved to be one the residue test sees,
  so adding a tenth without teaching both halves fails the suite. Smoke: **12,519** assertions.

  Then the same question was asked of all 134 buttons, since one of anything is rarely one.
  **`audit_ui.py` grew a check for it** — a handler that stops over an absence and says nothing —
  and it runs in CI with the rest. Sixteen more answered to it. Six were fixed here: **Spend Grit**,
  **Mark +1** and **Taint +1** all did nothing at all when no soul was picked, and now say so;
  **zoom in**, **zoom out** and **Tracker → Map** were silent whenever no survey had been rolled
  yet, and now name that. The wheel over an empty drafting table stays quiet on purpose — a refusal
  belongs to a press, not to a scroll.

  Two things the audit itself had to learn before it could be trusted, both found by it convicting
  honest code. A guard that hands off to a method which does the talking is not silent — **Level
  up**'s `BackfillSheet` explains that a hand-entered row has no sheet, or offers to draw one up and
  takes No for an answer — so a called method is now asked the same question as the line. And asking
  a control where it is hung is structural rather than a refusal: `mapHost.Parent` is null only
  before the tab exists, which no press can reach, while `mapPanel.Model` being null means no map
  has been rolled and is precisely what a Keeper should be told. An audit that cries wolf at
  well-written code is one people stop running.

  The pre-release read then caught what no audit could, because the check asks whether a refusal
  speaks and cannot ask whether it speaks sense. **Both new sentences were strangers.** The app had
  already said *"Select a soul first."* at eight guards, and the three new ones arrived with a ninth
  wording for one refusal — so they now say what the app says, and the sentence is one constant.
  The second was worse and was not new: three Map guards had been ending **"press Survey first"**,
  and there is no Survey button on that tab. There never has been. The control that draws a survey
  is the one labelled **🎲 New map**, so for as long as those messages have existed they have sent
  Keepers hunting a control that was never there. A refusal that is confidently wrong is a worse
  failure than the silent ones this release set out to find: silence at least admits it has nothing
  to say. One sentence, one place, naming one real button.

- **GritKeeper v1.35.0 — the field acts in the order the field shows (2026-08-08).**
  A Keeper reported that combat did not follow initiative, and it did not. The tracker sorted the
  grid `Init desc → souls first → name`; `Rules.NextUp` handed out turns `Init desc → name`. The
  two agree right up until somebody ties, and on a d20 with eight on the field a tie is closer to
  certain than not. When it happened the turn jumped to a row that was not the next one down, which
  from the Keeper's chair looks like the app ignoring initiative altogether.

  Two orderings for one order is the same fault as two authorities for one number, and the rule
  this project has always applied to numbers applies here: **one source, generated outward.**
  `Rules.InTurnOrder` is now the only answer to "what order is the field in", and both the grid and
  the turn read it. Souls before foes on a tie was already what the grid showed, so nothing moved
  on screen — the turn came to match the display rather than the other way about.

  The same fault had a second half. `ArrivalInit` rolls a real initiative for anything that joins a
  fight already in progress — added deliberately so the thing that kicks the door in does not go
  last every time — and then every arrival was **appended to the bottom of the grid** anyway. It
  acted from halfway up a list that showed it at the end. Arrivals now take their seat
  (`AddToField`), and a hand-typed correction to an Init cell re-sorts instead of leaving the
  Keeper looking at a stale order.

  **`Rules.NewRound` joins `ResetForNewFight` out of the UI**, for the reason that one moved: the
  round rollover is the spine of the combat loop, and while it sat in `Tabs.cs` no test could play
  a fight through it. Three full fights now run in the smoke suite — every round asserting that the
  turns came in the order the grid was showing, that nobody took two, and that everyone left
  standing got one — alongside nine more shapes the ordinary ones never reach: a lone survivor, a
  soul downed and healed before the round ended, a field wiped inside one round, a mid-fight Init
  correction, twelve riders in heavy ties asked twice for a stable answer, effects across three
  rollovers, and something arriving after the souls above it had gone.

  The daybook now records turn handoffs — who went, on what initiative, and who was still to go —
  which is what let this be proved in the running app rather than only in the test rig: a fight
  driven through the real Tracker on the engine, its `--verbose` transcript read back against the
  grid. Smoke: 12,490 assertions, self-test 37/37.

- **GritKeeper v1.34.0 — the daybook, for the failure that never throws (2026-08-08).**
  `Program.cs` has had two tiers of failure handling for a long time, and both answer the same
  question: *it stopped*. A recoverable exception writes `%TEMP%\BloodAndGrit-last-error.txt` and
  keeps the table running; a fatal one saves the session, writes `startup-error.txt` with the
  environment beside it, and goes down honestly. Neither answers the report a table actually makes.
  **"It gave my Padre the wrong Grace." "That roll can't have been a 3." "The tracker lost
  somebody."** Nothing threw, so there is no file, and the assertions only ever catch what somebody
  thought to assert.

  **`Daybook`** (`GK/rules/Daybook.cs`) is the missing half: a capped ring of the last **400**
  things the app did, held in memory and written out only when there is a reason to. It records
  every roll with its dice and its total, every four-degrees check with the degree it came to,
  every session save and load with the counts, every mode switch, and every soul the generator
  produced *with its reckoned numbers* — the Blood, the Nerve, the faith pool — because "the wrong
  Grace" is a complaint about what came out, not about what went in.

  Three decisions worth not re-deriving:

  - **It lives in `GK/rules` but is inert until opened.** The rules library is what the smoke rig
    fuzzes — `RollExprFull` and `Generate` run thousands of times per build — and a recorder that
    was always on would build and discard a string for every one of them. `Program.cs` opens it at
    launch, so the app always records and the library stays quiet. The smoke suite asserts both
    halves of that: closed, a roll leaves nothing; open, it leaves exactly one entry.
  - **Everything fails soft.** A diagnostic that can take the table down is worse than none, so a
    mirror write that throws drops the mirror rather than surfacing, and `Save` returns false
    instead of raising. Asserted, because the whole point is the path nobody exercises.
  - **A closed daybook says "not recording" rather than printing nothing.** An empty report reads
    as *nothing happened*, when the truth is that nobody was writing it down.

  Reachable without a command line: **Help ▸ Save a diagnostic log…** writes it wherever you like,
  and both error files now carry the dump underneath the stack. `GritKeeper.exe --verbose`
  additionally mirrors every entry to `daybook.txt` beside the exe as it happens, for the fault
  that takes the process down before anything can write the ring out. Nothing leaves the machine
  unless a Keeper saves it and sends it. Smoke: 12,373 assertions, self-test 37/37.

- **Every version claim is written by one script now (2026-08-08).**
  `GritKeeper/README.md` — the README *inside the delivered zip*, the first thing anybody who
  downloads the app reads — said **v1.10.1** while the app was on v1.33.0. Twenty-three releases,
  in the open, in the one document aimed at somebody who is not the author. It also still described
  110 creatures (there are 150) and an eleven-leaf Reference deck (there are thirteen), because it
  was a frozen fork of `GK/source/README.md` that stopped being updated in July.

  The cause has the same shape as the one `verify_release.py` was written for, one level down:
  **that copy had neither a writer nor a reader.** `update_readme.py` wrote only the root README;
  `verify_release.py` checked only the root README and CLAUDE.md. A claim nothing writes and
  nothing checks is a claim that will be wrong, and the more copies of it there are, the sooner
  one of them is.

  **`update_readme.py` now writes all of them.** The root README's `AUTO:editions` block is still
  regenerated wholesale; every other claim is patched **in place inside an anchored span** listed
  in the new `CLAIMS` table — CLAUDE.md's header paragraph and its `## GritKeeper (vX)` heading,
  and both app READMEs. The anchoring is load-bearing rather than tidy: CLAUDE.md also says "as of
  Bestiary v2.0" in a sentence about how the paginator works, and that is a fact about history that
  must not be dragged forward to the current edition. Only text inside a claim span is touched, and
  the files are read and written as **bytes**, so a three-digit correction does not rewrite every
  CRLF in the repo's two largest documents.

  **`verify_release.py` now reads all of them** — both app READMEs joined its claim list — and
  `.githooks/pre-commit` re-stages all four files instead of just the one. The delivered README was
  refreshed from `GK/source/README.md`, which is the same document kept current, so the counts are
  right again as well as the number. Proved the way the other checks were: three claim sites were
  broken on purpose, in three different shapes, and the pair caught and repaired all three.

- **A version that says it shipped has to have shipped (2026-08-02).**
  v1.33.0 was built, verified against the build, the 12,359 assertions, the self-test and the wiring
  audit, merged to `main` and pushed. Then the Keeper opened the app and it was **v1.31.0**.

  Two releases had gone missing the same way. v1.32.0 was written the day before, verified the same
  four ways, merged, and entered here as a shipped release — and was never published, signed,
  packaged or tagged. v1.33.0 went the same distance and stopped in the same place. The reason
  neither was caught is that **every check this project has looks at the source**, and the thing a
  Keeper double-clicks is `GritKeeper\app\GritKeeper.exe`, which nothing but `package.ps1` ever
  writes. A build in `bin\` changes what the developer runs and nothing about what anyone else does.

  CI already had the same check for the books — `git diff --exit-code -- '*.html'` fails when a
  build script changes and the built HTML does not. The app could never have that one: its artifact
  is a 163 MB signed binary that is git-ignored on purpose, so no diff can see it. **`verify_release.py`**
  is that check, split by what is visible from where. In CI it reads only what is in git: that the
  csproj, this file's newest entry, the README and CLAUDE.md's two version lines all say the same
  number, and that **every GritKeeper version here except the newest carries a `gritkeeper-vX.Y.Z`
  tag**. That second rule is the one with teeth, because it needs no binary: the moment v1.33.0
  became the newest entry, v1.32.0 stopped being the version in progress and had to prove it was
  released. Locally, `--delivered` adds the only question that really matters — whether the exe
  behind the shortcut carries the source's version — and `.githooks/pre-push` asks it whenever
  `main` is pushed, printing the three commands that fix it.

  **Neither gate blocks anything.** The hook warns and gets out of the way, because pushing
  half-finished work is what a branch is for, and a gate people route around is the defect it was
  meant to catch. The failing check is the tag, in CI, once a version can no longer claim to be
  the one being worked on.

  It found a second gap on its first run: **v1.28.0** was never tagged either, back in July. Both
  it and v1.32.0 are now recorded in the script's `UNSHIPPED` list with the reason each never
  shipped, which is the honest way to keep a check green — the alternative being to weaken the rule
  until the history it inherited stops failing it.

- **GritKeeper v1.33.0 — the app stops borrowing Windows' clothes (2026-08-02).**
  The tabs have been painted from the frontier palette for a long time: paper grounds, blood
  headers, an owner-drawn tab strip, gold on the row a Keeper has picked. What had never been done
  is everything a tab opens onto. Windows was still drawing the title bar of every window, the face
  of every dialog button, every checkbox and radio, and the selection in every plain list — so the
  app read as a book sitting inside somebody else's utility, and the further in you went the less
  of it was yours.

  **Three weights of button, and one place each is defined.** `Btn` is the ordinary one and now
  carries a paper face with a hairline edge; `PrimaryBtn` is the single action a bar exists for;
  `QuietBtn` is a housekeeping verb that keeps its full 32px target and gives up only its ink. All
  three are one dressing routine with different colour, so the focus ring, the border and the width
  guard cannot disagree between them. The ring is drawn in Paint rather than by swapping the border
  colour, because the loud weights set their own border afterwards and the first blur would have
  reset a red-edged button to a hairline one; its ink is now chosen against the face beneath it, so
  a focused Primary or a held-down toggle shows a ring instead of dark-on-dark.

  **`FitLabel` is the guard that made the change safe.** Every width in the app had been fitted by
  eye against the themed button, and the flat one reserves less room for its text — the move clipped
  "Dread check — selected" to "Dread check —" on a bar that had looked right for a year. Widths
  hand-fitted to a renderer break when the renderer changes, so a button now measures its own
  caption and refuses to be narrower than it, on font change as well as at build: a button takes its
  real font from its parent only after it is constructed.

  **What a rule cannot cover, a walk does.** About forty-five buttons in the app were built as a
  bare `new Button` — every dialog's OK and Cancel, the wizard's Back and Next, the map's ✕ Close —
  because a dialog button carries a `DialogResult` rather than a handler and so never fitted the
  helper's shape. Rather than rewrite forty-five call sites and trust the forty-sixth to remember,
  `DressControls` walks a window when it loads and a tab when it is realized, and dresses whatever
  is still on a system style. **The predicate is also the guard against dressing twice**: it only
  touches non-Flat controls, so a die's colour and a Primary's Blood are skipped, and a tree walked
  twice costs the visit and nothing else. Between that and `Sheet` — the Form subclass that carries
  the dark title bar, which `SoulWizard` and the tour callout had both quietly declined to inherit
  — a window in this app can only come out wearing Windows' clothes if somebody deliberately builds
  it off `Form`.

  **The system accent had nine places left to sit.** `#0078D4` is the one colour here belonging to
  no palette in the app, and after the lists gave it up in v1.32.0 it still owned every checkbox and
  radio: the run-mode chooser a Keeper meets before anything else, and the Map tab's row of overlay
  toggles, where the ticks are the brightest thing on a parchment survey. They are drawn in Ink on a
  hairline box now. Gold was tried for the tick and lost — at glyph size it reads as a smudge, and a
  checkbox has one job, which is to answer yes or no from across a table.

  **The tour's three buttons were the ones that mattered most and were the last to be found.** The
  callout is a borderless patch of Paper with nothing else on it, so three grey-blue Win32 blocks
  had no chrome to blend into — and it is the first thing a new Keeper sees, since the tour offers
  itself on first run. The app's introduction to itself was the one window that did not look like
  the app. They were invisible to `audit_ui.py` because they came from a bare `new Button`, so the
  count went 131 → 134 when they were rebuilt on the shared helper and `TourBtn` was registered: a
  helper the audit does not know about is a set of buttons nobody checks.

  **The wizard's three buttons read as three of the same thing**, which the pre-release UX check
  caught by looking at them. Being a bare `new Button` apiece — they carry a DialogResult and drive
  a step machine, so they never fitted the factory's shape — the walk gave all three the ordinary
  weight, and `Next ▸`, the action that drives nine steps and the only reason the window is open,
  came out identical to the `Cancel` sitting against it that throws all nine away. That adjacency is
  the exact case `DangerBtn` was written for: *it stops looking like the button beside it, so it is
  never pressed by muscle memory.* Next now wears Blood and Cancel the pale red; ◂ Back keeps the
  ordinary face, being neither the point nor a loss. The two faces were split out of their
  factories (`PrimaryFace`/`DangerFace`, reached by `DressPrimary`/`DressDanger`) so a hand-built
  button can wear one — and they have to be applied at construction, because the walk skips anything
  already Flat and would otherwise paint a colours-only button back to the ordinary face.

  **And one thing the previous release broke by fixing something else.** v1.32.0 renamed the Posse
  tab's current/max headers from `/Max` to `/ max` so a pair would read as one field. A space is
  where a header wraps, the header band is a fixed 30px that will not grow, and all three columns
  had been rendering a lone slash with "max" sliced through the middle underneath it ever since.
  The space is now non-breaking — written as an escape, because a literal U+00A0 cannot be told from
  a space by eye — and kept in one constant the corral shares, which also puts an end to that grid
  spelling the same header two ways. **The widths that go with it are measured rather than judged**,
  and that took three tries worth recording: widening the three columns by eye cost about 2%
  everywhere else, which was enough to start clipping "Blood", "Nerve" and "Mark" — and those are
  right-aligned, so they clip on the LEFT and came back as "3lood", "Verve" and "Vlark", which reads
  as a font fault rather than as a narrow column. In Fill mode a weight is a share and not a width;
  every point given to one column is taken from the other nineteen. So each header was measured
  against the room it actually gets, the twelve points needed were taken from Notes and Scars —
  whose content is longer than any width they will ever get, so they lose characters off an already
  truncated string — and the total was left where it was, which is what stops the fix moving
  anything it was not aimed at.

- **GritKeeper v1.32.0 — four things a Keeper looked at and could not read (2026-08-01).**
  All four came in from the table, which is the only place they could have come from: every one of
  them passed the build, the 12,359 headless checks, the self-test and the wiring audit, because
  each is a fact about what the ink LOOKS like rather than about what the code does.

  **The turn glass drew its lower bulb as a box.** The heap of fallen sand took the width of its
  own top edge from its height above the floor — the glass wall measured from the wrong end — so
  the fuller it got, the narrower it drew its surface. Near the end of a turn that put the heap's
  corners out at the widest part of the bulb with its surface up at the narrow neck: the sand
  painted a rectangle across the whole lower half and the drawn glass came out inside the box.
  Both bulbs now lay out from one number, the distance the remaining sand reaches from the waist,
  so the upper band's surface and the lower heap's surface are two cuts across the glass at equal
  distances from the neck and are drawn equally wide. That mirroring earns its keep: the two areas
  sum to a constant, so the sand in the glass is conserved and the eye reads one quantity moving.
  The falling stream now lands on the heap's real surface, off the same number.

  **The glass got a switch that works both ways.** Putting it out was a button on the Tracker bar;
  putting it away was back in a menu, because the button hid itself once used. A control that
  disappears when you press it says nothing about the state it left behind. It is now a held-down
  toggle in the same place, wearing the same shape as the Map tab's ✥ Move things, and it stays in
  step with the View menu, the Table menu and the Glass ▾ menu — four routes, one state, one place
  that sets the switch.

  **A survey with a town on it carried two names and captioned neither.** The cartouche named the
  country, the label under the buildings named the settlement, and both are drawn from the same
  well of frontier words, so *Providence Township* up top and *Mule Springs* on the ground read as
  the same kind of thing. The cartouche now carries a small line above its title saying what kind
  of name it holds — *the county of*, *the territory of*, *the ground at*, *the city ward of* — and
  the settlement wears *the settlement* under its own. The caption uses the word on the checkbox
  that draws it, so the map and the control that governs it need no translating between them.

  **The emblem was too shy to see.** It is painted into whatever background a pane has left below
  its content, and it was capped at three fifths of the pane's width and refused to draw at all
  under 150px — which took a nearly empty pane in a nearly full-screen window. Now three quarters
  and 104px, so it shows up on panes that have a little room instead of a lot. **The faintness is a
  separate dial and was left exactly where it was**: 0.15 alpha is what keeps it a watermark, and
  every host paints it behind live content.

- **The prose gate moved to where a commit message can still be changed (2026-08-01).**
  `audit_ai_tells.py` has scanned the last 40 commit messages from the start, and CI runs it, so
  a bad one turned the build red. But a commit message cannot be edited without rewriting
  history, and this project's standing rule is that history on `main` is never rewritten — so that
  finding could never be cleared. A gate nobody can satisfy is a gate people learn to route
  around, which is the same defect the quoted-book-text case had this morning.

  It went wrong exactly that way: a commit message written today closed on *“A duplicate that
  nothing keeps in step is not a backup, it is a second thing to be wrong”* — the precise figure
  the audit exists to catch — and there was nothing to be done about it once it had landed.
  It was missed because the audit is always run BEFORE committing, so the one input never checked
  by the person writing it is their own message.

  **`.githooks/commit-msg`** now runs the same scan over the message while it is still a file on
  disk, and rejects a hard tell with the finding quoted back. Merges, reverts, fixups and squashes
  are skipped (generated or conventional, not authored prose), a missing Python or missing audit
  fails open, and `--no-verify` still gets through when you mean it. Proved against all three
  cases: the figure is rejected, a plain message passes, a merge is skipped.

  Findings in messages that have already landed are now **reported and not counted**, in their own
  section, for the same reason quoted book text is. Files stay fatal — files can be edited.
  Install once per clone: `git config core.hooksPath .githooks`.

- **GritKeeper v1.31.0 — the table stops living beside the exe (2026-08-01, user-requested).**
  The ask was to reach the release build locally without going to GitHub for it — and Tidewatch
  already worked that way.
  It does, and this is why: Tidewatch keeps its state in `%APPDATA%\Tidewatch`, so republishing
  over its exe can never disturb anything. GritKeeper wrote beside its own exe, so the folder
  holding the release build was also the folder holding the campaign, and the two jobs fought.

  **`AppState.Dir` resolves the folder now** instead of assuming it, in three steps: a
  `portable.txt` beside the exe wins (an explicit "keep my things here", for a copy carried on a
  stick to somebody else's table); failing that, an existing `session.json` beside the exe is
  honoured, because nobody gets moved off a folder they are already using; otherwise
  **`%APPDATA%\GritKeeper\`**, which no build, publish or package step can reach. The four files
  that belong to a Keeper move with it — `session.json`, `prefs.json`, `session-backup.json`,
  `session-unreadable.json`. `startup-error.txt` and `selftest-report.txt` stay beside the exe,
  because a crash report has to land somewhere findable when the profile is the thing that is
  broken, and the `Data/` lookup stays too — it is a read, and the smoke rig depends on it.

  **The single-file promise is untouched.** The exe still needs nothing beside it, and rule 1
  means it can still be carried on a stick with its campaign. What changed is where a plain
  double-click keeps things.

  Consequences worth having: **`GritKeeperpp\GritKeeper.exe` is now a safe thing to play
  from** — which is what was wanted, since `package.ps1` refreshes it on every release — and the
  set-aside added earlier today becomes belt-and-braces rather than the only thing between a
  Keeper and a lost table.

  `--selftest` now points the state at a scratch folder before anything reads it. Each of its
  three `MainForm` instances runs `TryAutoLoad` in its constructor, which on an unparseable file
  MOVES it to `session-unreadable.json` — against a real folder that is a self-test rearranging
  somebody's table. It also makes the run hermetic: what the self-test does no longer depends on
  what happens to be saved on the machine running it.

  `AppState.Resolve` is a pure function in the rules library and the smoke suite walks all four
  combinations of its two inputs, because this decides whether a campaign is found or silently
  abandoned on a first run. Both branches were also proved live: a launch with no marker wrote
  `prefs.json` and a 25,894-byte `session.json` into `%APPDATA%\GritKeeper` and left the exe's
  folder holding nothing but the exe; a launch from a folder carrying `portable.txt` wrote both
  beside the exe and left the per-user copy untouched to the second.

- **`package.ps1` sets the runtime files aside instead of deleting them (2026-08-01,
  after it cost a Keeper their table).** No version bump — the app is untouched at v1.30.0;
  this is the release tooling.

  Step 1 of the packager copies the signed exe into `GritKeeper\app\` and then clears
  `session.json`, `prefs.json`, `startup-error.txt` and `selftest-report.txt` out of it. That
  intent is right and is unchanged: those files belong to whichever machine last ran the app,
  and v1.20.1 proved what happens when one ships — it went out carrying the packager's own
  `prefs.json` with `"Remember": true`, so every download launched into someone else's table
  and never saw the run-mode chooser.

  The **method** was wrong. It was `Remove-Item`, which does not use the Recycle Bin, and
  GritKeeper stages its saves to `session.json.new` and moves them rather than keeping a `.bak`
  the way Tidewatch does. So for anyone who plays out of `GritKeeper\app\` — which is the
  obvious thing to do, the exe is right there — the first release anyone packages takes their
  table with it, silently, with no way back. That is not hypothetical: it happened on
  2026-08-01, packaging v1.30.0 into that folder minutes after the app had autosaved into it on
  close. Nothing recovered it; there are no shadow copies and no File History on this machine.

  The files are **moved** now, to `.package-aside\<yyyy-mm-dd_HHmmss>\`, and the script says so
  by name as it goes. `GritKeeper\app\` still ends up holding the exe and nothing else, so the
  zip is unchanged and no runtime file can ship. `.package-aside/` is git-ignored.

  Proved rather than assumed: a decoy `session.json` and `prefs.json` were put in
  `GritKeeper\app\`, the packager was run, and afterwards the folder held only the exe while
  both files sat intact under `.package-aside\` — the decoy's contents read back byte-for-byte.

  **And the real fix is not in the script.** A separate play folder at `Desktop\GritKeeper\` was
  the first attempt, and it was the wrong shape: within hours it was a 156 MB duplicate sitting a
  version behind, because nothing kept it current. v1.31.0 later that day did it properly by moving
  the state out of the exe's folder entirely, which makes `GritKeeper\app\GritKeeper.exe` safe to
  play from — one copy, refreshed by the release it came from. The duplicate was deleted and a
  1 KB Desktop shortcut points at the real one.

- **GritKeeper v1.30.0 — a soul you can describe, a glass you can find, a map that fills the
  screen, and four things that only go wrong in month six (2026-07-31, user-requested).**

  Four asks and one standing instruction: *fix what will show up after six months of sessions
  without intervention.* The four are features; the fifth found more than the four did.

  - **"Write it down" writes it down where a Keeper reads it.** A scar always went onto the soul —
    the Posse tab's Scars column — and the button says the words the Session tab's *Keeper's
    ledger* is for. It now stamps a dated line there too, and the Ledger sheet carries a **What
    They Carry** box, so the answer to "did that get recorded" is visible in three places instead
    of one narrow column. Behind it, a worse thing: **the Posse tab and the Tracker were two
    implementations of the Dread Check and they disagreed about the rule.** The Posse tab rolled
    its own ladder and **doubled the Nerve on a critical failure**, which Ch. XII does not say
    ("loses the listed Nerve and imposes Frightened 1 at once"); it also never hung the Frightened,
    never rolled the Affliction a DC-25 failure carries, and never touched the break table — so
    the same horror cost twice the Nerve and left no mark on one tab and did the book's arithmetic
    on the other. One road now (`ResolveDread`), and the **Tier spinner is gone**: two boxes for
    one row of one table meant DC 25 beside Tier 2 took 1d4 for a truth that unmakes a world.
    The DC is asked for and the ladder is *derived* and shown beside it.
  - **The turn glass can be found.** It is off by default and, when off, the whole column hides —
    so the only route to turning it on was a menu called **Table**, which is not where anybody
    looks for a clock. There is now a **＋ Turn glass** button on the Tracker's own bar, visible
    exactly when the glass is not, and a **View** menu entry. All three call the one method.
  - **The map goes full screen** — a **◈ Full screen** button and a double-click on open country;
    Esc, F11 or ✕ brings it back. It **reparents the real controls** rather than building a second
    bar, so every ground, scale, hour, weather, overlay, marker and export control is the same
    object it was on the tab and the two can never disagree. Double-click is ignored over anything
    draggable, so it never takes the map away mid-drag.
  - **A soul you can describe** (new: `GK/rules/Look.cs`, `Data/appearance.json`). Physical
    traits, dress and the one detail a witness names first — 28 peoples of the 1880s West, 19
    whole styles of dress, and pools for build, bearing, face, marks, voice, hair and wear. Shown
    on the **Ledger sheet**, printed on the text sheet and the PDF, editable field by field in
    **✎ Tweak**, rolled from the New Soul tab, the wizard, and the Posse tab's right-click menu.
    Two decisions carry it: the draws are **conditioned, not shuffled** — colouring comes out of
    one people's own lists and every garment out of one style's wardrobe, because six independent
    lists give you a Norwegian in a charro jacket — and **nothing here is worth a point.** It
    touches no number and gates nothing; the books' line about the peoples of the West holds, that
    they appear as people, described and never costed. The very first soul it drew on screen was
    "Rafferty Luján, Chinese, out of Guangdong", so **the name and the people are now one
    decision**: the look is drawn first and the name follows it, and 600 generated souls assert it.

  **And the six-month sweep — four faults that a day's testing cannot find.**

  - **The session was thrown away when the posse was empty.** Launch asked "is the Party empty?"
    and, if it was, seeded the demo posse and **never applied the loaded session at all** — so a
    table whose posse the Keeper had cleared (an all-NPC night, a party wiped and not yet rebuilt)
    came back next launch with its written ledger, its clocks, its rides, its map markers and its
    tracker gone, and autosaved that loss over the file on the way out. `GameSession.IsUntouched`
    now asks the whole question, in the rules library so the smoke rig holds it.
  - **The session could stop saving and say nothing.** `AutoSave` swallowed every failure, which
    is right — it must never block closing — and then kept quiet about it, so a `session.json`
    unwritable since March (a sync client holding it, a read-only folder, a full disk) looked
    exactly like one saving perfectly, while File ▸ Save session said "Session saved." on top of
    it. It now reports whether it landed, says why once per new reason, and says so again when it
    recovers.
  - **Two native font leaks on the hottest paths.** A `Font` holds a GDI handle. The Dice tab's
    result card minted a new headline font on **every roll**, and the Bestiary's creature renderer
    about **thirty per creature** — so arrowing down the list of 150 spends four and a half
    thousand handles in seconds. Nothing disposed them; the finalizer gets there eventually, which
    is why an hour of testing looks clean and a long evening does not. One shared shelf
    (`MainForm.Face`) now hands out the few dozen the app actually uses.
  - **A blank Map tab, forever.** Reparenting is unwound in a `finally`, because that failure
    arrives with nothing to read: an empty Map tab that stays empty until the app is restarted,
    with the survey still parented to a window that has gone. `--selftest` walks the round trip.

  Build 0/0, smoke green, `--selftest` 37/37, `audit_ui.py` clean at 132 buttons / 20 dialogs /
  22 access keys.

- **Books v2.25 / v2.12 / v2.11 · GritKeeper v1.29.2 — the antithesis stopped being a habit, and
  the tracker's readouts caught up with the tracker (2026-07-30, user-requested).**

  A third pass at the one figure that keeps coming back: negative parallelism, the antithesis
  that denies one thing in order to assert another. Earlier passes (v2.15/v2.7/v2.7, then v2.23)
  each thinned it and each left the shape intact enough to regrow. This one took the count in the
  books from eighteen to seven.

  - **Eleven rewritten, seven kept.** Density was never the problem — eighteen across ~138,000
    words is roughly 1.3 per ten thousand. Monotony was: one figure carrying the weight in
    fourteen places reads as a formula whoever wrote it. The eleven were varied into direct
    assertion, subordination, and inversion, and in five of them the negative half turned out to
    be doing nothing that the positive half wasn't already doing, so it simply went. Diction and
    meaning are untouched; the architecture of the sentence is the only thing that moved.
  - **The seven kept, and why.** Four earn the figure — the horse and the line between a journey
    and a death, the occupied country between the last church and the first ocean, the tables as
    an oracle, the Bruja and the beliefs people actually hold. The other three were already ruled
    on and recorded: the two Bestiary flagships kept at v2.7 and the Sign-Rank antithesis kept at
    v2.23. **A decision already made and written down is not re-litigated by a later pass** — that
    is what writing it down was for.
  - **Two more found by hand.** `audit_ai_tells.py` flags the figure one line at a time, so it had
    nothing to say about two paragraphs that carried a *second* instance a sentence away from a
    flagged one — the Iron Code opener in Ch. XI and the safe-table paragraph in the Keeper's
    Ch. IV. A pair inside one paragraph is the monotony the whole pass is about, so both were
    varied too. Worth remembering: the audit measures per line and the tell lives per paragraph.
  - **The app followed the books, as it must.** Three creature entries changed lore text
    (Plague-Dead, the Sermon Made Flesh, the Longhorn Herd), so `Data/creatures.json` was
    re-extracted with `extract_creatures.py` and diffed first — exactly three entries moved, all
    150 present. Status-bar and `GK/source/README.md` book strings follow to v2.25 / v2.12 / v2.11.

  **The tracker's readouts, and one refresh instead of eighteen.** The round box and the hourglass
  face would sit on a stale number while the grid beside them was current, and the two faults had
  one cause: refreshing was written per site, as `trkGrid?.Refresh(); UpdateTurnLine();` copied to
  eighteen call sites. `ShowRound` documents itself as the one place the round moves through, and
  most of those sites never called it — so the round box updated only where somebody had remembered
  it. There is now a single `RefreshTracker()` that redraws the grid, the round, the turn line and
  the glass face together, and every one of those sites calls it. The bug class goes with the
  duplication: a readout added tomorrow is refreshed by the ten existing callers for free.

  **Choosing a turn length turns the glass over.** Picking "three minutes" from the drop-down set
  the preference and left the sand where it was, so the glass went on draining against the old
  length until somebody reset it by hand. `SetTurnLength` now resets the clock — and restores
  `Running` afterwards, because `Reset()` clears it, which is how a running glass used to stop dead
  the moment the Keeper adjusted the length mid-fight.

  **The glass is where a glass should be, and big enough to read across a table.** It sat inline in
  the tracker's button bar at 30×40, small enough to be ornamental. It now holds its own column at
  the far right of the bar, about 100×150, with the m:ss face and the length menu stacked beside it.
  `HourglassView` needed no change to grow: its geometry was already written as fractions of its own
  bounds. Verified by rendering it, per the project's own "look at it" standard — a TableLayoutPanel
  arrangement is the same landmine class as `SplitContainer`, and a clean build proves nothing here.

  **`audit_ui.py` grew the checks a UI reviewer would ask for.** Three, taken from the accessibility
  and Windows-UX guidance that is actually standardized rather than folklore: **target size**, at
  the 24px floor where WCAG 2.5.8 (AA) and Microsoft's own control guidance agree; **destructive
  actions are recoverable**, satisfied either by a `Confirm()` or by editing one of the six lists
  that `ListChanged += CaptureUndo` puts on the undo stack — an undoable action does not need a
  prompt, and a prompt on every one of them trains a Keeper to click through the one that matters;
  and **no two items in a menu claim the same Alt key**, which Windows resolves by quietly demoting
  the key from "activate" to "cycle", so a learned shortcut stops working and nothing says why. All
  three pass today, which makes them regression guards — so each was proved against a synthetic
  source file first, and each fired exactly once. Now covering 128 buttons, 19 modal dialogs and 21
  access keys.

  **Dead code now fails the build.** An analyzer sweep over both app projects, and what it found is
  the argument for keeping it on: a tracker sort mode the Keeper picks that was stored and never
  read back, a Ledger font minted at every zoom step and never drawn with, and a null check on the
  result of `new`. All three compiled clean and read as live code. Also a real leak — `LedgerView`
  re-mints its thirteen fonts whenever the zoom changes and stranded the previous set every time;
  they are pooled and disposed now, and on the control's own `Dispose` as well. Six doc comments
  were malformed in ways that silently did nothing: two `///` blocks on local functions (which
  cannot carry XML docs at all), a bare `&` inside XML, an unresolvable `cref`, three missing
  `<param>` tags, and the Nerve method's documentation sitting three methods above the method it
  describes. `GK/.editorconfig` plus `EnforceCodeStyleInBuild` makes all of it a build error under
  `-warnaserror` from here on; the guard was proved by planting an unused member and watching the
  build fail. One wrinkle worth recording: IDE0005 refuses to report unless the build generates XML
  docs and says so as its own error, so doc generation is on in every configuration and excluded
  from publish output — a Debug-only first attempt broke the Release build on the demand itself.

  Verified: all three books measure clean (200 / 101 / 166 pages, desktop-mobile parity, zero
  true-scale clip, zero mobile h-scroll, every TOC and index anchor resolved), builds idempotent,
  inline JS parses under `node --check`, `verify_rules.py` 697 cross-checks with zero drift, app
  build 0 warnings / 0 errors under `-warnaserror`, smoke 12,249 passed / 0 failed, `--selftest`
  36/36, `audit_ui.py` clean, PDFs regenerated and verified at 612×792pt with page count matching
  sheet count.

- **GritKeeper v1.29.1 — the release carries its own license, and the repository says what it
  is (2026-07-29).**

  No change to the app itself: the exe is functionally identical to v1.29.0 and the version moves
  only so the shipped archive can be told apart from the one before it. Everything here is about
  what leaves the building.

  - **The zip ships `LICENSE` and `NOTICE`.** It carries ~26,000 lines of source and, until now,
    nothing at all saying what anyone was allowed to do with them. **An unlicensed archive is worse
    than an unlicensed repository**, because the archive is the thing that leaves the site and it
    takes no context with it — no README, no repo page, no license tab. `package.ps1` copies both
    files in and its pre-upload check now asserts their presence, so a later release cannot quietly
    drop them. 29 entries → 31.
  - **The project is licensed: CC BY-NC-SA 4.0**, over the game and the app alike (user's choice,
    including the NonCommercial term). `LICENSE` is the verbatim legal code as published by Creative
    Commons — downloaded rather than written out, because a legal document recited approximately is
    worse than none — and `NOTICE` carries the plain-language summary, which parts of the repository
    fall on the game side and which on the software side, and the Pathfinder 2E lineage note.
    Recorded plainly in both: NonCommercial makes this **source-available, not open source** as the
    OSI defines it, since every OSI-approved license permits commercial use. Note that GitHub's
    sidebar will read "Other" for this and there is no fixing it — its detector uses
    choosealicense.com's set, which deliberately excludes the NC variants. Our `LICENSE` is
    byte-identical to the canonical text (438 of 438 lines); the label is GitHub's policy, not a
    defect.
  - **The repository stopped calling itself an HTML project.** GitHub computes its language bar from
    *bytes*, and the three **built** book files are 1.46 MB of them — so the bar read "HTML 42%" over
    ~16,000 lines of C# and ~10,000 of Python. A new `.gitattributes` marks them, the PDFs and the
    `GritKeeper/` mirror as `linguist-generated`, which is a statement of fact (nothing hand-edits
    them) and collapses half-megabyte artifacts in diffs as a bonus. Result: HTML gone, Python 50.7%,
    C# 48.8%.
  - **Line endings are declared.** There was no `.gitattributes` at all, so whether a file landed LF
    or CRLF depended on the machine that cloned it — the source of the "LF will be replaced by CRLF"
    warning on nearly every commit. `*.sh` is pinned to LF, which is correctness rather than
    cosmetics: a CRLF shebang fails on Debian with "bad interpreter". Applied across all four
    `Desktop\Git` repos.
  - **A CI workflow** (`.github/workflows/verify.yml`) running the checks this project already had
    and nobody could see: the build with warnings-as-errors, the ~12,000-assertion logic suite, the
    self-test in all three run modes, **a publish of the self-contained single file and a self-test
    of that** — the one failure a dev build cannot show, since `Db.ReadData` resolves embedded
    resources off `typeof(Db).Assembly` — plus the 697 cross-checks, the UI audit, an idempotent-build
    check and a check that the committed HTML matches a fresh build. The Playwright page-geometry
    tools are deliberately excluded: pagination is environment-dependent by design, so a cloud runner
    would measure a different page count and fail for no useful reason.
  - **`audit_ai_tells.py`** — the reads-like-a-person standard, which the books have always had,
    extended to the repository's own prose. Burstiness plus a scan for generated cadences. The docs
    came back clean (README 0.85 · CLAUDE.md 0.79 · CHANGELOG 0.80 · commit messages 0.63, against
    0.55+ for human-like). Three defects in its first version are recorded in CLAUDE.md, because each
    made the tool lie — most importantly that it **excused quoted spans as "somebody else's
    cadence"**, which was circular: what these docs quote is the books, written by the same hand.
    Removing that excuse and pointing the scan at the books found **eighteen negative-parallelism
    constructions** it had been waving through. Those are book content and are fixed in the next
    release, at source in the build scripts.
  - **Repository presentation:** descriptions filled where empty, topics added, and the README now
    explains that `autosync(session/…): <timestamp>` commits are a scheduled 30-minute backup rather
    than hand-authored history.
  - Verified: build 0/0 with `-warnaserror` · smoke **12,248 passed, 0 failed** · self-test 36/36 on
    the published single file · `audit_ui.py` 127 buttons and 18 dialogs clean · `verify_rules.py`
    697 cross-checks, 0 drift · zip 31 entries, signed and timestamped. No book content changed.

- **GritKeeper v1.29.0 — what a Sign actually does, what a wound leaves behind, and a glass
  on the table (2026-07-29).**

  The largest release since the app got its Tracker. Four strands: the Signs and Miracles
  system learned to describe itself, wounds and fright now leave a permanent mark on a soul,
  every control in the app says what it is (checked, not intended), and the Tracker can put a
  turn timer in front of the posse.

  - **Creature Tiers in the Encounter and Tracker pickers** (user-asked). Every line in the
    type-ahead now reads `The Wendigo  ·  Tier IV  ·  The Old Dark`, owner-drawn through one
    shared `CreatureLine`/`CreaturePicker` so the two bars can't disagree. The Tier is the whole
    basis of the budget math and of the safe-table rule, and it was the one thing the picker
    didn't show.
  - **The working model — what a Sign, a Miracle or a creature's power DOES** (user-asked; the
    old model held one shape and eighty hand-written workings do not have one shape).
    `Rules.Working` now carries a `WorkShape` (Self · OneCreature · Ally · Area · Place ·
    Counter · **Trait** · Unclear), a `WorkEnds` (Instant · Rounds · NextTurn · Scene · Hour ·
    Day · UntilDawn · UntilEnded), damage, ongoing, healing, Nerve, a save-for-half, whether it
    drains the worker, and its Backlash — all read out of the book's own printed text by
    `Rules.ReadWorking`, so nothing is transcribed twice.
    - The reader was tuned **empirically, not by assertion**: all 80 workings and 150 creature
      powers were dumped and read by hand until nothing came back `Unclear`, and the dump was
      then converted into permanent assertions and deleted. Dice are claimed in the order
      Nerve → Heal → Ongoing → Damage, and the damage verb list deliberately has no bare
      "for", because "Treat a wound for 1d8" was scoring as both damage and healing.
    - `WorkShape.Trait` came out of the data: **zero** of the 150 creature `special` lines carry
      dice, a save or a radius, so the old dialog's "on whom, for how many rounds" was a
      category error for every one of them.
    - `HasBacklash` is split from `BacklashBites` — four of the forty Signs print a Backlash of
      "None", *Salt & Iron*'s being "None. This is the kindest Sign in the book, and the weakest."
    - The Work dialog reshapes itself to the working: targets appear only where there is a
      target, the duration picker offers what the text actually says, and the Backlash is
      printed in Blood ink where it can't be missed.
  - **Wounds and fright leave a mark.** A hit that takes half a soul's Blood or lands as a crit
    is **grievous** (`Rules.IsGrievous`) and offers a Fortitude save at DC 15 against a **Lasting
    Injury**; a critically failed Dread Check now rolls the Keeper's Book Ch. III **d10 of
    Afflictions**. Both land on the sheet as `Scar`s, shown on the Posse grid with ✚ and ☾ marks
    and a hover for the whole list. The Afflictions table is `Rules.Afflictions` — an earlier
    draft of this invented its own list of suggestions while the book already had a d10, which
    is exactly the single-source violation this project keeps closing.
  - **Initiative is a Notice check** (Player's Book Ch. XI). The Tracker rolled a bare d20 for
    everyone while the app's own Reference deck printed the rule. `Rules.RollInitiative` adds the
    bonus and floors the result at 1, because a rolled 0 is indistinguishable from "not rolled".
  - **The turn hourglass** (user-asked), on the Tracker, **opt-in and off by default**. An
    owner-drawn glass whose sand really falls — the level drops by √time so the *area* the eye
    reads falls off linearly — beside an m:ss face and a Glass ▾ menu. A posse's turn defaults to
    **five minutes** (ten is one click away, any length from five seconds to an hour is allowed),
    the top of each round turns it over, and the length lives in `prefs.json` because it is a
    house rule about how this table plays, not state belonging to one fight. **It never acts on
    the game**: it logs and turns red, and does not end a turn or take a Beat, because nothing in
    the books says a slow player loses their action. The clock itself (`TurnClock`) is pure and in
    the rules library, so the smoke rig runs a five-minute turn in a millisecond.
  - **Every control says what it is — and it is now a failing check.** `--selftest` walks all ten
    realized tabs and every step of the wizard for **all seventeen Callings**, and fails on any
    interactive control with no tooltip. It found 13 silent controls on the tabs and, in the
    wizard, something reading the source would not have caught: **all five list boxes had no
    resting tooltip at all** — `ItemTips` only spoke once the pointer was already on a row, and
    cleared itself over the blank ground below the last one. So the two lists that silently
    *refuse* a click (past the trained-skill cap, past what the coin covers) never said why.
    Lists now carry their own instructions, with a row's tip laid over them.
  - **Every modal dialog answers Esc.** Four had drifted into wiring `AcceptButton` and leaving
    `CancelButton` unset — including **Strike and Dread**, the two a Keeper opens most in a fight.
    A modal that ignores Esc reads as a hung window. `audit_ui.py` now checks all 18 of them.
    Where cancelling is meaningless (the die prompt, the run-mode chooser) Esc does what the title
    bar's ✕ already did. The Level-up dialog's buttons were also the one pair in the app laid out
    Cancel-first; they now read `[Level up] [Cancel]` like everything else.
  - **Contrast and accents** (user-asked). The **selected tab was near-invisible** — under the
    Windows visual style it differed from the other nine by a couple of pixels of height. The
    strip is now owner-drawn: the live tab stands on Paper under a 3px Blood rule with its name in
    bold Blood, the rest sit back on a darker ground. Grid lines and the alternating row stripe
    were both a shade off Paper (the stripe differed by four points of blue); both are now
    visible. Blood bars went from 150 to 190 alpha. Two palette entries were added for contrast
    rather than meaning — `GoldDeep` (~5:1 on Paper, for the explanatory paragraphs that were set
    in Gold at ~3.5:1) and `Faint` — and the ⧖ glyph was dropped because it is not in the font
    and rendered as "≥".
  - **Reference deck knows its audience.** Two leaves are the Keeper's alone; a player's screen is
    now the shorter deck, asserted from both ends so a filter that stopped filtering fails the
    build rather than looking like nothing at all.
  - **Minimum system requirements** (user-asked), the way a PC-game box carried them —
    Help ▸ What it needs to run — plus a sweep for promises the app cannot keep. The books are
    PDFs, not a phone app, and the roll log does not keep everything forever.
  - **A first-run walkthrough with an opt-out** (user-asked): 14 tooltip callouts that follow the
    feature they describe, mode-aware, Esc-closable from either window, offered once.
  - **Tracker fixes** a player would have hit: a guarded `CellEndEdit`, Delete clearing Conditions,
    the posse mirror finding its soul by id, and `→ Tracker` from the Ledger going through the same
    path as every other route onto the field.
  - Verified: build 0 warnings / 0 errors · smoke **12,248 passed, 0 failed** · self-test 36/36 ·
    `audit_ui.py` 127 buttons and 18 dialogs, no findings · `verify_rules.py` 697 cross-checks, no
    drift. **No book content changed, so no book version moved and no PDF was regenerated.**

- **GritKeeper v1.28.0 — the rules are their own library now (2026-07-28).**

  A structural change with **no behavior change**: the game and the Windows UI became two
  projects instead of one. Nothing a Keeper can see moved; the exe is still a single
  self-contained file and still holds all its data inside itself.

  - **`GK/rules/BloodAndGrit.Rules.csproj`** — a plain `net8.0` class library, no WinForms
    reference at all, holding the six headless files (`Core.cs`, `CharGen.cs`, `IronCode.cs`,
    `Horror.cs`, `MapGen.cs`, `Pdf.cs`) and the five `Data/*.json`. `GK/source` is now the
    WinForms app on top of it; both it and `GK/smoke` reach it by `<ProjectReference>`.
  - **Why now, and why it was worth doing on its own merits.** `smoke.csproj` carried a
    hand-listed `<Compile Include="..\source\Foo.cs" />` for each of the six — a list that
    could silently fall out of step with what the app actually contained. Add a seventh
    headless file, forget to list it, and it went untested forever with nothing to say so.
    A project reference cannot drift that way. It also makes "the rules are one thing, the UI
    is another" structural rather than a convention, which is the discipline this project
    already insists on for every number it prints.
  - **The data had to move with `Core.cs`, and that is forced, not stylistic.** `Db.ReadData`
    resolves embedded resources off `typeof(Db).Assembly`. Leave the JSON embedded in the app
    while `Db` lives in the library and the lookup finds nothing, then falls back to a `Data/`
    folder on disk that a standalone exe does not have — a failure that would appear only in
    the published build, never in a dev run. The JSON is embedded in the library instead, and
    the comment in `Core.cs` now says which assembly pins it.
  - **The smoke rig no longer copies `Data/*.json` beside its binary.** It doesn't need to:
    the assembly it now loads carries them. `CharGen.FlavorList` stays `internal` and the rig
    still reaches it, via `<InternalsVisibleTo Include="smoke" />` — the flavor-pool depth
    floors were worth keeping and were not worth widening the API for.
  - **`package.ps1` mirrors both trees, as siblings** (`source/` and `rules/`), because the
    app's project reference points at `..\rules\` — flatten either and the delivered source
    stops building. Its zip check now asserts `rules/Core.cs`,
    `rules/Data/creatures.json` and the library csproj are present, not the old
    `source/Core.cs`. `verify_rules.py` reads `GK/rules/Data/chargen.json`.
  - **Verified:** library builds 0/0 on `net8.0` with no WinForms; app builds 0/0; smoke
    **12,144 passed, 0 failed**; `dotnet publish` still yields one 155 MB self-contained exe;
    that exe's `--selftest` passes 20/20, which is the real proof the embedded JSON still
    resolves once the library is bundled inside the single file; `verify_rules.py` 697
    cross-checks, 0 drift.
  - **What this unblocks** (see `DESIGN-online-play.md`): a rules engine that runs on Linux,
    which every rung of the Discord/online-play ladder needs before it needs anything else.
    Still not built, and this commit takes no position on whether it should be.

- **GritKeeper v1.27.0 — the Ledger's figures, the wizard's tooltips, and buying more than one
  (2026-07-27, all three user-reported).**

  - **The Ledger's type is fixed, and the cause was the font, not the layout.** Three faults, one
    screenshot: the subtitle read "A Reckoning of **OneSoul**", Speed read "**3o ft**", and a long
    name was cut off mid-word. Each was measured before it was fixed, with a side-by-side render.
    - *The collapsed word space* was `TextRenderingHint.AntiAliasGridFit`. Hinting rounds every
      glyph advance to a whole pixel, and at 9.5pt Georgia italic that rounds the word space away
      entirely; at 14pt it doesn't, which is why it looked intermittent. The sheet now paints under
      plain `AntiAlias`, and `PerformLayoutPass` measures under the same hint — measuring under one
      and painting under another is how a scroll height comes to disagree with the ink.
    - *The "3o"* is Georgia doing exactly what it was designed to do: it is a **text-figure** face,
      so 3 4 5 7 9 hang below the baseline and 0 1 2 sit at x-height. Beautiful in a sentence,
      unreadable in a stat column. GDI+ can't ask a font for its lining-figure set, so the figures
      are now set in `NumFace` — the first installed serif that has lining figures (Cambria,
      else Palatino Linotype, else Times New Roman, else Georgia). **Prose keeps Georgia**: text
      figures inside running text are correct typography and match the printed book. The line is
      drawn at the stat boxes, the ability boxes and the Mark, which is where figures are read off
      and compared.
    - *The cut-off name* was a one-step shrink-to-fit that could still overflow, after which the
      next box simply painted over the tail — so the text looked truncated by nothing. `FieldBox`
      now steps down through all three cuts and, failing that, trims with an ellipsis inside a
      bounding rectangle, so a value can never leave its own box. **Labels got the same treatment**
      (found by rendering the fix: "BLOOD / MAX" was running under Defense), and give up a word
      before they give up their size — "BLOOD", not "BLOOD /…".
  - **The soul wizard explains itself.** Every control and every list row now carries a tooltip,
    built out of the same `chargen.json` the sheet is built from, so a tip can't drift from the
    rule it describes: what each of the six abilities actually buys, what a Calling's die and saves
    and Sign-working mean, an Origin's boon and burden, a skill's ability and what training buys,
    an Edge's effect *and its requirements* (which the detail line never showed), a Sign's Rank,
    cost and effect, what each of the Four Questions is asking for. `ItemTips` gives a `ListBox` or
    `CheckedListBox` per-row tips, which WinForms has none of.
  - **You can buy more than one of a thing.** The general store was a plain checklist — one
    lantern, one box of cartridges, one pistol, ever. Highlight a line and set the number; the
    label, the price and the coin follow. Asking for more than the coin covers **walks the number
    back to what it covers** rather than refusing. The count is carried as repeated entries, so
    `Validate`'s coin ledger — which already priced gear by counting — keeps its single authority
    over the arithmetic and needed no change; the only rule edit was dropping the guard that
    refused an item already owned. `CharGen.Tally` is the one place that turns those entries back
    into lines ("Lantern × 3"), shared by the Ledger, the text sheet and the printed sheet.
    A second suit of armor is bought and paid for, and worn once — asserted.
  - **The store list stopped stuttering.** Several Ch. X price-list keys carry the price inside the
    name, which read "Cow pony ($25) — $25" and would have read worse with a count beside it. The
    key is still what the rules look the item up by; only the shown name loses the parenthetical.
  - **Verification.** Smoke suite **12,147 passing, 0 failing** (new: quantity reaches the sheet,
    the coin ledger still balances at every count, armor DR doesn't stack, `Tally` ordering and
    counting). Self-test **20/20** — including a new GUI check, in the `BuildReferenceTab` mould,
    that **builds all nine wizard steps** for a Gunhand, Hexer, Preacher and Witch, which between
    them reach every optional page. Wizard pages are realized lazily, so a step that throws on
    construction was previously only findable by a person clicking Next. The Ledger fixes were
    confirmed by rendering the real control at 540px and 900px and looking at it.

- **GritKeeper v1.26.0 — the Generators roll a whole adventure, not one more line (2026-07-27,
  user-requested, "expand it enough so that there are a wide variety").** Every other button in
  that column rolls one line off one table and leaves the joining to the Keeper. This one rolls
  the joins as well.

  - **An adventure, whole.** One click gives a titled scenario: the *shape* of the trouble (a hunt,
    a siege, a haunting, a quarantine, a bargain, a drowning…), how it *finds* the posse, the town
    and what ails it, what they're saying, **the trouble itself**, the truth underneath, the turn
    that lands when the table thinks it has the shape of it, an omen to open on, whoever stands in
    the way, what happens if nobody moves — and what's in it.
  - **The trouble is a real creature, not an adjective.** It comes out of the Bestiary at the
    posse's own tier ±1, so what gets rolled is a thing with a stat block that can go straight onto
    the Tracker. Set the party level on the tab and the weight class follows; leave it at zero and
    the whole Bestiary is in play.
  - **The truth is rolled apart from the monster, which is where the variety actually lives.** A
    Wendigo that *is collecting, and there is a list* is not the Wendigo that *only takes what is
    freely given* — same stat block, different session. Eight new tables, **156 entries**, and the
    independently-rolled parts alone give a bit over **49 million** combinations before the town,
    the face, the omen and 150-odd creatures multiply it again.
  - **It hands the pieces to the app rather than leaving them in a text box.** *→ Thread* puts
    "if nobody moves" on the Ledger as a running clock at the size it rolled (4, 6 or 8 segments —
    the sizes the app actually draws). *→ Map* surveys its town, either as streets or set down in
    open country, using the v1.25.0 menu. A scenario the Keeper has to retype at midnight is a
    scenario they won't use.
  - **Caught by reading the output rather than by a green tick:** the tell was being fitted into a
    sentence — "you'll notice they *wears* something of the child's". The table is written in bare
    third person, so any pronoun in front of it disagrees with the verb. It gets its own labelled
    line now. The suite also carried a hard-coded "17 simple tables" canary, which the eight new
    tables tripped; it says 25 and explains itself.
  - 29 new assertions, 12,102 → **12,131** — including that 400 consecutive rolls come back
    near-all distinct, and that the trouble suits the posse at every level from 1 to 10.

- **GritKeeper v1.25.0 — a rolled place can be surveyed twice: itself, and the country it stands
  in (2026-07-27, user-requested).** The Generators tab could already send a town or a city to the
  Map. It could only ever send it *one way*, and for a city that way was wrong.

  - **A city could only be drawn as a ward.** `SendPlaceToMap` forced The Lamplit City at block
    scale for anything rolled as a city, so the map you got was avenues and a depot. There was no
    way at all to ask the other question — *what is around it, and how far* — which is the only
    question a posse riding toward a city actually has. A town, meanwhile, inherited whatever
    ground happened to be set on the Map tab, which is to say it was luck.
  - **Both scales, for both kinds of place.** The two → Map buttons are drop-downs now. **The town
    itself / the ward itself** draws the place you walk — streets, blocks, the depot. **In its
    country** shrinks the whole settlement to one mark on open ground a day's ride across, and you
    can either roll the ground or name it: the open range, rivers and swamps, graveyards, mines,
    the high country, the badlands, the Old Places. Same rolled name on both, so the town in the
    desert and the streets of that town are recognizably the same place.
  - **The list of countries is derived, not typed.** `MapGen.SettingTerrains` is `Terrains` minus
    The Lamplit City — which is not ground you stand a town on; it *is* the town, at another
    scale. A country added to the Grounds later is offered as a setting without anyone remembering
    this list exists.
  - **Put where the tests can reach it,** on the lesson v1.24.2 paid for: the derivation lives in
    `MapGen.cs`, which the smoke suite compiles. Thirteen new assertions, and they check the thing
    that matters rather than the plumbing — every one of the eight settings really does draw a
    *named settlement* at county scale, and the ward still fills its sheet. 12,089 → **12,102**.

- **GritKeeper v1.24.2 — New fight actually starts a new fight (2026-07-27, user-reported:
  "I don't think the 'new fight' button is working in the tracking").** It was working, in the
  sense that the handler ran. It just no longer did what its name promised, and the audit that
  followed turned up four more of the same shape.

  - **The bug.** `NewFight()` was written before this session added the sign strip and Worked
    effects, and nothing went back to teach it about them. It cleared the foes out of `tracker`
    and stopped there — so every sign stayed on the trail and every Sign and Miracle stayed
    working on the survivors, straight into the next fight. On a field holding sign but no foes
    in the flesh it took the "no foes to clear" branch and did nothing whatsoever, which is
    exactly what a dead button looks like. `Clear field` had the identical hole.
  - **A whole class, not one button.** The pattern is *state added late that the older reset
    paths never learned about*, so the sweep went looking for the rest of it. `RollInitiative()`
    predates `HasActed` and never reset it, so spent-turn greying and the gold acting row
    survived into a freshly rolled order — the field showed souls as already done on a round that
    had not begun.
  - **Two things called "threads".** The sign strip went in this session labelled **THREADS ON
    THE TRAIL**, while the Ledger tab has had a "Threads && clocks" group with its own **Clear
    threads** button all along. Two unrelated features, one word, and a Keeper reaching for
    "Clear threads" to clear the trail. The strip is **SIGN ON THE TRAIL** now, and the internals
    (`signPanel`, `RefreshSigns`, `SignCard`) match.
  - **The release was going to ship mislabelled.** `AppVersion` was a hand-typed constant that
    had reached `1.24.1` while `<Version>` in the csproj sat four releases back at **1.20.1** —
    and `package.ps1` names the release tag from the built exe's `FileVersion`. A release cut
    from that tree would have published as `gritkeeper-v1.20.1`, over a tag that already exists.
    `AppVersion` is now read off the assembly, so the csproj is the only place a version lives.
  - **Why no test caught it.** `NewFight()` lives in `Tabs.cs`, which is not in `smoke.csproj` —
    it was UI code no assertion could reach. The per-survivor reset is now
    `Rules.ResetForNewFight()` in `Core.cs`, where the suite holds it to its word: conditions
    wiped, Beats back to 3, nobody mid-turn, **nothing still working** — and Blood deliberately
    *not* healed, because wounds carry between fights and Rest is what mends them. Eleven new
    assertions, 12,078 → **12,089**.

- **Repo cleanup — the spent release notes (2026-07-27, user-requested).** Seven
  `RELEASE_NOTES_vX.Y.Z.md` files (v1.16.2 through v1.20.1) had collected at the repo root. Each
  was written to be pasted into a GitHub Release, and each was — verified before deleting: every
  one of the seven matches the body of its published Release exactly. So the file was a third
  copy of text that already lives in two better places, the Release and this changelog, and the
  third copy is the one that drifts.

  - **The rule already existed; the notes just weren't covered by it.** CLAUDE.md has said since
    v1.16.2 that the zip, the `app/` exe and the `source/` mirror are git-ignored release assets,
    never committed. The notes file is the same kind of thing and was the only one being
    committed. `.gitignore` now carries `RELEASE_NOTES_v*.md`, and CLAUDE.md says so.
  - **Nothing was lost.** The text is on all seven Releases, the history is here, and the files
    remain in git history. Write the next one, paste it, leave it on disk.
  - **`package.ps1` stopped naming a stale file.** Its help text told you to paste
    `RELEASE_NOTES_v1.16.2.md` — frozen at whatever version was current when the line was
    written, four versions before the last one that used it. It says `vX.Y.Z` now, matching the
    line the script already generates at the end of a run.

- **GritKeeper v1.24.1 — the bar is grouped, and the grid says what you may type in (2026-07-26,
  user-requested).** The last two items off the UX pass.

  - **The action bar reads as a sentence now.** It was thirteen buttons of identical weight in no
    useful order. Hairline separators (`BarSep()`) group it: *the turn* — ▶ Next turn · Begin turn ·
    Next round — then *resolving* (Strike · Dread · ✦ Work), then *adjusting* (Amt · Damage · Heal),
    then Restore; and on the second row, ordering and filling the field.
  - **Destructive actions stopped looking like their neighbours.** ✕ Remove, New fight and Clear
    field sat immediately beside ＋ Foe and ＋ Add, identical in every respect, so the only thing
    standing between "add a combatant" and "wipe the battlefield" was aim. They now sit after a
    wider gap and wear `DangerBtn` — paler ground, Blood-red text. Not hidden and not shouted; just
    no longer reachable by muscle memory.
  - **A genuine trap found on the way: `Btn` is `FlatStyle.System`,** which hands painting to the
    theme and **silently ignores `BackColor` and `FlatAppearance`**. The v1.23.0 accent on ▶ Next
    turn was therefore doing nothing — what looked like emphasis in the screenshots was the focus
    ring, since the button had just been invoked. `PrimaryBtn` and `DangerBtn` switch to
    `FlatStyle.Flat`, which is the only way to actually colour a WinForms button, and Next turn is
    now genuinely the one weighted control on the bar.
  - **The grid says which columns you can type in.** Four of the Tracker's ten are editable and
    nothing distinguished them, so the only way to find out was to try. Editable columns carry **✎**
    in the header, their tooltips say so, and their cells stand on ground lifted 42% toward paper by
    `Writable(color)` — applied *after* the row colour, so it lifts posse green, foe rust, acting
    gold or down red rather than flattening the meaning those already carry. Column widths grew to
    fit the marker; "Beats ✎" does not fit the 44 that plain "Beats" did, and a clipped header is
    worse than no marker. Deliberately Tracker-only: every column on the Posse grid is editable, so
    marking all eighteen would be noise rather than information.
  - No logic changed; smoke holds at 12,077 passing, 0 failing. Verified by rendering.

- **GritKeeper v1.24.0 — a soul's gender is a box you can write in, and it says so (2026-07-26,
  user-requested).** Asked for a custom option alongside Woman and Man.

  - **It was already free text — nothing ever said so.** Both gender pickers (the wizard's step 1 and
    the ✎ hand-tweak sheet) were `ComboBoxStyle.DropDown`, so anything typed was accepted and stored.
    But the list offered two items and no hint, so in practice the app offered two choices. The list
    now reads **Woman · Man · Other…**, where *Other…* is a prompt rather than a value: picking it
    clears the box and hands over the caret. `CharGen.CleanGender` guarantees the prompt itself can
    never be stored as an answer, and both read sites go through it.
  - **One picker, built one way.** `MainForm.GenderBox` replaces the two hand-rolled combos, so the
    choices, the tooltip and the clearing behaviour cannot drift apart between the wizard and the
    tweak sheet.
  - **A real bug behind it: a custom gender drew a man's name.** `CharGen.FullName` chose its
    whole-name pool with `gender == "Woman" ? fullNamesWomen : fullNamesMen`, so *every* gender that
    was not exactly "Woman" fell down the men's branch — a soul whose player wrote their own gender
    got a man's whole name roughly one time in eight. It now draws from **both** pools in that case,
    matching what `GivenFor` already did correctly with the given-name lists. Woman and Man keep
    their own pools exactly as before.
  - **Smoke: 12,084 passing, 0 failing.** A custom gender is proved to reach both whole-name pools
    over 1,200 draws while a woman still never draws a man-only whole name; the prompt is proved
    unstorable; and a hand-built soul is proved to carry a written-in gender through `Assemble` onto
    a `Validate`-clean sheet.
  - Note: `CharGen.Generate` still rolls Woman or Man for a randomly dealt soul, which is what the
    name lists are written for. Writing your own is a choice made about a particular soul, not
    something to roll.

- **GritKeeper v1.23.0 — the combat loop becomes one action, and the round keeps itself (2026-07-26,
  user-requested).** The ask was that the Tracker's combat feel as intuitive as it can, and that the
  round be kept automatically with the Keeper still able to edit it. The bar had thirteen buttons of
  identical weight, and the two or three pressed every single turn looked exactly like *Clear field*.

  - **▶ Next turn** — one action for the whole loop. It hands the turn to whoever is up next by
    initiative and, when the field has all gone, **rolls the round over and starts the next one**, so
    the round is a consequence of play rather than a button the Keeper must remember. Ctrl+Space, and
    the only accented button on the bar: the loop should look like the loop. It carries the grid
    selection with it, so Strike, Dread and ✦ Work act on whoever is up without hunting for the row.
    *Begin turn* stays for handing the turn out of order, and now says so.
  - **The round is a spinner, not a label.** The app keeps it; the Keeper can reach in and correct it
    when the table has got ahead. (This also retires the last of the hard-coded "Round 1" string.)
  - **Who has already gone is visible.** Rows that have taken their turn fade; the turn line counts
    what is left ("· 2 still to go"). Turn order stops being something held in the head and lost
    track of on round four — recognition instead of recall.
  - **`Rules.NextUp` / `CanAct` / `RoundSpent`** carry the logic as pure functions over
    `Combatant.HasActed` (persisted, so a fight reloaded mid-round resumes mid-round). Someone
    bleeding out is skipped rather than holding the round open forever; a trace is never up whatever
    its initiative; an all-down or empty field is not a round ending over and over; and initiative
    ties break by name so the same field always yields the same order.
  - **"clean" now says which rule it is.** A Keeper asked what the word meant in the Next-strike
    column. It is the Player's Book's own — Ch. IX: *"Your first Strike in a turn is clean"* — but the
    column never named the rule, so there was nothing to look up. The header reads **Next strike
    (MAP)** and the tooltip cites the chapter and the whole ladder.
  - **Grid headers stop flashing Windows blue.** A header whose column held the current cell painted
    in the system selection colour — the one colour in the app belonging to no palette here, moving
    around the header row as the selection did. Fixed in `StyleGrid`, so every grid gets it.
  - **Smoke: 12,066 passing, 0 failing.** The turn order is proved end to end: first up, each in
    sequence, the round spent only when everyone who could act has, clearing it puts everyone back,
    the downed skipped, traces excluded, ties stable, and `HasActed` surviving save and load.

- **GritKeeper v1.22.0 — Signs, Miracles and creature powers tracked where they land (2026-07-26,
  user-requested).** The books have carried two power systems since the beginning — Signs (Ch. XIII)
  and Miracles (Ch. VI), on a shared five-Rank spine — and the app knew them only well enough to put
  them on a character sheet. Nothing tracked one once it was worked. The request was for **cause and
  effect, on the part of both posse members and creatures**, and this is that.

  - **The effect rides on whoever it landed on.** `Combatant.Worked` holds a list of `WorkedEffect` —
    name, kind, rank, **who worked it**, the printed cost, what it does, the rounds left, and the
    round it started. The question a Keeper asks mid-fight is "what is on *him*?", so that is where
    the answer lives; the cause travels inside the effect rather than being left to memory. They
    paint as chips in a new **Worked** column — **✦** Sign, **✝** Miracle, **◈** a creature's own —
    with the rounds left in brackets. The chips are deliberately terse; the whole of each effect is
    a hover away, and endable from the row's right-click menu, one at a time or all at once.
  - **A soul offers only what they have learned.** The picker reads `SignsKnown` / `MiraclesKnown`
    off the sheet and resolves each against the data for its rank, cost and text — a Gunhand offers
    nothing but a hand-named effect, and says so. **A creature offers the power its own stat block
    names**: `Rules.ParsePower` splits the Bestiary `special` line, every one of the 150 of which is
    written "Short name. What it does."
  - **The cost is real.** `Rules.ParseCost` takes the printed line apart — "1 Beat · 2 Nerve · Will
    save" → the action, the Nerve, the Faith, the Blood, the Mark, the save, and the single "or 6
    Blood" alternative the book offers in one place — so working a Sign spends Nerve and working a
    Miracle spends the Calling's pool, off the worker's own sheet. It **asks before overspending
    rather than refusing**: the Keeper may be running something the pools do not model, and the
    book's numbers are theirs to overrule.
  - **Rounds tick, and say so.** `Next round` counts every timed effect down and logs each one that
    runs out **by name and by who worked it** — an effect that vanished off a chip silently is one
    the table keeps playing anyway. `RoundsLeft = -1` means "until it is ended", which is what the
    book's "for a scene", "for an hour" and "for the next day" actually are; those never expire on
    their own, and the Keeper ends them by hand.
  - **Smoke: 12,046 passing, 0 failing** (from 11,332). The two parsers are held against the real
    data rather than samples: **every one of the 40 Signs and 40 Miracles** must name its action,
    must not be paid in the other side's currency, and must sit on the five-Rank spine; **every one
    of the 150 creatures** must yield a named power short enough to be a chip and keep its effect
    text. Plus the hand-checked cost shapes ("and" charges both, "or" charges the first and remembers
    the way out, an unparseable line keeps its words rather than throwing), the effect clock
    (counting down, expiring, open-ended ones never expiring), and a session round-trip proving an
    effect survives save and load with its cause and cost intact.
  - Verified by rendering and by driving it: the demo posse's Hexer offered her two real Signs with
    the parsed cost and her live Nerve beside it, working one put the chip on her row, spent 1 Nerve
    (17 → 16), and the effect came back off disk with its source, cost and starting round. One
    layout clip caught and fixed in the duration note.

- **GritKeeper v1.21.0 — the safe-table rule becomes a thing you can run, and the field says what
  just happened (2026-07-26, user-requested).** v1.20.0 put the Sign & Spoor rule in the books. This
  puts it in the app's hands, and then — on the user's word that it still did not read as intuitive —
  moves it out of the place it did not belong.

  - **Threads on the trail, not rows on the field.** A sign first arrived as a row in the initiative
    order with no Blood, no turn, and Init 0. It worked, and it was wrong: a line in a list of things
    that take turns, which could never take one, is a line a Keeper learns to skip past. Signs now
    live in `GameSession.Signs` and draw in their own **THREADS ON THE TRAIL** strip above the grid —
    one card each, carrying the name, what is on the ground, the Tier, the Survival and Dread DCs,
    the clock, and its own **Read it ▸**. The strip hides itself outright when the trail is clear, so
    a table that never meets the rule never sees it. Sessions saved with traces inside `Tracker`
    migrate across on load.
  - **The clock says "2 of 4".** Four small boxes told nobody anything — reported by the user as
    exactly that. The boxes remain, and the count beside them is now the part that does the teaching,
    with the strip's own caption saying what the whole band is for: *too far over the posse to meet
    in the flesh. Read them; they take no turn.*
  - **The rule's entry dialog names where the thing goes.** It offered "Sign & spoor" against "In
    the flesh" and left the Keeper to work out what either did. It now sets out both outcomes under
    headings — **ON THE TRAIL (what the book does)** and **ON THE FIELD (overrule the rule)** — each
    saying where the creature lands, what reading it costs, and, for the overrule, the Blood and
    Defense it brings and that at this level it is very likely a funeral. The buttons say **Put it on
    the trail** / **Put it on the field**.
  - **`Rules.PartyTier`** extracted from inside `Cost`, so "three Tiers over a posse of level 2" is
    the same arithmetic in the dialog as in the encounter budget rather than a second copy of
    `(level + 1) / 2`.
  - **A thread whose creature no longer resolves says so.** The lookup falls back to Tier I — the
    gentlest row on the table — and left unsaid that reads as a real reading. A re-extraction that
    renames a creature can orphan a saved thread, so the card now names the missing creature instead.
  - **In the fight itself:** a **Blood bar** behind every Blood number (green above two thirds, gold,
    red below a third), a **"Last"** column saying what just happened to each row — the damage, the
    healing, the moment they went down — coloured by direction and cleared at the top of each round,
    and **✚ Restore ▾** for the selected soul, the posse, or everyone on the field. Every route to a
    wound now goes through one `Combatant.Wound`, including the Strike engine, so an engine-resolved
    hit and a hand-typed one leave the same visible answer.
  - **Generators → Map.** A rolled town or city ward can be sent straight to the Map tab to be
    surveyed under its own name (`MapSpec.PlaceName`); the naming roll is still made, so naming a
    place never rearranges the country under it.
  - **Four stale facts fixed.** `AppVersion` had read **1.17.0** since v1.17 — the About box has been
    lying about the version for four releases. The same box carried hard-typed book editions (v2.15 /
    v2.7 / v2.7, nine editions behind) a foot away from the three constants the status bar reads
    correctly; it now interpolates them, so it cannot drift again. `GK/source/README.md` claimed app
    1.11.0 and books v2.16/v2.8/v2.8. And the Tracker's round label was built with the literal text
    "Round 1": the tab is lazy, so a session auto-loaded mid-fight set `round` before the label
    existed, and the label was the only thing in the app still saying Round 1 on the fight's third.
  - **Smoke: 11,329 passing, 0 failing** (from ~10,390). New: `SignOnly` agreeing with `Cost` across
    every Tier × level, `PartyTier`'s whole ladder, `ReadSign` across every Tier × d20 face with a
    monotonicity sweep on the Survival bonus, the sign half of `Combatant` (clock clamping, no
    wounding a trace, `Down` never true for one), `Wound`'s notes and clamps, and **`CharGen.SkillBonus`
    against every skill in the data** — the number that prefills every sign reading, which had none.
  - Verified by rendering: the strip, both cards, the entry dialog, and the read dialog captured with
    `PrintWindow` and looked at; migration proved by loading a session with a trace in the old place
    and one in the new.

- **GritKeeper v1.20.1 — two stale facts fixed at the source rather than in the text (2026-07-26,
  user-requested).** Both were noted at the end of the last release; both are the kind that come
  back unless the thing that generates them changes.

  - **The app told Keepers its reference screen held eleven leaves.** It has held thirteen since
    v1.17.0 — Miracles and Running in Town were added and the prose describing the deck was not.
    The count is now derived from `RefLeafTitles`, the one list the deck is built from, and every
    mention interpolates it: the five-minute lesson, the README, the handoff doc. Adding a leaf
    updates the prose by construction. `--selftest` builds the deck on purpose and checks every
    title has a renderer beside it — **16/16 checks now, up from 13**.
  - **The zip was shipping the packager's own `prefs.json`.** Found immediately after release, by
    the zip-contents check added below — the very first in-place package it ran on. `package.ps1`
    stripped the runtime `session.json` from `app/` and had never stripped `prefs.json`, so the
    v1.20.1 asset carried `{"Mode": "KeeperDice", "Remember": true}`: every download would have
    launched straight into someone else's run mode and never seen the chooser. The script now
    clears every file the app writes beside itself, and **refuses to declare a zip ready if
    `app/` holds anything but the exe**. The asset was rebuilt and re-uploaded; the exe itself is
    byte-identical, so the version stands.
  - **A stale `GK/source/sign.ps1`** (19 July) sat beside the root `sign.ps1` that supersedes it
    (24 July, and the one the release flow documents), and shipped in every source bundle. Two
    signing scripts, one of them out of date, is a trap. Removed — it is in git history at
    `2e09118` if it is ever wanted.
  - **`package.ps1` died on a file lock when GritKeeper was running from the delivered folder.**
    It failed twice this session, two thirds of the way through a release, as a raw `Copy-Item`
    access error naming no cause. It now looks for the process first, names it with its pid and
    start time, and builds the zip from a staging tree so the release is unaffected — leaving the
    running instance alone and saying plainly that `GritKeeper\app` stays on its old build until
    it's closed. It also verifies the zip carries the exe, the README, and the source before
    declaring itself ready, and prints the exact `gh release create` line for the version it just
    packaged.

- **Player's Book v2.24 · Keeper's Book v2.11 · Bestiary v2.10 · GritKeeper v1.20.0 — sign and
  spoor, and a wording pass (2026-07-26, user-requested).**

  - **The safe-table rule is a rule now, not a sentence.** It said a horror two or more Tiers over
    the posse "arrives as sign and spoor, not in the flesh" and stopped there — which told a Keeper
    what not to run and left them to invent the scene. The Bestiary's Grounds appendix gains a
    **Sign &amp; Spoor** section that runs it: what the words mean, a Survival DC to read the trace
    by the thing's Tier (12 at I up to 20 at V), a Dread Check **one rung below meeting the thing**
    (nothing at Tier I — out here a cougar kills a calf), what is left on the ground at each Tier,
    what each of the four degrees actually buys a tracker, and the **four-segment clock** that turns
    the monster into a thread.
  - **"Spoor" is finally defined.** It appeared in three books and the app without ever being
    glossed. Spoor is the physical trace — track, scat, hair on wire, blood, a scrape on a tree at a
    height that ends the conversation; sign is everything wider. Defined in the Player's Book under
    Reading the country, in the Keeper's Book, and in the Bestiary.
  - **The Keeper's Book never mentioned the rule at all** — the one chapter a Keeper reads to learn
    how to build a fight. Ch. IV now carries **The Safe-Table Rule**, with the numbers and a
    Keeper's-eye note on why it is a pacing tool rather than a restriction.
  - **In the app:** a new **Safe-Table Rule — Sign &amp; Spoor** block on the Reference deck's Long
    Odds leaf, rendered from `Rules.SpoorRow` so it cannot drift from the books; and rolling a ground
    on the Generators tab now prints the whole scene — the trace, the Survival DC, the Dread Check,
    the clock — instead of only flagging that the rule applies. Backed by `Rules.SpoorRow` /
    `SpoorRead` / `SpoorClockSegments`, with the "one rung below" claim asserted against the book's
    own Threat-by-Tier Dread DCs.
  - **A wording pass over everything, and it found the fault in the app rather than the books.**
    Every marker for machine-written prose was measured across all three books: negative
    parallelism, stock vocabulary, conversational filler, rhetorical shapes, hedging density, triad
    density, and sentence-length variance. The books came back clean — burstiness 0.91–1.52 against
    a generated-text threshold near 0.45, hedging under 1.4 per thousand words, and zero hits on
    every filler pattern. The **app-side table entries** were another matter: measured against the
    book's own entries they ran 21–88% longer, every one of them, with single-clause entries
    collapsing from 75% to 25%. Each carried a trailing clause explaining what it had already
    implied. **129 entries rewritten** to the book's economy across all thirteen prose tables.

  Smoke suite **10,418 assertions, all green**; books measure clean (200 / 101 / 166 pages, page
  parity, zero true-scale clipping, zero mobile h-scroll, every anchor resolving); whitespace audit
  shows no mid-flow gaps; PDFs regenerated and verified.

- **GritKeeper v1.19.1 — the last of the generators, and a repo/doc audit (2026-07-26,
  user-requested).**

  - **The city roller was the thinnest table set in the app** and the only one with no app-side
    additions at all: 12,000 combinations against the town roller's million. Doubled every one of
    its four tables — quarters (the brewery caves, the medical college, the freight tunnels), who
    really runs it (the waterworks board, the undertakers' trust, the coroner), its wrong note,
    and work for a posse. **192,000 combinations.**
  - **The chargen flavor pools grew too** — a soul's vice 20 → 32, what they lost 16 → 28, what
    they've seen 16 → 28, what moves them 16 → 28, and 12 more given names on each side. These
    are what a soul reads like on the Ledger, and they were repeating over a long campaign.
  - **Depth floors on every generator table and flavor pool**, asserted. `tables_extra.json` is
    merged on top of the book's `tables.json`; if a re-extraction ever landed without it the app
    would still boot and still roll, just from a much thinner deck and without saying so. Now
    that fails the smoke suite instead. Likewise a new assertion that **every creature in the
    Bestiary is reachable from some terrain table** — bar the White Bison, held back on purpose.
  - **Repo audit.** Deleted a stale `GK/publish/GritKeeper.exe` (155 MB, 22 July, in a path the
    release flow no longer uses) and five Jul-12 `BloodAndGritKeeper.*` files under the old
    assembly name — the ones that made a stale v1.2.2 binary look like the app hanging. Deleted
    `origin/session/2026-07-24-code-review`, fully merged and never cleaned up.
  - **CLAUDE.md corrected on five counts** it had drifted on: the app section still said v1.11.0;
    the build block still said `dotnet publish -c Release -o publish`, which is precisely what
    diverted the v1.18.0 release into signing the previous version's exe; the deliverable was
    listed at ~69 MB when compression is deliberately off and it is ~155 MB; the smoke count was
    four releases stale; and it claimed three separate times that the 18 removed Player plates
    were "still in `assets/`" and recoverable. They are not, and git has never tracked them.
    The blind-build caveat is gone as well — the app runs here, and the two bugs this release
    fixed were both invisible to assertions and obvious on sight.

  Smoke suite **10,391 assertions, all green** (the total drifts by a few dozen run to run —
  several sweeps assert once per random draw — so the number that matters is the zero).

- **GritKeeper v1.19.0 — weather and real country on the maps, and a turn you can see
  (2026-07-26, user-requested).**

  - **The maps have landforms now.** The country used to be hills, mesas and the odd snowy peak.
    A survey can now say *mountains here, a bluff along there, timber the whole north half*:
    mountains, whole ranges, ridges, bluffs and escarpments, buttes, hoodoos, hardwood forests and
    pine stands, marsh, orchards, springs. Each ground draws its own furniture, weighted so a
    county reads as country with a shape to it rather than one of everything scattered evenly.
  - **And each ground names its own places.** The high country offers The Divide, Lonesome Peak,
    The Palisades, Devil's Backbone, The Pinery; the badlands offer Chimney Butte, The Goblins,
    The Wall, The Tanks; the river bottoms offer The Sloughs and The Landing. Every ground has
    six to nine of its own on top of the ones people build anywhere. A place that comes already
    named is left alone by the name decorator, which is what used to produce "The Crooked The
    Wall" and "Pryor's The Spine".
  - **Weather.** Fair, sunny and hot, overcast, rain, thunderstorm, fog, wind and blowing dust,
    snow, a blizzard, hail, hard freeze — each inked over the survey with its own wash and marks,
    named in the cartouche and in the roll log. Left on **as the sky wills**, the country rolls
    what it would actually get: the high country hands you a blizzard, the badlands never will.
    Drawn from its own random stream, so forcing the sky does not move one rock — asserted.
  - **Begin turn does something you can see.** It always worked; nothing on screen said so. The
    acting combatant's row now lights gold and bold, a **Next strike** column shows what the next
    one costs (clean, then −5, then −10), and a line beside the round reads *"Ruth is up — 3 Beats
    left, next Strike clean."* Next round clears it, because a new round is nobody's turn yet.
  - **The Strike dialog stopped cutting itself off.** Its prose changes with the run mode and with
    whether a creature or a soul is swinging, and the fixed heights it was laid out with clipped
    the last line — and the Beats count off the right edge, which is exactly the readout a Keeper
    needs. Everything is now measured and sized to its own words at any DPI. Also fixed a stray
    comma in dice-and-books mode, and a font leaked on every open.
  - **Undo and Redo look like buttons.** They were always in the status bar, live on every tab,
    but flat text there reads as a caption (user-reported). They now wear a raised face and a
    border. Ctrl+Z / Ctrl+Y and **Edit ▸ Undo/Redo** are unchanged.
  - **Bigger tables everywhere else.** Rumors 44 → 56, trail days and nights 30 → 40 each, plunder
    30 → 40, omens 42 → 52, what ails a town and what it hides 20 → 28 each, NPC wants and tells
    20 → 28 each, given names and surnames up by 12 apiece. The town roller now has over a million
    combinations and the face roller nearly four. Every creature in the Bestiary except the White
    Bison — which stays off on purpose, per its Ch. XII "gone quiet" rumor — is now on a terrain
    table: twenty that no table cited, including the whole of Ch. IX's hard men and hard country.
  - Also: the cartouche is sized to fit its subtitle as well as its title, and weather ink is
    started far enough in that no stroke lands past the neatline.

  Smoke suite **10,372 assertions, all green** (+~250 this release); self-test 13/13; the button
  audit reports 118 buttons, every one with a handler and a tooltip.

- **GritKeeper v1.18.0 — what the posse rides, a right-click on everything, and marker colors
  that are the Keeper's own (2026-07-25, user-requested).** A session's worth of table feedback:

  - **Mounts and vehicles are tracked.** The Posse tab gained a lower pane — *the corral & the
    yard* — for what the posse rides, drives, or takes passage on: saddle horses, mules, the
    stagecoach, freight and buckboard wagons, a ferry, a sternwheeler, the cars. Each carries its
    own Blood, Defense, Speed, and capacity, takes a rider or a driver from the posse, can be hurt
    and mended, and goes to the combat tracker like anything else that can be shot at. New
    `Data/rides.json` roster and `Ride` model; a wrecked wagon or a downed horse reads red at a
    glance, the same as the tracker.
  - **Every list answers a right-click.** The posse, the corral, the tracker, the encounter plan,
    the Bestiary, and the roll log now offer the actions available for the row under the cursor —
    the same operations as the buttons above them, calling the same handlers, so the two can never
    drift into disagreement. The row is selected before the menu draws, so what you point at is
    what the app acts on. Three posse-bar handlers were pulled out of button lambdas into methods
    for exactly that reason, and the Bestiary gained *copy the stat block as text*.
  - **Marker colors on the trail map.** Four riders all drawn the same verdigris are four dots the
    table argues about. A single marker can now take a color of its own (right-click it), and a
    whole kind — the posse, NPCs, creatures — can be re-inked for good from **Marker colors ▾**;
    the standing choice is kept in `prefs.json`, a marker's own choice travels in the session file.
    Ten-color palette plus a mixer.
  - **Markers can be exported, or not — your call.** A saved SVG or PDF used to be the survey
    alone, silently: markers were screen-only and nothing said so. There is now a **with markers**
    box beside the save buttons (off by default — a map for the players shouldn't show them where
    the ambush is), and the log says either way which one you got.
  - **A latent map bug, fixed.** `OnWater` measured to the river's *vertices* rather than its
    channel, so a spot mid-stream on a long straight reach was called dry. It only ever worked
    because callers passed a pad wider than the vertex spacing. Now true point-to-segment distance,
    with a regression test that fails under the old code.
  - Also: naming a new ride took the lowest free number instead of a count (selling the middle
    horse of three no longer mints a duplicate); a `ContextMenuStrip`+`Font` leak on every
    right-click across five sites; the budget bar is double-buffered; `Prefs.Save` reads before it
    writes, so setting the run mode can't drop preferences it doesn't know about.

  Smoke suite **10,113 assertions, all green** (+~140 this release); self-test 13/13; the button
  audit reports 118 buttons, every one with a handler and a tooltip.

- **GritKeeper v1.17.0 — creatures fight with their own attacks, cities read right, and three
  ways to run the table (2026-07-25, user-requested).** Three changes, all from table feedback:

  - **The Bestiary's attacks reach combat.** Before, a creature dropped onto the tracker could
    only Strike with the *posse's* weapons — a ghoul shooting a revolver. Now the Strike dialog
    reads the creature's own free-text `attacks` line into structured attacks (name, built-in
    to-hit, damage, damage type, and the rider effect) and Strikes with **those** through the same
    Iron Code engine the guns use: a ghoul claws at +6 (1d8+3), a fiery touch types as fire so
    worn-armor DR doesn't stop it, and the creature's special maneuvers and auras are surfaced in
    the dialog for the Keeper to narrate. New pure parser `CreatureAttack.Parse` (paren-aware
    clause splitting, tolerant of trailing riders); ~40 new smoke assertions across all 150
    creatures. A stat audit confirmed the numbers were already tier-true — the gap was the app
    ignoring them, not thin stat blocks.
  - **City maps stop fighting themselves.** On a ward map, rivers and lakes were drawn first and
    then paved over by building blocks (blue scraps between roofs), and structures could land in
    the water because the water keep-out was being cleared. Now a city leaves the waterway open
    (no block is raised in it), redraws the water **over** the block layer so it reads as one
    course, keeps depots and landmarks out of it, and **labels** the scattered works (*works,
    depot, pens, chapel, landing*) so it's plain what each mark is.
  - **A mode chooser at launch.** GritKeeper now asks how you're running the table — **Player's
    table** (a player's pared-down view), **Keeper with dice & books** (you roll, the app referees
    and keeps the ledger), or **Keeper on the engine** (the app rolls everything, for dice-free
    play anywhere). Changeable any time from the **Table** menu; the choice is remembered. The
    Strike and Dread dialogs take the die you rolled in dice-and-books mode and roll it themselves
    on the engine. Self-test now constructs the UI in all three modes: **13/13 checks passed.**

  Also fixed a long-standing stale status-bar version string, now sourced from one C#-side
  constant beside the app version.

- **GritKeeper v1.16.2 — a headless self-test of the shipped binary (2026-07-25,
  user-requested).** `GritKeeper.exe --selftest` drives the real code paths behind the table
  tools — #1 the Iron Code Strike (hit, Fatal crit, typed DR), #2 the Beat/MAP turn state
  (spend, penalty, Begin turn), #3 the Dread economy and the live faith pool — validates a
  generated caster-hybrid, and **constructs the whole WinForms UI graph** (every tab, the new
  Strike ▸/Dread ▸ buttons, the Beats and Pool columns, the seeded demo posse). It prints to
  the caller's console (via `AttachConsole`) and drops a `selftest-report.txt`, exiting 0 (all
  clear) / 1 (a check failed). Normal launch is untouched.

  It lets a remote or headless session verify the built exe without a screen — and on this
  machine the full UI graph does construct headlessly, so the largest residual risk (does the
  new WinForms wiring even build?) is now a passing check rather than a manual step. The
  modal dialogs' visual layout and click-through still want the on-screen run-through. First
  run: **11/11 checks passed.**

- **Keeper's Book v2.10 · Bestiary v2.9 — the magic systems reach the Keeper's side
  (2026-07-25, user-requested).** The Signs (Ch. XIII) and Miracles (Ch. VI) are full systems
  now, but the two Keeper-facing books hadn't caught up — a Keeper running an NPC cultist or
  adjudicating the party's Padre had no quick number. Fixed in both, using one benchmark:
  **Sign/Miracle DC = 10 + half the worker's level + its keyed ability** (RES for Signs; PRE,
  RES, or WIT for Miracles), Rank opening at 1st/3rd/5th/7th/9th, and for a foe you read its
  level as twice its Tier — so a Tier III worker forces about DC 16.

  - The **Keeper's Screen** appendix gains a *Signs & Miracles* block beside Grit and Threat
    by Tier: the two DCs, the Rank ladder, and the costs (Signs in Nerve/Blood/Mark, Miracles
    from the pool).
  - The **Bestiary's** *House Rules of the Dead* gains *When the dead work the uncanny* — the
    same DC benchmark, with the standing advice to give a foe two or three workings, not a
    spellbook. A foe is its Special, not a caster's whole list.

- **Player's Book v2.23 — AI-detection pass on the session's new prose (2026-07-24,
  user-requested).** A read of everything written this session — the Signs and Miracles
  chapters, the armor rewrite, the new sections — for the tells that mark machine prose,
  against the standing bar that the books must read human and hold their period voice. It
  came back nearly clean: no AI vocabulary (no *delve*, *tapestry*, *navigate*, *underscore*),
  no hedging or signposting (*arguably*, *notably*, *ultimately*), and the eighty Sign and
  Miracle descriptions carry varied, concrete sentence rhythm rather than a uniform cadence.

  One real cluster fixed: the *Work of Faith* opening stacked two negative-parallelism
  constructions close together ("the difference is not only a matter of…", "chosen, not
  merely granted"). The concrete contrast — a Sign is *taken* and entered in a ledger, a
  Miracle is *asked for* on the knees — carries the point without the meta-framing, so the
  hedged versions are gone. The antithesis constructions left standing (a Rank "is not how
  hard the Sign is to say; it is how far you have to reach") do real explanatory work and
  read human, so they stay.

- **Player's Book v2.22 · GritKeeper v1.16.1 — rules consistency audit (2026-07-24,
  user-requested).** A cross-source pass, engineer and philosophy professor both: do the
  numbers agree across the book, the data, and the app, and are the concepts used the same
  way everywhere? The mechanical layer came back clean — the single-source discipline holds.
  `verify_rules.py` confirms the seventeen Calling tables (697 attack/save cross-checks) are
  in step; Sign DC, Miracle DC, the Dread ladder → Nerve loss, armor DR, and the Threat-by-Tier
  benchmarks (the Keeper's Book table is byte-identical to the app's `Rules.TierRow`) all agree.

  Three *textual* seams needed reconciling:
  - **The nat-20/nat-1 rule read two ways.** Chapter II calls it a one-step shift; Chapter XI,
    the combat chapter, says a natural 20 "always at least hits." At a wide margin those
    diverge. Ch. XI now states the relationship outright — the one-step shift as ever, *and*,
    in a Strike, an at-least-hits/at-least-misses floor — matching how the Iron Code engine
    (#1) already adjudicates it.
  - **Brother Elias Crow, the Appendix D Preacher, had no Miracles** — an omission from the
    Step-3b faith expansion. He now lists his two Rank-1 Miracles (The Steadying Word, Call to
    the Mourner's Bench), his Miracle DC 13, and his Conviction pool, exactly as generation
    would give a 1st-level Preacher.
  - **The Witch Hunter's Zeal pool sat only in prose.** The other four Callings of Faith name
    their pool feature in their 1st-level table; Zeal (added in Step 3b) did not. It now
    appears in the table and in `chargen.json` (feature + description), so the app grants and
    shows it like the rest. Smoke still green (Validate's feature-match accepts it).

- **GritKeeper v1.16.0 — the horror economy on rails (2026-07-24, user-requested).** The
  quiet bookkeeping a horror-tactical hybrid forgets mid-fight — Nerve off the ladder, the
  break, the faith pool — now runs itself.

  **A pure Dread engine (`Horror.cs`).** `DreadCheck` is a Will save vs the Dread DC (Ch. XII):
  crit success steadies (no Nerve), failure loses the ladder's Nerve (DC 10 → 1, 13 → 1d4,
  16 → 1d6, 20/25 → 1d10), critical failure loses it *and* imposes Frightened 1, and DC 25
  carries a lasting Affliction. `Break` rolls the 0-Nerve table, where a 6 is +1 Mark. A new
  tracker **Dread ▸** button rolls it for the selected soul off their own Will, applies the
  Nerve loss, hangs the Frightened, and — at 0 Nerve — rolls the break and takes the Mark.
  Quick-pick buttons for the five sights (a fresh corpse … a world unmade).

  **The faith/sign pool is tracked live.** Every believer's currency (Grace, Conviction,
  Breath, Vital Breath, Zeal) now rides on the posse as a Pool column, seeded full at
  generation and refreshed with a long rest alongside Blood and Nerve. The numeric max is
  re-derived on the sheet and re-checked in `CharGen.Validate`, so it can't drift from the
  Calling's formula — a Padre's Grace is PRE mod + half level or the build goes red.

  ~360 new smoke assertions (the Dread ladder over 400 iterations, the break table, the pool
  formula across every Calling); 7179 → 7986. Engine and pool logic fully covered; the two new
  WinForms dialogs and columns compile clean and want a run-through at the table.

- **GritKeeper v1.15.0 — the Iron Code, adjudicated at the table (2026-07-24,
  user-requested).** The combat crunch that makes a fight satisfying is also what slows a
  table down: Beats, the Multiple Attack Penalty, Fatal dice, Misfire, DR by damage type,
  all tracked by hand. The app now carries it. Two pieces landed together:

  **A pure Iron Code engine (`IronCode.cs`).** `WeaponTraits.Parse` reads structure (Fatal
  dX, Misfire X, Agile, Scatter, Volley, Kickback, …) out of a weapon's free-text `traits` —
  the book's printed trait stays the single source of truth, and a smoke test asserts every
  weapon parses to the right structure. `ResolveStrike` applies the four degrees, the MAP
  (−5/−10, Agile −4/−8), and a Misfire jam on a critical failure; `RollDamage` implements the
  Fatal rule faithfully (a 1d8 Fatal d10 crit is 2×1d10+1d10); `ApplyDR` is typed, best-of
  (no stacking), floored at zero. All pure and WinForms-free, proven by ~90 property-based
  smoke assertions.

  **A live Beat tracker.** Each combatant now carries three Beats and a MAP step; a **Begin
  turn** button resets them, and a **Strike ▸** dialog resolves an attack through the engine —
  prefilling a PC's own to-hit off their sheet, applying the MAP at the attacker's current
  step, rolling the Fatal die on a crit, subtracting the target's DR, taking the Blood, and
  spending the Beat. The result reads off one log line.

  **Fixed along the way (the Step-5 review's one real finding): PCs are now keyed by a stable
  id, not by name.** Renaming a posse soul after they were on the tracker used to silently
  break the Blood mirror, and two same-named souls collapsed to one row. `PartyMember.Id` and
  `Combatant.PcId` (both additive — old saves backfill on load) fix it; every posse↔tracker
  match now follows the id, with name only as a legacy fallback.

  Smoke 5137 → 7179. The engine and all combat logic are covered by tests; the new WinForms
  dialog and column compile clean but want a run-through at the table.

- **Player's Book v2.21 · Keeper's Book v2.9 — editorial pass: glossing the period idioms
  (2026-07-24, user-requested).** A read-through of all three books "like a teacher with a
  PhD in English," charged with preserving the period voice while briefly clarifying any
  frontier idiom a modern player wouldn't parse. The honest finding: the prose is already
  remarkably self-glossing — period terms are explained at first use (*the Exodus of 1879*,
  *Buffalo Soldiers*, *barrow* → "mounded tombs"), false-friends resolved on the spot
  (*The Drummer* → "a travelling seller of tonics, Bibles, futures, or lies"), and creature
  and feature names are self-defining (*psychopomp* → "a death-guide," *Viaticum* → "the last
  rites are also the kindest medicine"). Chapters I and II, the highest-traffic rules text,
  needed nothing.

  Three genuine gaps were filled, briefly and in voice: **"proving up"** (homestead-law
  jargon, never explained) gained a parenthetical — *working a claim the years the law
  required to earn its title*; **"Exoduster"** was tied to the Exodus of 1879 at the point
  that migration is described; and **"remuda"** — lumped in the Keeper's Book cowboy-vocabulary
  passage with the fully-assimilated *corral* and *rodeo*, though a modern reader knows those
  and not it — gained *the herd of spare mounts*. No voice was flattened and no atmospheric
  quote was touched. Player's Book 199 → 200 pages.

- **Player's Book v2.20 · GritKeeper v1.14.0 — the faithful get a magic system too
  (2026-07-24, user-requested).** Step 3 gave the Old Dark forty ranked Signs and left the
  five Callings of Faith with what they had before: a fixed kit of signature features and no
  chosen, ranked, growing repertoire. The asymmetry was glaring. So the faithful now work
  **Miracles** — the book already called them that ("Conviction fuels your sermons and
  miracles") — **forty of them, on six lists, across the same five Ranks** as the Signs.

  **The exact parallel to the Signs, deliberately.** Rank opens at 1st/3rd/5th/7th/9th (one
  shared `RankAt` spine now drives both systems); a soul begins knowing two Miracles and
  learns another as each Rank opens, to six by 10th. Every Calling of Faith draws on the
  **Common Blessings** plus one list of its own, closed to the others: the Padre's
  **Liturgy**, the Preacher's **Revival**, the Shaman's **Spirits**, the Medicine Man's
  **Mending**, the Witch Hunter's **Consecrations**. A Padre and a Preacher answer the same
  dark and no longer answer it with the same words.

  **What makes faith not the Old Dark.** Miracles cost no Mark and draw no Backlash — the
  price is the Calling's pool (Grace, Conviction, Breath, Vital Breath), and the risk is a
  prayer unanswered. They keep each Calling's signature features intact and sit on top, the
  way the Hexer kept Witch-Sight and chose Signs.

  **The Witch Hunter, who had no pool, gains one.** *Zeal* (WIT mod + half level) fuels their
  Consecrations — salt, silver, fire, ward, and the litany of weaknesses. The generic pool
  code meant adding it was a one-line data change that "just worked" through the reckoning,
  the sheet, and the ledger.

  **Enforced end to end, same discipline as the Signs.** `CgMiracle`, `miracleLists` and
  `miraclesKnownAt` per Calling, `MiraclesKnown` on the sheet, and `MiraclesFor` as the
  single gate every path draws through — generation, wizard, level-up, and the level-up
  option list. `Validate` rejects any Miracle off the Calling's lists or above its Rank, and
  — the one genuinely new rule — refuses any soul that somehow holds both a Sign and a
  Miracle. The in-app Quick Reference gained a Miracles leaf rendering all six lists live
  from the data; the printed sheet, the Ledger and the Posse notes all show them. Smoke
  5056 → 5137, including a per-Calling check that each faith soul actually receives its
  Miracles at the right count and legal Rank.

  Book 185 → 199 pages: a new *The Work of Faith* section closes Ch. VI (the rank/pool/list
  rules plus all six lists), the five Callings each name their lists, and the Index gained
  51 entries. Fixed in passing: the CLAUDE.md version table, which had been left at v2.18
  when Step 3's doc script threw before its write.

- **Player's Book v2.19 · GritKeeper v1.13.0 — the Signs become a magic system
  (2026-07-23, user-requested).** Ch. XIII held eight Signs, flat, with no progression and
  no distinction between the four Callings that work them: a 10th-level Hexer knew seven of
  the eight that existed, and knew exactly what a 10th-level Witch knew. It is now **forty
  Signs on three lists across five Ranks**.

  **Rank is the level gate.** Every Sign carries a Rank of 1–5; a soul reaches a new Rank at
  1st, 3rd, 5th, 7th and 9th level and may learn nothing above it. The Calling's table still
  says *how many* Signs you know — Rank says *which ones you may choose from*, so a caster
  now spends a scarce repertoire across a widening range instead of collecting the set.

  **Three lists, and the Witch is finally not a re-skinned Hexer.** The Common Signs (16)
  are open to any worker. **The Bargain** (12) belongs to the Hexer, Dark Cultist and False
  Prophet — the ones who reached out and took, priced accordingly, often in Mark. **The
  Craft** (12) is the Witch's alone: poppets, warded thresholds, knotted wind, a curse that
  cannot be lifted until the wrong is put right. The prose already claimed the Craft was
  "older than the dark the Hexer bargains with"; it now means something mechanically. No
  Hexer learns the Poppet, and no cultist will ever ward a house.

  **Nerve and Blood are stated as an economy, not a per-Sign footnote.** A new *Price*
  section names all three coins: Nerve is the standing one and generally costs the Sign's
  Rank; **two Blood buys one Nerve** where a Sign offers the trade, and Blood so spent does
  not return until a proper rest; Mark is the coin that never comes back, and Rank 5 always
  costs it.

  **The app enforces all of it.** `CgSign` gains `rank` and `list`, each Calling gains
  `signLists`, and `CharGen.SignsFor` is the single gate every path draws through —
  generation, the wizard, level-up, and the level-up option list alike. `Validate` rejects
  any Sign off the Calling's lists or above its Rank rather than trusting the data. Smoke
  4651 → 5053, including a check that no Calling is ever asked to know more Signs than its
  Rank has legally opened.

  **One regression caught while wiring it.** Gating by list meant *Hedge Magic* — the Edge
  that lets a non-caster hold a single Sign — would have granted zero, since a Drifter has
  no list. It now opens the shallow end and only that: the Common Signs at Rank 1, forever,
  which is what Ch. XIII's own lead sentence describes ("by the Hexer freely, by the Touched
  a little"). Opal Vance in Appendix D swapped Borrowed Breath, now Rank 3, for The Lender's
  Ear; a 1st-level Hexer reaches Rank 1 and no further. Book 176 → 185 pages, and the Index
  gained 38 entries (all 40 Signs plus the chapter's new rule sections).

- **Player's Book v2.18 · GritKeeper v1.12.0 — armor becomes a thing you can wear
  (2026-07-23, user-requested).** Ch. X promised that "worn armor grants Damage Reduction
  against blades and small shot only" and then printed a table that only ever named the
  blades half. The three entries now state both, in their own columns, and **small shot**
  is defined where it is used: birdshot and buckshot, a spent ricochet, a pocket pistol
  across a room — anything arriving with less than a full charge behind it. Heavy Duster
  DR 1/1, Boiled Leather DR 2/1 (−1 Defense), Scavenged Iron Plate DR 3/3 (−2 Speed, and
  alone of the three it stops a pistol ball). **No value changed**, as asked: the blades
  column, the penalties and the prices are exactly what they were.

  **Generated souls can now buy armor, which they could not before.** The three entries
  had no `gearPrices` rows, so `buyPlan` was literally unable to purchase them. Leather
  and plate were added at their printed prices, and each Calling now carries an ordered
  armor preference bought *last*, out of whatever the coin leaves after the gun, the horse
  and the rations. Roughly 390 of 400 sampled souls end up dressed — mostly in a duster,
  a third in leather, and plate stays as rare as $60 ought to make it.

  **Armor is on the sheet, and everywhere the sheet goes.** `ArmorWorn`, `DrBlades` and
  `DrShot` join `CharacterSheet` (additively — sheets saved before this deserialize as
  unarmored, so no `session.json` migration). Defense and Speed carry the armor modifier;
  the Ledger's Arms box, the printed text sheet, the Posse notes column and the in-app
  Quick Reference all show it, the last rendering the Ch. X table live from the data.

  **One authorship bug found and fixed by the new checks.** Extending `Validate` to
  re-derive Defense and Speed with the armor term immediately failed 40 level-up cases:
  `ReckonNumbers` overwrites both, so every caller had to remember to re-apply armor
  afterward, and the level-up path did not. Rather than add the missing call, the armor
  term moved *into* `ReckonNumbers` — it holds no randomness and is safe to run repeatedly,
  so Defense and Speed now have exactly one author. A second bug followed from the first:
  Callings that already bought a duster among their sundries skipped the armor step
  entirely, so a Witch Hunter could never reach the plate; the step now upgrades rather
  than skips. Smoke suite 4651 → 5045 checks, all passing, and prints the armor
  distribution so whoever next changes a price can see what it did.

  **Appendix D's six souls state what they are wearing**, like any other sheet. Anni
  Halvorsen gained a buffalo coat: thirty winters in the high country and no coat on her
  gear line contradicted Ch. X's own first sentence.

- **Player's Book v2.17 — one progression spine under seventeen tables (2026-07-23,
  user-requested).** The seventeen per-Calling tables were written one at a time, in 3.5
  idiom, and their attack columns had drifted into seventeen unrelated curves. Reduced to
  three named **attack ranks**, all of which climb by one per level: **Practiced** = your
  level (Bounty Hunter, Gunhand, Marshal, Mountain Man, Witch Hunter), **Steady** = level
  less 1 (the nine mixed Callings), **Slight** = level less 2, never below +0 (Hexer,
  Witch, Dark Cultist). The rank is now printed on each Calling's statline.

  **This was a real balance bug, not a tidying.** Under the old columns the gap between a
  gun Calling and a caster widened from 1 at first level to 5 at tenth, while Bestiary
  Defense climbs 13 → 23 over the same span — so a Hexer's chance to land a blow against a
  level-appropriate foe *fell* as they advanced. Ranks that all climb +1/level fix the
  distance in place: a Hexer never outshoots a Gunhand, but never stops being able to hit
  a barn door either. Martial Callings are unchanged; casters gain +3 by tenth level
  (75 of 170 table cells changed).

  **Saves needed no balance change at all — only to be stated.** All 510 printed save
  values already reduced to exactly two formulas: a **strong save is 2 plus half your
  level**, a **weak save a third of your level**, both rounding down. Ch. III's reckoning
  rows and a new Ch. XIV section, *Attack Rank and the Saves*, now say so outright, so a
  player can reckon either figure without the book. Book grew 174 → 175 pages.

  **The app can no longer drift from the book.** `chargen.json` gains an `attackRank` per
  Calling; `CharGen` gains `AttackFor`/`StrongSave`/`WeakSave`; and `CharGen.Validate`
  re-derives every row of the transcribed table from those formulas rather than trusting
  it. A mistyped `atk` value now fails the smoke suite instead of quietly disagreeing with
  the printed book — the structural fix for having two implementations of one rule. The
  Quick Reference leaf in-app renders the rank table live from the data. Smoke suite
  4569 → 4651 checks, all passing.

- **README — a front door instead of a build sheet (2026-07-23, user-requested).** The root
  `README.md` was purely build instructions: how to run the builders, how to verify. Nothing
  said what Blood & Grit *is*, and nothing linked to a single finished thing. Added a pitch
  above the technical content — the game in a paragraph (western horror on a PF2E-derived d20
  hybrid; Nerve and the Mark as the two tracks that are ours), a one-line-each table of the
  three books, and what GritKeeper actually does at the table.

  **Four links to the current release of each deliverable.** The three book PDFs go to their
  `blob/main` URLs, which GitHub renders inline in its own viewer — click and read, no
  download. They're unversioned filenames living on `main`, so they stay current by
  themselves. GritKeeper goes to `/releases/latest`, which never needs touching on a version
  bump. The self-contained HTML books get a note rather than a link: GitHub serves raw `.html`
  as plain text for security reasons, so a link would show source instead of the book — no
  third-party viewer dependency was added for it.

  **Deliberately version-agnostic prose** ("the current edition," "the latest release," "a
  whole mundane half" rather than a creature count) so a version bump never leaves the README
  lying. The build/verify instructions are unchanged below the fold, plus a `GK/` entry in
  "What's what" and the app's name corrected to GritKeeper. No version bumps.

- **Repo cleanup — the onboarding artifacts that drifted (2026-07-23, user-requested).**
  Housekeeping only: **no version bumps**, no content or behavior change to any book or to
  the app. Worked from a written assessment of the repo; the project itself was in good
  shape, but several files a fresh session reads *first* had quietly gone stale.

  **The `/session-start` command was describing the pre-rename project.** It still said to
  edit `KT/source`, called the delivered folder `BloodAndGrit-Keepers-Table/`, and named the
  app "The Keeper's Table" throughout — paths that stopped existing at the 2026-07-19 rename.
  A session following it literally would have written to the wrong tree. Rewritten against
  current conventions (`GK/`, `GritKeeper/`, `GritKeeper.zip`, GritKeeper), with the PDF rule
  and the `CHANGELOG.md` split folded in.

  **`preferences.md` deleted.** It was supposed to be a duplicate of `CLAUDE.md` — 687 of its
  815 lines had diverged, freezing it at roughly the 2026-07-11 state: Player's Book v2.12,
  app "The Keeper's Table" v1.2.2, none of the standing rules added since. `session-start.md`
  told you to "read one," so it was a coin flip whether a session picked up context 12 days
  and two renames out of date. `CLAUDE.md` is now the only handoff doc.

  **Onboarding no longer points at a packaged snapshot.** `CLAUDE.md`'s first line told you to
  import `blood-and-grit-sources.zip` into a fresh Project — a zip dated 2026-07-11 carrying
  the old thin `build_player.py`, a standalone `bestiary_extra.py`, and instructions for a
  `player-src.html` that was retired on 2026-07-18. Following it would have produced a broken
  build. Replaced with "hand over the current loose files," which can't go stale. The zip
  itself was deleted in a follow-up the same day, once nothing pointed at it any more (379 KB).

  **~3.9 MB of dead weight removed** (~11% of the repo): the nine root-level versioned book
  snapshots (`-v2.4/2.5/2.6` Bestiary and Keeper's, `-v2.12/2.13/2.14` Player's — all two or
  more versions behind, produced by no documented build, referenced by no script or doc), and
  the root copy of `img20.png` (byte-identical to `assets/img20.png`, which is the one the
  build actually inlines). `add_index.py` deliberately kept — documented-intentional dead
  code, not clutter.

  **`GritKeeper/source/` is now generated, not tracked.** It was a byte-identical second copy
  of `GK/source` living in git for no build reason — and the exact seam that silently diverged
  once before (2026-07-10). Now git-ignored like `GritKeeper/app/` already was, and rewritten
  from the master tree at package time (`robocopy GK\source GritKeeper\source /MIR /XD bin obj
  publish`). "Don't edit the delivered folder" still holds; the reason is now "it gets
  overwritten," not "it'll diverge." Verified byte-identical against `GK/source` before the
  untracking landed.

  Verified: `build_player.py` rebuilds byte-identical to `main` (the emblem still inlines from
  `assets/`), and twice in a row to itself.

- **Books v2.16 / v2.8 / v2.8 + GritKeeper v1.11.0 — the mundane frontier, the city, and
  the people who were actually out here (2026-07-22, user-requested).** One release, four
  asks.

  **Forty "normal" creatures, so the Bestiary can carry a slow burn.** The Bestiary goes
  110 → **150**. Twenty more honest animals join **Ch. VIII** (25 → 45): the Mad Dog and
  its hydrophobia, the Prairie Dog Town that breaks a horse's leg, the Snake Den, the Sow
  and Cubs, the Wild Cattle of the Brasada, the Stock-Killer Wolf with a name and a price
  on it. Twenty more become a **new Ch. IX, "Hard Men & Hard Country"** — ordinary men
  (rustlers, claim-jumpers, a saloon brawl, a lynch mob, deserters, Comancheros, a hired
  gun, an outlaw gang, a bounty killer, the Regulators) and the country itself (bad water,
  a norther, a prairie fire, a river crossing, a flash flood, a blizzard). Tiers skew low
  on purpose — 14 at Tier I, 14 at II, 10 at III, 2 at IV — because this is early-campaign
  material. Like the living beasts, **none of it costs a point of Nerve or moves the Mark**,
  and that is the whole design: run it for a month and the table learns the country is
  dangerous on its own terms, so the first genuinely wrong thing has nowhere to be filed.
  Mundane entries are now **65 of 150**, against 25 of 110 before. New Grounds table,
  **The Ordinary Country (d20)**; the Keeper's Ch. V now points at both mundane chapters
  and says what they are for.

  **The peoples of the frontier.** The Player's Book Ch. IV is titled *Origins & the
  Peoples of the Frontier* and carried careful long-form sections on **The First Peoples**
  and **The Mexican Frontier** — and nothing on two of the four peoples it most owed. Added
  in the same shape, same length, same rules-of-the-road box: **Black Westerners** (one
  trail hand in four, the Exodus of '79, Nicodemus, the Ninth and Tenth Cavalry) and **The
  Chinese on the Frontier** (nine men in ten on the Central Pacific grade, the Exclusion Act
  of '82, the district associations, Rock Springs this very year). Keeper's Book Ch. VIII
  gains **"Who Is Actually Out Here"** — the trade's Spanish vocabulary, the real
  proportions, and the instruction that this needs *names and jobs*, not a speech — plus a
  note on running horrors that come out of living belief. Bestiary Ch. IX carries the same
  in its own voice, and the Comancheros, Claim-Jumpers, Lynch Mob, Longhorn Herd, Wild
  Cattle and Regulators entries were rewritten where the history is exact. Two new rollable
  name tables in Ch. XII, and the app's `npcGiven`/`npcSurname` grew 20 → 48 and 20 → 46 to
  match, so the generators stop contradicting the page.

  **Cities.** New Keeper's Book **Ch. XIV, "The Lamplit City"** — running the game in Dodge,
  Kansas City, San Francisco, Butte, Tombstone, Omaha, Denver, Virginia City, Cheyenne and
  Leadville without losing the tone. Its argument is that a city is *better* ground for the
  dark, not worse: anonymity beats isolation (a thing that empties a town of 200 by Tuesday
  feeds in Kansas City forever), the crowd is cover, and indifference does the work fear used
  to. Six things change at the table and only six — guns checked at the deadline, gunfire
  that costs an inquest, witnesses and the press, institutions that commit you rather than
  disbelieve you, paper as the new tracking, and Dread moved indoors and underground. Each
  Bestiary chapter gets a paragraph on how it bends downtown, and **the Dark Cultist
  incorporates**: it charters as a benevolent society with a lawyer, a brass plate, and the
  coroner on its membership roll, so the final scene of a city campaign is an exposure rather
  than a gunfight. Ten real cities keyed, a build-your-own-city checklist, three new tables,
  and a closing note on keeping the party's country competence valuable. New Bestiary Grounds
  table, **The Lamplit City (d12)**; new app tables `cityQuarter` / `cityMachine` /
  `cityWrongNote` / `cityJob` behind a **"A city, in four rolls"** generator button.

  **An editor's pass and a whitespace audit.** Cross-checked every shared number across both
  books and `Core.cs` and found one real drift: the Bestiary's Threat-by-Tier table gave Tier
  I's Dread DC as "10–13" where the Keeper's Book and the app both say "— / 10–13" (a Tier I
  thing may have no Dread at all). Fixed in the Bestiary. All three books: 0 dead anchors, 0
  duplicate ids, 0 die-size/row-count mismatches. `audit_whitespace.py` now **classifies**
  gaps instead of listing them — a page that ends short because the next one opens a chapter
  is the design working, not a defect. Of 44 gaps over 140px across 439 pages, 36 are chapter
  starts and the remaining 8 are heading-orphan avoidance at 143–227px. Nothing to reclaim.

  Page counts 170 → **174** / 88 → **101** / 131 → **164**; all three measure clean (parity,
  zero true-scale clip, zero mobile h-scroll, every anchor resolved) and all three builds are
  idempotent. **PDFs regenerated on explicit request** — 174 / 101 / 164 pages, 612×792pt,
  verified page-for-sheet.

- **GritKeeper v1.11.0 — the Level up button works, and launch is 3x faster (2026-07-22,
  user-reported).**

  **The dead Level up button.** Reported as "I used it once, but now it seems broken," and it
  was: the first-launch demo posse seeded by builds older than v1.9.0 persists in
  `session.json` as six rows with `Sheet: null`, and `LevelUpMember` answered a sheetless row
  with one line in the roll log — on a different tab. The user's own live session had all six.
  Now a sheetless row is offered a repair: GritKeeper draws a rules-legal sheet for the row's
  Calling at its current level (keeping name and gender, and *not* inventing a gender the row
  never had) and levels them. Every other way out of that button now says so in a dialog.

  **Startup.** The v1.10.0 "startup pass" reasoned about JIT in the abstract and made launch
  worse. Measured four publish configurations to first window, each first launch on a
  brand-new copy of the exe so Defender's first-execution scan counts:

  | config | exe | first launch | every launch after |
  |---|---|---|---|
  | ReadyToRun + compression (v1.10.0) | 73 MB | 18.0 s | 1.64 s |
  | ReadyToRun, no compression | 172 MB | 14.5 s | 0.88 s |
  | **no ReadyToRun, no compression** | **155 MB** | **5.1 s** | **1.00 s** |

  Compression is the expensive one — ~39 MB of native libraries inflated and written to
  `%TEMP%\.net\GritKeeper` on the first run of every new build, then scanned. R2R doubles what
  goes through it. Shipping neither. **The zip shrinks** (71.3 → 65.4 MB) because Deflate does
  the same job once, at download time. `IncludeNativeLibrariesForSelfExtract=false` was tried
  and never opens a window; the csproj records that so nobody tries it again.

  **Tab loading.** Building all ten tabs up front cost 379 ms of a ~1,000 ms launch (Bestiary
  91, Posse 71, Map 61, Dice 46, Reference 45) for nine tabs nobody was looking at. Nine are
  now built on first visit; the roll log, the session ledger and the encounter party level
  moved behind fields first, so an unbuilt tab can't swallow them. Shipped and signed, the
  app now opens in **6.1 s first / 0.86 s after**, against 18.0 s / 1.64 s.

  **Five review findings, fixed.** `session.json` is written staged-then-moved — the old
  truncate-in-place could tear on a kill or a crash-time save, and `TryAutoLoad`'s fallback
  for an unparseable file was `SeedDemo()`, which silently replaced the Keeper's whole table
  with the demo posse and then autosaved over it. An unreadable session is now set aside as
  `session-unreadable.json` and reported. Open Ledger pop-outs close with the table they
  describe on load/undo (they were keyed to `PartyMember` instances that Load and Undo
  replace, so they went stale and leaked their dictionary entries). The encounter grid stopped
  allocating a `Font` per cell paint. Two hot regexes cached. The coin ledger parses prices as
  invariant.

  Also: `creatures.json` was **stale** — it still carried the pre-editorial prose for seven
  creatures from the 2026-07-21 pass, so the app and the book disagreed. Re-extracted. Smoke
  4569 → **4612**, 0 failed, with new guards on the creature count, the eight chapters, the 65
  mundane entries costing no Nerve and no Mark, every creature carrying lore and a Found line,
  and the four city tables.

- **GritKeeper v1.10.1 — book-version label sync (2026-07-21).** The status-bar and
  About-box labels now read **Player's Book v2.15 · Keeper's Book v2.7 · Bestiary v2.7**,
  matching the books' human-voice editorial pass. No behavior or embedded-content change
  (the app's creature/table data was never affected by that copyedit); build 0/0, smoke
  4569/4569, exe re-signed. Released with the signed exe.

- **Books v2.15 / v2.7 / v2.7 — editorial pass for a human voice (2026-07-21,
  user-requested).** A line-editor's read of all three books to strip the tells of
  machine prose, with the author's voice preserved tightly. The main target was
  **negative parallelism** — the "it's not X, it's Y" antithesis, which had quietly
  become a habit in the Bestiary's Keeper notes (the "Not a fight — a flood" construction
  alone appeared three times). The iconic flagships were kept ("this is not a thing you
  kill, it is a thing you resolve"; "a house that is a ghost"; "these are not killed, they
  are shut out"); the repetitions were varied so no single figure recurs enough to read as
  a formula. Every "not merely" (a formal/AI tic) across the Player's and Keeper's books
  was recast. No creature, rule, or table content changed — page counts hold at 170 / 88 /
  131, every book still measures clean (parity, zero true-scale clip, zero mobile h-scroll,
  all TOC/index anchors resolved), and all three builds are idempotent. (GritKeeper embeds
  no changed content, so its data is untouched; its README book-version labels were updated
  to match, and only the compiled status-bar label lags until the app's next build.)

- **GritKeeper v1.10.0 — souls level up at the table, and a faster cold start (2026-07-21).**
  - **Level up (Posse tab · Ledger window).** A New Soul–built soul can now advance one
    level at a time through a ✦ Level up button — on the Posse action bar (acts on the
    selected soul) and on each soul's Ledger window. The dialog shows only what the new
    level unlocks: the Hit-Die Blood roll (roll it or set the face; CON mod added), the
    5th/10th-level ability boost, the odd-level Edge (plus the Gunhand's bonus combat
    Edge), the 3/5/7/9 skill increase, the 3rd-level subpath, and any new Signs — each
    populated from the generator's own eligibility helpers so it can never offer an
    illegal pick, and each defaulting to "let the book choose." The soul's new Blood and
    Nerve are granted to current as well as maximum (leveling isn't a heal, but the new
    capacity is theirs), and any open Ledger refreshes in place. A hand-entered row (no
    character sheet) is told to build the soul out first; a 10th-level soul is told it's
    at the frontier's ceiling.
  - **How it works (`CharGen.LevelUp`).** Rather than reconstruct the wizard's
    `AssembleSpec` and re-walk from 1st — `Assemble` re-rolls every prior level's Blood and
    has no way to be handed the old rolls, so that path would quietly destabilize the
    levels below — `LevelUp` clones the finished sheet and appends exactly the new level's
    growth, mirroring `Generate`'s own per-level walk (boost → Blood → features → Edge(s)
    → skill increase → subpath → Signs → reckon). Everything below the new level is
    byte-stable, and the result passes `CharGen.Validate` clean. `PreviewLevelUp` drives
    the dialog's controls and option lists off a clone advanced by the level's
    deterministic part, so Edge/skill eligibility reflects the new level.
  - **Startup pass.** The self-contained publish now precompiles with **ReadyToRun**
    (cold start skips most JIT) and runs with **InvariantGlobalization** (no ICU culture
    load at launch) — the latter is safe because every coordinate the PDF/SVG exporters
    write already goes through an explicit `CultureInfo.InvariantCulture` formatter, so a
    comma-decimal locale can't corrupt an export. Single-file compression stays on so the
    release binary stays one modest file; `TieredPGO` stays at its default. The owner-drawn
    Ledger and map controls were audited for per-paint GDI churn — both were already
    double-buffered with cached brushes/pens, so no change was warranted, and the deeper
    map-bitmap cache was deliberately deferred (a mis-invalidated cache would risk a real
    visual bug on a surface that isn't animated).
  - Smoke suite **2348 → 4569** asserts (the level-up walk is proved conformant across
    every calling × ability method × level 1→10, with byte-stable lower levels, fixed-seed
    reproducibility, honored explicit choices, and the Gunhand/​caster growth paths). Build 0/0.

- **GritKeeper v1.9.0 — gender on every soul, and a first-launch posse with real sheets
  (2026-07-21).**
  - **Gender fills the Ledger on every row (follow-on to v1.8.0's box-filling).** The
    Ledger's Gender box now reads from the member as well as the sheet, so a hand-entered
    soul that carries a gender shows it instead of an em-dash; `PartyMember` gained a
    `Gender` property (change-notified, persisted in `session.json`), the Posse grid gained
    a **Gender** column, and both New Soul → Posse and the sheet→member resync carry it
    across. (Genuinely-unknown gender still reads as a muted em-dash.)
  - **The first-launch demo posse is now six full, rules-legal character sheets** rather
    than bare stat rows — each Appendix-D pregen opens a complete Ledger (abilities, saves,
    Signs, gear, the Four Questions), because `SeedDemo` now builds them through
    `CharGen.Generate` with a fixed Calling and the pregen's own name and gender. A fixed
    seed makes that opening posse identical for everyone; `Rules.Reseed`/`ReseedEntropy`
    bracket the seeding so play dice stay unpredictable afterward. Every seeded soul
    validates clean (0 violations). It persists after first launch exactly as before.
  - Smoke suite **2348** asserts, all passing; build 0/0.

- **GritKeeper v1.8.0 — the map holds still: per-feature random streams, WYSIWYG
  exports, movable secrets, fords on the water, a three-row Map bar, and the Ledger
  fills its boxes (2026-07-19, user-requested).**
  - **The toggle bug (user-reported: checking/unchecking a view box showed a different
    map).** Root cause: one shared `Random` stream — drawing the rail consumed numbers
    the land would otherwise have used, so any overlay toggle reshuffled symbols,
    landmarks, even the title. `Generate` now derives an independent stream per feature
    (water/trail/rail/town/land/landmarks/hour/secrets/name) from the seed, and the
    settlement claims its name and ground even when unshown. Every checkbox is pure
    ink-on/ink-off. Smoke-proved: flipping each of the five overlays leaves the title
    and every landmark byte-identical. (Seeds draw differently than v1.7 — the streams
    changed; determinism per seed+settings is unchanged and still asserted.)
  - **Exports are exactly what you see** — a corollary of the fix: Save SVG/PDF/Copy
    SVG export the displayed model, so checked overlays (grid, Keeper's layer), moved
    landmarks, and moved secrets all ride along. Tooltips now say so.
  - **Fords snap to the water (user-requested):** a Ford landmark places on the river's
    middle stretch (a vertex of the clipped polyline) or on the lake shore — never out
    in the sagebrush. Smoke asserts every generated ford touches the river.
  - **The Keeper's red marks are movable (user-requested):** secrets are recorded like
    landmarks (`MapModel.Secrets`, keyed by index since their lines can repeat) and,
    with ✥ pressed and the Keeper's layer shown, ring in red and drag like landmarks;
    right-click puts one back, "put everything back" covers both kinds (confirmed).
    Their labels also clamp inside the neatline now.
  - **Map bar: three rows by intent (user-requested)** — row 1 the survey (Ground/
    Scale/Hour/Water/Landmarks/Seed/New map), row 2 Show + Zoom (overlay checkboxes ·
    zoom/Fit), row 3 at-the-table + Export (✥ Landmarks, markers, Tracker → Map · the
    three exports), with thin rule separators between groups.
  - **Ledger pop-ups fill their boxes (user-reported):** souls without a full character
    record (hand-entered rows, the seeded Appendix D pregens) showed bare white boxes
    for Abilities/Speed/Init./Attack/Origin/Gender. Everything derivable now fills in —
    RES is recovered from Nerve − Level, Init. shows the DEX modifier on full sheets —
    and the genuinely unknown reads as a muted em-dash. (Init. was empty even on full
    sheets; now it's the DEX mod.)
  - Smoke suite 2339 → **2348** asserts, all passing.

- **GritKeeper v1.7.0 — movable landmarks, and the ink respects the border
  (2026-07-19, user-requested).**
  - **✥ Landmarks (Map tab):** a pressed-state toggle that lets the Keeper customize
    the survey's randomly-placed landmarks. While on, every named landmark wears a
    dashed gold grab ring; drag one and its whole ink (symbol + label) moves together —
    `MapModel` now records each landmark's name, anchor, generated position, and its
    contiguous prim range, and the pure `MapGen.MoveLandmark` translates exactly that
    range and nothing else (smoke-proved: own prims shift by exactly the delta, every
    other prim byte-identical, move-back restores the original ink). Right-click a
    landmark → "put it back where the survey drew it," or "put every landmark back"
    (confirmed, per the standing rule). Placements are kept per map number and
    re-applied when the same seed regenerates (hour/layer/water toggles), cleared on a
    genuinely new map; SVG/PDF exports carry the custom placement. Hover shows a hand
    cursor over anything grabbable (markers included — new to this pass).
  - **Border containment fix (user-reported: rivers ran past the map edge).** Rivers,
    creeks, trail legs + forks, and rail lines are deliberately generated from 12
    units off one edge to 12 off the other so they read as passing through the
    country — the SVG viewBox quietly clipped that overhang, but the GDI preview and
    the PDF drew it, so ink crossed the border frame. Now a Liang–Barsky polyline
    clipper trims them to the inner neatline at *generation* time, so all three
    renderers agree by construction; wide strokes' round caps stay inside the outer
    frame (clip inset 15, frames at 8/15). New smoke sweep: 5 seeds × all 6 water
    kinds with trail+rail+secrets on — zero Line-prim points beyond the paper.
  - Smoke suite 2333 → **2339** asserts, all passing.

- **GritKeeper v1.6.0 — universal undo/redo, a smarter watermark, a color-coded dice
  log, confirmations closed out everywhere, and bigger random generators (2026-07-19).**
  A user-requested UX pass:
  - **Universal Undo/Redo**: snapshot-based over the same `GameSession` shape File →
    Save/Load already uses. The four `BindingList`s (`party`/`tracker`/`encounter`/
    `clocks`) each push a JSON snapshot onto a 50-deep undo stack on any add/remove/edit;
    `ApplySession` now suppresses re-capture during its own bulk rebuild so a restore is
    one step, not N. Reachable via **Edit ▸ Undo/Redo** (Ctrl+Z/Ctrl+Y) and matching
    buttons pinned in the status bar, so it's live from any tab. Session notes keep the
    textbox's own native undo instead — snapshotting every keystroke would flood the stack.
  - **The emblem watermark scales with the window**: previously forced into the bottom
    half of a pane regardless of how much background space was actually free; now
    centers in whatever's free below the real content and grows/shrinks with the pane's
    own size, capped at a dignified share of the width.
  - **The Dice tab's roll log is color-coded** (`StyleRollLog`, an owner-drawn
    `ListBox`): a four-degrees result (CHECK/DREAD) is graded by its degree word —
    critical success gold and bold, critical failure near-black and bold, a plain
    success verdigris, a plain failure rust — a bare quick-die roll by whether it landed
    on its max or min face, any other roll gets a neutral steel-blue tag, and plain
    posse/tracker/session lines stay the default ink.
  - **Confirmation dialogs closed out on the last unguarded clears**: "Clear log" (Dice),
    "Clear" (Generators output), and "Clear" (New Soul sheet) now confirm before wiping,
    matching every other destructive action in the app.
  - **Random generators widened**: the `chargen.json` flavor pools (given names,
    vices, lost/seen/moving) roughly doubled (16→30 names each); the single-roll
    Country-in-Your-Pocket tables (rumors/trail/plunder/omens — the ones without the
    town/face generators' combinatorial multi-roll structure) grew by 10–12 entries
    apiece in `tables_extra.json`; and the Grounds terrain tables picked up every
    ordinary Bestiary beast that wasn't already cited anywhere (badger, bobcat, coyote,
    black bear, gray wolf, mountain lion, wild boar, bison bull, grizzly bear, old
    tusker, stampede — the Tier V White Bison stays off every table on purpose, per its
    Ch. XII "gone quiet" rumor).
  - **Map tab: tactical markers + zoom & pan (same session, user-requested).**
    ＋ Marker ▾ drops a posse soul (green) / NPC (gold) / creature (red) at the view
    center; **Tracker → Map** columns the whole tracker onto the field (posse west,
    trouble east, skips names already standing); markers drag into position (one undo
    step per completed drag), right-click renames or removes, Clear markers confirms.
    Markers live in map-model coordinates in `session.json` (`GameSession.MapMarkers`)
    so they survive restarts AND reseeds — session state, deliberately not part of the
    deterministic map. Zoom: mouse wheel at the cursor (1×–8×), drag empty ground to
    pan, 🔍＋/🔍−/Fit buttons; view state only, never in exports.
  - **Generators: "The Hand Behind It" left the Grounds dropdown (user-reported).**
    It's the villain picker, not a terrain — listed among the grounds it read like a
    stray creature. Now its own button under the terrain roller, same safe-table check.
  - **Expert-review pass on the session's own code, three real defects fixed before
    merge:** (1) the color-coded log's owner-draw handler disposed the ListBox's own
    Font on every non-bold line (worked only by TextRenderer's handle cache — latent
    crash); a cached bold variant now lives as long as the log. (2) Undo captured once
    per ListChanged event, so one click (Damage → posse edit + tracker mirror) made two
    steps with a desynced middle, and New Session flooded 2×posse-size steps; captures
    now coalesce via BeginInvoke — one user action, one undo step, always a consistent
    snapshot. (3) The Ctrl+Z/Ctrl+Y menu shortcuts intercepted the keys before any
    focused TextBox saw them, so typing in Session notes + Ctrl+Z would yank the whole
    table instead of undoing typing; Undo/Redo now route to the focused text field's
    native undo first, and no-op while a grid cell editor is open. Plus two smaller
    ones: owner-drawn ListBoxes don't auto-compute HorizontalExtent (long log lines
    couldn't h-scroll — now measured in Log()), and StatusStrip tooltips needed
    ShowItemToolTips.
  - **The name finished its move (user-requested):** working tree `KT/` → **`GK/`**,
    delivered folder `BloodAndGrit-Keepers-Table/` → **`GritKeeper/`**, zip →
    **`GritKeeper.zip`** — plus the last in-app "Keeper's Table" strings (session
    file-dialog filters, crash-report captions) → GritKeeper.
  - Smoke suite grew from 2322 to 2333 asserts (one per new terrain entry's
    real-creature-name check); all passing. Published, signed, mirrored to the
    deliverable, and rezipped.

- **GritKeeper v1.5.0 — the app renamed, the Map tab shipped, the Ledger everywhere,
  a chargen wizard, hand-tweaks, gender, colored dice (2026-07-18/19).** The app is now
  **GritKeeper** (exe `GritKeeper.exe`, product/title/About/README updated; the internal
  namespace stays `BloodAndGritKeeper` so embedded-resource names and the source tree
  hold still). One long user-request session:
  - **Map tab finished and wired in** (the previous session's `MapGen.cs`/`TabsMap.cs`/
    `Pdf.cs` were complete but never added to the tab strip): Trail Maps — seeded
    procedural frontier surveys by ground/scale/hour/water, trail/rail/settlement/grid/
    Keeper's-secrets toggles, deterministic per seed, Ctrl+G for a fresh map, export as
    SVG (file or clipboard) or **one-page landscape-Letter PDF** (per explicit user
    request). PDF writer proven with PyMuPDF (page count/size) and rendered visually.
  - **The Ledger, on glass** (`Ledger.cs`, new): the Player's Book's character sheet
    redrawn as a live WinForms control (`LedgerView`) — name/**gender**/calling/level/
    origin row, the six abilities, reckoned numbers, the Mark's six boxes, the Four
    Questions, all seventeen skills with proficiency ticks, edges & path, arms & gear &
    coin. The New Soul tab now renders every sheet on it (A−/A＋ zoom), replacing the
    plain-text view.
  - **Soul pop-out windows**: double-click a posse member (or their far-right **Ledger
    button**, also on the Tracker for posse souls — never for creatures or ad-hoc rows)
    to open their Ledger in a modeless window with the exact Bestiary-card configuration:
    one window per soul, reused, cascading, A−/A＋, → Tracker, and ✎ Tweak when a full
    sheet exists. Members carry their whole `CharacterSheet` in `PartyMember.Sheet`
    through `session.json` (sheet converted to auto-properties for serialization;
    round-trip smoke-tested).
  - **Notes expand**: double-click a truncated Posse Notes cell to read/edit the whole
    note in a resizable dialog (Enter stays a newline; explicit Save).
  - **Posse reorder**: ▲ ▼ move the selected soul, selection follows.
  - **Colored dice** (user-specified palette): d4 green · d6 blue · d8 orange · d10
    white · d12 yellow · d20 red · d100 purple — applied to the keypad and quick-dice
    buttons (`DieBtn`, FlatStyle.Flat) and the tray's tumbling faces; best face now
    rings gold and a 1 rings near-black (the old verdigris/blood rings vanished on
    colored faces). Fixed the keypad's +d100 label clipping at width 54.
  - **Dice quantity**: a × spinner on the keypad row — `Rules.ExprAddDie` takes a count
    (× 4 then +d6 → 4d6; stacks: 2d6 + ×3 → 5d6), clamped 1–100, smoke-tested.
  - **New Soul, three roads**: 🎲 generate (as before, now with **gender** rolled and
    the given name drawn from gender-matched lists in `chargen.json`; Ch. III review
    confirmed the book carries gender only in prose, so the app now records it
    explicitly) · **🧭 Wizard** (`TabsWizard.cs`, new — nine steps: level/method/name/
    gender, Calling, Origin, ability assignment with Suggest + 5th/10th boosts, skills +
    increases, Edges from lists filtered by live legality, Signs/path/calling-choice,
    coin + shopping the printed price list against a hard budget, the Four Questions;
    every unanswered choice falls back to the book's own random draw) · **✎ Tweak**
    (every number and list editable; sheet re-validated but never blocked — the Ledger
    notes "hand-tweaked" instead). Wizard assembly is pure logic in
    `CharGen.Assemble(AssembleSpec)` and re-uses the same `ReckonNumbers`/eligibility
    code as the generator, so the two roads can't disagree.
  - **Soul sheet → PDF**: Save PDF… on the New Soul tab writes the sheet as a printable
    Letter PDF (`Pdf.TextSheet`, previously written but never wired; footer em-dash
    WinAnsi bug fixed).
  - Ten tabs now: Ctrl+0 reaches the tenth, the five-minute lesson/shortcut card/status
    bar rewritten, View-menu shortcut labels fixed for tab 10.
  - Verified: build 0/0; smoke **2,322/0** (Assemble conformance sweeps incl. junk-choice
    fuzzing, gendered-name checks, sheet session round-trips, map generation/SVG/PDF
    structural + determinism, × count builder cases); PDFs validated with PyMuPDF and
    rendered; app driven and screenshot-verified (rename, Map, colored dice + × spinner,
    Ledger render with gender, posse ▲▼/double-click/Ledger buttons, Tracker button
    only on posse rows). Branch `session/2026-07-18-gritkeeper-ux`.

- **Keeper's Table v1.4.0 — menu bar, dice keypad, Reference deck, real icons, watermark,
  keyboard pass (2026-07-18).** Two user request batches in one session:
  - **Menu bar** (`Menus.cs`, new): **File** — Save session (Ctrl+S), Save session as…
    (Ctrl+Shift+S), Load session… (Ctrl+O; writes `session-backup.json` beside the exe
    before replacing the table, and validates the file before asking), Exit. **View** —
    all nine tabs with their Ctrl+N shortcuts shown. **Help** — *The five-minute lesson*
    (F1; a modeless, zoomable in-app walkthrough of all nine tabs, saving, and the
    session rhythm), *Keyboard shortcuts*, and *About* (emblem, app + book versions).
    Persistence refactored into shared `Snapshot()`/`ApplySession()` so autosave,
    save-as, load, and startup auto-load all ride one code path.
  - **Dice-tab expression keypad**: `+d4`…`+d100` buttons build the expression (clicking
    the same die stacks its count — d6 → 2d6 → 3d6), ＋/−/digits build the modifier,
    ⌫/C edit it; operators never double up. Logic lives in `Rules.ExprAddDie`/`ExprAppend`
    (pure, in `Core.cs`) with 63 new smoke asserts including builds-always-parse sweeps.
  - **Reference tab rebuilt as an 11-leaf Keeper's screen**, paged with ◀ ▶ or Left/Right
    (the arrow keys are captured in `ProcessCmdKey`, so they work regardless of focus;
    the deck wraps around). Every leaf is real tables (monospace, Blood-red header bands,
    last-column word-wrap): the Roll & DC ladder · Iron Code · wounds & Lasting Injuries ·
    Conditions · Nerve & Dread (+ recovery) · Mark & Taint · Signs & Grit · the Long
    Odds · **Arms of the Frontier** · **Goods & Provisions** · skills/saves/abilities.
    The arms, goods, signs, and skills leaves render live from `Data/chargen.json` —
    the printed prices and dice can never drift from the book. (RichTextBox landmine
    documented in `RTbl`: selection formatting must be re-asserted before *every*
    append or later lines silently fall back to the proportional default and the
    columns shear.)
  - **Keyboard pass** (20-year-UX discretion): Ctrl+D/Ctrl+H damage/heal on Posse *and*
    Tracker (scoped to the active tab, suppressed while a grid cell is mid-edit),
    Ctrl+I initiative + Ctrl+R next round on the Tracker, Ctrl+F to the Bestiary search,
    Enter pops out the selected creature. Deliberately NOT keyed: destructive clears
    (stay click-and-confirm) and generator browse buttons (Tab+Space serves them).
    Tooltips name their shortcuts; the Help shortcut card covers all of it.
  - **Real icons**: new multi-size `app.ico` built from the cover emblem (full emblem at
    256/128/64/48, a skull-tight crop at 32/24/16 so the small sizes stay readable) —
    `<ApplicationIcon>` gives the exe its Explorer/desktop icon, and the embedded copy
    feeds every window title bar (main, creature pop-outs, lesson/shortcuts). The small
    fixed dialogs drop the stock icon instead (`ShowIcon=false`). A desktop shortcut
    **"The Keeper's Table"** now points at the delivered exe.
  - **Watermark**: the emblem, ghost-faint (≈5% alpha), in the dead space bottom-right of
    the busier panes (Posse/Encounter/Tracker grids + empty-state hints, Dice and
    Generators button panels, Session clocks, New Soul hint). It sizes itself to the free
    space and vanishes entirely when content comes within reach — never behind rows or
    text.
  - Verified: build 0/0; smoke **1,960/0** (63 new builder asserts); launched and
    screenshot-verified (menu bar, icons, watermark restraint, keypad wiring via the
    smoke-tested pure functions, Reference paging by arrow key including wrap-around,
    Ctrl+R/Ctrl+I on the Tracker); published self-contained exe signed **Valid**
    (same CN=Cole Williams cert). Branch `session/2026-07-18-kt-menus-icon-ux`.

- **Keeper's Table v1.3.0 — New Soul character generator, padding/UX pass, clear-everywhere,
  signed exe (2026-07-18).** Five user requests in one session:
  - **New Soul tab (9th tab, Ctrl+1–9)** — a whole random character sheet, strictly
    conformant to the books: Ch. III's eight steps at any level 1–10, both ability methods,
    all 17 Callings × 10 Origins with every cross-constraint enforced (Faith may not take
    the Gambler origin or work Signs; Hedge Magic barred to Faith *and* to the four
    sign-working Callings per its own "you are not a Hexer" text; Hexer/Dark Cultist/Came
    Back Wrong Marks; the Dark Cultist's Patron named at 3rd as the book says, not at 1st;
    Gunhand's Edge bonus combat picks; Edges' ability/edge/skill prerequisites; 3rd-level
    subpaths; per-level Blood rolls; coin rolled on the Ch. X dice and spent only at
    printed prices). Rules data transcribed into `Data/chargen.json` (embedded like the
    rest); `CharGen.Validate` re-derives every figure independently and the smoke suite
    generates + validates ~370 sheets per run (all callings × levels × methods + random
    sweep + Appendix-D-style spot checks). Sheet renders in the pregens' format, four
    questions and Compass included; **→ Posse** seats the soul directly.
  - **Padding/UX pass** (user: words against the window edge don't conform to good UX).
    WinForms RichTextBoxes ignore their own `Padding`, so every text pane was flush to the
    chrome. New `Pad()` host-panel helper wraps the Bestiary reading pane (14px), the
    creature pop-out windows (16px), Reference (14px), Generators output (12px), the New
    Soul sheet (16px), and the Dice log panel (10px).
  - **A fresh start everywhere** (user request): every roster/record now has a confirmed
    clear — new "Clear posse", "Clear ledger", "Clear threads", Bestiary filter "Reset",
    New Soul "Clear", joining the existing Encounter/Tracker/Dice/Generators clears.
  - **Expert UX evaluation** (user request) with two fixes applied: the fixed 1280×820
    startup size exceeded this laptop's 1366×768 working area and clipped the bottom
    button row — now clamped to `Screen.WorkingArea`; and the creature pop-out was
    discoverable only via double-click + tooltip — a visible "⧉ Pop out" button now sits
    on the Bestiary bar. Remaining recommendations recorded in the session notes.
  - **Signed, metadata-complete exe** (user: Windows/firewall/Cortex warnings). New
    `KT/source/sign.ps1` creates/reuses a self-signed **CN=Cole Williams** code-signing
    certificate (10-year, reused across releases so the publisher identity is stable),
    installs it to this machine's LocalMachine Root + TrustedPublisher, signs with SHA-256
    + RFC3161 timestamp, and refuses success unless `Get-AuthenticodeSignature` reports
    Valid. csproj now carries honest metadata (Company/Product/Description/Copyright,
    v1.3.0). Published exe signs Valid and launch-checks clean. (SmartScreen on *other*
    machines still needs a CA cert or reputation — documented in sign.ps1 and README.)
  - Verified: build 0/0; smoke **1,897/0 × 5 consecutive runs**; app launched, all nine
    tabs + generated sheet + padded pop-out screenshot-verified; deliverable re-mirrored
    (stale duplicate root exe dropped) and re-zipped (63.4 MB). Released as GitHub Release
    `keepers-table-v1.3.0` with the signed exe as the release asset (binaries stay out of
    the tree). Branch `session/2026-07-18-kt-padding-chargen`.

- **2026-07-18 — Tracking standardized across all Desktop\Git repos (infrastructure).**
  Changelog moved from CLAUDE.md into this file; current versions tagged (`players-v2.14`,
  `keepers-v2.6`, `bestiary-v2.6` at the books commit, `keepers-table-v1.2.3` at the app-sync
  commit); canonical `autosync.ps1` / `register_autosync_task.ps1` installed (identical in
  every repo: auto-commit always, push only when an `origin` remote exists). Shared
  conventions documented in CLAUDE.md. No book or app changes; versions unchanged.

- **Player v2.14 / Keeper v2.6 / Bestiary v2.6 + app v1.2.3 — content expansion, Serling
  slow-burn pass, whitespace audit, and the app brought in sync (2026-07-18).** Four jobs in
  one session (all user-requested):
  - **Keeper's Table app synced — and a standing rule made of it** ("sync up the app and
    continue to do so"). Reference tab's DC ladder updated to the unified seven-step ladder;
    status bar + README to the current book versions; app version 1.2.2 → **1.2.3**.
    `Data/creatures.json` re-extracted from the current Bestiary with a new repo tool,
    **`extract_creatures.py`** — proven faithful by first re-extracting the *old* HTML and
    diffing against the shipped JSON (0 content diffs), which also revealed and fixed a
    latent gap: the original extraction had dropped the statblock **Mark** line, so 18
    creatures' Mark entries were empty in the app; they're populated now (the Bestiary popout
    already rendered the field). Built + smoke suite **1360/0 locally on Windows** (SDK 9),
    published, deliverable folder re-mirrored, zip rebuilt (63 MB). The standing rule is at
    the top of this doc.
  - **"The Patrons at the Table"** — new Keeper's Book section after The Dark's Wages: a
    veteran-Keeper essay per Patron on how and *when* each approaches players (each waits at
    a different door — want, the question, hurt, the grave, the strike, the flock), plus a
    "veteran's rules" closing note (offer only at the owned moment of weakness, speak through
    intermediaries, one waking Patron per campaign, no must always be a real answer). Indexed.
  - **Items** (Player's Book Ch. X): six new Uncommon Goods (camera & wet-plate kit,
    lead-lined coffin, Pinkerton file on a name, blasting machine & wire, galvanic battery,
    surveyor's transit — first three with mechanical notes); three new lesser relics
    (Coyote's Tooth, Widow's Locket, Church-Door Nail); four new artifacts (the Padre's
    Lantern, the Bone Fiddle, the Meridian Chain, the Ferryman's Dollar). All seven
    relics/artifacts added to the Index.
  - **Serling slow-burn tone pass across all three books** ("modify them as if you were Rod
    Serling… starts out feeling like a typical TTRPG about westerns"). Ch. I restructured to
    enact the descent: it now opens as a straight handbill western and closes with the turn
    (The Three Truths + the survey quote moved to chapter end); the cosmic thesis lines were
    split — "the land is occupied" stays as Ch. I's closing reveal, "it is not peace, it is
    patience" relocated to the Ch. XII narrator block where it lands hardest. A new
    **narrator thread ("the Compiler")** — `.narr` styled blocks, italic with a tilde mark —
    escalates at act boundaries: Player Ch. VII (the threshold), Ch. XII (the reveal), end of
    App. E (the "for your consideration" sign-off); Keeper Ch. I (host-to-host: let the first
    night stay a western), Ch. VI (the campaign quietly changes its nature), Ch. XIII
    ("Submitted for your consideration: one county…"); Bestiary Ch. I (the field-book road
    runs downhill), Ch. V (the remedies stopped mentioning the rifle), Ch. VII ("It has
    already noticed you reading"). No rules text touched.
  - **Whitespace audit** (user granted permission to break tables): new repo tool
    **`audit_whitespace.py`** measures every rendered page's bottom gap and names the block
    that moved. Findings: tables/lists/boxes/statblocks already split; the big gaps are
    deliberate chapter-start page breaks and orphan control (left alone — breaking those
    *would* hurt readability). The real fix: **`.quote` and `.narr` blocks are now
    word-splittable** like paragraphs (shell `isParaLike`), which closed the genuine
    mid-flow gaps (Bestiary flagged pages 11 → 8; the survivors are all intentional breaks).
  Final state: Player **v2.14, 170 pp** · Keeper **v2.6, 88 pp** · Bestiary **v2.6, 131 pp**,
  all render-verified (parity, zero clip, zero h-scroll, anchors resolve, idempotent);
  versioned copies rotated (kept three per book; v2.11/v2.3/v2.3 removed).

- **Build-system reconciliation — one builder per book (2026-07-18)** (user-requested: "the
  Player's Handbook is not built the same way as the other two … reconcile it, and combine the
  two Bestiary py builders into one"). All three books now follow the same pattern — **each
  book is a single `build_<book>.py` that carries its own content and runs standalone**:
  - `build_player.py` now embeds the entire Player's Book HTML as a raw string `SRC` (edit the
    book there); **`player-src.html` is retired** (deleted from the tree; full history in git).
  - `bestiary_extra.py` was **merged verbatim into `build_bestiary.py`** (ordinary beasts,
    `LIVING_LORE`, `sort_sections`, `gen_appendix`) and deleted — adding a creature now means
    editing that one file.
  - `build_keeper.py` and `build_bestiary.py` **read `blood-and-grit.html` directly** — the
    manual `cp blood-and-grit.html <target> &&` step is gone; each book builds with just
    `python build_<book>.py` (player first, since it produces the shared shell).
  - `measure_index.py` now patches the static Index page numbers into `build_player.py`'s
    `SRC` (same regexes, new target file); README, session-start command, and this doc updated.
  **Integrity proof:** every step was verified byte-identical — the converted `build_player.py`
  reproduces `blood-and-grit.html` md5-exact, and the rewired/merged Keeper and Bestiary builds
  reproduce their books md5-exact; `measure_index.py` re-run green end-to-end (168 pp, parity,
  zero true-scale clip, zero h-scroll, idempotent). No book content changed in this step.

- **Player v2.13 / Keeper v2.5 / Bestiary v2.5 — Editorial pass, 19 of 20 findings applied
  (2026-07-17/18).** A cover-to-cover editorial read of all three books produced 20 proposed
  changes, reviewed by Cole in an approve/deny artifact; 19 approved, R3 denied-with-note
  (recorded in `editorial-denials.md`). Applied:
  - **Rules (7).** The two books taught **different DC ladders** — the Player's Book now
    carries the Keeper's finer ladder everywhere (Trivial 10 · Easy 13 · Average 15 · Hard 18 ·
    Very Hard 20 · Punishing 25 · Beyond 30; Ch. II table re-pitched, Appendix C, and the Ch. X
    surgery DC relabeled). The **attack-formula contradiction** ("level + weapon rank" vs the
    Calling tables) resolved in the tables' favor in Ch. II / III / V / XI — attack *and save*
    proficiencies are now read straight from the Calling tables, the +2/+4/+6 rank formula
    applies to skills (the artifact's R2 text said "skills and saves"; the tables show saves on
    their own track, so the installed wording keeps tables authoritative for both). **Ability
    boost timing** unified to one point at **5th and 10th** in Ch. IX and Ch. XIV (per Cole's
    R3 note — the denied proposal had been 4th/8th). Cap-and-ball reload standardized to
    **three rounds** (Ch. XI now matches Ch. X). Both **Grit quick references** completed to
    all five uses (Appendix C + Keeper's Screen). **Venom save DCs** added (Rattlesnake Fort
    DC 13, Great Serpent Fort DC 18). Ch. XII Afflictions prose now points at the Keeper's
    full table.
  - **Prices (5).** Duplicate-row drift fixed: fine saddle horse $90+ both tables, mule $30,
    saddle scabbard $4, bedroll & tarp $2; the Camp & Trail "Saddlebags / panniers" row is now
    "Panniers (pair)" so it's honestly a different good from the $3 Tack saddlebags.
  - **Names (4).** Prospector Edge renamed **"Laid By"** (was a collision with the Pay Dirt
    class feature); the Wendigo's subtitle is now **"the deep winter given a body"** (its old
    subtitle was the Tier III entry's name); its Putting-It-Down line no longer puns on "iron
    heart"; the orphaned PF2E term "fortune bonus" removed from Stack the Odds.
  - **Magnitudes (6 in one).** Vague bonuses given numbers: Herb-Lore +2, Mend the Body 2d8
    per further point, Draw Out the Sickness +4 / 3 Vital Breath to cure, Call Back the Breath
    half maximum Vital Breath (rounded up), Hard Ride +10 ft, Honeyed Word +3.
  - **Style (3).** Three "was X once — until Y" origin pivots rewritten (Hollow Prophet,
    Dollmaker's Children, Stone Giant) to thin the Bestiary's densest formula cluster; nine
    self-praise adjectives stripped from How-to-Play notes ("brilliant"/"fantastic"/
    "masterclass"); the Prospector's two J. Halloran epigraphs differentiated (first byline
    now "testimony given at the Widow's Comfort inquest") so the bookend reads as one story
    in two halves.
  All three books rebuilt and render-verified (Player 168 pp — one page over v2.12 from the
  added lines; Keeper 84; Bestiary 131; parity, zero true-scale clip, zero h-scroll, all
  anchors resolve, idempotent builds; 204 Player index statics re-patched). *(The Keeper's
  Table follow-up flagged here — stale Reference-tab DC ladder and status-bar versions — was
  done on 2026-07-18; see the app-sync entry above.)*

- **Keeper's Table — true single-file standalone (embedded data) + first GitHub Release
  (2026-07-16).** The self-contained exe still needed its `Data/*.json` sitting in a `Data/`
  folder beside it (`creatures.json` is mandatory — the app crashed on launch without it), so a
  lone `.exe` download was broken. Fixed by **embedding the three JSON files into the exe**
  (`<EmbeddedResource>` in the csproj; `Db.ReadData` now reads them from the assembly and falls
  back to `Data/` on disk for the smoke rig / dev build). The published exe is now genuinely one
  file — no runtime, no data folder — and writes only `session.json` beside itself. Verified:
  build 0/0, embedded resources present + parseable (110 creatures, all tables), smoke 1360/1360,
  flagless publish emits exe-only (no `Data/`). Refreshed `publish/` + delivered `app/`, rebuilt
  the zip. **Published the exe as a GitHub Release** (tag `v1.2.2`) since binaries are git-ignored
  and don't belong in the repo tree — this is why the user saw no `.exe` on GitHub before. Done on
  `session/2026-07-16-kt-embed-data-standalone`.

- **Keeper's Table — self-contained single-file publish baked into the csproj (2026-07-15).**
  Made the app's zero-.NET-dependency packaging durable and cleaner. The self-contained flags
  used to live only on the publish *command line* (`-r win-x64 --self-contained true`), so a
  publish that forgot them would ship framework-dependent again — which is exactly what bit the
  very first delivery (it needed the Desktop Runtime installed). Verified the current build was
  already self-contained, then moved the settings **into `BloodAndGritKeeper.csproj`**
  (`RuntimeIdentifier=win-x64`, `SelfContained`, `PublishSingleFile`,
  `IncludeNativeLibrariesForSelfExtract`, `EnableCompressionInSingleFile`) so a bare
  `dotnet publish -c Release` can never regress. Because the app resolves every path via
  `AppContext.BaseDirectory` (never `Assembly.Location`), single-file is safe — the deliverable
  collapsed from **~258 files to a single 69 MB `BloodAndGritKeeper.exe` + `Data/`**. Synced the
  same csproj into the delivered `source/` mirror, regenerated `publish/` and the delivered
  `app/`, and rebuilt `BloodAndGrit-Keepers-Table.zip` (72 → 63 MB). Verified: build 0/0, smoke
  1360/1360, flagless publish produces the single-file self-contained exe. No app version bump
  (build-infrastructure only; behaviour unchanged). Done on
  `session/2026-07-15-kt-selfcontained-csproj`.

- **Infrastructure — relocated under `Desktop\Git\` (2026-07-15)** (user-requested: gather all
  local git repos into one `Git` folder on the desktop). The repo moved from
  `C:\Users\Cole\Desktop\BloodAndGrit` to **`C:\Users\Cole\Desktop\Git\BloodAndGrit`** (alongside
  `TideWatch` and the newly-imported `DebForge`). Two path fixes were needed: `autosync.ps1` had
  the repo root **hardcoded** to the old path (`$repo = "…\Desktop\BloodAndGrit"`), so it now
  derives it from `$PSScriptRoot` — portable, survives future moves (the same fix TideWatch's
  scripts already had); and the `/session-start` command's path was updated. Added the previously
  missing **`register_autosync_task.ps1`** (self-locating, "BloodAndGrit AutoSync"). The "BloodAndGrit
  AutoSync" scheduled task stores an absolute path to `autosync.ps1`, so it must be **re-registered
  from an elevated shell** to point at the new location: `pwsh -File
  "C:\Users\Cole\Desktop\Git\BloodAndGrit\register_autosync_task.ps1"`. Git repo, remote, and
  history are unaffected by the move. Done on `session/2026-07-15-relocate-under-git`.

- **Infrastructure — session-branch workflow (2026-07-12)** (user-requested: changes start on
  a branch, merge to main on success). `autosync.ps1` rewritten branch-aware: it commits and
  pushes whatever branch is checked out (upstream set on first push, rebase against the
  branch's own remote counterpart, detached-HEAD guard) so session branches are backed up to
  GitHub like main. Convention documented under "How I like to work"; full lifecycle
  dry-run-tested (branch → autosync push → `--no-ff` merge → branch deleted local + origin).
  Git global user.name/email configured on the machine — merges need a committer identity.

- **Player v2.12 / Keeper v2.4 / Bestiary v2.4 / app v1.2.2 — Books copyedit pass +
  feathering port + fresh PDFs (2026-07-12)** ("give the same treatment to the three books,
  and since the app quotes from the book, edit it accordingly as well" + "save the most
  recent builds of all books as .pdf and remove older PDF versions"). Three parts:
  - **Feathering paginator ported to sources** (prerequisite — see the resolved-divergence
    note at the top of this doc). The new script block was spliced verbatim from the
    delivered v2.11 into `player-src.html` (plus the `.sb-cont` CSS rule), the version
    cascade tuples in both build scripts were re-anchored, and `pag_patch.py` now detects
    the feathering engine and no-ops. Proof: rebuilt Player's Book was **byte-identical**
    to the delivered v2.11; Keeper/Bestiary matched except line-ending/CSS-position
    artifacts of the old hand-patching (script regions hash-identical).
  - **Copyedit (professor's rules: real errors only; the frontier voice stays).**
    Player's Book: "A Word on the Rules" no longer lists the gun rules as both adapted
    *and* original; a double-"and" list in the Ch. V intro; a double bolt-on "And" in the
    Ch. VI intro; "sickened" → "Sickened" in the Witch's Hex; and **five pregens in
    Appendix D used skills that don't exist in this game** (PF2E leakage: Deception→Deceive,
    Diplomacy→Persuade, Society→Insight, Nature→Animal Handling, Lore (Scripture)→Lore
    (Occult)). Keeper's Book: two stray `</p>` tags in keeper-notes (Ch. II, Ch. XI);
    "call for Presence, Deception, or Intimidation" → "Persuade, Deceive, or Intimidate";
    "better than eighty" creatures → "better than a hundred" (twice; the Bestiary holds
    110); "a name cut in a board hill" → "a boot-hill board" (Ch. I epigraph). Bestiary:
    remarkably clean — one clarification, the ordinary-beasts note now reads *marked "—"
    to say so*. `perdition_map.py` labels checked, clean. **App impact: none of the
    corrected passages live in `creatures.json`/`tables.json` or the Reference tab**, so
    app data is untouched; the app got the version-string bump only (status bar + README →
    v2.12/v2.4/v2.4, csproj 1.2.2), build 0/0, smoke 1360/1360, republished + re-zipped.
  - **Verification & PDFs.** All three books rebuilt idempotently (double-build md5) and
    render-verified: Player 167 pp (feathering absorbed 8 pages vs. the old 175; 204 index
    statics re-patched), Keeper 84 pp, Bestiary 131 pp — desktop/mobile parity, zero
    true-scale clip, zero h-scroll, all `toc2`/`ix` anchors resolve. `make_pdf.py`
    recreated for the Windows toolchain (it existed only on the old Linux box) and all
    three PDFs regenerated in place over the stale v2.11-era set, PyMuPDF-verified
    (167/84/131 pages, 612×792 pt).

- **Keeper's Table v1.2.1 — Copyedit pass over the UI (2026-07-12)** ("go over the user
  interface and correct any spelling or grammatical errors as if you were an English
  professor"). Reviewed every user-facing string in `MainForm.cs`, `Tabs.cs`, `Core.cs`,
  `Program.cs`, `README.md`, and `Data/tables_extra.json`, checking Reference-tab text
  against the books before touching it (book wording wins). Fixed:
  - *Recovering Nerve* (Reference): "…or a point of Grit each buy back a measure." had
    dropped the book's modal — restored "**can** each buy back a measure **of steadiness**"
    (with "or," the bare "each buy" is a subject–verb agreement error).
  - *Nonlethal* (Reference): "declare it before the roll; fists and clubs do so by
    default, most other arms take −2…" — "do so" pointed at "declare it" and the comma
    spliced two clauses. Now mirrors the book: "declare before the roll that you strike
    nonlethally; fists and a club do so by default; most other arms take −2…".
  - *Grit* (Reference): "act while Bleeding Out, or shrug a condition" — "Bleeding Out"
    is not a book term (the conditions are Bleeding/Dying) and "a condition" overstates
    the book's "a fright." Rewritten to the Player's Book Ch. II list (add 1d6 / re-roll /
    refuse to fall / shrug a fright / soften a crit fail). Matching fix to the Posse tab's
    Spend-Grit tooltip.
  - Dice-tab parse error: "try like 2d6+3" → "try something like 2d6+3."
  - Tracker empty-state: "pick a foe … or drop **them** in" → "drop **one** in"
    (pronoun agreement).
  - Encounter empty verdict still said creatures could only be added from the Bestiary
    tab (stale since the v1.2 on-tab picker) — now "add creatures above, or send them
    over from the Bestiary tab."
  - Status bar + README book versions were stale (v2.10/v2.2/v2.2 → v2.11/v2.3/v2.3).
  Book-extracted text (`creatures.json`, `tables.json`, Reference wording that matches
  the books) deliberately left as the books print it. Loop: build 0/0 → smoke 1360/1360 →
  publish → delivered `app/` + `source/` synced → zip rebuilt (68.9 MB) → launch-checked
  (no `startup-error.txt`). **Discovered while proofing:** the built books on disk are
  v2.11/v2.3/v2.3 with a feathering paginator that never made it back into the lean
  sources — see the ⚠️ OPEN ISSUE at the top of this doc.

- **Infrastructure — GitHub sync live (2026-07-12).** The project now lives in a **private**
  repo: https://github.com/cwgilgalad/blood-and-grit (account `cwgilgalad`, HTTPS). Local
  `main` tracks `origin/main`; auth is the GitHub CLI (`gh auth setup-git` wired
  `gh auth git-credential` in as git's credential helper for github.com, token in the Windows
  keyring, so headless pushes work). The **"BloodAndGrit AutoSync" scheduled task** (every
  30 min + at logon, running `autosync.ps1`) commits & pushes any local changes — so edits
  made on the laptop reach GitHub within half an hour with no manual step. `.gitignore`
  excludes regenerated build output, the ~160 MB delivered `app/` folder, the deliverable
  zip, and per-table runtime state (`session.json`); the lean sources, build scripts, books,
  and `KT/source` + `KT/smoke` are all tracked.

- **Keeper's Table v1.2 — Seven-tab feature pass** (the user's own wishlist: dice animation,
  bestiary pop-outs, a comprehensible Encounter tab, tracker foe dropdown, bigger generators,
  bigger reference, a clearer Session tab, then a logic review). All built, 1360/1360 smoke
  asserts green, and every feature launched and screenshot-verified on the Windows laptop:
  - **Dice tray** (Dice tab, above the roll log): every roll — expression, quick dice, d20
    check — tumbles owner-drawn dice for ~½ s and settles on the true per-die faces (new
    `Rules.RollExprFull` returns `(sides, value, sign)` per die; fonts cached, panel
    double-buffered; max face rings verdigris, a natural 1 rings red; 8 dice shown, "+N more").
  - **Bestiary pop-out windows**: double-click a creature → its own resizable, maximizable
    window with A−/A＋ text zoom and → Tracker; one window per creature (re-focused if open),
    cascade-placed; replaces the old single reused card, and the Tracker/Encounter
    double-click cards now use the same windows.
  - **Encounter tab de-mystified**: an "Add a creature" type-ahead picker (× N) on the tab
    itself, budget line reworded ("4 pts per soul in the posse (Posse tab)"), and an
    empty-state overlay that explains the whole loop (plan → verdict → Send all → Tracker).
    (The "can't add souls" confusion was real: adding lived only on the Bestiary tab.)
  - **Tracker Foe box**: the same type-ahead creature picker (× N) directly on the Tracker
    bar, so foes can be fielded without leaving the tab.
  - **Generators expanded**: new `Data/tables_extra.json` (merged after `tables.json` by the
    new `Db.MergeTables`, deliberately a separate file so book re-extraction can't clobber
    it) — new entries for all 13 simple tables (~10 towns, 24 NPC names, 8 wants, 8 tells,
    12 rumors, 8+8 trail, 8 plunder, 10 omens…) plus 2–6 new entries per terrain ground and
    4 new Hand-Behind-It villains, all in the book's voice and all naming real Bestiary
    creatures (smoke-asserted so the safe-table rule keeps firing).
  - **Reference doubled**: added the DC ladder, a turn in the Iron Code, Blood/Dying/Grievous
    Wounds + the d6 Lasting Injury table, the complete Appendix-B Conditions table,
    Recovering Nerve, and the Sign DC formula — all faithful to the books.
  - **Session tab**: "Stamp the date" ledger button, an always-visible explainer under
    Threads & clocks, trouble-pattern suggestions in the New-thread dialog, ✎ rename per
    clock, and the ledger title now admits it also autosaves every five minutes.
  - **Real layout bug found & fixed while verifying**: the top action bars (Bestiary
    filters, Posse, Encounter, Tracker) were fixed-height FlowLayoutPanels — at panel widths
    where the controls wrap to 3+ rows, the overflow row was silently clipped (the Bestiary's
    🎲 Random / → Encounter / → Tracker buttons were invisible at default window size). All
    four bars are now `AutoSize = true`.
  - Housekeeping: status bar book versions corrected to v2.10/v2.2/v2.2 (was stale at
    v2.9/v2.1), csproj `Version` 1.2.0, README rewritten for v1.2, smoke rig now loads
    `Data/` and rolls forward to the machine's .NET 9 runtime (`RollForward` — test rig
    only). **Note:** the delivered zip is fully v1.2; the unzipped
    `BloodAndGrit-Keepers-Table\app\` folder was still running v1.1 during the session, so
    a background waiter syncs it from `KT/source/publish` the moment that instance closes —
    if it didn't get the chance, re-copy `KT/source/publish\*` over `app\` by hand.

- **Player v2.10 / Keeper v2.2 / Bestiary v2.2 — Navigation + the sample county.** Three things,
  all built and render-verified on the Windows/Edge toolchain (`measure_book.py`, new general
  verifier; `measure_index.py` for the Player's Book):
  - **Detailed two-level Contents in all three books.** A shared `nav_tools.py:add_detailed_toc()`
    regenerates each book's simple chapter TOC into a flat, splittable `<ul class="toc2">` listing
    chapters + their `<h2>` sub-heads, generated from the assembled HTML at build time so it can
    never drift; page numbers resolve live. Two paginator facts pinned down doing this: `.toc`
    lists are deliberately *non-splittable* (they move whole — hence the new class `toc2`, which
    the split-fill code treats like the `.ix` index and flows across pages), and the paginator
    stamps a `<section>`'s id onto its *first block*, so a section-opening `<h2>` must be indexed by
    its section id, not a fresh one. Also corrected the clip test to force `zoom:1` on **each
    `.page`** (the note always said to; the script had been setting it on the container, which
    produced phantom ~20px "clips" on many-line TOC pages).
  - **Indexes for the Keeper's Book and Bestiary** (the Player's got one in v2.9), via
    `nav_tools.py:build_index()`. The Bestiary index auto-lists all 110 creatures (drift-proof) +
    curated terms; the Keeper index is curated craft/campaign/Perdition-Basin entries. New section
    `id="bookindex"` (the Bestiary's Roll-by-Tier appendix keeps `id="index"`).
  - **Perdition Basin — a worked sample county** (the biggest published-games gap on the old
    roadmap). One dry county whose spine is the padres' failing silver "nail" bindings on the wells
    (deliberately the Ch. XI Salt Valley seed, drawn out), with **Coffin Wells** (Ch. IX) and
    **Saltlick Station** (Ch. X) as two of its keyed sites. `perdition_map.py` draws a **two-layer
    inline-SVG map** from one coordinate model: a clean, secrets-free **player map** (Player's Book
    Appendix E, an in-world gazette) and a secrets-annotated **Keeper map** (Keeper's Book Ch. XIII,
    the full gazetteer — locations, three factions, the well-by-well campaign clock, ties to both
    adventures). The First Peoples (the Painted Mesa) are written as people with agency and
    grievance, not mystical props. Pages: Player 172→175, Keeper 77→89, Bestiary 133→136 (detailed
    TOC accounts for the first few pages each; the map/gazetteer for the Keeper's larger jump). All
    three pass parity / zero-clip / all-anchors-resolve / idempotent.

- **Keeper's Table v1.1 — Tracker/Posse flexibility pass** (in response to "more features on
  the GUI that make the program more flexible," with the Tracker's missing reset as the model).
  Added, all built and visually verified by launching the app natively on the user's Windows
  laptop (build clean 0/0; 930/930 headless logic assertions still green since `Core.cs` was
  untouched):
  - **Tracker "New fight"** — clears the foes, keeps the posse on the field, wipes per-fight
    conditions off the survivors, and resets to Round 1. This is the headline fix: "Clear field"
    (full wipe) was the only reset before, so you couldn't line up the next encounter without
    nuking and re-sending the party. Confirmed working on-screen (3 foes cleared, 2 PCs kept,
    Round 3→1, Frightened cleared).
  - **Flexible Sort ▾** — the old single "Sort" (always init-desc) is now a dropdown: Initiative
    high→low / low→high, Name A→Z / Z→A, Blood most→least / least→most. It commits any half-typed
    Init before sorting and refreshes the grid. The last mode sticks; "Roll initiative" forces
    init-desc.
  - **＋ Add** (Tracker) — an ad-hoc combatant/NPC dialog (name, Blood, Defense, PC? flag) for
    anything not in the Bestiary.
  - **× N quantity** on the Bestiary "→ Tracker" — drop several copies of a foe at once (numbered
    #1..#N; a lone first copy stays unnumbered, preserving prior behavior).
  - **＋ Condition ▾** (Tracker) — tag the selected combatant with any Appendix-B condition from a
    menu (Frightened/Slowed offer their steps; a valued step supersedes its siblings), plus a
    "— Clear all —" entry, instead of free-typing the Conditions cell.
  - **Rest ▾** (Posse) — a long rest restoring Blood **and** Nerve to full, whole-posse or
    selected soul (the old "New session" only did Nerve + Grit; Blood had no bulk restore).
  - Implementation: a shared `MenuBtn(text, w, tip, params (label, handler)[])` dropdown-button
    helper in `MainForm.cs` (a "-" label → separator) backs Sort, Condition, and Rest. The
    Tracker toolbar is now two rows (`SetFlowBreak`). Also fixed a stale status-bar string
    (Player's Book v2.8 → v2.9). **Discovered and reconciled a two-source-tree divergence** — see
    the Keeper's Table "Source-tree layout" note above; `KT/source` is now the single master and
    the delivered `BloodAndGrit-Keepers-Table/` + zip were regenerated from it (so the shipped
    build now also finally carries last session's uncommitted autosave-timer and two-tier
    crash-recovery work). Republished self-contained (win-x64, ~67 MB zip); published exe
    confirmed to launch standalone with no `startup-error.txt`.
- **Player v2.9 — Added the Index.** A full back-of-book index as a new section after The Ledger:
  ~200 entries (every rule concept, all 17 Callings, all 10 Origins, all 29 general Edges by name,
  all 8 Signs, all 5 Old Rites, all 14 relics/artifacts by name), two-column with letter heads and
  dotted leaders in the TOC's design language. Implementation: ~168 anchor ids (`ix-*`) added to
  headings, list items, and table rows across `player-src.html`; entries use the TOC's
  `<a href="#anchor">…</a><span class="pg">` structure, so **the existing paginator resolves every
  index page number live at render time** — no JS changes needed, and the numbers can never drift.
  A one-shot (`add_index.py`, kept, do-not-re-run) baked it all in with assert-guarded string
  edits. The extra Contents line overflowed the contents page (the paginator moves an unsplittable
  `.toc` list whole), fixed by tightening `.toc li` padding 2px — contents is one page again.
  Cascade done (`v2.8→v2.9` match strings in both other build scripts); Keeper/Bestiary rebuilt on
  the new shell and verified unchanged (74/132 pages as rendered here, covers still v2.1, no index
  leakage — note the Bestiary's own "Roll, by Tier" appendix has always used `id="index"`, which is
  fine since the Player index is spliced out of the other two books). Verified via headless Edge
  (`measure_index.py`, kept as a tool): 169/169 desktop/mobile page parity, 0 clipping at true
  scale, 0 h-scroll at natural zoom, no unresolved anchors, idempotent double-build. **Discovery
  worth keeping: pagination is environment-dependent** — the untouched v2.8 renders 164 pages on
  this Windows laptop vs 163 on the old Linux environment (one extra page inside Ch. XI; Keeper
  73→74, Bestiary 130→132 likewise) purely from platform font metrics. Live-resolved page numbers
  make this harmless; static fallbacks are approximate by design. Also this session: recreated the
  missing `build_player.py` on this machine (verified byte-identical output against the delivered
  v2.8 file) and installed real Python 3.12 + Playwright for the Windows toolchain.
- **Keeper's Table v1.0 — Ampersand mnemonic fix (first real visual verification pass).**
  Ran Claude Code CLI natively on the user's Windows laptop for the first time — built and
  actually launched the app, screenshotted all 8 tabs. Everything rendered correctly (palette,
  wiring, layout, DPI) except two labels that silently swallowed their `&`: WinForms treats a
  bare `&` in a `Label`/`GroupBox` `.Text` as a mnemonic-accelerator prefix (underlines the next
  letter, drops the `&`), so "Roll & event log" (Dice tab) rendered as "Roll  event log" and
  "Threads & clocks" (Session tab) rendered as "Threads _clocks." `Button.Text` has the same
  behavior, but the one existing button label with an ampersand ("Plunder & finds") had already
  been correctly escaped as `&&` — only the `Label` in `MainForm.cs` and the `GroupBox` in
  `Tabs.cs` had been missed. Fixed both by escaping to `&&`; re-verified both tabs render the
  ampersand correctly post-fix. Republished self-contained and re-zipped. No other layout/DPI
  issues found across the eight tabs.
- **Keeper's Table v1.0 — Crash fix.** A real Windows launch threw
  `SplitterDistance must be between Panel1MinSize and Width - Panel2MinSize` in
  `BuildDiceTab()`, immediately on startup — every tab using a `SplitContainer` had the same
  latent bug (geometry set before the control was laid out). Fixed by introducing a
  `Split()` helper that defers `SplitterDistance`/min-sizes to the control's first real
  `SizeChanged` event; applied to all four affected tabs (Dice, Bestiary, Generators,
  Session). Republished self-contained. This class of bug is now flagged as a standing
  landmine in this doc's Keeper's Table section so it isn't reintroduced.
- **Keeper's Table v1.0 — Full logic & UX audit** (in response to "check the logic, make
  sure the UI follows best practices, make sure everything is wired up"). Found and fixed
  real bugs: the four-degrees stepping logic had a signed-band gap at zero that made a
  natural 20 on a failing roll register as a *critical failure* instead of stepping up to
  success — rewritten on an ordered 0–3 scale with regression tests locking both edge
  cases. Made `PartyMember`/`Combatant`/`CampaignClock` implement
  `INotifyPropertyChanged` with clamped setters (Mark 0–6, Taint 0–4, Grit 0–9, Blood/Nerve
  ≥ 0) — they were plain classes in `BindingList`s before, so model edits made in code
  didn't reliably reach the grids. Added Nerve auto-recompute (`RES + level`). Made
  Tracker↔Posse Blood sync two-way (was one-way). UX rewrite: replaced blocking prompt
  dialogs for Damage/Heal/Dread with inline spinners on each tab's action bar; added
  danger-colour coding (Blood/Nerve amber under a third, red at zero; Mark/Taint as filled
  pips; downed/PC row tinting on the Tracker); confirmations on all destructive actions;
  numeric-cell input validation; Ctrl+1–8 tab shortcuts; Enter-to-roll; tooltips on every
  button; a themed New-Thread dialog with Cancel; an encounter-budget progress bar; and a
  consistent frontier-book palette replacing the plain spreadsheet look. Verified: clean
  build, 34/34 headless logic tests, static wiring audit (43 buttons, 10 inputs all
  confirmed connected).
- **Keeper's Table v1.0 — Initial build.** Built "Blood & Grit: The Keeper's Table," a
  C#/.NET 8 WinForms desktop app, from scratch: 8 tabs (Posse, Dice, Bestiary, Encounter,
  Tracker, Generators, Reference, Session), all 110 creatures and 22 tables extracted from
  the rendered books into JSON, session autosave/autoload, Appendix D pregens seeded on
  first run. Cross-compiled for `win-x64` using the official Microsoft .NET SDK (the Ubuntu
  apt package lacks WindowsDesktop targets). Delivered as a zip with a framework-dependent
  build; later republished self-contained (see the crash-fix entry above) after a user
  report showed the framework-dependent build wouldn't launch without the exact Desktop
  Runtime installed.
- **Keeper v2.1 / Bestiary v2.1 — Cross-book consistency audit.** Checked all rules numbers,
  creature references, chapter cross-references, and formulas across the three books. Fixed
  five inconsistencies: (1) Keeper's Alienist reference pointed at Ch. IX (Edges) — the
  Alienist is a Sawbones art, now cited as Player's Book Ch. V; (2) Keeper's Taint-clock
  reference said Chapter XIII — the Taint lives in Ch. XII (Nerve & the Uncanny); (3)
  Keeper's Threat-by-Tier Tier-I Dread cell said "—/10" while the Bestiary workshop and the
  actual stat blocks run — / 10–13, now aligned; (4) Grounds appendix "The Servant of the
  Deep Dark" → entry's real name "Servant of the Deep Dark"; (5) Grounds villain picker
  "The Hollow Prophet & his flock (III)" → the actual entry "Dark Cultist & the Hollow
  Prophet (II–III)". Verified consistent: Threat-by-Tier combat numbers, encounter budget
  (4 pts/PC; mook 1 / standout 8), Nerve = RES + level, Sign DC formula, Grit 3/session,
  Mark six steps, silver ammo in Ch. X, all 90 Grounds creature references, Bestiary→Keeper
  Ch. III/IV references, and the pregens' Signs. Page counts unchanged (73 / 130).
- **Bestiary v2.0 — Whitespace pass.** Registered `.creature` as a splittable block in
  `pag_patch.py` so creature entries flow continuously and split across page boundaries
  (with "(cont.)" headers, stat blocks kept intact, no orphaned headings). Bestiary
  148→130 pages; mean trailing whitespace 238→106px; big gaps 61→18 (mostly chapter-ends).
  Bestiary-only bump (no Player cascade). Keeper unaffected (no creature entries).
- **Player v2.8 / Keeper v2.0 / Bestiary v1.9 — Added more quotes.** Player: 4 new chapter
  epigraphs (III Making a Character, IX Edges, A Example of Play, B Conditions). Keeper:
  epigraph for the Screen appendix (added `screen` to `_chq`). Bestiary: 5 in-voice
  **witness quotes** on iconic creatures (Risen, Nightwalker, Skin-Walker, Thunderbird,
  Wendigo) via a new `witness=` param on `creature()`. Pages: Player 162→163, Bestiary
  143→148, Keeper 73. TOCs re-measured.
- **Player v2.7 / Keeper v1.9 / Bestiary v1.8 — Removed all 18 Player's Book plates** for
  cross-book design continuity (Player only; images retained unused in `assets/`). Player
  169→162 pages, ~5.4 MB→~0.40 MB.
- **Player v2.6 — Fixed Opal Vance** in the posse from Witch to **Hexer** (fits her Mark 1
  and bargain backstory); abilities/derived stats unchanged. Player only.
- **Player v2.5 / Keeper v1.9 / Bestiary v1.8 — Cover subtitle font** restyled to match the
  top kicker (EB Garamond small-caps, bold, upright, 24px). All three (shared shell).
- **Player v2.4 / Keeper v1.8 / Bestiary v1.7 — Removed the parchment page texture**
  (`img01.png`) from all three; pages now flat `--paper` + vignette. **Made the emblem's
  rifle-lever holes transparent.**
- **Player v2.3 / Keeper v1.7 / Bestiary v1.6 — Lowered/centered the cover emblem** in the
  blank lower cover area (flexbox `margin:auto`). All three (shared shell).
- **Player v2.2 / Keeper v1.6 / Bestiary v1.5 — Replaced the cover emblem** with
  `assets/img20.png` (raster steer-skull + crossed rifles, transparent background). All three.
- **Player v2.1 / Keeper v1.5 / Bestiary v1.4 — Re-laid-out the Player's 18 plates** for
  spacing (min gap 7, most 9–13) and thematic section fit.
- **Player v2.0 / Keeper v1.5 / Bestiary v1.4 — Playability pass.** Player: Appendix D
  pregens. Keeper: Ch. XII rollable tables (and Ch. XI Keeper's Year). Bestiary: The Grounds
  + Building Your Own Dead appendices, plus the creature-lore expansion to all 110 entries.

*Current as of the July 2026 sessions. Versions: **Player's Book v2.14 · Keeper's Book v2.6 ·
Bestiary v2.6 · The Keeper's Table app v1.2.3 (self-contained, crash-hardened).***
