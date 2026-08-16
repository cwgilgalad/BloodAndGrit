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
        Tip.SetToolTip(beastTier, "Show one Tier only. A creature's Tier is what makes it a fair, hard fight "
            + "for a posse of twice that many levels — Tier II is written for four 4th-level souls. Two Tiers "
            + "over the posse and the app will offer it as a sign on the trail instead of a thing on the field.");
        beastTier.Items.AddRange(new object[] { "Any tier", "Tier I", "Tier II", "Tier III", "Tier IV", "Tier V" });
        beastTier.SelectedIndex = 0; beastTier.SelectedIndexChanged += (s, e) => FilterBeasts();
        filters.Controls.Add(beastTier);
        beastChapter = new ComboBox { Width = 215, DropDownStyle = ComboBoxStyle.DropDownList };
        Tip.SetToolTip(beastChapter, "Show one chapter of the Bestiary only — the dead, cursed beasts, men "
            + "and their shapes, spirits, weather, the Old Dark, and the two mundane chapters.\nBeasts of the "
            + "Living World and Hard Men & Hard Country are the ordinary half: they cost no Nerve and never "
            + "move the Mark, which is what lets a Keeper run a slow burn before anything gets up that shouldn't.");
        beastChapter.Items.Add("All chapters");
        foreach (var ch in Db.Creatures.Select(c => c.chapter).Distinct()) beastChapter.Items.Add(ch);
        beastChapter.SelectedIndex = 0; beastChapter.SelectedIndexChanged += (s, e) => FilterBeasts();
        filters.Controls.Add(beastChapter);
        filters.SetFlowBreak(beastChapter, true);
        // Each of these four declines when there is nothing to act on, and every one of them used
        // to decline in silence — which from the Keeper's side of the screen is the same thing as a
        // button wired to nothing. Say so. (Tracker's New fight was reported as dead for exactly
        // this reason; the whole class was swept in v1.36.0.)
        filters.Controls.Add(Btn("🎲 Random", (s, e) =>
        {
            if (beastList.Items.Count == 0) { Nope("Nothing in the list to jump to — loosen the filters."); return; }
            beastList.SelectedIndex = Rules.Rng.Next(beastList.Items.Count);
        }, 95, "Jump to a random creature in the current filter"));
        filters.Controls.Add(Btn("→ Encounter", (s, e) =>
        {
            if (beastList.SelectedItem is not Creature c) { Nope("Pick a creature from the list first."); return; }
            encounter.Add(new EncounterPick(c)); RefreshEncounter(); Log($"Encounter: added {c.name}.");
        }, 110, "Add to the encounter builder"));
        filters.Controls.Add(Lbl("  ×"));
        beastQty = new NumericUpDown { Width = 46, Minimum = 1, Maximum = 20, Value = 1, Margin = new Padding(0, 5, 3, 3) };
        Tip.SetToolTip(beastQty, "How many copies → Tracker drops at once");
        filters.Controls.Add(beastQty);
        filters.Controls.Add(Btn("→ Tracker", (s, e) =>
        {
            if (beastList.SelectedItem is not Creature c) { Nope("Pick a creature from the list first."); return; }
            AddCreatureToTracker(c, (int)beastQty.Value);
        }, 95, "Drop this many onto the battlefield"));
        // the pop-out lived only behind a double-click and its tooltip; a visible button
        // makes the feature discoverable without the mouse hovering in the right place
        filters.Controls.Add(Btn("⧉ Pop out", (s, e) =>
        {
            if (beastList.SelectedItem is not Creature c) { Nope("Pick a creature from the list first."); return; }
            ShowCreatureCard(c);
        }, 90,
            "Open this creature in its own window (or double-click it in the list)"));
        filters.Controls.Add(QuietBtn("Reset", (s, e) =>
        {
            beastSearch.Text = ""; beastTier.SelectedIndex = 0; beastChapter.SelectedIndex = 0; beastQty.Value = 1;
        }, 65, "Clear the search and filters — the whole Bestiary again"));
        beastCount = Lbl("");
        beastCount.ForeColor = Slate;
        filters.Controls.Add(beastCount);

        beastList = new ListBox { Dock = DockStyle.Fill, Font = new Font("Segoe UI", 9.5f), BorderStyle = BorderStyle.None, BackColor = Color.FromArgb(252, 249, 240) };
        StyleList(beastList);
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
        split.Panel2.Controls.Add(Measure(beastView, 14, 580));
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

    /// <summary>A creature's page, set in two faces on purpose.
    ///
    /// <para><b>Narrative is Georgia; data is Segoe UI.</b> Georgia is the books' own face, and the
    /// lore, the witness quote and the Keeper's note are the parts of this page that ARE the book —
    /// setting them in the UI's sans made the Bestiary read as a database of creatures rather than
    /// as the chapter it was extracted from. The stat lines stay sans for a reason recorded in
    /// CLAUDE.md: Georgia is a text-figure face whose 3 4 5 7 9 descend below the baseline and whose
    /// 0 1 2 sit at x-height, so "Fort +4, Ref +5, Will +2 (boss +5)" comes out visibly uneven. A
    /// RichTextBox can carry both, so each half of the page gets the face that suits it.</para></summary>
    void RenderCreature(RichTextBox rtf, Creature c)
    {
        rtf.Clear();
        void W(string s, bool bold = false, float size = 10f, Color? col = null, bool italic = false,
               string face = "Segoe UI")
        {
            var style = (bold ? FontStyle.Bold : FontStyle.Regular) | (italic ? FontStyle.Italic : 0);
            // Off the shelf (MainForm.Face): this ran about thirty times per creature and fired on
            // every arrow-key move down a list of 150, minting a native font handle each time and
            // disposing none of them.
            rtf.SelectionFont = Face(face, size, style);
            rtf.SelectionColor = col ?? Ink;
            rtf.AppendText(s);
        }
        void Prose(string s, float size = 10.5f, Color? col = null, bool italic = false)
            => W(s, false, size, col, italic, "Georgia");

        W(c.name + "\n", true, 17, Blood, face: "Georgia");
        Prose(c.tierText + "\n\n", 10f, Gold, italic: true);
        foreach (var p in c.lore) Prose(p + "\n\n");
        // GoldDeep, not Gold: this is a whole sentence, and the palette's own note says Gold is a
        // heading colour that measures about 3.5:1 on Paper — under what a person reads comfortably.
        if (!string.IsNullOrEmpty(c.witness)) Prose("“" + c.witness + "”\n\n", 10.5f, GoldDeep, italic: true);
        if (!string.IsNullOrEmpty(c.found)) { W("FOUND — ", true, 9.5f, Blood); W(c.found + "\n\n"); }
        void Stat(string k, string v) { if (!string.IsNullOrEmpty(v)) { W(k.ToUpper() + "  ", true, 9.5f, Blood); W(v + "\n"); } }
        Stat("Defense", c.defense); Stat("Blood", c.blood); Stat("Speed", c.speed);
        Stat("Saves", c.saves); Stat("Attacks", c.attacks); Stat("Special", c.special);
        Stat("Dread", c.dread); Stat("The Mark", c.mark); Stat("Putting It Down", c.puttingItDown);
        if (!string.IsNullOrEmpty(c.keeperNote)) { W("\nHOW TO PLAY IT\n", true, 9.5f, Verdigris); Prose(c.keeperNote + "\n"); }
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

    /// <summary>One line of a creature picker. The list used to hold bare names, which left out the
    /// single fact the two tabs that use it are FOR: a creature's Tier is the whole of the encounter
    /// budget (Long Odds) and the whole of the safe-table rule, and picking blind meant costing the
    /// fight only after the thing was already on the plan. User-asked.
    ///
    /// <see cref="ToString"/> is what the type-ahead matches and what lands in the box when a line is
    /// picked, so it keeps the NAME first — autocomplete matches on a prefix, and a leading "Tier IV"
    /// would make every creature untypeable. <see cref="Sep"/> is what <see cref="PickedCreature"/>
    /// cuts the name back out at.</summary>
    sealed class CreatureLine
    {
        public const string Sep = "  ·  ";
        public Creature C { get; }
        public string TierText { get; }
        public CreatureLine(Creature c) { C = c; TierText = "Tier " + Rules.Roman(c.tier); }
        public override string ToString() => C.name + Sep + TierText;
    }

    // a creature-name picker with type-ahead, shared by the Encounter and Tracker tabs
    static ComboBox CreaturePicker(int width)
    {
        var box = new ComboBox
        {
            Width = width, DropDownStyle = ComboBoxStyle.DropDown,
            AutoCompleteMode = AutoCompleteMode.SuggestAppend,
            AutoCompleteSource = AutoCompleteSource.ListItems,
            Margin = new Padding(3, 5, 3, 3),
            // Owner-drawn so the Tier can sit hard against the right edge in its own ink. Padding the
            // string instead would not line up: the list is drawn in a proportional font, where a run
            // of spaces is not a column.
            DrawMode = DrawMode.OwnerDrawFixed
        };
        foreach (var c in Db.Creatures.OrderBy(c => c.name)) box.Items.Add(new CreatureLine(c));
        box.DrawItem += (s, e) =>
        {
            e.DrawBackground();
            if (e.Index < 0 || e.Index >= box.Items.Count) return;
            var line = (CreatureLine)box.Items[e.Index];
            bool sel = (e.State & DrawItemState.Selected) != 0;
            var r = e.Bounds; r.Inflate(-3, 0);
            const TextFormatFlags mid = TextFormatFlags.VerticalCenter | TextFormatFlags.NoPrefix;
            TextRenderer.DrawText(e.Graphics, line.TierText, box.Font, r,
                sel ? SystemColors.HighlightText : Gold, mid | TextFormatFlags.Right);
            // The name is drawn second and clipped short of the Tier, so a long name eats into its
            // own ellipsis rather than painting through the number the list was added for.
            var nameBox = new Rectangle(r.X, r.Y,
                Math.Max(10, r.Width - TextRenderer.MeasureText(line.TierText, box.Font).Width - 12), r.Height);
            TextRenderer.DrawText(e.Graphics, line.C.name, box.Font, nameBox,
                sel ? SystemColors.HighlightText : Ink, mid | TextFormatFlags.Left | TextFormatFlags.EndEllipsis);
            e.DrawFocusRectangle();
        };
        return box;
    }

    /// <summary>The creature a picker is sitting on. Resolved from the TEXT rather than the selected
    /// item, because the text is what the Keeper can see and it stays right after they type over a
    /// selection — a stale SelectedItem is exactly how a picker comes to add something other than
    /// what it is showing. The Tier suffix the list appends is cut back off, and a bare name typed
    /// by hand still resolves, so nobody has to know the list decorates itself.</summary>
    static Creature PickedCreature(ComboBox box)
    {
        string t = (box?.Text ?? "").Trim();
        int cut = t.IndexOf('·');
        if (cut > 0) t = t.Substring(0, cut).Trim();
        return t.Length == 0 ? null : Db.Find(t);
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
        Tip.SetToolTip(encPick, "Type a few letters or pick from the list, then Add. Every line "
            + "carries its creature's Tier — that is what the cost below is reckoned from.");
        encPick.KeyDown += (s, e) => { if (e.KeyCode == Keys.Enter) { AddPickToEncounter(); e.SuppressKeyPress = true; } };
        top.Controls.Add(encPick);
        top.Controls.Add(Lbl(" ×"));
        encQty = new NumericUpDown { Width = 46, Minimum = 1, Maximum = 20, Value = 1, Margin = new Padding(0, 5, 3, 3) };
        Tip.SetToolTip(encQty, "How many of that creature to cost into the plan at once. Six wolves is six "
            + "lines of budget, not one — which is the whole point of costing a fight before running it.");
        top.Controls.Add(encQty);
        top.Controls.Add(Btn("＋ Add", (s, e) => AddPickToEncounter(), 75, "Add it to the plan (or press Enter in the box)"));
        top.Controls.Add(Btn("✕ Remove", (s, e) =>
        {
            if (encGrid.CurrentRow?.DataBoundItem is not EncounterPick p) { Nope("Select a foe in the plan first."); return; }
            encounter.Remove(p); RefreshEncounter();
        }, 85, "Take the selected foe out of the encounter"));
        top.Controls.Add(Btn("Clear", (s, e) =>
        {
            if (encounter.Count == 0) { Nope("The plan is already empty."); return; }
            if (Confirm("Clear the encounter?")) { encounter.Clear(); RefreshEncounter(); }
        }, 65, "Empty the encounter and start costing a new one"));
        // An empty plan sent an empty loop and nothing happened — no rows, no word, no way to tell
        // it apart from a button that does not work.
        top.Controls.Add(Btn("Send all → Tracker", (s, e) =>
        {
            if (encounter.Count == 0) { Nope("Nothing costed yet — add a foe to the plan first."); return; }
            foreach (var p in encounter.ToList()) AddCreatureToTracker(p.Creature);
        }, 150, "Put every listed creature on the battlefield"));

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
        var c = PickedCreature(encPick);
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
    Label trkTurnLbl;
    NumericUpDown roundBox;      // the round, kept by the app and correctable by hand
    bool roundBusy;              // true while ShowRound writes it, so the edit handler doesn't echo
    FlowLayoutPanel signPanel;   // the sign strip; hidden entirely when nothing is out there
    NumericUpDown trkAmount, trkQty;
    ComboBox trkPick;

    // The acting row's ground — gold, so it reads as "this one is up" against the posse's green
    // and the foes' clay without competing with the red a downed combatant wears. Carried a little
    // deeper in v1.38.0 when the foe ground stopped being near-white: gold and clay are both warm,
    // so what separates them is the gap between green and blue — 50 points here against the foe's
    // 12. See the palette note in MainForm.
    static readonly Color ActingRow = Color.FromArgb(250, 236, 186);
    // A sign & spoor row: cold and bloodless, so it never reads as one more body to shoot at.
    static readonly Color SignRow = Color.FromArgb(234, 238, 240);
    // Faded ink for a combatant who has already taken their turn this round.
    static readonly Color Spent = Color.FromArgb(150, 142, 128);
    Font trkBold;   // built once with the grid; CellFormatting runs on every paint

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
            using var b = new SolidBrush(Color.FromArgb(190, ink));   // the number has to stay legible on it
            g.FillRectangle(b, new Rectangle(r.X, r.Y, w, r.Height));
        }
        using var pen = new Pen(BarEdge, 1f);
        g.DrawRectangle(pen, r);
    }

    /// <summary>The death clock in the Blood column, for a soul on the ground. The Blood bar has
    /// nothing left to draw — they are at zero, so it is simply empty, which reads as "nothing is
    /// happening here" at the exact moment the most is. This fills the OTHER way: from the left, in
    /// the app's darkest red, as the bleed runs from 0 toward −CON. Full bar, empty soul.
    ///
    /// <para>Drawn rather than left to the words beside it because this is the one row on the field
    /// a Keeper has to notice without reading. The figure is in the cell to its right for anybody
    /// who then wants the count.</para></summary>
    static void PaintDeathClock(Graphics g, Rectangle r, int bleed, int deathAt)
    {
        using (var back = new SolidBrush(BarTrack)) g.FillRectangle(back, r);
        float frac = Math.Clamp(bleed / (float)Math.Max(1, deathAt), 0f, 1f);
        int w = (int)Math.Round(r.Width * frac);
        if (w > 0)
        {
            using var b = new SolidBrush(Color.FromArgb(200, RollCritBad));   // near-black red: this is the end of it
            g.FillRectangle(b, new Rectangle(r.X, r.Y, w, r.Height));
        }
        using var pen = new Pen(Blood, 1f);
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

    /// <summary>The Tracker's one refresh. Every readout on the tab that is driven by a counter —
    /// the grid, the turn line, the round box and the glass face — is redrawn here.
    ///
    /// This exists because the alternative did not work. Refreshing was done per site, as
    /// <c>RefreshTracker();</c> repeated at eighteen call sites, and every one
    /// of them was a chance to remember two of the four. <c>ShowRound</c> documents itself as the
    /// one place the round moves through, and most of those sites never called it — which is
    /// exactly why the round box would sit on a stale number until something unrelated happened to
    /// redraw it (user-reported). A readout that updates only when the caller remembers is a
    /// readout that is sometimes wrong, and a number that is sometimes wrong is worse than no
    /// number, because the Keeper stops checking it.
    ///
    /// So: anything that moves tracker state calls this, and nothing calls the four by hand.
    /// It is cheap — all four are local redraws over at most a few dozen rows.</summary>
    void RefreshTracker()
    {
        trkGrid?.Refresh();
        ShowRound();
        UpdateTurnLine();
        ShowTurnFace();
    }

    /// <summary>Say in words what the turn state is, because Beats and the MAP step are small
    /// numbers in a wide grid and a Keeper pressing "Begin turn" deserves to see something answer.
    /// </summary>
    void UpdateTurnLine()
    {
        if (trkTurnLbl == null) return;
        var c = tracker.FirstOrDefault(t => t.Acting);
        int left = tracker.Count(Rules.CanAct);
        if (c == null)
        {
            trkTurnLbl.Text = tracker.Count == 0 ? "nobody on the field yet"
                : Rules.NextUp(tracker) is Combatant up ? $"press Next turn — {up.Name} is up first"
                : "the round is spent — Next turn starts the next one";
            trkTurnLbl.ForeColor = Faint;
            return;
        }
        // What is up, and what is still to come: the second half is the part that stops a Keeper
        // counting rows to work out whether the round is nearly over.
        trkTurnLbl.Text = $"{c.Name} is up — {c.Beats} Beat{(c.Beats == 1 ? "" : "s")} left"
            + (c.Beats == 0 ? ", spent" : $", next Strike {c.NextStrike}")
            + (left == 0 ? "  ·  last of the round" : $"  ·  {left} still to go");
        trkTurnLbl.ForeColor = c.Beats == 0 ? Faint : Blood;
    }

    void AddPickToTracker()
    {
        var c = PickedCreature(trkPick);
        if (c == null) { Nope("No creature by that name — pick one from the list."); return; }
        AddCreatureToTracker(c, (int)trkQty.Value);
    }

    // ============================================================ THE TURN HOURGLASS
    // A posse that takes twenty minutes to decide who opens the door is a fight with no shape to
    // it, so the Tracker can put a glass on the table: the posse's turn gets a fixed length, the
    // sand falls where everyone can see it, and the round rolls it over by itself.
    //
    // Three deliberate choices:
    //   * OPT-IN. Off until asked for. A table that never wanted timing should never find itself
    //     timed, and a countdown nobody agreed to is pressure, not a tool.
    //   * The LENGTH is a preference, not session state — it is a house rule about how this table
    //     plays, so it lives in prefs.json and is set before anyone sits down. Five minutes by
    //     default; ten is one click away, and any length from five seconds to an hour is allowed.
    //   * It NEVER acts on the game. It logs when the sand runs out and it turns red. It does not
    //     end a turn, spend a Beat, or take a Beat away. Nothing in the books says a slow player
    //     loses their action, so the app must not invent it — and a timer that silently ended
    //     someone's turn would be the one feature here that could lose a Keeper's work.
    //
    // The clock itself is pure and lives in the rules library (Rules' TurnClock), so the smoke rig
    // can run a five-minute turn in a millisecond. This half is ink, one Windows timer, and wiring.
    TurnClock turnClock;
    HourglassView turnGlass;
    Label turnFace;
    System.Windows.Forms.Timer turnTicker;
    readonly List<Control> turnGlassParts = new();
    /// The Tracker bar's own switch for the glass — down when the glass is out, up when it is not.
    /// See where it is built for why it has to exist.
    CheckBox glassToggle;
    /// Set while ShowTurnTimer is putting the switch back in agreement with the state it just set,
    /// so the CheckedChanged that follows doesn't call straight back into it.
    bool glassToggleSyncing;

    /// <summary>The glass, its face, and its own little menu, built as one column that the Tracker
    /// hangs at the RIGHT EDGE of the action bar rather than dropping into the flow.
    ///
    /// It used to ride inline at the end of the round row, which made it 30×40 — a postage stamp
    /// competing with fourteen buttons for the same eye. A turn timer is meant to be read across a
    /// table without looking for it, so it now gets a column of its own at the far right and takes
    /// the bar's FULL HEIGHT, which is as large as the layout can give it without taking a pixel
    /// from anything else: the flow simply keeps its own width and wraps a little sooner.
    ///
    /// The right edge is also the honest place for it. Everything else on this bar is something the
    /// Keeper DOES; the glass is the only thing that acts on its own, so it sits apart from the
    /// verbs instead of being filed among them. The m:ss face and the Glass ▾ menu stay beside it,
    /// because a clock you cannot set is a clock you stop trusting.</summary>
    Control BuildTurnGlass()
    {
        var prefs = Prefs.Load();
        turnClock = new TurnClock { PresetSeconds = prefs.TurnSeconds };

        // Dock-filled inside its cell, so its size comes from the bar rather than from constants —
        // the same rule the dialogs follow. HourglassView draws every part of the glass as a
        // fraction of its own box, so it simply gets bigger; nothing here needs a second layout.
        turnGlass = new HourglassView(turnClock)
        {
            Dock = DockStyle.Fill, MinimumSize = new Size(54, 44), Margin = new Padding(2, 2, 8, 2)
        };
        turnGlass.Click += (s, e) => ToggleTurnGlass();
        Tip.SetToolTip(turnGlass, "The posse's turn, running out. Click the glass to start or hold it.\n"
            + "It resets and starts itself at the top of every round. When the sand is through it says "
            + "so in the log and turns red — it never ends anyone's turn or takes a Beat away. That is "
            + "still the Keeper's call.");

        turnFace = new Label
        {
            AutoSize = false, Width = 52, Height = 24, TextAlign = ContentAlignment.MiddleLeft,
            Font = new Font("Segoe UI", 11f, FontStyle.Bold), ForeColor = Gold,
            Margin = new Padding(0, 8, 2, 3), Tag = "readout"      // a live number: it must say what it is
        };
        Tip.SetToolTip(turnFace, "How much of the posse's turn is left, counting down. Set the length "
            + "from the Glass menu beside it, or from Table ▸ The turn glass.");

        var menu = MenuBtn("Glass ▾", 74, "Start, hold or reset the turn glass, and set how long a turn is",
            ("Start / hold  (click the glass)", (s, e) => ToggleTurnGlass()),
            ("Reset to a full glass", (s, e) => { turnClock.Reset(); SyncTicker(); ShowTurnGlass(); Say("The turn glass is full again.", Gold); }),
            ("-", null),
            ("— How long is a turn —", null),
            (TurnPresetLabel(0), (s, e) => SetTurnLength(TurnClock.Presets[0])),
            (TurnPresetLabel(1), (s, e) => SetTurnLength(TurnClock.Presets[1])),
            (TurnPresetLabel(2), (s, e) => SetTurnLength(TurnClock.Presets[2])),
            (TurnPresetLabel(3), (s, e) => SetTurnLength(TurnClock.Presets[3])),
            (TurnPresetLabel(4), (s, e) => SetTurnLength(TurnClock.Presets[4])),
            (TurnPresetLabel(5), (s, e) => SetTurnLength(TurnClock.Presets[5])),
            ("Some other length…", (s, e) => AskTurnLength()),
            ("-", null),
            ("Put the glass away", (s, e) => { ShowTurnTimer(false); RebuildMenu(); }));

        // One timer for the whole feature, started only when the glass is on show. 60 ms is about
        // 16 frames a second — enough that sand looks like it is falling, cheap enough that a
        // Keeper with the Tracker open all evening never notices it.
        turnTicker = new System.Windows.Forms.Timer { Interval = 60 };
        turnTicker.Tick += (s, e) =>
        {
            if (turnClock.Tick(turnTicker.Interval))
                Log($"The posse's turn is through — {TurnClock.Spell(turnClock.PresetSeconds)} gone.");
            turnGlass.Advance();
            ShowTurnFace();
        };

        // The column: the glass down the left of it spanning both rows, the face and the menu
        // stacked to its right. Rows at 50/50 so the glass grows with the bar instead of being
        // pinned to whatever the face and the button happen to measure.
        var col = new TableLayoutPanel
        {
            Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 2,
            BackColor = Color.FromArgb(243, 237, 221),
            Margin = new Padding(0), Padding = new Padding(10, 3, 4, 3)
        };
        col.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100f));   // the glass takes the slack
        col.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        col.RowStyles.Add(new RowStyle(SizeType.Percent, 50f));
        col.RowStyles.Add(new RowStyle(SizeType.Percent, 50f));
        col.Controls.Add(turnGlass, 0, 0);
        col.SetRowSpan(turnGlass, 2);
        col.Controls.Add(turnFace, 1, 0);
        col.Controls.Add(menu, 1, 1);
        turnFace.Margin = new Padding(0, 4, 2, 0);
        turnFace.Anchor = AnchorStyles.Left | AnchorStyles.Bottom;
        menu.Margin = new Padding(0, 0, 2, 4);
        menu.Anchor = AnchorStyles.Left | AnchorStyles.Top;

        // One entry, so ShowTurnTimer keeps working: showing or hiding the column shows or hides
        // the whole feature, which is what it always meant.
        turnGlassParts.Clear();
        turnGlassParts.Add(col);
        ShowTurnTimer(prefs.TurnTimer, quiet: true);
        return col;
    }

    static string TurnPresetLabel(int i) => TurnClock.Spell(TurnClock.Presets[i])
        + (TurnClock.Presets[i] == TurnClock.DefaultSeconds ? "   (the default)" : "");

    /// <summary>Show or hide the whole glass, and remember the answer. Also reachable from the Table
    /// menu, so it can be settled before a session as well as during one.</summary>
    internal void ShowTurnTimer(bool on, bool quiet = false)
    {
        if (turnGlass == null) { Prefs.Save(WithTurn(Prefs.Load(), on, null)); return; }
        foreach (var c in turnGlassParts) c.Visible = on;
        SyncGlassToggle(on);            // four routes lead here; the switch must show all four
        if (!on) { turnClock.Pause(); turnClock.Reset(); }
        SyncTicker();
        ShowTurnGlass();
        if (!quiet) Prefs.Save(WithTurn(Prefs.Load(), on, null));   // the quiet call IS the saved state
        if (!quiet) Say(on
            ? $"The turn glass is on the table — {TurnClock.Spell(turnClock.PresetSeconds)} to a turn."
            : "The turn glass is put away.", Gold);
    }

    /// <summary>Put the Tracker bar's switch in agreement with the state, without letting it answer
    /// back. The switch is one of four routes to the glass — the other three are the View menu, the
    /// Table menu and the Glass ▾ menu's "Put the glass away" — and every one of them lands in
    /// <see cref="ShowTurnTimer"/>, so this is the single place the switch is ever set. Guarded
    /// because setting Checked raises CheckedChanged whether a hand or the code did it, and that
    /// handler calls ShowTurnTimer straight back.</summary>
    void SyncGlassToggle(bool on)
    {
        if (glassToggle == null || glassToggleSyncing) return;
        glassToggleSyncing = true;
        glassToggle.Checked = on;
        // What it SAYS, not what pressing it does: a switch already shows that by being down.
        glassToggle.Text = on ? "Turn glass — on" : "＋ Turn glass";
        glassToggleSyncing = false;
    }

    /// <summary>Whether the glass is on the table. Falls back to the saved preference, because the
    /// Table menu can ask this before the Tracker tab has ever been opened — tabs fill themselves
    /// on first selection, so there is no glass to interrogate until then.</summary>
    internal bool TurnTimerOn => turnGlassParts.Count > 0 ? turnGlassParts[0].Visible : Prefs.Load().TurnTimer;

    static Prefs.Data WithTurn(Prefs.Data d, bool? on, int? seconds)
    {
        if (on.HasValue) d.TurnTimer = on.Value;
        if (seconds.HasValue) d.TurnSeconds = seconds.Value;
        return d;
    }

    /// The animation timer runs only while sand is actually falling. A 16-frames-a-second repaint
    /// of a held glass costs nothing visible and does nothing useful, and the Tracker is the tab
    /// most likely to be left open all evening.
    void SyncTicker()
    {
        if (turnTicker != null) turnTicker.Enabled = TurnTimerOn && turnClock.Running;
    }

    void ToggleTurnGlass()
    {
        turnClock.Toggle();
        SyncTicker();
        ShowTurnGlass();
        Say(turnClock.Running
            ? $"The turn glass is running — {turnClock.Face} left."
            : turnClock.Expired ? "The turn glass is through." : $"The turn glass is held at {turnClock.Face}.",
            turnClock.Expired ? Blood : Gold);
    }

    /// <summary>Set how long a turn is, turn the glass over onto that length, and keep it for next
    /// time.
    ///
    /// Choosing a length used to leave a RUNNING glass alone, which was wrong two ways
    /// (user-reported). Picking "two minutes" is the Keeper saying a turn is two minutes; being
    /// told the current one keeps its old length is an answer to a question nobody asked. Worse,
    /// it rendered nonsense: <c>TurnClock.PresetSeconds</c> only refills a HELD clock, so the
    /// running one kept its old <c>LeftMs</c> against the new preset — and since the sand level is
    /// <c>1 - LeftMs/(preset*1000)</c>, shortening the turn drove Spent negative and the glass read
    /// FULL while counting down from the old, longer turn.
    ///
    /// So the glass is turned over onto the new length, and keeps running if it was running.</summary>
    internal void SetTurnLength(int seconds)
    {
        if (turnClock == null) { Prefs.Save(WithTurn(Prefs.Load(), null, seconds)); return; }
        bool wasRunning = turnClock.Running;
        turnClock.PresetSeconds = seconds;
        turnClock.Reset();                       // Reset clears Running, so restore it below
        if (wasRunning) turnClock.Start();
        Prefs.Save(WithTurn(Prefs.Load(), null, turnClock.PresetSeconds));
        SyncTicker();
        ShowTurnGlass();
        Say($"A posse's turn is now {TurnClock.Spell(turnClock.PresetSeconds)}."
            + (wasRunning ? " The glass is turned over and running." : ""), Gold);
    }

    /// A length of the Keeper's own choosing, in whole seconds, measured rather than laid out.
    /// Reachable from the Table menu before the Tracker has ever been built, so it reads the
    /// current length off the saved preference when there is no glass yet to ask.
    internal void AskTurnLength()
    {
        int current = turnClock?.PresetSeconds ?? Prefs.Load().TurnSeconds;
        using var f = new Sheet
        {
            Text = "How long is a turn?", FormBorderStyle = FormBorderStyle.FixedDialog,
            StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false,
            ShowIcon = false, BackColor = Paper
        };
        const int Pad = 16, CW = 380;
        string prose = "How long the posse gets to take its turn. The glass never ends a turn by "
            + "itself — it only shows the time going, and says so in the log when it is through.";
        var say = new Label
        {
            Left = Pad, Top = Pad, Width = CW, ForeColor = Ink, Text = prose,
            Height = TextRenderer.MeasureText(prose, f.Font, new Size(CW, 0), TextFormatFlags.WordBreak).Height + 4
        };
        var mins = new NumericUpDown
        {
            Left = Pad, Top = say.Bottom + 12, Width = 70, Minimum = 0, Maximum = 60,
            Value = current / 60
        };
        Tip.SetToolTip(mins, "Whole minutes.");
        var secs = new NumericUpDown
        {
            Left = mins.Right + 56, Top = mins.Top, Width = 70, Minimum = 0, Maximum = 59,
            Value = current % 60
        };
        Tip.SetToolTip(secs, "And seconds on top. Five seconds is the shortest turn the glass will keep.");
        var ok = new Button { Text = "That's a turn", Left = Pad + CW - 210, Top = mins.Bottom + 16, Width = 110, Height = 30, DialogResult = DialogResult.OK };
        var cancel = new Button { Text = "Cancel", Left = Pad + CW - 92, Top = ok.Top, Width = 92, Height = 30, DialogResult = DialogResult.Cancel };
        f.Controls.AddRange(new Control[]
        {
            say, mins, new Label { Left = mins.Right + 6, Top = mins.Top + 4, Width = 46, Text = "minutes", ForeColor = Ink },
            secs, new Label { Left = secs.Right + 6, Top = secs.Top + 4, Width = 54, Text = "seconds", ForeColor = Ink },
            ok, cancel
        });
        f.ClientSize = new Size(CW + Pad * 2, ok.Bottom + Pad);
        f.AcceptButton = ok; f.CancelButton = cancel;
        if (f.ShowDialog(this) != DialogResult.OK) return;
        SetTurnLength(Math.Max(5, (int)mins.Value * 60 + (int)secs.Value));
    }

    /// The top of a round turns the glass over — that IS the posse's turn beginning. Called from
    /// NextRound so the one path the app uses to roll a round over is the one that resets it.
    void TurnOverTheGlass()
    {
        if (turnClock == null || !TurnTimerOn) return;
        turnClock.Reset();
        turnClock.Start();
        SyncTicker();
        ShowTurnGlass();
    }

    void ShowTurnGlass() { ShowTurnFace(); turnGlass?.Invalidate(); }

    void ShowTurnFace()
    {
        if (turnFace == null) return;
        turnFace.Text = turnClock.Face;
        turnFace.ForeColor = turnClock.Expired ? Blood
            : turnClock.Running ? (turnClock.LeftMs <= 30_000 ? Color.FromArgb(150, 70, 30) : Ink)
            : Gold;
    }

    TabPage BuildTrackerTab()
    {
        var page = new TabPage("Tracker") { BackColor = Paper };
        var bar = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(6, 4, 6, 4), BackColor = Color.FromArgb(243, 237, 221) };
        // The round is the app's to keep — it advances itself as the turns are taken — but it stays
        // a number the Keeper can reach. A spinner says "you may change this" the way a label never
        // does, and the value is read live so a lazily-built tab never shows Round 1 on a fight's
        // third (which is exactly what the old hard-coded label did).
        bar.Controls.Add(new Label
        {
            Text = "Round", Font = new Font("Segoe UI", 12f, FontStyle.Bold), ForeColor = Blood,
            Padding = new Padding(0, 6, 4, 0), AutoSize = true
        });
        roundBox = new NumericUpDown
        {
            Minimum = 1, Maximum = 999, Value = Math.Clamp(round, 1, 999), Width = 62,
            Font = new Font("Segoe UI", 11f, FontStyle.Bold), ForeColor = Blood,
            Margin = new Padding(0, 5, 12, 3), TextAlign = HorizontalAlignment.Center
        };
        Tip.SetToolTip(roundBox, "The round. The app advances it as the field takes its turns — "
            + "set it by hand if the table has got ahead of it.");
        roundBox.ValueChanged += (s, e) =>
        {
            if (roundBusy) return;
            round = (int)roundBox.Value;
            Log($"— Round {round} (set by hand) —");
            UpdateTurnLine();
        };
        bar.Controls.Add(roundBox);
        // The turn readout rides beside the round, fixed-width so a long name can't shove the
        // button rows around, and it gets the row to itself.
        trkTurnLbl = new Label
        {
            Width = 430, Height = 22, AutoSize = false, Font = new Font("Segoe UI", 9.5f, FontStyle.Italic),
            TextAlign = ContentAlignment.MiddleLeft, Padding = new Padding(0, 0, 8, 0), AutoEllipsis = true
        };
        Tip.SetToolTip(trkTurnLbl, "Whose turn it is, what they have left to spend, and what the next Strike costs");
        bar.Controls.Add(trkTurnLbl);
        bar.SetFlowBreak(trkTurnLbl, true);
        UpdateTurnLine();

        // ---- row 2: the turn you are taking ----
        // The bar used to be thirteen buttons of identical weight in no particular order, so the
        // three pressed every single turn looked exactly like the one that wipes the field. It now
        // reads left to right as a sentence: whose turn → what they do → what it costs them → and
        // then, set apart, putting the field back together.
        // The one thing a Keeper presses over and over, painted like it. Everything else on this bar
        // is an exception to the loop; this IS the loop, and it carries the round with it.
        bar.Controls.Add(PrimaryBtn("▶  Next turn", (s, e) => NextTurn(), 112,
            "Hand the turn to whoever is up next by initiative, and roll the round over when the "
            + "field has all gone (Ctrl+Space)"));
        // The three OTHER ways a turn can move, behind one label. Each is an exception the loop
        // above already handles by itself — begin out of order, step the round by hand, re-roll the
        // order — so each was a button competing for the eye with the one button that runs the
        // fight. Collapsed, the row reads "press this; here are the exceptions", which is the shape
        // of the thing. Both shortcuts still work without opening it (Ctrl+R, Ctrl+I).
        bar.Controls.Add(MenuBtn("Turn order ▾", 104,
            "The exceptions to Next turn — hand the turn out of order, step the round by hand, or "
            + "roll the whole field's initiative again",
            ("Begin the SELECTED combatant's turn", (s, e) => BeginTurnForSelected()),
            ("Step to the next round  (Ctrl+R)", (s, e) => NextRound()),
            ("-", null),
            ("Roll initiative for the field  (Ctrl+I)", (s, e) => RollInitiative())));
        // The glass is off by default and, when it is off, the whole column at the right edge is
        // hidden — so the ONE route to turning it on was a menu called Table, which is where nobody
        // looks for a clock (user-reported: "I don't see an option to turn on the hourglass
        // anywhere"). This switch stands where the turn is taken, so the feature is never invisible.
        //
        // It was a button that appeared only while the glass was away, which answered half the
        // question: putting the glass OUT was on the bar, putting it away was back in a menu, and a
        // control that vanishes once you have used it says nothing about the state it left behind
        // (user-reported). A held-down switch says both things at once — that the glass is out, and
        // that this is what puts it away — which is what a toggle is FOR. Same shape as the Map
        // tab's ✥ Move things, so the app has one idiom for "this is on".
        glassToggle = ToggleBtn("＋ Turn glass", 108,
            "Put an hourglass on the bar that runs the posse's turn down, or take it "
            + "away. It never ends a turn or takes a Beat — it shows the time going and says so when it is "
            + "through. Also on the Table and View menus, and its length is yours to set.");
        glassToggle.CheckedChanged += (s, e) =>
        {
            if (glassToggleSyncing) return;
            ShowTurnTimer(glassToggle.Checked);
            RebuildMenu();                 // the two menu checkmarks answer to the same one state
        };
        bar.Controls.Add(glassToggle);

        bar.Controls.Add(BarSep());
        bar.Controls.Add(Btn("Strike ▸", (s, e) => StrikeDialog(), 72, "Resolve a Strike from the selected combatant — the engine handles to-hit, degrees, MAP, Fatal, and DR"));
        bar.Controls.Add(Btn("Dread ▸", (s, e) => DreadDialog(), 70, "Roll a Dread Check for the selected soul — Nerve off the ladder, Frightened, and the break at 0 Nerve"));
        bar.Controls.Add(Btn("✦ Work ▸", (s, e) => WorkPowerDialog(), 84,
            "Work a Sign, a Miracle, or a creature's own power: who works it, on whom, what it costs "
            + "them, and how many rounds it lasts"));

        bar.Controls.Add(BarSep());
        bar.Controls.Add(Lbl("Amt:"));
        trkAmount = new NumericUpDown { Minimum = 1, Maximum = 999, Value = 5, Width = 58, Margin = new Padding(3, 6, 3, 3) };
        Tip.SetToolTip(trkAmount, "How much Blood the Damage and Heal buttons beside it move. Neither runs "
            + "past 0 or past the maximum, and a posse soul's row here and on the Posse tab are the same "
            + "number — change it in one place and it changes in both.");
        bar.Controls.Add(trkAmount);
        bar.Controls.Add(Btn("Damage", (s, e) => AdjustCombatant(-1), 80, "Subtract the Amt from the selected combatant (Ctrl+D)"));
        bar.Controls.Add(Btn("Heal", (s, e) => AdjustCombatant(+1), 65, "Add the Amt to the selected combatant (Ctrl+H)"));

        bar.Controls.Add(BarSep());
        // Putting the field back on its feet: what a Keeper reaches for when a scene ENDS, so it
        // sits at the end of the doing-things row rather than among the combat actions.
        bar.Controls.Add(MenuBtn("✚ Restore ▾", 118,
            "Put Blood — and, for the posse, Nerve — back to full, or stop somebody bleeding out",
            ($"Stop the bleeding — DC {Rules.StabilizeDc} Fortitude or Medicine", (s, e) => StabilizeDialog()),
            ("-", null),
            ("Selected combatant — Blood to full", (s, e) => RestoreSelected()),
            ("The posse — Blood, Nerve & pool to full", (s, e) => RestPosse()),
            ("-", null),
            ("Everyone on the field — Blood to full", (s, e) => RestoreField())));
        bar.SetFlowBreak(bar.Controls[bar.Controls.Count - 1], true);

        // ---- row 3: the field itself — filling it, ordering it, and clearing it ----
        // Roll initiative moved up into Turn order ▾: it is pressed once at the top of a fight, and
        // it belongs with the other two ways the order gets set rather than beside the foe picker.
        bar.Controls.Add(MenuBtn("Sort ▾", 70, "Order the field",
            ("Initiative — high to low", (s, e) => SortTracker(TrkSort.InitDesc)),
            ("Initiative — low to high", (s, e) => SortTracker(TrkSort.InitAsc)),
            ("-", null),
            ("Name — A to Z", (s, e) => SortTracker(TrkSort.NameAsc)),
            ("Name — Z to A", (s, e) => SortTracker(TrkSort.NameDesc)),
            ("-", null),
            ("Blood — most to least", (s, e) => SortTracker(TrkSort.BloodDesc)),
            ("Blood — least to most", (s, e) => SortTracker(TrkSort.BloodAsc))));

        bar.Controls.Add(BarSep());
        bar.Controls.Add(Lbl("Foe:"));
        trkPick = CreaturePicker(200);
        Tip.SetToolTip(trkPick, "Any creature in the Bestiary, each line showing its Tier — type a "
            + "few letters, then Add. A thing two Tiers over the posse goes on the trail, not the field.");
        trkPick.KeyDown += (s, e) => { if (e.KeyCode == Keys.Enter) { AddPickToTracker(); e.SuppressKeyPress = true; } };
        bar.Controls.Add(trkPick);
        bar.Controls.Add(Lbl(" ×"));
        trkQty = new NumericUpDown { Width = 46, Minimum = 1, Maximum = 20, Value = 1, Margin = new Padding(0, 5, 3, 3) };
        Tip.SetToolTip(trkQty, "How many of that foe to put on the field at once. Each arrives as its own "
            + "row with its own Blood and its own initiative, numbered so you can tell them apart.");
        bar.Controls.Add(trkQty);
        bar.Controls.Add(Btn("＋ Foe", (s, e) => AddPickToTracker(), 70, "Drop it straight onto the field"));
        bar.Controls.Add(Btn("＋ Add", (s, e) => AddCustomCombatant(), 90, "Add an ad-hoc combatant or NPC by hand"));
        var condItems = BookConditions
            .Select(cd => (cd, (EventHandler)((s, e) => ApplyCondition(cd)))).ToList();
        condItems.Add(("-", null));
        condItems.Add(("— Clear all —", (s, e) => ClearConditions()));
        bar.Controls.Add(MenuBtn("＋ Condition ▾", 130, "Tag the selected combatant with a condition", condItems.ToArray()));

        // Everything past this line throws work away. A wider gap and a different face, so the hand
        // that means "＋ Add" never lands on "Clear field" — they were adjacent and identical before.
        bar.Controls.Add(BarSep(18));
        bar.Controls.Add(DangerBtn("✕ Remove", (s, e) => RemoveSelectedCombatant(), 85, "Remove the selected combatant from the field (or press Delete). A posse soul is asked about first."));
        bar.Controls.Add(DangerBtn("New fight", (s, e) => NewFight(), 90, "Clear the foes, keep the posse, back to Round 1"));
        bar.Controls.Add(DangerBtn("Clear field", (s, e) =>
        {
            if (tracker.Count == 0 && signs.Count == 0) { Nope("The field is already empty."); return; }
            if (!Confirm("Clear the whole battlefield?")) return;
            tracker.Clear(); signs.Clear(); round = 1; ShowRound(); Log("The field is cleared.");
        }, 95, "Wipe everyone — posse and foes — and the sign on the trail, and reset to Round 1"));

        trkGrid = new DataGridView
        {
            Dock = DockStyle.Fill, AutoGenerateColumns = false, DataSource = tracker,
            AllowUserToAddRows = false, RowHeadersVisible = false,
            AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
            SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = false
        };
        StyleGrid(trkGrid);
        trkBold = new Font(trkGrid.Font, FontStyle.Bold);
        // Columns carry their property name as their Name too, so everything downstream — the bar
        // painter, the tooltips, the button column — asks for a column by what it MEANS rather
        // than by an index that shifts the moment a column is inserted.
        // An editable column says so twice: ✎ in the header, and a cell lifted toward paper in the
        // body (see CellFormatting). Nothing in the grid distinguished the four columns you may type
        // in from the six you may not, so the only way to find out was to try.
        void C(string prop, string head, int w, bool ro = false, string tip = null)
            => trkGrid.Columns.Add(new DataGridViewTextBoxColumn
            {
                DataPropertyName = prop, Name = prop, FillWeight = w, ReadOnly = ro,
                HeaderText = ro ? head : head + " ✎",
                ToolTipText = ro ? (tip ?? "")
                    : (string.IsNullOrEmpty(tip) ? "" : tip + "\n\n") + "You can type in this column — click and type, or press F2."
            });
        // Widths allow for the ✎ on the editable ones — "Beats ✎" does not fit the 44 that plain
        // "Beats" did, and a clipped header is worse than no marker at all.
        C("Init", "Init", 58); C("Name", "Name", 152, true); C("BloodCur", "Blood", 68, false,
            "Blood left, drawn as a bar behind the number — full green, hurt gold, near death red. "
            + "On a sign & spoor row it is the spoor clock instead.");
        // Widened from 48 in v1.38.0: this cell is "/ 34" while a body is standing and the DEATH
        // CLOCK once it is not — "dying −3 of 12" needs room that a slash and two figures did not.
        C("BloodMax", "", 100, true,
            "The Blood maximum while they are standing. Once somebody is at 0 it becomes the count "
            + "instead: how far past zero they have bled, and how far it is to their CON — which is "
            + $"where the book says it ends. A Fortitude save or a Medicine check at DC {Rules.StabilizeDc} "
            + "stops the bleeding.");
        C("LastNote", "Last", 74, true,
            "What just happened here — the damage taken, the healing done, the moment they went down. "
            + "Cleared at the top of each round.");
        C("Defense", "Def", 46, true); C("Beats", "Beats", 66, false,
            "Beats left this turn — a Strike costs one. Begin turn puts them back to 3.");
        // The header names the RULE, not just the column. "clean" is the Player's Book's own word
        // (Ch. IX: "Your first Strike in a turn is clean"), but a Keeper reading it cold has no way
        // to know that or what to look up — reported by the user, who asked what it meant.
        C("NextStrike", "Next strike (MAP)", 104, true,
            "The Multiple Attack Penalty — Player's Book Ch. IX. Your first Strike in a turn is "
            + "\"clean\" (no penalty); the second takes −5, the third −10. An Agile weapon softens "
            + "it to −4/−8. Begin turn resets it to clean.");
        C("Conditions", "Conditions", 106);
        C("WorkedChips", "Worked", 114, true,
            "Signs, Miracles and creature powers working on this one — ✦ Sign, ✝ Miracle, ◈ a "
            + "creature's own, with the rounds left. Hover for who worked it and what it does; "
            + "right-click to end one.");
        // Figures right, words left. BloodMax is READ-ONLY here — unlike the Posse tab's, which can
        // be typed into — so it can carry the slash in the cell rather than in the header, and with
        // no rule drawn between them the pair reads as the single field it is: "12 / 12".
        Figures(trkGrid, "Init", "BloodCur", "Defense", "Beats");
        trkGrid.Columns["BloodMax"].DefaultCellStyle.Padding = new Padding(1, 0, 4, 0);
        // far-right Ledger button — posse souls only; creatures keep their double-click
        // stat block and ad-hoc rows have no sheet to show, so neither draws a button
        trkGrid.Columns.Add(QuietButtonCol("Ledger", 60));
        bool TrkHasSheet(int i) => i >= 0 && i < tracker.Count && tracker[i].IsPC
            && string.IsNullOrEmpty(tracker[i].Ref) && SoulOf(tracker[i]) != null;
        trkGrid.CellPainting += (s, e) =>
        {
            if (e.RowIndex < 0 || e.ColumnIndex >= trkGrid.Columns.Count || e.ColumnIndex < 0) return;
            string col = trkGrid.Columns[e.ColumnIndex].Name;
            // e.CellBounds, matching the Blood branch below. PaintBackground's first argument is a
            // CLIP, not the rectangle it fills — it always fills the cell — so the two forms paint
            // identically and the pair being written differently only invited the reading that one
            // of them smeared across the grid. (Checked by instrumenting both; they do not.)
            if (col == "ledgerBtn" && !TrkHasSheet(e.RowIndex))
            { e.PaintBackground(e.CellBounds, true); e.Handled = true; return; }
            if (col != "BloodCur" || e.RowIndex >= tracker.Count) return;

            // The Blood column is the one number a Keeper reads a dozen times a round, and a bare
            // "17" says nothing about whether 17 is nearly dead. Behind the number goes a bar: how
            // much is left, in a color that says how bad it is.
            var c = tracker[e.RowIndex];
            e.PaintBackground(e.CellBounds, true);
            var bar = e.CellBounds; bar.Inflate(-4, -5);
            if (bar.Width > 6 && bar.Height > 4)
            {
                // Once they are on the ground the Blood bar is an empty box, which is the least
                // urgent thing on the screen at the most urgent moment. The clock takes its place.
                if (c.Dying || (c.Dead && c.DeathAt > 0)) PaintDeathClock(e.Graphics, bar, c.Bleed, c.DeathAt);
                else if (c.BloodMax > 0) PaintBloodBar(e.Graphics, bar, c.BloodCur, c.BloodMax);
            }
            e.PaintContent(e.CellBounds);   // the number rides on top of its own bar
            e.Handled = true;
        };
        trkGrid.CellContentClick += (s, e) =>
        {
            if (e.RowIndex >= 0 && e.ColumnIndex >= 0 && trkGrid.Columns[e.ColumnIndex].Name == "ledgerBtn" && TrkHasSheet(e.RowIndex))
            { if (SoulOf(tracker[e.RowIndex]) is PartyMember p) ShowSoulCard(p); }
        };
        WireNumericValidation(trkGrid, new() { "Init", "BloodCur", "Beats" });
        // The field repaints because the FIELD CHANGED, not because whoever changed it remembered to
        // ask (v1.38.0). Every row's ground is decided from the combatant sitting at that row index,
        // so any reorder leaves each row wearing the last occupant's colour until something repaints
        // it — and the repaint was a `trkGrid.Refresh()` at the end of SortTracker, which is one call
        // site out of several and does nothing at all while the tab is hidden. It is hidden on the
        // commonest route of the lot: Send all -> Tracker is a button on the ENCOUNTER tab.
        // Hanging it on the list itself covers every route that exists and every route added later.
        tracker.ListChanged += (s, e) => trkGrid?.Invalidate();
        trkGrid.CellFormatting += (s, e) =>
        {
            if (e.RowIndex < 0 || e.RowIndex >= tracker.Count) return;
            // The row's OWN item, not the list read at the row's index. The two agree today — the
            // grid is bound straight to the BindingList — so this is hardening rather than a fix,
            // and it is worth having because the whole fault above was a row and an index being
            // treated as the same thing.
            if (trkGrid.Rows[e.RowIndex].DataBoundItem is not Combatant c) return;
            // Down beats acting: a combatant who is bleeding out reads red even on their own turn —
            // and since v1.38.0 there are three kinds of down, which the ground has to tell apart.
            // Dead first: it is the only one of the four that cannot change, so nothing may paint
            // over it. Then dying, which is the one with a clock on it. Then plainly down, which is
            // where a creature stops and where a stabilised soul waits.
            e.CellStyle.BackColor = c.Dead ? DeadRow : c.Dying ? DyingRow : c.Down ? DownRow
                                  : c.Acting ? ActingRow : c.IsPC ? PcRow : FoeRow;
            // A cell you can type in stands on lighter ground than one you cannot — applied after
            // the row colour so it lifts whatever that row happens to be wearing.
            if (!trkGrid.Columns[e.ColumnIndex].ReadOnly) e.CellStyle.BackColor = Writable(e.CellStyle.BackColor);
            // The dead read in Slate on ash: still legible, plainly finished, and not competing for
            // the eye with the soul two rows down who has four rounds left. The dying read in Ink,
            // not Blood — Blood on the loud red ground is mud, and this is the row that most has to
            // be readable across a table.
            if (c.Dead) e.CellStyle.ForeColor = Slate;
            else if (c.Dying) e.CellStyle.ForeColor = Ink;
            else if (c.Down) e.CellStyle.ForeColor = Blood;
            else if (c.Acting) e.CellStyle.Font = trkBold;   // cached: CellFormatting runs on every paint
            // Already gone this round: faded, so "who is still to go" is something the Keeper SEES
            // rather than something they hold in their head and lose track of on round four.
            else if (c.HasActed) e.CellStyle.ForeColor = Spent;

            string col = trkGrid.Columns[e.ColumnIndex].Name;
            // The "Last" cell is the whole point of the column: it has to be readable as harm or
            // mending from across the table, without stopping to read the sign of the number.
            if (col == "LastNote" && c.LastDelta != 0)
            {
                e.CellStyle.ForeColor = c.LastDelta < 0 ? Blood : Verdigris;
                e.CellStyle.Font = trkBold;
            }
            // Something worked on you is a fact about the fight, not a status you shrug off — it
            // reads in the ink the app already uses for the uncanny.
            if (col == "WorkedChips" && c.Worked is { Count: > 0 }) e.CellStyle.ForeColor = Verdigris;
            // The other half of "12 / 12". A sign & spoor row has no Blood maximum to show — its
            // Blood cell is a spoor clock, not a number — so it gets no orphaned slash either.
            if (col == "BloodMax")
            {
                // For anyone on the ground the Blood maximum is the one number that no longer helps.
                // "/ 34" beside a zero says what they used to have; "dying −3 of 12" says how many
                // rounds are left to do something about it. The column stops being the other half of
                // "12 / 12" and becomes the death clock, which is what a Keeper is actually reading
                // that row for. Bold, because it is the most time-critical thing on the screen.
                bool clock = c.DyingLine.Length > 0;
                e.Value = clock ? c.DyingLine : !c.IsSign && c.BloodMax > 0 ? "/ " + c.BloodMax : "";
                e.CellStyle.ForeColor = c.Dead ? Slate : c.Dying ? Ink : c.Down ? Blood
                                      : c.HasActed ? Spent : Faint;
                if (c.Dying) e.CellStyle.Font = trkBold;
                e.FormattingApplied = true;
            }
        };
        // The chips are deliberately terse, so the whole of each effect — who worked it, what it
        // cost, what it does, when it ends — lives one hover away rather than in a wider column.
        trkGrid.CellToolTipTextNeeded += (s, e) =>
        {
            if (e.RowIndex < 0 || e.RowIndex >= tracker.Count || e.ColumnIndex < 0) return;
            var c = tracker[e.RowIndex];
            string col = trkGrid.Columns[e.ColumnIndex].Name;
            if (col == "WorkedChips")
            {
                if (c.Worked is { Count: > 0 })
                    e.ToolTipText = string.Join("\n\n──────────\n\n", c.Worked.Select(w => w.Full));
                return;
            }
            // What the conditions on this row actually cost, worked out rather than recited. The
            // column has listed Appendix B's words since v1.4 and the arithmetic behind them was
            // the Keeper's to carry: "Frightened 2, Off-Guard" is −2 on everything AND −2 more
            // Defense on top, and nobody does that sum reliably in the middle of a fight.
            if (col == "Conditions" || col == "Defense")
            {
                var load = c.Load;
                if (!load.Anything)
                {
                    e.ToolTipText = col == "Defense"
                        ? "Defense — 10 + DEX + armor worn + cover. Nothing is riding on this one, so "
                          + "this is the number a Strike is rolled against."
                        : "Conditions off Appendix B. Add them from ＋ Condition ▾, or type your own. "
                          + "The ones the book gives numbers to are counted against Strikes and Defense "
                          + "automatically.";
                    return;
                }
                e.ToolTipText =
                    (load.Any ? $"What this costs them: {load.Line}\n" : "")
                  + (load.Defense != 0 ? $"Defense {c.Defense} → {c.EffectiveDefense}\n" : "")
                  + (load.BeatsLost > 0 ? $"Beats this turn: {c.BeatsThisTurn} of 3\n" : "")
                  + (load.Note.Length > 0 ? "\n" + load.Note : "")
                  + "\n\nThe Strike engine applies all of this by itself — it is not yours to remember.";
            }
        };
        trkGrid.CellEndEdit += (s, e) =>
        {
            // Guard the row index. An edit can still be open when the list underneath is rebuilt —
            // Undo and Redo are form-level shortcuts that work mid-edit, and Load session and New
            // fight both empty the tracker — and WinForms then ends the edit against a row that is
            // gone. The Posse grid has always had this guard; this one did not, so the throw took
            // the whole app down in the middle of a fight, which is the worst possible moment.
            if (e.RowIndex < 0 || e.RowIndex >= tracker.Count) return;
            var c = tracker[e.RowIndex];
            if (c.BloodMax > 0 && c.BloodCur > c.BloodMax) c.BloodCur = c.BloodMax;
            // SoulOf, not a match on Name. The mirror is keyed to the soul's stable id precisely so
            // it survives a rename (see SoulOf); this site still matched by name, so typing Blood
            // straight into the grid quietly stopped reaching a renamed soul while the Damage button
            // beside it went on working — the two disagreed and neither said so.
            if (SoulOf(c) is PartyMember p) { p.BloodCur = c.BloodCur; posseGrid?.Refresh(); }
            trkGrid.Refresh();
            // Typing a new initiative moves that combatant in the order, so it has to move in the
            // grid too. Without this the Keeper corrected a number, watched the row stay put, and
            // then Next turn went somewhere the field did not show. Deferred to BeginInvoke so the
            // grid is out of its edit cycle before the list underneath it is rebuilt.
            if (e.ColumnIndex >= 0 && e.ColumnIndex < trkGrid.Columns.Count
                && trkGrid.Columns[e.ColumnIndex].Name == "Init" && tracker.Any(t => t.Init != 0)
                && !IsDisposed && IsHandleCreated)
                BeginInvoke(new Action(() => { if (!IsDisposed) SortTracker(TrkSort.InitDesc); }));
        };
        trkGrid.KeyDown += (s, e) =>
        {
            if (e.KeyCode != Keys.Delete || trkGrid.IsCurrentCellInEditMode) return;
            e.Handled = true;
            // Delete on the Conditions cell CLEARS the cell, which is what a grid does everywhere
            // else in Windows. It used to take the whole combatant off the field instead — and rows
            // are full-select here, so nothing on screen distinguished the cell being deleted from
            // the row being deleted. Reaching to wipe a stale "Frightened 2" cost you the foe.
            if (trkGrid.CurrentCell?.OwningColumn?.Name == "Conditions"
                && trkGrid.CurrentRow?.DataBoundItem is Combatant cc
                && !string.IsNullOrWhiteSpace(cc.Conditions))
            { cc.Conditions = ""; trkGrid.Refresh(); Log($"{cc.Name}: conditions cleared."); return; }
            RemoveSelectedCombatant();
        };
        // double-click opens the combatant's card: foes get their Bestiary stat block,
        // posse members get their Ledger — the same windows the source tabs open
        trkGrid.CellDoubleClick += (s, e) =>
        {
            if (e.RowIndex < 0 || e.RowIndex >= tracker.Count) return;
            var t = tracker[e.RowIndex];
            if (!string.IsNullOrEmpty(t.Ref))
            { var c = Db.Find(t.Ref); if (c != null) ShowCreatureCard(c); }
            // SoulOf, for the same reason as the Blood mirror above: a name match left a renamed
            // soul's row opening nothing at all on a double-click, with no error to explain it.
            else if (SoulOf(t) is PartyMember p) ShowSoulCard(p);
        };

        Tip.SetToolTip(trkGrid, "Double-click a combatant for their card — right-click for everything that can be done to them");

        // The bar's actions, on the combatant itself. What's offered depends on who the row is:
        // only a soul takes a Dread Check or has a Ledger, and only a creature has a stat block.
        GridMenu<Combatant>(trkGrid, (menu, c) =>
        {
            MIHead(menu, c.Name is { Length: > 0 } ? c.Name : "This combatant");
            MI(menu, "Begin their turn — 3 Beats, a clean MAP", () => BeginTurnForSelected());
            // The Beats ride in the label rather than greying the line, so the Keeper learns the turn
            // is spent from the menu instead of from a dialog that refuses once it is open.
            MI(menu, c.Beats > 0 ? $"Strike…  ({c.Beats} Beat{(c.Beats == 1 ? "" : "s")} left)"
                                 : "Strike…  — no Beats left this turn", () => StrikeDialog(), !c.Down);
            if (c.IsPC) MI(menu, "Dread check…", () => DreadDialog());
            MISep(menu);
            MI(menu, $"Damage {trkAmount.Value}", () => AdjustCombatant(-1));
            MI(menu, $"Heal {trkAmount.Value}", () => AdjustCombatant(+1), c.BloodMax == 0 || c.BloodCur < c.BloodMax);
            MI(menu, "Restore to full Blood", () => RestoreSelected(), c.BloodMax > 0 && c.BloodCur < c.BloodMax);
            // The two things the book offers a body on the ground, offered where a Keeper's hand
            // already is — on the row itself, at the moment it matters. They appear only for the row
            // they can act on, because a menu that offers a stabilize check on a standing soul is a
            // menu that has to be read rather than glanced at.
            if (c.Dying)
            {
                MISep(menu);
                MI(menu, $"Stop the bleeding…  (DC {Rules.StabilizeDc}, {c.RoundsToDeath} round"
                       + $"{(c.RoundsToDeath == 1 ? "" : "s")} left)", () => StabilizeDialog());
                if (SoulOf(c) is PartyMember gr && !c.Upright)
                    MI(menu, gr.Grit > 0 ? $"Refuse to fall — spend 1 Grit ({gr.Grit} left)"
                                         : "Refuse to fall — no Grit left",
                       () => CheckFalling(c, false, false), gr.Grit > 0);
            }
            // The Keeper's override, named and deliberate. The app holds the book's line — dead is
            // dead, and no heal walks it back — and this is the one door through it, because the
            // table outranks the app and a rule with no override is a rule that gets fought.
            else if (c.Dead)
            {
                MISep(menu);
                MI(menu, "They were not dead after all…", () => Resurrect(c));
            }

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

            // What is working on them, and the way to end it. The whole of each effect hangs off
            // its own item as a tooltip, so ending the right one never means guessing from a chip.
            MI(menu, "Work a Sign or Miracle…", () => WorkPowerDialog(c));
            if (c.Worked is { Count: > 0 })
            {
                var wk = new ToolStripMenuItem($"Working on them ({c.Worked.Count})");
                foreach (var w in c.Worked.ToList())
                {
                    var effect = w;   // captured per item, not per loop
                    var item = new ToolStripMenuItem(Amp($"End {effect.Chip}")) { ToolTipText = effect.Full };
                    item.Click += (s, e) =>
                    {
                        c.Unwork(effect); trkGrid.Refresh();
                        Log($"{effect.Name} is ended on {c.Name}.");
                    };
                    wk.DropDownItems.Add(item);
                }
                wk.DropDownItems.Add(new ToolStripSeparator());
                wk.DropDownItems.Add("End all of them", null, (s, e) =>
                {
                    int n = c.Worked.Count;
                    foreach (var w in c.Worked.ToList()) c.Unwork(w);
                    trkGrid.Refresh(); Log($"Everything working on {c.Name} ends — {n} in all.");
                });
                menu.Items.Add(wk);
            }

            MISep(menu);
            if (!string.IsNullOrEmpty(c.Ref)) MI(menu, "Open the stat block", () => { if (Db.Find(c.Ref) is Creature b) ShowCreatureCard(b); });
            else if (c.IsPC && SoulOf(c) is PartyMember soul) MI(menu, "Open the Ledger", () => ShowSoulCard(soul));
            MI(menu, "Take them off the field", () => RemoveSelectedCombatant());
        });

        // Docking is resolved last-added-first, so the sign strip goes on AFTER the grid and
        // BEFORE the bar: the bar takes the top, threads take the band under it, the grid the rest.
        signPanel = new FlowLayoutPanel
        {
            Dock = DockStyle.Top, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink,
            FlowDirection = FlowDirection.LeftToRight, WrapContents = true, Visible = false,
            Padding = new Padding(8, 6, 8, 8), BackColor = SignRow
        };
        // The bar and the glass, side by side: the flow keeps the left and takes all the width it
        // wants, the glass column hangs off the right edge and stretches to whatever height the bar
        // ends up. A TableLayoutPanel rather than Dock=Right on a panel, because a docked Fill child
        // contributes nothing to a container's AutoSize and the bar's height is exactly what has to
        // travel outward here — the row measures the bar, and the glass is told that height.
        var head = new TableLayoutPanel
        {
            Dock = DockStyle.Top, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink,
            ColumnCount = 2, RowCount = 1, Margin = new Padding(0), Padding = new Padding(0),
            BackColor = Color.FromArgb(243, 237, 221)
        };
        head.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100f));
        head.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        head.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        bar.Dock = DockStyle.Fill;
        head.Controls.Add(bar, 0, 0);
        head.Controls.Add(BuildTurnGlass(), 1, 0);

        page.Controls.Add(trkGrid);
        page.Controls.Add(signPanel);
        page.Controls.Add(head);
        RefreshSigns();

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
        var win = new Sheet
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

    /// <summary>Take the selected combatant off the field. One method rather than three lambdas,
    /// because the bar's ✕ Remove, the Delete key and the right-click line all mean the same thing
    /// and had each written it out separately — which is how the Delete key came to skip the
    /// question the others should have been asking too.</summary>
    void RemoveSelectedCombatant()
    {
        if (trkGrid?.CurrentRow?.DataBoundItem is not Combatant c) { Nope("Select a combatant first."); return; }
        // A foe coming off the field is the routine end of a fight and is not worth a dialog. A
        // posse soul is not routine — it is one keystroke from the arrow that got you to the row,
        // and the soul's whole turn state goes with it. The Posse tab has always asked before
        // removing a soul; the tracker never did.
        if (c.IsPC && !Confirm($"Take {c.Name} off the field? Their Posse sheet is untouched.")) return;
        tracker.Remove(c);
    }

    /// <summary>The initiative a combatant walks in on. Zero while nobody has rolled — the tracker's
    /// own word for "not in the order yet" — but once the field HAS rolled, a new arrival rolls with
    /// it. Landing every mid-fight arrival at 0 put it at the bottom of an order everyone else had a
    /// d20 for, so the thing that just kicked the door in went last, every single time.</summary>
    internal int ArrivalInit(CharacterSheet sheet = null)
        => tracker.Any(t => t.Init != 0) ? Rules.RollInitiative(CharGen.InitiativeBonus(sheet)) : 0;

    /// <summary>Put an arrival on the field, in its place in the order rather than at the bottom of
    /// the grid. <see cref="ArrivalInit"/> has rolled it a real initiative whenever the field has
    /// rolled at all — and then appending it left the thing that just kicked the door in sitting
    /// under everyone, while Next turn handed it the turn from halfway up. The grid said one order
    /// and the fight ran another, which is the same fault as the tiebreak one and looked identical
    /// from the Keeper's chair.
    ///
    /// <para>Before anybody has rolled, every Init is 0 and the list is whatever order the Keeper
    /// built by hand. That is theirs, so it is left alone.</para></summary>
    void AddToField(Combatant c)
    {
        bool ordered = tracker.Any(t => t.Init != 0);
        tracker.Add(c);
        if (ordered && c.Init != 0) SortTracker(TrkSort.InitDesc);
    }

    void RollInitiative()
    {
        // Rolling initiative is the top of a fight: the order is fresh, so nobody has gone yet.
        // This method predates HasActed, so without the reset the "spent" greying and the acting
        // row carried over from the last fight into the new order — the field showed souls as
        // already done on a round that had not started.
        //
        // And it is a NOTICE check (Player's Book Ch. XI), which this rolled as a bare d20 for
        // eleven releases while the app's own Reference deck printed the rule two tabs away. A soul
        // with a sheet now brings their Notice bonus; a creature or a hand-entered NPC has none in
        // its stat block, so it keeps the plain die rather than being handed an invented number.
        int scouted = 0;
        foreach (var c in tracker)
        {
            int bonus = CharGen.InitiativeBonus(SoulOf(c)?.Sheet);
            if (bonus != 0) scouted++;
            c.Init = Rules.RollInitiative(bonus);
            c.Acting = false; c.HasActed = false;
        }
        SortTracker(TrkSort.InitDesc);
        UpdateTurnLine();
        Log(scouted == 0
            ? "Initiative rolled for the field."
            : $"Initiative rolled for the field — a Notice check, with {scouted} soul(s) adding their own bonus.");
    }

    /// <summary>Put the round on the bar without the spinner treating it as the Keeper's own edit.
    /// Everything that moves the round goes through here, so the number and the box never disagree.
    /// </summary>
    void ShowRound()
    {
        round = Math.Max(1, round);
        if (roundBox == null) return;
        roundBusy = true;
        roundBox.Value = Math.Clamp(round, roundBox.Minimum, roundBox.Maximum);
        roundBusy = false;
    }

    /// <summary>Hand the turn to whoever is up next, and let the round look after itself. When the
    /// field has all gone, this rolls the round over and starts the next one on its first
    /// combatant — so a Keeper running a fight presses one thing, over and over, and never has to
    /// remember to advance a counter. Ctrl+Space, and the primary button on the bar.</summary>
    void NextTurn()
    {
        if (tracker.Count == 0) { Nope("Nobody on the field."); return; }
        if (Rules.NextUp(tracker) == null)
        {
            // "Down" is no longer the end of it: a soul refusing to fall is at 0 Blood and still
            // taking turns, and the dead are down for good. Ask the same question CanAct asks.
            if (!tracker.Any(t => !t.IsSign && !t.Dead && (!t.Down || t.Upright)))
            { Nope("Everyone on the field is down — the fight is over."); return; }
            NextRound();                       // clears HasActed, so NextUp answers again below
        }
        var up = Rules.NextUp(tracker);
        // Nobody can act even after the round rolled over. A field of nothing but sign & spoor rows
        // gets here — a trace is not down, so the check above lets it through, and it takes no turn.
        if (up == null) { Nope("Nobody on the field can take a turn — sign on the trail is read, not fought."); return; }
        foreach (var t in tracker) t.Acting = false;
        up.BeginTurn();
        // Follow the turn with the selection, so Strike, Dread and Work all act on the one who is up
        // without the Keeper hunting for their row first.
        var row = trkGrid?.Rows.Cast<DataGridViewRow>().FirstOrDefault(r => ReferenceEquals(r.DataBoundItem, up));
        if (row != null) { trkGrid.ClearSelection(); row.Selected = true; trkGrid.CurrentCell = row.Cells[1]; }
        RefreshTracker();
        // The daybook's founding complaint is "the tracker lost somebody", so the turn handoff is
        // exactly the kind of thing it exists to have written down: who went, on what initiative,
        // and who was still to go when they did.
        Daybook.Note("turn", $"round {round}: {up.Name} (init {up.Init}) — still to go: "
            + (string.Join(", ", Rules.InTurnOrder(tracker.Where(Rules.CanAct)).Select(c => c.Name)) is { Length: > 0 } rest ? rest : "nobody"));
        Log($"{up.Name}'s turn — 3 Beats, a clean shot.");
    }

    void NextRound()
    {
        round++;
        ShowRound();
        // A new round means nobody has been handed the turn yet — the gold row would otherwise
        // sit on last round's combatant and read as though they were still up. The "Last" notes go
        // with it: they answer "what just happened", and at the top of a round nothing has.
        // Worked effects lose a round here too, and anything that runs out says so by name — an
        // effect that vanished off a chip without a word is one the table keeps playing anyway.
        foreach (var (on, done) in Rules.NewRound(tracker))
            Log($"{done.Name} ends on {on.Name} — {done.Kind.ToLowerInvariant()} worked by {done.Source}.");
        // A Blood a round off everyone on the ground, and the Grit that kept somebody standing runs
        // out. Every one of these is said by name: a soul who dies inside a column of numbers is
        // exactly the failure the daybook was built for, and a death nobody announced is a death the
        // table plays straight past.
        foreach (var (who, bleed, died, fell) in Rules.BleedOut(tracker))
        {
            if (fell) Log($"{who.Name}'s Grit runs out — they go down.");
            if (died)
            {
                Log($"{who.Name} bleeds out at −{bleed}. Dead, and out here dead is dead.");
                Daybook.Note("death", $"round {round}: {who.Name} died at −{bleed} of {who.DeathAt}");
                if (SoulOf(who) is PartyMember lost)
                    Nope($"{lost.Name} has bled out.\n\nThey reached −{bleed}, which is their CON, and the "
                       + "book is plain about what that means: out here dead is dead.\n\nGive the death its "
                       + "weight — a last word, a turn of silence — before the next scene rides in.");
            }
            else if (who.Dying)
                Log($"{who.Name} is bleeding — −{bleed} of {who.DeathAt}, "
                    + $"{who.RoundsToDeath} round{(who.RoundsToDeath == 1 ? "" : "s")} left. "
                    + $"A Fortitude or Medicine check at DC {Rules.StabilizeDc} stops it.");
        }
        Daybook.Note("turn", $"round {round} begins — {string.Join(", ", Rules.InTurnOrder(tracker).Select(c => $"{c.Name} {c.Init}"))}");
        RefreshTracker();
        TurnOverTheGlass();               // a new round is a new posse turn — see the hourglass block
        Log($"— Round {round} —");
    }

    // the conditions from Appendix B, in the order the book lists them (Frightened and
    // Slowed carry a value, so their common steps are offered explicitly)
    static readonly string[] BookConditions =
    {
        "Bleeding", "Blinded", "Clumsy", "Drained", "Dying", "Fatigued",
        "Frightened 1", "Frightened 2", "Frightened 3", "Grabbed", "Off-Guard",
        "Prone", "Sickened", "Slowed 1", "Slowed 2", "Stunned", "Marked"
    };

    void SortTracker(TrkSort mode)
    {
        try { trkGrid?.EndEdit(); } catch { }      // commit a half-typed Init before reading it
        // Remember WHO the Keeper had selected — clearing the list below resets the grid's
        // current row to the top, and every action that reads CurrentRow (Strike, Dread,
        // Damage) would then silently act on whoever the sort floated to row 0 instead of the
        // combatant the Keeper picked. Restore the same combatant after the reorder.
        var keep = trkGrid?.CurrentRow?.DataBoundItem as Combatant;
        var sorted = (mode switch
        {
            // Init order comes from Rules.InTurnOrder and nowhere else — it is the same sequence
            // Next turn hands the turn out in, so the grid cannot disagree with the fight. Ascending
            // is that order read backwards, which keeps the tiebreaks consistent between the two.
            TrkSort.InitDesc  => Rules.InTurnOrder(tracker),
            TrkSort.InitAsc   => Rules.InTurnOrder(tracker).Reverse(),
            TrkSort.NameAsc   => tracker.OrderBy(c => c.Name),
            TrkSort.NameDesc  => tracker.OrderByDescending(c => c.Name),
            TrkSort.BloodDesc => tracker.OrderByDescending(c => c.BloodCur).ThenBy(c => c.Name),
            TrkSort.BloodAsc  => tracker.OrderBy(c => c.BloodCur).ThenBy(c => c.Name),
            _                 => Rules.InTurnOrder(tracker),
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
        using var f = new Sheet { Width = 350, Height = 258, Text = "Add combatant", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper };
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
            // A hand-entered soul has no sheet and so no CON to read; the rule still governs them,
            // at the middle of the scale, and the Keeper can say otherwise. An ad-hoc NPC or foe
            // gets 0 and is simply put down at zero Blood, as every creature is.
            AddToField(new Combatant
            {
                Name = name.Text.Trim(), BloodCur = b, BloodMax = b, Defense = (int)def.Value,
                IsPC = pc.Checked, Init = ArrivalInit(),
                DeathAt = pc.Checked ? Rules.DefaultDeathAt : 0
            });
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
        // ?. because a Posse-tab Dread Check can hang a Frightened on a soul whose row is in the
        // tracker list while the Tracker TAB has never been opened — the tabs fill themselves on
        // first visit, so the grid can legitimately not exist yet.
        trkGrid?.Refresh();
        Log($"{c.Name}: {cond}.");
    }

    /// <summary>Ask the Keeper for the die they just rolled — the dice-and-books table's half of a
    /// roll the engine would otherwise make for them. Returns null when the engine is doing the
    /// rolling, so a caller can pass the result straight through as the "forced die".</summary>
    int? AskDie(string prompt)
    {
        if (EngineRolls) return null;
        using var f = new Sheet
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
        // Esc closes it the same way the title bar's ✕ already did — by taking the number that is
        // showing. There is no cancelling this one: the caller is mid-resolution and needs a die
        // either way, and a modal that ignores Esc reads as a hung window, not as a firm question.
        f.AcceptButton = ok; f.CancelButton = ok;
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
        int working = tracker.Sum(c => c.Worked.Count);
        int marked = tracker.Count(Rules.FightResidue);
        // An encounter is not just the foes standing in it. The signs on the trail are the spoor of
        // the fight now ending, and what the fight left ON the survivors — conditions, spent Beats,
        // a turn half taken, every Sign and Miracle still riding — belongs to it too. Until v1.24.2
        // only the foes were cleared, so on a field of signs alone the button appeared to do nothing
        // at all. The guard then undercounted a second time: it asked about foes, signs and worked
        // effects while the reset below clears six more things, so with the last foe already taken
        // off by hand it said "nothing to clear" over a posse still Frightened and out of Beats.
        // Both halves now ask Rules.FightResidue, which is the reset's own inventory.
        if (foes.Count == 0 && signs.Count == 0 && marked == 0 && round == 1)
        { Nope("Nothing to clear — no foes, no sign on the trail, and the posse is already fresh for Round 1."); return; }

        var bits = new List<string>();
        if (foes.Count > 0) bits.Add($"{foes.Count} foe(s)");
        if (signs.Count > 0) bits.Add($"{signs.Count} sign(s) on the trail");
        if (working > 0) bits.Add($"{working} effect(s) still working");
        // Everything else the reset touches, counted as souls rather than as a list of six fields —
        // "3 still carrying the last fight" is what a Keeper needs to agree to.
        int carrying = tracker.Count(c => Rules.FightResidue(c) && c.Worked.Count == 0);
        if (carrying > 0) bits.Add($"{carrying} still carrying the last fight");
        if (bits.Count == 0) bits.Add($"the round back to 1 from {round}");
        if (!Confirm($"New fight? Clears {string.Join(", ", bits)}, keeps the posse, resets to Round 1.")) return;

        foreach (var f in foes) tracker.Remove(f);
        signs.Clear();
        // a fresh fight: nothing carried over — no conditions, no spent Beats, nobody mid-turn,
        // and nothing still working from the last one (Rules.ResetForNewFight, so it is testable)
        Rules.ResetForNewFight(tracker);
        round = 1; ShowRound(); RefreshTracker();
        Log("New fight — foes cleared, the trail wiped, the posse holds the field, Round 1.");
    }

    /// <summary>The name a trace goes on the field under. "Sign of the Wendigo" rather than "Sign of
    /// The Wendigo" — the article belongs to the sentence now, not to the heading it came from.</summary>
    internal static string SignName(string creatureName)
    {
        string n = creatureName ?? "";
        if (n.StartsWith("The ", StringComparison.Ordinal)) n = "the " + n.Substring(4);
        return "Sign of " + n;
    }

    /// <summary>Put a creature's TRACE on the trail instead of the creature (the safe-table rule).
    /// One thread, however many were asked for: a thing two Tiers over the posse is one thread, and
    /// four copies of a thread is not a thing a table can run. It goes to <see cref="signs"/>, not
    /// to the field — it takes no initiative and no turn.</summary>
    void AddSign(Creature c)
    {
        string name = SignName(c.name);
        if (signs.Any(t => string.Equals(t.Ref, c.name, StringComparison.OrdinalIgnoreCase)))
        { Nope($"{name} is already on the trail — read it again to fill another segment."); return; }
        var (readDc, dreadDc, what) = Rules.SpoorFor(c.tier);
        signs.Add(new Combatant
        {
            Name = name, Ref = c.name, IsSign = true,
            BloodCur = 0, BloodMax = 0, Defense = 0, Beats = 0,
            Conditions = what
        });
        Log($"{name} — the trace, not the thing. Survival DC {readDc} to read it"
            + (dreadDc == 0 ? ", and it costs no Nerve" : $", Dread DC {dreadDc}")
            + $". A {Rules.SpoorClockSegments}-segment clock; a full one is the night it comes in the flesh.");
    }

    // ---- the sign strip: what is out there, above the field, where nothing takes a turn ----

    /// <summary>Rebuild the sign strip from <see cref="signs"/>. Hidden outright when the trail
    /// is clear, so a table that never meets the safe-table rule never sees a band of empty chrome.
    /// Everything the rule needs a Keeper to know is spelled out here in words — the clock says
    /// "2 of 4" and not just four boxes, because four boxes taught nobody anything.</summary>
    void RefreshSigns()
    {
        if (signPanel == null) return;
        signPanel.SuspendLayout();
        foreach (Control old in signPanel.Controls.Cast<Control>().ToList()) { signPanel.Controls.Remove(old); old.Dispose(); }

        if (signs.Count == 0) { signPanel.Visible = false; signPanel.ResumeLayout(); return; }

        var head = new Label
        {
            Text = "SIGN ON THE TRAIL — too far over the posse to meet in the flesh. Read them; they take no turn.",
            AutoSize = false, Width = 980, Height = 18, ForeColor = Blood,
            Font = new Font("Segoe UI", 8.25f, FontStyle.Bold), Margin = new Padding(2, 0, 0, 4)
        };
        signPanel.Controls.Add(head);
        signPanel.SetFlowBreak(head, true);
        foreach (var sign in signs.ToList()) signPanel.Controls.Add(SignCard(sign));

        signPanel.Visible = true;
        signPanel.ResumeLayout();
    }

    /// <summary>One thread, said plainly: what it is, how near it is, what is on the ground, what
    /// reading it costs, and the button that reads it. A Keeper should be able to run the whole
    /// rule off this card without having read the appendix.</summary>
    Control SignCard(Combatant sign)
    {
        var beast = Db.Find(sign.Ref);
        int tier = beast?.tier ?? 1;
        var (readDc, dreadDc, what) = Rules.SpoorFor(tier);
        const int CW = 452;

        var card = new Panel { Width = CW, BackColor = Paper, Margin = new Padding(2, 0, 8, 6), Padding = new Padding(10, 8, 10, 8) };
        card.Paint += (s, e) =>
        {
            using var pen = new Pen(BarEdge, 1f);
            e.Graphics.DrawRectangle(pen, 0, 0, card.Width - 1, card.Height - 1);
        };

        var name = new Label
        {
            Left = 10, Top = 8, Width = CW - 150, Height = 20, Text = sign.Name, UseMnemonic = false,
            Font = new Font("Segoe UI", 10f, FontStyle.Bold | FontStyle.Italic), ForeColor = Blood, AutoEllipsis = true
        };

        // The clock, drawn AND named. "2 of 4" is the part that makes the boxes mean something.
        var clock = new Panel { Left = CW - 136, Top = 8, Width = 126, Height = 20, BackColor = Paper };
        clock.Paint += (s, e) =>
        {
            PaintSpoorClock(e.Graphics, new Rectangle(0, 3, 58, 14), sign.SignFilled);
            TextRenderer.DrawText(e.Graphics, $"{sign.SignFilled} of {Rules.SpoorClockSegments}",
                clock.Font, new Rectangle(64, 0, 62, 20), Ink,
                TextFormatFlags.Left | TextFormatFlags.VerticalCenter);
        };
        Tip.SetToolTip(clock, $"The spoor clock. Every reading of this thing's trail fills one segment; "
            + $"at {Rules.SpoorClockSegments} of {Rules.SpoorClockSegments} it stops leaving sign and comes in the flesh.");

        var ground = new Label
        {
            Left = 10, Top = name.Bottom + 4, Width = CW - 20, Text = what, ForeColor = Ink, Font = DialogItalic,
            Height = TextRenderer.MeasureText(what, DialogItalic, new Size(CW - 20, 0), TextFormatFlags.WordBreak).Height + 2
        };

        // A thread whose creature no longer resolves falls back to Tier I — the GENTLEST row there
        // is. Left unsaid that reads as a real reading, so it says so: a re-extraction that renames
        // a creature can orphan a thread saved under the old name.
        string cost = beast == null
            ? $"“{sign.Ref}” is not in the Bestiary — showing Tier I"
            : $"Tier {Rules.Roman(tier)}  ·  Survival DC {readDc}  ·  " + (dreadDc == 0 ? "no Dread" : $"Dread DC {dreadDc}");
        var dcs = new Label
        {
            Left = 10, Top = ground.Bottom + 6, Width = CW - 130, Height = 20, Text = cost,
            ForeColor = beast == null ? Gold : Ink, Font = beast == null ? DialogItalic : Font, AutoEllipsis = true
        };

        var read = new Button { Text = "Read it ▸", Left = CW - 118, Top = ground.Bottom + 2, Width = 108, Height = 27 };
        read.Click += (s, e) => ReadSignDialog(sign);
        Tip.SetToolTip(read, "A Survival check at this Tier's DC, the Dread it costs the reader, and one more "
            + "segment of the clock");

        card.Controls.AddRange(new Control[] { name, clock, ground, dcs, read });
        card.Height = read.Bottom + 8;

        // Right-click for the things a Keeper needs occasionally and shouldn't have a button for.
        var menu = new ContextMenuStrip();
        MIHead(menu, sign.Name);
        MI(menu, "Read it… — Survival, Dread, and a segment of the clock", () => ReadSignDialog(sign));
        if (beast != null) MI(menu, $"Open {beast.name}'s stat block", () => ShowCreatureCard(beast));
        MISep(menu);
        MI(menu, $"Fill a segment by hand ({sign.SignFilled} of {Rules.SpoorClockSegments})",
            () => { sign.SignFilled += 1; AfterClockMoved(sign, beast); }, !sign.SignFull);
        MI(menu, "Rub out a segment", () => { sign.SignFilled -= 1; AfterClockMoved(sign, beast); }, sign.SignFilled > 0);
        MI(menu, "It comes in the flesh now", () => SignArrives(sign, beast));
        MISep(menu);
        MI(menu, "Lose the trail — take it off", () => signs.Remove(sign));
        foreach (Control child in card.Controls) if (child is not Button) child.ContextMenuStrip = menu;
        card.ContextMenuStrip = menu;
        return card;
    }

    /// <summary>The clock moved by hand: say where it stands, redraw the strip, and honour a clock
    /// that has just filled exactly as a read one does.</summary>
    void AfterClockMoved(Combatant sign, Creature beast)
    {
        Log($"{sign.Name}: the clock stands at {sign.SignFilled} of {Rules.SpoorClockSegments}.");
        RefreshSigns();
        if (sign.SignFull) SignArrives(sign, beast);
    }

    /// <summary>Ask, once, whether a horror the safe-table rule bars should take the field anyway.
    /// The rule is the Keeper's Book's, not the app's, so this offers rather than refuses — but it
    /// offers the book's answer first, and says what the cost of the other one is.</summary>
    bool AskInTheFlesh(Creature c, int partyLevel)
    {
        using var f = new Sheet
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
        int over = c.tier - Rules.PartyTier(partyLevel);
        var head = Para($"{c.name} is Tier {Rules.Roman(c.tier)} — {over} Tiers over a posse of level "
                      + $"{partyLevel}. The book does not put it in front of them yet.", Pad, DialogBold, Blood);

        // Both outcomes named by WHERE they put the thing, because that is the part a Keeper is
        // actually choosing between and the part the old wording left them to infer.
        var optA = Para("ON THE TRAIL  (what the book does)", head.Bottom + 12, DialogBold, Ink);
        var bodyA = Para($"It goes on the sign strip above the field — nothing to shoot, nothing that takes a "
                       + $"turn. On the ground: {what.ToLowerInvariant()}. Reading it is a Survival check at DC "
                       + $"{readDc}" + (dreadDc == 0 ? " and costs no Nerve" : $", and costs the reader a Dread Check at DC {dreadDc}")
                       + $". Each reading fills 1 of {Rules.SpoorClockSegments} segments; a full clock is the night "
                       + "it comes anyway.", optA.Bottom + 2, f.Font, Ink);

        var optB = Para("ON THE FIELD  (overrule the rule)", bodyA.Bottom + 10, DialogBold, Ink);
        var bodyB = Para($"It joins the initiative order now, at {c.BloodValue} Blood and Defense {c.DefenseValue}. "
                       + $"Against a posse of level {partyLevel}, that is very likely a funeral.", optB.Bottom + 2, DialogItalic, Gold);

        var asSign = new Button { Text = "Put it on the trail", Left = Pad, Top = bodyB.Bottom + 14, Width = 158, Height = 32, DialogResult = DialogResult.Yes };
        var flesh  = new Button { Text = "Put it on the field", Left = Pad + 166, Top = asSign.Top, Width = 152, Height = 32, DialogResult = DialogResult.No };
        var cancel = new Button { Text = "Cancel", Left = Pad + CW - 92, Top = asSign.Top, Width = 92, Height = 32, DialogResult = DialogResult.Cancel };
        f.Controls.AddRange(new Control[] { head, optA, bodyA, optB, bodyB, asSign, flesh, cancel });
        f.ClientSize = new Size(CW + Pad * 2, asSign.Bottom + Pad);
        f.AcceptButton = asSign; f.CancelButton = cancel;

        var answer = f.ShowDialog(this);
        if (answer == DialogResult.Yes) { AddSign(c); return false; }
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
            AddToField(new Combatant
            {
                Name = bare ? c.name : $"{c.name} #{k}",
                BloodCur = c.BloodValue, BloodMax = c.BloodValue,
                Defense = c.DefenseValue, Ref = c.name, Init = ArrivalInit()
            });
        }
        Log(count == 1
            ? $"Tracker: {c.name} takes the field ({c.BloodValue} Blood)."
            : $"Tracker: {count}× {c.name} take the field ({c.BloodValue} Blood each).");
    }

    void AdjustCombatant(int sign)
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Nope("Select a combatant first."); return; }
        int v = (int)trkAmount.Value;
        int was = c.BloodCur;
        bool wasDown = c.Down, wasDead = c.Dead;
        c.Wound(sign * v);                                     // clamps, and leaves the "Last" note
        Log($"{c.Name} {(sign < 0 ? "takes" : "recovers")} {Math.Abs(c.BloodCur - was)} → {c.BloodCur}/{c.BloodMax}"
            + (c.Dying ? $"  — DYING, −{c.Bleed} of {c.DeathAt}." : c.Down ? "  — PUT DOWN." : ""));
        trkGrid.Refresh();
        if (SoulOf(c) is PartyMember p) { p.BloodCur = c.BloodCur; posseGrid?.Refresh(); }
        CheckFalling(c, wasDown, wasDead);
    }

    /// <summary>Put the selected combatant back to full Blood — the ad-hoc heal a Keeper wants
    /// between scenes without arithmetic. A posse soul gets their Nerve and pool back too, because
    /// for a soul "restored" means the whole of what a long rest restores.</summary>
    void RestoreSelected()
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Nope("Select a combatant first."); return; }
        // Blood does not answer this one. Wound refuses to un-kill (see Combatant.Wound), so without
        // this the button would fill the bar, leave the row dead, and give a Keeper no idea why.
        if (c.Dead)
        {
            Nope($"{c.Name} is dead — out here dead is dead, and Blood is not what is wrong.\n\n"
               + "If the table has decided otherwise, right-click the row: \"They were not dead "
               + "after all\". That is the Keeper's call to make on purpose, not a side effect of "
               + "a heal.");
            return;
        }
        if (SoulOf(c) is PartyMember soul) { RestSoul(soul); c.Wound(c.BloodMax - c.BloodCur, "restored"); }
        else if (c.BloodMax <= 0) { Nope($"{c.Name} has no Blood maximum to restore to — set one in the /Max column."); return; }
        else
        {
            c.Wound(c.BloodMax - c.BloodCur, "restored");
            Log($"{c.Name} is made whole — {c.BloodCur}/{c.BloodMax} Blood.");
        }
        RefreshTracker();
    }

    /// <summary>Everyone on the field back to full Blood, and every posse soul back to full Nerve
    /// with them. The scene is over; this is the line between one and the next.</summary>
    void RestoreField()
    {
        // The dead are not "everyone on the field". A scene-end restore is a mercy for the living;
        // bringing somebody back is a decision, and it has its own item on their row.
        var bodies = tracker.Where(t => t.BloodMax > 0 && !t.Dead).ToList();
        int gone = tracker.Count(t => t.Dead);
        if (bodies.Count == 0)
        {
            Nope(gone > 0 ? $"Nobody left on the field has Blood to restore — {gone} of them are dead."
                          : "Nobody on the field has Blood to restore.");
            return;
        }
        int hurt = bodies.Count(t => t.BloodCur < t.BloodMax);
        if (!Confirm($"Restore everyone on the field? {hurt} of {bodies.Count} are carrying wounds; "
                   + "every posse soul also gets their Nerve and pool back."))
            return;
        foreach (var t in bodies) t.Wound(t.BloodMax - t.BloodCur, "restored");
        foreach (var p in party.Where(p => tracker.Any(t => t.IsSoul(p) && !t.Dead)))
        { p.BloodCur = p.BloodMax; p.NerveCur = p.NerveMax; p.PoolCur = p.PoolMax; }
        posseGrid?.Refresh(); RefreshTracker();
        Log($"The field is restored — {bodies.Count} back to full Blood, the posse's Nerve with them.");
    }

    // The posse soul behind a tracker row, matched by the stable id (Name only as a legacy
    // fallback) — so damage mirrors back to the right soul even after a rename.
    PartyMember SoulOf(Combatant c) => c != null && c.IsPC ? party.FirstOrDefault(c.IsSoul) : null;

    // The selected combatant's turn begins: three Beats, the next Strike clean (Ch. XI).
    void BeginTurnForSelected()
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Nope("Select a combatant first."); return; }
        foreach (var t in tracker) t.Acting = false;   // one at a time; the last turn is over
        c.BeginTurn(); RefreshTracker();
        Log($"{c.Name}'s turn — 3 Beats, a clean shot.");
    }

    // Resolve a Strike from the selected combatant through the Iron Code engine: to hit, the four
    // degrees, the Multiple Attack Penalty at this combatant's current step, the Fatal die on a
    // crit, and the damage after the target's DR — then spend the Beat and apply it.
    void StrikeDialog()
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant attacker) { Nope("Select the attacker first."); return; }
        var foes = tracker.Where(t => !ReferenceEquals(t, attacker)).ToList();
        // The safe-table rule needs no enforcing here any more — a trace is never on the field to
        // be picked as attacker or target. It only needs saying when the field is empty BECAUSE
        // everything out there is a thread.
        if (foes.Count == 0)
        { Nope(signs.Count > 0 ? "Nothing on the field to strike — only sign & spoor, which is read, not shot."
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
        using var f = new Sheet { Text = $"{attacker.Name} strikes", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper };
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

        // Declared before Sync rather than beside the other buttons at the bottom, because Sync is
        // what turns the Strike off once the Beats are gone and a local cannot reach one declared
        // after it. Placed further down, once the prose above them has been measured.
        var ok = new Button { Text = "Strike ▸", Width = 90, DialogResult = DialogResult.OK };
        var cancel = new Button { Text = "Close", Width = 84, DialogResult = DialogResult.Cancel };
        // Why the Strike is refused, on its own full-width line. It cannot ride in mapLbl — that is
        // 320px beside the To-hit box and would ellipsize the sentence to nothing. The line is
        // reserved whether or not it is currently saying anything, because this dialog is re-shown
        // in a loop and the reason appears mid-loop: a block that only exists once the Beats run
        // out would move the buttons out from under the Keeper's hand on the third Strike.
        var refusal = new Label { Left = Pad, Width = CW, ForeColor = Blood, Font = DialogItalic, AutoSize = false };
        // The line that says what this Strike is ACTUALLY rolled at and against, once everything
        // riding on either of them is counted. Without it the engine applies a Frightened 2 and a
        // −2 Defense correctly and the Keeper watches a number they cannot account for come out of
        // it — which reads as the app being wrong even when it is right.
        //
        // Declared up here with the buttons, and for the same reason they are: Sync writes to it,
        // and a local declared after Sync cannot be reached from inside it.
        var against = new Label { Left = Pad, Top = 152, Width = CW, Height = 20, ForeColor = GoldDeep, Font = DialogItalic, AutoEllipsis = true };

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
            // A Strike costs a Beat, and once they are gone the turn is over — so the button that
            // takes one goes grey and the dialog says which of the three reasons it is. It used to
            // stay live and keep resolving: the Beat count stopped at zero, the MAP step went on
            // climbing, and the engine handed out a fourth and fifth Strike the Iron Code does not
            // allow. The whole point of the app keeping the Beats is that it keeps them.
            string why = Rules.WhyNoBeats(attacker);
            ok.Enabled = why == null;
            // Esc and Enter must both still leave. With the commit greyed there is nothing for Enter
            // to do, so it answers with the way out rather than doing nothing at all — and the way
            // out says where it goes, because at that point it is the only thing left to press.
            cancel.Text = why == null ? "Close" : "Back to the field ▸";
            f.AcceptButton = why == null ? ok : cancel;
            refusal.Text = why ?? "";
            mapLbl.Text = $"This Strike: {(map == 0 ? "clean, no MAP" : "MAP " + map)}  ·  "
                + (attacker.Beats > 0
                    ? $"{attacker.Beats} Beat{(attacker.Beats == 1 ? "" : "s")} left"
                    : "no Beats left");
            mapLbl.ForeColor = attacker.Beats > 0 ? Blood : Faint;

            // What the roll really is, both ends of it, after Appendix B.
            var tgt = foes[Math.Clamp(target.SelectedIndex, 0, foes.Count - 1)];
            var mine = attacker.Load; var theirs = tgt.Load;
            int total = (int)toHit.Value + map + mine.Strike;
            var bits = new List<string> { $"Rolls d20{(total >= 0 ? "+" : "")}{total} vs Defense {tgt.EffectiveDefense}" };
            if (mine.Strike != 0)
                bits.Add($"{attacker.Name} is {attacker.Conditions.Trim()} — {(mine.Strike > 0 ? "+" : "")}{mine.Strike}");
            if (theirs.Defense != 0)
                bits.Add($"{tgt.Name} is {tgt.Conditions.Trim()} — Defense {tgt.Defense} → {tgt.EffectiveDefense}");
            if (mine.Damage != 0) bits.Add($"{mine.Damage} damage");
            against.Text = string.Join("   ·   ", bits);
            against.ForeColor = mine.Anything || theirs.Anything ? GoldDeep : Faint;
        }
        // default a soul to the gun they carry if we can spot one, else the first attack
        int guess = asCreature ? -1
            : sheet?.WeaponsCarried?.Select(wc => CharGen.D.weapons.FindIndex(w => wc.StartsWith(w.name)))
                   .FirstOrDefault(ix => ix >= 0) ?? -1;
        weapon.SelectedIndex = guess >= 0 ? guess : 0;
        weapon.SelectedIndexChanged += (s, e) => Sync();
        // The Defense being rolled against belongs to the TARGET, so changing who is being shot at
        // has to re-figure the line as surely as changing the gun does.
        target.SelectedIndexChanged += (s, e) => Sync();
        Sync();

        var how = Para(
            (EngineRolls ? "The engine rolls the d20 and reads the four degrees"
                         : "You roll the d20 and enter it above; the engine reads the four degrees")
            + ", applies the Multiple Attack Penalty at this combatant's step"
            + (asCreature ? "" : " and the Fatal die on a critical hit")
            + ", subtracts the target's DR, takes the Blood, and spends a Beat. Strike again to take "
            + "the next one at higher MAP; Begin turn on the tracker gives the Beats back and makes "
            + "the shot clean.", 178, f.Font, Ink);

        f.Controls.AddRange(new Control[] {
            L("Target:", 15), target, L(asCreature ? "Attack:" : "Weapon:", 51), weapon, L("To hit:", 87), toHit, mapLbl,
            L("Target DR:", 123), dr, against, how });
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

        // Reserved to the tallest sentence the rule can produce for THIS attacker, measured rather
        // than guessed — the name is in it, so the height is not a constant.
        refusal.Top = y;
        // Both sentences come from the rule itself rather than being copied here, so a reword there
        // cannot leave this reserving the wrong height. A stand-in with the attacker's name, no
        // Beats and Blood in it produces the longest of them.
        var spent = new Combatant { Name = attacker.Name, Beats = 0, BloodMax = 1, BloodCur = 1 };
        var felled = new Combatant { Name = attacker.Name, BloodMax = 1, BloodCur = 0 };
        refusal.Height = new[] { Rules.WhyNoBeats(spent), Rules.WhyNoBeats(felled) }
            .Max(t => TextRenderer.MeasureText(t, DialogItalic, new Size(CW, 0), TextFormatFlags.WordBreak).Height) + 4;
        y = refusal.Bottom + 8;

        ok.Left = Pad + CW - 182; ok.Top = y;
        cancel.Left = Pad + CW - 84; cancel.Top = y;
        f.Controls.AddRange(new Control[] { refusal, ok, cancel });
        f.ClientSize = new Size(CW + Pad * 2, ok.Bottom + Pad);
        f.CancelButton = cancel;
        Sync();                      // the buttons are placed now, so settle their state on them

        while (f.ShowDialog(this) == DialogResult.OK)
        {
            var tgt = foes[target.SelectedIndex];
            bool tgtWasDown = tgt.Down, tgtWasDead = tgt.Dead;
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
            // A terrible blow. The rule has been printed on the Keeper's screen since v1.4 and was
            // implemented nowhere — the app read it out and then left the Keeper to remember it in
            // the middle of a fight, which is the one moment nobody remembers anything.
            if (SoulOf(tgt) is PartyMember hurt
                && Rules.IsGrievous(rep.Res.AfterDR, tgt.BloodMax, rep.Res.Strike.Crit))
                OfferGrievous(hurt, tgt, rep.Res.AfterDR, rep.Res.Strike.Crit);
            // And the blow that put them on the ground. After the grievous offer on purpose: the
            // Lasting Injury is what the hit did, and refusing to fall is what they do about it.
            CheckFalling(tgt, tgtWasDown, tgtWasDead);
            // What the blow's own rider does beyond the Blood — a claw that grabs, a bite that
            // sickens. Last of the three, because a condition on somebody who is already dying is
            // the least of what just happened to them.
            if (asCreature) OfferConditions(tgt, rep.Inflicts, catks[idx].Effect);
            // Beats/MAP moved on — say so in both places, and keep the dialog live for a follow-up
            RefreshTracker(); Sync();
        }
    }

    /// <summary>A blow or a working named a condition — offer to lay it on. Offered rather than
    /// applied, and that is the whole design: the Bestiary's riders are English, and half of them
    /// hang on a save somebody still has to call ("Fort DC 15 or take the hydrophobia"). An engine
    /// that read "grab" and silently Grabbed the target would be right often enough to be trusted
    /// and wrong often enough to matter.
    ///
    /// <para>Already-held conditions are dropped from the offer rather than doubled: Frightened 2
    /// laid twice is Frightened 2, not Frightened 4, and a stack of duplicate words in the column is
    /// how the arithmetic below it stops being readable.</para></summary>
    void OfferConditions(Combatant on, List<string> named, string riderText)
    {
        if (on == null || named is not { Count: > 0 }) return;
        var have = (on.Conditions ?? "").Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries)
                       .Select(s => s.Trim()).ToList();
        var fresh = named.Where(n => !have.Any(h => h.StartsWith(n.Split(' ')[0], StringComparison.OrdinalIgnoreCase)))
                         .ToList();
        if (fresh.Count == 0) return;

        string what = string.Join(", ", fresh);
        var weight = Rules.ReadConditions(what);
        if (!Confirm($"That blow's own rider names {(fresh.Count == 1 ? "a condition" : "conditions")}: "
                   + $"{what}.\n\n\"{riderText?.Trim()}\"\n\n"
                   + $"Lay {(fresh.Count == 1 ? "it" : "them")} on {on.Name}?"
                   + (weight.Any ? $"\n\nIt would cost them: {weight.Line}." : "")
                   + "\n\nSay no if the save was made, or if you are calling it differently."))
            return;

        on.Conditions = have.Count == 0 ? what : string.Join(", ", have) + ", " + what;
        Log($"{on.Name} is {what}" + (weight.Any ? $" — {weight.Line}." : "."));
        Daybook.Note("turn", $"round {round}: {on.Name} takes {what}");
        RefreshTracker();
    }

    // ---- Dying, on the ground, and what can still be done about it (Ch. XI) ----

    /// <summary>Watch for the moment somebody goes down, and offer the one thing the book offers at
    /// that moment. Called with whether they were already down BEFORE the harm, because "they are
    /// down" is true for every round afterwards and the offer belongs to the round they fell.
    ///
    /// <para>Every route that can take Blood off a tracker row goes through here — the Strike, the
    /// Damage button, a working that deals damage — for the same reason every route onto the field
    /// goes through AddCreatureToTracker: a rule asked in three places is a rule forgotten in
    /// one.</para></summary>
    void CheckFalling(Combatant c, bool wasDown, bool wasDead)
    {
        if (c == null || c.IsSign) return;
        if (c.Dead && !wasDead)
        {
            Log($"{c.Name} is killed outright — the blow carried past −{c.DeathAt}.");
            Daybook.Note("death", $"round {round}: {c.Name} killed outright at −{c.Bleed} of {c.DeathAt}");
            if (SoulOf(c) is PartyMember gone)
                Nope($"{gone.Name} is killed outright.\n\nThe blow carried them to −{c.Bleed}, past the "
                   + $"−{c.DeathAt} the book puts the end at. There is no check for this one.\n\n"
                   + "Give the death its weight before the next scene rides in.");
            RefreshTracker();
            return;
        }
        if (wasDown || !c.Down || !c.Dying) return;

        var soul = SoulOf(c);
        // The offer is the posse's; a foe on the ground is simply on the ground.
        if (soul == null) return;
        Log($"{c.Name} falls — dying, and bleeding a Blood a round toward −{c.DeathAt}.");

        if (soul.Grit <= 0)
        {
            Nope($"{soul.Name} is down at 0 Blood — Dying, and bleeding one Blood every round toward "
               + $"−{c.DeathAt}.\n\nThey have no Grit left to refuse the fall. A Fortitude save or "
               + $"somebody's Medicine check at DC {Rules.StabilizeDc} stops the bleeding; right-click "
               + "their row for it.");
            return;
        }
        // A Confirm, not a menu: there are exactly two answers and one of them is doing nothing.
        if (!Confirm($"{soul.Name} is down at 0 Blood — Dying, and bleeding one Blood every round "
                   + $"toward −{c.DeathAt}. That is {c.DeathAt} rounds.\n\n"
                   + $"REFUSE TO FALL?  Spend 1 Grit ({soul.Grit} left) to stay conscious and on their "
                   + "feet for one more round (Ch. II). The bleeding does not stop — the book buys "
                   + "consciousness with Grit, not time.\n\n"
                   + "Yes spends the Grit. No lets them fall."))
            return;

        if (Rules.RefuseToFall(c, soul) is string why) { Nope(why); return; }
        Log($"{soul.Name} REFUSES TO FALL — 1 Grit spent ({soul.Grit} left), on their feet one more round.");
        Daybook.Note("turn", $"round {round}: {soul.Name} spent Grit to refuse the fall at −{c.Bleed}");
        posseGrid?.Refresh(); RefreshTracker();
    }

    /// <summary>The Keeper overruling the book. Nothing in Ch. XI walks a death back, and the app
    /// should not pretend otherwise by letting a heal do it quietly — but a Miracle, a Patron's
    /// bargain, or a table that simply decided is above the app's pay grade. So it exists, it is
    /// named for what it is, and it is asked about.</summary>
    void Resurrect(Combatant c)
    {
        if (c == null || !c.Dead) { Nope("That one is not dead."); return; }
        if (!Confirm($"{c.Name} is dead — they reached −{c.Bleed}, which is their CON.\n\n"
                   + "Put them back? They come round at 1 Blood: on their feet, and one hit from "
                   + "being back on the ground.\n\n"
                   + "The book has no rule for this. It is the table's call."))
            return;
        c.Bleed = 0; c.Stable = false; c.Upright = false;
        c.Wound(1, "back");
        if (SoulOf(c) is PartyMember p) p.BloodCur = c.BloodCur;
        posseGrid?.Refresh(); RefreshTracker();
        Log($"{c.Name} is back — 1 Blood, and the table's word for it.");
        Daybook.Note("death", $"round {round}: {c.Name} brought back by the Keeper's ruling");
    }

    /// <summary>Stop somebody bleeding out: a Fortitude save of their own, or another soul's
    /// Medicine check — the book gives both DC 15. Offered from the tracker's right-click menu and
    /// from Restore ▾, because it is the thing a Keeper reaches for at the worst moment and hunting
    /// for it is part of what makes that moment bad.</summary>
    void StabilizeDialog()
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Nope("Select whoever is on the ground first."); return; }
        if (c.Dead) { Nope($"{c.Name} is dead. Out here dead is dead — there is nothing left to stop."); return; }
        if (!c.Dying)
        {
            Nope(c.Stable ? $"{c.Name} is already stable — the bleeding has stopped."
               : c.Down ? $"{c.Name} is down, but the dying rule does not run on this row. It is the "
                        + "posse's rule; a creature at 0 Blood is simply put down."
                        : $"{c.Name} is still on their feet. There is nothing to stabilize.");
            return;
        }
        var soul = SoulOf(c);

        const int Pad = 16, CW = 470;
        using var f = new Sheet
        {
            Text = $"{c.Name} — stop the bleeding", FormBorderStyle = FormBorderStyle.FixedDialog,
            StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false,
            ShowIcon = false, BackColor = Paper
        };
        Label Para(string t, int top, Font font, Color fore) => new()
        {
            Left = Pad, Top = top, Width = CW, Text = t, Font = font, ForeColor = fore,
            Height = TextRenderer.MeasureText(t, font, new Size(CW, 0), TextFormatFlags.WordBreak).Height + 4
        };

        var head = Para($"{c.Name} is at −{c.Bleed} of −{c.DeathAt}. {c.RoundsToDeath} round"
                      + $"{(c.RoundsToDeath == 1 ? "" : "s")} left at a Blood a round.", Pad, DialogBold, Blood);
        var body = Para($"A Fortitude save or a Medicine check, either one at DC {Rules.StabilizeDc}, stops "
                      + "the bleeding (Ch. XI). Stable is not awake — they stay senseless at 0 Blood until "
                      + "somebody puts Blood back in them.", head.Bottom + 6, f.Font, Ink);

        var whichLbl = new Label { Left = Pad, Top = body.Bottom + 12, Width = 92, Text = "The check:" };
        var which = new ComboBox { Left = Pad + 96, Top = body.Bottom + 9, Width = CW - 96, DropDownStyle = ComboBoxStyle.DropDownList };
        which.Items.Add(soul != null ? $"{soul.Name}'s own Fortitude   ({(soul.Fort >= 0 ? "+" : "")}{soul.Fort})"
                                     : "their own Fortitude");
        which.Items.Add("somebody's Medicine check");
        which.SelectedIndex = 0;

        var modLbl = new Label { Left = Pad, Top = which.Bottom + 12, Width = 92, Text = "Modifier:" };
        var mod = new NumericUpDown { Left = Pad + 96, Top = which.Bottom + 9, Width = 70, Minimum = -20, Maximum = 40, Value = soul?.Fort ?? 0 };
        var modNote = new Label { Left = mod.Right + 10, Top = which.Bottom + 13, Width = CW - (mod.Right + 10 - Pad), Height = 18, ForeColor = Faint, Font = DialogItalic, AutoEllipsis = true };
        void SyncWhich()
        {
            bool own = which.SelectedIndex == 0;
            if (own && soul != null) mod.Value = Math.Clamp(soul.Fort, mod.Minimum, mod.Maximum);
            modNote.Text = own ? "their Fortitude, off the sheet" : "the healer's Medicine bonus — type it in";
        }
        which.SelectedIndexChanged += (s, e) => SyncWhich();
        SyncWhich();

        var d20Lbl = new Label { Left = Pad, Top = mod.Bottom + 12, Width = 92, Text = "d20 rolled:", ForeColor = Blood };
        var d20 = new NumericUpDown { Left = Pad + 96, Top = mod.Bottom + 9, Width = 70, Minimum = 1, Maximum = 20, Value = 10 };
        int y = (EngineRolls ? mod.Bottom : d20.Bottom) + 16;

        var go = new Button { Text = "Roll it ▸", Left = Pad + CW - 190, Top = y, Width = 96, Height = 30, DialogResult = DialogResult.OK };
        var close = new Button { Text = "Close", Left = Pad + CW - 88, Top = y, Width = 88, Height = 30, DialogResult = DialogResult.Cancel };
        f.Controls.AddRange(new Control[] { head, body, whichLbl, which, modLbl, mod, modNote, go, close });
        if (!EngineRolls) f.Controls.AddRange(new Control[] { d20Lbl, d20 });
        f.ClientSize = new Size(CW + Pad * 2, go.Bottom + Pad);
        f.AcceptButton = go; f.CancelButton = close;

        while (f.ShowDialog(this) == DialogResult.OK)
        {
            var res = Rules.Stabilize(c, (int)mod.Value, EngineRolls ? null : (int)d20.Value);
            Log($"{c.Name}: {res.Line}  (d20 {res.Die}{(res.Mod >= 0 ? "+" : "")}{res.Mod})");
            ShowResult(res.DegreeName, $"{c.Name} — {res.Line}", DegreeColor(res.DegreeName));
            if (SoulOf(c) is PartyMember p) { p.BloodCur = c.BloodCur; posseGrid?.Refresh(); }
            RefreshTracker();
            if (res.Stopped) break;                      // nothing left to roll for
            head.Text = $"{c.Name} is at −{c.Bleed} of −{c.DeathAt}. {c.RoundsToDeath} round"
                      + $"{(c.RoundsToDeath == 1 ? "" : "s")} left at a Blood a round.";
        }
    }

    // Roll a Dread Check for the selected soul (Ch. XII): Will save vs the Dread DC, Nerve off the
    // ladder on a failure, Frightened on a critical failure — and, at 0 Nerve, the break table.
    void DreadDialog()
    {
        if (trkGrid.CurrentRow?.DataBoundItem is not Combatant c) { Nope(NoSoulPicked); return; }
        var soul = SoulOf(c);
        if (soul == null) { Nope("Dread Checks are for the posse — select a player's soul."); return; }

        using var f = new Sheet { Width = 430, Height = 300, Text = $"{soul.Name} — Dread Check", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper };
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
        f.AcceptButton = check; f.CancelButton = close;

        while (f.ShowDialog(this) == DialogResult.OK)
            ResolveDread(soul, (int)dc.Value, EngineRolls ? null : (int)d20.Value);
    }

    /// <summary>One Dread Check, resolved one way, wherever it was called from — the Tracker's
    /// dialog above or the Posse tab's two buttons.
    ///
    /// It had two implementations, and they disagreed about the rule. The Posse tab rolled its own
    /// ladder and DOUBLED the loss on a critical failure, which the book does not say ("A critical
    /// failure … loses the listed Nerve and imposes Frightened 1 at once", Ch. XII); it also never
    /// hung the Frightened, never rolled the Affliction a DC-25 failure carries, and never touched
    /// the break table — so the same horror cost a soul twice the Nerve and left no mark on one tab,
    /// and cost the printed Nerve and left a scar on the other. This is the one road now.</summary>
    void ResolveDread(PartyMember soul, int dc, int? forcedDie)
    {
        if (soul == null) return;
        var o = Horror.DreadCheck(soul.Will, dc, forcedDie);
        Log($"{soul.Name}: {o.Line}");
        ShowResult(o.DegreeName, $"{soul.Name}: {o.Line}", DegreeColor(o.DegreeName));
        if (o.NerveLost > 0) soul.NerveCur = Math.Max(0, soul.NerveCur - o.NerveLost);
        if (o.Frightened)
        {
            // The condition rides the tracker row, and a soul checked from the Posse tab may not be
            // on the field. Say so rather than dropping it: an unrecorded condition is the Keeper's
            // problem two rounds later.
            var row = tracker.FirstOrDefault(t => t.IsSoul(soul));
            if (row != null) ApplyConditionTo(row, "Frightened 1");
            else Log($"{soul.Name} is Frightened 1 — send them to the Tracker for it to be carried.");
        }

        // Two rules, both the book's, and they can fire on the same check: a DC-25 failure carries
        // "1d10 + a lasting Affliction", and breaking at 0 Nerve takes "a lasting Affliction that
        // rides you until it is treated". One d10 is rolled either way — the soul came out of one
        // night changed once, and two modal dialogs back to back for it would be the app arguing
        // with itself in front of the table.
        bool broke = soul.NerveCur == 0;
        if (broke)
        {
            var bk = Horror.Break();
            Log($"{soul.Name} {bk.Line}");
            if (bk.GainsMark) soul.Mark += 1;
        }
        if (o.Affliction || broke)
        {
            var (d10, aff, cost) = Rules.RollAffliction();
            string why = o.Affliction && broke ? "a truth that unmakes a world, and no Nerve left to meet it"
                       : o.Affliction ? "a truth that unmakes a world"
                       : "driven to 0 Nerve — they broke";
            Log($"{soul.Name} does not come back whole — Affliction, d10 {d10}: {aff}. {cost}");
            ShowResult("AFFLICTION", $"{soul.Name}: {aff}\n{cost}", Blood);
            RecordScar(soul, "Affliction", aff, why);
        }
        posseGrid?.Refresh(); trkGrid?.Refresh();
    }

    /// <summary>A blow bad enough to leave something behind (Ch. XI): half the soul's maximum Blood
    /// in one hit, or any critical. Fortitude save at DC 15 — the engine table rolls it, the
    /// dice-and-books table is asked for it — and on a failure the d6 says what it cost.</summary>
    void OfferGrievous(PartyMember soul, Combatant row, int damage, bool crit)
    {
        string why = crit ? "a critical hit" : $"{damage} in one blow, against {row.BloodMax} Blood";
        if (!Confirm($"A terrible blow — {why}.\n\n{soul.Name} makes a Fortitude save at DC {Rules.GrievousDc} "
                   + "or takes a Lasting Injury. Roll it?")) return;

        int die = AskDie($"{soul.Name}'s Fortitude save against DC {Rules.GrievousDc} — what did the d20 come up?")
                  ?? Rules.Rng.Next(1, 21);
        var (idx, deg, detail) = Rules.FourDegrees(die, soul.Fort, Rules.GrievousDc);
        if (idx > 1)   // 2 = success, 3 = critical success
        {
            Log($"{soul.Name} rides it out — Fortitude {detail} → {deg}. No lasting injury.");
            ShowResult(deg, $"{soul.Name} rides out a terrible blow.", Verdigris);
            return;
        }
        var (d6, injury) = Rules.RollInjury();
        Log($"{soul.Name} — Fortitude {detail} → {deg}. Lasting Injury, d6 {d6}: {injury}.");
        ShowResult("LASTING INJURY", $"{soul.Name}: {injury}", Blood);
        RecordScar(soul, "Injury", injury, why);
    }

    /// <summary>Write a mark onto a soul that they do not get to put down — a Lasting Injury off
    /// the d6, or an Affliction out of a Dread Check that went badly. Prefilled with what the app
    /// knows and editable, because the books name the six injuries and deliberately leave the
    /// Afflictions to the table: "the scars that stay" is a prompt, not a list.</summary>
    /// <param name="soul">Who carries it. Null is a no-op, so callers need not test first.</param>
    /// <param name="kind">"Injury" or "Affliction" — which of the two ledgers, and which book's
    /// list the What box offers.</param>
    /// <param name="suggested">What the dice said, prefilled into the What box and editable.</param>
    /// <param name="because">What brought it on, in the app's own words, when the engine knows —
    /// it goes into the dialog's opening line and into the Keeper's ledger with the entry. Empty
    /// for the two hand-written routes off the Posse tab's menu, where the Keeper knows why.</param>
    void RecordScar(PartyMember soul, string kind, string suggested, string because = "")
    {
        if (soul == null) return;
        const int Pad = 16, CW = 420;
        using var f = new Sheet
        {
            Text = kind == "Affliction" ? "A scar that stays" : "A Lasting Injury",
            FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent,
            MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper
        };
        string blurb = kind == "Affliction"
            ? $"{soul.Name} came out of that changed{(because.Length > 0 ? " — " + because : "")}. An "
              + "Affliction is not a condition — it does not wear off, and it is yours to name: a fear "
              + "of the dark, a stammer, a thing they will not do any more. Keeper's Book, Ch. III."
            : $"{soul.Name} took a terrible blow{(because.Length > 0 ? " — " + because : "")}. A Lasting "
              + "Injury does not heal with rest alone — it takes a Sawbones, time, and sometimes a "
              + "graveyard. Player's Book, Ch. XI.";
        var say = new Label
        {
            Left = Pad, Top = Pad, Width = CW, ForeColor = Ink,
            Height = TextRenderer.MeasureText(blurb, f.Font, new Size(CW, 0), TextFormatFlags.WordBreak).Height + 6,
            Text = blurb
        };
        var nameLbl = new Label { Left = Pad, Top = say.Bottom + 12, Width = 70, Text = "What:" };
        var name = new ComboBox
        {
            Left = Pad + 74, Top = say.Bottom + 9, Width = CW - 74, DropDownStyle = ComboBoxStyle.DropDown
        };
        // Both lists are the BOOK's, not the app's: the d6 of Lasting Injuries (Ch. XI) and the
        // d10 of Afflictions (Keeper's Book Ch. III). Still a free-text combo, because the
        // Keeper's Book says plainly to "roll one, or choose the one that bites deepest".
        if (kind == "Injury") name.Items.AddRange(Rules.LastingInjuries.Cast<object>().ToArray());
        else name.Items.AddRange(Rules.Afflictions.Select(a => (object)a.name).ToArray());
        name.Text = suggested;

        var noteLbl = new Label { Left = Pad, Top = name.Bottom + 12, Width = 70, Text = "Note:" };
        var note = new TextBox { Left = Pad + 74, Top = name.Bottom + 9, Width = CW - 74, Height = 54, Multiline = true };
        // Picking one of the book's ten fills in what it costs, so the note is the rule rather
        // than a blank the Keeper has to go and look up mid-scene.
        if (kind == "Affliction")
            name.SelectedIndexChanged += (s, e) =>
            {
                int i = name.SelectedIndex;
                if (i >= 0 && i < Rules.Afflictions.Length) note.Text = Rules.Afflictions[i].cost;
            };
        var whenLbl = new Label { Left = Pad, Top = note.Bottom + 12, Width = 70, Text = "When:" };
        var when = new TextBox { Left = Pad + 74, Top = note.Bottom + 9, Width = 180, Text = DateTime.Now.ToString("d MMM yyyy") };

        var ok = new Button { Text = "Write it down", Left = Pad + CW - 226, Top = when.Bottom + 16, Width = 120, Height = 30, DialogResult = DialogResult.OK };
        var skip = new Button { Text = "Let it go", Left = Pad + CW - 100, Top = ok.Top, Width = 100, Height = 30, DialogResult = DialogResult.Cancel };
        f.Controls.AddRange(new Control[] { say, nameLbl, name, noteLbl, note, whenLbl, when, ok, skip });
        f.ClientSize = new Size(CW + Pad * 2, ok.Bottom + Pad);
        f.AcceptButton = ok; f.CancelButton = skip;

        if (f.ShowDialog(this) != DialogResult.OK) { Log($"{soul.Name} — the {kind.ToLowerInvariant()} was not written down."); return; }
        string what = name.Text.Trim();
        if (what.Length == 0) what = kind == "Affliction" ? "Something changed" : "A lasting hurt";
        var scar = new Scar { Kind = kind, Name = what, Note = note.Text.Trim(), When = when.Text.Trim() };
        soul.Scars ??= new();
        soul.Scars.Add(scar);
        CaptureUndo();
        posseGrid?.Refresh();
        RefreshSoulCard(soul);
        // "Write it down" now writes it down somewhere a Keeper can read at the end of the night.
        // It always went onto the soul — the Posse tab's Scars column, the Ledger sheet — and that
        // is the ledger the RULES care about, but the button says the words the Session tab's
        // Keeper's ledger is for, and a scar nobody sees written is a scar the table doubts
        // happened. Both, therefore: the sheet keeps it, the ledger says it happened tonight.
        ToLedger($"{soul.Name} — {kind.ToLowerInvariant()}: {what}"
            + (because.Length > 0 ? $"  ({because})" : "")
            + (scar.Note.Length > 0 ? Environment.NewLine + "    " + scar.Note : ""));
        Log($"{soul.Name} carries it now — {kind.ToLowerInvariant()}: {what}. Written into the Keeper's ledger.");
    }

    /// <summary>Append a dated line to the Keeper's ledger on the Session tab — the app's own hand
    /// in the notebook the Keeper keeps. Written through the FIELD as well as the box, because the
    /// Session tab fills itself on first visit and a night's play can easily never open it; the
    /// box, when it exists, is the live view of that same string.</summary>
    void ToLedger(string line)
    {
        if (string.IsNullOrWhiteSpace(line)) return;
        string stamp = $"[{DateTime.Now:HH:mm}]  {line}";
        if (notesBox != null)
        {
            notesBox.AppendText((notesBox.TextLength > 0 ? Environment.NewLine : "") + stamp);
            notesText = notesBox.Text;                 // TextChanged does this too; belt and braces
        }
        else notesText = (notesText.Length > 0 ? notesText + Environment.NewLine : "") + stamp;
    }

    /// <summary>Read a sign &amp; spoor row: a Survival check at the Tier's DC, what the four degrees
    /// give the tracker, the Dread it costs them, and one more segment of the clock. This is the
    /// safe-table rule as a scene you can actually run — the thing takes part in the fight through
    /// what it left behind, and the fight is against the reading.</summary>
    /// <param name="sign">The thread being read. Normally the card's own — each Threads card carries
    /// its Read it ▸ button, so there is no selection to guess at. Null falls back to the only thread
    /// on the trail, which is what a keyboard or menu route means when there is just one.</param>
    void ReadSignDialog(Combatant sign = null)
    {
        if (sign == null)
        {
            if (signs.Count == 0) { Nope("Nothing on the trail. A creature too far over the posse arrives as sign & spoor."); return; }
            if (signs.Count > 1) { Nope("More than one thread on the trail — press Read it ▸ on the one being read."); return; }
            sign = signs[0];
        }
        var beast = Db.Find(sign.Ref);
        int tier = beast?.tier ?? 1;
        var (readDc, dreadDc, what) = Rules.SpoorFor(tier);

        var readers = tracker.Where(t => SoulOf(t) != null).Select(t => SoulOf(t)).ToList();
        if (readers.Count == 0) readers = party.ToList();
        if (readers.Count == 0) { Nope("Nobody to read it — put the posse on the field first."); return; }

        const int Pad = 16, CW = 470;
        using var f = new Sheet
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
            posseGrid?.Refresh(); trkGrid?.Refresh(); RefreshSigns();

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
        signs.Remove(sign);
        if (beast != null)
        {
            AddCreatureToTracker(beast, 1, skipSafeTable: true);   // the rule has already run its course
            Log($"{beast.name} comes in the flesh. The safe table is over.");
        }
        RefreshSigns(); RefreshTracker();
    }

    // ---- Signs, Miracles, and creature powers: working one, and what it costs ----

    /// <summary>One thing a combatant could work, gathered from wherever that combatant's powers
    /// actually live — a soul's own known lists, or a creature's Bestiary line — together with what
    /// the printed text says it DOES (<see cref="Rules.ReadWorking"/>): who it lands on, how long it
    /// holds, what dice it rolls, and what it costs the worker when it turns on them.</summary>
    sealed record Workable(string Name, string Kind, int Rank, string Cost, string Effect, Rules.Working Read);

    /// <summary>What this combatant can work. A posse soul offers exactly what is written on their
    /// sheet — Signs from Ch. XIII, Miracles from Ch. VI, nothing they have not learned. A creature
    /// offers the power its own stat block names. Anything else is typed by hand, because the
    /// Keeper is allowed to invent and the app should not be the reason they cannot.
    ///
    /// The worker's level rides along because the book scales some durations by it — "one round per
    /// two levels" is a real number once you know whose Sign it is, and the app is what should be
    /// doing that arithmetic.</summary>
    List<Workable> WorkablesFor(Combatant c)
    {
        var list = new List<Workable>();
        if (c == null) return list;
        var sheet = SoulOf(c)?.Sheet;
        int lvl = Math.Max(1, sheet?.Level ?? 1);

        Workable Make(string n, string kind, int rank, string cost, string desc)
            => new(n, kind, rank, cost, desc, Rules.ReadWorking(n, kind, rank, cost, desc, lvl));

        if (sheet is CharacterSheet sh)
        {
            foreach (var name in sh.SignsKnown ?? new())
                if (CharGen.D?.signs?.Find(x => x.name == name) is CgSign sg)
                    list.Add(Make(sg.name, "Sign", sg.rank, sg.cost, sg.desc));
            foreach (var name in sh.MiraclesKnown ?? new())
                if (CharGen.D?.miracles?.Find(x => x.name == name) is CgMiracle mi)
                    list.Add(Make(mi.name, "Miracle", mi.rank, mi.cost, mi.desc));
        }
        else if (Db.Find(c.Ref) is Creature beast && !string.IsNullOrWhiteSpace(beast.special))
        {
            var (nm, eff) = Rules.ParsePower(beast.special);
            if (nm.Length > 0) list.Add(Make(nm, "Power", 0, "", eff));
        }
        return list;
    }

    /// <summary>Work a Sign, a Miracle, or a creature's own power onto someone, and keep the cause
    /// with the effect. The cost comes off the worker, the effect goes onto the target, and the
    /// tracker carries both until it runs out or is ended.</summary>
    void WorkPowerDialog(Combatant preferredWorker = null)
    {
        if (tracker.Count == 0) { Nope("Nobody on the field to work anything."); return; }

        const int Pad = 16, CW = 500;
        using var f = new Sheet
        {
            Text = "Work a Sign or Miracle", FormBorderStyle = FormBorderStyle.FixedDialog,
            StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false,
            ShowIcon = false, BackColor = Paper
        };
        Label L(string t, int top) => new() { Left = Pad, Top = top + 4, Width = 100, Text = t };

        var folk = tracker.ToList();
        var who = new ComboBox { Left = Pad + 104, Top = Pad, Width = CW - 104, DropDownStyle = ComboBoxStyle.DropDownList };
        foreach (var t in folk) who.Items.Add(t.Name);
        who.SelectedIndex = Math.Max(0, folk.IndexOf(preferredWorker ?? folk[0]));
        var whoLbl = L("Who works it:", Pad);
        var whoNote = new Label { Left = Pad + 104, Top = who.Bottom + 3, Width = CW - 104, Height = 17, ForeColor = Gold, Font = DialogItalic, AutoEllipsis = true };

        var what = new ComboBox { Left = Pad + 104, Top = whoNote.Bottom + 6, Width = CW - 104, DropDownStyle = ComboBoxStyle.DropDownList };
        var whatLbl = L("What:", whoNote.Bottom + 2);
        var freeName = new TextBox { Left = Pad + 104, Top = what.Bottom + 6, Width = CW - 104, Enabled = false, PlaceholderText = "name it yourself" };

        var detail = new TextBox
        {
            Left = Pad, Top = freeName.Bottom + 8, Width = CW, Height = 88, Multiline = true, ReadOnly = true,
            ScrollBars = ScrollBars.Vertical, BackColor = Color.FromArgb(250, 246, 236), BorderStyle = BorderStyle.FixedSingle
        };

        // The Backlash gets its own field, in the ink the app uses for what the dark costs you. It
        // used to sit in the middle of the effect blob above, which is where a Keeper looks last
        // and needs it first — and forty of the eighty workings have one.
        var backlash = new TextBox
        {
            Left = Pad, Top = detail.Bottom + 6, Width = CW, Height = 40, Multiline = true, ReadOnly = true,
            ScrollBars = ScrollBars.Vertical, BackColor = Color.FromArgb(252, 244, 242),
            ForeColor = Blood, BorderStyle = BorderStyle.FixedSingle, Visible = false
        };

        var onWhom = new ComboBox { Left = Pad + 104, Top = backlash.Bottom + 10, Width = CW - 104, DropDownStyle = ComboBoxStyle.DropDownList };
        var onLbl = L("On whom:", backlash.Bottom + 6);

        // Duration is the book's word, not a round count. Eleven of the eighty last "for a scene",
        // six until dawn, five a day — and every one of them showed on the chip as "until it is
        // ended by hand", which is true of none of them. The reader prefills this; the Keeper can
        // still say otherwise, because a ruling at the table beats a parser every time.
        var lasts = new ComboBox { Left = Pad + 104, Top = onWhom.Bottom + 8, Width = 178, DropDownStyle = ComboBoxStyle.DropDownList };
        var lastsKinds = new[] { Rules.WorkEnds.Rounds, Rules.WorkEnds.NextTurn, Rules.WorkEnds.Scene,
                                 Rules.WorkEnds.Hour, Rules.WorkEnds.Day, Rules.WorkEnds.UntilDawn,
                                 Rules.WorkEnds.UntilEnded, Rules.WorkEnds.Instant };
        foreach (var k in lastsKinds)
            lasts.Items.Add(k switch
            {
                Rules.WorkEnds.Rounds     => "a number of rounds",
                Rules.WorkEnds.NextTurn   => "until their next turn",
                Rules.WorkEnds.Scene      => "for the scene",
                Rules.WorkEnds.Hour       => "for an hour",
                Rules.WorkEnds.Day        => "for a day",
                Rules.WorkEnds.UntilDawn  => "until dawn",
                Rules.WorkEnds.Instant    => "at once — nothing to carry",
                _                         => "until something ends it",
            });
        var lastsLbl = L("Lasts:", onWhom.Bottom + 5);
        var rounds = new NumericUpDown { Left = lasts.Right + 8, Top = lasts.Top, Width = 62, Minimum = 1, Maximum = 99, Value = 1 };
        var roundsNote = new Label
        {
            Left = rounds.Right + 6, Top = lasts.Top + 3, Width = Math.Max(20, CW - (rounds.Right + 6 - Pad)),
            Height = 18, ForeColor = Ink, Font = DialogItalic, Text = "rounds"
        };

        // What it actually rolls, and what the table decides about the save. The old dialog knew a
        // working might force a save and said so in one line of prose; it never rolled the 3d6 the
        // Sign is FOR, so every damaging working was resolved on somebody's paper anyway.
        var rollIt = new CheckBox { Left = Pad, Top = lasts.Bottom + 10, Width = CW - 96, Height = 22, Visible = false };
        // At a dice-and-books table the Keeper rolls their own dice, so the app must ask for the
        // number rather than make one up. Same bargain as the Strike and Dread dialogs (AskDie):
        // the engine table gets its dice rolled for it, the dice table gets asked. Without this the
        // one dialog that rolls Signs would have quietly ignored the mode the whole app runs on.
        var rolled = new NumericUpDown
        {
            Left = Pad + CW - 88, Top = lasts.Bottom + 8, Width = 88, Minimum = 0, Maximum = 999, Value = 0,
            Visible = false, TextAlign = HorizontalAlignment.Center
        };
        Tip.SetToolTip(rolled, "The total you rolled on the dice this working calls for");
        var saved = new ComboBox { Left = Pad + 104, Top = rollIt.Bottom + 4, Width = CW - 104, DropDownStyle = ComboBoxStyle.DropDownList, Visible = false };
        saved.Items.AddRange(new object[] { "they failed the save — it lands in full", "they made it — half", "they made it — none at all" });
        saved.SelectedIndex = 0;
        var savedLbl = new Label { Left = Pad, Top = rollIt.Bottom + 8, Width = 100, Text = "The save:", Visible = false };

        var spend = new CheckBox { Left = Pad, Top = saved.Bottom + 8, Width = CW, Height = 22, Checked = true };
        // What working this costs OUT OF THE TURN, which is the half of the price the app never
        // charged. The cost line the book prints — "1 Beat · 2 Nerve · Will save" — has been parsed
        // since v1.20 and only its currencies were ever spent, so a soul with three Beats could work
        // six Signs and still Strike. Two lines tall, fixed: the refusal is longer than the price,
        // and a block that changes height would walk the buttons around under the Keeper's hand.
        var beatLbl = new Label
        {
            Left = Pad, Width = CW, Font = DialogItalic, AutoSize = false,
            Height = TextRenderer.MeasureText("Wg", DialogItalic).Height * 2 + 4
        };
        // Declared here rather than at the bottom because Relayout places them and sizes the form
        // off where they land, and a local function cannot reach a local declared after it.
        var go = new Button { Text = "Work it ▸", Left = Pad + CW - 198, Width = 100, Height = 32, DialogResult = DialogResult.OK };
        var close = new Button { Text = "Close", Left = Pad + CW - 92, Width = 92, Height = 32, DialogResult = DialogResult.Cancel };

        // ---- what the pickers say to each other ----
        List<Workable> options = new();
        void SyncWhat()
        {
            var worker = folk[Math.Max(0, who.SelectedIndex)];
            options = WorkablesFor(worker);
            what.Items.Clear();
            foreach (var o in options) what.Items.Add($"{(o.Kind == "Miracle" ? "✝" : o.Kind == "Power" ? "◈" : "✦")} {o.Name}"
                                                    + (o.Rank > 0 ? $"  (R{o.Rank})" : ""));
            what.Items.Add("— something else —");
            what.SelectedIndex = 0;

            var soul = SoulOf(worker);
            whoNote.Text = soul?.Sheet is CharacterSheet sh
                ? $"{sh.Calling}, level {sh.Level} — {options.Count(o => o.Kind == "Sign")} Signs, "
                  + $"{options.Count(o => o.Kind == "Miracle")} Miracles known"
                : soul != null ? "no sheet on this soul — name what they work by hand"
                : Db.Find(worker.Ref) != null ? "a creature — offering the power its stat block names"
                : "an ad-hoc combatant — name what they work by hand";
        }
        // Re-shape the "on whom" list for the working now selected. The old list offered
        // one combatant or "everyone on the field" and nothing else, which fits about half the
        // book: Witch-Sight is worked on yourself, The Tally is a question put to the dark and
        // lands on nobody, and Salt & Iron catches everything within ten feet — friends included,
        // which is not the same list as everyone in the fight. The right entry is preselected; the
        // whole roster stays on offer underneath it, because the parse is advice, not a gate.
        void SyncTargets(Rules.Working w, Combatant worker)
        {
            onWhom.Items.Clear();
            switch (w?.Shape)
            {
                case Rules.WorkShape.Trait:
                    onWhom.Items.Add("— nothing to target: this is what it IS —");
                    break;
                case Rules.WorkShape.Self:
                    onWhom.Items.Add($"— {worker.Name}, who is working it —");
                    break;
                case Rules.WorkShape.Area:
                    onWhom.Items.Add(w.AreaFeet > 0
                        ? $"— everything within {w.AreaFeet} feet (friends too) —"
                        : "— everything nearby (friends too) —");
                    break;
                case Rules.WorkShape.Place:
                    onWhom.Items.Add("— a place, a thing, or nobody at all —");
                    break;
                case Rules.WorkShape.Counter:
                    onWhom.Items.Add("— another working, not a person —");
                    break;
                default:
                    onWhom.Items.Add("— everyone on the field —");
                    break;
            }
            foreach (var t in folk) onWhom.Items.Add(t.Name);
            // Self lands on the worker; a shape that names a creature starts on somebody other than
            // the worker if there is one, since almost nobody Stills themselves.
            int pick = w?.Shape switch
            {
                Rules.WorkShape.Self => 1 + Math.Max(0, folk.IndexOf(worker)),
                Rules.WorkShape.OneCreature or Rules.WorkShape.Ally =>
                    1 + Math.Max(0, folk.FindIndex(t => !ReferenceEquals(t, worker))),
                _ => 0,
            };
            onWhom.SelectedIndex = Math.Clamp(pick, 0, onWhom.Items.Count - 1);
        }

        // Stack everything below the effect box off whatever is actually showing, and size
        // the form to what came out. The dialog's height genuinely changes with the working now —
        // a Sign shows its Backlash and a damaging one shows a save row, and a Miracle shows
        // neither — so a layout pinned to constants would leave a hole under half the workings and
        // clip the buttons off the bottom of the other half. Same rule as the Strike dialog: place
        // off the previous control's Bottom, and set ClientSize last.
        //
        // SyncDetail wraps its own body so this runs on EVERY path out of it, rather than on the
        // paths somebody remembered. It was written the other way first, and the "— something
        // else —" branch returned before reflowing: a Gunhand, who knows no Signs and no Miracles
        // and so only ever sees that branch, opened this dialog at the WinForms default 300x300
        // with the buttons off the bottom edge. It built clean and passed the whole smoke suite;
        // it was caught by taking a picture of it. The wrapper is why it cannot happen again.
        void Relayout()
        {
            backlash.Top = detail.Bottom + 6;
            backlash.Height = 40;
            int y = (backlash.Visible ? backlash.Bottom : detail.Bottom) + 10;

            onWhom.Top = y; onLbl.Top = y + 4;
            lasts.Top = onWhom.Bottom + 8; lastsLbl.Top = lasts.Top + 4;
            rounds.Top = lasts.Top; roundsNote.Top = lasts.Top + 3;

            y = lasts.Bottom;
            if (rollIt.Visible) { rollIt.Top = y + 10; rolled.Top = y + 8; y = rollIt.Bottom; }
            if (saved.Visible) { saved.Top = y + 4; savedLbl.Top = saved.Top + 4; y = saved.Bottom; }

            spend.Top = y + 8;
            beatLbl.Top = spend.Bottom + 6;
            go.Top = close.Top = beatLbl.Bottom + 10;
            f.ClientSize = new Size(CW + Pad * 2, go.Bottom + Pad);
        }

        // What the turn is charged, and whether there is a turn left to charge. Runs from the
        // SyncDetail wrapper so it covers every path out of the body — including the two early
        // returns, which is exactly the shape of miss that put a Gunhand's dialog at 300x300.
        void SyncBeats()
        {
            var worker = folk[Math.Max(0, who.SelectedIndex)];
            bool custom = what.SelectedIndex < 0 || what.SelectedIndex >= options.Count;
            // A hand-named working has no printed time line, so the app has no business inventing a
            // cost for it — the Keeper said what it was and the Keeper can say what it took.
            int beats = custom ? 0 : Rules.BeatsFor(Rules.ParseCost(options[what.SelectedIndex].Cost).Time);
            string why = Rules.WhyNoBeats(worker, beats);
            go.Enabled = why == null;
            close.Text = why == null ? "Close" : "Back to the field ▸";
            f.AcceptButton = why == null ? go : close;
            beatLbl.ForeColor = why == null ? Faint : Blood;
            beatLbl.Text = why ?? (beats == 0
                ? $"Takes no Beat — worked outside the turn. {worker.Name} still has {worker.Beats} of three."
                : $"Costs {beats} Beat{(beats == 1 ? "" : "s")} of {worker.Name}'s turn — {worker.Beats} left, "
                  + $"{worker.Beats - beats} after.");
        }

        void SyncEnds(Rules.WorkEnds e, int n)
        {
            int i = Array.IndexOf(lastsKinds, e);
            lasts.SelectedIndex = i < 0 ? Array.IndexOf(lastsKinds, Rules.WorkEnds.UntilEnded) : i;
            if (n > 0) rounds.Value = Math.Clamp(n, rounds.Minimum, rounds.Maximum);
            bool counted = e == Rules.WorkEnds.Rounds;
            rounds.Visible = roundsNote.Visible = counted;
        }
        lasts.SelectedIndexChanged += (s, e) =>
        {
            bool counted = lasts.SelectedIndex >= 0 && lastsKinds[lasts.SelectedIndex] == Rules.WorkEnds.Rounds;
            rounds.Visible = roundsNote.Visible = counted;
        };

        // The wrapper: whatever the body does, and whichever way it returns, the form gets measured.
        void SyncDetail() { SyncDetailBody(); SyncBeats(); Relayout(); }

        void SyncDetailBody()
        {
            bool custom = what.SelectedIndex >= options.Count;
            freeName.Enabled = custom;
            var worker = folk[Math.Max(0, who.SelectedIndex)];
            if (custom)
            {
                detail.Text = "Something the book does not print, or a power this app has not been told about. "
                            + "Name it, say who it lands on and how long it holds, and it rides on them like any other.";
                backlash.Visible = false;
                rollIt.Visible = rolled.Visible = saved.Visible = savedLbl.Visible = false;
                SyncTargets(null, worker);
                SyncEnds(Rules.WorkEnds.UntilEnded, 0);
                spend.Text = "Spend nothing — a hand-named effect has no printed cost";
                spend.Checked = false; spend.Enabled = false;
                return;
            }
            var o = options[what.SelectedIndex];
            var w = o.Read;
            var pc = Rules.ParseCost(o.Cost);

            // The header line now says the three things the Keeper is about to be asked about —
            // who it lands on, how long it holds, and what dice it rolls — instead of only the cost.
            var facts = new List<string> { w.Kind + (o.Rank > 0 ? $", Rank {o.Rank}" : "") };
            if (!string.IsNullOrWhiteSpace(o.Cost)) facts.Add(o.Cost);
            facts.Add(w.ShapeLine);
            facts.Add(w.EndsLine);
            if (w.Damage.Length > 0) facts.Add($"{w.Damage} damage" + (w.SaveForHalf ? ", save for half" : ""));
            if (w.Ongoing.Length > 0) facts.Add($"{w.Ongoing} each round");
            if (w.Heal.Length > 0) facts.Add($"heals {w.Heal}");
            if (w.Nerve.Length > 0) facts.Add($"{w.Nerve} Nerve");
            if (w.HasSave) facts.Add($"{w.Save} save");
            detail.Text = string.Join("   ·   ", facts) + "\r\n\r\n" + w.Effect;

            backlash.Visible = w.HasBacklash;
            if (w.HasBacklash) backlash.Text = "Backlash: " + w.Backlash;

            SyncTargets(w, worker);
            SyncEnds(w.Ends, w.Rounds);

            rollIt.Visible = w.Resolves;
            rollIt.Checked = w.Resolves;
            string dice = w.Heal.Length > 0 ? w.Heal : w.Nerve.Length > 0 ? w.Nerve
                        : w.Ongoing.Length > 0 ? w.Ongoing : w.Damage;
            string verb = w.Heal.Length > 0 ? "and mend them now"
                        : w.Nerve.Length > 0 ? "Nerve and apply it now"
                        : w.Ongoing.Length > 0 ? "now — it repeats each round"
                        : "and apply it now";
            rollIt.Text = EngineRolls ? $"Roll {dice} {verb}" : $"Apply {dice} {verb} — you rolled:";
            rolled.Visible = w.Resolves && !EngineRolls;
            if (rolled.Visible && rolled.Value == 0) rolled.Value = Math.Clamp(Rules.RollExpr(dice).total, 1, 999);
            saved.Visible = savedLbl.Visible = w.Resolves && (w.SaveForHalf || w.HasSave);

            var soul = SoulOf(worker);
            if (!pc.Spends || soul == null)
            {
                spend.Text = pc.Spends ? "Spend the cost — only a posse soul keeps the pools it comes out of"
                                       : "Costs nothing to work";
                spend.Checked = false; spend.Enabled = false;
                return;
            }
            var bits = new List<string>();
            if (pc.Nerve > 0) bits.Add($"{pc.Nerve} Nerve (has {soul.NerveCur})");
            if (pc.Faith > 0) bits.Add($"{pc.Faith} {(string.IsNullOrWhiteSpace(soul.PoolName) ? "Faith" : soul.PoolName)} (has {soul.PoolCur})");
            if (pc.Blood > 0) bits.Add($"{pc.Blood} Blood");
            if (pc.Mark > 0) bits.Add($"{pc.Mark} Mark");
            spend.Enabled = true; spend.Checked = true;
            spend.Text = "Spend it from " + soul.Name + " — " + string.Join(", ", bits)
                       + (pc.OrBlood > 0 ? $"   (or {pc.OrBlood} Blood instead)" : "");
        }

        f.Controls.AddRange(new Control[] { whoLbl, who, whoNote, whatLbl, what, freeName, detail, backlash,
                                            onLbl, onWhom, lastsLbl, lasts, rounds, roundsNote,
                                            rollIt, rolled, savedLbl, saved, spend, beatLbl, go, close });
        f.CancelButton = close;   // AcceptButton is SyncBeats', so Enter follows whichever is live

        // Wired and driven only once the buttons exist, because Relayout places them and sizes the
        // form off where they land.
        who.SelectedIndexChanged += (s, e) => { SyncWhat(); SyncDetail(); };
        what.SelectedIndexChanged += (s, e) => SyncDetail();
        SyncWhat(); SyncDetail();

        while (f.ShowDialog(this) == DialogResult.OK)
        {
            var worker = folk[Math.Max(0, who.SelectedIndex)];
            bool custom = what.SelectedIndex >= options.Count;
            string name = custom ? freeName.Text.Trim() : options[what.SelectedIndex].Name;
            if (name.Length == 0) { Nope("Name what is being worked."); continue; }

            var o = custom
                ? new Workable(name, "Sign", 0, "", "Worked by hand at the table.",
                               Rules.ReadWorking(name, "Sign", 0, "", "Worked by hand at the table."))
                : options[what.SelectedIndex];
            var w = o.Read;
            var pc = Rules.ParseCost(o.Cost);
            var soul = SoulOf(worker);

            // Ask before overspending rather than refusing: the Keeper may be running a thing the
            // pools do not model, and the book's numbers are theirs to overrule.
            if (spend.Checked && soul != null)
            {
                var short_ = new List<string>();
                if (pc.Nerve > soul.NerveCur) short_.Add($"{pc.Nerve} Nerve but has {soul.NerveCur}");
                if (pc.Faith > soul.PoolCur) short_.Add($"{pc.Faith} from the pool but has {soul.PoolCur}");
                if (short_.Count > 0 && !Confirm($"{soul.Name} cannot pay: needs {string.Join("; ", short_)}. Work it anyway?"))
                    continue;
                if (pc.Nerve > 0) soul.NerveCur = Math.Max(0, soul.NerveCur - pc.Nerve);
                if (pc.Faith > 0) soul.PoolCur = Math.Max(0, soul.PoolCur - pc.Faith);
                if (pc.Mark > 0) soul.Mark += pc.Mark;
                if (pc.Blood > 0) { worker.Wound(-pc.Blood, $"−{pc.Blood} working it"); soul.BloodCur = worker.BloodCur; }
            }

            // The Beat is charged whether or not the pools are — it is the turn's own currency and
            // it belongs to the combatant, not to the soul behind them, so a creature working its
            // own power pays it too. Outside the "spend it" checkbox for the same reason: that
            // switch is about the Keeper overruling a soul's Nerve and Faith, not about whether the
            // Iron Code's three Beats exist.
            int beatCost = custom ? 0 : Rules.BeatsFor(pc.Time);
            if (beatCost > 0) worker.Beats = Math.Max(0, worker.Beats - beatCost);

            // Duration is whatever the Keeper left in the box — prefilled from the book, theirs to
            // override. Only a round count is a number the tracker counts down; everything else
            // rides at −1 and says so in its own words on the chip.
            var ends = lastsKinds[Math.Max(0, lasts.SelectedIndex)];
            int left = ends == Rules.WorkEnds.Rounds ? (int)rounds.Value : -1;

            // The first entry is the shape's own answer — "everything within ten feet", "nobody at
            // all", "the worker". Beyond a Trait or a Place, that means the whole field; a Trait or
            // a Place lands on nothing and simply gets recorded against the worker so there is a
            // note of it somewhere.
            bool shapeEntry = onWhom.SelectedIndex == 0;
            bool landsNowhere = shapeEntry && (w.Shape == Rules.WorkShape.Trait
                                            || w.Shape == Rules.WorkShape.Place
                                            || w.Shape == Rules.WorkShape.Counter);
            var targets = !shapeEntry ? new List<Combatant> { folk[onWhom.SelectedIndex - 1] }
                        : landsNowhere ? new List<Combatant> { worker }
                        : w.Shape == Rules.WorkShape.Self ? new List<Combatant> { worker }
                        : folk;

            // Roll what it does, once, and share the one result out — an area Sign is one working,
            // not one per body, and rolling per target would make a 6d8 crack in the ground land
            // differently on two people standing in the same hole.
            string note = "";
            if (rollIt.Visible && rollIt.Checked)
            {
                int band = saved.Visible ? saved.SelectedIndex : 0;   // 0 failed · 1 half · 2 none
                string expr = w.Heal.Length > 0 ? w.Heal : w.Nerve.Length > 0 ? w.Nerve
                            : w.Ongoing.Length > 0 ? w.Ongoing : w.Damage;
                // The engine table's dice are the app's; the dice table's are the Keeper's.
                int total = EngineRolls ? Rules.RollExpr(expr).total : (int)rolled.Value;
                int applied = band == 2 ? 0 : band == 1 ? Math.Max(1, total / 2) : total;
                string saveWord = band == 2 ? " — saved, and it does nothing"
                                : band == 1 ? $" — saved for half, {applied}" : "";

                if (w.Heal.Length > 0)
                {
                    foreach (var t in targets)
                    { t.Wound(applied, $"+{applied} mended"); if (SoulOf(t) is PartyMember mp) mp.BloodCur = t.BloodCur; }
                    note = $"{expr} → {total} healed{saveWord}";
                }
                else if (w.Nerve.Length > 0)
                {
                    foreach (var t in targets)
                        if (SoulOf(t) is PartyMember np) np.NerveCur = Math.Min(np.NerveMax, np.NerveCur + applied);
                    note = $"{expr} → {total} Nerve{saveWord}";
                }
                else
                {
                    // Captured before the harm, because "were they already down" stops being
                    // answerable the moment it lands — same reason the Strike dialog captures it.
                    var before = targets.ToDictionary(t => t, t => (t.Down, t.Dead));
                    foreach (var t in targets)
                    { t.Wound(-applied, $"−{applied}"); if (SoulOf(t) is PartyMember dp) dp.BloodCur = t.BloodCur; }
                    foreach (var t in targets) CheckFalling(t, before[t].Down, before[t].Dead);
                    // The Hungering Hand and its kin: half of what was taken goes to the worker.
                    if (w.DrainsToWorker && applied > 0)
                    {
                        int back = Math.Max(1, applied / 2);
                        worker.Wound(back, $"+{back} drawn");
                        if (SoulOf(worker) is PartyMember wp) wp.BloodCur = worker.BloodCur;
                        note = $"{expr} → {total}{saveWord}, {back} drawn back to {worker.Name}";
                    }
                    else note = $"{expr} → {total}{saveWord}";
                }
            }

            foreach (var t in targets)
                t.Work(new WorkedEffect
                {
                    Name = o.Name, Kind = o.Kind, Rank = o.Rank, Source = worker.Name,
                    Cost = o.Cost, Effect = w.Effect, RoundsLeft = left, SinceRound = round,
                    Shape = w.Shape, AreaFeet = w.AreaFeet, Ends = ends,
                    Backlash = w.Backlash, Note = note
                });

            // A working that names one of Appendix B's conditions lays it on the same way a
            // creature's rider does — through the ONE condition column, so the arithmetic under it
            // has a single author. Not asked for a Trait or a Place: nothing is standing there to
            // be Frightened.
            if (w.Shape != Rules.WorkShape.Trait && w.Shape != Rules.WorkShape.Place)
                foreach (var t in targets)
                    OfferConditions(t, Rules.InflictedConditions(w.Effect), o.Name);

            string onWho = !shapeEntry ? targets[0].Name
                         : landsNowhere ? "no one — it is not that kind of working"
                         : w.Shape == Rules.WorkShape.Self ? worker.Name
                         : w.Shape == Rules.WorkShape.Area
                             ? (w.AreaFeet > 0 ? $"everything within {w.AreaFeet} feet" : "everything nearby")
                             : "everyone on the field";
            Log($"{worker.Name} works {o.Name} ({o.Kind.ToLowerInvariant()}) on {onWho} — "
                + $"{new WorkedEffect { Ends = ends, RoundsLeft = left }.Duration}"
                + (note.Length > 0 ? $". {note}" : "")
                + (pc.HasSave && !rollIt.Checked ? $". {(targets.Count > 1 ? "Each" : targets[0].Name)} rolls a {pc.Save} save." : "."));
            ShowResult(o.Name, $"{worker.Name} → {onWho}"
                + (note.Length > 0 ? $"\n{note}" : "")
                + (pc.HasSave && !rollIt.Checked ? $"\n{pc.Save} save to resist." : ""), Verdigris);

            // The Beat just spent has to reach the dialog that spent it, or the Keeper works a third
            // Sign out of a turn that has nothing left in it. Same shape as the Strike dialog's
            // trailing Sync: the window stays open for a follow-up, so it has to keep telling the
            // truth about what the follow-up costs.
            posseGrid?.Refresh(); RefreshTracker(); SyncDetail();
        }
    }

    // ============================================================ GENERATORS TAB
    RichTextBox genOut;

    // The last town and the last city rolled, kept so they can be handed to the Map tab as a
    // place to survey. A rolled town that can't be drawn is a rolled town the Keeper writes on
    // a napkin — this is the seam between "what's here" and "what it looks like".
    string genLastTown, genLastCity;
    Adventure genLastAdv;

    TabPage BuildGeneratorsTab()
    {
        var page = new TabPage("Generators") { BackColor = Paper };
        // Seated against the button column rather than at 27% of the window (v1.38.0, user-reported).
        // Every control in the left panel is 230px wide by construction, so a ratio could only ever
        // be right at one window size — at 1280 it put the splitter some seventy pixels clear of the
        // buttons and called the gap a layout. Panel1's minimum comes down with it: 300 was above
        // what the column measures, so it was doing the clamping and the measurement never got a
        // say. The Func is evaluated in the deferred handler, after `left` below has been filled.
        FlowLayoutPanel left = null;
        var split = Split(Orientation.Vertical, 200, 300, 0.27, () => MeasuredColumnWidth(left));

        left = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.TopDown, WrapContents = false, Padding = new Padding(12), AutoScroll = true, BackColor = Paper };
        left.Controls.Add(Heading("The Country in Your Pocket"));

        // The two "→ Map" buttons are built first so the roll handlers can wake them, and they
        // start asleep: a button that sends nowhere is worse than no button.
        //
        // Each is a menu rather than a single action because a settlement is two maps, not one.
        // The streets answer "what is in here"; the county answers "what is around it, and how far".
        // A city could only ever be drawn as a ward before v1.25.0, so the second question — the one
        // a posse riding toward it actually has — had no answer at all.
        (string, EventHandler)[] PlaceMenu(Func<string> Place, bool city)
        {
            var items = new List<(string, EventHandler)>
            {
                (city ? "The ward itself — blocks and avenues" : "The town itself — its streets",
                    (s, e) => SendPlaceToMap(Place(), city, PlaceView.Itself)),
                ("-", null),
                ("In its country — roll the ground",
                    (s, e) => SendPlaceToMap(Place(), city, PlaceView.InItsCountry)),
                ("Or set it down in…", null),      // null handler = a greyed heading, not a choice
            };
            foreach (var t in MapGen.SettingTerrains)
            {
                string ground = t;                 // captured per item, not per loop
                items.Add(("    " + ground,
                    (s, e) => SendPlaceToMap(Place(), city, PlaceView.InItsCountry, ground)));
            }
            return items.ToArray();
        }

        var townToMap = MenuBtn("→ Map — this town ▾", 230,
            "Survey the town just rolled — its streets, or the country it stands in",
            PlaceMenu(() => genLastTown, false));
        var cityToMap = MenuBtn("→ Map — this city ▾", 230,
            "Survey the city just rolled — its ward, or the country it stands in",
            PlaceMenu(() => genLastCity, true));
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
        // ---- a whole adventure ----
        // The rest of this column rolls one line at a time and leaves the joining to the Keeper.
        // This one rolls the joins as well: a shape, a hook, a place, a trouble out of the Bestiary,
        // the truth under it, the turn, and a clock — then hands the pieces to the parts of the app
        // that can actually run them, because a scenario that stays in a text box is a scenario the
        // Keeper has to retype at midnight.
        var advToThread = Btn("→ Thread — start its clock", (s, e) =>
        {
            if (genLastAdv == null) { Nope("Roll an adventure first — there is no clock to start yet."); return; }
            clocks.Add(new CampaignClock { Name = genLastAdv.Clock, Segments = genLastAdv.ClockSegments });
            RefreshClocks();
            Log($"Thread started — “{genLastAdv.Clock}”, {genLastAdv.ClockSegments} segments.");
        }, 230, "Put what happens if nobody moves on the Ledger as a running clock");
        var advToMap = MenuBtn("→ Map — its town ▾", 230,
            "Survey the adventure's town — its streets, or the country it stands in",
            PlaceMenu(() => genLastAdv?.TownName, false));
        advToThread.Enabled = advToMap.Enabled = false;

        left.Controls.Add(Btn("An adventure, whole", (s, e) =>
        {
            genLastAdv = Db.RollAdventure((int)(encLevel?.Value ?? partyLevelHint));
            advToThread.Enabled = advToMap.Enabled = true;
            Gen(genLastAdv.Sheet());
        }, 230, "Roll a whole scenario: its shape, the hook, the place, the trouble, the truth under it, the turn, and a clock"));
        left.Controls.Add(advToThread);
        left.Controls.Add(advToMap);

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
        Tip.SetToolTip(terr, "Which ground the posse is on — each of the Grounds has its own table of what "
            + "is out there, so a roll on the high desert can't hand you a swamp thing.\nRoll below. What "
            + "comes up is reported with its Tier, and where it is too much for the posse to meet head-on "
            + "you are given its sign and its clock instead: the safe-table rule, applied for you.");
        left.Controls.Add(terr);
        left.Controls.Add(Btn("Roll on that ground", (s, e) => RollGround(terr.SelectedItem.ToString()), 230, "Roll an encounter on the chosen ground — the safe-table rule is applied for you"));
        left.Controls.Add(Btn("The Hand Behind It — a villain", (s, e) => RollGround(villainTable), 230,
            "Who's truly behind the trouble — the villain picker, its own table in the book"));

        left.Controls.Add(new Label { Height = 8, Width = 4 });
        // A copy to the clipboard leaves no mark on the screen at all, so silence here reads as
        // failure whether it worked or not. Both ends now say which happened.
        left.Controls.Add(Btn("Copy output", (s, e) =>
        {
            if (genOut.TextLength == 0) { Nope("Nothing rolled yet — no output to copy."); return; }
            Clipboard.SetText(genOut.Text);
            Log("The generator's output is on the clipboard.");
        }, 112, "Copy everything rolled so far to the clipboard"));
        left.Controls.Add(Btn("Clear", (s, e) =>
        {
            if (genOut.TextLength == 0) { Nope("The output box is already empty."); return; }
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
    /// The pane's width in monospaced characters at the last deal — see the Resize handler.
    int refCols;

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

    /// <summary>Which leaves are the KEEPER's side of the screen, paired with the titles above.
    /// A player's table gets a rules reference; it does not get the Keeper's book. The two marked
    /// here are the two whose content comes wholly out of the Keeper's Book and appears nowhere in
    /// the Player's Book at all (checked against the built HTML, not judged by eye):
    ///
    ///   The Long Odds   — Keeper's Book Ch. IV. Threat by Tier is every creature's Defense, Attack,
    ///                     Blood, saves, damage and Dread DC before the posse has met one; the
    ///                     encounter budget is the Keeper's dial for how hard tonight is; and the
    ///                     safe-table rule tells a player which horrors the app will refuse to put
    ///                     in front of them. Reading it is reading the answers.
    ///   Running in Town — Keeper's Book Ch. XIV, and the leaf's own header says so. It is running
    ///                     advice end to end ("charge for it; never forbid it", how a city cult
    ///                     incorporates, how the last scene usually goes), which is craft for the
    ///                     chair, not a rule anyone at the table plays by.
    ///
    /// Everything else stays: the DC ladder, the Nerve-loss-by-Tier table and the rest all print in
    /// the Player's Book, so hiding them would be keeping a player from their own book.</summary>
    static readonly bool[] RefLeafKeeperOnly =
    {
        false, false, false, false,
        false, false, false, false,
        true,  false, false,
        false, true,
    };

    /// <summary>How many leaves the Keeper's screen holds — derived, never typed twice.</summary>
    internal static int RefLeafCount => RefLeafTitles.Length;

    /// <summary>How many leaves a given table's screen holds. Derived from the same two arrays for
    /// the same reason the total is: the five-minute lesson quotes this number and a player must not
    /// be told to look for a leaf their deck does not carry.</summary>
    internal static int RefLeafCountFor(RunMode mode)
        => mode == RunMode.Player ? RefLeafKeeperOnly.Count(k => !k) : RefLeafTitles.Length;

    /// <summary>The deck as actually built. Zero until the Reference tab is realized (tabs are
    /// lazy); <c>--selftest</c> builds it on purpose to check the titles and the renderers agree.
    /// </summary>
    internal int RefDeckLength => refDeck?.Length ?? 0;

    // The Keeper's screen, in the faces the books are set in — and, since v1.38.0, at a size a
    // Keeper can read across a table (user-reported: "change the font so that it's more in line with
    // the settings and themes of the game, also enlarging the reference material so that it fills
    // the empty space better").
    //
    // Two things were wrong and only one of them was the size. The prose was already Georgia, but
    // the TABLES — which are most of what is on every leaf — were Consolas, a face drawn in 2006 for
    // reading source code on a screen. Nothing else in this app or these books is set in it. The
    // deck is the Keeper's screen out of a western-horror rulebook and it read like a terminal.
    //
    // The columns still need a monospaced face and that is not a preference: the tables are padded
    // to width with spaces, which is also what carries the Blood-red header band out to the right
    // edge, and Georgia is a text-figure face whose 3 4 5 7 9 descend so a column of numbers does
    // not line up (the same reason LedgerView draws its figures in a different face). Courier New
    // is the monospace a period document would actually have been struck on, it is on every Windows
    // machine, and at 11.5pt it holds a line without reading as code.
    static readonly string RefMonoFace = FirstInstalledFace("Courier New", "Consolas");
    static Font RefMono  => Face(RefMonoFace, 11.5f);
    static Font RefMonoB => Face(RefMonoFace, 11.5f, FontStyle.Bold);
    static Font RefBody  => Face("Georgia", 12.5f);
    static Font RefItal  => Face("Georgia", 12f, FontStyle.Italic);
    static Font RefHead  => Face("Georgia", 16.5f, FontStyle.Bold);

    /// <summary>The first of these actually installed. GDI+ silently substitutes Microsoft Sans
    /// Serif for a family it does not have and the substitute reports its own name, which is the
    /// only way to catch it — the same probe LedgerView uses to pick its figures face, and it lives
    /// twice because the two files are on opposite sides of the rules/UI split.</summary>
    static string FirstInstalledFace(params string[] names)
    {
        foreach (var n in names)
        {
            try
            {
                using var probe = new Font(n, 10f);
                if (string.Equals(probe.Name, n, StringComparison.OrdinalIgnoreCase)) return n;
            }
            catch { /* a broken font file shouldn't cost us the deck */ }
        }
        return "Consolas";
    }

    /// <summary>How many monospaced characters fit across the reference pane right now. Measured
    /// with NoPadding over a long run, because TextRenderer adds a few pixels of its own to a short
    /// string and dividing that by one character is how a table comes out three columns too wide.
    /// </summary>
    int RefColumns()
    {
        if (refView == null || refView.ClientSize.Width < 80) return 0;
        int ten = TextRenderer.MeasureText(new string('0', 50), RefMono, Size.Empty, TextFormatFlags.NoPadding).Width;
        double ch = ten / 50.0;
        if (ch < 1) return 0;
        // The pane's own right margin, plus room for the vertical scrollbar every long leaf grows.
        int usable = refView.ClientSize.Width - 8 - SystemInformation.VerticalScrollBarWidth;
        return Math.Max(20, (int)(usable / ch));
    }

    /// <summary>Widen an authored table to the room actually on screen. The leaves' column widths
    /// were written to fit about eighty characters, so on this laptop's 1280px window the tables
    /// occupied a little under half the pane and the rest was empty paper — which is exactly what
    /// was reported.
    ///
    /// <para>The surplus goes to the LAST column and nowhere else — the one carrying the rule text.
    /// The columns beside it hold a DC, a die face, a condition name: they are already as wide as
    /// anything that goes in them, and widening one only opens a gulf between a label and the
    /// sentence it labels. The first version of this spread the leftovers across every column and
    /// put thirty-six characters under a heading reading "Degree", with "CRITICAL SUCCESS" marooned
    /// at one end of it — wider is not the same as better used.</para>
    ///
    /// <para>Capped at <see cref="RefMeasureCap"/> characters, because past about ninety a line
    /// stops being easier to read and starts being harder; whatever is left over stays as margin,
    /// which is what a book would do with it.</para></summary>
    const int RefMeasureCap = 90;
    static int[] RefFit(int[] w, int capacity)
    {
        if (w == null || w.Length == 0) return w;
        int joins = 2 * (w.Length - 1) + 2;              // the "  " between columns, plus the edges
        int authored = w.Sum() + joins;
        if (capacity <= authored) return w;
        var outw = (int[])w.Clone();
        int last = w.Length - 1;
        outw[last] += Math.Min(capacity - authored, Math.Max(0, RefMeasureCap - outw[last]));
        return outw;
    }

    static void RH(RichTextBox r, string s) { r.SelectionFont = RefHead; r.SelectionColor = Blood; r.AppendText(s + "\n"); }
    static void RT(RichTextBox r, string s) { r.SelectionFont = RefBody; r.SelectionColor = Ink; r.AppendText(s + "\n\n"); }
    static void RI(RichTextBox r, string s) { r.SelectionFont = RefItal; r.SelectionColor = GoldDeep; r.AppendText(s + "\n\n"); }

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
    void RTbl(RichTextBox r, int[] w, string[] head, IEnumerable<string[]> rows)
    {
        w = RefFit(w, RefColumns());          // widened to the pane the Keeper actually has
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
    void RTbl(RichTextBox r, int[] w, string[] head, params string[][] rows)
        => RTbl(r, w, head, (IEnumerable<string[]>)rows);

    internal TabPage BuildReferenceTab()
    {
        referencePage = new TabPage("Reference") { BackColor = Paper };

        var bar = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(6, 4, 6, 4), BackColor = Color.FromArgb(243, 237, 221) };
        bar.Controls.Add(Btn("◀", (s, e) => RefShow(refPage - 1), 44, "Previous leaf (or press Left)"));
        bar.Controls.Add(Btn("▶", (s, e) => RefShow(refPage + 1), 44, "Next leaf (or press Right)"));
        // The leaf's name is the page's title, so it is set in the book's face like every other
        // title in the deck. It was Segoe UI, which is Windows' voice rather than the game's, and it
        // sat directly above thirteen Georgia headings saying the same kind of thing.
        refTitle = new Label { AutoSize = true, UseMnemonic = false, Font = Face("Georgia", 14f, FontStyle.Bold), ForeColor = Blood, Padding = new Padding(10, 7, 0, 0) };
        bar.Controls.Add(refTitle);
        refCount = new Label { AutoSize = true, Font = Face("Georgia", 9.5f, FontStyle.Italic), ForeColor = Slate, Padding = new Padding(12, 12, 0, 0) };
        bar.Controls.Add(refCount);

        refView = new RichTextBox { ReadOnly = true, BackColor = Paper, Font = RefBody, BorderStyle = BorderStyle.None };
        // The tables are laid to the pane's width, so the pane changing width relaid them — but only
        // when the number of CHARACTERS across actually changes. A resize drag raises this event
        // dozens of times a second and re-dealing a leaf on every one of them would redraw the whole
        // deck while the mouse is still down. Comparing the measurement rather than the pixels means
        // the work happens once per column gained or lost.
        refView.Resize += (s, e) =>
        {
            int cols = RefColumns();
            if (cols == refCols || refDeck == null) return;
            refCols = cols;
            RefShow(refPage);
        };

        BuildRefDeck();
        referencePage.Controls.Add(Pad(refView, 14));
        referencePage.Controls.Add(bar);
        RefShow(0);
        return referencePage;
    }

    /// <summary>Deal the deck for the table this app is running. Split out of the tab build so a mode
    /// switched live from the Table menu re-deals rather than leaving a player looking at the deck a
    /// Keeper was handed.</summary>
    void BuildRefDeck()
    {
        // Paired with RefLeafTitles and RefLeafKeeperOnly, in that order. Kept as separate lists so
        // the titles can be a static the prose reads without constructing a form.
        var leaves = new Action<RichTextBox>[]
        {
            RefLeafRoll, RefLeafIronCode, RefLeafWounds, RefLeafConditions,
            RefLeafNerve, RefLeafMarkTaint, RefLeafSignsGrit, RefLeafMiracles,
            RefLeafLongOdds, RefLeafArms, RefLeafGoods,
            RefLeafSkills, RefLeafCity,
        };
        if (leaves.Length != RefLeafTitles.Length || RefLeafKeeperOnly.Length != RefLeafTitles.Length)
            throw new InvalidOperationException(
                $"Reference deck: {RefLeafTitles.Length} titles against {leaves.Length} leaves and "
                + $"{RefLeafKeeperOnly.Length} audience flags — add the title AND the flag beside the renderer.");
        refDeck = RefLeafTitles.Zip(leaves, (t, r) => (t, r))
            .Where((_, i) => Mode != RunMode.Player || !RefLeafKeeperOnly[i])
            .ToArray();
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
            new[] { "A terrible blow", $"One hit for half maximum Blood or more, or any critical hit → Fortitude save DC {Rules.GrievousDc} (higher for terrible weapons) or take a Lasting Injury" });

        RH(r, "Lasting Injuries");
        // Rendered from Rules.LastingInjuries, not typed here — the app rolls off that same list
        // when a terrible blow lands, and a printed table that could disagree with the roller is
        // the exact drift this project keeps closing.
        RTbl(r, new[] { 3, 60 }, new[] { "d6", "Injury" },
            Rules.LastingInjuries.Select((n, i) => new[] { (i + 1).ToString(), n }));
        RT(r, "Lasting Injuries do not heal with rest alone — they take a Sawbones, time, and sometimes a graveyard.");
        RI(r, "The app keeps them: a terrible blow offers the save, and what it costs goes on the "
             + "soul's Scars, beside any Affliction a Dread Check leaves. Posse tab, Scars column.");

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

        // Rendered from Rules.Afflictions, which is the Keeper's Book's own d10 — the app rolls
        // off that same list when a Dread Check leaves a scar, so the printed table and the roller
        // cannot part company.
        RH(r, "Afflictions — the Scars That Stay  (Keeper's Book, Ch. III)");
        RTbl(r, new[] { 4, 17, 58 }, new[] { "d10", "The Affliction", "What it costs" },
            Rules.Afflictions.Select((a, i) => new[] { (i + 1).ToString(), a.name, a.cost }));
        RT(r, "Rolled on a true Break, a horror beheld at DC 25, or a Mark step that should cost more "
             + "than the rest. They heal slowly and seldom on their own — a season of safety, a true "
             + "sanctification, an Alienist's care, or facing down the thing that caused it.");
        RI(r, "An Affliction is a story hook, not a punishment. The app writes it onto the soul's "
             + "Scars, and the Posse tab's right-click menu strikes it off when it is earned.");

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
        RT(r, "The app runs this for you. Send a creature the rule bars to the Tracker and it offers to put it "
             + "on the trail instead of the field. Threads live in their own strip above the initiative order — "
             + "they take no turn and there is nothing to shoot — each showing what is on the ground, the DCs, "
             + "and its clock in plain words. Read it ▸ resolves the Survival check, the Dread it costs the "
             + "reader, and one more segment. When the clock fills, the app offers to bring the thing in.");
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
        Tip.SetToolTip(notesBox, "The Keeper's notebook — whatever you want to still have next session. It "
            + "saves with everything else: on exit, and every five minutes while you work.\nThis box keeps "
            + "its own typing undo (Ctrl+Z inside it); the app's Undo in the status bar is for the tables, "
            + "and deliberately leaves your writing alone.");
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
        // AutoSave announces a failure once per distinct reason, which is right for the five-minute
        // timer and wrong for a hand-pressed button: press Save now twice against a disk that will
        // not take it and the second press said nothing whatever. A deliberate press always answers.
        cbar.Controls.Add(Btn("Save now", (s, e) =>
        {
            if (AutoSave()) Log("Session saved.");
            else Nope("The session did NOT save — see the message above, or use File ▸ Save session as…");
        }, 90, "Write the session to disk now — it also saves itself every 5 minutes and on exit"));
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
        using var f = new Sheet { Width = 360, Height = 200, Text = "New thread", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper };
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
        using var f = new Sheet { Width = 360, Height = 160, Text = "Rename thread", FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper };
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
