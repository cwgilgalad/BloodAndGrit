using System.Text;

namespace BloodAndGritKeeper;

public partial class MainForm
{
    // ============================================================ MAP TAB
    // The Trail Maps drafting table: set the ground, the scale, and the hour, and
    // MapGen draws a named frontier survey. The preview here, the SVG export, and
    // the PDF export all replay the same primitive list, so they always match.
    ComboBox mapGround, mapScale, mapTime, mapWater;
    CheckBox mapTrail, mapRail, mapTown, mapGrid, mapSecrets;
    NumericUpDown mapLm, mapSeed;
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
            SetStyle(ControlStyles.Selectable, true);   // so a click can focus it and the wheel zooms
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
        rowGen.Controls.Add(Lbl(" Landmarks:"));
        mapLm = new NumericUpDown { Minimum = 0, Maximum = 12, Value = 5, Width = 48, Margin = new Padding(3, 6, 3, 3) };
        Tip.SetToolTip(mapLm, "How many named places the survey marks");
        rowGen.Controls.Add(mapLm);
        rowGen.Controls.Add(Lbl(" Seed:"));
        mapSeed = new NumericUpDown { Minimum = 0, Maximum = 999999, Value = 0, Width = 74, Margin = new Padding(3, 6, 3, 3) };
        Tip.SetToolTip(mapSeed, "The map's number — the same seed and settings always draw the same map");
        rowGen.Controls.Add(mapSeed);
        rowGen.Controls.Add(Btn("🎲 New map", (s, e) => MapDraw(true), 92, "Draw a fresh map on a new seed (Ctrl+G)"));

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
        rowView.Controls.Add(Btn("Fit", (s, e) => { mapZoom = 1f; mapPan = PointF.Empty; mapPanel.Invalidate(); }, 46,
            "Fit the whole survey back in the window"));

        // ---- row 3: at the table, then out the door ----
        lmEditBtn = new CheckBox
        {
            Text = "✥ Landmarks", Appearance = Appearance.Button, AutoSize = false,
            Width = 105, Height = 32, Margin = new Padding(3),
            FlatStyle = FlatStyle.System, UseVisualStyleBackColor = true,
            TextAlign = ContentAlignment.MiddleCenter
        };
        Tip.SetToolTip(lmEditBtn, "Move the survey's own marks: while pressed, drag a named landmark — or a red " +
            "Keeper's-layer mark, when shown — to reposition it; right-click one to put it back. " +
            "Placements hold for this map number.");
        lmEditBtn.CheckedChanged += (s, e) =>
        {
            lmEditMode = lmEditBtn.Checked;
            if (!lmEditMode) { lmDragIdx = -1; secDragIdx = -1; }
            mapPanel.Invalidate();
            if (lmEditMode) Log("Placement: drag a named landmark (or a red secret, when shown); right-click to put it back.");
        };
        rowWork.Controls.Add(lmEditBtn);
        rowWork.Controls.Add(Btn("＋ Marker ▾", (s, e) => ShowMarkerMenu((Button)s), 100,
            "Place a marker — a posse soul, an NPC, or a creature — then drag it into position"));
        rowWork.Controls.Add(Btn("Tracker → Map", (s, e) => TrackerToMap(), 110,
            "Drop everyone on the Tracker onto the map — posse west, trouble east"));
        rowWork.Controls.Add(Btn("Clear markers", (s, e) =>
        {
            if (mapMarkers.Count == 0) { Log("No markers on the map."); return; }
            if (!Confirm($"Clear all {mapMarkers.Count} marker(s) from the map?")) return;
            mapMarkers.Clear(); CaptureUndo(); mapPanel.Invalidate();
            Log("The map is cleared of markers.");
        }, 105, "Remove every marker from the map"));
        rowWork.Controls.Add(Sep());
        rowWork.Controls.Add(Lbl("Export:"));
        rowWork.Controls.Add(Btn("Save SVG…", (s, e) => MapSaveSvg(), 95,
            "Save the map as a scalable SVG file — exactly as shown, checked overlays included"));
        rowWork.Controls.Add(Btn("Save PDF…", (s, e) => MapSavePdf(), 95,
            "Save the map as a one-page landscape PDF — exactly as shown, checked overlays included"));
        rowWork.Controls.Add(Btn("Copy SVG", (s, e) =>
        { if (curMap != null) { Clipboard.SetText(MapGen.ToSvg(curMap)); Log("Map SVG copied to the clipboard."); } }, 90,
            "Copy the SVG markup to the clipboard"));

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
        foreach (var c in new Control[] { mapGround, mapTime, mapWater, mapTrail, mapRail, mapTown, mapGrid, mapSecrets })
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

