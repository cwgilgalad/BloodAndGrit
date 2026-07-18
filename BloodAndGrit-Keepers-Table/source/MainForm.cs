using System.ComponentModel;
using System.Text.Json;

namespace BloodAndGritKeeper;

public partial class MainForm : Form
{
    // shared state
    readonly BindingList<PartyMember> party = new();
    readonly BindingList<Combatant> tracker = new();
    readonly BindingList<EncounterPick> encounter = new();
    readonly BindingList<CampaignClock> clocks = new();
    TextBox notesBox;
    ListBox rollLog;
    int round = 1;
    TabControl tabsCtl;

    // ---- shared theme (frontier-book palette) ----
    public static readonly Color Paper   = Color.FromArgb(247, 242, 228);
    public static readonly Color Ink     = Color.FromArgb(38, 28, 20);
    public static readonly Color Blood   = Color.FromArgb(120, 22, 22);
    public static readonly Color Gold     = Color.FromArgb(150, 116, 50);
    public static readonly Color Verdigris = Color.FromArgb(60, 96, 84);
    public static readonly Color PcRow   = Color.FromArgb(238, 244, 232);
    public static readonly Color FoeRow  = Color.FromArgb(250, 250, 247);
    public static readonly Color DownRow = Color.FromArgb(248, 224, 224);

    internal const string AppVersion = "1.4.0";

    public MainForm()
    {
        Text = "Blood & Grit — The Keeper's Table";
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
        tabs.TabPages.Add(BuildPosseTab());
        tabs.TabPages.Add(BuildDiceTab());
        tabs.TabPages.Add(BuildBestiaryTab());
        tabs.TabPages.Add(BuildEncounterTab());
        tabs.TabPages.Add(BuildTrackerTab());
        tabs.TabPages.Add(BuildGeneratorsTab());
        tabs.TabPages.Add(BuildSoulTab());
        tabs.TabPages.Add(BuildReferenceTab());
        tabs.TabPages.Add(BuildSessionTab());
        Controls.Add(tabs);

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
        };

        var status = new StatusStrip { BackColor = Paper };
        status.Items.Add(new ToolStripStatusLabel(
            $"{Db.Creatures.Count} creatures loaded  ·  Player's Book v2.14 · Keeper's Book v2.6 · Bestiary v2.6")
            { ForeColor = Ink });
        var spring = new ToolStripStatusLabel { Spring = true };
        status.Items.Add(spring);
        status.Items.Add(new ToolStripStatusLabel("Ctrl+1–9 tabs · F1 the five-minute lesson · auto-saves on exit + every 5 min") { ForeColor = Gold });
        Controls.Add(status);

        TryAutoLoad();
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

    // ---------------------------------------------------------- shared helpers
    void Log(string s)
    {
        if (rollLog == null) return;
        rollLog.Items.Insert(0, $"[{DateTime.Now:HH:mm}] {s}");
        while (rollLog.Items.Count > 400) rollLog.Items.RemoveAt(rollLog.Items.Count - 1);
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
    static Button MenuBtn(string text, int w, string tip, params (string label, EventHandler onClick)[] items)
    {
        var b = Btn(text, null, w, tip);
        var menu = new ContextMenuStrip { Font = new Font("Segoe UI", 9.5f) };
        foreach (var (label, onClick) in items)
        {
            if (label == "-") { menu.Items.Add(new ToolStripSeparator()); continue; }
            var mi = new ToolStripMenuItem(label);
            mi.Click += onClick;
            menu.Items.Add(mi);
        }
        b.Click += (s, e) => menu.Show(b, new Point(0, b.Height));
        return b;
    }

    static Label Lbl(string t, int w = 0)
    {
        var l = new Label { Text = t, AutoSize = w == 0, Padding = new Padding(0, 8, 4, 0), ForeColor = Ink };
        if (w > 0) l.Width = w;
        return l;
    }

    static Label Heading(string t) => new()
    { Text = t, AutoSize = true, Font = new Font("Segoe UI", 10f, FontStyle.Bold), ForeColor = Blood, Padding = new Padding(0, 6, 0, 2) };

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
        a.SetColorMatrix(new System.Drawing.Imaging.ColorMatrix { Matrix33 = 0.055f });   // ghost-faint
        return a;
    }

