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
/// <summary>The turn hourglass: how long the posse has, how much of it is gone, and what the glass
/// should look like — with no reference to drawing, so the smoke rig can hold it to all of that.
///
/// <para>It counts in milliseconds because the animation ticks far faster than a second, and it is
/// asked to render on every tick; a whole-second counter would make the sand fall in visible steps.
/// It is deliberately NOT a <c>System.Timers</c> anything: the caller owns the clock and feeds it
/// elapsed time, which is the only way a headless test can run five minutes in a millisecond.</para></summary>
public sealed class TurnClock
{
    /// Five minutes. Long enough for a posse of four to say what they are each doing, short enough
    /// that the fight keeps its shape. Ten is the other common house rule and is one click away.
    public const int DefaultSeconds = 300;

    /// The one-click lengths offered in the settings dialog and the drop-down, in seconds.
    public static readonly int[] Presets = { 60, 120, 180, 300, 600, 900 };

    public static string Spell(int seconds) => seconds % 60 == 0
        ? $"{seconds / 60} minute{(seconds / 60 == 1 ? "" : "s")}"
        : $"{seconds / 60}:{seconds % 60:00}";

    int preset = DefaultSeconds;

    /// <summary>How long a turn is, in seconds. Setting it re-loads the glass unless it is running,
    /// so changing the house rule mid-session doesn't cut the current turn short.</summary>
    public int PresetSeconds
    {
        get => preset;
        set
        {
            preset = Math.Clamp(value, 5, 3600);
            if (!Running) LeftMs = preset * 1000;
        }
    }

    public int LeftMs { get; private set; } = DefaultSeconds * 1000;
    public bool Running { get; private set; }

    /// <summary>True once the sand is through. Stays true until <see cref="Reset"/> — an expired
    /// glass is a fact about the turn, not a momentary event, so a Keeper who looks up late still
    /// sees that the time went.</summary>
    public bool Expired => LeftMs <= 0;

    /// <summary>How much of the turn has gone, 0 to 1 — the fraction of sand in the LOWER bulb.</summary>
    public double Spent => preset <= 0 ? 1 : Math.Clamp(1 - LeftMs / (preset * 1000.0), 0, 1);

    /// <summary>The face of the glass: m:ss remaining, and "0:00" once it is through. Rounded UP,
    /// so a glass reading 1:00 has a full minute in it rather than anything from 0 to 60 seconds —
    /// a timer that shows 0:00 for a whole second before it fires reads as a broken timer.</summary>
    public string Face
    {
        get
        {
            int s = Math.Max(0, (LeftMs + 999) / 1000);
            return $"{s / 60}:{s % 60:00}";
        }
    }

    public void Start() { if (Expired) Reset(); Running = true; }
    public void Pause() => Running = false;
    public void Toggle() { if (Running) Pause(); else Start(); }
    public void Reset() { LeftMs = preset * 1000; Running = false; }

