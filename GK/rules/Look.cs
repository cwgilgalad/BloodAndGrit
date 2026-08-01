using System.Text.Json;
using System.Text.Json.Serialization;

namespace BloodAndGritKeeper;

// ============================================================ WHAT A SOUL LOOKS LIKE
// The seventh headless file, and the first one that is not the books' rules. Chapter III makes a
// person out of numbers and the Four Questions and then stops, because a book is right to leave a
// face to the table — and a Keeper who needs one NOW, with five people waiting, is not helped by
// being left to it. So the app draws one.
//
// Nothing in here is worth a point. It touches no number, gates nothing, and is hand-editable
// everywhere it is shown; a soul with no look rolled is a soul in perfectly good standing. The
// books' standing line about the peoples of the West holds here as it holds there: they appear as
// people, described and never costed, and the invented dark is never pinned to a living one.
//
// The draws are CONDITIONED rather than shuffled, which is the whole craft of it. Complexion, hair
// and eyes come out of one people's own lists; every garment comes out of ONE style's wardrobe,
// and the style is drawn against the Calling. Six independent lists would give you a Norwegian
// wearing a queue and a charro jacket over mining boots — technically random, and instantly
// recognisable as a machine talking.

/// <summary>One row of Data/appearance.json's peoples list. Weighted, because the frontier was
/// not evenly divided and a generator that draws a Basque as often as a Texan is not describing
/// this country.</summary>
public class LkPeople
{
    public string name { get; set; }
    public int weight { get; set; } = 1;
    public List<string> complexions { get; set; } = new();
    public List<string> hair { get; set; } = new();
    public List<string> eyes { get; set; } = new();
}

/// <summary>One whole way of dressing, wardrobe and all. The garment lists belong to the style
/// rather than to the file, which is what keeps an outfit coherent.</summary>
public class LkStyle
{
    public string name { get; set; }
    public string note { get; set; }
    public List<string> hats { get; set; } = new();
    public List<string> coats { get; set; } = new();
    public List<string> shirts { get; set; } = new();
    public List<string> legs { get; set; } = new();
    public List<string> boots { get; set; } = new();
    public List<string> extras { get; set; } = new();
}

public class LookData
{
    public List<LkPeople> peoples { get; set; } = new();
    public List<string> heights { get; set; } = new();
    public List<string> frames { get; set; } = new();
    public List<string> bearings { get; set; } = new();
    public List<string> faces { get; set; } = new();
    public List<string> marks { get; set; } = new();
    public List<string> voices { get; set; } = new();
    public List<string> hairStyles { get; set; } = new();
    public List<string> facialHair { get; set; } = new();
    public List<string> wear { get; set; } = new();
    public List<string> details { get; set; } = new();
    public List<LkStyle> styles { get; set; } = new();
    /// <summary>Calling → the styles that Calling tends toward. A tendency, never a rule: see
    /// <see cref="Look.StyleFor"/> for how often the country surprises you.</summary>
    public Dictionary<string, List<string>> callingStyles { get; set; } = new();
}

/// <summary>A soul's physical description, their dress, and the one thing you remember about
/// them. Plain auto-properties so the whole of it rides in session.json with the rest of the
/// sheet, and every field is free text so a player who has their own idea can simply type it.
///
/// Every field may legitimately be empty — an old save has none of them, and a Keeper is allowed
/// to clear any of them — so nothing here may assume a value is present. <see cref="Any"/> is the
/// one question worth asking before showing it.</summary>
public class SoulLook
{
    /// <summary>Where their people came from. Description, never a stat line: nothing reads this
    /// but the eye.</summary>
    public string People { get; set; } = "";
    public string Height { get; set; } = "";
    public string Frame { get; set; } = "";
    public string Complexion { get; set; } = "";
    public string Hair { get; set; } = "";
    public string Eyes { get; set; } = "";
    public string Face { get; set; } = "";
    /// <summary>What the country has already taken off them — a scar, a brand, two missing
    /// fingers. Not a Lasting Injury: those are earned at the table and live on the soul's Scars.
    /// This is what they walked in with.</summary>
    public string Marks { get; set; } = "";
    public string Bearing { get; set; } = "";
    public string Voice { get; set; } = "";

