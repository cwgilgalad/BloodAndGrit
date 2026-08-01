namespace BloodAndGritKeeper;

public partial class MainForm
{
    // ============================================================ THE SOUL WIZARD
    // Chapter III's eight steps, walked by hand: the Keeper (or a player at their
    // shoulder) makes every choice the random generator would have rolled. Each pick
    // list is filtered to what the book allows, and the finished sheet goes through
    // CharGen.Assemble + Validate like any other.
    void RunSoulWizard()
    {
        using var wiz = new SoulWizard();
        if (wiz.ShowDialog(this) == DialogResult.OK && wiz.Result != null)
        {
            ShowSoul(wiz.Result);
            Log($"Soul built by hand: {wiz.Result.Name}, {wiz.Result.Calling} ({wiz.Result.Origin}), level {wiz.Result.Level}.");
        }
    }

    /// <summary>Self-test hook, the Reference deck's <see cref="BuildReferenceTab"/> pattern applied
    /// to the wizard: build every step that applies to this Calling and count them. Wizard pages are
    /// realized lazily — nothing else in the self-test would touch them, and a step that throws on
    /// construction is otherwise only found by a person clicking Next.
    /// <para>It also returns every control on those pages that carries no tooltip. The wizard's tips
    /// ARE its manual — a player meeting "Hedge Magic" has nothing else to go on — so a step added
    /// later with a bare ComboBox on it teaches nothing, and that silence is invisible at the table.
    /// Counting them here makes it a failing check instead of a thing somebody notices.</para></summary>
    internal static (int Pages, List<string> Untipped) BuildWizardStepsForSelfTest(string calling, string origin, int level)
    {
        using var wiz = new SoulWizard();
        int pages = wiz.RealizeEveryStep(calling, origin, level);
        return (pages, wiz.Untipped);
    }

    sealed class SoulWizard : Form
    {
        public CharacterSheet Result;

        // ---- collected choices (fields, so Back/Next never loses them) ----
        int level = 1;
        int methodIdx;                       // 0 array · 1 rolled · 2 by hand
        string charName = "", charGender = "";
        string calName, orgName, originChoice;
        List<int> pool = new();              // the six values to assign (array or rolled)
        readonly Dictionary<string, string> abilityPick = new();   // ability → chosen value (as string)
        readonly Dictionary<string, int> handScores = new();       // by-hand entry
        List<string> boostPicks = new();
        HashSet<string> skillPicks = new();
        List<string> increasePicks = new();
        List<string> edgePicks = new();
        List<string> gunPicks = new();
        HashSet<string> signPicks = new();
        string subpathPick, choicePick;
        double coinRolled = -1;
        readonly Dictionary<string, int> buyPicks = new();    // what's in the basket → how many of it
        string lost = "", seen = "", vice = "", moving = "", compass = "";

        static readonly string[] AbKeys = { "STR", "DEX", "CON", "WIT", "RES", "PRE" };
        static readonly string[] AbNames = { "Strength", "Dexterity", "Constitution", "Wits", "Resolve", "Presence" };
        const string LetBook = "(let the book pick)";

        CgCalling Cal => CharGen.D.callings.FirstOrDefault(c => c.name == calName);
        CgOrigin Org => CharGen.D.origins.FirstOrDefault(o => o.name == orgName);

        int step;
        readonly Label header;
        readonly Panel host;
        readonly Button back, next;

        (string title, Func<Control> build, Func<bool> collect, Func<bool> applicable)[] steps;

        public SoulWizard()
        {
            Text = "Build a soul — the wizard";
            Width = 780; Height = 680; MinimumSize = new Size(700, 560);
            StartPosition = FormStartPosition.CenterParent;
            MinimizeBox = false; ShowIcon = false; BackColor = Paper;

            header = new Label
            {
                Dock = DockStyle.Top, Height = 40, Font = new Font("Segoe UI", 12.5f, FontStyle.Bold),
                ForeColor = Blood, Padding = new Padding(14, 10, 0, 0), UseMnemonic = false
            };
            host = new Panel { Dock = DockStyle.Fill, Padding = new Padding(14, 4, 14, 4), AutoScroll = true };

            var bar = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 48, FlowDirection = FlowDirection.RightToLeft, Padding = new Padding(8) };
            var cancel = new Button { Text = "Cancel", Width = 88, Height = 32, DialogResult = DialogResult.Cancel };
            next = new Button { Text = "Next ▸", Width = 100, Height = 32 };
            back = new Button { Text = "◂ Back", Width = 88, Height = 32 };
            next.Click += (s, e) => GoNext();
            back.Click += (s, e) => GoBack();
            Tipped(next, "On to the next step. What this one asks for is checked first — anything the book insists on has to be settled before you move.");
            Tipped(back, "Back a step. Nothing you've chosen is lost; steps that don't apply to this soul are skipped over.");
            Tipped(cancel, "Close the wizard and build nothing.");
            bar.Controls.Add(cancel); bar.Controls.Add(next); bar.Controls.Add(back);
            Controls.Add(host); Controls.Add(header); Controls.Add(bar);
            CancelButton = cancel;

            steps = new (string, Func<Control>, Func<bool>, Func<bool>)[]
            {
                ("1 · Level, method & name",   BuildBasics,    CollectBasics,    () => true),
                ("2 · The Calling",            BuildCalling,   CollectCalling,   () => true),
                ("3 · The Origin",             BuildOrigin,    CollectOrigin,    () => true),
                ("4 · The six abilities",      BuildAbilities, CollectAbilities, () => true),
                ("5 · Skills",                 BuildSkills,    CollectSkills,    () => true),
                ("6 · Edges",                  BuildEdges,     CollectEdges,     () => true),
                ("7 · Signs & the path",       BuildSigns,     CollectSigns,     NeedsSignsStep),
                ("8 · Coin & outfit",          BuildOutfit,    CollectOutfit,    () => true),
                ("9 · The person",             BuildPerson,    CollectPerson,    () => true),
            };
            ShowStep(0);
        }

        /// Walk every applicable step's builder for the given soul. The choices are seeded
        /// directly rather than collected, because collect() is allowed to stop and ask the user
        /// a question and a self-test has nobody to answer it.
        internal int RealizeEveryStep(string calling, string origin, int lvl)
        {
            calName = calling; orgName = origin; level = lvl;
            int built = 0;
            for (int i = 0; i < steps.Length; i++)
                if (steps[i].applicable()) { ShowStep(i); built++; AuditStep(steps[i].title); }
            return built;
        }

        /// <summary>Controls on the realized steps that say nothing on hover, as "step · control".</summary>
        internal readonly List<string> Untipped = new();

        void AuditStep(string title) => WalkForTips(host, title, Untipped);

        void ShowStep(int i)
        {
            step = i;
            header.Text = steps[i].title;
            host.Controls.Clear();
            var c = steps[i].build();
            c.Dock = DockStyle.Top;
            host.Controls.Add(c);
            host.AutoScrollPosition = new Point(0, 0);
            back.Enabled = i > 0;
            next.Text = i == steps.Length - 1 ? "Finish ✓" : "Next ▸";
        }

        void GoNext()
        {
            if (!steps[step].collect()) return;
            int i = step + 1;
            while (i < steps.Length && !steps[i].applicable()) i++;
            if (i >= steps.Length) { Finish(); return; }
            ShowStep(i);
        }

        void GoBack()
        {
            steps[step].collect();          // keep what's set, even if incomplete
            int i = step - 1;
            while (i > 0 && !steps[i].applicable()) i--;
            ShowStep(Math.Max(0, i));
        }