    /// <summary>Hand the glass however many milliseconds have really passed. Returns true on the one
    /// tick that runs it out, so the caller can say so once instead of once per frame.</summary>
    public bool Tick(int ms)
    {
        if (!Running || ms <= 0) return false;
        bool wasRunning = LeftMs > 0;
        LeftMs = Math.Max(0, LeftMs - ms);
        if (LeftMs > 0) return false;
        Running = false;                 // it has run out; it does not keep counting downward
        return wasRunning;
    }
}

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

        /// <summary>Has this machine been shown around? False on a fresh install, which is what
        /// makes the first launch offer the tour. Set once the tour is finished OR declined, so
        /// nobody is asked twice — a walkthrough that keeps offering itself is a walkthrough
        /// people learn to dismiss without reading. Help ▸ Show me around re-runs it on purpose.
        /// Deliberately in prefs.json, not session.json: it belongs to the person at the keyboard,
        /// not to the game they happen to have loaded.</summary>
        public bool ToldTheTour { get; set; }

        /// <summary>Whether the Tracker shows the turn hourglass at all. Off by default: a table
        /// that has never asked to be timed should not find itself being timed.</summary>
        public bool TurnTimer { get; set; }

        /// <summary>How long one posse turn is allowed, in seconds. Settled before the session and
        /// kept between them — it is a house rule about how this table plays, not state belonging
        /// to any one fight, which is why it lives here and not in session.json. Five minutes by
        /// default; <see cref="TurnClock.Presets"/> holds the one-click choices.</summary>
        public int TurnSeconds { get; set; } = TurnClock.DefaultSeconds;
    }

    static string PathTo => Path.Combine(AppState.Dir, "prefs.json");

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

    /// <summary>What this soul carries out of the bad nights and does not put down: Lasting
    /// Injuries (Ch. XI — "they do not heal with rest alone; they take a Sawbones, time, and
    /// sometimes a graveyard") and Afflictions (Keeper's Book Ch. III — "the scars that stay").
    ///
    /// Both were in the app already and neither could be written down. The Reference deck printed
    /// the injury table, <see cref="Horror.DreadCheck"/> worked out whether a failure carried an
    /// Affliction and returned a flag no screen ever read, and a soul had nowhere to put either —
    /// so the one thing the game says is permanent lived on somebody's notepad, in the app whose
    /// whole promise is that nothing has to.</summary>
    public List<Scar> Scars { get; set; } = new();

    /// <summary>The scars as one line for the posse grid — "2: Gut-Shot, Sleepless".</summary>
    [JsonIgnore]
    public string ScarLine => Scars is not { Count: > 0 } ? ""
        : $"{Scars.Count}: " + string.Join(", ", Scars.Select(s => s.Name));

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
    string _name = "", _conditions = "", _ref = "", _pcId = "", _lastNote = "";
    int _init, _bloodCur, _bloodMax, _defense, _beats = 3, _mapStep = 1, _lastDelta, _signFilled;
    int _bleed, _deathAt;
    bool _isPC, _acting, _isSign, _hasActed, _stable, _upright;

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

    /// <summary>This row is the TRACE of a creature, not the creature — the safe-table rule made
    /// runnable (Bestiary, Appendix: The Grounds). A horror two or more Tiers over the posse takes
    /// the field like this: nothing to shoot, a Survival check to read, Nerve to be lost reading it,
    /// and a clock that fills toward the night it finally arrives. <see cref="Ref"/> still names the
    /// creature, so its Tier — and with it every DC — is derived rather than stored twice.</summary>
    public bool IsSign { get => _isSign; set { _isSign = value; On(); OnDerived(); } }

    /// <summary>How many segments of this thread's clock are filled. Each fresh sign of the same
    /// thing fills one; a full clock (<see cref="Rules.SpoorClockSegments"/>) is the night it comes
    /// in the flesh.</summary>
    public int SignFilled
    {
        get => _signFilled;
        set { _signFilled = Math.Clamp(value, 0, Rules.SpoorClockSegments); On(); OnDerived(); }
    }

    /// <summary>What just happened to this combatant, in the two or three characters a Keeper can
    /// read across a wide grid mid-fight — "−7", "+5", "PUT DOWN". Deliberately NOT saved: it is
    /// commentary on the last action, not state, and a reloaded session has no last action.</summary>
    [JsonIgnore] public string LastNote { get => _lastNote; set { _lastNote = value ?? ""; On(); } }

    /// <summary>Which way <see cref="LastNote"/> went — −1 harm, +1 mending, 0 nothing — so the
    /// grid can color it without parsing the words back out.</summary>
    [JsonIgnore] public int LastDelta { get => _lastDelta; set { _lastDelta = value; On(); } }

    // ---- Dying, bleeding, and death (Player's Book Ch. XI, "Wounds, Bleeding, and Death") ----
    // "At 0 Blood you fall, Dying and bleeding — losing 1 Blood each round — until someone
    // stabilizes you or you reach –CON, at which point you are dead, and out here dead is dead."
    //
    // The app printed that rule on the Reference deck from v1.4 and implemented none of it: Blood
    // clamped at zero, Down meant nothing more than "at zero", nobody bled and nobody could die. So
    // the one moment the whole game is built around — a soul on the ground with a count running —
    // was the one moment the Keeper had to run on paper.
    //
    // Blood does NOT go negative. Every screen, every save and every bar in the app reads BloodCur
    // as 0..max and would have to be re-proved; instead the ground below zero is its own number.
    // <see cref="Bleed"/> is how far past zero they are, counting up toward <see cref="DeathAt"/>.

    /// <summary>How far past 0 Blood this one has bled — the distance travelled toward −CON. Zero
    /// for anybody still standing, and for anybody the rule does not govern.</summary>
    public int Bleed { get => _bleed; set { _bleed = Math.Max(0, value); On(); OnDying(); } }

    /// <summary>The −CON this one dies at, held as a positive number. A soul takes it from their
    /// sheet's CON; 0 means the dying rule does not run here at all, which is every creature and
    /// every hand-entered row until a Keeper says otherwise. That default is deliberate: the book
    /// writes this rule for characters, and the Bestiary's answer to a horror at 0 Blood is its own
    /// <c>puttingItDown</c> line, not a count of rounds.</summary>
    public int DeathAt { get => _deathAt; set { _deathAt = Math.Clamp(value, 0, 99); On(); OnDying(); } }

    /// <summary>The bleeding has been stopped (Fortitude DC 15, or a Medicine check at the same DC).
    /// Still at 0 Blood and still senseless — stable is not awake — but no longer on the clock.</summary>
    public bool Stable { get => _stable; set { _stable = value; On(); OnDying(); } }

    /// <summary>Grit, spent to refuse to fall: "when dropped to 0 Blood, stay conscious and on your
    /// feet for one more round" (Ch. II). It cannot be derived from anything — at 0 Blood
    /// <see cref="Down"/> is true and <see cref="Rules.CanAct"/> refuses the turn — so the exception
    /// has to be a fact of its own. Cleared when the round turns over, which is what "one more
    /// round" means. It does not stop the bleeding; the book buys consciousness with it, not
    /// time.</summary>
    public bool Upright { get => _upright; set { _upright = value; On(); OnDying(); } }

    [JsonIgnore] public bool Down => !_isSign && _bloodCur <= 0;

    /// <summary>Dead. Out here dead is dead: no turn, no order, no roll.</summary>
    [JsonIgnore] public bool Dead => !_isSign && _deathAt > 0 && _bleed >= _deathAt;

    /// <summary>On the ground with the count running — at 0 Blood, governed by the rule, not yet
    /// stopped and not yet gone.</summary>
    [JsonIgnore] public bool Dying => Down && _deathAt > 0 && !_stable && !Dead;

    /// <summary>Rounds left before <see cref="DeathAt"/> is reached at a Blood a round. Zero once
    /// they are dead; zero, too, for anyone the rule does not govern.</summary>
    [JsonIgnore] public int RoundsToDeath => Dying ? Math.Max(0, _deathAt - _bleed) : 0;

    /// <summary>What the tracker prints where a standing combatant's Blood maximum goes. For anyone
    /// on the ground that number tells the Keeper nothing they need; the count does.</summary>
    [JsonIgnore]
    public string DyingLine =>
        Dead ? "dead"
      : !Down || _deathAt <= 0 ? ""
      : _stable ? "stable"
      : $"dying −{_bleed} of {_deathAt}";

    void OnDying()
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(Dead)));
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(Dying)));
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(RoundsToDeath)));
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(DyingLine)));
    }

    /// <summary>What the NEXT Strike this turn costs in MAP, in one word for the tracker. An Agile
    /// weapon softens it to −4/−8, which the Strike dialog figures once a weapon is picked; this is
    /// the plain step, so a Keeper glancing at the field knows whether the shot is still clean.</summary>
    [JsonIgnore] public string NextStrike => _isSign ? "—" : _mapStep <= 1 ? "clean" : _mapStep == 2 ? "−5" : "−10";

    /// <summary>The spoor clock as the tracker paints it in words — filled segments, then empty.
    /// Blank for anything with blood in it.</summary>
    [JsonIgnore]
    public string SignClock => !_isSign ? ""
        : new string('▮', _signFilled) + new string('▯', Rules.SpoorClockSegments - _signFilled);

    /// <summary>A sign whose clock has filled: the thread is spent, and the thing arrives.</summary>
    [JsonIgnore] public bool SignFull => _isSign && _signFilled >= Rules.SpoorClockSegments;

    void OnDerived()
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(SignClock)));
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(NextStrike)));
    }

    /// <summary>Take Blood off, or put it back, and leave the tracker a note about it. One method
    /// rather than a clamp at each call site, because every route to a wound — the Strike engine,
    /// the Damage button, the right-click menu — owes the Keeper the same visible answer.</summary>
    public void Wound(int delta, string note = null)
    {
        if (_isSign) return;
        int hi = _bloodMax > 0 ? _bloodMax : int.MaxValue;
        int was = _bloodCur, wasBleed = _bleed;
        bool wasDead = Dead;
        int raw = _bloodCur + delta;
        BloodCur = Math.Clamp(raw, 0, hi);

        // Below zero the harm does not stop counting — it fills the ground between 0 and −CON.
        // This is a READING of the book rather than a quotation of it: Ch. XI says you bleed a
        // Blood a round "until ... you reach –CON", which only makes sense if Blood is a real
        // number that goes negative, and a shot that takes a soul from 4 to −14 has reached it.
        // The alternative — overkill vanishing at zero — would make a cannonball and a slap
        // identical to a soul standing on 1 Blood, and the chapter's own sidebar is titled
        // "The Mercy of Lethality". Only rows the rule governs are touched; DeathAt is 0 on every
        // creature, so nothing about a horror at 0 Blood changes.
        if (_deathAt > 0 && !wasDead)
        {
            if (raw < 0) Bleed = _bleed - raw;             // raw is negative; its magnitude is the overkill
            else if (_bloodCur > 0) { Bleed = 0; Stable = false; Upright = false; }
        }

        int moved = _bloodCur - was;
        int overkill = _bleed - wasBleed;
        LastDelta = moved != 0 ? Math.Sign(moved) : overkill > 0 ? -1 : 0;
        LastNote = note ?? (Dead && !wasDead ? "KILLED"
                          : moved == 0 && overkill == 0 ? (delta < 0 ? "no effect" : "already full")
                          : Dying && overkill > 0 && was <= 0 ? $"−{overkill} — bleeding"
                          : Down ? $"−{Math.Abs(moved) + overkill} — DOWN"
                          : (moved > 0 ? "+" : "−") + Math.Abs(moved));
    }

    /// <summary>Forget what last happened here — a new round is a clean page.</summary>
    public void ClearLast() { LastDelta = 0; LastNote = ""; }

    /// <summary>Have they already had their turn this round? Kept so the app can track the round
    /// itself instead of asking the Keeper to — and so the field can show, at a glance, who is
    /// still to go. Persisted: a fight in progress survives a restart, and so must this.</summary>
    public bool HasActed { get => _hasActed; set { _hasActed = value; On(); } }

    /// <summary>Start this combatant's turn: Beats back to three, the next Strike clean, the row
    /// lit as the one acting, and their turn marked spent for the round. Clearing everyone else is
    /// the caller's business — the model has no idea who else is on the field.</summary>
    public void BeginTurn() { Beats = 3; MapStep = 1; Acting = true; HasActed = true; }

    /// <summary>Is this tracker row the given posse soul? By the stable PcId when it has one, else
    /// by Name — so a rename never breaks the link, and two same-named souls stay distinct.</summary>
    public bool IsSoul(PartyMember p)
        => _isPC && p != null && (!string.IsNullOrEmpty(_pcId) ? _pcId == p.Id : _name == p.Name);

    // ---- Signs, Miracles, and creature powers currently working on this one ----

    /// <summary>What is working ON this combatant right now — the effect half of a Sign (Ch. XIII),
    /// a Miracle (Ch. VI), or a creature's own power. Kept on the target rather than on the worker
    /// because the question a Keeper asks mid-fight is "what is on HIM?", and an effect outlives the
    /// turn that caused it. Who caused it rides along inside each entry.</summary>
    public List<WorkedEffect> Worked { get; set; } = new();

    /// <summary>The chips the tracker paints in the Worked column: the mark of the kind, the name,
    /// and the rounds left. Short on purpose — the whole of it is a tooltip and a right-click away,
    /// and a column a Keeper has to stop and read is a column they stop reading.</summary>
    [JsonIgnore]
    public string WorkedChips => Worked == null || Worked.Count == 0 ? ""
        : string.Join("  ", Worked.Select(w => w.Chip));

    /// <summary>Put an effect on this one, and say so.</summary>
    public void Work(WorkedEffect e)
    {
        if (e == null) return;
        (Worked ??= new()).Add(e);
        On(nameof(WorkedChips));
    }

    /// <summary>Take an effect off — it ran out, or it was ended.</summary>
    public void Unwork(WorkedEffect e)
    {
        if (e == null || Worked == null) return;
        Worked.Remove(e);
        On(nameof(WorkedChips));
    }

    /// <summary>A round has passed: everything counted in rounds loses one, and anything that
    /// reaches zero comes off. Only workings whose duration IS a round count are touched — "for a
    /// scene", "until dawn" and "until it is doctored" are the book's commonest durations and a
    /// combat round is the wrong unit for all three, so a clock that silently expired them would be
    /// worse than no clock.
    ///
    /// The test is on <see cref="WorkedEffect.RoundsLeft"/> alone and deliberately NOT also on
    /// <see cref="WorkedEffect.Ends"/>. Adding Ends as a second condition looked like belt and
    /// braces and was actually a migration bug: an effect saved before v1.29.0 carries no Ends at
    /// all, deserializes to the default, and would have quietly stopped counting down in every
    /// session anybody had already saved. RoundsLeft is the field that has always meant "counted",
    /// so it stays the one that decides.</summary>
    public List<WorkedEffect> TickWorked()
    {
        var done = new List<WorkedEffect>();
        if (Worked == null) return done;
        foreach (var w in Worked.ToList())
        {
            if (w.RoundsLeft < 0) continue;
            w.RoundsLeft--;
            if (w.RoundsLeft <= 0) { done.Add(w); Worked.Remove(w); }
        }
        if (done.Count > 0) On(nameof(WorkedChips));
        return done;
    }
}

/// <summary>A mark a soul does not get to put down: a Lasting Injury off the d6 (Ch. XI) or an
/// Affliction out of a bad Dread Check (Keeper's Book Ch. III). Deliberately a plain record with a
/// free-text note — the books name the six injuries and leave the Afflictions to the table, so the
/// app names what it knows and lets the Keeper write the rest.</summary>
public class Scar
{
    /// <summary>"Injury" or "Affliction" — which of the two ledgers this belongs on.</summary>
    public string Kind { get; set; } = "Injury";
    public string Name { get; set; } = "";
    /// <summary>How it happened, or what it costs at the table. The Keeper's own words.</summary>
    public string Note { get; set; } = "";
    /// <summary>The session date, as the Keeper stamped it, or whatever they typed.</summary>
    public string When { get; set; } = "";

    [JsonIgnore] public string Mark => Kind == "Affliction" ? "☾" : "✚";
    [JsonIgnore]
    public string Full => $"{Mark} {Name} — {Kind}"
        + (string.IsNullOrWhiteSpace(When) ? "" : $", {When}")
        + (string.IsNullOrWhiteSpace(Note) ? "" : $"\n{Note}");
}

/// <summary>One Sign, Miracle, or creature power in play: what it is, who worked it, what it cost,
/// what it does, and how long it has left. The cause and the effect travel together — an effect
/// whose source is forgotten is a note a Keeper cannot adjudicate.</summary>
public class WorkedEffect
{
    public string Name { get; set; } = "";
    /// <summary>"Sign" (Ch. XIII) · "Miracle" (Ch. VI) · "Power" (a creature's own).</summary>
    public string Kind { get; set; } = "Sign";
    public int Rank { get; set; }
    /// <summary>Who worked it — the cause. A name, not a reference: the worker may leave the field,
    /// or die, and the thing they did is still on the target.</summary>
    public string Source { get; set; } = "";
    /// <summary>The cost exactly as the book prints it, e.g. "1 Beat · 2 Nerve · Will save".</summary>
    public string Cost { get; set; } = "";
    /// <summary>What it does, in the book's own words.</summary>
    public string Effect { get; set; } = "";
    /// <summary>Rounds remaining, or −1 for anything the tracker does not count down. Note that −1
    /// is NOT the same as "the Keeper ends it by hand": a scene, an hour and until-dawn all ride at
    /// −1 because a combat round is the wrong unit for them, and <see cref="Ends"/> is what says
    /// which of them this one actually is. Conflating the two is exactly what made every long
    /// working read as "until it is ended by hand" on the chip.</summary>
    public int RoundsLeft { get; set; } = -1;
    /// <summary>The round it was worked on, so the log and the tooltip can say when.</summary>
    public int SinceRound { get; set; } = 1;

