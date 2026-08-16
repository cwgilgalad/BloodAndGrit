using System.Text.RegularExpressions;

namespace BloodAndGritKeeper;

// ============================================================ THE IRON CODE, ADJUDICATED
// The gun rules of Chapter XI applied, not just displayed. Everything here is pure (no
// WinForms), so the smoke rig can prove it against the book. The weapon's free-text `traits`
// string stays the single source of truth (it is what the book prints); WeaponTraits.Parse
// reads structure out of it, and a smoke test asserts every weapon parses cleanly — so the
// engine can never quietly disagree with the printed trait.

/// <summary>The structured form of a weapon's Chapter X traits, parsed from its `traits` text.</summary>
public class WeaponTraits
{
    public int FatalDie { get; set; }        // 0 = none; else 6/8/10/12 — the crit die (Ch. X "Fatal dX")
    public int Misfire { get; set; } = -1;   // -1 = no Misfire trait; else X: jam on crit-fail/nat 1, clear DC 10+X
    public bool Agile { get; set; }          // MAP softens to -4/-8 (Ch. XI)
    public int Scatter { get; set; }         // 0 = none; else feet — 1d6 splash within (Ch. X "Scatter X")
    public int Volley { get; set; }          // 0 = none; else feet — -2 to Strikes within (Ch. X "Volley X")
    public bool Kickback { get; set; }       // -2 and Off-Guard unless braced or STR 12+ (Ch. XI)
    public bool Repeating { get; set; }
    public bool Concealable { get; set; }

    public bool HasMisfire => Misfire >= 0;

