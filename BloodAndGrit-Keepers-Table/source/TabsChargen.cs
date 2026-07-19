namespace BloodAndGritKeeper;

public partial class MainForm
{
    // ============================================================ NEW SOUL TAB
    // A whole character sheet at the press of a button, walked through Chapter III's
    // eight steps against Data/chargen.json (transcribed from the Player's Book) and
    // re-validated by CharGen.Validate before it is ever shown — the generator is not
    // allowed to hand the Keeper a character the book couldn't have made. The result
    // is displayed on the book's own Ledger sheet, and can be hand-tweaked or built
    // choice by choice through the wizard.
    LedgerView soulLedger;
    NumericUpDown soulLevel;
    ComboBox soulMethod, soulCalling, soulOrigin;
    CharacterSheet lastSoul;
    Label soulHint;

    TabPage BuildSoulTab()
    {
        var page = new TabPage("New Soul") { BackColor = Paper };

        var bar = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(8, 6, 8, 6), BackColor = Color.FromArgb(243, 237, 221) };
        bar.Controls.Add(Lbl("Level:"));
        soulLevel = new NumericUpDown { Minimum = 1, Maximum = 10, Value = 1, Width = 52, Margin = new Padding(3, 6, 3, 3) };
        Tip.SetToolTip(soulLevel, "1st is a greenhorn; 10th is a long, unlikely old age");
        bar.Controls.Add(soulLevel);

        bar.Controls.Add(Lbl("  Abilities:"));
        soulMethod = new ComboBox { Width = 165, DropDownStyle = ComboBoxStyle.DropDownList };
        soulMethod.Items.AddRange(new object[] { "The Honest Array", "The Gamble (rolled)" });
        soulMethod.SelectedIndex = 0;
        Tip.SetToolTip(soulMethod, "Ch. III — the fixed 15/14/13/12/10/8 array, or 4d6-drop-lowest");
        bar.Controls.Add(soulMethod);

        bar.Controls.Add(Lbl("  Calling:"));
        soulCalling = new ComboBox { Width = 150, DropDownStyle = ComboBoxStyle.DropDownList };
        soulCalling.Items.Add("Random");
        foreach (var c in CharGen.D.callings.OrderBy(c => c.name)) soulCalling.Items.Add(c.name);
        soulCalling.SelectedIndex = 0;
        bar.Controls.Add(soulCalling);

        bar.Controls.Add(Lbl("  Origin:"));
        soulOrigin = new ComboBox { Width = 150, DropDownStyle = ComboBoxStyle.DropDownList };
        soulOrigin.Items.Add("Random");
        foreach (var o in CharGen.D.origins) soulOrigin.Items.Add(o.name);
        soulOrigin.SelectedIndex = 0;
        bar.Controls.Add(soulOrigin);
        bar.SetFlowBreak(soulOrigin, true);

        bar.Controls.Add(Btn("🎲 Make a soul", (s, e) => GenerateSoul(), 120, "Deal a whole character, strictly by the book"));
        bar.Controls.Add(Btn("🧭 Wizard…", (s, e) => RunSoulWizard(), 100, "Build a custom character choice by choice, Ch. III's eight steps"));
        bar.Controls.Add(Btn("✎ Tweak", (s, e) =>
        {
            if (lastSoul == null) { Log("Make a soul first."); return; }
            if (TweakSheet(lastSoul, this))
            {
                ShowSoul(lastSoul);
                Log($"{lastSoul.Name}'s sheet hand-tweaked.");
            }
        }, 85, "Hand-adjust the sheet — any number, any list"));
        bar.Controls.Add(Btn("→ Posse", (s, e) => SoulToPosse(), 85, "Add this soul to the Posse tab"));
        bar.Controls.Add(Btn("Copy sheet", (s, e) => { if (lastSoul != null) Clipboard.SetText(CharGen.Render(lastSoul)); }, 95, "Copy the sheet as plain text"));
        bar.Controls.Add(Btn("Save PDF…", (s, e) => SoulSavePdf(), 90, "Save the sheet as a printable PDF"));
        bar.Controls.Add(Btn("A−", (s, e) => { if (soulLedger != null) soulLedger.Zoom -= 0.15f; }, 46, "Smaller sheet"));
        bar.Controls.Add(Btn("A＋", (s, e) => { if (soulLedger != null) soulLedger.Zoom += 0.15f; }, 46, "Larger sheet"));
        bar.Controls.Add(Btn("Clear", (s, e) => { soulLedger.Clear(); lastSoul = null; soulHint.Visible = true; }, 70, "Wipe the sheet for a fresh start"));

