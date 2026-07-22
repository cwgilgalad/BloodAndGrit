using System.ComponentModel;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace BloodAndGritKeeper;

// ============================================================ MODELS

public class Creature
{
    public string name { get; set; } = "";
    public string chapter { get; set; } = "";
    public string tierText { get; set; } = "";
    public int tier { get; set; }
    public string defense { get; set; } = "";
    public string blood { get; set; } = "";
    public string speed { get; set; } = "";
    public string saves { get; set; } = "";
    public string attacks { get; set; } = "";
    public string special { get; set; } = "";
    public string dread { get; set; } = "";
    public string puttingItDown { get; set; } = "";
    public string mark { get; set; } = "";
    public List<string> lore { get; set; } = new();
    public string found { get; set; } = "";
    public string keeperNote { get; set; } = "";
    public string witness { get; set; } = "";

    public int BloodValue => Rules.FirstInt(blood, 10);
    public int DefenseValue => Rules.FirstInt(defense, 13);
    public int WillValue
    {
        get { var m = System.Text.RegularExpressions.Regex.Match(saves, @"Will\s*([+\-]\d+)");
              return m.Success ? int.Parse(m.Groups[1].Value) : 0; }
    }
    public override string ToString() => $"{name}  ·  T{Rules.Roman(tier)}";
}

public class PartyMember : INotifyPropertyChanged
{
    string _name = "New Soul", _calling = "", _gender = "", _notes = "";
    int _level = 1, _bloodCur = 10, _bloodMax = 10, _defense = 12;
    int _fort, _ref, _will, _nerveCur = 11, _nerveMax = 11, _grit = 3, _mark, _taint, _res = 10;

    public event PropertyChangedEventHandler PropertyChanged;
    void On([System.Runtime.CompilerServices.CallerMemberName] string p = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(p));

    public string Name { get => _name; set { _name = value; On(); } }
    public string Calling { get => _calling; set { _calling = value; On(); } }
    public string Gender { get => _gender; set { _gender = value; On(); } }
    public int Level { get => _level; set { _level = Math.Clamp(value, 1, 20); On(); RecalcNerve(); } }
    public int RES { get => _res; set { _res = value; On(); RecalcNerve(); } }
    public int BloodCur { get => _bloodCur; set { _bloodCur = Math.Clamp(value, 0, 999); On(); } }
    public int BloodMax { get => _bloodMax; set { _bloodMax = Math.Clamp(value, 1, 999); On(); } }
    public int Defense { get => _defense; set { _defense = value; On(); } }
    public int Fort { get => _fort; set { _fort = value; On(); } }
    public int Ref { get => _ref; set { _ref = value; On(); } }
    public int Will { get => _will; set { _will = value; On(); } }
    public int NerveCur { get => _nerveCur; set { _nerveCur = Math.Clamp(value, 0, 999); On(); } }
    public int NerveMax { get => _nerveMax; set { _nerveMax = Math.Clamp(value, 1, 999); On(); } }
    public int Grit { get => _grit; set { _grit = Math.Clamp(value, 0, 9); On(); } }
    public int Mark { get => _mark; set { _mark = Math.Clamp(value, 0, 6); On(); } }
    public int Taint { get => _taint; set { _taint = Math.Clamp(value, 0, 4); On(); } }
    public string Notes { get => _notes; set { _notes = value; On(); } }

    // The full character sheet, when this soul came out of the New Soul tab (generated,
    // wizard-built, or tweaked). Null for hand-entered rows; the Ledger window shows a
    // half-filled sheet in that case. Rides along in session.json.
    public CharacterSheet Sheet { get; set; }

    // Nerve = RES score + level. Only auto-recalcs when RES is set (>0); otherwise honors manual NerveMax.
    void RecalcNerve()
    {
        if (_res <= 0) return;
        int max = _res + _level;
        bool wasFull = _nerveCur >= _nerveMax;
        NerveMax = max;
        if (wasFull) NerveCur = max;
        else if (_nerveCur > max) NerveCur = max;
    }
}

