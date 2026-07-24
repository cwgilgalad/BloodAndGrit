namespace BloodAndGritKeeper;

// ============================================================ THE LEDGER, ON GLASS
// The Player's Book's character sheet ("The Ledger", back of the book), redrawn as a
// WinForms control and filled in with live data. One drawing serves the New Soul tab
// and the per-soul pop-out windows, so a character always looks like the book's sheet.
public sealed class LedgerView : Panel
{
    CharacterSheet sheet;          // the full record, when the soul came from the generator/wizard
    PartyMember member;            // the live table row, when opened from the Posse/Tracker
    public List<string> Warnings = new();

    float zoom = 1f;
    public float Zoom
    {
        get => zoom;
        set { zoom = Math.Clamp(value, 0.7f, 2.2f); PerformLayoutPass(); Invalidate(); }
    }

    // book palette (matches the HTML ledger's CSS)
    static readonly Color Paper   = Color.FromArgb(247, 242, 228);
    static readonly Color FieldBg = Color.FromArgb(252, 250, 243);
    static readonly Color Rule    = Color.FromArgb(196, 181, 148);
    static readonly Color Oxblood = Color.FromArgb(122, 31, 31);
    static readonly Color Ink     = Color.FromArgb(42, 32, 22);
    static readonly Color InkSoft = Color.FromArgb(106, 90, 68);

    public LedgerView()
    {
        DoubleBuffered = true;
        AutoScroll = true;
        BackColor = Paper;
        ResizeRedraw = true;
        Resize += (s, e) => PerformLayoutPass();
    }

    public void ShowSheet(CharacterSheet s, PartyMember m = null, List<string> warnings = null)
    {
        sheet = s; member = m;
        Warnings = warnings ?? new();
        AutoScrollPosition = new Point(0, 0);
        PerformLayoutPass();
        Invalidate();
    }

    public void Clear() { sheet = null; member = null; Warnings.Clear(); Invalidate(); }
    public bool IsEmpty => sheet == null && member == null;

    // ---- fonts, minted per zoom level (cached so paint never allocates) ----
    float cachedZoom = -1;
    Font fTitle, fSub, fLabel, fValue, fValueB, fSmall, fBig, fWarn;
    void MintFonts()
    {
        if (Math.Abs(cachedZoom - zoom) < 0.001f) return;
        cachedZoom = zoom;
        fTitle  = new Font("Georgia", 21f * zoom, FontStyle.Bold);
        fSub    = new Font("Georgia", 9.5f * zoom, FontStyle.Italic);
        fLabel  = new Font("Georgia", 7.6f * zoom, FontStyle.Bold);
        fValue  = new Font("Georgia", 10f * zoom);
        fValueB = new Font("Georgia", 10f * zoom, FontStyle.Bold);
        fSmall  = new Font("Georgia", 8.4f * zoom);
        fBig    = new Font("Georgia", 12.5f * zoom, FontStyle.Bold);
        fWarn   = new Font("Segoe UI", 8.8f * zoom, FontStyle.Bold);
    }

    int contentHeight = 400;
    void PerformLayoutPass()
    {
        // dry-run the drawing to learn the height, then size the scroll range to it
        MintFonts();
        using var bmp = new Bitmap(1, 1);
        using var g = Graphics.FromImage(bmp);
        contentHeight = Draw(g, measureOnly: true);
        AutoScrollMinSize = new Size(0, contentHeight + (int)(24 * zoom));
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        MintFonts();
        e.Graphics.TranslateTransform(AutoScrollPosition.X, AutoScrollPosition.Y);
        e.Graphics.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
        e.Graphics.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
        Draw(e.Graphics, measureOnly: false);
    }

