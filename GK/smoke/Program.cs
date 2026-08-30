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
T("175 creatures", Db.Creatures.Count == 175);
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
        // (An undescribed soul — no look passed — keeps those old odds; see FullName.)
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

    // ---- the residue test and the reset are one pair (v1.36.0) ----
    // Reported by a Keeper as "the New fight button never works". It didn't: the button asked
    // whether there were foes, sign on the trail, or worked effects, and then ran a reset that
    // clears six more things than that. Take the last foe off by hand and the button answered
    // "nothing to clear" over a posse still Frightened, out of Beats and mid-turn. So the guard
    // is now the reset's own inventory, and every field the reset touches is proved to be one
    // the residue test SEES — add a seventh field to ResetForNewFight without adding it here and
    // one of these fails.
    T("residue: a soul who never fought carries nothing", !Rules.FightResidue(C("Clean", 10)));
    T("residue: a null combatant carries nothing", !Rules.FightResidue(null));
    T("residue: an empty field carries nothing", !Rules.AnyFightResidue(new List<Combatant>()));
    T("residue: a null field carries nothing", !Rules.AnyFightResidue(null));
    foreach (var (what, mark) in new (string, Action<Combatant>)[]
    {
        ("a condition",        c => c.Conditions = "Frightened 1"),
        ("spent Beats",        c => c.Beats = 1),
        ("a MAP step",         c => c.MapStep = 2),
        ("a turn in progress", c => c.Acting = true),
        ("a turn already taken", c => c.HasActed = true),
        ("what just happened", c => c.Wound(-3)),
        ("something working",  c => c.Work(new WorkedEffect { Name = "Wither", Kind = "Sign", Source = "Opal", RoundsLeft = 2 })),
    })
    {
        var one = C("Ruth", 12);
        mark(one);
        T($"residue: {what} counts as the last fight still on them", Rules.FightResidue(one));
        T($"residue: {what} makes the whole field answer yes", Rules.AnyFightResidue(new List<Combatant> { C("Clean", 9), one }));
        Rules.ResetForNewFight(new List<Combatant> { one });
        T($"residue: and the reset actually clears {what}", !Rules.FightResidue(one));
    }

    // Ties break souls-first, then by name, so the same field always yields the same order rather
    // than a wobble.
    var tied = new List<Combatant> { C("Silas", 11), C("Anni", 11), C("Ruth", 11) };
    T("turn: an initiative tie breaks by name", Rules.NextUp(tied).Name == "Anni");
    tied.First(x => x.Name == "Anni").BeginTurn();
    T("turn: and keeps breaking the same way", Rules.NextUp(tied).Name == "Ruth");

    // ---- the order the field acts in IS the order the tracker shows (v1.35.0) ----
    // The fault this pins: the grid sorted Init desc -> souls first -> name while NextUp went
    // Init desc -> name, so the two agreed until somebody tied. A Keeper reported the turn
    // skipping down the field, and on a d20 with eight on the field a tie is closer to certain
    // than not. One ordering now, in Rules.InTurnOrder, read by both.
    var tieMixed = new List<Combatant>
    {
        new() { Name = "Bandit", Init = 15, BloodCur = 10, BloodMax = 10 },
        new() { Name = "Anni",   Init = 15, BloodCur = 10, BloodMax = 10, IsPC = true },
    };
    T("order: on a tie the soul goes before the foe", Rules.NextUp(tieMixed).Name == "Anni");
    T("order: and the grid would show that same first",
        Rules.InTurnOrder(tieMixed).First().Name == "Anni");
    var tieNamed = new List<Combatant>
    {
        new() { Name = "bandit b", Init = 12, BloodCur = 10, BloodMax = 10 },
        new() { Name = "Bandit A", Init = 12, BloodCur = 10, BloodMax = 10 },
    };
    T("order: two of a kind on a tie break by name, ignoring case",
        Rules.InTurnOrder(tieNamed).First().Name == "Bandit A");
    T("order: a null field orders to nothing rather than throwing",
        !Rules.InTurnOrder(null).Any());

    // ---- three full fights, played through (v1.35.0) ----
    // The combat loop was UI code and no test could reach it, which is how the two orderings
    // disagreed for as long as they did. Rules.NewRound is the rollover the Tracker now calls, so
    // a whole fight can be played here: every round, the turns must come out in exactly the order
    // the grid would be showing, everybody able to act must act once, and nobody twice.
    // Is every turn taken in the order the grid showed? Not "the same list" — somebody cut down
    // mid-round never gets their turn, which is the rule working. What must hold is that nobody
    // jumps the queue: the turns that DID happen came in the displayed order.
    bool InShownOrder(List<string> taken, List<string> shown)
    {
        int i = 0;
        foreach (var name in shown) if (i < taken.Count && taken[i] == name) i++;
        return i == taken.Count;
    }

    var fightRng = new Random(20260808);
    for (int fight = 1; fight <= 3; fight++)
    {
        var posse = new List<Combatant>();
        for (int i = 0; i < 4; i++)
            posse.Add(new Combatant { Name = $"Soul {(char)('A' + i)}", IsPC = true,
                                      BloodCur = 30, BloodMax = 30, Init = fightRng.Next(1, 21) });
        for (int i = 0; i < 4; i++)
            posse.Add(new Combatant { Name = $"Horror {(char)('A' + i)}",
                                      BloodCur = 20, BloodMax = 20, Init = fightRng.Next(1, 21) });
        // A tie every fight, deliberately: the bug only ever showed itself on one.
        posse[0].Init = posse[5].Init;

        int round = 0, guard = 0;
        while (posse.Any(c => c.IsPC && !c.Down) && posse.Any(c => !c.IsPC && !c.Down) && guard++ < 100)
        {
            round++;
            Rules.NewRound(posse);
            // Who the grid shows as still to go, at the top of the round.
            var expected = Rules.InTurnOrder(posse.Where(Rules.CanAct)).Select(c => c.Name).ToList();
            var went = new List<string>();
            while (Rules.NextUp(posse) is Combatant up)
            {
                went.Add(up.Name);
                foreach (var other in posse) other.Acting = false;
                up.BeginTurn();
                // The turn does something: a soul cuts a horror, a horror cuts back.
                var target = posse.FirstOrDefault(c => c.IsPC != up.IsPC && !c.Down);
                if (target != null) target.BloodCur = Math.Max(0, target.BloodCur - fightRng.Next(3, 9));
            }
            T($"fight {fight} round {round}: the turns came in the order the field showed",
                InShownOrder(went, expected));
            T($"fight {fight} round {round}: nobody took two turns",
                went.Distinct().Count() == went.Count);
            T($"fight {fight} round {round}: everyone left standing got their turn",
                posse.Where(c => !c.Down).All(c => went.Contains(c.Name)));
            T($"fight {fight} round {round}: the round is spent when the last one has gone",
                !posse.Any(Rules.CanAct));
        }
        T($"fight {fight}: it ended in somebody winning rather than running forever", guard < 100);
        T($"fight {fight}: it took more than one round", round > 1);

        // A late arrival takes its seat by initiative, not the bottom of the list — the second half
        // of the same fault: ArrivalInit rolls a real number and the grid used to append anyway.
        var latecomer = new Combatant { Name = "The Thing at the Door", BloodCur = 25, BloodMax = 25,
                                        Init = posse.Max(c => c.Init) + 1 };
        posse.Add(latecomer);
        T($"fight {fight}: an arrival on a high roll is placed at the top of the order",
            Rules.InTurnOrder(posse).First().Name == "The Thing at the Door");
    }

    // ---- every working says how long it lasts (v1.39.0) ----
    // Twenty-one of the eighty printed no duration at all, and the reader could not tell a book that
    // had DECIDED a thing resolves at once from a book that had simply not said — both came out as
    // "until something ends it", which was true of neither. Ch. VI and Ch. XIII now say which, and
    // this is the half of that agreement the app keeps.
    {
        CharGen.Load();
        var workings = CharGen.D.signs.Select(s => (s.name, kind: "Sign", s.rank, s.cost, s.desc))
            .Concat(CharGen.D.miracles.Select(m => (m.name, kind: "Miracle", m.rank, m.cost, m.desc)))
            .Select(x => Rules.ReadWorking(x.name, x.kind, x.rank, x.cost, x.desc, 5)).ToList();

        T("durations: all 116 workings still read", workings.Count == 116);
        // A duration is "findable" when the printed line names one, or when the thing resolves on
        // the spot. What must not exist any more is a working where neither is true.
        var mute = workings.Where(w =>
        {
            string t = w.Effect.ToLowerInvariant();
            // "night" is in this list because The Hearth Unbroken opens "For one night a place is
            // genuinely safe" — the book's own way of writing until dawn, and the reader has always
            // known it. A checklist that omits a phrasing the code handles reports a fault in the
            // checklist as a fault in the book.
            bool saysWhen = t.Contains("until") || t.Contains("scene") || t.Contains("dawn")
                         || t.Contains("night") || t.Contains("hour") || t.Contains("day")
                         || t.Contains("round") || t.Contains("month") || t.Contains("done")
                         || t.Contains("at once")
                         // B6 brought three more units the book now genuinely uses. A season is
                         // how The Long Winter is written, a week is how The Cup Not Emptied is,
                         // and the Rank 8 workings are simply permanent.
                         || t.Contains("season") || t.Contains("week") || t.Contains("permanent")
                         || t.Contains("for good") || t.Contains("instantly");
            return !saysWhen && w.Damage.Length == 0 && w.Heal.Length == 0 && w.Nerve.Length == 0;
        }).ToList();
        T($"durations: no working is silent about how long it lasts"
    + (mute.Count > 0 ? " — " + string.Join(", ", mute.Select(w => w.Name)) : ""), mute.Count == 0);

        Rules.Working W(string n) => workings.First(w => w.Name == n);
        T("durations: a question put to the dark is over when it is answered",
            W("The Tally").Ends == Rules.WorkEnds.Instant);
        T("durations: a handful of salt is thrown and done",
            W("Salt & Iron").Ends == Rules.WorkEnds.Instant);
        T("durations: a ward on a house holds to dawn and is laid again",
            W("Crossing the Threshold").Ends == Rules.WorkEnds.UntilDawn);
        T("durations: a bargain ends when its terms do, not on a clock",
            W("The Black Contract").Ends == Rules.WorkEnds.UntilEnded);
        T("durations: a familiar's errand lasts as long as you sit still",
            W("Cat's Errand").Ends == Rules.WorkEnds.UntilEnded);
        T("durations: a corked draught keeps a month, which is its own unit",
            W("The Brewing").Ends == Rules.WorkEnds.Month);
        T("durations: and a month reads as a month on the chip",
            new WorkedEffect { Ends = Rules.WorkEnds.Month, RoundsLeft = -1 }.Duration == "a month");

        // The regression this block exists for. Borrowed Breath heals 2d8 and says the worker's own
        // Blood "does not come back until you rest" — a clause about the WORKER, not about how long
        // the healing rides on anybody. A duration reader that anchors on a bare "until you …"
        // turns a heal that resolves on the spot into an effect sitting on the target until somebody
        // ends it by hand, and it does it to a working nobody edited.
        T("durations: a heal is not given a duration by a clause about the healer",
            W("Borrowed Breath").Ends == Rules.WorkEnds.Instant);
        T("durations: and it is still read as healing rather than harm",
            W("Borrowed Breath").Heal.Length > 0 && W("Borrowed Breath").Damage.Length == 0);
    }

    // ---- a new round hands the turn back (v1.39.0) ----
    // The fault this is here to stop: NewRound cleared who had acted and did NOT give the Beats or
    // the MAP step back. BeginTurn was the only thing that did, and it only runs when a row is
    // stepped through ▶ Next turn — so a round stepped by hand, or rolled over with somebody who
    // never got an explicit turn, left that row on Beats 0 and MapStep 4. MapStep 4 is a standing
    // −10 on every Strike it makes for the rest of the fight, and a Keeper reported it as the posse
    // being unable to hit anything. It was true: a level-1 Gunhand at +4 against Defense 13 fell
    // from three hits in five to needing a natural 19, while the dog biting her back at +5 off a
    // clean step hit seven times in ten.
    //
    // Note the three fights above could never have caught this: like GK/playtest, they call
    // BeginTurn() on every turn, which is the ideal path and not the one at the table. This block
    // deliberately does not.
    {
        var spent = new Combatant { Name = "Ruth", IsPC = true, Init = 12, BloodCur = 12, BloodMax = 12 };
        var mark  = new Combatant { Name = "The Mad Dog", Init = 8, BloodCur = 10, BloodMax = 10, Defense = 13 };
        var turnField = new List<Combatant> { spent, mark };
        var gun = new CgWeapon { name = "Single-Action Revolver", dmg = "1d8", traits = "", kind = "gun" };

        spent.BeginTurn();
        for (int i = 0; i < 3; i++) CombatFlow.StrikeAndApply(spent, mark, gun, 4);
        T("round: a full turn of three Strikes spends the Beats and walks the MAP up",
            spent.Beats == 0 && spent.MapStep == 4);
        T("round: and that step really is the −10 the Code's third Strike costs",
            IronCode.MapPenalty(spent.MapStep, false) == -10);

        Rules.NewRound(turnField);
        T("round: a new round gives the Beats back", spent.Beats == 3);
        T("round: a new round makes the first Strike clean again", spent.MapStep == 1);
        T("round: which is to say the next Strike carries no MAP",
            IronCode.MapPenalty(spent.MapStep, false) == 0);
        T("round: the foe is handed its turn back too — this was never the posse's rule alone",
            mark.Beats == 3 && mark.MapStep == 1);

        // ---- Aim, brace and the Kickback weapon (Ch. XI, "Aiming and Bracing") ----
        // Three rules that only read as one: the Beat buys +2 on ONE Strike, the same Beat is what
        // braces a shotgun, and the strong never needed it. Driven at the Keeper's path again —
        // nothing below leans on BeginTurn to tidy up after it.
        {
            var scattergun = new CgWeapon { name = "Double-Barrel Shotgun", dmg = "2d8",
                                            traits = "Scatter 10 ft, Kickback, Fatal d12", kind = "gun" };
            var plain      = new CgWeapon { name = "Single-Action Revolver", dmg = "1d8", traits = "", kind = "gun" };
            // Defense 9 is his own off Appendix D, and it matters: EffectiveDefense is floored at 1,
            // so a test row left on Defense 0 cannot show a −2 at all.
            Combatant Elias(int str) => new() { Name = "Brother Elias Crow", IsPC = true, Str = str,
                                                BloodCur = 9, BloodMax = 9, Defense = 9, Beats = 3, MapStep = 1 };
            Combatant Dog() => new() { Name = "The Mad Dog", BloodCur = 10, BloodMax = 10, Defense = 13 };

            // Forced die 10: against Defense 13 a +2 is exactly the difference between 12 and 14,
            // so the Aim is measured by whether the blow lands rather than by reading a number back.
            var aimed = Elias(9); aimed.Aimed = true;
            var r1 = CombatFlow.StrikeAndApply(aimed, Dog(), plain, 1, null, 10);
            T("aim: the Beat spent to Aim is worth +2 on the Strike", r1.Res.Strike.Hit);
            var hasty = Elias(9);
            var r2 = CombatFlow.StrikeAndApply(hasty, Dog(), plain, 1, null, 10);
            T("aim: and the same shot unaimed falls short", !r2.Res.Strike.Hit);
            T("aim: the Strike spends it, so the next one this turn is unaimed", !aimed.Aimed);

            // The Aim is spent hit or miss — the book buys one Strike with that Beat, not a turn.
            var missed = Elias(9); missed.Aimed = true;
            CombatFlow.StrikeAndApply(missed, Dog(), plain, -20, null, 1);
            T("aim: a missed Strike spends the Aim just the same", !missed.Aimed);

            // Kickback: -2 AND Off-Guard until their next turn, unless braced or STR 12+.
            var hipfire = Elias(9);
            CombatFlow.StrikeAndApply(hipfire, Dog(), scattergun, 4, null, 10);
            T("kickback: firing a Kickback weapon unbraced leaves them recoiling", hipfire.Recoiling);
            T("kickback: which is Off-Guard, and costs the Defense the book's Off-Guard costs",
                hipfire.EffectiveDefense == hipfire.Defense + Rules.OffGuardDefense);

            var braced = Elias(9); braced.Aimed = true;
            CombatFlow.StrikeAndApply(braced, Dog(), scattergun, 4, null, 10);
            T("kickback: the Beat spent to brace lifts it", !braced.Recoiling);

            var strong = Elias(IronCode.BraceStrength);
            CombatFlow.StrikeAndApply(strong, Dog(), scattergun, 4, null, 10);
            T("kickback: and STR 12 is exempt outright, braced or not", !strong.Recoiling);
            T("kickback: one under that is not", IronCode.KickbackBites(
                WeaponTraits.Parse(scattergun.traits), false, IronCode.BraceStrength - 1));

            // A soul cannot be doubly Off-Guard: the recoil adds nothing on top of the condition.
            var already = Elias(9); already.Conditions = "Off-Guard";
            int before = already.EffectiveDefense;
            CombatFlow.StrikeAndApply(already, Dog(), scattergun, 4, null, 10);
            T("kickback: recoil does not stack with an Off-Guard the Keeper already wrote",
                already.Recoiling && already.EffectiveDefense == before);

            // "Until your next turn" is exactly that, and the hand-stepped round clears it too.
            var lingering = Elias(9);
            CombatFlow.StrikeAndApply(lingering, Dog(), scattergun, 4, null, 10);
            Rules.NewRound(new List<Combatant> { lingering });
            T("kickback: a new round hands the turn back and the recoil is over", !lingering.Recoiling);

            // Zero STR means nobody said, not a soul who cannot lift a rifle.
            T("kickback: an unfilled row reckons at the middle of the scale",
                new Combatant().Strength == Rules.AverageScore);
        }

        // ---- Circumstance, Volley, Scatter and reloading (Ch. XI · Ch. X's arms table) ----
        {
            var sar = CharGen.D.weapons.First(w => w.name == "Single-Action Revolver");
            var buff = CharGen.D.weapons.First(w => w.name == "Buffalo Rifle");
            var scat = CharGen.D.weapons.First(w => w.name == "Double-Barrel Shotgun");
            var lever = CharGen.D.weapons.First(w => w.name == "Lever-Action Repeater");
            var capball = CharGen.D.weapons.First(w => w.name == "Cap-and-Ball Revolver");

            // The three columns the transcription had been dropping since the app was written.
            T("arms: the revolver carries its printed range, capacity and reload",
                sar.range == 50 && sar.cap == 6 && sar.reload == "1/shot");
            T("arms: and the cap-and-ball's slow reload is a COLUMN, not a trait",
                capball.reload == "slow" && !capball.traits.Contains("slow"));
            T("arms: fists are on the table at the book's 1d3, and Agile",
                CharGen.D.weapons.Any(w => w.name == "Fists / Boots" && w.dmg == "1d3"
                                        && WeaponTraits.Parse(w.traits).Agile));

            // Range increments: clean inside the first, −2 per full increment past it.
            T("range: inside the first increment costs nothing", IronCode.IncrementsPast(50, 50) == 0);
            T("range: a foot past it is the second increment", IronCode.IncrementsPast(51, 50) == 1);
            T("range: and it is cumulative", IronCode.IncrementsPast(150, 50) == 2);
            T("range: an unstated distance runs no range rule at all", IronCode.IncrementsPast(0, 50) == 0);
            T("range: a shot at 120 ft with a 50 ft iron takes −4",
                IronCode.Reckon(new IronCode.Shot { Distance = 120 }, sar).Total == -4);

            // Point-blank waives the increment, and hands a long gun its own problem instead.
            T("point-blank: no range penalty at arm's length",
                IronCode.Reckon(new IronCode.Shot { Distance = 5 }, sar).Total == 0);
            // Read on the shotgun, which carries no Volley, so the long-gun rule stands alone.
            T("point-blank: but a long gun is unwieldy this close",
                IronCode.Reckon(new IronCode.Shot { Distance = 5 }, scat).Total == -2);
            T("point-blank: and bracing lifts it",
                IronCode.Reckon(new IronCode.Shot { Distance = 5 }, scat, braced: true).Total == 0);
            // The Buffalo Rifle is both unwieldy AND inside its own Volley band at arm's length,
            // and the book gives no reason those two would not both bite.
            T("point-blank: a Volley iron at arm's length wears both penalties",
                IronCode.Reckon(new IronCode.Shot { Distance = 5 }, buff).Total == -4);
            T("point-blank: bracing lifts only the one bracing is for",
                IronCode.Reckon(new IronCode.Shot { Distance = 5 }, buff, braced: true).Total == -2);

            // The flat rows.
            T("cover: light is −2", IronCode.Reckon(new IronCode.Shot { Cover = IronCode.Cover.Light }, sar).Total == -2);
            T("cover: heavy is −4", IronCode.Reckon(new IronCode.Shot { Cover = IronCode.Cover.Heavy }, sar).Total == -4);
            T("circumstance: firing into melee is −4",
                IronCode.Reckon(new IronCode.Shot { IntoMelee = true }, sar).Total == -4);
            var blind = IronCode.Reckon(new IronCode.Shot { Concealed = true }, sar);
            T("circumstance: a concealed target is −8 and cannot be targeted directly",
                blind.Total == -8 && blind.CannotTarget);
            T("circumstance: they stack, and each says why",
                IronCode.Reckon(new IronCode.Shot { Distance = 120, Cover = IronCode.Cover.Light,
                                                    IntoMelee = true }, sar).Parts.Count == 3);

            // Volley: a long iron resents close work. The Buffalo Rifle's is 30 ft.
            T("volley: inside the Volley band is −2",
                IronCode.Reckon(new IronCode.Shot { Distance = 30 }, buff).Total == -2);
            T("volley: and outside it is not",
                !IronCode.Reckon(new IronCode.Shot { Distance = 200 }, buff).Parts.Any(p => p.Contains("Volley")));

            // Nothing said about the ground means nothing charged — this is what keeps the playtest
            // numbers and the smoke fights where they were.
            T("circumstance: a caller who says nothing about the ground is charged nothing",
                IronCode.Reckon(null, sar).Total == 0 && IronCode.Reckon(IronCode.Shot.Plain, buff).Total == 0);

            // Off-Guard and Aim are paid elsewhere; charging them here would charge them twice.
            T("circumstance: Off-Guard is not charged here — the Burden already pays it",
                !IronCode.Reckon(IronCode.Shot.Plain, sar).Parts.Any(p => p.Contains("Off-Guard")));

            // Scatter: on a hit it splashes; on a miss inside the first increment the target wears it.
            var trScat = WeaponTraits.Parse(scat.traits);
            T("scatter: a hit splashes within its radius",
                IronCode.ScatterFalls(trScat, scat, hit: true, distance: 20) is (true, 10, false));
            T("scatter: a miss inside the first increment still catches the target",
                IronCode.ScatterFalls(trScat, scat, hit: false, distance: 20) is (true, 10, true));
            T("scatter: a miss beyond it catches nobody",
                !IronCode.ScatterFalls(trScat, scat, hit: false, distance: 90).Falls);
            T("scatter: a weapon without the trait never splashes",
                !IronCode.ScatterFalls(WeaponTraits.Parse(sar.traits), sar, true, 10).Falls);

            // Reloading, in the units the book prices each kind in.
            T("reload: a break-action is one Interact and it is whole",
                IronCode.Reloading(scat).Beats == 1);
            T("reload: thumbing one round into a repeater is one Beat",
                IronCode.Reloading(lever, full: false).Beats == 1);
            T("reload: topping a twelve-shot repeater is six Beats",
                IronCode.Reloading(lever).Beats == 6);
            T("reload: a six-gun is three", IronCode.Reloading(sar).Beats == 3);
            T("reload: Practiced Reload shaves one",
                IronCode.Reloading(sar, practiced: true).Beats == 2);
            T("reload: and can never shave it below one",
                IronCode.Reloading(scat, practiced: true).Beats >= 1);
            var slow = IronCode.Reloading(capball);
            T("reload: a cap-and-ball is three ROUNDS of work, not Beats",
                slow.Rounds == IronCode.SlowReloadRounds && slow.Beats == 0);
            T("reload: a blade has nothing to reload",
                IronCode.Reloading(CharGen.D.weapons.First(w => w.name == "Hatchet")).Kind == IronCode.ReloadKind.None);
        }

        // ---- The seven Beat actions, reactions, nonlethal, and the saddle ----
        {
            Combatant Soul() => new() { Name = "Anni Halvorsen", IsPC = true, Str = 15, Defense = 9,
                                        BloodCur = 12, BloodMax = 12, DeathAt = 12, Beats = 3, MapStep = 1 };

            T("beats: the chapter's action table is seven rows", Rules.BeatActions.Length == 7);
            T("beats: and every one of them costs a Beat the app can spend",
                Rules.BeatActions.All(a => a.Beats == 1));

            var a1 = Soul();
            var aimed = Rules.TakeAction(a1, "aim");
            T("beats: Aim spends a Beat and holds the aim", aimed.Done && a1.Beats == 2 && a1.Aimed);
            T("beats: and aiming twice is refused, out loud", !Rules.TakeAction(a1, "aim").Done);

            var a2 = Soul(); a2.Aimed = true;
            T("beats: Stride loses the aim, because the book says 'and did not move'",
                Rules.TakeAction(a2, "stride").Done && !a2.Aimed);

            var a3 = Soul();
            Rules.TakeAction(a3, "cover");
            T("beats: Take Cover steps to light", a3.Cover == IronCode.Cover.Light && a3.Beats == 2);
            Rules.TakeAction(a3, "cover");
            T("beats: and again to heavy", a3.Cover == IronCode.Cover.Heavy);
            var noMore = Rules.TakeAction(a3, "cover");
            T("beats: there is no step past heavy, and it says so rather than going quiet",
                !noMore.Done && noMore.Line.Length > 0);
            Rules.LeaveCover(a3);
            T("beats: leaving cover puts it down", a3.Cover == IronCode.Cover.None);

            var spentAll = Soul(); spentAll.Beats = 0;
            var refused = Rules.TakeAction(spentAll, "interact");
            T("beats: a soul with no Beats is refused, with the reason",
                !refused.Done && refused.Line.Contains("Beat"));

            // Reactions: one between your turns, given back when the turn comes round.
            var diver = Soul();
            T("reaction: a fresh soul has theirs", Rules.CanReact(diver));
            var dive = Rules.DiveForCover(diver);
            T("reaction: Dive for Cover takes it, and buys cover and a Prone",
                dive.Taken && dive.Cover == IronCode.Cover.Light && dive.Condition == "Prone");
            T("reaction: and there is only the one", !Rules.CanReact(diver) && !Rules.DiveForCover(diver).Taken);
            T("reaction: the refusal says why", Rules.WhyNoReaction(diver).Contains("already reacted"));
            diver.BeginTurn();
            T("reaction: the turn coming round gives it back", Rules.CanReact(diver));

            // Nonlethal: a pulled blow lays them out and never fills the ground toward −CON.
            var club = CharGen.D.weapons.First(w => w.name == "Club");
            var sixgun = CharGen.D.weapons.First(w => w.name == "Single-Action Revolver");
            T("nonlethal: a club pulls its blows by nature", IronCode.NonlethalByNature(club));
            T("nonlethal: a revolver does not", !IronCode.NonlethalByNature(sixgun));
            T("nonlethal: so pulling one costs −2",
                IronCode.Reckon(new IronCode.Shot { Nonlethal = true }, sixgun).Total == -2);
            T("nonlethal: and pulling a club costs nothing",
                IronCode.Reckon(new IronCode.Shot { Nonlethal = true }, club).Total == 0);

            var laid = Soul();
            laid.Wound(-40, nonlethal: true);
            T("nonlethal: brought to 0 they are senseless, not dying",
                laid.Senseless && laid.Down && !laid.Dying && !laid.Dead);
            T("nonlethal: and forty Blood of overkill never counted toward −CON", !laid.Dead);
            laid.Wound(3);
            T("nonlethal: patched back up, the senselessness ends with it",
                !laid.Senseless && !laid.Down);

            var killed = Soul();
            killed.Wound(-40);
            T("nonlethal: the same blow meant in earnest still kills", killed.Dead);

            // The saddle.
            T("saddle: standing and walking are not a moving platform; trot and gallop are",
                !IronCode.IsMoving(IronCode.Gait.Standing) && !IronCode.IsMoving(IronCode.Gait.Walking)
                && IronCode.IsMoving(IronCode.Gait.Trotting) && IronCode.IsMoving(IronCode.Gait.Galloping));
            T("saddle: a pistol at a gallop takes the moving platform's −2",
                IronCode.Reckon(new IronCode.Shot { Gait = IronCode.Gait.Galloping }, sixgun).Total == -2);
            T("saddle: a long gun at a gallop takes −4 in all",
                IronCode.Reckon(new IronCode.Shot { Gait = IronCode.Gait.Galloping },
                    CharGen.D.weapons.First(w => w.name == "Lever-Action Repeater")).Total == -4);
            T("saddle: at a walk the horseman's pistol is free",
                IronCode.Reckon(new IronCode.Shot { Gait = IronCode.Gait.Walking }, sixgun).Total == 0);
            T("saddle: you cannot aim from a moving horse", !IronCode.CanAim(IronCode.Gait.Trotting));
            T("saddle: but you can from a standing one", IronCode.CanAim(IronCode.Gait.Standing));

            var saber = CharGen.D.weapons.First(w => w.name == "Saber");
            T("saddle: mounted, you strike down at a footman for +1",
                IronCode.Reckon(new IronCode.Shot { Gait = IronCode.Gait.Standing, TargetMounted = false },
                                saber).Total == 1);
            T("saddle: and not at another rider",
                IronCode.Reckon(new IronCode.Shot { Gait = IronCode.Gait.Standing, TargetMounted = true },
                                saber).Total == 0);

            // The charge.
            T("charge: twenty feet with a saber is worth a die",
                IronCode.Charge(saber, 20) is { Made: true, ExtraDice: 1, DefenseAfter: -2 });
            T("charge: nineteen feet is not a charge", !IronCode.Charge(saber, 19).Made);
            T("charge: and a knife earns nothing however far it ran",
                !IronCode.Charge(CharGen.D.weapons.First(w => w.name == "Knife / Bowie"), 40).Made);
            T("charge: a refused charge says why", IronCode.Charge(saber, 5).Line.Length > 0);

            // Keeping the saddle.
            T("saddle: fifteen keeps it", IronCode.KeepTheSaddle(15).Kept);
            var thrown2 = IronCode.KeepTheSaddle(14);
            T("saddle: fourteen does not, and it costs 1d6 on the way down",
                !thrown2.Kept && thrown2.Damage >= 1 && thrown2.Damage <= 6);

            // New fight clears the turn state, and does not clear what is not of the turn.
            var after = Soul();
            after.Aimed = true; after.Recoiling = true; after.ReactionSpent = true;
            after.Cover = IronCode.Cover.Heavy;
            T("new fight: an aim, a recoil, a cover and a spent reaction all read as residue",
                Rules.FightResidue(after));
            Rules.ResetForNewFight(new[] { after });
            T("new fight: and all four are cleared",
                !after.Aimed && !after.Recoiling && !after.ReactionSpent
                && after.Cover == IronCode.Cover.None);
        }

        // ---- every Appendix B condition reaches the fight ----
        // Not "is in the switch" — REACHES it. The table has fifteen rows and the app answered for
        // all fifteen while two of them did nothing a fight could feel: Fatigued's "cannot Aim" had
        // no Aim to refuse, and Prone's "+4 to others' ranged against you" has an attacker in it and
        // so could never be a number on the bearer's own Burden. Both are asserted below, from the
        // side they actually bite on.
        {
            // The fifteen the printed Appendix B carries, in its own order.
            string[] appendixB =
            {
                "Bleeding", "Blinded", "Clumsy", "Drained", "Dying", "Fatigued", "Frightened",
                "Grabbed", "Lost", "Marked", "Off-Guard", "Prone", "Sickened", "Slowed", "Stunned",
            };
            // Four are narrative or run by their own machinery rather than by arithmetic: Bleeding
            // and Dying are the dying model's, and Marked and Lost are Ch. XII's Mark track.
            string[] notArithmetic = { "Bleeding", "Dying", "Marked", "Lost" };

            foreach (var name in appendixB)
            {
                var b = Rules.ConditionBurden(name, 1);
                T($"conditions: {name} is known to the engine", b != null);
                if (!notArithmetic.Contains(name))
                    T($"conditions: {name} costs something a fight can feel", b.Any);
                T($"conditions: {name} says what it does", b.Anything);
            }

            // Slowed and Stunned reach the Beats, which is the column nothing else touches.
            var slowed = new Combatant { Name = "Opal", Conditions = "Slowed 1" };
            T("conditions: Slowed 1 takes a Beat off the turn", slowed.BeatsThisTurn == 2);
            var stunned = new Combatant { Name = "Opal", Conditions = "Stunned" };
            T("conditions: Stunned takes the whole turn", stunned.BeatsThisTurn == 0);

            // Frightened scales with its number, and reaches every column at once.
            var f2 = Rules.ConditionBurden("Frightened", 2);
            T("conditions: Frightened 2 is −2 on everything",
                f2.Strike == -2 && f2.Defense == -2 && f2.Check == -2 && f2.Save == -2);

            // Sickened is the only one that reaches the DAMAGE, and it is easy to lose.
            T("conditions: Sickened takes its −2 off the damage as well", Rules.ConditionBurden("Sickened", 1).Damage == -2);

            // Fatigued's "cannot Aim" — a sentence in a cell until there was an Aim to refuse.
            // Blood on the row, or she reads as Down and is refused for that instead.
            var tired = new Combatant { Name = "Anni", Conditions = "Fatigued", Beats = 3,
                                        BloodCur = 12, BloodMax = 12 };
            var noAim = Rules.TakeAction(tired, "aim");
            T("conditions: the Fatigued cannot Aim, and are told why",
                !noAim.Done && noAim.Line.Contains("Fatigued") && tired.Beats == 3);

            // Prone's other half, read from the shooter's side.
            var sixgun2 = CharGen.D.weapons.First(w => w.name == "Single-Action Revolver");
            var knife2 = CharGen.D.weapons.First(w => w.name == "Knife / Bowie");
            T("conditions: shooting a sprawling target is +4",
                IronCode.Reckon(new IronCode.Shot { TargetProne = true }, sixgun2).Total == 4);
            T("conditions: and reaching one with a blade is not",
                IronCode.Reckon(new IronCode.Shot { TargetProne = true }, knife2).Total == 0);
            T("conditions: the prone soul's own −4 is still theirs, and is not counted twice",
                Rules.ConditionBurden("Prone", 1).Strike == -4
                && !IronCode.Reckon(IronCode.Shot.Plain, sixgun2).Parts.Any(p => p.Contains("sprawl")));

            // And it arrives through a real Strike, off the target's row, with nobody passing it in.
            var sprawled = new Combatant { Name = "The Mad Dog", Defense = 13, BloodCur = 10,
                                           BloodMax = 10, Conditions = "Prone" };
            var shooter = new Combatant { Name = "Ruth", IsPC = true, Beats = 3, MapStep = 1 };
            var atProne = CombatFlow.StrikeAndApply(shooter, sprawled, sixgun2, 0, null, 10);
            T("conditions: the +4 is read off the target's row by the engine itself",
                atProne.Circ.Parts.Any(p => p.Contains("sprawling")));
        }

        // A trace takes no turn, so it is not handed three Beats to spend on nothing.
        var trace = new Combatant { Name = "Something passed here", IsSign = true, Beats = 0, MapStep = 1 };
        Rules.NewRound(new List<Combatant> { trace });
        T("round: sign & spoor is not handed a turn", trace.Beats == 0);

        // Neither are the dead. A corpse showing three Beats reads as a row still waiting to go.
        var gone = new Combatant { Name = "Addison", IsPC = true, BloodMax = 9, DeathAt = 10, Beats = 0, MapStep = 3 };
        gone.Wound(-30);                       // straight past −CON
        T("round: the dead are dead before the round turns", gone.Dead);
        Rules.NewRound(new List<Combatant> { gone });
        T("round: and the dead are not handed a turn back", gone.Beats == 0 && gone.MapStep == 3);

        // The chip has to move when the COUNT moves, not only when something runs out. It printed
        // "✦ The Stilling (3)" and went on printing 3 as the Sign ticked to 2 and to 1, because the
        // only thing that said the column had changed was an effect expiring — and that count is the
        // Keeper's one read on how long they have left.
        var held = new Combatant { Name = "Opal", IsPC = true, BloodCur = 8, BloodMax = 8 };
        held.Work(new WorkedEffect { Name = "The Stilling", Kind = "Sign", RoundsLeft = 3 });
        string chip3 = held.WorkedChips;
        T("chips: a counted working prints its count", chip3.Contains("(3)"));
        held.TickWorked();
        T("chips: and the count on the chip moves when the round does",
            held.WorkedChips.Contains("(2)") && held.WorkedChips != chip3);
        held.TickWorked(); held.TickWorked();
        T("chips: an expired working leaves the column", held.WorkedChips == "");

        // A working with no round count must not be ticked into nothing by a rollover.
        var scene = new Combatant { Name = "Elias", IsPC = true, BloodCur = 9, BloodMax = 9 };
        scene.Work(new WorkedEffect { Name = "Witch-Sight", Kind = "Sign", RoundsLeft = -1,
                                      Ends = Rules.WorkEnds.Scene });
        scene.TickWorked(); scene.TickWorked();
        T("chips: a working measured in scenes survives the rounds", scene.Worked.Count == 1);
        T("chips: and says the unit the book used", scene.WorkedChips.Contains("(scene)"));
    }

    // ---- what a condition costs, and that it is DERIVED (v1.39.0) ----
    // Appendix B has been printed on the Reference deck since v1.4 and the ＋ Condition ▾ menu has
    // offered all sixteen since, and not one of them did anything: "Frightened: −1 (or worse) on
    // everything" was a word in a column and the Keeper's own arithmetic to carry, in the middle of
    // a fight, while remembering four other things.
    {
        var none = Rules.ReadConditions("");
        T("burden: nothing on you weighs nothing", !none.Any && !none.Anything);
        T("burden: an unknown condition a Keeper typed weighs nothing rather than throwing",
            !Rules.ReadConditions("Spooked something awful").Any);

        var fr2 = Rules.ReadConditions("Frightened 2");
        T("burden: Frightened 2 is −2 on everything the book lists",
            fr2.Strike == -2 && fr2.Defense == -2 && fr2.Check == -2 && fr2.Save == -2);
        var stacked = Rules.ReadConditions("Frightened 2, Off-Guard");
        T("burden: two conditions sum rather than the worse one winning",
            stacked.Defense == -4 && stacked.Strike == -2);
        T("burden: Slowed 1 costs a Beat and nothing else",
            Rules.ReadConditions("Slowed 1") is { BeatsLost: 1, Strike: 0, Defense: 0 });
        T("burden: Stunned costs the whole turn and 2 Defense",
            Rules.ReadConditions("Stunned") is { BeatsLost: 3, Defense: -2 });
        T("burden: Sickened reaches damage, which is the column the others do not",
            Rules.ReadConditions("Sickened").Damage == -2);
        // Prone counts its −4 to melee and REFUSES to count the +4 everyone shooting at them gets,
        // because that one depends on what the attacker is holding and the row does not know. What
        // it must not do is drop it silently — a number the reader cannot carry has to become words.
        var prone = Rules.ReadConditions("Prone");
        T("burden: Prone counts the half of its line that is unconditional", prone.Strike == -4);
        T("burden: and says the half it cannot count rather than dropping it",
            prone.Note.Contains("+4") && prone.Note.Contains("SHOOTING"));

        var lit = new Combatant { Name = "Anni", Defense = 12, BloodCur = 12, BloodMax = 12 };
        T("burden: an unburdened row prints its plain Defense", lit.DefenseLine == "12");
        lit.Conditions = "Frightened 2, Off-Guard";
        T("burden: Defense falls by what is on them", lit.EffectiveDefense == 8);
        T("burden: and the column shows the arithmetic, not just the total", lit.DefenseLine == "12 → 8");
        T("burden: the STORED Defense never moved — this is derived, not applied", lit.Defense == 12);
        // The fault this shape exists to prevent: an earlier sketch applied the modifier on Work and
        // took it off on Unwork, so a session saved mid-Sign reloaded with the penalty baked into
        // Defense AND the working still on the row, and it landed twice. Reading it twice must be
        // idempotent, which a stored adjustment is not.
        T("burden: reading it twice gives the same answer", lit.EffectiveDefense == 8 && lit.EffectiveDefense == 8);
        lit.Conditions = "";
        T("burden: and it lifts clean when the condition goes", lit.EffectiveDefense == 12 && lit.DefenseLine == "12");

        var slow = new Combatant { Name = "Doc", BloodCur = 9, BloodMax = 9, Conditions = "Slowed 1" };
        T("burden: Slowed takes a Beat off the turn", slow.BeatsThisTurn == 2);
        slow.BeginTurn();
        T("burden: and BeginTurn hands out that many, not three", slow.Beats == 2);
        Rules.NewRound(new List<Combatant> { slow });
        T("burden: the round rollover honours it too", slow.Beats == 2);
        slow.Conditions = "Stunned";
        Rules.NewRound(new List<Combatant> { slow });
        T("burden: Stunned means no turn at all", slow.Beats == 0);

        // The engine end: a Strike is rolled against the Defense as it stands, not as it was typed.
        var shooter = new Combatant { Name = "Ruth", IsPC = true, BloodCur = 12, BloodMax = 12 };
        var mark = new Combatant { Name = "Bandit", Defense = 20, BloodCur = 40, BloodMax = 40,
                                   Conditions = "Off-Guard" };
        var gun2 = new CgWeapon { name = "Revolver", dmg = "1d8", traits = "", kind = "gun" };
        shooter.BeginTurn();
        // die 18 + 0 = 18: misses Defense 20, hits the 18 that Off-Guard leaves.
        var hit = CombatFlow.StrikeAndApply(shooter, mark, gun2, 0, null, 18);
        T("burden: Off-Guard is what let that shot land", hit.Res.Strike.Hit);
        T("burden: and the log says which Defense it was rolled against",
            hit.Line.Contains("was 20"));

        shooter.MapStep = 1; shooter.Beats = 3;
        shooter.Conditions = "Frightened 3";
        var missed = CombatFlow.StrikeAndApply(shooter, mark, gun2, 0, null, 18);
        T("burden: the attacker's own fear comes off the Strike", !missed.Res.Strike.Hit);

        // The riders a creature's own attacks line carries.
        T("inflicts: a claw that grabs names Grabbed",
            Rules.InflictedConditions("1d6+2 and grab").Contains("Grabbed")
            || Rules.InflictedConditions("grabbed and held").Contains("Grabbed"));
        T("inflicts: a horror that frightens names the step it frightens to",
            Rules.InflictedConditions("saves or is Frightened 2").Contains("Frightened 2"));
        T("inflicts: a plain blow names nothing", Rules.InflictedConditions("1d6+2").Count == 0);
        T("inflicts: and neither does an empty rider", Rules.InflictedConditions(null).Count == 0);
    }

    // ---- more shapes of fight, hunting the cases three ordinary ones never reach ----
    {
        // A lone survivor still gets rounds: NextUp answers, the round spends, and the loop does
        // not stall on a field of one.
        var solo = new List<Combatant> { new() { Name = "Ruth", IsPC = true, Init = 9, BloodCur = 8, BloodMax = 20 } };
        Rules.NewRound(solo);
        T("solo: the last one standing is still up", Rules.NextUp(solo)?.Name == "Ruth");
        solo[0].BeginTurn();
        T("solo: and the round spends after them", Rules.RoundSpent(solo));

        // Downed mid-round and healed back before the round ends. They have not acted, so the turn
        // is still owed to them — being knocked down and dragged up is not the same as having gone.
        var revive = new List<Combatant>
        {
            new() { Name = "Opal", IsPC = true, Init = 18, BloodCur = 12, BloodMax = 12 },
            new() { Name = "Doc",  IsPC = true, Init = 4,  BloodCur = 12, BloodMax = 12 },
        };
        revive[0].Wound(-12);
        T("revive: down is out of the order", Rules.NextUp(revive)?.Name == "Doc");
        revive[1].BeginTurn();
        revive[0].Wound(+5);                    // the Doc's whole turn, spent on the Padre
        T("revive: healed back before the round ended, the turn is still owed",
            Rules.NextUp(revive)?.Name == "Opal");
        T("revive: so the round is not spent yet", !Rules.RoundSpent(revive));

        // Everyone still up goes down inside one round. The round must end rather than hunting for
        // somebody to hand the turn to.
        var wipe = new List<Combatant>
        {
            new() { Name = "Bandit A", Init = 14, BloodCur = 6, BloodMax = 6 },
            new() { Name = "Bandit B", Init = 13, BloodCur = 6, BloodMax = 6 },
        };
        wipe[0].BeginTurn();
        wipe[1].Wound(-6);
        T("wipe: the last one on the field is down, so nobody is up", Rules.NextUp(wipe) == null);
        T("wipe: one still standing having gone IS a spent round", Rules.RoundSpent(wipe));
        wipe[0].Wound(-6);
        T("wipe: but once they are all down it is not a round ending over and over",
            !Rules.RoundSpent(wipe));

        // The Keeper corrects an initiative mid-fight. The order must follow the number, both for
        // the turn and for the grid — this is the hand-edit path that used to leave them disagreeing.
        var edited = new List<Combatant>
        {
            new() { Name = "Silas",  IsPC = true, Init = 7,  BloodCur = 10, BloodMax = 10 },
            new() { Name = "Coyote", Init = 16, BloodCur = 10, BloodMax = 10 },
        };
        T("edit: before the correction the coyote leads", Rules.InTurnOrder(edited).First().Name == "Coyote");
        edited[0].Init = 19;
        T("edit: after it the order follows the number", Rules.InTurnOrder(edited).First().Name == "Silas");
        T("edit: and the turn agrees with the order", Rules.NextUp(edited).Name == "Silas");

        // A crowded field with heavy ties, asked twice: the order must not wobble between calls, or
        // the grid redraws into a different sequence than the one the turn is walking.
        var crowd = new List<Combatant>();
        for (int i = 0; i < 12; i++)
            crowd.Add(new Combatant { Name = $"Rider {(char)('A' + i)}", IsPC = i % 2 == 0,
                                      Init = 10 + (i % 3), BloodCur = 10, BloodMax = 10 });
        var first = Rules.InTurnOrder(crowd).Select(c => c.Name).ToList();
        var again = Rules.InTurnOrder(crowd).Select(c => c.Name).ToList();
        T("crowd: the order is the same answer twice", first.SequenceEqual(again));
        T("crowd: souls lead their own initiative band",
            Rules.InTurnOrder(crowd.Where(c => c.Init == 12)).First().IsPC);

        // Worked effects across three rounds of a real loop, since the rollover now owns the tick.
        var bearer = new Combatant { Name = "Elias", IsPC = true, Init = 11, BloodCur = 14, BloodMax = 14 };
        bearer.Work(new WorkedEffect { Name = "Salt & Iron", Kind = "Sign", Source = "Opal", RoundsLeft = 2 });
        bearer.Work(new WorkedEffect { Name = "The Long Watch", Kind = "Miracle", Source = "Elias", RoundsLeft = -1 });
        var one = new List<Combatant> { bearer };
        Rules.NewRound(one);
        T("effects: a two-round sign survives the first rollover", bearer.Worked.Any(w => w.Name == "Salt & Iron"));
        var out2 = Rules.NewRound(one);
        T("effects: and ends on the second, reported by name",
            out2.Any(x => x.Effect.Name == "Salt & Iron") && !bearer.Worked.Any(w => w.Name == "Salt & Iron"));
        Rules.NewRound(one);
        T("effects: one that runs until it is ended outlives the rounds",
            bearer.Worked.Any(w => w.Name == "The Long Watch"));

        // Something arrives mid-round, after souls above it have already gone. It has not acted, so
        // it acts this round — the door opens and the thing comes through it now, not next round.
        var mid = new List<Combatant>
        {
            new() { Name = "Ruth", IsPC = true, Init = 17, BloodCur = 10, BloodMax = 10 },
            new() { Name = "Anni", IsPC = true, Init = 6,  BloodCur = 10, BloodMax = 10 },
        };
        mid[0].BeginTurn();
        mid.Add(new Combatant { Name = "Wendigo", Init = 12, BloodCur = 40, BloodMax = 40 });
        T("arrival: it takes its place in the standing order",
            Rules.InTurnOrder(mid).Select(c => c.Name).SequenceEqual(new[] { "Ruth", "Wendigo", "Anni" }));
        T("arrival: and is up next, ahead of the soul below it", Rules.NextUp(mid).Name == "Wendigo");

        // A new fight after all that: the order is rebuilt from fresh rolls and nothing carries.
        Rules.ResetForNewFight(mid);
        T("new fight: nobody is still marked as having gone", mid.All(c => !c.HasActed && !c.Acting));
        T("new fight: everyone who is standing is back in the order",
            mid.Where(c => !c.Down).All(c => Rules.CanAct(c)));
    }

    // ---- the round rollover, out of the UI where a test can hold it ----
    var rollover = new Combatant { Name = "Ruth", BloodCur = 10, BloodMax = 10, Init = 12 };
    rollover.Work(new WorkedEffect { Name = "Borrowed Breath", Kind = "Sign", Source = "Opal", RoundsLeft = 1 });
    rollover.BeginTurn();
    rollover.Wound(-3);
    var ended = Rules.NewRound(new List<Combatant> { rollover });
    T("round: the rollover clears who has gone", !rollover.HasActed && !rollover.Acting);
    T("round: it clears what just happened", rollover.LastDelta == 0);
    T("round: an effect that runs out is reported with who it was on",
        ended.Count == 1 && ended[0].On == rollover && ended[0].Effect.Name == "Borrowed Breath");
    T("round: and is gone from the target", rollover.Worked.Count == 0);
    bool nullRoundOk = true;
    try { Rules.NewRound(null); } catch { nullRoundOk = false; }
    T("round: a null field is survivable", nullRoundOk);

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

