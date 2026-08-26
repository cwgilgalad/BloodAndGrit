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

public class CgSign
{
    public string name { get; set; } public string cost { get; set; } public string desc { get; set; }
    /// <summary>"common" | "bargain" | "craft" — which of Ch. XIII's three lists it sits on.</summary>
    public string list { get; set; }
    /// <summary>1–5. A soul may learn it once their level has opened that Rank.</summary>
    public int rank { get; set; }
}

/// <summary>The faith-side counterpart to a Sign (Player's Book Ch. VI). Same shape and same
/// five-Rank spine; a Calling of Faith learns these instead of Signs, paid from its pool.</summary>
public class CgMiracle
{
    public string name { get; set; } public string cost { get; set; } public string desc { get; set; }
    /// <summary>"blessing" | "liturgy" | "revival" | "spirits" | "mending" | "consecration".</summary>
    public string list { get; set; }
    /// <summary>1–5. Same rank gate as the Signs (Rank opens at 1/3/5/7/9).</summary>
    public int rank { get; set; }
}

/// <summary>One row of the Ch. X arms table. <c>range</c> is the increment in feet, <c>cap</c> how
/// many shots before reloading, and <c>reload</c> the printed cost of making it ready again —
/// "1", "1/shot" or "slow". All three are zero or empty on a blade, which has no such columns.
/// They were absent until 2026-08-16, which is why the Iron Code's range increments and reload
/// actions could not be implemented at all: the book prints seven columns and this carried four.</summary>
public class CgWeapon
{
    public string name { get; set; } public string dmg { get; set; } public string traits { get; set; }
    public int range { get; set; } public int cap { get; set; } public string reload { get; set; } = "";
    public double cost { get; set; } public string kind { get; set; }
}

/// <summary>One row of the Ch. X armor table. <c>gear</c> is the gearPrices key that buys it,
/// which is how a duster already in a soul's kit is recognized as the armor it always was.</summary>
public class CgArmor
{
    public string name { get; set; } public string gear { get; set; }
    public int drBlades { get; set; } public int drShot { get; set; }
    public int defense { get; set; } public int speed { get; set; }
    public double cost { get; set; } public string note { get; set; }
}

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
    /// <summary>The Calling's opening words in the Player's Book, so the picker can say what a
    /// Calling <em>is</em> and not only what it rolls. Transcribed from the book, guarded by
    /// audits/verify_rules.py.</summary>
    public string blurb { get; set; }
    public int hitDie { get; set; } public int trainedSkills { get; set; }
    public string strongSaves { get; set; }
    public List<CgRow> rows { get; set; } = new();
    public Dictionary<string, string> featureDescs { get; set; } = new();
    public Dictionary<string, int> signsKnownAt { get; set; }
    /// <summary>Which of Ch. XIII's lists this Calling draws on. Null for the fourteen that
    /// work no Signs at all; the Witch alone holds "craft".</summary>
    public List<string> signLists { get; set; }
    /// <summary>Which of Ch. VI's Miracle lists this Calling draws on. Null for every Calling
    /// but the five of Faith; each holds "blessing" plus its own.</summary>
    public List<string> miracleLists { get; set; }
    public Dictionary<string, int> miraclesKnownAt { get; set; }
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
    public List<CgMiracle> miracles { get; set; } = new();
    /// <summary>The shared five-Rank spine: level → highest Rank, for Signs and Miracles alike.</summary>
    public Dictionary<string, int> rankAtLevel { get; set; } = new();
    public List<CgWeapon> weapons { get; set; } = new();
    public List<CgArmor> armor { get; set; } = new();
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
    public List<string> MiraclesKnown { get; set; } = new();          // Ch. VI, the Callings of Faith
    public string Subpath { get; set; }                                  // chosen at 3rd, or null
    public string CallingChoice { get; set; }                            // Marshal reputation / Shaman aspect / Witch familiar
    // The Witch's familiar (Ch. VII). Until v1.45.0 the bound beast was one third of the shared
    // CallingChoice string and nothing else — the books give it a standing +2, a touch-range
    // delivery, shared senses and a Sickened when it dies, and the app carried none of that. The
    // kind is still written into CallingChoice for every reader that already prints it; these
    // three carry the mechanics. Absent from sheets saved before v1.45.0, which deserialize to
    // null/false and read as a soul with no familiar, so no session.json migration is needed.
    public string FamiliarKind { get; set; }                             // "a crow", or null for no familiar
    public string FamiliarBoon { get; set; }                             // the standing +2 befitting its nature
    public bool FamiliarLost { get; set; }                               // it died; the Witch is Sickened until re-bound
    /// <summary>The Familiar-Bound's greater boon has been spent: "should you fall, it carries your
    /// spirit to a new dawn — <em>once</em>". Once ever, and nothing in the app gives it back — not
    /// a new fight, not a long rest, not a new session. It is stored on the SHEET rather than in
    /// <see cref="PartyMember.FeatureSpent"/> for exactly that reason: FeatureSpent is a ration and
    /// <see cref="CharGen.RefreshFeatures"/> walks it at every boundary, so a once-in-a-life thing kept
    /// there would quietly come back the first time somebody pressed New fight. Same separation,
    /// and the same reason, as the Pact-Sworn's Debts.</summary>
    public bool FamiliarCarried { get; set; }
    public string PoolLine { get; set; }                                 // e.g. "Favor 3 (PRE mod + half level, refreshed each dawn)"
    public string PoolName { get; set; }                                 // the faith/sign currency's name, or null
    public int PoolMax { get; set; }                                     // its maximum at this level, or 0 for no pool
    public double CoinRolled { get; set; } public double CoinLeft { get; set; }
    public List<string> Gear { get; set; } = new();
    public List<string> WeaponsCarried { get; set; } = new();            // "Single-Action Revolver 1d8 (Fatal d10, Misfire 1)"
    // Armor worn (Ch. X). Added v1.12; absent from sheets saved before it, which deserialize
    // to null/0 and simply read as an unarmored soul — no session.json migration needed.
    public string ArmorWorn { get; set; }                                // Ch. X name, or null for none
    public int DrBlades { get; set; } public int DrShot { get; set; }    // what the armor turns
    public string Lost { get; set; } public string Seen { get; set; }
    public string Vice { get; set; } public string Moving { get; set; }
    // What they look like and what they are wearing (Look.Roll). Added v1.30; absent from sheets
    // saved before it, which deserialize to null and simply read as a soul nobody has described
    // yet — every consumer tests Look?.Any, so no session.json migration is needed.
    public SoulLook Look { get; set; }
    public List<int> AbilityBoostLevels { get; set; } = new();           // 5 and/or 10 if reached
    public List<string> BoostedAbilities { get; set; } = new();
    public bool HandTweaked { get; set; }                                // edited after generation — the book no longer vouches
}

// ============================================================ GENERATOR
// ================================================= how often a feature may be used (v1.42.0)

/// <summary>The boundary a limited feature comes back at. Ordered, and the order is the whole
/// point: everything at or below the boundary that just passed comes back, so a scene returns
/// the Turn, Round and Scene features and leaves the once-a-session ones spent. Dawn sits under
/// Session because a posse can sleep twice in one night's play and the session's one great
/// mercy is still spent.
///
/// <para><b>Trigger</b> is the odd one, and it is here because the book has two of them: the
/// Witch Hunter's Judgment comes back "when you name a new quarry" and the Sawbones' Field
/// Surgery is "once per wound". No clock returns those, so nothing but the Keeper's hand and a
/// new session does either — which is exactly why it sits directly under Session.</para></summary>
public enum FeatureCadence { None = 0, Turn = 1, Round = 2, Scene = 3, Dawn = 4, Trigger = 5, Session = 6 }

/// <summary>What a Calling's feature says about how often it may be used, read out of the book's
/// own sentence rather than typed into the data a second time.
///
/// <para>Forty-six of the hundred and sixteen features print a limit, and thirty-one of those are
/// a limit on an <em>activation</em> — "Once per session, when an ally within sight would drop to
/// 0 Blood…". Those are the ones a table forgets, and the ones this reads. The rest describe
/// something ongoing ("allies inside recover Nerve each round"), which is not a thing anybody
/// presses, so it is deliberately not matched: a counter beside a feature nobody activates is
/// noise that teaches a Keeper to stop trusting the counters that matter.</para></summary>
public readonly struct FeatureLimit
{
    public FeatureCadence Cadence { get; init; }
    /// <summary>A flat number of uses, or 0 when <see cref="Ability"/> decides it.</summary>
    public int Uses { get; init; }
    /// <summary>"PRE", "WIT"… when the book counts the uses off a modifier, else null.</summary>
    public string Ability { get; init; }
    public bool HalfLevel { get; init; }
    public int Min { get; init; }
    /// <summary>The book's own words, for the tooltip. A Keeper deserves the sentence, not a code.</summary>
    public string Phrase { get; init; }

    static readonly System.Text.RegularExpressions.Regex TriggerNoun =
        new(@"per (quarry|wound|patient|target)", System.Text.RegularExpressions.RegexOptions.IgnoreCase);

    public bool Any => Cadence != FeatureCadence.None;

    /// <summary>How many uses a soul of this sheet actually gets. A hand-entered soul with no
    /// sheet has no modifier to read, so the floor is the answer — never zero, which would render
    /// as a feature that can never be used.</summary>
    public int UsesFor(CharacterSheet s)
    {
        if (Ability == null) return Math.Max(1, Uses);
        if (s == null || !s.Scores.TryGetValue(Ability, out int score)) return Math.Max(1, Min);
        int n = CharGen.Mod(score) + (HalfLevel ? s.Level / 2 : 0);
        return Math.Max(Math.Max(1, Min), n);
    }

    public string Says(CharacterSheet s)
    {
        if (!Any) return "";
        string when = Cadence switch
        {
            FeatureCadence.Turn => "per turn",
            FeatureCadence.Round => "per round",
            FeatureCadence.Scene => "per scene",
            FeatureCadence.Dawn => "each dawn",
            FeatureCadence.Trigger => TriggerNoun.Match(Phrase ?? "") is { Success: true } t
                                      ? "per " + t.Groups[1].Value.ToLowerInvariant() : "per quarry",
            _ => "per session",
        };
        int n = UsesFor(s);
        return n == 1 ? "once " + when : $"{n}× {when}";
    }
}

