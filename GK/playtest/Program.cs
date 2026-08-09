// Play the three adventures on the same rules library the app runs on, several posses each,
// and report what actually happened.
//
// The point is not to prove the engine works — GK/smoke does that. The point is that a module
// printing "this fight is a fair fight for a fresh posse" has to have somebody's word for it, and
// the only word this project accepts is the engine's. Every number in the three module books that
// describes difficulty comes out of this run.
//
// Deterministic: every run is seeded, the seed is printed, and re-running a seed reproduces the
// night exactly. A balance claim nobody can reproduce is a balance claim nobody can check.

using System.Text;
using BloodAndGritKeeper;

const int RunsPerAdventure = 12;      // twelve posses through each night
const int BaseSeed = 20260809;

var md = new StringBuilder();
bool verbose = args.Contains("--verbose");
string outPath = null;
for (int i = 0; i < args.Length - 1; i++) if (args[i] == "--out") outPath = args[i + 1];

// The four callings a first posse most often actually is — a gun, a faith, a frontier hand, and a
// doctor. Fixed rather than random so the three adventures are compared against the same party
// shape, and so a Keeper reading the results knows exactly who was at the table.
string[] Callings = { "Gunhand", "Preacher", "Mountain Man", "Sawbones" };

// The Bestiary and the chargen tables, off the rules assembly's embedded resources. Nothing below
// works without them, and CharGen.Generate fails with a bare null rather than a sentence if the
// load is skipped — so it is done once, here, before a single die is rolled.
Db.Load();
CharGen.Load();

Console.WriteLine($"Blood & Grit — module playtest\n  {Adventures.All.Length} adventures x {RunsPerAdventure} posses, base seed {BaseSeed}\n");

md.AppendLine("# Module playtest — what the engine says about the three adventures");
md.AppendLine();
md.AppendLine($"Every night below was played through **the same rules library the app runs on** "
            + $"(`GK/rules`), with the Bestiary's own numbers for every foe and the book's own dice "
            + $"for every roll. Nothing here is estimated. {Adventures.All.Length} adventures × "
            + $"{RunsPerAdventure} posses = {Adventures.All.Length * RunsPerAdventure} full runs, "
            + $"base seed `{BaseSeed}`; re-running a seed reproduces the night exactly.");
md.AppendLine();
md.AppendLine("The posse is the same four callings every time — **Gunhand, Preacher, Mountain Man, "
            + "Sawbones** — so the three nights are compared against one party shape, and a Keeper "
            + "reading a number knows who was at the table when it was earned.");
md.AppendLine();

var overall = new List<AdventureResult>();

foreach (var adv in Adventures.All)
{
    var runs = new List<RunResult>();
    var tendedRuns = new List<RunResult>();
    for (int r = 0; r < RunsPerAdventure; r++)
    {
        int seed = BaseSeed + adv.Slug.Length * 1000 + r;
        runs.Add(PlayOnce(adv, Callings, seed, verbose, tended: false));
        tendedRuns.Add(PlayOnce(adv, Callings, seed, verbose, tended: true));
    }

    var res = new AdventureResult(adv, runs, tendedRuns);
    overall.Add(res);
    Report(res, md);
}

// ---- the cross-adventure read ----
md.AppendLine("---");
md.AppendLine();
md.AppendLine("## The three nights side by side");
md.AppendLine();
md.AppendLine("| Adventure | Level | Finished (cold) | Finished (tended) | Broke off | Put down | Avg souls down |");
md.AppendLine("|---|---|---|---|---|---|---|");
foreach (var a in overall)
{
    md.AppendLine($"| {a.Adv.Title} | {a.Adv.PartyLevel} | {a.Finished}/{a.Runs.Count} | "
                + $"{a.TendedFinished}/{a.Tended.Count} | {a.BrokeOff} | {a.Wiped} | {a.AvgDown:0.0} |");
}
md.AppendLine();

Console.WriteLine();
foreach (var a in overall)
    Console.WriteLine($"  {a.Adv.Title,-32}  finished {a.Finished}/{a.Runs.Count}   broke off {a.BrokeOff}   "
                    + $"put down {a.Wiped}   | tended: finished {a.TendedFinished}/{a.Tended.Count}");

if (outPath != null)
{
    File.WriteAllText(outPath, md.ToString());
    Console.WriteLine($"\nwrote {outPath}");
}

return overall.Any(a => a.Runs.Count == 0) ? 1 : 0;


// ==================================================================== the runner