    // ------------------------------------------------------------ the drawing
    // One routine draws and measures (measureOnly skips ink) so the scroll height
    // can never disagree with what's painted.
    int Draw(Graphics g, bool measureOnly)
    {
        if (sheet == null && member == null) return 60;

        float pad = 20 * zoom;
        float w = Math.Max(360 * zoom, ClientSize.Width - pad * 2 - SystemInformation.VerticalScrollBarWidth * 0.4f);
        float x0 = pad, y = 14 * zoom;
        float gap = 8 * zoom;

        string S(int v) => v >= 0 ? "+" + v : "−" + (-v);

        // ---- helpers ----
        void Text(string t, Font f, Color c, float x, float yy)
        { if (!measureOnly) g.DrawString(t, f, GetBrush(c), x, yy); }

        float TextW(string t, Font f) => g.MeasureString(t, f).Width;

        void TextCenter(string t, Font f, Color c, float cx, float yy)
        { if (!measureOnly) g.DrawString(t, f, GetBrush(c), cx - TextW(t, f) / 2, yy); }

        // a bordered field box with a small-caps-style label and a value
        float FieldBox(float x, float yy, float bw, string label, string value, bool valueBold = false)
        {
            float bh = 40 * zoom;
            if (!measureOnly)
            {
                g.FillRectangle(GetBrush(FieldBg), x, yy, bw, bh);
                g.DrawRectangle(GetPen(Rule), x, yy, bw, bh);
                g.DrawString(label.ToUpperInvariant(), fLabel, GetBrush(Oxblood), x + 5 * zoom, yy + 3 * zoom);
                var vf = valueBold ? fValueB : fValue;
                var vt = value ?? "";
                // shrink-to-fit rather than clip a long value
                var use = vf;
                if (TextW(vt, vf) > bw - 8 * zoom) use = fSmall;
                g.DrawString(vt, use, GetBrush(Ink), x + 5 * zoom, yy + bh - (use == fSmall ? 15 : 19) * zoom - 2 * zoom);
            }
            return bh;
        }

        // a labeled prose box; wraps its lines, grows to fit
        float ProseBox(float x, float yy, float bw, string label, List<(string t, bool bold)> lines, float minH = 0)
        {
            float innerW = bw - 12 * zoom;
            float lh = fSmall.GetHeight(g) + 1 * zoom;
            var wrapped = new List<(string t, bool bold)>();
            foreach (var (t, bold) in lines)
                foreach (var piece in WrapText(g, t, fSmall, innerW))
                    wrapped.Add((piece, bold));
            float bh = Math.Max(minH, 22 * zoom + wrapped.Count * lh + 8 * zoom);
            if (!measureOnly)
            {
                g.FillRectangle(GetBrush(FieldBg), x, yy, bw, bh);
                g.DrawRectangle(GetPen(Rule), x, yy, bw, bh);
                g.DrawString(label.ToUpperInvariant(), fLabel, GetBrush(Oxblood), x + 5 * zoom, yy + 3 * zoom);
                float ly = yy + 18 * zoom;
                foreach (var (t, bold) in wrapped)
                {
                    g.DrawString(t, bold ? fValueB : fSmall, GetBrush(Ink), x + 6 * zoom, ly);
                    ly += lh;
                }
            }
            return bh;
        }

        // ---- what fills the sheet ----
        // A soul without a full character record (hand-entered, or the seeded pregens)
        // still shows everything the table row knows; what's genuinely unknown reads
        // as an em-dash, never as a bare white box that looks like a rendering bug.
        string name = sheet?.Name ?? member?.Name ?? "";
        string calling = sheet?.Calling ?? member?.Calling ?? "";
        // gender rides on the sheet, but hand-entered souls carry it on the member too — show
        // whichever we have. (pattern var is gv, not sg — sg collides with the SignsKnown loop below.)
        string Dash(string v) => string.IsNullOrWhiteSpace(v) ? "—" : v;
        string gender = Dash(sheet?.Gender is { Length: > 0 } gv ? gv : member?.Gender);
        string origin = sheet?.Origin ?? "—";
        int level = sheet?.Level ?? member?.Level ?? 1;
        string bloodTxt = member != null ? $"{member.BloodCur} / {member.BloodMax}"
                        : sheet != null ? $"{sheet.Blood} / {sheet.Blood}" : "";
        string nerveTxt = member != null ? $"{member.NerveCur} / {member.NerveMax}"
                        : sheet != null ? $"{sheet.NerveMax} / {sheet.NerveMax}" : "";
        int defense = sheet?.Defense ?? member?.Defense ?? 0;
        int fort = sheet?.Fort ?? member?.Fort ?? 0, rf = sheet?.Ref ?? member?.Ref ?? 0, wl = sheet?.Will ?? member?.Will ?? 0;
        int grit = member?.Grit ?? sheet?.Grit ?? 3;
        int mark = member?.Mark ?? sheet?.Mark ?? 0;

        // ---- header ----
        TextCenter("The Ledger", fTitle, Oxblood, x0 + w / 2, y);
        y += fTitle.GetHeight(g) + 1 * zoom;
        TextCenter("A Reckoning of One Soul — Blood and Grit", fSub, InkSoft, x0 + w / 2, y);
        y += fSub.GetHeight(g) + 5 * zoom;
        if (!measureOnly) g.DrawLine(GetPen(Rule), x0 + w * 0.18f, y, x0 + w * 0.82f, y);
        y += 8 * zoom;

        if (Warnings.Count > 0)
        {
            foreach (var warn in Warnings)
                foreach (var piece in WrapText(g, "⚠ " + warn, fWarn, w))
                { Text(piece, fWarn, Oxblood, x0, y); y += fWarn.GetHeight(g); }
            y += 4 * zoom;
        }

        // ---- row: name / gender / calling / level / origin ----
        float nW = w * 0.28f, gW = w * 0.12f, cW = w * 0.21f, lW = w * 0.08f, oW = w - nW - gW - cW - lW - gap * 4;
        float rowH = FieldBox(x0, y, nW, "Name", name, valueBold: true);
        FieldBox(x0 + nW + gap, y, gW, "Gender", gender);
        FieldBox(x0 + nW + gW + gap * 2, y, cW, "Calling", calling);
        FieldBox(x0 + nW + gW + cW + gap * 3, y, lW, "Level", level.ToString());
        FieldBox(x0 + nW + gW + cW + lW + gap * 4, y, oW, "Origin", origin);
        y += rowH + gap;

        // ---- abilities ----
        string[] abKeys = { "STR", "DEX", "CON", "WIT", "RES", "PRE" };
        string[] abNames = { "Strength", "Dexterity", "Constitution", "Wits", "Resolve", "Presence" };
        float aW = (w - gap * 5) / 6, aH = 46 * zoom;
        for (int i = 0; i < 6; i++)
        {
            float ax = x0 + i * (aW + gap);
            if (!measureOnly)
            {
                g.FillRectangle(GetBrush(FieldBg), ax, y, aW, aH);
                g.DrawRectangle(GetPen(Rule), ax, y, aW, aH);
                var nm = abNames[i];
                var lf = fLabel;
                if (TextW(nm.ToUpperInvariant(), lf) > aW - 4 * zoom) nm = abKeys[i];
                g.DrawString(nm.ToUpperInvariant(), lf, GetBrush(Oxblood), ax + (aW - TextW(nm.ToUpperInvariant(), lf)) / 2, y + 3 * zoom);
                if (sheet != null)
                {
                    int sc = sheet.Scores[abKeys[i]];
                    string val = $"{sc} ({S(CharGen.Mod(sc))})";
                    g.DrawString(val, fValueB, GetBrush(Ink), ax + (aW - TextW(val, fValueB)) / 2, y + aH - 22 * zoom);
                }
                else if (abKeys[i] == "RES" && member != null)
                {
                    // Nerve = RES + level, so RES is recoverable from the table row
                    int res = member.NerveMax - member.Level;
                    string val = $"{res} ({S(CharGen.Mod(res))})";
                    g.DrawString(val, fValueB, GetBrush(Ink), ax + (aW - TextW(val, fValueB)) / 2, y + aH - 22 * zoom);
                }
                else
                {
                    g.DrawString("—", fValue, GetBrush(InkSoft), ax + (aW - TextW("—", fValue)) / 2, y + aH - 22 * zoom);
                }
            }
        }
        y += aH + gap;

        // ---- row: blood / defense / speed / init / attack / grit ----
        float sW = (w - gap * 5) / 6;
        string atkTxt = sheet != null
            ? $"G {S(sheet.Attack + CharGen.Mod(sheet.Scores["DEX"]))} · M {S(sheet.Attack + CharGen.Mod(sheet.Scores["STR"]))}"
            : "—";
        FieldBox(x0,                  y, sW, "Blood / Max", bloodTxt, valueBold: true);
        FieldBox(x0 + (sW + gap),     y, sW, "Defense", defense > 0 ? defense.ToString() : "—");
        FieldBox(x0 + (sW + gap) * 2, y, sW, "Speed", sheet != null ? sheet.Speed + " ft" : "—");
        FieldBox(x0 + (sW + gap) * 3, y, sW, "Init.", sheet != null ? S(CharGen.Mod(sheet.Scores["DEX"])) : "—");
        FieldBox(x0 + (sW + gap) * 4, y, sW, "Attack", atkTxt);
        FieldBox(x0 + (sW + gap) * 5, y, sW, "Grit", grit.ToString());
        y += 40 * zoom + gap;

        // ---- row: saves / nerve ----
        float vW = (w - gap * 3) / 4;
        FieldBox(x0,                  y, vW, "Fortitude Save", S(fort));
        FieldBox(x0 + (vW + gap),     y, vW, "Reflex Save", S(rf));
        FieldBox(x0 + (vW + gap) * 2, y, vW, "Will Save", S(wl));
        FieldBox(x0 + (vW + gap) * 3, y, vW, "Nerve / Max", nerveTxt, valueBold: true);
        y += 40 * zoom + gap + 2 * zoom;

        // ---- the Mark ----
        float mb = 22 * zoom;
        Text("THE MARK", fLabel, Oxblood, x0, y + mb / 2 - fLabel.GetHeight(g) / 2);
        float mx = x0 + TextW("THE MARK", fLabel) + 12 * zoom;
        for (int i = 1; i <= 6; i++)
        {
            var r = new RectangleF(mx + (i - 1) * (mb + 6 * zoom), y, mb, mb);
            if (!measureOnly)
            {
                bool lost = i == 6;
                if (i <= mark) g.FillRectangle(GetBrush(lost ? Oxblood : Color.FromArgb(160, 122, 31, 31)), r.X, r.Y, r.Width, r.Height);
                else g.FillRectangle(GetBrush(FieldBg), r.X, r.Y, r.Width, r.Height);
                using var pen = new Pen(Oxblood, (lost ? 2.2f : 1f) * zoom);
                g.DrawRectangle(pen, r.X, r.Y, r.Width, r.Height);
                string n = i.ToString();
                var col = i <= mark ? Color.White : InkSoft;
                g.DrawString(n, fSmall, GetBrush(col), r.X + (mb - TextW(n, fSmall)) / 2, r.Y + (mb - fSmall.GetHeight(g)) / 2);
            }
        }
        if (member != null && member.Taint > 0)
        {
            float tx = mx + 6 * (mb + 6 * zoom) + 16 * zoom;
            Text($"TAINT {member.Taint} / 4", fLabel, Color.FromArgb(60, 96, 84), tx, y + mb / 2 - fLabel.GetHeight(g) / 2);
        }
        y += mb + gap + 2 * zoom;

        // ---- the Four Questions (or the table notes, for a hand-entered soul) ----
        var prose = new List<(string, bool)>();
        if (sheet != null)
        {
            prose.Add(("Lost — " + (sheet.Lost ?? ""), false));
            prose.Add(("Seen — " + (sheet.Seen ?? ""), false));
            prose.Add(("Vice — " + (sheet.Vice ?? ""), false));
            prose.Add(("Moving — " + (sheet.Moving ?? ""), false));
            if (!string.IsNullOrWhiteSpace(sheet.Compass)) prose.Add(("Compass — " + sheet.Compass, false));
            if (member != null && !string.IsNullOrWhiteSpace(member.Notes)) prose.Add(("Notes — " + member.Notes, false));
        }
        else if (!string.IsNullOrWhiteSpace(member?.Notes)) prose.Add((member.Notes, false));
        else prose.Add(("What did you lose? · What keeps you moving? · What is your vice? · What have you seen?", false));
        y += ProseBox(x0, y, w, "The Four Questions", prose) + gap;

        // ---- two columns: skills | edges & gear ----
        float colGap = 12 * zoom;
        float leftW = w * 0.40f, rightW = w - leftW - colGap;
        float yL = y, yR = y;

        // skills, every one of the seventeen, ticks on the trained
        {
            float bw = leftW, xx = x0;
            var skills = CharGen.D?.skills ?? new List<CgSkill>();
            float lh = fSmall.GetHeight(g) + 5 * zoom;
            float bh = 22 * zoom + skills.Count * lh + 6 * zoom;
            if (!measureOnly)
            {
                g.FillRectangle(GetBrush(FieldBg), xx, yL, bw, bh);
                g.DrawRectangle(GetPen(Rule), xx, yL, bw, bh);
                g.DrawString("SKILLS (MARK PROFICIENCY)", fLabel, GetBrush(Oxblood), xx + 5 * zoom, yL + 3 * zoom);
                float ly = yL + 18 * zoom;
                foreach (var sk in skills)
                {
                    float tick = 10 * zoom;
                    int rank = 0;
                    sheet?.SkillRanks.TryGetValue(sk.name, out rank);
                    g.DrawRectangle(GetPen(Rule), xx + 6 * zoom, ly + 2 * zoom, tick, tick);
                    if (rank > 0)
                    {
                        g.DrawLine(GetPen(Oxblood), xx + 7 * zoom, ly + 3 * zoom, xx + 5 * zoom + tick, ly + 1 * zoom + tick);
                        g.DrawLine(GetPen(Oxblood), xx + 7 * zoom, ly + 1 * zoom + tick, xx + 5 * zoom + tick, ly + 3 * zoom);
                    }
                    string line = $"{sk.name} ({sk.ability})" + (rank >= 3 ? " — Master" : rank == 2 ? " — Expert" : "");
                    g.DrawString(line, rank > 0 ? fValueB : fSmall, GetBrush(rank > 0 ? Ink : InkSoft), xx + 6 * zoom + tick + 5 * zoom, ly);
                    // dotted rule under each line, like the book's sheet
                    using var dotted = new Pen(Rule, 1f) { DashStyle = System.Drawing.Drawing2D.DashStyle.Dot };
                    g.DrawLine(dotted, xx + 6 * zoom, ly + lh - 2 * zoom, xx + bw - 6 * zoom, ly + lh - 2 * zoom);
                    ly += lh;
                }
            }
            yL += bh;
        }

        // edges, features & path — then arms, gear & coin
        {
            float bw = rightW, xx = x0 + leftW + colGap;
            var lines = new List<(string, bool)>();
            if (sheet != null)
            {
                foreach (var f in sheet.Features) lines.Add(("• " + f, false));
                if (sheet.Subpath != null) lines.Add(("• Path: " + sheet.Subpath, false));
                if (sheet.CallingChoice != null) lines.Add(("• " + sheet.CallingChoice, false));
                if (sheet.PoolLine != null) lines.Add(("• " + sheet.PoolLine, false));
                if (sheet.Features.Count > 0 || sheet.Edges.Count > 0) lines.Add((" ", false));
                foreach (var e in sheet.Edges) lines.Add(("✦ " + e, true));
                foreach (var e in sheet.BonusCombatEdges) lines.Add(("✦ " + e + " (Gunhand's Edge)", true));
                if (sheet.SignsKnown.Count > 0)
                {
                    lines.Add((" ", false));
                    foreach (var sg in sheet.SignsKnown)
                    {
                        var d = CharGen.D.signs.FirstOrDefault(x => x.name == sg);
                        lines.Add(("† " + sg + (d != null ? $" — Rank {d.rank}, {d.cost}" : ""), false));
                    }
                }
                if (sheet.MiraclesKnown.Count > 0)
                {
                    lines.Add((" ", false));
                    foreach (var mk in sheet.MiraclesKnown)
                    {
                        var d = CharGen.D.miracles.FirstOrDefault(x => x.name == mk);
                        lines.Add(("✝ " + mk + (d != null ? $" — Rank {d.rank}, {d.cost}" : ""), false));
                    }
                }
            }
            else lines.Add(("—", false));
            yR += ProseBox(xx, yR, bw, "Edges, Calling Features & Path", lines, minH: 120 * zoom) + gap;

            var gear = new List<(string, bool)>();
            if (sheet != null)
            {
                foreach (var wpn in sheet.WeaponsCarried) gear.Add(("• " + wpn, true));
                gear.Add(("• " + (string.IsNullOrEmpty(sheet.ArmorWorn)
                    ? "Armor: none" : CharGen.ArmorLine(sheet)), true));
                foreach (var it in sheet.Gear) gear.Add(("• " + it, false));
                gear.Add((" ", false));
                gear.Add(($"Coin — rolled ${sheet.CoinRolled:0}, ${sheet.CoinLeft:0.##} left", true));
            }
            else gear.Add(("—", false));
            yR += ProseBox(xx, yR, bw, "Arms, Gear & Coin", gear, minH: 90 * zoom);
        }

        return (int)(Math.Max(yL, yR) + 10 * zoom);
    }

