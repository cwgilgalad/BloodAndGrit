using System.ComponentModel;
using System.Text.Json;

namespace BloodAndGritKeeper;

public partial class MainForm : Form
{
    // shared state
    readonly BindingList<PartyMember> party = new();
    readonly BindingList<Combatant> tracker = new();
    readonly BindingList<Ride> rides = new();          // the corral and the yard — see TabsRides.cs
    readonly BindingList<EncounterPick> encounter = new();
    readonly BindingList<CampaignClock> clocks = new();
    TextBox notesBox;
    ListBox rollLog;
    int round = 1;
    TabControl tabsCtl;

    // ---- state that outlives its control ----
    // Nine of the ten tabs are built on first visit (see LazyTab), so anything the rest of
    // the app reads or writes has to live in a field the whole time and merely be MIRRORED
    // into a control once that control exists. Without this the roll log would swallow every
    // line rolled before the Keeper first opened the Dice tab, and the session ledger would
    // autosave an empty string over notes it had loaded but never shown.
    readonly List<string> logLines = new();   // newest first, same order as the ListBox
    string notesText = "";                    // the Keeper's ledger (Session tab)
    int partyLevelHint = 2;                   // encounter-budget party level (Encounter tab)

    // ---- shared theme (frontier-book palette) ----
    public static readonly Color Paper   = Color.FromArgb(247, 242, 228);
    public static readonly Color Ink     = Color.FromArgb(38, 28, 20);
    public static readonly Color Blood   = Color.FromArgb(120, 22, 22);
    public static readonly Color Gold     = Color.FromArgb(150, 116, 50);
    public static readonly Color Verdigris = Color.FromArgb(60, 96, 84);
    public static readonly Color PcRow   = Color.FromArgb(238, 244, 232);
    public static readonly Color FoeRow  = Color.FromArgb(250, 250, 247);
    public static readonly Color DownRow = Color.FromArgb(248, 224, 224);

    // roll-log result colors — so a dice result jumps out from plain event lines
    public static readonly Color RollCritGood = Color.FromArgb(150, 108, 0);   // critical success — rich gold
    public static readonly Color RollCritBad  = Color.FromArgb(48, 12, 12);    // critical failure — near-black
    public static readonly Color RollGood     = Verdigris;                     // plain success
    public static readonly Color RollBad      = Color.FromArgb(150, 70, 30);   // plain failure — rust
    public static readonly Color RollNeutral  = Color.FromArgb(52, 70, 120);   // a roll with no DC to judge it by

    // ---- universal undo/redo (snapshot-based over the shared game state) ----
    readonly List<string> undoStack = new();
    readonly List<string> redoStack = new();
    const int UndoDepth = 50;
    bool suppressUndo = true;                 // true until the initial load finishes
    string undoBaseline;
    ToolStripMenuItem undoMenuItem, redoMenuItem;
    ToolStripButton undoStatusBtn, redoStatusBtn;

    internal const string AppVersion = "1.17.0";
    // The book editions the app ships alongside — the C#-side copy of the numbers the Python builders
    // stamp. Bump these in the same breath as a book version (they show in the status bar).
    internal const string PlayerBookVer = "2.24", KeeperBookVer = "2.11", BestiaryVer = "2.10";

    // How this table is running (Player / Keeper-with-dice / Keeper-on-the-engine). Read live by the
    // Strike and Dread dialogs to decide who rolls, and by ApplyModeTabs to decide what's on show.
    internal RunMode Mode { get; private set; }
    readonly List<TabPage> allTabs = new();     // every tab, in order, so the mode can hide/show them

    public MainForm() : this(RunMode.KeeperEngine) { }

    public MainForm(RunMode mode)
    {
        Mode = mode;
        MapInk.LoadKindColors(Prefs.Load().MarkerInk);   // the Keeper's standing marker colors
        Text = "GritKeeper — Blood & Grit";
        if (AppIcon != null) Icon = AppIcon;      // the emblem, not the stock-Windows square
        // Never open taller or wider than the screen actually is — on a 1366×768 laptop the
        // old fixed 1280×820 put the bottom row of buttons below the taskbar, unreachable.
        var work = Screen.PrimaryScreen.WorkingArea;
        Width = Math.Min(1280, work.Width);
        Height = Math.Min(820, work.Height);
        MinimumSize = new Size(1040, 640);
        StartPosition = FormStartPosition.CenterScreen;
        Font = new Font("Segoe UI", 9.5f);
        BackColor = Paper;
        KeyPreview = true;

        var tabs = new TabControl { Dock = DockStyle.Fill, Padding = new Point(14, 6) };
        tabsCtl = tabs;
        // Build the tab the Keeper is looking at; hand the other nine over as shells that
        // fill themselves the first time they're selected. Measured on this laptop, building
        // all ten up front cost 379 ms of a ~1,000 ms launch (Bestiary 91, Posse 71, Map 61,
        // Dice 46, Reference 45, the rest small) — a third of the wait spent on nine tabs
        // nobody was looking at yet. Deferred, that third comes off the launch and is paid
        // back a tab at a time, none of them over ~90 ms, which is under the threshold where
        // a click feels like it waited.
        allTabs.Add(BuildPosseTab());
        allTabs.Add(LazyTab("Dice", BuildDiceTab));
        allTabs.Add(LazyTab("Bestiary", BuildBestiaryTab));
        allTabs.Add(LazyTab("Encounter", BuildEncounterTab));
        allTabs.Add(LazyTab("Tracker", BuildTrackerTab));
        allTabs.Add(LazyTab("Generators", BuildGeneratorsTab));
        allTabs.Add(LazyTab("Map", BuildMapTab));
        allTabs.Add(LazyTab("New Soul", BuildSoulTab));
        allTabs.Add(LazyTab("Reference", BuildReferenceTab));
        allTabs.Add(LazyTab("Session", BuildSessionTab));
        tabs.Selecting += (s, e) => RealizeTab(e.TabPage);
        Controls.Add(tabs);
        ApplyModeTabs();     // put the right tabs on show for the chosen mode, and land on the first

        var menu = BuildMenu(tabs);
        MainMenuStrip = menu;
        Controls.Add(menu);                       // added after the fill control so it docks above it

        // Ctrl+number jumps to a tab (keyboard-first, like the market tools), and each
        // busy tab gets table-speed shortcuts for its most-hammered buttons. Deliberately
        // NOT keyed: destructive clears (a confirm click should stay a deliberate act) and
        // browse-y generator buttons (Tab+Space already serves them).
        KeyDown += (s, e) =>
        {
            if (e.Control && e.KeyCode >= Keys.D1 && e.KeyCode <= Keys.D9)
            { tabs.SelectedIndex = e.KeyCode - Keys.D1; e.Handled = true; return; }
            if (e.Control && e.KeyCode == Keys.D0 && tabs.TabPages.Count >= 10)
            { tabs.SelectedIndex = 9; e.Handled = true; return; }
            if (!e.Control || e.Alt || e.Shift) return;
            void Did() { e.Handled = true; e.SuppressKeyPress = true; }
            string page = tabs.SelectedTab?.Text;
            if (page == "Posse" && posseGrid?.IsCurrentCellInEditMode != true)
            {
                if (e.KeyCode == Keys.D) { AdjustPC(-1); Did(); }
                else if (e.KeyCode == Keys.H) { AdjustPC(+1); Did(); }
            }
            else if (page == "Tracker" && trkGrid?.IsCurrentCellInEditMode != true)
            {
                if (e.KeyCode == Keys.D) { AdjustCombatant(-1); Did(); }
                else if (e.KeyCode == Keys.H) { AdjustCombatant(+1); Did(); }
                else if (e.KeyCode == Keys.I) { RollInitiative(); Did(); }
                else if (e.KeyCode == Keys.R) { NextRound(); Did(); }
            }
            else if (page == "Bestiary" && e.KeyCode == Keys.F)
            { beastSearch.Focus(); beastSearch.SelectAll(); Did(); }
            else if (page == "Map" && e.KeyCode == Keys.G)
            { MapDraw(true); Did(); }
        };

        var status = new StatusStrip { BackColor = Paper, ShowItemToolTips = true };
        statusLoaded = new ToolStripStatusLabel(Amp(StatusLoadedText())) { ForeColor = Ink };
        status.Items.Add(statusLoaded);
        // The last thing that happened, said where the Keeper is looking. Every action already
        // answered in the roll log — but the roll log lives on the Dice tab, so from the Posse or
        // the Tracker a button that declined (nothing selected, no soul made yet) looked like a
        // button that did nothing at all. That's the "some buttons don't work" report.
        statusSay = new ToolStripStatusLabel("") { Spring = true, ForeColor = Ink, TextAlign = ContentAlignment.MiddleLeft };
        status.Items.Add(statusSay);
        // Undo and Redo are pinned here rather than on a tab so they're reachable wherever the
        // Keeper is working. Flat text in a status bar reads as a caption, though, not as
        // something you can press (user-reported) — so they wear a raised face and a border.
        ToolStripButton UndoBtn(string text, string tip, Action go)
        {
            var b = new ToolStripButton(text)
            {
                Enabled = false, DisplayStyle = ToolStripItemDisplayStyle.Text, ToolTipText = tip,
                BackColor = Color.FromArgb(238, 230, 210), ForeColor = Ink,
                Margin = new Padding(3, 2, 3, 2), Padding = new Padding(7, 1, 7, 1),
                Font = new Font("Segoe UI", 9f, FontStyle.Bold)
            };
            b.Click += (s, e) => go();
            b.Paint += (s, e) =>
            {
                var r = new Rectangle(0, 0, b.Width - 1, b.Height - 1);
                using var pen = new Pen(Color.FromArgb(b.Enabled ? 150 : 205, 140, 118));
                e.Graphics.DrawRectangle(pen, r);
            };
            return b;
        }
        undoStatusBtn = UndoBtn("⟲ Undo", "Undo the last change — the posse, the corral, the tracker, "
            + "the encounter, the threads (Ctrl+Z)", Undo);
        redoStatusBtn = UndoBtn("⟳ Redo", "Redo the last undone change (Ctrl+Y)", Redo);
        status.Items.Add(undoStatusBtn);
        status.Items.Add(redoStatusBtn);
        status.Items.Add(new ToolStripStatusLabel("Ctrl+1–0 tabs · F1 the five-minute lesson · auto-saves on exit + every 5 min") { ForeColor = Gold });
        Controls.Add(status);

        // Universal undo/redo: any add/remove/edit to the posse, tracker, encounter, or
        // campaign threads captures a snapshot. Session notes keep the textbox's own
        // native per-field undo instead — snapshotting every keystroke would flood the stack.
        party.ListChanged += (s, e) => CaptureUndo();
        tracker.ListChanged += (s, e) => CaptureUndo();
        encounter.ListChanged += (s, e) => CaptureUndo();
        clocks.ListChanged += (s, e) => CaptureUndo();
        rides.ListChanged += (s, e) => CaptureUndo();

        TryAutoLoad();
        undoBaseline = JsonSerializer.Serialize(Snapshot());
        suppressUndo = false;
        RefreshUndoRedoButtons();
        FormClosing += (s, e) => AutoSave();

        // Complete the two-way Blood sync: a direct cell edit on the Posse grid must reach
        // the Tracker the same way the Damage/Heal buttons do — and the encounter budget
        // depends on posse size, so it re-verdicts when souls come or go.
        party.ListChanged += (s, e) =>
        {
            if (e.ListChangedType == ListChangedType.ItemChanged && e.PropertyDescriptor != null)
            {
                if ((e.PropertyDescriptor.Name == "BloodCur" || e.PropertyDescriptor.Name == "BloodMax")
                    && e.NewIndex >= 0 && e.NewIndex < party.Count)
                    MirrorToTracker(party[e.NewIndex]);
            }
            else if (e.ListChangedType is ListChangedType.ItemAdded or ListChangedType.ItemDeleted or ListChangedType.Reset)
                RefreshEncounter();
        };

        // Belt-and-braces against power loss / hard crashes: autosave every five minutes,
        // not only on clean exit.
        var saveTimer = new System.Windows.Forms.Timer { Interval = 5 * 60 * 1000 };
        saveTimer.Tick += (s, e) => AutoSave();
        saveTimer.Start();
    }

