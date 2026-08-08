namespace BloodAndGritKeeper;

/// <summary>A running record of what the app just did, for the failure that never throws.
///
/// <para>The two error paths in <c>Program.cs</c> answer "it stopped" — an exception with a stack,
/// written to <c>startup-error.txt</c> or <c>BloodAndGrit-last-error.txt</c>. Neither answers the
/// other kind of report, which is the one a table actually makes: <i>it gave my Padre the wrong
/// Grace</i>, <i>that roll can't have been a 3</i>, <i>the tracker lost somebody</i>. Nothing threw,
/// so there is no file, and the smoke suite only catches what somebody thought to assert. The
/// daybook is the missing half: the last few hundred things that happened, kept in memory, written
/// out when there is a reason to.</para>
///
/// <para><b>Inert until opened, on purpose.</b> The rules library is what the smoke rig fuzzes —
/// <c>RollExprFull</c> and <c>Generate</c> run thousands of times per build — and a recorder that
/// is always on would build and discard a string on every one of them for nobody's benefit.
/// <c>Program.cs</c> opens it at launch, so the app always records and the library stays silent
/// unless told otherwise.</para>
///
/// <para><b>Everything here fails soft.</b> A diagnostic that can take the table down is worse than
/// no diagnostic at all, so a write that throws drops the mirror and keeps going rather than
/// surfacing. The ring is capped, so a long evening cannot grow it without bound.</para></summary>
public static class Daybook
{
    /// <summary>How many entries the daybook keeps. Sized for "what just happened" — the last few
    /// minutes of a session at table pace — not for an audit trail. Four hundred lines is a couple
    /// of pages of text and comfortably covers a fight.</summary>
    public const int Cap = 400;

    static readonly Queue<string> Ring = new(Cap + 1);
    static readonly object Gate = new();
    static string mirror;                 // --verbose: the file every entry is also appended to
    static int dropped;                   // entries pushed out of the ring, for the dump's header

    /// <summary>Is the daybook recording? False in the smoke rig and anywhere else that has not
    /// asked for it.</summary>
    public static bool On { get; private set; }

    /// <summary>How many entries are held right now. Never above <see cref="Cap"/>.</summary>
    public static int Count { get { lock (Gate) return Ring.Count; } }

    /// <summary>Start recording. Pass a path to also append every entry to disk as it happens
    /// (<c>--verbose</c>) — worth it when chasing something that takes the process down before
    /// anything gets a chance to write the ring out.</summary>
    public static void Open(string mirrorPath = null)
    {
        lock (Gate)
        {
            On = true;
            mirror = string.IsNullOrWhiteSpace(mirrorPath) ? null : mirrorPath;
        }
    }

    /// <summary>Stop recording and forget everything. Exists for the smoke rig, which asserts
    /// against a known-empty daybook and must not leave one open for the sweeps that follow.</summary>
    public static void Close()
    {
        lock (Gate)
        {
            On = false;
            mirror = null;
            Ring.Clear();
            dropped = 0;
        }
    }

    /// <summary>Record one thing that happened. <paramref name="channel"/> is a short tag the eye
    /// can scan a column of — <c>roll</c>, <c>session</c>, <c>mode</c>, <c>soul</c>, <c>error</c>.
    /// Costs nothing when the daybook is closed, which is the common case in the rules library.</summary>
    public static void Note(string channel, string what)
    {
        if (!On) return;
        string line = $"{DateTime.Now:HH:mm:ss.fff}  {channel,-8} {what}";
        string toMirror;
        lock (Gate)
        {
            Ring.Enqueue(line);
            while (Ring.Count > Cap) { Ring.Dequeue(); dropped++; }
            toMirror = mirror;
        }
        if (toMirror == null) return;
        try
        {
            File.AppendAllText(toMirror, line + Environment.NewLine);
        }
        catch
        {
            // The mirror is a convenience; the ring is the record. A locked or unwritable file
            // drops the mirror once rather than throwing on every entry for the rest of the night.
            lock (Gate) mirror = null;
        }
    }

    /// <summary>The daybook as text, oldest first, headed by what it holds. Says so plainly when
    /// it is closed or empty — a report that reads as blank invites the reader to assume nothing
    /// happened, when the truth is that nobody was writing it down.</summary>
    public static string Dump()
    {
        string[] lines;
        int lost;
        bool on;
        lock (Gate) { lines = Ring.ToArray(); lost = dropped; on = On; }

        var sb = new System.Text.StringBuilder();
        if (!on)
        {
            sb.AppendLine("-- daybook: not recording --");
            return sb.ToString();
        }
        sb.AppendLine($"-- daybook: the last {lines.Length} of {lines.Length + lost} entries"
                      + (lost > 0 ? $" ({lost} older dropped; it keeps {Cap}) --" : " --"));
        foreach (var l in lines) sb.AppendLine(l);
        return sb.ToString();
    }

    /// <summary>Write the daybook to a file. Returns whether it landed — the caller decides what to
    /// say about it, and every caller here has somewhere better to put a failure than a throw.</summary>
    public static bool Save(string path)
    {
        try
        {
            File.WriteAllText(path, Dump());
            return true;
        }
        catch
        {
            return false;
        }
    }
}
