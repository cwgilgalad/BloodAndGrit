using System.Text;
using System.Text.Json;

namespace BloodAndGritKeeper;

// ============================================================ CHARGEN DATA (Data/chargen.json)
// Transcribed from the Player's Book (Ch. III–IV, VIII–X, XIII–XIV). The generator walks
// the same eight steps as Chapter III and never invents a number the book doesn't give it;
// CharGen.Validate re-derives every figure independently so the smoke suite can prove it.

public class CgSkill { public string name { get; set; } public string ability { get; set; } }

public class CgOrigin
{
    public string name { get; set; }
    public Dictionary<string, int> gifts { get; set; } = new();
    public List<string> trained { get; set; } = new();
    public List<string> trainedChoice { get; set; } = new();
    public bool notFaith { get; set; }
    public List<string> gear { get; set; } = new();
    public int startMark { get; set; }
    public string line { get; set; } public string boon { get; set; } public string burden { get; set; }
}

public class CgEdge
{
    public string name { get; set; } public string group { get; set; } public string desc { get; set; }
    public Dictionary<string, int> reqAbility { get; set; }
    public string reqEdge { get; set; } public string reqTrained { get; set; }
    public bool notFaith { get; set; } public string effect { get; set; }
    // calling-locked edges
    public string calling { get; set; } public string reqFeature { get; set; }
}

public class CgSign { public string name { get; set; } public string cost { get; set; } public string desc { get; set; } }

public class CgWeapon { public string name { get; set; } public string dmg { get; set; } public string traits { get; set; } public double cost { get; set; } public string kind { get; set; } }

public class CgRow
{
    public int level { get; set; }
    public int atk { get; set; } public int fort { get; set; } public int @ref { get; set; } public int will { get; set; }
    public List<string> features { get; set; } = new();
}

public class CgCoin { public int dice { get; set; } public int mult { get; set; } public List<string> kit { get; set; } = new(); public string note { get; set; } }
public class CgPool { public string name { get; set; } public string formula { get; set; } public int min { get; set; } }
public class CgChoice { public string label { get; set; } public List<string> options { get; set; } = new(); }
public class CgSubOption { public string name { get; set; } public string boon { get; set; } }
public class CgSubpath { public string section { get; set; } public List<CgSubOption> options { get; set; } = new(); }

public class CgCalling
{
    public string name { get; set; } public string group { get; set; }
    public int hitDie { get; set; } public int trainedSkills { get; set; }
    public string strongSaves { get; set; }
    public List<CgRow> rows { get; set; } = new();
    public Dictionary<string, string> featureDescs { get; set; } = new();
    public Dictionary<string, int> signsKnownAt { get; set; }
    public CgSubpath subpath { get; set; }
    public CgCoin coin { get; set; }
    public List<string> skillPrefs { get; set; } = new();
    public List<string> edgePrefs { get; set; } = new();
    public JsonElement buyPlan { get; set; }
    public List<string> keyAbilities { get; set; } = new();
    public CgPool pool { get; set; }
    public CgChoice choice { get; set; }
    public int startMark { get; set; }
    public bool bonusCombatEdgeAtOdd { get; set; }
    /// <summary>Practiced / Steady / Slight — see CharGen.AttackFor (Player's Book Ch. XIV).</summary>
    public string attackRank { get; set; }

    public CgRow Row(int level) => rows.First(r => r.level == level);
}

public class CgData
{
    public List<int> honestArray { get; set; } = new();
    public List<CgSkill> skills { get; set; } = new();
    public List<CgOrigin> origins { get; set; } = new();
    public List<CgEdge> edges { get; set; } = new();
    public List<CgEdge> callingEdges { get; set; } = new();
    public List<CgSign> signs { get; set; } = new();
    public List<CgWeapon> weapons { get; set; } = new();
    public Dictionary<string, double> gearPrices { get; set; } = new();
    public List<CgCalling> callings { get; set; } = new();
    public JsonElement flavor { get; set; }
}

// ============================================================ THE SHEET
// Auto-properties (not fields) so System.Text.Json carries the whole sheet — it rides
// inside PartyMember.Sheet through session.json and back.
public class CharacterSheet
{
    public string Name { get; set; } public string Gender { get; set; }
    public string Calling { get; set; }
    public string Origin { get; set; } public string Compass { get; set; }
    public int Level { get; set; }
    public string Method { get; set; }                                  // "The Honest Array" | "The Gamble (rolled)"
    public Dictionary<string, int> Scores { get; set; } = new();         // final scores, gifts applied
    public Dictionary<string, int> PreGiftScores { get; set; } = new();  // before origin gifts (for validation)
    public int Blood { get; set; } public int Defense { get; set; }
    public int Fort { get; set; } public int Ref { get; set; } public int Will { get; set; }
    public int NerveMax { get; set; } public int Grit { get; set; }
    public int Speed { get; set; } public int Mark { get; set; } public int Attack { get; set; }
    public List<int> BloodRolls { get; set; } = new();                   // per-level gains, level 1 first
    public List<int> ConModAtLevel { get; set; } = new();                // CON mod snapshot used per level
    public Dictionary<string, int> SkillRanks { get; set; } = new();     // 1 trained · 2 expert · 3 master
    public List<string> OriginSkills { get; set; } = new();              // granted by Origin (not counted vs the Calling's number)
    public List<string> Edges { get; set; } = new();
    public List<string> BonusCombatEdges { get; set; } = new();          // Gunhand's Edge picks
    public List<string> Features { get; set; } = new();
    public List<string> SignsKnown { get; set; } = new();
    public string Subpath { get; set; }                                  // chosen at 3rd, or null
    public string CallingChoice { get; set; }                            // Marshal reputation / Shaman aspect / Witch familiar
    public string PoolLine { get; set; }                                 // e.g. "Favor 3 (PRE mod + half level, refreshed each dawn)"
    public double CoinRolled { get; set; } public double CoinLeft { get; set; }
    public List<string> Gear { get; set; } = new();
    public List<string> WeaponsCarried { get; set; } = new();            // "Single-Action Revolver 1d8 (Fatal d10, Misfire 1)"
    public string Lost { get; set; } public string Seen { get; set; }
    public string Vice { get; set; } public string Moving { get; set; }
    public List<int> AbilityBoostLevels { get; set; } = new();           // 5 and/or 10 if reached
    public List<string> BoostedAbilities { get; set; } = new();
    public bool HandTweaked { get; set; }                                // edited after generation — the book no longer vouches
}

// ============================================================ GENERATOR
public static class CharGen
{
    // ---- the progression spine (Player's Book Ch. XIV, "Attack Rank and the Saves") ----
    // Every rank climbs by one per level; the rank fixes a constant distance behind the gun
    // Callings. Saves are two formulas shared by all seventeen Callings.

    /// <summary>Attack bonus from the Calling's rank at a given level.</summary>
    public static int AttackFor(string rank, int level) => rank switch
    {
        "Practiced" => level,
        "Steady"    => level - 1,
        "Slight"    => Math.Max(0, level - 2),
        _           => throw new ArgumentOutOfRangeException(nameof(rank), $"unknown attack rank '{rank}'"),
    };

    /// <summary>A strong save: 2 + half your level, rounding down.</summary>
    public static int StrongSave(int level) => 2 + level / 2;

    /// <summary>A weak save: a third of your level, rounding down.</summary>
    public static int WeakSave(int level) => level / 3;

    public static CgData D { get; private set; }

    public static void Load()
    {
        var opts = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        D = JsonSerializer.Deserialize<CgData>(Db.ReadDataFile("chargen.json"), opts);
    }

    static readonly string[] Ab = { "STR", "DEX", "CON", "WIT", "RES", "PRE" };
    public static int Mod(int score) => (int)Math.Floor((score - 10) / 2.0);

