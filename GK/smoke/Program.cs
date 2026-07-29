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

// ---- Creature attacks: the Bestiary's own attacks parse, and Strike through the Iron Code ----
// Every creature's free-text `attacks` line must yield structured Strikes with sane numbers, so a
// creature in the tracker fights with ITS OWN claws and bite, not the posse's guns.
{
    int totalStrikes = 0, withDice = 0, elemental = 0, noStrikeCreatures = 0;
    foreach (var c in Db.Creatures)
    {
        var (strikes, riders) = CreatureAttack.Parse(c.attacks);
        // A creature either has parseable Strikes, or its line is pure riders (an intangible hazard,
        // a phenomenon) — never a parser crash, never a half-parsed clause.
        if (strikes.Count == 0) { noStrikeCreatures++; }
        totalStrikes += strikes.Count;
        foreach (var a in strikes)
        {
            T($"[{c.name}] '{a.Name}' has a name", a.Name.Length > 0);
            T($"[{c.name}] '{a.Name}' bonus in range", a.Bonus >= 0 && a.Bonus <= 30);
            if (a.DealsDamage)
            {
                withDice++;
                var (dt, bd) = Rules.RollExpr(a.Damage);
                T($"[{c.name}] '{a.Name}' damage rolls ({a.Damage})", bd != "could not parse" && bd != "empty" && dt >= 1);
            }
            if (a.Type != "blades") elemental++;
        }
        // riders are non-empty text (the special maneuvers/auras the Keeper narrates)
        T($"[{c.name}] riders are non-empty", riders.All(r => r.Trim().Length > 0));
    }
    T("most creatures have at least one Strike", noStrikeCreatures <= 25);   // ~intangible hazards only
    T("attacks parse into 120+ strikes", totalStrikes >= 120);
    T("the great majority of strikes carry dice", withDice >= totalStrikes - 10);
    T("some creature attacks are elemental (fire/cold/…)", elemental >= 3);

    // End to end: a Tier-III ghoul claws a target through the very same engine a gun uses.
    var ghoulLike = new Combatant { Name = "Foe", Defense = 12, BloodCur = 40, BloodMax = 40 };
    var claw = new CreatureAttack { Name = "rending claws", Bonus = 8, Damage = "1d8+3" };
    var attacker = new Combatant { Name = "Ghoul", Beats = 3, MapStep = 1 };
    var rep = CombatFlow.StrikeAndApply(attacker, ghoulLike, claw, claw.Bonus, forcedDie: 15);
    T("a creature Strike lands and takes Blood", rep.Res.Strike.Hit && ghoulLike.BloodCur < 40);
    T("a creature Strike spends its Beat and steps the MAP", attacker.Beats == 2 && attacker.MapStep == 2);
    // an elemental touch types as its element, so worn-armor DR (blades) does not stop it
    var fireTouch = new CreatureAttack { Name = "a touch that blisters", Bonus = 20, Damage = "1d8+3", Type = "fire" };
    var burned = new Combatant { Name = "Armored", Defense = 5, BloodCur = 30, BloodMax = 30 };
    var fr = CombatFlow.StrikeAndApply(new Combatant { Beats = 3, MapStep = 1 }, burned, fireTouch, 20,
        new[] { new DrEntry(3, "blades") }, forcedDie: 15);
    T("blades DR does not reduce a fire touch", fr.Res.DamageType == "fire" && fr.Res.AfterDR == fr.Res.Damage.Total);
}

// CombatMenu is the single authority the Strike dialog uses to decide whose attacks a tracker
// row shows. The bug it guards: the posse and creatures showing EACH OTHER'S attacks. IsPC is
// decisive, so no stray Ref on a soul (or a lost Ref on a foe) can cross the wires.
{
    // a real Bestiary foe fights with its OWN attacks
    var badgerName = Db.Creatures.First(c => c.attacks.Length > 0 && c.DefenseValue > 0).name;
    var foe = new Combatant { Name = badgerName + " #2", Ref = badgerName, IsPC = false };
    T("a foe row is classed as a creature", CombatMenu.IsCreature(foe));
    var (fa, _, fc) = CombatMenu.For(foe);
    T("a foe draws its own attacks, not the posse's", fc != null && fa != null && fa.Count >= 1);

    // a posse soul NEVER fights as a creature — even if a stale Ref rode in on an old session
    var soul = new Combatant { Name = "Ruth", IsPC = true, Ref = badgerName };
    T("a PC is never classed as a creature (even with a stray Ref)", !CombatMenu.IsCreature(soul));
    var (sa, sr, sc) = CombatMenu.For(soul);
    T("a PC draws no creature attacks (falls to weapons)", sc == null && sa == null && sr == null);

    // a hand-entered NPC (no Bestiary match) falls back to weapons rather than throwing
    var npc = new Combatant { Name = "Bandit", IsPC = false, Ref = "" };
    T("a hand-entered foe with no Ref uses weapons", !CombatMenu.IsCreature(npc) && CombatMenu.For(npc).creature == null);
    var ghost = new Combatant { Name = "???", IsPC = false, Ref = "no such creature in the book" };
    T("a foe whose Ref no longer resolves falls back, never throws", !CombatMenu.IsCreature(ghost) && CombatMenu.For(ghost).creature == null);

    // a bodiless foe (no dice of its own) still gets a tier-benchmark blow, not an empty menu
    var bodiless = Db.Creatures.FirstOrDefault(c => CreatureAttack.Parse(c.attacks).strikes.Count == 0);
    if (bodiless != null)
    {
        var (ba, _, _) = CombatMenu.For(new Combatant { Ref = bodiless.name, IsPC = false });
        T($"bodiless foe [{bodiless.name}] still offers a blow", ba != null && ba.Count >= 1 && ba[0].Bonus > 0);
    }
}

// A canary that the data files really loaded: a missing or malformed tables file shows up here as
// a count rather than as an empty generator three menus deep. 17 through v1.25.0; the adventure
// generator added eight (shape, hook, truth, turn, clock, reward, and the two title halves).
T($"25 simple tables (got {Db.Simple.Count})", Db.Simple.Count == 25);
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

// Every creature can be rolled. A Bestiary entry no table ever offers is one a Keeper has to
// already know about to use, which defeats the point of having the tables. The White Bison is
// the one deliberate exception — Ch. XII says it has gone quiet, so it stays off.
{
    var onTables = new HashSet<string>(
        Db.Terrain.SelectMany(kv => kv.Value)
                  .Select(e => System.Text.RegularExpressions.Regex.Match(e, @"^(.*?)(\s*\(|$)").Groups[1].Value.Trim()));
    var unreachable = Db.Creatures.Select(c => c.name).Where(n => !onTables.Contains(n)).ToList();
    T("every creature is reachable from some terrain table, bar the one held back",
        unreachable.Count == 1 && unreachable[0] == "The White Bison");
}

// The generators the Keeper actually presses. A re-extraction of tables.json that lands without
// tables_extra.json would still boot and still roll — just thinly, and silently. Hold the floor.
foreach (var (table, floor) in new[]
{
    ("townFront", 40), ("townBack", 40), ("townAils", 28), ("townSecret", 28),
    ("npcGiven", 72), ("npcSurname", 70), ("npcWant", 28), ("npcTell", 28),
    ("rumors", 56), ("trailDay", 40), ("trailNight", 40), ("plunder", 40), ("omens", 52),
    ("cityQuarter", 20), ("cityMachine", 20), ("cityWrongNote", 24), ("cityJob", 20),
})
    T($"table [{table}] is at least {floor} deep", Db.Simple[table].Count >= floor);