// ---- the turn hourglass (v1.29.0) ----
// The clock is pure and fed elapsed milliseconds by its caller, which is the whole reason a
// five-minute turn can be run here in a millisecond. What has to hold: it counts down and stops at
// the floor, the sand's fraction tracks the time rather than the ticks, the face never lies about
// how much is left, and a held glass does not quietly keep draining.
{
    var g = new TurnClock();
    T("glass: a fresh glass holds the default five minutes",
        g.PresetSeconds == 300 && g.PresetSeconds == TurnClock.DefaultSeconds);
    T("glass: full, still, and not yet through", !g.Running && !g.Expired && g.Spent == 0 && g.Face == "5:00");

    T("glass: a still glass does not drain", !g.Tick(5000) && g.LeftMs == 300_000);

    g.Start();
    T("glass: started, it is running", g.Running && !g.Expired);
    g.Tick(60_000);
    T("glass: a minute gone reads 4:00", g.Face == "4:00");
    T("glass: a minute gone is a fifth of the sand", Math.Abs(g.Spent - 0.2) < 1e-9);

    g.Pause();
    g.Tick(60_000);
    T("glass: a HELD glass does not drain", g.Face == "4:00" && !g.Running);

    // Run it out in the small steps the animation really uses, not one big jump.
    g.Start();
    bool rang = false;
    for (int i = 0; i < 10_000 && !g.Expired; i++) if (g.Tick(60)) rang = true;
    T("glass: it runs out, and says so exactly once", g.Expired && rang);
    T("glass: through, it stops running rather than counting past zero", !g.Running && g.LeftMs == 0);
    T("glass: through, it reads 0:00 and all the sand is down", g.Face == "0:00" && g.Spent == 1);
    T("glass: an expired glass rings only once", !g.Tick(60));

    // Rounding UP: 1 ms left is still "0:01", never "0:00". A timer that shows zero for a whole
    // second before it fires reads as a broken timer.
    var nearly = new TurnClock { PresetSeconds = 10 };
    nearly.Start(); nearly.Tick(9_999);
    T("glass: a millisecond left still reads 0:01", nearly.Face == "0:01" && !nearly.Expired);

    // Start on a spent glass turns it over rather than doing nothing — otherwise the button is dead
    // exactly when a Keeper reaches for it.
    var again = new TurnClock { PresetSeconds = 5 };
    again.Start(); again.Tick(5_000);
    again.Start();
    T("glass: starting a spent glass fills it again", again.Running && !again.Expired && again.Spent == 0);

    // Changing the house rule mid-session must not cut the running turn short — but must take
    // effect on a glass nobody is using.
    var live = new TurnClock { PresetSeconds = 300 };
    live.Start(); live.Tick(10_000);
    live.PresetSeconds = 600;
    T("glass: a new length leaves the RUNNING turn alone", live.LeftMs == 290_000);
    live.Pause();
    live.PresetSeconds = 120;
    T("glass: a new length re-loads a held glass", live.LeftMs == 120_000);

    T("glass: the length is clamped to something a table could use",
        new TurnClock { PresetSeconds = 0 }.PresetSeconds == 5
        && new TurnClock { PresetSeconds = 999_999 }.PresetSeconds == 3600);

    T("glass: reset fills it and stops it", live.Running == false && Reset(live));
    static bool Reset(TurnClock c) { c.Start(); c.Tick(1000); c.Reset(); return !c.Running && c.Spent == 0; }

    // Every preset the menu offers must spell out as something a person would say out loud, and the
    // default has to be one of them — a default missing from its own list is a default nobody can
    // get back to after changing it.
    T("glass: six presets are offered", TurnClock.Presets.Length == 6);
    T("glass: the default is one of the presets", TurnClock.Presets.Contains(TurnClock.DefaultSeconds));
    T("glass: the presets are in order, and all usable",
        TurnClock.Presets.Zip(TurnClock.Presets.Skip(1)).All(p => p.First < p.Second)
        && TurnClock.Presets.All(s => s >= 5 && s <= 3600));
    T("glass: whole minutes are spelled in words", TurnClock.Spell(60) == "1 minute"
        && TurnClock.Spell(300) == "5 minutes" && TurnClock.Spell(900) == "15 minutes");
    T("glass: an odd length is spelled as a clock", TurnClock.Spell(90) == "1:30");

    // It is a preference, not session state: a house rule outlives the fight it was set during.
    var pd = new Prefs.Data();
    T("glass: off until asked for, and five minutes when it is", !pd.TurnTimer && pd.TurnSeconds == 300);
    var round2 = System.Text.Json.JsonSerializer.Deserialize<Prefs.Data>(
        System.Text.Json.JsonSerializer.Serialize(new Prefs.Data { TurnTimer = true, TurnSeconds = 600 }));
    T("glass: the house rule survives save and load", round2.TurnTimer && round2.TurnSeconds == 600);
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

    T("working: every Sign and Miracle is read", all.Count == 116);

    // Backlash is the Signs' half of the bargain and the Miracles' absence of one — the two
    // chapters saying, structurally, that faith does not bite back. It was buried mid-paragraph.
    T("working: all forty-four Signs carry a Backlash", signs.All(w => w.HasBacklash));
    T("working: no Miracle does — faith does not bite back", mirs.All(w => !w.HasBacklash));
    T("working: a Backlash is lifted clear of the effect text",
        !W("Witch-Sight").Effect.Contains("Backlash", StringComparison.OrdinalIgnoreCase)
        && W("Witch-Sight").Backlash.Length > 0);
    T("working: a Backlash printed as 'None' still keeps its words",
        W("Salt & Iron").HasBacklash && W("Salt & Iron").Backlash.Contains("kindest"));
    T("working: but it is not a warning — it does not bite", !W("Salt & Iron").BacklashBites);
    // Four of the forty-four print "Backlash: None" and then say something about why. The other
    // forty cost the worker something, and those are the ones the app should warn about.
    T("fifty-one of the fifty-five Signs actually bite", signs.Count(w => w.BacklashBites) == 51);

    // ---- the other half of the bargain, and the half a player actually chooses on ----
    // Backlash and the Mark are what a Sign COSTS. What it BUYS has to stay worth it, or the
    // choice between damnation and grace becomes a matter of taste. Measured 2026-08-27: rank
    // for rank the Signs lead on damage at 2, 3 and 5 and are level at 1 and 4, and the hardest
    // Sign in the book beats the hardest Miracle 27.0 to 21.0 on the average.
    //
    // These hold the SHAPE of that bargain rather than the exact figures, so that rebalancing is
    // free to move numbers and is not free to erase the trade.
    double Avg(string dice)
    {
        double t = 0;
        foreach (System.Text.RegularExpressions.Match m in
                 System.Text.RegularExpressions.Regex.Matches(dice ?? "", @"(?<n>\d*)d(?<s>\d+)"))
            t += (m.Groups["n"].Value == "" ? 1 : int.Parse(m.Groups["n"].Value))
                 * (int.Parse(m.Groups["s"].Value) + 1) / 2.0;
        return t;
    }
    double topSign = signs.Where(w => w.Damage.Length > 0).Select(w => Avg(w.Damage))
                          .DefaultIfEmpty(0).Max();
    double topMir = mirs.Where(w => w.Damage.Length > 0).Select(w => Avg(w.Damage))
                         .DefaultIfEmpty(0).Max();
    T($"bargain: the hardest Sign outhits the hardest Miracle ({topSign:0.0} to {topMir:0.0})",
        topSign > topMir);
    T("bargain: the Old Dark reaches a rank the faithful cannot buy safely",
        signs.Count(w => w.Damage.Length > 0) >= mirs.Count(w => w.Damage.Length > 0));

    // Two of the four Sign Callings begin play already Marked; not one of the six Faith Callings
    // ever does. That is the permanent half of the price, and it is what the Backlash clause
    // cannot express on its own.
    var signers = CharGen.D.callings.Where(c => c.signLists != null).ToList();
    var faithful = CharGen.D.callings.Where(c => c.miracleLists != null).ToList();
    T("bargain: some who work Signs begin the game Marked", signers.Any(c => c.startMark > 0));
    T("bargain: nobody who works Miracles ever does", faithful.All(c => c.startMark == 0));
    T("bargain: the two lists stay closed to each other",
        signers.All(c => c.miracleLists == null) && faithful.All(c => c.signLists == null));

    // Nothing is left as a shrug: Unclear is a legal answer but it should be rare, and right now
    // the two chapters give it up entirely.
    T("working: every one of the 116 resolves to a shape", all.All(w => w.Shape != Rules.WorkShape.Unclear));

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

    // A creature's power is a standing TRAIT, not something worked on anybody. Every Bestiary
    // special line is written that way and not one carries a die, a save, or a radius — so the
    // dialog must stop asking who it is being worked on and for how long. Counted against the
    // roster rather than a typed number: the claim is that EVERY creature has one, and a literal
    // here would have to be edited every time the Bestiary grows, which is how it goes stale.
    var powers = Db.Creatures.Where(c => !string.IsNullOrWhiteSpace(c.special))
        .Select(c => { var (n, e) = Rules.ParsePower(c.special); return Rules.ReadWorking(n, "Power", 0, "", e, 6); })
        .ToList();
    T("working: every creature's special line is read", powers.Count == Db.Creatures.Count);
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

    // The Afflictions are the Keeper's Book's own d10, transcribed — not a list the app made up.
    T("affliction: the d10 table has ten entries", Rules.Afflictions.Length == 10);
    T("affliction: in the book's order",
        Rules.Afflictions[0].name == "The Shakes" && Rules.Afflictions[9].name == "The Hollow");
    T("affliction: every one says what it costs", Rules.Afflictions.All(a => a.cost.Length > 20));
    bool affOk = true; var affSeen = new HashSet<string>();
    for (int i = 0; i < 900; i++)
    {
        var (d, n, c) = Rules.RollAffliction();
        if (d < 1 || d > 10 || Rules.Afflictions[d - 1].name != n || Rules.Afflictions[d - 1].cost != c) affOk = false;
        affSeen.Add(n);
    }
    T("affliction: a roll is always a real row of the table", affOk);
    T("affliction: and all ten can come up", affSeen.Count == 10);
}

