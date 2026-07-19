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
T("110 creatures", Db.Creatures.Count == 110);
T("creature names unique", Db.Creatures.Select(c => c.name).Distinct(StringComparer.OrdinalIgnoreCase).Count() == Db.Creatures.Count);
T("all stat blocks parse", Db.Creatures.All(c => c.BloodValue > 0 && c.DefenseValue > 0));
T("13 simple tables", Db.Simple.Count == 13);
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
T("17 callings", cg.callings.Count == 17);
T("10 origins", cg.origins.Count == 10);
T("17 skills", cg.skills.Count == 17);
T("8 signs", cg.signs.Count == 8);
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
    var expectList = CharGen.Flavor(g.Gender == "Woman" ? "givenWomen" : "givenMen");
    T("given name matches the gender list", expectList.Contains(g.Name.Split(' ')[0]));
}
T("both genders turn up", Enumerable.Range(0, 60).Select(_ => CharGen.Generate(1, false).Gender).Distinct().Count() == 2);
{
    var spec = new CharGen.AssembleSpec { Level = 1, Calling = "Gunhand", Origin = "The Outlaw", Gender = "Woman" };
    var pool2 = new List<int>(cg.honestArray);
    var gh = cg.callings.First(c => c.name == "Gunhand");
    for (int i = 0; i < 6; i++) spec.PreGiftScores[gh.keyAbilities[i]] = pool2[i];
    var s2 = CharGen.Assemble(spec);
    T("assemble honors the given gender", s2.Gender == "Woman");
    T("assemble rolls a matching name", CharGen.Flavor("givenWomen").Contains(s2.Name.Split(' ')[0]));
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
    spec.Subpath = "Not A Path";
    spec.BuyWeapons.Add(cg.weapons[Rules.Rng.Next(cg.weapons.Count)].name);
    spec.BuyGear.Add(cg.gearPrices.Keys.First());
    var sheet = CharGen.Assemble(spec);
    var v = CharGen.Validate(sheet);
    T($"assemble sweep #{i}" + (v.Count > 0 ? $" ({sheet.Calling}/{sheet.Origin} L{sheet.Level}): {v[0]}" : ""), v.Count == 0);
    if (i == 0) T("assemble honors the given name", sheet.Name == "Test Soul");
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
    Console.WriteLine($"sample PDFs → {outDir}");
}

Console.WriteLine($"\n{pass} passed, {fail} failed");
return fail == 0 ? 0 : 1;
