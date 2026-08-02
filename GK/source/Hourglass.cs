namespace BloodAndGritKeeper;

/// <summary>The turn hourglass, drawn rather than iconned so it can actually animate: sand drains
/// from the upper bulb into the lower one across the length of a posse's turn, with a falling
/// stream and a heap that grows where it lands.
///
/// <para>All state lives on the <see cref="TurnClock"/> it is pointed at — this control owns no
/// countdown of its own and starts no timer. The Tracker feeds the clock and calls
/// <see cref="Control.Invalidate()"/>; that keeps the rule (how long is a turn, how much is left) in the
/// rules library where the smoke rig can reach it, and keeps this file to ink.</para>
///
/// <para>Written double-buffered and antialiased because the glass is all diagonals. It draws no
/// text at all, deliberately — the m:ss face is a Label beside it, so the drawn-text landmines
/// recorded in CLAUDE.md (grid-fit eating word spaces, Georgia's descending figures, DrawString
/// with no width) simply do not apply here.</para></summary>
internal sealed class HourglassView : Control
{
    readonly TurnClock clock;

    /// Grains in the falling stream, as (x-jitter, phase). Fixed rather than random per frame: a
    /// stream re-scattered every tick reads as static, not as falling sand.
    static readonly (int dx, double phase)[] Grains =
    {
        (0, 0.00), (-2, 0.17), (1, 0.34), (-1, 0.51), (2, 0.68), (0, 0.85),
    };

    double drift;                 // advances every tick so the stream moves

    public HourglassView(TurnClock c)
    {
        clock = c;
        SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer
                 | ControlStyles.UserPaint | ControlStyles.ResizeRedraw, true);
        BackColor = MainForm.Paper;
        Size = new Size(30, 40);
        Cursor = Cursors.Hand;
    }

    /// <summary>Move the falling sand on one frame. Separate from the clock's own Tick so a PAUSED
    /// glass stops moving — sand that keeps pouring while the turn is held is a lie about the
    /// state, and the one thing a status display must never be.</summary>
    public void Advance()
    {
        if (clock.Running) drift = (drift + 0.055) % 1.0;
        Invalidate();
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        var g = e.Graphics;
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
        g.Clear(BackColor);

        // Geometry: two triangles nose to nose inside a 2px margin, with caps top and bottom.
        // Everything below is expressed as a fraction of the box so the glass scales with the
        // control instead of being laid out to constants (the dialog lesson, applied to ink).
        float w = Width - 4f, h = Height - 4f;
        if (w < 8 || h < 12) return;
        float x = 2f, y = 2f;
        float cap = Math.Max(2f, h * 0.07f);          // the wooden caps
        float neckY = y + cap + (h - cap * 2) / 2f;   // the waist
        float inset = w * 0.13f;                      // the glass is narrower than the caps
        float gx = x + inset, gw = w - inset * 2;
        float topY = y + cap, botY = y + h - cap;
        float neckHalf = Math.Max(1.2f, gw * 0.07f);
        float midX = x + w / 2f;

        bool through = clock.Expired;
        var frame = through ? MainForm.Blood : MainForm.Ink;
        var sand = through ? MainForm.Blood : MainForm.Gold;

        // ---- the sand, drawn behind the glass outline so the outline reads as glass ----
        //
        // Both bulbs are laid out from ONE number: how far out from the neck the sand still to
        // fall reaches, as a fraction of a bulb's height. Each bulb is a triangle on the neck, so
        // AREA — which is what the eye actually reads as "how much is left" — goes as the square
        // of that distance; taking the square root of the sand remaining is what makes the level
        // drop look linear in time.
        double spent = clock.Spent;
        float scale = (float)Math.Sqrt(Math.Clamp(1 - spent, 0, 1));
        // The half-width of the glass wall at that distance from the neck — the SAME number in
        // both bulbs, which is the whole trick. The surface of the upper band and the surface of
        // the lower heap are two cuts across the glass at equal distances from the waist, so they
        // are equally wide, and the two areas sum to a constant: sand is conserved, and the eye
        // reads one quantity moving rather than two shapes animating past each other.
        float halfAtSurface = neckHalf + (gw / 2f - neckHalf) * scale;
        float bandTop = neckY - (neckY - topY) * scale;
        float heapTop = neckY + (botY - neckY) * scale;
        using (var brush = new SolidBrush(Color.FromArgb(through ? 210 : 235, sand)))
        {
            // Upper bulb: an inverted triangle emptying from the top down.
            if (scale > 0.01f)
                g.FillPolygon(brush, new[]
                {
                    new PointF(midX - halfAtSurface, bandTop), new PointF(midX + halfAtSurface, bandTop),
                    new PointF(midX + neckHalf, neckY),        new PointF(midX - neckHalf, neckY),
                });

            // Lower bulb: the heap it lands in, growing up off the floor.
            //
            // This is the half that was wrong. It took its top edge's width from its own height
            // above the floor — the wall measured from the wrong end — so the wider the heap grew
            // the narrower it drew its surface. At a glass nearly through, that put the heap's
            // corners at the widest part of the bulb while its surface sat up at the narrow neck:
            // the sand painted a rectangle across the whole lower half, and the drawn glass came
            // out INSIDE the box instead of around the sand.
            if (scale < 0.99f)
                g.FillPolygon(brush, new[]
                {
                    new PointF(midX - gw / 2f, botY),          new PointF(midX + gw / 2f, botY),
                    new PointF(midX + halfAtSurface, heapTop), new PointF(midX - halfAtSurface, heapTop),
                });
        }

        // ---- the falling stream: only while it is actually running and has sand to fall ----
        if (clock.Running && spent > 0.001 && spent < 0.999)
        {
            using var grain = new SolidBrush(sand);
            // From just under the neck to just above the heap's surface — off the same heapTop the
            // heap is drawn to, so the stream always lands ON the sand rather than in it or short of it.
            float fallTop = neckY + 1, fallBot = heapTop - 1;
            if (fallBot > fallTop)
                foreach (var (dx, phase) in Grains)
                {
                    float t = (float)((phase + drift) % 1.0);
                    float gy = fallTop + (fallBot - fallTop) * t;
                    g.FillEllipse(grain, midX + dx * 0.7f - 0.9f, gy, 1.8f, 2.4f);
                }
        }

        // ---- the glass, then the caps over its ends ----
        using (var pen = new Pen(frame, 1.4f))
        {
            g.DrawLines(pen, new[]
            {
                new PointF(midX - gw / 2f, topY), new PointF(midX - neckHalf, neckY),
                new PointF(midX - gw / 2f, botY),
            });
            g.DrawLines(pen, new[]
            {
                new PointF(midX + gw / 2f, topY), new PointF(midX + neckHalf, neckY),
                new PointF(midX + gw / 2f, botY),
            });
        }
        using (var capBrush = new SolidBrush(frame))
        {
            g.FillRectangle(capBrush, x, y, w, cap);
            g.FillRectangle(capBrush, x, y + h - cap, w, cap);
        }
    }
}