T("tier 1 loss = 1",  Rules.NerveLoss(1).roll() == 1);
for (int i = 0; i < 100; i++)
{
    T("tier 2 = 1d4",  Rules.NerveLoss(2).roll() is >= 1 and <= 4);
    T("tier 3 = 1d6",  Rules.NerveLoss(3).roll() is >= 1 and <= 6);
    T("tier 5 = 1d10", Rules.NerveLoss(5).roll() is >= 1 and <= 10);
}

// ---- Encounter cost ----
// Typed on purpose. These are Ch. IV's own numbers as repriced in v1.44.0, and a test that read
// them off Rules.BudgetRungs would pass whatever the ladder later drifted to.
T("budget = 4 per soul", Rules.BudgetPerSoul == 4);
T("even foe = 8",   Rules.Cost(2, 4).cost == 8 && Rules.Cost(2, 4).role == "Even foe");
T("mook = 4",       Rules.Cost(1, 4).cost == 4);
T("standout = 16",  Rules.Cost(3, 4).cost == 16 && !Rules.Cost(3, 4).spoor);
T("spoor at +2",    Rules.Cost(4, 4).spoor);
{
    // The rungs are one array now, and everything that prices or prints a fight reads it. If Cost
    // ever grows a literal again this fails before the Reference deck starts reciting two ladders.
    var rungs = Rules.BudgetRungs;
    T("rungs: three of them, mook first", rungs.Length == 3
        && rungs[0].Name == "Mook" && rungs[1].Name == "Even foe" && rungs[2].Name == "Standout");
    T("rungs: Cost prices every creature off the array",
        Rules.Cost(1, 4).cost == rungs[0].Cost && Rules.Cost(2, 4).cost == rungs[1].Cost
        && Rules.Cost(3, 4).cost == rungs[2].Cost);
    // Ch. IV's shape, which the repricing kept: a standout is twice an even foe, an even foe twice
    // a mook. The measured ladder happened to hold it, and a later retune that breaks the doubling
    // is a different rule, which should have to come here and say so.
    T("rungs: each is twice the one below",
        rungs[1].Cost == rungs[0].Cost * 2 && rungs[2].Cost == rungs[1].Cost * 2);
    // Past the safe-table line a thing is never seated, but it still has to cost something.
    T("rungs: beyond the posse is priced at the dearest rung",
        Rules.Cost(4, 4).cost == rungs[2].Cost && Rules.Cost(4, 4).spoor);
}