    /// <summary>The name of the whole way of dressing — "vaquero", "circuit black" — that the
    /// five garments below were drawn out of.</summary>
    public string Style { get; set; } = "";
    public string Hat { get; set; } = "";
    public string Coat { get; set; } = "";
    public string Shirt { get; set; } = "";
    public string Legs { get; set; } = "";
    public string Boots { get; set; } = "";
    /// <summary>The state of the clothes, which says more about a life than the clothes do.</summary>
    public string Wear { get; set; } = "";
    /// <summary>The one thing a witness would describe first.</summary>
    public string Detail { get; set; } = "";

    /// <summary>Whether there is anything here at all. A soul made before this existed, or one
    /// whose look has been cleared by hand, has nothing to show and should be shown nothing —
    /// an empty box headed APPEARANCE reads as a bug in the sheet.</summary>
    [JsonIgnore]
    public bool Any => !string.IsNullOrWhiteSpace(People) || !string.IsNullOrWhiteSpace(Face)
        || !string.IsNullOrWhiteSpace(Style) || !string.IsNullOrWhiteSpace(Detail)
        || !string.IsNullOrWhiteSpace(Frame) || !string.IsNullOrWhiteSpace(Hair);

    static string Join(params string[] parts) =>
        string.Join(" · ", parts.Where(p => !string.IsNullOrWhiteSpace(p)));

    /// <summary>The body, as one line. Empty fields drop out rather than leaving "· ·" behind,
    /// which is what a hand-cleared field used to produce.</summary>
    [JsonIgnore] public string BodyLine => Join(Height, Frame, Complexion, Hair, Eyes);

    /// <summary>The face and how they hold themselves.</summary>
    [JsonIgnore] public string FaceLine => Join(Face, Marks, Bearing, Voice);

    /// <summary>What they are wearing, in the order you would see it.</summary>
    [JsonIgnore] public string DressLine => Join(Hat, Coat, Shirt, Legs, Boots, Wear);

    /// <summary>One sentence for a tooltip, a log line, or a grid cell — the least a Keeper needs
    /// to describe somebody who has just walked in.</summary>
    [JsonIgnore]
    public string AtAGlance
    {
        get
        {
            string who = Join(Height, Frame, People);
            string wearing = string.IsNullOrWhiteSpace(Style) ? Hat : Style;
            return Join(who, string.IsNullOrWhiteSpace(wearing) ? "" : "in " + wearing, Detail);
        }
    }
}

// ============================================================ THE GENERATOR
public static class Look
{
    public static LookData D { get; private set; }