    // ---------------------------------------------------------- the table's mode
    ToolStripStatusLabel statusLoaded;
    ToolStripStatusLabel statusSay;

    static string ModeLabel(RunMode m) => m switch
    {
        RunMode.Player      => "Player's table",
        RunMode.KeeperDice  => "Keeper · dice & books",
        _                   => "Keeper · on the engine",
    };
    string StatusLoadedText() =>
        $"{Db.Creatures.Count} creatures loaded  ·  {ModeLabel(Mode)}  ·  Player's Book v{PlayerBookVer} · Keeper's Book v{KeeperBookVer} · Bestiary v{BestiaryVer}";

    // True when the app rolls the dice (the engine table); false when the Keeper rolls their own and
    // just enters the result (the dice-and-books table). A player's own table rolls on the Dice tab.
    internal bool EngineRolls => Mode != RunMode.KeeperDice;

    // The tabs a given mode shows. A player gets their own three; a Keeper gets the whole board.
    static readonly string[] PlayerTabs = { "New Soul", "Dice", "Reference" };
    bool ShowsTab(string title) => Mode != RunMode.Player || Array.IndexOf(PlayerTabs, title) >= 0;

    // Put the right tabs on show for the current mode, preserving their order, and land on the first.
    // The lazy shells are reused, so hiding a tab the Keeper never opened costs nothing.
    void ApplyModeTabs()
    {
        tabsCtl.TabPages.Clear();
        foreach (var t in allTabs) if (ShowsTab(t.Text)) tabsCtl.TabPages.Add(t);
        if (tabsCtl.TabPages.Count > 0) { tabsCtl.SelectedIndex = 0; RealizeTab(tabsCtl.SelectedTab); }
    }

    /// <summary>Bring a tab to the front by name, realizing it if this is its first visit. Returns
    /// false when the current run mode doesn't show that tab at all — a player's view has no Map,
    /// and a feature that hands work across to one has to be able to find that out politely.</summary>
    internal bool ShowTab(string title)
    {
        for (int i = 0; i < tabsCtl.TabPages.Count; i++)
            if (tabsCtl.TabPages[i].Text == title)
            {
                tabsCtl.SelectedIndex = i;
                RealizeTab(tabsCtl.TabPages[i]);
                return true;
            }
        return false;
    }

    /// <summary>Switch modes live from the menu: re-lay the tabs, refresh the status line, and record
    /// the choice so the next launch remembers it. The roll behavior follows <see cref="EngineRolls"/>
    /// on the next Strike or Dread Check — no restart needed.</summary>
    internal void SetMode(RunMode mode)
    {
        if (mode == Mode) return;
        Mode = mode;
        ApplyModeTabs();
        if (statusLoaded != null) statusLoaded.Text = Amp(StatusLoadedText());
        Prefs.Save(mode, true);   // a deliberate switch is also a remembered preference
        Log($"Table set to {ModeLabel(mode)}.");
    }

    /// <summary>The launch chooser. Returns the picked mode and whether to skip this next time.
    /// A pure modal with no dependence on an existing MainForm, so Program can show it before the
    /// window is built. Cancel keeps the mode it opened on.</summary>
    public static (RunMode mode, bool remember) ChooseMode(RunMode current)
    {
        using var f = new Form
        {
            Text = "Blood & Grit — GritKeeper", Width = 560, Height = 470,
            FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterScreen,
            MinimizeBox = false, MaximizeBox = false, ShowIcon = AppIcon != null, BackColor = Paper
        };
        if (AppIcon != null) f.Icon = AppIcon;
        f.Controls.Add(new Label { Left = 24, Top = 18, Width = 500, Height = 24, Text = "How are you running the table tonight?",
            Font = new Font("Segoe UI Semibold", 12f), ForeColor = Ink });

        var picked = current;
        var cards = new (RunMode mode, string head, string blurb)[]
        {
            (RunMode.Player,       "I'm a Player",
                "Build and run your own character, roll your dice, and look up the rules. The Keeper's tools stay put away."),
            (RunMode.KeeperDice,   "Keeper — with dice & books",
                "You roll real dice and run from the books. GritKeeper is your referee and ledger: enter the die you rolled and it reads the degrees, the penalties, the damage, and keeps everyone's Blood and Nerve."),
            (RunMode.KeeperEngine, "Keeper — on the engine",
                "No dice on the table, no ledgers to keep. GritKeeper rolls it all — to-hit, damage, Dread — so you can play on a phone, on a porch, anywhere."),
        };
        int y = 56;
        var radios = new List<RadioButton>();
        foreach (var c in cards)
        {
            // UseMnemonic off, or the ampersand in "dice & books" is swallowed as a keyboard
            // mnemonic and the mode reads "Keeper — with dice  books" (the same trap the Labels
            // hit back in v1.4).
            var rb = new RadioButton { Left = 24, Top = y, Width = 500, Height = 22, Text = c.head,
                Font = new Font("Segoe UI Semibold", 10.5f), ForeColor = Ink, Checked = c.mode == current,
                UseMnemonic = false };
            var mode = c.mode; rb.CheckedChanged += (s, e) => { if (rb.Checked) picked = mode; };
            f.Controls.Add(rb); radios.Add(rb);
            // 44px held three lines and the longest blurb runs to four — it was cut mid-sentence.
            f.Controls.Add(new Label { Left = 44, Top = y + 24, Width = 480, Height = 58, Text = c.blurb,
                ForeColor = Ink, UseMnemonic = false });
            y += 96;
        }
        if (!radios.Any(r => r.Checked)) radios[2].Checked = true;

        var remember = new CheckBox { Left = 24, Top = y + 2, Width = 300, Text = "Start here next time (skip this)", ForeColor = Ink };
        f.Controls.Add(remember);
        var ok = new Button { Text = "Sit down ▸", Left = 360, Top = y, Width = 160, Height = 32, DialogResult = DialogResult.OK };
        f.Controls.Add(ok); f.AcceptButton = ok;

        f.ShowDialog();
        return (picked, remember.Checked);
    }

    // Left/Right turn the Reference deck no matter which control holds focus — arrow
    // keys are normally eaten as focus-navigation before KeyDown ever sees them. The
    // Reference tab has no text inputs, so stealing them there costs nothing.
    protected override bool ProcessCmdKey(ref Message msg, Keys keyData)
    {
        if (tabsCtl?.SelectedTab == referencePage && (keyData == Keys.Left || keyData == Keys.Right))
        {
            RefShow(refPage + (keyData == Keys.Right ? 1 : -1));
            return true;
        }
        return base.ProcessCmdKey(ref msg, keyData);
    }

    // ---------------------------------------------------------- lazy tabs
    // A tab page that hasn't been filled in yet, mapped to the builder that will fill it.
    readonly Dictionary<TabPage, Func<TabPage>> pendingTabs = new();

    TabPage LazyTab(string title, Func<TabPage> build)
    {
        var shell = new TabPage(title) { BackColor = Paper };
        pendingTabs[shell] = build;
        return shell;
    }

    // Run the builder and move what it made onto the shell the TabControl is already
    // holding. The builders each make their own TabPage (and half of them stash it in a
    // field), so reparenting the children is less invasive than rewriting ten signatures.
    // AddRange preserves the array's order, and WinForms resolves docking by z-order, so
    // the layout comes out identical to the eager build — including the SplitContainers,
    // whose geometry the Split() helper still defers to the first SizeChanged.
    void RealizeTab(TabPage shell)
    {
        if (shell == null || !pendingTabs.TryGetValue(shell, out var build)) return;
        pendingTabs.Remove(shell);          // remove FIRST: a builder that logs would re-enter
        var built = build();
        shell.SuspendLayout();
        shell.Text = built.Text;
        shell.BackColor = built.BackColor;
        shell.Padding = built.Padding;
        shell.AutoScroll = built.AutoScroll;
        var kids = new Control[built.Controls.Count];
        built.Controls.CopyTo(kids, 0);
        built.Controls.Clear();
        shell.Controls.AddRange(kids);
        shell.ResumeLayout(true);
        // ProcessCmdKey steers Left/Right to the Reference deck by comparing the selected
        // tab against this field — it has to name the page actually in the TabControl.
        if (ReferenceEquals(built, referencePage)) referencePage = shell;
        built.Dispose();
    }

    // ---------------------------------------------------------- shared helpers
    /// <summary>The app is declining to act — nothing is selected, nothing has been made yet.
    /// Says so in red on the status bar as well as in the log, so the refusal is visible from
    /// whatever tab the button was pressed on.</summary>
    void Nope(string s) { Log(s); Say(s, Blood); }

    /// <summary>Put a line on the status bar. Called for every logged event, so the bar always
    /// carries the last thing the app did.</summary>
    void Say(string s, Color c)
    {
        if (statusSay == null) return;          // logged before the shell was built
        statusSay.ForeColor = c;
        statusSay.Text = Amp(s);
        statusSay.ToolTipText = s;              // a tooltip draws its text literally — no escaping
    }

    /// <summary>Escape a run of prose for a control that reads "&amp;" as a keyboard mnemonic.
    /// ToolStrip items do, silently: "dice &amp; books" renders as "dice  books" on the status bar.
    /// Labels are handled at their own helpers (<see cref="Lbl"/>/<see cref="Heading"/>) by turning
    /// mnemonics off, but a ToolStripItem has no such switch, so the text has to be doubled.</summary>
    static string Amp(string s) => s?.Replace("&", "&&");

    Panel resultCard;
    Label resultBig, resultSub;

    /// <summary>Put a roll's outcome on the Dice tab's card: the headline big and graded by the
    /// same colors the log uses, the working underneath it in plain words. Long headlines (a
    /// degree name) step down a size rather than clipping.</summary>
    void ShowResult(string big, string sub, Color c)
    {
        if (resultBig == null) return;              // rolled before the Dice tab was ever built
        resultBig.Text = big;
        resultBig.ForeColor = c;
        resultBig.Font = new Font("Segoe UI", big.Length > 12 ? 18f : big.Length > 6 ? 24f : 30f, FontStyle.Bold);
        resultSub.Text = sub;
    }

    /// The color a four-degrees result is read in — shared with the roll log so one outcome is
    /// never gold in one place and rust in another.
    static Color DegreeColor(string degree) => degree switch
    {
        "CRITICAL SUCCESS" => RollCritGood,
        "CRITICAL FAILURE" => RollCritBad,
        "Success"          => RollGood,
        "Failure"          => RollBad,
        _                  => RollNeutral,
    };

    void Log(string s)
    {
        Say(s, Ink);
        string line = $"[{DateTime.Now:HH:mm}] {s}";
        // The list is the record; the ListBox is a view of it that may not exist yet.
        logLines.Insert(0, line);
        while (logLines.Count > 400) logLines.RemoveAt(logLines.Count - 1);
        if (rollLog == null) return;
        rollLog.Items.Insert(0, line);
        while (rollLog.Items.Count > 400) rollLog.Items.RemoveAt(rollLog.Items.Count - 1);
        // Owner-drawn ListBoxes don't compute their own horizontal extent, so the
        // h-scrollbar dies without this (+16 covers the bold variants running wider).
        int w = TextRenderer.MeasureText(line, rollLog.Font).Width + 16;
        if (w > rollLog.HorizontalExtent) rollLog.HorizontalExtent = w;
    }