        void Finish()
        {
            var spec = new CharGen.AssembleSpec
            {
                Level = level, Rolled = methodIdx != 0,
                Calling = calName, Origin = orgName, OriginSkillChoice = originChoice,
                TrainedPicks = skillPicks.ToList(),
                SkillIncreases = increasePicks.Where(x => x != LetBook).ToList(),
                Edges = edgePicks.Select(x => x == LetBook ? null : x).ToList(),
                BonusCombatEdges = gunPicks.Select(x => x == LetBook ? null : x).ToList(),
                Boosts = boostPicks,
                Signs = signPicks.ToList(),
                Subpath = subpathPick, CallingChoice = choicePick,
                CoinRolled = coinRolled > 0 ? coinRolled : null,
                // Assemble buys one entry at a time and prices each, so a count of three goes
                // down as the same name three times — which is also how the sheet stores it.
                BuyWeapons = buyPicks.Where(kv => CharGen.D.weapons.Any(w => w.name == kv.Key))
                                     .SelectMany(kv => Enumerable.Repeat(kv.Key, kv.Value)).ToList(),
                BuyGear = buyPicks.Where(kv => CharGen.D.gearPrices.ContainsKey(kv.Key))
                                  .SelectMany(kv => Enumerable.Repeat(kv.Key, kv.Value)).ToList(),
                Name = charName, Gender = charGender, Compass = compass,
                Lost = lost, Seen = seen, Vice = vice, Moving = moving,
                Look = look                                   // null draws one, like every line above
            };
            foreach (var a in AbKeys)
                spec.PreGiftScores[a] = methodIdx == 2
                    ? (handScores.TryGetValue(a, out var hv) ? hv : 10)
                    : int.Parse(abilityPick[a]);
            Result = CharGen.Assemble(spec);
            DialogResult = DialogResult.OK;
            Close();
        }

        // ---- shared little builders ----
        static Label Note(string t) => new()
        {
            Text = t, AutoSize = true, MaximumSize = new Size(690, 0),
            Font = new Font("Segoe UI", 9f, FontStyle.Italic), ForeColor = GoldDeep, Padding = new Padding(0, 4, 0, 6)
        };
        /// A bold caption. <paramref name="readout"/> marks one that carries a LIVE number rather
        /// than prose — the pool, the picked-of counts, the coin. Those are held to the same
        /// say-what-you-are standard as the controls; see <see cref="WantsTip"/>.
        static Label Cap(string t, bool readout = false) => new()
        {
            Text = t, AutoSize = true, Font = new Font("Segoe UI", 9.5f, FontStyle.Bold), ForeColor = Ink,
            Padding = new Padding(0, 8, 4, 2), Tag = readout ? "readout" : null
        };

        static FlowLayoutPanel Column() => new()
        { FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoSize = true, Padding = new Padding(2) };

        // ---- telling the player what a thing is ----
        // The wizard's lists are the book's own vocabulary, and a player meeting "Hedge Magic" or
        // "Salt & Iron" for the first time had nothing to go on but the name. Every list row and
        // every control now says what it is on hover, out of the same data the sheet is built
        // from, so a tip can never drift from the rule it describes. (User-asked, 2026-07-27.)
        static T Tipped<T>(T c, string tip) where T : Control
        { if (!string.IsNullOrEmpty(tip)) Tip.SetToolTip(c, Wrap(tip)); return c; }

        /// A tooltip is drawn as one long line unless it is broken by hand.
        static string Wrap(string t, int width = 84)
        {
            if (string.IsNullOrEmpty(t)) return t;
            var sb = new System.Text.StringBuilder();
            foreach (var para in t.Split('\n'))
            {
                int line = 0;
                foreach (var word in para.Split(' '))
                {
                    if (line > 0 && line + word.Length + 1 > width) { sb.Append('\n'); line = 0; }
                    else if (line > 0) { sb.Append(' '); line++; }
                    sb.Append(word); line += word.Length;
                }
                sb.Append('\n');
            }
            return sb.ToString().TrimEnd('\n');
        }

        /// Per-row tooltips for a ListBox or CheckedListBox. WinForms has none of its own, so
        /// follow the pointer and re-point the shared ToolTip whenever it crosses into a new row.
        ///
        /// <paramref name="resting"/> is what the list says when the pointer is NOT on a row — over
        /// the blank ground below the last item, or before it has moved at all. It used to be
        /// nothing, which made every list here the one thing on its step that explained itself only
        /// by accident: the rows described a Calling or a skill beautifully and the list never said
        /// what it wanted from you. That matters most on the two lists that REFUSE a click — tick
        /// past the cap, or past what the coin covers, and the tick simply doesn't take, with no
        /// word anywhere as to why. So the resting tip is the list's own instructions, and a row's
        /// tip is laid over it.
        static void ItemTips(ListBox lb, Func<int, string> textFor, string resting = null)
        {
            int shown = -2;
            string floor = Wrap(resting ?? "");
            Tip.SetToolTip(lb, floor);
            lb.MouseMove += (s, e) =>
            {
                int i = lb.IndexFromPoint(e.Location);
                if (i == shown) return;
                shown = i;
                Tip.SetToolTip(lb, i >= 0 && i < lb.Items.Count ? Wrap(textFor(i)) : floor);
            };
            lb.MouseLeave += (s, e) => { shown = -2; Tip.SetToolTip(lb, floor); };
        }

        // ---- the book's own words for each kind of thing, for the tips above ----
        static string SkillTip(CgSkill sk) =>
            $"{sk.name} — rolled on {sk.ability}. Trained adds your level to the roll; untrained is the bare ability modifier. "
          + "Expert and Master come later, from the skill increases at 3rd, 5th, 7th and 9th.";

        static string EdgeTip(string name)
        {
            var e = CharGen.EdgeByName(name);
            if (e == null) return name == LetBook ? "Leave this slot alone and the book deals it at the end, by the generator's own rules." : null;
            var req = new List<string>();
            if (e.reqAbility != null) req.AddRange(e.reqAbility.Select(kv => $"{kv.Key} {kv.Value}+"));
            if (e.reqEdge != null) req.Add("after " + e.reqEdge);
            if (e.reqTrained != null) req.Add("trained in " + e.reqTrained);
            if (e.calling != null) req.Add(e.calling + " only");
            return $"{e.name}  ({e.group})\n{e.desc}"
                 + (string.IsNullOrWhiteSpace(e.effect) ? "" : "\nEffect: " + e.effect)
                 + (req.Count > 0 ? "\nRequires: " + string.Join(", ", req) : "");
        }

        /// What each ability actually buys, in the book's terms — the six one-liners the sheet
        /// never has room for.
        static string AbilityTip(string key) => key switch
        {
            "STR" => "Strength — hauling, holding, and what a swung or thrust weapon does. Carries the Fortitude save's partner in a brawl.",
            "DEX" => "Dexterity — aim, balance and speed of hand. Sets Defense, Initiative, and what a gun hits with.",
            "CON" => "Constitution — wind and endurance. Sets the Fortitude save, and every level's Blood roll adds its modifier.",
            "WIT" => "Wits — sharpness and schooling. Adds to how many skills the Calling trains, and to noticing what is wrong with a room.",
            "RES" => "Resolve — nerve in the older sense. Sets the Will save, and Nerve itself is Resolve plus level — the stat the dark spends.",
            "PRE" => "Presence — bearing and force of person. Carries talking, leading, lying, and the Callings that work on people.",
            _ => key
        };

        static string SignTip(CgSign sg) =>
            $"{sg.name} — Rank {sg.rank}, on the {sg.list} list.\nCost: {sg.cost}\n{sg.desc}";