/// <summary>A count that goes <b>up</b> and that no boundary gives back — the one shape in the
/// Player's Book the Calling strip had no home for until v1.44.0.
///
/// <para>The Hexer's <b>Pact-Sworn</b> bargain is the whole of it: <i>"Once per scene, turn a
/// failed Sign or Will save into a success by taking a Debt; on your third Debt the Patron calls
/// it in — a demand, and +1 Mark."</i> The once-a-scene half is a ration and
/// <see cref="FeatureLimit"/> has counted it since v1.42.0. The Debts are the other half, and they
/// are a different animal: they accumulate across scenes, across nights, and across the whole
/// campaign, and nothing in the app's boundary machinery should ever hand one back. A Debt is owed
/// until the Patron collects it.</para>
///
/// <para>Read out of the feature's own prose, the same discipline <see cref="FeatureLimit"/>
/// follows and for the same reason: a <c>tally</c> column typed into <c>chargen.json</c> beside
/// the description is a second copy of a fact, and this project has paid for second copies twice.
/// A sweep of all 116 features and all 56 paths finds exactly one match, which is the honest
/// answer rather than a reason to special-case the Hexer in the UI.</para></summary>
public readonly struct FeatureTally
{
    /// <summary>What the book calls the thing being counted — "Debt".</summary>
    public string Noun { get; init; }
    /// <summary>The count at which it comes due. Three, for the Pact-Sworn.</summary>
    public int At { get; init; }
    /// <summary>The book's own sentence, for the tooltip and for the warning when it lands.</summary>
    public string Phrase { get; init; }

    public bool Any => At > 0 && !string.IsNullOrEmpty(Noun);

    // Only these five, because CharGen.ReadTally only ever produces these five — the book writes
    // its one threshold as a word. A general -st/-nd/-rd/-th builder would be dead code by the
    // build's own reckoning, and would answer "7th" for a number nothing can hand it.
    public static string Ordinal(int n) => n switch
    {
        1 => "first", 2 => "second", 3 => "third", 4 => "fourth", 5 => "fifth",
        _ => n.ToString(),
    };

    /// <summary>What the card says under the name — "the third Debt comes due".</summary>
    public string Says => Any ? $"the {Ordinal(At)} {Noun} comes due" : "";
}

/// <summary>A standing ± an Origin carries, and the condition the book hangs it on.
///
/// <para>The third shape on the strip, and the one that is neither a ration nor a tally. A
/// <see cref="FeatureLimit"/> is a thing you spend and a boundary returns; a
/// <see cref="FeatureTally"/> is a thing that climbs and nothing returns. This is neither: it is
/// always true and it is never automatic, because whether it applies is a fact about the world
/// — indoors, among the wealthy, talking to a lawman — that the app does not model and must not
/// guess at. It is <b>offered</b>, exactly as a creature's attack rider is (see the Iron Code's
/// rule that the engine may only write what needs nobody's judgement).</para>
///
/// <para>The value in it is not the arithmetic, which any Keeper can do. It is that the app knows
/// which of these this particular soul has, and says so at the moment the roll is being made
/// instead of leaving it on a sheet nobody rereads after first level.</para></summary>
public sealed class OriginEdge
{
    /// <summary>The Origin that grants it — the card's head line.</summary>
    public string Origin { get; init; }
    /// <summary>Signed, as the book prints it: +2, −1.</summary>
    public int Size { get; init; }
    /// <summary>The short of what it applies to — "Notice against ambush", "Fortitude saves
    /// against fatigue". One clause, because a chip is read at a glance or not at all.</summary>
    public string Applies { get; init; }
    /// <summary>The book's whole sentence, for the tooltip. A Keeper deserves the rule, not a
    /// code — the same standing choice <see cref="FeatureLimit.Phrase"/> makes.</summary>
    public string Phrase { get; init; }
    /// <summary>Whether it came out of the boon or the burden. Drawn differently: a burden a
    /// player can forget to apply is the half that decides whether an Origin is a CHOICE or a
    /// free +2.</summary>
    public bool IsBoon { get; init; }

