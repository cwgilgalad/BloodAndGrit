namespace BloodAndGritKeeper;

static class Program
{
    [STAThread]
    static void Main()
    {
        // Two tiers of failure handling:
        //  - UI-thread exceptions (a locked clipboard, a bad paste, one misbehaving
        //    handler) are RECOVERABLE — report them and keep the table running.
        //    Killing the app here would also skip FormClosing and lose the autosave.
        //  - Truly unhandled exceptions are fatal — attempt an emergency save,
        //    write startup-error.txt beside the exe (or %TEMP%), then exit.
        AppDomain.CurrentDomain.UnhandledException += (s, e) => Crash(e.ExceptionObject as Exception);
        Application.ThreadException += (s, e) => Recoverable(e.Exception);

        try
        {
            Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
            ApplicationConfiguration.Initialize();
            Db.Load();
            Application.Run(new MainForm());
        }
        catch (Exception ex)
        {
            Crash(ex);
        }
    }

    static void Recoverable(Exception ex)
    {
        try
        {
            File.WriteAllText(Path.Combine(Path.GetTempPath(), "BloodAndGrit-last-error.txt"), ex?.ToString() ?? "(null)");
        }
        catch { }
        try
        {
            MessageBox.Show(
                "That action hit a snag:\r\n\r\n" + ex?.Message +
                "\r\n\r\nThe table is unharmed — you can keep playing.\r\n" +
                "(Details in %TEMP%\\BloodAndGrit-last-error.txt.)",
                "Blood & Grit — The Keeper's Table",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        catch { }
    }

    static void Crash(Exception ex)
    {
        // last-ditch: keep the Keeper's table state even when going down
        try
        {
            if (Application.OpenForms.Count > 0 && Application.OpenForms[0] is MainForm mf)
                mf.AutoSave();
        }
        catch { }
        string report =
            "Blood & Grit — The Keeper's Table: startup/runtime error\r\n" +
            $"Time: {DateTime.Now}\r\n" +
            $"BaseDirectory: {AppContext.BaseDirectory}\r\n" +
            $"CurrentDirectory: {Environment.CurrentDirectory}\r\n" +
            $"OS: {Environment.OSVersion}, 64-bit: {Environment.Is64BitProcess}\r\n" +
            $"Data folder exists: {Directory.Exists(Path.Combine(AppContext.BaseDirectory, "Data"))}\r\n\r\n" +
            ex;
        string path;
        try
        {
            path = Path.Combine(AppContext.BaseDirectory, "startup-error.txt");
            File.WriteAllText(path, report);
        }
        catch
        {
            path = Path.Combine(Path.GetTempPath(), "BloodAndGrit-startup-error.txt");
            try { File.WriteAllText(path, report); } catch { path = "(could not write log)"; }
        }
        try
        {
            MessageBox.Show(
                "The Keeper's Table hit a snag and had to stop.\r\n\r\n" +
                ex?.Message + "\r\n\r\nA full report was written to:\r\n" + path,
                "Blood & Grit — The Keeper's Table",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        catch { /* headless — nothing more we can do */ }
        Environment.Exit(1);
    }
}