    static readonly Regex FatalRe   = new(@"fatal\s*d(\d+)", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    static readonly Regex MisfireRe = new(@"misfire\s*(\d+)", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    static readonly Regex ScatterRe = new(@"scatter\s*(\d+)", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    static readonly Regex VolleyRe  = new(@"volley\s*(\d+)", RegexOptions.IgnoreCase | RegexOptions.Compiled);

    public static WeaponTraits Parse(string traits)
    {
        traits ??= "";
        var t = new WeaponTraits();
        var m = FatalRe.Match(traits);   if (m.Success) t.FatalDie = int.Parse(m.Groups[1].Value);
        m = MisfireRe.Match(traits);     if (m.Success) t.Misfire  = int.Parse(m.Groups[1].Value);
        m = ScatterRe.Match(traits);     if (m.Success) t.Scatter  = int.Parse(m.Groups[1].Value);
        m = VolleyRe.Match(traits);      if (m.Success) t.Volley   = int.Parse(m.Groups[1].Value);
        t.Agile       = traits.Contains("Agile", StringComparison.OrdinalIgnoreCase);
        t.Kickback    = traits.Contains("Kickback", StringComparison.OrdinalIgnoreCase);
        t.Repeating   = traits.Contains("Repeating", StringComparison.OrdinalIgnoreCase);
        t.Concealable = traits.Contains("Concealable", StringComparison.OrdinalIgnoreCase);
        return t;
    }
}

/// <summary>One attack a Bestiary creature makes, read out of its free-text <c>attacks</c> line so a
/// creature can Strike through the very same Iron Code engine as a posse gun — with its OWN to-hit
/// and damage, not the party's. The free-text in creatures.json stays the single source of truth (it
/// is what the Bestiary prints); this parses structure out of it, exactly as <see cref="WeaponTraits"/>
/// does for a gun's traits. A creature's whole line splits on ';' into named Strikes ("pick and claw
/// +4 (1d6+2 and grab)") and riders — the maneuvers and auras with no to-hit that the Keeper narrates.</summary>
public class CreatureAttack
{
    public string Name { get; set; } = "";      // "pick and claw", "draining bite", "a touch that blisters"
    public int Bonus { get; set; }               // the built-in to-hit, e.g. +6
    public string Damage { get; set; } = "1d4";  // the dice, e.g. "1d6+2"; "" for a hit with no dice
    public string Type { get; set; } = "blades"; // a physical natural attack, or an element it names (fire/cold/…)
    public string Effect { get; set; } = "";     // the rider after the dice: "grab", "Fort DC 15 or Sickened 1"

    public bool DealsDamage => !string.IsNullOrWhiteSpace(Damage);

    /// <summary>A creature attack feeds the engine as a plain weapon of its own damage — no gun
    /// traits (no Fatal/Misfire). Its <see cref="Type"/> overrides the gun/blade damage-type guess.
    /// A dice-less attack ("spray +7 (no Blood…)") deals 0 Blood: the hit is real, the harm is the rider.</summary>
    public CgWeapon ToWeapon() => new() { name = Name, dmg = string.IsNullOrEmpty(Damage) ? "0" : Damage, traits = "", kind = "natural" };

    static readonly Regex StrikeRe  = new(@"^(?<name>.+?)\s*\+(?<bonus>\d+)\s*\((?<inner>[^)]*)\)(?<tail>.*)$", RegexOptions.Compiled);
    static readonly Regex LeadDice  = new(@"^\s*(?<dmg>\d*d\d+(?:\s*[+\-]\s*\d+)?)", RegexOptions.Compiled);
    static readonly Regex ElementRe = new(@"\b(fire|cold|acid|lightning|electric(?:ity)?|poison|necrotic|holy|unholy|spirit)\b",
        RegexOptions.IgnoreCase | RegexOptions.Compiled);

    static readonly char[] EffectTrim = { ' ', ',', '-', '—' };   // strip leading punctuation and dashes

    // Split a creature's line on ';' — but only at paren depth zero, so a parenthetical that itself
    // holds a ';' ("bite +5 (1d4 and holds; venom Fort DC 13 …)") is not sheared in two.
    static IEnumerable<string> Clauses(string s)
    {
        int depth = 0, start = 0;
        for (int i = 0; i < s.Length; i++)
        {
            char ch = s[i];
            if (ch == '(') depth++;
            else if (ch == ')') { if (depth > 0) depth--; }
            else if (ch == ';' && depth == 0) { yield return s.Substring(start, i - start); start = i + 1; }
        }
        yield return s.Substring(start);
    }

    /// <summary>Parse a creature's whole <c>attacks</c> line into its Strikes (with numbers, ready for
    /// the engine) and its riders (clauses that carry no to-hit — the special maneuvers and auras).</summary>
    public static (List<CreatureAttack> strikes, List<string> riders) Parse(string attacks)
    {
        var strikes = new List<CreatureAttack>();
        var riders = new List<string>();
        foreach (var raw in Clauses(attacks ?? ""))
        {
            var clause = raw.Trim();
            if (clause.Length == 0) continue;
            var m = StrikeRe.Match(clause);
            if (!m.Success) { riders.Add(clause); continue; }   // a rider: no "+N (…)"

            var a = new CreatureAttack { Name = m.Groups["name"].Value.Trim(), Bonus = int.Parse(m.Groups["bonus"].Value) };
            string inner = m.Groups["inner"].Value.Trim();
            string tail = m.Groups["tail"].Value.Trim();       // text after the ')': "…) and a strength that bends iron"
            var dm = LeadDice.Match(inner);
            string effect;
            if (dm.Success) { a.Damage = dm.Groups["dmg"].Value.Replace(" ", ""); effect = inner.Substring(dm.Length).TrimStart(EffectTrim); }
            else            { a.Damage = ""; effect = inner; }  // "+9 (all in its path)" — a hit, no dice of its own
            if (tail.Length > 0) effect = (effect.Length > 0 ? effect + " " : "") + tail.TrimStart(EffectTrim);
            if (effect.StartsWith("and ", StringComparison.OrdinalIgnoreCase)) effect = effect.Substring(4);
            a.Effect = effect.Trim();
            var el = ElementRe.Match(inner + " " + tail);
            if (el.Success) a.Type = el.Value.ToLowerInvariant();
            strikes.Add(a);
        }
        return (strikes, riders);
    }
}

/// <summary>Decides what a tracker row fights with — the one authority both the Strike dialog
/// and its tests go through, so the two can never drift. A foe that resolves to a Bestiary
/// entry uses THAT creature's own attacks; the posse and any hand-entered row reach for the
/// shared weapon table. <c>IsPC</c> is authoritative: a player's soul is never treated as a
/// creature, even if a stray Ref rode in on an old session, and a foe whose Ref no longer
/// resolves falls back to weapons rather than throwing.</summary>
public static class CombatMenu
{
    /// <summary>Does this combatant fight with a Bestiary creature's own attacks?</summary>
    public static bool IsCreature(Combatant c) =>
        c != null && !c.IsPC && !string.IsNullOrEmpty(c.Ref) && Db.Find(c.Ref) != null;

    /// <summary>The creature's own attacks (with a tier-benchmark blow for a bodiless foe that
    /// has no dice of its own), its riders, and the resolved Creature — or all null when this
    /// row fights with the posse's weapons instead.</summary>
    public static (List<CreatureAttack> attacks, List<string> riders, Creature creature) For(Combatant c)
    {
        var creature = IsCreature(c) ? Db.Find(c.Ref) : null;
        if (creature == null) return (null, null, null);
        var (atks, riders) = CreatureAttack.Parse(creature.attacks);
        if (atks.Count == 0)   // an intangible or pure-rider foe: give it its tier's benchmark blow
        {
            var row = Rules.TierRow[Math.Clamp(creature.tier - 1, 0, Rules.TierRow.Length - 1)];
            atks.Add(new CreatureAttack { Name = "its assault", Bonus = row.atk, Damage = row.dmg });
        }
        return (atks, riders, creature);
    }
}

/// <summary>One line of Damage Reduction on a defender (Ch. XI): an amount and what it turns.
/// <c>Vs</c> is "blades" | "small shot" | "ball" | "nonmagical" | "all".</summary>
public record DrEntry(int Amount, string Vs);

public static class IronCode
{
    // ---- the Multiple Attack Penalty (Ch. XI) ----
    /// <summary>The MAP for the Nth Strike this turn: 1st clean, 2nd -5, 3rd+ -10; Agile softens to -4/-8.</summary>
    public static int MapPenalty(int strikeNumber, bool agile)
        => strikeNumber <= 1 ? 0
         : strikeNumber == 2 ? (agile ? -4 : -5)
         : (agile ? -8 : -10);

    // ---- Aim, brace, and the Kickback weapon (Ch. XI, "Aiming and Bracing") ----

    /// <summary>What a Beat spent to Aim buys on the next Strike before the turn ends. The
    /// Circumstance table prints the same +2 for "you Aimed and did not move", which is the same
    /// rule seen from the other side rather than a second one that stacks with it.</summary>
    public const int AimBonus = 2;

    /// <summary>What a Kickback weapon costs the hasty, on top of leaving them Off-Guard.</summary>
    public const int KickbackPenalty = -2;

    /// <summary>The STR at which a soul holds a Kickback weapon steady without spending the Beat.
    /// The book gives the strong an outright exemption, not a smaller penalty.</summary>
    public const int BraceStrength = 12;

    /// <summary>Whether the recoil bites: a Kickback weapon, fired without the Beat spent to brace,
    /// by somebody under <see cref="BraceStrength"/> STR.</summary>
    public static bool KickbackBites(WeaponTraits tr, bool braced, int strScore)
        => (tr?.Kickback ?? false) && !braced && strScore < BraceStrength;

    // ---- Circumstance (Ch. XI, "Circumstance") ----

    /// <summary>What stands between the shot and the target.</summary>
    public enum Cover { None, Light, Heavy }

    /// <summary>Adjacent, in feet — one square, and the range at which a long gun becomes a
    /// nuisance rather than a reach.</summary>
    public const int PointBlankFeet = 5;

    /// <summary>The facts of a shot that the engine cannot see from a tracker row: how far, what is
    /// in the way, whether it is fired into a scrum, and whether the target can be seen at all. The
    /// app models no ground, so the Keeper is the only one who knows these — but once they are
    /// known the whole Circumstance table is arithmetic, and the arithmetic is the engine's.</summary>
    public record Shot
    {
        /// <summary>Feet to the target. <b>Zero means the Keeper did not say</b>, and every
        /// distance rule is then left alone rather than guessed at.</summary>
        public int Distance { get; init; }
        public Cover Cover { get; init; }
        public bool IntoMelee { get; init; }
        /// <summary>Target fully concealed: cannot be targeted directly, and firing blind into
        /// the guessed square is its own penalty.</summary>
        public bool Concealed { get; init; }

        /// <summary>Declared before the roll (Ch. XI, "Two Kinds of Fighting"): this blow is meant
        /// to subdue. Most arms take −2 to pull it; fists and a club do it by nature.</summary>
        public bool Nonlethal { get; init; }

        /// <summary>How the striker's horse is moving. Filled in by the engine from the row rather
        /// than asked of the Keeper — unlike the distance and the cover, this is something the app
        /// already knows.</summary>
        public Gait Gait { get; init; }

        /// <summary>Whether the target is themselves mounted, which decides the +1 a rider gets
        /// striking down at a footman. Also filled from the rows.</summary>
        public bool TargetMounted { get; init; }

        /// <summary>Whether the target is sprawling. Appendix B gives Prone two halves and the
        /// Burden can only carry one of them: the −4 it costs the prone soul's OWN melee Strikes
        /// rides on their row, while the +4 it hands everyone SHOOTING at them can only be reckoned
        /// here, where both parties are in view. Filled from the target's row.</summary>
        public bool TargetProne { get; init; }

        public static readonly Shot Plain = new();
    }

    /// <summary>What the moment costs a Strike, and the reason for each part of it. A Keeper who is
    /// shown only a total has to remember why it moved, and mid-fight nobody remembers anything.
    ///
    /// <para><b>Two rows of the book's table are deliberately NOT here.</b> <em>Target Off-Guard</em>
    /// is already paid by <see cref="Rules.ConditionBurden"/> as −2 to their Defense, and
    /// <em>You Aimed and did not move</em> is already paid by <see cref="Combatant.Aimed"/> in
    /// <c>CombatFlow.StrikeAndApply</c>. Adding either here would charge it twice, which is
    /// exactly the fault the derived-Burden design exists to prevent.</para></summary>
    public record Reckoning(int Total, List<string> Parts, bool CannotTarget);

    /// <summary>Whether this is a long gun — rifle, carbine, shotgun or repeater — which the Code
    /// handles differently at point-blank and from the saddle. Read off the NAME on purpose: Ch. X's
    /// glossary defines a <em>Two-Handed</em> trait and then prints it on no weapon in either table,
    /// so there is no trait to read. Ch. XI names them the same way — "a two-handed long gun
    /// (rifle, carbine, shotgun)" — so this follows the book rather than inventing data for it.</summary>
    public static bool IsLongGun(CgWeapon w)
    {
        if (!string.Equals(w?.kind, "gun", StringComparison.OrdinalIgnoreCase)) return false;
        string n = w.name ?? "";
        return n.Contains("Rifle", StringComparison.OrdinalIgnoreCase)
            || n.Contains("Shotgun", StringComparison.OrdinalIgnoreCase)
            || n.Contains("Carbine", StringComparison.OrdinalIgnoreCase)
            || n.Contains("Repeater", StringComparison.OrdinalIgnoreCase)
            || n.Contains("Musket", StringComparison.OrdinalIgnoreCase);
    }

    // ---- Fighting from the Saddle (Ch. XI) ----

    /// <summary>How the horse under you is moving, which is what the saddle rules turn on.
    /// <see cref="Afoot"/> is not mounted at all.</summary>
    public enum Gait { Afoot, Standing, Walking, Trotting, Galloping }

    /// <summary>A moving platform — trotting or galloping. Standing and walking shoot as normal,
    /// which the book says in as many words.</summary>
    public static bool IsMoving(Gait g) => g == Gait.Trotting || g == Gait.Galloping;

    /// <summary>Feet of straight line a mount must cover to make a Charge.</summary>
    public const int ChargeFeet = 20;

    /// <summary>Feet of straight line at which a gallop will ride a foe down or break a line.</summary>
    public const int RideDownFeet = 30;

    /// <summary>The DC to keep the saddle, or to master a green or frightened animal.</summary>
    public const int RideDc = 15;

    /// <summary>The charge weapons — lance, spear, saber. A knife or a hatchet earns no charge
    /// bonus, which the book's by-weapon box says outright.</summary>
    public static bool IsChargeWeapon(CgWeapon w)
    {
        string n = w?.name ?? "";
        return n.Contains("Saber", StringComparison.OrdinalIgnoreCase)
            || n.Contains("Lance", StringComparison.OrdinalIgnoreCase)
            || n.Contains("Spear", StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>A two-handed melee weapon, which is awkward swung from the saddle. Read off the
    /// name, and note that <b>no melee weapon in the arms table is one today</b> — the book prints
    /// a Two-Handed trait in Ch. X's glossary and applies it to nothing in either table. The rule
    /// is implemented rather than left out so that a pike or a polearm added later is handled;
    /// today it is correctly a no-op for every weapon a soul can actually buy.</summary>
    public static bool IsTwoHandedMelee(CgWeapon w)
    {
        if (string.Equals(w?.kind, "gun", StringComparison.OrdinalIgnoreCase)) return false;
        string n = w?.name ?? "";
        return n.Contains("Lance", StringComparison.OrdinalIgnoreCase)
            || n.Contains("Pike", StringComparison.OrdinalIgnoreCase)
            || n.Contains("Polearm", StringComparison.OrdinalIgnoreCase)
            || n.Contains("Spear", StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>Whether a shot may be aimed or braced at all. You cannot from a moving horse, which
    /// also means a Kickback weapon can never be braced at a gallop — the shotgun's recoil and the
    /// horse's motion arrive together, exactly as the chapter implies.</summary>
    public static bool CanAim(Gait g) => !IsMoving(g);

    /// <summary>The Charge (Ch. XI): twenty feet of straight line into a foe with a lance, spear or
    /// saber is worth an extra die of damage, and a couched lance doubles the dice instead. You are
    /// committed and off-balance after, at −2 Defense until your next turn.</summary>
    public record ChargeResult(bool Made, int ExtraDice, bool DoubleDice, int DefenseAfter, string Line);

    public static ChargeResult Charge(CgWeapon w, int feetStraight, bool couchedLance = false)
    {
        if (feetStraight < ChargeFeet)
            return new(false, 0, false, 0, $"a charge wants {ChargeFeet} feet of straight line, and this had {feetStraight}");
        if (!IsChargeWeapon(w))
            return new(false, 0, false, 0, $"{w?.name ?? "this"} earns no charge bonus — the lance, the spear and the saber do");
        return couchedLance && (w.name ?? "").Contains("Lance", StringComparison.OrdinalIgnoreCase)
            ? new(true, 0, true, -2, "a couched lance — double dice, and −2 Defense until your next turn")
            : new(true, 1, false, -2, "+1 die on the charge, and −2 Defense until your next turn");
    }

    /// <summary>Keeping the saddle: a Ride save against DC 15, or the attacker's own result. Failing
    /// it puts you on the ground, prone, a few feet from the animal, with 1d6 to show for it.</summary>
    public static (bool Kept, int Damage, string Line) KeepTheSaddle(int rideTotal, int dc = RideDc)
        => rideTotal >= dc
            ? (true, 0, "kept the saddle")
            : (false, Rules.Rng.Next(1, 7), "unhorsed — prone, and a few feet from the animal");

    // ---- Two Kinds of Fighting (Ch. XI) ----

    /// <summary>What it costs to pull a blow with an arm not made for it.</summary>
    public const int PulledBlowPenalty = -2;

    /// <summary>Whether this arm subdues by nature — fists and a club — so striking nonlethally
    /// with it costs nothing. Read off the printed Notes column, which is where the book says it:
    /// "nonlethal by choice", "Nonlethal unless you mean it".</summary>
    public static bool NonlethalByNature(CgWeapon w)
        => (w?.traits ?? "").Contains("nonlethal", StringComparison.OrdinalIgnoreCase);

    /// <summary>How many full range increments past the first this shot is thrown across. Zero
    /// inside the first increment, and zero as well when either number is unknown.</summary>
    public static int IncrementsPast(int distance, int rangeIncrement)
        => distance <= 0 || rangeIncrement <= 0 ? 0
         : Math.Max(0, (distance + rangeIncrement - 1) / rangeIncrement - 1);

    public static Reckoning Reckon(Shot s, CgWeapon w, bool braced = false)
    {
        s ??= Shot.Plain;
        var tr = WeaponTraits.Parse(w?.traits);
        int total = 0; var parts = new List<string>();
        void Take(int n, string why) { if (n != 0) { total += n; parts.Add($"{(n > 0 ? "+" : "")}{n} {why}"); } }

        bool pointBlank = s.Distance > 0 && s.Distance <= PointBlankFeet;

        // Range. Point-blank waives the increment penalty outright — you are not missing a man at
        // arm's length because the barrel is rated for two hundred yards.
        if (!pointBlank)
        {
            int past = IncrementsPast(s.Distance, w?.range ?? 0);
            Take(-2 * past, past == 1 ? "beyond the first range increment"
                                      : $"{past} increments beyond the first");
        }
        else if (IsLongGun(w) && !braced)
            Take(-2, "a long gun at arm's length, unbraced");

        // Volley: this long iron is made for distance, and resents being used up close.
        if (tr.Volley > 0 && s.Distance > 0 && s.Distance <= tr.Volley)
            Take(-2, $"inside the Volley {tr.Volley} ft this iron wants");

        Take(s.Cover switch { Cover.Light => -2, Cover.Heavy => -4, _ => 0 },
             s.Cover == Cover.Heavy ? "heavy cover" : "light cover");
        Take(s.IntoMelee ? -4 : 0, "fired into melee");
        Take(s.Concealed ? -8 : 0, "fired blind at a guessed square");
        Take(s.Nonlethal && !NonlethalByNature(w) ? PulledBlowPenalty : 0, "pulling the blow");

        // The other half of Prone (Appendix B): a sprawling target is easier to SHOOT and harder to
        // reach with a blade. The −4 on their own Strikes is already the Burden's; this is the +4
        // the book hands the shooter, and it has no other place it could live.
        bool ranged = string.Equals(w?.kind, "gun", StringComparison.OrdinalIgnoreCase)
                   || (w?.traits ?? "").Contains("Thrown", StringComparison.OrdinalIgnoreCase)
                   || (w?.traits ?? "").Contains("Throwable", StringComparison.OrdinalIgnoreCase);
        Take(s.TargetProne && ranged ? 4 : 0, "shooting at a sprawling target");

        // ---- from the saddle (Ch. XI) ----
        bool gun = string.Equals(w?.kind, "gun", StringComparison.OrdinalIgnoreCase);
        bool thrown = (w?.traits ?? "").Contains("Thrown", StringComparison.OrdinalIgnoreCase)
                   || (w?.traits ?? "").Contains("Throwable", StringComparison.OrdinalIgnoreCase);
        if (s.Gait != Gait.Afoot)
        {
            if (IsMoving(s.Gait))
            {
                // The moving platform. Ranged and thrown alike; a pistol at a walk is free, which is
                // the whole reason the horseman carries one.
                Take(gun || thrown ? -2 : 0, "shooting from a moving horse");
                // And a long gun is doubly awkward up there — the box's −4 in all.
                Take(gun && IsLongGun(w) ? -2 : 0, "a two-handed long gun from the saddle");
            }
            // Striking down at a footman. The saber is the horseman's blade and waives the mounted
            // penalty; everything else two-handed is awkward from up there.
            if (!gun && !thrown)
            {
                Take(!s.TargetMounted ? 1 : 0, "striking down at a man on foot");
                bool saber = (w?.name ?? "").Contains("Saber", StringComparison.OrdinalIgnoreCase);
                Take(IsTwoHandedMelee(w) && !saber ? -2 : 0, "a two-handed weapon swung from the saddle");
            }
        }

        return new Reckoning(total, parts, s.Concealed);
    }

    // ---- Scatter (Ch. X, "Scatter X") ----

    /// <summary>Where a Scatter weapon's splash falls. On a hit, everything within the radius takes
    /// 1d6. On a MISS inside the first range increment the target still wears it, which is the whole
    /// argument for a shotgun. Who is standing within the radius is the Keeper's to say — the app
    /// models no ground — so this answers whether the splash falls, not on whom.</summary>
    public static (bool Falls, int Radius, bool TargetToo) ScatterFalls(
        WeaponTraits tr, CgWeapon w, bool hit, int distance)
    {
        int radius = tr?.Scatter ?? 0;
        if (radius <= 0) return (false, 0, false);
        if (hit) return (true, radius, false);
        bool insideFirst = w != null && w.range > 0 && distance > 0 && distance <= w.range;
        return (insideFirst, radius, insideFirst);
    }

    /// <summary>One creature's share of the splash.</summary>
    public static int ScatterDamage() => Rules.Rng.Next(1, 7);

    // ---- Reloading (Ch. XI, "Reloading" · Ch. X, the arms table's Reload column) ----

    /// <summary>How a weapon is fed, off the arms table's printed Reload column.</summary>
    public enum ReloadKind { None, Single, PerShot, Slow }

    /// <summary>A cap-and-ball cylinder is three rounds of dedicated work, and cannot be part-filled
    /// in a hurry. Rounds, not Beats — it is the one reload the book prices in whole rounds.</summary>
    public const int SlowReloadRounds = 3;

    /// <summary>Read the arms table's Reload column. Anything unrecognised is
    /// <see cref="ReloadKind.None"/> rather than a guess: a blade has no such column.</summary>
    public static ReloadKind ReadReload(string reload) => (reload ?? "").Trim().ToLowerInvariant() switch
    {
        "1/shot" => ReloadKind.PerShot,
        "slow"   => ReloadKind.Slow,
        "1"      => ReloadKind.Single,
        _        => ReloadKind.None,
    };

    /// <summary>What making a weapon ready again costs, in the units the book prices it in.</summary>
    public record ReloadCost(ReloadKind Kind, int Beats, int Rounds, string Line);

    /// <summary>What making this weapon ready costs. <paramref name="full"/> asks for a top-off
    /// rather than a single round; <paramref name="practiced"/> is the <em>Practiced Reload</em>
    /// Edge, which shaves one Beat off a weapon you favor and can never take it below one.</summary>
    public static ReloadCost Reloading(CgWeapon w, bool full = true, bool practiced = false)
    {
        var kind = ReadReload(w?.reload);
        int cap  = Math.Max(0, w?.cap ?? 0);
        switch (kind)
        {
            case ReloadKind.Slow:
                // No partial loading in a hurry — the book is explicit, so there is no single-round
                // branch here to offer.
                return new(kind, 0, SlowReloadRounds,
                    $"{SlowReloadRounds} rounds of dedicated work — a cylinder is charged, not thumbed");

            case ReloadKind.Single:
                // A break-action is one Interact whether it holds one barrel or two.
                return new(kind, 1, 0, "one Interact, and it is whole again");

            case ReloadKind.PerShot when !full:
                return new(kind, 1, 0, "one Beat thumbs a single round in");

            case ReloadKind.PerShot:
            {
                // Beats equal to half its capacity, rounded up — a six-gun three, a twelve-shot six.
                int beats = Math.Max(1, (cap + 1) / 2 - (practiced ? 1 : 0));
                return new(kind, beats, 0,
                    $"{beats} Beat{(beats == 1 ? "" : "s")} to top off {cap}"
                    + (practiced ? ", one shaved by Practiced Reload" : ""));
            }

            default:
                return new(ReloadKind.None, 0, 0, "nothing to reload");
        }
    }

    // ---- the Strike (Ch. XI, "The Four Degrees of Success") ----
    public record StrikeOutcome(int Die, int Total, int Defense, int Degree, string DegreeName,
        bool Hit, bool Crit, bool Jam, string Detail);

    /// <summary>Resolve one Strike. <paramref name="attackMod"/> is the whole bonus already summed —
    /// attack rank + ability + circumstance − MAP − Volley, etc. A Misfire weapon jams on a critical
    /// failure (which includes any natural 1, per the four-degree rule).</summary>
    public static StrikeOutcome ResolveStrike(int attackMod, int defense, WeaponTraits tr, int? forcedDie = null)
    {
        int die = forcedDie ?? Rules.Rng.Next(1, 21);
        var (idx, _, detail) = Rules.FourDegrees(die, attackMod, defense);
        // Ch. XI states a combat-specific floor beyond the Ch. II one-step shift: "a natural 20
        // always at least hits; a natural 1 always at least misses." It only bites at wide margins
        // (a nat 20 that still missed by 10+, a nat 1 that still beat by 10+), and only for Strikes —
        // skill checks keep the pure one-step shift in Rules.FourDegrees. (Flagged for the Ch. II/XI
        // consistency pass: this is where the two chapters are reconciled.)
        if (die == 20) idx = Math.Max(idx, 2);
        if (die == 1)  idx = Math.Min(idx, 1);
        string name = idx switch { 3 => "CRITICAL SUCCESS", 2 => "Success", 1 => "Failure", _ => "CRITICAL FAILURE" };
        bool hit  = idx >= 2;
        bool crit = idx == 3;
        bool jam  = (tr?.HasMisfire ?? false) && idx == 0;
        return new StrikeOutcome(die, die + attackMod, defense, idx, name, hit, crit, jam, detail);
    }

    // ---- damage, with the Fatal rule (Ch. X / XI) ----
    public record DamageRoll(int Total, string Breakdown);

    static readonly Regex OneDice = new(@"^\s*(\d*)d(\d+)\s*$", RegexOptions.Compiled);

    /// <summary>Roll a weapon's damage. On a critical hit the damage doubles, and a Fatal weapon
    /// rolls its dice at the Fatal size and adds one more Fatal die <em>after</em> doubling — so a
    /// 1d8 Fatal d10 crit is 2×(1d10)+1d10, faithful to the PF2E rule the Code is built on.</summary>
    public static DamageRoll RollDamage(string dmgExpr, WeaponTraits tr, bool crit)
    {
        if (!crit)
        {
            var (t, b, _) = Rules.RollExprFull(dmgExpr);
            return new DamageRoll(t, b);
        }

        int fatal = tr?.FatalDie ?? 0;
        var m = OneDice.Match(dmgExpr ?? "");
        if (fatal > 0 && m.Success)
        {
            int n = m.Groups[1].Value.Length == 0 ? 1 : int.Parse(m.Groups[1].Value);
            // 2N dice of the Fatal size (the doubled weapon dice), plus one extra Fatal die
            int doubled = Enumerable.Range(0, 2 * n).Sum(_ => Rules.Rng.Next(1, fatal + 1));
            int extra   = Rules.Rng.Next(1, fatal + 1);
            return new DamageRoll(doubled + extra, $"crit: 2×{n}d{fatal} + 1d{fatal} (Fatal)");
        }

        // no Fatal (a plain blade) or a compound expression: just double the normal damage
        var (t2, b2, _) = Rules.RollExprFull(dmgExpr);
        return new DamageRoll(t2 * 2, $"crit: ({b2})×2");
    }

    // ---- Damage Reduction (Ch. XI) ----
    /// <summary>Apply the best matching DR to a hit. DR does not stack (Ch. X — "count the better of
    /// two"), only the highest applicable line applies, and it never lowers a hit below zero.</summary>
    public static int ApplyDR(int damage, string damageType, IEnumerable<DrEntry> dr)
    {
        int best = (dr ?? Enumerable.Empty<DrEntry>())
            .Where(d => d.Vs == "all" || string.Equals(d.Vs, damageType, StringComparison.OrdinalIgnoreCase))
            .Select(d => d.Amount).DefaultIfEmpty(0).Max();
        return Math.Max(0, damage - best);
    }

    /// <summary>How a weapon's damage reads for DR: a melee weapon cuts as "blades"; a gun fires
    /// "ball" (which worn armor mostly ignores) unless it Scatters, which is "small shot".</summary>
    public static string DamageType(CgWeapon w)
    {
        var tr = WeaponTraits.Parse(w?.traits);
        if (string.Equals(w?.kind, "gun", StringComparison.OrdinalIgnoreCase))
            return tr.Scatter > 0 ? "small shot" : "ball";
        return "blades";
    }

    // ---- one full Strike, composed: roll to hit, then damage after DR ----
    public record Resolution(StrikeOutcome Strike, DamageRoll Damage, int AfterDR, string DamageType);

    /// <summary>Resolve a Strike and its damage in one call, applying the defender's DR. Damage is
    /// null and AfterDR 0 on a miss. This is the whole of an attack the table can read off one line.</summary>
    public static Resolution Strike(int attackMod, int defense, CgWeapon weapon,
        IEnumerable<DrEntry> targetDr = null, int? forcedDie = null, string forceType = null)
    {
        var tr = WeaponTraits.Parse(weapon?.traits);
        var so = ResolveStrike(attackMod, defense, tr, forcedDie);
        if (!so.Hit) return new Resolution(so, null, 0, null);
        var dmg = RollDamage(weapon?.dmg ?? "1d4", tr, so.Crit);
        // A creature attack names its own damage type (a fiery touch, a freezing grip); a gun's is
        // read off its kind and Scatter. The forced type, when given, wins — so worn-armor DR ("blades")
        // keeps out a claw but not a flame.
        string dtype = string.IsNullOrEmpty(forceType) ? DamageType(weapon) : forceType;
        int after = ApplyDR(dmg.Total, dtype, targetDr);
        return new Resolution(so, dmg, after, dtype);
    }
}

// ============================================================ AT THE TABLE
// The bridge from the engine to the tracker: reads a PC's own to-hit off their sheet, and takes
// a Strike from one combatant at another — spending the Beat, taking the MAP at the attacker's
// current step, applying the damage, and advancing the step. Pure and smoke-tested; the UI just
// gathers the attacker, the target, and the weapon and calls it.
public static class CombatFlow
{
    /// <summary>A PC's attack bonus for a Strike with a given weapon: the sheet's Attack plus the
    /// keyed ability — DEX for guns and thrown, STR for blades and fists (Ch. XI).</summary>
    public static int AttackBonusFor(CharacterSheet s, CgWeapon w)
    {
        if (s == null) return 0;
        string ability = string.Equals(w?.kind, "gun", StringComparison.OrdinalIgnoreCase) ? "DEX" : "STR";
        int mod = s.Scores != null && s.Scores.TryGetValue(ability, out var sc) ? CharGen.Mod(sc) : 0;
        return s.Attack + mod;
    }

    /// <summary><paramref name="Inflicts"/> is the conditions this blow's own printed rider names —
    /// a ghoul's "grab", a horror's "and they are Frightened 2". Read off the Bestiary's free text by
    /// <see cref="Rules.InflictedConditions"/> and handed back rather than applied, because the
    /// riders are English and half of them hang on a save the Keeper has to call. The UI offers
    /// them; the engine never lays one on by itself.</summary>
    public record StrikeReport(IronCode.Resolution Res, int Map, string Line, List<string> Inflicts,
        IronCode.Reckoning Circ = null);

    /// <summary>Take one Strike from <paramref name="attacker"/> at <paramref name="target"/> and
    /// apply it: spend a Beat, resolve at the attacker's current MAP step, subtract the damage
    /// (after DR) from the target's Blood, and advance the step. Returns a one-line log summary.</summary>
    /// <summary>Take a Strike with a creature's own natural attack — its built-in to-hit, its damage,
    /// and its damage type — through the identical path a posse gun takes. The Bestiary's numbers
    /// finally reach the table: a ghoul claws with +6 (1d8+3), not with the party's revolver.</summary>
    public static StrikeReport StrikeAndApply(Combatant attacker, Combatant target, CreatureAttack attack,
        int attackBonus, IEnumerable<DrEntry> targetDr = null, int? forcedDie = null,
        IronCode.Shot shot = null)
        => StrikeAndApply(attacker, target, attack.ToWeapon(), attackBonus, targetDr, forcedDie, attack.Type,
                          attack.Effect, shot);

    public static StrikeReport StrikeAndApply(Combatant attacker, Combatant target, CgWeapon weapon,
        int attackBonus, IEnumerable<DrEntry> targetDr = null, int? forcedDie = null, string forceType = null,
        string rider = null, IronCode.Shot shot = null)
    {
        var tr = WeaponTraits.Parse(weapon?.traits);
        int map = IronCode.MapPenalty(attacker?.MapStep ?? 1, tr.Agile);
        // What is riding on the two of them (Appendix B). The attacker's conditions move the Strike;
        // the target's move the Defense it is rolled against. Both are DERIVED — nothing here reads
        // a number somebody stored earlier, so an effect cannot be applied twice.
        //
        // The playtest harness and the modules' What the Night Costs numbers are safe from this:
        // neither ever sets a condition, so both Burdens come out empty and the arithmetic is what
        // it always was. It only bites once somebody is actually Frightened, which is the point.
        var mine   = attacker?.Load ?? Rules.Burden.None;
        int defense = target.EffectiveDefense;

        // What the rows already know, filled in rather than asked of the Keeper: the gait of the
        // horse under the striker, and whether the target is mounted too. Distance and cover stay
        // the Keeper's to say, because the app models no ground — these two it can see.
        var facts = (shot ?? IronCode.Shot.Plain) with
        {
            Gait = attacker?.Gait ?? IronCode.Gait.Afoot,
            TargetMounted = target.Mounted,
            TargetProne = target.Load.Prone,
        };

        // Aim and brace are ONE action in the book, so one flag answers for both: the Beat spent
        // buys +2 on this Strike and it is also what "braced" means to a Kickback weapon. The
        // strong are exempt from the recoil outright rather than taking a lesser penalty.
        //
        // From a moving horse you can do neither, which the chapter says outright — so a shotgun
        // fired at a gallop recoils however strong the arm holding it was going to be about it.
        bool braced = (attacker?.Aimed ?? false) && IronCode.CanAim(facts.Gait);
        int aim     = braced ? IronCode.AimBonus : 0;
        bool kicks  = IronCode.KickbackBites(tr, braced, attacker?.Strength ?? Rules.AverageScore);
        int kick    = kicks ? IronCode.KickbackPenalty : 0;

        // What the moment costs (Ch. XI, "Circumstance"). A caller that says nothing about the
        // ground — the playtest harness, the smoke fights — gets Shot.Plain and no range rule runs,
        // so the numbers those were measured against do not move.
        var circ = IronCode.Reckon(facts, weapon, braced);

        var res = IronCode.Strike(attackBonus + map + mine.Strike + aim + kick + circ.Total, defense,
                                  weapon, targetDr, forcedDie, forceType);
        // Sickened takes its −2 off the damage as well as the Strike, and the adjustment is folded
        // back into the Resolution rather than applied at the wound: every caller downstream reads
        // AfterDR — the log line, the grievous-blow check, the tracker's Last column — and a number
        // that was quietly different from the one they were handed is a bug waiting on a bad night.
        if (res.Strike.Hit && mine.Damage != 0 && res.Damage != null)
            res = res with { AfterDR = Math.Max(0, res.AfterDR + mine.Damage) };

        if (attacker != null)
        {
            if (attacker.Beats > 0) attacker.Beats -= 1;   // a Strike is one Beat (Ch. XI)
            attacker.MapStep += 1;                          // the next Strike this turn is at higher MAP
            // The Aim is spent by the Strike that used it, hit or miss — the book buys ONE Strike
            // with that Beat, not every Strike left in the turn.
            attacker.Aimed = false;
            // And the shotgun fired from the hip leaves them open until their own turn comes round.
            if (kicks) attacker.Recoiling = true;
        }

        string who = $"{attacker?.Name ?? "—"} → {target.Name}";
        string mapNote = map != 0 ? $" (MAP {map})" : "";
        // Say so when a condition moved the numbers. A roll that silently came out different from
        // the one the Keeper expected is the fastest way to lose their trust in the engine.
        if (mine.Strike != 0)    mapNote += $" ({(mine.Strike > 0 ? "+" : "")}{mine.Strike} on them)";
        if (aim != 0)            mapNote += $" (+{aim} aimed)";
        if (kick != 0)           mapNote += $" ({kick} unbraced, and Off-Guard until their turn)";
        foreach (var part in circ.Parts) mapNote += $" ({part})";
        // Read off the two numbers rather than off the conditions alone: a target standing
        // Off-Guard from their own unbraced shotgun has moved their Defense without a word of it
        // being in Load.
        if (defense != target.Defense) mapNote += $" (vs Defense {defense}, was {target.Defense})";
        string line;
        // What this blow's own rider would lay on them, if it landed. A creature's attacks line is
        // the source: "pick and claw +4 (1d6+2 and grab)" means Grabbed, and until now that was a
        // word in a dialog the Keeper had to notice, remember, and type into the conditions column
        // themselves — which is to say a rule the app read out and did not run. Only on a hit: a
        // miss grabs nobody.
        var inflicts = res.Strike.Hit ? Rules.InflictedConditions(rider) : new List<string>();
        if (res.Strike.Hit)
        {
            // Through Wound rather than straight at BloodCur, so the tracker's "Last" column shows
            // an engine-resolved hit exactly the way it shows a hand-typed one. One route in.
            target.Wound(-res.AfterDR, nonlethal: shot?.Nonlethal ?? false);
            string drNote = res.Damage != null && res.AfterDR != res.Damage.Total
                ? $" ({res.Damage.Total} − DR)" : "";
            line = $"{who}{mapNote}: {res.Strike.DegreeName}{(res.Strike.Crit ? " —" : "")} "
                 + $"{res.AfterDR} Blood{drNote}. {target.Name} at {target.BloodCur}."
                 + (target.Senseless ? " SENSELESS — laid out, not killed."
                  : target.Down ? " DOWN." : "");
        }
        else
        {
            target.LastDelta = 0;
            target.LastNote = res.Strike.Jam ? "jam" : "missed";
            line = $"{who}{mapNote}: {res.Strike.DegreeName} — "
                 + (res.Strike.Jam ? "the iron JAMS (clear it: Interact + Repair)." : "a miss.");
        }
        return new StrikeReport(res, map, line, inflicts, circ);
    }
}
