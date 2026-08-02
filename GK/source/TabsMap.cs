using System.Text;

namespace BloodAndGritKeeper;

/// <summary>How a rolled settlement is put on the map. A place is two different maps depending on
/// which question the table is asking. <see cref="Itself"/> is the map you walk — streets, blocks,
/// the depot, the doors you can kick in. <see cref="InItsCountry"/> is the map you ride, where the
/// whole settlement shrinks to one mark and what matters is the ground around it: how far the next
/// water is, what the posse has to cross, where a thing could be waiting.</summary>
internal enum PlaceView { Itself, InItsCountry }

public partial class MainForm
{
    // ============================================================ MAP TAB
    // The Trail Maps drafting table: set the ground, the scale, and the hour, and
    // MapGen draws a named frontier survey. The preview here, the SVG export, and
    // the PDF export all replay the same primitive list, so they always match.
    ComboBox mapGround, mapScale, mapTime, mapWater, mapSky;
    CheckBox mapTrail, mapRail, mapTown, mapGrid, mapSecrets, mapMarkOut;
    NumericUpDown mapLm, mapSeed;
    TextBox mapName;
    MapPanel mapPanel;
    MapModel curMap;
    bool mapBusy;

    // Tactical markers — session state, not part of the seeded map (a map redraw or a
    // new seed keeps everyone standing where the Keeper put them).
    readonly List<MapMarker> mapMarkers = new();
    MapMarker dragMarker;
    bool dragMoved;

    // Landmark editing — "the survey drew the Hanging Tree there, but I want it HERE."
    // Custom placements are kept by landmark name and re-applied whenever the same
    // seed regenerates (toggling the hour or the Keeper's layer rebuilds the model);
    // a genuinely new map clears them. lmDragIdx is the landmark under the mouse.
    bool lmEditMode;
    int lmDragIdx = -1;
    bool lmDragMoved;
    readonly Dictionary<string, (float x, float y)> lmEdits = new();
    int lmEditSeed = -1;
    CheckBox lmEditBtn;

    // The Keeper's-layer marks move the same way; keyed by index, not text, because
    // two secrets on one map can carry the same line.
    int secDragIdx = -1;
    bool secDragMoved;
    readonly Dictionary<int, (float x, float y)> secEdits = new();

    // The settlement moves by the same hand. There's only ever one, so it needs no key —
    // just where the Keeper put it, held for as long as the map number holds.
    bool townDrag, townDragMoved;
    (float x, float y)? townEdit;

    // View state — zoom is 1 (fit-to-panel) up to 8×; pan only applies while zoomed.
    // Wheel to zoom at the cursor, drag empty ground to pan, Fit to come home.
    float mapZoom = 1f;
    PointF mapPan = PointF.Empty;
    bool mapPanning;
    Point mapPanLast;

    // The one transform the renderer, the markers, and the mouse all share, so a
    // marker draws exactly where a click lands: model → screen is (x*s+ox, y*s+oy).
    (float s, float ox, float oy) MapXform(MapModel m, Rectangle dest)
    {
        float s = Math.Min((dest.Width - 16f) / m.W, (dest.Height - 16f) / m.H) * mapZoom;
        return (s, dest.X + (dest.Width - m.W * s) / 2 + mapPan.X,
                   dest.Y + (dest.Height - m.H * s) / 2 + mapPan.Y);
    }

    // Zoom keeping the model point under the anchor fixed on screen.
    void MapZoomAt(Point anchor, float factor)
    {
        var m = mapPanel.Model; if (m == null) return;
        var dest = mapPanel.ClientRectangle;
        var (s, ox, oy) = MapXform(m, dest);
        if (s <= 0) return;
        float mx = (anchor.X - ox) / s, my = (anchor.Y - oy) / s;
        mapZoom = Math.Clamp(mapZoom * factor, 1f, 8f);
        if (mapZoom <= 1.001f) { mapZoom = 1f; mapPan = PointF.Empty; }
        else
        {
            float ns = Math.Min((dest.Width - 16f) / m.W, (dest.Height - 16f) / m.H) * mapZoom;
            mapPan = new PointF(
                anchor.X - mx * ns - dest.X - (dest.Width - m.W * ns) / 2,
                anchor.Y - my * ns - dest.Y - (dest.Height - m.H * ns) / 2);
        }
        mapPanel.Invalidate();
    }

    sealed class MapPanel : Panel
    {
        public MapModel Model;
        public MapPanel()
        {
            DoubleBuffered = true; ResizeRedraw = true;
            // Selectable so a click can focus it and the wheel zooms; the two click styles so the
            // panel actually raises MouseDoubleClick, which is what opens the map full screen.
            SetStyle(ControlStyles.Selectable | ControlStyles.StandardClick | ControlStyles.StandardDoubleClick, true);
        }
    }