    static T Pick<T>(List<T> list) => list[Rules.Rng.Next(list.Count)];

    static List<string> FlavorList(string key)
    {
        var l = new List<string>();
        foreach (var e in D.flavor.GetProperty(key).EnumerateArray()) l.Add(e.GetString());
        return l;
    }

    // a soul is somebody: gender rolled plainly, and the given name drawn to match.
    // TryGetProperty keeps an older chargen.json (no gendered lists) from crashing —
    // it falls back to the mixed NPC list and leaves gender blank.
    static (string gender, string given) PickPerson()
    {
        if (D.flavor.TryGetProperty("givenWomen", out _) && D.flavor.TryGetProperty("givenMen", out _))
        {
            bool woman = Rules.Rng.Next(2) == 0;
            return (woman ? "Woman" : "Man", Pick(FlavorList(woman ? "givenWomen" : "givenMen")));
        }
        return (null, Db.Pick("npcGiven"));
    }

    // A whole name for a soul. Most of the frontier's names are a given name drawn against
    // gender plus a surname drawn separately, and mixing those two pools freely is right —
    // "Refugio Whitlock" and "Jubal Deets" are both perfectly ordinary 1885. Some names do
    // NOT decompose that way, though: a Chinese name puts the surname first, and pairing one
    // half of it with a surname from the general pool produces nonsense. Those live in a
    // whole-name pool and are drawn complete, surname draw skipped.
    public static string FullName(string gender)
    {
        var whole = Flavor(gender == "Woman" ? "fullNamesWomen" : "fullNamesMen");
        if (whole.Count > 0 && Rules.Rng.Next(100) < 12) return Pick(whole);
        return GivenFor(gender) + " " + Db.Pick("npcSurname");
    }

    static string GivenFor(string gender) => gender switch
    {
        "Woman" when D.flavor.TryGetProperty("givenWomen", out _) => Pick(FlavorList("givenWomen")),
        "Man"   when D.flavor.TryGetProperty("givenMen", out _)   => Pick(FlavorList("givenMen")),
        _ => Db.Pick("npcGiven")
    };

    public static CharacterSheet Generate(int level, bool rolled, string fixedCalling = null, string fixedOrigin = null)
    {
        level = Math.Clamp(level, 1, 10);
        var s = new CharacterSheet { Level = level, Method = rolled ? "The Gamble (rolled)" : "The Honest Array" };

        // ---- Step 3/4: Origin & Calling (order swapped so the Origin constraint can see the Calling) ----
        var cal = fixedCalling != null ? D.callings.First(c => c.name == fixedCalling) : Pick(D.callings);
        bool isFaith = cal.group == "Faith";
        var legalOrigins = D.origins.Where(o => !(isFaith && o.notFaith)).ToList();   // Ch. IV: no Gambler origin for Callings of Faith
        var org = fixedOrigin != null ? D.origins.First(o => o.name == fixedOrigin) : Pick(legalOrigins);
        if (isFaith && org.notFaith) org = Pick(legalOrigins);                        // fixed pick that breaks the rule is re-drawn
        s.Calling = cal.name; s.Origin = org.name;

        // ---- Step 2: the six abilities (Ch. III methods), assigned by the Calling's priorities ----
        List<int> pool;
        if (rolled)
        {
            pool = new();
            for (int i = 0; i < 6; i++)
            {
                var d4 = Enumerable.Range(0, 4).Select(_ => Rules.Rng.Next(1, 7)).OrderBy(x => x).ToList();
                pool.Add(d4[1] + d4[2] + d4[3]);              // 4d6 drop lowest
            }
            pool = pool.OrderByDescending(x => x).ToList();
        }
        else pool = new(D.honestArray);                        // 15 14 13 12 10 8

        for (int i = 0; i < 6; i++) s.PreGiftScores[cal.keyAbilities[i]] = pool[i];
        foreach (var a in Ab) s.Scores[a] = s.PreGiftScores[a] + (org.gifts.TryGetValue(a, out var g) ? g : 0);

        // ---- Step 5: trained skills — the Calling's number + WIT modifier; Origin grants come free ----
        s.OriginSkills.AddRange(org.trained);
        if (org.trainedChoice.Count > 0) s.OriginSkills.Add(Pick(org.trainedChoice));
        int trainCount = Math.Max(1, cal.trainedSkills + Mod(s.Scores["WIT"]));
        var picks = new List<string>();
        foreach (var sk in cal.skillPrefs) { if (picks.Count >= trainCount) break; if (!s.OriginSkills.Contains(sk)) picks.Add(sk); }
        var rest = D.skills.Select(k => k.name).Where(n => !picks.Contains(n) && !s.OriginSkills.Contains(n)).ToList();
        while (picks.Count < trainCount && rest.Count > 0) { var r = Pick(rest); picks.Add(r); rest.Remove(r); }
        foreach (var sk in picks.Concat(s.OriginSkills)) s.SkillRanks[sk] = 1;

        // ---- the level walk: features, edges, skill increases, boosts, Blood, Signs ----
        var featureSet = new List<string>();
        for (int L = 1; L <= level; L++)
        {
            // ability boost first at 5/10 (Ch. IX / XIV: one point at 5th and 10th)
            if (L == 5 || L == 10)
            {
                string best = cal.keyAbilities[0];
                s.Scores[best] += 1;
                s.AbilityBoostLevels.Add(L); s.BoostedAbilities.Add(best);
            }
            int conMod = Mod(s.Scores["CON"]);
            int gain = (L == 1) ? cal.hitDie + conMod : Rules.Rng.Next(1, cal.hitDie + 1) + conMod;   // Ch. III: full Hit Die at 1st, roll after
            s.BloodRolls.Add(gain); s.ConModAtLevel.Add(conMod);

            foreach (var f in cal.Row(L).features)
                if (f != "Edge" && !f.StartsWith("Sign learned") && !f.StartsWith("Stolen Wonder")) featureSet.Add(f);

            // Edges at 1st and each odd level (Ch. IX), plus the Gunhand's bonus combat Edge
            if (L % 2 == 1)
            {
                var pick2 = PickEdge(s, cal, isFaith, null);
                if (pick2 != null) s.Edges.Add(pick2);
                if (cal.bonusCombatEdgeAtOdd)
                {
                    var gun = PickEdge(s, cal, isFaith, "Gun");
                    if (gun != null) s.BonusCombatEdges.Add(gun);
                }
            }

            // skill increase at 3/5/7/9 (Ch. VIII: a step toward Expert, then Master as level allows)
            if (L is 3 or 5 or 7 or 9) ApplySkillIncrease(s, cal, L);
        }
        s.Features = featureSet;

        // subpath at 3rd (Trades / Schools / Oaths / Bargains / Devotions …)
        if (level >= 3 && cal.subpath != null && cal.subpath.options.Count > 0)
            s.Subpath = Pick(cal.subpath.options).name;

        // calling one-of choice (Marshal's Reputation, Shaman's Aspect, Witch's Familiar)
        if (cal.choice != null) s.CallingChoice = $"{cal.choice.label}: {Pick(cal.choice.options)}";

        // Signs (Ch. VII / XIII): only the Old Dark works them by nature; Hedge Magic adds one
        var signNames = D.signs.Select(x => x.name).ToList();
        int signCount = cal.signsKnownAt != null ? cal.signsKnownAt[level.ToString()] : 0;
        if (s.Edges.Contains("Hedge Magic")) signCount += 1;
        while (s.SignsKnown.Count < Math.Min(signCount, signNames.Count))
        { var sg = Pick(signNames); if (!s.SignsKnown.Contains(sg)) s.SignsKnown.Add(sg); }

        // ---- Step 6: reckon the numbers (Ch. III) ----
        ReckonNumbers(s, cal, org);

        // ---- Step 7: outfit (Ch. X — coin rolled, kit granted, prices as printed) ----
        s.CoinRolled = Enumerable.Range(0, cal.coin.dice).Sum(_ => Rules.Rng.Next(1, 7)) * cal.coin.mult;
        double left = s.CoinRolled;
        s.Gear.AddRange(cal.coin.kit);
        s.Gear.AddRange(org.gear);
        bool hasGun = cal.coin.kit.Concat(org.gear).Any(x => x.Contains("rifle") || x.Contains("carbine") || x.Contains("Rifle"));
        foreach (var gunName in cal.buyPlan.GetProperty("guns").EnumerateArray())
        {
            if (hasGun) break;
            var w = D.weapons.First(x => x.name == gunName.GetString());
            if (left >= w.cost) { left -= w.cost; s.WeaponsCarried.Add($"{w.name} {w.dmg} ({w.traits}) — ${w.cost}"); hasGun = true; }
        }
        if (cal.buyPlan.GetProperty("melee").ValueKind == JsonValueKind.String)
        {
            var w = D.weapons.First(x => x.name == cal.buyPlan.GetProperty("melee").GetString());
            s.WeaponsCarried.Add($"{w.name} {w.dmg} ({w.traits})");
        }
        double horseCost = 0; var horseItems = new List<string>();
        foreach (var it in cal.buyPlan.GetProperty("sundries").EnumerateArray())
        {
            string item = it.GetString();
            if (item.Contains("Shotgun"))
            {
                var w = D.weapons.First(x => x.name == "Double-Barrel Shotgun");
                if (!hasGun && left >= w.cost) { left -= w.cost; s.WeaponsCarried.Add($"{w.name} {w.dmg} ({w.traits}) — ${w.cost}"); hasGun = true; }
                continue;
            }
            double cost = D.gearPrices[item];
            if (item.Contains("Cow pony") || item.Contains("Saddle, bridle")) { horseCost += cost; horseItems.Add(item); continue; }
            if (left >= cost) { left -= cost; s.Gear.Add(item); }
        }
        if (horseItems.Count == 2 && left >= horseCost) { left -= horseCost; s.Gear.AddRange(horseItems); }
        s.CoinLeft = Math.Round(left, 2);

        // ---- Steps 1 & 8: a person, not a statline ----
        var (gender, given) = PickPerson();
        s.Gender = gender;
        s.Name = given + " " + Db.Pick("npcSurname");
        s.Compass = WeightedCompass();
        s.Lost = Pick(FlavorList("lost")); s.Seen = Pick(FlavorList("seen"));
        s.Vice = Pick(FlavorList("vices")); s.Moving = Pick(FlavorList("moving"));
        return s;
    }

