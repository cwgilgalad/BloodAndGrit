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
        Tip.SetToolTip(beastList, "Double-click a creature (or press Enter) to open it in its own window");
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

    // ============================================================ ENCOUNTER TAB
    DataGridView encGrid;
    NumericUpDown encLevel, encQty;
    static readonly Font SpoorFont = new("Segoe UI", 9.5f, FontStyle.Bold);   // see the encounter grid's CellFormatting
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
            // SpoorFont is cached: CellFormatting fires per visible cell per repaint, and a
            // fresh Font each time hands a GDI handle to the finalizer queue on every paint.
            if (name == "role") { e.Value = role; if (spoor) { e.CellStyle.ForeColor = Blood; e.CellStyle.Font = SpoorFont; } }
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
        Watermark(encGrid, () => GridBottom(encGrid));
        Watermark(hint, () => HintBottom(hint));

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
        void C(string prop, string head, int w, bool ro = false)
            => trkGrid.Columns.Add(new DataGridViewTextBoxColumn { DataPropertyName = prop, HeaderText = head, FillWeight = w, ReadOnly = ro });
        C("Init", "Init", 50); C("Name", "Name", 210, true); C("BloodCur", "Blood", 60);
        C("BloodMax", "/Max", 55, true); C("Defense", "Def", 50, true); C("Conditions", "Conditions", 240);
        // far-right Ledger button — posse souls only; creatures keep their double-click
        // stat block and ad-hoc rows have no sheet to show, so neither draws a button
        trkGrid.Columns.Add(new DataGridViewButtonColumn
        { HeaderText = "", Text = "Ledger", UseColumnTextForButtonValue = true, FillWeight = 60, Name = "ledgerBtn", ReadOnly = true });
        bool TrkHasSheet(int i) => i >= 0 && i < tracker.Count && tracker[i].IsPC
            && string.IsNullOrEmpty(tracker[i].Ref) && party.Any(p => p.Name == tracker[i].Name);
        trkGrid.CellPainting += (s, e) =>
        {
            if (e.RowIndex >= 0 && e.ColumnIndex >= 0 && trkGrid.Columns[e.ColumnIndex].Name == "ledgerBtn" && !TrkHasSheet(e.RowIndex))
            { e.PaintBackground(e.ClipBounds, true); e.Handled = true; }
        };
        trkGrid.CellContentClick += (s, e) =>
        {
            if (e.RowIndex >= 0 && e.ColumnIndex >= 0 && trkGrid.Columns[e.ColumnIndex].Name == "ledgerBtn" && TrkHasSheet(e.RowIndex))
            { var p = party.FirstOrDefault(x => x.Name == tracker[e.RowIndex].Name); if (p != null) ShowSoulCard(p); }
        };
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
        if (foes.Count == 0) { Log("No foes on the field to clear."); round = 1; if (roundLbl != null) roundLbl.Text = "Round 1"; return; }
        if (!Confirm($"New fight? Clears {foes.Count} foe(s), keeps the posse, resets to Round 1.")) return;
        foreach (var f in foes) tracker.Remove(f);
        foreach (var c in tracker) c.Conditions = "";
        round = 1; if (roundLbl != null) roundLbl.Text = "Round 1"; trkGrid?.Refresh();
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
        // The city generator's four rolls answer the four questions the Keeper's Book (Ch. XIV)
        // says a city needs beyond a town's want/tell/secret: an industry quarter, a machine,
        // a wrong note, and something for a country posse to actually be hired for.
        left.Controls.Add(Btn("A city, in four rolls", (s, e) => Gen(
            $"A CITY — {Db.Pick("cityQuarter").ToUpper()}\n" +
            $"  Who really runs it: {Db.Pick("cityMachine")}\n" +
            $"  Its wrong note:     {Db.Pick("cityWrongNote")}\n" +
            $"  Work for a posse:   {Db.Pick("cityJob")}"), 230));
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
            if (c != null && Rules.Cost(c.tier, lvl).spoor)
                extra = $"\n  SAFE-TABLE RULE (vs party level {lvl}): two or more Tiers over the posse — it arrives as sign and spoor, not in the flesh.";
            Gen($"{t.ToUpper()} — {pick}{extra}");
        }
        var terr = new ComboBox { Width = 250, DropDownStyle = ComboBoxStyle.DropDownList };
        foreach (var k in Db.Terrain.Keys) if (k != villainTable) terr.Items.Add(k);
        terr.SelectedIndex = 0;
        left.Controls.Add(terr);
        left.Controls.Add(Btn("Roll on that ground", (s, e) => RollGround(terr.SelectedItem.ToString()), 230));
        left.Controls.Add(Btn("The Hand Behind It — a villain", (s, e) => RollGround(villainTable), 230,
            "Who's truly behind the trouble — the villain picker, its own table in the book"));

        left.Controls.Add(new Label { Height = 8, Width = 4 });
        left.Controls.Add(Btn("Copy output", (s, e) => { if (!string.IsNullOrEmpty(genOut.Text)) Clipboard.SetText(genOut.Text); }, 112));
        left.Controls.Add(Btn("Clear", (s, e) =>
        {
            if (genOut.TextLength == 0) return;
            if (Confirm("Clear the generator output?")) genOut.Clear();
        }, 112));

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

    TabPage BuildReferenceTab()
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

        refDeck = new (string, Action<RichTextBox>)[]
        {
            ("The Roll",                  RefLeafRoll),
            ("A Turn in the Iron Code",   RefLeafIronCode),
            ("Blood, Wounds & Healing",   RefLeafWounds),
            ("Conditions",                RefLeafConditions),
            ("Nerve & Dread",             RefLeafNerve),
            ("The Mark & the Taint",      RefLeafMarkTaint),
            ("Signs & Grit",              RefLeafSignsGrit),
            ("Miracles of the Faithful",  RefLeafMiracles),
            ("The Long Odds",             RefLeafLongOdds),
            ("Arms of the Frontier",      RefLeafArms),
            ("Goods & Provisions",        RefLeafGoods),
            ("Skills, Saves & Abilities", RefLeafSkills),
            ("Running in Town",           RefLeafCity),
        };

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
        RI(r, "The safe-table rule: a horror two or more Tiers over the posse arrives as sign and spoor, not in the flesh.");
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
        cbar.Controls.Add(Btn("＋ New thread", (s, e) => NewThread(), 110));
        cbar.Controls.Add(Btn("Save now", (s, e) => { AutoSave(); Log("Session saved."); }, 90));
        cbar.Controls.Add(Btn("Clear threads", (s, e) =>
        {
            if (clocks.Count == 0) { Log("No threads to clear."); return; }
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