    /// <summary>
    /// Paints the emblem, ghost-faint, in the dead space at the bottom-right of a pane.
    /// usedHeight reports how far real content reaches; the emblem draws only when the
    /// space left below can hold it with generous margin, so it never sits behind rows,
    /// text, or controls — panes that fill up simply don't show it.
    /// </summary>
    static void Watermark(Control host, Func<int> usedHeight)
    {
        host.Paint += (s, e) =>
        {
            var img = Emblem; if (img == null) return;
            int cw = host.ClientSize.Width, ch = host.ClientSize.Height;
            int free = ch - usedHeight();
            // scale to what the dead space can hold — full size in a big empty pane,
            // smaller where room is tighter, gone entirely below a dignified minimum
            int w = Math.Min(Math.Min(300, cw - 56), (free - 44) * img.Width / img.Height);
            if (w < 150) return;
            int h = w * img.Height / img.Width;
            var r = new Rectangle(cw - w - 26, ch - h - 20, w, h);
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
        Col("Name", "Name", 155); Col("Calling", "Calling", 115); Col("Level", "Lv", 40);
        Col("BloodCur", "Blood", 55); Col("BloodMax", "/Max", 50); Col("Defense", "Def", 45);
        Col("Fort", "Fort", 45); Col("Ref", "Ref", 45); Col("Will", "Will", 45);
        Col("NerveCur", "Nerve", 55); Col("NerveMax", "/Max", 50); Col("Grit", "Grit", 45);
        Col("Mark", "Mark", 48); Col("Taint", "Taint", 48); Col("Notes", "Notes", 150);
        WireNumericValidation(posseGrid, new() { "Level","BloodCur","BloodMax","Defense","Fort","Ref","Will","NerveCur","NerveMax","Grit","Mark","Taint" });

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

        bar.Controls.Add(Lbl("  Amount:"));
        adjAmount = new NumericUpDown { Minimum = 1, Maximum = 999, Value = 3, Width = 60, Margin = new Padding(3, 6, 3, 3) };
        Tip.SetToolTip(adjAmount, "How much Blood the Damage/Heal buttons apply");
        bar.Controls.Add(adjAmount);
        bar.Controls.Add(Btn("Damage", (s, e) => AdjustPC(-1), 80, "Subtract the Amount from the selected soul's Blood (Ctrl+D)"));
        bar.Controls.Add(Btn("Heal", (s, e) => AdjustPC(+1), 70, "Add the Amount to the selected soul's Blood (Ctrl+H)"));

        bar.Controls.Add(Btn("Spend Grit", (s, e) =>
        {
            var p = SelectedPC(); if (p == null) return;
            if (p.Grit > 0) { p.Grit--; Log($"{p.Name} spends Grit ({p.Grit} left)."); }
            else Log($"{p.Name} has no Grit left to spend.");
        }, 90, "Spend one Grit (re-roll, refuse to fall at 0 Blood, shrug a fright)"));
        bar.Controls.Add(Btn("Mark +1", (s, e) =>
        {
            var p = SelectedPC(); if (p == null) return;
            p.Mark = Math.Min(6, p.Mark + 1);
            Log($"{p.Name}'s Mark advances to step {p.Mark} of 6." + (p.Mark >= 6 ? "  THE MARK IS FULL — the country collects." : ""));
        }, 75, "Advance the Mark one step (only when a soul CHOOSES the dark)"));
        bar.Controls.Add(Btn("Taint +1", (s, e) =>
        {
            var p = SelectedPC(); if (p == null) return;
            p.Taint = Math.Min(4, p.Taint + 1);
            Log($"{p.Name}'s Taint deepens to {p.Taint} of 4.");
        }, 75, "Deepen the Taint of the Land one step"));

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

        page.Controls.Add(posseGrid);
        page.Controls.Add(bar);
        Watermark(posseGrid, () => GridBottom(posseGrid));
        return page;
    }

    PartyMember SelectedPC() => posseGrid?.CurrentRow?.DataBoundItem as PartyMember;

    void RemoveSelectedPC()
    {
        var p = SelectedPC(); if (p == null) return;
        if (Confirm($"Remove {p.Name} from the posse?")) party.Remove(p);
    }

    void AdjustPC(int sign)
    {
        var p = SelectedPC();
        if (p == null) { Log("Select a soul first."); return; }
        int v = (int)adjAmount.Value;
        p.BloodCur = Math.Clamp(p.BloodCur + sign * v, 0, p.BloodMax);
        Log($"{p.Name} {(sign < 0 ? "takes" : "recovers")} {v} Blood → {p.BloodCur}/{p.BloodMax}" + (p.BloodCur == 0 ? "  — DOWN." : ""));
        MirrorToTracker(p);
    }

    void DreadCheckPC(PartyMember p)
    {
        if (p == null) { Log("Select a soul first."); return; }
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
        if (!Confirm("A long rest for the whole posse? Restores every soul's Blood and Nerve to full.")) return;
        foreach (var p in party) { p.BloodCur = p.BloodMax; p.NerveCur = p.NerveMax; MirrorToTracker(p); }
        posseGrid?.Refresh();
        Log("The posse takes a long rest — Blood and Nerve restored to full.");
    }

    void RestSoul(PartyMember p)
    {
        if (p == null) { Log("Select a soul first."); return; }
        p.BloodCur = p.BloodMax; p.NerveCur = p.NerveMax;
        MirrorToTracker(p); posseGrid?.Refresh();
        Log($"{p.Name} rests — Blood and Nerve restored to full.");
    }

    void PartyToTracker()
    {
        int added = 0;
        foreach (var p in party)
            if (!tracker.Any(t => t.IsPC && t.Name == p.Name))
            { tracker.Add(new Combatant { Name = p.Name, IsPC = true, BloodCur = p.BloodCur, BloodMax = p.BloodMax, Defense = p.Defense }); added++; }
        Log($"Sent {added} soul(s) to the tracker.");
    }

    void MirrorToTracker(PartyMember p)
    {
        var c = tracker.FirstOrDefault(t => t.IsPC && t.Name == p.Name);
        if (c != null) { c.BloodCur = p.BloodCur; c.BloodMax = p.BloodMax; trkGrid?.Refresh(); }
    }

    // ============================================================ DICE TAB
    TextBox exprBox;

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
        using var border = new Pen(Color.FromArgb(214, 202, 176), 1.5f);
        using var face = new SolidBrush(Color.FromArgb(252, 249, 240));
        for (int i = 0; i < shown; i++)
        {
            var (sides, value, sign) = diceTray.Dice[i];
            int show = diceTray.Settled ? value : Rules.Rng.Next(1, sides + 1);
            var rect = new Rectangle(x + i * (size + gap), y, size, size);
            // a little jitter while tumbling, stillness once landed
            if (!diceTray.Settled) rect.Offset(Rules.Rng.Next(-2, 3), Rules.Rng.Next(-2, 3));
            using var path = RoundedRect(rect, 9);
            g.FillPath(face, path);
            Color edge = !diceTray.Settled ? Gold
                       : show == sides ? Verdigris                        // best face
                       : show == 1 && sides >= 6 ? Blood                  // worst face
                       : Color.FromArgb(178, 162, 128);
            using var pen = new Pen(edge, diceTray.Settled ? 2.2f : 1.4f);
            g.DrawPath(pen, path);
            Color numCol = diceTray.Settled && show == sides ? Verdigris
                         : diceTray.Settled && show == 1 && sides >= 6 ? Blood : Ink;
            TextRenderer.DrawText(g, show.ToString(), DieNumFont,
                new Rectangle(rect.X, rect.Y - 4, rect.Width, rect.Height), numCol,
                TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
            TextRenderer.DrawText(g, (sign < 0 ? "−d" : "d") + sides, DieTagFont,
                new Rectangle(rect.X, rect.Bottom - 17, rect.Width, 15), Gold,
                TextFormatFlags.HorizontalCenter);
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

        // build the expression by button: dice stack (d6 → 2d6 → 3d6), digits and
        // ＋/− make the modifier — no typing needed at the table
        var dicePad = new FlowLayoutPanel { AutoSize = true, MaximumSize = new Size(430, 0) };
        foreach (int d in new[] { 4, 6, 8, 10, 12, 20, 100 })
        {
            int sides = d;
            dicePad.Controls.Add(Btn("+d" + sides, (s, e) => ExprAddDie(sides), 54,
                $"Add a d{sides} to the expression — click again for another"));
        }
        left.Controls.Add(dicePad);
        var opsPad = new FlowLayoutPanel { AutoSize = true, MaximumSize = new Size(430, 0) };
        opsPad.Controls.Add(Btn("＋", (s, e) => ExprAppend("+"), 40, "Plus"));
        opsPad.Controls.Add(Btn("−", (s, e) => ExprAppend("-"), 40, "Minus"));
        foreach (int n in new[] { 1, 2, 3, 4, 5, 6, 7, 8, 9, 0 })
        {
            int digit = n;
            opsPad.Controls.Add(Btn(digit.ToString(), (s, e) => ExprAppend(digit.ToString()), 40));
        }
        opsPad.Controls.Add(Btn("⌫", (s, e) =>
        { if (exprBox.TextLength > 0) exprBox.Text = exprBox.Text[..^1]; ExprFocusEnd(); }, 40, "Backspace"));
        opsPad.Controls.Add(Btn("C", (s, e) => { exprBox.Clear(); ExprFocusEnd(); }, 40, "Clear the expression"));
        left.Controls.Add(opsPad);

        left.Controls.Add(Heading("Quick dice — roll one now"));
        var quick = new FlowLayoutPanel { AutoSize = true, MaximumSize = new Size(430, 0) };
        foreach (int d in new[] { 4, 6, 8, 10, 12, 20, 100 })
            quick.Controls.Add(Btn("d" + d, (s, e) =>
            {
                int r = Rules.Rng.Next(1, d + 1);
                AnimateDice(new() { (d, r, 1) });
                Log($"d{d} → {r}");
            }, 54));
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
        }, 84));
        left.Controls.Add(checkRow);
        left.Controls.Add(Lbl("Beat the DC by 10 (or nat 20) → critical success."));
        left.Controls.Add(Lbl("Miss by 10 (or nat 1) → critical failure."));

