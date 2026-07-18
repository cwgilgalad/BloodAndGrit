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
        Tip.SetToolTip(beastSearch, "Filter by name or where it's found");
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
        beastCount = Lbl("");
        filters.Controls.Add(beastCount);

        beastList = new ListBox { Dock = DockStyle.Fill, Font = new Font("Segoe UI", 9.5f), BorderStyle = BorderStyle.None, BackColor = Color.FromArgb(252, 249, 240) };
        beastList.SelectedIndexChanged += (s, e) => ShowBeast(beastList.SelectedItem as Creature);
        // double-click pops the creature out into its own window — maximize it, grow the
        // text, keep several open side by side
        beastList.DoubleClick += (s, e) => { if (beastList.SelectedItem is Creature c) ShowCreatureCard(c); };
        Tip.SetToolTip(beastList, "Double-click a creature to open it in its own window");
        leftPanel.Controls.Add(beastList); leftPanel.Controls.Add(filters);

        beastView = new RichTextBox { Dock = DockStyle.Fill, ReadOnly = true, BorderStyle = BorderStyle.None, BackColor = Paper, Font = new Font("Segoe UI", 10f) };

        split.Panel1.Controls.Add(leftPanel);
        split.Panel2.Controls.Add(beastView);
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

    // ============================================================ ENCOUNTER TAB
    DataGridView encGrid;
    NumericUpDown encLevel, encQty;
    ComboBox encPick;
    Label encVerdict;
    ProgressBar encBar;

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
        encLevel = new NumericUpDown { Minimum = 1, Maximum = 10, Value = 2, Width = 55, Margin = new Padding(3, 6, 3, 3) };
        encLevel.ValueChanged += (s, e) => RefreshEncounter();
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
        top.Controls.Add(Btn("✕ Remove", (s, e) => { if (encGrid.CurrentRow?.DataBoundItem is EncounterPick p) { encounter.Remove(p); RefreshEncounter(); } }, 85));
        top.Controls.Add(Btn("Clear", (s, e) => { if (encounter.Count > 0 && Confirm("Clear the encounter?")) { encounter.Clear(); RefreshEncounter(); } }, 65));
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
            if (name == "role") { e.Value = role; if (spoor) { e.CellStyle.ForeColor = Blood; e.CellStyle.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold); } }
            if (name == "cost") e.Value = cost;
        };
        encGrid.CellDoubleClick += (s, e) => { if (e.RowIndex >= 0) ShowCreatureCard(encounter[e.RowIndex].Creature); };

        var bottom = new Panel { Dock = DockStyle.Bottom, Height = 64, BackColor = Color.FromArgb(243, 237, 221), Padding = new Padding(8, 6, 8, 6) };
        encVerdict = new Label { Dock = DockStyle.Top, Height = 26, TextAlign = ContentAlignment.MiddleLeft, Font = new Font("Segoe UI", 10.5f, FontStyle.Bold), ForeColor = Ink };
        encBar = new ProgressBar { Dock = DockStyle.Bottom, Height = 22, Maximum = 100 };
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

        RefreshEncounter();
        return page;
    }

    void AddPickToEncounter()
    {
        var c = Db.Find((encPick.Text ?? "").Trim());
        if (c == null) { Log("No creature by that name — pick one from the list."); return; }
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
        string verdict = spend == 0 ? "Empty — add creatures above, or send them over from the Bestiary tab." :
            spend < budget ? "Under budget — a fight they should win." :
            spend == budget ? "On budget — a fair, hard fight." :
            spend <= budget + 4 ? "Over budget — mean. Somebody bleeds." :
            "WELL over budget — you had better mean it.";
        encVerdict.Text = $"Spend {spend}  /  budget {budget}   ({party.Count} souls × 4)     {verdict}";
        encVerdict.ForeColor = spend > budget + 4 ? Blood : (spend > budget ? Color.FromArgb(150, 80, 20) : Ink);
        if (encBar != null)
        {
            encBar.Maximum = Math.Max(budget * 2, Math.Max(spend, 1));
            encBar.Value = Math.Min(spend, encBar.Maximum);
        }
    }

    // ============================================================ TRACKER TAB
    DataGridView trkGrid;
    Label roundLbl;
    NumericUpDown trkAmount, trkQty;
    ComboBox trkPick;

    void AddPickToTracker()
    {
        var c = Db.Find((trkPick.Text ?? "").Trim());
        if (c == null) { Log("No creature by that name — pick one from the list."); return; }
        AddCreatureToTracker(c, (int)trkQty.Value);
    }

    TabPage BuildTrackerTab()
    {
        var page = new TabPage("Tracker") { BackColor = Paper };
        var bar = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(6, 4, 6, 4), BackColor = Color.FromArgb(243, 237, 221) };
        roundLbl = new Label { Text = "Round 1", Font = new Font("Segoe UI", 12f, FontStyle.Bold), ForeColor = Blood, Padding = new Padding(0, 6, 12, 0), AutoSize = true };
        bar.Controls.Add(roundLbl);
        bar.Controls.Add(Btn("Roll initiative", (s, e) => { foreach (var c in tracker) c.Init = Rules.Rng.Next(1, 21); SortTracker(TrkSort.InitDesc); Log("Initiative rolled for the field."); }, 110, "Roll a d20 for every combatant and sort by it"));
        bar.Controls.Add(MenuBtn("Sort ▾", 70, "Order the field",
            ("Initiative — high to low", (s, e) => SortTracker(TrkSort.InitDesc)),
            ("Initiative — low to high", (s, e) => SortTracker(TrkSort.InitAsc)),
            ("-", null),
            ("Name — A to Z", (s, e) => SortTracker(TrkSort.NameAsc)),
            ("Name — Z to A", (s, e) => SortTracker(TrkSort.NameDesc)),
            ("-", null),
            ("Blood — most to least", (s, e) => SortTracker(TrkSort.BloodDesc)),
            ("Blood — least to most", (s, e) => SortTracker(TrkSort.BloodAsc))));
        bar.Controls.Add(Btn("Next round ▸", (s, e) => { round++; roundLbl.Text = $"Round {round}"; Log($"— Round {round} —"); }, 100));
        bar.Controls.Add(Lbl("  Amt:"));
        trkAmount = new NumericUpDown { Minimum = 1, Maximum = 999, Value = 5, Width = 58, Margin = new Padding(3, 6, 3, 3) };
        bar.Controls.Add(trkAmount);
        bar.Controls.Add(Btn("Damage", (s, e) => AdjustCombatant(-1), 80));
        bar.Controls.Add(Btn("Heal", (s, e) => AdjustCombatant(+1), 65));
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
        bar.Controls.Add(Btn("Clear field", (s, e) => { if (tracker.Count > 0 && Confirm("Clear the whole battlefield?")) { tracker.Clear(); round = 1; roundLbl.Text = "Round 1"; Log("The field is cleared."); } }, 95, "Wipe everyone — posse and foes — and reset to Round 1"));

        trkGrid = new DataGridView
        {
            Dock = DockStyle.Fill, AutoGenerateColumns = false, DataSource = tracker,
            AllowUserToAddRows = false, RowHeadersVisible = false,
            AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
            SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = false
        };
        StyleGrid(trkGrid);
        void C(string prop, string head, int w, bool ro = false)
            => trkGrid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = prop, HeaderText = head, FillWeight = w, ReadOnly = ro });
        C("Init", "Init", 50); C("Name", "Name", 210, true); C("BloodCur", "Blood", 60);
        C("BloodMax", "/Max", 55, true); C("Defense", "Def", 50, true); C("Conditions", "Conditions", 240);
        WireNumericValidation(trkGrid, new() { "Init", "BloodCur" });
        trkGrid.CellFormatting += (s, e) =>
        {
            if (e.RowIndex < 0 || e.RowIndex >= tracker.Count) return;
            var c = tracker[e.RowIndex];
            e.CellStyle.BackColor = c.Down ? DownRow : (c.IsPC ? PcRow : FoeRow);
            if (c.Down) e.CellStyle.ForeColor = Blood;
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
        trkGrid.CellDoubleClick += (s, e) =>
        {
            if (e.RowIndex >= 0 && !string.IsNullOrEmpty(tracker[e.RowIndex].Ref))
            { var c = Db.Find(tracker[e.RowIndex].Ref); if (c != null) ShowCreatureCard(c); }
        };

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
        tracker.ListChanged += (s, e) => hint.Visible = tracker.Count == 0;
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
        var rtf = new RichTextBox { Dock = DockStyle.Fill, ReadOnly = true, BorderStyle = BorderStyle.None, BackColor = Paper, Font = new Font("Segoe UI", 10f) };
        var bar = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 42, Padding = new Padding(4, 2, 4, 2), BackColor = Color.FromArgb(243, 237, 221) };
        bar.Controls.Add(Btn("A−", (s, e) => rtf.ZoomFactor = Math.Max(0.7f, rtf.ZoomFactor - 0.15f), 46, "Smaller text"));
        bar.Controls.Add(Btn("A＋", (s, e) => rtf.ZoomFactor = Math.Min(3f, rtf.ZoomFactor + 0.15f), 46, "Larger text"));
        bar.Controls.Add(Btn("→ Tracker", (s, e) => AddCreatureToTracker(c), 95, "Drop one onto the battlefield"));
        win.Controls.Add(rtf);
        win.Controls.Add(bar);
        RenderCreature(rtf, c);
        beastWindows[c.name] = win;
        win.FormClosed += (s, e) => beastWindows.Remove(c.name);
        win.Show(this);
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
        trkGrid?.Refresh();
    }

    // Ad-hoc combatant: a named NPC, a hireling, an improvised foe — anything not in the
    // Bestiary. Blood/Defense by hand; the PC flag just tints the row green like the posse.
    void AddCustomCombatant()
    {
        using var f = new Form { Width = 350, Height = 258, Text = "Add combatant", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, BackColor = Paper };
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
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Log("Select a combatant first."); return; }
        var set = c.Conditions.Split(',', StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries).ToList();
        // a valued condition supersedes its other steps (one Frightened, not three)
        string family = cond.Split(' ')[0];
        if (cond != family) set.RemoveAll(x => x.StartsWith(family + " ") || x == family);
        if (!set.Contains(cond)) set.Add(cond);
        c.Conditions = string.Join(", ", set);
        trkGrid.Refresh();
        Log($"{c.Name}: {cond}.");
    }

    void ClearConditions()
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Log("Select a combatant first."); return; }
        c.Conditions = ""; trkGrid.Refresh();
        Log($"{c.Name}: conditions cleared.");
    }

    // Set up the next encounter without losing the party: clear the foes, wipe the
    // per-fight conditions off the survivors, and drop back to Round 1. Blood carries over
    // (use the Posse tab's Rest to heal up between fights).
    void NewFight()
    {
        var foes = tracker.Where(c => !c.IsPC).ToList();
        if (foes.Count == 0) { Log("No foes on the field to clear."); round = 1; roundLbl.Text = "Round 1"; return; }
        if (!Confirm($"New fight? Clears {foes.Count} foe(s), keeps the posse, resets to Round 1.")) return;
        foreach (var f in foes) tracker.Remove(f);
        foreach (var c in tracker) c.Conditions = "";
        round = 1; roundLbl.Text = "Round 1"; trkGrid?.Refresh();
        Log("New fight — foes cleared, the posse holds the field, Round 1.");
    }

    void AddCreatureToTracker(Creature c, int count = 1)
    {
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
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Log("Select a combatant first."); return; }
        int v = (int)trkAmount.Value;
        int hi = c.BloodMax > 0 ? c.BloodMax : int.MaxValue;   // healing can't outrun the maximum
        c.BloodCur = Math.Clamp(c.BloodCur + sign * v, 0, hi);
        Log($"{c.Name} {(sign < 0 ? "takes" : "recovers")} {v} → {c.BloodCur}/{c.BloodMax}" + (c.BloodCur == 0 ? "  — PUT DOWN." : ""));
        trkGrid.Refresh();
        if (c.IsPC) { var p = party.FirstOrDefault(x => x.Name == c.Name); if (p != null) { p.BloodCur = c.BloodCur; posseGrid?.Refresh(); } }
    }

    // ============================================================ GENERATORS TAB
    RichTextBox genOut;

    TabPage BuildGeneratorsTab()
    {
        var page = new TabPage("Generators") { BackColor = Paper };
        var split = Split(Orientation.Vertical, 300, 300, 0.27);

        var left = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.TopDown, WrapContents = false, Padding = new Padding(12), AutoScroll = true, BackColor = Paper };
        left.Controls.Add(Heading("The Country in Your Pocket"));
        left.Controls.Add(Btn("A town, in three rolls", (s, e) => Gen(
            $"THE TOWN OF {Db.Pick("townFront").ToUpper()} {Db.Pick("townBack").ToUpper()}\n" +
            $"  What ails it:  {Db.Pick("townAils")}\n" +
            $"  What it hides: {Db.Pick("townSecret")}"), 230));
        left.Controls.Add(Btn("A face, in four rolls", (s, e) => Gen(
            $"{Db.Pick("npcGiven")} {Db.Pick("npcSurname")}\n" +
            $"  Wants: {Db.Pick("npcWant")}\n" +
            $"  Tell:  {Db.Pick("npcTell")}"), 230));
        left.Controls.Add(Btn("Bar talk — a rumor", (s, e) => Gen("RUMOR — " + Db.Pick("rumors")), 230));
        left.Controls.Add(Btn("The trail, by day", (s, e) => Gen("TRAIL (day) — " + Db.Pick("trailDay")), 230));
        left.Controls.Add(Btn("The trail, by night", (s, e) => Gen("TRAIL (night) — " + Db.Pick("trailNight")), 230));
        left.Controls.Add(Btn("Plunder && finds", (s, e) => Gen("FIND — " + Db.Pick("plunder")), 230));
        left.Controls.Add(Btn("A wrong note — an omen", (s, e) => Gen("OMEN — " + Db.Pick("omens")), 230));

        left.Controls.Add(Heading("The Grounds — encounters by terrain"));
        var terr = new ComboBox { Width = 250, DropDownStyle = ComboBoxStyle.DropDownList };
        foreach (var k in Db.Terrain.Keys) terr.Items.Add(k);
        terr.SelectedIndex = 0;
        left.Controls.Add(terr);
        left.Controls.Add(Btn("Roll on that ground", (s, e) =>
        {
            var t = terr.SelectedItem.ToString();
            var list = Db.Terrain[t];
            var pick = list[Rules.Rng.Next(list.Count)];
            string extra = "";
            var m = System.Text.RegularExpressions.Regex.Match(pick, @"^(.*?)\s*\(");
            var c = m.Success ? Db.Find(m.Groups[1].Value.Trim()) : null;
            int lvl = (int)(encLevel?.Value ?? 2);
            if (c != null && Rules.Cost(c.tier, lvl).spoor)
                extra = $"\n  SAFE-TABLE RULE (vs party level {lvl}): two or more Tiers over the posse — it arrives as sign and spoor, not in the flesh.";
            Gen($"{t.ToUpper()} — {pick}{extra}");
        }, 230));

        left.Controls.Add(new Label { Height = 8, Width = 4 });
        left.Controls.Add(Btn("Copy output", (s, e) => { if (!string.IsNullOrEmpty(genOut.Text)) Clipboard.SetText(genOut.Text); }, 112));
        left.Controls.Add(Btn("Clear", (s, e) => genOut.Clear(), 112));

        genOut = new RichTextBox { Dock = DockStyle.Fill, ReadOnly = true, Font = new Font("Consolas", 10.5f), BackColor = Color.FromArgb(252, 249, 240), BorderStyle = BorderStyle.None };
        split.Panel1.Controls.Add(left);
        split.Panel2.Controls.Add(genOut);
        page.Controls.Add(split);
        return page;
    }

    void Gen(string s)
    {
        genOut.Text = s + "\n\n" + new string('—', 44) + "\n\n" + genOut.Text;
        Log(s.Split('\n')[0]);
    }

    // ============================================================ REFERENCE TAB
    TabPage BuildReferenceTab()
    {
        var page = new TabPage("Reference") { BackColor = Paper };
        var rtf = new RichTextBox { Dock = DockStyle.Fill, ReadOnly = true, BackColor = Paper, Font = new Font("Segoe UI", 10f), BorderStyle = BorderStyle.None, Padding = new Padding(10) };
        void H(string s) { rtf.SelectionFont = new Font("Segoe UI", 12.5f, FontStyle.Bold); rtf.SelectionColor = Blood; rtf.AppendText(s + "\n"); }
        void T(string s) { rtf.SelectionFont = new Font("Segoe UI", 10f); rtf.SelectionColor = Ink; rtf.AppendText(s + "\n"); }
        void M(string s) { rtf.SelectionFont = new Font("Consolas", 10f); rtf.SelectionColor = Ink; rtf.AppendText(s + "\n"); }

        H("The Four Degrees");
        T("Beat the DC: success. Beat it by 10: critical success. Miss: failure. Miss by 10: critical failure.");
        T("A natural 20 steps the result up one degree; a natural 1 steps it down one.\n");

        H("Setting a DC");
        T("Trivial 10 · Easy 13 · Average 15 · Hard 18 · Very Hard 20 · Punishing 25 · Beyond 30.\n");

        H("A Turn in the Iron Code");
        T("Initiative is a Notice check. Each turn is three Beats: Strike, Stride, Aim/Brace, Interact, Reload, Take Cover. A Strike is d20 + attack proficiency + DEX/STR against Defense. Multiple Attack Penalty −5/−10 (Agile weapons −4/−8). A critical hit applies the weapon's Fatal die.\n");

        H("Threat by Tier");
        T("A creature is a fair, hard fight for a party of twice its Tier in levels.");
        M("Tier   Defense  Attack  Blood   Saves(hi/lo)  Damage    Dread DC");
        for (int i = 0; i < 5; i++)
        {
            var r = Rules.TierRow[i];
            M($"  {Rules.Roman(i + 1),-4} {r.def,6} {("+" + r.atk),7} {r.blood,6}    +{r.hi} / +{r.lo,-5} {r.dmg,-8} {r.dread}");
        }
        T("");
        H("The Encounter Budget");
        T("4 points per player character. An even-Tier foe costs 4; a mook (a Tier or two down) costs 1; a standout (a Tier up) costs 8. Spend the budget and the fight is fair; overspend and you had better mean it.\n");

        H("Blood, Dying & Grievous Wounds");
        T("At 0 Blood a soul is Dying and Bleeding; death comes at −CON. A single blow for half maximum Blood or more, or any critical hit, forces a Fortitude save (DC 15, higher for terrible weapons) or a Lasting Injury:");
        M("  d6   1 Bloody Gash · 2 Cracked Ribs · 3 Maimed Hand");
        M("       4 Lamed Leg · 5 Ruined Eye or Ear · 6 Gut-Shot");
        T("Lasting Injuries do not heal with rest alone — they take a Sawbones, time, and sometimes a graveyard. Nonlethal: declare before the roll that you strike nonlethally; fists and a club do so by default; most other arms take −2 to pull the blow. A foe at 0 Blood that way is senseless, not dead.\n");

        H("Conditions  (Appendix B)");
        M("Bleeding    Lose 1 Blood each round until stabilized");
        M("Blinded     −4 Defense, −4 most actions, lose DEX to Defense, half Speed");
        M("Clumsy      −2 on DEX-based Strikes, checks, and Defense");
        M("Drained     −2 on Fortitude and CON checks; lose Blood equal to");
        M("            your level, until recovered");
        M("Dying       At 0 Blood; unconscious and Bleeding toward −CON and death");
        M("Fatigued    −2 on checks and saves; cannot Aim or run; rest to shed it");
        M("Frightened  −1 (or worse) on everything; lessens one step each turn");
        M("Grabbed     Held fast; Off-Guard; −4 DEX; a check to break free");
        M("Lost        Mark 6; the character passes into the Keeper's hands");
        M("Marked      Stepped along the Mark track (see The Mark, below)");
        M("Off-Guard   −2 Defense; unaware, flanked, sprawled, or caught unready");
        M("Prone       −4 to melee; +4 to others' ranged against you;");
        M("            rising costs a Beat");
        M("Sickened    −2 on Strikes, damage, checks, and saves; nausea");
        M("Slowed      Lose one Beat each turn while it lasts; may still defend");
        M("Stunned     Drop what you hold; lose all Beats this round; −2 Defense");
        T("");

        H("Nerve & Dread");
        T("Nerve = RES score + level. A Dread Check is a Will save against the horror's Dread DC. On a failure, Nerve is lost by the horror's Tier: 1 (I), 1d4 (II), 1d6 (III), 1d10 (IV–V). A critical failure doubles it. At 0 Nerve a soul Breaks. Familiarity is the death of dread — the same sight costs nothing the second time.\n");

        H("Recovering Nerve");
        T("Confession, spoken plainly to someone who listens: 1d6. A full night unmolested in genuine safety: 1d6 — a week of true peace restores all of it. A Preacher's sermon, a Sawbones' reason, a comrade's grim joke, or a point of Grit can each buy back a measure of steadiness. Whiskey steadies the hand now (1d4) but courts a vice and the Fortitude saves that come with it.\n");

        H("The Mark  (six steps)");
        T("The Mark moves only when a soul CHOOSES the dark — a bargain, a rite, a heeding. Never for a bad roll, never for merely being wounded. At the sixth step, the country keeps what it was promised.\n");

        H("The Taint of the Land  (four steps)");
        T("For every three days on cursed ground: a Fortitude save (the body first), then Will once it reaches the mind. DC 13 for uneasy ground, 16 for wronged ground, 20 for the old places. Wards ease it; sanctification or leaving sheds it.\n");

        H("Signs & the Sign DC");
        T("Where a Sign forces a save, the DC is the worker's Sign DC = 10 + half their level + RES modifier. A soul without the Signs feature working folk-rites has a Sign DC of only 10 + RES modifier — no level added.\n");

        H("Grit");
        T("Three per soul, refreshed each session. Spend one, after seeing the result, to add 1d6 to a roll just made, re-roll a failed check, refuse to fall at 0 Blood for one more round, shrug a fright until the end of your next turn, or soften a critical failure to an ordinary failure. The Keeper may award a point mid-session for a deed of true courage.");

        page.Controls.Add(rtf);
        return page;
    }

    // ============================================================ SESSION TAB
    FlowLayoutPanel clockPanel;

    TabPage BuildSessionTab()
    {
        var page = new TabPage("Session") { BackColor = Paper };
        var split = Split(Orientation.Horizontal, 160, 160, 0.45);

        var notesGroup = new GroupBox { Text = "The Keeper's ledger  (auto-saves on exit && every five minutes)", Dock = DockStyle.Fill, Padding = new Padding(8), ForeColor = Blood, Font = new Font("Segoe UI", 9.5f, FontStyle.Bold) };
        notesBox = new TextBox { Multiline = true, Dock = DockStyle.Fill, ScrollBars = ScrollBars.Vertical, Font = new Font("Segoe UI", 10f), BorderStyle = BorderStyle.None, BackColor = Color.FromArgb(252, 249, 240) };
        var nbar = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 40 };
        nbar.Controls.Add(Btn("Stamp the date", (s, e) =>
        {
            notesBox.AppendText((notesBox.TextLength > 0 ? Environment.NewLine : "") +
                $"—  {DateTime.Now:MMMM d, yyyy}  —" + Environment.NewLine);
            notesBox.Focus();
        }, 115, "Drop a dated session header into the ledger"));
        notesGroup.Controls.Add(notesBox);
        notesGroup.Controls.Add(nbar);

        var clocksGroup = new GroupBox { Text = "Threads && clocks", Dock = DockStyle.Fill, Padding = new Padding(8), ForeColor = Blood, Font = new Font("Segoe UI", 9.5f, FontStyle.Bold) };
        var cbar = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 40 };
        cbar.Controls.Add(Btn("＋ New thread", (s, e) => NewThread(), 110));
        cbar.Controls.Add(Btn("Save now", (s, e) => { AutoSave(); Log("Session saved."); }, 90));
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
        return page;
    }

    void NewThread()
    {
        using var f = new Form { Width = 360, Height = 200, Text = "New thread", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, BackColor = Paper };
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
        using var f = new Form { Width = 360, Height = 160, Text = "Rename thread", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, BackColor = Paper };
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