    TabPage BuildMapTab()
    {
        var page = new TabPage("Map") { BackColor = Paper };

        // Three rows, grouped by intent, so nothing hunts for a home when the bar wraps:
        //   1. the survey — everything that decides WHAT the map is
        //   2. show / zoom — how you VIEW it (overlays never change the map, only its ink)
        //   3. at the table / export — what you DO with it
        var barBg = Color.FromArgb(243, 237, 221);
        FlowLayoutPanel Row(int padTop, int padBottom) => new()
        { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(8, padTop, 8, padBottom), BackColor = barBg };
        var rowGen = Row(6, 1);
        var rowView = Row(1, 1);
        var rowWork = Row(1, 5);
        Control Sep() => new Panel { Width = 1, Height = 26, BackColor = Color.FromArgb(196, 181, 148), Margin = new Padding(10, 5, 10, 3) };

        ComboBox Combo(FlowLayoutPanel row, string[] items, int sel, int w, string tip)
        {
            var c = new ComboBox { Width = w, DropDownStyle = ComboBoxStyle.DropDownList, Margin = new Padding(3, 5, 3, 3) };
            c.Items.AddRange(items);
            c.SelectedIndex = sel;
            Tip.SetToolTip(c, tip);
            row.Controls.Add(c);
            return c;
        }
        CheckBox Check(FlowLayoutPanel row, string text, bool val, string tip)
        {
            var c = new CheckBox { Text = text, Checked = val, AutoSize = true, Margin = new Padding(6, 8, 3, 3), ForeColor = Ink };
            Tip.SetToolTip(c, tip);
            row.Controls.Add(c);
            return c;
        }

        // ---- row 1: the survey ----
        rowGen.Controls.Add(Lbl("Ground:"));
        mapGround = Combo(rowGen, MapGen.Terrains, 0, 192, "The kind of country — the Bestiary's Grounds");
        rowGen.Controls.Add(Lbl(" Scale:"));
        mapScale = Combo(rowGen, MapGen.Scales, 2, 156, "From a single gunfight up to weeks of trail");
        rowGen.Controls.Add(Lbl(" Hour:"));
        mapTime = Combo(rowGen, MapGen.Times, 1, 100, "The hour sets the light — night maps come with stars and a moon");
        rowGen.Controls.Add(Lbl(" Water:"));
        mapWater = Combo(rowGen, MapGen.Waters, 0, 118, "Force a creek, river, or lake — or let the terrain decide");
        rowGen.Controls.Add(Lbl(" Weather:"));
        mapSky = Combo(rowGen, MapGen.Weathers, 0, 124,
            "The sky over the survey — fair, overcast, rain, fog, blowing dust, snow, a blizzard. "
            + "Left on “As the sky wills” the country picks what it would actually get: the high "
            + "country gets snow, the badlands get heat and sand.");
        rowGen.Controls.Add(Lbl(" Landmarks:"));
        mapLm = new NumericUpDown { Minimum = 0, Maximum = 12, Value = 5, Width = 48, Margin = new Padding(3, 6, 3, 3) };
        Tip.SetToolTip(mapLm, "How many named places the survey marks");
        rowGen.Controls.Add(mapLm);
        rowGen.Controls.Add(Lbl(" Seed:"));
        mapSeed = new NumericUpDown { Minimum = 0, Maximum = 999999, Value = 0, Width = 74, Margin = new Padding(3, 6, 3, 3) };
        Tip.SetToolTip(mapSeed, "The map's number — the same seed and settings always draw the same map");
        rowGen.Controls.Add(mapSeed);
        rowGen.Controls.Add(Btn("🎲 New map", (s, e) => MapDraw(true), 92, "Draw a fresh map on a new seed (Ctrl+G)"));
        rowGen.SetFlowBreak(rowGen.Controls[rowGen.Controls.Count - 1], true);
        // A place the Keeper has already named — usually rolled on the Generators tab and sent
        // over. Empty means the survey names it, which is what it did before this box existed.
        rowGen.Controls.Add(Lbl("Name:"));
        mapName = new TextBox { Width = 210, Margin = new Padding(3, 6, 3, 3) };
        Tip.SetToolTip(mapName, "Name this place yourself — the town's name on a county map, the ward's on a city map. "
            + "Leave it empty and the survey names it. Roll a town or a city on the Generators tab and press "
            + "“→ Map” to fill this in.");
        // Redraw when the Keeper is DONE typing, not per keystroke: every redraw writes a line to
        // the roll log, and "Coffin Wells" typed a letter at a time would write eleven of them.
        mapName.Leave += (s, e) => { if (!mapBusy) MapDraw(false); };
        mapName.KeyDown += (s, e) =>
        {
            if (e.KeyCode != Keys.Enter) return;
            e.SuppressKeyPress = true;
            if (!mapBusy) MapDraw(false);
        };
        rowGen.Controls.Add(mapName);
        rowGen.Controls.Add(QuietBtn("Clear name", (s, e) => mapName.Text = "", 88,
            "Give the naming back to the survey"));

        // ---- row 2: what's shown, and how close ----
        rowView.Controls.Add(Lbl("Show:"));
        mapTrail = Check(rowView, "Trail", true, "A trail or wagon road across the country");
        mapRail = Check(rowView, "Rail", false, "A rail line — straight as money");
        mapTown = Check(rowView, "Settlement", true, "A named town or camp on the trail");
        mapGrid = Check(rowView, "Grid", false, "Overlay squares — a battle map's grid (on by default at gunfight scale)");
        mapSecrets = Check(rowView, "Keeper's layer", false, "The secrets, in red — leave off before showing players. Exports include whatever is checked.");
        rowView.Controls.Add(Sep());
        rowView.Controls.Add(Lbl("Zoom:"));
        rowView.Controls.Add(Btn("🔍＋", (s, e) => MapZoomAt(new Point(mapPanel.Width / 2, mapPanel.Height / 2), 1.4f), 46,
            "Zoom in — or roll the mouse wheel over the map"));
        rowView.Controls.Add(Btn("🔍−", (s, e) => MapZoomAt(new Point(mapPanel.Width / 2, mapPanel.Height / 2), 1 / 1.4f), 46,
            "Zoom out"));
        rowView.Controls.Add(QuietBtn("Fit", (s, e) => { mapZoom = 1f; mapPan = PointF.Empty; mapPanel.Invalidate(); }, 46,
            "Fit the whole survey back in the window"));
        rowView.Controls.Add(Btn("◈ Full screen", (s, e) => MapFullScreen(), 108,
            "Throw the map across the whole screen, with every control on this bar still on it — "
            + "or just double-click the map. Esc, F11 or ✕ brings it back."));

        // ---- row 3: at the table, then out the door ----
        // The old label just read "✥ Landmarks", which named a thing rather than an action — you
        // had to already know that pressing it let you move anything (user-reported). It now says
        // what it does, and stays saying it while it's held down.
        lmEditBtn = ToggleBtn("✥ Move things", 118,
            "Press to pick things up. While it's down, drag the town, any named landmark, " +
            "or a red Keeper's-layer mark to a better spot — right-click one to put it back where the survey " +
            "drew it. Placements hold for this map number, and exports carry them.");
        lmEditBtn.CheckedChanged += (s, e) =>
        {
            lmEditMode = lmEditBtn.Checked;
            lmEditBtn.Text = lmEditMode ? "✥ Moving — on" : "✥ Move things";
            if (!lmEditMode) { lmDragIdx = -1; secDragIdx = -1; townDrag = false; }
            mapPanel.Invalidate();
            if (lmEditMode) Log("Moving is on: drag the town, a landmark, or a red secret. Right-click one to put it back.");
        };
        rowWork.Controls.Add(lmEditBtn);
        rowWork.Controls.Add(Btn("＋ Marker ▾", (s, e) => ShowMarkerMenu((Button)s), 100,
            "Place a marker — a posse soul, an NPC, or a creature — then drag it into position"));
        rowWork.Controls.Add(Btn("Tracker → Map", (s, e) => TrackerToMap(), 110,
            "Drop everyone on the Tracker onto the map — posse west, trouble east"));
        rowWork.Controls.Add(Btn("Marker colors ▾", (s, e) => ShowKindInkMenu((Button)s), 112,
            "Choose the ink for each kind of marker — and remember it. A single marker can also take " +
            "a color of its own: right-click it on the map."));
        rowWork.Controls.Add(Btn("Clear markers", (s, e) =>
        {
            if (mapMarkers.Count == 0) { Nope("No markers on the map."); return; }
            if (!Confirm($"Clear all {mapMarkers.Count} marker(s) from the map?")) return;
            mapMarkers.Clear(); CaptureUndo(); mapPanel.Invalidate();
            Log("The map is cleared of markers.");
        }, 105, "Remove every marker from the map"));
        rowWork.Controls.Add(Sep());
        rowWork.Controls.Add(Lbl("Export:"));
        // Markers are the table's business, not the survey's, so a saved map leaves them off unless
        // the Keeper says otherwise — a map for the players shouldn't show them where the ambush is.
        // The checkbox is here, beside the save buttons, because that's the moment the question comes up.
        mapMarkOut = new CheckBox
        { Text = "with markers", AutoSize = true, Margin = new Padding(2, 7, 6, 3), ForeColor = Ink, UseMnemonic = false };
        Tip.SetToolTip(mapMarkOut, "Off, a saved SVG or PDF is the survey alone — the markers stay on screen. " +
            "On, they're drawn onto the file too, in the colors shown here.");
        rowWork.Controls.Add(mapMarkOut);
        rowWork.Controls.Add(Btn("Save SVG…", (s, e) => MapSaveSvg(), 95,
            "Save the map as a scalable SVG file — exactly as shown, checked overlays included"));
        rowWork.Controls.Add(Btn("Save PDF…", (s, e) => MapSavePdf(), 95,
            "Save the map as a one-page landscape PDF — exactly as shown, checked overlays included"));
        rowWork.Controls.Add(Btn("Copy SVG", (s, e) =>
        {
            if (curMap == null) return;
            Clipboard.SetText(MapGen.ToSvg(curMap, MarkerOverlay()));
            Log("Map SVG copied to the clipboard" + MarkerNote() + ".");
        }, 90, "Copy the SVG markup to the clipboard"));

        mapPanel = new MapPanel { Dock = DockStyle.Fill, BackColor = Color.FromArgb(236, 229, 212) };
        mapPanel.Paint += (s, e) =>
        {
            if (mapPanel.Model == null) return;
            DrawModel(e.Graphics, mapPanel.Model, mapPanel.ClientRectangle);
            DrawLandmarkHandles(e.Graphics, mapPanel.Model, mapPanel.ClientRectangle);
            DrawMarkers(e.Graphics, mapPanel.Model, mapPanel.ClientRectangle);
        };
        WireMarkerMouse();

        // any knob turned redraws the same map under the new settings; the dice draw a new one
        void Redraw(object s, EventArgs e) { if (!mapBusy) MapDraw(false); }
        foreach (var c in new Control[] { mapGround, mapTime, mapWater, mapSky, mapTrail, mapRail, mapTown, mapGrid, mapSecrets })
        {
            if (c is ComboBox cb) cb.SelectedIndexChanged += Redraw;
            else if (c is CheckBox ck) ck.CheckedChanged += Redraw;
        }
        mapLm.ValueChanged += Redraw;
        mapSeed.ValueChanged += Redraw;
        mapScale.SelectedIndexChanged += (s, e) =>
        {
            if (mapBusy) return;
            mapBusy = true;
            mapGrid.Checked = mapScale.SelectedIndex == 0;    // a gunfight wants its squares
            mapBusy = false;
            MapDraw(false);
        };

        // The whole drafting table — three bars and the map — lives in ONE host panel so that going
        // full screen can move the real thing rather than build a second copy of it. A full-screen
        // view with its own rebuilt bar would be eleven combo boxes and twenty buttons written
        // twice, and the day the two disagree is the day a Keeper draws a map they cannot reproduce.
        mapHost = new Panel { Dock = DockStyle.Fill, BackColor = Paper };
        mapHost.Controls.Add(mapPanel);
        mapHost.Controls.Add(rowWork);   // Dock=Top stacks bottom-up: last added sits highest
        mapHost.Controls.Add(rowView);
        mapHost.Controls.Add(rowGen);
        page.Controls.Add(mapHost);
        MapDraw(true);
        return page;
    }