// ---- The budget verdict (what the Encounter tab's bar and line both read from) ----
{
    // Ch. IV names FOUR fights and prices each as a multiple of the budget: half is easy, the
    // budget is standard ("the party should win bloodied"), half again over is hard, double is
    // deadly. Nothing else is a band. Until v1.41.0 the app had five of its own invention and
    // called the exact budget "a fair, hard fight" — the book's word for 1.5x.
    T("budget: nothing costed is Empty",     Rules.BudgetBand(0, 24) == Rules.Weight.Empty);
    T("budget: half is Easy",                Rules.BudgetBand(12, 24) == Rules.Weight.Easy);
    T("budget: the budget is Standard",      Rules.BudgetBand(24, 24) == Rules.Weight.Standard);
    T("budget: half again over is Hard",     Rules.BudgetBand(36, 24) == Rules.Weight.Hard);
    T("budget: double is Deadly",            Rules.BudgetBand(48, 24) == Rules.Weight.Deadly);
    T("budget: past double is Beyond",       Rules.BudgetBand(60, 24) == Rules.Weight.Beyond);

    // The boundaries fall at the MIDPOINTS between the named multiples — 3/4, 5/4, 7/4, 9/4 — so a
    // spend belongs to whichever of the four it is nearest.
    T("budget: 3/4 of budget is still Easy", Rules.BudgetBand(18, 24) == Rules.Weight.Easy);
    T("budget: a point past 3/4 is Standard",Rules.BudgetBand(19, 24) == Rules.Weight.Standard);
    T("budget: 5/4 is still Standard",       Rules.BudgetBand(30, 24) == Rules.Weight.Standard);
    T("budget: a point past 5/4 is Hard",    Rules.BudgetBand(31, 24) == Rules.Weight.Hard);
    T("budget: 9/4 is still Deadly",         Rules.BudgetBand(54, 24) == Rules.Weight.Deadly);
    T("budget: a point past 9/4 is Beyond",  Rules.BudgetBand(55, 24) == Rules.Weight.Beyond);

    // The band is a RATIO, and this is the whole reason the old flat "budget + 4" had to go: it
    // made one point past the budget mean a different fight for a two-hand posse than for a six.
    // The same fraction must read the same band at every party size.
    for (int souls = 1; souls <= 8; souls++)
    {
        int b = 4 * souls;
        if (Rules.BudgetBand(b, b) != Rules.Weight.Standard)
            { T($"budget: {souls} souls — the budget must be Standard", false); goto doneBudget; }
        if (Rules.BudgetBand(b * 2, b) != Rules.Weight.Deadly)
            { T($"budget: {souls} souls — double must be Deadly", false); goto doneBudget; }
    }
    T("budget: the same fraction reads the same band at every party size", true);

    // Empty wins when nothing is costed, whatever the budget.
    T("budget: 0 spend, 0 budget is Empty", Rules.BudgetBand(0, 0) == Rules.Weight.Empty);
    T("budget: negative spend is Empty",    Rules.BudgetBand(-3, 12) == Rules.Weight.Empty);

    // Every spend lands in exactly one band, the bands only ever climb, and all of them have words.
    for (int budget = 4; budget <= 40; budget += 4)
    {
        var last = Rules.Weight.Empty;
        for (int spend = 0; spend <= budget * 3; spend++)
        {
            var band = Rules.BudgetBand(spend, budget);
            if (band < last)
                { T($"budget: {spend}/{budget} went backwards down the scale", false); goto doneBudget; }
            last = band;
            if (string.IsNullOrWhiteSpace(Rules.BudgetVerdict(spend, budget)))
                { T($"budget: {spend}/{budget} has no words", false); goto doneBudget; }
        }
    }
    T("budget: every spend 0..3x budget lands in one band, and the scale only climbs", true);
    doneBudget: ;

    T("budget: the standard verdict says so", Rules.BudgetVerdict(24, 24).Contains("STANDARD"));
    T("budget: standard promises bloodied",   Rules.BudgetVerdict(24, 24).Contains("win bloodied"));
    T("budget: the deadly verdict says so",   Rules.BudgetVerdict(48, 24).Contains("DEADLY"));

    // Ch. IV does not only price a deadly fight, it tells the Keeper to warn the table first. A
    // warning the app knows to give and does not give is the same fault as a Beat action it prints
    // and cannot spend.
    T("budget: deadly carries the warning",   Rules.BudgetVerdict(48, 24).Contains("before they commit"));

    // The scale is written down ONCE. The Reference deck's Long Odds leaf renders from this same
    // array, so leaf and tab cannot print different scales the way they did for six releases.
    T("budget: four fights, in the book's order",
        Rules.BudgetFights.Length == 4
        && Rules.BudgetFights[0].Band == Rules.Weight.Easy
        && Rules.BudgetFights[1].Band == Rules.Weight.Standard
        && Rules.BudgetFights[2].Band == Rules.Weight.Hard
        && Rules.BudgetFights[3].Band == Rules.Weight.Deadly);
    T("budget: every named fight has a name and a spend",
        Rules.BudgetFights.All(f => !string.IsNullOrWhiteSpace(f.Name) && !string.IsNullOrWhiteSpace(f.Spend)));
    // The chapter glosses two of the four and no more; the other two carry null rather than words
    // the book never wrote.
    T("budget: only the two the chapter glosses carry a promise",
        Rules.BudgetFights.Count(f => f.Promise != null) == 2);
    T("budget: the verdict for a band renders from that band's own row",
        Rules.BudgetFights.All(f => Rules.BudgetVerdict(0, 0) != null
            && Rules.BudgetVerdict(f.Band == Rules.Weight.Easy ? 12
                                 : f.Band == Rules.Weight.Standard ? 24
                                 : f.Band == Rules.Weight.Hard ? 36 : 48, 24)
                 .Contains(f.Name.ToUpperInvariant())));
}

// ---- Junior for the Tier: the odd level is not the same fight as the even one ----
{
    // Ch. IV rounds half the party's level TOWARD danger, so a posse at an odd level is matched
    // against the Tier the Bestiary reserves for the level above them. Both books are right and
    // they are not the same night — measured on the engine, one rung of level is worth about a
    // whole creature at every Tier. The app used to print "Even foe" for both and mean two things.
    T("junior: level 1 is the junior half of Tier I",  Rules.JuniorForTier(1));
    T("junior: level 2 is not",                        !Rules.JuniorForTier(2));
    T("junior: level 3 is the junior half of Tier II", Rules.JuniorForTier(3));
    T("junior: level 5 is the junior half of Tier III",Rules.JuniorForTier(5));
    T("junior: level 0 is nobody",                     !Rules.JuniorForTier(0));

    // The junior levels are exactly the ones where PartyTier rounds UP past level/2.
    for (int lvl = 1; lvl <= 10; lvl++)
        if (Rules.JuniorForTier(lvl) != (Rules.PartyTier(lvl) * 2 > lvl))
            { T($"junior: level {lvl} disagrees with PartyTier's rounding", false); goto doneJunior; }
    T("junior: the flag is exactly PartyTier rounding toward danger", true);
    doneJunior: ;

    T("junior: an even foe at an odd level says the posse is junior",
        Rules.Cost(1, 1).role.Contains("junior") && Rules.Cost(1, 1).cost == 8);
    T("junior: an even foe at an even level says only Even foe",
        Rules.Cost(1, 2).role == "Even foe");
    // A mook or a standout is priced off the same Tier ladder and gains nothing from the note.
    T("junior: a mook is still just a Mook at an odd level", Rules.Cost(1, 5).role == "Mook");
}

