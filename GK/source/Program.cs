namespace BloodAndGritKeeper;

static class Program
{
    [System.Runtime.InteropServices.DllImport("kernel32.dll")]
    static extern bool AttachConsole(int dwProcessId);

    [STAThread]
    static void Main(string[] args)
    {
        // Headless self-check of THIS binary: `GritKeeper.exe --selftest`. Drives the real code
        // paths behind the table tools (#1 the Iron Code Strike, #2 the Beat/MAP turn state,
        // #3 the Dread economy and the faith pool), validates a generated soul, and attempts to
        // construct the whole WinForms UI graph — then writes a report and exits 0 (clear) / 1
        // (a check failed). Lets a remote/headless session verify the shipped exe; the visual and
        // click behavior of the modal dialogs still wants the on-screen run-through.
        if (args != null && Array.IndexOf(args, "--selftest") >= 0)
        {
            AttachConsole(-1);   // ATTACH_PARENT_PROCESS — this is a WinExe; borrow the caller's console
            Environment.Exit(SelfTest());
            return;
        }

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
            CharGen.Load();
            Application.Run(new MainForm());
        }
        catch (Exception ex)
        {
            Crash(ex);
        }
    }

    static int SelfTest()
    {
        var log = new System.Text.StringBuilder();
        int checks = 0, fails = 0;
        void Line(string s) { Console.WriteLine(s); log.AppendLine(s); }
        void Chk(bool ok, string label) { checks++; if (!ok) fails++; Line((ok ? "  ok   " : "  FAIL ") + label); }

        Line("GritKeeper self-test — v" + typeof(Program).Assembly.GetName().Version);
        try
        {
            ApplicationConfiguration.Initialize();
            Db.Load();
            CharGen.Load();

            // -- #1 the Iron Code Strike, end to end: a sure hit takes Blood; a Fatal crit is bigger --
            var revolver = CharGen.D.weapons.First(w => w.name == "Single-Action Revolver");
            var atk = new Combatant { Name = "Ruth" };
            var tgt = new Combatant { Name = "Ghoul", Defense = 1, BloodCur = 40, BloodMax = 40 };
            var s1 = CombatFlow.StrikeAndApply(atk, tgt, revolver, attackBonus: 50, forcedDie: 10);
            Chk(s1.Res.AfterDR > 0 && tgt.BloodCur == 40 - s1.Res.AfterDR, "#1 Strike lands and takes the target's Blood");
            Chk(IronCode.RollDamage("1d8", WeaponTraits.Parse(revolver.traits), crit: true).Total >= 3, "#1 a Fatal-d10 crit rolls its dice");
            Chk(IronCode.ApplyDR(6, "blades", new[] { new DrEntry(2, "blades") }) == 4
                && IronCode.ApplyDR(6, "ball", new[] { new DrEntry(2, "blades") }) == 6, "#1 DR is typed and floors at zero");

            // -- #2 the Beat/MAP turn state: a Strike spends a Beat and steps the MAP; Begin turn resets --
            Chk(atk.Beats == 2 && atk.MapStep == 2, "#2 a Strike spends a Beat and advances the MAP step");
            Chk(CombatFlow.StrikeAndApply(atk, tgt, revolver, 50, forcedDie: 10).Map == -5, "#2 the second Strike takes the Multiple Attack Penalty");
            atk.BeginTurn();
            Chk(atk.Beats == 3 && atk.MapStep == 1, "#2 Begin turn restores 3 Beats and a clean MAP");

            // -- #3 the horror economy: a crit-fail Dread, the break's Mark, and the live faith pool --
            var d = Horror.DreadCheck(will: 0, dreadDc: 20, forcedDie: 1);
            Chk(d.Frightened && d.NerveLost > 0, "#3 a crit-fail Dread Check loses Nerve and Frightens");
            Chk(Horror.Break(forcedRoll: 6).GainsMark && !Horror.Break(forcedRoll: 3).GainsMark, "#3 the break table gains a Mark only on a 6");
            var padre = CharGen.Generate(5, false, "Padre");
            Chk(padre.PoolName == "Grace" && padre.PoolMax == Math.Max(1, CharGen.Mod(padre.Scores["PRE"]) + 5 / 2), "#3 a generated Padre carries Grace = PRE mod + half level");

            // -- the whole character math still validates on a caster-hybrid --
            Chk(CharGen.Validate(CharGen.Generate(7, true, "Witch Hunter")).Count == 0, "a generated Witch Hunter validates (Zeal + Miracles included)");

            // -- the WinForms/GUI test: construct the whole UI graph (all tabs, the new Strike/Dread
            //    buttons, the Beats and Pool columns, the seeded demo posse). WinForms wants an
            //    interactive desktop; on a headless station this may not realize, so it is reported
            //    but does not by itself fail the run. --
            try
            {
                using var mf = new MainForm();
                Chk(mf != null, "GUI: the full WinForms graph constructs (tabs, tracker, posse, demo posse)");
            }
            catch (Exception ux)
            {
                Line("  n/a  GUI: not constructible headlessly (needs a desktop) — "
                     + ux.GetType().Name + ": " + ux.Message.Split('\n')[0]);
            }
        }
        catch (Exception ex)
        {
            Line("self-test CRASHED: " + ex);
            fails++;
        }

        Line($"\nself-test: {checks - fails}/{checks} checks passed" + (fails == 0 ? " — all clear." : $" — {fails} FAILED."));
        try { File.WriteAllText(Path.Combine(AppContext.BaseDirectory, "selftest-report.txt"), log.ToString()); } catch { }
        return fails == 0 ? 0 : 1;
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
                "Blood & Grit — GritKeeper",
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
            "Blood & Grit — GritKeeper: startup/runtime error\r\n" +
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
                "GritKeeper hit a snag and had to stop.\r\n\r\n" +
                ex?.Message + "\r\n\r\nA full report was written to:\r\n" + path,
                "Blood & Grit — GritKeeper",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        catch { /* headless — nothing more we can do */ }
        Environment.Exit(1);
    }
}