    // ---------------------------------------------------------- full screen
    Panel mapHost;
    bool mapFull;

    /// <summary>Send the map away to a second window and bring it back, without showing anything —
    /// the reparenting half of <see cref="MapFullScreen"/> with the modal taken out, so
    /// <c>--selftest</c> can prove the Map tab survives the round trip. Hands back true when the
    /// host is home again with all four of its children.
    ///
    /// Worth a check of its own because of what the failure looks like: not a crash, not a wrong
    /// number, just a Map tab that is empty for the rest of the session with the survey still
    /// parented to a window nobody can see.</summary>
    internal bool MapFullScreenRoundTrip()
    {
        if (mapHost == null) return false;
        var home = mapHost.Parent;
        if (home == null) return false;
        int had = mapHost.Controls.Count;
        using (var f = new Sheet { FormBorderStyle = FormBorderStyle.None, ShowInTaskbar = false })
        {
            mapHost.Parent = f;
            if (mapHost.Parent != f) return false;
            mapHost.Parent = home;
        }
        return mapHost.Parent == home && mapHost.Controls.Count == had && !mapHost.IsDisposed
            && mapPanel is { IsDisposed: false };
    }

    /// <summary>Show the map across the whole screen, carrying its own controls with it.
    ///
    /// The host panel is REPARENTED into a borderless window and handed back afterwards, so
    /// everything available while the map is in its tab is available here — the same ground, scale,
    /// hour and weather boxes, the same overlay checks, the same markers, the same exports, and the
    /// same objects behind them. Nothing here is a copy that could fall out of step.
    ///
    /// Modal on purpose: the tab it came from is standing empty while its contents are away, and a
    /// modeless window would let a Keeper click back to a blank Map tab and conclude the app had
    /// lost their survey. Esc closes it, as every dialog in this app does; so does the ✕, and so
    /// does F11, which is what a full screen is expected to answer.</summary>
    internal void MapFullScreen()
    {
        if (mapHost == null || mapFull) return;
        var home = mapHost.Parent;
        if (home == null) return;

        using var f = new Sheet
        {
            Text = "The Trail Maps drafting table — full screen",
            FormBorderStyle = FormBorderStyle.None, StartPosition = FormStartPosition.Manual,
            ShowInTaskbar = false, BackColor = Paper, KeyPreview = true,
            Bounds = Screen.FromControl(this).Bounds
        };
        if (AppIcon != null) f.Icon = AppIcon;

        var strip = new FlowLayoutPanel
        {
            Dock = DockStyle.Top, AutoSize = true, FlowDirection = FlowDirection.RightToLeft,
            Padding = new Padding(6, 4, 8, 4), BackColor = Color.FromArgb(243, 237, 221)
        };
        var close = new Button
        {
            Text = "✕  Close  (Esc)", Width = 132, Height = 30, Margin = new Padding(3),
            DialogResult = DialogResult.Cancel
        };
        Tip.SetToolTip(close, "Put the map back on its tab — Esc and F11 do the same");
        strip.Controls.Add(close);
        var says = new Label
        {
            AutoSize = true, ForeColor = GoldDeep, Padding = new Padding(10, 8, 4, 0),
            Font = new Font("Segoe UI", 9f, FontStyle.Italic),
            Text = "Every control the tab has is on this screen. Esc, F11 or ✕ puts it back."
        };
        strip.Controls.Add(says);

        f.KeyDown += (s, e) => { if (e.KeyCode == Keys.F11) { e.Handled = true; f.Close(); } };
        f.CancelButton = close;

        // Pan is a pixel offset against the panel that was on screen when it was dragged, so it
        // means nothing once the panel is four times the size. Zoom is a magnification and travels
        // fine, so it is kept and only the pan is dropped — the view re-centres at the same scale.
        void Rehome(Control to)
        {
            home.SuspendLayout(); to.SuspendLayout();
            mapHost.Parent = to;
            mapPan = PointF.Empty;
            to.ResumeLayout(true); home.ResumeLayout(true);
            mapPanel.Invalidate();
        }

        mapFull = true;
        try
        {
            // If this throws between here and the finally, the finally still hands the host back.
            // That is the whole reason this is a try/finally rather than a straight line. The
            // failure it guards against arrives with nothing to read: a Map tab that stays blank
            // until the app is restarted, and a Keeper with no way of knowing their survey is
            // still parented to a window that went away.
            // Host first, strip second. Docking resolves from the highest index down, so the strip
            // takes the top edge and the host fills whatever is left — the same order the tabs use.
            Rehome(f);
            f.Controls.Add(strip);
            Log("The map is full screen — Esc, F11 or ✕ brings it back.");
            f.ShowDialog(this);
        }
        finally
        {
            // Unconditional: `using` disposes the window on the way out, and a host still parented
            // to it would be disposed WITH it — the Map tab would come back permanently empty.
            Rehome(home);
            mapFull = false;
        }
    }