    // ============================================================ THE WIZARD'S ROAD
    // Every choice the wizard collects. Anything left null/empty falls back to the same
    // random draw Generate would have made, so a half-answered wizard still yields a
    // legal sheet — and the smoke suite can prove Assemble conformant with random specs.
    public class AssembleSpec
    {
        public int Level = 1;
        public bool Rolled;                                   // ability method label
        public string Calling, Origin;
        public Dictionary<string, int> PreGiftScores = new(); // all six, before Origin gifts
        public string OriginSkillChoice;                      // the Origin's either/or skill, if it has one
        public List<string> TrainedPicks = new();             // the Calling's trained skills (Origin grants ride free)
        public List<string> SkillIncreases = new();           // one target per increase earned (3/5/7/9), in order
        public List<string> Edges = new();                    // one per odd level, in order
        public List<string> BonusCombatEdges = new();         // the Gunhand's picks, one per odd level
        public List<string> Boosts = new();                   // ability per boost level reached (5, 10)
        public List<string> Signs = new();
        public string Subpath;                                // at 3rd+, if the Calling has one
        public string CallingChoice;                          // the option only; the label is added
        public double? CoinRolled;                            // null → roll fresh
        public List<string> BuyWeapons = new();               // weapon names bought at printed price
        public List<string> BuyGear = new();                  // price-list names bought at printed price
        public string Name, Gender, Compass, Lost, Seen, Vice, Moving;
    }

