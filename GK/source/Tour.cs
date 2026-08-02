using System.Drawing.Drawing2D;

namespace BloodAndGritKeeper;

// ============================================================ THE GUIDED TOUR
//
// A walkthrough that points at the real thing. Every step names a control the app actually built,
// brings its tab to the front, and floats a callout beside it with a little pointer aimed at it —
// so what is being described and what is on screen are never two different objects.
//
// Three rules it keeps, all learned from tours that are worse than nothing:
//
//   1. It ASKS FIRST and it takes no for an answer. The offer is a real choice with a real
//      decline, the decline is remembered (Prefs.ToldTheTour), and it never asks again. Help ▸
//      Show me around brings it back for anyone who changes their mind.
//   2. It is MODELESS and it does not trap you. The callout is a floating owned window, not a
//      modal — the app underneath stays live, so a Keeper can poke the thing being described
//      while it is being described. Esc, the ✕, and Finish all end it at once.
//   3. It follows the MODE. A player's table has three tabs, so a player's tour has the steps
//      that belong to those three and no others. Being walked through a Bestiary you cannot open
//      is how a tutorial teaches somebody that the app is not for them.
//
// A step whose control has gone (a lazily-built tab that has never been realized, a mode that
// hides it) is skipped rather than pointed at nothing. That is why every step resolves its
// control through a Func at display time instead of holding a reference from construction.
/// <summary>One stop on the tour: which tab to bring up, which control to point at (resolved when
/// the step is reached, because tabs are built lazily and a control that does not exist yet cannot
/// be handed over at construction), and what to say about it.</summary>
internal sealed record TourStop(string Tab, Func<Control> Target, string Title, string Body);

public partial class MainForm
{
    TourCallout tourWindow;

    /// <summary>The first-launch offer. A choice, not an announcement: the tour is the default
    /// button because somebody opening this for the first time usually does want the tour, but
    /// declining is one click and is remembered forever.</summary>
    internal void OfferTourOnFirstRun()
    {
        var prefs = Prefs.Load();
        if (prefs.ToldTheTour) return;

        using var f = new Sheet
        {
            Text = "Welcome to GritKeeper", Width = 520, Height = 268,
            FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent,
            MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper
        };
        var head = new Label
        {
            Left = 20, Top = 18, Width = 464, Height = 30, ForeColor = Blood,
            Font = new Font("Segoe UI", 13f, FontStyle.Bold), Text = "First time at this table?"
        };
        var body = new Label
        {
            Left = 20, Top = 54, Width = 464, Height = 92, ForeColor = Ink,
            Text = "There is a lot in here, and none of it is worth hunting for. I can walk you "
                 + "round the whole app — a few lines at each thing, pointing at the real button, "
                 + "with the app still live underneath so you can try it as we go.\n\n"
                 + "It takes about three minutes. Esc stops it anywhere."
        };
        var again = new Label
        {
            Left = 20, Top = 150, Width = 464, Height = 20, ForeColor = Gold,
            Font = new Font("Segoe UI", 9f, FontStyle.Italic),
            Text = "Either way, it is under Help ▸ Show me around whenever you want it."
        };
        var yes = new Button { Text = "Show me around", Left = 232, Top = 186, Width = 130, Height = 32, DialogResult = DialogResult.Yes };
        var no = new Button { Text = "No thanks", Left = 372, Top = 186, Width = 112, Height = 32, DialogResult = DialogResult.No };
        f.Controls.AddRange(new Control[] { head, body, again, yes, no });
        f.AcceptButton = yes; f.CancelButton = no;

        var answer = f.ShowDialog(this);

        // Remembered either way. Asked once is a welcome; asked every launch is a nag.
        prefs.ToldTheTour = true;
        Prefs.Save(prefs);

        if (answer == DialogResult.Yes) StartTour();
        else Log("Tour skipped — Help ▸ Show me around brings it back.");
    }