    /// <summary>Who it landed on, as the reader worked it out from the printed text.</summary>
    public Rules.WorkShape Shape { get; set; } = Rules.WorkShape.Unclear;
    /// <summary>The radius the book printed, when it printed one.</summary>
    public int AreaFeet { get; set; }
    /// <summary>What actually ends it — the fact <see cref="RoundsLeft"/> cannot carry.</summary>
    public Rules.WorkEnds Ends { get; set; } = Rules.WorkEnds.UntilEnded;
    /// <summary>What working it costs the worker when it goes wrong. Signs all carry one, Miracles
    /// none. It used to sit buried in the middle of <see cref="Effect"/>, which is where a Keeper
    /// looks last and needs it first.</summary>
    public string Backlash { get; set; } = "";
    /// <summary>What happened when it was worked — the dice that were actually rolled and who they
    /// landed on ("14 damage, saved for half → 7"). The book says what a working does; this says
    /// what it did, which is the half the table argues about an hour later.</summary>
    public string Note { get; set; } = "";

    [JsonIgnore] public string Mark => Kind == "Miracle" ? "✝" : Kind == "Power" ? "◈" : "✦";

    /// <summary>How long is left, in the unit the book used rather than in rounds it never
    /// mentioned. <see cref="RoundsLeft"/> wins when it is counting, because that is the field the
    /// tracker actually ticks and an effect saved before v1.29.0 has a round count and no
    /// <see cref="Ends"/> — it still has to read correctly.</summary>
    [JsonIgnore]
    public string Duration =>
        RoundsLeft > 0 ? $"{RoundsLeft} rd" + (RoundsLeft == 1 ? "" : "s")
      : RoundsLeft == 0 ? "spent"
      : Ends switch
        {
            Rules.WorkEnds.NextTurn   => "to their next turn",
            Rules.WorkEnds.Scene      => "the scene",
            Rules.WorkEnds.Hour       => "an hour",
            Rules.WorkEnds.Day        => "a day",
            Rules.WorkEnds.UntilDawn  => "until dawn",
            Rules.WorkEnds.Instant    => "done",
            _                         => "until ended",
        };

    /// <summary>The terse tag in the grid's Worked column. A counted working shows its count; the
    /// rest show the word the book used, because "(scene)" and "(dawn)" tell a Keeper something and
    /// a bare name tells them nothing about when to stop applying it.</summary>
    [JsonIgnore]
    public string Chip => $"{Mark} {Name}" +
        (RoundsLeft >= 0 ? $" ({RoundsLeft})"
       : Ends switch
        {
            Rules.WorkEnds.NextTurn   => " (turn)",
            Rules.WorkEnds.Scene      => " (scene)",
            Rules.WorkEnds.Hour       => " (hour)",
            Rules.WorkEnds.Day        => " (day)",
            Rules.WorkEnds.UntilDawn  => " (dawn)",
            _                         => "",
        });

    /// <summary>The whole of it, for a tooltip or a menu: what it is, who caused it, who it landed
    /// on, what it cost, what it did, when it stops — and, for a Sign, what it costs the worker
    /// when it turns on them.</summary>
    [JsonIgnore]
    public string Full =>
        $"{Mark} {Name} — {Kind}" + (Rank > 0 ? $", Rank {Rank}" : "") + "\n"
        + $"Worked by {(string.IsNullOrWhiteSpace(Source) ? "someone" : Source)}, round {SinceRound}\n"
        + $"Lands: {ShapeLine}\n"
        + (string.IsNullOrWhiteSpace(Cost) ? "" : $"Cost: {Cost}\n")
        + $"Ends: {Duration}\n"
        + (string.IsNullOrWhiteSpace(Note) ? "" : $"Rolled: {Note}\n")
        + "\n" + Effect
        + (string.IsNullOrWhiteSpace(Backlash) ? "" : $"\n\nBacklash: {Backlash}");

    /// <summary>Who it landed on, in words. Mirrors <see cref="Rules.Working.ShapeLine"/>; kept here
    /// too because a saved session carries the shape and not the working it was read from.</summary>
    [JsonIgnore]
    public string ShapeLine => Shape switch
    {
        Rules.WorkShape.Self        => "the worker",
        Rules.WorkShape.OneCreature => "one creature",
        Rules.WorkShape.Ally        => "one willing soul",
        Rules.WorkShape.Area        => AreaFeet > 0 ? $"everything within {AreaFeet} feet" : "everything nearby",
        Rules.WorkShape.Place       => "a place, a thing, or nobody at all",
        Rules.WorkShape.Counter     => "another working",
        Rules.WorkShape.Trait       => "nothing — this is what it IS",
        _                           => "whoever the Keeper said",
    };
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

    /// <summary>Sign &amp; spoor — the threads on the trail, kept apart from the field because they
    /// are not on it. A trace takes no initiative and no turn, so putting it in <see cref="Tracker"/>
    /// made the Keeper read past a row that could never act. Sessions written before this list
    /// existed carry their traces inside Tracker; ApplySession moves them across on load.</summary>
    public List<Combatant> Signs { get; set; } = new();

    public int Round { get; set; } = 1;
    public List<MapMarker> MapMarkers { get; set; } = new();
    public List<Ride> Rides { get; set; } = new();

    /// <summary>Nothing in it at all — the only state in which handing a Keeper the Appendix D
    /// pregens is help rather than a mess.
    ///
    /// The launch path used to ask a much cruder question, "is the PARTY empty?", and if it was it
    /// seeded the demo posse and never applied the loaded session at all. So a table whose posse
    /// the Keeper had cleared — an all-NPC night, a party wiped and not yet rebuilt — came back
    /// next launch with its written ledger, its clocks, its rides, its map markers and its tracker
    /// all gone, and then autosaved that loss over the file on the way out. An empty posse is a
    /// legitimate table; it is not an empty session.
    ///
    /// Here rather than on the form so the smoke rig can hold it: this decides whether a Keeper's
    /// work is kept, and it is the kind of thing that is only ever wrong months later.</summary>
    [JsonIgnore]
    public bool IsUntouched =>
        (Party is not { Count: > 0 }) && (Tracker is not { Count: > 0 })
        && (Signs is not { Count: > 0 }) && (Clocks is not { Count: > 0 })
        && (Rides is not { Count: > 0 }) && (MapMarkers is not { Count: > 0 })
        && (EncounterCreatures is not { Count: > 0 })
        && string.IsNullOrWhiteSpace(Notes);
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

    /// <summary>Sign and spoor — the safe-table rule's numbers (Bestiary, Appendix: The Grounds).
    /// <para><i>Spoor</i> is the physical trace a thing leaves: track, scat, hair, blood, the
    /// scrape on a tree at a height that stops the conversation. <i>Sign</i> is everything wider
    /// than that — a kill, a silence, stock that won't go back in the barn. When a horror stands
    /// two or more Tiers over the posse it does not arrive in the flesh; it arrives as this, and
    /// the scene is a reading, not a fight.</para>
    /// <para>Read the sign with Survival at <c>ReadDc</c>. It costs Nerve like anything else, but
    /// one rung down the ladder from meeting the thing — the aftermath is not the animal — which
    /// is why <c>DreadDc</c> here is the Dread DC of the Tier BELOW, and a Tier I trace costs
    /// nothing at all.</para></summary>
    public static readonly (int readDc, int dreadDc, string what)[] SpoorRow =
    {
        (12,  0, "Tracks, and a killed animal that was eaten properly"),
        (14, 10, "A killed animal that was not eaten, and was not left the way a beast leaves one"),
        (16, 13, "A killed man, and the manner of it plain in what's left"),
        (18, 16, "A killed party, and one survivor who will not go back"),
        (20, 20, "A place unmade — ground, weather, and the people in it, all wrong together"),
    };

    /// <summary>The sign a creature of this Tier leaves: the Survival DC to read it, the Dread DC
    /// reading it costs, and what is actually on the ground. Clamped, so an off-book Tier still
    /// answers rather than throwing at the table.</summary>
    public static (int readDc, int dreadDc, string what) SpoorFor(int creatureTier)
        => SpoorRow[Math.Clamp(creatureTier - 1, 0, SpoorRow.Length - 1)];

    /// <summary>Does the safe-table rule apply — is this thing so far over the posse that it may
    /// only appear as sign and spoor? The one authority; <see cref="Cost"/> decides it, and both
    /// the Encounter tab's verdict and the Tracker's refusal to put it on the field read this.</summary>
    public static bool SignOnly(int creatureTier, int partyLevel) => Cost(creatureTier, partyLevel).spoor;

    /// <summary>What a Survival check against <see cref="SpoorRow"/> buys, by degree — the same
    /// ordered 0–3 scale <see cref="FourDegrees"/> returns.</summary>
    public static string SpoorRead(int degree) => degree switch
    {
        3 => "What it is, how many, how long ago, which way — and whether it already knows about you.",
        2 => "What it is, and which way it went.",
        1 => "Something passed, and it was wrong. Nothing further.",
        _ => "You read it backward: the wrong direction, the wrong number, or you miss that it is circling.",
    };

    /// <summary>The safe-table rule turns a monster into a thread. Four segments: each fresh sign
    /// of the same thing fills one, and a filled clock is the night it finally arrives in the
    /// flesh — by which time the posse should be a Tier higher, or have a plan.</summary>
    public const int SpoorClockSegments = 4;

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
        string detail = $"d20({die}) {(mod>=0?"+":"")}{mod} = {total} vs DC {dc}";
        Daybook.Note("check", $"{detail} → {deg}");
        return (idx, deg, detail);
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
        if (bits.Count == 0)
        {
            // Worth a line of its own: an expression the parser could not read returns 0 and says
            // so quietly, which at the table looks like a roll that came up nothing.
            Daybook.Note("roll", $"\"{expr}\" — could not parse");
            return (0, "could not parse", dice);
        }
        string bd = string.Join(" ", bits);
        Daybook.Note("roll", $"{expr} → {bd} = {total}");
        return (total, bd, dice);
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
    /// <summary>What Tier a posse of this level stands at — ceil(level/2), the ladder the encounter
    /// budget and the safe-table rule are both measured against. One authority, so "two Tiers over"
    /// means the same arithmetic wherever the app says it.</summary>
    public static int PartyTier(int partyLevel) => Math.Max(1, (partyLevel + 1) / 2);

