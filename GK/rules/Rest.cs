namespace BloodAndGritKeeper;

// ============================================================ REST, AND THE BOTTLE
// Chapter XI's three rests and Chapter XII's whiskey and laudanum, worked out on a soul. Until
// v1.60.0 the app had one rest, "Blood and Nerve to full", and the book had never printed it:
// what the book gives back is a dawn's pools, a safe night's measure of Blood and Nerve, and a
// week's peace for the lot, and the difference between those three is most of what makes a long
// ride cost something. Pure and smoke-tested; the Posse and Tracker tabs only choose which.

/// <summary>The three rests the book prints (Player's Book Ch. XI, <em>Rest</em>).</summary>
public enum RestKind { Dawn, Night, Week }

public static class Rest
{
    /// <summary>A week of true peace is seven days, and a Taint eases one step for every three
    /// days clear of the ground (Ch. XII, <em>Shedding the Taint</em>), so a week eases it by what
    /// those two make. Derived rather than typed, so the book's two numbers and the app's third
    /// cannot come apart.</summary>
    public const int WeekDays = 7, DaysPerTaintStep = 3, WeekEasesTaint = WeekDays / DaysPerTaintStep;

    /// <summary>Blood from a safe night: level times the CON modifier, the modifier counted as 1
    /// when it is lower.</summary>
    public static int NightsBlood(int level, int conMod) => Math.Max(1, level) * Math.Max(1, conMod);

    /// <summary>What a safe night gives one soul in Blood: <see cref="NightsBlood"/>, and one more
    /// per level for a Mountain Man who has come into Iron Constitution (Ch. V, since v1.60.0:
    /// "a safe night gives you back one more Blood for each of your levels"). It read "you heal a
    /// little faster" until then, which no rest could count.</summary>
    public static int NightsBloodFor(PartyMember p)
        => NightsBlood(p.Level, ConMod(p.Sheet))
         + (CharGen.FeaturesAt(p.Calling, p.Level, p.Sheet?.Subpath).Any(f => f.Name == IronConstitution)
            ? Math.Max(1, p.Level) : 0);

    public const string IronConstitution = "Iron Constitution";

    /// <summary>The CON modifier off a soul's sheet. A hand-entered row has no sheet, and reads as
    /// the middle of the scale, which the minimum of 1 then governs: the same reading
    /// <see cref="Rules.DeathThresholdFor"/> gives a soul nobody has written a CON for.</summary>
    public static int ConMod(CharacterSheet s)
        => CharGen.Mod(s?.Scores != null && s.Scores.TryGetValue("CON", out int c) && c > 0 ? c : Rules.AverageScore);

    public static string Title(RestKind kind) => kind switch
    {
        RestKind.Dawn => "Dawn in the field",
        RestKind.Night => "A safe night",
        _ => "A week of peace",
    };

    /// <summary>The die a safe night rolls for Nerve.</summary>
    public const int NightNerveDie = 6;

    /// <summary>The die a drink or a dose rolls for Nerve: a d4 for whiskey, a d6 for laudanum.
    /// Named so the menu line, the dialog that asks for the die and the roll itself read one
    /// number.</summary>
    public static int DoseDie(bool laudanum) => laudanum ? 6 : 4;