        // ============================================== 1 · basics
        NumericUpDown wLevel; ComboBox wMethod, wGender; TextBox wName;
        Control BuildBasics()
        {
            var col = Column();
            col.Controls.Add(Note("Every choice ahead is filtered to what the book allows. Anything left on \"" + LetBook + "\" is rolled for you at the end, by the same rules as the generator."));
            var row1 = new FlowLayoutPanel { AutoSize = true };
            row1.Controls.Add(Lbl("Level:"));
            wLevel = new NumericUpDown { Minimum = 1, Maximum = 10, Value = level, Width = 56, Margin = new Padding(3, 6, 3, 3) };
            Tipped(wLevel, "How experienced this soul already is. 1 is a fresh character; the wizard walks every "
                + "level up to this one, so a higher number means more Edges, more skill increases, more Blood — and more steps to answer. "
                + "Changing it clears the Edge, skill-increase, Sign and boost picks, since which of those you get depends on it.");
            row1.Controls.Add(wLevel);
            row1.Controls.Add(Lbl("   Abilities by:"));
            wMethod = new ComboBox { Width = 240, DropDownStyle = ComboBoxStyle.DropDownList };
            wMethod.Items.AddRange(new object[] { "The Honest Array (15 14 13 12 10 8)", "The Gamble (roll 4d6, drop lowest)", "Set the scores by hand" });
            wMethod.SelectedIndex = methodIdx;
            Tipped(wMethod, "How the six ability scores are found (Ch. III).\n"
                + "• The Honest Array — everyone gets the same six numbers to arrange. Fair, and no one is born unlucky.\n"
                + "• The Gamble — roll 4d6 and drop the lowest die, six times. Swingier; you may end up better or worse than the array.\n"
                + "• By hand — type the scores yourself. The sheet is still checked, but nothing stops you being generous.");
            row1.Controls.Add(wMethod);
            col.Controls.Add(row1);
            var row2 = new FlowLayoutPanel { AutoSize = true };
            row2.Controls.Add(Lbl("Name:"));
            wName = new TextBox { Width = 260, Text = charName, Margin = new Padding(3, 5, 3, 3) };
            Tipped(wName, "What they are called. Leave it blank and a frontier name is dealt at the end, matched to the gender if one is set.");
            row2.Controls.Add(wName);
            row2.Controls.Add(Lbl("  Gender:"));
            wGender = GenderBox(charGender);
            row2.Controls.Add(wGender);
            row2.Controls.Add(Btn("🎲", (s, e) =>
            {
                if (wGender.Text.Length == 0) wGender.Text = Rules.Rng.Next(2) == 0 ? "Woman" : "Man";
                string table = wGender.Text == "Woman" ? "givenWomen" : wGender.Text == "Man" ? "givenMen" : null;
                string given = table != null && CharGen.Flavor(table) is { Count: > 0 } l
                    ? l[Rules.Rng.Next(l.Count)] : Db.Pick("npcGiven");
                wName.Text = given + " " + Db.Pick("npcSurname");
            }, 40, "Deal a frontier name (matched to the gender, if one is set)"));
            row2.Controls.Add(Lbl("  (leave blank to roll at the end)"));
            col.Controls.Add(row2);
            return col;
        }
        bool CollectBasics()
        {
            int newLevel = (int)wLevel.Value; int newMethod = wMethod.SelectedIndex;
            if (newLevel != level) { increasePicks.Clear(); edgePicks.Clear(); gunPicks.Clear(); signPicks.Clear(); boostPicks.Clear(); }
            if (newMethod != methodIdx) { abilityPick.Clear(); pool.Clear(); }
            level = newLevel; methodIdx = newMethod; charName = wName.Text.Trim(); charGender = CharGen.CleanGender(wGender.Text);
            return true;
        }

        // ============================================== 2 · calling
        ListBox wCalList;
        Control BuildCalling()
        {
            var col = Column();
            col.Controls.Add(Note("Step 4 in the book, but chosen early here so every later list can honor its rules."));
            var row = new FlowLayoutPanel { AutoSize = true };
            wCalList = new ListBox { Width = 220, Height = 330, Font = new Font("Segoe UI", 9.5f) };
            foreach (var c in CharGen.D.callings.OrderBy(c => c.group).ThenBy(c => c.name)) wCalList.Items.Add(c.name);
            ItemTips(wCalList, i =>
            {
                var c = CharGen.D.callings.FirstOrDefault(x => x.name == (string)wCalList.Items[i]);
                if (c == null) return null;
                return $"{c.name} — a Calling of the {c.group}. Blood is rolled on a d{c.hitDie}; strong saves are {c.strongSaves}; "
                     + $"trains {c.trainedSkills} skills plus your WIT modifier; leans on {string.Join(", ", c.keyAbilities.Take(2))}."
                     + (c.signsKnownAt != null ? " Works the Signs of Ch. XIII." : "")
                     + (c.miracleLists != null ? " Works Miracles, paid from its own pool." : "")
                     + (c.bonusCombatEdgeAtOdd ? " Takes a bonus combat Edge at every odd level." : "")
                     + (c.startMark > 0 ? $" Begins already at Mark {c.startMark}." : "");
            },
            "What this soul does for a living — the single choice the rest of the sheet hangs off. It sets "
          + "the Hit Die that rolls Blood, which two saves are strong, how many skills are trained, and "
          + "whether they work Signs or Miracles at all. Grouped by the three kinds: the Worldly, the "
          + "Faithful, and the Old Dark.\nHover a name for its numbers; the panel to the right carries the "
          + "whole of it. Changing it later clears the picks that depended on it.");
            var detail = new Label { Width = 440, Height = 330, ForeColor = Ink, Font = new Font("Segoe UI", 9.5f) };
            wCalList.SelectedIndexChanged += (s, e) =>
            {
                var c = CharGen.D.callings.FirstOrDefault(x => x.name == (string)wCalList.SelectedItem);
                if (c == null) { detail.Text = ""; return; }
                detail.Text = $"{c.name} — a Calling of the {c.group}\n\n" +
                    $"Hit Die: d{c.hitDie}\nStrong saves: {c.strongSaves}\nTrained skills: {c.trainedSkills} + WIT modifier\n" +
                    $"Key abilities (in order): {string.Join(", ", c.keyAbilities)}\n" +
                    (c.signsKnownAt != null ? "Works the Signs.\n" : "") +
                    (c.bonusCombatEdgeAtOdd ? "Bonus combat Edge at every odd level.\n" : "") +
                    (c.startMark > 0 ? $"Begins at Mark {c.startMark}.\n" : "") +
                    (c.subpath != null ? $"\nAt 3rd level, chooses among the {c.subpath.section}:\n  {string.Join("\n  ", c.subpath.options.Select(o => o.name))}" : "");
            };
            wCalList.SelectedItem = calName ?? (string)null;
            if (wCalList.SelectedIndex < 0) wCalList.SelectedIndex = 0;
            row.Controls.Add(wCalList); row.Controls.Add(detail);
            col.Controls.Add(row);
            return col;
        }
        bool CollectCalling()
        {
            string picked = (string)wCalList.SelectedItem;
            if (picked != calName)
            { skillPicks.Clear(); increasePicks.Clear(); edgePicks.Clear(); gunPicks.Clear(); signPicks.Clear(); subpathPick = null; choicePick = null; coinRolled = -1; buyPicks.Clear(); abilityPick.Clear(); boostPicks.Clear(); }
            calName = picked;
            // Ch. IV: a Calling of Faith may not keep the Gambler origin
            if (Cal?.group == "Faith" && Org?.notFaith == true) orgName = null;
            return calName != null;
        }