public class Combatant : INotifyPropertyChanged
{
    string _name = "", _conditions = "", _ref = "";
    int _init, _bloodCur, _bloodMax, _defense;
    bool _isPC;

    public event PropertyChangedEventHandler PropertyChanged;
    void On([System.Runtime.CompilerServices.CallerMemberName] string p = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(p));

    public string Name { get => _name; set { _name = value; On(); } }
    public int Init { get => _init; set { _init = value; On(); } }
    public int BloodCur { get => _bloodCur; set { _bloodCur = Math.Clamp(value, 0, 9999); On(); } }
    public int BloodMax { get => _bloodMax; set { _bloodMax = value; On(); } }
    public int Defense { get => _defense; set { _defense = value; On(); } }
    public bool IsPC { get => _isPC; set { _isPC = value; On(); } }
    public string Conditions { get => _conditions; set { _conditions = value; On(); } }
    public string Ref { get => _ref; set { _ref = value; On(); } }   // creature name for lookup, or ""
    [JsonIgnore] public bool Down => _bloodCur <= 0;
}

public class CampaignClock : INotifyPropertyChanged
{
    string _name = "New Thread"; int _filled; int _segments = 6;
    public event PropertyChangedEventHandler PropertyChanged;
    void On([System.Runtime.CompilerServices.CallerMemberName] string p = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(p));
    public string Name { get => _name; set { _name = value; On(); } }
    public int Filled { get => _filled; set { _filled = value; On(); } }
    public int Segments { get => _segments; set { _segments = value; On(); } }
}

// A tactical marker the Keeper drops on the Trail Map — a posse soul, an NPC, or a
// creature, dragged into position. Coordinates are in map-model space (MapModel.W/H),
// so markers hold their ground when the panel resizes. Rides in session.json.
public class MapMarker
{
    public string Label { get; set; } = "";
    public string Kind { get; set; } = "creature";   // "posse" | "npc" | "creature" — sets the color
    public float X { get; set; }
    public float Y { get; set; }
}

public class GameSession
{
    public List<PartyMember> Party { get; set; } = new();
    public List<CampaignClock> Clocks { get; set; } = new();
    public string Notes { get; set; } = "";
    public List<string> EncounterCreatures { get; set; } = new();
    public int PartyLevelHint { get; set; } = 2;
    public List<Combatant> Tracker { get; set; } = new();
    public int Round { get; set; } = 1;
    public List<MapMarker> MapMarkers { get; set; } = new();
}

// ============================================================ RULES & DICE

public static class Rules
{
    public static Random Rng { get; private set; } = new();
    // Seed the shared stream for deterministic runs (the first-launch demo posse), then
    // ReseedEntropy() to hand play back its unpredictable dice. See SeedDemo.
    public static void Reseed(int seed) => Rng = new Random(seed);
    public static void ReseedEntropy() => Rng = new Random();

    public static string Roman(int t) => t switch { 1=>"I",2=>"II",3=>"III",4=>"IV",5=>"V", _=>t.ToString() };

    public static int FirstInt(string s, int fallback)
    {
        var m = System.Text.RegularExpressions.Regex.Match(s ?? "", @"\d+");
        return m.Success ? int.Parse(m.Value) : fallback;
    }

    /// Threat-by-Tier benchmarks: Defense, Attack, Blood, HighSave, LowSave, Damage, DreadDC
    public static readonly (int def, int atk, int blood, int hi, int lo, string dmg, string dread)[] TierRow =
    {
        (13,  4, 12,  6, 2, "1d6+2", "— / 10–13"),
        (15,  6, 22,  8, 3, "1d8+3", "13"),
        (17,  9, 40, 11, 5, "2d6+4", "16"),
        (20, 13, 70, 15, 8, "2d8+6", "20"),
        (23, 17,110, 19,11, "3d8+8", "25"),
    };