    // ---- the marks that do not wash off (Player's Book Ch. XI · Keeper's Book Ch. III) ----

    /// <summary>The six Lasting Injuries, in the book's own d6 order. Lives here rather than typed
    /// into the Reference leaf so the printed table and the roller are the same six words — the
    /// leaf renders from this list, and rolling one picks out of it.</summary>
    public static readonly string[] LastingInjuries =
    { "Bloody Gash", "Cracked Ribs", "Maimed Hand", "Lamed Leg", "Ruined Eye or Ear", "Gut-Shot" };

    /// <summary>The Fortitude DC a terrible blow demands, per the Reference leaf and Ch. XI.</summary>
    public const int GrievousDc = 15;

    /// <summary>Was that a terrible blow? "One hit for half maximum Blood or more, or any critical
    /// hit" (Ch. XI). Printed on the Keeper's screen since v1.4 and implemented nowhere until
    /// v1.29.0 — the app read the rule out to the Keeper and then left them to remember it.</summary>
    public static bool IsGrievous(int damage, int bloodMax, bool crit)
        => damage > 0 && (crit || (bloodMax > 0 && damage * 2 >= bloodMax));

    /// <summary>Roll one off the d6 table, as the injury and the die that found it.</summary>
    public static (int die, string injury) RollInjury()
    {
        int d = Rng.Next(1, LastingInjuries.Length + 1);
        return (d, LastingInjuries[d - 1]);
    }

    /// <summary>The ten Afflictions and what each one costs, transcribed from the Keeper's Book
    /// Ch. III ("Afflictions — the Scars That Stay"). The app had a hand-invented list of
    /// suggestions here for about an hour, which is exactly the mistake this project keeps
    /// closing: the book already had a d10, so the book's d10 is what the app offers.</summary>
    public static readonly (string name, string cost)[] Afflictions =
    {
        ("The Shakes",       "−2 to anything fine or steady-handed while under any strain"),
        ("Night Terrors",    "No Nerve returns from sleep alone — only by a fire, in company, or in drink"),
        ("The Long Stare",   "−2 to be trusted or read by folk; they see the haunt on you"),
        ("A Compulsion",     "A small rite — counting, salt, a rhyme — must be done, or be Shaken until it is"),
        ("The Cold",         "Never quite warm again; −2 against cold and against fear"),
        ("Faithless",        "The old comforts — prayer, ward, hymn — no longer steady you as they did"),
        ("The Whisper",      "You hear it now; once a session it tells you something true, to earn a lie later"),
        ("Brittle Nerve",    "Begin each session at −2 maximum Nerve until it heals"),
        ("Marked in Dreams", "The dark knows where you sleep; count your Taint exposure one step worse"),
        ("The Hollow",       "A piece did not come back; −1 to one ability score until you are made whole"),
    };

    /// <summary>Roll one off the d10, as the Affliction, what it costs, and the die that found it.
    /// </summary>
    public static (int die, string name, string cost) RollAffliction()
    {
        int d = Rng.Next(1, Afflictions.Length + 1);
        var a = Afflictions[d - 1];
        return (d, a.name, a.cost);
    }

    // ---- whose turn it is, and when the round is over ----

    /// <summary>A roll for a place in the order. The Player's Book is plain about what this is —
    /// "Initiative: a Notice check" — and the tracker rolled a bare d20 for everyone for eleven
    /// releases, so a Scout with Notice +9 took their place in the line exactly as often as the
    /// bandit beside them. The bonus comes from the roller's sheet where there is one
    /// (<see cref="CharGen.InitiativeBonus"/>); a creature has no skill ranks in its stat block, so
    /// it passes 0 and rolls the plain die rather than being handed a number the book never gave it.
    ///
    /// Floored at 1 on purpose: a low-Wits soul can carry a negative bonus, and 0 is the value the
    /// tracker uses to mean "has not rolled yet". A rolled 0 and an unrolled 0 must not look alike.
    /// </summary>
    public static int RollInitiative(int noticeBonus) => Math.Max(1, Rng.Next(1, 21) + noticeBonus);

    /// <summary>Can this one still be handed a turn this round? A trace takes none, someone bleeding
    /// out takes none, and nobody takes two — unless they have spent Grit to refuse to fall, which
    /// is the one thing in the book that buys a turn out of a body at 0 Blood (Ch. II). The dead are
    /// never <see cref="Combatant.Upright"/>; <see cref="RefuseToFall"/> is what keeps that true.
    /// </summary>
    public static bool CanAct(Combatant c)
        => c != null && !c.HasActed && !c.IsSign && !c.Dead && (!c.Down || c.Upright);

    // ---- Dying, stabilised, dead (Player's Book Ch. XI) ----

    /// <summary>The DC to stop somebody bleeding, whether it is their own Fortitude save or another
    /// soul's Medicine check — the book gives both the same number.</summary>
    public const int StabilizeDc = 15;

    /// <summary>Where a soul's −CON sits. Off the sheet where there is one; where there is not, the
    /// app has no CON to read and says so rather than inventing a number that looks authoritative —
    /// 10 is the middle of the scale and the Keeper can overrule it.</summary>
    public const int DefaultDeathAt = 10;

    /// <summary>A soul's death threshold: their CON. Returns <see cref="DefaultDeathAt"/> for a soul
    /// with no sheet, which is every hand-entered row on the Posse tab.</summary>
    public static int DeathThresholdFor(CharacterSheet s)
        => s?.Scores != null && s.Scores.TryGetValue("CON", out int con) && con > 0 ? con : DefaultDeathAt;

    /// <summary>What one round costs the fallen. Everyone the rule governs loses a Blood, and the
    /// Grit that kept somebody standing runs out — "one more round" is one round.
    ///
    /// <para>Returns what happened to each of them so the caller can say it by name. A soul dying
    /// quietly in a column of numbers is the exact failure this app exists to prevent, and an
    /// effect that expires without a word is the fault this project already fixed once for the
    /// Worked chips.</para>
    ///
    /// <para>Out here rather than inside <see cref="NewRound"/> so it can be tested without a round,
    /// and so NewRound's signature — which the playtest harness and the smoke rig both call —
    /// does not change.</para></summary>
    public static List<(Combatant Who, int Bleed, bool Died, bool Fell)> BleedOut(IEnumerable<Combatant> field)
    {
        var news = new List<(Combatant, int, bool, bool)>();
        if (field == null) return news;
        foreach (var c in field)
        {
            if (c == null || c.IsSign) continue;
            // The Grit is spent whether or not they are still on the ground: it bought a round and
            // the round is over. Cleared BEFORE the bleed so "fell" and "bled" can be reported of
            // the same round, which is what actually happens at the table.
            bool fell = c.Upright;
            if (fell) c.Upright = false;
            if (!c.Dying) { if (fell) news.Add((c, c.Bleed, false, true)); continue; }
            c.Bleed += 1;
            news.Add((c, c.Bleed, c.Dead, fell));
        }
        return news;
    }

    /// <summary>Spend Grit to refuse to fall (Ch. II): "when dropped to 0 Blood, stay conscious and
    /// on your feet for one more round." Refuses the dead, refuses anybody still standing, and
    /// refuses a soul with no Grit left — and answers WHY, so no caller can turn it down in silence.
    /// </summary>
    public static string RefuseToFall(Combatant c, PartyMember soul)
    {
        if (c == null) return "Nobody is selected.";
        if (c.Dead) return $"{c.Name} is dead. Grit does not reach that far.";
        if (!c.Down) return $"{c.Name} is still on their feet — there is nothing to refuse yet.";
        if (c.Upright) return $"{c.Name} is already refusing to fall this round.";
        if (soul == null) return $"{c.Name} is not a posse soul, and Grit is the posse's alone.";
        if (soul.Grit <= 0) return $"{soul.Name} has no Grit left to spend.";
        soul.Grit -= 1;
        c.Upright = true;
        return null;
    }

    /// <summary>Stop the bleeding. The book gives a Fortitude save and a Medicine check the same DC,
    /// so this takes the roll and the modifier and does not care which it was. A critical success
    /// also brings them round on 1 Blood — the one degree the four-degree ladder has spare here, and
    /// the reading that keeps a natural 20 worth rolling.</summary>
    public record StabilizeOutcome(int Die, int Mod, int Degree, string DegreeName, bool Stopped,
                                   bool Woke, string Detail)
    {
        public string Line => !Stopped
            ? $"Stabilize (DC {StabilizeDc}): {DegreeName} — still bleeding."
            : Woke ? $"Stabilize (DC {StabilizeDc}): {DegreeName} — the bleeding stops and they come round on 1 Blood."
                   : $"Stabilize (DC {StabilizeDc}): {DegreeName} — the bleeding stops. Still senseless.";
    }

    /// <summary>Try to stop somebody bleeding out. Applies the result: a success sets
    /// <see cref="Combatant.Stable"/>, a critical success also puts a Blood back in them.</summary>
    public static StabilizeOutcome Stabilize(Combatant c, int mod, int? forcedDie = null)
    {
        int die = forcedDie ?? Rng.Next(1, 21);
        var (idx, name, detail) = FourDegrees(die, mod, StabilizeDc);
        bool stopped = idx >= 2, woke = idx == 3;
        if (c != null && stopped)
        {
            c.Stable = true;
            if (woke) c.Wound(1, "stabilized");   // Wound clears Bleed and Stable on the way up
        }
        return new StabilizeOutcome(die, mod, idx, name, stopped, woke, detail);
    }

    // ---- the Beat, spent (Ch. XI: "The turn — three Beats, spent as you like") ----
    // The Beats were counted from the start and never enforced. A Strike decremented them and then
    // resolved anyway at zero (see CombatFlow.StrikeAndApply, which guards the subtraction and not
    // the attack), so a fourth, fifth and sixth Strike in one turn were free and the MAP step went
    // on climbing past anything the book prints. Working a Sign cost nothing at all, though the app
    // has parsed "1 Beat" off its printed cost line since v1.20. The turn had a budget on screen and
    // no budget in fact, which is the one shape of bug this app exists to prevent.
    //
    // Both live here, in one pair, because the answer and the REASON for the answer have to agree —
    // a button that goes grey without saying why is a button a Keeper reports as broken.