        soulLedger = new LedgerView { Dock = DockStyle.Fill };

        soulHint = new Label
        {
            Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleCenter,
            Font = new Font("Segoe UI", 11f, FontStyle.Italic), ForeColor = Gold, BackColor = Paper,
            Text = "Eight steps from a blank page to a soul worth losing.\n\n" +
                   "🎲 Make a soul rolls the whole character for you, strictly by the book —\n" +
                   "pin a level, Calling, or Origin first if you have one in mind.\n\n" +
                   "🧭 Wizard… walks you through every choice yourself: abilities, skills,\n" +
                   "Edges, Signs, coin and all — checked against the rules at each step.\n\n" +
                   "Either way the sheet lands on the book's own Ledger. ✎ Tweak it by hand,\n" +
                   "send it to the Posse, or copy it out."
        };
        page.Controls.Add(soulLedger);
        page.Controls.Add(soulHint);
        page.Controls.Add(bar);
        soulHint.BringToFront();
        Watermark(soulHint, () => HintBottom(soulHint));
        return page;
    }

    void ShowSoul(CharacterSheet sheet)
    {
        lastSoul = sheet;
        soulLedger.ShowSheet(sheet, null, SheetWarnings(sheet));
        soulHint.Visible = false;
    }

    void GenerateSoul()
    {
        string calling = soulCalling.SelectedIndex > 0 ? soulCalling.SelectedItem.ToString() : null;
        string origin = soulOrigin.SelectedIndex > 0 ? soulOrigin.SelectedItem.ToString() : null;

        // Ch. IV: a Calling of Faith may not take the Gambler background — say so rather than silently ignoring
        if (calling != null && origin == "The Gambler" && CharGen.D.callings.First(c => c.name == calling).group == "Faith")
        {
            Log("Ch. IV: a soul sworn to the pulpit has no business at the green table — a Calling of Faith may not take the Gambler origin. Origin re-drawn.");
            origin = null;
        }

        var sheet = CharGen.Generate((int)soulLevel.Value, soulMethod.SelectedIndex == 1, calling, origin);
        ShowSoul(sheet);
        Log($"New soul: {sheet.Name}, {sheet.Calling} ({sheet.Origin}), level {sheet.Level}.");
    }

    void SoulSavePdf()
    {
        if (lastSoul == null) { Log("Make a soul first."); return; }
        var s = lastSoul;
        using var d = new SaveFileDialog
        {
            Title = "Save the sheet as PDF",
            Filter = "PDF (*.pdf)|*.pdf|All files (*.*)|*.*",
            FileName = new string(s.Name.ToLowerInvariant().Select(c => char.IsLetterOrDigit(c) ? c : '-').ToArray()).Trim('-') + ".pdf"
        };
        if (d.ShowDialog(this) != DialogResult.OK) return;
        try
        {
            File.WriteAllBytes(d.FileName, Pdf.TextSheet(
                s.Name,
                $"{s.Calling} · {s.Origin} — level {s.Level}" + (string.IsNullOrEmpty(s.Gender) ? "" : $" · {s.Gender.ToLowerInvariant()}"),
                CharGen.Render(s)));
            Log($"Sheet saved: {Path.GetFileName(d.FileName)}.");
        }
        catch (Exception ex)
        {
            MessageBox.Show("Couldn't save there:\r\n\r\n" + ex.Message, "GritKeeper", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    void SoulToPosse()
    {
        if (lastSoul == null) { Log("Make a soul first."); return; }
        var s = lastSoul;
        var p = new PartyMember
        {
            Name = s.Name, Calling = s.Calling, Level = s.Level,
            BloodMax = s.Blood, BloodCur = s.Blood, Defense = s.Defense,
            Fort = s.Fort, Ref = s.Ref, Will = s.Will,
            RES = s.Scores["RES"],                       // drives the Nerve auto-recalc
            Grit = s.Grit, Mark = s.Mark,
            Notes = s.Origin + (s.Subpath != null ? " · " + s.Subpath : ""),
            Sheet = s                                    // the full record rides along
        };
        if (p.NerveMax != s.NerveMax) { p.NerveMax = s.NerveMax; p.NerveCur = s.NerveMax; }   // Stone Nerve
        party.Add(p);
        Log($"{s.Name} joins the posse.");
    }

    // ============================================================ THE TWEAK DIALOG
    // Hand adjustments to a finished sheet — every number and every list editable.
    // The result is re-checked, but never blocked: a tweaked sheet is the Keeper's
    // word against the book's, and the Ledger notes it instead of arguing.
    internal bool TweakSheet(CharacterSheet s, IWin32Window owner)
    {
        using var f = new Form
        {
            Width = 700, Height = 760, Text = $"Tweak — {s.Name}",
            StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = true,
            ShowIcon = false, BackColor = Paper, MinimumSize = new Size(560, 480)
        };

        var scroll = new Panel { Dock = DockStyle.Fill, AutoScroll = true, Padding = new Padding(12) };
        var grid = new TableLayoutPanel
        {
            Dock = DockStyle.Top, AutoSize = true, ColumnCount = 4,
            Padding = new Padding(0, 0, 18, 0)
        };
        grid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 118));
        grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        grid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 118));
        grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));

        int row = 0;
        Label L(string t) => new() { Text = t, AutoSize = true, Padding = new Padding(0, 8, 4, 2), ForeColor = Ink };
        void Pair(string label, Control c, string label2 = null, Control c2 = null)
        {
            grid.Controls.Add(L(label), 0, row);
            c.Anchor = AnchorStyles.Left | AnchorStyles.Right;
            grid.Controls.Add(c, 1, row);
            if (label2 != null)
            {
                grid.Controls.Add(L(label2), 2, row);
                c2.Anchor = AnchorStyles.Left | AnchorStyles.Right;
                grid.Controls.Add(c2, 3, row);
            }
            row++;
        }
        void Wide(string label, Control c)
        {
            grid.Controls.Add(L(label), 0, row);
            c.Anchor = AnchorStyles.Left | AnchorStyles.Right;
            grid.Controls.Add(c, 1, row);
            grid.SetColumnSpan(c, 3);
            row++;
        }
        NumericUpDown Num(int val, int min, int max)
            => new() { Minimum = min, Maximum = max, Value = Math.Clamp(val, min, max), Width = 70, Margin = new Padding(3, 5, 3, 3) };
        TextBox Multi(IEnumerable<string> lines, int h) => new()
        {
            Multiline = true, Height = h, ScrollBars = ScrollBars.Vertical, WordWrap = false,
            Text = string.Join(Environment.NewLine, lines), Font = new Font("Consolas", 9.5f),
            Margin = new Padding(3, 5, 3, 3)
        };

        var name = new TextBox { Text = s.Name, Margin = new Padding(3, 5, 3, 3) };
        var gender = new ComboBox { Text = s.Gender ?? "", DropDownStyle = ComboBoxStyle.DropDown, Margin = new Padding(3, 5, 3, 3) };
        gender.Items.AddRange(new object[] { "Woman", "Man" });
        Pair("Name", name, "Gender", gender);

        var scores = new Dictionary<string, NumericUpDown>();
        string[] abs = { "STR", "DEX", "CON", "WIT", "RES", "PRE" };
        for (int i = 0; i < 6; i += 2)
        {
            scores[abs[i]] = Num(s.Scores.TryGetValue(abs[i], out var v1) ? v1 : 10, 1, 24);
            scores[abs[i + 1]] = Num(s.Scores.TryGetValue(abs[i + 1], out var v2) ? v2 : 10, 1, 24);
            Pair(abs[i], scores[abs[i]], abs[i + 1], scores[abs[i + 1]]);
        }

        var blood = Num(s.Blood, 1, 999); var defense = Num(s.Defense, 1, 40);
        Pair("Blood (max)", blood, "Defense", defense);
        var fort = Num(s.Fort, -10, 30); var reff = Num(s.Ref, -10, 30);
        Pair("Fortitude", fort, "Reflex", reff);
        var will = Num(s.Will, -10, 30); var nerve = Num(s.NerveMax, 1, 99);
        Pair("Will", will, "Nerve (max)", nerve);
        var grit = Num(s.Grit, 0, 9); var speed = Num(s.Speed, 0, 120);
        Pair("Grit", grit, "Speed (ft)", speed);
        var mark = Num(s.Mark, 0, 6);
        var coin = new NumericUpDown { Minimum = 0, Maximum = 99999, DecimalPlaces = 2, Value = (decimal)Math.Max(0, s.CoinLeft), Width = 90, Margin = new Padding(3, 5, 3, 3) };
        Pair("Mark", mark, "Coin left ($)", coin);

        string RankSuffix(int r) => r >= 3 ? " (Master)" : r == 2 ? " (Expert)" : "";
        var skills = Multi(s.SkillRanks.OrderByDescending(kv => kv.Value).ThenBy(kv => kv.Key)
            .Select(kv => kv.Key + RankSuffix(kv.Value)), 96);
        Tip.SetToolTip(skills, "One skill per line — add (Expert) or (Master) after the name for higher ranks");
        Wide("Skills", skills);

        var edges = Multi(s.Edges, 76);
        Wide("Edges", edges);
        TextBox gunEdges = null;
        if (s.BonusCombatEdges.Count > 0)
        {
            gunEdges = Multi(s.BonusCombatEdges, 56);
            Wide("Gunhand's Edges", gunEdges);
        }
        TextBox signs = null;
        if (s.SignsKnown.Count > 0 || CharGen.D.callings.FirstOrDefault(c => c.name == s.Calling)?.signsKnownAt != null)
        {
            signs = Multi(s.SignsKnown, 56);
            Wide("Signs known", signs);
        }
        var features = Multi(s.Features, 76);
        Wide("Features", features);
        var weapons = Multi(s.WeaponsCarried, 56);
        Wide("Arms carried", weapons);
        var gear = Multi(s.Gear, 96);
        Wide("Gear", gear);

        var lost = new TextBox { Text = s.Lost, Margin = new Padding(3, 5, 3, 3) };
        Wide("Lost", lost);
        var seen = new TextBox { Text = s.Seen, Margin = new Padding(3, 5, 3, 3) };
        Wide("Seen", seen);
        var vice = new TextBox { Text = s.Vice, Margin = new Padding(3, 5, 3, 3) };
        Wide("Vice", vice);
        var moving = new TextBox { Text = s.Moving, Margin = new Padding(3, 5, 3, 3) };
        Wide("Moving", moving);
        var compass = new TextBox { Text = s.Compass, Margin = new Padding(3, 5, 3, 3) };
        Wide("Compass", compass);

        scroll.Controls.Add(grid);

        var bar = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 46, FlowDirection = FlowDirection.RightToLeft, Padding = new Padding(8) };
        var cancel = new Button { Text = "Cancel", Width = 88, Height = 30, DialogResult = DialogResult.Cancel };
        var ok = new Button { Text = "Apply", Width = 88, Height = 30, DialogResult = DialogResult.OK };
        bar.Controls.Add(cancel); bar.Controls.Add(ok);
        var note = new Label
        {
            Dock = DockStyle.Bottom, Height = 34, ForeColor = Gold, Padding = new Padding(12, 2, 4, 2),
            Font = new Font("Segoe UI", 8.8f, FontStyle.Italic),
            Text = "Hand tweaks are the Keeper's word against the book's — the sheet is re-checked but never blocked;\nthe Ledger simply notes it was tweaked."
        };
        f.Controls.Add(scroll); f.Controls.Add(note); f.Controls.Add(bar);
        f.AcceptButton = ok; f.CancelButton = cancel;

        if (f.ShowDialog(owner) != DialogResult.OK) return false;

        static List<string> Lines(TextBox t) =>
            t == null ? new() : t.Text.Split('\n').Select(x => x.Trim('\r').Trim()).Where(x => x.Length > 0).ToList();

        s.Name = string.IsNullOrWhiteSpace(name.Text) ? s.Name : name.Text.Trim();
        s.Gender = gender.Text.Trim();
        foreach (var a in abs) s.Scores[a] = (int)scores[a].Value;
        s.Blood = (int)blood.Value; s.Defense = (int)defense.Value;
        s.Fort = (int)fort.Value; s.Ref = (int)reff.Value; s.Will = (int)will.Value;
        s.NerveMax = (int)nerve.Value; s.Grit = (int)grit.Value; s.Speed = (int)speed.Value;
        s.Mark = (int)mark.Value; s.CoinLeft = (double)coin.Value;

        s.SkillRanks.Clear();
        foreach (var line in Lines(skills))
        {
            int rank = line.Contains("(Master)") ? 3 : line.Contains("(Expert)") ? 2 : 1;
            string nm = line.Replace("(Master)", "").Replace("(Expert)", "").Trim();
            if (nm.Length > 0) s.SkillRanks[nm] = rank;
        }
        s.Edges = Lines(edges);
        if (gunEdges != null) s.BonusCombatEdges = Lines(gunEdges);
        if (signs != null) s.SignsKnown = Lines(signs);
        s.Features = Lines(features);
        s.WeaponsCarried = Lines(weapons);
        s.Gear = Lines(gear);
        s.Lost = lost.Text.Trim(); s.Seen = seen.Text.Trim();
        s.Vice = vice.Text.Trim(); s.Moving = moving.Text.Trim();
        s.Compass = compass.Text.Trim();
        s.HandTweaked = true;
        return true;
    }
}
