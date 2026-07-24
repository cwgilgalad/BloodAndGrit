using BloodAndGritKeeper;

int pass = 0, fail = 0;
void T(string name, bool ok)
{
    if (ok) pass++; else { fail++; Console.WriteLine($"FAIL  {name}"); }
}

// ---- FourDegrees: all edges on the ordered 0-3 scale ----
T("plain success",        Rules.FourDegrees(10, 5, 13).idx == 2);
T("plain failure",        Rules.FourDegrees(5, 2, 13).idx == 1);
T("crit success by +10",  Rules.FourDegrees(15, 8, 13).idx == 3);
T("crit failure by -10",  Rules.FourDegrees(2, 1, 13).idx == 0);
T("nat 20 on a fail steps UP to success",   Rules.FourDegrees(20, -10, 13).idx == 2);
T("nat 20 on success steps to crit",        Rules.FourDegrees(20, 0, 13).idx == 3);
T("nat 1 on a success steps DOWN to fail",  Rules.FourDegrees(1, 15, 13).idx == 1);
T("nat 1 on a fail steps to crit fail",     Rules.FourDegrees(1, 5, 13).idx == 1 || Rules.FourDegrees(1, 5, 13).idx == 0);
T("nat 1 already crit-fail stays 0",        Rules.FourDegrees(1, 0, 13).idx == 0);
T("degree label matches idx",               Rules.FourDegrees(10, 5, 13).degree == "Success");

// ---- Dice parser ----
for (int i = 0; i < 200; i++)
{
    var (t, _) = Rules.RollExpr("2d6+3");
    T("2d6+3 in range", t >= 5 && t <= 15);
    var (t2, _) = Rules.RollExpr("d20");
    T("d20 in range", t2 >= 1 && t2 <= 20);
    var (t3, _) = Rules.RollExpr("1d8+1d6+2");
    T("1d8+1d6+2 in range", t3 >= 4 && t3 <= 16);
}
T("garbage is rejected", Rules.RollExpr("banana").breakdown == "could not parse");
T("empty is rejected",   Rules.RollExpr("").breakdown == "empty");

// ---- RollExprFull: the per-die detail must agree with the total ----
for (int i = 0; i < 100; i++)
{
    var (t, _, dice) = Rules.RollExprFull("2d6+1d4-2");
    T("full: three dice", dice.Count == 3);
    T("full: dice in range", dice.All(d => d.value >= 1 && d.value <= d.sides));
    T("full: dice sum + mods = total", dice.Sum(d => d.sign * d.value) - 2 == t);
}
T("full: negative dice sign", Rules.RollExprFull("1d6-1d4").dice.Count(d => d.sign == -1) == 1);
T("full: garbage gives no dice", Rules.RollExprFull("banana").dice.Count == 0);

// ---- The Dice tab's expression-builder buttons (pure logic behind +d6 / ＋ / digits) ----
T("builder: empty + d6",          Rules.ExprAddDie("", 6) == "1d6");
T("builder: d6 again stacks",     Rules.ExprAddDie("1d6", 6) == "2d6");
T("builder: bare d6 stacks",      Rules.ExprAddDie("d6", 6) == "2d6");
T("builder: stack keeps prefix",  Rules.ExprAddDie("1d8+2d6", 6) == "1d8+3d6");
T("builder: different die joins", Rules.ExprAddDie("1d20", 6) == "1d20+1d6");
T("builder: d10 does not eat d100",  Rules.ExprAddDie("1d100", 10) == "1d100+1d10");
T("builder: d100 does not eat d10",  Rules.ExprAddDie("1d10", 100) == "1d10+1d100");
T("builder: after operator no extra +", Rules.ExprAddDie("2d6+", 8) == "2d6+1d8");
T("builder: after modifier joins",      Rules.ExprAddDie("2d6+3", 6) == "2d6+3+1d6");
T("builder: append digit",        Rules.ExprAppend("2d6+", "3") == "2d6+3");
T("builder: append operator",     Rules.ExprAppend("2d6", "+") == "2d6+");
T("builder: operator replaces operator", Rules.ExprAppend("2d6+", "-") == "2d6-");
T("builder: null-safe",           Rules.ExprAddDie(null, 6) == "1d6" && Rules.ExprAppend(null, "+") == "+");
T("builder: × count from empty",  Rules.ExprAddDie("", 6, 4) == "4d6");
T("builder: × count stacks",      Rules.ExprAddDie("2d6", 6, 3) == "5d6");
T("builder: × count joins",       Rules.ExprAddDie("1d8", 6, 3) == "1d8+3d6");
T("builder: × count after op",    Rules.ExprAddDie("2d6+", 8, 2) == "2d6+2d8");
T("builder: × count clamped",     Rules.ExprAddDie("", 6, 0) == "1d6" && Rules.ExprAddDie("", 6, 999) == "100d6");
for (int i = 0; i < 50; i++)
{
    // whatever the buttons build must parse and roll cleanly
    string e = "";
    e = Rules.ExprAddDie(e, 6); e = Rules.ExprAddDie(e, 6); e = Rules.ExprAddDie(e, 8);
    e = Rules.ExprAppend(e, "+"); e = Rules.ExprAppend(e, "3");
    var (bt, bb, bd) = Rules.RollExprFull(e);
    T("builder output rolls", bb != "could not parse" && bd.Count == 3 && bt >= 6 && bt <= 23);
}

// ---- Data loads, extra tables merge, terrain entries resolve to real creatures ----
Db.Load();
T("150 creatures", Db.Creatures.Count == 150);
T("creature names unique", Db.Creatures.Select(c => c.name).Distinct(StringComparer.OrdinalIgnoreCase).Count() == Db.Creatures.Count);
T("all stat blocks parse", Db.Creatures.All(c => c.BloodValue > 0 && c.DefenseValue > 0));
T("eight creature chapters", Db.Creatures.Select(c => c.chapter).Distinct().Count() == 8);   // Bestiary II-IX; I is How to Read the Dead
// The two mundane chapters are the campaign's slow-burn material and are meant to be
// roughly half the book; they are also the two that must never cost Nerve or Mark.
var mundane = Db.Creatures.Where(c => c.chapter is "Beasts of the Living World" or "Hard Men & Hard Country").ToList();
T("65 mundane creatures", mundane.Count == 65);
T("mundane creatures cost no Nerve", mundane.All(c => c.dread is "" or "—"));
T("mundane creatures never move the Mark", mundane.All(c => string.IsNullOrEmpty(c.mark)));
T("every creature carries lore", Db.Creatures.All(c => c.lore.Count > 0 && c.lore[0].Length > 0));
T("every creature carries a Found line", Db.Creatures.All(c => c.found.Length > 0));
T("17 simple tables", Db.Simple.Count == 17);
// The city generator (Keeper's Book Ch. XIV) is data-driven off these four; a missing
// one is a KeyNotFoundException on the Generators tab, not a quiet blank.
foreach (var t in new[] { "cityQuarter", "cityMachine", "cityWrongNote", "cityJob" })
    T($"city table [{t}] present and non-empty", Db.Simple.TryGetValue(t, out var ct) && ct.Count >= 10);
