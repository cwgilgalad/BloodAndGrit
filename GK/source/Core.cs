using System.ComponentModel;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace BloodAndGritKeeper;

// ============================================================ HOW THE TABLE RUNS

/// <summary>How this table is being run — chosen at launch, changeable from the menu.
/// <list type="bullet">
/// <item><b>Player</b> — a player's own view: build and run a character, roll dice, look up the rules;
/// the Keeper's tabs (the Bestiary, encounters, the tracker, the map, the campaign threads) are put away.</item>
/// <item><b>KeeperDice</b> — a Keeper who runs the game with physical dice and the books. The app is the
/// tracker and the referee: the Keeper enters the die they rolled, and GritKeeper reads the four
/// degrees, the Multiple Attack Penalty, the damage, the DR, and keeps the Blood and the Beats.</item>
/// <item><b>KeeperEngine</b> — a Keeper leaning on the engine, so the game can be played anywhere there
/// are no dice and the players can't keep their own ledgers. GritKeeper rolls everything.</item>
/// </list></summary>
public enum RunMode { Player, KeeperDice, KeeperEngine }

/// <summary>The one small preference that outlives a session: how the last table chose to run, and
/// whether to skip the chooser next time. Kept beside the exe in prefs.json; a missing or unreadable
/// file just means "ask, defaulting to the engine".</summary>
public static class Prefs
{
    public class Data
    {
        public string Mode { get; set; } = "KeeperEngine";
        public bool Remember { get; set; }

        /// What the Keeper wants each KIND of map marker inked in, where that differs from the
        /// book. A single marker's own color travels in the session file with the marker; this
        /// is the standing choice that outlives any one session.
        public Dictionary<string, int> MarkerInk { get; set; } = new();
    }

    static string PathTo => Path.Combine(AppContext.BaseDirectory, "prefs.json");

    public static Data Load()
    {
        try { if (File.Exists(PathTo)) return JsonSerializer.Deserialize<Data>(File.ReadAllText(PathTo)) ?? new(); }
        catch { }
        return new();
    }

    public static RunMode ModeOf(Data d) => Enum.TryParse<RunMode>(d?.Mode, out var m) ? m : RunMode.KeeperEngine;

    public static void Save(Data d)
    {
        try { File.WriteAllText(PathTo, JsonSerializer.Serialize(d ?? new(), new JsonSerializerOptions { WriteIndented = true })); }
        catch { }
    }

    /// Set the run mode without disturbing anything else in the file. Writing a freshly-built
    /// Data here would silently drop every preference this call doesn't happen to know about —
    /// which is how a Keeper's marker colors would vanish the first time they changed modes.
    public static void Save(RunMode mode, bool remember)
    {
        var d = Load();
        d.Mode = mode.ToString();
        d.Remember = remember;
        Save(d);
    }
}

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

    // Built once. These are computed properties read per creature per encounter/tracker
    // operation, and the static Regex.Match overload only reaches its pattern cache after
    // re-hashing the pattern string on every single call.
    static readonly System.Text.RegularExpressions.Regex WillRe =
        new(@"Will\s*([+\-]\d+)", System.Text.RegularExpressions.RegexOptions.Compiled);

    public int BloodValue => Rules.FirstInt(blood, 10);
    public int DefenseValue => Rules.FirstInt(defense, 13);
    public int WillValue
    {
        get { var m = WillRe.Match(saves ?? ""); return m.Success ? int.Parse(m.Groups[1].Value) : 0; }
    }
    public override string ToString() => $"{name}  ·  T{Rules.Roman(tier)}";
}

public class PartyMember : INotifyPropertyChanged
{
    // A stable identity that survives a rename. Combatant.PcId points at it, so the posse↔tracker
    // Blood mirror follows a soul even after the Keeper renames them, and two same-named souls
    // never collapse to one row. Assigned once; old saves without it are backfilled on load.
    public string Id { get; set; } = Guid.NewGuid().ToString("N");

