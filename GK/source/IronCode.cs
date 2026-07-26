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

    public record StrikeReport(IronCode.Resolution Res, int Map, string Line);

    /// <summary>Take one Strike from <paramref name="attacker"/> at <paramref name="target"/> and
    /// apply it: spend a Beat, resolve at the attacker's current MAP step, subtract the damage
    /// (after DR) from the target's Blood, and advance the step. Returns a one-line log summary.</summary>
    /// <summary>Take a Strike with a creature's own natural attack — its built-in to-hit, its damage,
    /// and its damage type — through the identical path a posse gun takes. The Bestiary's numbers
    /// finally reach the table: a ghoul claws with +6 (1d8+3), not with the party's revolver.</summary>
    public static StrikeReport StrikeAndApply(Combatant attacker, Combatant target, CreatureAttack attack,
        int attackBonus, IEnumerable<DrEntry> targetDr = null, int? forcedDie = null)
        => StrikeAndApply(attacker, target, attack.ToWeapon(), attackBonus, targetDr, forcedDie, attack.Type);

    public static StrikeReport StrikeAndApply(Combatant attacker, Combatant target, CgWeapon weapon,
        int attackBonus, IEnumerable<DrEntry> targetDr = null, int? forcedDie = null, string forceType = null)
    {
        var tr = WeaponTraits.Parse(weapon?.traits);
        int map = IronCode.MapPenalty(attacker?.MapStep ?? 1, tr.Agile);
        var res = IronCode.Strike(attackBonus + map, target.Defense, weapon, targetDr, forcedDie, forceType);

        if (attacker != null)
        {
            if (attacker.Beats > 0) attacker.Beats -= 1;   // a Strike is one Beat (Ch. XI)
            attacker.MapStep += 1;                          // the next Strike this turn is at higher MAP
        }

        string who = $"{attacker?.Name ?? "—"} → {target.Name}";
        string mapNote = map != 0 ? $" (MAP {map})" : "";
        string line;
        if (res.Strike.Hit)
        {
            target.BloodCur = Math.Max(0, target.BloodCur - res.AfterDR);
            string drNote = res.Damage != null && res.AfterDR != res.Damage.Total
                ? $" ({res.Damage.Total} − DR)" : "";
            line = $"{who}{mapNote}: {res.Strike.DegreeName}{(res.Strike.Crit ? " —" : "")} "
                 + $"{res.AfterDR} Blood{drNote}. {target.Name} at {target.BloodCur}."
                 + (target.Down ? " DOWN." : "");
        }
        else
        {
            line = $"{who}{mapNote}: {res.Strike.DegreeName} — "
                 + (res.Strike.Jam ? "the iron JAMS (clear it: Interact + Repair)." : "a miss.");
        }
        return new StrikeReport(res, map, line);
    }
}