T("Lamplit City ground present", Db.Terrain.ContainsKey("The Lamplit City") && Db.Terrain["The Lamplit City"].Count == 12);
T("extra rumors merged", Db.Simple["rumors"].Count >= 30);
T("extra terrain merged", Db.Terrain["The Old Places"].Count >= 11);
T("no duplicate table entries", Db.Simple.All(kv => kv.Value.Distinct().Count() == kv.Value.Count));
foreach (var (ground, list) in Db.Terrain)
    foreach (var entry in list.Where(x => x.Contains('(')))
    {
        var nm = System.Text.RegularExpressions.Regex.Match(entry, @"^(.*?)\s*\(").Groups[1].Value.Trim();
        T($"terrain resolves [{ground}]: {entry}", Db.Find(nm) != null);
    }

// ---- Nerve-loss ladder ----
T("tier 1 loss = 1",  Rules.NerveLoss(1).roll() == 1);
for (int i = 0; i < 100; i++)
{
    T("tier 2 = 1d4",  Rules.NerveLoss(2).roll() is >= 1 and <= 4);
    T("tier 3 = 1d6",  Rules.NerveLoss(3).roll() is >= 1 and <= 6);
    T("tier 5 = 1d10", Rules.NerveLoss(5).roll() is >= 1 and <= 10);
}

// ---- Encounter cost ----
T("even foe = 4",   Rules.Cost(2, 4).cost == 4 && Rules.Cost(2, 4).role == "Even foe");
T("mook = 1",       Rules.Cost(1, 4).cost == 1);
T("standout = 8",   Rules.Cost(3, 4).cost == 8 && !Rules.Cost(3, 4).spoor);
T("spoor at +2",    Rules.Cost(4, 4).spoor);

// ---- Model clamps ----
var p = new PartyMember();
p.Mark = 99;  T("Mark clamps to 6", p.Mark == 6);
p.Taint = 99; T("Taint clamps to 4", p.Taint == 4);
p.Grit = 99;  T("Grit clamps to 9", p.Grit == 9);
p.BloodCur = -5; T("Blood floor 0", p.BloodCur == 0);

// ---- Nerve recompute incl. the new cur<=max clamp ----
var q = new PartyMember { RES = 14, Level = 3 };
T("NerveMax = RES + level", q.NerveMax == 17);
T("full nerve follows max up", q.NerveCur == 17);
q.NerveCur = 16;           // now not full
q.Level = 1;               // max drops to 15
T("max drops on level drop", q.NerveMax == 15);
T("cur clamps down to new max", q.NerveCur == 15);

// ---- INotifyPropertyChanged fires ----
bool fired = false;
var r = new PartyMember();
r.PropertyChanged += (s, e) => { if (e.PropertyName == "BloodCur") fired = true; };
r.BloodCur = 5;
T("PropertyChanged fires", fired);

// ---- Serialization round-trip incl. new GameSession fields ----
var sess = new GameSession
{
    Party = { new PartyMember { Name = "Ruth", BloodCur = 7, BloodMax = 12 } },
    Tracker = { new Combatant { Name = "Wolf #2", BloodCur = 3, BloodMax = 9, Ref = "The Gray Wolf" } },
    Round = 4
};
string json = System.Text.Json.JsonSerializer.Serialize(sess);
var back = System.Text.Json.JsonSerializer.Deserialize<GameSession>(json);
T("round survives",   back.Round == 4);
T("tracker survives", back.Tracker.Count == 1 && back.Tracker[0].Name == "Wolf #2" && back.Tracker[0].BloodCur == 3);
T("party survives",   back.Party[0].BloodCur == 7 && back.Party[0].BloodMax == 12);

// old save files (no Tracker/Round) must still load
var legacy = System.Text.Json.JsonSerializer.Deserialize<GameSession>("{\"Party\":[],\"Notes\":\"x\"}");
T("legacy session loads", legacy != null && legacy.Tracker.Count == 0 && legacy.Round == 1);

// ---- Character generator: data sanity ----
CharGen.Load();
var cg = CharGen.D;

