using System.Text;

namespace BloodAndGritKeeper;

// A tiny from-scratch PDF writer — no packages, nothing for the Keeper to install.
// Two products: a Letter-portrait text sheet (the New Soul export) and a Letter-
// landscape vector page (the map export, drawn from the same primitives as the
// screen and the SVG). Everything here is plain PDF 1.4: numbered objects, an
// xref table, uncompressed content streams — every byte is Latin-1, so offsets
// can be counted as characters.
public static class Pdf
{
    // ---------------------------------------------------------- assembly
    // objects[i] is the full body of object i+1 (dictionary or stream, without the
    // "n 0 obj"/"endobj" wrapper). Object 1 must be the Catalog.
    static byte[] Build(List<string> objects)
    {
        var sb = new StringBuilder("%PDF-1.4\n%âãÏÓ\n");
        var offs = new List<int>();
        for (int i = 0; i < objects.Count; i++)
        {
            offs.Add(sb.Length);
            sb.Append(i + 1).Append(" 0 obj\n").Append(objects[i]).Append("\nendobj\n");
        }
        int xref = sb.Length;
        sb.Append("xref\n0 ").Append(objects.Count + 1).Append("\n0000000000 65535 f \n");
        foreach (var o in offs) sb.Append(o.ToString("D10")).Append(" 00000 n \n");
        sb.Append("trailer\n<< /Size ").Append(objects.Count + 1)
          .Append(" /Root 1 0 R >>\nstartxref\n").Append(xref).Append("\n%%EOF");
        string s = sb.ToString();
        var bytes = new byte[s.Length];
        for (int k = 0; k < s.Length; k++) bytes[k] = (byte)(s[k] <= 255 ? s[k] : '?');
        return bytes;
    }

    static string Stream(string content) => $"<< /Length {content.Length} >>\nstream\n{content}\nendstream";

    static string Font(string baseFont) => $"<< /Type /Font /Subtype /Type1 /BaseFont /{baseFont} /Encoding /WinAnsiEncoding >>";

    // Escape a run of text for a PDF string literal, folding typography the books use
    // (em-dashes, curly quotes, bullets, the true minus) into WinAnsi code points so
    // the sheet prints exactly as it reads on screen.
    static string Esc(string s)
    {
        var sb = new StringBuilder(s.Length + 8);
        foreach (var ch in s)
        {
            char c = ch switch
            {
                '—' => (char)0x97, '–' => (char)0x96,           // — –
                '‘' => (char)0x91, '’' => (char)0x92,           // ‘ ’
                '“' => (char)0x93, '”' => (char)0x94,           // “ ”
                '•' => (char)0x95, '●' => (char)0x95,           // • ●
                '…' => (char)0x85, '†' => (char)0x86,           // … †
                '−' => '-', ' ' => ' ',                          // − nbsp
                '＋' => '+', '✕' => 'x', '⚠' => '!',        // ＋ ✕ ⚠
                _ => ch
            };
            if (c is '(' or ')' or '\\') { sb.Append('\\').Append(c); }
            else if (c < 32) sb.Append(' ');
            else if (c > 255) sb.Append('?');
            else sb.Append(c);
        }
        return sb.ToString();
    }

    static string N(double v) => v.ToString("0.##", System.Globalization.CultureInfo.InvariantCulture);

    // "#rrggbb" → "r g b" in 0–1 for rg/RG operators
    static string Rgb(string hex)
    {
        int r = Convert.ToInt32(hex.Substring(1, 2), 16),
            g = Convert.ToInt32(hex.Substring(3, 2), 16),
            b = Convert.ToInt32(hex.Substring(5, 2), 16);
        return $"{N(r / 255.0)} {N(g / 255.0)} {N(b / 255.0)}";
    }