    string _name = "New Soul", _calling = "", _gender = "", _notes = "";
    int _level = 1, _bloodCur = 10, _bloodMax = 10, _defense = 12;
    int _fort, _ref, _will, _nerveCur = 11, _nerveMax = 11, _grit = 3, _mark, _taint, _res = 10;
    int _poolCur, _poolMax; string _poolName = "";

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
    // The faith/sign pool a caster or believer spends (Grace, Conviction, Breath, Vital Breath,
    // Zeal…). Empty name and 0 max for the mundane. Refreshed to max at a full rest / dawn.
    public string PoolName { get => _poolName; set { _poolName = value ?? ""; On(); } }
    public int PoolCur { get => _poolCur; set { _poolCur = Math.Clamp(value, 0, 99); On(); } }
    public int PoolMax { get => _poolMax; set { _poolMax = Math.Clamp(value, 0, 99); On(); } }
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
    string _name = "", _conditions = "", _ref = "", _pcId = "";
    int _init, _bloodCur, _bloodMax, _defense, _beats = 3, _mapStep = 1;
    bool _isPC, _acting;

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
    // Links a PC row back to its PartyMember.Id (empty for foes and hand-entered rows), so the
    // Blood mirror survives a rename. Falls back to Name-match for legacy rows that lack it.
    public string PcId { get => _pcId; set { _pcId = value; On(); } }
    // The Iron Code turn state (Ch. XI): three Beats to spend, and which Strike this turn is next
    // (1 = clean, 2 = second at MAP, 3 = third). Reset when the combatant's turn comes round.
    public int Beats { get => _beats; set { _beats = Math.Clamp(value, 0, 9); On(); } }
    public int MapStep { get => _mapStep; set { _mapStep = Math.Clamp(value, 1, 9); On(); } }
    /// <summary>Whose turn it is right now. Turn state like the Beats and the MAP step, and worth
    /// keeping for the same reason: "Begin turn" changes numbers a Keeper can't see moving unless
    /// the table lights the row it happened to.</summary>
    public bool Acting { get => _acting; set { _acting = value; On(); } }
    [JsonIgnore] public bool Down => _bloodCur <= 0;

    /// <summary>What the NEXT Strike this turn costs in MAP, in one word for the tracker. An Agile
    /// weapon softens it to −4/−8, which the Strike dialog figures once a weapon is picked; this is
    /// the plain step, so a Keeper glancing at the field knows whether the shot is still clean.</summary>
    [JsonIgnore] public string NextStrike => _mapStep <= 1 ? "clean" : _mapStep == 2 ? "−5" : "−10";

    /// <summary>Start this combatant's turn: Beats back to three, the next Strike clean, and the
    /// row lit as the one acting. Clearing everyone else is the caller's business — the model has
    /// no idea who else is on the field.</summary>
    public void BeginTurn() { Beats = 3; MapStep = 1; Acting = true; }

    /// <summary>Is this tracker row the given posse soul? By the stable PcId when it has one, else
    /// by Name — so a rename never breaks the link, and two same-named souls stay distinct.</summary>
    public bool IsSoul(PartyMember p)
        => _isPC && p != null && (!string.IsNullOrEmpty(_pcId) ? _pcId == p.Id : _name == p.Name);
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

    /// This one marker's own ink, if the Keeper picked one — otherwise <see cref="MapInk.Unset"/>
    /// and it takes its kind's color. Four riders all drawn verdigris are four dots the table
    /// can't tell apart, which is the whole reason a marker can break ranks. Saved with the
    /// marker, so a soul who has been the blue one all campaign is still blue next session.
    public int Argb { get; set; }
}

/// <summary>The map's marker inks: what each kind is drawn in by default, what the Keeper may have
/// chosen instead, and the palette the right-click menu offers. Kept in one place so the preview,
/// the menu, and the saved preference can't drift apart — and kept in plain ARGB ints rather than
/// <c>Color</c> so nothing here needs System.Drawing to be read or tested.</summary>
public static class MapInk
{
    public const int Unset = 0;   // "the Keeper hasn't said" — fall back to the kind's color

    // The book's own inks: verdigris for the posse, gold for whoever is neither friend nor
    // foe yet, blood for what means to kill them. These match MainForm's palette by value;
    // they're written out here because Core.cs has no business referencing the shell.
    public const int Verdigris = unchecked((int)0xFF3C6054);
    public const int Gold      = unchecked((int)0xFF967432);
    public const int BloodRed  = unchecked((int)0xFF781616);

    /// The color a kind is drawn in before anyone changes anything. An unknown kind reads as
    /// trouble, which is the safer way to be wrong.
    public static int BookColor(string kind) => kind switch
    {
        "posse" => Verdigris,
        "npc"   => Gold,
        _       => BloodRed,
    };