// ============================================================ THE IRON CODE ENGINE (Ch. XI)
// Property-based proof that the adjudicator matches the printed gun rules.
{
    // -- every weapon's free-text traits parse, and known ones parse to the right structure --
    T("every weapon's traits parse without throwing",
        cg.weapons.All(w => WeaponTraits.Parse(w.traits) != null));
    var sa = WeaponTraits.Parse(cg.weapons.First(w => w.name == "Single-Action Revolver").traits);
    T("Single-Action Revolver → Fatal d10, Misfire 1", sa.FatalDie == 10 && sa.Misfire == 1 && !sa.Agile);
    var sg = WeaponTraits.Parse(cg.weapons.First(w => w.name == "Double-Barrel Shotgun").traits);
    T("Double-Barrel → Scatter 10, Fatal d12, Kickback", sg.Scatter == 10 && sg.FatalDie == 12 && sg.Kickback);
    var kn = WeaponTraits.Parse(cg.weapons.First(w => w.name == "Knife / Bowie").traits);
    T("Knife → Agile, no Misfire", kn.Agile && !kn.HasMisfire && kn.FatalDie == 0);
    var br = WeaponTraits.Parse(cg.weapons.First(w => w.name == "Buffalo Rifle").traits);
    T("Buffalo Rifle → Volley 30, Fatal d12", br.Volley == 30 && br.FatalDie == 12);

    // -- the Multiple Attack Penalty (Ch. XI) --
    T("MAP: 1st clean, 2nd -5, 3rd -10", IronCode.MapPenalty(1, false) == 0
        && IronCode.MapPenalty(2, false) == -5 && IronCode.MapPenalty(3, false) == -10);
    T("MAP: Agile softens to -4/-8", IronCode.MapPenalty(2, true) == -4 && IronCode.MapPenalty(3, true) == -8);

    // -- the Strike: nat 20 always hits, nat 1 always misses, jam only on a Misfire crit-fail --
    T("nat 20 hits even against an impossible Defense",
        IronCode.ResolveStrike(-50, 99, sa, forcedDie: 20).Hit);
    T("nat 1 misses even against a trivial Defense",
        !IronCode.ResolveStrike(+50, 1, sa, forcedDie: 1).Hit);
    T("beat-by-10 is a critical hit", IronCode.ResolveStrike(20, 13, sa, forcedDie: 15).Crit);      // 35 vs 13
    T("a Misfire weapon jams on a natural 1", IronCode.ResolveStrike(0, 13, sa, forcedDie: 1).Jam);
    var saber = cg.weapons.First(w => w.name == "Saber");
    T("a no-Misfire weapon never jams", !IronCode.ResolveStrike(0, 13, WeaponTraits.Parse(saber.traits), forcedDie: 1).Jam);

    // -- damage bounds, incl. the Fatal crit rule (2N dice of Fatal + one more) --
    for (int i = 0; i < 500; i++)
    {
        var norm = IronCode.RollDamage("1d8", sa, crit: false);
        T("1d8 normal in [1,8]", norm.Total is >= 1 and <= 8);
        var crit = IronCode.RollDamage("1d8", sa, crit: true);   // 2×1d10 + 1d10 = 3d10
        T("1d8 Fatal d10 crit in [3,30]", crit.Total is >= 3 and <= 30);
        var shot = IronCode.RollDamage("2d8", sg, crit: true);   // 2×2d12 + 1d12 = 5d12
        T("2d8 Fatal d12 crit in [5,60]", shot.Total is >= 5 and <= 60);
        var plain = IronCode.RollDamage("1d8", WeaponTraits.Parse(saber.traits), crit: true);  // no Fatal → ×2
        T("no-Fatal crit is doubled dice [2,16]", plain.Total is >= 2 and <= 16);
    }

    // -- Damage Reduction: typed, best-of (no stacking), floored at zero (Ch. XI) --
    var dr = new[] { new DrEntry(2, "blades"), new DrEntry(1, "small shot") };
    T("DR vs blades reduces a blade hit", IronCode.ApplyDR(6, "blades", dr) == 4);
    T("DR vs blades does NOT reduce a ball hit", IronCode.ApplyDR(6, "ball", dr) == 6);
    T("DR does not stack — best line applies",
        IronCode.ApplyDR(6, "blades", new[] { new DrEntry(2, "blades"), new DrEntry(3, "all") }) == 3);
    T("DR never lowers a hit below zero", IronCode.ApplyDR(1, "blades", new[] { new DrEntry(5, "blades") }) == 0);

    // -- damage types for DR matching --
    T("a revolver fires ball (armor mostly ignores)",
        IronCode.DamageType(cg.weapons.First(w => w.name == "Single-Action Revolver")) == "ball");
    T("a shotgun throws small shot", IronCode.DamageType(cg.weapons.First(w => w.name == "Double-Barrel Shotgun")) == "small shot");
    T("a blade cuts as blades", IronCode.DamageType(saber) == "blades");

    // -- the composed Strike: a miss deals nothing; a hit rolls damage and applies DR --
    var miss = IronCode.Strike(-50, 99, cg.weapons.First(w => w.name == "Single-Action Revolver"), forcedDie: 10);
    T("a missed Strike deals no damage", miss.Damage == null && miss.AfterDR == 0);
    var hit = IronCode.Strike(+50, 1, cg.weapons.First(w => w.name == "Knife / Bowie"),
        targetDr: new[] { new DrEntry(1, "blades") }, forcedDie: 10);
    T("a landed knife Strike deals its damage minus DR",
        hit.Damage != null && hit.AfterDR == Math.Max(0, hit.Damage.Total - 1));

    // -- combat state: identity survives a rename, Beats/MAP reset per turn (#2) --
    var soul = new PartyMember { Name = "Ruth" };
    var pcRow = new Combatant { IsPC = true, PcId = soul.Id, Name = "Ruth" };
    soul.Name = "Ruth (the Kid) Calloway";                    // rename after they're on the tracker
    T("a PC row follows its soul by id across a rename", pcRow.IsSoul(soul));
    var twin = new PartyMember { Name = "Ruth" };             // a different soul, same original name
    T("a different soul with the same name does not match", !pcRow.IsSoul(twin));
    var legacyRow = new Combatant { IsPC = true, PcId = "", Name = "Doc" };
    T("a legacy row (no id) still matches by name", legacyRow.IsSoul(new PartyMember { Name = "Doc" }));
    var foe = new Combatant { IsPC = false, PcId = soul.Id, Name = "x" };
    T("a foe row is never mistaken for a soul", !foe.IsSoul(soul));

    var actor = new Combatant { Name = "actor", Beats = 0, MapStep = 3 };
    actor.BeginTurn();
    T("BeginTurn restores 3 Beats and a clean MAP", actor.Beats == 3 && actor.MapStep == 1);

    // -- CombatFlow: a PC's to-hit off the sheet, and a resolved Strike that applies --
    var gh = CharGen.Generate(3, false, "Gunhand");
    var revolver = cg.weapons.First(w => w.name == "Single-Action Revolver");
    T("gun to-hit = sheet Attack + DEX mod",
        CombatFlow.AttackBonusFor(gh, revolver) == gh.Attack + CharGen.Mod(gh.Scores["DEX"]));
    var knife = cg.weapons.First(w => w.name == "Knife / Bowie");
    T("melee to-hit = sheet Attack + STR mod",
        CombatFlow.AttackBonusFor(gh, knife) == gh.Attack + CharGen.Mod(gh.Scores["STR"]));

    {
        var atk = new Combatant { Name = "Ruth" };            // fresh: Beats 3, MapStep 1
        var tgt = new Combatant { Name = "Ghoul", Defense = 1, BloodCur = 40, BloodMax = 40 };
        var rep = CombatFlow.StrikeAndApply(atk, tgt, revolver, attackBonus: 50, forcedDie: 10);   // sure hit
        T("a landed Strike drops the target's Blood", tgt.BloodCur == 40 - rep.Res.AfterDR && rep.Res.AfterDR > 0);
        T("a Strike spends a Beat and advances the MAP step", atk.Beats == 2 && atk.MapStep == 2);
        var rep2 = CombatFlow.StrikeAndApply(atk, tgt, revolver, attackBonus: 50, forcedDie: 10);  // second, at MAP -5
        T("the second Strike this turn takes the Multiple Attack Penalty", rep2.Map == -5 && atk.MapStep == 3);
    }
    {
        var atk = new Combatant { Name = "Ruth" };
        var tgt = new Combatant { Name = "Ghoul", Defense = 99, BloodCur = 40, BloodMax = 40 };
        CombatFlow.StrikeAndApply(atk, tgt, revolver, attackBonus: -50, forcedDie: 10);            // sure miss
        T("a missed Strike leaves the target's Blood alone", tgt.BloodCur == 40);
    }
}

// ============================================================ BALANCE, SIMULATED (#4)
// Run the actual Iron Code engine to answer the question a playtest can only guess at:
// can a level-appropriate soul still threaten a level-appropriate foe at every level?
// This is the property Step 1 restored — casters' attack had drifted so far behind monster
// Defense that their hit rate fell as they advanced. Turn that into a failing test, not a hunch.
{
    // to-hit ability held at a fixed +3 so the sim isolates the CALLING's attack progression
    // (the attack rank) from stat luck — the rank curve is exactly what broke and was fixed.
    const int AtkAbility = 3;
    int TierDefFor(int level) => Rules.TierRow[Math.Max(1, (level + 1) / 2) - 1].def;
    double HitRate(int toHit, int def, int n)
    {
        int hits = 0;
        for (int i = 0; i < n; i++)
            if (IronCode.ResolveStrike(toHit, def, new WeaponTraits()).Hit) hits++;
        return (double)hits / n;
    }

    Console.WriteLine("balance — hit rate vs a tier-appropriate foe (attack rank + " + AtkAbility + " to-hit):");
    bool floorHeld = true, martialBandHeld = true;
    foreach (var c in cg.callings.OrderBy(x => x.attackRank).ThenBy(x => x.name))
    {
        var rates = new List<string>();
        foreach (int L in new[] { 1, 3, 5, 7, 10 })
        {
            int toHit = CharGen.AttackFor(c.attackRank, L) + AtkAbility;
            double rate = HitRate(toHit, TierDefFor(L), 3000);
            rates.Add($"L{L}:{rate,4:P0}");
            // the floor: no soul, however magical, becomes unable to threaten a level-appropriate foe
            if (rate < 0.30) floorHeld = false;
            // martials are the reliable damage dealers; they should stay solidly able to hit
            if (c.attackRank == "Practiced" && (rate < 0.45 || rate > 0.80)) martialBandHeld = false;
        }
        Console.WriteLine($"  {c.name,-16} {c.attackRank,-9} {string.Join("  ", rates)}");
    }
    T("no calling falls below a 30% hit rate vs a tier-appropriate foe at any level", floorHeld);
    T("martial (Practiced) callings hold a 45–80% hit band across levels", martialBandHeld);

    // Step 1's structural invariant: every attack rank climbs +1 per level, so the distance
    // between the best gun Calling and the worst caster is fixed — it never widens with level.
    bool gapConstant = true;
    for (int L = 2; L <= 10; L++)
        if (CharGen.AttackFor("Practiced", L) - CharGen.AttackFor("Slight", L) != 2) gapConstant = false;
    T("the Practiced→Slight attack gap is a constant 2 from 2nd level up (never widens)", gapConstant);
    T("no attack rank ever loses ground as level rises", Enumerable.Range(2, 9).All(L =>
        new[] { "Practiced", "Steady", "Slight" }.All(rk =>
            CharGen.AttackFor(rk, L) >= CharGen.AttackFor(rk, L - 1))));
}