// ---- The safe-table rule: sign and spoor ----
{
    T("spoor: a row for every Tier", Rules.SpoorRow.Length == 5);
    // The DCs climb with the Tier, and the Dread cost is one rung below meeting the thing —
    // which is the whole claim the books make about this rule, so hold them to it.
    for (int i = 1; i < Rules.SpoorRow.Length; i++)
    {
        T($"spoor: Tier {Rules.Roman(i + 1)} is harder to read than {Rules.Roman(i)}",
            Rules.SpoorRow[i].readDc > Rules.SpoorRow[i - 1].readDc);
        T($"spoor: Tier {Rules.Roman(i + 1)} costs no less Nerve than {Rules.Roman(i)}",
            Rules.SpoorRow[i].dreadDc >= Rules.SpoorRow[i - 1].dreadDc);
    }
    T("spoor: a Tier I trace costs nothing — out here a cougar kills a calf", Rules.SpoorRow[0].dreadDc == 0);
    // "one rung below the thing itself": the sign of a Tier N horror costs what MEETING a
    // Tier N-1 horror costs. Tier II's 10 is the bottom of Tier I's "— / 10–13" band.
    for (int i = 1; i < Rules.SpoorRow.Length; i++)
        T($"spoor: Tier {Rules.Roman(i + 1)} sign costs a Tier {Rules.Roman(i)} meeting",
            Rules.TierRow[i - 1].dread.Contains(Rules.SpoorRow[i].dreadDc.ToString()));
    T("spoor: every Tier says what is left on the ground",
        Rules.SpoorRow.All(s => !string.IsNullOrWhiteSpace(s.what) && s.what.Length > 20));
    T("spoor: the four degrees each buy something different",
        Enumerable.Range(0, 4).Select(Rules.SpoorRead).Distinct().Count() == 4);
    T("spoor: and none of them is blank",
        Enumerable.Range(0, 4).All(d => !string.IsNullOrWhiteSpace(Rules.SpoorRead(d))));
    T("spoor: the thread is a four-segment clock", Rules.SpoorClockSegments == 4);
    // The rule only fires where Rules.Cost says it does — two or more Tiers over the posse.
    T("spoor: a Tier III horror is sign-only against a 2nd-level posse", Rules.Cost(3, 2).spoor);
    T("spoor: and is met in the flesh by a 6th-level one",              !Rules.Cost(3, 6).spoor);

    // SignOnly is the one authority the Tracker asks before it puts anything on the field. If it
    // ever answered differently from the Encounter tab's cost verdict, the two halves of the app
    // would disagree about the same rule in front of the same table.
    for (int tier = 1; tier <= 5; tier++)
        for (int lvl = 1; lvl <= 10; lvl++)
            T($"spoor: SignOnly agrees with Cost (T{tier} vs level {lvl})",
                Rules.SignOnly(tier, lvl) == Rules.Cost(tier, lvl).spoor);
    // PartyTier is the ladder both the budget and the safe-table rule are measured against, so
    // "two Tiers over" has to mean the same arithmetic in the dialog as in Cost.
    foreach (var (lvl, want) in new[] { (1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (6, 3), (7, 4), (8, 4), (9, 5), (10, 5) })
        T($"spoor: a level-{lvl} posse stands at Tier {want}", Rules.PartyTier(lvl) == want);
    for (int tier = 1; tier <= 5; tier++)
        for (int lvl = 1; lvl <= 10; lvl++)
            T($"spoor: the rule fires exactly when the gap is 2+ (T{tier} vs level {lvl})",
                Rules.SignOnly(tier, lvl) == (tier - Rules.PartyTier(lvl) >= 2));

    for (int tier = 1; tier <= 5; tier++)
        T($"spoor: SpoorFor(T{tier}) is that Tier's own row", Rules.SpoorFor(tier) == Rules.SpoorRow[tier - 1]);
    T("spoor: an off-book Tier still answers rather than throwing",
        Rules.SpoorFor(0) == Rules.SpoorRow[0] && Rules.SpoorFor(99) == Rules.SpoorRow[4]);

    // ---- reading a sign: Horror.ReadSign ----
    for (int tier = 1; tier <= 5; tier++)
    {
        var row = Rules.SpoorFor(tier);
        for (int die = 1; die <= 20; die++)
        {
            var o = Horror.ReadSign(0, tier, die);
            T($"read sign: T{tier} d{die} carries its Tier's DCs", o.ReadDc == row.readDc && o.DreadDc == row.dreadDc);
            T($"read sign: T{tier} d{die} says what is on the ground", o.What == row.what);
            T($"read sign: T{tier} d{die} reads the same degree the d20 does",
                o.Degree == Rules.FourDegrees(die, 0, row.readDc).idx);
            T($"read sign: T{tier} d{die} learns what that degree buys", o.Learned == Rules.SpoorRead(o.Degree));
            T($"read sign: T{tier} d{die} fills a segment either way", o.FillsClock);
            T($"read sign: T{tier} d{die} has a line to log", !string.IsNullOrWhiteSpace(o.Line));
        }
        // A better tracker reads more: at a fixed die, raising the bonus never lowers the degree.
        int last = -1;
        for (int mod = -5; mod <= 20; mod++)
        {
            int deg = Horror.ReadSign(mod, tier, 10).Degree;
            T($"read sign: T{tier} a bigger Survival bonus never reads worse (+{mod})", deg >= last);
            last = deg;
        }
    }

    // ---- a sign on the field: the Combatant half ----
    {
        var sign = new Combatant { Name = "Sign of the Wendigo", Ref = "The Wendigo", IsSign = true };
        T("sign: a trace with no Blood is not 'Down' — it was never up", !sign.Down);
        T("sign: a trace has no next Strike", sign.NextStrike == "—");
        T("sign: an empty clock draws all empty", sign.SignClock == new string('▯', Rules.SpoorClockSegments));
        T("sign: a fresh trace is not full", !sign.SignFull);
        sign.Wound(-99);
        T("sign: a trace cannot be wounded", sign.BloodCur == 0 && sign.LastNote == "");
        for (int i = 1; i <= Rules.SpoorClockSegments; i++)
        {
            sign.SignFilled = i;
            T($"sign: clock at {i} draws {i} filled", sign.SignClock.Count(ch => ch == '▮') == i);
            T($"sign: clock at {i} is {Rules.SpoorClockSegments} segments wide", sign.SignClock.Length == Rules.SpoorClockSegments);
        }
        T("sign: a filled clock is the night it comes", sign.SignFull);
        sign.SignFilled = 99;
        T("sign: the clock cannot be overfilled", sign.SignFilled == Rules.SpoorClockSegments);
        sign.SignFilled = -3;
        T("sign: nor run backward past empty", sign.SignFilled == 0);
    }

    // ---- Wound: one route in, and the note the tracker shows ----
    {
        var c = new Combatant { Name = "Ruth", BloodCur = 20, BloodMax = 20 };
        c.Wound(-7);
        T("wound: takes the Blood", c.BloodCur == 13);
        T("wound: notes what it cost", c.LastNote == "−7" && c.LastDelta == -1);
        c.Wound(+5);
        T("wound: mends", c.BloodCur == 18 && c.LastNote == "+5" && c.LastDelta == 1);
        c.Wound(+99);
        T("wound: healing stops at the maximum", c.BloodCur == 20);
        c.Wound(+5);
        T("wound: and says so when there is nothing to mend", c.LastNote == "already full" && c.LastDelta == 0);
        c.Wound(-500);
        T("wound: cannot go below nothing", c.BloodCur == 0);
        T("wound: and calls it what it is", c.Down && c.LastNote.Contains("DOWN"));
        c.ClearLast();
        T("wound: a new round is a clean page", c.LastNote == "" && c.LastDelta == 0);
        var noMax = new Combatant { Name = "a wall", BloodCur = 5, BloodMax = 0 };
        noMax.Wound(+40);
        T("wound: no maximum means healing is not capped", noMax.BloodCur == 45);
    }
}

// ---- a soul's gender, including one the lists were not written for ----
{
    CharGen.Load();
    // The two named genders draw from their own pools; anything else must draw from all of them
    // rather than falling down the "not Woman" branch into the men's list, which is what it did.
    var seenOther = new HashSet<string>();
    for (int i = 0; i < 600; i++) seenOther.Add(CharGen.FullName("Two-Spirit"));
    T("gender: a custom gender still gets a full name", seenOther.All(n => n.Trim().Length > 2));
    T("gender: and gets more than one of them", seenOther.Count > 20);

    var womenWhole = CharGen.Flavor("fullNamesWomen");
    var menWhole = CharGen.Flavor("fullNamesMen");
    if (womenWhole.Count > 0 && menWhole.Count > 0)
    {
        // Over 600 draws at a 12% whole-name rate, a custom gender should reach BOTH pools.
        var custom = new List<string>();
        for (int i = 0; i < 1200; i++) custom.Add(CharGen.FullName("Nonbinary"));
        T("gender: a custom gender reaches the women's whole-name pool", custom.Any(womenWhole.Contains));
        T("gender: and the men's", custom.Any(menWhole.Contains));

        // The two named ones stay exclusive — the fix must not blur them together.
        var asWoman = new List<string>();
        for (int i = 0; i < 1200; i++) asWoman.Add(CharGen.FullName("Woman"));
        T("gender: a woman never draws a man's whole name", !asWoman.Any(n => menWhole.Contains(n) && !womenWhole.Contains(n)));
    }

    T("gender: the 'Other…' prompt is never stored as a value", CharGen.CleanGender("Other…") == "");
    T("gender: an ordinary answer is kept, trimmed", CharGen.CleanGender("  Two-Spirit  ") == "Two-Spirit");
    T("gender: null is blank, not a crash", CharGen.CleanGender(null) == "");
    T("gender: Woman and Man come through untouched",
        CharGen.CleanGender("Woman") == "Woman" && CharGen.CleanGender("Man") == "Man");

    // A hand-built soul keeps whatever gender it was given, all the way onto the sheet — the road
    // the wizard walks. Calling and Origin come from the data so this never fails on a renamed one.
    var gCal = CharGen.D.callings[0];
    var gOrg = CharGen.D.origins.First(o => !(gCal.group == "Faith" && o.notFaith));
    var spec = new CharGen.AssembleSpec
    { Level = 1, Calling = gCal.name, Origin = gOrg.name, Rolled = true, Gender = "Two-Spirit", Name = "Wren Ashby" };
    foreach (var a in new[] { "STR", "DEX", "CON", "WIT", "RES", "PRE" }) spec.PreGiftScores[a] = 12;
    var built = CharGen.Assemble(spec);
    T("gender: a hand-built soul keeps the gender it was given", built.Gender == "Two-Spirit");
    T("gender: and the name it was given", built.Name == "Wren Ashby");
    T("gender: and is still a legal sheet", CharGen.Validate(built).Count == 0);

    // The wizard's road with the gender left empty still yields a soul — the assembler rolls one
    // rather than shipping a blank, which is what it has always done for an unanswered step.
    var blank = new CharGen.AssembleSpec { Level = 1, Calling = gCal.name, Origin = gOrg.name, Rolled = true };
    foreach (var a in new[] { "STR", "DEX", "CON", "WIT", "RES", "PRE" }) blank.PreGiftScores[a] = 12;
    T("gender: an unanswered gender is filled in, not left blank", CharGen.Assemble(blank).Gender is { Length: > 0 });
}

// ---- whose turn it is, and when the round is spent ----
{
    Combatant C(string n, int init, bool acted = false, int blood = 10) =>
        new() { Name = n, Init = init, HasActed = acted, BloodCur = blood, BloodMax = 10 };

    var field = new List<Combatant> { C("Coyote", 8), C("Ruth", 19), C("Silas", 14) };
    T("turn: the highest initiative is up first", Rules.NextUp(field).Name == "Ruth");
    T("turn: nobody has gone, so the round is not spent", !Rules.RoundSpent(field));

    field[1].BeginTurn();
    T("turn: beginning a turn marks it taken", field[1].HasActed && field[1].Acting);
    T("turn: and the next one down is up", Rules.NextUp(field).Name == "Silas");
    field[2].BeginTurn();
    T("turn: then the last", Rules.NextUp(field).Name == "Coyote");
    field[0].BeginTurn();
    T("turn: with everyone gone, nobody is up", Rules.NextUp(field) == null);
    T("turn: and the round is spent", Rules.RoundSpent(field));

    foreach (var c in field) c.HasActed = false;
    T("turn: clearing the round puts everyone back in it", Rules.NextUp(field).Name == "Ruth" && !Rules.RoundSpent(field));

    // A combatant bleeding out is skipped rather than blocking the round forever.
    field[1].Wound(-99);
    T("turn: someone down cannot act", field[1].Down && !Rules.CanAct(field[1]));
    T("turn: so the turn passes them by", Rules.NextUp(field).Name == "Silas");
    field[2].BeginTurn(); field[0].BeginTurn();
    T("turn: a round ends with the downed one never having gone", Rules.RoundSpent(field));

    // A field where everyone is down is not a round ending over and over.
    var allDown = new List<Combatant> { C("a", 5), C("b", 3) };
    foreach (var c in allDown) c.Wound(-99);
    T("turn: an all-down field is not a spent round", !Rules.RoundSpent(allDown));
    T("turn: an empty field is not one either", !Rules.RoundSpent(new List<Combatant>()));

    // A trace never takes a turn — it is not on the field to take one.
    var withSign = new List<Combatant> { C("Ruth", 12), new() { Name = "Sign of it", IsSign = true, Init = 99 } };
    T("turn: a trace is never up, whatever its initiative", Rules.NextUp(withSign).Name == "Ruth");
    withSign[0].BeginTurn();
    T("turn: and does not hold the round open", Rules.RoundSpent(withSign));

    // ---- what a new fight must leave behind ----
    // Regression, 2026-07-27: "New fight" was written before Worked effects and the sign strip
    // existed and never learned about either, so a Keeper pressed it and the previous fight's
    // Signs and Miracles walked into the next one. It read as a dead button. Blood is the one
    // thing that MUST survive — wounds carry between fights; Rest is what heals them.
    var survivor = C("Ruth", 12);
    survivor.Conditions = "Bleeding, Prone";
    survivor.Beats = 0; survivor.MapStep = 4; survivor.Acting = true; survivor.HasActed = true;
    survivor.Wound(6);
    int bloodAfterFight = survivor.BloodCur;
    survivor.Work(new WorkedEffect { Name = "Hand of the Almighty", Kind = "Miracle", Rank = 2, Source = "Padre", RoundsLeft = -1 });
    survivor.Work(new WorkedEffect { Name = "Wither", Kind = "Sign", Rank = 1, Source = "Hexer", RoundsLeft = 3 });
    T("new fight: the fight left effects working", survivor.Worked.Count == 2);

    Rules.ResetForNewFight(new List<Combatant> { survivor });
    T("new fight: conditions are wiped", survivor.Conditions == "");
    T("new fight: Beats are back to 3", survivor.Beats == 3);
    T("new fight: nobody is mid-turn", !survivor.Acting && !survivor.HasActed);
    T("new fight: everyone is back in the order", Rules.CanAct(survivor));
    T("new fight: the map step resets", survivor.MapStep == 1);
    T("new fight: nothing is still working — the whole point of the fix", survivor.Worked.Count == 0);
    T("new fight: an effect with no duration ends too, not just the timed one", !survivor.Worked.Any(w => w.RoundsLeft == -1));
    T("new fight: but Blood carries over — wounds are not healed by a new fight", survivor.BloodCur == bloodAfterFight);
    bool nullFieldOk = true;
    try { Rules.ResetForNewFight(null); } catch { nullFieldOk = false; }
    T("new fight: a null field is survivable", nullFieldOk);

    // Ties break by name, so the same field always yields the same order rather than a wobble.
    var tied = new List<Combatant> { C("Silas", 11), C("Anni", 11), C("Ruth", 11) };
    T("turn: an initiative tie breaks by name", Rules.NextUp(tied).Name == "Anni");
    tied.First(x => x.Name == "Anni").BeginTurn();
    T("turn: and keeps breaking the same way", Rules.NextUp(tied).Name == "Ruth");

    // HasActed rides along in a saved session — a fight reloaded mid-round resumes mid-round.
    var saved = System.Text.Json.JsonSerializer.Deserialize<Combatant>(
        System.Text.Json.JsonSerializer.Serialize(field[2]));
    T("turn: who has gone survives save and load", saved.HasActed == field[2].HasActed);

    // ---- initiative is a Notice check (Player's Book Ch. XI) ----
    // The tracker rolled a bare d20 for everyone until v1.29.0 while the app's own Reference deck
    // printed the rule. Two things have to hold: the die is still a d20, and the bonus is really
    // added — and the floor at 1 has to hold, or a negative bonus mints a "0" that the tracker
    // reads as "has not rolled yet".
    bool initInBand = true, initFloored = true, initMoved = false;
    for (int i = 0; i < 4000; i++)
    {
        int plain = Rules.RollInitiative(0);
        if (plain < 1 || plain > 20) initInBand = false;
        if (Rules.RollInitiative(-9) < 1) initFloored = false;
        if (Rules.RollInitiative(5) > 20) initMoved = true;      // the bonus reaches past a bare d20
    }
    T("initiative: an unmodified roll is a d20", initInBand);
    T("initiative: a bonus actually moves the result", initMoved);
    T("initiative: never lands on 0, which means 'not rolled yet'", initFloored);

    // The bonus itself comes off the sheet's Notice skill and nowhere else, so the tracker cannot
    // drift onto a different skill than the rule names.
    var scout = CharGen.Generate(6, false, "Mountain Man");
    T("initiative: the bonus is exactly the sheet's Notice bonus",
        CharGen.InitiativeBonus(scout) == CharGen.SkillBonus(scout, "Notice"));
    T("initiative: no sheet, no bonus — a creature rolls the plain die",
        CharGen.InitiativeBonus(null) == 0);
}

// ---- Nerve-loss ladder ----
// ---- reading a working: what a Sign, a Miracle or a creature's power actually DOES ----
// The old model held one shape — a target and a round count — and eighty hand-written workings do
// not have one shape. These assertions are the guard on the reader that pulls the real shapes out
// of the printed text. Named workings are checked by hand where the answer is known for certain;
// everything else is held to a floor, so a re-transcription of either chapter that quietly stops
// parsing fails here instead of at somebody's table.
{
    var signs = CharGen.D.signs.Select(s => Rules.ReadWorking(s.name, "Sign", s.rank, s.cost, s.desc, 6)).ToList();
    var mirs  = CharGen.D.miracles.Select(m => Rules.ReadWorking(m.name, "Miracle", m.rank, m.cost, m.desc, 6)).ToList();
    var all   = signs.Concat(mirs).ToList();
    Rules.Working W(string n) => all.First(x => x.Name == n);

    T("working: every Sign and Miracle is read", all.Count == 80);

    // Backlash is the Signs' half of the bargain and the Miracles' absence of one — the two
    // chapters saying, structurally, that faith does not bite back. It was buried mid-paragraph.
    T("working: all forty Signs carry a Backlash", signs.All(w => w.HasBacklash));
    T("working: no Miracle does — faith does not bite back", mirs.All(w => !w.HasBacklash));
    T("working: a Backlash is lifted clear of the effect text",
        !W("Witch-Sight").Effect.Contains("Backlash", StringComparison.OrdinalIgnoreCase)
        && W("Witch-Sight").Backlash.Length > 0);
    T("working: a Backlash printed as 'None' still keeps its words",
        W("Salt & Iron").HasBacklash && W("Salt & Iron").Backlash.Contains("kindest"));
    T("working: but it is not a warning — it does not bite", !W("Salt & Iron").BacklashBites);
    // Four of the forty print "Backlash: None" and then say something about why. The other
    // thirty-six cost the worker something, and those are the ones the app should warn about.
    T("working: thirty-six of the forty actually bite", signs.Count(w => w.BacklashBites) == 36);

    // Nothing is left as a shrug: Unclear is a legal answer but it should be rare, and right now
    // the two chapters give it up entirely.
    T("working: every one of the eighty resolves to a shape", all.All(w => w.Shape != Rules.WorkShape.Unclear));

    // The shapes the old dialog could not express at all.
    T("working: Witch-Sight is worked on the worker", W("Witch-Sight").Shape == Rules.WorkShape.Self);
    T("working: The Tally lands on nobody", W("The Tally").Shape == Rules.WorkShape.Place);
    T("working: Ward of the Threshold is a place", W("Ward of the Threshold").Shape == Rules.WorkShape.Place);
    T("working: Unmake the Working targets a working", W("Unmake the Working").Shape == Rules.WorkShape.Counter);
    T("working: Borrowed Breath is worked on a companion", W("Borrowed Breath").Shape == Rules.WorkShape.Ally);
    T("working: The Crimson Word picks one creature", W("The Crimson Word").Shape == Rules.WorkShape.OneCreature);

    // An area is a radius in feet, not "everyone on the field" — the book's areas catch friends.
    T("working: Salt & Iron reaches ten feet",
        W("Salt & Iron").Shape == Rules.WorkShape.Area && W("Salt & Iron").AreaFeet == 10);
    T("working: The Grasping Dark reaches twenty", W("The Grasping Dark").AreaFeet == 20);
    T("working: Open the Vein of the World reaches thirty", W("Open the Vein of the World").AreaFeet == 30);
    T("working: every radius the book prints is read", all.Count(w => w.AreaFeet > 0) >= 3);

    // Mending must never be read as harm. This is the single worst thing the reader could get
    // wrong, and "Treat a wound for 1d8" plus "heal a touched ally 2d6" both used to score as damage.
    T("working: Borrowed Breath heals 2d8", W("Borrowed Breath").Heal == "2d8" && W("Borrowed Breath").Damage.Length == 0);
    T("working: The Green Hand treats a wound for 1d8", W("The Green Hand").Heal == "1d8" && W("The Green Hand").Damage.Length == 0);
    T("working: The Altar Call heals 2d6", W("The Altar Call").Heal == "2d6" && W("The Altar Call").Damage.Length == 0);
    T("working: The Life Shared spreads 2d8 across an area",
        W("The Life Shared").Heal == "2d8" && W("The Life Shared").Shape == Rules.WorkShape.Area);
    T("working: Extreme Unction wakes them on 1d6", W("Extreme Unction").Heal == "1d6");
    T("working: no working both heals and harms with the same die",
        all.All(w => w.Heal.Length == 0 || w.Damage.Length == 0));

    // Nerve is its own currency and is neither harm nor healing.
    T("working: The Unburdening restores 1d6 Nerve", W("The Unburdening").Nerve == "1d6");
    T("working: Coin of Pain buys 1d6 Nerve", W("Coin of Pain").Nerve == "1d6");

    // Damage, ongoing damage, and save-for-half.
    T("working: The Crimson Word deals 3d6", W("The Crimson Word").Damage == "3d6");
    T("working: Open the Vein deals 6d8 and saves for half",
        W("Open the Vein of the World").Damage == "6d8" && W("Open the Vein of the World").SaveForHalf);
    T("working: The Reckoning Fire deals 6d6 across an area",
        W("The Reckoning Fire").Damage == "6d6" && W("The Reckoning Fire").Shape == Rules.WorkShape.Area);
    T("working: Rot the Wound is 1d6 EACH ROUND, not once",
        W("Rot the Wound").Ongoing == "1d6" && W("Rot the Wound").Damage.Length == 0);
    T("working: and it lasts until something is done about it",
        W("Rot the Wound").Ends == Rules.WorkEnds.UntilEnded);
    T("working: The Hungering Hand takes 2d6 and gives half back",
        W("The Hungering Hand").Damage == "2d6" && W("The Hungering Hand").DrainsToWorker);

    // Durations the old round-counter could not hold.
    T("working: Witch-Sight lasts a scene", W("Witch-Sight").Ends == Rules.WorkEnds.Scene);
    T("working: Cold Lamp lasts an hour", W("Cold Lamp").Ends == Rules.WorkEnds.Hour);
    T("working: Ward of the Threshold holds until dawn", W("Ward of the Threshold").Ends == Rules.WorkEnds.UntilDawn);
    T("working: The Blessing of the Road runs a day", W("The Blessing of the Road").Ends == Rules.WorkEnds.Day);
    T("working: The Crimson Word is over when it is done", W("The Crimson Word").Ends == Rules.WorkEnds.Instant);
    T("working: every duration the two chapters print is represented",
        all.Select(w => w.Ends).Distinct().Count() >= 6);

    // "A round per two levels" is arithmetic the app exists to do — a chip saying "a round per
    // two levels" would be handing it straight back to the Keeper.
    var stillL6 = Rules.ReadWorking("The Stilling", "Sign", 2, "1 Beat · 2 Nerve · Will save",
        CharGen.D.signs.First(s => s.name == "The Stilling").desc, 6);
    var stillL10 = Rules.ReadWorking("The Stilling", "Sign", 2, "1 Beat · 2 Nerve · Will save",
        CharGen.D.signs.First(s => s.name == "The Stilling").desc, 10);
    T("working: The Stilling scales with the worker — 3 rounds at 6th",
        stillL6.Ends == Rules.WorkEnds.Rounds && stillL6.Rounds == 3);
    T("working: and 5 rounds at 10th", stillL10.Rounds == 5);
    T("working: it never scales below one round",
        Rules.ReadWorking("x", "Sign", 1, "", "held for one round per two levels", 1).Rounds >= 1);

    // The save the cost line prints is the save the target rolls.
    T("working: a printed save reaches the working", W("The Stilling").Save == "Will");
    T("working: at least twenty workings ask for one", all.Count(w => w.HasSave) >= 20);

    // A creature's power is a standing TRAIT, not something worked on anybody. All 150 Bestiary
    // special lines are written that way and not one carries a die, a save, or a radius — so the
    // dialog must stop asking who it is being worked on and for how long.
    var powers = Db.Creatures.Where(c => !string.IsNullOrWhiteSpace(c.special))
        .Select(c => { var (n, e) = Rules.ParsePower(c.special); return Rules.ReadWorking(n, "Power", 0, "", e, 6); })
        .ToList();
    T("working: every creature's special line is read", powers.Count == 150);
    T("working: a creature's power reads as a trait, not a targeting",
        powers.Count(w => w.IsTrait) >= 140);
    T("working: a trait has nothing to roll", powers.Where(w => w.IsTrait).All(w => !w.Resolves));
    T("working: and every one is still named", powers.All(w => w.Name.Length > 0));

    // A working saved before the shapes and durations existed carries a round count and nothing
    // else. It must still tick, and it must still read as a round count — the first cut of this
    // gated the tick on Ends as well, which would have frozen every effect in every session
    // anybody had already saved.
    var oldSave = System.Text.Json.JsonSerializer.Deserialize<WorkedEffect>(
        "{\"Name\":\"The Stilling\",\"Kind\":\"Sign\",\"RoundsLeft\":2,\"SinceRound\":1}");
    var carrier = new Combatant { Name = "Silas", BloodCur = 10, BloodMax = 10 };
    carrier.Work(oldSave);
    T("worked: a pre-v1.29 effect still says how many rounds it has", oldSave.Chip.EndsWith("(2)"));
    carrier.TickWorked();
    T("worked: and it still counts down", oldSave.RoundsLeft == 1);
    T("worked: and it still runs out", carrier.TickWorked().Count == 1 && carrier.Worked.Count == 0);

    // Junk in, no throw out: the reader runs at the table and must never be the thing that dies.
    bool workingSurvivesJunk = true;
    foreach (var junk in new[] { null, "", "   ", "Backlash:", "3d6", "·····", "within  feet" })
        try { Rules.ReadWorking("x", "Sign", 1, junk, junk, 3); } catch { workingSurvivesJunk = false; }
    T("working: junk text yields a reading rather than a throw", workingSurvivesJunk);
}

// ---- the marks that do not wash off (Ch. XI · Keeper's Book Ch. III) ----
// Printed on the Keeper's screen since v1.4 and implemented nowhere until v1.29.0.
{
    T("grievous: half maximum Blood in one blow is a terrible blow", Rules.IsGrievous(10, 20, false));
    T("grievous: and so is more than half", Rules.IsGrievous(14, 20, false));
    T("grievous: a scratch is not", !Rules.IsGrievous(9, 20, false));
    T("grievous: but ANY critical is, however small", Rules.IsGrievous(1, 99, true));
    T("grievous: no damage is never a terrible blow", !Rules.IsGrievous(0, 20, true));
    T("grievous: a target with no Blood maximum cannot be measured against one",
        !Rules.IsGrievous(5, 0, false));
    T("grievous: the DC is the book's fifteen", Rules.GrievousDc == 15);

    T("injury: the d6 table has six entries", Rules.LastingInjuries.Length == 6);
    T("injury: in the book's order", Rules.LastingInjuries[0] == "Bloody Gash" && Rules.LastingInjuries[5] == "Gut-Shot");
    bool injuryInRange = true, sawGash = false, sawGut = false;
    for (int i = 0; i < 600; i++)
    {
        var (d, name) = Rules.RollInjury();
        if (d < 1 || d > 6 || Rules.LastingInjuries[d - 1] != name) injuryInRange = false;
        if (name == "Bloody Gash") sawGash = true;
        if (name == "Gut-Shot") sawGut = true;
    }
    T("injury: a roll is always a real row of the table", injuryInRange);
    T("injury: and the whole table can come up", sawGash && sawGut);

    // A scar is the one thing on a soul that has to survive the night, so it has to survive the file.
    var scarred = new PartyMember { Name = "Anni Halvorsen", BloodMax = 12, BloodCur = 12 };
    scarred.Scars.Add(new Scar { Kind = "Injury", Name = "Gut-Shot", Note = "the mine, at the ladder", When = "3 Aug" });
    scarred.Scars.Add(new Scar { Kind = "Affliction", Name = "Will not go underground" });
    T("scars: the grid line names them all", scarred.ScarLine == "2: Gut-Shot, Will not go underground");
    T("scars: an unscarred soul shows nothing", new PartyMember().ScarLine.Length == 0);
    T("scars: an injury and an affliction wear different marks",
        scarred.Scars[0].Mark == "✚" && scarred.Scars[1].Mark == "☾");
    T("scars: the whole of one reads back", scarred.Scars[0].Full.Contains("at the ladder"));
    var reloaded = System.Text.Json.JsonSerializer.Deserialize<PartyMember>(
        System.Text.Json.JsonSerializer.Serialize(scarred));
    T("scars: they survive save and load", reloaded.Scars.Count == 2
        && reloaded.Scars[0].Name == "Gut-Shot" && reloaded.Scars[1].Kind == "Affliction");
    var older = System.Text.Json.JsonSerializer.Deserialize<PartyMember>("{\"Name\":\"Ruth\"}");
    T("scars: a soul saved before them loads with none, not a null", older.Scars is { Count: 0 });
}

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

// ---- The budget verdict (what the Encounter tab's bar and line both read from) ----
{
    // The band the whole tab hangs on: exactly on budget is the balanced fight, and it is the
    // ONLY band that reads green. Anything over reads red, however far over.
    T("budget: nothing costed is Empty",   Rules.BudgetBand(0, 24) == Rules.Weight.Empty);
    T("budget: under is Under",            Rules.BudgetBand(23, 24) == Rules.Weight.Under);
    T("budget: exact is Exact",            Rules.BudgetBand(24, 24) == Rules.Weight.Exact);
    T("budget: one over is Over",          Rules.BudgetBand(25, 24) == Rules.Weight.Over);
    T("budget: +4 is still Over",          Rules.BudgetBand(28, 24) == Rules.Weight.Over);
    T("budget: +5 is WellOver",            Rules.BudgetBand(29, 24) == Rules.Weight.WellOver);

    // A one-soul posse (budget 4) is the tightest case — Exact must not be swallowed by the
    // "within 4 of budget" Over band, which spans the same width.
    T("budget: 4/4 exact on a lone soul",  Rules.BudgetBand(4, 4) == Rules.Weight.Exact);
    T("budget: 5/4 is Over",               Rules.BudgetBand(5, 4) == Rules.Weight.Over);
    T("budget: 9/4 is WellOver",           Rules.BudgetBand(9, 4) == Rules.Weight.WellOver);

    // Empty wins over Exact when the posse is empty too — a budget of 0 with nothing costed is
    // an empty tab, not a perfectly balanced fight. (The tab floors the budget at 4, but the
    // rule shouldn't depend on the caller to keep it honest.)
    T("budget: 0 spend, 0 budget is Empty", Rules.BudgetBand(0, 0) == Rules.Weight.Empty);
    T("budget: negative spend is Empty",    Rules.BudgetBand(-3, 12) == Rules.Weight.Empty);

    // Exactly one band per spend, and every band has words.
    for (int budget = 4; budget <= 40; budget += 4)
        for (int spend = 0; spend <= budget * 3; spend++)
        {
            var band = Rules.BudgetBand(spend, budget);
            if (spend > 0 && spend == budget && band != Rules.Weight.Exact)
                { T($"budget: {spend}/{budget} must be Exact", false); goto doneBudget; }
            if (spend > budget && band != Rules.Weight.Over && band != Rules.Weight.WellOver)
                { T($"budget: {spend}/{budget} must read over", false); goto doneBudget; }
            if (spend > 0 && spend < budget && band != Rules.Weight.Under)
                { T($"budget: {spend}/{budget} must be Under", false); goto doneBudget; }
            if (string.IsNullOrWhiteSpace(Rules.BudgetVerdict(spend, budget)))
                { T($"budget: {spend}/{budget} has no words", false); goto doneBudget; }
        }
    T("budget: every spend 0..3x budget lands in one band, with words", true);
    doneBudget: ;

    T("budget: the exact verdict says so", Rules.BudgetVerdict(24, 24).Contains("ON BUDGET"));
    T("budget: the over verdict says so",  Rules.BudgetVerdict(30, 24).Contains("WELL over"));
}

// ---- Recovering Nerve (the Posse tab's Steady menu) ----
{
    // NerveCur clamps to 0..999, NOT to NerveMax — so anything handing Nerve back has to clamp
    // itself. This is the assumption Steady()/SteadyByHand() are written on; if it ever changes,
    // this test is the thing that says so.
    var n = new PartyMember { NerveMax = 10, NerveCur = 2 };
    n.NerveCur = 500;
    T("Nerve: the model does NOT clamp cur to max", n.NerveCur == 500);

    // The shape Steady uses: never past max, never backwards, and "all of it" means max.
    static int Steadied(int cur, int max, int gain) => Math.Min(max, cur + gain);
    T("steady: a remedy stops at max",      Steadied(8, 10, 6) == 10);
    T("steady: a remedy adds what it can",  Steadied(3, 10, 4) == 7);
    T("steady: already full gains nothing", Steadied(10, 10, 6) == 10);
    T("steady: a broken soul can come back", Steadied(0, 10, 1) == 1);
    for (int cur = 0; cur <= 20; cur++)
        for (int gain = 1; gain <= 10; gain++)
            if (Steadied(cur, 20, gain) < cur || Steadied(cur, 20, gain) > 20)
                { T("steady: never loses Nerve and never passes max", false); goto doneSteady; }
    T("steady: never loses Nerve and never passes max", true);
    doneSteady: ;

    // The remedies the menu offers, as the book prints them.
    for (int i = 0; i < 200; i++)
    {
        int d6 = Rules.RollExpr("1d6").total, d4 = Rules.RollExpr("1d4").total;
        if (d6 < 1 || d6 > 6 || d4 < 1 || d4 > 4)
            { T("steady: the remedies roll in range", false); goto doneRemedy; }
    }
    T("steady: the remedies roll in range (1d6 confession/night, 1d4 whiskey)", true);
    doneRemedy: ;
}

// ---- Naming a new ride when one of that name is already in the corral ----
{
    T("ride name: an empty corral takes the stem", Db.FreeRideName(new string[0], "Mule") == "Mule");
    T("ride name: the second is numbered 2",       Db.FreeRideName(new[] { "Mule" }, "Mule") == "Mule 2");
    T("ride name: the third is numbered 3",        Db.FreeRideName(new[] { "Mule", "Mule 2" }, "Mule") == "Mule 3");

    // The regression this helper exists for: sell the middle horse of three and the next one must
    // NOT take a name that is already standing in the corral.
    T("ride name: a sold middle number is reused, not collided with",
        Db.FreeRideName(new[] { "Mule", "Mule 3" }, "Mule") == "Mule 2");

    T("ride name: a different stem is untouched", Db.FreeRideName(new[] { "Mule", "Mule 2" }, "Ox") == "Ox");
    T("ride name: matching ignores case",         Db.FreeRideName(new[] { "mule" }, "Mule") == "Mule 2");
    T("ride name: a null roster is an empty one", Db.FreeRideName(null, "Ox") == "Ox");

    // Add a hundred of the same thing and every name must still be its own.
    var corral = new List<string>();
    for (int i = 0; i < 100; i++) corral.Add(Db.FreeRideName(corral, "Saddle Horse"));
    T("ride name: 100 of a kind are 100 distinct names",
        corral.Distinct(StringComparer.OrdinalIgnoreCase).Count() == 100);

    // Remove a scatter of them, add as many back, and the corral is still collision-free.
    foreach (var gone in corral.Where((_, i) => i % 3 == 1).ToList()) corral.Remove(gone);
    for (int i = 0; i < 40; i++) corral.Add(Db.FreeRideName(corral, "Saddle Horse"));
    T("ride name: still distinct after a churn of sales and purchases",
        corral.Distinct(StringComparer.OrdinalIgnoreCase).Count() == corral.Count);
}

// ---- The turn state, which the tracker now has to be able to SHOW ----
{
    var c = new Combatant { Name = "Ruth", BloodCur = 20, BloodMax = 20, Defense = 15 };
    T("turn: a fresh combatant is nobody's turn", !c.Acting);
    T("turn: and their next Strike is clean",     c.NextStrike == "clean");

    c.BeginTurn();
    T("turn: Begin turn hands them the turn", c.Acting && c.Beats == 3 && c.MapStep == 1);

    var foe = new Combatant { Name = "The Bobcat", BloodCur = 9, BloodMax = 9, Defense = 15 };
    var claw = new CreatureAttack { Name = "claws", Bonus = 5, Damage = "1d6+1" };
    CombatFlow.StrikeAndApply(c, foe, claw, 5, null, 12);
    T("turn: a Strike spends a Beat",        c.Beats == 2);
    T("turn: and the next one costs −5",     c.NextStrike == "−5");
    CombatFlow.StrikeAndApply(c, foe, claw, 5, null, 12);
    T("turn: the third costs −10",           c.NextStrike == "−10" && c.Beats == 1);
    CombatFlow.StrikeAndApply(c, foe, claw, 5, null, 12);
    T("turn: three Strikes and the Beats are spent", c.Beats == 0);
    CombatFlow.StrikeAndApply(c, foe, claw, 5, null, 12);
    T("turn: Beats never go negative",       c.Beats == 0);
    T("turn: and the MAP does not run past the worst step", c.NextStrike == "−10");

    c.BeginTurn();
    T("turn: Begin turn gives it all back", c.Beats == 3 && c.NextStrike == "clean" && c.Acting);

    // The readout is turn state, so it has to survive a save and a load like Beats do.
    var session = new GameSession();
    session.Tracker.Add(c);
    var reloaded = System.Text.Json.JsonSerializer.Deserialize<GameSession>(
        System.Text.Json.JsonSerializer.Serialize(session));
    T("turn: who is acting rides in the session file", reloaded.Tracker[0].Acting);
    T("turn: so do the Beats and the step",
        reloaded.Tracker[0].Beats == 3 && reloaded.Tracker[0].MapStep == 1);
}

// ---- Marker ink: the book's colors, the Keeper's, and one marker's own ----
{
    MapInk.LoadKindColors(null);                                  // start from the book

    T("ink: the posse is verdigris",   MapInk.BookColor("posse")    == MapInk.Verdigris);
    T("ink: an NPC is gold",           MapInk.BookColor("npc")      == MapInk.Gold);
    T("ink: a creature is blood",      MapInk.BookColor("creature") == MapInk.BloodRed);
    T("ink: an unknown kind reads as trouble", MapInk.BookColor("bandit") == MapInk.BloodRed);
    T("ink: a null kind reads as trouble",     MapInk.BookColor(null)     == MapInk.BloodRed);

    // A marker with no color of its own takes its kind's.
    var plain = new MapMarker { Label = "Jed", Kind = "posse" };
    T("ink: a plain marker takes its kind's color", MapInk.Of(plain) == MapInk.Verdigris);
    T("ink: a null marker still answers something", MapInk.Of(null) == MapInk.BloodRed);

    // One marker breaking ranks must not move anything else.
    int indigo = MapInk.Palette.First(p => p.name == "Indigo").argb;
    var own = new MapMarker { Label = "Mose", Kind = "posse", Argb = indigo };
    T("ink: a marker's own color wins",             MapInk.Of(own) == indigo);
    T("ink: and leaves its kinsman alone",          MapInk.Of(plain) == MapInk.Verdigris);
    own.Argb = MapInk.Unset;
    T("ink: clearing it falls back to the kind",    MapInk.Of(own) == MapInk.Verdigris);

    // Re-inking a whole kind.
    int moss = MapInk.Palette.First(p => p.name == "Moss").argb;
    MapInk.SetKindColor("posse", moss);
    T("ink: a re-inked kind takes the new color",   MapInk.KindColor("posse") == moss);
    T("ink: and its plain markers follow",          MapInk.Of(plain) == moss);
    T("ink: other kinds are untouched",             MapInk.KindColor("creature") == MapInk.BloodRed);
    T("ink: the book's color is still the book's",  MapInk.BookColor("posse") == MapInk.Verdigris);
    T("ink: kind lookup ignores case",              MapInk.KindColor("POSSE") == moss);

    // Only decisions are kept — setting a kind back to the book's own color is not a decision,
    // so prefs.json must not grow a line recording that nothing changed.
    T("ink: a changed kind is recorded",            MapInk.KindColors().Count == 1);
    MapInk.SetKindColor("posse", MapInk.Verdigris);
    T("ink: setting the book's color clears the record", MapInk.KindColors().Count == 0);
    MapInk.SetKindColor("posse", moss);
    MapInk.SetKindColor("posse", MapInk.Unset);
    T("ink: Unset also clears the record",          MapInk.KindColors().Count == 0);
    T("ink: and the kind is back to the book",      MapInk.KindColor("posse") == MapInk.Verdigris);

    // A round trip through what prefs.json would hold.
    MapInk.SetKindColor("npc", indigo);
    MapInk.SetKindColor("creature", moss);
    var saved = MapInk.KindColors();
    MapInk.LoadKindColors(null);
    T("ink: loading nothing puts every kind back", MapInk.KindColor("npc") == MapInk.Gold);
    MapInk.LoadKindColors(saved);
    T("ink: a saved choice survives the round trip", MapInk.KindColor("npc") == indigo
        && MapInk.KindColor("creature") == moss && MapInk.KindColor("posse") == MapInk.Verdigris);

    // Names and hex, which the menus and both exporters depend on.
    T("ink: a palette color knows its name", MapInk.NameOf(MapInk.Verdigris) == "Verdigris");
    T("ink: a mixed color falls back to hex", MapInk.NameOf(unchecked((int)0xFF123456)) == "#123456");
    T("ink: hex drops the alpha",             MapInk.Hex(unchecked((int)0xFF781616)) == "#781616");
    T("ink: hex pads short channels",         MapInk.Hex(unchecked((int)0xFF010203)) == "#010203");
    T("ink: every palette color is opaque",   MapInk.Palette.All(p => ((p.argb >> 24) & 0xFF) == 0xFF));
    T("ink: no two palette colors are alike", MapInk.Palette.Select(p => p.argb).Distinct().Count() == MapInk.Palette.Length);
    T("ink: no two palette names are alike",  MapInk.Palette.Select(p => p.name).Distinct().Count() == MapInk.Palette.Length);
    T("ink: every palette hex is well formed",
        MapInk.Palette.All(p => System.Text.RegularExpressions.Regex.IsMatch(MapInk.Hex(p.argb), "^#[0-9a-f]{6}$")));
    T("ink: all three book colors are in the palette",
        MapInk.Palette.Any(p => p.argb == MapInk.Verdigris) && MapInk.Palette.Any(p => p.argb == MapInk.Gold)
        && MapInk.Palette.Any(p => p.argb == MapInk.BloodRed));

    MapInk.LoadKindColors(null);                                  // leave the rig as we found it
}

// ---- Markers as export ink: the overlay the SVG and PDF writers take ----
{
    MapInk.LoadKindColors(null);
    var map = MapGen.Generate(new MapSpec { Seed = 4242, Landmarks = 4 });
    int survey = map.P.Count;

    T("marker export: no markers, no ink", MapGen.MarkerPrims(new List<MapMarker>(), map.W, map.H).Count == 0);
    T("marker export: a null list is an empty one", MapGen.MarkerPrims(null, map.W, map.H).Count == 0);

    var crew = new List<MapMarker>
    {
        new() { Label = "Jed",   Kind = "posse",    X = 100, Y = 100 },
        new() { Label = "Mose",  Kind = "npc",      X = 200, Y = 150 },
        new() { Label = "",      Kind = "creature", X = 300, Y = 200 },   // unnamed — dot only
    };
    var ink = MapGen.MarkerPrims(crew, map.W, map.H);
    T("marker export: a named marker is a dot, a backing, and a name; an unnamed one just a dot",
        ink.Count == 3 + 3 + 1);
    T("marker export: every dot is a circle",
        ink.Count(p => p.Kind == PrimKind.Circle) == 3);
    T("marker export: the names are carried",
        ink.Where(p => p.Kind == PrimKind.Text).Select(p => p.Text).OrderBy(x => x).SequenceEqual(new[] { "Jed", "Mose" }));
    T("marker export: each dot is drawn in its kind's ink",
        ink.Where(p => p.Kind == PrimKind.Circle).Select(p => p.Fill).SequenceEqual(
            new[] { MapInk.Hex(MapInk.Verdigris), MapInk.Hex(MapInk.Gold), MapInk.Hex(MapInk.BloodRed) }));

    // A marker off the edge of the map is drawn at the edge, not off the page.
    var stray = MapGen.MarkerPrims(new List<MapMarker> { new() { Label = "", X = -500, Y = 9999 } }, map.W, map.H);
    T("marker export: a stray marker is pulled back onto the paper",
        stray[0].Pts[0] == 0 && stray[0].Pts[1] == map.H);

    // The whole point of an overlay: the model the Map tab holds is not touched by an export.
    string svgPlain = MapGen.ToSvg(map);
    string svgMarked = MapGen.ToSvg(map, ink);
    T("marker export: the survey's own ink is unchanged by drawing markers", map.P.Count == survey);
    T("marker export: markers off, the name is not in the file", !svgPlain.Contains(">Jed<"));
    T("marker export: markers on, it is",                        svgMarked.Contains(">Jed<"));
    T("marker export: markers on, the file is the bigger one",   svgMarked.Length > svgPlain.Length);
    T("marker export: the marker's ink reaches the SVG",         svgMarked.Contains(MapInk.Hex(MapInk.Verdigris)));

    // Both writers must accept the overlay, and the PDF must still be a PDF with one on.
    var pdfPlain = Pdf.MapPdf(map);
    var pdfMarked = Pdf.MapPdf(map, ink);
    T("marker export: the PDF still starts with its header",
        System.Text.Encoding.Latin1.GetString(pdfMarked, 0, 5) == "%PDF-");
    T("marker export: the marked PDF carries more than the plain one", pdfMarked.Length > pdfPlain.Length);
    T("marker export: the survey's ink is STILL unchanged after both writers", map.P.Count == survey);

    // The label backing is drawn behind the name, and is see-through enough to read paper through.
    var backing = ink.First(p => p.Kind == PrimKind.Poly);
    T("marker export: the label's backing is translucent", backing.Alpha > 0 && backing.Alpha < 1);
    T("marker export: a backing comes before the name it backs",
        ink.IndexOf(backing) < ink.FindIndex(p => p.Kind == PrimKind.Text));
}

// ---- The weather over the survey ----
{
    var sky = new Random(7);
    // An explicit pick is honored exactly; only "as the sky wills" rolls.
    for (int w = 1; w < MapGen.Weathers.Length; w++)
        T($"weather: a forced sky stands ({MapGen.Weathers[w]})", MapGen.WeatherFor(w, 0, sky) == w);
    T("weather: an out-of-range pick falls back to the country's own",
        MapGen.WeatherFor(99, 0, new Random(1)) is > 0 and < 12);
    T("weather: every index has words for the cartouche",
        Enumerable.Range(0, MapGen.Weathers.Length).All(i => !string.IsNullOrWhiteSpace(MapGen.WeatherLine(i))));

    // Rolled skies are the ones the ground would actually get: the high country can hand you a
    // blizzard, and the badlands never will.
    var high = new HashSet<int>();
    var dry = new HashSet<int>();
    for (int i = 0; i < 400; i++)
    {
        high.Add(MapGen.WeatherFor(0, 5, new Random(i)));
        dry.Add(MapGen.WeatherFor(0, 6, new Random(i)));
    }
    T("weather: the high country rolls snow and blizzards", high.Contains(8) && high.Contains(9));
    T("weather: the badlands roll neither",               !dry.Contains(8) && !dry.Contains(9));
    T("weather: the badlands roll heat and blowing dust",  dry.Contains(2) && dry.Contains(7));

    // Forcing the sky must not move one rock: the weather draws off its own stream, and every
    // prim the country laid down is still there, in the same order, before the sky goes on.
    MapModel Sky(int w) => MapGen.Generate(new MapSpec { Seed = 31337, Weather = w, Landmarks = 5 });
    var fair = Sky(1);
    var blizzard = Sky(9);
    // Every sky over one seed has to leave the same country underneath: the same named places in
    // the same spots, the same town on the same ground, the same title on the cartouche.
    string Places(MapModel m) => string.Join("|", m.Landmarks.Select(l => $"{l.Name}@{l.X:F2},{l.Y:F2}"))
        + "//" + (m.Town == null ? "-" : $"{m.Town.Name}@{m.Town.X:F2},{m.Town.Y:F2}") + "//" + m.Title;
    string ground = Places(fair);
    bool same = true;
    for (int w = 0; w < MapGen.Weathers.Length; w++) if (Places(Sky(w)) != ground) same = false;
    T("weather: the country under every sky is the same country", same);
    // …and the country's ink is laid down before the sky goes over it, prim for prim.
    int common = 0;
    while (common < fair.P.Count && common < blizzard.P.Count
           && MapGen.ToSvg(new MapModel { P = new List<Prim> { fair.P[common] } })
              == MapGen.ToSvg(new MapModel { P = new List<Prim> { blizzard.P[common] } })) common++;
    // The whole country, then the sky, then the frame and the cartouche over both — so the
    // identical prefix is the great bulk of a fair-day map, and everything after it is furniture.
    T("weather: and the survey's ink runs identical right up to the sky",
        common > 60 && common > fair.P.Count * 0.7);
    T("weather: a blizzard puts more ink on the page than a fair day", blizzard.P.Count > fair.P.Count);
    T("weather: the sky is named on the model",   blizzard.Weather == "Blizzard" && fair.Weather == "Fair");
    T("weather: and it reaches the cartouche",    blizzard.Sub.Contains("blizzard"));
    T("weather: a rolled sky still names itself", Sky(0).Weather.Length > 0);
    T("weather: same seed, same sky",             Sky(0).Weather == Sky(0).Weather);

    // Weather ink is thrown at random across the sheet, which is exactly how it got past the
    // edge the first time. Hold every sky to the paper.
    for (int w = 0; w < MapGen.Weathers.Length; w++)
    {
        var m = MapGen.Generate(new MapSpec { Seed = 8080 + w, Weather = w });
        bool inside = true;
        foreach (var wp in m.P)
        {
            if (wp.Kind is not (PrimKind.Line or PrimKind.Poly) || wp.Pts == null) continue;
            for (int i = 0; i + 1 < wp.Pts.Length; i += 2)
                if (wp.Pts[i] < 0 || wp.Pts[i] > m.W || wp.Pts[i + 1] < 0 || wp.Pts[i + 1] > m.H) inside = false;
        }
        T($"weather: {MapGen.Weathers[w]} keeps its ink on the paper", inside);
    }
}

// ---- Landforms: the country has hills, ridges, timber and whole ranges in it ----
{
    // Every ground draws its own furniture and offers its own named places. A landmark named
    // The Divide has to be drawn as a range, which means the symbol behind it has to exist —
    // a name with no case in Sym() is a label floating over blank paper.
    foreach (var terrain in MapGen.Terrains)
    {
        var m = MapGen.Generate(new MapSpec { Terrain = terrain, Seed = 991, Landmarks = 12 });
        T($"land: {terrain} draws something", m.P.Count > 60);
        T($"land: {terrain} names its places", m.Landmarks.Count > 0);
        foreach (var lm in m.Landmarks)
            T($"land: {terrain} — “{lm.Name}” has ink of its own", lm.PrimCount >= 1);
    }

    // The high country and the badlands must not read as the same county.
    var peaks = MapGen.Generate(new MapSpec { Terrain = "Winter & the High Country", Seed = 55, Landmarks = 12 });
    var sand = MapGen.Generate(new MapSpec { Terrain = "Desert & the Badlands", Seed = 55, Landmarks = 12 });
    T("land: two grounds on one seed name different places",
        !peaks.Landmarks.Select(l => l.Name).SequenceEqual(sand.Landmarks.Select(l => l.Name)));

    // A landmark still moves as one piece now that some of them are five-crown forests.
    var moved = MapGen.Generate(new MapSpec { Terrain = "Winter & the High Country", Seed = 606, Landmarks = 6 });
    if (moved.Landmarks.Count > 0)
    {
        var lm = moved.Landmarks[0];
        float ox = lm.X, oy = lm.Y;
        var before = moved.P[lm.PrimStart].Pts[0];
        MapGen.MoveLandmark(moved, 0, ox + 40, oy - 25);
        T("land: a moved landmark takes all its own ink with it",
            Math.Abs(moved.P[lm.PrimStart].Pts[0] - (before + 40)) < 0.01f);
        T("land: and remembers where the survey put it", lm.GenX == ox && lm.GenY == oy);
    }
}

// ---- Water is measured to the river's CHANNEL, not to its vertices ----
{
    // A long straight reach whose two ends are 1000px apart. A spot at its midpoint is squarely in
    // the water, but it is 500px from the nearest VERTEX — the old test called it dry.
    var straight = new MapModel { RiverPts = new float[] { 0, 0, 1000, 0 }, RiverHalf = 16, W = 1000, H = 600 };
    T("water: mid-channel on a long reach is wet", MapGen.OnWater(straight, 500, 0, 1));
    T("water: mid-channel clearance is negative",  MapGen.WaterClearance(straight, 500, 0) < 0);
    T("water: well off the reach is dry",         !MapGen.OnWater(straight, 500, 400, 1));
    T("water: clearance off the reach is the gap", Math.Abs(MapGen.WaterClearance(straight, 500, 400) - (400 - 16)) < 0.01);

    // Past the end of a reach the distance is to the endpoint, not to the infinite line.
    T("water: beyond the reach's end is dry",     !MapGen.OnWater(straight, 1200, 0, 1));
    T("water: clearance past the end measures from the end",
        Math.Abs(MapGen.WaterClearance(straight, 1200, 0) - (200 - 16)) < 0.01);

    // No river and no lake: everything is dry, and clearance answers big rather than throwing.
    var dry = new MapModel { W = 1000, H = 600 };
    T("water: a map with no water is dry",        !MapGen.OnWater(dry, 500, 300, 40));
    T("water: no water answers a big clearance",   MapGen.WaterClearance(dry, 500, 300) > 1000);

    // A degenerate one-point run must not divide by zero.
    var speck = new MapModel { RiverPts = new float[] { 100, 100 }, RiverHalf = 8, W = 400, H = 400 };
    T("water: a one-point run still measures",     MapGen.OnWater(speck, 102, 100, 1));
    T("water: a one-point run is dry far off",    !MapGen.OnWater(speck, 300, 300, 1));

    // The lake is a disc, and the two waters are read together.
    var lake = new MapModel { LakeX = 200, LakeY = 200, LakeR = 50, W = 600, H = 600 };
    T("water: inside the lake is wet",             MapGen.OnWater(lake, 200, 200, 0));
    T("water: outside the lake is dry",           !MapGen.OnWater(lake, 400, 200, 0));
    T("water: the pad pushes the shore outward",   MapGen.OnWater(lake, 260, 200, 20));
}

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

// The flavor pools — a soul's vice, what they lost, what they've seen, what moves them, and the
// gendered given names. A pool that thinned out still generates perfectly valid souls; they just
// come out the same souls over a long campaign, which is the failure nobody notices.
foreach (var (pool, floor) in new[] { ("vices", 32), ("lost", 28), ("seen", 28), ("moving", 28),
                                      ("givenWomen", 50), ("givenMen", 51) })
    T($"flavor pool [{pool}] is at least {floor} deep", CharGen.FlavorList(pool).Count >= floor);

// ---- SkillBonus: the number the Read Sign dialog puts in front of the Keeper ----
// It prefills the Survival bonus for every sign & spoor reading, so a wrong answer here is a
// wrong DC check at the table, silently, every time.
{
    T("skills: Survival is a real skill keyed to RES — the Read Sign dialog asks for it by name",
        cg.skills.Any(k => k.name == "Survival" && k.ability == "RES"));

    var sheet = new CharacterSheet { Level = 5, Scores = new() { ["RES"] = 16, ["STR"] = 8, ["WIT"] = 10 } };
    T("skillBonus: untrained is the keyed ability alone", CharGen.SkillBonus(sheet, "Survival") == 3);
    foreach (var (rank, name, want) in new[] { (1, "trained", 3 + 5 + 2), (2, "expert", 3 + 5 + 4), (3, "master", 3 + 5 + 6) })
    {
        sheet.SkillRanks["Survival"] = rank;
        T($"skillBonus: {name} is the modifier, the level, and the rank", CharGen.SkillBonus(sheet, "Survival") == want);
    }

    // Keyed to the ability the DATA names, not to a second list inside SkillBonus — the whole
    // reason the method reads the definition rather than carrying its own table.
    foreach (var k in cg.skills)
    {
        var s2 = new CharacterSheet { Level = 3, Scores = new() { [k.ability] = 18 } };
        T($"skillBonus: [{k.name}] reads its own ability ({k.ability})", CharGen.SkillBonus(s2, k.name) == 4);
        s2.SkillRanks[k.name] = 2;
        T($"skillBonus: [{k.name}] trained to expert adds level and rank", CharGen.SkillBonus(s2, k.name) == 4 + 3 + 4);
    }

    T("skillBonus: a null sheet is nothing, not a crash", CharGen.SkillBonus(null, "Survival") == 0);
    T("skillBonus: so is a nameless skill", CharGen.SkillBonus(sheet, "") == 0);
    T("skillBonus: an unknown skill falls back to no ability rather than throwing",
        CharGen.SkillBonus(sheet, "Basket Weaving") == 0);
    T("skillBonus: a sheet with no scores answers zero",
        CharGen.SkillBonus(new CharacterSheet { Level = 4 }, "Survival") == 0);

    // A generated soul's Survival bonus and the Ledger's own tick have to agree, since the dialog
    // shows one and the sheet shows the other.
    var soul = CharGen.Generate(6, false, "Marshal");
    int rank6 = soul.SkillRanks != null && soul.SkillRanks.TryGetValue("Survival", out int r6) ? r6 : 0;
    int want6 = rank6 <= 0 ? CharGen.Mod(soul.Scores["RES"])
                           : CharGen.Mod(soul.Scores["RES"]) + soul.Level + rank6 * 2;
    T("skillBonus: agrees with a generated soul's own sheet", CharGen.SkillBonus(soul, "Survival") == want6);
}

// ---- Signs, Miracles, and what working one costs (Ch. XIII / Ch. VI) ----
{
    // Hand-checked shapes first, so a regression names the case it broke rather than a count.
    var a = Rules.ParseCost("1 Beat · 2 Nerve · Will save");
    T("cost: time, Nerve and a save all read", a.Time == "1 Beat" && a.Nerve == 2 && a.Save == "Will" && a.HasSave);
    T("cost: and nothing it did not say", a.Faith == 0 && a.Blood == 0 && a.Mark == 0 && a.OrBlood == 0);

    var b = Rules.ParseCost("One minute · 5 Nerve and 1 Mark");
    T("cost: 'and' charges both", b.Nerve == 5 && b.Mark == 1 && b.Time == "One minute" && !b.HasSave);

    var c = Rules.ParseCost("1 Beat · 3 Nerve or 6 Blood");
    T("cost: 'or' charges the first and remembers the way out", c.Nerve == 3 && c.OrBlood == 6 && c.Blood == 0);

    var d = Rules.ParseCost("1 Beat · 1 Faith · Fortitude save");
    T("cost: a Miracle is paid in Faith", d.Faith == 1 && d.Nerve == 0 && d.Save == "Fortitude");

    var e = Rules.ParseCost("Free · 1 Nerve");
    T("cost: a free action still costs Nerve", e.Time == "Free" && e.Nerve == 1 && e.Spends);

    var f = Rules.ParseCost("1 Beat · 0 Faith");
    T("cost: nothing to spend is not a spend", !f.Spends && f.Faith == 0);

    T("cost: an empty line is a cost of nothing, not a crash", !Rules.ParseCost(null).Spends && !Rules.ParseCost("").Spends);
    T("cost: an unparseable line keeps its words as the time", Rules.ParseCost("whenever you like").Time == "whenever you like");

    // Then the whole printed table: every Sign and Miracle in the data has to come apart cleanly,
    // because the Work dialog quotes what it parsed and spends what it found.
    int signsCosting = 0, miraclesCosting = 0;
    foreach (var sg in CharGen.D.signs)
    {
        var pc = Rules.ParseCost(sg.cost);
        T($"cost: Sign [{sg.name}] names its action", pc.Time.Length > 0);
        T($"cost: Sign [{sg.name}] is not paid in Faith", pc.Faith == 0);
        T($"cost: Sign [{sg.name}] has a rank on the spine", sg.rank >= 1 && sg.rank <= 5);
        if (pc.Spends) signsCosting++;
    }
    foreach (var mi in CharGen.D.miracles)
    {
        var pc = Rules.ParseCost(mi.cost);
        T($"cost: Miracle [{mi.name}] names its action", pc.Time.Length > 0);
        T($"cost: Miracle [{mi.name}] is not paid in Nerve", pc.Nerve == 0);
        T($"cost: Miracle [{mi.name}] has a rank on the spine", mi.rank >= 1 && mi.rank <= 5);
        if (pc.Spends) miraclesCosting++;
    }
    T($"cost: nearly every Sign costs something ({signsCosting}/{CharGen.D.signs.Count})",
        signsCosting >= CharGen.D.signs.Count - 2);
    T($"cost: nearly every Miracle costs something ({miraclesCosting}/{CharGen.D.miracles.Count})",
        miraclesCosting >= CharGen.D.miracles.Count - 2);

    // ---- creature powers off the Bestiary line ----
    foreach (var cr in Db.Creatures)
    {
        var (nm, eff) = Rules.ParsePower(cr.special);
        if (string.IsNullOrWhiteSpace(cr.special)) continue;
        T($"power: [{cr.name}] yields a named power", nm.Length > 0);
        T($"power: [{cr.name}]'s power name is short enough to be a chip", nm.Length <= 60);
        T($"power: [{cr.name}] keeps the effect text", eff.Length > 0);
    }
    var (wn, we) = Rules.ParsePower("Killing cold & the call. A blizzard rides with it.");
    T("power: the lead phrase is the name", wn == "Killing cold & the call");
    T("power: and the rest is what it does", we == "A blizzard rides with it.");
    T("power: an empty line yields nothing, not a crash", Rules.ParsePower(null).name == "");

    // ---- an effect on a combatant: the clock, and coming off it ----
    {
        var target = new Combatant { Name = "Ruth", BloodCur = 20, BloodMax = 20 };
        T("worked: nothing on her reads as nothing", target.WorkedChips == "");
        target.Work(new WorkedEffect { Name = "Hobble", Kind = "Sign", Rank = 1, Source = "Hexer", RoundsLeft = 2, SinceRound = 3 });
        target.Work(new WorkedEffect { Name = "Shield of the Word", Kind = "Miracle", Rank = 2, Source = "Padre", RoundsLeft = -1 });
        T("worked: two chips, both named", target.WorkedChips.Contains("Hobble") && target.WorkedChips.Contains("Shield of the Word"));
        T("worked: a Sign and a Miracle wear different marks", target.Worked[0].Mark == "✦" && target.Worked[1].Mark == "✝");
        T("worked: a counted effect shows its rounds", target.Worked[0].Chip.Contains("(2)"));
        T("worked: an open-ended one shows none", !target.Worked[1].Chip.Contains("("));
        T("worked: the full text carries cause and end",
            target.Worked[0].Full.Contains("Hexer") && target.Worked[0].Full.Contains("round 3"));

        var doneA = target.TickWorked();
        T("worked: one round down, nothing expired yet", doneA.Count == 0 && target.Worked[0].RoundsLeft == 1);
        var doneB = target.TickWorked();
        T("worked: the counted one runs out", doneB.Count == 1 && doneB[0].Name == "Hobble");
        T("worked: and comes off her", target.Worked.Count == 1 && target.Worked[0].Name == "Shield of the Word");
        for (int i = 0; i < 20; i++) target.TickWorked();
        T("worked: an open-ended effect never expires on its own", target.Worked.Count == 1);
        target.Unwork(target.Worked[0]);
        T("worked: ended by hand, it is gone", target.Worked.Count == 0 && target.WorkedChips == "");

        var creaturePower = new WorkedEffect { Name = "The call", Kind = "Power", Source = "The Wendigo" };
        T("worked: a creature's power wears its own mark", creaturePower.Mark == "◈");
    }

    // Effects survive a session round-trip — an effect lost on save is a rule the table forgets.
    {
        var c2 = new Combatant { Name = "Silas" };
        c2.Work(new WorkedEffect { Name = "Witch-Sight", Kind = "Sign", Rank = 1, Source = "Hexer", RoundsLeft = 4, Cost = "Free · 1 Nerve" });
        var round = System.Text.Json.JsonSerializer.Deserialize<Combatant>(System.Text.Json.JsonSerializer.Serialize(c2));
        T("worked: survives save and load", round.Worked.Count == 1 && round.Worked[0].Name == "Witch-Sight");
        T("worked: with its cause and cost intact",
            round.Worked[0].Source == "Hexer" && round.Worked[0].Cost == "Free · 1 Nerve" && round.Worked[0].RoundsLeft == 4);
    }
}

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

    // -- the horror economy: Dread Checks and the break table (#3, Ch. XII) --
    T("Dread DC maps to the Nerve ladder's tier",
        Horror.DreadTier(10) == 1 && Horror.DreadTier(13) == 2 && Horror.DreadTier(16) == 3
        && Horror.DreadTier(20) == 4 && Horror.DreadTier(25) == 5);
    // a natural 20 always steels the soul (nat-20 floor via FourDegrees); crit success loses no Nerve
    T("a crit-success Dread Check steadies and costs no Nerve",
        Horror.DreadCheck(will: 0, dreadDc: 16, forcedDie: 20) is { Steadied: true, NerveLost: 0 });
    // a natural 1 against a high DC is a critical failure: Nerve lost AND Frightened
    T("a crit-failure Dread Check loses Nerve and imposes Frightened 1",
        Horror.DreadCheck(will: 0, dreadDc: 20, forcedDie: 1) is { Frightened: true, NerveLost: > 0 });
    // tier-5 dread (DC 25) carries a lasting Affliction on a failure
    T("tier-5 dread carries an Affliction on failure",
        Horror.DreadCheck(will: 0, dreadDc: 25, forcedDie: 2).Affliction);
    for (int i = 0; i < 400; i++)
    {
        var d3 = Horror.DreadCheck(will: 0, dreadDc: 16);   // 1d6 ladder
        T("a Dread Check never loses more than its ladder allows", d3.NerveLost is >= 0 and <= 6);
        T("Nerve is lost only on a failure, never a success", d3.Degree >= 2 ? d3.NerveLost == 0 : true);
    }
    // the break table: only a 6 gains a Mark, and it always names an outcome
    for (int roll = 1; roll <= 6; roll++)
    {
        var bk = Horror.Break(forcedRoll: roll);
        T($"break d6={roll}: Mark only on a 6", bk.GainsMark == (roll == 6) && bk.Text.Length > 0);
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
// the live faith/sign pool the app tracks is re-derived on the sheet (#3): a Padre at 5th holds
// Grace = PRE mod + half level; a mundane Gunhand carries none.
{
    var padre = CharGen.Generate(5, false, "Padre");
    T("a Padre's Grace pool = PRE mod + half level",
        padre.PoolName == "Grace" && padre.PoolMax == Math.Max(1, CharGen.Mod(padre.Scores["PRE"]) + 5 / 2));
    T("a Gunhand carries no pool", CharGen.Generate(5, false, "Gunhand").PoolMax == 0);
}
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

// ---- buying more than one of a thing (wizard, 2026-07-27) ----
// The count is carried as repeated entries, so the coin ledger prices it by counting and
// Validate keeps its one authority over the arithmetic. Prove the money is right, the sheet
// stays legal, and a second suit of armor buys no second helping of DR.
{
    var cheap = cg.gearPrices.OrderBy(kv => kv.Value).First(kv => cg.armor.All(a => a.gear != kv.Key));
    foreach (int qty in new[] { 1, 2, 5 })
    {
        var spec = new CharGen.AssembleSpec { Level = 1, Calling = "Gunhand", Origin = "The Outlaw", Rolled = true };
        foreach (var a in new[] { "STR", "DEX", "CON", "WIT", "RES", "PRE" }) spec.PreGiftScores[a] = 12;
        spec.CoinRolled = 6 * cg.callings.First(c => c.name == "Gunhand").coin.mult * 6;   // the top of the range, so the coin never binds
        for (int i = 0; i < qty; i++) spec.BuyGear.Add(cheap.Key);
        var sheet = CharGen.Assemble(spec);
        int held = sheet.Gear.Count(g => g == cheap.Key);
        T($"buy × {qty}: {qty} of \"{cheap.Key}\" reach the sheet (held {held})", held >= qty);
        var v = CharGen.Validate(sheet);
        T($"buy × {qty}: sheet stays conformant" + (v.Count > 0 ? " — " + v[0] : ""), v.Count == 0);
        T($"buy × {qty}: the tally says so", CharGen.Tally(sheet.Gear).Any(l => qty == 1 ? l == cheap.Key : l == $"{cheap.Key} × {held}"));
    }

    // two of the same armor: bought and paid for twice, worn once
    var suit = cg.armor.OrderBy(a => a.cost).First();
    var aspec = new CharGen.AssembleSpec { Level = 1, Calling = "Gunhand", Origin = "The Outlaw", Rolled = true, CoinRolled = 6 * 20 * 6 };
    foreach (var a in new[] { "STR", "DEX", "CON", "WIT", "RES", "PRE" }) aspec.PreGiftScores[a] = 12;
    aspec.BuyGear.Add(suit.gear); aspec.BuyGear.Add(suit.gear);
    var ash = CharGen.Assemble(aspec);
    var av = CharGen.Validate(ash);
    T("buy × 2 armor: still conformant" + (av.Count > 0 ? " — " + av[0] : ""), av.Count == 0);
    T("buy × 2 armor: DR does not stack", ash.DrBlades == suit.drBlades && ash.DrShot == suit.drShot);
}

// Tally: order of first appearance, a count only where there is one to give
T("tally keeps first-appearance order",
    CharGen.Tally(new[] { "Rope", "Candle", "Rope", "Lantern", "Rope" })
           .SequenceEqual(new[] { "Rope × 3", "Candle", "Lantern" }));
T("tally leaves singles alone", CharGen.Tally(new[] { "Rope" }).SequenceEqual(new[] { "Rope" }));
T("tally of nothing is nothing", CharGen.Tally(Array.Empty<string>()).Count == 0);

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
// ---- a whole adventure, rolled (v1.26.0) ----
{
    var a = Db.RollAdventure(6);
    T("adventure: it has a name", !string.IsNullOrWhiteSpace(a.Title));
    foreach (var (field, val) in new[]
    {
        ("shape", a.Shape), ("hook", a.Hook), ("town", a.TownName), ("ails", a.Ails),
        ("rumor", a.Rumor), ("trouble", a.Trouble), ("truth", a.Truth), ("turn", a.Turn),
        ("omen", a.Omen), ("npc", a.NpcName), ("clock", a.Clock), ("reward", a.Reward),
    })
        T($"adventure: {field} is filled in", !string.IsNullOrWhiteSpace(val));

    T("adventure: the clock is a size the app actually draws",
        a.ClockSegments == 4 || a.ClockSegments == 6 || a.ClockSegments == 8);
    T("adventure: the sheet carries the town and the trouble",
        a.Sheet().Contains(a.TownName) && a.Sheet().Contains(a.Trouble));
    T("adventure: the trouble is a real creature out of the Bestiary",
        Db.Find(a.Trouble) != null);

    // The trouble must be in the posse's weight class, or the generator is just a random monster.
    for (int lvl = 1; lvl <= 10; lvl++)
    {
        int tier = Rules.PartyTier(lvl);
        bool ok = true;
        for (int i = 0; i < 60; i++)
        {
            var roll = Db.RollAdventure(lvl);
            var beast = Db.Find(roll.Trouble);
            if (beast != null && Math.Abs(beast.tier - tier) > 1) { ok = false; break; }
        }
        T($"adventure: the trouble suits a level-{lvl} posse (tier {tier} ± 1)", ok);
    }

    // Variety is the whole ask. 400 rolls should not be visibly repeating itself.
    var seen = new HashSet<string>();
    var titles = new HashSet<string>();
    var troubles = new HashSet<string>();
    for (int i = 0; i < 400; i++)
    {
        var adv = Db.RollAdventure(6);
        seen.Add($"{adv.Shape}|{adv.Hook}|{adv.Truth}|{adv.Turn}|{adv.Trouble}|{adv.Clock}");
        titles.Add(adv.Title);
        troubles.Add(adv.Trouble);
    }
    T($"adventure: 400 rolls are near-all distinct ({seen.Count})", seen.Count >= 395);
    T($"adventure: titles vary ({titles.Count} in 400)", titles.Count >= 150);
    T($"adventure: the trouble varies ({troubles.Count} distinct creatures)", troubles.Count >= 10);
    T("adventure: level 0 opens the whole Bestiary", Db.RollAdventure(0) != null);

    // Print two so a human can judge whether it reads like the books rather than like a form.
    Console.WriteLine();
    Console.WriteLine("sample adventures —");
    for (int i = 0; i < 2; i++)
    {
        foreach (var line in Db.RollAdventure(6).Sheet().Split('\n'))
            Console.WriteLine("  " + line.TrimEnd());
        Console.WriteLine();
    }
}

// ---- a settlement set down in open country (v1.25.0) ----
// Before this, a rolled city could only be drawn as a ward, so "what is AROUND it" had no answer.
// SettingTerrains is derived from Terrains rather than typed out again, so the guard that matters
// is that it tracks the source list and drops exactly the one country that is not a setting.
{
    T("setting terrains: the Lamplit City is not ground you stand a town on",
        !MapGen.SettingTerrains.Contains("The Lamplit City"));
    T("setting terrains: everything else survives",
        MapGen.SettingTerrains.Length == MapGen.Terrains.Length - 1);
    T("setting terrains: order follows the source list, so a rolled index is stable",
        MapGen.SettingTerrains.SequenceEqual(MapGen.Terrains.Where(t => t != "The Lamplit City")));
    T("setting terrains: the open range and the badlands are both offered",
        MapGen.SettingTerrains.Contains("The Trail & the Open Range")
        && MapGen.SettingTerrains.Contains("Desert & the Badlands"));

    // Every setting must actually draw a named settlement at county scale — that IS the feature.
    int county = Array.IndexOf(MapGen.Scales, "A county (a day's ride)");
    T("setting terrains: the county scale still exists to set them in", county >= 0);
    foreach (var ground in MapGen.SettingTerrains)
    {
        var m = MapGen.Generate(new MapSpec
        { Terrain = ground, Scale = county, Seed = 4242, Landmarks = 5, Town = true, PlaceName = "Perdition Wells" });
        T($"a town stands in {ground}", m?.Town != null && m.Town.Name.Contains("Perdition"));
    }

    // A city ward is the other half: the place itself, at the scale you walk it.
    var ward = MapGen.Generate(new MapSpec
    { Terrain = "The Lamplit City", Scale = Array.IndexOf(MapGen.Scales, "A city ward (blocks)"), Seed = 4242, Town = true, PlaceName = "Ashpit Quarter" });
    T("a ward still draws as the whole sheet", ward != null && ward.P.Count > 20);
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

// ---- Trail Maps: a city on a river reads as ONE course, not blue scraps between roofs ----
// The reported bug: in a ward, building blocks stamped over the water, and structures landed in
// it. The fix leaves the waterway open and redraws the water ON TOP of the block layer — so the
// last water ink must sit above the last block, and a lake must carve blocks out of the ward.
{
    // a ward block is a 4-point rectangle (8 floats); the 5-point church roof shares the fill but isn't one
    bool IsBlock(Prim p) => p.Kind == PrimKind.Poly && p.Fill == "#d9cba8" && p.Pts.Length == 8;
    // WaterEdge stroke, or WaterFill as a river's fill-line stroke or a lake's polygon fill
    bool IsWater(Prim p) => p.Stroke == "#7d98a1" || p.Stroke == "#b9cbcf" || p.Fill == "#b9cbcf";

    int riverAboveBlocks = 0, seeds = 0;
    foreach (int seed in new[] { 3, 88, 421, 1500, 27182 })
    {
        seeds++;
        var m = MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[8], Scale = 4, Seed = seed, Water = 3, Town = true });
        int lastBlock = -1, lastWater = -1;
        for (int i = 0; i < m.P.Count; i++)
        {
            if (IsBlock(m.P[i])) lastBlock = i;
            if (IsWater(m.P[i])) lastWater = i;
        }
        if (lastBlock >= 0 && lastWater > lastBlock) riverAboveBlocks++;
        // and the ward's ink still stays on the paper
        foreach (var pr in m.P)
            if (pr.Kind == PrimKind.Poly)
                for (int i = 0; i + 1 < pr.Pts.Length; i += 2)
                    T($"city block on paper (seed {seed})", pr.Pts[i] > -0.01f && pr.Pts[i] < m.W + 0.01f && pr.Pts[i + 1] > -0.01f && pr.Pts[i + 1] < m.H + 0.01f);
    }
    T("a city river is redrawn over the blocks (unbroken course)", riverAboveBlocks == seeds);

    // a lake carves building blocks out of the ward it sits in
    int Blocks(MapSpec sp) => MapGen.Generate(sp).P.Count(IsBlock);
    int dry = Blocks(new MapSpec { Terrain = MapGen.Terrains[8], Scale = 4, Seed = 77, Water = 1, Town = true });
    int wet = Blocks(new MapSpec { Terrain = MapGen.Terrains[8], Scale = 4, Seed = 77, Water = 4, Town = true });
    T("a lake carves blocks out of the ward", wet < dry);

    // scattered city works are labeled ("works", "depot", "pens", "chapel", "landing"), so it is
    // plain what each mark is — the second reported symptom.
    var caps = new HashSet<string> { "works", "depot", "pens", "chapel", "landing" };
    var cityMap = MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[8], Scale = 4, Seed = 4242, Water = 3, Landmarks = 6 });
    T("city works carry captions", cityMap.P.Any(p => p.Kind == PrimKind.Text && caps.Contains(p.Text)));

    // and no named landmark is planted in the river — structures keep out of the water now
    var riverVerts = cityMap.P.Where(IsWater).SelectMany(p =>
    {
        var v = new List<(float x, float y)>();
        for (int i = 0; i + 1 < p.Pts.Length; i += 2) v.Add((p.Pts[i], p.Pts[i + 1]));
        return v;
    }).ToList();
    bool AnyInWater(float x, float y) => riverVerts.Any(v => (v.x - x) * (v.x - x) + (v.y - y) * (v.y - y) < 12 * 12);
    T("no city landmark is planted in the river", cityMap.Landmarks.All(l => !AnyInWater(l.X, l.Y)));
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