    /// Builds a sheet from the wizard's explicit choices, walking the same eight steps as
    /// Generate. Choices are honored where legal; gaps are filled the way Generate would.
    public static CharacterSheet Assemble(AssembleSpec spec)
    {
        int level = Math.Clamp(spec.Level, 1, 10);
        var cal = D.callings.First(c => c.name == spec.Calling);
        var org = D.origins.First(o => o.name == spec.Origin);
        bool isFaith = cal.group == "Faith";
        var s = new CharacterSheet
        {
            Level = level, Calling = cal.name, Origin = org.name,
            Method = spec.Rolled ? "The Gamble (rolled)" : "The Honest Array"
        };

        foreach (var a in Ab) s.PreGiftScores[a] = spec.PreGiftScores.TryGetValue(a, out var v) ? v : 10;
        foreach (var a in Ab) s.Scores[a] = s.PreGiftScores[a] + (org.gifts.TryGetValue(a, out var g) ? g : 0);

        // trained skills: Origin grants free, then exactly the Calling's number of picks
        s.OriginSkills.AddRange(org.trained);
        if (org.trainedChoice.Count > 0)
            s.OriginSkills.Add(org.trainedChoice.Contains(spec.OriginSkillChoice) ? spec.OriginSkillChoice : Pick(org.trainedChoice));
        int trainCount = Math.Max(1, cal.trainedSkills + Mod(s.Scores["WIT"]));
        var picks = spec.TrainedPicks.Where(sk => D.skills.Any(k => k.name == sk) && !s.OriginSkills.Contains(sk))
                                     .Distinct().Take(trainCount).ToList();
        foreach (var sk in cal.skillPrefs) { if (picks.Count >= trainCount) break; if (!picks.Contains(sk) && !s.OriginSkills.Contains(sk)) picks.Add(sk); }
        var rest = D.skills.Select(k => k.name).Where(n => !picks.Contains(n) && !s.OriginSkills.Contains(n)).ToList();
        while (picks.Count < trainCount && rest.Count > 0) { var r = Pick(rest); picks.Add(r); rest.Remove(r); }
        foreach (var sk in picks.Concat(s.OriginSkills)) s.SkillRanks[sk] = 1;

        // the level walk — boosts, Blood, features, Edges, skill increases, in book order
        var featureSet = new List<string>();
        int edgeIdx = 0, gunIdx = 0, incIdx = 0, boostIdx = 0;
        for (int L = 1; L <= level; L++)
        {
            if (L == 5 || L == 10)
            {
                string ab = boostIdx < spec.Boosts.Count && Ab.Contains(spec.Boosts[boostIdx]) ? spec.Boosts[boostIdx] : cal.keyAbilities[0];
                boostIdx++;
                s.Scores[ab] += 1;
                s.AbilityBoostLevels.Add(L); s.BoostedAbilities.Add(ab);
            }
            int conMod = Mod(s.Scores["CON"]);
            int gain = (L == 1) ? cal.hitDie + conMod : Rules.Rng.Next(1, cal.hitDie + 1) + conMod;
            s.BloodRolls.Add(gain); s.ConModAtLevel.Add(conMod);

            foreach (var f in cal.Row(L).features)
                if (f != "Edge" && !f.StartsWith("Sign learned") && !f.StartsWith("Stolen Wonder")) featureSet.Add(f);
            s.Features = featureSet;                           // keep current for eligibility checks

            if (L % 2 == 1)
            {
                var owned = s.Edges.Concat(s.BonusCombatEdges).ToHashSet();
                string want = edgeIdx < spec.Edges.Count ? spec.Edges[edgeIdx] : null;
                edgeIdx++;
                var e = want != null ? EdgeByName(want) : null;
                string chosen = e != null && EdgeEligible(e, s, cal, isFaith, owned) ? e.name
                              : PickEdge(s, cal, isFaith, null);
                if (chosen != null) s.Edges.Add(chosen);

                if (cal.bonusCombatEdgeAtOdd)
                {
                    owned = s.Edges.Concat(s.BonusCombatEdges).ToHashSet();
                    string wantGun = gunIdx < spec.BonusCombatEdges.Count ? spec.BonusCombatEdges[gunIdx] : null;
                    gunIdx++;
                    var ge = wantGun != null ? EdgeByName(wantGun) : null;
                    string gun = ge != null && ge.group == "Gun" && EdgeEligible(ge, s, cal, isFaith, owned) ? ge.name
                               : PickEdge(s, cal, isFaith, "Gun");
                    if (gun != null) s.BonusCombatEdges.Add(gun);
                }
            }

            if (L is 3 or 5 or 7 or 9)
            {
                string target = incIdx < spec.SkillIncreases.Count ? spec.SkillIncreases[incIdx] : null;
                incIdx++;
                bool applied = false;
                if (target != null && D.skills.Any(k => k.name == target))
                {
                    if (!s.SkillRanks.TryGetValue(target, out var r)) { s.SkillRanks[target] = 1; applied = true; }
                    else if (r == 1) { s.SkillRanks[target] = 2; applied = true; }
                    else if (r == 2 && L >= 7) { s.SkillRanks[target] = 3; applied = true; }
                }
                if (!applied) ApplySkillIncrease(s, cal, L);
            }
        }

        // subpath, the one-of choice, Signs
        if (level >= 3 && cal.subpath != null && cal.subpath.options.Count > 0)
            s.Subpath = cal.subpath.options.Any(o => o.name == spec.Subpath) ? spec.Subpath : Pick(cal.subpath.options).name;
        if (cal.choice != null)
            s.CallingChoice = $"{cal.choice.label}: {(cal.choice.options.Contains(spec.CallingChoice) ? spec.CallingChoice : Pick(cal.choice.options))}";

        var signNames = D.signs.Select(x => x.name).ToList();
        int signCount = cal.signsKnownAt != null ? cal.signsKnownAt[level.ToString()] : 0;
        if (s.Edges.Contains("Hedge Magic")) signCount += 1;
        signCount = Math.Min(signCount, signNames.Count);
        foreach (var sg in spec.Signs.Where(signNames.Contains).Distinct())
            if (s.SignsKnown.Count < signCount) s.SignsKnown.Add(sg);
        while (s.SignsKnown.Count < signCount)
        { var sg = Pick(signNames); if (!s.SignsKnown.Contains(sg)) s.SignsKnown.Add(sg); }

        ReckonNumbers(s, cal, org);

        // outfit: coin as rolled (or roll it here), the kit free, purchases at printed prices
        int minCoin = cal.coin.dice * cal.coin.mult, maxCoin = cal.coin.dice * 6 * cal.coin.mult;
        s.CoinRolled = spec.CoinRolled is double c && c >= minCoin && c <= maxCoin && c % cal.coin.mult == 0
            ? c : Enumerable.Range(0, cal.coin.dice).Sum(_ => Rules.Rng.Next(1, 7)) * cal.coin.mult;
        double left = s.CoinRolled;
        s.Gear.AddRange(cal.coin.kit);
        s.Gear.AddRange(org.gear);
        foreach (var wn in spec.BuyWeapons)
        {
            var w = D.weapons.FirstOrDefault(x => x.name == wn);
            if (w != null && left >= w.cost)
            { left -= w.cost; s.WeaponsCarried.Add($"{w.name} {w.dmg} ({w.traits}) — ${w.cost}"); }
        }
        foreach (var gn in spec.BuyGear)
        {
            if (D.gearPrices.TryGetValue(gn, out var price) && left >= price && !s.Gear.Contains(gn))
            { left -= price; s.Gear.Add(gn); }
        }
        s.CoinLeft = Math.Round(left, 2);

        // a person, not a statline
        if (string.IsNullOrWhiteSpace(spec.Gender)) { var (rg, _) = PickPerson(); s.Gender = rg; }
        else s.Gender = spec.Gender.Trim();
        s.Name = string.IsNullOrWhiteSpace(spec.Name) ? FullName(s.Gender) : spec.Name.Trim();
        s.Compass = string.IsNullOrWhiteSpace(spec.Compass) ? WeightedCompass() : spec.Compass;
        s.Lost = string.IsNullOrWhiteSpace(spec.Lost) ? Pick(FlavorList("lost")) : spec.Lost;
        s.Seen = string.IsNullOrWhiteSpace(spec.Seen) ? Pick(FlavorList("seen")) : spec.Seen;
        s.Vice = string.IsNullOrWhiteSpace(spec.Vice) ? Pick(FlavorList("vices")) : spec.Vice;
        s.Moving = string.IsNullOrWhiteSpace(spec.Moving) ? Pick(FlavorList("moving")) : spec.Moving;
        return s;
    }

    // ============================================================ LEVELLING UP
    // One soul, one level higher. Rather than reconstruct an AssembleSpec and re-walk from
    // 1st — Assemble re-rolls every prior level's Blood and has no way to be handed the old
    // rolls, so that path would destabilize the levels below — LevelUp clones the finished
    // sheet and appends exactly the new level's growth, mirroring Generate's own per-level
    // walk (boost → Blood → features → Edge(s) → skill increase → subpath → Signs → reckon).
    // Everything below the new level is byte-stable, and the result is Validate-clean.
    // Choices are honored where legal; anything blank falls back to the draw Generate makes.
    public class LevelUpChoices
    {
        public string Boost;              // ability raised, if the new level is 5th or 10th
        public int? BloodDie;             // the new level's Hit-Die face (1..hitDie); null → roll
        public string Edge;               // the odd-level Edge; null → draw
        public string BonusCombatEdge;    // the Gunhand's odd-level Gun Edge; null → draw
        public string SkillIncrease;      // the 3/5/7/9 increase target; null → draw
        public string Subpath;            // chosen when 3rd unlocks it; null → draw
        public List<string> NewSigns = new();   // signs for any slots the new level opens
    }

    // What a soul's next level grants — drives the level-up dialog's controls and their
    // option lists, computed on a clone advanced by the deterministic part of the level
    // (default boost + the new features) so Edge/skill eligibility reflects the new level.
    public class LevelUpGrants
    {
        public int NewLevel, HitDie, ConModForBlood;
        public bool Boost, Edge, GunEdge, SkillIncrease, Subpath, AtCeiling;
        public int NewSignSlots;
        public string DefaultBoost, DefaultSubpath;
        public List<string> BoostOptions = new(), EdgeOptions = new(), GunEdgeOptions = new(),
            SkillOptions = new(), SubpathOptions = new(), SignOptions = new();
    }

    static CharacterSheet Clone(CharacterSheet s)
        => JsonSerializer.Deserialize<CharacterSheet>(JsonSerializer.Serialize(s));

    // legal targets for a skill increase at this level: trained skills that can still step
    // (→ Expert always at 3rd+, → Master at 7th+) and any untrained skill (train it new)
    static List<string> SkillIncreaseTargets(CharacterSheet s, int level)
    {
        var opts = new List<string>();
        foreach (var name in D.skills.Select(k => k.name))
        {
            if (s.SkillRanks.TryGetValue(name, out var r))
            { if (r == 1) opts.Add(name); else if (r == 2 && level >= 7) opts.Add(name); }
            else opts.Add(name);
        }
        return opts;
    }