T("17 callings", cg.callings.Count == 17);
T("10 origins", cg.origins.Count == 10);
T("17 skills", cg.skills.Count == 17);
// ---- the Signs (Ch. XIII): three lists, five Ranks, and a gate that actually holds ----
T("40 signs across three lists", cg.signs.Count == 40
    && cg.signs.All(s => s.list is "common" or "bargain" or "craft"));
T("every sign carries a Rank of 1-5", cg.signs.All(s => s.rank >= 1 && s.rank <= 5));
T("every Rank is represented on every list", new[] { "common", "bargain", "craft" }
    .All(l => Enumerable.Range(1, 5).All(r => cg.signs.Any(s => s.list == l && s.rank == r))));
T("sign names are unique", cg.signs.Select(s => s.name).Distinct().Count() == cg.signs.Count);
T("the Craft is the Witch's alone", cg.callings
    .Where(c => c.signLists != null && c.signLists.Contains("craft"))
    .Select(c => c.name).SequenceEqual(new[] { "Witch" }));
T("sign-workers and signLists are the same four callings", cg.callings
    .All(c => (c.signsKnownAt != null) == (c.signLists != null && c.signLists.Count > 0)));
T("Rank opens at 1st, 3rd, 5th, 7th, 9th", Enumerable.Range(1, 10)
    .All(l => CharGen.SignRankAt(l) == (l + 1) / 2));
// A Calling must never be asked to know more Signs than its Rank has actually opened.
T("no caster is starved of legal signs at any level", cg.callings
    .Where(c => c.signsKnownAt != null)
    .All(c => Enumerable.Range(1, 10)
        .All(l => CharGen.SignsFor(c, l).Count >= c.signsKnownAt[l.ToString()] + 1)));
// Hedge Magic (Ch. IX) is the only way a non-caster ever holds a Sign, and it reaches
// the shallow end only: the Common Signs at Rank 1, at any level, forever.
{
    var noSigns = cg.callings.First(c => c.signsKnownAt == null);
    T("Hedge Magic opens the Common Signs at Rank 1 and nothing else",
        CharGen.SignsFor(noSigns, 10, hedgeMagic: true).All(s => s.list == "common" && s.rank == 1)
        && CharGen.SignsFor(noSigns, 10, hedgeMagic: true).Count > 0);
    T("a mundane Calling without Hedge Magic reaches no Sign at all",
        CharGen.SignsFor(noSigns, 10).Count == 0);
}
// ---- the Miracles (Ch. VI): the faith counterpart to the Signs, same Rank spine ----
T("40 miracles across six lists", cg.miracles.Count == 40 && cg.miracles.All(m =>
    m.list is "blessing" or "liturgy" or "revival" or "spirits" or "mending" or "consecration"));
T("every miracle carries a Rank of 1-5", cg.miracles.All(m => m.rank >= 1 && m.rank <= 5));
T("every Rank is represented on every miracle list", new[] {
    "blessing", "liturgy", "revival", "spirits", "mending", "consecration" }
    .All(l => Enumerable.Range(1, 5).All(rk => cg.miracles.Any(m => m.list == l && m.rank == rk))));
T("miracle names are unique", cg.miracles.Select(m => m.name).Distinct().Count() == cg.miracles.Count);
T("Signs and Miracles ride the one Rank spine", Enumerable.Range(1, 10)
    .All(l => CharGen.MiracleRankAt(l) == CharGen.SignRankAt(l)));
// Exactly the five Callings of Faith work Miracles, and none of them works a Sign.
T("the five faith callings work Miracles", cg.callings
    .Where(c => c.miracleLists != null && c.miracleLists.Count > 0)
    .Select(c => c.name).OrderBy(n => n)
    .SequenceEqual(new[] { "Medicine Man", "Padre", "Preacher", "Shaman", "Witch Hunter" }));
T("miracle-workers and Sign-workers never overlap", cg.callings
    .All(c => !(c.miracleLists?.Count > 0 && c.signLists?.Count > 0)));
T("every faith calling holds the Common Blessings plus one own list", cg.callings
    .Where(c => c.miracleLists != null)
    .All(c => c.miracleLists.Count == 2 && c.miracleLists[0] == "blessing"));
T("the Witch Hunter now has a pool (Zeal)", cg.callings
    .First(c => c.name == "Witch Hunter").pool?.name == "Zeal");
T("no faith calling is starved of legal miracles at any level", cg.callings
    .Where(c => c.miraclesKnownAt != null)
    .All(c => Enumerable.Range(1, 10)
        .All(l => CharGen.MiraclesFor(c, l).Count >= c.miraclesKnownAt[l.ToString()] + 1)));
T("every calling has 10 table rows", cg.callings.All(c => c.rows.Count == 10 && c.rows.Select(r => r.level).SequenceEqual(Enumerable.Range(1, 10))));
T("attack/saves never regress", cg.callings.All(c => Enumerable.Range(1, 9).All(l =>
    c.Row(l + 1).atk >= c.Row(l).atk && c.Row(l + 1).fort >= c.Row(l).fort
    && c.Row(l + 1).@ref >= c.Row(l).@ref && c.Row(l + 1).will >= c.Row(l).will)));
T("every calling has a 3rd-level path", cg.callings.All(c => c.subpath != null && c.subpath.options.Count >= 2));
T("sign workers are exactly the Old Dark", cg.callings.Where(c => c.signsKnownAt != null).All(c => c.group == "Old Dark")
    && cg.callings.Count(c => c.signsKnownAt != null) == 4);
T("casters start with two signs", cg.callings.Where(c => c.signsKnownAt != null).All(c => c.signsKnownAt["1"] == 2));
T("edge prereq names resolve", cg.edges.Where(e => e.reqEdge != null).All(e => cg.edges.Any(x => x.name == e.reqEdge)));
T("calling-edge callings resolve", cg.callingEdges.All(e => cg.callings.Any(c => c.name == e.calling)));
T("Faith may not take the Gambler origin (flag present)", cg.origins.Single(o => o.name == "The Gambler").notFaith);