    // ---- wrapped text, brush/pen caches ----
    static List<string> WrapText(Graphics g, string t, Font f, float width)
    {
        var lines = new List<string>();
        if (string.IsNullOrEmpty(t)) { lines.Add(""); return lines; }
        string cur = "";
        foreach (var wd in t.Split(' '))
        {
            string trial = cur.Length == 0 ? wd : cur + " " + wd;
            if (g.MeasureString(trial, f).Width <= width || cur.Length == 0) cur = trial;
            else { lines.Add(cur); cur = wd; }
        }
        lines.Add(cur);
        return lines;
    }

    static readonly Dictionary<Color, SolidBrush> brushes = new();
    static SolidBrush GetBrush(Color c)
    { if (!brushes.TryGetValue(c, out var b)) brushes[c] = b = new SolidBrush(c); return b; }

    static readonly Dictionary<Color, Pen> pens = new();
    static Pen GetPen(Color c)
    { if (!pens.TryGetValue(c, out var p)) pens[c] = p = new Pen(c, 1f); return p; }
}

// ============================================================ SOUL POP-OUT WINDOWS
// The Bestiary's creature-card pattern, for people: one modeless window per soul,
// reused if already open, cascading placement, its own zoom and → Tracker button.
public partial class MainForm
{
    readonly Dictionary<PartyMember, Form> soulWindows = new();