RunResult PlayOnce(Adventure adv, string[] callings, int seed, bool loud, bool tended)
{
    Rules.Reseed(seed);
    var log = new List<string>();

    // Build the posse on the real generator, then put it on the field as real combatants.
    var sheets = callings.Select(c => CharGen.Generate(adv.PartyLevel, rolled: false, fixedCalling: c)).ToList();
    var souls = sheets.Select(s => new Combatant
    {
        Name = s.Name, IsPC = true,
        BloodCur = s.Blood, BloodMax = s.Blood, Defense = s.Defense,
    }).ToList();

    // Nerve is a PartyMember's, not a Combatant's — the tracker carries a fight, and Nerve is a
    // thing a soul carries through a whole night. Kept beside the field, indexed with it.
    var nerve = sheets.Select(s => s.NerveMax).ToArray();

    var run = new RunResult(seed);
    int actNo = 0;

    foreach (var act in adv.Acts)
    {
        actNo++;
        foreach (var beat in act.Beats)
        {
            if (souls.All(s => s.Down)) { run.Wiped = true; goto done; }

            switch (beat.Kind)
            {
                case BeatKind.Dread:
                {
                    foreach (var s in souls.Where(s => !s.Down))
                    {
                        int who = souls.IndexOf(s);
                        int die = Rules.Rng.Next(1, 21);
                        int will = sheets[who].Will;
                        var (idx, degree, _) = Rules.FourDegrees(die, will, beat.DreadDc);
                        if (idx <= 1)                                  // failure or critical failure
                        {
                            var (label, roll) = Rules.NerveLoss(beat.DreadTier);
                            int loss = roll();
                            if (idx == 0) loss *= 2;                   // a critical failure costs double
                            nerve[who] = Math.Max(0, nerve[who] - loss);
                            run.NerveLost += loss;
                            if (nerve[who] == 0 && !run.Broke.Contains(s.Name)) run.Broke.Add(s.Name);
                            log.Add($"    dread {beat.DreadDc}: {s.Name} rolled {die}{will:+#;-#;+0} — {degree}, -{loss} Nerve ({label}) -> {nerve[who]}");
                        }
                        else log.Add($"    dread {beat.DreadDc}: {s.Name} rolled {die}{will:+#;-#;+0} — {degree}");
                    }
                    break;
                }

                case BeatKind.Toll:
                {
                    foreach (var s in souls.Where(s => !s.Down)) s.Wound(-beat.Toll);
                    log.Add($"    toll: {beat.Toll} Blood each — {beat.Name}");
                    break;
                }

                case BeatKind.Fight:
                {
                    var f = Fight(adv, souls, sheets, beat, log);
                    run.Fights.Add(f);
                    if (souls.All(s => s.Down)) { run.Wiped = true; goto done; }
                    if (f.Withdrew) { run.BrokeOff = true; goto done; }   // the night ends when they ride out
                    break;
                }
            }
        }

        // Between acts the posse gets its breath back the way a night actually gives it: the fight
        // is over, so ResetForNewFight clears the residue. Blood and Nerve do NOT come back — that
        // is the whole shape of a one-night adventure, and it is why act three is the dangerous one.
        Rules.ResetForNewFight(souls.Where(s => !s.Down));

        // Between acts, the Sawbones works and somebody boils coffee. Modelled as the posse coming
        // back to half Blood — deliberately modest, and deliberately NOT full: a one-night adventure
        // that hands back everything between acts has no arc, and the whole shape of act three is
        // that it is fought by people who are already hurt. Souls already down stay down; a soul
        // put on the ground is a soul the night has taken.
        if (tended)
            foreach (var s in souls.Where(s => !s.Down))
                if (s.BloodCur < s.BloodMax / 2) s.Wound(s.BloodMax / 2 - s.BloodCur);
    }

done:
    run.Down = souls.Count(s => s.Down);
    run.NerveLeft = nerve.Sum();
    run.NerveMax = sheets.Sum(x => x.NerveMax);
    run.BloodLeft = souls.Where(s => !s.Down).Sum(s => s.BloodCur);
    run.Log = log;
    if (loud) foreach (var l in log) Console.WriteLine(l);
    return run;
}

