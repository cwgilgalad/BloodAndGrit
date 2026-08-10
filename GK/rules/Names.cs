using System.Text.Json;
using System.Text.Json.Serialization;

namespace BloodAndGritKeeper;

/// <summary>One title form — a grammatical shape with slots, e.g. <c>What {actor} {verb3}</c>.</summary>
public sealed class TitleForm
{
    public string Id { get; set; } = "";
    public string Pattern { get; set; } = "";
}

/// <summary>The naming stock, loaded from <c>Data/names.json</c>. App-side data, not a book
/// transcription — see the note at the top of the file.</summary>
public sealed class NameData
{
    public List<string> Spent { get; set; } = new();
    public List<TitleForm> TitleForms { get; set; } = new();

    public List<string> Adj { get; set; } = new();
    public List<string> Noun { get; set; } = new();
    public List<string> HardNoun { get; set; } = new();
    public List<string> BodyNoun { get; set; } = new();
    public List<string> Actor { get; set; } = new();
    public List<string> ActorP { get; set; } = new();
    public List<string> Motion3 { get; set; } = new();
    public List<string> Verb3 { get; set; } = new();
    public List<string> Verb { get; set; } = new();
    public List<string> Verbing { get; set; } = new();
    public List<string> Num { get; set; } = new();
    public List<string> Plural { get; set; } = new();
    public List<string> Poss { get; set; } = new();
    public List<string> Given { get; set; } = new();
    public List<string> Surname { get; set; } = new();

    public List<string> TownFirst { get; set; } = new();
    public List<string> TownSecond { get; set; } = new();
    public List<string> CityFirst { get; set; } = new();
    public List<string> CitySecond { get; set; } = new();
    public List<string> TitleFirst { get; set; } = new();
    public List<List<string>> TitleGeo { get; set; } = new();
    public List<string> LmOwner { get; set; } = new();
    public List<string> LmAdj { get; set; } = new();

    /// <summary>The slot name a template writes, mapped to the stock it draws from. One place, so
    /// a template naming a slot that does not exist is a startup failure rather than a title with
    /// a literal <c>{actor}</c> in it.</summary>
    [JsonIgnore]
    public IReadOnlyDictionary<string, List<string>> Slots => slots ??= new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase)
    {
        ["adj"] = Adj, ["noun"] = Noun, ["hardnoun"] = HardNoun, ["bodynoun"] = BodyNoun,
        ["actor"] = Actor, ["actorp"] = ActorP, ["motion3"] = Motion3,
        ["verb3"] = Verb3, ["verb"] = Verb, ["verbing"] = Verbing,
        ["num"] = Num, ["plural"] = Plural, ["poss"] = Poss, ["given"] = Given,
        ["surname"] = Surname, ["titlefirst"] = TitleFirst,
    };
    Dictionary<string, List<string>> slots;
}

/// <summary>Draws names that do not repeat themselves.
///
/// <para>Two different problems are being solved and they need different tools. <b>Breadth</b> is
/// the only defence ACROSS seeds — nothing one run remembers can stop two evenings drawing the
/// same word, so the pools in <c>names.json</c> are large. <b>Memory</b> is the defence WITHIN a
/// seed: a Namer spends every distinctive word it hands out and will not hand it out twice.</para>
///
/// <para>It spends <i>shapes</i> too, and that is the part that was actually broken. Modules I and
/// III shipped as "The Salt at Coffin Wells" and "The Reckoning of the Wells" — they collide on the
/// word <i>Wells</i>, and they collide again on the shape <c>The &lt;abstract noun&gt; &lt;prep&gt;
/// &lt;place&gt;</c>. Widening the word lists alone would have produced "The Ashes at Gallows Fork"
/// and "The Judgment of the Hollow", which is the same title twice in a better costume.</para>
///
/// <para><b>Exactly one <c>rng.Next</c> per draw.</b> A rejection-sampling loop would consume a
/// variable number of values, and MapGen's landmark stream (<c>rngLm</c>) names AND places from the
/// same Random — so a name that cost two rolls instead of one would silently move the rocks. The
/// draw picks a start index and then scans forward for the first unspent entry, which is one roll
/// whatever it finds.</para>
///
/// <para>Pure and deterministic: same seed and same exclusions, same names, every time. No ambient
/// state, no <c>Rules.Rng</c>, nothing carried between instances.</para></summary>
public sealed class Namer
{
    readonly Random rng;
    readonly HashSet<string> spentWords = new(StringComparer.OrdinalIgnoreCase);
    readonly HashSet<string> spentForms = new(StringComparer.Ordinal);