    MapSpec MapSpecFromUi() => new()
    {
        Terrain = mapGround.SelectedItem.ToString(),
        Scale = mapScale.SelectedIndex,
        Time = mapTime.SelectedIndex,
        Water = mapWater.SelectedIndex,
        Weather = mapSky.SelectedIndex,
        Trail = mapTrail.Checked, Rail = mapRail.Checked, Town = mapTown.Checked,
        Grid = mapGrid.Checked, Secrets = mapSecrets.Checked,
        Landmarks = (int)mapLm.Value,
        Seed = (int)mapSeed.Value,
        PlaceName = mapName?.Text ?? ""
    };

    /// <summary>Draw a survey of a place the Keeper has already rolled up on the Generators tab.
    ///
    /// Both scales are offered for both kinds of settlement, which is the point: before v1.25.0 a
    /// city could ONLY be drawn as a ward, so there was no way to ask "and what is around it?" —
    /// the one question a posse riding toward a city actually has. Now either can be surveyed as
    /// itself or set down in open country, and the country can be rolled or named.</summary>
    /// <param name="placeName">The rolled-up place's name, as the Generators tab left it.</param>
    /// <param name="city">True for a city, false for a town — the two roll up differently.</param>
    /// <param name="view">Survey the place itself, or set it down in open country.</param>
    /// <param name="terrain">The ground to set it in. Null rolls one — "surprise me" being most
    /// of what a generator is for. Ignored unless the view is <see cref="PlaceView.InItsCountry"/>.</param>
    internal void SendPlaceToMap(string placeName, bool city, PlaceView view = PlaceView.Itself, string terrain = null)
    {
        if (string.IsNullOrWhiteSpace(placeName)) { Nope("Roll a town or a city first."); return; }
        // Realizes the tab if this is its first visit — and says so plainly if this table is being
        // run in a player's view, where there is no Map tab to send anything to.
        if (!ShowTab("Map") || mapName == null) { Nope("The Map is a Keeper's tab — switch tables under the Table menu."); return; }

        mapBusy = true;
        mapName.Text = placeName.Trim();
        string ground;

        if (view == PlaceView.InItsCountry)
        {
            // One mark on open ground, a day's ride across. The settlement is still drawn (mapTown
            // below) — it is simply no longer the whole sheet.
            ground = terrain ?? MapGen.SettingTerrains[Rules.Rng.Next(MapGen.SettingTerrains.Length)];
            mapScale.SelectedIndex = Array.IndexOf(MapGen.Scales, "A county (a day's ride)");
            mapGrid.Checked = false;
        }
        else if (city)
        {
            ground = "The Lamplit City";
            mapScale.SelectedIndex = Array.IndexOf(MapGen.Scales, "A city ward (blocks)");
            mapGrid.Checked = false;
        }
        else
        {
            // A town you can walk, where the buildings are the map rather than a dot on it.
            ground = "Towns, Homesteads & Haunted Houses";
            mapScale.SelectedIndex = Array.IndexOf(MapGen.Scales, "A homestead (half a mile)");
        }

        mapGround.SelectedIndex = Math.Max(0, Array.IndexOf(MapGen.Terrains, ground));
        mapTown.Checked = true;                // a place with a name is a place that is drawn
        mapBusy = false;
        MapDraw(true);                         // a new place is a new survey, not a relabelled old one

        string what = view == PlaceView.InItsCountry
            ? $"{mapName.Text} and the country around it — {ground.ToLowerInvariant()}"
            : city ? $"The ward of {mapName.Text}" : $"The town of {mapName.Text}";
        Log($"{what} — surveyed as map N° {(int)mapSeed.Value}.");
    }

    internal void MapDraw(bool newSeed)
    {
        if (mapBusy) return;
        mapBusy = true;
        if (newSeed) mapSeed.Value = Rules.Rng.Next(0, 1000000);
        curMap = MapGen.Generate(MapSpecFromUi());
        lmDragIdx = -1; secDragIdx = -1; townDrag = false;   // the model they pointed into is gone
        int seed = (int)mapSeed.Value;
        if (seed != lmEditSeed) { lmEdits.Clear(); secEdits.Clear(); townEdit = null; lmEditSeed = seed; }
        else                                              // same survey, rebuilt (hour, layer…) — hold the Keeper's placements
        {
            for (int i = 0; i < curMap.Landmarks.Count; i++)
                if (lmEdits.TryGetValue(curMap.Landmarks[i].Name, out var at))
                    MapGen.MoveLandmark(curMap, i, at.x, at.y);
            for (int i = 0; i < curMap.Secrets.Count; i++)
                if (secEdits.TryGetValue(i, out var at))
                    MapGen.MoveSecret(curMap, i, at.x, at.y);
            if (townEdit is (float tex, float tey)) MapGen.MoveTown(curMap, tex, tey);
        }
        mapPanel.Model = curMap;
        mapPanel.Invalidate();
        mapBusy = false;
        // Name the sky as well as the map — when the Keeper leaves it on "as the sky wills", the
        // country rolls its own, and they're owed the answer without squinting at the cartouche.
        Log($"Map drawn: {curMap.Title}, N° {(int)mapSeed.Value} — {MapGen.WeatherLine(Array.IndexOf(MapGen.Weathers, curMap.Weather))}.");
        // Say it plainly when the survey wanted the town in the river and it was seated on the
        // bank instead — otherwise a map number that used to draw a town in the water quietly
        // draws it somewhere else, and that reads like a bug.
        if (curMap.TownSeated && curMap.Town != null)
            Log($"{curMap.Town.Name} was seated on the bank — the survey had it standing in the water.");
    }

    /// <summary>The markers as export ink, or null for "the survey alone". Null rather than an empty
    /// list when the box is unchecked, so the writers take their no-overlay path outright.</summary>
    List<Prim> MarkerOverlay()
        => mapMarkOut != null && mapMarkOut.Checked && mapMarkers.Count > 0 && curMap != null
            ? MapGen.MarkerPrims(mapMarkers, curMap.W, curMap.H)
            : null;

    /// <summary>What to say about the markers when a file is written. A map that quietly comes out
    /// without the markers the Keeper spent ten minutes arranging is a map they'll assume is broken,
    /// so the log says which way it went — and, when they're left off, where the switch is.</summary>
    string MarkerNote()
    {
        if (mapMarkers.Count == 0) return "";
        return mapMarkOut != null && mapMarkOut.Checked
            ? $" — {mapMarkers.Count} marker(s) drawn on it"
            : $" — the survey alone; {mapMarkers.Count} marker(s) stayed on screen (tick “with markers” to include them)";
    }

    static string MapSlug(string title) =>
        new string(title.ToLowerInvariant().Select(c => char.IsLetterOrDigit(c) ? c : '-').ToArray()).Trim('-');