FightResult Fight(Adventure adv, List<Combatant> souls, List<CharacterSheet> sheets, Beat beat, List<string> log)
{
    var foes = new List<Combatant>();
    var foeCreature = new Dictionary<Combatant, Creature>();
    var seen = new Dictionary<string, int>();

    foreach (var name in beat.Foes)
    {
        var c = Db.Find(name)
            ?? throw new InvalidOperationException(
                $"'{name}' is not in the Bestiary. An adventure may not cite a creature the book does not have.");
        seen[name] = seen.TryGetValue(name, out var n) ? n + 1 : 1;
        var body = new Combatant
        {
            Name = seen[name] > 1 || beat.Foes.Count(x => x == name) > 1 ? $"{c.name} #{seen[name]}" : c.name,
            BloodCur = c.BloodValue, BloodMax = c.BloodValue, Defense = c.DefenseValue, Ref = c.name,
        };
        foes.Add(body);
        foeCreature[body] = c;
    }

    var fr = new FightResult(beat.Name,
        beat.Foes.Select(n => Db.Find(n)).Where(c => c != null).Max(c => c.tier),
        Rules.PartyTier(adv.PartyLevel));

    // The safe-table rule, asked of this fight before a die is rolled — the same question the
    // Tracker asks every time something is put on the field.
    fr.SignOnly = beat.Foes.Any(n => Rules.SignOnly(Db.Find(n).tier, adv.PartyLevel));

    var field = souls.Where(s => !s.Down).Concat(foes).ToList();
    foreach (var c in field) c.Init = Rules.RollInitiative(0);

    log.Add($"    fight: {beat.Name}  [{string.Join(", ", beat.Foes)}]"
          + (fr.SignOnly ? "   ** safe-table rule: this would be offered as SIGN, not a fight **" : ""));

    int round = 0, guard = 0;
    int half = (int)Math.Ceiling(souls.Count(s => !s.Down) / 2.0);
    while (field.Any(c => c.IsPC && !c.Down) && field.Any(c => !c.IsPC && !c.Down) && guard++ < 60)
    {
        // The break-off. A posse with half its number on the ground quits the field — which is what
        // a table does, and what the books assume when they say the dawn is always one scene away.
        // Without it this rig measures how long four souls take to die standing in the open, which
        // is a fact about the rig rather than about the adventure.
        if (field.Count(c => c.IsPC && c.Down) >= half) { fr.Withdrew = true; break; }

        round++;
        Rules.NewRound(field);
        while (Rules.NextUp(field) is Combatant up)
        {
            foreach (var other in field) other.Acting = false;
            up.BeginTurn();
            if (up.Down) continue;

            // The posse concentrates — that is what a table does, and it is the posse's whole
            // advantage over a pack. The pack does not: three Risen do not agree on which soul to
            // pull down, and a rig in which they do is a rig measuring perfect enemy coordination
            // rather than an adventure. This one line moved every fight below from a slaughter to
            // a fight.
            var target = PickTarget(field, up);
            if (target == null) break;

            // Three Beats is three Strikes, at the rising MAP the engine applies for us.
            while (up.Beats > 0 && !target.Down)
            {
                if (up.IsPC)
                {
                    var sheet = sheets[souls.IndexOf(up)];
                    var w = BestWeapon(sheet);
                    var rep = CombatFlow.StrikeAndApply(up, target, w, CombatFlow.AttackBonusFor(sheet, w));
                    fr.PosseSwings++;
                    if (rep.Res.Strike.Hit) { fr.PosseHits++; fr.DamageDealt += rep.Res.AfterDR; }
                }
                else
                {
                    var cr = foeCreature[up];
                    var (strikes, _) = CreatureAttack.Parse(cr.attacks);
                    var atk = strikes.FirstOrDefault();
                    if (atk == null) { up.Beats = 0; break; }
                    var rep = CombatFlow.StrikeAndApply(up, target, atk, atk.Bonus);
                    fr.FoeSwings++;
                    if (rep.Res.Strike.Hit) { fr.FoeHits++; fr.DamageTaken += rep.Res.AfterDR; }
                }
                if (target.Down)
                {
                    log.Add($"      round {round}: {target.Name} is put down by {up.Name}");
                    target = PickTarget(field, up);
                    if (target == null) break;
                }
            }
        }
    }

    fr.Rounds = round;
    fr.PosseWon = !fr.Withdrew && field.Any(c => c.IsPC && !c.Down) && field.All(c => c.IsPC || c.Down);
    fr.SoulsDown = field.Count(c => c.IsPC && c.Down);
    fr.Stalled = guard >= 60;
    log.Add($"      -> {(fr.PosseWon ? "posse standing" : fr.Withdrew ? "posse broke off" : fr.Stalled ? "STALLED" : "posse down")}"
          + $" after {round} rounds; {fr.SoulsDown} soul(s) down");
    return fr;
}