        // ============================================== 3 · origin
        ListBox wOrgList; ComboBox wOrgChoice;
        Control BuildOrigin()
        {
            var col = Column();
            bool isFaith = Cal?.group == "Faith";
            col.Controls.Add(Note(isFaith
                ? "A soul sworn to the pulpit has no business at the green table — the Gambler is barred to Callings of Faith (Ch. IV)."
                : "Where they come from — gifts, free trained skills, a boon and a burden."));
            var row = new FlowLayoutPanel { AutoSize = true };
            wOrgList = new ListBox { Width = 220, Height = 300, Font = new Font("Segoe UI", 9.5f) };
            foreach (var o in CharGen.D.origins.Where(o => !(isFaith && o.notFaith))) wOrgList.Items.Add(o.name);
            ItemTips(wOrgList, i =>
            {
                var o = CharGen.D.origins.FirstOrDefault(x => x.name == (string)wOrgList.Items[i]);
                if (o == null) return null;
                return $"{o.name} — {o.line}\n"
                     + (o.gifts.Count > 0 ? "Gifts " + string.Join(", ", o.gifts.Select(kv => $"{kv.Key} +{kv.Value}")) + ". " : "")
                     + (o.trained.Count > 0 ? "Trained free in " + string.Join(", ", o.trained) + ". " : "")
                     + $"\nBoon: {o.boon}\nBurden: {o.burden}";
            },
            "Where they come from — the second half of who this is. An Origin gives ability points, trains "
          + "a skill or two free of the Calling's allowance, sometimes hands over gear, and always carries "
          + "one boon and one burden.\nHover a name for the whole of it. There is no wrong pick here: every "
          + "Origin goes with every Calling, save one — the Gambler is barred to the Callings of Faith.");
            var detail = new Label { Width = 440, Height = 300, ForeColor = Ink, Font = new Font("Segoe UI", 9.5f) };
            var choiceRow = new FlowLayoutPanel { AutoSize = true };
            choiceRow.Controls.Add(Lbl("Either/or skill:"));
            wOrgChoice = new ComboBox { Width = 220, DropDownStyle = ComboBoxStyle.DropDownList };
            Tipped(wOrgChoice, "This Origin trains one of these two, your pick — it comes free and does not count against the Calling's trained skills.");
            choiceRow.Controls.Add(wOrgChoice);
            wOrgList.SelectedIndexChanged += (s, e) =>
            {
                var o = CharGen.D.origins.FirstOrDefault(x => x.name == (string)wOrgList.SelectedItem);
                if (o == null) { detail.Text = ""; return; }
                detail.Text = $"{o.name}\n{o.line}\n\n" +
                    (o.gifts.Count > 0 ? "Gifts: " + string.Join(", ", o.gifts.Select(kv => $"{kv.Key} +{kv.Value}")) + "\n" : "") +
                    (o.trained.Count > 0 ? "Trained free: " + string.Join(", ", o.trained) + "\n" : "") +
                    (o.gear.Count > 0 ? "Comes with: " + string.Join(", ", o.gear) + "\n" : "") +
                    (o.startMark > 0 ? $"Begins at Mark {o.startMark}.\n" : "") +
                    $"\nBoon: {o.boon}\nBurden: {o.burden}";
                wOrgChoice.Items.Clear();
                foreach (var t in o.trainedChoice) wOrgChoice.Items.Add(t);
                choiceRow.Visible = o.trainedChoice.Count > 0;
                if (wOrgChoice.Items.Count > 0)
                    wOrgChoice.SelectedItem = o.trainedChoice.Contains(originChoice) ? originChoice : o.trainedChoice[0];
            };
            wOrgList.SelectedItem = orgName ?? (string)null;
            if (wOrgList.SelectedIndex < 0) wOrgList.SelectedIndex = 0;
            row.Controls.Add(wOrgList); row.Controls.Add(detail);
            col.Controls.Add(row);
            col.Controls.Add(choiceRow);
            return col;
        }
        bool CollectOrigin()
        {
            string picked = (string)wOrgList.SelectedItem;
            if (picked != orgName) { skillPicks.Clear(); abilityPick.Clear(); }
            orgName = picked;
            originChoice = wOrgChoice.SelectedItem as string;
            return orgName != null;
        }

        // ============================================== 4 · abilities
        readonly Dictionary<string, ComboBox> wAbCombos = new();
        readonly Dictionary<string, NumericUpDown> wAbNums = new();
        readonly List<ComboBox> wBoostCombos = new();
        Label wPoolLbl;
        Control BuildAbilities()
        {
            var col = Column();
            wAbCombos.Clear(); wAbNums.Clear(); wBoostCombos.Clear();

            if (methodIdx == 2)
            {
                col.Controls.Add(Note("Set each score by hand, 3–18. The sheet is checked as a rolled character."));
                for (int i = 0; i < 6; i++)
                {
                    var row = new FlowLayoutPanel { AutoSize = true };
                    row.Controls.Add(Lbl(AbNames[i] + $" ({AbKeys[i]}):", 150));
                    var n = new NumericUpDown { Minimum = 3, Maximum = 18, Width = 60, Value = handScores.TryGetValue(AbKeys[i], out var v) ? Math.Clamp(v, 3, 18) : 10, Margin = new Padding(3, 5, 3, 3) };
                    Tipped(n, AbilityTip(AbKeys[i]) + "\n10–11 is an ordinary person; every 2 points above or below moves the modifier by 1.");
                    wAbNums[AbKeys[i]] = n;
                    row.Controls.Add(n);
                    var gift = Org?.gifts.TryGetValue(AbKeys[i], out var g) == true ? g : 0;
                    if (gift > 0) row.Controls.Add(Lbl($"  +{gift} Origin gift"));
                    col.Controls.Add(row);
                }
            }
            else
            {
                if (methodIdx == 0) pool = new(CharGen.D.honestArray);
                if (methodIdx == 1 && pool.Count != 6)
                {
                    pool = new();
                    for (int i = 0; i < 6; i++)
                    {
                        var d = Enumerable.Range(0, 4).Select(_ => Rules.Rng.Next(1, 7)).OrderBy(x => x).ToList();
                        pool.Add(d[1] + d[2] + d[3]);
                    }
                    pool = pool.OrderByDescending(x => x).ToList();
                    abilityPick.Clear();
                }
                wPoolLbl = Tipped(Cap("The pool:  " + string.Join("  ", pool), readout: true),
                    "The six numbers this soul has to spend, before the Origin's gifts are added on top. "
                  + (methodIdx == 0
                        ? "The Honest Array — the same six for everybody, so nobody is born unlucky."
                        : "Rolled 4d6 and dropped the lowest die, six times, and sorted highest first. Re-roll "
                        + "above if the dice were unkind; that clears what you have assigned.")
                  + "\nAssign each one to an ability below. All six must be used, and a value that appears "
                  + "twice must be assigned twice.");
                col.Controls.Add(wPoolLbl);
                var noteRow = new FlowLayoutPanel { AutoSize = true };
                if (methodIdx == 1)
                    noteRow.Controls.Add(Btn("🎲 Re-roll the pool", (s, e) =>
                    {
                        pool = new();
                        for (int i = 0; i < 6; i++)
                        {
                            var d = Enumerable.Range(0, 4).Select(_ => Rules.Rng.Next(1, 7)).OrderBy(x => x).ToList();
                            pool.Add(d[1] + d[2] + d[3]);
                        }
                        pool = pool.OrderByDescending(x => x).ToList();
                        abilityPick.Clear();
                        ShowStep(step);                      // rebuild with the fresh pool
                    }, 140, "Roll six fresh scores (4d6 drop lowest)"));
                noteRow.Controls.Add(Btn("Suggest", (s, e) =>
                {
                    var sorted = pool.OrderByDescending(x => x).ToList();
                    for (int i = 0; i < 6; i++) wAbCombos[Cal.keyAbilities[i]].SelectedItem = sorted[i].ToString();
                }, 90, "Assign the pool by the Calling's own priorities"));
                col.Controls.Add(noteRow);
                col.Controls.Add(Note("Give each ability one value from the pool — every value used exactly as often as it appears."));
                foreach (var (key, name) in AbKeys.Zip(AbNames))
                {
                    var row = new FlowLayoutPanel { AutoSize = true };
                    row.Controls.Add(Lbl(name + $" ({key}):", 150));
                    var cb = new ComboBox { Width = 70, DropDownStyle = ComboBoxStyle.DropDownList, Margin = new Padding(3, 5, 3, 3) };
                    foreach (var v in pool.Distinct().OrderByDescending(x => x)) cb.Items.Add(v.ToString());
                    if (abilityPick.TryGetValue(key, out var prev)) cb.SelectedItem = prev;
                    Tipped(cb, AbilityTip(key) + "\nGive it one value from the pool — every value must be used exactly as often as it appears.");
                    wAbCombos[key] = cb;
                    row.Controls.Add(cb);
                    var gift = Org?.gifts.TryGetValue(key, out var g) == true ? g : 0;
                    if (gift > 0) row.Controls.Add(Lbl($"  +{gift} Origin gift"));
                    col.Controls.Add(row);
                }
            }

            // the 5th/10th-level boosts, if the level reaches them
            var boostLevels = new[] { 5, 10 }.Where(l => l <= level).ToList();
            if (boostLevels.Count > 0)
            {
                col.Controls.Add(Cap("Ability boosts (+1)"));
                for (int i = 0; i < boostLevels.Count; i++)
                {
                    var row = new FlowLayoutPanel { AutoSize = true };
                    row.Controls.Add(Lbl($"At {boostLevels[i]}th level:", 150));
                    var cb = new ComboBox { Width = 130, DropDownStyle = ComboBoxStyle.DropDownList, Margin = new Padding(3, 5, 3, 3) };
                    cb.Items.AddRange(AbKeys.Cast<object>().ToArray());
                    cb.SelectedItem = i < boostPicks.Count ? boostPicks[i] : Cal.keyAbilities[0];
                    Tipped(cb, $"At {boostLevels[i]}th level one ability rises by 1. Worth spending on an odd score — it is the even numbers "
                        + "that move the modifier. Everything derived from it (Defense, saves, Nerve, Blood) is re-reckoned for you.");
                    wBoostCombos.Add(cb);
                    row.Controls.Add(cb);
                    col.Controls.Add(row);
                }
            }
            return col;
        }
        bool CollectAbilities()
        {
            if (methodIdx == 2)
            {
                foreach (var kv in wAbNums) handScores[kv.Key] = (int)kv.Value.Value;
            }
            else
            {
                var chosen = new List<int>();
                foreach (var key in AbKeys)
                {
                    if (wAbCombos[key].SelectedItem is not string v)
                    { MessageBox.Show("Give every ability a value from the pool.", "The wizard", MessageBoxButtons.OK, MessageBoxIcon.Information); return false; }
                    chosen.Add(int.Parse(v));
                }
                if (!chosen.OrderBy(x => x).SequenceEqual(pool.OrderBy(x => x)))
                { MessageBox.Show("Each pool value must be used exactly as often as it appears — the six picks must be the pool itself.", "The wizard", MessageBoxButtons.OK, MessageBoxIcon.Information); return false; }
                abilityPick.Clear();
                foreach (var key in AbKeys) abilityPick[key] = (string)wAbCombos[key].SelectedItem;
            }
            boostPicks = wBoostCombos.Select(cb => (string)cb.SelectedItem).ToList();
            return true;
        }