    /// <summary>The stops, in the order a night actually goes: sit the posse down, learn to roll,
    /// find out what is out there, weigh it, fight it, and keep the record. Only the ones whose tab
    /// this mode shows are used.</summary>
    List<TourStop> TourStops() => new()
    {
        // Tab is null so this one survives every mode — the opening stop is the orientation, and a
        // player's tour losing it (because it was pinned to a tab a player has not got) would open
        // on "Roll anything" with nothing to say where they are. The count and the shortcut line
        // are read off the tabs actually on show, for the same reason.
        new(null, () => tabsCtl, Mode == RunMode.Player ? "Your side of the table" : "The tabs, left to right",
            Mode == RunMode.Player
              ? $"You have {tabsCtl.TabPages.Count} tabs: make and run your own character, roll your own "
                + "dice, and look up any rule. The Keeper's side of the app is put away — you can bring "
                + "it back any time from the Table menu if you end up running the game yourself.\n\n"
                + $"Ctrl+1 to Ctrl+{tabsCtl.TabPages.Count} jump straight to them."
              : "The bar across the top is the whole app, and it runs roughly in the order a night "
                + "does — seat the posse, roll the dice, look up a horror, weigh the fight, run it, "
                + "and keep the record. Ctrl+1 to Ctrl+0 jump straight to any of them."),

        new("Posse", () => posseGrid, "The posse sheet",
            "Every soul at the table, with Blood, Defense, saves, Nerve, Grit, the Mark and the "
            + "Taint. Click straight into a cell to edit it. Double-click a soul to open their "
            + "Ledger — the book's own character sheet — in its own window, and right-click any "
            + "row for everything that can be done to them.\n\nThe six ready-made souls from "
            + "Appendix D are already seated, so you can play tonight without making anybody."),

        new("Dice", () => exprBox, "Roll anything",
            "Type an expression — 2d6+3, or 1d8+1d6+2 — and press Enter. Or punch it in with the "
            + "keypad below: each +d button stacks that die, the digits build the modifier. The "
            + "dice tumble in the tray and land on the true result, and everything the app rolls "
            + "anywhere lands in the log on the right."),

        new("Bestiary", () => beastList, "All 150 creatures, word for word",
            "Taken straight out of the Bestiary — lore, stat block, witness quotes and all. Search "
            + "by name, filter by Tier or chapter. Double-click one to pop it out into its own "
            + "window so several horrors can sit side by side, and send it to the Encounter or "
            + "straight onto the Tracker from here."),

        new("Encounter", () => encPick, "Weigh the fight before you run it",
            "Pick creatures here — each line shows its Tier, which is what the whole cost is "
            + "reckoned from — and the bar at the bottom says whether what you have built is fair, "
            + "mean, or a massacre against your posse's level. The book's own budget: four points "
            + "a soul, an even foe 4, a mook 1, a standout 8.\n\nHappy with the odds? Send all → "
            + "Tracker and run it."),

        new("Tracker", () => trkGrid, "The fight itself",
            "Initiative, Blood, conditions, and whose turn it is. Rows are colour-coded — green "
            + "for the posse, rust for foes, gold for whoever is up, red for the downed — and the "
            + "ones who have already gone this round are faded, so what is left to do is something "
            + "you see rather than something you remember.\n\nThe columns marked ✎ are the ones "
            + "you can type into."),

        new("Tracker", () => trkGrid, "One button, over and over",
            "▶ Next turn is the loop. It hands the turn to whoever is up next by initiative, "
            + "carries the selection with it, and rolls the round over by itself when the field "
            + "has all gone — so you never advance a counter by hand.\n\nStrike, Dread and ✦ Work "
            + "then act on whoever is up. Strike runs the whole Iron Code: to-hit, the four "
            + "degrees, the multiple-attack penalty, the Fatal die, and damage after armour."),

        new("Tracker", () => trkGrid, "Signs, Miracles, and what a creature is",
            "✦ Work reads the printed rule and does what it says: who it lands on (yourself, one "
            + "creature, a companion, everything within ten feet, or a place that is nobody at "
            + "all), how long it holds, and the dice it rolls — and it can roll and apply them "
            + "for you. Every Sign's Backlash gets its own line, in red, because that is the half "
            + "you need when it goes wrong.\n\nWhat is working on somebody shows as chips in the "
            + "Worked column. Hover one for the whole of it."),

        new("Generators", () => genOut, "When the party goes somewhere you did not prepare",
            "Every rollable table from The Country in Your Pocket, plus all nine Grounds and the "
            + "villain picker. A town in three rolls, a city in four, a stranger with a face and a "
            + "want, a rumour, a thing on the trail. The safe-table rule is applied for you, so "
            + "nothing walks out of a table that the posse has no business meeting yet."),

        new("Map", () => tabsCtl, "Trail maps, drawn to a number",
            "A procedural survey of any of the nine Grounds at any scale from a gunfight to weeks "
            + "of trail. The same number and settings always draw the same map, so note the N° and "
            + "you can have it back. Drop markers for the posse and the foes, drag the landmarks "
            + "where you want them, and export to SVG or a one-page PDF."),

        new("New Soul", () => tabsCtl, "Make a character, strictly by the book",
            "🎲 Make a soul rolls a complete character at any level, all eight of Chapter III's "
            + "steps. 🧭 Wizard… walks you through every choice yourself, each list filtered to "
            + "what the book actually allows. Either way the sheet is re-derived and checked "
            + "against the rules before you ever see it, and ✎ Tweak lets you change anything "
            + "after — the Ledger notes it was hand-tweaked rather than arguing with you."),

        new("Reference", () => referencePage, "The rules at your elbow",
            "A Keeper's screen you turn with ◀ ▶ or the Left and Right arrow keys: the four "
            + "degrees, the DC ladder, the Iron Code, wounds, every condition, Nerve and Dread, "
            + "the Mark and the Taint, Signs, Miracles, and the book's own arms, goods and skills "
            + "tables.\n\nWhen a ruling is needed and the book is across the room, it is here."),

        new("Session", () => clockPanel, "Keep the record",
            "Notes for the night — Stamp the date starts each session's entry — and threads with "
            + "clocks beside them. A thread is trouble on its way: name it, give it four, six or "
            + "eight segments, and tick it forward when the world moves toward it. When the last "
            + "segment fills, it comes due."),

        new(null, () => null, "That is the whole of it",
            "The table auto-saves beside the app on exit and every five minutes, and reloads when "
            + "you come back — you never have to think about it.\n\nEverything else is one hover "
            + "away: every button carries a tooltip, and every list has a right-click menu. F1 "
            + "opens the five-minute lesson, and Help ▸ Show me around runs this again.\n\nGo on, "
            + "then. Something is out there."),
    };