    // What the Keeper set instead, by kind. Loaded from prefs.json at startup and written back
    // when it changes; empty means every kind is still in the book's ink.
    static readonly Dictionary<string, int> kindInk = new(StringComparer.OrdinalIgnoreCase);

    public static int KindColor(string kind)
        => kind != null && kindInk.TryGetValue(kind, out int c) && c != Unset ? c : BookColor(kind);

    public static void SetKindColor(string kind, int argb)
    {
        if (string.IsNullOrEmpty(kind)) return;
        if (argb == Unset || argb == BookColor(kind)) kindInk.Remove(kind);   // back to the book
        else kindInk[kind] = argb;
    }

    /// Only the kinds that actually differ from the book, so prefs.json stays a record of
    /// decisions rather than a copy of the defaults.
    public static Dictionary<string, int> KindColors() => new(kindInk);

    public static void LoadKindColors(Dictionary<string, int> saved)
    {
        kindInk.Clear();
        if (saved == null) return;
        foreach (var kv in saved) SetKindColor(kv.Key, kv.Value);
    }

    /// What a given marker is drawn in: its own ink if it has one, else its kind's.
    public static int Of(MapMarker mk)
        => mk == null ? BookColor(null) : mk.Argb != Unset ? mk.Argb : KindColor(mk.Kind);

    /// The choices the menu offers. Ten, because a posse and its trouble rarely need more, and
    /// every one of them dark enough to read as a filled dot on the survey's cream paper.
    public static readonly (string name, int argb)[] Palette =
    {
        ("Verdigris", Verdigris),
        ("Blood",     BloodRed),
        ("Gold",      Gold),
        ("Indigo",    unchecked((int)0xFF344678)),
        ("Rust",      unchecked((int)0xFF96461E)),
        ("Plum",      unchecked((int)0xFF5A2A52)),
        ("Slate",     unchecked((int)0xFF44505A)),
        ("Moss",      unchecked((int)0xFF4A6B2A)),
        ("Copper",    unchecked((int)0xFF8C5A2A)),
        ("Ink",       unchecked((int)0xFF261C14)),
    };

    /// The palette's name for a color, or its hex if it isn't one of ours — so a menu can always
    /// say what's currently set without having to guess.
    public static string NameOf(int argb)
    {
        foreach (var (name, c) in Palette) if (c == argb) return name;
        return Hex(argb);
    }

    /// "#rrggbb", which is what both the SVG writer and the PDF writer speak. Alpha is dropped:
    /// map primitives carry their opacity separately, and a marker is never drawn see-through.
    public static string Hex(int argb) => $"#{(argb & 0xFFFFFF):x6}";
}

// What the posse rides, drives, or takes passage on — a saddle horse, a freight wagon, the
// stage, a ferry, a sternwheeler, the cars. They take damage like anything else (a wagon is
// what a Tier-III thing goes for first), they carry weight and people, and they move at their
// own rate, so they're tracked rather than remembered. Built from the Data/rides.json roster
// but free to be edited afterward — a horse with a name and a limp is the point.
public class Ride : INotifyPropertyChanged
{
    string _name = "", _type = "", _kind = "mount", _rider = "", _notes = "";
    int _bloodCur = 10, _bloodMax = 10, _defense = 12, _capacity = 1;
    string _speed = "";

    public event PropertyChangedEventHandler PropertyChanged;
    void On([System.Runtime.CompilerServices.CallerMemberName] string p = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(p));

    /// What it's called at this table — "Deuteronomy", "the Concord coach".
    public string Name { get => _name; set { _name = value; On(); } }
    /// Which entry in the roster it was built from — "Saddle Horse", "Stagecoach".
    public string Type { get => _type; set { _type = value; On(); } }
    /// "mount" (it breathes) or "vehicle" (it doesn't) — sets how a Keeper treats a wound.
    public string Kind { get => _kind; set { _kind = value; On(); } }
    /// The soul in the saddle or holding the lines; empty when it's standing in the corral.
    public string Rider { get => _rider; set { _rider = value; On(); } }
    public int BloodCur { get => _bloodCur; set { _bloodCur = Math.Clamp(value, 0, 9999); On(); OnDown(); } }
    public int BloodMax { get => _bloodMax; set { _bloodMax = Math.Clamp(value, 1, 9999); On(); } }
    public int Defense { get => _defense; set { _defense = Math.Clamp(value, 1, 40); On(); } }
    /// How fast, in the book's own words — "40 ft, gallop 120 ft", "as the river runs".
    public string Speed { get => _speed; set { _speed = value; On(); } }
    /// How many it carries — riders for a mount, passengers for a vehicle.
    public int Capacity { get => _capacity; set { _capacity = Math.Clamp(value, 0, 999); On(); } }
    public string Notes { get => _notes; set { _notes = value; On(); } }