        int WitMod()
        {
            int wit = methodIdx == 2 ? (handScores.TryGetValue("WIT", out var h) ? h : 10)
                    : abilityPick.TryGetValue("WIT", out var v) ? int.Parse(v) : 10;
            wit += Org?.gifts.TryGetValue("WIT", out var g) == true ? g : 0;
            return CharGen.Mod(wit);
        }
        int TrainCount() => Math.Max(1, (Cal?.trainedSkills ?? 2) + WitMod());

        // the sheet as it stands mid-wizard, for edge-eligibility checks
        CharacterSheet ScratchSheet()
        {
            var t = new CharacterSheet { Level = level, Calling = calName, Origin = orgName };
            foreach (var a in AbKeys)
            {
                int pre = methodIdx == 2 ? (handScores.TryGetValue(a, out var h) ? h : 10)
                        : abilityPick.TryGetValue(a, out var v) ? int.Parse(v) : 10;
                int gift = Org?.gifts.TryGetValue(a, out var g) == true ? g : 0;
                t.Scores[a] = pre + gift;
            }
            for (int i = 0; i < boostPicks.Count; i++) if (AbKeys.Contains(boostPicks[i])) t.Scores[boostPicks[i]] += 1;
            foreach (var sk in skillPicks) t.SkillRanks[sk] = 1;
            foreach (var sk in Org?.trained ?? new()) t.SkillRanks[sk] = 1;
            if (originChoice != null) t.SkillRanks[originChoice] = 1;
            t.Features = Cal?.rows.Where(r => r.level <= level).SelectMany(r => r.features)
                .Where(f => f != "Edge" && !f.StartsWith("Sign learned") && !f.StartsWith("Stolen Wonder")).ToList() ?? new();
            return t;
        }

        // ============================================== 5 · skills
        CheckedListBox wSkillList; Label wSkillCount; readonly List<ComboBox> wIncCombos = new();
        Control BuildSkills()
        {
            var col = Column();
            wIncCombos.Clear();
            var free = new List<string>(Org?.trained ?? new());
            if (originChoice != null) free.Add(originChoice);
            int count = TrainCount();
            col.Controls.Add(Note($"The {calName} trains {count} skill(s) — the Calling's {Cal.trainedSkills} plus your WIT modifier ({WitMod():+0;−0})." +
                (free.Count > 0 ? $"  The Origin's own — {string.Join(", ", free)} — come free." : "")));
            wSkillCount = Tipped(Cap("", readout: true),
                $"How many of the {count} trained skills you have ticked. It must read {count} of {count} "
              + "before the wizard will move on — this is the one step in the book with an exact number "
              + "rather than an allowance.");
            col.Controls.Add(wSkillCount);
            wSkillList = new CheckedListBox { Width = 340, Height = 300, CheckOnClick = true, Font = new Font("Segoe UI", 9.5f) };
            var shelf = new List<CgSkill>();
            foreach (var sk in CharGen.D.skills)
            {
                if (free.Contains(sk.name)) continue;
                shelf.Add(sk);
                int idx = wSkillList.Items.Add($"{sk.name} ({sk.ability})");
                if (skillPicks.Contains(sk.name)) wSkillList.SetItemChecked(idx, true);
            }
            ItemTips(wSkillList, i => SkillTip(shelf[i]),
                $"The skills this soul is trained in — tick exactly {count}, no more. Trained means you add "
              + "your whole level to the roll; untrained is the bare ability modifier and nothing else.\n"
              + "The count is watched: once you have ticked all " + count + ", a further tick will not take. "
              + "Untick something first. Anything the Origin trains free is already off this list.\n"
              + "Hover a line for which ability rolls it.");
            void Refresh() => wSkillCount.Text = $"Picked {wSkillList.CheckedItems.Count} of {count}";
            wSkillList.ItemCheck += (s, e) =>
            {
                int after = wSkillList.CheckedItems.Count + (e.NewValue == CheckState.Checked ? 1 : -1);
                if (after > count) { e.NewValue = CheckState.Unchecked; }
                BeginInvoke(Refresh);
            };
            Refresh();
            col.Controls.Add(wSkillList);

            int increases = new[] { 3, 5, 7, 9 }.Count(l => l <= level);
            if (increases > 0)
            {
                col.Controls.Add(Cap("Skill increases"));
                col.Controls.Add(Note("One step each at 3rd, 5th, 7th and 9th: train something new, step a trained skill to Expert, or (from 7th) an Expert one to Master. An impossible pick is re-drawn by the book."));
                var levels = new[] { 3, 5, 7, 9 }.Where(l => l <= level).ToList();
                for (int i = 0; i < increases; i++)
                {
                    var row = new FlowLayoutPanel { AutoSize = true };
                    row.Controls.Add(Lbl($"At {levels[i]}th:", 70));
                    var cb = new ComboBox { Width = 220, DropDownStyle = ComboBoxStyle.DropDownList, Margin = new Padding(3, 5, 3, 3) };
                    cb.Items.Add(LetBook);
                    foreach (var sk in CharGen.D.skills) cb.Items.Add(sk.name);
                    cb.SelectedItem = i < increasePicks.Count && cb.Items.Contains(increasePicks[i]) ? increasePicks[i] : LetBook;
                    Tipped(cb, $"The step earned at {levels[i]}th level. Name an untrained skill to train it, a trained one to make it Expert, "
                        + "or (from 7th) an Expert one to make it Master. If the pick turns out to be impossible on this sheet, the book re-draws it.");
                    wIncCombos.Add(cb);
                    row.Controls.Add(cb);
                    col.Controls.Add(row);
                }
            }
            return col;
        }
        bool CollectSkills()
        {
            int count = TrainCount();
            if (wSkillList.CheckedItems.Count != count)
            { MessageBox.Show($"Pick exactly {count} trained skill(s).", "The wizard", MessageBoxButtons.OK, MessageBoxIcon.Information); return false; }
            skillPicks = wSkillList.CheckedItems.Cast<string>()
                .Select(x => x.Substring(0, x.LastIndexOf(" ("))).ToHashSet();
            increasePicks = wIncCombos.Select(cb => (string)cb.SelectedItem).ToList();
            return true;
        }

