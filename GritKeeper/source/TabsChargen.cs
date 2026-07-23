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
        bar.Controls.Add(Btn("Clear", (s, e) =>
        {
            if (lastSoul == null) return;
            if (!Confirm($"Clear {lastSoul.Name}'s sheet? Unsaved work is lost.")) return;
            soulLedger.Clear(); lastSoul = null; soulHint.Visible = true;
        }, 70, "Wipe the sheet for a fresh start"));

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
            Name = s.Name, Calling = s.Calling, Gender = s.Gender, Level = s.Level,
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

    // ============================================================ LEVEL UP
    // Advance one seated soul by a single level, choosing what the new level unlocks. The
    // heavy lifting (and every rule) lives in CharGen.LevelUp; this is just the picker. Any
    // choice left on "(let the book choose)" is drawn the way Generate would, and
    // CharGen.LevelUp re-draws anything that turns out illegal.
    //
    // Every road out of here that ISN'T a level-up says so in a dialog. It used to write the
    // reason to the roll log and return, which — on the far side of the screen from the
    // button, in a list that scrolls — is indistinguishable from a button that does nothing.
    internal void LevelUpMember(PartyMember p, IWin32Window owner)
    {
        if (p == null)
        {
            MessageBox.Show(owner, "Pick a soul on the Posse table first, then level them up.",
                "Level up", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        if (p.Level >= 10)
        {
            MessageBox.Show(owner,
                $"{p.Name} already stands at 10th level — the frontier's ceiling. There's nothing "
                + "above it in the book.",
                "Level up — at the ceiling", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        if (p.Sheet == null && !BackfillSheet(p, owner)) return;
        var cur = p.Sheet;
        var g = CharGen.PreviewLevelUp(cur);
        if (g.AtCeiling)
        {
            MessageBox.Show(owner,
                $"{p.Name}'s sheet already stands at 10th level — the frontier's ceiling.",
                "Level up — at the ceiling", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        using var f = new Form
        {
            Text = $"Level up — {cur.Name}", Width = 520, AutoSize = true,
            AutoSizeMode = AutoSizeMode.GrowAndShrink, FormBorderStyle = FormBorderStyle.FixedDialog,
            StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false,
            ShowIcon = false, BackColor = Paper
        };
        var tbl = new TableLayoutPanel
        {
            Dock = DockStyle.Fill, ColumnCount = 2, AutoSize = true, Padding = new Padding(14),
            GrowStyle = TableLayoutPanelGrowStyle.AddRows
        };
        tbl.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        tbl.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        void Row(string label, Control c)
        {
            tbl.Controls.Add(new Label { Text = label, AutoSize = true, Margin = new Padding(3, 8, 10, 3), ForeColor = Ink });
            c.Margin = new Padding(3, 5, 3, 3);
            tbl.Controls.Add(c);
        }
        void Span(Control c) { tbl.Controls.Add(c); tbl.SetColumnSpan(c, 2); }
        ComboBox Choice(List<string> opts, int width = 260)
        {
            var cb = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = width };
            cb.Items.Add("(let the book choose)");
            foreach (var o in opts) cb.Items.Add(o);
            cb.SelectedIndex = 0;
            return cb;
        }

        Span(new Label { Text = $"{cur.Calling}   ·   Level {cur.Level} → {g.NewLevel}", AutoSize = true,
            Font = new Font(Font, FontStyle.Bold), ForeColor = Blood, Margin = new Padding(3, 0, 3, 8) });

        // Blood — roll the new level's Hit Die (or set the face), CON mod added automatically
        var dieUp = new NumericUpDown { Minimum = 1, Maximum = g.HitDie, Width = 55 };
        dieUp.Value = Rules.Rng.Next(1, g.HitDie + 1);
        var totalLbl = new Label { AutoSize = true, ForeColor = Ink, Margin = new Padding(8, 8, 3, 3) };
        void RefreshTotal() => totalLbl.Text =
            $"= +{(int)dieUp.Value + g.ConModForBlood} Blood   (d{g.HitDie} rolled {(int)dieUp.Value}, CON {(g.ConModForBlood >= 0 ? "+" : "")}{g.ConModForBlood})";
        dieUp.ValueChanged += (s, e) => RefreshTotal(); RefreshTotal();
        var bloodPanel = new FlowLayoutPanel { AutoSize = true, FlowDirection = FlowDirection.LeftToRight, Margin = new Padding(0), WrapContents = false };
        bloodPanel.Controls.Add(dieUp);
        bloodPanel.Controls.Add(Btn("Roll", (s, e) => dieUp.Value = Rules.Rng.Next(1, g.HitDie + 1), 50, "Roll the new level's Hit Die"));
        bloodPanel.Controls.Add(totalLbl);
        Row("Blood gain:", bloodPanel);

        ComboBox boostCb = null, edgeCb = null, gunCb = null, skillCb = null, subCb = null;
        var signCbs = new List<ComboBox>();

        if (g.Boost)
        {
            boostCb = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 120 };
            foreach (var a in g.BoostOptions) boostCb.Items.Add(a);
            boostCb.SelectedItem = g.DefaultBoost;
            Row("Ability boost (+1):", boostCb);
        }
        if (g.Edge) { edgeCb = Choice(g.EdgeOptions); Row("New Edge:", edgeCb); }
        if (g.GunEdge) { gunCb = Choice(g.GunEdgeOptions); Row("Gunhand's combat Edge:", gunCb); }
        if (g.SkillIncrease)
        {
            skillCb = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 260 };
            skillCb.Items.Add("(let the book choose)");
            foreach (var sk in g.SkillOptions)
            {
                int r = cur.SkillRanks.TryGetValue(sk, out var rr) ? rr : 0;
                skillCb.Items.Add($"{sk} ({(r == 0 ? "train" : r == 1 ? "→ Expert" : "→ Master")})");
            }
            skillCb.SelectedIndex = 0;
            Row("Skill increase:", skillCb);
        }
        if (g.Subpath)
        {
            subCb = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 260 };
            foreach (var o in g.SubpathOptions) subCb.Items.Add(o);
            subCb.SelectedIndex = 0;
            string section = CharGen.D.callings.First(c => c.name == cur.Calling).subpath.section;
            Row($"{section}:", subCb);
        }
        for (int i = 0; i < g.NewSignSlots; i++)
        {
            var sc = Choice(g.SignOptions);
            signCbs.Add(sc);
            Row(g.NewSignSlots == 1 ? "New Sign:" : $"New Sign {i + 1}:", sc);
        }

        var okBtn = new Button { Text = "Level up", DialogResult = DialogResult.OK, AutoSize = true, Margin = new Padding(6, 10, 3, 3) };
        var cancelBtn = new Button { Text = "Cancel", DialogResult = DialogResult.Cancel, AutoSize = true, Margin = new Padding(6, 10, 3, 3) };
        f.AcceptButton = okBtn; f.CancelButton = cancelBtn;
        var btnPanel = new FlowLayoutPanel { FlowDirection = FlowDirection.RightToLeft, AutoSize = true, Dock = DockStyle.Fill, Margin = new Padding(0) };
        btnPanel.Controls.Add(okBtn); btnPanel.Controls.Add(cancelBtn);
        Span(btnPanel);

        f.Controls.Add(tbl);
        if (f.ShowDialog(owner) != DialogResult.OK) return;

        var ch = new CharGen.LevelUpChoices { BloodDie = (int)dieUp.Value };
        if (boostCb != null) ch.Boost = (string)boostCb.SelectedItem;
        if (edgeCb != null && edgeCb.SelectedIndex > 0) ch.Edge = (string)edgeCb.SelectedItem;
        if (gunCb != null && gunCb.SelectedIndex > 0) ch.BonusCombatEdge = (string)gunCb.SelectedItem;
        if (skillCb != null && skillCb.SelectedIndex > 0) ch.SkillIncrease = g.SkillOptions[skillCb.SelectedIndex - 1];
        if (subCb != null) ch.Subpath = (string)subCb.SelectedItem;
        foreach (var sc in signCbs) if (sc.SelectedIndex > 0) ch.NewSigns.Add((string)sc.SelectedItem);

        // apply: swap in the grown sheet, resync the row, then grant the new level's Blood &
        // Nerve to *current* too (leveling isn't a heal, but the new capacity is theirs).
        int oldBloodMax = p.BloodMax, oldNerveMax = p.NerveMax;
        var next = CharGen.LevelUp(cur, ch);
        p.Sheet = next;
        SyncMemberFromSheet(p);
        int bloodGain = p.BloodMax - oldBloodMax; if (bloodGain > 0) p.BloodCur = Math.Min(p.BloodMax, p.BloodCur + bloodGain);
        int nerveGain = p.NerveMax - oldNerveMax; if (nerveGain > 0) p.NerveCur = Math.Min(p.NerveMax, p.NerveCur + nerveGain);
        posseGrid?.Refresh();
        if (soulWindows.TryGetValue(p, out var win) && !win.IsDisposed)
            foreach (var lv in win.Controls.OfType<LedgerView>()) lv.ShowSheet(next, p, SheetWarnings(next));
        Log($"{next.Name} rises to {Ordinal(next.Level)} level — +{bloodGain} Blood."
            + (next.Edges.Count > cur.Edges.Count ? $"  New Edge: {next.Edges[^1]}." : "")
            + (next.SignsKnown.Count > cur.SignsKnown.Count ? $"  New Sign: {next.SignsKnown[^1]}." : "")
            + (next.Subpath != null && cur.Subpath == null ? $"  Path: {next.Subpath}." : ""));
    }

    static string Ordinal(int n) => n + (n % 100 is >= 11 and <= 13 ? "th"
        : (n % 10) switch { 1 => "st", 2 => "nd", 3 => "rd", _ => "th" });

    // ------------------------------------------------------------ SHEETLESS SOULS
    // A posse row with no CharacterSheet can't level: there's nothing to grow. Two ways a
    // row ends up that way — a Keeper typed it in by hand, or (the one that bit us) it was
    // seeded by a build older than v1.9.0, when the first-launch demo posse was bare rows
    // rather than full sheets. Those rows persist in session.json forever, so the ✦ Level up
    // button quietly did nothing for the six souls most Keepers actually have seated. It used
    // to say so in the roll log only, which reads as a dead button, not as an explanation.
    //
    // So offer the repair instead of the complaint: draw a book-legal sheet for their Calling
    // at their current level and hang it on the row. Returns true when the soul now has a
    // sheet and the level-up may proceed.
    bool BackfillSheet(PartyMember p, IWin32Window owner)
    {
        bool known = !string.IsNullOrWhiteSpace(p.Calling)
                     && CharGen.D.callings.Any(c => c.name == p.Calling);
        if (!known)
        {
            MessageBox.Show(owner,
                $"{p.Name} has no character sheet, and \"{p.Calling}\" isn't one of the seventeen "
                + "Callings in Chapter IV — so there's no table to grow them by.\r\n\r\n"
                + "Set their Calling on the Posse tab to a Calling from the book, or build them "
                + "on the New Soul tab, and they'll level by the book from then on.",
                "Level up — no sheet to grow",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
            return false;
        }

        var answer = MessageBox.Show(owner,
            $"{p.Name} is a hand-entered row — no character sheet behind it, so there's nothing "
            + "for the book to advance.\r\n\r\n"
            + $"Draw one up now? GritKeeper will roll a rules-legal {p.Calling} at "
            + $"{Ordinal(p.Level)} level, keeping their name and gender, and then level them.\r\n\r\n"
            + "Their Blood, Nerve, Defense and saves will be replaced by the new sheet's numbers "
            + "(current Blood and Nerve stay where they are, capped at the new maximums). "
            + "Notes and Grit are untouched.",
            "Level up — draw up a sheet?",
            MessageBoxButtons.YesNo, MessageBoxIcon.Question);
        if (answer != DialogResult.Yes) return false;

        int bloodCur = p.BloodCur, nerveCur = p.NerveCur;
        var s = CharGen.Generate(Math.Clamp(p.Level, 1, 10), rolled: false, fixedCalling: p.Calling);
        s.Name = p.Name;
        // Keep the row's gender; where the row has none — every pre-v1.9.0 demo row — leave it
        // blank rather than let the generator's coin-flip write one in. Ruth "Six-Finger"
        // Calloway coming back from this as a Man is worse than her coming back unstated.
        s.Gender = p.Gender ?? "";
        p.Sheet = s;
        SyncMemberFromSheet(p);
        p.BloodCur = Math.Min(bloodCur, p.BloodMax);
        p.NerveCur = Math.Min(nerveCur, p.NerveMax);
        posseGrid?.Refresh();
        Log($"{p.Name} gets a sheet — a {Ordinal(s.Level)}-level {s.Calling} out of {s.Origin}.");
        return true;
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