    /// <summary>How many Beats a working's printed time line costs. "1 Beat" is one and "3 Beats"
    /// three; "1 minute", "10 minutes", "one hour" and the rest are not things done inside a turn,
    /// so they cost none. Anything unparseable costs none — the Keeper can still read the printed
    /// line, and inventing a cost from a string we did not understand is worse than charging nothing.
    /// </summary>
    public static int BeatsFor(string time)
    {
        var m = System.Text.RegularExpressions.Regex.Match(time ?? "", @"(\d+)\s*Beat",
            System.Text.RegularExpressions.RegexOptions.IgnoreCase);
        if (m.Success) return Math.Clamp(int.Parse(m.Groups[1].Value), 0, 9);
        // The book writes a single Beat both ways — "1 Beat" and "one Beat".
        return System.Text.RegularExpressions.Regex.IsMatch(time ?? "", @"\bone\s+Beat\b",
            System.Text.RegularExpressions.RegexOptions.IgnoreCase) ? 1 : 0;
    }

    /// <summary>Has this one the Beats to do a thing that costs <paramref name="beats"/>? A free
    /// action (a working the book times in minutes) is always allowed; a trace and a body on the
    /// ground never act.</summary>
    public static bool CanSpendBeats(Combatant c, int beats = 1)
        => c != null && !c.IsSign && !c.Down && (beats <= 0 || c.Beats >= beats);

    /// <summary>Why not — the sentence the dialog prints beside the greyed button. Null when the
    /// action is allowed, so a caller can write <c>if (Rules.WhyNoBeats(c) is string why)</c> and
    /// never end up refusing in silence.</summary>
    public static string WhyNoBeats(Combatant c, int beats = 1)
    {
        if (c == null) return "Nobody is selected.";
        if (c.IsSign) return $"{c.Name} is sign on the trail — it is read, not fought.";
        if (c.Down) return $"{c.Name} is down. The fallen take no actions.";
        if (beats <= 0 || c.Beats >= beats) return null;
        return c.Beats == 0
            ? $"{c.Name} has spent all three Beats — the turn is done. ▶ Next turn hands the turn on."
            : $"{c.Name} has {c.Beats} Beat{(c.Beats == 1 ? "" : "s")} left and this costs {beats}.";
    }

    /// <summary>The order the field acts in — and the order the tracker shows it in. One answer to
    /// one question, which is the whole point of it living here.
    ///
    /// <para>It did not, and that was a real fault a Keeper found at the table: the grid sorted
    /// <c>Init desc → souls first → name</c> while <c>NextUp</c> picked <c>Init desc → name</c>, so
    /// the two agreed only until somebody tied. On a d20 with eight on the field a tie is closer to
    /// certain than not, and when it happened the turn jumped to a row that was not the next one
    /// down — the app looked like it was ignoring initiative altogether. Two orderings for one
    /// order is the same bug as two authorities for one number, and this project's standing rule
    /// covers both.</para>
    ///
    /// <para>Souls before foes on a tie is the table convention and the one the grid already
    /// showed, so the display did not move; the turn came to match it. The name is the last
    /// tiebreak and it is ordinal, so the order never wobbles between two identically-rolled
    /// bandits.</para></summary>
    public static IEnumerable<Combatant> InTurnOrder(IEnumerable<Combatant> field)
        => (field ?? Enumerable.Empty<Combatant>())
            .Where(c => c != null)
            .OrderByDescending(c => c.Init)
            .ThenByDescending(c => c.IsPC)
            .ThenBy(c => c.Name, StringComparer.OrdinalIgnoreCase);

    /// <summary>Who is up next: the first in the turn order who has not gone yet. Null when
    /// everyone who could act has, which is the same thing as the round being over — so the app can
    /// keep the round itself rather than asking the Keeper to remember to press a button.</summary>
    public static Combatant NextUp(IEnumerable<Combatant> field)
        => InTurnOrder(field?.Where(CanAct)).FirstOrDefault();

    /// <summary>Is the round spent? Only if somebody could have acted in the first place — an empty
    /// field, or one where everyone is down, is not a round that just ended over and over.</summary>
    public static bool RoundSpent(IEnumerable<Combatant> field)
        => field != null && field.Any(c => !c.IsSign && !c.Dead && (!c.Down || c.Upright))
           && NextUp(field) == null;

    /// <summary>Turn the round over on the whole field: everybody gets their turn back — three
    /// Beats and a clean first Strike — nobody has been handed it yet, the "what just happened"
    /// notes are a clean page, and every Worked effect loses a round. Returns the effects that ran
    /// out, each with who it was on, so the caller can say so by name — an effect that vanishes off
    /// a chip without a word is one the table keeps playing anyway.
    ///
    /// <para>Out here rather than inline in the Tracker for the reason <see cref="ResetForNewFight"/>
    /// is: the round rollover is the spine of the combat loop, and while it sat in UI code no test
    /// could play a fight through it.</para>
    ///
    /// <para><b>The Beats and the MAP step are given back HERE, and that is the whole of a real bug
    /// (v1.39.0).</b> They were handed out by <see cref="Combatant.BeginTurn"/> and by nothing else,
    /// and BeginTurn only runs when a row is stepped through ▶ Next turn. Step the round by hand, or
    /// let it roll over while somebody never got an explicit turn, and that row walked into the new
    /// round still spent: Beats 0, MapStep 4, which is a standing −10 on every Strike it makes for
    /// the rest of the fight. A Keeper reported it as the posse being unable to hit anything, and
    /// the arithmetic bears that out exactly — a level-1 Gunhand at +4 against Defense 13 goes from
    /// hitting three times in five to needing a natural 19, while the dog biting her at +5 off a
    /// clean MapStep 1 hits four times in five. The same zero Beats greys the Work button, so the
    /// same fault reads at the table as the Signs and Miracles having stopped working.</para>
    ///
    /// <para>Ch. XI is not ambiguous about it — "On your turn you have three Beats", and the
    /// Multiple Attack Penalty counts Strikes <em>in a turn</em>. A new round is a new turn for
    /// everyone in it. BeginTurn still does this too, and the two being idempotent is the point:
    /// one route that is remembered and one that is not is how this got out.</para></summary>
    public static List<(Combatant On, WorkedEffect Effect)> NewRound(IEnumerable<Combatant> field)
    {
        var ended = new List<(Combatant, WorkedEffect)>();
        if (field == null) return ended;
        foreach (var c in field)
        {
            if (c == null) continue;
            c.Acting = false; c.HasActed = false; c.ClearLast();
            // The turn's own currency, back for the new turn. A trace takes no turn and is left
            // alone; the dead are left alone too, so a corpse on the field never reads as a row
            // with three Beats waiting to be spent.
            if (!c.IsSign && !c.Dead) { c.Beats = 3; c.MapStep = 1; }
            foreach (var done in c.TickWorked()) ended.Add((c, done));
        }
        return ended;
    }

    /// <summary>Has the last fight left anything on this one that <see cref="ResetForNewFight"/>
    /// would clear — a condition, spent Beats, a MAP step, a turn in progress or already taken, the
    /// "what just happened" note, or something still working on them?
    ///
    /// <para>The pair exists so the two can never disagree, and it exists because they did. New
    /// fight asked only "are there foes, sign on the trail, or worked effects?" and then ran a reset
    /// that clears six more things than that. Take the last foe off by hand — which is what a
    /// Keeper does when the thing dies — and the button answered "nothing to clear" and left the
    /// posse Frightened, out of Beats and mid-turn walking into the next fight. From the outside
    /// that is a button that does nothing, and it was reported as one. Same class as the v1.24.2
    /// escape: a guard that undercounts what a fight leaves behind.</para></summary>
    /// <para>Bleed, Stable and DeathAt are deliberately NOT in this inventory, and neither is the
    /// reset below. They are Blood, and Blood carries between fights by design — a soul on the
    /// ground with a count running is still on the ground when the shooting stops, and "New fight"
    /// must not quietly make them well. <see cref="Combatant.Upright"/> IS here, because refusing to
    /// fall buys one round and the round is over.</para>
    public static bool FightResidue(Combatant c)
        => c != null && (!string.IsNullOrWhiteSpace(c.Conditions) || c.Beats != 3 || c.MapStep != 1
            || c.Acting || c.HasActed || c.Upright || c.LastDelta != 0 || !string.IsNullOrEmpty(c.LastNote)
            || c.Worked is { Count: > 0 });

    /// <summary>Is there anything of the last fight still on the field? <see cref="FightResidue"/>
    /// over everyone standing on it.</summary>
    public static bool AnyFightResidue(IEnumerable<Combatant> field)
        => field != null && field.Any(FightResidue);

    /// <summary>Wipe everything the last fight left on a survivor: conditions, spent Beats, position
    /// in the order, and every Sign or Miracle still working on them. Blood is deliberately NOT
    /// touched — wounds carry between fights, and the Posse tab's Rest is what heals them.
    ///
    /// This lives here rather than inline in the Tracker because it is the exact seam a bug walked
    /// through: New fight was written before Worked effects and the sign strip existed, and being UI
    /// code no test could reach it, so it silently stopped resetting everything a fight leaves
    /// behind. Out here the smoke suite holds it to its word.</summary>
    public static void ResetForNewFight(IEnumerable<Combatant> survivors)
    {
        if (survivors == null) return;
        foreach (var c in survivors)
        {
            if (c == null) continue;
            c.Conditions = ""; c.Beats = 3; c.MapStep = 1;
            c.Acting = false; c.HasActed = false; c.Upright = false;
            c.ClearLast();
            foreach (var w in c.Worked.ToList()) c.Unwork(w);
        }
    }

    // ---- what a Sign or a Miracle costs to work (Player's Book Ch. XIII and Ch. VI) ----

    /// <summary>The price of working one, pulled apart from the line the book prints. Signs are paid
    /// in Nerve, Miracles from the Calling's Faith pool, and a few of the worst ask for Blood or a
    /// point of Mark on top. <paramref name="OrBlood"/> carries the one alternative the book offers
    /// ("3 Nerve or 6 Blood") rather than flattening it away.</summary>
    public record PowerCost(string Time, int Nerve, int Faith, int Blood, int Mark, int OrBlood, string Save)
    {
        /// <summary>Does working this ask anything a soul has to actually spend?</summary>
        public bool Spends => Nerve > 0 || Faith > 0 || Blood > 0 || Mark > 0;
        public bool HasSave => !string.IsNullOrEmpty(Save);
    }