        page.Controls.Add(mapPanel);
        page.Controls.Add(rowWork);      // Dock=Top stacks bottom-up: last added sits highest
        page.Controls.Add(rowView);
        page.Controls.Add(rowGen);
        MapDraw(true);
        return page;
    }

    MapSpec MapSpecFromUi() => new()
    {
        Terrain = mapGround.SelectedItem.ToString(),
        Scale = mapScale.SelectedIndex,
        Time = mapTime.SelectedIndex,
        Water = mapWater.SelectedIndex,
        Trail = mapTrail.Checked, Rail = mapRail.Checked, Town = mapTown.Checked,
        Grid = mapGrid.Checked, Secrets = mapSecrets.Checked,
        Landmarks = (int)mapLm.Value,
        Seed = (int)mapSeed.Value
    };

    internal void MapDraw(bool newSeed)
    {
        if (mapBusy) return;
        mapBusy = true;
        if (newSeed) mapSeed.Value = Rules.Rng.Next(0, 1000000);
        curMap = MapGen.Generate(MapSpecFromUi());
        lmDragIdx = -1; secDragIdx = -1;                  // the model they pointed into is gone
        int seed = (int)mapSeed.Value;
        if (seed != lmEditSeed) { lmEdits.Clear(); secEdits.Clear(); lmEditSeed = seed; }
        else                                              // same survey, rebuilt (hour, layer…) — hold the Keeper's placements
        {
            for (int i = 0; i < curMap.Landmarks.Count; i++)
                if (lmEdits.TryGetValue(curMap.Landmarks[i].Name, out var at))
                    MapGen.MoveLandmark(curMap, i, at.x, at.y);
            for (int i = 0; i < curMap.Secrets.Count; i++)
                if (secEdits.TryGetValue(i, out var at))
                    MapGen.MoveSecret(curMap, i, at.x, at.y);
        }
        mapPanel.Model = curMap;
        mapPanel.Invalidate();
        mapBusy = false;
        Log($"Map drawn: {curMap.Title}, N° {(int)mapSeed.Value}.");
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
            File.WriteAllText(d.FileName, MapGen.ToSvg(curMap), new UTF8Encoding(false));
            Log($"Map saved: {Path.GetFileName(d.FileName)}.");
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
            File.WriteAllBytes(d.FileName, Pdf.MapPdf(curMap));
            Log($"Map saved: {Path.GetFileName(d.FileName)} (landscape Letter).");
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
            Color c = mk.Kind == "posse" ? Verdigris : mk.Kind == "npc" ? Gold : Blood;
            using var b = new SolidBrush(c);
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
            // nothing in hand — show what's grabbable under the cursor
            mapPanel.Cursor = HitMarker(e.Location) != null
                || (lmEditMode && (HitLandmark(e.Location) >= 0 || HitSecret(e.Location) >= 0))
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
                    var menu = new ContextMenuStrip { Font = new Font("Segoe UI", 9.5f) };
                    menu.Items.Add($"Rename {mk.Label}…", null, (ss, ee) =>
                    {
                        string n = AskLine("Rename the marker", mk.Label);
                        if (!string.IsNullOrWhiteSpace(n)) { mk.Label = n.Trim(); CaptureUndo(); mapPanel.Invalidate(); }
                    });
                    menu.Items.Add($"Remove {mk.Label}", null, (ss, ee) =>
                    { mapMarkers.Remove(mk); CaptureUndo(); mapPanel.Invalidate(); });
                    menu.Show(mapPanel, e.Location);
                    return;
                }
                if (lmEditMode && mapPanel.Model != null)
                {
                    var m2 = mapPanel.Model;
                    int li = HitLandmark(e.Location), si = li >= 0 ? -1 : HitSecret(e.Location);
                    if (li < 0 && si < 0) return;
                    var menu = new ContextMenuStrip { Font = new Font("Segoe UI", 9.5f) };
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
            }
        };
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
        if (!lmEditMode || (m.Landmarks.Count == 0 && m.Secrets.Count == 0)) return;
        var (s, ox, oy) = MapXform(m, dest);
        if (s <= 0) return;
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
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
        var menu = new ContextMenuStrip { Font = new Font("Segoe UI", 9.5f) };
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
        using var dlg = new Form
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