    public static LevelUpGrants PreviewLevelUp(CharacterSheet cur)
    {
        var cal = D.callings.First(c => c.name == cur.Calling);
        int N = cur.Level + 1;
        var g = new LevelUpGrants { NewLevel = N, HitDie = cal.hitDie };
        if (cur.Level >= 10) { g.AtCeiling = true; return g; }

        g.Boost = N is 5 or 10;
        g.Edge = N % 2 == 1;
        g.GunEdge = g.Edge && cal.bonusCombatEdgeAtOdd;
        g.SkillIncrease = N is 3 or 5 or 7 or 9;
        g.Subpath = N >= 3 && cal.subpath != null && cal.subpath.options.Count > 0 && cur.Subpath == null;

        int Signs(int lvl)
        {
            int c = cal.signsKnownAt != null ? cal.signsKnownAt[lvl.ToString()] : 0;
            if (cur.Edges.Contains("Hedge Magic")) c += 1;
            return Math.Min(c, D.signs.Count);
        }
        g.NewSignSlots = Math.Max(0, Signs(N) - Signs(cur.Level));

        var clone = Clone(cur); clone.Level = N;
        if (g.Boost) clone.Scores[cal.keyAbilities[0]] += 1;
        foreach (var f in cal.Row(N).features)
            if (f != "Edge" && !f.StartsWith("Sign learned") && !f.StartsWith("Stolen Wonder")) clone.Features.Add(f);
        g.ConModForBlood = Mod(clone.Scores["CON"]);

        g.BoostOptions = Ab.ToList(); g.DefaultBoost = cal.keyAbilities[0];
        if (g.Edge)
            g.EdgeOptions = EligibleEdges(clone)
                .Where(n => !(cal.bonusCombatEdgeAtOdd && EdgeByName(n).group == "Gun")).ToList();
        if (g.GunEdge) g.GunEdgeOptions = EligibleEdges(clone, "Gun");
        if (g.SkillIncrease) g.SkillOptions = SkillIncreaseTargets(clone, N);
        if (g.Subpath) { g.SubpathOptions = cal.subpath.options.Select(o => o.name).ToList(); g.DefaultSubpath = g.SubpathOptions[0]; }
        if (g.NewSignSlots > 0) g.SignOptions = D.signs.Select(x => x.name).Where(n => !cur.SignsKnown.Contains(n)).ToList();
        return g;
    }

    public static CharacterSheet LevelUp(CharacterSheet cur, LevelUpChoices ch)
    {
        ch ??= new LevelUpChoices();
        var cal = D.callings.First(c => c.name == cur.Calling);
        var org = D.origins.First(o => o.name == cur.Origin);
        bool isFaith = cal.group == "Faith";
        var s = Clone(cur);
        if (cur.Level >= 10) return s;                    // the frontier's ceiling
        int N = cur.Level + 1; s.Level = N;

        if (N is 5 or 10)                                  // boost first, as in Generate
        {
            string ab = Ab.Contains(ch.Boost ?? "") ? ch.Boost : cal.keyAbilities[0];
            s.Scores[ab] += 1; s.AbilityBoostLevels.Add(N); s.BoostedAbilities.Add(ab);
        }
        int conMod = Mod(s.Scores["CON"]);
        int die = ch.BloodDie is int bd && bd >= 1 && bd <= cal.hitDie ? bd : Rules.Rng.Next(1, cal.hitDie + 1);
        s.BloodRolls.Add(die + conMod); s.ConModAtLevel.Add(conMod);

        foreach (var f in cal.Row(N).features)
            if (f != "Edge" && !f.StartsWith("Sign learned") && !f.StartsWith("Stolen Wonder")) s.Features.Add(f);

        if (N % 2 == 1)
        {
            var owned = s.Edges.Concat(s.BonusCombatEdges).ToHashSet();
            var want = ch.Edge != null ? EdgeByName(ch.Edge) : null;
            bool ok = want != null && !(cal.bonusCombatEdgeAtOdd && want.group == "Gun")
                      && EdgeEligible(want, s, cal, isFaith, owned);
            string chosen = ok ? want.name : PickEdge(s, cal, isFaith, null);
            if (chosen != null) s.Edges.Add(chosen);
            if (cal.bonusCombatEdgeAtOdd)
            {
                owned = s.Edges.Concat(s.BonusCombatEdges).ToHashSet();
                var wg = ch.BonusCombatEdge != null ? EdgeByName(ch.BonusCombatEdge) : null;
                string gun = wg != null && wg.group == "Gun" && EdgeEligible(wg, s, cal, isFaith, owned)
                           ? wg.name : PickEdge(s, cal, isFaith, "Gun");
                if (gun != null) s.BonusCombatEdges.Add(gun);
            }
        }

        if (N is 3 or 5 or 7 or 9)
        {
            string t = ch.SkillIncrease; bool applied = false;
            if (t != null && D.skills.Any(k => k.name == t))
            {
                if (!s.SkillRanks.TryGetValue(t, out var r)) { s.SkillRanks[t] = 1; applied = true; }
                else if (r == 1) { s.SkillRanks[t] = 2; applied = true; }
                else if (r == 2 && N >= 7) { s.SkillRanks[t] = 3; applied = true; }
            }
            if (!applied) ApplySkillIncrease(s, cal, N);
        }

        if (N >= 3 && cal.subpath != null && cal.subpath.options.Count > 0 && s.Subpath == null)
            s.Subpath = cal.subpath.options.Any(o => o.name == ch.Subpath) ? ch.Subpath : Pick(cal.subpath.options).name;

        var signNames = D.signs.Select(x => x.name).ToList();
        int signCount = cal.signsKnownAt != null ? cal.signsKnownAt[N.ToString()] : 0;
        if (s.Edges.Contains("Hedge Magic")) signCount += 1;
        signCount = Math.Min(signCount, signNames.Count);
        foreach (var sg in ch.NewSigns.Where(signNames.Contains).Distinct())
            if (s.SignsKnown.Count < signCount && !s.SignsKnown.Contains(sg)) s.SignsKnown.Add(sg);
        while (s.SignsKnown.Count < signCount)
        { var sg = Pick(signNames); if (!s.SignsKnown.Contains(sg)) s.SignsKnown.Add(sg); }

        ReckonNumbers(s, cal, org);
        return s;                                          // HandTweaked provenance rides through the clone
    }

    static string WeightedCompass()
    {
        var opts = new List<(string name, int w)>();
        foreach (var e in D.flavor.GetProperty("compass").EnumerateArray())
            opts.Add((e.GetProperty("name").GetString(), e.GetProperty("weight").GetInt32()));
        int total = opts.Sum(o => o.w), roll = Rules.Rng.Next(total);
        foreach (var o in opts) { roll -= o.w; if (roll < 0) return o.name; }
        return opts[0].name;
    }

    // one Edge's legality against a sheet-in-progress — shared by the random generator,
    // the wizard's option lists, and nothing else that could drift from it
    static bool EdgeEligible(CgEdge e, CharacterSheet s, CgCalling cal, bool isFaith, HashSet<string> owned)
    {
        if (owned.Contains(e.name)) return false;
        if (e.notFaith && isFaith) return false;
        // "though you are not a Hexer" — Hedge Magic is for souls WITHOUT the Signs
        // feature; the four sign-working Callings already have the whole craft
        if (e.effect == "sign+1" && cal.signsKnownAt != null) return false;
        if (e.reqAbility != null && e.reqAbility.Any(kv => s.Scores[kv.Key] < kv.Value)) return false;
        if (e.reqEdge != null && !owned.Contains(e.reqEdge)) return false;
        if (e.reqTrained != null && !s.SkillRanks.ContainsKey(e.reqTrained)) return false;
        if (e.calling != null)
        {
            if (e.calling != cal.name) return false;
            if (e.reqFeature != null && !s.Features.Any(f => f.StartsWith(e.reqFeature))) return false;
        }
        return true;
    }

