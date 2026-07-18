namespace BloodAndGritKeeper;

public partial class MainForm
{
    // ============================================================ NEW SOUL TAB
    // A whole character sheet at the press of a button, walked through Chapter III's
    // eight steps against Data/chargen.json (transcribed from the Player's Book) and
    // re-validated by CharGen.Validate before it is ever shown — the generator is not
    // allowed to hand the Keeper a character the book couldn't have made.
    RichTextBox soulOut;
    NumericUpDown soulLevel;
    ComboBox soulMethod, soulCalling, soulOrigin;
    CharacterSheet lastSoul;

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
        bar.Controls.Add(Btn("→ Posse", (s, e) => SoulToPosse(), 85, "Add this soul to the Posse tab"));
        bar.Controls.Add(Btn("Copy sheet", (s, e) => { if (!string.IsNullOrEmpty(soulOut.Text)) Clipboard.SetText(soulOut.Text); }, 95));
        bar.Controls.Add(Btn("Clear", (s, e) => { soulOut.Clear(); lastSoul = null; }, 70, "Wipe the sheet for a fresh start"));

        soulOut = new RichTextBox { Dock = DockStyle.Fill, ReadOnly = true, BorderStyle = BorderStyle.None, BackColor = Color.FromArgb(252, 249, 240), Font = new Font("Consolas", 10f) };

        var hint = new Label
        {
            Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleCenter,
            Font = new Font("Segoe UI", 11f, FontStyle.Italic), ForeColor = Gold, BackColor = Paper,
            Text = "Eight steps from a blank page to a soul worth losing —\nrolled for you, strictly by the book.\n\n" +
                   "Pick a level and (if you care to) a Calling and Origin, then Make a soul.\n" +
                   "Every sheet is checked against the rules before it reaches you:\n" +
                   "abilities, saves, skills, Edges and their requirements, Signs, coin and all.\n\n" +
                   "Like one? Send them to the Posse, or copy the sheet out."
        };
        page.Controls.Add(Pad(soulOut, 16));
        page.Controls.Add(hint);
        page.Controls.Add(bar);
        hint.BringToFront();
        soulOut.TextChanged += (s, e) => hint.Visible = soulOut.TextLength == 0;
        Watermark(hint, () => HintBottom(hint));
        return page;
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
        var violations = CharGen.Validate(sheet);
        lastSoul = sheet;

        soulOut.Clear();
        soulOut.SelectionFont = new Font("Consolas", 10f);
        soulOut.SelectionColor = Ink;
        soulOut.AppendText(CharGen.Render(sheet));
        if (violations.Count > 0)
        {
            // should never happen — the smoke suite proves the generator conformant — but if it
            // ever does, the Keeper sees it plainly instead of trusting a broken sheet
            soulOut.SelectionColor = Blood;
            soulOut.AppendText("\n⚠ RULES CHECK FAILED:\n   " + string.Join("\n   ", violations) + "\n");
        }
        soulOut.SelectionStart = 0; soulOut.ScrollToCaret();
        Log($"New soul: {sheet.Name}, {sheet.Calling} ({sheet.Origin}), level {sheet.Level}.");
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
            Notes = s.Origin + (s.Subpath != null ? " · " + s.Subpath : "")
        };
        if (p.NerveMax != s.NerveMax) { p.NerveMax = s.NerveMax; p.NerveCur = s.NerveMax; }   // Stone Nerve
        party.Add(p);
        Log($"{s.Name} joins the posse.");
    }
}
