using System.Text.Json;

namespace BloodAndGritKeeper;

// The menu bar and everything it opens: session save/load, the five-minute lesson,
// keyboard shortcuts, and the About box.
public partial class MainForm
{
    // ---------------------------------------------------------- menu bar
    MenuStrip BuildMenu(TabControl tabs)
    {
        static ToolStripMenuItem Item(string text, EventHandler click, Keys keys = Keys.None, string shortcutText = null)
        {
            var it = new ToolStripMenuItem(text);
            if (click != null) it.Click += click;
            if (keys != Keys.None) it.ShortcutKeys = keys;
            if (shortcutText != null) it.ShortcutKeyDisplayString = shortcutText;
            return it;
        }

        var menu = new MenuStrip { BackColor = Paper, Font = new Font("Segoe UI", 9.5f), Padding = new Padding(8, 4, 0, 4) };

        var file = new ToolStripMenuItem("&File");
        file.DropDownItems.Add(Item("&Save session", (s, e) => { AutoSave(); Log("Session saved."); }, Keys.Control | Keys.S));
        file.DropDownItems.Add(Item("Save session &as…", (s, e) => SaveSessionAs(), Keys.Control | Keys.Shift | Keys.S));
        file.DropDownItems.Add(Item("&Load session…", (s, e) => LoadSessionFromFile(), Keys.Control | Keys.O));
        file.DropDownItems.Add(new ToolStripSeparator());
        file.DropDownItems.Add(Item("E&xit", (s, e) => Close(), shortcutText: "Alt+F4"));
        menu.Items.Add(file);

        // one entry per tab, so the Ctrl+number shortcuts are discoverable
        var view = new ToolStripMenuItem("&View");
        for (int i = 0; i < tabs.TabPages.Count; i++)
        {
            int idx = i;
            view.DropDownItems.Add(Item(tabs.TabPages[i].Text,
                (s, e) => tabs.SelectedIndex = idx, shortcutText: $"Ctrl+{i + 1}"));
        }
        menu.Items.Add(view);

        var help = new ToolStripMenuItem("&Help");
        help.DropDownItems.Add(Item("The &five-minute lesson", (s, e) => ShowLesson(), Keys.F1));
        help.DropDownItems.Add(Item("&Keyboard shortcuts", (s, e) => ShowShortcuts()));
        help.DropDownItems.Add(new ToolStripSeparator());
        help.DropDownItems.Add(Item("&About The Keeper's Table…", (s, e) => ShowAbout()));
        menu.Items.Add(help);

        return menu;
    }