    /// <summary>Run the tour from the top. Safe to call twice — an open one is closed first, so
    /// Help ▸ Show me around during a tour restarts it rather than stacking two callouts.</summary>
    internal void StartTour()
    {
        tourWindow?.Close();
        var stops = TourStops().Where(s => s.Tab == null || ShowsTab(s.Tab)).ToList();
        if (stops.Count == 0) return;
        tourWindow = new TourCallout(this, stops);
        tourWindow.Show(this);
        Log($"Showing you around — {stops.Count} stops. Esc ends it.");
    }
}

/// <summary>The floating callout. Owned by the main window so it rides above it and closes with
/// it, borderless so it reads as a speech bubble rather than another dialog, and deliberately NOT
/// modal — the whole point is that the app stays usable while it is talking about it.</summary>
// Sheet rather than Form even though this one is borderless and so has no caption to colour: what
// it is really joining is the contents pass, so a control added to the callout later cannot arrive
// wearing the system theme. Chrome's DWM calls on a borderless window are a no-op, which is the
// right outcome and costs one failing HRESULT nobody reads.
sealed class TourCallout : Sheet
{
    readonly MainForm host;
    readonly List<TourStop> stops;
    int at;

    readonly Label titleLbl, bodyLbl, countLbl;
    readonly Button back, next, done;

