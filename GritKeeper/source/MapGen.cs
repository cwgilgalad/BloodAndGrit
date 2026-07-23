using System.Text;

namespace BloodAndGritKeeper;

// ============================================================ TRAIL MAPS
// A seeded random map generator in the book's hand: pick the ground, the scale,
// and the hour, and it draws a one-page frontier survey — water, trails, a
// settlement, named landmarks, and (on the Keeper's layer) the secrets in red.
//
// Everything is generated as a flat list of drawing primitives (Prim), which
// three dumb renderers replay identically: the on-screen GDI painter (TabsMap),
// the SVG writer (here), and the PDF page (Pdf.MapPdf). No WinForms types in
// this file — the smoke rig compiles it headless.

public enum PrimKind { Poly, Line, Circle, Text }

public sealed class Prim
{
    public PrimKind Kind;
    public float[] Pts;              // Poly/Line: x0,y0,x1,y1,… · Circle: cx,cy,r · Text: x,y (baseline)
    public string Fill, Stroke;      // "#rrggbb" or null
    public float StrokeW = 1f;
    public float[] Dash;             // null = solid
    public float Alpha = 1f;
    public string Text;
    public float FontSize;
    public bool Bold, Italic;
    public int Anchor;               // 0 start · 1 middle · 2 end
}

public sealed class MapSpec
{
    public string Terrain = "The Trail & the Open Range";
    public int Scale;                // 0 gunfight · 1 homestead · 2 county · 3 territory
    public int Time = 1;             // 0 first light · 1 high noon · 2 dusk · 3 dead of night
    public int Water;                // index into MapGen.Waters
    public bool Trail = true, Rail, Town = true, Grid, Secrets;
    public int Landmarks = 5;
    public int Seed;
}

// A named landmark the Keeper can pick up and move: its anchor (the symbol's
// center) plus the contiguous run of prims that draw it, so a move translates
// exactly its own ink and nothing else's. GenX/GenY remember where the survey
// originally drew it, for "put it back".
public sealed class Landmark
{
    public string Name = "";
    public float X, Y;
    public float GenX, GenY;
    public int PrimStart, PrimCount;
}

public sealed class MapModel
{
    public int W = 1000, H = 700;
    public string Title = "", Sub = "";
    public List<Prim> P = new();
    public List<Landmark> Landmarks = new();
    public List<Landmark> Secrets = new();     // the Keeper's-layer marks, movable the same way
}

public static class MapGen
{
    public static readonly string[] Terrains =
    {
        "The Trail & the Open Range", "Rivers, Lakes & Swamps", "Towns, Homesteads & Haunted Houses",
        "Graveyards & Battlefields", "Mines & Under the Earth", "Winter & the High Country",
        "Desert & the Badlands", "The Old Places", "The Lamplit City"
    };
    // The city ward is appended rather than slotted in by size, so every stored or
    // remembered Scale index keeps meaning what it meant before Ch. XIV existed.
    public static readonly string[] Scales =
        { "A gunfight (yards)", "A homestead (half a mile)", "A county (a day's ride)", "A territory (the long trail)",
          "A city ward (blocks)" };
    public static readonly string[] Times = { "First light", "High noon", "Dusk", "Dead of night" };
    public static readonly string[] Waters = { "As the land wills", "No water", "A creek", "A river", "A lake", "River & lake" };

    // ---- palette (the books' frontier colors, map-toned) ----
    const string Ink = "#4a3826", Dark = "#3a2c1e", Blood = "#8f1d1d", Gold = "#967432";
    const string WaterEdge = "#7d98a1", WaterFill = "#b9cbcf", TrailBrown = "#7a5c38";
    const string Green = "#6f7d54", PineGreen = "#5d6f52", Tan = "#d8c49a", Bone = "#b5a98c";