    /// Nerve loss ladder by Dread severity tier (I..V → 1, 1d4, 1d6, 1d10, 1d10)
    public static (string label, Func<int> roll) NerveLoss(int tier) => tier switch
    {
        <= 1 => ("1",    () => 1),
        2    => ("1d4",  () => Rng.Next(1, 5)),
        3    => ("1d6",  () => Rng.Next(1, 7)),
        _    => ("1d10", () => Rng.Next(1, 11)),
    };

    /// Four degrees for a d20 check: returns (idx, degree, detail).
    /// idx is the ordered scale — 0=crit fail, 1=fail, 2=success, 3=crit success —
    /// so callers branch on the number, never on the display string.
    public static (int idx, string degree, string detail) FourDegrees(int die, int mod, int dc)
    {
        int total = die + mod;
        int idx = total >= dc ? (total >= dc + 10 ? 3 : 2) : (total <= dc - 10 ? 0 : 1);
        if (die == 20) idx = Math.Min(3, idx + 1);
        if (die == 1)  idx = Math.Max(0, idx - 1);
        string deg = idx switch { 3 => "CRITICAL SUCCESS", 2 => "Success", 1 => "Failure", _ => "CRITICAL FAILURE" };
        return (idx, deg, $"d20({die}) {(mod>=0?"+":"")}{mod} = {total} vs DC {dc}");
    }

    /// Parse and roll a dice expression: "2d6+3", "d20", "1d8+1d6+2"
    public static (int total, string breakdown) RollExpr(string expr)
    {
        var (total, breakdown, _) = RollExprFull(expr);
        return (total, breakdown);
    }

    /// Like RollExpr, but also hands back every individual die (sides, value, sign)
    /// so the table can watch the dice land, not just read the sum.
    public static (int total, string breakdown, List<(int sides, int value, int sign)> dice) RollExprFull(string expr)
    {
        expr = (expr ?? "").Replace(" ", "").ToLowerInvariant();
        var dice = new List<(int sides, int value, int sign)>();
        if (expr.Length == 0) return (0, "empty", dice);
        var parts = System.Text.RegularExpressions.Regex.Matches(expr, @"([+\-]?)(\d*)d(\d+)|([+\-]?\d+)(?![d\d])");
        int total = 0; var bits = new List<string>();
        foreach (System.Text.RegularExpressions.Match p in parts)
        {
            if (p.Groups[3].Success)
            {
                int sign = p.Groups[1].Value == "-" ? -1 : 1;
                int n = p.Groups[2].Value == "" ? 1 : int.Parse(p.Groups[2].Value);
                int d = int.Parse(p.Groups[3].Value);
                n = Math.Clamp(n, 1, 100); d = Math.Clamp(d, 2, 1000);
                var rolls = Enumerable.Range(0, n).Select(_ => Rng.Next(1, d + 1)).ToArray();
                total += sign * rolls.Sum();
                foreach (var r in rolls) dice.Add((d, r, sign));
                bits.Add($"{(sign<0?"-":"")}{n}d{d}[{string.Join(",", rolls)}]");
            }
            else if (p.Groups[4].Success)
            {
                int v = int.Parse(p.Groups[4].Value);
                total += v; bits.Add(v >= 0 ? $"+{v}" : v.ToString());
            }
        }
        if (bits.Count == 0) return (0, "could not parse", dice);
        return (total, string.Join(" ", bits), dice);
    }

    /// The Dice tab's expression-builder buttons. Clicking a die whose kind already ends
    /// the expression bumps its count ("2d6", not "1d6+1d6"); anything else joins with a +.
    /// count lets the × spinner add several at once (count 3 on "2d6" → "5d6").
    public static string ExprAddDie(string expr, int sides, int count = 1)
    {
        count = Math.Clamp(count, 1, 100);
        string t = (expr ?? "").Trim();
        var m = System.Text.RegularExpressions.Regex.Match(t, @"^(.*?)(\d*)d" + sides + "$");
        if (m.Success)
        {
            int n = m.Groups[2].Value.Length == 0 ? 1 : int.Parse(m.Groups[2].Value);
            return m.Groups[1].Value + (n + count) + "d" + sides;
        }
        if (t.Length == 0) return count + "d" + sides;
        if (t.EndsWith("+") || t.EndsWith("-")) return t + count + "d" + sides;
        return t + "+" + count + "d" + sides;
    }