    /// <summary>Read a printed cost line — "1 Beat · 2 Nerve · Will save" — into what it actually
    /// takes. Everything is optional and the order is the book's, so an unparseable line yields a
    /// cost of nothing rather than throwing at the table: the Keeper still sees the printed string.
    /// </summary>
    public static PowerCost ParseCost(string cost)
    {
        string time = ""; int nerve = 0, faith = 0, blood = 0, mark = 0, orBlood = 0; string save = "";
        foreach (var raw in (cost ?? "").Split('·', StringSplitOptions.RemoveEmptyEntries))
        {
            string seg = raw.Trim();
            if (seg.Length == 0) continue;

            var saveM = System.Text.RegularExpressions.Regex.Match(seg, @"^(Will|Fortitude|Reflex)\s+save$",
                System.Text.RegularExpressions.RegexOptions.IgnoreCase);
            if (saveM.Success) { save = saveM.Groups[1].Value; continue; }

            // "5 Nerve and 1 Mark", "3 Nerve or 6 Blood", "2 Faith" — every number-and-currency pair
            // in the segment, with "or" remembered so the alternative isn't silently charged as well.
            var pairs = System.Text.RegularExpressions.Regex.Matches(seg, @"(\d+)\s*(Nerve|Faith|Blood|Mark)",
                System.Text.RegularExpressions.RegexOptions.IgnoreCase);
            if (pairs.Count == 0) { if (time.Length == 0) time = seg; continue; }

            bool alternative = seg.Contains(" or ", StringComparison.OrdinalIgnoreCase);
            for (int i = 0; i < pairs.Count; i++)
            {
                int n = int.Parse(pairs[i].Groups[1].Value);
                string what = pairs[i].Groups[2].Value.ToLowerInvariant();
                // In "3 Nerve or 6 Blood" the FIRST is the price and the second the way out.
                if (alternative && i > 0) { if (what == "blood") orBlood = n; continue; }
                switch (what)
                {
                    case "nerve": nerve += n; break;
                    case "faith": faith += n; break;
                    case "blood": blood += n; break;
                    case "mark":  mark  += n; break;
                }
            }
        }
        return new PowerCost(time, nerve, faith, blood, mark, orBlood, save);
    }

    // ---- what a working actually DOES (Ch. XIII, Ch. VI, and every creature's special line) ----

    /// <summary>Who or what a working lands on. The tracker asked one question — "on whom?" — and
    /// offered one combatant or the whole field, which fits perhaps half of the eighty workings in
    /// the two chapters. Witch-Sight is worked on yourself. The Tally is a question put to the dark
    /// and lands on nobody. Ward of the Threshold is chalked across a doorway. Salt &amp; Iron
    /// catches everything within ten feet, friends included, which is not the same as everyone on
    /// the field. Naming the shapes lets the app stop pretending they are one shape.</summary>
    public enum WorkShape
    {
        /// <summary>The worker, and only the worker.</summary>
        Self,
        /// <summary>One creature the worker picks out.</summary>
        OneCreature,
        /// <summary>One willing soul — a companion held, healed, or steadied.</summary>
        Ally,
        /// <summary>Everything inside a radius, which the book prints in feet and does not sort
        /// into friend and foe.</summary>
        Area,
        /// <summary>A doorway, a wall, a camp, a journey, a question put to the dark — something
        /// that is not a combatant at all.</summary>
        Place,
        /// <summary>Another working, not a person: Unmake the Working, and anything like it.</summary>
        Counter,
        /// <summary>Not worked on anybody — something a creature simply IS. Every one of the 150
        /// Bestiary <c>special</c> lines is written this way ("Does not stop. Ignores pain, fear,
        /// and being bloodied"), and not one of them carries a die or a save. The dialog used to
        /// ask who a creature's nature was being worked on and how many rounds it would last, which
        /// are both the wrong question about a thing that is simply true of it.</summary>
        Trait,
        /// <summary>The printed text does not say plainly enough to guess. A first-class answer,
        /// deliberately — a wrong shape confidently asserted is worse at the table than an honest
        /// "you tell me", because the Keeper stops reading and trusts it.</summary>
        Unclear,
    }

    /// <summary>When a working stops. Rounds are the only one the old model could hold, so a Sign
    /// that lasts a scene and a Sign that lasts until somebody pulls the nail out both showed up on
    /// the chip as "until it is ended by hand" — true of neither.</summary>
    public enum WorkEnds
    {
        /// <summary>It happens and it is over: damage dealt, a wound closed, a question answered.</summary>
        Instant,
        /// <summary>A counted number of rounds. The tracker ticks these.</summary>
        Rounds,
        /// <summary>Until the worker's next turn.</summary>
        NextTurn,
        /// <summary>For the scene — the book's most common duration, and not a round count.</summary>
        Scene,
        /// <summary>An hour.</summary>
        Hour,
        /// <summary>A day.</summary>
        Day,
        /// <summary>Until dawn. A ward, a vigil, a soul held at the edge.</summary>
        UntilDawn,
        /// <summary>Until something is done about it — the nail pulled, the wound doctored, the
        /// promise kept. Nothing the app can count, and it should not pretend to.</summary>
        UntilEnded,
    }

    /// <summary>One working, read out of the words the book prints. Every facet here is derived from
    /// <see cref="Text"/> rather than stored beside it, which is the same bargain
    /// <see cref="WeaponTraits"/> and <see cref="CreatureAttack"/> already strike: the printed line
    /// stays the single source of truth, the data files do not grow a parallel schema to fall out of
    /// step with, and a re-transcription of the chapter cannot silently disagree with the app.
    ///
    /// The parse INFORMS; it never restricts. Everything it works out is a default the Keeper can
    /// overrule at the dialog, because eighty hand-written English sentences will not all yield to a
    /// reader and the ones that do not are exactly the interesting ones.</summary>
    public record Working(
        string Name, string Kind, int Rank, string Cost, string Text,
        WorkShape Shape, int AreaFeet,
        WorkEnds Ends, int Rounds,
        string Damage, string Ongoing, string Heal, string Nerve,
        bool SaveForHalf, string Save,
        bool DrainsToWorker,
        string Effect, string Backlash)
    {
        /// <summary>Does anything here need dice rolled and applied to somebody?</summary>
        public bool Resolves => Damage.Length > 0 || Heal.Length > 0 || Nerve.Length > 0;

        /// <summary>Is there a Backlash clause printed at all? Every Sign has one; no Miracle does.
        /// </summary>
        public bool HasBacklash => Backlash.Length > 0;

        /// <summary>Does the Backlash actually cost anything? Salt &amp; Iron's reads "None. This is
        /// the kindest Sign in the book, and the weakest" — words a Keeper should still get, and a
        /// warning the app should not raise. The two questions are not the same one, so the text is
        /// kept whole and the warning is asked for separately.</summary>
        public bool BacklashBites => Backlash.Length > 0
            && !Backlash.StartsWith("None", StringComparison.OrdinalIgnoreCase);

        public bool HasSave => Save.Length > 0;

        /// <summary>Who it lands on, in the words a Keeper would use.</summary>
        public string ShapeLine => Shape switch
        {
            WorkShape.Self        => "on the worker",
            WorkShape.OneCreature => "on one creature",
            WorkShape.Ally        => "on one willing soul",
            WorkShape.Area        => AreaFeet > 0 ? $"on everything within {AreaFeet} feet" : "on everything nearby",
            WorkShape.Place       => "on a place, a thing, or nobody at all",
            WorkShape.Counter     => "on another working",
            WorkShape.Trait       => "nothing to target — this is what it IS",
            _                     => "the book does not say plainly — your call",
        };

        /// <summary>Something a creature simply has, rather than something worked on anybody.</summary>
        public bool IsTrait => Shape == WorkShape.Trait;

        /// <summary>How long, in the words the book used.</summary>
        public string EndsLine => Ends switch
        {
            WorkEnds.Instant    => "at once — nothing to carry",
            WorkEnds.Rounds     => $"{Rounds} round" + (Rounds == 1 ? "" : "s"),
            WorkEnds.NextTurn   => "until the worker's next turn",
            WorkEnds.Scene      => "for the scene",
            WorkEnds.Hour       => "for an hour",
            WorkEnds.Day        => "for a day",
            WorkEnds.UntilDawn  => "until dawn",
            _                   => "until something ends it",
        };
    }

    static readonly Dictionary<string, int> SpelledFeet = new(StringComparer.OrdinalIgnoreCase)
    { ["five"]=5, ["ten"]=10, ["fifteen"]=15, ["twenty"]=20, ["thirty"]=30, ["forty"]=40, ["fifty"]=50, ["sixty"]=60, ["hundred"]=100 };

    static string Dice(string text, params string[] patterns)
    {
        foreach (var p in patterns)
        {
            var m = System.Text.RegularExpressions.Regex.Match(text, p,
                System.Text.RegularExpressions.RegexOptions.IgnoreCase);
            if (m.Success) return m.Groups[1].Value.ToLowerInvariant();
        }
        return "";
    }

    static bool Has(string text, string pattern) =>
        System.Text.RegularExpressions.Regex.IsMatch(text, pattern,
            System.Text.RegularExpressions.RegexOptions.IgnoreCase);

