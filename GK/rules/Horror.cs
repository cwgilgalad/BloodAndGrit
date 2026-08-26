namespace BloodAndGritKeeper;

// ============================================================ THE HORROR, ON RAILS
// Chapter XII's Nerve economy, adjudicated: a Dread Check is a Will save against the Dread DC,
// and the app should roll it, read the four degrees, take the Nerve off the ladder, and hang the
// Frightened on the soul — the quiet bookkeeping a table forgets mid-fight. Pure and smoke-tested.

public static class Horror
{
    /// <summary>The Dread severity tier (1..5) for a Dread DC, which fixes the Nerve-loss die
    /// (Ch. XII: DC 10 → 1, 13 → 1d4, 16 → 1d6, 20 → 1d10, 25 → 1d10 + an Affliction).</summary>
    public static int DreadTier(int dc) => dc <= 10 ? 1 : dc <= 13 ? 2 : dc <= 16 ? 3 : dc <= 20 ? 4 : 5;

    public record DreadOutcome(int Die, int Will, int DreadDc, int Degree, string DegreeName,
        int NerveLost, bool Frightened, bool Steadied, bool Affliction, string Detail, bool Numb = false)
    {
        public string Line =>
            Numb ? $"Dread {DreadDc}: {DegreeName} — nothing moves. The Hunger has taken the fear with it."
          : Steadied ? $"Dread {DreadDc}: {DegreeName} — steeled, no Nerve lost, and steady against it this scene."
          : NerveLost == 0 ? $"Dread {DreadDc}: {DegreeName} — held. No Nerve lost."
          : $"Dread {DreadDc}: {DegreeName} — {NerveLost} Nerve lost"
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
            case 2: break;                                                         // success — steel yourself
            case 1: nerve = Rules.NerveLoss(tier).roll(); affliction = tier >= 5; break;   // failure
            default: nerve = Rules.NerveLoss(tier).roll(); frightened = true; affliction = tier >= 5; break; // crit fail
        }
        // At Hunger 3 the fear stops landing. The check is still ROLLED and still fails — the
        // Frightened and the Affliction both stand, because those are things done TO a soul — and
        // only the Nerve is spared, since Nerve is the one that measures being able to care.
        bool numb = nerve > 0 && CharGen.NumbToDread(who);
        if (numb) nerve = 0;
        return new DreadOutcome(die, will, dreadDc, idx, name, nerve, frightened, steadied, affliction, detail, numb);
    }

    /// <summary>One row of the break table (Ch. XII): when a soul is driven to 0 Nerve, roll a d6;
    /// on a 6 the clarity is its own wound and the soul gains +1 Mark.</summary>
    public record BreakOutcome(int Roll, bool GainsMark, string Text)
    {
        public string Line => $"Breaks (d6={Roll}): {Text}." + (GainsMark ? " +1 Mark." : "");
    }

    static readonly string[] BreakTable =
    {
        "freezes — loses the next turn, then acts Frightened",
        "flees, heedless, toward the nearest dark or door",
        "fires wild at the threat — and at whatever is near it",
        "goes to their knees, useless, until shaken hard",
        "hysterical laughter or weeping; others nearby test Nerve too",
        "a moment of terrible clarity — they understand, and gain +1 Mark",
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
        /// <summary>Every reading is a fresh sign, so every reading fills a segment — including a
        /// bad one. The clock measures how often the posse has crossed this thing's trail, not how
        /// well they read it; what the roll decides is what they take away from the crossing.</summary>
        public bool FillsClock => true;

        public string Line => $"Reads the sign (Survival DC {ReadDc}): {DegreeName}. {Learned}";
    }

    /// <summary>Read the sign a Tier-<paramref name="tier"/> thing left (Bestiary, Appendix: The
    /// Grounds). A Survival check against the Tier's read DC, and the four degrees decide what the
    /// tracker takes away — everything, the direction, a bad feeling, or a reading that is simply
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