    // Color-codes dice-roll results in the log so they jump out from plain event lines:
    // a four-degrees outcome (CHECK/DREAD) is graded by its degree word, a bare die roll
    // (quick dice) by whether it landed on its max or min face, and any other roll
    // (ROLL <expr>) gets a neutral "this is a roll" accent. Everything else — posse,
    // tracker, session events — stays the plain ink color.
    static readonly System.Text.RegularExpressions.Regex DegreeRe =
        new(@"→ (CRITICAL SUCCESS|CRITICAL FAILURE|Success|Failure)\b");
    static readonly System.Text.RegularExpressions.Regex QuickDieRe =
        new(@"^\[\d\d:\d\d\] d(\d+) → (\d+)$");
    static readonly System.Text.RegularExpressions.Regex RollLineRe =
        new(@"^\[\d\d:\d\d\] (ROLL |CHECK — |DREAD — )");

    static void StyleRollLog(ListBox log)
    {
        // One bold variant, created once and kept for the log's lifetime. Never wrap
        // e.Font in a using — that disposes the control's own Font out from under it.
        var boldFont = new Font(log.Font, log.Font.Style | FontStyle.Bold);
        log.Disposed += (s, e) => boldFont.Dispose();
        log.DrawMode = DrawMode.OwnerDrawFixed;
        log.ItemHeight = TextRenderer.MeasureText("Xg", boldFont).Height + 3;
        log.DrawItem += (s, e) =>
        {
            if (e.Index < 0 || e.Index >= log.Items.Count) return;
            string text = log.Items[e.Index].ToString() ?? "";
            Color color = Ink;
            bool bold = false;
            var dm = DegreeRe.Match(text);
            if (dm.Success)
            {
                switch (dm.Groups[1].Value)
                {
                    case "CRITICAL SUCCESS": color = RollCritGood; bold = true; break;
                    case "CRITICAL FAILURE": color = RollCritBad; bold = true; break;
                    case "Success": color = RollGood; break;
                    case "Failure": color = RollBad; break;
                }
            }
            else
            {
                var qm = QuickDieRe.Match(text);
                if (qm.Success)
                {
                    int sides = int.Parse(qm.Groups[1].Value), val = int.Parse(qm.Groups[2].Value);
                    color = val == sides ? RollCritGood : val == 1 ? RollCritBad : RollNeutral;
                }
                else if (RollLineRe.IsMatch(text)) color = RollNeutral;
            }
            e.DrawBackground();
            bool selected = (e.State & DrawItemState.Selected) != 0;
            TextRenderer.DrawText(e.Graphics, text, bold ? boldFont : e.Font, e.Bounds,
                selected ? SystemColors.HighlightText : color,
                TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPrefix);
            e.DrawFocusRectangle();
        };
    }

    static Button Btn(string text, EventHandler onClick, int w = 120, string tip = null)
    {
        var b = new Button
        {
            Text = text, Width = w, Height = 32, Margin = new Padding(3),
            FlatStyle = FlatStyle.System, UseVisualStyleBackColor = true
        };
        b.Click += onClick;
        if (tip != null) Tip.SetToolTip(b, tip);
        return b;
    }

    static readonly ToolTip Tip = new() { AutoPopDelay = 12000, InitialDelay = 400 };

    // A button that drops a menu of choices on click, so one control offers several
    // related actions (sort orders, rest scopes, conditions) without crowding the bar.
    // A "-" label becomes a separator. The menu lives as long as the button (closure-held).
    /// One font for every drop-down in the app, instead of a fresh one per menu. The pop-ups below
    /// are built on each click by design — the lists they carry (who's in the posse, what's under
    /// the cursor) must never be stale — so anything allocated per menu is allocated per click.
    static readonly Font MenuFont = new("Segoe UI", 9.5f);
    static readonly Font MenuFontBold = new("Segoe UI", 9.5f, FontStyle.Bold);

    /// <summary>A right-click menu that lets itself go once it closes. Built-per-click menus used to
    /// leave the strip (and its native handles) behind for the life of the process; a Keeper who
    /// spends an evening nudging map markers can open a great many of them.</summary>
    static ContextMenuStrip PopupMenu()
    {
        var menu = new ContextMenuStrip { Font = MenuFont };
        // Disposing inside the Closed handler would pull the strip out from under the click that
        // is still being dispatched, so it waits for the message to finish first.
        menu.Closed += (s, e) => menu.BeginInvoke(new Action(menu.Dispose));
        return menu;
    }

    static Button MenuBtn(string text, int w, string tip, params (string label, EventHandler onClick)[] items)
    {
        var b = Btn(text, null, w, tip);
        // NOT PopupMenu(): this one belongs to the button and is shown again on every press.
        var menu = new ContextMenuStrip { Font = MenuFont };
        foreach (var (label, onClick) in items)
        {
            if (label == "-") { menu.Items.Add(new ToolStripSeparator()); continue; }
            // A null handler means the line is a group heading, not a choice — grey it out so it
            // doesn't read as a button that does nothing when clicked. Amp() because a menu item
            // DOES take "&" as a mnemonic, and these labels are prose.
            var mi = new ToolStripMenuItem(Amp(label)) { Enabled = onClick != null };
            if (onClick != null) mi.Click += onClick;
            menu.Items.Add(mi);
        }
        b.Click += (s, e) => menu.Show(b, new Point(0, b.Height));
        return b;
    }

    // ---------------------------------------------------------- right-click on a list
    // Every list in the app answers a right-click with the things that can be done to the row
    // under the cursor — the same operations as the buttons above it, no more and no less, so
    // the menu can never quietly become a second, divergent set of features. The row is SELECTED
    // first, before the menu is built: that way each item can call the very same handler the
    // button calls ("the selected soul…"), and what the Keeper pointed at and what the app acts
    // on are guaranteed to be the same row. Wiring is on MouseDown so the selection has moved
    // before the menu draws, which is what makes it look like it belongs to the row.

    /// <summary>Hang a right-click menu on a data-bound grid. <paramref name="build"/> fills the menu
    /// for the row's item; an empty menu simply doesn't show, and a right-click on blank space below
    /// the rows does nothing at all.</summary>
    void GridMenu<T>(DataGridView grid, Action<ContextMenuStrip, T> build) where T : class
    {
        grid.MouseDown += (s, e) =>
        {
            if (e.Button != MouseButtons.Right) return;
            var hit = grid.HitTest(e.X, e.Y);
            if (hit.RowIndex < 0 || hit.RowIndex >= grid.Rows.Count) return;

            // A cell left mid-edit would otherwise refuse the move and throw on CurrentCell.
            grid.EndEdit();
            var row = grid.Rows[hit.RowIndex];
            if (row.DataBoundItem is not T item) return;
            grid.ClearSelection();
            row.Selected = true;
            // Land on a real column: the hit can be a row header (-1), and a button column would
            // put the grid's focus on something that isn't a value.
            var cell = row.Cells[hit.ColumnIndex >= 0 && grid.Columns[hit.ColumnIndex] is DataGridViewTextBoxColumn
                ? hit.ColumnIndex : FirstTextColumn(grid)];
            if (cell.Visible) grid.CurrentCell = cell;

            var menu = PopupMenu();
            build(menu, item);
            if (menu.Items.Count > 0) menu.Show(grid, e.Location);
        };
    }

    static int FirstTextColumn(DataGridView g)
    {
        for (int i = 0; i < g.Columns.Count; i++)
            if (g.Columns[i] is DataGridViewTextBoxColumn && g.Columns[i].Visible) return i;
        return 0;
    }

    /// <summary>The same, for a ListBox. <paramref name="build"/> is handed the item under the cursor.</summary>
    void ListMenu<T>(ListBox list, Action<ContextMenuStrip, T> build) where T : class
    {
        list.MouseDown += (s, e) =>
        {
            if (e.Button != MouseButtons.Right) return;
            int i = list.IndexFromPoint(e.Location);
            if (i < 0 || i >= list.Items.Count) return;
            list.SelectedIndex = i;
            if (list.Items[i] is not T item) return;
            var menu = PopupMenu();
            build(menu, item);
            if (menu.Items.Count > 0) menu.Show(list, e.Location);
        };
    }

    /// <summary>One menu line. Kept as a helper so every list's menu is built the same way and every
    /// label goes through <see cref="Amp"/> — a menu item reads "&amp;" as a mnemonic, and these are
    /// creature names and prose, not accelerators.</summary>
    static ToolStripItem MI(ContextMenuStrip menu, string label, Action go, bool enabled = true)
    {
        var it = menu.Items.Add(Amp(label), null, (s, e) => go());
        it.Enabled = enabled;
        return it;
    }

    static void MISep(ContextMenuStrip menu) => menu.Items.Add(new ToolStripSeparator());

    /// <summary>A greyed line naming what the menu is acting on, so there is never any doubt which
    /// row the actions below will land on. Bold, because it's a title and not a choice.</summary>
    static void MIHead(ContextMenuStrip menu, string label)
    {
        // MenuFontBold, not a fresh Font: these menus are built on every right-click by design,
        // and a Font handed to a ToolStripItem isn't disposed with the item.
        menu.Items.Add(new ToolStripMenuItem(Amp(label)) { Enabled = false, Font = MenuFontBold });
        menu.Items.Add(new ToolStripSeparator());
    }

    // UseMnemonic off on both: a Label treats "&" as a keyboard mnemonic and swallows it, so
    // "dice & books" renders as "dice  books" and "The corral & the yard" loses its ampersand.
    // Labels here are prose, never accelerators, so the trap has no upside — closing it in the
    // helpers means no future caller has to remember (it has bitten this app three times now).
    /// <summary>A Panel that paints without flicker. A plain Panel can't be told to double-buffer
    /// from outside (the property is protected), and anything owner-drawn on one tears as the
    /// window resizes — which is exactly when a docked bar gets repainted most.</summary>
    sealed class BufferedPanel : Panel
    {
        public BufferedPanel() { DoubleBuffered = true; ResizeRedraw = true; }
    }

    static Label Lbl(string t, int w = 0)
    {
        var l = new Label { Text = t, AutoSize = w == 0, Padding = new Padding(0, 8, 4, 0), ForeColor = Ink, UseMnemonic = false };
        if (w > 0) l.Width = w;
        return l;
    }

    static Label Heading(string t) => new()
    { Text = t, AutoSize = true, Font = new Font("Segoe UI", 10f, FontStyle.Bold), ForeColor = Blood, Padding = new Padding(0, 6, 0, 2), UseMnemonic = false };

    /// <summary>
    /// Breathing room for text panes. WinForms RichTextBox/ListBox ignore their own Padding
    /// property entirely, so docked read-panes used to press their first character straight
    /// against the window edge. Wrapping the control in a padded host panel is the reliable
    /// fix; the host takes the control's own back color so the margin reads as part of the page.
    /// </summary>
    static Panel Pad(Control c, int all)
    {
        var host = new Panel { Dock = DockStyle.Fill, Padding = new Padding(all), BackColor = c.BackColor };
        c.Dock = DockStyle.Fill;
        host.Controls.Add(c);
        return host;
    }

    // ---- the emblem (embedded in the exe) as window icon and watermark ----
    static Image _emblem;
    static bool _emblemTried;
    internal static Image Emblem
    {
        get
        {
            if (!_emblemTried)
            {
                _emblemTried = true;
                try
                {
                    var asm = typeof(MainForm).Assembly;
                    var name = Array.Find(asm.GetManifestResourceNames(),
                        n => n.EndsWith("emblem.png", StringComparison.OrdinalIgnoreCase));
                    if (name != null)
                    { using var s = asm.GetManifestResourceStream(name); _emblem = Image.FromStream(s); }
                }
                catch { /* purely cosmetic — never let branding take the app down */ }
            }
            return _emblem;
        }
    }