    public string Says => $"{(Size >= 0 ? "+" : "−")}{Math.Abs(Size)} {Applies}";
}

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

    /// <summary>What a soul adds to a skill check (Player's Book Ch. VIII): the keyed ability's
    /// modifier alone while untrained, and once trained, that plus your level plus the rank's
    /// bonus — +2 trained, +4 expert, +6 master. The ability a skill is keyed to comes from the
    /// data, not from a second list here, so the Ledger's tick and this number always agree.</summary>
    public static int SkillBonus(CharacterSheet s, string skill)
    {
        if (s == null || string.IsNullOrEmpty(skill)) return 0;
        var def = D?.skills?.Find(k => string.Equals(k.name, skill, StringComparison.OrdinalIgnoreCase));
        int mod = def != null && s.Scores != null && s.Scores.TryGetValue(def.ability, out int score) ? Mod(score) : 0;
        int rank = s.SkillRanks != null && s.SkillRanks.TryGetValue(def?.name ?? skill, out int r) ? r : 0;
        return (rank <= 0 ? mod : mod + s.Level + rank * 2) + FamiliarBoonOn(s, def?.name ?? skill);
    }

    /// <summary>What the bound beast adds to this skill — the standing boon of Ch. VII, applied
    /// here so that it is applied at all.
    ///
    /// <para>From v1.45.0 the sheet has printed "+2 Stealth" and every number the app worked out
    /// has ignored it, because the only place that skill's name existed was in the middle of a
    /// sentence written for a human reader. A bonus nobody adds is not a rule; it is a decoration.
    /// Putting it inside <see cref="SkillBonus"/> means every roll the app already reckons picks it
    /// up at once — a Witch's initiative is a Notice check, so a live crow now moves her place in
    /// the order, and the Read-the-sign dialog prefills a toad's Medicine and a cat's Stealth the
    /// same way.</para>
    ///
    /// <para>Nothing while the beast is dead, which is the other half of what the book says it is
    /// worth. Applied whether or not the soul is trained: the book grants the boon for having the
    /// beast near, not for having studied.</para></summary>
    public static int FamiliarBoonOn(CharacterSheet s, string skill)
        => s != null && !s.FamiliarLost && !string.IsNullOrEmpty(skill)
           && FamiliarSkillFor(s.FamiliarKind) is string sk
           && string.Equals(sk, skill, StringComparison.OrdinalIgnoreCase)
         ? FamiliarBoonSize : 0;

    /// <summary>What a soul adds to initiative — their Notice bonus, because initiative IS a Notice
    /// check (Player's Book Ch. XI, and the app's own Reference deck says so on the Iron Code leaf).
    /// Named rather than left as a bare <see cref="SkillBonus"/> call at the tracker, so the skill
    /// the rule keys to is written down once and the tracker cannot quietly start rolling a
    /// different one. A soul with no sheet — an ad-hoc NPC, a creature — has nothing to read and
    /// adds nothing.</summary>
    public static int InitiativeBonus(CharacterSheet s) => SkillBonus(s, "Notice");

    // ---- the Rank spine, shared by Signs (Ch. XIII) and Miracles (Ch. VI) ----

    /// <summary>The highest Rank a soul of this level may reach: Rank 1 at 1st, then a new Rank at
    /// 3rd, 5th, 7th and 9th. One spine for both magic systems, read from the data where it is
    /// stated so the book's table and this rule cannot part company.</summary>
    public static int RankAt(int level)
        => D.rankAtLevel.TryGetValue(level.ToString(), out var r) ? r
         : Math.Clamp((level + 1) / 2, 1, 5);

    /// <summary>The Sign Rank a soul of this level reaches (Player's Book Ch. XIII).</summary>
    public static int SignRankAt(int level) => RankAt(level);

    /// <summary>The Miracle Rank a soul of this level reaches (Player's Book Ch. VI).</summary>
    public static int MiracleRankAt(int level) => RankAt(level);

    /// <summary>Every Miracle a Calling of Faith may learn at a level: its lists, gated by Rank.
    /// A Calling that works no Miracles gets nothing.</summary>
    public static List<CgMiracle> MiraclesFor(CgCalling cal, int level)
        => cal.miraclesKnownAt == null || cal.miracleLists == null ? new()
         : D.miracles.Where(x => cal.miracleLists.Contains(x.list) && x.rank <= RankAt(level)).ToList();

    /// <summary>Every Sign a soul may actually learn at a level: their Calling's lists, gated by Rank.
    /// A Calling that works no Signs gets nothing — unless the soul took <em>Hedge Magic</em> (Ch. IX),
    /// which opens the shallow end and only that: the Common Signs at Rank 1. Ch. XIII puts it as
    /// reached "by the Hexer freely, by the Touched a little."</summary>
    public static List<CgSign> SignsFor(CgCalling cal, int level, bool hedgeMagic = false)
        => cal.signsKnownAt != null && cal.signLists != null
         ? D.signs.Where(x => cal.signLists.Contains(x.list) && x.rank <= SignRankAt(level)).ToList()
         : hedgeMagic ? D.signs.Where(x => x.list == "common" && x.rank == 1).ToList()
         : new();

    /// <summary>Does this Calling work anything at all, at any level it can reach? A Gunhand knows
    /// no Signs and no Miracles at 1st and still knows none at 10th, and that is the rule rather
    /// than a gap in their sheet — so a screen offering "what do they work?" has to be able to tell
    /// a soul who works nothing from a soul who has simply not learned one yet, and say which.
    /// <para>Reads the CALLING's lists rather than the soul's known names, which is the whole point:
    /// a Preacher with an empty <c>MiraclesKnown</c> is a different sentence from a Gunhand with
    /// one. <em>Hedge Magic</em> is deliberately excluded — the Edge opens the shallow end for a
    /// soul who takes it, and this question is about the Calling.</para></summary>
    public static bool CallingWorksNothing(string calling)
    {
        var cal = D?.callings?.Find(c => c.name == calling);
        if (cal == null) return false;                 // unknown Calling: say nothing rather than guess
        return SignsFor(cal, 10).Count == 0 && MiraclesFor(cal, 10).Count == 0;
    }

    // ---- armor (Player's Book Ch. X, "On Armor") ----

    /// <summary>What a soul is actually wearing, read off the gear they ended up with. The book
    /// says armor does not stack — "count only the better of the two" — so the best row wins.</summary>
    public static CgArmor ArmorFrom(IEnumerable<string> gear)
    {
        var owned = D.armor.Where(a => gear.Contains(a.gear)).ToList();
        return owned.Count == 0 ? null
             : owned.OrderByDescending(a => a.drBlades).ThenByDescending(a => a.drShot).First();
    }

    /// <summary>A kit list read back the way a person would say it: one line per distinct thing,
    /// in the order it was acquired, with a count on anything held more than once ("Lantern × 3").
    /// Gear and weapons are stored one entry per item so the coin ledger can price them by
    /// counting; this is the single place that turns those entries back into lines, so the
    /// Ledger, the text sheet and the printed sheet can never tally them differently.</summary>
    public static List<string> Tally(IEnumerable<string> items)
    {
        var order = new List<string>();
        var count = new Dictionary<string, int>();
        foreach (var it in items)
        {
            if (count.TryGetValue(it, out var n)) count[it] = n + 1;
            else { count[it] = 1; order.Add(it); }
        }
        return order.Select(it => count[it] > 1 ? $"{it} × {count[it]}" : it).ToList();
    }

    /// <summary>How a soul's armor reads — one phrasing, used by the sheet, the ledger, the posse
    /// notes and the printed page alike. Empty when they are standing in nothing but a shirt.</summary>
    public static string ArmorLine(CharacterSheet s) => string.IsNullOrEmpty(s.ArmorWorn)
        ? "" : $"{s.ArmorWorn} — DR {s.DrBlades} vs blades, DR {s.DrShot} vs small shot";

    /// <summary>Record what the gear says a soul is wearing, without touching Defense or Speed.
    /// Safe to call again after a hand edit: the numbers stay whatever the user typed.</summary>
    public static void ReadArmor(CharacterSheet s)
    {
        var a = ArmorFrom(s.Gear);
        s.ArmorWorn = a?.name;
        s.DrBlades  = a?.drBlades ?? 0;
        s.DrShot    = a?.drShot   ?? 0;
    }

    public static CgData D { get; private set; }

    public static void Load()
    {
        var opts = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        D = JsonSerializer.Deserialize<CgData>(Db.ReadDataFile("chargen.json"), opts);
    }

    static readonly string[] Ab = { "STR", "DEX", "CON", "WIT", "RES", "PRE" };
    public static int Mod(int score) => (int)Math.Floor((score - 10) / 2.0);

    static T Pick<T>(List<T> list) => list[Rules.Rng.Next(list.Count)];

    /// <summary>One of the colour pools in chargen.json — vices, what a soul lost, what they've
    /// seen, what moves them, the gendered given names. Internal rather than private so the smoke
    /// rig can hold each pool to a depth: a thin pool repeats over a campaign, and a pool that
    /// silently emptied would still generate perfectly valid, identical souls.</summary>
    internal static List<string> FlavorList(string key)
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
    //
    // WHICH souls get one used to be a bare 12% roll answerable to nothing, which was fine while
    // the app never said where anybody was from and became a contradiction on screen the moment it
    // did — "Rafferty Luján, Chinese, out of Guangdong". The look decides now: a people that owns a
    // whole-name pool (LkPeople.namesFrom) always draws from it, and everybody else always draws
    // given-plus-surname. One decision, made once. Pass a null look and the old odds stand, which
    // is what an NPC with no description should still get.
    public static string FullName(string gender, SoulLook look = null)
    {
        // A gender the lists are not written for draws from BOTH whole-name pools, the same way
        // GivenFor falls back to the mixed given-name list. The old ternary sent every gender that
        // was not exactly "Woman" down the men's branch, so a soul whose player wrote their own
        // gender got a man's whole name one time in eight.
        string stem = NamePoolFor(look);
        if (stem != null)
        {
            var owned = WholeNames(stem, gender);
            if (owned.Count > 0) return Pick(owned);
        }
        if (look != null) return GivenFor(gender) + " " + Db.Pick("npcSurname");

        var whole = WholeNames("fullNames", gender);
        if (whole.Count > 0 && Rules.Rng.Next(100) < 12) return Pick(whole);
        return GivenFor(gender) + " " + Db.Pick("npcSurname");
    }

    /// <summary>The whole-name pool stem a described soul's people owns, or null for the great
    /// majority whose names are a given name and a surname like anybody else's.</summary>
    static string NamePoolFor(SoulLook look)
    {
        if (look == null || string.IsNullOrWhiteSpace(look.People) || Look.D?.peoples == null) return null;
        var p = Look.D.peoples.Find(x => x.name == look.People);
        return string.IsNullOrWhiteSpace(p?.namesFrom) ? null : p.namesFrom;
    }

    static List<string> WholeNames(string stem, string gender) => gender switch
    {
        "Woman" => Flavor(stem + "Women"),
        "Man" => Flavor(stem + "Men"),
        _ => Flavor(stem + "Women").Concat(Flavor(stem + "Men")).ToList(),
    };

    /// <summary>The prompt the gender picker offers beside Woman and Man. It is an invitation to
    /// type, never an answer — <see cref="CleanGender"/> is what guarantees it can't be stored as
    /// one. It lives here rather than on the form so the rule holds for every caller and the smoke
    /// rig can hold it to that.</summary>
    public const string GenderOther = "Other…";

    /// <summary>Tidy what came out of a gender box: trimmed, and never the prompt itself. A soul's
    /// gender is free text — the two the name lists are written for are not the only two allowed,
    /// they are only the two with their own pools of given names.</summary>
    public static string CleanGender(string gender)
    {
        string t = (gender ?? "").Trim();
        return t == GenderOther ? "" : t;
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
        BindFamiliar(s, cal);

        // Signs (Ch. VII / XIII): only the Old Dark works them by nature; Hedge Magic adds one
        var signNames = SignsFor(cal, level, s.Edges.Contains("Hedge Magic"))
                            .Select(x => x.name).ToList();                   // Ch. XIII list + Rank gate
        int signCount = cal.signsKnownAt != null ? cal.signsKnownAt[level.ToString()] : 0;
        if (s.Edges.Contains("Hedge Magic")) signCount += 1;
        while (s.SignsKnown.Count < Math.Min(signCount, signNames.Count))
        { var sg = Pick(signNames); if (!s.SignsKnown.Contains(sg)) s.SignsKnown.Add(sg); }

        // Miracles (Ch. VI): the five Callings of Faith, from their lists, gated by Rank
        var miracleNames = MiraclesFor(cal, level).Select(x => x.name).ToList();
        int miracleCount = cal.miraclesKnownAt != null ? cal.miraclesKnownAt[level.ToString()] : 0;
        while (s.MiraclesKnown.Count < Math.Min(miracleCount, miracleNames.Count))
        { var m = Pick(miracleNames); if (!s.MiraclesKnown.Contains(m)) s.MiraclesKnown.Add(m); }

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
        // Armor last, out of whatever is left. Ch. X is plain that there is precious little of it
        // out here, so it is what a soul buys after the gun, the horse and the week's rations —
        // never instead of them. Callings that already bought a duster as a sundry are dressed.
        // Most of them have already bought a duster among the sundries, so this is an upgrade
        // step, not a first purchase: walk the preference best-first and stop at the first thing
        // better than what they are standing in — or at what they are standing in.
        if (cal.buyPlan.TryGetProperty("armor", out var armorPref))
        {
            var have = ArmorFrom(s.Gear);
            foreach (var an in armorPref.EnumerateArray())
            {
                var a = D.armor.FirstOrDefault(x => x.name == an.GetString());
                if (a == null) continue;
                if (have != null && a.drBlades <= have.drBlades) break;   // nothing better left on the list
                if (left >= a.cost) { left -= a.cost; s.Gear.Add(a.gear); break; }
            }
        }
        s.CoinLeft = Math.Round(left, 2);
        ReckonNumbers(s, cal, org);   // again, now that the gear — and so the armor — is known

        // ---- Steps 1 & 8: a person, not a statline ----
        var (gender, _) = PickPerson();
        s.Gender = gender;
        // The look is drawn BEFORE the name, and the name is drawn against it — see FullName.
        // Drawn against the Calling too, because most of what a soul is wearing is what they do
        // for a living. Costs nothing and gates nothing.
        s.Look = Look.Roll(s.Gender, s.Calling);
        s.Name = FullName(s.Gender, s.Look);
        s.Compass = WeightedCompass();
        s.Lost = Pick(FlavorList("lost")); s.Seen = Pick(FlavorList("seen"));
        s.Vice = Pick(FlavorList("vices")); s.Moving = Pick(FlavorList("moving"));
        // The reckoned numbers, not the roll: "the wrong Grace" and "that Blood is too high" are the
        // reports this line exists to answer, and they are about what came out, not what went in.
        Daybook.Note("soul", $"generated {s.Name} — level {s.Level} {s.Calling}/{s.Origin}, "
                             + $"{s.Method}, Blood {s.Blood}, Nerve {s.NerveMax}"
                             + (s.PoolName != null ? $", {s.PoolName} {s.PoolMax}" : ""));
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
        public SoulLook Look;                                 // what they look like; null draws one
        public List<string> TrainedPicks = new();             // the Calling's trained skills (Origin grants ride free)
        public List<string> SkillIncreases = new();           // one target per increase earned (3/5/7/9), in order
        public List<string> Edges = new();                    // one per odd level, in order
        public List<string> BonusCombatEdges = new();         // the Gunhand's picks, one per odd level
        public List<string> Boosts = new();                   // ability per boost level reached (5, 10)
        public List<string> Signs = new();
        public List<string> Miracles = new();
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
        BindFamiliar(s, cal);

        var signNames = SignsFor(cal, level, s.Edges.Contains("Hedge Magic"))
                            .Select(x => x.name).ToList();                   // Ch. XIII list + Rank gate
        int signCount = cal.signsKnownAt != null ? cal.signsKnownAt[level.ToString()] : 0;
        if (s.Edges.Contains("Hedge Magic")) signCount += 1;
        signCount = Math.Min(signCount, signNames.Count);
        foreach (var sg in spec.Signs.Where(signNames.Contains).Distinct())
            if (s.SignsKnown.Count < signCount) s.SignsKnown.Add(sg);
        while (s.SignsKnown.Count < signCount)
        { var sg = Pick(signNames); if (!s.SignsKnown.Contains(sg)) s.SignsKnown.Add(sg); }

        var miracleNames = MiraclesFor(cal, level).Select(x => x.name).ToList();
        int miracleCount = Math.Min(cal.miraclesKnownAt != null ? cal.miraclesKnownAt[level.ToString()] : 0, miracleNames.Count);
        foreach (var m in spec.Miracles.Where(miracleNames.Contains).Distinct())
            if (s.MiraclesKnown.Count < miracleCount) s.MiraclesKnown.Add(m);
        while (s.MiraclesKnown.Count < miracleCount)
        { var m = Pick(miracleNames); if (!s.MiraclesKnown.Contains(m)) s.MiraclesKnown.Add(m); }

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
        // One entry per thing owned, repeats and all — a soul may want three lanterns or a
        // dozen candles, and the wizard now lets them buy that (2026-07-27). The coin ledger in
        // Validate already sums Gear entry by entry, so a repeat prices itself with no other
        // change; ArmorFrom takes the best single suit, so a second duster grants no second DR.
        foreach (var gn in spec.BuyGear)
        {
            if (D.gearPrices.TryGetValue(gn, out var price) && left >= price)
            { left -= price; s.Gear.Add(gn); }
        }
        s.CoinLeft = Math.Round(left, 2);
        ReckonNumbers(s, cal, org);   // the wizard buys armor like any other gear; re-reckon on it

        // a person, not a statline
        if (string.IsNullOrWhiteSpace(spec.Gender)) { var (rg, _) = PickPerson(); s.Gender = rg; }
        else s.Gender = spec.Gender.Trim();
        // The wizard's own look if it collected one, otherwise a drawn one — same rule as every
        // other line here. Before the name, because the name is drawn against it (see FullName);
        // a name the wizard was GIVEN is of course kept, and then nothing is drawn against it.
        bool named = !string.IsNullOrWhiteSpace(spec.Name);
        s.Look = spec.Look ?? Look.Roll(s.Gender, s.Calling, nameIsFixed: named);
        s.Name = named ? spec.Name.Trim() : FullName(s.Gender, s.Look);
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
        public List<string> NewSigns = new();      // signs for any slots the new level opens
        public List<string> NewMiracles = new();   // miracles for any slots the new level opens
    }

    // What a soul's next level grants — drives the level-up dialog's controls and their
    // option lists, computed on a clone advanced by the deterministic part of the level
    // (default boost + the new features) so Edge/skill eligibility reflects the new level.
    public class LevelUpGrants
    {
        public int NewLevel, HitDie, ConModForBlood;
        public bool Boost, Edge, GunEdge, SkillIncrease, Subpath, AtCeiling;
        public int NewSignSlots, NewMiracleSlots;
        public string DefaultBoost, DefaultSubpath;
        public List<string> BoostOptions = new(), EdgeOptions = new(), GunEdgeOptions = new(),
            SkillOptions = new(), SubpathOptions = new(), SignOptions = new(), MiracleOptions = new();
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
            return Math.Min(c, SignsFor(cal, lvl, cur.Edges.Contains("Hedge Magic")).Count);
        }
        g.NewSignSlots = Math.Max(0, Signs(N) - Signs(cur.Level));

        int Miracles(int lvl)
        {
            int c = cal.miraclesKnownAt != null ? cal.miraclesKnownAt[lvl.ToString()] : 0;
            return Math.Min(c, MiraclesFor(cal, lvl).Count);
        }
        g.NewMiracleSlots = Math.Max(0, Miracles(N) - Miracles(cur.Level));

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
        if (g.NewSignSlots > 0)
            g.SignOptions = SignsFor(cal, cur.Level + 1, cur.Edges.Contains("Hedge Magic")).Select(x => x.name)
                                .Where(n => !cur.SignsKnown.Contains(n)).ToList();
        if (g.NewMiracleSlots > 0)
            g.MiracleOptions = MiraclesFor(cal, cur.Level + 1).Select(x => x.name)
                                .Where(n => !cur.MiraclesKnown.Contains(n)).ToList();
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

        var signNames = SignsFor(cal, N, s.Edges.Contains("Hedge Magic"))
                            .Select(x => x.name).ToList();                   // Ch. XIII list + Rank gate
        int signCount = cal.signsKnownAt != null ? cal.signsKnownAt[N.ToString()] : 0;
        if (s.Edges.Contains("Hedge Magic")) signCount += 1;
        signCount = Math.Min(signCount, signNames.Count);
        foreach (var sg in ch.NewSigns.Where(signNames.Contains).Distinct())
            if (s.SignsKnown.Count < signCount && !s.SignsKnown.Contains(sg)) s.SignsKnown.Add(sg);
        while (s.SignsKnown.Count < signCount)
        { var sg = Pick(signNames); if (!s.SignsKnown.Contains(sg)) s.SignsKnown.Add(sg); }

        var miracleNames = MiraclesFor(cal, N).Select(x => x.name).ToList();
        int miracleCount = Math.Min(cal.miraclesKnownAt != null ? cal.miraclesKnownAt[N.ToString()] : 0, miracleNames.Count);
        foreach (var m in ch.NewMiracles.Where(miracleNames.Contains).Distinct())
            if (s.MiraclesKnown.Count < miracleCount && !s.MiraclesKnown.Contains(m)) s.MiraclesKnown.Add(m);
        while (s.MiraclesKnown.Count < miracleCount)
        { var m = Pick(miracleNames); if (!s.MiraclesKnown.Contains(m)) s.MiraclesKnown.Add(m); }

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
        // Armor (Ch. X) rides in the gear, which on the generation path is not bought until after
        // the first reckoning — hence the second call once outfitting is done. This method holds no
        // randomness and is safe to run any number of times, so Defense and Speed have exactly one
        // author and no caller has to remember to re-apply the armor itself.
        ReadArmor(s);
        var worn = ArmorFrom(s.Gear);
        s.Blood = Math.Max(1, s.BloodRolls.Sum() + rawhide);
        s.Defense = 10 + Mod(s.Scores["DEX"]) + (worn?.defense ?? 0);
        s.Fort = row.fort + Mod(s.Scores["CON"]);
        s.Ref = row.@ref + Mod(s.Scores["DEX"]);
        s.Will = row.will + Mod(s.Scores["RES"]);
        s.Attack = row.atk;
        s.NerveMax = s.Scores["RES"] + level + stoneNerve;
        s.Grit = 3;
        s.Speed = 30 + (s.Edges.Contains("Fleet") ? 10 : 0) + (worn?.speed ?? 0);
        s.Mark = org.startMark + cal.startMark + (s.Edges.Contains("Touched") ? 1 : 0);

        if (cal.pool != null)
        {
            int baseMod = Mod(s.Scores[cal.pool.formula.Substring(0, 3)]);
            int val = cal.pool.formula.EndsWith("level") ? baseMod + level : baseMod + level / 2;
            val = Math.Max(cal.pool.min, val);
            string refresh = cal.pool.formula.EndsWith("level") ? "RES mod + level" : cal.pool.formula.Substring(0, 3) + " mod + half level";
            s.PoolLine = $"{cal.pool.name} {val} ({refresh}, refreshed each dawn)";
            s.PoolName = cal.pool.name;
            s.PoolMax = val;
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
        // Armor is worn out of the gear, so Defense and Speed carry its modifier (Ch. X).
        var worn = ArmorFrom(s.Gear);
        Check(s.ArmorWorn == worn?.name, $"ArmorWorn \"{s.ArmorWorn}\" ≠ best armor in the gear \"{worn?.name}\"");
        Check(s.DrBlades == (worn?.drBlades ?? 0), $"DR vs blades {s.DrBlades} ≠ Ch. X row for {worn?.name ?? "no armor"}");
        Check(s.DrShot == (worn?.drShot ?? 0), $"DR vs small shot {s.DrShot} ≠ Ch. X row for {worn?.name ?? "no armor"}");
        Check(s.Defense == 10 + Mod(s.Scores["DEX"]) + (worn?.defense ?? 0),
            $"Defense {s.Defense} ≠ 10 + DEX mod + armor {worn?.defense ?? 0}");
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
        // the faith/sign pool (re-derived so a bad transcription can't drift; 0 for Callings without one)
        int expectPool = 0;
        if (cal.pool != null)
        {
            int baseMod = Mod(s.Scores[cal.pool.formula.Substring(0, 3)]);
            expectPool = Math.Max(cal.pool.min, cal.pool.formula.EndsWith("level") ? baseMod + s.Level : baseMod + s.Level / 2);
        }
        Check(s.PoolMax == expectPool, $"pool {s.PoolMax} ≠ {cal.pool?.name ?? "none"} formula {expectPool}");
        Check(s.Grit == 3, "Grit must be 3");
        Check(s.Speed == 30 + (s.Edges.Contains("Fleet") ? 10 : 0) + (ArmorFrom(s.Gear)?.speed ?? 0),
            "Speed ≠ 30 (+Fleet, +armor)");

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
        var legal = SignsFor(cal, s.Level, owned.Contains("Hedge Magic"));
        expectSigns = Math.Min(expectSigns, legal.Count);
        Check(s.SignsKnown.Count == expectSigns, $"{s.SignsKnown.Count} signs ≠ {expectSigns} allowed");
        Check(!(isFaith && s.SignsKnown.Count > 0), "a Calling of Faith may never work a Sign (Ch. XIII)");
        Check(s.SignsKnown.Distinct().Count() == s.SignsKnown.Count, "duplicate sign");
        // Ch. XIII: a Sign must sit on one of the Calling's lists and at a Rank the level has opened.
        // Checked here rather than trusted, so a mis-listed Sign in the data cannot pass silently.
        foreach (var sg in s.SignsKnown)
        {
            var sign = D.signs.FirstOrDefault(x => x.name == sg);
            Check(sign != null, $"unknown sign {sg}");
            if (sign == null) continue;
            Check(legal.Any(x => x.name == sg),
                $"{cal.name} L{s.Level} may not know {sg} (Rank {sign.rank}, {sign.list} list)");
        }

        // Miracles (Ch. VI): the five Callings of Faith, from their lists, gated by the same Rank.
        // The Old Dark and the mundane never hold one; a Calling never mixes Signs and Miracles.
        int expectMiracles = cal.miraclesKnownAt != null ? cal.miraclesKnownAt[s.Level.ToString()] : 0;
        var legalM = MiraclesFor(cal, s.Level);
        expectMiracles = Math.Min(expectMiracles, legalM.Count);
        Check(s.MiraclesKnown.Count == expectMiracles, $"{s.MiraclesKnown.Count} miracles ≠ {expectMiracles} allowed");
        Check(!(s.SignsKnown.Count > 0 && s.MiraclesKnown.Count > 0), "no soul works both Signs and Miracles");
        Check(s.MiraclesKnown.Distinct().Count() == s.MiraclesKnown.Count, "duplicate miracle");
        foreach (var mk in s.MiraclesKnown)
        {
            var mir = D.miracles.FirstOrDefault(x => x.name == mk);
            Check(mir != null, $"unknown miracle {mk}");
            if (mir == null) continue;
            Check(legalM.Any(x => x.name == mk),
                $"{cal.name} L{s.Level} may not know {mk} (Rank {mir.rank}, {mir.list} list)");
        }

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
        sb.AppendLine("Armor " + (string.IsNullOrEmpty(s.ArmorWorn)
            ? "none — no DR; cover and not being shot are your whole defense"
            : ArmorLine(s)));
        if (cal.signsKnownAt != null)
            sb.AppendLine($"Sign DC {10 + s.Level / 2 + Mod(s.Scores["RES"])} (10 + half level + RES mod)");
        else if (s.SignsKnown.Count > 0)
            sb.AppendLine($"Sign DC {10 + Mod(s.Scores["RES"])} (Hedge Magic — no Signs feature, so no level added)");
        if (cal.miraclesKnownAt != null)
        {
            string fa = cal.pool.formula.Substring(0, 3);
            sb.AppendLine($"Miracle DC {10 + s.Level / 2 + Mod(s.Scores[fa])} (10 + half level + {fa} mod)");
        }
        if (s.PoolLine != null) sb.AppendLine(s.PoolLine);
        sb.AppendLine();

        string Rank(int r) => r switch { 3 => " (Master)", 2 => " (Expert)", _ => "" };
        sb.AppendLine("TRAINED — " + string.Join(", ", s.SkillRanks.OrderByDescending(kv => kv.Value).ThenBy(kv => kv.Key)
            .Select(kv => kv.Key + Rank(kv.Value))));
        sb.AppendLine();

        sb.AppendLine("FEATURES");
        foreach (var f in s.Features)
        {
            string desc = FeatureText(cal, f);
            var lim = ReadLimit(desc);
            sb.AppendLine("   " + f + (lim.Any ? $"  [{lim.Says(s)}]" : "")
                                    + (desc != null ? " — " + FirstSentence(desc) : ""));
        }
        if (s.Subpath != null)
        {
            var opt = cal.subpath.options.First(o => o.name == s.Subpath);
            sb.AppendLine($"   {cal.subpath.section}: {opt.name} — {FirstSentence(opt.boon)}");
        }
        // The familiar's own line replaces the bare "Familiar: a crow" the choice would print,
        // because the beast carries mechanics the other two choices do not.
        var fam = FamiliarLine(s);
        if (fam != null) sb.AppendLine("   " + fam);
        else if (s.CallingChoice != null) sb.AppendLine("   " + s.CallingChoice);
        sb.AppendLine();

        sb.AppendLine("EDGES");
        var allEdges = D.edges.Concat(D.callingEdges).ToList();
        foreach (var e in s.Edges) sb.AppendLine("   " + e + " — " + allEdges.First(x => x.name == e).desc);
        foreach (var e in s.BonusCombatEdges) sb.AppendLine("   " + e + " (Gunhand's Edge) — " + allEdges.First(x => x.name == e).desc);
        sb.AppendLine();

        if (s.SignsKnown.Count > 0)
        {
            sb.AppendLine($"SIGNS KNOWN — {string.Join(" + ", cal.signLists ?? new())}, to Rank {SignRankAt(s.Level)}");
            foreach (var d in s.SignsKnown.Select(n => D.signs.First(x => x.name == n)).OrderBy(x => x.rank))
                sb.AppendLine($"   Rank {d.rank}  {d.name} ({d.cost}) — {FirstSentence(d.desc)}");
            sb.AppendLine();
        }

        if (s.MiraclesKnown.Count > 0)
        {
            sb.AppendLine($"MIRACLES KNOWN — {string.Join(" + ", cal.miracleLists ?? new())}, to Rank {MiracleRankAt(s.Level)}");
            foreach (var d in s.MiraclesKnown.Select(n => D.miracles.First(x => x.name == n)).OrderBy(x => x.rank))
                sb.AppendLine($"   Rank {d.rank}  {d.name} ({d.cost}) — {FirstSentence(d.desc)}");
            sb.AppendLine();
        }

        sb.AppendLine($"ORIGIN — {org.name}: {org.line}");
        sb.AppendLine("   Boon: " + org.boon);
        sb.AppendLine("   Burden: " + org.burden);
        sb.AppendLine();

        sb.AppendLine($"GEAR   (rolled ${s.CoinRolled:0} {cal.coin.note}{(cal.coin.note != "" ? ", " : "")}${s.CoinLeft:0.##} left)");
        foreach (var g in Tally(s.Gear)) sb.AppendLine("   " + g);
        sb.AppendLine();

        sb.AppendLine("THE FOUR QUESTIONS");
        sb.AppendLine("   Lost:   " + s.Lost);
        sb.AppendLine("   Seen:   " + s.Seen);
        sb.AppendLine("   Vice:   " + s.Vice);
        sb.AppendLine("   Moving: " + s.Moving);

        // Last, and only if there is one: a sheet saved before v1.30 has no look, and a heading
        // with four empty lines under it is worse than no heading. Every line is guarded the same
        // way, because any one field can be cleared by hand.
        if (s.Look is { Any: true })
        {
            sb.AppendLine();
            sb.AppendLine("APPEARANCE" + (string.IsNullOrWhiteSpace(s.Look.People) ? "" : "   (" + s.Look.People + ")"));
            void Row(string label, string value)
            { if (!string.IsNullOrWhiteSpace(value)) sb.AppendLine("   " + label.PadRight(8) + value); }
            Row("Build:", s.Look.BodyLine);
            Row("Face:", s.Look.FaceLine);
            Row("Wearing:", string.IsNullOrWhiteSpace(s.Look.Style) ? s.Look.DressLine
                : $"{s.Look.Style} — {s.Look.DressLine}");
            Row("Detail:", s.Look.Detail);
        }
        return sb.ToString();
    }

    // ============================================ reading a feature's limit out of its own prose

    // The book states every limit in the sentence, so the sentence is where this reads it. The
    // alternative — a `uses` column typed into chargen.json beside the description — is a second
    // copy of a fact, and the twenty repaired descriptions of 2026-08-19 are what a second copy
    // does when nobody is auditing it. See audits/verify_rules.py.
    //
    // Ordered most specific first. "a number of times per scene equal to your PRE modifier" has to
    // beat the bare "per scene", and a fight and an encounter are a scene by another name.
    static readonly System.Text.RegularExpressions.Regex FormulaUses = new(
        @"a number of times per (?<when>turn|round|scene|fight|encounter|session)\s+equal to your\s+"
        + @"(?<abl>STR|DEX|CON|WIT|RES|PRE) modifier(?<half>\s*\+\s*half your level)?"
        + @"(?:\s*\(minimum (?<min>\d+)\))?",
        System.Text.RegularExpressions.RegexOptions.IgnoreCase);

    static readonly System.Text.RegularExpressions.Regex PreparedEachDawn = new(
        @"(?:each|every) dawn[^.]{0,40}?prepare a number of [a-z ]{1,24}equal to your\s+"
        + @"(?<abl>STR|DEX|CON|WIT|RES|PRE) modifier(?<half>\s*\+\s*half your level)?"
        + @"(?:\s*\(minimum (?<min>\d+)\))?",
        System.Text.RegularExpressions.RegexOptions.IgnoreCase);

    static readonly System.Text.RegularExpressions.Regex CountedUses = new(
        @"\b(?<n>once|twice|three times|four times|five times|\d+ times) per\s+"
        + @"(?<when>turn|round|scene|fight|encounter|session|quarry|wound|patient|target)\b",
        System.Text.RegularExpressions.RegexOptions.IgnoreCase);

    static FeatureCadence WhenOf(string w) => w.ToLowerInvariant() switch
    {
        "turn" => FeatureCadence.Turn,
        "round" => FeatureCadence.Round,
        // A fight IS a scene at this table, and the book uses both words for the same boundary.
        "scene" or "fight" or "encounter" => FeatureCadence.Scene,
        // Once per quarry, once per wound: the fiction says when, so the Keeper does.
        "quarry" or "wound" or "patient" or "target" => FeatureCadence.Trigger,
        _ => FeatureCadence.Session,
    };

    static int CountOf(string n) => n.ToLowerInvariant() switch
    {
        "once" => 1, "twice" => 2, "three times" => 3, "four times" => 4, "five times" => 5,
        _ => int.TryParse(n.Split(' ')[0], out int v) ? v : 1,
    };

    /// <summary>The sentence a limit lives in, so the tooltip can show the rule and not a summary.</summary>
    static string SentenceAround(string text, int at)
    {
        int lo = text.LastIndexOf(". ", Math.Min(at, text.Length - 1), StringComparison.Ordinal);
        lo = lo < 0 ? 0 : lo + 2;
        int hi = text.IndexOf(". ", at, StringComparison.Ordinal);
        hi = hi < 0 ? text.Length : hi + 1;
        return text.Substring(lo, hi - lo).Trim();
    }

    /// <summary>How often this feature may be used, read from its description. A description that
    /// states no limit — or states one about something ongoing rather than something pressed —
    /// comes back as <see cref="FeatureCadence.None"/>.</summary>
    public static FeatureLimit ReadLimit(string desc)
    {
        if (string.IsNullOrWhiteSpace(desc)) return default;

        var m = FormulaUses.Match(desc);
        if (m.Success)
            return new FeatureLimit
            {
                Cadence = WhenOf(m.Groups["when"].Value),
                Ability = m.Groups["abl"].Value.ToUpperInvariant(),
                HalfLevel = m.Groups["half"].Success,
                Min = m.Groups["min"].Success ? int.Parse(m.Groups["min"].Value) : 1,
                Phrase = SentenceAround(desc, m.Index),
            };

        m = PreparedEachDawn.Match(desc);
        if (m.Success)
            return new FeatureLimit
            {
                Cadence = FeatureCadence.Dawn,
                Ability = m.Groups["abl"].Value.ToUpperInvariant(),
                HalfLevel = m.Groups["half"].Success,
                Min = m.Groups["min"].Success ? int.Parse(m.Groups["min"].Value) : 1,
                Phrase = SentenceAround(desc, m.Index),
            };

        m = CountedUses.Match(desc);
        if (m.Success)
            return new FeatureLimit
            {
                Cadence = WhenOf(m.Groups["when"].Value),
                Uses = CountOf(m.Groups["n"].Value),
                Phrase = SentenceAround(desc, m.Index),
            };

        return default;
    }

    // A tally is the opposite of a ration: it climbs, and no boundary returns it. The book states
    // one in the shape "on your third Debt the Patron calls it in", so that is what is matched —
    // the count, the thing counted, and the sentence it lives in. Deliberately narrow: a looser
    // pattern would start reading "on your first turn" as a debt, and a counter the app invented
    // is worse than a counter it lacks.
    static readonly System.Text.RegularExpressions.Regex TallyThreshold = new(
        @"\bon your (?<n>first|second|third|fourth|fifth) (?<noun>[A-Za-z][A-Za-z-]{2,20})\b",
        System.Text.RegularExpressions.RegexOptions.IgnoreCase);

    static int OrdinalOf(string w) => w.ToLowerInvariant() switch
    {
        "first" => 1, "second" => 2, "third" => 3, "fourth" => 4, "fifth" => 5, _ => 0,
    };

    /// <summary>The accumulating tally a feature's prose declares, or
    /// <see cref="FeatureTally.Any"/> false when it declares none — which is all but one of them.
    /// </summary>
    public static FeatureTally ReadTally(string desc)
    {
        if (string.IsNullOrWhiteSpace(desc)) return default;
        var m = TallyThreshold.Match(desc);
        if (!m.Success) return default;
        int at = OrdinalOf(m.Groups["n"].Value);
        if (at <= 0) return default;
        // The book capitalises the thing counted where it is a game noun ("a Debt"); a lowercase
        // word after "on your third" is ordinary prose ("on your third try") and is not a tally.
        string noun = m.Groups["noun"].Value;
        if (!char.IsUpper(noun[0])) return default;
        return new FeatureTally { Noun = noun, At = at, Phrase = SentenceAround(desc, m.Index) };
    }

    /// <summary>Which key in <see cref="CgCalling.featureDescs"/> a level table's feature name means.
    ///
    /// <para>The two do not always match on the nose: a level row prints "Judgment 3d8" or
    /// "Dead Aim +1d6" where the prose heads its section "Judgment", and the Drifter's 6th-level
    /// row names one entry that the book writes up as "Ghost / Uncanny Step / Vanish". This is the
    /// one place that reconciliation lives — it used to be three chained lookups inline in
    /// <c>Render</c>, where nothing else could reach it.</para></summary>
    public static string FeatureKey(CgCalling cal, string feature)
    {
        if (cal?.featureDescs == null || string.IsNullOrEmpty(feature)) return null;
        var keys = cal.featureDescs.Keys;
        if (keys.Contains(feature)) return feature;

        // A level table prints the die in the column — "Judgment 3d8", "Dead Aim +1d6",
        // "Precise Strike 2d6" — where the prose heads the section by name alone.
        string stem = DieSuffix.Replace(feature, "").Trim();
        foreach (var k in keys) if (k == stem) return k;
        foreach (var k in keys) if (feature.StartsWith(k, StringComparison.Ordinal)) return k;

        // Three features can share one heading: the Drifter's "Ghost / Uncanny Step / Vanish" is
        // written up once and named a level at a time, and so is the Marshal's "Hold the Line /
        // Unflinching" and the Sawbones' "Anatomist / Precise Strike".
        foreach (var k in keys)
            foreach (var part in k.Split(" / "))
                if (part == stem || part == feature) return k;

        foreach (var k in keys) if (k.Contains(stem, StringComparison.Ordinal)) return k;
        return null;
    }

    static readonly System.Text.RegularExpressions.Regex DieSuffix =
        new(@"\s*\+?\s*\d+d\d+\s*$");

    /// <summary>The whole of what the book says about this feature, or null.</summary>
    public static string FeatureText(CgCalling cal, string feature)
        => FeatureKey(cal, feature) is string k ? cal.featureDescs[k] : null;

    /// <summary>How often this Calling's feature may be used.</summary>
    public static FeatureLimit LimitOf(CgCalling cal, string feature)
        => ReadLimit(FeatureText(cal, feature));

    /// <summary>Every feature a soul of this Calling and level has, paired with its limit — the
    /// list the Tracker's Calling strip is built from. Features that are really a slot rather than
    /// a thing you do (an Edge, a Sign learned, a Stolen Wonder) are left out, the same three the
    /// sheet's own feature list leaves out.</summary>
    public static List<(string Name, string Desc, FeatureLimit Limit)> FeaturesAt(
        string callingName, int level, string subpathChoice = null)
    {
        var cal = D?.callings?.FirstOrDefault(c => c.name == callingName);
        var list = new List<(string, string, FeatureLimit)>();
        if (cal == null) return list;

        // The printed table sets the two subpath entries in bold; the data cannot carry weight, so
        // find them by the suffix instead — "Trade Mastery" at 10th for the Worldly and the
        // Faithful, "Devotion (Greater)" at 9th for the three of the Old Dark. The word in front of
        // that suffix is what the 3rd-level row calls the choice, and the two are a pair.
        string greater = cal.rows.Where(r => r.level >= 9).SelectMany(r => r.features ?? new())
            .FirstOrDefault(f => f.EndsWith(" Mastery", StringComparison.Ordinal)
                              || f.EndsWith(" (Greater)", StringComparison.Ordinal));
        string pick = greater?.Replace(" Mastery", "").Replace(" (Greater)", "");

        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (var row in cal.rows.Where(r => r.level <= Math.Clamp(level, 1, 10)).OrderBy(r => r.level))
            foreach (var f in row.features ?? new())
            {
                if (f == "Edge" || f.StartsWith("Sign learned", StringComparison.Ordinal)
                                || f.StartsWith("Stolen Wonder", StringComparison.Ordinal)) continue;
                // Level 3 and up, because the Dark Cultist's 1st-level Devotion is the pool they
                // spend and their 3rd-level Devotion is the path they walk. Same word, and the
                // book means two different things by it.
                bool isPath = cal.subpath != null && row.level >= 3 && (f == pick || f == greater);
                var entry = isPath ? Subpath(cal, f == greater, subpathChoice)
                                   : (f, FeatureText(cal, f), LimitOf(cal, f));
                if (seen.Add(entry.Item1)) list.Add(entry);
            }
        return list;
    }

    /// <summary>The 3rd-level path and its 10th-level mastery — "Game" and "Game Mastery" on the
    /// Gambler's table, "Order" and "Order Mastery" on the Padre's. No featureDescs entry covers
    /// them: the rules live in <see cref="CgSubpath.options"/>, one boon per option, and half the
    /// Callings' Mastery abilities are in there. Left unresolved they were the only features in
    /// the app with no text at all — the 3rd-level choice a player makes and then cannot read.
    ///
    /// <para>Once a soul has chosen, this narrows to their own boon, and the mastery half narrows
    /// again to the sentence after the marker. Before they have chosen, it lists what is on
    /// offer, which is what a player at 3rd level is actually deciding between.</para></summary>
    static (string, string, FeatureLimit) Subpath(CgCalling cal, bool greater, string chosen)
    {
        var opt = cal.subpath.options.FirstOrDefault(o => o.name == chosen);
        if (opt == null)
            return (cal.subpath.section + (greater ? " — the greater boon" : ""),
                    cal.subpath.section + " — chosen at 3rd level: "
                        + string.Join("; ", cal.subpath.options.Select(o => o.name)),
                    default);

        string boon = opt.boon;
        int cut = MasteryMark.Match(boon) is { Success: true } m ? m.Index : -1;
        string text = cut < 0 ? boon
                    : greater ? boon.Substring(cut).Trim()
                              : boon.Substring(0, cut).Trim();
        return ($"{cal.subpath.section}: {opt.name}" + (greater ? " — greater" : ""),
                text, ReadLimit(text));
    }

    /// <summary>What a card or a sheet should CALL a feature, which is not always the key it is
    /// stored under. <see cref="Subpath"/> keys a 3rd-level path as the section, a colon, and the
    /// option — so the key stays unique across seventeen Callings that all print a path at 3rd.
    /// On a 232px card that ellipsised to the section and three letters of the option: character
    /// for character the same on the 3rd-level card and on the 9th-level greater one sitting next
    /// to it, so the Tracker strip showed a Hexer two cards they could not tell apart.
    ///
    /// <para>The strip already names the Calling in its head line, so the section is the half worth
    /// dropping. Structural rather than an exemption list: the separator is there because
    /// <see cref="Subpath"/> puts it there, and nothing off a level table carries one. Display only
    /// — <c>FeatureSpent</c> and <c>TallyOwed</c> are still keyed by the whole string, so trimming
    /// here cannot orphan a saved session.</para></summary>
    public static string ShortFeatureName(string key)
    {
        int cut = key?.IndexOf(": ", StringComparison.Ordinal) ?? -1;
        return cut > 0 ? key.Substring(cut + 2) : key;
    }

    // Worldly and Faith paths deepen at 10th and say "Mastery (10th):"; the three Callings of the
    // Old Dark deepen a level earlier and say "Greater (9th):". Both are the same seam.
    static readonly System.Text.RegularExpressions.Regex MasteryMark =
        new(@"(?:Mastery \(10th\)|Greater \(9th\))\s*:", System.Text.RegularExpressions.RegexOptions.IgnoreCase);

    // ------------------------------------------- what the ORIGIN is worth at the table

    /// <summary>Cut a description into sentences, so each one can be read for a limit of its own.
    ///
    /// <para>An Origin states more than one rationed thing in a single paragraph — the Veteran's
    /// boon holds <em>"Once per session steady the line"</em> and <em>"once per scene reroll a
    /// failed Reflex save"</em> in one breath — and <see cref="ReadLimit"/> answers with the first
    /// match it finds. Handing it the whole paragraph would therefore have quietly dropped the
    /// second half of four Origins.</para>
    ///
    /// <para><b>The semicolon counts as a full stop here, and that is the whole trick.</b> Ch. IV
    /// writes its second clause in lower case after a semicolon — <em>"…for a round; once per scene
    /// reroll a failed Reflex save"</em> — so a split that demanded a capital letter found one
    /// sentence where the book states two, and the Veteran's second ration went missing. Caught by
    /// running the reader over all ten Origins and reading what came out, which is the only way
    /// this kind of fault ever shows: every assertion about the first half passes perfectly.</para>
    ///
    /// <para>No decimal is at risk — this book writes <c>1d6</c> and <c>−2</c>, never <c>1.5</c> —
    /// so the split needs no lookahead beyond the whitespace.</para></summary>
    static IEnumerable<string> Sentences(string text)
        => string.IsNullOrWhiteSpace(text)
         ? System.Linq.Enumerable.Empty<string>()
         : System.Text.RegularExpressions.Regex.Split(text.Trim(), @"(?<=[.;])\s+")
                 .Where(s => !string.IsNullOrWhiteSpace(s));

    /// <summary>What a soul's ORIGIN puts on the Tracker's strip.
    ///
    /// <para>Ch. IV gives every Origin a <b>boon</b> and a <b>burden</b>, and until v1.49.0 the app
    /// printed both on the sheet and counted neither. Five of the ten ration an activation in so
    /// many words — <em>"Once per session, when you would drop to 0 Blood…"</em> — which is the same
    /// sentence shape the Callings use and so is read by the same <see cref="ReadLimit"/>. This is
    /// deliberately NOT a <c>uses</c> column added to <c>chargen.json</c>: that file is a
    /// transcription, and a second copy of a fact beside the prose is what the twenty repaired
    /// descriptions of 2026-08-19 were.</para>
    ///
    /// <para>Keyed <c>"Origin: &lt;name&gt;"</c> so the key cannot collide with a Calling feature in
    /// <see cref="PartyMember.FeatureSpent"/>, and so <see cref="ShortFeatureName"/> — which trims
    /// at the colon for exactly this reason — shows a card that says <em>Came Back Wrong</em>
    /// rather than the word <em>Origin</em>. Where one half states two rationed things, the second
    /// takes a numeral, because a card a player cannot tell from its neighbour is the fault
    /// v1.44.0 fixed for the Hexer's two Bargain cards.</para></summary>
    public static List<(string Name, string Desc, FeatureLimit Limit)> OriginFeatures(string originName)
    {
        var list = new List<(string, string, FeatureLimit)>();
        var o = D?.origins?.FirstOrDefault(x => x.name == originName);
        if (o == null) return list;

        int n = 0;
        foreach (var half in new[] { o.boon, o.burden })
            foreach (var sentence in Sentences(half))
            {
                var lim = ReadLimit(sentence);
                if (!lim.Any) continue;
                n++;
                list.Add(($"Origin: {o.name}" + (n > 1 ? $" ({n})" : ""), sentence, lim));
            }
        return list;
    }

    /// <summary>The standing ± an Origin carries, and what it is conditional on.
    ///
    /// <para>The other half of Ch. IV, and the half no counter can hold: the Scout is <em>"+2 on
    /// Notice against ambush… −1 on Notice indoors"</em>, and the app does not know whether the
    /// posse is indoors. So these are never applied behind the Keeper's back — they are
    /// <b>offered</b>, the way a creature's attack rider is and for the same reason. What the app
    /// contributes is that it knows WHICH ones this soul has and what the book says they are worth,
    /// so a Keeper stops having to remember that the Fallen Gentry is worse at going hungry.</para>
    ///
    /// <para>The sign, the size and the skill or save all come off the book's own sentence. A
    /// modifier typed into the data beside the prose would be the same second copy
    /// <see cref="OriginFeatures"/> refuses, and this project has paid for second copies
    /// twice.</para></summary>
    public static List<OriginEdge> OriginEdges(string originName)
    {
        var list = new List<OriginEdge>();
        var o = D?.origins?.FirstOrDefault(x => x.name == originName);
        if (o == null) return list;

        foreach (var (half, isBoon) in new[] { (o.boon, true), (o.burden, false) })
            foreach (var sentence in Sentences(half))
                foreach (System.Text.RegularExpressions.Match m in StandingMod.Matches(sentence))
                {
                    int size = int.Parse(m.Groups["n"].Value);
                    if (m.Groups["sign"].Value is "−" or "-") size = -size;
                    list.Add(new OriginEdge
                    {
                        Origin = o.name,
                        Size = size,
                        Applies = Tidy(m.Groups["what"].Value),
                        Phrase = sentence.Trim(),
                        IsBoon = isBoon,
                    });
                }
        return list;
    }

    // "+2 on Fortitude saves against fatigue", "−1 on checks of fine dexterity", "+2 to slip a
    // bond". The book writes every one of them as sign, digit, then "on"/"to"/"with"/"against" and
    // the thing — so the shape is the book's, not one invented here.
    //
    // The PREPOSITION is inside the capture on purpose. Left out, the chip for "+2 with criminals
    // and fences" renders as "+2 criminals", which reads like a typo rather than a rule; the
    // book's own word costs four characters and makes the chip a sentence.
    static readonly System.Text.RegularExpressions.Regex StandingMod =
        new(@"(?<sign>[+−-])(?<n>\d+)\s+(?<what>(?:on|to|with|against)\s+[^,.;:]+)",
            System.Text.RegularExpressions.RegexOptions.IgnoreCase);

    static string Tidy(string s)
    {
        s = s.Trim();
        // The book runs a clause on with "and" more often than it punctuates it, and a chip that
        // reads "on Notice against ambush, tracks, and lying-in-wait out of doors and never
        // surprised" is a chip nobody reads. One clause is the whole of what a chip is for.
        // An em dash opens a gloss on the clause just made — "against plain hardships — hunger,
        // exposure, hard labor" — and the gloss is the tooltip's job, not the chip's.
        foreach (var stop in new[] { " and ", " — " })
        {
            int at = s.IndexOf(stop, StringComparison.OrdinalIgnoreCase);
            if (at > 0) s = s.Substring(0, at);
        }
        // Four of these are printed inside a parenthetical aside — "(−1 on first impressions with
        // the breathing)" — so the closing bracket rides in on the last word.
        return s.TrimEnd('.', ')', ' ');
    }

    // ------------------------------------------- spending a feature, and getting it back

    /// <summary>Every limited feature this soul has, with how many uses are left on each. The
    /// Tracker's Calling strip is drawn straight off this, and so is the answer to "can I?".</summary>
    public static List<(string Name, string Desc, FeatureLimit Limit, int Left, int Of)> LedgerFor(PartyMember p)
    {
        var outp = new List<(string, string, FeatureLimit, int, int)>();
        if (p == null) return outp;
        // The Origin's rations come first, because Ch. III picks an Origin before a Calling and
        // because they are the ones a table forgets — a Calling's features get read every level,
        // an Origin's boon gets read once at character creation and never again.
        foreach (var f in OriginFeatures(p.Sheet?.Origin).Concat(
                          FeaturesAt(p.Calling, p.Level, p.Sheet?.Subpath)))
        {
            if (!f.Limit.Any) continue;
            int of = f.Limit.UsesFor(p.Sheet);
            p.FeatureSpent.TryGetValue(f.Name, out int used);
            outp.Add((f.Name, f.Desc, f.Limit, Math.Max(0, of - used), of));
        }
        return outp;
    }

    /// <summary>Why this feature cannot be used right now, or null when it can. Paired with
    /// <see cref="SpendFeature"/> on purpose: a control that greys without saying why is reported
    /// as broken, so the answer and the reason come from one place (same shape as
    /// <c>Rules.CanSpendBeats</c> and <c>Rules.WhyNoBeats</c>).</summary>
    public static string WhyNotFeature(PartyMember p, string feature)
    {
        if (p == null) return "Nobody is selected.";
        var row = LedgerFor(p).FirstOrDefault(r => r.Name == feature);
        if (row.Name == null) return $"{p.Name} has no feature called {feature}.";
        if (row.Left > 0) return null;
        return row.Limit.Cadence switch
        {
            FeatureCadence.Turn => $"{feature} is spent for this turn — it comes back on their next one.",
            FeatureCadence.Round => $"{feature} is spent for this round.",
            FeatureCadence.Scene => $"{feature} is spent for this scene — a new fight returns it.",
            FeatureCadence.Dawn => $"{feature} is spent until they prepare again at dawn — a long rest returns it.",
            FeatureCadence.Trigger => $"{feature} is spent. {row.Limit.Phrase}",
            _ => $"{feature} is spent for the session. Nothing short of the next one returns it.",
        };
    }

    /// <summary>Spend one use. False when there was none to spend — ask
    /// <see cref="WhyNotFeature"/> for the sentence to show.</summary>
    public static bool SpendFeature(PartyMember p, string feature)
    {
        if (WhyNotFeature(p, feature) != null) return false;
        p.FeatureSpent.TryGetValue(feature, out int used);
        p.FeatureSpent[feature] = used + 1;
        p.Touched(nameof(PartyMember.FeatureSpent));
        return true;
    }

    /// <summary>Give one back — the Keeper's undo for a press that was a mis-click or a rule the
    /// table decided differently.</summary>
    public static bool UnspendFeature(PartyMember p, string feature)
    {
        if (p == null || !p.FeatureSpent.TryGetValue(feature, out int used) || used <= 0) return false;
        if (used == 1) p.FeatureSpent.Remove(feature); else p.FeatureSpent[feature] = used - 1;
        // AFTER the mutation, never before it. Announcing first tells the app to look at a table
        // that has not changed yet, and with no handle to defer through — the self-test rig, and
        // any early-startup path — the capture happens on the spot and the real change lands behind
        // it, unseen. Found by AuditUndo on its first run against this method, which is what that
        // audit is for.
        p.Touched(nameof(PartyMember.FeatureSpent));
        return true;
    }

    /// <summary>A boundary has passed: return everything that comes back at or before it. A scene
    /// returns the turn, round and scene features and leaves the once-a-session ones spent; a long
    /// rest reaches the dawn ones as well; a new session returns the lot. Answers with how many
    /// features actually came back, so the caller can say so rather than logging a boundary that
    /// changed nothing.</summary>
    public static int RefreshFeatures(PartyMember p, FeatureCadence upTo)
    {
        // FeatureSpent only, on purpose: PartyMember.TallyOwed is a separate store precisely so
        // that no boundary can reach it. See the note there before wiring a reset through here.
        if (p == null || p.FeatureSpent.Count == 0) return 0;
        int gave = 0;
        foreach (var row in LedgerFor(p))
        {
            if (row.Limit.Cadence > upTo) continue;
            if (p.FeatureSpent.Remove(row.Name)) gave++;
        }
        if (gave > 0) p.Touched(nameof(PartyMember.FeatureSpent));
        return gave;
    }

    // ------------------------------------------- what a soul owes, and who is owed it

    /// <summary>Every feature of this soul's that keeps a running tally, with what stands against
    /// it. Drawn on the Tracker's Calling strip beside the rationed cards, and read by the Ledger.
    /// <para>Empty for all but a Hexer who has chosen the Pact-Sworn, which is correct: a card for
    /// a debt nobody can owe teaches a Keeper to stop reading the strip.</para></summary>
    public static List<(string Name, string Desc, FeatureTally Tally, int Owed)> TalliesFor(PartyMember p)
    {
        var outp = new List<(string, string, FeatureTally, int)>();
        if (p == null) return outp;
        foreach (var f in FeaturesAt(p.Calling, p.Level, p.Sheet?.Subpath))
        {
            var t = ReadTally(f.Desc);
            if (!t.Any) continue;
            p.TallyOwed.TryGetValue(f.Name, out int owed);
            outp.Add((f.Name, f.Desc, t, Math.Max(0, owed)));
        }
        return outp;
    }

    /// <summary>Take one on. Answers with what now stands and whether that is the one that comes
    /// due, so the caller can say the book's own consequence out loud rather than logging a
    /// number and leaving the Keeper to notice.</summary>
    public static (int Owed, bool Due) TakeTally(PartyMember p, string feature)
    {
        var row = TalliesFor(p).FirstOrDefault(r => r.Name == feature);
        if (row.Name == null) return (0, false);
        p.TallyOwed.TryGetValue(feature, out int owed);
        owed++;
        p.TallyOwed[feature] = owed;
        p.Touched(nameof(PartyMember.TallyOwed));
        return (owed, owed >= row.Tally.At);
    }

    /// <summary>Strike one off — the Patron collected, or the table read it differently, or it was
    /// a mis-click. Never happens on its own: see PartyMember.TallyOwed.</summary>
    public static bool ForgiveTally(PartyMember p, string feature)
    {
        if (p == null || !p.TallyOwed.TryGetValue(feature, out int owed) || owed <= 0) return false;
        if (owed == 1) p.TallyOwed.Remove(feature); else p.TallyOwed[feature] = owed - 1;
        p.Touched(nameof(PartyMember.TallyOwed));
        return true;
    }

    static string FirstSentence(string t)
    {
        if (string.IsNullOrEmpty(t)) return "";
        int i = t.IndexOf(". ");
        return i > 0 && i < 220 ? t.Substring(0, i + 1) : (t.Length > 220 ? t.Substring(0, 220) + "…" : t);
    }

    // ------------------------------------------------------------------ the Witch's familiar

    /// <summary>How much the standing boon is worth, in the one place the book's number lives.
    /// The sentence on the sheet is built from it and <see cref="FamiliarBoonOn"/> adds it, so the
    /// printed line and the number a Keeper rolls against cannot part company.</summary>
    public const int FamiliarBoonSize = 2;

    /// <summary>Which skill each bound beast lifts, on its own, as a name a lookup can use.
    ///
    /// <para>Split out of <see cref="FamiliarBoonFor"/> because the boon could not otherwise be
    /// applied: the skill's name existed only inside a sentence, and a sentence is not something
    /// <see cref="SkillBonus"/> can read. Same fault, same shape, as every other pair of facts this
    /// project has had to pull apart — the moment one of them is only printable, the other one
    /// silently stops being true.</para>
    ///
    /// <para>Null for a beast nobody has keyed. The book states the boon as a principle — "a +2 to
    /// one sense or skill befitting its nature" — and leaves the choice to the table, so a sixth
    /// animal gets the generic line and no automatic bonus, rather than a guessed one.</para></summary>
    public static string FamiliarSkillFor(string kind) => (kind ?? "").ToLowerInvariant() switch
    {
        var k when k.Contains("cat")   => "Stealth",
        var k when k.Contains("crow")  => "Notice",
        var k when k.Contains("hare")  => "Acrobatics",
        var k when k.Contains("toad")  => "Medicine",
        var k when k.Contains("snake") => "Insight",
        _ => null,
    };

    /// <summary>Why that skill and not another — the half of the boon line that is prose, kept
    /// beside the half that is a rule so a Keeper reading the sheet gets both.</summary>
    static string FamiliarReasonFor(string kind) => (kind ?? "").ToLowerInvariant() switch
    {
        var k when k.Contains("cat")   => "it goes where you cannot and comes back",
        var k when k.Contains("crow")  => "it sees the country from above and tells you",
        var k when k.Contains("hare")  => "its quickness is in your feet",
        var k when k.Contains("toad")  => "it knows what grows and what it is for",
        var k when k.Contains("snake") => "it reads warmth, and fear is warm",
        _ => null,
    };

    /// <summary>
    /// The standing boon each bound beast grants — "a +2 to one sense or skill befitting its
    /// nature", which the book states as a principle and leaves to the table. The app has to
    /// pick something, so it picks the obvious thing and says so on the sheet; a Keeper who
    /// wants otherwise edits the line. Keyed on the beast alone, so the five options in
    /// chargen.json's Witch choice are the five keys and a sixth would fall through to the
    /// generic reading rather than crashing.
    /// </summary>
    public static string FamiliarBoonFor(string kind)
        => FamiliarSkillFor(kind) is string sk
         ? $"+{FamiliarBoonSize} {sk} — {FamiliarReasonFor(kind)}"
         : $"+{FamiliarBoonSize} to one sense or skill befitting its nature";

    /// <summary>Which level a Calling's 3rd-level path opens at, and which level its greater half
    /// opens at — read off the level table rather than typed here, because the table is where the
    /// book states them and the two differ by Calling: the three of the Old Dark deepen at 9th and
    /// everybody else masters at 10th. Zeroes for a Calling with no path at all.
    ///
    /// <para>Worth the four lines. The alternative is the literal 3 and the literal 9 written into
    /// every rule that turns on the Craft, which is how a level table and the code that reads it
    /// part company — and this project has already paid for that lesson under two other
    /// names.</para></summary>
    public static (int At, int Greater) SubpathLevels(string callingName)
    {
        var cal = D?.callings?.FirstOrDefault(c => c.name == callingName);
        if (cal?.subpath == null) return (0, 0);
        var rows = cal.rows.OrderBy(r => r.level).ToList();
        string greater = rows.SelectMany(r => r.features ?? new())
            .FirstOrDefault(f => f.EndsWith(" Mastery", StringComparison.Ordinal)
                              || f.EndsWith(" (Greater)", StringComparison.Ordinal));
        if (greater == null) return (0, 0);
        string stem = greater.Replace(" Mastery", "").Replace(" (Greater)", "");
        return (rows.FirstOrDefault(r => (r.features ?? new()).Contains(stem))?.level ?? 0,
                rows.FirstOrDefault(r => (r.features ?? new()).Contains(greater))?.level ?? 0);
    }

    /// <summary>Has this soul taken <b>the Familiar-Bound</b> — the Witch's Craft whose whole
    /// subject is the beast? At its own level the familiar "grows clever and hardy", which is the
    /// only thing the book says about how much the beast can take, and so the only thing the app
    /// has to go on when it gives the beast a Blood of its own.</summary>
    public static bool FamiliarBound(CharacterSheet s)
        => s != null && !string.IsNullOrEmpty(s.FamiliarKind)
           && (s.Subpath ?? "").Contains("Familiar-Bound", StringComparison.OrdinalIgnoreCase)
           && s.Level >= SubpathLevels(s.Calling).At;

    /// <summary>...and reached its greater boon — swap places once per scene, share wounds or
    /// Blood, and the once-only spirit-carry to a new dawn.</summary>
    public static bool FamiliarBoundGreater(CharacterSheet s)
        => FamiliarBound(s) && s.Level >= SubpathLevels(s.Calling).Greater;

    /// <summary>What to call the beast on the field. The sheet holds a kind and not a name — "a
    /// crow" — so the field row borrows its Witch's, which is also how a table refers to it out
    /// loud. A Keeper who has named the thing types over it.</summary>
    public static string FamiliarFieldName(string witchName, string kind)
    {
        string k = (kind ?? "familiar").Trim();
        foreach (var art in new[] { "a ", "an ", "the " })
            if (k.StartsWith(art, StringComparison.OrdinalIgnoreCase)) { k = k.Substring(art.Length); break; }
        return string.IsNullOrWhiteSpace(witchName) ? k : $"{witchName}'s {k}";
    }

    /// <summary>
    /// Bind the beast if this Calling has one. Reads the kind back out of CallingChoice rather
    /// than re-rolling it, so the sheet's familiar and its bonus can never name two animals —
    /// which is the whole failure mode of storing the same fact twice.
    /// </summary>
    static void BindFamiliar(CharacterSheet s, CgCalling cal)
    {
        if (cal.choice == null || !cal.choice.label.Equals("Familiar", StringComparison.OrdinalIgnoreCase))
            return;
        int i = (s.CallingChoice ?? "").IndexOf(':');
        s.FamiliarKind = i >= 0 ? s.CallingChoice.Substring(i + 1).Trim() : null;
        s.FamiliarBoon = FamiliarBoonFor(s.FamiliarKind);
        s.FamiliarLost = false;
    }

    /// <summary>
    /// What the sheet says about the beast, or null when there is none. One line, because it is
    /// one line in the book: what it is, what it gives you, and whether it is still alive.
    /// </summary>
    public static string FamiliarLine(CharacterSheet s)
    {
        if (string.IsNullOrEmpty(s?.FamiliarKind)) return null;
        if (s.FamiliarLost)
            return $"Familiar: {s.FamiliarKind} — DEAD. Sickened until you bind another over a long night's rite.";
        string line = $"Familiar: {s.FamiliarKind} — {s.FamiliarBoon}; scouts, spies, shares its senses, "
                    + "and can deliver a touch-range Sign.";
        if (FamiliarBoundGreater(s))
            line += " Familiar-Bound: swap places with it once per scene and share wounds or Blood"
                  + (s.FamiliarCarried ? "; it has already carried your spirit to a new dawn, and that was the once."
                                       : "; should you fall it carries your spirit to a new dawn, once.");
        else if (FamiliarBound(s))
            line += " Familiar-Bound: clever and hardy, it delivers your Signs and you see and hear "
                  + "through it at any distance.";
        return line;
    }
}