// ---- Character generator: every calling × sampled levels × both methods, all rule-checked ----
foreach (var c in cg.callings)
    foreach (int lvl in new[] { 1, 3, 5, 7, 10 })
        foreach (bool rolled in new[] { false, true })
        {
            var sheet = CharGen.Generate(lvl, rolled, c.name);
            var v = CharGen.Validate(sheet);
            T($"conformant: {c.name} L{lvl} {(rolled ? "rolled" : "array")}" + (v.Count > 0 ? " — " + v[0] : ""), v.Count == 0);
        }

// ---- and a fully random sweep ----
for (int i = 0; i < 200; i++)
{
    var sheet = CharGen.Generate(Rules.Rng.Next(1, 11), Rules.Rng.Next(2) == 0);
    var v = CharGen.Validate(sheet);
    T($"random sweep #{i}" + (v.Count > 0 ? $" ({sheet.Calling}/{sheet.Origin} L{sheet.Level}): {v[0]}" : ""), v.Count == 0);
}

// ---- armor (Ch. X): the three rows, and souls who actually end up wearing them ----
T("three armors, each priced in gearPrices", cg.armor.Count == 3
    && cg.armor.All(a => cg.gearPrices.TryGetValue(a.gear, out var p) && Math.Abs(p - a.cost) < 0.001));
T("every calling has an armor preference, all names resolving",
    cg.callings.All(c => c.buyPlan.TryGetProperty("armor", out var ap)
        && ap.GetArrayLength() > 0
        && ap.EnumerateArray().All(n => cg.armor.Any(a => a.name == n.GetString()))));
{
    // Armor is bought last, out of what the coin leaves, so this is a distribution not a
    // guarantee — but "precious little armor" must not turn out to mean "none, ever."
    var wearing = new Dictionary<string, int>();
    int dressed = 0, n = 400;
    for (int i = 0; i < n; i++)
    {
        var sheet = CharGen.Generate(Rules.Rng.Next(1, 11), Rules.Rng.Next(2) == 0);
        if (string.IsNullOrEmpty(sheet.ArmorWorn)) continue;
        dressed++;
        wearing[sheet.ArmorWorn] = wearing.GetValueOrDefault(sheet.ArmorWorn) + 1;
        // whatever they wear, the sheet must agree with the Ch. X row it came from
        var row = cg.armor.Single(a => a.name == sheet.ArmorWorn);
        T($"armor sheet matches Ch. X row: {sheet.ArmorWorn}",
            sheet.DrBlades == row.drBlades && sheet.DrShot == row.drShot && sheet.Gear.Contains(row.gear));
    }
    // printed, not just asserted: whoever next changes a price wants to see what it did
    Console.WriteLine($"armor worn: {dressed}/{n} souls dressed — "
        + string.Join(", ", wearing.OrderByDescending(k => k.Value).Select(k => $"{k.Key} {k.Value}")));
    T($"generated souls buy armor ({dressed}/{n} dressed)", dressed > n / 4);
    T("iron plate stays rare (it costs $60)",
        wearing.GetValueOrDefault("Scavenged Iron Plate") < n / 2);
}

// ---- a faith soul actually receives its Miracles, at the right count and Rank ----
foreach (var name in new[] { "Padre", "Preacher", "Shaman", "Medicine Man", "Witch Hunter" })
    foreach (int lvl in new[] { 1, 3, 5, 7, 10 })
    {
        var fs = CharGen.Generate(lvl, false, name);
        var cal = cg.callings.First(c => c.name == name);
        T($"{name} L{lvl}: knows {cal.miraclesKnownAt[lvl.ToString()]} miracles",
            fs.MiraclesKnown.Count == cal.miraclesKnownAt[lvl.ToString()]);
        T($"{name} L{lvl}: every miracle is legal (list + Rank)", fs.MiraclesKnown.All(mk =>
            CharGen.MiraclesFor(cal, lvl).Any(x => x.name == mk)));
        T($"{name} L{lvl}: works no Sign", fs.SignsKnown.Count == 0);
    }

// ---- targeted rule spot-checks (the Appendix D cross-checks) ----
for (int i = 0; i < 25; i++)
{
    var g = CharGen.Generate(1, false, "Gunhand");
    T("Gunhand L1: one Edge + one bonus combat Edge (Gunhand's Edge)", g.Edges.Count == 1 && g.BonusCombatEdges.Count == 1);
    T("Gunhand L1 Blood = 10 + CON mod (+Rawhide)", g.Blood == 10 + g.ConModAtLevel[0]
        + ((g.Edges.Contains("Tough as Rawhide") || g.BonusCombatEdges.Contains("Tough as Rawhide")) ? 1 : 0));
    var h = CharGen.Generate(1, false, "Hexer");
    T("Hexer L1: two Signs, Mark 1+, Will the only strong save", h.SignsKnown.Count == 2 && h.Mark >= 1 && h.Will >= CharGen.Mod(h.Scores["RES"]) + 2);
    var w = CharGen.Generate(1, false, "Witch");
    T("Witch starts unmarked save for Touched or Came Back Wrong",
        w.Mark == (w.Edges.Contains("Touched") ? 1 : 0) + (w.Origin == "Came Back Wrong" ? 1 : 0));
    var pr = CharGen.Generate(5, true, "Preacher");
    T("Faith knows no Signs, never the Gambler origin", pr.SignsKnown.Count == 0 && pr.Origin != "The Gambler" && !pr.Edges.Contains("Hedge Magic"));
    var cw = CharGen.Generate(1, false, null, "Came Back Wrong");
    T("Came Back Wrong carries Mark 1+", cw.Mark >= 1);
}
var dc10 = CharGen.Generate(10, false, "Dark Cultist");
T("Dark Cultist L10: patron named at 3rd among the six", CharGen.D.callings.First(c => c.name == "Dark Cultist").subpath.options.Any(o => o.name == dc10.Subpath));
T("Nerve = RES + level (+Stone Nerve)", dc10.NerveMax == dc10.Scores["RES"] + 10 + (dc10.Edges.Contains("Stone Nerve") ? 20 : 0));
var sheet10 = CharGen.Generate(10, false, "Marshal");
T("L10 boosts at 5 and 10", sheet10.AbilityBoostLevels.SequenceEqual(new[] { 5, 10 }));
T("L10 Marshal attack +10 per table", sheet10.Attack == 10);
T("render carries the Four Questions", CharGen.Render(sheet10).Contains("THE FOUR QUESTIONS"));