    /// <summary>Read Data/appearance.json. Called beside <see cref="CharGen.Load"/>; everything
    /// here tolerates a missing file by handing back an empty look rather than throwing, because
    /// a data file that failed to embed should cost a Keeper a description, not the app.</summary>
    public static void Load()
    {
        var json = Db.ReadDataFile("appearance.json");
        D = string.IsNullOrEmpty(json)
            ? new LookData()
            : JsonSerializer.Deserialize<LookData>(json, new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
              ?? new LookData();
    }

    static string Pick(List<string> l) => l is { Count: > 0 } ? l[Rules.Rng.Next(l.Count)] : "";

    /// <summary>A people, drawn against the weights. Falls through to an even draw if every
    /// weight is zero or missing, so a hand-edited data file can't produce an empty result.</summary>
    public static LkPeople People()
    {
        var ps = D?.peoples;
        if (ps is not { Count: > 0 }) return null;
        int total = ps.Sum(p => Math.Max(0, p.weight));
        if (total <= 0) return ps[Rules.Rng.Next(ps.Count)];
        int roll = Rules.Rng.Next(total);
        foreach (var p in ps)
        {
            roll -= Math.Max(0, p.weight);
            if (roll < 0) return p;
        }
        return ps[^1];
    }

    /// <summary>How much of the time a Calling dresses the way its Calling dresses. Four in five:
    /// high enough that a Preacher reads as a Preacher, low enough that the fifth one is a
    /// Preacher in a dead man's cavalry coat, which is the interesting one.</summary>
    public const int StyleTruePercent = 80;

    /// <summary>The way this Calling dresses — usually. An unknown or empty Calling draws from
    /// the whole wardrobe, which is also what an NPC with no Calling should get.</summary>
    public static LkStyle StyleFor(string calling)
    {
        var all = D?.styles;
        if (all is not { Count: > 0 }) return null;
        if (!string.IsNullOrWhiteSpace(calling)
            && D.callingStyles != null
            && D.callingStyles.TryGetValue(calling, out var prefs)
            && prefs is { Count: > 0 }
            && Rules.Rng.Next(100) < StyleTruePercent)
        {
            // A preference naming a style that is not in the file is a data error, not a crash:
            // fall through to the whole wardrobe rather than handing back null.
            var named = all.Where(s => prefs.Contains(s.name)).ToList();
            if (named.Count > 0) return named[Rules.Rng.Next(named.Count)];
        }
        return all[Rules.Rng.Next(all.Count)];
    }

    /// <summary>How often a soul carries a mark the country already put on them. Two in five —
    /// enough that a posse has one or two, rare enough that it still means something.</summary>
    public const int MarkedPercent = 40;

    /// <summary>Roll a whole look.</summary>
    /// <param name="gender">The soul's own word for it. Only one thing reads it: whether to draw
    /// facial hair, which is offered for "Man" and left alone otherwise — the frontier's own
    /// convention, not a rule about anybody, and every field is editable by hand precisely so the
    /// convention can be ignored.</param>
    /// <param name="calling">What they do for a living, which is most of what they wear.</param>
    public static SoulLook Roll(string gender, string calling = null)
    {
        var look = new SoulLook();
        if (D == null) Load();

        var people = People();
        if (people != null)
        {
            look.People = people.name;
            look.Complexion = Pick(people.complexions);
            look.Eyes = Pick(people.eyes);
            // Colour from the people, cut from the shared list: a braid and a shorn scalp are not
            // anybody's property, and keeping every cut in one place is what stops the file
            // needing twenty-eight copies of "cropped close to the skull".
            string colour = Pick(people.hair);
            string cut = Pick(D.hairStyles);
            look.Hair = string.IsNullOrEmpty(cut) ? colour : $"{colour}, {cut}";
        }
        look.Height = Pick(D.heights);
        look.Frame = Pick(D.frames);
        look.Face = Pick(D.faces);
        look.Bearing = Pick(D.bearings);
        look.Voice = Pick(D.voices);

        if (string.Equals(gender, "Man", StringComparison.OrdinalIgnoreCase))
        {
            string whiskers = Pick(D.facialHair);
            if (!string.IsNullOrEmpty(whiskers))
                look.Face = string.IsNullOrEmpty(look.Face) ? whiskers : $"{look.Face}, {whiskers}";
        }

        if (Rules.Rng.Next(100) < MarkedPercent) look.Marks = Pick(D.marks);

        var style = StyleFor(calling);
        if (style != null)
        {
            look.Style = style.name;
            look.Hat = Pick(style.hats);
            look.Coat = Pick(style.coats);
            look.Shirt = Pick(style.shirts);
            look.Legs = Pick(style.legs);
            look.Boots = Pick(style.boots);
            // The style's own extra and the file's shared detail are two different things — the
            // extra belongs to the outfit (a reata, a carbide lamp), the detail belongs to the
            // person (a tintype kept face-down). A soul gets one of each.
            string extra = Pick(style.extras);
            string detail = Pick(D.details);
            look.Detail = string.Join("; ", new[] { extra, detail }.Where(x => !string.IsNullOrWhiteSpace(x)));
        }
        else look.Detail = Pick(D.details);
        look.Wear = Pick(D.wear);

        return look;
    }
}
