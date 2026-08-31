namespace BloodAndGritKeeper;

public partial class MainForm
{
    // ============================================================ RIDES (Posse tab, lower pane)
    // What the posse rides and drives. A horse is not scenery: it takes the first shot when
    // something comes out of the dark, it carries the water, and losing it two days from a
    // town is its own kind of trouble. Same for a wagon, the stage, a ferry, or the cars.
    // Rides sit under the posse because that's who they belong to; they go to the Tracker
    // like anything else that can be hurt.
    DataGridView ridesGrid;
    NumericUpDown rideAmount;

    Control BuildRidesPane()
    {
        var host = new Panel { Dock = DockStyle.Fill, BackColor = Paper };

        ridesGrid = new DataGridView
        {
            Dock = DockStyle.Fill, AutoGenerateColumns = false, DataSource = rides,
            AllowUserToAddRows = false, RowHeadersVisible = false,
            AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
            SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = false
        };
        StyleGrid(ridesGrid);
        // Name = prop, which the corral did without until v1.33.0 — with no name a column cannot be
        // reached as g.Columns["BloodCur"], and that is the only way Figures() finds the ones to set
        // right. It is why this grid kept its figures ragged while the Posse's were squared up.
        void Col(string prop, string head, int weight, bool ro = false)
            => ridesGrid.Columns.Add(new DataGridViewTextBoxColumn
            { DataPropertyName = prop, Name = prop, HeaderText = head, FillWeight = weight, ReadOnly = ro });
        Col("Name", "Name", 130); Col("Type", "What it is", 110, ro: true); Col("Kind", "Kind", 60, ro: true);
        Col("Rider", "Rider / driver", 115);
        // MaxHead and not "/Max": this grid sits directly under the Posse's on the same tab, close
        // enough that the two are read in one glance, and they were wearing two spellings of the
        // same header. Sharing the constant also means the corral cannot pick up the wrap-and-clip
        // the Posse tab just got rid of — see MaxHead for the non-breaking space that prevents it.
        Col("BloodCur", "Blood", 52); Col("BloodMax", MaxHead, 58); Col("Defense", "Def", 42);
        Col("Speed", "Speed", 140, ro: true); Col("Capacity", "Carries", 55); Col("Notes", "Notes", 210);
        Figures(ridesGrid, "BloodCur", "Defense", "Capacity");
        WireNumericValidation(ridesGrid, new() { "BloodCur", "BloodMax", "Defense", "Capacity" });

        // a wrecked wagon or a downed horse reads at a glance, the same red the Tracker uses
        ridesGrid.CellFormatting += (s, e) =>
        {
            if (e.RowIndex < 0 || e.RowIndex >= rides.Count) return;
            var r = rides[e.RowIndex];
            e.CellStyle.BackColor = r.Down ? DownRow : (r.IsMount ? PcRow : FoeRow);
        };
        ridesGrid.CellEndEdit += (s, e) =>
        {
            if (e.RowIndex < 0 || e.RowIndex >= rides.Count) return;
            var r = rides[e.RowIndex];
            if (r.BloodCur > r.BloodMax) r.BloodCur = r.BloodMax;   // current can't outrun its maximum
        };
        ridesGrid.KeyDown += (s, e) =>
        {
            if (e.KeyCode == Keys.Delete && SelectedRide() is Ride r && !ridesGrid.IsCurrentCellInEditMode)
            { RemoveRide(r); e.Handled = true; }
        };
        Tip.SetToolTip(ridesGrid, "Right-click a ride for everything that can be done to it");

        // The bar's actions, on the ride itself.
        GridMenu<Ride>(ridesGrid, (menu, r) =>
        {
            MIHead(menu, $"{r.Name} — {r.Type}");
            MI(menu, "Rename…", () => RenameRide(r));
            MI(menu, r.Rider is { Length: > 0 } ? $"Rider — {r.Rider}" : "Assign a rider…",
                () => ShowRiderMenu(ridesGrid, ridesGrid.PointToClient(Cursor.Position)));
            MISep(menu);
            MI(menu, $"Hurt {rideAmount.Value}", () => AdjustRide(-1), r.BloodCur > 0);
            MI(menu, $"Mend {rideAmount.Value}", () => AdjustRide(+1), r.BloodCur < r.BloodMax);
            MISep(menu);
            MI(menu, "Send to the Tracker", () => RideToTracker(r));
            MI(menu, r.IsMount ? "Sold, lost, or left behind" : "Sold, wrecked, or left behind", () => RemoveRide(r));
        });

        var bar = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(8, 5, 8, 5), BackColor = Color.FromArgb(243, 237, 221) };
        bar.Controls.Add(Heading("The corral & the yard"));
        bar.SetFlowBreak(bar.Controls[bar.Controls.Count - 1], true);