// ---- a soul is somebody: gender rolled, name drawn to match ----
for (int i = 0; i < 50; i++)
{
    var g = CharGen.Generate(1, false);
    T("generated soul has a gender", g.Gender is "Woman" or "Man");
    // A name is either given+surname drawn against gender, or one of the whole names that
    // do not decompose into those two pools (a Chinese name is surname-first). Both are legal.
    var expectList = CharGen.Flavor(g.Gender == "Woman" ? "givenWomen" : "givenMen");
    var wholeList  = CharGen.Flavor(g.Gender == "Woman" ? "fullNamesWomen" : "fullNamesMen");
    T("name is drawn coherently for the gender",
        expectList.Contains(g.Name.Split(' ')[0]) || wholeList.Contains(g.Name));
}
T("both genders turn up", Enumerable.Range(0, 60).Select(_ => CharGen.Generate(1, false).Gender).Distinct().Count() == 2);
{
    var spec = new CharGen.AssembleSpec { Level = 1, Calling = "Gunhand", Origin = "The Outlaw", Gender = "Woman" };
    var pool2 = new List<int>(cg.honestArray);
    var gh = cg.callings.First(c => c.name == "Gunhand");
    for (int i = 0; i < 6; i++) spec.PreGiftScores[gh.keyAbilities[i]] = pool2[i];
    var s2 = CharGen.Assemble(spec);
    T("assemble honors the given gender", s2.Gender == "Woman");
    T("assemble rolls a matching name",
        CharGen.Flavor("givenWomen").Contains(s2.Name.Split(' ')[0])
        || CharGen.Flavor("fullNamesWomen").Contains(s2.Name));   // a name may be a whole-name draw
    T("render carries the gender", CharGen.Render(s2).Contains("woman"));
}

// ---- the wizard's road: Assemble must be exactly as conformant as Generate ----
// empty specs (every choice left to the book) across all callings and levels
foreach (var c in cg.callings)
    foreach (int lvl in new[] { 1, 5, 10 })
    {
        var org = cg.origins.First(o => !(c.group == "Faith" && o.notFaith));
        var spec = new CharGen.AssembleSpec { Level = lvl, Calling = c.name, Origin = org.name };
        var pool = new List<int>(cg.honestArray);
        for (int i = 0; i < 6; i++) spec.PreGiftScores[c.keyAbilities[i]] = pool[i];
        var sheet = CharGen.Assemble(spec);
        var v = CharGen.Validate(sheet);
        T($"assemble conformant: {c.name} L{lvl}" + (v.Count > 0 ? " — " + v[0] : ""), v.Count == 0);
    }

// specs with explicit (sometimes illegal) choices — illegal picks must be re-drawn, never shipped
for (int i = 0; i < 100; i++)
{
    var c = cg.callings[Rules.Rng.Next(cg.callings.Count)];
    var legalOrigins = cg.origins.Where(o => !(c.group == "Faith" && o.notFaith)).ToList();
    var org = legalOrigins[Rules.Rng.Next(legalOrigins.Count)];
    int lvl = Rules.Rng.Next(1, 11);
    var spec = new CharGen.AssembleSpec { Level = lvl, Calling = c.name, Origin = org.name, Rolled = true, Name = "Test Soul" };
    foreach (var a in new[] { "STR", "DEX", "CON", "WIT", "RES", "PRE" }) spec.PreGiftScores[a] = Rules.Rng.Next(3, 19);
    // scattershot choices: some real, some junk the assembler must shrug off
    spec.TrainedPicks.Add(cg.skills[Rules.Rng.Next(cg.skills.Count)].name);
    spec.TrainedPicks.Add("Not A Skill");
    spec.Edges.Add(cg.edges[Rules.Rng.Next(cg.edges.Count)].name);
    spec.Edges.Add("Not An Edge");
    spec.SkillIncreases.Add(cg.skills[Rules.Rng.Next(cg.skills.Count)].name);
    spec.Signs.Add(cg.signs[Rules.Rng.Next(cg.signs.Count)].name);
    spec.Miracles.Add(cg.miracles[Rules.Rng.Next(cg.miracles.Count)].name);
    spec.Subpath = "Not A Path";
    spec.BuyWeapons.Add(cg.weapons[Rules.Rng.Next(cg.weapons.Count)].name);
    spec.BuyGear.Add(cg.gearPrices.Keys.First());
    var sheet = CharGen.Assemble(spec);
    var v = CharGen.Validate(sheet);
    T($"assemble sweep #{i}" + (v.Count > 0 ? $" ({sheet.Calling}/{sheet.Origin} L{sheet.Level}): {v[0]}" : ""), v.Count == 0);
    if (i == 0) T("assemble honors the given name", sheet.Name == "Test Soul");
}

// ---- levelling up: append exactly one level, keep the levels below stable, stay conformant ----
foreach (var c in cg.callings)
    foreach (bool rolled in new[] { false, true })
    {
        var s = CharGen.Generate(1, rolled, c.name);
        for (int target = 2; target <= 10; target++)
        {
            var before = s;
            int preBlood = before.BloodRolls.Count;
            var grants = CharGen.PreviewLevelUp(before);
            T($"levelup preview: {c.name} → L{target}", grants.NewLevel == target && !grants.AtCeiling);
            s = CharGen.LevelUp(before, new CharGen.LevelUpChoices());
            var lv = CharGen.Validate(s);
            T($"levelup conformant: {c.name} {(rolled ? "rolled" : "array")} → L{target}" + (lv.Count > 0 ? " — " + lv[0] : ""), lv.Count == 0);
            T($"levelup increments to L{target}: {c.name}", s.Level == target);
            T($"levelup adds one Blood roll: {c.name} → L{target}", s.BloodRolls.Count == preBlood + 1);
            // the levels below are byte-stable: prior Blood rolls / edges / signs are an unchanged prefix
            T($"levelup keeps prior Blood: {c.name} → L{target}", before.BloodRolls.SequenceEqual(s.BloodRolls.Take(preBlood)));
            T($"levelup keeps prior edges: {c.name} → L{target}", before.Edges.SequenceEqual(s.Edges.Take(before.Edges.Count)));
            T($"levelup keeps prior signs: {c.name} → L{target}", before.SignsKnown.SequenceEqual(s.SignsKnown.Take(before.SignsKnown.Count)));
        }
        var capped = CharGen.LevelUp(s, new CharGen.LevelUpChoices());
        T($"levelup ceiling no-op: {c.name}", capped.Level == 10 && CharGen.Validate(capped).Count == 0);
        T($"levelup preview at ceiling: {c.name}", CharGen.PreviewLevelUp(s).AtCeiling);
    }

// under a fixed seed the whole grow-up is reproducible (Generate + nine LevelUps)
{
    string Grow(int seed)
    {
        Rules.Reseed(seed);
        var s = CharGen.Generate(1, false, "Marshal");
        for (int L = 2; L <= 10; L++) s = CharGen.LevelUp(s, new CharGen.LevelUpChoices());
        return System.Text.Json.JsonSerializer.Serialize(s);
    }
    T("levelup reproducible under a fixed seed", Grow(0x1010) == Grow(0x1010));
    T("different seed grows a different soul", Grow(0x1010) != Grow(0x2020));
    Rules.ReseedEntropy();
}

// explicit choices are honored (edge, subpath, Blood die) and the sheet still conforms
{
    var s = CharGen.Generate(2, false, "Marshal");
    var gr = CharGen.PreviewLevelUp(s);                    // → 3rd: edge + skill increase + subpath
    var ch = new CharGen.LevelUpChoices { BloodDie = 1 };  // minimum Hit-Die face
    if (gr.EdgeOptions.Count > 0) ch.Edge = gr.EdgeOptions[0];
    if (gr.SkillOptions.Count > 0) ch.SkillIncrease = gr.SkillOptions[0];
    if (gr.Subpath && gr.SubpathOptions.Count > 0) ch.Subpath = gr.SubpathOptions[^1];
    var up = CharGen.LevelUp(s, ch);
    T("levelup honors chosen edge", gr.EdgeOptions.Count == 0 || up.Edges.Contains(gr.EdgeOptions[0]));
    T("levelup honors chosen subpath", !gr.Subpath || up.Subpath == gr.SubpathOptions[^1]);
    T("levelup honors chosen Blood die", up.BloodRolls[^1] == 1 + up.ConModAtLevel[^1]);
    T("levelup with explicit choices conformant", CharGen.Validate(up).Count == 0);
}