    void MapSaveSvg()
    {
        if (curMap == null) return;
        using var d = new SaveFileDialog
        {
            Title = "Save the map as SVG",
            Filter = "Scalable Vector Graphics (*.svg)|*.svg|All files (*.*)|*.*",
            FileName = $"{MapSlug(curMap.Title)}-{(int)mapSeed.Value}.svg"
        };
        if (d.ShowDialog(this) != DialogResult.OK) return;
        try
        {
            File.WriteAllText(d.FileName, MapGen.ToSvg(curMap, MarkerOverlay()), new UTF8Encoding(false));
            Log($"Map saved: {Path.GetFileName(d.FileName)}{MarkerNote()}.");
        }
        catch (Exception ex)
        {
            MessageBox.Show("Couldn't save there:\r\n\r\n" + ex.Message, "Blood & Grit", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    void MapSavePdf()
    {
        if (curMap == null) return;
        using var d = new SaveFileDialog
        {
            Title = "Save the map as PDF",
            Filter = "PDF (*.pdf)|*.pdf|All files (*.*)|*.*",
            FileName = $"{MapSlug(curMap.Title)}-{(int)mapSeed.Value}.pdf"
        };
        if (d.ShowDialog(this) != DialogResult.OK) return;
        try
        {
            File.WriteAllBytes(d.FileName, Pdf.MapPdf(curMap, MarkerOverlay()));
            Log($"Map saved: {Path.GetFileName(d.FileName)} (landscape Letter){MarkerNote()}.");
        }
        catch (Exception ex)
        {
            MessageBox.Show("Couldn't save there:\r\n\r\n" + ex.Message, "Blood & Grit", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    // ---------------------------------------------------------- markers
    void DrawMarkers(Graphics g, MapModel m, Rectangle dest)
    {
        if (mapMarkers.Count == 0) return;
        var (s, ox, oy) = MapXform(m, dest);
        if (s <= 0) return;
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
        using var f = new Font("Segoe UI", 8.5f, FontStyle.Bold);
        using var ink = new Pen(Ink, 1.8f);
        using var held = new Pen(Gold, 3f);
        using var inkBrush = new SolidBrush(Ink);
        using var halo = new SolidBrush(Color.FromArgb(210, Paper));
        foreach (var mk in mapMarkers)
        {
            float x = ox + Math.Clamp(mk.X, 0, m.W) * s, y = oy + Math.Clamp(mk.Y, 0, m.H) * s;
            using var b = new SolidBrush(Color.FromArgb(MapInk.Of(mk)));
            g.FillEllipse(b, x - 8, y - 8, 16, 16);
            g.DrawEllipse(mk == dragMarker ? held : ink, x - 8, y - 8, 16, 16);
            var sz = g.MeasureString(mk.Label, f);
            g.FillRectangle(halo, x + 10, y - sz.Height / 2, sz.Width, sz.Height);
            g.DrawString(mk.Label, f, inkBrush, x + 10, y - sz.Height / 2);
        }
    }

    MapMarker HitMarker(Point p)
    {
        if (mapPanel.Model == null) return null;
        var (s, ox, oy) = MapXform(mapPanel.Model, mapPanel.ClientRectangle);
        if (s <= 0) return null;
        // walk backward so the most recently drawn (topmost) marker wins the click
        for (int i = mapMarkers.Count - 1; i >= 0; i--)
        {
            float x = ox + mapMarkers[i].X * s, y = oy + mapMarkers[i].Y * s;
            if ((p.X - x) * (p.X - x) + (p.Y - y) * (p.Y - y) <= 12 * 12) return mapMarkers[i];
        }
        return null;
    }

    void WireMarkerMouse()
    {
        mapPanel.MouseWheel += (s, e) => MapZoomAt(e.Location, e.Delta > 0 ? 1.2f : 1 / 1.2f);
        // Double-click the open country to throw the map across the screen. Deliberately only the
        // open country: with Moving on, or with the pointer on a marker, a double-click is two
        // grabs at the thing under it, and answering that with a window would take the map away
        // mid-drag. So a double-click that landed on anything draggable does nothing here and lets
        // the drag handlers have it.
        mapPanel.MouseDoubleClick += (s, e) =>
        {
            if (e.Button != MouseButtons.Left || mapFull) return;
            if (HitMarker(e.Location) != null) return;
            if (lmEditMode && (HitLandmark(e.Location) >= 0 || HitSecret(e.Location) >= 0 || HitTown(e.Location))) return;
            MapFullScreen();
        };
        mapPanel.MouseDown += (s, e) =>
        {
            mapPanel.Focus();                       // so the wheel zooms after any click on the map
            if (e.Button != MouseButtons.Left) return;
            dragMarker = HitMarker(e.Location);
            dragMoved = false;
            if (dragMarker != null) { mapPanel.Invalidate(); return; }
            if (lmEditMode)
            {
                lmDragIdx = HitLandmark(e.Location);
                lmDragMoved = false;
                if (lmDragIdx >= 0) { mapPanel.Invalidate(); return; }
                secDragIdx = HitSecret(e.Location);
                secDragMoved = false;
                if (secDragIdx >= 0) { mapPanel.Invalidate(); return; }
                // the town is tested last: a landmark standing in the town's streets is the
                // smaller, more precise target, so it wins the click
                if (HitTown(e.Location)) { townDrag = true; townDragMoved = false; mapPanel.Invalidate(); return; }
            }
            if (mapZoom > 1f)                       // empty ground while zoomed — pan the view
            {
                mapPanning = true;
                mapPanLast = e.Location;
                mapPanel.Cursor = Cursors.SizeAll;
            }
        };
        mapPanel.MouseMove += (s, e) =>
        {
            if (mapPanning)
            {
                mapPan = new PointF(mapPan.X + e.X - mapPanLast.X, mapPan.Y + e.Y - mapPanLast.Y);
                mapPanLast = e.Location;
                mapPanel.Invalidate();
                return;
            }
            var m = mapPanel.Model;
            if (m == null) return;
            var (sc, ox, oy) = MapXform(m, mapPanel.ClientRectangle);
            if (sc <= 0) return;
            if (dragMarker != null)
            {
                dragMarker.X = Math.Clamp((e.X - ox) / sc, 0, m.W);
                dragMarker.Y = Math.Clamp((e.Y - oy) / sc, 0, m.H);
                dragMoved = true;
                mapPanel.Invalidate();
                return;
            }
            if (lmDragIdx >= 0)
            {
                // keep the symbol and its label inside the neatline
                float nx = Math.Clamp((e.X - ox) / sc, 32, m.W - 32);
                float ny = Math.Clamp((e.Y - oy) / sc, 32, m.H - 48);
                MapGen.MoveLandmark(m, lmDragIdx, nx, ny);
                lmDragMoved = true;
                mapPanel.Invalidate();
                return;
            }
            if (secDragIdx >= 0)
            {
                float nx = Math.Clamp((e.X - ox) / sc, 32, m.W - 32);
                float ny = Math.Clamp((e.Y - oy) / sc, 32, m.H - 48);
                MapGen.MoveSecret(m, secDragIdx, nx, ny);
                secDragMoved = true;
                mapPanel.Invalidate();
                return;
            }
            if (townDrag && m.Town != null)
            {
                // a town needs more elbow room than a single mark — it carries its street and its name
                float reach = MapGen.TownReach(mapScale.SelectedIndex);
                float nx = Math.Clamp((e.X - ox) / sc, reach * 0.4f + 24, m.W - reach * 0.4f - 24);
                float ny = Math.Clamp((e.Y - oy) / sc, 40, m.H - 72);
                MapGen.MoveTown(m, nx, ny);
                townDragMoved = true;
                mapPanel.Invalidate();
                return;
            }
            // nothing in hand — show what's grabbable under the cursor
            mapPanel.Cursor = HitMarker(e.Location) != null
                || (lmEditMode && (HitLandmark(e.Location) >= 0 || HitSecret(e.Location) >= 0 || HitTown(e.Location)))
                ? Cursors.Hand : Cursors.Default;
        };
        mapPanel.MouseUp += (s, e) =>
        {
            if (mapPanning) { mapPanning = false; mapPanel.Cursor = Cursors.Default; return; }
            if (e.Button == MouseButtons.Right)
            {
                var mk = HitMarker(e.Location);
                if (mk != null)
                {
                    var menu = PopupMenu();
                    menu.Items.Add($"Rename {mk.Label}…", null, (ss, ee) =>
                    {
                        string n = AskLine("Rename the marker", mk.Label);
                        if (!string.IsNullOrWhiteSpace(n)) { mk.Label = n.Trim(); CaptureUndo(); mapPanel.Invalidate(); }
                    });
                    menu.Items.Add(InkMenu($"Color — {MapInk.NameOf(MapInk.Of(mk))}", MapInk.Of(mk),
                        mk.Argb == MapInk.Unset ? null : $"Back to the {mk.Kind} color",
                        argb =>
                        {
                            mk.Argb = argb;
                            CaptureUndo(); mapPanel.Invalidate();
                            Log(argb == MapInk.Unset
                                ? $"{mk.Label} goes back to the {mk.Kind} color."
                                : $"{mk.Label} is drawn in {MapInk.NameOf(argb).ToLowerInvariant()} now.");
                        }));
                    menu.Items.Add(new ToolStripSeparator());
                    menu.Items.Add($"Remove {mk.Label}", null, (ss, ee) =>
                    { mapMarkers.Remove(mk); CaptureUndo(); mapPanel.Invalidate(); });
                    menu.Show(mapPanel, e.Location);
                    return;
                }
                if (lmEditMode && mapPanel.Model != null)
                {
                    var m2 = mapPanel.Model;
                    int li = HitLandmark(e.Location), si = li >= 0 ? -1 : HitSecret(e.Location);
                    bool onTown = li < 0 && si < 0 && HitTown(e.Location);
                    if (li < 0 && si < 0 && !onTown) return;
                    if (onTown)
                    {
                        var town = m2.Town;
                        var tmenu = PopupMenu();
                        bool wet = MapGen.OnWater(m2, town.X, town.Y, MapGen.TownReach(mapScale.SelectedIndex));
                        var dry = tmenu.Items.Add($"Move {town.Name} onto dry ground", null, (ss, ee) =>
                        {
                            var (nx, ny) = MapGen.DryGroundNear(m2, town.X, town.Y, MapGen.TownReach(mapScale.SelectedIndex));
                            if (nx == town.X && ny == town.Y) { Nope($"{town.Name} already stands clear of the water."); return; }
                            MapGen.MoveTown(m2, nx, ny);
                            townEdit = (nx, ny);
                            lmEditSeed = (int)mapSeed.Value;
                            Log($"{town.Name} moved off the water.");
                            mapPanel.Invalidate();
                        });
                        dry.Enabled = wet;
                        if (!wet) dry.ToolTipText = "It's already on dry ground.";
                        tmenu.Items.Add($"Put {town.Name} back where the survey drew it", null, (ss, ee) =>
                        {
                            MapGen.MoveTown(m2, town.GenX, town.GenY);
                            townEdit = null;
                            mapPanel.Invalidate();
                        });
                        tmenu.Show(mapPanel, e.Location);
                        return;
                    }
                    var menu = PopupMenu();
                    if (li >= 0)
                    {
                        var lm = m2.Landmarks[li];
                        menu.Items.Add($"Put {lm.Name} back where the survey drew it", null, (ss, ee) =>
                        {
                            MapGen.MoveLandmark(m2, li, lm.GenX, lm.GenY);
                            lmEdits.Remove(lm.Name);
                            mapPanel.Invalidate();
                        });
                    }
                    else
                    {
                        var sec = m2.Secrets[si];
                        menu.Items.Add($"Put \"{sec.Name}\" back where the survey drew it", null, (ss, ee) =>
                        {
                            MapGen.MoveSecret(m2, si, sec.GenX, sec.GenY);
                            secEdits.Remove(si);
                            mapPanel.Invalidate();
                        });
                    }
                    menu.Items.Add("Put everything back", null, (ss, ee) =>
                    {
                        int n = lmEdits.Count + secEdits.Count;
                        if (n == 0) return;
                        if (!Confirm($"Put all {n} moved mark(s) back where the survey drew them?")) return;
                        for (int i = 0; i < m2.Landmarks.Count; i++)
                            MapGen.MoveLandmark(m2, i, m2.Landmarks[i].GenX, m2.Landmarks[i].GenY);
                        for (int i = 0; i < m2.Secrets.Count; i++)
                            MapGen.MoveSecret(m2, i, m2.Secrets[i].GenX, m2.Secrets[i].GenY);
                        lmEdits.Clear(); secEdits.Clear();
                        mapPanel.Invalidate();
                    });
                    menu.Show(mapPanel, e.Location);
                }
                return;
            }
            if (dragMarker != null)
            {
                if (dragMoved) CaptureUndo();      // one undo step per completed drag
                dragMarker = null;
                mapPanel.Invalidate();
                return;
            }
            if (lmDragIdx >= 0)
            {
                if (lmDragMoved && mapPanel.Model != null)
                {
                    var lm = mapPanel.Model.Landmarks[lmDragIdx];
                    lmEdits[lm.Name] = (lm.X, lm.Y);
                    lmEditSeed = (int)mapSeed.Value;
                }
                lmDragIdx = -1;
                mapPanel.Invalidate();
                return;
            }
            if (secDragIdx >= 0)
            {
                if (secDragMoved && mapPanel.Model != null)
                {
                    var sec = mapPanel.Model.Secrets[secDragIdx];
                    secEdits[secDragIdx] = (sec.X, sec.Y);
                    lmEditSeed = (int)mapSeed.Value;
                }
                secDragIdx = -1;
                mapPanel.Invalidate();
                return;
            }
            if (townDrag)
            {
                if (townDragMoved && mapPanel.Model?.Town != null)
                {
                    townEdit = (mapPanel.Model.Town.X, mapPanel.Model.Town.Y);
                    lmEditSeed = (int)mapSeed.Value;
                }
                townDrag = false;
                mapPanel.Invalidate();
            }
        };
    }

    // The town is grabbed anywhere in its seat — a broad target, since it's a broad thing.
    bool HitTown(Point p)
    {
        var m = mapPanel.Model;
        if (m?.Town == null) return false;
        var (s, ox, oy) = MapXform(m, mapPanel.ClientRectangle);
        if (s <= 0) return false;
        float x = ox + m.Town.X * s, y = oy + m.Town.Y * s;
        float r = Math.Max(22f, MapGen.TownReach(mapScale.SelectedIndex) * 0.5f * s);
        return (p.X - x) * (p.X - x) + (p.Y - y) * (p.Y - y) <= r * r;
    }

    int HitSecret(Point p)
    {
        var m = mapPanel.Model;
        if (m == null) return -1;
        var (s, ox, oy) = MapXform(m, mapPanel.ClientRectangle);
        if (s <= 0) return -1;
        for (int i = m.Secrets.Count - 1; i >= 0; i--)
        {
            float x = ox + m.Secrets[i].X * s, y = oy + m.Secrets[i].Y * s;
            if ((p.X - x) * (p.X - x) + (p.Y - y) * (p.Y - y) <= 16 * 16) return i;
        }
        return -1;
    }

    // While landmark editing is on, every named landmark wears a dashed gold ring —
    // the grab handle — and the one in hand rings solid. Off, the map stays clean.
    void DrawLandmarkHandles(Graphics g, MapModel m, Rectangle dest)
    {
        if (!lmEditMode) return;
        var (s, ox, oy) = MapXform(m, dest);
        if (s <= 0) return;
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;

        // A banner across the top while moving is on, so the mode is never a secret the Keeper
        // has to remember they turned on.
        using (var f = new Font("Segoe UI", 9f, FontStyle.Bold))
        using (var band = new SolidBrush(Color.FromArgb(224, 244, 236, 210)))
        using (var edge = new Pen(Gold, 1.4f))
        using (var ink = new SolidBrush(Ink))
        {
            string hint = "Moving is on — drag the town, a landmark, or a red secret. Right-click one to put it back.";
            var sz = g.MeasureString(hint, f);
            float bw = sz.Width + 22, bx = dest.X + (dest.Width - bw) / 2, by = dest.Y + 6;
            g.FillRectangle(band, bx, by, bw, sz.Height + 8);
            g.DrawRectangle(edge, bx, by, bw, sz.Height + 8);
            g.DrawString(hint, f, ink, bx + 11, by + 4);
        }

        // the town rings like everything else that can be picked up
        if (m.Town != null)
        {
            float r = Math.Max(24f, MapGen.TownReach(mapScale.SelectedIndex) * 0.5f * s);
            using var townRing = new Pen(Gold, townDrag ? 2.6f : 1.6f) { DashPattern = new[] { 5f, 3.5f } };
            float tx = ox + m.Town.X * s, ty = oy + m.Town.Y * s;
            g.DrawEllipse(townRing, tx - r, ty - r, r * 2, r * 2);
        }
        using var ring = new Pen(Gold, 1.6f) { DashPattern = new[] { 3f, 2.5f } };
        using var held = new Pen(Gold, 2.6f);
        for (int i = 0; i < m.Landmarks.Count; i++)
        {
            float x = ox + m.Landmarks[i].X * s, y = oy + m.Landmarks[i].Y * s;
            g.DrawEllipse(i == lmDragIdx ? held : ring, x - 14, y - 14, 28, 28);
        }
        // the Keeper's marks ring in their own red, so the two kinds never read as one
        using var secRing = new Pen(Blood, 1.6f) { DashPattern = new[] { 3f, 2.5f } };
        using var secHeld = new Pen(Blood, 2.6f);
        for (int i = 0; i < m.Secrets.Count; i++)
        {
            float x = ox + m.Secrets[i].X * s, y = oy + m.Secrets[i].Y * s;
            g.DrawEllipse(i == secDragIdx ? secHeld : secRing, x - 20, y - 20, 40, 40);
        }
    }

    // A landmark is grabbed by its symbol — generous 16px screen radius, topmost wins.
    int HitLandmark(Point p)
    {
        var m = mapPanel.Model;
        if (m == null) return -1;
        var (s, ox, oy) = MapXform(m, mapPanel.ClientRectangle);
        if (s <= 0) return -1;
        for (int i = m.Landmarks.Count - 1; i >= 0; i--)
        {
            float x = ox + m.Landmarks[i].X * s, y = oy + m.Landmarks[i].Y * s;
            if ((p.X - x) * (p.X - x) + (p.Y - y) * (p.Y - y) <= 16 * 16) return i;
        }
        return -1;
    }

    void ShowMarkerMenu(Button host)
    {
        var menu = PopupMenu();
        foreach (var p in party)
        {
            var soul = p;
            menu.Items.Add($"{soul.Name}  ({soul.Calling})", null, (s, e) => AddMarker(soul.Name, "posse"));
        }
        if (party.Count > 0) menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add("An NPC…", null, (s, e) =>
        { string n = AskLine("Name the NPC", ""); if (!string.IsNullOrWhiteSpace(n)) AddMarker(n.Trim(), "npc"); });
        menu.Items.Add("A creature…", null, (s, e) =>
        { string n = AskLine("Name the creature", ""); if (!string.IsNullOrWhiteSpace(n)) AddMarker(n.Trim(), "creature"); });
        menu.Show(host, new Point(0, host.Height));
    }

    // ---------------------------------------------------------- marker ink
    // Four riders all drawn the same verdigris are four dots the table argues about. A marker
    // can take its own color, and a whole kind can be re-inked for good — the first travels in
    // the session file with the marker, the second in prefs.json with the Keeper.

    // Swatches live as long as the app does. The menus below are rebuilt on every right-click
    // by design, and an Image handed to a ToolStripItem isn't reliably disposed with the item,
    // so building them per click would leak a bitmap a click. The palette is ten colors; the
    // rest of the cache is however many the Keeper mixes by hand, which is not a growth curve.
    static readonly Dictionary<int, Image> swatchCache = new();

    static Image Swatch(int argb)
    {
        if (swatchCache.TryGetValue(argb, out var img)) return img;
        var bmp = new Bitmap(16, 16);
        using (var g = Graphics.FromImage(bmp))
        using (var b = new SolidBrush(Color.FromArgb(argb)))
        using (var pen = new Pen(Color.FromArgb(96, 86, 70)))
        { g.FillRectangle(b, 2, 2, 12, 12); g.DrawRectangle(pen, 2, 2, 12, 12); }
        swatchCache[argb] = bmp;
        return bmp;
    }

    /// <summary>The ink choices as a submenu: the palette with the current color ticked, a mixer for
    /// anything else, and — when <paramref name="backLabel"/> is given — the way back to the default.
    /// <paramref name="pick"/> receives the chosen ARGB, or <see cref="MapInk.Unset"/> for "back".</summary>
    ToolStripMenuItem InkMenu(string head, int current, string backLabel, Action<int> pick)
    {
        var sub = new ToolStripMenuItem(Amp(head), Swatch(current));
        foreach (var (name, argb) in MapInk.Palette)
        {
            int c = argb;
            sub.DropDownItems.Add(new ToolStripMenuItem(name, Swatch(c), (s, e) => pick(c))
            { Checked = c == current });
        }
        sub.DropDownItems.Add(new ToolStripSeparator());
        sub.DropDownItems.Add("Mix another color…", null, (s, e) =>
        {
            using var d = new ColorDialog { Color = Color.FromArgb(current), FullOpen = true, AnyColor = true };
            if (d.ShowDialog(this) == DialogResult.OK) pick(d.Color.ToArgb());
        });
        if (backLabel != null)
            sub.DropDownItems.Add(Amp(backLabel), null, (s, e) => pick(MapInk.Unset));
        return sub;
    }

    /// <summary>Re-ink a whole kind at once, and keep it. Markers that have taken a color of their
    /// own are left alone — a soul the Keeper singled out shouldn't lose that to a sweep.</summary>
    void ShowKindInkMenu(Button host)
    {
        var menu = PopupMenu();
        foreach (var (kind, said) in new[] { ("posse", "The posse"), ("npc", "NPCs"), ("creature", "Creatures") })
        {
            string k = kind;
            int cur = MapInk.KindColor(k);
            menu.Items.Add(InkMenu($"{said} — {MapInk.NameOf(cur)}", cur,
                cur == MapInk.BookColor(k) ? null : "Back to the book's color",
                argb =>
                {
                    MapInk.SetKindColor(k, argb);
                    SaveMarkerInk();
                    mapPanel.Invalidate();
                    Log($"{said} now drawn in {MapInk.NameOf(MapInk.KindColor(k)).ToLowerInvariant()} on the map.");
                }));
        }
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add("Put every kind back to the book's colors", null, (s, e) =>
        {
            MapInk.LoadKindColors(null);
            SaveMarkerInk();
            mapPanel.Invalidate();
            Log("Marker colors are back to the book's.");
        });
        menu.Show(host, new Point(0, host.Height));
    }

    void SaveMarkerInk()
    {
        var d = Prefs.Load();          // read-modify-write: this file also holds the run mode
        d.MarkerInk = MapInk.KindColors();
        Prefs.Save(d);
    }

    void AddMarker(string label, string kind)
    {
        var m = mapPanel.Model; if (m == null) return;
        // new markers cascade from the center of the CURRENT VIEW (matters zoomed in),
        // so several drops don't stack invisibly
        var dest = mapPanel.ClientRectangle;
        var (s, ox, oy) = MapXform(m, dest);
        float cx = s > 0 ? Math.Clamp((dest.Width / 2f - ox) / s, 0, m.W) : m.W * 0.5f;
        float cy = s > 0 ? Math.Clamp((dest.Height / 2f - oy) / s, 0, m.H) : m.H * 0.5f;
        int n = mapMarkers.Count;
        mapMarkers.Add(new MapMarker
        {
            Label = label, Kind = kind,
            X = Math.Clamp(cx + (n % 5 - 2) * m.W * 0.05f / mapZoom, 0, m.W),
            Y = Math.Clamp(cy + (n / 5 % 4) * m.H * 0.06f / mapZoom, 0, m.H)
        });
        CaptureUndo();
        mapPanel.Invalidate();
        Log($"Marker placed: {label}.");
    }

    void TrackerToMap()
    {
        var m = mapPanel.Model; if (m == null) return;
        var standing = new HashSet<string>(mapMarkers.Select(x => x.Label), StringComparer.OrdinalIgnoreCase);
        var incoming = tracker.Where(c => !standing.Contains(c.Name)).ToList();
        if (incoming.Count == 0) { Log("Everyone on the tracker already stands on the map."); return; }
        var pcs  = incoming.Where(c => c.IsPC).ToList();
        var foes = incoming.Where(c => !c.IsPC).ToList();
        void Column(List<Combatant> list, float x)
        {
            for (int i = 0; i < list.Count; i++)
                mapMarkers.Add(new MapMarker
                {
                    Label = list[i].Name,
                    Kind = list[i].IsPC ? "posse" : list[i].Ref != "" ? "creature" : "npc",
                    X = x,
                    Y = m.H * (i + 1f) / (list.Count + 1)
                });
        }
        Column(pcs, m.W * 0.18f);
        Column(foes, m.W * 0.82f);
        CaptureUndo();
        mapPanel.Invalidate();
        Log($"{incoming.Count} marker(s) take the field — posse west, trouble east. Drag them into position.");
    }

    // A one-line ask — small, centered on the app, Enter accepts, Esc cancels.
    string AskLine(string title, string initial)
    {
        using var dlg = new Sheet
        {
            Text = title, Width = 340, Height = 128, FormBorderStyle = FormBorderStyle.FixedDialog,
            StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false,
            BackColor = Paper, Font = new Font("Segoe UI", 9.5f)
        };
        var box = new TextBox { Left = 12, Top = 14, Width = 300, Text = initial };
        var ok = new Button { Text = "Place", DialogResult = DialogResult.OK, Left = 146, Top = 48, Width = 80 };
        var cancel = new Button { Text = "Cancel", DialogResult = DialogResult.Cancel, Left = 232, Top = 48, Width = 80 };
        dlg.Controls.AddRange(new Control[] { box, ok, cancel });
        dlg.AcceptButton = ok; dlg.CancelButton = cancel;
        box.SelectAll();
        return dlg.ShowDialog(this) == DialogResult.OK ? box.Text : null;
    }

    // ---------------------------------------------------------- GDI replay
    // The on-screen renderer for the primitive list — the same drawing the SVG and
    // PDF exports make, scaled to fit whatever room the panel has.
    void DrawModel(Graphics g, MapModel m, Rectangle dest)
    {
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
        g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
        var (s, ox, oy) = MapXform(m, dest);
        if (s <= 0) return;
        var state = g.Save();
        g.TranslateTransform(ox, oy);
        g.ScaleTransform(s, s);

        Color? Col(string hex, float alpha) => hex == null ? null
            : Color.FromArgb((int)(Math.Clamp(alpha, 0f, 1f) * 255),
                Convert.ToInt32(hex.Substring(1, 2), 16), Convert.ToInt32(hex.Substring(3, 2), 16), Convert.ToInt32(hex.Substring(5, 2), 16));

        foreach (var p in m.P)
        {
            var fill = Col(p.Fill, p.Alpha);
            var stroke = Col(p.Stroke, p.Alpha);
            Pen MkPen()
            {
                var pen = new Pen(stroke.Value, p.StrokeW) { StartCap = System.Drawing.Drawing2D.LineCap.Round, EndCap = System.Drawing.Drawing2D.LineCap.Round, LineJoin = System.Drawing.Drawing2D.LineJoin.Round };
                if (p.Dash != null) pen.DashPattern = p.Dash.Select(d => Math.Max(0.1f, d / p.StrokeW)).ToArray();
                return pen;
            }
            switch (p.Kind)
            {
                case PrimKind.Poly:
                {
                    var pts = new PointF[p.Pts.Length / 2];
                    for (int i = 0; i < pts.Length; i++) pts[i] = new PointF(p.Pts[i * 2], p.Pts[i * 2 + 1]);
                    if (fill != null) { using var b = new SolidBrush(fill.Value); g.FillPolygon(b, pts); }
                    if (stroke != null) { using var pen = MkPen(); g.DrawPolygon(pen, pts); }
                    break;
                }
                case PrimKind.Line:
                {
                    if (stroke == null || p.Pts.Length < 4) break;
                    var pts = new PointF[p.Pts.Length / 2];
                    for (int i = 0; i < pts.Length; i++) pts[i] = new PointF(p.Pts[i * 2], p.Pts[i * 2 + 1]);
                    using var pen = MkPen();
                    g.DrawLines(pen, pts);
                    break;
                }
                case PrimKind.Circle:
                {
                    var r = new RectangleF(p.Pts[0] - p.Pts[2], p.Pts[1] - p.Pts[2], p.Pts[2] * 2, p.Pts[2] * 2);
                    if (fill != null) { using var b = new SolidBrush(fill.Value); g.FillEllipse(b, r); }
                    if (stroke != null) { using var pen = MkPen(); g.DrawEllipse(pen, r); }
                    break;
                }
                case PrimKind.Text:
                {
                    var style = (p.Bold ? FontStyle.Bold : FontStyle.Regular) | (p.Italic ? FontStyle.Italic : FontStyle.Regular);
                    using var f = new Font("Georgia", p.FontSize, style, GraphicsUnit.Pixel);
                    var ff = f.FontFamily;
                    float ascent = p.FontSize * ff.GetCellAscent(style) / ff.GetEmHeight(style);
                    float w = g.MeasureString(p.Text, f, PointF.Empty, StringFormat.GenericTypographic).Width;
                    float x = p.Pts[0] - (p.Anchor == 1 ? w / 2 : p.Anchor == 2 ? w : 0);
                    using var b = new SolidBrush(Col(p.Fill ?? "#4a3826", p.Alpha).Value);
                    g.DrawString(p.Text, f, b, x, p.Pts[1] - ascent, StringFormat.GenericTypographic);
                    break;
                }
            }
        }
        g.Restore(state);
    }
}