    /// Every Edge the sheet could legally take right now (group != null restricts, e.g. "Gun").
    /// The wizard fills its pick lists from this so it can never offer an illegal Edge.
    public static List<string> EligibleEdges(CharacterSheet s, string group = null)
    {
        var cal = D.callings.First(c => c.name == s.Calling);
        bool isFaith = cal.group == "Faith";
        var owned = s.Edges.Concat(s.BonusCombatEdges).ToHashSet();
        return D.edges.Concat(D.callingEdges)
            .Where(e => (group == null || e.group == group) && EdgeEligible(e, s, cal, isFaith, owned))
            .Select(e => e.name).OrderBy(n => n).ToList();
    }

    public static CgEdge EdgeByName(string name)
        => D.edges.Concat(D.callingEdges).FirstOrDefault(e => e.name == name);

    // pick one legal, not-yet-owned Edge; group != null restricts (the Gunhand's combat pool)
    static string PickEdge(CharacterSheet s, CgCalling cal, bool isFaith, string group)
    {
        var owned = s.Edges.Concat(s.BonusCombatEdges).ToHashSet();
        bool Eligible(CgEdge e) => EdgeEligible(e, s, cal, isFaith, owned);
        var all = D.edges.Concat(D.callingEdges).ToList();
        if (group != null)
        {
            var pool = all.Where(e => e.group == group && Eligible(e)).ToList();
            return pool.Count > 0 ? Pick(pool).name : null;
        }
        // The Gunhand's ordinary picks stay out of the Gun group: the bonus combat Edge draws
        // from that pool at every odd level, and there are only nine combat Edges in Ch. IX —
        // free choice elsewhere keeps the guaranteed pick guaranteed.
        bool BlockedGroup(CgEdge e) => cal.bonusCombatEdgeAtOdd && e.group == "Gun";
        // preferred groups first (calling edges ride with the first preferred group), then anything
        foreach (var g in cal.edgePrefs)
        {
            var pool = all.Where(e => Eligible(e) && !BlockedGroup(e) && (e.group == g || (e.calling == cal.name && g == cal.edgePrefs[0]))).ToList();
            if (pool.Count > 0 && Rules.Rng.Next(100) < 75) return Pick(pool).name;
        }
        var any = all.Where(e => Eligible(e) && !BlockedGroup(e)).ToList();
        return any.Count > 0 ? Pick(any).name : null;
    }

    /// Step 6 of Ch. III — the reckoned numbers, shared by Generate and Assemble so the
    /// two roads can never disagree on the arithmetic.
    static void ReckonNumbers(CharacterSheet s, CgCalling cal, CgOrigin org)
    {
        int level = s.Level;
        var row = cal.Row(level);
        int rawhide = (s.Edges.Contains("Tough as Rawhide") || s.BonusCombatEdges.Contains("Tough as Rawhide")) ? level : 0;   // +1 Blood per level
        int stoneNerve = s.Edges.Contains("Stone Nerve") ? 2 * level : 0;                                                       // +2 max Nerve per level
        s.Blood = Math.Max(1, s.BloodRolls.Sum() + rawhide);
        s.Defense = 10 + Mod(s.Scores["DEX"]);
        s.Fort = row.fort + Mod(s.Scores["CON"]);
        s.Ref = row.@ref + Mod(s.Scores["DEX"]);
        s.Will = row.will + Mod(s.Scores["RES"]);
        s.Attack = row.atk;
        s.NerveMax = s.Scores["RES"] + level + stoneNerve;
        s.Grit = 3;
        s.Speed = 30 + (s.Edges.Contains("Fleet") ? 10 : 0);
        s.Mark = org.startMark + cal.startMark + (s.Edges.Contains("Touched") ? 1 : 0);

        if (cal.pool != null)
        {
            int baseMod = Mod(s.Scores[cal.pool.formula.Substring(0, 3)]);
            int val = cal.pool.formula.EndsWith("level") ? baseMod + level : baseMod + level / 2;
            val = Math.Max(cal.pool.min, val);
            string refresh = cal.pool.formula.EndsWith("level") ? "RES mod + level" : cal.pool.formula.Substring(0, 3) + " mod + half level";
            s.PoolLine = $"{cal.pool.name} {val} ({refresh}, refreshed each dawn)";
        }
    }

    /// The flavor tables (lost / seen / vices / moving / gendered names), for the
    /// wizard's pick lists. Empty (never a throw) when the data file lacks the key.
    public static List<string> Flavor(string key)
        => D.flavor.TryGetProperty(key, out _) ? FlavorList(key) : new();
    public static List<string> CompassOptions()
    {
        var l = new List<string>();
        foreach (var e in D.flavor.GetProperty("compass").EnumerateArray()) l.Add(e.GetProperty("name").GetString());
        return l;
    }

    static void ApplySkillIncrease(CharacterSheet s, CgCalling cal, int level)
    {
        // a step toward Expert (3rd+), then Master (7th+), else train something new
        foreach (var sk in cal.skillPrefs)
        {
            if (s.SkillRanks.TryGetValue(sk, out var r))
            {
                if (r == 1) { s.SkillRanks[sk] = 2; return; }
                if (r == 2 && level >= 7) { s.SkillRanks[sk] = 3; return; }
            }
        }
        var untrained = D.skills.Select(k => k.name).Where(n => !s.SkillRanks.ContainsKey(n)).ToList();
        if (untrained.Count > 0) { s.SkillRanks[Pick(untrained)] = 1; return; }
        var anyTrained = s.SkillRanks.Where(kv => kv.Value == 1).Select(kv => kv.Key).ToList();
        if (anyTrained.Count > 0) s.SkillRanks[Pick(anyTrained)] = 2;
    }

