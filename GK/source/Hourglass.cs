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
        double spent = clock.Spent;
        using (var brush = new SolidBrush(Color.FromArgb(through ? 210 : 235, sand)))
        {
            // Upper bulb: an inverted triangle emptying from the top down. Its remaining sand is a
            // triangle similar to the bulb, so the AREA left — which is what the eye reads as
            // "how much is left" — falls off as the square of the height. Scaling the height by
            // sqrt(remaining) is what makes the level drop look linear in time.
            double left = 1 - spent;
            float scale = (float)Math.Sqrt(Math.Max(0, left));
            if (scale > 0.01f)
            {
                float bandTop = neckY - (neckY - topY) * scale;
                float halfAtTop = neckHalf + (gw / 2f - neckHalf) * scale;
                g.FillPolygon(brush, new[]
                {
                    new PointF(midX - halfAtTop, bandTop), new PointF(midX + halfAtTop, bandTop),
                    new PointF(midX + neckHalf, neckY),    new PointF(midX - neckHalf, neckY),
                });
            }

            // Lower bulb: a heap growing up from the floor, same square-law in reverse.
            float heap = (float)Math.Sqrt(Math.Max(0, spent));
            if (heap > 0.01f)
            {
                float heapTop = botY - (botY - neckY) * heap;
                float halfAtHeap = neckHalf + (gw / 2f - neckHalf) * heap;
                g.FillPolygon(brush, new[]
                {
                    new PointF(midX - gw / 2f, botY),      new PointF(midX + gw / 2f, botY),
                    new PointF(midX + halfAtHeap, heapTop), new PointF(midX - halfAtHeap, heapTop),
                });
            }
        }

        // ---- the falling stream: only while it is actually running and has sand to fall ----
        if (clock.Running && spent > 0.001 && spent < 0.999)
        {
            using var grain = new SolidBrush(sand);
            float fallTop = neckY + 1, fallBot = botY - (botY - neckY) * (float)Math.Sqrt(spent) - 1;
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