    static Icon _appIcon;
    static bool _appIconTried;
    internal static Icon AppIcon
    {
        get
        {
            if (!_appIconTried)
            {
                _appIconTried = true;
                try
                {
                    var asm = typeof(MainForm).Assembly;
                    var name = Array.Find(asm.GetManifestResourceNames(),
                        n => n.EndsWith("app.ico", StringComparison.OrdinalIgnoreCase));
                    if (name != null)
                    { using var s = asm.GetManifestResourceStream(name); _appIcon = new Icon(s); }
                }
                catch { }
            }
            return _appIcon;
        }
    }

    static readonly System.Drawing.Imaging.ImageAttributes WmAttr = MakeWmAttr();
    static System.Drawing.Imaging.ImageAttributes MakeWmAttr()
    {
        var a = new System.Drawing.Imaging.ImageAttributes();
        a.SetColorMatrix(new System.Drawing.Imaging.ColorMatrix { Matrix33 = 0.15f });   // ghost-faint
        return a;
    }

    /// <summary>
    /// Paints the emblem, ghost-faint, centered in whatever background space is left
    /// once real content is accounted for. usedHeight reports how far real content
    /// reaches; the emblem centers in the full free zone below it (not just the
    /// bottom half), and scales with the pane's own size — bigger in a roomy window,
    /// smaller in a tight one, gone entirely below a dignified minimum — so it never
    /// sits behind rows, text, or controls.
    /// </summary>
    static void Watermark(Control host, Func<int> usedHeight)
    {
        host.Paint += (s, e) =>
        {
            var img = Emblem; if (img == null) return;
            int cw = host.ClientSize.Width, ch = host.ClientSize.Height;
            int top = usedHeight() + 22;
            int freeH = ch - top;
            if (freeH < 60) return;                             // no room at all below content
            // scale with the window: as large as the free background allows, capped so a
            // big pane doesn't let it balloon past a dignified share of the width
            int maxW = Math.Min(cw - 56, cw * 3 / 5);
            int w = Math.Min(maxW, (freeH - 24) * img.Width / img.Height);
            if (w < 150) return;
            int h = w * img.Height / img.Width;
            var r = new Rectangle((cw - w) / 2, top + (freeH - h) / 2, w, h);
            e.Graphics.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.HighQualityBicubic;
            e.Graphics.DrawImage(img, r, 0, 0, img.Width, img.Height, GraphicsUnit.Pixel, WmAttr);
        };
        host.Resize += (s, e) => host.Invalidate();
    }

    // content extent of a FlowLayoutPanel (or any panel): the lowest control edge
    static int FlowBottom(Control c)
        => c.Controls.Cast<Control>().Select(x => x.Bottom).DefaultIfEmpty(0).Max();

    // content extent of a grid: header plus every visible row
    static int GridBottom(DataGridView g)
        => g.ColumnHeadersHeight + g.Rows.GetRowsHeight(DataGridViewElementStates.Visible);

    // content extent of a centered hint label: the bottom edge of its centered text block
    static int HintBottom(Label l)
        => (l.Height + TextRenderer.MeasureText(l.Text, l.Font).Height) / 2;

    /// <summary>
    /// SplitContainer whose minimum panel sizes and splitter position are applied only
    /// once the control has been laid out with a real size. Setting these at construction
    /// throws (SplitterDistance must fit inside the not-yet-sized control), which crashed
    /// the app at startup on real Windows.
    /// </summary>
    static SplitContainer Split(Orientation o, int p1Min, int p2Min, double ratio)
    {
        var sc = new SplitContainer { Dock = DockStyle.Fill, Orientation = o };
        void Apply(object s, EventArgs e)
        {
            int span = o == Orientation.Vertical ? sc.Width : sc.Height;
            if (span < 80) return;                              // not laid out yet — wait
            int p1 = Math.Min(p1Min, span * 2 / 5);             // shrink mins on small windows
            int p2 = Math.Min(p2Min, span * 2 / 5);
            try
            {
                sc.Panel1MinSize = p1;
                sc.Panel2MinSize = p2;
                sc.SplitterDistance = Math.Clamp((int)(span * ratio), p1, Math.Max(p1, span - p2));
            }
            catch { return; }                                   // odd intermediate size — retry on next resize
            sc.SizeChanged -= Apply;                            // success: one-shot
        }
        sc.SizeChanged += Apply;
        return sc;
    }