        rollLog = new ListBox { Dock = DockStyle.Fill, Font = new Font("Consolas", 9.5f), HorizontalScrollbar = true, BackColor = Color.FromArgb(252, 249, 240), BorderStyle = BorderStyle.None };
        var right = new Panel { Dock = DockStyle.Fill, Padding = new Padding(10) };
        var logHead = new Label { Text = "  Roll && event log", Dock = DockStyle.Top, Height = 26, Font = new Font("Segoe UI", 10f, FontStyle.Bold), ForeColor = Blood, TextAlign = ContentAlignment.MiddleLeft };

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
        logBar.Controls.Add(Btn("Copy log", (s, e) => { if (rollLog.Items.Count > 0) Clipboard.SetText(string.Join(Environment.NewLine, rollLog.Items.Cast<object>())); }, 90));
        logBar.Controls.Add(Btn("Clear log", (s, e) => rollLog.Items.Clear(), 90));
        right.Controls.Add(rollLog); right.Controls.Add(diceTray); right.Controls.Add(logHead); right.Controls.Add(logBar);

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
        exprBox.Text = Rules.ExprAddDie(exprBox.Text, sides);
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
        if (br == "could not parse" || br == "empty") { Log($"Couldn't read \"{exprBox.Text}\" — try something like 2d6+3."); return; }
        AnimateDice(dice);
        Log($"ROLL {exprBox.Text} → {t}   ({br})");
    }

    // ---------------------------------------------------------- dialogs
    static bool Confirm(string msg) =>
        MessageBox.Show(msg, "Blood & Grit", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes;

    // ---------------------------------------------------------- persistence
    string SavePath => Path.Combine(AppContext.BaseDirectory, "session.json");

    GameSession Snapshot() => new()
    {
        Party = party.ToList(), Clocks = clocks.ToList(), Notes = notesBox?.Text ?? "",
        EncounterCreatures = encounter.Select(x => x.Creature.name).ToList(),
        PartyLevelHint = (int)(encLevel?.Value ?? 2),
        Tracker = tracker.ToList(), Round = round
    };

    internal void AutoSave()
    {
        try
        {
            File.WriteAllText(SavePath, JsonSerializer.Serialize(Snapshot(), new JsonSerializerOptions { WriteIndented = true }));
        }
        catch { /* never block closing */ }
    }

    // Replace the whole table with a saved session — the shared road for the startup
    // auto-load and File → Load session.
    void ApplySession(GameSession s)
    {
        party.Clear(); clocks.Clear(); encounter.Clear(); tracker.Clear();
        foreach (var p in s.Party ?? new()) party.Add(p);
        foreach (var c in s.Clocks ?? new()) clocks.Add(c);
        if (notesBox != null) notesBox.Text = s.Notes ?? "";
        foreach (var n in s.EncounterCreatures ?? new())
        { var c = Db.Find(n); if (c != null) encounter.Add(new EncounterPick(c)); }
        if (encLevel != null && s.PartyLevelHint >= 1) encLevel.Value = Math.Clamp(s.PartyLevelHint, 1, 10);
        foreach (var c in s.Tracker ?? new()) tracker.Add(c);   // a fight in progress survives a restart
        round = Math.Max(1, s.Round);
        if (roundLbl != null) roundLbl.Text = $"Round {round}";
        RefreshClocks(); RefreshEncounter();
        posseGrid?.Refresh(); trkGrid?.Refresh();
    }

    void TryAutoLoad()
    {
        try
        {
            if (!File.Exists(SavePath)) { SeedDemo(); return; }
            var s = JsonSerializer.Deserialize<GameSession>(File.ReadAllText(SavePath));
            if (s == null || s.Party.Count == 0) { SeedDemo(); return; }
            ApplySession(s);
        }
        catch { if (party.Count == 0) SeedDemo(); }
    }

    void SeedDemo()
    {
        // The ready-made posse from Appendix D, so the app is useful on first launch.
        void Add(string n, string call, int bl, int def, int f, int r, int w, int nv, int mark = 0)
            => party.Add(new PartyMember { Name = n, Calling = call, Level = 1, BloodCur = bl, BloodMax = bl, Defense = def, Fort = f, Ref = r, Will = w, NerveCur = nv, NerveMax = nv, Mark = mark });
        Add("Ruth \"Six-Finger\" Calloway", "Gunhand", 12, 13, 4, 5, 1, 13);
        Add("Doc Aurelia Mercer", "Sawbones", 9, 11, 3, 1, 4, 15);
        Add("Brother Elias Crow", "Preacher", 9, 9, 3, -1, 4, 16);
        Add("Anni Halvorsen", "Mountain Man", 12, 10, 4, 0, 4, 15);
        Add("Addison Quill", "Bounty Hunter", 8, 12, 0, 4, 3, 14);
        Add("Opal Vance", "Hexer", 7, 10, 1, 0, 5, 17, 1);
    }
}