    internal void ShowSoulCard(PartyMember p)
    {
        if (p == null) return;
        if (soulWindows.TryGetValue(p, out var open) && !open.IsDisposed)
        { open.BringToFront(); open.Activate(); return; }

        int cascade = (soulWindows.Count % 5) * 26;
        var win = new Form
        {
            Text = p.Name, Width = 560, Height = 660, BackColor = Paper,
            MinimumSize = new Size(340, 300), StartPosition = FormStartPosition.Manual,
            Location = new Point(Math.Max(0, Right - 580 - cascade), Top + 80 + cascade)
        };
        if (AppIcon != null) win.Icon = AppIcon;

        var ledger = new LedgerView { Dock = DockStyle.Fill };
        var bar = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 42, Padding = new Padding(4, 2, 4, 2), BackColor = Color.FromArgb(243, 237, 221) };
        bar.Controls.Add(Btn("A−", (s, e) => ledger.Zoom -= 0.15f, 46, "Smaller text"));
        bar.Controls.Add(Btn("A＋", (s, e) => ledger.Zoom += 0.15f, 46, "Larger text"));
        bar.Controls.Add(Btn("→ Tracker", (s, e) =>
        {
            if (!tracker.Any(t => t.IsPC && t.Name == p.Name))
            {
                tracker.Add(new Combatant { Name = p.Name, IsPC = true, BloodCur = p.BloodCur, BloodMax = p.BloodMax, Defense = p.Defense });
                Log($"{p.Name} takes the field.");
            }
            else Log($"{p.Name} is already on the field.");
        }, 95, "Put this soul onto the combat tracker"));
        if (p.Sheet != null)
        {
            bar.Controls.Add(Btn("✦ Level up", (s, e) => LevelUpMember(p, win), 90, "Advance this soul one level"));
            bar.Controls.Add(Btn("✎ Tweak", (s, e) =>
            {
                if (TweakSheet(p.Sheet, win))
                {
                    SyncMemberFromSheet(p);
                    win.Text = p.Name;
                    ledger.ShowSheet(p.Sheet, p, SheetWarnings(p.Sheet));
                    posseGrid?.Refresh();
                    Log($"{p.Name}'s sheet hand-tweaked.");
                }
            }, 85, "Hand-adjust this soul's sheet"));
        }