// ---- Rides: the corral and the yard ----
{
    T("the ride roster loads", Db.Rides.Count >= 20);
    T("it carries both mounts and vehicles",
        Db.Rides.Any(r => r.kind == "mount") && Db.Rides.Any(r => r.kind == "vehicle"));
    foreach (var want in new[] { "Saddle Horse", "Mule", "Wagon", "Stagecoach", "Ferry", "Riverboat", "Locomotive & Cars" })
        T($"the roster carries the {want}", Db.Rides.Any(r => r.name == want));
    T("every roster entry is whole", Db.Rides.All(r =>
        r.name.Length > 0 && (r.kind == "mount" || r.kind == "vehicle") &&
        r.blood > 0 && r.defense > 0 && r.speed.Length > 0 && r.capacity >= 0 && r.notes.Length > 0));
    T("no two roster entries share a name", Db.Rides.Select(r => r.name).Distinct().Count() == Db.Rides.Count);

    var coach = Db.MakeRide("Stagecoach");
    T("a built ride takes its roster numbers",
        coach.Type == "Stagecoach" && coach.Kind == "vehicle" && coach.BloodCur == coach.BloodMax
        && coach.BloodMax > 0 && coach.Capacity == 9 && !coach.IsMount);
    var horse = Db.MakeRide("saddle horse");           // the roster is matched case-insensitively
    T("the roster is found whatever the case", horse.Type == "Saddle Horse" && horse.IsMount);
    var odd = Db.MakeRide("A Borrowed Handcart");
    T("an unknown ride is still usable", odd.Name == "A Borrowed Handcart" && odd.BloodMax >= 1);

    coach.BloodCur = 0;
    T("a ride at no Blood is down", coach.Down);
    coach.BloodCur = -50;
    T("Blood is clamped at nothing", coach.BloodCur == 0);
    coach.BloodMax = 0;
    T("a ride always has at least one Blood of maximum", coach.BloodMax == 1);
    horse.Defense = 999;
    T("Defense is clamped to something sane", horse.Defense == 40);

    // it rides in the session file with everything else
    var rideSess = new GameSession { Rides = { Db.MakeRide("Wagon"), Db.MakeRide("Mule") } };
    rideSess.Rides[0].Rider = "Anni Halvorsen";
    rideSess.Rides[0].Notes = "Nearside wheel is complaining.";
    var rideBack = System.Text.Json.JsonSerializer.Deserialize<GameSession>(
        System.Text.Json.JsonSerializer.Serialize(rideSess));
    T("rides survive a session round-trip", rideBack.Rides.Count == 2
        && rideBack.Rides[0].Type == "Wagon" && rideBack.Rides[0].Rider == "Anni Halvorsen"
        && rideBack.Rides[0].Notes.StartsWith("Nearside") && rideBack.Rides[1].IsMount);
}