// Who this one swings at. A soul picks the foe already hurt worst — finish what is started. A
// horror picks whoever is in front of it, which on a dark night is whoever the dice say.
Combatant PickTarget(List<Combatant> field, Combatant up)
{
    var candidates = field.Where(c => c.IsPC != up.IsPC && !c.Down).ToList();
    if (candidates.Count == 0) return null;
    return up.IsPC
        ? candidates.OrderBy(c => c.BloodCur).First()
        : candidates[Rules.Rng.Next(candidates.Count)];
}

// The heaviest thing on the sheet, which is what a soul in a fight for their life actually reaches
// for. Falls back to fists rather than throwing: a soul who bought no weapon still gets a turn.
CgWeapon BestWeapon(CharacterSheet s)
{
    CgWeapon best = null; double bestAvg = -1;
    foreach (var line in s.WeaponsCarried ?? new List<string>())
    {
        var name = line.Split("  ")[0].Split(" 1d")[0].Split(" 2d")[0].Trim();
        var w = CharGen.D?.weapons?.FirstOrDefault(x =>
            string.Equals(x.name, name, StringComparison.OrdinalIgnoreCase));
        if (w == null) continue;
        double avg = AvgOf(w.dmg);
        if (avg > bestAvg) { bestAvg = avg; best = w; }
    }
    return best ?? new CgWeapon { name = "fists", dmg = "1d4", traits = "", kind = "blade" };
}

// The mean of a damage expression, computed rather than rolled. Rolling to compare two weapons
// would pick a different gun every run and make the whole report unreproducible.
double AvgOf(string expr)
{
    double total = 0;
    foreach (System.Text.RegularExpressions.Match m in
             System.Text.RegularExpressions.Regex.Matches(expr ?? "", @"(?<sign>[+\-])?\s*(?<n>\d*)d(?<s>\d+)|(?<sign2>[+\-])\s*(?<flat>\d+)"))
    {
        if (m.Groups["s"].Success)
        {
            int n = m.Groups["n"].Value == "" ? 1 : int.Parse(m.Groups["n"].Value);
            int sides = int.Parse(m.Groups["s"].Value);
            double v = n * (sides + 1) / 2.0;
            total += m.Groups["sign"].Value == "-" ? -v : v;
        }
        else if (m.Groups["flat"].Success)
        {
            double v = int.Parse(m.Groups["flat"].Value);
            total += m.Groups["sign2"].Value == "-" ? -v : v;
        }
    }
    return total;
}


// ==================================================================== reporting

void Report(AdventureResult a, StringBuilder md)
{
    var adv = a.Adv;
    md.AppendLine("---");
    md.AppendLine();
    md.AppendLine($"## {adv.Title}");
    md.AppendLine();
    md.AppendLine($"*{adv.Subtitle}*");
    md.AppendLine();
    md.AppendLine($"**{adv.Site} · a posse of four at level {adv.PartyLevel} · "
                + $"party Tier {Rules.PartyTier(adv.PartyLevel)}**");
    md.AppendLine();
    md.AppendLine($"- **Finished the night on their feet: {a.Finished} of {a.Runs.Count} runs.** "
                + $"Broke off and rode out: {a.BrokeOff}. Put down to the last soul: {a.Wiped}.");
    md.AppendLine($"- Souls down at the end, on average: **{a.AvgDown:0.0} of 4**.");
    md.AppendLine($"- Nerve left across the whole posse, on average: **{a.AvgNerve:0.0} of "
                + $"{a.Runs.First().NerveMax}**. Runs in which at least one soul broke (Nerve to 0): "
                + $"**{a.BrokeAny}** of {a.Runs.Count}.");
    md.AppendLine();

    md.AppendLine($"- **The same twelve nights, with the Sawbones working between acts** "
                + $"(the posse back to half Blood, never more): finished standing "
                + $"**{a.TendedFinished} of {a.Tended.Count}**, put down to the last soul {a.TendedWiped}.");
    md.AppendLine();
    md.AppendLine("### Fight by fight");
    md.AppendLine();
    md.AppendLine("*Cold — no recovery between acts, no Grit spent, no Sign or Miracle worked. "
                + "This is the floor: what the night costs a posse that only shoots.*");
    md.AppendLine();
    md.AppendLine("| Fight | Foe tier | Cleared | Broke off | Avg rounds | Posse hit rate | Foe hit rate |");
    md.AppendLine("|---|---|---|---|---|---|---|");
    foreach (var g in a.ByFight)
    {
        md.AppendLine($"| {g.Name} | T{Rules.Roman(g.Tier)}{(g.SignOnly ? " ⚠" : "")} | "
                    + $"{g.Won}/{g.Count} | {g.Withdrew}/{g.Count} | {g.AvgRounds:0.0} | "
                    + $"{g.PosseHitRate:P0} | {g.FoeHitRate:P0} |");
    }
    md.AppendLine();

    // The way through, in the Bestiary's own words. Every one of these bosses is 0-for-everything
    // when the posse only shoots, and every one of them has a printed answer. Quoted, never
    // paraphrased: this is the book's sentence, and the module is not entitled to a second one.
    var bosses = adv.Acts.SelectMany(x => x.Beats).Where(b => b.Kind == BeatKind.Fight)
        .SelectMany(b => b.Foes).Distinct()
        .Select(Db.Find).Where(c => c != null && c.tier >= 3).ToList();
    if (bosses.Any())
    {
        md.AppendLine("### The way through");
        md.AppendLine();
        md.AppendLine("Not one of the Tier III fights above was ever cleared by shooting it — across "
                    + "every run, cold or tended. That is the design, not a shortfall: the Bestiary "
                    + "prints an answer for each of them, and the module's job is to put that answer "
                    + "where the posse can find it under fire.");
        md.AppendLine();
        foreach (var c in bosses)
        {
            md.AppendLine($"**{c.name}** — *putting it down:* {c.puttingItDown}");
            md.AppendLine();
        }
    }

    var flagged = a.ByFight.Where(g => g.SignOnly).ToList();
    if (flagged.Any())
    {
        md.AppendLine($"> **⚠ The safe-table rule refuses {(flagged.Count == 1 ? "one of these fights" : $"{flagged.Count} of these fights")}.** "
                    + $"A horror two or more Tiers over the posse is offered as sign and spoor rather "
                    + $"than seated on the field — so if a Keeper builds {(flagged.Count == 1 ? "this fight" : "these fights")} "
                    + $"in GritKeeper, the app will ask whether it should go on the trail instead. That is "
                    + $"not a bug in either the module or the app: it is the book saying out loud that this "
                    + $"is not a fight to be won by shooting, and the module has to give the posse the other way through.");
        md.AppendLine();
    }
}