    /// <summary>Read a printed working into its parts. <paramref name="workerLevel"/> resolves the
    /// durations the book scales — "a round per two levels" is a real number once you know whose
    /// turn it is, and a chip that said "a round per two levels" would be making the Keeper do the
    /// arithmetic the app exists to do.</summary>
    public static Working ReadWorking(string name, string kind, int rank, string cost, string text, int workerLevel = 1)
    {
        string all = (text ?? "").Trim();

        // Every one of the forty Signs ends on a "Backlash:" clause and not one of the forty
        // Miracles does — which is the two chapters agreeing with the Reference deck's own line
        // that faith does not bite back. It was being buried mid-paragraph in a blob of effect
        // text; it is the half a Keeper needs when the working goes wrong, so it comes out whole.
        string effect = all, backlash = "";
        int bl = all.IndexOf("Backlash:", StringComparison.OrdinalIgnoreCase);
        if (bl >= 0)
        {
            effect = all.Substring(0, bl).Trim();
            backlash = all.Substring(bl + "Backlash:".Length).Trim();
        }

        var pc = ParseCost(cost);

        // --- the radius, where the book prints one ---
        int feet = 0;
        var ft = System.Text.RegularExpressions.Regex.Match(effect, @"within\s+(\w+)\s+feet",
            System.Text.RegularExpressions.RegexOptions.IgnoreCase);
        if (ft.Success)
        {
            string n = ft.Groups[1].Value;
            if (!int.TryParse(n, out feet) && SpelledFeet.TryGetValue(n, out int spelled)) feet = spelled;
        }

        // --- dice, in the order that keeps them from stealing each other ---
        // Nerve first: "restore 1d6 of their Nerve" and "buy 1d6 Nerve" both read as damage to a
        // pattern that only looks for a number and a die. Healing next, for the same reason —
        // "heal a touched ally 2d6" is not 2d6 taken off anybody, and a mending Miracle scored as
        // damage is the worst single thing this reader could get wrong.
        string nerve = Dice(effect, @"(\d+d\d+)\s+(?:of\s+(?:their|your|his|her)\s+)?Nerve", @"Nerve\D{0,12}(\d+d\d+)");
        string heal  = Dice(effect,
            @"(?:heal|treat|mend|knit|poultice)\w*\s+[^.]{0,48}?(\d+d\d+)",
            @"wake\s+with\s+(\d+d\d+)\s+Blood",
            @"(\d+d\d+)\s+Blood\s+back");
        string ongoing = Dice(effect, @"(\d+d\d+)\s+each\s+round");
        // Damage only competes for a die once healing and Nerve have taken theirs. Note the verb
        // list has no bare "for": "Treat a wound for 1d8" is the Green Hand mending somebody, and
        // a lone "for" scored it as a die of damage AND a die of healing at the same time.
        string damage = "";
        if (ongoing.Length == 0 && heal.Length == 0 && nerve.Length == 0)
            damage = Dice(effect, @"(?:takes?|deals?|dealing|suffers?|strikes?\s+for)\s+(?:an\s+extra\s+|an\s+additional\s+|a\s+further\s+)?(\d+d\d+)",
                                  @"extra\s+(\d+d\d+)");
        // A die that is none of the above is still a die the Keeper will want rolled.
        if (damage.Length == 0 && ongoing.Length == 0 && heal.Length == 0 && nerve.Length == 0)
            damage = Dice(effect, @"(\d+d\d+)");

        bool half = Has(effect, @"saves?\s+for\s+half|save\s+for\s+half");
        bool drains = Has(effect, @"gives?\s+half\s+of\s+it\s+to\s+you|and\s+gives\s+half|takes?\s+.{0,24}\s+from\s+.{0,30}\s+and\s+gives");

        // --- how long ---
        // Ordered most specific first: "a round per two levels" has to beat the bare "round", and
        // "until dawn" has to beat the general "until".
        WorkEnds ends; int rounds = 0;
        if (Has(effect, @"rounds?\s+per\s+two\s+levels"))
        { ends = WorkEnds.Rounds; rounds = Math.Max(1, workerLevel / 2); }
        else if (Has(effect, @"until\s+(?:your|their|the worker's)\s+next\s+turn")) ends = WorkEnds.NextTurn;
        else if (Has(effect, @"until\s+(?:dawn|sunrise|morning)")) ends = WorkEnds.UntilDawn;
        else if (Has(effect, @"for\s+one\s+night|for\s+a\s+night|that\s+night\b")) ends = WorkEnds.UntilDawn;
        // "until it is doctored" beats "this scene" on purpose. Rot the Wound reads "A wound you
        // dealt this scene will not close … until it is doctored, bound, or dead" — the scene is
        // when the wound was made, not when the Sign lets go, and taking the first phrase that
        // matched put it off the field a scene early.
        else if (Has(effect, @"until\s+it\s+is|until\s+the\s+\w+\s+is|until\s+they|cannot\s+be\s+taken\s+back")) ends = WorkEnds.UntilEnded;
        else if (Has(effect, @"for\s+(?:a|the|this)\s+scene|for\s+the\s+scene|this\s+scene|the\s+scene\s+ends")) ends = WorkEnds.Scene;
        else if (Has(effect, @"for\s+(?:an|one)\s+hour|lasting\s+an\s+hour|lasts?\s+an\s+hour")) ends = WorkEnds.Hour;
        else if (Has(effect, @"for\s+the\s+next\s+day|for\s+a\s+(?:full\s+)?day")) ends = WorkEnds.Day;
        else
        {
            var rd = System.Text.RegularExpressions.Regex.Match(effect, @"(?:for\s+)?(?:one|two|three|\d+)\s+rounds?",
                System.Text.RegularExpressions.RegexOptions.IgnoreCase);
            if (rd.Success)
            {
                ends = WorkEnds.Rounds;
                rounds = rd.Value.Contains("one", StringComparison.OrdinalIgnoreCase) ? 1
                       : rd.Value.Contains("two", StringComparison.OrdinalIgnoreCase) ? 2
                       : rd.Value.Contains("three", StringComparison.OrdinalIgnoreCase) ? 3
                       : int.TryParse(System.Text.RegularExpressions.Regex.Match(rd.Value, @"\d+").Value, out int r) ? r : 1;
            }
            // Nothing said how long, so: dice and no duration is a thing that happens and is over.
            else ends = (damage.Length > 0 || heal.Length > 0 || nerve.Length > 0) && ongoing.Length == 0
                        ? WorkEnds.Instant : WorkEnds.UntilEnded;
        }

        // --- who it lands on ---
        // Strongest signals first, and Unclear rather than a guess when none of them fire. A save
        // in the printed cost is the surest sign there IS somebody else in it: nothing saves
        // against its own worker.
        WorkShape shape;
        // A creature's own line comes off its stat block, and the Bestiary writes those as what a
        // thing IS, never as something it works on somebody: no dice, no save, no radius in any of
        // the 150. So unless this particular line plainly reaches out and touches someone, it is a
        // trait, and the dialog stops asking a question it has no answer to.
        if (string.Equals(kind, "Power", StringComparison.OrdinalIgnoreCase)
            && feet == 0 && !pc.HasSave && damage.Length == 0 && ongoing.Length == 0
            && heal.Length == 0 && nerve.Length == 0)
            shape = WorkShape.Trait;
        else if (feet > 0 || Has(effect, @"\bEach\s+(?:lesser|creature|soul|of them)|Every\s+creature|every\s+ally|every\s+uncanny|\bAllies\s+who|the\s+party\b|in\s+the\s+camp\b"))
            shape = WorkShape.Area;
        else if (Has(effect, @"another'?s?\s+Sign|End\s+another|their\s+Sign\s+DC|unmakes\s+the\s+lower"))
            shape = WorkShape.Counter;
        else if (Has(effect, @"your\s+familiar|year\s+of\s+your\s+own\s+life|\byou\s+work\b|as\s+though\s+you\s+were|wear\s+it\s+for"))
            shape = WorkShape.Self;
        else if (Has(effect, @"across\s+a\s+doorway|on\s+a\s+wall|Lay\s+your\s+palm|Ask\s+the\s+dark|Put\s+a\s+question|Bless\s+a\s+journey|out\s+of\s+the\s+dark|wherever\s+they\s+are|the\s+ground\s+splits|that\s+country|\ba\s+house\b|(?:its|that)\s+roof|a\s+place\s+is|into\s+a\s+(?:cord|draught)|Call\s+up\b|the\s+weather\b|upon\s+a\s+place|a\s+grave\b|patch\s+of\s+ground|Sanctify|spirits\s+of\s+(?:a|that)\s+(?:place|ground)|ammunition|Undo\s+one"))
            shape = WorkShape.Place;
        else if (Has(effect, @"\bally\b|\ballies\b|companion|another\s+soul|\ba\s+soul\b|one\s+soul\s+who|(?:wounded|hurt|mortally\s+hurt)\s+soul|their\s+Frightened|a\s+dying\b|the\s+dying\b|Take\s+an\s+ally"))
            shape = WorkShape.Ally;
        else if (pc.HasSave || Has(effect, @"One\s+living\s+creature|\ba\s+creature\b|Name\s+a\s+creature|one\s+creature|Point\s+and\s+name|the\s+creature\b|\ba\s+thing\b"))
            shape = WorkShape.OneCreature;
        else if (Has(effect, @"\byou\s+(?:see|are|arrive|wear|speak|hold|take)\b|off\s+you\b|your\s+own\s+arm|your\s+hand|at\s+your\s+word|Wear\s+the\s+face|buy\s+\d+d\d+\s+Nerve"))
            shape = WorkShape.Self;
        // A working that mends is a working somebody stands still for. When nothing else in the
        // text said who, healing dice are the tell — better than shrugging.
        else if (heal.Length > 0) shape = WorkShape.Ally;
        else shape = WorkShape.Unclear;

        return new Working(name ?? "", kind ?? "Sign", rank, cost ?? "", all,
            shape, feet, ends, rounds,
            damage, ongoing, heal, nerve,
            half, pc.Save ?? "", drains,
            effect, backlash);
    }

    /// <summary>A creature's power, pulled off its Bestiary <c>special</c> line. Every one of the
    /// 150 entries is written "Short name. What it does.", so the lead phrase is the name and the
    /// rest is the effect. A line that doesn't follow it still yields one power, named by its own
    /// opening words, rather than nothing.</summary>
    public static (string name, string effect) ParsePower(string special)
    {
        string s = (special ?? "").Trim();
        if (s.Length == 0) return ("", "");
        int stop = s.IndexOf(". ", StringComparison.Ordinal);
        if (stop <= 0 || stop > 60)
        {
            // No lead-in: name it by its first few words so the chip still says something.
            var words = s.Split(' ');
            string lead = string.Join(" ", words.Take(Math.Min(4, words.Length))).TrimEnd(',', '.', ';');
            return (lead, s);
        }
        return (s.Substring(0, stop).Trim(), s.Substring(stop + 2).Trim());
    }

