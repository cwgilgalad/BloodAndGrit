using BloodAndGritKeeper;

// A throwaway visual check: write one SVG per sky and one per ground, so the new weather
// washes and the new landforms can be looked at rather than merely asserted. Not part of the
// suite's pass/fail — it just drops files where a human can open them.
static class WeatherSheets
{
    public static void Write(string dir)
    {
        Directory.CreateDirectory(dir);
        for (int w = 0; w < MapGen.Weathers.Length; w++)
        {
            var m = MapGen.Generate(new MapSpec
            { Terrain = "Winter & the High Country", Seed = 4242, Weather = w, Landmarks = 6, Secrets = false });
            File.WriteAllText(Path.Combine(dir, $"sky-{w:00}-{Slug(MapGen.Weathers[w])}.svg"), MapGen.ToSvg(m));
        }
        foreach (var t in MapGen.Terrains)
        {
            var m = MapGen.Generate(new MapSpec { Terrain = t, Seed = 909, Landmarks = 8 });
            File.WriteAllText(Path.Combine(dir, $"ground-{Slug(t)}.svg"), MapGen.ToSvg(m));
        }
    }

    static string Slug(string s)
    {
        var sb = new System.Text.StringBuilder();
        foreach (char c in s.ToLowerInvariant())
            sb.Append(char.IsLetterOrDigit(c) ? c : '-');
        return sb.ToString().Trim('-').Replace("---", "-").Replace("--", "-");
    }
}