    // ============================================================ VALIDATION
    // Re-derives every number from Data/chargen.json and the sheet's recorded choices.
    // Returns the list of violations; an empty list is a rules-conformant character.
    public static List<string> Validate(CharacterSheet s)
    {
        var v = new List<string>();
        void Check(bool ok, string msg) { if (!ok) v.Add(msg); }

        var cal = D.callings.FirstOrDefault(c => c.name == s.Calling);
        var org = D.origins.FirstOrDefault(o => o.name == s.Origin);
        if (cal == null || org == null) { v.Add("unknown Calling or Origin"); return v; }
        bool isFaith = cal.group == "Faith";
        var row = cal.Row(s.Level);

        // Ch. IV constraint: a Calling of Faith may not take the Gambler background
        Check(!(isFaith && org.notFaith), $"{s.Calling} (Faith) took the {s.Origin} origin — forbidden by Ch. IV");

        // ability legality
        if (s.Method.StartsWith("The Honest"))
        {
            var used = s.PreGiftScores.Values.OrderBy(x => x).ToList();
            Check(used.SequenceEqual(D.honestArray.OrderBy(x => x)), "Honest Array scores are not the 15/14/13/12/10/8 set");
        }
        else
            Check(s.PreGiftScores.Values.All(x => x is >= 3 and <= 18), "rolled score outside 4d6-drop-lowest range");
        foreach (var a in Ab)
        {
            int gift = org.gifts.TryGetValue(a, out var g) ? g : 0;
            int expect = s.PreGiftScores[a] + gift + s.BoostedAbilities.Count(b => b == a);
            Check(s.Scores[a] == expect, $"{a} score {s.Scores[a]} ≠ pre-gift {s.PreGiftScores[a]} + gift {gift} + boosts");
        }
        Check(s.AbilityBoostLevels.SequenceEqual(new[] { 5, 10 }.Where(l => l <= s.Level)), "ability boosts not exactly at 5th/10th");

        // Blood: full Hit Die + CON at 1st, per-level rolls after (Ch. III), + Tough as Rawhide
        Check(s.BloodRolls.Count == s.Level, "one Blood gain per level required");
        Check(s.BloodRolls[0] == cal.hitDie + s.ConModAtLevel[0], "1st-level Blood must be the full Hit Die + CON mod");
        for (int i = 1; i < s.BloodRolls.Count; i++)
        {
            int die = s.BloodRolls[i] - s.ConModAtLevel[i];
            Check(die >= 1 && die <= cal.hitDie, $"level {i + 1} Blood roll {die} outside 1..d{cal.hitDie}");
        }
        int rawhide = (s.Edges.Contains("Tough as Rawhide") || s.BonusCombatEdges.Contains("Tough as Rawhide")) ? s.Level : 0;
        Check(s.Blood == Math.Max(1, s.BloodRolls.Sum() + rawhide), "Blood total ≠ sum of per-level gains (+Rawhide)");

        // the reckoned numbers (Ch. III step 6)
        Check(s.Defense == 10 + Mod(s.Scores["DEX"]), $"Defense {s.Defense} ≠ 10 + DEX mod");
        Check(s.Fort == row.fort + Mod(s.Scores["CON"]), $"Fort {s.Fort} ≠ table {row.fort} + CON mod");
        Check(s.Ref == row.@ref + Mod(s.Scores["DEX"]), $"Ref {s.Ref} ≠ table {row.@ref} + DEX mod");
        Check(s.Will == row.will + Mod(s.Scores["RES"]), $"Will {s.Will} ≠ table {row.will} + RES mod");
        Check(s.Attack == row.atk, "Attack must be read straight from the Calling table");
        // The table is a transcription of the Player's Book spine (Ch. XIV). Re-derive it here so a
        // bad transcription in chargen.json can never pass silently — book and app cannot drift apart.
        Check(row.atk == AttackFor(cal.attackRank, s.Level),
            $"{cal.name} L{s.Level}: table attack {row.atk} ≠ {cal.attackRank} rank formula {AttackFor(cal.attackRank, s.Level)}");
        foreach (var (label, val) in new[] { ("Fort", row.fort), ("Ref", row.@ref), ("Will", row.will) })
            Check(val == StrongSave(s.Level) || val == WeakSave(s.Level),
                $"{cal.name} L{s.Level}: table {label} {val} is neither strong ({StrongSave(s.Level)}) nor weak ({WeakSave(s.Level)})");
        int stoneNerve = s.Edges.Contains("Stone Nerve") ? 2 * s.Level : 0;
        Check(s.NerveMax == s.Scores["RES"] + s.Level + stoneNerve, "Nerve ≠ RES score + level (+Stone Nerve)");
        Check(s.Grit == 3, "Grit must be 3");
        Check(s.Speed == 30 + (s.Edges.Contains("Fleet") ? 10 : 0), "Speed ≠ 30 (+Fleet)");

        // trained skills: Calling number + WIT mod (min 1) — the WIT of creation, before any
        // 5th/10th-level boost — with Origin grants riding free
        int witAtCreation = s.PreGiftScores["WIT"] + (org.gifts.TryGetValue("WIT", out var wg) ? wg : 0);
        int expectTrained = Math.Max(1, cal.trainedSkills + Mod(witAtCreation));
        int newFromIncreases = s.SkillRanks.Count - expectTrained - s.OriginSkills.Distinct().Count();
        int increases = new[] { 3, 5, 7, 9 }.Count(l => l <= s.Level);
        Check(newFromIncreases >= 0 && newFromIncreases <= increases,
            $"trained-skill count {s.SkillRanks.Count} outside Calling {cal.trainedSkills}+WIT rules");
        int steps = s.SkillRanks.Values.Sum(r => r - 1) + newFromIncreases;
        Check(steps <= increases, $"{steps} skill-increase steps but only {increases} earned");
        Check(s.SkillRanks.Values.All(r => r is >= 1 and <= 3), "illegal skill rank");
        Check(!s.SkillRanks.Values.Contains(3) || s.Level >= 7, "Master rank before 7th level");
        Check(!s.SkillRanks.Values.Contains(2) || s.Level >= 3, "Expert rank before 3rd level");
        foreach (var sk in s.OriginSkills) Check(s.SkillRanks.ContainsKey(sk), $"Origin skill {sk} not trained");
        foreach (var sk in s.SkillRanks.Keys) Check(D.skills.Any(k => k.name == sk), $"unknown skill {sk}");

        // features must be exactly the table's, cumulative
        var expectFeatures = cal.rows.Where(r => r.level <= s.Level)
            .SelectMany(r => r.features)
            .Where(f => f != "Edge" && !f.StartsWith("Sign learned") && !f.StartsWith("Stolen Wonder")).ToList();
        Check(s.Features.SequenceEqual(expectFeatures), "feature list diverges from the Calling table");

        // edges: count, prerequisites, faith bans
        int expectEdges = new[] { 1, 3, 5, 7, 9 }.Count(l => l <= s.Level);
        Check(s.Edges.Count == expectEdges, $"{s.Edges.Count} edges ≠ {expectEdges} earned (Ch. IX)");
        Check(cal.bonusCombatEdgeAtOdd ? s.BonusCombatEdges.Count == expectEdges : s.BonusCombatEdges.Count == 0,
            "bonus combat edges only for the Gunhand, one per odd level");
        var all = D.edges.Concat(D.callingEdges).ToList();
        var owned = s.Edges.Concat(s.BonusCombatEdges).ToList();
        Check(owned.Distinct().Count() == owned.Count, "duplicate edge");
        foreach (var name in owned)
        {
            var e = all.FirstOrDefault(x => x.name == name);
            if (e == null) { v.Add($"unknown edge {name}"); continue; }
            Check(!(e.notFaith && isFaith), $"{name} is barred to Callings of Faith");
            if (e.reqAbility != null) foreach (var kv in e.reqAbility) Check(s.Scores[kv.Key] >= kv.Value, $"{name} needs {kv.Key} {kv.Value}");
            if (e.reqEdge != null) Check(owned.Contains(e.reqEdge), $"{name} requires the {e.reqEdge} edge");
            if (e.reqTrained != null) Check(s.SkillRanks.ContainsKey(e.reqTrained), $"{name} requires training in {e.reqTrained}");
            if (e.calling != null)
            {
                Check(e.calling == s.Calling, $"{name} belongs to the {e.calling}");
                if (e.reqFeature != null) Check(s.Features.Any(f => f.StartsWith(e.reqFeature)), $"{name} requires the {e.reqFeature} feature");
            }
        }
        foreach (var g in s.BonusCombatEdges)
            Check(all.First(x => x.name == g).group == "Gun", "Gunhand's Edge picks must be combat (Gun) edges");

        // Signs: the Old Dark works them; Faith never; Hedge Magic adds one; counts per table
        Check(!(cal.signsKnownAt != null && owned.Contains("Hedge Magic")),
            "Hedge Magic on a Calling that already has the Signs feature");
        int expectSigns = cal.signsKnownAt != null ? cal.signsKnownAt[s.Level.ToString()] : 0;
        if (owned.Contains("Hedge Magic")) expectSigns += 1;
        expectSigns = Math.Min(expectSigns, D.signs.Count);
        Check(s.SignsKnown.Count == expectSigns, $"{s.SignsKnown.Count} signs ≠ {expectSigns} allowed");
        Check(!(isFaith && s.SignsKnown.Count > 0), "a Calling of Faith may never work a Sign (Ch. XIII)");
        Check(s.SignsKnown.Distinct().Count() == s.SignsKnown.Count, "duplicate sign");
        foreach (var sg in s.SignsKnown) Check(D.signs.Any(x => x.name == sg), $"unknown sign {sg}");

        // the Mark: Hexer & Dark Cultist begin at 1; Came Back Wrong adds 1; Touched adds 1; Witch starts clean
        int expectMark = org.startMark + cal.startMark + (owned.Contains("Touched") ? 1 : 0);
        Check(s.Mark == expectMark, $"Mark {s.Mark} ≠ origin {org.startMark} + calling {cal.startMark} + Touched");

        // subpath at 3rd
        if (s.Level >= 3 && cal.subpath != null && cal.subpath.options.Count > 0)
            Check(cal.subpath.options.Any(o => o.name == s.Subpath), $"subpath \"{s.Subpath}\" not among the {cal.subpath.section}");
        else Check(s.Subpath == null, "subpath before 3rd level");

        // coin: rolled within the Calling's dice, purchases priced as printed, ledger balances
        Check(s.CoinRolled >= cal.coin.dice * cal.coin.mult && s.CoinRolled <= cal.coin.dice * 6 * cal.coin.mult
              && s.CoinRolled % cal.coin.mult == 0, $"starting coin ${s.CoinRolled} outside {cal.coin.dice}d6 × ${cal.coin.mult}");
        double spent = 0;
        foreach (var g in s.Gear)
            if (D.gearPrices.TryGetValue(g, out var c)) spent += c;
        foreach (var w in s.WeaponsCarried)
        {
            var m = System.Text.RegularExpressions.Regex.Match(w, @"— \$(\d+(\.\d+)?)$");
            // The price is written with a '.' decimal point, so parse it as one. The shipped
            // app sets InvariantGlobalization and would be fine either way, but the smoke rig
            // doesn't, and on a comma-decimal machine the bare Parse throws FormatException
            // and takes the whole validation pass down with it.
            if (m.Success) spent += double.Parse(m.Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture);
        }
        Check(Math.Abs(s.CoinRolled - spent - s.CoinLeft) < 0.001, $"coin ledger: rolled {s.CoinRolled}, spent {spent}, left {s.CoinLeft}");
        Check(s.CoinLeft >= 0, "spent more than the rolled coin");

        return v;
    }