        // ============================================== 6 · edges
        readonly List<ComboBox> wEdgeCombos = new(); readonly List<ComboBox> wGunCombos = new();
        Label wEdgeDetail;
        Control BuildEdges()
        {
            var col = Column();
            wEdgeCombos.Clear(); wGunCombos.Clear();
            var levels = new[] { 1, 3, 5, 7, 9 }.Where(l => l <= level).ToList();
            col.Controls.Add(Note($"An Edge at 1st and each odd level — {levels.Count} in all" +
                (Cal.bonusCombatEdgeAtOdd ? ", and the Gunhand's bonus combat Edge beside each" : "") +
                ". Each list shows only what's legal given everything picked so far; later slots re-check as earlier ones change."));
            wEdgeDetail = new Label { AutoSize = true, MaximumSize = new Size(690, 0), ForeColor = Ink, Font = new Font("Segoe UI", 9f), Padding = new Padding(0, 6, 0, 0) };

            bool refilling = false;
            void RefillAll()
            {
                if (refilling) return;                       // combos refill each other — no echoes
                refilling = true;
                try { RefillCore(); } finally { refilling = false; }
            }
            void RefillCore()
            {
                var scratch = ScratchSheet();
                for (int i = 0; i < wEdgeCombos.Count; i++)
                {
                    // owned = every pick in earlier slots (both lists), so options stay legal in order
                    scratch.Edges = wEdgeCombos.Take(i).Select(cb => (string)cb.SelectedItem).Where(x => x != null && x != LetBook).ToList();
                    scratch.BonusCombatEdges = wGunCombos.Take(i).Select(cb => (string)cb.SelectedItem).Where(x => x != null && x != LetBook).ToList();
                    Refill(wEdgeCombos[i], CharGen.EligibleEdges(scratch));
                    if (i < wGunCombos.Count)
                    {
                        scratch.Edges = wEdgeCombos.Take(i + 1).Select(cb => (string)cb.SelectedItem).Where(x => x != null && x != LetBook).ToList();
                        Refill(wGunCombos[i], CharGen.EligibleEdges(scratch, "Gun"));
                    }
                }
            }
            void Refill(ComboBox cb, List<string> options)
            {
                string keep = cb.SelectedItem as string;
                cb.Items.Clear();
                cb.Items.Add(LetBook);
                foreach (var o in options) cb.Items.Add(o);
                cb.SelectedItem = keep != null && cb.Items.Contains(keep) ? keep : LetBook;
            }
            ComboBox MakeCombo(List<string> prior, int idx)
            {
                var cb = new ComboBox { Width = 260, DropDownStyle = ComboBoxStyle.DropDownList, Margin = new Padding(3, 5, 3, 3) };
                cb.Items.Add(LetBook);
                if (idx < prior.Count && prior[idx] != null) { cb.Items.Add(prior[idx]); cb.SelectedItem = prior[idx]; }
                else cb.SelectedIndex = 0;
                cb.SelectedIndexChanged += (s, e) =>
                {
                    var edge = CharGen.EdgeByName(cb.SelectedItem as string);
                    wEdgeDetail.Text = edge != null ? $"{edge.name} — {edge.desc}" : "";
                    // the tip carries what the detail line leaves out — the effect and the requirements
                    Tip.SetToolTip(cb, Wrap(EdgeTip(cb.SelectedItem as string) ?? ""));
                    RefillAll();
                };
                cb.DropDown += (s, e) => RefillAll();
                Tip.SetToolTip(cb, Wrap(EdgeTip(cb.SelectedItem as string) ?? ""));
                return cb;
            }

            for (int i = 0; i < levels.Count; i++)
            {
                var row = new FlowLayoutPanel { AutoSize = true };
                row.Controls.Add(Lbl($"At {levels[i]}{(levels[i] == 1 ? "st" : levels[i] == 3 ? "rd" : "th")}:", 70));
                var cb = MakeCombo(edgePicks, i);
                wEdgeCombos.Add(cb);
                row.Controls.Add(cb);
                if (Cal.bonusCombatEdgeAtOdd)
                {
                    row.Controls.Add(Lbl("  Gunhand's:"));
                    var gcb = MakeCombo(gunPicks, i);
                    wGunCombos.Add(gcb);
                    row.Controls.Add(gcb);
                }
                col.Controls.Add(row);
            }
            RefillAll();
            col.Controls.Add(wEdgeDetail);
            return col;
        }
        bool CollectEdges()
        {
            edgePicks = wEdgeCombos.Select(cb => (string)cb.SelectedItem).ToList();
            gunPicks = wGunCombos.Select(cb => (string)cb.SelectedItem).ToList();
            return true;
        }

        // ============================================== 7 · signs & path
        int SignCount()
        {
            int n = Cal?.signsKnownAt != null ? Cal.signsKnownAt[level.ToString()] : 0;
            if (edgePicks.Contains("Hedge Magic")) n += 1;
            return Math.Min(n, CharGen.D.signs.Count);
        }
        bool NeedsSignsStep() => SignCount() > 0
            || (level >= 3 && Cal?.subpath != null && Cal.subpath.options.Count > 0)
            || Cal?.choice != null;

        CheckedListBox wSignList; ComboBox wSubpath, wChoice; Label wSignCount;
        Control BuildSigns()
        {
            var col = Column();
            wSignList = null; wSubpath = null; wChoice = null;
            int signs = SignCount();
            if (signs > 0)
            {
                col.Controls.Add(Cap($"Signs known — pick {signs}"));
                wSignCount = Tipped(Cap("", readout: true),
                    $"How many of this soul's {signs} Signs you have chosen yourself. Unlike the skills you "
                  + "may leave this short and move on: every Sign you don't pick is dealt at the end from "
                  + "the lists this Calling may draw on, at the Ranks this level has opened.");
                col.Controls.Add(wSignCount);
                wSignList = new CheckedListBox { Width = 480, Height = Math.Min(220, 40 + CharGen.D.signs.Count * 18), CheckOnClick = true, Font = new Font("Segoe UI", 9.5f) };
                foreach (var sg in CharGen.D.signs)
                {
                    int idx = wSignList.Items.Add($"{sg.name} ({sg.cost})");
                    if (signPicks.Contains(sg.name)) wSignList.SetItemChecked(idx, true);
                }
                ItemTips(wSignList, i => SignTip(CharGen.D.signs[i]),
                    $"The Signs this soul already knows — tick up to {signs}. Each is listed with what it "
                  + "costs to work; hover one for its Rank, its list, and what it does.\nA tick past "
                  + $"{signs} will not take — untick something first. Unlike the skills you may stop short: "
                  + "whatever you leave unpicked is dealt at the end from the lists this Calling is allowed, "
                  + "at the Ranks this level has opened.");
                void Refresh() => wSignCount.Text = $"Picked {wSignList.CheckedItems.Count} of {signs}  (any left unpicked are dealt at the end)";
                wSignList.ItemCheck += (s, e) =>
                {
                    int after = wSignList.CheckedItems.Count + (e.NewValue == CheckState.Checked ? 1 : -1);
                    if (after > signs) e.NewValue = CheckState.Unchecked;
                    BeginInvoke(Refresh);
                };
                Refresh();
                col.Controls.Add(wSignList);
            }
            if (level >= 3 && Cal?.subpath != null && Cal.subpath.options.Count > 0)
            {
                col.Controls.Add(Cap($"The {Cal.subpath.section} (chosen at 3rd)"));
                wSubpath = new ComboBox { Width = 300, DropDownStyle = ComboBoxStyle.DropDownList };
                foreach (var o in Cal.subpath.options) wSubpath.Items.Add(o.name);
                Tipped(wSubpath, $"At 3rd level the {Cal.name} narrows to one of the {Cal.subpath.section}. It is chosen once and kept — "
                    + "the boon it grants is printed below as you move through the list.");
                wSubpath.SelectedItem = subpathPick != null && wSubpath.Items.Contains(subpathPick) ? subpathPick : wSubpath.Items[0];
                var detail = new Label { AutoSize = true, MaximumSize = new Size(690, 0), ForeColor = Ink, Font = new Font("Segoe UI", 9f), Padding = new Padding(0, 4, 0, 0) };
                wSubpath.SelectedIndexChanged += (s, e) =>
                { detail.Text = Cal.subpath.options.FirstOrDefault(o => o.name == (string)wSubpath.SelectedItem)?.boon ?? ""; };
                detail.Text = Cal.subpath.options.FirstOrDefault(o => o.name == (string)wSubpath.SelectedItem)?.boon ?? "";
                col.Controls.Add(wSubpath);
                col.Controls.Add(detail);
            }
            if (Cal?.choice != null)
            {
                col.Controls.Add(Cap(Cal.choice.label));
                wChoice = new ComboBox { Width = 300, DropDownStyle = ComboBoxStyle.DropDownList };
                foreach (var o in Cal.choice.options) wChoice.Items.Add(o);
                Tipped(wChoice, $"{Cal.choice.label} — the {Cal.name}'s own standing choice, made at 1st level and written on the sheet.");
                wChoice.SelectedItem = choicePick != null && wChoice.Items.Contains(choicePick) ? choicePick : wChoice.Items[0];
                col.Controls.Add(wChoice);
            }
            return col;
        }
        bool CollectSigns()
        {
            if (wSignList != null)
                signPicks = wSignList.CheckedItems.Cast<string>()
                    .Select(x => x.Substring(0, x.LastIndexOf(" ("))).ToHashSet();
            subpathPick = wSubpath?.SelectedItem as string;
            choicePick = wChoice?.SelectedItem as string;
            return true;
        }