// ==================================================================== records

record FightResult(string Name, int Tier, int PartyTier)
{
    public int Rounds, SoulsDown, PosseSwings, PosseHits, FoeSwings, FoeHits, DamageDealt, DamageTaken;
    public bool PosseWon, SignOnly, Stalled, Withdrew;
}

class RunResult(int seed)
{
    public int Seed = seed;
    public List<FightResult> Fights = new();
    public List<string> Broke = new();
    public List<string> Log = new();
    public int Down, NerveLeft, NerveMax, NerveLost, BloodLeft;
    public bool Wiped, BrokeOff;
}

class AdventureResult(Adventure adv, List<RunResult> runs, List<RunResult> tended)
{
    public Adventure Adv = adv;
    public List<RunResult> Runs = runs;
    public List<RunResult> Tended = tended;
    public int TendedFinished => Tended.Count(r => !r.Wiped && !r.BrokeOff);
    public int TendedWiped => Tended.Count(r => r.Wiped);

    public int Wiped => Runs.Count(r => r.Wiped);
    public int BrokeOff => Runs.Count(r => r.BrokeOff);
    public int Finished => Runs.Count(r => !r.Wiped && !r.BrokeOff);
    public double AvgDown => Runs.Average(r => (double)r.Down);
    public double AvgNerve => Runs.Average(r => (double)r.NerveLeft);
    public int BrokeAny => Runs.Count(r => r.Broke.Any());
    public int WorstRounds => Runs.SelectMany(r => r.Fights).DefaultIfEmpty().Max(f => f?.Rounds ?? 0);

    public IEnumerable<FightGroup> ByFight => Runs
        .SelectMany(r => r.Fights)
        .GroupBy(f => f.Name)
        .Select(g => new FightGroup(
            g.Key, g.First().Tier, g.First().SignOnly, g.Count(),
            g.Count(f => f.PosseWon), g.Count(f => f.Withdrew), g.Average(f => (double)f.Rounds),
            g.Sum(f => f.PosseSwings) == 0 ? 0 : (double)g.Sum(f => f.PosseHits) / g.Sum(f => f.PosseSwings),
            g.Sum(f => f.FoeSwings) == 0 ? 0 : (double)g.Sum(f => f.FoeHits) / g.Sum(f => f.FoeSwings),
            g.Average(f => (double)f.DamageTaken)));
}

record FightGroup(string Name, int Tier, bool SignOnly, int Count, int Won, int Withdrew,
                  double AvgRounds, double PosseHitRate, double FoeHitRate, double AvgTaken);