    // The two pools a rest leaves alone, and what fills each instead. Ch. XI's dawn "brings back the
    // pools and preparations your Calling renews each dawn", and every Calling's pool says that of
    // itself but two. The Dark Cultist's Devotion is "refreshed through observance: the kept fast,
    // the night vigil, the rite performed at the proper hour"; the False Prophet's Tribute "refills
    // when you preach the false gospel to believers" (and through Feed the Dark, once a session).
    // Until this the app filled both at every rest, a free tank the book prices in observance and
    // in preaching. Named here because chargen.json carries no refresh field, and the Engineer's
    // and the Sister's pool sentences are not transcribed anywhere it could be read from; the smoke
    // rig holds both names to the data and to the prose that is.
    static readonly Dictionary<string, (string Short, string Long)> RefilledOtherwise = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Devotion"] = ("refreshed through observance",
                        "it comes back through observance (the kept fast, the night vigil, the rite at its hour), not with the sun"),
        ["Tribute"]  = ("refilled by preaching to believers",
                        "it refills when the false gospel is preached to believers, not with the sun"),
    };

    /// <summary>The pools no rest refills: Devotion and Tribute, which the Player's Book says
    /// come back through observance and through preaching. The Keeper fills them on the Posse
    /// tab's Pool column when the rite is kept or the sermon preached.</summary>
    public static IReadOnlyCollection<string> PoolsRefilledOtherwise => RefilledOtherwise.Keys;

    /// <summary>Whether a dawn, and so every rest, fills this pool. True for every pool but the
    /// two in <see cref="PoolsRefilledOtherwise"/>, and true for no pool at all, where there is
    /// nothing to fill.</summary>
    public static bool RenewsAtDawn(string poolName)
        => string.IsNullOrWhiteSpace(poolName) || !RefilledOtherwise.ContainsKey(poolName.Trim());

    /// <summary>How a pool comes back, in the words a sheet's pool line has room for:
    /// "refreshed each dawn" for all but two.</summary>
    public static string HowItRefills(string poolName)
        => !string.IsNullOrWhiteSpace(poolName) && RefilledOtherwise.TryGetValue(poolName.Trim(), out var how)
            ? how.Short : "refreshed each dawn";

    /// <summary>What a rest gives back, in the few words a menu line has room for. Read off the
    /// same constants <see cref="Take"/> spends, so a menu cannot promise what the rest does not
    /// do.</summary>
    public static string Gives(RestKind kind) => kind switch
    {
        RestKind.Dawn => "pools and dawn features, no Blood or Nerve",
        RestKind.Night => $"pools, 1d{NightNerveDie} Nerve, Blood",
        _ => $"pools, all Blood and Nerve, Taint eased {WeekEasesTaint}",
    };

    /// <summary>A rest's menu line: its title and what it gives, "A safe night: pools, 1d6 Nerve,
    /// Blood". No access key: the menus that carry it escape ampersands on the way in.</summary>
    public static string Label(RestKind kind) => $"{Title(kind)}: {Gives(kind)}";

    /// <summary>What a rest gave back, counted rather than described, so the log can say exactly
    /// what moved and say "nothing" when nothing did.</summary>
    public record RestOutcome(RestKind Kind, string Who, int Blood, int Nerve, int Pool, string PoolName,
        int TaintEased, bool DrainLifted, int FeaturesBack, bool Returned)
    {
        /// <summary>Why a pool short of full stayed where it was, when it is one of the two no
        /// rest refills: "Devotion stays at 1 of 4: it comes back through observance…". Null when
        /// the rest filled it, or it was full already.</summary>
        public string PoolKept { get; init; }

        public string Line
        {
            get
            {
                var got = new List<string>();
                if (Blood > 0) got.Add($"+{Blood} Blood");
                if (Nerve > 0) got.Add($"+{Nerve} Nerve");
                if (Pool > 0) got.Add($"+{Pool} {(string.IsNullOrEmpty(PoolName) ? "pool" : PoolName)}");
                if (TaintEased > 0) got.Add($"Taint eased {TaintEased}");
                if (DrainLifted) got.Add("the drink's Drained lifts");
                if (FeaturesBack > 0) got.Add(FeaturesBack == 1 ? "1 feature back" : $"{FeaturesBack} features back");
                string what = got.Count == 0 ? "nothing to give back" : string.Join(", ", got);
                // Said even when the soul was at full Blood, because the Keeper deciding whether to
                // rest a wounded Returned soul needs to know before, and the log is where it lands.
                string note = Returned && Kind != RestKind.Dawn ? " No Blood: the Returned heal only by Mending." : "";
                string kept = PoolKept == null ? "" : $" {PoolKept}.";
                return $"{Who}, {Title(Kind).ToLowerInvariant()}: {what}.{note}{kept}";
            }
        }
    }

    /// <summary>Rest a soul. Every kind ends in a dawn, so every kind refills the pools a Calling
    /// "renews each dawn" (Ch. XI), returns the once-a-day features, and starts the day's count of
    /// drinks again. A safe night adds 1d6 Nerve and <see cref="NightsBlood"/>, and lifts a Drained
    /// the bottle left; a week gives back all the Blood and all the Nerve and eases the Taint.
    ///
    /// <para>Two pools are not renewed at dawn and no rest fills them: Devotion, "refreshed
    /// through observance", and Tribute, which "refills when you preach the false gospel to
    /// believers" (<see cref="PoolsRefilledOtherwise"/>). The outcome says so when one is short,
    /// so the Keeper is not left wondering why the Cultist woke with an empty hand.</para>
    ///
    /// <para>A dawn in the field restores pools and nothing else, Cole's call of 2026-09-27: a
    /// posse that sleeps in its boots by the wreck has had no rest the book would recognise, and
    /// the Blood and the Nerve are exactly what that night should have cost them. It leaves the
    /// bottle's Drained standing for the same reason, since the book prints that as "Drained 1
    /// until a safe night", and says outright that a dawn in the field does not lift it.</para>
    ///
    /// <para>No rest touches the Mark, Grit, a Hunger, a Debt or a familiar. Each of those has its
    /// own way back, or none, and a track that eased overnight would say its cost was nothing.
    /// The Returned get no Blood from any of them (Ch. XII: Mending is the only healing they have);
    /// their Nerve comes back like anyone's.</para></summary>
    public static RestOutcome Take(PartyMember p, RestKind kind, int? nerveDie = null)
    {
        if (p == null) return null;
        bool returned = CharGen.IsReturned(p.Sheet);
        int blood0 = p.BloodCur, nerve0 = p.NerveCur, pool0 = p.PoolCur, taint0 = p.Taint;
        bool drain0 = p.DrainedByDrink;

        bool poolRenews = RenewsAtDawn(p.PoolName);
        if (poolRenews) p.PoolCur = p.PoolMax;
        int features = CharGen.RefreshFeatures(p, FeatureCadence.Dawn);
        p.DosesToday = 0;
        p.DosedThisScene = false;

        if (kind == RestKind.Night)
        {
            p.NerveCur = Math.Min(p.NerveMax, p.NerveCur + (nerveDie ?? Rules.Rng.Next(1, NightNerveDie + 1)));
            if (!returned) p.BloodCur = Math.Min(p.BloodMax, p.BloodCur + NightsBloodFor(p));
            p.DrainedByDrink = false;
        }
        else if (kind == RestKind.Week)
        {
            p.NerveCur = p.NerveMax;
            if (!returned) p.BloodCur = p.BloodMax;
            p.Taint -= Math.Min(p.Taint, WeekEasesTaint);
            p.DrainedByDrink = false;
        }

        return new RestOutcome(kind, p.Name, p.BloodCur - blood0, p.NerveCur - nerve0, p.PoolCur - pool0,
            p.PoolName, taint0 - p.Taint, drain0 && !p.DrainedByDrink, features, returned)
        {
            PoolKept = poolRenews || p.PoolCur >= p.PoolMax ? null
                : $"{p.PoolName} stays at {p.PoolCur} of {p.PoolMax}: {RefilledOtherwise[p.PoolName.Trim()].Long}",
        };
    }

    public static RestOutcome DawnInTheField(PartyMember p) => Take(p, RestKind.Dawn);
    public static RestOutcome NightsRest(PartyMember p, int? nerveDie = null) => Take(p, RestKind.Night, nerveDie);
    public static RestOutcome WeekOfPeace(PartyMember p) => Take(p, RestKind.Week);

    // ---- whiskey and worse (Ch. XII, Recovering Nerve)

    /// <summary>The Fortitude DC a drink or dose calls, given how many the soul has had today:
    /// none for the first, 12 for the second, and 2 more for every one after that. 0 means no
    /// save.</summary>
    public static int DoseDc(int dosesBefore) => dosesBefore <= 0 ? 0 : 12 + 2 * (dosesBefore - 1);

    /// <summary>Why this soul cannot take a drink or a dose right now, or null when they can. One
    /// a scene, of either: the book counts the bottle and the phial together.</summary>
    public static string WhyNotDose(PartyMember p)
        => p == null ? "Nobody is selected."
         : p.DosedThisScene ? $"{p.Name} has had their one this scene. The bottle steadies a hand once a scene and no more."
         : null;

    public record DoseOutcome(string Who, bool Laudanum, int Nerve, int SaveDc, int Die, int Degree,
        string DegreeName, bool Drained, int BloodLost, string Detail)
    {
        public string Line
        {
            get
            {
                string took = Laudanum ? "a dose of laudanum" : "a drink";
                string head = $"{Who} takes {took}: +{Nerve} Nerve.";
                if (SaveDc == 0) return head;
                if (!Drained) return $"{head} Fortitude DC {SaveDc}: {DegreeName}, and it sits well enough.";
                return $"{head} Fortitude DC {SaveDc}: {DegreeName}, Drained 1 until a safe night"
                     + (BloodLost > 0 ? $", and {BloodLost} Blood lost with it." : ".");
            }
        }
    }

    /// <summary>A drink of whiskey (1d4 Nerve) or a dose of laudanum (1d6). The Nerve comes back
    /// whatever else happens. The second and later in a day call a Fortitude save at
    /// <see cref="DoseDc"/>, and a failure leaves the soul Drained 1: Appendix B's Drained, which
    /// takes Blood equal to their level as well as the −2, until a safe night.
    ///
    /// <para>A soul who is already Drained, from the bottle or from anything else, loses nothing
    /// more to a second failure. Two of the same condition are one condition, and the worse of
    /// two values is the one that holds (Ch. II, <em>When Bonuses Meet</em>); the app cannot see a
    /// Tracker row from here, so the caller says whether one is showing.</para></summary>
    public static DoseOutcome TakeDose(PartyMember p, bool laudanum, int? nerveDie = null, int? fortDie = null,
                                       bool alreadyDrained = false)
    {
        if (WhyNotDose(p) != null) return null;
        int nerve0 = p.NerveCur;
        p.NerveCur = Math.Min(p.NerveMax, p.NerveCur + (nerveDie ?? Rules.Rng.Next(1, DoseDie(laudanum) + 1)));

        int dc = DoseDc(p.DosesToday), die = 0, idx = 2, blood = 0;
        string name = "", detail = "";
        bool drained = false;
        if (dc > 0)
        {
            die = fortDie ?? Rules.Rng.Next(1, 21);
            // Named, so the daybook's check line says whose save it was (GK-B5): a posse drinking
            // together leaves one Fortitude line a soul.
            using (Daybook.As(p.Name)) { (idx, name, detail) = Rules.FourDegrees(die, p.Fort, dc); }
            drained = idx <= 1;
            if (drained && !p.DrainedByDrink && !alreadyDrained)
            {
                int before = p.BloodCur;
                p.BloodCur -= Math.Max(1, p.Level);
                blood = before - p.BloodCur;
            }
            if (drained) p.DrainedByDrink = true;
        }
        p.DosesToday++;
        p.DosedThisScene = true;
        return new DoseOutcome(p.Name, laudanum, p.NerveCur - nerve0, dc, die, idx, name, drained, blood, detail);
    }

    /// <summary>A soul's conditions line with the bottle's Drained 1 on it. A Drained already
    /// showing is left as it stands, at whatever value it carries: the worse one holds.</summary>
    public static string WithDrinkDrain(string conditions)
    {
        var set = Split(conditions);
        if (!set.Any(IsDrained)) set.Add("Drained 1");
        return string.Join(", ", set);
    }

    /// <summary>The conditions line with the bottle's Drained taken off, when a safe night has
    /// lifted it. Only "Drained 1", the bottle's own: a deeper Drained came from something else and
    /// keeps its own clock.</summary>
    public static string WithoutDrinkDrain(string conditions)
    {
        var set = Split(conditions);
        set.RemoveAll(x => x == "Drained 1" || x == "Drained");
        return string.Join(", ", set);
    }

    /// <summary>What a soul's conditions line carries from one fight into the next: the bottle's
    /// Drained, which holds until a safe night and so outlasts any scene. Empty for anybody sober,
    /// and for a row with no soul behind it. New fight puts it back after clearing the fight's own
    /// conditions, and a soul sent to the field arrives wearing it.</summary>
    public static string Standing(PartyMember p) => p?.DrainedByDrink == true ? "Drained 1" : "";

    /// <summary>Whether two conditions lines hold the same conditions, whatever order they were
    /// written in.</summary>
    public static bool SameConditions(string a, string b)
        => new HashSet<string>(Split(a), StringComparer.OrdinalIgnoreCase).SetEquals(Split(b));

    static List<string> Split(string conditions) => (conditions ?? "")
        .Split(',', StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries).ToList();

    static bool IsDrained(string c) => c == "Drained" || c.StartsWith("Drained ");

    /// <summary>Whether a conditions line already shows a Drained, of any value.</summary>
    public static bool ShowsDrained(string conditions) => Split(conditions).Any(IsDrained);
}