    /// Digits and operators for the same buttons; a second operator click replaces the
    /// first, so the box can never hold "2d6+-".
    public static string ExprAppend(string expr, string tok)
    {
        string t = expr ?? "";
        if ((tok == "+" || tok == "-") && (t.EndsWith("+") || t.EndsWith("-"))) t = t[..^1];
        return t + tok;
    }

    /// Encounter cost of a creature vs the party: even=4, mook=1, standout=8.
    /// Party tier = ceil(level/2). A creature 2+ tiers above the party trips the safe-table rule.
    public static (int cost, string role, bool spoor) Cost(int creatureTier, int partyLevel)
    {
        int pt = Math.Max(1, (partyLevel + 1) / 2);
        if (creatureTier >= pt + 2) return (8, "BEYOND the party — sign & spoor only (safe-table rule)", true);
        if (creatureTier >  pt)     return (8, "Standout", false);
        if (creatureTier == pt)     return (4, "Even foe", false);
        return (1, "Mook", false);
    }
}

// ============================================================ DATA STORE

public static class Db
{
    public static List<Creature> Creatures { get; private set; } = new();
    public static Dictionary<string, List<string>> Simple { get; private set; } = new();
    public static Dictionary<string, List<string>> Terrain { get; private set; } = new();

    public static void Load()
    {
        var opts = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        Creatures = JsonSerializer.Deserialize<List<Creature>>(ReadData("creatures.json"), opts) ?? new();

        Simple = new(); Terrain = new();
        // tables.json is extracted verbatim from the books and may be regenerated wholesale;
        // tables_extra.json carries the app's own additions, so a re-extraction can't eat them.
        MergeTables(ReadData("tables.json"));
        MergeTables(ReadData("tables_extra.json"));
    }

    // The JSON data is EMBEDDED in the app assembly so the published exe is a TRUE single-file
    // standalone (one .exe, no Data/ folder needed beside it). Falls back to Data/ on disk for
    // the dev build and the smoke rig, whose assemblies don't carry the embedded copies.
    public static string ReadDataFile(string fileName) => ReadData(fileName);

    static string ReadData(string fileName)
    {
        var asm = typeof(Db).Assembly;
        var resName = System.Array.Find(asm.GetManifestResourceNames(),
            n => n.EndsWith(fileName, StringComparison.OrdinalIgnoreCase));
        if (resName != null)
        {
            using var s = asm.GetManifestResourceStream(resName);
            using var r = new StreamReader(s);
            return r.ReadToEnd();
        }
        string path = Path.Combine(AppContext.BaseDirectory, "Data", fileName);
        return File.Exists(path) ? File.ReadAllText(path) : null;
    }

    static void MergeTables(string json)
    {
        if (string.IsNullOrEmpty(json)) return;
        using var doc = JsonDocument.Parse(json);
        foreach (var prop in doc.RootElement.EnumerateObject())
        {
            if (prop.Name == "terrain")
            {
                foreach (var t in prop.Value.EnumerateObject())
                {
                    var list = Terrain.TryGetValue(t.Name, out var l) ? l : (Terrain[t.Name] = new());
                    list.AddRange(t.Value.EnumerateArray().Select(e => e.GetString() ?? ""));
                }
            }
            else
            {
                var list = Simple.TryGetValue(prop.Name, out var l) ? l : (Simple[prop.Name] = new());
                list.AddRange(prop.Value.EnumerateArray().Select(e => e.GetString() ?? ""));
            }
        }
    }

    public static string Pick(string table)
    {
        var l = Simple[table];
        return l[Rules.Rng.Next(l.Count)];
    }

    public static Creature Find(string name) =>
        Creatures.FirstOrDefault(c => c.name.Equals(name, StringComparison.OrdinalIgnoreCase));
}