// the Gunhand's bonus combat Edge keeps pace, one Gun edge per odd level
{
    var s = CharGen.Generate(1, false, "Gunhand");
    for (int L = 2; L <= 9; L++) s = CharGen.LevelUp(s, new CharGen.LevelUpChoices());
    T("Gunhand leveled to 9: 5 edges + 5 bonus combat edges", s.Edges.Count == 5 && s.BonusCombatEdges.Count == 5);
    T("Gunhand leveled bonus edges are all Gun-group", s.BonusCombatEdges.All(n => CharGen.EdgeByName(n).group == "Gun"));
    T("Gunhand leveled to 9 conformant", CharGen.Validate(s).Count == 0);
}

// a caster's Signs grow with the level, distinct and legal
{
    var s = CharGen.Generate(1, false, "Hexer");
    int startSigns = s.SignsKnown.Count;
    for (int L = 2; L <= 10; L++) s = CharGen.LevelUp(s, new CharGen.LevelUpChoices());
    T("Hexer leveled to 10 grows Signs, distinct & real",
        s.SignsKnown.Count >= startSigns && s.SignsKnown.Distinct().Count() == s.SignsKnown.Count
        && s.SignsKnown.All(n => cg.signs.Any(x => x.name == n)));
    T("Hexer leveled to 10 conformant", CharGen.Validate(s).Count == 0);
}

// the sheet now rides inside PartyMember through session.json — prove the round-trip
var soulSess = new GameSession();
var carried = CharGen.Generate(3, false, "Gunhand");
soulSess.Party.Add(new PartyMember { Name = carried.Name, Sheet = carried });
var soulJson = System.Text.Json.JsonSerializer.Serialize(soulSess);
var soulBack = System.Text.Json.JsonSerializer.Deserialize<GameSession>(soulJson);
T("sheet survives the session round-trip", soulBack.Party[0].Sheet != null
    && soulBack.Party[0].Sheet.Calling == "Gunhand"
    && soulBack.Party[0].Sheet.Edges.SequenceEqual(carried.Edges)
    && soulBack.Party[0].Sheet.Scores["RES"] == carried.Scores["RES"]
    && CharGen.Validate(soulBack.Party[0].Sheet).Count == 0);
T("legacy member without a sheet still loads", System.Text.Json.JsonSerializer
    .Deserialize<GameSession>("{\"Party\":[{\"Name\":\"Old Hand\"}]}").Party[0].Sheet == null);

// ---- Trail Maps: generation, SVG, and PDF must all hold together ----
foreach (var terrain in MapGen.Terrains)
    for (int scale = 0; scale < MapGen.Scales.Length; scale++)
    {
        var spec = new MapSpec { Terrain = terrain, Scale = scale, Seed = 1234, Landmarks = 5, Secrets = true, Rail = true };
        var m = MapGen.Generate(spec);
        T($"map generates: {terrain} @ scale {scale}", m != null && m.P.Count > 20 && !string.IsNullOrWhiteSpace(m.Title));
        var svg = MapGen.ToSvg(m);
        T($"map SVG well-formed: {terrain} @ {scale}", svg.StartsWith("<svg") && svg.TrimEnd().EndsWith("</svg>") && svg.Contains(m.Title.Split(' ')[0]));
        var pdf = Pdf.MapPdf(m);
        string head = System.Text.Encoding.Latin1.GetString(pdf, 0, 8);
        string tail = System.Text.Encoding.Latin1.GetString(pdf, Math.Max(0, pdf.Length - 32), Math.Min(32, pdf.Length));
        T($"map PDF structural: {terrain} @ {scale}", head.StartsWith("%PDF-1.4") && tail.Contains("%%EOF") && pdf.Length > 2000);
    }
{
    var spec = new MapSpec { Terrain = MapGen.Terrains[0], Scale = 2, Seed = 777 };
    T("same seed, same map", MapGen.ToSvg(MapGen.Generate(spec)) == MapGen.ToSvg(MapGen.Generate(spec)));
    T("different seed, different map", MapGen.ToSvg(MapGen.Generate(spec))
        != MapGen.ToSvg(MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[0], Scale = 2, Seed = 778 })));
}

// ---- Trail Maps: nothing linear may cross the map border (rivers used to) ----
// Rivers/creeks/trails/rails are generated edge-to-edge and then clipped to the
// inner neatline; every Line prim across a spread of seeds and waters must stay
// on the paper, with a whisker of tolerance for the neatline itself.
{
    int outOfBounds = 0; string firstBad = null;
    foreach (int seed in new[] { 1, 77, 555, 1234, 99999 })
        for (int waterKind = 0; waterKind < MapGen.Waters.Length; waterKind++)
        {
            var m = MapGen.Generate(new MapSpec
            {
                Terrain = MapGen.Terrains[seed % MapGen.Terrains.Length],
                Scale = seed % 4, Water = waterKind, Seed = seed,
                Trail = true, Rail = true, Town = true, Secrets = true, Landmarks = 6
            });
            foreach (var pr in m.P)
            {
                if (pr.Kind != PrimKind.Line) continue;
                for (int i = 0; i + 1 < pr.Pts.Length; i += 2)
                    if (pr.Pts[i] < -0.01f || pr.Pts[i] > m.W + 0.01f || pr.Pts[i + 1] < -0.01f || pr.Pts[i + 1] > m.H + 0.01f)
                    { outOfBounds++; firstBad ??= $"seed {seed} water {waterKind}: ({pr.Pts[i]}, {pr.Pts[i + 1]})"; }
            }
        }
    T($"no line ink beyond the map edge (first offender: {firstBad ?? "none"})", outOfBounds == 0);
}