    // ============================================================ RENDER (Appendix D pattern)
    public static string Render(CharacterSheet s)
    {
        var cal = D.callings.First(c => c.name == s.Calling);
        var org = D.origins.First(o => o.name == s.Origin);
        var sb = new StringBuilder();
        string M(int m) => m >= 0 ? "+" + m : "−" + (-m);

        sb.AppendLine($"{s.Name} — {s.Calling} · {org.name}");
        sb.AppendLine($"Level {s.Level}{(string.IsNullOrEmpty(s.Gender) ? "" : " · " + s.Gender.ToLowerInvariant())} · {s.Method} · {s.Compass}"
                      + (s.HandTweaked ? " · hand-tweaked" : ""));
        sb.AppendLine();
        sb.AppendLine(string.Join(" · ", Ab.Select(a => $"{a} {s.Scores[a]} ({M(Mod(s.Scores[a]))})")));
        sb.AppendLine();
        sb.AppendLine($"Blood {s.Blood} · Defense {s.Defense} · Saves Fort {M(s.Fort)}, Ref {M(s.Ref)}, Will {M(s.Will)} · Nerve {s.NerveMax} · Grit {s.Grit} · Speed {s.Speed} ft"
                      + (s.Mark > 0 ? $" · Mark {s.Mark}" : ""));
        int gunAtk = s.Attack + Mod(s.Scores["DEX"]), melAtk = s.Attack + Mod(s.Scores["STR"]);
        sb.AppendLine($"Attack {M(s.Attack)} (guns {M(gunAtk)} with DEX · melee {M(melAtk)} with STR)");
        if (s.WeaponsCarried.Count > 0) foreach (var w in s.WeaponsCarried) sb.AppendLine("   " + w);
        if (cal.signsKnownAt != null)
            sb.AppendLine($"Sign DC {10 + s.Level / 2 + Mod(s.Scores["RES"])} (10 + half level + RES mod)");
        else if (s.SignsKnown.Count > 0)
            sb.AppendLine($"Sign DC {10 + Mod(s.Scores["RES"])} (Hedge Magic — no Signs feature, so no level added)");
        if (s.PoolLine != null) sb.AppendLine(s.PoolLine);
        sb.AppendLine();

        string Rank(int r) => r switch { 3 => " (Master)", 2 => " (Expert)", _ => "" };
        sb.AppendLine("TRAINED — " + string.Join(", ", s.SkillRanks.OrderByDescending(kv => kv.Value).ThenBy(kv => kv.Key)
            .Select(kv => kv.Key + Rank(kv.Value))));
        sb.AppendLine();

        sb.AppendLine("FEATURES");
        foreach (var f in s.Features)
        {
            string key = cal.featureDescs.Keys.FirstOrDefault(k => f.StartsWith(k))
                      ?? cal.featureDescs.Keys.FirstOrDefault(k => k.StartsWith(f.Split(" +")[0].Split(" 1d")[0]))
                      ?? cal.featureDescs.Keys.FirstOrDefault(k => k.Contains(f));
            string desc = key != null ? cal.featureDescs[key] : null;
            sb.AppendLine("   " + f + (desc != null ? " — " + FirstSentence(desc) : ""));
        }
        if (s.Subpath != null)
        {
            var opt = cal.subpath.options.First(o => o.name == s.Subpath);
            sb.AppendLine($"   {cal.subpath.section}: {opt.name} — {FirstSentence(opt.boon)}");
        }
        if (s.CallingChoice != null) sb.AppendLine("   " + s.CallingChoice);
        sb.AppendLine();

        sb.AppendLine("EDGES");
        var allEdges = D.edges.Concat(D.callingEdges).ToList();
        foreach (var e in s.Edges) sb.AppendLine("   " + e + " — " + allEdges.First(x => x.name == e).desc);
        foreach (var e in s.BonusCombatEdges) sb.AppendLine("   " + e + " (Gunhand's Edge) — " + allEdges.First(x => x.name == e).desc);
        sb.AppendLine();

        if (s.SignsKnown.Count > 0)
        {
            sb.AppendLine("SIGNS KNOWN");
            foreach (var sg in s.SignsKnown)
            { var d = D.signs.First(x => x.name == sg); sb.AppendLine($"   {d.name} ({d.cost}) — {FirstSentence(d.desc)}"); }
            sb.AppendLine();
        }

        sb.AppendLine($"ORIGIN — {org.name}: {org.line}");
        sb.AppendLine("   Boon: " + org.boon);
        sb.AppendLine("   Burden: " + org.burden);
        sb.AppendLine();

        sb.AppendLine($"GEAR   (rolled ${s.CoinRolled:0} {cal.coin.note}{(cal.coin.note != "" ? ", " : "")}${s.CoinLeft:0.##} left)");
        foreach (var g in s.Gear) sb.AppendLine("   " + g);
        sb.AppendLine();

        sb.AppendLine("THE FOUR QUESTIONS");
        sb.AppendLine("   Lost:   " + s.Lost);
        sb.AppendLine("   Seen:   " + s.Seen);
        sb.AppendLine("   Vice:   " + s.Vice);
        sb.AppendLine("   Moving: " + s.Moving);
        return sb.ToString();
    }

    static string FirstSentence(string t)
    {
        if (string.IsNullOrEmpty(t)) return "";
        int i = t.IndexOf(". ");
        return i > 0 && i < 220 ? t.Substring(0, i + 1) : (t.Length > 220 ? t.Substring(0, 220) + "…" : t);
    }
}