        win.Controls.Add(ledger);
        win.Controls.Add(bar);
        ledger.ShowSheet(p.Sheet, p, p.Sheet != null ? SheetWarnings(p.Sheet) : null);

        soulWindows[p] = win;
        win.FormClosed += (s, e) => soulWindows.Remove(p);
        win.Show(this);
    }

    // the live table row follows the sheet after a tweak (Blood/Nerve refill to the new max)
    internal void SyncMemberFromSheet(PartyMember p)
    {
        var s = p.Sheet; if (s == null) return;
        p.Name = s.Name; p.Calling = s.Calling; p.Gender = s.Gender; p.Level = s.Level;
        p.RES = s.Scores.TryGetValue("RES", out var res) ? res : p.RES;
        p.BloodMax = s.Blood; p.BloodCur = Math.Min(p.BloodCur, s.Blood);
        p.Defense = s.Defense; p.Fort = s.Fort; p.Ref = s.Ref; p.Will = s.Will;
        if (p.NerveMax != s.NerveMax) { p.NerveMax = s.NerveMax; p.NerveCur = Math.Min(p.NerveCur, s.NerveMax); }
        p.Grit = s.Grit; p.Mark = s.Mark;
        MirrorToTracker(p);
    }

    // validation, phrased for the ledger: hand-tweaked sheets show a notice, not a failure
    internal static List<string> SheetWarnings(CharacterSheet s)
    {
        var v = CharGen.Validate(s);
        if (v.Count == 0) return new();
        if (s.HandTweaked)
            return new() { $"Hand-tweaked — the book no longer vouches for {v.Count} figure(s) on this sheet." };
        var outp = new List<string> { "RULES CHECK FAILED:" };
        outp.AddRange(v);
        return outp;
    }
}
