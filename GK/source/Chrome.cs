using System.Runtime.InteropServices;

namespace BloodAndGritKeeper;

/// <summary>The window frame — the title bar, its text, and the border around it.
///
/// <para>Everything inside a GritKeeper window is painted from the frontier palette: paper grounds,
/// blood headers, gold accents, an owner-drawn tab strip. The title bar was the one surface still
/// wearing whatever Windows handed it, which on this machine is white with black text, so every
/// window opened with a bright bar across the top of a warm page. Nothing about that reads as a
/// deliberate choice — it reads as the theme not being finished.</para>
///
/// <para>Windows 11 build 22000 and up will colour the caption for an app that asks
/// (<c>DWMWA_CAPTION_COLOR</c> and friends, documented on the Dwm API). Older Windows returns a
/// failing HRESULT and keeps its own bar, which is the correct outcome — this is decoration, and
/// decoration never gets to decide whether a window opens.</para></summary>
internal static class Chrome
{
    const int UseImmersiveDarkMode = 20, BorderColor = 34, CaptionColor = 35, TextColor = 36;

    /// The bar is Ink lifted just off black — pure Ink (38,28,20) against a bright desktop reads as
    /// a black bar rather than as a brown one, and the whole point is that it belongs to the paper.
    static readonly Color Caption = Color.FromArgb(46, 35, 26);

    [DllImport("dwmapi.dll")]
    static extern int DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int value, int size);

    /// COLORREF is 0x00BBGGRR — the reverse of the order every other Windows colour is written in,
    /// and the reason a caption tint comes out blue when it was meant to come out brown.
    static int Ref(Color c) => c.R | (c.G << 8) | (c.B << 16);

    static void Set(IntPtr h, int attr, int value)
    {
        try { DwmSetWindowAttribute(h, attr, ref value, sizeof(int)); }
        catch { /* pre-22000, or no dwmapi at all: the system bar stands, and that is fine */ }
    }

    /// <summary>Dress one window's frame. Safe to call on any handle and on any Windows.</summary>
    internal static void Apply(IWin32Window w)
    {
        if (w?.Handle is not { } h || h == IntPtr.Zero) return;
        // Dark mode first: it is what makes the system draw LIGHT close/minimise glyphs. Without it
        // a dark caption keeps black glyphs and the buttons vanish into the bar.
        Set(h, UseImmersiveDarkMode, 1);
        Set(h, CaptionColor, Ref(Caption));
        Set(h, TextColor, Ref(MainForm.Paper));
        Set(h, BorderColor, Ref(Caption));
    }
}

/// <summary>A Form that wears the app's frame. Every window in GritKeeper is built from this rather
/// than from <see cref="Form"/> directly — the main window, the pop-out creature cards and soul
/// Ledgers, and all twenty modal dialogs.
///
/// <para>It exists as a base class rather than as a call each window makes because the call is the
/// kind that gets forgotten: a dialog added a year from now would open with a white bar and nobody
/// would notice for a release or two. Inheriting it means the only way to get the frame wrong is to
/// deliberately write <c>Form</c>, and <c>audit_ui.py</c> counts these by name.</para></summary>
public class Sheet : Form
{
    protected override void OnHandleCreated(EventArgs e)
    {
        base.OnHandleCreated(e);
        Chrome.Apply(this);
    }

    /// <summary>Dress the contents, once, after they exist.
    ///
    /// <para>Load rather than the constructor or <c>OnHandleCreated</c>, because a dialog in this
    /// app is built the whole way — every control added — and only then shown, so Load is the first
    /// moment there is anything to walk. See <see cref="MainForm.DressControls"/> for what it does
    /// and why it is a walk rather than a rule about how to build a button.</para></summary>
    protected override void OnLoad(EventArgs e)
    {
        base.OnLoad(e);
        MainForm.DressControls(this);
    }
}
