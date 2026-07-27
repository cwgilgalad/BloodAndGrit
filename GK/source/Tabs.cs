using System.ComponentModel;

namespace BloodAndGritKeeper;

public enum TrkSort { InitDesc, InitAsc, NameAsc, NameDesc, BloodDesc, BloodAsc }

public class EncounterPick
{
    public Creature Creature { get; }
    public EncounterPick(Creature c) { Creature = c; }
    public string Name => Creature.name;
    public string Tier => "T" + Rules.Roman(Creature.tier);
}

public partial class MainForm
{
    // ============================================================ BESTIARY TAB
    ListBox beastList;
    RichTextBox beastView;
    TextBox beastSearch;
    ComboBox beastTier, beastChapter;
    Label beastCount;
    NumericUpDown beastQty;

    TabPage BuildBestiaryTab()
    {
        var page = new TabPage("Bestiary") { BackColor = Paper };
        var split = Split(Orientation.Vertical, 300, 340, 0.30);

        var leftPanel = new Panel { Dock = DockStyle.Fill, BackColor = Paper };
        // AutoSize: at narrow widths this bar wraps to 3–4 rows — a fixed height clipped
        // the action buttons clean out of view
        var filters = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(6), BackColor = Color.FromArgb(243, 237, 221) };

        filters.Controls.Add(Lbl("Search:"));
        beastSearch = new TextBox { Width = 180 };
        beastSearch.TextChanged += (s, e) => FilterBeasts();
        Tip.SetToolTip(beastSearch, "Filter by name or where it's found (Ctrl+F jumps here)");
        filters.Controls.Add(beastSearch);
        beastTier = new ComboBox { Width = 90, DropDownStyle = ComboBoxStyle.DropDownList };
        beastTier.Items.AddRange(new object[] { "Any tier", "Tier I", "Tier II", "Tier III", "Tier IV", "Tier V" });
        beastTier.SelectedIndex = 0; beastTier.SelectedIndexChanged += (s, e) => FilterBeasts();
        filters.Controls.Add(beastTier);
        beastChapter = new ComboBox { Width = 215, DropDownStyle = ComboBoxStyle.DropDownList };
        beastChapter.Items.Add("All chapters");
        foreach (var ch in Db.Creatures.Select(c => c.chapter).Distinct()) beastChapter.Items.Add(ch);
        beastChapter.SelectedIndex = 0; beastChapter.SelectedIndexChanged += (s, e) => FilterBeasts();
        filters.Controls.Add(beastChapter);
        filters.SetFlowBreak(beastChapter, true);
        filters.Controls.Add(Btn("🎲 Random", (s, e) => { if (beastList.Items.Count > 0) beastList.SelectedIndex = Rules.Rng.Next(beastList.Items.Count); }, 95, "Jump to a random creature in the current filter"));
        filters.Controls.Add(Btn("→ Encounter", (s, e) => { if (beastList.SelectedItem is Creature c) { encounter.Add(new EncounterPick(c)); RefreshEncounter(); Log($"Encounter: added {c.name}."); } }, 110, "Add to the encounter builder"));
        filters.Controls.Add(Lbl("  ×"));
        beastQty = new NumericUpDown { Width = 46, Minimum = 1, Maximum = 20, Value = 1, Margin = new Padding(0, 5, 3, 3) };
        Tip.SetToolTip(beastQty, "How many copies → Tracker drops at once");
        filters.Controls.Add(beastQty);
        filters.Controls.Add(Btn("→ Tracker", (s, e) => { if (beastList.SelectedItem is Creature c) AddCreatureToTracker(c, (int)beastQty.Value); }, 95, "Drop this many onto the battlefield"));
        // the pop-out lived only behind a double-click and its tooltip; a visible button
        // makes the feature discoverable without the mouse hovering in the right place
        filters.Controls.Add(Btn("⧉ Pop out", (s, e) => { if (beastList.SelectedItem is Creature c) ShowCreatureCard(c); }, 90,
            "Open this creature in its own window (or double-click it in the list)"));
        filters.Controls.Add(Btn("Reset", (s, e) =>
        {
            beastSearch.Text = ""; beastTier.SelectedIndex = 0; beastChapter.SelectedIndex = 0; beastQty.Value = 1;
        }, 65, "Clear the search and filters — the whole Bestiary again"));
        beastCount = Lbl("");
        filters.Controls.Add(beastCount);

        beastList = new ListBox { Dock = DockStyle.Fill, Font = new Font("Segoe UI", 9.5f), BorderStyle = BorderStyle.None, BackColor = Color.FromArgb(252, 249, 240) };
        beastList.SelectedIndexChanged += (s, e) => ShowBeast(beastList.SelectedItem as Creature);
        // double-click pops the creature out into its own window — maximize it, grow the
        // text, keep several open side by side
        beastList.DoubleClick += (s, e) => { if (beastList.SelectedItem is Creature c) ShowCreatureCard(c); };
        beastList.KeyDown += (s, e) =>
        {
            if (e.KeyCode == Keys.Enter && beastList.SelectedItem is Creature c)
            { ShowCreatureCard(c); e.Handled = true; e.SuppressKeyPress = true; }
        };
        Tip.SetToolTip(beastList, "Double-click a creature (or press Enter) to open it in its own window — right-click for where else it can go");

        // The filter bar's actions, on the creature itself. The quantity spinner is honored here
        // too, so "× 4 → Tracker" means the same thing whichever way it's reached.
        ListMenu<Creature>(beastList, (menu, c) =>
        {
            MIHead(menu, $"{c.name} — Tier {Rules.Roman(c.tier)}");
            MI(menu, "Open it in its own window", () => ShowCreatureCard(c));
            MISep(menu);
            MI(menu, "Add to the encounter plan", () => { encounter.Add(new EncounterPick(c)); RefreshEncounter(); Log($"Encounter: added {c.name}."); });
            int n = (int)beastQty.Value;
            MI(menu, n == 1 ? "Drop one onto the battlefield" : $"Drop {n} onto the battlefield", () => AddCreatureToTracker(c, n));
            MISep(menu);
            MI(menu, "Copy its stat block", () => { Clipboard.SetText(CreatureText(c)); Log($"{c.name}'s stat block copied to the clipboard."); });
        });
        leftPanel.Controls.Add(beastList); leftPanel.Controls.Add(filters);

        beastView = new RichTextBox { ReadOnly = true, BorderStyle = BorderStyle.None, BackColor = Paper, Font = new Font("Segoe UI", 10f) };