        // ============================================== 8 · outfit
        /// One line on the general store's shelf. The list holds these rather than formatted
        /// strings, so the item's name is read back off the object instead of cut out of its own
        /// label — a name containing the separator used to take the whole purchase with it.
        sealed class StoreItem
        {
            public string Name; public double Cost; public string Detail; public bool IsWeapon;
            public int Qty = 1;
            public static string Money(double v) => v < 1 ? $"{v * 100:0}¢" : $"${v:0.##}";

            /// Several of Ch. X's price-list keys carry the price inside the name itself
            /// ("Cow pony ($25)"), which read as a stutter beside the column price and reads
            /// worse once a count is added. The key is what the rules look the item up by, so
            /// only the shown name loses it.
            public string Shown => System.Text.RegularExpressions.Regex
                .Replace(Name, @"\s*\((?:\$[\d.,]+|[\d.,]+¢)\)$", "");

            public override string ToString() =>
                $"{Shown}{(Qty > 1 ? $"  × {Qty}" : "")} — {Money(Cost * Qty)}"
              + (Qty > 1 ? $" ({Money(Cost)} ea.)" : "")
              + (string.IsNullOrEmpty(Detail) ? "" : "   " + Detail);
        }

        CheckedListBox wBuyList; Label wCoinLbl; NumericUpDown wQty;
        bool qtySuppress;                       // re-labelling a row re-enters ItemCheck; don't recurse
        Control BuildOutfit()
        {
            var col = Column();
            if (coinRolled <= 0)
                coinRolled = Enumerable.Range(0, Cal.coin.dice).Sum(_ => Rules.Rng.Next(1, 7)) * Cal.coin.mult;
            wCoinLbl = Tipped(Cap("", readout: true),
                $"The money this soul starts with — {Cal.coin.dice}d6 × ${Cal.coin.mult} {Cal.coin.note}, rolled "
              + "for you — against what is in the basket, and what is left. Whatever is left stays on the "
              + "sheet as coin in their pocket; there is no requirement to spend it. The store below will not "
              + "let the basket pass this number.");
            var rollRow = new FlowLayoutPanel { AutoSize = true };
            rollRow.Controls.Add(Btn("🎲 Re-roll the coin", (s, e) =>
            {
                coinRolled = Enumerable.Range(0, Cal.coin.dice).Sum(_ => Rules.Rng.Next(1, 7)) * Cal.coin.mult;
                qtySuppress = true;
                foreach (int i in wBuyList.CheckedIndices.Cast<int>().ToList()) wBuyList.SetItemChecked(i, false);
                qtySuppress = false;
                RefreshCoin();
            }, 140, $"Roll the starting coin again — {Cal.coin.dice}d6 × ${Cal.coin.mult} {Cal.coin.note}. Everything in the basket is put back."));
            col.Controls.Add(wCoinLbl);
            col.Controls.Add(rollRow);
            var kit = Cal.coin.kit.Concat(Org?.gear ?? new List<string>()).ToList();
            if (kit.Count > 0)
                col.Controls.Add(Note("Comes free with the Calling and Origin: " + string.Join(" · ", kit)));
            col.Controls.Add(Cap("At the general store (printed prices)"));
            col.Controls.Add(Note("Tick a line to buy it. To take more than one — a second pistol, a dozen candles — highlight the "
                + "line and set the number below; the price and what's left of the coin follow along."));

            wBuyList = new CheckedListBox { Width = 560, Height = 260, CheckOnClick = true, Font = new Font("Segoe UI", 9f) };
            foreach (var w in CharGen.D.weapons.OrderBy(w => w.kind == "gun" ? 0 : 1).ThenBy(w => w.name))
            {
                if (w.cost <= 0) continue;
                var it = new StoreItem
                {
                    Name = w.name, Cost = w.cost, IsWeapon = true,
                    Detail = $"({w.dmg}{(string.IsNullOrEmpty(w.traits) ? "" : ", " + w.traits)})",
                    Qty = buyPicks.TryGetValue(w.name, out var qw) ? qw : 1
                };
                int idx = wBuyList.Items.Add(it);
                if (buyPicks.ContainsKey(w.name)) wBuyList.SetItemChecked(idx, true);
            }
            foreach (var kv in CharGen.D.gearPrices.OrderBy(kv => kv.Key))
            {
                var it = new StoreItem
                {
                    Name = kv.Key, Cost = kv.Value,
                    Qty = buyPicks.TryGetValue(kv.Key, out var qg) ? qg : 1
                };
                int idx = wBuyList.Items.Add(it);
                if (buyPicks.ContainsKey(kv.Key)) wBuyList.SetItemChecked(idx, true);
            }
            ItemTips(wBuyList, i => StoreTip((StoreItem)wBuyList.Items[i]),
                "The general store, at Chapter X's printed prices — guns and blades first, then goods, both "
              + "alphabetical. Tick a line to buy it.\nA tick the rolled coin will not cover does not take: "
              + "that is the refusal, not a stuck checkbox. To take more than one of something, highlight the "
              + "line and set the number below.\nNothing here is compulsory — coin left unspent stays on the "
              + "sheet as money. Hover a line for its price, its damage and traits, and whether it is armor.");

            wBuyList.ItemCheck += (s, e) =>
            {
                if (qtySuppress) return;
                if (e.NewValue == CheckState.Checked && SpentIf(e.Index, ((StoreItem)wBuyList.Items[e.Index]).Qty) > coinRolled)
                    e.NewValue = CheckState.Unchecked;      // can't afford it — the tick doesn't take
                BeginInvoke(RefreshCoin);
            };
            wBuyList.SelectedIndexChanged += (s, e) => SyncQtyBox();
            col.Controls.Add(wBuyList);

            var qtyRow = new FlowLayoutPanel { AutoSize = true };
            qtyRow.Controls.Add(Lbl("Of the highlighted line, take:"));
            wQty = new NumericUpDown { Minimum = 1, Maximum = 99, Value = 1, Width = 60, Margin = new Padding(3, 5, 3, 3) };
            Tipped(wQty, "How many of the highlighted line to buy. Setting it above 1 buys the line if it isn't bought already. "
                + "If the coin won't stretch to the number asked for, it falls back to the most that will.");
            wQty.ValueChanged += (s, e) => ApplyQty();
            qtyRow.Controls.Add(wQty);
            qtyRow.Controls.Add(Lbl("   (each one is charged at the printed price)"));
            col.Controls.Add(qtyRow);

            SyncQtyBox();
            RefreshCoin();
            return col;
        }

