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
        readonly HashSet<string> buyPicks = new();
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
                BuyWeapons = buyPicks.Where(n => CharGen.D.weapons.Any(w => w.name == n)).ToList(),
                BuyGear = buyPicks.Where(n => CharGen.D.gearPrices.ContainsKey(n)).ToList(),
                Name = charName, Gender = charGender, Compass = compass,
                Lost = lost, Seen = seen, Vice = vice, Moving = moving
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
            Font = new Font("Segoe UI", 9f, FontStyle.Italic), ForeColor = Gold, Padding = new Padding(0, 4, 0, 6)
        };
        static Label Cap(string t) => new()
        { Text = t, AutoSize = true, Font = new Font("Segoe UI", 9.5f, FontStyle.Bold), ForeColor = Ink, Padding = new Padding(0, 8, 4, 2) };

        static FlowLayoutPanel Column() => new()
        { FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoSize = true, Padding = new Padding(2) };

        // ============================================== 1 · basics
        NumericUpDown wLevel; ComboBox wMethod, wGender; TextBox wName;
        Control BuildBasics()
        {
            var col = Column();
            col.Controls.Add(Note("Every choice ahead is filtered to what the book allows. Anything left on \"" + LetBook + "\" is rolled for you at the end, by the same rules as the generator."));
            var row1 = new FlowLayoutPanel { AutoSize = true };
            row1.Controls.Add(Lbl("Level:"));
            wLevel = new NumericUpDown { Minimum = 1, Maximum = 10, Value = level, Width = 56, Margin = new Padding(3, 6, 3, 3) };
            row1.Controls.Add(wLevel);
            row1.Controls.Add(Lbl("   Abilities by:"));
            wMethod = new ComboBox { Width = 240, DropDownStyle = ComboBoxStyle.DropDownList };
            wMethod.Items.AddRange(new object[] { "The Honest Array (15 14 13 12 10 8)", "The Gamble (roll 4d6, drop lowest)", "Set the scores by hand" });
            wMethod.SelectedIndex = methodIdx;
            row1.Controls.Add(wMethod);
            col.Controls.Add(row1);
            var row2 = new FlowLayoutPanel { AutoSize = true };
            row2.Controls.Add(Lbl("Name:"));
            wName = new TextBox { Width = 260, Text = charName, Margin = new Padding(3, 5, 3, 3) };
            row2.Controls.Add(wName);
            row2.Controls.Add(Lbl("  Gender:"));
            wGender = new ComboBox { Width = 110, DropDownStyle = ComboBoxStyle.DropDown, Text = charGender, Margin = new Padding(3, 5, 3, 3) };
            wGender.Items.AddRange(new object[] { "Woman", "Man" });
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
            level = newLevel; methodIdx = newMethod; charName = wName.Text.Trim(); charGender = wGender.Text.Trim();
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
            var detail = new Label { Width = 440, Height = 300, ForeColor = Ink, Font = new Font("Segoe UI", 9.5f) };
            var choiceRow = new FlowLayoutPanel { AutoSize = true };
            choiceRow.Controls.Add(Lbl("Either/or skill:"));
            wOrgChoice = new ComboBox { Width = 220, DropDownStyle = ComboBoxStyle.DropDownList };
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
                wPoolLbl = Cap("The pool:  " + string.Join("  ", pool));
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
            wSkillCount = Cap("");
            col.Controls.Add(wSkillCount);
            wSkillList = new CheckedListBox { Width = 340, Height = 300, CheckOnClick = true, Font = new Font("Segoe UI", 9.5f) };
            foreach (var sk in CharGen.D.skills)
            {
                if (free.Contains(sk.name)) continue;
                int idx = wSkillList.Items.Add($"{sk.name} ({sk.ability})");
                if (skillPicks.Contains(sk.name)) wSkillList.SetItemChecked(idx, true);
            }
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
                    RefillAll();
                };
                cb.DropDown += (s, e) => RefillAll();
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
                wSignCount = Cap("");
                col.Controls.Add(wSignCount);
                wSignList = new CheckedListBox { Width = 480, Height = Math.Min(220, 40 + CharGen.D.signs.Count * 18), CheckOnClick = true, Font = new Font("Segoe UI", 9.5f) };
                foreach (var sg in CharGen.D.signs)
                {
                    int idx = wSignList.Items.Add($"{sg.name} ({sg.cost})");
                    if (signPicks.Contains(sg.name)) wSignList.SetItemChecked(idx, true);
                }
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
        CheckedListBox wBuyList; Label wCoinLbl;
        readonly Dictionary<string, double> buyCost = new();
        Control BuildOutfit()
        {
            var col = Column();
            buyCost.Clear();
            if (coinRolled <= 0)
                coinRolled = Enumerable.Range(0, Cal.coin.dice).Sum(_ => Rules.Rng.Next(1, 7)) * Cal.coin.mult;
            wCoinLbl = Cap("");
            var rollRow = new FlowLayoutPanel { AutoSize = true };
            rollRow.Controls.Add(Btn("🎲 Re-roll the coin", (s, e) =>
            {
                coinRolled = Enumerable.Range(0, Cal.coin.dice).Sum(_ => Rules.Rng.Next(1, 7)) * Cal.coin.mult;
                foreach (int i in wBuyList.CheckedIndices.Cast<int>().ToList()) wBuyList.SetItemChecked(i, false);
                RefreshCoin();
            }, 140, $"{Cal.coin.dice}d6 × ${Cal.coin.mult} {Cal.coin.note}"));
            col.Controls.Add(wCoinLbl);
            col.Controls.Add(rollRow);
            var kit = Cal.coin.kit.Concat(Org?.gear ?? new List<string>()).ToList();
            if (kit.Count > 0)
                col.Controls.Add(Note("Comes free with the Calling and Origin: " + string.Join(" · ", kit)));
            col.Controls.Add(Cap("At the general store (printed prices)"));
            wBuyList = new CheckedListBox { Width = 520, Height = 280, CheckOnClick = true, Font = new Font("Segoe UI", 9f) };
            foreach (var w in CharGen.D.weapons.OrderBy(w => w.kind == "gun" ? 0 : 1).ThenBy(w => w.name))
            {
                if (w.cost <= 0) continue;
                string label = $"{w.name} — ${w.cost:0}   ({w.dmg}{(string.IsNullOrEmpty(w.traits) ? "" : ", " + w.traits)})";
                buyCost[label] = w.cost;
                int idx = wBuyList.Items.Add(label);
                if (buyPicks.Contains(w.name)) wBuyList.SetItemChecked(idx, true);
            }
            foreach (var kv in CharGen.D.gearPrices.OrderBy(kv => kv.Key))
            {
                string label = $"{kv.Key} — {(kv.Value < 1 ? $"{kv.Value * 100:0}¢" : $"${kv.Value:0.##}")}";
                buyCost[label] = kv.Value;
                int idx = wBuyList.Items.Add(label);
                if (buyPicks.Contains(kv.Key)) wBuyList.SetItemChecked(idx, true);
            }
            wBuyList.ItemCheck += (s, e) =>
            {
                if (e.NewValue == CheckState.Checked)
                {
                    double spent = wBuyList.CheckedItems.Cast<string>().Sum(x => buyCost[x]);
                    if (spent + buyCost[(string)wBuyList.Items[e.Index]] > coinRolled) e.NewValue = CheckState.Unchecked;
                }
                BeginInvoke(RefreshCoin);
            };
            col.Controls.Add(wBuyList);
            RefreshCoin();
            return col;
        }
        void RefreshCoin()
        {
            double spent = wBuyList?.CheckedItems.Cast<string>().Sum(x => buyCost[x]) ?? 0;
            wCoinLbl.Text = $"Rolled ${coinRolled:0} {Cal.coin.note} — spent ${spent:0.##}, ${coinRolled - spent:0.##} left";
        }
        bool CollectOutfit()
        {
            buyPicks.Clear();
            foreach (string item in wBuyList.CheckedItems)
            {
                string name = item.Substring(0, item.LastIndexOf(" — "));
                buyPicks.Add(name);
            }
            return true;
        }

        // ============================================== 9 · the person
        ComboBox wLost, wSeen, wVice, wMoving, wCompass;
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
                row.Controls.Add(cb);
                row.Controls.Add(Btn("🎲", (s, e) => cb.Text = (string)cb.Items[Rules.Rng.Next(cb.Items.Count)], 40));
                col.Controls.Add(row);
                return cb;
            }
            wLost = Row("Lost", "lost", lost);
            wSeen = Row("Seen", "seen", seen);
            wVice = Row("Vice", "vices", vice);
            wMoving = Row("Moving", "moving", moving);
            wCompass = Row("Compass", "compass", compass);
            return col;
        }
        bool CollectPerson()
        {
            lost = wLost.Text.Trim(); seen = wSeen.Text.Trim(); vice = wVice.Text.Trim();
            moving = wMoving.Text.Trim(); compass = wCompass.Text.Trim();
            return true;
        }
    }
}