    /// <summary>Words that carry no identity, so two titles sharing one have not collided. "The
    /// Long Debt" and "The Cold Water" are different titles; "the" is not what makes them so.</summary>
    static readonly HashSet<string> Bland = new(StringComparer.OrdinalIgnoreCase)
    {
        "the", "a", "an", "of", "at", "and", "for", "to", "not", "own", "that", "where",
        "until", "what", "no", "something", "do", "in", "on", "by", "with", "from", "is",
        "his", "her", "their", "it", "its", "as", "or", "but", "so", "up", "out", "off",
    };

    /// <param name="seed">Same seed, same names. This is the whole point of the class.</param>
    /// <param name="alreadySpent">Words this run may not use — the stock's own <c>spent</c> list
    /// (words already on published work) plus anything the caller has committed to elsewhere.</param>
    public Namer(int seed, IEnumerable<string> alreadySpent = null)
    {
        rng = new Random(seed);
        if (alreadySpent != null)
            foreach (var s in alreadySpent) Spend(s);
    }

    /// <summary>The distinctive words in a phrase: everything that is not punctuation, a
    /// possessive, or a bland connective. "Widow's Bend" spends WIDOW and BEND.</summary>
    public static IEnumerable<string> Distinctive(string phrase)
    {
        if (string.IsNullOrWhiteSpace(phrase)) yield break;
        foreach (var raw in phrase.Split(new[] { ' ', '\t', '-', '—' }, StringSplitOptions.RemoveEmptyEntries))
        {
            var w = raw.Trim('.', ',', ':', ';', '!', '?', '"', '\'', '(', ')');
            int apos = w.IndexOf('\'');
            if (apos > 0) w = w.Substring(0, apos);          // Widow's -> Widow
            if (w.Length > 2 && !Bland.Contains(w)) yield return w;
        }
    }

    void Spend(string phrase)
    {
        foreach (var w in Distinctive(phrase)) spentWords.Add(w);
    }

    /// <summary>Mark a phrase used without drawing it — for a name that arrived from somewhere
    /// else (a book table, a Keeper's typing, a module already published) and which the rest of
    /// this run must not echo. Consumes no randomness, so it cannot shift a seeded sequence.</summary>
    public void Reserve(string phrase) => Spend(phrase);

    bool IsFree(string phrase) => !Distinctive(phrase).Any(spentWords.Contains);

    /// <summary>Has this run already used any distinctive word of <paramref name="phrase"/>?</summary>
    public bool WouldRepeat(string phrase) => !IsFree(phrase);

    /// <summary>Take one entry, preferring one whose words this run has not spent. Exactly one
    /// <c>rng.Next</c> — see the class note.</summary>
    public string Draw(IReadOnlyList<string> pool)
    {
        if (pool == null || pool.Count == 0) return "";
        int start = rng.Next(pool.Count);
        for (int i = 0; i < pool.Count; i++)
        {
            var cand = pool[(start + i) % pool.Count];
            if (IsFree(cand)) { Spend(cand); return cand; }
        }
        // Every entry is spent. Repeat rather than fail: a name is always better than none, and a
        // pool this exhausted means the caller asked for more names than the stock can distinguish.
        Spend(pool[start]);
        return pool[start];
    }