// ---- A Calling that works nothing works nothing at TENTH level either ----
{
    // The Work dialog's commonest state is an empty list — four of the six pregens work nothing,
    // correctly — and it showed that as a bare "— something else —" over nothing, which reads from
    // the far side of the table as the app having lost the soul's Signs. This is what lets it say
    // WHICH empty: the Calling works none, or this soul has not learned one yet.
    T("works-nothing: a Gunhand works nothing",     CharGen.CallingWorksNothing("Gunhand"));
    T("works-nothing: a Sawbones works nothing",    CharGen.CallingWorksNothing("Sawbones"));
    T("works-nothing: a Preacher works Miracles",   !CharGen.CallingWorksNothing("Preacher"));
    T("works-nothing: a Hexer works Signs",         !CharGen.CallingWorksNothing("Hexer"));
    // An unknown Calling says nothing rather than guessing — a wrong sentence is worse than none.
    T("works-nothing: an unknown Calling is not claimed", !CharGen.CallingWorksNothing("Riverboat Gambler"));

    // The claim is about the CALLING and must hold at every level it can reach, or the dialog would
    // tell a 1st-level Preacher they work nothing and then contradict itself at 3rd.
    foreach (var cal in CharGen.D.callings)
    {
        bool never = CharGen.CallingWorksNothing(cal.name);
        for (int lvl = 1; lvl <= 10; lvl++)
        {
            bool anyHere = CharGen.SignsFor(cal, lvl).Count > 0 || CharGen.MiraclesFor(cal, lvl).Count > 0;
            if (never && anyHere)
                { T($"works-nothing: {cal.name} works something at level {lvl}", false); goto doneWorks; }
        }
    }
    T("works-nothing: no Calling it denies works anything at any level 1-10", true);
    doneWorks: ;
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

// ---- The Beat, enforced (Ch. XI) ----
// The Beats were counted and never spent-out: the Strike dialog kept resolving at zero. These hold
// the predicate the UI greys its button on, and the reason it prints beside it.
{
    var up = new Combatant { Name = "Ruth", BloodCur = 20, BloodMax = 20, Beats = 3 };
    T("beats: three Beats can pay for one",  Rules.CanSpendBeats(up));
    T("beats: and nothing is refused",        Rules.WhyNoBeats(up) == null);
    up.Beats = 0;
    T("beats: an empty turn cannot pay",      !Rules.CanSpendBeats(up));
    T("beats: and it says so, by name",       Rules.WhyNoBeats(up)?.Contains("Ruth") == true);
    T("beats: and says the turn is done",     Rules.WhyNoBeats(up)?.Contains("Next turn") == true);
    up.Beats = 1;
    T("beats: one Beat cannot buy two",       !Rules.CanSpendBeats(up, 2));
    T("beats: and the refusal names the price", Rules.WhyNoBeats(up, 2)?.Contains("costs 2") == true);
    T("beats: a free action is always allowed", Rules.CanSpendBeats(up, 0));
    T("beats: even with nothing left",          Rules.CanSpendBeats(new Combatant { Name = "x", BloodCur = 1, BloodMax = 1, Beats = 0 }, 0));

    var trace = new Combatant { Name = "Sign of the Wendigo", IsSign = true, Beats = 3 };
    T("beats: a trace never acts",            !Rules.CanSpendBeats(trace));
    var felled = new Combatant { Name = "Jed", BloodCur = 0, BloodMax = 10, Beats = 3 };
    T("beats: the fallen never act",          !Rules.CanSpendBeats(felled));
    T("beats: and are told why",              Rules.WhyNoBeats(felled)?.Contains("down") == true);

    // The printed time line, read as a cost. This is the half the app parsed and never charged.
    T("beats: \"1 Beat\" costs one",          Rules.BeatsFor("1 Beat") == 1);
    T("beats: \"3 Beats\" costs three",       Rules.BeatsFor("3 Beats") == 3);
    T("beats: the book's spelt-out one",      Rules.BeatsFor("one Beat") == 1);
    T("beats: a minute is not a Beat",        Rules.BeatsFor("1 minute") == 0);
    T("beats: nor is an hour",                Rules.BeatsFor("one hour") == 0);
    T("beats: nor ten minutes",               Rules.BeatsFor("10 minutes") == 0);
    T("beats: an unreadable line costs nothing", Rules.BeatsFor("as the Keeper says") == 0);
    T("beats: and so does no line at all",    Rules.BeatsFor(null) == 0 && Rules.BeatsFor("") == 0);
    // Read off a real printed cost, the way the Work dialog does it.
    T("beats: parsed out of a whole cost line",
        Rules.BeatsFor(Rules.ParseCost("1 Beat · 2 Nerve · Will save").Time) == 1);
}

// ---- Dying, bleeding, and death (Player's Book Ch. XI) ----
// "At 0 Blood you fall, Dying and bleeding — losing 1 Blood each round — until someone stabilizes
// you or you reach –CON, at which point you are dead." Printed on the Reference deck since v1.4 and
// implemented nowhere until v1.38.0, so every one of these is a first assertion.
{
    Combatant Soul(int blood = 20, int con = 12) =>
        new() { Name = "Ruth", BloodCur = blood, BloodMax = blood, IsPC = true, DeathAt = con, Beats = 3 };

    // -- a creature is untouched by all of it: DeathAt 0 means the rule does not run here --
    var beast = new Combatant { Name = "The Risen", BloodCur = 4, BloodMax = 14 };
    beast.Wound(-9);
    T("dying: a creature at 0 Blood is simply down", beast.Down && !beast.Dying && !beast.Dead);
    T("dying: and its overkill is not counted",      beast.Bleed == 0);
    T("dying: and it shows no death clock",          beast.DyingLine == "");

    // -- a soul falls, and the count starts --
    var ruth = Soul();
    ruth.Wound(-20);
    T("dying: a soul at 0 Blood is Dying",     ruth.Dying && ruth.Down && !ruth.Dead);
    T("dying: and starts the count at zero",   ruth.Bleed == 0);
    T("dying: with CON rounds to live",        ruth.RoundsToDeath == 12);
    T("dying: and the row says so",            ruth.DyingLine == "dying −0 of 12");
    T("dying: the fallen take no turn",        !Rules.CanAct(ruth));

    // -- a Blood a round, and the round says it --
    var news = Rules.BleedOut(new[] { ruth });
    T("dying: a round costs a Blood",          ruth.Bleed == 1 && ruth.RoundsToDeath == 11);
    T("dying: and the round reports it",       news.Count == 1 && news[0].Who == ruth && !news[0].Died);
    for (int i = 0; i < 10; i++) Rules.BleedOut(new[] { ruth });
    T("dying: eleven rounds is not yet death", ruth.Bleed == 11 && ruth.Dying && !ruth.Dead);
    T("dying: with one round left",            ruth.RoundsToDeath == 1);
    var last = Rules.BleedOut(new[] { ruth });
    T("dying: reaching −CON is death",         ruth.Dead && ruth.Bleed == 12);
    T("dying: the round says who died",        last.Count == 1 && last[0].Died);
    T("dying: the dead are no longer dying",   !ruth.Dying);
    T("dying: and the row says dead",          ruth.DyingLine == "dead");
    T("dying: the dead take no turn",          !Rules.CanAct(ruth));
    T("dying: and the dead stop bleeding",     Rules.BleedOut(new[] { ruth }).Count == 0 && ruth.Bleed == 12);

    // -- the boundary, exactly. Dead AT −CON, not one short and not one past --
    var edge = Soul(1, 3);
    edge.Wound(-1);
    Rules.BleedOut(new[] { edge }); Rules.BleedOut(new[] { edge });
    T("dying: −2 of 3 is still alive",         edge.Bleed == 2 && !edge.Dead && edge.Dying);
    Rules.BleedOut(new[] { edge });
    T("dying: −3 of 3 is dead",                edge.Bleed == 3 && edge.Dead);

    // -- overkill carries past zero, which is what "reach −CON" has to mean --
    var shot = Soul(4, 12);
    shot.Wound(-14);
    T("dying: a blow past zero keeps counting", shot.Bleed == 10 && shot.Dying);
    T("dying: and Blood itself never goes negative", shot.BloodCur == 0);
    var cannon = Soul(4, 12);
    cannon.Wound(-40);
    T("dying: a blow past −CON kills outright", cannon.Dead && cannon.Bleed >= 12);
    T("dying: and says so in the Last column",  cannon.LastNote == "KILLED");

    // -- stabilizing stops the clock; it does not wake anybody --
    var bled = Soul(10, 12);
    bled.Wound(-10);
    Rules.BleedOut(new[] { bled }); Rules.BleedOut(new[] { bled });
    var missed = Rules.Stabilize(bled, 0, forcedDie: 2);     // 2 vs DC 15 — a critical failure
    T("dying: a failed check leaves them bleeding", !missed.Stopped && !bled.Stable && bled.Dying);
    var ok2 = Rules.Stabilize(bled, 0, forcedDie: 16);        // 16 vs DC 15 — a plain success
    T("dying: a success stops the bleeding",   ok2.Stopped && bled.Stable && !bled.Dying);
    T("dying: stable is not awake",            bled.BloodCur == 0 && bled.Down);
    T("dying: and the row says stable",        bled.DyingLine == "stable");
    T("dying: a stable body stops losing Blood", Rules.BleedOut(new[] { bled }).Count == 0 && bled.Bleed == 2);
    var crit = Soul(10, 12);
    crit.Wound(-10);
    var woke = Rules.Stabilize(crit, 10, forcedDie: 20);      // beats DC 15 by 10 — critical success
    T("dying: a critical success brings them round", woke.Woke && crit.BloodCur == 1 && !crit.Down);
    T("dying: and clears the count with them", crit.Bleed == 0 && !crit.Stable);

    // -- healing past zero undoes all of it --
    var mended = Soul(8, 12);
    mended.Wound(-8);
    Rules.BleedOut(new[] { mended });
    mended.Wound(6);
    T("dying: healing above zero ends the dying", !mended.Dying && !mended.Down && mended.Bleed == 0);
    T("dying: and they can act again",          Rules.CanAct(mended));

    // -- Grit: refuse to fall (Ch. II) --
    var brave = Soul(6, 12);
    var soul = new PartyMember { Name = "Ruth", Grit = 1 };
    brave.Wound(-6);
    T("grit: a fallen soul cannot act",        !Rules.CanAct(brave));
    T("grit: refusing spends the point",       Rules.RefuseToFall(brave, soul) == null && soul.Grit == 0);
    T("grit: and puts them back on their feet", brave.Upright && Rules.CanAct(brave));
    T("grit: but it does not stop the bleeding", brave.Dying);
    T("grit: it cannot be spent twice in a round", Rules.RefuseToFall(brave, soul)?.Contains("already") == true);
    Rules.BleedOut(new[] { brave });
    T("grit: one more round means one",        !brave.Upright && !Rules.CanAct(brave));
    T("grit: and the round still cost a Blood", brave.Bleed == 1);
    T("grit: with no Grit there is no refusing", Rules.RefuseToFall(brave, soul)?.Contains("no Grit") == true);
    T("grit: nobody standing has a fall to refuse",
        Rules.RefuseToFall(Soul(), new PartyMember { Grit = 3 })?.Contains("still on their feet") == true);
    T("grit: and the dead are past it",
        Rules.RefuseToFall(cannon, new PartyMember { Grit = 3 })?.Contains("dead") == true);
    T("grit: a foe has no Grit to spend",
        Rules.RefuseToFall(beast, null)?.Contains("posse") == true);

    // -- where −CON comes from --
    T("dying: a sheet's CON is the threshold",
        Rules.DeathThresholdFor(new CharacterSheet { Scores = new() { ["CON"] = 14 } }) == 14);
    T("dying: no sheet falls back to the middle of the scale",
        Rules.DeathThresholdFor(null) == Rules.DefaultDeathAt);
    T("dying: and so does a sheet with no CON on it",
        Rules.DeathThresholdFor(new CharacterSheet()) == Rules.DefaultDeathAt);

    // -- the round is not over while somebody is still up on Grit --
    var standing = Soul(); standing.Wound(-20);
    Rules.RefuseToFall(standing, new PartyMember { Grit = 3 });
    T("dying: a soul up on Grit keeps the round open", !Rules.RoundSpent(new[] { standing }));
    T("dying: and is who is up next",                  Rules.NextUp(new[] { standing }) == standing);
    var corpses = new[] { cannon, beast };
    T("dying: a field of the dead and the downed has no round left", !Rules.RoundSpent(corpses));

    // -- New fight is Blood-adjacent, so it must NOT quietly make a dying soul well --
    var stillDying = Soul(9, 12);
    stillDying.Wound(-9);
    Rules.BleedOut(new[] { stillDying });
    Rules.RefuseToFall(stillDying, new PartyMember { Grit = 2 });
    Rules.ResetForNewFight(new[] { stillDying });
    T("dying: New fight does not stop the bleeding", stillDying.Dying && stillDying.Bleed == 1);
    T("dying: nor heal the body",                    stillDying.BloodCur == 0 && stillDying.DeathAt == 12);
    T("dying: but the Grit round is over",           !stillDying.Upright);

    // Standing on Grit is turn state, so New fight has to count it as something to clear — the
    // paired guard that stopped New fight answering "nothing to clear" over a spent posse.
    var stillUp = Soul(5, 12);
    stillUp.Wound(-5);
    Rules.RefuseToFall(stillUp, new PartyMember { Grit = 1 });
    T("dying: refusing to fall is fight residue", Rules.FightResidue(stillUp));

    // -- all of it survives a save and a load, and an old session defaults to nobody dying --
    var dySess = new GameSession();
    dySess.Tracker.Add(stillDying);
    var dyBack = System.Text.Json.JsonSerializer.Deserialize<GameSession>(
        System.Text.Json.JsonSerializer.Serialize(dySess));
    T("dying: the count rides in the session file",
        dyBack.Tracker[0].Bleed == 1 && dyBack.Tracker[0].DeathAt == 12 && dyBack.Tracker[0].Dying);
    var oldRow = System.Text.Json.JsonSerializer.Deserialize<Combatant>(
        "{\"Name\":\"old row\",\"BloodCur\":0,\"BloodMax\":10,\"IsPC\":true}");
    T("dying: a session written before the rule has nobody dying",
        oldRow.Down && !oldRow.Dying && !oldRow.Dead && oldRow.DeathAt == 0);
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

// ---- what counts as an empty session, and so what may be overwritten with the demo posse ----
// The launch path asked "is the PARTY empty?" and threw away everything else in the file when it
// was. Each of these is a night's work that used to vanish on the next launch, and did it quietly.
{
    T("untouched: a genuinely blank session is untouched", new GameSession().IsUntouched);
    T("untouched: a session with a posse is not", new GameSession { Party = { new PartyMember() } }.IsUntouched == false);
    T("untouched: a written ledger alone is enough to keep", new GameSession { Notes = "the well at Coffin Wells" }.IsUntouched == false);
    T("untouched: so is a thread on the clock", new GameSession { Clocks = { new CampaignClock() } }.IsUntouched == false);
    T("untouched: so is a field left standing", new GameSession { Tracker = { new Combatant() } }.IsUntouched == false);
    T("untouched: so is a sign on the trail", new GameSession { Signs = { new Combatant { IsSign = true } } }.IsUntouched == false);
    T("untouched: so is a horse in the corral", new GameSession { Rides = { new Ride() } }.IsUntouched == false);
    T("untouched: so is a marker on the map", new GameSession { MapMarkers = { new MapMarker() } }.IsUntouched == false);
    T("untouched: so is an encounter being costed", new GameSession { EncounterCreatures = { "The Risen" } }.IsUntouched == false);
    T("untouched: whitespace in the ledger is not writing", new GameSession { Notes = "   \r\n " }.IsUntouched);
    // The shape the bug actually took: a posse cleared, everything else still there.
    var nightOff = new GameSession { Notes = "Tuesday — nobody but NPCs", Clocks = { new CampaignClock { Name = "The ring of nails" } } };
    T("untouched: an all-NPC night with an empty posse is NOT an empty session", nightOff.IsUntouched == false);
    T("untouched: and it survives a save and load", System.Text.Json.JsonSerializer
        .Deserialize<GameSession>(System.Text.Json.JsonSerializer.Serialize(nightOff)).IsUntouched == false);
}

// ---- Where the table lives (AppState.Resolve) ----
// This decides whether a Keeper's campaign is found or silently abandoned on a first run, so
// every combination is walked rather than trusted. The order it encodes: an explicit portable
// marker wins; an existing session beside the exe is honoured (nobody gets moved off a folder
// they are already using); otherwise the per-user folder, which no build or package step can
// reach. Before this, "beside the exe" was the only answer and packaging a release destroyed
// the table of anyone playing out of the delivered folder.
{
    const string Beside = @"C:\app", Roaming = @"C:\users\x\AppData\Roaming\GritKeeper";
    string R(bool portable, bool session) => AppState.Resolve(Beside, Roaming, portable, session);

    T("state: a plain first run goes to the per-user folder", R(false, false) == Roaming);
    T("state: a portable marker pins it beside the exe", R(true, false) == Beside);
    T("state: an existing session beside the exe is honoured", R(false, true) == Beside);
    T("state: both together still mean beside the exe", R(true, true) == Beside);
    // The property that matters: nothing but the two beside-the-exe signals can pull it off the
    // per-user folder, and either one on its own is enough.
    T("state: the per-user folder is the answer only when neither signal is present",
        (R(false,false) == Roaming) && (R(true,false) != Roaming) && (R(false,true) != Roaming) && (R(true,true) != Roaming));
    T("state: the marker filename is the one the docs and package.ps1 name", AppState.PortableMarker == "portable.txt");

    // The live folder must be usable and must exist — a Keeper whose profile is locked down
    // should still get an app that runs, which is why Dir falls back rather than throwing.
    var live = AppState.Dir;
    T("state: the resolved folder is a real, created directory",
        !string.IsNullOrWhiteSpace(live) && System.IO.Directory.Exists(live));
    T("state: it is stable within a run", AppState.Dir == live);
}

// ---- Character generator: data sanity ----
CharGen.Load();
var cg = CharGen.D;

// The flavor pools — a soul's vice, what they lost, what they've seen, what moves them, and the
// gendered given names. A pool that thinned out still generates perfectly valid souls; they just
// come out the same souls over a long campaign, which is the failure nobody notices.
foreach (var (pool, floor) in new[] { ("vices", 32), ("lost", 28), ("seen", 28), ("moving", 28),
                                      ("givenWomen", 50), ("givenMen", 51) })
    T($"flavor pool [{pool}] is at least {floor} deep", CharGen.FlavorList(pool).Count >= floor);

// ---- What a soul looks like (Data/appearance.json) ----
// Held to the same depth rule as the flavor pools, and for the same reason: a thin list still
// generates perfectly good descriptions, and a campaign quietly meets the same face nine times.
{
    Look.Load();
    var L = Look.D;
    T("look: the data loads", L.peoples.Count >= 20 && L.styles.Count >= 15);
    foreach (var (name, count, floor) in new[]
    {
        ("peoples", L.peoples.Count, 24), ("styles", L.styles.Count, 15),
        ("heights", L.heights.Count, 6), ("frames", L.frames.Count, 8),
        ("bearings", L.bearings.Count, 10), ("faces", L.faces.Count, 12),
        ("marks", L.marks.Count, 14), ("voices", L.voices.Count, 8),
        ("hairStyles", L.hairStyles.Count, 10), ("facialHair", L.facialHair.Count, 8),
        ("wear", L.wear.Count, 10), ("details", L.details.Count, 14),
    })
        T($"look: [{name}] is at least {floor} deep", count >= floor);

    // Every people has to be able to answer all three of its own questions, or a draw comes back
    // with a blank complexion and the sheet reads as broken rather than as unfinished data.
    T("look: every people carries complexions, hair and eyes",
        L.peoples.All(p => p.complexions.Count >= 3 && p.hair.Count >= 3 && p.eyes.Count >= 3));
    T("look: every people is weighted above zero", L.peoples.All(p => p.weight > 0));
    T("look: peoples are named once each",
        L.peoples.Select(p => p.name).Distinct(StringComparer.OrdinalIgnoreCase).Count() == L.peoples.Count);

    // Same for a style's wardrobe: a style with no boots dresses a soul barefoot by accident.
    T("look: every style dresses a soul head to foot",
        L.styles.All(s => s.hats.Count >= 3 && s.coats.Count >= 3 && s.shirts.Count >= 3
                       && s.legs.Count >= 3 && s.boots.Count >= 3 && s.extras.Count >= 3));
    T("look: styles are named once each",
        L.styles.Select(s => s.name).Distinct(StringComparer.OrdinalIgnoreCase).Count() == L.styles.Count);

    // The Calling→style map is the one place two data files have to agree. A Calling missing from
    // it dresses out of the whole wardrobe (harmless); a style named there that does not exist is
    // a typo that silently narrows the draw, which is exactly the kind of thing nobody sees.
    var styleNames = new HashSet<string>(L.styles.Select(s => s.name));
    foreach (var (cal, prefs) in L.callingStyles)
    {
        T($"look: [{cal}] names only real styles", prefs.All(styleNames.Contains));
        T($"look: [{cal}] is a real Calling", cg.callings.Any(c => c.name == cal));
    }
    foreach (var c in cg.callings)
        T($"look: the {c.name} has a way of dressing", L.callingStyles.ContainsKey(c.name));

    // A roll fills every part of a description. Marks are deliberately not always drawn, and
    // whiskers only for one gender, so those two are excluded from the "always filled" sweep and
    // proved separately below.
    for (int i = 0; i < 200; i++)
    {
        var cal = cg.callings[Rules.Rng.Next(cg.callings.Count)].name;
        var lk = Look.Roll(i % 2 == 0 ? "Woman" : "Man", cal);
        if (!lk.Any || string.IsNullOrWhiteSpace(lk.People) || string.IsNullOrWhiteSpace(lk.Complexion)
            || string.IsNullOrWhiteSpace(lk.Hair) || string.IsNullOrWhiteSpace(lk.Eyes)
            || string.IsNullOrWhiteSpace(lk.Face) || string.IsNullOrWhiteSpace(lk.Bearing)
            || string.IsNullOrWhiteSpace(lk.Style) || string.IsNullOrWhiteSpace(lk.Hat)
            || string.IsNullOrWhiteSpace(lk.Boots) || string.IsNullOrWhiteSpace(lk.Detail))
        { T($"look: a roll for a {cal} fills every part of the description", false); break; }
        // Coherence is the whole point of drawing from ONE style: every garment must come out of
        // the wardrobe the style names, or the outfit is a shuffle wearing a label.
        var st = L.styles.First(s => s.name == lk.Style);
        if (!st.hats.Contains(lk.Hat) || !st.coats.Contains(lk.Coat) || !st.shirts.Contains(lk.Shirt)
            || !st.legs.Contains(lk.Legs) || !st.boots.Contains(lk.Boots))
        { T($"look: every garment comes out of the one style ({lk.Style})", false); break; }
        // …and colouring out of the one people, for the same reason.
        var pp = L.peoples.First(p => p.name == lk.People);
        if (!pp.complexions.Contains(lk.Complexion) || !pp.eyes.Contains(lk.Eyes)
            || !pp.hair.Any(h => lk.Hair.StartsWith(h, StringComparison.Ordinal)))
        { T($"look: complexion, hair and eyes come out of the one people ({lk.People})", false); break; }
    }
    T("look: 200 rolls are complete, coherently dressed and coherently coloured", true);

    // The Calling steers the wardrobe without owning it — a Preacher usually preaches in black,
    // and once in a while turns up in somebody's cavalry coat. Both halves are asserted, because
    // a bug in either direction (never steering, or never straying) reads as working.
    {
        var preacher = Enumerable.Range(0, 400).Select(_ => Look.Roll("Man", "Preacher").Style).ToList();
        var own = new HashSet<string>(L.callingStyles["Preacher"]);
        int inTrade = preacher.Count(own.Contains);
        T("look: a Calling mostly dresses as its Calling", inTrade > 260);
        T("look: and sometimes does not", inTrade < 400);
        T("look: an unknown Calling still gets dressed",
            Look.Roll("Woman", "Snake Charmer") is { Style.Length: > 0, Boots.Length: > 0 });
        T("look: so does no Calling at all", Look.Roll(null, null) is { Any: true });
    }

    // Whiskers are offered to one gender and not drawn for the others. This is a convention of the
    // period's own descriptions, not a rule about anybody — which is why every field is editable —
    // but the draw must at least be consistent with itself.
    {
        var whisk = new HashSet<string>(L.facialHair);
        bool Bearded(SoulLook lk) => whisk.Any(w => (lk.Face ?? "").EndsWith(w, StringComparison.Ordinal));
        int men = Enumerable.Range(0, 200).Count(_ => Bearded(Look.Roll("Man", "Drifter")));
        int others = Enumerable.Range(0, 200).Count(_ => Bearded(Look.Roll("Two-Spirit", "Drifter")));
        T("look: whiskers are drawn for a man", men > 150);
        T("look: and not drawn uninvited for anybody else", others == 0);
    }

    // Marks land on some souls and not others. A generator that marked everybody would make the
    // scarred ones ordinary, which is the opposite of what a scar is for.
    {
        int marked = Enumerable.Range(0, 400).Count(_ => !string.IsNullOrWhiteSpace(Look.Roll("Woman", "Gunhand").Marks));
        T("look: marks are drawn for some souls", marked > 80);
        T("look: and not for most", marked < 320);
    }

    // Depth, the way it actually matters: a table meets a lot of people over a campaign.
    {
        var faces = new HashSet<string>();
        for (int i = 0; i < 500; i++) faces.Add(Look.Roll("Woman", "Gambler").AtAGlance);
        T("look: 500 draws give 500 distinct descriptions", faces.Count > 480);
    }

    // It rides in the sheet, which is what puts it in session.json and on the printed PDF.
    {
        var made = CharGen.Generate(3, false, "Sawbones");
        T("look: a generated soul comes with one", made.Look is { Any: true });
        var round = System.Text.Json.JsonSerializer.Deserialize<CharacterSheet>(
            System.Text.Json.JsonSerializer.Serialize(made));
        T("look: it survives save and load", round.Look.Style == made.Look.Style && round.Look.Detail == made.Look.Detail);
        T("look: and it is printed on the sheet", CharGen.Render(made).Contains("APPEARANCE"));

        // A sheet from before any of this existed must read as a soul nobody has described, not as
        // a crash. This is the shape every consumer guards on.
        var older = System.Text.Json.JsonSerializer.Deserialize<CharacterSheet>(
            System.Text.Json.JsonSerializer.Serialize(made).Replace("\"Look\":", "\"LookWas\":"));
        T("look: a sheet saved before it loads with none, not a crash", older.Look == null);
        T("look: and prints without the heading", !CharGen.Render(older).Contains("APPEARANCE"));
        T("look: an emptied one is not Any", new SoulLook().Any == false);
        T("look: and its lines come back empty rather than as separators", new SoulLook().BodyLine == "");
    }

    // ---- the name and the people are ONE decision ----
    // The first soul this generator ever put on screen was "Rafferty Luján, Chinese, out of
    // Guangdong": chargen.json drew a whole name on a bare 12% roll answerable to nothing, and
    // appearance.json drew a people answerable to nothing else. Neither was wrong on its own.
    // Now the look is drawn first and the name follows it, and this is what holds that.
    {
        var owning = Look.D.peoples.Where(p => !string.IsNullOrWhiteSpace(p.namesFrom)).ToList();
        T("names: at least one people draws its names whole", owning.Count >= 1);
        var wholeNames = new HashSet<string>(CharGen.Flavor("fullNamesWomen").Concat(CharGen.Flavor("fullNamesMen")));

        int checkedSouls = 0, wrong = 0, fromOwning = 0;
        for (int i = 0; i < 600; i++)
        {
            var made = CharGen.Generate(1, false);
            checkedSouls++;
            bool ownsNames = owning.Any(p => p.name == made.Look.People);
            if (ownsNames) fromOwning++;
            // A whole name and a people that owns one must go together, both ways round.
            if (ownsNames != wholeNames.Contains(made.Name)) wrong++;
        }
        T($"names: all {checkedSouls} generated souls are named as their people are named", wrong == 0);
        T("names: and the peoples that own their names do come up", fromOwning > 5);

        // A soul given a name keeps it, and is not handed a people that would contradict it.
        var cal2 = CharGen.D.callings[0];
        var org2 = CharGen.D.origins.First(o => !(cal2.group == "Faith" && o.notFaith));
        for (int i = 0; i < 120; i++)
        {
            var sp = new CharGen.AssembleSpec
            { Level = 1, Calling = cal2.name, Origin = org2.name, Name = "Wren Ashby", Gender = "Woman" };
            foreach (var a in new[] { "STR", "DEX", "CON", "WIT", "RES", "PRE" }) sp.PreGiftScores[a] = 12;
            var b = CharGen.Assemble(sp);
            if (b.Name != "Wren Ashby" || owning.Any(p => p.name == b.Look.People))
            { T("names: a soul given a name is never described as a people whose names come whole", false); break; }
        }
        T("names: a given name survives, and nothing is drawn that contradicts it", true);

        // …and the redraw button obeys the same rule, since it changes a description on somebody
        // who is already called something.
        int strays = Enumerable.Range(0, 400)
            .Count(_ => owning.Any(p => p.name == Look.Roll("Man", "Drifter", nameIsFixed: true).People));
        T("names: a redrawn look never lands on a people whose names come whole", strays == 0);
        T("names: and an ordinary draw still reaches every other people",
            Enumerable.Range(0, 600).Select(_ => Look.Roll("Man", "Drifter", nameIsFixed: true).People)
                      .Distinct().Count() >= Look.D.peoples.Count - owning.Count - 4);
    }
}

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
        T($"cost: Sign [{sg.name}] has a rank on the spine", sg.rank >= 1 && sg.rank <= 8);
        if (pc.Spends) signsCosting++;
    }
    foreach (var mi in CharGen.D.miracles)
    {
        var pc = Rules.ParseCost(mi.cost);
        T($"cost: Miracle [{mi.name}] names its action", pc.Time.Length > 0);
        T($"cost: Miracle [{mi.name}] is not paid in Nerve", pc.Nerve == 0);
        T($"cost: Miracle [{mi.name}] has a rank on the spine", mi.rank >= 1 && mi.rank <= 8);
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

T("19 callings", cg.callings.Count == 19);
T("16 origins", cg.origins.Count == 16);

// ---- the Perks (v1.50.0) ----------------------------------------------------------------------
// One per Calling, printed above its level table and typed here so the picker can sell a Calling
// the way the page does. verify_rules.py holds the two word for word; these hold the shape the app
// relies on — that every Calling has one, that no two share a name, and that a Perk is always-on,
// which is what keeps it off the Tracker's rationed strip.
T("every Calling carries a Perk", cg.callings.All(c => c.perk != null
    && !string.IsNullOrWhiteSpace(c.perk.name) && !string.IsNullOrWhiteSpace(c.perk.desc)));
// Null-safe on purpose: a Calling with no Perk at all must report as ONE failure above, not take
// the remaining three down with a NullReferenceException and hide whatever else is wrong.
T("Perk names are unique across the nineteen",
    cg.callings.Select(c => c.perk?.name).Distinct().Count() == cg.callings.Count);
T("no Perk repeats the name of one of its Calling's own features", cg.callings.All(c =>
    c.perk?.name == null || !c.rows.SelectMany(r => r.features).Contains(c.perk.name)));
T("no Perk is rationed or tallied — it would want a card nothing can spend", cg.callings.All(c =>
    c.perk?.desc == null
    || (!CharGen.ReadLimit(c.perk.desc).Any && !CharGen.ReadTally(c.perk.desc).Any)));

// ---- the fight ledger (B5) ---------------------------------------------------------------
// Every Calling states what it does in a round and what it pays to be that. The Perk sells the
// Calling; the ledger is the half that has to stay honest, so what is asserted here is mostly
// that the unflattering half is really there and really unflattering.
T("every Calling carries a fight ledger", cg.callings.All(c => c.fight != null
    && !string.IsNullOrWhiteSpace(c.fight.brings) && !string.IsNullOrWhiteSpace(c.fight.costs)));
T("both halves of every ledger are a real sentence, not a label", cg.callings.All(c =>
    c.fight?.brings == null || c.fight.costs == null
    || (c.fight.brings.Length > 60 && c.fight.costs.Length > 40
        && c.fight.brings.TrimEnd().EndsWith('.') && c.fight.costs.TrimEnd().EndsWith('.'))));
T("no ledger repeats its own Perk back at the reader", cg.callings.All(c =>
    c.fight?.brings == null || c.perk?.desc == null || c.fight.brings != c.perk.desc));
// The measurement that produced these lines is in _combatlab/Roster.cs. Two of its findings are
// load-bearing and are pinned here so a later rewrite cannot quietly flatter them away: the
// Marshal is the Calling that does not top a damage table, and the Witch is the one that cannot
// shoot its way out. Both entries say so in the book.
T("the Marshal's ledger admits it will not top a damage table",
    (cg.callings.First(c => c.name == "Marshal").fight?.costs ?? "")
        .Contains("damage table", StringComparison.OrdinalIgnoreCase));
T("the Witch's ledger admits she cannot shoot her way out",
    (cg.callings.First(c => c.name == "Witch").fight?.costs ?? "")
        .Contains("shoot", StringComparison.OrdinalIgnoreCase));

// ---- the Engineer got a combat answer, and it is GRANT (B5) -------------------------------
// It was the only Calling in the book with no scaling answer in any column a round can be spent
// in and no workings to fall back on, because its signature feature was undefined prose. The
// frames fix that, and the clause that makes the Engineer itself rather than a lesser Prospector
// is that anybody it has shown a frame to may work the frame instead.
{
    var eng = cg.callings.First(c => c.name == "Engineer");
    var frames = eng.featureDescs.TryGetValue("A Contraption's Frames", out var f) ? f : "";
    T("the Engineer has a printed menu of frames", frames.Length > 400);
    T("eight of them, as the Powderman has eight Devices",
        new[] { "The Repeater", "The Bulwark", "The Winch", "The Governor",
                "The Alarum", "The Listening Horn", "The Diving Lamp", "The Heliograph" }
            .All(n => frames.Contains(n, StringComparison.Ordinal)));
    T("at least three of the frames reach a round",
        frames.Contains("1d10") && frames.Contains("hard cover") && frames.Contains("Prone"));
    T("a frame works in somebody else's hands — the Engineer's whole column",
        (eng.featureDescs.TryGetValue("The Contraption", out var con) ? con : "")
            .Contains("may work it instead of you", StringComparison.Ordinal));
    T("Powder & Fuse now gives the Engineer something to set",
        (eng.featureDescs.TryGetValue("Powder & Fuse", out var pf) ? pf : "")
            .Contains("prepare two charges", StringComparison.Ordinal));
}

// ---- a granted weapon is a weapon you can fire (v1.51.0) --------------------------------------
// A Calling's kit and an Origin's gear can GRANT a gun instead of selling one, and three lines do.
// The outfit step read those lines only to suppress the purchase, so the soul ended up with the
// rifle in Gear and NOTHING in WeaponsCarried: every Mountain Man ever generated, and anyone rolled
// with the Veteran's service carbine — the printed pregen Addison Quill among them. The Strike
// dialog offered them no weapon, and every balance sweep this project has run had the Mountain Man
// punching with his fists. Found by reading _combatlab's output, which is the only way it shows:
// nothing asserted that a generated soul was armed.
T("every granted weapon names one the arms table has", cg.grantedWeapons.All(g =>
    cg.weapons.Any(w => w.name == g.weapon)));
{
    // Any kit or gear line stating a damage die is granting a weapon and must be mapped.
    var die = new System.Text.RegularExpressions.Regex(@"\b\d*d\d+\b");
    var granting = cg.callings.SelectMany(c => c.coin.kit)
                     .Concat(cg.origins.SelectMany(o => o.gear ?? new List<string>()))
                     .Where(x => die.IsMatch(x)).ToList();
    T("every granted line maps to a weapon", granting.Count > 0 && granting.All(line =>
        cg.grantedWeapons.Any(g => line.Contains(g.match, StringComparison.OrdinalIgnoreCase))));

    bool allArmed = true; string bare = null;
    foreach (var c in cg.callings)
        foreach (int lvl in new[] { 1, 5, 10 })
            for (int t = 0; t < 12; t++)
            {
                Rules.Reseed(770000 + lvl * 100 + t);
                var sh = CharGen.Generate(lvl, rolled: false, fixedCalling: c.name);
                if ((sh.WeaponsCarried?.Count ?? 0) == 0) { allArmed = false; bare ??= $"{c.name} L{lvl}"; }
            }
    T("every Calling generates a soul carrying at least one weapon" + (bare == null ? "" : $" (bare: {bare})"),
      allArmed);

    Rules.Reseed(770001);
    var mm = CharGen.Generate(1, rolled: false, fixedCalling: "Mountain Man");
    T("the Mountain Man's Hawken reaches his weapon list",
      mm.WeaponsCarried.Any(w => w.StartsWith("Buffalo Rifle", StringComparison.Ordinal)));
}

// ---- what a Calling adds to a Strike (v1.51.0) ------------------------------------------------
// Six Callings scale their damage with a die step named in the level table. Read off the table, so
// the step a soul has reached is the step they get; offered rather than applied, because the
// condition is a fact about the field.
T("six Callings carry a scaling damage rider at 10th", cg.callings
    .Count(c => CharGen.StrikeRiders(c.name, 10).Count > 0) == 6);
T("a rider's dice grow with the level reached", CharGen.StrikeRiders("Bounty Hunter", 1)[0].Dice == "1d6"
    && CharGen.StrikeRiders("Bounty Hunter", 5)[0].Dice == "2d6"
    && CharGen.StrikeRiders("Bounty Hunter", 10)[0].Dice == "4d6");
T("a rider carries the book's own condition, not its payload",
    CharGen.StrikeRiders("Witch Hunter", 10)[0].When.StartsWith("Once per quarry", StringComparison.Ordinal));
T("no rider is reported before its Calling has reached it",
    CharGen.StrikeRiders("Preacher", 4).Count == 1 && CharGen.StrikeRiders("Preacher", 3).Count == 0);
T("every rider resolves to prose the book prints", cg.callings.All(c =>
    CharGen.StrikeRiders(c.name, 15).All(r => !string.IsNullOrWhiteSpace(r.Desc))));
T("17 skills", cg.skills.Count == 17);
// ---- the Signs (Ch. XIII): three lists, five Ranks, and a gate that actually holds ----
T("55 signs across three lists", cg.signs.Count == 55
    && cg.signs.All(s => s.list is "common" or "bargain" or "craft"));
T("every sign carries a Rank of 1-8", cg.signs.All(s => s.rank >= 1 && s.rank <= 8));
// Rank 8 is meant to be thin, and thin is a thing a test can hold. Three Signs, one per list.
T("Rank 8 holds three Signs, one to each list", cg.signs.Count(s => s.rank == 8) == 3
    && cg.signs.Where(s => s.rank == 8).Select(s => s.list).Distinct().Count() == 3);
T("every Rank is represented on every list", new[] { "common", "bargain", "craft" }
    .All(l => Enumerable.Range(1, 5).All(r => cg.signs.Any(s => s.list == l && s.rank == r))));
T("sign names are unique", cg.signs.Select(s => s.name).Distinct().Count() == cg.signs.Count);
T("the Craft is the Witch's alone", cg.callings
    .Where(c => c.signLists != null && c.signLists.Contains("craft"))
    .Select(c => c.name).SequenceEqual(new[] { "Witch" }));

// ---- the Witch's familiar (v1.45.0) -----------------------------------------------------------
// The books give the bound beast a standing +2, a touch-range delivery, shared senses and a
// Sickened when it dies; until v1.45.0 the app held the kind inside the shared CallingChoice
// string and none of the rest. These hold the three fields to the one fact they describe — the
// failure mode being a sheet whose familiar and whose bonus name two different animals.
{
    var witch = cg.callings.First(c => c.name == "Witch");
    T("the Witch is the only Calling with a Familiar choice", cg.callings
        .Where(c => c.choice != null && c.choice.label == "Familiar")
        .Select(c => c.name).SequenceEqual(new[] { "Witch" }));
    T("every familiar option has a boon of its own", witch.choice.options
        .Select(CharGen.FamiliarBoonFor).Distinct().Count() == witch.choice.options.Count);
    T("an unknown beast still gets a readable boon",
        CharGen.FamiliarBoonFor("a badger").Contains("befitting its nature")
        && CharGen.FamiliarBoonFor(null).Length > 0);

    for (int lv = 1; lv <= 10; lv++)
    {
        var s = CharGen.Generate(lv, false, "Witch");
        T($"a Witch at {lv} is bound to a beast", !string.IsNullOrEmpty(s.FamiliarKind));
        T($"the Witch at {lv} names one animal, not two",
            s.CallingChoice.EndsWith(s.FamiliarKind, StringComparison.Ordinal)
            && s.FamiliarBoon == CharGen.FamiliarBoonFor(s.FamiliarKind));
        T($"the familiar at {lv} starts alive", !s.FamiliarLost);
        T($"the sheet at {lv} says what the beast gives",
            CharGen.FamiliarLine(s).Contains(s.FamiliarKind)
            && CharGen.FamiliarLine(s).Contains("touch-range"));
        s.FamiliarLost = true;
        T($"a dead familiar at {lv} reads as Sickened until re-bound",
            CharGen.FamiliarLine(s).Contains("Sickened", StringComparison.Ordinal));
    }

    // Everybody else keeps the plain choice line and gains no familiar.
    foreach (var name in new[] { "Marshal", "Shaman", "Gunhand" })
    {
        var s = CharGen.Generate(3, false, name);
        T($"{name} has no familiar", s.FamiliarKind == null && CharGen.FamiliarLine(s) == null);
    }

    // ---- v1.48.0: the boon is APPLIED, the beast has a body, and the Craft does something ----
    // The whole of what v1.45.0 left undone. Each of these is a thing the sheet has printed since
    // then and nothing in the app has ever done.

    // The skill and the sentence come from one place, so the printed line cannot name a skill the
    // bonus lands on somewhere else. This is the fault the split was made to close.
    foreach (var kind in witch.choice.options)
    {
        string sk = CharGen.FamiliarSkillFor(kind);
        T($"[{kind}] the boon names the skill it lifts", sk != null
            && CharGen.FamiliarBoonFor(kind).Contains($"+{CharGen.FamiliarBoonSize} {sk}", StringComparison.Ordinal));
    }
    T("a beast nobody keyed lifts no named skill", CharGen.FamiliarSkillFor("a badger") == null);

    // The +2 reaches a roll. A live beast lifts its own skill and nothing else; a dead one lifts
    // nothing at all, which is the other half of what the book says the boon is worth.
    {
        var crow = new CharacterSheet
        { Calling = "Witch", Level = 3, FamiliarKind = "a crow", Scores = new() { ["RES"] = 10 } };
        int bare = CharGen.SkillBonus(new CharacterSheet { Level = 3, Scores = new() { ["RES"] = 10 } }, "Notice");
        T("a live crow is worth +2 Notice on the roll",
            CharGen.SkillBonus(crow, "Notice") == bare + CharGen.FamiliarBoonSize);
        T("initiative IS that Notice check, so the crow moves her place in the order",
            CharGen.InitiativeBonus(crow) == CharGen.SkillBonus(crow, "Notice"));
        T("the crow lifts nothing but Notice",
            CharGen.SkillBonus(crow, "Survival") == CharGen.SkillBonus(
                new CharacterSheet { Level = 3, Scores = new() { ["RES"] = 10 } }, "Survival"));
        crow.FamiliarLost = true;
        T("a dead crow is worth nothing", CharGen.SkillBonus(crow, "Notice") == bare);
        crow.FamiliarLost = false;
        crow.SkillRanks["Notice"] = 1;
        T("the boon rides on top of training, not instead of it",
            CharGen.SkillBonus(crow, "Notice") == 0 + crow.Level + 2 + CharGen.FamiliarBoonSize);
    }

    // The Craft's two levels are read off the level table, never typed. The Witch's Craft opens at
    // 3rd and deepens at 9th; hold the data to that, because these are the two numbers every
    // familiar rule below turns on.
    {
        var (at, greater) = CharGen.SubpathLevels("Witch");
        T("the Witch's Craft opens at 3rd and deepens at 9th", at == 3 && greater == 9);
        T("the Worldly master at 10th instead", CharGen.SubpathLevels("Gambler").Greater == 10);
        T("a Calling with no path reports no levels", CharGen.SubpathLevels("Nobody Here") == (0, 0));

        var s = new CharacterSheet
        { Calling = "Witch", FamiliarKind = "a cat", Subpath = "The Familiar-Bound", Level = 2 };
        T("below 3rd the Familiar-Bound is not yet taken", !CharGen.FamiliarBound(s));
        s.Level = 3;
        T("at 3rd it is", CharGen.FamiliarBound(s) && !CharGen.FamiliarBoundGreater(s));
        s.Level = 8;
        T("at 8th the greater boon is still shut", !CharGen.FamiliarBoundGreater(s));
        s.Level = 9;
        T("at 9th it opens", CharGen.FamiliarBoundGreater(s));
        s.Subpath = "The Greenwitch";
        T("another Craft is not the Familiar-Bound", !CharGen.FamiliarBound(s));
        T("neither is no familiar at all",
            !CharGen.FamiliarBound(new CharacterSheet
            { Calling = "Witch", Level = 9, Subpath = "The Familiar-Bound" }));
    }

    // The beast's own Blood — the app's default for a creature the book leaves to the table.
    // What is held here is the SHAPE of it: always smaller than hers, always at least the floor,
    // and always larger once she has taken the Craft that makes it hardy.
    {
        var plain = new CharacterSheet { Calling = "Witch", Level = 5, Blood = 30, Defense = 15, FamiliarKind = "a toad" };
        var bound = new CharacterSheet { Calling = "Witch", Level = 9, Blood = 30, Defense = 15,
                                         FamiliarKind = "a toad", Subpath = "The Familiar-Bound" };
        T("the beast has less to lose than its Witch", Rules.FamiliarBloodFor(plain) < plain.Blood);
        T("the Familiar-Bound beast is hardier", Rules.FamiliarBloodFor(bound) > Rules.FamiliarBloodFor(plain));
        T("and cleverer to hit", Rules.FamiliarDefenseFor(bound) > Rules.FamiliarDefenseFor(plain));
        T("a 1st-level beast is a creature, not a rounding error",
            Rules.FamiliarBloodFor(new CharacterSheet { Calling = "Witch", Level = 1, Blood = 9, FamiliarKind = "a cat" })
                >= Rules.FamiliarBloodFloor);
        T("no sheet is still a beast and not a crash",
            Rules.FamiliarBloodFor(null) >= Rules.FamiliarBloodFloor && Rules.FamiliarDefenseFor(null) > 0);
        T("its Defense is hers when the Craft is not taken", Rules.FamiliarDefenseFor(plain) == plain.Defense);
    }

    // The greater boon reads on the sheet, and the once-in-a-life carry reads as spent once it is.
    {
        var s = CharGen.Generate(9, false, "Witch");
        s.Subpath = "The Familiar-Bound";
        T("the greater boon is on the sheet's familiar line",
            CharGen.FamiliarLine(s).Contains("swap places", StringComparison.Ordinal));
        T("and the carry reads as still to come",
            CharGen.FamiliarLine(s).Contains("new dawn, once", StringComparison.Ordinal));
        s.FamiliarCarried = true;
        T("and as spent once it has been",
            CharGen.FamiliarLine(s).Contains("that was the once", StringComparison.Ordinal));
        // The one thing that must never happen: a boundary handing back a once-in-a-life thing.
        var p9 = new PartyMember { Calling = "Witch", Level = 9, Sheet = s };
        CharGen.RefreshFeatures(p9, FeatureCadence.Session);
        T("no boundary gives the spirit-carry back", s.FamiliarCarried);
    }

    // A row on the field belongs to its Witch by id, follows her through a rename, and is never
    // mistaken for a soul by anything that walks the posse.
    {
        var her = new PartyMember { Name = "Ruth" };
        var beast = new Combatant { Name = CharGen.FamiliarFieldName("Ruth", "a crow"), FamiliarOf = her.Id };
        T("the field names the beast for its Witch", beast.Name == "Ruth's crow");
        T("an article is not part of the name", !CharGen.FamiliarFieldName("Ruth", "the black snake").Contains(" the "));
        T("a familiar row knows whose it is", beast.IsFamiliar && beast.IsFamiliarOf(her));
        her.Name = "Ruth Colley";
        T("and follows her through a rename", beast.IsFamiliarOf(her));
        T("a familiar is never mistaken for a soul", !beast.IsSoul(her) && !beast.IsPC);
        T("a twin Witch does not own it", !beast.IsFamiliarOf(new PartyMember { Name = "Ruth Colley" }));
        T("an ordinary row is nobody's familiar",
            !new Combatant { Name = "a bandit" }.IsFamiliar);
        var reloaded = System.Text.Json.JsonSerializer.Deserialize<Combatant>(
            System.Text.Json.JsonSerializer.Serialize(beast));
        T("and the binding survives a saved session", reloaded.IsFamiliarOf(her));
    }
}
// B6. A ladder that stops short of the ceiling used to throw KeyNotFoundException out of
// LevelUp, in a Keeper's hands, mid-session. KnownAt holds the last rung now, so the fault would
// be silent instead of loud -- which is worse. This is the assertion that keeps it loud.
T("every known-at ladder covers every level to the ceiling", cg.callings.All(c =>
    (c.signsKnownAt == null || Enumerable.Range(1, Rules.MaxLevel)
        .All(l => c.signsKnownAt.ContainsKey(l.ToString())))
    && (c.miraclesKnownAt == null || Enumerable.Range(1, Rules.MaxLevel)
        .All(l => c.miraclesKnownAt.ContainsKey(l.ToString())))));
// Cole, 2026-08-30: every Calling gets a notable, significant thing at 15th. Nineteen rows, each
// naming at least one feature that is not an Edge and not a scaling step of something older.
T("every Calling reaches a named capstone at the ceiling", cg.callings.All(c =>
    c.rows.Where(r => r.level == Rules.MaxLevel).SelectMany(r => r.features)
     .Any(f => f != "Edge" && f != "Sign learned"
            && c.featureDescs != null && c.featureDescs.ContainsKey(f))));
T("every Calling's table runs the whole way", cg.callings.All(c =>
    c.rows.Select(r => r.level).OrderBy(l => l).SequenceEqual(Enumerable.Range(1, Rules.MaxLevel))));
// The printed table and Validate's count are two statements of the Edge rule, and until 2026-08-30
// nothing compared them: the tables named 3rd/7th/9th while Validate counted 1/3/5/7/9, so a player
// at 5th was never told about an Edge they already had. This is what stops that recurring.
T("every table prints an Edge on exactly the rungs that grant one", cg.callings.All(c =>
    c.rows.Where(r => r.features.Contains("Edge")).Select(r => r.level).OrderBy(l => l)
     .SequenceEqual(Enumerable.Range(1, Rules.MaxLevel).Where(Rules.IsEdgeLevel))));
// The two late Edges at 12th and 14th want something worth reaching for, so B6 gated thirty-one
// Edges behind 11th. EdgeEligible enforces reqLevel; this is what proves it does.
T("Edges gated at 11th are not offered before it", cg.edges.Concat(cg.callingEdges)
    .Count(e => e.reqLevel == 11) == 31);
{
    // Ask about the whole gate rather than one Edge: a generated soul may already OWN the Edge you
    // named, and EligibleEdges quite correctly stops offering what you have. The first draft of
    // this assertion did exactly that and failed for a reason that was not the reason.
    var late = cg.edges.Concat(cg.callingEdges).Where(e => e.reqLevel == 11).Select(e => e.name).ToHashSet();
    var young = CharGen.Generate(9, false, "Gunhand");
    var old = CharGen.Generate(Rules.MaxLevel, false, "Gunhand");
    T("no 11th-level Edge is offered to a 9th-level soul",
        !CharGen.EligibleEdges(young).Any(late.Contains));
    T("a soul at the ceiling is offered some of them",
        CharGen.EligibleEdges(old).Concat(old.Edges).Any(late.Contains));
    T("and never holds one it could not have earned", CharGen.Generate(9, false, "Gunhand")
        .Edges.Concat(young.BonusCombatEdges).All(e => !late.Contains(e)));
}

T("sign-workers and signLists are the same four callings", cg.callings
    .All(c => (c.signsKnownAt != null) == (c.signLists != null && c.signLists.Count > 0)));
T("Rank opens on every odd rung to the ceiling", Enumerable.Range(1, Rules.MaxLevel)
    .All(l => CharGen.SignRankAt(l) == (l + 1) / 2));
T("the top Rank is reached at the top level", CharGen.SignRankAt(Rules.MaxLevel) == 8
    && CharGen.SignRankAt(Rules.MaxLevel - 1) == 7);
// A Calling must never be asked to know more Signs than its Rank has actually opened.
T("no caster is starved of legal signs at any level", cg.callings
    .Where(c => c.signsKnownAt != null)
    .All(c => Enumerable.Range(1, Rules.MaxLevel)
        .All(l => CharGen.SignsFor(c, l).Count >= CharGen.KnownAt(c.signsKnownAt, l) + 1)));
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
T("61 miracles across seven lists", cg.miracles.Count == 61 && cg.miracles.All(m =>
    m.list is "blessing" or "liturgy" or "revival" or "spirits" or "mending" or "consecration"
           or "vigil"));

// ---- answering a working: the counter pair (v1.51.0) -----------------------------------------
// Two workings answer another before it lands, one on each side, and they only make sense as a
// pair: a Sign that fouls anything and a Miracle that refuses only the dark. If one of them ever
// goes missing the other becomes an unanswerable advantage, which is the exact thing the pair
// exists to prevent.
{
    var foul = cg.signs.FirstOrDefault(x => x.name == "Foul the Working");
    var stand = cg.miracles.FirstOrDefault(x => x.name == "Not While I Stand");
    T("the counter exists on both sides", foul != null && stand != null);
    T("both counters are Reactions", foul != null && stand != null
        && foul.cost.StartsWith("Reaction", StringComparison.Ordinal)
        && stand.cost.StartsWith("Reaction", StringComparison.Ordinal));
    T("both counters are reachable at the same Rank", foul?.rank == stand?.rank);
    T("the Sign counter is on the common list, the Miracle's on the blessing list",
        foul?.list == "common" && stand?.list == "blessing");
    // The asymmetry is the whole design and it is stated in the prose, so it is held there.
    T("the Sign counter answers anything worked",
        foul != null && foul.desc.Contains("a Sign or a Miracle", StringComparison.Ordinal));
    T("the Miracle counter refuses only the dark",
        stand != null && stand.desc.Contains("may not answer a Miracle", StringComparison.Ordinal));
    T("the Sign counter carries a Backlash clause and the Miracle names none",
        foul != null && stand != null
        && foul.desc.Contains("Backlash:", StringComparison.Ordinal)
        && !stand.desc.Contains("Backlash", StringComparison.Ordinal));
}
T("every miracle carries a Rank of 1-8", cg.miracles.All(m => m.rank >= 1 && m.rank <= 8));
T("every Rank is represented on every miracle list", new[] {
    "blessing", "liturgy", "revival", "spirits", "mending", "consecration", "vigil" }
    .All(l => Enumerable.Range(1, 5).All(rk => cg.miracles.Any(m => m.list == l && m.rank == rk))));
T("miracle names are unique", cg.miracles.Select(m => m.name).Distinct().Count() == cg.miracles.Count);
// All three Rank 8 Miracles are Common Blessings, so every Calling of Faith reaches the same
// three at 15th. That is a design decision from B6 and not an accident of the list.
T("Rank 8 holds three Miracles, all of them Common Blessings",
    cg.miracles.Count(m => m.rank == 8) == 3
    && cg.miracles.Where(m => m.rank == 8).All(m => m.list == "blessing"));
T("Signs and Miracles ride the one Rank spine", Enumerable.Range(1, Rules.MaxLevel)
    .All(l => CharGen.MiracleRankAt(l) == CharGen.SignRankAt(l)));
// Exactly the six Callings of Faith work Miracles, and none of them works a Sign.
T("the six faith callings work Miracles", cg.callings
    .Where(c => c.miracleLists != null && c.miracleLists.Count > 0)
    .Select(c => c.name).OrderBy(n => n)
    .SequenceEqual(new[] { "Medicine Man", "Padre", "Preacher", "Shaman", "Sister",
                           "Witch Hunter" }));
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
T($"every calling has {Rules.MaxLevel} table rows", cg.callings.All(c => c.rows.Count == Rules.MaxLevel
    && c.rows.Select(r => r.level).SequenceEqual(Enumerable.Range(1, Rules.MaxLevel))));
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

// ---- what an Origin is worth at the table (v1.49.0) ----
// Ch. IV gives all ten a boon and a burden and the app counted none of them. Both readers work
// off the book's own sentences, so what they must never do is INVENT: a reading that finds a
// ration where the book states none puts a counter on the strip that no rule backs.
foreach (var og in CharGen.D.origins)
{
    foreach (var f in CharGen.OriginFeatures(og.name))
    {
        T($"{og.name}: rationed boon '{CharGen.ShortFeatureName(f.Name)}' states its cadence",
            f.Limit.Any && f.Limit.Cadence != FeatureCadence.None);
        T($"{og.name}: its ration is keyed apart from any Calling feature", f.Name.StartsWith("Origin: "));
        T($"{og.name}: the card's sentence is the book's own",
            !string.IsNullOrWhiteSpace(f.Desc) && (og.boon + og.burden).Contains(f.Desc.Trim()));
    }
    foreach (var e in CharGen.OriginEdges(og.name))
    {
        T($"{og.name}: standing {e.Says} is signed and non-zero", e.Size != 0);
        T($"{og.name}: standing {e.Says} names what it applies to", !string.IsNullOrWhiteSpace(e.Applies));
        T($"{og.name}: standing {e.Says} carries the book's sentence",
            (og.boon + og.burden).Contains(e.Phrase.Trim()));
    }
}
// ---- the Returned: Hunger, the Shapes, and what the grave gave (v1.49.0) ----
{
    T("Ch. XII's Hunger ladder is six rungs", CharGen.D.hungerLadder.Count == CharGen.HungerLost);
    T("every Hunger rung says something", Enumerable.Range(0, CharGen.HungerLost + 1)
        .All(i => !string.IsNullOrWhiteSpace(CharGen.HungerSays(i))));
    T("four Shapes of Return, each whole", CharGen.ShapesOfReturn.Count == 4
        && CharGen.ShapesOfReturn.All(x => !string.IsNullOrWhiteSpace(x.name)
            && !string.IsNullOrWhiteSpace(x.hunger) && !string.IsNullOrWhiteSpace(x.feeding)
            && !string.IsNullOrWhiteSpace(x.gift)));
    // Mending is 1d6 per two levels and never less than one, so a 1st-level soul is not handed a
    // heal of zero dice — the failure mode a bare level/2 has at exactly the level most souls are.
    T("mend never rolls zero dice", Enumerable.Range(1, 10).All(l => CharGen.MendDice(l) >= 1));
    T("mend is 1d6 per two levels", CharGen.MendDice(2) == 1 && CharGen.MendDice(10) == 5);

    var ret = CharGen.Generate(3, false, null, CharGen.ReturnedOrigin);
    T("a generated Returned soul has a Shape the book prints",
        CharGen.ShapesOfReturn.Any(x => x.name == ret.Shape));
    T("a Returned soul begins quiet", ret.Hunger == 0);
    T("a Returned soul validates", CharGen.Validate(ret).Count == 0);

    // The whole engine in four lines: mending is the only way this soul heals, and it is the only
    // thing that moves them toward the ending. Nothing else in the app may hand the Hunger back.
    CharGen.TakeHunger(ret);
    T("mending takes a Hunger", ret.Hunger == 1);
    CharGen.Feed(ret);
    T("feeding gives one back", ret.Hunger == 0);
    CharGen.TakeHunger(ret, 99);
    T("Hunger stops at Consumed", ret.Hunger == CharGen.HungerLost);
    T("Consumed refuses to mend and says why", CharGen.WhyNotMend(ret) != null);
    CharGen.Feed(ret, 99);
    T("feeding cannot go below quiet", ret.Hunger == 0);

    // A boundary must never hand a Hunger back — the same guard the Hexer's Debts and the Witch's
    // rite carry, and for the same reason: a track that eases overnight says the cost was nothing.
    var boundary = CharGen.Generate(3, false, null, CharGen.ReturnedOrigin);
    CharGen.TakeHunger(boundary, 2);
    var pm = new PartyMember { Name = boundary.Name, Calling = boundary.Calling, Level = 3, Sheet = boundary };
    CharGen.RefreshFeatures(pm, FeatureCadence.Session);
    T("no boundary hands a Hunger back", boundary.Hunger == 2);

    // What the grave gave has to REACH A ROLL, or it is a decoration on a sheet — the v1.48.0
    // lesson, run on a second subsystem.
    var living = CharGen.Generate(3, false, null, "The Scout");
    T("the Returned get +2 on Dread and the living get nothing",
        CharGen.DreadBonus(ret) == 2 && CharGen.DreadBonus(living) == 0);
    var numb = CharGen.Generate(3, false, null, CharGen.ReturnedOrigin);
    CharGen.TakeHunger(numb, CharGen.HungerNumb);
    T("at Hunger 3 the fear stops landing", CharGen.NumbToDread(numb) && !CharGen.NumbToDread(living));
    // Forced die 1 against DC 25 is a critical failure at any Will: Nerve is spared and the
    // Frightened and the Affliction are NOT, because those are done TO a soul.
    var dr = Horror.DreadCheck(0, 25, forcedDie: 1, who: numb);
    T("a numb soul loses no Nerve but is still Frightened and still scarred",
        dr.NerveLost == 0 && dr.Numb && dr.Frightened && dr.Affliction);
    var feels = Horror.DreadCheck(0, 25, forcedDie: 1, who: living);
    T("a living soul still pays the Nerve", feels.NerveLost > 0 && !feels.Numb);

    // Nobody else may carry either fact, and Validate is what says so.
    var trespass = CharGen.Generate(3, false, null, "The Laborer");
    trespass.Hunger = 2;
    T("Validate refuses a Hunger on a living soul", CharGen.Validate(trespass).Count > 0);
    var noshape = CharGen.Generate(3, false, null, CharGen.ReturnedOrigin);
    noshape.Shape = "The Unwritten";
    T("Validate refuses a Shape the book does not print", CharGen.Validate(noshape).Count > 0);
}

// The Veteran is the reason the reader splits on sentences at all: its boon states TWO rationed
// things in one breath, and a reader handed the whole paragraph answers with the first only.
T("The Veteran's boon yields both of its rations",
    CharGen.OriginFeatures("The Veteran").Count(f => f.Name.StartsWith("Origin: The Veteran")) >= 2);
// The Scout is the matching case on the other reader: a boon and a burden touching the same skill
// in opposite directions, which is precisely why these are offered and never auto-applied.
{
    var sc = CharGen.OriginEdges("The Scout");
    T("The Scout carries both a + and a − on Notice",
        sc.Any(e => e.Size > 0 && e.Applies.Contains("Notice")) &&
        sc.Any(e => e.Size < 0 && e.Applies.Contains("Notice")));
}
// Nothing may be read off an Origin that has no such sentence: the Freed states no ration at all,
// and a counter appearing on that card would be the app inventing a rule.
T("An Origin that rations nothing gets no ration card", CharGen.OriginFeatures("The Freed").Count == 0);
if (Environment.GetEnvironmentVariable("GK_ORIGIN_PROBE") == "1")
    foreach (var og in CharGen.D.origins)
    {
        Console.WriteLine($"\n{og.name}");
        foreach (var f in CharGen.OriginFeatures(og.name))
            Console.WriteLine($"    ration  {CharGen.ShortFeatureName(f.Name),-22} {f.Limit.Says(null)}");
        foreach (var e in CharGen.OriginEdges(og.name))
            Console.WriteLine($"    {(e.IsBoon ? "boon  " : "burden")}  {e.Says}");
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
        for (int target = 2; target <= Rules.MaxLevel; target++)
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
        var capLv = CharGen.Validate(capped);
        T($"levelup ceiling no-op: {c.name}" + (capLv.Count > 0 ? " — " + capLv[0] : ""),
            capped.Level == Rules.MaxLevel && capLv.Count == 0);
        T($"levelup preview at ceiling: {c.name}", CharGen.PreviewLevelUp(s).AtCeiling);
    }

// under a fixed seed the whole grow-up is reproducible (Generate + every LevelUp to the ceiling)
{
    string Grow(int seed)
    {
        Rules.Reseed(seed);
        var s = CharGen.Generate(1, false, "Marshal");
        for (int L = 2; L <= Rules.MaxLevel; L++) s = CharGen.LevelUp(s, new CharGen.LevelUpChoices());
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
    // Was >= 150, which the old advTitleA x advTitleB could just about clear: 20 x 20 = 400 combos
    // in ONE shape, so 400 rolls collided constantly and every title read "The <adj> <noun>".
    // Namer draws 21 grammars off pools an order of magnitude wider; below ~350 means it regressed.
    T($"adventure: titles vary ({titles.Count} in 400)", titles.Count >= 350);
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

// ---- the naming stock and Namer (2026-08-09) ----
// Written for a fault that shipped: Modules I and III went out as "The Salt at Coffin Wells" and
// "The Reckoning of the Wells". Two separate defences are asserted here because they fail
// separately — BREADTH across seeds, MEMORY within one.
{
    var stock = Names.Data;

    // Breadth is the only thing that reaches across seeds: no amount of within-run memory stops
    // two Keepers on two evenings drawing the same word. The old town stock was 16 x 16 = 256 and
    // the birthday bound puts the first repeat at roughly twenty draws, which is one campaign.
    foreach (var (slot, floor) in new[]
    {
        ("adj", 50), ("noun", 60), ("actor", 35), ("actorp", 25), ("verb3", 30),
        ("verb", 24), ("verbing", 22), ("plural", 25), ("surname", 45), ("given", 45),
        ("titlefirst", 55), ("motion3", 12), ("hardnoun", 30), ("bodynoun", 22),
    })
        T($"names: {slot} pool is broad enough ({Names.PoolSize(slot)} >= {floor})",
            Names.PoolSize(slot) >= floor);
    T($"names: town stock multiplies out ({stock.TownFirst.Count} x {stock.TownSecond.Count})",
        stock.TownFirst.Count * stock.TownSecond.Count >= 4000);
    T($"names: there are many title shapes, not one ({stock.TitleForms.Count})",
        stock.TitleForms.Count >= 15);
    T("names: every ground has its own geography words",
        stock.TitleGeo.Count == MapGen.Terrains.Length && stock.TitleGeo.TrueForAll(g => g.Count >= 8));

    // Every slot a template writes must resolve, or a title ships with a literal "{actor}" in it.
    foreach (var f in stock.TitleForms)
    {
        var filled = new Namer(4242).Fill(stock, f.Pattern);
        T($"names: form '{f.Id}' fills every slot", !filled.Contains('{') && filled.Length > 3);
    }

    // Determinism. Same seed, same names — this is the whole reason the class exists, and it is
    // what makes a rolled adventure something a Keeper can come back to.
    string Twelve(int seed)
    {
        var n = Names.For(seed);
        return string.Join("|", Enumerable.Range(0, 12).Select(_ => n.Title(stock)));
    }
    T("names: a seed reproduces its titles exactly", Twelve(31337) == Twelve(31337));
    T("names: different seeds tell different stories", Twelve(31337) != Twelve(31338));

    // Reserve must not consume randomness. If it did, excluding a word would shift every draw
    // after it and "the same seed" would stop meaning anything the moment a caller reserved.
    var plain = Names.For(909);
    var reserved = Names.For(909);
    reserved.Reserve("Nothing In Any Pool Whatsoever Zzz");
    T("names: Reserve costs no randomness",
        plain.Title(stock) == reserved.Title(stock));

    // Memory within one run: 12 titles off one namer must share no distinctive word and no shape.
    {
        var namer = Names.For(20260809);
        var words = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        bool wordClash = false;
        for (int i = 0; i < 12; i++)
            foreach (var w in Namer.Distinctive(namer.Title(stock)))
                if (!words.Add(w)) wordClash = true;
        T("names: one namer never spends a distinctive word twice", !wordClash);
    }

    // One survey names a town, a cartouche and every landmark. What the namer DRAWS may not echo.
    //
    // Scoped to drawn words on purpose. The first cut of this asserted that no word repeated
    // anywhere on the sheet and failed on seed 5150 — because the open range offers "Line Camp"
    // and "Cold Camp", and "Signal Hill" beside "Boot Hill". Those are hand-authored landmark
    // nouns that share a generic word the way real country does, and a surveyor drawing two camps
    // has not made a mistake. The Namer's promise is about what it hands out, not about the
    // vocabulary it was handed.
    // A second cut failed too, and taught the rest of the lesson: a word being IN a draw pool does
    // not mean the namer drew it. "Hanging Tree" and "Burned Homestead" are authored nouns that
    // happen to contain LmAdj words; "Well" is an authored noun and also a TownSecond word. Only
    // provenance settles it, so the assertions below are scoped to text the namer alone can emit —
    // the cartouche against the town, and the owner surnames, which appear in no authored noun.
    {
        bool titleEchoesTown = false, ownerTwice = false;
        var owners = new HashSet<string>(Names.Data.LmOwner, StringComparer.OrdinalIgnoreCase);
        for (int s = 1; s <= 60; s++)
        {
            var m = MapGen.Generate(new MapSpec { Seed = s * 5150, Landmarks = 8 });
            var townWords = new HashSet<string>(Namer.Distinctive(m.Town?.Name ?? ""), StringComparer.OrdinalIgnoreCase);
            if (Namer.Distinctive(m.Title).Any(townWords.Contains)) titleEchoesTown = true;

            var seenOwner = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var l in m.Landmarks)
                foreach (var w in Namer.Distinctive(l.Name))
                    if (owners.Contains(w) && !seenOwner.Add(w)) ownerTwice = true;
        }
        T("names: a map's cartouche never echoes its own town (60 surveys)", !titleEchoesTown);
        T("names: no two landmarks on a sheet share an owner (60 surveys)", !ownerTwice);
    }

    // A seeded adventure is reproducible whole — words AND monster AND clock.
    {
        var a1 = Db.RollAdventure(6, 777);
        var a2 = Db.RollAdventure(6, 777);
        T("adventure: a seed reproduces the whole night",
            a1.Title == a2.Title && a1.Trouble == a2.Trouble && a1.NpcName == a2.NpcName
            && a1.TownName == a2.TownName && a1.ClockSegments == a2.ClockSegments);
        T("adventure: it reports the seed that made it", a1.Seed == 777);
        T("adventure: an unseeded roll still reports a usable seed", Db.RollAdventure(6).Seed != 0);

        // The town comes off the book's own Ch. XII tables and is reserved into the namer, so the
        // title cannot echo it — "The Salt at Coffin Wells" beside "the Wells" is the shipped fault.
        bool titleEchoesTown = false;
        for (int s = 1; s <= 200; s++)
        {
            var a = Db.RollAdventure(6, s * 104729);
            var townWords = new HashSet<string>(Namer.Distinctive(a.TownName), StringComparer.OrdinalIgnoreCase);
            if (Namer.Distinctive(a.Title).Any(townWords.Contains)) { titleEchoesTown = true; break; }
        }
        T("adventure: a title never echoes its own town (200 seeds)", !titleEchoesTown);
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

// ---- The daybook: what the app did, for the failure that never throws ----
// Held to the end of the run on purpose. It is the one thing here with process-wide state, and
// every sweep above calls the paths it listens to — so it opens, proves itself, and closes again
// with nothing left behind.
T("daybook: closed until somebody opens it", !Daybook.On && Daybook.Count == 0);
Rules.RollExpr("2d6+3");
T("daybook: a closed daybook records nothing", Daybook.Count == 0);

Daybook.Open();
T("daybook: opens empty", Daybook.On && Daybook.Count == 0);
Rules.RollExpr("2d6+3");
T("daybook: a roll leaves one entry", Daybook.Count == 1);
T("daybook: the entry carries the expression", Daybook.Dump().Contains("2d6+3"));
Rules.FourDegrees(10, 5, 13);
T("daybook: a check leaves one too", Daybook.Count == 2);
T("daybook: the check names its degree", Daybook.Dump().Contains("Success"));

// The cap is the whole reason this is safe to leave recording all evening.
for (int i = 0; i < Daybook.Cap + 50; i++) Daybook.Note("test", $"entry {i}");
string dbDump = Daybook.Dump();
T("daybook: the ring holds at its cap", Daybook.Count == Daybook.Cap);
T("daybook: the dump admits what it dropped", dbDump.Contains("older dropped"));
T("daybook: the oldest went and the newest stayed",
    !dbDump.Contains("entry 49" + Environment.NewLine)
    && dbDump.Contains($"entry {Daybook.Cap + 49}" + Environment.NewLine));

string dbPath = Path.Combine(Path.GetTempPath(), "gritkeeper-daybook-smoke.txt");
T("daybook: writes itself out",
    Daybook.Save(dbPath) && File.ReadAllText(dbPath).Contains($"entry {Daybook.Cap + 49}"));
// A diagnostic that throws is worse than no diagnostic — an impossible path must come back false,
// not come back as the exception the Keeper was trying to report.
T("daybook: an unwritable path fails soft",
    !Daybook.Save(Path.Combine(dbPath, "no", "such", "place.txt")));
try { File.Delete(dbPath); } catch { }

Daybook.Close();
T("daybook: closing forgets everything", !Daybook.On && Daybook.Count == 0);
T("daybook: and says so rather than reading as an empty night", Daybook.Dump().Contains("not recording"));

// ---- what a Calling's features let you do, and how often (v1.42.0) ----
// The limit is READ OUT OF THE BOOK'S SENTENCE, never typed beside it, so these tests are really
// two questions: does the reader understand the sentences the book uses today, and has the book
// started using a sentence it does not understand? The second is the one that bites — a new
// Calling written with "no more than twice in a scene" would sail past a reader that only knows
// "twice per scene", and the feature would quietly become unlimited at every table.
{
    var callings = CharGen.D.callings;

    // --- the reader agrees with a plain scan of the prose ---
    var broad = new System.Text.RegularExpressions.Regex(
        @"\b(once|twice|three times|four times|five times|\d+ times|a number of times) per "
        + @"(turn|round|scene|fight|encounter|session|quarry|wound|patient|target)\b",
        System.Text.RegularExpressions.RegexOptions.IgnoreCase);
    int stated = 0, read = 0;
    foreach (var cal in callings)
        foreach (var kv in cal.featureDescs)
        {
            bool says = broad.IsMatch(kv.Value);
            var lim = CharGen.ReadLimit(kv.Value);
            if (says) stated++;
            if (says && lim.Any) read++;
            T($"limit read where the book states one: {cal.name}/{kv.Key}", !says || lim.Any);
            // and nothing invented where the book states nothing
            T($"no limit invented: {cal.name}/{kv.Key}",
              says || !lim.Any || lim.Cadence == FeatureCadence.Dawn);
        }
    T("every stated limit is read", stated == read);
    // 36 before B6. Fifty-seven new feature write-ups arrived with the levels above ten, and
    // every fifteenth-level capstone is once a session by design, so the number had to move.
    T($"the book still states as many limits as it did ({stated})", stated == 71);

    // --- the shapes the book actually uses ---
    CgCalling Cal(string n) => callings.First(c => c.name == n);
    FeatureLimit Lim(string cal, string feat) => CharGen.LimitOf(Cal(cal), feat);

    var command = Lim("Marshal", "Command");
    T("Command is per scene",            command.Cadence == FeatureCadence.Scene);
    T("Command counts off PRE",          command.Ability == "PRE");
    T("Command has a floor of 1",        command.Min == 1);
    T("Command is not half-level",       !command.HalfLevel);

    var powder = Lim("Prospector", "Powderman");
    T("Powderman is prepared each dawn", powder.Cadence == FeatureCadence.Dawn);
    T("Powderman counts off WIT",        powder.Ability == "WIT");
    T("Powderman adds half a level",     powder.HalfLevel);
    T("Powderman floors at 2",           powder.Min == 2);

    T("Tonics are prepared each dawn",   Lim("Sawbones", "Tonics").Cadence == FeatureCadence.Dawn);
    T("Bushwhack is once a turn",        Lim("Bounty Hunter", "Bushwhack").Cadence == FeatureCadence.Turn);
    T("Stack the Odds is once a round",  Lim("Gambler", "Stack the Odds").Cadence == FeatureCadence.Round);
    T("Cold Deck is once a scene",       Lim("Gambler", "Cold Deck").Cadence == FeatureCadence.Scene);
    T("a fight is a scene",              Lim("Gunhand", "Lightning Hand").Cadence == FeatureCadence.Scene);
    T("Last Stand is once a session",    Lim("Marshal", "Last Stand").Cadence == FeatureCadence.Session);
    T("Last Stand is one use",           Lim("Marshal", "Last Stand").Uses == 1);

    // --- the two the fiction returns rather than a clock ---
    var judgment = Lim("Witch Hunter", "Judgment");
    T("Judgment is a trigger, not a clock", judgment.Cadence == FeatureCadence.Trigger);
    T("Judgment says what returns it",      judgment.Says(null) == "once per quarry");
    T("Field Surgery is per wound",         Lim("Sawbones", "Field Surgery").Says(null) == "once per wound");
    T("a scene does not return a trigger",  FeatureCadence.Trigger > FeatureCadence.Scene);
    T("a new session does",                 FeatureCadence.Trigger < FeatureCadence.Session);

    // --- the level table's name and the prose's heading are reconciled in ONE place ---
    T("a die in the column is not a new feature",
      CharGen.FeatureKey(Cal("Witch Hunter"), "Judgment 3d8") == "Judgment");
    T("a plus and a die, likewise",
      CharGen.FeatureKey(Cal("Mountain Man"), "Dead Aim +1d6") == "Dead Aim");
    T("three features may share one heading",
      CharGen.FeatureKey(Cal("Drifter"), "Vanish") == "Ghost / Uncanny Step / Vanish");
    T("and the Sawbones' pair does",
      CharGen.FeatureKey(Cal("Sawbones"), "Precise Strike 2d6") == "Anatomist / Precise Strike");

    // --- and nothing that merely happens every round is mistaken for something you press ---
    T("Sanctuary is not a counter",      !Lim("Padre", "Sanctuary").Any);
    T("the Rite is not a counter",       !Lim("Padre", "Rite of Exorcism").Any);
    T("the Hawken is not a counter",     !Lim("Mountain Man", "Hawken Rifle").Any);
    T("Cardsharp is not a counter",      !Lim("Gambler", "Cardsharp").Any);

    // --- the sentence rides along, because a Keeper deserves the rule and not a code ---
    T("the limit carries the book's sentence",
      Lim("Marshal", "Last Stand").Phrase.StartsWith("Once per session, when an ally within sight"));

    // --- how many uses a given soul gets ---
    var marshal = CharGen.Generate(6, false, "Marshal");
    int pre = CharGen.Mod(marshal.Scores["PRE"]);
    T("Command's uses follow PRE",   command.UsesFor(marshal) == Math.Max(1, pre));
    T("a floor is never zero uses",  command.UsesFor(null) >= 1);
    T("once per session reads as one use", Lim("Marshal", "Last Stand").UsesFor(marshal) == 1);
    T("Says is the book's cadence",  Lim("Marshal", "Last Stand").Says(marshal) == "once per session");

    // --- the strip's own list ---
    var gambler = CharGen.FeaturesAt("Gambler", 10);
    T("a 10th-level Gambler has features",   gambler.Count >= 8);
    T("the strip leaves out the Edge slots", gambler.All(f => f.Name != "Edge"));
    T("the strip knows Cold Deck's limit",
      gambler.Any(f => f.Name == "Cold Deck" && f.Limit.Cadence == FeatureCadence.Scene));
    T("the strip carries the whole rule",
      gambler.All(f => f.Desc == null || f.Desc.Length > 20));
    var green = CharGen.FeaturesAt("Gambler", 1);
    T("a green Gambler has fewer",           green.Count < gambler.Count);
    T("an unknown Calling is empty, not a throw", CharGen.FeaturesAt("Rustler", 5).Count == 0);

    // --- the 3rd-level path, which no featureDescs entry covers ---
    var unchosen = CharGen.FeaturesAt("Gambler", 10).First(f => f.Name == "Games of the Gambler");
    T("an unchosen path offers the list", unchosen.Desc.Contains("The Duelist"));
    T("and claims no limit yet",          !unchosen.Limit.Any);
    var duelist = CharGen.FeaturesAt("Gambler", 10, "The Duelist");
    T("a chosen path is named",     duelist.Any(f => f.Name == "Games of the Gambler: The Duelist"));
    var chosen = duelist.First(f => f.Name == "Games of the Gambler: The Duelist");
    T("the 3rd-level boon stops at the mastery", !chosen.Desc.Contains("Mastery (10th)"));
    var mast = duelist.First(f => f.Name.EndsWith("— greater"));
    T("the mastery half is the mastery",  mast.Desc.StartsWith("Mastery (10th)"));
    T("and carries its own limit",        mast.Limit.Cadence == FeatureCadence.Scene);
    T("an Old Dark path deepens at 9th",
      CharGen.FeaturesAt("Witch", 10, "The Familiar-Bound").First(f => f.Name.EndsWith("— greater"))
             .Desc.StartsWith("Greater (9th)"));
    T("a 9th-level path is not offered at 8th",
      !CharGen.FeaturesAt("Witch", 8, "The Familiar-Bound").Any(f => f.Name.EndsWith("— greater")));

    // The Dark Cultist prints Devotion twice: the pool at 1st, the path at 3rd. Both must survive,
    // and the pool must keep its own rules rather than inheriting the path's list of options.
    var cultist = CharGen.FeaturesAt("Dark Cultist", 9, "The Whisperer");
    T("the pool keeps its own name",  cultist.Any(f => f.Name == "Devotion"));
    T("and its own rules",            cultist.First(f => f.Name == "Devotion").Desc.Contains("pool"));
    T("the path is the path",         cultist.Any(f => f.Name == "Dark Cultist’s Devotions: The Whisperer"));
    T("and deepens at 9th",           cultist.Any(f => f.Name.EndsWith("— greater")));

    // --- the level table's names reconcile with the prose's headings ---
    foreach (var cal in callings)
        foreach (var f in CharGen.FeaturesAt(cal.name, 10))
            T($"every feature has its rule: {cal.name}/{f.Name}", f.Desc != null);
}

// ---- spending a rationed feature, and the boundaries that hand it back (v1.42.0) ----
// The counting is the whole point. A once-per-session feature that nobody counts is a feature the
// table argues about at exactly the moment it matters, and the answer four people give is four.
{
    // 10th level, because Last Stand is the Marshal’s capstone and the capstone is the
    // once-a-session feature this whole ledger exists for.
    var sheet = CharGen.Generate(10, false, "Marshal");
    var soul = new PartyMember { Name = "Coyle", Calling = "Marshal", Level = 10, Sheet = sheet };

    var ledger = CharGen.LedgerFor(soul);
    T("the Marshal's rationed features are found", ledger.Count >= 2);
    T("Last Stand is one of them", ledger.Any(r => r.Name == "Last Stand"));
    T("nothing starts spent", ledger.All(r => r.Left == r.Of));

    T("Last Stand can be spent",  CharGen.SpendFeature(soul, "Last Stand"));
    T("and then it is gone",      CharGen.LedgerFor(soul).First(r => r.Name == "Last Stand").Left == 0);
    T("and says why",             CharGen.WhyNotFeature(soul, "Last Stand").Contains("session"));
    T("and refuses a second",     !CharGen.SpendFeature(soul, "Last Stand"));
    T("a feature they lack is refused by name",
      CharGen.WhyNotFeature(soul, "Powderman").Contains("no feature"));

    // A scene does not return a session's one great moment. This is the check that matters:
    // getting it wrong in the generous direction is worse than not counting at all.
    T("a scene leaves it spent",  CharGen.RefreshFeatures(soul, FeatureCadence.Scene) == 0);
    T("still spent after the scene", CharGen.LedgerFor(soul).First(r => r.Name == "Last Stand").Left == 0);
    T("a long rest does not either", CharGen.RefreshFeatures(soul, FeatureCadence.Dawn) == 0);
    T("a new session does",       CharGen.RefreshFeatures(soul, FeatureCadence.Session) == 1);
    T("and it is back",           CharGen.LedgerFor(soul).First(r => r.Name == "Last Stand").Left == 1);

    // Command is counted off PRE, so it takes as many presses as the modifier allows and no more.
    var cmd = CharGen.LedgerFor(soul).FirstOrDefault(r => r.Name == "Command");
    if (cmd.Name != null)
    {
        int of = cmd.Of;
        for (int i = 0; i < of; i++) T($"Command press {i + 1} of {of}", CharGen.SpendFeature(soul, "Command"));
        T("and no more than the modifier allows", !CharGen.SpendFeature(soul, "Command"));
        T("a scene returns the scene's own",      CharGen.RefreshFeatures(soul, FeatureCadence.Scene) == 1);
        T("all of them at once",                  CharGen.LedgerFor(soul).First(r => r.Name == "Command").Left == of);
    }

    // Taking one back, for the press that was a mis-click
    CharGen.SpendFeature(soul, "Last Stand");
    T("a use can be handed back",  CharGen.UnspendFeature(soul, "Last Stand"));
    T("and the count agrees",      CharGen.LedgerFor(soul).First(r => r.Name == "Last Stand").Left == 1);
    T("but not below nothing",     !CharGen.UnspendFeature(soul, "Last Stand"));

    // The ledger is derived, so levelling changes what is on it rather than needing a top-up
    var green = new PartyMember { Name = "Green", Calling = "Marshal", Level = 1, Sheet = CharGen.Generate(1, false, "Marshal") };
    T("a 1st-level Marshal has no Last Stand", CharGen.LedgerFor(green).All(r => r.Name != "Last Stand"));

    // A hand-entered soul has no sheet at all and must still be readable rather than a throw
    var handmade = new PartyMember { Name = "Nobody", Calling = "Marshal", Level = 10 };
    T("a soul with no sheet still reads",   CharGen.LedgerFor(handmade).Count >= 2);
    T("and its counts floor at one",        CharGen.LedgerFor(handmade).All(r => r.Of >= 1));
    T("a soul with no Calling is empty",    CharGen.LedgerFor(new PartyMember()).Count == 0);
    T("and null is empty, not a throw",     CharGen.LedgerFor(null).Count == 0);
    T("null refuses with a sentence",       CharGen.WhyNotFeature(null, "Last Stand") != null);

    // What is spent rides along in the save file — the property is public, so the session's
    // serializer carries it without being told twice.
    soul.FeatureSpent["Last Stand"] = 1;
    var round = System.Text.Json.JsonSerializer.Deserialize<PartyMember>(
        System.Text.Json.JsonSerializer.Serialize(soul));
    T("what was spent survives a save", round.FeatureSpent.TryGetValue("Last Stand", out int st) && st == 1);
}

// ---- what a soul OWES: the running tally (v1.44.0) ----
// A ration is given back by a boundary; a tally is not given back by anything. The Hexer's
// Pact-Sworn is the only feature in the book with the second shape, and the whole risk here is the
// app being generous with a debt the Patron has not forgiven.
{
    var pact = CharGen.FeaturesAt("Hexer", 9, "The Pact-Sworn")
                      .First(f => f.Name.Contains("Pact-Sworn") && !f.Name.EndsWith("— greater"));
    var t = CharGen.ReadTally(pact.Desc);
    T("tally: the Pact-Sworn keeps one",        t.Any);
    T("tally: it counts Debts",                 t.Noun == "Debt");
    T("tally: and the third one comes due",     t.At == 3);
    T("tally: the book's sentence is kept",     (t.Phrase ?? "").Contains("Patron calls it in"));
    T("tally: the card says it in words",       t.Says == "the third Debt comes due");

    // Ordinary prose is not a tally. "on your first turn" is the shape that would flood the strip
    // with counters nobody asked for, and a counter the app invented is worse than one it lacks.
    T("tally: a turn is not a debt",            !CharGen.ReadTally("On your first turn, move twice.").Any);
    T("tally: nothing said, nothing counted",   !CharGen.ReadTally("Once per scene, shoot twice.").Any);
    T("tally: empty prose is not a throw",      !CharGen.ReadTally(null).Any && !CharGen.ReadTally("").Any);

    // The structural claim, held to the data: exactly ONE of the book's features declares a tally.
    // If a new Calling or path ever states a second, this fails and somebody reads the strip before
    // a card appears on it unannounced.
    int declared = 0;
    foreach (var cal in CharGen.D.callings)
    {
        foreach (var kv in cal.featureDescs ?? new())
            if (CharGen.ReadTally(kv.Value).Any) declared++;
        foreach (var o in cal.subpath?.options ?? new())
            if (CharGen.ReadTally(o.boon).Any) declared++;
    }
    T("tally: exactly one in the whole book", declared == 1);

    var hex = new PartyMember { Name = "Opal", Calling = "Hexer", Level = 9,
                                Sheet = CharGen.Generate(9, false, "Hexer") };
    hex.Sheet.Subpath = "The Pact-Sworn";

    var rows = CharGen.TalliesFor(hex);
    T("tally: the Hexer has one to keep", rows.Count == 1 && rows[0].Owed == 0);

    var (owed1, due1) = CharGen.TakeTally(hex, rows[0].Name);
    T("tally: the first is taken on",  owed1 == 1 && !due1);
    var (owed2, due2) = CharGen.TakeTally(hex, rows[0].Name);
    T("tally: the second stands too",  owed2 == 2 && !due2);
    var (owed3, due3) = CharGen.TakeTally(hex, rows[0].Name);
    T("tally: the third comes due",    owed3 == 3 && due3);
    // Past the threshold it keeps counting rather than clamping: the Patron collecting is the
    // Keeper's move, and an app that refused a fourth Debt would be making it for them.
    var (owed4, due4) = CharGen.TakeTally(hex, rows[0].Name);
    T("tally: and a fourth is allowed", owed4 == 4 && due4);

    // THE check this whole store exists for. Every boundary the app has, in order, and the debt is
    // still owed after all of them. RefreshFeatures walks FeatureSpent alone by design; if that
    // ever changes, this is what says so.
    foreach (var b in new[] { FeatureCadence.Turn, FeatureCadence.Round, FeatureCadence.Scene,
                              FeatureCadence.Dawn, FeatureCadence.Trigger, FeatureCadence.Session })
    {
        CharGen.RefreshFeatures(hex, b);
        T($"tally: {b} does not forgive a Debt", CharGen.TalliesFor(hex)[0].Owed == 4);
    }

    T("tally: the Keeper can strike one off",  CharGen.ForgiveTally(hex, rows[0].Name));
    T("tally: and the count agrees",           CharGen.TalliesFor(hex)[0].Owed == 3);
    while (CharGen.ForgiveTally(hex, rows[0].Name)) { }
    T("tally: down to nothing owed",           CharGen.TalliesFor(hex)[0].Owed == 0);
    T("tally: and no further",                 !CharGen.ForgiveTally(hex, rows[0].Name));
    T("tally: a feature nobody has moves nothing", CharGen.TakeTally(hex, "The Conjurer").Owed == 0);

    // A Hexer who has chosen a different bargain owes nothing, and one who has chosen none owes
    // nothing either — the strip must not offer a debt to somebody who cannot take one.
    var conjurer = new PartyMember { Name = "Ida", Calling = "Hexer", Level = 9,
                                     Sheet = CharGen.Generate(9, false, "Hexer") };
    conjurer.Sheet.Subpath = "The Conjurer";
    T("tally: the Conjurer keeps none", CharGen.TalliesFor(conjurer).Count == 0);
    var unchosen = new PartyMember { Name = "Kit", Calling = "Hexer", Level = 9,
                                     Sheet = CharGen.Generate(9, false, "Hexer") };
    unchosen.Sheet.Subpath = null;
    T("tally: an unchosen bargain keeps none", CharGen.TalliesFor(unchosen).Count == 0);
    T("tally: a Gunhand keeps none",    CharGen.TalliesFor(
        new PartyMember { Name = "Ruth", Calling = "Gunhand", Level = 9 }).Count == 0);
    T("tally: null is empty, not a throw", CharGen.TalliesFor(null).Count == 0);

    // What the card CALLS a feature, versus the key it is stored under. Both Bargain cards used to
    // ellipsise to the same 24 characters, which is two cards a Keeper cannot tell apart.
    string longKey = rows[0].Name;
    T("short name: the section is dropped",  CharGen.ShortFeatureName(longKey) == "The Pact-Sworn");
    T("short name: the greater one differs",
        CharGen.ShortFeatureName(longKey) != CharGen.ShortFeatureName(longKey + " — greater"));
    T("short name: a plain feature is untouched",
        CharGen.ShortFeatureName("Last Stand") == "Last Stand");
    T("short name: null and empty survive",
        CharGen.ShortFeatureName(null) == null && CharGen.ShortFeatureName("") == "");
    // Display only: the key everything is stored under is never the short one.
    T("short name: the store still uses the whole key",
        hex.TallyOwed.Keys.All(k => k.Contains(": ")));

    // And it rides in the save file, same as what was spent.
    CharGen.TakeTally(hex, rows[0].Name);
    var reloaded = System.Text.Json.JsonSerializer.Deserialize<PartyMember>(
        System.Text.Json.JsonSerializer.Serialize(hex));
    T("tally: what is owed survives a save",
        reloaded.TallyOwed.TryGetValue(rows[0].Name, out int ow) && ow == 1);
}

Console.WriteLine($"\n{pass} passed, {fail} failed");
return fail == 0 ? 0 : 1;
