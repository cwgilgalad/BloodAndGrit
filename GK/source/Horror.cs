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
        int NerveLost, bool Frightened, bool Steadied, bool Affliction, string Detail)
    {
        public string Line =>
            Steadied ? $"Dread {DreadDc}: {DegreeName} — steeled, no Nerve lost, and steady against it this scene."
          : NerveLost == 0 ? $"Dread {DreadDc}: {DegreeName} — held. No Nerve lost."
          : $"Dread {DreadDc}: {DegreeName} — {NerveLost} Nerve lost"
              + (Frightened ? ", and Frightened 1" : "")
              + (Affliction ? ", and a lasting Affliction" : "") + ".";
    }

    /// <summary>A Dread Check (Ch. XII). Crit success steadies (no Nerve); success steels (none);
    /// failure loses the ladder's Nerve; critical failure loses it and adds Frightened 1. A Dread
    /// DC of 25 (tier 5) also carries a lasting Affliction on any failure.</summary>
    public static DreadOutcome DreadCheck(int will, int dreadDc, int? forcedDie = null)
    {
        int die = forcedDie ?? Rules.Rng.Next(1, 21);
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
        return new DreadOutcome(die, will, dreadDc, idx, name, nerve, frightened, steadied, affliction, detail);
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
}