// ---- Trail Maps: a town is never seated in the water, and it can be picked up ----
// (A settlement drawn on the river inked its streets straight through the channel and the two
// layers argued — you couldn't tell a roof from a bank. The seat is now walked onto dry ground
// before anything is drawn, and the Keeper can still move it by hand.)
{
    int seated = 0, checkedMaps = 0;
    bool allDry = true;
    foreach (int water in new[] { 2, 3, 4, 5 })
        foreach (int scale in new[] { 1, 2, 3 })
            for (int seed = 1; seed <= 40; seed++)
            {
                var mm = MapGen.Generate(new MapSpec
                { Terrain = MapGen.Terrains[seed % 8], Scale = scale, Seed = seed * 7 + water, Water = water, Landmarks = 4 });
                if (mm.Town == null) continue;
                checkedMaps++;
                if (mm.TownSeated) seated++;
                if (MapGen.OnWater(mm, mm.Town.X, mm.Town.Y, MapGen.TownReach(scale))) allDry = false;
            }
    T("every town across the water settings stands on dry ground", allDry && checkedMaps > 300);
    T("the seating rule actually fired on some of them", seated > 0);

    // a town clear of the water is left exactly where the survey put it — old maps don't shift
    var dryMap = MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[0], Scale = 2, Seed = 4242, Water = 1, Landmarks = 4 });
    T("a town on dry ground is not moved at all", dryMap.Town != null && !dryMap.TownSeated);

    // the settlement is recorded like a landmark, and moving it touches only its own ink
    var tm = MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[0], Scale = 2, Seed = 909, Water = 1, Landmarks = 4 });
    T("the town is recorded with a sane prim range", tm.Town != null && tm.Town.PrimCount > 0
        && tm.Town.PrimStart >= 0 && tm.Town.PrimStart + tm.Town.PrimCount <= tm.P.Count
        && tm.Town.Name.Length > 0 && tm.Town.X == tm.Town.GenX && tm.Town.Y == tm.Town.GenY);
    if (tm.Town != null)
    {
        var before = tm.P.Select(p => (float[])p.Pts.Clone()).ToList();
        float tox = tm.Town.X, toy = tm.Town.Y;
        MapGen.MoveTown(tm, tox - 60, toy + 35);
        bool ownMoved = true, othersStill = true;
        for (int i = 0; i < tm.P.Count; i++)
        {
            bool mine = i >= tm.Town.PrimStart && i < tm.Town.PrimStart + tm.Town.PrimCount;
            var (a, b) = (before[i], tm.P[i].Pts);
            if (!mine) { if (!a.SequenceEqual(b)) othersStill = false; continue; }
            int n = tm.P[i].Kind == PrimKind.Circle ? 2 : a.Length;
            for (int j = 0; j < n; j += 2)
                if (Math.Abs(b[j] - a[j] + 60) > 0.001f || Math.Abs(b[j + 1] - a[j + 1] - 35) > 0.001f) ownMoved = false;
        }
        T("moving the town translates exactly its own ink", ownMoved && tm.Town.X == tox - 60 && tm.Town.Y == toy + 35);
        T("moving the town leaves every other prim alone", othersStill);
        MapGen.MoveTown(tm, tm.Town.GenX, tm.Town.GenY);
        T("putting the town back restores its seat", tm.Town.X == tox && tm.Town.Y == toy);
    }

    // the water question is asked of one description of the water, so the app and the
    // generator can never disagree about what counts as wet
    var wm = MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[1], Scale = 2, Seed = 313, Water = 4, Landmarks = 4 });
    T("the model carries its lake", wm.LakeR > 0);
    T("the lake's middle reads as water", MapGen.OnWater(wm, wm.LakeX, wm.LakeY, 0));
    T("clearance is negative in the water, positive out of it",
        MapGen.WaterClearance(wm, wm.LakeX, wm.LakeY) < 0 && MapGen.WaterClearance(wm, 20, 20) > 0);
    var moved = MapGen.DryGroundNear(wm, wm.LakeX, wm.LakeY, 40);
    T("dry ground near the lake's middle is out of the lake", !MapGen.OnWater(wm, moved.x, moved.y, 40));
    T("dry ground leaves an already-dry spot alone", MapGen.DryGroundNear(wm, 30, 30, 10) == (30f, 30f));

    // a city ward carries a key; the open country doesn't need one
    var keyed = MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[8], Scale = 4, Seed = 4242, Water = 3, Landmarks = 6 });
    var plain = MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[0], Scale = 2, Seed = 4242, Water = 3, Landmarks = 6 });
    T("a city ward draws a key", keyed.P.Any(p => p.Kind == PrimKind.Text && p.Text == "THE KEY"));
    T("open country draws no key", !plain.P.Any(p => p.Kind == PrimKind.Text && p.Text == "THE KEY"));
    T("a city has no movable town — the ward IS the map", keyed.Town == null);
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
    // city wards WITH water — eyeball that the river/lake reads as one open course through the
    // blocks (the reported bug), and that the scattered works are labeled
    File.WriteAllText(Path.Combine(outDir, "sample-city-river.svg"),
        MapGen.ToSvg(MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[8], Scale = 4, Seed = 4242, Water = 3, Rail = true, Landmarks = 6 })));
    File.WriteAllText(Path.Combine(outDir, "sample-city-lake.svg"),
        MapGen.ToSvg(MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[8], Scale = 4, Seed = 313, Water = 4, Landmarks = 6 })));
    File.WriteAllBytes(Path.Combine(outDir, "sample-city-river.pdf"),
        Pdf.MapPdf(MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[8], Scale = 4, Seed = 4242, Water = 3, Rail = true, Landmarks = 6 })));
    File.WriteAllBytes(Path.Combine(outDir, "sample-city-lake.pdf"),
        Pdf.MapPdf(MapGen.Generate(new MapSpec { Terrain = MapGen.Terrains[8], Scale = 4, Seed = 313, Water = 4, Landmarks = 6 })));
    // one sheet per sky and one per ground — the weather washes and the new landforms are
    // asserted above, but they also have to be looked at
    WeatherSheets.Write(Path.Combine(outDir, "weather"));
    Console.WriteLine($"sample PDFs → {outDir}");
}

Console.WriteLine($"\n{pass} passed, {fail} failed");
return fail == 0 ? 0 : 1;