    void OnDown() => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(Down)));
    /// A mount at 0 Blood is down; a vehicle at 0 is wrecked. Either way it isn't going anywhere.
    [JsonIgnore] public bool Down => _bloodCur <= 0;
    [JsonIgnore] public bool IsMount => _kind == "mount";
}

/// One entry in the roster the Keeper builds rides from — the printed animal or rig, before
/// a table gives it a name and a history.
public class RideTemplate
{
    public string name { get; set; } = "";
    public string kind { get; set; } = "mount";
    public int blood { get; set; } = 10;
    public int defense { get; set; } = 12;
    public string speed { get; set; } = "";
    public int capacity { get; set; } = 1;
    public string notes { get; set; } = "";
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
    public List<Ride> Rides { get; set; } = new();
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

    static readonly System.Text.RegularExpressions.Regex FirstIntRe =
        new(@"\d+", System.Text.RegularExpressions.RegexOptions.Compiled);

    public static int FirstInt(string s, int fallback)
    {
        var m = FirstIntRe.Match(s ?? "");
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

    /// How a costed encounter stands against the budget. Lives here, not in the Encounter tab, so
    /// the words and the color the tab shows are decided in one place the smoke rig can hold to
    /// the book's rule — spend the budget exactly and the fight is fair; overspend and you had
    /// better mean it (Keeper's Book Ch. IV).
    public enum Weight { Empty, Under, Exact, Over, WellOver }

    public static Weight BudgetBand(int spend, int budget) =>
        spend <= 0            ? Weight.Empty :
        spend <  budget       ? Weight.Under :
        spend == budget       ? Weight.Exact :
        spend <= budget + 4   ? Weight.Over :
                                Weight.WellOver;

    public static string BudgetVerdict(int spend, int budget) => BudgetBand(spend, budget) switch
    {
        Weight.Empty    => "Empty — add creatures above, or send them over from the Bestiary tab.",
        Weight.Under    => "Under budget — a fight they should win.",
        Weight.Exact    => "ON BUDGET — a fair, hard fight.",
        Weight.Over     => "Over budget — mean. Somebody bleeds.",
        _               => "WELL over budget — you had better mean it.",
    };
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

        Rides = JsonSerializer.Deserialize<List<RideTemplate>>(ReadData("rides.json"), opts) ?? new();
    }

    /// The roster of mounts and vehicles a Keeper can put in the corral or the yard.
    public static List<RideTemplate> Rides { get; private set; } = new();

    /// Build a working ride from its roster entry. The Keeper renames it afterward — a horse
    /// with a name is a horse the table will miss.
    public static Ride MakeRide(string type)
    {
        var t = Rides.Find(r => string.Equals(r.name, type, StringComparison.OrdinalIgnoreCase));
        if (t == null) return new Ride { Name = type, Type = type };
        return new Ride
        {
            Name = t.name, Type = t.name, Kind = t.kind,
            BloodMax = t.blood, BloodCur = t.blood, Defense = t.defense,
            Speed = t.speed, Capacity = t.capacity, Notes = t.notes
        };
    }

    /// <summary>The name a new ride should take when one of that name is already in the corral:
    /// the stem, then the lowest free number after it. Counting how many of a TYPE are standing
    /// there isn't the same thing — sell the second of three horses and the count says 2 again,
    /// which collides with the horse still in the corral. Pure, so the smoke rig can prove it.</summary>
    public static string FreeRideName(IEnumerable<string> taken, string stem)
    {
        var used = new HashSet<string>(taken ?? Enumerable.Empty<string>(), StringComparer.OrdinalIgnoreCase);
        if (!used.Contains(stem)) return stem;
        for (int n = 2; ; n++)
        {
            string candidate = $"{stem} {n}";
            if (!used.Contains(candidate)) return candidate;
        }
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