        static string StoreTip(StoreItem it) =>
            it == null ? null
          : it.IsWeapon
            ? $"{it.Shown} — {StoreItem.Money(it.Cost)} each. {it.Detail}\nBought more than once, each is carried separately: "
              + "a brace of pistols is two guns, not one gun fired twice."
            : $"{it.Shown} — {StoreItem.Money(it.Cost)} each."
              + (CharGen.D.armor.FirstOrDefault(a => a.gear == it.Name) is { } ar
                 ? $"\nThis is armor: DR {ar.drBlades} vs blades, DR {ar.drShot} vs small shot"
                   + (ar.defense != 0 ? $", Defense {ar.defense:+0;−0}" : "") + (ar.speed != 0 ? $", Speed {ar.speed:+0;−0} ft" : "")
                   + ".\nA second suit grants nothing — only the best one worn counts."
                 : "");

        /// What the basket costs if row <paramref name="index"/> were held at <paramref name="qty"/>.
        double SpentIf(int index, int qty)
        {
            double total = 0;
            for (int i = 0; i < wBuyList.Items.Count; i++)
            {
                var it = (StoreItem)wBuyList.Items[i];
                bool taken = i == index ? true : wBuyList.GetItemChecked(i);
                if (taken) total += it.Cost * (i == index ? qty : it.Qty);
            }
            return total;
        }

        void SyncQtyBox()
        {
            if (wQty == null || wBuyList?.SelectedItem is not StoreItem it) return;
            qtySuppress = true;
            wQty.Value = Math.Clamp(it.Qty, (int)wQty.Minimum, (int)wQty.Maximum);
            qtySuppress = false;
        }

        void ApplyQty()
        {
            if (qtySuppress || wBuyList?.SelectedIndex is not int idx || idx < 0) return;
            var it = (StoreItem)wBuyList.Items[idx];
            int want = (int)wQty.Value;
            // walk the number back to whatever the coin actually covers rather than refusing outright
            while (want > 1 && SpentIf(idx, want) > coinRolled) want--;
            it.Qty = want;
            qtySuppress = true;
            if (want != (int)wQty.Value) wQty.Value = want;
            bool afford = SpentIf(idx, want) <= coinRolled;
            wBuyList.Items[idx] = it;                       // re-read ToString() for the new count
            wBuyList.SetItemChecked(idx, afford);           // asking for some of a thing buys it
            wBuyList.SelectedIndex = idx;
            qtySuppress = false;
            RefreshCoin();
        }

        double Spent() => wBuyList == null ? 0
            : Enumerable.Range(0, wBuyList.Items.Count)
                .Where(i => wBuyList.GetItemChecked(i))
                .Sum(i => ((StoreItem)wBuyList.Items[i]).Cost * ((StoreItem)wBuyList.Items[i]).Qty);

        void RefreshCoin()
        {
            double spent = Spent();
            wCoinLbl.Text = $"Rolled ${coinRolled:0} {Cal.coin.note} — spent ${spent:0.##}, ${coinRolled - spent:0.##} left";
        }

        bool CollectOutfit()
        {
            buyPicks.Clear();
            for (int i = 0; i < wBuyList.Items.Count; i++)
            {
                if (!wBuyList.GetItemChecked(i)) continue;
                var it = (StoreItem)wBuyList.Items[i];
                buyPicks[it.Name] = Math.Max(1, it.Qty);
            }
            return true;
        }

        // ============================================== 9 · the person
        ComboBox wLost, wSeen, wVice, wMoving, wCompass;
        Label wLookLbl;
        SoulLook look;
        Control BuildPerson()
        {
            var col = Column();
            col.Controls.Add(Note("The Four Questions and the Compass — pick from the book's tables, write your own, or leave blank to roll."));
            ComboBox Row(string label, string key, string current)
            {
                var row = new FlowLayoutPanel { AutoSize = true };
                row.Controls.Add(Lbl(label + ":", 70));
                var cb = new ComboBox { Width = 460, DropDownStyle = ComboBoxStyle.DropDown, Margin = new Padding(3, 5, 3, 3) };
                foreach (var o in key == "compass" ? CharGen.CompassOptions() : CharGen.Flavor(key)) cb.Items.Add(o);
                cb.Text = current ?? "";
                Tipped(cb, key switch
                {
                    "lost"    => "What did you lose? The thing that is already gone when play starts — it is what the Keeper reaches for when the game needs to hurt.",
                    "seen"    => "What have you seen? The reason you believe in the dark when the sensible people don't.",
                    "vices"   => "What is your vice? Where the money and the good sense go. Grit is easier to spend when a soul has somewhere to fall.",
                    "moving"  => "What keeps you moving? The one thing that gets a frightened person back on the trail.",
                    "compass" => "Which way the soul points — the standing lean the Keeper reads you by. Not a rule, a promise about who this is.",
                    _ => null
                } + "\nPick from the book's table, write your own, or leave it blank to have it dealt at the end.");
                row.Controls.Add(cb);
                row.Controls.Add(Btn("🎲", (s, e) => cb.Text = (string)cb.Items[Rules.Rng.Next(cb.Items.Count)], 40, "Let the dice choose this one"));
                col.Controls.Add(row);
                return cb;
            }
            wLost = Row("Lost", "lost", lost);
            wSeen = Row("Seen", "seen", seen);
            wVice = Row("Vice", "vices", vice);
            wMoving = Row("Moving", "moving", moving);
            wCompass = Row("Compass", "compass", compass);

            // …and what they look like. Drawn here rather than asked for field by field: eighteen
            // more boxes at the end of a nine-step wizard is where a player puts the thing down.
            // One button, a plain-English read-back, and the whole of it is editable afterwards
            // from ✎ Tweak — which is the right place for somebody who wants to choose the coat.
            col.Controls.Add(Note("A face and an outfit, drawn against the Calling. Roll it as often as you like — "
                + "✎ Tweak on the finished sheet opens every part of it for editing."));
            var lookRow = new FlowLayoutPanel { AutoSize = true };
            lookRow.Controls.Add(Lbl("Look:", 70));
            wLookLbl = new Label
            {
                Width = 460, AutoSize = false, Height = 46, ForeColor = Ink, Padding = new Padding(0, 4, 0, 0),
                Font = new Font("Segoe UI", 9f, FontStyle.Italic), Tag = "readout"
            };
            Tipped(wLookLbl, "How this soul strikes a stranger — their people, build, dress and the one detail "
                + "anybody would describe first. Nothing here costs or grants anything.");
            ShowLook();
            lookRow.Controls.Add(wLookLbl);
            // A wizard that was given a name cannot have that name overruled by a description, so
            // the draw leaves out the peoples whose names come whole. Left blank, the name is
            // still to be drawn and follows whatever this hands back.
            lookRow.Controls.Add(Btn("🎲", (s, e) =>
            {
                look = Look.Roll(charGender, calName, nameIsFixed: !string.IsNullOrWhiteSpace(charName));
                ShowLook();
            }, 40, "Draw a fresh description"));
            col.Controls.Add(lookRow);
            return col;
        }
        void ShowLook()
        {
            if (wLookLbl == null) return;
            wLookLbl.Text = look is { Any: true }
                ? look.AtAGlance
                : "Not drawn yet — one is dealt with the sheet if you leave it.";
        }
        bool CollectPerson()
        {
            lost = wLost.Text.Trim(); seen = wSeen.Text.Trim(); vice = wVice.Text.Trim();
            moving = wMoving.Text.Trim(); compass = wCompass.Text.Trim();
            return true;
        }
    }
}