        // The roster, split the way a Keeper thinks of it: things that breathe, things that don't.
        var mounts = Db.Rides.Where(r => r.kind == "mount")
            .Select(r => (r.name, (EventHandler)((s, e) => AddRide(r.name)))).ToList();
        var vehicles = Db.Rides.Where(r => r.kind != "mount")
            .Select(r => (r.name, (EventHandler)((s, e) => AddRide(r.name)))).ToList();
        var items = new List<(string, EventHandler)>();
        items.Add(("— Mounts —", null));
        items.AddRange(mounts);
        items.Add(("-", null));
        items.Add(("— Vehicles —", null));
        items.AddRange(vehicles);
        bar.Controls.Add(MenuBtn("＋ Add a ride ▾", 120, "Put a mount or a vehicle in the posse's keeping", items.ToArray()));

        bar.Controls.Add(Btn("✎ Rename", (s, e) =>
        {
            if (SelectedRide() is not Ride r) { Nope("Select a ride first."); return; }
            RenameRide(r);
        }, 88, "Give it a name — a horse the table knows by name is a horse the table will miss"));

        bar.Controls.Add(Btn("Assign rider ▾", (s, e) =>
        {
            var b = (Button)s;
            ShowRiderMenu(b, new Point(0, b.Height));
        }, 105, "Say who's in the saddle or holding the lines"));

        bar.Controls.Add(Lbl("  Damage/heal:"));
        rideAmount = new NumericUpDown { Minimum = 1, Maximum = 999, Value = 5, Width = 60, Margin = new Padding(3, 6, 3, 3) };
        Tip.SetToolTip(rideAmount, "How much Blood the next button takes or gives back");
        bar.Controls.Add(rideAmount);
        bar.Controls.Add(Btn("− Hurt", (s, e) => AdjustRide(-1), 70, "Take that much Blood off the selected ride"));
        bar.Controls.Add(Btn("＋ Mend", (s, e) => AdjustRide(+1), 74, "Give it back — a night's rest, a wheelwright, a farrier"));

        bar.Controls.Add(Btn("→ Tracker", (s, e) =>
        {
            if (SelectedRide() is not Ride r) { Nope("Select a ride first."); return; }
            RideToTracker(r);
        }, 92, "Put it on the combat tracker — it can be shot at like anything else"));

        bar.Controls.Add(DangerBtn("✕ Remove", (s, e) =>
        {
            if (SelectedRide() is not Ride r) { Nope("Select a ride first."); return; }
            RemoveRide(r);
        }, 88, "Sold, lost, or left behind (or press Delete)"));

        bar.Controls.Add(DangerBtn("Clear rides", (s, e) =>
        {
            if (rides.Count == 0) { Nope("Nothing in the corral."); return; }
            if (!Confirm($"Clear all {rides.Count} ride(s)?")) return;
            rides.Clear();
            Log("The corral is empty.");
        }, 92, "Empty the corral and the yard"));

