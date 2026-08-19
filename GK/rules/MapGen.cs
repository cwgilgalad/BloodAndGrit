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
    // Auto-properties rather than fields, and that is not decoration: a survey is written into
    // session.json and into every undo snapshot, and System.Text.Json does not serialize fields.
    // Source-compatible with the fields these were -- every read and every object initializer
    // stands unchanged.
    public string Terrain { get; set; } = "The Trail & the Open Range";
    public int Scale { get; set; }                // 0 gunfight · 1 homestead · 2 county · 3 territory
    public int Time { get; set; } = 1;            // 0 first light · 1 high noon · 2 dusk · 3 dead of night
    public int Water { get; set; }                // index into MapGen.Waters
    public bool Trail { get; set; } = true;
    public bool Rail { get; set; }
    public bool Town { get; set; } = true;
    public bool Grid { get; set; }
    public bool Secrets { get; set; }
    public int Landmarks { get; set; } = 5;
    public int Seed { get; set; }
    // The sky over the survey: an index into MapGen.Weathers, 0 = let the country decide.
    // Appended last so every stored Scale/Time/Water index keeps its old meaning.
    public int Weather { get; set; }

    /// <summary>What this place is called, when the Keeper already knows — the town rolled on the
    /// Generators tab, or a name typed on the Map bar. Empty means the survey names it itself. It
    /// replaces the drawn name only; the roll that would have produced one is still made, so
    /// naming a place never redraws the country under it.</summary>
    public string PlaceName { get; set; } = "";
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

    // The settlement, when it's a discrete town rather than a city ward that fills the
    // whole sheet — movable exactly like a landmark, so a town the survey seated badly
    // can be picked up and put on better ground. Null on a city map and when Town is off.
    public Landmark Town;

    // True when the survey wanted to seat the town in the water and it was walked onto dry
    // ground instead. The app says so in the roll log — a Keeper who wrote down a map's number
    // is owed an explanation when the same number draws a town in a different spot than before.
    public bool TownSeated;

    // The water this map carries, kept with the model so the town-seating rule at
    // generation and the "move it off the water" action in the app ask the same question
    // of the same geometry. RiverPts is the channel's centerline; LakeR is 0 when there's
    // no lake.
    public float[] RiverPts;
    public float RiverHalf;
    public float LakeX, LakeY, LakeR;

    // The sky this survey was drawn under, resolved — so the app can say it in the roll log even
    // when the Keeper left the choice to the country.
    public string Weather = "";
}

public static class MapGen
{
    public static readonly string[] Terrains =
    {
        "The Trail & the Open Range", "Rivers, Lakes & Swamps", "Towns, Homesteads & Haunted Houses",
        "Graveyards & Battlefields", "Mines & Under the Earth", "Winter & the High Country",
        "Desert & the Badlands", "The Old Places", "The Lamplit City",
        // Appended, never inserted: every index above is the Bestiary's Appendix "The Grounds" in
        // the book's own order, and a stored MapSpec.Terrain, a WeatherByGround row and a saved
        // survey all read by position. The seven below are the app's, drawn from the country west
        // and south of the Mississippi that the nine did not already name — timber, black water,
        // canyon, shortgrass, thornscrub, alkali and salt marsh. No state is named in any of them:
        // this is a frontier a table can put wherever their trail runs.
        "Pinewoods & the Deep Timber", "Bayou, Cypress & the Delta", "Canyon Country & the Mesas",
        "Shortgrass & the Staked Plain", "Brush Country & the Border", "Salt Flats & the Alkali Sink",
        "The Gulf Coast & the Marshes"
    };
    /// <summary>The countries a settlement can be set down in: every terrain except the Lamplit
    /// City, which is not ground you stand a town on — it IS the town, at a different scale.
    /// Derived from <see cref="Terrains"/> rather than typed out again, so a country added later
    /// is offered as a setting without anyone remembering this list exists.</summary>
    public static readonly string[] SettingTerrains =
        Terrains.Where(t => t != "The Lamplit City").ToArray();

    // The city ward is appended rather than slotted in by size, so every stored or
    // remembered Scale index keeps meaning what it meant before Ch. XIV existed.
    public static readonly string[] Scales =
        { "A gunfight (yards)", "A homestead (half a mile)", "A county (a day's ride)", "A territory (the long trail)",
          "A city ward (blocks)" };
    public static readonly string[] Times = { "First light", "High noon", "Dusk", "Dead of night" };
    public static readonly string[] Waters = { "As the land wills", "No water", "A creek", "A river", "A lake", "River & lake" };

    /// <summary>The sky. Index 0 lets the country pick its own — the high country gets snow the
    /// badlands never will — and the rest force it. Weather is half of what a day on the trail
    /// actually is: the same county in a blizzard is a different map.</summary>
    public static readonly string[] Weathers =
    {
        "As the sky wills", "Fair", "Sunny & hot", "Overcast", "Rain", "Thunderstorm",
        "Fog", "Wind & dust", "Snow", "Blizzard", "Hail", "Hard freeze"
    };

    // What each ground is apt to get, weighted by repetition. Rolled on its own stream, so
    // changing any other setting never reshuffles the sky.
    static readonly int[][] WeatherByGround =
    {
        new[] { 1, 1, 2, 2, 3, 4, 7, 7, 5 },        // 0 open range — hot, windy, the odd storm
        new[] { 1, 3, 3, 4, 4, 5, 6, 6, 2 },        // 1 river bottoms — wet and fogbound
        new[] { 1, 1, 2, 3, 3, 4, 5, 7, 10 },       // 2 settled country
        new[] { 1, 3, 3, 4, 6, 6, 5, 2, 11 },       // 3 graveyards & battlefields — grey and still
        new[] { 1, 2, 3, 3, 4, 7, 10, 11, 5 },      // 4 mining country
        new[] { 8, 8, 9, 9, 11, 3, 3, 1, 10 },      // 5 the high country — snow, and worse
        new[] { 2, 2, 2, 1, 7, 7, 7, 5, 10 },       // 6 badlands — heat and blowing sand
        new[] { 6, 6, 3, 3, 4, 1, 11, 5, 7 },       // 7 the old places — fog suits them
        new[] { 3, 3, 4, 6, 6, 7, 1, 2, 5 },        // 8 a city ward — coal smoke and river fog
        new[] { 1, 3, 3, 4, 4, 6, 6, 5, 8 },        // 9 deep timber — overcast, rain, and fog in it
        new[] { 2, 4, 4, 5, 5, 6, 6, 3, 1 },        // 10 the bayou — hot, wet, thunder off the Gulf
        new[] { 1, 2, 2, 3, 7, 7, 5, 10, 4 },       // 11 canyon country — sun, wind, a flash flood
        new[] { 7, 7, 2, 1, 5, 5, 10, 9, 3 },       // 12 the shortgrass — wind, hail, and the blizzard
        new[] { 2, 2, 2, 1, 7, 5, 3, 4, 10 },       // 13 brush country — heat, and heat, and heat
        new[] { 2, 2, 1, 7, 7, 3, 11, 5, 10 },      // 14 the alkali sink — glare by day, freezing by night
        new[] { 4, 4, 5, 5, 6, 6, 2, 3, 1 },        // 15 the coast marshes — rain, fog, and the big blow
    };

