namespace BloodAndGritKeeper;

// ============================================================ THE HORROR, ON RAILS
// Chapter XII's Nerve economy, adjudicated: a Dread Check is a Will save against the Dread DC,
// and the app should roll it, read the four degrees, take the Nerve off the ladder, and hang the
// Frightened on the soul, the quiet bookkeeping a table forgets mid-fight. Pure and smoke-tested.

public static class Horror
{
    /// <summary>The Dread severity tier (1..5) for a Dread DC, which fixes the Nerve-loss die
    /// (Ch. XII: DC 10 → 1, 13 → 1d4, 16 → 1d6, 20 → 1d10, 25 → 1d10 + an Affliction).</summary>
    public static int DreadTier(int dc) => dc <= 10 ? 1 : dc <= 13 ? 2 : dc <= 16 ? 3 : dc <= 20 ? 4 : 5;

    public record DreadOutcome(int Die, int Will, int DreadDc, int Degree, string DegreeName,
        int NerveLost, bool Frightened, bool Steadied, bool Affliction, string Detail, bool Numb = false)
    {
        public string Line =>
            Numb ? $"Dread {DreadDc}: {DegreeName}. Nothing moves. The Hunger has taken the fear with it."
          : Steadied ? $"Dread {DreadDc}: {DegreeName}, steeled, no Nerve lost, and steady against it this scene."
          : NerveLost == 0 ? $"Dread {DreadDc}: {DegreeName}, held. No Nerve lost."
          : $"Dread {DreadDc}: {DegreeName}, {NerveLost} Nerve lost"
              + (Frightened ? ", and Frightened 1" : "")
              + (Affliction ? ", and a lasting Affliction" : "") + ".";
    }

    /// <summary>A Dread Check (Ch. XII). Crit success steadies (no Nerve); success steels (none);
    /// failure loses the ladder's Nerve; critical failure loses it and adds Frightened 1. A Dread
    /// DC of 25 (tier 5) also carries a lasting Affliction on any failure.</summary>
    public static DreadOutcome DreadCheck(int will, int dreadDc, int? forcedDie = null,
                                          CharacterSheet who = null)
    {
        int die = forcedDie ?? Rules.Rng.Next(1, 21);
        // Ch. XII gives a Returned soul +2 here, and it is added to the WILL rather than subtracted
        // from the DC so the four degrees are worked out against the number the book prints. An
        // optional parameter for the same reason IronCode.Strike takes forceType: every existing
        // caller means "a soul with nothing special about them", and that stays true unchanged.
        will += CharGen.DreadBonus(who);
        var (idx, name, detail) = Rules.FourDegrees(die, will, dreadDc);
        int tier = DreadTier(dreadDc);
        int nerve = 0; bool frightened = false, steadied = false, affliction = false;
        switch (idx)
        {
            case 3: steadied = true; break;                                        // critical success
            case 2: break;                                                         // success: steel yourself
            case 1: nerve = Rules.NerveLoss(tier).roll(); affliction = tier >= 5; break;   // failure
            default: nerve = Rules.NerveLoss(tier).roll(); frightened = true; affliction = tier >= 5; break; // crit fail
        }
        // At Hunger 3 the fear stops landing. The check is still ROLLED and still fails (the
        // Frightened and the Affliction both stand, because those are things done TO a soul) and
        // only the Nerve is spared, since Nerve is the one that measures being able to care.
        bool numb = nerve > 0 && CharGen.NumbToDread(who);
        if (numb) nerve = 0;
        return new DreadOutcome(die, will, dreadDc, idx, name, nerve, frightened, steadied, affliction, detail, numb);
    }

    /// <summary>The Mark step at which "the uncanny treats you as kin; +2 on your Dread Checks"
    /// (Ch. XII, The Mark).</summary>
    public const int MarkKin = 4;

    /// <summary>The Taint step called the Stain: "while you remain, you take –2 on every Dread
    /// Check" (Ch. XII, The Taint of the Land).</summary>
    public const int TaintStain = 3;