    void StyleGrid(DataGridView g)
    {
        g.BorderStyle = BorderStyle.None;
        g.BackgroundColor = Paper;
        g.EnableHeadersVisualStyles = false;
        g.ColumnHeadersDefaultCellStyle.BackColor = Blood;
        g.ColumnHeadersDefaultCellStyle.ForeColor = Paper;
        g.ColumnHeadersDefaultCellStyle.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);
        g.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.DisableResizing;
        g.ColumnHeadersHeight = 30;
        g.RowTemplate.Height = 28;
        g.GridColor = Color.FromArgb(214, 202, 176);
        g.DefaultCellStyle.SelectionBackColor = Gold;
        g.DefaultCellStyle.SelectionForeColor = Color.White;
        g.AlternatingRowsDefaultCellStyle.BackColor = Color.FromArgb(243, 237, 221);
        g.EditMode = DataGridViewEditMode.EditOnKeystrokeOrF2;
    }

    // shared numeric cell-validation for grids: reject non-numbers on numeric columns
    void WireNumericValidation(DataGridView g, HashSet<string> numericProps)
    {
        g.CellValidating += (s, e) =>
        {
            var col = g.Columns[e.ColumnIndex];
            if (col is DataGridViewTextBoxColumn tc && numericProps.Contains(tc.DataPropertyName))
            {
                string v = Convert.ToString(e.FormattedValue);
                if (!string.IsNullOrEmpty(v) && !int.TryParse(v, out _))
                {
                    g.Rows[e.RowIndex].ErrorText = "Numbers only";
                    e.Cancel = true;
                }
            }
        };
        g.CellEndEdit += (s, e) => g.Rows[e.RowIndex].ErrorText = "";
    }

    // ============================================================ POSSE TAB
    DataGridView posseGrid;
    NumericUpDown adjAmount;
    NumericUpDown dreadDc, dreadTier;

    TabPage BuildPosseTab()
    {
        var page = new TabPage("Posse") { BackColor = Paper };

        posseGrid = new DataGridView
        {
            Dock = DockStyle.Fill, AutoGenerateColumns = false, DataSource = party,
            AllowUserToAddRows = false, RowHeadersVisible = false,
            AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
            SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = false
        };
        StyleGrid(posseGrid);
        void Col(string prop, string head, int weight, bool ro = false)
            => posseGrid.Columns.Add(new DataGridViewTextBoxColumn
            { DataPropertyName = prop, HeaderText = head, FillWeight = weight, ReadOnly = ro });
        Col("Name", "Name", 155); Col("Calling", "Calling", 115); Col("Gender", "Gender", 70); Col("Level", "Lv", 40);
        Col("BloodCur", "Blood", 55); Col("BloodMax", "/Max", 50); Col("Defense", "Def", 45);
        Col("Fort", "Fort", 45); Col("Ref", "Ref", 45); Col("Will", "Will", 45);
        Col("NerveCur", "Nerve", 55); Col("NerveMax", "/Max", 50); Col("Grit", "Grit", 45);
        Col("PoolCur", "Pool", 46); Col("PoolMax", "/Max", 45);
        Col("Mark", "Mark", 48); Col("Taint", "Taint", 48); Col("Notes", "Notes", 140);
        // far-right Ledger button — one click to the soul's character sheet
        posseGrid.Columns.Add(new DataGridViewButtonColumn
        { HeaderText = "", Text = "Ledger", UseColumnTextForButtonValue = true, FillWeight = 60, Name = "ledgerBtn", ReadOnly = true });
        posseGrid.CellContentClick += (s, e) =>
        {
            if (e.RowIndex >= 0 && e.RowIndex < party.Count && posseGrid.Columns[e.ColumnIndex].Name == "ledgerBtn")
                ShowSoulCard(party[e.RowIndex]);
        };
        WireNumericValidation(posseGrid, new() { "Level","BloodCur","BloodMax","Defense","Fort","Ref","Will","NerveCur","NerveMax","Grit","PoolCur","PoolMax","Mark","Taint" });

        // current values can't outrun their maximums, whichever side of the pair was edited
        posseGrid.CellEndEdit += (s, e) =>
        {
            if (e.RowIndex < 0 || e.RowIndex >= party.Count) return;
            var p = party[e.RowIndex];
            if (p.BloodCur > p.BloodMax) p.BloodCur = p.BloodMax;
            if (p.NerveCur > p.NerveMax) p.NerveCur = p.NerveMax;
        };
        posseGrid.KeyDown += (s, e) =>
        {
            if (e.KeyCode == Keys.Delete && !posseGrid.IsCurrentCellInEditMode)
            { RemoveSelectedPC(); e.Handled = true; }
        };

        // double-click the Notes cell to read/edit the whole note; anywhere else on the
        // row opens the soul's Ledger in its own window (the Bestiary pop-out pattern)
        posseGrid.CellDoubleClick += (s, e) =>
        {
            if (e.RowIndex < 0 || e.RowIndex >= party.Count || e.ColumnIndex < 0) return;
            var p = party[e.RowIndex];
            var prop = (posseGrid.Columns[e.ColumnIndex] as DataGridViewTextBoxColumn)?.DataPropertyName;
            if (prop == "Notes") ExpandNotes(p);
            else ShowSoulCard(p);
        };
        Tip.SetToolTip(posseGrid, "Double-click a soul to open their Ledger — double-click the Notes cell to read the whole note, " +
            "right-click for everything that can be done to them");

        // Everything the bar above can do to one soul, on the soul itself. The row is selected by
        // GridMenu before this runs, so each line calls the very same handler the button does.
        GridMenu<PartyMember>(posseGrid, (menu, p) =>
        {
            MIHead(menu, p.Name is { Length: > 0 } ? p.Name : "This soul");
            MI(menu, "Open the Ledger", () => ShowSoulCard(p));
            MI(menu, "Read and edit the note…", () => ExpandNotes(p));
            MISep(menu);
            MI(menu, $"Damage {adjAmount.Value}", () => AdjustPC(-1));
            MI(menu, $"Heal {adjAmount.Value}", () => AdjustPC(+1));
            MI(menu, p.Grit > 0 ? $"Spend Grit  ({p.Grit} left)" : "Spend Grit — none left", () => SpendGrit(p), p.Grit > 0);
            MISep(menu);
            MI(menu, $"Dread check  (DC {dreadDc.Value}, Tier {dreadTier.Value})", () => DreadCheckPC(p));
            var steady = new ToolStripMenuItem("Steady — give Nerve back");
            steady.DropDownItems.Add("Confession, spoken plainly  (1d6)", null, (s, e) => Steady(false, "1d6", "makes confession"));
            steady.DropDownItems.Add("A night unmolested, in real safety  (1d6)", null, (s, e) => Steady(false, "1d6", "sleeps a night in real safety"));
            steady.DropDownItems.Add("Whiskey  (1d4 — and it courts a vice)", null, (s, e) => Steady(false, "1d4", "takes to the bottle"));
            steady.DropDownItems.Add("A week of true peace  (all of it)", null, (s, e) => Steady(false, null, "takes a week of true peace"));
            steady.DropDownItems.Add("Steady by hand…", null, (s, e) => SteadyByHand(false));
            menu.Items.Add(steady);
            MI(menu, "Long rest — Blood and Nerve to full", () => RestSoul(p));
            MISep(menu);
            MI(menu, p.Mark < 6 ? $"Mark +1  (step {p.Mark} of 6)" : "Mark is full at 6", () => AdvanceMark(p), p.Mark < 6);
            MI(menu, p.Taint < 4 ? $"Taint +1  ({p.Taint} of 4)" : "Taint is full at 4", () => DeepenTaint(p), p.Taint < 4);
            MI(menu, "Level up…", () => LevelUpMember(p, this));
            MISep(menu);
            MI(menu, "Send to the Tracker", () => AddSoulToTracker(p));
            MI(menu, "Move up the list", () => MovePC(-1), party.IndexOf(p) > 0);
            MI(menu, "Move down the list", () => MovePC(+1), party.IndexOf(p) < party.Count - 1);
            MI(menu, "Remove from the posse", () => RemoveSelectedPC());
        });

        // colour Blood/Nerve/Mark cells by danger so the Keeper can read the table at a glance
        posseGrid.CellFormatting += (s, e) =>
        {
            if (e.RowIndex < 0 || e.RowIndex >= party.Count) return;
            var p = party[e.RowIndex];
            string prop = (posseGrid.Columns[e.ColumnIndex] as DataGridViewTextBoxColumn)?.DataPropertyName;
            if (prop == "BloodCur")
            {
                double f = p.BloodMax == 0 ? 0 : (double)p.BloodCur / p.BloodMax;
                e.CellStyle.ForeColor = p.BloodCur == 0 ? Color.White : (f <= 0.34 ? Blood : Ink);
                e.CellStyle.BackColor = p.BloodCur == 0 ? Blood : (f <= 0.34 ? Color.FromArgb(248, 224, 224) : e.CellStyle.BackColor);
            }
            if (prop == "NerveCur")
            {
                double f = p.NerveMax == 0 ? 0 : (double)p.NerveCur / p.NerveMax;
                e.CellStyle.ForeColor = p.NerveCur == 0 ? Color.White : (f <= 0.34 ? Blood : Ink);
                e.CellStyle.BackColor = p.NerveCur == 0 ? Blood : (f <= 0.34 ? Color.FromArgb(250, 236, 224) : e.CellStyle.BackColor);
            }
            if (prop == "Mark" && p.Mark > 0)
            { e.CellStyle.ForeColor = p.Mark >= 6 ? Color.White : Blood; if (p.Mark >= 6) e.CellStyle.BackColor = Blood; e.Value = new string('●', p.Mark); }
            if (prop == "Taint" && p.Taint > 0)
            { e.CellStyle.ForeColor = Verdigris; e.Value = new string('●', p.Taint); }
        };

        // ---- action bar: inline amount spinner instead of pop-up prompts ----
        var bar = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(4), BackColor = Color.FromArgb(243, 237, 221) };

        bar.Controls.Add(Btn("＋ Add soul", (s, e) => { party.Add(new PartyMember()); posseGrid.CurrentCell = posseGrid.Rows[party.Count - 1].Cells[0]; }, 95, "Add a blank character to the posse"));
        bar.Controls.Add(Btn("✕ Remove", (s, e) => RemoveSelectedPC(), 90, "Remove the selected soul (or press Delete)"));
        bar.Controls.Add(Btn("▲", (s, e) => MovePC(-1), 38, "Move the selected soul up the list"));
        bar.Controls.Add(Btn("▼", (s, e) => MovePC(+1), 38, "Move the selected soul down the list"));
        bar.Controls.Add(Btn("✦ Level up", (s, e) => LevelUpMember(SelectedPC(), this), 90, "Advance the selected soul one level (New Soul–built souls only)"));

        bar.Controls.Add(Lbl("  Amount:"));
        adjAmount = new NumericUpDown { Minimum = 1, Maximum = 999, Value = 3, Width = 60, Margin = new Padding(3, 6, 3, 3) };
        Tip.SetToolTip(adjAmount, "How much Blood the Damage/Heal buttons apply");
        bar.Controls.Add(adjAmount);
        bar.Controls.Add(Btn("Damage", (s, e) => AdjustPC(-1), 80, "Subtract the Amount from the selected soul's Blood (Ctrl+D)"));
        bar.Controls.Add(Btn("Heal", (s, e) => AdjustPC(+1), 70, "Add the Amount to the selected soul's Blood (Ctrl+H)"));

        bar.Controls.Add(Btn("Spend Grit", (s, e) => SpendGrit(SelectedPC()), 90,
            "Spend one Grit (re-roll, refuse to fall at 0 Blood, shrug a fright)"));
        bar.Controls.Add(Btn("Mark +1", (s, e) => AdvanceMark(SelectedPC()), 75,
            "Advance the Mark one step (only when a soul CHOOSES the dark)"));
        bar.Controls.Add(Btn("Taint +1", (s, e) => DeepenTaint(SelectedPC()), 75,
            "Deepen the Taint of the Land one step"));

        // Dread on its own row with inline DC + tier
        bar.SetFlowBreak(bar.Controls[bar.Controls.Count - 1], true);
        bar.Controls.Add(Lbl("Dread DC:"));
        dreadDc = new NumericUpDown { Minimum = 1, Maximum = 40, Value = 13, Width = 55, Margin = new Padding(3, 6, 3, 3) };
        bar.Controls.Add(dreadDc);
        bar.Controls.Add(Lbl("Tier:"));
        dreadTier = new NumericUpDown { Minimum = 1, Maximum = 5, Value = 2, Width = 45, Margin = new Padding(3, 6, 3, 3) };
        Tip.SetToolTip(dreadTier, "Horror's Tier — sets the Nerve-loss ladder (1 / 1d4 / 1d6 / 1d10)");
        bar.Controls.Add(dreadTier);
        bar.Controls.Add(Btn("Dread check — selected", (s, e) => DreadCheckPC(SelectedPC()), 155, "Roll the selected soul's Will vs the Dread DC"));
        bar.Controls.Add(Btn("Dread check — whole posse", (s, e) => { foreach (var p in party.ToList()) DreadCheckPC(p); }, 175, "Roll every soul at once"));

        // Dread takes Nerve; something has to give it back. Until now the only ways were a long
        // rest or a new session — both of which do more than steady a soul, and neither of which
        // is named for Nerve, so a Keeper who had just spent it had nowhere obvious to go. These
        // are the Player's Book remedies (Ch. XII, "Recovering Nerve") in the order it prints them.
        bar.Controls.Add(MenuBtn("Steady ▾", 92, "Give Nerve back — the book's remedies, or straight to full",
            ("— The selected soul —", null),
            ("Confession, spoken plainly  (1d6)", (s, e) => Steady(false, "1d6", "makes confession")),
            ("A night unmolested, in real safety  (1d6)", (s, e) => Steady(false, "1d6", "sleeps a night in real safety")),
            ("Whiskey  (1d4 — and it courts a vice)", (s, e) => Steady(false, "1d4", "takes to the bottle")),
            ("A week of true peace  (all of it)", (s, e) => Steady(false, null, "takes a week of true peace")),
            ("Steady by hand…", (s, e) => SteadyByHand(false)),
            ("-", null),
            ("— The whole posse —", null),
            ("Confession, spoken plainly  (1d6 each)", (s, e) => Steady(true, "1d6", "makes confession")),
            ("A night unmolested, in real safety  (1d6 each)", (s, e) => Steady(true, "1d6", "sleeps a night in real safety")),
            ("Whiskey  (1d4 each — and it courts a vice)", (s, e) => Steady(true, "1d4", "takes to the bottle")),
            ("A week of true peace  (all of it)", (s, e) => Steady(true, null, "takes a week of true peace")),
            ("Steady by hand…", (s, e) => SteadyByHand(true))));

        bar.Controls.Add(Btn("New session", (s, e) =>
        {
            if (!Confirm("Start a new session? Refills every soul's Nerve and resets Grit to 3.")) return;
            foreach (var p in party) { p.NerveCur = p.NerveMax; p.Grit = 3; }
            Log("New session — Nerve refilled and Grit reset to 3 for the whole posse.");
        }, 100, "Refill Nerve and reset Grit for everyone"));
        bar.Controls.Add(MenuBtn("Rest ▾", 100, "A long rest — restore Blood and Nerve to full",
            ("Whole posse — heal to full", (s, e) => RestPosse()),
            ("Selected soul — heal to full", (s, e) => RestSoul(SelectedPC()))));
        bar.Controls.Add(Btn("Send posse → Tracker", (s, e) => PartyToTracker(), 155, "Put the whole posse onto the combat tracker"));
        bar.Controls.Add(Btn("Clear posse", (s, e) =>
        {
            if (party.Count == 0) { Log("The posse is already empty."); return; }
            if (!Confirm($"Clear the whole posse? Removes all {party.Count} soul(s) for a fresh start.")) return;
            party.Clear();
            Log("The posse is cleared — a fresh start.");
        }, 100, "Remove every soul and start fresh"));

        // The posse above, what they ride below — one deferred split, never geometry at
        // construction time (the SplitContainer landmine).
        var split = Split(Orientation.Horizontal, 180, 150, 0.62);
        split.Panel1.Controls.Add(posseGrid);
        split.Panel2.Controls.Add(BuildRidesPane());
        page.Controls.Add(split);
        page.Controls.Add(bar);
        Watermark(posseGrid, () => GridBottom(posseGrid));
        return page;
    }

    PartyMember SelectedPC() => posseGrid?.CurrentRow?.DataBoundItem as PartyMember;

    // reorder the posse: swap the selected soul with its neighbor and keep it selected
    void MovePC(int delta)
    {
        var p = SelectedPC();
        if (p == null) { Nope("Select a soul first."); return; }
        int i = party.IndexOf(p), j = i + delta;
        if (j < 0 || j >= party.Count) return;
        int col = posseGrid.CurrentCell?.ColumnIndex ?? 0;
        party.RaiseListChangedEvents = false;
        party.RemoveAt(i);
        party.Insert(j, p);
        party.RaiseListChangedEvents = true;
        party.ResetBindings();
        posseGrid.CurrentCell = posseGrid.Rows[j].Cells[col];
    }

    // the Notes column shows what fits in one cell; this shows (and edits) the whole note
    void ExpandNotes(PartyMember p)
    {
        using var f = new Form
        {
            Width = 520, Height = 380, Text = $"Notes — {p.Name}",
            StartPosition = FormStartPosition.CenterParent, MinimizeBox = false,
            ShowIcon = false, BackColor = Paper, MinimumSize = new Size(340, 240)
        };
        var box = new TextBox
        {
            Multiline = true, Dock = DockStyle.Fill, ScrollBars = ScrollBars.Vertical,
            Font = new Font("Segoe UI", 10.5f), Text = p.Notes, BorderStyle = BorderStyle.None,
            BackColor = Color.FromArgb(252, 249, 240), WordWrap = true
        };
        var bar = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 44, FlowDirection = FlowDirection.RightToLeft, Padding = new Padding(6) };
        var cancel = new Button { Text = "Cancel", Width = 84, Height = 30, DialogResult = DialogResult.Cancel };
        var ok = new Button { Text = "Save", Width = 84, Height = 30, DialogResult = DialogResult.OK };
        bar.Controls.Add(cancel); bar.Controls.Add(ok);
        f.Controls.Add(Pad(box, 10)); f.Controls.Add(bar);
        f.AcceptButton = null; f.CancelButton = cancel;          // Enter stays a newline in the note
        if (f.ShowDialog(this) == DialogResult.OK && box.Text != p.Notes)
        {
            p.Notes = box.Text;
            posseGrid?.Refresh();
            Log($"{p.Name}'s notes updated.");
        }
    }

    void RemoveSelectedPC()
    {
        var p = SelectedPC(); if (p == null) return;
        if (Confirm($"Remove {p.Name} from the posse?")) party.Remove(p);
    }

    void AdjustPC(int sign)
    {
        var p = SelectedPC();
        if (p == null) { Nope("Select a soul first."); return; }
        int v = (int)adjAmount.Value;
        p.BloodCur = Math.Clamp(p.BloodCur + sign * v, 0, p.BloodMax);
        Log($"{p.Name} {(sign < 0 ? "takes" : "recovers")} {v} Blood → {p.BloodCur}/{p.BloodMax}" + (p.BloodCur == 0 ? "  — DOWN." : ""));
        MirrorToTracker(p);
    }

    void DreadCheckPC(PartyMember p)
    {
        if (p == null) { Nope("Select a soul first."); return; }
        int dc = (int)dreadDc.Value, tier = (int)dreadTier.Value;
        int die = Rules.Rng.Next(1, 21);
        var (idx, deg, detail) = Rules.FourDegrees(die, p.Will, dc);
        if (idx <= 1)                                       // 0 = crit fail, 1 = fail
        {
            bool crit = idx == 0;
            var (label, roll) = Rules.NerveLoss(tier);
            int loss = roll();
            if (crit) loss *= 2;
            p.NerveCur = Math.Max(0, p.NerveCur - loss);
            Log($"DREAD — {p.Name}: {detail} → {deg}. −{loss} Nerve ({label}{(crit ? " ×2" : "")}) → {p.NerveCur}/{p.NerveMax}" + (p.NerveCur == 0 ? "  — BREAKS." : ""));
        }
        else Log($"DREAD — {p.Name}: {detail} → {deg}. Holds their nerve.");
    }

    // A long rest heals the body and steadies the mind: Blood and Nerve back to full.
    // The Mark and Taint do not wash off with rest, so they're left alone.
    void RestPosse()
    {
        if (party.Count == 0) return;
        if (!Confirm("A long rest for the whole posse? Restores every soul's Blood, Nerve, and pool to full.")) return;
        foreach (var p in party) { p.BloodCur = p.BloodMax; p.NerveCur = p.NerveMax; p.PoolCur = p.PoolMax; MirrorToTracker(p); }
        posseGrid?.Refresh();
        Log("The posse takes a long rest — Blood, Nerve, and the day's pool restored to full.");
    }

    void RestSoul(PartyMember p)
    {
        if (p == null) { Nope("Select a soul first."); return; }
        p.BloodCur = p.BloodMax; p.NerveCur = p.NerveMax; p.PoolCur = p.PoolMax;
        MirrorToTracker(p); posseGrid?.Refresh();
        Log($"{p.Name} rests — Blood, Nerve, and pool restored to full.");
    }

    /// <summary>Give Nerve back. <paramref name="expr"/> is the remedy's die (rolled fresh per soul,
    /// the way the table reads) or null for "all of it". Nothing here touches Blood, the Mark, or
    /// the Taint — steadying a soul is not healing one, and the book is careful about the difference.</summary>
    // The three one-step marks a soul can take. Methods rather than button lambdas so the buttons
    // on the bar and the lines in the row's right-click menu are literally the same code — a menu
    // that reimplements what a button does is a menu that will one day disagree with it.
    void SpendGrit(PartyMember p)
    {
        if (p == null) return;
        if (p.Grit > 0) { p.Grit--; Log($"{p.Name} spends Grit ({p.Grit} left)."); }
        else Log($"{p.Name} has no Grit left to spend.");
    }

    void AdvanceMark(PartyMember p)
    {
        if (p == null) return;
        p.Mark = Math.Min(6, p.Mark + 1);
        Log($"{p.Name}'s Mark advances to step {p.Mark} of 6." + (p.Mark >= 6 ? "  THE MARK IS FULL — the country collects." : ""));
    }

    void DeepenTaint(PartyMember p)
    {
        if (p == null) return;
        p.Taint = Math.Min(4, p.Taint + 1);
        Log($"{p.Name}'s Taint deepens to {p.Taint} of 4.");
    }

    void Steady(bool wholePosse, string expr, string doing)
    {
        var who = wholePosse ? party.ToList() : new List<PartyMember> { SelectedPC() };
        if (wholePosse && who.Count == 0) { Nope("No souls in the posse yet."); return; }
        if (who[0] == null) { Nope("Select a soul first."); return; }

        foreach (var p in who)
        {
            int before = p.NerveCur;
            if (expr == null) p.NerveCur = p.NerveMax;
            else p.NerveCur = Math.Min(p.NerveMax, p.NerveCur + Rules.RollExpr(expr).total);
            int back = p.NerveCur - before;
            Log(back == 0
                ? $"{p.Name} {doing} — Nerve already steady at {p.NerveCur}/{p.NerveMax}."
                : $"{p.Name} {doing} — +{back} Nerve → {p.NerveCur}/{p.NerveMax}.");
        }
        posseGrid?.Refresh();
        // No CaptureUndo here: party is a BindingList of INotifyPropertyChanged souls, so setting
        // NerveCur already raises ListChanged, and CaptureUndo coalesces the whole posse's worth
        // into one step. Same reason RestPosse/RestSoul don't call it either.
    }

    /// <summary>The escape hatch for a remedy the book doesn't print — a Sawbones' reason, a sermon,
    /// a grim joke. The Keeper says how much steadiness it was worth.</summary>
    void SteadyByHand(bool wholePosse)
    {
        var who = wholePosse ? party.ToList() : new List<PartyMember> { SelectedPC() };
        if (wholePosse && who.Count == 0) { Nope("No souls in the posse yet."); return; }
        if (who[0] == null) { Nope("Select a soul first."); return; }

        string ans = AskLine(wholePosse ? "How much Nerve does each soul get back?" : "How much Nerve comes back?", "3");
        if (!int.TryParse(ans?.Trim(), out int amt) || amt <= 0) return;

        foreach (var p in who)
        {
            int before = p.NerveCur;
            p.NerveCur = Math.Min(p.NerveMax, p.NerveCur + amt);
            Log($"{p.Name} steadies — +{p.NerveCur - before} Nerve → {p.NerveCur}/{p.NerveMax}.");
        }
        posseGrid?.Refresh();
    }

    void PartyToTracker()
    {
        int added = party.Count(p => AddSoulToTracker(p, quiet: true));
        Log($"Sent {added} soul(s) to the tracker.");
    }

    /// <summary>Put one soul on the field, unless they're already standing on it. Answers whether a
    /// row was actually added, which is what lets <see cref="PartyToTracker"/> count honestly.</summary>
    bool AddSoulToTracker(PartyMember p, bool quiet = false)
    {
        if (p == null || tracker.Any(t => t.IsSoul(p)))
        {
            if (!quiet && p != null) Log($"{p.Name} is already on the field.");
            return false;
        }
        tracker.Add(new Combatant
        { Name = p.Name, PcId = p.Id, IsPC = true, BloodCur = p.BloodCur, BloodMax = p.BloodMax, Defense = p.Defense });
        if (!quiet) Log($"{p.Name} takes the field.");
        return true;
    }

    void MirrorToTracker(PartyMember p)
    {
        var c = tracker.FirstOrDefault(t => t.IsSoul(p));
        if (c != null)
        {
            if (string.IsNullOrEmpty(c.PcId)) c.PcId = p.Id;   // adopt the id on a legacy row
            c.Name = p.Name;                                    // keep the tracker label in step with a rename
            c.BloodCur = p.BloodCur; c.BloodMax = p.BloodMax;
            trkGrid?.Refresh();
        }
    }

    // ============================================================ DICE TAB
    TextBox exprBox;
    NumericUpDown exprQty;

    // Every die wears its own color — buttons and the tumbling tray alike — so the
    // Keeper can tell a d8 from a d12 across the table without reading the tag.
    static (Color face, Color text) DieCol(int sides) => sides switch
    {
        4   => (Color.FromArgb(72, 132, 72),  Color.White),                  // green
        6   => (Color.FromArgb(62, 104, 158), Color.White),                  // blue
        8   => (Color.FromArgb(214, 126, 44), Color.White),                  // orange
        10  => (Color.FromArgb(250, 248, 242), Ink),                         // white
        12  => (Color.FromArgb(232, 196, 62), Ink),                          // yellow
        20  => (Color.FromArgb(172, 36, 36),  Color.White),                  // red
        100 => (Color.FromArgb(122, 72, 152), Color.White),                  // purple
        _   => (Color.FromArgb(252, 249, 240), Ink)
    };

    static Color Darken(Color c, double f = 0.72)
        => Color.FromArgb((int)(c.R * f), (int)(c.G * f), (int)(c.B * f));

    // a die button in its die's color (FlatStyle.Flat — the System style ignores BackColor)
    static Button DieBtn(string text, int sides, EventHandler onClick, int w, string tip = null)
    {
        var (face, fore) = DieCol(sides);
        var b = new Button
        {
            Text = text, Width = w, Height = 32, Margin = new Padding(3),
            FlatStyle = FlatStyle.Flat, BackColor = face, ForeColor = fore,
            Font = new Font("Segoe UI", 9.5f, FontStyle.Bold), UseVisualStyleBackColor = false
        };
        b.FlatAppearance.BorderColor = Darken(face);
        b.FlatAppearance.BorderSize = 1;
        b.Click += onClick;
        if (tip != null) Tip.SetToolTip(b, tip);
        return b;
    }

    // ---- dice animation: the dice tumble in the tray, then land on the real results ----
    sealed class DiceTray : Panel
    {
        public List<(int sides, int value, int sign)> Dice = new();
        public bool Settled = true;
        public DiceTray() { DoubleBuffered = true; ResizeRedraw = true; }
    }
    DiceTray diceTray;
    System.Windows.Forms.Timer diceTimer;
    int diceTick;
    const int DiceTicks = 14;                 // ~half a second of tumble at 40 ms
    const int DiceShownMax = 8;               // a 100-die roll shows 8 and says so

    // paint runs ~25×/second during a tumble — keep the fonts, don't mint GDI handles per frame
    static readonly Font DieNumFont  = new("Consolas", 15f, FontStyle.Bold);
    static readonly Font DieTagFont  = new("Segoe UI", 7.5f);
    static readonly Font DieHintFont = new("Segoe UI", 9.5f, FontStyle.Italic);
    static readonly Font DieMoreFont = new("Segoe UI", 8.5f, FontStyle.Italic);

    void AnimateDice(List<(int sides, int value, int sign)> dice)
    {
        if (diceTray == null || dice == null || dice.Count == 0) return;
        diceTray.Dice = dice;
        diceTray.Settled = false;
        diceTick = 0;
        diceTimer.Stop();
        diceTimer.Start();
        diceTray.Invalidate();
    }

    void PaintDiceTray(object s, PaintEventArgs e)
    {
        var g = e.Graphics;
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
        if (diceTray.Dice.Count == 0)
        {
            TextRenderer.DrawText(g, "The dice land here.", DieHintFont,
                diceTray.ClientRectangle, Gold, TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
            return;
        }
        int shown = Math.Min(diceTray.Dice.Count, DiceShownMax);
        int size = 52, gap = 10;
        int x = Math.Max(8, (diceTray.Width - shown * (size + gap)) / 2), y = (diceTray.Height - size) / 2 - 4;
        for (int i = 0; i < shown; i++)
        {
            var (sides, value, sign) = diceTray.Dice[i];
            var (faceCol, textCol) = DieCol(sides);
            int show = diceTray.Settled ? value : Rules.Rng.Next(1, sides + 1);
            var rect = new Rectangle(x + i * (size + gap), y, size, size);
            // a little jitter while tumbling, stillness once landed
            if (!diceTray.Settled) rect.Offset(Rules.Rng.Next(-2, 3), Rules.Rng.Next(-2, 3));
            using var path = RoundedRect(rect, 9);
            using var face = new SolidBrush(faceCol);
            g.FillPath(face, path);
            // the faces carry the die colors now, so the verdicts ring in metal instead:
            // best face a bright gold, a 1 near-black — both read on every face color
            Color edge = !diceTray.Settled ? Gold
                       : show == sides ? Color.FromArgb(255, 208, 74)     // best face
                       : show == 1 && sides >= 6 ? Color.FromArgb(28, 20, 14)   // worst face
                       : Darken(faceCol);
            using var pen = new Pen(edge, diceTray.Settled && (show == sides || (show == 1 && sides >= 6)) ? 3f : 1.6f);
            g.DrawPath(pen, path);
            TextRenderer.DrawText(g, show.ToString(), DieNumFont,
                new Rectangle(rect.X, rect.Y - 4, rect.Width, rect.Height), textCol,
                TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
            TextRenderer.DrawText(g, (sign < 0 ? "−d" : "d") + sides, DieTagFont,
                new Rectangle(rect.X, rect.Bottom - 17, rect.Width, 15),
                textCol, TextFormatFlags.HorizontalCenter);   // GDI text is opaque — no alpha tricks
        }
        if (diceTray.Dice.Count > shown)
            TextRenderer.DrawText(g, $"+{diceTray.Dice.Count - shown} more", DieMoreFont,
                new Rectangle(diceTray.Width - 78, diceTray.Height - 22, 74, 18), Gold, TextFormatFlags.Right);
    }

    static System.Drawing.Drawing2D.GraphicsPath RoundedRect(Rectangle r, int rad)
    {
        var p = new System.Drawing.Drawing2D.GraphicsPath();
        int d = rad * 2;
        p.AddArc(r.X, r.Y, d, d, 180, 90);
        p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
        p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
        p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
        p.CloseFigure();
        return p;
    }

    TabPage BuildDiceTab()
    {
        var page = new TabPage("Dice") { BackColor = Paper };
        var split = Split(Orientation.Vertical, 380, 260, 0.42);

        var left = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.TopDown, WrapContents = false, Padding = new Padding(12), BackColor = Paper };

        left.Controls.Add(Heading("Roll an expression"));
        left.Controls.Add(Lbl("e.g.  2d6+3   ·   d20   ·   1d8+1d6+2"));
        var exprRow = new FlowLayoutPanel { AutoSize = true };
        exprBox = new TextBox { Width = 250, Text = "1d20", Font = new Font("Consolas", 11f) };
        exprBox.KeyDown += (s, e) => { if (e.KeyCode == Keys.Enter) { RollExprBox(); e.SuppressKeyPress = true; } };
        exprRow.Controls.Add(exprBox);
        exprRow.Controls.Add(Btn("Roll", (s, e) => RollExprBox(), 80, "Roll the expression (or press Enter)"));
        left.Controls.Add(exprRow);

        // build the expression by button: dice stack (d6 → 2d6 → 3d6), the × spinner
        // adds several at once (× 4 then +d6 → 4d6), digits and ＋/− make the
        // modifier — no typing needed at the table
        var dicePad = new FlowLayoutPanel { AutoSize = true, MaximumSize = new Size(470, 0) };
        dicePad.Controls.Add(Lbl("×"));
        exprQty = new NumericUpDown { Minimum = 1, Maximum = 99, Value = 1, Width = 46, Margin = new Padding(0, 6, 4, 3) };
        Tip.SetToolTip(exprQty, "How many dice each +d button adds — set 4 and click +d6 for 4d6");
        dicePad.Controls.Add(exprQty);
        foreach (int d in new[] { 4, 6, 8, 10, 12, 20, 100 })
        {
            int sides = d;
            dicePad.Controls.Add(DieBtn("+d" + sides, sides, (s, e) => ExprAddDie(sides), sides == 100 ? 64 : 54,
                $"Add ×-many d{sides} to the expression — click again for more"));
        }
        left.Controls.Add(dicePad);
        var opsPad = new FlowLayoutPanel { AutoSize = true, MaximumSize = new Size(430, 0) };
        opsPad.Controls.Add(Btn("＋", (s, e) => ExprAppend("+"), 40, "Plus"));
        opsPad.Controls.Add(Btn("−", (s, e) => ExprAppend("-"), 40, "Minus"));
        foreach (int n in new[] { 1, 2, 3, 4, 5, 6, 7, 8, 9, 0 })
        {
            int digit = n;
            opsPad.Controls.Add(Btn(digit.ToString(), (s, e) => ExprAppend(digit.ToString()), 40,
                $"Type {digit} into the modifier"));
        }
        opsPad.Controls.Add(Btn("⌫", (s, e) =>
        { if (exprBox.TextLength > 0) exprBox.Text = exprBox.Text[..^1]; ExprFocusEnd(); }, 40, "Backspace"));
        opsPad.Controls.Add(Btn("C", (s, e) => { exprBox.Clear(); ExprFocusEnd(); }, 40, "Clear the expression"));
        left.Controls.Add(opsPad);

        left.Controls.Add(Heading("Quick dice — roll one now"));
        var quick = new FlowLayoutPanel { AutoSize = true, MaximumSize = new Size(430, 0) };
        foreach (int d in new[] { 4, 6, 8, 10, 12, 20, 100 })
            quick.Controls.Add(DieBtn("d" + d, d, (s, e) =>
            {
                int r = Rules.Rng.Next(1, d + 1);
                AnimateDice(new() { (d, r, 1) });
                Log($"d{d} → {r}");
                ShowResult(r.ToString(), $"one d{d}" + (r == d ? " — the best face" : r == 1 ? " — a one" : ""),
                    r == d ? RollCritGood : r == 1 ? RollCritBad : RollNeutral);
            }, 54, $"Roll one d{d} now"));
        left.Controls.Add(quick);

        left.Controls.Add(Heading("The d20 check — four degrees"));
        var modBox = new NumericUpDown { Minimum = -20, Maximum = 40, Value = 4, Width = 60 };
        var dcBox = new NumericUpDown { Minimum = 1, Maximum = 50, Value = 13, Width = 60 };
        var checkRow = new FlowLayoutPanel { AutoSize = true };
        checkRow.Controls.Add(Lbl("Modifier:")); checkRow.Controls.Add(modBox);
        checkRow.Controls.Add(Lbl("   DC:")); checkRow.Controls.Add(dcBox);
        checkRow.Controls.Add(Btn("Check!", (s, e) =>
        {
            int die = Rules.Rng.Next(1, 21);
            var (_, deg, det) = Rules.FourDegrees(die, (int)modBox.Value, (int)dcBox.Value);
            AnimateDice(new() { (20, die, 1) });
            Log($"CHECK — {det} → {deg}");
            ShowResult(deg, det, DegreeColor(deg));
        }, 84, "Roll a d20 against the DC and read the four degrees"));
        left.Controls.Add(checkRow);
        left.Controls.Add(Lbl("Beat the DC by 10 (or nat 20) → critical success."));
        left.Controls.Add(Lbl("Miss by 10 (or nat 1) → critical failure."));

        rollLog = new ListBox { Dock = DockStyle.Fill, Font = new Font("Consolas", 9.5f), HorizontalScrollbar = true, BackColor = Color.FromArgb(252, 249, 240), BorderStyle = BorderStyle.None };
        StyleRollLog(rollLog);
        // Catch the view up on everything logged before this tab was first opened.
        if (logLines.Count > 0)
        {
            rollLog.BeginUpdate();
            foreach (var line in logLines) rollLog.Items.Add(line);
            int widest = logLines.Max(l => TextRenderer.MeasureText(l, rollLog.Font).Width) + 16;
            if (widest > rollLog.HorizontalExtent) rollLog.HorizontalExtent = widest;
            rollLog.EndUpdate();
        }
        var right = new Panel { Dock = DockStyle.Fill, Padding = new Padding(10) };
        var logHead = new Label { Text = "  Roll & event log", UseMnemonic = false, Dock = DockStyle.Top, Height = 26, Font = new Font("Segoe UI", 10f, FontStyle.Bold), ForeColor = Blood, TextAlign = ContentAlignment.MiddleLeft };

        // The last roll, said loud. The log is the record and the tray shows the dice, but the
        // one thing a Keeper actually wants — what did it come to, and did it beat the DC — was
        // a line of 9pt monospace among four hundred others (user-reported). It now gets its own
        // card at the top of the pane, in the same colors the log grades by.
        resultCard = new Panel { Dock = DockStyle.Top, Height = 92, BackColor = Color.FromArgb(252, 249, 240), Padding = new Padding(12, 6, 12, 6) };
        resultSub = new Label { Dock = DockStyle.Bottom, Height = 22, ForeColor = Ink, Font = new Font("Segoe UI", 9.5f), TextAlign = ContentAlignment.MiddleLeft, UseMnemonic = false };
        resultBig = new Label { Dock = DockStyle.Fill, ForeColor = Ink, Font = new Font("Segoe UI", 30f, FontStyle.Bold), TextAlign = ContentAlignment.MiddleLeft, UseMnemonic = false };
        resultCard.Controls.Add(resultBig);
        resultCard.Controls.Add(resultSub);
        resultCard.Paint += (s, e) =>          // a hairline under the card, so it reads as its own thing
        {
            using var p = new Pen(Color.FromArgb(196, 181, 148), 1f);
            e.Graphics.DrawLine(p, 0, resultCard.Height - 1, resultCard.Width, resultCard.Height - 1);
        };
        ShowResult("—", "Roll something and the result lands here.", Ink);

        diceTray = new DiceTray { Dock = DockStyle.Top, Height = 84, BackColor = Color.FromArgb(243, 237, 221) };
        diceTray.Paint += PaintDiceTray;
        diceTimer = new System.Windows.Forms.Timer { Interval = 40 };
        diceTimer.Tick += (s, e) =>
        {
            if (++diceTick >= DiceTicks)
            {
                diceTimer.Stop();
                diceTray.Settled = true;
            }
            diceTray.Invalidate();
        };

        var logBar = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 40 };
        logBar.Controls.Add(Btn("Copy log", (s, e) => { if (rollLog.Items.Count > 0) Clipboard.SetText(string.Join(Environment.NewLine, rollLog.Items.Cast<object>())); }, 90,
            "Copy every line of the log to the clipboard"));
        logBar.Controls.Add(Btn("Clear log", (s, e) =>
        {
            if (rollLog.Items.Count == 0) return;
            if (Confirm($"Clear all {rollLog.Items.Count} log line(s)? This can't be undone."))
            { rollLog.Items.Clear(); logLines.Clear(); }
        }, 90, "Wipe the log — the rolls themselves are already spent"));
        Tip.SetToolTip(rollLog, "Right-click a line to copy it, or the whole log");

        // A log line isn't a thing that can be acted on so much as one the Keeper wants OUT — into
        // a chat window, into notes. The menu is exactly the two Copy paths plus the Clear the bar
        // below already offers, so no reader has to hunt for the button.
        ListMenu<string>(rollLog, (menu, line) =>
        {
            MI(menu, "Copy this line", () => Clipboard.SetText(line));
            MI(menu, $"Copy the whole log  ({rollLog.Items.Count} lines)",
                () => Clipboard.SetText(string.Join(Environment.NewLine, rollLog.Items.Cast<object>())));
            MISep(menu);
            MI(menu, "Clear the log", () =>
            {
                if (Confirm($"Clear all {rollLog.Items.Count} log line(s)? This can't be undone."))
                { rollLog.Items.Clear(); logLines.Clear(); }
            });
        });

        // Added last among the top-docked children, so the card sits above the heading and the tray.
        right.Controls.Add(rollLog); right.Controls.Add(diceTray); right.Controls.Add(logHead);
        right.Controls.Add(resultCard); right.Controls.Add(logBar);

        split.Panel1.Controls.Add(left);
        split.Panel2.Controls.Add(right);
        page.Controls.Add(split);
        Watermark(left, () => FlowBottom(left));
        return page;
    }

    void ExprFocusEnd()
    {
        exprBox.Focus();
        exprBox.SelectionStart = exprBox.TextLength;
    }

    // the builder logic itself lives in Rules (pure, smoke-tested); these just wire the box
    void ExprAddDie(int sides)
    {
        exprBox.Text = Rules.ExprAddDie(exprBox.Text, sides, (int)(exprQty?.Value ?? 1));
        ExprFocusEnd();
    }

    void ExprAppend(string s)
    {
        exprBox.Text = Rules.ExprAppend(exprBox.Text, s);
        ExprFocusEnd();
    }

    void RollExprBox()
    {
        var (t, br, dice) = Rules.RollExprFull(exprBox.Text);
        if (br == "could not parse" || br == "empty")
        {
            Nope($"Couldn't read \"{exprBox.Text}\" — try something like 2d6+3.");
            ShowResult("?", $"Couldn't read \"{exprBox.Text}\" — try something like 2d6+3.", Blood);
            return;
        }
        AnimateDice(dice);
        Log($"ROLL {exprBox.Text} → {t}   ({br})");
        ShowResult(t.ToString(), br, RollNeutral);   // the breakdown already names the dice
    }

    // ---------------------------------------------------------- dialogs
    static bool Confirm(string msg) =>
        MessageBox.Show(msg, "Blood & Grit", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes;

    // ---------------------------------------------------------- persistence
    string SavePath => Path.Combine(AppContext.BaseDirectory, "session.json");

    GameSession Snapshot() => new()
    {
        // ?? the field, never ?? a default: an unbuilt tab means "not shown yet", not "empty".
        Party = party.ToList(), Clocks = clocks.ToList(), Notes = notesBox?.Text ?? notesText,
        EncounterCreatures = encounter.Select(x => x.Creature.name).ToList(),
        PartyLevelHint = (int)(encLevel?.Value ?? partyLevelHint),
        Tracker = tracker.ToList(), Round = round,
        MapMarkers = mapMarkers.ToList(),
        Rides = rides.ToList()
    };

    // Write the session WHOLE or not at all. WriteAllText truncates the file and then fills
    // it, so anything that interrupts the write — the five-minute timer firing as the machine
    // sleeps, a kill, a power cut, and above all Crash(), which calls this while the process
    // is already coming apart — leaves a half-written session.json on disk. TryAutoLoad can't
    // parse that, and its fallback is SeedDemo(), so a torn write doesn't merely lose the last
    // few minutes: it silently replaces the Keeper's whole table with the demo posse. Staging
    // to a sibling file and moving it over is a single filesystem operation on NTFS, so the
    // old session survives intact until the new one is complete on disk.
    internal void AutoSave()
    {
        try
        {
            string json = JsonSerializer.Serialize(Snapshot(), new JsonSerializerOptions { WriteIndented = true });
            string staged = SavePath + ".new";
            File.WriteAllText(staged, json);
            File.Move(staged, SavePath, overwrite: true);
        }
        catch { /* never block closing */ }
    }

    // Replace the whole table with a saved session — the shared road for the startup
    // auto-load and File → Load session.
    void ApplySession(GameSession s)
    {
        bool prevSuppress = suppressUndo;
        suppressUndo = true;                  // the whole-table rebuild below is one event, not N
        try
        {
            // Every soul in the table is about to be replaced by a freshly deserialized
            // object. The open Ledger pop-outs are keyed on the OLD PartyMember instances,
            // so left alone they'd show a soul that no longer exists, refuse to refresh,
            // and hold their dictionary entries forever. Close them with the table.
            foreach (var w in soulWindows.Values.ToList())
                if (!w.IsDisposed) w.Close();
            soulWindows.Clear();

            party.Clear(); clocks.Clear(); encounter.Clear(); tracker.Clear(); rides.Clear();
            foreach (var p in s.Party ?? new()) party.Add(p);
            foreach (var c in s.Clocks ?? new()) clocks.Add(c);
            notesText = s.Notes ?? "";
            if (notesBox != null) notesBox.Text = notesText;
            foreach (var n in s.EncounterCreatures ?? new())
            { var c = Db.Find(n); if (c != null) encounter.Add(new EncounterPick(c)); }
            if (s.PartyLevelHint >= 1)
            {
                partyLevelHint = Math.Clamp(s.PartyLevelHint, 1, 10);
                if (encLevel != null) encLevel.Value = partyLevelHint;
            }
            foreach (var c in s.Tracker ?? new()) tracker.Add(c);   // a fight in progress survives a restart
            round = Math.Max(1, s.Round);
            if (roundLbl != null) roundLbl.Text = $"Round {round}";
            foreach (var r in s.Rides ?? new()) rides.Add(r);      // the corral survives a restart too
            mapMarkers.Clear();
            mapMarkers.AddRange(s.MapMarkers ?? new());
            mapPanel?.Invalidate();
            RefreshClocks(); RefreshEncounter();
            posseGrid?.Refresh(); trkGrid?.Refresh();
        }
        finally { suppressUndo = prevSuppress; }
        undoBaseline = JsonSerializer.Serialize(Snapshot());   // re-synced whichever path called this
    }

    // ---------------------------------------------------------- universal undo/redo
    // Snapshot-based over the same GameSession shape File → Save/Load already uses:
    // simple, and correct-by-construction since round-tripping through JSON gives a
    // true deep copy (the in-memory Snapshot() lists share references, which is fine
    // for serializing but not for stashing a past state to restore later).
    bool undoCapturePending;

    void CaptureUndo()
    {
        if (suppressUndo || undoCapturePending) return;
        // Coalesce: one user action can fan out into several list events (a Damage
        // click edits the posse AND mirrors to the tracker; New Session touches every
        // soul twice; Send posse → Tracker adds N rows). Deferring the capture to
        // after the current message settles makes each action exactly ONE undo step,
        // and never snapshots a half-synced intermediate state.
        if (!IsHandleCreated) { CaptureUndoNow(); return; }
        undoCapturePending = true;
        BeginInvoke(new Action(() => { undoCapturePending = false; CaptureUndoNow(); }));
    }

    void CaptureUndoNow()
    {
        if (suppressUndo) return;
        string now = JsonSerializer.Serialize(Snapshot());
        if (now == undoBaseline) return;
        undoStack.Add(undoBaseline);
        if (undoStack.Count > UndoDepth) undoStack.RemoveAt(0);
        undoBaseline = now;
        redoStack.Clear();
        RefreshUndoRedoButtons();
    }

    // Ctrl+Z pressed while typing belongs to the text field, not the table — the menu
    // shortcut would otherwise intercept it before the field's native undo ever fires.
    Control DeepActive()
    {
        Control a = ActiveControl;
        while (a is ContainerControl cc && cc.ActiveControl != null) a = cc.ActiveControl;
        return a;
    }

    bool GridEditing =>
        posseGrid?.IsCurrentCellInEditMode == true || trkGrid?.IsCurrentCellInEditMode == true;

    void Undo()
    {
        if (DeepActive() is TextBoxBase tb && tb.CanUndo) { tb.Undo(); return; }
        if (GridEditing) return;                    // don't yank the table out from under a cell editor
        if (undoStack.Count == 0) return;
        redoStack.Add(undoBaseline);
        string target = undoStack[^1]; undoStack.RemoveAt(undoStack.Count - 1);
        ApplySession(JsonSerializer.Deserialize<GameSession>(target));
        Log("Undo.");
        RefreshUndoRedoButtons();
    }

    void Redo()
    {
        var f = DeepActive();
        if (f is RichTextBox rtb && rtb.CanRedo) { rtb.Redo(); return; }
        if (f is TextBoxBase) return;               // a plain TextBox has no redo; leave the typist alone
        if (GridEditing) return;
        if (redoStack.Count == 0) return;
        undoStack.Add(undoBaseline);
        string target = redoStack[^1]; redoStack.RemoveAt(redoStack.Count - 1);
        ApplySession(JsonSerializer.Deserialize<GameSession>(target));
        Log("Redo.");
        RefreshUndoRedoButtons();
    }

    void RefreshUndoRedoButtons()
    {
        if (undoMenuItem != null) undoMenuItem.Enabled = undoStack.Count > 0;
        if (redoMenuItem != null) redoMenuItem.Enabled = redoStack.Count > 0;
        if (undoStatusBtn != null) undoStatusBtn.Enabled = undoStack.Count > 0;
        if (redoStatusBtn != null) redoStatusBtn.Enabled = redoStack.Count > 0;
    }

    void TryAutoLoad()
    {
        if (!File.Exists(SavePath)) { SeedDemo(); return; }
        try
        {
            var s = JsonSerializer.Deserialize<GameSession>(File.ReadAllText(SavePath));
            if (s == null || s.Party.Count == 0) { SeedDemo(); return; }
            ApplySession(s);
        }
        catch (Exception ex)
        {
            // An unreadable session used to be swallowed and papered over with the demo
            // posse, which then autosaved on exit — the Keeper's table quietly gone for
            // good. Set the bad file aside under a name nothing else writes, and say so.
            string kept = Path.Combine(AppContext.BaseDirectory, "session-unreadable.json");
            try { File.Move(SavePath, kept, overwrite: true); } catch { kept = SavePath; }
            MessageBox.Show(
                "GritKeeper couldn't read the saved session:\r\n\r\n" + ex.Message +
                "\r\n\r\nThe file has been set aside as\r\n" + kept +
                "\r\nso nothing is lost, and the table starts from the ready-made posse. " +
                "If the file looks salvageable, File → Load session will take it back.",
                "Blood & Grit — GritKeeper", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            if (party.Count == 0) SeedDemo();
        }
    }

    void SeedDemo()
    {
        // The ready-made posse from Appendix D, so the app is useful on first launch — now
        // seeded as full, rules-legal character sheets (Ledger, Signs, gear and all), not bare
        // rows. A fixed seed makes the first-launch posse identical for everyone; ReseedEntropy
        // afterward hands play back its unpredictable dice. Generate() (not Assemble — that
        // throws on a null Origin) with a fixed Calling, then the pregen's own name and gender.
        Rules.Reseed(0x5EEDA117);
        void Add(string name, string gender, string calling)
        {
            var s = CharGen.Generate(1, rolled: false, fixedCalling: calling);
            s.Name = name; s.Gender = gender;
            var p = new PartyMember
            {
                Name = s.Name, Calling = s.Calling, Gender = s.Gender, Level = s.Level,
                BloodMax = s.Blood, BloodCur = s.Blood, Defense = s.Defense,
                Fort = s.Fort, Ref = s.Ref, Will = s.Will,
                RES = s.Scores["RES"], Grit = s.Grit, Mark = s.Mark,
                Notes = s.Origin + (s.Subpath != null ? " · " + s.Subpath : "")
                                 + (CharGen.ArmorLine(s) is { Length: > 0 } a ? " · " + a : ""),
                Sheet = s
            };
            if (p.NerveMax != s.NerveMax) { p.NerveMax = s.NerveMax; p.NerveCur = s.NerveMax; }   // Stone Nerve
            p.PoolName = s.PoolName ?? ""; p.PoolMax = s.PoolMax; p.PoolCur = s.PoolMax;           // faith/sign pool, full
            party.Add(p);
        }
        Add("Ruth \"Six-Finger\" Calloway", "Woman", "Gunhand");
        Add("Doc Aurelia Mercer",           "Woman", "Sawbones");
        Add("Brother Elias Crow",           "Man",   "Preacher");
        Add("Anni Halvorsen",               "Woman", "Mountain Man");
        Add("Addison Quill",                "Man",   "Bounty Hunter");
        Add("Opal Vance",                   "Woman", "Hexer");
        Rules.ReseedEntropy();   // restore entropy so play dice stay random
    }
}