        // Empty-state hint. The Encounter and the Tracker both explain themselves when they have
        // nothing in them; the corral was a header band over a void, which says only that something
        // is missing and never what. The band is the emptiest surface in the app on a first run,
        // because a new table has a posse before it has a horse.
        var hint = new Label
        {
            Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleCenter,
            Font = new Font("Segoe UI", 10.5f, FontStyle.Italic), ForeColor = GoldDeep, BackColor = Paper,
            Text = "Nothing in the corral.\n\n"
                 + "＋ Add a ride puts a horse, a mule, a wagon or the stage in the posse's keeping.\n"
                 + "A ride carries the water and takes the first shot out of the dark, so it can be\n"
                 + "hurt, mended, named, and sent to the Tracker like anything else that bleeds."
        };
        // Added in the Tracker's exact order — content, then the bar, then the hint brought to the
        // front. Docking is resolved last-added-first, so the bar keeps its band and the hint fills
        // only what is left; BringToFront is what puts it over the grid rather than under it.
        host.Controls.Add(ridesGrid);
        host.Controls.Add(bar);
        host.Controls.Add(hint);
        hint.BringToFront();
        hint.Visible = rides.Count == 0;
        rides.ListChanged += (s, e) => hint.Visible = rides.Count == 0;
        Watermark(hint, () => HintBottom(hint));
        return host;
    }

    Ride SelectedRide() => ridesGrid?.CurrentRow?.DataBoundItem as Ride;

    void AddRide(string type)
    {
        var r = Db.MakeRide(type);
        r.Name = Db.FreeRideName(rides.Select(x => x.Name), r.Name);
        rides.Add(r);
        Log($"{r.Name} joins the outfit — Blood {r.BloodCur}/{r.BloodMax}, Def {r.Defense}, carries {r.Capacity}.");
    }

    void RenameRide(Ride r)
    {
        string n = AskLine($"Name this {r.Type.ToLowerInvariant()}", r.Name);
        if (!string.IsNullOrWhiteSpace(n)) { r.Name = n.Trim(); CaptureUndo(); ridesGrid.Refresh(); }
    }

    void RideToTracker(Ride r)
    {
        tracker.Add(new Combatant
        { Name = r.Name, BloodCur = r.BloodCur, BloodMax = r.BloodMax, Defense = r.Defense, IsPC = false, Init = ArrivalInit() });
        Log($"{r.Name} is on the field.");
    }

    void RemoveRide(Ride r)
    {
        if (!Confirm($"Remove {r.Name}?")) return;
        rides.Remove(r);
        Log($"{r.Name} is gone from the outfit.");
    }

    void AdjustRide(int sign)
    {
        if (SelectedRide() is not Ride r) { Nope("Select a ride first."); return; }
        int v = (int)rideAmount.Value;
        r.BloodCur = Math.Clamp(r.BloodCur + sign * v, 0, r.BloodMax);
        Log($"{r.Name} {(sign < 0 ? "takes" : "recovers")} {v} → {r.BloodCur}/{r.BloodMax}"
            + (r.BloodCur == 0 ? (r.IsMount ? "  — DOWN." : "  — WRECKED.") : ""));
        ridesGrid.Refresh();
    }

    // Riders come from the posse, so the list can't go stale — plus a way to unhitch. Anchored to
    // whatever asked for it: the bar's button, or the grid at the point of a right-click.
    void ShowRiderMenu(Control anchor, Point at)
    {
        if (SelectedRide() is not Ride r) { Nope("Select a ride first."); return; }
        var menu = PopupMenu();
        if (party.Count == 0)
            menu.Items.Add(new ToolStripMenuItem("No souls in the posse yet") { Enabled = false });
        foreach (var p in party)
        {
            var soul = p;
            menu.Items.Add(soul.Name, null, (s, e) =>
            { r.Rider = soul.Name; CaptureUndo(); ridesGrid.Refresh(); Log($"{soul.Name} takes {r.Name}."); });
        }
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add("Nobody — put it up", null, (s, e) =>
        { r.Rider = ""; CaptureUndo(); ridesGrid.Refresh(); Log($"{r.Name} is put up."); });
        menu.Show(anchor, at);   // PopupMenu() lets it go when it closes
    }
}