    /// <summary>What the Mark and the Taint do to a Dread Check: +2 at Mark 4, –2 at Taint 3. Both
    /// were printed as a number on the check and neither reached a roll, because both callers
    /// passed a bare Will. Added to the Will, never taken off the DC, for the reason the Returned's
    /// +2 is: the DC also picks the Nerve die, and neither of these was meant to move it.
    ///
    /// <para>The Stain holds only "while you remain" on the ground, and the app cannot see where
    /// the posse stands, so it is taken to hold unless the caller says otherwise. A Taint eases a
    /// step for every three days clear of the ground, so a soul still at 3 has not been away long;
    /// the Dread dialog asks the Keeper all the same.</para></summary>
    public static int DreadModifier(PartyMember soul, bool onStainedGround = true)
        => soul == null ? 0
         : (soul.Mark >= MarkKin ? 2 : 0) - (onStainedGround && soul.Taint >= TaintStain ? 2 : 0);

    /// <summary>A Dread Check for a posse soul, with everything the soul brings to it read off the
    /// soul: their Will, the Returned's +2 and the Mark and the Taint. One road, so no caller can
    /// remember three of the four.</summary>
    public static DreadOutcome DreadCheck(PartyMember soul, int dreadDc, int? forcedDie = null,
                                          bool onStainedGround = true)
        => DreadCheck((soul?.Will ?? 0) + DreadModifier(soul, onStainedGround), dreadDc, forcedDie, soul?.Sheet);

    /// <summary>Whether a Dread Check broke the soul who made it (Ch. XII, Breaking): it cost them
    /// Nerve, and it left them at 0. The app used to ask only whether the pool read 0 afterward,
    /// which broke a soul already standing at 0 who had just steeled themselves, and so a success
    /// cost them an Affliction. Nerve goes no lower than 0, and the book now says what a further
    /// failure there does: it breaks them again. A soul numbed by the Hunger loses no Nerve and so
    /// does not break, which is the point of being numb.</summary>
    public static bool Breaks(DreadOutcome o, int nerveAfter) => o != null && o.NerveLost > 0 && nerveAfter == 0;

    /// <summary>One row of the break table (Ch. XII): when a soul is driven to 0 Nerve, or fails a
    /// Dread Check while already there, roll a d6; on a 6 the clarity is its own wound and the soul
    /// gains +1 Mark.</summary>
    public record BreakOutcome(int Roll, bool GainsMark, string Text)
    {
        public string Line => $"Breaks (d6={Roll}): {Text}." + (GainsMark ? " +1 Mark." : "");
    }

    static readonly string[] BreakTable =
    {
        "freezes, loses the next turn, then acts Frightened",
        "flees, heedless, toward the nearest dark or door",
        "fires wild at the threat, and at whatever is near it",
        "goes to their knees, useless, until shaken hard",
        "hysterical laughter or weeping; others nearby test Nerve too",
        "a moment of terrible clarity; they understand, and gain +1 Mark",
    };

    /// <summary>Roll on the break table for a soul brought to 0 Nerve.</summary>
    public static BreakOutcome Break(int? forcedRoll = null)
    {
        int r = forcedRoll ?? Rules.Rng.Next(1, 7);
        return new BreakOutcome(r, r == 6, BreakTable[r - 1]);
    }

    // ---- the safe-table rule, resolved: reading what a thing left behind ----

    public record SignOutcome(int Die, int Mod, int Tier, int ReadDc, int DreadDc,
        int Degree, string DegreeName, string What, string Learned, string Detail)
    {
        /// <summary>Every reading is a fresh sign, so every reading fills a segment, including a
        /// bad one. The clock measures how often the posse has crossed this thing's trail, not how
        /// well they read it; what the roll decides is what they take away from the crossing.</summary>
        public bool FillsClock => true;

        public string Line => $"Reads the sign (Survival DC {ReadDc}): {DegreeName}. {Learned}";
    }

    /// <summary>Read the sign a Tier-<paramref name="tier"/> thing left (Bestiary, Appendix: The
    /// Grounds). A Survival check against the Tier's read DC, and the four degrees decide what the
    /// tracker takes away: everything, the direction, a bad feeling, or a reading that is simply
    /// backward. The Dread the reading costs comes back with the outcome rather than being rolled
    /// here: it is the reader's save, and the caller knows who is reading.</summary>
    public static SignOutcome ReadSign(int survivalMod, int tier, int? forcedDie = null)
    {
        var (readDc, dreadDc, what) = Rules.SpoorFor(tier);
        int die = forcedDie ?? Rules.Rng.Next(1, 21);
        var (idx, name, detail) = Rules.FourDegrees(die, survivalMod, readDc);
        return new SignOutcome(die, survivalMod, tier, readDc, dreadDc, idx, name,
                               what, Rules.SpoorRead(idx), detail);
    }
}
