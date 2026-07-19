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

    sealed class MapPanel : Panel
    {
        public MapModel Model;
        public MapPanel() { DoubleBuffered = true; ResizeRedraw = true; }
    }

    TabPage BuildMapTab()
    {
        var page = new TabPage("Map") { BackColor = Paper };

        var bar = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(8, 6, 8, 6), BackColor = Color.FromArgb(243, 237, 221) };
        ComboBox Combo(string[] items, int sel, int w, string tip)
        {
            var c = new ComboBox { Width = w, DropDownStyle = ComboBoxStyle.DropDownList, Margin = new Padding(3, 5, 3, 3) };
            c.Items.AddRange(items);
            c.SelectedIndex = sel;
            Tip.SetToolTip(c, tip);
            bar.Controls.Add(c);
            return c;
        }
        CheckBox Check(string text, bool val, string tip)
        {
            var c = new CheckBox { Text = text, Checked = val, AutoSize = true, Margin = new Padding(6, 8, 3, 3), ForeColor = Ink };
            Tip.SetToolTip(c, tip);
            bar.Controls.Add(c);
            return c;
        }

        bar.Controls.Add(Lbl("Ground:"));
        mapGround = Combo(MapGen.Terrains, 0, 235, "The kind of country — the Bestiary's Grounds");
        bar.Controls.Add(Lbl("  Scale:"));
        mapScale = Combo(MapGen.Scales, 2, 195, "From a single gunfight up to weeks of trail");
        bar.Controls.Add(Lbl("  Hour:"));
        mapTime = Combo(MapGen.Times, 1, 120, "The hour sets the light — night maps come with stars and a moon");
        bar.Controls.Add(Lbl("  Water:"));
        mapWater = Combo(MapGen.Waters, 0, 140, "Force a creek, river, or lake — or let the terrain decide");
        bar.Controls.Add(Lbl("  Landmarks:"));
        mapLm = new NumericUpDown { Minimum = 0, Maximum = 12, Value = 5, Width = 48, Margin = new Padding(3, 6, 3, 3) };
        Tip.SetToolTip(mapLm, "How many named places the survey marks");
        bar.Controls.Add(mapLm);
        bar.SetFlowBreak(mapLm, true);

        mapTrail = Check("Trail", true, "A trail or wagon road across the country");
        mapRail = Check("Rail", false, "A rail line — straight as money");
        mapTown = Check("Settlement", true, "A named town or camp on the trail");
        mapGrid = Check("Grid", false, "Overlay squares — a battle map's grid (on by default at gunfight scale)");
        mapSecrets = Check("Keeper's layer", false, "The secrets, in red — leave off before showing players");
        bar.Controls.Add(Lbl("   Seed:"));
        mapSeed = new NumericUpDown { Minimum = 0, Maximum = 999999, Value = 0, Width = 74, Margin = new Padding(3, 6, 3, 3) };
        Tip.SetToolTip(mapSeed, "The map's number — the same seed and settings always draw the same map");
        bar.Controls.Add(mapSeed);
        bar.Controls.Add(Btn("🎲 New map", (s, e) => MapDraw(true), 100, "Draw a fresh map on a new seed (Ctrl+G)"));
        bar.Controls.Add(Btn("Save SVG…", (s, e) => MapSaveSvg(), 95, "Save the map as a scalable SVG file"));
        bar.Controls.Add(Btn("Save PDF…", (s, e) => MapSavePdf(), 95, "Save the map as a one-page landscape PDF"));
        bar.Controls.Add(Btn("Copy SVG", (s, e) =>
        { if (curMap != null) { Clipboard.SetText(MapGen.ToSvg(curMap)); Log("Map SVG copied to the clipboard."); } }, 90,
            "Copy the SVG markup to the clipboard"));

        mapPanel = new MapPanel { Dock = DockStyle.Fill, BackColor = Color.FromArgb(236, 229, 212) };
        mapPanel.Paint += (s, e) => { if (mapPanel.Model != null) DrawModel(e.Graphics, mapPanel.Model, mapPanel.ClientRectangle); };

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
        page.Controls.Add(bar);
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

    // ---------------------------------------------------------- GDI replay
    // The on-screen renderer for the primitive list — the same drawing the SVG and
    // PDF exports make, scaled to fit whatever room the panel has.
    static void DrawModel(Graphics g, MapModel m, Rectangle dest)
    {
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
        g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
        float s = Math.Min((dest.Width - 16f) / m.W, (dest.Height - 16f) / m.H);
        if (s <= 0) return;
        var state = g.Save();
        g.TranslateTransform(dest.X + (dest.Width - m.W * s) / 2, dest.Y + (dest.Height - m.H * s) / 2);
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