    // ---------------------------------------------------------- the text sheet
    // A Letter-portrait document: serif title block, then the monospace sheet body.
    // ALL-CAPS section heads render bold and oxblood, so the printed page carries
    // the same structure the screen does.
    public static byte[] TextSheet(string title, string subtitle, string body)
    {
        const double pw = 612, ph = 792, margin = 54;
        const double bodySize = 9, lead = 11.6;
        const int wrap = 92;                          // Courier 9pt in a 504pt column

        // wrap long lines, keeping the sheet's own indentation on continuations
        var lines = new List<string>();
        foreach (var raw in (body ?? "").Replace("\r\n", "\n").Split('\n'))
        {
            string line = raw.TrimEnd();
            if (line.Length <= wrap) { lines.Add(line); continue; }
            string indent = new string(' ', Math.Min(line.Length - line.TrimStart().Length + 2, wrap / 2));
            string rest = line;
            bool first = true;
            while (rest.Length > wrap)
            {
                int cut = rest.LastIndexOf(' ', wrap);
                if (cut <= indent.Length) cut = wrap;
                lines.Add(rest[..cut].TrimEnd());
                rest = (first ? indent : indent) + rest[cut..].TrimStart();
                first = false;
            }
            lines.Add(rest);
        }
        while (lines.Count > 0 && lines[^1].Length == 0) lines.RemoveAt(lines.Count - 1);

        // paginate: the first page loses room to the title block
        double headerH = 64;
        int perFirst = (int)((ph - margin - headerH - margin - 18) / lead);
        int perRest = (int)((ph - margin - margin - 18) / lead);
        var pages = new List<List<string>>();
        for (int i = 0; i < lines.Count || pages.Count == 0;)
        {
            int take = Math.Min(pages.Count == 0 ? perFirst : perRest, lines.Count - i);
            pages.Add(lines.GetRange(i, Math.Max(0, take)));
            i += Math.Max(1, take);
        }

        // objects: 1 Catalog · 2 Pages · 3 Courier · 4 Courier-Bold · 5 Times-Bold ·
        // 6 Times-Italic · then per page: content stream, page
        var objs = new List<string>
        {
            "<< /Type /Catalog /Pages 2 0 R >>",
            "",                                           // patched below
            Font("Courier"), Font("Courier-Bold"), Font("Times-Bold"), Font("Times-Italic"),
        };
        var kids = new List<string>();
        string fonts = "/F1 3 0 R /F2 4 0 R /F3 5 0 R /F4 6 0 R";
        bool IsHead(string l) => l.Length > 2 && l == l.ToUpperInvariant() && l.Any(char.IsLetter) && !l.StartsWith(" ");

        for (int p = 0; p < pages.Count; p++)
        {
            var c = new StringBuilder();
            double y = ph - margin;
            if (p == 0)
            {
                c.Append($"BT /F3 16 Tf {Rgb("#781616")} rg {N(margin)} {N(y - 14)} Td ({Esc(title)}) Tj ET\n");
                if (!string.IsNullOrEmpty(subtitle))
                    c.Append($"BT /F4 10.5 Tf {Rgb("#967432")} rg {N(margin)} {N(y - 30)} Td ({Esc(subtitle)}) Tj ET\n");
                c.Append($"{Rgb("#781616")} RG 1.2 w {N(margin)} {N(y - 40)} m {N(pw - margin)} {N(y - 40)} l S\n");
                y -= headerH;
            }
            foreach (var line in pages[p])
            {
                y -= lead;
                if (line.Length == 0) continue;
                bool head = IsHead(line);
                c.Append($"BT /{(head ? "F2" : "F1")} {N(bodySize)} Tf {Rgb(head ? "#781616" : "#261c14")} rg ")
                 .Append($"{N(margin)} {N(y)} Td ({Esc(line)}) Tj ET\n");
            }
            c.Append($"BT /F4 8 Tf {Rgb("#8a7a5c")} rg {N(margin)} {N(margin - 18)} Td ")
             .Append($"({Esc($"GritKeeper — Blood & Grit  ·  page {p + 1} of {pages.Count}")}) Tj ET\n");

            objs.Add(Stream(c.ToString()));
            objs.Add($"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {N(pw)} {N(ph)}] " +
                     $"/Resources << /Font << {fonts} >> >> /Contents {objs.Count} 0 R >>");
            kids.Add($"{objs.Count} 0 R");
        }
        objs[1] = $"<< /Type /Pages /Kids [{string.Join(" ", kids)}] /Count {pages.Count} >>";
        return Build(objs);
    }

    // ---------------------------------------------------------- the map page
    // One landscape Letter page, the map's primitives replayed as PDF vector
    // operators — the same model the screen and the SVG render, so all three match.
    public static byte[] MapPdf(MapModel m)
    {
        const double pw = 792, ph = 612, margin = 22;
        double s = Math.Min((pw - 2 * margin) / m.W, (ph - 2 * margin) / m.H);
        double ox = (pw - m.W * s) / 2, oy = (ph - m.H * s) / 2;
        double X(double x) => ox + x * s;
        double Y(double y) => ph - oy - y * s;

        // shared alpha states (PDF opacity lives in ExtGState resources, not operators)
        var alphas = m.P.Where(p => p.Alpha < 0.999f).Select(p => Math.Round(p.Alpha, 3)).Distinct().OrderBy(a => a).ToList();
        string GsFor(float a) => alphas.IndexOf(Math.Round(a, 3)) is int i && i >= 0 ? $"/G{i} gs " : "";

        var c = new StringBuilder();
        const double k = 0.5523;                      // circle-by-Béziers constant
        foreach (var p in m.P)
        {
            string fill = p.Fill != null ? Rgb(p.Fill) + " rg " : "";
            string stroke = p.Stroke != null ? Rgb(p.Stroke) + " RG " + N(Math.Max(0.4, p.StrokeW * s)) + " w " : "";
            string dash = p.Dash != null
                ? "[" + string.Join(" ", p.Dash.Select(d => N(Math.Max(0.4, d * s)))) + "] 0 d "
                : "[] 0 d ";
            string paint = p.Fill != null && p.Stroke != null ? "B" : p.Fill != null ? "f" : "S";

            switch (p.Kind)
            {
                case PrimKind.Poly:
                case PrimKind.Line:
                    if (p.Pts.Length < 4) break;
                    c.Append("q ").Append(GsFor(p.Alpha)).Append(fill).Append(stroke).Append(dash);
                    c.Append(N(X(p.Pts[0]))).Append(' ').Append(N(Y(p.Pts[1]))).Append(" m ");
                    for (int i = 2; i + 1 < p.Pts.Length; i += 2)
                        c.Append(N(X(p.Pts[i]))).Append(' ').Append(N(Y(p.Pts[i + 1]))).Append(" l ");
                    if (p.Kind == PrimKind.Poly) c.Append("h ");
                    c.Append(p.Kind == PrimKind.Line && p.Fill == null ? "S" : paint).Append(" Q\n");
                    break;

                case PrimKind.Circle:
                {
                    double cx = X(p.Pts[0]), cy = Y(p.Pts[1]), r = p.Pts[2] * s, kr = k * r;
                    c.Append("q ").Append(GsFor(p.Alpha)).Append(fill).Append(stroke).Append(dash);
                    c.Append($"{N(cx + r)} {N(cy)} m ")
                     .Append($"{N(cx + r)} {N(cy + kr)} {N(cx + kr)} {N(cy + r)} {N(cx)} {N(cy + r)} c ")
                     .Append($"{N(cx - kr)} {N(cy + r)} {N(cx - r)} {N(cy + kr)} {N(cx - r)} {N(cy)} c ")
                     .Append($"{N(cx - r)} {N(cy - kr)} {N(cx - kr)} {N(cy - r)} {N(cx)} {N(cy - r)} c ")
                     .Append($"{N(cx + kr)} {N(cy - r)} {N(cx + r)} {N(cy - kr)} {N(cx + r)} {N(cy)} c h ")
                     .Append(paint).Append(" Q\n");
                    break;
                }

                case PrimKind.Text:
                {
                    string f = p.Bold ? "/F2" : p.Italic ? "/F4" : "/F5";
                    double size = p.FontSize * s;
                    double est = Esc(p.Text).Replace("\\", "").Length * size * (p.Bold ? 0.52 : 0.48);
                    double dx = p.Anchor == 1 ? -est / 2 : p.Anchor == 2 ? -est : 0;
                    c.Append("q ").Append(GsFor(p.Alpha))
                     .Append($"BT {f} {N(size)} Tf {Rgb(p.Fill ?? "#261c14")} rg ")
                     .Append($"{N(X(p.Pts[0]) + dx)} {N(Y(p.Pts[1]))} Td ({Esc(p.Text)}) Tj ET Q\n");
                    break;
                }
            }
        }

        var objs = new List<string>
        {
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [8 0 R] /Count 1 >>",
            Font("Times-Bold"), Font("Times-Italic"), Font("Times-Roman"),
            "<< " + string.Join(" ", alphas.Select((a, i) => $"/G{i} << /Type /ExtGState /ca {N(a)} /CA {N(a)} >>")) + " >>",
            Stream(c.ToString()),
        };
        objs.Add($"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {N(pw)} {N(ph)}] " +
                 "/Resources << /Font << /F2 3 0 R /F4 4 0 R /F5 5 0 R >> /ExtGState 6 0 R >> /Contents 7 0 R >>");
        return Build(objs);
    }
}