    public static (int cost, string role, bool spoor) Cost(int creatureTier, int partyLevel)
    {
        int pt = PartyTier(partyLevel);
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

// ============================================================ WHERE THE TABLE LIVES
/// <summary>The one folder GritKeeper writes a Keeper's own things into — the session, the
/// preferences, and the two files that exist to rescue a session that went wrong.
///
/// It used to be "beside the exe", full stop, which is a fine answer for a single-file portable
/// app and a terrible one the moment the exe's folder is BUILD OUTPUT. `package.ps1` clears the
/// runtime files out of <c>GritKeeper\app\</c> on every release — it has to, or a download ships
/// carrying the packager's own table — and a Keeper who plays out of that folder, which is the
/// obvious thing to do since the exe is right there, loses everything the first time anyone cuts
/// a release. That happened on 2026-08-01.
///
/// So the folder is RESOLVED rather than assumed, in this order:
///
/// <list type="number">
/// <item>A <c>portable.txt</c> beside the exe — an explicit "keep my things here", for a copy on
///   a USB stick carried to somebody else's table. Nothing is written to their machine.</item>
/// <item>An existing <c>session.json</c> beside the exe — someone is already using this folder as
///   their table and it is not this code's place to move them off it silently.</item>
/// <item>Otherwise <c>%APPDATA%\GritKeeper\</c>, which no build, publish or package step can
///   reach. This is the answer nearly everyone gets, and it is the one that cannot lose a table.</item>
/// </list>
///
/// The single-file promise is untouched: the exe still needs nothing beside it, and rule 1 means
/// it can still be carried on a stick with its table. What changed is only where a plain
/// double-click keeps things.</summary>
public static class AppState
{
    /// <summary>Drop this beside the exe to pin the state to the exe's own folder.</summary>
    public const string PortableMarker = "portable.txt";

    /// <summary>Which folder wins, given only what exists on disk. Pure and separated from the
    /// filesystem so the smoke rig can walk every combination without creating any of it — the
    /// order below decides whether a Keeper's campaign is found or silently abandoned, which is
    /// not something to leave to a first run on somebody's machine.</summary>
    /// <param name="besideExe">The exe's own folder.</param>
    /// <param name="appData">The per-user folder.</param>
    /// <param name="hasPortableMarker">Is there a portable.txt beside the exe?</param>
    /// <param name="hasSessionBesideExe">Is there already a session.json beside the exe?</param>
    public static string Resolve(string besideExe, string appData, bool hasPortableMarker, bool hasSessionBesideExe)
        => hasPortableMarker || hasSessionBesideExe ? besideExe : appData;

    static string _dir;

    /// <summary>The resolved folder, worked out once per run and created if it is missing.
    /// Falls back to the exe's own folder if the per-user folder cannot be made — a Keeper with a
    /// locked-down profile should still get an app that runs, not one that refuses to start.</summary>
    public static string Dir
    {
        get
        {
            if (_dir != null) return _dir;
            string beside = AppContext.BaseDirectory;
            try
            {
                string appData = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "GritKeeper");
                _dir = Resolve(beside, appData,
                    File.Exists(Path.Combine(beside, PortableMarker)),
                    File.Exists(Path.Combine(beside, "session.json")));
                Directory.CreateDirectory(_dir);
            }
            catch { _dir = beside; }
            return _dir;
        }
    }

    /// <summary>Point the state somewhere else. For the smoke rig and for --selftest, so neither
    /// writes into a real Keeper's folder while it works.</summary>
    public static void UseForTesting(string dir) => _dir = dir;
}

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

    // The JSON data is EMBEDDED in THIS assembly — the rules library, the one that also holds
    // Db — so the published exe is a TRUE single-file standalone (one .exe, no Data/ folder
    // beside it) and the smoke rig reads the same bytes without anything being copied next to
    // it. Note the resource lookup below keys off typeof(Db).Assembly, which is what pins the
    // JSON to this project: embed it anywhere else and this silently finds nothing.
    // The on-disk fallback is a courtesy for a host that wants to override the data without
    // rebuilding; neither the app nor the smoke rig relies on it any more.
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

    /// <summary>The same pick off a stream the caller owns. A generator that reaches for the
    /// ambient <see cref="Rules.Rng"/> cannot be reproduced from a seed no matter what else it
    /// does — <see cref="RollAdventure"/> seeded its namer and its monster and stayed unrepeatable
    /// until every table read came through here too.</summary>
    public static string Pick(Random rng, string table)
    {
        var l = Simple[table];
        return l[rng.Next(l.Count)];
    }

    public static Creature Find(string name) =>
        Creatures.FirstOrDefault(c => c.name.Equals(name, StringComparison.OrdinalIgnoreCase));

    /// <summary>Pick a table entry that isn't <paramref name="notThis"/>, so an adventure never
    /// rolls the same line into two of its slots and reads like the dice got stuck. Gives up after
    /// a few tries rather than looping forever on a one-entry table.</summary>
    static string PickDistinct(Random rng, string table, params string[] notThis)
    {
        for (int i = 0; i < 12; i++)
        {
            var s = Pick(rng, table);
            if (!notThis.Contains(s)) return s;
        }
        return Pick(rng, table);
    }

    /// <summary>Roll a whole adventure rather than one more line off one more table.
    ///
    /// The variety is deliberately multiplicative and the parts are rolled independently, because
    /// that is what makes the same monster read as a different job twice: a Wendigo that is
    /// <i>collecting, and there is a list</i> is not the Wendigo that <i>only takes what is freely
    /// given</i>. The trouble comes out of the Bestiary rather than a table of adjectives, so what
    /// gets rolled is a thing with a stat block the Keeper can put straight on the Tracker.</summary>
    /// <param name="partyLevel">Used to keep the trouble in the posse's weight class. 0 or less
    /// takes the whole Bestiary, which is what "surprise me, and God help them" looks like.</param>
    /// <param name="seed">Same seed, same adventure — the whole thing, title and town and cast.
    /// 0 draws a fresh one and reports it on <see cref="Adventure.Seed"/>, so an adventure a Keeper
    /// liked can be rolled again rather than remembered. Before 2026-08-09 this rolled off the
    /// ambient <see cref="Rules.Rng"/> and could not be reproduced at all.</param>
    public static Adventure RollAdventure(int partyLevel = 0, int seed = 0)
    {
        if (seed == 0) seed = Rules.Rng.Next(1, int.MaxValue);
        // EVERY draw below comes off this stream. The first cut of this seeded the namer and the
        // monster and left the twelve table reads on the ambient Rules.Rng, so a "seeded" adventure
        // reproduced its title and nothing else — caught by the smoke rig, which is what it is for.
        var rng = new Random(unchecked(seed * 92821 + 17));

        // The town keeps coming off the book's own Ch. XII tables — those are a transcription and
        // stay one. But its words are handed to the namer as already spent, so the title and the
        // cast cannot echo them: "The Salt at Coffin Wells" beside "The Reckoning of the Wells" is
        // exactly the fault this is here to stop.
        var town = $"{Pick(rng, "townFront")} {Pick(rng, "townBack")}";
        var namer = Names.For(seed);
        var stock = Names.Data;
        namer.Reserve(town);

        // Tier-appropriate where possible: the party's own tier, or one either side of it, so the
        // fight is a fight. Falls back to the whole Bestiary rather than returning nothing when a
        // tier is thinly populated — an adventure with no trouble in it is not an adventure.
        var pool = Creatures.AsEnumerable();
        if (partyLevel > 0)
        {
            int tier = Rules.PartyTier(partyLevel);
            var near = Creatures.Where(c => Math.Abs(c.tier - tier) <= 1).ToList();
            if (near.Count > 0) pool = near;
        }
        var list = pool.ToList();
        var beast = list.Count > 0 ? list[rng.Next(list.Count)] : null;

        return new Adventure
        {
            Seed = seed,
            // Was advTitleA x advTitleB — 20 x 20 in ONE shape, so every roll read "The Long Debt",
            // "A Bad Harvest", "The Quiet Verdict". Namer varies the grammar as well as the words.
            Title = namer.Title(stock),
            Shape = Pick(rng, "advShape"),
            Hook = Pick(rng, "advHook"),
            TownName = town,
            Ails = Pick(rng, "townAils"),
            Rumor = Pick(rng, "rumors"),
            Trouble = beast?.name ?? "something the Bestiary has not named",
            TroubleTier = beast?.tier ?? 0,
            Truth = PickDistinct(rng, "advTruth"),
            Turn = Pick(rng, "advTurn"),
            Omen = Pick(rng, "omens"),
            NpcName = namer.Person(stock),
            NpcWant = Pick(rng, "npcWant"),
            NpcTell = Pick(rng, "npcTell"),
            Clock = Pick(rng, "advClock"),
            ClockSegments = 4 + rng.Next(3) * 2,         // 4, 6 or 8 — the app's own clock sizes
            Reward = Pick("advReward"),
            Plunder = Pick("plunder"),
        };
    }
}

/// <summary>One rolled adventure: the parts a Keeper needs before a session and nothing they can
/// look up mid-scene. Kept as data rather than a formatted string so the Generators tab can render
/// it AND hand the pieces to the rest of the app — the town to the Map, the clock to a Thread, the
/// trouble to the Tracker.</summary>
public sealed class Adventure
{
    public string Title = "", Shape = "", Hook = "", TownName = "", Ails = "", Rumor = "";
    public string Trouble = "", Truth = "", Turn = "", Omen = "";
    public string NpcName = "", NpcWant = "", NpcTell = "";
    public string Clock = "", Reward = "", Plunder = "";
    public int ClockSegments = 6;
    public int TroubleTier;
    /// <summary>What to type to get this night back. Rolling is cheap; a Keeper who liked the
    /// third roll and has since made twelve more has no other way to return to it.</summary>
    public int Seed;

    /// <summary>The adventure as the Keeper reads it off the tab. Written in the order it gets used
    /// at the table: what it is and how it arrives, then where, then what is actually true, then the
    /// turn, and only then the bookkeeping.</summary>
    public string Sheet() =>
        $"{Title.ToUpperInvariant()}\n" +
        $"  The shape of it:  {Shape}\n" +
        $"  How it finds you: {Hook}\n" +
        $"\n" +
        $"  Where:            {TownName}\n" +
        $"  What ails it:     {Ails}\n" +
        $"  What they say:    {Rumor}\n" +
        $"\n" +
        $"  The trouble:      {Trouble}{(TroubleTier > 0 ? $"  (Tier {TroubleTier})" : "")}\n" +
        $"  The truth of it:  {Truth}\n" +
        $"  The turn:         {Turn}\n" +
        $"  An omen first:    {Omen}\n" +
        $"\n" +
        // The tell gets its own labelled line rather than a sentence around it: the table is written
        // in bare third person ("Counts things — coins, exits, your party"), so any pronoun put in
        // front of it disagrees with the verb — "they wears something of the child's".
        $"  In the way:       {NpcName} — wants {char.ToLowerInvariant(NpcWant[0])}{NpcWant.Substring(1)}\n" +
        $"  Their tell:       {NpcTell}\n" +
        $"\n" +
        $"  If nobody moves:  {Clock}   [{ClockSegments}-segment clock]\n" +
        $"  What's in it:     {Reward}\n" +
        $"  On the body:      {Plunder}";
}