    // ---------------------------------------------------------- save / load to a chosen file
    void SaveSessionAs()
    {
        using var d = new SaveFileDialog
        {
            Title = "Save the session",
            Filter = "Keeper's Table session (*.json)|*.json|All files (*.*)|*.*",
            FileName = $"blood-and-grit-session-{DateTime.Now:yyyy-MM-dd}.json"
        };
        if (d.ShowDialog(this) != DialogResult.OK) return;
        try
        {
            File.WriteAllText(d.FileName, JsonSerializer.Serialize(Snapshot(), new JsonSerializerOptions { WriteIndented = true }));
            Log($"Session saved to {Path.GetFileName(d.FileName)}.");
        }
        catch (Exception ex)
        {
            MessageBox.Show("Couldn't save there:\r\n\r\n" + ex.Message, "Blood & Grit",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    void LoadSessionFromFile()
    {
        using var d = new OpenFileDialog
        {
            Title = "Load a session",
            Filter = "Keeper's Table session (*.json)|*.json|All files (*.*)|*.*"
        };
        if (d.ShowDialog(this) != DialogResult.OK) return;
        GameSession s;
        try
        {
            s = JsonSerializer.Deserialize<GameSession>(File.ReadAllText(d.FileName));
            if (s == null) throw new InvalidDataException("the file is empty");
        }
        catch (Exception ex)
        {
            MessageBox.Show("That file doesn't read as a Keeper's Table session.\r\n\r\n" + ex.Message,
                "Blood & Grit", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        if (!Confirm("Load this session? The whole table — posse, tracker, encounter, threads, ledger — " +
                     "is replaced.\n\n(The table as it stands now is kept as session-backup.json beside the app.)"))
            return;
        try
        {
            File.WriteAllText(Path.Combine(AppContext.BaseDirectory, "session-backup.json"),
                JsonSerializer.Serialize(Snapshot(), new JsonSerializerOptions { WriteIndented = true }));
        }
        catch { /* the backup is best-effort — never block a load over it */ }
        ApplySession(s);
        AutoSave();
        Log($"Session loaded from {Path.GetFileName(d.FileName)}.");
    }

    // ---------------------------------------------------------- help windows
    // Modeless and reused, like the creature cards — read the lesson beside the live table.
    Form lessonWin, shortcutsWin;

    static Form HelpWindow(ref Form slot, string title, int w, int h)
    {
        if (slot != null && !slot.IsDisposed) { slot.BringToFront(); slot.Activate(); return null; }
        var win = new Form
        {
            Text = title, Width = w, Height = h, BackColor = Paper,
            MinimumSize = new Size(420, 360), StartPosition = FormStartPosition.CenterScreen
        };
        if (AppIcon != null) win.Icon = AppIcon;
        slot = win;
        return win;
    }

    void ShowLesson()
    {
        var win = HelpWindow(ref lessonWin, "The Five-Minute Lesson", 760, 780);
        if (win == null) return;

        var rtf = new RichTextBox { ReadOnly = true, BorderStyle = BorderStyle.None, BackColor = Paper, Font = new Font("Segoe UI", 10f) };
        var bar = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 42, Padding = new Padding(4, 2, 4, 2), BackColor = Color.FromArgb(243, 237, 221) };
        bar.Controls.Add(Btn("A−", (s, e) => rtf.ZoomFactor = Math.Max(0.7f, rtf.ZoomFactor - 0.15f), 46, "Smaller text"));
        bar.Controls.Add(Btn("A＋", (s, e) => rtf.ZoomFactor = Math.Min(3f, rtf.ZoomFactor + 0.15f), 46, "Larger text"));

        void H(string s) { rtf.SelectionFont = new Font("Segoe UI", 12.5f, FontStyle.Bold); rtf.SelectionColor = Blood; rtf.AppendText(s + "\n"); }
        void T(string s) { rtf.SelectionFont = new Font("Segoe UI", 10f); rtf.SelectionColor = Ink; rtf.AppendText(s + "\n\n"); }
        void I(string s) { rtf.SelectionFont = new Font("Segoe UI", 9.7f, FontStyle.Italic); rtf.SelectionColor = Gold; rtf.AppendText(s + "\n\n"); }

        H("The Keeper's Table, in five minutes");
        I("Everything a Keeper reaches for mid-scene, in nine tabs. Ctrl+1 through Ctrl+9 jump straight to them. " +
          "Nothing here invents rules — every number, table, and creature is taken word-for-word from the books.");

        H("1 · Seat the posse  (Posse)");
        T("The party sheet. Add each soul's Blood, Defense, saves, Nerve, Grit, Mark, and Taint — or click straight " +
          "into a cell to edit it. The buttons along the top do the bookkeeping: Damage and Heal apply the Amount " +
          "spinner to the selected soul, Spend Grit counts it down, and Dread check rolls a Will save against the DC " +
          "you set, taking the Nerve loss by the horror's Tier automatically. \"New session\" refills Nerve and " +
          "resets Grit to 3; Rest ▾ is the long rest. On first run the six ready-made souls from Appendix D are " +
          "already seated — clear them out whenever your own posse is ready.");

        H("2 · Roll anything  (Dice)");
        T("Type an expression — 2d6+3, 1d8+1d6+2 — and press Enter, or punch it in with the buttons: the +d buttons " +
          "add dice (click one twice and it stacks: d6, 2d6, 3d6), the digits and ＋/− build the modifier. The dice " +
          "tumble in the tray and land on the true results. Below that, the d20 checker rolls a full four-degrees " +
          "check against a DC. Everything the app ever rolls — here or on any other tab — lands in the log on the " +
          "right, so there is always a paper trail.");

        H("3 · Know your horrors  (Bestiary)");
        T("All 110 creatures from the book, word for word. Search by name or haunt, filter by tier or chapter. " +
          "Double-click a creature (or hit ⧉ Pop out) to open it in its own window — open several side by side and " +
          "size the text to the light in the room. From here one click sends a creature to the Encounter builder or " +
          "drops N copies straight onto the Tracker.");

        H("4 · Weigh the fight  (Encounter)");
        T("The book's Long Odds math, live. Add creatures, set the party's level, and the bar at the bottom says " +
          "plainly whether the fight is fair, mean, or a massacre — the budget is 4 points per soul seated on the " +
          "Posse tab. When a horror stands two or more Tiers over the posse, the safe-table rule flags it in red: " +
          "it arrives as sign and spoor, not in the flesh. Happy with the odds? Send all → Tracker.");

        H("5 · Run the fight  (Tracker)");
        T("Roll initiative for the whole field with one click, step the rounds, deal damage with the Amt spinner, " +
          "and tag conditions from Appendix B with ＋ Condition ▾. Posse rows stay green, foes cream, the fallen red. " +
          "Blood is synced two ways with the Posse sheet — hurt a soul here and the party sheet knows, and the other " +
          "way around. \"New fight\" clears the foes and keeps the posse; double-click any foe to open its stat block.");

        H("6 · Deal a new soul  (New Soul)");
        T("A complete character, rolled strictly by Chapter III's eight steps at any level 1–10 — abilities, Calling, " +
          "Origin, skills, Edges, Signs, coin and gear, all cross-checked against the rules before the sheet reaches " +
          "you. Pin the Calling or Origin if you have one in mind, or let the country deal. → Posse seats them at " +
          "the table; Copy sheet takes the text anywhere.");

        H("7 · When the trail runs dry  (Generators)");
        T("Every rollable table from The Country in Your Pocket: a town in three rolls, a face in four, rumors, " +
          "trail events, plunder, omens — and the Grounds tables, an encounter for any terrain with the safe-table " +
          "rule applied automatically. One click, and the country answers.");

        H("8 · The rules at your elbow  (Reference)");
        T("A Keeper's screen in eleven leaves — the four degrees, the DC ladder, the Iron Code, wounds, every " +
          "condition, Nerve and Dread, the Mark and the Taint, Signs and Grit, the Long Odds, and the book's own " +
          "arms, goods, and skills tables. Turn the deck with the ◀ ▶ buttons or the Left and Right arrow keys. " +
          "When a ruling is needed and the book is across the room, it's here.");

        H("9 · Keep the record  (Session)");
        T("The Keeper's ledger for notes — Stamp the date starts each session's entry — and threads with clocks " +
          "beside it. A thread is trouble on its way: name it, give it 4, 6, or 8 segments, and tick ＋ when the " +
          "world moves toward it. When the last segment fills, it comes due.");

        H("Saving — you mostly don't have to think about it");
        T("The whole table auto-saves beside the app on exit and every five minutes, and reloads when you return. " +
          "File → Save session (Ctrl+S) saves that same file on demand. Save session as… writes the table to a file " +
          "of your choosing — end-of-campaign archives, or a second campaign — and Load session… brings one back " +
          "(the table you're replacing is kept as session-backup.json, just in case).");

        H("The habit that makes it sing");
        T("Before the game: seat the posse, weigh the night's fight on the Encounter tab, set a thread or two. " +
          "During: run everything from the Tracker and the Dice tab, and let the log remember for you. " +
          "After: stamp the date, write three lines in the ledger, tick the clocks. That's the whole craft — " +
          "the rest is nerve.");

        rtf.SelectionStart = 0; rtf.ScrollToCaret();
        win.Controls.Add(Pad(rtf, 18));
        win.Controls.Add(bar);
        win.Show(this);
    }

    void ShowShortcuts()
    {
        var win = HelpWindow(ref shortcutsWin, "Keyboard Shortcuts", 560, 520);
        if (win == null) return;

        var rtf = new RichTextBox { ReadOnly = true, BorderStyle = BorderStyle.None, BackColor = Paper, Font = new Font("Consolas", 10f) };
        void H(string s) { rtf.SelectionFont = new Font("Segoe UI", 12f, FontStyle.Bold); rtf.SelectionColor = Blood; rtf.AppendText(s + "\n"); }
        void M(string s) { rtf.SelectionFont = new Font("Consolas", 10f); rtf.SelectionColor = Ink; rtf.AppendText(s + "\n"); }

        H("Anywhere");
        M("  Ctrl+1 … Ctrl+9   Jump to a tab (in bar order)");
        M("  Ctrl+S            Save the session now");
        M("  Ctrl+Shift+S      Save the session to a file…");
        M("  Ctrl+O            Load a session from a file…");
        M("  F1                The five-minute lesson");
        M("");
        H("Posse");
        M("  Ctrl+D / Ctrl+H   Damage / Heal the selected soul (by the Amount)");
        M("  Delete            Remove the selected soul");
        M("  F2 (or type)      Edit the selected cell");
        M("");
        H("Tracker");
        M("  Ctrl+I            Roll initiative for the field");
        M("  Ctrl+R            Next round");
        M("  Ctrl+D / Ctrl+H   Damage / Heal the selected combatant (by the Amt)");
        M("  Delete            Remove the selected combatant");
        M("");
        H("Bestiary & pickers");
        M("  Ctrl+F            Jump to the search box");
        M("  Enter / dbl-click Pop the creature out into its own window");
        M("  Enter             Add the typed creature (Encounter/Tracker pickers)");
        M("");
        H("Dice");
        M("  Enter             Roll the expression in the box");
        M("");
        H("Reference");
        M("  Left / Right      Turn the deck (or click ◀ ▶)");
        M("");
        H("Everything else");
        M("  Hover any button — every control carries a tooltip.");

        rtf.SelectionStart = 0; rtf.ScrollToCaret();
        win.Controls.Add(Pad(rtf, 18));
        win.Show(this);
    }

    void ShowAbout()
    {
        using var f = new Form
        {
            Width = 520, Height = 420, Text = "About The Keeper's Table",
            FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent,
            MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper
        };
        var pic = new PictureBox
        {
            Image = Emblem, SizeMode = PictureBoxSizeMode.Zoom,
            Left = 110, Top = 20, Width = 280, Height = 145
        };
        var title = new Label
        {
            Text = "Blood & Grit — The Keeper's Table", AutoSize = false, TextAlign = ContentAlignment.MiddleCenter,
            Left = 0, Top = 178, Width = 504, Height = 30, Font = new Font("Segoe UI", 13f, FontStyle.Bold), ForeColor = Blood
        };
        var ver = new Label
        {
            Text = $"Version {AppVersion}\nPlayer's Book v2.14  ·  Keeper's Book v2.6  ·  Bestiary v2.6",
            AutoSize = false, TextAlign = ContentAlignment.MiddleCenter,
            Left = 0, Top = 212, Width = 504, Height = 40, ForeColor = Ink
        };
        var blurb = new Label
        {
            Text = "The companion app to Blood & Grit,\na roleplaying game of the haunted frontier.\n\n© 2026 Cole Williams",
            AutoSize = false, TextAlign = ContentAlignment.MiddleCenter,
            Left = 0, Top = 260, Width = 504, Height = 80, ForeColor = Ink
        };
        var ok = new Button { Text = "Ride on", Left = 208, Top = 344, Width = 88, DialogResult = DialogResult.OK };
        f.Controls.AddRange(new Control[] { pic, title, ver, blurb, ok });
        f.AcceptButton = ok; f.CancelButton = ok;
        f.ShowDialog(this);
    }
}