    internal TourCallout(MainForm owner, List<TourStop> steps)
    {
        host = owner;
        stops = steps;

        FormBorderStyle = FormBorderStyle.None;
        StartPosition = FormStartPosition.Manual;
        ShowInTaskbar = false;
        BackColor = MainForm.Paper;
        Width = 400;
        KeyPreview = true;

        titleLbl = new Label
        {
            Left = Pad, Top = Pad, Width = Width - Pad * 2, Height = 26, ForeColor = MainForm.Blood,
            Font = new Font("Segoe UI", 12f, FontStyle.Bold), UseMnemonic = false
        };
        bodyLbl = new Label
        {
            Left = Pad, Top = titleLbl.Bottom + 4, Width = Width - Pad * 2, AutoSize = false,
            ForeColor = MainForm.Ink, Font = new Font("Segoe UI", 9.75f), UseMnemonic = false
        };
        countLbl = new Label
        {
            Left = Pad, Width = 120, Height = 22, ForeColor = MainForm.Gold,
            Font = new Font("Segoe UI", 9f, FontStyle.Italic), TextAlign = ContentAlignment.MiddleLeft
        };
        back = TourBtn("◀ Back", (s, e) => Go(at - 1), 88, "The stop before this one");
        next = TourBtn("Next ▶", (s, e) => Go(at + 1), 88, "The next stop on the tour");
        done = TourBtn("Finish", (s, e) => Close(), 88,
            "Close the tour — Help ▸ Take the tour brings it back whenever you want it");
        Controls.AddRange(new Control[] { titleLbl, bodyLbl, countLbl, back, next, done });

        // Esc anywhere in the callout ends it. The host also wires Esc, so it works whichever of
        // the two windows has focus — a tour you cannot dismiss from the app you are using is a trap.
        KeyDown += (s, e) => { if (e.KeyCode == Keys.Escape) Close(); };
        Go(0);
    }

    const int Pad = 16;

    /// <summary>The callout's three buttons, built from the app's own <see cref="MainForm.Btn"/>
    /// rather than from a bare <c>Button</c>.
    ///
    /// <para>They were the last <c>FlatStyle.System</c> controls left after v1.33.0 dressed every
    /// bar in the app, and they were the worst place to leave them: this bubble is a borderless
    /// patch of Paper with nothing else on it, so three grey-blue Win32 blocks had no surrounding
    /// chrome to blend into — and it is the FIRST thing a new Keeper sees, since the tour offers
    /// itself on first run. The app's introduction to itself was the one window that did not look
    /// like the app.</para>
    ///
    /// <para>Going through the shared helper rather than restating the flat face here is the point:
    /// a second place that paints a button is a second place for the palette to drift. It also puts
    /// these three inside <c>audit_ui.py</c>'s count, which is why they now carry tooltips.</para>
    ///
    /// <para>The parameter list is <c>Btn</c>'s exactly — <c>(text, onClick, w, tip)</c> — and that
    /// is not decoration. The audit exempts a wrapper from its literal-tooltip rule only when every
    /// argument it passes down is a forwarded parameter, so a helper that hard-codes its width
    /// reads to it as a real button site with no caption to check. Matching the signature is what
    /// lets the audit skip this line and check the three call sites instead.</para></summary>
    static Button TourBtn(string text, EventHandler onClick, int w = 88, string tip = null)
    {
        var b = MainForm.Btn(text, onClick, w, tip);
        // 28, not Btn's 32: the callout is a small bubble and its own measured layout reads this
        // back off `done.Height`, so the row and the form shrink with it.
        b.Height = 28;
        return b;
    }

    // Room reserved on whichever edge the pointer lives, so the triangle is drawn INSIDE the form.
    // A borderless form clips to its own bounds, so a pointer drawn past the edge simply is not
    // there — which is how the first cut had an arrow nobody could see.
    const int Beak = 13;

