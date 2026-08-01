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

        var edit = new ToolStripMenuItem("&Edit");
        undoMenuItem = Item("&Undo", (s, e) => Undo(), Keys.Control | Keys.Z);
        redoMenuItem = Item("&Redo", (s, e) => Redo(), Keys.Control | Keys.Y);
        undoMenuItem.Enabled = false; redoMenuItem.Enabled = false;
        edit.DropDownItems.Add(undoMenuItem);
        edit.DropDownItems.Add(redoMenuItem);
        menu.Items.Add(edit);

        // one entry per tab, so the Ctrl+number shortcuts are discoverable
        var view = new ToolStripMenuItem("&View");
        for (int i = 0; i < tabs.TabPages.Count; i++)
        {
            int idx = i;
            view.DropDownItems.Add(Item(tabs.TabPages[i].Text,
                (s, e) => tabs.SelectedIndex = idx, shortcutText: $"Ctrl+{(i + 1) % 10}"));
        }
        // Show/hide belongs on a menu called View — which is where the glass was NOT, and the only
        // menu it was on is called Table. Same one method underneath as the Table entry and the
        // Tracker's own button, so three routes cannot come to three different answers.
        if (ShowsTab("Tracker"))
        {
            view.DropDownItems.Add(new ToolStripSeparator());
            var vglass = new ToolStripMenuItem("The turn &hourglass") { Checked = TurnTimerOn };
            vglass.Click += (s, e) => { ShowTurnTimer(!TurnTimerOn); RebuildMenu(); };
            vglass.ToolTipText = "Put an hourglass on the Tracker that times the posse's turn, or take it away";
            view.DropDownItems.Add(vglass);
        }
        menu.Items.Add(view);

        // Switch how the table is run without leaving the app — a checkmark on the mode in force.
        var table = new ToolStripMenuItem("&Table");
        void ModeItem(string text, RunMode m)
        {
            var it = Item(text, (s, e) => { SetMode(m); RebuildMenu(); });
            it.Checked = Mode == m;
            table.DropDownItems.Add(it);
        }
        ModeItem("&Player's table", RunMode.Player);
        ModeItem("Keeper — &dice && books", RunMode.KeeperDice);
        ModeItem("Keeper — on the &engine", RunMode.KeeperEngine);

        // The turn glass is a house rule about how this table plays, so it belongs on the Table
        // menu and not only on the Tracker's own bar — it is the kind of thing settled before
        // anyone sits down, by someone who has not opened the Tracker yet. It appears on the two
        // Keeper tables because the Tracker does; a player's table has no field to time.
        if (ShowsTab("Tracker"))
        {
            table.DropDownItems.Add(new ToolStripSeparator());
            var glass = new ToolStripMenuItem("The turn &glass") { Checked = TurnTimerOn };
            glass.Click += (s, e) => { ShowTurnTimer(!TurnTimerOn); RebuildMenu(); };
            glass.ToolTipText = "Put an hourglass on the Tracker that times the posse's turn, or take it away";
            table.DropDownItems.Add(glass);
            var howLong = new ToolStripMenuItem("How long is a &turn…");
            howLong.Click += (s, e) => AskTurnLength();
            howLong.ToolTipText = "Set how long a posse's turn runs — five minutes unless you say otherwise";
            table.DropDownItems.Add(howLong);
        }
        menu.Items.Add(table);

        var help = new ToolStripMenuItem("&Help");
        help.DropDownItems.Add(Item("The &five-minute lesson", (s, e) => ShowLesson(), Keys.F1));
        help.DropDownItems.Add(Item("&Keyboard shortcuts", (s, e) => ShowShortcuts()));
        help.DropDownItems.Add(new ToolStripSeparator());
        help.DropDownItems.Add(Item("Show me a&round", (s, e) => StartTour()));
        help.DropDownItems.Add(new ToolStripSeparator());
        help.DropDownItems.Add(Item("What it &needs to run…", (s, e) => ShowRequirements()));
        help.DropDownItems.Add(Item("&About GritKeeper…", (s, e) => ShowAbout()));
        menu.Items.Add(help);

        return menu;
    }

    // Rebuild the menu bar in place — after a live mode switch, so the View list matches the tabs now
    // on show and the Table checkmark tracks the mode. Cheap, and keeps the menu the single source.
    void RebuildMenu()
    {
        var old = MainMenuStrip;
        var menu = BuildMenu(tabsCtl);
        MainMenuStrip = menu;
        Controls.Add(menu);
        if (old != null) Controls.Remove(old);
        RefreshUndoRedoButtons();   // the fresh Undo/Redo items start disabled; restore their real state
    }

    // ---------------------------------------------------------- save / load to a chosen file
    void SaveSessionAs()
    {
        using var d = new SaveFileDialog
        {
            Title = "Save the session",
            Filter = "GritKeeper session (*.json)|*.json|All files (*.*)|*.*",
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
            Filter = "GritKeeper session (*.json)|*.json|All files (*.*)|*.*"
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
            MessageBox.Show("That file doesn't read as a GritKeeper session.\r\n\r\n" + ex.Message,
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

        H("GritKeeper, in five minutes");
        // The count is READ, not typed, and the shortcut sentence follows it. It said "ten tabs …
        // Ctrl+0 to the tenth" to everybody, including a player's table, which shows three — so a
        // player was told about seven tabs they do not have and seven shortcuts that do nothing.
        // Same lesson as the Keeper's screen leaf count: a number in prose has to be derived.
        int shown = tabsCtl?.TabPages.Count ?? allTabs.Count;
        string spelled = shown switch
        { 1 => "one", 2 => "two", 3 => "three", 4 => "four", 5 => "five", 6 => "six",
          7 => "seven", 8 => "eight", 9 => "nine", 10 => "ten", _ => shown.ToString() };
        I($"Everything a Keeper reaches for mid-scene, in {spelled} tab{(shown == 1 ? "" : "s")}. "
          + (shown >= 10 ? "Ctrl+1 through Ctrl+9 jump straight to them, Ctrl+0 to the tenth. "
                         : $"Ctrl+1 through Ctrl+{shown} jump straight to them. ")
          + "Nothing here invents rules — every number, table, and creature is taken "
          + "word-for-word from the books.");

        H("1 · Seat the posse  (Posse)");
        T("The party sheet. Add each soul's Blood, Defense, saves, Nerve, Grit, Mark, and Taint — or click straight " +
          "into a cell to edit it. The buttons along the top do the bookkeeping: Damage and Heal apply the Amount " +
          "spinner to the selected soul, Spend Grit counts it down, and Dread check rolls a Will save against the DC " +
          "you set, taking the Nerve loss by the horror's Tier automatically. \"New session\" refills Nerve and " +
          "resets Grit to 3; Rest ▾ is the long rest; ▲ ▼ put the posse in whatever order you ride in. " +
          "Double-click a soul to open their Ledger — the book's own character sheet — in its own window; " +
          "double-click the Notes cell to read and edit the whole note. On first run the six ready-made souls from " +
          "Appendix D are already seated — clear them out whenever your own posse is ready.");

        H("2 · Roll anything  (Dice)");
        T("Type an expression — 2d6+3, 1d8+1d6+2 — and press Enter, or punch it in with the buttons: the +d buttons " +
          "add dice (click one twice and it stacks: d6, 2d6, 3d6), the digits and ＋/− build the modifier. The dice " +
          "tumble in the tray and land on the true results — every die wears its color (green d4, blue d6, orange d8, " +
          "white d10, yellow d12, red d20, purple d100), best faces ring gold and a 1 rings black. Below that, the " +
          "d20 checker rolls a full four-degrees check against a DC. Everything the app rolls — here or on any " +
          "other tab — lands in the log on the right, so the whole night is on the record. The log belongs to " +
          "the sitting, though: it is not part of the saved session and starts clean next launch, so Copy log " +
          "is how you keep one.");

        H("3 · Know your horrors  (Bestiary)");
        T("All 150 creatures from the book, word for word. Search by name or haunt, filter by tier or chapter. " +
          "Double-click a creature (or hit ⧉ Pop out) to open it in its own window — open several side by side and " +
          "size the text to the light in the room. From here one click sends a creature to the Encounter builder or " +
          "drops N copies straight onto the Tracker. Sixty-five of the hundred and fifty are the mundane half — " +
          "the two chapters Beasts of the Living World and Hard Men & Hard Country, which cost no Nerve and never " +
          "move the Mark. Filter to those for the slow-burn weeks before anything gets up that shouldn't.");

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

        H("6 · When the trail runs dry  (Generators)");
        T("Every rollable table from The Country in Your Pocket: a town in three rolls, a CITY in four (its quarter, " +
          "who really runs it, its wrong note, and work for a country posse — Keeper's Book Ch. XIV), a face in four, " +
          "rumors, trail events, plunder, omens — and the Grounds tables, an encounter for any terrain with the " +
          "safe-table rule applied automatically. Two grounds are new: The Ordinary Country, for the sessions before " +
          "the horror, and The Lamplit City. One click, and the country answers.");

        H("7 · Survey the country  (Map)");
        T("A drafting table for frontier maps. Set the ground — including The Lamplit City — and the scale (a single " +
          "gunfight, a homestead, a county, a territory, or a city ward of streets and blocks), " +
          "the hour, and the water; tick a trail, a rail line, a settlement, a grid; and 🎲 New map (Ctrl+G) draws a " +
          "named survey — the same seed and settings always draw the same map, so note the number and you can have " +
          "it back. The Keeper's layer adds the secrets in red; leave it off before showing players. Save as SVG or " +
          "a one-page PDF, or copy the SVG straight to the clipboard.");

        H("8 · Deal a new soul  (New Soul)");
        T("A complete character at any level 1–10, displayed on the book's own Ledger sheet. 🎲 Make a soul rolls " +
          "the whole character strictly by Chapter III's eight steps — pin the Calling or Origin if you have one in " +
          "mind. 🧭 Wizard… walks you through every choice yourself: abilities, skills, Edges, Signs, coin and all, " +
          "each list filtered to what the book allows. Either way the sheet is cross-checked against the rules " +
          "before it reaches you, and ✎ Tweak lets you hand-adjust anything after (the Ledger notes the sheet was " +
          "tweaked rather than arguing). → Posse seats them at the table; Copy sheet takes the text anywhere.");

        H("9 · The rules at your elbow  (Reference)");
        // Both the count and the contents follow the table. A player's deck leaves out the two
        // Keeper's-Book leaves, and prose that listed them anyway would send a player hunting the
        // deck for something that is deliberately not in it.
        T($"A Keeper's screen in {RefLeafCountFor(Mode)} leaves — the four degrees, the DC ladder, the Iron Code, wounds, " +
          "every condition, Nerve and Dread, the Mark and the Taint, Signs and Grit, Miracles, " +
          (Mode == RunMode.Player ? "" : "the Long Odds and the safe-table rule, running in town, ") +
          "and the book's own arms, goods, and skills tables. Turn the deck " +
          "with the ◀ ▶ buttons or the Left and Right arrow keys. When a ruling is needed and the book is across " +
          "the room, it's here.");

        H("10 · Keep the record  (Session)");
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
        M("  Ctrl+1 … Ctrl+0   Jump to a tab (in bar order; Ctrl+0 is the tenth)");
        M("  Ctrl+S            Save the session now");
        M("  Ctrl+Shift+S      Save the session to a file…");
        M("  Ctrl+O            Load a session from a file…");
        M("  F1                The five-minute lesson");
        M("");
        H("Posse");
        M("  Ctrl+D / Ctrl+H   Damage / Heal the selected soul (by the Amount)");
        M("  Delete            Remove the selected soul");
        M("  F2 (or type)      Edit the selected cell");
        M("  Double-click      Open the soul's Ledger (on the Notes cell: the whole note)");
        M("");
        H("Tracker");
        M("  Ctrl+I            Roll initiative for the field");
        M("  Ctrl+R            Next round");
        M("  Ctrl+D / Ctrl+H   Damage / Heal the selected combatant (by the Amt)");
        M("  Delete            Remove the selected combatant");
        M("  Double-click      Open the combatant's card (stat block, or a soul's Ledger)");
        M("");
        H("Bestiary & pickers");
        M("  Ctrl+F            Jump to the search box");
        M("  Enter / dbl-click Pop the creature out into its own window");
        M("  Enter             Add the typed creature (Encounter/Tracker pickers)");
        M("");
        H("Dice");
        M("  Enter             Roll the expression in the box");
        M("");
        H("Map");
        M("  Ctrl+G            Draw a fresh map on a new seed");
        M("");
        H("Reference");
        M("  Left / Right      Turn the deck (or click ◀ ▶)");
        M("");
        H("Everything else");
        M("  Hover a button — every one of them carries a tooltip (audit_ui.py holds them to it).");
        M("  Grid headers and the columns you may type in carry one too.");

        rtf.SelectionStart = 0; rtf.ScrollToCaret();
        win.Controls.Add(Pad(rtf, 18));
        win.Show(this);
    }

    void ShowAbout()
    {
        using var f = new Form
        {
            Width = 520, Height = 420, Text = "About GritKeeper",
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
            Text = "GritKeeper", AutoSize = false, TextAlign = ContentAlignment.MiddleCenter,
            Left = 0, Top = 178, Width = 504, Height = 30, Font = new Font("Segoe UI", 13f, FontStyle.Bold), ForeColor = Blood
        };
        var ver = new Label
        {
            // Interpolated, never typed: the About box had drifted nine book editions behind the
            // status bar, which reads the same three constants a foot away from here.
            Text = $"Version {AppVersion}\nPlayer's Book v{PlayerBookVer}  ·  Keeper's Book v{KeeperBookVer}  ·  Bestiary v{BestiaryVer}",
            AutoSize = false, TextAlign = ContentAlignment.MiddleCenter,
            Left = 0, Top = 212, Width = 504, Height = 40, ForeColor = Ink
        };
        var blurb = new Label
        {
            Text = "The Keeper's table companion to Blood & Grit,\na roleplaying game of the haunted frontier.\n\n© 2026 Cole Williams",
            AutoSize = false, TextAlign = ContentAlignment.MiddleCenter,
            Left = 0, Top = 260, Width = 504, Height = 80, ForeColor = Ink
        };
        var reqs = new LinkLabel
        {
            Text = "What it needs to run", AutoSize = false, TextAlign = ContentAlignment.MiddleCenter,
            Left = 0, Top = 318, Width = 504, Height = 22, LinkColor = Blood, ActiveLinkColor = Gold
        };
        reqs.LinkClicked += (s, e) => ShowRequirements();
        var ok = new Button { Text = "Ride on", Left = 208, Top = 344, Width = 88, DialogResult = DialogResult.OK };
        f.Controls.AddRange(new Control[] { pic, title, ver, blurb, reqs, ok });
        f.AcceptButton = ok; f.CancelButton = ok;
        f.ShowDialog(this);
    }

    /// <summary>What the app actually needs, on the back of the box. Written from what the build
    /// really is rather than from ambition: a self-contained win-x64 single file, so 64-bit Windows
    /// and no .NET install; a window that refuses to go below 1040x640; and a folder it can WRITE
    /// to, because the session, the preferences and the crash report all land beside the exe.
    ///
    /// Every line here is a promise. Nothing goes on this list that the app cannot do — the app
    /// spent two releases telling people they could play on a phone.</summary>
    void ShowRequirements()
    {
        using var f = new Form
        {
            Width = 560, Height = 520, Text = "GritKeeper — what it needs",
            FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent,
            MinimizeBox = false, MaximizeBox = false, ShowIcon = false, BackColor = Paper
        };
        var rtf = new RichTextBox
        {
            ReadOnly = true, BorderStyle = BorderStyle.None, BackColor = Paper,
            Left = 18, Top = 14, Width = 508, Height = 412
        };
        void H(string s) { rtf.SelectionFont = new Font("Segoe UI", 11.5f, FontStyle.Bold); rtf.SelectionColor = Blood; rtf.AppendText(s + "\n"); }
        void L(string k, string v)
        {
            rtf.SelectionFont = new Font("Consolas", 9.5f, FontStyle.Bold); rtf.SelectionColor = Ink;
            rtf.AppendText("  " + k.PadRight(13));
            rtf.SelectionFont = new Font("Consolas", 9.5f); rtf.SelectionColor = Ink;
            rtf.AppendText(v + "\n");
        }
        void N(string s) { rtf.SelectionFont = new Font("Segoe UI", 9.5f, FontStyle.Italic); rtf.SelectionColor = Gold; rtf.AppendText(s + "\n"); }

        H("Minimum");
        L("System",   "Windows 10 (version 1607) or Windows 11, 64-bit");
        L("Processor", "Any x64 processor");
        L("Memory",   "2 GB RAM");
        L("Disk",     "400 MB free — the app is ~155 MB and unpacks its");
        L("",         "own libraries to your TEMP folder on first run");
        L("Display",  "1280 × 720. The window will not go below 1040 × 640");
        L("Input",    "Keyboard and mouse");
        L("Other",    "None. No .NET install, no internet, no account,");
        L("",         "no administrator rights, nothing to configure");
        rtf.AppendText("\n");

        H("Recommended");
        L("Memory",   "4 GB RAM");
        L("Display",  "1920 × 1080 — the tracker and the Ledger both");
        L("",         "breathe better with the room");
        L("Printing", "Any printer, for the PDFs it writes (character");
        L("",         "sheets and trail maps). Not required to play");
        rtf.AppendText("\n");

        H("One thing that matters");
        N("  Put the folder somewhere you can write to — your Desktop, your Documents,");
        N("  a USB stick. GritKeeper saves the table beside its own exe (session.json,");
        N("  prefs.json), so a read-only place like Program Files will not hold your game.");
        rtf.AppendText("\n");

        H("What it is not");
        N("  A Windows desktop program, and only that. It does not run on macOS, Linux,");
        N("  a phone or a tablet, there is no browser version, and it does not connect");
        N("  players over a network — one machine at the table, usually the Keeper's.");
        N("  (The three books are PDFs. Those open on anything, phone included — it is");
        N("  the app that is Windows-only, not the game.)");
        rtf.AppendText("\n");

        // A Linux build is INTENDED, not shipped. Worded as a plan and nothing more, because this
        // screen exists to stop the app claiming what it cannot do — the standing rule is that no
        // promise is made to a player or Keeper that the current build cannot keep. "Planned" is a
        // statement about intent, which is honest; a date or a "coming soon" would not be.
        H("Planned, not here yet");
        N("  A Linux package is intended. The game's rules already build and run as a");
        N("  plain .NET library with no Windows dependency, which is the hard half of");
        N("  that job — but the window you are looking at is Windows Forms, and until");
        N("  there is something to download, treat this as an intention and not a date.");

        var ok = new Button { Text = "Ride on", Left = 232, Top = 440, Width = 88, DialogResult = DialogResult.OK };
        f.Controls.AddRange(new Control[] { rtf, ok });
        f.AcceptButton = ok; f.CancelButton = ok;
        rtf.SelectionStart = 0; rtf.ScrollToCaret();
        f.ShowDialog(this);
    }
}