        split.Panel1.Controls.Add(leftPanel);
        split.Panel2.Controls.Add(Pad(beastView, 14));
        page.Controls.Add(split);
        FilterBeasts();
        return page;
    }

    void FilterBeasts()
    {
        string q = (beastSearch?.Text ?? "").Trim().ToLowerInvariant();
        int tier = beastTier?.SelectedIndex ?? 0;
        string chap = beastChapter?.SelectedIndex > 0 ? beastChapter.SelectedItem.ToString() : null;
        beastList.BeginUpdate();
        beastList.Items.Clear();
        foreach (var c in Db.Creatures
                 .Where(c => (tier == 0 || c.tier == tier)
                          && (chap == null || c.chapter == chap)
                          && (q == "" || c.name.ToLowerInvariant().Contains(q) || c.found.ToLowerInvariant().Contains(q)))
                 .OrderBy(c => c.tier).ThenBy(c => c.name))
            beastList.Items.Add(c);
        beastList.EndUpdate();
        if (beastCount != null) beastCount.Text = $"  {beastList.Items.Count} shown";
        if (beastList.Items.Count > 0) beastList.SelectedIndex = 0;
        else beastView?.Clear();
    }

    void ShowBeast(Creature c)
    {
        if (c == null) return;
        RenderCreature(beastView, c);
    }

    void RenderCreature(RichTextBox rtf, Creature c)
    {
        rtf.Clear();
        void W(string s, bool bold = false, float size = 10f, Color? col = null, bool italic = false)
        {
            var style = (bold ? FontStyle.Bold : FontStyle.Regular) | (italic ? FontStyle.Italic : 0);
            rtf.SelectionFont = new Font("Segoe UI", size, style);
            rtf.SelectionColor = col ?? Ink;
            rtf.AppendText(s);
        }
        W(c.name + "\n", true, 16, Blood);
        W(c.tierText + "\n\n", false, 9.5f, Gold, italic: true);
        foreach (var p in c.lore) W(p + "\n\n");
        if (!string.IsNullOrEmpty(c.witness)) W("“" + c.witness + "”\n\n", false, 9.7f, Gold, italic: true);
        if (!string.IsNullOrEmpty(c.found)) { W("FOUND — ", true, 9.5f, Blood); W(c.found + "\n\n"); }
        void Stat(string k, string v) { if (!string.IsNullOrEmpty(v)) { W(k.ToUpper() + "  ", true, 9.5f, Blood); W(v + "\n"); } }
        Stat("Defense", c.defense); Stat("Blood", c.blood); Stat("Speed", c.speed);
        Stat("Saves", c.saves); Stat("Attacks", c.attacks); Stat("Special", c.special);
        Stat("Dread", c.dread); Stat("The Mark", c.mark); Stat("Putting It Down", c.puttingItDown);
        if (!string.IsNullOrEmpty(c.keeperNote)) { W("\nHOW TO PLAY IT\n", true, 9.5f, Verdigris); W(c.keeperNote + "\n"); }
        rtf.SelectionStart = 0; rtf.ScrollToCaret();
    }

    /// <summary>The same stat block as plain text, for pasting into notes or a chat window. It follows
    /// <see cref="RenderCreature"/> line for line on purpose — a Keeper who copies what's on screen
    /// should get what's on screen, not an abridgement of it.</summary>
    static string CreatureText(Creature c)
    {
        var sb = new System.Text.StringBuilder();
        sb.AppendLine(c.name).AppendLine(c.tierText).AppendLine();
        foreach (var p in c.lore) sb.AppendLine(p).AppendLine();
        if (!string.IsNullOrEmpty(c.witness)) sb.AppendLine("“" + c.witness + "”").AppendLine();
        if (!string.IsNullOrEmpty(c.found)) sb.AppendLine("FOUND — " + c.found).AppendLine();
        void Stat(string k, string v) { if (!string.IsNullOrEmpty(v)) sb.AppendLine(k.ToUpperInvariant() + "  " + v); }
        Stat("Defense", c.defense); Stat("Blood", c.blood); Stat("Speed", c.speed);
        Stat("Saves", c.saves); Stat("Attacks", c.attacks); Stat("Special", c.special);
        Stat("Dread", c.dread); Stat("The Mark", c.mark); Stat("Putting It Down", c.puttingItDown);
        if (!string.IsNullOrEmpty(c.keeperNote)) sb.AppendLine().AppendLine("HOW TO PLAY IT").AppendLine(c.keeperNote);
        return sb.ToString().TrimEnd();
    }

    // ============================================================ ENCOUNTER TAB
    DataGridView encGrid;
    NumericUpDown encLevel, encQty;
    static readonly Font SpoorFont = new("Segoe UI", 9.5f, FontStyle.Bold);   // see the encounter grid's CellFormatting
    ComboBox encPick;
    Label encVerdict;
    Panel encBar;
    int encSpend, encBudget;    // what the bar paints — set by RefreshEncounter, read by the Paint handler

    // a creature-name picker with type-ahead, shared by the Encounter and Tracker tabs
    static ComboBox CreaturePicker(int width)
    {
        var box = new ComboBox
        {
            Width = width, DropDownStyle = ComboBoxStyle.DropDown,
            AutoCompleteMode = AutoCompleteMode.SuggestAppend,
            AutoCompleteSource = AutoCompleteSource.ListItems,
            Margin = new Padding(3, 5, 3, 3)
        };
        foreach (var c in Db.Creatures.OrderBy(c => c.name)) box.Items.Add(c.name);
        return box;
    }

    TabPage BuildEncounterTab()
    {
        var page = new TabPage("Encounter") { BackColor = Paper };
        var top = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(6, 4, 6, 4), BackColor = Color.FromArgb(243, 237, 221) };
        top.Controls.Add(Lbl("Party level:"));
        encLevel = new NumericUpDown { Minimum = 1, Maximum = 10, Width = 55, Margin = new Padding(3, 6, 3, 3) };
        encLevel.Value = Math.Clamp(partyLevelHint, 1, 10);     // built on first visit — adopt the loaded value
        encLevel.ValueChanged += (s, e) => { partyLevelHint = (int)encLevel.Value; RefreshEncounter(); };
        Tip.SetToolTip(encLevel, "Sets each creature's role and cost against the posse");
        top.Controls.Add(encLevel);
        top.Controls.Add(Lbl("   Budget = 4 pts per soul in the posse (Posse tab).  Even foe 4 · Mook 1 · Standout 8."));
        top.SetFlowBreak(top.Controls[top.Controls.Count - 1], true);

        top.Controls.Add(Lbl("Add a creature:"));
        encPick = CreaturePicker(230);
        Tip.SetToolTip(encPick, "Type a few letters or pick from the list, then Add");
        encPick.KeyDown += (s, e) => { if (e.KeyCode == Keys.Enter) { AddPickToEncounter(); e.SuppressKeyPress = true; } };
        top.Controls.Add(encPick);
        top.Controls.Add(Lbl(" ×"));
        encQty = new NumericUpDown { Width = 46, Minimum = 1, Maximum = 20, Value = 1, Margin = new Padding(0, 5, 3, 3) };
        top.Controls.Add(encQty);
        top.Controls.Add(Btn("＋ Add", (s, e) => AddPickToEncounter(), 75, "Add it to the plan (or press Enter in the box)"));
        top.Controls.Add(Btn("✕ Remove", (s, e) => { if (encGrid.CurrentRow?.DataBoundItem is EncounterPick p) { encounter.Remove(p); RefreshEncounter(); } }, 85,
            "Take the selected foe out of the encounter"));
        top.Controls.Add(Btn("Clear", (s, e) => { if (encounter.Count > 0 && Confirm("Clear the encounter?")) { encounter.Clear(); RefreshEncounter(); } }, 65,
            "Empty the encounter and start costing a new one"));
        top.Controls.Add(Btn("Send all → Tracker", (s, e) => { foreach (var p in encounter.ToList()) AddCreatureToTracker(p.Creature); }, 150, "Put every listed creature on the battlefield"));

        encGrid = new DataGridView
        {
            Dock = DockStyle.Fill, AutoGenerateColumns = false, DataSource = encounter,
            AllowUserToAddRows = false, ReadOnly = true, RowHeadersVisible = false,
            AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
            SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = false
        };
        StyleGrid(encGrid);
        encGrid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = "Name", HeaderText = "Creature", FillWeight = 220 });
        encGrid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = "Tier", HeaderText = "Tier", FillWeight = 50 });
        encGrid.Columns.Add(new DataGridViewTextBoxColumn { HeaderText = "Role vs party", FillWeight = 260, Name = "role" });
        encGrid.Columns.Add(new DataGridViewTextBoxColumn { HeaderText = "Cost", FillWeight = 45, Name = "cost" });
        encGrid.CellFormatting += (s, e) =>
        {
            if (e.RowIndex < 0 || e.RowIndex >= encounter.Count) return;
            var pick = encounter[e.RowIndex];
            var (cost, role, spoor) = Rules.Cost(pick.Creature.tier, (int)encLevel.Value);
            string name = encGrid.Columns[e.ColumnIndex].Name;
            // SpoorFont is cached: CellFormatting fires per visible cell per repaint, and a
            // fresh Font each time hands a GDI handle to the finalizer queue on every paint.
            if (name == "role") { e.Value = role; if (spoor) { e.CellStyle.ForeColor = Blood; e.CellStyle.Font = SpoorFont; } }
            if (name == "cost") e.Value = cost;
        };
        encGrid.CellDoubleClick += (s, e) => { if (e.RowIndex >= 0) ShowCreatureCard(encounter[e.RowIndex].Creature); };
        Tip.SetToolTip(encGrid, "Double-click a creature for its stat block — right-click for what can be done with it");

        GridMenu<EncounterPick>(encGrid, (menu, pick) =>
        {
            var beast = pick.Creature;
            MIHead(menu, $"{beast.name} — Tier {Rules.Roman(beast.tier)}");
            MI(menu, "Open the stat block", () => ShowCreatureCard(beast));
            MISep(menu);
            MI(menu, "Add another of these", () => { encounter.Add(new EncounterPick(beast)); RefreshEncounter(); Log($"Encounter: added {beast.name}."); });
            MI(menu, "Send this one to the Tracker", () => AddCreatureToTracker(beast));
            MISep(menu);
            MI(menu, "Take it off the plan", () => { encounter.Remove(pick); RefreshEncounter(); });
        });

        var bottom = new Panel { Dock = DockStyle.Bottom, Height = 64, BackColor = Color.FromArgb(243, 237, 221), Padding = new Padding(8, 6, 8, 6) };
        encVerdict = new Label { Dock = DockStyle.Top, Height = 26, TextAlign = ContentAlignment.MiddleLeft, Font = new Font("Segoe UI", 10.5f, FontStyle.Bold), ForeColor = Ink };
        // Owner-drawn rather than a ProgressBar: a themed ProgressBar ignores ForeColor outright,
        // so the bar could never agree with the verdict line above it. Drawing it also buys the
        // budget tick — the mark that says where "a fair, hard fight" actually sits, so being
        // over is something you can SEE, not just read.
        encBar = new BufferedPanel { Dock = DockStyle.Bottom, Height = 22, BackColor = Color.FromArgb(243, 237, 221) };
        encBar.Paint += (s, e) => PaintBudgetBar(e.Graphics, encBar.ClientRectangle);
        bottom.Controls.Add(encVerdict); bottom.Controls.Add(encBar);

        page.Controls.Add(encGrid);
        page.Controls.Add(bottom);
        page.Controls.Add(top);

        // empty-state: say plainly what this tab is FOR
        var hint = new Label
        {
            Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleCenter,
            Font = new Font("Segoe UI", 11f, FontStyle.Italic), ForeColor = Gold, BackColor = Paper,
            Text = "The Long Odds — weigh a fight BEFORE you run it.\n\n" +
                   "Add creatures above (or send them over from the Bestiary tab),\n" +
                   "set the party's level, and the verdict bar below tells you\n" +
                   "whether the fight is fair, mean, or a massacre.\n\n" +
                   "Happy with the odds? Send all → Tracker and run it."
        };
        page.Controls.Add(hint);
        hint.BringToFront();
        hint.Visible = encounter.Count == 0;
        encounter.ListChanged += (s, e) => hint.Visible = encounter.Count == 0;
        Watermark(encGrid, () => GridBottom(encGrid));
        Watermark(hint, () => HintBottom(hint));

        RefreshEncounter();
        return page;
    }

    void AddPickToEncounter()
    {
        var c = Db.Find((encPick.Text ?? "").Trim());
        if (c == null) { Nope("No creature by that name — pick one from the list."); return; }
        int n = (int)encQty.Value;
        for (int i = 0; i < n; i++) encounter.Add(new EncounterPick(c));
        RefreshEncounter();
        Log($"Encounter: added {(n == 1 ? c.name : $"{n}× {c.name}")}.");
    }

    void RefreshEncounter()
    {
        if (encGrid == null) return;
        encGrid.Refresh();
        int budget = 4 * Math.Max(1, party.Count);
        int spend = encounter.Sum(p => Rules.Cost(p.Creature.tier, (int)encLevel.Value).cost);
        encVerdict.Text = $"Spend {spend}  /  budget {budget}   ({party.Count} souls × 4)     {Rules.BudgetVerdict(spend, budget)}";
        encVerdict.ForeColor = BudgetColor(spend, budget);
        encSpend = spend; encBudget = budget;
        encBar?.Invalidate();
    }

    /// <summary>What the spend means in color, for the verdict line and the bar both, so the two can
    /// never disagree. Green ONLY at exactly budget — that is the balanced fight, and it should be
    /// the one reading on this tab you can spot without reading. Red the moment it goes over, at
    /// any depth; the words are what say how far over.</summary>
    public static Color BudgetColor(int spend, int budget) => Rules.BudgetBand(spend, budget) switch
    {
        Rules.Weight.Exact    => Verdigris,   // perfectly balanced
        Rules.Weight.Over     => Blood,
        Rules.Weight.WellOver => Blood,
        _                     => Ink,         // empty or under — safe, and not worth a color
    };

    /// <summary>The same reading, as a solid fill. Under budget takes a muted tan rather than the
    /// text's Ink: a bar filled with near-black weighs heavier on the eye than the red one beside
    /// it, which would make the safe state look like the loud one. Only over budget gets to shout.</summary>
    public static Color BudgetFill(int spend, int budget) => Rules.BudgetBand(spend, budget) switch
    {
        Rules.Weight.Exact    => Verdigris,
        Rules.Weight.Over     => Blood,
        Rules.Weight.WellOver => Blood,
        _                     => Color.FromArgb(176, 163, 138),
    };

    /// <summary>The budget bar: a track, the spend filled in the verdict's own color, and a tick
    /// standing at the budget so overspend is visible as distance past the mark.</summary>
    void PaintBudgetBar(Graphics g, Rectangle r)
    {
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
        var track = new Rectangle(r.X, r.Y + 4, Math.Max(1, r.Width - 1), Math.Max(1, r.Height - 9));
        using (var back = new SolidBrush(Color.FromArgb(232, 224, 205))) g.FillRectangle(back, track);

        // The scale always shows twice the budget, so the tick sits mid-bar and there is room to
        // run past it; a spend beyond that stretches the scale rather than pinning at the end.
        int scale = Math.Max(Math.Max(encBudget * 2, encSpend), 1);
        int fill = (int)Math.Round(track.Width * (double)Math.Min(encSpend, scale) / scale);
        if (fill > 0)
            using (var b = new SolidBrush(BudgetFill(encSpend, encBudget)))
                g.FillRectangle(b, new Rectangle(track.X, track.Y, fill, track.Height));

        int tick = track.X + (int)Math.Round(track.Width * (double)encBudget / scale);
        using (var pen = new Pen(Ink, 2f)) g.DrawLine(pen, tick, r.Y + 1, tick, r.Bottom - 2);
        using (var pen = new Pen(Color.FromArgb(150, 140, 120), 1f)) g.DrawRectangle(pen, track);
    }

    // ============================================================ TRACKER TAB
    DataGridView trkGrid;
    Label roundLbl, trkTurnLbl;
    NumericUpDown trkAmount, trkQty;
    ComboBox trkPick;

    // The acting row's ground — gold, so it reads as "this one is up" against the posse's green
    // and the foes' rust without competing with the red a downed combatant wears.
    static readonly Color ActingRow = Color.FromArgb(250, 240, 205);
    // A sign & spoor row: cold and bloodless, so it never reads as one more body to shoot at.
    static readonly Color SignRow = Color.FromArgb(234, 238, 240);
    Font trkBold, trkItalic;   // built once with the grid; CellFormatting runs on every paint

    // The Blood bar's three states. Green while they can take it, gold once it hurts, red when the
    // next hit is the last one — the same reading the Encounter tab's budget bar offers, so a
    // Keeper learns one color language and not two.
    static readonly Color BarTrack = Color.FromArgb(226, 218, 200);
    static readonly Color BarEdge   = Color.FromArgb(186, 174, 150);

    /// <summary>How much Blood is left, as a bar and a color. Above two thirds it is green; below
    /// a third it is red; between, gold. A bar exactly at zero draws only its track — the row is
    /// already wearing red, and a red bar of no length would just be noise.</summary>
    static void PaintBloodBar(Graphics g, Rectangle r, int cur, int max)
    {
        using (var back = new SolidBrush(BarTrack)) g.FillRectangle(back, r);
        float frac = Math.Clamp(cur / (float)Math.Max(1, max), 0f, 1f);
        int w = (int)Math.Round(r.Width * frac);
        if (w > 0)
        {
            var ink = frac >= 0.66f ? Verdigris : frac >= 0.33f ? Gold : Blood;
            using var b = new SolidBrush(Color.FromArgb(150, ink));   // the number has to stay legible on it
            g.FillRectangle(b, new Rectangle(r.X, r.Y, w, r.Height));
        }
        using var pen = new Pen(BarEdge, 1f);
        g.DrawRectangle(pen, r);
    }

    /// <summary>The spoor clock in the Blood column: one box per segment, filled as the posse keeps
    /// crossing this thing's trail. A full clock is the night it arrives in the flesh.</summary>
    static void PaintSpoorClock(Graphics g, Rectangle r, int filled)
    {
        int n = Rules.SpoorClockSegments;
        int gap = 2, box = Math.Max(3, (r.Width - gap * (n - 1)) / n);
        int h = Math.Min(r.Height, box + 4);
        int y = r.Y + (r.Height - h) / 2;
        using var fill = new SolidBrush(Blood);
        using var pen = new Pen(BarEdge, 1f);
        for (int i = 0; i < n; i++)
        {
            var cell = new Rectangle(r.X + i * (box + gap), y, box, h);
            if (i < filled) g.FillRectangle(fill, cell);
            g.DrawRectangle(pen, cell);
        }
    }
    // One italic, shared: a Font handed to a Label isn't disposed with the Label, so building a
    // fresh one every time the Strike dialog opens leaks a handle per fight.
    static readonly Font DialogItalic = new("Segoe UI", 9f, FontStyle.Italic);
    static readonly Font DialogBold = new("Segoe UI", 9.75f, FontStyle.Bold);

    /// <summary>Say in words what the turn state is, because Beats and the MAP step are small
    /// numbers in a wide grid and a Keeper pressing "Begin turn" deserves to see something answer.
    /// </summary>
    void UpdateTurnLine()
    {
        if (trkTurnLbl == null) return;
        var c = tracker.FirstOrDefault(t => t.Acting);
        if (c == null)
        {
            trkTurnLbl.Text = "no one's turn yet — select a combatant, then Begin turn";
            trkTurnLbl.ForeColor = Color.FromArgb(122, 112, 96);
            return;
        }
        trkTurnLbl.Text = $"{c.Name} is up — {c.Beats} Beat{(c.Beats == 1 ? "" : "s")} left"
            + (c.Beats == 0 ? ", spent" : $", next Strike {c.NextStrike}");
        trkTurnLbl.ForeColor = c.Beats == 0 ? Color.FromArgb(122, 112, 96) : Blood;
    }

    void AddPickToTracker()
    {
        var c = Db.Find((trkPick.Text ?? "").Trim());
        if (c == null) { Nope("No creature by that name — pick one from the list."); return; }
        AddCreatureToTracker(c, (int)trkQty.Value);
    }

    TabPage BuildTrackerTab()
    {
        var page = new TabPage("Tracker") { BackColor = Paper };
        var bar = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(6, 4, 6, 4), BackColor = Color.FromArgb(243, 237, 221) };
        roundLbl = new Label { Text = "Round 1", Font = new Font("Segoe UI", 12f, FontStyle.Bold), ForeColor = Blood, Padding = new Padding(0, 6, 12, 0), AutoSize = true };
        bar.Controls.Add(roundLbl);
        // The turn readout rides beside the round, fixed-width so a long name can't shove the
        // button rows around, and it gets the row to itself.
        trkTurnLbl = new Label
        {
            Width = 430, Height = 22, AutoSize = false, Font = new Font("Segoe UI", 9.5f, FontStyle.Italic),
            TextAlign = ContentAlignment.MiddleLeft, Padding = new Padding(0, 0, 8, 0), AutoEllipsis = true
        };
        Tip.SetToolTip(trkTurnLbl, "Whose turn it is, what they have left to spend, and what the next Strike costs");
        bar.Controls.Add(trkTurnLbl);
        // Putting the field back on its feet between fights. It rides at the top, beside the round,
        // because it is the thing a Keeper reaches for when a scene ENDS — not one more combat
        // action to hunt for among the combat actions.
        bar.Controls.Add(MenuBtn("✚ Restore ▾", 118,
            "Put Blood — and, for the posse, Nerve — back to full",
            ("Selected combatant — Blood to full", (s, e) => RestoreSelected()),
            ("The posse — Blood, Nerve & pool to full", (s, e) => RestPosse()),
            ("-", null),
            ("Everyone on the field — Blood to full", (s, e) => RestoreField())));
        bar.SetFlowBreak(bar.Controls[bar.Controls.Count - 1], true);
        UpdateTurnLine();
        bar.Controls.Add(Btn("Roll initiative", (s, e) => RollInitiative(), 110, "Roll a d20 for every combatant and sort by it (Ctrl+I)"));
        bar.Controls.Add(MenuBtn("Sort ▾", 70, "Order the field",
            ("Initiative — high to low", (s, e) => SortTracker(TrkSort.InitDesc)),
            ("Initiative — low to high", (s, e) => SortTracker(TrkSort.InitAsc)),
            ("-", null),
            ("Name — A to Z", (s, e) => SortTracker(TrkSort.NameAsc)),
            ("Name — Z to A", (s, e) => SortTracker(TrkSort.NameDesc)),
            ("-", null),
            ("Blood — most to least", (s, e) => SortTracker(TrkSort.BloodDesc)),
            ("Blood — least to most", (s, e) => SortTracker(TrkSort.BloodAsc))));
        bar.Controls.Add(Btn("Next round ▸", (s, e) => NextRound(), 100, "Step to the next round (Ctrl+R)"));
        bar.Controls.Add(Btn("Begin turn", (s, e) => BeginTurnForSelected(), 82,
            "Hand the turn to the selected combatant: their Beats go back to 3, their next Strike is "
            + "clean (no MAP), and their row lights gold as the one acting"));
        bar.Controls.Add(Btn("Strike ▸", (s, e) => StrikeDialog(), 72, "Resolve a Strike from the selected combatant — the engine handles to-hit, degrees, MAP, Fatal, and DR"));
        bar.Controls.Add(Btn("Dread ▸", (s, e) => DreadDialog(), 70, "Roll a Dread Check for the selected soul — Nerve off the ladder, Frightened, and the break at 0 Nerve"));
        bar.Controls.Add(Btn("Read sign ▸", (s, e) => ReadSignDialog(), 92,
            "Read the selected sign & spoor: a Survival check at the Tier's DC, the Dread it costs the "
            + "reader, and one more segment of the clock toward the night it comes in the flesh"));
        bar.Controls.Add(Lbl("  Amt:"));
        trkAmount = new NumericUpDown { Minimum = 1, Maximum = 999, Value = 5, Width = 58, Margin = new Padding(3, 6, 3, 3) };
        bar.Controls.Add(trkAmount);
        bar.Controls.Add(Btn("Damage", (s, e) => AdjustCombatant(-1), 80, "Subtract the Amt from the selected combatant (Ctrl+D)"));
        bar.Controls.Add(Btn("Heal", (s, e) => AdjustCombatant(+1), 65, "Add the Amt to the selected combatant (Ctrl+H)"));
        bar.SetFlowBreak(bar.Controls[bar.Controls.Count - 1], true);

        bar.Controls.Add(Lbl("Foe:"));
        trkPick = CreaturePicker(200);
        Tip.SetToolTip(trkPick, "Any creature in the Bestiary — type a few letters, then Add");
        trkPick.KeyDown += (s, e) => { if (e.KeyCode == Keys.Enter) { AddPickToTracker(); e.SuppressKeyPress = true; } };
        bar.Controls.Add(trkPick);
        bar.Controls.Add(Lbl(" ×"));
        trkQty = new NumericUpDown { Width = 46, Minimum = 1, Maximum = 20, Value = 1, Margin = new Padding(0, 5, 3, 3) };
        bar.Controls.Add(trkQty);
        bar.Controls.Add(Btn("＋ Foe", (s, e) => AddPickToTracker(), 70, "Drop it straight onto the field"));
        bar.Controls.Add(Btn("＋ Add", (s, e) => AddCustomCombatant(), 90, "Add an ad-hoc combatant or NPC by hand"));
        var condItems = BookConditions
            .Select(cd => (cd, (EventHandler)((s, e) => ApplyCondition(cd)))).ToList();
        condItems.Add(("-", null));
        condItems.Add(("— Clear all —", (s, e) => ClearConditions()));
        bar.Controls.Add(MenuBtn("＋ Condition ▾", 130, "Tag the selected combatant with a condition", condItems.ToArray()));
        bar.Controls.Add(Btn("✕ Remove", (s, e) => { if (trkGrid.CurrentRow?.DataBoundItem is Combatant c) tracker.Remove(c); }, 85, "Remove the selected combatant (or press Delete)"));
        bar.Controls.Add(Btn("New fight", (s, e) => NewFight(), 90, "Clear the foes, keep the posse, back to Round 1"));
        bar.Controls.Add(Btn("Clear field", (s, e) => { if (tracker.Count > 0 && Confirm("Clear the whole battlefield?")) { tracker.Clear(); round = 1; if (roundLbl != null) roundLbl.Text = "Round 1"; Log("The field is cleared."); } }, 95, "Wipe everyone — posse and foes — and reset to Round 1"));

        trkGrid = new DataGridView
        {
            Dock = DockStyle.Fill, AutoGenerateColumns = false, DataSource = tracker,
            AllowUserToAddRows = false, RowHeadersVisible = false,
            AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
            SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = false
        };
        StyleGrid(trkGrid);
        trkBold = new Font(trkGrid.Font, FontStyle.Bold);
        trkItalic = new Font(trkGrid.Font, FontStyle.Italic);
        // Columns carry their property name as their Name too, so everything downstream — the bar
        // painter, the tooltips, the button column — asks for a column by what it MEANS rather
        // than by an index that shifts the moment a column is inserted.
        void C(string prop, string head, int w, bool ro = false, string tip = null)
            => trkGrid.Columns.Add(new DataGridViewTextBoxColumn
            { DataPropertyName = prop, Name = prop, HeaderText = head, FillWeight = w, ReadOnly = ro, ToolTipText = tip ?? "" });
        C("Init", "Init", 50); C("Name", "Name", 190, true); C("BloodCur", "Blood", 62, false,
            "Blood left, drawn as a bar behind the number — full green, hurt gold, near death red. "
            + "On a sign & spoor row it is the spoor clock instead.");
        C("BloodMax", "/Max", 48, true);
        C("LastNote", "Last", 74, true,
            "What just happened here — the damage taken, the healing done, the moment they went down. "
            + "Cleared at the top of each round.");
        C("Defense", "Def", 46, true); C("Beats", "Beats", 44, false,
            "Beats left this turn — a Strike costs one. Begin turn puts them back to 3.");
        C("NextStrike", "Next strike", 68, true,
            "What the next Strike this turn costs in MAP: clean, then −5, then −10 "
            + "(an Agile weapon softens it to −4/−8). Begin turn makes it clean again.");
        C("Conditions", "Conditions", 186);
        // far-right Ledger button — posse souls only; creatures keep their double-click
        // stat block and ad-hoc rows have no sheet to show, so neither draws a button
        trkGrid.Columns.Add(new DataGridViewButtonColumn
        { HeaderText = "", Text = "Ledger", UseColumnTextForButtonValue = true, FillWeight = 60, Name = "ledgerBtn", ReadOnly = true });
        bool TrkHasSheet(int i) => i >= 0 && i < tracker.Count && tracker[i].IsPC
            && string.IsNullOrEmpty(tracker[i].Ref) && SoulOf(tracker[i]) != null;
        trkGrid.CellPainting += (s, e) =>
        {
            if (e.RowIndex < 0 || e.ColumnIndex >= trkGrid.Columns.Count || e.ColumnIndex < 0) return;
            string col = trkGrid.Columns[e.ColumnIndex].Name;
            if (col == "ledgerBtn" && !TrkHasSheet(e.RowIndex))
            { e.PaintBackground(e.ClipBounds, true); e.Handled = true; return; }
            if (col != "BloodCur" || e.RowIndex >= tracker.Count) return;

            // The Blood column is the one number a Keeper reads a dozen times a round, and a bare
            // "17" says nothing about whether 17 is nearly dead. Behind the number goes a bar: how
            // much is left, in a color that says how bad it is. A sign & spoor row has no blood to
            // draw, so it gets its clock here instead — the thing that IS its state.
            var c = tracker[e.RowIndex];
            e.PaintBackground(e.CellBounds, true);
            var bar = e.CellBounds; bar.Inflate(-4, -5);
            if (bar.Width > 6 && bar.Height > 4)
            {
                if (c.IsSign) PaintSpoorClock(e.Graphics, bar, c.SignFilled);
                else if (c.BloodMax > 0) PaintBloodBar(e.Graphics, bar, c.BloodCur, c.BloodMax);
            }
            if (!c.IsSign) e.PaintContent(e.CellBounds);   // the number rides on top of its own bar
            e.Handled = true;
        };
        trkGrid.CellContentClick += (s, e) =>
        {
            if (e.RowIndex >= 0 && e.ColumnIndex >= 0 && trkGrid.Columns[e.ColumnIndex].Name == "ledgerBtn" && TrkHasSheet(e.RowIndex))
            { if (SoulOf(tracker[e.RowIndex]) is PartyMember p) ShowSoulCard(p); }
        };
        WireNumericValidation(trkGrid, new() { "Init", "BloodCur", "Beats" });
        trkGrid.CellFormatting += (s, e) =>
        {
            if (e.RowIndex < 0 || e.RowIndex >= tracker.Count) return;
            var c = tracker[e.RowIndex];
            // Down beats acting: a combatant who is bleeding out reads red even on their own turn.
            e.CellStyle.BackColor = c.Down ? DownRow : c.Acting ? ActingRow : c.IsSign ? SignRow : c.IsPC ? PcRow : FoeRow;
            if (c.Down) e.CellStyle.ForeColor = Blood;
            else if (c.Acting) e.CellStyle.Font = trkBold;   // cached: CellFormatting runs on every paint

            string col = trkGrid.Columns[e.ColumnIndex].Name;
            // The "Last" cell is the whole point of the column: it has to be readable as harm or
            // mending from across the table, without stopping to read the sign of the number.
            if (col == "LastNote" && c.LastDelta != 0)
            {
                e.CellStyle.ForeColor = c.LastDelta < 0 ? Blood : Verdigris;
                e.CellStyle.Font = trkBold;
            }
            // A sign is a thread, not a body. The italic name is what says so at a glance, next to
            // the clock its Blood column carries instead of a number.
            if (c.IsSign && col == "Name") e.CellStyle.Font = trkItalic;
        };
        trkGrid.CellEndEdit += (s, e) =>
        {
            var c = tracker[e.RowIndex];
            if (c.BloodMax > 0 && c.BloodCur > c.BloodMax) c.BloodCur = c.BloodMax;
            if (c.IsPC) { var p = party.FirstOrDefault(x => x.Name == c.Name); if (p != null) { p.BloodCur = c.BloodCur; posseGrid?.Refresh(); } }
            trkGrid.Refresh();
        };
        trkGrid.KeyDown += (s, e) =>
        {
            if (e.KeyCode == Keys.Delete && !trkGrid.IsCurrentCellInEditMode)
            { if (trkGrid.CurrentRow?.DataBoundItem is Combatant c) tracker.Remove(c); e.Handled = true; }
        };
        // double-click opens the combatant's card: foes get their Bestiary stat block,
        // posse members get their Ledger — the same windows the source tabs open
        trkGrid.CellDoubleClick += (s, e) =>
        {
            if (e.RowIndex < 0 || e.RowIndex >= tracker.Count) return;
            var t = tracker[e.RowIndex];
            if (!string.IsNullOrEmpty(t.Ref))
            { var c = Db.Find(t.Ref); if (c != null) ShowCreatureCard(c); }
            else if (t.IsPC)
            { var p = party.FirstOrDefault(x => x.Name == t.Name); if (p != null) ShowSoulCard(p); }
        };

        Tip.SetToolTip(trkGrid, "Double-click a combatant for their card — right-click for everything that can be done to them");

        // The bar's actions, on the combatant itself. What's offered depends on who the row is:
        // only a soul takes a Dread Check or has a Ledger, and only a creature has a stat block.
        GridMenu<Combatant>(trkGrid, (menu, c) =>
        {
            MIHead(menu, c.Name is { Length: > 0 } ? c.Name : "This combatant");
            // A sign is a different kind of thing, so it gets a different menu — offering "Strike"
            // and "Heal" on a set of tracks is the app not knowing what it put on the field.
            if (c.IsSign)
            {
                MI(menu, "Read it… — Survival, Dread, and a segment of the clock", () => ReadSignDialog());
                if (Db.Find(c.Ref) is Creature signOf) MI(menu, $"Open {signOf.name}'s stat block", () => ShowCreatureCard(signOf));
                MISep(menu);
                MI(menu, $"Fill a segment by hand ({c.SignFilled} of {Rules.SpoorClockSegments})",
                    () => { c.SignFilled += 1; trkGrid.Refresh(); Log($"{c.Name}: the clock stands at {c.SignFilled} of {Rules.SpoorClockSegments}."); },
                    !c.SignFull);
                MI(menu, "Rub out a segment",
                    () => { c.SignFilled -= 1; trkGrid.Refresh(); Log($"{c.Name}: the clock stands at {c.SignFilled} of {Rules.SpoorClockSegments}."); },
                    c.SignFilled > 0);
                MI(menu, "It comes in the flesh now", () => SignArrives(c, Db.Find(c.Ref)));
                MISep(menu);
                MI(menu, "Take it off the field", () => tracker.Remove(c));
                return;
            }
            MI(menu, "Begin their turn — 3 Beats, a clean MAP", () => BeginTurnForSelected());
            MI(menu, "Strike…", () => StrikeDialog(), !c.Down);
            if (c.IsPC) MI(menu, "Dread check…", () => DreadDialog());
            MISep(menu);
            MI(menu, $"Damage {trkAmount.Value}", () => AdjustCombatant(-1));
            MI(menu, $"Heal {trkAmount.Value}", () => AdjustCombatant(+1), c.BloodMax == 0 || c.BloodCur < c.BloodMax);
            MI(menu, "Restore to full Blood", () => RestoreSelected(), c.BloodMax > 0 && c.BloodCur < c.BloodMax);

            var cond = new ToolStripMenuItem("Conditions");
            foreach (var name in BookConditions)
            {
                string cd = name;
                cond.DropDownItems.Add(Amp(cd), null, (s, e) => ApplyCondition(cd));
            }
            cond.DropDownItems.Add(new ToolStripSeparator());
            var clear = cond.DropDownItems.Add("Clear all of them", null, (s, e) => ClearConditions());
            clear.Enabled = !string.IsNullOrWhiteSpace(c.Conditions);
            menu.Items.Add(cond);

            MISep(menu);
            if (!string.IsNullOrEmpty(c.Ref)) MI(menu, "Open the stat block", () => { if (Db.Find(c.Ref) is Creature b) ShowCreatureCard(b); });
            else if (c.IsPC && SoulOf(c) is PartyMember soul) MI(menu, "Open the Ledger", () => ShowSoulCard(soul));
            MI(menu, "Take them off the field", () => tracker.Remove(c));
        });

        page.Controls.Add(trkGrid);
        page.Controls.Add(bar);

        // empty-state hint — the tracker fills from OTHER tabs, which is invisible until told
        var hint = new Label
        {
            Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleCenter,
            Font = new Font("Segoe UI", 11f, FontStyle.Italic), ForeColor = Gold, BackColor = Paper,
            Text = "The field is empty.\n\nSend the posse over from the Posse tab (Send posse → Tracker),\npick a foe from the Foe box above, or drop one in from the Bestiary tab (→ Tracker)."
        };
        page.Controls.Add(hint);
        hint.BringToFront();
        hint.Visible = tracker.Count == 0;
        tracker.ListChanged += (s, e) => { hint.Visible = tracker.Count == 0; UpdateTurnLine(); };
        Watermark(trkGrid, () => GridBottom(trkGrid));
        Watermark(hint, () => HintBottom(hint));
        return page;
    }

    // Modeless creature windows: the Keeper can read a stat block and run the tracker at
    // the same time (a modal box locked the whole app while open). One window PER creature,
    // reused if that creature is already open — so two horrors can sit side by side. Each
    // window resizes, maximizes, and carries its own text-size controls.
    readonly Dictionary<string, Form> beastWindows = new(StringComparer.OrdinalIgnoreCase);
    void ShowCreatureCard(Creature c)
    {
        if (beastWindows.TryGetValue(c.name, out var open) && !open.IsDisposed)
        { open.BringToFront(); open.Activate(); return; }

        int cascade = (beastWindows.Count % 5) * 26;
        var win = new Form
        {
            Text = c.name, Width = 520, Height = 620, BackColor = Paper,
            MinimumSize = new Size(340, 300), StartPosition = FormStartPosition.Manual,
            Location = new Point(Math.Max(0, Right - 540 - cascade), Top + 80 + cascade)
        };
        if (AppIcon != null) win.Icon = AppIcon;
        var rtf = new RichTextBox { ReadOnly = true, BorderStyle = BorderStyle.None, BackColor = Paper, Font = new Font("Segoe UI", 10f) };
        var bar = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 42, Padding = new Padding(4, 2, 4, 2), BackColor = Color.FromArgb(243, 237, 221) };
        bar.Controls.Add(Btn("A−", (s, e) => rtf.ZoomFactor = Math.Max(0.7f, rtf.ZoomFactor - 0.15f), 46, "Smaller text"));
        bar.Controls.Add(Btn("A＋", (s, e) => rtf.ZoomFactor = Math.Min(3f, rtf.ZoomFactor + 0.15f), 46, "Larger text"));
        bar.Controls.Add(Btn("→ Tracker", (s, e) => AddCreatureToTracker(c), 95, "Drop one onto the battlefield"));
        win.Controls.Add(Pad(rtf, 16));                  // the words stay off the window edge
        win.Controls.Add(bar);
        RenderCreature(rtf, c);
        beastWindows[c.name] = win;
        win.FormClosed += (s, e) => beastWindows.Remove(c.name);
        win.Show(this);
    }

    void RollInitiative()
    {
        foreach (var c in tracker) c.Init = Rules.Rng.Next(1, 21);
        SortTracker(TrkSort.InitDesc);
        Log("Initiative rolled for the field.");
    }

    void NextRound()
    {
        round++;
        if (roundLbl != null) roundLbl.Text = $"Round {round}";
        // A new round means nobody has been handed the turn yet — the gold row would otherwise
        // sit on last round's combatant and read as though they were still up. The "Last" notes go
        // with it: they answer "what just happened", and at the top of a round nothing has.
        foreach (var c in tracker) { c.Acting = false; c.ClearLast(); }
        trkGrid?.Refresh(); UpdateTurnLine();
        Log($"— Round {round} —");
    }

    TrkSort trkSort = TrkSort.InitDesc;

    // the conditions from Appendix B, in the order the book lists them (Frightened and
    // Slowed carry a value, so their common steps are offered explicitly)
    static readonly string[] BookConditions =
    {
        "Bleeding", "Blinded", "Clumsy", "Drained", "Dying", "Fatigued",
        "Frightened 1", "Frightened 2", "Frightened 3", "Grabbed", "Off-Guard",
        "Prone", "Sickened", "Slowed 1", "Slowed 2", "Stunned", "Marked"
    };

    void SortTracker() => SortTracker(trkSort);
    void SortTracker(TrkSort mode)
    {
        trkSort = mode;
        try { trkGrid?.EndEdit(); } catch { }      // commit a half-typed Init before reading it
        // Remember WHO the Keeper had selected — clearing the list below resets the grid's
        // current row to the top, and every action that reads CurrentRow (Strike, Dread,
        // Damage) would then silently act on whoever the sort floated to row 0 instead of the
        // combatant the Keeper picked. Restore the same combatant after the reorder.
        var keep = trkGrid?.CurrentRow?.DataBoundItem as Combatant;
        var sorted = (mode switch
        {
            TrkSort.InitDesc  => tracker.OrderByDescending(c => c.Init).ThenByDescending(c => c.IsPC).ThenBy(c => c.Name),
            TrkSort.InitAsc   => tracker.OrderBy(c => c.Init).ThenByDescending(c => c.IsPC).ThenBy(c => c.Name),
            TrkSort.NameAsc   => tracker.OrderBy(c => c.Name),
            TrkSort.NameDesc  => tracker.OrderByDescending(c => c.Name),
            TrkSort.BloodDesc => tracker.OrderByDescending(c => c.BloodCur).ThenBy(c => c.Name),
            TrkSort.BloodAsc  => tracker.OrderBy(c => c.BloodCur).ThenBy(c => c.Name),
            _                 => tracker.OrderByDescending(c => c.Init).ThenByDescending(c => c.IsPC).ThenBy(c => c.Name),
        }).ToList();
        tracker.RaiseListChangedEvents = false;
        tracker.Clear();
        foreach (var c in sorted) tracker.Add(c);
        tracker.RaiseListChangedEvents = true;
        tracker.ResetBindings();
        RestoreTrkSelection(keep);
        trkGrid?.Refresh();
    }

    // Re-seat the grid's current row on a specific combatant after the list was rebuilt, so the
    // Keeper's selection survives a sort/roll-initiative. No match (it was removed) leaves the
    // grid as-is rather than guessing.
    void RestoreTrkSelection(Combatant keep)
    {
        if (trkGrid == null || keep == null) return;
        int row = tracker.IndexOf(keep);
        if (row < 0 || row >= trkGrid.Rows.Count) return;
        try
        {
            trkGrid.ClearSelection();
            trkGrid.CurrentCell = trkGrid.Rows[row].Cells[0];
            trkGrid.Rows[row].Selected = true;
        }
        catch { /* grid mid-rebuild — the next click re-selects */ }
    }

    // Ad-hoc combatant: a named NPC, a hireling, an improvised foe — anything not in the
    // Bestiary. Blood/Defense by hand; the PC flag just tints the row green like the posse.
    void AddCustomCombatant()
    {
        using var f = new Form { Width = 350, Height = 258, Text = "Add combatant", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper };
        var l1 = new Label { Left = 16, Top = 18, Width = 80, Text = "Name:" };
        var name = new TextBox { Left = 104, Top = 15, Width = 210, Text = "Bandit" };
        var l2 = new Label { Left = 16, Top = 54, Width = 80, Text = "Blood:" };
        var blood = new NumericUpDown { Left = 104, Top = 51, Width = 80, Minimum = 1, Maximum = 9999, Value = 12 };
        var l3 = new Label { Left = 16, Top = 90, Width = 80, Text = "Defense:" };
        var def = new NumericUpDown { Left = 104, Top = 87, Width = 80, Minimum = 0, Maximum = 40, Value = 13 };
        var pc = new CheckBox { Left = 104, Top = 122, Width = 210, Text = "Player character (green row)" };
        var ok = new Button { Text = "Add", Left = 138, Top = 168, Width = 84, DialogResult = DialogResult.OK };
        var cancel = new Button { Text = "Cancel", Left = 230, Top = 168, Width = 84, DialogResult = DialogResult.Cancel };
        f.Controls.AddRange(new Control[] { l1, name, l2, blood, l3, def, pc, ok, cancel });
        f.AcceptButton = ok; f.CancelButton = cancel;
        if (f.ShowDialog(this) == DialogResult.OK && !string.IsNullOrWhiteSpace(name.Text))
        {
            int b = (int)blood.Value;
            tracker.Add(new Combatant { Name = name.Text.Trim(), BloodCur = b, BloodMax = b, Defense = (int)def.Value, IsPC = pc.Checked });
            Log($"Tracker: {name.Text.Trim()} added by hand ({b} Blood).");
        }
    }

    void ApplyCondition(string cond)
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Nope("Select a combatant first."); return; }
        ApplyConditionTo(c, cond);
    }

    /// <summary>Tag a named combatant, whoever the grid happens to be sitting on. The bar's
    /// ＋ Condition and the engine's own outcomes (a Dread Check that goes badly, a sign read while
    /// standing over it) both come through here, so "Frightened 1" means one thing in the app.</summary>
    void ApplyConditionTo(Combatant c, string cond)
    {
        if (c == null) return;
        var set = c.Conditions.Split(',', StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries).ToList();
        // a valued condition supersedes its other steps (one Frightened, not three)
        string family = cond.Split(' ')[0];
        if (cond != family) set.RemoveAll(x => x.StartsWith(family + " ") || x == family);
        if (!set.Contains(cond)) set.Add(cond);
        c.Conditions = string.Join(", ", set);
        trkGrid.Refresh();
        Log($"{c.Name}: {cond}.");
    }

    /// <summary>Ask the Keeper for the die they just rolled — the dice-and-books table's half of a
    /// roll the engine would otherwise make for them. Returns null when the engine is doing the
    /// rolling, so a caller can pass the result straight through as the "forced die".</summary>
    int? AskDie(string prompt)
    {
        if (EngineRolls) return null;
        using var f = new Form
        {
            Text = "The die", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent,
            MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper
        };
        const int Pad = 16, CW = 330;
        var say = new Label
        {
            Left = Pad, Top = Pad, Width = CW, Text = prompt, ForeColor = Ink,
            Height = TextRenderer.MeasureText(prompt, f.Font, new Size(CW, 0), TextFormatFlags.WordBreak).Height + 4
        };
        var d20 = new NumericUpDown { Left = Pad, Top = say.Bottom + 10, Width = 74, Minimum = 1, Maximum = 20, Value = 10 };
        var ok = new Button { Text = "That's the roll", Left = Pad + CW - 120, Top = d20.Top - 2, Width = 120, Height = 30, DialogResult = DialogResult.OK };
        f.Controls.AddRange(new Control[] { say, d20, ok });
        f.ClientSize = new Size(CW + Pad * 2, ok.Bottom + Pad);
        f.AcceptButton = ok;
        f.ShowDialog(this);
        return (int)d20.Value;
    }

    void ClearConditions()
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Nope("Select a combatant first."); return; }
        c.Conditions = ""; trkGrid.Refresh();
        Log($"{c.Name}: conditions cleared.");
    }

    // Set up the next encounter without losing the party: clear the foes, wipe the
    // per-fight conditions off the survivors, and drop back to Round 1. Blood carries over
    // (use the Posse tab's Rest to heal up between fights).
    void NewFight()
    {
        var foes = tracker.Where(c => !c.IsPC).ToList();
        if (foes.Count == 0) { Nope("No foes on the field to clear."); round = 1; if (roundLbl != null) roundLbl.Text = "Round 1"; return; }
        if (!Confirm($"New fight? Clears {foes.Count} foe(s), keeps the posse, resets to Round 1.")) return;
        foreach (var f in foes) tracker.Remove(f);
        // a fresh fight: nothing carried over — no conditions, no spent Beats, nobody mid-turn
        foreach (var c in tracker) { c.Conditions = ""; c.Beats = 3; c.MapStep = 1; c.Acting = false; c.ClearLast(); }
        round = 1; if (roundLbl != null) roundLbl.Text = "Round 1"; trkGrid?.Refresh(); UpdateTurnLine();
        Log("New fight — foes cleared, the posse holds the field, Round 1.");
    }

    /// <summary>The name a trace goes on the field under. "Sign of the Wendigo" rather than "Sign of
    /// The Wendigo" — the article belongs to the sentence now, not to the heading it came from.</summary>
    internal static string SignName(string creatureName)
    {
        string n = creatureName ?? "";
        if (n.StartsWith("The ", StringComparison.Ordinal)) n = "the " + n.Substring(4);
        return "Sign of " + n;
    }

    /// <summary>Put a creature's TRACE on the field instead of the creature (the safe-table rule).
    /// One row, however many were asked for: a thing two Tiers over the posse is one thread, and
    /// four copies of a thread is not a thing a table can run.</summary>
    void AddSignToTracker(Creature c)
    {
        string name = SignName(c.name);
        if (tracker.Any(t => t.IsSign && string.Equals(t.Ref, c.name, StringComparison.OrdinalIgnoreCase)))
        { Nope($"{name} is already on the field — read it again to fill another segment."); return; }
        var (readDc, dreadDc, what) = Rules.SpoorFor(c.tier);
        tracker.Add(new Combatant
        {
            Name = name, Ref = c.name, IsSign = true,
            BloodCur = 0, BloodMax = 0, Defense = 0, Beats = 0,
            Conditions = what
        });
        Log($"{name} — the trace, not the thing. Survival DC {readDc} to read it"
            + (dreadDc == 0 ? ", and it costs no Nerve" : $", Dread DC {dreadDc}")
            + $". A {Rules.SpoorClockSegments}-segment clock; a full one is the night it comes in the flesh.");
    }

    /// <summary>Ask, once, whether a horror the safe-table rule bars should take the field anyway.
    /// The rule is the Keeper's Book's, not the app's, so this offers rather than refuses — but it
    /// offers the book's answer first, and says what the cost of the other one is.</summary>
    bool AskInTheFlesh(Creature c, int partyLevel)
    {
        using var f = new Form
        {
            Text = "The safe-table rule", FormBorderStyle = FormBorderStyle.FixedDialog,
            StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false,
            ShowIcon = false, BackColor = Paper
        };
        const int Pad = 16, CW = 460;
        Label Para(string text, int top, Font font, Color fore)
            => new()
            {
                Left = Pad, Top = top, Width = CW, Text = text, Font = font, ForeColor = fore,
                Height = TextRenderer.MeasureText(text, font, new Size(CW, 0), TextFormatFlags.WordBreak).Height + 4
            };
        var (readDc, dreadDc, what) = Rules.SpoorFor(c.tier);
        var head = Para($"{c.name} is Tier {Rules.Roman(c.tier)}, two or more Tiers over a posse of level "
                      + $"{partyLevel}. The book does not put it in front of them yet.", Pad, DialogBold, Blood);
        var body = Para($"As sign & spoor it arrives as “{what.ToLowerInvariant()}” — Survival DC {readDc} to read"
                      + (dreadDc == 0 ? ", costing no Nerve" : $", Dread DC {dreadDc}")
                      + $", and a {Rules.SpoorClockSegments}-segment clock that fills every time the posse "
                      + "crosses its trail. A full clock is the night it comes anyway.", head.Bottom + 8, f.Font, Ink);
        var warn = Para("In the flesh, at this level, it is very likely a funeral.", body.Bottom + 8, DialogItalic, Gold);
        var asSign = new Button { Text = "Sign && spoor", Left = Pad, Top = warn.Bottom + 14, Width = 150, Height = 32, DialogResult = DialogResult.Yes };
        var flesh  = new Button { Text = "In the flesh", Left = Pad + 158, Top = asSign.Top, Width = 130, Height = 32, DialogResult = DialogResult.No };
        var cancel = new Button { Text = "Cancel", Left = Pad + CW - 92, Top = asSign.Top, Width = 92, Height = 32, DialogResult = DialogResult.Cancel };
        f.Controls.AddRange(new Control[] { head, body, warn, asSign, flesh, cancel });
        f.ClientSize = new Size(CW + Pad * 2, asSign.Bottom + Pad);
        f.AcceptButton = asSign; f.CancelButton = cancel;

        var answer = f.ShowDialog(this);
        if (answer == DialogResult.Yes) { AddSignToTracker(c); return false; }
        return answer == DialogResult.No;
    }

    void AddCreatureToTracker(Creature c, int count = 1, bool skipSafeTable = false)
    {
        // The one place every route onto the battlefield goes through — the Bestiary's → Tracker,
        // the Foe box, the Encounter's Send all, the right-click menus — so the safe-table rule
        // gets asked once, here, rather than in five places that would each forget it differently.
        if (!skipSafeTable && Rules.SignOnly(c.tier, partyLevelHint) && !AskInTheFlesh(c, partyLevelHint)) return;
        count = Math.Clamp(count, 1, 20);
        // number from the highest existing suffix, not the row count — otherwise
        // add/remove/add mints two "#2"s
        var kin = tracker.Where(t => t.Ref == c.name).ToList();
        int start = kin.Count == 0 ? 0 : kin.Max(t =>
        {
            var m = System.Text.RegularExpressions.Regex.Match(t.Name, @"#(\d+)$");
            return m.Success ? int.Parse(m.Groups[1].Value) : 1;
        });
        for (int i = 1; i <= count; i++)
        {
            int k = start + i;
            bool bare = start == 0 && count == 1;   // a lone first copy stays unnumbered
            tracker.Add(new Combatant
            {
                Name = bare ? c.name : $"{c.name} #{k}",
                BloodCur = c.BloodValue, BloodMax = c.BloodValue,
                Defense = c.DefenseValue, Ref = c.name
            });
        }
        Log(count == 1
            ? $"Tracker: {c.name} takes the field ({c.BloodValue} Blood)."
            : $"Tracker: {count}× {c.name} take the field ({c.BloodValue} Blood each).");
    }

    void AdjustCombatant(int sign)
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Nope("Select a combatant first."); return; }
        if (c.IsSign) { Nope($"{c.Name} is a trace, not a body — there is nothing there to wound or mend."); return; }
        int v = (int)trkAmount.Value;
        int was = c.BloodCur;
        c.Wound(sign * v);                                     // clamps, and leaves the "Last" note
        Log($"{c.Name} {(sign < 0 ? "takes" : "recovers")} {Math.Abs(c.BloodCur - was)} → {c.BloodCur}/{c.BloodMax}" + (c.Down ? "  — PUT DOWN." : ""));
        trkGrid.Refresh();
        if (SoulOf(c) is PartyMember p) { p.BloodCur = c.BloodCur; posseGrid?.Refresh(); }
    }

    /// <summary>Put the selected combatant back to full Blood — the ad-hoc heal a Keeper wants
    /// between scenes without arithmetic. A posse soul gets their Nerve and pool back too, because
    /// for a soul "restored" means the whole of what a long rest restores.</summary>
    void RestoreSelected()
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Nope("Select a combatant first."); return; }
        if (c.IsSign) { Nope($"{c.Name} is a trace — there is nothing there to restore."); return; }
        if (SoulOf(c) is PartyMember soul) { RestSoul(soul); c.Wound(c.BloodMax - c.BloodCur, "restored"); }
        else if (c.BloodMax <= 0) { Nope($"{c.Name} has no Blood maximum to restore to — set one in the /Max column."); return; }
        else
        {
            c.Wound(c.BloodMax - c.BloodCur, "restored");
            Log($"{c.Name} is made whole — {c.BloodCur}/{c.BloodMax} Blood.");
        }
        trkGrid.Refresh(); UpdateTurnLine();
    }

    /// <summary>Everyone on the field back to full Blood, and every posse soul back to full Nerve
    /// with them. The scene is over; this is the line between one and the next.</summary>
    void RestoreField()
    {
        var bodies = tracker.Where(t => !t.IsSign && t.BloodMax > 0).ToList();
        if (bodies.Count == 0) { Nope("Nobody on the field has Blood to restore."); return; }
        int hurt = bodies.Count(t => t.BloodCur < t.BloodMax);
        if (!Confirm($"Restore everyone on the field? {hurt} of {bodies.Count} are carrying wounds; "
                   + "every posse soul also gets their Nerve and pool back."))
            return;
        foreach (var t in bodies) t.Wound(t.BloodMax - t.BloodCur, "restored");
        foreach (var p in party.Where(p => tracker.Any(t => t.IsSoul(p))))
        { p.BloodCur = p.BloodMax; p.NerveCur = p.NerveMax; p.PoolCur = p.PoolMax; }
        posseGrid?.Refresh(); trkGrid?.Refresh(); UpdateTurnLine();
        Log($"The field is restored — {bodies.Count} back to full Blood, the posse's Nerve with them.");
    }

    // The posse soul behind a tracker row, matched by the stable id (Name only as a legacy
    // fallback) — so damage mirrors back to the right soul even after a rename.
    PartyMember SoulOf(Combatant c) => c != null && c.IsPC ? party.FirstOrDefault(c.IsSoul) : null;

    // The selected combatant's turn begins: three Beats, the next Strike clean (Ch. XI).
    void BeginTurnForSelected()
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Nope("Select a combatant first."); return; }
        if (c.IsSign) { Nope($"{c.Name} takes no turn — it is a trace. Read it (Read sign ▸)."); return; }
        foreach (var t in tracker) t.Acting = false;   // one at a time; the last turn is over
        c.BeginTurn(); trkGrid.Refresh(); UpdateTurnLine();
        Log($"{c.Name}'s turn — 3 Beats, a clean shot.");
    }

    // Resolve a Strike from the selected combatant through the Iron Code engine: to hit, the four
    // degrees, the Multiple Attack Penalty at this combatant's current step, the Fatal die on a
    // crit, and the damage after the target's DR — then spend the Beat and apply it.
    void StrikeDialog()
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant attacker) { Nope("Select the attacker first."); return; }
        // The safe-table rule, enforced at the only place it could be broken: a trace has nothing
        // to swing and nothing to be shot at. Reading it is the scene.
        if (attacker.IsSign)
        { Nope($"{attacker.Name} is a trace, not the thing — it strikes nobody. Read it instead (Read sign ▸)."); return; }
        var foes = tracker.Where(t => !ReferenceEquals(t, attacker) && !t.IsSign).ToList();
        if (foes.Count == 0)
        { Nope(tracker.Any(t => t.IsSign) ? "Nothing on the field to strike — only sign & spoor, which is read, not shot."
                                          : "Nothing on the field to strike."); return; }

        // A creature strikes with its OWN attacks, parsed from the Bestiary line; a soul (or a
        // hand-entered row) reaches for the posse's guns. The attacker's Ref names its creature.
        var sheet = SoulOf(attacker)?.Sheet;
        var (catks, riders, creature) = CombatMenu.For(attacker);
        bool asCreature = creature != null;

        bool hasSpecials = asCreature && (!string.IsNullOrWhiteSpace(creature.special) || riders.Count > 0);
        // Everything below is laid out by measurement, not by guessed constants. The prose here
        // changes with the run mode and with whether a creature or a soul is swinging, and the
        // old fixed heights cut the last line of it — and the Beats count — off the right edge.
        const int Pad = 16, CW = 500;   // left margin and the content width every row shares
        using var f = new Form { Text = $"{attacker.Name} strikes", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper };
        Label L(string t, int top) => new() { Left = Pad, Top = top + 3, Width = 92, Text = t };
        // A block of prose sized to the words in it, so it can never be clipped at any DPI.
        Label Para(string text, int top, Font font, Color fore)
            => new()
            {
                Left = Pad, Top = top, Width = CW, Text = text, Font = font, ForeColor = fore,
                Height = TextRenderer.MeasureText(text, font, new Size(CW, 0), TextFormatFlags.WordBreak).Height + 4
            };
        var target = new ComboBox { Left = 112, Top = 15, Width = CW - 96, DropDownStyle = ComboBoxStyle.DropDownList };
        foreach (var t in foes) target.Items.Add(t.Name);
        target.SelectedIndex = 0;
        var weapon = new ComboBox { Left = 112, Top = 51, Width = CW - 96, DropDownStyle = ComboBoxStyle.DropDownList };
        if (asCreature)
            foreach (var a in catks)
                weapon.Items.Add($"{a.Name}  +{a.Bonus} ({(a.DealsDamage ? a.Damage : "no dice")}{(a.Type != "blades" ? " " + a.Type : "")})"
                                 + (string.IsNullOrEmpty(a.Effect) ? "" : "  · " + a.Effect));
        else
            foreach (var w in CharGen.D.weapons) weapon.Items.Add($"{w.name}  ({w.dmg}{(string.IsNullOrEmpty(w.traits) ? "" : ", " + w.traits)})");
        var toHit = new NumericUpDown { Left = 112, Top = 87, Width = 70, Minimum = -20, Maximum = 40, Value = 0 };
        var dr = new NumericUpDown { Left = 112, Top = 123, Width = 70, Minimum = 0, Maximum = 40, Value = 0 };
        var mapLbl = new Label { Left = 196, Top = 90, Width = Pad + CW - 196, Height = 20, ForeColor = Blood, AutoEllipsis = true };
        // Dice-and-books table: the Keeper rolls the d20 and enters it; the engine table rolls its own.
        var d20 = new NumericUpDown { Left = 248, Top = 123, Width = 60, Minimum = 1, Maximum = 20, Value = 10 };

        // Prefill the to-hit — a creature's built-in bonus, or a soul's own off their sheet — and
        // re-figure it (and the MAP) when the chosen attack changes.
        void Sync()
        {
            int idx = Math.Max(0, weapon.SelectedIndex);
            bool agile;
            if (asCreature) { toHit.Value = Math.Clamp(catks[idx].Bonus, -20, 40); agile = false; }
            else
            {
                var w = CharGen.D.weapons[idx];
                if (sheet != null) toHit.Value = Math.Clamp(CombatFlow.AttackBonusFor(sheet, w), -20, 40);
                agile = WeaponTraits.Parse(w.traits).Agile;
            }
            int map = IronCode.MapPenalty(attacker.MapStep, agile);
            mapLbl.Text = $"This Strike: {(map == 0 ? "clean, no MAP" : "MAP " + map)}  ·  "
                + (attacker.Beats > 0
                    ? $"{attacker.Beats} Beat{(attacker.Beats == 1 ? "" : "s")} left"
                    : "no Beats left — Begin turn on the tracker");
        }
        // default a soul to the gun they carry if we can spot one, else the first attack
        int guess = asCreature ? -1
            : sheet?.WeaponsCarried?.Select(wc => CharGen.D.weapons.FindIndex(w => wc.StartsWith(w.name)))
                   .FirstOrDefault(ix => ix >= 0) ?? -1;
        weapon.SelectedIndex = guess >= 0 ? guess : 0;
        weapon.SelectedIndexChanged += (s, e) => Sync();
        Sync();

        var how = Para(
            (EngineRolls ? "The engine rolls the d20 and reads the four degrees"
                         : "You roll the d20 and enter it above; the engine reads the four degrees")
            + ", applies the Multiple Attack Penalty at this combatant's step"
            + (asCreature ? "" : " and the Fatal die on a critical hit")
            + ", subtracts the target's DR, takes the Blood, and spends a Beat. Strike again to take "
            + "the next one at higher MAP; Begin turn on the tracker gives the Beats back and makes "
            + "the shot clean.", 160, f.Font, Ink);

        f.Controls.AddRange(new Control[] {
            L("Target:", 15), target, L(asCreature ? "Attack:" : "Weapon:", 51), weapon, L("To hit:", 87), toHit, mapLbl,
            L("Target DR:", 123), dr, how });
        if (!EngineRolls)
        {
            f.Controls.Add(new Label { Left = 196, Top = 126, Width = 48, Text = "d20:", ForeColor = Blood, TextAlign = ContentAlignment.MiddleRight });
            f.Controls.Add(d20);
        }

        int y = how.Bottom + 12;
        if (hasSpecials)
        {
            var bits = new List<string>();
            if (!string.IsNullOrWhiteSpace(creature.special)) bits.Add(creature.special.Trim());
            foreach (var r in riders) bits.Add("• " + char.ToUpper(r[0]) + r.Substring(1));
            var head = Para("Its special work — narrate as it fights:", y, DialogItalic, Blood);
            f.Controls.Add(head);
            // Sized to the words, capped so a wordy horror can't push the buttons off a small
            // screen — past the cap it scrolls.
            string body = string.Join("\r\n", bits);
            int wanted = TextRenderer.MeasureText(body, f.Font, new Size(CW - 8, 0), TextFormatFlags.WordBreak).Height + 12;
            var box = new TextBox
            {
                Left = Pad, Top = head.Bottom + 4, Width = CW, Height = Math.Clamp(wanted, 56, 150),
                Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Vertical,
                BorderStyle = BorderStyle.FixedSingle, BackColor = Paper, Text = body
            };
            f.Controls.Add(box);
            y = box.Bottom + 14;
        }

        var ok = new Button { Text = "Strike ▸", Left = Pad + CW - 182, Top = y, Width = 90, DialogResult = DialogResult.OK };
        var cancel = new Button { Text = "Close", Left = Pad + CW - 84, Top = y, Width = 84, DialogResult = DialogResult.Cancel };
        f.Controls.AddRange(new Control[] { ok, cancel });
        f.ClientSize = new Size(CW + Pad * 2, ok.Bottom + Pad);
        f.AcceptButton = ok;

        while (f.ShowDialog(this) == DialogResult.OK)
        {
            var tgt = foes[target.SelectedIndex];
            var drList = dr.Value > 0 ? new[] { new DrEntry((int)dr.Value, "all") } : null;
            int idx = Math.Max(0, weapon.SelectedIndex);
            int? forced = EngineRolls ? null : (int)d20.Value;
            var rep = asCreature
                ? CombatFlow.StrikeAndApply(attacker, tgt, catks[idx], (int)toHit.Value, drList, forced)
                : CombatFlow.StrikeAndApply(attacker, tgt, CharGen.D.weapons[idx], (int)toHit.Value, drList, forced);
            Log(rep.Line + (asCreature && !string.IsNullOrEmpty(catks[idx].Effect) && rep.Res.Strike.Hit ? $"  — {catks[idx].Effect}." : ""));
            // the Strike reads on the Dice tab's card too, graded like any other check
            ShowResult(rep.Res.Strike.DegreeName, rep.Line, DegreeColor(rep.Res.Strike.DegreeName));
            if (SoulOf(tgt) is PartyMember tp) { tp.BloodCur = tgt.BloodCur; posseGrid?.Refresh(); }
            // Beats/MAP moved on — say so in both places, and keep the dialog live for a follow-up
            trkGrid.Refresh(); UpdateTurnLine(); Sync();
        }
    }

    // Roll a Dread Check for the selected soul (Ch. XII): Will save vs the Dread DC, Nerve off the
    // ladder on a failure, Frightened on a critical failure — and, at 0 Nerve, the break table.
    void DreadDialog()
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Nope("Select a soul first."); return; }
        var soul = SoulOf(c);
        if (soul == null) { Nope("Dread Checks are for the posse — select a player's soul."); return; }

        using var f = new Form { Width = 430, Height = 300, Text = $"{soul.Name} — Dread Check", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper };
        f.Controls.Add(new Label { Left = 16, Top = 14, Width = 390, Text = $"Will save {(soul.Will >= 0 ? "+" : "")}{soul.Will} vs the Dread DC. Nerve now {soul.NerveCur}/{soul.NerveMax}." });
        var dc = new NumericUpDown { Left = 112, Top = 48, Width = 70, Minimum = 5, Maximum = 40, Value = 16 };
        f.Controls.Add(new Label { Left = 16, Top = 51, Width = 92, Text = "Dread DC:" });
        f.Controls.Add(dc);
        int top = 84;
        foreach (var (label, val) in new[] { ("A fresh corpse (10)", 10), ("A mutilation (13)", 13),
            ("The walking dead (16)", 16), ("A thing from outside (20)", 20), ("A world unmade (25)", 25) })
        {
            var b = new Button { Left = 16, Top = top, Width = 185, Height = 26, Text = label, TextAlign = ContentAlignment.MiddleLeft };
            int v = val; b.Click += (s, e) => dc.Value = v;
            f.Controls.Add(b); top += 30;
        }
        var check = new Button { Text = "Check ▸", Left = 250, Top = 90, Width = 150, Height = 34, DialogResult = DialogResult.OK };
        var close = new Button { Text = "Close", Left = 250, Top = 132, Width = 150, Height = 30, DialogResult = DialogResult.Cancel };
        f.Controls.AddRange(new Control[] { check, close });
        // Dice-and-books table: the Keeper rolls the Will save and enters it; the engine table rolls it.
        var d20 = new NumericUpDown { Left = 335, Top = 174, Width = 65, Minimum = 1, Maximum = 20, Value = 10 };
        if (!EngineRolls)
        {
            f.Controls.Add(new Label { Left = 250, Top = 176, Width = 82, Text = "d20 rolled:", ForeColor = Blood });
            f.Controls.Add(d20);
        }
        f.AcceptButton = check;

        while (f.ShowDialog(this) == DialogResult.OK)
        {
            var o = Horror.DreadCheck(soul.Will, (int)dc.Value, EngineRolls ? null : (int)d20.Value);
            Log($"{soul.Name}: {o.Line}");
            ShowResult(o.DegreeName, $"{soul.Name}: {o.Line}", DegreeColor(o.DegreeName));
            if (o.NerveLost > 0) soul.NerveCur = Math.Max(0, soul.NerveCur - o.NerveLost);
            if (o.Frightened) ApplyCondition("Frightened 1");   // applies to the selected row (this soul)
            if (soul.NerveCur == 0)
            {
                var bk = Horror.Break();
                Log($"{soul.Name} {bk.Line}");
                if (bk.GainsMark) soul.Mark += 1;
            }
            posseGrid?.Refresh(); trkGrid?.Refresh();
        }
    }

    /// <summary>Read a sign & spoor row: a Survival check at the Tier's DC, what the four degrees
    /// give the tracker, the Dread it costs them, and one more segment of the clock. This is the
    /// safe-table rule as a scene you can actually run — the thing takes part in the fight through
    /// what it left behind, and the fight is against the reading.</summary>
    void ReadSignDialog()
    {
        var sign = trkGrid.CurrentRow?.DataBoundItem as Combatant;
        // Being helpful about the selection: with exactly one sign on the field, the Keeper who
        // presses this plainly means that one, whichever row the grid happens to be sitting on.
        if (sign is not { IsSign: true })
        {
            var signs = tracker.Where(t => t.IsSign).ToList();
            if (signs.Count == 0) { Nope("No sign & spoor on the field. A creature too far over the posse arrives as one."); return; }
            if (signs.Count > 1) { Nope("Select which sign is being read — there is more than one on the field."); return; }
            sign = signs[0];
        }
        var beast = Db.Find(sign.Ref);
        int tier = beast?.tier ?? 1;
        var (readDc, dreadDc, what) = Rules.SpoorFor(tier);

        var readers = tracker.Where(t => SoulOf(t) != null).Select(t => SoulOf(t)).ToList();
        if (readers.Count == 0) readers = party.ToList();
        if (readers.Count == 0) { Nope("Nobody to read it — put the posse on the field first."); return; }

        const int Pad = 16, CW = 470;
        using var f = new Form
        {
            Text = $"{sign.Name} — read it", FormBorderStyle = FormBorderStyle.FixedDialog,
            StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false,
            ShowIcon = false, BackColor = Paper
        };
        Label Para(string text, int top, Font font, Color fore)
            => new()
            {
                Left = Pad, Top = top, Width = CW, Text = text, Font = font, ForeColor = fore,
                Height = TextRenderer.MeasureText(text, font, new Size(CW, 0), TextFormatFlags.WordBreak).Height + 4
            };
        Label L(string t, int top) => new() { Left = Pad, Top = top + 3, Width = 104, Text = t };

        var ground = Para($"On the ground: {what.ToLowerInvariant()}.", Pad, DialogBold, Blood);
        var who = new ComboBox { Left = Pad + 108, Top = ground.Bottom + 11, Width = CW - 108, DropDownStyle = ComboBoxStyle.DropDownList };
        foreach (var p in readers) who.Items.Add(p.Name);
        who.SelectedIndex = 0;
        var whoLbl = L("Who reads it:", ground.Bottom + 8);

        var mod = new NumericUpDown { Left = Pad + 108, Top = who.Bottom + 8, Width = 74, Minimum = -20, Maximum = 40 };
        var modLbl = L("Survival:", who.Bottom + 5);
        var modNote = new Label
        {
            Left = Pad + 190, Top = who.Bottom + 8, Width = CW - 190, Height = 20,
            ForeColor = Gold, Font = DialogItalic, AutoEllipsis = true
        };
        // Prefilled from the reader's own sheet by the book's formula (Ch. VIII), so the Keeper
        // isn't asked for a number the app already knows — and can still overrule it.
        void SyncReader()
        {
            var p = readers[Math.Max(0, who.SelectedIndex)];
            var sheet = p.Sheet;
            if (sheet != null)
            {
                mod.Value = Math.Clamp(CharGen.SkillBonus(sheet, "Survival"), -20, 40);
                int rank = sheet.SkillRanks != null && sheet.SkillRanks.TryGetValue("Survival", out int r) ? r : 0;
                modNote.Text = rank <= 0 ? "untrained — RES alone"
                    : (rank >= 3 ? "master" : rank == 2 ? "expert" : "trained") + $", level {sheet.Level}";
            }
            else { modNote.Text = "no sheet on this soul — set the bonus by hand"; }
        }
        who.SelectedIndexChanged += (s, e) => SyncReader();
        SyncReader();

        var dcLine = Para($"Survival DC {readDc}  ·  "
            + (dreadDc == 0 ? "no Dread — this one is only weather and teeth" : $"Dread DC {dreadDc} for the reader")
            + $"  ·  clock {sign.SignFilled} of {Rules.SpoorClockSegments}", mod.Bottom + 10, DialogItalic, Ink);

        var d20 = new NumericUpDown { Left = Pad + 108, Top = dcLine.Bottom + 8, Width = 68, Minimum = 1, Maximum = 20, Value = 10 };
        var d20Lbl = L("d20 rolled:", dcLine.Bottom + 5);
        int afterDice = EngineRolls ? dcLine.Bottom : d20.Bottom + 4;

        var how = Para("Every reading is a fresh crossing of its trail, so every reading fills a segment — "
            + "what the roll decides is what the tracker takes away from the crossing. A full clock is the "
            + "night it stops leaving sign and arrives.", afterDice + 8, f.Font, Ink);

        var go = new Button { Text = "Read it ▸", Left = Pad + CW - 198, Top = how.Bottom + 14, Width = 100, Height = 32, DialogResult = DialogResult.OK };
        var close = new Button { Text = "Close", Left = Pad + CW - 92, Top = go.Top, Width = 92, Height = 32, DialogResult = DialogResult.Cancel };
        f.Controls.AddRange(new Control[] { ground, whoLbl, who, modLbl, mod, modNote, dcLine, how, go, close });
        if (!EngineRolls) f.Controls.AddRange(new Control[] { d20Lbl, d20 });
        f.ClientSize = new Size(CW + Pad * 2, go.Bottom + Pad);
        f.AcceptButton = go; f.CancelButton = close;

        while (f.ShowDialog(this) == DialogResult.OK)
        {
            var reader = readers[Math.Max(0, who.SelectedIndex)];
            var o = Horror.ReadSign((int)mod.Value, tier, EngineRolls ? null : (int)d20.Value);
            Log($"{reader.Name} reads {sign.Name}: {o.Detail} → {o.DegreeName}. {o.Learned}");
            ShowResult(o.DegreeName, $"{reader.Name} reads {sign.Name}: {o.Learned}", DegreeColor(o.DegreeName));

            // The Dread of standing over it — one rung below meeting the thing, and nothing at all
            // for a Tier I trace, which is a dead rabbit eaten the way rabbits get eaten.
            if (o.DreadDc > 0)
            {
                var d = Horror.DreadCheck(reader.Will, o.DreadDc,
                    AskDie($"{reader.Name}'s Will save against the Dread of it (DC {o.DreadDc}) — what did the d20 come up?"));
                Log($"{reader.Name}: {d.Line}");
                if (d.NerveLost > 0) reader.NerveCur = Math.Max(0, reader.NerveCur - d.NerveLost);
                if (d.Frightened) ApplyConditionTo(tracker.FirstOrDefault(t => t.IsSoul(reader)), "Frightened 1");
                if (reader.NerveCur == 0)
                {
                    var bk = Horror.Break();
                    Log($"{reader.Name} {bk.Line}");
                    if (bk.GainsMark) reader.Mark += 1;
                }
            }

            if (o.FillsClock) sign.SignFilled += 1;
            dcLine.Text = $"Survival DC {readDc}  ·  "
                + (dreadDc == 0 ? "no Dread — this one is only weather and teeth" : $"Dread DC {dreadDc} for the reader")
                + $"  ·  clock {sign.SignFilled} of {Rules.SpoorClockSegments}";
            posseGrid?.Refresh(); trkGrid?.Refresh();

            if (sign.SignFull) { SignArrives(sign, beast); break; }
        }
    }

    /// <summary>The clock is full: the thing stops leaving sign. Offered rather than done, because
    /// WHEN it walks in is the Keeper's call — but the row is spent either way, and leaving a full
    /// clock sitting on the field is how a thread quietly stops meaning anything.</summary>
    void SignArrives(Combatant sign, Creature beast)
    {
        Log($"{sign.Name}: the clock is full. It stops leaving sign.");
        string ask = beast == null
            ? $"{sign.Name}'s clock is full — the thread is spent. Take it off the field?"
            : $"{sign.Name}'s clock is full. It comes in the flesh: put {beast.name} on the field "
              + $"in its place — {beast.BloodValue} Blood, Defense {beast.DefenseValue}?";
        if (!Confirm(ask)) return;
        tracker.Remove(sign);
        if (beast != null)
        {
            AddCreatureToTracker(beast, 1, skipSafeTable: true);   // the rule has already run its course
            Log($"{beast.name} comes in the flesh. The safe table is over.");
        }
        trkGrid?.Refresh(); UpdateTurnLine();
    }

    // ============================================================ GENERATORS TAB
    RichTextBox genOut;

    // The last town and the last city rolled, kept so they can be handed to the Map tab as a
    // place to survey. A rolled town that can't be drawn is a rolled town the Keeper writes on
    // a napkin — this is the seam between "what's here" and "what it looks like".
    string genLastTown, genLastCity;

    TabPage BuildGeneratorsTab()
    {
        var page = new TabPage("Generators") { BackColor = Paper };
        var split = Split(Orientation.Vertical, 300, 300, 0.27);

        var left = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.TopDown, WrapContents = false, Padding = new Padding(12), AutoScroll = true, BackColor = Paper };
        left.Controls.Add(Heading("The Country in Your Pocket"));

        // The two "→ Map" buttons are built first so the roll handlers can wake them, and they
        // start asleep: a button that sends nowhere is worse than no button.
        var townToMap = Btn("→ Map — survey this town", (s, e) => SendPlaceToMap(genLastTown, city: false), 230,
            "Draw a map of the town just rolled — its name goes on the survey");
        var cityToMap = Btn("→ Map — survey this ward", (s, e) => SendPlaceToMap(genLastCity, city: true), 230,
            "Draw a city-ward map of the quarter just rolled — blocks, avenues, and the depot");
        townToMap.Enabled = cityToMap.Enabled = false;

        left.Controls.Add(Btn("A town, in three rolls", (s, e) =>
        {
            genLastTown = $"{Db.Pick("townFront")} {Db.Pick("townBack")}";
            townToMap.Enabled = true;
            Gen($"THE TOWN OF {genLastTown.ToUpper()}\n" +
                $"  What ails it:  {Db.Pick("townAils")}\n" +
                $"  What it hides: {Db.Pick("townSecret")}");
        }, 230, "Roll a town: its name, what ails it, what it hides"));
        left.Controls.Add(townToMap);
        // The city generator's four rolls answer the four questions the Keeper's Book (Ch. XIV)
        // says a city needs beyond a town's want/tell/secret: an industry quarter, a machine,
        // a wrong note, and something for a country posse to actually be hired for.
        left.Controls.Add(Btn("A city, in four rolls", (s, e) =>
        {
            genLastCity = Db.Pick("cityQuarter");
            cityToMap.Enabled = true;
            Gen($"A CITY — {genLastCity.ToUpper()}\n" +
                $"  Who really runs it: {Db.Pick("cityMachine")}\n" +
                $"  Its wrong note:     {Db.Pick("cityWrongNote")}\n" +
                $"  Work for a posse:   {Db.Pick("cityJob")}");
        }, 230, "Roll a city: its quarter, its machine, its wrong note, and work for a posse"));
        left.Controls.Add(cityToMap);
        left.Controls.Add(Btn("A face, in four rolls", (s, e) => Gen(
            $"{Db.Pick("npcGiven")} {Db.Pick("npcSurname")}\n" +
            $"  Wants: {Db.Pick("npcWant")}\n" +
            $"  Tell:  {Db.Pick("npcTell")}"), 230, "Roll a face: a name, what they want, and the tell that gives them away"));
        left.Controls.Add(Btn("Bar talk — a rumor", (s, e) => Gen("RUMOR — " + Db.Pick("rumors")), 230, "What they're saying in the saloon"));
        left.Controls.Add(Btn("The trail, by day", (s, e) => Gen("TRAIL (day) — " + Db.Pick("trailDay")), 230, "Something met on the trail between dawn and dusk"));
        left.Controls.Add(Btn("The trail, by night", (s, e) => Gen("TRAIL (night) — " + Db.Pick("trailNight")), 230, "Something met on the trail after dark"));
        left.Controls.Add(Btn("Plunder && finds", (s, e) => Gen("FIND — " + Db.Pick("plunder")), 230, "What's worth carrying off"));
        left.Controls.Add(Btn("A wrong note — an omen", (s, e) => Gen("OMEN — " + Db.Pick("omens")), 230, "A sign the country is wrong here"));

        left.Controls.Add(Heading("The Grounds — encounters by terrain"));
        // "The Hand Behind It" is the villain picker, not a terrain — in the dropdown it
        // reads like a stray creature, so it gets its own button below instead.
        const string villainTable = "The Hand Behind It";
        void RollGround(string t)
        {
            var list = Db.Terrain[t];
            var pick = list[Rules.Rng.Next(list.Count)];
            string extra = "";
            var m = System.Text.RegularExpressions.Regex.Match(pick, @"^(.*?)\s*\(");
            var c = m.Success ? Db.Find(m.Groups[1].Value.Trim()) : null;
            int lvl = (int)(encLevel?.Value ?? 2);
            // Flagging the rule was never enough on its own: it told the Keeper what NOT to run and
            // left them to invent the scene. Roll it out here — how to read the sign, what it costs,
            // and what to leave on the table — so the answer arrives with the problem.
            if (c != null && Rules.Cost(c.tier, lvl).spoor)
            {
                var sp = Rules.SpoorRow[Math.Clamp(c.tier - 1, 0, Rules.SpoorRow.Length - 1)];
                extra = $"\n  SAFE-TABLE RULE (vs party level {lvl}): two or more Tiers over the posse."
                      + "\n  It arrives as sign and spoor — the trace, not the thing."
                      + $"\n    On the ground:  {sp.what}."
                      + $"\n    Read it:        Survival DC {sp.readDc}."
                      + $"\n    Dread Check:    {(sp.dreadDc == 0 ? "none — this one is only weather and teeth" : "DC " + sp.dreadDc)}."
                      + $"\n    Then:           a {Rules.SpoorClockSegments}-segment clock. Each fresh sign fills one;"
                      + "\n                    a full clock is the night it comes in the flesh.";
            }
            Gen($"{t.ToUpper()} — {pick}{extra}");
        }
        var terr = new ComboBox { Width = 250, DropDownStyle = ComboBoxStyle.DropDownList };
        foreach (var k in Db.Terrain.Keys) if (k != villainTable) terr.Items.Add(k);
        terr.SelectedIndex = 0;
        left.Controls.Add(terr);
        left.Controls.Add(Btn("Roll on that ground", (s, e) => RollGround(terr.SelectedItem.ToString()), 230, "Roll an encounter on the chosen ground — the safe-table rule is applied for you"));
        left.Controls.Add(Btn("The Hand Behind It — a villain", (s, e) => RollGround(villainTable), 230,
            "Who's truly behind the trouble — the villain picker, its own table in the book"));

        left.Controls.Add(new Label { Height = 8, Width = 4 });
        left.Controls.Add(Btn("Copy output", (s, e) => { if (!string.IsNullOrEmpty(genOut.Text)) Clipboard.SetText(genOut.Text); }, 112, "Copy everything rolled so far to the clipboard"));
        left.Controls.Add(Btn("Clear", (s, e) =>
        {
            if (genOut.TextLength == 0) return;
            if (Confirm("Clear the generator output?")) genOut.Clear();
        }, 112, "Empty the output box and start a fresh page"));

        genOut = new RichTextBox { ReadOnly = true, Font = new Font("Consolas", 10.5f), BackColor = Color.FromArgb(252, 249, 240), BorderStyle = BorderStyle.None };
        split.Panel1.Controls.Add(left);
        split.Panel2.Controls.Add(Pad(genOut, 12));
        page.Controls.Add(split);
        Watermark(left, () => FlowBottom(left));
        return page;
    }

    void Gen(string s)
    {
        genOut.Text = s + "\n\n" + new string('—', 44) + "\n\n" + genOut.Text;
        Log(s.Split('\n')[0]);
    }

    // ============================================================ REFERENCE TAB
    // A Keeper's screen the veteran way: one topic per leaf, dense tables, and the whole
    // deck turned with ◀ ▶ or the Left/Right arrow keys. Arms, goods, signs, and skills
    // render live from the chargen data (transcribed from the Player's Book), so the
    // printed prices and dice here can never drift from the book.
    TabPage referencePage;
    RichTextBox refView;
    Label refTitle, refCount;
    int refPage;
    (string title, Action<RichTextBox> render)[] refDeck;

    /// <summary>The Keeper's screen, leaf by leaf. Named here rather than inline with the
    /// renderers so that everything which counts them reads one list — the five-minute lesson
    /// quotes the number, and prose has no way of noticing when a leaf is added. It went stale
    /// twice: the app told Keepers it held eleven leaves for two releases while the deck held
    /// thirteen.</summary>
    static readonly string[] RefLeafTitles =
    {
        "The Roll", "A Turn in the Iron Code", "Blood, Wounds & Healing", "Conditions",
        "Nerve & Dread", "The Mark & the Taint", "Signs & Grit", "Miracles of the Faithful",
        "The Long Odds", "Arms of the Frontier", "Goods & Provisions",
        "Skills, Saves & Abilities", "Running in Town",
    };

    /// <summary>How many leaves the Keeper's screen holds — derived, never typed twice.</summary>
    internal static int RefLeafCount => RefLeafTitles.Length;

    /// <summary>The deck as actually built. Zero until the Reference tab is realized (tabs are
    /// lazy); <c>--selftest</c> builds it on purpose to check the titles and the renderers agree.
    /// </summary>
    internal int RefDeckLength => refDeck?.Length ?? 0;

    static readonly Font RefMono  = new("Consolas", 9.5f);
    static readonly Font RefMonoB = new("Consolas", 9.5f, FontStyle.Bold);
    static readonly Font RefBody  = new("Segoe UI", 10f);
    static readonly Font RefItal  = new("Segoe UI", 9.7f, FontStyle.Italic);
    static readonly Font RefHead  = new("Segoe UI", 12.5f, FontStyle.Bold);

    static void RH(RichTextBox r, string s) { r.SelectionFont = RefHead; r.SelectionColor = Blood; r.AppendText(s + "\n"); }
    static void RT(RichTextBox r, string s) { r.SelectionFont = RefBody; r.SelectionColor = Ink; r.AppendText(s + "\n\n"); }
    static void RI(RichTextBox r, string s) { r.SelectionFont = RefItal; r.SelectionColor = Gold; r.AppendText(s + "\n\n"); }

    static List<string> RWrap(string s, int width)
    {
        var lines = new List<string>(); string cur = "";
        foreach (var wd in (s ?? "").Split(' '))
        {
            if (cur.Length == 0) cur = wd;
            else if (cur.Length + 1 + wd.Length <= width) cur += " " + wd;
            else { lines.Add(cur); cur = wd; }
        }
        lines.Add(cur);
        return lines;
    }

    // A monospace table with a Blood-red header band; only the LAST column wraps, with
    // continuation lines under itself, so alignment survives long rules text.
    // RichTextBox quirk: selection formatting must be re-asserted before EVERY append —
    // set once before a loop, later lines silently fall back to the control's default
    // proportional font and the columns shear.
    static void RTbl(RichTextBox r, int[] w, string[] head, IEnumerable<string[]> rows)
    {
        int last = w.Length - 1;
        string Row(IReadOnlyList<string> cells) =>
            " " + string.Join("  ", cells.Select((c, i) => (c ?? "").PadRight(w[i]))) + " ";
        void Line(string txt, Font f, Color fore, bool band)
        {
            r.SelectionStart = r.TextLength; r.SelectionLength = 0;
            r.SelectionFont = f; r.SelectionColor = fore;
            r.SelectionBackColor = band ? Blood : r.BackColor;
            r.AppendText(txt);
        }
        Line(Row(head), RefMonoB, Paper, true);
        Line("\n", RefMono, Ink, false);
        foreach (var row in rows)
        {
            var chunks = RWrap(row[last], w[last]);
            for (int li = 0; li < chunks.Count; li++)
                Line(Row(row.Select((c, i) => i == last ? chunks[li] : (li == 0 ? c : "")).ToArray()) + "\n",
                     RefMono, Ink, false);
        }
        Line("\n", RefMono, Ink, false);
    }
    static void RTbl(RichTextBox r, int[] w, string[] head, params string[][] rows)
        => RTbl(r, w, head, (IEnumerable<string[]>)rows);

    internal TabPage BuildReferenceTab()
    {
        referencePage = new TabPage("Reference") { BackColor = Paper };

        var bar = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(6, 4, 6, 4), BackColor = Color.FromArgb(243, 237, 221) };
        bar.Controls.Add(Btn("◀", (s, e) => RefShow(refPage - 1), 44, "Previous leaf (or press Left)"));
        bar.Controls.Add(Btn("▶", (s, e) => RefShow(refPage + 1), 44, "Next leaf (or press Right)"));
        refTitle = new Label { AutoSize = true, UseMnemonic = false, Font = new Font("Segoe UI", 11.5f, FontStyle.Bold), ForeColor = Blood, Padding = new Padding(10, 9, 0, 0) };
        bar.Controls.Add(refTitle);
        refCount = new Label { AutoSize = true, Font = new Font("Segoe UI", 9f, FontStyle.Italic), ForeColor = Gold, Padding = new Padding(12, 11, 0, 0) };
        bar.Controls.Add(refCount);

        refView = new RichTextBox { ReadOnly = true, BackColor = Paper, Font = RefBody, BorderStyle = BorderStyle.None };

        // Paired with RefLeafTitles, in that order. Kept as two lists so the titles can be a
        // static the prose reads without constructing a form.
        var leaves = new Action<RichTextBox>[]
        {
            RefLeafRoll, RefLeafIronCode, RefLeafWounds, RefLeafConditions,
            RefLeafNerve, RefLeafMarkTaint, RefLeafSignsGrit, RefLeafMiracles,
            RefLeafLongOdds, RefLeafArms, RefLeafGoods,
            RefLeafSkills, RefLeafCity,
        };
        if (leaves.Length != RefLeafTitles.Length)
            throw new InvalidOperationException(
                $"Reference deck: {RefLeafTitles.Length} titles against {leaves.Length} leaves — "
                + "add the title beside the renderer.");
        refDeck = RefLeafTitles.Zip(leaves, (t, r) => (t, r)).ToArray();

        referencePage.Controls.Add(Pad(refView, 14));
        referencePage.Controls.Add(bar);
        RefShow(0);
        return referencePage;
    }

    void RefShow(int i)
    {
        int n = refDeck.Length;
        refPage = ((i % n) + n) % n;                        // the deck wraps around
        refTitle.Text = refDeck[refPage].title;
        refCount.Text = $"leaf {refPage + 1} of {n}  ·  ◀ ▶ or the Left / Right keys turn the deck";
        refView.Clear();
        refDeck[refPage].render(refView);
        refView.SelectionStart = 0; refView.ScrollToCaret();
    }

    // ---- the leaves ----
    void RefLeafRoll(RichTextBox r)
    {
        RH(r, "The Four Degrees");
        RTbl(r, new[] { 17, 62 }, new[] { "Degree", "How it happens" },
            new[] { "CRITICAL SUCCESS", "Beat the DC by 10 — or a natural 20 steps the result up one degree" },
            new[] { "Success",          "Meet or beat the DC" },
            new[] { "Failure",          "Miss the DC" },
            new[] { "CRITICAL FAILURE", "Miss by 10 — or a natural 1 steps the result down one degree" });

        RH(r, "Setting a DC");
        RTbl(r, new[] { 4, 60 }, new[] { "DC", "The task" },
            new[] { "10", "Trivial" },
            new[] { "13", "Easy" },
            new[] { "15", "Average" },
            new[] { "18", "Hard" },
            new[] { "20", "Very Hard" },
            new[] { "25", "Punishing" },
            new[] { "30", "Beyond" });
        RI(r, "The Keeper calls for a roll only when failure is interesting. Everything else just happens.");
    }

    void RefLeafIronCode(RichTextBox r)
    {
        RH(r, "A Turn in the Iron Code");
        RTbl(r, new[] { 16, 66 }, new[] { "Element", "The rule" },
            new[] { "Initiative",   "A Notice check" },
            new[] { "The turn",     "Three Beats, spent as you like" },
            new[] { "A Beat",       "Strike · Stride · Aim/Brace · Interact · Reload · Take Cover" },
            new[] { "A Strike",     "d20 + attack proficiency + DEX/STR against Defense" },
            new[] { "More attacks", "Multiple Attack Penalty −5 / −10 (Agile weapons −4 / −8)" },
            new[] { "A critical hit", "Applies the weapon's Fatal die" });
    }

    void RefLeafWounds(RichTextBox r)
    {
        RH(r, "Blood, Dying & Grievous Wounds");
        RTbl(r, new[] { 16, 66 }, new[] { "State", "The rule" },
            new[] { "0 Blood",      "Dying and Bleeding; unconscious" },
            new[] { "Death",        "Comes at −CON" },
            new[] { "A terrible blow", "One hit for half maximum Blood or more, or any critical hit → Fortitude save DC 15 (higher for terrible weapons) or take a Lasting Injury" });

        RH(r, "Lasting Injuries");
        RTbl(r, new[] { 3, 60 }, new[] { "d6", "Injury" },
            new[] { "1", "Bloody Gash" },
            new[] { "2", "Cracked Ribs" },
            new[] { "3", "Maimed Hand" },
            new[] { "4", "Lamed Leg" },
            new[] { "5", "Ruined Eye or Ear" },
            new[] { "6", "Gut-Shot" });
        RT(r, "Lasting Injuries do not heal with rest alone — they take a Sawbones, time, and sometimes a graveyard.");

        RH(r, "Nonlethal");
        RT(r, "Declare before the roll that you strike nonlethally; fists and a club do so by default; most other arms " +
              "take −2 to pull the blow. A foe at 0 Blood that way is senseless, not dead.");
    }

    void RefLeafConditions(RichTextBox r)
    {
        RH(r, "Conditions  (Appendix B)");
        RTbl(r, new[] { 11, 68 }, new[] { "Condition", "Effect" },
            new[] { "Bleeding",  "Lose 1 Blood each round until stabilized" },
            new[] { "Blinded",   "−4 Defense, −4 most actions, lose DEX to Defense, half Speed" },
            new[] { "Clumsy",    "−2 on DEX-based Strikes, checks, and Defense" },
            new[] { "Drained",   "−2 on Fortitude and CON checks; lose Blood equal to your level, until recovered" },
            new[] { "Dying",     "At 0 Blood; unconscious and Bleeding toward −CON and death" },
            new[] { "Fatigued",  "−2 on checks and saves; cannot Aim or run; rest to shed it" },
            new[] { "Frightened","−1 (or worse) on everything; lessens one step each turn" },
            new[] { "Grabbed",   "Held fast; Off-Guard; −4 DEX; a check to break free" },
            new[] { "Lost",      "Mark 6; the character passes into the Keeper's hands" },
            new[] { "Marked",    "Stepped along the Mark track (see The Mark & the Taint leaf)" },
            new[] { "Off-Guard", "−2 Defense; unaware, flanked, sprawled, or caught unready" },
            new[] { "Prone",     "−4 to melee; +4 to others' ranged against you; rising costs a Beat" },
            new[] { "Sickened",  "−2 on Strikes, damage, checks, and saves; nausea" },
            new[] { "Slowed",    "Lose one Beat each turn while it lasts; may still defend" },
            new[] { "Stunned",   "Drop what you hold; lose all Beats this round; −2 Defense" });
        RI(r, "Tag any of these onto a combatant from the Tracker's ＋ Condition ▾ menu.");
    }

    // Keeper's Book Ch. XIV in one leaf: what actually changes when the game moves off the
    // range and into Dodge, Kansas City, or Butte. Nothing here is a new rule — it is the
    // existing rules, plus the handful of rulings a city keeps asking for.
    void RefLeafCity(RichTextBox r)
    {
        RH(r, "The City  (Keeper's Book, Ch. XIV)");
        RT(r, "A crowd is better cover than a wilderness. In a town of two hundred a thing that takes one soul a week " +
              "is noticed by Tuesday; in Kansas City it feeds forever, because a missing stranger is a filing. Run the " +
              "same rules — the city changes what they cost, not what they are.");

        RH(r, "The Six Changes");
        RTbl(r, new[] { 22, 44 }, new[] { "At the table", "What it costs" },
            new[] { "The deadline",        "Guns checked north of the tracks by ordinance — the party is disarmed lawfully, by their own choice" },
            new[] { "Firing a shot",       "An arrest, a coroner's inquest, two newspapers, a bail bond. Charge for it; never forbid it" },
            new[] { "Witnesses & the press","Nothing done in public stays private — and a thing can be put IN the paper too" },
            new[] { "Help exists",         "Police, hospital, coroner — and a man raving about the dead is committed, not ignored" },
            new[] { "Paper is the tracking","Newspaper morgue, city directory, recorder, inquest book, hospital register, a bought telegraph clerk" },
            new[] { "Dread moves indoors", "The killing floor at three, the tenement stair, the ore drift, the fog. DCs unchanged; there is nowhere to ride to" });

        RH(r, "The Cult, Chartered");
        RT(r, "In the country a cult is a barn and eleven people. In a city it incorporates — a benevolent association " +
              "with a president, a treasurer, minute-books, a lawyer, and the coroner on its roll. It need not silence a " +
              "witness; it can outspend one, sue one, or have one committed. Its one weakness is publicity, so the last " +
              "scene of a city campaign is usually an exposure rather than a gunfight.");
        RI(r, "Give the party one honest official, well down the ladder, with no power and a family.");

        RH(r, "Keeping the Tone");
        RT(r, "Keep the party's country competence valuable — they read sign, sit a horse, and stay calm with a gun, and " +
              "the city has almost nobody who can do all three. Keep the money problems mundane. And ride out to a ranch, " +
              "a mine, or a rail camp every third night, so the city is a place they come back to rather than a box.");
    }

    void RefLeafNerve(RichTextBox r)
    {
        RH(r, "Nerve & Dread");
        RT(r, "Nerve = RES score + level. A Dread Check is a Will save against the horror's Dread DC. On a failure, " +
              "Nerve is lost by the horror's Tier; a critical failure doubles it. At 0 Nerve a soul Breaks.");
        RTbl(r, new[] { 6, 40 }, new[] { "Tier", "Nerve lost on a failure" },
            new[] { "I",    "1" },
            new[] { "II",   "1d4" },
            new[] { "III",  "1d6" },
            new[] { "IV–V", "1d10" });
        RI(r, "Familiarity is the death of dread — the same sight costs nothing the second time.");

        RH(r, "Recovering Nerve");
        RTbl(r, new[] { 44, 30 }, new[] { "The remedy", "It restores" },
            new[] { "Confession, spoken plainly to a listener",  "1d6" },
            new[] { "A full night unmolested in genuine safety", "1d6" },
            new[] { "A week of true peace",                      "All of it" },
            new[] { "A sermon, a Sawbones' reason, a grim joke, or a point of Grit", "A measure of steadiness" },
            new[] { "Whiskey — steadies the hand now",           "1d4, but courts a vice and its Fortitude saves" });
    }

    void RefLeafMarkTaint(RichTextBox r)
    {
        RH(r, "The Mark  (six steps)");
        RT(r, "The Mark moves only when a soul CHOOSES the dark — a bargain, a rite, a heeding. Never for a bad roll, " +
              "never for merely being wounded. At the sixth step, the country keeps what it was promised.");

        RH(r, "The Taint of the Land  (four steps)");
        RT(r, "For every three days on cursed ground: a Fortitude save (the body first), then Will once it reaches " +
              "the mind. Wards ease it; sanctification or leaving sheds it.");
        RTbl(r, new[] { 16, 30 }, new[] { "The ground", "Save DC" },
            new[] { "Uneasy ground",  "13" },
            new[] { "Wronged ground", "16" },
            new[] { "The old places", "20" });
    }

    void RefLeafSignsGrit(RichTextBox r)
    {
        RH(r, "Signs & the Sign DC");
        RT(r, "Where a Sign forces a save, the DC is the worker's Sign DC = 10 + half their level + RES modifier. " +
              "A soul without the Signs feature working folk-rites has a Sign DC of only 10 + RES modifier — no level added.");
        RT(r, "Rank opens at 1st, 3rd, 5th, 7th and 9th level. A Sign above your Rank does nothing at all — "
             + "the words are there, the meaning is not. Nerve is the standing coin; two Blood buys one Nerve where "
             + "a Sign offers the trade; Rank 5 costs Mark, and Mark never comes back.");
        if (CharGen.D?.signs?.Count > 0)
            foreach (var (key, title) in new[] { ("common", "The Common Signs — any worker"),
                                                 ("bargain", "The Bargain — Hexer, Dark Cultist, False Prophet"),
                                                 ("craft",   "The Craft — the Witch alone") })
            {
                RH(r, title);
                RTbl(r, new[] { 6, 19, 22, 46 }, new[] { "Rank", "Sign", "Cost", "The working" },
                    CharGen.D.signs.Where(sg => sg.list == key).OrderBy(sg => sg.rank).ThenBy(sg => sg.name)
                        .Select(sg => new[] { sg.rank.ToString(), sg.name, sg.cost ?? "—", sg.desc ?? "" }));
            }

        RH(r, "Grit");
        RT(r, "Three per soul, refreshed each session. Spend one AFTER seeing the result:");
        RTbl(r, new[] { 60 }, new[] { "Spend one Grit to…" },
            new[] { "Add 1d6 to a roll just made" },
            new[] { "Re-roll a failed check" },
            new[] { "Refuse to fall at 0 Blood for one more round" },
            new[] { "Shrug a fright until the end of your next turn" },
            new[] { "Soften a critical failure to an ordinary failure" });
        RI(r, "The Keeper may award a point mid-session for a deed of true courage.");
    }

    void RefLeafMiracles(RichTextBox r)
    {
        RH(r, "Miracles & the Miracle DC");
        RT(r, "The faith-side counterpart to the Signs, worked by the five Callings of Faith (Ch. VI). "
             + "Where a Miracle forces a save, the DC is 10 + half your level + your faith ability's modifier "
             + "(the Padre's and Preacher's PRE, the Shaman's and Medicine Man's RES, the Witch Hunter's WIT).");
        RT(r, "Same Rank spine as the Signs — Rank opens at 1st, 3rd, 5th, 7th and 9th level, and nothing above "
             + "your Rank will work. Miracles are paid from your Calling's pool (Grace, Conviction, Breath, Vital "
             + "Breath, or the Witch Hunter's Zeal), not in Nerve or Blood. Faith does not bite back; the cost is "
             + "the pool, and the risk is a prayer unanswered.");
        if (CharGen.D?.miracles?.Count > 0)
            foreach (var (key, title) in new[] {
                    ("blessing",     "The Common Blessings — any Calling of Faith"),
                    ("liturgy",      "The Liturgy — the Padre"),
                    ("revival",      "The Revival — the Preacher"),
                    ("spirits",      "The Spirits — the Shaman"),
                    ("mending",      "The Mending — the Medicine Man"),
                    ("consecration", "The Consecrations — the Witch Hunter") })
            {
                RH(r, title);
                RTbl(r, new[] { 6, 21, 20, 46 }, new[] { "Rank", "Miracle", "Cost", "The working" },
                    CharGen.D.miracles.Where(m => m.list == key).OrderBy(m => m.rank).ThenBy(m => m.name)
                        .Select(m => new[] { m.rank.ToString(), m.name, m.cost ?? "—", m.desc ?? "" }));
            }
        RI(r, "\"Faith\" in a Miracle's cost means points from your Calling's pool, whatever your Calling names it.");
    }

    void RefLeafLongOdds(RichTextBox r)
    {
        RH(r, "Threat by Tier");
        RT(r, "A creature is a fair, hard fight for a party of twice its Tier in levels.");
        RTbl(r, new[] { 5, 7, 6, 5, 12, 6, 8 },
            new[] { "Tier", "Defense", "Attack", "Blood", "Saves hi/lo", "Damage", "Dread DC" },
            Enumerable.Range(0, 5).Select(i =>
            {
                var t = Rules.TierRow[i];
                return new[] { Rules.Roman(i + 1), t.def.ToString(), "+" + t.atk, t.blood.ToString(),
                               $"+{t.hi} / +{t.lo}", t.dmg, t.dread };
            }));

        RH(r, "The Encounter Budget");
        RTbl(r, new[] { 34, 6 }, new[] { "The fight", "Cost" },
            new[] { "The budget, per player character", "4" },
            new[] { "An even-Tier foe",                 "4" },
            new[] { "A mook (a Tier or two down)",      "1" },
            new[] { "A standout (a Tier up)",           "8" });
        RT(r, "Spend the budget and the fight is fair; overspend and you had better mean it.");

        RH(r, "The Safe-Table Rule — Sign & Spoor");
        RT(r, "A horror two or more Tiers over the posse does not arrive in the flesh. It arrives as "
             + "sign and spoor, and the scene is a reading rather than a fight.");
        RI(r, "Spoor is the physical trace — track, scat, hair, blood, a scrape on a tree at a height "
             + "that ends the conversation. Sign is everything wider: a kill, a silence, stock that "
             + "will not go back in the barn.");
        RTbl(r, new[] { 6, 9, 9, 46 },
            new[] { "Tier", "Read it", "Dread", "What is left of it" },
            Enumerable.Range(0, Rules.SpoorRow.Length).Select(i =>
            {
                var s = Rules.SpoorRow[i];
                return new[] { Rules.Roman(i + 1), "Survival " + s.readDc,
                               s.dreadDc == 0 ? "—" : "DC " + s.dreadDc, s.what };
            }));
        RT(r, "The Dread DC is one rung below meeting the thing itself: reading an aftermath is not "
             + "standing in front of the animal. Nerve is lost off the usual ladder.");
        RH(r, "Reading it — the four degrees");
        RTbl(r, new[] { 18, 52 }, new[] { "Degree", "What the tracker gets" },
            new[] { "CRITICAL SUCCESS", Rules.SpoorRead(3) },
            new[] { "Success",          Rules.SpoorRead(2) },
            new[] { "Failure",          Rules.SpoorRead(1) },
            new[] { "CRITICAL FAILURE", Rules.SpoorRead(0) });
        RI(r, $"Then it is a thread, not a funeral: a {Rules.SpoorClockSegments}-segment clock, and every "
             + "fresh sign of the same thing fills one. A full clock is the night it comes in the flesh — "
             + "and by then the posse should be a Tier higher, or have a plan.");
        RT(r, "The app runs this for you. Send a creature the rule bars to the Tracker and it offers to put "
             + "the trace on the field instead: a row with no Blood, its clock in place of a Blood bar, and "
             + "Read sign ▸ to resolve the Survival check, the Dread it costs the reader, and one more "
             + "segment. When the clock fills, the Tracker offers to swap the trace for the creature.");
    }

    void RefLeafArms(RichTextBox r)
    {
        var guns  = CharGen.D?.weapons?.Where(w => w.kind == "gun").ToList();
        var steel = CharGen.D?.weapons?.Where(w => w.kind != "gun").ToList();
        string Cost(double c) => c > 0 ? "$" + c.ToString("0") : "—";
        RH(r, "Guns");
        if (guns?.Count > 0)
            RTbl(r, new[] { 23, 7, 5, 42 }, new[] { "Arm", "Damage", "Cost", "Traits" },
                guns.Select(w => new[] { w.name, w.dmg, Cost(w.cost), w.traits ?? "" }));
        RH(r, "Steel & Wood");
        if (steel?.Count > 0)
            RTbl(r, new[] { 23, 7, 5, 42 }, new[] { "Arm", "Damage", "Cost", "Traits" },
                steel.Select(w => new[] { w.name, w.dmg, Cost(w.cost), w.traits ?? "" }));
        RI(r, "Prices as printed in Goods & Provisions (Ch. X). A critical hit applies the Fatal die.");
    }

    void RefLeafGoods(RichTextBox r)
    {
        RH(r, "Goods & Provisions  (Ch. X printed prices)");
        var gear = CharGen.D?.gearPrices;
        if (gear?.Count > 0)
        {
            string Price(double v) => v < 1 ? $"{v * 100:0}¢" : "$" + v.ToString("0.##");
            RTbl(r, new[] { 34, 8 }, new[] { "The goods", "Price" },
                gear.Select(kv => new[]
                {
                    System.Text.RegularExpressions.Regex.Replace(kv.Key, @"\s*\([^()]*\)$", ""),
                    Price(kv.Value)
                }));
        }
        RI(r, "The general store carries what the country allows. The rest is barter, luck, and the road.");
    }

    void RefLeafSkills(RichTextBox r)
    {
        RH(r, "Abilities");
        RT(r, "STR · DEX · CON · WIT (Wits) · RES (Resolve) · PRE (Presence).  Modifier = (score − 10) / 2.");
        RH(r, "Saves");
        RTbl(r, new[] { 10, 30 }, new[] { "Save", "Ability" },
            new[] { "Fortitude", "CON" },
            new[] { "Reflex",    "DEX" },
            new[] { "Will",      "RES" });
        RT(r, "Strong save = 2 + half your level.  Weak save = a third of your level.  Both round down.");

        RH(r, "Attack Rank");
        if (CharGen.D?.callings?.Count > 0)
            RTbl(r, new[] { 11, 26, 34 }, new[] { "Rank", "Your attack", "Callings" },
                new[] { ("Practiced", "your level"),
                        ("Steady",    "your level, less 1"),
                        ("Slight",    "your level, less 2 (min +0)") }
                    .Select(x => new[] { x.Item1, x.Item2,
                        string.Join(", ", CharGen.D.callings
                            .Where(c => c.attackRank == x.Item1).Select(c => c.name)) }));
        RI(r, "Every rank climbs by one each level, so the distance between a Gunhand and a Hexer never widens.");

        RH(r, "Armor");
        if (CharGen.D?.armor?.Count > 0)
            RTbl(r, new[] { 22, 9, 12, 8 }, new[] { "Protection", "Blades", "Small shot", "Price" },
                CharGen.D.armor.Select(a => new[] {
                    a.name, "DR " + a.drBlades, "DR " + a.drShot, "$" + a.cost.ToString("0.##") }));
        RI(r, "Most firearms ignore most armor. DR applies to blades and small shot only — birdshot, "
             + "buckshot, a ricochet, a pocket pistol across a room. Armor does not stack: count the better of two.");
        RH(r, "Skills");
        if (CharGen.D?.skills?.Count > 0)
            RTbl(r, new[] { 17, 10 }, new[] { "Skill", "Ability" },
                CharGen.D.skills.Select(sk => new[] { sk.name, sk.ability }));
    }

    // ============================================================ SESSION TAB
    FlowLayoutPanel clockPanel;

    TabPage BuildSessionTab()
    {
        var page = new TabPage("Session") { BackColor = Paper };
        var split = Split(Orientation.Horizontal, 160, 160, 0.45);

        var notesGroup = new GroupBox { Text = "The Keeper's ledger  (auto-saves on exit && every five minutes)", Dock = DockStyle.Fill, Padding = new Padding(8), ForeColor = Blood, Font = new Font("Segoe UI", 9.5f, FontStyle.Bold) };
        notesBox = new TextBox { Multiline = true, Dock = DockStyle.Fill, ScrollBars = ScrollBars.Vertical, Font = new Font("Segoe UI", 10f), BorderStyle = BorderStyle.None, BackColor = Color.FromArgb(252, 249, 240) };
        // This tab is built on first visit, so the box takes over from the field that has
        // been holding the ledger since load, and keeps it fed from here on.
        notesBox.Text = notesText;
        notesBox.TextChanged += (s, e) => notesText = notesBox.Text;
        var nbar = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 40 };
        nbar.Controls.Add(Btn("Stamp the date", (s, e) =>
        {
            notesBox.AppendText((notesBox.TextLength > 0 ? Environment.NewLine : "") +
                $"—  {DateTime.Now:MMMM d, yyyy}  —" + Environment.NewLine);
            notesBox.Focus();
        }, 115, "Drop a dated session header into the ledger"));
        nbar.Controls.Add(Btn("Clear ledger", (s, e) =>
        {
            if (notesBox.TextLength == 0) { Log("The ledger is already blank."); return; }
            if (Confirm("Clear the whole ledger? The written record is wiped for a fresh start."))
            { notesBox.Clear(); Log("The ledger is wiped clean."); }
        }, 100, "Wipe the written record and start fresh"));
        notesGroup.Controls.Add(notesBox);
        notesGroup.Controls.Add(nbar);

        var clocksGroup = new GroupBox { Text = "Threads && clocks", Dock = DockStyle.Fill, Padding = new Padding(8), ForeColor = Blood, Font = new Font("Segoe UI", 9.5f, FontStyle.Bold) };
        var cbar = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 40 };
        cbar.Controls.Add(Btn("＋ New thread", (s, e) => NewThread(), 110, "Start a new thread of trouble, with a clock to run it down"));
        cbar.Controls.Add(Btn("Save now", (s, e) => { AutoSave(); Log("Session saved."); }, 90, "Write the session to disk now — it also saves itself every 5 minutes and on exit"));
        cbar.Controls.Add(Btn("Clear threads", (s, e) =>
        {
            if (clocks.Count == 0) { Nope("No threads to clear."); return; }
            if (Confirm($"Clear all {clocks.Count} thread(s) and their clocks for a fresh start?"))
            { clocks.Clear(); RefreshClocks(); Log("All threads cleared — the board is clean."); }
        }, 105, "Delete every thread and clock at once"));
        var clockHint = new Label
        {
            Dock = DockStyle.Top, Height = 36, ForeColor = Gold,
            Font = new Font("Segoe UI", 9f, FontStyle.Italic),
            Text = "A thread is trouble on its way — name it and give it a clock. Tick ＋ when the world\nmoves toward it (a lead ignored, a night wasted). When the last segment fills, it comes due."
        };
        clockPanel = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoScroll = true };
        clocksGroup.Controls.Add(clockPanel);
        clocksGroup.Controls.Add(clockHint);
        clocksGroup.Controls.Add(cbar);

        split.Panel1.Controls.Add(notesGroup);
        split.Panel2.Controls.Add(clocksGroup);
        page.Controls.Add(split);
        Watermark(clockPanel, () => FlowBottom(clockPanel));
        return page;
    }

    void NewThread()
    {
        using var f = new Form { Width = 360, Height = 200, Text = "New thread", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper };
        var l1 = new Label { Left = 14, Top = 14, Width = 320, Text = "Name the trouble (type your own, or pick a pattern):" };
        var name = new ComboBox { Left = 14, Top = 38, Width = 320, DropDownStyle = ComboBoxStyle.DropDown };
        name.Items.AddRange(new object[]
        {
            "The Sorrel Gang finds the posse",
            "The next well fails",
            "The law closes in",
            "The debt comes due",
            "Winter closes the passes",
            "The congregation turns",
            "Word of what they did gets ahead of them",
            "The thing they wounded heals"
        });
        name.Text = "The Sorrel Gang finds the posse";
        var l2 = new Label { Left = 14, Top = 76, Width = 100, Text = "Segments:" };
        var seg = new ComboBox { Left = 120, Top = 72, Width = 90, DropDownStyle = ComboBoxStyle.DropDownList };
        seg.Items.AddRange(new object[] { "4", "6", "8" }); seg.SelectedIndex = 1;
        Tip.SetToolTip(seg, "4 = a short fuse · 6 = most troubles · 8 = a slow doom");
        // affirmative left of Cancel, per Windows convention
        var ok = new Button { Text = "Create", Left = 148, Top = 118, Width = 90, DialogResult = DialogResult.OK };
        var cancel = new Button { Text = "Cancel", Left = 244, Top = 118, Width = 90, DialogResult = DialogResult.Cancel };
        f.Controls.AddRange(new Control[] { l1, name, l2, seg, ok, cancel });
        f.AcceptButton = ok; f.CancelButton = cancel;
        if (f.ShowDialog() == DialogResult.OK && !string.IsNullOrWhiteSpace(name.Text))
        {
            clocks.Add(new CampaignClock { Name = name.Text.Trim(), Segments = int.Parse((string)seg.SelectedItem) });
            RefreshClocks();
        }
    }

    void RenameThread(CampaignClock c)
    {
        using var f = new Form { Width = 360, Height = 160, Text = "Rename thread", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper };
        var l1 = new Label { Left = 14, Top = 14, Width = 320, Text = "Thread name:" };
        var name = new TextBox { Left = 14, Top = 38, Width = 320, Text = c.Name };
        var ok = new Button { Text = "Rename", Left = 148, Top = 78, Width = 90, DialogResult = DialogResult.OK };
        var cancel = new Button { Text = "Cancel", Left = 244, Top = 78, Width = 90, DialogResult = DialogResult.Cancel };
        f.Controls.AddRange(new Control[] { l1, name, ok, cancel });
        f.AcceptButton = ok; f.CancelButton = cancel;
        if (f.ShowDialog() == DialogResult.OK && !string.IsNullOrWhiteSpace(name.Text))
        { c.Name = name.Text.Trim(); RefreshClocks(); }
    }

    void RefreshClocks()
    {
        if (clockPanel == null) return;
        clockPanel.Controls.Clear();
        foreach (var c in clocks.ToList())
        {
            var row = new FlowLayoutPanel { AutoSize = true, Margin = new Padding(0, 2, 0, 2) };
            var pips = new Label
            {
                AutoSize = true, Font = new Font("Segoe UI", 12f), ForeColor = c.Filled >= c.Segments ? Blood : Gold,
                Text = new string('●', c.Filled) + new string('○', Math.Max(0, c.Segments - c.Filled)), Padding = new Padding(0, 4, 6, 0)
            };
            row.Controls.Add(pips);
            row.Controls.Add(new Label { Text = $"{c.Name}  ({c.Filled}/{c.Segments})", AutoSize = true, Padding = new Padding(0, 7, 6, 0), ForeColor = Ink });
            row.Controls.Add(Btn("＋", (s, e) => { c.Filled = Math.Min(c.Segments, c.Filled + 1); if (c.Filled == c.Segments) Log($"THREAD COMPLETE — {c.Name}. It comes due."); RefreshClocks(); }, 34, "Tick the clock forward"));
            row.Controls.Add(Btn("−", (s, e) => { c.Filled = Math.Max(0, c.Filled - 1); RefreshClocks(); }, 34, "Untick a segment"));
            row.Controls.Add(Btn("✎", (s, e) => RenameThread(c), 34, "Rename this thread"));
            row.Controls.Add(Btn("✕", (s, e) => { if (Confirm($"Delete the thread \"{c.Name}\"?")) { clocks.Remove(c); RefreshClocks(); } }, 34, "Delete this thread"));
            clockPanel.Controls.Add(row);
        }
    }
}