    // ---- palette (the books' frontier colors, map-toned) ----
    const string Ink = "#4a3826", Dark = "#3a2c1e", Blood = "#8f1d1d", Gold = "#967432";
    const string WaterEdge = "#7d98a1", WaterFill = "#b9cbcf", TrailBrown = "#7a5c38";
    const string Green = "#6f7d54", PineGreen = "#5d6f52", Tan = "#d8c49a", Bone = "#b5a98c";
    // The clear paper a ward's street grid leaves round itself. The grid is laid to it, and the
    // country roads are cut back to it, so the two agree by construction rather than by luck.
    const float WardMargin = 40;

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
               rngLand = R(5), rngLm = R(6), rngHour = R(7), rngSecrets = R(8),
               rngSky = R(10);
        // One namer for the whole survey, so no two things on this sheet share a distinctive word:
        // the town, the cartouche and every landmark draw from it and it remembers what it spent.
        // Seeded off the map seed like every stream above, so a survey is still the same survey.
        var namer = Names.For(unchecked(sp.Seed * 92821 + 11));
        var stock = Names.Data;

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
            4 => "#ece2cc", 5 => "#eef0ee", 6 => "#f2e5c6", 8 => "#e7e4dc",
            9 => "#e4e8d6", 10 => "#dee7dc", 11 => "#f0e0cb", 12 => "#ece9d2",
            13 => "#e9e5cc", 14 => "#f1f0e7", 15 => "#e2e8e2",
            _ => "#e8e0cf"
        };
        P.Add(Rect(0, 0, W, H, bg, null, 0));

        // keep-out circles: features, labels, and furniture never overprint each other
        var blocked = new List<(float x, float y, float r)>
        {
            (W - 64, 92, 95),                   // compass
            (150, H - 40, 170),                 // scale bar
        };
        // The cartouche, covered by a ROW of circles along its spine rather than one round the whole
        // box: a circle wide enough for a 460x92 box also blocks two hundred pixels of clear country
        // underneath it, which is country the survey could have used.
        float cartW = CartoucheMaxWidth(sp, ti, city);
        // A local function and not two copies: the ward below CLEARS this list and rebuilds it, and
        // when the row of circles lived inline the ward's rebuild kept the old typed circle at
        // (170,70) r190 — which reaches x=360 against a box that reaches 523. Every ward printed a
        // landmark half under the cartouche, and the fix here never touched them.
        void BlockCartouche()
        {
            for (float bx = 26 + 50; bx < 26 + cartW - 50; bx += 66) blocked.Add((bx, 72, 68));
            blocked.Add((26 + cartW - 50, 72, 68));
        }
        BlockCartouche();
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
            ? ti switch
              {
                  1 => 5, 5 => 4, 6 => 1, 3 => rngWater.Next(2) == 0 ? 2 : 1,
                  10 => 5, 15 => 4,                          // the bayou and the coast ARE their water
                  9 or 11 or 13 => 3,                        // timber creeks, the canyon's cutter, the border river
                  12 or 14 => 1,                             // the staked plain and the sink hold none
                  _ => rngWater.Next(3) == 0 ? 2 : 1
              }
            : sp.Water;
        float[] riverPts = null;
        (float x, float y, float r) lake = default;
        bool frozen = ti == 5;
        // Where the water's ink begins, its channel half-width, and where it ends — so a city ward
        // can leave the waterway open (no blocks stamped over it) and redraw it, unbroken, on top.
        int waterStart = P.Count;
        float waterHalf = 0f;

        // One clip per stroke width, not one for the sheet — see ClipFor. A river's edge is 13px and
        // its round cap paints half of that past the last vertex, which is how blue ink came to sit
        // on the outer frame of a rendered city ward.
        var clipRiver = ClipFor(13f, W, H);
        var clipCreek = ClipFor(4.5f, W, H);
        var clipTrail = ClipFor(2.6f, W, H);
        var clipRail  = ClipFor(2.2f, W, H);
        if (water is 3 or 5)                                     // a river, edge to edge
        {
            bool vert = rngWater.Next(2) == 0;
            var raw = vert
                ? Meander(rngWater, Lerp(rngWater, 0.25f, 0.75f) * W, -12, Lerp(rngWater, 0.25f, 0.75f) * W, H + 12, 7, 90)
                : Meander(rngWater, -12, Lerp(rngWater, 0.25f, 0.75f) * H, W + 12, Lerp(rngWater, 0.25f, 0.75f) * H, 7, 90);
            var runs = ClipPolyline(raw, clipRiver.x0, clipRiver.y0, clipRiver.x1, clipRiver.y1);
            foreach (var run in runs)                            // edge under, water over — layer order kept
                P.Add(new Prim { Kind = PrimKind.Line, Pts = run, Stroke = WaterEdge, StrokeW = 13 });
            foreach (var run in runs)
                P.Add(new Prim { Kind = PrimKind.Line, Pts = run, Stroke = frozen ? "#dfe8ea" : WaterFill, StrokeW = 9 });
            riverPts = Longest(runs);
            waterHalf = 16;
            if (riverPts != null) BlockAlong(blocked, riverPts, 26);
        }
        else if (water == 2)                                     // a creek
        {
            bool vert = rngWater.Next(2) == 0;
            var raw = vert
                ? Meander(rngWater, Lerp(rngWater, 0.2f, 0.8f) * W, -12, Lerp(rngWater, 0.2f, 0.8f) * W, H + 12, 8, 110)
                : Meander(rngWater, -12, Lerp(rngWater, 0.2f, 0.8f) * H, W + 12, Lerp(rngWater, 0.2f, 0.8f) * H, 8, 110);
            foreach (var run in ClipPolyline(raw, clipCreek.x0, clipCreek.y0, clipCreek.x1, clipCreek.y1))
            {
                P.Add(new Prim { Kind = PrimKind.Line, Pts = run, Stroke = WaterEdge, StrokeW = 4.5f });
                if (riverPts == null || run.Length > riverPts.Length) riverPts = run;
            }
            waterHalf = 10;
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
        int waterEnd = P.Count;

        // Hand the water to the model, so the seating rule below, the city's block test, and the
        // app's "move it off the water" all read one description of where the wet ground is.
        m.RiverPts = riverPts;
        m.RiverHalf = waterHalf;
        m.LakeX = lake.x; m.LakeY = lake.y; m.LakeR = lake.r;

        // True when a spot of the given reach touches the river channel or the lake — so a city ward
        // can refuse to build there, leaving the water an open, legible course through the blocks.
        bool OverWater(float px, float py, float pad) => OnWater(m, px, py, pad);

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
        // A town seated in the river or the lake draws its roofs and its streets straight through
        // the water, and the two layers argue — you can't tell a building from a bank (user-reported).
        // Walk the seat to the nearest dry ground before anything is drawn, while the trail still
        // has time to meet it there. A town that wasn't in the water doesn't move at all, so every
        // survey that was fine stays exactly as it was.
        if (!city)
        {
            var seat = DryGroundNear(m, tx, ty, TownReach(sp.Scale));
            m.TownSeated = seat.x != tx || seat.y != ty;
            (tx, ty) = seat;
        }
        // Where the roads' ink begins and ends. A ward stamps its blocks over everything drawn so
        // far, which buried the trail and the rail and left them as disconnected stubs in the street
        // gaps — the strange shading a Keeper reported. The span is re-inked on top of the blocks,
        // the same way the water already is.
        bool ward = city && sp.Town;
        int roadStart = P.Count;
        float[] railPts = null;
        if (sp.Trail)
        {
            bool vert = rngTrail.Next(2) == 0;
            float a0 = Lerp(rngTrail, 0.2f, 0.8f), a1 = Lerp(rngTrail, 0.2f, 0.8f);
            var leg1 = vert ? Meander(rngTrail, a0 * W, -12, tx, ty, 5, 60) : Meander(rngTrail, -12, a0 * H, tx, ty, 5, 60);
            var leg2 = vert ? Meander(rngTrail, tx, ty, a1 * W, H + 12, 5, 60) : Meander(rngTrail, tx, ty, W + 12, a1 * H, 5, 60);
            // Round the lake, across the river. A trail does not swim.
            SkirtLake(leg1, lake.x, lake.y, lake.r, 14);
            SkirtLake(leg2, lake.x, lake.y, lake.r, 14);
            foreach (var leg in new[] { leg1, leg2 })
            {
                foreach (var run in RoadRuns(leg, clipTrail, ward, W, H))
                    P.Add(new Prim { Kind = PrimKind.Line, Pts = run, Stroke = TrailBrown, StrokeW = 2.6f, Dash = new[] { 8f, 5f } });
                MarkCrossings(P, m, leg, rail: false);
            }
            if (sp.Scale >= 2 && rngTrail.Next(2) == 0)          // a fork, at riding scales
            {
                int j = rngTrail.Next(leg2.Length / 4) * 2;
                var fork = Meander(rngTrail, leg2[j], leg2[j + 1], rngTrail.Next(2) == 0 ? -12 : W + 12, Lerp(rngTrail, 0.15f, 0.85f) * H, 4, 70);
                SkirtLake(fork, lake.x, lake.y, lake.r, 14);
                foreach (var run in RoadRuns(fork, clipTrail, ward, W, H))
                    P.Add(new Prim { Kind = PrimKind.Line, Pts = run, Stroke = TrailBrown, StrokeW = 2f, Dash = new[] { 7f, 5f } });
                MarkCrossings(P, m, fork, rail: false);
            }
        }

        // ---- the rail line (straight as money) ----
        if (sp.Rail)
        {
            var rawRail = Meander(rngRail, -12, Lerp(rngRail, 0.25f, 0.75f) * H, W + 12, Lerp(rngRail, 0.25f, 0.75f) * H, 3, 30);
            // A railroad bends round a lake and trestles a river. Straight as money, but not through
            // water: the grade goes round the standing water and over the running.
            SkirtLake(rawRail, lake.x, lake.y, lake.r, 20);
            railPts = rawRail;
            foreach (var rail in ClipPolyline(rawRail, clipRail.x0, clipRail.y0, clipRail.x1, clipRail.y1))
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
                        // A tie reaches 5px either side of the rail, so the guard has to hold in
                        // BOTH axes or a tie on a rail running near the top edge pokes past the
                        // neatline — the same fault the river's stroke cap had.
                        if (px < 22 || px > W - 22 || py < 22 || py > H - 22) continue;
                        // No ties laid on the water: a trestle is drawn as one by MarkCrossings.
                        if (OnWater(m, px, py, 0)) continue;
                        P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { px - nx, py - ny, px + nx, py + ny }, Stroke = "#4a4038", StrokeW = 1.2f });
                    }
                }
            }
            MarkCrossings(P, m, rawRail, rail: true);
        }
        int roadEnd = P.Count;

        // ---- the settlement ----
        // The town's name and ground are claimed whether or not it's shown, so toggling
        // Settlement adds/removes only the town's own ink — the land never reshuffles.
        // Naming draws off the namer, which is a stream of its own, so a Keeper who names their
        // town cannot rearrange the country under it: rngTown lays the street grid and is never
        // touched by a name either way. That invariant used to be maintained by hand — the draw
        // was made and thrown away so rngTown would not fall a step behind — and is now structural.
        string rolled = namer.Town(stock, city);
        string townName = string.IsNullOrWhiteSpace(sp.PlaceName) ? rolled : sp.PlaceName.Trim();
        blocked.Add((tx, ty, sp.Scale == 0 ? 150 : 95));
        if (sp.Town && city)
        {
            // A ward: avenues and cross streets, the blocks between them, and the
            // three things every city in Ch. XIV has — a depot, works that smoke,
            // and a quarter the city would rather not look at.
            const float m0 = WardMargin;
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
                    // No block is raised in the river or the lake — the waterway stays open ground,
                    // so the water reads as one course through the city, not blue scraps between roofs.
                    float rr = Math.Min(bw, bh) * 0.35f;
                    if (waterHalf > 0 || lake.r > 0)
                        if (OverWater(bx + bw / 2, by + bh / 2, rr))
                        {
                            // Not a hole punched in the ward: the ground a city keeps beside its
                            // water. Levee, yard and mud, so the waterfront reads as somewhere a
                            // posse can stand rather than as a block the generator forgot.
                            P.Add(Rect(bx, by, bw, bh, Bone, null, 0, 0.3f));
                            continue;
                        }
                    // A railroad takes its right-of-way through a ward the way it does through a real
                    // city — the blocks give way to the grade, not the other way about — and the line
                    // is re-inked below so it runs unbroken instead of surfacing in the street gaps.
                    if (railPts != null && PolyDistSq(railPts, bx + bw / 2, by + bh / 2) < Sq(rr + 14))
                    {
                        P.Add(Rect(bx, by, bw, bh, Bone, null, 0, 0.3f));
                        continue;
                    }
                    P.Add(Rect(bx, by, bw, bh, "#d9cba8", Dark, 1.2f));
                    // a couple of blocks are dense tenement rows rather than one mass
                    if (rngTown.Next(3) == 0)
                        for (int t = 1; t < 4; t++)
                            P.Add(new Prim { Kind = PrimKind.Line,
                                Pts = new[] { bx + bw * t / 4f, by, bx + bw * t / 4f, by + bh },
                                Stroke = Dark, StrokeW = 0.8f, Alpha = 0.7f });
                }
            // Redraw the water over the streets and block-borders so the course is unbroken and plainly
            // blue — the river a city is built along, not one hidden beneath it. The banks are already
            // lined with blocks; a redraw on top is what a surveyor's hand would ink last.
            for (int i = waterStart; i < waterEnd; i++)
            {
                var wp = P[i];
                P.Add(new Prim { Kind = wp.Kind, Pts = wp.Pts, Fill = wp.Fill, Stroke = wp.Stroke,
                                 StrokeW = wp.StrokeW, Dash = wp.Dash, Alpha = wp.Alpha });
            }
            // The same hand, the same pass: rail and road re-inked over the blocks. The trail was cut
            // back to the ward's edge above, so nothing dashed crosses a roof — only the rail runs
            // through, and it runs through ground the blocks were told to leave it.
            for (int i = roadStart; i < roadEnd; i++)
            {
                var rp = P[i];
                P.Add(new Prim { Kind = rp.Kind, Pts = rp.Pts, Fill = rp.Fill, Stroke = rp.Stroke,
                                 StrokeW = rp.StrokeW, Dash = rp.Dash, Alpha = rp.Alpha });
            }
            // The furniture keeps its keep-out; so does the water, so no depot or landmark lands in it.
            blocked.Clear();
            BlockCartouche();
            blocked.Add((W - 64, 92, 95)); blocked.Add((150, H - 40, 170));
            blocked.Add((W - 144, H - 104, 135));            // the key's corner — nothing gets planted under it
            if (riverPts != null) BlockAlong(blocked, riverPts, waterHalf + 8);
            if (lake.r > 0) blocked.Add((lake.x, lake.y, lake.r + 14));
        }
        else if (sp.Town)
        {
            int townStart = P.Count;                             // its ink begins here, so it can be picked up whole
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
            float nameY = ty + (sp.Scale == 0 ? 66 : 48);
            P.Add(TextP(tx, nameY, townName, 14, Ink, bold: true, anchor: 1));
            // What the name IS, said under it. A survey that draws a settlement carries two names on
            // one sheet — the country's in the cartouche, the town's down here — and both are drawn
            // from the same well of frontier words, so "Coffin Flats" up top and "Coffin Wells" on
            // the ground read as the same kind of thing (user-reported: which name is the settlement
            // and which is the territory). The caption says "settlement" rather than "town" because
            // that is the word on the checkbox that draws it: the map and the control that governs
            // it should not need translating between them.
            P.Add(TextP(tx, nameY + 13, "the settlement", 9, Gold, italic: true, anchor: 1));
            // The whole settlement — street, buildings, church, name — as one movable thing,
            // recorded the way a landmark is so it drags with the same hand.
            m.Town = new Landmark
            {
                Name = townName, X = tx, Y = ty, GenX = tx, GenY = ty,
                PrimStart = townStart, PrimCount = P.Count - townStart
            };
        }

        // ---- the land itself ----
        // Each ground's furniture. The landforms — hills, ridges, bluffs, peaks, whole ranges,
        // stands of timber — are weighted by repetition rather than picked evenly, so a county
        // reads as country with a shape to it instead of a scatter of one of everything.
        string[] kit = ti switch
        {
            0 => new[] { "grass", "grass", "grass", "scrub", "scrub", "tree", "hill", "hill", "hills",
                         "ridge", "bluff", "forest", "bones", "rock", "butte" },
            1 => new[] { "reeds", "reeds", "deadtree", "deadtree", "tree", "tuft", "tuft", "rock", "grass",
                         "marsh", "marsh", "forest", "spring", "hill" },
            2 => new[] { "grass", "grass", "tree", "tree", "fence", "fence", "field", "field", "hill",
                         "scrub", "orchard", "orchard", "forest", "hills", "spring" },
            3 => new[] { "grave", "grave", "grave", "deadtree", "grass", "grass", "trench", "rock", "scrub",
                         "mound", "hill", "forest" },
            4 => new[] { "mesa", "mesa", "rock", "rock", "rock", "mine", "tailing", "scrub", "deadtree",
                         "mountain", "ridge", "bluff", "hills", "hoodoo" },
            5 => new[] { "pine", "pine", "pine", "pine", "snowpeak", "snowpeak", "snowpeak", "rock", "deadtree",
                         "mountain", "mountain", "range", "bluff", "pinestand", "pinestand", "ridge" },
            6 => new[] { "cactus", "cactus", "cactus", "mesa", "mesa", "dune", "dune", "bones", "bones",
                         "scrub", "rock", "butte", "butte", "hoodoo", "hoodoo", "bluff", "ridge" },
            9 => new[] { "pine", "pine", "pinestand", "pinestand", "forest", "forest", "tree", "tree",
                         "rock", "deadtree", "hill", "hills", "ridge", "spring", "tuft" },
            10 => new[] { "reeds", "reeds", "reeds", "marsh", "marsh", "marsh", "deadtree", "deadtree",
                          "tuft", "tuft", "forest", "wharf", "spring", "grass" },
            11 => new[] { "mesa", "mesa", "butte", "butte", "hoodoo", "hoodoo", "bluff", "bluff",
                          "ridge", "rock", "rock", "scrub", "cactus", "ruin", "stone" },
            12 => new[] { "grass", "grass", "grass", "grass", "tuft", "tuft", "scrub", "bones", "bones",
                          "hill", "hills", "ridge", "well", "windmill" },
            13 => new[] { "scrub", "scrub", "scrub", "cactus", "cactus", "tuft", "mesa", "rock",
                          "deadtree", "hills", "ridge", "corral", "spring", "bones" },
            14 => new[] { "dune", "dune", "bones", "bones", "rock", "scrub", "mesa", "butte", "hoodoo",
                          "tuft", "ridge", "bluff", "well" },
            15 => new[] { "marsh", "marsh", "marsh", "reeds", "reeds", "dune", "dune", "tuft",
                          "deadtree", "wharf", "forest", "grass", "spring" },
            _ => new[] { "stone", "stone", "stone", "ruin", "ruin", "deadtree", "deadtree", "mound", "tree",
                         "grass", "hill", "forest", "hoodoo" },
        };
        if (city) kit = new[] { "stack", "stack", "depot", "pens", "church", "wharf", "stack", "pens" };
        int count = city ? 9 : (sp.Scale == 0 ? 16 : 30);
        for (int i = 0; i < count; i++)
        {
            var (x, y) = Place(rngLand, 15 * k + (city ? 20 : 12));
            if (float.IsNaN(x)) continue;
            string sym = kit[rngLand.Next(kit.Length)];
            Sym(P, rngLand, sym, x, y, k);
            // In a city, the little marks sit on the built-up blocks, so name what each one is —
            // otherwise it's a scatter of unreadable symbols. Country marks (a tree, a hill) need no label.
            if (city && CitySymCaption(sym) is string cap)
            {
                float cy = y + 15 * k + 9;
                P.Add(TextP(x, cy, cap, 8.5f, Ink, italic: true, anchor: 1));
                blocked.Add((x, cy, 22));
            }
        }

        // ---- named landmarks ----
        // What people build, anywhere — then what this particular country has in it. Splitting the
        // two is the whole point: the high country's map should offer a Divide and a Notch, and the
        // badlands' should offer a Butte, instead of every ground drawing from one flat list.
        var nouns = new List<(string sym, string noun)>
        {
            ("deadtree", "Hanging Tree"), ("rock", "Lookout"), ("well", "Well"), ("ruin", "Burned Homestead"),
            ("grave", "Boot Hill"), ("mine", "Diggings"), ("windmill", "Windmill"), ("corral", "Corral"),
            ("stone", "Standing Stones"), ("church", "Mission"), ("camp", "Cold Camp"), ("soddy", "Soddy"),
        };
        // A ground's own places arrive already named — The Palisades, Lonesome Peak — so the
        // decorator below has to leave them alone. Run through it they came out "The Crooked The
        // Wall" and "Pryor's The Spine", which is the same fault the city list hit and fixed.
        var ownName = new HashSet<string>(StringComparer.Ordinal);
        foreach (var g in GroundLandmarks(ti)) { nouns.Add(g); ownName.Add(g.noun); }
        if (riverPts != null || lake.r > 0) { nouns.Add(("ford", "Ford")); nouns.Add(("ford", "Crossing")); }
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
            // rngLm keeps deciding the SHAPE and the namer only supplies the words — the same
            // stream places these landmarks, so moving the form rolls onto the namer would shift
            // every rock on the sheet.
            if (city)
                name = pick.noun.StartsWith("The ")
                    ? pick.noun
                    : rngLm.Next(2) == 0 ? "The " + pick.noun
                                         : namer.Draw(stock.LmOwner) + " " + pick.noun;
            else if (ownName.Contains(pick.noun))
            {
                // The country's own. A man can own the working of a place ("Merritt's Pinery")
                // but not the Divide, so the owner form only takes the name off the article.
                name = pick.noun.StartsWith("The ") && rngLm.Next(4) == 0
                    ? namer.Draw(stock.LmOwner) + "'s " + pick.noun.Substring(4)
                    : pick.noun;
            }
            else
                name = namer.Landmark(stock, pick.noun,
                    rngLm.Next(3) == 0 ? 0 : rngLm.Next(2) == 0 ? 1 : 2);
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

        // ---- the key (city wards only) ----
        // A ward is a crowded sheet — avenues, blocks, works, water all inked over one another —
        // and a Keeper running a scene shouldn't have to guess which mark is the depot and which
        // is the smelter. Country maps get no key: out there a mark is a tree or a hill, and the
        // survey already labels the ones that matter.
        if (city && sp.Town) CityKey(P, W, H);

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

        // ---- the weather ----
        // Over the hour, because the sky is the nearer thing: a blizzard whitens noon and midnight
        // alike. Drawn from its own stream so forcing rain doesn't move a single rock.
        int wx = WeatherFor(sp.Weather, ti, rngSky);
        DrawWeather(P, rngSky, wx, W, H, m);

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
        m.Title = city ? townName : namer.MapTitle(stock, ti);
        string ground = GroundWord(ti);
        m.Weather = Weathers[wx];
        m.Sub = $"{ground}  ·  {ScaleLine(sp.Scale)}  ·  {Times[sp.Time].ToLowerInvariant()}  ·  {WeatherLine(wx)}";
        // What KIND of name the big one is, in the small line above it. The cartouche used to state
        // a name and leave the reader to work out what it named; on a sheet that also draws a town,
        // that is a genuine question with two answers on it. The subtitle already gives the scale,
        // but it gives it as the ride ("a county, a hard day's ride"), which describes the map — this
        // line reaches the other way and describes the NAME. It reads as a survey heading because
        // that is exactly what it is.
        string of = city ? "the city ward of" : sp.Scale switch
        {
            0 => "the ground at", 1 => "the country about", 2 => "the county of", _ => "the territory of"
        };
        // Wide enough for ALL THREE lines. Sizing it off the title alone left the subtitle hanging out
        // past the box and off the paper once the weather was added to it.
        float cw = Math.Max(280, Math.Max(m.Title.Length * 12.5f + 40,
                                          Math.Max(m.Sub.Length * 5.2f + 34, of.Length * 6.5f + 96)));
        P.Add(Rect(26, 26, cw, 92, "#f6efdd", Dark, 1.6f, 0.93f));
        P.Add(Rect(31, 31, cw - 10, 82, null, Dark, 0.7f));
        P.Add(TextP(26 + cw / 2, 48, of, 10, Gold, italic: true, anchor: 1));
        P.Add(TextP(26 + cw / 2, 76, m.Title, 21, Dark, bold: true, anchor: 1));
        P.Add(TextP(26 + cw / 2, 100, m.Sub, 10.5f, Gold, italic: true, anchor: 1));
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

    // ---------------------------------------------------------- the weather
    /// <summary>Resolve the sky: an explicit pick stands, and 0 rolls one this ground would
    /// actually get. Pure and seeded, so the same map number always draws the same day.</summary>
    public static int WeatherFor(int pick, int ti, Random rng)
    {
        if (pick > 0 && pick < Weathers.Length) return pick;
        var table = WeatherByGround[Math.Clamp(ti, 0, WeatherByGround.Length - 1)];
        return table[rng.Next(table.Length)];
    }

    /// <summary>The sky in the cartouche's voice — a survey doesn't say "Wind &amp; dust".</summary>
    public static string WeatherLine(int w) => w switch
    {
        1 => "fair", 2 => "clear and hot", 3 => "overcast", 4 => "rain",
        5 => "thunder on the ridge", 6 => "fog to the ground", 7 => "wind and blowing dust",
        8 => "snow falling", 9 => "a blizzard", 10 => "hail", 11 => "hard freeze", _ => "fair"
    };

    /// <summary>Ink the sky over everything else. Each is a wash plus its own marks, kept light —
    /// the map still has to be read through it.</summary>
    static void DrawWeather(List<Prim> P, Random rng, int w, float W, float H, MapModel m)
    {
        // The WASH is the sky's colour over the whole sheet and belongs on the water as much as on
        // the ground — a lake under a thunderhead is a darker lake. The scattered strokes are the
        // other thing: hatching thrown across open water reads as scratches in the ink rather than
        // as rain, and that is what a rendered city ward looked like. So every stroke asks whether
        // it landed in the water and drops itself if it did.
        //
        // The reject happens AFTER the position is drawn, never instead of drawing it — a skipped
        // stroke must still consume its rolls or every seed's sky would change.
        bool Dry(float x, float y) => !OnWater(m, x, y, 0);
        void Wash(string col, float a) => P.Add(Rect(0, 0, W, H, col, null, 0, a));
        // A run of slanted strokes, thrown across the whole sheet: rain, snow on the wind, hail.
        // Every stroke is started far enough in that its far end still lands on the paper — line
        // ink past the edge shows up in the SVG viewBox and on the PDF page as a clipped stub.
        void Slant(int n, float len, float lean, string col, float sw, float a)
        {
            float dx = lean * len, spanX = Math.Max(1f, W - Math.Abs(dx)), spanY = Math.Max(1f, H - len);
            for (int i = 0; i < n; i++)
            {
                float x = (dx < 0 ? -dx : 0) + (float)rng.NextDouble() * spanX;
                float y = (float)rng.NextDouble() * spanY;
                if (!Dry(x + dx / 2, y + len / 2)) continue;
                P.Add(new Prim
                {
                    Kind = PrimKind.Line, Pts = new[] { x, y, x + dx, y + len },
                    Stroke = col, StrokeW = sw, Alpha = a
                });
            }
        }
        void Specks(int n, float r, string col, float a)
        {
            for (int i = 0; i < n; i++)
            {
                float sx = (float)rng.NextDouble() * W, sy = (float)rng.NextDouble() * H;
                float sr = r * (0.6f + (float)rng.NextDouble());
                if (!Dry(sx, sy)) continue;
                P.Add(new Prim { Kind = PrimKind.Circle, Pts = new[] { sx, sy, sr }, Fill = col, Alpha = a });
            }
        }
        // Long shallow curves — the shape wind and fog take on a surveyor's sheet. An Arc spans
        // ±rx across and rises ry above its center, so the center is kept that far off the edges.
        void Streaks(int n, float rx, float ry, string col, float sw, float a)
        {
            float spanX = Math.Max(1f, W - 2 * rx), spanY = Math.Max(1f, H - ry);
            for (int i = 0; i < n; i++)
                P.Add(new Prim
                {
                    Kind = PrimKind.Line, Alpha = a, Stroke = col, StrokeW = sw,
                    Pts = Arc(rx + (float)rng.NextDouble() * spanX, ry + (float)rng.NextDouble() * spanY, rx, ry)
                });
        }

        switch (w)
        {
            case 1:                                        // fair — a couple of high clouds, nothing more
                Streaks(3, 60, 7, "#ffffff", 6f, 0.30f);
                break;
            case 2:                                        // clear and hot — a bleaching glare, heat off the ground
                Wash("#ffe9a8", 0.13f);
                Streaks(9, 26, 3, "#ffffff", 2f, 0.28f);
                break;
            case 3:                                        // overcast — the light goes flat and grey
                Wash("#8b8f92", 0.17f);
                Streaks(6, 70, 9, "#e8e9e6", 9f, 0.22f);
                break;
            case 4:                                        // rain
                Wash("#6f7f8c", 0.16f);
                Slant(150, 11, 0.32f, "#8fa6b4", 1f, 0.5f);
                break;
            case 5:                                        // thunderstorm — heavier, and a fork out of it
                Wash("#4c5663", 0.24f);
                Slant(230, 14, 0.42f, "#7f96a6", 1.2f, 0.55f);
                float lx2 = W * (0.25f + (float)rng.NextDouble() * 0.5f);
                P.Add(new Prim
                {
                    Kind = PrimKind.Line, Stroke = "#f6f0c8", StrokeW = 2.6f, Alpha = 0.9f,
                    Pts = new[] { lx2, 20, lx2 - 16, H * 0.24f, lx2 + 10, H * 0.26f, lx2 - 12, H * 0.5f }
                });
                break;
            case 6:                                        // fog to the ground — banded, and it eats the distance
                Wash("#d8dcd8", 0.28f);
                for (int i = 0; i < 7; i++)
                {
                    float y = H * (0.1f + 0.12f * i);
                    P.Add(Rect(0, y, W, 20 + (float)rng.NextDouble() * 26, "#eef0ec", null, 0, 0.30f));
                }
                break;
            case 7:                                        // wind and blowing dust
                Wash("#c9a86a", 0.20f);
                Streaks(26, 90, 11, "#e6cd9c", 2.4f, 0.45f);
                Specks(40, 1.3f, "#a98c58", 0.5f);
                break;
            case 8:                                        // snow falling
                Wash("#e9eef2", 0.26f);
                Specks(200, 1.8f, "#ffffff", 0.85f);
                break;
            case 9:                                        // a blizzard — the map goes half-blind, which is the point,
                Wash("#eef3f6", 0.34f);                    // but only half: the Keeper still has to run off it
                Slant(200, 16, 0.75f, "#ffffff", 1.6f, 0.65f);
                Specks(220, 2.1f, "#ffffff", 0.85f);
                break;
            case 10:                                       // hail
                Wash("#7d8a92", 0.18f);
                Slant(90, 9, 0.5f, "#a9bcc6", 1f, 0.45f);
                Specks(110, 2.2f, "#f2f6f8", 0.9f);
                break;
            case 11:                                       // hard freeze — no weather falling, just the cold in the light
                Wash("#b9cede", 0.22f);
                Streaks(5, 80, 6, "#ffffff", 5f, 0.22f);
                break;
        }
    }

    static string ScaleLine(int s) => s switch
    {
        0 => "close work, counted in yards", 1 => "a homestead and its bounds",
        2 => "a county, a hard day's ride", 4 => "a few blocks, and what is under them",
        _ => "a territory, weeks on the trail"
    };
    static string GridLabel(int s) => s switch { 0 => "ten yards", 1 => "a furlong", 2 => "five miles", 4 => "two blocks", _ => "a day's ride" };

    // What a scattered city mark is, in a word — so the ward reads as a place with a depot and a
    // packing house, not a field of anonymous symbols.
    static string CitySymCaption(string sym) => sym switch
    {
        "stack" => "works", "depot" => "depot", "pens" => "pens",
        "church" => "chapel", "wharf" => "landing", _ => null
    };

    // ---------------------------------------------------------- names
    // The naming stock moved to Data/names.json and Names.cs on 2026-08-09. What lived here was
    // 24 title words, 16 x 16 town words and 10 landmark owners — small enough that the birthday
    // bound put the first repeat at about twenty draws, which is one campaign. It also drew every
    // name independently, so nothing stopped one sheet calling two things by the same word.
    // Namer is seeded, remembers what it spent, and varies title SHAPE as well as vocabulary.
    static readonly string[] SecretLines =
    {
        "something buried here", "it dens here", "they watch the trail", "old blood in the ground",
        "the ground is wrong", "an ambush waiting", "the door under the hill", "what the well keeps",
        "sign of the beast", "a cache — powder and coin"
    };

    /// <summary>The named places this ground can offer beyond the ones people build everywhere —
    /// its own landforms and the works that only belong in it. Drawn with the same symbols the
    /// country is furnished with, so a landmark called The Divide is a mountain range, not a dot.
    /// </summary>
    static (string sym, string noun)[] GroundLandmarks(int ti) => ti switch
    {
        0 => new[]                                         // the open range
        {
            ("hills", "Twin Buttes"), ("ridge", "The Hogback"), ("bluff", "The Breaks"),
            ("forest", "The Timber"), ("hill", "Signal Hill"), ("butte", "Lone Butte"),
            ("spring", "The Springs"), ("corral", "Line Camp"),
        },
        1 => new[]                                         // rivers, lakes & swamps
        {
            ("marsh", "The Sloughs"), ("forest", "Cypress Stand"), ("spring", "Boiling Spring"),
            ("wharf", "The Landing"), ("hill", "Island Mound"), ("marsh", "Drowned Ground"),
            ("deadtree", "Snag Bend"),
        },
        2 => new[]                                         // towns, homesteads & haunted houses
        {
            ("orchard", "The Orchard"), ("forest", "The Woodlot"), ("field", "The Home Place"),
            ("hills", "The Pastures"), ("spring", "Sweetwater"), ("fence", "The Section Line"),
            ("hill", "Schoolhouse Hill"),
        },
        3 => new[]                                         // graveyards & battlefields
        {
            ("mound", "The Burial Mound"), ("trench", "The Works"), ("hill", "The High Ground"),
            ("forest", "The Wood"), ("ridge", "The Sunken Road"), ("grave", "The Trench Graves"),
        },
        4 => new[]                                         // mines & under the earth
        {
            ("mountain", "The Peak"), ("hoodoo", "Cathedral Rock"), ("ridge", "The Lode"),
            ("bluff", "The Highwall"), ("hills", "The Dumps"), ("tailing", "The Tailings"),
            ("mine", "The Deep Shaft"), ("butte", "Chimney Rock"),
        },
        5 => new[]                                         // winter & the high country
        {
            ("range", "The Divide"), ("mountain", "Lonesome Peak"), ("bluff", "The Palisades"),
            ("pinestand", "The Pinery"), ("ridge", "Devil's Backbone"), ("hills", "The Saddle"),
            ("snowpeak", "The Notch"), ("pinestand", "Timber Camp"), ("mountain", "Bald Knob"),
        },
        6 => new[]                                         // desert & the badlands
        {
            ("butte", "Chimney Butte"), ("hoodoo", "The Goblins"), ("bluff", "The Wall"),
            ("mesa", "The Mesa"), ("ridge", "The Spine"), ("dune", "The Sand Hills"),
            ("spring", "The Tanks"), ("hills", "The Little Badlands"),
        },
        7 => new[]                                         // the old places
        {
            ("mound", "The Barrow"), ("hoodoo", "The Watcher"), ("forest", "The Old Wood"),
            ("hill", "The Sleeping Hill"), ("stone", "The Ring"), ("ridge", "The Long Wall"),
        },
        9 => new[]                                         // pinewoods & the deep timber
        {
            ("pinestand", "The Big Timber"), ("forest", "The Brakes"), ("ridge", "The Divide"),
            ("spring", "Cold Spring"), ("hill", "Lookout Knob"), ("deadtree", "The Burn"),
            ("hills", "The Knobs"), ("camp", "The Cutting"),
        },
        10 => new[]                                        // bayou, cypress & the delta
        {
            ("marsh", "The Bayou"), ("forest", "The Cypress Brake"), ("wharf", "The Landing"),
            ("mound", "Shell Mound"), ("marsh", "Black Water"), ("deadtree", "The Drowned Wood"),
            ("spring", "The Blue Hole"), ("soddy", "The Stilt House"),
        },
        11 => new[]                                        // canyon country & the mesas
        {
            ("butte", "Chimney Rock"), ("mesa", "The Mesa"), ("hoodoo", "The Sentinels"),
            ("bluff", "The Rim"), ("ruin", "The Cliff House"), ("ridge", "The Slot"),
            ("stone", "The Painted Wall"), ("spring", "The Seep"),
        },
        12 => new[]                                        // shortgrass & the staked plain
        {
            ("hills", "The Swells"), ("well", "The Dug Well"), ("windmill", "The Windmill"),
            ("bones", "The Bone Field"), ("ridge", "The Caprock"), ("spring", "Seep Spring"),
            ("hill", "Wagon Mound"), ("corral", "The Half-Way House"),
        },
        13 => new[]                                        // brush country & the border
        {
            ("scrub", "The Thicket"), ("ridge", "The Rimrock"), ("corral", "The Holding Pens"),
            ("spring", "The Tinaja"), ("mesa", "The Table"), ("bones", "The Dry Wash"),
            ("hills", "The Malpais"), ("ford", "The Crossing"),
        },
        14 => new[]                                        // salt flats & the alkali sink
        {
            ("dune", "The White Sands"), ("bones", "The Bone Playa"), ("spring", "The Bitter Spring"),
            ("butte", "The Needle"), ("bluff", "The Rim of the Sink"), ("ridge", "The Salt Ridge"),
            ("ruin", "The Borax Works"),
        },
        15 => new[]                                        // the gulf coast & the marshes
        {
            ("marsh", "The Salt Marsh"), ("wharf", "The Fish Camp"), ("dune", "The Barrier Sand"),
            ("mound", "The Shell Ridge"), ("forest", "The Live Oaks"), ("deadtree", "The Hurricane Wood"),
            ("reeds", "The Grass Flats"), ("church", "The Chapel on the Point"),
        },
        _ => Array.Empty<(string, string)>(),
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

            // ---- landforms (v1.19) ----
            // The country used to be hills, mesas and one snowy peak. A survey ought to be able
            // to say "mountains here, a bluff along there, and timber the whole north half."
            case "hills":                                  // a run of low swells, the far ones smaller
                P.Add(new Prim { Kind = PrimKind.Line, Pts = Arc(x - 8 * k, y + 2 * k, 11 * k, 5f * k), Stroke = Ink, StrokeW = 1.3f });
                P.Add(new Prim { Kind = PrimKind.Line, Pts = Arc(x + 7 * k, y + 2 * k, 13 * k, 6.5f * k), Stroke = Ink, StrokeW = 1.3f });
                P.Add(new Prim { Kind = PrimKind.Line, Pts = Arc(x - 1 * k, y - 3 * k, 9 * k, 4.5f * k), Stroke = Ink, StrokeW = 1f });
                break;
            case "mountain":                               // bare rock: a peak with a shadowed face
                Pl("#a89c86", Dark, 1.3f, -15, 8, -3, -14, 6, 0, 15, 8);
                Pl("#8d8271", null, 0, -3, -14, 6, 0, 1, 8, -3, 8);
                L(-3, -14, -8, 0, Dark, 0.7f); break;
            case "range":                                  // a whole range on the skyline, snow on top
                Pl("#a89c86", Dark, 1.2f, -20, 8, -12, -6, -5, 2, 2, -11, 10, 1, 15, -4, 20, 8);
                Pl("#eef1f2", null, 0, -12, -6, -8.5f, -1, -15.5f, -1);
                Pl("#eef1f2", null, 0, 2, -11, 6, -4, -2, -4);
                L(-12, -6, -16, 4, Dark, 0.6f); L(2, -11, -2, 2, Dark, 0.6f); break;
            case "bluff":                                  // an escarpment, hachured down the drop
                P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { x - 16 * k, y - 3 * k, x - 6 * k, y - 5 * k, x + 4 * k, y - 2 * k, x + 16 * k, y - 4 * k }, Stroke = Ink, StrokeW = 1.6f });
                for (float t = -15; t <= 15; t += 5) L(t, -4, t - 1, 3, Ink, 0.8f);
                break;
            case "ridge":                                  // a long spine, ticked on the steep side
                P.Add(new Prim { Kind = PrimKind.Line, Pts = new[] { x - 17 * k, y + 3 * k, x - 7 * k, y - 4 * k, x + 3 * k, y - 2 * k, x + 17 * k, y + 4 * k }, Stroke = Ink, StrokeW = 1.5f });
                for (float t = -14; t <= 14; t += 4.6f) L(t, 0, t + 1.5f, 5, Ink, 0.7f);
                break;
            case "butte":                                  // narrower and taller than a mesa
                Pl(Tan, Ink, 1.3f, -7, 8, -5, -12, 5, -12, 7, 8);
                L(-5, -12, -6.5f, 8, Ink, 0.7f); L(5, -12, 6.5f, 8, Ink, 0.7f); break;
            case "hoodoo":                                 // a balanced rock on its stem
                Pl("#b7ab93", Ink, 1.1f, -6, -8, 6, -8, 4, -12, -4, -12);
                Pl("#a99d85", Ink, 1f, -2.5f, -8, 2.5f, -8, 3.5f, 8, -3.5f, 8); break;
            case "forest":                                 // a stand of hardwood, five crowns deep
                foreach (var (dx, dy, r) in new[] { (-9f, 2f, 5f), (0f, 4f, 5.5f), (9f, 2f, 5f), (-4.5f, -4f, 5f), (4.5f, -4f, 5f) })
                { C(dx, dy + 1.5f, r, Green, PineGreen, 1f); }
                L(-9, 8, -9, 5, "#574433", 1.1f); L(0, 10, 0, 7, "#574433", 1.1f); L(9, 8, 9, 5, "#574433", 1.1f);
                break;
            case "pinestand":                              // timber: three firs shoulder to shoulder
                for (int i2 = -1; i2 <= 1; i2++)
                {
                    float ox = i2 * 8f, oy = i2 == 0 ? -2f : 1f;
                    Pl(PineGreen, "#46543e", 0.9f, ox, oy - 13, ox - 5.5f, oy + 2, ox + 5.5f, oy + 2);
                    L(ox, oy + 6, ox, oy + 1, "#574433", 1.3f);
                }
                break;
            case "marsh":                                  // standing water, drawn the surveyor's way
                for (int r4 = -1; r4 <= 1; r4++)
                {
                    float yy = r4 * 4.5f;
                    L(-11, yy, -4, yy, WaterEdge, 1.2f); L(0, yy, 7, yy, WaterEdge, 1.2f);
                }
                L(-7, -7, -7, -3, "#6c7c54", 1f); L(3, -7, 3, -3, "#6c7c54", 1f); break;
            case "orchard":                                // planted rows — settled country, and money
                for (int r5 = 0; r5 < 2; r5++)
                    for (int c5 = 0; c5 < 4; c5++)
                        C(-10.5f + c5 * 7, -4 + r5 * 8, 2.4f, Green, PineGreen, 0.8f);
                break;
            case "spring":                                 // water coming up out of the ground
                C(0, 0, 3.2f, WaterFill, WaterEdge, 1.3f);
                P.Add(new Prim { Kind = PrimKind.Line, Pts = Arc(x, y + 5 * k, 9 * k, 3 * k), Stroke = WaterEdge, StrokeW = 1f });
                P.Add(new Prim { Kind = PrimKind.Line, Pts = Arc(x, y + 8 * k, 13 * k, 4 * k), Stroke = WaterEdge, StrokeW = 0.8f });
                break;
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

    /// Move the whole settlement — street, roofs, church, name — to a new seat.
    public static void MoveTown(MapModel m, float nx, float ny)
    {
        if (m?.Town != null) MoveOne(m, m.Town, nx, ny);
    }

    static void MoveFeature(MapModel m, List<Landmark> list, int index, float nx, float ny)
    {
        if (index < 0 || index >= list.Count) return;
        MoveOne(m, list[index], nx, ny);
    }

    static void MoveOne(MapModel m, Landmark lm, float nx, float ny)
    {
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

    // The city key: a small paper panel in the free corner, one row per mark the ward
    // actually draws. Deterministic on purpose — a key that reshuffles between two draws
    // of the same survey would be worse than none.
    static void CityKey(List<Prim> P, float W, float H)
    {
        var rows = new (string sym, string label)[]
        {
            ("depot", "Depot & rail platform"),
            ("stack", "Works — a smelter, a packing house"),
            ("pens",  "Stockyards"),
            ("church","Church or cathedral"),
            ("wharf", "The levee — moorings"),
            ("lodge", "A lodge hall, a charity ward"),
        };
        float w = 236, h = 30 + rows.Length * 21;
        float x0 = W - w - 26, y0 = H - h - 26;
        P.Add(Rect(x0, y0, w, h, "#f2ecd8", Dark, 1.3f, 0.94f));
        P.Add(TextP(x0 + 12, y0 + 19, "THE KEY", 10.5f, Ink, bold: true));
        var still = new Random(0);
        for (int i = 0; i < rows.Length; i++)
        {
            float ry = y0 + 34 + i * 21;
            Sym(P, still, rows[i].sym, x0 + 24, ry + 2, 0.62f);
            P.Add(TextP(x0 + 44, ry + 6, rows[i].label, 9f, Ink));
        }
    }

    // ---------------------------------------------------------- water & seating
    /// How much dry ground a settlement wants around its seat before the water starts running
    /// through its streets: a gunfight map draws a whole main street, a wider map a cluster of roofs.
    public static float TownReach(int scale) => scale == 0 ? 110f : 46f;

    /// True when a spot of the given reach touches this map's river channel or its lake.
    public static bool OnWater(MapModel m, float x, float y, float pad)
    {
        if (m == null) return false;
        if (m.LakeR > 0 && Sq(m.LakeX - x) + Sq(m.LakeY - y) < Sq(m.LakeR + pad)) return true;
        float half = m.RiverHalf + pad;
        return RiverDistSq(m, x, y) < half * half;
    }

    /// <summary>Walk a line around a lake instead of straight across it.
    /// <para>A trail drawn edge to edge and a lake dropped on the same sheet had nothing to say to
    /// each other: on a rendered ward the trail entered the north shore and left the south, with no
    /// ford, no ferry and no acknowledgement that there was water there. Pushing every vertex that
    /// lands in the lake out to the shore bends the line round it, which is what a trail does in
    /// fact. It consumes no randomness, so the same seed still draws the same country.</para>
    /// <para>A RIVER is deliberately left alone: a trail crossing a river is a ford, and it earns a
    /// mark rather than a detour. See <see cref="MarkCrossings"/>.</para></summary>
    public static void SkirtLake(float[] pts, float lx, float ly, float lr, float margin)
    {
        if (pts == null || lr <= 0) return;
        float keep = lr + margin;
        for (int i = 0; i + 1 < pts.Length; i += 2)
        {
            float dx = pts[i] - lx, dy = pts[i + 1] - ly;
            float d = (float)Math.Sqrt(dx * dx + dy * dy);
            if (d >= keep) continue;
            if (d < 0.001f) { dx = 1; dy = 0; d = 1; }        // dead centre: any bearing will do
            pts[i] = lx + dx / d * keep;
            pts[i + 1] = ly + dy / d * keep;
        }
    }

    /// <summary>The runs of a country road that belong on the sheet.
    /// <para>On open country that is the whole line, clipped to the neatline. On a CITY WARD it is
    /// only the part outside the street grid: inside the grid the streets are the roads, already
    /// drawn, and a dashed trail inked across the roofs reads as neither a street nor a trail. So the
    /// highway comes in off the sheet edge, meets the ward, and stops — which is what a ward map of a
    /// real place shows. Four margin bands rather than one rectangle-complement: a line clipped twice
    /// at a corner paints the same ink twice and nobody can tell.</para></summary>
    static List<float[]> RoadRuns(float[] pts, (float x0, float y0, float x1, float y1) clip,
                                  bool ward, float W, float H)
    {
        if (!ward) return ClipPolyline(pts, clip.x0, clip.y0, clip.x1, clip.y1);
        var runs = new List<float[]>();
        var bands = new[]
        {
            (clip.x0, clip.y0, clip.x1, Math.Min(clip.y1, WardMargin)),          // north of the grid
            (clip.x0, Math.Max(clip.y0, H - WardMargin), clip.x1, clip.y1),      // south
            (clip.x0, clip.y0, Math.Min(clip.x1, WardMargin), clip.y1),          // west
            (Math.Max(clip.x0, W - WardMargin), clip.y0, clip.x1, clip.y1),      // east
        };
        foreach (var (x0, y0, x1, y1) in bands)
            if (x1 > x0 && y1 > y0) runs.AddRange(ClipPolyline(pts, x0, y0, x1, y1));
        return runs;
    }

    /// <summary>Stamp the surveyor's mark wherever a line crosses the river.
    /// <para>A trail or a rail inked straight over a river with nothing on it reads as a fault
    /// because it is one — the country does not let you walk across water because two strokes happen
    /// to overlap. This finds each place the line ENTERS the channel and puts there what would
    /// actually be there: a ford's pair of bank marks for a trail, a trestle's deck and piers for a
    /// rail. It is drawn after the water, so the mark sits on the blue rather than under it.</para>
    /// </summary>
    static void MarkCrossings(List<Prim> P, MapModel m, float[] pts, bool rail)
    {
        if (pts == null || m?.RiverPts == null || m.RiverHalf <= 0) return;
        float half = m.RiverHalf;
        bool wasWet = false;
        for (int i = 0; i + 3 < pts.Length; i += 2)
        {
            float ax = pts[i], ay = pts[i + 1], bx = pts[i + 2], by = pts[i + 3];
            float mx = (ax + bx) / 2, my = (ay + by) / 2;
            bool wet = RiverDistSq(m, mx, my) < half * half;
            if (wet && !wasWet)
            {
                float dx = bx - ax, dy = by - ay;
                float len = (float)Math.Sqrt(dx * dx + dy * dy);
                if (len < 0.5f) { wasWet = true; continue; }
                float nx = -dy / len, ny = dx / len;            // across the line of travel
                float reach = half + 4;
                if (rail)
                {
                    // A trestle: the deck carried across, and a pier at each bank.
                    P.Add(new Prim { Kind = PrimKind.Line, StrokeW = 3.4f, Stroke = "#4a4038",
                        Pts = new[] { mx - dx / len * reach, my - dy / len * reach,
                                      mx + dx / len * reach, my + dy / len * reach } });
                    for (int s = -1; s <= 1; s += 2)
                        P.Add(new Prim { Kind = PrimKind.Line, StrokeW = 1.2f, Stroke = "#4a4038",
                            Pts = new[] { mx + dx / len * reach * s - nx * 5, my + dy / len * reach * s - ny * 5,
                                          mx + dx / len * reach * s + nx * 5, my + dy / len * reach * s + ny * 5 } });
                }
                else
                {
                    // A ford: the two banks marked, and nothing between them, which is the point.
                    for (int s = -1; s <= 1; s += 2)
                        P.Add(new Prim { Kind = PrimKind.Line, StrokeW = 2f, Stroke = TrailBrown,
                            Pts = new[] { mx + dx / len * reach * s - nx * 6, my + dy / len * reach * s - ny * 6,
                                          mx + dx / len * reach * s + nx * 6, my + dy / len * reach * s + ny * 6 } });
                }
            }
            wasWet = wet;
        }
    }

    /// How far a spot stands from the nearest water — negative when it's standing in it.
    /// A map with no water at all answers with a large number rather than a special case.
    public static float WaterClearance(MapModel m, float x, float y)
    {
        float d = float.MaxValue;
        if (m == null) return 9999f;
        if (m.LakeR > 0) d = Math.Min(d, Dist(m.LakeX, m.LakeY, x, y) - m.LakeR);
        float rq = RiverDistSq(m, x, y);
        if (rq < float.MaxValue) d = Math.Min(d, (float)Math.Sqrt(rq) - m.RiverHalf);
        return d == float.MaxValue ? 9999f : d;
    }

    /// Squared distance from a spot to the river's CHANNEL — measured to the segments, not to the
    /// vertices. Vertex-only sampling was near enough while the meander's points sit ~40px apart and
    /// every caller passes a pad wider than that, but it was only near enough by luck: shrink the
    /// pad and a town could be seated mid-channel on a straight reach and called dry.
    /// Answers float.MaxValue when the map has no river at all.
    static float RiverDistSq(MapModel m, float x, float y) => PolyDistSq(m.RiverPts, x, y);

    /// How far a spot is from a drawn line, squared. The river's own version is this one; the ward's
    /// block test asks it of the rail as well, and both want a segment answer rather than a vertex one.
    static float PolyDistSq(float[] p, float x, float y)
    {
        if (p == null || p.Length < 2) return float.MaxValue;
        if (p.Length == 2) return Sq(p[0] - x) + Sq(p[1] - y);        // a one-point run
        float best = float.MaxValue;
        for (int i = 0; i + 3 < p.Length; i += 2)
            best = Math.Min(best, SegDistSq(x, y, p[i], p[i + 1], p[i + 2], p[i + 3]));
        return best;
    }

    static float SegDistSq(float px, float py, float ax, float ay, float bx, float by)
    {
        float dx = bx - ax, dy = by - ay;
        float len2 = dx * dx + dy * dy;
        if (len2 <= 1e-6f) return Sq(px - ax) + Sq(py - ay);          // a degenerate segment
        float t = Math.Clamp(((px - ax) * dx + (py - ay) * dy) / len2, 0f, 1f);
        return Sq(px - (ax + dx * t)) + Sq(py - (ay + dy * t));
    }

    /// The nearest dry seat to a spot, searched in widening rings so a town lands as close to
    /// where it was wanted as the water allows. A spot that's already dry doesn't move at all.
    /// A river laid across a gunfight map can leave nowhere truly dry — then this gives back the
    /// driest ground it found rather than refusing to answer.
    public static (float x, float y) DryGroundNear(MapModel m, float x, float y, float reach)
    {
        if (m == null || !OnWater(m, x, y, reach)) return (x, y);
        float loX = reach + 24, hiX = m.W - reach - 24;
        float loY = reach + 24, hiY = m.H - reach - 40;
        if (loX > hiX) { loX = hiX = m.W / 2f; }        // a reach wider than the paper: hold the middle
        if (loY > hiY) { loY = hiY = m.H / 2f; }
        var best = (x, y);
        float bestClear = WaterClearance(m, x, y);
        for (float rad = 28; rad <= 470; rad += 28)
            for (int i = 0; i < 16; i++)
            {
                double a = Math.PI * 2 * i / 16;
                float cx = Math.Clamp(x + (float)Math.Cos(a) * rad, loX, hiX);
                float cy = Math.Clamp(y + (float)Math.Sin(a) * rad, loY, hiY);
                if (!OnWater(m, cx, cy, reach)) return (cx, cy);
                float c = WaterClearance(m, cx, cy);
                if (c > bestClear) { bestClear = c; best = (cx, cy); }
            }
        return best;
    }

    // ---------------------------------------------------------- geometry helpers
    static float Sq(float v) => v * v;
    static float Dist(float ax, float ay, float bx, float by) => (float)Math.Sqrt(Sq(ax - bx) + Sq(ay - by));
    static float Lerp(Random rng, float a, float b) => a + (float)rng.NextDouble() * (b - a);
    static float[] Longest(List<float[]> runs)
    {
        float[] best = null;
        foreach (var r in runs) if (best == null || r.Length > best.Length) best = r;
        return best;
    }

    static Prim Rect(float x, float y, float w, float h, string fill, string stroke, float sw, float alpha = 1f) =>
        new() { Kind = PrimKind.Poly, Pts = new[] { x, y, x + w, y, x + w, y + h, x, y + h }, Fill = fill, Stroke = stroke, StrokeW = sw, Alpha = alpha };

    /// <summary>The Keeper's tactical markers, drawn as map primitives so an export can carry them:
    /// a filled dot per marker in its own ink, with the name beside it. Deliberately NOT produced by
    /// <see cref="Generate"/> — markers are session state, not survey ink, and redrawing the map must
    /// never move or lose one. The exporters take these as a separate overlay rather than having them
    /// appended to the model, so the map the Map tab is holding keeps exactly what the survey drew.</summary>
    public static List<Prim> MarkerPrims(IEnumerable<MapMarker> markers, float w, float h)
    {
        var list = new List<Prim>();
        if (markers == null) return list;
        const float r = 10f, fs = 11f;
        foreach (var mk in markers)
        {
            if (mk == null) continue;
            float x = Math.Clamp(mk.X, 0, w), y = Math.Clamp(mk.Y, 0, h);
            list.Add(new Prim
            { Kind = PrimKind.Circle, Pts = new[] { x, y, r }, Fill = MapInk.Hex(MapInk.Of(mk)), Stroke = Dark, StrokeW = 1.8f });
            if (string.IsNullOrWhiteSpace(mk.Label)) continue;
            // The label's backing is sized by estimate, not measurement: out here there's no font
            // to ask for metrics, and paper laid a little wide on paper costs nothing to look at.
            float tw = mk.Label.Length * fs * 0.55f + 7;
            list.Add(Rect(x + r + 3, y - fs * 0.72f, tw, fs * 1.34f, "#f4efdd", null, 0, 0.82f));
            list.Add(TextP(x + r + 6, y + fs * 0.36f, mk.Label, fs, Dark, bold: true));
        }
        return list;
    }

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

    // The map content's edge: the inner neatline, drawn at 15px inside the sheet with the outer
    // frame at 8px.
    const float ClipInset = 15f;

    /// <summary>The clip rectangle for a line of a given stroke width, so the INK lands on the
    /// neatline rather than the geometry.
    /// <para>This was a real fault and the old comment here denied it: clipping the polyline at
    /// <see cref="ClipInset"/> puts the last VERTEX on the neatline, and a round cap then paints
    /// half the stroke width further out. A river's edge stroke is 13px, so its cap reached 8.5px —
    /// on top of the outer frame at 8px — and a rendered city ward showed a blue stub sitting across
    /// the border. Pulling the clip in by half the stroke puts the cap's outer edge exactly on the
    /// neatline, which is where the ink was always supposed to stop.</para></summary>
    static (float x0, float y0, float x1, float y1) ClipFor(float w, float W, float H)
    {
        float d = ClipInset + w / 2f;
        return (d, d, W - d, H - d);
    }

    /// <summary>The widest the cartouche can be on this survey.
    /// <para>The box is <b>measured</b> from its own three lines when it is drawn — five hundred
    /// lines below here, after the sky and the name have been rolled. The keep-out that stops a
    /// landmark being planted under it therefore has to be computed HERE, from what is known: the
    /// scale, the hour and the ground are fixed by the spec, and the two that are not — the title
    /// and the weather — take their longest possible value.</para>
    /// <para>It used to be a typed circle at (170,&#160;70) r190, covering out to x&#160;=&#160;360
    /// against a box that reaches 466 once the weather joined the subtitle. A rendered ward printed
    /// <i>The Shanties</i> as <i>hanties</i> with the rest under the box. Measured furniture with a
    /// typed keep-out is the same fault as a typed count in prose, and this project already has a
    /// rule about that.</para></summary>
    static float CartoucheMaxWidth(MapSpec sp, int ti, bool city)
    {
        string of = city ? "the city ward of" : sp.Scale switch
        {
            0 => "the ground at", 1 => "the country about", 2 => "the county of", _ => "the territory of"
        };
        string ground = GroundWord(ti);
        // The sky is not rolled yet, so price the longest line it could produce.
        int widestSky = 0;
        for (int w = 0; w < Weathers.Length; w++) widestSky = Math.Max(widestSky, WeatherLine(w).Length);
        int subLen = ground.Length + ScaleLine(sp.Scale).Length + Times[sp.Time].Length + widestSky + 12;
        return Math.Max(280, Math.Max(MaxTitleChars * 12.5f + 40,
                                      Math.Max(subLen * 5.2f + 34, of.Length * 6.5f + 96)));
    }

    /// <summary>The longest map title the namer can hand back. A bound rather than a measurement,
    /// because the title is not drawn until long after the keep-out is needed — and the smoke suite
    /// asserts it against thousands of real draws, so it is a checked claim and not a guess.</summary>
    public const int MaxTitleChars = 34;

    /// <summary>What the cartouche's subtitle calls this ground. Lives here rather than inline in
    /// the cartouche because <see cref="CartoucheMaxWidth"/> has to price the same words.</summary>
    static string GroundWord(int ti) => ti switch
    {
        0 => "the open range", 1 => "the river bottoms", 2 => "settled country", 3 => "a field of the dead",
        4 => "mining country", 5 => "the high country", 6 => "the badlands",
        8 => "a city ward",
        9 => "deep timber", 10 => "the bayou country", 11 => "canyon country", 12 => "the shortgrass",
        13 => "the brush country", 14 => "the alkali flats", 15 => "the coast marshes",
        _ => "the old places"
    };

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

    /// <paramref name="overlay"/> is drawn last, over the finished survey — the Keeper's tactical
    /// markers, when the Map tab was asked to include them. Null means the map alone.
    public static string ToSvg(MapModel m, IEnumerable<Prim> overlay = null)
    {
        var sb = new StringBuilder();
        sb.Append($"<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 {m.W} {m.H}\" width=\"{m.W}\" height=\"{m.H}\" font-family=\"Georgia, 'Times New Roman', serif\">\n");
        sb.Append("<title>").Append(Xml(m.Title)).Append("</title>\n");
        foreach (var p in overlay == null ? m.P : m.P.Concat(overlay))
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