    // ---------------------------------------------------------- generation
    public static MapModel Generate(MapSpec sp)
    {
        // One independent random stream per feature, all derived from the seed.
        // Toggling an overlay (trail, rail, settlement, grid, Keeper's layer) must
        // never reshuffle the rest of the map — with the old single shared stream,
        // drawing the rail consumed numbers the land would otherwise have used, so
        // checking a box quietly regenerated a different countryside (user-reported).
        Random R(int salt) => new(unchecked(sp.Seed * 92821 + salt));
        Random rngWater = R(1), rngTrail = R(2), rngRail = R(3), rngTown = R(4),
               rngLand = R(5), rngLm = R(6), rngHour = R(7), rngSecrets = R(8), rngName = R(9);

        var m = new MapModel();
        var P = m.P;
        float W = m.W, H = m.H;
        int ti = Math.Max(0, Array.IndexOf(Terrains, sp.Terrain));
        float k = sp.Scale switch { 0 => 1.5f, 1 => 1.15f, 2 => 0.95f, 4 => 1.25f, _ => 0.8f };
        // A city map is asked for either by ground or by scale; either way it draws
        // streets and blocks instead of open country (Keeper's Book, Ch. XIV).
        bool city = ti == 8 || sp.Scale == 4;

        string bg = ti switch
        {
            0 => "#eee7cf", 1 => "#e6e9d3", 2 => "#efe8d2", 3 => "#e9e2cf",
            4 => "#ece2cc", 5 => "#eef0ee", 6 => "#f2e5c6", 8 => "#e7e4dc", _ => "#e8e0cf"
        };
        P.Add(Rect(0, 0, W, H, bg, null, 0));

        // keep-out circles: features, labels, and furniture never overprint each other
        var blocked = new List<(float x, float y, float r)>
        {
            (170, 70, 190),                     // cartouche
            (W - 64, 92, 95),                   // compass
            (150, H - 40, 170),                 // scale bar
        };
        bool Free(float x, float y, float r) =>
            x > 24 + r && x < W - 24 - r && y > 24 + r && y < H - 24 - r &&
            blocked.All(b => Sq(b.x - x) + Sq(b.y - y) > Sq(b.r + r));
        (float x, float y) Place(Random rig, float r, int tries = 40)
        {
            for (int t = 0; t < tries; t++)
            {
                float x = 30 + (float)rig.NextDouble() * (W - 60), y = 30 + (float)rig.NextDouble() * (H - 60);
                if (Free(x, y, r)) { blocked.Add((x, y, r)); return (x, y); }
            }
            return (float.NaN, 0);
        }

        // ---- water ----
        int water = sp.Water == 0
            ? ti switch { 1 => 5, 5 => 4, 6 => 1, 3 => rngWater.Next(2) == 0 ? 2 : 1, _ => rngWater.Next(3) == 0 ? 2 : 1 }
            : sp.Water;
        float[] riverPts = null;
        (float x, float y, float r) lake = default;
        bool frozen = ti == 5;

        var clipR = (x0: ClipInset, y0: ClipInset, x1: W - ClipInset, y1: H - ClipInset);
        if (water is 3 or 5)                                     // a river, edge to edge
        {
            bool vert = rngWater.Next(2) == 0;
            var raw = vert
                ? Meander(rngWater, Lerp(rngWater, 0.25f, 0.75f) * W, -12, Lerp(rngWater, 0.25f, 0.75f) * W, H + 12, 7, 90)
                : Meander(rngWater, -12, Lerp(rngWater, 0.25f, 0.75f) * H, W + 12, Lerp(rngWater, 0.25f, 0.75f) * H, 7, 90);
            var runs = ClipPolyline(raw, clipR.x0, clipR.y0, clipR.x1, clipR.y1);
            foreach (var run in runs)                            // edge under, water over — layer order kept
                P.Add(new Prim { Kind = PrimKind.Line, Pts = run, Stroke = WaterEdge, StrokeW = 13 });
            foreach (var run in runs)
                P.Add(new Prim { Kind = PrimKind.Line, Pts = run, Stroke = frozen ? "#dfe8ea" : WaterFill, StrokeW = 9 });
            riverPts = Longest(runs);
            if (riverPts != null) BlockAlong(blocked, riverPts, 26);
        }
        else if (water == 2)                                     // a creek
        {
            bool vert = rngWater.Next(2) == 0;
            var raw = vert
                ? Meander(rngWater, Lerp(rngWater, 0.2f, 0.8f) * W, -12, Lerp(rngWater, 0.2f, 0.8f) * W, H + 12, 8, 110)
                : Meander(rngWater, -12, Lerp(rngWater, 0.2f, 0.8f) * H, W + 12, Lerp(rngWater, 0.2f, 0.8f) * H, 8, 110);
            foreach (var run in ClipPolyline(raw, clipR.x0, clipR.y0, clipR.x1, clipR.y1))
            {
                P.Add(new Prim { Kind = PrimKind.Line, Pts = run, Stroke = WaterEdge, StrokeW = 4.5f });
                if (riverPts == null || run.Length > riverPts.Length) riverPts = run;
            }
            if (riverPts != null) BlockAlong(blocked, riverPts, 16);
        }
        if (water is 4 or 5)                                     // a lake
        {
            var (lx, ly) = Place(rngWater, 120);
            if (float.IsNaN(lx)) { lx = W * 0.68f; ly = H * 0.6f; }
            float lr = 80 + (float)rngWater.NextDouble() * 55;
            var shore = Blob(rngWater, lx, ly, lr);
            P.Add(new Prim { Kind = PrimKind.Poly, Pts = shore, Fill = frozen ? "#e3ebed" : WaterFill, Stroke = WaterEdge, StrokeW = 2.2f });
            lake = (lx, ly, lr);
            blocked.Add((lx, ly, lr + 18));
        }
        if (ti == 1)                                             // swamp country: reeds crowd the water
            for (int i = 0; i < 14; i++)
            {
                float ang = (float)(rngWater.NextDouble() * Math.PI * 2);
                float x, y;
                if (lake.r > 0 && rngWater.Next(2) == 0)
                { x = lake.x + (float)Math.Cos(ang) * (lake.r + 16); y = lake.y + (float)Math.Sin(ang) * (lake.r * 0.8f + 14); }
                else if (riverPts != null)
                { int j = rngWater.Next(riverPts.Length / 2) * 2; x = riverPts[j] + rngWater.Next(-30, 31); y = riverPts[j + 1] + rngWater.Next(-24, 25); }
                else break;
                if (x > 30 && x < W - 30 && y > 30 && y < H - 30) Sym(P, rngWater, "reeds", x, y, k);
            }

        // ---- grid (a battle map's squares; optional elsewhere) ----
        if (sp.Grid)
        {
            float step = sp.Scale == 0 ? 40 : 50;
            for (float x = step; x < W - 8; x += step)
                P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { x, 10, x, H - 10 }, Stroke = "#6b5947", StrokeW = 0.7f, Alpha = 0.22f });
            for (float y = step; y < H - 8; y += step)
                P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { 10, y, W - 10, y }, Stroke = "#6b5947", StrokeW = 0.7f, Alpha = 0.22f });
        }

        // ---- the trail, and where it leads ----
        float tx = W * 0.5f + rngTown.Next(-120, 121), ty = H * 0.5f + rngTown.Next(-80, 81);
        if (sp.Trail)
        {
            bool vert = rngTrail.Next(2) == 0;
            float a0 = Lerp(rngTrail, 0.2f, 0.8f), a1 = Lerp(rngTrail, 0.2f, 0.8f);
            var leg1 = vert ? Meander(rngTrail, a0 * W, -12, tx, ty, 5, 60) : Meander(rngTrail, -12, a0 * H, tx, ty, 5, 60);
            var leg2 = vert ? Meander(rngTrail, tx, ty, a1 * W, H + 12, 5, 60) : Meander(rngTrail, tx, ty, W + 12, a1 * H, 5, 60);
            foreach (var leg in new[] { leg1, leg2 })
                foreach (var run in ClipPolyline(leg, clipR.x0, clipR.y0, clipR.x1, clipR.y1))
                    P.Add(new Prim { Kind = PrimKind.Line, Pts = run, Stroke = TrailBrown, StrokeW = 2.6f, Dash = new[] { 8f, 5f } });
            if (sp.Scale >= 2 && rngTrail.Next(2) == 0)          // a fork, at riding scales
            {
                int j = rngTrail.Next(leg2.Length / 4) * 2;
                var fork = Meander(rngTrail, leg2[j], leg2[j + 1], rngTrail.Next(2) == 0 ? -12 : W + 12, Lerp(rngTrail, 0.15f, 0.85f) * H, 4, 70);
                foreach (var run in ClipPolyline(fork, clipR.x0, clipR.y0, clipR.x1, clipR.y1))
                    P.Add(new Prim { Kind = PrimKind.Line, Pts = run, Stroke = TrailBrown, StrokeW = 2f, Dash = new[] { 7f, 5f } });
            }
        }

        // ---- the rail line (straight as money) ----
        if (sp.Rail)
        {
            var rawRail = Meander(rngRail, -12, Lerp(rngRail, 0.25f, 0.75f) * H, W + 12, Lerp(rngRail, 0.25f, 0.75f) * H, 3, 30);
            foreach (var rail in ClipPolyline(rawRail, clipR.x0, clipR.y0, clipR.x1, clipR.y1))
            {
                P.Add(new Prim { Kind = PrimKind.Line, Pts = rail, Stroke = "#4a4038", StrokeW = 2.2f });
                for (int i = 0; i + 3 < rail.Length; i += 2)     // cross-ties
                {
                    float dx = rail[i + 2] - rail[i], dy = rail[i + 3] - rail[i + 1];
                    float len = (float)Math.Sqrt(dx * dx + dy * dy);
                    if (len < 1) continue;
                    for (float d = 10; d < len; d += 16)
                    {
                        float px = rail[i] + dx * d / len, py = rail[i + 1] + dy * d / len;
                        float nx = -dy / len * 5, ny = dx / len * 5;
                        if (px < 20 || px > W - 20) continue;
                        P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { px - nx, py - ny, px + nx, py + ny }, Stroke = "#4a4038", StrokeW = 1.2f });
                    }
                }
            }
        }

        // ---- the settlement ----
        // The town's name and ground are claimed whether or not it's shown, so toggling
        // Settlement adds/removes only the town's own ink — the land never reshuffles.
        string townName = TownName(rngTown, ti);
        blocked.Add((tx, ty, sp.Scale == 0 ? 150 : 95));
        if (sp.Town && city)
        {
            // A ward: avenues and cross streets, the blocks between them, and the
            // three things every city in Ch. XIV has — a depot, works that smoke,
            // and a quarter the city would rather not look at.
            const float m0 = 40;
            float gw = W - m0 * 2, gh = H - m0 * 2;
            int cols = 5 + rngTown.Next(2), rows = 3 + rngTown.Next(2);
            float colW = gw / cols, rowH = gh / rows;
            for (int c = 0; c <= cols; c++)
                P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { m0 + c * colW, m0, m0 + c * colW, m0 + gh },
                                 Stroke = "#b09a72", StrokeW = c % 3 == 1 ? 9 : 5, Alpha = 0.6f });
            for (int r2 = 0; r2 <= rows; r2++)
                P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { m0, m0 + r2 * rowH, m0 + gw, m0 + r2 * rowH },
                                 Stroke = "#b09a72", StrokeW = r2 % 2 == 1 ? 9 : 5, Alpha = 0.6f });
            for (int c = 0; c < cols; c++)
                for (int r2 = 0; r2 < rows; r2++)
                {
                    if (rngTown.Next(9) == 0) continue;           // a lot the fire took
                    float bx = m0 + c * colW + 7, by = m0 + r2 * rowH + 7;
                    float bw = colW - 14, bh = rowH - 14;
                    P.Add(Rect(bx, by, bw, bh, "#d9cba8", Dark, 1.2f));
                    // a couple of blocks are dense tenement rows rather than one mass
                    if (rngTown.Next(3) == 0)
                        for (int t = 1; t < 4; t++)
                            P.Add(new Prim { Kind = PrimKind.Line,
                                Pts = new[] { bx + bw * t / 4f, by, bx + bw * t / 4f, by + bh },
                                Stroke = Dark, StrokeW = 0.8f, Alpha = 0.7f });
                }
            blocked.Clear();
            blocked.Add((170, 70, 190)); blocked.Add((W - 64, 92, 95)); blocked.Add((150, H - 40, 170));
        }
        else if (sp.Town)
        {
            if (sp.Scale == 0)                                   // a main street, building by building
            {
                P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { tx - 150, ty, tx + 150, ty }, Stroke = "#b09a72", StrokeW = 16, Alpha = 0.65f });
                int n = 7 + rngTown.Next(4);
                for (int i = 0; i < n; i++)
                {
                    float bx = tx - 130 + i * (270f / n) + rngTown.Next(-6, 7);
                    float by = ty + (i % 2 == 0 ? -34 : 16) + rngTown.Next(-4, 5);
                    P.Add(Rect(bx, by, 34 + rngTown.Next(12), 20 + rngTown.Next(6), "#d9cba8", Dark, 1.4f));
                }
                if (rngTown.Next(2) == 0) Sym(P, rngTown, "church", tx + 170, ty - 30, 1.4f);
            }
            else
            {
                int n = 5 + rngTown.Next(4);
                for (int i = 0; i < n; i++)
                {
                    double ang = rngTown.NextDouble() * Math.PI * 2;
                    float bx = tx + (float)(Math.Cos(ang) * (12 + rngTown.Next(30))), by = ty + (float)(Math.Sin(ang) * (8 + rngTown.Next(22)));
                    P.Add(Rect(bx, by, 11, 8, "#d9cba8", Dark, 1f));
                }
                if (rngTown.Next(2) == 0) Sym(P, rngTown, "church", tx + 40, ty - 22, k);
            }
            P.Add(TextP(tx, ty + (sp.Scale == 0 ? 66 : 48), townName, 14, Ink, bold: true, anchor: 1));
        }

        // ---- the land itself ----
        string[] kit = ti switch
        {
            0 => new[] { "grass", "grass", "grass", "scrub", "scrub", "tree", "hill", "hill", "bones", "rock" },
            1 => new[] { "reeds", "reeds", "deadtree", "deadtree", "tree", "tuft", "tuft", "rock", "grass" },
            2 => new[] { "grass", "grass", "tree", "tree", "fence", "fence", "field", "hill", "scrub" },
            3 => new[] { "grave", "grave", "grave", "deadtree", "grass", "grass", "trench", "rock", "scrub" },
            4 => new[] { "mesa", "mesa", "rock", "rock", "rock", "mine", "tailing", "scrub", "deadtree" },
            5 => new[] { "pine", "pine", "pine", "pine", "snowpeak", "snowpeak", "snowpeak", "rock", "deadtree" },
            6 => new[] { "cactus", "cactus", "cactus", "mesa", "mesa", "dune", "dune", "bones", "bones", "scrub", "rock" },
            _ => new[] { "stone", "stone", "stone", "ruin", "ruin", "deadtree", "deadtree", "mound", "tree", "grass" },
        };
        if (city) kit = new[] { "stack", "stack", "depot", "pens", "church", "wharf", "stack", "pens" };
        int count = city ? 9 : (sp.Scale == 0 ? 16 : 30);
        for (int i = 0; i < count; i++)
        {
            var (x, y) = Place(rngLand, 15 * k + 12);
            if (float.IsNaN(x)) continue;
            Sym(P, rngLand, kit[rngLand.Next(kit.Length)], x, y, k);
        }

        // ---- named landmarks ----
        var nouns = new List<(string sym, string noun)>
        {
            ("deadtree", "Hanging Tree"), ("rock", "Lookout"), ("well", "Well"), ("ruin", "Burned Homestead"),
            ("grave", "Boot Hill"), ("mine", "Diggings"), ("windmill", "Windmill"), ("corral", "Corral"),
            ("stone", "Standing Stones"), ("church", "Mission"), ("camp", "Cold Camp"), ("soddy", "Soddy"),
        };
        if (riverPts != null || lake.r > 0) nouns.Add(("ford", "Ford"));
        if (city)
            nouns = new List<(string sym, string noun)>
            {
                ("depot", "Union Depot"), ("pens", "Stockyards"), ("stack", "Packing House"),
                ("stack", "Smelter"), ("church", "Cathedral"), ("grave", "Potter's Field"),
                ("ruin", "Burned Block"), ("well", "Waterworks"), ("mine", "Shaft House"),
                ("wharf", "The Levee"), ("lodge", "The Lodge Hall"), ("lodge", "Benevolent Association"),
                ("camp", "The Shanties"), ("soddy", "Charity Ward"),
            };
        for (int i = 0; i < sp.Landmarks && nouns.Count > 0; i++)
        {
            var pick = nouns[rngLm.Next(nouns.Count)];
            nouns.Remove(pick);
            // City landmarks arrive already named ("The Levee", "Union Depot"), so the
            // country decorator is skipped for them — it produced "The Drowned The Levee".
            // They take a ward name or a company name instead, the way a city labels things.
            string name;
            if (city)
                name = pick.noun.StartsWith("The ")
                    ? pick.noun
                    : rngLm.Next(2) == 0 ? "The " + pick.noun
                                         : Choice(rngLm, LmOwner) + " " + pick.noun;
            else
                name = rngLm.Next(3) == 0
                    ? Choice(rngLm, LmOwner) + "'s " + pick.noun
                    : "The " + (rngLm.Next(2) == 0 ? Choice(rngLm, LmAdj) + " " : "") + pick.noun;
            float x, y;
            if (pick.sym == "ford" && riverPts != null)
            {
                // a ford lives ON the water: pick a spot along the middle stretch of
                // the river so the crossing never sits at the map's lip
                int half = riverPts.Length / 2;
                int j = (half / 5 + rngLm.Next(Math.Max(1, half * 3 / 5))) * 2;
                x = riverPts[j]; y = riverPts[j + 1];
                blocked.Add((x, y, 34));
            }
            else if (pick.sym == "ford" && lake.r > 0)
            {
                double ang = rngLm.NextDouble() * Math.PI * 2;   // on the lake shore
                x = Math.Clamp(lake.x + (float)Math.Cos(ang) * lake.r, 40, W - 40);
                y = Math.Clamp(lake.y + (float)Math.Sin(ang) * lake.r * 0.8f, 40, H - 52);
                blocked.Add((x, y, 34));
            }
            else
            {
                (x, y) = Place(rngLm, 34);
                if (float.IsNaN(x)) continue;
            }
            int primStart = P.Count;
            Sym(P, rngLm, pick.sym, x, y, k);
            // centered label: nudge it inward near the edges so a long name never
            // runs off the paper (half-width ≈ 2.7px/char at this size and face)
            float est = name.Length * 2.7f;
            float lx = Math.Clamp(x, ClipInset + 4 + est, W - ClipInset - 4 - est);
            P.Add(TextP(lx, y + 15 * k + 12, name, 10.5f, Ink, italic: true, anchor: 1));
            blocked.Add((x, y + 15 * k + 12, 40));
            m.Landmarks.Add(new Landmark
            {
                Name = name, X = x, Y = y, GenX = x, GenY = y,
                PrimStart = primStart, PrimCount = P.Count - primStart
            });
        }

        // ---- the hour ----
        (string col, float a) overlay = sp.Time switch
        {
            0 => ("#e8b46b", 0.10f), 2 => ("#b0672f", 0.16f), 3 => ("#1b2540", 0.30f), _ => (null, 0f)
        };
        if (overlay.col != null)
            P.Add(Rect(0, 0, W, H, overlay.col, null, 0, overlay.a));
        if (sp.Time == 3)
        {
            for (int i = 0; i < 26; i++)
                P.Add(new Prim { Kind = PrimKind.Circle, Pts = new[] { (float)rngHour.NextDouble() * W, (float)rngHour.NextDouble() * H, 1f + (float)rngHour.NextDouble() }, Fill = "#f5f2e4", Alpha = 0.55f });
            // the moon: a pale disc with the night sky biting the crescent out of it
            string bite = Mix(bg, overlay.col, overlay.a);
            P.Add(new Prim { Kind = PrimKind.Circle, Pts = new[] { W - 170, 130, 17 }, Fill = "#efe8d0", Alpha = 0.9f });
            P.Add(new Prim { Kind = PrimKind.Circle, Pts = new[] { W - 178, 124, 15 }, Fill = bite });
        }

        // ---- the Keeper's layer, in red ----
        if (sp.Secrets)
        {
            int n = 2 + rngSecrets.Next(3);
            for (int i = 0; i < n && SecretLines.Length > 0; i++)
            {
                var (x, y) = Place(rngSecrets, 40);
                if (float.IsNaN(x)) continue;
                string line = Choice(rngSecrets, SecretLines);
                int primStart = P.Count;
                P.Add(new Prim { Kind = PrimKind.Circle, Pts = new[] { x, y, 15 }, Stroke = Blood, StrokeW = 1.8f, Dash = new[] { 4f, 3f }, Alpha = 0.85f });
                P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { x - 6, y - 6, x + 6, y + 6 }, Stroke = Blood, StrokeW = 1.8f, Alpha = 0.85f });
                P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { x - 6, y + 6, x + 6, y - 6 }, Stroke = Blood, StrokeW = 1.8f, Alpha = 0.85f });
                float slx = Math.Clamp(x, ClipInset + 4 + line.Length * 2.6f, W - ClipInset - 4 - line.Length * 2.6f);
                P.Add(TextP(slx, y + 30, line, 10, Blood, italic: true, anchor: 1));
                blocked.Add((x, y + 30, 44));
                // recorded like landmarks, so the Keeper can drag a secret to where the
                // trouble actually is (keyed by index — secret texts can repeat)
                m.Secrets.Add(new Landmark
                {
                    Name = line, X = x, Y = y, GenX = x, GenY = y,
                    PrimStart = primStart, PrimCount = P.Count - primStart
                });
            }
        }

        // ---- frame ----
        P.Add(Rect(8, 8, W - 16, H - 16, null, Dark, 2.2f));
        P.Add(Rect(15, 15, W - 30, H - 30, null, Dark, 0.8f));

        // ---- cartouche ----
        // On a ward map the cartouche IS the city's name — the generated map title and a
        // separate settlement label put two different names on one place.
        m.Title = city ? townName : MapTitle(rngName, ti);
        string ground = ti switch
        {
            0 => "the open range", 1 => "the river bottoms", 2 => "settled country", 3 => "a field of the dead",
            4 => "mining country", 5 => "the high country", 6 => "the badlands",
            8 => "a city ward", _ => "the old places"
        };
        m.Sub = $"{ground}  ·  {ScaleLine(sp.Scale)}  ·  {Times[sp.Time].ToLowerInvariant()}";
        float cw = Math.Max(280, m.Title.Length * 12.5f + 40);
        P.Add(Rect(26, 26, cw, 78, "#f6efdd", Dark, 1.6f, 0.93f));
        P.Add(Rect(31, 31, cw - 10, 68, null, Dark, 0.7f));
        P.Add(TextP(26 + cw / 2, 62, m.Title, 21, Dark, bold: true, anchor: 1));
        P.Add(TextP(26 + cw / 2, 86, m.Sub, 10.5f, Gold, italic: true, anchor: 1));
        P.Add(TextP(26 + cw - 12, 42, "N° " + sp.Seed, 8, Gold, italic: true, anchor: 2));

        // ---- compass ----
        float cx2 = W - 64, cy2 = 92;
        P.Add(new Prim { Kind = PrimKind.Circle, Pts = new[] { cx2, cy2, 24 }, Stroke = Dark, StrokeW = 1.6f });
        P.Add(new Prim { Kind = PrimKind.Circle, Pts = new[] { cx2, cy2, 20 }, Stroke = Dark, StrokeW = 0.6f });
        P.Add(new Prim { Kind = PrimKind.Poly, Pts = new[] { cx2, cy2 - 19, cx2 + 5, cy2, cx2, cy2 + 19, cx2 - 5, cy2 }, Fill = Dark });
        P.Add(new Prim { Kind = PrimKind.Poly, Pts = new[] { cx2 - 19, cy2, cx2, cy2 + 5, cx2 + 19, cy2, cx2, cy2 - 5 }, Fill = null, Stroke = Dark, StrokeW = 1f });
        P.Add(TextP(cx2, cy2 - 32, "N", 12, Dark, bold: true, anchor: 1));

        // ---- scale bar ----
        var (barLen, barLabel) = sp.Scale switch
        {
            0 => (200f, "fifty yards"), 1 => (250f, "half a mile"), 2 => (333f, "ten miles"),
            4 => (250f, "four blocks"), _ => (333f, "fifty miles")
        };
        float sy = H - 40;
        P.Add(Rect(28, sy - 14, barLen + 28, 34, "#f6efdd", null, 0, 0.8f));
        P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { 40, sy, 40 + barLen, sy }, Stroke = Dark, StrokeW = 2f });
        foreach (var f in new[] { 0f, 0.5f, 1f })
            P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { 40 + barLen * f, sy - 5, 40 + barLen * f, sy + 5 }, Stroke = Dark, StrokeW = 1.6f });
        P.Add(TextP(40 + barLen / 2, sy + 16, barLabel + (sp.Grid ? $"   ·   squares are {GridLabel(sp.Scale)}" : ""), 9.5f, Dark, italic: true, anchor: 1));

        return m;
    }

    static string ScaleLine(int s) => s switch
    {
        0 => "close work, counted in yards", 1 => "a homestead and its bounds",
        2 => "a county, a hard day's ride", 4 => "a few blocks, and what is under them",
        _ => "a territory, weeks on the trail"
    };
    static string GridLabel(int s) => s switch { 0 => "ten yards", 1 => "a furlong", 2 => "five miles", 4 => "two blocks", _ => "a day's ride" };

    // ---------------------------------------------------------- names
    static readonly string[] TitleFirst =
    {
        "Coffin", "Gallows", "Salt", "Dead Horse", "Buzzard", "Widow's", "Cold Iron", "Lament",
        "Bone", "Ash", "Jubilee", "Providence", "Hangman's", "Rattler", "Mercy", "Perdition",
        "Silver", "Tallow", "Brimstone", "Copper", "Furnace", "Sorrow", "Owl Creek", "Redemption"
    };
    static readonly string[][] TitleGeo =
    {
        new[] { "Flats", "Range", "Prairie", "Reach" },     new[] { "Bottoms", "Bend", "Slough", "Crossing" },
        new[] { "County", "Hollow", "Township", "Claim" },  new[] { "Field", "Ground", "Acre", "Rest" },
        new[] { "Gulch", "Diggings", "Lode", "Draw" },      new[] { "Pass", "Divide", "Heights", "Timber" },
        new[] { "Badlands", "Wash", "Mesa", "Wells" },      new[] { "Barrows", "Stones", "Hollow", "Ring" },
        new[] { "Ward", "Bottoms", "Yards", "Works" },
    };
    static readonly string[] TownFirst =
    {
        "Gallows", "Dry", "Salt", "Lonesome", "Bitter", "Grace", "Coffin", "Candle",
        "Hollow", "Mule", "Cinder", "Vesper", "Harlow", "Deacon", "Rook", "Solace"
    };
    static readonly string[] TownSecond =
    {
        "Rest", "Gulch", "Springs", "Fork", "Landing", "Bluff", "Camp", "Junction",
        "Well", "Cross", "Ridge", "Hollow", "Mills", "Station", "Flat", "Creek"
    };
    static readonly string[] LmOwner = { "Weir", "Callow", "Merritt", "Boone", "Vance", "Crow", "Halloran", "Pryor", "Slade", "Ketch" };
    static readonly string[] LmAdj = { "Hanging", "Burned", "Broken", "Silent", "Old", "Drowned", "Crooked", "Weeping", "Salted", "Forgotten" };
    static readonly string[] SecretLines =
    {
        "something buried here", "it dens here", "they watch the trail", "old blood in the ground",
        "the ground is wrong", "an ambush waiting", "the door under the hill", "what the well keeps",
        "sign of the beast", "a cache — powder and coin"
    };

    static string MapTitle(Random rng, int ti) => Choice(rng, TitleFirst) + " " + Choice(rng, TitleGeo[Math.Clamp(ti, 0, 8)]);
    static string TownName(Random rng, int ti) =>
        ti == 8 ? Choice(rng, CityFirst) + " " + Choice(rng, CitySecond)
                : Choice(rng, TownFirst) + " " + Choice(rng, TownSecond);

    // City names carry the words a place uses once it has a stockyard and four newspapers.
    static readonly string[] CityFirst =
    {
        "Ashton", "Cordell", "Marrow", "Bellhaven", "Kirkwood", "Ransom", "Calvary", "Ellsworth",
        "Sable", "Thurlow", "Greystone", "Hollis", "Vesper", "Ironhead", "Chandler", "Merritt"
    };
    static readonly string[] CitySecond =
    {
        "City", "Junction", "Terminal", "Landing", "Works", "Yards", "Bluffs", "Crossing",
        "Union", "Basin", "Falls", "Heights"
    };
    static string Choice(Random rng, string[] a) => a[rng.Next(a.Length)];

    // ---------------------------------------------------------- symbols
    // Little line-art marks in a surveyor's hand. Each is centered on (x, y) and
    // scales with k so a battle map's features read bigger than a territory's.
    static void Sym(List<Prim> P, Random rng, string s, float x, float y, float k)
    {
        void L(float x0, float y0, float x1, float y1, string col, float w) =>
            P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { x + x0 * k, y + y0 * k, x + x1 * k, y + y1 * k }, Stroke = col, StrokeW = w });
        void Pl(string fill, string stroke, float w, params float[] rel)
        {
            var pts = new float[rel.Length];
            for (int i = 0; i < rel.Length; i += 2) { pts[i] = x + rel[i] * k; pts[i + 1] = y + rel[i + 1] * k; }
            P.Add(new Prim { Kind = PrimKind.Poly, Pts = pts, Fill = fill, Stroke = stroke, StrokeW = w });
        }
        void C(float dx, float dy, float r, string fill, string stroke, float w) =>
            P.Add(new Prim { Kind = PrimKind.Circle, Pts = new[] { x + dx * k, y + dy * k, r * k }, Fill = fill, Stroke = stroke, StrokeW = w });

        switch (s)
        {
            case "grass":
                L(-4, 0, -2, -6, Green, 1.2f); L(0, 1, 0, -7, Green, 1.2f); L(3, 0, 5, -5, Green, 1.2f); break;
            case "scrub":
                C(-3, 0, 3, null, "#8b8a5c", 1.1f); C(4, -1, 2.4f, null, "#8b8a5c", 1.1f); break;
            case "tree":
                L(0, 8, 0, 2, "#574433", 1.8f); C(0, -3, 7, Green, PineGreen, 1.2f); break;
            case "pine":
                Pl(PineGreen, "#46543e", 1f, 0, -15, -6.5f, 1, 6.5f, 1); L(0, 7, 0, 1, "#574433", 1.6f); break;
            case "hill":
                P.Add(new Prim { Kind = PrimKind.Line, Pts = Arc(x, y, 13 * k, 5.5f * k), Stroke = Ink, StrokeW = 1.3f });
                L(-5, -1, -3, 2, Ink, 0.8f); L(1, -2, 3, 2, Ink, 0.8f); break;
            case "dune":
                P.Add(new Prim { Kind = PrimKind.Line, Pts = Arc(x, y, 14 * k, 4 * k), Stroke = "#b89f6b", StrokeW = 1.4f }); break;
            case "mesa":
                Pl(Tan, Ink, 1.3f, -14, 0, -8, -11, 9, -11, 14, 0); L(-8, -11, -11, 0, Ink, 0.7f); L(9, -11, 11.5f, 0, Ink, 0.7f); break;
            case "cactus":
                L(0, 6, 0, -9, Green, 2.2f); L(-5, -4, -5, -1, Green, 1.8f); L(-5, -4, -1, -4, Green, 1.8f);
                L(4, -7, 4, -3, Green, 1.8f); L(4, -3, 1, -3, Green, 1.8f); break;
            case "rock":
                Pl("#b7ab93", Ink, 1.1f, -8, 2, -4, -6, 2, -7, 8, -1, 5, 3); break;
            case "reeds":
                L(-4, 2, -5, -8, "#6c7c54", 1.2f); L(-1, 2, -1, -10, "#6c7c54", 1.2f);
                L(2, 2, 3, -8, "#6c7c54", 1.2f); L(5, 2, 7, -6, "#6c7c54", 1.2f); break;
            case "tuft":
                L(-3, 0, -4, -5, "#55684a", 1.1f); L(0, 0, 0, -6, "#55684a", 1.1f); L(3, 0, 4, -5, "#55684a", 1.1f);
                C(6, 2, 1, null, WaterEdge, 0.8f); break;
            case "deadtree":
                L(0, 8, 0, -6, "#574433", 1.8f); L(0, -6, -5, -11, "#574433", 1.3f);
                L(0, -4, 4, -9, "#574433", 1.3f); L(0, -1, 3, -3, "#574433", 1f); break;
            case "grave":
                L(0, 5, 0, -6, Ink, 1.6f); L(-4, -2, 4, -2, Ink, 1.6f);
                Pl(null, Ink, 1f, 7, 5, 7, -1, 9, -3, 11, -1, 11, 5); break;
            case "trench":
                P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { x - 16 * k, y, x - 8 * k, y + 4 * k, x, y - 2 * k, x + 8 * k, y + 3 * k, x + 16 * k, y - 1 * k }, Stroke = "#6b5947", StrokeW = 2f }); break;
            case "stone":
                Pl("#9a917e", Dark, 1.1f, -2, 5, -2.5f, -8, 2, -9, 2.5f, 5); break;
            case "mound":
                P.Add(new Prim { Kind = PrimKind.Line, Pts = Arc(x, y, 12 * k, 7 * k), Stroke = Ink, StrokeW = 1.3f });
                L(-3, -4, 3, -4, Ink, 0.7f); break;
            case "ruin":
                P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { x - 8 * k, y - 2 * k, x - 8 * k, y + 5 * k, x + 8 * k, y + 5 * k, x + 8 * k, y - 5 * k, x + 3 * k, y - 5 * k }, Stroke = "#6b5947", StrokeW = 1.6f });
                C(-3, 3, 1.2f, "#6b5947", null, 0); C(2, 4, 1, "#6b5947", null, 0); break;
            case "bones":
                L(-5, -3, 5, 3, Bone, 2f); L(-5, 3, 5, -3, Bone, 2f); C(7, -4, 2, Bone, null, 0); break;
            case "snowpeak":
                Pl("#dfe4e6", Dark, 1.2f, -12, 6, 0, -13, 12, 6); Pl("#f5f7f7", null, 0, -4, -6, 0, -13, 4, -6, 0, -4); break;
            case "fence":
                L(-12, 0, 12, -1, "#7a5c38", 1.2f); L(-10, 3, -10, -4, "#7a5c38", 1.4f);
                L(0, 3, 0, -4, "#7a5c38", 1.4f); L(10, 3, 10, -4, "#7a5c38", 1.4f); break;
            case "field":
                Pl(null, "#a08c58", 1.1f, -14, -8, 14, -8, 14, 8, -14, 8);
                for (int i = -1; i <= 1; i++) L(-12, i * 4.5f, 12, i * 4.5f, "#a08c58", 0.6f); break;
            case "mine":
                Pl("#3a2c1e", null, 0, -6, 2, 0, -7, 6, 2); L(-7, 2, 7, 2, "#574433", 1.8f); L(-5, -3, 5, -3, "#574433", 1.2f); break;
            case "tailing":
                Pl(Tan, null, 0, -8, 4, 0, -6, 8, 4); P[^1].Alpha = 0.85f; break;
            case "well":
                C(0, 0, 4.5f, "#cbb98c", Ink, 1.4f); L(-4, -4, 4, -4, Ink, 1f); break;
            case "windmill":
                L(-4, 8, 0, -8, "#574433", 1.4f); L(4, 8, 0, -8, "#574433", 1.4f);
                L(-5, -8, 5, -8, "#574433", 1f); L(0, -13, 0, -3, Ink, 1f); L(-5, -8, 5, -8, Ink, 1f); break;
            case "corral":
                P.Add(new Prim { Kind = PrimKind.Circle, Pts = new[] { x, y, 9 * k }, Stroke = "#7a5c38", StrokeW = 1.4f, Dash = new[] { 3f, 2.4f } }); break;
            case "church":
                Pl("#d9cba8", Dark, 1.3f, -7, 6, -7, -4, 0, -9, 7, -4, 7, 6);
                L(0, -9, 0, -14, Dark, 1.4f); L(-2.5f, -12, 2.5f, -12, Dark, 1.4f); break;
            case "camp":
                Pl(null, "#574433", 1.4f, -6, 4, 0, -6, 6, 4); C(9, 3, 1.6f, Blood, null, 0); break;
            case "soddy":
                Pl("#b3a281", Dark, 1.2f, -8, 4, -8, -2, 0, -6, 8, -2, 8, 4); break;
            case "depot":                                  // a shed and a platform on the rails
                Pl("#cbbb95", Dark, 1.3f, -11, 5, -11, -3, 0, -8, 11, -3, 11, 5);
                L(-13, 7, 13, 7, Dark, 1.5f); L(-13, 9.5f, 13, 9.5f, Dark, 1.5f);
                for (float t = -12; t <= 12; t += 4) L(t, 6, t, 10.5f, Dark, 0.7f);
                break;
            case "stack":                                  // works, and the smoke off them
                Pl("#c7b892", Dark, 1.3f, -9, 6, -9, -1, 9, -1, 9, 6);
                Pl("#b5a681", Dark, 1.2f, 3, -1, 3, -12, 7, -12, 7, -1);
                L(5, -14, 8, -19, "#8c8578", 1.4f); L(8, -19, 5, -23, "#8c8578", 1.2f);
                break;
            case "pens":                                   // stockyard pens, seen from above
                for (int r3 = 0; r3 < 2; r3++)
                    for (int c3 = 0; c3 < 3; c3++)
                        Pl(null, "#7a6647", 1.1f, -10 + c3 * 7, -5 + r3 * 6, -4 + c3 * 7, -5 + r3 * 6,
                                                 -4 + c3 * 7, 0 + r3 * 6, -10 + c3 * 7, 0 + r3 * 6);
                break;
            case "wharf":                                  // a levee and two moored hulls
                L(-11, 4, 11, 4, "#7a6647", 2f);
                Pl("#c7b892", Dark, 1.1f, -9, 1, -3, 1, -4, -2, -8, -2);
                Pl("#c7b892", Dark, 1.1f, 3, 1, 9, 1, 8, -2, 4, -2);
                break;
            case "lodge":                                  // a good address, and a brass plate
                Pl("#d3c49e", Dark, 1.3f, -9, 6, -9, -4, 9, -4, 9, 6);
                Pl("#c0b088", Dark, 1.2f, -11, -4, 0, -10, 11, -4);
                for (float t = -6; t <= 6; t += 6) L(t, -4, t, 6, Dark, 0.9f);
                break;
            case "ford":
                L(-8, -3, 8, -3, WaterEdge, 1.6f); L(-8, 1, 8, 1, WaterEdge, 1.6f); break;
        }
    }

    // ---------------------------------------------------------- landmark editing
    /// Move a landmark to a new anchor: translates exactly its own prims (symbol +
    /// label) and nothing else. Pure model surgery — the UI drags, the smoke rig
    /// proves the arithmetic. Callers clamp the target inside the neatline.
    public static void MoveLandmark(MapModel m, int index, float nx, float ny)
        => MoveFeature(m, m.Landmarks, index, nx, ny);

    public static void MoveSecret(MapModel m, int index, float nx, float ny)
        => MoveFeature(m, m.Secrets, index, nx, ny);

    static void MoveFeature(MapModel m, List<Landmark> list, int index, float nx, float ny)
    {
        if (index < 0 || index >= list.Count) return;
        var lm = list[index];
        float dx = nx - lm.X, dy = ny - lm.Y;
        if (dx == 0 && dy == 0) return;
        for (int i = lm.PrimStart; i < lm.PrimStart + lm.PrimCount && i < m.P.Count; i++)
        {
            var p = m.P[i];
            if (p.Kind == PrimKind.Circle) { p.Pts[0] += dx; p.Pts[1] += dy; }   // (cx, cy, r) — radius stays
            else for (int j = 0; j + 1 < p.Pts.Length; j += 2) { p.Pts[j] += dx; p.Pts[j + 1] += dy; }
        }
        lm.X = nx; lm.Y = ny;
    }

    // ---------------------------------------------------------- geometry helpers
    static float Sq(float v) => v * v;
    static float Lerp(Random rng, float a, float b) => a + (float)rng.NextDouble() * (b - a);
    static float[] Longest(List<float[]> runs)
    {
        float[] best = null;
        foreach (var r in runs) if (best == null || r.Length > best.Length) best = r;
        return best;
    }

    static Prim Rect(float x, float y, float w, float h, string fill, string stroke, float sw, float alpha = 1f) =>
        new() { Kind = PrimKind.Poly, Pts = new[] { x, y, x + w, y, x + w, y + h, x, y + h }, Fill = fill, Stroke = stroke, StrokeW = sw, Alpha = alpha };

    static Prim TextP(float x, float y, string t, float size, string col, bool bold = false, bool italic = false, int anchor = 0) =>
        new() { Kind = PrimKind.Text, Pts = new[] { x, y }, Text = t, FontSize = size, Fill = col, Bold = bold, Italic = italic, Anchor = anchor };

    static float[] Arc(float x, float y, float rx, float ry)
    {
        var pts = new float[22];
        for (int i = 0; i <= 10; i++)
        {
            double a = Math.PI - Math.PI * i / 10;
            pts[i * 2] = x + (float)(Math.Cos(a) * rx);
            pts[i * 2 + 1] = y - (float)(Math.Sin(a) * ry);
        }
        return pts;
    }

    // Clip a polyline to a rectangle (Liang–Barsky per segment), returning the runs
    // that survive. Rivers, trails, and rails are deliberately generated from just
    // off one edge to just off the other so they read as passing through the country
    // — this trims them to the map's inner neatline so no ink crosses the border,
    // identically in all three renderers (the SVG viewBox used to hide it; the GDI
    // panel and the PDF page didn't).
    static List<float[]> ClipPolyline(float[] pts, float x0, float y0, float x1, float y1)
    {
        var runs = new List<float[]>();
        var cur = new List<float>();
        void EndRun() { if (cur.Count >= 4) runs.Add(cur.ToArray()); cur.Clear(); }
        for (int i = 0; i + 3 < pts.Length; i += 2)
        {
            float ax = pts[i], ay = pts[i + 1], bx = pts[i + 2], by = pts[i + 3];
            float dx = bx - ax, dy = by - ay, t0 = 0, t1 = 1;
            bool ok = true;
            Span<(float p, float q)> edges = stackalloc[] { (-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay) };
            foreach (var (p, q) in edges)
            {
                if (p == 0) { if (q < 0) { ok = false; break; } }
                else
                {
                    float r = q / p;
                    if (p < 0) { if (r > t1) { ok = false; break; } if (r > t0) t0 = r; }
                    else       { if (r < t0) { ok = false; break; } if (r < t1) t1 = r; }
                }
            }
            if (!ok) { EndRun(); continue; }
            if (cur.Count == 0) { cur.Add(ax + dx * t0); cur.Add(ay + dy * t0); }
            else if (t0 > 0) { EndRun(); cur.Add(ax + dx * t0); cur.Add(ay + dy * t0); }
            cur.Add(ax + dx * t1); cur.Add(ay + dy * t1);
            if (t1 < 1) EndRun();
        }
        EndRun();
        return runs;
    }

    // The map content's edge: the inner neatline. Line ends land ON it, and even a
    // wide river's round stroke cap stays inside the outer frame.
    const float ClipInset = 15f;

    static float[] Meander(Random rng, float x0, float y0, float x1, float y1, int segs, float wobble)
    {
        var pts = new List<(float x, float y)> { (x0, y0) };
        for (int i = 1; i < segs; i++)
        {
            float t = i / (float)segs;
            pts.Add((x0 + (x1 - x0) * t + Lerp(rng, -1, 1) * wobble * 0.5f,
                     y0 + (y1 - y0) * t + Lerp(rng, -1, 1) * wobble * 0.5f));
        }
        pts.Add((x1, y1));
        for (int r = 0; r < 2; r++) pts = Chaikin(pts, false);
        return Flat(pts);
    }

    static float[] Blob(Random rng, float cx, float cy, float r)
    {
        var pts = new List<(float x, float y)>();
        int n = 14;
        for (int i = 0; i < n; i++)
        {
            double a = i * Math.PI * 2 / n;
            double rr = r * (0.72 + rng.NextDouble() * 0.5);
            pts.Add((cx + (float)(Math.Cos(a) * rr), cy + (float)(Math.Sin(a) * rr * 0.8)));
        }
        for (int k = 0; k < 2; k++) pts = Chaikin(pts, true);
        return Flat(pts);
    }

    static List<(float x, float y)> Chaikin(List<(float x, float y)> pts, bool closed)
    {
        var o = new List<(float x, float y)>();
        if (!closed) o.Add(pts[0]);
        int n = closed ? pts.Count : pts.Count - 1;
        for (int i = 0; i < n; i++)
        {
            var a = pts[i];
            var b = pts[(i + 1) % pts.Count];
            o.Add((a.x * 0.75f + b.x * 0.25f, a.y * 0.75f + b.y * 0.25f));
            o.Add((a.x * 0.25f + b.x * 0.75f, a.y * 0.25f + b.y * 0.75f));
        }
        if (!closed) o.Add(pts[^1]);
        return o;
    }

    static float[] Flat(List<(float x, float y)> pts)
    {
        var f = new float[pts.Count * 2];
        for (int i = 0; i < pts.Count; i++) { f[i * 2] = pts[i].x; f[i * 2 + 1] = pts[i].y; }
        return f;
    }

    static void BlockAlong(List<(float x, float y, float r)> blocked, float[] pts, float r)
    {
        for (int i = 0; i + 1 < pts.Length; i += 8)
            blocked.Add((pts[i], pts[i + 1], r));
    }

    // "#rrggbb" over "#rrggbb" at alpha a — the composite the night sky actually shows
    static string Mix(string under, string over, float a)
    {
        int C2(string h, int i) => Convert.ToInt32(h.Substring(i, 2), 16);
        int r = (int)(C2(over, 1) * a + C2(under, 1) * (1 - a));
        int g = (int)(C2(over, 3) * a + C2(under, 3) * (1 - a));
        int b = (int)(C2(over, 5) * a + C2(under, 5) * (1 - a));
        return $"#{r:x2}{g:x2}{b:x2}";
    }

    // ---------------------------------------------------------- SVG
    static string N(float v) => v.ToString("0.##", System.Globalization.CultureInfo.InvariantCulture);
    static string Xml(string s) => s.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;");

    public static string ToSvg(MapModel m)
    {
        var sb = new StringBuilder();
        sb.Append($"<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 {m.W} {m.H}\" width=\"{m.W}\" height=\"{m.H}\" font-family=\"Georgia, 'Times New Roman', serif\">\n");
        sb.Append("<title>").Append(Xml(m.Title)).Append("</title>\n");
        foreach (var p in m.P)
        {
            string op = p.Alpha < 0.999f ? $" opacity=\"{N(p.Alpha)}\"" : "";
            string dash = p.Dash != null ? $" stroke-dasharray=\"{string.Join(" ", p.Dash.Select(N))}\"" : "";
            string stroke = p.Stroke != null ? $" stroke=\"{p.Stroke}\" stroke-width=\"{N(p.StrokeW)}\" stroke-linecap=\"round\" stroke-linejoin=\"round\"" : "";
            switch (p.Kind)
            {
                case PrimKind.Poly:
                    sb.Append($"<polygon points=\"{Pts(p.Pts)}\" fill=\"{p.Fill ?? "none"}\"{stroke}{dash}{op}/>\n");
                    break;
                case PrimKind.Line:
                    sb.Append($"<polyline points=\"{Pts(p.Pts)}\" fill=\"none\"{stroke}{dash}{op}/>\n");
                    break;
                case PrimKind.Circle:
                    sb.Append($"<circle cx=\"{N(p.Pts[0])}\" cy=\"{N(p.Pts[1])}\" r=\"{N(p.Pts[2])}\" fill=\"{p.Fill ?? "none"}\"{stroke}{dash}{op}/>\n");
                    break;
                case PrimKind.Text:
                    string anchor = p.Anchor == 1 ? "middle" : p.Anchor == 2 ? "end" : "start";
                    sb.Append($"<text x=\"{N(p.Pts[0])}\" y=\"{N(p.Pts[1])}\" font-size=\"{N(p.FontSize)}\" fill=\"{p.Fill ?? Ink}\" text-anchor=\"{anchor}\"")
                      .Append(p.Bold ? " font-weight=\"bold\"" : "").Append(p.Italic ? " font-style=\"italic\"" : "")
                      .Append(op).Append('>').Append(Xml(p.Text)).Append("</text>\n");
                    break;
            }
        }
        sb.Append("</svg>\n");
        return sb.ToString();

        static string Pts(float[] f)
        {
            var s = new StringBuilder();
            for (int i = 0; i + 1 < f.Length; i += 2)
            { if (i > 0) s.Append(' '); s.Append(N(f[i])).Append(',').Append(N(f[i + 1])); }
            return s.ToString();
        }
    }
}