    void Go(int i)
    {
        at = Math.Clamp(i, 0, stops.Count - 1);
        var stop = stops[at];

        if (stop.Tab != null) host.ShowTab(stop.Tab);

        // Where it will sit decides how much room the beak needs at the top, which decides where
        // the text starts — so the placement is worked out first and the layout follows it.
        Place(stop.Target?.Invoke());

        int top = Pad + (beakUp ? Beak : 0);
        titleLbl.Top = top;
        titleLbl.Text = stop.Title;
        bodyLbl.Top = titleLbl.Bottom + 4;
        bodyLbl.Text = stop.Body;
        // Measured, not laid out to constants: these bodies run from three lines to nine, and a
        // fixed height would clip the long ones and leave a hole under the short ones.
        bodyLbl.Height = TextRenderer.MeasureText(stop.Body, bodyLbl.Font,
            new Size(bodyLbl.Width, int.MaxValue), TextFormatFlags.WordBreak).Height + 6;

        int row = bodyLbl.Bottom + 14;
        countLbl.Top = row + 3;
        countLbl.Text = $"{at + 1} of {stops.Count}";
        done.Left = Width - Pad - done.Width; done.Top = row;
        next.Left = done.Left - next.Width - 6; next.Top = row;
        back.Left = next.Left - back.Width - 6; back.Top = row;
        back.Enabled = at > 0;
        next.Enabled = at < stops.Count - 1;
        done.Text = at == stops.Count - 1 ? "Finish" : "Skip";
        Height = row + done.Height + Pad + (beakUp || !hasBeak ? 0 : Beak);

        // Height changed, so where it sits may have to change with it.
        Place(stop.Target?.Invoke());
        Invalidate();
    }

    bool hasBeak;      // is this stop pointing at anything in particular?
    bool beakUp;       // the callout sits BELOW its control, so the beak is on the top edge
    int beakX;         // where along that edge, in our own coordinates

    /// <summary>Park the callout beside what it is talking about, without covering it and without
    /// walking off the screen. Below the control if there is room under it, above if not, pinned
    /// inside the working area either way — a callout half off the edge of the monitor describes
    /// its control perfectly and cannot be read.
    ///
    /// A control that fills most of the window (the tab control itself, a docked grid) gets no
    /// beak and sits low and centred instead. Pointing at something that big says nothing, and
    /// aiming at its edge shoved the callout into the corner of the screen — which is exactly what
    /// the first version did on the very first stop.</summary>
    void Place(Control target)
    {
        var screen = Screen.FromControl(host).WorkingArea;
        void Loose()
        {
            hasBeak = false;
            Location = new Point(
                Math.Clamp(host.Left + (host.Width - Width) / 2, screen.Left + 8, Math.Max(screen.Left + 8, screen.Right - Width - 8)),
                Math.Clamp(host.Bottom - Height - 56, screen.Top + 8, Math.Max(screen.Top + 8, screen.Bottom - Height - 8)));
        }

        if (target == null || !target.IsHandleCreated || !target.Visible) { Loose(); return; }
        var r = target.RectangleToScreen(target.ClientRectangle);
        if (r.Height > host.Height * 0.55 || r.Width > host.Width * 0.9) { Loose(); return; }

        hasBeak = true;
        int x = Math.Clamp(r.Left + 24, screen.Left + 8, Math.Max(screen.Left + 8, screen.Right - Width - 8));
        int y = r.Bottom + 10;
        beakUp = true;
        if (y + Height > screen.Bottom - 8)
        {
            y = r.Top - Height - 10;
            beakUp = false;
            if (y < screen.Top + 8) { Loose(); return; }
        }
        Location = new Point(x, y);
        beakX = Math.Clamp(r.Left + Math.Min(r.Width / 2, 90) - x, 22, Width - 22);
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        using var pen = new Pen(MainForm.Blood, 2f);
        using var fill = new SolidBrush(MainForm.Paper);
        g.DrawRectangle(pen, new Rectangle(0, 0, Width - 1, Height - 1));

        if (!hasBeak) return;
        // A solid arrowhead in the strip reserved on whichever edge faces the control. Drawn as a
        // filled mark rather than as a bubble's tail, because a borderless form clips to its own
        // bounds — a tail has nowhere to protrude to, and the attempt just yields a shape sitting
        // oddly on the border.
        using var head = new SolidBrush(MainForm.Blood);
        var tri = beakUp
            ? new[] { new Point(beakX, 4), new Point(beakX - 9, Beak + 1), new Point(beakX + 9, Beak + 1) }
            : new[] { new Point(beakX, Height - 5), new Point(beakX - 9, Height - Beak - 2), new Point(beakX + 9, Height - Beak - 2) };
        g.FillPolygon(head, tri);
    }
}