    /// <summary>Draw a template, preferring a shape this run has not used. One roll, like Draw.</summary>
    public TitleForm DrawForm(IReadOnlyList<TitleForm> forms)
    {
        if (forms == null || forms.Count == 0) return new TitleForm { Id = "adj-noun", Pattern = "{adj} {noun}" };
        int start = rng.Next(forms.Count);
        for (int i = 0; i < forms.Count; i++)
        {
            var f = forms[(start + i) % forms.Count];
            if (spentForms.Add(f.Id)) return f;
        }
        return forms[start];
    }

    // ---------------------------------------------------------------- the named things

    /// <summary>A settlement. <paramref name="city"/> takes the words a place uses once it has a
    /// stockyard and four newspapers.</summary>
    public string Town(NameData d, bool city = false) =>
        city ? Draw(d.CityFirst) + " " + Draw(d.CitySecond)
             : Draw(d.TownFirst) + " " + Draw(d.TownSecond);

    /// <summary>A person.</summary>
    public string Person(NameData d) => Draw(d.Given) + " " + Draw(d.Surname);

    /// <summary>What a survey calls the country it draws. The second half suits the ground, so a
    /// mine map says Lode or Adit and a graveyard map does not.</summary>
    public string MapTitle(NameData d, int ground)
    {
        string first = Draw(d.TitleFirst);
        var geo = d.TitleGeo.Count > 0 ? d.TitleGeo[Math.Clamp(ground, 0, d.TitleGeo.Count - 1)] : null;
        string second = Draw(geo);
        return (first + " " + second).Trim();
    }

    /// <summary>A landmark's name, in one of the three shapes the country uses: bare, owned, or
    /// described. <paramref name="shape"/> is the caller's roll, so the placement stream keeps
    /// deciding form and the Namer only supplies words.</summary>
    public string Landmark(NameData d, string noun, int shape) => shape switch
    {
        0 => Draw(d.LmOwner) + "'s " + noun,
        1 => "The " + Draw(d.LmAdj) + " " + noun,
        _ => "The " + noun,
    };

    /// <summary>A title, built from a shape this run has not used yet. This is the method the
    /// adventure generator and the module builders both go through.</summary>
    public string Title(NameData d)
    {
        var form = DrawForm(d.TitleForms);
        return Fill(d, form.Pattern);
    }

    /// <summary>Fill one template's slots. <c>{place}</c> is special — it is two draws off the town
    /// stock rather than one off a list, so a title can name a town that does not exist yet.</summary>
    public string Fill(NameData d, string pattern)
    {
        var outp = new System.Text.StringBuilder();
        int i = 0;
        while (i < pattern.Length)
        {
            if (pattern[i] != '{') { outp.Append(pattern[i]); i++; continue; }
            int close = pattern.IndexOf('}', i);
            if (close < 0) { outp.Append(pattern.Substring(i)); break; }
            string slot = pattern.Substring(i + 1, close - i - 1);
            outp.Append(slot.Equals("place", StringComparison.OrdinalIgnoreCase)
                ? Town(d)
                : d.Slots.TryGetValue(slot, out var pool) ? Draw(pool) : "{" + slot + "}");
            i = close + 1;
        }
        return outp.ToString();
    }
}

/// <summary>Loads and holds the naming stock.</summary>
public static class Names
{
    static NameData data;

    /// <summary>The stock, loaded once. Embedded in the rules assembly like every other data file
    /// — see the csproj note; embedding it anywhere else makes <c>Db.ReadData</c> find nothing.</summary>
    public static NameData Data => data ??= Load();

    static NameData Load()
    {
        var opts = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        return JsonSerializer.Deserialize<NameData>(Db.ReadDataFile("names.json"), opts) ?? new NameData();
    }

    /// <summary>A namer seeded off <paramref name="seed"/>, already refusing every word the stock
    /// records as spent on published work.</summary>
    public static Namer For(int seed) => new(seed, Data.Spent);

    /// <summary>How many distinct names a slot can offer. Used by the smoke rig to hold the stock
    /// to a floor — breadth is the only thing that defends across seeds, so it is worth asserting
    /// rather than trusting.</summary>
    public static int PoolSize(string slot) =>
        Data.Slots.TryGetValue(slot, out var p) ? p.Count : 0;
}