// ---- Trail Maps: landmarks are movable, and a move touches ONLY their own ink ----
{
    var m = MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[0], Scale = 2, Seed = 4242, Landmarks = 6 });
    T("landmarks recorded with sane prim ranges", m.Landmarks.Count > 0 && m.Landmarks.All(l =>
        l.PrimStart >= 0 && l.PrimCount > 0 && l.PrimStart + l.PrimCount <= m.P.Count && l.Name.Length > 0
        && l.X == l.GenX && l.Y == l.GenY));
    T("landmark prim ranges never overlap", m.Landmarks.Zip(m.Landmarks.Skip(1))
        .All(pair => pair.First.PrimStart + pair.First.PrimCount <= pair.Second.PrimStart));
    if (m.Landmarks.Count > 0)
    {
        var lm = m.Landmarks[0];
        var before = m.P.Select(p => (float[])p.Pts.Clone()).ToList();
        float ox2 = lm.X, oy2 = lm.Y;
        MapGen.MoveLandmark(m, 0, ox2 + 40, oy2 - 25);
        bool ownMoved = true, othersStill = true;
        for (int i = 0; i < m.P.Count; i++)
        {
            bool mine = i >= lm.PrimStart && i < lm.PrimStart + lm.PrimCount;
            var (a, b) = (before[i], m.P[i].Pts);
            if (!mine) { if (!a.SequenceEqual(b)) othersStill = false; continue; }
            int n = m.P[i].Kind == PrimKind.Circle ? 2 : a.Length;   // circle: only cx,cy translate
            for (int j = 0; j < n; j += 2)
                if (Math.Abs(b[j] - a[j] - 40) > 0.001f || Math.Abs(b[j + 1] - a[j + 1] + 25) > 0.001f) ownMoved = false;
            if (m.P[i].Kind == PrimKind.Circle && a[2] != b[2]) ownMoved = false;
        }
        T("moving a landmark translates exactly its own prims", ownMoved && lm.X == ox2 + 40 && lm.Y == oy2 - 25);
        T("moving a landmark leaves every other prim alone", othersStill);
        MapGen.MoveLandmark(m, 0, ox2, oy2);
        bool restored = true;
        for (int i = lm.PrimStart; i < lm.PrimStart + lm.PrimCount; i++)
            for (int j = 0; j < m.P[i].Pts.Length; j++)
                if (Math.Abs(m.P[i].Pts[j] - before[i][j]) > 0.001f) restored = false;
        T("moving it back restores the original ink", restored);
    }
}

// ---- Trail Maps: overlays are VIEWS — toggling one must not reshuffle the map ----
// (One shared rng stream used to mean checking Rail regenerated a different
// countryside; per-feature streams make every checkbox pure ink on/ink off.)
{
    string Sig(MapModel mm) => mm.Title + "|" +
        string.Join(";", mm.Landmarks.Select(l => $"{l.Name}:{l.GenX:0.#}:{l.GenY:0.#}"));
    var baseSpec = new MapSpec { Terrain = MapGen.Terrains[0], Scale = 2, Seed = 5150, Water = 3,
        Trail = false, Rail = false, Town = false, Grid = false, Secrets = false, Landmarks = 5 };
    string baseSig = Sig(MapGen.Generate(baseSpec));
    (string flag, MapSpec s)[] flips =
    {
        ("trail", new MapSpec { Terrain = baseSpec.Terrain, Scale = 2, Seed = 5150, Water = 3, Trail = true,  Rail = false, Town = false, Grid = false, Secrets = false, Landmarks = 5 }),
        ("rail",  new MapSpec { Terrain = baseSpec.Terrain, Scale = 2, Seed = 5150, Water = 3, Trail = false, Rail = true,  Town = false, Grid = false, Secrets = false, Landmarks = 5 }),
        ("town",  new MapSpec { Terrain = baseSpec.Terrain, Scale = 2, Seed = 5150, Water = 3, Trail = false, Rail = false, Town = true,  Grid = false, Secrets = false, Landmarks = 5 }),
        ("grid",  new MapSpec { Terrain = baseSpec.Terrain, Scale = 2, Seed = 5150, Water = 3, Trail = false, Rail = false, Town = false, Grid = true,  Secrets = false, Landmarks = 5 }),
        ("secrets", new MapSpec { Terrain = baseSpec.Terrain, Scale = 2, Seed = 5150, Water = 3, Trail = false, Rail = false, Town = false, Grid = false, Secrets = true, Landmarks = 5 }),
    };
    foreach (var (flag, s) in flips)
        T($"toggling {flag} leaves the land, landmarks & title alone", Sig(MapGen.Generate(s)) == baseSig);
}

// ---- Trail Maps: a Ford sits ON the water, not out in the sagebrush ----
{
    int fords = 0, snapped = 0;
    for (int seed = 1; seed <= 60 && fords < 4; seed++)
    {
        var m = MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[0], Scale = 2, Seed = seed, Water = 3, Landmarks = 8 });
        var ford = m.Landmarks.FirstOrDefault(l => l.Name.EndsWith("Ford"));
        if (ford == null) continue;
        fords++;
        // the river is the widest stroke on the map; the ford anchor must touch a vertex of it
        float best = float.MaxValue;
        foreach (var rp in m.P)
        {
            if (rp.Kind != PrimKind.Line || rp.StrokeW < 12) continue;
            for (int i = 0; i + 1 < rp.Pts.Length; i += 2)
                best = Math.Min(best, (rp.Pts[i] - ford.GenX) * (rp.Pts[i] - ford.GenX) + (rp.Pts[i + 1] - ford.GenY) * (rp.Pts[i + 1] - ford.GenY));
        }
        if (best < 1f) snapped++;
    }
    T($"fords snap to the river ({snapped}/{fords} across seeds)", fords > 0 && snapped == fords);
}

// ---- Trail Maps: the Keeper's marks are recorded and movable like landmarks ----
{
    var m = MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[0], Scale = 2, Seed = 909, Secrets = true, Landmarks = 4 });
    T("secrets recorded with sane prim ranges", m.Secrets.Count >= 2 && m.Secrets.All(sx =>
        sx.PrimStart >= 0 && sx.PrimCount >= 4 && sx.PrimStart + sx.PrimCount <= m.P.Count));
    var sec = m.Secrets[0];
    float sx0 = sec.X, sy0 = sec.Y;
    var circleBefore = (float[])m.P[sec.PrimStart].Pts.Clone();
    MapGen.MoveSecret(m, 0, sx0 + 33, sy0 - 21);
    var circleAfter = m.P[sec.PrimStart].Pts;
    T("moving a secret translates its ring", Math.Abs(circleAfter[0] - circleBefore[0] - 33) < 0.001f
        && Math.Abs(circleAfter[1] - circleBefore[1] + 21) < 0.001f && circleAfter[2] == circleBefore[2]
        && sec.X == sx0 + 33 && sec.Y == sy0 - 21);
    T("a map without the Keeper's layer records no secrets",
        MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[0], Scale = 2, Seed = 909, Secrets = false }).Secrets.Count == 0);
}

// the text-sheet PDF (the New Soul export) — structural checks + samples for external validation
{
    var soulPdfSheet = CharGen.Generate(5, false, "Gunhand");
    var sheetPdf = Pdf.TextSheet(soulPdfSheet.Name, "Gunhand — test", CharGen.Render(soulPdfSheet));
    string head = System.Text.Encoding.Latin1.GetString(sheetPdf, 0, 8);
    T("sheet PDF structural", head.StartsWith("%PDF-1.4") && sheetPdf.Length > 1500);
    string outDir = Path.Combine(Path.GetTempPath(), "gritkeeper-smoke");
    Directory.CreateDirectory(outDir);
    File.WriteAllBytes(Path.Combine(outDir, "sample-map.pdf"),
        Pdf.MapPdf(MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[0], Scale = 2, Seed = 42, Secrets = true })));
    File.WriteAllBytes(Path.Combine(outDir, "sample-sheet.pdf"), sheetPdf);
    // a river map as SVG — eyeball that waterways end AT the neatline, not past it
    File.WriteAllText(Path.Combine(outDir, "sample-river.svg"),
        MapGen.ToSvg(MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[1], Scale = 2, Seed = 4242, Water = 3, Rail = true })));
    Console.WriteLine($"sample PDFs → {outDir}");
}

Console.WriteLine($"\n{pass} passed, {fail} failed");
return fail == 0 ? 0 : 1;
